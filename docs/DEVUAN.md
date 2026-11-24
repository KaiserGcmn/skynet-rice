# Devuan + SysVinit/elogind

28 Ekim 2026'da çalışan sistem doğrulandı: PID 1 `init`, `/usr/sbin/init`
dosyasının sahibi `sysvinit-core`, çalışma seviyesi 2. `sysv-rc` ve
`initscripts` kurulu; `systemd`, `systemd-sysv` ve OpenRC kurulu değil.
Init yöneticisi değiştirilmedi.

## Etkin başlangıç düzeni

| Bileşen | Çalışan düzen |
| --- | --- |
| greetd, D-Bus, elogind, NetworkManager, Bluetooth, TLP | `/etc/init.d/` betikleri ve `/etc/rc*.d/` bağlantıları |
| ZRAM ve parlaklık kaydı | SysV `zram-swap` ve `brightness` hizmetleri |
| USB-C UCSI açılış kurtarması | SysV `expertbook-ucsi-recover` → `/usr/local/libexec/expertbook-ucsi-recover --boot` |
| NVMe kapanış denetimi | SysV `nvme-shutdown-audit` → `/usr/local/libexec/nvme-shutdown-audit` (`--record-stop` kapanışta, `--boot` açılışta) |
| DWM, ses sunucusu ve oturum yardımcıları | `/usr/local/bin/dwm-session` |
| Otomatik kilit | Oturumun yönettiği `xss-lock` → `/usr/local/libexec/dwm-lock` |
| Bar, bildirimler, duvar kâğıdı ve tepsi uygulamaları | `/etc/dwm/autostart.sh` |
| Hoparlör/mikrofon durum kaydı | `dwm-session-extras` → `audio-mute-state watch --restore` |
| Kilit/giriş güç işlemleri | Kurulu Devuan uyarlamasında elogind/loginctl |

Elogind'in login1 D-Bus arayüzü ve `loginctl` kullanımı, systemd'nin init
yöneticisi olarak çalıştığı anlamına gelmez. Güncel canlı denetim ve test
sınırları [COMPATIBILITY.md](COMPATIBILITY.md) ve [MAINTENANCE.md](MAINTENANCE.md)
içindedir.

## Kaldırılan eski başlangıç dosyaları

Kullanıcının isteğiyle 28 Ekim 2026'da 22 kullanılmayan dosya kaldırıldı:

- İki OpenRC hizmet taslağı ve boşalan profil dizini.
- Eski Debian profilindeki 15 systemd hizmet, timer, drop-in ve güç ayarı.
- Bu hizmetleri başlatan eski `.xprofile`, `.xsessionrc` ve mute LED udev kuralı.
- `dwm-session-lock` yardımcısının runtime ve kaynak kopyaları.

Eski kilit yardımcısı çalışan sisteme kurulu değildi. Silinen dosyalar kullanıcı
ayarlarını geri yükleme kapsamına girmiyordu; runtime kopyasının kaldırılması,
sonraki derlemelerde de bu eski yardımcının çıktıya taşınmasını önler.
İlgili kayıtlar `captured-files.json` içinden çıkarıldı ve `SHA256SUMS` yenilendi.

Temizlik depo içeriğiyle sınırlıdır. Kurulu paketlerin `/usr/lib/systemd` veya
`/etc/systemd` altındaki uyumluluk dosyaları ve paket yöneticisinin bağlantıları
elle silinmedi. SysVinit bu unit dosyalarını çalıştırmaz. Paketler, elogind,
udev, PAM, çalışan servisler ve kilit/giriş ayarları değiştirilmedi.

## Derleme ve tarihsel kayıtların sınırı

Depodaki temel gtkgreet kaynağı ve XSecureLock yaması hâlâ Debian'a ait
`systemctl` güç çağrılarını içerir. Bunlar kullanılan bileşenlerin kaynaklarıdır;
servis arşivi temizliği sırasında silinmedi veya yeniden derlenmedi.
Bu makinedeki kurulu sürüm, `~/.local/share/skynet-rice/devuan-source.patch`
yerel uyarlamasıyla `loginctl` kullanır. `scripts/build.py` bu yamayı otomatik
uygulamaz; çıktıyı çalışan sistemin üzerine topluca kopyalama. Yerel katman ve
yeniden derleme sınırları [LOGO.md](LOGO.md) ve [RESTORE.md](RESTORE.md) içindedir.

