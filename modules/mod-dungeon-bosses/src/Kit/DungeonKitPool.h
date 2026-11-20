/*
 * mod-dungeon-bosses, the shared dungeon kit: a health pool shared by several units (Blackrock Depths WP-KT-D2,
 * handoff section 3.11 #4; the Seven). The pure rules are DungeonKitPoolLogic.h (HealthPool).
 *
 *   SharedHealthPool   one pool of health for a set of creatures (the Twin Val'kyr pattern, made exact): every hit on
 *                      a member comes off the pool, a cleave counts once per cast (the largest of its hits), heals on a
 *                      member go into the pool, and every member shows the pool's percent of its own max health. The
 *                      hit that empties the pool is clamped to leave 1 health (as InterceptLethal does) and every
 *                      member is held at 1 health; the next Update kills them all in that one tick, each with the
 *                      player who emptied the pool as the killer (credit and loot as for any kill)
 *
 * One pool, many AIs: own it where every member's AI reaches it (the instance script, or one leader AI that the others
 * fetch through the instance). Members are kept as guids; every call takes a member (any member) to find the others.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_POOL_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_POOL_H

#include "DungeonKitPoolLogic.h"
#include "ObjectGuid.h"
#include <functional>
#include <vector>

class Creature;
class Unit;
enum DamageEffectType : uint8;

namespace DungeonKit
{
    struct SharedHealthPoolSpec
    {
        // The pool. 0 (the Seven's choice: TheSevenFight.h sizes it through the templates, 320k / 450k): the first
        // member's max health at Engage.
        uint32 maxHealth = 0;
        uint32 castWindowMs = kPoolCastWindowMs;    // once-per-cast window for direct hits and heals (DoTs: one tick)
        bool keepThreat = true;             // a merged cleave hit still gives its attacker the hit's full threat
        char const* dungeon = "kit";        // LogMechanic: "<dungeon> <boss> pool-engage|pool-empty|pool-death"
        char const* boss = "pool";
        // Capture guids only. onEmpty: the hit that emptied the pool, before the death tick (`killer` may be null).
        std::function<void(Creature* hit, Unit* killer)> onEmpty;
    };

    // The AIs (all seven ghosts run the same one):
    //
    //     SharedHealthPool* Pool();           // from the owner (the instance, or the leader's AI)
    //     void JustEngagedWith(Unit*) override
    //     {
    //         if (!Pool()->Engaged())         // once per pull: Engage refills the pool
    //             Pool()->Engage(me);
    //     }
    //     void DamageTaken(Unit* who, uint32& damage, DamageEffectType type, SpellSchoolMask) override
    //     {
    //         Pool()->DamageTaken(me, who, damage, type);
    //     }
    //     void HealReceived(Unit* who, uint32& heal) override { Pool()->HealReceived(me, who, heal); }
    //     void UpdateAI(uint32 diff) override
    //     {
    //         Pool()->Update(me);             // keeps this member on the pool; the death tick kills all members
    //         ...
    //     }
    //     // the wipe / evade (any member): Pool()->Reset();   Vile Communion: Pool()->RestorePct(me, 5.f);
    //
    // Add the members (all seven, alive) before Engage. Engage fills the pool, sets every member to full and lowers
    // each member's player damage requirement to 0 (a member brought down by the mirror alone would otherwise give
    // no loot, reputation or credit). Until Engage (and after Reset) every hook leaves the hit untouched.
    class SharedHealthPool
    {
    public:
        SharedHealthPool() : SharedHealthPool(SharedHealthPoolSpec{}) { }
        explicit SharedHealthPool(SharedHealthPoolSpec spec);

        void Add(Creature* member);
        void Add(ObjectGuid member);
        bool Contains(ObjectGuid member) const;
        std::vector<ObjectGuid> const& Members() const { return _members; }
        // Drops the members and resets the pool (a new set for the next pull).
        void ClearMembers();

        // The pull: the pool full (spec.maxHealth, or `any`'s max health), every member full and on the pool.
        void Engage(Creature* any);
        bool Engaged() const { return _engaged; }

        // From a member's DamageTaken: the pool loses the hit (once per cast); `damage` becomes what takes `me` to the
        // pool's mirror (0 for a merged cleave hit), the other members are set to it. The emptying hit leaves `me` at
        // 1 health. True when it changed `damage`. Not a member, or not engaged: false, untouched.
        bool DamageTaken(Creature* me, Unit* attacker, uint32& damage, DamageEffectType type);

        // From a member's HealReceived: the pool gains the heal (once per cast), `heal` becomes what takes `me` to
        // the mirror. While emptied every heal is 0.
        bool HealReceived(Creature* me, Unit* healer, uint32& heal);

        // A scripted heal of the pool (Vile Communion): never grouped. Returns the gain; every member is mirrored.
        uint32 Restore(Creature* any, uint32 amount);
        uint32 RestorePct(Creature* any, float pct);

        // From every member's UpdateAI: `me` back on the pool when its health drifted (a heal no hook saw), and, once
        // the pool is empty, the death tick: every living member killed (Unit::Kill) in Members() order.
        void Update(Creature* me);

        // The wipe (any member's EnterEvadeMode / the owner's Reset): not engaged, the pool full, members kept.
        void Reset();

        bool Emptied() const { return _pool.Emptied(); }
        bool Dead() const { return _pool.DeathTaken(); }
        uint32 Current() const { return _pool.Current(); }
        uint32 Max() const { return _pool.Max(); }
        float Pct() const { return _pool.Pct(); }
        HealthPool const& Logic() const { return _pool; }

    private:
        void MirrorAll(Creature* any, ObjectGuid skip = ObjectGuid::Empty);
        // Each member dies to the pool's killer; when that one has left the map, to a member's loot recipient or any
        // living player on the map (ChoosePoolKiller), so the encounter credit and the bind land; only with no player
        // left, to itself (Unit::Kill(member, member): its own KilledUnit(member) runs first, so the AIs guard kill
        // taunts with `victim->IsPlayer()`; R-1-FW NIT-4).
        void KillAll(Creature* any);
        Unit* ResolveKiller(Creature* any, char const*& source) const;

        SharedHealthPoolSpec _spec;
        HealthPool _pool;
        std::vector<ObjectGuid> _members;
        ObjectGuid _killer;                 // who emptied the pool
        bool _engaged = false;
    };
}

#endif
