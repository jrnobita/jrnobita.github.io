# Ungrouped Counters

A small Hearts of Iron IV mod that stops unit counters from merging into stacked
group icons when you zoom out. Every division, fleet and air wing keeps its own
counter at every zoom level, all the way out to a continent-wide view.

No new art, no UI replacement, no gameplay changes — it only retunes the
graphics defines that control counter grouping and counter draw distance.

---

## What it actually changes

Vanilla HOI4 runs three successive grouping passes as the camera pulls back, and
then hides counters entirely past a cutoff. This mod pushes all of those
thresholds to `25000.0`, roughly an order of magnitude beyond the furthest the
in-game camera can reach, so the checks never fire.

| Define (`NDefines.NGraphics.…`) | Vanilla | Here | What it controls |
| --- | --- | --- | --- |
| `MAP_ICONS_GROUP_CAM_DISTANCE` | `90.0` | `25000.0` | Camera distance where counters start grouping. The main one. |
| `MAP_ICONS_STATE_GROUP_CAM_DISTANCE` | `180.0` | `25000.0` | Second pass — grouping at state level. |
| `MAP_ICONS_STRATEGIC_GROUP_CAM_DISTANCE` | `350` | `25000.0` | Third pass — grouping across a strategic region. |
| `MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE` | `350` | `25000.0` | Distance where grouping gets coarse enough to merge *different unit types* together. |
| `MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE_STRATEGIC` | `350` | `25000.0` | Same, for strategic map modes. |
| `MAPICON_GROUP_STRATEGIC_SIZE` | `1000` | `1` | Strategic areas this size or bigger skip strategic grouping. At `1`, every area qualifies. |
| `MAP_ICONS_GROUP_SPLIT_SELECTED_LIMIT` | `8` | `1000` | How many units you can have selected before stacks stop splitting apart. |
| `UNITS_ICONS_DISTANCE_CUTOFF` | `900` | `25000.0` | Camera distance past which counters stop being drawn at all. |

That last row matters as much as the grouping ones: without it, switching
grouping off would just give you an empty map at far zoom instead of merged
counters.

Everything lives in one file —
[`ungrouped_counters/common/defines/zz_ungrouped_counters.lua`](ungrouped_counters/common/defines/zz_ungrouped_counters.lua).
The `zz_` prefix matters: HOI4 reads `common/defines/` alphabetically and later
assignments win, so this has to sort after the game's own `00_defines.lua` and
`00_graphics.lua`. Only the listed values are assigned; everything else keeps its
vanilla value, so there's no need to copy the whole vanilla file.

---

## Get it onto your PC

Everything here lives in this repo on the branch
`claude/hoi4-zoomed-out-icons-fs7qbp`, so it survives independently of any chat
session. Three ways to pull it down, easiest first.

**1. Direct zip download** — already laid out in the folder structure HOI4
expects, so it's just "unzip into the mod folder":

```
https://github.com/jrnobita/jrnobita.github.io/raw/refs/heads/claude/hoi4-zoomed-out-icons-fs7qbp/hoi4-ungrouped-counters/ungrouped_counters.zip
```

**2. Clone the branch** in a fresh terminal or Claude Code session:

```bash
git clone https://github.com/jrnobita/jrnobita.github.io.git
cd jrnobita.github.io
git checkout claude/hoi4-zoomed-out-icons-fs7qbp
cd hoi4-ungrouped-counters
```

If you already have the repo cloned, just fetch the branch:

```bash
git fetch origin claude/hoi4-zoomed-out-icons-fs7qbp
git checkout claude/hoi4-zoomed-out-icons-fs7qbp
```

**3. Copy straight into the game folder** (Windows, from Git Bash or WSL) once
you have the repo cloned:

```bash
cp -r hoi4-ungrouped-counters/ungrouped_counters.mod \
      hoi4-ungrouped-counters/ungrouped_counters \
      "$USERPROFILE/Documents/Paradox Interactive/Hearts of Iron IV/mod/"
```

---

