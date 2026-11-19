#!/usr/bin/env python3
"""Retire the one-off 6.12.115 VMD fallback after booting 6.12.116.

Explicit local maintenance, not a restore hook. Refuses unexpected boot policy.
Does not remove kernel packages or regenerate initramfs/install GRUB.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile


CURRENT = "6.12.116+deb13-amd64"
OLD = "6.12.115+deb13.1-amd64"
BACKUP = Path(f"/boot/initrd.img-{OLD}.skynet-stock")
CUSTOM = Path("/boot/grub/custom.cfg")
GRUB = Path("/boot/grub/grub.cfg")
ENV = Path("/boot/grub/grubenv")
ENTRY_ID = "skynet-vmd-stock"


def remove_entry(text):
    entries = list(re.finditer(
        r"(?m)^menuentry [^\n]*--id ['\"]?skynet-vmd-stock['\"]?\s*\{\n", text))
    if not entries:
        if ENTRY_ID in text:
            raise ValueError("Unexpected fallback syntax; manual review required")
        return text, False
    if len(entries) != 1:
        raise ValueError("Ambiguous duplicate fallback entries")
    start = entries[0].start()
    close = re.search(r"(?m)^\}[ \t]*(?:\n|$)", text[entries[0].end():])
    if close is None:
        raise ValueError("Unterminated fallback entry")
    end = entries[0].end() + close.end()
    block = text[start:end]
    if not re.search(r"(?m)^\s*linux\s+/boot/vmlinuz-" + re.escape(OLD) + r"\s", block):
        raise ValueError("Fallback points to a different kernel")
    if not re.search(r"(?m)^\s*initrd\s+" + re.escape(str(BACKUP)) + r"[ \t]*$", block):
        raise ValueError("Unexpected fallback initramfs")
    if re.search(r"(?m)^menuentry ", block[1:]):
        raise ValueError("Nested/unterminated fallback entry")
    result = text[:start] + text[end:]
    result = result.replace("# SKYNET exact-kernel VMD fallback; original kernel arguments preserved.\n", "", 1)
    return result, True


def verify_default(text):
    first = re.search(r"(?ms)^menuentry [^\n]*\n.*?^\}", text)
    if first is None:
        raise ValueError("No normal top-level boot entry")
    if not re.search(r"(?m)^\s*linux\s+/boot/vmlinuz-" + re.escape(CURRENT) + r"\s", first[0]):
        raise ValueError("The normal entry does not boot the running kernel")
    if not re.search(r"(?m)^\s*initrd\s+/boot/initrd.img-" + re.escape(CURRENT) + r"[ \t]*$", first[0]):
        raise ValueError("Unexpected normal initramfs")
    if not re.search(r'(?m)^\s*set default="0"\s*$', text):
        raise ValueError("Expected normal default entry 0")
    if not re.search(r'(?m)^\s*set timeout=3\s*$', text):
        raise ValueError("Expected existing three-second menu")
    if "source ${config_directory}/custom.cfg" not in text:
        raise ValueError("Expected runtime custom.cfg loader")
    return first[0].splitlines()[0]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def check_custom_syntax(text):
    # grub-script-check returns 1 for an empty/comment-only fragment. Removing
    # our sole entry legitimately leaves no commands and needs no replacement.
    if not any(line.strip() and not line.lstrip().startswith("#") for line in text.splitlines()):
        return
    with tempfile.TemporaryDirectory(prefix="skynet-grub-check-") as temporary:
        candidate = Path(temporary) / "custom.cfg"
        candidate.write_text(text)
        run("/usr/bin/grub-script-check", str(candidate))


def atomic(path, data, mode):
    fd, name = tempfile.mkstemp(prefix=".skynet-grub-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
            os.fchown(stream.fileno(), 0, 0)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or os.uname().release != CURRENT:
        raise SystemExit("Requires root on the validated 6.12.116 running kernel")
    for path in (CUSTOM, BACKUP, GRUB, ENV):
        if path.is_symlink():
            raise SystemExit(f"Unexpected symlink: {path}")
    grub_before = GRUB.read_bytes()
    title = verify_default(grub_before.decode())
    run("/usr/bin/grub-script-check", str(GRUB))
    custom_before = CUSTOM.read_bytes() if CUSTOM.exists() else None
    custom_mode = stat.S_IMODE(CUSTOM.stat().st_mode) if CUSTOM.exists() else 0o600
    updated, removed = remove_entry(custom_before.decode() if custom_before else "")
    # Refuse to delete an image still referenced by another GRUB fragment/script.
    for directory in (Path("/boot/grub"), Path("/etc/grub.d")):
        paths = directory.rglob("*.cfg") if directory.name == "grub" else directory.iterdir()
        for path in paths:
            if not path.is_file():
                continue
            content = updated if path == CUSTOM else path.read_text(errors="replace")
            if BACKUP.name in content:
                raise SystemExit(f"Another reference to backup remains: {path}")
    protected = [Path(f"/boot/vmlinuz-{CURRENT}"), Path(f"/boot/initrd.img-{CURRENT}"),
                 Path("/etc/default/grub.d/95-expertbook-boot.cfg"),
                 Path("/etc/default/grub.d/90-expertbook-hardening.cfg"),
                 Path("/etc/default/grub.d/99-skynet-wallpaper.cfg")]
    hashes = {str(path): digest(path) for path in protected}
    env_before = ENV.read_bytes()
    env_mode = stat.S_IMODE(ENV.stat().st_mode)
    env_values = dict(line.split("=", 1) for line in run("/usr/bin/grub-editenv", str(ENV), "list").splitlines() if "=" in line)
    clear = [key for key, value in env_values.items()
             if key == "next_entry" or (key in ("saved_entry", "prev_saved_entry") and value == ENTRY_ID)]
    backup_before = BACKUP.read_bytes() if BACKUP.exists() else None
    backup_mode = stat.S_IMODE(BACKUP.stat().st_mode) if BACKUP.exists() else 0o644
    # Validate the candidate before the first write; all writes have rollback data.
    check_custom_syntax(updated)
    try:
        if removed:
            if updated.strip():
                atomic(CUSTOM, updated.encode(), custom_mode)
            else:
                CUSTOM.unlink()
        if clear:
            run("/usr/bin/grub-editenv", str(ENV), "unset", *clear)
        run("/usr/bin/grub-script-check", str(GRUB))
        if GRUB.read_bytes() != grub_before:
            raise RuntimeError("Unexpected generated GRUB configuration change")
        if CUSTOM.exists():
            check_custom_syntax(CUSTOM.read_text())
        if any(digest(Path(path)) != value for path, value in hashes.items()):
            raise RuntimeError("Protected boot files changed")
        BACKUP.unlink(missing_ok=True)
        result = {"default_kernel": CURRENT, "normal_entry": title, "timeout_seconds": 3,
                  "removed_entry": ENTRY_ID if removed else None,
                  "removed_backup": str(BACKUP) if backup_before is not None else None,
                  "freed_bytes": len(backup_before or b""), "grubenv_cleared": clear,
                  "grub_cfg_unchanged": True, "protected_sha256": hashes,
                  "kernel_packages_removed": False, "reboot_performed": False}
        args.report.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
    except BaseException:
        if backup_before is not None:
            atomic(BACKUP, backup_before, backup_mode)
        if custom_before is not None:
            atomic(CUSTOM, custom_before, custom_mode)
        else:
            CUSTOM.unlink(missing_ok=True)
        if ENV.read_bytes() != env_before:
            atomic(ENV, env_before, env_mode)
        raise


if __name__ == "__main__":
    main()
