# Birlikte çalışma denetimi — 28 Ekim 2026

## Güncelleme — 19 Kasım 2026

Aşağıdaki **NVMe** bulgusunun nedeni, yamalı VMD sürücüsünün 6.12.116/117'ye
taşınmamasıydı. Düzeltme DKMS paketi olarak kuruldu; ayrıntılar
`NVME-VMD.md` belgesinde. Bu inceleme sırasında:
- Polkit MATE ajanının çalıştığı görüldü.
- Kilit PAM'ındaki `pam_unix(...:account): setuid failed` kaydının başarılı
  açılışlardan sonra yazıldığı ve Debian `common-auth` hizmetinde de çıktığı
  görüldü. Zararsız kayıt olarak değerlendirildi; değiştirilmedi.
- USB-C `ucsi` hatası değişmedi.

## Güncel denetim — 12 Kasım 2026

**Aynı gün Polkit düzeltmesi:** Aşağıdaki denetimde bulunan yanlış KDE ajan
başlangıcı düzeltildi. Yerel MATE ajanı çalışıyor; normal `pkexec`
yetkilendirmesiyle autostart kuruldu. PAM dosyaları değişmedi. Başlangıç
bloğunun iki kez tekrarında aynı tek ajan korundu. Dört yeni başlangıç testi
geçti; ayrıntılar `AUTOSTART.md` içinde. Aşağıdaki NVMe ve USB-C bulgularının
durumunda bu işlemle değişiklik olmadı.

6.12.116+deb13-amd64 / SysVinit oturumunda salt okunur genel inceleme yapıldı.
Bu bölüm aşağıdaki tarihsel sonuçların güncel karşılığıdır; üretim ayarı,
sürücü, servis veya oturum değiştirilmedi.

### Açık bulgular

- **Polkit grafik ajanı:** canlı `/etc/dwm/autostart.sh`, kurulu olmayan
  `polkit-kde-agent-1` paketinin ikilisini hedefliyor. Dosya bulunmadığından
  `-x` kontrolü başlatmayı atlıyor. Dağıtımın ve yerel yamalı MATE ajanının
  dosyaları mevcut, ancak oturumda çalışan grafik Polkit ajanı yok. Polkit
  authority çalışıyor; terminalde normal parola doğrulaması mümkün. Bu,
  grafik yetkilendirme pencerelerinin açılmasını etkileyen gerçek bir
  başlangıç yapılandırması hatasıdır; bu incelemede düzeltilmedi.
- **NVMe:** bu boot'un 443,291934. saniyesinde bir
  `I/O tag 98 (9062) QID 2 timeout, completion polled` kaydı var. SMART
  başarılı, critical_warning/media_errors/num_err_log_entries sıfır, disk
  sıcaklığı 39 °C. Sağlık sayaçları temiz olsa da timeout kaydı çözülmüş
  sayılmaz. Çalışan VMD sürümü `0.6`, modül yolu 6.12.116 dağıtım paketine
  ait; 6.12.115 için derlenen yerel etiketli modül etkin değil. Bu bilgi
  tek başına timeout'un kesin sebebini veya paketli sürücünün içerdiği
  upstream düzeltmeleri kanıtlamaz. Eski özel GRUB yedeğinin kaldırılması
  çalışan sürücüyü değiştirmedi.
- **USB-C:** `ucsi_acpi ... error -ETIMEDOUT: PPM init failed` ve oturum
  yardımcısında eksik port kayıtları devam ediyor. Önceki kullanıcı kapsamı
  dışında bırakılan bu alan değiştirilmedi.
- Grafik greeterin xdg_surface/keymap/kapanış mesajları, TP-Link başlangıç
  USB `-71` kayıtları, Logitech HID++ 0x08 ve uygulama kaynaklı bildirimler
  mevcut. TP-Link ve dahili Wi-Fi bu denetimde bağlı; bu başlangıç
  kayıtlarından sürekli bağlantı arızası sonucu çıkarılmadı. Ferdium'un
  SNI özelliği okuma hatasında snixembed kayıtlı simgeyi koruyor; tepsi
  süreci çalışıyor. Tarayıcı kaynaklarının ağ/JavaScript hata satırları
  bütün işletim sisteminin bozulduğu şeklinde değerlendirilmedi.

### Çalışan ve doğrulanan alanlar

- Greetd, D-Bus, elogind, NetworkManager, Bluetooth, rsyslog, cron, TLP ve
  CUPS durum kontrolleri başarılı. Masaüstü yardımcıları tek örnek; ikinci
  bir ses sunucusu görülmedi. `dpkg --audit`, bağımlılık denetimi ve depo
  bütünlük kontrolleri başarılı.
