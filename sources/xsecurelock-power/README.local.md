# Yerel kilit ekranı ve güç ayarları

Debian XSecureLock 1.9.0 kaynağına `Reboot [F11]`, `Shut down [F12]` denetimleri ve isteğe bağlı
klavye/fare hareketsizliğiyle ekran kapatma zamanlayıcısı eklendi.
Sistem paketi `/usr/bin/xsecurelock` değiştirilmedi. Yerel program:
`/usr/local/bin/xsecurelock-power`.

Parola arayüzü ve PAM doğrulaması kurulu Debian paketinin
`/usr/libexec/xsecurelock/auth_x11` ve `authproto_pam` programlarını kullanır.
`--without-pam` derleme seçeneği yalnızca yeni bir PAM yardımcısı derlenmesini
önler; çalışırken parola doğrulaması kaldırılmaz veya değiştirilmez.

Reboot/F11 ve Shut down/F12, ek bir onay istemeden sırasıyla şu normal sistem işlemlerini çalıştırır:

```
/usr/bin/systemctl --no-ask-password --check-inhibitors=yes reboot
/usr/bin/systemctl --no-ask-password --check-inhibitors=yes poweroff
```

Zorla kapatma kullanılmaz. İşlem engellenirse ekran kilitli kalır ve düğme
`Reboot blocked` veya `Shutdown blocked` yazar. Kapatma, açık dosyaları uygulamalarda kaydetmenin
yerine geçmez.

## İlgili dosyalar

- `/usr/local/libexec/dwm-session-lock`: logind kilit isteğini dinler.
- `~/.config/systemd/user/dwm-session-lock@.service`: her dwm oturumuna ait hizmet.
- `~/.xprofile`: oturumda kilit dinleyicisini başlatır ve ekran zaman aşımını kapatır.
- `~/.config/powerdevilrc`: Plasma'nın AC/Battery/LowBattery profilleri.
- `/etc/systemd/sleep.conf.d/80-no-sleep.conf`: tüm uyku/hibernasyon türleri kapalı.
- `/etc/systemd/logind.conf.d/85-no-sleep.conf`: uyku tuşları ve kapak ekranı kilitler.
- `/etc/systemd/logind.conf.d/80-power-button-lock.conf`: kısa güç tuşu ekranı kilitler.

Uyku hedefleri kalıcı olarak maskelenmiştir. Çekirdek, GRUB, initramfs, swap ve
dosya sistemi ayarları bu işlem kapsamında değiştirilmedi.

Dwm kilit ekranında 5 saniye klavye/fare hareketsizliğinden sonra ekran kapanır.
Normal masaüstünde ekran koruyucu ve DPMS kapalıdır.

## Görünüm — 2026-10-14

Greetd/tuigreet görünümüne yakın siyah zemin, ince köşeli gri çerçeve ve
13 punto JetBrains Mono kullanılır. Çerçeve başlığında “Session locked”, altında
Enter yönergesi vardır. Saat/tarih, parola yıldızları, klavye düzeni ve
Kapat/F12 korunur. Görsel ayarlar `dwm-session-lock` içindedir.

Bu tema özel Xvfb ekranında önizlendi; dört deneme karakterinin yıldız olarak
görünmesi, klavye yakalaması ve gerçek kapatma yapmayan test modunda F12/fare
düğmesi kontrol edildi. Ana kilit programı ve görsel yardımcı değişmedi.
Eski görünüm ve ara deneme kopyaları, kullanıcı isteğiyle 2026-10-15 tarihinde temizlendi.

`/usr/local/libexec/saver-lock-style` yalnızca XSecureLock'un verdiği saver
penceresinin içine çizen küçük bir X11/PNG programıdır. Kök pencereye çizmeyi
reddeder. Giriş okumaz, doğrulama veya kilit açma işlemi yapmaz. Ana kilit
programı ve Debian parola/PAM yardımcıları değiştirilmedi.

Dekor bir kez hazırlanmış `~/.local/share/xsecurelock-style/background.png`
dosyasından yüklenir. Her kilitlemede Python/GDK yüklenmez; arka plan X sunucusunda
saklanır; pil bilgisi 10 saniyede bir okunur ve yalnızca değiştiğinde küçük durum
alanı yeniden çizilir. Ekran boyutu değişirse görsel ortalanır ve
kenarlardan kırpılır. Kaynaklar `/usr/local/src/xsecurelock-style/` içindedir.
PNG, mevcut 1920×1200 ekran için hazırlanmıştır. Başka boyutta üretmek için:

