#!/usr/bin/python3 -I
"""Prepare a flat, terminal-style lock background outside the startup path."""
import sys


def main():
    import gi
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Pango, PangoCairo
    import cairo

    width, height = int(sys.argv[1]), int(sys.argv[2])
    if not (1 <= width <= 8192 and 1 <= height <= 8192
            and width * height <= 16777216):
        raise ValueError('Unsupported image size')

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    ctx = cairo.Context(surface)

    def color(value):
        ctx.set_source_rgb(*(int(value[i:i+2], 16) / 255 for i in (1, 3, 5)))

    def text(value, cx, cy, foreground, font='JetBrains Mono 12', backing=False):
        layout = PangoCairo.create_layout(ctx)
        layout.set_font_description(Pango.FontDescription(font))
        layout.set_text(value, -1)
        tw, th = layout.get_pixel_size()
        left, top = round(cx - tw / 2), round(cy - th / 2)
        if backing:
            color('#000000')
            ctx.rectangle(left - 10, top, tw + 20, th)
            ctx.fill()
        color(foreground)
        ctx.move_to(left, top)
        PangoCairo.show_layout(ctx, layout)

    color('#000000')
    ctx.paint()
    cx, cy = width / 2, height / 2
    panel_width, panel_height = min(720, width - 64), min(340, height - 140)
    if panel_width >= 360 and panel_height >= 300:
        left = round(cx - panel_width / 2) + .5
        top = round(cy - panel_height / 2) + .5
        color('#a4a4a4')
        ctx.set_line_width(1)
        ctx.rectangle(left, top, panel_width, panel_height)
        ctx.stroke()
        # Labels remain clear of the independent, live authentication window.
        text('Session locked', cx, top, '#d6d6d6', backing=True)
        text('Enter your password · Press Enter to unlock', cx, top + panel_height - 28,
             '#999999', font='JetBrains Mono 11')
    surface.write_to_png(sys.argv[3])


if __name__ == '__main__':
    main()
