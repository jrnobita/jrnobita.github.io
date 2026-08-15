# Smart Navy AI

A Hearts of Iron IV mod that makes the AI stop losing its navy in stupid ways.

It does two things. It tells each major power which water it can survive in and
which it cannot, and it makes ship design react to what intelligence actually
knows about the enemy fleet instead of following a fixed script.

Everything in it is script — no events, no flags, no periodic recalculation, no
save-game footprint. The AI strategy system already re-evaluates its `enable`
triggers on its own, so a declarative mod is both simpler and cheaper than one
that fires events at itself on a timer.

---

## The two problems

### 1. The AI sails into water it cannot survive

The clearest case is Germany and the English Channel. Vanilla does know about
this — `common/ai_strategy/GER.txt` ships a plan called
`axis_stay_away_from_the_royal_navy` that avoids region 18 (English Channel) at
weight 600, and regions 16 and 43 at weight 100. The idea is right. The gating
is what fails:

```
enable = {
    date < 1942.1.1
    OR = {
        GER = { naval_strength_ratio = { tag = ENG ratio < 0.5 } }
        ... thirteen divisions_in_state checks ...
    }
}
abort_when_not_enabled = yes
```

Two switches turn it off exactly when it is still needed.

- **The date cap.** On 1 January 1942 the plan aborts and never comes back.
  Every convoy Germany routes after that date is routed with no penalty on the
  Channel or the Western Approaches — which is where the Royal Navy and its
  submarines are for the rest of the game.
- **The strength ratio.** It only holds while the Kriegsmarine is under *half*
  the Royal Navy. An AI on a production bonus, or a Germany that went down the
  naval focus tree, crosses 0.5, the plan aborts, and the fleet walks into the
  Home Fleet.

It is also incomplete: 16 and 43 at weight 100 are a preference, not a refusal,
next to the 600 used for the Channel itself.

Japan is worse. Vanilla `JAP.txt` contains exactly **one** naval mission
strategy in the entire file — `jap_conserve_fuel_for_usa_fight`, which raises
the convoy escort threshold so Japan escorts *less* before 1941. That is
defensible on its own terms, and this mod leaves it alone, because nobody is
raiding Japan in 1940. The problem is that it aborts on war with the United
States and nothing replaces it. At the moment the largest submarine campaign of
the war opens against the one sea lane Japan cannot live without, Japan's
scripted naval priorities are empty.

### 2. The AI builds ships that cannot hurt what it is fighting

Naval gunnery resolves through a piercing-to-armour ratio read out of
`common/defines/00_defines.lua`:

| piercing / armour | damage | crit |
| --- | --- | --- |
| ≥ 2.00 | 1.00 | 2.00 |
| 1.00 – 1.99 | 1.00 | 1.00 |
| 0.75 – 0.99 | 0.70 | 0.75 |
| 0.50 – 0.74 | 0.40 | 0.50 |
| 0.10 – 0.49 | 0.30 | 0.10 |
| < 0.10 | 0.10 | 0.00 |

Against the module values in `common/units/equipment/modules/`:

| battery | piercing | | armour module | armour |
| --- | --- | --- | --- | --- |
| `ship_light_battery_1..4` | 1.0 – 2.5 | | `ship_armor_cruiser_1..4` | 6 – 12 |
| `ship_light_medium_battery_1..4` | 5.5 – 9.0 | | `ship_armor_bc_1..3` | 22 – 34 |
| `ship_medium_battery_1..4` | 22 – 34 | | `ship_armor_bb_1..3` | 30 – 40 |
| `ship_heavy_battery_1..4` | 31 – 45 | | `ship_armor_shbb` | 55 |
| `ship_super_heavy_battery_1` | 45 | | | |

Three things fall out of those two tables, and they drive every design in the
mod:

- **Light attack cannot hurt armour.** The best light battery pierces 2.5.
  Against the thinnest cruiser belt that is 0.42 — the 0.30 band. Against a
  battleship it is 0.08 — the 0.10 band. Light attack is for killing unarmoured
  screens, and it is superb at that, but a light-attack fleet cannot sink a
  capital ship.
- **The gun ladder stops at 45 piercing, and super-heavy armour is 55.**
  Nothing in the game reaches ratio 1.0 against it; the best case is 0.82, the
  0.70 band. So against a super-heavy enemy the answer is not a bigger gun —
  there isn't one. It is torpedoes, which skip the piercing table entirely.
