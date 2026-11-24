import colorsys
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'build_icon_theme', Path(__file__).resolve().parents[1] / 'scripts/build-icon-theme.py')
icons = importlib.util.module_from_spec(spec)
spec.loader.exec_module(icons)

BLUE = '<svg><style>.ColorScheme-Highlight { color: #3daee9; }</style></svg>'
GREEN = '<svg><path style="fill:#27ae60"/></svg>'
PLAIN = '<svg><style>.ColorScheme-Text { color: #fcfcfc; }</style></svg>'
INDEX = """[Icon Theme]
Name=Source
Name[tr]=Kaynak

Comment=Source theme
Comment[de]=Quelle
Inherits=breeze,hicolor
Directories=places/64

[places/64]
Size=64
"""


def hls(value):
    red, green, blue = (int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    return hue * 360, lightness, saturation


def shifted(color):
    return icons.recolour('<path fill="%s"/>' % color, '#b02a30').split('"')[1]


class PaletteTest(unittest.TestCase):
    def test_accent_becomes_the_configured_colour_exactly(self):
        self.assertEqual(shifted('#3DAEE9'), '#b02a30')

    def test_greys_white_and_black_are_untouched(self):
        for color in ('#fcfcfc', '#232629', '#000000', '#ffffff', '#808080', '#eff0f1'):
            self.assertEqual(shifted(color), color)

    def test_saturated_colours_move_to_the_red_family_and_keep_their_order(self):
        results = {}
        for name, color in {'green': '#27ae60', 'orange': '#f67400', 'yellow': '#fdbc4b',
                            'purple': '#aa478a', 'blue': '#2980b9', 'light blue': '#20bcfa'}.items():
            hue, lightness, saturation = hls(shifted(color))
            self.assertTrue(hue >= 350 or hue <= 5, (name, hue))
            self.assertLessEqual(saturation, 0.63, name)
            results[name] = lightness
        self.assertLess(results['blue'], results['light blue'])
        self.assertLess(results['green'], results['yellow'])

    def test_soft_tints_become_steel_grey(self):
        for color in ('#bdb49e', '#383e51'):
            hue, _lightness, saturation = hls(shifted(color))
            self.assertAlmostEqual(hue, 210, delta=3)
            self.assertLess(saturation, 0.10)
            self.assertEqual(hls(color)[1].__round__(2), hls(shifted(color))[1].__round__(2))

    def test_ids_and_urls_that_look_like_hex_are_not_colours(self):
        text = '<use href="#27ae60abc"/><stop id="a" style="stop-color:#27ae60"/>'
        result = icons.recolour(text, '#b02a30')
        self.assertIn('#27ae60abc', result)
        self.assertNotIn('stop-color:#27ae60', result)


class IconThemeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source = root / 'source'
        self.target = root / 'out' / 'source-red'
        places = self.source / 'places/64'
        places.mkdir(parents=True)
        (self.source / 'index.theme').write_text(INDEX)
        (places / 'folder.svg').write_text(BLUE)
        (places / 'text.svg').write_text(PLAIN)
        (places / 'ok.svg').write_text(GREEN)
        (places / 'folder-alias.svg').symlink_to('folder.svg')
        (self.source / 'places/64@2x').symlink_to('64')

    def test_accent_is_replaced_and_other_icons_are_left_to_the_source(self):
        count = icons.build(self.source, self.target, '#b02a30')
        folder = (self.target / 'places/64/folder.svg').read_text()
        self.assertEqual(count, 3)
        ok = (self.target / 'places/64/ok.svg').read_text()
        self.assertNotIn('27ae60', ok)
        self.assertIn('#b02a30', folder)
        self.assertNotIn('3daee9', folder)
        self.assertFalse((self.target / 'places/64/text.svg').exists())
        self.assertEqual((self.source / 'places/64/folder.svg').read_text(), BLUE)

    def test_symlinked_aliases_become_recoloured_files_and_directory_links_survive(self):
        icons.build(self.source, self.target, '#b02a30')
        alias = self.target / 'places/64/folder-alias.svg'
        self.assertFalse(alias.is_symlink())
        self.assertIn('#b02a30', alias.read_text())
        self.assertEqual(os.readlink(self.target / 'places/64@2x'), '64')

    def test_index_inherits_the_source_and_drops_translations(self):
        icons.build(self.source, self.target, '#b02a30')
        index = (self.target / 'index.theme').read_text()
        self.assertIn('Name=Breeze Dark Red', index)
        self.assertIn('Inherits=source,breeze,hicolor', index)
        self.assertIn('X-Recolored-From=source', index)
        self.assertIn('Directories=places/64', index)
        self.assertIn('[places/64]', index)
        self.assertNotIn('Name[tr]', index)
        self.assertNotIn('Comment[de]', index)

    def test_repeat_run_replaces_its_own_output_only(self):
        icons.build(self.source, self.target, '#b02a30')
        icons.build(self.source, self.target, '#112233')
        self.assertIn('#112233', (self.target / 'places/64/folder.svg').read_text())
        self.assertFalse(self.target.with_name(self.target.name + '.old').exists())
        stranger = self.target.parent / 'stranger'
        stranger.mkdir()
        (stranger / 'index.theme').write_text('[Icon Theme]\nName=Mine\n')
        with self.assertRaises(ValueError):
            icons.build(self.source, stranger, '#b02a30')
        self.assertTrue((stranger / 'index.theme').exists())

    def test_invalid_input_is_rejected_without_leaving_files(self):
        for color in ('red', '#12345', '#12345g'):
            with self.assertRaises(ValueError):
                icons.build(self.source, self.target, color)
        with self.assertRaises(ValueError):
            icons.build(self.source, self.source, '#b02a30')
        (self.source / 'places/64/folder.svg').write_text(PLAIN)
        (self.source / 'places/64/ok.svg').write_text(PLAIN)
        (self.source / 'places/64/folder-alias.svg').unlink()
        with self.assertRaises(ValueError):
            icons.build(self.source, self.target, '#b02a30')
        self.assertEqual(list(self.target.parent.glob('*')) if self.target.parent.exists() else [], [])


if __name__ == '__main__':
    unittest.main()
