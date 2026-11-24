# Grafik girişin ASCII yedeğe düşmesi — 11 Kasım 2026

Kullanıcının belirttiği aralıklı ASCII logo, GTK logosunun karakterlere
dönüşmesi değil, `hud-greeter` başlatıcısının tuigreet yedeğidir. Eski
başlatıcı Cage/GTK'nin tek başarısız çıkışından sonra hemen bu yolu seçiyordu.
Paket sürümü uyuşmazlığı veya gerekli ikililerin yokluğu da aynı yedeği seçer.
Kurulu `gtkgreet 0.8-1+b1`, Cage ve wlroots paket doğrulamaları temizdi.

Okunan kayıtlar grafik arayüzün yakın açılışlarda başlatıldığını ve i915'in
yüklendiğini gösterdi; yedeğe geçiren Cage hatasının kendisi kaydedilmemişti.
Dolayısıyla belirli bir sürücü/GPU hatası veya açılış yarışı kesin neden olarak
saptanmış değildir. Logo çiziminin mevcut offscreen testi geçti ve çizim
kodunda değişiklik yapılmadı.

## Uygulama

`runtime/usr/local/libexec/greetd/hud-greeter`, grafik başlangıcı en fazla
üç kez dener. Yalnız başarısız denemeler arasında birer saniye bekler; sağlıklı
ilk açılışa ek bekleme ve çalışan giriş ekranına zaman aşımı koymaz. Yeniden
denemeler en fazla iki saniye ek bekleme getirir; Cage'in kendi başlangıç
süresi buna dahil değildir. Her deneme yeni, özel 0700 runtime dizini alır;
önceki dizin ve soketleri kaldırılır. Başarıda tekrar veya TTY açılışı olmaz.
Kalıcı hata halinde aynı parola isteyen tuigreet yedeği kalır. SIGTERM/HUP/INT
sonrası yeniden deneme yapılmaz.

Cage'in kendi stderr'i özel geçici dosyada toplanır; çıkınca özgün stderr'e
aktarılır ve `hud-greeter` etiketiyle mevcut syslog'a yazılır. Başarısız
denemenin çıkış kodu ve yedek seçme nedeni de kaydedilir. GTK'nin stderr'i
ayrı fd üzerinden özgün hedefine gider, bu yeni syslog yoluna alınmaz.
Parola girdisi, greetd soketi veya doğrulama yanıtları yakalanmaz. Logger
çalışmasa bile özgün hata çıktısı ve giriş yolu devam eder. Kalıcı yeni log
dosyası, servis, paket veya boot genelinde bekleme eklenmez.

Dağıtım paket sürümünü kontrol eden koruma, `_greetd` kullanıcısı, Wayland
izolasyonu, ortam temizliği, greetd/PAM ve parola politikası korunur. Greetd
yeniden başlatılmaz; açık masaüstü kapatılmaz. Yalnız başlatıcı root:root / 0755
olarak atomik değiştirilir ve sonraki normal giriş ekranında kullanılır.
Depodaki oturum komutu da makinedeki mevcut `start-x dwm-session` ile
eşitlenir; canlı makinenin oturum komutu değişmez.

## Doğrulama ve sınır

- `test_greeter_startup.py`: yedi test; gecikmesiz başarı, geçici hata,
  kalıcı hata, paket sürümü koruması, logger hatası, sonlandırma ve runtime
  oluşturma hatası. Geçici dizinler, GTK stderr ayrımı ve yedek komutu sınanır.
- Gerçek Cage 0.2.0 özel headless/pixman ekranında çalıştırıldı. İlk yapay
  hatadan sonra ikinci deneme başarılı oldu; fd 3 GTK istemcisine sızmadı,
  istemci stderr'i syslog yoluna karışmadı ve runtime dizinleri temizlendi.
  Bu testte GTK yerine sahte bir istemci kullanıldı; fiziksel DRM denenmedi.
- Beş greetd protokol testi geçti; sentetik parola reddi, yalnız açık başarı
  yanıtı, bozuk yanıtlar ve parola tamponlarının temizlenmesi korundu.
- Mevcut logo testi üç boyutta ve iki animasyon döngüsünde geçti.
- Gerçek boot'taki aralıklı hata yeniden üretilmedi. Değişiklik geçici
  başlangıç hatasından toparlanmayı sağlar; kök nedenin kesin çözüldüğü
  iddia edilmez. Tekrar ASCII görünürse yeni syslog kaydı gerçek hatayı
  ayırt etmeye yarar. Grafik motoru veya güvenlik kontrolleri kapatılmadı.

