# Devuan bakım ve kaynak kullanımı — 25 Ekim 2026

## Dahili kamera için boşta güç tasarrufu — 2 Kasım 2026

Pil süresini uzatma isteği üzerine yalnız dahili `13d3:52bf` UVC kameraya
10 saniyelik boşta otomatik askıya alma istisnası eklendi. Önceden genel USB
kuralı kameranın `autosuspend_delay_ms` değerini `-1` yapıyor ve kullanılmadığı
zaman da uyanık tutuyordu. Artık gecikme `10000`, `power/control` değeri `auto`.
İstisna adaptör ve pil modunda geçerlidir; yalnız aygıtın boşta gücünü yönetir,
bilgisayarın uyku/hibernasyon ayarlarını değiştirmez.

Kural `profiles/debian/rootfs/etc/udev/rules.d/90-usb-no-autosuspend.rules`
dosyasında saklanır ve bu Devuan makinede `/etc/udev/rules.d/` altında kuruludur.
Genel USB kararlılık kuralları korunur; iki kamera satırı dosyanın sonunda
yalnız bu aygıt kimliğine istisna getirir. USB Wi-Fi, alıcı, Bluetooth,
parmak izi, kart okuyucu ve USB denetleyicileri için ayar değişmez. TLP,
ses, ekran parlaklığı ve %80 şarj sınırı aynı kalır.

Kalıcı kurulumdan önce kamera boşta askıya alındı; `/dev/video0` açılarak
`VIDIOC_QUERYCAP` ile yalnız aygıt yetenekleri okundu. Görüntü tamponu veya
kayıt akışı başlatılmadı. İki askıya alma/yeniden erişim döngüsünde aynı
yetenek bilgisi alındı ve kamera `active` durumuna geçti. Ardından tekrar
`suspended` olduğu, yeni kamera USB hatası/reset/bağlantı kopması olmadığı
doğrulandı. Diğer USB güç ayarları ve TLP dosyası karşılaştırıldı. Test
başarısızlığında eski ayarı geri yükleyen kurucu kullanıldı; yalnız başarılı
testlerden sonra kural atomik kuruldu ve udev kuralları yeniden yüklendi.
Gerçek video görüşmesi ve kart okuyucu testi yapılmadı.

Geri almak için dosyanın sonundaki yalnız `13d3:52bf` istisnasını kaldırıp
udev kurallarını yeniden yükleyin. Etkin kamerada `power/control=on` ve
`power/autosuspend_delay_ms=-1` değerleri önceki davranışı geri getirir.
Yeni açılışta genel USB kuralı da aynı değerleri uygular.

