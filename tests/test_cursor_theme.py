"""SKYNET HUD cursor theme: every size, hotspot, animation and alias."""
import importlib.machinery
import importlib.util
import math
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/skynet-cursor/render-cursors.py'

try:
    import cairo  # noqa: F401
    HAVE_TOOLS = shutil.which('xcursorgen') is not None
except ImportError:
    HAVE_TOOLS = False


def images(path):
    """(nominal size, width, height, xhot, yhot, delay, BGRA bytes) per image."""
    data = path.read_bytes()
    assert data[:4] == b'Xcur'
    count = struct.unpack('<I', data[12:16])[0]
    found = []
    for index in range(count):
        kind, subtype, position = struct.unpack('<III', data[16 + index * 12:28 + index * 12])
        if kind != 0xfffd0002:
            continue
        fields = struct.unpack('<IIIIIIIII', data[position:position + 36])
        width, height, xhot, yhot, delay = fields[4:9]
        found.append((subtype, width, height, xhot, yhot, delay,
                      data[position + 36:position + 36 + width * height * 4]))
    return found


@unittest.skipUnless(HAVE_TOOLS, 'requires pycairo and xcursorgen')
class CursorThemeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = importlib.machinery.SourceFileLoader('render_cursors', str(SOURCE))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        cls.module = importlib.util.module_from_spec(spec)
        loader.exec_module(cls.module)
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-cursor-test-')
        cls.theme = Path(cls.work.name) / 'Skynet'
        with tempfile.TemporaryDirectory() as scratch:
            cls.module.build(cls.theme, Path(scratch))

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_every_cursor_has_all_sizes_and_hotspots_inside(self):
        for name in self.module.CURSORS:
            found = images(self.theme / 'cursors' / name)
            self.assertEqual(sorted({image[0] for image in found}),
                             list(self.module.SIZES), name)
            for size, width, height, xhot, yhot, _, _ in found:
                self.assertEqual((width, height), (size, size), name)
                self.assertLess(xhot, width)
                self.assertLess(yhot, height)

    def test_spinners_are_animated_and_others_static(self):
        for name, (_, _, animated) in self.module.CURSORS.items():
            found = images(self.theme / 'cursors' / name)
            expected = self.module.SPIN_FRAMES if animated else 1
            self.assertEqual(len(found), expected * len(self.module.SIZES), name)
            if animated:
                self.assertEqual({image[5] for image in found}, {self.module.SPIN_DELAY})

    def test_arrow_tip_sits_on_the_hotspot(self):
        for size, width, _, xhot, yhot, _, pixels in images(self.theme / 'cursors/left_ptr'):
            alpha = lambda x, y: pixels[(y * width + x) * 4 + 3]
            self.assertGreater(alpha(xhot, yhot), 200, size)
            # Only the dark outline (half its 2.65-unit width) may sit above
            # the click point; the red rim itself starts at the hotspot.
            allowance = math.ceil(1.4 * size / 32)
            for y in range(0, max(0, yhot - allowance)):
                for x in range(width):
                    self.assertLess(alpha(x, y), 128, (size, x, y))

    def test_aliases_resolve_to_rendered_files(self):
        cursors = self.theme / 'cursors'
        for alias, target in self.module.ALIASES.items():
            link = cursors / alias
            self.assertTrue(link.is_symlink(), alias)
            self.assertIn(target, self.module.CURSORS)
            self.assertTrue(link.resolve().is_file(), alias)
        for name in ('default', 'pointer', 'text', 'wait', 'progress', 'not-allowed'):
            self.assertIn(name, self.module.ALIASES)
        self.assertIn('Inherits=breeze_cursors', (self.theme / 'index.theme').read_text())


if __name__ == '__main__':
    unittest.main()
