# NVMe / VMD MTL016 düzeltmesi — 2026-11-04

## DKMS'e geçiş — 2026-11-19

**Neden:** 6.12.115 için elle kurulan override, 6.12.116 ve 6.12.117
güncellemelerine taşınmadı. Çalışan sürücü yeniden dağıtımın `0.6`
sürümüne döndü ve takılmalar geri geldi. `kern.log` arşivinde her açılış,
çekirdek sürümüyle eşleştirildi:

| Dönem | Sürücü | Açılış | `completion polled` |
|---|---|---|---|
| 19 Eki 16:40 – 2 Kas | 6.12.113 yamalı | ~50 | 0 |
| 2 – 4 Kas | 6.12.115 dağıtım | 9 | 39 |
| 4 – 9 Kas | 6.12.115 yamalı | 10 | 0 |
| 9 – 19 Kas | 6.12.116/117 dağıtım | 27 | 97 |

SMART temiz (critical warning 0, media error 0, hata günlüğü boş).
BIOS'ta VMD kapatılamıyor. TLP bu sorunun nedeni değil: zaman aşımları
TLP başlamadan, kök bağlanırken de görüldü; `PCIE_ASPM_*=default` ayarlı;
VMD denetleyicisinin `runtime_suspended_time` değeri 0.

**Kaynak:** Debian `linux-source-6.12_6.12.117-1_all.deb`, APT ile indirildi.
SHA-256 `9141325315c7f1eca682113d185a8c77c82814aa6e32f7e127e61d6106403835`,
APT paket kaydıyla eşleşti. İçindeki `vmd.c`
(`pristine/vmd-6.12.117.c`, SHA-256 `e36d7995…3e82`) 6.12.113–116 kaynağından
farklı. Eklenenler `vmd_get_bus_number_start()` içinde `PCI_POSSIBLE_ERROR`
kontrolü ve `case 3`; kesme yoluna dokunmuyor. Eski kaynakla 117 başlıklarına
karşı yapılan derlemenin `.text` bölümü dağıtım modülünden farklı çıktı. 117
kaynağıyla yeniden derlenen stock modülün `.text` bölümü ise dağıtım
modülüyle birebir aynı. `backport.patch` bu kaynağa `--fuzz=0` ile yalnız
satır kaymasıyla uygulandı. `W=1` uyarısız, tüm ithal sembol CRC'leri
`Module.symvers` ile eşleşti. Yeni semboller `_raw_spin_lock` ve
`_raw_spin_unlock`. Disassembly'de `vmd_irq` sırası şöyle:
kilit → 16 bit okuma → kilit açma → `generic_handle_irq`.

**Paket:** `drivers/vmd/dkms/` (`vmd-mtl016/0.6-mtl016.1`, modül sürümü
`0.6-mtl016-deb13-117`), `/usr/src/vmd-mtl016-0.6-mtl016.1` altına
kuruldu. DKMS modülü `/lib/modules/<sürüm>/updates/dkms/` altına koyar,
`/var/lib/dkms/mok.key` ile imzalar ve dağıtım dosyasını silmez.

**Güvenlik kilidi:** `dkms.conf`, hedef çekirdeğin dağıtım `vmd.ko`
`srcversion` değerini okur. `srcversion`, `vmd.c` içeriğinin özetidir.
Ölçülen değerler: 113/115/116 için `DCAC3E633F46229E3E74768`, 117 için
`9CED7F0241F8FAD2F7858E3`. Değer `9CED7F02…` değilse `BUILD_EXCLUSIVE_KERNEL`
hiçbir sürümle eşleşmez. DKMS bu durumu 77 çıkış koduyla "atlandı" olarak
işler; çekirdek paketinin `postinst` adımı başarısız olmaz. Sistem dağıtımın
yamasız sürücüsüyle açılır. 6.12.116 üzerinde atlama, 6.12.117 üzerinde
derleme denendi. DKMS çıktısının `.text` bölümü doğrulanmış yamalı derlemeyle
aynı.

