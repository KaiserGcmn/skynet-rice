# Floorp sağ tık menüsünde simge boşluğu — 4 Kasım 2026

Kurulu Floorp 12.20.2 / Gecko 158.0.1, simgeli sayfa menüsünün düz
menu/menuitem satırlarında yazıyı arka plan simgesinin üzerine yerleştiriyordu.
Kullanıcının userChrome.css dosyasında özel kural yoktu. Aynı sorun temiz
test profilinde tekrarlandı; kurulu omni.ja içindeki Chrome Extras stili
bu satırlarda yalnız arka plan boşluğunu metin dolgusu olarak kullanıyordu.
Upstream rapor: https://github.com/Floorp-Projects/Floorp/issues/2816

`home/.config/dwm-desktop/floorp-context-menu.css` yalnız
`#contentAreaContextMenu` doğrudan altındaki düz satırlara en az 32 px
başlangıç dolgusu verir; 16 px simgeye ve metin aralığına yer ayırır.
Gerçek iconic satırlar, yer imleri ve checkbox/radio satırları dışarıda
kalır. Simge özelliği kapalıysa düzeltme uygulanmaz. Menü renkleri,
web sayfaları, kısayollar ve komutlar değiştirilmez.

## Profil bağlantısı

Etkin Floorp profilinin `chrome/userChrome.css` dosyasında, `@charset`
sonrasında ve diğer stil kurallarından önce şu satır bulunur:

```css
@import url("../../../skynet/floorp-context-menu.css");
```

Bu göreli yol `~/.config/floorp/PROFIL/chrome/` düzeni içindir;
`~/.config/dwm-desktop/floorp-context-menu.css` dosyasına gider. Başka profil
konumlarında göreli yol uyarlanmalıdır. Profilin kendisi, prefs.js,
çerezler veya diğer tarayıcı verileri depoya alınmaz. Restore merkezi CSS
varlığını kurar; mevcut profile bu import satırı ayrıca eklenmelidir.
Kurulu Floorp varsayılanlarında legacyUserProfileCustomizations.stylesheets
zaten true; bu ayar veya güvenlik tercihleri değiştirilmedi.

CSS sonraki tarayıcı açılışında yüklenir; kullanıcının açık tarayıcısı
kapatılmadı. Geri almak için yalnız import satırını kaldırmak yeterlidir.

## Doğrulama

Gizli Xephyr ve ayrı D-Bus üzerinde iki geçici Floorp profili çalıştırıldı.
Yalnız görsel tercihler kopyalandı; hesap/geçmiş/oturum verisi alınmadı.
Yerel test sayfasında bağlantı içindeki resmin sağ tık menüsü açıldı.
Önceki görünümde örtüşme tekrarlandı; CSS ile düz satırların ve alt menü
başlıklarının simge-yazı ayrımı görüntüde doğrulandı. Test profilleri,
özel X11/D-Bus süreçleri ve geçici dosyalar işlem sonunda temizlenir.

