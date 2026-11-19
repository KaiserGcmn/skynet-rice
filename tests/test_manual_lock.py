"""Opt-in xss-lock integration test on a private X server and private D-Bus.

Set SKYNET_LOCK_TEST_DISPLAY to an isolated display numbered 90 or higher.
Ordinary test runs skip this test. No real login1 service or locker is used.
"""
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
import unittest


DISPLAY = os.environ.get('SKYNET_LOCK_TEST_DISPLAY')


@unittest.skipUnless(DISPLAY, 'requires a private X11 display')
class ManualLockTest(unittest.TestCase):
    def setUp(self):
        number = re.fullmatch(r':(\d+)(?:\.0)?', DISPLAY)
        if not number or int(number[1]) < 90:
            raise RuntimeError('Refusing to use an ordinary desktop display')
        self.work = tempfile.TemporaryDirectory(prefix='skynet-lock-test-')
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.log = (self.root / 'test.log').open('w')
        self.addCleanup(self.log.close)
        self.processes = []
        self.addCleanup(self.stop_processes)
        self.env = dict(os.environ, DISPLAY=DISPLAY, XDG_SESSION_ID='test')
        daemon = self.spawn(['dbus-daemon', '--session', '--nofork', '--print-address=1'],
                            stdout=subprocess.PIPE, text=True)
        address = daemon.stdout.readline().strip()
        self.assertTrue(address)
        self.address = address
        self.env.update(DBUS_SESSION_BUS_ADDRESS=address,
                        DBUS_SYSTEM_BUS_ADDRESS=address)
        fixture = Path(__file__).parent / 'fixtures/login1_lock.py'
        mock = self.spawn(['/usr/bin/python3', str(fixture)])
        self.until(lambda: self.service_ready())
        self.assertIsNone(mock.poll())
        self.marker = self.root / 'locked'
        self.locker = self.root / 'locker.py'
        self.locker.write_text(
            "from pathlib import Path\nimport time\n"
            "with Path(__file__).with_name('locked').open('a') as f: f.write('lock\\n')\n"
            "time.sleep(.3)\n")

    def spawn(self, command, **kwargs):
        kwargs.setdefault('stdout', self.log)
        proc = subprocess.Popen(command, env=self.env, stderr=self.log,
                                start_new_session=True, **kwargs)
        self.processes.append(proc)
        return proc

    def stop_processes(self):
        for proc in reversed(self.processes):
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=3)
            if proc.stdout:
                proc.stdout.close()

    def run_command(self, *args):
        return subprocess.run(args, env=self.env, stdout=self.log, stderr=self.log,
                              check=True, timeout=5)

    def service_ready(self):
        result = subprocess.run(
            ['gdbus', 'call', '--address', self.address, '--dest', 'org.freedesktop.login1',
             '--object-path', '/org/freedesktop/login1', '--method',
             'org.freedesktop.login1.Manager.GetSession', 'test'],
            env=self.env, capture_output=True, timeout=2)
        return result.returncode == 0

    def until(self, predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(.05)
        self.log.flush()
        self.fail((self.root / 'test.log').read_text()[-2000:])

    def count(self):
        return len(self.marker.read_text().splitlines()) if self.marker.exists() else 0

    def test_disabled_idle_timeout_preserves_explicit_lock_paths(self):
        self.run_command('xset', 's', '1', '0')
        self.run_command('xset', 's', 'reset')
        watcher = self.spawn(['xss-lock', '--session', 'test', '--transfer-sleep-lock',
                              '--', '/usr/bin/python3', str(self.locker)])
        self.until(lambda: self.count() == 1)
        self.run_command('xset', 's', '0', '0')
        time.sleep(2.5)
        self.assertEqual(self.count(), 1, 'An idle lock fired with timeout zero')
        self.run_command('gdbus', 'call', '--address', self.address,
                         '--dest', 'org.freedesktop.login1', '--object-path',
                         '/org/freedesktop/login1', '--method', 'org.skynet.Test.EmitLock')
        self.until(lambda: self.count() == 2)
        time.sleep(.6)
        self.run_command('xset', 's', 'activate')
        self.until(lambda: self.count() == 3)
        time.sleep(.6)
        self.assertIsNone(watcher.poll())


if __name__ == '__main__':
    unittest.main()
