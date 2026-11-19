"""USB-C UCSI boot recovery checks using a disposable sysfs/proc tree."""
import importlib.machinery
import importlib.util
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / 'runtime/usr/local/libexec/expertbook-ucsi-recover'
INIT = REPO / 'runtime/etc/init.d/expertbook-ucsi-recover'
loader = importlib.machinery.SourceFileLoader('ucsi_recover', str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
ucsi = importlib.util.module_from_spec(spec)
loader.exec_module(ucsi)


class Machine:
    """Fake sysfs/proc whose USB-C ports appear or vanish like the real one."""

    def __init__(self, root, model=ucsi.MODEL, bound=True, ports=0, up=40.0):
        self.sys = root / 'sys'
        self.proc = root / 'proc'
        (self.sys / 'class/dmi/id').mkdir(parents=True)
        (self.sys / 'class/dmi/id/product_name').write_text(model + '\n')
        (self.sys / 'class/typec').mkdir(parents=True)
        self.device = self.sys / 'devices/platform/USBC000:00'
        (self.device / 'typec').mkdir(parents=True)
        (self.sys / 'bus/platform/devices').mkdir(parents=True)
        (self.sys / 'bus/platform/devices/USBC000:00').symlink_to(self.device)
        self.driver = self.sys / 'bus/platform/drivers/ucsi_acpi'
        self.driver.mkdir(parents=True)
        (self.proc / 'sys/kernel/random').mkdir(parents=True)
        (self.proc / 'sys/kernel/random/boot_id').write_text('boot-1\n')
        self.set_uptime(up)
        if bound:
            (self.device / 'driver').symlink_to(self.driver)
        self.set_ports(ports)
        self.calls = []
        self.ports_after_reload = 2
        self.fail = None

    def set_uptime(self, value):
        (self.proc / 'uptime').write_text(f'{value:.2f} 1.00\n')

    def set_ports(self, count):
        for link in (self.sys / 'class/typec').iterdir():
            link.unlink()
        for port in (self.device / 'typec').iterdir():
            port.rmdir()
        for index in range(count):
            target = self.device / 'typec' / f'port{index}'
            target.mkdir()
            (self.sys / 'class/typec' / f'port{index}').symlink_to(target)

    def sleep(self, seconds):
        uptime = float((self.proc / 'uptime').read_text().split()[0])
        self.set_uptime(uptime + seconds)

    def modprobe(self, *args):
        self.calls.append(args)
        if self.fail == args:
            return False, 'FATAL: Module ucsi_acpi is in use.'
        if args == (ucsi.MODULE,):
            self.set_ports(self.ports_after_reload)
        return True, ''


class UcsiRecoverTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='skynet-ucsi-test-')
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.marker = self.root / 'run-marker'
        self.messages = []

    def run_recover(self, machine):
        return ucsi.recover(machine.sys, machine.proc, self.marker,
                            run=machine.modprobe, sleep=machine.sleep,
                            say=self.messages.append)

    def test_healthy_boot_never_touches_the_driver(self):
        machine = Machine(self.root, ports=2)
        self.assertEqual(self.run_recover(machine), 'ready')
        self.assertEqual(machine.calls, [])

    def test_bound_without_ports_reloads_once_and_recovers(self):
        machine = Machine(self.root, ports=0)
        self.assertEqual(self.run_recover(machine), 'recovered')
        self.assertEqual(machine.calls, [('-r', 'ucsi_acpi'), ('ucsi_acpi',)])

    def test_only_one_attempt_per_boot(self):
        machine = Machine(self.root, ports=0)
        machine.ports_after_reload = 0
        self.assertEqual(self.run_recover(machine), 'not_recovered')
        self.assertEqual(self.run_recover(machine), 'already_checked')
        self.assertEqual(len(machine.calls), 2)

    def test_new_boot_id_allows_a_new_check(self):
        machine = Machine(self.root, ports=0)
        self.run_recover(machine)
        (machine.proc / 'sys/kernel/random/boot_id').write_text('boot-2\n')
        machine.set_ports(0)
        self.assertEqual(self.run_recover(machine), 'recovered')

    def test_waits_for_settle_and_accepts_late_registration(self):
        machine = Machine(self.root, ports=0, up=8.0)
        original = machine.sleep

        def sleep(seconds):
            original(seconds)
            if float((machine.proc / 'uptime').read_text().split()[0]) >= 14:
                machine.set_ports(2)
        machine.sleep = sleep
        self.assertEqual(self.run_recover(machine), 'ready')
        self.assertEqual(machine.calls, [])

    def test_early_start_waits_until_settled_before_reloading(self):
        machine = Machine(self.root, ports=0, up=5.0)
        self.assertEqual(self.run_recover(machine), 'recovered')
        uptime = float((machine.proc / 'uptime').read_text().split()[0])
        self.assertGreaterEqual(uptime, ucsi.SETTLE_UPTIME)

    def test_unbound_driver_is_never_loaded(self):
        machine = Machine(self.root, bound=False)
        self.assertEqual(self.run_recover(machine), 'left_unchanged')
        self.assertEqual(machine.calls, [])

    def test_other_model_is_left_alone(self):
        machine = Machine(self.root, model='OTHER LAPTOP', ports=0)
        self.assertEqual(self.run_recover(machine), 'left_unchanged')
        self.assertEqual(machine.calls, [])

    def test_unload_failure_does_not_load_or_retry(self):
        machine = Machine(self.root, ports=0)
        machine.fail = ('-r', 'ucsi_acpi')
        self.assertEqual(self.run_recover(machine), 'unload_failed')
        self.assertEqual(machine.calls, [('-r', 'ucsi_acpi')])
        self.assertIn('in use', self.messages[-1])

    def test_status_observation_is_read_only(self):
        machine = Machine(self.root, ports=2)
        before = sorted(str(path) for path in self.root.rglob('*'))
        self.assertEqual(ucsi.observe(machine.sys), ('ready', ['port0', 'port1']))
        self.assertEqual(sorted(str(path) for path in self.root.rglob('*')), before)


class InitScriptTest(unittest.TestCase):
    def test_posix_syntax_and_lsb_header(self):
        subprocess.run(['sh', '-n', str(INIT)], check=True)
        text = INIT.read_text()
        header = re.search(r'### BEGIN INIT INFO\n(.*?)### END INIT INFO', text, re.S)
        self.assertIsNotNone(header)
        self.assertIn('# Provides:          expertbook-ucsi-recover', header.group(1))
        self.assertIn('# Default-Start:     2 3 4 5', header.group(1))

    def test_start_is_detached_so_boot_is_not_delayed(self):
        start = INIT.read_text().split('start)', 1)[1].split(';;', 1)[0]
        self.assertIn('--boot', start)
        self.assertTrue(start.strip().endswith('&'))


if __name__ == '__main__':
    unittest.main()
