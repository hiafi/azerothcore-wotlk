/*
 * mod-dungeon-bosses, Blackrock Spire B5: the Stolen Magic shard and the Stolen Power stacks, the engine side that Urok
 * (boss_urok_doomhowl_rework.cpp, UR3 / UR5 / UR9) and Wyrmthalak's hard mode (B9, WT10 "Stolen Boulders": the shards
 * crawl to the Spirestone Champion, 5 stacks overcharge) share. Header only; the ids and numbers are UrokLogic.h's.
 *
 * Use from B8 / B9:
 *
 *     #include "UrokShards.h"
 *     DungeonKit::CrawlPickups _shards;                   // an AI member: Update from UpdateAI, Clear on reset/death
 *     // a boulder landed: a shard at its center, no buff, crawling to the champion after 10 s
 *     DungeonKit::CrawlPickupSpec spec = BrsStolenMagic::ShardSpec(10s, TAG_WT_SHARD);
 *     spec.onReach = [guid = champion->GetGUID(), map = me->GetMap()](ObjectGuid, Position const&)
 *     {
 *         if (Creature* c = map->GetCreature(guid))
 *             if (BrsStolenMagic::AddStolenPower(c, 5) >= 5)
 *                 ...;                                    // the champion's 3 s cast, then BrsStolenMagic::Overcharge
 *     };
 *     _shards.Add(me, spot, std::move(spec), { champion->GetGUID(), std::nullopt });
 *
 * The shard is creature 300706 (NPC_BRS_STOLEN_MAGIC_SHARD: Power Spark display 26753, a passive helper; its AI
 * npc_brs_stolen_magic_shard is registered by AddSC_boss_urok_doomhowl_rework); the spells are SPELL_UR_STOLEN_POWER
 * (210151), SPELL_UR_SHARD_RECLAIM (210152), SPELL_UR_OVERCHARGE_CAST (210160), SPELL_UR_OVERCHARGE (210161) and
 * SPELL_UR_OVERCHARGE_LOOK (210162), declared in apps/dbc-tools source/npcs/blackrock_spire/urok.py.
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_UROK_SHARDS_H
#define MOD_DUNGEON_BOSSES_BRS_UROK_SHARDS_H

#include "BossMechanics.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFields.h"
#include "Duration.h"
#include "Map.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "SharedDefines.h"
#include "UrokLogic.h"

namespace BrsStolenMagic
{
    // A Stolen Magic shard: taken on touch (2 yd), it lies still for `wait`, then crawls at 3 yd/s to its goal (still
    // taken on the way). Everyone may take it; narrow `who` for a stack rule (Urok's heroic Unstable). Add onPick /
    // onReach to it, then CrawlPickups::Add.
    inline DungeonKit::CrawlPickupSpec ShardSpec(Milliseconds wait, uint32 tag)
    {
        DungeonKit::CrawlPickupSpec spec;
        spec.entry = BlackrockSpireRework::NPC_BRS_STOLEN_MAGIC_SHARD;
        spec.radius = BrsUrok::kShardRadiusYd;
        spec.wait = wait;
        spec.crawl = true;
        spec.crawlSpeed = BrsUrok::kShardCrawlYdPerSec;
        spec.reach = BrsUrok::kShardReachYd;
        spec.count = 1;
        spec.oneClaimPerBot = true;
        spec.tag = tag;
        return spec;
    }

    // A shard reached `holder`: one Stolen Power stack (held at `cap`), with the reclaim look. Returns the new count.
    inline uint32 AddStolenPower(Creature* holder, uint32 cap)
    {
        if (!holder || !holder->IsAlive())
            return 0;
        uint32 const after = DungeonKit::AddStacks(holder, BrsUrok::SPELL_UR_STOLEN_POWER, 1, holder, cap);
        holder->CastSpell(holder, BrsUrok::SPELL_UR_SHARD_RECLAIM, true);
        return after;
    }

    // Every living player within `range` of `from` (game masters left out).
    inline GuidSet PlayersNear(WorldObject const* from, float range)
    {
        GuidSet out;
        if (!from || !from->IsInWorld())
            return out;
        for (auto const& ref : from->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && !player->IsGameMaster() && player->IsWithinDistInMap(from, range))
                out.insert(player->GetGUID());
        }
        return out;
    }

    // The nearest of those (nullptr: nobody).
    inline Player* NearestPlayer(WorldObject const* from, float range)
    {
        Player* best = nullptr;
        float bestDist = range;
        if (!from || !from->IsInWorld())
            return nullptr;
        for (auto const& ref : from->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster())
                continue;
            float const dist = from->GetDistance(player);
            if (dist <= bestDist)
            {
                best = player;
                bestDist = dist;
            }
        }
        return best;
    }

    // The backfire (UR9; WT10's champion): `pct` percent of the reference row to every living player within `range`
    // of `owner` (no Weakened, through the registry: the ledger and the bots' healers see it), the nova's look, and
    // the Stolen Power stacks gone. Start it with DungeonKit::CastBar(owner, SPELL_UR_OVERCHARGE_CAST, ...) 3 s
    // before (kOverchargeCastMs). Returns the hit (invalid: nobody in range).
    inline BossMechanics::MechanicHandle Overcharge(Creature* owner, float pct, float range, uint32 tag)
    {
        if (!owner || !owner->IsAlive())
            return {};
        owner->CastSpell(owner, BrsUrok::SPELL_UR_OVERCHARGE_LOOK, true);
        owner->RemoveAurasDueToSpell(BrsUrok::SPELL_UR_STOLEN_POWER);
        DungeonKit::RegistryHitSpec spec;
        spec.pct = pct;
        spec.school = SPELL_SCHOOL_ARCANE;
        spec.spellId = BrsUrok::SPELL_UR_OVERCHARGE;
        spec.weakened = false;
        spec.tag = tag;
        return DungeonKit::RegistryHit(owner, PlayersNear(owner, range), spec);
    }
}

#endif
