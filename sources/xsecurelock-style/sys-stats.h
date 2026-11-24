/* Live, non-sensitive machine activity for the lock HUD.
 *
 * Only aggregate numbers are read: per-core and total CPU load, memory and
 * swap use, busiest-disk activity, total network throughput, package
 * temperature, average clock, the ACPI platform profile and a few hardware
 * temperatures (SSD, RAM, Wi-Fi card, board) found by hwmon driver type,
 * and the laptop battery: charge, power draw, state, health and cycles. No host, user,
 * interface, device, address or process names ever leave this file, and
 * nothing is written. Every source is optional; a missing one reads as
 * "unknown" (negative) and the HUD shows "--".
 *
 * `root` prefixes every path so tests can point at a fake /proc and /sys.
 * SPDX-License-Identifier: MIT
 */
#ifndef SKYNET_SYS_STATS_H
#define SKYNET_SYS_STATS_H
#include <ctype.h>
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STATS_MAX_CORES 64
#define STATS_MAX_SENSORS 12
/* Non-CPU sensors are read rarely: reading an NVMe temperature sends the
 * drive an admin command, and temperatures change slowly anyway. */
#define STATS_SENSOR_PERIOD 10000.0

/* The battery goes through ACPI; every 2 s is plenty for a power gauge. */
#define STATS_BATTERY_PERIOD 2000.0

enum { STATS_BAT_UNKNOWN, STATS_BAT_CHARGING, STATS_BAT_DISCHARGING,
       STATS_BAT_FULL, STATS_BAT_HOLD };

enum { STATS_T_CPU, STATS_T_SSD, STATS_T_RAM, STATS_T_WIFI, STATS_T_BOARD,
       STATS_T_COUNT };

typedef struct {
  unsigned long long busy, total;
} StatsCpuTicks;

typedef struct {
  char root[256];
  char temp_path[320];          /* x86_pkg_temp zone, found once */
  int cores;                    /* logical CPUs seen in /proc/stat */
  /* Raw counters from the previous sample. */
  StatsCpuTicks cpu_prev, core_prev[STATS_MAX_CORES];
  unsigned long long disk_prev, rx_prev, tx_prev;
  double prev_ms;
  int have_prev;
  /* Latest values (targets); negative means unknown. */
  double cpu, core[STATS_MAX_CORES], mem, swap, disk;  /* 0..1 */
  double rx, tx;                /* bytes per second */
  double temp;                  /* degrees Celsius */
  double ghz;
  char mode[24];                /* upper-case platform profile */
  /* Hardware temperatures in degrees Celsius, max per kind; -1 unknown.
   * Only hwmon index paths are kept, never driver or device names. */
  char sensor_path[STATS_MAX_SENSORS][48];
  int sensor_kind[STATS_MAX_SENSORS], sensors;
  double sensor_next_ms;
  double therm[STATS_T_COUNT];
  /* System battery (not a mouse/keyboard one); negative means unknown. */
  char bat_path[48];
  double bat_next_ms;
  double bat_pct, bat_watts, bat_health;  /* 0..1, W, 0..1 */
  int bat_state, bat_cycles;
} SysStats;

static FILE *stats_open(const SysStats *s, const char *path) {
  char full[512];
  snprintf(full, sizeof(full), "%s%s", s->root, path);
  return fopen(full, "re");
}

static int stats_read_line(const SysStats *s, const char *path, char *out,
                           size_t size) {
  FILE *f = stats_open(s, path);
  if (!f) return 0;
  int ok = fgets(out, (int)size, f) != NULL;
  fclose(f);
  if (ok) out[strcspn(out, "\n")] = 0;
  return ok;
}