- **Armour is bought in bands.** To drop an enemy from 1.00 to 0.70 you need
  armour above their piercing; to reach 0.40, above `piercing / 0.75`; to reach
  0.30, above `piercing / 0.5`. Tonnage spent between those points buys nothing.

The mod reads the enemy's numbers through `estimated_intel_max_armor` and
`estimated_intel_max_piercing`, which report armour and piercing **as estimated
from intelligence**. A country with no intel network sees nothing and keeps
building what it was building. A country that has done the intelligence work
designs against the real fleet. Vanilla already uses this idiom — but only for
tanks, in `GER_anti_armor`. Never for ships.

---

## What it changes

### Every country (`common/ai_strategy/snai_00_doctrine.txt`)

| Plan | Fires when | Effect |
| --- | --- | --- |
| `snai_screens_before_capitals` | more than 3 capitals | shifts production toward screens; an unscreened capital dies to destroyers it cannot hit back |
| `snai_answer_the_submarine_campaign` | an enemy has more than 25 submarines | escorts, convoys, and a much lower convoy-escort threshold |
| `snai_weaker_fleet_does_not_seek_battle` | `enemies_naval_strength_ratio < 0.4` | stops hunting, starts raiding — the one mission where being outnumbered costs little |
| `snai_stronger_fleet_presses` | ratio above 2 | forces engagements and covers invasions instead of sitting in port |
| `snai_answer_the_carriers` | an enemy has more than 2 carriers | light cruisers and carriers, because there is no gun answer to an air wing |

### Germany (`snai_10_germany.txt`)

Channel, Western Approaches, North Sea and Denmark Strait avoided on the naval
balance alone, with no date cap — and released if Germany genuinely builds a
fleet that can win, which vanilla's 0.5 cut-off never allows for. The Baltic is
treated as what it is, the iron ore lifeline, and is never given an avoidance
anywhere in the mod. Raiders are pointed at the mid-Atlantic gaps, away from the
escort concentration. Biscay opens up once France falls; the Norwegian coast
becomes a base once Norway does.

### Japan (`snai_11_japan.txt`)

The oil lane is treated as the war: escort priority pushed hard, escorts and
convoys built, and the strike force based on the South China Sea instead of the
central Pacific. Hawaii, Midway and the north Pacific are refused while Japan is
outmatched — Expert AI reaches the same conclusion independently, which is a
useful check that the region ids and the judgement are both right. Once the
carriers are below four, the fleet stops hunting and covers the lane.

### Britain, USA, Italy, USSR, France (`snai_12_other_majors.txt`)

Same idea, different geography. Britain escorts the Atlantic and bases on the
Western Approaches. The USA runs the submarine campaign against Japanese
shipping that the AI almost never runs, and waits for carriers before entering
the Sea of Japan. Italy escorts the Libya run from the Sicily narrows and
declines the general action. The Soviet fleet stays in the Baltic and Black Sea
where it is at least a coastal defence. France covers the Mediterranean.

### Ship designs (`common/ai_equipment/snai_counter_designs.txt`)

Five design groups, each inert unless its condition holds — they sit at priority
1200 with a modifier that zeroes them, so a group is either the best answer
available or not in the running at all. Capital designs that answer armour, guns
or both; a torpedo destroyer for armour no gun can reach; an ASW escort; a light
cruiser in either screen-killer or anti-air trim; a raider submarine.

---

## What it deliberately does not do

Being straight about the ceiling, because a lot of "AI overhaul" mods are not:

- **It cannot assign missions to individual task forces.** There is no scripted
  hook for that. `naval_mission_threshold` shifts how willing the AI is to run a
  mission type; it does not order a specific fleet anywhere.
- **It cannot route convoys.** Convoy pathing is engine-side. What it can do is
  make the AI escort, build escorts, and keep its warships out of the water where
  its convoys are being killed.
- **It does not touch defines or combat maths.** No stat buffs, no `is_ai = yes`
  bonuses. Everything is a priority the AI was already weighing.
- **It does not control the player's navy.** Nothing in HOI4 can.
- **`naval_dominance` is not used.** It exists in 1.15+ and not in 1.14, and the
  mod prefers to degrade gracefully over pinning to one patch.

