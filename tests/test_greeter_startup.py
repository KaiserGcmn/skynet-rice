"""Exercise startup recovery with private stand-ins, never the real login service."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "runtime/usr/local/libexec/greetd/hud-greeter"
STUB = r'''#!/usr/bin/python3
import json, os, signal, subprocess, sys
from pathlib import Path
root = Path(os.environ['TEST_ROOT'])
name = Path(sys.argv[0]).name
def record(**values):
    with (root / 'events').open('a') as out:
        out.write(json.dumps(dict(tool=name, **values)) + '\n')
if name == 'dpkg-query':
    print(os.environ.get('TEST_VERSION', '0.8-1+b1'))
elif name == 'cage':
    count = root / 'count'
    attempt = int(count.read_text()) + 1 if count.exists() else 1
    count.write_text(str(attempt))
    runtime = Path(os.environ['XDG_RUNTIME_DIR'])
    assert runtime.stat().st_mode & 0o777 == 0o700
    (runtime / 'wayland-stale').touch()
    assert os.environ['GDK_BACKEND'] == 'wayland'
    assert os.environ['GREETD_SOCK'] == 'SYNTHETIC_SOCKET'
    assert 'WAYLAND_DISPLAY' not in os.environ
    assert 'DISPLAY' not in os.environ
    # No autolaunched session bus (it needs X11, i.e. Xwayland) or a11y bus.
    assert os.environ['DBUS_SESSION_BUS_ADDRESS'] == 'disabled:'
    assert os.environ['NO_AT_BRIDGE'] == '1'
    record(attempt=attempt, runtime=str(runtime), args=sys.argv[1:])
    if os.environ.get('TEST_TERMINATE'):
        os.kill(os.getppid(), signal.SIGTERM)
        raise SystemExit(1)
    failures = int(os.environ.get('TEST_FAILURES', '0'))
    if attempt <= failures:
        print('Synthetic compositor initialization failure', file=sys.stderr)
        raise SystemExit(1)
    child = sys.argv[sys.argv.index('--') + 1:]
    # Python normally closes extra descriptors; Cage preserves fd 3 at exec.
    raise SystemExit(subprocess.run(child, pass_fds=(3,)).returncode)
elif name == 'gtkgreet':
    try:
        os.fstat(3)
    except OSError:
        pass
    else:
        raise SystemExit('Compositor stderr descriptor leaked to GTK')
    record(args=sys.argv[1:])
    print('SYNTHETIC_FRONTEND_DIAGNOSTIC', file=sys.stderr)
elif name == 'logger':
    args=sys.argv[1:]
    value=Path(args[args.index('--file')+1]).read_text() if '--file' in args else args[-1]
    record(message=value)
    raise SystemExit(int(os.environ.get('TEST_LOGGER_FAILURE', '0')))
elif name == 'sleep':
    record(seconds=sys.argv[1:])
elif name == 'fallback':
    record(args=sys.argv[1:], graphical_env={k:v for k,v in os.environ.items()
        if k in ('XDG_RUNTIME_DIR', 'XDG_SESSION_TYPE', 'GDK_BACKEND', 'GTK_THEME',
                 'DBUS_SESSION_BUS_ADDRESS', 'NO_AT_BRIDGE')})
'''


class GreeterStartupTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix="hud-greeter-startup-")
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("dpkg-query", "cage", "gtkgreet", "logger", "sleep", "fallback"):
            f = self.bin / name
            f.write_text(STUB)
            f.chmod(0o755)
        self.candidate = self.root / "launcher"
        text = LAUNCHER.read_text()
        substitutions = {
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin":
                f"PATH={self.bin}:/usr/bin:/bin",
            "/usr/bin/cage": str(self.bin / "cage"),
            "/usr/local/libexec/greetd/gtkgreet-hud": str(self.bin / "gtkgreet"),
            "/usr/local/libexec/greetd/tuigreet-capslock": str(self.bin / "fallback"),
            "/etc/default/keyboard": str(self.root / "absent-keyboard"),
            "/tmp/hud-greeter.XXXXXXXX": str(self.root / "runtime.XXXXXXXX"),
        }
        for old, new in substitutions.items():
            self.assertIn(old, text)
            text = text.replace(old, new)
        self.candidate.write_text(text)

    def run_launcher(self, **extra):
        env = os.environ | {
            "TEST_ROOT": str(self.root), "GREETD_SOCK": "SYNTHETIC_SOCKET",
            "DISPLAY": ":9876", "WAYLAND_DISPLAY": "fake-wayland",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent-test-bus",
        } | extra
        result = subprocess.run(["/bin/sh", str(self.candidate)], env=env,
                                text=True, capture_output=True, timeout=10)
        f = self.root / "events"
        events = [json.loads(line) for line in f.read_text().splitlines()] if f.exists() else []
        self.assertFalse(list(self.root.glob("runtime.*")), "private runtime must be removed")
        return result, events

    def test_success_has_no_delay_or_fallback_and_keeps_frontend_stderr_private(self):
        result, events = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([e['tool'] for e in events], ['cage', 'gtkgreet'])
        self.assertIn('SYNTHETIC_FRONTEND_DIAGNOSTIC', result.stderr)

    def test_transient_failure_retries_with_fresh_runtime_and_records_real_error(self):
        result, events = self.run_launcher(TEST_FAILURES='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        attempts = [e for e in events if e['tool'] == 'cage']
        self.assertEqual(len(attempts), 2)
        self.assertNotEqual(attempts[0]['runtime'], attempts[1]['runtime'])
        self.assertEqual([e['seconds'] for e in events if e['tool'] == 'sleep'], [['1']])
        logs = '\n'.join(e['message'] for e in events if e['tool'] == 'logger')
        self.assertIn('Synthetic compositor initialization failure', logs)
        self.assertIn('Synthetic compositor initialization failure', result.stderr)
        self.assertNotIn('SYNTHETIC_FRONTEND_DIAGNOSTIC', logs)
        self.assertFalse(any(e['tool'] == 'fallback' for e in events))

    def test_persistent_failure_is_bounded_and_retains_password_login_fallback(self):
        result, events = self.run_launcher(TEST_FAILURES='9')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sum(e['tool'] == 'cage' for e in events), 3)
        self.assertEqual(sum(e['tool'] == 'sleep' for e in events), 2)
        fallback = [e for e in events if e['tool'] == 'fallback']
        self.assertEqual(len(fallback), 1)
        self.assertEqual(fallback[0]['graphical_env'], {})
        self.assertIn('--asterisks', fallback[0]['args'])
        self.assertIn('/usr/local/libexec/greetd/start-x /usr/local/bin/dwm-session', fallback[0]['args'])

    def test_package_version_guard_is_not_bypassed_by_retry(self):
        result, events = self.run_launcher(TEST_VERSION='0.9-1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([e['tool'] for e in events], ['logger', 'fallback'])

    def test_logger_failure_does_not_prevent_recovery_or_hide_stderr(self):
        result, events = self.run_launcher(TEST_FAILURES='1', TEST_LOGGER_FAILURE='1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Synthetic compositor initialization failure', result.stderr)
        self.assertTrue(any(e['tool'] == 'gtkgreet' for e in events))

    def test_termination_never_restarts_graphics_or_opens_fallback(self):
        result, events = self.run_launcher(TEST_TERMINATE='1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual([e['tool'] for e in events], ['cage'])

    def test_runtime_creation_failure_uses_fallback_without_launching_graphics(self):
        text = self.candidate.read_text().replace('mktemp -d ', '/bin/false ')
        self.candidate.write_text(text)
        result, events = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any(e['tool'] in ('cage', 'sleep') for e in events))
        self.assertTrue(any(e['tool'] == 'fallback' for e in events))


if __name__ == '__main__':
    unittest.main()
