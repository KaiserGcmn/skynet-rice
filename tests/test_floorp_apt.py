"""Floorp's apt repository: trusted key, floorp-only pin, unattended updates."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

APT = Path(__file__).resolve().parents[1] / 'runtime/etc/apt'
SOURCES = APT / 'sources.list.d/floorp-ppa.sources'
PREFERENCES = APT / 'preferences.d/floorp-ppa'
UNATTENDED = APT / 'apt.conf.d/99floorp-ppa'
FINGERPRINT = 'A8C20FCDD57739941A813D5D8F64DCC7C806D572'


class FloorpAptTest(unittest.TestCase):
    def test_source_uses_https_and_an_embedded_key(self):
        text = SOURCES.read_text()
        self.assertNotIn('\r', text)
        self.assertIn('URIs: https://ppa.floorp.app/amd64/\n', text)
        self.assertIn('Suites: ./\n', text)
        self.assertNotIn('Components:', text)
        self.assertIn('Signed-By:\n -----BEGIN PGP PUBLIC KEY BLOCK-----\n .\n', text)
        self.assertTrue(text.endswith(' -----END PGP PUBLIC KEY BLOCK-----\n'))
        self.assertNotIn('PRIVATE', text)

    def test_embedded_key_is_the_floorp_signing_key(self):
        if not shutil.which('gpg'):
            self.skipTest('gpg is not installed')
        lines = SOURCES.read_text().splitlines()
        start = lines.index(' -----BEGIN PGP PUBLIC KEY BLOCK-----')
        armor = '\n'.join('' if l == ' .' else l[1:] for l in lines[start:]) + '\n'
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                ['gpg', '--homedir', home, '--show-keys', '--with-colons'],
                input=armor, capture_output=True, text=True, check=True)
        fingerprints = [l.split(':')[9] for l in result.stdout.splitlines()
                        if l.startswith('fpr:')]
        self.assertEqual(fingerprints[0], FINGERPRINT)
        self.assertIn(' '.join(FINGERPRINT[i:i + 4] for i in range(0, 20, 4)),
                      SOURCES.read_text())

    def test_repository_may_only_provide_floorp(self):
        stanzas = [dict(line.split(': ', 1) for line in block.splitlines()
                        if line and not line.startswith('#'))
                   for block in PREFERENCES.read_text().split('\n\n')]
        self.assertEqual(stanzas, [
            {'Package': '*', 'Pin': 'origin "ppa.floorp.app"', 'Pin-Priority': '-1'},
            {'Package': 'floorp', 'Pin': 'origin "ppa.floorp.app"', 'Pin-Priority': '500'},
        ])

    def test_unattended_pattern_is_read_after_the_list_is_cleared(self):
        # 99expertbook-security-upgrades starts with "#clear ...Origins-Pattern".
        self.assertGreater(UNATTENDED.name, '99expertbook-security-upgrades')
        self.assertIn('"site=ppa.floorp.app";', UNATTENDED.read_text())
        self.assertNotIn('#clear', UNATTENDED.read_text())


if __name__ == '__main__':
    unittest.main()
