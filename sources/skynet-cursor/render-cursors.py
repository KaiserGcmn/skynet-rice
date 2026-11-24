#!/usr/bin/python3
"""Render the SKYNET HUD Xcursor theme from vector shapes.

Every cursor is drawn with Cairo in a 32-unit design grid and rasterized at
each Xcursor size, so 24, 32, 48 and 64 px all stay sharp. Palette follows the
rice: near-black steel body, red #ff4050 rim, a dark outer outline and a soft
shadow so the pointer stays visible on both the black desktop and light pages.

usage: render-cursors.py OUTPUT_THEME_DIR [--preview PNG]
"""
import argparse
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

import cairo

SIZES = (24, 32, 48, 64)
RED = (1.0, 0.25, 0.31)          # #ff4050
RED_DEEP = (0.64, 0.10, 0.17)
STEEL = (0.62, 0.67, 0.74)
INK = (0.02, 0.024, 0.03)
SPIN_FRAMES = 24
SPIN_DELAY = 40                  # ms: one turn per ~0.96 s

# Arrow outline (tip at 2,2) shared by pointer variants.
ARROW = ((2, 2), (2, 24.5), (7.6, 19.4), (11.4, 28.4), (15.3, 26.7),
         (11.6, 17.9), (19.2, 17.9))


def polygon(cr, points):
    cr.move_to(*points[0])
    for point in points[1:]:
        cr.line_to(*point)
    cr.close_path()


def shadow(cr, path, width=2.6, fill=True):
    """Soft offset shadow: a few widening translucent strokes. Solid shapes
    also fill; rings and lines must not, or light pages show a grey disc."""
    cr.save()
    cr.translate(0.7, 1.3)
    for grow, alpha in ((3.2, 0.10), (2.0, 0.16), (0.8, 0.24)):
        path(cr)
        cr.set_source_rgba(0, 0, 0, alpha)
        cr.set_line_width(width + grow)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        if fill:
            cr.stroke_preserve()
            cr.fill()
        else:
            cr.stroke()
    cr.restore()


def steel_fill(cr, x0, y0, x1, y1):
    gradient = cairo.LinearGradient(x0, y0, x1, y1)
    gradient.add_color_stop_rgb(0, 0.13, 0.145, 0.18)
    gradient.add_color_stop_rgb(1, 0.035, 0.04, 0.05)
    return gradient


def red_fill(cr, x0, y0, x1, y1):
    gradient = cairo.LinearGradient(x0, y0, x1, y1)
    gradient.add_color_stop_rgb(0, *RED)
    gradient.add_color_stop_rgb(1, *RED_DEEP)
    return gradient


def body(cr, path, fill, rim=RED, rim_width=1.15):
    """Dark outline, filled body, then an inner red rim."""
    cr.set_line_join(cairo.LINE_JOIN_MITER)
    # Sharp corners (the arrow tip) bevel instead of growing a long miter
    # spike, so the visible tip stays where the hotspot is.
    cr.set_miter_limit(2)
    path(cr)
    cr.set_source_rgb(*INK)
    cr.set_line_width(rim_width + 1.5)
    cr.stroke_preserve()
    cr.set_source(fill)
    cr.fill_preserve()
    cr.set_source_rgb(*rim)
    cr.set_line_width(rim_width)
    cr.stroke()


def line(cr, segments, width=1.5, color=RED, cap=cairo.LINE_CAP_SQUARE):
    """Stroke segments twice: dark outline first, then colour."""
    for stroke_width, rgb in ((width + 1.7, INK), (width, color)):
        cr.set_line_cap(cap)
        cr.set_line_width(stroke_width)
        cr.set_source_rgb(*rgb)
        for (x0, y0), (x1, y1) in segments:
            cr.move_to(x0, y0)
            cr.line_to(x1, y1)
        cr.stroke()


def arrow(cr, filled_red=False):
    path = lambda c: polygon(c, ARROW)
    shadow(cr, path)
    if filled_red:
        body(cr, path, red_fill(cr, 2, 2, 14, 26), rim=(1.0, 0.55, 0.6), rim_width=0.9)
    else:
        body(cr, path, steel_fill(cr, 2, 2, 14, 26))
        # Inner facet: a thin steel highlight along the leading edge and a
        # short red core near the tip give the flat shape some depth.
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(*STEEL, 0.55)
        cr.set_line_width(0.75)
        cr.move_to(3.9, 6.6)
        cr.line_to(3.9, 19.6)
        cr.stroke()
        cr.set_source_rgb(*RED)
        polygon(cr, ((3.9, 5.2), (3.9, 11.5), (8.6, 10.2)))
        cr.fill()


