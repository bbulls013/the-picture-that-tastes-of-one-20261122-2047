#!/usr/bin/env python3
"""Golden Hour Burger - a deterministic 1024x1024 food picture.

Renders one glossy cheeseburger with fries on a wooden table in warm
evening light: sesame dome, melted cheese drip, charred patty, steam.
Standard library only; writes a PNG to /output/entry.png (or a path
given as argv[1] for local testing).
"""
import math
import os
import struct
import sys
import zlib

W = 1024
H = 1024
px = bytearray(W * H * 3)


def put(x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = r
        px[i + 1] = g
        px[i + 2] = b


def blend(x, y, r, g, b, a):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i] = int(px[i] * (1 - a) + r * a)
        px[i + 1] = int(px[i + 1] * (1 - a) + g * a)
        px[i + 2] = int(px[i + 2] * (1 - a) + b * a)


def hline(y, x0, x1, r, g, b):
    if y < 0 or y >= H:
        return
    x0 = max(0, x0)
    x1 = min(W - 1, x1)
    base = y * W * 3
    for x in range(x0, x1 + 1):
        i = base + x * 3
        px[i] = r
        px[i + 1] = g
        px[i + 2] = b


def ellipse(cx, cy, rx, ry, r, g, b, top_only=False):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        if top_only and y > cy:
            continue
        t = (y - cy) / ry
        if abs(t) > 1:
            continue
        half = rx * math.sqrt(1 - t * t)
        hline(y, int(cx - half), int(cx + half), r, g, b)


