# VMD MTL016 kaynak kaydı

**2026-11-19'dan beri etkin yol DKMS'tir:** `dkms/`, `vmd-mtl016/0.6-mtl016.1`.
- Kaynak: `pristine/vmd-6.12.117.c` + `backport.patch` = `dkms/vmd.c`.
- `dkms.conf`, hedef çekirdeğin dağıtım `vmd.ko` srcversion değeri
  `9CED7F0241F8FAD2F7858E3` değilse derlemeyi atlar. Bu durumda dağıtım
  sürücüsü kalır ve apt bozulmaz.
- Kurulum, doğrulama, geri dönüş ve yeni çekirdeğe taşıma adımları
  [NVME-VMD.md](../../docs/NVME-VMD.md) belgesinin en üstünde.
- Tutarlılığı `tests/test_vmd_dkms.py` denetler.

Aşağıdaki 6.12.115 araçları ve 6.12.113 bilgileri tarihsel kayıttır.

2026-11-04 / Devuan 6.12.115 için güncel, ayrı derleme ve kurulum araçları:
`build-6.12.115.py`, `install-6.12.115.py`. Kaynak doğrulaması, kapsam, yeniden
başlatma kontrolü ve orijinal sürücüye geri dönüş [NVME-VMD.md](../../docs/NVME-VMD.md)
belgesinde açıklanır. Aşağıdaki 6.12.113 bilgileri tarihsel kayıttır.

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
