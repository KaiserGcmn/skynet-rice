# Geri yükleme ve derleme

Hedef sistem Devuan + SysVinit/elogind. Önce [DEVUAN.md](DEVUAN.md) içindeki güncel durumu oku.
Bu depo bir kurulum ISO'su veya tek komutla dağıtım dönüştürücü içermez.

## Kullanıcı dosyaları

`python3 scripts/restore-home.py` yalnızca değişiklik listesini gösterir.
`--apply` ile ev dizinine yazılır; `--home /başka/mevcut/dizin` ile deneme yapılabilir.
Root olarak çalıştırmak, hedefte sembolik bağlantı üzerinden yazmak ve dizin
üzerine dosya yazmak reddedilir. Değişecek tüm eski dosyalar önce yedeklenir.
Yedekteki `manifest.json` önce var olan ve yeni oluşturulan yolları ayırır;
`files/` altındaki dosyaları aynı göreli yola geri koyarak eski ayarlara dönülebilir.

Geri yüklenenler: Bash/nvm başlangıç ayarları, Kitty teması, Dunst, Fastfetch,
bottom, GTK 2/3/4 görünümü, fontconfig, xsettingsd, Flameshot, SKYNET duvar
kâğıdı ve kilit arka planı. Programların kendileri bu komutla kurulmaz. DWM'nin
`autostart.sh` betiği genel XDG autostart dosyalarını çalıştırmadığı için eski
Ferdium XDG autostart kaydı 20 Kasım 2026'da depodan çıkarıldı (hiç
tetiklenmiyordu); Ferdium elle başlatılır.

`home/.config/mimeapps.list`, PDF için Zathura'nın PDF Poppler başlatıcısını,
ses ve video için VLC'yi, JPEG/PNG/GIF/BMP/WebP fotoğrafları için `qimgv`'yi
varsayılan yapar. Kurulu uygulamaların bildirdiği medya türleri ve sistem MIME
eş adları dahil edilmiştir; qimgv'nin bildirdiği WebM desteğine rağmen videolar
VLC'ye gider. Programlar önceden kurulu olmalıdır. Bu dosya tarayıcı ve metin
düzenleyici tercihlerini de içerir; başka sisteme aktarırken önizlemeyi kontrol
et. 25 Ekim 2026'da canlı oturumda GIO ve `xdg-mime` sorgularıyla doğrulandı.

GTK görünümü `home/.themes/SKYNET-Black-Red/` ve GTK/xsettingsd kullanıcı
ayarlarıyla geri yüklenir. Tam siyah-kırmızı tema, kaynak/lisans, önizleme,
dconf tercihleri ve geri alma adımları [GTK-THEME.md](GTK-THEME.md) içindedir.

## Programlar

VS Code'un yalnız arayüzünü değiştiren SKYNET önayarı
`home/.config/skynet/vscode-ui.json` içindedir. Kullanıcı ayarlarıyla
birleştirme, kod/uyarı renklerinin korunması ve geri alma adımları
[VSCODE-UI.md](VSCODE-UI.md) içinde açıklanır.
Yerleşik Copilot/Chat özelliklerini kapatan ayrı tercih
`home/.config/skynet/vscode-no-ai.json` içindedir; bunu da mevcut VS Code
kullanıcı ayarlarına birleştir.

Greetd ve kilit ekranındaki dönen üçgenin kaynakları, yerel Devuan katmanı
ve doğrulaması [LOGO.md](LOGO.md) içinde açıklanır.
Yatay batarya simgesi ve DWM oturumunda etkinleştirme ayrıntıları
[BATTERY-BAR.md](BATTERY-BAR.md) içindedir.
Barın güncel SKYNET paleti, çalışma alanları ve başlık düzeni
[DWM-BAR.md](DWM-BAR.md) içinde açıklanır.

qimgv ve VLC'nin uyumlu siyah-kırmızı görünümü [MEDIA-UI.md](MEDIA-UI.md)
içindedir. qimgv yerleşik tema dosyasını kullanır; VLC için qt5ct paketi,
standart konuma kurulacak renk paleti ve kullanıcıya ait başlatıcılar gerekir.

