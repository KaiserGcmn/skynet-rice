import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / 'runtime/usr/local/libexec/nvme-shutdown-audit'
INIT = REPO / 'runtime/etc/init.d/nvme-shutdown-audit'
loader = importlib.machinery.SourceFileLoader('nvme_audit', str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
audit = importlib.util.module_from_spec(spec)
loader.exec_module(audit)


class Drive:
    """Fake smartctl: counters change only when the test says so."""

    def __init__(self, unsafe=153, cycles=401):
        self.unsafe, self.cycles = unsafe, cycles
        self.readable = True
        self.calls = []

    def run(self, command, **kwargs):
        self.calls.append(command)
        if not self.readable:
            return subprocess.CompletedProcess(command, 2, stdout='{}')
        log = {'nvme_smart_health_information_log': {
            'unsafe_shutdowns': self.unsafe, 'power_cycles': self.cycles}}
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(log))

    def power_cycle(self, unsafe=False):
        self.cycles += 1
        self.unsafe += 1 if unsafe else 0


class AuditTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='nvme-audit-test-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.state = root / 'lib/nvme-shutdown.json'
        self.history = root / 'log/history.log'
        self.drive = Drive()
        self.boot = 'boot-1'
        self.messages = []

    def read(self):
        return audit.counters(run=self.drive.run)

    def boot_up(self):
        return audit.on_boot(self.state, self.history, read=self.read,
                             log=self.messages.append, current=lambda: self.boot)

    def shut_down(self, kind='poweroff'):
        return audit.on_stop(kind, self.state, read=self.read,
                             current=lambda: self.boot)

    def next_boot(self, name, unsafe=False):
        self.drive.power_cycle(unsafe)
        self.boot = name

    def test_first_run_only_records_a_baseline(self):
        self.assertEqual(self.boot_up(), 'first-run')
        self.assertIn('Unsafe Shutdowns=153', self.messages[-1])
        self.assertEqual(json.loads(self.state.read_text())['phase'], 'booted')

    def test_clean_poweroff_and_reboot(self):
        self.boot_up()
        for name, kind in (('boot-2', 'poweroff'), ('boot-3', 'reboot')):
            self.shut_down(kind)
            self.next_boot(name)
            self.assertEqual(self.boot_up(), 'clean')
            self.assertIn(f'previous {kind}', self.messages[-1])

    def test_orderly_shutdown_with_counter_growth_is_unsafe(self):
        self.boot_up()
        self.shut_down('reboot')
        self.next_boot('boot-2', unsafe=True)
        self.assertEqual(self.boot_up(), 'unsafe')
        self.assertIn('previous reboot', self.messages[-1])
        self.assertIn('+1', self.messages[-1])

    def test_missing_stop_record_means_forced_off_or_crash(self):
        self.boot_up()
        self.next_boot('boot-2', unsafe=True)   # power button held
        self.assertEqual(self.boot_up(), 'no-record')
        self.assertIn('without an orderly shutdown', self.messages[-1])
        self.assertIn('+1', self.messages[-1])

    def test_one_verdict_per_boot(self):
        self.boot_up()
        self.assertEqual(self.boot_up(), 'already_checked')
        self.assertEqual(len(self.messages), 1)

    def test_unreadable_smart_gives_no_false_verdict(self):
        self.boot_up()
        self.shut_down()
        self.next_boot('boot-2', unsafe=True)
        self.drive.readable = False
        self.assertEqual(self.boot_up(), 'unknown')
        self.drive.readable = True
        self.shut_down()
        self.next_boot('boot-3')
        # The stop record re-reads the counters, so the next verdict is real.
        self.assertEqual(self.boot_up(), 'clean')

    def test_corrupt_state_is_treated_as_first_run(self):
        self.state.parent.mkdir(parents=True)
        self.state.write_text('{not json')
        self.assertEqual(self.boot_up(), 'first-run')

    def test_history_is_bounded(self):
        for index in range(audit.HISTORY_LINES + 25):
            audit.append_history(self.history, f'line {index}')
        lines = self.history.read_text().splitlines()
        self.assertEqual(len(lines), audit.HISTORY_LINES)
        self.assertEqual(lines[-1], f'line {audit.HISTORY_LINES + 24}')

    def test_smart_access_is_read_only(self):
        self.boot_up()
        self.shut_down()
        for command in self.drive.calls:
            self.assertEqual(command, [audit.SMARTCTL, '-j', '-A', audit.DEVICE])

    def test_state_write_is_atomic(self):
        self.boot_up()
        self.assertFalse(self.state.with_name(self.state.name + '.tmp').exists())


class InitScriptTest(unittest.TestCase):
    def test_posix_syntax_and_lsb_header(self):
        subprocess.run(['sh', '-n', str(INIT)], check=True)
        text = INIT.read_text()
        self.assertIn('### BEGIN INIT INFO', text)
        self.assertIn('### END INIT INFO', text)
        self.assertRegex(text, r'Default-Stop:\s+0 6')
        # Stop must run while / is still mounted read-write.
        self.assertRegex(text, r'Required-Stop:\s+\$local_fs')

    def run_init(self, action, runlevel):
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'helper'
            record = Path(directory) / 'called'
            fake.write_text(f'#!/bin/sh\necho "$@" > {record}\n')
            fake.chmod(0o755)
            script = INIT.read_text().replace(
                'HELPER=/usr/local/libexec/nvme-shutdown-audit',
                f'HELPER={fake}')
            env = dict(os.environ, PATH='/usr/bin:/bin')
            env.pop('RUNLEVEL', None)
            if runlevel is not None:
                env['RUNLEVEL'] = runlevel
            subprocess.run(['sh', '-c', script, 'init', action], env=env,
                           check=True, timeout=10)
            return record.read_text().strip() if record.exists() else None

    def test_stop_records_only_real_shutdowns(self):
        self.assertEqual(self.run_init('stop', '0'), '--record-stop poweroff')
        self.assertEqual(self.run_init('stop', '6'), '--record-stop reboot')
        self.assertIsNone(self.run_init('stop', '2'))

    def test_start_is_detached(self):
        self.assertRegex(INIT.read_text(), re.compile(
            r'start\)\s*\n\s*setsid "\$HELPER" --boot .*&'))


if __name__ == '__main__':
    unittest.main()