def badge(cr, x, y, radius=5.2):
    shadow(cr, lambda c: c.arc(x, y, radius, 0, 2 * math.pi), width=1.4)
    cr.arc(x, y, radius, 0, 2 * math.pi)
    cr.set_source_rgb(*INK)
    cr.fill_preserve()
    cr.set_source_rgb(*RED)
    cr.set_line_width(1.1)
    cr.stroke()


def spinner(cr, x, y, radius, phase, width=2.2, segments=12):
    """Segmented ring; a bright head travels round with a fading tail."""
    gap = 0.16
    span = 2 * math.pi / segments
    cr.set_line_cap(cairo.LINE_CAP_BUTT)
    cr.set_line_width(width + 1.6)
    cr.set_source_rgb(*INK)
    cr.arc(x, y, radius, 0, 2 * math.pi)
    cr.stroke()
    for index in range(segments):
        start = -math.pi / 2 + index * span
        # Distance behind the head, 0..1 around the ring.
        behind = (phase - index / segments) % 1.0
        level = max(0.0, 1.0 - behind * 1.35)
        red = tuple(0.16 + (channel - 0.16) * level for channel in RED)
        cr.set_source_rgb(*red)
        cr.set_line_width(width)
        cr.arc(x, y, radius, start + gap / 2, start + span - gap / 2)
        cr.stroke()


def cursor_default(cr, frame):
    arrow(cr)


def cursor_link(cr, frame):
    arrow(cr, filled_red=True)


