from pathlib import Path
import unittest


CONF = Path(__file__).resolve().parents[1] / 'runtime/etc/sysctl.d/91-hardening.conf'


def settings():
    values = {}
    for line in CONF.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, value = line.partition('=')
        values[key.strip().lstrip('-')] = value.strip()
    return values


class SysctlHardeningTests(unittest.TestCase):
    def test_kernel_exposure_is_restricted(self):
        values = settings()
        self.assertEqual(values['kernel.kptr_restrict'], '1')
        self.assertEqual(values['kernel.yama.ptrace_scope'], '1')
        self.assertEqual(values['kernel.kexec_load_disabled'], '1')

    def test_icmp_redirects_are_off_for_current_and_future_interfaces(self):
        values = settings()
        for family in ('ipv4', 'ipv6'):
            for scope in ('default', '*'):
                self.assertEqual(values[f'net.{family}.conf.{scope}.accept_redirects'], '0')
        for scope in ('default', '*'):
            self.assertEqual(values[f'net.ipv4.conf.{scope}.send_redirects'], '0')

    def test_ipv6_lines_are_optional_so_a_missing_stack_cannot_fail_boot(self):
        for line in CONF.read_text(encoding='utf-8').splitlines():
            if line.startswith('net.ipv6.'):
                self.fail(f'IPv6 setting must carry the "-" prefix: {line}')

    def test_installed_copy_matches_the_repository(self):
        installed = Path('/etc/sysctl.d/91-hardening.conf')
        if not installed.exists():
            self.skipTest('not installed on this machine')
        self.assertEqual(installed.read_text(encoding='utf-8'), CONF.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