static void stats_find_temp(SysStats *s) {
  char dir[300];
  snprintf(dir, sizeof(dir), "%s/sys/class/thermal", s->root);
  DIR *d = opendir(dir);
  if (!d) return;
  struct dirent *e;
  while ((e = readdir(d))) {
    if (strncmp(e->d_name, "thermal_zone", 12)) continue;
    char path[300], type[64];
    snprintf(path, sizeof(path), "/sys/class/thermal/%.200s/type", e->d_name);
    if (stats_read_line(s, path, type, sizeof(type)) &&
        !strcmp(type, "x86_pkg_temp")) {
      snprintf(s->temp_path, sizeof(s->temp_path), "/sys/class/thermal/%.200s/temp",
               e->d_name);
      break;
    }
  }
  closedir(d);
}

/* Map a hwmon driver name to a sensor kind; -1 means not shown. */
static int stats_sensor_kind(const char *name) {
  if (!strcmp(name, "nvme")) return STATS_T_SSD;
  if (!strcmp(name, "spd5118") || !strcmp(name, "jc42")) return STATS_T_RAM;
  if (!strncmp(name, "iwlwifi", 7) || !strncmp(name, "ath1", 4) ||
      !strncmp(name, "mt79", 4))
    return STATS_T_WIFI;
  if (!strcmp(name, "acpitz")) return STATS_T_BOARD;
  if (!strcmp(name, "coretemp") || !strcmp(name, "k10temp")) return STATS_T_CPU;
  return -1;
}

static void stats_find_sensors(SysStats *s) {
  char dir[300];
  snprintf(dir, sizeof(dir), "%s/sys/class/hwmon", s->root);
  DIR *d = opendir(dir);
  if (!d) return;
  struct dirent *e;
  while ((e = readdir(d)) && s->sensors < STATS_MAX_SENSORS) {
    if (strncmp(e->d_name, "hwmon", 5) || strlen(e->d_name) > 12) continue;
    char path[48], name[64];
    snprintf(path, sizeof(path), "/sys/class/hwmon/%.12s/name", e->d_name);
    if (!stats_read_line(s, path, name, sizeof(name))) continue;
    int kind = stats_sensor_kind(name);
    if (kind < 0) continue;
    snprintf(path, sizeof(path), "/sys/class/hwmon/%.12s/temp1_input", e->d_name);
    if (kind == STATS_T_CPU) {
      /* Fallback only when there is no x86_pkg_temp thermal zone. */
      if (!*s->temp_path) snprintf(s->temp_path, sizeof(s->temp_path), "%s", path);
      continue;
    }
    snprintf(s->sensor_path[s->sensors], sizeof(s->sensor_path[0]), "%s", path);
    s->sensor_kind[s->sensors++] = kind;
  }
  closedir(d);
}

static void stats_find_battery(SysStats *s) {
  char dir[300];
  snprintf(dir, sizeof(dir), "%s/sys/class/power_supply", s->root);
  DIR *d = opendir(dir);
  if (!d) return;
  struct dirent *e;
  while ((e = readdir(d))) {
    if (e->d_name[0] == '.' || strlen(e->d_name) > 16) continue;
    char path[64], line[32];
    snprintf(path, sizeof(path), "/sys/class/power_supply/%.16s/type", e->d_name);
    if (!stats_read_line(s, path, line, sizeof(line)) || strcmp(line, "Battery")) continue;
    /* Peripheral batteries (wireless mouse, keyboard) report scope Device. */
    snprintf(path, sizeof(path), "/sys/class/power_supply/%.16s/scope", e->d_name);
    if (stats_read_line(s, path, line, sizeof(line)) && !strcmp(line, "Device")) continue;
    snprintf(s->bat_path, sizeof(s->bat_path), "/sys/class/power_supply/%.16s", e->d_name);
    break;
  }
  closedir(d);
}

/* One integer from the battery directory; -1 when missing. */
static double stats_bat_value(const SysStats *s, const char *field) {
  char path[96], line[64];
  snprintf(path, sizeof(path), "%s/%s", s->bat_path, field);
  if (!stats_read_line(s, path, line, sizeof(line))) return -1;
  char *end;
  double v = strtod(line, &end);
  return end != line ? v : -1;
}

