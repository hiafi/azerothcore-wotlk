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
 * Rogue rework - Subtlety spell scripts (rogue-rework S2a; docs/reworks/rogue-subtlety-rework.md). The PlayerScript /
 * UnitScript hooks (dispatcher, Hidden-state buffs, Lingering Shadow, Executioner, Honor Among Thieves) live in
 * rogue_hooks.cpp and RogueMechanics.cpp; this file holds the spell and aura scripts.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Player.h"
#include "PriestMechanics.h"
#include "RogueMechanics.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"
#include <algorithm>
#include <list>

namespace
{
    Player* GetRoguePlayer(Unit* unit)
    {
        return unit ? unit->ToPlayer() : nullptr;
    }

    // The caster of a spell script when it is a player and the cast is the player's own (not a script cast). Every
    // S2 hit hook below uses it: the Defias casters of Backstab / Ambush are NPCs (S2a-0VERIFY item 16).
    Player* GetOwnCastRogue(SpellScript& script)
    {
        Unit* caster = script.GetCaster();
        if (!caster || !caster->IsPlayer() || script.GetSpell()->IsTriggered())
            return nullptr;

        return caster->ToPlayer();
    }
}

// 204148 - Death from Above (rogue-rework S2a, R8 / R15). The DUMMY hit runs inside the cast, before the finish phase
// spends the combo points: the landing's base value is read now (native line + the per-point line x the held points,
// R4), the area hit launches with the points held, and Rogue::LaunchDeathFromAbove owns the flight and the landing.
class spell_rog_death_from_above : public SpellScript
{
    PrepareSpellScript(spell_rog_death_from_above);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_DEATH_FROM_ABOVE_AREA,
            RogueData::SPELL_DEATH_FROM_ABOVE_LANDING });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!rogue || !target || target == rogue || !target->IsAlive())
            return;

        SpellInfo const* landing = sSpellMgr->GetSpellInfo(RogueData::SPELL_DEATH_FROM_ABOVE_LANDING);
        if (!landing)
            return;

        int32 const landingBase = landing->Effects[EFFECT_0].CalcValue(rogue);
        // Cast at the target: the area is centred on it, and it is the area spell's explicit target (S2a-REVIEW L8).
        rogue->CastSpell(target, RogueData::SPELL_DEATH_FROM_ABOVE_AREA, TRIGGERED_FULL_MASK);
        // The area hit lands inside CastSpell: a target it killed leaves nothing to land on, so no leap (the cast,
        // cooldown and points are spent; S2-CODE-REVIEW M1).
        if (!target->IsAlive())
            return;

        Rogue::LaunchDeathFromAbove(rogue, target, landingBase);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_rog_death_from_above::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 204169 - Death from Above's area hit, 8 yd around Death from Above's target (the area spell's explicit target, cast
// at it by spell_rog_death_from_above). Only that target and enemies already fighting the rogue take it: it never
// pulls a sleeping pack, whatever the rogue has selected.
class spell_rog_death_from_above_area : public SpellScript
{
    PrepareSpellScript(spell_rog_death_from_above_area);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsPlayer())
            return;

        Unit* primary = GetExplTargetUnit();
        targets.remove_if([caster, primary](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || (unit != primary && !unit->IsInCombatWith(caster));
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_rog_death_from_above_area::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 204170 - Death from Above's landing (a custom-bp cast from Rogue::LaunchDeathFromAbove): it resolves like an
// Eviscerate hit (Hemorrhage's share, Finality) with its own damage.
class spell_rog_death_from_above_landing : public SpellScript
{
    PrepareSpellScript(spell_rog_death_from_above_landing);

    void HandleAfterHit()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        Rogue::OnEviscerateHit(rogue, target, uint32(std::max(0, GetHitDamage())),
            RogueData::SPELL_DEATH_FROM_ABOVE_LANDING);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_death_from_above_landing::HandleAfterHit);
    }
};

// 2098 - Eviscerate (Subtlety): Hemorrhage's bleed and Finality resolve on a hit (a dodge changes nothing).
class spell_rog_eviscerate_subtlety : public SpellScript
{
    PrepareSpellScript(spell_rog_eviscerate_subtlety);

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        Rogue::OnEviscerateHit(rogue, target, uint32(std::max(0, GetHitDamage())), RogueData::SPELL_EVISCERATE);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_eviscerate_subtlety::HandleAfterHit);
    }
};

