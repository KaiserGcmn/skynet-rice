# SKYNET HUD imleç teması — 22 Kasım 2026

`~/.icons/Skynet` artık depodaki üreteçle çizilen özgün bir settir. Eski set
48 px için çizilmiş üçüncü taraf piksel-art idi; `Xcursor.size: 32` ile
küçültülünce bulanık ve tırtıklı görünüyordu.

- Üreteç: `sources/skynet-cursor/render-cursors.py`. Her imleç 32 birimlik
  ızgarada Cairo ile vektör olarak çizilir ve 24/32/48/64 px için ayrı ayrı
  rasterlanır, `xcursorgen` ile paketlenir.
- Görünüm: koyu çelik gövde, `#ff4050` kırmızı kenar, siyah dış çizgi ve
  yumuşak gölge; siyah masaüstünde de açık sayfalarda da görünür. Ok ucunda
  ince çelik yansıma ve kırmızı çekirdek. Bağlantı imleci kırmızı dolu ok,
  yardım `?` rozetli, meşgul imleçleri 24 karelik dönen bölümlü halka
  (40 ms, ~1 tur/sn). Yazı, artı, taşıma, boyutlandırma ve yasak imleçleri aynı
  dilde.
- Ok ucu keskin köşede eğik kesilir (miter limit 2); tıklama noktası kırmızı
  ucun üstündedir.
- 13 dosya + 67 standart takma ad (`default`, `pointer`, `text`, `wait`,
  `progress`, `not-allowed`, CSS/X11 boyutlandırma adları, karma adlar).
  Eksik adlar `breeze_cursors` temasından gelir.

Kurulum/yeniden üretim:

```sh
python3 sources/skynet-cursor/render-cursors.py ~/.icons/Skynet
xsetroot -cursor_name left_ptr   # masaüstü kök imlecini yeniler
```

Açık uygulamalar imleci yeniden başlatılınca alır; tamamı için oturumu
kapatıp açmak yeterli. `--preview PNG [--preview-size N]` siyah ve açık zeminde
önizleme üretir. Eski set yedeği:
`~/.local/state/skynet-rice/backups/cursor-before-hud-20261122/`.

Testler: `tests/test_cursor_theme.py` (tüm boyutlar, sıcak noktalar, animasyon
kare sayısı, ok ucu–sıcak nokta hizası, takma adlar).
