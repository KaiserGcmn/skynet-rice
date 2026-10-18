# TP-Link Archer T3U Plus LED sürücüsü

Bu kurulum, USB kimliği `2357:0138` olan adaptör için hazırlanmıştır.
Kaynak: https://github.com/lwfinger/rtw88
Sabitlenen commit: `a56bcd26e770257612a0803249cbd4095fc6feca`

DKMS paketi: `rtw88-tplink-led/0.6+a56bcd26e770`.
Yalnızca `rtw_core`, `rtw_usb`, `rtw_8822b` ve `rtw_8822bu` modülleri
kurulur. Kaynağın özgün Makefile dosyası derleme için korunmuştur.
LED kodu bu kaynak sürümünde etkindir.

Debian'ın özgün `rtw88_8822bu` sürücüsü silinmez. Yeni sürücü etkinken
`/etc/modprobe.d/tplink-led-driver.conf` dosyası eski USB sürücüsünün
otomatik yüklenmesini engeller. Dahili Intel kartın `iwlwifi` sürücüsü
değiştirilmez. Mevcut Wi-Fi ağı için önceden hazırlanan TP-Link önceliği
ve dahili kart yedeği korunur.

## Kurulum

```bash
bash /usr/local/src/tplink-led-driver/install.sh
```

Yönetici parolası, doğrudan terminalde `sudo` tarafından istenir.
Kurulum günlüğü `/var/log/expertbook/tplink-led-driver.log` dosyasındadır. Betik mevcut
`6.12.111+deb13-amd64` çekirdeği için hazırlanmıştır.
DKMS, sonraki çekirdeklerde derlemeyi otomatik dener; gelecekteki bir
çekirdek API değişikliği bu kaynak sürümünü uyumsuz hâle getirebilir.

## Eski sürücüye dönüş

```bash
bash /usr/local/src/tplink-led-driver/install.sh rollback
```

Bu komut yeni DKMS paketini ve onun blacklist dosyasını kaldırır,
Debian'ın özgün sürücüsünü yükler ve açılış dosyalarını günceller.
Kurulmuş çekirdek başlıkları ve inceleme için tutulan kaynak dosyaları kalır.

## Doğrulama

```bash
dkms status
nmcli device status
ls /sys/class/leds/
```

Yeni sürücüyle `/sys/class/leds/rtw88-*` altında LED kontrolü görünmelidir.
Fiziksel ışığın çalıştığı ayrıca adaptörün üzerinden gözle doğrulanmalıdır.
