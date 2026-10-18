# SKYNET graphical greetd interface

Based on Debian gtkgreet 0.8-1 (binary package 0.8-1+b1), upstream GPL-3.0.
Source: https://deb.debian.org/debian/pool/main/g/gtkgreet/gtkgreet_0.8.orig.tar.gz
SHA256: e5c70219da191a60e2e009412603e05c36cee15bbbf7657dbbeaa1d21a692873

Cage runs this GTK3 front end as _greetd. Greetd and its PAM configuration
still perform authentication. proto.c and its protocol structures are unchanged.
UI changes: Cairo-rendered lock-screen mesh (8-second turn, about 30 fps),
static dot-art SKYNET wordmark, date/time/battery, masked password input,
readable red theme and safe systemctl reboot/poweroff buttons (F11/F12).
The drawing widget's frame callback stops while unmapped.
Sessions are read from /usr/share/xsessions and run through the existing
/usr/local/libexec/greetd/start-x wrapper. DWM is the default; Plasma remains
selectable. UID 1000's login name is prefilled and can be edited.
The selected session is displayed by name instead of a raw shell command.

/etc/greetd/config.toml invokes /usr/local/libexec/greetd/skynet-greeter.
That launcher reads the system keyboard layout, creates a private runtime
directory and removes it when the greeter exits. If Cage fails, or the
installed gtkgreet version changes, it falls back to the existing themed
tuigreet command. The version check prevents silently retaining an old
locally built front end after a distribution update. Rebase/rebuild this
source against an updated gtkgreet before adjusting that guard.

The login daemon is not restarted during installation. Reboot normally to
activate the changed config. No lock-screen or terminal settings are changed.

Build with `make` after installing the development packages listed in Makefile.
Build packages and test files were temporary and are not runtime requirements.
Verification: private Xvfb + Cage, fake greetd IPC for failed authentication,
cancellation, retry, masked input and DWM/Plasma session commands. These tests
do not replace a real login at the next boot. Power actions are not exercised
against the real machine during tests.


## Live AC/battery refresh — 2026-10-16

Battery labels refresh every 1000 ms in both GTK greetd and the lock decoration.
The internal BAT0 percentage is read afresh. ADP1/online takes precedence over
BAT0/status so unplugging cannot leave a stale Charging or Full label. While AC
is connected, a non-charging battery is labeled Plugged in; status is used as a
fallback only if AC information is unavailable. Invalid/absent battery data
clears the label instead of retaining the previous state. The lock decoration
also refreshes immediately on remap or when screen blanking ends.

Only the decoration's data reader and refresh timers changed. GTK authentication,
PAM, the locker core, keyboard grabs, animation and power actions are unchanged.
Tests: eleven sysfs fixture cases; live GTK-label and X11-pixel checks for unplug,
replug, percentage changes and stale status; remap refresh. Measured updates
were within one second in the private Xvfb test. No real credentials or power
actions were used. New binaries take effect the next time each screen opens.