## Install

The mod folder lives in your HOI4 **user data** directory, not the Steam install
directory:

| OS | Path |
| --- | --- |
| Windows | `Documents\Paradox Interactive\Hearts of Iron IV\mod\` |
| macOS | `~/Documents/Paradox Interactive/Hearts of Iron IV/mod/` |
| Linux | `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/` |

Copy **both** items from this folder into that `mod/` directory:

```
mod/
├── ungrouped_counters.mod          ← the launcher reads this
└── ungrouped_counters/
    ├── descriptor.mod
    └── common/
        └── defines/
            └── zz_ungrouped_counters.lua
```

Then open the HOI4 launcher → **All installed mods** → tick **Ungrouped
Counters** → add it to a playset → Play.

If it doesn't appear in the launcher, the usual cause is the outer `.mod` file
being in the wrong place or its `path=` line not matching the folder name. Both
files here already agree on `mod/ungrouped_counters`, so keep the folder name as
is or change it in three places at once.

---

## Verify it's working

Zoom out until the whole of Europe is on screen. In vanilla you'd see a handful
of merged counters with unit-count numbers on them; with this on you should see
one counter per division, densely packed along the front.

If nothing changed, check that the define names still match your game version —
Paradox does occasionally rename these. Open

```
<Steam>\steamapps\common\Hearts of Iron IV\common\defines\00_graphics.lua
```

and search for `MAP_ICONS_`. Every name in the table above should be present. If
one has been renamed, update the matching line in the mod's `.lua` and it'll work
again. The vanilla values quoted above are the ones shipped in the game's own
`00_graphics.lua`; if yours differ, yours are authoritative.

---

## Tuning

The mod ships fully aggressive — grouping off at *every* distance. If that's too
busy at maximum zoom-out, edit the `.lua` and use one of these instead. The file
has the vanilla value in a comment on every line.

**Middle ground** — individual counters through normal play, grouping only at
extreme zoom-out:

```lua
NDefines.NGraphics.MAP_ICONS_GROUP_CAM_DISTANCE = 600.0
NDefines.NGraphics.MAP_ICONS_STATE_GROUP_CAM_DISTANCE = 700.0
NDefines.NGraphics.MAP_ICONS_STRATEGIC_GROUP_CAM_DISTANCE = 800.0
NDefines.NGraphics.MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE = 800.0
NDefines.NGraphics.MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE_STRATEGIC = 800.0
```

**Keep types distinct but allow same-type stacking** — leave the first three
thresholds at vanilla and only raise the two `COARSE` ones, so armour never gets
merged into an infantry counter.

There are also three optional extras commented out at the bottom of the `.lua`:
movement arrows at full zoom-out, the per-frame icon processing budget, and the
3D-model cutoff.

---

## Caveats

**Ironman achievements will be off.** HOI4 decides achievement and multiplayer
compatibility from a checksum, and the game's `checksum_manifest.txt` includes
the entire `common/` folder — which is where defines live. Any mod that touches
defines changes the checksum. There's no way to do this as an
achievement-compatible mod, because there's no non-`common/` place to put the
change.

**Multiplayer needs everyone on it.** Same checksum rule: you can only join a
host whose checksum matches yours, so every player needs the mod enabled.

**Expect an FPS cost at far zoom.** You're asking the game to draw hundreds or
thousands of individual counters where it normally draws a few dozen merged ones.
Late-game 1944 Eastern Front at full zoom-out is the worst case. If it bites, the
"middle ground" preset above is the fix.

**Save-safe.** Defines are read at load, not baked into saves, so you can enable
or disable this on an existing save with no corruption — though you can't load an
Ironman save with a different checksum than it was made with.

---

## Not yet tested in-game

This was written against the game's define files rather than by running it, since
the machine it was built on has no HOI4 install. The define names, vanilla values
and file structure are taken from HOI4's own `common/defines/00_graphics.lua` and
from working mod descriptors, but the first person to actually launch it will be
you. The verification section above is there for exactly that reason.
