"""Run with the built Kitty, from its extracted source directory.

kitty +runpy 'import runpy; runpy.run_path("/path/test_compat.py", run_name="__main__")'
The real wheel/keyboard integration checks are in probe.py and gui_test.py.
"""

import unittest

from kitty.fast_data_types import create_mock_window, send_mock_scroll_event_to_window
from kitty_tests.base import BaseTest, parse_bytes


class CompatibilityTests(BaseTest):
    def query(self, screen, expected):
        screen.callbacks.wtcbuf = b""
        parse_bytes(screen, b"\x1b[?1007$p")
        self.assertEqual(screen.callbacks.wtcbuf, f"\x1b[?1007;{expected}$y".encode())

    def test_alternate_scroll_mode_query_and_reset(self):
        screen = self.create_screen()
        self.query(screen, 1)  # Preserve Kitty's previous alternate-screen wheel default.
        parse_bytes(screen, b"\x1b[?1007l")
        self.query(screen, 2)
        parse_bytes(screen, b"\x1b[?1007h")
        self.query(screen, 1)
        parse_bytes(screen, b"\x1b[?1007l\x1bc")
        self.query(screen, 1)

    def test_alternate_scroll_save_restore(self):
        screen = self.create_screen()
        parse_bytes(screen, b"\x1b[?1007s\x1b[?1007l")
        self.query(screen, 2)
        parse_bytes(screen, b"\x1b[?1007r")
        self.query(screen, 1)
        parse_bytes(screen, b"\x1b[?1007l\x1b[?1007s\x1b[?1007h\x1b[?1007r")
        self.query(screen, 2)

    def test_main_screen_scrollback_still_works(self):
        screen = self.create_screen(lines=5, scrollback=50,
                                    options={"pixel_scroll": False, "wheel_scroll_multiplier": 1.0})
        window = create_mock_window(screen)
        for i in range(30):
            parse_bytes(screen, f"line {i}\r\n".encode())
        parse_bytes(screen, b"\x1b[?1007l")
        send_mock_scroll_event_to_window(window, 0, 0.0, 2.0, 0)
        self.assertEqual(screen.scrolled_by, 2)

    def test_mouse_reporting_works_with_alternate_scroll_disabled(self):
        screen = self.create_screen(options={"wheel_scroll_multiplier": 1.0})
        window = create_mock_window(screen)
        parse_bytes(screen, b"\x1b[?1049h\x1b[?1007l\x1b[?1000h\x1b[?1006h")
        screen.callbacks.wtcbuf = b""
        send_mock_scroll_event_to_window(window, 0, 0.0, 1.0, 0)
        self.assertIn(b"\x1b[<64;", screen.callbacks.wtcbuf)

    def test_codex_keyboard_reset_preserves_kitty_protocol(self):
        screen = self.create_screen()
        parse_bytes(screen, b"\x1b[>4;0m\x1b[>7u\x1b[>4;0m\x1b[?u")
        self.assertEqual(screen.callbacks.wtcbuf, b"\x1b[?7u")
        screen.callbacks.wtcbuf = b""
        parse_bytes(screen, b"\x1b[<u\x1b[>4;0m\x1b[?u")
        self.assertEqual(screen.callbacks.wtcbuf, b"\x1b[?0u")

    def test_status_protocol_reaches_handler(self):
        screen = self.create_screen()
        reports = [f"state={state}:app=codex" for state in ("idle", "working", "done", "clear")]
        for report in reports:
            parse_bytes(screen, f"\x1b]7501;{report}\x1b\\".encode())
        self.assertEqual(screen.callbacks.program_status_reports, reports)

    def test_synchronized_output_repeated_modes(self):
        screen = self.create_screen(cols=20)
        for sequence, expected in ((b"\x1b[?2026h\x1b[?2026h", 1),
                                   (b"\x1b[?2026l\x1b[?2026l", 2)):
            screen.callbacks.wtcbuf = b""
            parse_bytes(screen, sequence + b"\x1b[?2026$p")
            self.assertEqual(screen.callbacks.wtcbuf, f"\x1b[?2026;{expected}$y".encode())
        parse_bytes(screen, b"\x1b[?2026h\x1b[?2026htext\x1b[?2026l\x1b[?2026l")
        self.assertEqual(str(screen.line(0)), "text")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CompatibilityTests)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
