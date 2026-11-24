# Yayın öncesi kontrol — 18 Ekim 2026

Debian 13, x86_64, Python 3.13 üzerinde:

- DWM, dmenu/stest, slstatus, xwinwrap, gtkgreet-hud, saver-lock-style,
  tuigreet-battery ve yamalı XSecureLock kaynakları başarıyla derlendi.
- XSecureLock 1.9.0 kaynak arşivinin SHA-256 değeri doğrulandı; yerel yama
  `--fuzz=0` ile uygulandı. Upstream `system()` dönüş değerleri için üç
  `warn_unused_result` uyarısı var; derleme hatası yok.
- Geri yükleme aracı: dört test geçti (yazmayan önizleme, yedek/izinleri koruma,
  tekrar çalıştırma, symlink ve dosya/dizin çakışmasında yazmadan durma).
- Ses durumunu saklama aracının mevcut 12 testi geçti.
- 29 Python ve 20 kabuk/OpenRC dosyasının sözdizimi kontrol edildi.
- Yayına girecek içerikte bilinen anahtar/token örüntüleri, özel anahtar
  dosyaları, ELF ikilileri, `.ko` modülleri ve `.deb` arşivleri bulunmadı.
  `SHA256SUMS` depo içeriğinin tamamı için üretildi.

Eksik GTK/JSON derleme bağımlılıkları sistem paket veritabanına kurulmadan
geçici dizinde açıldı. Derlenen programlar çalışan sisteme kurulmadı.
Bu yayında giriş ekranı/ekran kilidi fiilen çalıştırılmadı; parola, kapatma,
yeniden başlatma veya çekirdek modülü yükleme testi yapılmadı.

OpenRC dosyaları taslak durumunda; gerçek Devuan/OpenRC oturum, servis,
kilit ve güç davranışı henüz doğrulanmadı. DKMS/VMD kaynakları bu yayın
hazırlığında tekrar derlenmedi; önceki sistemin kaynak kaydı olarak alındı.

> **Güncel durum:** OpenRC kullanılmıyor. Sistem Devuan 6 + SysVinit/elogind
> ile çalışır; OpenRC taslakları 28 Ekim 2026'da depodan kaldırıldı. Yukarıdaki
> OpenRC notları yalnız o tarihteki yayın öncesi kontrolü anlatır. Güncel
> başlangıç düzeni için [DEVUAN.md](DEVUAN.md).


## Native login/lock logo — 23 October 2026

Both logo renderers now use flat red stripes and a 3.8-second text scan based on
the supplied Skynet4.gif. This is native drawing, with no runtime media asset.
The greeter's installed Devuan/fingerprint UI patch was retained while rebuilding.
Private X11 and nested Cage/Wayland checks covered masked input, biometric
countdown, failed authentication and successful session handoff through mock IPC.
The lock decoration animated without taking keyboard grabs. Actual PAM, locker
core, authentication UI and launch configuration hashes stayed unchanged.
Build/test installers and screenshots were temporary and removed after validation.


## Biometric countdown styling — 23 October 2026

A common native Cairo panel replaced the plain GTK progress bar and X11 ASCII
meter in the existing machine-local fingerprint overlay. Both builds succeeded.
Private X11 and Cage/Wayland mock authentication checks covered countdown,
masked password fallback, rejection and backend-controlled success; existing
lock decoration placement was inspected. No real authentication/session test
was performed. Core/PAM/launcher hashes and greeter protocol/action sources were
unchanged. Both source patch layers applied cleanly with `--fuzz=0`. Details and
rebuild instructions are in `BIOMETRIC.md`.


## Wallpaper and system optimization — 24 October 2026

Devuan 6/SysVinit, X11/DWM: the wallpaper wrapper now pauses mpv when its
window is fully obscured and resumes on partial/full visibility. It uses the
existing wrapper process, retains hardware decoding, and adds no package or
resident daemon. The updated source compiled with `-Wall -Wextra -Werror`,
FORTIFY, stack protection and RELRO/NOW. Installed binaries remain root-owned
with mode 0755; the installed Python helper matches the repository copy.

Five integration tests passed against the installed wrapper on an unmapped
800×600 Xephyr fixture: visibility transitions and playback progress, delayed
IPC startup and hidden file replacement/quit, missing-socket child exit,
termination forwarding, and legacy invocation. The four restore tests also
passed; ordinary discovery safely skipped the five opt-in display tests.

