# Ses seviyesi ve bildirim sesleri — 25 Ekim 2026

`runtime/usr/local/bin/dwm-volume`, kurulu Devuan'ın mevcut pactl tabanlı ses
kontrolünü korur ve ses artırma/azaltma işlemlerinden sonra kullanıcının
`~/customsounds/Soundleveltest.mp3` dosyasını çalar. DWM'nin mevcut tuş bağları
aynı komutu çağırır; DWM derlemesi veya oturum yeniden başlatması gerekmez.
SKYNET Dunst göstergesi ve beş puanlık ses adımları korunur.

Mute, mikrofon mute ve yalnız göstergeyi açan `show` işlemleri örnek çalmaz.
Çıkış sessizde veya sıfır seviyedeyse, dosya eksikse ya da mpv yoksa örnek
atlanır. Ses artırma tuşunun mevcut mute açma davranışı korunur; azaltma tuşu
mute durumunu değiştirmez.

Örnek mevcut ses çıkışında, sistem seviyesine bağlı olarak mpv ile çalınır.
`--volume=100` mpv'nin yazılımsal çarpanını değiştirmeden bırakır; sistem
seviyesini yüzde yüze çıkarmaz. Ek kazanç veya normalizasyon uygulanmaz.
Kullanıcı mpv betikleri/ayarları yüklenmez, pencere açılmaz, ekran kilidi
engellenmez ve oynatma geçmişi yazılmaz. Ayrı bir beklemesiz flock kilidi,
basılı tutulan tuşlarda seslerin üst üste binmesini veya kuyruk oluşturmasını
önler. Ses çalan süreç ana ses kontrolü kilidini taşımaz.

Yeni sürekli çalışan yardımcı veya paket gerekmez. İki kilit dosyası kullanıcı
runtime dizininde işlevsel oturum dosyalarıdır. MP3 asıl yerinde korunur;
dönüştürülmez ve depoya kopyalanmaz. Başka bir örnek için oturumda
`SKYNET_VOLUME_SOUND` ortam değişkeni kullanılabilir. Geri yükleme sırasında
ses dosyası ayrıca sağlanmalıdır.

