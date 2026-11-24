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

`runtime/usr/local/bin/audio-leds`, kurulu yardımcının güncel kaynağıdır.
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

`audio-leds`, PulseAudio aboneliğini saniyede bir select zaman
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

Yalnız `/usr/local/bin/audio-leds` atomik kuruldu. Açık oturumdaki
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
  `/usr/local/bin/dwm-session` oturumunu da tanıyor; depo kopyası geride
  kalmıştı. `sh -n` geçer.

**Bilerek bırakılanlar (karar kullanıcıda)**

- `home/.config/autostart/ferdium.desktop`: DWM autostart XDG girdilerini
  çalıştırmadığı için hiç tetiklenmiyor ve canlıda yok
  (`docs/RESTORE.md` bunu zaten belirtiyor).
- `runtime/usr/local/libexec/expertbook-mute-led`: kurulu değil, hiçbir
  başlatıcı çağırmıyor; LED'leri `audio-leds` yönetiyor. Donanım
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

Skynet imleci (`~/.icons/Skynet`) 22 Kasım 2026'dan beri depoya ait özgün bir
settir; `sources/skynet-cursor/render-cursors.py ~/.icons/Skynet` ile üretilir
(bkz. [CURSOR.md](CURSOR.md)). Eski üçüncü taraf set depoya alınmadı.

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
  `runtime/usr/local/libexec/dwm-session-extras` (dwm-session
  çağırır), `runtime/usr/local/libexec/expertbook-led-access` ve onu çağıran
  `runtime/etc/udev/rules.d/91-audio-leds.rules`.
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

## Floorp'un kendiliğinden güncellenmesi — 22 Kasım 2026

Floorp 19 Ekim'de elle `.deb` ile kurulmuştu ve hiç güncellenmiyordu (12.20.2
kalmıştı; 22 Kasım'da 12.21.2'ye elle yükseltildi). Artık resmi depodan
gelir ve sistemin günlük `unattended-upgrades` çalışmasıyla güncellenir.

| Dosya | Görevi |
| --- | --- |
| `runtime/etc/apt/sources.list.d/floorp-ppa.sources` | `https://ppa.floorp.app/amd64/` deposu. İmza anahtarı (Floorp Dev, `A8C2 0FCD D577 3994 1A81 3D5D 8F64 DCC7 C806 D572`) dosyanın içindedir; yalnız bu depo için geçerlidir, genel anahtar halkasına eklenmedi. |
| `runtime/etc/apt/preferences.d/floorp-ppa` | Bu depodan yalnız `floorp` paketi gelebilir; başka her paket için öncelik -1'dir. |
| `runtime/etc/apt/apt.conf.d/99floorp-ppa` | `unattended-upgrades` izinli kaynaklarına `site=ppa.floorp.app` ekler. Deponun Release dosyasında Origin/Suite alanı olmadığından ana makine adıyla eşleşir. |

Ad sırası önemlidir: `99expertbook-security-upgrades` listeyi `#clear` ile
sıfırlayıp yalnız Devuan güvenlik deposunu bırakır. `52...` adıyla okunan ilk
deneme bu yüzden siliniyordu; dosya `99floorp-ppa` olarak ondan sonra
okunur. Devuan tarafındaki otomatik güncelleme kapsamı değişmedi (yalnız
güvenlik).

Kurulum (root, 0644): üç dosyayı aynı yollarla `/etc/apt/` altına koy,
`apt-get update` çalıştır. Doğrulama:

```sh
apt-cache policy floorp                 # aday ppa.floorp.app'ten
apt-config dump | grep Origins-Pattern  # Devuan-Security ve site=ppa.floorp.app
sudo unattended-upgrade --dry-run -d    # "Allowed origins" ikisini de listeler
```

Floorp açıkken güncellenirse tarayıcı yeniden başlatma ister; ayarlar ve
profil korunur. Kaldırmak için üç dosyayı silip `apt-get update` çalıştır;
kurulu paket yerinde kalır. Testler: `tests/test_floorp_apt.py`.

