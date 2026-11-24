#!/usr/bin/env python3
"""Overlay the tested compatibility backport on the verified Debian package.

Does not download, install or modify the running terminal. No root required.
"""
import argparse
import gzip
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

BASE_VERSION = "0.41.1-2+deb13u2"
VERSION = BASE_VERSION + "+skynet1"
BASE_SHA256 = "27a43046a7782bf803c51afd49bf257edf24d5563a02e723519d2ecbb5228576"
PYTHON_FILES = ("child.py", "window.py", "shm.py", "program_status.py")


def run(*args):
    subprocess.run(args, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_deb", type=Path)
    parser.add_argument("built_source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.built_source.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("Refusing to overwrite output")
    if hashlib.sha256(args.base_deb.read_bytes()).hexdigest() != BASE_SHA256:
        raise SystemExit("Original Debian package checksum mismatch")
    for old, relation, new in ((BASE_VERSION, "lt", VERSION),
                              (VERSION, "lt", "0.41.1-2+deb13u3"),
                              (VERSION, "lt", "0.41.1-3")):
        run("dpkg", "--compare-versions", old, relation, new)
    with tempfile.TemporaryDirectory(prefix="kitty-repack-", dir=output.parent) as temp:
        root = Path(temp) / "root"
        run("dpkg-deb", "--raw-extract", str(args.base_deb.resolve()), str(root))
        lib = root / "usr/lib/kitty/kitty"
        for name in PYTHON_FILES:
            shutil.copyfile(source / "kitty" / name, lib / name)
            (lib / name).chmod(0o644)
        shutil.copyfile(source / "kitty/fast_data_types.so", lib / "fast_data_types.so")
        (lib / "fast_data_types.so").chmod(0o644)
        run("strip", "--strip-unneeded", str(lib / "fast_data_types.so"))
        shutil.copyfile(source / "kitty/launcher/kitten", root / "usr/bin/kitten")
        (root / "usr/bin/kitten").chmod(0o755)
        # Keep Debian's original launcher, GLFW plugins, rsync module and scripts.
        # The source-tree launcher has different library paths and must not be installed.
        doc = root / "usr/share/doc/kitty"
        note = (
            f"Local SKYNET compatibility build: {VERSION}\n"
            "Based on authenticated Debian trixie-security source and binary.\n"
            "Original /usr/bin/kitty launcher and Debian package scripts retained.\n"
            "Backports: OSC 7501; DEC 1007; idempotent DEC 2026; keyboard reset; SysVinit.\n"
            "Security backports: askpass owner/mode/handle checks and prompt sanitization;\n"
            "decimal echo/canary; encoded unknown color responses; multicell bounds.\n"
            "Source patch, build instructions and tests: skynet-rice/sources/kitty-compat/debian.\n"
            "This is a local build, not a Debian-maintained binary.\n"
            "No APT hold or pin. Official higher versions replace it, including local patches.\n"
            "Go module source versions/checksums accompany this file.\n"
        )
        (doc / "README.skynet").write_text(note)
        for name in ("go.mod", "go.sum"):
            (doc / ("skynet-" + name + ".gz")).write_bytes(
                gzip.compress((source / name).read_bytes(), mtime=0))
        control = root / "DEBIAN/control"
        lines = control.read_text().splitlines()
        lines = [line for line in lines if not line.startswith(("Built-Using:", "Installed-Size:"))]
        for i, line in enumerate(lines):
            if line.startswith("Version:"):
                lines[i] = "Version: " + VERSION
            elif line.startswith("Maintainer:"):
                lines[i] = "Maintainer: Local SKYNET build <root@localhost>"
        size = sum(f.stat().st_size for f in (root / "usr").rglob("*")
                   if f.is_file() and not f.is_symlink())
        lines += [f"Installed-Size: {(size + 1023) // 1024}"]
        control.write_text("\n".join(lines) + "\n")
        files = sorted(f for f in root.rglob("*") if f.is_file() and not f.is_symlink()
                       and f.relative_to(root).parts[0] != "DEBIAN")
        (root / "DEBIAN/md5sums").write_text("".join(
            f"{hashlib.md5(f.read_bytes()).hexdigest()}  {f.relative_to(root)}\n" for f in files))
        run("dpkg-deb", "--root-owner-group", "--build", str(root), str(output))
    print(hashlib.sha256(output.read_bytes()).hexdigest(), output.name)


if __name__ == "__main__":
    main()
