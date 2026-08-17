#!/usr/bin/env python3
"""Cut the country-leader portrait from tools/leader_portrait.png.

HOI4 country leader portraits are 156x210 and vanilla ships them as .dds, so
that is what gets written:

    gfx/leaders/GER/Portrait_Kekistan_Ben_Shapiro.dds

The source is 1024x1536 (2:3), portraits are ~0.74:1, so the height is cropped
from the bottom — the head stays where it is and torso comes off instead.

Requires Pillow.  Run from anywhere:  python3 tools/generate_portrait.py
"""

import os
import struct
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "leader_portrait.png")
OUT = os.path.join(HERE, "..", "Kekistan", "gfx", "leaders", "GER",
                   "Portrait_Kekistan_Ben_Shapiro.dds")

PORTRAIT = (156, 210)


def write_dds(img, path):
    """Uncompressed 32-bit BGRA .dds, the format vanilla portraits use.

    Pillow cannot write DDS, so the 128-byte header is assembled by hand:
    no mipmaps, no DXT compression, straight A8R8G8B8 pixel data.
    """
    img = img.convert("RGBA")
    w, h = img.size

    header = b"DDS " + struct.pack(
        "<7I44x8I20x",
        124,            # dwSize
        0x0000100F,     # CAPS | HEIGHT | WIDTH | PITCH | PIXELFORMAT
        h, w,
        w * 4,          # dwPitchOrLinearSize
        0,              # dwDepth
        0,              # dwMipMapCount   (dwReserved1[11] is the 44x)
        32,             # pixel format dwSize
        0x41,           # ALPHAPIXELS | RGB
        0,              # dwFourCC
        32,             # bits per pixel
        0x00FF0000,     # red mask
        0x0000FF00,     # green mask
        0x000000FF,     # blue mask
        0xFF000000,     # alpha mask   (dwCaps..dwReserved2 is the 20x)
    )
    # dwCaps sits inside that trailing pad, so patch DDSCAPS_TEXTURE in.
    header = header[:108] + struct.pack("<I", 0x1000) + header[112:]
    assert len(header) == 128, len(header)

    px = img.load()
    body = bytearray()
    for y in range(h):                  # dds is top-down
        for x in range(w):
            r, g, b, a = px[x, y]
            body += bytes((b, g, r, a))

    with open(path, "wb") as f:
        f.write(header)
        f.write(body)


def crop_to_aspect(img, aspect):
    """Trim the bottom (or the fly) until the image matches the aspect."""
    w, h = img.size
    if w / h > aspect:
        return img.crop((0, 0, round(h * aspect), h))
    return img.crop((0, 0, w, round(w / aspect)))


def main():
    src = Image.open(SOURCE).convert("RGB")
    cropped = crop_to_aspect(src, PORTRAIT[0] / PORTRAIT[1])
    print("source", src.size, "cropped to", cropped.size)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    write_dds(cropped.resize(PORTRAIT, Image.LANCZOS), OUT)
    print("wrote", os.path.relpath(OUT, os.path.join(HERE, "..")),
          os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
