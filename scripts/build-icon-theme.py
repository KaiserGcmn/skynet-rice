#!/usr/bin/env python3
"""Build a user-level copy of an icon theme recoloured for the black and red desktop.

Breeze paints folders, places, apps and status icons with a wide palette: the
blue accent #3daee9, other blues, green, orange, yellow, purple and soft beige
or slate tints. This writes a small theme that overrides only the icons using
such colours and inherits everything else from the source theme:

* the blue accent becomes --color exactly;
* every other saturated colour moves to the same red, keeping its relative
  lightness so multi-tone icons stay readable;
* soft tints (beige, slate) become neutral steel grey;
* greys, white and black are left alone.

Nothing below /usr/share/icons is modified.

    python3 scripts/build-icon-theme.py [--color #b02a30]
"""
import argparse
import colorsys
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ACCENT = '3daee9'
HEX_COLOR = re.compile(r'#[0-9a-fA-F]{6}')
SVG_COLOR = re.compile(r'#([0-9a-fA-F]{6})(?![0-9A-Za-z_-])')
NEUTRAL_SATURATION = 0.10   # below this a colour is a grey and stays as it is
MUTED_SATURATION = 0.30     # below this a tint (beige, slate) becomes steel grey
EDGE_LIGHTNESS = (0.06, 0.94)  # near black or white: saturation is meaningless
STEEL_HUE, STEEL_SATURATION = 210 / 360, 0.08
RED_HUE, RED_SATURATION_MAX = 357 / 360, 0.62
DEFAULT_SOURCE = Path('/usr/share/icons/breeze-dark')
DEFAULT_TARGET = Path.home() / '.local/share/icons/breeze-dark-red'
DEFAULT_COLOR = '#b02a30'
MARKER = 'X-Recolored-From'
LOCALIZED = re.compile(r'^(Name|Comment)\[[^\]]*\]=')


def index_text(source, name, comment):
    """Return the source index.theme with the header rewritten for the copy."""
    lines = []
    header = True
    for line in (source / 'index.theme').read_text(encoding='utf-8').splitlines():
        if header and line.startswith('['):
            header = line == '[Icon Theme]'
        if header:
            if LOCALIZED.match(line):
                continue
            if line.startswith('Name='):
                line = 'Name=' + name
            elif line.startswith('Comment='):
                line = 'Comment=' + comment
            elif line.startswith('Inherits='):
                line = 'Inherits=' + ','.join([source.name] + line[len('Inherits='):].split(','))
        lines.append(line)
        if header and line.startswith('Inherits='):
            lines.append(f'{MARKER}={source.name}')
    return '\n'.join(lines) + '\n'


def shift_color(match, accent):
    """Map one #rrggbb match of an SVG to the red and steel palette."""
    value = match.group(1).lower()
    if value == ACCENT:
        return accent
    red, green, blue = (int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    if saturation < NEUTRAL_SATURATION or not EDGE_LIGHTNESS[0] < lightness < EDGE_LIGHTNESS[1]:
        return match.group(0)
    if saturation < MUTED_SATURATION:
        hue, saturation = STEEL_HUE, STEEL_SATURATION
    else:
        hue, saturation = RED_HUE, min(saturation, RED_SATURATION_MAX)
        lightness = 0.15 + 0.5 * lightness
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return '#%02x%02x%02x' % tuple(round(channel * 255) for channel in (red, green, blue))


def recolour(text, accent):
    return SVG_COLOR.sub(lambda match: shift_color(match, accent), text)


def recoloured_icons(source, color):
    """Yield (relative path, new text) for every SVG whose final target changes colour."""
    for root, _dirs, files in os.walk(source):
        for name in files:
            if not name.endswith('.svg'):
                continue
            path = Path(root) / name
            resolved = Path(os.path.realpath(path))
            try:
                text = resolved.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            changed = recolour(text, color)
            if changed != text:
                yield path.relative_to(source), changed


def directory_links(source):
    """Yield (relative path, target) for same-directory symlinks such as 16@2x -> 16."""
    for root, dirs, _files in os.walk(source):
        for name in dirs:
            path = Path(root) / name
            if path.is_symlink():
                target = os.readlink(path)
                if '/' not in target and target not in ('.', '..'):
                    yield path.relative_to(source), target


def build(source, target, color):
    source = Path(source)
    target = Path(target)
    if not HEX_COLOR.fullmatch(color):
        raise ValueError(f'Colour must look like #rrggbb: {color}')
    if not (source / 'index.theme').is_file():
        raise ValueError(f'Not an icon theme: {source}')
    if target.resolve() == source.resolve():
        raise ValueError('Target must differ from the source theme')
    if target.exists():
        marker = target / 'index.theme'
        if not marker.is_file() or MARKER + '=' not in marker.read_text(encoding='utf-8'):
            raise ValueError(f'Refusing to replace a directory this script did not create: {target}')

    target.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=target.name + '.new-', dir=target.parent))
    try:
        count = 0
        for relative, text in recoloured_icons(source, color):
            destination = work / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(text, encoding='utf-8')
            count += 1
        if count == 0:
            raise ValueError(f'No icon in {source} has a colour to change')
        for relative, link_target in directory_links(source):
            link = work / relative
            if (link.parent / link_target).is_dir() and not link.exists():
                link.symlink_to(link_target)
        name = 'Breeze Dark Red'
        comment = f'{source.name} recoloured to red and steel, accent {color}'
        (work / 'index.theme').write_text(index_text(source, name, comment), encoding='utf-8')
        for path in [work, *work.rglob('*')]:
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o755)
        old = None
        if target.exists():
            old = target.with_name(target.name + '.old')
            shutil.rmtree(old, ignore_errors=True)
            target.rename(old)
        work.rename(target)
        if old is not None:
            shutil.rmtree(old, ignore_errors=True)
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise
    cache = shutil.which('gtk-update-icon-cache')
    if cache:
        subprocess.run([cache, '-q', '-f', '-t', str(target)], check=False)
    return count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--target', type=Path, default=DEFAULT_TARGET)
    parser.add_argument('--color', default=DEFAULT_COLOR)
    args = parser.parse_args(argv)
    try:
        count = build(args.source, args.target, args.color)
    except ValueError as error:
        print(f'error: {error}', file=sys.stderr)
        return 1
    print(f'{count} icons recoloured to {args.color} in {args.target}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