```sh
python3 -I /usr/local/src/xsecurelock-style/render-style.py 1920 1200 ~/.local/share/xsecurelock-style/background.png
```

Görsel yardımcının derlenmesi (kurulu X11/libpng geliştirme dosyalarıyla):

```sh
export DEB_BUILD_MAINT_OPTIONS=hardening=+all
cc $(dpkg-buildflags --get CPPFLAGS) $(dpkg-buildflags --get CFLAGS) $(pkg-config --cflags xft xrender xscrnsaver libpng) -Wall -Wextra -Werror /usr/local/src/xsecurelock-style/saver-lock-style.c -o /tmp/saver-lock-style $(dpkg-buildflags --get LDFLAGS) $(pkg-config --libs xft xrender xscrnsaver libpng) -lXext -lm
sudo install -m 0755 /tmp/saver-lock-style /usr/local/libexec/.saver-lock-style.new
sudo mv /usr/local/libexec/.saver-lock-style.new /usr/local/libexec/saver-lock-style
rm /tmp/saver-lock-style
```

Dinleyici paket sürümü sorgusunu oturum başlangıcında hazırlar. dpkg durum
veritabanı veya sistemin xsecurelock dosyası değiştiğinde yeniden doğrular;
eski özel sürümü kullanmama kontrolü korunur. Kilit ekranı kapatılıp giriş
aygıtları yakalandıktan sonra XSecureLock'un bildirim komutu ebeveynine SIGUSR2
gönderir; parola penceresi ek tuş/fare hareketi gerektirmeden açılır. Uyandırma
komutu sabittir ve parola ya da kullanıcı girdisi içermez.

2026-10-14: özel 1920×1200 Xvfb ekranında üç ölçümün ortancası, görselin ilk
çiziminde 167.8 ms → 47.7 ms oldu. Sürüm önbelleği kontrolü yaklaşık 0.05 ms,
parola yardımcısının başlatılması 53 ms ölçüldü. Bunlar özel test ekranındaki
ölçümlerdir; fiziksel güç tuşundan tam ekran açılışına veya gerçek parola
kabulünden masaüstüne dönüşe ait süreler değildir. Yıldızlar, F12, fare düğmesi,
Escape, görsel yardımcının kapanması, klavye/fare kilidi ve paket güncellemesi
sonrası standart kilide geçiş sınandı. Gerçek kapatma yapılmadı. Geçici test
araçları ve önizlemeler kaldırıldı.

İlk kurulum öncesindeki temel kullanıcı ayarlarının küçük geri dönüş yedeği
`~/.local/state/lock-power-options-w982wpze/` altında korunur.

## Derleme ve test

Kaynak: https://deb.debian.org/debian/pool/main/x/xsecurelock/xsecurelock_1.9.0.orig.tar.gz

Yerel kaynak değişiklikleri `local-changes.patch` içinde saklanır; lisans
`LICENSE` dosyasındadır. İndirme, açılmış kaynak, derleme çıktıları, test ekran
görüntüsü ve yalnızca test için açılan Xvfb paketi temizlik sırasında kaldırıldı.

Yeniden derlemek için yukarıdaki 1.9.0 arşivini indirip geçici bir dizinde açın.
Kaynak dizininin içinde şu komutları çalıştırın:

```sh
patch -p1 < "/usr/local/src/xsecurelock-power/local-changes.patch"
export DEB_BUILD_MAINT_OPTIONS=hardening=+all
export CFLAGS="$(dpkg-buildflags --get CFLAGS)"
export CPPFLAGS="$(dpkg-buildflags --get CPPFLAGS) -D_DEFAULT_SOURCE"
export LDFLAGS="$(dpkg-buildflags --get LDFLAGS)"
export GIT_VERSION=1.9.0-local-power
./configure --prefix=/usr/local --libexecdir=/usr/libexec --without-pam --with-default-authproto-module=authproto_pam --with-default-auth-module=auth_x11 --without-pandoc
make -j2 xsecurelock
sudo install -m 0755 xsecurelock /usr/local/bin/xsecurelock-power
```

Kurulan ve sınanan programın SHA-256 değeri:
`62ab5f7bb523cafa7f9d20130f4673e6198b370ad63c3038fd0ce1cc8fb69b4e`.

2026-10-14 tarihinde özel bir Xvfb ekranında F12, fareyle kapatma düğmesi,
düğme dışında bırakılan tıklamanın iptali ve Escape sonrasında klavye kilidinin
korunması doğrulandı. `XSECURELOCK_POWER_TEST=1` ile gerçek kapatma engellendi;
üretim hizmeti bu değişkeni kullanmaz. Geçici test aracı kaldırıldı.

