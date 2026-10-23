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

#include "EngagementMechanics.h"
#include "CellImpl.h"
#include "Creature.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Unit.h"
#include <list>

namespace
{
    // The checks every candidate passes, whichever step found it.
    bool IsUsableTarget(Creature const* summon, Player const* owner, Unit const* target, float range)
    {
        return target && target->IsAlive() && target->IsInMap(summon) && summon->IsValidAttackTarget(target) &&
            summon->IsWithinDistInMap(target, range) && Engagement::IsEngagedWithOwnerOrGroup(target, owner);
    }
}

namespace Engagement
{
    bool IsEngagedWithOwnerOrGroup(Unit const* hostile, Player const* owner)
    {
        if (!hostile || !owner)
            return false;

        // Same idiom as the priest copy (spell_priest_shadow.cpp IsEngagedWithOwnerOrGroup), left in place there.
        if (hostile->IsInCombatWith(owner))
            return true;

        if (Group const* group = owner->GetGroup())
            for (GroupReference const* ref = group->GetFirstMember(); ref; ref = ref->next())
                if (Player const* member = ref->GetSource())
                    if (member != owner && hostile->IsInCombatWith(member))
                        return true;

        return false;
    }

    Unit* SelectEngagedTarget(Creature* summon, Player* owner, ObjectGuid preferred, float range)
    {
        if (!summon || !owner)
            return nullptr;

        if (!preferred.IsEmpty())
            if (Unit* preferredUnit = ObjectAccessor::GetUnit(*summon, preferred))
                if (IsUsableTarget(summon, owner, preferredUnit, range) && summon->IsWithinLOSInMap(preferredUnit))
                    return preferredUnit;

        // Only follow onto a target the owner or the group is already fighting (Warlock::SelectGuardianTarget
        // shape, widened to the group).
        if (Unit* ownerTarget = ObjectAccessor::GetUnit(*owner, owner->GetTarget()))
            if (IsUsableTarget(summon, owner, ownerTarget, range) && summon->IsWithinLOSInMap(ownerTarget))
                return ownerTarget;

        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(summon, summon, range);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(summon, nearby, check);
        Cell::VisitObjects(summon, searcher, range);

        Unit* nearest = nullptr;
        float nearestDist = 0.0f;
        for (Unit* candidate : nearby)
        {
            if (!IsUsableTarget(summon, owner, candidate, range) || !summon->IsWithinLOSInMap(candidate))
                continue;

            float const dist = summon->GetDistance(candidate);
            if (!nearest || dist < nearestDist)
            {
                nearest = candidate;
                nearestDist = dist;
            }
        }

        return nearest;
    }
}
