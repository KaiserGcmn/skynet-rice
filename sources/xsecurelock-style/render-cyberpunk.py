#!/usr/bin/python3 -I
"""Add a static cyberpunk HUD around the unchanged SKYNET lock artwork.

Usage: render-cyberpunk.py BASE.png OUT.png
       render-cyberpunk.py --blank OUT.png

BASE is the original 1920x1200 SKYNET lock background. With --blank the
frames are drawn on black instead: the GTK login screen draws its own
emblem, login box and power buttons and uses that image (greeter HUD). Its pixels are copied
unchanged; the HUD is drawn only in the empty side, top and bottom margins.
The rotating emblem, wordmark, captions, central frame, live controls,
battery label and power buttons keep their own areas (see PROTECTED).

Only the static frame of each widget is drawn here. The moving parts (CPU
core tiles and pin pulses, live readouts, memory trace, load bars, active
subsystem rows, battery and energy-flow rings with power readouts, network traffic graph and rates, thermometers, ticker text, status dot and
edge scanners) are drawn live by saver-lock-style from cyber-hud.h, whose
HUD_* geometry this script reads.
"""
import math
from pathlib import Path
import re
import sys

WIDTH, HEIGHT = 1920, 1200

# Areas painted live by saver-lock-style/auth/power UI, or holding SKYNET art.
PROTECTED = (
    (700, 60, 1220, 450),     # rotating emblem, S K Y N E T, taglines
    (596, 426, 1324, 774),    # central frame and authentication window
    (660, 776, 1260, 840),    # CYBERDYNE SYSTEMS CORPORATION caption
    (500, 900, 1420, 1100),   # live audio/microphone/display readout
    (1456, 12, 1906, 62),     # battery label
    (1392, 1108, 1898, 1180), # Reboot / Shut down buttons
)

RED = '#ff4050'
RED_MID = '#c42a3e'
RED_DIM = '#5a1520'
RED_FAINT = '#2a0a10'
GRID = '#170609'
TEXT = '#9c6b76'
TEXT_DIM = '#6e4750'
TEXT_HI = '#e6dbde'
STEEL = '#8a9099'
STEEL_DIM = '#4a5058'


def hud_geometry(header=Path(__file__).resolve().with_name('cyber-hud.h')):
    """HUD_* integer constants shared with the animated C layer."""
    values = dict(re.findall(r'(?m)^#define HUD_(\w+) (-?\d+)$', header.read_text()))
    return {key: int(value) for key, value in values.items()}


