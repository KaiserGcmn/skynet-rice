# SKYNET Black Red GTK teması

Kullanıcının seçimiyle tema yalnız Thunar'a değil, GTK uygulamalarına uygulandı.
Tema `home/.themes/SKYNET-Black-Red/` altında korunur ve `restore-home.py` ile
`~/.themes/SKYNET-Black-Red/` konumuna aktarılır. GNOME masaüstünü gerektirmez.

- Ana zemin, dosya listesi, kenar çubuğu ve menü yüzeyleri `#000000`.
- Kırmızı vurgu `#d32f2f`; beyaz seçim yazısıyla kontrast yaklaşık 4,98:1.
- Kompakt aralıklar, normal kenar çubuğu ve 4 piksel temel köşe yarıçapı.
- `breeze-dark-red` simgeleri (`breeze-dark`'ın kullanıcı kopyası: mavi vurgu `#3daee9` tam olarak
  `#b02a30` olur, diğer canlı renkler aynı kırmızı ailesine, soluk bej ve arduvaz tonları çelik
  grisine çekilir, gri/beyaz/siyaha dokunulmaz; `python3 scripts/build-icon-theme.py` ile üretilir),
  `Skynet` imleci ve JetBrains Mono yazı tipi.
- GTK 3 ve GTK 4 için derlenmiş stiller; eski GTK 2 için sistemin
  `/usr/share/themes/Adwaita-dark/gtk-2.0/gtkrc` dosyasını kullanan küçük uyum stili.

Yüzeyler siyahtır; seçim, metin, simge ve üzerine
gelme efektleri okunabilirlik için renkli kalır.

## Kaynak ve yeniden derleme

