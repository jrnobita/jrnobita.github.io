-- =====================================================================
-- Fair Challenge AI - AI competence defines
-- =====================================================================
-- Every key below exists in vanilla common/defines/00_defines.lua.
-- The "vanilla:" comment records the stock value so every change here is
-- auditable and reversible.
--
-- DESIGN RULE: nothing in this file gives the AI a bonus. There are no
-- combat multipliers, no free resources, no cheaper equipment. These
-- values only change *what the AI chooses to do* with the same rules and
-- the same numbers the player plays under.
--
-- This is a partial override: assigning a key here replaces only that key,
-- everything else stays vanilla.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. ENGAGEMENT DISCIPLINE - when to attack, when to wait
-- ---------------------------------------------------------------------
-- The single largest weakness of the stock AI is throwing divisions at a
-- line at low organisation, losing the combat, and repeating. Org is what
-- actually wins land combats, so the AI is made to wait until its units
-- can land a real punch. LOW/MED/HIGH map to the plan aggressiveness
-- level, so all three tiers are raised in proportion.

NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_LOW = 0.90        -- vanilla: 0.85
NDefines.NAI.PLAN_ATTACK_MIN_STRENGTH_FACTOR_LOW = 0.65   -- vanilla: 0.60
NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_MED = 0.78        -- vanilla: 0.70
NDefines.NAI.PLAN_ATTACK_MIN_STRENGTH_FACTOR_MED = 0.56   -- vanilla: 0.50
NDefines.NAI.PLAN_ATTACK_MIN_ORG_FACTOR_HIGH = 0.55       -- vanilla: 0.45
NDefines.NAI.PLAN_ATTACK_MIN_STRENGTH_FACTOR_HIGH = 0.38  -- vanilla: 0.30

-- Wait for a meaningful planning bonus before kicking off an offensive
-- rather than jumping at the halfway mark.
NDefines.NAI.PLAN_AVG_PREPARATION_TO_EXECUTE = 0.68       -- vanilla: 0.50

-- Consider a front "ready" only when it has genuinely settled, so
-- offensives start with units in position instead of still marching.
NDefines.NAI.AI_FRONT_MOVEMENT_FACTOR_FOR_READY = 0.16    -- vanilla: 0.25

-- Commit more of the order before executing, and give up on a failing
-- push slightly sooner so units are recycled instead of ground down.
NDefines.NAI.PLAN_FACTION_STRONG_TO_EXECUTE = 0.58        -- vanilla: 0.50
NDefines.NAI.PLAN_FACTION_NORMAL_TO_EXECUTE = 0.70        -- vanilla: 0.65
NDefines.NAI.PLAN_FACTION_WEAK_TO_ABORT = 0.60            -- vanilla: 0.65

-- Naval invasions only launch with the org to survive the landing.
NDefines.NAI.MIN_INVASION_ORG_FACTOR_TO_EXECUTE = 0.82    -- vanilla: 0.75

-- ---------------------------------------------------------------------
-- 2. AGGRESSION CALIBRATION - picking careful vs balanced vs rush
-- ---------------------------------------------------------------------
-- These thresholds decide the stance the AI takes on a front based on the
-- strength balance. Vanilla goes aggressive too readily on even fronts and
-- stays aggressive while losing. Lowering CHECK_BASE lets it commit when it
-- genuinely holds an edge; raising CHECK_CAREFUL makes it drop to a careful
-- stance *earlier* when the balance turns against it - which is the
-- engine's nearest equivalent to "back off and hold a better line".

NDefines.NAI.AGGRESSIVENESS_CHECK_BASE = 1.35             -- vanilla: 1.5
NDefines.NAI.AGGRESSIVENESS_CHECK_CAREFUL = 0.85          -- vanilla: 0.6
NDefines.NAI.AGGRESSIVENESS_CHECK_EASY_TARGET = -0.45     -- vanilla: -0.3

-- Respect fortifications properly instead of grinding into forts.
NDefines.NAI.AGGRESSIVENESS_CHECK_PARTLY_FORTIFIED = 2.3              -- vanilla: 2.0
NDefines.NAI.AGGRESSIVENESS_CHECK_PARTLY_FORTIFIED_WEAK_POINTS = 0.9  -- vanilla: 0.75
NDefines.NAI.AGGRESSIVENESS_CHECK_FULLY_FORTIFIED = 12                -- vanilla: 10
NDefines.NAI.AGGRESSIVENESS_CHECK_FULLY_FORTIFIED_POCKET = 5          -- vanilla: 6

