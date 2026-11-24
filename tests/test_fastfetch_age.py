"""Do not mistake filesystem/image timestamps for the user's OS age."""
from datetime import date
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'home/.local/bin/os-age'
SPEC = spec_from_loader('skynet_os_age', SourceFileLoader('skynet_os_age', str(SCRIPT)))
AGE = module_from_spec(SPEC)
SPEC.loader.exec_module(AGE)


class FirstUseAgeTest(unittest.TestCase):
    def test_confirmed_first_use_and_singular_day(self):
        self.assertEqual(AGE.age_text('2026-10-19\n', date(2026, 10, 28)),
                         '9 days / first use 2026-10-19')
        self.assertEqual(AGE.age_text('2026-10-19', date(2026, 10, 20)),
                         '1 day / first use 2026-10-19')

    def test_calendar_days_across_clock_changes(self):
        self.assertTrue(AGE.age_text('2026-10-24', date(2026, 10, 26)).startswith('2 days /'))
        self.assertTrue(AGE.age_text('2024-02-28', date(2024, 3, 1)).startswith('2 days /'))

    def test_missing_invalid_or_future_dates_are_not_fabricated(self):
        for value in [None, '', '2026-02-30', '20261019', '2026-10-29', '2026-10-19\necho bad']:
            with self.subTest(value=value):
                self.assertTrue(AGE.age_text(value, date(2026, 10, 28)).startswith('unknown /'))

    def test_cli_uses_only_explicit_state_file(self):
        with tempfile.TemporaryDirectory() as directory:
            env = os.environ | {'HOME': directory, 'XDG_STATE_HOME': directory + '/state'}
            def run():
                return subprocess.check_output(['/usr/bin/python3', str(SCRIPT)], env=env, text=True).strip()
            self.assertEqual(run(), 'unknown / first-use date not recorded')
            record = Path(env['XDG_STATE_HOME']) / 'skynet-rice/first-use-date'
            record.parent.mkdir(parents=True)
            record.write_text(date.today().isoformat() + '\n')
            # The record mtime must not be interpreted as the first-use date.
            os.utime(record, (0, 0))
            self.assertEqual(run(), f'0 days / first use {date.today().isoformat()}')


if __name__ == '__main__':
    unittest.main()
