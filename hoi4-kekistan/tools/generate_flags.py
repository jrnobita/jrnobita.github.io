#!/usr/bin/env python3
"""Generate the Kekistan flag TGAs used by the mod.

Draws the flag once at high resolution (pure vector-ish primitives, no external
assets) and downsamples to the three sizes Hearts of Iron IV expects:

    gfx/flags/<TAG>.tga         82x52
    gfx/flags/medium/<TAG>.tga  41x26
    gfx/flags/small/<TAG>.tga   10x7

Requires Pillow.  Run from anywhere:  python3 tools/generate_flags.py
"""

import os
from PIL import Image, ImageDraw

# ---------------------------------------------------------------- palette ---
GREEN = (95, 150, 65)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Master canvas: 24x the large flag so downsampling does the anti-aliasing.
W, H = 82 * 24, 52 * 24

# Cross is offset toward the hoist, like the Reichskriegsflagge it parodies.
CX, CY = 0.381 * W, 0.500 * H

# Half-widths of the cross bands, measured from the cross centre line.
# Given in fractions of the flag height so the vertical and horizontal arms
# end up with identical stroke weights.
BAND_BLACK_IN = 0.045   # thick central black bar
BAND_WHITE_IN = 0.062
BAND_BLACK_OUT = 0.082  # thin outer black line
BAND_WHITE_OUT = 0.115

# Concentric rings of the central disc, as fractions of the flag height.
RING_WHITE_OUT = 0.328
RING_BLACK_OUT = 0.320
RING_WHITE_MID = 0.262
RING_BLACK_IN = 0.252
RING_FIELD = 0.240

# Clover in the canton.
CLOVER_CX, CLOVER_CY = 0.113 * W, 0.169 * H
CLOVER_R = 0.115 * H


def _bar(draw, colour, half):
    """Draw one horizontal + one vertical band of the cross."""
    d = half * H
    draw.rectangle([0, CY - d, W, CY + d], fill=colour)
    draw.rectangle([CX - d, 0, CX + d, H], fill=colour)


def _disc(draw, colour, r):
    d = r * H
    draw.ellipse([CX - d, CY - d, CX + d, CY + d], fill=colour)