-- Require a real advantage before attacking a heavily defended front.
NDefines.NAI.ATTACK_HEAVILY_DEFENDED_LIMIT = 0.78         -- vanilla: 0.5

-- Weight fortification harder when scoring where to attack, so the AI
-- routes around the Maginot instead of into it.
NDefines.NAI.PLAN_VALUE_FORTIFICATION_LEVEL_MAX_PENALTY = -0.8  -- vanilla: -0.5
NDefines.NAI.FORT_LEVEL_TO_CONSIDER_HIGHLY_FORTIFIED = 1        -- vanilla: 1 (unchanged, documented)

-- ---------------------------------------------------------------------
-- 3. OPPORTUNISM AND MICRO
-- ---------------------------------------------------------------------
-- MAX_MICRO_ATTACKS_PER_ORDER is the engine's own opportunistic-attack
-- budget: vanilla comment reads "AI goes through its orders and checks if
-- there are situations to take advantage of". Raising it is the single
-- most direct lever available for better unit handling. It costs CPU per
-- order, so 8 is a deliberate balance rather than the maximum.

NDefines.NAI.MAX_MICRO_ATTACKS_PER_ORDER = 8              -- vanilla: 3
NDefines.NAI.MIN_PLAN_VALUE_TO_MICRO_INACTIVE = 0.15      -- vanilla: 0.25

-- Encirclements: look for them three times as often and act on larger
-- pockets, at a greater distance. This is what turns a pushed front into
-- an actual cauldron.
NDefines.NAI.HOURS_BETWEEN_ENCIRCLEMENT_DISCOVERY = 24    -- vanilla: 72
NDefines.NAI.MICRO_POCKET_SIZE = 8                        -- vanilla: 4
NDefines.NAI.POCKET_DISTANCE_MAX = 90000                  -- vanilla: 40000

-- Value entrenchment more when shuffling units, so the AI stops trading
-- away dug-in positions for marginal repositioning.
NDefines.NAI.ENTRENCHMENT_WEIGHT = 3.2                    -- vanilla: 2.0

-- ---------------------------------------------------------------------
-- 4. TERRAIN AWARENESS
-- ---------------------------------------------------------------------
-- These multiply the terrain-adjusted attack/defence modifiers when the AI
-- scores front provinces and assigns units. Raising them makes the AI far
-- more sensitive to *where* it fights - preferring to attack across plains
-- and hold in hills, mountains and marsh, and sending the right divisions
-- to the right tiles.

NDefines.NAI.FRONT_TERRAIN_ATTACK_FACTOR = 9.0            -- vanilla: 5.0
NDefines.NAI.FRONT_TERRAIN_DEFENSE_FACTOR = 7.0           -- vanilla: 3.75
NDefines.NAI.ASSIGN_FRONT_TERRAIN_ATTACK_FACTOR = 6.0     -- vanilla: 3.0
NDefines.NAI.ASSIGN_DEFENSE_TERRAIN_ATTACK_FACTOR = 1.2   -- vanilla: 0.5

-- Make battleplans less willing to path through hard terrain. Lower cost
-- limit = plans break when they hit mountains/marsh instead of drawing
-- arrows through them.
NDefines.NAI.PLAN_STEP_COST_LIMIT = 7                     -- vanilla: 9
NDefines.NAI.PLAN_STEP_COST_LIMIT_REDUCTION = 3           -- vanilla: 3 (unchanged, documented)

-- Weight the actual offensive stats of a division when assigning it to a
-- front, so attack divisions end up on attacking fronts.
NDefines.NAI.ASSIGN_FRONT_ARMY_SOFT_ATTACK_FACTOR = 0.30  -- vanilla: 0.1
NDefines.NAI.ASSIGN_FRONT_ARMY_HARD_ATTACK_FACTOR = 0.25  -- vanilla: 0.1

-- ---------------------------------------------------------------------
-- 5. SUPPLY AWARENESS
-- ---------------------------------------------------------------------
-- Post-NSB, supply is the main reason AI offensives collapse. The AI
-- overdeploys into regions it cannot feed, then fights at a large stat
-- penalty. These make it feel supply pain sooner and field fewer,
-- better-supplied divisions.

