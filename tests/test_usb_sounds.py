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

    def event(self, action, path, devtype='usb_device'):
        return {'ACTION': action, 'DEVPATH': path, 'SUBSYSTEM': 'usb',
                'DEVTYPE': devtype}

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

    def test_event_pipeline_coalesces_hubs_and_stops_children_with_session(self):
        state = usb.Devices(self.root)
        first, second = self.device('1-2'), self.device('1-3')
        internal = self.device('1-4', 'fixed')
        def block(action, path):
            return ''.join(f'{k}={v}\n' for k, v in
                           self.event(action, path).items()) + '\n'
        added = block('add', first) * 2 + block('add', second) + block('add', internal)
        removed = block('remove', first) * 2 + block('remove', second)
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
                           'time.sleep(30)', added, removed]
            elif command[0] == '/usr/bin/mpv':
                command = ['/usr/bin/python3', '-c',
                           'import sys,time;from pathlib import Path;'
                           'f=open(sys.argv[1],"a");'
                           'f.write(Path(sys.argv[2]).name+"\\n");f.close();'
                           'time.sleep(30)', str(record), command[-1]]
            child = actual_popen(command, **kwargs)
            children.append(child)
            return child
        with actual_popen(['/bin/sleep', '1']) as session:
            try:
                with mock.patch.object(usb, 'Devices', return_value=state), \
                        mock.patch.object(usb.subprocess, 'Popen', side_effect=popen):
                    usb.monitor(self.root, session.pid)
                self.assertEqual(record.read_text().splitlines(),
                                 list(usb.SOUNDS.values()))
                self.assertTrue(all(p.poll() is not None for p in children))
            finally:
                for child in children:
                    usb.stop(child)


if __name__ == '__main__':
    unittest.main()
