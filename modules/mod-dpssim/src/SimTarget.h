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
#include "ObjectGuid.h"
#include "Position.h"
#include <memory>
#include <vector>

class Creature;
class Map;
class Player;
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
    // Which dummy entries spawn. Boss is the single-target default (rank 3, BOSS_MOB); Elite is the multi-target
    // pack dummy (rank 1, no BOSS_MOB), so strategy rows gated on `not boss(target)` (e.g. Shadow's pack) can open.
    enum class Rank : uint8
    {
        Boss,
        Elite
    };

    // "boss" / "elite", for logs and the report
    static char const* RankName(Rank rank);

    struct Config
    {
        uint8 Level = 80;
        Rank TargetRank = Rank::Boss;
        uint32 Armor = 0;
        // With health drain off the dummy AI zeroes all damage taken, so health never moves and this is only a
        // defensive default. With HealthDrain on it is the pool the fight drains (the profile's DummyMaxHealth;
        // 0 there keeps this default), which "target below N%" rows read.
        uint32 MaxHealth = 100000000;
        // Dummy health drain (SimDummyAI::SetHealthDrain) - the dummy takes real damage but never dies. Set by the
        // profile keys DummyHealthDrain / DummyMaxHealth. Off = the dummy zeroes all damage, as before.
        bool HealthDrain = false;
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

    // Elite pack dummies for multi-target runs: copies of the three above with rank 1 and no BOSS_MOB flag,
    // declared in apps/dbc-tools next to the boss dummies
    static constexpr uint32 DUMMY_ENTRY_ELITE_LEVEL_60 = 900007;
    static constexpr uint32 DUMMY_ENTRY_ELITE_LEVEL_70 = 900008;
    static constexpr uint32 DUMMY_ENTRY_ELITE_LEVEL_80 = 900009;

    // Maps a target level and rank to the matching dummy entry above. Exact matches for 60/70/80; anything
    // else logs a warning and falls back to the nearest bracket at or below `level` (60 for
    // anything under 60, 70 for 61-69, 80 for 71+) - callers asking for an off-bracket level are
    // almost certainly a mistake, not a deliberate scenario, since this fork only cares about
    // 60/70/80.
    static uint32 EntryForLevel(uint8 level, Rank rank);

    ~SimTarget();

    // Spawns the dummy entry matching `config.Level` and `config.TargetRank` (see EntryForLevel()) on `map` at
    // `pos` and applies the rest of `config`. Returns false (logging why) on failure - most likely the
    // resolved entry not existing in this deployment's DB (base data, should always be present,
    // but worth checking explicitly rather than dereferencing null).
    bool Create(Map* map, Position const& pos, Config const& config);

    [[nodiscard]] Creature* GetCreature() const;

private:
    TempSummon* _summon = nullptr;
};

// The run's N dummies (1-10), spawned once per process and reused by every iteration, like the single dummy
// before multi-target runs. Owns each SimTarget through a unique_ptr: ~SimTarget() unsummons, so one must never be
// copied or moved by a vector reallocation.
//
// The layout is a stacked pack, the best case for AoE: index 0 (the primary) stands where the single dummy always
// stood, 8 yd in front of the actor; indexes 1..N-1 sit on a ring of radius `spreadYards` around the primary at
// evenly spaced angles, starting directly behind the primary as seen from the actor. At the default 3 yd every
// dummy is inside the smallest AoE cluster radius any bot strategy uses (5 yd) and inside a cone from a caster at
// range.
class SimTargetGroup
{
public:
    // Spawns `count` dummies (clamped to at least 1) around `actor` on its map, each with `config`. Returns false
    // (logging why) if any spawn fails.
    bool Create(Player* actor, uint32 count, float spreadYards, SimTarget::Config const& config);

    // In index order; the primary is first
    [[nodiscard]] std::vector<Creature*> GetCreatures() const;
    [[nodiscard]] Creature* GetPrimary() const;
    [[nodiscard]] std::vector<ObjectGuid> GetGuids() const;

private:
    std::vector<std::unique_ptr<SimTarget>> _targets;
};

#endif