## Güvenlik denetimi — 2026-10-14

- Kaynak arşivi Debian HTTPS deposundan alındı ve `.dsc` içindeki SHA-256 ile
  karşılaştırıldı: `6e8df4d804e388499e7a9116161a0355034d2ebb61471291383875be515e8025`.
- Debian derleme korumaları etkin: PIE, yürütülemez yığın, full RELRO,
  stack protector, stack clash protection, FORTIFY ve `-fcf-protection`.
- Kapatma komutuna X11 bağlantısı ve kimlik doğrulama boruları aktarılmaz;
  standart giriş/çıkış dışındaki tanıtıcılar önce kapatılır (`closefrom(3)`).
- Dinleyici, yerel programı yalnızca denetlenen Debian `xsecurelock 1.9.0-1`
  sürümü hâlâ kuruluysa kullanır. Paket sürümü değişirse veya sürüm okunamazsa
  bir sonraki kilitte dağıtımın `/usr/bin/xsecurelock` programını seçer.
  Bu durumda özel Kapat düğmesi/F12, yama yeniden denetlenip derlenene kadar
  kullanılamaz. `AUDITED_XSECURELOCK_VERSION` ancak bu kontrolden sonra güncellenir.
- Kilit, temiz bir ortamla başlar; Debian'ın mutlak yollu `auth_x11`,
  `authproto_pam` ve `common-auth` PAM ayarı açıkça seçilir. Devralınan test,
  farklı doğrulama modülü veya ek tuş komutu ayarları kullanılmaz.
- Kilit ve parola yardımcıları için `LimitCORE=0`, `UMask=0077` uygulanır.
  Dinleyici ayrıca yalıtılmış Python (`-I`) ve `NoNewPrivileges=yes` kullanır.
  PAM'ın Debian `unix_chkpwd` setgid yardımcısının çalışabilmesi için kilit
  işlemine `NoNewPrivileges` uygulanmaz; dosyaların setuid/setgid yetkileri değişmez.
- Paket bütünlüğü `dpkg --verify xsecurelock` ile doğrulandı. Ana X sunucusunda
  erişim denetimi açık ve TCP dinleme kapalıdır.
- Kimlik doğrulamalı, TCP dinlemeyen özel Xvfb ekranında: F12, fare düğmesi,
  düğme dışında bırakılan tıklama, sentetik F12, Escape, auth_x11 ve
  authproto_pam süreçlerinin zorla sonlandırılması sınandı. Kilit ve klavye/fare
  yakalaması korundu; alttaki pencereye giriş ulaşmadı. Yardımcı süreçler yeniden
  açıldı. Paket sürümü değişikliği ve sorgu hatasında standart kilide geçiş,
  dışarıdan verilen doğrulama/komut ayarlarının temizlenmesi, core limitleri ve
  normal PAM yetkileri de sınandı. Gerçek kapatma yapılmadı.

Bu denetim yalnızca buradaki eklemeleri kapsar; tüm sistem için açık olmadığı
veya fiziksel erişime karşı mutlak koruma garantisi değildir. X11'de aynı kullanıcı
hesabı altında zaten kod çalıştırabilen bir süreç, ekran kilidinin güvenlik sınırı
dışındadır. Kaynak projenin güvenlik tasarımı ve bilinen sınırları:
https://github.com/google/xsecurelock#security-design

Bu değişiklikten önceki kullanıcı ayarları:
`~/.local/state/lock-power-options-w982wpze/`.
Sistem ayarı yedekleri: `/var/backups/no-sleep-*`.

## Pil göstergesi — 2026-10-14

Kilit ekranının sağ üstünde kalan yüzde ve pil/şarj durumu görünür. Donanımın
`/sys/class/power_supply/BAT0` ve `ADP1` salt okunur dosyaları kullanılır;
kablosuz farenin piliyle karıştırılmaz. 10 saniyede bir güncellenir. Pil yoksa
veya yüzde geçersizse gösterge gizlenir. Xft yalnızca yazı çizer; klavye/fare,
parola ve PAM işlemlerine erişmez. Kilit çekirdeği değiştirilmedi.

Kaynaklar: `/usr/local/src/xsecurelock-style/battery-status.h` ve
`saver-lock-style.c`. Güncel bakım kaynakları korunur; ara sürüm kopyaları
temizlenmiştir.

