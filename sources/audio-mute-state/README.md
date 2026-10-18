# Hoparlör ve mikrofon mute kaydı

Bu kullanıcı servisi normal oturum kapanışında donanım ses aygıtlarının mute
durumlarını kaydeder; sonraki açılışta PipeWire ve WirePlumber başladıktan sonra
geri yükler. Hoparlör ve mikrofon birbirinden bağımsızdır. Ses seviyesi ve varsayılan
aygıt seçimi değiştirilmez. ALSA ve Bluetooth aygıtları sabit adlarıyla eşleştirilir;
monitor kaynakları ve sanal uygulama aygıtları dışarıda bırakılır.

İlk çalıştırma mevcut durumu kaydeder, mute değiştirmez. Bu nedenle kurulumdan
sonra, bilgisayarı kapatmadan önce servisi bir kez başlatın:

```sh
systemctl --user daemon-reload
systemctl --user start audio-mute-state.service
```

Servis `default.target.wants` bağlantısıyla sonraki oturumlar için etkinleştirildi.
`After=` sıralaması, kapanıştaki kaydın ses servisleri durmadan önce yapılmasını
sağlar. Durum dosyası `$XDG_STATE_HOME/audio-mute-state/state.json` veya varsayılan
olarak `~/.local/state/audio-mute-state/state.json` konumuna atomik olarak yazılır.
Bağlantısı kesilen aygıtların kayıtları korunur. Açılıştan sonra takılan aygıtlar
için anlık geri yükleme yapılmaz. Ani güç kesilmesinde son normal kapanış kaydı
kullanılır.

Durum ve günlük:

```sh
systemctl --user status audio-mute-state.service
journalctl --user -u audio-mute-state.service -b
```

Kontrol: servisi başlatın, hoparlör ve mikrofonu ayrı ayrı mute edin, normal şekilde
yeniden başlatın. `wpctl get-volume @DEFAULT_AUDIO_SINK@` ve
`wpctl get-volume @DEFAULT_AUDIO_SOURCE@` çıktılarında `[MUTED]` görünmelidir.
Sonra mute'u kaldırıp yeniden başlatarak açık durumun da korunduğunu kontrol edin.

Testler:

```sh
cd /usr/local/src/audio-mute-state
python3 -m unittest -v
```

Kaldırma:

```sh
systemctl --user disable --now audio-mute-state.service
rm ~/.config/systemd/user/audio-mute-state.service
sudo rm /usr/local/libexec/audio-mute-state
systemctl --user daemon-reload
```