The current desktop session automatically started the updated helper after
reboot. While fully covered, mpv and xwinwrap together consumed 0.00% of one CPU
core during an 8-second sample; playback position stayed fixed and VA-API stayed
active. The pre-change mpv sample was 7.0% over four seconds. These short samples
were taken in different sessions and are not a battery-runtime or general
system-performance benchmark. No greeter, desktop or user application restart
was needed during final verification.

Existing settings were reviewed and retained: 4 GiB LZ4 ZRAM at priority 100,
256 MiB fallback swap, root `noatime`, weekly low-priority SSD TRIM, battery
power/quiet profile and 80% charging limit. Package audit returned no issues.
No network tuning, brightness change, service removal or USB-C work was done.
The existing GRUB override already waits one second. Current process start
timestamps were 6.68 seconds for the greetd daemon and 13.79 seconds for DWM
after kernel boot; these are not measurements of interactive readiness or
evidence of a boot-speed improvement. Build/test artifacts and the private
display were removed after verification.


## Greeter credential cleanup and idle lock — 24 October 2026

The inherited gtkgreet request-object leak was replaced with bounded request
encoding and explicit buffer erasure. Caller-owned request memory is cleared
before transport, and the wire buffer is cleared before reading the response,
including transport failures. The asynchronous Devuan source layer was updated
for the consuming pointer API and clears the submitted GTK entry immediately.
No request/password JSON object is retained. Malformed/closed/oversized replies
remain failures; only an explicit daemon success reaches session handoff.

Both the captured repository frontend and the installed Devuan variant built
with Debian hardening and `-Werror`; the refreshed machine source layer applied
with `--fuzz=0`. Five protocol regression tests passed, including instrumented
checks of erasure before response reads. Four restore tests passed. Normal
discovery skipped the five unrelated opt-in wallpaper display tests.

Hidden GTK/X11 and Cage/Wayland mock-server runs covered rejection,
cancellation/retry, fingerprint information and password fallback, followed by
handoff only after mock success. No real credentials, PAM, fingerprint enrollment
or power actions were used. A separate fake login1 service on a private D-Bus
and hidden X server verified xss-lock invoking a fake locker after 1.061 seconds
with a one-second test timeout.

The live session's existing xss-lock now has a 300-second idle timeout, verified
with `xset q`; the same setting is saved in `/usr/local/bin/dwm-session`.
Activation checked for an existing lock first, then reset the idle counter.
Brightness and desktop DPMS settings were unchanged. Only the GTK greeter binary
and session launcher were installed, root-owned 0755; the greeter is used on its
next normal invocation. PAM, locker core, authentication helpers, greeter launcher
and login configuration hashes were unchanged. No service/session restart or
forced live lock was performed. See `SECURITY.md` for scope and limitations.


## Keyring startup — 24 October 2026

The DWM session now completes GNOME Keyring initialization before launching
desktop applications. The command reuses a PAM-started daemon, only enables
the secrets component, and has a bounded startup time. Both keyring packages
were already installed and are now included in the desktop package inventory.

An isolated D-Bus session with disposable XDG data/runtime directories and an
artificial login password verified that initialization retained the original
daemon PID and exposed an unlocked test login collection. Repeating the command
was harmless; the two calls together took 0.060 seconds. The daemon and temporary
directories were removed. No real keyring item, password or authentication
session was used. This is not evidence that fingerprint-only login can decrypt
the user's keyring: it still requires the keyring password. Real password-login
and Spotify startup behavior remain to be checked at the next voluntary login.


## Spotify keyring experiment and rollback — 24 October 2026

Spotify 1:1.2.95.453.g0eeebbed was launched twice on a private Xephyr display
inside an unmapped parent window. Each run had separate temporary XDG directories,
an explicit temporary cache path and a private D-Bus daemon with no service
activation directories. A fake Secret Service recorded method names only and
contained no credentials. The default launch contacted `ReadAlias`; the launch
with `--password-store=basic` made no Secret Service calls. Both stayed running
and displayed a window during the 16-second checks. This verifies the startup
behavior in empty profiles, not account migration or authenticated playback.

The option was installed in a user shell wrapper and desktop entry. Their shell
syntax, desktop-entry syntax, version invocation and application discovery passed.
The user subsequently requested rollback because of the local-storage security
tradeoff. Both added launchers were removed from the installed home and repository,
and the desktop database was refreshed. Normal package launch behavior is restored;
future configuration restoration will not reintroduce the override. No package,
authentication rule, user keyring or account data was removed. Test processes and
temporary data were cleaned up. See `SECURITY.md` for the current state.


## Spotify package reinstallation — 24 October 2026

