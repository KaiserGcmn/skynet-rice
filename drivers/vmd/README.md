# VMD MTL016 kaynak kaydı

`pristine/vmd.c`, Debian Linux 6.12.113 kaynağı; `backport.patch` etkin
`0.6-mtl016-b437504-deb13-113` düzeltmesini üretir. Kaynak sistemdeki tam ABI:
`6.12.113+deb13-amd64`. Derlenmiş `.ko` veya initramfs depoda bulunmaz.

Yamayı yalnızca kaynak üzerinde incelemek için (modül kurulmaz/yüklenmez):

```sh
mkdir -p .build/vmd-review
cp drivers/vmd/pristine/vmd.c .build/vmd-review/vmd.c
patch --batch --fuzz=0 -d .build/vmd-review -p1 < drivers/vmd/backport.patch
```

Yeni Devuan çekirdeğinin düzeltmeyi zaten içerip içermediği önce kontrol edilir.
Yama gerekiyorsa o çekirdeğin kaynağı/başlıkları, symbol CRC/vermagic ve Secure
Boot politikasıyla yeniden doğrulanır. Eski modül başka çekirdeğe kopyalanmaz.
`historical-build.py` kaynak paketi, önceki yama ve eski doğrulama çalışma
dizinlerini bekleyen tarihsel betiktir; doğrudan kurulum komutu değildir.

Eski initramfs kancasının ve stock VMD kurtarma girdisinin örnekleri
`profiles/debian/rootfs/etc/` altında tutulur. Gerekli modül/önyükleme dosyaları
oluşturulmadan bu dosyaları `/etc` altına kopyalama.
