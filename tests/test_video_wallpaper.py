"""The tracked 4K video wallpaper stays a clean, publishable MP4."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / 'home/wallpapers/livewallpaperskynet.mp4'
SIZE_WARNING = 50 * 1024 * 1024  # GitHub warns about single files above 50 MiB


class VideoWallpaperTest(unittest.TestCase):
    def test_file_is_an_mp4_below_the_hosting_size_warning(self):
        self.assertTrue(VIDEO.is_file())
        self.assertLess(VIDEO.stat().st_size, SIZE_WARNING)
        with VIDEO.open('rb') as stream:
            self.assertEqual(stream.read(12)[4:8], b'ftyp')

    def test_stream_matches_the_documented_spec_and_carries_no_personal_tags(self):
        if not shutil.which('ffprobe'):
            self.skipTest('requires ffprobe')
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-print_format', 'json', '-show_format',
             '-show_streams', str(VIDEO)],
            check=True, capture_output=True, text=True)
        info = json.loads(result.stdout)
        video, = [s for s in info['streams'] if s['codec_type'] == 'video']
        self.assertEqual((video['codec_name'], video['width'], video['height']),
                         ('h264', 3840, 2160))
        self.assertEqual([s for s in info['streams'] if s['codec_type'] != 'video'], [])
        # Only technical tags: no title, artist, comment, location or creation time.
        self.assertLessEqual(set(info['format'].get('tags', {})),
                             {'major_brand', 'minor_version', 'compatible_brands', 'encoder'})
        self.assertLessEqual(set(video.get('tags', {})),
                             {'language', 'handler_name', 'vendor_id', 'encoder'})

    def test_wallpaper_guide_names_the_tracked_path(self):
        guide = (ROOT / 'docs/WALLPAPER.md').read_text()
        self.assertIn('home/wallpapers/livewallpaperskynet.mp4', guide)
        self.assertNotIn('depoya eklenmedi', guide)


if __name__ == '__main__':
    unittest.main()
