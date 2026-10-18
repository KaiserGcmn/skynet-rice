# Kaynaklar, değişiklikler ve lisanslar

Bu depo farklı lisanslara sahip bileşenleri birlikte arşivler. Tek bir üst
lisans tüm üçüncü taraf kodunu yeniden lisanslamaz; dosyalardaki telif/SPDX
başlıkları ve bileşenlerin `LICENSE` dosyaları geçerlidir.

| Bileşen | Kaynak / lisans kaydı |
| --- | --- |
| DWM 6.8, dmenu 5.4, slstatus | suckless projeleri; her dizinde MIT/X lisans metni; mevcut özel değişikliklerle alındı |
| gtkgreet-skynet | gtkgreet 0.8; `sources/gtkgreet-skynet/LICENSE` (GPLv3); yerel SKYNET görünümü |
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
`drivers/vmd/historical-build.py` önceki doğrulama işleminin kaydıdır; büyük
kaynak paketi ve çalışma dizinleri depoya dahil değildir. Tekrar derleme için
`drivers/vmd/README.md` içindeki sınırları kullan.

## Dışa aktarımdaki değişiklikler

- DWM/dmenu/slstatus `config.h` bağlantıları gerçek dosya olarak alındı.
- `.fehbg` içindeki sabit kullanıcı yolu `$HOME` oldu; Fastfetch yolu geri
  yükleme anında JSON kaçışları korunarak yeni ev dizinine uyarlanır.
- GRUB kurtarma örneğindeki makineye özgü disk UUID'si şablonla değiştirildi.
- Tarihsel bakım dosyaları çalıştırılabilir bit olmadan saklanır.
- `manifests/captured-files.json` ilk seçimin kaynak yollarını ve **orijinal**
  hashlerini kaydeder; bu dönüşümlerden sonraki yayın içeriği `SHA256SUMS` ile doğrulanır.
- Özel anahtarlar, sertifika paketleri, derlenmiş ikililer, geçmişler,
  tarayıcı profilleri, hesap verileri ve önceki `.git` geçmişleri alınmadı.

`check-public.py` yayındaki dosyalar için bilinen anahtar/token örüntülerini,
yasak dosya türlerini ve checksum listesini kontrol eder. Bu denetim genel bir
güvenlik garantisi veya tüm olası sır biçimlerinin tespiti anlamına gelmez.
