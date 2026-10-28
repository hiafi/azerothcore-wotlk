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
 * Rogue rework - Assassination spell scripts (rogue-rework S1a; docs/reworks/rogue-assassination-rework.md). The
 * PlayerScript / UnitScript hooks (dispatcher, Overkill, Remorseless, Zoldyck, Dashing Scoundrel, dual-strike records)
 * live in rogue_hooks.cpp and RogueMechanics.cpp; this file holds the spell and aura scripts.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "Duration.h"
#include "EngagementMechanics.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "ItemTemplate.h"
#include "ObjectAccessor.h"
#include "Player.h"
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
#include <cmath>
#include <list>

namespace
{
    // Fan of Knives' off-hand strike (a linked spell, stock) is not declared in RogueData.
    constexpr uint32 SPELL_ROGUE_FAN_OF_KNIVES_OFFHAND = 52874;

    // The hands of Mutilate and Kingsbane resolve their crit talents once, through the parent's AfterCast
    // (Rogue::ResolveDualStrike), so no talent proc may fire from a hand.
    bool IsMutilateHand(uint32 spellId)
    {
        return spellId == RogueData::SPELL_MUTILATE_MH || spellId == RogueData::SPELL_MUTILATE_OH;
    }

    bool IsDualStrikeHand(uint32 spellId)
    {
        return IsMutilateHand(spellId) || spellId == RogueData::SPELL_KINGSBANE_MH ||
            spellId == RogueData::SPELL_KINGSBANE_OH;
    }

    Player* GetRoguePlayer(Unit* unit)
    {
        return unit ? unit->ToPlayer() : nullptr;
    }

    // An enemy near a point that Poison Bomb may touch: alive, attackable, already in combat with the rogue or the
    // rogue's group (the bomb never pulls).
    class EngagedEnemyInRadius
    {
    public:
        EngagedEnemyInRadius(Player const* rogue, float x, float y, float z, float radius)
            : _rogue(rogue), _x(x), _y(y), _z(z), _radius(radius) { }

        bool operator()(Unit* unit) const
        {
            return unit->IsAlive() && _rogue->IsValidAttackTarget(unit) &&
                unit->IsWithinDist3d(_x, _y, _z, _radius) && Engagement::IsEngagedWithOwnerOrGroup(unit, _rogue);
        }

    private:
        Player const* _rogue;
        float _x;
        float _y;
        float _z;
        float _radius;
    };

    // Poison Bomb: `stacks` Deadly Poison applications (ordinary ones: Kingsbane stacks, Deadly Brew) on every
    // engaged enemy within the bomb radius of the stored point. The point is fixed (the cloud stays where the target
    // stood), so the pulse events re-resolve the caster by guid.
    void ApplyBombStacks(Player* rogue, float x, float y, float z, int32 stacks)
    {
        Map* map = rogue->GetMap();
        if (!map)
            return;

        float const radius = float(RogueData::POISON_BOMB_RADIUS_YD);
        std::list<Unit*> enemies;
        EngagedEnemyInRadius check(rogue, x, y, z, radius);
        Acore::UnitListSearcher<EngagedEnemyInRadius> searcher(rogue, enemies, check);
        Cell::VisitObjects(x, y, map, searcher, radius);

        for (Unit* enemy : enemies)
            for (int32 i = 0; i < stacks; ++i)
                Rogue::ApplyPoison(rogue, enemy, RogueData::SPELL_DEADLY_POISON, nullptr, Rogue::PoisonSource::Talent);
    }
}