`profiles/debian/` altındaki kalan donanım/masaüstü ayarları,
`reference/debian-maintenance/` betikleri ve APT envanterleri tarihsel kayıtlardır;
güncel SysVinit kurulum listesi değildir. Geçmiş doğrulama notları, o tarihteki
testleri anlatmaya devam eder. Bu temizlik yeni bir init geçişi veya yeniden
başlatma testi değildir.

## Uyku ve hazırda bekletme kapalı

Sistem hiçbir koşulda uyumaz ve hazırda bekletmeye geçmez; işlemler kapak
kapalıyken de çalışmaya devam eder. Ayar iki elogind eki ile yapılır
(depoda `runtime/etc/elogind/`):

- `sleep.conf.d/80-no-sleep.conf`: suspend, hibernate, hybrid-sleep
  ve suspend-then-hibernate yasak. elogind D-Bus `CanSuspend`/`CanHibernate`
  sorgularına `no` döner; masaüstü veya bir program istese de uyku olmaz.
- `logind.conf.d/80-dwm-lock.conf`: güç tuşu, uyku/hazırda bekletme
  tuşları ve kapak (pil, adaptör, dock) yalnız oturumu kilitler; boşta
  kalma eylemi yok.

`/etc/acpi/powerbtn-acpi-support.sh` logind D-Bus servisi varken hiçbir şey
yapmaz. 20 Kasım 2026 denetiminde kayıtlarda (19 Ekim'den beri) hiç
`PM: suspend`/`hibernation` girdisi yoktu.


## Konsol klavyesi ve initramfs uyarıları — 21 Kasım 2026

`apt full-upgrade` sırasında `update-initramfs`, 92 kez `WARNING: Unknown X
keysym "none"` basıyordu. Sebep iki parçalıydı:

- `cryptsetup-initramfs`, `conf-hooks.d/cryptsetup` içinde `KEYMAP=y`
  ayarlıyor. Bu dosya `/etc/initramfs-tools/conf.d` sonrasında okunduğu için
  `initramfs.conf` içindeki `KEYMAP=n` geçersiz kalıyor. Kök disk şifreli değil
  (`/etc/crypttab` boş); paket ileride şifreleme için kurulu tutuldu.
- `setupcon` geçerli bir önbellek bulamayınca Türkçe XKB düzenini her seferinde
  `ckbcomp` ile yeniden çeviriyor. xkb-data 2.42'nin `symbols/tr` dosyasındaki
  `none` sembolünü `ckbcomp` tanımıyor. Uyarılar yalnızca boş tuş seviyeleri
  için.

Bulunan gerçek hata: `/etc/console-setup/cached_setup_keyboard.sh`, kurulumdan
kalma ISO-8859-15 önbelleğini (`cached_ISO-8859-15_del.kmap.gz`, 3 Ocak 2026)
ASCII kipinde yüklüyordu. Bu önbellek ABD düzeniydi (keycode 23 = `i`,
39 = `;`). tty1–6 ve tuigreet yedek girişi Türkçe yerine ABD düzeniyle
çalışıyordu.

Düzeltme, Debian'ın standart yolu olan `setupcon --save-only` oldu. Bu,
`/etc/default/keyboard` (pc105, tr) ve `CHARMAP=UTF-8` ile
`cached_UTF-8_del.kmap.gz` dosyasını ve Unicode kipli (`kbd_mode -u`) kurulum
betiğini üretti. `update-initramfs -u` artık bu önbelleği kullanıyor ve uyarı
basmıyor. Initramfs içinde `etc/console-setup/cached_UTF-8_del.kmap`,
`updates/dkms/vmd.ko.xz`, `nvme.ko.xz` ve `ext4.ko.xz` doğrulandı. Düzen açık
oturumda tty1–6'ya yüklendi (`dumpkeys`: 23 = `idotless`, 26 = `gbreve`,
39 = `scedilla`, 40 = `+i`). X tty7'de ayrı XKB kullandığı için etkilenmedi.

`loadkeys` konsol dışından (`</dev/null`) çalıştırılınca `unknown keysym
'Omega'` uyarısıyla 1 döndürür. `-C /dev/ttyN` ile ya da önyüklemede konsolda
0 döner.

