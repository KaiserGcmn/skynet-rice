"""The AMOLED theme is true black, code-free and reproducible."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/vscode-amoled-theme'
THEME = SOURCE / 'themes/skynet-amoled-black-color-theme.json'
BUILTIN = Path('/usr/share/code/resources/app/extensions/theme-defaults/themes')
HEX = re.compile(r'^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$')
GREY_SURFACES = {'#191a1b', '#121314', '#181818', '#1f1f1f', '#202122', '#242526', '#2a2b2c'}
BLACK_SURFACES = (
    'editor.background', 'editorGutter.background', 'sideBar.background', 'activityBar.background',
    'panel.background', 'titleBar.activeBackground', 'titleBar.inactiveBackground',
    'statusBar.background', 'statusBar.noFolderBackground', 'tab.activeBackground',
    'tab.inactiveBackground', 'editorGroupHeader.tabsBackground', 'terminal.background',
    'breadcrumb.background', 'minimap.background', 'peekViewEditor.background')


def load_module(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ThemeFileTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theme = json.loads(THEME.read_text(encoding='utf-8'))
        cls.package = json.loads((SOURCE / 'package.json').read_text(encoding='utf-8'))

    def test_all_colours_are_valid_hex(self):
        for key, value in self.theme['colors'].items():
            self.assertRegex(value, HEX, key)

    def test_main_surfaces_are_true_black(self):
        for key in BLACK_SURFACES:
            self.assertEqual(self.theme['colors'][key].lower(), '#000000', key)

    def test_no_grey_surface_of_the_base_theme_is_left(self):
        for key, value in self.theme['colors'].items():
            self.assertNotIn(value.lower(), GREY_SURFACES, key)

    def test_accents_are_red_not_the_base_blue(self):
        colors = self.theme['colors']
        self.assertEqual(colors['button.background'], '#94313C')
        self.assertEqual(colors['tab.activeBorderTop'], '#C6535C')
        self.assertEqual(colors['focusBorder'], '#A84952')
        self.assertNotIn('#297AA0', colors.values())

    def test_syntax_highlighting_is_kept(self):
        self.assertEqual(self.theme['type'], 'dark')
        self.assertTrue(self.theme['semanticHighlighting'])
        self.assertGreater(len(self.theme['tokenColors']), 100)
        self.assertTrue(self.theme['semanticTokenColors'])

    def test_package_is_a_theme_without_code(self):
        self.assertEqual(self.package['categories'], ['Themes'])
        for key in ('main', 'browser', 'activationEvents', 'scripts', 'dependencies'):
            self.assertNotIn(key, self.package)
        (entry,) = self.package['contributes']['themes']
        self.assertEqual(entry['label'], self.theme['name'])
        self.assertEqual(entry['uiTheme'], 'vs-dark')
        self.assertEqual((SOURCE / entry['path']).resolve(), THEME.resolve())

    @unittest.skipUnless(BUILTIN.is_dir(), 'VS Code built-in themes are unavailable')
    def test_committed_theme_matches_the_generator(self):
        generator = load_module(SOURCE / 'generate-theme.py', 'generate_theme')
        expected = generator.build(BUILTIN)
        self.assertEqual(self.theme['tokenColors'], expected['tokenColors'],
                         'syntax rules drifted; rerun generate-theme.py')
        self.assertEqual(self.theme['semanticTokenColors'], expected['semanticTokenColors'])
        self.assertEqual(self.theme['colors'], expected['colors'])


class PackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_module(ROOT / 'scripts/build-vscode-theme.py', 'build_vscode_theme')

    def test_vsix_is_complete_and_reproducible(self):
        with tempfile.TemporaryDirectory(prefix='vsix-test-') as work:
            first = self.builder.build(Path(work) / 'a')
            second = self.builder.build(Path(work) / 'b')
            self.assertEqual(first.name, 'skynet-amoled-black-0.1.0.vsix')
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(sorted(archive.namelist()), [
                    '[Content_Types].xml', 'extension.vsixmanifest', 'extension/NOTICE.md',
                    'extension/package.json',
                    'extension/themes/skynet-amoled-black-color-theme.json'])
                self.assertEqual(archive.read('extension/package.json'),
                                 (SOURCE / 'package.json').read_bytes())
                self.assertEqual(archive.read('extension/themes/skynet-amoled-black-color-theme.json'),
                                 THEME.read_bytes())
                manifest = ET.fromstring(archive.read('extension.vsixmanifest'))
                ET.fromstring(archive.read('[Content_Types].xml'))
        ns = {'v': 'http://schemas.microsoft.com/developer/vsx-schema/2011'}
        identity = manifest.find('v:Metadata/v:Identity', ns)
        self.assertEqual(identity.get('Id'), 'skynet-amoled-black')
        self.assertEqual(identity.get('Publisher'), 'skynet-rice')

    def test_third_party_notice_is_shipped(self):
        notice = (SOURCE / 'NOTICE.md').read_text(encoding='utf-8')
        self.assertIn('Microsoft Corporation', notice)
        self.assertIn('MIT', notice)


if __name__ == '__main__':
    unittest.main()
