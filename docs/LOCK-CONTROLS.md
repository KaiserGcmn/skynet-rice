# Kilit ekranı donanım kontrolleri — 2 Kasım 2026

XSecureLock açıkken klavyenin ses artırma/azaltma, hoparlör mute, mikrofon mute
ve ekran parlaklığı artırma/azaltma tuşları çalışır. Görsel yardımcının altındaki
üç koyu panel ses/parlaklık yüzdesini ve mute durumunu gösterir.
3 Kasım düzeltmesi: mikrofon panelinde yüzde ve seviye çubuğu kaldırıldı;
yalnız `ON / INPUT ENABLED` veya `OFF / INPUT MUTED` gösterilir. Okunamayan
durum `-- / UNAVAILABLE` olarak belirtilir. Mikrofon kazancı değiştirilmez.

Ses ve parlaklık adımları %5'tir. Hoparlör seviyesi %0–100 ile, parlaklık
ekranın maksimumunun %5–100'ü ile sınırlanır. Sesi artırmak hoparlör mute'unu
açar; azaltmak mikrofonu veya hoparlör mute durumunu değiştirmez. Mikrofon
tuşu yalnız varsayılan girişin mute durumunu değiştirir. Varsayılan cihaz
değişimleri takip edilir; okunamayan veride son değeri doğruymuş gibi
göstermek yerine `--` / `N/A` kullanılır. Kilidi açmak seviyeleri sıfırlamaz.

Kırmızı bölümlü çubuklar, sıcak beyaz sayılar, soluk kırmızı etiketler ve
SKYNET başlığı mevcut siyah temaya eklenir. Dönen üçgen ve taranan küçük yazı
korunur. Kontroller parola penceresinden ve güç düğmelerinden ayrıdır; fareyle
sürüklenen kaydırıcı bulunmaz. 900 pikselden kısa ekranlarda kompakt panel
kullanılır; 640×720'den küçük ekranlarda ek panel çizilmez, tuşlar çalışır.

## Uygulama ve güvenlik sınırı

- `runtime/usr/local/libexec/dwm-lock`: kurulu temiz ortam başlatıcısı.
  Yalnız altı sabit `XSECURELOCK_KEY_*_COMMAND` tanımlar. Devralınan key-command
  ve auth ayarları alınmaz; paket sürümü değişince dağıtım kilidine dönüş
  kontrolü korunur.
- `runtime/usr/local/libexec/dwm-lock-controls`: Python `-I` ile çalışan
  sınırlı yardımcı. Shell çalıştırmaz; mutlak yollu `pactl` / `brightnessctl`
  komutlarına yalnız sabit eylem ve doğrulanmış sayısal değer geçirir. Key-repeat
  yığılmasını önlemek için `/run/user/UID/` altında geçici çalışma kilidi kullanır.
  Bu oturum dosyası kurulum artığı değildir; yeniden başlatmada temizlenir.
- `sources/xsecurelock-style/lock-controls.h`: XSecureLock'un saver penceresine
  yalnız çizer. Klavye/fare okumaz ve auth sonucuna erişmez. Sabit `--watch`
  çocuğunun stdout borusundan beş sınırlandırılmış sayı okur; okuma bloklamaz.
- Watcher kilit ekranıyla birlikte başlar ve biter. Ses için `pactl subscribe`
  olayları, parlaklık için salt okunur sysfs sorgusu kullanılır. Göstergeler
  yalnız veri değişince çizilir. Kalıcı bir SysVinit/systemd hizmeti eklenmez.
  Saver çocukta X11 ve diğer devralınan tanıtıcıları kapatır; parent-death
  sinyali ve normal kapanış temizliği watcher'ı sonlandırır.

PAM dosyaları, `authproto_pam`, `auth_x11_hud`, kilit çekirdeği ve oturum
başlatıcısı değiştirilmez. Parmak izi/parola, AFK kilidi tercihi, güç tuşuyla
kilit ve ekran karartma süresi korunur. Bildirimleri kilidin üstüne çıkarmak
için X11/compositor koruması kapatılmaz; Dunst veya masaüstü penceresi açılmaz.
Kilitli bilgisayardaki kişi bu altı donanım eylemini kullanabilir; bunun dışında
yeni komut, uygulama başlatma veya kilit açma yolu eklenmez.