Önceki `/etc/console-setup` ve initrd yedeği:
`~/.local/state/skynet-rice/console-keymap-20261121/`. Artık kullanılmayan
`cached_ISO-8859-15_del.kmap.gz` zararsızdır ve elle silinebilir. Klavye
ayarı değişirse (`dpkg-reconfigure keyboard-configuration`) önbellek kendiliğinden
yenilenir. xkb-data güncellemesinden sonra `sudo setupcon --save-only` yeniden
çalıştırılabilir. `live-boot`/`live-config` ve refractasnapshot ileride ISO yedeği
için kurulu bırakıldı.

## NVMe "Unsafe Shutdowns" denetimi — 21 Kasım 2026

Micron MTFDKBA512QGN-1BN1AABGA (yazılım V8MA000) diskinin `Unsafe Shutdowns`
sayacı 20 Kasım 00:19 ile 21 Kasım arasında 152'den 153'e çıktı. Aynı
dönemde güç döngüsü 398'den 401'e çıktı. Bu arada üç kapanış oldu: 20 Kasım
01:26, 20 Kasım 16:56 (yeniden başlatma) ve 21 Kasım 01:18.

8–21 Kasım arasında 16 Kasım 15:58'deki VMD öncesi NVMe donması dışında her
kapanışın syslog'u düzenli biter (`acpid: exiting`). Hiçbir açılışta ext4
kurtarması yok; `tune2fs` durumu `clean`. Veri kaybı yok.

İncelenenler:

- `rc0`/`rc6` sırası standart: sendsigs → rsyslog → umountfs → umountroot
  → halt/reboot. `K13live-tools` kurulu sistemde hemen çıkar
  (`boot=live` yok).
- DKMS `vmd_shutdown()` upstream ile aynıdır (yalnız IRQ alanını kaldırır).
  NVMe, VMD'den sonra kaydedildiği için `device_shutdown()` içinde önce
  kapatılır.
- Disk RTD3E değerini 512 µs bildiriyor. Çekirdek bunu
  `clamp(rtd3e, nvme_core.shutdown_timeout=5, 60)` ile en az 5 saniyeye
  çıkarır. APST en derin durumu (ps4) 5 ms giriş ve 30 ms çıkış süresiyle
  `default_ps_max_latency_us=100000` sınırının içinde kalır.

Çekirdeğin son NVMe kapanış adımı syslog durduktan sonra çalıştığı için
hangi kapanışın güvensiz olduğu kayıtlardan çıkarılamaz. Kanıt olmadan
`shutdown_timeout` değiştirilmedi.

`nvme-shutdown-audit` bu ayrımı yapar. Diske yalnız
`smartctl -j -A /dev/nvme0` ile okuma yapar.

- **Kapanış (`rc0`/`rc6`):** `RUNLEVEL` 0 ya da 6 iken, `$local_fs` henüz
  bağlıyken kapanış türünü ve sayaçları
  `/var/lib/skynet-rice/nvme-shutdown.json` dosyasına yazar.
- **Açılış:** Ayrık çalışır, açılışı bekletmez. Önceki kaydı ve sayaçları
  karşılaştırıp syslog'a (`nvme-shutdown-audit`) ve
  `/var/log/nvme-shutdown-audit.log` dosyasına (en fazla 200 satır) bir
  sonuç yazar:
  - `clean`: düzenli kapanış, sayaç aynı.
  - `unsafe`: düzenli kapanış, ama sayaç arttı. Son NVMe adımı bitmeden güç
    kesildi; o zaman `nvme_core.shutdown_timeout=10` denenecek.
  - `no-record`: kapanış kaydı yok. Zorla kapatma, çökme ya da elektrik
    kesintisi.
- **Durum:** `/etc/init.d/nvme-shutdown-audit status` geçmişi gösterir.

Kurulum `update-rc.d nvme-shutdown-audit defaults` ile yapıldı
(S04 ve K01). insserv bu sırada `eudev`'i paketin
`Required-Stop: umountroot` başlığına göre K11'e taşıdı; umountroot K12'de
kaldı. 18:08'de başlangıç kaydı alındı (`first-run`, 153).

Testler `tests/test_nvme_shutdown_audit.py` içinde (13 test). Sınıflandırma,
kapanış kaydı, geçmiş sınırı ve init çalışma seviyesi seçimi mutasyonla
doğrulandı.

Kaldırmak için:

```sh
update-rc.d -f nvme-shutdown-audit remove
```

Ardından iki kurulu dosya ile `/var/lib/skynet-rice/nvme-shutdown.json`
silinir.
