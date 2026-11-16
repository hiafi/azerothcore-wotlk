/*
 * mod-dungeon-bosses, the shared dungeon kit: the script side of mod-boss-mechanics' rolling fronts (Blackrock Spire
 * WP-KT-B2, handoff section 3.11 #7; BM README "Rolling fronts", MechanicFront.h). BM registers one front and judges
 * it; the kit runs a sequence of them on a clock the boss AI drives:
 *
 *   FrontDirector::StartRings   a ring sequence (Emberseer EM3): Mechanic::ConeFront per ring with its slice turned,
 *                               each registered when the plan says (SP: as the ring before it launches), a
 *                               Mechanic::FrontSafe per ring (the bot tank leads the boss into the slice), the
 *                               visual carriers at each launch, the launch callback (Flame Wave)
 *   FrontDirector::StartWalls   a wall sequence (Rend RG6): Mechanic::LineFront per wall, each gap placed off the live
 *                               pools inside the usable span, a later wall's gap on the other side near the previous
 *                               one (a fallback chain always places one), carriers along the wall moving with it
 *   Update / Cancel / Clear     from UpdateAI / Reset, JustDied, EnterEvadeMode (Clear cancels the registered fronts
 *                               and their safe slots and despawns every carrier)
 *
 * The pure plan (timing, slices, gaps, carrier spots) is DungeonKitFrontLogic.h (DungeonKit::Fronts). Damage, school,
 * Weakened, rider and tag are the boss's: `decorate` is called on every front's ref in its registering statement.
 * Callbacks run from Update / Start only (inside the owning AI), so they may capture the AI's `this`; they must not
 * call Start, Cancel or Clear on the same director (refused and logged while it runs a callback).
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FRONTS_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FRONTS_H

#include "BossMechanics.h"
#include "DungeonKit.h"
#include "DungeonKitFrontLogic.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <vector>

class Unit;

namespace DungeonKit
{
    class PuddleField;

    // Invisible units that carry a front's look and move with its band (SP RG6 "Frost wall, invisible trigger"; a
    // ring's fire). Summoned at each launch (timed despawn at the front's end), `aura` cast on themselves, moved by
    // spline at the front's speed. entry 0: none.
    struct FrontCarrierSpec
    {
        uint32 entry = 0;
        uint32 aura = 0;
        float spacingYd = 6.f;          // along the wall, or along the ring's arc at the band's start
        uint32 maxCount = 16;           // per front (0: no cap)
        float zOffset = 0.f;
    };

    // Options on each front's ref (Damage, School, Weakened, Rider, Tag, Color). Not Persistent, Projectile,
    // OutAndBack, FacingOffset, Rear, ExcludeSourceEnd, AnchorOn, Park or DropSpot (BM refuses them on a front).
    using FrontDecorate = std::function<void(BossMechanics::MechanicRef& ref, uint32 index)>;
    // A front launched (its band starts to roll): `at` is the apex or the start point, oriented along the slice's
    // middle (rings) or the facing (walls).
    using FrontLaunched = std::function<void(uint32 index, Position const& at)>;

    struct RingSequence
    {
        Fronts::RingSequenceSpec plan;      // rings, first slice, turn, slice width, radii, speed, warn, spacing
        FrontDecorate decorate;
        // Mechanic::FrontSafe per ring: the bot tank of `parked` (empty: the owner) leads it into the ring's slice and
        // stands there with it, until the band's back edge passes safeUntilYd (0: the whole ring).
        bool safeSlot = true;
        ObjectGuid parked;
        float safeUntilYd = 0.f;
        std::optional<BossMechanics::SpotBounds> within;    // the room: bots plan inside it (BM Within)
        FrontCarrierSpec carriers;
        FrontLaunched onLaunch;
        // A cue `cueMs` after the start (ms on the sequence's clock), called once with the apex: user ruling (HANDOFF
        // section 10, rolling fronts 1): ring 0 shows its slice 5 s ahead (plan.firstWarnMs 5000) while the nova keeps
        // its 2.5 s warning, so the boss registers the nova from onCue at cueMs 2500 and it erupts as ring 0 launches.
        uint32 cueMs = 0;
        std::function<void(Position const& apex)> onCue;
        char const* dungeon = "kit";
        char const* boss = "front";
    };

    struct WallSequence
    {
        float facing = 0.f;                 // radians: the way the walls travel
        float travelYd = 0.f;               // over once the back edge passes this far from the start line
        float widthYd = 0.f;                // across, centred on the start point (the room's widest part)
        float bandYd = Fronts::kDefaultBandYd;
        float speed = Fronts::kDefaultSpeed;
        uint32 walls = 1;                   // RG6: N 1, H 2
        uint32 firstWarnMs = 3000;          // RG6: the wall starts 3 s after the call
        uint32 spacingMs = 3000;            // RG6 heroic: 3 s apart
        // false (default): every wall and gap registers at the start (the second gap is seen from the call, so a
        // player can plan the cross behind the first wall). true: wall k registers at wall k-1's launch, its gap off
        // the pools then.
        bool revealAtPreviousLaunch = false;
        Fronts::WallGapSpec gaps;           // gap width, usable span, edge, pool margin, other side, within
        // The live pools, read when a wall registers (its gap is never on one). PoolsOf(field) for a PuddleField.
        std::function<std::vector<Fronts::PoolCircle>()> pools;
        FrontDecorate decorate;
        std::optional<BossMechanics::SpotBounds> within;    // give every wall the room (RF: outside reads "safe")
        // Mechanic::FrontSafe on gap 0 (a unit to lead into the gap). Off by default (RG6 parks nothing).
        bool safeSlot = false;
        ObjectGuid parked;
        float safeUntilYd = 0.f;
        FrontCarrierSpec carriers;
        FrontLaunched onLaunch;
        char const* dungeon = "kit";
        char const* boss = "front";
    };

    // A PuddleField's live puddles (armed or arming) as pools for a wall's gap placement.
    std::vector<Fronts::PoolCircle> PoolsOf(PuddleField const& field);

    class FrontDirector
    {
    public:
        // Starts a sequence at `apex` / `start` (a point; its orientation is ignored) and registers whatever the plan
        // registers at 0 (ring 0, or every wall). Returns its id (0: refused: no owner, an invalid plan).
        uint32 StartRings(Unit* owner, Position const& apex, RingSequence spec);
        uint32 StartWalls(Unit* owner, Position const& start, WallSequence spec);

        // From UpdateAI (every tick, also during casts: the clock must not pause).
        void Update(Unit* owner, uint32 diff);
        // Cancels a sequence's registered fronts and safe slots and despawns its carriers.
        void Cancel(Unit* owner, uint32 id);
        void Clear(Unit* owner);

        bool Active() const { return !_seqs.empty(); }
        bool Active(uint32 id) const { return Find(id) != nullptr; }
        // The fronts a sequence registered so far (handles of cancelled or finished ones may be stale).
        std::vector<BossMechanics::MechanicHandle> Handles(uint32 id) const;
        // A ring sequence's plan (ms from its start; nullptr: none or a wall sequence).
        std::vector<Fronts::RingStep> const* RingPlan(uint32 id) const;
        // A wall sequence's gaps placed so far, in wall order.
        std::vector<Fronts::GapPick> Gaps(uint32 id) const;
        // ms since a sequence started (0: none).
        uint32 ElapsedMs(uint32 id) const;

    private:
        struct Step
        {
            uint32 index = 0;
            uint32 registerMs = 0;
            uint32 launchMs = 0;
            uint32 overMs = 0;
            float sliceBearing = 0.f;       // rings
            float startYd = 0.f;            // rings
            std::optional<Fronts::GapPick> gap;     // walls, once registered
            bool registered = false;
            bool launched = false;
            BossMechanics::MechanicHandle front;
            BossMechanics::MechanicHandle safe;
            std::vector<ObjectGuid> carriers;
        };

        struct Sequence
        {
            uint32 id = 0;
            bool rings = true;
            Position at;
            uint64 startMs = 0;
            RingSequence ring;
            WallSequence wall;
            std::vector<Fronts::RingStep> plan;
            std::vector<Step> steps;
            bool cued = false;
        };

        Sequence const* Find(uint32 id) const;
        void Tick(Unit* owner, Sequence& s);
        void Register(Unit* owner, Sequence& s, Step& step, uint32 elapsed);
        void Launch(Unit* owner, Sequence& s, Step& step);
        static void Despawn(Unit* owner, Step& step);
        static void CancelStep(Unit* owner, Step& step);
        Fronts::WallFrame FrameOf(Sequence const& s) const;

        std::vector<Sequence> _seqs;
        uint64 _clockMs = 0;
        uint32 _nextId = 1;
        bool _busy = false;                 // inside Start / Update: a callback may not reshape _seqs
    };
}

#endif