// 1943 - Rupture (third binding, beside Carnage's and the stock one): Finality resolves after the hit.
class spell_rog_rupture_finality : public SpellScript
{
    PrepareSpellScript(spell_rog_rupture_finality);

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        if (!rogue || !GetHitUnit())
            return;

        Rogue::ResolveFinality(rogue, RogueData::SPELL_RUPTURE);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_rupture_finality::HandleAfterHit);
    }
};

// 26679 - Deadly Throw (Subtlety): Throwing Specialization's capstone throws up to two more copies (204168) at other
// enemies around the primary, launched in OnCast so they leave with the points still held; Finality resolves in
// AfterCast (the missile's own damage lands later: accepted, S2a-WP-BRIEF 10.6).
class spell_rog_deadly_throw_subtlety : public SpellScript
{
    PrepareSpellScript(spell_rog_deadly_throw_subtlety);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_THROWING_SPECIALIZATION_COPY,
            RogueData::SPELL_THROWING_SPECIALIZATION_51679 });
    }

    void HandleCopies()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* primary = GetExplTargetUnit();
        if (!rogue || !primary || !rogue->HasAura(RogueData::SPELL_THROWING_SPECIALIZATION_51679))
            return;

        float const radius = float(RogueData::THROWING_SPEC_RADIUS_YD);
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(primary, rogue, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(primary, nearby, check);
        Cell::VisitObjects(primary, searcher, radius);

        // A triggered cast still runs the caster-to-target line of sight test, so only a reachable enemy is a candidate
        nearby.remove_if([rogue, primary](Unit* unit)
        {
            return unit == primary || !unit->IsAlive() || !rogue->IsValidAttackTarget(unit) ||
                !unit->IsInCombatWith(rogue) || !rogue->IsWithinLOSInMap(unit);
        });
        nearby.sort([primary](Unit const* a, Unit const* b)
        {
            return primary->GetExactDistSq(a) < primary->GetExactDistSq(b);
        });

        int32 copies = 0;
        for (Unit* unit : nearby)
        {
            if (copies >= int32(RogueData::THROWING_SPEC_EXTRA_TARGETS))
                break;

            rogue->CastSpell(unit, RogueData::SPELL_THROWING_SPECIALIZATION_COPY, TRIGGERED_FULL_MASK);
            ++copies;
        }
    }

    void HandleAfterCast()
    {
        Player* rogue = GetOwnCastRogue(*this);
        if (!rogue)
            return;

        Rogue::ResolveFinality(rogue, RogueData::SPELL_DEADLY_THROW);
    }

    void Register() override
    {
        OnCast += SpellCastFn(spell_rog_deadly_throw_subtlety::HandleCopies);
        AfterCast += SpellCastFn(spell_rog_deadly_throw_subtlety::HandleAfterCast);
    }
};

// 53 - Backstab (Subtlety): Slaughter from the Shadows' cooldown roll and Lingering Shadow's extra point. The caster
// may be a creature (Defias casters): the helper is only called for a player's own cast.
class spell_rog_backstab_subtlety : public SpellScript
{
    PrepareSpellScript(spell_rog_backstab_subtlety);

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        Rogue::OnBackstabHit(rogue, target);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_backstab_subtlety::HandleAfterHit);
    }
};

// 8676 - Ambush (second binding, beside RG0b's teleport script): Akaari's Echo's roll, with the strike's damage.
class spell_rog_ambush_subtlety : public SpellScript
{
    PrepareSpellScript(spell_rog_ambush_subtlety);

    void HandleAfterHit()
    {
        Player* rogue = GetOwnCastRogue(*this);
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        Rogue::OnAmbushHit(rogue, target, uint32(std::max(0, GetHitDamage())));
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_ambush_subtlety::HandleAfterHit);
    }
};

