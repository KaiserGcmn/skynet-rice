"""Drag-select box in Thunar/GTK3 must stay translucent over the black views."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / 'home/.themes/SKYNET-Black-Red/gtk-3.0/gtk.css'

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    HAVE_GTK = Gtk.init_check(None)[0]
except (ImportError, ValueError):
    HAVE_GTK = False


@unittest.skipUnless(HAVE_GTK, 'requires PyGObject GTK 3 and a display')
class RubberbandTest(unittest.TestCase):
    def background(self, widget):
        provider = Gtk.CssProvider()
        provider.load_from_path(str(CSS))
        context = widget.get_style_context()
        context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        # Thunar adds the rubberband class to the view's own style context.
        context.add_class('view')
        context.add_class('rubberband')
        return context.get_property('background-color', Gtk.StateFlags.NORMAL)

    def test_icon_and_detail_views_get_translucent_red(self):
        for widget in (Gtk.IconView(), Gtk.TreeView()):
            color = self.background(widget)
            self.assertLess(color.alpha, 0.5, type(widget).__name__)
            self.assertGreater(color.alpha, 0.05, type(widget).__name__)
            self.assertGreater(color.red, color.green * 3)


if __name__ == '__main__':
    unittest.main()
