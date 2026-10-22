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

#include "SimTank.h"
#include "StringFormat.h"
#include "Util.h"
#include <stdexcept>

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

    // A whole number of 1-MAX_HIT_DAMAGE; false for anything else (no sign, no fraction, no trailing text)
    bool ParseDamage(std::string const& text, uint32& out)
    {
        std::string const value = Trim(text);
        if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos)
            return false;

        try
        {
            unsigned long const number = std::stoul(value);
            if (number == 0 || number > SimTank::MAX_HIT_DAMAGE)
                return false;
            out = uint32(number);
            return true;
        }
        catch (std::exception const&)
        {
            return false;
        }
    }
}

bool SimTank::ParseScenario(std::string const& text, Scenario& out, std::string& error)
{
    std::string const value = Trim(text);
    if (StringEqualI(value, "dps"))
        out = Scenario::Dps;
    else if (StringEqualI(value, "survive"))
        out = Scenario::Survive;
    else
    {
        error = Acore::StringFormat("scenario '{}' is not dps or survive", value);
        return false;
    }

    return true;
}

bool SimTank::ParseHitRange(std::string const& text, HitRange& out, std::string& error)
{
    std::string const value = Trim(text);
    HitRange range;
    size_t const dash = value.find('-');
    bool ok = false;
    if (dash == std::string::npos)
    {
        ok = ParseDamage(value, range.Min);
        range.Max = range.Min;
    }
    else
        ok = ParseDamage(value.substr(0, dash), range.Min) && ParseDamage(value.substr(dash + 1), range.Max);

    if (!ok)
    {
        error = Acore::StringFormat("hit damage '{}' is not '<min>-<max>' or a single value of 1-{}", value,
            MAX_HIT_DAMAGE);
        return false;
    }

    if (range.Min > range.Max)
    {
        error = Acore::StringFormat("hit damage '{}' has its minimum above its maximum", value);
        return false;
    }

    out = range;
    return true;
}

char const* SimTank::ScenarioName(Scenario scenario)
{
    return scenario == Scenario::Survive ? "survive" : "dps";
}

std::string SimTank::HitRangeText(HitRange const& range)
{
    if (range.Min == range.Max)
        return std::to_string(range.Min);

    return Acore::StringFormat("{}-{}", range.Min, range.Max);
}

char const* SimTank::OutcomeName(Outcome outcome)
{
    switch (outcome)
    {
        case Outcome::Miss:
            return "miss";
        case Outcome::Dodge:
            return "dodge";
        case Outcome::Parry:
            return "parry";
        case Outcome::Block:
            return "block";
        case Outcome::FullBlock:
            return "full block";
        case Outcome::Crit:
            return "crit";
        case Outcome::Crush:
            return "crush";
        case Outcome::Hit:
            return "hit";
        case Outcome::Glancing:
            return "glancing";
        default:
            return "other";
    }
}
