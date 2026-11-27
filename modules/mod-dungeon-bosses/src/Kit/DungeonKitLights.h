/*
 * mod-dungeon-bosses, the shared dungeon kit (Gnomeregan WP-KT-G, handoff sections 3.11 and 3.4 F23, F53): turning
 * lights. The pure rules are DungeonKitLightLogic.h (LightClock, SweptSector, InLight, TouchLatch).
 *
 *   TurningLights  `count` cones evenly spaced around an anchor (a fixed point, or a unit the lights ride on: the
 *                  Alert System's light stalker, Thermaplugg walking with his tank), turning continuously. Each light
 *                  is a stalker of its own (summoned by the owner at Start) that the kit keeps on the anchor and turns
 *                  every tick; its registry cone (FollowFacing, telegraph-only, the whole life) is the marker and the
 *                  bots' live hazard (BM poses it at +-FacingSlackDeg). The script judges the touch: every lit tick,
 *                  each eligible player inside a light is Spotted at most once per latch (shared by all the lights),
 *                  and onSpotted runs. The bot look ahead: per light, the sector its cone sweeps over the next
 *                  lookAheadMs (the stop first, then the turn the way it now goes) as a telegraph-only cone Zone on
 *                  the anchor, registered anew every lookAheadStepMs and at once on Reverse and SetSpeed (the new one
 *                  first, then the old one canceled), so bots leave the floor the light is about to cross, on the
 *                  side it turns to.
 *
 * Normal (MA1, a lock-on and one 60 degree sweep): count 1, startBearing at the player, litAfter 2000 (the dim
 * warning: the light holds and is not judged), degPerSec 20, direction -1, life 5000, lookAheadMs 5000 with
 * lookAheadStepMs 0 (one sector for the whole sweep) and drawLookAhead (the swept floor is marked).
 * Heroic (MA2, MA4): count 2, litAfter 3000, degPerSec 12, life 0; Reverse(2000) every 15-25 s; SetSpeed(+10%) in
 * onSpotted. The Whole Workshop (MT23): anchorUnit = Thermaplugg, lengthYd to the wall.
 *
 * Owned by one AI: Update from UpdateAI, Stop from Reset, JustDied and EnterEvadeMode (the registry also ends the
 * cones of an owner that dies or evades; the kit then despawns the stalkers). Lambdas capture guids only.
 *
 *     DungeonKit::TurningLights _lights;
 *     _lights.Start(me, { .anchorPoint = spot, .stalkerEntry = NPC_LIGHT_STALKER, .count = 2, .startBearing = o,
 *         .degPerSec = 12.f, .angleDeg = 30.f, .lengthYd = 30.f, .litAfter = 3000ms,
 *         .onSpotted = [](Creature* owner, Player* who, uint8 light) { ... }, .dungeon = "gnomer-build",
 *         .boss = "alert", .name = "lights" });
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LIGHTS_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LIGHTS_H

#include "BossMechanics.h"
#include "DungeonKitLightLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <vector>

class Creature;
class Player;

namespace DungeonKit
{
    struct TurningLightsSpec
    {
        // The anchor: a unit the lights ride on (its position each tick; its facing is never used), else the point.
        ObjectGuid anchorUnit;
        Position anchorPoint;
        uint32 stalkerEntry = 0;            // one per light: a passive, unselectable stalker (its display is the look)
        uint8 count = 1;
        float startBearing = 0.f;           // radians, light 0's bearing at Start
        float degPerSec = 12.f;
        int direction = 1;                  // +1 counter-clockwise, -1 clockwise
        float angleDeg = 30.f;              // each cone's full opening
        float lengthYd = 30.f;
        float zBand = 6.f;                  // |dz| from the anchor that is still lit (the registry's ZTolerance too)
        Milliseconds litAfter{ 0 };         // dark first: the cone shows as a warning, holds still, judges nobody
        Milliseconds life{ 0 };             // then Stop and onEnd (0: until Stop)
        Milliseconds latch{ 3000 };         // per player, across all the lights
        // Bot look ahead: the sector each light sweeps over the next lookAheadMs, registered every lookAheadStepMs
        // (0: once at Start, and again only on Reverse or SetSpeed). lookAheadMs 0: none.
        Milliseconds lookAhead{ 3000 };
        Milliseconds lookAheadStep{ 500 };
        bool drawLookAhead = false;         // false: NoTelegraph (bots only); true: drawn (the normal swept floor)
        bool drawLights = true;             // false: NoTelegraph cones (a display on the stalker is the look)
        std::optional<BossMechanics::Color> color;
        std::optional<BossMechanics::Color> lookAheadColor;
        uint32 tag = 0;
        // Who can be Spotted besides the kit's own rule (alive, in the world, no GM, within zBand): e.g. in combat
        // with the owner, or inside the hall. Empty: everyone on the map. Capture guids only.
        std::function<bool(Player* who)> eligible;
        // Every Spotted player, after the tick's judge (Reverse, SetSpeed and Stop are safe here). light: the light
        // that caught them (TrySpot passes its own). Capture guids only.
        std::function<void(Creature* owner, Player* who, uint8 light)> onSpotted;
        std::function<void(Creature* owner)> onEnd;                     // the life ran out (not on Stop)
        // Extra registry options on every light cone and every look-ahead zone (Within, ZTolerance ...).
        std::function<void(BossMechanics::MechanicRef&)> configureLight;
        std::function<void(BossMechanics::MechanicRef&)> configureLookAhead;
        char const* dungeon = "kit";        // LogMechanic: "<dungeon> <boss> <name>-start|-lit|-spotted|-reverse|..."
        char const* boss = "lights";
        char const* name = "lights";
    };

    class TurningLights
    {
    public:
        static uint32 constexpr kForeverMs = 3600000;       // a cone "until Stop": an hour outlives any fight
        static uint32 constexpr kSyncMs = 250;              // the stalkers' client update (the server's is every tick)
        static uint8 constexpr kNoLight = 0xFF;             // TrySpot's light when no light caught them

        // Summons the stalkers, registers the cones and the first look ahead. False (and inactive) with no owner, no
        // stalker entry, no anchor unit found, or when no stalker could be summoned.
        bool Start(Creature* owner, TurningLightsSpec spec);
        // Turns the lights, moves the stalkers onto the anchor, judges the touches, refreshes the look ahead.
        void Update(Creature* owner, uint32 diff);
        // MA4: stop for `stop`, then turn the other way. The look ahead is registered anew at once.
        void Reverse(Creature* owner, Milliseconds stop);
        // The lights stand still for `hold` (not reversed).
        void Hold(Creature* owner, Milliseconds hold);
        void SetSpeed(Creature* owner, float degPerSec);
        // Spots `who` through the shared latch (the 30 yd cameras, a netted player): onSpotted runs now when the latch
        // lets it. True when it did.
        bool TrySpot(Creature* owner, Player* who, uint8 light = kNoLight);
        // Cancels the cones and the look ahead, despawns the stalkers.
        void Stop(Creature* owner);

        bool Active() const { return _active; }
        bool Lit() const { return _active && _lit; }
        LightClock const& Clock() const { return _clock; }
        float BearingOf(uint8 i) const { return _clock.BearingOf(i); }
        uint32 ElapsedMs() const { return _elapsedMs; }
        uint32 SpottedCount() const { return _spotted; }
        // The light's stalker (the cone's anchor), for a look aura or a beam.
        ObjectGuid StalkerOf(uint8 i) const { return i < _stalkers.size() ? _stalkers[i] : ObjectGuid::Empty; }
        BossMechanics::MechanicHandle ConeOf(uint8 i) const
        {
            return i < _cones.size() ? _cones[i] : BossMechanics::MechanicHandle{};
        }

    private:
        bool AnchorAt(Creature* owner, Position& out) const;
        void PlaceStalkers(Creature* owner, Position const& at, bool syncClients);
        void RegisterLookAhead(Creature* owner);
        void CancelLookAhead(Creature* owner, std::vector<BossMechanics::MechanicHandle>& handles);
        void Judge(Creature* owner, Position const& at, std::vector<std::pair<ObjectGuid, uint8>>& spotted);
        void Fire(Creature* owner, std::vector<std::pair<ObjectGuid, uint8>> const& spotted);
        uint32 HorizonMs() const;

        TurningLightsSpec _spec;
        LightClock _clock;
        TouchLatch _latch;
        std::vector<ObjectGuid> _stalkers;
        std::vector<BossMechanics::MechanicHandle> _cones;
        std::vector<BossMechanics::MechanicHandle> _ahead;
        uint32 _elapsedMs = 0;
        uint32 _darkLeftMs = 0;
        uint32 _aheadLeftMs = 0;
        uint32 _syncLeftMs = 0;
        uint32 _spotted = 0;
        bool _lit = false;
        bool _active = false;
    };
}

#endif
