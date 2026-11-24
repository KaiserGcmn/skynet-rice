# Biyometrik sayaç görünümü — 23 Ekim 2026

## Parmak izi tarayıcı paneli yeniden tasarımı — 22 Kasım 2026

Kilit ekranındaki parmak izi paneli (`sources/xsecurelock-power/skynet-biometric.h`,
520×184) SKYNET HUD diliyle yeniden çizildi. Boyut, tetikleyici mesajlar,
10 saniyelik süre ve PAM akışı değişmedi; yalnız görünüm değişti.

- Başlık: kırmızı sekme, aralıklı `BIOMETRIC // IDENTITY SCAN`, sağda
  `SEC 09`; kilit HUD'undaki panellerle aynı köşe braketleri.
- Sol: noktalı ızgaralı, cetvel çentikli kare tarayıcı penceresi ve parmak ucu
  biçiminde, kesikli sırtlı loop tipi parmak izi. Okuyucu beklerken kırmızı bir
  tarama çizgisi 1,8 saniyede yukarıdan aşağı döner; dekoratiftir, tarama
  kalitesi veya ilerleme göstermez. Kilit yardımcısı zaten 200 ms'de bir
  yeniden çizdiği için ek zamanlayıcı yok; yanıp sönme yok.
- Orta: başlık, ipucu ve `READER / MODE / FALLBACK` durum satırları
  (`ARMED`, `PROCESSING`, `NO MATCH`, `TIMEOUT`, `RETRY`, `FAULT`).
- Sağ: `T-MINUS` büyük saniye sayacı; son 3 saniye parlak kırmızı. Sonuç
  durumlarında sayaç yerine durum kodu (`E01` eşleşmedi, `E02` zaman aşımı,
  `R01` yeniden dene, `E03` okuyucu hatası).
- Alt: 40 hücreli kalan süre çizgisi; sonuç durumlarında sabit tehlike şeridi
  ve `LOCK REMAINS ACTIVE`.
- Sonuç/bekleme kareleri her yeniden çizimde birebir aynıdır. Başlık libm
  kullanmaz; `auth_x11` bağlama bayrakları değişmedi.
- Panel 96 DPI Xephyr'de gerçek kilit dekoruyla (1920×1200) sınandı; en küçük
  yazı 8,5 px.

Kurulum: yalnız `/usr/local/libexec/auth_x11_hud` yenilendi. Önceki ikili,
eski başlık ve makine yaması yedeği:
`~/.local/share/dwm-theme-backups/before-fingerprint-redesign-20261122/`.
Makine katmanı `~/.local/share/skynet-rice/devuan-source.patch` yeni başlıkla
yeniden üretildi ve temiz HEAD kopyasına `--fuzz=0` ile uygulanıp doğrulandı.
Ana kilit, `authproto_pam` ve PAM ayarları değişmedi. Greeter'ın
(`sources/gtkgreet-hud/skynet-biometric.h`) paneli bu değişikliğin dışında.

Testler: `tests/test_biometric_notice.py` → `BiometricPanelTest` (libm yok,
süre çizgisi kalan süreyi izler, son saniyeler farklı renk, sonuç kareleri
yeniden çizimde değişmez).

## Gerçek ekranda alt yazının kesilmesi (96 DPI) — 21 Kasım 2026

Aşağıdaki düzeltmeden sonra da gerçek ekranda, parmak izi paneli açıkken
`FINGERPRINT OR PASSWORD / ENTER TO VERIFY` yazısının üst 2–3 piksel satırı
kesiliyordu. Xephyr testlerinde görünmüyordu.

Gerçek kilit `ffmpeg x11grab` ile kaydedilince sebep çıktı:

- Xephyr varsayılan olarak **75 DPI** açılıyor; gerçek ekran 96 DPI.
- `XSECURELOCK_FONT` 13 pt olduğu için satır yüksekliği 75 DPI'da 23 px,
  96 DPI'da 28 px (ascent 18 + descent 6 + aralık 4).
