"""Exercise control boundaries without changing real audio or backlight state."""
import contextlib
import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    loader = importlib.machinery.SourceFileLoader(
        name.replace('-', '_'), str(ROOT / 'runtime/usr/local/libexec' / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ControlsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controls = load('dwm-lock-controls')

    @contextlib.contextmanager
    def fake_io(self):
        c = self.controls
        with patch.object(c.os, 'open', return_value=100), \
             patch.object(c.os, 'close'), patch.object(c.fcntl, 'flock'), \
             patch.object(c, 'command', return_value='') as command:
            yield command

    def test_volume_bounds_and_unmute_only_on_raise(self):
        c = self.controls
        for start, action, target in [(98, 'volume-up', '100%'),
                                      (2, 'volume-down', '0%'),
                                      (150, 'volume-up', '100%')]:
            with self.subTest(action=action, start=start), self.fake_io() as run, \
                 patch.object(c, 'audio_status', return_value=(start, 1, 70, 1)):
                c.action(action)
                self.assertEqual(run.call_args_list[0].args,
                                 ('/usr/bin/pactl', 'set-sink-volume', '@DEFAULT_SINK@', target))
                self.assertEqual(run.call_count, 2 if action == 'volume-up' else 1)

    def test_speaker_and_microphone_mutes_are_independent(self):
        with self.fake_io() as run:
            self.controls.action('mic-mute')
            run.assert_called_once_with('/usr/bin/pactl', 'set-source-mute',
                                        '@DEFAULT_SOURCE@', 'toggle')
        with self.fake_io() as run:
            self.controls.action('volume-mute')
            run.assert_called_once_with('/usr/bin/pactl', 'set-sink-mute',
                                        '@DEFAULT_SINK@', 'toggle')

    def test_backlight_floor_and_screen_device(self):
        c = self.controls
        with self.fake_io() as run, patch.object(c, 'backlight', return_value=('intel_backlight', 38400, 1920)):
            c.action('brightness-down')
            run.assert_called_once_with('/usr/bin/brightnessctl', '--class=backlight',
                                        '--device=intel_backlight', '--min-value=1920',
                                        '--quiet', 'set', '5%-')

    def test_default_device_selection_and_unknown(self):
        c = self.controls
        devices = [dict(name='other', mute=False, volume={'mono': {'value': 65536}}),
                   dict(name='wanted', mute=True, volume={'left': {'value': 32768},
                                                         'right': {'value': 16384}})]
        self.assertEqual(c.device_status(devices, 'wanted'), (50, 1))
        self.assertEqual(c.device_status(devices, 'missing'), (-1, -1))
        with patch.object(c, 'command', side_effect=OSError):
            self.assertEqual(c.audio_status(), (-1, -1, -1, -1))
        with patch.object(c, 'audio_status', return_value=(-1, -1, -1, -1)), self.fake_io() as run:
            c.action('volume-up')
            run.assert_not_called()

    def test_unknown_actions_cannot_run_commands(self):
        with self.fake_io() as run:
            for action in ('poweroff', 'volume-up; id', '--exec', 'mic-volume-up'):
                with self.assertRaises(ValueError):
                    self.controls.action(action)
            run.assert_not_called()

    def test_status_reads_without_writing_backlight(self):
        c = self.controls
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            device = root / 'display'
            device.mkdir()
            (device / 'max_brightness').write_text('1000')
            (device / 'brightness').write_text('375')
            with patch.object(c, 'BACKLIGHT', root):
                self.assertEqual(c.brightness(), 38)
                self.assertEqual((device / 'brightness').read_text(), '375')
                (device / 'max_brightness').write_text('0')
                self.assertEqual(c.brightness(), -1)

    def test_launcher_has_only_fixed_commands_and_preserves_auth(self):
        locker = load('dwm-lock')
        with patch.dict(locker.os.environ, {
                'DISPLAY': ':190', 'XSECURELOCK_KEY_F1_COMMAND': 'bad',
                'XSECURELOCK_AUTH': '/bin/true'}, clear=True), \
             patch.object(locker, 'choose_locker', return_value='/usr/bin/xsecurelock'), \
             patch.object(locker.os, 'umask'), patch.object(locker.resource, 'setrlimit'):
            binary, env = locker.lock_command('test', None)
        self.assertEqual(binary, '/usr/bin/xsecurelock')
        bindings = {k: v for k, v in env.items() if k.startswith('XSECURELOCK_KEY_')}
        self.assertEqual(len(bindings), 6)
        self.assertNotIn('XSECURELOCK_KEY_F1_COMMAND', env)
        self.assertEqual(set(bindings.values()), {
            '/usr/local/libexec/dwm-lock-controls ' + name for name in self.controls.ACTIONS})
        self.assertEqual(env['XSECURELOCK_AUTHPROTO'], '/usr/libexec/xsecurelock/authproto_pam')
        self.assertEqual(env['XSECURELOCK_PAM_SERVICE'], 'dwm-fingerprint')
        self.assertEqual(env['XSECURELOCK_AUTH'], '/usr/libexec/xsecurelock/auth_x11')
        # Fixed prompt position: a random burn-in offset pushed the fingerprint
        # window over the frame captions. The locker core also reads the
        # fingerprint timeout to keep the screen lit through that prompt.
        self.assertEqual(env['XSECURELOCK_BURNIN_MITIGATION'], '0')
        self.assertEqual(env['XSECURELOCK_FPRINT_TIMEOUT'], '10')
        self.assertEqual(env['XSECURELOCK_BLANK_TIMEOUT'], '12')


if __name__ == '__main__':
    unittest.main()
