# Başlangıç denetimi — 3 Kasım 2026

SpoofDPI kaydı eksik değildi. Hem özgün rice hem kurulu `/etc/dwm/autostart.sh`
aynı özel komutu içeriyordu; güncel oturum günlüğü `application failed to
start / create server: failed to find default route: discover gateway: no
gateway found` gösterdi. Canlı süreç ve 9080 dinleyicisi yoktu. DWM açılırken
Wi-Fi rotası henüz hazır olmadığı için tek başlangıç denemesi kapanmıştı.

`skynet-spoofdpi` artık DWM autostart'ın arka plan işi olarak en fazla 120
saniye IPv4 varsayılan ağ geçidini bekler. Linkdown rotayı hazır saymaz;
oturum biterse beklemeyi bırakır. Ağ hazır olunca `exec` ile SpoofDPI olur;
kalıcı Python gözetmeni, sürekli yoklama veya ek sistem servisi yoktur.
`/run/user/UID/skynet-spoofdpi.lock` bekleme sırasında da yinelenen başlatmayı
engeller; kilit tanıtıcısı exec boyunca korunur. Çalışan bir SpoofDPI varsa
ikinci örnek başlatılmaz. 120 saniye boyunca ağ yoksa açık hata kaydıyla
çıkar; daha sonra bağlanıldığında `skynet-spoofdpi` elle çalıştırılabilir.

Korunan özel komut:

```sh
/usr/local/bin/spoofdpi --listen-addr 127.0.0.1:9080 \
  --dns-mode https --dns-https-url https://1.1.1.1/dns-query \
  --dns-qtype ipv4 --dns-cache --https-split-mode first-byte \
  --no-tui --log-level error
```

Kurulu SpoofDPI 1.5.5 seçenekleri yerel `--help` ile doğrulandı. Proxy ayarları,
DNS adresleri, TLS doğrulaması, güvenlik duvarı ve uygulama tercihleri
aynı kaldı. Dinleyici dış arayüze açılmaz. Kullanıcı oturumunda çalışır.

## Diğer başlangıç öğeleri

| Başlatıcı | Doğrulanan öğeler |
| --- | --- |
| `/etc/dwm/autostart.sh` | Dunst, snixembed, slstatus, nm-applet, blueman-applet, polkit MATE ajanı, skynet-wallpaper (xwinwrap + mpv) |
| `skynet-session` | xss-lock, xsettingsd, PulseAudio, Flameshot, skynet-usb-sounds, skynet-audio-leds, skynet-session-extras |
| `skynet-session-extras` | audio-mute-state watch --restore; planlı USB-C salt okunur kontrolü |
| PAM + oturum | gnome-keyring-daemon |

Bu öğeler canlı süreç listesiyle eşlendi. DWM kullanıcı autostart dizinleri
bulunmadığından `/etc/dwm` kullanır; kullanıcı XDG autostart dizini boştur.
Ferdium ve AFK kilidi kullanıcının isteğiyle kapalıdır. Eski feh başlangıcı
animasyonlu duvar kâğıdı yardımcısıyla, eski systemd kilit/ses işleri Devuan
SysVinit/elogind ve oturum yardımcılarıyla değiştirilmiştir. Özgün Ferdium
.desktop dosyasının depoda bulunması canlı oturumda etkin olduğu anlamına
gelmez. Bu denetim uygulamaların tüm işlevlerini değil başlangıç kapsamını
kontrol eder; snixembed'in günlükteki ayrı tepsi uyarıları bu işlemde değiştirilmedi.

## Doğrulama

Beş başlangıç regresyon testi: ağın gecikmeli gelmesi, linkdown/rotasız durum,
120 saniyelik üst sınır, oturum kapanışı ve özel argümanların korunması geçti.
Canlı kullanıcı oturumunda yardımcı üzerinden SpoofDPI başlatıldı; ikinci
çalıştırma yeni süreç açmadı. `ss` yalnız 127.0.0.1:9080 dinleyicisini gösterdi.
Proxy üzerinden example.com HTTPS isteği HTTP 200 / TLS doğrulama sonucu 0
verdi. Gerçek ağ bağlantısı kesilmedi, bilgisayar yeniden başlatılmadı.

Kalıcı değişiklikler yalnız `/usr/local/bin/skynet-spoofdpi` ve mevcut
`/etc/dwm/autostart.sh` içindeki SpoofDPI satırıdır. Makinedeki imleç/MATE
ajanı gibi diğer başlangıç uyarlamaları korunur. İki dosya root:root 0755
olarak kurulur. Kaynak, test ve belge depoda tutulur; kurulum geçicileri silinir.

## Polkit ajan seçimi — 12 Kasım 2026

Denetimde canlı ve depodaki başlangıcın kurulu olmayan KDE ajanını hedeflediği
bulundu. Başlangıç artık önce `/usr/local/libexec/` içindeki DWM uyumlu MATE
ajanını, bulunmazsa `/usr/libexec/` içindeki dağıtım sürümünü seçer. İki yolun
herhangi birinden çalışan MATE ajanı varsa ikinci örnek başlatılmaz. İkisi de
bulunmazsa sessizce atlamak yerine stderr'e açık bir hata yazılır. Polkit
kuralları, PAM ve parola doğrulaması değişmez.

Dört yalıtılmış başlangıç testi yerel seçim, dağıtım yedeği, mevcut ajanı
tekrar başlatmama ve eksik ajan hata kaydını doğruladı. Eski özel D-Bus
entegrasyon testleri bu ortamda Polkit geliştirme başlıkları bulunmadığından
atlanmıştır; bunlar başarılı test olarak sayılmaz.

Canlı kurulum normal Polkit yetkilendirmesiyle tamamlandı. Başlangıç dosyası
root:root 0755, depo kopyasıyla aynı; SHA-256:
`405aea80cc814634e3a23e11c1bfd8073332e2b97932676040fbf869508793a3`.
PAM dosyalarının önce/sonra hashleri aynı. Yerel ajan hata kaydı boş ve
başlangıç bloğu iki kez çalıştırıldığında aynı tek süreç korundu. Gerçek
yeniden açılış bu değişiklikten sonra henüz denenmedi.