- Bu yüzden parmak izi penceresi gerçek ekranda 276 px. Ekranın tam ortasına
  (y = 600) konunca 462–738. satırları kaplıyor ve 736. satırda başlayan yazıyı
  örtüyordu. Üstte ise 25 px boşluk kalıyordu.

Düzeltme: makine katmanındaki `auth_x11.c`
(`CreateOrUpdatePerMonitorWindow`). Pencere ekranın değil, çerçevenin iç
bandının (1200 px yükseklikte 438–735; başka yüksekliklerde orantılı)
ortasına konuyor. Parmak izi penceresi 448–724, şifre penceresi 464–708
arasına düşüyor; iki yazıya da en az 10 px boşluk kalıyor.

Doğrulama:

- Tüm test betikleri artık Xephyr'i `-dpi 96` ile açıyor. Kurulu eski sürüm
  bu ayarla gerçek ekrandaki kesilmeyi birebir gösteriyor.
- Yeni sürümde üst (416–440) ve alt (731–755) yazı bantları, doğrulama
  penceresi açılmadan önceki kareyle piksel piksel aynı kalıyor. Bakılan
  durumlar: parmak izi istemi, "Failed to match fingerprint", en uzun
  "Your finger was not centered…" uyarısı, süre dolunca şifre paneli,
  Num Lock + Caps Lock açıkken karanlık ekrandan uyanma.
- İki yama katmanı da tur testinden geçti: repo `local-changes.patch` +
  `devuan-source.patch` yeni makine yamasını, o da temiz 1.9.0 kaynağına
  uygulanınca kurulu kodu birebir veriyor.

Önceki dosyalar `~/.local/state/skynet-rice/backups/lock-band-20261121/`
içindedir.

## Doğrulama penceresi yerleşimi ve Esc ipucu — 21 Kasım 2026

Sorun: parmak izi paneli açıkken çerçevenin altındaki
`FINGERPRINT OR PASSWORD / ENTER TO VERIFY` yazısı bazen yarım görünüyor,
bazen hiç görünmüyordu. Sebepler:

- XSecureLock her kilitte doğrulama penceresini rastgele ±16 px kaydırıyor
  (`XSECURELOCK_BURNIN_MITIGATION`, varsayılan 16).
- Parmak izi penceresi çerçevenin iç bandından (yazılar arasında 438–735.
  satırlar) uzundu: yükseklik 286 px, ortadan aşağı 143 px. Banda sığması için
  en fazla 135 px olabilir.
- Şifre penceresi +4 px'ten büyük kaymada yazıya değiyordu.

Düzeltme:

- `dwm-lock`: `XSECURELOCK_BURNIN_MITIGATION=0`. Pencere en fazla ~22 sn
  görünüp ekran karardığı ve arka plan zaten sabit olduğu için kaydırmanın
  yanmaya karşı faydası yoktu.
- `auth_x11.c`: parmak izi panelinin üst/alt boşluğu 12+12 px'ten 2+2 px'e
  indi. Pencere 266 px oldu; alt kenar 733. satırda kalıyor.
- `skynet-password.h`: alt satıra `ESC / BACK` ipucu eklendi. Esc'nin
  davranışı değişmedi: şifre istemini iptal edip kilit dekoruna döner, sonraki
  tuşta parmak izi yeniden başlar.

Doğrulama: gerçek `dwm-lock` ortamı, gerçek saver/arka plan ve sahte
authproto ile Xephyr'de 3 çalıştırma yapıldı. Her birinde parmak izi, süre
doldu ve şifre durumları çekildi. Karşılaştırma, aynı çalıştırmanın
doğrulamasız karesiyle yapıldı:

- Eskisinde parmak izi ekranında alt yazı 3 çalıştırmanın 2'sinde kısmen
  kapanıyordu (821 ve 1083 piksel).
