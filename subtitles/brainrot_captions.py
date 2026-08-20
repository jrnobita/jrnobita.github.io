#!/usr/bin/env python3
"""
Karaoke caption generator that reproduces the "brainrot short" subtitle style
(white Bebas Neue caps, black outline + hard drop shadow, one word highlighted
yellow as it is spoken, occasional whole-line green emphasis).

Every number in DEFAULTS was measured off a reference 1080x1920 clip; see
STYLE.md for the measurements and how they were taken.

Usage
-----
  # word timings -> .ass
  python3 brainrot_captions.py words.json -o out.ass

  # word timings -> captions burned into a video
  python3 brainrot_captions.py words.json --video in.mp4 -o out.mp4

Input format (JSON), as produced by WhisperX / whisper-timestamped:

  [{"word": "no", "start": 0.00, "end": 0.18}, ...]

  or  {"words": [ ...same... ]}

Marking a group for the green emphasis colour: add "emphasis": true to any
word in it, or pass --emphasis-words "then why do".
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# Style constants (measured from the reference clip at 1080x1920)
# --------------------------------------------------------------------------

DEFAULTS = dict(
    play_w=1080,
    play_h=1920,
    font="Bebas Neue",
    # libass sizes a font so that usWinAscent+usWinDescent == Fontsize.
    # For Bebas Neue that makes the cap height 0.538 * Fontsize, so 132 -> 71px.
    font_size=132,
    scale_x=104,          # the reference is ~4% wider than stock Bebas Neue
    spacing=4,            # letter tracking, px
    sep_spacing=12,       # tracking applied to the two hard spaces between words
    outline=3,            # black border, px
    shadow=4.5,           # hard black shadow, offset down-right, px
    cap_top=861,          # y of the cap-height top of the FIRST line
    line_pitch=115,       # y distance between successive cap tops
    center_x=540,         # centring anchor; the trailing separator pulls the
                          # visible ink ~33px left of this, as in the reference
    max_line_w=690,       # wrap when a line's ink would exceed this, px
    words_per_group=3,
    color_idle="FFFFFF",  # RRGGBB
    color_active="FFD500",
    color_emphasis="00FF40",
)

# distance from an \an8 anchor down to the cap-height top, as a fraction of
# font_size: (usWinAscent - sCapHeight) / (usWinAscent + usWinDescent).
AN8_TO_CAP = (950 - 700) / 1300.0

# em height as a fraction of font_size, for Bebas Neue:
# unitsPerEm / (usWinAscent + usWinDescent).
EM_PER_FONTSIZE = 1000 / 1300.0

# Bebas Neue advance widths in 1/1000 em, for the wrap calculation.
_ADV = {
    "A": 401, "B": 404, "C": 383, "D": 406, "E": 363, "F": 344, "G": 391,
    "H": 420, "I": 192, "J": 265, "K": 414, "L": 344, "M": 538, "N": 427,
    "O": 400, "P": 386, "Q": 400, "R": 403, "S": 372, "T": 364, "U": 402,
    "V": 382, "W": 557, "X": 406, "Y": 394, "Z": 362,
    "0": 400, "1": 400, "2": 400, "3": 400, "4": 400, "5": 400, "6": 400,
    "7": 400, "8": 400, "9": 400,
    ".": 188, ",": 188, "!": 210, "?": 363, "'": 188, "’": 188,
    "-": 270, ":": 188, ";": 188, "\"": 336, "%": 589, "$": 400, "&": 417,
    " ": 160,
}
_ADV_DEFAULT = 400

SENTENCE_END = re.compile(r"[.!?…]$")


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

@dataclass
class Word:
    text: str
    start: float
    end: float
    emphasis: bool = False


@dataclass
class Group:
    words: list[Word]
    lines: list[list[Word]] = field(default_factory=list)

    @property
    def start(self) -> float:
        return self.words[0].start

    @property
    def end(self) -> float:
        return self.words[-1].end

    @property
    def emphasis(self) -> bool:
        return any(w.emphasis for w in self.words)


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

def word_width(text: str, cfg: dict) -> float:
    """Ink+advance width of a word in px, close enough for wrap decisions."""
    em = cfg["font_size"] * EM_PER_FONTSIZE
    adv = sum(_ADV.get(c, _ADV_DEFAULT) for c in text) / 1000.0 * em
    return (adv + cfg["spacing"] * len(text)) * cfg["scale_x"] / 100.0


def sep_width(cfg: dict) -> float:
    em = cfg["font_size"] * EM_PER_FONTSIZE
    return 2 * (_ADV[" "] / 1000.0 * em + cfg["sep_spacing"]) * cfg["scale_x"] / 100.0


def group_words(words: list[Word], cfg: dict) -> list[Group]:
    """Chunk into groups of N words, restarting at every sentence end."""
    groups: list[Group] = []
    buf: list[Word] = []
    for w in words:
        buf.append(w)
        if len(buf) >= cfg["words_per_group"] or SENTENCE_END.search(w.text):
            groups.append(Group(buf))
            buf = []
    if buf:
        groups.append(Group(buf))
    for g in groups:
        g.lines = wrap_group(g, cfg)
    return groups


def wrap_group(group: Group, cfg: dict) -> list[list[Word]]:
    """Greedy wrap at max_line_w; the reference never needs more than 2 lines."""
    lines: list[list[Word]] = []
    cur: list[Word] = []
    cur_w = 0.0
    sep = sep_width(cfg)
    for w in group.words:
        ww = word_width(w.text, cfg)
        add = ww if not cur else sep + ww
        if cur and cur_w + add > cfg["max_line_w"]:
            lines.append(cur)
            cur, cur_w = [w], ww
        else:
            cur.append(w)
            cur_w += add
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------------------
# ASS output
# --------------------------------------------------------------------------

def ass_color(rgb: str) -> str:
    rgb = rgb.lstrip("#")
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H00{b}{g}{r}".upper()


def ass_time(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def header(cfg: dict) -> str:
    return f"""[Script Info]
