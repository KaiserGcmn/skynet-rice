import importlib.machinery
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('spoofdpi_startup', str(ROOT / 'runtime/usr/local/bin/spoofdpi-launch'))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)


class StartupTest(unittest.TestCase):
    def test_gateway_must_be_up(self):
        for route, expected in [('', False),
                                ('default dev tun0 scope link\n', False),
                                ('default via 192.0.2.1 dev wlan0 linkdown\n', False),
                                ('default via 192.0.2.1 dev wlan0\n', True)]:
            with self.subTest(route=route), patch.object(m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, route)):
                self.assertEqual(m.gateway_ready(), expected)

    def test_network_becomes_ready_without_blocking_session(self):
        with patch.object(m.Path, 'exists', return_value=True), \
             patch.object(m, 'gateway_ready', side_effect=[False, False, True]), \
             patch.object(m.time, 'sleep') as sleep:
            self.assertTrue(m.wait_for_gateway('123'))
            self.assertEqual(sleep.call_count, 2)

    def test_wait_is_bounded(self):
        with patch.object(m.Path, 'exists', return_value=True), \
             patch.object(m, 'gateway_ready', return_value=False), \
             patch.object(m.time, 'monotonic', side_effect=[0, 120]), \
             patch.object(m.time, 'sleep') as sleep:
            self.assertFalse(m.wait_for_gateway('123'))
            sleep.assert_not_called()

    def test_logout_cancels_pending_start(self):
        with patch.object(m.Path, 'exists', return_value=False), \
             patch.object(m, 'gateway_ready') as ready:
            self.assertFalse(m.wait_for_gateway('123'))
            ready.assert_not_called()

    def test_rice_proxy_options_are_preserved(self):
        self.assertEqual(m.COMMAND, ['/usr/local/bin/spoofdpi', '--listen-addr', '127.0.0.1:9080', '--dns-mode', 'https', '--dns-https-url', 'https://1.1.1.1/dns-query', '--dns-qtype', 'ipv4', '--dns-cache', '--https-split-mode', 'first-byte', '--no-tui', '--log-level', 'error'])


if __name__ == '__main__':
    unittest.main()
