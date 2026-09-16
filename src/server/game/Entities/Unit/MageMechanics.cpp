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
#include "ObjectGuid.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "Util.h"
#include <algorithm>
#include <map>

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

        // Arcane Mage rework (docs/arcane-mage-rework-design.md) - real stock spell ids this file's
        // Arcane blocks need by number. Keep in sync with spell_mage.cpp's own MageSpells enum if
        // either changes; spell_mage.cpp's SPELL_MAGE_ARCANE_BLAST_STACKS / SPELL_MAGE_ARCANE_POWER.
        constexpr uint32 SPELL_ARCANE_BLAST_STACKS = 36032;
        constexpr uint32 SPELL_ARCANE_POWER = 12042;
        // Phase 3 Batch C - keep in sync with spell_mage.cpp's own SPELL_MAGE_ARCANE_MASTERY.
        constexpr uint32 SPELL_ARCANE_MASTERY = 200085;

        // Fire Mage rework (docs/reworks/fire-mage-rework.md) - keep in sync with spell_mage.cpp's
        // SPELL_MAGE_IGNITE / SPELL_MAGE_IGNITE_TICK / SPELL_MAGE_KINDLING.
        constexpr uint32 SPELL_IGNITE_DOT = 12654;
        constexpr uint32 SPELL_IGNITE_TICK = 200098;
        constexpr uint32 SPELL_KINDLING = 200097;
        constexpr uint32 SPELL_FIRE_BLAST = 2136;
        constexpr uint32 SPELL_BLAZING_SPEED_ESCAPE = 200113;
        // Phase 3 - keep in sync with spell_mage.cpp's own SPELL_MAGE_PYROBLAST /
        // SPELL_MAGE_HOT_STREAK_PROC / MAGE_ICON_HOT_STREAK.
        constexpr uint32 SPELL_PYROBLAST = 11366;
        constexpr uint32 SPELL_HOT_STREAK_PROC = 48108;
        constexpr uint32 MAGE_ICON_HOT_STREAK = 2999;
        // Sec 3.3: 4 sec, 1 sec tick interval, 4 ticks. Kept as the count rather than derived from
        // the aura's duration/amplitude so a refresh mid-cadence still means "4 more payouts".
        constexpr uint8 IGNITE_TICKS = 4;
        // Sec 4.1's client-display fallback: stack count = banked damage / this. The 3.3.5 aura
        // update packet carries a stack byte but never effect amounts, so this is the only number
        // the client can show.
        constexpr uint32 IGNITE_DAMAGE_PER_DISPLAY_STACK = 100;

        struct IgniteBank
        {
            uint32 remaining = 0;
            uint8 ticksRemaining = 0;
        };

        // Keyed by (caster, target) GUID pair - one bank per mage per victim, exactly like one
        // Ignite aura per mage per victim. Entries only live while the aura does (ClearIgnite runs
        // from the aura's own AfterEffectRemove), so this never grows past the number of live
        // Ignites in the world.
        std::map<std::pair<ObjectGuid, ObjectGuid>, IgniteBank> igniteBanks;

        std::pair<ObjectGuid, ObjectGuid> IgniteKey(Unit const* caster, Unit const* target)
        {
            return { caster->GetGUID(), target->GetGUID() };
        }

        void SyncIgniteDisplay(Aura* ignite, IgniteBank const& bank)
        {
            uint32 stacks = std::clamp<uint32>(bank.remaining / IGNITE_DAMAGE_PER_DISPLAY_STACK, 1, 255);
            if (ignite->GetStackAmount() != stacks)
                ignite->SetStackAmount(uint8(stacks));
        }
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

        // Arcane Resonance (Arcane Mage rework, docs/arcane-mage-rework-design.md Row 3, all 3
        // ranks) - "While you have 4 stacks of Arcane Blast, your Arcane damage is increased by
        // 3/6/9%." Real stock "Arcane Blast" stacking buff (36032, apps/dbc-tools
        // source/spells/mage.csv) caps at exactly 4 stacks (raw_overrides.CumulativeAura /
        // SpellInfo::StackAmount) - read live rather than a static aura since stacks rise and fall
        // mid-fight. Design also says "spells that consume your Arcane Blast stacks benefit from
        // this bonus" (Arcane Missiles, Arcane Overload) - not yet covered, since nothing in this
        // rework actually drops the caster's Arcane Blast stacks on cast yet (that mechanic itself
        // isn't built anywhere - see design doc's Progress notes). Once it is, that consuming cast's
        // own script needs to read this stack count *before* dropping it, same ordering concern as
        // Missile Barrage's Mastery clause.
        if (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_ARCANE)
            if (Aura const* arcaneBlastStacks = caster->GetAura(SPELL_ARCANE_BLAST_STACKS))
                if (arcaneBlastStacks->GetStackAmount() >= arcaneBlastStacks->GetSpellInfo()->StackAmount)
                    if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 3007, EFFECT_0))
                        AddPct(doneTotalMod, aurEff->GetAmount());

        // Arcane Mind (Arcane Mage rework, Row 4, all 3 ranks) - "Your magic damage is increased by
        // up to 4/8/12%, scaling with your current mana percentage." Scales *up* with mana%, not
        // down - confirmed with the user (2026-09-08), matches the Rotation Model section's "Arcane
        // Mind's high-mana scaling means the player weaves mana stones... to hold mana high while
        // draining" framing. Player-only (mana% is meaningless for a non-mana guardian).
        if (Player* player = caster->ToPlayer())
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 71, EFFECT_1))
                if (uint32 maxMana = player->GetMaxPower(POWER_MANA))
                {
                    float manaPct = float(player->GetPower(POWER_MANA)) / float(maxMana);
                    AddPct(doneTotalMod, aurEff->GetAmount() * manaPct);
                }

        // Arcane Flows capstone (Arcane Mage rework, Row 7, rank 2 only - granted at max rank per
        // System Rulings) - "Your Arcane Power increases your magic damage dealt by an additional
        // 5%." Same live HasAura idiom as Shattered Barrier's capstone above (Ice Barrier check).
        if (caster->HasAura(SPELL_ARCANE_POWER))
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 2940, EFFECT_2))
                AddPct(doneTotalMod, aurEff->GetAmount());

        // Arcane Concentration (Row 2) / Missile Barrage (Row 5) shared Mastery clause, Phase 3
        // Batch C - see spell_mage.cpp's GrantArcaneMasteryMarker (granted right before Clearcasting
        // or Missile Barrage's own buff is consumed, not read live off either of those - both can
        // empower a channeled Arcane Missiles cast, whose consumption happens before any tick's
        // damage calc runs). Consumed immediately on read, not left to expire naturally, so it only
        // ever applies to the one cast it was granted for.
        if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_DUMMY, SPELLFAMILY_MAGE, 1976, EFFECT_0))
        {
            AddPct(doneTotalMod, aurEff->GetAmount());
            caster->RemoveAurasDueToSpell(SPELL_ARCANE_MASTERY);
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

namespace Mage
{
    void AddIgniteDamage(Unit* caster, Unit* target, uint32 amount)
    {
        if (!caster || !target || !amount || !target->IsAlive())
            return;

        Aura* ignite = target->GetAura(SPELL_IGNITE_DOT, caster->GetGUID());
        if (!ignite)
        {
            // Fresh application - triggered and ALWAYS_HIT (12654's own AttributesEx3), so it's on
            // the target synchronously unless the target is immune, in which case nothing banks.
            caster->CastSpell(target, SPELL_IGNITE_DOT, true);
            ignite = target->GetAura(SPELL_IGNITE_DOT, caster->GetGUID());
            if (!ignite)
                return;
            igniteBanks[IgniteKey(caster, target)] = IgniteBank();
        }
        else
            // Sec 4.1 "On a Fire critical strike" step 2/3: duration back to the full 4 sec, but
            // RefreshDuration (not RefreshTimers) so the periodic timer keeps its schedule.
            ignite->RefreshDuration();

        IgniteBank& bank = igniteBanks[IgniteKey(caster, target)];
        bank.remaining += amount;
        bank.ticksRemaining = IGNITE_TICKS;
        SyncIgniteDisplay(ignite, bank);
    }

    uint32 GetIgniteRemaining(Unit const* caster, Unit const* target)
    {
        if (!caster || !target)
            return 0;
        auto it = igniteBanks.find(IgniteKey(caster, target));
        return it != igniteBanks.end() ? it->second.remaining : 0;
    }

    uint32 ConsumeIgnite(Unit* caster, Unit* target)
    {
        uint32 remaining = GetIgniteRemaining(caster, target);
        // RemoveAura -> spell_mage_ignite_dot's AfterEffectRemove -> ClearIgnite erases the bank.
        target->RemoveAura(SPELL_IGNITE_DOT, caster->GetGUID());
        ClearIgnite(caster->GetGUID(), target->GetGUID());
        return remaining;
    }

    uint32 TakeIgniteTick(Unit* caster, Unit* target, Aura* /*ignite*/)
    {
        if (!caster || !target)
            return 0;
        auto it = igniteBanks.find(IgniteKey(caster, target));
        if (it == igniteBanks.end())
            return 0;

        IgniteBank& bank = it->second;
        if (!bank.remaining)
            return 0;

        // Sec 4.1 "On tick": deal remaining / ticks_remaining, subtract, decrement. The final tick
        // takes whatever is left so rounding never strands damage in the bank.
        uint32 tick = bank.ticksRemaining <= 1 ? bank.remaining : bank.remaining / bank.ticksRemaining;
        bank.remaining -= tick;
        bank.ticksRemaining = bank.ticksRemaining ? bank.ticksRemaining - 1 : 0;
        if (Aura* ignite = target->GetAura(SPELL_IGNITE_DOT, caster->GetGUID()))
            SyncIgniteDisplay(ignite, bank);
        return tick;
    }

    void ClearIgnite(ObjectGuid casterGuid, ObjectGuid targetGuid)
    {
        igniteBanks.erase({ casterGuid, targetGuid });
    }

    void GrantKindling(Unit* caster, uint32 stacks)
    {
        if (!caster || !stacks)
            return;

        Aura* kindling = caster->GetAura(SPELL_KINDLING, caster->GetGUID());
        if (!kindling)
        {
            caster->CastSpell(caster, SPELL_KINDLING, true);
            kindling = caster->GetAura(SPELL_KINDLING, caster->GetGUID());
            if (!kindling)
                return;
            --stacks; // the fresh application is stack 1
        }
        if (stacks)
            kindling->ModStackAmount(int32(stacks));
    }

    bool ApplySpellCritChanceMods(Unit const* caster, SpellInfo const* spellProto, float& critChance)
    {
        if (spellProto->Id == SPELL_FIRE_BLAST)
        {
            critChance = 100.0f;
            return true;
        }
        // Hot Streak (sec 5 (8,2)) - "This Pyroblast always critically strikes." Same HasAura gate
        // ApplyDoneDamagePctMods' Mastery bonus uses; spell_mage_pyroblast consumes the buff after
        // this cast either way.
        if (spellProto->Id == SPELL_PYROBLAST && caster && caster->HasAura(SPELL_HOT_STREAK_PROC))
        {
            critChance = 100.0f;
            return true;
        }
        return false;
    }

    bool CanCastWhileMoving(Unit const* caster, SpellInfo const* spellInfo)
    {
        if (!caster || !spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_MAGE)
            return false;
        if (spellInfo->IsChanneled())
            return false;
        if (!(spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_FIRE))
            return false;
        return caster->HasAura(SPELL_BLAZING_SPEED_ESCAPE);
    }
}