; Generated by brainrot_captions.py -- see STYLE.md
ScriptType: v4.00+
PlayResX: {cfg['play_w']}
PlayResY: {cfg['play_h']}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{cfg['font']},{cfg['font_size']},{ass_color(cfg['color_idle'])},{ass_color(cfg['color_active'])},&H00000000,&H00000000,0,0,0,0,{cfg['scale_x']},100,{cfg['spacing']},0,1,{cfg['outline']},{cfg['shadow']},8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def render_line(line: list[Word], active: Word | None, cfg: dict) -> str:
    """One line of a group, with `active` painted in the highlight colour."""
    idle = ass_color(cfg["color_idle"])
    hot = ass_color(cfg["color_active"])
    sep = r"{\fsp%s}\h\h{\fsp%s}" % (cfg["sep_spacing"], cfg["spacing"])
    out = []
    for w in line:
        color = hot if (active is not None and w is active) else idle
        out.append(r"{\c%s}%s" % (color, w.text))
    # the trailing separator is what pulls the block ~half a word-space left,
    # exactly as the reference does
    return sep.join(out) + sep


def render_line_solid(line: list[Word], color: str, cfg: dict) -> str:
    sep = r"{\fsp%s}\h\h{\fsp%s}" % (cfg["sep_spacing"], cfg["spacing"])
    body = sep.join(w.text for w in line)
    return r"{\c%s}" % ass_color(color) + body + sep


def dialogue(start: float, end: float, y: float, text: str, cfg: dict) -> str:
    pos = r"{\an8\pos(%s,%s)}" % (cfg["center_x"], round(y, 1))
    return (f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,"
            f"{pos}{text}\n")


