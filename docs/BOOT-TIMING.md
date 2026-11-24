# SysVinit açılış incelemesi — 12 Kasım 2026

Kullanıcı güvenlik özelliklerini koruyarak açılışı hızlandırmayı istedi.
Çalışan sistemde SysVinit, startpar, bağımlılık dosyaları, init betikleri,
çekirdek komut satırı, iki açılış günlüğü ve mevcut süreç başlangıç zamanları
salt okunur incelendi. Ölçümlerde anlamlı ek kazanç sağlayacak doğrulanmış
bir yapılandırma sorunu bulunmadı; **üretim ayarı değiştirilmedi**.

## Son açılış ölçümleri

Süreler kernel açılışından itibaren saniyedir; BIOS/UEFI ve GRUB beklemesini
kapsamaz. Çekirdek `6.12.116+deb13-amd64`.

| Aşama | Saniye | Kaynak |
| --- | ---: | --- |
| Initramfs /init başlatıldı | 1,109 | dmesg |
| Kök ext4 dosya sistemi salt okunur bağlandı | 2,978 | dmesg |
| Ana sistem eudev süreci | 3,19 | /proc/PID/stat |
| Kök dosya sistemi yazılabilir yeniden bağlandı | 4,160 | dmesg |
| rsyslog | 5,56 | /proc/PID/stat |
| D-Bus | 5,59 | /proc/PID/stat |
| greetd | 5,61 | /proc/PID/stat |
| NetworkManager | 6,01 | /proc/PID/stat |

`greetd` başlangıcı, grafik giriş ekranının ilk çizildiği an değildir.
Ekranın görünür olma anı bu incelemede ölçülmedi. Kullanıcının parolasını
girmesine kadar geçen süre boot gecikmesi olarak sayılmadı. Oturum betiği
ve DWM başlatma kayıtları aynı saniyede; bu saniye çözünürlüklü kayıt kesin
bir alt-saniye süre ölçümü değildir.

## Mevcut optimizasyonlar ve korunan davranış

- `/etc/init.d/rc` zaten `CONCURRENCY=makefile` kullanıyor; üç bağımlılık
  dosyası mevcut, legacy boot işareti ve `concurrency=none` parametresi yok.
  Boot günlüğü paralel runlevel 2 başlangıcını doğruluyor.
- Greetd yalnız gerekli bağımlılıkları bekliyor; bütün masaüstü/ağ
  yardımcılarının tamamlanmasına bağlı değil. NetworkManager giriş
  yöneticisinden sonra başlamış; Wi-Fi bağlantısını bekletme söz konusu değil.
- GRUB override menü süresi 3 saniye; önceki kullanıcı tercihi korundu.
- Initramfs zaten zstd kullanıyor. Güvenli donanım kapsaması için MODULES=most
  korundu; initramfs yeniden üretilmedi ve sürücü çıkarılmadı.
- AppArmor, güvenlik duvarı sıralaması, dosya sistemi kontrolleri, çekirdek
  güvenlik parametreleri, PAM, şifreli keyring ve parola doğrulaması korunuyor.
- Udev settle beklemesi kısaltılmadı; USB aygıtlarının hazır olmadan diğer
  servislerin başlaması riski oluşturulmadı. Yazıcı/tarayıcı, Bluetooth,
  ses ve TLP servisleri kapatılmadı.

GPU firmware başlangıcında yaklaşık 585 ms GuC ve 51 ms HuC uyarısı var;
sonraki satırlar başarılı başlatma/doğrulamayı gösteriyor. Bu donanım
başlatma maliyeti için firmware doğrulaması veya GPU özellikleri kapatılmadı.
Bilinen UCSI `PPM init failed` mesajı 11,60. saniyede; tek başına bu mesajın
zamanından SysVinit'in aynı süre boyunca beklediği sonucu çıkarılamaz.
Greetd süreci bu mesajdan önce başlamış. USB-C önceki kapsam dışında kaldı.

Bu inceleme bir önce/sonra hızlanma testi değildir. Sistemi değiştirmeden
mevcut hızın iyi olduğu ve güvenli ek kazanç için kanıt bulunmadığı kaydedildi.
Özel günlükler kamuya açık depoya eklenmedi; geçici günlük okuma yardımcıları
ve ham günlük kopyaları temizlendi.
