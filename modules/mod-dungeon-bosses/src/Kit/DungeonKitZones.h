/*
 * mod-dungeon-bosses, the shared dungeon kit (Scarlet Monastery WP-KT-SM, handoff section 3.11 #1 and #5): zones that
 * change over time. The pure rules are DungeonKitZoneLogic.h (GrowthPlan, NearestRung, BeamClock, BeamSegment).
 *
 *   GrowingZone     a persistent registry Zone whose radius grows in steps (F3: the registry cannot resize a zone, so
 *                   each step registers the grown zone and cancels the old one once the new one is live, the BRD
 *                   Doomgrip pattern), timed (fromYd -> toYd over overMs, a step every stepMs) or by hand (GrowTo /
 *                   Grow: the Librarian's mist, +3 yd per page), swapping the ground look's rung aura as it grows.
 *                   Ironspine's heroic Grave Rot, the Emerald Dream mist
 *   GrowingZones    a set of them owned by one AI (Ironspine's many rot pools): Add, Update, GrowTo, Cancel, Clear
 *   TurningBeams    L43 (Herod's Ravager's Beacon, hard mode): `count` beams evenly spaced around an anchor, turning
 *                   stepDeg every stepMs; each next step is a registry Line marked one step ahead (it resolves when the
 *                   beam gets there: the hit plus Weakened); Flip() reverses the turn (at each Blades of Light). An
 *                   optional look: a stalker at each beam's end, moved each step, and a chain spell from the anchor's
 *                   unit to it
 *
 * Owned by a boss AI (or an add's): Update from UpdateAI, Cancel / Stop / Clear from Reset, JustDied and
 * EnterEvadeMode (the registry also ends every zone of an owner that dies, evades or despawns; the kit then only
 * removes its looks). Every registration takes `configure`, a hook for registry options the spec does not name.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ZONES_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_ZONES_H

#include "BossMechanics.h"
#include "DungeonKitArena.h"
#include "DungeonKitZoneLogic.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Unit;

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Growing zone
    // ----------------------------------------------------------------------------------------------------------------

    // One visual rung: the ground look of a pool of `radiusYd` (a STATE aura such as the rot rungs 90550-90553).
    struct GrowRung
    {
        float radiusYd = 0.f;
        uint32 spellId = 0;
    };

    struct GrowingZoneSpec
    {
        BossMechanics::Anchor anchor;           // a point, or a unit the zone follows (the Librarian's book)
        float fromYd = 7.f;
        float toYd = 7.f;                       // timed growth target (== fromYd: none)
        uint32 overMs = 0;                      // timed growth: fromYd -> toYd over this long ...
        uint32 stepMs = 0;                      // ... one step every stepMs (0 / 0: grows by hand only)
        uint32 lifeMs = 0;                      // then it is gone (0: until Cancel or the owner's encounter ends)
        uint32 warnMs = 1500;                   // the first zone's warning (its marker before the first tick)
        uint32 stepWarnMs = 1000;               // each grown zone's warning; the old one keeps ticking until then
        uint32 tickMs = 1000;
        float pct = 5.f;                        // per tick, % of reference non-tank health
        float tankPct = -1.f;                   // >= 0: the tank takes this % of tank health instead
        uint8 school = 0;                       // SpellSchools 0 physical .. 6 arcane
        uint32 spellId = 0;                     // a dungeon copy of the resolve spell (0: by school)
        uint32 rider = 0;                       // cast on every unit hit (Drowsy; 0: none)
        std::optional<BossMechanics::Color> color;
        uint32 tag = 0;
        // Ground looks per radius (the nearest rung to the current radius is worn; empty: no look), worn by `look`
        // (a unit), else the anchor's unit, else a stalker of `lookEntry` summoned on the anchor point by the owner
        // (0: none). The rung auras are cast triggered on the look's own unit.
        std::vector<GrowRung> rungs;
        ObjectGuid look;
        uint32 lookEntry = 0;
        // Extra registry options on every registration (Eligible, Within, ZTolerance, OnHit ...). Capture guids only.
        std::function<void(BossMechanics::MechanicRef&)> configure;
        char const* dungeon = "kit";            // LogMechanic: "<dungeon> <boss> <name>-start|-grow|-end"
        char const* boss = "zone";
        char const* name = "growing-zone";
    };

    class GrowingZone
    {
    public:
        // Registers the zone at fromYd. False (and inactive) when the registry refuses it or there is no owner.
        bool Start(Unit* owner, GrowingZoneSpec spec);
        // Timed growth, the old zone's hand-over, the life's end. Call it every tick while Active().
        void Update(Unit* owner, uint32 diff);
        // A step by hand to `radiusYd` (no-op at the same radius). Stops any timed growth still to come.
        void GrowTo(Unit* owner, float radiusYd);
        void Grow(Unit* owner, float deltaYd) { GrowTo(owner, _radius + deltaYd); }
        // The zones, the look's rung aura and the summoned look go now.
        void Cancel(Unit* owner);

        bool Active() const { return _active; }
        float Radius() const { return _radius; }
        BossMechanics::MechanicHandle Handle() const { return _zone; }
        uint32 ElapsedMs() const { return _elapsedMs; }

    private:
        // Registers the zone at `radius` with `warnMs`, keeps the old one ticking until it is live.
        bool Register(Unit* owner, float radius, uint32 warnMs);
        void WearRung(Unit* owner, float radius);
        void ClearLook(Unit* owner);
        Unit* LookUnit(Unit* owner) const;

        GrowingZoneSpec _spec;
        GrowthPlan _plan;
        BossMechanics::MechanicHandle _zone;
        BossMechanics::MechanicHandle _old;
        uint32 _oldEndMs = 0;                   // _elapsedMs at which _old is canceled
        uint32 _elapsedMs = 0;
        float _radius = 0.f;
        bool _timed = false;
        bool _active = false;
        ObjectGuid _summonedLook;
        uint32 _rungSpell = 0;
    };

    // Many growing zones of one owner. Ids start at 1; 0 is a refused Add.
    class GrowingZones
    {
    public:
        uint32 Add(Unit* owner, GrowingZoneSpec spec);
        void Update(Unit* owner, uint32 diff);      // also forgets zones whose life has ended
        void GrowTo(Unit* owner, uint32 id, float radiusYd);
        void Grow(Unit* owner, uint32 id, float deltaYd);
        void Cancel(Unit* owner, uint32 id);
        void Clear(Unit* owner);
        GrowingZone const* Get(uint32 id) const;
        std::size_t Count() const { return _zones.size(); }

    private:
        struct Entry
        {
            uint32 id = 0;
            GrowingZone zone;
        };

        std::vector<Entry> _zones;
        uint32 _nextId = 1;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Turning beams (L43)
    // ----------------------------------------------------------------------------------------------------------------

    struct TurningBeamsSpec
    {
        Position anchor;                        // the turning center (the planted axe); its z is the lanes' height
        uint8 count = 2;                        // evenly spaced (2: opposite each other)
        float startBearing = 0.f;               // radians, beam 0's first bearing
        float stepDeg = 30.f;
        uint32 stepMs = 1500;                   // each next step is marked this far ahead
        int direction = 1;                      // +1 counter-clockwise, -1 clockwise
        float innerYd = 3.f;                    // the lane starts this far off the anchor
        float lengthYd = 14.f;                  // ... and runs this long, or to the wall:
        Arena const* clip = nullptr;            // stop `inset` short of this arena's edge (the pit's)
        float inset = 0.5f;
        float widthYd = 4.f;
        float pct = 45.f;                       // % of reference non-tank health
        float tankPct = -1.f;
        uint8 school = 1;                       // SPELL_SCHOOL_HOLY
        uint32 spellId = 0;
        bool weakened = true;
        std::optional<BossMechanics::Color> color;
        uint32 tag = 0;
        // Look: a stalker of endEntry at each beam's end (summoned by the owner at Start, moved each step), and
        // `beamSpell` cast by `beamSource` (the axe stalker) on each (0 / empty: no look).
        uint32 endEntry = 0;
        uint32 beamSpell = 0;
        ObjectGuid beamSource;
        std::function<void(BossMechanics::MechanicRef&)> configure;
        char const* dungeon = "kit";
        char const* boss = "beams";
        char const* name = "turning-beams";
    };

    class TurningBeams
    {
    public:
        // Marks the first step (resolving stepMs from now) and raises the look on it. False with no owner.
        bool Start(Unit* owner, TurningBeamsSpec spec);
        // Every stepMs: the marked step resolves (the registry), the look moves onto it, the next step is marked.
        void Update(Unit* owner, uint32 diff);
        // Reverse the turn from the next marked step on.
        void Flip();
        // Cancels the marked step and removes the look.
        void Stop(Unit* owner);

        bool Active() const { return _active; }
        BeamClock const& Clock() const { return _clock; }

    private:
        void MarkNext(Unit* owner);
        void PlaceLook(Unit* owner, BeamClock const& at);

        TurningBeamsSpec _spec;
        BeamClock _clock;
        std::vector<BossMechanics::MechanicHandle> _marked;
        std::vector<ObjectGuid> _ends;
        uint32 _stepLeftMs = 0;
        bool _active = false;
    };
}

#endif
