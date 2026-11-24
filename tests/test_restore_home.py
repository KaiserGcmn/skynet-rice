import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('restore_home', Path(__file__).resolve().parents[1] / 'scripts/restore-home.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


class RestoreTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home with spaces'
        self.home.mkdir()

    def call_restore(self, apply):
        with contextlib.redirect_stdout(io.StringIO()):
            return restore.restore(self.home, apply)

    def test_preview_does_not_write(self):
        self.call_restore(False)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_restore_backup_permissions_and_repeat(self):
        original = self.home / '.bashrc'
        original.write_text('previous shell config\n')
        original.chmod(0o600)
        backup = self.call_restore(True)
        self.assertEqual((backup / 'files/.bashrc').read_text(), 'previous shell config\n')
        self.assertEqual(original.stat().st_mode & 0o777, 0o600)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o700)
        fastfetch = (self.home / '.config/fastfetch/config.jsonc').read_text()
        self.assertNotIn('@@HOME@@', fastfetch)
        logo = json.loads(fastfetch)['logo']
        self.assertEqual(logo['type'], 'file')
        self.assertEqual(logo['source'], '~/.config/fastfetch/skynet-globe.txt')
        self.assertTrue((self.home / '.config/fastfetch/skynet-globe.txt').is_file())
        self.assertFalse((self.home / '.local/bin/fastfetch').exists())
        self.assertFalse((self.home / '.local/bin/skynet-fetch-logo').exists())
        self.assertFalse((self.home / '.config/systemd').exists())
        # The old service-starting .xprofile must never return; the tracked one
        # only selects the cursor theme.
        profile = (self.home / '.xprofile').read_text()
        for line in profile.splitlines():
            if line.strip() and not line.startswith('#'):
                self.assertRegex(line, r'^export XCURSOR_(THEME|SIZE)=[A-Za-z0-9_-]+$')
        self.assertIsNone(self.call_restore(True))

    def test_symlink_aborts_before_replacing_files(self):
        original = self.home / '.bashrc'
        original.write_text('keep me')
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (self.home / '.config').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.call_restore(True)
        self.assertEqual(original.read_text(), 'keep me')
        self.assertEqual(list(outside.iterdir()), [])

    def test_file_as_parent_aborts_before_writing(self):
        (self.home / '.config').write_text('not a directory')
        with self.assertRaises(ValueError):
            self.call_restore(True)
        self.assertFalse((self.home / '.bashrc').exists())


if __name__ == '__main__':
    unittest.main()