static void stats_sample_battery(SysStats *s) {
  s->bat_pct = s->bat_watts = s->bat_health = -1;
  s->bat_state = STATS_BAT_UNKNOWN;
  s->bat_cycles = -1;
  if (!*s->bat_path) return;
  double pct = stats_bat_value(s, "capacity");
  if (pct >= 0) s->bat_pct = pct > 100 ? 1 : pct / 100;
  double power = stats_bat_value(s, "power_now");           /* uW */
  if (power < 0) {
    double amps = stats_bat_value(s, "current_now");        /* uA */
    double volts = stats_bat_value(s, "voltage_now");       /* uV */
    if (amps >= 0 && volts >= 0) power = amps * volts / 1e6;
  }
  if (power >= 0) s->bat_watts = power / 1e6;
  double full = stats_bat_value(s, "energy_full");
  double design = stats_bat_value(s, "energy_full_design");
  if (full < 0 || design <= 0) {
    full = stats_bat_value(s, "charge_full");
    design = stats_bat_value(s, "charge_full_design");
  }
  if (full >= 0 && design > 0) s->bat_health = full > design ? 1 : full / design;
  double cycles = stats_bat_value(s, "cycle_count");
  if (cycles >= 0 && cycles < 1e6) s->bat_cycles = (int)cycles;
  char path[96], line[32];
  snprintf(path, sizeof(path), "%s/status", s->bat_path);
  if (stats_read_line(s, path, line, sizeof(line))) {
    if (!strcmp(line, "Charging")) s->bat_state = STATS_BAT_CHARGING;
    else if (!strcmp(line, "Discharging")) s->bat_state = STATS_BAT_DISCHARGING;
    else if (!strcmp(line, "Full")) s->bat_state = STATS_BAT_FULL;
    else if (!strcmp(line, "Not charging")) s->bat_state = STATS_BAT_HOLD;
  }
}

static double stats_read_celsius(const SysStats *s, const char *path) {
  char line[64];
  if (!stats_read_line(s, path, line, sizeof(line))) return -1;
  double milli = atof(line);
  return milli > 0 && milli < 150000 ? milli / 1000 : -1;
}

static void stats_init(SysStats *s, const char *root) {
  memset(s, 0, sizeof(*s));
  snprintf(s->root, sizeof(s->root), "%s", root ? root : "");
  s->cpu = s->mem = s->swap = s->disk = s->rx = s->tx = s->temp = s->ghz = -1;
  for (int i = 0; i < STATS_MAX_CORES; ++i) s->core[i] = -1;
  snprintf(s->mode, sizeof(s->mode), "--");
  for (int i = 0; i < STATS_T_COUNT; ++i) s->therm[i] = -1;
  stats_find_temp(s);
  stats_find_sensors(s);
  s->bat_pct = s->bat_watts = s->bat_health = -1;
  s->bat_cycles = -1;
  stats_find_battery(s);
}

static double stats_ratio(StatsCpuTicks now, StatsCpuTicks before) {
  if (now.total <= before.total || now.busy < before.busy) return -1;
  double r = (double)(now.busy - before.busy) / (double)(now.total - before.total);
  return r < 0 ? 0 : r > 1 ? 1 : r;
}

/* Whole disks only: nvme0n1, sda, mmcblk0, vda (no partitions, loop, zram, dm). */
static int stats_is_disk(const char *name) {
  size_t n = strlen(name);
  if (!strncmp(name, "nvme", 4))  /* nvme0n1 yes, nvme0n1p2 no */
    return strchr(name + 4, 'n') && !strchr(name + 4, 'p') &&
           isdigit((unsigned char)name[n - 1]);
  if (!strncmp(name, "mmcblk", 6)) return !strchr(name + 6, 'p');
  if ((!strncmp(name, "sd", 2) || !strncmp(name, "vd", 2)) && n >= 3)
    return !isdigit((unsigned char)name[n - 1]);
  return 0;
}

