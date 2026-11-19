"""Opt-in: launches only a hidden private Xephyr/D-Bus tray fixture."""
import os
from pathlib import Path
import subprocess
import unittest


class SnixembedTest(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('SKYNET_TRAY_TEST_BINARY'),
                         'requires built binary and permission for private X11/D-Bus')
    def test_failed_properties_menu_and_pixel_lifecycle(self):
        fixture = Path(__file__).parent / 'fixtures/snixembed_x11.py'
        command = ['/usr/bin/python3', '-I', str(fixture), os.environ['SKYNET_TRAY_TEST_BINARY']]
        if os.environ.get('SKYNET_TRAY_BASELINE'):
            command.append(os.environ['SKYNET_TRAY_BASELINE'])
        subprocess.run(command, check=True, timeout=60)
