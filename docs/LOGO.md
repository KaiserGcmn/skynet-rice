# Dönen SKYNET küresi — 22 Kasım 2026

Kilit ekranında ve greetd'de dönen çizgili üçgen yerine, kullanıcının verdiği
kırmızı dünya + SKYNET görseli esas alınarak çizilmiş **dönen bir dünya küresi**
kullanılır. Görsel fotoğraf olarak eklenmez; her kare koddan çizilir.

- **Küre:** ortografik izdüşüm, gerçek kıtalar (Natural Earth 1:50m kara
  poligonları, kamu malı), 15° enlem-boylam ağı, kenar ışıması. Eksen
  görseldeki gibi sola eğiktir (bakış 18° kuzeyden, 18° dönüş). Dünya doğuya
  döner (yüzey soldan sağa akar), tam tur 30 saniyedir.
- **Hologram dokunuşu:** arka yüzün ağı okyanusun içinden soluk görünür.
- **Sabit katman:** merkezdeki üç parçalı SKYNET amblemi, geniş geometrik
  `SKYNET` yazısı ve alt çizgi dönmez. Siyah dış hat ve yazı plakası,
  görseldeki beyaz boşluklar gibi küreyi keser.
- **Görseldeki hatalar düzeltildi:** çarpık/eksik kıtalar gerçek haritayla,
  düzensiz ve kenarda kırılan ağ çizgileri geometrik ağla, simetrisi bozuk
  amblem önceki amblemin ölçüleriyle değiştirildi.
- Küçük `CYBERDYNE SYSTEMS CORPORATION` yazısı ve 3,8 saniyelik ışık
  taraması korunur. Greeter'daki noktalı SKYNET yazısı kaldırıldı; isim artık
  kürenin içinde. Kilit arka planındaki `S K Y N E T` başlığı değişmedi.

## Kaynak

- `sources/xsecurelock-style/skynet-globe.h`: ortak çizim (Cairo, istemci
  tarafı). Görünüm, eğim ve dönüş ekseni sabit olduğu için her pikselin enlem
  ve taban boylamı bir kez hesaplanır; kare başına yalnız boylam kaydırılıp
  kara maskesi örneklenir. Amblem katmanı bir kez çizilip önbelleğe alınır.
- `sources/xsecurelock-style/skynet-globe-land.h`: 1024×512 eşdikdörtgen kara
  maskesi, satır başına koşu uzunluğu kodlu (~25 KB). Yeniden üretmek için:
  `python3 -I render-globe-land.py ne_50m_land.geojson skynet-globe-land.h`.
- `sources/xsecurelock-style/skynet-logo.h` (kilit): 480×260 alan, küre çapı
  226 px. Küre 15 fps, yazı taraması 30 fps; yalnız değişen bölge MIT-SHM
  `XShmPutImage` ile gönderilir. Eski sunucu taraflı XRender çizimi kalktı.
- `sources/gtkgreet-hud/skynet-logo.h` (greeter): 480×340 tasarım alanında
  290 px küre; cihaz pikselinde çizilir, ölçekte bulanıklaşmaz.

## Kurulum ve doğrulama — 22 Kasım 2026

Kurulu iki ikili önce depodaki kaynakla karşılaştırıldı: greeter (depo +
`devuan-source.patch`) bayt bayt, kilit dekoru `.text` bölümüyle eşleşti.
Yenileri aynı yöntemle derlenip `/usr/local/libexec/saver-lock-style` ve
`/usr/local/libexec/greetd/gtkgreet-hud` olarak root:root 0755, atomik
kuruldu. Önceki ikililer `~/.local/state/skynet-rice/backups/globe-logo-20261122/`
içindedir. PAM, doğrulama, kilit çekirdeği ve greetd yapılandırması değişmedi;
yeni görünüm sonraki kilit/girişte etkinleşir.

- `tests/test_skynet_globe.py`: kara maskesi (oran ve bilinen noktalar),
  izdüşüm yönü, 30 s periyot, kare süresi, kilit yerleşimi (küre yazı
  şeridine taşmaz), sunucu taraflı çizimin kalktığı.
