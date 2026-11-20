/*
 * mod-dungeon-bosses, Blackrock Depths D21: The Seven, the instance's half of the shared health pool (handoff section
 * 3.11 #4; STAGE-KT-D2-REPORT "Pool owner": the instance script is the safe home, since the seven ghosts' AIs all
 * reach it and none outlives it). WP-D21 owns this header; the instance (a shared file) holds the pool through it:
 *
 *     struct instance_blackrock_depths_rework_InstanceMapScript : public InstanceScript, public BrdTheSeven::PoolHost
 *     DungeonKit::SharedHealthPool _sevenPool{ BrdTheSeven::PoolSpec() };
 *     DungeonKit::SharedHealthPool& TheSevenPool() override { return _sevenPool; }
 *     ObjectGuid TheSevenGuid(std::size_t ghost) const override { return ghost < _seven.size() ? _seven[ghost] : {}; }
 *
 * The ghosts' AI (boss_the_seven_rework.cpp) fetches it with PoolOf(me->GetInstanceScript()) on every call (never a
 * cached pointer). Without the host (the instance not yet carrying it) PoolOf is null and the AI fights on with seven
 * separate health bars, logging "brd seven pool-missing" at every pull.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_THE_SEVEN_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRD_THE_SEVEN_FIGHT_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitPool.h"
#include "InstanceScript.h"
#include "ObjectGuid.h"
#include <cstddef>

namespace BrdTheSeven
{
    // What the instance script offers the Seven: the pool, and the seven ghosts' guids in the rotation order (the
    // instance's `_seven`, filled by OnCreatureCreate; BlackrockDepthsRework::kTheSeven).
    class PoolHost
    {
    public:
        virtual ~PoolHost() = default;
        virtual DungeonKit::SharedHealthPool& TheSevenPool() = 0;
        virtual ObjectGuid TheSevenGuid(std::size_t ghost) const = 0;
    };

    // The pool's spec: the size is the members' own max health (0: the first member's at Engage), every ghost's
    // template carrying the whole pool (320k normal by the_seven.py's HealthModifier, 450k heroic by WP-H's override:
    // TheSevenLogic.h kPoolHealth), so the frames read the pool's number and a tuning pass changes data only. Cleave
    // once per cast (KT-D2: 250 ms, DoTs one tick; section 7 #18), threat kept for merged hits, logs as "brd seven".
    inline DungeonKit::SharedHealthPoolSpec PoolSpec()
    {
        DungeonKit::SharedHealthPoolSpec spec;
        spec.maxHealth = 0;
        spec.castWindowMs = DungeonKit::kPoolCastWindowMs;
        spec.keepThreat = true;
        spec.dungeon = BlackrockDepthsRework::kLogDungeon;
        spec.boss = "seven";
        return spec;
    }

    // The host, when the instance carries it (a cross-cast: InstanceScript is polymorphic).
    inline PoolHost* HostOf(InstanceScript* instance)
    {
        return instance ? dynamic_cast<PoolHost*>(instance) : nullptr;
    }

    inline DungeonKit::SharedHealthPool* PoolOf(InstanceScript* instance)
    {
        PoolHost* host = HostOf(instance);
        return host ? &host->TheSevenPool() : nullptr;
    }
}

#endif