- Yaklaşık 9,5 GiB RAM kullanılabilir; 4 GiB ZRAM + 11 GiB disk swap etkin,
  kullanımı sıfır. Örnekleme anında CPU/bellek/I/O baskısı sıfır. Bunlar
  anlık ölçümlerdir; geçmiş NVMe timeout'unu geçersiz kılmaz.
- Greetd parola yığını ve kilidin ayrı parmak izi/parola yığını korunuyor.
  Resume `0:0`; varsayılan PDF/video/ses/görüntü uygulamaları istenenlerle
  eşleşiyor. TP-Link ve mute LED DKMS modülleri çalışan çekirdek için kurulu.
- SpoofDPI yalnız 127.0.0.1:9080'de dinliyor. Güvenlik duvarı etkin; mevcut
  politikası yerel ağ kaynaklarına izin veriyor. AppArmor etkin; profiller
  14 enforce, 25 complain, 77 unconfined modunda. Etkin olması bütün
  programların tam kısıtlandığı şeklinde yorumlanmadı; modlar değiştirilmedi.
- Ana test kümesinde 81 testten 71'i geçti, özel ekran/D-Bus isteyen 10'u
  atlandı. Ses durumu kümesindeki 18 test de geçti: **89 başarılı test**.
  Bu sonuç canlı başlangıç betiğindeki yanlış ajan yolunu kapsayan bir
  uçtan uca masaüstü testi değildir.

Gerçek kilitle/aç, parmak okutma, kamera kaydı, Bluetooth eşleştirme, fiziksel
USB çıkar/tak veya yeniden boot yapılmadı. Bu denetim kapsamlı güvenlik/açık
taraması değildir. Yeni hata yokluğu veya tüm fiziksel özelliklerin koşulsuz
uyumu iddia edilmez. Testler geçici kaynakları kullandı ve temizledi.

## Güncel denetim — 3 Kasım 2026, akşam

SpoofDPI ve parmak izi sonuç paneli değişikliklerinden sonra canlı oturum
salt okunur yeniden incelendi. Bu denetimde üretim ayarı değiştirilmedi,
ağ/ses/oturum yeniden başlatılmadı; gerçek kilit veya sensör testi yapılmadı.
Aşağıdaki 28 Ekim tablosu tarihsel örnektir; özellikle AFK/greetd politikası
artık aşağıdaki güncel durumla değerlendirilmelidir.

- SysVinit PID 1, çekirdek `6.12.115+deb13.1-amd64`. Oturum yardımcıları
  tek örnek; PulseAudio yanında ikinci PipeWire/WirePlumber sunucusu yok.
- SpoofDPI özel DoH/IPv4/first-byte argümanlarıyla yalnız 127.0.0.1:9080
  dinliyor. Kurulu başlangıç yardımcısı ve autostart dosyasının hashleri
  son kurulum kaydıyla eşleşiyor. Ağ beklemeli gerçek yeniden açılış henüz
  denenmedi; önceki adımda canlı HTTPS/tek örnek testleri geçti.
- Greetd parola ile giriş; ayrı kilit PAM yığını parmak izi (3 deneme/10 s)
  ardından parola. Yeni auth arayüzü ve korunan yedi doğrulama/başlatıcı
  dosyası son kayıtla eşleşiyor. XSecureLock paket sürümü 1.9.0-1.
- AFK kilidi kapalı (`xset` timeout 0, DPMS disabled); güç tuşu/kapak
  elogind lock eylemine bağlı. Uyku ve hibernasyon kapalı, resume 0:0.
- Pil modunda EPP power/platform quiet, şarj üst sınırı 80. 11 GiB disk
  swap + 4 GiB ZRAM; swap kullanımı sıfır. Yaklaşık 8.6 GiB RAM kullanılabilir,
  kök dosya sisteminde yaklaşık 410 GiB boş alan var. Değerler anlık örnektir.
- Ses sunucusu ve kalıcı durum/LED yardımcıları çalışıyor. Duvar kâğıdı
  VAAPI kullanıyor, ses izi kapalı (`aid=false`), örtülü örnekte duraklatılmış.
- TP-Link ve mute LED DKMS modülleri hem 113 hem 115 çekirdeği için kurulu.
  Wi-Fi/Bluetooth rfkill engeli yok. Bluetooth eşleşme/bağlantı testi yapılmadı.
