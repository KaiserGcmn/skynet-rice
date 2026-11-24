"""System files that the restore guide installs by hand must stay valid and consistent."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
ETC = ROOT / 'runtime/etc'
INIT_SCRIPTS = ('greetd', 'host-firewall', 'zram-swap')


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

    def test_default_files_are_shell_syntax_and_keep_the_machine_values(self):
        expected = {
            'zramswap': {'ALGO': 'lz4', 'SIZE': '4096', 'PRIORITY': '100'},
            'dbus': {'IDTYPE': 'FIXED'},
            'keyboard': {'XKBLAYOUT': 'tr'},
        }
        for name, wanted in expected.items():
            path = ETC / 'default' / name
            with self.subTest(file=name):
                subprocess.run(['sh', '-n', str(path)], check=True)
                found = {}
                for line in path.read_text().splitlines():
                    if line.strip() and not line.lstrip().startswith('#'):
                        key, value = re.fullmatch(r'([A-Z_]+)=("?)([^"]*)\2', line).group(1, 3)
                        found[key] = value
                for key, value in wanted.items():
                    self.assertEqual(found.get(key), value)

    def test_xwrapper_allows_only_the_console_user(self):
        lines = [line for line in (ETC / 'X11/Xwrapper.config').read_text().splitlines()
                 if line.strip() and not line.startswith('#')]
        self.assertEqual(lines, ['allowed_users=console'])


class MachinePatchTest(unittest.TestCase):
    patch = ROOT / 'profiles/devuan/devuan-source.patch'

    def test_patch_only_touches_tracked_sources_and_names_no_one(self):
        text = self.patch.read_text()
        files = re.findall(r'(?m)^diff --git a/(\S+) b/', text)
        self.assertTrue(files)
        for name in files:
            with self.subTest(file=name):
                self.assertTrue(name.startswith('sources/'))
                self.assertTrue((ROOT / name).is_file())
        self.assertNotRegex(text, r'/home/[A-Za-z]')

    def test_patch_applies_cleanly_to_the_tracked_sources(self):
        if not shutil.which('git') or not (ROOT / '.git').exists():
            self.skipTest('requires a git checkout')
        result = subprocess.run(['git', 'apply', '--check', str(self.patch)],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


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

    def test_hand_installed_system_files_are_covered_by_the_guide(self):
        section = self.guide.split(self.heading)[1]
        for relative in ('init.d/host-firewall', 'init.d/zram-swap', 'init.d/greetd',
                         'cron.weekly/weekly-fstrim', 'sysctl.d/99-zram.conf',
                         'apt/apt.conf.d/20auto-upgrades', 'default/zramswap',
                         'default/dbus', 'default/keyboard', 'X11/Xwrapper.config'):
            with self.subTest(file=relative):
                self.assertTrue((ETC / relative).is_file())
                self.assertIn(relative, section)


if __name__ == '__main__':
    unittest.main()
