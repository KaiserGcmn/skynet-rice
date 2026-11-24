"""Actual D-Bus regression tests; never contact the system Polkit authority."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources/mate-polkit-hud'


@unittest.skipUnless(os.environ.get('SKYNET_DBUS_TESTS') == '1',
                     'set SKYNET_DBUS_TESTS=1 to run private D-Bus integration tests')
class OptionalSessionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('dbus-run-session'):
            raise unittest.SkipTest('dbus-run-session required')
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-polkit-test-')
        cls.addClassCleanup(cls.work.cleanup)
        cls.binary = Path(cls.work.name) / 'session-test'
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'gtk+-3.0',
                                'gio-2.0'], capture_output=True, text=True)
        if flags.returncode:
            raise unittest.SkipTest('GTK development headers required')
        polkit = subprocess.run(['pkg-config', '--cflags', '--libs',
                                'polkit-agent-1', 'polkit-gobject-1'],
                               capture_output=True, text=True)
        if 'POLKIT_CFLAGS' in os.environ:
            polkit_flags = shlex.split(os.environ['POLKIT_CFLAGS']) + shlex.split(
                os.environ.get('POLKIT_LIBS', '-l:libpolkit-agent-1.so.0 -l:libpolkit-gobject-1.so.0'))
        elif polkit.returncode:
            raise unittest.SkipTest('Polkit development headers required')
        else:
            polkit_flags = shlex.split(polkit.stdout)
        command = ['cc', '-DHAVE_CONFIG_H', '-DPOLKIT_AGENT_I_KNOW_API_IS_SUBJECT_TO_CHANGE',
                   '-DMATELOCALEDIR="/usr/share/locale"', '-I' + str(SOURCE),
                   str(ROOT / 'tests/fixtures/polkit_session.c')]
        command += [str(SOURCE / name) for name in ('polkitmatelistener.c',
                    'polkitmateauthenticator.c', 'polkitmateauthenticationdialog.c')]
        command += shlex.split(flags.stdout) + polkit_flags + ['-o', str(cls.binary)]
        subprocess.run(command, check=True, capture_output=True, text=True)

    def run_private(self, present=False, startup_id=None):
        env = dict(os.environ, G_DEBUG='fatal-criticals')
        env.pop('DESKTOP_AUTOSTART_ID', None)
        if startup_id is not None:
            env['DESKTOP_AUTOSTART_ID'] = startup_id
        command = ['dbus-run-session', '--']
        if present:
            command += ['/usr/bin/python3', str(ROOT / 'tests/fixtures/polkit_session_bus.py')]
        command += [str(self.binary)]
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('CRITICAL', result.stderr)
        self.assertNotIn('Failed to register client', result.stderr)

    def test_no_desktop_session_manager(self):
        self.run_private()

    def test_desktop_session_with_missing_startup_id(self):
        self.run_private(present=True)

    def test_existing_startup_id_is_preserved(self):
        self.run_private(present=True, startup_id='skynet-test-123')
