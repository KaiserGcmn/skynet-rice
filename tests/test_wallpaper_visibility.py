"""Opt-in X11 integration checks; never run against the user's display.

Set SKYNET_TEST_DISPLAY to a private X server, SKYNET_TEST_XWINWRAP to the
staged executable, and SKYNET_TEST_VIDEO to a local test video. Ordinary test
runs skip these checks rather than opening windows on the current desktop.
"""
import ctypes as C
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
import unittest


DISPLAY = os.environ.get('SKYNET_TEST_DISPLAY')
BINARY = os.environ.get('SKYNET_TEST_XWINWRAP')
VIDEO = os.environ.get('SKYNET_TEST_VIDEO')


@unittest.skipUnless(DISPLAY and BINARY and VIDEO, 'requires private X11 fixture')
class WallpaperVisibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if DISPLAY in (':0', ':0.0'):
            raise RuntimeError('Refusing to use the primary display')
        cls.x = C.CDLL('libX11.so.6')
        cls.x.XOpenDisplay.argtypes = [C.c_char_p]
        cls.x.XOpenDisplay.restype = C.c_void_p
        cls.x.XDefaultRootWindow.argtypes = [C.c_void_p]
        cls.x.XDefaultRootWindow.restype = C.c_ulong
        cls.x.XCreateSimpleWindow.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_int,
                                            C.c_uint, C.c_uint, C.c_uint, C.c_ulong, C.c_ulong]
        cls.x.XCreateSimpleWindow.restype = C.c_ulong
        for name in ('XMapRaised', 'XDestroyWindow'):
            getattr(cls.x, name).argtypes = [C.c_void_p, C.c_ulong]
        cls.x.XResizeWindow.argtypes = [C.c_void_p, C.c_ulong, C.c_uint, C.c_uint]
        cls.x.XSync.argtypes = [C.c_void_p, C.c_int]
        cls.x.XCloseDisplay.argtypes = [C.c_void_p]
        cls.display = cls.x.XOpenDisplay(DISPLAY.encode())
        if not cls.display:
            raise RuntimeError('Private display unavailable')
        cls.root = cls.x.XDefaultRootWindow(cls.display)

    @classmethod
    def tearDownClass(cls):
        cls.x.XCloseDisplay(cls.display)

    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix='skynet-visibility-test-')
        self.socket = Path(self.work.name) / 'mpv.sock'
        self.process = None
        self.windows = []

    def tearDown(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()
        for window in self.windows:
            self.x.XDestroyWindow(self.display, window)
        self.x.XSync(self.display, False)
        self.work.cleanup()

    def cover(self, width=800):
        window = self.x.XCreateSimpleWindow(self.display, self.root, 0, 0,
                                            width, 600, 0, 0, 0)
        self.windows.append(window)
        self.x.XMapRaised(self.display, window)
        self.x.XSync(self.display, False)
        return window

    def request(self, *command):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(1)
            connection.connect(str(self.socket))
            connection.sendall(json.dumps({'command': command, 'request_id': 77}).encode() + b'\n')
            with connection.makefile('rb') as stream:
                for line in stream:
                    data = json.loads(line)
                    if data.get('request_id') == 77:
                        if command[0] == 'get_property' and data.get('error') == 'property unavailable':
                            return None  # mpv has not decoded its first frame yet.
                        self.assertEqual(data.get('error'), 'success', data)
                        return data.get('data')
        raise RuntimeError('No IPC reply')

    def until(self, function):
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            try:
                if function():
                    return
            except (OSError, ValueError):
                pass
            time.sleep(.03)
        log = Path(self.work.name, 'mpv.log')
        detail = log.read_text(errors='replace')[-2500:] if log.exists() else ''
        wrapper_log = Path(self.work.name, 'wrapper.log')
        if wrapper_log.exists():
            detail += '\n' + wrapper_log.read_text(errors='replace')[-2500:]
        detail += '\n' + subprocess.check_output(
            ['xwininfo', '-root', '-tree'], env=dict(os.environ, DISPLAY=DISPLAY), text=True)
        self.fail('Condition did not become true: ' + detail)

    def launch(self, delay=0):
        player = ['/usr/bin/mpv', '--no-config', '--load-scripts=no', '--vo=gpu',
                  '--gpu-api=opengl', '--gpu-context=x11egl',
                  '--log-file=' + str(Path(self.work.name, 'mpv.log')),
                  '--no-audio', '--no-sub', '--loop-file=inf', '--no-terminal',
                  '--stop-screensaver=no', '--input-default-bindings=no',
                  '--input-vo-keyboard=no', '-wid', 'WID',
                  '--input-ipc-server=' + str(self.socket), VIDEO]
        if delay:
            player = ['/usr/bin/python3', '-c',
                      'import os,sys,time;time.sleep(.5);os.execv(sys.argv[1],sys.argv[1:])', *player]
        with Path(self.work.name, 'wrapper.log').open('wb') as log:
            self.process = subprocess.Popen(
                [BINARY, '-debug', '-ovr', '-ni', '-nf', '-b', '-fdt',
                 '-pause-hidden', str(self.socket), '--', *player],
                env=dict(os.environ, DISPLAY=DISPLAY), start_new_session=True,
                stdout=log, stderr=log)
        self.until(lambda: self.socket.exists() and self.request('get_property', 'video-params'))

    def test_full_coverage_pauses_partial_coverage_resumes(self):
        self.launch()
        self.until(lambda: self.request('get_property', 'pause') is False)
        window = self.cover(400)
        time.sleep(.15)
        self.assertFalse(self.request('get_property', 'pause'))
        self.x.XResizeWindow(self.display, window, 800, 600)
        self.x.XSync(self.display, False)
        self.until(lambda: self.request('get_property', 'pause') is True)
        before = self.request('get_property', 'time-pos')
        time.sleep(.2)
        self.assertAlmostEqual(before, self.request('get_property', 'time-pos'), places=3)
        self.x.XResizeWindow(self.display, window, 400, 600)
        self.x.XSync(self.display, False)
        self.until(lambda: self.request('get_property', 'pause') is False)
        before = self.request('get_property', 'time-pos')
        time.sleep(.2)
        self.assertNotEqual(before, self.request('get_property', 'time-pos'))

    def test_hidden_startup_file_change_and_quit_remain_responsive(self):
        self.cover()
        self.launch(delay=.5)
        self.until(lambda: self.request('get_property', 'pause') is True)
        self.request('loadfile', VIDEO, 'replace')
        self.until(lambda: self.request('get_property', 'video-params'))
        self.assertTrue(self.request('get_property', 'pause'))
        self.request('quit')
        self.assertEqual(self.process.wait(timeout=3), 0)

    def test_missing_socket_does_not_block_child_exit(self):
        for _ in range(3):
            self.process = subprocess.Popen(
                [BINARY, '-ovr', '-pause-hidden', str(self.socket), '--', '/bin/true'],
                env=dict(os.environ, DISPLAY=DISPLAY), start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.assertEqual(self.process.wait(timeout=2), 0)

    def test_termination_is_forwarded_while_paused(self):
        self.cover()
        self.launch()
        self.until(lambda: self.request('get_property', 'pause') is True)
        pid = self.request('get_property', 'pid')
        self.process.terminate()
        self.assertEqual(self.process.wait(timeout=3), 0)
        self.assertFalse(Path('/proc', str(pid)).exists())

    def test_legacy_invocation_still_exits(self):
        self.process = subprocess.Popen(
            [BINARY, '-ovr', '--', '/bin/true'], env=dict(os.environ, DISPLAY=DISPLAY),
            start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertEqual(self.process.wait(timeout=2), 0)


if __name__ == '__main__':
    unittest.main()
