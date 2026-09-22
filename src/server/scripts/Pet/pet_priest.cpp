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

/*
 * Ordered alphabetically using scriptname.
 * Scriptnames of files in this file should be prefixed with "npc_pet_pri_".
 */

#include "CellImpl.h"
#include "CreatureScript.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "PetAI.h"
#include "ScriptedCreature.h"
#include "TaskScheduler.h"
#include "TemporarySummon.h"
#include "TotemAI.h"
#include <algorithm>

enum PriestSpells
{
    // Holy rework (docs/reworks/priest-holy-rework.md sec 3 "Lightwell",
    // priest-rework.HOLY.md 6,1): "290 + 0.4 SP coefficient" (PLAN sec 2 default - the spec text
    // only says "290"). Retires the old click-to-drink path entirely: SPELL_PRIEST_LIGHTWELL_CHARGES
    // (59907) is no longer cast, and the click spell (spell_pri_lightwell/spell_pri_lightwell_renew
    // in spell_priest.cpp) is left unbound but harmless once the creature_template npcflag/
    // npc_spellclick_spells rows granting the click are removed (see this pass's hand-written
    // pending_db_world migration).
    SPELL_PRIEST_LIGHTWELL_HEAL              = 200202
};

enum PriestLightwellMisc
{
    // Design doc sec 3: "once per second it selects a party or raid member within 20 yds below
    // 50% health and heals them for 290. Expires after 30 sec or 10 heals, whichever comes first."
    // The 30 sec half of that is the summon's own TempSummon duration (baseline edit, WP-A data) -
    // this file only owns the heal-count half.
    PRIEST_LIGHTWELL_MAX_HEALS               = 10,
    PRIEST_LIGHTWELL_RANGE_YARDS             = 20,
    PRIEST_LIGHTWELL_HEAL_THRESHOLD_PCT      = 50
};

struct npc_pet_pri_lightwell : public TotemAI
{
    npc_pet_pri_lightwell(Creature* creature) : TotemAI(creature) { }

    uint32 _healsUsed = 0;

    void InitializeAI() override
    {
        if (TempSummon* tempSummon = me->ToTempSummon())
        {
            if (Unit* owner = tempSummon->GetSummonerUnit())
            {
                uint32 hp = uint32(owner->GetMaxHealth() * 0.3f);
                me->SetMaxHealth(hp);
                me->SetHealth(hp);
                me->SetLevel(owner->GetLevel());
            }
        }

        TotemAI::InitializeAI();

        // No more player interaction (design doc sec 3) - tick every 1 sec and auto-heal the
        // lowest-health ally in range instead of waiting on SPELL_PRIEST_LIGHTWELL_CHARGES clicks.
        // TotemAI has no scheduler/EventMap driver of its own (its base UpdateAI only ever runs
        // TOTEM_ACTIVE's attack-search logic, which a passive healing totem never reaches), so
        // UpdateAI() below drives `scheduler` (CreatureAI member, cpp-guidelines.md) directly.
        scheduler.Schedule(1s, [this](TaskContext context)
        {
            TryHealLowestAlly();
            context.Repeat(1s);
        });
    }

    void TryHealLowestAlly()
    {
        TempSummon* tempSummon = me->ToTempSummon();
        Unit* owner = tempSummon ? tempSummon->GetSummonerUnit() : nullptr;
        if (!owner)
            return;

        std::list<Unit*> nearby;
        Acore::AnyGroupedUnitInObjectRangeCheck check(me, owner, float(PRIEST_LIGHTWELL_RANGE_YARDS), true);
        Acore::UnitListSearcher<Acore::AnyGroupedUnitInObjectRangeCheck> searcher(me, nearby, check);
        Cell::VisitObjects(me, searcher, float(PRIEST_LIGHTWELL_RANGE_YARDS));

        nearby.remove_if([](Unit const* unit) { return !unit->HealthBelowPct(PRIEST_LIGHTWELL_HEAL_THRESHOLD_PCT); });
        if (nearby.empty())
            return;

        Unit* lowest = *std::min_element(nearby.begin(), nearby.end(), Acore::HealthPctOrderPred());

        me->CastSpell(lowest, SPELL_PRIEST_LIGHTWELL_HEAL, true);

        if (++_healsUsed >= PRIEST_LIGHTWELL_MAX_HEALS)
            if (TempSummon* summon = me->ToTempSummon())
                summon->UnSummon();
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);
    }
};

void AddSC_priest_pet_scripts()
{
    RegisterCreatureAI(npc_pet_pri_lightwell);
}
