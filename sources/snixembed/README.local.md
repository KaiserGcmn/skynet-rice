# SKYNET snixembed 0.3.3-skynet1

Upstream 0.3.3: https://git.sr.ht/~steef/snixembed
Kaynak arşivi: https://deb.debian.org/debian/pool/main/s/snixembed/snixembed_0.3.3.orig.tar.gz
SHA-256: `2e18b852caca081b92bf580d8439f6eb4e85bc28cee5df0932830649940c51bd`.
Arşiv özeti Debian 0.3.3-2 `.dsc` içindeki özetle karşılaştırıldı.
Upstream ISC lisansı `LICENSE` içinde korunur.

Yerel düzeltmeler:

- D-Bus özellik hataları async işlemden dışarı kaçmaz; son geçerli simge
  korunur. Aynı özellik/aynı hata yalnız ilkinde uygulama adıyla kaydedilir;
  başarılı yanıt bu tanılama durumunu sıfırlar. Global günlük filtresi yoktur.
- Eşzamanlı NewIcon istekleri birleştirilir; değişen son durum tekrar okunur.
  Aynı değerler Variant.equal ile karşılaştırılır. Özellik ve tıklama
  sorguları iki saniye ile sınırlıdır; kapanmış uygulama yeniden başlatılmaz.
- Simge varsayılan görünürlüğüyle tek seferde oluşturulur. `visible` bir
  construct özelliği olmadığı için `Object.new(..., "visible", false)` bile
  ilk gösterimden sonra gizleme/unrealize yapıyordu; bu yol kaldırıldı.
  GtkStatusIcon.set_name yerine pencereyi yeniden oluşturmayan set_title
  kullanılır. Böylece tepsiye eklenirken gereksiz hide/show yapılmaz.
- ARGB → RGBA dönüşümü üç yerine dört bayt adımlar; boyut/veri uzunluğu
  doğrulanır, kaynak D-Bus önbelleği değiştirilmez. Geçersiz veride eski
  simge veya başlangıç yer tutucusu korunur.
- Menü yalnız sağ tıkta hazırlanır. İlk kök/öğeler hazır olmadan popup
  yapılmaz. Sadece bekleyen sağ tık için 25 ms / en fazla iki saniyelik
  hazırlık kontrolü vardır; sürekli çalışan zamanlayıcı yoktur.
- Uygulama kapanınca bekleyen kurulum/tıklamalar iptal edilir; sinyal
  bağlantıları, menü ve simge görünürlüğü açıkça temizlenir.

`make`, Vala ve GTK/dbusmenu geliştirme paketleriyle normal kullanıcı olarak
derler. `scripts/build.py` bileşeni staging alanına alır; otomatik kurmaz.
Debian sertleştirme seçenekleri CPPFLAGS/CFLAGS/LDFLAGS ile aktarılabilir.
Bu makinedeki derleme araçları yalnız geçici olarak açılmış `.deb` dosyalarından
kullanıldı; sisteme yeni paket kurulmadı. Runtime mevcut GTK/dbusmenu
kütüphanelerini kullanır; geçici derleme yollarına RPATH yoktur.

## Regresyon testi

Gerçek masaüstünü değiştirmeyen özel Xephyr, D-Bus, DWM ve sahte SNI/menu
servisi kullanılır. Mevcut kurulu DWM gerekir; geçici HOME altındaki boş
DWM dizini gerçek autostart'ı engeller.

```sh
SKYNET_TRAY_TEST_BINARY=/absolute/path/to/snixembed \
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_snixembed.py -v
```

İsteğe bağlı `SKYNET_TRAY_BASELINE=/path/to/upstream-binary`, eski sürümün
aynı özellik hatasını ürettiğini karşılaştırır. Xephyr, xauth, xdotool,
x11-utils, python3-dbus ve python3-gi test bağımlılıklarıdır. Kullanıcı
oturumunun X sunucusuna erişim gerekir; test içeriği görünmeyen ayrı
pencerede çalışır. Ayrıntılar `docs/TRAY.md` içindedir.
