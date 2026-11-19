"""LED synchronization and idle-query regression checks with no real devices."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import signal
import tempfile
import time
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / 'runtime/usr/local/bin/skynet-audio-leds'


class AudioLedsTest(unittest.TestCase):
    def setUp(self):
        loader = importlib.machinery.SourceFileLoader('audio_leds_fixture', str(SOURCE))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        self.leds = importlib.util.module_from_spec(spec)
        loader.exec_module(self.leds)
        work = tempfile.TemporaryDirectory(prefix='skynet-led-test-')
        self.addCleanup(work.cleanup)
        self.root = Path(work.name)
        self.leds.LEDS = {kind: self.root / kind for kind in ('sink', 'source')}
        for path in self.leds.LEDS.values():
            path.write_text('0\n')

    def test_speaker_and_microphone_independent_and_failed_query_preserves_led(self):
        def query(args, **kwargs):
            muted = args[1] == 'get-source-mute'
            return subprocess.CompletedProcess(args, 0, 'Mute: yes\n' if muted else 'Mute: no\n')
        with mock.patch.object(self.leds.subprocess, 'run', side_effect=query):
            self.assertTrue(self.leds.sync())
        self.assertEqual(self.leds.LEDS['sink'].read_text(), '0\n')
        self.assertEqual(self.leds.LEDS['source'].read_text(), '1\n')
        with mock.patch.object(self.leds.subprocess, 'run',
                               return_value=subprocess.CompletedProcess([], 1, '')):
            self.assertFalse(self.leds.sync())
        self.assertEqual(self.leds.LEDS['source'].read_text(), '1\n')

    def simulate(self, duration, events=None, fail_first=False):
        clock = [0.0]
        sync_times = []
        events = dict(events or {})
        pending = [b'']
        waits = []
        subscriber = mock.Mock()
        subscriber.poll.return_value = None
        def synchronize():
            sync_times.append(clock[0])
            return not (fail_first and len(sync_times) == 1)
        def select(readers, writers, errors, timeout):
            self.assertGreater(timeout, 0)
            waits.append(timeout)
            next_event = min((t for t in events if t > clock[0]), default=duration)
            clock[0] = min(clock[0] + timeout, next_event, duration)
            if clock[0] >= duration:
                self.leds.running = False
            if clock[0] in events:
                pending[0] = events.pop(clock[0])
                return [subscriber.stdout], [], []
            return [], [], []
        with mock.patch.dict(os.environ, XDG_RUNTIME_DIR=str(self.root)), \
                mock.patch.object(self.leds.sys, 'argv', ['skynet-audio-leds']), \
                mock.patch.object(self.leds.signal, 'signal'), \
                mock.patch.object(self.leds.time, 'monotonic', side_effect=lambda: clock[0]), \
                mock.patch.object(self.leds, 'sync', side_effect=synchronize), \
                mock.patch.object(self.leds.subprocess, 'Popen', return_value=subscriber), \
                mock.patch.object(self.leds.select, 'select', side_effect=select), \
                mock.patch.object(self.leds.os, 'read', side_effect=lambda *_: pending[0]):
            self.assertEqual(self.leds.main(), 0)
        subscriber.terminate.assert_called_once()
        subscriber.wait.assert_called_once()
        subscriber.stdout.close.assert_called_once()
        self.last_waits = waits
        return sync_times

    def test_idle_queries_are_bounded(self):
        times = self.simulate(65)
        self.assertEqual(times[0], 0)
        self.assertLessEqual(len(times), 3)
        self.assertTrue(all(b - a >= 30 for a, b in zip(times, times[1:])))
        self.assertEqual(len(self.last_waits), 3)
        self.assertTrue(all(wait == 30 for wait in self.last_waits))

    def test_sigterm_interrupts_idle_wait_and_reaps_subscriber(self):
        fake = self.root / 'pactl'
        fake.write_text('#!/usr/bin/python3\nimport os,signal,sys\nfrom pathlib import Path\n'
                        'if sys.argv[1] == "subscribe":\n'
                        ' Path(__file__).with_name("child.pid").write_text(str(os.getpid()))\n'
                        ' signal.pause()\n'
                        'else: print("Mute: no")\n')
        fake.chmod(0o755)
        runner = self.root / 'runner.py'
        runner.write_text('import runpy\nfrom pathlib import Path\n'
                          f'ns=runpy.run_path({str(SOURCE)!r})\n'
                          f'ns["main"].__globals__["PACTL"]={str(fake)!r}\n'
                          f'ns["main"].__globals__["LEDS"]={{"sink":Path({str(self.root / "sink")!r}),"source":Path({str(self.root / "source")!r})}}\n'
                          'raise SystemExit(ns["main"]())\n')
        proc = subprocess.Popen(['/usr/bin/python3', str(runner)],
                                env=dict(os.environ, XDG_RUNTIME_DIR=str(self.root)),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 3
            while not (self.root / 'child.pid').exists() and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertTrue((self.root / 'child.pid').exists())
            child_pid = int((self.root / 'child.pid').read_text())
            time.sleep(.15)
            start = time.monotonic()
            proc.send_signal(signal.SIGTERM)
            stdout, stderr = proc.communicate(timeout=2)
            self.assertEqual(proc.returncode, 0, stderr.decode())
            self.assertLess(time.monotonic() - start, 1)
            self.assertFalse(Path('/proc', str(child_pid)).exists())
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()

    def test_audio_events_are_immediate_but_client_events_do_not_poll(self):
        times = self.simulate(20, {
            3: b"Event 'new' on client #1\n",
            7: b"Event 'change' on sink #2\n",
            12: b"Event 'change' on source #3\n",
            17: b"Event 'change' on server #0\n",
        })
        self.assertEqual(times, [0, 7, 12, 17])

    def test_failed_initial_sync_retries_promptly(self):
        times = self.simulate(10, fail_first=True)
        self.assertEqual(len(times), 2)
        self.assertGreater(times[1], 0)
        self.assertLessEqual(times[1], 2)


if __name__ == '__main__':
    unittest.main()
