# Greetd ve kilit ayarları

2 Kasım eklemesi: [kilit ekranı donanım kontrolleri](LOCK-CONTROLS.md) altı sabit
medya/parlaklık tuşunu etkinleştirir. Güncel başlatıcıya bu sınırlı eşlemeler
eklenmiştir; PAM ve kilit/auth ikilileri aynı kalır.

## Güncel giriş ve kilit tercihi — 2 Kasım 2026

Kullanıcının isteğiyle otomatik AFK kilidi kapatıldı. Oturum başlatıcısı artık
`xset s 0 0` çalıştırır. `xss-lock` ve elogind'in `HandlePowerKey=lock` ayarı
korunur: güç tuşu, elogind Lock isteği ve mevcut elle kilitleme kısayolu aynı
kilit ekranını açar. Masadan ayrılırken kilitleme kullanıcı tarafından yapılır.
Masaüstünde DPMS kapalı kalır; kilit ekranının kendi ekran karartma ayarı değişmez.

Greetd PAM dosyasındaki `auth substack skynet-fingerprint` satırı
`auth substack common-auth` olarak değiştirildi. Giriş artık standart parola
doğrulamasını kullanır. Hata gecikmesi, nologin kontrolü, grup, hesap/parola/oturum
politikaları ve anahtarlık modülleri korunur. Parmak izi yalnız kilit ekranının
`skynet-fingerprint` PAM hizmetinde kalır; bu dosya, kilit başlatıcısı ve parmak
izi kayıtları değiştirilmedi. GTK/TTY greeter ikilileri yeniden derlenmedi;
parmak izi PAM istemi gelmediği için girişte biyometrik sayaç açılmaz.

Kurulum öncesi yeni greetd politikası ayrı, root erişimli geçici PAM dizininde
sınandı. Geçersiz kimlik reddedildi; kullanıcının terminalde girdiği doğru
parola ve hesap kontrolü geçti. Parola kurulum betiğine veya dosyaya alınmadı;
yerleşik PAM terminal konuşması kullanıldı. Başarılı testten sonra iki hedef
dosya atomik kuruldu; mevcut masaüstü ve greetd yeniden başlatılmadı.

Canlı masaüstünde kilit durumunun kapalı olduğu doğrulanıp yalnız zaman aşımı
değiştirildi; ekran koruyucu zorla sıfırlanmadı. `xss-lock` aynı süreç olarak
kaldı. Ayrı Xephyr ve ayrı sahte login1 hizmetiyle eski bir saniyelik kontrol
eşiğinin kilidi başlattığı, sıfır eşikte AFK kilidinin gelmediği, elogind Lock
sinyali ve `xset s activate` ile kilidin hâlâ başlatıldığı doğrulandı.
Gerçek güç düğmesine basılmadı ve masaüstü test amacıyla kilitlenmedi.

Greetd dosyası `profiles/debian/rootfs/etc/pam.d/greetd`, oturum başlatıcısı
`runtime/usr/local/bin/skynet-session` içinde saklanır. Bunlar sistem dosyalarıdır;
`restore-home.py` tarafından kurulmaz. Başka dağıtıma aktarırken oradaki
`common-auth` ve `login` PAM zincirleriyle birlikte değerlendirilmelidir.

Regresyon testi `tests/test_manual_lock.py` içindedir. Normal test keşfi özel
ekran verilmediğinde bu testi atlar. Önceden hazırlanmış ayrı bir X sunucusunda:

```sh
PYTHONDONTWRITEBYTECODE=1 SKYNET_LOCK_TEST_DISPLAY=:190 \
python3 -m unittest discover -s tests -p test_manual_lock.py -v
```

Test ayrı D-Bus ve sahte kilitleyici kullanır; ekran numarası 90'dan küçükse
çalışmayı reddeder. Özel X sunucusunun XAUTHORITY değeri ortamda verilmelidir.

