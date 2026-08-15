# Fair Challenge AI

A Hearts of Iron IV mod that makes the AI a harder opponent by making it
**play better**, not by giving it bonuses.

There are no combat multipliers, no free equipment, no research or
production bonuses, no manpower gifts, no supply exemptions. The AI fights
under exactly the rules and numbers you do. Every change either alters a
*decision threshold* or removes a bonus vanilla would otherwise hand out.

Target version: **HOI4 1.19.x**

---

## Install

1. Copy the `hoi4-fair-challenge-ai` folder into your HOI4 mod directory:
   - Linux: `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/`
   - Windows: `Documents\Paradox Interactive\Hearts of Iron IV\mod\`
   - macOS: `~/Documents/Paradox Interactive/Hearts of Iron IV/mod/`

2. Generate the no-cheat layer against your own game files:

   ```bash
   python3 tools/generate_no_cheat_modifiers.py
   ```

   If it cannot find your install, pass it explicitly:

   ```bash
   python3 tools/generate_no_cheat_modifiers.py --hoi4-dir "/path/to/Hearts of Iron IV"
   ```

3. Create a `.mod` file next to the folder so the launcher sees it, or add
   the folder through the launcher's "Add a mod" flow.

**Re-run step 2 after every game update.** See below for why this is a
script instead of a shipped file.

---

## Read this first: what this mod can and cannot do

You asked for an AI that micromanages its units well. I want to be
straight with you about where that is achievable and where it is not,
because the honest answer changes what this mod is.

**HOI4's tactical combat AI is compiled C++.** There is no scripting hook
for per-battle decisions. No mod can add a routine that says "this attack
is going badly, withdraw to the hills tile behind us and re-entrench."
That behaviour does not exist as a moddable system. Any mod claiming
otherwise is either changing something adjacent or giving the AI stat
bonuses and calling the result "better micro."

What *is* exposed is the layer above: the thresholds, weights and stance
selection that feed those hardcoded routines. That layer is genuinely
rich, and tuning it well produces an AI that holds better ground, commits
at better moments, and punishes mistakes harder. That is what this mod
does.

Here is each of your asks, mapped honestly:

| What you asked for | Status | How it is delivered |
|---|---|---|
| No cheating, no multipliers | **Fully achievable** | All AI bonus modifier blocks emptied; nothing added anywhere |
| When to engage vs. when to hold | **Largely achievable** | Situational `front_control` stance + raised org/strength attack thresholds |
| Terrain awareness | **Largely achievable** | Terrain attack/defence scoring weights roughly doubled; battleplans avoid hard terrain |
| Supply awareness | **Largely achievable** | Supply pain weighted 2.1×; fewer, better-fed divisions; logistics buffer |
| Air / CAS awareness | **Largely achievable** | Air priority weights raised; more CAS per combat; twice as responsive |
| Unit stat quality | **Partially** | AI equips existing divisions before building new ones |
| Micro their units well | **Partially — engine-limited** | Opportunistic-attack budget raised 3→8, encirclement scanning 3× more frequent, larger pockets pursued. This is real, but it is the engine's own opportunism budget, not true micro |
| Retreat to a better tile | **Engine-blocked** | No such routine exists to hook. The nearest available behaviour is dropping to a careful stance so the AI stops feeding units into losing attacks and lets them entrench |
| META division builds | **Deliberately not shipped by default** | See "On meta builds" below |

---

## The no-cheat layer

### What vanilla actually does

I checked this rather than assuming, and the popular claim that "the HOI4
AI always cheats" is **mostly wrong at default settings**. In vanilla
`common/modifiers/00_static_modifiers.txt`:

```
diff_normal_ai     = { no_supply_grace = 36 }
diff_normal_player = { no_supply_grace = 36 }
```

Identical. At default difficulty the AI gets nothing you do not get.

The real bonuses live in blocks that only apply when difficulty or the
per-country AI bonus sliders are raised. `diff_strong_ai_generic` — the
one behind the AI bonus slider — is substantial:

```
dig_in_speed_factor = 0.25          army_core_attack_factor = 0.15
planning_speed = 0.25               army_core_defence_factor = 0.15
supply_consumption_factor = -0.25   attrition = -0.075
army_morale_factor = 0.15           research_speed_factor = 0.1
production_factory_max_efficiency_factor = 0.15
experience_gain_army_factor = 0.25  ... and more
```

`diff_hard_ai` and `diff_very_hard_ai` add fuel discounts and supply
grace on top.

So the no-cheat guarantee here is not "undo something vanilla always
does" — it is **"the AI gets nothing extra no matter where the sliders
are."** You can crank AI difficulty to maximum and it will still fight
you on equal terms; the challenge comes only from playing better.

### Why this ships as a script

`00_static_modifiers.txt` has no partial-override mechanism — a mod file
with that name replaces the vanilla one wholesale. That file also holds
weather, resistance, intel, naval and a long tail of DLC-specific
modifier blocks, and Paradox adds to it every patch.

Shipping a pre-baked copy would silently delete every block added after
whatever version it was built from, breaking unrelated content. So the
mod ships a generator that patches **your** file at **your** version
instead. It brace-counts rather than regexes, backs up any previous
output, and reports any block it cannot find.

`diff_normal_ai` is deliberately left intact. Emptying it would leave the
AI with less supply grace than the player — cheating in the other
direction.

---

## What actually changed, and why

Full detail with vanilla values is in
`common/defines/zzz_fair_challenge_ai.lua`. The headline changes:

**Engagement discipline.** The stock AI's worst habit is attacking at low
organisation, losing, and repeating. Organisation is what wins land
combats, so the minimum org to attack rises across all three
aggressiveness tiers (e.g. `PLAN_ATTACK_MIN_ORG_FACTOR_HIGH` 0.45 → 0.55).
It attacks less often and hits considerably harder when it does.

**Stance selection.** `AGGRESSIVENESS_CHECK_CAREFUL` rises 0.6 → 0.85, so
the AI drops to a careful stance *earlier* when a front turns against it,
instead of grinding forward while losing. `AGGRESSIVENESS_CHECK_BASE`
falls 1.5 → 1.35 so it commits when it genuinely holds an edge. Net
effect: more decisive when winning, less self-destructive when losing.

**Opportunism.** `MAX_MICRO_ATTACKS_PER_ORDER` 3 → 8. Paradox's own
comment on this define reads *"AI goes through its orders and checks if
there are situations to take advantage of"* — it is the engine's
opportunistic-attack budget, and it is the most direct unit-handling
lever available. Encirclement scanning goes from every 72 hours to every
24, pocket size pursued from 4 to 8, and chase distance is more than
doubled. Expect to get punished for leaving a flank open.

**Terrain.** `FRONT_TERRAIN_ATTACK_FACTOR` 5.0 → 9.0 and the defensive
equivalent 3.75 → 7.0, plus a lower battleplan path cost through hard
terrain. The AI attacks across plains and holds hills, mountains and
marsh far more consistently.

**Supply.** `FRONT_EVAL_UNIT_SUPPLY_AND_ORG_LACK_IMPACT` 1.0 → 2.1 and
`MAX_SUPPLY_DIVISOR` 1.75 → 2.1. Post-NSB, the AI's offensives mostly die
to logistics, not enemy fire. It now fields fewer, better-supplied
divisions and feels supply strain sooner.

**Air.** Land combat weighting in air priority scoring roughly doubles,
CAS per combat 60 → 85, and the air AI re-evaluates every 2 days instead
of 4.

**Force quality.** `MIN_FIELD_STRENGTH_TO_BUILD_UNITS` 0.7 → 0.82, so the
AI tops up existing divisions before raising new ones — fewer paper
divisions, without a single free rifle.

---

## On meta builds

You asked for meta division templates, so here is what I found and why I
did not ship a template override.

I pulled the real terrain widths out of `common/terrain/00_terrain.txt`
rather than trusting forum lore, and they are **not** the 75/80/84/90
figures that circulate widely — those predate the No Step Back rework:

| Terrain | Combat width |
|---|---|
| Mountain, Marsh | 50 |
| Forest, Jungle | 60 |
| Plains, Hills, Desert | 70 |
| Urban | 80 |

Every one is divisible by 10, so a pure divisor analysis says 10-width
divisions waste zero width. That result is a mathematical artifact: it
ignores support-company cost, organisation, and commander bonuses, all of
which scale badly as divisions get smaller. Real 10w divisions are weak.

Vanilla's AI templates target widths of 17, 18 and 20. Against 50/60/70/80
that is already reasonable — 20 divides 60 and 80 exactly. The genuine
weakness in AI templates is composition and support companies, not width,
and improving that well needs campaign playtesting I cannot do from here.

So rewriting templates would have meant gambling with your game to look
more thorough. Instead the width analysis is documented above, and the
force-composition ideas live in `optional/force_composition/`, disabled,
with their risks written down. Turn them on if you want to experiment.

---

## Testing it works

Mod changes to AI behaviour are easy to *believe* and hard to *see*. To
actually verify:

1. **Confirm it loaded.** Launch with the mod active and open the console
   (`` ` ``). Run `reload defines`. Errors point at
   `common/defines/zzz_fair_challenge_ai.lua`.

