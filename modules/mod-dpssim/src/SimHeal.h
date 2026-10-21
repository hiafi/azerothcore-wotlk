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

#ifndef MODULE_DPSSIM_SIMHEAL_H
#define MODULE_DPSSIM_SIMHEAL_H

#include "Define.h"
#include <string>
#include <vector>

// Heal-mode configuration shared by the profile loader (SimProfile.cpp), the conf overrides (DpsSim.cpp) and the
// scenario (SimHealScenario.cpp): the group shape and the per-target damage modes of the healing sim (plan
// .agents/plans/healing-sim/healing-sim.PLAN.md, sections 2 and 3). Pure data and parsing, no game headers.
namespace SimHeal
{
    // Who a target is. Self is the healer itself (exactly one per run); Tank and Dps are headless allies.
    enum class Role : uint8
    {
        Tank,
        Dps,
        Self
    };

    // What happens to a target. Drain: real damage every pulse, the target can die. Pin: real damage hits keep the
    // target at a fixed percent of its max health, it never fills up and never dies.
    enum class ModeKind : uint8
    {
        Drain,
        Pin
    };

    // One target of the group, in index order. `value` is, for Drain, hit points per pulse (or percent of the target's
    // max health per pulse when `percent` is set) and, for Pin, the pin percent (1-99).
    struct TargetSpec
    {
        Role TargetRole = Role::Dps;
        ModeKind Kind = ModeKind::Pin;
        bool Percent = false;
        float Value = 50.0f;
    };

    // The two damage spells the boss casts on the group (apps/dbc-tools/source/npcs/healsim_spells.py, reserved range
    // 202900-202909): Sim Damage Pulse for drain targets, Sim Pin Hit for pinned ones
    constexpr uint32 SPELL_DAMAGE_PULSE = 202900;
    constexpr uint32 SPELL_PIN_HIT = 202901;

    // ---- What a heal-mode iteration records (filled by HealRecorder and SimHealScenario, copied into RunResult) ----
    // All timestamps are in the recorders' raw clock; SimDaemon rebases them to ms since the iteration start.

    // One direct heal or HoT tick from the healer (or its pet, guardian or totem) to a group member. Raw is the heal
    // before heal-absorb auras, Effective is what landed, Overheal what was left over, HealAbsorbed what a heal-absorb
    // took (Raw = Effective + Overheal + HealAbsorbed).
    struct HealEvent
    {
        uint32 TimestampMs = 0;
        uint32 SpellId = 0;
        bool IsPet = false;
        uint8 TargetIndex = 0;
        uint32 Raw = 0;
        uint32 Effective = 0;
        uint32 Overheal = 0;
        uint32 HealAbsorbed = 0;
        bool Crit = false;
        bool Periodic = false;
    };

    // A shield of the healer that took damage off a group member
    struct AbsorbEvent
    {
        uint32 TimestampMs = 0;
        uint32 SpellId = 0;
        bool IsPet = false;
        uint8 TargetIndex = 0;
        uint32 Amount = 0;
    };

    // One hit of the boss on a group member. Raw is the hit after the target's mitigation, before shields; Final is
    // what
    // was left after the shields, Absorbed = Raw - Final.
    struct DamageEvent
    {
        uint32 TimestampMs = 0;
        uint8 TargetIndex = 0;
        bool Pin = false;
        uint32 Raw = 0;
        uint32 Absorbed = 0;
        uint32 Final = 0;
    };

    // An aura gained or lost by a group member
    struct GroupAuraEvent
    {
        uint32 TimestampMs = 0;
        uint8 TargetIndex = 0;
        uint32 SpellId = 0;
        uint8 StackAmount = 0;
        bool Positive = false;
        bool Applied = false;
        // Cast by the healer or something it owns
        bool ByHealer = false;
    };

    // A target's health, sampled every HEALTH_SAMPLE_INTERVAL_MS
    struct HealthSample
    {
        uint32 TimestampMs = 0;
        uint8 TargetIndex = 0;
        uint32 Health = 0;
        uint32 MaxHealth = 0;
    };
    constexpr uint32 HEALTH_SAMPLE_INTERVAL_MS = 500;

    // A death or a resurrection of a target
    struct LifeEvent
    {
        uint32 TimestampMs = 0;
        uint8 TargetIndex = 0;
    };

    // What a target is, as the iteration started: its raid subgroup (0 in a party) and its max health at the pull
    struct TargetInfo
    {
        TargetSpec Spec;
        uint8 Subgroup = 0;
        uint32 MaxHealth = 0;
    };

    // Group sizes: party (5), raid10 (10) and raid20 (20); the healer counts as one of them
    constexpr uint32 PARTY_SIZE = 5;
    constexpr uint32 RAID10_SIZE = 10;
    constexpr uint32 RAID20_SIZE = 20;

    // "party" / "raid10" / "raid20" -> size. False (with `error`) for anything else
    bool ParseGroup(std::string const& text, uint32& size, std::string& error);

    // "tank:drain:450, 3*dps:drain:150, self:drain:100" -> one TargetSpec per target, counts expanded. False (with
    // `error`) for an unknown role or mode, a malformed count, a missing or duplicate self, a drain that is not
    // positive, a drain percent above 100 or a pin outside 1-99. Does not check the group size; see Validate().
    bool ParseTargets(std::string const& text, std::vector<TargetSpec>& out, std::string& error);

    // The checks that need the group size: the number of targets matches it and there is at least one tank (the boss
    // pins its victim to the first tank, and the group's main tank is that one)
    bool Validate(uint32 groupSize, std::vector<TargetSpec> const& targets, std::string& error);

    // "tank", "dps", "self"
    char const* RoleName(Role role);

    // "drain:450", "drain:3.5%", "pin:50", for logs
    std::string ModeText(TargetSpec const& spec);
}

#endif
