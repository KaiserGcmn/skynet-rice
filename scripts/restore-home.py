#!/usr/bin/env python3
"""Preview or restore portable user configuration; never install system services."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]


def check_path(path):
    for node in (path, *path.parents):
        if node.is_symlink():
            raise ValueError(f'Symlink destination refused: {node}')


def plan(home):
    check_path(home)
    if not home.is_dir():
        raise ValueError('Destination home must already exist.')
    if home.stat().st_uid != os.getuid():
        raise ValueError('Destination home must belong to the current user.')
    entries = []
    for source in sorted((ROOT / 'home').rglob('*')):
        if source.is_symlink():
            raise ValueError(f'Symlink source refused: {source}')
        if not source.is_file():
            continue
        relative = source.relative_to(ROOT / 'home')
        destination = home / relative
        check_path(destination)
        if destination.exists() and not destination.is_file():
            raise ValueError(f'Destination is not a regular file: {destination}')
        for parent in destination.parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError(f'Parent is not a directory: {parent}')
        data = source.read_bytes()
        # This placeholder occurs inside a JSON string, so escape the new path.
        if str(relative) == '.config/fastfetch/config.jsonc':
            data = data.replace(b'@@HOME@@', json.dumps(str(home))[1:-1].encode())
        if destination.exists() and destination.read_bytes() == data:
            continue
        entries.append((source, destination, data))
    check_path(home / '.local/state/skynet-rice/backups')
    return entries


def restore(home, apply=False):
    entries = plan(home)
    for _, destination, _ in entries:
        print(('REPLACE ' if destination.exists() else 'CREATE  ') + str(destination.relative_to(home)))
    if not apply:
        print(f'Preview: {len(entries)} files. Use --apply to write with backups.')
        return None
    if not entries:
        print('Already up to date.')
        return None
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = home / '.local/state/skynet-rice/backups' / (stamp + '-' + uuid.uuid4().hex[:8])
    backup.mkdir(parents=True, mode=0o700)
    manifest = []
    # Back up the complete plan before replacing any existing configuration.
    for source, destination, _ in entries:
        relative = destination.relative_to(home)
        existed = destination.exists()
        if existed:
            saved = backup / 'files' / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, saved)
        manifest.append({'path': str(relative), 'existed': existed})
    (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    installed = []
    try:
        for source, destination, data in entries:
            check_path(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            fd, temp = tempfile.mkstemp(prefix='.skynet-rice-', dir=destination.parent)
            try:
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(data)
                # Preserve stricter existing permissions; new files follow umask.
                if destination.exists():
                    os.chmod(temp, destination.stat().st_mode & 0o777)
                else:
                    mask = os.umask(0)
                    os.umask(mask)
                    os.chmod(temp, (source.stat().st_mode & 0o777) & ~mask)
                os.replace(temp, destination)
                installed.append(destination)
            finally:
                Path(temp).unlink(missing_ok=True)
    except Exception:
        for destination in reversed(installed):
            saved = backup / 'files' / destination.relative_to(home)
            if saved.exists():
                shutil.copy2(saved, destination)
            else:
                destination.unlink()
        raise
    print(f'Restored {len(entries)} files. Previous files: {backup}')
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as the desktop user, without sudo.')
    try:
        restore(args.home.absolute(), args.apply)
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
