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

// Passive target dummy for the sim to cast at. Built on this fork's own training dummies
// (creature_template entries 900001/900002/900003, added by
// data/sql/updates/db_world/2026_09_01_26.sql for exactly this purpose - "Training Dummy" at level
// 60/70/80 respectively, `ScriptName = npc_training_dummy`) rather than the base game's plain "Target
// Dummy" (entry 2673). That base entry was tried first and rejected: its faction (14) fails
// Unit::_IsValidAttackTarget's friendly-target check, so every hostile spell cast at it returns
// SPELL_FAILED_BAD_TARGETS - entries 900001/900002/900003 use faction 31 (Critter) instead, the
// same "always attackable, never retaliates" trick real non-combat critters use, specifically so
// players (and now this sim) can cast damage at them at all. See npc_training_dummy
// (src/server/scripts/World/npcs_special.cpp) for the AI: it zeroes `damage` in its DamageTaken()
// hook so the dummy never dies, and runs its own 5s combat-timeout bookkeeping.
//
// **2026-09-13**: all three brackets now spawn sim-exclusive entries (900004/900005/900006) running
// npc_dpssim_training_dummy (modules/mod-dpssim/src/SimDummyAI.cpp) instead of the player-facing
// 900001/900002/900003 (real npc_training_dummy) - the same AI minus a 5s no-damage combat timeout,
// added specifically because that timeout turned out to be the root cause of a real
// RunPlayerbotBatch() failure (see docs/bugs-and-fixes.md). 900004 (level 60) was validated alone
// first - a full stat-weights batch, 10 container boots, 0 zero-cast failures - before 900005/900006
// were added to extend the same fix to 70/80.
//
// Create() picks the sibling entry matching `config.Level` (see EntryForLevel()) rather than always
// spawning one and overriding its level - the three original rows were otherwise identical
// (creature_template's faction/unit_flags/AIName/ScriptName all matched, confirmed against this
// deployment's own DB, not assumed), so this was about matching the deployment's own per-bracket
// convention rather than a functional necessity - 900004/900005/900006 keep everything but
// ScriptName identical to their 900001/900002/900003 counterparts for exactly that reason.
// Level/armor are still applied programmatically after spawn (SetLevel/SetResistance) regardless of
// which entry was picked.
//
// **Load-bearing gotcha, matters to EventRecorder, not just this class**: DamageTaken() runs
// *before* ScriptMgr::OnDamage() inside Unit::DealDamage (see the "its rare to modify damage in
// hooks, however training dummy's sets damage to 0" comment at the top of Unit::DealDamage) - by
// the time OnDamage fires, `damage` has already been zeroed for any hit against this dummy.
// EventRecorder reads the real, pre-zero, fully mitigated (crit multiplier included) damage (and
// isCrit) from the earlier OnSpellDamageTakenFinal hook instead, which fires from
// CalculateSpellDamageTaken, upstream of DamageTaken - see its own doc comment for why OnDamage
// isn't used at all here.
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

    // The three training dummy template entries - see the class comment. Only levels 60/70/80 have
    // a dedicated entry (the brackets that actually matter for this fork's balance work); anything
    // else falls back to the nearest bracket at or below it in EntryForLevel(), logging a warning,
    // rather than failing outright.
    //
    // **2026-09-13**: all three point at the sim-exclusive npc_dpssim_training_dummy entries
    // (900004/900005/900006, see data/sql/updates/pending_db_world's two migrations and
    // modules/mod-dpssim/src/SimDummyAI.cpp) rather than the original player-facing
    // 900001/900002/900003 - dropping npc_training_dummy's 5-second no-damage combat timeout fixed
    // RunPlayerbotBatch()'s "iteration 1 lands hits, every iteration after it doesn't" failure
    // (docs/bugs-and-fixes.md) at its source. 900004 was validated alone first (a full stat-weights
    // batch, 0/10 zero-cast failures) before 900005/900006 were added to match.
    static constexpr uint32 DUMMY_ENTRY_LEVEL_60 = 900004;
    static constexpr uint32 DUMMY_ENTRY_LEVEL_70 = 900005;
    static constexpr uint32 DUMMY_ENTRY_LEVEL_80 = 900006;

    // Maps a target level to the matching dummy entry above. Exact matches for 60/70/80; anything
    // else logs a warning and falls back to the nearest bracket at or below `level` (60 for
    // anything under 60, 70 for 61-69, 80 for 71+) - callers asking for an off-bracket level are
    // almost certainly a mistake, not a deliberate scenario, since this fork only cares about
    // 60/70/80.
    static uint32 EntryForLevel(uint8 level);

    ~SimTarget();

    // Spawns the dummy entry matching `config.Level` (see EntryForLevel()) on `map` at `pos` and
    // applies the rest of `config`. Returns false (logging why) on failure - most likely the
    // resolved entry not existing in this deployment's DB (base data, should always be present,
    // but worth checking explicitly rather than dereferencing null).
    bool Create(Map* map, Position const& pos, Config const& config);

    [[nodiscard]] Creature* GetCreature() const;

private:
    TempSummon* _summon = nullptr;
};

#endif
