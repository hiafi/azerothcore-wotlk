/*
 * mod-dungeon-bosses, Shadowfang Keep: Soul Drain, the engine glue Rethilgore (WP-S1, RG4-RG5) and Baron Silverlaine's
 * Echo of Rethilgore (WP-S3) share (handoff section 3.3 item 3). The pure part (spell ids, tuning, fragment points,
 * PickFreePoint) is RethilgoreLogic.h; the spells are apps/dbc-tools source/npcs/shadowfang_keep/rethilgore.py.
 *
 *   Channeling / StartChannel / StopChannel   the soul beam on the prisoner (205913, a look only: the drainer keeps
 *                                             acting while it channels)
 *   Tick                                      one 5% Shadow tick on the prisoner (205914, RefFlat in its SpellScript)
 *   Streak                                    a fragment's flight from its point to a unit (205916, a wisp casts it)
 *   ReturnSoul                                a caught fragment: the streak to its owner and 5% of the reference row
 *   Feast                                     a missed fragment: the streak to the drainer and 5% of its max health
 *
 * The fragment pickups themselves are the caller's (DungeonKit::Pickups with NPC_SFK_SOUL_FRAGMENT as the look): their
 * life, points and eligibility are the encounter's.
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_SOUL_DRAIN_H
#define MOD_DUNGEON_BOSSES_SFK_SOUL_DRAIN_H

#include "Creature.h"
#include "DungeonKit.h"
#include "RethilgoreLogic.h"
#include "ShadowfangKeepRework.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "TemporarySummon.h"
#include "Unit.h"

namespace SoulDrain
{
    // How long the wisp that flies the streak lives.
    inline constexpr uint32 kStreakWispMs = 1500;

    inline bool Channeling(Unit const* drainer)
    {
        Spell const* channel = drainer ? drainer->GetCurrentSpell(CURRENT_CHANNELED_SPELL) : nullptr;
        return channel && channel->m_spellInfo->Id == Rethilgore::SPELL_SOUL_DRAIN;
    }

    // Starts the channel on `target` unless it already runs (call it every update while draining: it comes back if
    // anything ever drops it).
    inline void StartChannel(Unit* drainer, Unit* target)
    {
        if (drainer && target && drainer->IsAlive() && !Channeling(drainer))
            drainer->CastSpell(target, Rethilgore::SPELL_SOUL_DRAIN, true);
    }

    inline void StopChannel(Unit* drainer)
    {
        if (Channeling(drainer))
            drainer->InterruptSpell(CURRENT_CHANNELED_SPELL);
    }

    // One tick: 5% Shadow of the reference non-tank row of `drainer`'s map (205914's SpellScript).
    inline void Tick(Unit* drainer, Unit* target)
    {
        if (drainer && target)
            drainer->CastSpell(target, Rethilgore::SPELL_SOUL_DRAIN_TICK, true);
    }

    // A fragment's flight from `from` to `to`: a short-lived wisp summoned by `summoner` casts the streak missile.
    inline void Streak(Creature* summoner, Position const& from, Unit* to)
    {
        if (!summoner || !to)
            return;
        if (TempSummon* wisp = summoner->SummonCreature(ShadowfangKeepRework::NPC_SFK_SOUL_FRAGMENT, from,
                TEMPSUMMON_TIMED_DESPAWN, kStreakWispMs))
            wisp->CastSpell(to, Rethilgore::SPELL_SOUL_STREAK, true);
    }

    // A caught fragment returns to `soulOwner`: the streak, then 5% of `refOwner`'s reference non-tank row as a heal
    // (205915, cast by the owner on itself). Returns the amount (0: nothing done).
    inline int32 ReturnSoul(Creature* refOwner, Position const& from, Unit* soulOwner)
    {
        if (!refOwner || !soulOwner || !soulOwner->IsAlive())
            return 0;
        Streak(refOwner, from, soulOwner);
        int32 const amount = static_cast<int32>(DungeonKit::RefFlat(refOwner, Rethilgore::kFragmentHealPct));
        soulOwner->CastCustomSpell(Rethilgore::SPELL_SOUL_RETURN, SPELLVALUE_BASE_POINT0, amount, soulOwner, true);
        return amount;
    }

    // A missed fragment feeds `drainer`: the streak, then 5% of its max health as a heal (205917). Returns the amount.
    inline int32 Feast(Creature* drainer, Position const& from)
    {
        if (!drainer || !drainer->IsAlive())
            return 0;
        Streak(drainer, from, drainer);
        int32 const amount = static_cast<int32>(drainer->CountPctFromMaxHealth(
            static_cast<int32>(Rethilgore::kFragmentFeastPct)));
        drainer->CastCustomSpell(Rethilgore::SPELL_SOUL_FEAST, SPELLVALUE_BASE_POINT0, amount, drainer, true);
        return amount;
    }
}

#endif
