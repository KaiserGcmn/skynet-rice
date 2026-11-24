# Oturum ve açılış hataları — 2026-11-05

**11 Kasım güncellemesi:** Kitty uyumluluk yamaları artık APT ile yönetilen
`0.41.1-2+deb13u2+skynet1` paketinde. Ayrı 0.50.0 kurulumu hakkındaki aşağıdaki
notlar önceki durumu anlatır. Güncel kurulum ve sınırlar [KITTY.md](KITTY.md).

## Uygulanan düzeltmeler

1. **Polkit / dwm:** MATE aracının bulunmayan GNOME SessionManager servisine
   kayıt isteği ve boş `DESKTOP_AUTOSTART_ID` kaynaklı GLib assertion giderildi.
   Kaynak `sources/mate-polkit-hud/`; isteğe bağlı oturum kaydı servis varsa
   yapılır. Sistem Polkit kaydı ve parola denetimi aynı kalır. Yeni araç
   `/usr/local/libexec/` altında; dağıtımın `/usr/libexec/` kopyası korunur.
   Autostart yerel sürümü seçer, bulunamazsa dağıtım kopyasına döner.
2. **Kitty / SysVinit:** systemd bulunmayan sistemde scope oluşturma isteği
   yapılmaz. Yeni bağımsız Kitty penceresiyle doğrulandı. Zaten açık Kitty
   süreçleri eski Python kodunu bellekte tutabilir; kapatılıp yeniden
   açıldığında yeni kontrol kullanılır. Tema/render ayarları değiştirilmedi.
3. **Bluetooth OBEX:** kullanıcı telefon rehberi eşitlemesini kullanmadığını
   açıkladı. Kullanıcı D-Bus servis tanımında yalnız `pbap,irmc` sunucu
   eklentileri kapatıldı. Eksik Evolution adres defteri servisine yapılan
   istekler kesildi; dosya aktarım istemcisi ve `CreateSession` arayüzü mevcut.
   Bluetooth daemon'ı, eşleştirmeler, kulaklık/fare/klavye bağlantıları
   değiştirilmedi. Evolution paketleri kurulmadı.
4. **saned:** IPv6 soketinin zaten IPv4 de kabul ettiği durumda ikinci IPv4
   bind denemesinin çakışması giderildi. Tek çift protokollü soket kullanılır;
   IPv6 kapalı/yalnız IPv6 ayarında önceki davranış korunur. Tarayıcı ACL ve
   yetkileri aynı. Geçici portta iki protokol de test edildi; canlı servis
   yeniden başlatılmadı, yeni seçenekler sonraki başlangıçta uygulanır.
5. **zram açılış kaydı:** `/dev/log` oluşmadan logger çağırmak yerine mevcut
   konsol mesajı yolu kullanılır. Hatalar hâlâ görünürdür. Swap ayarları aynı;
   erken açılış davranışının uçtan uca kontrolü sonraki boot'ta yapılabilir.
6. **greetd status:** servis betiğinde olmayan `status` işlemi eklendi;
   artık çalışan servis için doğru sonuç döner. Login servisi yeniden
   başlatılmadı; PAM ve parmak izi akışı değiştirilmedi.

## Doğrulama

- Üç özel D-Bus testi geçti: GNOME yöneticisi yokken, yönetici var ama startup
  kimliği yokken ve startup kimliği varken. Gerçek sistem Polkit authority'si
  testlerde kullanılmadı. Komut: `SKYNET_DBUS_TESTS=1 python3 -m unittest discover
  -s tests -p test_polkit_session.py -v` (GTK/Polkit geliştirme başlıkları gerekir).
- Yeni Polkit aracı aynı elogind oturumunda etkinleştirildi; başlangıç günlüğü
  boş, kayıt hatası yok. Ardından gerçek `pkexec` salt okunur kontrolü UID 0
  ile tamamlandı. Yetki/PAM kuralları değiştirilmedi.
- OBEX yeniden başlatılmadan önce aktif transfer olmadığı kontrol edildi.
  Yeni süreç doğru eklenti seçenekleriyle başladı; sonraki syslog'da eksik
  Evolution registry hatası yok. Gerçek telefona aktarım yapılmadı.
