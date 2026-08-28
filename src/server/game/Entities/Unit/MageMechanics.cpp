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

#include "MageMechanics.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "Util.h"
#include <algorithm>

namespace Mage
{
    namespace
    {
        // Bare spell-ID literals, not enum constants - this file has no access to spell_mage.cpp's
        // own FrostMageReworkSpells enum (scripts, which this core file can't depend on). Keep in
        // sync with spell_mage.cpp's SPELL_MAGE_FINGERS_OF_FROST_CHARGES / SPELL_MAGE_SHATTERING_COLD
        // if either one ever changes.
        constexpr uint32 SPELL_FINGERS_OF_FROST_CHARGES = 74396;
        constexpr uint32 SPELL_SHATTERING_COLD = 200003;
        constexpr uint32 SPELL_ICE_BARRIER = 11426;
    }

    bool IsFrozenTarget(Unit const* caster, Unit const* victim)
    {
        if (!victim)
            return false;

        // A real freeze/root/stun Frost effect sets AURA_STATE_FROZEN globally (not per-caster -
        // SharedDefines.h's PER_CASTER_AURA_STATE_MASK doesn't include it), so it counts here
        // regardless of who applied it.
        if (victim->HasAuraState(AURA_STATE_FROZEN))
            return true;

        if (caster)
        {
            // Fingers of Frost ("treat the target as if it were Frozen") is a personal charge buff
            // on the caster, not the target.
            if (caster->HasAura(SPELL_FINGERS_OF_FROST_CHARGES))
                return true;

            // Shattering Cold is caster-scoped by design - only the mage who applied it benefits.
            if (victim->HasAura(SPELL_SHATTERING_COLD, caster->GetGUID()))
                return true;
        }

        return false;
    }

    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, float& doneTotalMod)
    {
        Unit* owner = caster->GetOwner() ? caster->GetOwner() : caster;

        // Ice Lance. "Frozen" here is the redesign's unified definition (docs/frost-mage-
        // redesign.md sec 3 "Frozen state") - real freeze, Fingers of Frost, or Shattering Cold -
        // same as Shatter's crit bonus (Unit.cpp) and Frozen Core's capstone (spell_mage.cpp), not
        // just the engine's native AURA_STATE_FROZEN.
        if (spellProto->SpellIconID == 186)
        {
            if (IsFrozenTarget(caster, victim))
            {
                // Glyph of Ice Lance
                if (owner->HasAura(56377) && victim->GetLevel() > owner->GetLevel())
                    doneTotalMod *= 4.0f;
                else
                    doneTotalMod *= 3.0f;
            }

            // Permafrost capstone (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 2,
            // rank 3) - "increasing the damage of your next Ice Lance by 20%." The stack buff
            // (200015, icon 143 - reused from the talent's own icon) is consumed entirely by
            // spell_mage_ice_lance (spell_mage.cpp) after this damage calc runs; read here rather
            // than a static aura since the bonus only applies while stacks are actually banked.
            // Playtest bugfix (2026-08-26, user call): scales with stack count (20% * stacks, up
            // to 100% at 5) rather than a flat 20% regardless of how many were banked, now that
            // Ice Lance clears the whole stack in one cast instead of spending 1 at a time -
            // otherwise banking past 1 stack would have no payoff.
            // Playtest bugfix (2026-08-27, user call): GetAmount() already factors in the current
            // stack count (AuraEffect::CalculateAmount() does `amount *= GetBase()->GetStackAmount()`
            // before returning - see SpellAuraEffects.cpp), so multiplying by GetStackAmount() again
            // here double-counted it (20% * stacks^2 instead of 20% * stacks - e.g. 5 stacks read as
            // +500% instead of the intended +100%).
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 143, EFFECT_0))
                AddPct(doneTotalMod, aurEff->GetAmount());
        }

        // Shattered Barrier (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 7) - "While
        // Ice Barrier is active your damage is increased by 2/4%." Not scoped to Frost (spec says
        // "your damage", not "your Frost damage") - unconditional within this SPELLFAMILY_MAGE
        // case, same live "does the caster have the buff" idiom as Frost Warding's capstone
        // (a cached mod would go stale as Ice Barrier is applied/consumed independently).
        if (caster->HasAura(SPELL_ICE_BARRIER))
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 2945, EFFECT_0))
                AddPct(doneTotalMod, aurEff->GetAmount());

        // Torment the weak
        if (spellProto->SpellFamilyFlags[0] & 0x20600021 || spellProto->SpellFamilyFlags[1] & 0x9000)
            if (victim->HasAuraWithMechanic((1ULL << MECHANIC_SNARE) | (1ULL << MECHANIC_SLOW_ATTACK)))
                if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_GENERIC, 3263, EFFECT_0))
                    AddPct(doneTotalMod, aurEff->GetAmount());

        // Biting Cold (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 2) - +2/4/6% Frost
        // damage against targets affected by a chill effect. Same "any chill on the target, not
        // caster-scoped" check as Torment the Weak above, for consistency with this function's
        // existing idiom rather than a new caster-scoped check.
        if (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST)
            if (victim->HasAuraWithMechanic(1ULL << MECHANIC_SNARE))
                if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 189, EFFECT_0))
                    AddPct(doneTotalMod, aurEff->GetAmount());

        // Frostbite capstone (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 1, rank 3) -
        // "Increases the damage of your Frost spells against frozen targets by Mastery." First
        // real GetMasteryPercentage() consumer. Player-only per the redesign's Mastery section
        // ("Guardians do not inherit it") - a Water Elemental dealing its own Frost damage is a
        // separate caster, so ToPlayer() already excludes it here.
        if (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST)
            if (Player* player = caster->ToPlayer())
                if (caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 119, EFFECT_1))
                    if (IsFrozenTarget(caster, victim))
                        AddPct(doneTotalMod, player->GetMasteryPercentage());

        // Ice Shards capstone (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 5, rank 3)
        // - "Increases damage against frozen targets by 6%."
        if (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST)
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 1236, EFFECT_1))
                if (IsFrozenTarget(caster, victim))
                    AddPct(doneTotalMod, aurEff->GetAmount());

        // Arctic Reach capstone (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 4, rank
        // 2) - "Your Frost damage is increased by up to 10% based on the target's distance,
        // reaching full effect at 30 yards or more." Not a stock aura type (needs live distance at
        // damage-calc time), so it's a plain linear ramp on GetDistance() gated by the rank-2-only
        // dummy marker (icon 154, EFFECT_2 - effects 0/1 are already the range/radius effects on
        // both ranks).
        if (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST)
            if (caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 154, EFFECT_2))
            {
                float distance = caster->GetDistance(victim);
                float bonusPct = std::min(distance / 30.0f, 1.0f) * 10.0f;
                AddPct(doneTotalMod, bonusPct);
            }
    }

    void ApplyMeleeDamageTakenPctMods(Unit* defender, Unit* /*attacker*/, SpellSchoolMask damageSchoolMask, float& takenTotalMod)
    {
        // Frost Warding capstone (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 2) -
        // -20% physical damage taken while Frost Armor (168) or Ice Armor (7302) is active. A
        // rank-2-only SPELL_AURA_DUMMY (EFFECT_2, SpellIconID 501) rather than a plain
        // SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN, so it's checked live here instead of going stale
        // between armor swaps.
        if (defender->IsPlayer() && defender->getClass() == CLASS_MAGE && (damageSchoolMask & SPELL_SCHOOL_MASK_NORMAL))
            if (defender->HasAura(168) || defender->HasAura(7302))
                if (AuraEffect* aurEff = defender->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 501, EFFECT_2))
                    AddPct(takenTotalMod, aurEff->GetAmount());
    }

    void OnKill(Unit* killer, Unit* victim, SpellInfo const* spellProto)
    {
        if (!killer)
            return;

        Player* killerPlr = killer->ToPlayer();
        if (!killerPlr)
            return;

        // Frost Channeling capstone (Frost Mage rework, docs/frost-mage-redesign.md sec 4 Row 3,
        // rank 3) - "Killing an enemy that yields experience or honor with Frost damage restores
        // 12% of your mana." Checked here rather than in a PlayerScript on-kill hook because those
        // don't carry the killing blow's school - spellProto does, threaded this far by DealDamage.
        // isHonorOrXPTarget() covers both the PvE (non-trivial mob) and PvP (real player) cases the
        // spec asks for in one call. A pet/guardian landing the blow doesn't credit this (killer->
        // ToPlayer() is null for them), same "guardians don't inherit" shape as Frostbite's Mastery.
        if (spellProto && (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_FROST))
            if (killerPlr->isHonorOrXPTarget(victim))
                if (killerPlr->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 15, EFFECT_2))
                    killerPlr->EnergizeBySpell(killerPlr, 12519, CalculatePct(killerPlr->GetMaxPower(POWER_MANA), 12), POWER_MANA);
    }
}
