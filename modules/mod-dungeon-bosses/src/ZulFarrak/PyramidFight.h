/*
 * mod-dungeon-bosses, Zul'Farrak D4a: the Pyramid's shared engine pieces (the Block, the Stair, the Altar). Skeleton
 * written by WP-S0; WP-D4a owns this file from now on (handoff section 3.5 row D4a: "PyramidFight.h (stage, Offerings,
 * Blood Price)"); D4b reads it and asks D4a (or, after D4a reports, the orchestrator) for changes.
 *
 * What already exists, in the instance and ZulFarrakKit.h: the stage machine (DATA_PYRAMID_STAGE / _RUNNING, START,
 * COMPLETE, FAIL), the stage directors (RegisterPyramidStage), the Offerings count (DATA_OFFERINGS: the instance adds
 * one per crew member lost on the Block, cap 4) and the Blood Price total (DATA_BLOOD_PRICE: the instance adds 30 per
 * crew member lost on the Block on heroic, the owners write the per-second ticks), both snapshot and restored on a
 * wipe. TODO(WP-D4a): the buffs that carry them on every Sandfury of the encounter (PY3, PY16), the Grievous Wound
 * watch that ticks the Blood Price, and whatever D4b shares with the Block.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_PYRAMID_FIGHT_H
#define MOD_DUNGEON_BOSSES_ZF_PYRAMID_FIGHT_H

#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"

namespace ZfPyramid
{
}

#endif
