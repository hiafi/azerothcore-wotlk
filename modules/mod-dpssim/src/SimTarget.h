/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MODULE_DPSSIM_SIMTARGET_H
#define MODULE_DPSSIM_SIMTARGET_H

#include "Define.h"
#include "Position.h"

class Creature;
class Map;
class TempSummon;

// Passive target dummy for the sim to cast at. Built on this fork's own level-80 training dummy
// (creature_template entry 900003, added by data/sql/updates/db_world/2026_09_01_26.sql for
// exactly this purpose - "Training Dummy" / "Level 80", `AIName = npc_training_dummy`) rather than
// the base game's plain "Target Dummy" (entry 2673). That base entry was tried first and rejected:
// its faction (14) fails Unit::_IsValidAttackTarget's friendly-target check, so every hostile
// spell cast at it returns SPELL_FAILED_BAD_TARGETS - entries 900001/900002/900003 use faction 31
// (Critter) instead, the same "always attackable, never retaliates" trick real non-combat critters
// use, specifically so players (and now this sim) can cast damage at them at all. See
// npc_training_dummy (src/server/scripts/World/npcs_special.cpp) for the AI: it zeroes `damage` in
// its DamageTaken() hook so the dummy never dies, and runs its own 5s combat-timeout bookkeeping -
// SimTarget doesn't need to reimplement any of that.
//
// Level/armor are still overridden programmatically after spawn (SetLevel/SetResistance), so this
// entry is just the spawn shell, not a hardcoded level-80-only assumption - see Config below.
//
// **Load-bearing gotcha, matters to EventRecorder, not just this class**: DamageTaken() runs
// *before* ScriptMgr::OnDamage() inside Unit::DealDamage (see the "its rare to modify damage in
// hooks, however training dummy's sets damage to 0" comment at the top of Unit::DealDamage) - by
// the time OnDamage fires, `damage` has already been zeroed for any hit against this dummy.
// EventRecorder reads the real, pre-zero damage (and isCrit) from the earlier
// ModifySpellDamageTaken hook instead, which fires upstream of DamageTaken - see its own doc
// comment for why OnDamage isn't used at all here.
//
// This fork's PvE-always-hit override (Unit.cpp, "Custom: Hit/Expertise are no longer meaningful
// player stats") already makes any non-player victim of a player's spell-cast damage un-missable
// and un-dodgeable/un-parryable for free - see the design doc's section 5.3 "boss mode" guarantee
// and open ruling 41's caveat that this does NOT extend to raw melee auto-attacks. SimTarget does
// not need its own hit-suppression logic for Phase 1's spell-only (Frostbolt) pilot.
class SimTarget
{
public:
    struct Config
    {
        uint8 Level = 80;
        uint32 Armor = 0;
        // Health has no gameplay effect on a target dummy's damage output/mitigation - the
        // training dummy AI (see class comment) zeroes all damage taken regardless, so this is
        // purely a defensive default in case that AI's behavior ever changes.
        uint32 MaxHealth = 100000000;
    };

    // The level-80 training dummy template reused as the spawn shell - see the class comment.
    // Siblings 900001 (level 60) and 900002 (level 70) exist too; this sim always spawns 900003
    // and overrides level/armor itself rather than picking a sibling per Config.Level, since all
    // three share the identical AI/faction/flags setup and only differ in their SQL-row level.
    static constexpr uint32 TARGET_DUMMY_ENTRY = 900003;

    ~SimTarget();

    // Spawns the dummy on `map` at `pos` and applies `config`. Returns false (logging why) on
    // failure - most likely TARGET_DUMMY_ENTRY not existing in this deployment's DB (base data,
    // should always be present, but worth checking explicitly rather than dereferencing null).
    bool Create(Map* map, Position const& pos, Config const& config);

    [[nodiscard]] Creature* GetCreature() const;

private:
    TempSummon* _summon = nullptr;
};

#endif