Temel: [vinceliuice/Graphite-gtk-theme](https://github.com/vinceliuice/Graphite-gtk-theme),
2026-08-23 sürümü, `2a8dd5aa1346d77539bf8196061260f353ee8d75` commit'i.
[Kaynak arşivi](https://codeload.github.com/vinceliuice/Graphite-gtk-theme/tar.gz/2a8dd5aa1346d77539bf8196061260f353ee8d75)
SHA-256: `a07b6a78af315a6d33a49108839bed0e8232cb367ff0c6a658ce22cc99665e63`.
GPL-3.0 lisansı temadaki `COPYING` dosyasında korunmuştur.

Arşivi doğrulayıp geçici bir dizine açtıktan sonra kaynak kökünde
`patch -p1 -i /depo/yolu/sources/gtk-skynet/graphite-skynet.patch` çalıştır.
`src/sass/_tweaks.scss` dosyasını `src/sass/_tweaks-temp.scss` olarak kopyala.
Yama kırmızı vurgu, tam siyah yüzeyler, kompakt düzen ve köşeleri içerir.

`sassc` ve `libsass` kullanarak, her `VERSION` için `3.0` ve `4.0` değerleriyle:

```sh
sassc -M -t expanded "src/main/gtk-$VERSION/gtk-Dark.scss" \
    "/hedef/SKYNET-Black-Red/gtk-$VERSION/gtk.css"
```

Her GTK dizinindeki `gtk-dark.css` yalnız `@import url("gtk.css");` içerir.
`src/assets/gtk/assets-red/` içeriğini ilgili `assets/` dizinine;
`src/assets/gtk/scalable/` dizinini `assets/scalable/` konumuna kopyala.
CSS içindeki yerel `url(...)` referanslarını doğrula ve referans verilmeyen
varlıkları çıkar. GTK 2 için `sources/gtk-skynet/gtk2-compat.rc` dosyasını
`gtk-2.0/gtkrc` olarak kullan. `index.theme`, `README.md` ve lisansı da koru.
Upstream `install.sh` çalıştırılmadı; GNOME Shell/GDM/Cinnamon veya GTK 4
libadwaita dosyalarına genel CSS bağlantısı kurulmadı.

Canlı sistemde derleyici paketleri kurulmadı: dağıtımın `sassc` ve `libsass1`
paketleri geçici dizine açılarak kullanıldı. Derleme araçları, indirmeler ve
test dizinleri işlem sonunda kaldırıldı. Kullanılan tema yaklaşık 541 KiB'dir.

## Etkinleştirme ve geri alma

Kullanıcı dosyaları şu tercihleri içerir:

- `~/.gtkrc-2.0`: `gtk-theme-name="SKYNET-Black-Red"`.
- GTK 3/4 `settings.ini`: `gtk-theme-name=SKYNET-Black-Red` ve
  `gtk-application-prefer-dark-theme=true`.
- `~/.config/xsettingsd/xsettingsd.conf`: `Net/ThemeName "SKYNET-Black-Red"`.

Grafik oturumundaki kullanıcıyla ayrıca:

```sh
gsettings set org.gnome.desktop.interface gtk-theme SKYNET-Black-Red
gsettings set org.gnome.desktop.interface color-scheme prefer-dark
pkill -HUP -u "$(id -u)" -x xsettingsd
```

Dconf tercihlerini `restore-home.py` otomatik uygulamaz. Libadwaita veya kendi
stilini zorlayan uygulamalar sistem temasını tamamen izlemeyebilir; bunlara
zorunlu stil enjeksiyonu yapılmadı. Qt uygulamalarının tema ayarı değiştirilmedi.

Geri almak için GTK 2/3 ve xsettingsd tema adını `Adwaita-dark` yap; GTK 3/4
`gtk-application-prefer-dark-theme` değerini `false` yap. GTK 4 dosyasında
önceden `gtk-theme-name` bulunmuyordu; yeni girdiyi kaldır. Bu makinenin önceki
dconf değerleri `gtk-theme=Clearlooks-Phenix-Sapphire` ve `color-scheme=default`
idi; xsettingsd'nin `Adwaita-dark` değeri canlı görünümü belirliyordu.
Tercihleri geri aldıktan sonra xsettingsd'yi HUP ile yenile.

## Doğrulama

Gizli bir Xephyr ekranı ve özel D-Bus/HOME dizinlerinde gerçek Thunar 4.20.2
ile önizleme alındı. GTK 3 ve GTK 4 CSS ayrıştırma hatası sayısı sıfırdı;
GTK 2 uyum stilinde temel zemin RGB `0,0,0` olarak doğrulandı. Önizleme
piksellerinin yaklaşık %91,5'i tam siyahtı; bu enerji tüketimi ölçümü değildir.
Stil dosyalarının başvurduğu bütün görsel varlıkların mevcut olduğu denetlendi.
Canlı xsettingsd süreci sonlandırılmadan yapılandırması yeniden yüklendi.

## 12 Kasım 2026 stil güncellemesi

Güncel palet, çerçeve ölçüleri ve doğrulamalar [CYBERPUNK-STYLE.md](CYBERPUNK-STYLE.md) içinde.

## Thunar sürükle-seç kutusu — 22 Kasım 2026

Thunar'da fareyle toplu seçim kutusunun içi opak siyahtı ve altındaki
dosyaları gizliyordu. Neden: SKYNET bölümündeki
`.view, textview text, treeview.view { background-color: #000000; }` kuralı.
GTK 3 kutuyu ayrı bir düğüm olarak değil, görünümün kendi stiline
`.rubberband` sınıfı ekleyerek çizer; aynı özgüllükteki sonraki kural yarı
saydam kırmızıyı eziyordu. Hemen ardından `.view.rubberband` vb. kural eklendi:
`rgba(227, 38, 54, 0.22)` dolgu, `#ff4050` kenar. Simge ve ayrıntı
görünümünde geçerli; GTK 4'te kutu ayrı düğüm olduğundan etkilenmez.
Test: `tests/test_gtk_rubberband.py`. Açık Thunar'ın yeni stili alması için
`thunar -q` ile kapatılıp yeniden açılması gerekir.