- `tests/test_logo_rotation.py`: üç greeter boyutunda yalnız küre ve yazı
  ışığı değişir; amblem sabit; 30 s ve 3,8 s döngüleri.
- Özel Xephyr (1920×1200, 96 DPI): kilit dekorunda dönüş ve doğu yönü
  görüldü. Dekor + X sunucusu toplamı eski %9–11'e karşı %12; greeter eski
  %70'e karşı %58 (yazılım çizimli Xephyr; gerçek ekranda daha düşük). Kilit
  içi 12 saniyelik karartma animasyonu durdurmaya devam eder.

---

# Dönen SKYNET üçgeni — 26 Ekim 2026 (yerini küre aldı)

11 Kasım 2026: açılışta bazen görülen ASCII logo, başlatıcının TTY yedeğidir.
Çizim değişmeden grafik başlangıç kurtarması eklendi; ayrıntılar ve sınırlar
[GREETER-STARTUP.md](GREETER-STARTUP.md) içindedir.

GTK greetd ve XSecureLock dekorunda yalnızca kırmızı, çizgili üçgen dikey
ekseni çevresinde döner. Tam tur dört saniyedir; hafif perspektif kullanılır.
Üçgen ve içindeki çizgiler birlikte hareket eder. SKYNET yazısı ve bütün
metinlerin yerleşimi sabittir. Küçük CYBERDYNE yazısının koyu kırmızı harfleri
üzerindeki eski beyaz ışık taraması, bağımsız 3,8 saniyelik döngüsüyle korunur.
Saat, pil bilgisi ve parmak izi sayacı kendi güncellemelerini sürdürür.

Yeni medya dosyası, oynatıcı, paket veya arka plan hizmeti kullanılmaz.
Mevcut yaklaşık 30 fps sınırı korunur. GTK çizimi görünmeyen pencerede durur;
kilit dekoru da gizliyken veya ekran karardığında animasyonu durdurur.

## AFK görünümünün düzeltilmesi — 27 Ekim 2026

Güç tuşu (`HandlePowerKey=lock`) ve beş dakikalık AFK kilidi aynı `xss-lock`
süreci üzerinden `/usr/local/libexec/dwm-lock` başlatıcısını kullanır.
Farklı görünen eski logo, ayrı bir kilitleyiciye yönlendirmeden kaynaklanmıyordu.
Dekor, X11 `ScreenSaverOn` durumunu fiziksel ekran kapanması saydığı için
AFK tetiklenince ilk animasyon karesini bile çizmiyordu; arka plan PNG'sindeki
eski noktalı üçgen görünür kalıyordu. Bu durum, `ScreenSaverOn` / `kind=Blanked`
olan özel Xephyr ekranında kurulu eski programla tekrar üretildi. Aynı program
X11 durumu sıfırlanınca animasyona başlıyordu.