- `dpkg --audit` temiz, `apt-get -s check` başarılı. Depo bütünlük ve
  `git diff --check` kontrolleri geçti.

### Test kapsamı ve açık gözlemler

Depoda 63 test metodu var: normal çalışmada 52 geçti, özel X11 gerektiren
6 metot atlandı; 5 greetd protokol testi sınıfı sandbox Unix soketi sınırı
nedeniyle ilk çalışmada atlandı ve ardından özel soketle tamamı geçti.
Ses durumu için ayrıca 18 test geçti. Toplam **75 başarılı test**, bu
denetimde yeniden çalıştırılmayan **6 özel X11 testi** vardır. İlk unittest
çıktısındaki `skipped=7`, sınıf seviyesindeki bu soket atlamasını da sayar.
Testler kendi geçici dosyalarını temizledi; bytecode üretimi kapalıydı.

Mevcut oturum günlüğünde snixembed tepsi köprüsünün yinelenen D-Bus Get
uyarıları sürüyor; süreç çalışıyor olsa da bu alan tamamen hatasız sayılmadı.
Önceki root denetiminde USB-C UCSI zaman aşımı ve tek NVMe
`timeout, completion polled` kaydı vardı; o denetimde SMART temizdi.
Kernel günlüğü bu salt okunur kullanıcı denetiminde izin gerektirdiğinden
tekrar okunmadı; bu eski kayıtların giderildiği veya tekrarlamadığı iddia
edilmez. Gerçek reboot, Bluetooth bağlantısı ve tüm fiziksel işlevlerin
uçtan uca testi yapılmadan koşulsuz uyumluluk garantisi verilmez.


Mevcut Devuan 6 / SysVinit / elogind / DWM oturumu incelendi. Denetlenen
özellikler arasında çalışma çakışması bulunmadı. Üretim ayarları değiştirilmedi;
oturum, ses sunucusu, ağ veya gerçek kilit yeniden başlatılmadı.

## Canlı oturum bulguları

| Alan | Doğrulanan durum |
| --- | --- |
| Oturum ve başlangıç | DWM, slstatus, Dunst, xss-lock, xsettingsd, xwinwrap, USB sesi ve ses LED yardımcısı tek kopya. Çalışan DWM/slstatus/xwinwrap kurulu güncel ikililerle aynı. XFCE oturumu veya ikinci ses sunucusu görülmedi. |
| Giriş ve kilit | Greetd 0.10.3, gtkgreet 0.8-1+b1 ve XSecureLock 1.9.0-1 mevcut sürüm korumalarıyla uyumlu. Kilit seçicisi güncel özel kilidi seçiyor. Otomatik kilit 300 saniye; güç tuşu/kapak aynı kilit politikasına bağlı. |
| Parmak izi | Aygıt D-Bus üzerinden erişilebilir; yalnız `right-index-finger` kaydı var. PAM parmak izi için üç deneme/10 saniye kullanıyor ve parola yolu mevcut. Bu denetimde gerçek parmak okutulmadı. |
| Duvar kâğıdı | Kaynak GIF mevcut; mpv VAAPI kullanıyor, sesi kapalı ve ekran koruyucu engellemesi yok. Tam örtülü canlı duvar kâğıdı duraklamış. Özel ekranda örtülme/kısmi görünürlük ve süreç kapanışı test edildi. |
| Ses ve mikrofon | Tek PulseAudio 17 sunucusu var. Kayıtlı mute/seviye bilgileri canlı varsayılan aygıtlarla eşleşiyor. Örnekte hoparlör %45 ve mute, mikrofon %100 ve mute; iki LED de 1. Bu kullanıcı durumu değiştirilmedi. |
| Bildirim ve USB sesleri | Dunst etkin ve duraklatılmamış. Dört MP3 dosyası mevcut ve ffprobe ile geçerli ses akışı olarak okunuyor. Ses/parlaklık OSD'sinin ayrıca bildirim sesi üretmesini engelleyen kurallar/yardımcılar mevcut. USB olay birleştirme ve ses tuşu kilit davranışları testleri geçti. |
| Pil ve güç | Pil örneğinde ADP1=0, Discharging; TLP power/quiet, turbo kapalı. Şarj üst sınırı %80. Pil verisinin bağlı bekleme/şarj ayrımı ve geçersiz değerleri ilgili kaynak testleriyle doğrulandı. |
| Uyku, parlaklık ve swap | Elogind CanSuspend/CanHibernate `no`; resume 0:0. Parlaklık kaydetme hizmeti ve kayıt dosyası mevcut. 4 GiB ZRAM + disk swap ile kullanılabilir toplam 15 GiB, ZRAM önceliği 100. |
| GTK ve imleç | Canlı GTK sorgusu SKYNET-Black-Red, breeze-dark, JetBrains Mono ve Skynet imlecini döndürüyor. GTK 3/4 ve xsettingsd aynı temaya işaret ediyor. |
| VLC ve qimgv | VLC başlatıcısı geçerli ve qt5ct seçimi yalnız VLC'ye özgü. qimgv kendi özel temasını kullanıyor; tema dosyası kayıtlı kaynakla aynı. |
| Varsayılan uygulamalar | PDF → Zathura; video ve ses → VLC; JPEG/PNG/GIF → qimgv. |
| VS Code ve ağ | 69 arayüz renk ayarı, `chat.disableAIFeatures=true`; `editor.tokenColorCustomizations` girdisi yok. Ayarlı yerel SpoofDPI proxy'si üzerinden Marketplace eklenti sayfası ve eklenti manifesti GET ile HTTP 200 verdi; TLS doğrulama sonucu 0. Eklenti kurulmadı. |
| Bluetooth ve sistem tepsisi | Adaptör açık, Blueman applet/tray ve snixembed çalışıyor. Blueman'ın SNI eklentisi kapalı; mevcut XEmbed yolu korunuyor. |
| Anahtarlık ve Spotify | Anahtarlık servisi var, D-Bus kimlik politikası FIXED. Spotify kurulu; kullanıcıya özel parola deposunu atlayan başlatıcı bulunmuyor. Hesap oturumu veya anahtarlık içeriği okunmadı. |
| Ferdium | Kullanıcı autostart girdisi yok; DWM başlangıç betiğinde otomatik başlatılmıyor. |
| Kitty ve Fastfetch | Kurulu kullanıcı başlatıcıları ve ayrıntılı ASCII dosyaları kaynaklarla aynı. Fastfetch döngüsü, sabit yazılar, oran ve açık argüman/boru davranışı testleri geçti. |
| Temel güvenlik ve bütünlük | X erişim denetimi açık, AppArmor çekirdek bayrağı Y. 27 korunan PAM, kilit, giriş, oturum, güç ve sistem yapılandırması denetim öncesi/sonrası aynı. Bu bir kapsamlı güvenlik veya açık taraması değildir. |

