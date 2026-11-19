# Kitty compatibility

Current installation (2026-11-11): the native distribution package carries the
backport and normal launches use `/usr/bin/kitty`. See
[debian/README.md](debian/README.md) for its source, security fixes, tests and APT
update behavior. The standalone installation below is historical; the current
launcher no longer selects it. Do not delete its files while an existing
terminal still uses them.

## Previous standalone 0.50.0 build — 2026-11-05

Optional native Kitty build at `~/.local/lib/skynet-kitty`. The launcher in
`home/.local/bin/kitty` selects it on DWM/X11 with a separate single-instance
group. The Debian package and Codex binary remain unchanged. Wayland sessions
use `/usr/bin/kitty`. No terminal stream filter or disabled keyboard features.

## Runtime patch

- Upstream 0.50.0 implements OSC 7501 program status and understands the
  modifyOtherKeys **reset** Codex actually sends (`CSI >4;0m`). The earlier
  synthetic test also enabled modifyOtherKeys without Kitty keyboard mode;
  that is a different operation and still produces an upstream warning.
- DEC 1007 now has real state, query, save/restore, reset and alternate-screen
  wheel-to-cursor-key behavior. Default on preserves Kitty's previous behavior.
  Disabling it stops synthesized arrow keys. Normal scrollback and explicit
  mouse reporting retain their original behavior.
- DEC 2026 set/reset is idempotent: duplicate commands preserve the frozen
  frame and original timeout. Allocation/state-change failures still log an
  error. The false duplicate-mode warning from actual Codex startup is corrected.
- The SysVinit guard prevents scope requests when `/run/systemd/system` is absent.
- Native packages find bundled Slang beside the executable; explicit `SLANGC`
  still takes precedence.

## Verified build inputs

Official [0.50.0 release](https://github.com/kovidgoyal/kitty/releases/tag/v0.50.0):

| File | SHA256 |
| --- | --- |
| `kitty-0.50.0.tar.xz` | `01f20d0b253af0a7e041394a501adc83483f2eee01faf607a933c028343ab71a` |
| `kitty-0.50.0-x86_64.txz` | `f04b11775574d6aabfb529b7e734cc0a7d7d12c7df9fb8ec1843e45420e514ee` |

Hashes matched official GitHub release API digests; no GPG verification claimed.
GPLv3 source notices remain intact. Core terminal/X11 code links system Python
3.13/shared libraries. Unchanged official kitten, fonts, shaders and Slang are
reused; an additional Go toolchain is not required. Stack protection, upstream
fortify flags, RELRO/NOW and non-executable stack are retained.

Build dependencies follow [upstream instructions](https://sw.kovidgoyal.net/kitty/build/).
Seven missing header packages were downloaded with APT and extracted temporarily,
without installing packages: `libpython3.13-dev`, `liblcms2-dev`,
`libxkbcommon-x11-dev`, `libx11-xcb-dev`, `libxcb-xkb-dev`, `libxxhash-dev`,
`libsimde-dev`. Temporary pkg-config prefixes referenced that extraction root;
linker symlinks referenced installed shared libraries. Runtime ELF dependencies
do not point into the temporary root. Installed wayland-protocols lacks a new
0.50.0 requirement: this build targets X11, not Wayland.

## Rebuild and validate

1. Verify both archives and safely extract the source in a temporary directory.
   From the source directory, apply `kitty-0.50.0.patch` using `patch -p1 --fuzz=0`.
2. From this repository run `python3 sources/kitty-compat/package.py SOURCE
   BINARY_ARCHIVE OUTPUT`, using absolute paths and a nonexistent OUTPUT.
   Optional `--headers ABSOLUTE_EXTRACTED_ROOT` supports the header setup above.
   This script packages only; it never installs or downloads.
3. From the source directory, execute `test_compat.py` using the built Kitty's
   `+runpy` and `runpy.run_path`. Also run upstream `kitty_tests.parser`, `screen`,
   `keys`, `mouse` and `program_status` via Python unittest inside the built Kitty.
4. Run `python3 sources/kitty-compat/gui_test.py OUTPUT/bin/kitty NEW_PRIVATE_DIR
   /absolute/path/to/codex`. Requires DWM, Xephyr, xauth and xdotool. Optional
   Codex probe uses an empty unauthenticated CODEX_HOME, submits no prompt and
   uses a non-working local HTTP proxy. It does not touch the live Codex session.
5. Atomically install the validated output at the runtime location and restore
   the launcher; preserve the package-managed `/usr/bin/kitty` fallback.

## Validation — 2026-11-05

- Seven local regression tests and 109 relevant upstream tests passed.
- Private authenticated Xephyr: real wheel on/off, Shift+Enter, Ctrl+C, SGR
  mouse reports and keyboard mode queries passed. Repeated synchronized-output
  starts retain the original two-second safety timeout. Kitty stderr was empty.
- Real Codex 0.166.0 fresh onboarding starts and exits without Kitty diagnostics.
  This is not a full authenticated conversation/model-request test.
- User theme, font size, render and remote-control options match the previous
  terminal; configuration parses without errors. No remote listener enabled.
- Upstream negative tests still emit intentional invalid-command diagnostics;
  logging is not disabled.

This local fork is **not updated by APT**; APT still updates the fallback.
Review upstream security/compatibility changes and rebuild verified releases.
Periodic upstream update checking is disabled for this locally patched package.
Removing its runtime directory returns the launcher to the distribution Kitty.
Existing windows retain their loaded version until closed normally.

References: [upstream changes](https://sw.kovidgoyal.net/kitty/changelog/),
[synchronized-output semantics](https://github.com/contour-terminal/vt-extensions/blob/master/synchronized-output.md).
