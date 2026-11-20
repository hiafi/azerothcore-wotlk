/*
 * mod-dungeon-bosses, the shared dungeon kit: pushes over a floor's real edge and lethal edge bands
 * (DungeonKitEdges.h, Blackrock Depths WP-KT-D1).
 */

#include "DungeonKitEdges.h"
#include "DungeonKitRingLogic.h"
#include "GameTime.h"
#include "GridTerrainData.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Unit.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <string>

namespace DungeonKit
{
    namespace
    {
        uint64 NowMs()
        {
            return static_cast<uint64>(GameTime::GetGameTimeMS().count());
        }

        Unit* FindOwner(Map* map, ObjectGuid guid)
        {
            if (!map)
                return nullptr;
            if (guid.IsPlayer())
                return ObjectAccessor::GetPlayer(map, guid);
            return map->GetCreature(guid);
        }

        bool CanPush(Unit const* unit)
        {
            return unit && unit->IsInWorld() && unit->IsAlive() && !unit->IsTotem() && !unit->GetVehicle();
        }

        // The jump's end height: `landZ`; on the floor, the floor there; over the edge, a player's ends just under
        // the start (the client falls from there), anything else's on the ground below (it would hang in the air).
        float LandingZ(Unit* unit, EdgePush const& plan, EdgePushOptions const& o)
        {
            if (o.landZ)
                return *o.landZ;
            float const z = unit->GetPositionZ();
            if (!plan.overEdge)
            {
                float const ground = unit->GetMapHeight(plan.landing.x, plan.landing.y, z + 2.f);
                return ground > INVALID_HEIGHT + 1.f ? ground : z;
            }
            float const below = z - std::max(0.f, o.dropYd);
            if (unit->IsPlayer())
                return below;
            float const ground = unit->GetMapHeight(plan.landing.x, plan.landing.y, below, true, o.groundSearchYd);
            return ground > INVALID_HEIGHT + 1.f ? ground : below;
        }

