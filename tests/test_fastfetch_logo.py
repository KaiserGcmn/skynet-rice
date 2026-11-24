import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'home/.config/fastfetch/config.jsonc'
LOGO = ROOT / 'home/.config/fastfetch/skynet-globe.txt'
TAG = re.compile(r'\$\d')


class FastfetchLogoTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding='utf-8'))
        self.logo = LOGO.read_text(encoding='utf-8').splitlines()

    def test_logo_is_text_not_image(self):
        logo = self.config['logo']
        self.assertEqual(logo['type'], 'file')
        self.assertEqual(logo['source'], '~/.config/fastfetch/skynet-globe.txt')
        self.assertNotIn('\x1b', LOGO.read_text(encoding='utf-8'))

    def test_logo_is_braille_dot_matrix_with_fixed_width(self):
        visible = [TAG.sub('', line) for line in self.logo]
        self.assertLessEqual(max(len(line) for line in visible), 56)
        braille = sum(1 for line in visible for ch in line if 0x2800 <= ord(ch) <= 0x28FF)
        self.assertGreater(braille, 500)
        self.assertIn('█', ''.join(visible))          # half-block SKYNET wordmark

    def test_every_logo_colour_tag_is_defined(self):
        used = {m[1:] for line in self.logo for m in TAG.findall(line)}
        self.assertTrue(used <= set(self.config['logo']['color']))

    def test_no_terminator_names_or_self_aware_row(self):
        text = (CONFIG.read_text(encoding='utf-8') + LOGO.read_text(encoding='utf-8')).upper()
        for word in ('CSM-101', 'T-800', 'CYBERDYNE', 'NORAD', 'SELF-AWARE', '1997'):
            self.assertNotIn(word, text)


if __name__ == '__main__':
    unittest.main()
