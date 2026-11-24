"""dwm-session stops the daemonized PulseAudio before the session ends."""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / 'runtime/usr/local/bin/dwm-session'
# Fake pulseaudio: logs its arguments; --check reports "running" until the
# number of --check calls after --kill reaches $FAKE_PA_EXIT_AFTER.
FAKE = r'''#!/bin/sh
log="$FAKE_PA_DIR/calls"
printf '%s\n' "$*" >>"$log"
case "$1" in
    --check)
        [ -e "$FAKE_PA_DIR/running" ] || exit 1
        if [ -e "$FAKE_PA_DIR/killed" ]; then
            n=$(grep -c -- '^--check' "$log")
            [ "$n" -gt "$FAKE_PA_EXIT_AFTER" ] && exit 1
        fi
        exit 0 ;;
    --kill) touch "$FAKE_PA_DIR/killed"; exit 0 ;;
esac
exit 0
'''


def functions(text, *names):
    return '\n'.join(re.search(r'^%s\(\) \{\n.*?^\}' % name, text, re.S | re.M).group(0)
                     for name in names)


class SessionPulseaudioTest(unittest.TestCase):
    def setUp(self):
        self.text = SESSION.read_text()
        self.work = tempfile.TemporaryDirectory(prefix='dwm-session-pa-')
        self.addCleanup(self.work.cleanup)
        self.dir = Path(self.work.name)
        fake = self.dir / 'bin/pulseaudio'
        fake.parent.mkdir()
        fake.write_text(FAKE)
        fake.chmod(0o755)

    def run_shell(self, body, running=True, exit_after=3):
        if running:
            (self.dir / 'running').touch()
        env = dict(os.environ, PATH=f'{self.dir}/bin:/usr/bin:/bin',
                   FAKE_PA_DIR=str(self.dir), FAKE_PA_EXIT_AFTER=str(exit_after))
        script = functions(self.text, 'stop_pulseaudio', 'cleanup') + '\n' + body
        start = time.monotonic()
        subprocess.run(['sh', '-c', script], env=env, check=True, timeout=20)
        calls = self.dir / 'calls'
        return (calls.read_text().split('\n')[:-1] if calls.exists() else []), time.monotonic() - start

    def test_running_daemon_is_killed_once_and_waited_for(self):
        calls, _ = self.run_shell('stop_pulseaudio', exit_after=3)
        self.assertEqual(calls.count('--kill'), 1)
        self.assertEqual(calls[:2], ['--check', '--kill'])
        self.assertEqual(calls.count('--check'), 4)

    def test_absent_daemon_is_not_killed(self):
        calls, _ = self.run_shell('stop_pulseaudio', running=False)
        self.assertEqual(calls, ['--check'])

    def test_wait_is_bounded_when_the_daemon_never_exits(self):
        calls, elapsed = self.run_shell('stop_pulseaudio', exit_after=10 ** 6)
        self.assertEqual(calls.count('--kill'), 1)
        self.assertEqual(calls.count('--check'), 31)
        self.assertLess(elapsed, 10)

    def test_cleanup_stops_children_first_then_pulseaudio(self):
        body = ('sleep 30 & children=" $!"; child=$!\n'
                'cleanup\n'
                'sleep 0.2; kill -0 "$child" 2>/dev/null && exit 9; exit 0')
        calls, _ = self.run_shell(body, exit_after=1)
        self.assertIn('--kill', calls)
        cleanup = functions(self.text, 'cleanup')
        self.assertLess(cleanup.index('kill "$child"'), cleanup.index('stop_pulseaudio'))

    def test_session_still_starts_pulseaudio_and_calls_cleanup_on_exit(self):
        self.assertIn('start pulseaudio --start', self.text)
        self.assertIn('trap cleanup EXIT', self.text)


if __name__ == '__main__':
    unittest.main()
