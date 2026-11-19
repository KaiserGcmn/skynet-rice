# Kitty in the distribution package

The local `0.41.1-2+deb13u2+skynet1` package replaces the separate 0.50.0
runtime for normal launches. It retains Debian's original `/usr/bin/kitty`
launcher, library paths, dependencies, maintainer scripts, GLFW plugins,
shell integration and terminfo. Patched Python/C terminal code and the
matching Go helper are installed through dpkg. This is a local build, not an
official Debian binary; it must not be described as the upstream 0.50 release.

No hold, pin, alternate repository or automatic patch reapplication is added.
Debian version ordering is tested:
`0.41.1-2+deb13u2 < 0.41.1-2+deb13u2+skynet1 < 0.41.1-2+deb13u3`.
An official higher version can replace the package, including these patches.
Review compatibility again after that update; automatic preservation of local
patches is not promised. `apt update` refreshes indexes; `apt upgrade` installs
eligible updates.

## Changes

- SysVinit scope guard, DEC 1007 behavior/query/save/restore, idempotent DEC
  2026 without extending its timeout, and Codex's modifyOtherKeys reset.
- OSC 7501 bounded program-status parser/handler from upstream 0.50.0,
  adapted to the older title API and strict Python Base64 decoder.
- Security fixes from upstream: askpass shared-memory owner/mode validation,
  sanitized prompts and retaining the verified handle; decimal-only echo and
  matching SSH canary; Base64-encoded unknown color-query keys; multicell
  character capacity checking. Genuine invalid input still logs diagnostics.
- Go module mode uses pinned gopsutil/v4 (Debian's source patch uses a GOPATH
  import). Versions and hashes are captured by the patch's go.mod/go.sum.

Relevant upstream commits, adapted rather than applied wholesale:

- [Askpass](https://github.com/kovidgoyal/kitty/commit/3281919056c442e4ba6f5abed7ee2c5130de31ff)
- [Echo/canary](https://github.com/kovidgoyal/kitty/commit/9dca948e9bec3c926ab3370f2cd10f9b9b10821f)
- [Color responses](https://github.com/kovidgoyal/kitty/commit/03fbdad855490470233954bc810e517027e5e640)
- [Strict echo validation](https://github.com/kovidgoyal/kitty/commit/57bb144d96c0f9d48a2b0a6d43c9a23d2a091cbf)
- [Multicell capacity](https://github.com/kovidgoyal/kitty/commit/7d2fbaadcc2b1eeeef89bd875ec622b42362574b)

The existing Debian security patches remain applied. Later drag-and-drop
protocol fixes concern functionality introduced after this 0.41 base.
This is a targeted backport, not a complete security audit of Kitty.

## Authenticated inputs

Source artifacts were checked against the SHA256/size entry in
`trixie-security/main/source/Sources.xz`, itself verified against the signed
Debian security InRelease using `/usr/share/keyrings/debian-archive-keyring.gpg`.
The base binary was downloaded through APT and its hash checked. The source
index was authenticated on 2026-11-05; tests below were completed 2026-11-11.

| File | SHA256 |
| --- | --- |
| kitty_0.41.1-2+deb13u2_amd64.deb | 27a43046a7782bf803c51afd49bf257edf24d5563a02e723519d2ecbb5228576 |
| kitty_0.41.1-2+deb13u2.dsc | f0f0161516d189d124e7521b9dc275b5704fd53093033d3d8b100bc01e724ed1 |
| kitty_0.41.1.orig.tar.gz | 16b26d56a06b1c94f02b0b8f6c7c8e557d208083f8b75235b1fcb68ed69d8b3d |
| kitty_0.41.1-2+deb13u2.debian.tar.xz | 5e6c99f98b9c6ba6dfecdea780ad20c5dc40a835a114d5afb59d159d358edfaf |

## Rebuild

1. Authenticate/download the artifacts above, then extract with `dpkg-source`.
   Preserve its Debian patches and license notices. From that source root,
   apply `kitty-0.41.1-deb13u2.patch` with `patch -p1 --fuzz=0`.
2. Build against system Python 3.13 and the dependencies documented in the
   parent directory. Also supply librsync headers. Missing development .debs
   can be extracted in a temporary prefix; adjust their pkg-config prefixes
   and resolve dev symlinks against installed system libraries. No need to
   install an alternate Python or change system runtime libraries.
3. Run `python3 setup.py build --skip-building-kitten`, supplying the temporary
   include/library directories with `--extra-include-dirs`,
   `--extra-library-dirs`, `--python-compiler-flags` and
   `--python-linker-flags` if needed. The latter must include the temporary
   library directory, `-lpython3.13 -ldl -lm`. Follow Debian's `debian/rules`:
   `OVERRIDE_CFLAGS` contains `dpkg-buildflags --get CFLAGS` plus
   `-DSIMDE_ENABLE_OPENMP -fopenmp-simd -O3`. Keep stack protection, fortify,
   RELRO/NOW and the non-executable stack. Do not hide compiler warnings.
   This laptop build uses upstream's native CPU optimization; do not deploy
   its binary to a different CPU without rebuilding.
4. With Go 1.24.4, `GOTOOLCHAIN=local` and GOPATH/GOMODCACHE/GOCACHE confined
   to temporary build directories, run `go mod download` and `go mod verify`.
   Run `kitty/launcher/kitty +launch gen/go_code.py`, then
   `go build -p 4 -trimpath -ldflags='-s -w' -o kitty/launcher/kitten ./tools/cmd`.
5. Run `test_backport.py` via the candidate's `+runpy`/`runpy.run_path` from
   the source directory. Run upstream unittest modules `kitty_tests.parser`,
   `screen`, `keys`, `multicell`, `mouse`, `shm` via the same launcher.
   Shared-memory tests need a real user session, not a restricted fake /dev/shm.
   Run `go test -p 4 ./tools/utils/secrets ./kittens/ssh`.
6. Run `python3 repack.py ORIGINAL_DEB BUILT_SOURCE NEW_OUTPUT_DEB` with
   absolute paths. It verifies the base hash, preserves the original
   launcher/plugins and package scripts, recalculates checksums/size and
   produces root-owned package entries without requiring root to build.
7. Extract the output and run `../gui_test.py EXTRACTED/usr/bin/kitty
   NEW_PRIVATE_DIRECTORY /absolute/path/to/codex`. Validate the actual payload,
   then simulate installation with `apt-get --simulate install OUTPUT_DEB`.
   Install only after those checks pass. Do not delete a separate runtime while
   a running terminal still uses it. Test the installed path again.

The module manifest is included under `/usr/share/doc/kitty/skynet-go.*.gz`;
the original binary's Built-Using field is removed because its Go dependency
versions do not describe this locally rebuilt helper. No generated binaries
or build downloads belong in this repository.

## Validation, 2026-11-11

- 10 focused regression tests and 58 upstream tests passed. Upstream color
  tests were updated with its new encoded response contract, not skipped.
- Go modules verified; SSH tests passed (the secrets package has no upstream
  tests of its own).
- Private authenticated Xephyr: eleven real input/protocol checks passed;
  fresh unauthenticated Codex 0.167.1 startup/exit produced empty Kitty stderr.
  No prompt submitted, no model request, no live session input.
- Package simulation upgrades only Kitty; version comparisons prove that
  the next stable security revision outranks this local revision.
- X11 is tested; no real Wayland session or authenticated SSH server tested.

Rollback uses a trusted distribution Kitty package through APT/dpkg; the
terminal remains package-owned. An older explicit version may require APT's
normal downgrade confirmation. Review security status before downgrading.
