"""Exercise only a supplied Kitty candidate in a private, authenticated Xephyr.

Usage: python3 gui_test.py /absolute/kitty /empty/private/test-directory
No remote control, network listener, model request or live session input.
"""

import json
import os
from pathlib import Path
import secrets
import re
import shlex
import subprocess
import sys
import time


def desktop_env():
    env = os.environ.copy()
    for process in Path("/proc").iterdir():
        if not process.name.isdecimal():
            continue
        try:
            if (process / "comm").read_text().strip() != "dwm":
                continue
            if process.stat().st_uid != os.getuid():
                continue
            values = dict(part.split(b"=", 1) for part in
                          (process / "environ").read_bytes().split(b"\0") if b"=" in part)
            for key in ("DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR"):
                if key.encode() in values:
                    env[key] = values[key.encode()].decode()
            return env
        except (PermissionError, FileNotFoundError, ProcessLookupError):
            continue
    raise RuntimeError("Cannot locate this user's DWM display")


def main():
    executable = str(Path(sys.argv[1]).resolve())
    version = subprocess.check_output([executable, "--version"], text=True)
    options = ["-o", "wheel_scroll_multiplier=1"]
    if "0.41." not in version:
        options += ["-o", "pixel_scroll=no"]
    work = Path(sys.argv[2]).resolve()
    work.mkdir(mode=0o700, parents=True, exist_ok=False)
    env = desktop_env()
    display = next(f":{n}" for n in range(150, 180)
                   if not Path(f"/tmp/.X11-unix/X{n}").exists()
                   and not Path(f"/tmp/.X{n}-lock").exists())
    authority = work / "Xauthority"
    authority.touch(mode=0o600)
    subprocess.run(["xauth", "-f", str(authority), "add", display, ".", secrets.token_hex(16)], check=True)
    child_env = env | {"DISPLAY": display, "XAUTHORITY": str(authority),
                       "XDG_CACHE_HOME": str(work / "cache")}
    procs = []
    try:
        with (work / "xephyr.log").open("w") as log:
            server = subprocess.Popen(["Xephyr", display, "-screen", "1100x800", "-nolisten", "tcp",
                                       "-auth", str(authority)], env=env, stdout=log, stderr=log)
        procs.append(server)
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError("Xephyr failed")
            if subprocess.run(["xdotool", "getdisplaygeometry"], env=child_env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(0.05)
        else:
            raise TimeoutError("Xephyr readiness")
        with (work / "kitty.log").open("w") as log:
            terminal = subprocess.Popen([executable, "--title", "SKYNET compatibility test", *options,
                                         "/usr/bin/python3", str(Path(__file__).with_name("probe.py")), str(work)],
                                        env=child_env, stdout=log, stderr=log)
        procs.append(terminal)
        seen = set()
        deadline = time.monotonic() + 25
        while terminal.poll() is None and time.monotonic() < deadline:
            try:
                phase = (work / "phase").read_text()
            except FileNotFoundError:
                phase = ""
            if phase and phase not in seen:
                window = subprocess.check_output(["xdotool", "search", "--name", "^SKYNET compatibility test$"],
                                                 env=child_env, text=True).splitlines()[-1]
                subprocess.run(["xdotool", "windowfocus", window, "mousemove", "--window", window, "200", "200"],
                               env=child_env, check=True)
                action = ["click", "4"] if phase.startswith("wheel") or phase == "mouse_reporting" else [
                    "key", "--clearmodifiers", "shift+Return" if phase == "shift_enter" else "ctrl+c"]
                subprocess.run(["xdotool"] + action, env=child_env, check=True)
                seen.add(phase)
            time.sleep(0.02)
        if terminal.poll() is None:
            raise TimeoutError("Terminal probe")
        assert terminal.returncode == 0, terminal.returncode
        result = json.loads((work / "probe-result.json").read_text())
        decoded = {key: bytes.fromhex(value) for key, value in result.items()}
        assert decoded["keyboard_query"] == b"\x1b[?7u", decoded
        assert decoded["mode_disabled_query"] == b"\x1b[?1007;2$y", decoded
        assert decoded["mode_enabled_query"] == b"\x1b[?1007;1$y", decoded
        assert decoded["wheel_enabled"] == b"\x1b[A", decoded
        assert decoded["wheel_disabled"] == b"", decoded
        assert b"\x1b[13;2u" in decoded["shift_enter"], decoded
        assert b"\x1b[99;5u" in decoded["ctrl_c"], decoded
        assert b"\x1b[<64;" in decoded["mouse_reporting"], decoded
        assert decoded["sync_repeated_begin"] == b"\x1b[?2026;1$y", decoded
        assert decoded["sync_repeated_end"] == b"\x1b[?2026;2$y", decoded
        assert decoded["sync_original_timeout"] == b"\x1b[?2026;2$y", decoded
        assert not (work / "kitty.log").read_text().strip(), (work / "kitty.log").read_text()
        print(json.dumps({"status": "passed", "checks": list(decoded), "stderr": "empty"}))
        if len(sys.argv) > 3:
            codex_home = work / "codex-home"
            codex_home.mkdir(mode=0o700)
            codex_env = child_env | {
                "CODEX_HOME": str(codex_home), "DO_NOT_TRACK": "1",
                "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",
                "ALL_PROXY": "http://127.0.0.1:9", "NO_PROXY": "",
            }
            codex_command = [str(Path(sys.argv[3]).resolve()), "--cd", str(work),
                             "-c", "check_for_update_on_startup=false"]
            transcript = work / "codex-tui.raw"
            with (work / "codex-kitty.log").open("w") as log:
                smoke = subprocess.Popen([
                    executable, "--title", "SKYNET isolated Codex test",
                    "/usr/bin/script", "-q", "-e", "-f", "-c", shlex.join(codex_command), str(transcript),
                ], cwd=work, env=codex_env, stdout=log, stderr=log)
            procs.append(smoke)
            time.sleep(4)
            for _ in range(4):
                if smoke.poll() is not None:
                    break
                window = subprocess.check_output([
                    "xdotool", "search", "--class", "kitty"], env=child_env, text=True).splitlines()[-1]
                subprocess.run(["xdotool", "windowfocus", window, "key", "--clearmodifiers", "ctrl+c"],
                               env=child_env, check=True)
                time.sleep(0.8)
            if smoke.poll() is None:
                raise TimeoutError("Isolated Codex did not exit after Ctrl+C")
            raw = transcript.read_bytes()
            sequences = re.findall(rb"\x1b\[[?>][0-9;]*[muhlp]", raw)
            assert b"\x1b[>4;0m" in sequences, "Codex keyboard reset not observed"
            log = (work / "codex-kitty.log").read_text()
            assert not log.strip(), log
            summary = {"status": "passed", "exit": smoke.returncode,
                       "scope": "fresh unauthenticated onboarding, no submitted prompt",
                       "terminal_sequences": sorted({x.hex() for x in sequences}), "stderr": "empty"}
            (work / "codex-smoke.json").write_text(json.dumps(summary, indent=2))
            print(json.dumps(summary))
    finally:
        for proc in reversed(procs):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)


if __name__ == "__main__":
    main()