- Dört home restore ve beş SpoofDPI regresyon testi geçti. Shell/Python sözdizimi,
  kurulu dosya hash'leri ve korunan PAM/TLP/VMD/initramfs dosyaları doğrulandı.
- İlk incelenen boot'ta 12230 saniye boyunca NVMe timeout/reset/I/O hatası yoktu.
  Çalışma sırasında yeni boot saptandı; son kontrolde 376.95 saniyelik bu boot'ta
  da yamalı VMD etkin ve aynı hatalar yok. Bunlar farklı açılışların ölçümleridir.

## Kalan kayıtların anlamı ve sınırlar

- Intel Wi-Fi önce bulunmayan API 93 firmware'ini arıyor, ardından API 92
  `92.7541f516.0` ve PNVM başarıyla yükleniyor. Daha yeni firmware dosyasının
  adını eski sürüm gibi değiştirmek veya rastgele symlink kurmak uygulanmadı.
- Cirrus iki kanalda önce özel varyantları arıyor; ardından cihazın ortak
  `.wmfw` ve ayrı sol/sağ `.bin` dosyaları yükleniyor. İki kanalda firmware
  yükleme, hoparlör koruması ve kalibrasyon günlükte doğrulandı.
- TP-Link `0xc4` / `0x4e0`, `-71` kayıtları USB2 aygıtının ilk başlangıcında;
  ardından USB3 olarak yeniden enumerate olup arayüzü açılıyor. Kaynakta
  `0xc4=REG_PAD_CTRL2` USB mod geçişinde kullanılıyor; zamanlama bu geçişle
  ilişkili olduğunu düşündürüyor. Adaptör son kontrolde USB 5000 Mbps ve
  link `up`. Mesajların sebebi kesin çözüldü denmedi; hız/USB3 desteği kapatılmadı.
- Logitech `protocol error 0x08`, BIOS kaynak/HPET/EDAC ve yerel VMD modülüne
  ait out-of-tree/imza kayıtları kalabilir. Genel kernel parametreleriyle
  gizlenmedi ve cihaz sürücüleri gelişigüzel değiştirilmedi.
- Codex'in Kitty 0.41.1'in tanımadığı OSC 7501 ve bazı diğer terminal kodları
  hâlâ uyarı üretebilir. Bu uygulama/terminal protokol uyumu bu düzeltmede
  giderilmedi; stderr veya günlük kayıtları bastırılmadı.
- USB-C önceki kullanıcı kapsamı dışında; bu işlemde ayarı değiştirilmedi.

## Codex–Kitty ilk uyum incelemesi — 2026-11-05

**Sonraki durum:** aşağıdaki ilk denemeden sonra yerel yamalı Kitty 0.50.0
kuruldu. OSC 7501, Codex klavye sıfırlaması, 1007 ve tekrarlı 2026 komutları
testlerde uyarısız çalışıyor. Önceki “giderilmedi” kayıtları ilk incelemeye
aittir; güncel sonuç ve sınırlar [KITTY.md](KITTY.md) içindedir.

Kitty 0.41.1 ile resmi Kitty 0.50.0 x86_64 ikilisi özel, kimlik doğrulamalı
Xephyr ekranında aynı terminal komutlarıyla karşılaştırıldı. İkisi de normal
sonlandı. Test, çalışan Codex oturumuna komut göndermedi; protokol dizilerini
ayrı bir Python süreci üretti:

- `CSI > 4 ; 2 m` ve `CSI > 4 ; 0 m`: modifyOtherKeys açma/kapatma.
- `CSI ? 1007 h/l`: alternatif ekran kaydırma modu.
- `OSC 7501`: uygulama durum bildirimi.

0.50.0, 7501 için bilinmeyen OSC hatasını kaldırdı; 1007 modu desteklenmiyor.
modifyOtherKeys açma denemesinde Kitty kendi klavye protokolünü öneriyor.
Bu sentetik açma denemesi, Codex'in her başlangıçta aynı komutu gönderdiğinin
kanıtı değildir. Ayrıca resmi ikili, SysVinit'te systemd scope çağrısını
yeniden deneyip uyarı üretiyor; yerel 0.41.1 yaması bu çağrıyı önlüyor.