XSecureLock'un mevcut tuş komutu desteği kullanılır:
[upstream belgeleri](https://github.com/google/xsecurelock/blob/master/README.md).
Bu desteğin başarısı giriş başarısı sayılmaz; kilit açma kararı yine auth
yardımcısının doğrulama sonucudur.

## Derleme, kurulum ve doğrulama

Mevcut `scripts/build.py` görsel yardımcıyı derler, runtime yardımcılarını
staging alanına alır. Yeni paket veya geliştirme bağımlılığı gerekmez.
Bu makinede üç hedef root:root / 0755 olarak atomik değiştirilir:
`/usr/local/libexec/{dwm-lock,dwm-lock-controls,saver-lock-style}`.
Parmak izi aşamasından sonra yalnız parola isteyen PAM yardımcısı
(`dwm-lock-fingerprint-gate`) ayrıdır; bkz. [BIOMETRIC.md](BIOMETRIC.md).
Greetd ve oturum yeniden başlatılmaz; yeni görünüm bir sonraki kilitte kullanılır.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_lock_*.py' -v
```

10 test geçti: ses sınırları, ayrı mute işlemleri, parlaklık alt sınırı,
varsayılan cihaz seçimi, veri/komut hataları, tanımsız eylem reddi, temiz
başlatıcı ortamı ve mevcut DPMS davranışı. Derleme Debian `hardening=+all` ve
`-Wall -Wextra -Werror` ile geçti; PIE, RELRO ve yürütülemez yığın doğrulandı.

Ayrı ve kimlik doğrulamalı Xephyr `:190`, özel D-Bus ve yalnız null-sink
kullanan özel PulseAudio sunucusunda altı tuş sınandı. Gerçek laptop sesi,
mikrofonu ve parlaklığı test için değiştirilmedi. Gerçek auth arayüzüne yalnız
başarısız sonuç döndüren sahte authproto bağlandı; gerçek PAM, parola veya
parmak izi kullanılmadı. Hatalı parola ve Escape sonrasında kilit/klavye/fare
yakalamaları korundu; parola arayüzü kapalıyken de medya tuşları çalıştı.
1920×1200 görüntüsü incelendi. Fiziksel Fn tuşları ve gerçek parmak iziyle
uçtan uca kullanıcı denemesi yapılmadı. Geçici kaynak, derleme ve test dosyaları
kurulum sonunda kaldırılır.

3 Kasım 2026: yalnız mikrofon panelinin çizimi güncellendi. ON, OFF ve veri
okunamayan durumları ayrı Xephyr ekranında önizlendi; sertleştirilmiş derleme
uyarısız geçti. Yalnız `saver-lock-style` ikilisi yenilendi; tuş eşlemeleri,
kontrol yardımcısı, PAM ve doğrulama ikilileri korunur.

## HUD tarzı donanım kartları — 22 Kasım 2026

Kilit ekranının altındaki ses, mikrofon ve parlaklık kutuları HUD panelleriyle
aynı dile getirildi (`sources/xsecurelock-style/lock-controls.h`):

- Başlık diğer paneller gibi: kırmızı sekme, `LOCAL CONTROLS // HARDWARE KEYS`,
  sağda `SEC 08`, kırmızı vurgulu alt çizgi.
- Her kart: köşe braketleri, vektör simge (hoparlör/mikrofon/güneş; susturulunca
  çarpı/çizgi), `01..03` dizini, büyük değer ve küçük `%`, durum rozeti
  (`OUTPUT`, `INPUT LIVE`, `BACKLIGHT`; susturulunca dolu kırmızı `MUTED`,
  veri yoksa `N/A`).
- Ses ve parlaklık: 25 hücreli seviye çubuğu, çeyrek çentikleri. Mikrofon:
  yalnız aç/kapa olduğu için `LIVE | MUTED` iki konumlu anahtar (kazanç ayarı
  varmış gibi gösterilmez).
- Alt satırda tuş ipuçları tuş başlığı kutularıyla (`- + VOLUME MUTE`,
  `MIC TOGGLE INPUT`, `- + BRIGHTNESS`).
- Çizim Cairo ile istemci tarafında yapılır ve tek `XPutImage` ile gönderilir;
  yalnız değer değişince yeniden çizilir. Konum ve boyut değişmedi; parola
  alanı ve güç düğmeleri etkilenmez. Kısa ekranlarda (yükseklik < 900) kompakt
  düzen ipucu satırını atlar.
- Yalnız `/usr/local/libexec/saver-lock-style` yenilendi; kilit çekirdeği,
  `auth_x11_hud` ve PAM değişmedi. Önceki ikili ve başlık:
  `~/.local/state/skynet-rice/backups/lock-controls-20261122/`.

Testler: `tests/test_lock_controls_panel.py` (normal, susturulmuş, veri yok,
kompakt; rozet ve seviye çubuğu renkleri).