## Test sonuçları

- Normal masaüstü test çalıştırması: 33 başarılı test; özel ekran testleri ve
  Unix soketi gerektiren sınıf ilk sandbox çalıştırmasında atlandı.
- Greetd protokolü: özel sahte Unix soketinde 5 test geçti; gerçek kimlik
  bilgileri kullanılmadı.
- Kurulu xwinwrap: ana masaüstüne gösterilmeyen, özel yetkilendirilmiş
  Xephyr ekranında 5 test geçti; ses kapalı test videosu kullanıldı.
- Ses durumu saklama: 18 test geçti.
- Toplam: **61 farklı başarılı test**. Atlanan ilgili testler yukarıdaki
  ayrı ortamlarda tamamlandı.
- `dpkg --audit`, bağımlılık kontrolünün simülasyonu, depo bütünlük ve
  `git diff --check` kontrolleri geçti. Paket kurulmadı/yükseltilmedi.

Marketplace sunucuları ilk HEAD denemesinde 404/405 döndürdü. Gerçek GET
istekleri 200 verdi; bu HEAD davranışı sertifika/proxy arızası sayılmadı.

## Bu denetimin sınırları

Gerçek parmak izi doğrulaması, kilitleyip yeniden açma, bilgisayarı kapatma,
adaptörü takıp çıkarma, hoparlörden ses dinleme ve Spotify hesabının yeniden
açılıştaki kalıcılığı denenmedi. TP-Link ağ adaptörü bağlı görünmedi; dahili
iwlwifi bağlantısı açıktı. Anahtarlığın parmak izi girişinden sonra parola
istemesi, şifreli anahtarlık tasarımının mevcut sınırıdır; parola koruması
atlatılmadı. USB-C önceki kullanıcı tercihi doğrultusunda değiştirilmedi
ve bu denetimde giderilmiş sayılmadı.

Bu sonuç kontrol edilen kurulum ve örneklenen durumlar için geçerlidir;
her donanım/uygulama sürümünde tüm davranışların garantisi değildir.
Geçici test ekranı, test süreçleri ve çalışma dosyaları temizlendi.
