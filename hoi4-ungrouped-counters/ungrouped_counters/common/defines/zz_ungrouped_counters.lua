-- =============================================================================
--  Ungrouped Counters - unit icons stay separate at every zoom level
-- =============================================================================
--
--  Vanilla HOI4 merges nearby unit counters into a single stacked "group"
--  counter once the camera pulls back past a set distance, and hides counters
--  entirely once you pull back far enough. This file pushes every one of those
--  thresholds past any distance the camera can actually reach, so each division,
--  fleet and air wing keeps its own counter no matter how far out you are.
--
--  HOW THIS FILE WORKS
--  HOI4 reads common/defines/ in alphabetical order and later assignments win,
--  so the "zz_" prefix guarantees this runs after the game's own 00_defines.lua
--  and 00_graphics.lua. Only the values below are changed - everything not
--  listed here keeps its vanilla value, so there is no need to copy the whole
--  vanilla file.
--
--  The base game's 00_graphics.lua ends with
--      for k,v in pairs( NDefines_Graphics ) do NDefines[k] = v end
--  which copies the table *reference*, not a clone. NDefines.NGraphics and
--  NDefines_Graphics.NGraphics are therefore the same table, and assigning
--  through NDefines (below) is enough to change a graphics define.
--
--  25000.0 is used throughout as "never". It is roughly an order of magnitude
--  beyond the furthest the in-game camera can pull back, so any check written
--  as "camera distance > threshold" simply never becomes true.
--
--  Vanilla values are noted on every line so you can dial any knob back.
--  See README.md for tuning presets.
-- =============================================================================


-- -----------------------------------------------------------------------------
--  1. Never merge counters into groups
-- -----------------------------------------------------------------------------

-- Camera distance at which counters begin to group up. This is the main one:
-- at vanilla 90.0 the merging starts almost as soon as you leave full zoom-in.
NDefines.NGraphics.MAP_ICONS_GROUP_CAM_DISTANCE = 25000.0                       -- vanilla 90.0

-- Second, coarser pass that groups counters together at the state level.
NDefines.NGraphics.MAP_ICONS_STATE_GROUP_CAM_DISTANCE = 25000.0                 -- vanilla 180.0

-- Third pass that groups counters together across a whole strategic region.
NDefines.NGraphics.MAP_ICONS_STRATEGIC_GROUP_CAM_DISTANCE = 25000.0             -- vanilla 350

-- Distance past which grouping gets coarse enough to merge *different unit
-- types* into one counter, i.e. where an armour and an infantry stack stop
-- being distinguishable.
NDefines.NGraphics.MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE = 25000.0         -- vanilla 350
NDefines.NGraphics.MAP_ICONS_COARSE_COUNTRY_GROUPING_DISTANCE_STRATEGIC = 25000.0 -- vanilla 350

-- Strategic areas of this size or bigger skip strategic-area grouping entirely.
-- Dropping it to 1 means every strategic area qualifies, which disables that
-- grouping pass regardless of the distance thresholds above.
NDefines.NGraphics.MAPICON_GROUP_STRATEGIC_SIZE = 1                             -- vanilla 1000

-- Upper bound on how many units you can have selected before the game stops
-- splitting icon stacks apart. Raised so that selecting a large army group
-- still shows you the individual counters.
NDefines.NGraphics.MAP_ICONS_GROUP_SPLIT_SELECTED_LIMIT = 1000                  -- vanilla 8


-- -----------------------------------------------------------------------------
--  2. Never hide the counters when zoomed out
-- -----------------------------------------------------------------------------

-- Camera distance past which on-map unit counters stop being drawn at all.
-- Without this, disabling the grouping above would just leave you with an empty
-- map at far zoom instead of merged counters.
NDefines.NGraphics.UNITS_ICONS_DISTANCE_CUTOFF = 25000.0                        -- vanilla 900


-- -----------------------------------------------------------------------------
--  3. Optional extras - commented out by default
-- -----------------------------------------------------------------------------
--  Uncomment any of these if you want them. They are left off so the mod only
--  does the one thing it says on the tin.

-- Keep movement arrows drawn at full zoom-out too. Pairs well with the rest if
-- you like watching offensives develop from a continent-wide view, but it does
-- add a lot of lines to the screen.
-- NDefines.NGraphics.UNIT_ARROW_DISTANCE_CUTOFF = 25000.0                      -- vanilla 1000

-- How many map icons get processed per frame for grouping. More = the map
-- settles faster after moving the camera, fewer = better performance. With
-- grouping disabled there is more per-frame icon work than vanilla expects, so
-- this is the first knob to *lower* if you lose FPS at max zoom-out.
-- NDefines.NGraphics.MAPICON_GROUP_PASSES = 20                                 -- vanilla 20

-- Max size in screen pixels of a merged group counter. Irrelevant while
-- grouping is off, listed here only so you know it exists.
-- NDefines.NGraphics.MAP_ICONS_GROUP_MAX_SIZE = 15                             -- vanilla 15

-- 3D unit models rather than counters. Raising this is a heavy performance hit
-- and is NOT what this mod is about - listed as a warning, not a suggestion.
-- NDefines.NGraphics.UNITS_DISTANCE_CUTOFF = 120                               -- vanilla 120