## PulseAudio çalışma dizini hatası — 22 Kasım 2026

Belirti: her çıkışta ve kapanışta syslog'a
`pa_get_runtime_dir:Failed to create secure directory (/run/user/1000/pulse): No such file or directory`
yazılıyordu (19–22 Kasım arasında 24 kez).

Neden: `dwm-session`, PulseAudio'yu `pulseaudio --start` ile başlatıyor.
Daemon kendini arka plana aldığı için oturumun izlediği alt süreçler arasında
değil. Oturum kapanınca elogind `/run/user/1000` dizinini siliyor; daemon ise
çıkışta son istemcinin gidişinden 20 sn sonra (boşta çıkma), kapanışta
`sendsigs` ile daha sonra sonlanıyor ve artık var olmayan dizine yazmaya
çalışıyor. Ses çalışmasını etkilemiyordu; yalnızca günlük gürültüsüydü.

Düzeltme: `runtime/usr/local/bin/dwm-session` içindeki `cleanup`, alt
süreçleri durdurduktan sonra `stop_pulseaudio` çağırıyor: daemon çalışıyorsa
`pulseaudio --kill`, ardından en fazla 3 sn `pulseaudio --check` ile bekliyor.
Bu, çalışma dizini hâlâ varken olduğu için hata oluşmuyor. Ses düzeyleri
PulseAudio'nun kendi veritabanında kaldığı için sonraki girişte aynen geliyor.

Doğrulama: `tests/test_session_pulseaudio.py` (5 test); yalıtılmış bir
PulseAudio örneğinde dizin silinip boşta çıkıldığında PID dosyası uyarıları
çıktı, `stop_pulseaudio` ile önce durdurulunca hiç uyarı çıkmadı (12 ms).
Canlı doğrulama: sonraki çıkış veya kapanıştan sonra
`grep pa_get_runtime_dir /var/log/syslog` boş dönmeli.

## Çekirdek ve ağ sertleştirmesi, 6.12.118 — 23 Kasım 2026

Tam sistem denetiminden sonra düşük riskli sertleştirme eklendi:
`runtime/etc/sysctl.d/91-hardening.conf` → `/etc/sysctl.d/`. Açılışta
`procps` yüklüyor; `sysctl -p` ile hemen uygulandı.

| Ayar | Önce | Sonra | Etkisi |
| --- | --- | --- | --- |
| `kernel.kptr_restrict` | 0 | 1 | Çekirdek adresleri yetkisiz kullanıcıya görünmez |
| `kernel.yama.ptrace_scope` | 0 | 1 | Süreç yalnız kendi alt süreçlerini izler; `gdb -p`/`strace -p` başka sürece root ister |
| `kernel.kexec_load_disabled` | 0 | 1 | Çalışan çekirdek kexec ile değiştirilemez (yeniden başlatmaya kadar geri alınamaz) |
| `accept_redirects`, `send_redirects` | 1 | 0 | ICMP yönlendirmesi kabul edilmez/gönderilmez; mevcut ve sonradan açılan arayüzler dahil |
| `net.ipv4.tcp_rfc1337` | 0 | 1 | TIME-WAIT soketleri RST ile öldürülemez |