Üç davranış testi; iki yönü, sessiz durumları, eksik dosyayı, ses kontrolü
kilidinin serbest kalmasını ve meşgul örneğin kuyruk oluşturmamasını sınar:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_volume_feedback.py -v
```

Başvuru: [mpv ses seviyesi seçeneği](https://mpv.io/manual/stable/#options-volume).

## Bildirim sesi

`home/.config/dunst/notification-sound`, Dunst'ın `skynet-notification-sound`
kuralından çağrılır ve `~/customsounds/Notificationrecieved.mp3` dosyasını çalar.
Yardımcı kullanıcı ayarlarının parçasıdır; yönetici yetkisi, ek paket veya
sürekli çalışan yeni süreç gerekmez. MP3 depoya kopyalanmaz. Başka dosya için
`SKYNET_NOTIFICATION_SOUND` kullanılabilir.

Ses/parlaklık göstergeleri uygulama adıyla; ses, mikrofon ve parlaklık
bildirimleri ayrıca stack tag ile dışarıda tutulur. Böylece ses tuşunun kısa
örneğine ikinci bildirim sesi eklenmez. `always_run_script = false` gizlenen
bildirimleri sessiz bırakır; yardımcı ayrıca Dunst'ın duraklatma durumunu
kontrol eder. Geçmişten geri çağrılan bildirimler tekrar ses çalmaz.

Beklemesiz runtime kilidi, aynı anda gelen bildirimlerde tek örnek çalınmasını
sağlar; kuyruk oluşmaz. Varsayılan ses çıkışı ve mute durumu korunur. Bildirim
başlığı, gövdesi ve URL'leri komut olarak değerlendirilmez veya kaydedilmez.
Ses dosyası yoksa işlem sessizce atlanır. Sistem dışındaki bir uygulamanın
kendi arayüzünde çaldığı sesler bu ayarın kapsamında değildir.

Kurulumda mevcut kırmızı SKYNET dunstrc ve kullandığı beş SVG simge depodaki
eski görünümün yerine kaydedildi; canlı görünüm değiştirilmedi. Yapılandırma
`dunstctl reload` ile aynı Dunst sürecinde etkinleştirildi. Gizli X11 ekranı,
ayrı D-Bus ve sahte oynatıcıyla normal bildirim, OSD istisnaları, gizlenen ve
duraklatılan bildirimler, bildirim yoğunluğu, geçmişten çağırma ve eksik dosya
durumları doğrulandı. Gerçek deneme bildiriminin ses sunucusunda
`Notifications` akışını oluşturduğu da gözlendi; test bildirimi kendi
kimliğiyle kapatılıp geçmişten kaldırıldı. Diğer bildirimlere dokunulmadı.

Devuan'da `dunstctl rules` için gereken busctl bulunmadığından kural kontrolü
doğrudan D-Bus `RuleList` yöntemiyle yapıldı; bunun için paket kurulmadı.
Kaynak: [Dunst betik desteği](https://dunst-project.org/documentation/#SCRIPTING).

## Başlangıç gecikmesi düzeltmesi — 26 Ekim 2026

Kullanıcının MP3 dosyalarında bildirim için yaklaşık 376 ms, USB takma için
415 ms, USB çıkarma için 424 ms ve ses seviyesi örneğinde 61 ms başlangıç
sessizliği ölçüldü (`silencedetect`, -45 dB eşiği). Oynatıcı bu boşluğu da
çalınca bildirim/USB olayından sonra ses gecikiyordu.

Üç yardımcı artık mpv'nin mevcut FFmpeg filtresiyle sadece ilk yakın sessizliği
atlar: `silenceremove`, tek başlangıç dönemi, -60 dB eşik, 2 ms algılama ve
10 ms başlangıç payı. İç duraklamalar ve sesin sonu korunur. USB'nin -6 dB
azaltması, diğer efektlerin mevcut kazancı ve mute davranışları aynı kalır.
`--audio-buffer=0.05 --pulse-buffer=50` yalnız bu kısa efektlerin tamponlarını
ayarlar; müzik/video oynatıcıları veya genel ses sunucusu ayarları değişmez.

Özel bir PulseAudio null sink hazır olduktan sonra, yalnız onun monitor
kaynağında ilk sinyale kadar geçen süre ölçüldü; hoparlör/mikrofon kaydı
alınmadı. Her durumda iki çalıştırmanın ortanca değerleri:

| Ses | Önce | Sessizlik atlama | Sessizlik atlama + 50 ms tampon |
| --- | --- | --- | --- |
| USB takma | 573 ms | 177 ms | 171 ms |
| Bildirim | 527 ms | 177 ms | 172 ms |

Bu ölçüm oynatıcı başlangıcını kapsar; fiziksel USB algılama ve uyuyan ses
donanımının uyanması dahil değildir. Asıl kazanç dosya başındaki boşluğun
atlanmasıdır. Donanımın uyku/güç tasarrufu ayarları değiştirilmemiştir.

Dört dosyanın çözümlenmiş sesi karşılaştırıldı: başlangıç payından sonraki
dalga biçimi, iç duraklamalar ve son bölüm birebir korundu. MP3 SHA-256
değerleri aynı kaldı. Sekiz USB ve üç ses seviyesi davranış testi geçti;
ses çıkışı/mikrofon seviyesi, mute ve varsayılan aygıtlar ölçüm öncesi/sonrası
aynıydı. Geçici ölçüm çıkışı kaldırıldı. USB yardımcısı aynı oturum izleme
bağıyla yeniden başlatılır; DWM/Dunst veya ses sunucusu yeniden başlatılmaz.