// 14177 - Cold Blood (fork of the stock spell_rog_cold_blood). A hand of Mutilate or Kingsbane never consumes the
// charge: the parent's AfterCast removes it once (ConsumeColdBlood). A real consumption (the proc system dropped the
// last charge) gives the after-buff and, for a finishing move, the Seal Fate capstone's speed roll.
class spell_rog_cold_blood_rework : public AuraScript
{
    PrepareAuraScript(spell_rog_cold_blood_rework);

public:
    bool WasUsedByDualStrike() const { return _usedByDualStrike; }

private:
    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_COLD_BLOOD_AFTER, RogueData::SPELL_SEAL_FATE_HASTE,
            RogueData::SPELL_SEAL_FATE_14193 });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (spellInfo && IsDualStrikeHand(spellInfo->Id))
        {
            _usedByDualStrike = true;
            return false;
        }

        return true;
    }

    // AfterProc runs only when the proc fired; the charge was already taken, so this is the consumption.
    void HandleAfterProc(ProcEventInfo& eventInfo)
    {
        Player* rogue = GetRoguePlayer(GetUnitOwner());
        if (!rogue)
            return;

        rogue->CastSpell(rogue, RogueData::SPELL_COLD_BLOOD_AFTER, TRIGGERED_FULL_MASK);

        // Seal Fate capstone: consuming Cold Blood with a finishing move, per combo point (still held: the finisher
        // spends them after its hits).
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || !spellInfo->NeedsComboPoints() || !rogue->HasAura(RogueData::SPELL_SEAL_FATE_14193))
            return;

        uint8 const comboPoints = rogue->GetComboPoints();
        if (comboPoints && Rogue::RollProcChance(rogue,
                float(RogueData::SEAL_FATE_CAPSTONE_PCT_PER_CP) * float(comboPoints)))
            rogue->CastSpell(rogue, RogueData::SPELL_SEAL_FATE_HASTE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rog_cold_blood_rework::CheckProc);
        AfterProc += AuraProcFn(spell_rog_cold_blood_rework::HandleAfterProc);
    }

    bool _usedByDualStrike = false;
};

// 203838 - Remorseless Attacks' crit buff. A hand of Mutilate never consumes it: the Mutilate parent removes it once.
class spell_rog_remorseless_attacks_rework : public AuraScript
{
    PrepareAuraScript(spell_rog_remorseless_attacks_rework);

public:
    bool WasUsedByDualStrike() const { return _usedByDualStrike; }

private:
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (spellInfo && IsMutilateHand(spellInfo->Id))
        {
            _usedByDualStrike = true;
            return false;
        }

        return true;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rog_remorseless_attacks_rework::CheckProc);
    }

    bool _usedByDualStrike = false;
};

namespace
{
    // The parent's AfterCast: if a hand tried to consume Cold Blood, the cast used it up (remove it, give the
    // after-buff once).
    void ConsumeColdBlood(Player* rogue)
    {
        Aura* coldBlood = rogue->GetAura(RogueData::SPELL_COLD_BLOOD);
        if (!coldBlood)
            return;

        auto* script = coldBlood->GetScript<spell_rog_cold_blood_rework>("spell_rog_cold_blood_rework");
        if (!script || !script->WasUsedByDualStrike())
            return;

        coldBlood->Remove();
        rogue->CastSpell(rogue, RogueData::SPELL_COLD_BLOOD_AFTER, TRIGGERED_FULL_MASK);
    }

    void ConsumeRemorselessCrit(Player* rogue)
    {
        Aura* remorseless = rogue->GetAura(RogueData::SPELL_REMORSELESS_CRIT);
        if (!remorseless)
            return;

        auto* script = remorseless->GetScript<spell_rog_remorseless_attacks_rework>(
            "spell_rog_remorseless_attacks_rework");
        if (script && script->WasUsedByDualStrike())
            remorseless->Remove();
    }
}

