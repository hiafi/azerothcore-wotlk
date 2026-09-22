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
}

#endif
