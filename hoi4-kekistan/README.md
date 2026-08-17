# Kekistan — a Hearts of Iron IV mod

Renames Germany to Kekistan and gives it the Kekistan flag and a dark green
map colour. Purely cosmetic — politics, focus tree and AI are untouched, so
the game plays exactly like vanilla Germany.

![flag](tools/kekistan_flag.png)

## What it changes

| Thing | File |
| --- | --- |
| Flag (all sizes + every ideology variant) | `Kekistan/gfx/flags/**/GER*.tga` |
| Map / UI colour → dark green `40 90 40` | `Kekistan/common/countries/Germany.txt` |
| Country name → Kekistan | `Kekistan/localisation/english/kekistan_l_english.yml` |
| Ruling party name → *Kekistani Front* | `Kekistan/localisation/english/kekistan_l_english.yml` |

The country is called **Kekistan** — flat, with no formal variant. HOI4 keeps a
short name and a formal name (`_DEF`) per ideology, so it would normally read
"The Republic of …" or similar depending on the ruling party; every one of
those keys is set to plain Kekistan instead, so the name never changes shape.

The adjective (`_ADJ`) stays *Kekistani*, since that is what fills in phrases
like "Kekistani infantry" rather than a name in its own right.

## Politics

Nothing mechanical is changed. GER keeps its vanilla ruling party, leader,
focus tree and AI, because switching the ruling party away from fascism locks
off most of the German focus tree and stops the AI opening the war — it breaks
the game rather than reskinning it.

What *is* changed is the label: the ruling party reads **Kekistani Front**
instead of the vanilla party name. That is a localisation override, so it has
no effect on gameplay whatsoever.

`gfx/leaders/GER/Portrait_Kekistan_Ben_Shapiro.dds` is in the mod but nothing
references it yet — see the note below.

## Install

Copy `Kekistan/` **and** `Kekistan.mod` into your HOI4 mod folder:

* Windows — `%USERPROFILE%\Documents\Paradox Interactive\Hearts of Iron IV\mod\`
* Linux — `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/`
* macOS — `~/Documents/Paradox Interactive/Hearts of Iron IV/mod/`

You should end up with `.../mod/Kekistan.mod` and `.../mod/Kekistan/descriptor.mod`.
Launch HOI4, enable **Kekistan** in the launcher's playset, and start a game.

## Notes

* The party-name override assumes the loc key `GER_fascism_party`. If your
  build names it differently the label just stays vanilla — nothing breaks.
  Search the game's own localisation for the current party name to find the
  right key.
* The leader portrait is unused right now. Wiring it to the country leader
  means replacing the fascist leader, which is the Hitler slot; putting it on
  an advisor or a general instead leaves the leader alone and changes no
  mechanics.
* `common/countries/Germany.txt` is a whole-file override, so this conflicts
  with any other mod that changes Germany's colour or graphical culture. It is
  a three-line file — merge by hand if you need to.
* The flags are plain uncompressed 32-bit TGAs at HOI4's three sizes
  (82×52, 41×26, 10×7), one per ideology, cut from the artwork in
  `tools/kekistan_flag.png`.
* The portrait is an uncompressed 32-bit `.dds` at 156×210, the size and format
  vanilla character portraits use, so it is ready to drop into whichever slot
  it ends up in.
* `supported_version` is set to `1.16.*`.

## Regenerating the art

Both scripts read one source file, so swapping art means replacing that file
and re-running:

```sh
pip install pillow
python3 tools/generate_flags.py      # tools/kekistan_flag.png  -> 15 flag TGAs
python3 tools/generate_portrait.py   # tools/leader_portrait.png -> portrait DDS (unused)
```

Each crops to the target aspect before scaling rather than squeezing the art —
85px off the fly for the flag, 158px off the bottom for the portrait. The crop
is computed from the requested aspect, so replacement art of any size works.
