# Kitty açılışı

`home/.local/bin/kitty`, parametresiz masaüstü açılışlarında Kitty'nin yerleşik
`--single-instance` yöntemini kullanır. DWM'nin mevcut `kitty` kısayolu ve
`Exec=kitty` kullanan uygulama menüsü, `~/.local/bin` PATH'te `/usr/bin` önünde
olduğunda bu başlatıcıya ulaşır. Aynı ortamla açılan pencereler GPU yazı
önbelleğini paylaşır. Her pencerenin kendi kabuğu ve çalışma dizini vardır.

Kitty 0.41, yeni pencerelere ilk pencerenin ortamını aktarır. Bu nedenle grup
adı, sıralanmış ve NUL ile ayrılmış tüm ortamın SHA-256 özetinden üretilir.
PATH, sanal ortam, ekran, giriş veya başka bir ortam değeri değişirse ayrı
grup açılır. Paket çekirdeğinin dosya kimliği de grup adına katılır; yeni paket
önceden açık eski Kitty işlemine bağlanmaz. Ortam değerleri diske veya komut satırına yazılmaz. Değişen PWD
gibi değerler de ayrı grup oluşturabilir; öncelik doğru ortamın korunmasıdır.

İlk pencere normal başlangıç maliyetini taşır. Hızlanma, bu yöntemle açılmış
bir pencere açıkken sonraki pencerelerde görülür. Önceden açılmış bağımsız
Kitty pencereleri gruba sonradan katılmaz. Son pencere kapandığında grup da
sona erer; otomatik başlayan veya sürekli çalışan ek servis yoktur.

`--wait-for-single-instance-window-close`, sonraki çağrıların kendi penceresi
kapanana kadar beklemesini sağlar. İlk çağrı, gruptaki son pencere kapanana
kadar ana işlem olarak çalışır. Parametre verilirse bütün argümanlar
seçilen Kitty ikilisine geçer: örneğin `kitty +kitten …`, `kitty @ …`,
`kitty --config …` ve `kitty komut` önceki davranışını sürdürür. Bu komutlu
açılışlar otomatik olarak gruba dahil edilmez. `allow_remote_control`
etkinleştirilmez; ağ dinleyicisi eklenmez.

Kitty'nin görünümü, fontu, Bash, Fastfetch, kabuk tamamlama ve 60 Hz ekran için
mevcut `repaint_delay 16`, `input_delay 2`, `sync_to_monitor yes` ayarları
korunur. Daha yüksek pil tüketimi pahasına çizim sıklığı artırılmaz.

## APT ile yönetilen uyumluluk paketi — 11 Kasım 2026

Yamalar artık dağıtımın özgün `/usr/bin/kitty` ve `/usr/lib/kitty` konumlarında,
`kitty 0.41.1-2+deb13u2+skynet1` paketiyle kurulu. Başlatıcı doğrudan
`/usr/bin/kitty`yi seçer. Paket, Debian'ın özgün başlatıcısını, GLFW eklentilerini,
bağımlılıklarını ve paket betiklerini korur. Codex için OSC 7501, klavye sıfırlama,
1007 ve tekrarlı 2026 desteği ile SysVinit kontrolü bu tabana aktarıldı.
Yeni sürümlerdeki ilgili güvenlik düzeltmeleri de geri taşındı; stok eski
Kitty'ye doğrudan dönüş yapılmadı. Tema ve terminal yapılandırması değiştirilmedi.

APT hold/pin veya ek depo yok. `...+deb13u3` gibi sonraki resmî paket, yerel
`...+deb13u2+skynet1` sürümünden yüksek sayılır ve normal güncellemeyle kurulur.
**Resmî güncelleme yerel yamaları değiştirebilir; uyumluluk yeniden kontrol
edilmelidir.** Yamalar otomatik olarak yeni sürüme zorla uygulanmaz.
`apt update` listeyi yeniler; kurulum normal `apt upgrade` ile yapılır.

10 özel ve 58 upstream test geçti. Paket içeriği ve kurulu konum özel Xephyr
ile kontrol edildi: tekerlek, Shift+Enter, Ctrl+C, klavye/screen modu sorguları,
2026 zaman aşımı ve kimliksiz Codex 0.167.1 açılış/çıkışı. Kitty stderr boştu.
Geçersiz girdi testleri ise gerçek hataları kaydetmeye devam eder. APT denemesi
yalnız Kitty'nin yükseldiğini gösterdi; `dpkg --verify kitty` ve `dpkg --audit`
temiz. Wayland oturumu ve gerçek SSH sunucusuna bağlantı test edilmedi.

Önceki 5 Kasım kurulumu ayrı `~/.local/lib/skynet-kitty` altında Kitty 0.50.0
kullanıyordu. Yeni başlatıcı bu kopyayı seçmez. Önceden açık pencerelerin
kullandığı dosyalar, o süreçler kapanmadan silinmemelidir; eski pencereler normal
kapatılıp yenileri açıldığında paket sürümü kullanılır. Açık oturumlar zorla
sonlandırılmadı. Ayrı sürüme ait derleme tarifi tarihsel kayıt olarak korunur.

Kaynak, güvenlik düzeltmeleri, sürüm sıralaması, yeniden derleme ve testler:
[`sources/kitty-compat/debian/README.md`](../sources/kitty-compat/debian/README.md).

## Doğrulama — 27 Ekim 2026

Kurulu Kitty 0.41.1 ile gerçek Bash yapılandırması ve Fastfetch çalıştırılarak,
ana masaüstüne gösterilmeyen ayrı Xephyr ekranında altışar açılış dönüşümlü
ölçüldü. İşlem başlatılmasından kabuğun hazır işareti yazmasına kadar medyan:

| Açılış | Süre |
| --- | ---: |
| Bağımsız yeni Kitty işlemi | 957 ms |
| Açık grupta yeni Kitty penceresi | 172 ms |

Bu sonuç ayrı test ekranına aittir; gerçek masaüstü açılış süresi, ilk soğuk
açılış veya tuş gecikmesi ölçümü değildir. İlk/ikinci pencere, aynı ortamda
ortak işlem, değişen ortamda ayrı işlem ve doğru çalışma dizini, pencere
kapanışını bekleme, son pencerenin işlemi bitirmesi, boş/boşluklu argümanlar,
`--version` ve `+runpy` ayrıca doğrulandı. Kabuk sözdizimi kontrolü ve dört
geri yükleme testi geçti. Test ekranı, işlemleri ve geçici dosyaları temizlendi.

Başlatıcıyı kaldırmak `kitty` komutunu tekrar paketle gelen `/usr/bin/kitty`ye
yönlendirir. Bu yalnız başlatıcının kaldırılmasıdır; paketteki uyumluluk yamasını kaldırmaz.

Kaynak: [Kitty komut satırı — single-instance](https://sw.kovidgoyal.net/kitty/invocation/#cmdoption-kitty-single-instance),
[performans ayarları](https://sw.kovidgoyal.net/kitty/conf/#performance-tuning).