def ellipse_shade(cx, cy, rx, ry, dark, light, top_only=False):
    """Ellipse with a vertical gradient: light at top, dark at bottom."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        if top_only and y > cy:
            continue
        t = (y - cy) / ry
        if abs(t) > 1:
            continue
        half = rx * math.sqrt(1 - t * t)
        f = (t + 1) / 2
        r = int(light[0] + (dark[0] - light[0]) * f)
        g = int(light[1] + (dark[1] - light[1]) * f)
        b = int(light[2] + (dark[2] - light[2]) * f)
        hline(y, int(cx - half), int(cx + half), r, g, b)


def rrect(x0, y0, x1, y1, rad, r, g, b):
    for y in range(y0, y1 + 1):
        inset = 0
        if y < y0 + rad:
            d = y0 + rad - y
            inset = rad - int(math.sqrt(max(0, rad * rad - d * d)))
        elif y > y1 - rad:
            d = y - (y1 - rad)
            inset = rad - int(math.sqrt(max(0, rad * rad - d * d)))
        hline(y, x0 + inset, x1 - inset, r, g, b)


def speckles(cx, cy, rx, ry, n, seed, r, g, b, size=2):
    s = seed
    for _ in range(n):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        a = (s % 6283) / 1000.0
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        d = math.sqrt((s % 1000) / 1000.0)
        x = int(cx + math.cos(a) * rx * d)
        y = int(cy + math.sin(a) * ry * d)
        for dy in range(size):
            for dx in range(size):
                put(x + dx, y + dy, r, g, b)


def steam(x0, y0, height, sway, seed):
    for i in range(height):
        t = i / height
        x = int(x0 + math.sin(t * 5.2 + seed) * sway * t)
        y = y0 - i
        wdt = 3 + int(7 * t)
        a = 0.30 * (1 - t) + 0.05
        for dx in range(-wdt, wdt + 1):
            blend(x + dx, y, 245, 240, 230, a * (1 - abs(dx) / (wdt + 1)))


def background():
    for y in range(H):
        t = y / H
        r = int(58 + 30 * t)
        g = int(34 + 16 * t)
        b = int(22 + 8 * t)
        hline(y, 0, W - 1, r, g, b)
    # warm glow behind the dish
    for y in range(H):
        for x in range(W):
            dx = (x - 512) / 560
            dy = (y - 430) / 520
            d = dx * dx + dy * dy
            if d < 1:
                f = (1 - d) * 0.45
                blend(x, y, 255, 190, 110, f)
    # wooden table
    for y in range(700, H):
        t = (y - 700) / 324
        r = int(96 + 26 * t)
        g = int(60 + 14 * t)
        b = int(34 + 8 * t)
        hline(y, 0, W - 1, r, g, b)
    for py_ in (760, 830, 905, 975):
        hline(py_, 0, W - 1, 52, 32, 18)
        hline(py_ + 2, 0, W - 1, 140, 96, 58)


def plate():
    ellipse(512, 782, 372, 96, 30, 18, 10)          # shadow
    ellipse_shade(512, 764, 360, 92, (168, 160, 148), (250, 246, 236))
    ellipse_shade(512, 758, 300, 72, (196, 188, 172), (238, 232, 218))


def fries():
    # a heaped pile of thick golden fries on the right of the plate
    sticks = [(730, 712, 786, 596), (758, 716, 824, 592), (700, 714, 740, 606),
              (792, 718, 864, 612), (724, 722, 772, 624), (764, 724, 820, 630),
              (742, 728, 800, 652), (706, 726, 752, 640), (796, 730, 856, 656)]
    for (x0, y0, x1, y1) in sticks:
        steps = 70
        for i in range(steps + 1):
            t = i / steps
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)
            for dy in range(-9, 10):
                for dx in range(-9, 10):
                    if dx * dx + dy * dy <= 81:
                        put(x + dx, y + dy, 240, 182, 76)
        for i in range(steps + 1):
            t = i / steps
            x = int(x0 + (x1 - x0) * t) - 4
            y = int(y0 + (y1 - y0) * t) - 4
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    put(x + dx, y + dy, 255, 226, 152)
    speckles(785, 672, 95, 62, 80, 777, 255, 252, 240, 2)
    ellipse_shade(866, 730, 48, 17, (150, 24, 18), (224, 64, 46))  # ketchup
    ellipse(858, 724, 16, 5, 244, 110, 88)


def soda():
    # a tall glass of cola with ice and a straw, back left
    gx, gy = 176, 560
    rrect(gx - 52, gy, gx + 52, gy + 190, 14, 96, 44, 20)
    rrect(gx - 44, gy + 10, gx + 44, gy + 182, 10, 120, 58, 26)
    for (ix, iy) in ((-24, 30), (10, 52), (-8, 88), (20, 118)):
        rrect(gx + ix - 15, gy + iy, gx + ix + 15, gy + iy + 26, 6, 236, 224, 204)
    speckles(gx, gy + 100, 38, 80, 70, 555, 232, 180, 120, 2)
    for i in range(150):
        x = gx + 18 + i // 3
        y = gy - 84 + i
        for dx in range(-5, 6):
            put(x + dx, y, 216, 48, 52 if (i // 14) % 2 else 244)
    ellipse(gx, gy + 196, 62, 12, 30, 18, 10)


def bokeh():
    s = 8080
    for _ in range(26):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        x = s % W
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        y = s % 480
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        r = 8 + s % 30
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r, x + r + 1):
                d = ((xx - x) / r) ** 2 + ((yy - y) / r) ** 2
                if d < 1:
                    blend(xx, yy, 255, 196, 120, 0.10 * (1 - d))


def burger():
    cx = 462
    # bottom bun
    ellipse_shade(cx, 748, 248, 46, (168, 100, 42), (234, 166, 94))
    # thick charred patty
    ellipse_shade(cx, 714, 262, 44, (62, 36, 20), (120, 74, 42))
    speckles(cx, 708, 230, 28, 320, 4242, 38, 20, 11, 3)
    speckles(cx, 702, 218, 24, 170, 99, 152, 102, 60, 2)
    # melted cheese with long drips
    ellipse_shade(cx, 682, 268, 36, (224, 142, 18), (255, 198, 66))
    for dx, ln in ((-196, 52), (-84, 72), (18, 44), (116, 64), (204, 42)):
        for i in range(ln):
            wdt = 15 - i // 7
            hline(698 + i, cx + dx - wdt, cx + dx + wdt, 250, 178, 46)
        ellipse(cx + dx, 698 + ln, 10, 7, 250, 178, 46)
    # tomato slice
    ellipse_shade(cx, 656, 240, 28, (166, 32, 24), (234, 86, 64))
    ellipse(cx - 60, 650, 60, 8, 246, 120, 96)
    # lettuce frill
    for i in range(16):
        lx = cx - 248 + i * 33
        ellipse(lx, 634 + (7 if i % 2 else -5), 31, 17, 94, 180, 60)
    ellipse_shade(cx, 630, 250, 24, (68, 138, 42), (142, 216, 94))
    # top bun: a true dome rising from the lettuce line
    ellipse_shade(cx, 626, 262, 176, (184, 110, 46), (248, 188, 104), top_only=True)
    # toasted rim along the dome base
    for y in range(606, 628):
        t = (y - 626) / 176
        half = 262 * math.sqrt(max(0, 1 - t * t))
        hline(y, int(cx - half), int(cx + half), 214, 138, 62)
    # gloss highlight sweeping the dome
    for y in range(462, 580):
        for x in range(292, 540):
            dx = (x - 404) / 128
            dy = (y - 508) / 44
            if dx * dx + dy * dy < 1:
                blend(x, y, 255, 242, 208, 0.55 * (1 - dx * dx - dy * dy))
    # sesame seeds scattered over the dome
    s = 2026
    for _ in range(58):
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        a = (s % 6283) / 1000.0
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        d = math.sqrt((s % 1000) / 1000.0) * 0.88
        x = int(cx + math.cos(a) * 240 * d)
        y = int(560 + math.sin(a) * 120 * d)
        if y > 616 or y < 452:
            continue
        ellipse(x, y, 10, 6, 252, 231, 170)
        ellipse(x - 2, y - 2, 4, 2, 255, 247, 212)


def garnish():
    # herb leaves on the table
    for (x, y) in ((180, 850), (230, 880), (840, 860), (150, 800)):
        ellipse(x, y, 26, 10, 74, 150, 54)
        ellipse(x, y - 3, 18, 6, 116, 196, 80)
    # tomato wedges beside the plate
    ellipse_shade(196, 726, 52, 20, (160, 30, 22), (228, 76, 54))
    ellipse_shade(828, 800, 44, 17, (160, 30, 22), (228, 76, 54))
    speckles(512, 900, 420, 60, 90, 31, 250, 232, 180, 2)


def main():
    background()
    bokeh()
    soda()
    plate()
    fries()
    burger()
    garnish()
    steam(408, 452, 210, 28, 1.3)
    steam(500, 444, 240, 34, 3.9)
    steam(592, 456, 190, 24, 5.1)
    out = sys.argv[1] if len(sys.argv) > 1 else "/output/entry.png"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += px[y * W * 3:(y + 1) * W * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(out, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