1. `manifests/build-dependencies.txt` derleme için gereken paketleri listeler.
2. `python3 scripts/build.py --with-locker` DWM, dmenu/stest, slstatus, xwinwrap,
   gtkgreet-skynet, saver-lock-style, tuigreet-battery ve xsecurelock-power derler.
3. Çıktı yolunu `.build/last-build.txt` gösterir. `rootfs/` altında kurulacak
   ikililer ve yardımcı betikler bulunur. Bu ağacı `/` üzerine topluca kopyalama:
   kilit/giriş kaynaklarındaki Debian güç çağrıları için kurulu sürümün yerel
   Devuan kaynak yaması ayrıca gerekir. DWM/dmenu/slstatus gibi bağımsız
   bileşenler ayrı kurulabilir. Eski systemd kilit başlatıcısı artık derlemeye girmez.
4. `manifests/desktop-packages.txt` masaüstü bağımlılıkları için başlangıç
   listesidir. Devuan paket yöneticisinin çözdüğü sürümleri kullan; systemd
   kurmayı önerirse işlemi durdurup paket kaynağını düzelt.
5. Greetd/Cage/gtkgreet/tuigreet, Fastfetch/eza/bottom, Floorp, Ferdium,
   Spotify, SpoofDPI ve snixembed dağıtım/üçüncü taraf paketlerinden ayrıca sağlanır.
   Bunların ikilileri ve hesap verileri depoya gömülmedi.

