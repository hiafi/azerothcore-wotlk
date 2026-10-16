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
 * Hunter rework - hunter-wide spell scripts (hunter-rework.SHARED.md §A4 / §B6 / §B9 / §C4).
 * H0 WP-B1: shot mana, the aspect procs, Aspect of the Monkey, Aspect of the Viper poison, the Dragonhawk explosion
 * hook and Glaive Toss target filtering. Ids come from the Hunter:: aliases in HunterMechanics.h; stock ids the
 * hunter DSL never declares stay hand literals.
 */

#include "HunterMechanics.h"
#include "Pet.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Timer.h"
#include "Unit.h"
#include <list>

namespace
{
    // Stock Aspect of the Monkey aura id, 13163 (Hunter::SPELL_ASPECT_OF_THE_MONKEY)
    constexpr uint32 SPELL_MONKEY = Hunter::SPELL_ASPECT_OF_THE_MONKEY;
}

// 3044 Arcane Shot, 2973 Raptor Strike - shot mana (SHARED §B2): once per cast, hit or miss (Steady Shot returns none)
class spell_hun_shot_mana : public SpellScript
{
    PrepareSpellScript(spell_hun_shot_mana);

    void HandleAfterCast()
    {
        if (Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr)
            Hunter::RestoreShotMana(player, GetSpellInfo());
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_hun_shot_mana::HandleAfterCast);
    }
};