/* Take one sample. `now_ms` is a monotonic clock; rates need two samples. */
static void stats_sample(SysStats *s, double now_ms) {
  char line[512];
  StatsCpuTicks cpu = {0, 0}, core[STATS_MAX_CORES];
  memset(core, 0, sizeof(core));
  int cores = 0, have_cpu = 0;
  FILE *f = stats_open(s, "/proc/stat");
  if (f) {
    while (fgets(line, sizeof(line), f)) {
      if (strncmp(line, "cpu", 3)) break;
      unsigned long long v[8] = {0};
      int id = -1, n;
      if (line[3] == ' ') {
        n = sscanf(line + 3, "%llu %llu %llu %llu %llu %llu %llu %llu", &v[0], &v[1],
                   &v[2], &v[3], &v[4], &v[5], &v[6], &v[7]);
      } else {
        n = sscanf(line + 3, "%d %llu %llu %llu %llu %llu %llu %llu %llu", &id, &v[0],
                   &v[1], &v[2], &v[3], &v[4], &v[5], &v[6], &v[7]) - 1;
      }
      if (n < 4) continue;
      unsigned long long total = 0;
      for (int k = 0; k < 8; ++k) total += v[k];
      StatsCpuTicks ticks = {total - v[3] - v[4], total};  /* minus idle, iowait */
      if (id < 0) {
        cpu = ticks;
        have_cpu = 1;
      } else if (id < STATS_MAX_CORES) {
        core[id] = ticks;
        if (id + 1 > cores) cores = id + 1;
      }
    }
    fclose(f);
  }

  unsigned long long mem_total = 0, mem_avail = 0, swap_total = 0, swap_free = 0;
  int have_avail = 0;
  f = stats_open(s, "/proc/meminfo");
  if (f) {
    while (fgets(line, sizeof(line), f)) {
      unsigned long long kb;
      if (sscanf(line, "MemTotal: %llu", &kb) == 1) mem_total = kb;
      else if (sscanf(line, "MemAvailable: %llu", &kb) == 1) mem_avail = kb, have_avail = 1;
      else if (sscanf(line, "SwapTotal: %llu", &kb) == 1) swap_total = kb;
      else if (sscanf(line, "SwapFree: %llu", &kb) == 1) swap_free = kb;
    }
    fclose(f);
  }

  /* Busiest whole disk: milliseconds spent doing I/O (field 13). */
  unsigned long long disk_ms = 0;
  int have_disk = 0;
  f = stats_open(s, "/proc/diskstats");
  if (f) {
    while (fgets(line, sizeof(line), f)) {
      char name[64];
      unsigned long long v[10];
      if (sscanf(line, "%*u %*u %63s %llu %llu %llu %llu %llu %llu %llu %llu %llu %llu",
                 name, &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], &v[6], &v[7], &v[8],
                 &v[9]) == 11 && stats_is_disk(name)) {
        if (!have_disk || v[9] > disk_ms) disk_ms = v[9];
        have_disk = 1;
      }
    }
    fclose(f);
  }

  /* Total bytes over every interface except loopback. */
  unsigned long long rx = 0, tx = 0;
  int have_net = 0;
  f = stats_open(s, "/proc/net/dev");
  if (f) {
    while (fgets(line, sizeof(line), f)) {
      char *colon = strchr(line, ':');
      if (!colon) continue;
      *colon = 0;
      const char *name = line;
      while (*name == ' ') ++name;
      unsigned long long v[9];
      if (sscanf(colon + 1, "%llu %llu %llu %llu %llu %llu %llu %llu %llu", &v[0], &v[1],
                 &v[2], &v[3], &v[4], &v[5], &v[6], &v[7], &v[8]) != 9)
        continue;
      if (!strcmp(name, "lo")) continue;
      rx += v[0];
      tx += v[8];
      have_net = 1;
    }
    fclose(f);
  }

  double dt = now_ms - s->prev_ms;
  if (s->have_prev && dt > 50) {
    s->cpu = have_cpu ? stats_ratio(cpu, s->cpu_prev) : -1;
    for (int i = 0; i < STATS_MAX_CORES; ++i)
      s->core[i] = i < cores ? stats_ratio(core[i], s->core_prev[i]) : -1;
    s->disk = have_disk && disk_ms >= s->disk_prev
                  ? (double)(disk_ms - s->disk_prev) / dt : -1;
    if (s->disk > 1) s->disk = 1;
    s->rx = have_net && rx >= s->rx_prev ? (rx - s->rx_prev) * 1000.0 / dt : -1;
    s->tx = have_net && tx >= s->tx_prev ? (tx - s->tx_prev) * 1000.0 / dt : -1;
  }
  s->cores = cores;
  s->cpu_prev = cpu;
  memcpy(s->core_prev, core, sizeof(core));
  s->disk_prev = disk_ms;
  s->rx_prev = rx;
  s->tx_prev = tx;
  s->prev_ms = now_ms;
  s->have_prev = 1;

  s->mem = mem_total && have_avail && mem_avail <= mem_total
               ? 1 - (double)mem_avail / mem_total : -1;
  s->swap = swap_total && swap_free <= swap_total
                ? 1 - (double)swap_free / swap_total : swap_total ? -1 : 0;

  s->temp = *s->temp_path ? stats_read_celsius(s, s->temp_path) : -1;
  s->therm[STATS_T_CPU] = s->temp;
  if (now_ms >= s->sensor_next_ms) {
    for (int k = STATS_T_SSD; k < STATS_T_COUNT; ++k) s->therm[k] = -1;
    for (int i = 0; i < s->sensors; ++i) {
      double c = stats_read_celsius(s, s->sensor_path[i]);
      int k = s->sensor_kind[i];
      if (c > s->therm[k]) s->therm[k] = c;
    }
    s->sensor_next_ms = now_ms + STATS_SENSOR_PERIOD;
  }
  if (now_ms >= s->bat_next_ms) {
    stats_sample_battery(s);
    s->bat_next_ms = now_ms + STATS_BATTERY_PERIOD;
  }

  double khz = 0;
  int clocks = 0;
  for (int i = 0; i < cores; ++i) {
    char path[96];
    snprintf(path, sizeof(path), "/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq", i);
    if (stats_read_line(s, path, line, sizeof(line)) && atof(line) > 0) {
      khz += atof(line);
      ++clocks;
    }
  }
  s->ghz = clocks ? khz / clocks / 1e6 : -1;

  snprintf(s->mode, sizeof(s->mode), "--");
  if (stats_read_line(s, "/sys/firmware/acpi/platform_profile", line, sizeof(line))) {
    size_t k = 0;
    for (; line[k] && k + 1 < sizeof(s->mode); ++k) {
      unsigned char c = (unsigned char)line[k];
      s->mode[k] = isalnum(c) || c == '-' ? (char)toupper(c) : '-';
    }
    s->mode[k] = 0;
    if (!k) snprintf(s->mode, sizeof(s->mode), "--");
  }
}

/* "1.2 MB/S" style throughput, fixed small width. */
static void stats_format_rate(double bytes, char *out, size_t size) {
  if (bytes < 0) { snprintf(out, size, "--"); return; }
  const char *unit = "B/S";
  if (bytes >= 1e9) { bytes /= 1e9; unit = "GB/S"; }
  else if (bytes >= 1e6) { bytes /= 1e6; unit = "MB/S"; }
  else if (bytes >= 1e3) { bytes /= 1e3; unit = "KB/S"; }
  if (bytes >= 999.5) bytes = 999;
  snprintf(out, size, bytes < 10 && strcmp(unit, "B/S") ? "%.1f %s" : "%.0f %s",
           bytes, unit);
}
#endif
