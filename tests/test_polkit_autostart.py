"""Exercise agent selection in the shipped autostart without a live session."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUTOSTART = ROOT / 'profiles/debian/rootfs/etc/dwm/autostart.sh'


class PolkitAutostartTest(unittest.TestCase):
    def run_startup(self, local=True, distro=True, running=False):
        with tempfile.TemporaryDirectory(prefix='skynet-polkit-startup-') as name:
            work = Path(name)
            for directory, present in (('local', local), ('distro', distro)):
                target = work / directory
                target.mkdir()
                if present:
                    agent = target / 'polkit-mate-authentication-agent-1'
                    agent.write_text('#!/bin/sh\nprintf "%s\\n" ' + directory + ' >> "$START_LOG"\n')
                    agent.chmod(0o755)
            pgrep = work / 'pgrep'
            pgrep.write_text('#!/bin/sh\nexit ' + ('0' if running else '1') + '\n')
            pgrep.chmod(0o755)
            block = AUTOSTART.read_text().split(
                '# Provide the standard desktop dialog for administrative authentication.', 1)[1]
            block = block.replace('/usr/local/libexec', str(work / 'local'))
            block = block.replace('/usr/libexec', str(work / 'distro'))
            log = work / 'started'
            result = subprocess.run(
                ['/bin/sh', '-c', 'task_uid=$(id -u)\n' + block + '\nwait\n'],
                env=dict(os.environ, PATH=str(work) + ':' + os.environ['PATH'],
                         START_LOG=str(log)), capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            return log.read_text().splitlines() if log.exists() else [], result.stderr

    def test_prefers_local_agent(self):
        self.assertEqual(self.run_startup(), (['local'], ''))

    def test_falls_back_to_distribution_agent(self):
        self.assertEqual(self.run_startup(local=False), (['distro'], ''))

    def test_existing_agent_is_not_started_again(self):
        self.assertEqual(self.run_startup(running=True), ([], ''))

    def test_missing_agents_are_reported(self):
        started, error = self.run_startup(local=False, distro=False)
        self.assertEqual(started, [])
        self.assertIn('no executable MATE Polkit agent found', error)
