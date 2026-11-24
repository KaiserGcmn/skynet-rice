"""System files that the restore guide installs by hand must stay valid and consistent."""
from pathlib import Path
import os
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
ETC = ROOT / 'runtime/etc'
INIT_SCRIPTS = ('host-firewall', 'zram-swap')


class InitScriptsTest(unittest.TestCase):
    def test_scripts_are_valid_sh_executable_and_carry_an_lsb_header(self):
        for name in INIT_SCRIPTS:
            path = ETC / 'init.d' / name
            with self.subTest(script=name):
                subprocess.run(['sh', '-n', str(path)], check=True)
                self.assertTrue(os.access(path, os.X_OK))
                text = path.read_text()
                header = text.split('### BEGIN INIT INFO')[1].split('### END INIT INFO')[0]
                self.assertRegex(header, rf'(?m)^# Provides:\s+{re.escape(name)}$')
                for field in ('Required-Start', 'Required-Stop', 'Default-Start',
                              'Default-Stop', 'Short-Description'):
                    self.assertIn(f'# {field}:', header)

    def test_firewall_loads_the_tracked_ruleset_and_manages_its_own_table(self):
        script = (ETC / 'init.d/host-firewall').read_text()
        ruleset = (ROOT / 'profiles/debian/rootfs/etc/nftables.conf').read_text()
        self.assertIn('--check --file /etc/nftables.conf', script)
        table = re.search(r'table inet (\w+)', ruleset).group(1)
        self.assertIn(f'destroy table inet {table}', script)

    def test_weekly_trim_is_valid_sh_executable_and_never_blocks(self):
        path = ETC / 'cron.weekly/weekly-fstrim'
        subprocess.run(['sh', '-n', str(path)], check=True)
        self.assertTrue(os.access(path, os.X_OK))
        text = path.read_text()
        for needle in ('flock -n', 'ionice -c 3', 'nice -n 19', '--quiet-unsupported'):
            self.assertIn(needle, text)


class ConfigFilesTest(unittest.TestCase):
    def test_zram_sysctl_lines_are_key_value_pairs(self):
        values = {}
        for line in (ETC / 'sysctl.d/99-zram.conf').read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, value = re.fullmatch(r'([a-z_.-]+) = (\d+)', line).groups()
                values[key] = int(value)
        self.assertEqual(values, {'vm.swappiness': 100, 'vm.page-cluster': 0})

    def test_auto_upgrade_lines_are_terminated_apt_options(self):
        for line in (ETC / 'apt/apt.conf.d/20auto-upgrades').read_text().splitlines():
            self.assertRegex(line, r'^APT::Periodic::[A-Za-z-]+ "\d+";$')


class RestoreGuideTest(unittest.TestCase):
    guide = (ROOT / 'docs/RESTORE.md').read_text()
    heading = '## Sistem hizmetleri ve kullanıcıya özel dosyalar'

    def test_sudoers_files_are_validated_before_they_are_installed(self):
        section = self.guide.split(self.heading)[1]
        for name in ('90-no-mail', '99-pwfeedback'):
            self.assertIn(f'/etc/sudoers.d/{name}', section)
        self.assertEqual(section.count('visudo -cf "$T" && sudo install -m 0440'), 2)
        self.assertIn('Defaults !mail_badpass', section)
        self.assertIn('Defaults:$USER pwfeedback', section)

    def test_user_specific_files_use_variables_instead_of_a_real_login_name(self):
        section = self.guide.split(self.heading)[1]
        self.assertIn('su $USER $USER', section)
        self.assertIn('$HOME/.local/state/skynet-rice/session.log', section)
        self.assertNotRegex(section, r'/home/[A-Za-z]')


if __name__ == '__main__':
    unittest.main()
