"""Check narrowly scoped GRUB entry removal; no access to the machine's /boot."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("retire_vmd", ROOT / "scripts/retire-vmd-grub-backup.py")
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)
OLD_ENTRY = f"""# SKYNET exact-kernel VMD fallback; original kernel arguments preserved.
menuentry 'Devuan 6.12.115 - original VMD (recovery)' --id skynet-vmd-stock {{
    linux /boot/vmlinuz-{cleanup.OLD} root=UUID=example ro quiet
    initrd {cleanup.BACKUP}
}}
"""
OTHER = "# User entry\nmenuentry 'Other recovery' --id keep-me {\n    echo 'Keep this'\n}\n"
NORMAL = f"""if [ "${{next_entry}}" ]; then
    set default="${{next_entry}}"
else
    set default="0"
fi
set timeout=3
menuentry 'Devuan' --id normal {{
    linux /boot/vmlinuz-{cleanup.CURRENT} root=UUID=example ro quiet
    initrd /boot/initrd.img-{cleanup.CURRENT}
}}
source ${{config_directory}}/custom.cfg
"""


class GrubBackupCleanupTest(unittest.TestCase):
    def test_removes_only_named_backup_preserving_other_content(self):
        self.assertEqual(cleanup.remove_entry(OTHER + OLD_ENTRY + OTHER), (OTHER + OTHER, True))

    def test_only_backup_leaves_no_empty_configuration(self):
        self.assertEqual(cleanup.remove_entry(OLD_ENTRY), ("", True))

    def test_empty_or_comment_only_fragment_needs_no_script_check(self):
        with patch.object(cleanup, 'run') as run:
            cleanup.check_custom_syntax('')
            cleanup.check_custom_syntax('# unrelated user note\n\n')
            run.assert_not_called()
            cleanup.check_custom_syntax(OTHER)
            run.assert_called_once()

    def test_repeated_run_preserves_unrelated_entries(self):
        for value in ("", OTHER):
            self.assertEqual(cleanup.remove_entry(value), (value, False))

    def test_different_kernel_or_image_is_rejected(self):
        for value in (OLD_ENTRY.replace(cleanup.OLD, cleanup.CURRENT),
                      OLD_ENTRY.replace('.skynet-stock', ''),
                      OLD_ENTRY + OLD_ENTRY, OLD_ENTRY.rstrip()[:-1]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    cleanup.remove_entry(value)

    def test_default_requires_current_kernel_and_existing_boot_policy(self):
        self.assertIn("'Devuan'", cleanup.verify_default(NORMAL))
        for value in (NORMAL.replace(cleanup.CURRENT, cleanup.OLD),
                      NORMAL.replace('set default="0"', 'set default="saved"'),
                      NORMAL.replace('set timeout=3', 'set timeout=0'),
                      NORMAL.replace('initrd /boot/initrd.img-', 'initrd /wrong-')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    cleanup.verify_default(value)


if __name__ == '__main__':
    unittest.main()
