#!/usr/bin/env python3
"""Check the exported tree for forbidden artifacts, known secret patterns and hashes."""
import argparse
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', '.build', '.downloads', '__pycache__'}
FORBIDDEN = {'.pem', '.key', '.p12', '.pfx', '.der', '.deb', '.ko', '.o', '.pyc'}
PATTERNS = [
    re.compile(rb'-----BEGIN(?: [A-Z]+)* PRIVATE KEY-----'),
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{50,}'),
    re.compile(rb'AKIA[A-Z0-9]{16}'),
    re.compile(rb'https?://[^\s/@:]+:[^\s/@]+@'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-checksums', action='store_true')
    args = parser.parse_args()
    files, errors = [], []
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if any(part in SKIP for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append(f'Symlink: {relative}')
            continue
        if not path.is_file() or relative.as_posix() == 'SHA256SUMS':
            continue
        data = path.read_bytes()
        if path.suffix in FORBIDDEN or data.startswith(b'\x7fELF'):
            errors.append(f'Forbidden artifact: {relative}')
        if any(pattern.search(data) for pattern in PATTERNS):
            # Do not disclose the matching value in logs.
            errors.append(f'Possible secret: {relative}')
        files.append((relative.as_posix(), hashlib.sha256(data).hexdigest()))
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    actual = ''.join(f'{digest}  {name}\n' for name, digest in files)
    manifest = ROOT / 'SHA256SUMS'
    if args.write_checksums:
        manifest.write_text(actual)
    elif not manifest.exists() or manifest.read_text() != actual:
        print('Checksum manifest missing or tree changed.', file=sys.stderr)
        return 1
    print(f'OK: {len(files)} files; no known secret pattern or forbidden artifact; SHA256SUMS matches.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