Spotify için [resmi Debian paketini](https://www.spotify.com/us/download/linux/)
kullan. Minimal DWM kurulumunda `/usr/share/desktop-directories` yoksa paketin
`xdg-desktop-menu` çağrısı menü girdisini oluşturamayabilir. Bu standart dizini
root sahipliğinde 0755 izinle oluşturup paketle gelen
`/usr/share/spotify/spotify.desktop` dosyasını
`xdg-desktop-menu install --mode system --novendor` ile kaydet. Başlatıcı
`Exec=spotify %U` olarak kalmalıdır; anahtarlığı atlayan seçenek ekleme.
Kullanıcının Spotify profili ve oturum bilgileri depoya alınmaz.

USB takma/çıkarma sesleri için `runtime/usr/local/bin/skynet-usb-sounds` ve
güncel `skynet-session` birlikte kullanılır. Kullanıcının iki MP3 dosyası
`~/customsounds/` altında ayrıca bulunmalıdır; davranış, bağımlılıklar ve
kontrol adımları [USB-SOUNDS.md](USB-SOUNDS.md) içinde açıklanır.

Ses seviyesi tuşlarının örneği için güncel `dwm-volume` yardımcısını ve
`~/customsounds/Soundleveltest.mp3` dosyasını kullan. Mikrofon/mute göstergeleri
korunur; ayrıntılar [AUDIO-FEEDBACK.md](AUDIO-FEEDBACK.md) içindedir.
Bildirim sesi için `home/.config/dunst/` altındaki güncel yapılandırma, çalıştırılabilir
`notification-sound` yardımcısı ve SVG simgeler birlikte geri yüklenir;
`~/customsounds/Notificationrecieved.mp3` ayrıca sağlanır. Çalışan Dunst'a
`dunstctl reload` yeterlidir.

Bu Devuan makinesinde yeniden başlatma sonrası Spotify oturum kaybı için,
kullanıcının onayıyla `/etc/default/dbus` içindeki `IDTYPE="RANDOM"` değeri
`IDTYPE="FIXED"` yapıldı. Kurulu SysV betiği bu değerde mevcut
`/var/lib/dbus/machine-id` dosyasını sonraki açılışlarda korur. Gerçek makine
kimliğini silme, yenileme veya başka cihaza kopyalama; kimlik depoda bulunmaz.
Bu ayar `restore-home.py` tarafından uygulanmaz ve başka dağıtımların D-Bus
başlatıcıları için varsayılmamalıdır. Şifreleme değişmez; ancak kimliği okuyan
uygulamalar cihazı açılışlar arasında aynı kimlikle tanıyabilir. Spotify'a
yeniden giriş ve ardından gönüllü tam yeniden başlatma testi hâlâ gereklidir.
Geri almak için değeri `IDTYPE="RANDOM"` yap; sonraki açılışta kimlik yeniden
değişir ve kimliğe bağlı uygulamalar tekrar oturum açılmasını isteyebilir.
Bu ayar için çalışan D-Bus servisini yeniden başlatma.

Kilit ekranı dağıtımın **xsecurelock** paketi, `auth_x11` ve `authproto_pam`
yardımcılarını gerektirir. `--without-pam`, özel bir PAM yardımcısı
derlenmemesi içindir; parola doğrulaması kaldırılmamıştır. Sürüm korumaları
özelleştirilmiş eski arayüzü kullanmak yerine paket arayüzüne dönebilir.
Yeni dağıtımda bu kontrolleri kaldırarak zorla özel sürüm kullanma.

VS Code eklentilerini tekrar kurmak için, VS Code kurulduktan sonra:

```sh
while IFS= read -r extension; do
    code --install-extension "$extension" || break
done < manifests/vscode-extensions.txt
```

`apt-packages.tsv` 2.671 paketin, `apt-manual.txt` 339 manuel işaretin
17 Ekim 2026 envanteridir. Bağımlılıklar, eski çekirdekler ve Plasma da
listede bulunur; Devuan kurulum listesi olarak kullanılmaz. Node listesi
envanterdir; Node/npm veya Codex hesap verileri depoya kopyalanmadı.
Floorp eklentileri uBlock Origin ve Bonjourr; profil/oturum verileri alınmadı.

## GRUB ve donanım

- Güncel `/etc/default/grub` ve iki `grub.d/*.cfg` dosyası `profiles/debian/rootfs/`
  altında. Bir saniyelik menü, normal giriş seçimi ve çekirdek parametreleri korunuyor.
- Stock VMD kurtarma girdisi `.example` olarak tutulur. Eski disk UUID'si
  `@@ROOT_UUID@@` ile değiştirildi. Yeni sistemde doğru disk/çekirdek/initramfs
  yollarıyla tekrar oluşturulmalı. Eski `/boot/grub/grub.cfg` kopyalanmaz;
  yeni sistemin `update-grub` komutu çıktıyı yeniden üretir.
- VMD düzeltmesi `drivers/vmd/dkms/` altında bir DKMS paketi. Yalnız dağıtım
  `vmd.c` kaynağı incelenmiş 6.12.117 kaynağıyla aynı olan çekirdeklerde
  derlenir (srcversion kilidi); diğerlerinde atlanır. Kurulum ve yeni kaynağa
  taşıma: `docs/NVME-VMD.md`. Eski initramfs,
  imzalı modüller ve imzalama anahtarları bu depoda bulunmaz.
- ExpertBook LED ve rtw88 kaynakları `drivers/` içinde. DKMS ile yeni çekirdekte
  tekrar derlenmeli. Secure Boot gerekiyorsa yeni sisteme ait anahtar üretilir.
- TLP, USB udev kuralları, nftables ve initramfs kancası cihaz/dağıtım ayarlarıdır;
  yeni cihazın veya yeni çekirdeğin gereksinimleriyle birlikte uygulanır.

`reference/debian-maintenance/` eski bakım işlemlerinin kaydıdır. Bazı betikler
çekirdek, açılış veya masaüstü paketlerini değiştirebilir; bunlar genel kurulum
adımlarına dahil edilmedi. Eski test hazırlama betiğinin varlığı o testin aktif
olduğu anlamına gelmez.

Güncel Devuan LED yardımcısı `runtime/usr/local/bin/skynet-audio-leds` altındadır;
`skynet-session` bunu kullanıcı yetkisiyle başlatır. Oturum günlüklerinin boyuta
göre döndürülmesi ve gerçek sistem denetimi [MAINTENANCE.md](MAINTENANCE.md)
içinde açıklanır. Root logrotate ayarı `restore-home.py` tarafından kurulmaz.
Blueman'ın DWM çubuğuna doğrudan simge yerleştiren kalıcı kullanıcı ayarı da
[MAINTENANCE.md](MAINTENANCE.md#bluetooth-simgesi) içindedir; dconf tercihleri
`restore-home.py` kapsamına girmez.