Kaynaklar: [xss-lock olay kaynakları](https://manpages.debian.org/trixie/xss-lock/xss-lock.1.en.html),
[PAM substack](https://manpages.debian.org/trixie/libpam-runtime/pam.d.5.en.html).

## 24 Ekim 2026 güvenlik incelemesi — tarihsel kayıt

Bu işlem, güvenlik incelemesinde önceliklendirilen iki düzeltmeyi uygular:
greeter parola isteğinin bellekte kalması ve hareketsizlikte otomatik kilit.

## Parola isteğinin ömrü

`sources/gtkgreet-skynet/proto.c` istekleri artık sınırları belirli tek bir
geçici tamponda kodlar. İstek yapısı gönderim öncesinde, gönderim tamponu ise
yanıt beklenmeden önce temizlenir; hata yolları da temizleme yapar. JSON-C içinde
istek/parola kopyası oluşturulmaz. Gönderilen GTK giriş kutusu ve makineye özgü
asenkron katmanın ara kopyaları da temizlenir. Bu, tüm işlem veya üçüncü taraf
kütüphane belleğinin parolasız olduğu anlamına gelmez.

Başarı kararını greetd/PAM verir. Sayaç, logo veya bağlantı hatası oturum
başlatmaz. PAM dosyaları, parmak izi kayıtları, kilit çekirdeği ve doğrulama
yardımcıları bu işlemde değiştirilmez. Kurulum hedefi yalnız yeni GTK ikilisidir;
etkin masaüstünü kapatmadan sonraki giriş ekranı açılışında kullanılır.

## Beş dakikalık otomatik kilit — 24 Ekim'deki ayar

`runtime/usr/local/bin/skynet-session`, makinedeki Devuan oturum başlatıcısının
o tarihteki kaynağıydı. Girişte `xset s reset` ve `xset s 300 300` çalıştırıyordu. Mevcut
`xss-lock`, X11 hareketsizlik olayında `/usr/local/libexec/skynet-lock` çağırır.
Ek izleyici süreç veya zamanlayıcı servisi yoktur. DPMS'in masaüstünde kapalı
olması ve kilit ekranının kendi ekran kapatma davranışı korunur; parlaklık
değeri değiştirilmez. Duvar kâğıdı oynatıcısı ekran koruyucuyu engellemez.

Canlı uygulamada kilit zaten açıkken ekran koruyucu sıfırlanmamalıdır: xss-lock
zorla ekran koruyucu kapatılması üzerine kilit sürecini sonlandırabilir. Önce
kilit durumu kontrol edilir; yalnız açık masaüstünde sayaç sıfırlanıp süre
etkinleştirilir. Uygulamaların ekran koruyucu engelleyicileri ve X11'in klavye/
fare yakalama sınırları geçerlidir. Bir uygulama girdiyi yakalamışsa kilidin
gerçekten açıldığını kontrol etmek gerekir.

## Doğrulama ve kalan sınırlar

- Beş protokol testi sahte veriyle geçti; gerçek parola veya PAM kullanılmadı.
- Gizli Xephyr üzerinde GTK/X11 ve Cage/Wayland giriş akışları geçti.
- Ayrı D-Bus üzerindeki sahte login1 hizmeti ve sahte kilitleyiciyle xss-lock,
  bir saniyelik test eşiğinde 1,061 saniyede tetiklendi. Gerçek oturum kilitlenmedi.
- Dört geri yükleme testi ve depo yayın/bütünlük kontrolleri çalıştırılır.
- Yerel kaynak yaması `--fuzz=0` ile uygulanıp Debian hardening ve `-Werror`
  ile derlendi. Giriş ve kilit servisleri yeniden başlatılmaz.

Disk şifrelemesi bu düzeltmenin parçası değildir; sistem bölümü LUKS olmadan
kalır. X11 kilidi, aynı kullanıcı olarak çalışan zararlı yazılımdan izolasyon
sağlamaz. Parmak izi parolaya alternatif olmaya devam eder. XSecureLock upstream
arşivlenmiştir; dağıtımın güvenlik güncellemeleri izlenmelidir. Mevcut başlatıcı,
denetlenen paket sürümü değişirse dağıtımın kilit programına döner.

Kaynaklar: [greetd IPC](https://manpages.debian.org/trixie/greetd/greetd-ipc.7.en.html),
[xss-lock](https://manpages.debian.org/trixie/xss-lock/xss-lock.1.en.html),
[XSecureLock güvenlik tasarımı](https://github.com/google/xsecurelock#security-design).

## GNOME Keyring oturum başlangıcı — 24 Ekim 2026

DWM, GNOME anahtarlığının masaüstü otomatik başlatma girdisini çalıştırmıyordu.
Oturum başlatıcısı artık D-Bus ortamını aktardıktan sonra, uygulamalardan önce
`gnome-keyring-daemon --start --components=secrets` çağırır. Bu, PAM'in başlattığı
işlemi tamamlar; kasa parolasını saklamaz veya şifrelemeyi değiştirmez. Bir hata
oturum açmayı engellemez ve başlangıç komutu beş saniye, zorunlu sonlandırma
için ek bir saniye ile sınırlıdır.

Giriş parolası anahtarlığın parolasıyla aynıysa PAM otomatik açabilir. Yalnız
parmak iziyle giriş kasanın şifresini çözemez ve ilk kullanımda parola istemeye
devam eder. Bu değişiklik, parmak iziyle tamamen parolasız kasa açılışı sağlamaz;
greetd ve kilit ekranının mevcut doğrulama seçeneklerini değiştirmez.

Kaynaklar: [GNOME Keyring başlangıcı](https://wiki.gnome.org/Projects/GnomeKeyring/RunningDaemon),
[PAM modülü](https://wiki.gnome.org/Projects/GnomeKeyring/Pam/Manual).

## Spotify anahtarlık istisnasının geri alınması — 24 Ekim 2026

Spotify için denenen `--password-store=basic` istisnası, yerel veri korumasını
azalttığı için kullanıcının isteğiyle geri alındı. Eklenen kullanıcı komutu ve
masaüstü girdisi hem kurulu sistemden hem `home/` ağacından kaldırıldı; masaüstü
uygulama veritabanı yenilendi. Spotify yeniden paket başlatıcısının normal
depolama seçimini kullanır. GNOME Keyring başlangıç düzeltmesi, PAM ve parmak
izi ayarları korunur. Hesap, önbellek ve anahtarlık dosyaları silinmedi.

## Devuan cihaz kimliğinin sabitlenmesi — 24–25 Ekim 2026

Yeniden başlatmada Spotify hesabının kapanması araştırılırken Devuan'ın
`/etc/default/dbus` dosyasında `IDTYPE="RANDOM"` bulundu. Kullanıcının onayıyla
bu değer `FIXED` yapıldı; mevcut `/var/lib/dbus/machine-id` korundu. Ayar tüm
sistemin D-Bus makine kimliği politikasını etkiler: bu kimliği okuyan uygulamalar
artık bilgisayarı yeniden başlatmalar arasında aynı kimlikle tanıyabilir.
Rastgele kimliğin sağladığı açılışlar arası değişkenlikten vazgeçilir.

Bu işlem anahtarlık şifrelemesini veya giriş/kilit doğrulamasını değiştirmez.
Parmak iziyle girişte şifreli anahtarlık için parola gerekebilir. Spotify'a
anahtarlığı atlayan seçenek eklenmedi. Makine kimliği, hesap verileri ve sırlar
depoya alınmadı. Yeniden Spotify girişi ve tam yeniden başlatma sonrası hesap
kalıcılığı henüz doğrulanmadığından neden-sonuç ilişkisi kesin değildir.
