/*
 * mod-dungeon-bosses, the shared dungeon kit: pushes over a floor's real edge and lethal edge bands (Blackrock Depths
 * WP-KT-D1, handoff section 3.11 #2 and #3). The pure rules are DungeonKitEdgeLogic.h.
 *
 *   PushOverEdge   a computed JumpTo from anywhere on the floor to a point `beyondYd` past the real edge (Lord
 *                  Incendius's Crumbling Ground and Arm Sweep throw): never a fixed knockback, so a unit deep in a
 *                  later band still goes over
 *   PushAlong      a fixed-length throw (Magma Fist's 10 yd) made deterministic: it lands on the floor, or, when the
 *                  throw crosses the edge, past it (never on the rim)
 *   LethalBand     a lethal two-point band: a telegraph-only persistent registry Line, `.Lethal()` from the warning on
 *                  (bots keep out; the navmesh still sees floor there), a 5 s warning, then everyone in the band at
 *                  the crumble and anyone who steps in later is pushed over the edge (PushOverEdge), pets too
 *   LethalBands    the bands one AI raised: Add, AddEdges (one per polygon edge between two depths), Clear
 *
 * The push is the fall; the kit kills no one. A floor 38 yd over lava (Incendius) is lethal only with the fall damage
 * and the lava: pair it with a FallWatch (DungeonKitChase.h) whose onCatch kills, if the fight must never be survived.
 * Lambdas kept by the registry capture the map and guids only, never a Unit*.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_EDGES_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_EDGES_H

#include "BossMechanics.h"
#include "DungeonKit.h"
#include "DungeonKitEdgeLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <span>
#include <vector>

class Unit;

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // PushOverEdge, PushAlong
    // ----------------------------------------------------------------------------------------------------------------

    struct EdgePushOptions
    {
        std::optional<float> bearing;           // the push's direction (Arm Sweep: the sweep's); none: OutwardBearing
        float beyondYd = kEdgeBeyondYd;         // past the real edge
        // A player's jump ends `dropYd` under the start height, past the rim, and the client falls from there (a
        // real fall). Other units (pets, guardians) do not fall on their own: their jump ends on the ground below the
        // landing (Map height, searched down `groundSearchYd`), or `landZ` when given.
        float dropYd = kEdgeDropYd;
        std::optional<float> landZ;             // every unit's jump ends at this height (the lava's surface)
        float groundSearchYd = 80.f;
        uint32 flightMs = kEdgeFlightMs;        // the jump's duration (its speed follows, at least kEdgeMinSpeedXY)
        float minSpeedZ = 0.f;
        uint32 lookSpell = 0;                   // JumpTo's look: `lookCaster` casts it on the unit first
        Unit* lookCaster = nullptr;
    };

    struct EdgePushResult
    {
        bool pushed = false;
        bool overEdge = false;
        Position landing;
        float distance = 0.f;
        uint32 flightMs = 0;
    };

    // Throws `unit` over the edge of `floor` (the real walkable edge polygon). False / not pushed for a dead unit, one
    // not in the world, a totem, or a vehicle passenger.
    EdgePushResult PushOverEdge(Unit* unit, std::span<Vec2 const> floor, EdgePushOptions const& options = {});

    // Throws `unit` `distanceYd` along `bearing`: on the floor when the throw stays on it (the jump ends on the floor
    // there), else over the edge as PushOverEdge (options.bearing is ignored).
    EdgePushResult PushAlong(Unit* unit, std::span<Vec2 const> floor, float bearing, float distanceYd,
        EdgePushOptions const& options = {});

    // ----------------------------------------------------------------------------------------------------------------
    // LethalBand
    // ----------------------------------------------------------------------------------------------------------------

    struct LethalBandSpec
    {
        Position from;                          // the band's centre line on the floor (z: the floor height there)
        Position to;
        float width = 4.f;                      // SP S2 909: the outer 4 yd
        std::vector<Vec2> floor;                // the real edge polygon the push goes over (required)
        Milliseconds warn{ kBandWarnMs };       // the edge marker before the crumble (SP: 5 s)
        Milliseconds lifetime{ 4 * 3600 * 1000 };   // the rest of the fight (it ends with the encounter or Clear)
        Milliseconds tick{ kWallTickMs };
        float zTolerance = 0.f;                 // > 0: the registry hitbox's ZTolerance
        bool pets = true;                       // pets and guardians are pushed too (never totems)
        std::optional<float> pushBearing;       // none: each unit's own way out (OutwardBearing)
        float beyondYd = kEdgeBeyondYd;
        float dropYd = kEdgeDropYd;
        std::optional<float> landZ;
        uint32 flightMs = kEdgeFlightMs;
        uint32 pushSpell = 0;                   // cast (triggered) by the owner on each pushed unit for the look
        std::optional<BossMechanics::Color> color;      // default: the encounter's get-out color
        uint32 tag = 0;
        char const* dungeon = "kit";            // LogMechanic: "<dungeon> <boss> lethal-band ..."
        char const* boss = "band";
        // Capture guids only.
        std::function<void()> onCrumble;                // once, at the first tick (the burst, the emote)
        std::function<void(Unit* pushed)> onPush;       // after each push
    };

    // Registers (and, at the end of the calling statement, commits) one band: a telegraph-only persistent Line from
    // `spec.from` to `spec.to` of `spec.width`, warn `spec.warn`, ticking every `spec.tick` for `spec.lifetime`,
    // NoFillTimer, Lethal, no Eligible and no TankExempt (every bot keeps out, the tank too). Every tick pushes each
    // player in it (the registry's hits) and each pet / guardian in it over the edge of `spec.floor`, at most once
    // per flight (a grace). Further options may be chained on the returned ref (Color, Within); do not replace its
    // OnResolve, and do not add Damage, Weakened or OnHit. Returns an invalid ref when refused (no owner, width <= 0,
    // a floor of fewer than 3 points).
    BossMechanics::MechanicRef LethalBand(Unit* owner, LethalBandSpec const& spec);

    // The bands one boss AI raised (a crumble step adds 4, or 2 on Lord of the Lake's long edges). Clear from Reset /
    // JustDied / EnterEvadeMode (the registry also ends an owner's mechanics on death, evade and despawn).
    //
    //     DungeonKit::LethalBands _bands;
    //     LethalBandSpec band;                     // floor, warn, color, onCrumble ...
    //     band.floor = { kCausewayFloor.begin(), kCausewayFloor.end() };
    //     _bands.AddEdges(me, band, kLongEdges, 0.f, 4.f, kFloorZ);    // the first crumble: the outer 4 yd
    //     void JustDied(Unit*) override { _bands.Clear(me); ... }
    class LethalBands
    {
    public:
        BossMechanics::MechanicHandle Add(Unit* owner, LethalBandSpec const& spec);
        // One band per listed edge of `spec.floor` (all edges when `edges` is empty) between the depths, at height
        // `z`: EdgeBand's line and width replace spec.from / to / width. Returns how many registered.
        std::size_t AddEdges(Unit* owner, LethalBandSpec const& spec, std::span<std::size_t const> edges,
            float fromDepthYd, float toDepthYd, float z, float extendYd = 0.f);
        void Clear(Unit* owner);

        // A unit stands in any live band now (the registry's hitbox).
        bool Contains(Unit* owner, Unit const* who) const;
        std::size_t Count() const { return _bands.size(); }

    private:
        std::vector<BossMechanics::MechanicHandle> _bands;
    };
}

#endif
