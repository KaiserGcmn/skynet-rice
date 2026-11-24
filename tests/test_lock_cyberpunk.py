import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / 'sources/xsecurelock-style'
GENERATOR = STYLE / 'render-cyberpunk.py'
BASE = STYLE / 'skynet-base.png'
INSTALLED = ROOT / 'home/.local/share/xsecurelock-style/background.png'


def load_generator():
    spec = importlib.util.spec_from_file_location('render_cyberpunk', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def have_renderer():
    try:
        import cairo  # noqa: F401
        import gi
        gi.require_version('PangoCairo', '1.0')
        from gi.repository import PangoCairo  # noqa: F401
        from PIL import Image  # noqa: F401
    except (ImportError, ValueError):
        return False
    return True


@unittest.skipUnless(have_renderer(), 'cairo, PangoCairo and Pillow are required')
class CyberpunkLockBackgroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PIL import Image
        cls.generator = load_generator()
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / 'background.png'
        subprocess.run([sys.executable, '-I', str(GENERATOR), str(BASE), str(out)],
                       check=True)
        cls.base = Image.open(BASE).convert('RGB')
        cls.out = Image.open(out).convert('RGB')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_size_matches_saver_logo_requirement(self):
        # saver-lock-style only animates the emblem on 1920x1200 artwork.
        self.assertEqual(self.out.size, (1920, 1200))

    def test_skynet_artwork_and_live_areas_are_unchanged(self):
        for box in self.generator.PROTECTED:
            with self.subTest(box=box):
                self.assertEqual(self.base.crop(box).tobytes(),
                                 self.out.crop(box).tobytes())

    def test_hud_is_drawn_in_margins(self):
        for box in ((40, 90, 520, 880), (1400, 90, 1880, 880), (40, 1120, 1380, 1180)):
            with self.subTest(box=box):
                self.assertNotEqual(self.base.crop(box).tobytes(),
                                    self.out.crop(box).tobytes())

    def test_repository_background_is_generated_output(self):
        from PIL import Image
        installed = Image.open(INSTALLED).convert('RGB')
        self.assertEqual(installed.tobytes(), self.out.tobytes())



class LockBatteryLabelTest(unittest.TestCase):
    """The live battery label mirrors the artwork's top-left caption."""

    def define(self, name):
        import re
        source = (STYLE / 'saver-lock-style.c').read_text()
        match = re.search(r'^#define %s (.+)$' % name, source, re.M)
        self.assertIsNotNone(match, name)
        return match.group(1)

    def test_label_mirrors_the_top_left_caption(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow is required')
        art = Image.open(INSTALLED).convert('RGB')
        px = art.load()
        ink = [(x, y) for x in range(30, 300) for y in range(20, 48)
               if sum(px[x, y]) > 150]
        left = min(x for x, _ in ink)
        bottom = max(y for _, y in ink)
        self.assertEqual(int(self.define('BATTERY_EDGE')), left)
        self.assertLessEqual(abs(int(self.define('BATTERY_BASELINE')) - bottom), 1)

    def test_label_uses_ink_width_and_header_size(self):
        source = (STYLE / 'saver-lock-style.c').read_text()
        self.assertIn('attr->width - BATTERY_EDGE - extents.width + extents.x', source)
        self.assertIn('size=10', self.define('BATTERY_FONT'))
        self.assertNotIn('attr->width - 28', source)

if __name__ == '__main__':
    unittest.main()