def build_ass(groups: list[Group], cfg: dict) -> str:
    out = [header(cfg)]
    anchor0 = cfg["cap_top"] - AN8_TO_CAP * cfg["font_size"]
    for g in groups:
        ys = [anchor0 + i * cfg["line_pitch"] for i in range(len(g.lines))]
        if g.emphasis:
            # whole group in the emphasis colour for its full duration
            for line, y in zip(g.lines, ys):
                out.append(dialogue(g.start, g.end, y,
                                    render_line_solid(line, cfg["color_emphasis"], cfg), cfg))
            continue
        for w in g.words:
            for line, y in zip(g.lines, ys):
                out.append(dialogue(w.start, w.end, y,
                                    render_line(line, w, cfg), cfg))
    return "".join(out)


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------

def load_words(path: str, upper: bool = True) -> list[Word]:
    with open(path) as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        data = data.get("words") or data.get("segments") or []
        if data and "words" in data[0]:          # whisper segment list
            data = [w for seg in data for w in seg["words"]]
    words = []
    for item in data:
        text = (item.get("word") or item.get("text") or "").strip()
        if not text:
            continue
        words.append(Word(
            text=text.upper() if upper else text,
            start=float(item["start"]),
            end=float(item["end"]),
            emphasis=bool(item.get("emphasis", False)),
        ))
    return words


def apply_emphasis_phrase(words: list[Word], phrase: str) -> None:
    target = [w.upper() for w in phrase.split()]
    n = len(target)
    for i in range(len(words) - n + 1):
        if [re.sub(r"[^\w']", "", w.text) for w in words[i:i + n]] == target:
            for w in words[i:i + n]:
                w.emphasis = True


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def burn(video: str, ass_path: str, out: str, fontsdir: str | None) -> None:
    ffmpeg = os.environ.get("FFMPEG", "ffmpeg")
    esc = ass_path.replace("\\", "/").replace(":", r"\:")
    vf = f"subtitles={esc}"
    if fontsdir:
        vf += f":fontsdir={fontsdir}"
    cmd = [ffmpeg, "-y", "-i", video, "-vf", vf,
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-c:a", "copy", out]
    subprocess.run(cmd, check=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("words", help="JSON file of word-level timings")
    p.add_argument("-o", "--out", required=True, help="output .ass or video file")
    p.add_argument("--video", help="burn the captions into this video")
    p.add_argument("--fontsdir", help="directory holding Anton.ttf")
    p.add_argument("--emphasis-words", action="append", default=[],
                   help="phrase to render in the green emphasis colour (repeatable)")
    p.add_argument("--no-upper", action="store_true", help="keep the original casing")
    for key in ("font", "color_idle", "color_active", "color_emphasis"):
        p.add_argument("--" + key.replace("_", "-"), default=None)
    for key in ("font_size", "scale_x", "spacing", "sep_spacing", "outline",
                "shadow", "cap_top", "line_pitch", "center_x", "max_line_w",
                "words_per_group", "play_w", "play_h"):
        p.add_argument("--" + key.replace("_", "-"), type=float, default=None)
    args = p.parse_args(argv)

    cfg = dict(DEFAULTS)
    for key in cfg:
        val = getattr(args, key, None)
        if val is None:
            continue
        cfg[key] = int(val) if isinstance(DEFAULTS[key], int) else val

    words = load_words(args.words, upper=not args.no_upper)
    if not words:
        print("no words in input", file=sys.stderr)
        return 1
    for phrase in args.emphasis_words:
        apply_emphasis_phrase(words, phrase)

    ass = build_ass(group_words(words, cfg), cfg)

    if args.video:
        ass_path = os.path.splitext(args.out)[0] + ".ass"
        with open(ass_path, "w") as fh:
            fh.write(ass)
        burn(args.video, ass_path, args.out, args.fontsdir)
        print(f"wrote {ass_path} and {args.out}")
    else:
        with open(args.out, "w") as fh:
            fh.write(ass)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
