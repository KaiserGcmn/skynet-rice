# Hedef: Devuan + OpenRC

Kullanıcı OpenRC seçti. Yeni kurulumda systemd servisleri kurulmayacak.
Kaynak sistem Debian 13 + systemd olduğu için mevcut servis dosyaları,
daha sonra davranışlarını karşılaştırabilmek üzere `profiles/debian/` altında
korunuyor. Kullanıcı ayarlarını geri yükleme komutu bu dizini okumaz.

| Bileşen | OpenRC geçişi |
| --- | --- |
| DWM, dmenu, slstatus, Kitty, Dunst, GTK, duvar kâğıdı | systemd'ye doğrudan bağlı değil; yeni sistemde derle/kur |
| `/etc/dwm/autostart.sh` | Aynı başlangıç betiği kullanılabilir; isteğe bağlı program yollarını doğrula |
| Greetd | Dağıtımın OpenRC hizmetini tercih et; yoksa `profiles/openrc` taslağını gözden geçir |
| Özel greetd güç düğmeleri | C kaynaklarında `systemctl` çağrısı var; elogind D-Bus güç isteklerine uyarlama bekliyor |
| DWM kilit dinleyicisi | logind D-Bus arayüzünü dinliyor, fakat kilidi `systemd-run` ile başlatıyor; kullanıcı oturumunda gözetim/kilit yaşam döngüsü uyarlanmalı |
| XSecureLock F11/F12 | Yamada `systemctl` kullanılıyor; elogind/polkit ve inhibitor davranışı korunarak uyarlanmalı |
| Güç tuşu/kapak | Mevcut logind ayarları referans; elogind karşılıkları kilit dinleyicisi çalıştıktan sonra uygulanmalı |
| Ses durumunu saklama | Python aracı bağımsız; PipeWire hazır olduktan sonra `restore`, oturum kapanmadan önce `save` çalıştırılmalı |
| PipeWire/WirePlumber | Devuan'ın kullanıcı oturumu başlangıcı/gözetimi sağlanmalı; root hizmeti olarak başlatılmaz |
| ExpertBook mute LED | OpenRC oneshot taslağı eklendi; modül yükleme ve ALSA sıralaması cihazda doğrulanmalı |
| USB-C izleyicisi | Oturumda 2 dakika sonra, ardından 5 dakikada bir çağrılmalı; cron'a root olarak bağlanmaz |
| TLP, nftables, AppArmor, SMART | Dağıtımın OpenRC hizmetleri kullanılır; systemd hardening/drop-in sözdizimi taşınmaz |
| Otomatik güvenlik güncellemeleri | Devuan'ın güvenlik deposu ve cron/OpenRC düzenine göre yeniden ayarlanmalı; Debian kaynak adı kopyalanmaz |
| VMD, DKMS, GRUB | Init yöneticisinden ayrı olarak yeni çekirdek/disk üzerinde doğrulanır |

## OpenRC taslaklarının durumu

`profiles/openrc/etc/init.d/` içindeki iki hizmet **taslaktır**: yalnızca kabuk
sözdizimi ve bağımlılık mantığı gözden geçirildi. Gerçek OpenRC üzerinde
başlatma/durdurma testi yapılmadı; varsayılan geri yükleme/derleme bunları kurmaz.
Greetd taslağı kilit dinleyicisi, güç tuşu veya PipeWire'ı tek başına çözmez.
Oturum güvenliğini doğrulamadan mevcut giriş yöneticisini devre dışı bırakma.

Devuan üzerinde ilk kontrol sırası: doğru init ve elogind/PAM oturumu, D-Bus,
Xorg+DWM, ses, manuel kilitleme/kilit açma, güç tuşu/kapak, giriş ekranı,
son olarak cihaz sürücüleri ve GRUB. `systemctl` adlı sahte bir uyumluluk
betiği ekleyerek davranışları taklit etmek bu geçişin parçası değildir.

Kaynaklar:

- [Devuan Debian Trixie → Excalibur rehberi](https://www.devuan.org/os/documentation/install-guides/excalibur/trixie-to-excalibur.html)
- [OpenRC hizmet yazma rehberi](https://github.com/OpenRC/openrc/blob/master/service-script-guide.md)
- [elogind kaynak ve belgeleri](https://github.com/elogind/elogind)

Bu kaynaklar geçişteki bileşenleri açıklıyor; bu özel rice'ın OpenRC üzerinde
çalıştığına dair test sonucu oluşturmuyor.