`saver-lock-style.c` artık ekranın açık olup olmadığını DPMS'ten, dekorun
görünürlüğünü haritalama ve `VisibilityNotify` olaylarından öğrenir. AFK olayı
tek başına animasyonu durdurmaz. DPMS kapalıysa veya pencere gizli/tamamen örtülü
ise animasyon durur; kısmi örtülmede görünür logo hareket etmeye devam eder.
İlk kare ve boyut değişimi sonrasında güncel logo çizilmeden arka planın tamamı
gösterilmez. Böylece ilk açılışta eski bitmap'in gösterilmesi de önlenir.
[X11 ekran koruyucu durumları](https://xorg.freedesktop.org/archive/X11R7.6/doc/scrnsaverproto/saver.html).
21 Kasım 2026'dan beri aynı görünürlük kuralı kenar HUD animasyonunu da
(`cyber-hud.h`) yönetir. Logo veya HUD görünürse kare döngüsü çalışır, karanlıkta
ikisi de durur. Ayrıntılar: [CYBERPUNK-STYLE.md](CYBERPUNK-STYLE.md).

Bu düzeltme yalnız `/usr/local/libexec/saver-lock-style` ikilisini değiştirir.
PAM, doğrulama yardımcıları, kilit çekirdeği, beş dakikalık AFK süresi, 12 saniyelik
kilit içi karartma ve güç tuşu politikası korunur. Greetd'deki logo kodu ve
kilitteki dört saniyelik dönüş/3,8 saniyelik yazı ışığı değiştirilmez. Sonraki
kilit açılışında etkinleşir; masaüstü veya kilit izleyicisi yeniden başlatılmaz.

Doğrulama: üç `test_lock_display_power.py` testi, açık/kapalı/standby/suspend,
devre dışı ve okunamayan DPMS durumlarını gerçek ekrana erişmeden sınar.
Özel Xephyr testinde güncel program AFK sırasında da hareket etti ve eski
bitmap'i göstermedi. Pencere gizlenince/tamamen örtülünce iki ayrı 0,7 saniyelik
ölçümde CPU zamanı artmadı; yeniden görünürken animasyon sürdü. Kısmi örtülme ve
yeniden boyutlandırma da sınandı. Gerçek oturum kilitlenmedi; PAM veya parmak izi
sensörü kullanılmadı. Fiziksel panelin DPMS kapanışı bu testte tetiklenmedi.

## Kaynak ve kurulum

Çizim değişiklikleri `sources/gtkgreet-hud/skynet-logo.h` ve
`sources/xsecurelock-style/skynet-logo.h` içindedir. Yerel GTK sürümü için
[BIOMETRIC.md](BIOMETRIC.md) içindeki kaynak katmanlama yöntemi korunur:
geçici kaynak kopyasına mevcut `~/.local/share/skynet-rice/devuan-source.patch`
uygulanır, ardından `make` çalıştırılır. Bu yama değiştirilmemiştir.
Kilit dekorunun derleme bayrakları `scripts/build.py` içinde tanımlıdır.

Yalnızca `/usr/local/libexec/greetd/gtkgreet-hud` ve
`/usr/local/libexec/saver-lock-style` atomik olarak, root:root / 0755
izinleriyle güncellenir. PAM, parmak izi yardımcıları, ana kilit programı,
greetd başlatıcısı ve yapılandırması değiştirilmez. Yeni görünüm, giriş ve
kilit ekranları bir sonraki açıldığında kullanılır; oturum yeniden başlatılmaz.

## Doğrulama

- Her iki program mevcut Devuan katmanıyla, yeni derleyici uyarısı olmadan
  derlendi; bağlantı kitaplıkları kontrol edildi.
- `python3 -m unittest discover -s tests -p test_logo_rotation.py -v`:
  üç widget boyutunda yalnızca üçgen ve küçük yazının ışığı değişir; büyük
  SKYNET yazısı sabit kalır. Üçgen dört saniyede ilk konumuna döner ve birinci
  saniyede yandan görünür. Küçük yazı 3,8 saniyede ilk ışık durumuna döner.
- Özel Xephyr ekranındaki XRender kontrolü de 65 örnek karede değişimin
  bu alanlarla sınırlı kaldığını ve iki döngünün ayrı sürelerini doğruladı.
  Önceki kurulumda gerçek dekor programının animasyonu,
  gizlenince düşük işlemci kullanımı, yeniden gösterilmesi ve klavyeyi
  yakalamadığı ayrıca kontrol edildi.
- Önceki kurulumda beş `test_greeter_protocol.py` testi geçti. Özel Cage/Wayland ekranında
  sahte greetd hizmetiyle parmak izi bekleme, hatalı parola reddi, yeniden
  deneme ve yalnızca başarı yanıtından sonra oturum isteği sınandı. Bu hız/ışık
  düzeltmesi sadece iki çizim başlığını değiştirir; doğrulama kaynakları korunur.
- Gerçek PAM, parola, parmak izi kaydı veya oturum kilitleme kullanılmadı.
  Korunan sistem dosyalarının SHA-256 değerleri kurulumdan sonra karşılaştırıldı.

