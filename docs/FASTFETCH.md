# SKYNET braille küresi ve sistem paneli

Fastfetch doğrudan `/usr/bin/fastfetch` üzerinden çalışır. Logo **metindir**:
PNG, Kitty resim protokolü, animasyon veya ara başlatıcı kullanılmaz
(kullanıcı tercihi, 2026-11-22). Önceki ASCII logo, yedeği ve geçici
dönüştürme dosyaları kullanıcı isteğiyle silindi.

## Logo — `home/.config/fastfetch/skynet-globe.txt`

56 sütun × 30 satır. ASCII yerine Unicode braille (U+2800–28FF; hücre başına
2×4 nokta) kullanılır, bu yüzden çözünürlük eski ASCII küreden 8 kat yüksektir.

- **Küre (23 satır):** kullanıcının kırmızı/beyaz dünya görselinden
  (`~/wallpapers/Kırmızı Beyaz Dünya Küresi.png`) bir defalık dönüşüm.
  Kıta maskesi `R - max(G, B) > 70` ile ayrılır, 15 px açma işlemiyle ağ
  çizgileri temizlenir, nokta ızgarasına kutu ortalamasıyla örneklenir.
  Görseldeki ağ, braille çözünürlüğünde her yeri doldurduğu için kullanılmaz;
  yerine görselin eğimine uyan (kutup sol üstte, −20° dönüş) 15° aralıklı
  geometrik enlem-boylam ağı tek nokta kalınlığında çizilir.
- **Merkez:** üç parçalı SKYNET üçgeni, siyah boşluk payıyla, çelik beyaz.
- **Köşeler:** nötr HUD etiketleri `NODE 01`, `UPLINK`, `GRID 15°`, `SYNC`.
- **Kelime işareti:** `SKYNET`, yarım blok (`▀▄█`) karakterlerle 3 satır.
- **Alt yazılar:** `NEURAL NET-BASED ARTIFICIAL INTELLIGENCE` ve
  `◆ GLOBAL DIGITAL DEFENSE NETWORK ◆`.

Terminatör adları (CSM-101, T-800, Cyberdyne, NORAD…) ve SELF-AWARE / 1997
satırı kullanıcı isteğiyle kaldırıldı; `tests/test_fastfetch_logo.py` bunu denetler.

| Etiket | Renk | Kullanım |
| --- | --- | --- |
| `$1` | `#A42839` | çizgiler |
| `$2` | `#FF4050` | kıtalar, vurgular |
| `$3` | `#DDE3EA` | üçgen, kelime işareti |
| `$4` | `#3E333F` | sönük yardımcılar |
| `$5` | `#A9BBC5` | etiketler |
| `$6` | `#761C28` | enlem-boylam ağı |

Kitty braille noktalarını küçük çizer; ince ağ ile dolu kıtalar arasındaki
kontrast bu yüzden ağ için ayrı, koyu `$6` tonuyla sağlanır. Dönüştürücü
betikler kurulmaz; logo düz metin olarak saklanır.

## Panel

64 sütun, sağı açık HUD düzeni (sağ kenarlık yok, bu yüzden uzun değerler
çerçeveyi bozmaz). Logo + boşluk + panel ≈ 126 sütun.

- Başlık: `SKYNET ▌ NEURAL NET CONTROL ──── ● ONLINE`, altında kırmızı çizgi,
  `OPERATOR user@host`.
- Bölümler: `01 CHASSIS` (host, CPU · çekirdek · frekans, GPU, ekran),
  `02 NEURAL LOAD` (bellek/swap/disk/pil çubukları, yük ortalaması),
  `03 KERNEL` (OS, çekirdek, BIOS, paketler), `04 INTERFACE` (shell, WM,
  terminal, font, uptime, AGE).
- Çubuklar 18 karakterlik `━` hat; dolu kısım kırmızı, boş kısım `#3E333F`.
- Ekran satırı yenileme hızı veya inç bilgisi yoksa o parçayı gizler.
- Alt: `WE SOLVE HUMAN PROBLEMS. PERMANENTLY.` ve 8 tonluk palet şeridi.

Değerler komutun çalıştığı andaki anlık görüntüdür.

## AGE tarih kaynağı

AGE, kök dizinin doğum tarihine dayanmaz. Kullanıcının seçtiği ilk düzenli
kullanım tarihi 19 Ekim 2026'dır; 29 Ekim'de `10 days / first use 2026-10-19`
gösterir. Bu kullanım yaşıdır; kesin kurulum tarihi olduğu ileri sürülmez.

`home/.local/bin/os-age`, `$XDG_STATE_HOME/skynet-rice/first-use-date`
dosyasını okur; XDG değişkeni ayarlı değilse
`~/.local/state/skynet-rice/first-use-date` kullanılır. Dosya tek satır
`YYYY-MM-DD` içerir. Tarih cihazın yerel durumudur ve depoya kopyalanmaz.
Eksik, geçersiz veya gelecekteki tarihler `unknown` verir.

## Doğrulama — 22 Kasım 2026

Ayrı, kimlik doğrulamalı Xephyr (`-dpi 96`) içinde Kitty 0.41.1 ile çalıştırıldı:
braille küre, üçgen, yarım blok kelime işareti, 64 sütun başlık genişliği ve
panel hizası kontrol edildi. Belge görselinde kullanıcı/cihaz adı
`operator@expertbook-b3` olarak genelleştirildi; ekran çözünürlüğü test
ekranına aittir. `tests/test_fastfetch_logo.py` logonun metin olduğunu,
genişliğini, renk etiketlerini ve kaldırılan adları denetler.
