/*
 * mod-dungeon-bosses, the shared dungeon kit: the movers Blackrock Spire wave 1 adds (WP-KT-B1,
 * .agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md section 3.11 #3-#5). The pure rules are
 * DungeonKitChaseLogic.h. Include this header (it includes DungeonKit.h).
 *
 *   Chaser        a unit that runs at one target at a set speed: taunt immune, stopped 1 s by a toss or a stun,
 *                 a new target when its target dies (or every N s: no-threat mode), an arrival callback (#3)
 *   CrawlPickups  walk-over pickups on a unit of their own (a shard): a telegraph-only Soak anchored on it for the
 *                 bots (MissedSoak Never), taken on touch, crawling to a goal unit or point after a wait (#4)
 *   FallWatch     catches players and their pets a set height under a deck, inside a region, before they land (#5)
 *
 * Lambdas kept by these helpers capture guids only, never a Unit*.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_CHASE_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_CHASE_H

#include "BossMechanics.h"
#include "DungeonKit.h"
#include "DungeonKitArena.h"
#include "DungeonKitChaseLogic.h"
#include "DungeonKitLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <vector>

class Creature;
class Map;
class Player;
class Unit;
class WorldObject;

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Chaser (#3)
    // ----------------------------------------------------------------------------------------------------------------

    enum class ChaseEnd : uint8
    {
        Arrived,    // reached its target (endOnArrive)
        Expired,    // its life ran out
        NoTarget,   // its target went and nobody else qualifies
        Stopped     // Stop, or the chaser died or left the world
    };

    struct ChaserSpec
    {
        float speed = 5.f;                  // yd/s (a player runs 7); 0: the chaser's own run speed
        bool honorSlows = true;             // slows on the chaser still cut `speed` (re-read at every re-aim)
        float reach = 2.f;                  // yd (2D): arrived
        Milliseconds pauseOnControl{ 1000 };    // a toss (knockback, jump) or a stun stops it at least this long
        Milliseconds retargetEvery{ 0 };    // no-threat mode: a new random pick every this long (0: when it goes)
        Milliseconds life{ 0 };             // 0: until it arrives or Stop
        Milliseconds repath{ 250 };         // re-aim period (MovePoint at the target's spot)
        bool endOnArrive = true;            // false: it keeps after the target; onArrive on every new contact
        bool tauntImmune = true;            // taunt and Attack Me immunity while chasing (removed at the end)
        bool fixate = true;                 // threat fixate on the target: a chaser that melees hits only it
        // The pick for a new target: the players on `picker`'s threat list (Start's `picker`, else the chaser's own),
        // PickPlayer's rule; the old target is excluded when anyone else qualifies.
        PickRule pick;
        // Capture guids only. The chase is already over when onArrive (endOnArrive) and onEnd run, so they may
        // despawn the chaser.
        std::function<void(Creature* chaser, Unit* target)> onArrive;
        std::function<void(Creature* chaser, Unit* target)> onTarget;   // a new target (not the first: Start's)
        std::function<void(Creature* chaser, ChaseEnd why)> onEnd;      // Expired, NoTarget (not Arrived, Stopped)
    };

    // Owned by the chaser's AI (or by a boss that drives an add: pass the add every call). Start turns combat movement
    // off (the AI's AttackStart no longer chases its victim), sets the speed and runs at the target; Update re-aims
    // every `repath`, holds after a toss or a stun, retargets, and ends the chase. Call Update from UpdateAI and Stop
    // from Reset / JustDied / EnterEvadeMode (Stop restores combat movement, the run speed, taunt and the fixate).
    //
    //     DungeonKit::Chaser _chase;
    //     void IsSummonedBy(WorldObject*) override { _chase.Start(me, target, { .speed = 5.f, .life = 10s,
    //         .onArrive = [](Creature* sheep, Unit*) { Explode(sheep); } }); }
    //     void UpdateAI(uint32 diff) override { _chase.Update(me, diff); }
    class Chaser
    {
    public:
        // False when refused: a side missing, dead or not in the world, or on another map.
        bool Start(Creature* chaser, Unit* target, ChaserSpec spec, Creature* picker = nullptr);
        void Update(Creature* chaser, uint32 diff);
        void Stop(Creature* chaser);

        bool Active() const { return _active; }
        bool Holding() const { return _active && _clock.Holding(); }
        ObjectGuid Target() const { return _target; }

    private:
        void Aim(Creature* chaser, Unit* target);
        void ApplySpeed(Creature* chaser) const;
        bool Retarget(Creature* chaser);
        void Finish(Creature* chaser, ChaseEnd why, Unit* target);

        ChaserSpec _spec;
        ChaseClock _clock;
        ObjectGuid _target;
        ObjectGuid _picker;
        uint32 _repathMs = 0;
        bool _active = false;
        bool _prevCombatMovement = true;
        bool _setTauntImmune = false;       // this chase added the spell-0 taunt immunity (and removes it)
        bool _setAttackMeImmune = false;    // ... and the spell-0 Attack Me immunity
    };

    // ----------------------------------------------------------------------------------------------------------------
    // CrawlPickups (#4)
    // ----------------------------------------------------------------------------------------------------------------

    // Where a pickup crawls: the unit while it is on the map, else the point; neither: it lies still.
    struct CrawlGoal
    {
        ObjectGuid unit;
        std::optional<Position> point;
    };

    struct CrawlPickupSpec
    {
        uint32 entry = 0;                   // the pickup's own unit (required): summoned on the spot, passive
        float radius = 2.f;
        float zBand = 6.f;                  // yd above or below the pickup that still count as on it
        Milliseconds dwell{ 0 };            // an eligible player inside this long takes it (0: on touch)
        bool crawl = true;
        Milliseconds wait{ 10000 };         // lying still, then it crawls (Urok: 10 s normal, 7 s heroic)
        float crawlSpeed = 3.f;             // yd/s along the floor (FloorPathOnMap)
        float reach = 1.5f;                 // yd (2D) from the goal: it arrives (onReach)
        Milliseconds repath{ 1000 };        // the crawl's re-path period (the goal moves)
        Milliseconds life{ 0 };             // a safety: gone after this long (onExpire); 0: until taken or reached
        BossMechanics::Eligibility who;     // who may take it (and which bots go for it): Registry::IsEligible
        // Bots only (B5 / SP UR10): the Soak's claim order. Its capStacks is claim-only (a bot at or above it never
        // goes for the pickup), the touch still follows `who`: e.g. who.maxStacks 2 (anyone may take a third stack)
        // with order { aura, true, 2 } (bots stop at two). Empty: no order, bots follow `who` alone.
        std::optional<BossMechanics::Ordering> order;
        uint8 count = 1;                    // bodies the bots send (the Soak's count)
        bool oneClaimPerBot = true;         // among this tag's live pickups, a bot claims one (Malicia's souls)
        // Only while a walker exists (Zul'Farrak WP-KT, F8: Zum'rah's souls go to the walkers alone): the takers are
        // the pickups' SetCarriers set, not who.carriers (which an empty set would turn into "everyone"). While that
        // set is empty the pickup is dormant: no Soak (no bot goes for it) and no touch takes it; it still waits,
        // crawls, arrives and expires. A new set re-registers its Soak (a new walk, a new walker).
        bool onlyWhileCarriers = false;
        std::optional<BossMechanics::Color> color;
        uint32 tag = 0;
        // Capture guids only. `at` is where the pickup was when it was taken / arrived.
        std::function<void(Player* taker, Position const& at)> onPick;
        std::function<void(ObjectGuid goal, Position const& at)> onReach;
        std::function<void(Position const& at)> onExpire;
    };

    // Walk-over pickups on units, owned by one AI (`owner` is the encounter of their Soaks: a boss, or an
    // instance-owned helper before the boss is out). Add summons spec.entry on the spot and registers a
    // telegraph-only Soak anchored on it (outline only, MissedSoak Never: the cost of a missed shard is the crawl's
    // arrival, not a failure); Update polls every 250 ms for the first eligible player within `radius` of the unit
    // (taken: onPick), crawls it to its goal after `wait` (arrived: onReach), and ends it at `life`. Either way the
    // unit despawns and the Soak goes; a unit despawned by anything else drops its pickup quietly. Call Update from
    // UpdateAI (in or out of combat) and Clear from Reset / JustDied / EnterEvadeMode.
    class CrawlPickups
    {
    public:
        static uint32 constexpr kPollMs = 250;
        static Milliseconds constexpr kWholeFight{ 4 * 3600 * 1000 };  // a life-0 pickup's Soak warning

        // Returns the pickup id (0: refused: no owner, no entry, radius <= 0, the summon failed).
        uint32 Add(Creature* owner, Position const& at, CrawlPickupSpec spec, CrawlGoal goal = {});
        // A new goal for every live pickup (the prelude's pile, then Urok when he arrives).
        void SetGoal(CrawlGoal goal);
        // The takers of every onlyWhileCarriers pickup, live and to come (the walkers now; empty: none, dormant). A
        // changed set re-registers their Soaks; the other pickups are untouched.
        void SetCarriers(Creature* owner, GuidSet carriers);
        GuidSet const& Carriers() const { return _carriers; }
        // A dormant pickup: onlyWhileCarriers with nobody to take it.
        bool Dormant(uint32 id) const;
        void Update(Creature* owner, uint32 diff);
        void Cancel(Creature* owner, uint32 id);
        void Clear(Creature* owner);

        std::size_t Count() const { return _pickups.size(); }
        // The pickup's unit (empty: gone).
        ObjectGuid UnitOf(uint32 id) const;
        std::vector<uint32> Ids() const;

    private:
        struct Entry
        {
            uint32 id = 0;
            ObjectGuid unit;
            CrawlPickupSpec spec;
            CrawlGoal goal;
            CrawlClock clock;
            BossMechanics::MechanicHandle soak;
            DwellTracker dwell;
            uint32 repathMs = 0;
            bool moving = false;
            Position last;
        };

        void Remove(Creature* owner, Entry& e);
        void RegisterSoak(Creature* owner, Entry& e, Creature* unit = nullptr);
        bool GoalPosition(Map* map, CrawlGoal const& goal, Position& out) const;

        std::vector<Entry> _pickups;
        GuidSet _carriers;
        uint32 _nextId = 1;
        uint32 _pollMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // FallWatch (#5)
    // ----------------------------------------------------------------------------------------------------------------

    struct FallWatchSpec
    {
        float deckZ = 0.f;                  // the deck's floor height
        float below = 15.f;                 // caught this far under it (Omokk's Pit Drop: 15 yd, about 1.5 s of fall)
        Arena region;                       // where the pit is (plane and z band); empty: anywhere on the map
        Milliseconds grace{ 3000 };         // not caught again this soon (the jump back climbs through the band)
        bool pets = true;                   // a player's pets and guardians too (no totems, no charmed mobs)
        // Capture guids only. The unit is still falling; jump it back (JumpTo). A caught player's fall start is reset
        // to the catch height first, so landing from the jump deals no fall damage.
        std::function<void(Unit* caught)> onCatch;
    };

    // Polled by one AI every 100 ms while armed: every living player on `ref`'s map (not a GM), and with `pets` their
    // pets and guardians, inside `region` and at least `below` yd under `deckZ` is caught (onCatch), at most once per
    // `grace`. Call Update from UpdateAI (it does nothing while disarmed) and Disarm from Reset / JustDied /
    // EnterEvadeMode.
    class FallWatch
    {
    public:
        static uint32 constexpr kPollMs = 100;

        void Arm(FallWatchSpec spec);
        void Disarm();
        bool Armed() const { return _armed; }
        // Returns how many units it caught this call.
        uint32 Update(WorldObject* ref, uint32 diff);

    private:
        bool Watch(Unit* unit, uint64 nowMs);

        FallWatchSpec _spec;
        FallCatchBook _book;
        bool _armed = false;
        uint32 _pollMs = 0;
        uint64 _clockMs = 0;
    };
}

#endif
