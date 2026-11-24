# Kaynaklar, değişiklikler ve lisanslar

Bu depo farklı lisanslara sahip bileşenleri birlikte arşivler. Tek bir üst
lisans tüm üçüncü taraf kodunu yeniden lisanslamaz; dosyalardaki telif/SPDX
başlıkları ve bileşenlerin `LICENSE` dosyaları geçerlidir.

| Bileşen | Kaynak / lisans kaydı |
| --- | --- |
| DWM 6.8, dmenu 5.4, slstatus | suckless projeleri; her dizinde MIT/X lisans metni; mevcut özel değişikliklerle alındı |
| gtkgreet-hud | gtkgreet 0.8; `sources/gtkgreet-hud/LICENSE` (GPLv3); yerel SKYNET görünümü |
| XSecureLock | 1.9.0; `sources/xsecurelock-power/LICENSE`; yerel yama ayrı |
| xwinwrap | Novell telif/izin metni `xwinwrap.c` başında; yerel kaynak README'si upstream bilgilerini içerir |
| rtw88 | [lwfinger/rtw88](https://github.com/lwfinger/rtw88), commit `a56bcd26e770257612a0803249cbd4095fc6feca`; dosya bazında SPDX lisansları |
| ExpertBook LED / VMD | Linux modülü kaynaklarındaki lisans başlıkları; GPL-2 metni `licenses/` altında |
| Yerel yardımcılar/görünüm varlıkları | Kullanılan sistemden seçilerek alındı; mevcut telif/marka hakları korunur |

gtkgreet özgün arşivi:
`https://deb.debian.org/debian/pool/main/g/gtkgreet/gtkgreet_0.8.orig.tar.gz`
SHA-256: `e5c70219da191a60e2e009412603e05c36cee15bbbf7657dbbeaa1d21a692873`.

XSecureLock özgün arşivi:
`https://deb.debian.org/debian/pool/main/x/xsecurelock/xsecurelock_1.9.0.orig.tar.gz`
SHA-256: `6e8df4d804e388499e7a9116161a0355034d2ebb61471291383875be515e8025`.

VMD kaynağı Debian `linux-source-6.12_6.12.113-1_all.deb` paketinden:
paket SHA-256 `6ad4a0316ddefced87cef8cd9a25a268e0cdfe0a10adc5148401f49f90b336b5`.
Upstream düzeltme commit'i `b43750456515c52c5b0b714f2a2ea84d6f940e19`.
DKMS paketinin kaynağı (`drivers/vmd/pristine/vmd-6.12.117.c`) Debian
`linux-source-6.12_6.12.117-1_all.deb` paketinden alındı. Paket SHA-256
`9141325315c7f1eca682113d185a8c77c82814aa6e32f7e127e61d6106403835`, APT
kaydıyla doğrulandı.
`drivers/vmd/historical-build.py` önceki doğrulama işleminin kaydıdır; büyük
kaynak paketi ve çalışma dizinleri depoya dahil değildir. Tekrar derleme için
`drivers/vmd/README.md` içindeki sınırları kullan.

## Dışa aktarımdaki değişiklikler

- DWM/dmenu/slstatus `config.h` bağlantıları gerçek dosya olarak alındı.
- İlk dışa aktarımda `.fehbg` içindeki sabit kullanıcı yolu `$HOME` oldu;
  bu eski başlatıcı sonradan kaldırıldı. Fastfetch logosu ve ona ait sabit
  kullanıcı yolu 29 Ekim 2026'da kaldırıldı; yalnız bilgi paneli korunur.
- GRUB kurtarma örneğindeki makineye özgü disk UUID'si şablonla değiştirildi.
- Tarihsel bakım dosyaları çalıştırılabilir bit olmadan saklanır.
- `manifests/captured-files.json` ilk seçimin kaynak yollarını ve **orijinal**
  hashlerini kaydeder; bu dönüşümlerden sonraki yayın içeriği `SHA256SUMS` ile doğrulanır.
  28–29 Ekim 2026'da kaldırılan eski init ve Fastfetch logo dosyalarının kayıtları da bu listeden çıkarıldı;
  kalan kayıtların orijinal hashleri değiştirilmedi.
- Özel anahtarlar, sertifika paketleri, derlenmiş ikililer, geçmişler,
  tarayıcı profilleri, hesap verileri ve önceki `.git` geçmişleri alınmadı.

`check-public.py` yayındaki dosyalar için bilinen anahtar/token örüntülerini,
yasak dosya türlerini ve checksum listesini kontrol eder. Bu denetim genel bir
güvenlik garantisi veya tüm olası sır biçimlerinin tespiti anlamına gelmez.

## snixembed yerel düzeltmesi — 3 Kasım 2026

`sources/snixembed`, Debian arşivinden SHA-256 doğrulamalı upstream 0.3.3
kaynağı ve SKYNET tepsi düzeltmeleridir. ISC lisansı korunur. Kaynak URL,
özet, derleme ve değişiklikler `sources/snixembed/README.local.md` ve
`docs/TRAY.md` içinde kayıtlıdır. İkili/derleme araçları depoya alınmaz.

## Küre kara verisi — 22 Kasım 2026

`sources/xsecurelock-style/skynet-globe-land.h`, Natural Earth 1:50m kara
poligonlarından (`ne_50m_land.geojson`, nvkelso/natural-earth-vector,
kamu malı) `render-globe-land.py` ile üretilmiş 1024×512 kara maskesidir.
İndirilen GeoJSON'un SHA-256 özeti: `e874b27a51d146452be360cafb3cc50c86001074a67d534113e6534682f9826b`. GeoJSON depoya alınmadı;
yalnız üretilen başlık dosyası tutulur. Ayrıntı: [LOGO.md](LOGO.md).
