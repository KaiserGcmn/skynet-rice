"""Lock HUD machine stats: correct aggregates, no names leak, missing data safe."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / 'sources/xsecurelock-style'

CHECK = r'''
#include "sys-stats.h"
#include <assert.h>
#include <math.h>

static int near(double a, double b) { return fabs(a - b) < 1e-6; }

int main(int argc, char **argv) {
    (void)argc;
    SysStats s;
    stats_init(&s, argv[1]);
    /* Nothing is known before two samples. */
    assert(s.cpu < 0 && s.rx < 0 && !strcmp(s.mode, "--"));
    stats_sample(&s, 0);
    assert(s.cpu < 0 && s.disk < 0 && s.rx < 0);
    assert(near(s.mem, .75));            /* 1 - 1000/4000 */
    assert(near(s.swap, .25));           /* 1 - 300/400 */
    assert(near(s.temp, 47.5));          /* x86_pkg_temp zone only */
    assert(near(s.ghz, 2.0));            /* (1.5 + 2.5) / 2 GHz */
    assert(!strcmp(s.mode, "LOW-POWER"));
    assert(s.cores == 2);
    /* Hardware sensors by driver type: hottest SSD, the DIMM, Wi-Fi, board. */
    assert(s.sensors == 5);
    assert(near(s.therm[STATS_T_CPU], 47.5));
    assert(near(s.therm[STATS_T_SSD], 40.0) && near(s.therm[STATS_T_RAM], 47.75));
    assert(near(s.therm[STATS_T_WIFI], 55.0) && near(s.therm[STATS_T_BOARD], 27.8));
    /* System battery from charge_* files; the mouse battery is skipped. */
    assert(strstr(s.bat_path, "/BAT0") && near(s.bat_pct, .8));
    assert(near(s.bat_watts, 1.5 * 12.0));             /* 1.5 A x 12 V */
    assert(near(s.bat_health, 4000000.0 / 5000000.0) && s.bat_cycles == 38);
    assert(s.bat_state == STATS_BAT_DISCHARGING);
    /* energy_* / power_now battery, "Not charging" = HOLD. */
    SysStats e;
    stats_init(&e, argv[3]);
    stats_sample(&e, 0);
    assert(near(e.bat_watts, 7.25) && near(e.bat_health, 1) && e.bat_cycles == -1);
    assert(e.bat_state == STATS_BAT_HOLD && near(e.bat_pct, 1));
    snprintf(s.root, sizeof(s.root), "%s", argv[2]);  /* second snapshot */
    stats_sample(&s, 1000);
    assert(near(s.cpu, .5));             /* busy +100 of total +200 */
    assert(near(s.core[0], .25) && near(s.core[1], .75) && s.core[2] < 0);
    assert(near(s.disk, .4));            /* nvme0n1: +400 ms of 1000; partition ignored */
    assert(near(s.rx, 3000) && near(s.tx, 1000));  /* lo excluded */
    /* Non-CPU sensors are not re-read within 10 s (NVMe admin commands). */
    assert(near(s.therm[STATS_T_SSD], 40.0) && s.therm[STATS_T_CPU] < 0);
    stats_sample(&s, 10500);  /* now due: the second root has no sensors */
    assert(s.therm[STATS_T_SSD] < 0 && s.therm[STATS_T_WIFI] < 0);
    /* No interface, disk or host name is kept anywhere in the struct. */
    const char *secret[] = {"secretwifi0", "nvme0n1", "lo", "hostname", "nvme", "iwlwifi"};
    for (size_t i = 0; i < sizeof(secret) / sizeof(secret[0]); ++i)
        assert(!memmem(&s, sizeof(s), secret[i], strlen(secret[i])) || i == 2);
    char out[24];
    stats_format_rate(1536, out, sizeof(out)); assert(!strcmp(out, "1.5 KB/S"));
    stats_format_rate(12.4e6, out, sizeof(out)); assert(!strcmp(out, "12 MB/S"));
    stats_format_rate(-1, out, sizeof(out)); assert(!strcmp(out, "--"));
    /* A root with nothing in it stays unknown and never crashes. */
    SysStats empty;
    stats_init(&empty, "/nonexistent-skynet-root");
    stats_sample(&empty, 0); stats_sample(&empty, 1000);
    assert(empty.cpu < 0 && empty.mem < 0 && empty.disk < 0 && empty.rx < 0 &&
           empty.temp < 0 && empty.ghz < 0 && !strcmp(empty.mode, "--") &&
           empty.sensors == 0 && empty.therm[STATS_T_SSD] < 0 &&
           empty.bat_pct < 0 && empty.bat_watts < 0 && empty.bat_state == 0);
    return 0;
}
'''


def write(base, rel, text):
    path = Path(base) / rel.lstrip('/')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def snapshot(base, cpu, cores, disk_ms, part_ms, rx, tx):
    write(base, '/proc/stat', f'cpu  {cpu[0]} 0 0 {cpu[1]} 0 0 0 0 0 0\n' +
          ''.join(f'cpu{i} {b} 0 0 {idle} 0 0 0 0 0 0\n' for i, (b, idle) in enumerate(cores)) +
          'intr 0\n')
    write(base, '/proc/diskstats',
          f'259 0 nvme0n1 1 0 0 0 1 0 0 0 0 {disk_ms} 0\n'
          f'259 1 nvme0n1p1 1 0 0 0 1 0 0 0 0 {part_ms} 0\n'
          '7 0 loop0 1 0 0 0 1 0 0 0 0 999999 0\n')
    write(base, '/proc/net/dev',
          'Inter-|   Receive  |  Transmit\n face |bytes packets|bytes\n'
          f'    lo: 900000 0 0 0 0 0 0 0 900000 0 0 0 0 0 0 0\n'
          f'secretwifi0: {rx} 0 0 0 0 0 0 0 {tx} 0 0 0 0 0 0 0\n')


class SysStatsTest(unittest.TestCase):
    def test_aggregates_without_names(self):
        if not shutil.which('cc'):
            self.skipTest('requires a C compiler')
        with tempfile.TemporaryDirectory(prefix='skynet-stats-test-') as work:
            fake = Path(work) / 'root'
            write(fake, '/proc/meminfo', 'MemTotal: 4000 kB\nMemFree: 10 kB\n'
                  'MemAvailable: 1000 kB\nSwapTotal: 400 kB\nSwapFree: 300 kB\n')
            write(fake, '/sys/class/thermal/thermal_zone0/type', 'acpitz\n')
            write(fake, '/sys/class/thermal/thermal_zone0/temp', '90000\n')
            write(fake, '/sys/class/thermal/thermal_zone3/type', 'x86_pkg_temp\n')
            write(fake, '/sys/class/thermal/thermal_zone3/temp', '47500\n')
            write(fake, '/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', '1500000\n')
            write(fake, '/sys/devices/system/cpu/cpu1/cpufreq/scaling_cur_freq', '2500000\n')
            write(fake, '/sys/firmware/acpi/platform_profile', 'low-power\n')
            sensors = [('acpitz', 27800), ('nvme', 36850), ('spd5118', 47750),
                       ('iwlwifi_1', 55000), ('nvme', 40000), ('coretemp', 99000),
                       ('BAT0', None), ('asus', None)]
            for i, (name, milli) in enumerate(sensors):
                write(fake, f'/sys/class/hwmon/hwmon{i}/name', name + '\n')
                if milli is not None:
                    write(fake, f'/sys/class/hwmon/hwmon{i}/temp1_input', f'{milli}\n')
            mouse = '/sys/class/power_supply/hidpp_battery_0/'
            for name, value in (('type', 'Battery'), ('scope', 'Device'), ('capacity', '5'),
                                ('status', 'Discharging')):
                write(fake, mouse + name, value + '\n')
            bat = '/sys/class/power_supply/BAT0/'
            for name, value in (('type', 'Battery'), ('capacity', '80'), ('status', 'Discharging'),
                                ('current_now', '1500000'), ('voltage_now', '12000000'),
                                ('charge_full', '4000000'), ('charge_full_design', '5000000'),
                                ('cycle_count', '38')):
                write(fake, bat + name, value + '\n')
            write(fake, '/sys/class/power_supply/ADP1/type', 'Mains\n')
            energy = Path(work) / 'energy'
            for name, value in (('type', 'Battery'), ('capacity', '104'),
                                ('status', 'Not charging'), ('power_now', '7250000'),
                                ('energy_full', '61000000'), ('energy_full_design', '60000000')):
                write(energy, '/sys/class/power_supply/BAT1/' + name, value + '\n')
            snapshot(fake, (100, 900), [(50, 450), (50, 450)], 1000, 5000, 10000, 5000)
            later = Path(work) / 'later'
            snapshot(later, (200, 1000), [(75, 525), (125, 475)], 1400, 9000, 13000, 6000)
            source = Path(work) / 'check.c'
            source.write_text(CHECK)
            binary = Path(work) / 'check'
            subprocess.run(['cc', '-D_GNU_SOURCE', '-Wall', '-Wextra', '-Werror',
                            '-I', str(STYLE), str(source), '-o', str(binary), '-lm'],
                           check=True)
            result = subprocess.run([str(binary), str(fake), str(later), str(energy)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
