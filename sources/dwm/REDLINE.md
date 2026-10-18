# REDLINE INDUSTRIAL dwm

Mevcut dwm 6.8 kaynaklarının, systray ve autostart yamalarının sistem genelindeki özelleştirilmiş kurulumudur.

- Üst çubuk ve dmenu zemini: `#070809`.
- Seçili etiket ve aktif pencere başlığı: `#C3131C`, beyaz yazı.
- Aktif pencere çerçevesi: `#FF1B22`, 4 piksel.
- Pasif pencere çerçevesi: çelik grisi `#393D42`.
- Üst çubukta 12 piksel toplam dikey boşluk ve 3 piksel kırmızı alt çizgi.
- dmenu seçimi: `#D21920`, beyaz yazı.
- Font: JetBrains Mono ExtraBold, 13.
- Etiketler: `[01]`–`[06]`; mevcut etiket sayısı ve kısayollar korunur.
- Yerleşim göstergeleri: `[TILE]`, `[FLOAT]`, `[MONO:n]`.
- Durum çubuğu: aralarında 3 piksel siyah boşluk olan dört dikdörtgen panel.
- CPU: çelik çerçeve içinde kırmızı, köşesi kırpılmış CPU plakası; yüke göre dolan 10 eğik kırmızı çentik ve sabit genişlikte metal beyazı yüzde. Her çentik %10'luk bir aralığı temsil eder; %0 tamamen boştur, eksik/geçersiz veri `--%` olur. slstatus ölçümü ve saniyelik güncelleme değişmez. BAT: siyaha yakın zeminde kırmızı dikdörtgen çerçeve, kırmızı pil hücreleri ve metal grisi bilgi.
- DATE: çelik grisi zemin; TIME: dolu kırmızı zeminde beyaz, saniyeli saat.
- Pil: `▰▰▰▰▱` hücreleri köşeli parantez içinde; hizalı tam sayı yüzde ve `↑` şarj / `↓` deşarj / `•` dolu veya takılı göstergesi. Örnek: `BAT [▰▰▰▰▱]   76% ↑`. Dolu hücreler soldan sağa giderek açılan beş kırmızı tondadır: `#FF3B38`, `#FF5956`, `#FF7774`, `#FF9592`, `#FFB3B0`. Boş hücrelerin konturları ve parantezler mevcut kırmızıda, BAT etiketi/yüzde/ok metal grisinde kalır. Okunamayan değerler `--` olarak gösterilir.
- Yüzde doğrudan `/sys/class/power_supply/BAT0/capacity` içindeki tam sayı değerinden alınır. Küsürat hesabı kaldırılmıştır; geçerli aralık %0–100'dür.

Kaynak: `/usr/local/src/dwm`.
Kurulu program: `/usr/local/bin/dwm`.
Durum kaynağı: `/usr/local/src/slstatus/config.h`.
Durum programı: `/usr/local/bin/slstatus`.

slstatus, `CPU ...|BAT ...|DATE ...|TIME ...` biçimini saniyede bir üretir. dwm bu dört alanı ayrı renklerle çizer. `statuspadding` ve `statusgap`, dwm'in `config.h` dosyasındadır. Düz metin üreten durum programları da desteklenir.

Greetd X11 oturumunda `~/.xprofile` okunur. dwm ve slstatus artık `/usr/local/bin` altından çalışır; kullanıcı dizininde bunları gölgeleyen kopya yoktur.

Renk, çerçeve kalınlığı, font, `barpadding` ve `barlinepx` için `config.h` düzenlenir. Kırmızı alt çizginin çizimi ve bar yüksekliği `dwm.c` içindedir. Yeniden derleyip kurmak için:

```sh
sudo make -C /usr/local/src/dwm install PREFIX=/usr/local
sudo make -C /usr/local/src/dwm clean
sudo make -C /usr/local/src/slstatus install PREFIX=/usr/local
sudo make -C /usr/local/src/slstatus clean
```

Ardından oturumdan çıkılıp dwm'e yeniden girilir. Masaüstü yardımcıları `/etc/dwm/autostart.sh` ile başlar. Derleme ayarları `/etc/dwm/config.h` ve `/etc/slstatus/config.h` içindedir; kaynak dizinlerindeki `config.h` bağlantıları bu dosyalara gider.

Önceki yapılandırma, program ve `.xprofile` yedeği:
`~/.local/share/dwm-theme-backups/before-redline-20261013T074654888773Z/`.

İlk kırmızı temanın program, `config.h`, `dwm.c` ve açıklama yedeği:
`~/.local/share/dwm-theme-backups/before-industrial-20261013T092052748166Z/`.

Durum panellerinden önceki dwm, yapılandırma, slstatus ve autostart yedeği:
`~/.local/share/dwm-theme-backups/before-status-20261013T092708829357Z/`.

Programlar, kaynaklar ve kılavuzlar sistemin `/usr/local` dizinlerine taşındı. Önceki kullanıcı kopyaları kaldırıldı. Alt+Q pencere kapatma ve beş kademeli pil rengi korunur. Açık dwm süreci sonlandırılmadı; yeni konumdaki program sonraki girişte çalışır.

Kısayollar doğrudan bu dizindeki `config.h` ve `dwm.c` üzerinden doğrulanmıştır. `MODKEY`, Alt tuşudur. Etiketler `[01]`–`[06]`, çalışma alanları gibi kullanılır; bir pencere birden fazla etikette bulunabilir. Ana alan, döşeme düzeninde varsayılan olarak soldaki büyük alandır.

