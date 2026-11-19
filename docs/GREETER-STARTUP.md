# Grafik girişin ASCII yedeğe düşmesi — 11 Kasım 2026

Kullanıcının belirttiği aralıklı ASCII logo, GTK logosunun karakterlere
dönüşmesi değil, `skynet-greeter` başlatıcısının tuigreet yedeğidir. Eski
başlatıcı Cage/GTK'nin tek başarısız çıkışından sonra hemen bu yolu seçiyordu.
Paket sürümü uyuşmazlığı veya gerekli ikililerin yokluğu da aynı yedeği seçer.
Kurulu `gtkgreet 0.8-1+b1`, Cage ve wlroots paket doğrulamaları temizdi.

Okunan kayıtlar grafik arayüzün yakın açılışlarda başlatıldığını ve i915'in
yüklendiğini gösterdi; yedeğe geçiren Cage hatasının kendisi kaydedilmemişti.
Dolayısıyla belirli bir sürücü/GPU hatası veya açılış yarışı kesin neden olarak
saptanmış değildir. Logo çiziminin mevcut offscreen testi geçti ve çizim
kodunda değişiklik yapılmadı.

## Uygulama

`runtime/usr/local/libexec/greetd/skynet-greeter`, grafik başlangıcı en fazla
üç kez dener. Yalnız başarısız denemeler arasında birer saniye bekler; sağlıklı
ilk açılışa ek bekleme ve çalışan giriş ekranına zaman aşımı koymaz. Yeniden
denemeler en fazla iki saniye ek bekleme getirir; Cage'in kendi başlangıç
süresi buna dahil değildir. Her deneme yeni, özel 0700 runtime dizini alır;
önceki dizin ve soketleri kaldırılır. Başarıda tekrar veya TTY açılışı olmaz.
Kalıcı hata halinde aynı parola isteyen tuigreet yedeği kalır. SIGTERM/HUP/INT
sonrası yeniden deneme yapılmaz.

Cage'in kendi stderr'i özel geçici dosyada toplanır; çıkınca özgün stderr'e
aktarılır ve `skynet-greeter` etiketiyle mevcut syslog'a yazılır. Başarısız
denemenin çıkış kodu ve yedek seçme nedeni de kaydedilir. GTK'nin stderr'i
ayrı fd üzerinden özgün hedefine gider, bu yeni syslog yoluna alınmaz.
Parola girdisi, greetd soketi veya doğrulama yanıtları yakalanmaz. Logger
çalışmasa bile özgün hata çıktısı ve giriş yolu devam eder. Kalıcı yeni log
dosyası, servis, paket veya boot genelinde bekleme eklenmez.

Dağıtım paket sürümünü kontrol eden koruma, `_greetd` kullanıcısı, Wayland
izolasyonu, ortam temizliği, greetd/PAM ve parola politikası korunur. Greetd
yeniden başlatılmaz; açık masaüstü kapatılmaz. Yalnız başlatıcı root:root / 0755
olarak atomik değiştirilir ve sonraki normal giriş ekranında kullanılır.
Depodaki oturum komutu da makinedeki mevcut `start-x skynet-session` ile
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