Bilerek dokunulmayanlar: `rp_filter` (`50-default.conf` zaten 2), kullanıcı
ad alanları (Floorp ve bubblewrap sandbox'ı için gerekli), `kernel.sysrq`.
Geri alma: dosyayı silip yeniden başlatmak yeterli. Ek olarak `~/.config/gh`
izni 771'den 700'e çekildi.

Aynı gün güvenlik güncellemeleri ve çekirdek 6.12.118 kuruldu. 118'in stok
`vmd.ko` srcversion'ı (9CED7F0241F8FAD2F7858E3) 117 ile aynı olduğundan
`vmd-mtl016` DKMS paketi kapıdan geçip derlendi; `expertbook-mute-led` ve
`rtw88-tplink-led` de derlendi. Yeni initrd'de yamalı `vmd.ko`
(`0.6-mtl016-deb13-117`) ve `mei_me`/`mei_gsc_proxy` var. 117 ve 116
yedek olarak duruyor; 116 yamasız olduğu için yedek olarak kullanılmamalı.
Doğrulama: `tests/test_sysctl_hardening.py`. Canlı doğrulama: 118'e yeniden
başlatınca `/sys/module/vmd/version` `0.6-mtl016-deb13-117` vermeli ve
`sudo dmesg | grep -i "nvme.*timeout"` boş dönmeli.

## Araç adlarından `skynet-` önekinin kaldırılması — 23 Kasım 2026

Programlar, servisler ve paketler işlevlerini anlatan adlar aldı. Başka bir
paketle çakışmadığı Debian trixie `Contents` dizinine (main, amd64 ve all) ve
bu makinedeki kurulu dosyalara karşı doğrulandı. Önce `fingerprint-auth`
seçilmişti, ancak `authselect` aynı adı `/etc/pam.d` altında üretebildiğinden
`dwm-fingerprint` kullanıldı.

| Eski | Yeni |
| --- | --- |
| `skynet-session` | `dwm-session` (xsession: `dwm-session.desktop`) |
| `skynet-wallpaper` | `dwm-wallpaper` |
| `skynet-spoofdpi` | `spoofdpi-launch` |
| `skynet-usb-sounds` | `usb-sounds` |
| `skynet-audio-leds` | `audio-leds` |
| `skynet-lock`, `skynet-lock-controls` | `dwm-lock`, `dwm-lock-controls` |
| `skynet-session-extras` | `dwm-session-extras` |
| `skynet-led-access` | `expertbook-led-access` |
| `skynet-nvme-shutdown-audit` (+ `/var/log/skynet-nvme-shutdown.log`) | `nvme-shutdown-audit` (+ `/var/log/nvme-shutdown-audit.log`) |
| `greetd/skynet-greeter`, `gtkgreet-skynet` | `greetd/hud-greeter`, `gtkgreet-hud` |
| `/usr/local/share/skynet-greeter`, `/etc/greetd/skynet.css` | `/usr/local/share/hud-greeter`, `/etc/greetd/gtkgreet-hud.css` |
| `auth_x11_skynet` | `auth_x11_hud` |
| `mate-polkit-skynet` (kaynak dizini) | `mate-polkit-hud` |
| `~/.local/bin/skynet-os-age` | `~/.local/bin/os-age` |
| `~/.config/skynet/` | `~/.config/dwm-desktop/` |
| PAM `skynet-fingerprint` | `dwm-fingerprint` |
| init: `skynet-firewall`, `skynet-zram` | `host-firewall`, `zram-swap` |
| `cron.weekly/skynet-fstrim` | `cron.weekly/weekly-fstrim` |
| sysctl `90-skynet-panic`, `91-skynet-hardening` | `90-panic-reboot`, `91-hardening` |
| `sudoers.d/99-skynet-pwfeedback` | `99-pwfeedback` |
| elogind `80-skynet-lock`, `80-skynet-no-sleep` | `80-dwm-lock`, `80-no-sleep` |
| `udev 91-skynet-audio-leds.rules`, `grub.d/99-skynet-wallpaper.cfg` | `91-audio-leds.rules`, `99-grub-wallpaper.cfg` |
| apt `skynet-floorp` (üç dosya) | `floorp-ppa` |
| DKMS `skynet-vmd`, modül etiketi `0.6-skynet-mtl016-deb13-117` | `vmd-mtl016`, `0.6-mtl016-deb13-117` |

Bilerek değişmeyenler: görsel kimlik (GTK teması `SKYNET-Black-Red`, imleç,
GRUB teması `skynet-neon`, duvar kâğıtları, arayüz yazıları) ve proje adı
(`skynet-rice` deposu, `~/.local/state/skynet-rice`, `/var/lib/skynet-rice`).
Derleme başlıklarının dosya adları (`skynet-hud.h` gibi) ve tarihsel kayıtlar
(`manifests/captured-files.json`, 6.12.115 kurulum betikleri) de aynen kaldı.

DKMS geçişi çekirdek başına yapıldı: eski paket kaldırıldı, yenisi derlendi ve
`.text`, `.data`, `.rodata*`, `.bss` bölümleri eski modülle bayt bayt
karşılaştırıldı; tek fark derleme dizini yolunu taşıyan hata iletisi dizgesi
(`/var/lib/dkms/<paket>/…/build/vmd.c`). Aksi halde eski paket otomatik geri
yüklenecekti. 117 ve 118 initrd'lerinin dosya listeleri geçişten önceki
listelerle aynı.

Makineye özgü `~/.local/share/skynet-rice/devuan-source.patch` yeni dizin
adlarıyla güncellendi (eskisi yedekte); `sources/gtkgreet-hud` üzerine
uygulanınca kurulu greeter ile aynı boyutta ikili üretiyor, tek fark
`/usr/local/share/hud-greeter/…` yolu.

Çalışan masaüstü oturumu eski adlı dosyaları kullandığı için şu kalıntılar
oturum yenilenene kadar bırakılmıştı:
`/usr/local/bin/skynet-{session,wallpaper,spoofdpi,usb-sounds,audio-leds}`,
`/usr/local/libexec/{skynet-lock,skynet-lock-controls,skynet-session-extras,auth_x11_skynet}`,
`/usr/local/libexec/greetd/skynet-greeter` (yeni greeter'a yönlendiren tek
satırlık kabuk), `/etc/pam.d/skynet-fingerprint` ve `~/.config/skynet/`.
Yeniden başlatıp yeni oturum açıldıktan sonra (çekirdek 6.12.118,
`/sys/module/vmd/version` = `0.6-mtl016-deb13-117`, NVMe zaman aşımı yok,
tüm oturum süreçleri yeni adlarla çalışıyor) hiçbir sürecin bu dosyaları açık
tutmadığı ve `~/.config/skynet` ile `~/.config/dwm-desktop` içeriğinin birebir
aynı olduğu doğrulanıp hepsi silindi.
Yedek (depo, canlı sistem dosyaları ve initrd'ler) doğrulama bittikten sonra
23 Kasım 2026'da silindi.

Silmeden önce yapılan derin doğrulamada tek gerçek eksik bulundu:
`x-session-manager` alternatifi elle `/usr/local/bin/skynet-session` dosyasına
ayarlıydı (`/var/lib/dpkg/alternatives` altında olduğu için metin taraması
görmemişti). `update-alternatives` ile `dwm-session` kaydedilip seçildi, eski
kayıt kaldırıldı. Başka kırık bağlantı yok ve derlenmiş ikililerde eski araç
adı gömülü değil. `saver-lock-style` ikilisinin eskisinden tek anlamlı farkı
`dwm-lock-controls` yolu (dizgenin kısalması sonraki adresleri kaydırdığı için
`.text` ve `.rodata` baytları değişiyor). Özel Xephyr ekranlarında gerçek
`dwm-lock` zinciri (`xsecurelock-power`, `auth_x11_hud`, `saver-lock-style`,
PAM `dwm-fingerprint`), kilit ve duvar kâğıdı entegrasyon testleri (6 test) ve
cage içinde `gtkgreet-hud` çalıştırıldı; eski ve yeni `saver-lock-style` ile
kilit ekranı görüntüsü aynı çıktı. Her iki initrd'deki `vmd.ko.xz` diskteki
modülle aynı SHA-256'ya sahip.

Notlar: `test_polkit_session` (Polkit geliştirme başlıkları yok) ve
`test_snixembed` (ikili derlenemedi) bu makinede çalışamıyor.
`~/.local/lib/skynet-kitty` (120 MB), `docs/KITTY.md`'de belgelenen,
kullanılmayan önceki 5 Kasım kurulumudur; başlatıcı `/usr/bin/kitty` kullanıyor
ve adı bilerek değiştirilmedi. `host-firewall`, `zram-swap` ve `weekly-fstrim`
bu sırada depoda yoktu; 23 Kasım'da `runtime/etc/` altına alındı. `99-pwfeedback`
kullanıcı adı içerdiği için dosya olarak değil, `docs/RESTORE.md`'de komut olarak belgelenir.

## Thunar ve GTK simgelerinin mavisi — 23 Kasım 2026

Thunar'daki mavi klasör ve yer simgeleri tema CSS'inden değil, `breeze-dark`
simge temasından geliyordu: Breeze bunları SVG içindeki tek bir
`.ColorScheme-Highlight { color: #3daee9; }` ile boyar. Sonrasında tüm
simgelerin temaya uyması istendi: `breeze-dark`'ın 7618 SVG'sinin yarısı
(3734) mavinin yanında yeşil, turuncu, sarı, mor, başka maviler ve soluk
bej/arduvaz tonları kullanıyordu.

Sistem dosyalarına dokunmadan `scripts/build-icon-theme.py`
`~/.local/share/icons/breeze-dark-red` temasını üretir (7131 simge, 40 MB;
sembolik bağlar çözülür). Kural: `#3daee9` tam olarak `--color` (varsayılan
`#b02a30`, tema vurgusu `#d32f2f`'den bir ton koyu) olur; doygunluğu 0,30'dan
yüksek diğer renkler aynı kırmızı tona (doygunluk en çok 0,62) gider ve
açıklık `0,15 + 0,5·L` ile sıkıştırılır, böylece çok tonlu simgelerin ton
sırası korunur; doygunluğu 0,10–0,30 olan tonlar (bej, arduvaz) çelik grisine
çekilir; gri, beyaz ve siyaha dokunulmaz. Üretilen temada kalan tüm doygun
renkler 0° (kırmızı) tonundadır. `index.theme`, `Inherits=breeze-dark,...` ile
kalan her şeyi kaynak temadan alır. Betik kendi ürettiği dizinin dışında
hiçbir şeyi silmez. Bedeli: yeşil/turuncu gibi anlam taşıyan durum renkleri
de kırmızı olur, ayrım şekille yapılır. PNG simgeler (hicolor, Adwaita uygulama
simgeleri) yeniden boyanmaz; `blueman` özel simgeleri zaten beyazdır.

Simge teması adı GTK 2/3/4 (`gtkrc-2.0`, `settings.ini`), `qt5ct.conf`,
`xsettingsd.conf` ve `dunstrc` (`icon_theme` ile `icon_path`, `~` ile) içinde
`breeze-dark-red` olarak ayarlandı (hem `home/` hem canlı). `xsettingsd`
çalıştığı için GTK uygulamaları simge temasını oradan alır; `SIGHUP` ile,
`dunst` ise `dunstctl reload` ile yüklendi. Doğrulama: gerçek ekranda yalnız
Thunar penceresi yakalandı, dunst özel D-Bus ve Xephyr içinde denendi; testler:
`tests/test_icon_theme.py`.

## Prizde işlemci performansı — 23 Kasım 2026

Core Ultra 7 255H prizdeyken `CPU_ENERGY_PERF_POLICY_ON_AC=balance_performance`
nedeniyle yavaş kalıyordu. Platform profili (`balanced` ya da `performance`)
sonucu değiştirmedi; tavanı enerji tercihi (EPP) koyuyordu. Aynı yük, EPP
dışındaki her şey sabitken (turbo açık, profil `balanced`, prizde) iki kez
ölçüldü:

| Ölçüm | `balance_performance` | `performance` |
|---|---|---|
| tek çekirdek (cpu0), iş hacmi | ~800 it/s | ~1800 it/s (yaklaşık 2,2 kat) |
| 16 çekirdek toplam iş hacmi | ~10 bin it/s | ~14 bin it/s (yaklaşık %40) |
| P-çekirdek frekansı, tüm çekirdek yükü | 2,3 GHz | 3,9 GHz |
| paket gücü / sıcaklık (tüm çekirdek) | ~15 W / 61 °C | ~29 W / 76 °C |

Ölçüm Python döngüsüyle ve yaklaşık 8 saniyelikti; gerçek uygulama hızı
değildir. BIOS'un MMIO güç sınırları 25 W (sürekli) ve 44 W (kısa süreli),
MSR tarafında görünen 50 W/64 W'ın altındadır, bu yüzden uzun süreli tam
yükte `performance` ile de güç 25 W civarına iner. Süre ölçerek karşılaştırmak
yanıltıcıdır: toplam süreyi 2,5 GHz'de kalan düşük güçlü 14-15 numaralı
çekirdekler belirler.

`/etc/tlp.d/90-expertbook-b3405.conf` içinde yalnız
`CPU_ENERGY_PERF_POLICY_ON_AC=performance` yapıldı (yedek:
`~/.local/state/skynet-rice/backups/tlp-epp-20261123/`); pil ayarları
(`power`, turbo kapalı, `quiet`) aynı. `tlp start` ile uygulandı, tüm
çekirdeklerde `performance` okunuyor. Bedeli: yüklü işlerde yaklaşık 15-20 °C
daha sıcak ve fan daha çok çalışır; boşta fark yoktur. Geri almak için satırı
`balance_performance` yapıp `tlp start` çalıştırmak yeter.

### Pil modu: hızlı ama uzun gitsin — 23 Kasım 2026

Pil ayarı (`power`, turbo kapalı, profil `quiet`) enerji açısından en
cimrisiydi ama gereksiz yavaştı. Prizde pil modu zorlanıp (`quiet` profil)
beş aday aynı yükle karşılaştırıldı; RAPL paket enerjisi, ekran ve Wi-Fi hariç.
"Görev": cpu0'da sabit bir iş, 6 saniyelik pencerede enerji (iş bitince boşta
beklenir); "16 çekirdek": sürekli tam yük.

| Ayar | görev süresi | 6 sn enerji | 16 çekirdek | sürekli güç |
|---|---|---|---|---|
| `power`, turbo kapalı (eski) | 2,09 s | 23,3 J | 7888 it/s | 16,7 W |
| `balance_power`, turbo kapalı | 2,00 s | 23,5 J | 8403 it/s | 16,6 W |
| `balance_power` + turbo | 1,66 s | 23,1 J | 10128 it/s | 24,1 W |
| `power` + turbo | 1,86 s | 24,0 J | 9796 it/s | 23,9 W |
| `balance_performance` + turbo | 1,19 s | 37,6 J | 9287 it/s | 24,5 W |

İlk seçim `balance_power` + turbo idi; aynı gün turbo kapatıldı (aşağıda). Geçerli ayar: `CPU_ENERGY_PERF_POLICY_ON_BAT=balance_power`, `CPU_BOOST_ON_BAT=0`.
Kısa ve orta işlerde görev yaklaşık %20 hızlı biter, harcanan enerji aynı ya da
biraz düşüktür (işlemci işi çabuk bitirip boşa döner). `balance_performance`
en hızlısıdır ama aynı işe yaklaşık %60 fazla enerji harcar. Bedel: derleme,
video kodlama gibi uzun tam yüklerde paket gücü 17 W yerine 24 W'a çıkar; bu
tür işlerde pil daha hızlı biter. O durumda `CPU_BOOST_ON_BAT=0` (EPP
`balance_power` kalsın) yeterlidir: hız eskisine yakın kalır, güç 17 W'ta tutulur.
Platform profili `quiet`, HWP dinamik artırma kapalı kaldı. Gerçek pil saati
ölçülmedi (ölçümler prizdeydi ve yalnız işlemci paketini kapsar; pilin asıl
tüketicisi ekran ve Wi-Fi'dır). `tlp bat` ve `tlp start` ile iki modda
uygulanan değerler okunup doğrulandı. Yedek:
`~/.local/state/skynet-rice/backups/tlp-epp-20261123/`.

Turbo kararı: turbo bir ara kapatıldı, sonra kullanıcının önceliği netleşince
(pil uzun gitsin ama bilgisayar aşırı kısıtlanmasın) geri açıldı. Aynı
`balance_power` ayarında turbo 2 saniyelik görevi 2,00 s yerine 1,66 s'de
bitirir ve 6 saniyelik enerji aynıdır (23,5 / 23,1 J); bedeli yalnız sürekli
tam yük gücüdür (16,6 W yerine 24,1 W, iş hacmi %20 fazla). Kısa ve orta
işlerde pil tüketimi değişmez, bilgisayar da hissedilir biçimde daha çevik
kalır; uzun derleme ya da kodlama gibi işlerde pil daha hızlı biter. Geçerli
ayar: `CPU_ENERGY_PERF_POLICY_ON_BAT=balance_power`, `CPU_BOOST_ON_BAT=1`.
Pil modu yine de prizin yaklaşık 2 katı yavaşıdır (görev 1,66 s, prizde
`performance` ile 0,83 s). Daha çevik isteniyorsa bir basamak yukarısı
`balance_performance` + turbodur (1,19 s) ama aynı işe yaklaşık %60 fazla enerji
harcar; uzun ağır işlerde pili korumak için `CPU_BOOST_ON_BAT=0` yeter.

En dengeli ayar: `CPU_MAX_PERF_ON_BAT` — 23 Kasım 2026

Pilde turbo açıkken uzun tam yükte güç 23-24 W'a çıkıyordu. TLP'de bunu
doğrudan sınırlayan tek ayar `CPU_MAX_PERF_ON_BAT` (en yüksek frekansın yüzdesi);
`balance_power`, turbo açık, profil `quiet` ile aynı yük altında denendi
(ölçüm gürültüsü görev süresinde yaklaşık ±0,1 s):

| `max_perf` | görev süresi | 16 çekirdek gücü |
|---|---|---|
| 100 | 1,67 s | 23,4 W |
| 80 | 1,65 s | 21,1 W |
| 70 | 1,77 s | 20,6 W |
| 60 | 1,70 s | 20,0 W |
| 50 | 1,88 s | 19,7 W |
| turbo kapalı | 2,16 s | 16,8 W |

Güç sınırla düzenli azalır ama etkisi küçüktür (en sıkı sınırda bile yalnız
yaklaşık 4 W). %70 seçildi: sürekli güç yaklaşık %12 düşer, kısa işte kayıp
gürültü düzeyindedir; %50'de kayıp %13'e çıkar. Gerçek bir sürekli güç sınırı
(RAPL PL1) TLP ile ayarlanamaz; ayrı bir udev/acpid betiği gerekir ve şimdilik
yapılmadı. Prizdeki `max_perf` %100 kalır. Geri almak için satırı `100` yapıp
`tlp start` çalıştırmak yeter.

Son karar: pil sağlığı öncelikli — 23 Kasım 2026

Kullanıcı önceliği "pil sağlığı ön planda" olarak netleştirdi; bu yüzden pil
modu yukarıdaki turbo ve `max_perf` denemelerinden önceki muhafazakâr ayara
döndürüldü, yalnız EPP bir basamak yükseltilmiş kaldı. Geçerli pil ayarları:
`CPU_ENERGY_PERF_POLICY_ON_BAT=balance_power`, `CPU_BOOST_ON_BAT=0`,
`CPU_MAX_PERF_ON_BAT=100`, profil `quiet`, HWP dinamik artırma kapalı. Ölçülen
karşılığı (tablolardaki "turbo kapalı" satırı): görev 2,0-2,2 s, tam yükte
yaklaşık 17 W. Eski `power` ayarına göre görev biraz hızlıdır, güç aynıdır.
Prizdeki ayar (`performance`, turbo açık) değişmedi. Şarj üst sınırı %80 olarak
kalır; pil sağlığı için en etkili ayar odur (CPU ayarları hücre ömrünü
anlamlı biçimde etkilemez: 24 W, yaklaşık 64 Wh'lik pil için ~0,4C'dir).
Daha da uzun hücre ömrü isteniyorsa `STOP_CHARGE_THRESH_BAT0` %70 ya da %60
yapılabilir; bedeli pilde kullanılabilir süredir. Hızlı denemek için pil
ayarındaki turbo tek satırla açılır: `CPU_BOOST_ON_BAT=1`.

## Arduino IDE 2 ve ESP32 kartları — 23 Kasım 2026

- Arduino IDE 2.3.11 apt ile gelmez (Devuan'da yalnız 1.8.19 var). Resmî ZIP
  `~/.local/opt/arduino-ide-<sürüm>` altındadır, `~/.local/bin/arduino-ide`
  bağlantısı ve kullanıcı menü girdisi vardır. Güncelleme: yeni ZIP'i yan
  klasöre açıp bağlantıyı değiştirmek. Kaldırma: bu dizin, bağlantı, `.desktop`
  ve simge ile verisi (`~/.arduino15`, `~/.arduinoIDE`, `~/.config/Arduino IDE`).
- Seri port erişimi `dialout` üyeliğiyle gelir (CH340, CP210x, FTDI, cdc-acm
  sürücüleri çekirdekte). USB programlayıcı kuralları için `avrdude` paketi
  kurulu tutulur: `60-avrdude.rules` yalnız onun içinde. IDE kendi avrdude'unu
  `~/.arduino15` içinden kullanır, sistemdekini değil.
- ESP32: IDE'nin `arduino-cli`'sine Espressif dizini eklendi
  (`~/.arduinoIDE/arduino-cli.yaml`); `esp32:esp32` (S2, S3, C3, C6, H2, P4 dahil
  çip ailesi) ve Nano ESP32 için `arduino:esp32` kuruldu. Sonraki çekirdek
  güncellemeleri IDE'nin Boards Manager'ından yapılır. Nano ESP32 çekirdeği
  Python `esptool` kullandığı için `python3-serial` paketi gerekir.
- `runtime/etc/udev/rules.d/71-esp32-usb.rules`: yerleşik USB'li kartların
  (Espressif 303a, Nano ESP32 2341:0070/0470) yükleme kipinde `uaccess` ile
  kullanıcıya açılması. Sahte seri köprüler zaten `dialout` ile çalışır.
- ESP8266 çekirdeği (`esp8266:esp8266`) de aynı `arduino-cli.yaml` dizinleriyle kuruldu;
  CH340/CP210x köprüleri `dialout` ile çalıştığı için ek kural gerekmedi.

## Yerel posta sunucusu ve popularity-contest kaldırıldı — 23 Kasım 2026

- `exim4-base`, `exim4-config`, `exim4-daemon-light`, `bsd-mailx` ve
  `popularity-contest` purge edildi; artık gereksiz kalan altı kütüphane
  (`libgnutls-dane0t64`, `libunbound8`, `libevent-2.1-7t64`, `liblockfile1`,
  `liblockfile-bin`, `libnsl2`), `Debian-exim` kullanıcısı, `/etc/aliases`,
  `/etc/mailname` ve `/var/mail/mail` da silindi. 25. port artık kapalıdır.
- Neden: `popularity-contest` yapılandırma dosyası silindiği için her gün
  `run-parts ... return code 2` ile başarısız oluyor ve root'a mail atıyordu;
  kutuda 115 mail birikmişti (69'u sudo'nun yanlış parola bildirimi, 28'i
  anacron, 17'si cron hatası). Mail okuyan kimse yoktu.
- `/etc/sudoers.d/90-no-mail` (`Defaults !mail_badpass`) depoda dosya olarak
  tutulmaz (sudoers `0440` ister, derleme `0755` hazırlar); kurulum komutu
  `docs/RESTORE.md` içindedir. Posta sunucusu yokken sudo'nun
  yanlış parolada `sendmail` çalıştıramadığına dair hata vermesini engeller;
  başarısız denemeler zaten günlüklere düşer. Cron çıktısı artık teslim edilmez,
  "No MTA installed, discarding output" notuyla atılır.
