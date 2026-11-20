"""Regression checks for the terminal palette, tray icons and dmenu panel."""
from pathlib import Path
import re
import tomllib
import shutil
import subprocess
import tempfile
import unittest
import xml.dom.minidom


ROOT = Path(__file__).resolve().parents[1]
KITTY_THEME = ROOT / 'home/.config/kitty/current-theme.conf'
ICON_ROOT = ROOT / 'home/.local/share/icons/hicolor'
ICON_DIRS = ('16x16', '22x22', '24x24', '32x32', '48x48', '64x64', 'scalable')
ICON_NAMES = ('blueman-tray', 'blueman-active', 'blueman-disabled')
DMENU = ROOT / 'sources/dmenu'
KITTY_CONF = ROOT / 'home/.config/kitty/kitty.conf'
DUNSTRC = ROOT / 'home/.config/dunst/dunstrc'
BOTTOM = ROOT / 'home/.config/bottom/bottom.toml'


class KittyPaletteTest(unittest.TestCase):
    def setUp(self):
        self.settings = {}
        for line in KITTY_THEME.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split(None, 1)
            self.assertNotIn(key, self.settings, f'duplicate kitty setting {key}')
            self.settings[key] = value

    def test_all_sixteen_ansi_colors_are_defined(self):
        for index in range(16):
            value = self.settings.get(f'color{index}')
            self.assertIsNotNone(value, f'color{index} falls back to kitty defaults')
            self.assertRegex(value, r'^#[0-9a-f]{6}$')

    def test_red_matches_the_theme_signal_color(self):
        self.assertEqual(self.settings['color1'], self.settings['cursor'])

    def test_diff_colors_stay_distinguishable(self):
        def rgb(value):
            return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
        red, green = rgb(self.settings['color1']), rgb(self.settings['color2'])
        self.assertGreater(sum(abs(a - b) for a, b in zip(red, green)), 300)


class BluetoothTrayIconTest(unittest.TestCase):
    def icons(self):
        for directory in ICON_DIRS:
            for name in ICON_NAMES:
                yield ICON_ROOT / directory / 'status' / f'{name}.svg'

    def test_every_size_overrides_the_stock_png(self):
        # hicolor lists fixed sizes before scalable/, so each tray size needs a copy.
        for path in self.icons():
            self.assertTrue(path.is_file(), path)

    def test_svg_root_precedes_comments(self):
        # gdk-pixbuf failed to recognise the file when a long comment sat
        # between the XML declaration and <svg>, showing image-missing.
        for path in self.icons():
            text = path.read_text()
            self.assertRegex(text, r'^<\?xml[^>]*\?>\n<svg ', path)
            document = xml.dom.minidom.parseString(text.encode())
            self.assertEqual(document.documentElement.tagName, 'svg')

    def test_icons_are_monochrome_not_symbolic(self):
        # The dwm systray sets no _NET_SYSTEM_TRAY_COLORS, so symbolic icons draw black.
        for path in self.icons():
            fills = set(re.findall(r'fill="(#[0-9a-fA-F]{6})"', path.read_text()))
            self.assertEqual(fills, {'#fcfcfc'}, path)
        self.assertFalse(list(ICON_ROOT.rglob('*-symbolic.svg')))

    def test_icons_load_through_gdk_pixbuf(self):
        try:
            import gi
            gi.require_version('GdkPixbuf', '2.0')
            from gi.repository import GdkPixbuf
        except (ImportError, ValueError):
            self.skipTest('GdkPixbuf is unavailable')
        for path in self.icons():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(str(path), 24, 24)
            self.assertEqual(pixbuf.get_width(), 24, path)


class DmenuPanelTest(unittest.TestCase):
    def build(self, config):
        if not shutil.which('make') or not shutil.which('cc'):
            self.skipTest('C toolchain is unavailable')
        with tempfile.TemporaryDirectory(prefix='skynet-dmenu-test-') as work:
            tree = Path(work) / 'dmenu'
            shutil.copytree(DMENU, tree)
            if config == 'config.def.h':
                (tree / 'config.h').unlink()
            result = subprocess.run(['make', '-s', 'dmenu'], cwd=tree,
                                    capture_output=True, text=True)
            if result.returncode and 'X11/Xlib.h' in result.stderr:
                self.skipTest('X11 headers are unavailable')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('warning', result.stderr)
            usage = subprocess.run([tree / 'dmenu', '-h'], capture_output=True, text=True)
            self.assertIn('[-bcfiv]', usage.stderr)

    def test_live_config_builds(self):
        self.build('config.h')

    def test_upstream_default_config_builds(self):
        self.build('config.def.h')

    def test_live_config_enables_the_centred_panel(self):
        config = (DMENU / 'config.h').read_text()
        self.assertRegex(config, r'static int centered = 1;')
        self.assertRegex(config, r'static unsigned int lines\s+= 12;')
        default = (DMENU / 'config.def.h').read_text()
        self.assertRegex(default, r'static int centered = 0;')
        self.assertRegex(default, r'static unsigned int lines\s+= 0;')


