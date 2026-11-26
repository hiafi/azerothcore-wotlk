/*
 * mod-dungeon-bosses, Zul'Farrak D7: the pool's hooks (engine side) for the hard mode packages. Skeleton written by
 * WP-S0; WP-D7 owns this file from now on (handoff section 3.1, 3.5 row D7) and finishes it before D7Ha and D7Hb start
 * (they never edit D7's .cpp; they share only this file).
 *
 * What already exists, in the instance: Gahz'rilla's summon at the gong (SetData(DATA_GONG_STRUCK, 1)), the hard mode
 * key (DATA_HARD_MODE_KEY, read at Velratha's pull for her 200,000), the flag (DATA_HARD_MODE, armed at the gong, held
 * for the lockout), its loot bit and kill slot 8, the pool wipe (slot 0 reopened after Gahz'rilla's wipe, the five crew
 * back as PoolAlly with ACTION_ZF_POOL_RESET). TODO(WP-D7): the per-pull hard mode objects and factories D7Ha (the crew
 * at the pool) and D7Hb (the Deluge) register (the TaragamanFight.h / DoanFight.h shape), the water field's handles
 * (KT's WaterField), the descriptor's extra entries.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_POOL_FIGHT_H
#define MOD_DUNGEON_BOSSES_ZF_POOL_FIGHT_H

#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"

namespace ZfPool
{
}

#endif