- Yenisinde 9 karenin hepsinde üst (423–437) ve alt (736–749) yazı satırları
  birebir aynı.

`tests/test_lock_controls.py` launcher ortamındaki
`BURNIN_MITIGATION=0`, `FPRINT_TIMEOUT=10` ve `BLANK_TIMEOUT=12` değerlerini
sınar. Önceki dosyalar
`~/.local/state/skynet-rice/backups/lock-layout-20261121/` içindedir.

## Parmak izi süresi bitince parola akışı — 21 Kasım 2026

Sorun: parmak izi sayacı (10 sn) bitince parola paneli açılmasına rağmen
kilit hemen yeniden parmak izi istiyordu. PAM yığını doğruydu. `pamtrace`
ile ölçüldü: `pam_fprintd` 10,0 sn'de `Verification timed out`, ardından
hemen `Password:` istemi. Hata kilit arayüzündeydi; özel Xephyr ekranında
gerçek `xsecurelock-power` + `auth_x11_hud` ve sahte authproto ile yeniden
üretildi. İki yol vardı:

1. Parmak izi beklenirken basılan tuşlar (ör. Enter) arabellekte kalıyordu.
   Parola istemi açıldıktan 3 ms sonra boş parola olarak gönderiliyordu. PAM
   başarısız oluyor, yeni deneme yine parmak iziyle başlıyordu.
2. Karartma sayacı (12 sn) son tuştan sayıyordu ve parmak izi beklemesi bunun
   10 sn'sini yiyordu. Parola paneli yalnız ~2 sn görünüp ekran kararıyordu.
   Ekranı uyandıran Enter da boş parola olarak gönderiliyordu; sonuç aynıydı.

Düzeltme (makine katmanı, kilit yaması):

- `auth_x11.c`: parmak izi isteminden sonra gelen ilk parola/kullanıcı
  isteminden önce, bu sırada beklemede kalan tuşlar atılır
  (`DiscardTypeahead`). Yalnız siler, PAM'e hiçbir yanıt vermez.
- `main.c`: kararmış ekranı uyandıran tuş yalnız uyandırır. Parola alanına
  yazılmaz ve F11/F12 güç eylemi tetiklemez; bu, fare tıklaması için zaten
  geçerli olan kuralın aynısıdır. Ses/parlaklık tuşları çalışmaya devam eder.
- `main.c`: yeni bir doğrulama penceresi açıldığında karartma en erken
  `XSECURELOCK_FPRINT_TIMEOUT + XSECURELOCK_BLANK_TIMEOUT` (10 + 12 = 22 sn)
  sonra olur. Parola paneline tam 12 sn kalır; tuşlar bu süreyi kısaltmaz.
  Doğrulama yokken saver üzerindeki 12 sn karartma aynıdır.

PAM, `authproto_pam`, parmak izi deneme sayısı/süresi, parola tamponu,
kilidin açılma koşulu ve güç tuşu politikası değişmedi.

Doğrulama (Xephyr, `FPRINT_TIMEOUT=4`):

- Parmak izi sırasında basılan Enter atıldı. Sonra yazılan 3 karakterli
  parola tek yanıt olarak geldi.
