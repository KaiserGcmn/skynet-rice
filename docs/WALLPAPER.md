# GIF, video ve resim arka planı

`dwm-wallpaper`, DWM altında mevcut xwinwrap ve mpv kullanır. Kurulumda
`runtime/usr/local/bin/dwm-wallpaper` dosyasını aynı yola 0755 izinleriyle
kurun ve `sources/xwinwrap` içindeki güncel xwinwrap sürümünü birlikte derleyip
kurun; yardımcı, bu sürümün `-pause-hidden` seçeneğini kullanır. `mpv` ve
`ffmpeg` paketleri `manifests/desktop-packages.txt` içindedir.
DWM autostart yeni yardımcıyı arka planda çağırır. Pencere root altında,
override-redirect ve DESKTOP türünde açılır; DWM döşemesine katılmaz,
klavye/fare girdisi veya odak almaz. mpv sesi ve ekran koruyucu engellemesi kapalıdır.

```sh
dwm-wallpaper set "$HOME/wallpapers/Skynet4.gif"
dwm-wallpaper set "$HOME/wallpapers/skynet.png"
dwm-wallpaper status
dwm-wallpaper stop
dwm-wallpaper start
```

Seçim `~/.config/dwm-desktop/wallpaper.json` içinde saklanır. Seçim bulunamazsa rice
ile gelen `~/wallpapers/skynet.png` kullanılır. Başlangıç tek örnek kilidiyle
korunur; yalnız xwinwrap ve mpv kalıcı süreçtir. Normal fotoğraflar süresiz
sabit gösterilir, GIF ve videolar döngüye alınır. Görüntü ekranı dolduracak
şekilde oranı korunarak kırpılır; kenarları siyah olan görseller ise 1:1
gösterilir (aşağıdaki 22 Kasım notu). Ekran düzeni değişirse `stop` ardından `start`
pencere boyutunu günceller.

GIF seçildiğinde FFmpeg aynı kare zamanlaması ve çözünürlükle bir HEVC 4:4:4
oynatma kopyası oluşturur; kaynak GIF değiştirilmez. `~/.cache/dwm-wallpaper/` içinde
yalnız etkin GIF'in içerik özetiyle adlandırılan MP4 tutulur; başka GIF seçilince
eskisi kaldırılır, fotoğrafa geçilince önbellek boşaltılır. Dönüşüm başarısızsa
asıl GIF doğrudan oynatılır. mpv VA-API uygun olduğunda donanım çözme kullanır,
10 nice önceliğiyle çalışır ve görüntü iyileştirme efektleri kapalıdır.

Pencereler arka planı tamamen kapatınca xwinwrap, X11 görünürlük olayına göre
mpv'yi IPC üzerinden duraklatır. Arka planın bir kısmı bile görünür olduğunda
oynatma devam eder. Ek kalıcı süreç veya düzenli kontrol zamanlayıcısı yoktur;
yalnız mpv başlangıcında soket hazır olana kadar kısa süreli tekrar denenir.
Görünür animasyonun çözünürlüğü, kare hızı ve kalitesi değişmez. Duraklamış
oynatıcı dosya değiştirme ve kapatma komutlarını almaya devam eder. Bu davranış
X11 pencere görünürlüğüne dayanır; yalnız ekranın kararması ayrı bir tetikleyici
değildir. Şeffaf/composite masaüstlerinde ayrıca doğrulama gerekir.

23 Ekim 2026 cihaz kontrolü: 1920×1200 X11/DWM oturumunda 1920×1080,
180 kare, 3,8 saniyelik GIF ve PNG arasında geçiş, kalıcı seçim, tekrar başlatmada
tek süreç ve masaüstü pencere türü doğrulandı. GIF'in 60.618 bayt H.264 kopyası
aynı kare sayısı/süreyi korudu; VA-API etkin ve kare düşmesi 0 idi. Dört saniyelik
örneklerde mpv CPU kullanımı tek çekirdek üzerinden doğrudan GIF'te %17,25,
video kopyasında %5,25 ölçüldü; bu bir pil ömrü testi değildir. Ekran görüntüsüyle
SKYNET görseli kontrol edildi. Gerçek yeniden giriş yapılmadan autostart komutu
canlı test edildi. Geçici önizleme ve kurulum dosyaları kaldırıldı.

