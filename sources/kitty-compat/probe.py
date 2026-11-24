"""Raw-TTY integration probe; only run in the isolated test terminal."""

import json
import os
from pathlib import Path
import select
import sys
import termios
import time
import tty


def main():
    work = Path(sys.argv[1])
    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    results = {}

    def send(text):
        os.write(sys.stdout.fileno(), text.encode())

    def read_for(seconds=0.7):
        end = time.monotonic() + seconds
        data = b""
        while time.monotonic() < end:
            if select.select([fd], [], [], max(0, end - time.monotonic()))[0]:
                data += os.read(fd, 4096)
        return data

    def phase(name, commands):
        send(commands)
        read_for(0.1)
        (work / "phase").write_text(name)
        return read_for(1.0)

    try:
        tty.setraw(fd)
        send("\x1b[>4;0m\x1b[>7u\x1b[?u")
        results["keyboard_query"] = read_for().hex()
        send("\x1b[<u\x1b[?1007l\x1b[?1007$p")
        results["mode_disabled_query"] = read_for().hex()
        send("\x1b[?1007h\x1b[?1007$p")
        results["mode_enabled_query"] = read_for().hex()
        results["wheel_enabled"] = phase("wheel_enabled", "\x1b[?1049h\x1b[?1007h").hex()
        results["wheel_disabled"] = phase("wheel_disabled", "\x1b[?1007l").hex()
        results["shift_enter"] = phase("shift_enter", "\x1b[>7u").hex()
        results["ctrl_c"] = phase("ctrl_c", "").hex()
        results["mouse_reporting"] = phase("mouse_reporting", "\x1b[?1000h\x1b[?1006h").hex()
        for state in ("idle", "working", "done", "clear"):
            send(f"\x1b]7501;state={state}:app=codex\x1b\\")
        send("\x1b[?2026h\x1b[?2026h\x1b[?2026$p")
        results["sync_repeated_begin"] = read_for(0.1).hex()
        send("\x1b[?2026l\x1b[?2026l\x1b[?2026$p")
        results["sync_repeated_end"] = read_for(0.1).hex()
        send("\x1b[?2026h")
        read_for(1.5)
        send("\x1b[?2026h")
        read_for(0.8)
        send("\x1b[?2026$p")
        results["sync_original_timeout"] = read_for(0.1).hex()
        send("\x1b[?2026l")
        read_for(0.2)
    finally:
        send("\x1b[?2026l\x1b[?1000l\x1b[?1006l\x1b[<u\x1b[>4;0m\x1b[?1007l\x1b[?1049l")
        termios.tcsetattr(fd, termios.TCSANOW, original)
    (work / "probe-result.json").write_text(json.dumps(results, indent=2))
    print("SKYNET compatibility probe finished")


if __name__ == "__main__":
    main()