// 204160 - Hemorrhage's bleed (a PERIODIC_DUMMY on the target). Every tick deals the stored per-tick amount through
// 204161, a never-miss, no-crit, no-caster-modifier Physical hit (Doomblade's shape: the stored damage already carries
// every modifier).
class spell_rog_hemorrhage : public AuraScript
{
    PrepareAuraScript(spell_rog_hemorrhage);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_HEMORRHAGE_BLEED, RogueData::SPELL_HEMORRHAGE_TICK });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* target = GetUnitOwner();
        if (!rogue || !target || !target->IsAlive())
            return;

        int32 const tick = int32(Rogue::GetStoredBleedTick(rogue, target, RogueData::SPELL_HEMORRHAGE_BLEED));
        if (tick <= 0)
            return;

        // No triggering aura: Spell.cpp rejects a cast triggered by an aura whose caster is dead, and the bleed keeps
        // ticking after the rogue dies like Rupture and Garrote do (S1-CODE-REVIEW L2).
        rogue->CastCustomSpell(target, RogueData::SPELL_HEMORRHAGE_TICK, &tick, nullptr, nullptr, true);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_rog_hemorrhage::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 204165 - Sinister Calling's volley (centred on the finisher's target). The explicit target is always kept, then up
// to SINISTER_CALLING_MAX_TARGETS - 1 other enemies already fighting the rogue, the ones closest to it first.
class spell_rog_sinister_calling_volley : public SpellScript
{
    PrepareSpellScript(spell_rog_sinister_calling_volley);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        Unit* primary = GetExplTargetUnit();
        if (!caster || !caster->IsPlayer())
            return;

        targets.remove_if([caster, primary](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || (unit != primary && !unit->IsInCombatWith(caster));
        });

        if (primary)
        {
            targets.sort([primary](WorldObject const* a, WorldObject const* b)
            {
                if ((a == primary) != (b == primary))
                    return a == primary;

                return primary->GetExactDistSq(a) < primary->GetExactDistSq(b);
            });
        }

        size_t const maxTargets = size_t(RogueData::SINISTER_CALLING_MAX_TARGETS);
        if (targets.size() > maxTargets)
            targets.resize(maxTargets);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_rog_sinister_calling_volley::FilterTargets,
            EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 204154 - Master of Subtlety's buff: the damage bonus is the held rank's amount (+ Mastery with rank 3), polled once a
// second because Mastery is not an aura amount (S1's Vile Poisons precedent); an effect is only rewritten when its
// value moved. Rogue::GetMasterOfSubtletyPct is the one formula (UpdateHiddenBuffs reads it too).
class spell_rog_master_of_subtlety_buff : public AuraScript
{
    PrepareAuraScript(spell_rog_master_of_subtlety_buff);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Player* rogue = GetRoguePlayer(GetUnitOwner()))
            amount = Rogue::GetMasterOfSubtletyPct(rogue);
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* rogue = GetRoguePlayer(GetUnitOwner());
        AuraEffect* damage = GetEffect(EFFECT_0);
        if (!rogue || !damage)
            return;

        int32 const wanted = Rogue::GetMasterOfSubtletyPct(rogue);
        if (damage->GetAmount() != wanted)
            damage->ChangeAmount(wanted);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_master_of_subtlety_buff::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_DONE);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_rog_master_of_subtlety_buff::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 204173 - Enveloping Shadows' helper (linked to Ghostly Veil's aura, which it lives exactly as long as): the damage
// taken reduction is the held talent rank's amount.
class spell_rog_enveloping_shadows : public AuraScript
{
    PrepareAuraScript(spell_rog_enveloping_shadows);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Player* rogue = GetRoguePlayer(GetUnitOwner());
        if (!rogue)
            return;

        amount = -Rogue::GetRankAmount(rogue, { RogueData::SPELL_ENVELOPING_SHADOWS,
            RogueData::SPELL_ENVELOPING_SHADOWS_31212, RogueData::SPELL_ENVELOPING_SHADOWS_31213 }, EFFECT_0);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_enveloping_shadows::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
    }
};

