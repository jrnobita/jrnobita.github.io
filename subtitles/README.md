# Brainrot karaoke captions

Reverse-engineered spec and generator for the caption style in the reference
clip: white ultra-condensed caps just above centre, black outline plus a hard
drop shadow, and exactly one word turning yellow as it is spoken.

| file | what it is |
|---|---|
| `STYLE.md` | the measured spec — font, spacing, placement, colour, motion, grouping |
| `PROMPT.md` | copy-paste prompt to hand to a future clip |
| `brainrot_captions.py` | word timings → `.ass`, or captions burned into a video |
| `fetch_font.sh` | downloads Bebas Neue into `fonts/` |
| `examples/reference_clip.json` | the reference clip's word timings, read frame by frame |
| `examples/reference_clip.ass` | what the generator emits for it |
| `examples/comparison.png` | nine frames, source vs regenerated |
| `examples/demo.mp4` | the regenerated captions on a flat background |

## Quick start

```sh
sh fetch_font.sh                        # -> fonts/BebasNeue.ttf
pip install fonttools brotli            # only if Google serves woff2

# transcribe with word-level timestamps
whisperx clip.mp4 --output_format json -o .

# caption it
python3 brainrot_captions.py clip.json \
    --video clip.mp4 -o clip_captioned.mp4 \
    --fontsdir fonts \
    --emphasis-words "then why do"
```

Drop `--video` to get just the `.ass`, which you can drag into CapCut, Premiere,
Resolve, or feed to `ffmpeg -vf subtitles=` yourself.

## Input

A JSON list of word-level timings — WhisperX and whisper-timestamped both emit
this shape directly:

```json
[{"word": "no", "start": 0.00, "end": 0.18}, ...]
```

Words are upper-cased automatically (`--no-upper` to keep the original casing).
Add `"emphasis": true` to any word to turn its whole group green, or use
`--emphasis-words "<phrase>"` on the command line.

## Tuning

Every measured constant is a flag: `--font`, `--font-size`, `--scale-x`,
`--spacing`, `--sep-spacing`, `--outline`, `--shadow`, `--cap-top`,
`--line-pitch`, `--center-x`, `--max-line-w`, `--words-per-group`,
`--color-idle`, `--color-active`, `--color-emphasis`, `--play-w`, `--play-h`.
Defaults are the reference clip's values at 1080×1920. `STYLE.md` explains what
each one was measured from, so you know what you are breaking when you change
it.

## Verification

Regenerating the reference clip and diffing all 118 frames against the source:
mean caption-edge error 2.35 px, median 2 px, max 7 px; wrap points, line
count, block centre and cap tops identical on every frame; group and highlight
boundaries identical on every frame but one (a one-frame glitch in the source
itself, not reproduced).
