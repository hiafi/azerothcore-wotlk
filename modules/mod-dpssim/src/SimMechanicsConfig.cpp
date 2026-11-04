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

#include "SimMechanicsConfig.h"
#include "Config.h"
#include "Log.h"
#include "SharedDefines.h"
#include "SimBossMechanics.h"
#include "StringFormat.h"
#include <algorithm>
#include <array>

namespace
{
    // The fixed reference group (STAGE-M4-HANDOFF decision 7.3): Horde-friendly, no pets, real tank / healer / melee /
    // ranged bodies. Each list is cycled when a group needs more slots of the role than it holds.
    constexpr char const* DEFAULT_TANK_PROFILES = "ProtWarriorTankSim, ProtPaladinTankSim";
    constexpr char const* DEFAULT_HEALER_PROFILES = "RestoShamanHealSim, HolyPriestHealSim, RestoDruidHealSim, "
        "HolyPaladinHealSim";
    constexpr char const* DEFAULT_DPS_PROFILES = "ArmsWarriorSim, FireMageSim, CombatRogueSim, ShadowPriestSim, "
        "ShamanEleSim, FuryWarriorSim";

    std::string ProfileName(std::string const& path)
    {
        size_t const slash = path.find_last_of('/');
        std::string name = slash == std::string::npos ? path : path.substr(slash + 1);
        std::string const suffix = ".conf";
        if (name.size() > suffix.size() && name.compare(name.size() - suffix.size(), suffix.size(), suffix) == 0)
            name.resize(name.size() - suffix.size());
        return name;
    }

    SimMechanics::Role RoleOf(SimProfile::Profile const& profile)
    {
        if (profile.MechanicsMode)
        {
            SimMechanics::Role role = SimMechanics::Role::Dps;
            if (!profile.MechanicsRole.empty())
                SimMechanics::ParseRole(profile.MechanicsRole, role);
            return role;
        }
        if (profile.TankMode)
            return SimMechanics::Role::Tank;
        if (profile.HealMode)
            return SimMechanics::Role::Healer;
        return SimMechanics::Role::Dps;
    }

    SimMechanics::MemberSpec SpecOf(std::string const& name, SimProfile::Profile const& profile,
        SimMechanics::Role role, bool underTest)
    {
        SimMechanics::MemberSpec spec;
        spec.Profile = name;
        spec.MemberRole = role;
        spec.UnderTest = underTest;
        spec.Class = profile.Class;
        spec.Race = SimMechanicsConfig::HordeRaceFor(profile.Class);
        spec.Talents = profile.PlayerbotTalents;
        spec.Glyphs = profile.PlayerbotGlyphs;
        spec.GearItemIds = profile.GearItemIds;
        spec.SpellPower = profile.SpellPower;
        spec.CombatRatings = profile.CombatRatings;
        spec.Stats = profile.Stats;
        spec.AttackPower = profile.AttackPower;
        spec.PetCreatureEntry = profile.PetCreatureEntry;
        spec.PrePullBuffMs = profile.PrePullBuffMs;
        return spec;
    }

    // A text conf value; an empty value (dpssim.conf.dist ships the keys empty) is the fallback
    std::string TextOption(char const* key, char const* fallback)
    {
        std::string const text = sConfigMgr->GetOption<std::string>(key, "");
        return text.empty() ? std::string(fallback) : text;
    }

    // An unsigned conf value in [lo, hi]; false with `error` when it is outside or not a number
    bool ReadUInt(char const* key, uint32 fallback, uint32 lo, uint32 hi, uint32& out, std::string& error)
    {
        std::string const text = sConfigMgr->GetOption<std::string>(key, "");
        if (text.empty())
        {
            out = fallback;
            return true;
        }
        if (text.find_first_not_of("0123456789") != std::string::npos || text.size() > 9)
        {
            error = Acore::StringFormat("{} '{}' is not a whole number", key, text);
            return false;
        }
        uint32 const value = uint32(std::stoul(text));
        if (value < lo || value > hi)
        {
            error = Acore::StringFormat("{} {} is outside {}-{}", key, value, lo, hi);
            return false;
        }
        out = value;
        return true;
    }
}

uint8 SimMechanicsConfig::HordeRaceFor(uint8 playerClass)
{
    switch (playerClass)
    {
        case CLASS_WARRIOR:
        case CLASS_HUNTER:
        case CLASS_ROGUE:
        case CLASS_DEATH_KNIGHT:
        case CLASS_SHAMAN:
        case CLASS_WARLOCK:
            return RACE_ORC;
        case CLASS_PALADIN:
            return RACE_BLOODELF;
        case CLASS_PRIEST:
        case CLASS_MAGE:
            return RACE_TROLL;
        case CLASS_DRUID:
            return RACE_TAUREN;
        default:
            return 0;
    }
}