| Klavye kısayolu | İşlev |
| --- | --- |
| Alt+Q | Seçili pencereyi kapatır; eski Alt+Shift+C ataması kaldırılmıştır. |
| Alt+Shift+Q | dwm'den çıkar; bu kurulumda masaüstü oturumunu sonlandırır. |
| Alt+Enter | Kitty açar. Aynı tuşa ayrıca `zoom` bağlı olduğundan seçili döşenmiş pencereyi ana alana taşıma/değiştirme işlemi de çalışır. |
| Alt+P | Uygulama başlatmak için dmenu açar. |
| Alt+B | Üst çubuğu gösterir/gizler. |
| Alt+J / Alt+K | Sonraki / önceki pencereye odaklanır. |
| Alt+I / Alt+D | Ana alandaki pencere sayısını artırır / azaltır. |
| Alt+H / Alt+L | Ana alanın genişlik payını 5 yüzde puan azaltır / artırır. |
| Alt+T | Döşeme düzenini seçer: `[TILE]`. |
| Alt+F | Serbest pencere düzenini seçer: `[FLOAT]`. |
| Alt+M | Döşenmiş pencerelerin kullanılabilir alanı kapladığı düzeni seçer: `[MONO]`. |
| Alt+Space | Mevcut ve önceki yerleşim düzeni arasında geçiş yapar. |
| Alt+Shift+Space | Seçili pencerenin serbest/döşenmiş durumunu değiştirir. |
| Alt+Tab | Önceki etiket görünümüne döner. |
| Alt+1…6 | İlgili etiketi gösterir. |
| Alt+Ctrl+1…6 | İlgili etiketi mevcut görünüme ekler/çıkarır. |
| Alt+Shift+1…6 | Seçili pencereyi ilgili etikete taşır. |
| Alt+Ctrl+Shift+1…6 | Seçili pencereye ilgili etiketi ekler/çıkarır. |
| Alt+0 | Tüm etiketlerdeki pencereleri gösterir. |
| Alt+Shift+0 | Seçili pencereyi bütün etiketlerde gösterir. |
| Alt+, / Alt+. | Önceki / sonraki monitöre odaklanır. |
| Alt+Shift+, / Alt+Shift+. | Seçili pencereyi önceki / sonraki monitöre taşır. |
| Print Screen | Flameshot ekran görüntüsü seçim aracını açar. |
| Ses artırma / azaltma tuşları | Sesi 5 yüzde puan artırır / azaltır; artırma sessizi de kaldırır. |
| Hoparlör sessiz tuşu | Hoparlörü sessize alır/sessizden çıkarır. |
| Mikrofon sessiz tuşu | Mikrofonu sessize alır/sessizden çıkarır. |
| Parlaklık azaltma / artırma tuşları | Parlaklığı yaklaşık 5 yüzde puan azaltır / artırır; alt sınır %5'tir. |

Ses ve parlaklık atamaları, klavyenin gönderdiği XF86 medya tuşlarına bağlıdır. Yapılandırmadaki notlara göre bunlar Fn+F1–F4 ve Fn+F5/F6 üzerinden gönderilir; Fn kilidi durumuna göre Fn gereksinimi değişebilir. Düz F1–F6 için ayrıca dwm ataması yoktur.

Yapılandırmada 7–9 için de eski `TAGKEYS` satırları vardır, fakat yalnızca altı etiket tanımlıdır. Bu yüzden Alt+7/8/9 önceki etiket görünümüne döner; Ctrl/Shift içeren 7–9 atamaları etiket seçimini veya pencere etiketlerini değiştirmez. Bu satırlar ve Alt+Enter'daki çift atama mevcut davranışı korumak için değiştirilmedi.

| Fare kısayolu | İşlev |
| --- | --- |
| Pencere üzerinde Alt+sol tuşla sürükleme | Pencereyi taşır; yeterince sürüklenen döşenmiş pencere serbest duruma geçer. |
| Pencere üzerinde Alt+sağ tuşla sürükleme | Pencereyi boyutlandırır; yeterince değiştirilen döşenmiş pencere serbest duruma geçer. |
| Pencere üzerinde Alt+orta tık | Pencerenin serbest/döşenmiş durumunu değiştirir. |
| Etiket üzerinde sol tık | Etiketi gösterir. |
| Etiket üzerinde sağ tık | Etiketi mevcut görünüme ekler/çıkarır. |
| Etiket üzerinde Alt+sol tık | Seçili pencereyi etikete taşır. |
| Etiket üzerinde Alt+sağ tık | Seçili pencereye etiketi ekler/çıkarır. |
| Yerleşim göstergesinde sol tık | Mevcut ve önceki yerleşim düzeni arasında geçiş yapar. |
| Yerleşim göstergesinde sağ tık | `[MONO]` düzenini seçer. |
| Üst çubuktaki pencere başlığında orta tık | Seçili döşenmiş pencereyi ana alana taşır; zaten ana alandaysa sıradakiyle değiştirir. |
| Durum yazısında orta tık | Kitty açar. |

Orta tık, fare tekerleğine basmaktır. Monitör kısayolları birden fazla monitör olduğunda etkilidir. Bu liste dwm atamalarını kapsar; Kitty, uygulamalar ve kilit ekranı kendi kısayollarını ayrıca işler.
