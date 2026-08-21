# The prompt

Two versions. Use the **short form** when the generator in this directory is
available; use the **full form** when whatever is doing the work has to rebuild
the style from scratch.

---

## Short form

```
Caption this clip in our house style. The spec is subtitles/STYLE.md in this
repo and subtitles/brainrot_captions.py already encodes every number in it.

1. Transcribe with word-level timestamps (WhisperX or whisper-timestamped),
   output JSON.
2. sh subtitles/fetch_font.sh                    # Bebas Neue -> subtitles/fonts
3. python3 subtitles/brainrot_captions.py words.json \
       --video IN.mp4 -o OUT.mp4 \
       --fontsdir subtitles/fonts \
       --emphasis-words "<the one rhetorical line that should go green>"

Do not change any style flag unless I ask. Two judgement calls are yours:
- which single group gets the green emphasis (the question / reveal /
  punchline -- roughly one group in six, never two in a row);
- whether the caption block collides with the character. It sits just above
  centre because these clips put the character in the lower third. If this one
  frames the subject higher, move the whole block with --cap-top and keep
  everything else.

If the clip is not 1080x1920, scale --font-size, --cap-top, --line-pitch,
--max-line-w, --outline and --shadow by the frame-height ratio and pass
--play-w/--play-h.
```

---

## Full form

Self-contained: describes the style tightly enough to rebuild from scratch,
and names the tooling here for when it is available.

---

```
Caption this clip in the "brainrot karaoke" style. Match it exactly — these
numbers are measured from a reference render at 1080x1920 and scale linearly
with frame height.

TYPEFACE
- Bebas Neue (Google Fonts, OFL), set 4% WIDE -- ASS ScaleX 104. The extra 4%
  matters: stock Bebas is uniformly a touch narrow against the reference.
  Fallbacks in order: Economica, Anton, Fjalla One, Staatliches, Impact.
  (Anton is the obvious guess and it is wrong: its T and N are ~5px too narrow
  at this size.)
- ALL CAPS, always. Never lowercase, never title case.
- Cap height 72px = 3.75% of frame height. In ASS/libass that is Fontsize 132
  for Bebas Neue (libass fits usWinAscent+usWinDescent to Fontsize, so Bebas's
  cap height = 0.538 x Fontsize).

SPACING
- Letter tracking: ASS Spacing 4 -> ~11px of air between letters.
- Word gap: 69px of ink-to-ink air, ~0.96 x cap height -- much wider than any
  font's own space. Reproduce with two hard spaces carrying extra tracking:
  {\fsp12}\h\h{\fsp4}
- Line pitch: 115px between cap tops (1.61 x cap height).

PLACEMENT
- Cap top of the FIRST line is pinned at y = 44.8% of frame height (861px at
  1920). Top-anchored: extra lines grow downward, line 1 never moves.
- Horizontally centred, then shifted 33px left of centre. Get this for free by
  emitting a TRAILING word separator on every line -- the renderer counts it
  when centring, which is exactly what the reference does.
- Max line width ~62% of frame width (670px at 1080) before wrapping.

COLOUR
- Idle word: #FFFFFF
- Word currently being spoken: #FFD500
- Outline: #000000 at 3px. Shadow: #000000, hard-edged (no blur), offset
  +4.5px right and down. In ASS: Outline 3, Shadow 4.5, BorderStyle 1.
- No box, no plate, no glow, no gradient.

MOTION -- there is none
- No pop, no scale-in, no fade, no drift. Captions cut in and out on one frame.
- The ONLY movement is the yellow: exactly one word is #FFD500 at a time, for
  exactly the interval it is spoken, then it reverts to white. Previous words
  do NOT stay highlighted. It is a travelling word, not a fill sweep.
- A group is on screen from its first word's start to its last word's end.
  Any blank frames between groups are just pauses in the audio -- do not add
  artificial gaps.
- A one-word group is yellow for its whole duration.

GROUPING
- Chunk words into groups of 3, restarting the count at every sentence end
  (so a trailing 1- or 2-word remainder before a full stop is its own group).
- If a group is wider than the max line width, break before the overflowing
  word. Never more than 2 lines.

EMPHASIS (use sparingly, roughly 1 group in 6)
- Occasionally render an ENTIRE group in #00FF40 green for its whole duration,
  with no travelling highlight inside it. Put it on the rhetorical turn -- the
  question, the reveal, the punchline. It is an emphasis colour, not a speaker
  colour: the same voice goes back to white/yellow immediately after.

TIMING SOURCE
- Word-level timestamps from ASR (WhisperX / whisper-timestamped). Use them
  raw -- do not quantise, smooth, or pad them.

If subtitles/brainrot_captions.py from this repo is available, use it:
  python3 subtitles/brainrot_captions.py words.json --video in.mp4 -o out.mp4 \
      --fontsdir /path/to/fonts --emphasis-words "then why do"
It already encodes every number above.
```

---

## Notes on using it

**Emphasis colour.** The reference gives no rule for which group turns green —
one group in six did, on the rhetorical pivot. Pick the group deliberately; the
generator takes `--emphasis-words "<phrase>"` (repeatable) or an
`"emphasis": true` flag on any word in the group.

**Other resolutions.** Every number above is a fraction of frame height or
width, so a 720×1280 clip wants `Fontsize 88`, cap top `y = 574`, line pitch
`77`, outline `2`, shadow `3`. The generator's `--play-w/--play-h` plus scaled
`--font-size/--cap-top/--line-pitch` cover it.

**Character-safe placement.** The caption sits just above centre because the
character in these clips stands in the lower third. If a clip frames its
subject higher, move the block rather than let it collide — but move the whole
block, keeping the top-anchored behaviour.