// 1329 - Mutilate (the parent). The two hands (203827 / 203828) strike first; the parent resolves the once-per-cast
// talents (Seal Fate, Focused Attacks, Doomblade, Blindside, Quick Recovery) and consumes Cold Blood and
// Remorseless Attacks once. The parent rolls its own miss / dodge / parry: a parent that did not hit resolves nothing
// (the next cast's stamp replaces its record).
class spell_rog_mutilate_rework : public SpellScript
{
    PrepareSpellScript(spell_rog_mutilate_rework);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_MUTILATE, RogueData::SPELL_MUTILATE_MH,
            RogueData::SPELL_MUTILATE_OH, RogueData::SPELL_COLD_BLOOD, RogueData::SPELL_COLD_BLOOD_AFTER,
            RogueData::SPELL_REMORSELESS_CRIT });
    }

    // AfterHit runs only for a unit the cast hit (not on a miss, dodge or parry).
    void HandleAfterHit()
    {
        _hit = true;
    }

    void HandleAfterCast()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue)
            return;

        Unit* target = GetExplTargetUnit();
        if (target && _hit)
            Rogue::ResolveDualStrike(rogue, target, RogueData::SPELL_MUTILATE);

        ConsumeColdBlood(rogue);
        ConsumeRemorselessCrit(rogue);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_mutilate_rework::HandleAfterHit);
        AfterCast += SpellCastFn(spell_rog_mutilate_rework::HandleAfterCast);
    }

    bool _hit = false;
};

// 203827, 203828 - Mutilate's main-hand and off-hand strikes. Each hand treats its weapon as a 1.7 speed weapon for
// both its weapon damage and its attack power part (a design rule: weapon choice does not change damage per press),
// and takes +15% per poison of the rogue's on the target.
// The engine's hit damage is (weapon roll + AP / 14 x the weapon's normalization factor) x percents; the rescale
// multiplies it by target / actual, where actual = average weapon + AP / 14 x factor and target = (average weapon /
// weapon speed + AP / 14) x 1.7. Both sides use the average roll, so the roll's variance is kept.
// Accepted (S1a review L5): the hit damage here already includes the flat bonus, so the rescale scales that small flat
// part too; weapon choice still moves damage slightly.
class spell_rog_dual_strike_hand : public SpellScript
{
    PrepareSpellScript(spell_rog_dual_strike_hand);

    void HandleRescale(SpellEffIndex /*effIndex*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!rogue || !target)
            return;

        WeaponAttackType const attackType =
            GetSpellInfo()->Id == RogueData::SPELL_MUTILATE_OH ? OFF_ATTACK : BASE_ATTACK;
        Item const* weapon = rogue->GetWeaponForAttack(attackType, true);
        if (!weapon)
            return;

        float const weaponSpeed = float(weapon->GetTemplate()->Delay) / 1000.0f;
        float const referenceSpeed = float(RogueData::MUTILATE_NORMALIZED_SPEED_MS) / 1000.0f;
        float const averageWeapon = 0.5f * (rogue->GetWeaponDamageRange(attackType, MINDAMAGE) +
            rogue->GetWeaponDamageRange(attackType, MAXDAMAGE));
        float const attackPower = rogue->GetTotalAttackPowerValue(attackType) / 14.0f;
        float const actual = averageWeapon + attackPower * rogue->GetAPMultiplier(attackType, true);

        float multiplier = 1.0f;
        if (weaponSpeed > 0.0f && actual > 0.0f)
            multiplier = ((averageWeapon / weaponSpeed + attackPower) * referenceSpeed) / actual;

        multiplier *= 1.0f + float(RogueData::MUTILATE_PER_POISON_PCT) * float(Rogue::CountOwnPoisons(rogue, target))
            / 100.0f;

        SetHitDamage(int32(float(GetHitDamage()) * multiplier));
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_rog_dual_strike_hand::HandleRescale, EFFECT_0,
            SPELL_EFFECT_WEAPON_PERCENT_DAMAGE);
    }
};

// 203822 - Kingsbane (the parent). The hands (203840 / 203841) strike first; then the old DoT goes and a fresh one
// (0 stacks) is applied, the once-per-cast talents resolve, and Cold Blood is consumed once. The parent rolls its own
// miss / dodge / parry: a parent that did not hit applies no DoT and resolves nothing.
class spell_rog_kingsbane : public SpellScript
{
    PrepareSpellScript(spell_rog_kingsbane);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_KINGSBANE, RogueData::SPELL_KINGSBANE_MH,
            RogueData::SPELL_KINGSBANE_OH, RogueData::SPELL_KINGSBANE_DOT, RogueData::SPELL_COLD_BLOOD,
            RogueData::SPELL_COLD_BLOOD_AFTER });
    }

    // AfterHit runs only for a unit the cast hit (not on a miss, dodge or parry).
    void HandleAfterHit()
    {
        _hit = true;
    }

    void HandleAfterCast()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue)
            return;

        Unit* target = GetExplTargetUnit();
        if (target && _hit)
        {
            target->RemoveAurasDueToSpell(RogueData::SPELL_KINGSBANE_DOT, rogue->GetGUID());
            if (target->IsAlive())
                rogue->CastSpell(target, RogueData::SPELL_KINGSBANE_DOT, TRIGGERED_FULL_MASK);

            Rogue::ResolveDualStrike(rogue, target, RogueData::SPELL_KINGSBANE);
        }

        ConsumeColdBlood(rogue);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_kingsbane::HandleAfterHit);
        AfterCast += SpellCastFn(spell_rog_kingsbane::HandleAfterCast);
    }

    bool _hit = false;
};

// 203842 - Kingsbane's DoT. The tick is fixed when applied (potency, modifiers) and never recalculated, so the
// amount always stays round(base x (1 + 5% x stacks)); Rogue::AddKingsbaneStacks drives it (SetCharges for the
// client's counter, ChangeAmount for the damage) and recovers the stack-free base from the live amount.
class spell_rog_kingsbane_dot : public AuraScript
{
    PrepareAuraScript(spell_rog_kingsbane_dot);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& /*amount*/, bool& canBeRecalculated)
    {
        canBeRecalculated = false;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_kingsbane_dot::CalculateAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// 203829 - Doomblade's bleed (a PERIODIC_DUMMY on the target). Every tick deals the stored per-tick amount through
// 203830, a never-miss, no-crit, no-caster-modifier Physical hit (the stored damage already carries every modifier).
class spell_rog_doomblade : public AuraScript
{
    PrepareAuraScript(spell_rog_doomblade);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_DOOMBLADE_BLEED, RogueData::SPELL_DOOMBLADE_TICK });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* target = GetUnitOwner();
        if (!rogue || !target || !target->IsAlive())
            return;

