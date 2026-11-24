"""The lock screen asks only for the password after a failed fingerprint stage."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'runtime/usr/local/libexec/dwm-lock-fingerprint-gate'
PAM_SERVICE = ROOT / 'profiles/debian/rootfs/etc/pam.d/dwm-fingerprint'
GATE = '/usr/local/libexec/dwm-lock-fingerprint-gate'


def load():
    loader = importlib.machinery.SourceFileLoader('dwm_lock_fingerprint_gate', str(HELPER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class GateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load()

    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix='lock-gate-test-')
        self.addCleanup(self.work.cleanup)
        self.dir = Path(self.work.name) / 'run'
        self.dir.mkdir(mode=0o700)
        self.marker = self.dir / self.gate.MARKER

    def run_gate(self, action, *extra):
        return self.gate.main([action, '--state-dir', str(self.dir), *extra])

    def test_first_attempt_still_scans_the_fingerprint(self):
        self.assertEqual(self.run_gate('check'), 1)

    def test_failed_fingerprint_makes_the_retry_password_only(self):
        self.assertEqual(self.run_gate('mark'), 0)
        self.assertEqual(self.run_gate('check'), 0)
        self.assertEqual(oct(self.marker.stat().st_mode & 0o777), '0o600')

    def test_marker_expires_so_a_later_return_scans_again(self):
        self.run_gate('mark')
        old = time.time() - 121
        os.utime(self.marker, (old, old))
        self.assertEqual(self.run_gate('check'), 1)
        self.assertEqual(self.run_gate('check', '--ttl', '300'), 0)

    def test_every_failed_attempt_refreshes_the_time(self):
        self.run_gate('mark')
        old = time.time() - 100
        os.utime(self.marker, (old, old))
        self.run_gate('mark')
        self.assertLess(time.time() - self.marker.stat().st_mtime, 5)

    def test_timestamp_in_the_future_is_not_trusted(self):
        self.run_gate('mark')
        future = time.time() + 3600
        os.utime(self.marker, (future, future))
        self.assertEqual(self.run_gate('check'), 1)

    def test_successful_unlock_clears_the_marker(self):
        self.run_gate('mark')
        self.assertEqual(self.run_gate('clear'), 0)
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.run_gate('check'), 1)
        self.assertEqual(self.run_gate('clear'), 0)  # repeat run

    def test_zero_ttl_never_skips_the_scan(self):
        self.run_gate('mark')
        self.assertEqual(self.run_gate('check', '--ttl', '0'), 1)

    def test_symlinked_marker_is_not_followed(self):
        target = Path(self.work.name) / 'victim'
        target.write_text('keep')
        old = time.time() - 1000
        os.utime(target, (old, old))
        self.marker.symlink_to(target)
        self.assertEqual(self.run_gate('mark'), 1)
        self.assertEqual(self.run_gate('check'), 1)
        self.assertEqual(target.read_text(), 'keep')
        self.assertLess(target.stat().st_mtime, time.time() - 900)

    def test_shared_state_directory_is_refused(self):
        self.dir.chmod(0o770)
        self.assertEqual(self.run_gate('mark'), 1)
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.run_gate('check'), 1)

    def test_missing_state_directory_keeps_the_normal_order(self):
        self.dir.rmdir()
        self.assertEqual(self.run_gate('check'), 1)
        self.assertEqual(self.run_gate('mark'), 1)
        self.assertEqual(self.run_gate('clear'), 0)

    def test_bad_arguments_exit_with_usage_status(self):
        result = subprocess.run([sys.executable, str(HELPER), 'grant'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.gate.main(['check', '--ttl', 'soon']), 2)

    def test_helper_is_executable_with_a_python_shebang(self):
        self.assertTrue(os.access(HELPER, os.X_OK))
        self.assertEqual(HELPER.read_text().splitlines()[0], '#!/usr/bin/python3')


class PamServiceTest(unittest.TestCase):
    def lines(self):
        # kind, control (a bracketed control may contain spaces), rest of the line
        parsed = []
        for line in PAM_SERVICE.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                parsed.append(list(re.match(r'(\S+)\s+(\[[^\]]*\]|\S+)\s*(.*)$', line).groups()))
        return parsed

    def test_order_gate_fingerprint_mark_password_clear(self):
        modules = [tuple(l) for l in self.lines()]
        names = []
        for kind, control, rest in modules:
            if kind == '@include':
                names.append('include:' + control)
            else:
                action = rest.split()[-1] if 'dwm-lock-fingerprint-gate' in rest else ''
                module = re.search(r'(pam_\w+)\.so', rest).group(1)
                names.append(f'{module}:{action}' if action else module)
        self.assertEqual(names, ['pam_exec:check', 'pam_fprintd', 'pam_exec:mark',
                                 'include:common-auth', 'pam_exec:clear'])

    def test_gate_can_only_skip_the_fingerprint_line(self):
        lines = self.lines()
        check = lines[0]
        # Exactly one line is skipped and a helper failure ignores the gate.
        self.assertEqual(check[1], '[success=1 default=ignore]')
        self.assertTrue(check[2].endswith(f'{GATE} check'))
        self.assertEqual(lines[1][1], 'sufficient')
        self.assertIn('pam_fprintd.so', lines[1][2])
        # mark/clear are optional: their failure never changes the outcome.
        for index, action in ((2, 'mark'), (4, 'clear')):
            self.assertEqual(lines[index][1], 'optional')
            self.assertTrue(lines[index][2].endswith(f'{GATE} {action}'))
        # No helper line may grant access.
        for kind, control, rest in lines:
            if 'pam_exec' in rest:
                self.assertNotIn('sufficient', control)
                self.assertNotIn('done', control)
                self.assertNotIn('ok', control)

    def test_password_stack_is_still_reached_and_unchanged(self):
        self.assertIn(['@include', 'common-auth'], [l[:2] for l in self.lines()])
        self.assertEqual(
            sum('pam_deny' in l[-1] or 'pam_permit' in l[-1] for l in self.lines()), 0)

    def test_locker_still_uses_this_service(self):
        launcher = (ROOT / 'runtime/usr/local/libexec/dwm-lock').read_text()
        self.assertIn("'XSECURELOCK_PAM_SERVICE': 'dwm-fingerprint'", launcher)


if __name__ == '__main__':
    unittest.main()