**Kurulum (root):** `dkms add/build/install -k 6.12.117+deb13-amd64`, ardından
`update-initramfs -u -k 6.12.117+deb13-amd64`. Orijinal initramfs
`/boot/initrd.img-6.12.117+deb13-amd64.skynet-stock` olarak saklandı
(20 Kasım 2026'da, yamalı initrd ile çok sayıda sorunsuz açılıştan sonra
kullanıcı onayıyla silindi; geri dönüş yolu GRUB'daki 6.12.116 girdisidir).
Kurulum sırasında şunlar doğrulandı:
- `modinfo -k` DKMS yolunu seçiyor.
- Yeni initramfs açıldığında içindeki `updates/dkms/vmd.ko.xz` modülünün
  `.text` bölümü doğrulanmış yamalı derlemeyle aynı.
- initramfs içindeki `modprobe --show-depends vmd` aynı yolu seçiyor.
- initramfs'te `nvme`, `nvme-core` ve `ext4` mevcut.

**Yeniden başlatma sonrası:**
- `/sys/module/vmd/version` = `0.6-mtl016-deb13-117`, srcversion
  `B6060B1858F3C89288A5273`.
- İlk 6 dakikada `completion polled` sayısı 0. I/O PSI tam bekleme
  toplamı 0,36 sn; önceki açılışta 33,9 sn idi.
- NVMe `Unsafe Shutdowns` 144'te kaldı.

Bunlar yalnız ilk açılışın ölçümleri; uzun dönem gözlem gerekir.

**Geri dönüş:**

```sh
sudo dkms remove vmd-mtl016/0.6-mtl016.1 --all
sudo update-initramfs -u -k 6.12.117+deb13-amd64
```

Açılmazsa GRUB "Advanced options" menüsünden 6.12.115'i seçin; elle kurulan
yamalı override hâlâ onda.

**Sonraki çekirdekler:** Her güncellemeden sonra
`cat /sys/module/vmd/version` kontrol edilir. Değer yalnız `0.6` ise kaynak
değişmiş ve kilit derlemeyi atlamıştır. Bu durumda yeni `linux-source`
içindeki `vmd.c` alınır ve yukarıdaki stock `.text` eşitliği ile yama
uygulaması tekrarlanır. Ardından `pristine/`, `dkms/vmd.c`,
`VMD_STOCK_SRCVERSION` ve `PACKAGE_VERSION` güncellenir.
`tests/test_vmd_dkms.py` şunları denetler:
- Yama, `pristine/vmd-6.12.117.c` üzerine `--fuzz=0` ile uygulandığında
  `dkms/vmd.c` ile aynı çıktıyı veriyor.
- Quirk yalnız `0x7d0b` aygıtında etkin.
- Bilinmeyen çekirdekte kilit kapalı kalıyor.

Aynı işlemde: 6.12.113 paketleri kaldırıldı (117 ana, 115 yamalı yedek,
116 dağıtım yedeği kaldı). `kernel.panic = 10` ayarlandı
(`profiles/debian/rootfs/etc/sysctl.d/90-panic-reboot.conf`). Kök için tam
fsck istendi. `/forcefsck` bu sistemde etkisiz kaldı, çünkü kökü initramfs
denetliyor. Bu yüzden `tune2fs -c 1` ile tek sefer zorlandı; fsck'den sonra
`tune2fs -c -1` ile geri alınacak.

## Eski özel GRUB yedeğinin kaldırılması — 2026-11-12

Kullanıcı isteğiyle `skynet-vmd-stock` kimlikli **Devuan 6.12.115 - original
VMD (recovery)** girdisi ve yalnız ona ait
`/boot/initrd.img-6.12.115+deb13.1-amd64.skynet-stock` kaldırıldı. Başka girdi
içermeyen `/boot/grub/custom.cfg` de silindi; 110776556 bayt boşaldı.
Aşağıdaki orijinal kurulum notlarındaki bu özel yedek artık mevcut değildir.

Çalışan çekirdek ve normal ilk GRUB girdisi `6.12.116+deb13-amd64` olarak
doğrulandı. `GRUB_DEFAULT=0`, üç saniyelik normal menü süresi, tema, güvenlik
parametreleri, mevcut kernel/initramfs ve diğer çekirdek paketleri korunur.
GRUB ortamında farklı çekirdeğe yönlendiren tek seferlik seçim yoktu.
Sonraki resmî çekirdek güncellemeleri normal ilk girdiyi yenilemeye devam eder.

`41_custom`, özel dosyayı ancak varsa çalışma anında yükler. Bu nedenle
üretilmiş `grub.cfg` yeniden yazılmadı; `grub-install`, initramfs üretimi veya
yeniden başlatma çalıştırılmadı. GRUB sözdizimi ve korunan dosyaların hashleri
kontrol edildi. İşlemde hata durumuna karşı bellekte geri dönüş kopyaları
tutuldu; başarılı işlem sonunda geçici çalışma dosyaları temizlendi.

`scripts/retire-vmd-grub-backup.py` bu tek seferlik işlemin sınırlı bakım
aracıdır; otomatik restore/boot kancası değildir. Beklenmeyen çekirdek,
varsayılan girdi, symlink veya başka yedek referansında değişiklikten önce
durur. Altı test; yalnız hedef girdinin kaldırılması, diğer içeriklerin
korunması, tekrar çalıştırma, hatalı hedeflerin reddi ve boş özel menü
dosyasının geçerli kaldırılma durumu olduğunu sınar.

Bu işlem Devuan 6 / SysVinit, `6.12.115+deb13.1-amd64` için hazırlanmıştır.
Denetleyici `8086:7d0b`, altındaki SSD Micron 2500 / `1344:5425`.
Günlükte tekrarlanan `timeout, completion polled` mesajları, sağlıklı SMART
sonucuyla birlikte, VMD kesmesinin DMA yazılarından erken ulaşması sorunuyla
uyumludur. Bu eşleşme tek başına kesin teşhis değildir; düzelmenin gerçek
doğrulaması yeni sürücüyle yeniden başlatma ve kullanım gözlemidir.

## Kaynak ve kapsam

- [Linux PCI yama tartışması](https://lists.openwall.net/linux-kernel/2026/10/05/2042):
  MTL016 için kesmeyi alt aygıta iletmeden önce **alt aygıtın** PCI yapılandırma
  alanından okuma; okuma boyunca `cfg_lock`. VMD'nin kendi BAR'ından okuma değil.
- `drivers/vmd/backport.patch` mevcut tarihsel 6.12 uyarlamasıdır. Yeni derleme
  yalnız modül sürüm etiketini `0.6-skynet-mtl016-deb13-115` yapar; 7d0b dışındaki
  aygıtların davranışını değiştirmez. Tarihsel etiketteki commit kimliğinin
  upstream'de birleştirildiği bu işlemde doğrulanmamıştır.
- Debian `linux-source-6.12_6.12.115-2_all.deb` SHA256:
  `dd4eb9248eb941e769688d847d5046ab7d05d3608e156ec07da0863a3230f03c`.
  APT paket bilgisiyle doğrulandı. İçindeki `vmd.c`, depodaki 6.12.113 kaynak
  dosyasıyla aynı SHA256'ya sahip; eşitlik varsayılmadı, ölçüldü.

`drivers/vmd/build-6.12.115.py WORKDIR`, indirilen paketin bulunduğu ayrı çalışma
dizininde stock kontrol modülünü ve yamalı modülü derler; kurulum yapmaz.
Stock `.text` bölümünün paketli modülle birebir eşitliği, modül vermagic,
PCI alias listesi, bağımlılıklar ve tüm ithal sembollerin CRC değerleri
kontrol edilir. `W=1` derlemesi uyarısız tamamlandı. Eklenen iki sembol
`_raw_spin_lock` ve `_raw_spin_unlock`; bunlar da aynı çekirdeğin başlıklarıyla
doğrulandı. Disassembly'de kilit–16 bit okuma–kilit açma sırasının alt kesme
işleyicisinden önce bulunduğu kontrol edildi.

## Kurulum ve geri dönüş

Yönetici kurulum aracı `drivers/vmd/install-6.12.115.py WORKDIR` açıkça
hazırlanmış hash manifesti ve doğrulama sonucu ister. Normal restore işleminde
otomatik çalıştırılmaz. Canlı VMD sürücüsünü kaldırmaz veya yeniden yüklemez.

- Override: `/lib/modules/6.12.115+deb13.1-amd64/updates/vmd-mtl016/vmd.ko`.
  Dağıtımın `kernel/drivers/pci/controller/vmd.ko.xz` dosyası korunur.
- Yeni initramfs önce geçici konumda oluşturulur, açılıp içindeki modülün hash'i
  ve modprobe çözümlemesi doğrulanır. Eski initramfs'teki modüllerin hiçbirinin
  kaybolmadığı, NVMe/ext4 ve init dosyalarının bulunduğu kontrol edilir.
- Orijinal initramfs `/boot/initrd.img-6.12.115+deb13.1-amd64.skynet-stock`
  olarak korunur. Bu dosya kurulum artığı değil, geri dönüş dosyasıdır.
- `/boot/grub/custom.cfg`, mevcut normal girdinin çekirdek parametrelerini
  koruyarak **Devuan 6.12.115 - original VMD (recovery)** seçeneğini ekler.
  Var olan `41_custom` yükleyicisi kullanılır; `grub.cfg` yeniden yazılmaz.
- Normal girdinin initramfs'i ancak doğrulamalar bitince atomik değiştirilir.
  Başarısızlıkta bu işlemde eklenen dosyalar kaldırılır ve modül indeksi geri
  oluşturulur. Eski 6.12.113 çekirdeği/initramfs'i değiştirilmez.

Açılışta sorun olursa GRUB'dan yukarıdaki **original VMD (recovery)** girdisini
seç. Aynı 6.12.115 çekirdeği orijinal initramfs ve sürücüyle başlar. Kalıcı geri
alımda yalnız bu override kaldırılıp `depmod -a 6.12.115+deb13.1-amd64` çalıştırılır
ve orijinal initramfs normal adına atomik geri taşınır; sonra bu işleme ait
custom.cfg girdisi kaldırılır. Başka özel girdiler eklenmişse dosyanın tamamı
silinmez. Geri dönüş dosyası doğrulama tamamlanmadan kaldırılmamalıdır.

## Güvenlik ve sonraki açılış

Bu yerel derlenmiş bir çekirdek modülüdür; dağıtım imzalı modül değildir.
Secure Boot işlemden önce kapalıydı; durumu değiştirilmez. Yerel modül yüklenmesi
çekirdeğin dış modül/imza taint bayraklarına yansıyabilir; kernel hata raporlarında
belirtilmelidir. IOMMU, DMA koruması, kernel hardening, PAM, TLP, NVMe zaman aşımı,
APST/ASPM ve USB-C ayarları bu işlem kapsamında değiştirilmez.

Yalnız bu tam kernel ABI'si için kurulur; farklı bir çekirdeğe otomatik taşınmaz.
Çekirdek güncellemesi sonrasında VMD sürümü ve hata günlükleri yeniden incelenir.
Eski 6.12.113'e ait initramfs kancası ilk kurulumda korunmuş, aşağıda açıklanan
kullanıcı isteğiyle temizlik sırasında kaldırılmıştır.

Yeniden başlatmadan sonraki kontroller:

```sh
uname -r
cat /sys/module/vmd/version
sudo dmesg | grep -Ei 'nvme.*(timeout|reset|error)|vmd|I/O error'
cat /proc/pressure/io
```

Beklenen sürücü sürümü `0.6-skynet-mtl016-deb13-115`.
`modinfo vmd` diskteki gelecek açılış modülünü, `/sys/module/vmd/version` ise
gerçekte çalışan modülü gösterir. İlk açılıştan sonra normal kullanım boyunca
timeout sayısının artmaması gözlenmeden sorun kesin giderildi denmez. Ağır
yazma testi, cache boşaltma veya kullanıcı verisini etkileyen test gerekmez.

## Kurulum sonucu

2026-11-04 tarihinde kuruldu; aynı gün ilk yeniden başlatma kontrolü geçti.
Uzun süreli kullanım gözlemi ayrıca gereklidir. Kurulu override SHA256:
`fd1d7eeecad16334634dcd9d290ac631825e8329d02841f581ebe16fb2742ca4`.
Bağımsız son kontrolde initramfs, orijinal geri dönüş kopyası ve korunan
dosyaların hash'leri doğrulandı; çalışan sürücü hâlâ `0.6` idi.

`MODULES=most`, initramfs'e paketli ve yerel modülü birlikte alabiliyor.
İlk kurulum kontrolü bu durumda işlemi durdurdu; geri alımdan sonra mevcut
açılış dosyaları ve korunan ayarlar birebir aynı kaldı. Tamamlanan kurulumda
yalnız bilinen iki dosyaya izin verildi ve hem `vmd` adı hem gerçek PCI
modalias'ı için modprobe planının yalnız doğrulanmış override'ı seçtiği
kontrol edildi. İlk denemeden kalmış override veya geçici initramfs bırakılmadı.

İlk yeniden başlatmada `/sys/module/vmd/version` beklenen
`0.6-skynet-mtl016-deb13-115` değerini gösterdi; NVMe durumu `live`.
Açılıştan 211.49 saniye sonra okunan çekirdek günlüğünde NVMe timeout, reset
veya I/O hatası bulunmadı. `/proc/pressure/io` tam bekleme toplamı 0.319 saniye,
son 10 saniyelik ortalama %0.00 idi. Yerel modüle ait out-of-tree/imza taint
satırları beklendiği gibi mevcut. Bu sonuç yalnız ilk açılış ve olağan başlangıç
etkinliğini kapsar; ağır disk testi yapılmadı ve uzun dönem hatasızlığı kanıtlamaz.
GRUB'daki orijinal sürücüye dönüş seçeneği korunuyor.

## Eski özel sürücünün temizliği

2026-11-04, kullanıcının eski sürücüyü kaldırma isteği üzerine etkin olmayan
`/usr/local/lib/vmd-mtl016/6.12.113+deb13-amd64/vmd.ko.xz` ve yalnız ona bağlı
`/etc/initramfs-tools/hooks/zz-vmd-mtl016` kaldırıldı; boş dizinleri temizlendi.
Toplam 119458 bayt eski özel dosya kaldırıldı. Temizlik öncesindeki 608.88
saniyelik açılış günlüğünde NVMe timeout/reset/I/O hatası bulunmadı.

Dağıtım paketlerine ait VMD modülleri silinmedi. Etkin 6.12.115 override'ı,
her iki çekirdeğin mevcut initramfs'i ve GRUB geri dönüş dosyaları hash ile
kontrol edilerek korundu. Eski 6.12.113 initramfs'inin içinde önceki özel
modülün kopyası hâlâ vardır; mevcut yedek çekirdeğin açılışını değiştirmemek
için yeniden oluşturulmadı. O initramfs ileride yeniden oluşturulursa artık
özel kanca çalışmayacak, dağıtımın paketli sürücüsü kullanılacaktır.
