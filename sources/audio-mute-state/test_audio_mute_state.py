import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import audio_mute_state as audio


SPEAKER = "alsa_output.pci-speaker"
MIC = "alsa_input.pci-microphone"
BLUETOOTH = "bluez_output.test-headset"


def state(speaker=True, mic=False):
    return {"version": 1, "sinks": {SPEAKER: speaker}, "sources": {MIC: mic}}


class Clock:
    now = 0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class MuteStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "audio/state.json"
        self.clock = Clock()
        self.enterContext(patch.object(audio.time, "monotonic", self.clock.monotonic))
        self.enterContext(patch.object(audio.time, "sleep", self.clock.sleep))
        self.enterContext(patch("builtins.print"))

    def install_backend(self, current):
        snapshot_mock = self.enterContext(patch.object(audio, "snapshot", side_effect=lambda: copy.deepcopy(current)))

        def set_mute(command, name, value):
            kind = {"set-sink-mute": "sinks", "set-source-mute": "sources"}[command]
            current[kind][name] = value == "1"

        command_mock = self.enterContext(patch.object(audio, "pactl", side_effect=set_mute))
        return snapshot_mock, command_mock

    def test_restore_both_mute_and_unmute_independently(self):
        for speaker, mic in ((True, False), (False, True), (True, True), (False, False)):
            with self.subTest(speaker=speaker, mic=mic):
                saved = state(speaker, mic)
                audio.write_state(self.path, saved)
                current = state(not speaker, not mic)
                with patch.object(audio, "snapshot", side_effect=lambda: copy.deepcopy(current)):
                    def set_mute(command, name, value):
                        kind = "sinks" if command == "set-sink-mute" else "sources"
                        current[kind][name] = value == "1"
                    with patch.object(audio, "pactl", side_effect=set_mute) as commands:
                        audio.restore(self.path)
                        self.assertEqual(current, saved)
                        self.assertEqual(commands.call_count, 2)

    def test_first_start_captures_without_changing_audio(self):
        current = state()
        _, commands = self.install_backend(current)
        audio.restore(self.path)
        commands.assert_not_called()
        self.assertEqual(audio.load_state(self.path), current)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_numeric_indices_ignored_and_monitors_and_virtual_devices_excluded(self):
        sinks = [
            {"name": SPEAKER, "index": 99, "mute": True},
            {"name": "auto_null", "index": 1, "mute": False},
            {"name": "virtual-capture", "index": 2, "mute": False},
        ]
        sources = [
            {"name": MIC, "index": 700, "mute": False},
            {"name": SPEAKER + ".monitor", "index": 701, "mute": True},
        ]
        with patch.object(audio, "pactl", side_effect=[json.dumps(sinks), json.dumps(sources)]):
            self.assertEqual(audio.snapshot(), state())

    def test_unrelated_new_device_unchanged(self):
        audio.write_state(self.path, state())
        current = state(False, True)
        current["sinks"][BLUETOOTH] = False
        _, commands = self.install_backend(current)
        audio.restore(self.path)
        self.assertFalse(current["sinks"][BLUETOOTH])
        self.assertEqual(commands.call_count, 2)

    def test_disconnected_devices_retained_when_saving(self):
        previous = state()
        previous["sinks"][BLUETOOTH] = True
        audio.write_state(self.path, previous)
        self.install_backend(state(False, True))
        audio.save(self.path)
        self.assertEqual(audio.load_state(self.path), {
            "version": 1, "sinks": {SPEAKER: False, BLUETOOTH: True}, "sources": {MIC: True},
        })

    def test_disconnected_devices_do_not_fail_restore(self):
        saved = state()
        saved["sinks"][BLUETOOTH] = True
        audio.write_state(self.path, saved)
        current = state(False, True)
        _, commands = self.install_backend(current)
        audio.restore(self.path, timeout=3)
        self.assertEqual(current, state())
        self.assertEqual(commands.call_count, 2)
        self.assertEqual(audio.load_state(self.path), saved)

    def test_waits_for_server_and_late_microphone(self):
        audio.write_state(self.path, state())
        current = state(False, True)
        snapshots, _ = self.install_backend(current)
        calls = 0

        def readiness():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise audio.AudioError("server not ready")
            result = copy.deepcopy(current)
            if calls < 4:
                result["sources"] = {}
            return result

        snapshots.side_effect = readiness
        audio.restore(self.path)
        self.assertEqual(current, state())
        self.assertGreaterEqual(calls, 5)

    def test_policy_override_gets_reapplied(self):
        audio.write_state(self.path, state())
        current = state(False, True)
        snapshots, _ = self.install_backend(current)
        calls = 0

        def readiness():
            nonlocal calls
            calls += 1
            if calls == 2:
                current["sinks"][SPEAKER] = False
            return copy.deepcopy(current)

        snapshots.side_effect = readiness
        audio.restore(self.path)
        self.assertEqual(current, state())

    def test_invalid_saved_state_does_not_touch_audio(self):
        self.path.parent.mkdir()
        for contents in ('{', '{"version":1,"sinks":{},"sources":{"alsa_input.mic":0}}'):
            self.path.write_text(contents)
            with patch.object(audio, "pactl") as commands:
                with self.assertRaises(audio.AudioError):
                    audio.restore(self.path)
                commands.assert_not_called()
            self.assertEqual(self.path.read_text(), contents)

    def test_partial_snapshot_failure_preserves_previous_state(self):
        audio.write_state(self.path, state())
        before = self.path.read_bytes()
        with patch.object(audio, "pactl", side_effect=[
            json.dumps([{"name": SPEAKER, "mute": False}]),
            audio.AudioError("source list failed"),
        ]):
            with self.assertRaises(audio.AudioError):
                audio.save(self.path)
        self.assertEqual(self.path.read_bytes(), before)

    def test_failed_atomic_replace_preserves_previous_state(self):
        audio.write_state(self.path, state())
        before = self.path.read_bytes()
        with patch.object(audio.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                audio.write_state(self.path, state(False, True))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_unavailable_server_fails_without_replacing_state(self):
        audio.write_state(self.path, state())
        before = self.path.read_bytes()
        with patch.object(audio, "snapshot", side_effect=audio.AudioError("offline")):
            with self.assertRaises(audio.AudioError):
                audio.restore(self.path, timeout=3)
        self.assertEqual(self.path.read_bytes(), before)

    def test_volume_snapshot_preserves_channel_order_and_excludes_monitors(self):
        devices = [{"name": SPEAKER, "mute": False,
                    "channel_map": "front-right,front-left",
                    "volume": {"front-left": {"value": 20000},
                               "front-right": {"value": 30000}}}]
        with patch.object(audio, "pactl", side_effect=[json.dumps(devices), "[]"]):
            saved = audio.snapshot()
        self.assertEqual(list(saved["volumes"]["sinks"][SPEAKER]),
                         ["front-right", "front-left"])
        self.assertEqual(saved["volumes"]["sinks"][SPEAKER]["front-left"], 20000)

    def test_restore_channel_volumes_before_unmuting_and_after_muting(self):
        for muted in (True, False):
            with self.subTest(muted=muted):
                saved = state(muted, not muted)
                saved["volumes"] = {
                    "sinks": {SPEAKER: {"front-left": 20000, "front-right": 30000}},
                    "sources": {MIC: {"mono": 45000}},
                }
                audio.write_state(self.path, saved)
                current = state(not muted, muted)
                current["volumes"] = {
                    "sinks": {SPEAKER: {"front-right": 40000, "front-left": 40000}},
                    "sources": {MIC: {"mono": 10000}},
                }

                def apply(command, name, *values):
                    kind = "sinks" if command.startswith("set-sink-") else "sources"
                    if command.endswith("-mute"):
                        current[kind][name] = values[0] == "1"
                    else:
                        channels = current["volumes"][kind][name]
                        current["volumes"][kind][name] = dict(zip(channels, map(int, values)))

                with patch.object(audio, "snapshot", side_effect=lambda: copy.deepcopy(current)):
                    with patch.object(audio, "pactl", side_effect=apply) as commands:
                        audio.restore(self.path)
                self.assertEqual(current, saved)
                sink_calls = [call.args for call in commands.call_args_list if call.args[1] == SPEAKER]
                self.assertIn(("set-sink-volume", SPEAKER, "30000", "20000"), sink_calls)
                self.assertEqual(sink_calls[0][0], "set-sink-mute" if muted else "set-sink-volume")

    def test_invalid_volumes_rejected_before_any_change(self):
        for value in (-1, True, 0x80000000, "50000"):
            saved = state()
            saved["volumes"] = {"sinks": {SPEAKER: {"mono": value}}, "sources": {}}
            audio.write_state(self.path, saved)
            with patch.object(audio, "pactl") as commands:
                with self.assertRaises(audio.AudioError):
                    audio.restore(self.path)
                commands.assert_not_called()

    def test_changed_channel_layout_keeps_volume_and_restores_mute(self):
        saved = state()
        saved["volumes"] = {"sinks": {SPEAKER: {"mono": 40000}}, "sources": {}}
        audio.write_state(self.path, saved)
        current = state(False, True)
        current["volumes"] = {"sinks": {SPEAKER: {"front-left": 100, "front-right": 200}}, "sources": {}}
        _, commands = self.install_backend(current)
        audio.restore(self.path)
        self.assertEqual(commands.call_count, 2)
        self.assertEqual(current["volumes"]["sinks"][SPEAKER], {"front-left": 100, "front-right": 200})

    def test_save_preserves_disconnected_volumes_and_avoids_rewriting(self):
        previous = state()
        previous["sinks"][BLUETOOTH] = True
        previous["volumes"] = {"sinks": {BLUETOOTH: {"mono": 22000}}, "sources": {}}
        audio.write_state(self.path, previous)
        self.install_backend(state())
        with patch.object(audio, "write_state", wraps=audio.write_state) as writes:
            audio.save(self.path, quiet=True)
            writes.assert_not_called()
        self.assertEqual(audio.load_state(self.path), previous)

    def test_subscriber_filters_client_and_stream_events(self):
        self.assertTrue(audio.relevant_event(b"Event 'change' on sink #4"))
        self.assertTrue(audio.relevant_event(b"Event 'change' on source #2"))
        self.assertFalse(audio.relevant_event(b"Event 'change' on sink-input #4"))
        self.assertFalse(audio.relevant_event(b"Event 'new' on client #42"))


if __name__ == "__main__":
    unittest.main()