// -31228 - Cheat Death (fork of the stock spell_rog_cheat_death on the Ardent Defender prot shape). Chance = the rank's
// EFFECT_0 (33 / 66 / 100); a lethal hit (other finite absorbs counted first) no larger than the victim's health plus
// CHEAT_DEATH_CAP_MAX_HEALTH_PCT of its maximum is absorbed whole; Cheating Death (-90% damage taken for 3 s) and the
// shared 2 min marker (Spirit of Redemption / Ardent Defender) follow; the capstone also resets Vanish.
class spell_rog_cheat_death_rework : public AuraScript
{
    PrepareAuraScript(spell_rog_cheat_death_rework);

    int32 _chance = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_CHEATING_DEATH, Priest::SPELL_CHEATED_DEATH_MARKER,
            RogueData::SPELL_VANISH, RogueData::SPELL_CHEAT_DEATH_31230 });
    }

    bool Load() override
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return false;

        _chance = GetSpellInfo()->Effects[EFFECT_0].CalcValue();
        return true;
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = -1; // unlimited
    }

    // Remaining amount of the victim's other finite school absorbs that match the hit (absorb order is unspecified)
    static uint32 CountOtherFiniteAbsorbs(Unit const* victim, AuraEffect const* self, DamageInfo const& dmgInfo)
    {
        uint32 total = 0;
        for (AuraEffect const* effect : victim->GetAuraEffectsByType(SPELL_AURA_SCHOOL_ABSORB))
        {
            if (effect == self || effect->GetAmount() <= 0)
                continue;

            if (effect->GetMiscValue() & dmgInfo.GetSchoolMask())
                total += uint32(effect->GetAmount());
        }

        return total;
    }

    void HandleAbsorb(AuraEffect* aurEff, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        Player* victim = GetRoguePlayer(GetTarget());
        if (!victim || victim->HasAura(Priest::SPELL_CHEATED_DEATH_MARKER))
            return;

        int64 const health = int64(victim->GetHealth());
        int64 const damage = int64(dmgInfo.GetDamage());
        bool const lethal = health - damage + int64(CountOtherFiniteAbsorbs(victim, aurEff, dmgInfo)) <= 0;
        if (!lethal)
            return;

        // A blow far past the health pool (a one-shot mechanic) is not saved
        if (damage > health + int64(victim->CountPctFromMaxHealth(uint32(RogueData::CHEAT_DEATH_CAP_MAX_HEALTH_PCT))))
            return;

        if (!Rogue::RollProcChance(victim, float(_chance)))
            return;

        // Avoid the whole hit, then the -90% window and the shared 2 min lockout (the marker is the lockout)
        absorbAmount = dmgInfo.GetDamage();
        victim->CastSpell(victim, RogueData::SPELL_CHEATING_DEATH, TRIGGERED_FULL_MASK);
        victim->CastSpell(victim, Priest::SPELL_CHEATED_DEATH_MARKER, TRIGGERED_FULL_MASK);

        if (victim->HasAura(RogueData::SPELL_CHEAT_DEATH_31230))
            victim->RemoveSpellCooldown(RogueData::SPELL_VANISH, true);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_cheat_death_rework::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_rog_cheat_death_rework::HandleAbsorb, EFFECT_0);
    }
};

void AddSC_rogue_subtlety_spell_scripts()
{
    RegisterSpellScript(spell_rog_death_from_above);
    RegisterSpellScript(spell_rog_death_from_above_area);
    RegisterSpellScript(spell_rog_death_from_above_landing);
    RegisterSpellScript(spell_rog_eviscerate_subtlety);
    RegisterSpellScript(spell_rog_rupture_finality);
    RegisterSpellScript(spell_rog_deadly_throw_subtlety);
    RegisterSpellScript(spell_rog_backstab_subtlety);
    RegisterSpellScript(spell_rog_ambush_subtlety);
    RegisterSpellScript(spell_rog_hemorrhage);
    RegisterSpellScript(spell_rog_sinister_calling_volley);
    RegisterSpellScript(spell_rog_master_of_subtlety_buff);
    RegisterSpellScript(spell_rog_enveloping_shadows);
    RegisterSpellScript(spell_rog_cheat_death_rework);
}
