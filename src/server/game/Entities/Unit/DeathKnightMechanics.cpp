/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "DeathKnightMechanics.h"
#include "Creature.h"
#include "DataMap.h"
#include "GameTime.h"
#include "Player.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <deque>
#include <limits>

/*
 * DK0a block (docs/reworks/death-knight-shared-rework.md): the Death Strike damage-taken record and heal, the
 * Pestilence copy hook (empty until S3) and the Anti-Magic Zone shared pool (U12). Per-player and per-zone state lives
 * in CustomData: it belongs to the object's map thread, needs no lock, and dies with the object (a relog builds a new
 * Player, a recast summons a new zone), so nothing can go stale across sessions.
 */
namespace
{
    // Hits closer together than this share one record entry (the entry keeps the first hit's time). Bounds the record
    // to DEATH_STRIKE_WINDOW_MS / RECORD_COALESCE_MS + 1 entries however many hits land (AoE, DoTs, many attackers);
    // the cost is that up to this much damage at the window's far edge may drop out of the sum early.
    constexpr int64 RECORD_COALESCE_MS = 100;

    struct DamageTakenEntry
    {
        int64 timeMs;   // GameTime ms of the entry's first hit (monotonic, server-uptime based, no wrap)
        uint64 amount;
    };

    struct DamageTakenRecord : DataMap::Base
    {
        std::deque<DamageTakenEntry> entries;
    };

    constexpr char const* DAMAGE_TAKEN_RECORD_KEY = "deathknight_damage_taken_record";

    struct ZoneAbsorbPool : DataMap::Base
    {
        bool initialised = false;
        bool depleted = false;   // reached 0 and the unsummon is scheduled; every later call absorbs nothing
        uint64 remaining = 0;
    };

    constexpr char const* ZONE_ABSORB_POOL_KEY = "deathknight_amz_pool";

    int64 NowMs()
    {
        return int64(GameTime::GetGameTimeMS().count());
    }

    void PruneRecord(DamageTakenRecord& record, int64 now)
    {
        int64 const window = int64(std::max<int32>(0, DeathKnightData::DEATH_STRIKE_WINDOW_MS));
        while (!record.entries.empty() && record.entries.front().timeMs + window < now)
            record.entries.pop_front();
    }

    uint32 ClampToUInt32(uint64 value)
    {
        return uint32(std::min<uint64>(value, std::numeric_limits<uint32>::max()));
    }

    // The pool's starting size (brief ruling 10): 50461's flat (level-scaled base through the owner, potency correction
    // included) plus the generated AP coefficient x the owner's attack power. The engine adds neither SP nor AP to a
    // SCHOOL_ABSORB amount, so both parts are read here; without the spell_bonus_data row it is the flat only.
    uint64 ComputeInitialZonePool(Player const* owner)
    {
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_ANTI_MAGIC_ZONE);
        if (!spellInfo)
            return 0;

        float amount = float(std::max<int32>(0, spellInfo->Effects[EFFECT_0].CalcValue(owner)));
        if (SpellBonusEntry const* bonus = sSpellMgr->GetSpellBonusData(DeathKnightData::SPELL_ANTI_MAGIC_ZONE))
            if (bonus->ap_bonus > 0.0f)
                amount += bonus->ap_bonus * owner->GetTotalAttackPowerValue(BASE_ATTACK);

        return uint64(std::max(0.0f, amount));
    }
}

namespace DeathKnight
{
    bool TracksDamageTaken(Player const* player)
    {
        return player && player->HasSpell(DeathKnightData::SPELL_DEATH_STRIKE);
    }

    void RecordDamageTaken(Player* player, uint32 amount)
    {
        if (!player || !amount)
            return;

        DamageTakenRecord* record = player->CustomData.GetDefault<DamageTakenRecord>(DAMAGE_TAKEN_RECORD_KEY);
        int64 const now = NowMs();
        PruneRecord(*record, now);

        if (!record->entries.empty() && record->entries.back().timeMs + RECORD_COALESCE_MS > now)
            record->entries.back().amount += amount;
        else
            record->entries.push_back({ now, amount });
    }

    uint32 GetRecordedDamage(Player* player)
    {
        if (!player)
            return 0;

        // Get, not GetDefault: a player who was never hit has no record and needs none allocated.
        DamageTakenRecord* record = player->CustomData.Get<DamageTakenRecord>(DAMAGE_TAKEN_RECORD_KEY);
        if (!record)
            return 0;

        PruneRecord(*record, NowMs());

        uint64 total = 0;
        for (DamageTakenEntry const& entry : record->entries)
            total += entry.amount;

        return ClampToUInt32(total);
    }

    uint32 ComputeDeathStrikeHeal(Player* player, int32 healPct)
    {
        if (!player)
            return 0;

        uint64 const fromRecord = uint64(GetRecordedDamage(player)) * uint64(std::max<int32>(0, healPct)) / 100;
        int32 const minPct = std::max<int32>(0, DeathKnightData::DEATH_STRIKE_MIN_HEAL_PCT);
        uint64 const floor = player->CountPctFromMaxHealth(minPct);
        return ClampToUInt32(std::max(fromRecord, floor));
    }

    void OnPestilenceCopy(Player* /*dk*/, Unit* /*source*/, Unit* /*target*/)
    {
        // Intentionally empty in DK0a: Pestilence's copy rules (skip a target that already has the caster's disease,
        // no Glyph of Disease refresh) live in spell_dk_pestilence_rework. S3 adds the Unholy wound copies and On a
        // Pale Horse here; the script already calls this once per enemy a copy reached.
    }

    uint32 ConsumeZoneAbsorb(Unit* zone, Player* owner, uint32 wanted)
    {
        if (!zone || !wanted)
            return 0;

        ZoneAbsorbPool* pool = zone->CustomData.GetDefault<ZoneAbsorbPool>(ZONE_ABSORB_POOL_KEY);
        if (pool->depleted)
            return 0;

        if (!pool->initialised)
        {
            // The first absorb sizes the pool from the owner (the DK who placed the zone). Without an owner there is
            // nothing to size it from: absorb nothing this time and try again on the next hit.
            if (!owner)
                return 0;

            pool->remaining = ComputeInitialZonePool(owner);
            pool->initialised = true;
        }

        uint64 const absorbed = std::min<uint64>(wanted, pool->remaining);
        pool->remaining -= absorbed;

        if (!pool->remaining)
        {
            pool->depleted = true;

            // Called from inside an OnEffectAbsorb handler of the zone's own area aura. TempSummon::UnSummon(0ms) goes
            // through Map::AddObjectToRemoveList -> CleanupsBeforeDelete -> RemoveAllAuras right now, which would
            // remove the very aura (and its applications on the party) whose absorb is being processed. A 1 ms delay
            // queues a ForcedUnsummonDelayEvent (ForcedDespawnDelayEvent for a non-summon) on the zone's own event
            // processor instead, so the removal runs in the zone's next Unit::Update, outside any damage/absorb stack.
            // `depleted` keeps the pool at 0 until then (the area aura may re-apply copies meanwhile).
            if (Creature* creature = zone->ToCreature())
                creature->DespawnOrUnsummon(1ms);
        }

        return uint32(absorbed);
    }
}
