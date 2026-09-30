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
 * This pass (Affliction, S1) added:
 *   - UnitScript::ModifyPeriodicDamageAurasTick - Bane of Agony's live per-tick stack multiplier
 *     (AFFLICTION.md §7.2); since moved onto 980's own AuraScript when 980 became the stacking
 *     aura (spell_warl_bane_of_agony_aura).
 *   - AllSpellScript::OnCalcMaxDuration - Pandemic's duration carry (AFFLICTION.md §7.4).
 *   - AllSpellScript::CanPrepare / OnSpellCast - the instant-cast priority arbiter
 *     (Warlock::OnPrepareGrantInstantCast / OnCastConsumeInstantCast); a no-op that pass (empty
 *     registry - Destruction registers real sources below).
 *   - PlayerScript::OnPlayerLearnTalents / OnPlayerTalentsReset / OnPlayerAfterSpecSlotChanged /
 *     OnPlayerLogin - Warlock::RefreshLeechTalents (SHARED §4's leech-talent rule; note this
 *     fires for every class, since Blazing Speed is a Fire Mage talent).
 *   - An AuraScript on Fire Mage Blazing Speed (31641/31642/200107) - spell_leech_talent_gate,
 *     zeroing its leech amount unless it is the caster's active leech talent.
 *
 * This pass (Destruction, S2) extends the two existing handlers above (no second registration of
 * either hook, per the WP brief) and adds one new class:
 *   - WarlockHooksUnit::ModifyPeriodicDamageAurasTick gains Nether Protection's periodic-taken
 *     reduction branch (DESTRUCTION.md §7.12, victim side).
 *   - WarlockHooksAllSpell::CanPrepare gains the Destructive Reach crit-helper branch
 *     (DESTRUCTION.md §7.9, via Warlock::ApplyDestructiveReachCrit).
 *   - New class WarlockEmberstormCooldown (AllSpellScript::OnSpellCast) - Emberstorm's capstone
 *     Chaos Bolt cooldown reduction (DESTRUCTION.md §7.15); a second AllSpellScript instance
 *     hooking OnSpellCast is fine (the brief explicitly calls this class out separately from the
 *     "don't re-register CanPrepare/ModifyPeriodicDamageAurasTick" rule).
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

    // Destruction pass (S2) local ids - talent rank ids not part of the frozen WarlockMechanics.h
    // block (Destruction didn't mint new ids for these moved/retained-stock talents), duplicated
    // here rather than widening the frozen header (DESTRUCTION.md §7.12, §7.15).
    constexpr uint32 SPELL_NETHER_PROTECTION_R1 = 30299;
    constexpr uint32 SPELL_NETHER_PROTECTION_R2 = 30301;
    constexpr uint32 SPELL_NETHER_PROTECTION_R3 = 30302;
    constexpr uint32 SPELL_EMBERSTORM_R3 = 17956;
    constexpr uint32 SPELL_SEARING_PAIN = 5676;

    // druid_hooks.cpp:266-276 precedent, reused verbatim: ModifyPeriodicDamageAurasTick also fires
    // for periodic heals (SpellAuraEffects.cpp:6699, the heal amount passed as `damage`) - a heal
    // tick must never be reduced by Nether Protection.
    bool IsPeriodicDamageSpell(SpellInfo const* spellInfo)
    {
        if (spellInfo->HasAura(SPELL_AURA_PERIODIC_HEAL) || spellInfo->HasAura(SPELL_AURA_OBS_MOD_HEALTH))
            return false;

        return spellInfo->HasAura(SPELL_AURA_PERIODIC_DAMAGE) ||
               spellInfo->HasAura(SPELL_AURA_PERIODIC_DAMAGE_PERCENT) ||
               spellInfo->HasAura(SPELL_AURA_PERIODIC_LEECH);
    }
}

// DESTRUCTION.md §7.12 - Nether Protection's periodic-taken DR (S2). Originally added for Bane of
// Agony's stack multiplier, which now lives on spell_warl_bane_of_agony_aura.
class WarlockHooksUnit : public UnitScript
{
public:
    WarlockHooksUnit() : UnitScript("WarlockHooksUnit", true, { UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK }) { }

    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* /*attacker*/, uint32& damage,
                                        SpellInfo const* spellInfo) override
    {
        if (!target || !spellInfo)
            return;

        // DESTRUCTION.md §7.12 - Nether Protection's periodic-taken reduction (victim side).
        // Only needs the target (the attacker may be null).
        if (Player* player = target->ToPlayer())
        {
            if (IsPeriodicDamageSpell(spellInfo) && (spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_MAGIC))
            {
                AuraEffect const* rank = player->GetAuraEffect(SPELL_NETHER_PROTECTION_R3, EFFECT_1);
                if (!rank)
                    rank = player->GetAuraEffect(SPELL_NETHER_PROTECTION_R2, EFFECT_1);
                if (!rank)
                    rank = player->GetAuraEffect(SPELL_NETHER_PROTECTION_R1, EFFECT_1);

                if (rank)
                    damage = uint32(float(damage) * (1.0f - float(rank->GetAmount()) / 100.0f));
            }
        }
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
            {
                Warlock::OnPrepareGrantInstantCast(player, spell);
                // DESTRUCTION.md §7.9 - Destructive Reach's >20 yd crit helper (C3), same handler,
                // same timing contract.
                Warlock::ApplyDestructiveReachCrit(player, spell);
            }
        }
        return true;
    }

    void OnSpellCast(Spell* spell, Unit* caster, SpellInfo const* /*spellInfo*/, bool /*skipCheck*/) override
    {
        if (Player* player = GetWarlockPlayer(caster))
            Warlock::OnCastConsumeInstantCast(player, spell);
    }
};

// DESTRUCTION.md §7.15 - Emberstorm's capstone Chaos Bolt cooldown reduction. Scorch and Fireball
// are mage-family (Classless, PLAN B4), so this needs AllSpellScript::OnSpellCast rather than a
// same-spell SpellScript bound to 29722/5676.
class WarlockEmberstormCooldown : public AllSpellScript
{
public:
    WarlockEmberstormCooldown() : AllSpellScript("WarlockEmberstormCooldown", { ALLSPELLHOOK_ON_CAST }) { }

    void OnSpellCast(Spell* spell, Unit* caster, SpellInfo const* spellInfo, bool /*skipCheck*/) override
    {
        if (!spell || !spellInfo || spell->IsTriggered())
            return;

        Player* player = GetWarlockPlayer(caster);
        if (!player || !player->HasAura(SPELL_EMBERSTORM_R3))
            return;

        bool qualifies = false;
        if (spellInfo->SpellFamilyName == SPELLFAMILY_WARLOCK)
            qualifies = spellInfo->Id == Warlock::SPELL_INCINERATE || spellInfo->Id == SPELL_SEARING_PAIN;
        else if (spellInfo->SpellFamilyName == SPELLFAMILY_MAGE)
            qualifies = spellInfo->SpellFamilyFlags.HasFlag(0x1, 0, 0) ||  // Fireball
                        spellInfo->SpellFamilyFlags.HasFlag(0x10, 0, 0);   // Scorch

        if (qualifies)
            Warlock::ReduceChaosBoltCooldown(player, 1500);
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
    new WarlockEmberstormCooldown();
    new WarlockLeechTalentRefresh();
    RegisterSpellScript(spell_leech_talent_gate);
}
