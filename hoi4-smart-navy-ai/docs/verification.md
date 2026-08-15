# What was verified, and how

HOI4 modding is full of confidently-repeated identifiers that do not exist. This
records where each fact in the mod came from, and — more usefully — which parts
are inference rather than verified fact.

Sources, in descending order of authority:

1. **Vanilla 1.14.1 game files.** `common/ai_strategy/*.txt`,
   `common/ai_equipment/*.txt`, `common/units/equipment/`,
   `common/defines/00_defines.lua`. Confirmed as 1.14.1 by its own changelog
   header, `Update 1.14.1 "Bolivar"`.
2. **The CWT schema** (`cwtools-hoi4-config`), which is the machine-readable
   grammar the community's language server validates against. Note it tracks a
   later version than the file corpus, so it is authoritative for "does this
   token exist" and weaker for "does this token exist *in 1.14*".
3. **Shipped mods** — Expert AI (`supported_version="1.15.1"`), Kaiserreich,
   Road to 56, Millennium Dawn, Pax Britannica Redux and others. A construct
   used by a mod with a large player base is a construct that loads.

---

## Verified against vanilla files

**The path for AI ship designs is `common/ai_equipment/`.** Not
`common/ai_equipment_design/`, which is a plausible-looking name that returns
zero results across all of GitHub. This mod was initially built with the wrong
folder name and corrected.

**`naval_avoid_region` takes a numeric strategic region; `area_priority` takes a
named `ai_area`.** Both appear in vanilla with their ids visible:

```
ai_strategy = { type = naval_avoid_region  id = 18  value = 600 }   # GER.txt
ai_strategy = { type = area_priority       id = scandinavia  value = -300 }  # ENG.txt
```

The CWT enums confirm the split — `strat_region_strats` contains
`naval_avoid_region`, `naval_convoy_raid_region`, `strategic_air_importance`,
`strike_force_home_base` and `naval_dominance`; `ai_area_id_strats` contains
`area_priority` and `naval_dominance`. A numeric id on `area_priority` is
silently dead, which is why the validator checks for exactly that.

**Region ids.** Vanilla comments its own naval regions, which is ground truth:

| id | vanilla comment | file |
| --- | --- | --- |
| 18 | `#english channel` | GER.txt |
| 16, 43 | `#around UK` | GER.txt |
| 9 | `#northern baltic` | ENG.txt |
| 206 | `#central baltic` | ENG.txt |
| 207 | `#danish belts` | ENG.txt |
| 173 | `#eastern north sea` | ENG.txt |
| 168 | `#adriatic` | ENG.txt |
| 69 | `#eastern med` | ENG.txt |
| 45 | `# norwegian sea` | ENG.txt |
| 61 | `# cape verde plain` | ENG.txt |
| 79 | `#sea of japan` | SOV.txt |

Ids not commented by vanilla were taken from the agreement of eight independent
shipped mods' `map/strategicregions/` filenames, and every one is recorded in
`tools/data/naval_regions.csv` with its confidence. Ids above 207 are excluded
unless vanilla itself references them, because total-conversion mods append
their own regions from there and the numbering stops being portable. Expert AI
independently uses 75, 78, 80, 91, 93, 95 and 105 as Pacific naval regions,
which corroborates the Pacific block.

**`naval_mission_threshold` is inverted.** Vanilla JAP.txt states the base
outright: `value = 150 #puts our threshold at 250`. So the base is 100, the
value is added, and a higher number makes the mission *less* likely. Getting
this backwards would invert the entire Japan file.

**Mission tokens.** `MISSION_CONVOY_ESCORT` appears in vanilla.
`MISSION_CONVOY_RAIDING`, `MISSION_PATROL`, `MISSION_STRIKE_FORCE`,
`MISSION_NAVAL_INVASION_SUPPORT`, `MISSION_MINES_PLANTING` and
`MISSION_MINES_SWEEPING` all appear in Expert AI. Every token the mod uses is in
one of those two sets.

**Fleet-comparison triggers**, from the CWT schema:

```
alias[trigger:naval_strength_ratio] = { tag = ... ratio = float }
alias[trigger:enemies_naval_strength_ratio] = float
alias[trigger:alliance_naval_strength_ratio] = float
```

`enemies_naval_strength_ratio` compares the scope country against all of its
enemies combined, which is what the doctrine actually wants.

**Intel triggers.**

```
### Compares estimated max armor based on intel.
alias[trigger:estimated_intel_max_armor] = { tag = ... value = float }
alias[trigger:estimated_intel_max_piercing] = { tag = ... value = float }
```

Used by vanilla in `GER_anti_armor` and `SOV.txt`, with this nesting, which the
mod copies verbatim:

```
any_enemy_country = {
    ROOT = { estimated_intel_max_armor = { tag = PREV  value > 25 } }
}
```

