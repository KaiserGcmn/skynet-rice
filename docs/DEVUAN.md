# Devuan + SysVinit/elogind

28 Ekim 2026'da çalışan sistem doğrulandı: PID 1 `init`, `/usr/sbin/init`
dosyasının sahibi `sysvinit-core`, çalışma seviyesi 2. `sysv-rc` ve
`initscripts` kurulu; `systemd`, `systemd-sysv` ve OpenRC kurulu değil.
Init yöneticisi değiştirilmedi.

## Etkin başlangıç düzeni

| Bileşen | Çalışan düzen |
| --- | --- |
| greetd, D-Bus, elogind, NetworkManager, Bluetooth, TLP | `/etc/init.d/` betikleri ve `/etc/rc*.d/` bağlantıları |
| ZRAM ve parlaklık kaydı | SysV `skynet-zram` ve `brightness` hizmetleri |
| USB-C UCSI açılış kurtarması | SysV `expertbook-ucsi-recover` → `/usr/local/libexec/expertbook-ucsi-recover --boot` |
| DWM, ses sunucusu ve oturum yardımcıları | `/usr/local/bin/skynet-session` |
| Otomatik kilit | Oturumun yönettiği `xss-lock` → `/usr/local/libexec/skynet-lock` |
| Bar, bildirimler, duvar kâğıdı ve tepsi uygulamaları | `/etc/dwm/autostart.sh` |
| Hoparlör/mikrofon durum kaydı | `skynet-session-extras` → `audio-mute-state watch --restore` |
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

- `sleep.conf.d/80-skynet-no-sleep.conf`: suspend, hibernate, hybrid-sleep
  ve suspend-then-hibernate yasak. elogind D-Bus `CanSuspend`/`CanHibernate`
  sorgularına `no` döner; masaüstü veya bir program istese de uyku olmaz.
- `logind.conf.d/80-skynet-lock.conf`: güç tuşu, uyku/hazırda bekletme
  tuşları ve kapak (pil, adaptör, dock) yalnız oturumu kilitler; boşta
  kalma eylemi yok.

`/etc/acpi/powerbtn-acpi-support.sh` logind D-Bus servisi varken hiçbir şey
yapmaz. 20 Kasım 2026 denetiminde kayıtlarda (19 Ekim'den beri) hiç
`PM: suspend`/`hibernation` girdisi yoktu.

