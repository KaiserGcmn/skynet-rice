# Geri yükleme ve derleme

Hedef sistem Devuan + OpenRC. Önce [DEVUAN.md](DEVUAN.md) içindeki geçiş durumunu oku.
Bu depo bir kurulum ISO'su veya tek komutla dağıtım dönüştürücü içermez.

## Kullanıcı dosyaları

`python3 scripts/restore-home.py` yalnızca değişiklik listesini gösterir.
`--apply` ile ev dizinine yazılır; `--home /başka/mevcut/dizin` ile deneme yapılabilir.
Root olarak çalıştırmak, hedefte sembolik bağlantı üzerinden yazmak ve dizin
üzerine dosya yazmak reddedilir. Değişecek tüm eski dosyalar önce yedeklenir.
Yedekteki `manifest.json` önce var olan ve yeni oluşturulan yolları ayırır;
`files/` altındaki dosyaları aynı göreli yola geri koyarak eski ayarlara dönülebilir.

Geri yüklenenler: Bash/nvm başlangıç ayarları, Kitty teması, Dunst, Fastfetch,
bottom, GTK 2/3/4 görünümü, fontconfig, xsettingsd, Flameshot, Ferdium XDG
autostart kaydı, SKYNET duvar kâğıdı ve kilit arka planı. Programların kendileri
bu komutla kurulmaz. Ferdium'un yolu `/opt/Ferdium/ferdium`; farklı bir paket
kullanılırsa `.config/autostart/ferdium.desktop` güncellenmelidir. DWM'nin
`autostart.sh` betiği genel XDG autostart dosyalarını çalıştırmaz.

## Programlar

1. `manifests/build-dependencies.txt` derleme için gereken paketleri listeler.
2. `python3 scripts/build.py --with-locker` DWM, dmenu/stest, slstatus, xwinwrap,
   gtkgreet-skynet, saver-lock-style, tuigreet-battery ve xsecurelock-power derler.
3. Çıktı yolunu `.build/last-build.txt` gösterir. `rootfs/` altında kurulacak
   ikililer ve yardımcı betikler bulunur. Bu ağacı `/` üzerine topluca kopyalama:
   OpenRC'ye uyarlanmamış kilit/giriş yardımcıları da mevcut Debian sürümleriyle
   korunmuştur. DWM/dmenu/slstatus gibi bağımsız bileşenler ayrı kurulabilir.
4. `manifests/desktop-packages.txt` masaüstü bağımlılıkları için başlangıç
   listesidir. Devuan paket yöneticisinin çözdüğü sürümleri kullan; systemd
   kurmayı önerirse işlemi durdurup paket kaynağını düzelt.
5. Greetd/Cage/gtkgreet/tuigreet, Fastfetch/eza/bottom, Floorp, Ferdium,
   SpoofDPI ve snixembed dağıtım/üçüncü taraf paketlerinden ayrıca sağlanır.
   Bunların ikilileri ve hesap verileri depoya gömülmedi.

Kilit ekranı dağıtımın **xsecurelock** paketi, `auth_x11` ve `authproto_pam`
yardımcılarını gerektirir. `--without-pam`, özel bir PAM yardımcısı
derlenmemesi içindir; parola doğrulaması kaldırılmamıştır. Sürüm korumaları
özelleştirilmiş eski arayüzü kullanmak yerine paket arayüzüne dönebilir.
Yeni dağıtımda bu kontrolleri kaldırarak zorla özel sürüm kullanma.

VS Code eklentilerini tekrar kurmak için, VS Code kurulduktan sonra:

```sh
while IFS= read -r extension; do
    code --install-extension "$extension" || break
done < manifests/vscode-extensions.txt
```

`apt-packages.tsv` 2.671 paketin, `apt-manual.txt` 339 manuel işaretin
17 Ekim 2026 envanteridir. Bağımlılıklar, eski çekirdekler ve Plasma da
listede bulunur; OpenRC kurulum listesi olarak kullanılmaz. Node listesi
envanterdir; Node/npm veya Codex hesap verileri depoya kopyalanmadı.
Floorp eklentileri uBlock Origin ve Bonjourr; profil/oturum verileri alınmadı.

## GRUB ve donanım

- Güncel `/etc/default/grub` ve iki `grub.d/*.cfg` dosyası `profiles/debian/rootfs/`
  altında. Bir saniyelik menü, normal giriş seçimi ve çekirdek parametreleri korunuyor.
- Stock VMD kurtarma girdisi `.example` olarak tutulur. Eski disk UUID'si
  `@@ROOT_UUID@@` ile değiştirildi. Yeni sistemde doğru disk/çekirdek/initramfs
  yollarıyla tekrar oluşturulmalı. Eski `/boot/grub/grub.cfg` kopyalanmaz;
  yeni sistemin `update-grub` komutu çıktıyı yeniden üretir.
- VMD düzeltmesi yalnızca **6.12.113+deb13-amd64** için incelenmiş bir kaynak
  yamasıdır. Devuan'ın yeni çekirdeğine körlemesine yüklenmez. Eski initramfs,
  imzalı modüller ve imzalama anahtarları bu depoda bulunmaz.
- ExpertBook LED ve rtw88 kaynakları `drivers/` içinde. DKMS ile yeni çekirdekte
  tekrar derlenmeli. Secure Boot gerekiyorsa yeni sisteme ait anahtar üretilir.
- TLP, USB udev kuralları, nftables ve initramfs kancası cihaz/dağıtım ayarlarıdır;
  yeni cihazın veya yeni çekirdeğin gereksinimleriyle birlikte uygulanır.

`reference/debian-maintenance/` eski bakım işlemlerinin kaydıdır. Bazı betikler
çekirdek, açılış veya masaüstü paketlerini değiştirebilir; bunlar genel kurulum
adımlarına dahil edilmedi. Eski test hazırlama betiğinin varlığı o testin aktif
olduğu anlamına gelmez.