Greetd için `tuigreet-battery.c`, kurulu `/usr/bin/tuigreet` programını aynı
parametrelerle çalıştırır; mevcut `--greeting` metnine başlangıçtaki pil bilgisini
ekler. Bu sürümde greetd göstergesi ekrana her dönüşte yenilenir, açık beklerken
canlı güncellenmez. Derleme:

```sh
export DEB_BUILD_MAINT_OPTIONS=hardening=+all
cc $(dpkg-buildflags --get CPPFLAGS) $(dpkg-buildflags --get CFLAGS) -Wall -Wextra /usr/local/src/xsecurelock-style/tuigreet-battery.c -o /tmp/tuigreet-battery $(dpkg-buildflags --get LDFLAGS)
```

Kurulum hedefi `/usr/local/libexec/tuigreet-battery` (root:root, 0755) ve
`/usr/local/libexec/greetd/tuigreet-capslock` içindeki çağrıdır. Dağıtımın tuigreet/PAM dosyaları
ve oturum seçenekleri değiştirilmez. Greetd yeniden başlatılmaz; değişiklik
bir sonraki normal giriş ekranı açılışında görünür. Sistem kurulumu yönetici
kimlik doğrulamasıyla tamamlandı. Geçici kurulum dizini ve test araçları silindi;
root sarmalayıcısının yedeği `/var/backups/greetd-battery-*` altında kalır.

Doğrulama: yüzde 0/100, şarj oluyor/dolu/pilde, veri hatası ve pil yokluğu;
oturum parametrelerinin korunması; özel Xvfb'de canlı değişim ve göstergeyi
kaldırma, klavye yakalaması. Paketli tuigreet özel terminalde, gerçek greetd
soketine bağlanmadan pil satırını çizdi.

## English interface — 2026-10-15

All visible custom labels now use English: Session locked; Enter your password ·
Press Enter to unlock; Shut down [F12]; Shutting down...; Shutdown blocked;
Battery: 62% (example), Charging, Full, On battery and Plugged in.
The locker uses LANG=en_US.UTF-8. The greetd wrapper scopes LANG, LC_ALL and
LANGUAGE to English for its greeter process. Keyboard layout settings are unchanged.

Only string literals changed in the power-control patch and battery formatter.
The core was rebuilt from the same SHA-256-verified XSecureLock 1.9.0 archive,
with Debian hardening=+all and the same build options. The distribution's
PAM/authentication helpers and session arguments are unchanged.

Private Xvfb verification covered asterisk rendering, keyboard and pointer
capture, F12, clicking Shut down and Escape. Power actions used the dry-run
setting; the real computer was not shut down. The four English battery states,
percentage formatting, greeter argument preservation and packaged tuigreet's
English display were checked in isolated fixtures and a private terminal.
The new core and helpers retain PIE, full RELRO and non-executable stack.

Superseded theme, speed and language snapshots were removed on 2026-10-15.
The original pre-setup user configuration backup remains in
`~/.local/state/lock-power-options-w982wpze/`.
Greetd's original root-owned files are backed up by the system installer under
`/var/backups/greetd-english-*`. Temporary build/preview files are removed after
installation. Updated screens appear on the next normal lock/login.

## Five-second display idle timeout — 2026-10-15

The dwm locker now uses XSECURELOCK_BLANK_TIMEOUT=5,
XSECURELOCK_BLANK_WHILE_AUTH=1 and XSECURELOCK_BLANK_DPMS_STATE=off.
BLANK_WHILE_AUTH is an opt-in local extension: the existing display blank timer
continues while the packaged authentication helper is open. Keyboard/pointer
activity resets the timer and wakes the display. The authentication process,
password timeout, keyboard/pointer grabs and successful-unlock path remain in
place. No authentication or input is handled by the decoration program.

The normal default behavior remains available when the new setting is absent.
If the Debian package version changes and the listener falls back to the stock
binary, the stock program ignores this local setting; blanking then waits until
the authentication prompt closes. Review/rebuild the local core after such an
update to restore the five-second behavior, as with the custom power button.

Blanking requests DPMS off and uses the core's existing DPMS restoration on
wake/unlock; desktop auto-blanking and system suspend/hibernation stay disabled.
A mouse click that only wakes the dark screen cannot activate the shutdown
button. Normal F12 and a subsequent deliberate button click retain the existing
systemctl poweroff action with inhibitor checking and no forced shutdown.

