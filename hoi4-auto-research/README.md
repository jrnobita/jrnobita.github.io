# Auto Research — Era Aware (Hearts of Iron IV)

Grants you one technology on a timer, and picks a technology that actually
belongs to the year you are in rather than blindly walking up a tier ladder.

## The one thing to know first

**HOI4 script cannot queue a technology into a research slot.** The engine
exposes `set_technology` (completes a tech instantly) and `add_tech_bonus`
(discounts a category), and nothing that means "start researching this."
There is no effect, trigger, or on_action for the research queue.

So this mod does not drive the research UI. It *grants* a tech every N days.
That is how every auto-research mod for this game works, and it is worth
knowing before you install it, because it means the mod is a supplement to
your research, not a replacement for it — your normal slots keep running
untouched alongside it.

Two related consequences:

- There is no trigger for "is a research slot idle", so the mod cannot detect
  that you have nothing queued. It works off a fixed interval instead.
- There is no wall-clock hook either. The finest tick a modder gets is one
  in-game day. At speed 5 a day is roughly a second, so the default interval
  of **5 days ≈ your 5 seconds**. Tune it in-game.

## The era-aware part

This is the behaviour you asked for. Each lane is a list of techs sorted by
year, and the picker takes the first entry that is both unresearched and not
ahead of the calendar. A tech that is out of era is skipped, not waited on.

Your example, playing it out — it is 1940 and Infantry Equipment III just
finished:

| candidate | year | result |
|---|---|---|
| `infantry_weapons3` | 1942 | skipped, two years out of reach |
| `support_weapons1` | 1939 | already researched |
| `artillery2` | 1941 | skipped |
| `construction3` | 1940 | **taken** |

So instead of stalling on a 1942 gun, it drops sideways onto the best thing
1940 actually offers. Set a focus and the same logic applies within your
preferred branch first — and if that branch has nothing in-era, it falls
through to the others rather than wasting the tick.

If the era is *genuinely* exhausted, the "Reach Into Future Techs" decision
lets it pull from a later year instead of idling. Off by default.

## Install

1. Copy this folder to `Documents/Paradox Interactive/Hearts of Iron IV/mod/auto_research`
2. Copy `auto_research.mod` up one level, into `mod/` itself
3. Enable it in the launcher

## In-game controls

Decisions tab → **Auto Research**:

- **Auto Research** — master on/off, and shows the running count of grants
- **Reach Into Future Techs** — allow pulling from later years when the era runs dry
- **Research Focus** — `0` balanced, `1` infantry, `2` artillery, `3` industry, `4` electronics
- **Research Faster / Slower** — adjust the interval

## Deliberate omissions

- **The AI does not get this.** Free techs on a timer for every nation would
  flatten the game. To change it anyway, delete the `limit = { is_ai = no }`
  line in `common/on_actions/zzz_auto_research.txt`.
- **No doctrines.** Doctrine branches are mutually exclusive choices, and
  `set_technology` ignores that restriction — the mod would happily hand you
  two incompatible doctrine paths. Pick those yourself. The same hazard applies
  to concentrated vs. dispersed industry, which is why those entries use
  `ar_try_x` with an explicit blocker.
- **No armour, air, or naval lanes enabled.** See below.

## Editing the tech tables

`common/scripted_effects/auto_research_lanes.txt`. Each line is
`ar_try = { TECH = <id> YEAR = <year> }`, sorted by year within a lane.

The `YEAR` value is *"when is this reasonable to own"*, not literally the
`start_year` from the vanilla files — raise it to make the mod hold off, lower
it to make it grab the tech sooner. Reorder lines to change preference within
a lane.

**Verify tech ids against your own install** at
`Hearts of Iron IV/common/technologies/` before adding lines. Ids move between
versions and DLC — No Step Back reworked armour into chassis techs, By Blood
Alone reworked aircraft into modules — which is exactly why the armour, air,
and naval lanes ship commented out rather than guessed at. The default lanes
stick to infantry, artillery, industry, and electronics, which are the most
stable ids across versions.

A line naming a tech that does not exist in your version fails quietly: the
game logs it and the line does nothing. If a lane seems to be skipping
something, check `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`
first — that is where a bad tech id or a broken parameter substitution shows up.

## What was tested

Brace balance and effect-resolution were checked mechanically across all six
script files, and the localisation file carries the UTF-8 BOM the game
requires. It has **not** been run in-game — I have no HOI4 install here — so
the tech ids and the `generic_research` decision icon are the two things to
confirm on first load via `error.log`.
