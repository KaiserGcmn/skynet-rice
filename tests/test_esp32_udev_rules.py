"""Native-USB ESP32 boards must be usable by the logged-in user without root."""
from pathlib import Path
import re
import unittest


RULE_DIR = Path(__file__).resolve().parents[1] / 'runtime/etc/udev/rules.d'
RULES = RULE_DIR / '71-esp32-usb.rules'


def rule_lines(path=RULES):
    return [line for line in path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


class Esp32UdevRulesTest(unittest.TestCase):
    def test_every_rule_is_well_formed_and_only_grants_uaccess(self):
        term = r'[A-Za-z_]+(\{[A-Za-z_]+\})?(==|!=|\+=|=)"[^"]*"'
        for path in (RULES,):
            self.assertTrue(rule_lines(path), path.name)
            for line in rule_lines(path):
                self.assertRegex(line, rf'^{term}(, {term})*$')
                self.assertIn('SUBSYSTEM=="usb"', line)
                self.assertIn('TAG+="uaccess"', line)
                self.assertNotIn('MODE', line, 'uaccess must not widen device permissions')
                self.assertNotIn('GROUP=', line)

    def test_covers_espressif_and_nano_esp32_ids(self):
        text = '\n'.join(rule_lines())
        self.assertIn('ATTR{idVendor}=="303a"', text)
        self.assertRegex(text, r'ATTR\{idVendor\}=="2341", ATTR\{idProduct\}=="0070\|0470"')

    def test_rule_sorts_before_the_seat_tagging_stage(self):
        # uaccess tags only take effect when added before 73-seat-late.rules.
        for path in (RULES,):
            self.assertLess(int(path.name.split('-')[0]), 73)


if __name__ == '__main__':
    unittest.main()
