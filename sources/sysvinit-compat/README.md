# Targeted compatibility patches, 2026-11-05

These are reviewable patches for the installed Debian/Devuan package files,
not replacement init systems. They were applied with before/after SHA256
guards and rollback on verification failure. Package updates may replace
these files; review updated upstream behavior before reapplying a patch.
They are not applied automatically by desktop build or home restoration.

- `kitty-child.py.patch`: Kitty 0.41.1 child launcher checks whether systemd
  is actually the running init before attempting a systemd scope. Genuine
  scope errors on systemd hosts are still reported. No stderr filter.
- `zramswap.patch`: zram-tools uses syslog only when `/dev/log` exists; its
  existing console error/reporting branch covers early SysVinit boot.
  No swap size, priority or allocation policy change.
- `greetd.patch`: add the missing LSB `status` operation. Login/PAM and
  start/stop behavior are unchanged. Previously `status` only printed usage.
- `saned.patch`: use a single `::` listener when IPv6 is enabled and
  `bindv6only=0`, retaining IPv4-mapped clients. Otherwise use the original
  binding behavior. Scanner ACLs, privileges and firewall remain unchanged.

The saned candidate was exercised on a temporary high port as an ordinary
user: both IPv4 and IPv6 connected, with no duplicate-bind failure. No scan
was requested. The live scanner daemon was not restarted; its new launch
arguments apply on its next normal start. Early zram logging similarly
requires the next boot for end-to-end confirmation.