def main():
    import gi
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Pango, PangoCairo
    import cairo

    hud = hud_geometry()
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)
    if sys.argv[1] == '--blank':
        ctx.set_source_rgb(0, 0, 0)
    else:
        base = cairo.ImageSurface.create_from_png(sys.argv[1])
        if (base.get_width(), base.get_height()) != (WIDTH, HEIGHT):
            raise SystemExit('Base artwork must be 1920x1200')
        ctx.set_source_surface(base, 0, 0)
    ctx.paint()

    # Everything below is clipped away from the protected areas.
    ctx.rectangle(0, 0, WIDTH, HEIGHT)
    for x0, y0, x1, y1 in PROTECTED:
        ctx.rectangle(x1, y0, -(x1 - x0), y1 - y0)
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.clip()

    def rgb(value, alpha=1.0):
        r, g, b = (int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))
        ctx.set_source_rgba(r, g, b, alpha)

    def line(x0, y0, x1, y1, color, width=1.0):
        rgb(color)
        ctx.set_line_width(width)
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
        ctx.stroke()

    def rect(x, y, w, h, color, fill=True, width=1.0):
        rgb(color)
        if fill:
            ctx.rectangle(x, y, w, h)
            ctx.fill()
        else:
            ctx.set_line_width(width)
            ctx.rectangle(x + .5, y + .5, w - 1, h - 1)
            ctx.stroke()

    def text(value, x, y, color, size=9, weight='', align='left', spacing=0):
        layout = PangoCairo.create_layout(ctx)
        layout.set_font_description(
            Pango.FontDescription(f'JetBrains Mono {weight} {size}'.replace('  ', ' ')))
        if spacing:
            attrs = Pango.AttrList()
            attrs.insert(Pango.attr_letter_spacing_new(spacing * Pango.SCALE))
            layout.set_attributes(attrs)
        layout.set_text(value, -1)
        tw, th = layout.get_pixel_size()
        if align == 'right':
            x -= tw
        elif align == 'center':
            x -= tw / 2
        rgb(color)
        ctx.move_to(round(x), round(y - th / 2))
        PangoCairo.show_layout(ctx, layout)
        return tw

    def bracket(x, y, dx, dy, size=34, color=RED, width=2.0):
        rgb(color)
        ctx.set_line_width(width)
        ctx.move_to(x + dx * size, y)
        ctx.line_to(x, y)
        ctx.line_to(x, y + dy * size)
        ctx.stroke()

    def dot_grid(x0, y0, x1, y1, step=24):
        rgb(GRID)
        for y in range(y0, y1 + 1, step):
            for x in range(x0, x1 + 1, step):
                ctx.rectangle(x, y, 2, 2)
        ctx.fill()

    def header(x, y, w, label, index, align='left'):
        rect(x, y - 7, 3, 14, RED)
        text(label, x + 12, y, TEXT_HI, size=9, weight='Bold', spacing=1)
        text(index, x + w, y, TEXT_DIM, size=8, align='right')
        line(x, y + 14.5, x + w, y + 14.5, RED_DIM)
        line(x, y + 14.5, x + 60, y + 14.5, RED_MID, 1.5)

    # ---- frame of the whole display --------------------------------------
    for x, y, dx, dy in ((12, 12, 1, 1), (1908, 12, -1, 1),
                         (12, 1188, 1, -1), (1908, 1188, -1, -1)):
        bracket(x, y, dx, dy)
    for y in range(120, 1081, 40):
        size = 10 if y % 200 == 0 else 5
        line(12, y + .5, 12 + size, y + .5, RED_DIM)
        line(1908 - size, y + .5, 1908, y + .5, RED_DIM)

    # ---- top status rail --------------------------------------------------
    rail = 35.5
    line(250, rail, 690, rail, RED_DIM)
    line(1230, rail, 1440, rail, RED_DIM)
    for x in range(250, 691, 20):
        line(x + .5, rail - 3, x + .5, rail, RED_DIM)
    text('NODE 07  //  DEFENSE GRID  //  LINK SECURE', 470, 22, TEXT_DIM,
         size=8, align='center', spacing=1)
    text('SYS.OK', 1335, 22, TEXT_DIM, size=8, align='center', spacing=1)
    text('ONLINE  ·  UPLINK ACTIVE', 46, 57, TEXT, size=8, spacing=1)

    # ---- left column: neural net core ------------------------------------
    lx, lw = 48, 452
    dot_grid(lx, 96, lx + lw, 868)
    header(lx, 108, lw, 'NEURAL NET CPU  //  CORE MATRIX', 'SEC 01')

    # CPU package; core tiles, pin pulses and readouts are live (cyber-hud.h).
    cx, cy = hud['CORE_CX'], hud['CORE_CY']
    half, pin, pins = hud['PKG_HALF'], hud['PIN_LEN'], hud['PINS']
    rgb('#000000')
    ctx.rectangle(cx - half - pin - 6, cy - half - pin - 6,
                  2 * (half + pin + 6), 2 * (half + pin + 6))
    ctx.fill()
    for side in range(4):
        for k in range(pins):
            along = -half + 16 + k * (2 * half - 32) / (pins - 1)
            a, b = half, half + pin
            if side == 0:
                line(cx + along + .5, cy - b, cx + along + .5, cy - a, RED_DIM, 2)
            elif side == 1:
                line(cx + a, cy + along + .5, cx + b, cy + along + .5, RED_DIM, 2)
            elif side == 2:
                line(cx + along + .5, cy + a, cx + along + .5, cy + b, RED_DIM, 2)
            else:
                line(cx - b, cy + along + .5, cx - a, cy + along + .5, RED_DIM, 2)
    # Substrate with a chamfered pin-1 corner.
    x0, y0, x1, y1, ch = cx - half + .5, cy - half + .5, cx + half - .5, cy + half - .5, 14
    ctx.move_to(x0 + ch, y0)
    for px, py in ((x1, y0), (x1, y1), (x0, y1), (x0, y0 + ch)):
        ctx.line_to(px, py)
    ctx.close_path()
    rgb('#0b0406')
    ctx.fill_preserve()
    rgb(RED_MID)
    ctx.set_line_width(1.5)
    ctx.stroke()
    rgb(RED)
    ctx.arc(x0 + 12, y0 + 12, 2.5, 0, 2 * math.pi)
    ctx.fill()
    span = 4 * hud['TILE'] + 3 * hud['TILE_GAP']
    rect(cx - span / 2 - 6, cy - span / 2 - 6, span + 12, span + 12, RED_DIM,
         fill=False)
    text('CYBERDYNE  CSM-101', cx, cy + half - 13, TEXT_DIM, size=6,
         align='center', spacing=1)
    rx = hud['READOUT_X']
    for i, label in enumerate(('CORES', 'LOAD', 'TEMP', 'CLOCK', 'MODE')):
        y = hud['READOUT_Y'] + i * hud['READOUT_STEP']
        text(label, rx, y, TEXT_DIM, size=8, spacing=1)

    # Memory trace rows and load bars are animated (cyber-hud.h).
    header(lx, 478, lw, 'MEMORY TRACE  //  CPU 0x1F', 'SEC 02')
    header(lx, 732, lw, 'SYSTEM LOAD  //  RESOURCES', 'SEC 03')
    for i, name in enumerate(('CPU', 'MEM', 'SWAP', 'DISK')):
        y = hud['BARS_Y'] + 3 + i * hud['BARS_STEP']
        text(name, lx, y, TEXT, size=8, spacing=1)

    # ---- right column: threat assessment ---------------------------------
    rx0, rw = 1420, 452
    dot_grid(rx0, 96, rx0 + rw, 868)
    # Subsystem names are invented; the first row and every status are live.
    header(rx0, 108, rw, 'SUBSYSTEMS  //  LIVE', 'SEC 04')
    units = (('SKYNET.KERNEL', '', True), ('MEMORY.MANAGER', '', False),
             ('THERMAL.CONTROL', '', False), ('NETWORK.UPLINK', '', False),
             ('STORAGE.ARRAY', '', False))
    for i, (unit, state, hot) in enumerate(units):
        if hot:
            continue
        y = 146 + i * 30
        rect(rx0, y - 11, rw, 22, RED_FAINT if hot else '#0b0406')
        rect(rx0, y - 11, 2, 22, RED if hot else RED_DIM)
        text(unit, rx0 + 12, y, TEXT_HI if hot else STEEL, size=9)

    # Power gauge; charge, flow and readouts are live (cyber-hud.h).
    header(rx0, 304, rw, 'POWER  //  BATTERY', 'SEC 05')
    tx, ty = hud['POWER_CX'], hud['POWER_CY']
    rgb('#000000')
    ctx.rectangle(tx - 100, ty - 92, 200, 192)
    ctx.fill()
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bracket(tx + dx * 92, ty + dy * 84, -dx, -dy, size=18, color=RED_MID, width=1.5)
    segments, r = hud['POWER_SEGMENTS'], hud['POWER_R']
    ctx.set_line_width(7)
    rgb('#1a080c')
    for i in range(segments):
        a = -math.pi / 2 + i * 2 * math.pi / segments + .02
        ctx.new_sub_path()
        ctx.arc(tx, ty, r, a, a + 2 * math.pi / segments - .06)
        ctx.stroke()
    for k in range(4):
        a = k * math.pi / 2
        line(tx + math.cos(a) * (r + 6), ty + math.sin(a) * (r + 6),
             tx + math.cos(a) * (r + 11), ty + math.sin(a) * (r + 11), RED_DIM, 1.5)
    rgb(RED_FAINT)
    ctx.set_line_width(1)
    ctx.arc(tx, ty, hud['POWER_INNER'], 0, 2 * math.pi)
    ctx.stroke()
    text('CHARGE', tx, ty + 22, TEXT_DIM, size=7, align='center', spacing=1)
    sx = hud['POWER_TEXT_X']
    for i, label in enumerate(('STATE', 'DRAW', 'HEALTH', 'CYCLES')):
        y = hud['POWER_TEXT_Y'] + i * hud['POWER_TEXT_STEP']
        text(label, sx, y, TEXT_DIM, size=8, spacing=1)

    header(rx0, 548, rw, 'NETWORK  //  TRAFFIC', 'SEC 06')
    wave_top, wave_h = hud['WAVE_Y'], hud['WAVE_H']
    for y in range(wave_top, wave_top + wave_h + 1, 24):
        line(rx0, y + .5, rx0 + rw, y + .5, '#140507')
    # RX / TX rates under the wave are live (cyber-hud.h, HUD_NET_Y).

    # Thermometer tracks; fills, peaks and values are live (cyber-hud.h).
    header(rx0, 732, rw, 'THERMAL  //  SENSORS', 'SEC 07')
    bar_x, bar_w = hud['THERM_BAR_X'], hud['THERM_BAR_W']
    t_min, t_max = hud['THERM_MIN'], hud['THERM_MAX']
    for i, label in enumerate(('CPU', 'SSD', 'RAM', 'WIFI', 'BOARD')):
        y = hud['THERM_Y'] + i * hud['THERM_STEP']
        text(label, rx0, y, TEXT, size=8, spacing=1)
        rect(bar_x, y - 2, bar_w, 4, '#1a080c')
        for k in range(9):
            x = round(bar_x + k * bar_w / 8) + .5
            line(x, y + 4, x, y + (8 if k % 4 == 0 else 6), RED_DIM)
    y = hud['THERM_Y'] + 4 * hud['THERM_STEP'] + 18
    for k, value in ((0, t_min), (4, (t_min + t_max) / 2), (8, t_max)):
        text(f'{value:.0f}\u00b0', bar_x + k * bar_w / 8, y, TEXT_DIM, size=7,
             align='center')

    # ---- bottom ticker ----------------------------------------------------
    by = 1124.5
    line(48, by, 1380, by, RED_DIM)
    for x in range(48, 1381, 24):
        line(x + .5, by, x + .5, by + (6 if (x - 48) % 120 == 0 else 3), RED_DIM)
    # A small barcode tag, deterministic.
    bx = 1180
    for i in range(46):
        w = 1 + ((i * 7) % 5 == 0) + ((i * 3) % 7 == 0)
        if (i * 11) % 4:
            rect(bx, 1140, w, 22, RED_DIM if i % 9 else RED_MID)
        bx += w + 2
    text('CYB-0x00', 1380, 1174, TEXT_DIM, size=7, align='right', spacing=1)

    surface.write_to_png(sys.argv[2])


if __name__ == '__main__':
    main()
