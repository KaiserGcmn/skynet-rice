"""Exercise volume-key feedback with fake audio and notification commands."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'runtime/usr/local/bin/dwm-volume'
FAKE = '''#!/usr/bin/python3
import json,os,sys,time
from pathlib import Path
name=Path(sys.argv[0]).name
with open(os.environ['TEST_CALLS'],'a') as f:
    f.write(json.dumps([name,*sys.argv[1:]])+'\\n')
if name=='pactl':
    if sys.argv[1]=='get-sink-volume':
        print('Volume: front-left: 32768 / '+os.environ['TEST_LEVEL']+'% / -18.00 dB')
    elif sys.argv[1] in ('get-sink-mute','get-source-mute'):
        print('Mute: '+os.environ['TEST_MUTED'])
elif name=='mpv':
    try:
        os.fstat(9)
        Path(os.environ['TEST_BAD_FD']).touch()
    except OSError:
        pass
    time.sleep(.45)
'''


class VolumeFeedbackTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix='skynet-volume-test-')
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name in ['pactl', 'dunstify', 'mpv']:
            p = self.bin / name
            p.write_text(FAKE)
            p.chmod(0o755)
        self.sound = self.root / 'Soundleveltest.mp3'
        self.sound.touch()
        self.calls = self.root / 'calls'
        self.calls.touch()
        self.bad_fd = self.root / 'inherited-control-lock'
        self.env = dict(os.environ, PATH=f'{self.bin}:/usr/bin:/bin',
                        XDG_RUNTIME_DIR=str(self.root),
                        SKYNET_VOLUME_SOUND=str(self.sound),
                        TEST_CALLS=str(self.calls), TEST_LEVEL='50', TEST_MUTED='no',
                        TEST_BAD_FD=str(self.bad_fd))

    def run_action(self, action):
        return subprocess.run(['/bin/sh', str(SCRIPT), action], env=self.env,
                              capture_output=True, timeout=1, check=True)

    def players(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()
                if json.loads(line)[0] == 'mpv']

    def await_player(self):
        deadline = time.monotonic() + 1
        while not self.players() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertEqual(len(self.players()), 1)

    def test_both_level_keys_play_selected_file_without_holding_control_lock(self):
        for action in ['up', 'down']:
            with self.subTest(action=action):
                self.calls.write_text('')
                self.run_action(action)
                self.await_player()
                self.assertEqual(self.players()[0][-1], str(self.sound))
                # Playback must not block subsequent level/notification updates.
                with (self.root / 'dwm-volume.lock').open('r') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertFalse(self.bad_fd.exists())
                time.sleep(.5)

    def test_muted_zero_missing_file_and_nonlevel_actions_are_silent(self):
        for action, level, muted in [('show','50','no'), ('mute','50','no'),
                                     ('mic-mute','50','no'), ('down','0','no'),
                                     ('down','50','yes')]:
            with self.subTest(action=action, level=level, muted=muted):
                self.env.update(TEST_LEVEL=level, TEST_MUTED=muted)
                self.run_action(action)
        self.env.update(TEST_LEVEL='50', TEST_MUTED='no')
        self.sound.unlink()
        self.run_action('up')
        time.sleep(.05)
        self.assertEqual(self.players(), [])

    def test_busy_feedback_does_not_queue_or_block_level_change(self):
        with (self.root / 'dwm-volume-feedback.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.run_action('up')
            self.run_action('down')
            time.sleep(.05)
            self.assertEqual(self.players(), [])
        time.sleep(.05)
        self.assertEqual(self.players(), [])
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()]
        self.assertIn(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '55%'], calls)
        self.assertIn(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-5%'], calls)


if __name__ == '__main__':
    unittest.main()