**Ship type tokens** for `has_navy_size` come from the `type` field on each
equipment archetype: `ship_hull_light` and `ship_hull_cruiser` are
`screen_ship`, `ship_hull_heavy` is `capital_ship`, plus `carrier` and
`submarine`.

**Module, hull and slot names** were extracted from the equipment files by
parsing them, not by typing them: 95 modules, 30 module categories, 62 hulls,
17 slot names, all in `tools/data/`.

**Piercing/armour damage bands** are the `NAVY_PIERCING_THRESHOLDS` and
`NAVY_PIERCING_THRESHOLD_DAMAGE_VALUES` arrays in `00_defines.lua`. Note that
`COMBAT_ARMOR_PIERCING_DAMAGE_REDUCTION` is `0` and marked deprecated in the
file — guides still quoting a flat −90% for failing to pierce are describing
pre-1.6 behaviour.

---

## Things that do not exist

Checked and absent from both vanilla and the CWT schema, despite appearing in
various guides and forum posts: `naval_convoy_escort_region`, `force_build_navy`,
`build_convoy`, `protect_shipping`, `raid_shipping`, `remove_ai_strategy`. There
is no region-scoped convoy *escort* strategy — only a region-scoped convoy
*raid* one. That asymmetry is why escort behaviour in this mod is expressed
through mission thresholds and production rather than through a map region.

---

## Inference, not fact

Three things in the mod are reasoned rather than verified. All three fail safe:
if the inference is wrong the mod does less than intended, not something wrong.

**1. Negative `naval_mission_threshold` values.** The direction is documented —
higher means less likely — and vanilla states the base is 100. It follows that a
negative value lowers the threshold below the base and makes the mission more
likely. But every observed use in vanilla and in Expert AI is positive, so a
negative value is an extrapolation from a stated rule rather than something seen
working. If the engine clamps at zero, the escort plans become no-ops and the
production side of those plans still applies.

**2. `any_enemy_country` and `estimated_intel_max_armor` inside an
`ai_equipment` design `enable` block.** The triggers are verified and the
documented scope for a design `enable` is the country, so this should hold. What
is not verified is that particular combination in that particular block —
vanilla only ever uses these triggers in `ai_strategy`. If it does not evaluate,
the design group is skipped and vanilla's designs are used, which is the current
behaviour anyway.

**3. `has_navy_size = { type = convoy }`.** `convoy` is a valid `unit_ratio` id
in vanilla and convoys are an equipment archetype, so `convoy` should be a valid
ship type token. It is used in one place — the raider submarine group's enable
condition — and if it is wrong, that group stays inert.

---

## The version gap

The file corpus available for verification was **1.14.1**. The current game is
**1.19.x**, and 1.19 included a naval rebalance — dual-purpose guns moved onto
the light gun branch as a 1939 tech, secondary battery techs folded into the
medium gun line, shell upgrades became intermediate techs, ship speeds came
down, and armour and piercing values were reviewed.

What that does and does not undermine:

- **Strategy types** are safe. They came from the CWT schema, which tracks
  ~1.19 (the config checkout's own dependency declares `1.19.2.*`).
- **Region ids** are safe. The consensus table was built from mods that declare
  `supported_version = "1.19.*"` alongside older ones, and the ids agree across
  both — this part of the API has been stable for years.
- **Module keys and stat values** are the exposure. They were read from 1.14.1
  equipment files. Attempts to corroborate them at 1.19 failed for a mundane
  reason: none of the mods in the corpus ship their own module files, because
  they inherit vanilla's, so there was nothing 1.19-era to compare against.

This is handled by `tools/refresh_tables.py`, which re-derives every table from
an installed copy of the game. That converts an unverifiable authoring-time
assumption into a check the user runs in one command against the exact version
they play. The tool was round-trip tested: pointed at a reconstructed game tree
it reproduced all six tables exactly and the mod validated clean against them.

Building it also caught a real bug in its own region classifier. Deciding
"is this a naval region" by whether *most* of its provinces are sea looks
careful and is wrong — the East China Sea is 13 sea provinces against 14
islands, and the Banda Sea 15 against 42, so both were classified as land and
the Japan and USA files failed validation against them. The correct rule is
"contains any sea province", which across a full 228-region map adds seven
regions and produces no land-region false positives.

---

## What could not be checked from here

Nothing in this mod was run inside Hearts of Iron IV. There was no game
installation available in the environment it was built in, so every claim about
*behaviour* — that the AI will weigh these priorities the way the doctrine
intends, that the counter designs will be chosen at the moment intended — is a
claim about the documented and observed semantics of these hooks, not an
observed outcome.

What can be said without hedging is narrower and still worth something: every
identifier exists, every file parses, every id points at something real, and the
mod as written cannot fail to load. The testing section of the README describes
what to watch for in game, and the Germany case is checkable in a single
observer run.
