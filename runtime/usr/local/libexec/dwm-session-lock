#!/usr/bin/python3
"""Forward this dwm session's logind Lock requests to XSecureLock."""

import os
import re
import subprocess
import sys

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib


# This local core was reviewed against this exact Debian package revision.
# After a distribution update use its maintained binary until the patch is
# reviewed and rebuilt. Authentication helpers always come from Debian.
AUDITED_XSECURELOCK_VERSION = '1.9.0-1'


_locker_cache_key = None
_locker_cache_result = '/usr/bin/xsecurelock'


def choose_locker():
    global _locker_cache_key, _locker_cache_result
    local = '/usr/local/bin/xsecurelock-power'
    if not os.access(local, os.X_OK):
        return '/usr/bin/xsecurelock'
    try:
        # dpkg updates status atomically; also watch the actual package binary.
        # Recheck the package revision whenever either file changes.
        cache_key = tuple(
            (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns, info.st_size)
            for info in (os.stat('/var/lib/dpkg/status'),
                         os.stat('/usr/bin/xsecurelock'))
        )
        if cache_key == _locker_cache_key:
            return _locker_cache_result
        result = subprocess.run(
            ['/usr/bin/dpkg-query', '-W',
             '-f=${db:Status-Status} ${Version}', 'xsecurelock'],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return '/usr/bin/xsecurelock'
        audited = result.stdout.strip() == 'installed ' + AUDITED_XSECURELOCK_VERSION
        _locker_cache_result = local if audited else '/usr/bin/xsecurelock'
        _locker_cache_key = cache_key
        if not audited:
            print('Using Debian locker: local build needs package-version review',
                  flush=True)
        return _locker_cache_result
    except (OSError, subprocess.TimeoutExpired):
        return '/usr/bin/xsecurelock'


def lock_command(session_id, unit):
    # Start with a clean environment: inherited debug/auth/key-command options
    # must not change the lock's authentication or execute extra commands.
    home = os.path.expanduser('~')
    runtime = f'/run/user/{os.getuid()}'
    environment = {
        'HOME': home,
        'PATH': '/usr/bin:/bin',
        'LANG': 'en_US.UTF-8',
        'DISPLAY': os.environ['DISPLAY'],
        'XAUTHORITY': os.environ.get('XAUTHORITY', home + '/.Xauthority'),
        'XDG_RUNTIME_DIR': runtime,
        'DBUS_SESSION_BUS_ADDRESS': f'unix:path={runtime}/bus',
        'XDG_SESSION_ID': session_id,
        'XDG_SESSION_TYPE': 'x11',
        'XSECURELOCK_AUTH': '/usr/libexec/xsecurelock/auth_x11',
        'XSECURELOCK_AUTHPROTO': '/usr/libexec/xsecurelock/authproto_pam',
        'XSECURELOCK_PAM_SERVICE': 'common-auth',
        # Visual theme uses the packaged authentication helper's settings.
        'XSECURELOCK_FONT': 'JetBrains Mono:style=Regular:size=13',
        'XSECURELOCK_BACKGROUND_COLOR': '#000000',
        'XSECURELOCK_AUTH_BACKGROUND_COLOR': '#000000',
        'XSECURELOCK_AUTH_FOREGROUND_COLOR': '#d6d6d6',
        'XSECURELOCK_AUTH_WARNING_COLOR': '#f08080',
        'XSECURELOCK_SHOW_HOSTNAME': '0',
        'XSECURELOCK_SHOW_USERNAME': '1',
        'XSECURELOCK_SHOW_DATETIME': '1',
        'XSECURELOCK_DATETIME_FORMAT': '%H:%M  |  %d.%m.%Y',
        'XSECURELOCK_PASSWORD_PROMPT': 'asterisks',
        # Count inactivity even while the password prompt is displayed.
        'XSECURELOCK_BLANK_TIMEOUT': '5',
        'XSECURELOCK_BLANK_WHILE_AUTH': '1',
        'XSECURELOCK_BLANK_DPMS_STATE': 'off',
        'XSECURELOCK_GLOBAL_SAVER': '/usr/libexec/xsecurelock/saver_multiplex',
        'XSECURELOCK_SAVER': '/usr/local/libexec/saver-lock-style',
        'XSECURELOCK_STYLE_IMAGE': home + '/.local/share/xsecurelock-style/background.png',
    }
    return [
        '/usr/bin/systemd-run', '--user', '--quiet', '--collect',
        '--service-type=exec', f'--unit={unit}',
        '--property=LimitCORE=0', '--property=UMask=0077',
        '--', '/usr/bin/env', '-i',
        *(f'{key}={value}' for key, value in environment.items()),
        choose_locker(),
        # Called by XSecureLock only after the screen is covered and grabbed.
        # Show the password prompt immediately, without a wake-up keypress.
        '--', '/bin/sh', '-c', 'kill -USR2 "$PPID"',
    ]


def main():
    session_id = sys.argv[1]
    if not re.fullmatch(r'[A-Za-z0-9_]+', session_id):
        raise RuntimeError('Invalid session ID')
    if not os.environ.get('DISPLAY'):
        raise RuntimeError('DISPLAY is missing')
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    manager = dbus.Interface(
        bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1'),
        'org.freedesktop.login1.Manager',
    )
    try:
        session_path = manager.GetSession(session_id)
    except dbus.DBusException as error:
        if error.get_dbus_name() == 'org.freedesktop.login1.NoSuchSession':
            return
        raise
    properties = dbus.Interface(
        bus.get_object('org.freedesktop.login1', session_path),
        'org.freedesktop.DBus.Properties',
    ).GetAll('org.freedesktop.login1.Session')
    # greetd's default command can register as tty before startx starts X11.
    # The X profile provides the actual desktop type for that same login.
    desktop = str(properties.get('Desktop') or os.environ.get('XDG_CURRENT_DESKTOP', '')).lower()
    if (int(properties['User'][0]) != os.getuid()
            or str(properties['Type']) not in ('x11', 'tty')
            or os.environ.get('XDG_SESSION_TYPE') != 'x11'
            or 'dwm' not in desktop.split(':')):
        raise RuntimeError('Refusing to attach to a different user or desktop')

    choose_locker()  # Warm the revision check before handling power-button events.
    unit = f'dwm-screen-lock-{session_id}.service'
    loop = GLib.MainLoop()

    def lock():
        if subprocess.run(
            ['/usr/bin/systemctl', '--user', 'is-active', '--quiet', unit]
        ).returncode == 0:
            return
        # A separate service keeps the actual locker alive if this listener stops.
        command = lock_command(session_id, unit)
        result = subprocess.run(command)
        print(f'Lock request: launcher exit status {result.returncode}', flush=True)

    def session_removed(removed_id, removed_path):
        if str(removed_id) == session_id:
            loop.quit()

    bus.add_signal_receiver(
        lock, signal_name='Lock', dbus_interface='org.freedesktop.login1.Session',
        bus_name='org.freedesktop.login1', path=str(session_path),
    )
    bus.add_signal_receiver(
        session_removed, signal_name='SessionRemoved',
        dbus_interface='org.freedesktop.login1.Manager',
        bus_name='org.freedesktop.login1', path='/org/freedesktop/login1',
    )
    print(f'Ready: listening for Lock on dwm session {session_id}', flush=True)
    loop.run()


if __name__ == '__main__':
    main()