Cage'in compositor ve uygulama çıkışlarını iletmesi:
[Cage 0.2.0 kaynağı](https://github.com/cage-kiosk/cage/blob/v0.2.0/cage.c).

## Gerçek açılış kontrolü

11 Kasım 23:26:32 açılışının kayıtları sonradan okundu. GTK greeter çalışmış,
ardından kullanıcı oturumu başarıyla açılmış; yeniden deneme veya TTY yedeğe
geçiş mesajı yok. Greeter geçici runtime dizinlerini temizlemiş.
Kayıtlar tamamen boş değildir: Xwayland keycode/keysym uyarıları, wlroots
xdg_surface uyarısı ve greeter kapanışında Broken pipe mesajı bulunur.
Bu açılışta grafik login'i engellememişlerdir. Tek başarılı boot, aralıklı
sorunun her koşulda tamamen ortadan kalktığının kanıtı sayılmaz.

## Yanlış şifrede grafik giriş ekranının kapanması — 20 Kasım 2026

Belirti: 12 Kasım'dan beri her yanlış şifreden yaklaşık 3 saniye sonra
(pam_faildelay) grafik ekran kapanıp yeniden açılıyordu. Syslog'da 9 kez
`Graphical attempt N/3 exited with status 1` var ve her birinin 2,5–3,8 saniye
öncesinde bir `pam_unix(greetd:auth): authentication failure` bulunuyor. Üst
üste üç yanlış şifre, launcher'ın yeniden deneme hakkını bitirip tuigreet
yedeğine düşürüyordu. Yeniden açılan ekranda şifreyi kullanıcı adı alanına
yazmak da `user unknown` kaydına yol açıyordu.

Neden: makinedeki `devuan-source.patch` içindeki asenkron gtkgreet katmanı
(12 Kasım 11:56), doğrulama hatasından sonra `cancel_session` gönderiyor ve
`RESET_REPLY` başarılı değilse `exit(1)` yapıyordu. greetd 0.10.3, başarısız
doğrulamada oturumu zaten kendisi iptal ediyor. Bu yüzden ikinci iptal
`unable to send message: Connection refused (os error 111)` hatası döndürüyor.
Bu, VT'ye dokunmayan ayrı bir gerçek greetd örneğiyle (`vt = "none"`,
`-s /run/greetd-test.sock`) doğrulandı; ardından gelen `create_session`
normal çalışıyor.

Düzeltme (yerel yama): hata mesajı taşıyan sıfırlamalarda iptal yanıtı yok
sayılıyor; yalnız kullanıcının bastığı İptal başarısız olursa eski `exit(1)`
korunuyor. Yamanın önceki hali ve önceki ikili
`~/.local/share/dwm-theme-backups/before-greeter-fix-20261120/` altında.
Doğrulama:
- Sahte greetd ve iç içe cage ile aynı senaryoda eski ikili `exit 1` ile
  kapanıyor; yeni ikili "Login failed" gösterip ikinci denemeyi kabul ediyor.
- Gerçek izole greetd ile eski ikilide `greeter exited without creating a
  session` kaydı çıkıyor; yenisi ayakta kalıyor.

Tam yama, depo HEAD'ine ve çalışma ağacına `--fuzz=0` ile uygulanıyor.
Kurulu ikili (20 Kasım 14:47) SHA-256:
`a1c2075791cbeb9861074e60ce065b1d37eb5cb35ab3d4c08275408b0c5d5503`.


## Giriş ekranı günlüğündeki Xwayland/D-Bus hataları — 22 Kasım 2026

**Belirti:** HUD'lu giriş ekranının ilk gerçek açılışı sorunsuz geçti: yeniden
deneme ve TTY yedeği yok. Ancak her açılışta syslog'a `hud-greeter`
etiketiyle şu satırlar düşüyordu:

- xkbcomp uyarıları (`keycode 708`, `XF86KbdInputAssist…`),
- wlroots `[ERROR] A configure is scheduled for an uninitialized xdg_surface`,
- kapanışta Xwayland'ın `failed to read Wayland events: Broken pipe` satırı.

**Nedenler:**

- **Xwayland ve ek süreçler:** başlatıcı `DBUS_SESSION_BUS_ADDRESS`'i
  siliyordu. Bu yüzden GLib oturum veri yolunu `dbus-launch --autolaunch`
  ile kendisi açıyordu. Bu yol X11 istediği için Cage Xwayland'ı
  başlatıyordu. Ardından erişilebilirlik veri yolu, xdg-desktop-portal
  (-gtk) ve FUSE bağlamalı xdg-document-portal geliyordu. İç içe testte
  bu, giriş ekranı yanında **11 ek süreç, yaklaşık 136 MB** demekti.
  Giriş ekranının bunların hiçbirine ihtiyacı yok.
- **wlroots hatası:** GTK, tam ekran isteğini yüzey daha ilk kez
  işlenmeden gönderiyordu.

**Düzeltmeler:**

- `hud-greeter`: grafik deneme için
  `DBUS_SESSION_BUS_ADDRESS=disabled:` ve `NO_AT_BRIDGE=1` ayarlanır.
  TTY yedeğinden önce ikisi de silinir. Giriş ekranı greetd ve logind
  ile sistem veri yolu ya da soket üzerinden konuştuğu için etkilenmez.
- `window.c`: pencere kenarlıksızdır ve tam ekrana haritalandıktan
  (`map`) sonra geçer. Yalnızca tam ekran isteğini kaldırmak GTK'ya
  kapatma düğmeli bir başlık çubuğu çizdiriyordu; kenarlıksız pencere
  bunu engeller.

**Doğrulama:** iç içe Cage/Wayland (Xephyr 1920x1200, 96 DPI), sahte greetd.

- Ek süreç sayısı 0. Üç denemede `xdg_surface` ve xkbcomp satırı 0.
- Yerleşim değişmedi. Giriş kutusu, logo yazısı ve üst kenar piksel piksel
  aynı.
- Aşağıdaki akışlar çalıştı:
  - parmak izi geri sayımı,
  - şifre,
  - hatalı giriş, ardından `cancel_session`,
  - başarılı giriş: `start_session`, ardından çıkış kodu 0,
  - F12 test modu: STAND BY.
- `tests/test_greeter_startup.py` iki değişkeni ve TTY yedeğinde
  silinmelerini, `tests/test_greeter_hud.py` de pencere ayarını denetler.
- İşlemci ölçümü bu iç içe ortamda çok oynak (%21–36, aynı ikili). Bu
  nedenle işlemci kazancı iddia edilmez.
- Gerçek açılıştaki sonuç bir sonraki açılışta görülecek.
- Yedek: `~/.local/state/skynet-rice/backups/greeter-env-20261122/`.