2. **Check for script errors.** `Documents/Paradox Interactive/Hearts of
   Iron IV/logs/error.log` should contain no references to this mod's
   files. Unknown `ai_strategy` types show up here — this is the main way
   a silently-dead strategy reveals itself.

3. **Watch the AI think.** With the console open:
   - `debug_ai` / `aiview` — inspect AI strategy weights per country
   - `ai` — toggle AI on/off to isolate behaviour
   - `debug_air_vs_land` — air/CAS contribution
   - `tdebug` — tooltip debug info

4. **Behavioural smoke test.** Observe Germany vs. Poland in 1939 and
   France in 1940 without intervening. You should see fewer, larger,
   better-organised attacks and noticeably more encirclements than
   vanilla.

5. **Verify the no-cheat layer.** After running the generator, open
   `common/modifiers/00_static_modifiers.txt` and confirm
   `diff_strong_ai_generic` is empty. Then set the AI bonus slider to
   maximum in game setup — it should have no effect.

---

## Known risks and limits

- **Performance.** Raising `MAX_MICRO_ATTACKS_PER_ORDER` and shortening
  the encirclement scan interval both cost CPU per AI order. 8 and 24h
  are deliberately moderate, not maximal. If late-game speed 5 suffers,
  lower these two first.
- **Version fragility.** Define *names* are stable across patches, and an
  unknown key in a defines file is harmless. The static modifiers
  override is the version-sensitive part, which is exactly why it is
  generated rather than shipped.
