# Yatay batarya simgesi — 26 Ekim 2026

> **Güncel görünüm 23 Kasım 2026'dan beri aşağıdaki son bölümdedir**
> ("Pil sembolü ve doluluk çubuğu"). Bu dosyanın ortasındaki `BAT`/`AC`/`CHG`
> etiketi, beş hücreli gövde ve fiş/şimşek/üçgen rozeti anlatımları tarihseldir;
> durum kuralları (hangi durumda ne gösterildiği) korunmuştur.

2 Kasım'daki genel bar görünümü güncellemesi [DWM-BAR.md](DWM-BAR.md)
içindedir. Aşağıdaki pil davranışı korunur; renkler ve panel çerçevesi yeni
bar paletine uyarlanır. Aktif şarj etiketi açık yazılı kırmızı rozet kullanır.

DWM barındaki beş ayrı pil hücresi yerine ince, yuvarlatılmış yatay pil
gövdesi çizilir. Tek piksel açık renk çerçeve, kırmızı doluluk ve koyu arka
plan mevcut SKYNET paletinden gelir. Dolgunun üst kenarındaki hafif açık
kırmızı çizgi hacim verir. Dolgu yüzdeye göre soldan sağa genişler; sıfırda
boş, yüzde yüz olduğunda doludur.

`Charging` durumunda etiket kırmızı `CHG` olur; gövde, uç ve panelin üst
çizgisi kırmızı yanar. Gövdenin içindeki açık renk şimşek, koyu konturuyla
hem boş hem dolu pil üzerinde okunur. Adaptör bağlıyken şarj sınırında bekleme
veya `Full` durumunda kırmızı `AC` etiketi, kırmızı uç ve açık renk fiş
gösterilir. Pil gövdesi ve panel üst çizgisi normal renginde kalır. Bu,
adaptöre bağlı beklemeyi aktif şarjdan ayırır; şimşek yalnız `Charging` içindir.
Gösterge sabittir; animasyon zamanlayıcısı veya ek arka plan süreci yoktur.

Pil seviyesi **%0–10 dahil** olduğunda, adaptör/şarj durumu yoksa pilin
üzerinde kırmızı uyarı üçgeni ve açık renk ünlem görünür. Yüzde ve BAT
etiketi de kırmızı olur. **%11'de uyarı kalkar.** `AC` ve `CHG` durumlarında
düşük yüzdeye rağmen üçgen gösterilmez; fiş veya şimşek korunur.
Geçersiz/eksik yüzde düşük pil sayılmaz. Yüzde biliniyor fakat güç durumu
`?` ise adaptör bağlantısı doğrulanamadığından düşük pil uyarısı gösterilir.

Sayısal yüzde korunur. Geçersiz/eksik veri `--%` ve boş gövde
olarak gösterilir. Panel genişliği yüzde ve şarj durumundan bağımsızdır;
gerçek oturum ekranının font ölçüleriyle 136 px, bar yüksekliği 30 px'dir.
Önceki özel Xephyr ekranında ölçülen 122/25 px farklı ekran font ölçeğinden
gelir. Bu düzeltme font, panel genişliği veya bar yüksekliği ayarını değiştirmez.
Panel, CPU bölümüne uyumlu çelik rengi kenar ve kırmızı köşe detayı kullanır.
CPU, tarih/saat, etiketler, sistem tepsisi, bar ayırıcıları ve alt kırmızı
çizgi korunur. Simge Xlib ile çizilir; ikon fontu, resim veya yeni bağımlılık
gerektirmez.

## Kaynak ve etkinleştirme

Çizim `sources/dwm/dwm.c` içindedir. `sources/slstatus/config.h` içindeki
üretici Linux'ta `Full`/`Not charging` durumunda
`/sys/class/power_supply/*/type=Mains` ve `online=1` bilgisini doğrular.
Adaptör adı sabit kodlanmaz; farenin pili veya USB cihazının `online` değeri
adaptör sanılmaz. Onaylanmış bekleme mevcut `•` durum işaretiyle aktarılır.
Adaptör çevrimdışıysa `↓`, bilgi eksik/bozuksa `?` üretilir. `Charging` için
`↑`, `Discharging` için `↓` korunur. Yeni protokol alanı yoktur; önceki DWM
sürümü de bu çıktıyı okuyabilir. TLP, şarj sınırı, yüzde hesabı ve saniyede bir
örnekleme değişmez. Bekleme kontrolü dış komut veya yeni süreç başlatmaz.