std::vector<std::string> SimMechanicsConfig::SplitList(std::string const& text, char separator)
{
    std::vector<std::string> out;
    size_t start = 0;
    while (start <= text.size())
    {
        size_t const end = std::min(text.find(separator, start), text.size());
        std::string piece = text.substr(start, end - start);
        size_t const first = piece.find_first_not_of(" \t");
        if (first != std::string::npos)
            out.push_back(piece.substr(first, piece.find_last_not_of(" \t") - first + 1));
        start = end + 1;
    }
    return out;
}

std::string SimMechanicsConfig::ResolveProfilePath(std::string const& profilePath, std::string const& name)
{
    std::string const suffix = ".conf";
    bool const isPath = name.find('/') != std::string::npos ||
        (name.size() > suffix.size() && name.compare(name.size() - suffix.size(), suffix.size(), suffix) == 0);
    if (isPath)
        return name;

    size_t const slash = profilePath.find_last_of('/');
    std::string const dir = slash == std::string::npos ? std::string(".") : profilePath.substr(0, slash);
    return dir + "/" + name + suffix;
}

bool SimMechanicsConfig::Build(std::string const& profilePath, SimProfile::Profile const& actor,
    SimDaemon::RunConfig& config, std::string& error)
{
    if (!SimMech::Available())
    {
        error = "this worldserver is built without mod-boss-mechanics";
        return false;
    }

    // ---- the slot under test ----
    SimMechanics::Role actorRole = RoleOf(actor);
    std::string const roleText = sConfigMgr->GetOption<std::string>("DpsSim.MechanicsRole", "");
    if (!roleText.empty() && !SimMechanics::ParseRole(roleText, actorRole))
    {
        error = Acore::StringFormat("DpsSim.MechanicsRole '{}' is not tank, healer or dps", roleText);
        return false;
    }
    if (HordeRaceFor(actor.Class) == 0)
    {
        error = Acore::StringFormat("class {} has no Horde race for the mechanics group", uint32(actor.Class));
        return false;
    }

    // ---- the group's shape ----
    uint32 groupSize = SimMechanics::DEFAULT_GROUP;
    if (!ReadUInt("DpsSim.MechanicsGroup", SimMechanics::DEFAULT_GROUP, SimMechanics::MIN_GROUP,
        SimMechanics::MAX_GROUP, groupSize, error))
        return false;

    std::array<uint32, 3> counts{};     // indexed by Role
    counts[size_t(SimMechanics::Role::Tank)] = groupSize > 10 ? 2 : 1;
    counts[size_t(SimMechanics::Role::Healer)] = groupSize < 3 ? 0 : groupSize <= 5 ? 1 : groupSize <= 10 ? 2 : 4;
    counts[size_t(SimMechanics::Role::Dps)] = groupSize - counts[0] - counts[1];
    if (counts[size_t(actorRole)] == 0)
    {
        // A group of 2 with a healer under test: the tank and the healer
        ++counts[size_t(actorRole)];
        --counts[size_t(SimMechanics::Role::Dps)];
    }

    std::array<std::vector<std::string>, 3> references = {
        SplitList(TextOption("DpsSim.MechanicsTankProfiles", DEFAULT_TANK_PROFILES), ','),
        SplitList(TextOption("DpsSim.MechanicsHealerProfiles", DEFAULT_HEALER_PROFILES), ','),
        SplitList(TextOption("DpsSim.MechanicsDpsProfiles", DEFAULT_DPS_PROFILES), ','),
    };

    std::string const actorName = ProfileName(profilePath);
    std::map<std::string, SimProfile::Profile> loaded;
    std::vector<SimMechanics::MemberSpec> members;
    for (SimMechanics::Role role : { SimMechanics::Role::Tank, SimMechanics::Role::Healer, SimMechanics::Role::Dps })
    {
        uint32 needed = counts[size_t(role)];
        if (role == actorRole)
        {
            members.push_back(SpecOf(actorName, actor, actorRole, true));
            --needed;
        }

        // The role's references in order, without the profile under test
        std::vector<std::string> pool;
        for (std::string const& name : references[size_t(role)])
            if (ProfileName(name) != actorName)
                pool.push_back(name);
        if (needed > 0 && pool.empty())
        {
            error = Acore::StringFormat("the group needs {} {} reference(s) and DpsSim.Mechanics{}Profiles has none "
                "besides the profile under test", needed, SimMechanics::RoleName(role),
                role == SimMechanics::Role::Tank ? "Tank" : role == SimMechanics::Role::Healer ? "Healer" : "Dps");
            return false;
        }

        for (uint32 k = 0; k < needed; ++k)
        {
            std::string const& name = pool[k % pool.size()];
            auto it = loaded.find(name);
            if (it == loaded.end())
            {
                SimProfile::Profile reference;
                std::string const path = ResolveProfilePath(profilePath, name);
                if (!SimProfile::Load(path, reference))
                {
                    error = Acore::StringFormat("reference profile '{}' ({}) failed to load", name, path);
                    return false;
                }
                if (HordeRaceFor(reference.Class) == 0)
                {
                    error = Acore::StringFormat("reference profile '{}' has class {}, which has no Horde race", name,
                        uint32(reference.Class));
                    return false;
                }
                it = loaded.emplace(name, std::move(reference)).first;
            }
            members.push_back(SpecOf(ProfileName(name), it->second, role, false));
        }
    }

    // ---- programs ----
    std::vector<std::string> programs;
    if (sConfigMgr->GetOption<bool>("DpsSim.MechanicsBaseline", false))
        programs.push_back(SimMechanics::BASELINE_PROGRAM);
    else
        programs = SplitList(TextOption("DpsSim.MechanicsPrograms", SimMechanics::DEFAULT_PROGRAMS), ';');
    if (programs.empty())
    {
        error = "DpsSim.MechanicsPrograms holds no program";
        return false;
    }
    for (std::string const& program : programs)
    {
        uint32 lengthMs = 0;
        std::string programError;
        if (!SimMech::CheckProgram(program, lengthMs, programError))
        {
            error = Acore::StringFormat("program '{}': {}", program, programError);
            return false;
        }
        if (lengthMs > config.DurationMs)
            LOG_INFO("server.dpssim", "mod-dpssim: mechanics program '{}' runs {} ms, longer than the {} ms fight: an "
                "iteration sees its first {} ms.", program, lengthMs, config.DurationMs, config.DurationMs);
    }

    uint32 seed = 1;
    uint32 damage = 1;
    uint32 anchorRace = 2;
    if (!ReadUInt("DpsSim.MechanicsSeed", 1, 0, 999999999, seed, error) ||
        !ReadUInt("DpsSim.MechanicsDamage", 1, 0, 1000000, damage, error) ||
        !ReadUInt("DpsSim.MechanicsAnchorRace", 2, 1, 11, anchorRace, error))
        return false;

    config.RunMode = SimDaemon::Mode::Mechanics;
    config.MechMembers = std::move(members);
    config.MechPrograms = std::move(programs);
    config.MechSeed = seed;
    config.MechDamage = int32(damage);
    config.MechAnchorRace = uint8(anchorRace);
    config.MechBossSwings = sConfigMgr->GetOption<bool>("DpsSim.MechanicsBossSwings", true);

    // The boss's swing: the first tank's own Tank* keys when it is a Tank profile, the tank sim's defaults otherwise
    config.MechBossHit = SimTank::DEFAULT_BOSS_HIT;
    config.MechBossSwingMs = SimTank::DEFAULT_SWING_MS;
    config.MechBossCrit = true;
    for (SimMechanics::MemberSpec const& member : config.MechMembers)
    {
        if (member.MemberRole != SimMechanics::Role::Tank)
            continue;

        SimProfile::Profile const* tankProfile = member.UnderTest ? &actor : nullptr;
        if (!tankProfile)
        {
            for (auto const& [name, profile] : loaded)
                if (ProfileName(name) == member.Profile)
                    tankProfile = &profile;
        }
        if (tankProfile && tankProfile->TankMode)
        {
            config.MechBossHit = tankProfile->TankHitDamage;
            config.MechBossSwingMs = tankProfile->TankSwingMs;
            config.MechBossCrit = tankProfile->TankDummyCrit;
        }
        break;
    }

    std::string roster;
    for (SimMechanics::MemberSpec const& member : config.MechMembers)
        roster += Acore::StringFormat("{}{} {}{} (race {})", roster.empty() ? "" : ", ",
            SimMechanics::RoleName(member.MemberRole), member.Profile, member.UnderTest ? "*" : "",
            uint32(member.Race));
    LOG_INFO("server.dpssim", "mod-dpssim: mechanics mode - group of {}: {} (* = under test); {} program(s){}, seed "
        "{}, damage {}, anchor race {}, boss swings {} ({}-{} every {} ms).", config.MechMembers.size(), roster,
        config.MechPrograms.size(), config.MechPrograms.size() == 1 && config.MechPrograms[0] ==
        SimMechanics::BASELINE_PROGRAM ? " (baseline)" : "", config.MechSeed, config.MechDamage,
        uint32(config.MechAnchorRace), config.MechBossSwings ? "on" : "off", config.MechBossHit.Min,
        config.MechBossHit.Max, config.MechBossSwingMs);
    return true;
}