After the user removed Spotify, its existing official HTTPS repository was
updated with APT signature verification and `spotify-client`
`1:1.2.95.453.g0eeebbed` was reinstalled. No additional package was installed or
removed. `dpkg --verify spotify-client` reported no file mismatch.

The package's post-install menu command reported a missing writable system menu
directory. Creating the missing standard `/usr/share/desktop-directories`
directory (root-owned 0755) and rerunning `xdg-desktop-menu install --mode system
--novendor` registered the unmodified packaged desktop entry in
`/usr/share/applications/spotify.desktop`. Desktop validation and Spotify URI
handler discovery passed. The normal launch remains `spotify %U`, with no
password-store override. The 171,638,972-byte cached installer was removed.

The existing profile was retained. Its directory and existing subdirectories
were restricted to mode 0700, existing profile files to 0600. No credential
values were printed. The user unlocked GNOME Keyring and signed into Spotify;
the application was then exited through its MPRIS Quit method and relaunched
without additional flags. The user confirmed that the account stayed signed in.
This verifies an application restart in the current unlocked-keyring session;
the subsequent full computer reboot failed to retain the signed-in account,
as described below.


## Spotify reboot logout and Devuan machine identity — 24–25 October 2026

After reboot, the user unlocked the login keyring but Spotify still displayed
its account login screen. Relaunching Spotify with the keyring already unlocked
did not restore the account. Existing profile credential fields were nonempty;
only their presence and file metadata were inspected. The persistent login
collection contained an existing Chromium item; no secret values were retrieved.

Devuan's `/etc/default/dbus` set `IDTYPE="RANDOM"`, which instructs the installed
SysV init script to regenerate `/var/lib/dbus/machine-id` at boot. The current
file was created about seven seconds after boot. Spotify's binary references
that path, making changing machine identity a candidate cause of device-bound
login failure; this does not establish that it caused the observed logout.

With the user's approval, the configuration was atomically changed to
`IDTYPE="FIXED"`, retaining the current machine ID and root-owned 0644 permissions.
No `/etc/machine-id` was created and D-Bus and the desktop were not restarted.
An isolated check of the installed init script's `create_machineid()` function
used a temporary ID and simulated early boot: RANDOM changed the temporary ID
across two invocations, while FIXED retained it. The real ID was not used in
that test. On 25 October, the installed setting and shell syntax passed; the
real ID's modification time remained unchanged from before the edit.

The packaged Spotify desktop entry remains unmodified, with no user launcher
override. PAM, the fingerprint stack, locker and session launcher hashes were
unchanged. Diagnostic and installation temporary files were removed. The user
must sign into Spotify once under the retained identity, then check persistence
after a voluntary reboot. That end-to-end check is still pending; the change
is not yet a confirmed Spotify fix. See `SECURITY.md` for the privacy tradeoff
and `RESTORE.md` for the setting and rollback.


## USB connection sounds — 25 October 2026

The user-session helper `usb-sounds` listens to completed USB device
events using the existing udevadm and plays the two user-provided MP3 files
using the existing mpv. The session launcher starts it asynchronously. The
helper tracks external devices, ignores interfaces/internal devices/startup
enumeration, coalesces same-direction bursts and prevents duplicate instances.
It stops its monitor and audio children when the desktop session exits.

After native administrator authentication, the helper and session launcher
were installed root-owned 0755 and verified byte-for-byte against the repository.
The temporary launch from the repository was stopped along with its udevadm
child, then the installed helper was activated in the existing desktop session.
Exactly one helper and one USB monitor were present; the session launcher's
shell syntax and the private 0600 runtime lock passed checks. No desktop or
device restart was required. The next real login has not yet been exercised.

Eight regression tests passed, including a synthetic event pipeline that
verified connection/disconnection file selection, hub coalescing and child
cleanup. A temporary live monitor ran unprivileged without touching devices:
startup was silent, a second instance exited, and terminating the disposable
session process stopped the monitor and reaped its child. Over a two-second
idle sample, the helper plus udevadm consumed zero additional CPU ticks.

Both actual MP3 files played successfully through the live audio server.
Speaker and microphone volume/mute queries were identical before and after.
No package, udev rule, device authorization or automount policy was changed.
Temporary test directories were removed; the original audio files remain in
`~/customsounds`. Physical USB insertion/removal remains a user check; no
network adapter or other real device was forcibly disconnected. See
`USB-SOUNDS.md` for restoration and operational details.


## Volume-key audio feedback — 25 October 2026

