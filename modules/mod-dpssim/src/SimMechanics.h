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

#ifndef MODULE_DPSSIM_SIMMECHANICS_H
#define MODULE_DPSSIM_SIMMECHANICS_H

#include "Define.h"
#include "SimBossMechanics.h"
#include <map>
#include <string>
#include <utility>
#include <vector>

// The mechanics sim's types (plan .agents/plans/dungeon-mechanics/dungeon-mechanics.STAGE-M4-HANDOFF.md, section 3.4):
// a group of real bots (1 tank, 1 healer, 3 DPS by default) fights a boss stand-in while mod-boss-mechanics runs a
// drill program on it; every bot reports its damage, the failures the module's global failure sink saw for it, and
// the module's own counters. The paired baseline is the same run with the program `none`. Pure types: the scenario is
// SimMechanicsScenario.h, the batch SimDaemon.cpp, the report SimReport.cpp.
namespace SimMechanics
{
    enum class Role : uint8
    {
        Tank,
        Healer,
        Dps
    };

    // "tank" / "healer" / "dps"
    char const* RoleName(Role role);
    // Case-insensitive "tank" / "healer" (or "heal") / "dps"; false for anything else
    bool ParseRole(std::string const& text, Role& out);

    // The default per-iteration programs of a mechanics run (DpsSim.MechanicsPrograms). Iteration i runs entry
    // i % count, so a 5-iteration batch covers every kind once inside 120 s each: Frontal, Spread, Bait, RunOut and
    // Stack; the cookie cones, puddles and run-outs plus a short barrage; soaks and a random minefield; Alexei's rules
    // (one cycle is 156 s, so a 120 s fight sees the first ten slots: hold still, stack, spread, out of bounds, line
    // up, desks and four heroic pairs); a long barrage, a lane set and a U minefield. The program grammar is
    // mod-boss-mechanics' Drill::ParseProgram (MechanicDrillPlan.h).
    constexpr char const* DEFAULT_PROGRAMS =
        "smite,fenrus,ras; cookie,barrage:15; soaks,minefield:30; alexei; barrage:60,lanes:3,uminefield:20";

    // The baseline program: the encounter and its scope exist (so every bot has the strategy, as in the paired run)
    // but nothing fires
    constexpr char const* BASELINE_PROGRAM = "none";

    // Group sizes the mode accepts (DpsSim.MechanicsGroup)
    constexpr uint32 MIN_GROUP = 2;
    constexpr uint32 MAX_GROUP = 40;
    constexpr uint32 DEFAULT_GROUP = 5;

    // The failure log of one iteration is capped (a 20-bot barrage can post thousands of hits)
    constexpr size_t MAX_FAILURE_LOG = 2000;

    // One member of the group, built from a profile (SimProfile.h). Index order is the group order: the tanks first,
    // then the healers, then the DPS; the member under test sits in its role's first slot.
    struct MemberSpec
    {
        std::string Profile;    // the profile's file name without ".conf"
        Role MemberRole = Role::Dps;
        bool UnderTest = false;
        uint8 Race = 0;
        uint8 Class = 0;
        std::string Talents;
        bool Glyphs = true;
        std::vector<uint32> GearItemIds;
        int32 SpellPower = 0;
        std::map<uint8, int32> CombatRatings;
        std::map<uint8, float> Stats;
        int32 AttackPower = 0;
        uint32 PetCreatureEntry = 0;
        uint32 PrePullBuffMs = 15000;
    };

    // One logged failure (iteration-relative time; member -1 = a group failure such as MissedSoak)
    struct FailureRecord
    {
        uint32 AtMs = 0;
        int32 Member = -1;
        std::string Type;
        std::string Kind;
        uint32 Tag = 0;
        uint32 MechanicId = 0;
        uint32 Damage = 0;
    };

    // "<Kind>/<tag>", the key failures are counted under (tags are per drill, so the kind keeps them apart)
    std::string FailureKey(std::string const& kind, uint32 tag);

    // One member's iteration
    struct MemberResult
    {
        uint32 Index = 0;
        std::string Profile;
        Role MemberRole = Role::Dps;
        bool UnderTest = false;
        uint8 Race = 0;
        uint8 Class = 0;
        uint8 SpecTab = 0;
        // The bot has the "boss mechanics" strategy after the program started (Sim::ReconcileBot)
        bool StrategyInstalled = false;
        // The strategies the bot ran with, and the follow-type ones the scenario removed (SimMechanicsScenario)
        std::string Strategies;
        std::vector<std::string> Stripped;
        // Damage to the boss stand-in (the member's pet included) and its DPS over the full duration
        uint64 Damage = 0;
        double Dps = 0.0;
        // Deliberate casts (not triggered)
        uint32 Casts = 0;
        // Failures by type, then by FailureKey(); FailureTotal is their sum; Hits and HitDamage the Hit failures
        std::map<std::string, std::map<std::string, uint32>> Failures;
        uint32 FailureTotal = 0;
        uint32 Hits = 0;
        uint64 HitDamage = 0;
        // Sim-side movement: steps in which the member moved more than 0.1 yd, and the path length
        uint32 MovingMs = 0;
        float DistanceYd = 0.0f;
        bool Died = false;
        uint32 DiedAtMs = 0;
        // mod-boss-mechanics' own counters (Sim::ReadBotStats), flattened
        SimMech::Stats ModuleStats;
    };
}

#endif
