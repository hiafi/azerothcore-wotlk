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

#ifndef __MAGEMECHANICS_H
#define __MAGEMECHANICS_H

#include "Define.h"
#include "SharedDefines.h"

class SpellInfo;
class Unit;

/*
 * Mage-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors of the engine call sites in
 * Unit.cpp (SpellPctDamageModsDone, MeleeDamageBonusTaken, Kill) that need live state (frozen
 * checks, Mastery%, kill context) a static aura value can't express. Consolidated here, one
 * function per hook, instead of growing Unit.cpp's existing per-class switch cases inline - the
 * whole set of Mage special cases (and their one shared helper, IsFrozenTarget) can be read in one
 * file instead of scattered hundreds of lines apart across three different functions.
 *
 * Lives in game/Entities/Unit/ (core), not scripts/ - Unit.cpp (core) can't depend on scripts/, so
 * this can't live next to spell_mage.cpp. spell_mage.cpp (scripts, which may depend on core) calls
 * into this file's IsFrozenTarget() too rather than keeping its own separate copy.
 *
 * Other classes with the same "special-cased directly in Unit.cpp" problem should get their own
 * equivalent file (WarlockMechanics, PriestMechanics, ...) rather than growing the existing
 * switch-case blocks further.
 */
namespace Mage
{
    // docs/frost-mage-redesign.md sec 4: "The following count as frozen for Shatter, Frostbite's
    // Mastery, Ice Lance's bonus damage, and Deep Freeze's usability requirement: a real freeze
    // effect, Fingers of Frost, and Shattering Cold." `caster` may be null (only the real-freeze
    // case is checked then).
    bool IsFrozenTarget(Unit const* caster, Unit const* victim);

    // Unit::SpellPctDamageModsDone's SPELLFAMILY_MAGE case - Ice Lance's triple damage, Torment
    // the Weak's Mage-side gate (both pre-existing/stock), and every Frost Mage rework "+X%
    // damage" capstone (Biting Cold, Frostbite, Ice Shards, Arctic Reach, Permafrost's Ice Lance
    // bonus, Shattered Barrier's Ice-Barrier-active bonus).
    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, float& doneTotalMod);

    // Unit::MeleeDamageBonusTaken's Frost Warding capstone check.
    void ApplyMeleeDamageTakenPctMods(Unit* defender, Unit* attacker, SpellSchoolMask damageSchoolMask, float& takenTotalMod);

    // Unit::Kill's Frost Channeling capstone check.
    void OnKill(Unit* killer, Unit* victim, SpellInfo const* spellProto);
}

#endif