NDefines.NAI.FRONT_EVAL_UNIT_SUPPLY_AND_ORG_LACK_IMPACT = 2.1  -- vanilla: 1.0
NDefines.NAI.MAX_SUPPLY_DIVISOR = 2.1                          -- vanilla: 1.75
NDefines.NAI.AVERAGE_SUPPLY_USE_PESSIMISM = 1.75               -- vanilla: 1.5

-- Keep a real logistics buffer of trucks and trains rather than running
-- the network at the edge.
NDefines.NAI.DEFAULT_SUPPLY_TRUCK_BUFFER_RATIO = 2.0      -- vanilla: 1.5
NDefines.NAI.DEFAULT_SUPPLY_TRAIN_NEED_FACTOR = 1.5       -- vanilla: 1.2

-- Defend and target supply hubs more seriously.
NDefines.NAI.LAND_DEFENSE_SUPPLY_HUB_IMPORTANCE = 7       -- vanilla: 4
NDefines.NAI.STR_BOMB_SUPPLY_HUB_IMPORTANCE = 3           -- vanilla: 1

-- ---------------------------------------------------------------------
-- 6. AIR AND CAS AWARENESS
-- ---------------------------------------------------------------------
-- CAS and air superiority are undervalued by the stock AI's air priority
-- scoring. These raise the weight of contested land combat when the air
-- AI decides where to send wings, and increase CAS committed per combat.

NDefines.NAI.AIR_SUPERIORITY_FACTOR = 3.6                      -- vanilla: 2.5
NDefines.NAI.LAND_COMBAT_AIR_SUPERIORITY_IMPORTANCE = 0.95     -- vanilla: 0.40
NDefines.NAI.LAND_DEFENSE_AIR_SUPERIORITY_IMPORTANCE = 1.6     -- vanilla: 1.0
NDefines.NAI.LAND_COMBAT_OUR_COMBATS_AIR_IMPORTANCE = 210      -- vanilla: 155
NDefines.NAI.LAND_COMBAT_OUR_ARMIES_AIR_IMPORTANCE = 28        -- vanilla: 20
NDefines.NAI.LAND_COMBAT_CAS_PER_COMBAT = 85                   -- vanilla: 60
NDefines.NAI.LAND_COMBAT_CAS_PER_ENEMY_ARMY = 38               -- vanilla: 30

-- React to a changing air situation twice as fast.
NDefines.NAI.DAYS_BETWEEN_AIR_PRIORITIES_UPDATE = 2       -- vanilla: 4

-- Rebase more willingly to follow the fighting instead of sitting on a
-- partially covered region.
NDefines.NAI.AI_AIR_MISSION_COVERAGE_TO_STAY_PUT = 0.35   -- vanilla: 0.5

-- ---------------------------------------------------------------------
-- 7. FORCE QUALITY - equip what exists before building more
-- ---------------------------------------------------------------------
-- The stock AI floods the field with under-equipped divisions. Raising the
-- field strength floor makes it top up existing divisions first, which
-- raises average division quality without giving it a single free rifle.

NDefines.NAI.MIN_FIELD_STRENGTH_TO_BUILD_UNITS = 0.82     -- vanilla: 0.7

-- Keep a deeper reserve pool so combats get reinforced properly.
NDefines.NAI.RESERVE_TO_COMMITTED_BALANCE = 0.45          -- vanilla: 0.3

-- Don't send green divisions to the front.
NDefines.NAI.START_TRAINING_EQUIPMENT_LEVEL = 0.95        -- vanilla: 0.95 (unchanged, documented)
NDefines.NAI.STOP_TRAINING_EQUIPMENT_LEVEL = 0.90         -- vanilla: 0.90 (unchanged, documented)

-- ---------------------------------------------------------------------
-- 8. FRONT FOCUS
-- ---------------------------------------------------------------------
-- Concentrate force instead of smearing divisions evenly along every
-- border - schwerpunkt rather than cordon.

NDefines.NAI.MAIN_ENEMY_FRONT_IMPORTANCE = 5.5            -- vanilla: 4.0
NDefines.NAI.EASY_TARGET_FRONT_IMPORTANCE = 8.5           -- vanilla: 7.5

-- Slightly longer front sections so the AI plans in larger, more coherent
-- blocks rather than many small disconnected pushes.
NDefines.NAI.PLAN_FRONT_SECTION_MAX_LENGTH = 20           -- vanilla: 18
NDefines.NAI.PLAN_FRONT_SECTION_MIN_LENGTH = 11           -- vanilla: 10