İncelenen güncel Codex kaynaklarında modifyOtherKeys sıfırlama ve 1007
komutları bulunuyor. Resmi yapılandırma belgelerinde bu komutları ve OSC 7501'i
birlikte, özellik kaybı olmadan engelleyen bir ayar bulunamadı. Dolayısıyla
0.50.0 günlük kullanıma alınmadı; Kitty/Codex ayarları ve ikilileri bu incelemede
değiştirilmedi. Terminal çıktısı filtrelenmedi, klavye özellikleri kapatılmadı.
Bu uyarılar çözülmüş sayılmıyor. Geçici indirme ve test dosyaları temizlendi.

Kaynaklar: [Kitty değişiklikleri](https://sw.kovidgoyal.net/kitty/changelog/),
[Codex klavye modları](https://github.com/openai/codex/blob/main/codex-rs/tui/src/tui/keyboard_modes.rs),
[alternatif ekran](https://github.com/openai/codex/blob/main/codex-rs/tui/src/tui/alternate_screen.rs).
Test edilen resmi arşivin SHA256 değeri GitHub release API digest'i ile aynı:
`f04b11775574d6aabfb529b7e734cc0a7d7d12c7df9fb8ec1843e45420e514ee`.

## Kaynak ve yeniden üretim

Polkit: [upstream MATE 1.26.1 main.c](https://github.com/mate-desktop/mate-polkit/blob/v1.26.1/src/main.c),
Debian kaynak paketi `mate-polkit_1.26.1-4`. Resmi Debian HTTPS kaynağından
alındı; arşiv hash'leri `.dsc` ile kontrol edildi. GPG imzası yerel anahtar
olmadığından doğrulanamadı; imza doğrulaması yapıldığı iddia edilmez.

- orig.tar.xz SHA256: `55f54cd4bf15293a9a1ba0de645223401b48c10aedd5f4d650a8d4bb6a27b7e8`
- debian.tar.xz SHA256: `31daefa55413802e8a4023d5fd1f5cf5721454e1e7782d8bcfb8ff06dd20d45a`

Listener, authenticator ve parola diyaloğu kaynakları byte karşılaştırmasıyla
aynı. Yalnız main.c içindeki isteğe bağlı masaüstü kaydı değiştirildi.
Dağıtım hardening bayraklarıyla derlendi; GTK'nin eski tray API'sine ait
deprecation uyarıları var. Testler ve derleme recipe'si depoda, derlenmiş
ikili/geçici paketler depoda tutulmaz. Sistem betiği yamaları ve kapsamı
`sources/sysvinit-compat/README.md` içinde. Paket güncellemeleri bu küçük
yamaları değiştirebilir; güncel sürüm incelenmeden otomatik yeniden uygulanmaz.


## Java uygulamaları dwm altında gri kalıyordu — 2026-11-23

Arduino IDE (Java/Swing) dwm altında ilk boyutunda kalıyor, pencerenin geri kalanı gri
görünüyordu. dwm pencereleri yeniden ebeveynlemez; Java bunu `_JAVA_AWT_WM_NONREPARENTING=1`
ile öğrenir. Daha önce bu değişkeni yalnız Arduino'ya özel bir başlatıcı veriyordu; paket
yeniden kurulunca (paketin kendi menü girdisi doğrudan `/usr/bin/arduino`'yu çalıştırır)
sorun geri geldi. Değişken artık `runtime/usr/local/bin/dwm-session` içinde oturum
ortamına konur, böylece her Java uygulaması (menüden, dmenu'den, `.ino` dosyasından)
doğru boyutlanır. Geçici Xephyr'de değişkensiz ve değişkenli denendi: değişkensizde
içerik küçük, çevresi gri; değişkenle pencere doluyor. Oturum betiği değişikliği bir
sonraki girişte devreye girer. Test: `tests/test_session_java_env.py`.
