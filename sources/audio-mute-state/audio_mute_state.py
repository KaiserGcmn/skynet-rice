#!/usr/bin/python3
"""Save hardware mute switches on logout and restore them on the next login."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


KINDS = ("sinks", "sources")
PREFIXES = ("alsa_output.", "alsa_input.", "bluez_output.", "bluez_input.")


class AudioError(RuntimeError):
    pass


def pactl(*args):
    try:
        result = subprocess.run(
            ["/usr/bin/pactl", *args], check=True, capture_output=True,
            text=True, timeout=2, env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AudioError(f"pactl failed: {exc}") from exc
    return result.stdout


def snapshot():
    state = {"version": 1, "sinks": {}, "sources": {}}
    for kind in KINDS:
        try:
            devices = json.loads(pactl("--format=json", "list", kind))
        except json.JSONDecodeError as exc:
            raise AudioError("pactl returned invalid JSON") from exc
        if not isinstance(devices, list):
            raise AudioError("pactl returned an invalid device list")
        for device in devices:
            if not isinstance(device, dict):
                raise AudioError("pactl returned an invalid device")
            name = device.get("name", "")
            if not isinstance(name, str) or not name.startswith(PREFIXES):
                continue
            if name.endswith(".monitor"):
                continue
            mute = device.get("mute")
            if type(mute) is not bool:
                raise AudioError(f"Invalid mute switch for {name}")
            state[kind][name] = mute
    return state


def load_state(path):
    try:
        state = json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        raise AudioError(f"Cannot read saved mute state: {exc}") from exc
    if not isinstance(state, dict) or type(state.get("version")) is not int or state["version"] != 1:
        raise AudioError("Unsupported saved mute state")
    for kind in KINDS:
        devices = state.get(kind)
        if not isinstance(devices, dict) or any(
            not isinstance(name, str) or not name.startswith(PREFIXES)
            or name.endswith(".monitor") or type(mute) is not bool
            for name, mute in devices.items()
        ):
            raise AudioError("Invalid saved mute state; leaving audio unchanged")
    return state


def write_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
            temporary = handle.name
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary is not None:
            os.unlink(temporary)


def save(path):
    previous = load_state(path)
    current = snapshot()  # Both lists must succeed before replacing the file.
    if previous is not None:
        for kind in KINDS:
            current[kind] = {**previous[kind], **current[kind]}
    if not any(current[kind] for kind in KINDS):
        raise AudioError("No hardware audio devices available to save")
    write_state(path, current)
    print("Saved speaker and microphone mute switches", flush=True)


def restore(path, timeout=12):
    saved = load_state(path)  # Validate before making any audio changes.
    deadline = time.monotonic() + timeout
    restored = set()
    contacted = False
    last_error = None
    pending = {(kind, name) for kind in KINDS for name in saved[kind]} if saved else set()
    # Give WirePlumber's initial routing policy a chance to finish first.
    time.sleep(1)
    while time.monotonic() < deadline:
        try:
            current = snapshot()
            contacted = True
            if saved is None:
                if any(current[kind] for kind in KINDS):
                    write_state(path, current)
                    print("Initialized mute state without changing audio", flush=True)
                    return
            else:
                available = {(kind, name) for kind, name in pending if name in current[kind]}
                for kind, name in sorted(available):
                    pactl(f"set-{kind[:-1]}-mute", name, "1" if saved[kind][name] else "0")
                if available:
                    time.sleep(0.3)
                    checked = snapshot()
                    for kind, name in available:
                        if checked[kind].get(name) is saved[kind][name]:
                            pending.remove((kind, name))
                            restored.add((kind, name))
                if not pending:
                    print(f"Restored {len(restored)} mute switches", flush=True)
                    return
            last_error = None
        except AudioError as exc:
            last_error = exc
        time.sleep(0.3)
    if last_error is not None:
        raise last_error
    if saved is None or not contacted:
        raise AudioError("Audio devices did not become ready before the timeout")
    current = snapshot()
    if any(name in current[kind] for kind, name in pending):
        raise AudioError("Some connected devices did not retain their saved mute switch")
    print(f"Restored {len(restored)} mute switches; {len(pending)} devices disconnected", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("save", "restore"))
    args = parser.parse_args()
    state_root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    path = state_root / "audio-mute-state/state.json"
    try:
        (save if args.action == "save" else restore)(path)
    except (AudioError, OSError) as exc:
        print(f"audio-mute-state: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