- 14. saniyede ekran hâlâ açıktı (eskisi 12'de kararıyordu).
- Karartma ~16. saniyede oldu. Uyandıran Enter yazılmadı. Sonra yazılan 2
  karakter geldi.

Temiz XSecureLock 1.9.0 (SHA-256 doğrulanmış) + yeni `local-changes`, test
edilen kaynağın aynısını verdi. HEAD + yeni `devuan-source.patch` ise yeni
`local-changes`'ı birebir verdi; diğer bölümler bayt bayt aynı. Derlemede
`GIT_VERSION=1.9.0-local-power` kullanıldı. Önceki ikililer ve yama
`~/.local/state/skynet-rice/backups/lock-fprint-flow-20261121/` içindedir.

## Şifre paneli (ACCESS KEY) — 21 Kasım 2026

Kilit ekranındaki parola isteği, parmak izi paneliyle aynı tasarım dilinde
520×168 px bir panelde gösterilir: köşeli kırmızı çerçeve, başlıkta
`ACCESS KEY / 02`, saat/tarih ve `SKYNET`; solda kilit simgesi ve her yazılan
karakterde bir bölümü yanan 28 parçalı halka; sağda `OPERATOR` + kullanıcı adı,
PAM isteminin metni (ör. `Password:`) ve giriş alanı. Yıldızların yerine her
karakter için kırmızı bir elmas, sonda yanıp sönen blok imleç çizilir; 22'yi
aşan girişte `+N` gösterilir. Altta `ENTER / VERIFY`, `ESC / BACK` ve
`CTRL-U / CLEAR` ipuçları vardır. Klavye düzeni / Caps Lock satırı panelin altında aynen kalır.
Saat panelin başlığına taşındığı için doğrulama penceresi kısaldı ve çerçevedeki
`FINGERPRINT OR PASSWORD` yazısını artık kesmez.

Panel yalnız `XSECURELOCK_PASSWORD_PROMPT=asterisks` parola isteminde
kullanılır. Çizim işlevi parolayı değil, yalnız ekranda zaten görünen maskeli
karakter sayısını ve imlecin yanıp sönme durumunu alır; bu değerler tek
`DisplayMessage` çağrısı sonunda sıfırlanır. Kullanıcı adı / görünür girişli
istemler, hata ve bilgi mesajları ile parmak izi paneli eskisi gibi çizilir.
`Prompt` girdi işleme, parola tamponu, mlock/explicit_bzero, PAM protokolü,
zaman aşımları ve çıkış kodu değişmedi.

Kaynak: [`skynet-password.h`](../sources/xsecurelock-power/skynet-password.h).
Makine katmanı `~/.local/share/skynet-rice/devuan-source.patch` içindeki
kilit yaması bu başlığı ve `auth_x11.c` bağlantısını içerecek şekilde yeniden
üretildi; temiz depo + katman + SHA-256 doğrulanmış XSecureLock 1.9.0 kaynağı
`--fuzz=0` ile derlenen kaynakla birebir eşleşti. Önceki binary ve yama
`~/.local/state/skynet-rice/backups/lock-password-20261121/` içindedir.
Yalnız `/usr/local/libexec/auth_x11_hud` root:root 0755 olarak atomik
yenilendi; `xsecurelock-power`, `authproto_pam`, `saver-lock-style` ve
`dwm-lock` hashleri korundu. PIE, full RELRO ve yürütülemez yığın
doğrulandı; derleme yalnız upstream'in mevcut strncpy uyarısını verdi.

Doğrulama: `tests/test_password_panel.py` çizimin panel sınırları dışına
taşmadığını (0–taşma karakter sayısı, çok uzun ad/istem/saat, NULL değerler),
aynı maskeli durumun aynı görüntüyü verdiğini ve API'nin parola metni
almadığını sınar. Özel Xephyr ekranında xsecurelock pencere hiyerarşisi ve
yalnız test için yazılmış sahte authproto ile eski ve yeni binary aynı
girdilerde aynı çıkış kodlarını verdi: yanlış parola 1, doğru parola 0,
Escape 1, Backspace sonrası doğru parola 0, eksik parola 1; Ctrl-U sonrası
doğru parola 0. Gerçek oturum kilitlenmedi; gerçek PAM, parola veya sensör
kullanılmadı.

## Parmak izi sonuç paneli — 3 Kasım 2026

Parmak izi eşleşmediğinde aynı 520×184 çerçevede kırmızı çarpı rozeti,
“PRINT NOT MATCHED” ve “LOCK REMAINS ACTIVE” gösterilir. Süre aşımı
“SCAN TIMED OUT”, okuma yönlendirmesi “ADJUST YOUR FINGER”, bilinen sensör
hatası “READER ERROR” görünümünü seçer. Yeni tarama mesajında normal sayaç
geri gelir. Metinler mevcut İngilizce SKYNET arayüzüne uygundur.

Sınıflandırma yalnız kurulu pam_fprintd 1.94.5'in bilinen İngilizce
mesajlarıyla tam eşleşir; bilinmeyen/parola hataları eski genel görünümde
kalır. Sensörün özgün mesajı panelin üstünde korunur. Paket kaynağındaki
`send_err_msg`/`send_info_msg` yolları kontrol edildi: süre aşımı INFO,
eşleşmeme ve yeniden konumlandırma ERROR olarak iletilir. Bu ayrım sınandı.
Yerel sayaç sıfıra indi diye başarısızlık üretilmez.

Değişiklik yalnız `DisplayMessage` çizimini ve bu mesajlarda görünüm
sayacının durmasını kapsar. `Prompt`, protokol yanıtları, parolanın bellekten
silinmesi, PAM deneme sınırları, mevcut bir saniyelik mesaj beklemesi ve
çıkış durumuyla kilit açma kararı korunur. İlave bekleme veya giriş yolu
eklenmedi. Retry yönlendirmesi yeni mesaj gelene kadar ekranda kalabilir;
doğrulama hizmeti aynı sırada çalışmaya devam eder.

`test_biometric_notice.py`: bilinen sensör mesajları, genel parola hatası,
bilinmeyen mesaj/null için geri dönüş ve çizim sınırları geçti. Özel Xephyr
ve sahte authproto ile eşleşmeme → yeniden tarama → yerleştirme uyarısı →
INFO süre aşımı → sensör hatası → genel hata → maskeli parola geçişleri
sınandı. Hata mesajı eski sayaçla üzerine yazılmadı; başarısız parola ve
Escape sonrası kilit/klavye/fare yakalamaları korundu. Yalnız başarılı
sahte authproto sonucu kilidi açtı. Gerçek kullanıcı oturumu, PAM ve sensör
bu testte kullanılmadı.

Temiz kaynak üzerinde iki yama katmanı sıfır fuzz ile yeniden uygulandı ve
derlenen kaynakla eşleşti. PIE/full RELRO/yürütülemez yığın korundu.
Yalnız `auth_x11_hud` atomik root:root 0755 yenilenir; PAM, ana kilit,
başlatıcı, authproto ve dekor/medya yardımcılarının hashleri korunur.

## Kilit paneli yenilemesi — 3 Kasım 2026

Yalnız kilit ekranının parmak izi paneli yenilendi. Greetd parola ile giriş
politikasını korur; GTK panelinin çizimi değiştirilmedi. Aşağıdaki 23 Ekim
notları önceki ortak tasarımın geçmişidir.

Yeni panel 520×184 px: siyaha yakın zemin, ince koyu kırmızı çerçeve, belirgin
köşe işaretleri, sıcak beyaz metin ve büyük saniye göstergesi. Yerel Cairo
çizimi parmak izi simgesini, 28 parçalı dairesel sayacı ve 30 parçalı yatay
sayacı oluşturur. İki gösterge de kalan süreyi temsil eder; okuma kalitesi
veya eşleşme yüzdesi göstermez. Son üç saniye parlak kırmızıdır, yanıp sönmez.
Sıfırda “WAITING FOR RESULT” gösterilir; süre dolması başarı/başarısızlık
kararı üretmez. Hangi parmağın istendiğini belirten PAM mesajı korunur.

Biyometrik görünümde yinelenen kullanıcı başlığı ve tarih satırı kaldırıldı;
panel mevcut SKYNET başlığı ve dış çerçevenin içine sığar. Parola ekranındaki
başlık, saat/tarih, maskeli giriş ve klavye göstergeleri korunur.

Çizimin okunabilir kaynağı
[`skynet-biometric.h`](../sources/xsecurelock-power/skynet-biometric.h).
Makinede yeniden derleme için `devuan-source.patch` içindeki kilit yaması da
aynı başlık ve `DisplayMessage` yerleşimiyle güncellendi. Diğer makine
katmanları korunur. Temiz kaynakta iki yama katmanı `--fuzz=0` ile uygulandı;
derlenen kaynakla birebir eşleşti. `DisplayMessage` dışındaki auth kaynak
kodunun önceki sürümle aynı olduğu doğrulandı. Sayaç süresi 10 saniyedir.

Yalnız `/usr/local/libexec/auth_x11_hud` root:root, 0755 olarak atomik
kurulur. PAM, authproto_pam, ana kilit programı, başlatıcı, logo/dekor ve
medya kontrol yardımcıları hash ile korunur. Servis veya oturum yeniden
başlatılmaz; görünüm bir sonraki kilitte kullanılır. Yeni paket, servis veya
medya oynatımı eklenmez.

Özel, kimlik doğrulamalı ve TCP dinlemeyen Xephyr ekranında sahte authproto
ile sıfırda kilidin korunması, hatalı girişin reddi, Escape, klavye/fare
yakalamaları, maskeli parola geri dönüşü ve yalnız başarı yanıtıyla açılma
sınandı. Bu test gerçek PAM/sensör veya kullanıcı parolasını kullanmaz;
canlı masaüstü kilitlenmez. PIE, full RELRO ve yürütülemez yığın doğrulandı.
Derleme yalnız upstream'in mevcut üç strncpy uyarısını verdi.

İlk tam ekran yerleşimi ve 10/5/2/0 saniyelik panel çizimleri incelendi.
Gizli Xephyr ana penceresinde sonraki ekran görüntülerinde bazı sabit dekor
alanları eksik yakalandı; aynı durum eski kurulu auth yardımcısıyla da
tekrarlandı. Bu gözlem yeni panelin doğrulama davranışını etkilemedi;
gerçek kilit ekranında uzun süreli görsel test yapıldığı iddia edilmez.

2 Kasım 2026 tercihi: parmak izi yalnız kilit ekranında etkin bırakıldı.
Greetd artık parola ile giriş yapar; bu bölümde anlatılan greetd parmak izi
paneli mevcut giriş akışında gösterilmez. Kayıtlı parmaklar ve kilit ekranının
paneli korunur. Güncel politika ve testler [SECURITY.md](SECURITY.md) içindedir.

Greetd/GTK ve XSecureLock parmak izi bekleme paneli aynı SKYNET tasarımını
kullanır: yerel çizilen parmak izi simgesi, büyük saniye rakamı, yirmi kırmızı
bölüm ve ince köşe çerçeveleri. Son üç saniye daha parlaktır; yanıp sönme yoktur.
Süre sıfırda sabitlenir ve sonraki ekranı doğrulama hizmetinin yanıtı belirler.
Yeni medya dosyası, arka plan işlemi veya paket kurulmadı.

## Yanlış paroladan sonra yalnız parola — 23 Kasım 2026

Sorun: kilit ekranında yanlış parola girince parmak izi taraması tekrar
başlıyordu. Neden: XSecureLock her başarısız denemeden sonra yeni bir PAM işlemi
başlatır ve `dwm-fingerprint` yığını her işlemde önce `pam_fprintd` çalıştırır.
Kilit arayüzü veya ikilileri değişmedi; çözüm yalnız PAM katmanındadır.

Yığın (`profiles/debian/rootfs/etc/pam.d/dwm-fingerprint`):

```
auth [success=1 default=ignore] pam_exec.so quiet /usr/local/libexec/dwm-lock-fingerprint-gate check
auth sufficient pam_fprintd.so max-tries=3 timeout=10
auth optional pam_exec.so quiet /usr/local/libexec/dwm-lock-fingerprint-gate mark
@include common-auth
auth optional pam_exec.so quiet /usr/local/libexec/dwm-lock-fingerprint-gate clear
```

- `mark`: parmak izi aşaması başarısız olup parolaya düşüldüğünde
  `/run/user/<uid>/dwm-lock-password-only` dosyasının zamanı yenilenir.
- `check`: bu kayıt 120 saniyeden yeniyse yalnız `pam_fprintd` satırı atlanır
  (`success=1`); sonuç parola yığınına kalır. Kayıt yoksa, eskiyse, bozuksa veya
  yardımcı çalışmazsa (`default=ignore`) eski sıra aynen sürer: önce parmak izi.
- `clear`: parola ile başarılı girişte kayıt silinir; sonraki kilit yine
  parmak iziyle başlar. Parmak iziyle başarılı girişte kayıt zaten yoktur.

Beklenen akış: ilk denemede parmak izi (10 sn) → parola → yanlışsa yeniden
denemede yalnız parola. İki dakikadan uzun süre sonra gelinirse parmak izi yeniden
sorulur. Bu 120 saniyede parmak izi kasıtlı olarak kapalıdır; süre
`--ttl` ile PAM satırından değiştirilir.

Yardımcı kimseyi doğrulamaz ve erişim vermez. Dizin kullanıcıya ait ve
yalnız kullanıcı tarafından yazılabilir olmalıdır; kayıt dosyası simgesel bağ
olamaz, 0600 açılır ve geleceğe ait zaman damgasına güvenilmez. Parola
yığınına (`common-auth`) dokunulmaz.

Doğrulama:

- `tests/test_lock_fingerprint_gate.py` (16 test): süre aşımı, yenileme,
  temizleme, simgesel bağ, paylaşılan dizin, eksik dizin ve PAM satırlarının
  sırası/denetimi (yardımcı satırları `sufficient`/`done` olamaz).
- Gerçek PAM motorunda, geçici ve sonradan silinen bir servisle (`pam_fprintd`
  ve `pam_unix` yerine kayıt tutan yer tutucular): ilk deneme
  parmak izi → parola; sonraki iki deneme yalnız parola; kayıt 121 sn eskitilince
  parmak izi geri geldi; doğru parolada kayıt silindi ve sonraki kilit parmak
  iziyle başladı; parmak izi başarısında parola sorulmadı; yardımcıya erişim
  kapatılınca (`chmod 000`) normal sıra korundu.
- Canlı `dwm-fingerprint` hizmeti, gerçek `pam_fprintd` ve `pam_unix` ile bilerek
  yanlış parolayla 3 kez denendi (sensöre dokunulmadı): ilk deneme 13,3 sn
  (`Place your right index finger…` → `Verification timed out` → `Password:`),
  ikinci ve üçüncü yalnız `Password:` (≈2 sn, `pam_unix` hata gecikmesi).
  Gerçek oturum kilitlenmedi; parola kaydedilmedi.

Günlükte her kilit denemesinin ilkinde `auth.log` içinde
`pam_exec(dwm-fingerprint:auth): ...dwm-lock-fingerprint-gate failed: exit code 1`
satırı görünür. Bu hata değildir: `check` kayıt bulamadığında 1 döner ve
`pam_exec` bunu her zaman yazar. Kayıt tazeyken (yanlış paroladan sonraki
denemeler) satır yazılmaz, parmak izi atlanır.

Bilinen sınır: parmak izi taraması (10 sn) aynı zamanda doğal bir bekleme
sağlıyordu. Atlandığında parola denemeleri yalnız `pam_unix` hata gecikmesiyle
(≈2 sn) ilerler; `pam_faillock` gibi bir kilitleme yoktu ve eklenmedi.

Önceki dosya `~/.local/state/skynet-rice/backups/lock-fprint-gate-20261123/`
içindedir. Yardımcı root:root 0755, PAM dosyası root:root 0644 olarak atomik
kuruldu; kilit ekranı bir sonraki kilitte yeni yığını kullanır. Geri almak için
yedekteki `dwm-fingerprint.before` dosyası `/etc/pam.d/dwm-fingerprint` olarak
geri konur.

## Kaynak ve derleme

Bu depo Debian kaynak görüntüsüdür. Makinedeki mevcut Devuan değişiklikleri
`~/.local/share/skynet-rice/devuan-source.patch` içinde tutulur. Bu yama DWM
ayarları, greetd asenkron doğrulama/sayaç entegrasyonu ve XSecureLock yamasının
makineye özgü sürümünü içerir; bu işlem yalnızca sayaç çizimini güncelledi.
Yamayı deponun geçici kopyasında `patch --batch --fuzz=0 -p1` ile uygulayın.
Asıl depoya tekrar tekrar uygulamayın.

- GTK: `sources/gtkgreet-hud` içinde `make`; yeni `skynet-biometric.h`
  dosyası depo kaynağıdır. Makine yaması `window.c`/`window.h` entegrasyonunu sağlar.
- Kilit arayüzü: SHA-256 doğrulanmış XSecureLock 1.9.0 kaynağına, Devuan
  katmanı uygulandıktan sonraki `sources/xsecurelock-power/local-changes.patch`
  uygulanır. Bu iç yama aynı çizim başlığını da içerir.
- XSecureLock: `autoreconf -fi`; `./configure --prefix=/usr/local
  --libexecdir=/usr/libexec --without-pam
  --with-default-authproto-module=authproto_pam
  --with-default-auth-module=auth_x11 --without-pandoc`; `make -j2 auth_x11`.
  Debian hardening CFLAGS/CPPFLAGS/LDFLAGS ve `-D_DEFAULT_SOURCE` kullanılır.
  Yalnızca `auth_x11` çıktısı `/usr/local/libexec/auth_x11_hud` olarak kurulur.
  Ana kilit programını ve PAM yardımcısını bu görünüm için yeniden kurmayın.
- `libcairo2-dev` doğrudan derleme bağımlılığıdır; GTK üzerinden zaten kuruluydu.
- Aktif GTK stili `/etc/greetd/gtkgreet-hud.css`; eski `fingerprint-countdown` ve
  `fingerprint-meter` kuralları yerine `#fingerprint-panel { background:
  transparent; }` kullanılır. Panel kendi renklerini çizer.

## Doğrulama

Görünmeyen bir ana pencere altında özel Xephyr ekranı kullanıldı. Hem GTK/X11
hem Cage/Wayland üzerinde sahte greetd IPC ile geri sayım, maskeli parola,
hatalı girişin reddi ve yalnızca başarı yanıtından sonra `start_session`
gönderilmesi sınandı. Kilidin görsel yardımcısı sahte `authproto` üzerinden
süre bitimi, parola yanıtı ve başarısız/başarılı çıkış durumlarıyla sınandı.
Mevcut kilit dekoruyla yerleşim ve her iki arayüzün ekran görüntüleri incelendi.

Gerçek oturum kilitlenmedi/yeniden başlatılmadı; gerçek parola, sensör veya
parmak izi kayıtları kullanılmadı. PAM, `authproto_pam`, ana kilit programı,
başlatıcılar ve mevcut logo yardımcısının SHA-256 değerleri korundu. GTK
`actions.c`, `proto.c`, `proto.h`, `gtkgreet.c` ve logo çizimi değişmedi.
10 saniyelik süre, PAM yanıtları ve parola geri dönüşü aynı kaldı.

Derleme başarılı; XSecureLock upstream `strncpy` satırındaki üç mevcut derleyici
uyarısı dışında yeni derleyici uyarısı yok. Yeni yama özgün arşive ve tüm
makine katmanı temiz kaynak kopyasına `--fuzz=0` ile uygulanarak doğrulandı.
Kurulum servisleri yeniden başlatmaz; yeni görünüm ekranlar sonraki açıldığında
kullanılır. Geçici derleme, test, indirme ve ekran görüntüleri temizlenir.
