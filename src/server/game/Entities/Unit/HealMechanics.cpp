/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#include "HealMechanics.h"
#include "CellImpl.h"
#include "GridNotifiersImpl.h"
#include "Unit.h"
#include "SharedDefines.h"
#include "SpellInfo.h"
#include <algorithm>
#include <array>
#include <list>

namespace Heal
{
    namespace
    {
        // Never-list (RESTO §0.13 Q4 / §9). A later class pass appends its own ids here rather than
        // creating a second never-list mechanism.
        constexpr std::array<uint32, 6> NEVER_LIST =
        {
            44203,  // Tranquility's per-tick triggered heal
            33778,  // Lifebloom's bloom
            48503,  // Living Seed's bloom
            200569, // Ysera's Gift
            200574, // Tree of Life's instant Rejuvenation heal
            50464,  // Nourish (removed)
        };
    }

    bool IsDirectNatureHeal(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false;

        if (spellInfo->SpellFamilyName == SPELLFAMILY_GENERIC)
            return false;

        if (!(spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_NATURE))
            return false;

        if (!spellInfo->HasEffect(SPELL_EFFECT_HEAL))
            return false;

        if (std::find(NEVER_LIST.begin(), NEVER_LIST.end(), spellInfo->Id) != NEVER_LIST.end())
            return false;

        return true;
    }

    void SelectMostInjured(Unit* caster, WorldObject const* center, float range, uint8 count,
                           std::vector<Unit*>& out, Unit const* exclude)
    {
        out.clear();
        if (!caster || !center || !count)
            return;

        std::list<Unit*> nearby;
        Acore::AnyGroupedUnitInObjectRangeCheck check(center, caster, range, true);
        Acore::UnitListSearcher<Acore::AnyGroupedUnitInObjectRangeCheck> searcher(caster, nearby, check);
        Cell::VisitObjects(center, searcher, range);

        // A4 says "party/raid members": players (the caster included), not their pets or guardians. The
        // grouped-unit check also accepts a group member's pets (IsInRaidWith resolves the owner), which
        // would let a 20% pet soak the 3 heals of Divine Storm / Seal of Light's echo.
        for (Unit* unit : nearby)
            if (unit != exclude && (unit->IsPlayer() || unit == caster))
                out.push_back(unit);

        std::stable_sort(out.begin(), out.end(), [](Unit const* a, Unit const* b)
        {
            return a->GetHealthPct() < b->GetHealthPct();
        });

        if (out.size() > count)
            out.resize(count);
    }
}
