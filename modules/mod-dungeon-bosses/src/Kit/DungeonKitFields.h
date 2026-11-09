/*
 * mod-dungeon-bosses, the shared dungeon kit: the engine helpers Stratholme wave 1 adds (WP-KT-1,
 * .agents/plans/stratholme-build/stratholme-build.HANDOFF.md section 3.11 #12, #16-#24). The pure rules are
 * DungeonKitFloor.h and DungeonKitFlow.h; the generic percent spells are DungeonKitSpells.cpp; the generic leash preset
 * is ArenaGuard.h LeashPreset. Include this header (it includes DungeonKit.h).
 *
 *   FloorPathOnMap      FloorPath with the map's floor as the probe; MoveAlongFloor runs a unit along it (#12)
 *   PuddleField         a union of telegraph-only persistent Zones: bots avoid them, the script applies its effect
 *                       once per tick to each player inside any of them, however many overlap (#16)
 *   RegistryHit         a script-picked hit on exact players through the registry: damage, Weakened, rider, ledger
 *                       and cleanup like any mechanic, no marker (#18)
 *   WeightedShares      a shared hit split evenly, each share raised by the taker's stacks (#19)
 *   FollowThenLand      a circle that follows a player and lands where they stand; it never hits that player (#20)
 *   PickFloorSpot       a random floor point in an arena near a point, outside avoid circles (#21)
 *   SummonWave          adds on a list of points into a SummonList, tracked by the boss's encounter (#22)
 *   HoldInUnit          a player held inside a unit (a cocoon, a tomb): released when the holder dies or despawns,
 *                       at a timeout, or when the held player dies or leaves (#23)
 *
 * Lambdas kept by the registry (OnResolve, OnHit) and by these helpers capture guids only, never a Unit*.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FIELDS_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FIELDS_H

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "DungeonKit.h"
#include "DungeonKitFloor.h"
#include "DungeonKitFlow.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <unordered_map>
#include <utility>
#include <vector>

class Creature;
class Player;
class SummonList;
class Unit;
class WorldObject;

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // FloorPath on the map (#12)
    // ----------------------------------------------------------------------------------------------------------------

    // FloorPath (DungeonKitFloor.h) from `from` to `to` with `ref`'s map as the probe (the floor under each point,
    // searched from maxStepZ above the last point's height).
    std::vector<FloorPathPoint> FloorPathOnMap(WorldObject const* ref, Vec2 from, Vec2 to, float startZ,
        float step = kFloorPathStepYd, float maxStepZ = kFloorPathMaxStepZ);

    // Moves `mover` along `path` (a spline through every point; no pathfinding, so it follows the floor the path
    // sampled) at `speed` yd/s (0: its own run speed). False when the path has fewer than two points or the unit
    // cannot move. Watch `mover->movespline->Finalized()` for the end.
    bool MoveAlongFloor(Unit* mover, std::vector<FloorPathPoint> const& path, float speed = 0.f);

    // ----------------------------------------------------------------------------------------------------------------
    // PuddleField (#16)
    // ----------------------------------------------------------------------------------------------------------------

    struct PuddleSpec
    {
        float radius = 5.f;
        Milliseconds armAfter{ 1000 };              // the marker shows at once; the puddle counts once armed
        Milliseconds life{ 0 };                     // 0: until Remove / Clear (the whole fight)
        bool merge = false;                         // a center inside a live puddle adds nothing (the merge rule)
        std::optional<BossMechanics::Color> color;  // default: the encounter's get-out color
        bool fillTimer = true;                      // false: outline only until armed (NoFillTimer)
        uint32 tag = 0;
    };

    // Owned by one boss AI. Every puddle is a telegraph-only persistent Zone (Circle on its spot, warn = armAfter): it
    // draws, bots avoid it, nobody is hit by the registry. Update polls the map's players every kPollMs and, every
    // `tick`, calls `onTick(player, msInside)` once for each living player (not a GM) inside any armed puddle, with
    // the time that player has stood inside the union without a break (Stuck after 2 s, an infection after 0.5 s).
    // Call Update from UpdateAI (in combat) and Clear from Reset / JustDied / EnterEvadeMode.
    //
    //     DungeonKit::PuddleField _webs{ 1000ms };
    //     _webs.Add(me, spot, { .radius = 5.f, .merge = true });
    //     _webs.Update(me, diff, [this](Player* p, uint32 inside) { if (inside >= 2000) Stuck(p); });
    class PuddleField
    {
    public:
        static uint32 constexpr kPollMs = 250;
        static Milliseconds constexpr kWholeFight{ 4 * 3600 * 1000 };   // a life-0 puddle's registry duration

        using TickFn = std::function<void(Player* player, uint32 msInside)>;

        explicit PuddleField(Milliseconds tick = Milliseconds(1000), float zBand = PuddleSet::kDefaultZBand);

        // A puddle at `at` (its z is the floor height the caller found). Returns the new puddle's id, or the old
        // one's with `merged` (the merge rule); id 0: refused (no owner, radius <= 0).
        PuddleSet::AddResult Add(Creature* owner, Position const& at, PuddleSpec const& spec);

        void Update(Creature* owner, uint32 diff, TickFn const& onTick);

        void Remove(Creature* owner, uint32 id);
        void Clear(Creature* owner);

        // Armed puddles only (a boss standing in any: Kindled; a pile raising in the rot).
        bool Contains(Position const& p) const;
        bool Contains(WorldObject const* o) const;
        std::optional<uint32> PuddleAt(Position const& p) const;
        // The puddle `id` (nullptr: gone).
        Puddle const* Find(uint32 id) const { return _set.Find(id); }
        std::vector<Puddle> const& All() const { return _set.All(); }
        std::size_t Count() const { return _set.Size(); }
        // The union's floor in square yd (DungeonKitFloor.h PuddleSet::CoveredArea).
        float CoveredArea(float cell = 0.25f) const { return _set.CoveredArea(_clockMs, cell); }
        // The players inside the union at the last poll, with their time inside.
        std::vector<std::pair<uint64, uint32>> const& Inside() const { return _inside; }
        uint64 ClockMs() const { return _clockMs; }

    private:
        void CancelZone(Creature* owner, uint32 id);

        Milliseconds _tick;
        PuddleSet _set;
        InsideClock _clock;
        std::unordered_map<uint32, BossMechanics::MechanicHandle> _zones;
        std::vector<std::pair<uint64, uint32>> _inside;
        uint64 _clockMs = 0;
        uint32 _pollMs = 0;
        uint32 _tickMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // RegistryHit (#18)
    // ----------------------------------------------------------------------------------------------------------------

    struct RegistryHitSpec
    {
        float pct = 0.f;                    // % of the reference non-tank row (0 with a rider or Weakened: no damage)
        float tankPct = -1.f;               // >= 0: the tank (role provider) takes this % of tank health instead
        uint8 school = 0;
        uint32 spellId = 0;                 // a dungeon copy of the resolve spell (0 = by school)
        bool weakened = true;
        uint32 rider = 0;
        uint32 tag = 0;
        std::function<void(Unit* hit)> onHit;   // capture guids only
    };

    // Hits exactly the players in `targets` now (a RunOut measured from the owner, NoTelegraph, warn 0, one pass per
    // target, players only: their pets are never hit) and lists each hit in the encounter's ledger: Weakened, rider,
    // onHit, the failure feed and the encounter's cleanup work as for any mechanic. Targets not on `owner`'s map, dead
    // or game masters are skipped. Returns the mechanic (invalid: no target left, or refused).
    BossMechanics::MechanicHandle RegistryHit(Unit* owner, GuidSet const& targets, RegistryHitSpec const& spec);
    // The handoff's short form.
    BossMechanics::MechanicHandle RegistryHit(Unit* owner, GuidSet const& targets, float pct, uint8 school,
        bool weakened, uint32 rider = 0);

    // ----------------------------------------------------------------------------------------------------------------
    // WeightedShares (#19)
    // ----------------------------------------------------------------------------------------------------------------

    // The players in `inside` (null entries skipped with their stacks) each get a share of `totalPct` % of `owner`'s
    // reference non-tank row: the even split (SplitShares), then x (1 + perStack x stacks[i]), at most `capPct` % each
    // (0 = no cap). `stacks` runs parallel to `inside` (missing entries count 0). Deal the shares with a SpellScript of
    // your own (SetEffectValue in OnEffectLaunchTarget).
    std::vector<std::pair<ObjectGuid, uint32>> WeightedShares(Unit const* owner, std::vector<Unit*> const& inside,
        float totalPct, std::vector<uint32> const& stacks, float perStack, float capPct = 0.f);
    // The stacks are each unit's stacks of `stackSpell` (any caster).
    std::vector<std::pair<ObjectGuid, uint32>> WeightedShares(Unit const* owner, std::vector<Unit*> const& inside,
        float totalPct, uint32 stackSpell, float perStack, float capPct = 0.f);

    // ----------------------------------------------------------------------------------------------------------------
    // FollowThenLand (#20)
    // ----------------------------------------------------------------------------------------------------------------

    // `owner`, `spot` (where it landed, the floor height of the carrier then) and the resolve's result. `owner` is the
    // owner creature (nullptr when the owner is not a creature).
    using LandFn = std::function<void(Creature* owner, Position const& spot, BossMechanics::ResolveResult const& r)>;

    // A Circle of `radius` anchored on `target` that follows them for `warn`, then resolves where they stand with
    // `impact`'s damage (pct, tankPct, school, spellId, weakened, tag; its shape and warn are not read). A shape
    // anchored on a player never hits that player (the carrier takes its own hit, if any, from the script). Then
    // `onLand` runs with the landing spot (a puddle, a linger, a jump). The ref's other options can still be chained
    // (the carrier's drop spot rule, a color; it commits at the end of the calling statement); do not replace its
    // OnResolve. pct 0 with weakened false: a telegraph-only landing.
    BossMechanics::MechanicRef FollowThenLand(Unit* owner, Unit* target, float radius, Milliseconds warn,
        ImpactSpec const& impact, LandFn onLand = {});

    // ----------------------------------------------------------------------------------------------------------------
    // PickFloorSpot (#21)
    // ----------------------------------------------------------------------------------------------------------------

    struct FloorProbe
    {
        float z = 0.f;                      // the floor's expected height (the boss's z, a measured floor)
        float zBand = 3.f;                  // a floor more than this above or below it is not this floor
        float probeUp = 3.f;                // the height search starts this far above `z`
        bool reachable = false;             // also on the navmesh, reachable from `ref` (Map::CanReachPosition...)
    };

    // A random floor point by `rules` (DungeonKitFloor.h PickFloorSpotFrom), inside `arena` when given (its region
    // holding the floor height), on `ref`'s map floor by `probe`. `fixed` are measured fallbacks. nullopt: no floor
    // point found (or none keeps every rule without bestEffort). The orientation faces `rules.near`.
    std::optional<Position> PickFloorSpot(WorldObject const* ref, Arena const* arena, FloorSpotRules const& rules,
        FloorProbe const& probe, std::vector<Vec2> const& fixed = {});

    // ----------------------------------------------------------------------------------------------------------------
    // SummonWave (#22)
    // ----------------------------------------------------------------------------------------------------------------

    struct WaveSpec
    {
        uint32 entry = 0;
        uint32 health = 0;                  // > 0: max and current health (0: the template's)
        TempSummonType type = TEMPSUMMON_CORPSE_TIMED_DESPAWN;
        Milliseconds despawn{ 5000 };
        bool passive = false;               // REACT_PASSIVE (the meat walks, it does not fight)
        bool track = true;                  // Mechanic::TrackUnit: a unit of the boss's encounter (descriptors)
        std::function<void(Creature* add)> onSummon;
    };

    // Summons spec.entry at every point of `at` by `boss` (BossAI's JustSummoned adds each to its `summons` and puts
    // it in combat while engaged), adds each to `list` when it is not there yet, sets the health and tracks it. Returns
    // the adds summoned (their guids belong in the script, never the pointers).
    std::vector<Creature*> SummonWave(Creature* boss, WaveSpec const& spec, std::vector<Position> const& at,
        SummonList& list);
    // The handoff's short form.
    std::vector<Creature*> SummonWave(Creature* boss, uint32 entry, std::vector<Position> const& at, SummonList& list,
        uint32 health = 0);

    // ----------------------------------------------------------------------------------------------------------------
    // HoldInUnit (#23)
    // ----------------------------------------------------------------------------------------------------------------

    struct HoldSpec
    {
        // The hold aura on the held unit, applied by the holder (the boss WP's own spell: a stun, its own
        // CHANGE_MAP interrupt flag so it never outlives the instance, no dispel type). Required.
        uint32 holdSpell = 0;
        // Damage immunity while held (the cocoon; not the tomb): the boss WP's own aura (school immunity, CHANGE_MAP
        // interrupt), applied with the hold and removed with it. 0: none.
        uint32 immuneSpell = 0;
        Milliseconds maxHold{ 10000 };
        // Called once per hold when it ends (capture guids only): the hatch at a timeout, a log line, a respawn.
        std::function<void(ObjectGuid holder, ObjectGuid held, HoldEnd why)> onRelease;
    };

    // Owned by one boss AI: the holds it made. Hold applies the auras (from the holder, at maxHold) and books the
    // pair; Update (every kCheckMs) releases a hold when its holder died, despawned or left the map, when the held
    // unit died or left, or at maxHold, removing both auras. Call Update from UpdateAI (in or out of combat) and Clear
    // from Reset / JustDied / EnterEvadeMode. The holder is usually a creature summoned on the held player's spot.
    class HoldInUnit
    {
    public:
        static uint32 constexpr kCheckMs = 250;

        // False when refused: a side missing or dead, the held unit already held, no holdSpell, the aura refused.
        bool Hold(Unit* holder, Unit* held, HoldSpec spec);
        void Update(WorldObject* owner, uint32 diff);
        // Lets go of `held` now (HoldEnd::Released). False when it was not held.
        bool Release(WorldObject* owner, ObjectGuid held);
        void Clear(WorldObject* owner);

        bool IsHeld(ObjectGuid held) const { return _book.HolderOf(held.GetRawValue()) != 0; }
        ObjectGuid HolderOf(ObjectGuid held) const;
        std::size_t Count() const { return _book.Size(); }

    private:
        struct Entry
        {
            ObjectGuid holder;
            ObjectGuid held;
            HoldSpec spec;
        };

        void End(WorldObject* owner, HoldBook::Ended const& ended);

        HoldBook _book;
        std::vector<Entry> _entries;
        uint32 _checkMs = 0;
    };
}

#endif
