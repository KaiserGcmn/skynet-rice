"""Known sensor feedback must not relabel unrelated/password PAM messages."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BiometricNoticeTest(unittest.TestCase):
    def test_sensor_messages_and_unknown_fallback(self):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            self.skipTest('requires C compiler and Cairo development files')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'cairo'],
                               capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires Cairo development files')
        with tempfile.TemporaryDirectory(prefix='skynet-biometric-test-') as work:
            source = Path(work) / 'check.c'
            source.write_text(r'''
#include "skynet-biometric.h"
#include <assert.h>
int main(void) {
    assert(skynet_biometric_notice("Failed to match fingerprint") == BIOMETRIC_NO_MATCH);
    assert(skynet_biometric_notice("Verification timed out") == BIOMETRIC_TIMEOUT);
    assert(skynet_biometric_notice("Your finger was not centered, try touching the sensor again") == BIOMETRIC_RETRY);
    assert(skynet_biometric_notice("An unexpected error happened during finger verification") == BIOMETRIC_READER_ERROR);
    const char *plain[] = {NULL, "", "Authentication failure", "Password:",
        "Failed to match fingerprint: unsupported variant", "verify-match",
        "Place your right index finger on the fingerprint reader", "Success"};
    for (size_t i = 0; i < sizeof(plain)/sizeof(plain[0]); ++i)
        assert(skynet_biometric_notice(plain[i]) == BIOMETRIC_NONE);
    cairo_surface_t *surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 520, 184);
    cairo_t *cr = cairo_create(surface);
    for (int notice = BIOMETRIC_NONE; notice <= BIOMETRIC_READER_ERROR; ++notice) {
        skynet_biometric_draw(cr, 520, 184, 0, 10, notice);
        skynet_biometric_draw(cr, 260, 92, -1, 0, notice);
        assert(cairo_status(cr) == CAIRO_STATUS_SUCCESS);
    }
    cairo_destroy(cr); cairo_surface_destroy(surface);
    return 0;
}
''')
            binary = Path(work) / 'check'
            subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-I',
                            str(ROOT / 'sources/xsecurelock-power'), str(source),
                            '-o', str(binary), *shlex.split(flags.stdout)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
