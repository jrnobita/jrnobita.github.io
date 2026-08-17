#!/usr/bin/env python3
"""Cut the Kekistan flag TGAs from tools/kekistan_flag.png.

Hearts of Iron IV wants three sizes of every flag:

    gfx/flags/<TAG>.tga         82x52
    gfx/flags/medium/<TAG>.tga  41x26
    gfx/flags/small/<TAG>.tga   10x7

The source art is 1599x960 (5:3) and HOI4 flags are ~1.58:1, so it is cropped
to the right aspect before scaling — otherwise the resize would squeeze it
horizontally by about 5%. The 85px comes off the fly (right edge), which is
empty green, so the cross keeps its original distance from the hoist.

Requires Pillow.  Run from anywhere:  python3 tools/generate_flags.py
"""

import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "kekistan_flag.png")
FLAGS = os.path.join(HERE, "..", "Kekistan", "gfx", "flags")

SIZES = {
    "": (82, 52),
    "medium": (41, 26),
    "small": (10, 7),
}

# Base tag plus every ideology variant HOI4 looks for.
NAMES = ["GER", "GER_fascism", "GER_communism", "GER_democratic", "GER_neutrality"]


def write_tga(img, path):
    """Uncompressed 32-bit BGRA, bottom-up — the layout vanilla flags use.

    Pillow's own TGA writer emits a top-down 24-bit file, which some builds
    render upside down, so the header is written by hand.
    """
    img = img.convert("RGB")
    w, h = img.size
    header = bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0]) + \
        w.to_bytes(2, "little") + h.to_bytes(2, "little") + bytes([32, 8])

    px = img.load()
    body = bytearray()
    for y in range(h - 1, -1, -1):          # bottom row first
        for x in range(w):
            r, g, b = px[x, y]
            body += bytes((b, g, r, 255))

    with open(path, "wb") as f:
        f.write(header)
        f.write(body)


def crop_to_aspect(img, aspect):
    """Trim the fly (right edge) until the image matches the target aspect."""
    w, h = img.size
    if w / h > aspect:
        return img.crop((0, 0, round(h * aspect), h))
    return img.crop((0, 0, w, round(w / aspect)))     # trim the bottom instead


def main():
    master = crop_to_aspect(Image.open(SOURCE).convert("RGB"), 82 / 52)
    print("source cropped to", master.size)

    for subdir, size in SIZES.items():
        out_dir = os.path.join(FLAGS, subdir)
        os.makedirs(out_dir, exist_ok=True)
        scaled = master.resize(size, Image.LANCZOS)
        for name in NAMES:
            path = os.path.join(out_dir, name + ".tga")
            write_tga(scaled, path)
            print("wrote", os.path.relpath(path, os.path.dirname(FLAGS)))


if __name__ == "__main__":
    main()