Private Xvfb checks measured 5.05 seconds from start and 5.06 seconds after
keyboard/mouse activity. Wake, activity reset, keyboard grab, wake-only click
and dry-run F12/button action passed. Xvfb verifies X11 blanking; it cannot
measure physical panel power. The poweroff helper itself is unchanged and the
new core retains the Debian hardening settings. Temporary tests/builds are
removed after installation; no new persistent rollback copies were created.

## System installation layout

Custom executables and helpers are root-owned under `/usr/local/bin` and `/usr/local/libexec`; source files are under `/usr/local/src`. Commands that write these system directories require administrator privileges. The user units, private audio state and lock background remain in their normal per-user configuration/data directories. The original Debian authentication helpers and package-version check are unchanged.


## Reboot control — 2026-10-16

Reboot [F11] is drawn beside Shut down [F12] in the same protected child
window. Each button has its own hitbox and status. On narrow displays the
buttons stack vertically. Dragging from one action to the other cancels the
click. Synthetic key/button events cannot request a power action; a click that
only wakes the dark screen cannot activate either button.

Both actions use fixed systemctl verbs, --no-ask-password and
--check-inhibitors=yes. Only one power request may be pending. Failed requests
show the corresponding blocked label and allow a retry while keeping the
session locked. The child closes inherited descriptors before exec.

The same SHA-256-verified Debian 1.9.0 source and hardening build options were
used. PIE, full RELRO and non-executable stack were checked. No authentication
helper, session listener, clean environment or package-version guard changed.

This update was checked on an authenticated private Xvfb display with TCP
disabled: F11/F12, both mouse buttons, inactive gap, drag cancellation,
synthetic F11/F12 rejection, five-second blanking, wake-only click, subsequent
deliberate click, Escape and keyboard/pointer grabs passed. The SKYNET layout
and both buttons were inspected in a screenshot. A separate harness replaced
exec with a stub to verify both command arguments, inhibitor flags, refused
actions, duplicate request suppression, synthetic clicks and narrow layout.
No real reboot or shutdown was performed during testing.

The binary is replaced atomically and the existing patch/documentation are
updated in place. It takes effect at the next lock. Temporary downloads,
build tree, test programs, logs and previews are removed after installation;
no new backup copy is created.


## Animated SKYNET emblem — 2026-10-16

The decorative saver now renders the three SKYNET plates as a solid, extruded
mesh with perspective, shaded side faces, red edges and rotating dot/scanline
texture. One full turn takes eight seconds, at approximately 30 fps. The
SKYNET wordmark, existing background, password UI and power buttons stay fixed.

The native C renderer lives in `/usr/local/src/xsecurelock-style/skynet-logo.h`,
included by `saver-lock-style.c`. It uses existing X11, XRender, Xss, Xext, Xft,
libpng and libm libraries. Two-times supersampling and bilinear reduction smooth
the edges. Only the 480x260 logo area is repainted using reusable pixmaps; no
video player, browser, generated animation file or per-frame file reads are used.
The original background PNG remains intact as the static fallback. The overlay
uses the current centered 1920x1200 artwork; other image sizes keep their static
background. Cropping follows the existing saver behavior on smaller displays.

The saver checks screen-saver/DPMS state every 250 ms and stops animating while
the screen is dark, its window is unmapped or the logo is outside the viewport.
Battery checks now run every second (see the live-refresh update below). The existing five-second idle timeout
is unchanged; animation drawing does not count as user input. The saver never
reads keyboard/pointer events, authenticates, unlocks or runs power commands.
The locker core, PAM helpers, listener and package-version guard are unchanged.

Validation: compiled with Debian hardening=+all and -Wall -Wextra -Werror. PIE,
full RELRO and non-executable stack were checked. A SHA-256-verified Debian
Xvfb ran with a private authentication cookie and TCP disabled. All mesh
vertices stayed within the logo area over a full revolution; successive frames
differed only inside that area. Native-rendered previews were visually checked.
Animation, pause/resume, resize (including cropped/offscreen logo) and clean
window-destruction exit passed. In the short software-rendered test, the saver
used about 1% of one CPU core while animating and 0% at timer resolution while
blank; the private Xvfb process used about 4% while animating. These are test
measurements, not a promise for every display server or machine.

The installed locker with the staged saver passed F11/F12 dry runs, five-second
blanking, wake, Escape and keyboard/pointer grab checks. No actual power action
or user password was used. Installation replaces the decorative executable
atomically; it takes effect on the next normal lock. Temporary test programs,
previews, logs, Xvfb package/extraction and build files are deleted afterward.
No new backup is kept.


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
