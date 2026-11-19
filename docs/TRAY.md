# Tepsi köprüsü düzeltmesi — 4 Kasım 2026

Kurulu snixembed 0.3.3, `StatusNotifierItem` özellik sorgusundan dönen genel
D-Bus Failed hatasını yakalamıyordu. Özellikle bazı Qt/Electron simgeleri
ad veya tema yolu sağlayamadığında her NewIcon mesajı yeni uncaught/CRITICAL
kaydı üretiyordu. Canlı tanılama bu makinede Ferdium'un
`org.freedesktop.StatusNotifierItem-17380-1` öğesini işaret etti. Uygulamanın
kendisi veya hesabı değiştirilmedi; köprü mevcut pixmap/önbellekle devam eder.

Yeni `0.3.3-skynet1` uygulama ve özellik adını ilk hatada tanılama olarak
yazar, son geçerli simgeyi korur ve başarılı güncellemeleri işlemeye devam
eder. Sorunu gizlemek için stderr veya GLib günlükleri kapatılmaz.

Seyrek GDK `gdk_window_thaw_toplevel_updates` uyarısı için yalnız
`set_name` yerine `set_title` kullanmak yeterli olmadı: 4 Kasım açılışında
uyarı tekrarlandı. GTK kaynağında `visible` özelliğinin construct olmadığı,
`constructed` aşamasının pencereyi önce gösterdiği doğrulandı. Bu nedenle
`Object.new(..., "visible", false)` ardından `visible=true` kullanımı da
hide/unrealize/show döngüsü yaratıyordu. Son sürüm varsayılan görünür
`Gtk.StatusIcon` oluşturur, yeniden gizleyip göstermez; açıklama için
pencereyi yeniden oluşturmayan `set_title` kullanır.
[GTK 3 kaynak kodu](https://raw.githubusercontent.com/GNOME/gtk/gtk-3-24/gtk/deprecated/gtkstatusicon.c)
(`PROP_VISIBLE`, `constructed`, `set_visible`, `set_name`) incelendi.
İptal edilebilir async işlemler, açık simge/menü temizliği ve sağ tıkta
menü hazır olma kontrolü de korunur.

Simge piksel döngüsündeki `i += 3` hatası `i += 4` olarak düzeltildi;
boyut ve veri uzunluğu denetlenir, ARGB önbelleği yerinde değiştirilmez.
Bu, bozuk renkleri ve geçersiz piksel okumasını önler.

## Doğrulama ve sınırlar

- Debian arşivi `.dsc` özetiyle doğrulandı; kaynak/lisans depoda korundu.
- Aynı 30 NewIcon olayında eski kaynak 60 uncaught CRITICAL üretti. Yeni
  köprü hatayı yakaladı; son test dizisi kritik hata/uyarı olmadan geçti.
- Sol tıklama uygulamaya ulaştı; ilk sağ tık menüsü açıldı; menü eylemi
  D-Bus üzerinden test uygulamasına ulaştı. Bozuk pixmap → geçerli pixmap
  geçişi, kapanan uygulama ve köprünün açık kalması sınandı.
- Sahte uygulama D-Bus adını gerçekten bırakarak 30 kez kapatılıp yeniden
  açıldı; son simgenin sol tıklaması çalıştı. Yeni sürümde test boyunca
  0 CRITICAL, 0 WARNING ve 0 uncaught kaydı oluştu. Aynı gerçek yaşam
  döngüsü testi, hide/show kullanan önceki ikilide 29 GDK CRITICAL
  üreterek beklendiği gibi başarısız oldu. Yalnız tekrar kayıt
  isteği göndermek bu testi karşılamaz: watcher aynı kaydı reddeder.
- Kurulu son dosyanın SHA-256 özeti:
  `36ef4d3eeb8847703b7633932e662f5eac9738c132bec10e59eb3d97ffd27e65`.
  Kurulum sonrası yalnız köprü yenilendi; çalışan sürecin özeti eşleşti,
  tek köprü süreci ve tepsiye gömülü simge pencereleri doğrulandı. İlk
  74 saniyelik canlı gözlemde 0 CRITICAL/WARNING, Ferdium için iki
  özellik tanılama kaydı vardı. Son sürümle bir sonraki tam açılış henüz
  sınanmadı.
- Normal `make` ve sertleştirilmiş derleme başarılı. GTK StatusIcon
  kullanımı nedeniyle upstream/deprecation derleme uyarıları sürer;
  bunlar çalışma zamanındaki uncaught hatalarıyla aynı şey değildir.
- Tek kurulum hedefi `/usr/local/bin/snixembed`, root:root 0755. Autostart,
  ağ, kilit/PAM ve masaüstü teması değiştirilmez. Yalnız köprü yeniden
  başlatılır; açık uygulamalar kapatılmaz.

Her üçüncü taraf uygulamanın tüm menü türleri için garanti verilmez.
Beklenmedik uygulama yanıtları artık uygulama/özellik adıyla izlenebilir.
Kaynak, lisans, test ve belgeler kalıcıdır; indirilen paketler, açılmış
araç zinciri, test ekranları ve kurulum dosyaları işlem sonunda temizlenir.