class HudStylingTest(unittest.TestCase):
    def dunst_sections(self):
        sections, name = {}, None
        for line in DUNSTRC.read_text().splitlines():
            line = line.strip()
            if line.startswith('[') and line.endswith(']'):
                name = line[1:-1]
                sections[name] = {}
            elif name and '=' in line and not line.startswith('#'):
                key, value = (part.strip() for part in line.split('=', 1))
                sections[name][key] = value
        return list(sections), sections

    def test_notifications_carry_the_skynet_header(self):
        _, sections = self.dunst_sections()
        self.assertIn('SKYNET // %a', sections['global']['format'])
        self.assertIn('LOG', sections['urgency_low']['format'])
        self.assertIn('THREAT ALERT', sections['urgency_critical']['format'])
        for name in ('global', 'urgency_low', 'urgency_critical'):
            self.assertIn('%s', sections[name]['format'])
            self.assertIn('%b', sections[name]['format'])

    def test_osd_rules_still_override_the_generic_format(self):
        # dunst applies matching rules in file order; OSD formats must come later.
        order, sections = self.dunst_sections()
        last_generic = order.index('urgency_critical')
        for name in ('skynet-volume', 'skynet-volume-muted', 'skynet-microphone',
                     'skynet-microphone-muted', 'skynet-brightness'):
            self.assertGreater(order.index(name), last_generic, name)
            self.assertIn('format', sections[name])

    def test_kitty_hud_is_static(self):
        settings = {}
        for line in KITTY_CONF.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, _, value = line.strip().partition(' ')
                settings[key] = value.strip()
        self.assertIn('{index:02d}', settings['tab_title_template'])
        self.assertIn('{index:02d}', settings['active_tab_title_template'])
        # Battery-conscious rendering stays untouched; no cursor animation.
        self.assertEqual(settings['repaint_delay'], '16')
        self.assertEqual(settings['sync_to_monitor'], 'yes')
        self.assertNotIn('cursor_trail', settings)

    def test_bottom_styles_use_theme_hex_colors(self):
        styles = tomllib.loads(BOTTOM.read_text())['styles']
        colors = []
        def collect(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ('color', 'bg_color') or key.endswith('_color'):
                        colors.append(value)
                    else:
                        collect(value)
            elif isinstance(node, list):
                colors.extend(node)
        collect(styles)
        self.assertGreater(len(colors), 20)
        for value in colors:
            self.assertRegex(value, r'^#[0-9a-f]{6}$')
        self.assertEqual(styles['widgets']['selected_border_color'], '#ff4050')


class DwmSchemeHygieneTest(unittest.TestCase):
    def setUp(self):
        self.dwm = (ROOT / 'sources/dwm/dwm.c').read_text()
        self.config = (ROOT / 'sources/dwm/config.h').read_text()
        enum = re.search(r'enum \{ SchemeNorm.*?\};', self.dwm, re.S).group(0)
        self.schemes = re.findall(r'Scheme[A-Za-z0-9]+', enum)

    def test_every_scheme_is_drawn(self):
        # Each colour scheme allocates X colours at startup; unused ones are waste.
        for scheme in self.schemes:
            self.assertGreater(len(re.findall(r'\b%s\b' % scheme, self.dwm)), 1, scheme)

    def test_config_defines_only_known_schemes(self):
        defined = re.findall(r'\[(Scheme[A-Za-z0-9]+)\]\s*=', self.config)
        self.assertEqual(sorted(defined), sorted(self.schemes))

    def test_rules_change_something(self):
        rules = re.search(r'static const Rule rules\[\] = \{(.*?)\n\};', self.config, re.S).group(1)
        for rule in re.findall(r'\{([^{}]*)\}', rules):
            fields = [field.strip() for field in rule.split(',')]
            self.assertNotEqual(fields[3:6], ['0', '0', '-1'], rule)


if __name__ == '__main__':
    unittest.main()