---

## Install

```
Documents/Paradox Interactive/Hearts of Iron IV/
├── mod/
│   ├── smart_navy_ai.mod        <- copy of the file in this folder
│   └── smart_navy_ai/           <- everything else in this folder
│       ├── descriptor.mod
│       └── common/
```

The `.mod` file in `mod/` carries `path`; the `descriptor.mod` inside the folder
does not. On Linux the root is `~/.local/share/Paradox Interactive/Hearts of Iron IV/`.

`supported_version` is set to `1.19.*`, the current branch.

### Read this if you care about the ship designs

The mod was authored against vanilla **1.14.1** files, because that is the
corpus that was available to verify identifiers against. Since then, 1.19
shipped a naval rebalance: dual-purpose guns moved onto the light gun branch as
a 1939 tech, secondary battery techs folded into the medium gun line, shell
upgrades became intermediate techs, and ship speeds came down. Armour and
piercing values were part of that review.

That splits the mod cleanly in two.

- **The doctrine half is version-robust.** Strategy type names come from the CWT
  schema, which tracks ~1.19. Region ids are corroborated by mods that declare
  `supported_version = "1.19.*"` and later. Region ids and strategy tokens are
  the stable part of this API.
- **The design half is dated.** The piercing and armour numbers quoted above are
  1.14.1 numbers. The *shape* of the argument does not change — the piercing
  bands are engine behaviour, and "light attack cannot hurt armour" follows from
  any plausible set of values — but a specific threshold like "armour above 36"
  is calibrated against a table that may have moved.

If a module key was renamed, the affected design group simply never matches and
vanilla's designs are used. The mod still loads and the doctrine still works.

To check this against *your* game rather than trusting the above:

```
python3 tools/refresh_tables.py --game-dir "/path/to/Hearts of Iron IV"
python3 tools/validate.py --strict
```

`refresh_tables.py` re-derives every table — modules, hulls, slots, strategy
types, ai_areas, roles, and the naval region list — from your installation's own
files, reading `map/definition.csv` to work out which strategic regions are sea
zones. Anything this mod references that your version renamed becomes an error
instead of a design that silently never matches. It writes nothing unless every
table extracted cleanly, so a wrong path is harmless.

---

## Checking it

HOI4 fails silently. A misspelled strategy type, a region id that does not
exist, or a module name that was renamed all give you a mod that loads, runs,
and does nothing — and the only symptom is an ordinary game where the AI still
sails into the Channel.

```
python3 tools/validate.py --strict
python3 tools/test_pdxscript.py
```

`tools/pdxscript.py` is a strict Clausewitz parser with line-accurate errors.
`tools/validate.py` checks brace balance, every `ai_strategy` type against the
CWT schema enums, every numeric region id against `tools/data/naval_regions.csv`,
every hull, module, slot and role against the real equipment files, plus event
namespaces and localisation encoding for when the mod grows.

It earns its keep: it caught `dp_ship_secondaries` (the module is
`dp_ship_secondaries_1`, but the *category* you reference in a design is
`ship_dp_secondaries`) before the mod was ever loaded.

The distinction it cares most about is that `naval_avoid_region` takes a numeric
strategic region while `area_priority` takes a **named** `ai_area` from
`common/ai_areas/`. Mixing them up produces a strategy that is silently dead,
and both mistakes are easy to make.

## In game

Launch with `-debug`, `tag` to the country you want to watch, and let it run.
Check `error.log` first — a rejected file shows up there and nowhere else. The
Germany case is visible without any tooling: start a 1936 game as an observer,
run to 1943, and watch whether the Kriegsmarine and its convoys are still using
the Channel.

## Compatibility

Additive. It adds new files under `common/ai_strategy/` and
`common/ai_equipment/` and overwrites nothing, so it stacks with vanilla rather
than replacing it — the values are written as deltas on vanilla's own scale for
that reason.

It will conflict with any mod that uses `replace_path` on either folder.
Kaiserreich does this for `common/ai_equipment`. Expert AI adds files the same
way this mod does, so the two load together; their region avoidances stack,
which for Japan means the shared conclusions get firmer rather than doubled up
incoherently.

## Provenance

`docs/verification.md` records what was checked against what, and which two
claims in the mod are inference rather than verified fact.
