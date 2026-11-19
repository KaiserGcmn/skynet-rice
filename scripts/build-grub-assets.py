#!/usr/bin/env python3
"""Render geometric GRUB panel tiles and build the menu font locally."""
import argparse
from pathlib import Path
import struct
import subprocess
import zlib


def chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload
            + struct.pack('>I', zlib.crc32(kind + payload)))


def tile(path, part, selected):
    rows = []
    for y in range(8):
        row = bytearray([0])
        for x in range(8):
            if selected:
                rgb = (255, 57, 75) if 'w' in part and x < 3 else (134, 20, 37)
            else:
                border = (('w' in part and x < 2) or ('e' in part and x >= 6)
                          or ('n' in part and y < 2) or ('s' in part and y >= 6))
                rgb = (112, 28, 43) if border else (8, 9, 11)
            row.extend(rgb)
        rows.append(bytes(row))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'
                     + chunk(b'IHDR', struct.pack('>IIBBBBB', 8, 8, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(b''.join(rows)))
                     + chunk(b'IEND', b''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for prefix, selected in [('panel', False), ('select', True)]:
        for part in ('c', 'n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'):
            tile(args.output / f'{prefix}_{part}.png', part, selected)
    subprocess.run([
        'grub-mkfont', '-s', '28', '-o', str(args.output / 'dejavu-mono-bold-28.pf2'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
    ], check=True)


if __name__ == '__main__':
    main()