Feh ve artık kullanılmayan `libimlib2t64`, `libid3tag0`, `yudit-common` kaldırıldı.
Eski `~/.fehbg` başlatıcısı kaldırıldı. `manifests/apt-*` ve `captured-files.json`
ilk yakalamanın tarihsel envanteri olduğu için önceki feh kayıtlarını korur.

24 Ekim 2026 kontrolünde yeni oturumun güncel komutu otomatik başlattığı
doğrulandı. Tamamen örtülü duvar kâğıdında 8 saniyelik örnekte mpv + xwinwrap
CPU kullanımı tek çekirdek üzerinden %0,00 ölçüldü; oynatma konumu sabit,
VA-API etkin kaldı. Değişiklik öncesindeki 4 saniyelik mpv örneği %7,0 idi.
Bu kısa örnekler pil ömrü veya genel sistem hızlanması ölçümü değildir.

`tests/test_wallpaper_visibility.py` ayrı bir 800×600 X11 sunucusunda beş
entegrasyon kontrolü içerir. Normal test çalıştırması bu kontrolleri atlar.
Önceden başlatılmış, kullanıcı masaüstünden ayrı bir test sunucusu için:

```sh
PYTHONDONTWRITEBYTECODE=1 \
SKYNET_TEST_DISPLAY=:98 \
SKYNET_TEST_XWINWRAP=/usr/local/bin/xwinwrap \
SKYNET_TEST_VIDEO=/path/to/local-test-video.mp4 \
python3 -m unittest discover -s tests -p test_wallpaper_visibility.py -v
```

Kurulu ikiliyle görünmeyen Xephyr test sunucusunda beş test geçti: tam/kısmi
örtülme, geç başlayan oynatıcı ve gizliyken dosya değiştirme/çıkış, eksik soket,
sinyalin çocuğa iletilmesi ve eski seçeneklerle çalıştırma. Test sunucusu ve
geçici dosyalar doğrulamadan sonra kaldırıldı.