        EdgePushResult Jump(Unit* unit, EdgePush const& plan, EdgePushOptions const& o)
        {
            EdgePushResult r;
            float const speedXY = EdgeJumpSpeedXY(plan.distance, o.flightMs);
            r.landing = Position(plan.landing.x, plan.landing.y, LandingZ(unit, plan, o), plan.bearing);
            r.overEdge = plan.overEdge;
            r.distance = plan.distance;
            r.flightMs = EdgeFlightMs(plan.distance, speedXY);
            JumpTo(unit, r.landing, speedXY, o.minSpeedZ, o.lookSpell, o.lookCaster);
            r.pushed = true;
            return r;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // PushOverEdge, PushAlong
    // ----------------------------------------------------------------------------------------------------------------

    EdgePushResult PushOverEdge(Unit* unit, std::span<Vec2 const> floor, EdgePushOptions const& options)
    {
        if (!CanPush(unit) || floor.size() < 3)
            return {};
        Vec2 const at = PlaneOf(unit);
        float const bearing = options.bearing ? *options.bearing
            : OutwardBearing(floor, at, unit->GetOrientation());
        return Jump(unit, PlanOverEdge(floor, at, bearing, options.beyondYd), options);
    }

    EdgePushResult PushAlong(Unit* unit, std::span<Vec2 const> floor, float bearing, float distanceYd,
        EdgePushOptions const& options)
    {
        if (!CanPush(unit) || floor.size() < 3 || distanceYd <= 0.f)
            return {};
        return Jump(unit, PlanKnockback(floor, PlaneOf(unit), bearing, distanceYd, options.beyondYd), options);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LethalBand
    // ----------------------------------------------------------------------------------------------------------------

    namespace
    {
        // One band's state, shared by the copies of its OnResolve callback (the registry copies the function).
        struct BandState
        {
            explicit BandState(LethalBandSpec const& s) : spec(s) { }

            LethalBandSpec spec;
            GraceBook grace;
            bool crumbled = false;
        };

        // A player or a player's pet / guardian (never a totem), alive, here, never a GM (nor a GM's pet).
        bool CountsForBand(Unit const* u, Map const* map)
        {
            if (!CanPush(u) || u->GetMap() != map)
                return false;
            Player const* controller = u->GetCharmerOrOwnerPlayerOrPlayerItself();
            return controller && !controller->IsGameMaster();
        }

        void PushOne(Unit* owner, BandState& b, Unit* u, uint64 now)
        {
            EdgePushOptions o;
            o.bearing = b.spec.pushBearing;
            o.beyondYd = b.spec.beyondYd;
            o.dropYd = b.spec.dropYd;
            o.landZ = b.spec.landZ;
            o.flightMs = b.spec.flightMs;
            if (b.spec.pushSpell)
                owner->CastSpell(u, b.spec.pushSpell, true);
            EdgePushResult const r = PushOverEdge(u, b.spec.floor, o);
            if (!r.pushed)
                return;
            b.grace.Grant(u->GetGUID().GetRawValue(), now + r.flightMs + kBandGraceExtraMs);
            LogMechanic(b.spec.dungeon, b.spec.boss, "lethal-band-push", "unit=" + u->GetName()
                + (u->IsPlayer() ? "" : " pet=1") + " yd=" + std::to_string(static_cast<int>(r.distance + 0.5f)));
            if (b.spec.onPush)
                b.spec.onPush(u);
        }

        // One tick of an armed band: the crumble (first tick only), then the registry's list (players inside) and
        // every pet / guardian inside, then the pushes. Collected first: a push can change the control sets.
        void TickBand(Map* map, ObjectGuid ownerGuid, BandState& b, BossMechanics::ResolveResult const& res)
        {
            Unit* owner = FindOwner(map, ownerGuid);
            if (!owner)
                return;
            if (!b.crumbled)
            {
                b.crumbled = true;
                LogMechanic(b.spec.dungeon, b.spec.boss, "lethal-band-crumble", "players="
                    + std::to_string(res.hits.size()));
                if (b.spec.onCrumble)
                    b.spec.onCrumble();
                owner = FindOwner(map, ownerGuid);
                if (!owner)
                    return;
            }

            BossMechanics::MechanicHandle const handle{ res.mechanicId };
            uint64 const now = NowMs();
            std::vector<ObjectGuid> victims;
            GuidUnorderedSet listed;
            auto add = [&](ObjectGuid g)
            {
                if (!b.grace.Has(g.GetRawValue(), now) && listed.insert(g).second)
                    victims.push_back(g);
            };
            for (ObjectGuid const& g : res.hits)
                add(g);
            if (b.spec.pets)
                for (auto const& ref : map->GetPlayers())
                {
                    Player* player = ref.GetSource();
                    if (!CountsForBand(player, map))
                        continue;
                    std::vector<Unit*> controlled(player->m_Controlled.begin(), player->m_Controlled.end());
                    for (Unit* u : controlled)
                        if (u && !u->IsPlayer() && CountsForBand(u, map) && Mechanic::Contains(owner, handle, u))
                            add(u->GetGUID());
                }

            for (ObjectGuid const& g : victims)
            {
                Unit* again = FindOwner(map, ownerGuid);
                if (!again)
                    break;
                Unit* u = ObjectAccessor::GetUnit(*again, g);
                if (CountsForBand(u, map))
                    PushOne(again, b, u, now);
            }
            b.grace.Prune(now);
        }
    }

    BossMechanics::MechanicRef LethalBand(Unit* owner, LethalBandSpec const& spec)
    {
        if (!owner || !owner->IsInWorld() || spec.width <= 0.f || spec.floor.size() < 3)
            return {};
        BossMechanics::MechanicRef ref = Mechanic::Zone(owner,
            BossMechanics::Shapes::Line(spec.from, spec.to, spec.width), spec.warn);
        if (!ref.IsValid())
            return ref;
        // Lethal() first, in the registering statement (refused after the commit; X4).
        ref.Lethal().Persistent(spec.lifetime, spec.tick).NoFillTimer();
        if (!spec.pets)
            ref.SparesPets();
        if (spec.color)
            ref.Color(*spec.color);
        if (spec.tag)
            ref.Tag(spec.tag);
        if (spec.zTolerance > 0.f)
            ref.ZTolerance(spec.zTolerance);

        Map* map = owner->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        auto state = std::make_shared<BandState>(spec);
        ref.OnResolve([map, ownerGuid, state](BossMechanics::ResolveResult const& r)
        {
            TickBand(map, ownerGuid, *state, r);
        });
        float const length = std::hypot(spec.to.GetPositionX() - spec.from.GetPositionX(),
            spec.to.GetPositionY() - spec.from.GetPositionY());
        LogMechanic(spec.dungeon, spec.boss, "lethal-band-raised", "length="
            + std::to_string(static_cast<int>(length + 0.5f)) + " width="
            + std::to_string(static_cast<int>(spec.width + 0.5f)) + " warn=" + std::to_string(spec.warn.count()));
        return ref;
    }

    BossMechanics::MechanicHandle LethalBands::Add(Unit* owner, LethalBandSpec const& spec)
    {
        BossMechanics::MechanicHandle const h = LethalBand(owner, spec);
        if (h)
            _bands.push_back(h);
        return h;
    }

    std::size_t LethalBands::AddEdges(Unit* owner, LethalBandSpec const& spec, std::span<std::size_t const> edges,
        float fromDepthYd, float toDepthYd, float z, float extendYd)
    {
        std::size_t added = 0;
        for (WallLine const& line : EdgeBands(spec.floor, edges, fromDepthYd, toDepthYd, extendYd))
        {
            LethalBandSpec band = spec;
            band.from = Position(line.from.x, line.from.y, z);
            band.to = Position(line.to.x, line.to.y, z);
            band.width = line.width;
            if (Add(owner, band))
                ++added;
        }
        return added;
    }

    void LethalBands::Clear(Unit* owner)
    {
        if (owner)
            for (BossMechanics::MechanicHandle const& h : _bands)
                Mechanic::Cancel(owner, h);
        _bands.clear();
    }

    bool LethalBands::Contains(Unit* owner, Unit const* who) const
    {
        if (!owner || !who)
            return false;
        return std::any_of(_bands.begin(), _bands.end(), [owner, who](BossMechanics::MechanicHandle const& h)
        {
            return Mechanic::Contains(owner, h, who);
        });
    }
}
