"""Java/Swing windows must resize under dwm, a non-reparenting window manager."""
from pathlib import Path
import re
import subprocess
import unittest


SESSION = Path(__file__).resolve().parents[1] / 'runtime/usr/local/bin/dwm-session'


class SessionJavaEnvironmentTest(unittest.TestCase):
    def test_session_exports_the_non_reparenting_flag(self):
        text = SESSION.read_text()
        self.assertRegex(text, r'(?m)^export _JAVA_AWT_WM_NONREPARENTING=1$')

    def test_flag_is_set_before_any_program_is_started(self):
        text = SESSION.read_text()
        flag = text.index('export _JAVA_AWT_WM_NONREPARENTING=1')
        first_start = re.search(r'(?m)^start ', text).start()
        self.assertLess(flag, first_start)

    def test_session_script_is_valid_sh(self):
        subprocess.run(['sh', '-n', str(SESSION)], check=True)


if __name__ == '__main__':
    unittest.main()
