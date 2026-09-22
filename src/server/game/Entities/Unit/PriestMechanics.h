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

#ifndef __PRIESTMECHANICS_H
#define __PRIESTMECHANICS_H

#include "Define.h"
#include "SharedDefines.h"

class Aura;
class SpellInfo;
class Unit;
enum DamageEffectType : uint8;

/*
 * Priest-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors MageMechanics.h's shape
 * (see that file's own header comment for the general rationale: Unit.cpp/core can't depend on
 * scripts/, so this can't live next to spell_priest_new.cpp).
 */
namespace Priest
{
    // Spell ids shared across translation units - defined once here so the cross-class and core
    // call sites can't drift from the priest scripts' own copy.

    // Shared "death-prevention already used" lockout (2 min) between Spirit of Redemption (Holy
    // 4,1), Ardent Defender and Cheat Death - each checks and casts it (spell_priest_holy.cpp,
    // spell_paladin.cpp, spell_rogue.cpp).
    constexpr uint32 SPELL_CHEATED_DEATH_MARKER = 200193;

    // Echo of Light (Holy 8,3) reservoir ticks - fixed cadence, done/taken bonus snapshotted at
    // application (SpellAuraEffects.cpp's IsFixedCadencePeriodic list).
    constexpr uint32 SPELL_ECHO_OF_LIGHT_HEAL = 200218;
    constexpr uint32 SPELL_ECHO_OF_LIGHT_DAMAGE = 200219;

    // Unit::SpellPctDamageModsDone's whole (former) SPELLFAMILY_PRIEST case: Void Eruption's
    // Voidform buff (docs/reworks/priest-new-spells.md - "increases your periodic Shadow damage by
    // 10% for 10 sec"; no native WotLK AuraType computes "+X% periodic damage done", hence the live
    // marker-aura-by-icon read), plus the stock Mind Flay / Smite / Shadow Word: Death glyph
    // clauses and Twisted Faith's Mind Flay half, migrated out of Unit.cpp verbatim
    // (.agents/plans/priest-rework/priest-rework.PLAN.md sec 6.8).
    //
    // The call site now sits *outside* Unit::SpellPctDamageModsDone's per-family switch (PLAN sec
    // 6.7), so this runs for every spell family - each clause carries its own gate. Everything
    // here is currently priest-family-only and lives behind one shared family check; a later
    // cross-class clause (Holy's Divine Fury, which buffs Holy-school damage from any class) goes
    // *above* that check.
    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, DamageEffectType damagetype, float& doneTotalMod);

    // Unit::SpellDoneCritChance's priest hook, next to Mage's own equivalent - Discipline's Inner
    // Focus (2,1) turns its charge into a guaranteed Flash Heal crit
    // (docs/reworks/priest-disc-rework.md). An absolute override, applied last, so no other
    // modifier can push it off 100.
    void ApplySpellCritChanceMods(Unit const* caster, SpellInfo const* spellProto, float& critChance);

    // Unit::SpellTakenCritChance's "Custom crit by class" SPELLFAMILY_PRIEST case - Renewed Hope's
    // Weakened-Soul crit bonus (migrated out of that function's OVERRIDE_CLASS_SCRIPTS loop, PLAN
    // sec 6.8) and Focused Power's (5,0) Prayer of Healing capstone. `victim` is the unit being
    // healed/hit, `caster` the priest.
    void ApplySpellTakenCritChanceMods(Unit const* victim, Unit const* caster, SpellInfo const* spellProto, float& critChance);

    // Spirit Shell (Discipline 10,1): "your direct healing spells no longer heal - instead they
    // create an absorption shield on the target for the amount that would have been healed."
    // Called from Spell::DoAllEffectOnTarget's heal branch with the post-crit heal amount; returns
    // true (and zeroes `heal`) when the heal was converted, so the heal itself lands for 0 and
    // Divine Aegis sees nothing to work with.
    bool TryConvertHealToSpiritShell(Unit* caster, Unit* target, SpellInfo const* spellProto, uint32& heal);

    // Holy rework (docs/reworks/priest-holy-rework.md, priest-rework.HOLY.md "Core hardcode
    // migration owed by this pass") - Test of Faith's (8,2) healing clause, migrated out of
    // Unit::SpellPctHealingModsDone's OVERRIDE_CLASS_SCRIPTS loop (`case 21: case 6935: case
    // 6918:`, one misc value per rank). One call site in that function.
    void ApplyDoneHealingPctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, float& doneTotalMod);

    // Test of Faith (8,2) capstone: "10% less magic damage taken while casting Smite, Holy Fire or
    // any Priest healing spell." `victim` is the priest taking incoming spell damage; `attacker` is
    // whoever cast the incoming spell (any class). Called from Unit::SpellDamageBonusTaken.
    void ApplySpellDamageTakenPctMods(Unit* victim, Unit* attacker, SpellInfo const* spellProto, float& takenMod);

    // Renew extension pool (docs/reworks/priest-holy-rework.md 5.3): shared by Holy Concentration
    // (6,0, spell_pri_holy_concentration_extend) and Empowered Renew's capstone (8,0,
    // spell_pri_empowered_renew_capstone), both in spell_priest_holy.cpp - a free function here
    // (rather than a member on spell_pri_renew, spell_priest.cpp) because both callers need to
    // reach the pool from a different translation unit than spell_pri_renew is defined in;
    // Aura::GetScript<T>() (a dynamic_cast) needs T's complete definition, which isn't available
    // across files without a shared header. Needs no per-instance state: "how much extension this
    // Renew has already used" is re-derived each call from the gap between the aura's current and
    // base max duration. `renew` is the caster's live Renew Aura on some target (`Unit::GetAura`);
    // `ms` is the requested extension, capped so total duration never exceeds base + 6000ms (PLAN's
    // "Total duration may never exceed 21 seconds from application", base Renew being 15 s).
    void ExtendRenewDuration(Aura* renew, int32 ms);
}

#endif
