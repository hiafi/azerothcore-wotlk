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

#ifndef MODULE_DPSSIM_SIMTANK_H
#define MODULE_DPSSIM_SIMTANK_H

#include "Define.h"
#include <string>
#include <vector>

// Tank-mode configuration shared by the profile loader (SimProfile.cpp), the conf overrides (DpsSim.cpp), the dummy AI
// (SimTankDummyAI.cpp) and the recorder (DamageTakenRecorder.cpp), plus the event structs RunResult carries (plan
// .agents/plans/tank-sim/tank-sim.PLAN.md, sections 3 and 4). Pure data and parsing, no game headers.
namespace SimTank
{
    // What the incoming hits are for. Dps: real damage, the actor's health refilled after every sim step so it never
    // dies (tank DPS with every avoidance proc live). Survive: real damage, no refill; the run ends at the actor's
    // death and the time of death is the headline.
    enum class Scenario : uint8
    {
        Dps,
        Survive
    };

    // An inclusive damage range. A single value is Min == Max.
    struct HitRange
    {
        uint32 Min = 0;
        uint32 Max = 0;

        bool operator==(HitRange const& other) const { return Min == other.Min && Max == other.Max; }
    };

    // Plan T3/T4 defaults: a boss swings for 2,250-2,750 before armor, each pack dummy for 500-600, every 2.0 s, with
    // crits on
    constexpr HitRange DEFAULT_BOSS_HIT = {2250, 2750};
    constexpr HitRange DEFAULT_PACK_HIT = {500, 600};
    constexpr uint32 DEFAULT_SWING_MS = 2000;

    // Bounds of TankSwingMs: a swing under half a second or over 10 s is a typo, not a scenario
    constexpr uint32 MIN_SWING_MS = 500;
    constexpr uint32 MAX_SWING_MS = 10000;

    // The longest damage a hit can be asked to do
    constexpr uint32 MAX_HIT_DAMAGE = 1000000;

    // The Paladin's Bulwark: the buff is the resource (spell_paladin_protection.cpp, aura 201360), sampled as stacks
    constexpr uint32 SPELL_BULWARK = 201360;

    // "dps" / "survive" (any case) -> scenario. False (with `error`) for anything else.
    bool ParseScenario(std::string const& text, Scenario& out, std::string& error);

    // "<min>-<max>" or one value -> range. False (with `error`) for a missing, non-numeric, zero or inverted value.
    bool ParseHitRange(std::string const& text, HitRange& out, std::string& error);

    // "dps" / "survive"
    char const* ScenarioName(Scenario scenario);

    // "2250-2750", or "1000" for a single value
    std::string HitRangeText(HitRange const& range);

    // ---- What a tank-mode iteration records (filled by DamageTakenRecorder and SimDaemon, copied into RunResult) ----
    // All timestamps are in the recorders' raw clock; SimDaemon rebases them to ms since the iteration start.
    //
    // Time bases (for TS2): one sim step is clock.Tick() (the map update, in which the dummies swing), then the
    // samples, then the bot's AI. SwingEvent::TimestampMs is stamped by the recorder during the tick, at the tick's
    // start (the clock's time before the step). Sample, ThreatSample and RunResult::ActorDiedAtMs are read after the
    // tick, at its end, so they sit one StepMs later: the swing that killed the actor is at ActorDiedAtMs - StepMs.

    // How a dummy's swing at the actor ended
    enum class Outcome : uint8
    {
        Miss,
        Dodge,
        Parry,
        Block,       // blocked, some damage got through
        FullBlock,   // VICTIMSTATE_BLOCKS: the block took the whole hit
        Crit,
        Crush,
        Hit,
        Glancing,
        // Any other hitOutCome. Unreachable with the actor (a player) as the victim: MELEE_HIT_EVADE is only rolled
        // against an evading creature (Unit::RollMeleeOutcomeAgainst) and an immune swing returns from
        // CalculateMeleeDamage before the hook. Kept so an unexpected outcome is counted under its own name instead of
        // passing for a real one, and as the end of the enum (LogTankSummary sizes its counters by it).
        Other
    };

    // "miss", "dodge", "parry", "block", "full block", "crit", "crush", "hit", "glancing", "other"
    char const* OutcomeName(Outcome outcome);

