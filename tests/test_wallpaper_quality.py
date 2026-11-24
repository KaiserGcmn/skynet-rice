"""GIF wallpapers keep full colour and are not rescaled when edges are black."""
import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'runtime/usr/local/bin/dwm-wallpaper'
loader = importlib.machinery.SourceFileLoader('wallpaper_quality', str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
wallpaper = importlib.util.module_from_spec(spec)
loader.exec_module(wallpaper)


def frame(width, height, edge=0, inside=200):
    pixels = bytearray([inside]) * (width * height)
    for y in range(height):
        for x in range(width):
            if x < 4 or y < 4 or x >= width - 4 or y >= height - 4:
                pixels[y * width + x] = edge
    return bytes(pixels)


class EdgeTest(unittest.TestCase):
    def test_black_or_dithered_black_edges_letterbox(self):
        self.assertTrue(wallpaper.black_edges(frame(32, 18), 32, 18))
        self.assertTrue(wallpaper.black_edges(frame(32, 18, edge=12), 32, 18))

    def test_bright_edge_keeps_fill(self):
        self.assertFalse(wallpaper.black_edges(frame(32, 18, edge=90), 32, 18))
        pixels = bytearray(frame(32, 18))
        pixels[17 * 32 + 16] = 255          # one bright pixel on the bottom row
        self.assertFalse(wallpaper.black_edges(bytes(pixels), 32, 18))
        pixels = bytearray(frame(32, 18))
        pixels[9 * 32 + 31] = 255           # and on the right column
        self.assertFalse(wallpaper.black_edges(bytes(pixels), 32, 18))

    def test_short_or_tiny_frames_keep_fill(self):
        self.assertFalse(wallpaper.black_edges(b'\0' * 10, 32, 18))
        self.assertFalse(wallpaper.black_edges(b'\0' * 16, 4, 4))

    def test_probe_failure_falls_back_to_fill(self):
        with patch.object(wallpaper.subprocess, 'run',
                          side_effect=subprocess.CalledProcessError(1, 'ffprobe')):
            self.assertEqual(wallpaper.fit_mode(Path('/missing.mp4')), '1')


class EncodeTest(unittest.TestCase):
    def test_gif_is_encoded_as_full_colour_hevc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gif = root / 'art.gif'
            gif.write_bytes(b'GIF89a test')

            def encode(command, **_):
                Path(command[-1]).write_bytes(b'video')
                return subprocess.CompletedProcess(command, 0, '', '')

            with patch.dict(wallpaper.os.environ, {'XDG_CACHE_HOME': str(root)}), \
                 patch.object(wallpaper.shutil, 'which', return_value='/usr/bin/ffmpeg'), \
                 patch.object(wallpaper.subprocess, 'run', side_effect=encode) as run:
                target = wallpaper.playback_file(gif)
            command = run.call_args.args[0]
            self.assertIn('yuv444p', command)
            self.assertIn('libx265', command)
            self.assertNotIn('yuv420p', command)
            self.assertEqual(command[command.index('-crf') + 1], '4')
            self.assertTrue(target.name.endswith('-hevc444.mp4'))
            self.assertTrue(wallpaper.CACHE_NAME.fullmatch(target.name))

    def test_prune_removes_old_420_cache_but_not_other_files(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / 'dwm-wallpaper'
            cache.mkdir()
            digest = 'a' * 64
            old = cache / f'gif-{digest}.mp4'
            current = cache / f'gif-{"b" * 64}-hevc444.mp4'
            other = cache / 'gif-notes.mp4'
            for path in (old, current, other):
                path.write_bytes(b'x')
            with patch.dict(wallpaper.os.environ, {'XDG_CACHE_HOME': directory}):
                wallpaper.prune_cache(current)
            self.assertFalse(old.exists())
            self.assertTrue(current.exists())
            self.assertTrue(other.exists())


if __name__ == '__main__':
    unittest.main()
