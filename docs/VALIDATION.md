# Yayın öncesi kontrol — 18 Ekim 2026

Debian 13, x86_64, Python 3.13 üzerinde:

- DWM, dmenu/stest, slstatus, xwinwrap, gtkgreet-skynet, saver-lock-style,
  tuigreet-battery ve yamalı XSecureLock kaynakları başarıyla derlendi.
- XSecureLock 1.9.0 kaynak arşivinin SHA-256 değeri doğrulandı; yerel yama
  `--fuzz=0` ile uygulandı. Upstream `system()` dönüş değerleri için üç
  `warn_unused_result` uyarısı var; derleme hatası yok.
- Geri yükleme aracı: dört test geçti (yazmayan önizleme, yedek/izinleri koruma,
  tekrar çalıştırma, symlink ve dosya/dizin çakışmasında yazmadan durma).
- Ses durumunu saklama aracının mevcut 12 testi geçti.
- 29 Python ve 20 kabuk/OpenRC dosyasının sözdizimi kontrol edildi.
- Yayına girecek içerikte bilinen anahtar/token örüntüleri, özel anahtar
  dosyaları, ELF ikilileri, `.ko` modülleri ve `.deb` arşivleri bulunmadı.
  `SHA256SUMS` depo içeriğinin tamamı için üretildi.

Eksik GTK/JSON derleme bağımlılıkları sistem paket veritabanına kurulmadan
geçici dizinde açıldı. Derlenen programlar çalışan sisteme kurulmadı.
Bu yayında giriş ekranı/ekran kilidi fiilen çalıştırılmadı; parola, kapatma,
yeniden başlatma veya çekirdek modülü yükleme testi yapılmadı.

OpenRC dosyaları taslak durumunda; gerçek Devuan/OpenRC oturum, servis,
kilit ve güç davranışı henüz doğrulanmadı. DKMS/VMD kaynakları bu yayın
hazırlığında tekrar derlenmedi; önceki sistemin kaynak kaydı olarak alındı.
