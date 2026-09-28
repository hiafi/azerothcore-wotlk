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
 * Warlock rework - every ScriptMgr hook (as opposed to a SpellScript/AuraScript bound to one
 * spell id) the three passes need, in one file (druid_hooks.cpp precedent;
 * .agents/plans/warlock-rework/warlock-rework.SHARED.md §4's handler table,
 * warlock-rework.AFFLICTION.md §7.14). These run on every damage/heal/cast event for every class
 * server-wide - every handler here checks for a warlock caster/target (or the specific spell/
 * talent id it cares about) first before doing anything.
 *
 * This pass (Affliction, S1) adds:
 *   - UnitScript::ModifyPeriodicDamageAurasTick - Bane of Agony's live per-tick stack multiplier
 *     (AFFLICTION.md §7.2). Destruction adds Nether Protection's periodic-taken DR to the same
 *     handler in S2.
 *   - AllSpellScript::OnCalcMaxDuration - Pandemic's duration carry (AFFLICTION.md §7.4).
 *   - AllSpellScript::CanPrepare / OnSpellCast - the instant-cast priority arbiter
 *     (Warlock::OnPrepareGrantInstantCast / OnCastConsumeInstantCast); a no-op this pass (empty
 *     registry - Destruction registers real sources in S2).
 *   - PlayerScript::OnPlayerLearnTalents / OnPlayerTalentsReset / OnPlayerAfterSpecSlotChanged /
 *     OnPlayerLogin - Warlock::RefreshLeechTalents (SHARED §4's leech-talent rule; note this
 *     fires for every class, since Blazing Speed is a Fire Mage talent).
 *   - An AuraScript on Fire Mage Blazing Speed (31641/31642/200107) - spell_leech_talent_gate,
 *     zeroing its leech amount unless it is the caster's active leech talent.
 */

#include "WarlockMechanics.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"

namespace
{
    Player* GetWarlockPlayer(Unit* unit)
    {
        Player* player = unit ? unit->ToPlayer() : nullptr;
        return player && player->getClass() == CLASS_WARLOCK ? player : nullptr;
    }
}

// AFFLICTION.md §7.2 - Bane of Agony's live per-tick stack multiplier. Destruction extends this
// same handler with Nether Protection's periodic-taken DR (S2).
class WarlockHooksUnit : public UnitScript
{
public:
    WarlockHooksUnit() : UnitScript("WarlockHooksUnit", true, { UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK }) { }

    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage,
                                        SpellInfo const* spellInfo) override
    {
        if (!target || !attacker || !spellInfo || spellInfo->Id != Warlock::SPELL_BANE_OF_AGONY)
            return;

        if (!GetWarlockPlayer(attacker))
            return;

        uint8 const stacks = Warlock::GetAgonyStacks(target, attacker->GetGUID());
        if (stacks)
            damage = uint32(float(damage) * (1.0f + 0.1f * float(stacks)));
    }
};

// AFFLICTION.md §7.4 (Pandemic carry) and §7.14 (instant-cast arbiter).
class WarlockHooksAllSpell : public AllSpellScript
{
public:
    WarlockHooksAllSpell()
        : AllSpellScript("WarlockHooksAllSpell",
                          { ALLSPELLHOOK_ON_CALC_MAX_DURATION, ALLSPELLHOOK_CAN_PREPARE, ALLSPELLHOOK_ON_CAST })
    {
    }

