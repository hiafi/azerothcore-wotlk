/*
 * mod-dungeon-bosses, the shared dungeon kit: death spots and held bodies (Blackrock Depths WP-KT-D1, handoff section
 * 3.11 #1). The pure rules are DungeonKitBodyLogic.h.
 *
 *   DeathSpots   where the units of a fight died (entry, position, time, a tag): Record from the dying unit's
 *                JustDied (or the summoner's SummonedCreatureDies), Take (oldest or random, marked used) for Raise
 *                Dead, Find / Nearest for a burst at a corpse whose body is already gone (TEMPSUMMON_DEAD_DESPAWN)
 *   HeldBody     the "held body" form of LethalGuard: the first lethal hit (or the first `holds`) leaves the unit at
 *                1 health as a body (feign-death look, rooted, passive, not attackable, casts stopped, still in
 *                combat) until Revive (Korv's Ancestral Spirit), Finish (the real death: the fight is over, or the
 *                swell of Acid Burst ran out) or its hold limit; a lethal hit with no hold left is a real death
 *
 * One owner each: DeathSpots on the AI that runs the fight (Grimstone, the champion), HeldBody on the unit itself.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_BODIES_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_BODIES_H

#include "DungeonKit.h"
#include "DungeonKitBodyLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <optional>
#include <vector>

class Creature;
class Unit;

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // DeathSpots
    // ----------------------------------------------------------------------------------------------------------------

    // A stored death as engine types.
    struct DeathSpotAt
    {
        ObjectGuid guid;
        uint32 entry = 0;
        Position at;                // x, y, z, orientation at the death
        uint32 tag = 0;
    };

    class DeathSpots
    {
    public:
        explicit DeathSpots(std::size_t cap = kDeathSpotCap) : _book(cap) { }

        // Stores `dead`'s spot now (call from its JustDied, the summoner's SummonedCreatureDies, or a held body's
        // onFall). The entry is its creature entry (0 for a player). The same unit again replaces its old spot.
        void Record(Unit const* dead, uint32 tag = 0);
        void Record(ObjectGuid guid, uint32 entry, Position const& at, uint32 tag = 0);

        // Up to `n` unused matching spots, oldest death first / random (urand), each marked used.
        std::vector<DeathSpotAt> TakeOldest(std::size_t n, DeathSpotFilter const& filter = {});
        std::vector<DeathSpotAt> TakeRandom(std::size_t n, DeathSpotFilter const& filter = {});

        std::optional<DeathSpotAt> Find(ObjectGuid guid) const;
        std::optional<DeathSpotAt> Nearest(Position const& p, float maxYd = 0.f,
            DeathSpotFilter const& filter = {}) const;
        bool Mark(ObjectGuid guid, bool used = true) { return _book.Mark(guid.GetRawValue(), used); }
        bool Forget(ObjectGuid guid) { return _book.Forget(guid.GetRawValue()); }
        std::size_t Count(DeathSpotFilter const& filter = { 0, 0, false }) const { return _book.Count(filter); }

        // From Reset / JustDied / EnterEvadeMode (a wipe forgets the fight's dead).
        void Clear() { _book.Clear(); }

        DeathSpotBook const& Book() const { return _book; }

    private:
        DeathSpotBook _book;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // HeldBody
    // ----------------------------------------------------------------------------------------------------------------

    struct HeldBodySpec
    {
        uint8 holds = 1;                    // lethal hits held as a fall (Ancestral Spirit once per member: 1)
        Milliseconds holdLimit{ 0 };        // a fall finishes by itself after this long (Acid Burst's swell: 2 s)
        bool look = true;                   // feign-death look (stand state dead, UNIT_DYNFLAG_DEAD, FEIGN_DEATH)
        bool root = true;
        uint32 fallAura = 0;                // an aura held on the body while it lies (a swell, a glow); 0: none
        float revivePct = 50.f;             // Revive's default health
        char const* dungeon = "kit";        // LogMechanic: "<dungeon> <boss> body-fall|body-revive|body-finish"
        char const* boss = "body";
        // Capture guids only.
        std::function<void(Creature* body)> onFall;
        std::function<void(Creature* body)> onRevive;
        std::function<void(Creature* body)> onFinish;   // just before the real death (the hold ran out, or Finish)
    };

    // Owned by the unit's own AI:
    //
    //     DungeonKit::HeldBody _body{ spec };
    //     void Reset() override { _body.Reset(me); ... }
    //     void EnterEvadeMode(EvadeReason why) override { _body.Reset(me); ScriptedAI::EnterEvadeMode(why); }
    //     void DamageTaken(Unit*, uint32& damage, DamageEffectType, SpellSchoolMask) override
    //     {
    //         _body.Intercept(me, damage);
    //     }
    //     void UpdateAI(uint32 diff) override
    //     {
    //         _body.Update(me, diff);
    //         if (_body.Fallen() || !UpdateVictim())      // a body never fights (and never calls UpdateVictim)
    //             return;
    //         ...
    //     }
    //     // Korv's Ancestral Spirit lands: _body.Revive(me);   the Encore ends: _body.Finish(me, killer);
    //
    // While Fallen the unit stays in combat (no evade: its AI must not call UpdateVictim), is not attackable
    // (UNIT_FLAG_NON_ATTACKABLE, so players and bots drop it; friendly spells still reach it), takes no damage, does
    // not move, cast or attack. Revive restores all of it (and the react state it had). Finish clears the look and
    // kills it (Unit::Kill: credit and loot go to its loot recipient, as for any kill).
    class HeldBody
    {
    public:
        HeldBody() : HeldBody(HeldBodySpec{}) { }
        explicit HeldBody(HeldBodySpec spec);

        // From DamageTaken: clamps a lethal hit while a hold is left (the fall), absorbs every hit while Fallen.
        // True when it changed `damage`.
        bool Intercept(Creature* me, uint32& damage);

        // Fallen -> Up at `healthPct` (< 0: the spec's revivePct). False when not Fallen.
        bool Revive(Creature* me, float healthPct = -1.f);

        // The real death now (Fallen or Up). `killer` gets the kill (nullptr: the unit itself; loot still goes to its
        // loot recipient). False when already finished or `me` is not alive. With no killer the engine's self-kill
        // (Unit::Kill(me, me)) calls the unit's own KilledUnit(me) before JustDied: guard a kill taunt with
        // `victim->IsPlayer()` (R-1-FW NIT-4).
        bool Finish(Creature* me, Unit* killer = nullptr);

        // From UpdateAI, every update: the hold limit.
        void Update(Creature* me, uint32 diff);

        // From Reset / EnterEvadeMode: the look off, Up again, no falls.
        void Reset(Creature* me);

        bool Fallen() const { return _latch.Fallen(); }
        BodyState State() const { return _latch.State(); }
        uint8 Falls() const { return _latch.Falls(); }
        uint8 Revives() const { return _latch.Revives(); }
        // Where it fell (valid while Fallen and after).
        Position const& Spot() const { return _spot; }

    private:
        void LieDown(Creature* me);
        void StandUp(Creature* me);

        HeldBodySpec _spec;
        HeldBodyLatch _latch;
        Position _spot;
        uint8 _reactBefore = 2;             // REACT_AGGRESSIVE
        bool _lying = false;
    };
}

#endif
