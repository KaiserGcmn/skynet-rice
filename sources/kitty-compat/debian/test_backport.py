"""Run through the candidate Kitty +runpy from the Debian source directory."""
import base64
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from kitty.program_status import InvalidReport, ProgramStatus, parse_report
from kitty.shm import SharedMemory
from kitty.window import Window, color_control
from kitty_tests import BaseTest, draw_multicell, parse_bytes


class BackportTests(BaseTest):
    def test_mode_1007_query_save_restore(self):
        s = self.create_screen()
        for command, state in ((b"", 1), (b"\x1b[?1007s\x1b[?1007l", 2),
                               (b"\x1b[?1007r", 1), (b"\x1b[?1007l\x1bc", 1)):
            s.callbacks.wtcbuf = b""
            parse_bytes(s, command + b"\x1b[?1007$p")
            self.assertEqual(s.callbacks.wtcbuf, f"\x1b[?1007;{state}$y".encode())

    def test_keyboard_reset_and_sync(self):
        s = self.create_screen()
        parse_bytes(s, b"\x1b[>4;0m\x1b[>7u\x1b[?u")
        self.assertEqual(s.callbacks.wtcbuf, b"\x1b[?7u")
        for command, state in ((b"\x1b[?2026h\x1b[?2026h", 1),
                               (b"\x1b[?2026l\x1b[?2026l", 2)):
            s.callbacks.wtcbuf = b""
            parse_bytes(s, command + b"\x1b[?2026$p")
            self.assertEqual(s.callbacks.wtcbuf, f"\x1b[?2026;{state}$y".encode())

    def test_status_handler_and_query(self):
        status = ProgramStatus()
        responses = []
        window = SimpleNamespace(program_status=status, title_updated=lambda: None,
                                 screen=SimpleNamespace(send_escape_code_to_child=lambda *a: responses.append(a)))
        Window.program_status_report(window, memoryview(b"state=working:app=codex:progress=25"))
        self.assertEqual(status.most_urgent().progress, 25)
        Window.program_status_report(window, memoryview(b"?"))
        self.assertIn("states=", responses[0][1])
        Window.program_status_report(window, memoryview(b"state=clear"))
        self.assertFalse(status)

    def test_status_rejects_control_characters_and_excessive_size(self):
        for data in (b"state=working:title=G1swbQ==", b"state=working:msg=" + b"A" * 5000):
            self.assertRaises(InvalidReport, parse_report, data)

    def test_echo_accepts_only_decimal_canary(self):
        output = []
        window = SimpleNamespace(write_to_child=output.append)
        for data in (b"12; echo invalid", b"123\n", b"abc", b"123456"):
            Window.handle_remote_echo(window, memoryview(base64.b64encode(data)))
        self.assertEqual(output, [b"123456"])

    def test_unknown_color_fields_are_encoded(self):
        s = self.create_screen()
        name = "unrecognized field $(value)"
        result = color_control(s.color_profile, 21, name + "=?")
        self.assertNotIn(name, result)
        self.assertIn("unknown=" + base64.b64encode(name.encode()).decode().rstrip("="), result)

    def test_multicell_long_graphemes(self):
        s = self.create_screen(cols=80)
        draw_multicell(s, "a" + "\u0301" * 100 + "b" + "\u0301" * 150)
        self.assertEqual(s.cursor.x, 2)

    def test_shared_memory_permissions(self):
        with SharedMemory(size=4096, unlink_on_exit=True) as shm:
            shm.verify_owner_and_mode()
            for mode in (0o644, 0o660, 0o400):
                os.fchmod(shm.fileno(), mode)
                with SharedMemory(name=shm.name, readonly=True) as check:
                    self.assertRaises(ValueError, check.verify_owner_and_mode)

    def test_askpass_reuses_verified_handle(self):
        callbacks = []
        boss = SimpleNamespace(get_line=lambda message, callback, **kw: callbacks.append((message, callback, kw)))
        with SharedMemory(size=4096, unlink_on_exit=True) as shm:
            shm.seek(1)
            shm.write_data_with_size(json.dumps({"type": "get_line", "message": "Test\x1b[2J", "is_password": True}))
            shm.flush()
            with patch("kitty.window.get_boss", return_value=boss):
                Window.handle_remote_askpass(SimpleNamespace(), memoryview(shm.name.encode()))
            self.assertEqual(len(callbacks), 1)
            self.assertNotIn("\x1b[2J", callbacks[0][0])
            self.assertTrue(callbacks[0][2]["is_password"])
            callbacks[0][1]("test-value")
            shm.seek(1)
            self.assertEqual(json.loads(shm.read_data_with_size()), "test-value")

    def test_askpass_rejects_shared_object(self):
        boss = unittest.mock.Mock()
        with SharedMemory(size=4096, unlink_on_exit=True) as shm:
            os.fchmod(shm.fileno(), 0o666)
            with patch("kitty.window.get_boss", return_value=boss):
                Window.handle_remote_askpass(SimpleNamespace(), memoryview(shm.name.encode()))
            boss.get_line.assert_not_called()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BackportTests)
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
