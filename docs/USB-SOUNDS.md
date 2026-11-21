# USB bağlantı sesleri — 25 Ekim 2026

`runtime/usr/local/bin/skynet-usb-sounds`, DWM kullanıcısı olarak USB olaylarını
dinler. `skynet-session` yardımcıyı arka planda başlatır; pencere yöneticisinin
açılışını bekletmez. Ayrıca mevcut açık oturumda başlatılabilir.

| Olay | Kullanıcının ses dosyası |
| --- | --- |
| USB cihazı takılması | `~/customsounds/Usbdeviceconnected.mp3` |
| USB cihazı çıkarılması | `~/customsounds/Usbdevicedisconnected.mp3` |

Sesler belirtilen yerlerinden okunur; kaynak dosyalar dönüştürülmez, kopyalanmaz
ve depoya eklenmez. Geri yüklemede bu iki dosya ayrıca sağlanmalıdır. Dizin
`--sounds-dir` ile değiştirilebilir. Python 3, Linux pidfd desteği, udevadm, mpv
ve kullanıcının PulseAudio uyumlu ses sunucusu gerekir; bu makinede zaten vardı.

## Davranış

- Yalnız `usb/usb_device` için udev tarafından tamamlanmış add/remove olayları
  dinlenir. Arayüz, disk bölümü, bind/change ve yazılımsal çıkarma olayları
  ayrı ses oluşturmaz.
- Başlangıçta zaten bağlı cihazlar sessizce kaydedilir; sonradan çıkarılmaları
  algılanır. Root hub'lar ve sysfs'te `removable=fixed` olan dahili kamera,
  Bluetooth, parmak izi okuyucusu gibi aygıtlar dışarıda tutulur. Donanımın bu
  bilgiyi doğru bildirmesine bağlıdır; unknown harici portlar kabul edilir.
- Aynı cihazın tekrarlanan olayları atlanır. Hub'ın aynı yöndeki 400 ms içindeki
  olayları tek sesle bildirilir. Yeni olay sesi önceki sesi kesebilir; uzun
  ses kuyrukları oluşmaz.
- Çıkarma sesi 1,5 sn bekletilir. Aynı üretici/ürün kimliği (bcdDevice hariç)
  bu sürede geri gelirse ne çıkarma ne ikinci takma sesi çalınır. Neden: TP-Link
  Archer T3U (2357:0138, rtw88_8822bu) takılınca önce USB 2 olarak bağlanıyor,
  sürücü onu USB 3 kipine geçirince kopup 0,5 sn sonra SuperSpeed veriyolunda
  tekrar geliyor (21 Kasım 2026 14:58:01–02). Eskiden bu "tak–çıkar–tak" üç
  ses olarak duyuluyordu. Gevşek temasta oluşan kısa kopmalar da aynı şekilde
  tek ses olur. Gerçek çıkarmanın sesi 1,5 sn gecikmeli gelir; takma sesi
  bekletilmez.
- mpv yalnız ses çalarken çalışır. Kullanıcının mpv ayarları ve betikleri
  yüklenmez; pencere açılmaz, oynatma geçmişi tutulmaz, ekran kilidi engellenmez.
  Ses örneğine -6 dB azaltma uygulanır; sistem sesi ve mikrofon ayarları
  değiştirilmez. Varsayılan ses çıkışını ve onun mute durumunu kullanır.
- Başlangıçtaki yakın sessizlik oynatılırken atlanır; MP3 dosyaları korunur.
  İlk sesin önünde 10 ms pay bırakılır, ses içindeki duraklamalar ve sonu
  kesilmez. Kısa efektler için mpv/Pulse tampon hedefi 50 ms'dir. USB olay
  seçimi ve 400 ms tekrarlı olay bastırma değişmemiştir; bu bastırma ilk
  olayı bekletmez. Ölçümler [AUDIO-FEEDBACK.md](AUDIO-FEEDBACK.md) içindedir.
- Yardımcı ve udevadm olay bekleyerek uyur; periyodik cihaz taraması yapılmaz.
  Kullanıcının özel runtime dizinindeki kilit ikinci kopyayı engeller. Bu boş
  kilit dosyası çalışan mekanizmanın parçasıdır, kurulum artığı değildir.
  Oturum süreci çıkınca veya yardımcı sonlandırılınca oynatıcı ve dinleyici
  kapatılıp beklenir. Root olarak çalışan ses servisi veya yeni udev kuralı yoktur.

## Kontrol ve kaldırma

Sesleri cihazı çıkarmadan ayrı ayrı dinlemek için:

```sh
skynet-usb-sounds --preview add
skynet-usb-sounds --preview remove
```

Kaldırmak için `/usr/local/bin/skynet-session` içindeki
`start skynet-usb-sounds --session-pid "$$"` satırını ve kurulu
`/usr/local/bin/skynet-usb-sounds` dosyasını kaldır. Açık oturumdaki yardımcıya
SIGTERM gönderilebilir; D-Bus veya masaüstünü yeniden başlatmak gerekmez.
Kullanıcının ses dosyaları korunur.

Davranış testleri: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_usb_sounds.py -v`.
Canlı oturumda iki dosyanın çalınması, ses/mikrofon seviyelerinin ve mute
durumlarının korunması, tek kopya ve oturum bitişi temizliği doğrulandı.
İki saniyelik boşta ölçümde yardımcı ve udevadm toplam CPU tick artışı sıfırdı;
bu uzun süreli pil testi değildir. Fiziksel USB takıp çıkarma kullanıcı
tarafından ayrıca kontrol edilmelidir; ağ adaptörü zorla yeniden bağlanmadı.

Başvuru: [udevadm monitor](https://www.freedesktop.org/software/systemd/man/latest/udevadm.html#udevadm%20monitor%20%5Boptions%E2%80%A6%5D),
[mpv seçenekleri](https://mpv.io/manual/stable/).
