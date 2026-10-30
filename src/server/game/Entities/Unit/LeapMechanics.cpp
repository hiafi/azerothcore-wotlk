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

// Custom: warrior-rework W0b (D10, D11; climb cap and transport rule: user 2026-10-29) - fork file, not upstream.

#include "LeapMechanics.h"
#include "DetourCommon.h"
#include "DetourNavMesh.h"
#include "DetourNavMeshQuery.h"
#include "GridDefines.h"
#include "Map.h" // also GridTerrainData.h (LiquidData, MAP_LIQUID_*, INVALID_HEIGHT), not self-contained
#include "MapCollisionData.h"
#include "MapDefines.h"
#include "Unit.h"
#include <cmath>

namespace Leap
{
    namespace
    {
        // D11 (a): the ground search starts this far above the point (= Z_OFFSET_FIND_HEIGHT), so ground a little
        // above the cursor (a slope's uphill side) is still found.
        constexpr float GROUND_PROBE_UP_YD = 2.0f;
        // D11 (a): the ground under the point must lie within this of the point's Z, or there is no ground to land
        // on (a wall face, an overhang, open air). Also the water surface tolerance.
        constexpr float GROUND_TOLERANCE_YD = 2.0f;
        // D11 (b): the nearest walkable navmesh polygon must lie within this of the found ground point.
        constexpr float NAV_TOLERANCE_YD = 1.5f;

        // A swimmable water or ocean surface near z (D11: water lands swimming). Magma and slime never pass.
        bool IsSwimmableSurface(Map* map, Unit const* caster, float x, float y, float z)
        {
            LiquidData const liquid = map->GetLiquidData(caster->GetPhaseMask(), x, y, z, caster->GetCollisionHeight(),
                {});
            if (liquid.Status == LIQUID_MAP_NO_WATER || liquid.Level <= INVALID_HEIGHT)
                return false;

            if (liquid.Flags & (MAP_LIQUID_TYPE_MAGMA | MAP_LIQUID_TYPE_SLIME))
                return false;

            return std::fabs(liquid.Level - z) <= GROUND_TOLERANCE_YD
                && liquid.Level - liquid.DepthLevel >= caster->GetMinHeightInWater();
        }

        // D11 (b), only where the map has a navmesh and the tile under the point is loaded: a walkable polygon
        // (ground or water; never the 50-60 degree NAV_GROUND_STEEP band, magma or slime) next to the ground point.
        // Slopes steeper than 60 degrees have no polygon at all.
        bool HasWalkablePolygon(Map* map, float x, float y, float groundZ)
        {
            MMapData& mmap = map->GetMapCollisionData().GetMMapData();
            dtNavMesh const* navMesh = mmap.GetNavMesh();
            if (!navMesh)
                return true;

            dtNavMeshQuery const* query = mmap.GetNavMeshQuery();
            if (!query)
                return true;

            // World (x, y, z) is Detour (y, z, x).
            float const point[3] = { y, groundZ, x };

            // An unloaded tile: no navmesh answer, rule (a) alone (as PathGenerator::HaveTile).
            int tileX = -1;
            int tileY = -1;
            navMesh->calcTileLoc(point, &tileX, &tileY);
            if (tileX < 0 || tileY < 0 || !navMesh->getTileAt(tileX, tileY, 0))
                return true;

            dtQueryFilter filter;
            filter.setIncludeFlags(NAV_GROUND | NAV_WATER);
            filter.setExcludeFlags(NAV_GROUND_STEEP | NAV_MAGMA | NAV_SLIME);

            float const extents[3] = { NAV_TOLERANCE_YD, NAV_TOLERANCE_YD, NAV_TOLERANCE_YD };
            dtPolyRef polyRef = 0;
            float nearest[3] = { 0.0f, 0.0f, 0.0f };
            if (dtStatusFailed(query->findNearestPoly(point, extents, &filter, &polyRef, nearest)) || !polyRef)
                return false;

            return dtVdist(nearest, point) <= NAV_TOLERANCE_YD;
        }
    }

    bool IsLandablePoint(Unit const* caster, float x, float y, float z)
    {
        if (!caster || !caster->IsInWorld() || !Acore::IsValidMapCoord(x, y, z))
            return false;

        // User 2026-10-29: no leaping off a transport deck, and no climbing more than MAX_CLIMB_YD.
        if (caster->GetTransport() || z - caster->GetPositionZ() > MAX_CLIMB_YD)
            return false;

        Map* map = caster->GetMap();

        // A lake's ground is its floor, which fails (a): the water surface is checked first.
        if (IsSwimmableSurface(map, caster, x, y, z))
            return true;

        // (a) ground (terrain, WMO/M2 via vmaps, gameobject floors in the caster's phase) within 2 yd of the point.
        float const groundZ = map->GetHeight(caster->GetPhaseMask(), x, y, z + GROUND_PROBE_UP_YD, true,
            GROUND_PROBE_UP_YD + GROUND_TOLERANCE_YD);
        if (groundZ <= INVALID_HEIGHT || std::fabs(groundZ - z) > GROUND_TOLERANCE_YD)
            return false;

        // (b) the navmesh, checked at the found ground point (the cursor Z may be up to 2 yd off it).
        return HasWalkablePolygon(map, x, y, groundZ);
    }
}