// 13165 Aspect of the Hawk, 61846 Aspect of the Dragonhawk, 13161 Aspect of the Beast, 34074 Aspect of the Viper
// - which events roll (SHARED §B6.2) and the proc action (§B6.1)
class spell_hun_aspect_proc : public AuraScript
{
    PrepareAuraScript(spell_hun_aspect_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_QUICK_SHOTS, Hunter::SPELL_ASPECT_OF_THE_DRAGONHAWK_EXPLOSION,
            Hunter::SPELL_ASPECT_OF_THE_VIPER_POISON, Hunter::SPELL_ASPECT_OF_THE_BEAST_PET_BUFF });
    }

    // The engine starts the internal cooldown right after CheckProc passes, so an event with nothing to act on (no
    // live pet for Beast, no living enemy for Dragonhawk and Viper) is rejected here instead of in HandleProc
    bool HasProcAction(Player* player, ProcEventInfo& eventInfo) const
    {
        switch (GetId())
        {
            case Hunter::SPELL_ASPECT_OF_THE_BEAST:
            {
                Pet* pet = player->GetPet();
                return pet && pet->IsAlive();
            }
            case Hunter::SPELL_ASPECT_OF_THE_DRAGONHAWK:
            case Hunter::SPELL_ASPECT_OF_THE_VIPER:
            {
                Unit* target = Hunter::GetProcTarget(eventInfo);
                return target && target->IsAlive() && !player->IsFriendlyTo(target);
            }
            default:
                return true;
        }
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_HIT)
        {
            // Auto Shot is triggered, so it has no CAST phase; every other HIT event (one per Multi-Shot target) is
            // rejected, which keeps the roll to once per cast
            return (eventInfo.GetTypeMask() & PROC_FLAG_DONE_RANGED_AUTO_ATTACK) && spellInfo &&
                spellInfo->Id == Hunter::SPELL_AUTO_SHOT && HasProcAction(owner->ToPlayer(), eventInfo);
        }

        if (eventInfo.GetSpellPhaseMask() & PROC_SPELL_PHASE_CAST)
            return spellInfo && Hunter::IsAspectRollSource(spellInfo) && HasProcAction(owner->ToPlayer(), eventInfo);

        return false;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        if (!player)
            return;

        Unit* target = Hunter::GetProcTarget(eventInfo);
        switch (GetId())
        {
            case Hunter::SPELL_ASPECT_OF_THE_HAWK:
                player->CastSpell(player, Hunter::SPELL_QUICK_SHOTS, true);
                break;
            case Hunter::SPELL_ASPECT_OF_THE_DRAGONHAWK:
                if (target)
                    player->CastSpell(target, Hunter::SPELL_ASPECT_OF_THE_DRAGONHAWK_EXPLOSION, true);
                break;
            case Hunter::SPELL_ASPECT_OF_THE_BEAST:
                if (Pet* pet = player->GetPet())
                    player->CastSpell(pet, Hunter::SPELL_ASPECT_OF_THE_BEAST_PET_BUFF, true);
                break;
            case Hunter::SPELL_ASPECT_OF_THE_VIPER:
                if (target)
                    player->CastSpell(target, Hunter::SPELL_ASPECT_OF_THE_VIPER_POISON, true);
                break;
            default:
                break;
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_aspect_proc::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_aspect_proc::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 13163 Aspect of the Monkey - hunter side (SHARED §B6.6)
class spell_hun_aspect_of_the_monkey : public AuraScript
{
    PrepareAuraScript(spell_hun_aspect_of_the_monkey);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Hunter::SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY,
            Hunter::SPELL_ASPECT_OF_THE_MONKEY_PET });
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        Unit* owner = GetUnitOwner();
        return owner && owner->IsPlayer();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        if (Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr)
            player->CastSpell(player, Hunter::SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY, true);
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player)
            return;

        if (Pet* pet = player->GetPet())
            player->CastSpell(pet, Hunter::SPELL_ASPECT_OF_THE_MONKEY_PET, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player)
            return;

        if (Pet* pet = player->GetPet())
            pet->RemoveAurasDueToSpell(Hunter::SPELL_ASPECT_OF_THE_MONKEY_PET);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_aspect_of_the_monkey::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_aspect_of_the_monkey::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
        AfterEffectApply += AuraEffectApplyFn(spell_hun_aspect_of_the_monkey::HandleApply, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_hun_aspect_of_the_monkey::HandleRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 201605 Aspect of the Monkey - pet side: the pet's own roll, sharing the hunter's 13163 internal cooldown
// (SHARED §B6.6, §0.13)
class spell_hun_aspect_of_the_monkey_pet : public AuraScript
{
    PrepareAuraScript(spell_hun_aspect_of_the_monkey_pet);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_MONKEY, Hunter::SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY });
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        Player* owner = Hunter::GetOwningPlayer(GetUnitOwner());
        if (!owner)
            return false;

        Aura* hunterAura = owner->GetAura(SPELL_MONKEY);
        if (!hunterAura || hunterAura->IsProcOnCooldown(Acore::Time::SteadyNow()))
            return false;

        SpellProcEntry const* procEntry = sSpellMgr->GetSpellProcEntry(SPELL_MONKEY);
        if (!procEntry)
            return false;

        // same chance as the hunter-side roll, so Pathfinding-style SPELLMOD_CHANCE_OF_SUCCESS applies to both paths
        float chance = procEntry->Chance;
        owner->ApplySpellMod(SPELL_MONKEY, SPELLMOD_CHANCE_OF_SUCCESS, chance);
        return Hunter::RollProcChance(owner, chance);
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* owner = Hunter::GetOwningPlayer(GetUnitOwner());
        if (!owner)
            return;

        owner->CastSpell(owner, Hunter::SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY, true);

        // shared 20 s internal cooldown with the hunter-side proc
        if (Aura* hunterAura = owner->GetAura(SPELL_MONKEY))
            if (SpellProcEntry const* procEntry = sSpellMgr->GetSpellProcEntry(SPELL_MONKEY))
                hunterAura->AddProcCooldown(procEntry, Acore::Time::SteadyNow());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_hun_aspect_of_the_monkey_pet::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_hun_aspect_of_the_monkey_pet::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 201602 Aspect of the Viper - poison: each tick restores eff0 hundredths of a percent of max mana (SHARED §B6.5;
// S1a-1: stored x10, live 50 = 0.50%, so Improved Aspect of the Viper and Glyph 56851 percent mods don't truncate)
class spell_hun_aspect_of_the_viper_poison : public AuraScript
{
    PrepareAuraScript(spell_hun_aspect_of_the_viper_poison);

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsPlayer())
            return;

        caster->EnergizeBySpell(caster, GetId(),
            CalculatePct(caster->GetMaxPower(POWER_MANA), aurEff->GetAmount() / 100.0f), POWER_MANA);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_hun_aspect_of_the_viper_poison::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 201601 Aspect of the Dragonhawk - explosion: a suppressed direct Fire hit still counts for Burning Tar
// (SHARED §B6.4, §A5 OnDirectFireHit contract)
class spell_hun_aspect_of_the_dragonhawk_explosion : public SpellScript
{
    PrepareSpellScript(spell_hun_aspect_of_the_dragonhawk_explosion);

    void HandleAfterHit()
    {
        if (GetHitDamage() > 0)
            Hunter::OnDirectFireHit(GetCaster(), GetHitUnit(), GetSpellInfo());
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_hun_aspect_of_the_dragonhawk_explosion::HandleAfterHit);
    }
};

// 201600 Glaive Toss - bounces only to enemies in combat with the caster (SHARED §B9.3)
class spell_hun_glaive_toss : public SpellScript
{
    PrepareSpellScript(spell_hun_glaive_toss);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        Unit* explTarget = GetExplTargetUnit();
        targets.remove_if([caster, explTarget](WorldObject* obj)
        {
            if (obj == explTarget)
                return false;

            Unit* unit = obj->ToUnit();
            return !unit || !unit->IsInCombatWith(caster);
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_hun_glaive_toss::FilterTargets, EFFECT_0,
            TARGET_UNIT_TARGET_ENEMY);
    }
};

void AddSC_hunter_shared_spell_scripts()
{
    RegisterSpellScript(spell_hun_shot_mana);
    RegisterSpellScript(spell_hun_aspect_proc);
    RegisterSpellScript(spell_hun_aspect_of_the_monkey);
    RegisterSpellScript(spell_hun_aspect_of_the_monkey_pet);
    RegisterSpellScript(spell_hun_aspect_of_the_viper_poison);
    RegisterSpellScript(spell_hun_aspect_of_the_dragonhawk_explosion);
    RegisterSpellScript(spell_hun_glaive_toss);
}
