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

#include "SimProfile.h"
#include "Log.h"
#include "Unit.h"
#include <algorithm>
#include <fstream>
#include <sstream>

namespace
{
    std::string Trim(std::string const& s)
    {
        size_t const start = s.find_first_not_of(" \t\r\n");
        if (start == std::string::npos)
            return "";
        size_t const end = s.find_last_not_of(" \t\r\n");
        return s.substr(start, end - start + 1);
    }

    // Accepts "true"/"false" (any case) or "1"/"0" - mirrors ConfigMgr::GetOption<bool>'s own
    // accepted spellings closely enough that a "TestX = true" line reads the same way any other
    // boolean conf key in this repo does. Returns false (via `ok`) rather than throwing on
    // anything else, so the caller can log a proper line/key-specific error the same way every
    // other malformed-value case here does.
    bool ParseBool(std::string const& value, bool& ok)
    {
        ok = true;
        if (value == "true" || value == "True" || value == "1")
            return true;
        if (value == "false" || value == "False" || value == "0")
            return false;
        ok = false;
        return false;
    }

    // Conf key name -> CombatRating(s) (Unit.h) it fans out to. Hit/Crit/Haste each cover all
    // three (melee/ranged/spell) variants at once, mirroring how a real item's single rating stat
    // applies (Player::_ApplyItemBonuses()'s ITEM_MOD_HASTE_RATING/CRIT_RATING/HIT_RATING cases
    // each call Player::ApplyRatingMod() three times, once per variant, for the same reason) -
    // every other rating here has only one variant. Includes this deployment's custom repurposed
    // slots (Mastery/Versatility/CooldownHaste/ProcChance - see Unit.h's own "Custom: was ..."
    // comments on those four).
    std::map<std::string, std::vector<uint8>> const RATING_KEYS = {
        {"HitRating", {CR_HIT_MELEE, CR_HIT_RANGED, CR_HIT_SPELL}},
        {"CritRating", {CR_CRIT_MELEE, CR_CRIT_RANGED, CR_CRIT_SPELL}},
        {"HasteRating", {CR_HASTE_MELEE, CR_HASTE_RANGED, CR_HASTE_SPELL}},
        {"ExpertiseRating", {CR_EXPERTISE}},
        {"ArmorPenetrationRating", {CR_ARMOR_PENETRATION}},
        {"MasteryRating", {CR_MASTERY}},
        {"VersatilityRating", {CR_VERSATILITY}},
        {"CooldownHasteRating", {CR_COOLDOWN_HASTE}},
        {"ProcChanceRating", {CR_PROC_CHANCE}},
    };

    // Conf key name -> Stats (SharedDefines.h, included transitively via Unit.h) it sets. Unlike
    // RATING_KEYS above, each of these is exactly one Stats value - no fan-out.
    std::map<std::string, uint8> const STAT_KEYS = {
        {"Strength", STAT_STRENGTH},
        {"Agility", STAT_AGILITY},
        {"Stamina", STAT_STAMINA},
        {"Intellect", STAT_INTELLECT},
        {"Spirit", STAT_SPIRIT},
    };

    // "Test<key>" flag names modules/mod-dpssim/tools/stat_weights.py reads - exactly the 13
    // stats that tool's stat-weight pass considers (2026-09-13 request), each name matching a
    // STAT_KEYS/RATING_KEYS entry above or one of the two flat fields (SpellPower/AttackPower)
    // that aren't in either map. Deliberately not "every RATING_KEYS entry" - e.g. no
    // TestHitRating/TestExpertiseRating/TestArmorPenetrationRating, since those weren't asked for
    // and hit/expertise are meaningless on this deployment's always-hit-vs-PvE custom rule anyway.
    // See Profile::StatWeightTests' own doc comment (SimProfile.h) for why this C++ module parses
    // and stores these at all despite never reading them itself.
    std::vector<std::string> const TEST_FLAG_KEYS = {
        "TestStrength", "TestAgility", "TestStamina", "TestIntellect", "TestSpirit",
        "TestSpellPower", "TestAttackPower",
        "TestCritRating", "TestHasteRating", "TestMasteryRating", "TestVersatilityRating",
        "TestCooldownHasteRating", "TestProcChanceRating",
    };
}