def _kek_glyph(size):
    """The barred KEK monogram: K + centre bars + mirrored K, with a K's
    arms and stem repeated above and below the centre."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    s = size

    def rect(x0, y0, x1, y1):
        d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=BLACK)

    def line(x0, y0, x1, y1, w):
        d.line([(x0 * s, y0 * s), (x1 * s, y1 * s)], fill=BLACK, width=int(w * s))

    stem = 0.052   # width of an upright bar
    arm = 0.072    # diagonal stroke weight
    bar = 0.042    # thickness of the horizontal bars

    # --- centre: three short uprights between two horizontal bars ---------
    for x in (0.438, 0.500, 0.562):
        rect(x - 0.022, 0.390, x + 0.022, 0.610)
    rect(0.385, 0.330 - bar / 2, 0.615, 0.330 + bar / 2)
    rect(0.385, 0.670 - bar / 2, 0.615, 0.670 + bar / 2)

    # --- left K and its mirror on the right -------------------------------
    for sign, x_stem in ((1, 0.150), (-1, 0.850)):
        rect(x_stem - stem / 2, 0.285, x_stem + stem / 2, 0.715)
        line(x_stem, 0.500, x_stem + sign * 0.255, 0.245, arm)
        line(x_stem, 0.500, x_stem + sign * 0.255, 0.755, arm)

    # --- the same K rotated a quarter turn, above and below ---------------
    for sign, y_stem in ((1, 0.200), (-1, 0.800)):
        rect(0.400, y_stem - stem / 2, 0.600, y_stem + stem / 2)
        line(0.500, y_stem + sign * 0.045, 0.278, y_stem - sign * 0.118, arm)
        line(0.500, y_stem + sign * 0.045, 0.722, y_stem - sign * 0.118, arm)

    return layer


def _heart(draw, cx, bottom, w, h, colour):
    """A heart with its tip at (cx, bottom), body rising to bottom - h."""
    top = bottom - h
    lobe_r = 0.30 * w
    lobe_y = top + 0.34 * h
    draw.ellipse([cx - 0.52 * w, lobe_y - lobe_r, cx - 0.52 * w + 2 * lobe_r,
                  lobe_y + lobe_r], fill=colour)
    draw.ellipse([cx + 0.52 * w - 2 * lobe_r, lobe_y - lobe_r, cx + 0.52 * w,
                  lobe_y + lobe_r], fill=colour)
    draw.polygon([(cx - 0.52 * w, lobe_y), (cx, bottom), (cx + 0.52 * w, lobe_y),
                  (cx, top + 0.20 * h)], fill=colour)


def _clover(size):
    """Four outlined hearts pointing at a common centre."""
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    leaf = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(leaf)

    cx = size / 2
    tip = size / 2 - 0.06 * size          # small gap at the centre
    w, h = 0.56 * size, 0.46 * size
    _heart(d, cx, tip, w, h, BLACK)
    _heart(d, cx, tip - 0.055 * size, 0.58 * w, 0.60 * h, WHITE)

    for angle in (45, 135, 225, 315):
        layer.alpha_composite(leaf.rotate(angle, resample=Image.BICUBIC))
    return layer


def build_flag():
    img = Image.new("RGB", (W, H), GREEN)
    draw = ImageDraw.Draw(img)

    # Cross, painted outside-in.
    _bar(draw, WHITE, BAND_WHITE_OUT)
    _bar(draw, BLACK, BAND_BLACK_OUT)
    _bar(draw, WHITE, BAND_WHITE_IN)
    _bar(draw, BLACK, BAND_BLACK_IN)

    # Central disc.
    _disc(draw, WHITE, RING_WHITE_OUT)
    _disc(draw, BLACK, RING_BLACK_OUT)
    _disc(draw, WHITE, RING_WHITE_MID)
    _disc(draw, BLACK, RING_BLACK_IN)
    _disc(draw, WHITE, RING_FIELD)

    glyph_size = int(2 * RING_FIELD * H * 0.93)
    glyph = _kek_glyph(glyph_size)
    img.paste(glyph, (int(CX - glyph_size / 2), int(CY - glyph_size / 2)), glyph)

    clover_size = int(2 * CLOVER_R)
    clover = _clover(clover_size)
    img.paste(clover, (int(CLOVER_CX - clover_size / 2),
                       int(CLOVER_CY - clover_size / 2)), clover)

    return img


def write_tga(img, path):
    """Uncompressed 32-bit BGRA, bottom-up — the layout vanilla flags use.

    Pillow's own TGA writer emits a top-down 24-bit file, which some builds
    render upside down, so the header is written by hand.
    """
    img = img.convert("RGBA")
    w, h = img.size
    header = bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0]) + \
        w.to_bytes(2, "little") + h.to_bytes(2, "little") + bytes([32, 8])

    px = img.load()
    body = bytearray()
    for y in range(h - 1, -1, -1):          # bottom row first
        for x in range(w):
            r, g, b, a = px[x, y]
            body += bytes((b, g, r, a))

    with open(path, "wb") as f:
        f.write(header)
        f.write(body)


SIZES = {
    "": (82, 52),
    "medium": (41, 26),
    "small": (10, 7),
}

# Base tag plus every ideology variant HOI4 looks for.
NAMES = ["GER", "GER_fascism", "GER_communism", "GER_democratic", "GER_neutrality"]


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "Kekistan", "gfx", "flags")
    master = build_flag()

    for subdir, size in SIZES.items():
        out_dir = os.path.join(root, subdir)
        os.makedirs(out_dir, exist_ok=True)
        scaled = master.resize(size, Image.LANCZOS)
        for name in NAMES:
            path = os.path.join(out_dir, name + ".tga")
            write_tga(scaled, path)
            print("wrote", os.path.relpath(path, os.path.dirname(root)))

    preview = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "preview.png")
    master.resize((820, 520), Image.LANCZOS).save(preview)
    print("wrote", preview)


if __name__ == "__main__":
    main()
