<div align="center">

# SKYNET / REDLINE

**Siyah yüzeyler, kırmızı sinyaller.** Devuan 6 + SysVinit üzerinde çalışan,
kaynaktan derlenen bir DWM masaüstü.

![Devuan 6](https://img.shields.io/badge/Devuan-6%20Excalibur-c8102e?style=flat-square&labelColor=0b0b0b)
![SysVinit](https://img.shields.io/badge/init-SysVinit%20%2B%20elogind-c8102e?style=flat-square&labelColor=0b0b0b)
![DWM 6.8](https://img.shields.io/badge/WM-DWM%206.8-c8102e?style=flat-square&labelColor=0b0b0b)
![X11](https://img.shields.io/badge/display-X11-c8102e?style=flat-square&labelColor=0b0b0b)

![SKYNET masaüstü](docs/screenshots/desktop.png)

</div>

| Giriş ekranı | Kilit ekranı | Terminal |
| :---: | :---: | :---: |
| ![Giriş ekranı](docs/screenshots/greeter-hud.png) | ![Kilit ekranı](docs/screenshots/lock-hud.png) | ![Kitty ve Fastfetch](docs/screenshots/terminal-fastfetch.png) |

## Özellikler

- **DWM 6.8 + slstatus** — çalışma alanları, CPU, RAM, pil, tarih ve saat tek kırmızı barda.
- **Giriş ve kilit ekranı** — greetd ve XSecureLock; ortak canlı HUD, parmak izi + parola, Reboot / Shut down.
- **Tema** — SKYNET Black Red GTK 2/3/4; Qt, Kitty, Dunst, VLC ve Floorp uyumlu; kırmızı simge teması, HUD imleci ve AMOLED siyah VS Code teması.
- **Duvar kâğıdı** — GIF, 4K dahil video veya resim (video yeniden kodlanmadan oynatılır); GRUB için Neon tema.
- **Ses** — USB ve şarj cihazı sesleri, hoparlör ve mikrofon için ayrı mute LED'leri.

## Sistem

| | |
| --- | --- |
| Dağıtım | Devuan 6 (Excalibur), SysVinit + elogind |
| Oturum | X11, DWM, Kitty |
| Giriş / kilit | greetd + gtkgreet-hud / xss-lock + XSecureLock |

## Kurulum

```sh
git clone https://github.com/KaiserGcmn/skynet-rice.git
cd skynet-rice
python3 scripts/restore-home.py           # önizleme
python3 scripts/restore-home.py --apply   # uygula (değişen dosyalar yedeklenir)
python3 scripts/build.py --with-locker    # bileşenleri derle, sisteme kurmaz
```

Derleme bağımlılıkları `manifests/build-dependencies.txt` içindedir. Ayrıntılar:
[RESTORE.md](docs/RESTORE.md). Testler: `python3 -m unittest discover -s tests`.

## Belgeler

- **Görünüm:** [DWM bar](docs/DWM-BAR.md) · [GTK teması](docs/GTK-THEME.md) · [Cyberpunk stili](docs/CYBERPUNK-STYLE.md) · [Fastfetch](docs/FASTFETCH.md) · [Duvar kâğıdı](docs/WALLPAPER.md) · [İmleç](docs/CURSOR.md) · [VS Code](docs/VSCODE-UI.md)
- **Giriş ve kilit:** [Güvenlik](docs/SECURITY.md) · [Biyometrik](docs/BIOMETRIC.md) · [Kilit kontrolleri](docs/LOCK-CONTROLS.md)
- **Sistem:** [Devuan + SysVinit](docs/DEVUAN.md) · [Ses](docs/AUDIO-FEEDBACK.md) · [USB sesleri](docs/USB-SOUNDS.md) · [NVMe / VMD](docs/NVME-VMD.md) · [Bakım kaydı](docs/MAINTENANCE.md)

Tüm notlar [`docs/`](docs/) altındadır.

## Kapsam ve lisans

Bu depo bir disk yedeği değildir; anahtarlar, parolalar ve tarayıcı profilleri
dahil edilmez (`scripts/check-public.py` denetler). Bileşenler kendi lisanslarını
korur; ayrıntılar: [PROVENANCE.md](docs/PROVENANCE.md).