def cursor_help(cr, frame):
    arrow(cr)
    badge(cr, 23.5, 23.5)
    cr.set_source_rgb(*RED)
    cr.select_font_face('JetBrains Mono', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(8.4)
    extents = cr.text_extents('?')
    cr.move_to(23.5 - extents.width / 2 - extents.x_bearing,
               23.5 - extents.height / 2 - extents.y_bearing)
    cr.show_text('?')


def cursor_progress(cr, frame):
    arrow(cr)
    badge(cr, 23.5, 23.5, radius=6.4)
    spinner(cr, 23.5, 23.5, 3.9, frame / SPIN_FRAMES, width=1.5, segments=8)


def cursor_wait(cr, frame):
    shadow(cr, lambda c: c.arc(16, 16, 10.5, 0, 2 * math.pi), width=3.2, fill=False)
    spinner(cr, 16, 16, 10.5, frame / SPIN_FRAMES, width=2.6)
    # Steel inner ring and a steady red core: the motion stays in the ring.
    cr.set_line_width(0.8)
    cr.set_source_rgba(*STEEL, 0.6)
    cr.arc(16, 16, 6.4, 0, 2 * math.pi)
    cr.stroke()
    cr.arc(16, 16, 2.1, 0, 2 * math.pi)
    cr.set_source_rgb(*INK)
    cr.set_line_width(1.6)
    cr.stroke_preserve()
    cr.set_source_rgb(*RED)
    cr.fill()


def cursor_text(cr, frame):
    shadow(cr, lambda c: (c.move_to(16, 6), c.line_to(16, 26)), width=2, fill=False)
    line(cr, [((16, 7.2), (16, 24.8))], width=1.5)
    line(cr, [((12.6, 5.6), (14.8, 7.2)), ((14.8, 7.2), (17.2, 7.2)), ((17.2, 7.2), (19.4, 5.6)),
              ((12.6, 26.4), (14.8, 24.8)), ((14.8, 24.8), (17.2, 24.8)), ((17.2, 24.8), (19.4, 26.4))],
         width=1.3, cap=cairo.LINE_CAP_ROUND)


def cursor_crosshair(cr, frame):
    arms = [((16, 3.5), (16, 12.5)), ((16, 19.5), (16, 28.5)),
            ((3.5, 16), (12.5, 16)), ((19.5, 16), (28.5, 16))]
    shadow(cr, lambda c: [(c.move_to(*a), c.line_to(*b)) for a, b in arms], width=1.6, fill=False)
    line(cr, arms, width=1.3)
    brackets = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            corner = (16 + sx * 7, 16 + sy * 7)
            brackets += [(corner, (corner[0] - sx * 3, corner[1])),
                         (corner, (corner[0], corner[1] - sy * 3))]
    line(cr, brackets, width=0.9, color=STEEL)
    cr.arc(16, 16, 1.4, 0, 2 * math.pi)
    cr.set_source_rgb(*RED)
    cr.fill()


def double_arrow(cr, angle, four_way=False):
    cr.save()
    cr.translate(16, 16)
    cr.rotate(angle)
    directions = (0, math.pi / 2, math.pi, 3 * math.pi / 2) if four_way else (0, math.pi)
    reach = 13.2

    def head(c, direction):
        c.save()
        c.rotate(direction)
        polygon(c, ((reach, 0), (reach - 5.4, -4.6), (reach - 4.1, 0), (reach - 5.4, 4.6)))
        c.restore()

    def outline(c):
        for direction in directions:
            c.move_to(0, 0)
            c.line_to(math.cos(direction) * reach, math.sin(direction) * reach)

    shadow(cr, outline, width=3.0, fill=False)
    for direction in directions:
        x, y = math.cos(direction) * (reach - 4.4), math.sin(direction) * (reach - 4.4)
        line(cr, [((math.cos(direction) * (1.8 if four_way else 0),
                    math.sin(direction) * (1.8 if four_way else 0)), (x, y))], width=1.6,
             cap=cairo.LINE_CAP_BUTT)
    for direction in directions:
        body(cr, lambda c, d=direction: head(c, d), red_fill(cr, -reach, 0, reach, 0),
             rim=RED, rim_width=0.6)
    if four_way:
        polygon(cr, ((0, -2.6), (2.6, 0), (0, 2.6), (-2.6, 0)))
        cr.set_source_rgb(*INK)
        cr.set_line_width(1.4)
        cr.stroke_preserve()
        cr.set_source_rgb(*STEEL)
        cr.fill()
    cr.restore()


def cursor_move(cr, frame):
    double_arrow(cr, 0, four_way=True)


def cursor_ew(cr, frame):
    double_arrow(cr, 0)


def cursor_ns(cr, frame):
    double_arrow(cr, math.pi / 2)


def cursor_nwse(cr, frame):
    double_arrow(cr, math.pi / 4)


def cursor_nesw(cr, frame):
    double_arrow(cr, -math.pi / 4)


def cursor_forbidden(cr, frame):
    ring = lambda c: c.arc(16, 16, 9.5, 0, 2 * math.pi)
    shadow(cr, ring, width=2.4, fill=False)
    for width, rgb in ((4.1, INK), (2.3, RED)):
        ring(cr)
        cr.set_line_width(width)
        cr.set_source_rgb(*rgb)
        cr.stroke()
    slash = 9.5 * math.cos(math.pi / 4)
    line(cr, [((16 - slash, 16 - slash), (16 + slash, 16 + slash))], width=2.3,
         cap=cairo.LINE_CAP_BUTT)


# file name -> (painter, hotspot in design units, animated)
CURSORS = {
    'left_ptr': (cursor_default, (2, 2), False),
    'hand2': (cursor_link, (2, 2), False),
    'question_arrow': (cursor_help, (2, 2), False),
    'left_ptr_watch': (cursor_progress, (2, 2), True),
    'watch': (cursor_wait, (16, 16), True),
    'xterm': (cursor_text, (16, 16), False),
    'crosshair': (cursor_crosshair, (16, 16), False),
    'fleur': (cursor_move, (16, 16), False),
    'size_hor': (cursor_ew, (16, 16), False),
    'size_ver': (cursor_ns, (16, 16), False),
    'size_fdiag': (cursor_nwse, (16, 16), False),
    'size_bdiag': (cursor_nesw, (16, 16), False),
    'crossed_circle': (cursor_forbidden, (16, 16), False),
}


# Standard X11/CSS/freedesktop names -> rendered file (resolved, no chains).
ALIASES = {
    '00000000000000020006000e7e9ffc3f': 'left_ptr_watch',
    '00008160000006810000408080010102': 'size_ver',
    '03b6e0fcb3499374a867c041f52298f0': 'crossed_circle',
    '08e8e1c95fe2fc01f976f1e063a24ccd': 'left_ptr_watch',
    '3ecb610c1bf2410f44200f48c40d3599': 'left_ptr_watch',
    '5c6cd98b3f3ebcb1f9c7f1c204630408': 'question_arrow',
    '9d800788f1b08800ae810202380a0822': 'hand2',
    'all-scroll': 'fleur',
    'arrow': 'left_ptr',
    'bottom_left_corner': 'size_bdiag',
    'bottom_right_corner': 'size_fdiag',
    'bottom_side': 'size_ver',
    'closedhand': 'fleur',
    'col-resize': 'size_hor',
    'context-menu': 'left_ptr',
    'cross': 'crosshair',
    'd9ce0ab605698f320427677b458ad60b': 'question_arrow',
    'default': 'left_ptr',
    'diamond_cross': 'crosshair',
    'e29285e634086352946a0e7090d73106': 'hand2',
    'e-resize': 'size_hor',
    'ew-resize': 'size_hor',
    'forbidden': 'crossed_circle',
    'grab': 'fleur',
    'grabbing': 'fleur',
    'half-busy': 'left_ptr_watch',
    'hand1': 'hand2',
    'h_double_arrow': 'size_hor',
    'help': 'question_arrow',
    'ibeam': 'xterm',
    'left_ptr_help': 'question_arrow',
    'left_side': 'size_hor',
    'link': 'hand2',
    'move': 'fleur',
    'ne-resize': 'size_bdiag',
    'nesw-resize': 'size_bdiag',
    'no-drop': 'crossed_circle',
    'not-allowed': 'crossed_circle',
    'n-resize': 'size_ver',
    'ns-resize': 'size_ver',
    'nw-resize': 'size_fdiag',
    'nwse-resize': 'size_fdiag',
    'openhand': 'fleur',
    'pointer': 'hand2',
    'pointing_hand': 'hand2',
    'progress': 'left_ptr_watch',
    'right_ptr': 'left_ptr',
    'right_side': 'size_hor',
    'row-resize': 'size_ver',
    'sb_h_double_arrow': 'size_hor',
    'sb_v_double_arrow': 'size_ver',
    'se-resize': 'size_fdiag',
    'size_all': 'fleur',
    'split_h': 'size_hor',
    'split_v': 'size_ver',
    's-resize': 'size_ver',
    'sw-resize': 'size_bdiag',
    'tcross': 'crosshair',
    'text': 'xterm',
    'top_left_arrow': 'left_ptr',
    'top_left_corner': 'size_fdiag',
    'top_right_corner': 'size_bdiag',
    'top_side': 'size_ver',
    'v_double_arrow': 'size_ver',
    'wait': 'watch',
    'whats_this': 'question_arrow',
    'w-resize': 'size_hor',
}

THEME_INDEX = """[Icon Theme]
Name=Skynet
Comment=SKYNET HUD cursors: vector-rendered at 24/32/48/64 px (skynet-rice sources/skynet-cursor)
Inherits=breeze_cursors
Example=left_ptr
"""


def render(painter, size, frame=0):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    cr = cairo.Context(surface)
    cr.scale(size / 32, size / 32)
    painter(cr, frame)
    surface.flush()
    return surface


def build(output, work):
    cursors = output / 'cursors'
    cursors.mkdir(parents=True, exist_ok=True)
    for name, (painter, (hx, hy), animated) in CURSORS.items():
        lines = []
        for size in SIZES:
            for frame in range(SPIN_FRAMES if animated else 1):
                png = work / f'{name}-{size}-{frame:02d}.png'
                render(painter, size, frame).write_to_png(str(png))
                hot_x = min(size - 1, round(hx * size / 32))
                hot_y = min(size - 1, round(hy * size / 32))
                delay = f' {SPIN_DELAY}' if animated else ''
                lines.append(f'{size} {hot_x} {hot_y} {png.name}{delay}')
        config = work / f'{name}.cfg'
        config.write_text('\n'.join(lines) + '\n')
        subprocess.run(['xcursorgen', '-p', str(work), str(config), str(cursors / name)],
                       check=True)
    for alias, target in ALIASES.items():
        link = cursors / alias
        if link.is_symlink() or not link.exists():
            link.unlink(missing_ok=True)
            link.symlink_to(target)
    (output / 'index.theme').write_text(THEME_INDEX)


def preview(path, size=48):
    names = list(CURSORS)
    pad = 16
    cell = size + pad
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, cell * len(names) + pad, cell * 2 + pad)
    cr = cairo.Context(surface)
    for row, background in enumerate(((0.0, 0.0, 0.0), (0.93, 0.93, 0.94))):
        cr.set_source_rgb(*background)
        cr.rectangle(0, row * cell + pad / 2, surface.get_width(), cell)
        cr.fill()
        for index, name in enumerate(names):
            cr.set_source_surface(render(CURSORS[name][0], size, 5), pad + index * cell,
                                  pad + row * cell)
            cr.paint()
    surface.write_to_png(str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('output', type=Path)
    parser.add_argument('--preview', type=Path)
    parser.add_argument('--preview-size', type=int, default=48)
    args = parser.parse_args()
    if args.preview:
        preview(args.preview, args.preview_size)
    with tempfile.TemporaryDirectory(prefix='skynet-cursor-') as work:
        build(args.output, Path(work))


if __name__ == '__main__':
    main()
