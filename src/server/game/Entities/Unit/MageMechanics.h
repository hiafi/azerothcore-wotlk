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
#include "ObjectGuid.h"
#include "SharedDefines.h"

class Aura;
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

    /*
     * Ignite accumulator - Fire Mage rework, docs/reworks/fire-mage-rework.md sec 4.1. Explicit
     * per-(caster, target) server state { remaining_damage, ticks_remaining } instead of a re-applied
     * DoT aura, so two crits landing in the same batch both bank (no "munching") and the bank can
     * never pay out more than it holds (no "vomit"). The visible Ignite aura (12654) is only the
     * timing/display vehicle: applied once, refreshed in place, ticking as PERIODIC_DUMMY - its
     * script (spell_mage_ignite_dot) calls TakeIgniteTick each tick and deals the payout itself
     * via the Ignite tick spell (200098). Lives here rather than in spell_mage.cpp so Unit.cpp
     * (Burnout's capstone reads the bank from SpellPctDamageModsDone) and mod-playerbots/mod-dpssim
     * (a rotation deciding when to Flashpoint) can read it without depending on scripts/.
     */
    // Banks `amount` into caster's Ignite on target: applies 12654 if it isn't up, otherwise
    // RefreshDuration()s it (tick cadence deliberately untouched), then refreshes ticks_remaining
    // to the full count. Fanned Flames' non-crit Scorch calls this directly - it's the amount, not
    // the crit, that this cares about.
    void AddIgniteDamage(Unit* caster, Unit* target, uint32 amount);
    uint32 GetIgniteRemaining(Unit const* caster, Unit const* target);
    // Flashpoint: returns the whole bank, zeroes it and removes the aura.
    uint32 ConsumeIgnite(Unit* caster, Unit* target);
    // One tick's payout (remaining / ticks_remaining, everything on the final tick) - advances the
    // state and re-syncs the aura's stack-count display. 0 when nothing is banked.
    uint32 TakeIgniteTick(Unit* caster, Unit* target, Aura* ignite);
    // Aura gone (expired, dispelled, target died/despawned) - drop the bank. GUIDs, not Unit*,
    // because the aura's own removal hook can fire after its caster has logged out.
    void ClearIgnite(ObjectGuid casterGuid, ObjectGuid targetGuid);

    // Kindling (sec 4.2) - grants `stacks` stacks of the Kindling buff (200097) to the mage, capped
    // at the aura's own max stack count. Tinderbox and Impact Crater both feed this one pool.
    void GrantKindling(Unit* caster, uint32 stacks);
}

#endif
