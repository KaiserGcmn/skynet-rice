# Hoparlör ve mikrofon durum kaydı

Yardımcı, donanım ses aygıtlarının ses seviyesini ve mute durumunu birbirinden
bağımsız olarak kaydeder. ALSA ve Bluetooth aygıtları sabit adlarıyla eşleştirilir;
monitor kaynakları ve sanal uygulama aygıtları dışarıda bırakılır. Varsayılan
aygıt seçimi değiştirilmez. Kanal dengesi korunur; kanal düzeni değişen bir
aygıta eski kanal seviyeleri uygulanmaz.

## Devuan oturumu

Kurulu `/usr/local/libexec/dwm-session-extras`, yeni girişte
`audio-mute-state watch --restore` çalıştırır. Canlı oturumda ilk etkinleştirmede
`audio-mute-state watch` kullanılır: mevcut ayarlar kaydedilir, değiştirilmez.
Yardımcı, `pactl subscribe` üzerinden sink/source olaylarını dinler ve değişiklikleri
150 ms içinde toplu olarak kaydeder. Boştayken sürekli ses sorgusu veya disk yazımı
yapmaz. Aynı oturumda ikinci bir izleyici başlatılması kilitle engellenir.

Kapanış sırasında PulseAudio önce dursa da son olayın kaydı korunur. Ses sunucusu
oturum içinde yeniden başlarsa kaydedilmiş durum geri yüklenir ve izleme devam
eder. Devuan ayarındaki her açılışta rastgele D-Bus makine kimliği, bu sabit dosyanın
adını değiştirmez. Parlaklık ayrı olarak mevcut SysV `brightness` hizmetiyle normal
kapanışta kaydedilir ve açılışta geri yüklenir; bu yardımcı parlaklığı değiştirmez.

Durum dosyası `$XDG_STATE_HOME/audio-mute-state/state.json` veya varsayılan olarak
`~/.local/state/audio-mute-state/state.json` konumuna 0600 izinleriyle atomik yazılır.
Değişmeyen kayıt tekrar yazılmaz; bağlantısı kesilen aygıtların kayıtları korunur.
Eski, yalnız mute içeren sürüm 1 kayıtları da okunur. Eksik/bozuk ses sorgusu önceki
kaydı silmez. Açılıştan sonra takılan aygıtlara özel geri yükleme yapılmaz; bu işi
ses sunucusunun mevcut aygıt politikası yönetir.

## Tek seferlik komutlar

Eski systemd oneshot arşivi 28 Ekim 2026'da kaldırıldı. Sürekli olay kaydı için
yukarıdaki `watch --restore` oturum süreci kullanılır. Tek seferlik `save` ve
`restore` komutları uyumluluk için korunmuştur.

## Doğrulama

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s sources/audio-mute-state -v
```

23 Ekim 2026: Ayrı PulseAudio sunucusu ve null aygıtlarla dört mute birleşimi,
ikisinin ses seviyesi, kanal sırası, gereksiz yazım yapılmaması, ikinci izleyicinin
engellenmesi, sunucunun ani kapanması ve sonraki girişte geri yükleme doğrulandı.
Fiziksel ses aygıtlarına test değişikliği uygulanmadı. Gerçek yeniden başlatma
yapılmadı; kurulu Devuan oturumu canlı etkinleştirme sonrası ayrıca kontrol edildi.

Protokol: [pactl](https://manpages.debian.org/unstable/pulseaudio-utils/pactl.1.en.html).
