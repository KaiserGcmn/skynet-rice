# Devuan Neon Arc GRUB arka planı — 2 Kasım 2026

Kullanıcının `~/wallpapers/Devuan Neon Arc Interface.png` görseli, baytları
değiştirilmeden `/boot/grub/themes/skynet-neon/background.png` olarak kuruldu.
1670×941 RGB PNG dosyası GRUB tarafından çizilir; ev dizinine erişim gerekmez.

Tema dosyası aynı dizinde `theme.txt` adını taşır. Menü logonun altındaki
koyu panelde gösterilir; normal yazılar açık gri, seçili satır beyaz yazılı
kırmızı bir şerittir. Görselde Devuan logosu bulunduğundan ikinci logo eklenmedi.
Menü ve geri sayım DejaVu Sans Mono Bold 28 kullanır. Başlangıçtaki 16 px yazı
büyütülmüş, satır yüksekliği 48 px ve aralık 8 px yapılmıştır. Panel ve seçim
çerçeveleri 18 küçük RGB PNG parçasından oluşur; arka plan görseli değişmez.

Terminal için Unifont Regular 16 korunur; gerekli PF2 dosyası dağıtımın
`/usr/share/desktop-base/grub-themes/desktop-grub-theme/unifont-regular-16.pf2`
dosyasından tema dizinine kopyalandı. Bu paket fontu depoda ikinci kez saklanmaz;
başka makineye bu temayı kurarken aynı font dosyasını da kopyalamak gerekir.
Menü fontu ve panel parçaları normal kullanıcı olarak yeniden üretilebilir:

```sh
python3 scripts/build-grub-assets.py /tmp/skynet-grub-assets
```

Bu işlem `grub-mkfont` ve
`/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf` gerektirir.
Üretilen `dejavu-mono-bold-28.pf2` dosyasını tema dizinine kurmak gerekir;
üretilmiş font ikilisi depoya alınmaz. Geometrik PNG parçaları ve üretici kodu
depoda saklanır. Üretici kaynak duvar kâğıdını okumaz veya değiştirmez.

`/etc/default/grub.d/99-skynet-wallpaper.cfg` yalnız `GRUB_THEME` değerini
ayarlar. Dağıtımın paket tema dosyaları değiştirilmedi. Üç saniyelik menü
süresi, varsayılan giriş, kernel parametreleri ve kurtarma girdileri korunur.

Kurulum yeni GRUB yapılandırmasını önce `/boot/grub` içinde geçici hedefe
üretti. `grub-script-check` başarılı oldu; menü/alt menü, linux/initrd,
chainloader, varsayılan giriş ve süre satırları önceki dosyayla karşılaştırıldı.
Eşleşme doğrulandıktan sonra yapılandırma atomik kuruldu. Hata durumunda eski
yapılandırma ve tema seçimini koruyan geri alma yolu kullanıldı. `grub-install`
çalıştırılmadı, initramfs veya firmware açılış kaydı değiştirilmedi.

Gerçek firmware/GRUB ekranında görsel test için yeniden başlatma yapılmadı.
Yeni görünüm bir sonraki açılışta kullanılır. Geri almak için yalnız
`99-skynet-wallpaper.cfg` dosyasını kaldırıp `update-grub` çalıştırmak önceki
paket temasını yeniden seçer; bundan sonra kullanılmayan `skynet-neon` tema
dizini kaldırılabilir.

Tema ve görsel `profiles/debian/rootfs/boot/grub/themes/skynet-neon/`, seçim
dosyası `profiles/debian/rootfs/etc/default/grub.d/` altında saklanır.
`restore-home.py` bu sistem dosyalarını otomatik kurmaz.