        int32 const tick = int32(Rogue::GetStoredBleedTick(rogue, target, RogueData::SPELL_DOOMBLADE_BLEED));
        if (tick <= 0)
            return;

        // No triggering aura: Spell.cpp rejects a cast triggered by an aura whose caster is dead, and Doomblade keeps
        // ticking after the rogue dies like Rupture and Garrote do (S1-CODE-REVIEW L2).
        rogue->CastCustomSpell(target, RogueData::SPELL_DOOMBLADE_TICK, &tick, nullptr, nullptr, true);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_rog_doomblade::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// 1752 - Sinister Strike: Blindside's empowered strike. The cast is marked in BeforeCast (the poison guard reads the
// mark at proc time, which is before AfterHit), the strike gains a combo point, applies every Lethal poison at 100%
// and adds a Nature hit equal to its own damage; the buff is spent in AfterCast.
class spell_rog_sinister_strike_blindside : public SpellScript
{
    PrepareSpellScript(spell_rog_sinister_strike_blindside);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_SINISTER_STRIKE, RogueData::SPELL_BLINDSIDE_BUFF,
            RogueData::SPELL_BLINDSIDE_STRIKE });
    }

    void HandleBeforeCast()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        // Only the player's own Sinister Strike spends Blindside (S3 may add triggered strikes).
        if (!rogue || GetSpell()->IsTriggered() || !rogue->HasAura(RogueData::SPELL_BLINDSIDE_BUFF))
            return;

        _empowered = true;
        Rogue::MarkBlindsideEmpowered(rogue, GetSpell());
    }

    void HandleAfterHit()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!_empowered || !rogue || !target || target == rogue)
            return;

        Rogue::GainComboPoints(rogue, target, 1);
        Rogue::ApplyLethalPoisons(rogue, target, Rogue::PoisonSource::Talent);

        // The Nature half equals the strike's real damage (Cold Blood and crit included)
        int32 const damage = GetHitDamage();
        if (damage > 0)
            rogue->CastCustomSpell(target, RogueData::SPELL_BLINDSIDE_STRIKE, &damage, nullptr, nullptr, true);
    }

    void HandleAfterCast()
    {
        if (!_empowered)
            return;

        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue)
            return;

        rogue->RemoveAurasDueToSpell(RogueData::SPELL_BLINDSIDE_BUFF);
        Rogue::ClearBlindsideEmpowered(rogue);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_rog_sinister_strike_blindside::HandleBeforeCast);
        AfterHit += SpellHitFn(spell_rog_sinister_strike_blindside::HandleAfterHit);
        AfterCast += SpellCastFn(spell_rog_sinister_strike_blindside::HandleAfterCast);
    }

    bool _empowered = false;
};