`profiles/debian/rootfs/etc/slstatus/config.h` aynı kaynak ayarını taşır.

Makinedeki DWM kurulurken mevcut
`~/.local/share/skynet-rice/devuan-source.patch` geçici kaynak kopyasına
`patch --batch --fuzz=0 -p1` ile uygulanır; ardından `sources/dwm` içinde
`make` çalıştırılır. Bu yerel katman kompakt bar, CPU görünümü ve tuş bağlarını
korur. 26 Ekim'deki kurulumda yama dosyası değiştirilmemiştir; 2 Kasım'da
kompakt CPU çizimi depoya taşındığı için yalnız eski CPU yama bölümü
kaldırılmıştır. Güncel derleme ayrıntıları DWM-BAR.md içindedir.

Doğrulanan programlar `/usr/local/bin/dwm` ve `/usr/local/bin/slstatus`
konumlarına atomik olarak, root:root ve 0755 izinleriyle kurulur.
Çalışan pencere yöneticisi kapatılmaz. Bu DWM
sürümünde canlı çizim yenileme bulunmadığından yeni simge **bir sonraki
DWM oturum açılışında** etkinleşir.

## Doğrulama

- `python3 -m unittest discover -s tests -p 'test_battery*.py' -v` (6 test):
  yüzde sınırları, şarj/dolu/boşalma/bilinmeyen durumları ve bozuk veri sınandı.
  Sahte sysfs ile adaptörün bağlı/ayrılmış olması, birden fazla adaptör,
  farklı adlar, çevre birimleri ve eksik/bozuk `online` verisi sınandı.
  Şimşek kararı yüzdeye göre verilmez; yalnız şarj durumuna bağlıdır.
- Uyarı eklenirken penceresiz X11 çizim tamponunda önceki ve yeni çizim
  karşılaştırıldı: %0, 1, 9, 10, 11, 78, 100 ve bilinmeyen yüzde; dört güç
  durumu; 30 ve 25 px yükseklik (64 durum). Gerçek masaüstü görüntüsü okunmadı.
  16 düşük pil görünümünde üçgen/ünlem doğrulandı. Kalan 48 görünüm, tüm
  `AC`/`CHG` durumları dahil, önceki çizimle piksel piksel aynıydı.
  Sabit panel genişliği, kesintisiz alt çizgi ve GC ayarları korundu.
- Önceki pil görünümü değişikliklerinde tam DWM özel ekranda çalıştırıldı;
  test autostart betikleri boştu.
  Gerçek oturumdaki uygulamalar ve sistem servisleri başlatılmadı/kapatılmadı.
- Mevcut Devuan yaması sapma kabul etmeden uygulandı, derleme uyarısız bitti.
  Fontlar, renk tanımları ve CPU işlevi değiştirilmedi.

## %80 sınırında %78 bekleme

