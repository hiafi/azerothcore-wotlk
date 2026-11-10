/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): the arena guard, Captain Greenskin's "the fight stays on the
 * ship" (Deadmines playtest 1, item 2) made generic. The pure half (Arena, GripTracker, LandingToward) is
 * DungeonKitArena.h.
 *
 * ArenaGuard, owned by a boss AI:
 *
 *     DungeonKit::ArenaGuard _arena{ kMyArena, MyArenaOptions() };
 *     void JustEngagedWith(Unit* who) override { BossAI::JustEngagedWith(who); _arena.Engage(me); ... }
 *     void UpdateAI(uint32 diff) override
 *     {
 *         if (!UpdateVictim())
 *             return;
 *         if (!_arena.Update(me, diff))
 *             return;                 // he left his arena: evading
 *         ...
 *     }
 *     void Reset() / EnterEvadeMode() / JustDied(): _arena.Reset();
 *
 *   - the pull (Engage, with gripOnPull): everyone in combat with the boss (his threat list: players, pets, guardians,
 *     bots) who is off the arena is gripped onto it at once;
 *   - during the fight (gripBack): a unit off the arena for graceMs (continuously) is gripped back, then left alone for
 *     cooldownMs, or its flight time + 0.5 s when that is longer (no second grip mid-air: GripCooldownMs);
 *   - holdWhileVictimOff: the boss never chases a victim who is off the arena (he holds; the grip brings it back);
 *   - switchWhenVictimOff: while the top of his threat list is off the arena, the boss turns to the highest-threat
 *     unit on it (a threat fixate the guard sets and clears; a fixate the script set itself is left alone); with
 *     nobody on it he holds as above;
 *   - evadeWhenBossOff: the boss evades (EVADE_REASON_BOUNDARY) once he has been off it himself for bossGraceMs (0:
 *     at the first check; the leash). With leashSkipAirborne a check while he jumps or falls (his own leap, a drop
 *     between floors) neither counts nor evades;
 *   - evadeNoTargetInsideMs: ... or when nobody in combat with him has been on it that long (a grip-less arena).
 *   A grip: the boss casts `gripSpell` (the look; triggered) on the unit, then the unit jumps (JumpTo) to `landing`
 *   (default: landYd from the boss toward where it was, clamped into landBox; the floor height under it, searched
 *   from the top of the boss's region; a point the arena does not hold falls back to the boss's own spot, so a
 *   polygon or multi-region arena should give landBox or `landing`). Units farther than maxGripYd, totems and
 *   vehicles are never gripped, nor units the skipGrip option names (SkipEngagedWithOtherBoss: a unit in combat with
 *   another guarded boss). Units that left the map are forgotten at the next check.
 *
 * Confinement, for cells and jails ("server-side movement ignores closed doors", SFK handoff kit #1b): ConfineIn
 * keeps a unit inside a cell (off it for the grace: put back), KeepOut keeps everyone else out of one (inside for the
 * grace: put out). Update sweeps the map's players and their pets; a fence forgets units it no longer sees.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_ARENA_GUARD_H
#define MOD_DUNGEON_BOSSES_KIT_ARENA_GUARD_H

#include "DungeonKitArena.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Unit;
class WorldObject;

namespace DungeonKit
{
    struct ArenaGuardOptions
    {
        uint32 graceMs = GripTracker::kDefaultGraceMs;          // off the arena this long: gripped back
        uint32 cooldownMs = GripTracker::kDefaultCooldownMs;    // after a grip, left alone this long
        uint32 checkMs = 250;                                   // how often Update sweeps
        float maxGripYd = 120.f;                                // never grip a unit farther than this from the boss
        bool gripOnPull = true;
        bool gripBack = true;
        bool holdWhileVictimOff = true;
        bool switchWhenVictimOff = false;                       // turn to the top-threat unit on the arena instead
        bool evadeWhenBossOff = true;
        uint32 bossGraceMs = 0;                                 // the boss off his arena this long: the leash
        bool leashSkipAirborne = true;                          // no leash check while the boss jumps or falls
        // > 0: the boss also evades when nobody in combat with him has been on the arena this long (Scholomance's
        // "hold at the edge, evade after 10 s with no target inside", for an arena with no grips).
        uint32 evadeNoTargetInsideMs = 0;
        uint32 gripSpell = 0;                                   // the look the boss casts on a gripped unit (0: none)
        float jumpSpeedXY = 25.f;
        float minJumpSpeedZ = 8.f;                              // a short grip still arcs
        float landYd = 8.f;                                     // default landing: this far from the boss toward it
        std::optional<Box2> landBox;                            // ... clamped into this box
        // Overrides the default landing: its x, y (the floor height is searched there, as for the default), or its
        // x, y, z as given with landingKeepsZ.
        std::function<Position(Creature const* boss, Unit const* unit)> landing;
        bool landingKeepsZ = false;
        std::string logPrefix = "dungeon-kit arena";            // "<prefix> grip pull units=.. gripped=..", ...
        std::string offArenaReason = "off-arena";               // "<prefix> grip <reason> unit=..": a grip back
        // Units this guard never grips (the pull, a grip back, Grip through Grippable); empty: none.
        // SkipEngagedWithOtherBoss builds the usual one.
        std::function<bool(Creature const* boss, Unit const* unit)> skipGrip;
    };

    // A skipGrip for an instance whose guarded bosses can overlap (SFK R2 S-2: Odo and the Deathsworn Captain): a
    // unit in combat with another live creature whose entry `isBossEntry` names is left to that boss, so two guards
    // never grip it back and forth.
    std::function<bool(Creature const*, Unit const*)> SkipEngagedWithOtherBoss(std::function<bool(uint32)> isBossEntry);

    // The generic leash (Scholomance's LeashOptions lifted into the kit, Stratholme WP-KT-1; the user's arena ruling
    // "stop at the edge, evade if dragged out", Stratholme handoff section 10): no grips at all; the boss never chases
    // a victim off his arena (switchToInside: he turns to the highest-threat unit on it; nobody there: he holds at the
    // edge); he evades when he has been off it himself for bossGraceMs (a charge or a knockback that ends outside does
    // not reset him at once), and when nobody in combat with him has been on it for noTargetInsideMs. A boss whose
    // lethal wall arms after a pull grip (KT-2) turns gripOnPull back on in the options this returns.
    struct LeashSpec
    {
        uint32 bossGraceMs = 2000;
        uint32 noTargetInsideMs = 10000;
        bool switchToInside = true;
    };

    // `logPrefix` names the guard's log lines ("strat baron arena").
    ArenaGuardOptions LeashPreset(std::string const& logPrefix, LeashSpec const& spec = {});

    class ArenaGuard
    {
    public:
        ArenaGuard() = default;
        ArenaGuard(Arena arena, ArenaGuardOptions options);

        void Configure(Arena arena, ArenaGuardOptions options);

        // The pull (with gripOnPull): grip everyone in combat with `boss` who is off the arena now.
        void Engage(Creature* boss);

        // Every checkMs (call it every tick after UpdateVictim): grip back, hold the chase, leash. False when the boss
        // was off his arena and is now evading (stop the tick).
        bool Update(Creature* boss, uint32 diff);

        // Grip `unit` onto the arena now (no grace; `why` goes in the log: "pull", "off-arena", "test").
        void Grip(Creature* boss, Unit* unit, char const* why);

        // Forget every unit (Reset, JustDied, EnterEvadeMode).
        void Reset();

        bool Contains(WorldObject const* o) const;
        bool Grippable(Creature const* boss, Unit const* unit) const;
        bool Holding() const { return _holding; }
        ObjectGuid SwitchedTo() const { return _switchedTo; }
        Arena const& GetArena() const { return _arena; }
        ArenaGuardOptions const& Options() const { return _options; }

    private:
        // switchWhenVictimOff: fixate the top-threat unit on the arena while the top one is off it.
        void UpdateSwitch(Creature* boss);

        Arena _arena;
        ArenaGuardOptions _options;
        GripTracker _grip;
        LeashTimer _leash;
        uint32 _checkMs = 0;
        uint32 _emptyMs = 0;
        bool _holding = false;
        ObjectGuid _switchedTo;                                 // the unit the guard fixated (switchWhenVictimOff)
    };

    struct ConfineOptions
    {
        uint32 graceMs = 500;
        uint32 cooldownMs = 2000;
        uint32 checkMs = 250;
        bool jump = true;                   // put back with a jump (JumpTo); false: NearTeleportTo
        float jumpSpeedXY = 20.f;
        float minJumpSpeedZ = 5.f;
        std::string logPrefix = "dungeon-kit confine";
    };

    class Confinement
    {
    public:
        explicit Confinement(ConfineOptions options = {});

        // Keep `unit` inside `cell`: off it for the grace, it is put back at `putBack`. A second call for the same
        // unit replaces its cell.
        void ConfineIn(Unit const* unit, Arena cell, Position const& putBack);
        // Keep every unit that is not confined out of `cell`: inside it for the grace, it is put out at `putOut`.
        // Returns the rule id for ReleaseKeepOut.
        uint32 KeepOut(Arena cell, Position const& putOut);

        void Release(ObjectGuid unit);
        void ReleaseKeepOut(uint32 id);
        void Clear();
        bool IsConfined(ObjectGuid unit) const;

        // Sweeps `owner`'s map (its players and their pets) every checkMs.
        void Update(WorldObject* owner, uint32 diff);

    private:
        struct Jail
        {
            ObjectGuid unit;
            Arena cell;
            Position putBack;
        };

        struct Fence
        {
            uint32 id = 0;
            Arena cell;
            Position putOut;
            GripTracker tracker;
        };

        // Returns the cooldown for the tracker (a jump: at least its flight time + 0.5 s).
        uint32 PutAt(Unit* unit, Position const& at, char const* why);

        ConfineOptions _options;
        std::vector<Jail> _jails;
        GripTracker _jailTracker;
        std::vector<Fence> _fences;
        uint32 _nextFence = 1;
        uint32 _checkMs = 0;
    };
}

#endif
