# Optional: force composition tweaks

**These are OFF by default. Enable only if you want to experiment.**

To enable, copy `zzz_fair_ai_composition.txt` into
`../../common/ai_strategy/` and restart the game.

## Why these are not enabled by default

The rest of Fair Challenge AI changes *decision quality* — thresholds and
weights whose direction of effect is unambiguous. Waiting for more
organisation before attacking is better play at any industry level, for
every country.

Force composition is not like that. `role_ratio` shifts what the AI
*wants* to build, but whether that helps depends on industry, resources,
doctrine and theatre. Pushing every nation toward more armour helps
Germany and actively hurts Romania, which ends up with a handful of
under-equipped tank divisions instead of a working infantry line.

I could not playtest these across a campaign, so shipping them enabled
would be guessing with your game. They are here, documented, with the
reasoning visible — but the default build only contains changes I can
justify from the game files alone.

## What is in the file

| Strategy | Effect | Rationale |
|---|---|---|
| `role_ratio` / `armor` +15 | AI wants ~15% more armour divisions | Armour is what actually breaks fortified lines; the stock AI under-builds it relative to what a strong player fields |
| `role_ratio` / `infantry` -5 | Slightly fewer infantry divisions | Pays for the armour above without expanding total force beyond what supply can feed |
| `equipment_production_factor` / `fighter` +20 | More factories on fighters | Air superiority multiplies CAS effectiveness, and the AI chronically under-invests in fighters |

Values are read as "base 100 plus this", per Paradox's
`common/ai_strategy/documentation.info`. So `+15` means 115% of the
normally wanted amount.

## If you enable these, watch for

- **Minors fielding paper tank divisions.** If you see small nations with
  armour divisions stuck at low equipment, drop the armour value or
  restrict the strategy with an `enable` trigger on industry size, e.g.
  `num_of_factories > 40`.
- **Fighter production crowding out army equipment.** Lower the
  `equipment_production_factor` value first.
