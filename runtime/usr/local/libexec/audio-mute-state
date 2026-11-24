#!/usr/bin/python3
"""Remember hardware volume and mute changes and restore them on login."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
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
    volumes = {kind: {} for kind in KINDS}
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
            volume = device.get("volume", {})
            if volume:
                if not isinstance(volume, dict):
                    raise AudioError(f"Invalid volume for {name}")
                try:
                    channels = device.get("channel_map", ",".join(volume)).split(",")
                    values = {channel: volume[channel]["value"] for channel in channels}
                except (KeyError, TypeError, AttributeError) as exc:
                    raise AudioError(f"Invalid volume channels for {name}") from exc
                if not valid_volume(values):
                    raise AudioError(f"Invalid volume for {name}")
                volumes[kind][name] = values
    if any(volumes.values()):
        state["volumes"] = volumes
    return state


def valid_volume(volume):
    return isinstance(volume, dict) and 0 < len(volume) <= 32 and all(
        isinstance(channel, str) and channel
        and type(value) is int and 0 <= value <= 0x7fffffff
        for channel, value in volume.items()
    )


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
    if "volumes" in state:
        volumes = state["volumes"]
        if not isinstance(volumes, dict) or set(volumes) != set(KINDS):
            raise AudioError("Invalid saved volume state")
        for kind in KINDS:
            devices = volumes[kind]
            if not isinstance(devices, dict) or any(
                name not in state[kind] or not valid_volume(volume)
                for name, volume in devices.items()
            ):
                raise AudioError("Invalid saved volume state; leaving audio unchanged")
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


def save(path, quiet=False):
    previous = load_state(path)
    current = snapshot()  # Both lists must succeed before replacing the file.
    if previous is not None:
        for kind in KINDS:
            current[kind] = {**previous[kind], **current[kind]}
        if "volumes" in previous or "volumes" in current:
            current["volumes"] = {
                kind: {**previous.get("volumes", {}).get(kind, {}),
                       **current.get("volumes", {}).get(kind, {})}
                for kind in KINDS
            }
    if not any(current[kind] for kind in KINDS):
        raise AudioError("No hardware audio devices available to save")
    if current != previous:
        write_state(path, current)
    if not quiet:
        print("Saved speaker and microphone volume/mute state", flush=True)


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
                    # Keep muted devices silent while restoring their volume.
                    if saved[kind][name]:
                        pactl(f"set-{kind[:-1]}-mute", name, "1")
                    volume = saved.get("volumes", {}).get(kind, {}).get(name)
                    channels = current.get("volumes", {}).get(kind, {}).get(name, {})
                    if volume and volume.keys() == channels.keys():
                        pactl(f"set-{kind[:-1]}-volume", name,
                              *(str(volume[channel]) for channel in channels))
                    if saved[kind][name]:
                        continue
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


def relevant_event(line):
    return b" on sink #" in line or b" on source #" in line


def watch(path, restore_first=False):
    """Save on server events, before logout can shut down the audio server."""
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR") or path.parent)
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (runtime / "audio-mute-state.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        stop = threading.Event()
        subscriber = None

        def stopping(*_):
            stop.set()
            if subscriber is not None and subscriber.poll() is None:
                subscriber.terminate()

        handlers = {sig: signal.signal(sig, stopping)
                    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT)}
        try:
            while not stop.is_set():
                try:
                    if restore_first:
                        restore(path)
                    if stop.is_set():
                        break
                    subscriber = subprocess.Popen(
                        ["/usr/bin/pactl", "subscribe"], stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, env={**os.environ, "LC_ALL": "C"},
                    )
                    with selectors.DefaultSelector() as events:
                        events.register(subscriber.stdout, selectors.EVENT_READ)
                        # Capture once after subscribing, including live activation.
                        save(path, quiet=True)
                        pending = None
                        buffer = b""
                        while not stop.is_set():
                            delay = None if pending is None else max(0, pending - time.monotonic())
                            ready = events.select(delay)
                            if ready:
                                chunk = os.read(subscriber.stdout.fileno(), 65536)
                                if not chunk:
                                    break
                                buffer += chunk
                                lines = buffer.split(b"\n")
                                buffer = lines.pop()
                                if any(relevant_event(line) for line in lines) and pending is None:
                                    pending = time.monotonic() + 0.15
                            if pending is not None and time.monotonic() >= pending:
                                save(path, quiet=True)
                                pending = None
                except (AudioError, OSError) as exc:
                    if not stop.is_set():
                        print(f"audio-mute-state: {exc}; retrying", file=sys.stderr, flush=True)
                finally:
                    if subscriber is not None:
                        if subscriber.poll() is None:
                            subscriber.terminate()
                        try:
                            subscriber.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            subscriber.kill()
                            subscriber.wait()
                        subscriber.stdout.close()
                        subscriber = None
                # Reapply saved settings if the audio server restarts mid-session.
                restore_first = True
                if not stop.is_set():
                    stop.wait(2)
        finally:
            try:
                save(path, quiet=True)
            except (AudioError, OSError):
                pass  # The last event has already been committed if audio is gone.
            for sig, handler in handlers.items():
                signal.signal(sig, handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("save", "restore", "watch"))
    parser.add_argument("--restore", action="store_true", help="Restore before watching a new login")
    args = parser.parse_args()
    state_root = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    path = state_root / "audio-mute-state/state.json"
    try:
        if args.action == "watch":
            watch(path, restore_first=args.restore)
        else:
            (save if args.action == "save" else restore)(path)
    except (AudioError, OSError) as exc:
        print(f"audio-mute-state: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