    // One swing of a dummy at the actor. Damage fields are for landed swings (zero for an avoided one):
    //  PreArmor        the swing's damage after the dummy's damage fields and the actor's damage-taken modifiers (the
    //                  ModifyMeleeDamage point), before armor, the outcome and the crit multiplier. Kept for an avoided
    //                  swing too (the damage that was dodged, parried or missed).
    //  ArmorMitigated  PreArmor - CalcArmorReducedDamage(PreArmor), what armor took off
    //  Blocked         what the block took off after armor (the flat 20%, the block value and Critical Block); 0 unless
    //                  the outcome is Block or FullBlock
    //  Absorbed        shields (the per-spell split is in SwingAbsorb), Resisted resists
    //  Final           the damage that reached the actor's health, after shields
    // Crit and crush multiply before the block and shield steps, so for those PreArmor is the base roll, not the sum.
    struct SwingEvent
    {
        uint32 TimestampMs = 0;
        uint8 DummyIndex = 0;
        Outcome Result = Outcome::Hit;
        uint32 PreArmor = 0;
        uint32 ArmorMitigated = 0;
        uint32 Blocked = 0;
        uint32 Absorbed = 0;
        uint32 Resisted = 0;
        uint32 Final = 0;
        // The actor's rage across the dummy's swing, in tenths of a point (rage is stored x10): damage-taken rage plus
        // whatever the swing procs (Shield Specialization, ...). -1 when the actor has no rage.
        int32 RageGained = -1;
        // What the core rolled the swing against, in hundredths of a percent, after the skill difference and with the
        // arc and casting rules applied (0 when the actor could not dodge/parry/block that swing): the "expected" side
        // of expected-vs-observed outcome rates
        uint16 ExpectedMiss = 0;
        uint16 ExpectedDodge = 0;
        uint16 ExpectedParry = 0;
        uint16 ExpectedBlock = 0;
        uint16 ExpectedCrit = 0;
        // Whether the swing hit the actor from inside its front arc
        bool InFrontArc = true;
        // The actor's damage-taken multiplier on this swing (Defensive Stance, talents, Versatility), measured with
        // Unit::MeleeDamageBonusTaken on a large hit: PreArmor / TakenMult is the dummy's own roll
        float TakenMult = 1.0f;
    };

    // One shield that took damage off the actor during a swing, attributed to the shield's aura spell
    struct SwingAbsorb
    {
        uint32 TimestampMs = 0;
        // Index into the iteration's SwingEvent list
        uint32 SwingIndex = 0;
        uint32 SpellId = 0;
        uint32 Amount = 0;
    };

    // The actor's health and class power, every TANK_SAMPLE_INTERVAL_MS
    struct Sample
    {
        uint32 TimestampMs = 0;
        uint32 Health = 0;
        uint32 MaxHealth = 0;
        // The class's resource: POWER_* of the actor's current power type (rage for a warrior or a bear, runic power
        // for a DK, mana otherwise), in the unit the core stores (rage and runic power x10)
        uint8 PowerType = 0;
        uint32 Power = 0;
        uint32 MaxPower = 0;
        // Stacks of the Paladin's Bulwark buff (0 for everyone else)
        uint8 BulwarkStacks = 0;
    };
    constexpr uint32 TANK_SAMPLE_INTERVAL_MS = 500;

    // The actor's threat on one dummy
    struct ThreatSample
    {
        uint32 TimestampMs = 0;
        uint8 DummyIndex = 0;
        float Threat = 0.0f;
    };
    constexpr uint32 THREAT_SAMPLE_INTERVAL_MS = 1000;

    // What a dummy was at the pull: the damage fields the solver ended up with and the chance it had to crit the actor
    struct DummyInfo
    {
        HitRange Hit;
        uint32 SwingMs = 0;
        uint32 Level = 0;
        // The creature's own level, and the level it fights the actor at (BOSS_MOB: +3)
        uint32 LevelForTarget = 0;
        uint32 Armor = 0;
        // dummy->GetUnitCriticalChance(BASE_ATTACK, actor) at the pull, percent. Zero on a crit-immune actor: a crit
        // taken then is a bug
        float ExpectedCritPct = 0.0f;
        // The solver's result: base weapon damage, attack power and the multipliers (SimTankDummyAI.cpp)
        float WeaponMin = 0.0f;
        float WeaponMax = 0.0f;
        float AttackPower = 0.0f;
        float DamageModifier = 0.0f;
        float BasePct = 1.0f;
        // The damage fields (UNIT_FIELD_MIN/MAXDAMAGE) the formula gives with them
        float FieldMin = 0.0f;
        float FieldMax = 0.0f;
    };

    // The actor's character sheet from the core's own getters, percent (RunResult keeps it at the pull and after 1 s)
    struct ActorInfo
    {
        uint32 Level = 0;
        uint32 Health = 0;
        uint32 Armor = 0;
        uint32 DefenseSkill = 0;
        uint32 MaxSkillForLevel = 0;
        float Dodge = 0.0f;
        float Parry = 0.0f;
        float Block = 0.0f;
        uint32 BlockValue = 0;
        // The dummy's crit chance against it: see DummyInfo::ExpectedCritPct
        bool CritImmune = false;
    };
}

#endif