The installed Devuan pactl-based `dwm-volume` implementation was preserved in
the repository, replacing the older wpctl snapshot. Speaker level up/down now
optionally plays the user's `Soundleveltest.mp3` after the usual control and
Dunst notification. Mute, microphone mute, show, zero volume and muted output
remain silent. No new daemon is required. Playback uses a separate nonblocking
lock and closes the volume-control lock before starting mpv, avoiding queued
sounds or blocked volume keys.

Three shell-level regression tests with fake audio/notification commands
passed: correct file selection for both directions, silent cases and missing
file, and nonblocking behavior when feedback is busy. The checks also verified
that the player does not inherit the volume-control lock. The actual MP3 played
through the live audio server with unchanged speaker/microphone volume and
mute values before and after. The original MP3 was neither altered nor copied;
temporary test directories were removed. See `AUDIO-FEEDBACK.md`.

The helper was atomically installed root-owned 0755, with its original installed
control code unchanged and the feedback block appended. It matches the saved
repository version. A live `show` invocation displayed the existing Dunst
notification without changing speaker/microphone state. Shell syntax, four
restore tests and the 374-file publication/checksum check passed. No session
restart, additional package or installation residue was required.


## Dunst notification sound — 25 October 2026

A user-owned Dunst script hook now plays `Notificationrecieved.mp3` for displayed
notifications. Volume/brightness applications and volume/microphone/brightness
stack tags are excluded; the volume key's existing sample remains independent.
The hook respects paused notifications and coalesces overlapping playback with
a nonblocking runtime lock. Notification content is not interpreted or logged.

The installed Dunst 1.12.2 was tested on an unmapped Xephyr display with a private
D-Bus and fake player. Ordinary notifications invoked playback; OSD exclusions,
suppressed and paused notifications, a three-notification burst, history recall
and a missing audio file behaved as intended. Dunst's warning log was empty.
The private test's initial rule inspection encountered the absent optional
busctl command; direct D-Bus RuleList completed the check without adding packages.
Private display/bus processes and temporary files were removed.

The helper was installed under `~/.config/dunst` with mode 0755 and the existing
config mode was preserved. The current red SKYNET config and its five existing
SVG assets replace the older repository snapshot, preserving the live appearance
on future restores. Reload retained the same Dunst PID and pause state. A single
live test notification produced a `Notifications` PulseAudio stream.
Speaker/microphone volume and mute were unchanged. Only the test notification
was closed and removed from history; no session restart was performed.


## Conservative maintenance and LED idle queries — 25 October 2026

The installed LED observer now uses audio events for immediate synchronization
and a 30-second healthy fallback instead of querying both devices every two
seconds. Failed synchronization still retries after two seconds. Four regression
tests passed, covering independent LEDs, query failure, bounded idle queries,
immediate relevant events, unrelated client events and subscriber cleanup.
The audio persistence helper's 18 tests also passed.

The existing logrotate policy now includes `.xsession-errors` alongside the
session log, retaining its 1 MiB threshold and two historical files. The staged
and complete installed configurations passed logrotate debug validation. With
APT/dpkg locks held, 177 installed/superseded package archives totaling
364,641,346 bytes were removed. No package was removed or upgraded. The LED
helper and logrotate file were atomically installed root-owned 0755/0644.

The audit found no current memory pressure or package dependency problem; NVMe
SMART passed with zero media errors and zero error-log entries. Existing ZRAM,
TRIM, power and boot policies were retained. Protected PAM, locker, session,
TLP, GRUB, fstab and USB-C observer hashes were unchanged. See `MAINTENANCE.md`
for measurements, kernel-warning context and limits; no boot or battery-life
improvement is claimed from this audit.


## Unused init archives removed — 28 October 2026

Removed 22 unchanged, Git-tracked files: two OpenRC service drafts, 15 archived
systemd units/drop-ins/power settings, the old Debian `.xprofile` and
`.xsessionrc`, the systemd-only mute LED udev rule, and both copies of the old
`dwm-session-lock` helper. Empty profile directories and 20 corresponding
capture-manifest entries were removed. Current SysVinit startup and build
limitations are documented in `DEVUAN.md` and the restore instructions.

All four restore tests passed. Removed paths are absent from the capture
manifest and active build/test/runtime references; future build staging no
longer copies the obsolete lock helper. SHA-256 comparisons confirmed that
13 protected live files were unchanged, including SysV services, greetd/PAM,
DWM/autostart, session/lock launchers, slstatus and the local Devuan source patch.
Package-provided systemd compatibility files and historical package inventories
were retained. No package, active service, root configuration or running session
was changed. No new build output, persistent backup or temporary file was created.
