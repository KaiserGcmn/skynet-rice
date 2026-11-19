"""Startup races and bounded recovery without touching the real desktop."""
import importlib.machinery
import importlib.util
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch


SOURCE = Path(__file__).resolve().parents[1] / 'runtime/usr/local/bin/skynet-wallpaper'
loader = importlib.machinery.SourceFileLoader('wallpaper_startup', str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
wallpaper = importlib.util.module_from_spec(spec)
loader.exec_module(wallpaper)


class WallpaperStartupTest(unittest.TestCase):
    def test_slow_cold_start_survives_previous_eight_second_limit(self):
        elapsed = [0.0]

        def request(_, command):
            if elapsed[0] < 12:
                raise ConnectionRefusedError()
            return {'path': '/image.mp4', 'video-params': {'w': 1920},
                    'vo-configured': True, 'idle-active': False}[command[1]]

        with patch.object(wallpaper.time, 'monotonic', side_effect=lambda: elapsed[0]), \
             patch.object(wallpaper.time, 'sleep', side_effect=lambda delay: elapsed.__setitem__(0, elapsed[0] + delay)), \
             patch.object(wallpaper, 'request', side_effect=request):
            wallpaper.wait_for_file(Path('/socket'), Path('/image.mp4'), Mock(poll=lambda: None))
        self.assertGreaterEqual(elapsed[0], 12)

    def test_failed_first_start_is_cleaned_before_one_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = Mock(), Mock()
            with patch.object(wallpaper.subprocess, 'Popen', side_effect=[first, second]) as launch, \
                 patch.object(wallpaper, 'wait_for_file', side_effect=[RuntimeError('cold start'), None]), \
                 patch.object(wallpaper, 'stop_player') as stop, patch.object(wallpaper.time, 'sleep'):
                wallpaper.start(root, root/'socket', Path('/image.mp4'))
            self.assertEqual(launch.call_count, 2)
            stop.assert_called_once_with(first)
            self.assertTrue(launch.call_args.kwargs['start_new_session'])

    def test_repeated_failure_has_bounded_retries_and_no_stale_socket(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            endpoint = root/'socket'
            endpoint.touch()
            with patch.object(wallpaper.subprocess, 'Popen') as launch, \
                 patch.object(wallpaper, 'wait_for_file', side_effect=RuntimeError('not ready')), \
                 patch.object(wallpaper, 'stop_player') as stop, patch.object(wallpaper.time, 'sleep'):
                with self.assertRaises(RuntimeError):
                    wallpaper.start(root, endpoint, Path('/image.mp4'))
            self.assertEqual(launch.call_count, 2)
            self.assertEqual(stop.call_count, 2)
            self.assertFalse(endpoint.exists())

    def test_existing_player_is_checked_without_spawning_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(wallpaper.fcntl, 'flock', side_effect=BlockingIOError), \
                 patch.object(wallpaper, 'wait_for_file') as ready, \
                 patch.object(wallpaper.subprocess, 'Popen') as launch:
                wallpaper.start(root, root/'socket', Path('/image.mp4'))
            ready.assert_called_once_with(root/'socket')
            launch.assert_not_called()

    def test_exited_player_fails_immediately(self):
        with patch.object(wallpaper, 'request') as request:
            with self.assertRaisesRegex(RuntimeError, 'exited'):
                wallpaper.wait_for_file(Path('/socket'), child=Mock(poll=lambda: 1))
        request.assert_not_called()

    def test_cleanup_targets_only_the_new_process_group(self):
        child = Mock(pid=123456)
        child.wait.side_effect = [subprocess.TimeoutExpired('test', 3), 0]
        with patch.object(wallpaper.os, 'killpg') as kill:
            wallpaper.stop_player(child)
        self.assertEqual([c.args for c in kill.call_args_list],
                         [(123456, signal.SIGTERM), (123456, signal.SIGKILL)])


if __name__ == '__main__':
    unittest.main()