    // Pandemic (R3): if the refreshing aura is Unstable Affliction from a warlock with either
    // Pandemic rank and 0 < remaining <= 5 s, carry the remainder onto the new maximum. Runs
    // before SPELLMOD_DURATION (SpellAuras.cpp), so Lingering Agony's flat bonus still adds.
    void OnCalcMaxDuration(Aura const* aura, int32& maxDuration) override
    {
        if (!aura || aura->GetId() != Warlock::SPELL_UNSTABLE_AFFLICTION)
            return;

        Unit* casterUnit = aura->GetCaster();
        if (!GetWarlockPlayer(casterUnit))
            return;

        if (!casterUnit->HasAura(Warlock::SPELL_PANDEMIC_R1) && !casterUnit->HasAura(Warlock::SPELL_PANDEMIC_R2))
            return;

        // Hazard (found this session): CalcMaxDuration runs before m_duration is ever assigned on
        // a fresh apply (SpellAuras.cpp), so GetDuration() is uninitialized there. Only treat this
        // as a refresh when the owner already holds this exact aura instance.
        Unit* owner = aura->GetOwner() ? aura->GetOwner()->ToUnit() : nullptr;
        if (!owner || owner->GetOwnedAura(aura->GetId(), aura->GetCasterGUID()) != aura)
            return;

        int32 const left = aura->GetDuration();
        if (left > 0 && left <= 5000)
            maxDuration += left;
    }

    // SHARED §4 "Arbiter timing contract": CanPrepare runs before the SPELL_FAILED_SPELL_IN_PROGRESS
    // rejection and before CheckCast, so it only ever grants, never consumes. The registry is empty
    // this pass (no RegisterInstantCastSource callers yet) - a no-op until Destruction/Demonology add
    // sources in S2/S3.
    bool CanPrepare(Spell* spell, SpellCastTargets const* /*targets*/, AuraEffect const* /*triggeredByAura*/) override
    {
        if (spell)
        {
            Unit* casterUnit = spell->GetCaster() ? spell->GetCaster()->ToUnit() : nullptr;
            if (Player* player = GetWarlockPlayer(casterUnit))
                Warlock::OnPrepareGrantInstantCast(player, spell);
        }
        return true;
    }

    void OnSpellCast(Spell* spell, Unit* caster, SpellInfo const* /*spellInfo*/, bool /*skipCheck*/) override
    {
        if (Player* player = GetWarlockPlayer(caster))
            Warlock::OnCastConsumeInstantCast(player, spell);
    }
};

// SHARED §4 leech-talent rule: re-evaluates every class/spec change and login, since Blazing Speed
// (a Fire Mage talent) needs its aura-295 amount gated the same way as the warlock leech talents.
class WarlockLeechTalentRefresh : public PlayerScript
{
public:
    WarlockLeechTalentRefresh()
        : PlayerScript("WarlockLeechTalentRefresh",
                        { PLAYERHOOK_ON_PLAYER_LEARN_TALENTS, PLAYERHOOK_ON_TALENTS_RESET,
                          PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED, PLAYERHOOK_ON_LOGIN })
    {
    }

    void OnPlayerLearnTalents(Player* player, uint32 /*talentId*/, uint32 /*talentRank*/, uint32 /*spellid*/) override
    {
        Warlock::RefreshLeechTalents(player);
    }

    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        Warlock::RefreshLeechTalents(player);
    }

    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        Warlock::RefreshLeechTalents(player);
    }

    void OnPlayerLogin(Player* player) override
    {
        Warlock::RefreshLeechTalents(player);
    }
};

// 31641, 31642, 200107 - Fire Mage Blazing Speed. Bound additively by the warlock DSL even though
// the spell itself isn't a warlock spell (SHARED §4's leech-talent rule): its aura-295 leech only
// applies while it is the caster's active leech talent (highest %, ties favour the earlier entry
// of Warlock::LeechTalent).
class spell_leech_talent_gate : public AuraScript
{
    PrepareAuraScript(spell_leech_talent_gate);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        if (!player || Warlock::GetActiveLeechTalent(player) != Warlock::LeechTalent::BlazingSpeed)
            amount = 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_leech_talent_gate::CalculateAmount, EFFECT_1,
            SPELL_AURA_MOD_LEECH_PCT);
    }
};

void AddSC_warlock_hooks()
{
    new WarlockHooksUnit();
    new WarlockHooksAllSpell();
    new WarlockLeechTalentRefresh();
    RegisterSpellScript(spell_leech_talent_gate);
}
