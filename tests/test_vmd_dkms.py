"""Keep the VMD MTL016 DKMS package consistent with its reviewed sources."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VMD = ROOT / 'drivers/vmd'
DKMS_CONF = VMD / 'dkms/dkms.conf'
MODULE_VERSION = '0.6-mtl016-deb13-117'
STOCK_SRCVERSION = '9CED7F0241F8FAD2F7858E3'
NEVER_MATCH = '^vmd-mtl016-kaynak-dogrulanmadi$'


def source_conf(kernelver):
    """Return BUILD_EXCLUSIVE_KERNEL after sourcing dkms.conf the way DKMS does."""
    script = ('kernel_source_dir=/nonexistent; dkms_tree=/nonexistent; '
              f'kernelver="$1"; . "{DKMS_CONF}"; '
              'printf "%s\\n%s\\n" "$BUILD_EXCLUSIVE_KERNEL" "$PACKAGE_NAME"')
    result = subprocess.run(['bash', '-c', script, 'test', kernelver],
                            capture_output=True, text=True, check=True)
    return result.stdout.splitlines()


class VmdDkmsTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which('patch'), 'patch is not installed')
    def test_dkms_source_is_reviewed_patch_on_debian_6_12_117(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / 'vmd.c').write_bytes((VMD / 'pristine/vmd-6.12.117.c').read_bytes())
            patch = (VMD / 'backport.patch').read_text().replace(
                '0.6-mtl016-b437504-deb13-113', MODULE_VERSION)
            result = subprocess.run(
                ['patch', '--batch', '--fuzz=0', '-p1', '-d', str(work)],
                input=patch, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('fuzz', result.stdout)
            self.assertEqual((work / 'vmd.c').read_bytes(),
                             (VMD / 'dkms/vmd.c').read_bytes())

    def test_quirk_targets_only_the_arrow_lake_controller(self):
        source = (VMD / 'dkms/vmd.c').read_text()
        quirked = re.findall(r'PCI_VDEVICE\(INTEL, (0x[0-9a-f]+)\),\s*\.driver_data = '
                             r'[^,]*VMD_FEAT_INTERRUPT_QUIRK', source)
        self.assertEqual(quirked, ['0x7d0b'])
        self.assertIn(f'MODULE_VERSION("{MODULE_VERSION}");', source)

    def test_gate_fails_closed_for_unknown_kernel(self):
        exclusive, name = source_conf('0.0.0-skynet-test-yok')
        self.assertEqual(name, 'vmd-mtl016')
        self.assertEqual(exclusive, NEVER_MATCH)
        self.assertIsNone(re.search(exclusive, '6.12.117+deb13-amd64'))

    def test_gate_pins_the_reviewed_stock_source(self):
        conf = DKMS_CONF.read_text()
        self.assertIn(f'VMD_STOCK_SRCVERSION="{STOCK_SRCVERSION}"', conf)
        self.assertIn('DEST_MODULE_LOCATION[0]="/updates/dkms"', conf)


if __name__ == '__main__':
    unittest.main()
