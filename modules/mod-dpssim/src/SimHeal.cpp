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

#include "SimHeal.h"
#include "StringFormat.h"
#include <algorithm>
#include <cctype>
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

    std::string Lower(std::string s)
    {
        std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return char(std::tolower(c)); });
        return s;
    }

    // A whole-string unsigned decimal number ("450", "3.5"); false for anything else, a sign or trailing text included
    bool ParseNumber(std::string const& text, float& value)
    {
        if (text.empty() || text.find_first_not_of("0123456789.") != std::string::npos)
            return false;

        try
        {
            size_t used = 0;
            value = std::stof(text, &used);
            return used == text.size();
        }
        catch (std::exception const&)
        {
            return false;
        }
    }
}

bool SimHeal::ParseGroup(std::string const& text, uint32& size, std::string& error)
{
    std::string const group = Lower(Trim(text));
    if (group == "party")
        size = PARTY_SIZE;
    else if (group == "raid10")
        size = RAID10_SIZE;
    else if (group == "raid20")
        size = RAID20_SIZE;
    else
    {
        error = Acore::StringFormat("HealGroup '{}' is not party, raid10 or raid20", text);
        return false;
    }

    return true;
}

bool SimHeal::ParseTargets(std::string const& text, std::vector<TargetSpec>& out, std::string& error)
{
    std::vector<TargetSpec> parsed;
    uint32 selfCount = 0;

    size_t pos = 0;
    while (pos <= text.size())
    {
        size_t comma = text.find(',', pos);
        if (comma == std::string::npos)
            comma = text.size();
        std::string item = Trim(text.substr(pos, comma - pos));
        pos = comma + 1;

        if (item.empty())
        {
            error = "HealTargets has an empty entry";
            return false;
        }

        // Optional "<count>*" prefix
        uint32 count = 1;
        if (size_t const star = item.find('*'); star != std::string::npos)
        {
            std::string const countText = Trim(item.substr(0, star));
            if (countText.empty() || countText.find_first_not_of("0123456789") != std::string::npos ||
                countText.size() > 3)
            {
                error = Acore::StringFormat("HealTargets entry '{}': the count before '*' is not a number", item);
                return false;
            }

            count = uint32(std::stoul(countText));
            if (count == 0)
            {
                error = Acore::StringFormat("HealTargets entry '{}': the count is 0", item);
                return false;
            }

            item = Trim(item.substr(star + 1));
        }

        // <role>:<mode>:<value>
        size_t const first = item.find(':');
        size_t const second = first == std::string::npos ? std::string::npos : item.find(':', first + 1);
        if (first == std::string::npos || second == std::string::npos)
        {
            error = Acore::StringFormat("HealTargets entry '{}': expected <role>:<mode>:<value>", item);
            return false;
        }

        std::string const roleText = Lower(Trim(item.substr(0, first)));
        std::string const modeText = Lower(Trim(item.substr(first + 1, second - first - 1)));
        std::string valueText = Trim(item.substr(second + 1));

        TargetSpec spec;
        if (roleText == "tank")
            spec.TargetRole = Role::Tank;
        else if (roleText == "dps")
            spec.TargetRole = Role::Dps;
        else if (roleText == "self")
            spec.TargetRole = Role::Self;
        else
        {
            error = Acore::StringFormat("HealTargets entry '{}': unknown role '{}' (tank, dps or self)", item,
                roleText);
            return false;
        }

        if (modeText == "drain")
            spec.Kind = ModeKind::Drain;
        else if (modeText == "pin")
            spec.Kind = ModeKind::Pin;
        else
        {
            error = Acore::StringFormat("HealTargets entry '{}': unknown mode '{}' (drain or pin)", item, modeText);
            return false;
        }

        if (!valueText.empty() && valueText.back() == '%')
        {
            if (spec.Kind != ModeKind::Drain)
            {
                error = Acore::StringFormat("HealTargets entry '{}': a pin value is already a percent, drop the '%'",
                    item);
                return false;
            }

            spec.Percent = true;
            valueText = Trim(valueText.substr(0, valueText.size() - 1));
        }

        float value = 0.0f;
        if (!ParseNumber(valueText, value))
        {
            error = Acore::StringFormat("HealTargets entry '{}': the value '{}' is not a number", item, valueText);
            return false;
        }

        if (spec.Kind == ModeKind::Pin)
        {
            if (value < 1.0f || value > 99.0f || value != float(uint32(value)))
            {
                error = Acore::StringFormat("HealTargets entry '{}': a pin must be a whole percent from 1 to 99",
                    item);
                return false;
            }
        }
        else if (value <= 0.0f || (spec.Percent && value > 100.0f))
        {
            error = Acore::StringFormat("HealTargets entry '{}': a drain must be above 0{}", item,
                spec.Percent ? " and at most 100%" : "");
            return false;
        }

        spec.Value = value;

        if (spec.TargetRole == Role::Self)
            selfCount += count;
        if (selfCount > 1)
        {
            error = "HealTargets has more than one 'self' (the healer is exactly one target)";
            return false;
        }

        for (uint32 i = 0; i < count; ++i)
            parsed.push_back(spec);
    }

    if (selfCount != 1)
    {
        error = "HealTargets has no 'self' (the healer is exactly one target)";
        return false;
    }

    out = std::move(parsed);
    return true;
}

bool SimHeal::Validate(uint32 groupSize, std::vector<TargetSpec> const& targets, std::string& error)
{
    if (targets.size() != groupSize)
    {
        error = Acore::StringFormat("HealTargets lists {} target(s) but the group has {}", targets.size(),
            groupSize);
        return false;
    }

    bool tank = false;
    for (TargetSpec const& spec : targets)
        tank = tank || spec.TargetRole == Role::Tank;
    if (!tank)
    {
        error = "HealTargets has no tank (the boss keeps the first tank as its victim)";
        return false;
    }

    return true;
}

char const* SimHeal::RoleName(Role role)
{
    switch (role)
    {
        case Role::Tank:
            return "tank";
        case Role::Dps:
            return "dps";
        case Role::Self:
            return "self";
    }

    return "?";
}

std::string SimHeal::ModeText(TargetSpec const& spec)
{
    if (spec.Kind == ModeKind::Pin)
        return Acore::StringFormat("pin:{}", uint32(spec.Value));

    return Acore::StringFormat("drain:{}{}", spec.Value, spec.Percent ? "%" : "");
}

char const* SimHeal::GroupName(uint32 size)
{
    switch (size)
    {
        case PARTY_SIZE:
            return "party";
        case RAID10_SIZE:
            return "raid10";
        case RAID20_SIZE:
            return "raid20";
    }

    return "";
}

std::string SimHeal::TargetsText(std::vector<TargetSpec> const& targets)
{
    std::string text;
    for (size_t i = 0; i < targets.size();)
    {
        size_t run = 1;
        while (i + run < targets.size() && targets[i + run].TargetRole == targets[i].TargetRole &&
            targets[i + run].Kind == targets[i].Kind && targets[i + run].Percent == targets[i].Percent &&
            targets[i + run].Value == targets[i].Value)
            ++run;

        if (!text.empty())
            text += ", ";
        if (run > 1)
            text += Acore::StringFormat("{}*", run);
        text += Acore::StringFormat("{}:{}", RoleName(targets[i].TargetRole), ModeText(targets[i]));
        i += run;
    }

    return text;
}
