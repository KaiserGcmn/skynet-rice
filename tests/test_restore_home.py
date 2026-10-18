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
        self.assertIn(str(self.home), fastfetch)
        self.assertFalse((self.home / '.config/systemd').exists())
        self.assertFalse((self.home / '.xprofile').exists())
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