- **Defines were read from a 1.14 mirror.** Names and vanilla values were
  verified against real game files, but from a 1.14-era mirror, since
  newer verbatim mirrors were not reachable. If a key was renamed in
  1.15–1.19 it will be silently ignored rather than break anything.
  Cross-check `error.log` after first load.
- **Not ironman/achievement compatible.** Like any mod that changes
  checksummed files.
- **The AI is still the AI.** It will still do things no competent player
  would. This mod narrows the gap; it does not close it.

---

## Sources

Everything here was verified against actual game files rather than
community summaries, because a misspelled define or a non-existent
`ai_strategy` type does not error in HOI4 — it silently does nothing.

- Paradox's shipped `common/ai_strategy/documentation.info` — authoritative
  strategy token list and `front_control` semantics
- Paradox's shipped `common/ai_templates/documentation.info`
- Vanilla `common/defines/00_defines.lua` — all define names and vanilla values
- Vanilla `common/terrain/00_terrain.txt` — terrain combat widths
- Vanilla `common/modifiers/00_static_modifiers.txt` — the `diff_*` blocks
- [CWTools HOI4 config](https://github.com/cwtools/cwtools-hoi4-config) —
  formal schema used to confirm token spellings and trigger signatures.
  This is what caught that the token is `research_weight_factor`, not
  `research_weight` as Paradox's own comment list abbreviates it.
