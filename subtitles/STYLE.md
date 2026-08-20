# Karaoke caption style — measured spec

Everything below was measured off the reference clip
(`1080×1920`, `29.97 fps`, `3.91 s`, H.264) frame by frame: every frame was
decoded to PNG, the caption band was colour-thresholded into white / yellow /
green masks, and glyph runs, gaps, baselines and outline widths were read off
the pixel grid. Numbers are in pixels at 1080×1920 unless noted.

---

## 1. Typeface

| property | measurement |
|---|---|
| case | **ALL CAPS**, always — no lowercase anywhere in the clip |
| class | ultra-condensed display grotesque (Bebas / Impact family) |
| cap height | **71–73 px** ≈ 3.75 % of frame height |
| stem width | 12–13 px = **0.17 × cap height** |
| counter of `O` | 8 px — so narrow the black outline nearly closes it |
| `O` ink width | 34 px = 0.48 × cap height |
| glyph widths | near-uniform, 30–36 px for most caps; `I` = 12, `M` = 47, `W` = 54 |

**Font: `Bebas Neue`** (Google Fonts, OFL), set **4 % wide** (`ScaleX 104`).

How that was pinned down: 49 condensed/heavy families were rendered through the
same libass pipeline, each sized so its cap height was exactly 72 px, and the
per-glyph ink-width vectors of `TARGETED`, `INTERNET`, `ILLNESS`, `CAUSED`,
`PEOPLE` and `WHY` were compared against the clip. Stock Bebas Neue was closest
(1.85 px average error per glyph) and is uniformly ~4 % narrow, which the
`ScaleX 104` correction removes — final error **0.79 px per glyph**, i.e. below
the clip's own compression noise.

Anton was the runner-up (2.08 px) and is the family most people reach for, but
it is wrong here in a specific, visible way: Anton's `T` renders 30 px against
the clip's 35, and its `N` 30 px against 35–36. Bebas gets both right. The other
near-misses, in order: `Economica`, `Fjalla One`, `Staatliches`,
`Saira ExtraCondensed Black`.

Because libass scales a font so that `usWinAscent + usWinDescent == Fontsize`,
Bebas Neue's cap height works out to `0.538 × Fontsize`:

```
Fontsize 132, ScaleX 104  ->  cap height 71–72 px   (the reference value)
```

## 2. Spacing

| property | measurement |
|---|---|
| letter tracking | ink gap **10–13 px** between adjacent letters → ASS `Spacing: 4` |
| word gap | ink gap **69 px** ≈ 0.96 × cap height — words are pushed far apart |
| line pitch | **115 px** between successive cap tops = 1.61 × cap height |
| max line width | ~**670 px** (62 % of frame width) before the group wraps |

The word gap is far wider than any font's space character; it is reproduced with
two hard spaces carrying extra tracking: `{\fsp12}\h\h{\fsp4}`.

## 3. Placement

| property | measurement |
|---|---|
| cap top of line 1 | **y = 861** (44.8 % of height) — fixed, whatever the line count |
| growth direction | downward; a second line puts its cap top at y = 976 |
| horizontal | centred, but the ink sits at **x = 507**, i.e. **33 px left of centre** |

That 33 px offset is not a design choice — it is exactly half a word gap. The
source builds each line as `WORD␣WORD␣WORD␣` with a **trailing** separator, and
the renderer counts that trailing separator when centring. Emitting the same
trailing separator reproduces the offset for free, on one-word and three-word
lines alike.

Note what this means vertically: the block is **top-anchored, not centred**. A
one-line caption and the first line of a two-line caption sit at exactly the
same height, just above the middle of the frame, clear of the character
standing in the lower third.

## 4. Colour

| role | colour |
|---|---|
| idle words | `#FFFFFF` |
| word being spoken | `#FFD500` |
| emphasis line | `#00FF40` |
| outline | `#000000`, **3 px** |
| shadow | `#000000`, hard (no blur), offset **≈ +4.5 px right and down** |

Measured at a glyph edge: 3 px of black on the left and top, 7–8 px on the
right and bottom — outline plus an offset shadow, exactly what ASS
`Outline: 3, Shadow: 4.5` produces. There is no box, no background plate, no
blur, no glow.

## 5. Motion

There is **no** animation: no pop, no scale-in, no fade, no drift. Captions cut
in and out on a single frame. All the movement is colour.

- One word at a time turns `#FFD500` for exactly the interval it is spoken, then
  reverts to white. Earlier words do **not** stay highlighted — the yellow is a
  single travelling word, not a fill sweep.
- A group is on screen from the start of its first word to the end of its last
  word. Gaps between groups (0–2 frames of empty screen in the reference) are
  just pauses in the speech, not a designed gap.
- A one-word group renders that word yellow the whole time (`HIM.`).

Measured highlight durations: 0.53 s, 0.33 s, 0.10 s, 0.40 s, 0.13 s, 0.47 s,
0.40 s, 0.37 s, 0.30 s — i.e. straight word-level ASR timestamps, nothing
quantised or smoothed.

### The green line

`THEN WHY DO` renders **entirely** green for its whole 0.53 s, with no
travelling highlight inside it. It is not a speaker colour — the same character
speaks the very next group in normal white/yellow. Treat it as an occasional
whole-group emphasis: one group in six here, landing on the rhetorical turn.

## 6. Grouping and line breaking

Reference text: *"…no evidence the CIA caused his illness or targeted him. Then
why do internet people call…"*

```
NO EVIDENCE THE          CIA CAUSED HIS         ILLNESS OR      HIM.
                                                TARGETED

THEN WHY DO              INTERNET PEOPLE
(all green)              CALL
```

The rule that produces exactly this:

1. Chunk the word stream into groups of **3**, restarting the count at every
   sentence end. `him.` ends a sentence, so it becomes a group of one.
2. If a group's rendered width exceeds ~670 px, break before the word that
   overflows. Never more than two lines.
3. Show each group from its first word's start to its last word's end.

## 7. Reproduction

`brainrot_captions.py` in this directory implements all of the above and emits
an `.ass` file (or burns it in with ffmpeg).

Verified by regenerating the reference clip's captions from
`examples/reference_clip.json` and diffing every frame against the source:

```
466 measured caption-block edges across 118 frames
  mean error 2.35 px   median 2 px   p90 6 px   max 7 px
  wrap points, line count, block centre, cap tops: identical on every frame
  group boundaries and highlight advances: identical on every frame but one
```

The single disagreeing frame is the source's own glitch — it shows `HIM.` in
white for one frame before the highlight catches up. That was not reproduced.

`examples/comparison.png` is a side-by-side of nine frames.