bool SimProfile::Load(std::string const& path, Profile& out)
{
    std::ifstream file(path);
    if (!file.is_open())
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimProfile::Load() - could not open '{}'.", path);
        return false;
    }

    Profile parsed;
    bool haveClass = false;
    std::string line;
    uint32 lineNo = 0;
    while (std::getline(file, line))
    {
        ++lineNo;
        std::string const trimmed = Trim(line);
        if (trimmed.empty() || trimmed[0] == '#')
            continue;

        size_t const eq = trimmed.find('=');
        if (eq == std::string::npos)
        {
            LOG_ERROR("server.dpssim",
                "mod-dpssim: SimProfile::Load() - '{}' line {}: expected 'Key = Value', got '{}' - skipping.",
                path, lineNo, trimmed);
            continue;
        }

        std::string const key = Trim(trimmed.substr(0, eq));
        std::string const value = Trim(trimmed.substr(eq + 1));

        if (key == "Class")
        {
            try
            {
                parsed.Class = uint8(std::stoul(value));
                haveClass = true;
            }
            catch (std::exception const&)
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: SimProfile::Load() - '{}' line {}: 'Class' value '{}' is not a number.",
                    path, lineNo, value);
                return false;
            }
        }
        else if (key == "PlayerbotTalents")
            parsed.PlayerbotTalents = value;
        else if (key == "Gear")
        {
            std::istringstream ids(value);
            std::string token;
            while (std::getline(ids, token, ','))
            {
                std::string const itemId = Trim(token);
                if (itemId.empty())
                    continue;
                try
                {
                    parsed.GearItemIds.push_back(uint32(std::stoul(itemId)));
                }
                catch (std::exception const&)
                {
                    LOG_ERROR("server.dpssim",
                        "mod-dpssim: SimProfile::Load() - '{}' line {}: 'Gear' entry '{}' is not a number.",
                        path, lineNo, itemId);
                    return false;
                }
            }
        }
        else if (key == "SpellPower")
        {
            try
            {
                parsed.SpellPower = int32(std::stol(value));
            }
            catch (std::exception const&)
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: SimProfile::Load() - '{}' line {}: 'SpellPower' value '{}' is not a number.",
                    path, lineNo, value);
                return false;
            }
        }
        else if (key == "AttackPower")
        {
            try
            {
                parsed.AttackPower = int32(std::stol(value));
            }
            catch (std::exception const&)
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: SimProfile::Load() - '{}' line {}: 'AttackPower' value '{}' is not a number.",
                    path, lineNo, value);
                return false;
            }
        }
        else if (key == "StatWeightsEnabled")
        {
            bool ok = false;
            bool const flagValue = ParseBool(value, ok);
            if (!ok)
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: SimProfile::Load() - '{}' line {}: 'StatWeightsEnabled' value '{}' is not true/false.",
                    path, lineNo, value);
                return false;
            }

            parsed.StatWeightsEnabled = flagValue;
        }
        else if (auto const it = RATING_KEYS.find(key); it != RATING_KEYS.end())
        {
            int32 ratingValue = 0;
            try
            {
                ratingValue = int32(std::stol(value));
            }
            catch (std::exception const&)
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: SimProfile::Load() - '{}' line {}: '{}' value '{}' is not a number.",
                    path, lineNo, key, value);
                return false;
            }

            for (uint8 cr : it->second)
                parsed.CombatRatings[cr] = ratingValue;
        }
        else if (auto const it = STAT_KEYS.find(key); it != STAT_KEYS.end())
        {
            float statValue = 0.0f;
            try
            {
                statValue = std::stof(value);
            }
            catch (std::exception const&)
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: SimProfile::Load() - '{}' line {}: '{}' value '{}' is not a number.",
                    path, lineNo, key, value);
                return false;
            }

            parsed.Stats[it->second] = statValue;
        }
        else if (std::find(TEST_FLAG_KEYS.begin(), TEST_FLAG_KEYS.end(), key) != TEST_FLAG_KEYS.end())
        {
            bool ok = false;
            bool const flagValue = ParseBool(value, ok);
            if (!ok)
            {
                LOG_ERROR("server.dpssim",
                    "mod-dpssim: SimProfile::Load() - '{}' line {}: '{}' value '{}' is not true/false.",
                    path, lineNo, key, value);
                return false;
            }

            parsed.StatWeightTests[key] = flagValue;
        }
        else
            LOG_ERROR("server.dpssim",
                "mod-dpssim: SimProfile::Load() - '{}' line {}: unknown key '{}' - ignoring.", path, lineNo, key);
    }

    if (!haveClass)
    {
        LOG_ERROR("server.dpssim", "mod-dpssim: SimProfile::Load() - '{}': missing required 'Class' key.", path);
        return false;
    }

    out = parsed;
    return true;
}
