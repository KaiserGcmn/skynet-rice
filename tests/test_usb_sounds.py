"""USB notification checks using disposable sysfs and event fixtures."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


HELPER = Path(__file__).resolve().parents[1] / 'runtime/usr/local/bin/skynet-usb-sounds'
loader = importlib.machinery.SourceFileLoader('usb_sounds', str(HELPER))
spec = importlib.util.spec_from_loader(loader.name, loader)
usb = importlib.util.module_from_spec(spec)
loader.exec_module(usb)


class UsbSoundsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='skynet-usb-test-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / 'bus/usb/devices').mkdir(parents=True)

    def device(self, name='1-2', removable='removable'):
        path = self.root / 'devices/pci/usb1' / name
        path.mkdir(parents=True, exist_ok=True)
        (path / 'idVendor').write_text('1234\n')
        (path / 'removable').write_text(removable + '\n')
        (self.root / 'bus/usb/devices' / name).symlink_to(path)
        return '/' + str(path.relative_to(self.root))

    def event(self, action, path, devtype='usb_device', product=None):
        properties = {'ACTION': action, 'DEVPATH': path, 'SUBSYSTEM': 'usb',
                      'DEVTYPE': devtype}
        if product:
            properties['PRODUCT'] = product
        return properties

    def test_startup_is_silent_but_removing_existing_device_is_reported(self):
        path = self.device()
        state = usb.Devices(self.root)
        self.assertIsNone(state.event(self.event('add', path)))
        self.assertEqual(state.event(self.event('remove', path)), 'remove')
        self.assertIsNone(state.event(self.event('remove', path)))

    def test_one_sound_per_device_not_per_interface_or_change(self):
        state = usb.Devices(self.root)
        path = self.device()
        self.assertIsNone(state.event(self.event('add', path, 'usb_interface')))
        self.assertEqual(state.event(self.event('add', path)), 'add')
        self.assertIsNone(state.event(self.event('add', path)))
        self.assertIsNone(state.event(self.event('change', path)))
        # Removal needs cached identity, not sysfs files that are already gone.
        for file in (self.root / path.lstrip('/')).iterdir():
            file.unlink()
        self.assertEqual(state.event(self.event('remove', path)), 'remove')

    def test_fixed_devices_root_hubs_and_unknown_removals_are_silent(self):
        state = usb.Devices(self.root)
        for path in (self.device('1-3', 'fixed'), self.device('usb2', 'unknown')):
            self.assertIsNone(state.event(self.event('add', path)))
            self.assertIsNone(state.event(self.event('remove', path)))
        self.assertIsNone(state.event(self.event('remove', '/devices/absent')))

    def test_reconnection_and_unknown_external_port(self):
        state = usb.Devices(self.root)
        path = self.device(removable='unknown')
        for action in ['add', 'remove', 'add', 'remove']:
            self.assertEqual(state.event(self.event(action, path)), action)

    def test_fragmented_udev_blocks_keep_add_and_remove_separate(self):
        events = usb.Events()
        stream = (b'monitor will print the received events for:\n\n'
                  b'UDEV [1.0] add /devices/a (usb)\nACTION=add\n'
                  b'DEVTYPE=usb_device\nDEVPATH=/devices/a\nSUBSYSTEM=usb\n\n'
                  b'UDEV [2.0] remove /devices/a (usb)\nACTION=remove\n'
                  b'DEVTYPE=usb_device\nDEVPATH=/devices/a\nSUBSYSTEM=usb\n\n')
        results = []
        for i in range(0, len(stream), 7):
            results.extend(events.feed(stream[i:i + 7]))
        self.assertEqual([r['ACTION'] for r in results], ['add', 'remove'])
        self.assertEqual([r['DEVPATH'] for r in results], ['/devices/a'] * 2)

    def test_duplicate_launch_exits_without_starting_monitor(self):
        fd = usb.acquire_lock(self.root)
        try:
            result = subprocess.run(
                ['/usr/bin/python3', str(HELPER)],
                env=dict(os.environ, XDG_RUNTIME_DIR=str(self.root)),
                capture_output=True, timeout=3)
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            os.close(fd)

    def test_runtime_lock_rejects_public_directory_and_symlink(self):
        self.root.chmod(0o755)
        with self.assertRaises(RuntimeError):
            usb.acquire_lock(self.root)
        self.root.chmod(0o700)
        (self.root / 'skynet-usb-sounds.lock').symlink_to(self.root / 'other')
        with self.assertRaises(OSError):
            usb.acquire_lock(self.root)

    def run_pipeline(self, first_burst, second_burst, state, session_seconds='1'):
        """Feed two udev bursts 0.2 s apart; return the sound files played."""
        for name in usb.SOUNDS.values():
            (self.root / name).touch()
        record = self.root / 'played'
        actual_popen = subprocess.Popen
        children = []
        def popen(command, **kwargs):
            if command[0] == '/usr/bin/udevadm':
                command = ['/usr/bin/python3', '-c',
                           'import sys,time;sys.stdout.write(sys.argv[1]);'
                           'sys.stdout.flush();time.sleep(.2);'
                           'sys.stdout.write(sys.argv[2]);sys.stdout.flush();'
                           'time.sleep(30)', first_burst, second_burst]
            elif command[0] == '/usr/bin/mpv':
                command = ['/usr/bin/python3', '-c',
                           'import sys,time;from pathlib import Path;'
                           'f=open(sys.argv[1],"a");'
                           'f.write(Path(sys.argv[2]).name+"\\n");f.close();'
                           'time.sleep(30)', str(record), command[-1]]
            child = actual_popen(command, **kwargs)
            children.append(child)
            return child
        with actual_popen(['/bin/sleep', session_seconds]) as session:
            try:
                with mock.patch.object(usb, 'Devices', return_value=state), \
                        mock.patch.object(usb, 'REPLUG_WINDOW', 0.3), \
                        mock.patch.object(usb.subprocess, 'Popen', side_effect=popen):
                    usb.monitor(self.root, session.pid)
                self.assertTrue(all(p.poll() is not None for p in children))
            finally:
                for child in children:
                    usb.stop(child)
        return record.read_text().splitlines() if record.exists() else []

    def block(self, action, path, product=None):
        return ''.join(f'{k}={v}\n' for k, v in
                       self.event(action, path, product=product).items()) + '\n'

    def test_event_pipeline_coalesces_hubs_and_stops_children_with_session(self):
        state = usb.Devices(self.root)
        first, second = self.device('1-2'), self.device('1-3')
        internal = self.device('1-4', 'fixed')
        added = (self.block('add', first) * 2 + self.block('add', second) +
                 self.block('add', internal))
        removed = self.block('remove', first) * 2 + self.block('remove', second)
        self.assertEqual(self.run_pipeline(added, removed, state),
                         list(usb.SOUNDS.values()))

    def test_usb3_mode_switch_after_plugging_makes_one_sound(self):
        # Archer T3U, 2026-11-21 14:58: USB 2 arrival, rtw88 drops it and it
        # returns 0.5 s later on the SuperSpeed bus with another bcdDevice.
        state = usb.Devices(self.root)
        usb2, usb3 = self.device('3-9'), self.device('2-3')
        burst = (self.block('add', usb2, '2357/138/210') +
                 self.block('remove', usb2, '2357/138/210'))
        again = self.block('add', usb3, '2357/0138/300')
        self.assertEqual(self.run_pipeline(burst, again, state),
                         ['Usbdeviceconnected.mp3'])

    def test_real_unplug_is_still_announced_after_the_window(self):
        state = usb.Devices(self.root)
        path = self.device('3-9')
        played = self.run_pipeline(self.block('add', path, '2357/138/210'),
                                   self.block('remove', path, '2357/138/210'), state)
        self.assertEqual(played, list(usb.SOUNDS.values()))


class ReplugTest(unittest.TestCase):
    def test_identity_ignores_usb_mode_and_leading_zeros(self):
        self.assertEqual(usb.identity({'PRODUCT': '2357/138/210'}),
                         usb.identity({'PRODUCT': '2357/0138/300'}))
        self.assertNotEqual(usb.identity({'PRODUCT': '2357/138/210'}),
                            usb.identity({'PRODUCT': '2357/120/210'}))
        self.assertEqual(usb.identity({'DEVPATH': '/devices/x'}), '/devices/x')

    def test_default_window_covers_the_measured_reenumeration(self):
        # Measured gap: USB disconnect 14:58:02.113 -> SuperSpeed add .629.
        self.assertGreaterEqual(usb.REPLUG_WINDOW, 1.0)
        self.assertLessEqual(usb.REPLUG_WINDOW, 3.0)
        self.assertEqual(usb.Replug().window, usb.REPLUG_WINDOW)

    def test_quick_return_cancels_both_sounds(self):
        replug = usb.Replug(window=1.5)
        self.assertEqual(replug.feed('add', 'tp', 0.0), 'add')
        self.assertIsNone(replug.feed('remove', 'tp', 0.3))
        self.assertEqual(replug.timeout(0.3), 1.5)
        self.assertIsNone(replug.feed('add', 'tp', 0.8))
        self.assertIsNone(replug.due(10.0))
        self.assertIsNone(replug.timeout(10.0))

    def test_removal_is_announced_once_the_window_ends(self):
        replug = usb.Replug(window=1.5)
        self.assertIsNone(replug.feed('remove', 'tp', 0.0))
        self.assertIsNone(replug.due(1.4))
        self.assertEqual(replug.due(1.5), 'remove')
        self.assertIsNone(replug.due(2.0))

    def test_late_return_and_other_devices_are_announced(self):
        replug = usb.Replug(window=1.5)
        replug.feed('remove', 'tp', 0.0)
        self.assertEqual(replug.feed('add', 'mouse', 0.5), 'add')
        self.assertEqual(replug.feed('add', 'tp', 2.0), 'add')
        self.assertEqual(replug.due(2.0), 'remove')


if __name__ == '__main__':
    unittest.main()