26 Ekim 2026 kontrolünde `ADP1/online=1`, `BAT0/capacity=78`,
`BAT0/status=Not charging`, `current_now=0` ve durdurma eşiği `80` idi.
Bu bir gösterge hatası değildir. ASUS, %80 modunda yeniden şarjın %78'in
altında başladığını açıklar; gözlenen durum bu davranışla uyumludur.
Bu cihaz Linux'ta yalnız durdurma eşiğini sunar; başlangıç eşiği okunamadı
ve zorla şarj başlatılmadı. TLP ayarları değiştirilmedi.
[ASUS açıklaması](https://www.asus.com/support/FAQ/1032726/),
[TLP ASUS desteği](https://linrunner.de/tlp/settings/bc-vendors.html#asus).

## Batarya simgesi yenilemesi — 4 Kasım 2026

Yalnız `batterypanel` içindeki pil gövdesi/doluluk/durum simgesi çizimi
sadeleştirildi. Gövde 34×16 px, küçük köşe yarıçapı, açık çelik kontur ve
ince alt kenar kullanır. İçeride dört koyu yuva vardır; kırmızı doluluk
seviyeye göre bu yuvaları soldan sağa doldurur. İnce açık kırmızı üst kenar
hücreleri ayırır. Boş hücreler de seçilebilir. Kontur ve uç daha belirgindir.
Şarj şimşeği, bekleme fişi ve düşük pil üçgeni koyu ayırıcı zemine sahiptir.

Yüzde, BAT/AC/CHG etiketleri, panel genişliği, renk paleti, diğer göstergeler
ve durum ayrıştırıcıları değiştirilmedi. %0–10 dahil uyarı yalnız pilde
kalır; %11'de kalkar, şarjda/AC'de görünmez. Ek süreç, animasyon, resim veya
ikon fontu yoktur. Eski yerel yapılandırma yaması korunarak yalnız DWM
uyarısız derlendi. Altı mevcut batarya testi geçti; özel, görünmeyen Xephyr
ortamında dokuz pil durumu görüntülendi ve DWM çalışmayı sürdürdü. Kaynağın
`batterypanel` dışındaki kısmı işlem öncesi kopyayla birebir karşılaştırıldı.

Kurulum `/usr/local/bin/dwm` dosyasını atomik değiştirir; çalışan pencere
yöneticisi kapatılmaz. Görünüm **sonraki oturum açılışında** etkinleşir.
İkili SHA-256: `e9b07398cf0d6c8f633a2dd686b84ec18c9d206dab70bbd68820d6db27702175`.

## Ayrı durum simgesi ve beş hücre — 12 Kasım 2026

Pil gövdesi beş okunaklı kırmızı hücreyle çizilir. Doluluk seviyeye göre
ilerler; yüzde verisi değiştirilmez. Önceki doluluğun üzerine bindirilen
fiş/şimşek/uyarı yerine gövdenin sağında sabit genişlikli bir durum alanı
vardır. AC beklemesinde iki kırmızı uçlu açık renk fiş, şarjda açık renk
şimşek, normal pilde aşağı ok; %0–10 dahil yalnız pilde kırmızı ünlemli
üçgen gösterilir. Eksik veri `--%` ve kısa çizgi olarak kalır.

BAT/AC/CHG etiketleri korunur. Durum alanı paneli 19 px genişletir; yüzde
ve güç kaynağı değiştiğinde alan genişliği sabit kalır. Birleşik panelin
çerçevesi, CPU/tarih/saat, tepsi ve klavye kısayolları değişmez. Şarj limitine
ulaşmış adaptör bağlantısı aktif şarj gibi gösterilmez; BIOS/TLP ayarlarına
dokunulmaz. Animasyon veya yeni arka plan süreci eklenmez.

Önceki ikili kaynak + yerel yama ile birebir yeniden üretildi. Kaynak farkı
yalnız `batterypanel` içinde; yeni derleme uyarısız. Altı batarya testi geçti.
Özel Xephyr ekranında %79/%80 AC, %50 şarj, %10/%11 pil, %0/%100 pil,
%10 şarj ve eksik veri görsel olarak sınandı. Normal Polkit doğrulamasıyla
ikili atomik olarak kuruldu; çalışan oturum kapatılmadı. Görünüm sonraki
oturum girişinde etkinleşir. Geçici derleme/test/kurulum dosyaları temizlendi.

İkili SHA-256: `6a781d994e5a4dd470a254d5dafdd657af44185b2c659069b59a64b58ec73b5a`.


## Pil sembolü ve doluluk çubuğu — 23 Kasım 2026

Pil paneli CPU ve RAM ile aynı düzene geçti: **sembol, yatay doluluk çubuğu,
yüzde.** Çubuk CPU/RAM ile aynı ortak işlevden (`gaugebar`) çizilir. Yazılı
`BAT`/`AC`/`CHG` etiketi, beş hücre ve ayrı rozet alanı kalktı; durumu artık
sembolün içindeki işaret ve renkler anlatır. Panel genişliği duruma ve
yüzdeye bağlı değildir. Durum alanı toplamda 610 px'ten 573 px'e indi (aynı
durum metniyle ölçüldü: Xephyr, 96 DPI, 1920 px bar).

Sembol 23×14 px düz bir pil gövdesi, köşeleri 1 px yuvarlatılmış ve sağda
3×6 px belirgin bir uç içerir (ilk sürümdeki 18×12 kırpık köşeli gövde gerçek
çubukta küçük ve koyu kırmızı zeminde okunmaz bulunduğu için aynı gün
büyütüldü). İç zemin çubuk izinin koyu rengidir; içindeki işaretler büyük ve
açık renklidir. Seviyeyi sembol değil çubuk gösterir. Durumlar önceki
kurallarla aynıdır:

| Durum | Sembol | Çubuk, yüzde |
|---|---|---|
| Pilde (`↓`) | koyu yeşil çerçeve, uç ve aşağı ok | **koyu yeşil** dolgu, normal yüzde |
| Şarjda (`↑`, `Charging`) | neon yeşil çerçeve, uç ve şimşek | **neon yeşil** dolgu |
| Adaptör bağlı, bekleme/dolu (`•`) | beyaz çerçeve, uç ve fiş; şarj sınırı beklemesi dahil | **beyaz** dolgu |
| Kritik: **%0–10 dahil**, adaptör/şarj yok | gövde dolu kırmızı, koyu ünlem | **kırmızı** dolgu, yüzde kırmızı |
| Güç durumu `?` ama yüzde biliniyor | adaptör doğrulanamadığından pilde sayılır: koyu yeşil aşağı ok, ≤%10'da kritik | koyu yeşil (kritikte kırmızı) |
| Yüzde eksik/geçersiz | nötr (açık gri) çerçeve, tire | `--%`, boş çubuk (düşük pil sayılmaz) |

**%11'de uyarı kalkar.** `AC` ve `CHG` durumlarında düşük yüzdeye rağmen kritik
görünüm gösterilmez; fiş veya şimşek korunur. Şimşek yalnız şarj durumuna
bağlıdır, yüzdeye değil. Kritik karar tek yerde, `batterylow()` içindedir.
Şimşek ve ok ucu XRender ile kenar yumuşatmalı çizilir, ortak yardımcı
`aapoly()`; `slantbar` da bunu kullanır. Animasyon, zamanlayıcı, resim veya
ikon fontu yoktur.

Veri biçimi değişmedi: slstatus yine `BAT [▰▰▰▰▱]  80% •` üretir; DWM hücre
karakterlerini yok sayar, yalnız yüzde ve durum işaretini okur
(`batterypercent()` aynı). Bu yüzden slstatus, TLP, şarj sınırı ve adaptör
doğrulaması dokunulmadan kalır. Kilit ekranı ve greeter pil çizimleri ayrı
koddur, bu değişiklikten etkilenmez.

Doğrulama:

- `tests/test_cpu_panel.py` içindeki `batterylow` testi: eksik, %0, %1,
  %10 (kritik), %11 ve %100 pilde; %0, %5 ve %10 şarjda ve adaptörde
  kritik değil. `test_battery_panel.py` ayrıştırma testleri (6 test) ve
  `test_battery_power.py` aynen geçti. Eski `batterylitcells` ve testi
  kaldırıldı; çubuk dolgusu `gaugefillpx` testindedir.
- Özel çerezli Xephyr ekranında (96 DPI, boş autostart) sekiz durum çizildi:
  %100 şarjda, %80 bekleme, %47 ve %11 pilde, %10 ve %5 kritik (`↓`, `?`),
  %5 şarjda, eksik veri. Hepsi okunur ve aynı genişlikteydi. Büyütülen sembol
  altı durumda (şarj, bekleme, pilde, kritik, şarjda düşük, eksik veri) yeniden
  çizilip kontrol edildi.
- DWM, depo kaynağı artı yerel yamanın DWM bölümüyle (`patch --fuzz=0`)
  uyarısız derlendi. Yeni ikili SHA-256:
  `1499a11d08ab83f81b6f17599bfcbf4b0e78b8d976ab8e3aef12fff4c966a84c`. Yedekler:
  `~/.local/share/dwm-theme-backups/before-battery-gauge-20261123T113416Z/`
  (ilk çubuklu sürüm öncesi) ve `before-battery-symbol-20261123T114141Z/`
  (büyütme öncesi).
  Görünüm **sonraki DWM oturum açılışında** etkinleşir.

### Neon yeşil sembol — 23 Kasım 2026

Kullanıcının isteğiyle pil sembolü neon yeşil (`#39FF14`) yapıldı; bu, rice'ın
siyah/kırmızı/çelik paletinde bilinçli ve tek bir istisnadır. Renk
`sources/dwm/config.h` içinde `SchemeStatusBatGreen` şemasıdır. Gövde çerçevesi,
uç ve içindeki şimşek, fiş ve ok yeşildir; iç zemin koyu gridir.

- **Kritik seviye kırmızı kalır** (dolu kırmızı gövde, koyu ünlem): yeşil bir
  uyarı işlevini yitirirdi.
- **Veri yokken** sembol yeşil değil nötr açık griyle çizilir; yeşil "pil
  sağlıklı/biliniyor" anlamı taşır.
- CPU ve RAM kırmızı kalır. Pil çubuğunun dolgu rengi durumu izler (bir sonraki
  bölüm); sembolün içindeki işaret (şimşek/fiş/ok) de durumu ayırır.
- Yamanın `config.h` bölümü renk satırlarına dokunmadığı için sıfır fuzz ile
  uygulanmaya devam eder (yalnız 1 satır kayma).
- *Sonradan değişti:* sembolün rengi artık çubuk dolgusunu izler; ayrıntı en
  alttaki "Sembol rengi çubukla aynı" bölümündedir. Bu bölümdeki "sembol
  neon yeşildir" anlatımı yalnız ilk sürüm içindir.
- Yeni ikili SHA-256: `3dfe7f497572abeab586cf4b1adfbbdee01fafefeb75df1d733ee368f8e7701d`. Yedek:
  `~/.local/share/dwm-theme-backups/before-battery-green-20261123T114924Z/`.

### Çubuk dolgusunun durum rengi — 23 Kasım 2026

Pil çubuğunun dolgusu artık duruma göre renklenir (`batterycolor()`):
**şarjda neon yeşil**, **kritikte kırmızı**, **geri kalan her durumda beyaz**
(pilde boşalırken ve adaptörde şarj sınırı beklemesinde). Şarj, kritikten
önceliklidir: %5'te şarj oluyorsa dolgu yeşildir. Dolgu rengi artık çubuk
çizen `gaugebar()` işlevine parametre olarak verilir; CPU ve RAM aynı işlevi
kendi kuralıyla (`loadcolor()`: kırmızı, %85 ve üstünde açık kırmızı)
çağırır, görünümleri değişmedi. Beyaz, bardaki `#ECEEF1` açık tondur.
Altı durum özel Xephyr ekranında çizilip dolgu pikselleri renk renk sayıldı:
şarjda yeşil, kritikte kırmızı, bekleme ve pilde beyaz, veri yokken dolgu yok.
Yeni ikili SHA-256: `482b2a97ded0d7553ba1807aee4e26ef47d4479fcbed9eb173692e70c81b0ada`. Yedek:
`~/.local/share/dwm-theme-backups/before-battery-bar-colors-*/`.

### Pilde kullanılırken koyu yeşil — 23 Kasım 2026

Kullanıcının isteğiyle pil boşalırken (pilde kullanım) çubuk dolgusu koyu
yeşil (`#1E9E3A`, `SchemeStatusBatDrain`) olur. Önceki bölümdeki "geri kalan
her durumda beyaz" kuralı daraldı; geçerli `batterycolor()` sırası:

1. **Şarjda** (`↑`): neon yeşil `#39FF14`.
2. **Adaptörde bekleme/dolu** (`•`, şarj sınırı beklemesi dahil): beyaz.
3. **Kritik** (%0–10, pilde): kırmızı.
4. **Pilde kullanım** (`↓`, ayrıca doğrulanamayan `?`): koyu yeşil.

(İlk sürümde sembol neon yeşil kalıyor, yalnız çubuk koyu yeşil oluyordu;
sembol rengi sonra çubuğa bağlandı, aşağıdaki bölüme bakın.) Sekiz durum özel Xephyr ekranında çizilip dolgu pikselleri
renk renk sayıldı (şarj, bekleme, pilde %47 ve %20, kritik, şarjda %5, `?` %62,
veri yok). Yeni ikili SHA-256: `ec3c991f9820e27a74b16443a2f32b337f3f13697f3ac838269e32d87366280a`. Yedek:
`~/.local/share/dwm-theme-backups/before-battery-drain-green-*/`.

### Sembol rengi çubukla aynı — 23 Kasım 2026

Kullanıcının isteğiyle pil sembolünün (çerçeve, uç ve içindeki şimşek/fiş/ok)
rengi, her durumda çubuk dolgusuyla aynıdır: tek kaynak `batterycolor()`.
Şarjda neon yeşil, pilde kullanımda koyu yeşil, adaptörde beklemede beyaz,
kritikte kırmızı (dolu kırmızı gövde, koyu ünlem). Veri yokken çubukta dolgu
olmadığı için sembol nötr açık gri kalır. Sekiz durumda sembolün ve çubuğun
baskın rengi piksel sayımıyla karşılaştırıldı; hepsi eşleşti. Koyu yeşil 1 px
çerçeve neon yeşile göre daha soluktur, bu seçimin doğal sonucudur.
Yeni ikili SHA-256: `fa9b9d0ec0e9ca5740d0a6757023d519b637ccf938360a6b81acd39b5dfd358c`. Yedek:
`~/.local/share/dwm-theme-backups/before-battery-symbol-tone-*/`.