Kaynaklar: [mpv seçenekleri](https://mpv.io/manual/stable/),
[xwinwrap yerel kaynak açıklaması](../sources/xwinwrap/README.md).

## Aralıklı giriş başlangıcı — 3 Kasım 2026

Oturum günlüğünde `Wallpaper player did not become ready` görüldü. Eski
yardımcı sekiz saniyede vazgeçiyor ve yeniden denemiyordu. İnceleme anındaki
oynatıcı ise seçili GIF'in önbelleğini VA-API ile sağlıklı oynatıyordu; masaüstü
pencerelerle örtülü olduğunda duraklaması normaldi. Hatanın altındaki GPU/oturum
gecikmesinin kesin kaynağı eski sürümün hataları gizlemesi nedeniyle belirlenemedi.

Başlangıç hazırlık süresi 30 saniyeye çıkarıldı; dosya, video parametreleri,
video çıkışı ve idle durumu birlikte doğrulanır. Başarısız ilk denemede yalnız
yeni başlatılan oynatıcı süreç grubu temizlenip bir kez daha denenir. İkinci
başarısızlık bildirilir; sonsuz yeniden başlatma veya sürekli gözetleyici yoktur.
Mevcut tek örnek kilidi tutuluyorsa ikinci oynatıcı açılmaz, mevcut oynatıcının
hazırlığı kontrol edilir. mpv hataları mevcut `session.log` dosyasına iletilir.
Ek günlük dosyası oluşturulmaz. DWM autostart hâlâ arka planda çalıştığı için
bu süre masaüstünün açılmasını bekletmez. GIF, önbellek, kalite, VA-API ve
örtülünce duraklatma seçenekleri korunur.

`tests/test_wallpaper_startup.py` içindeki altı test geçti: eski sekiz saniyeyi
aşan başlangıç, tek tekrar, kalıcı hatada durma/temizlik, tek örnek, erken süreç
çıkışı ve yalnız ilgili süreç grubunu temizleme. Kimlik doğrulamalı ayrı Xephyr
`:192` üzerinde beş mevcut görünürlük testi ve yeni yardımcının gerçek
start/status/stop ile tekrar start çağrısında tek süreç kontrolü geçti.
Gerçek oturum kapatılmadı ve soğuk açılıştaki aralıklı olay yeniden üretilmedi.

## Kayıpsıza yakın GIF kalitesi — 22 Kasım 2026

GIF'ler artık H.264 4:2:0 yerine **HEVC 4:4:4** (`libx265`, CRF 4, `yuv444p`)
olarak önbelleğe alınır. 4:2:0 renk alt örneklemesi siyah üzerindeki ince
kırmızı çizgi ve yazıları bulanıklaştırıyordu. `skynet_globe_3d_wallpaper.gif`
için ortalama PSNR 37,0 dB'den 55,0 dB'ye çıktı. Intel VA-API HEVC Range
Extension profilini donanımda çözer (`hwdec-current=vaapi`, `vuyx`). Önbellek
adı `gif-<sha256>-hevc444.mp4`; eski 4:2:0 dosyaları bir sonraki `set` ile silinir.
Kodlama ~20 s sürer, sınır 300 s'dir.

Ölçekleme: görüntünün dört kenarındaki 4 piksellik şeritler (neredeyse) siyahsa
mpv `panscan=0` ile 1:1 gösterir. 1920×1080 GIF, 1920×1200 ekranda ölçeklenmez;
üst/alt 60 px siyah bant zeminle birleşir. Kenarı siyah olmayan görseller eski
gibi ekranı doldurup kırpılır (`panscan=1`). Açık oynatıcıya da IPC ile uygulanır.

Ölçüm (görünürken, 10 s): mpv ~%6, Xorg ~%2 tek çekirdek; PSS ~126 MB.
Doğrudan GIF oynatma tüm kareleri yazılımla çözdüğü için ~%16 CPU harcıyordu.
Testler: `tests/test_wallpaper_quality.py`.

## 4K video arka plan — 23 Kasım 2026

`~/wallpapers/livewallpaperskynet.mp4` (3840×2160, 50 kare/sn, H.264 High,
23,6 Mbit/s, 12 saniye, sessiz) `dwm-wallpaper set` ile seçildi. GIF'in aksine
video dönüştürülmez; dosya olduğu gibi oynatılır, önbellek kopyası oluşmaz ve
eski GIF kopyası temizlenir. Dosya (35 MB) 24 Kasım 2026'da
`home/wallpapers/livewallpaperskynet.mp4` olarak depoya eklendi; `restore-home.py`
onu `~/wallpapers/` altına geri yükler. Seçim kullanıcıya özeldir ve ev dizini
yolunu içerdiği için `~/.config/dwm-desktop/wallpaper.json` depoda yoktur.
Geri yükledikten sonra seçmek için:

```sh
dwm-wallpaper set "$HOME/wallpapers/livewallpaperskynet.mp4"
```

Videonun üst verisinde kodlayıcı dışında başlık, yazar, konum ya da oluşturma
zamanı yoktur (`tests/test_video_wallpaper.py` bunu sınar).

Ölçümler (1920×1200 ekran, pilde, tek örnek):

- mpv VA-API ile çözüyor, 3840→1920 tam iki kat küçültülüyor; kare düşmesi 0.
  Video 16:9 ve kenarları siyah olduğundan `fit_mode` tüm kareyi gösterir;
  üst ve alt 60 piksel tam siyahtır, kırpma yoktur.
- Kalite: mpv'nin kendi çıktısı, aynı karenin BT.709 etiketli ideal küçültmesiyle
  karşılaştırıldı: alan (kutu) süzgeci SSIM 0,997 / PSNR 48,2 dB, Lanczos
  SSIM 0,992 / PSNR 46,7 dB. Bilinear küçültme tam 2 katta 2×2 ortalama
  olduğundan mpv ayarları (`--profile=fast`, `dscale=bilinear`) burada kaliteyi
  düşürmez. Ölçüm için referans karesi etiketsiz kaynağı BT.709 varsayarak
  üretilmelidir; ffmpeg etiketsiz videoyu varsayılan olarak BT.601 çevirir ve
  renkler ölçümü bozar.
- Güç: oynarken pilden 7,97 W (±1,17), duraklatılmışken 6,99 W (±0,35); fark
  yaklaşık 1 W, mpv + xwinwrap tek çekirdeğin %2,5'i. Bu tek ve gürültülü bir
  ölçümdür, pil ömrü testi değildir. Pencereler arka planı tamamen örttüğünde
  oynatma duraklar.
- Ölçüm yöntemi: mpv IPC üzerinden duraklatıp `screenshot-to-file <dosya> window`
  ile gerçek çıktı karesi alındı; masaüstü etkilenmedi.