// 32645 - Envenom (Assassination). Server effect order after the SpellMgr swap: 0 the Lethal chance aura, 1 Dashing
// Scoundrel's crit aura (aura half below), 2 the damage. Doomblade's capstone raises the damage per own bleed on the
// target; a rogue that knows Mutilate gets Slice and Dice at its 5 combo point duration.
class spell_rog_envenom_assassination : public SpellScript
{
    PrepareSpellScript(spell_rog_envenom_assassination);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_ENVENOM, RogueData::SPELL_MUTILATE,
            RogueData::SPELL_SLICE_AND_DICE, RogueData::SPELL_DOOMBLADE_203804 });
    }

    void HandleDamage(SpellEffIndex /*effIndex*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!rogue || !target || !rogue->HasAura(RogueData::SPELL_DOOMBLADE_203804))
            return;

        uint8 const bleeds = Rogue::CountOwnBleeds(rogue, target);
        if (!bleeds)
            return;

        float const multiplier = 1.0f + float(RogueData::DOOMBLADE_CAPSTONE_PCT_PER_BLEED) * float(bleeds) / 100.0f;
        SetHitDamage(int32(float(GetHitDamage()) * multiplier));
    }

    void HandleAfterHit()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        if (_sliceAndDiceApplied || !rogue || !rogue->HasSpell(RogueData::SPELL_MUTILATE))
            return;

        _sliceAndDiceApplied = true;

        // The aura, not a cast: 5171's effect 0 (DUMMY, TARGET_UNIT_TARGET_ENEMY) makes it an enemy-targeted
        // spell, so a cast on the rogue fails Spell::CheckCast's explicit target check (BAD_TARGETS), and a cast
        // on the Envenom target fails when Envenom killed it. AddAura builds only the self aura effect (1).
        Aura* sliceAndDice = rogue->AddAura(RogueData::SPELL_SLICE_AND_DICE, rogue);

        // Envenom always gives the 5 point duration (the way the stock Cut to the Chase refreshed it), with the
        // duration modifiers applied.
        if (sliceAndDice)
        {
            sliceAndDice->SetDuration(sliceAndDice->GetSpellInfo()->GetMaxDuration(), true);
            sliceAndDice->SetMaxDuration(sliceAndDice->GetDuration());
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_rog_envenom_assassination::HandleDamage, EFFECT_2,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_rog_envenom_assassination::HandleAfterHit);
    }

    bool _sliceAndDiceApplied = false;
};

// Envenom's buff: server effect 1 is the flat crit modifier for the poisons (Dashing Scoundrel), 0 without the talent.
class spell_rog_envenom_assassination_aura : public AuraScript
{
    PrepareAuraScript(spell_rog_envenom_assassination_aura);

    void CalculateCrit(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        amount = rogue ? Rogue::GetRankAmount(rogue, { RogueData::SPELL_DASHING_SCOUNDREL,
            RogueData::SPELL_DASHING_SCOUNDREL_203821 }, EFFECT_0) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_envenom_assassination_aura::CalculateCrit, EFFECT_1,
            SPELL_AURA_ADD_FLAT_MODIFIER);
    }
};

// 1943 - Rupture (beside the stock aura script): Indiscriminate Carnage copies a full Rupture onto up to 1 / 2 other
// enemies near the primary that are in combat with the rogue or the group and carry none of the rogue's.
// The copies are applied as auras (AddAura), not cast: a triggered cast would still pass CheckRange (melee reach,
// in front of the rogue) and line of sight, which the doc's "nearby enemies" (within 8 yd of the primary) does not
// ask for. The aura is created inside the parent's AfterHit, before the cast's finish phase clears the combo points,
// with the rogue as caster: its duration (CalcSpellDuration + SPELLMOD_DURATION) and its periodic amount (CalcValue's
// per-point part, potency, the stock spell_rog_rupture CalculateAmount, the rogue's DoT modifiers) are computed from
// the same points and the same caster as the primary's. No recursion and no talent rolls (no Spell, no dispatcher).
class spell_rog_rupture_carnage : public SpellScript
{
    PrepareSpellScript(spell_rog_rupture_carnage);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_RUPTURE, RogueData::SPELL_INDISCRIMINATE_CARNAGE,
            RogueData::SPELL_INDISCRIMINATE_CARNAGE_203819 });
    }

    void HandleAfterHit()
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        Unit* primary = GetHitUnit();
        if (_spread || !rogue || !primary || GetSpell()->IsTriggered())
            return;

        int32 const extra = Rogue::GetRankAmount(rogue, { RogueData::SPELL_INDISCRIMINATE_CARNAGE,
            RogueData::SPELL_INDISCRIMINATE_CARNAGE_203819 }, EFFECT_0);
        if (extra <= 0)
            return;

        _spread = true;

        float const radius = float(RogueData::INDISCRIMINATE_CARNAGE_RADIUS_YD);
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(primary, rogue, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(primary, nearby, check);
        Cell::VisitObjects(primary, searcher, radius);

        nearby.remove_if([&](Unit* unit)
        {
            return unit == primary || !unit->IsAlive() || !rogue->IsValidAttackTarget(unit) ||
                !Engagement::IsEngagedWithOwnerOrGroup(unit, rogue) ||
                unit->HasAura(RogueData::SPELL_RUPTURE, rogue->GetGUID());
        });
        nearby.sort([primary](Unit const* a, Unit const* b)
        {
            return primary->GetExactDistSq(a) < primary->GetExactDistSq(b);
        });

        int32 copies = 0;
        for (Unit* unit : nearby)
        {
            if (copies >= extra)
                break;

            Aura* copy = rogue->AddAura(RogueData::SPELL_RUPTURE, unit);
            if (!copy)
                continue;

            // The target-side duration mods a cast applies at hit (Spell::DoSpellHitOnUnit); diminishing returns
            // do not apply to Rupture.
            int32 const duration = rogue->ModSpellDuration(copy->GetSpellInfo(), unit, copy->GetMaxDuration(), false,
                copy->GetEffectMask());
            if (duration != copy->GetMaxDuration())
            {
                copy->SetMaxDuration(duration);
                copy->SetDuration(duration);
            }

            ++copies;
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_rog_rupture_carnage::HandleAfterHit);
    }

    bool _spread = false;
};

// 703 - Garrote (Cut Throat). The stock "caster behind the target" attribute is cleared in data so a triggered Garrote
// (Envenom's Cut Throat roll) is legal from any side: the player's own cast keeps the check here (the core's own test)
// and ONLY_STEALTHED stays in the DBC. A triggered cast is a full Garrote (damage and duration) without the combo
// point and without the silence.
class spell_rog_garrote_cut_throat : public SpellScript
{
    PrepareSpellScript(spell_rog_garrote_cut_throat);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!caster || !caster->IsPlayer() || !target || target == caster || GetSpell()->IsTriggered())
            return SPELL_CAST_OK;

        if (target->HasInArc(float(M_PI), caster))
            return SPELL_FAILED_NOT_BEHIND;

        return SPELL_CAST_OK;
    }

    // Effect 1 (ADD_COMBO_POINTS runs at hit) and effect 2 (the silence is a TRIGGER_SPELL, which only runs in the
    // launch phase) are skipped for a triggered cast of a player.
    void PreventForTriggered(SpellEffIndex effIndex)
    {
        Unit* caster = GetCaster();
        if (caster && caster->IsPlayer() && GetSpell()->IsTriggered())
            PreventHitDefaultEffect(effIndex);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_rog_garrote_cut_throat::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_rog_garrote_cut_throat::PreventForTriggered, EFFECT_1,
            SPELL_EFFECT_ADD_COMBO_POINTS);
        OnEffectLaunchTarget += SpellEffectFn(spell_rog_garrote_cut_throat::PreventForTriggered, EFFECT_2,
            SPELL_EFFECT_TRIGGER_SPELL);
    }
};

// 51662 - Hunger for Blood: the buff halves the tick interval of the rogue's poisons and bleeds (a percent
// ACTIVATION_TIME modifier). Effects already running keep their old interval until recalculated, so the rogue's
// DoTs on every engaged unit are recalculated when the buff comes and goes.
class spell_rog_hunger_for_blood : public AuraScript
{
    PrepareAuraScript(spell_rog_hunger_for_blood);

    void HandleChange(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* rogue = GetRoguePlayer(GetTarget()))
            Rogue::SetHungerForBlood(rogue);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_rog_hunger_for_blood::HandleChange, EFFECT_0,
            SPELL_AURA_ADD_PCT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_rog_hunger_for_blood::HandleChange, EFFECT_0,
            SPELL_AURA_ADD_PCT_MODIFIER, AURA_EFFECT_HANDLE_REAL);
    }
};

// 203807 - Poison Bomb. The castable is also the cloud (one row, one visual: the vial flies, the cloud stays where
// the target stood). At impact every enemy already engaged with the rogue or the group within the radius takes the
// impact applications of Deadly Poison, then three fixed-cadence pulses at the stored point add one each. The row
// carries "no initial aggro", so the cast's own area hits never pull an unengaged pack.
class spell_rog_poison_bomb : public SpellScript
{
    PrepareSpellScript(spell_rog_poison_bomb);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_DEADLY_POISON });
    }

    void HandleImpact(SpellEffIndex /*effIndex*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        WorldLocation const* dest = GetHitDest();
        if (!rogue || !dest)
            return;

        float const x = dest->GetPositionX();
        float const y = dest->GetPositionY();
        float const z = dest->GetPositionZ();
        ApplyBombStacks(rogue, x, y, z, int32(RogueData::POISON_BOMB_IMPACT_STACKS));

        ObjectGuid const guid = rogue->GetGUID();
        uint32 const mapId = rogue->GetMapId();
        uint32 const instanceId = rogue->GetInstanceId();
        for (int32 pulse = 1; pulse <= int32(RogueData::POISON_BOMB_PULSES); ++pulse)
        {
            rogue->m_Events.AddEventAtOffset([guid, mapId, instanceId, x, y, z]()
            {
                Player* caster = ObjectAccessor::FindPlayer(guid);
                if (!caster || !caster->IsAlive() || caster->GetMapId() != mapId ||
                    caster->GetInstanceId() != instanceId)
                    return;

                ApplyBombStacks(caster, x, y, z, 1);
            }, Milliseconds(int32(RogueData::POISON_BOMB_PULSE_MS) * pulse));
        }
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_rog_poison_bomb::HandleImpact, EFFECT_0,
            SPELL_EFFECT_PERSISTENT_AREA_AURA);
    }
};

// 203836 - Shattering Vial's splash: only enemies already in combat with the rogue take it.
class spell_rog_shattering_vial : public SpellScript
{
    PrepareSpellScript(spell_rog_shattering_vial);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        targets.remove_if([caster](WorldObject* object)
        {
            Unit* unit = object->ToUnit();
            return !unit || !unit->IsInCombatWith(caster);
        });
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_rog_shattering_vial::FilterTargets, EFFECT_0,
            TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// -51634 - Focused Attacks (fork of the stock spell_rog_focused_attacks): the hands of Mutilate and Kingsbane and
// Fan of Knives (both hands) never proc it; they roll it once per cast in Rogue::RollFocusedAttacks.
class spell_rog_focused_attacks_rework : public AuraScript
{
    PrepareAuraScript(spell_rog_focused_attacks_rework);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo)
            return true;

        uint32 const id = spellInfo->Id;
        return !IsDualStrikeHand(id) && id != RogueData::SPELL_FAN_OF_KNIVES &&
            id != SPELL_ROGUE_FAN_OF_KNIVES_OFFHAND;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rog_focused_attacks_rework::CheckProc);
    }
};

// 13218 - Wound Poison's debuff: Improved Poisons' capstone adds half of the rogue's Mastery to the bleed damage
// bonus (aura 271). Computed when applied.
class spell_rog_wound_poison_mastery : public AuraScript
{
    PrepareAuraScript(spell_rog_wound_poison_mastery);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_IMPROVED_POISONS_14115 });
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Player* rogue = GetRoguePlayer(GetCaster());
        if (!rogue || !rogue->HasAura(RogueData::SPELL_IMPROVED_POISONS_14115))
            return;

        float const mastery = std::max(0.0f, rogue->GetMasteryPercentage());
        amount += int32(std::lround(mastery / float(RogueData::WOUND_MASTERY_DIVISOR)));
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rog_wound_poison_mastery::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_FROM_CASTER);
    }
};

// 203846 - Vile Poisons helper (rank 3, linked to 16515): the capstone adds the rogue's Mastery to the poison and
// Envenom damage bonus. Mastery is not an aura amount, so a 1 s poll moves both modifiers when it changes
// (the Heart of the Wild mastery precedent); a modifier is only rewritten when its value moved.
class spell_rog_vile_poisons_mastery : public AuraScript
{
    PrepareAuraScript(spell_rog_vile_poisons_mastery);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ RogueData::SPELL_VILE_POISONS_16515 });
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Player* rogue = GetRoguePlayer(GetTarget());
        Aura* vilePoisons = rogue ? rogue->GetAura(RogueData::SPELL_VILE_POISONS_16515) : nullptr;
        if (!vilePoisons)
            return;

        int32 const mastery = int32(std::lround(std::max(0.0f, rogue->GetMasteryPercentage())));
        for (uint8 index : { EFFECT_0, EFFECT_1 })
        {
            AuraEffect* effect = vilePoisons->GetEffect(index);
            if (!effect)
                continue;

            int32 const wanted = effect->GetSpellInfo()->Effects[index].CalcValue() + mastery;
            if (effect->GetAmount() != wanted)
                effect->ChangeAmount(wanted);
        }
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_rog_vile_poisons_mastery::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

void AddSC_rogue_assassination_spell_scripts()
{
    RegisterSpellScript(spell_rog_cold_blood_rework);
    RegisterSpellScript(spell_rog_remorseless_attacks_rework);
    RegisterSpellScript(spell_rog_mutilate_rework);
    RegisterSpellScript(spell_rog_dual_strike_hand);
    RegisterSpellScript(spell_rog_kingsbane);
    RegisterSpellScript(spell_rog_kingsbane_dot);
    RegisterSpellScript(spell_rog_doomblade);
    RegisterSpellScript(spell_rog_sinister_strike_blindside);
    RegisterSpellAndAuraScriptPair(spell_rog_envenom_assassination, spell_rog_envenom_assassination_aura);
    RegisterSpellScript(spell_rog_rupture_carnage);
    RegisterSpellScript(spell_rog_garrote_cut_throat);
    RegisterSpellScript(spell_rog_hunger_for_blood);
    RegisterSpellScript(spell_rog_poison_bomb);
    RegisterSpellScript(spell_rog_shattering_vial);
    RegisterSpellScript(spell_rog_focused_attacks_rework);
    RegisterSpellScript(spell_rog_wound_poison_mastery);
    RegisterSpellScript(spell_rog_vile_poisons_mastery);
}
