/* See LICENSE file for copyright and license details. */
#if defined(__linux__)
#include <dirent.h>
#include <limits.h>

#ifndef SKYNET_POWER_SUPPLY_ROOT
#define SKYNET_POWER_SUPPLY_ROOT "/sys/class/power_supply"
#endif

/* Confirm an idle battery is on mains; peripheral batteries are not adapters. */
static int
battery_mains_online(const char *root)
{
    DIR *dir;
    struct dirent *entry;
    FILE *fp;
    char path[PATH_MAX], type[32], extra;
    int online, result = -1, uncertain = 0, n;

    if (!(dir = opendir(root)))
        return -1;
    while ((entry = readdir(dir))) {
        if (entry->d_name[0] == '.')
            continue;
        n = snprintf(path, sizeof(path), "%s/%s/type", root, entry->d_name);
        if (n < 0 || (size_t)n >= sizeof(path) || !(fp = fopen(path, "r")))
            continue;
        n = fscanf(fp, "%31s", type);
        fclose(fp);
        if (n != 1 || strcmp(type, "Mains"))
            continue;
        n = snprintf(path, sizeof(path), "%s/%s/online", root, entry->d_name);
        if (n < 0 || (size_t)n >= sizeof(path) || !(fp = fopen(path, "r"))) {
            uncertain = 1;
            continue;
        }
        n = fscanf(fp, "%d %c", &online, &extra);
        fclose(fp);
        if (n != 1 || (online != 0 && online != 1)) {
            uncertain = 1;
            continue;
        }
        result = online;
        if (online)
            break;
    }
    closedir(dir);
    return result == 1 ? 1 : uncertain ? -1 : result;
}
#endif

/* interval between updates (in ms) */
const unsigned int interval = 1000;

/* text to show if no value can be retrieved */
static const char unknown_str[] = "--";

/* maximum output string length */
#define MAXLEN 2048

/*
 * function            description                     argument (example)
 *
 * battery_perc        battery percentage              battery name (BAT0)
 *                                                     NULL on OpenBSD/FreeBSD
 * battery_remaining   battery remaining HH:MM         battery name (BAT0)
 *                                                     NULL on OpenBSD/FreeBSD
 * battery_state       battery charging state          battery name (BAT0)
 *                                                     NULL on OpenBSD/FreeBSD
 * cat                 read arbitrary file             path
 * cpu_freq            cpu frequency in MHz            NULL
 * cpu_perc            cpu usage in percent            NULL
 * datetime            date and time                   format string (%F %T)
 * disk_free           free disk space in GB           mountpoint path (/)
 * disk_perc           disk usage in percent           mountpoint path (/)
 * disk_total          total disk space in GB          mountpoint path (/)
 * disk_used           used disk space in GB           mountpoint path (/)
 * entropy             available entropy               NULL
 * gid                 GID of current user             NULL
 * hostname            hostname                        NULL
 * ipv4                IPv4 address                    interface name (eth0)
 * ipv6                IPv6 address                    interface name (eth0)
 * kernel_release      `uname -r`                      NULL
 * keyboard_indicators caps/num lock indicators        format string (c?n?)
 *                                                     see keyboard_indicators.c
 * keymap              layout (variant) of current     NULL
 *                     keymap
 * load_avg            load average                    NULL
 * netspeed_rx         receive network speed           interface name (wlan0)
 * netspeed_tx         transfer network speed          interface name (wlan0)
 * num_files           number of files in a directory  path
 *                                                     (/home/foo/Inbox/cur)
 * ram_free            free memory in GB               NULL
 * ram_perc            memory usage in percent         NULL
 * ram_total           total memory size in GB         NULL
 * ram_used            used memory in GB               NULL
 * run_command         custom shell command            command (echo foo)
 * swap_free           free swap in GB                 NULL
 * swap_perc           swap usage in percent           NULL
 * swap_total          total swap size in GB           NULL
 * swap_used           used swap in GB                 NULL
 * temp                temperature in degree celsius   sensor file
 *                                                     (/sys/class/thermal/...)
 *                                                     NULL on OpenBSD
 *                                                     thermal zone on FreeBSD
 *                                                     (tz0, tz1, etc.)
 * uid                 UID of current user             NULL
 * up                  interface is running            interface name (eth0)
 * uptime              system uptime                   NULL
 * username            username of current user        NULL
 * vol_perc            OSS/ALSA volume in percent      mixer file (/dev/mixer)
 *                                                     NULL on OpenBSD/FreeBSD
 * wifi_essid          WiFi ESSID                      interface name (wlan0)
 * wifi_perc           WiFi signal in percent          interface name (wlan0)
 */

/* Original five-cell meter inside a squared industrial frame. */
static const char *
battery_visual(const char *bat)
{
    static const char *levels[] = {
        "▱▱▱▱▱", "▰▱▱▱▱", "▰▰▱▱▱",
        "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"
    };
    const char *value, *state, *direction;
    char *end;
    long percent;

    if (!(value = battery_perc(bat)))
        return "[▱▱▱▱▱]   --% ?";
    percent = strtol(value, &end, 10);
    if (end == value || *end || percent < 0 || percent > 100)
        return "[▱▱▱▱▱]   --% ?";

    state = battery_state(bat);
    direction = !state ? "?" : !strcmp(state, "+") ? "↑" :
                !strcmp(state, "-") ? "↓" : !strcmp(state, "o") ? "•" : "?";
#if defined(__linux__)
    if (state && !strcmp(state, "o")) {
        int online = battery_mains_online(SKYNET_POWER_SUPPLY_ROOT);
        direction = online == 1 ? "•" : online == 0 ? "↓" : "?";
    }
#endif
    return bprintf("[%s]  %3ld%% %s", levels[(percent + 19) / 20], percent, direction);
}

static const struct arg args[] = {
    /* ASCII | separates the four colored panels in REDLINE dwm. */
    /* function        format                argument */
    { cpu_perc,        "CPU %3s%%|",          NULL },
    { battery_visual,  "BAT %s|",             "BAT0" },
    { datetime,        "DATE %s|",            "%d.%m.%Y" },
    { datetime,        "TIME %s",             "%H:%M:%S" },
};
