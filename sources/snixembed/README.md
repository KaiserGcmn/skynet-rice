snixembed - proxy StatusNotifierItems as XEmbedded systemtray-spec icons

INFO: recent electron versions [supports XEmbed tray icons again for now](https://github.com/electron/electron/pull/23674).
This means snixembed is of limited use. It will however be maintained in case
electron or other software eventually drops their XEmbed support again.

Previously, electron dropped support for the old XEmbed-based system tray
protocol, while many status bars for simple X window managers still do no not
support newer protocols like [StatusNotifierItem](https://freedesktop.org/wiki/Specifications/StatusNotifierItem/).
This project is basically a dirty hack using deprecated GTK+ StatusIcons to
proxy this new specification to the old one.

As newer electron versions support the old XEmbed-based tray icons again,
snixembed is currently not very useful, unless you rely on those old versions.
(or rely on chromium tray icons, which still only support StatusNotifierItem)
Most other software supports XEmbed icons as a fallback.

While snixembed works fine with most setups, some bars and DEs provide their
own optional SNI support, which should be preferred when available.

## Status
Currently supported:

- icons¹ (by pixmap and by freedesktop name)
- activation on left mouse button
- context menu on right mouse button (Menu dbusmenu or ContextMenu)
- tooltips (on hover, all markup except hyperlinks)
- limited AppIndicator support as a fallback (see Known issues and workarounds)

This is enough for electron apps like Riot and Signal, and also for most Qt
apps as the list above includes all functionality QSystemTrayIcon permits.
Please see the known issues and issue tracker if an app doesn't work properly.

¹: so-called AttentionIcons and OverlayIcons are not supported, but I have yet
to encounter software that uses this part of the spec. Qt does not support it.

## Usage
Simply launch `snixembed` to start watching for icons.

Some applications only present a tray icon if snixembed is available on start.
For autostarting, use `snixembed --fork` before starting SNI applications to
avoid race conditions. This will fork once the service is running. (e.g. in an
`.xinitrc`, use `snixembed --fork` instead of `snixembed &` before tray apps)

## Issues and support
Issues are tracked on sourcehut: [~steef/snixembed](https://todo.sr.ht/~steef/snixembed).
There's a Matrix room at [#snixembed:matrix.org](https://matrix.to/#/#snixembed:matrix.org)
for discussion and support. Come say hi!

## Building and installing
### Dependencies
- make (make)
- vala (make)
- gtk+-3.0, gio-2.0, glib-2.0
- libdbusmenu-gtk3-0.4, libdbusmenu-glib-0.4 (the most recent version)

These should be packaged in most major distributions.

### Building
Simply run `make` to build and if desired `make install` to install, by default
to `/usr/bin/snixembed`.

### Packages
There are AUR packages available:
[stable](https://aur.archlinux.org/packages/snixembed)
and [development](https://aur.archlinux.org/packages/snixembed-git).

For Gentoo/Portage, [powerman made an ebuild](https://github.com/powerman/powerman-overlay/tree/master/x11-misc/snixembed).

For Void Linux, it is [packaged by projectmoon](https://github.com/void-linux/void-packages/tree/master/srcpkgs/snixembed).

## Known issues and workarounds
- ayatana/libappindicator seem to think their standard is supported when they
  see the service, and then start talking appindicator to it. Therefore they
  do not fall back to XEmbed specification, and snixembed gets a load of
  AppIndicator jargon thrown at it. Currently, snixembed can handle basic
  AppIndicator functionality (icons and menus), and may support more in the
  future. But not everything works. Feel free to report issues to the tracker.

  As a workaround, you may start such applications with their own D-Bus
  session bus. They will be unable to communicate through D-Bus with the
  outside world, and therefore they won't find snixembed and fall back to the
  XEmbed tray icon. To do this, execute application like this:
  `dbus-launch --exit-with-session <application>`.

  As already mentioned, this will only work for apps that don't heavily rely
  on other services on the session bus for functionality. Examples that have
  been tested to work are discord and skypeforlinux.

  Alternatively, one could also choose to run snixembed on a separate session
  bus, and let all SNI-only apps run on that session bus too by running
  `dbus-daemon --session --print-address` and then setting the environment
  variable `DBUS_SESSION_BUS_ADDRESS` to the address printed by dbus-daemon
  for all applications that have to communicate with snixembed. This will
  isolate snixembed and those applications from the rest of the D-Bus world.
  As the author does not really use any non-SNI applcations, this is not well
  tested or supported, but I'm happy to assist anyone going this route or look
  into contributions that make this easier.

- some apps probe for StatusNotifierItem support not by checking for the D-Bus
  service but by checking environment variables. Exporting
  `XDG_CURRENT_DESKTOP=KDE` and `KDE_SESSION_CURRENT=5` seems to do the trick.

- `gtk_widget_get_scale_factor: assertion 'GTK_IS_WIDGET (widget)' failed`:
  This error could mean that no XEmbed tray is present.