Bu değişiklik CPU hız sınırı veya ekran karartma eklemez. Kısa tüketim
örnekleri kullanıcı iş yükünden etkilendiği için belirli bir saat/yüzde
pil ömrü kazancı garanti edilmez.
[Linux USB güç yönetimi](https://docs.kernel.org/driver-api/usb/power-management.html).

Önceki iki dakikalık örnek 8,02 W, değişiklik sonrası iki dakikalık örnek
11,63 W ortalamaydı. Bunlar kontrollü bir A/B karşılaştırması değildir:
sonraki işlem örneğinde Floorp, web içerik süreçleri ve Ferdium belirgin
CPU kullanıyordu. Kamera 25 ölçümün tamamında `suspended` kaldı ve etkin
kalma sayacı artmadı. Yeni bir kamera hata döngüsü saptanmadı; gözlenen toplam
güç farkından bu değişikliğe ait pil süresi kazancı veya kaybı hesaplanmadı.

## 25 Ekim bakım kaydı

Bu denetim gerçek Devuan Excalibur, SysVinit/elogind ve DWM oturumunda yapıldı.
OpenRC taslakları kurulu hizmetler olarak değerlendirilmedi. Kullanıcının günlük
kullanım, uzun pil süresi, parlaklığın korunması ve USB-C'ye dokunulmaması
istekleri korundu.

## Uygulanan değişiklikler

`runtime/usr/local/bin/skynet-audio-leds`, kurulu yardımcının güncel kaynağıdır.
Ses sunucusunun sink/source/server/card olayları LED'leri hemen güncellemeye
devam eder. Sağlıklı durumda yedek donanım sorgusu 2 saniyeden 30 saniyeye
çıkarıldı; sorgu başarısızsa 2 saniyelik yeniden deneme korunur. İlk başarılı
eşitlemeden hemen sonra yapılan gereksiz ikinci sorgu kaldırıldı. Boşta yedek
ses sorgularının sıklığı yaklaşık %93 azalır; bu, toplam sistem CPU tüketiminin
veya pil ömrünün aynı oranda iyileştiği anlamına gelmez. Udev'in LED'i ses olayı
olmadan yeniden oluşturması durumunda yedek eşitleme 30 saniyeye kadar sürebilir.

Mevcut `/etc/logrotate.d/skynet-rice` kuralına `.xsession-errors` eklendi.
İki oturum günlüğü, günlük bakım çalıştığında 1 MiB eşiğine göre döndürülür;
iki eski kopya, sıkıştırma, `copytruncate`, `missingok` ve `notifempty` korunur.
Bu anlık bir dosya boyutu üst sınırı değildir; günlük iş çalışana kadar büyüme
olabilir. Günlükler temizlenerek hata kanıtları yok edilmedi. Kurulu kuralın
dosya listesi aşağıdaki gibidir; başka kullanıcıya aktarırken adları uyarlamak
gerekir:

```text
/home/<kullanıcı>/.local/state/skynet-rice/session.log /home/<kullanıcı>/.xsession-errors {
    su <kullanıcı> <kullanıcı>
    size 1M
    rotate 2
    compress
    delaycompress
    copytruncate
    missingok
    notifempty
}
```

APT/dpkg kilitleri alınarak yalnız kurulu veya kurulu sürümden eski olan 177
`.deb` arşivi kaldırıldı: 364.641.346 bayt, yaklaşık 348 MiB. Paketler, uygulama
profilleri ve kullanılan önbellekler kaldırılmadı; gelecekte gereken paket
arşivleri yeniden indirilebilir. Bu işlem disk alanı temizliğidir, hız testi
değildir. Otomatik güncellemeler ve indirme hızları değiştirilmedi.

## Denetim bulguları

- Yaklaşık 10 GiB kullanılabilir RAM, sıfır swap kullanımı ve %5 dolu kök
  dosya sistemi gözlendi. Örnek sırasında CPU/bellek/I/O basınç ortalamaları
  sıfırdı; genel bir kaynak darboğazı saptanmadı.
- NVMe SMART sağlık sonucu başarılı, kritik uyarı 0, medya hatası 0, hata
  günlüğü kaydı 0, sıcaklık 33 °C. Birikmiş unsafe-shutdown sayısı 141'dir;
  tek ölçüm mevcut kapatma akışının bozuk olduğunu göstermez.
- Çekirdek günlüğünde OOM, GPU reset, dosya sistemi I/O hatası veya kernel
  crash kategorileri bulunmadı. iwlwifi'nin 93 numaralı dosya arayışı ardından
  desteklenen 92 sürümü başarıyla yüklendi. TP-Link'in -71 uyarıları USB
  yeniden tanınma kayıtlarının yanındaydı; ardından SuperSpeed bağlantısı
  görüldü. Bunlar için çalışan sürücüler sıfırlanmadı veya değiştirilmedi.
- Paket bağımlılık ve dpkg denetimleri temizdi. O gün yenilenmiş APT listelerine
  göre bekleyen yükseltme yoktu. Otomatik güvenlik güncellemesi, cron,
  SMART izleme ve logrotate çalışıyordu.
- DWM, Dunst, slstatus, xwinwrap, PulseAudio, LED izleyicisi, USB izleyicisi ve
  Flameshot tek kopyaydı. Beş saniyelik örnek aktif uygulamaların kaynak
  tüketimini gösterir; uzun süreli boşta veya pil testi sayılmaz.
- Greetd ana süreci çekirdek başlangıcından 5,56 saniye, DWM 16,23 saniye sonra
  başladı. DWM zamanı kullanıcı girişini de içerir; açılış hızlanması veya
  etkileşime hazır olma ölçümü değildir. Greetd'in SysV betiğinde `status`
  eylemi yoktur; bu komutun hata dönmesi servisin durduğunu göstermez.

Mevcut 4 GiB LZ4 ZRAM, düşük öncelikli haftalık TRIM, `noatime`, pilde quiet/power
profili, %80 şarj sınırı ve bir saniyelik GRUB menüsü korundu. Baskı göstermeyen
sisteme rastgele swappiness/cache/çekirdek parametresi eklenmedi. Ağ,
Bluetooth, yazıcı/tarayıcı ve oturum hizmetleri devre dışı bırakılmadı.

## Doğrulama

Dört LED testi; bağımsız hoparlör/mikrofon durumu, başarısız sorguda mevcut LED'in
korunması, 65 saniyelik sanal boşta aralığında en fazla üç eşitleme, olayların
hemen işlenmesi, hızlı yeniden deneme ve alt süreç temizliğini doğrular.
Ses durumunu saklayan yardımcının 18 testi de geçti. Logrotate yeni kuralı ayrı
geçici dosyayla ve ardından tüm kurulu yapılandırmayla `--debug` modunda
doğruladı. PAM, kilit, oturum başlatıcısı, TLP, GRUB, fstab ve USB-C izleyicisi
hashleri korundu. Gerçek yeniden başlatma veya pil süresi deneyi yapılmadı.

Kaynaklar: [pactl olay dinleme](https://manpages.debian.org/trixie/pulseaudio-utils/pactl.1.en.html),
[logrotate](https://manpages.debian.org/trixie/logrotate/logrotate.8.en.html),
[çekirdek bellek parametreleri](https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html).

## Bluetooth simgesi

Bluetooth simgesi kaybolduğunda BlueZ, `blueman-applet` ve `blueman-tray`
çalışıyordu; adaptör açıktı ve rfkill engeli yoktu. DWM'nin XEmbed bildirim
alanı vardı, fakat `snixembed` çalışmıyordu. Köprü yeniden başlatıldığında
Bluetooth ve diğer SNI simgeleri çubuğa döndü. Köprünün neden sonlandığı
kesinleştirilmedi.

Blueman 2.4.4'ün `StatusNotifierItem` eklentisi kullanıcı ayarından kapatıldı.
`org.blueman.general` şemasının `plugin-list` değeri bu kullanıcıda
`['!StatusNotifierItem']` oldu. Böylece Blueman doğrudan DWM'nin desteklediği
`GtkStatusIcon`/XEmbed yöntemini kullanır; Bluetooth simgesi artık
`snixembed` sürecine bağlı değildir. Diğer uygulamalar için köprü korunur.
Bu ayar dconf'ta kalıcıdır, her girişte yeniden yazılması gerekmez.

Başka sisteme aktarırken mevcut eklenti tercihlerini koruyarak yalnız bu
tercihi eklemek için, grafik oturumundaki normal kullanıcıyla çalıştır:

```python
from gi.repository import Gio

settings = Gio.Settings.new('org.blueman.general')
plugins = [name for name in settings.get_strv('plugin-list')
           if name not in ('StatusNotifierItem', '!StatusNotifierItem')]
settings.set_strv('plugin-list', plugins + ['!StatusNotifierItem'])
Gio.Settings.sync()
```

Geri almak için yalnız `!StatusNotifierItem` girdisini kaldırmak yeterlidir.
`restore-home.py` dconf veritabanını kopyalamaz. Bluetooth hizmeti, eşleşmeler
ve adaptörün keşfedilebilirlik ayarı değiştirilmedi. Canlı oturumda
`GetStatusIconImplementations` yalnız `GtkStatusIcon` döndürdü; yeni simge
penceresi köprü yerine `blueman-tray` sürecine aitti.

## 27 Ekim 2026 — toplam 15 GiB swap

Kullanıcının isteğiyle yerel disk swap dosyası 256 MiB'den 11 GiB'ye
çıkarıldı; iki swap başlık sayfası için ayrıca 8 KiB eklendi. Mevcut 4 GiB
LZ4 ZRAM ile kullanılabilir toplam tam 15 GiB (16.106.127.360 bayt) oldu.
`free -h` çıktısı 15 GiB gösterir.
ZRAM önceliği 100, `/swapfile` önceliği -2 olarak korunur.

Ext4 üzerinde önceden ayrılmış yeni dosya hazırlandı; eski swap gerektiğinde
geri alınabilecek şekilde korunarak değiştirildi. `/swapfile` root:root 0600,
11.811.168.256 bayt ve aynı swap UUID'siyle doğrulandı. Etkinleştirme başarılı
olunca eski dosya ve geçici hazırlık dizini kaldırıldı. Büyük swap dosyası
kaynak deposuna dahil edilmez.

`/etc/fstab` içindeki mevcut `/swapfile` kaydı aynı kaldı; boyut sonraki açılışta
korunur. ZRAM yapılandırması, swappiness ve hibernasyon politikası değişmedi;
çekirdeğin resume aygıtı 0:0. Canlı `swapon`, `free`, izin/boyut ve başlangıç
kaydı kontrolleri geçti; yeniden başlatma gerekmedi.
## TP-Link ve çekirdek başlıkları — 3 Kasım 2026

`6.12.113+deb13-amd64` → `6.12.115+deb13.1-amd64` geçişi sonrasında TP-Link
`2357:0138` USB'de görünür fakat sürücüsüzdü. Güç durumu aktif, autosuspend
kapalıydı. LED destekli `rtw88-tplink-led` DKMS sürücüsü yalnız eski çekirdeğe
kuruluydu; yeni çekirdeğin headers paketi ve `linux-headers-amd64` takip paketi
eksikti. Paketli `rtw88_8822bu` mevcut LED sürücüsü tercihi nedeniyle blacklist'te
olduğundan yeni çekirdekte yedek sürücüye otomatik geçiş de yoktu.

Yalnız yeni çekirdeğin headers/common/kbuild paketleri ve `linux-headers-amd64`
kuruldu. Mevcut DKMS kaynaklarıyla TP-Link ve `expertbook-mute-led` yeni
çekirdeğe derlendi; `rtw_8822bu` ve `expertbook_mute_led` yüklendi. Güvenlik
doğrulamaları, blacklist, TLP, USB güç ayarları veya ağ hizmeti değiştirilmedi.
Adaptör kayıtlı 5 GHz bağlantısını kurdu; yalnız TP-Link arayüzünden yönlendiriciye
iki ping başarılıydı, paket kaybı yoktu. Eski çekirdek geri dönüş için korundu.

Sonraki çekirdek yükseltmelerinde `linux-headers-amd64`, eşleşen başlıkların
güncellenmesini sağlar; mevcut DKMS `AUTOINSTALL=yes` kancaları sürücüleri
hazırlar. Bu, gelecekteki her çekirdekle kaynak uyumluluğu garantisi değildir;
paket işlemi ve DKMS derleme hataları gözden geçirilmelidir. Kaynak ve kurulu
DKMS verisi bakım için gereklidir; yalnız bu işlemde indirilen .deb arşivleri
ve geçici çalışma dosyaları temizlendi.


## Ses ışığı yardımcısının boşta beklemesi — 4 Kasım 2026

`skynet-audio-leds`, PulseAudio aboneliğini saniyede bir select zaman
aşımıyla kontrol ediyordu. Yeni sürüm abonelik borusu, sinyal uyandırma
borusu veya zaten var olan 30 saniyelik donanım denetimini bekler.
Sessiz bir dakikada zamanlayıcı kaynaklı uyanma 60 yerine yaklaşık 2'dir;
bu oran tüm sistem CPU kullanımında aynı oranda kazanç anlamına gelmez.
Ses/mute olayları beklemeyi anında keser. Hatalı ilk sorguda 2 saniyelik
yeniden deneme, 30 saniyelik donanım toparlama kontrolü, konuşmacı/mikrofon
bağımsızlığı ve kapatılırken aboneliğin sonlandırılması korunur.

Beş test geçti: boşta bekleme sayısı, anlık ses olayları, ilgisiz client
olaylarının sorgu başlatmaması, ilk sorgu hatasından toparlama, iki ayrı
LED durumu ve gerçek alt süreçte SIGTERM sonrası bir saniyeden kısa
kapanış/alt sürecin toplanması. Gerçek hoparlör veya mikrofon durumu
değiştirilmedi. USB ses yardımcısı zaten bloklayan udev olayları kullanır;
USB sesleri ve diğer efekt yardımcıları değiştirilmedi. Yazıcı, tarayıcı
ve ağ keşfi servisleri kullanıcının tercihiyle korundu.

Yalnız `/usr/local/bin/skynet-audio-leds` atomik kuruldu. Açık oturumdaki
yardımcı kapatılmadı; değişiklik sonraki oturumda etkinleşir. SHA-256:
`97d385e2c0b05b622b8d1b2700ad3365fca933590bdd5b8faed70cb44a3d2a9f`.

Aynı gün yapılan salt okunur çekirdek kontrolünde 31.77, 67.87, 199.81 ve
483.47 saniyelerinde (son anda iki) toplam beş NVMe completion-polled
zaman aşımı bulundu. Bu SSD/sürücü bildirim sorununun kök nedeni henüz
belirlenmedi; LED optimizasyonuyla çözüldüğü iddia edilmez. USB-C UCSI
hatası da sürer. Disk, çekirdek, TLP, PAM veya güvenlik ayarları değiştirilmedi.

## Kararlılık denetimi ve USB-C kurtarması — 20 Kasım 2026

Root yetkili salt okunur denetimde (çekirdek 6.12.117, BIOS 310) oops,
kilitlenme veya GPU donması yoktu. SMART temiz (0 medya hatası, %0 aşınma),
yamalı VMD ile NVMe zaman aşımı 0. Normal `poweroff` sonrası NVMe
"Unsafe Shutdowns" 152'de kaldı; SysVinit kapanışı SSD'yi düzgün kapatıyor.

Kullanıcının "en sağlıklı" tercihiyle depo dışı sistem ayarları:

- `/etc/sysctl.d/99-zram.conf`: `vm.swappiness=100`, `vm.page-cluster=0`
  (zram öncelik 100 birincil swap; boyut/öncelik değişmedi).
- `/etc/initramfs-tools/modules`: `mei_me`, `mei_gsc_proxy`. GSC proxy artık
  i915'ten önce bağlanıyor; HuC "authenticated for all workloads". Eski
  initrd yedeği `/root/initrd.img-6.12.117+deb13-amd64.pre-mei.bak`;
  initramfs içinde DKMS `vmd.ko` doğrulandı.
- debconf `grub2/force_efi_extra_removable=true` (sonraki GRUB güncellemesi
  `EFI/BOOT` yedeğini de yeniler; şimdi `grub-install` çalıştırılmadı).
- 6.12.115 çekirdek/başlık paketleri ve ESP'deki BIOS 310 kopyası kaldırıldı;
  6.12.116 yedek çekirdektir ancak VMD düzeltmesini içermez.
- `live-config`/`live-tools` korunur: `refractasnapshot-base` bunlara
  bağımlıdır ve `boot=live` olmadan etkisizdir.

USB-C: `ucsi_acpi ... PPM init failed` kayıtlı 114 açılışın 72'sinde vardı
(BIOS 303 döneminde de). Bu durumda sürücü bağlı kalır ama Type-C portları
oluşmaz; şarj EC üzerinden etkilenmez. `ucsi_acpi` yeniden yüklenince iki
port geri geldi. Kullanıcı bu kez USB-C'ye dokunulmaması yerine sistemi
yavaşlatmayan güvenli düzeltmeyi seçti:

- `runtime/etc/init.d/expertbook-ucsi-recover`: SysV `S03`, yardımcıyı
  `setsid … &` ile ayırır; açılışı bekletmez.
- `runtime/usr/local/libexec/expertbook-ucsi-recover`: yalnız B3405CCA'da,
  `uptime` 30 s olana kadar bekler; portlar kendiliğinden gelirse dokunmaz.
  Yalnız `ucsi_acpi` bağlı ve port yoksa modülü bir kez yeniden yükler,
  sonucu syslog'a yazar; açılış başına tek deneme (`/run` + boot_id),
  bağlı olmayan sürücüyü asla yüklemez. `--status` salt okunurdur.
- `expertbook-usbc-watch` salt okunur gözlemci olarak değiştirilmedi.

`tests/test_ucsi_recover.py` 12 testle sağlıklı açılış, tek deneme, yeni
boot_id, geç kayıt, erken başlatma, bağlı olmayan sürücü, farklı model,
modül kaldırma hatası ve init betiği sözdizimini doğrular. Canlı kurulumda
portlar hazırken çalıştırıldı: "USB-C ready (port0,port1); no action".
Kurtarma yolu, bir sonraki hatalı açılışta syslog'dan doğrulanmalıdır.

### Temizlik (aynı gün, kullanıcı onaylı liste)

- Sistem: 6.12.115'ten kalan `/lib/modules/6.12.115+deb13.1-amd64`
  (yalnız eski elle kurulmuş `vmd.ko`), `skynet-stock` ve `pre-mei` initrd
  yedekleri (~180 MB), `/etc/ca-certificates.conf.dpkg-old`, kurulu olmayan
  xfce4-panel/xfce4-settings'e ait sahipsiz iki `.dpkg-new` dosyası ve
  kaldırılmış `claude-desktop` paketinin config artığı silindi. `/boot` içinde
  yalnız 6.12.116 ve 6.12.117 kaldı; `rc` durumunda paket yok.
- Ev dizini: kökteki kayıt videosu `~/Videos`, `lineercebir.txt`
  `~/Documents` altına taşındı; boş not, eski `package_list`, kurulum
  logu kopyası, eski `.xsession-errors.1`, boş `.kde` ve BIOS 310 zip'i
  silindi. Uygulama önbellekleri (~1.7 GB) bilerek korundu.
- Depo: `scripts/build.py` artık `runtime/` altındaki `__pycache__`/`.pyc`
  dosyalarını staging'e kopyalamaz (`tests/test_build_runtime.py`);
  çalışma ağacındaki bytecode önbellekleri silindi.

### ModemManager kaldırıldı

Kaynak denetiminde WWAN/modem donanımı bulunmadı (USB/PCI modem ve
`/sys/class/wwan` yok). Kullanıcı onayıyla `modemmanager` paketi purge
edildi; D-Bus etkinleştirme dosyası paketle kalktığından çalışan süreç de
durduruldu. NetworkManager, Wi-Fi ve bağlantı durumu (`connected:full`)
etkilenmedi. Arduino kartlarının seri portları artık modem yoklamasına
uğramaz. NFS istemcisi (`rpcbind`, `nfs-common`) kullanıcı tercihiyle korundu.
Geri dönüş: `sudo apt install modemmanager`.

## Gereksiz kod ve dosya temizliği — 20 Kasım 2026

Tema bileşenleri kullanılmayan kod, ölü yapılandırma ve canlı sistemden kopmuş
kopyalar için tarandı: DWM ve dmenu `-Wall -Wextra -Wunused` ile derlendi;
tüm `sources/` C kodunda tanımlı ama çağrılmayan statik fonksiyon/makro
arandı ve her aday elle doğrulandı; ekran görüntüleri, Dunst simgeleri, GTK
varlıkları, `runtime/` ve `home/` dosyaları canlı kopyalarla ve
referanslarıyla karşılaştırıldı.

**Kaldırılanlar**

- DWM: hiç çizilmeyen `SchemeStatusBATCell1/2/4/5` renk şemaları (her biri
  açılışta X sunucusunda boşuna 3 renk ayırıyordu), kullanılmayan
  `col_gray1` ve hiçbir şey değiştirmeyen `floorp` pencere kuralı (etiket
  0, yüzme 0, monitör −1 = varsayılan). Tek kalan `BATCell3`, gerçek işine
  göre `SchemeStatusAccent` oldu. Yeni ikilinin durum alanı önceki sürümle
  piksel düzeyinde aynıdır (0 farklı piksel). Kurulu SHA-256:
  `f90c8817101d6e3d1244c421d2d78a4068aac10be28528f598b705f26a838d0a`;
  önceki ikili `~/.local/share/dwm-theme-backups/before-cleanup-20261120T110043Z/`.
- GTK: `~/.config/gtk-3.0` ve `gtk-4.0` altındaki `gtk.css` (yalnız
  `@import 'colors.css';`), iki `colors.css` (yalnız `*_breeze` adlı
  renkler) ve 24 SVG'lik `gtk-3.0/assets/`. Bunlar KDE GTK ayar aracının
  Breeze çıktısıydı; SKYNET-Black-Red teması bu adların hiçbirini
  kullanmıyor ve aracın paketi kurulu değil. Canlı kopyalar silinmedi,
  `~/.local/state/skynet-rice/cleanup-20261120/` altına taşındı. Sonrasında
  GTK 3 teması, ikonlar ve imleç aynı şekilde yükleniyor.
  `manifests/captured-files.json` tarihsel yakalama kaydı olarak değişmedi
  (önceden silinen `.fehbg` gibi).

**Canlıyla eşitlenen kopyalar**

- `home/.icons/default/index.theme`: canlı `Inherits=Skynet`, depo hâlâ
  `breeze_cursors` diyordu.
- `runtime/usr/local/libexec/greetd/start-x`: canlı sürüm
  `/usr/local/bin/skynet-session` oturumunu da tanıyor; depo kopyası geride
  kalmıştı. `sh -n` geçer.

**Bilerek bırakılanlar (karar kullanıcıda)**

- `home/.config/autostart/ferdium.desktop`: DWM autostart XDG girdilerini
  çalıştırmadığı için hiç tetiklenmiyor ve canlıda yok
  (`docs/RESTORE.md` bunu zaten belirtiyor).
- `runtime/usr/local/libexec/expertbook-mute-led`: kurulu değil, hiçbir
  başlatıcı çağırmıyor; LED'leri `skynet-audio-leds` yönetiyor. Donanım
  geçmişi için referans olarak tutuluyor olabilir.
- slstatus'un `BAT [▰▰▰▰▱]` hücre karakterleri: DWM artık hücreleri kendisi
  çiziyor, ama bu biçim DWM ile slstatus arasındaki veri sözleşmesi ve
  testlere bağlı; kazanç birkaç satır.
- suckless ortak dosyalarındaki kullanılmayan `BETWEEN`/`ARGF` makroları ve
  systray yamasının `XEMBED_WINDOW_ACTIVATE` sabiti: upstream kod.

Taramada çıkan diğer adaylar (greeter `skynet_biometric_draw`, MATE Polkit
`*_init`, xwinwrap fonksiyonları) yerel yama veya GObject makroları
üzerinden kullanıldığı için yanlış pozitifti.

Regresyon: `tests/test_theme_assets.py` içindeki `DwmSchemeHygieneTest`
her şemanın çizildiğini, `config.h`'nin yalnız bilinen şemaları
tanımladığını ve etkisiz pencere kuralı olmadığını denetler; temizlik
öncesi kaynakta bu kontroller beş sorunu da yakalıyor.

### Kullanılmayan paketler ve manifest — 20 Kasım 2026

`manifests/desktop-packages.txt` canlı sistemle karşılaştırıldı. Listede
kurulu olmayan ve geri yüklemede yanlış/çakışan kurulum önerecek beş paket
vardı: `network-manager-gnome` (paket adı artık `network-manager-applet`),
`polkit-kde-agent-1` (yerine MATE Polkit ajanı, `mate-polkit`) ve
`pipewire`/`pipewire-pulse`/`wireplumber` (oturum PulseAudio kullanıyor;
PipeWire hiç çalışmıyor). Bunlar gerçek karşılıklarıyla değiştirildi;
rice'ın doğrudan kullandığı ama listede olmayan `xss-lock`, `flameshot`,
`zathura`, `zathura-pdf-poppler`, `thunar`, `mousepad`, `fprintd`,
`libpam-fprintd` eklendi. Liste artık 36 pakettir ve hepsi kurulu.
greetd, Fastfetch ve bottom `docs/RESTORE.md` gereği ayrı sağlanır.
`breeze-cursor-theme` listede kalır: Skynet imleci `Inherits=breeze_cursors`.

Sistemde kurulu olup rice tarafından kullanılmayanlar (kaldırılmadı, karar
kullanıcıda): Devuan canlı imajının XFCE görevinden kalan `parole`,
`ristretto`, `xfce4-clipman`, `xfce4-dict`, `xfce4-notes`,
`xfce4-screenshooter`, `xfce4-taskmanager`, `xfce4-terminal`, devre dışı
`slim` (`K01slim`; giriş yöneticisi greetd), `xscreensaver`,
`xscreensaver-gl`, `xscreensaver-data` (kilit XSecureLock + kendi saver'ı)
ve ModemManager kaldırıldıktan sonra sahipsiz kalan 10 paket
(`apt-get -s autoremove`: usb-modeswitch, libqmi/libmbim/libqrtr, libjim).
Thunar ve eklentileri, tumbler, xfconf ve Mousepad kullanıldığı için
aday değildir. `task-desktop`/`task-laptop` meta paketleri kaldırılırsa
bağımlılıkları otomatik işaretlenir; önce kullanılanlar `apt-mark manual`
ile korunmalıdır.

Skynet imleci (`~/.icons/Skynet`, üçüncü taraf) lisansı doğrulanmadığı
için depoya alınmadı.

**Uygulanan temizlik (kullanıcı onayıyla: "sistem sağlığını, temayı ve
donanımı bozmayacak olanlar")**

- `usb-modeswitch` ve `usb-modeswitch-data` **korundu** ve `apt-mark manual`
  ile autoremove'dan çıkarıldı: kuralları `0bda:1a2b` (RTL8822BU'nun sürücü
  CD modu) içeriyor; TP-Link `2357:0138` adaptörü bir gün bu modda açılırsa
  Wi-Fi'ı bu araç kurtarır. Bağımlılığı `libjim0.83` de bu sayede kalır.
- Kaldırılan 23 paket (`remove`, ayar dosyaları korunarak; sürümler
  `~/.local/state/skynet-rice/cleanup-20261120/removed-packages.txt`):
  parole, ristretto, xfce4-clipman/dict/notes/screenshooter/taskmanager/
  terminal, xscreensaver(+gl, data), slim ve bunların bıraktığı sahipsiz
  kütüphaneler (libck-connector0, libdbus-glib-1-2, libturbojpeg0,
  libjpeg-turbo-progs) ile ModemManager'dan kalan hücresel modem
  kütüphaneleri (libqmi/libmbim/libqrtr; sistemde WWAN modemi yok).
  apt'nin göremediği `/opt`, `/usr/local`, Floorp ve Spotify ikilileri bu
  kütüphaneler için tarandı; kullanan yok. `task-*` meta paketleri ve
  Thunar/Mousepad/tumbler/xfconf zincire girmedi.
- Devre dışı `slim`'in kalan init betiği `purge` ile silindi; açılışta
  yalnız `S05greetd` var.
- Sonrası: `dpkg --audit` temiz, autoremove adayı 0, iki Wi-Fi arayüzü IP
  almış, greetd/dwm/slstatus/dunst/nm-applet/blueman/snixembed/PulseAudio/
  xss-lock çalışıyor, GTK teması/ikon/imleç aynı.
- Depoya alınan, kurulu ve kullanılan ama eksik üç dosya:
  `runtime/usr/local/libexec/skynet-session-extras` (skynet-session
  çağırır), `runtime/usr/local/libexec/skynet-led-access` ve onu çağıran
  `runtime/etc/udev/rules.d/91-skynet-audio-leds.rules`.
- Hiç tetiklenmeyen `home/.config/autostart/ferdium.desktop` depodan
  çıkarıldı. `expertbook-mute-led` donanım geçmişi referansı olarak
  bırakıldı.

### USB-C (UCSI) kurtarma — 20 Kasım 2026

115 açılışın yaklaşık %60'ında `ucsi_acpi` "PPM init failed (ETIMEDOUT)" veriyor.
Oran şarj adaptörü takılıyken (%57) ve çıkıkken (%67) benzer. Kernel 6.12.117,
upstream'deki 10 sn zaman aşımı düzeltmelerini zaten içeriyor. Mainline'daki
init yeniden denemesi ise `ETIMEDOUT`'u kapsamıyor.

Aynı gün yapılan denemeler, modülün kaldırılıp hemen yüklenmesinin işe
yaramadığını gösterdi. Bekleme koyulduğunda kurtarma çalıştı. Adaptör
belirleyici değildi:

| Deneme | Adaptör | Kaldırma–yükleme arası | Sonuç |
|---|---|---|---|
| 11:16, 16:59 açılış servisi; 16:10 elle; 17:07 servis | takılı | yok | başarısız |
| 17:15 servis | çıkık | yok | başarısız |
| 16:44 elle | çıkık | 3 sn | başarılı |
| 17:16 elle | takılı | 3 sn | başarılı |

İkinci bulgu: `ucsi_init()` portları PPM ile konuşmasını bitirmeden kaydediyor.
Sonraki bir komut zaman aşımına uğrarsa portları yaklaşık 20 sn sonra geri
kaldırıyor (16:59: "con2: failed to get status", ardından "PPM init failed").
Eski yardımcı bu ara durumu "recovered" diye kaydetmişti.

`expertbook-ucsi-recover` buna göre güncellendi:

- Modül kaldırıldıktan sonra 5/10/20 sn bekleniyor.
- Bir açılışta en fazla 3 deneme yapılıyor; denemeler arasında 60 sn var.
- Portlar ancak 30 sn kesintisiz kayıtlı kalırsa hazır sayılıyor.
- Ara beklemede portlar kendiliğinden gelirse ya da sürücü elle kaldırılırsa
  dokunulmuyor.

Ara sürümde denenen "adaptör çıkınca yeniden dene" mantığı, 17:15'teki
başarısız denemeden sonra kaldırıldı. Testler `tests/test_ucsi_recover.py`
içinde (21 test). Bekleme, deneme sınırı ve deneme aralığı mutasyonla
doğrulandı.
