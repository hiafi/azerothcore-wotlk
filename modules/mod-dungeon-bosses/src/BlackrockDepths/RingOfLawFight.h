/*
 * mod-dungeon-bosses, Blackrock Depths D4: the Ring of Law's hook surface (engine side). WP-D4 owns this file.
 *
 * Grimstone's AI (npc_grimstone_rework.cpp) runs every attempt: the entry, the Sentence, Crowd Favor, the opener wave,
 * the two champions back to back, the Encore's place in the run, the wipe and the credit. The champions (D5,
 * boss_ring_champions_rework.cpp) and the Encore (D6, ring_encore_hard_mode.cpp) build on him through this header:
 *
 *   RingFrame       what Grimstone offers a Ring unit during an attempt (FrameOf(me) finds it through the instance:
 *                   GetGuidData(kGuidGrimstone) and a dynamic_cast of his AI). Every call is made from the caller's
 *                   own UpdateAI, hook or OnResolve, on the map thread.
 *   Judged          chains Crowd Favor's judge on a dodgeable registry mechanic (RL1): +1 when it resolves with no
 *                   player hit, -1 per player hit (x2 under Trial by the Crowd). JudgedPersistent for a lasting zone
 *                   (its landing judged once, then -1 for each player the first time a later tick hits them).
 *   EncoreScript    D6's per-attempt object, from a factory D6 registers once (RegisterEncore, from its AddSC_);
 *                   Grimstone calls its hooks.
 *
 * What Grimstone does for the champions (D5): he summons the rolled pair (kRingChampions[DATA_RING_FIRST], then
 * [DATA_RING_SECOND]) behind the east gate (kRingChampionSummon, TEMPSUMMON_DEAD_DESPAWN), tracks each on the Ring's
 * registry encounter (his own: Mechanic::TrackUnit), gives it every player on the floor at 0 threat and an attack on
 * one of them, and sends the title holder DoAction(ACTION_RING_TITLE_HOLDER) right after its summon (CH1 Title Holder
 * is D5's aura; line 9 is his). The challenger's death starts the 5 s interlude, the title holder's death the credit
 * (or the Encore's 15 s beat). A champion that is gone without dying for 5 s is summoned again. Nothing of his writes a
 * boss slot: the instance writes BOSS_RING_OF_LAW from TYPE_RING_OF_LAW.
 *
 * Rules for D5 / D6 (they keep one descriptor for the whole Ring, the BM view takes only one encounter's):
 *   - Never call Mechanic::Describe on a champion or a member: hand your kick, dispel, purge, hold and kill-order
 *     entries to SetUnitDescriptor(me->GetGUID(), fill) at the pull; Grimstone merges them into the Ring's descriptor
 *     and drops them on ClearUnitDescriptor (call it from JustDied / EnterEvadeMode).
 *   - Your registry mechanics stay owned by you (Mechanic::Circle(me, ...)); one that must outlive its caster (a pool
 *     that stays after the caster's death) is owned by RingFrame::Owner().
 *   - A unit you summon (Risen beasts, the Risen Champion, Korv's totems, the Encore's five): JoinRing(unit) right
 *     after the summon (tracked, engaged, despawned on a wipe and at the credit).
 *   - The banner flags are the instance's (SetData(DATA_BANNER_BURNED, 1) from D6's banner); Grimstone throws it.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_RING_OF_LAW_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRD_RING_OF_LAW_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "DungeonKitBodies.h"
#include "ObjectGuid.h"
#include "RingOfLawLogic.h"
#include <functional>
#include <memory>
#include <vector>

class Creature;
class Player;
class WorldObject;

namespace BrdRingOfLaw
{
    // CreatureAI::DoAction ids Grimstone sends to a champion (D5).
    inline constexpr int32 ACTION_RING_TITLE_HOLDER = 0x524C0001;     // the second champion: CH1 Title Holder

    // Grimstone's AI as the champions (D5) and the Encore (D6) see it.
    class RingFrame
    {
    public:
        virtual ~RingFrame() = default;

        // ---- the attempt ------------------------------------------------------------------------------------------
        virtual Step CurrentStep() const = 0;
        virtual bool Heroic() const = 0;
        virtual Sentence ActiveSentence() const = 0;
        // The rolled wave type, 0-5 (kWaveTypes / kRingWaveMobs index; the saved roll DATA_RING_WAVE).
        virtual uint32 WaveType() const = 0;
        // 1: the challenger, 2: the title holder (Title Holder, the Molten legs token), 0: not this attempt's champion.
        virtual uint8 ChampionOrder(ObjectGuid champion) const = 0;
        // Grimstone himself: the Ring's registry encounter (its descriptor) and the owner of a mechanic that must
        // outlive its caster.
        virtual Creature* Owner() = 0;
        // The players on the floor, alive (not game masters).
        virtual std::vector<Player*> FloorPlayers() const = 0;

        // ---- Crowd Favor (RL1) --------------------------------------------------------------------------------------
        virtual uint32 Favor() const = 0;
        // A dodgeable registry mechanic resolved: +1 with no player hit, else -1 per player hit (x2 under the Crowd).
        // Judged() chains it on a registration; call it yourself from an OnResolve you already own.
        virtual void JudgeResolve(BossMechanics::ResolveResult const& result, char const* source) = 0;
        // A dodgeable hit that is not a registry resolve (a script's own projectile, a lasting zone's later tick): -1
        // for `player` (x2 under the Crowd).
        virtual void FavorHit(ObjectGuid player, char const* source) = 0;

        // ---- units --------------------------------------------------------------------------------------------------
        // A Ring unit Grimstone did not summon (Risen beasts, the Risen Champion, Korv's totems, the Encore's five):
        // tracked on the Ring's encounter (kicks, dispels), every player on the floor added at 0 threat, despawned on a
        // wipe and at the credit.
        virtual void JoinRing(Creature* unit) = 0;
        // Where the wave's beasts died this attempt (DeathSpots tag = wave type + 1, entry = the beast's): AN1 Raise
        // Dead takes its spots from here (TakeRandom with an unused-only filter marks them used).
        virtual DungeonKit::DeathSpots& BeastDeaths() = 0;

        // ---- the descriptor -----------------------------------------------------------------------------------------
        // `fill` adds the unit's entries (kicks, dispels, purges, holds, kill order) to the Ring's one descriptor; it
        // is called on every rebuild until ClearUnitDescriptor. Capture nothing that dies with the unit.
        virtual void SetUnitDescriptor(ObjectGuid unit, std::function<void(BossMechanics::Descriptor&)> fill) = 0;
        virtual void ClearUnitDescriptor(ObjectGuid unit) = 0;

        // ---- Grimstone ----------------------------------------------------------------------------------------------
        // He says `group` (RingOfLawLogic.h GrimstoneTexts: D6 uses SAY_GRIM_BANNER_BURNED).
        virtual void GrimstoneSay(uint8 group, WorldObject const* target = nullptr) = 0;

        // ---- the Encore (D6) ----------------------------------------------------------------------------------------
        // The Encore's team is down (call it once, after its last member's real death): the Arena Spoils chest and the
        // Theldren kill credit 16166 (stock, unchanged), then the Ring's credit.
        virtual void EncoreWon() = 0;
    };

    // The frame of `any`'s instance while an attempt runs (Grimstone alive and running the reworked AI); nullptr
    // otherwise (no attempt, the stock Grimstone, another map).
    RingFrame* FrameOf(WorldObject const* any);

    // Chains RingFrame::JudgeResolve on a dodgeable registration (it sets the ref's OnResolve: set no other one after
    // it). Out of an attempt the judge does nothing. Returns `ref` for more chaining.
    BossMechanics::MechanicRef& Judged(BossMechanics::MechanicRef& ref, WorldObject const* any, char const* source);
    // For a Persistent registration: its first pass judged like Judged (+1 clean, -1 per player hit), every later pass
    // -1 for each player hit the first time (once per player per zone).
    BossMechanics::MechanicRef& JudgedPersistent(BossMechanics::MechanicRef& ref, WorldObject const* any,
        char const* source);

    // D6's per-attempt object. Grimstone makes one at the start of every attempt when a factory is registered, calls
    // its hooks from his own updates and drops it with the attempt.
    class EncoreScript
    {
    public:
        virtual ~EncoreScript() = default;

        // Favor reached 10 on heroic for the first time this run (EN1; DATA_BANNER_THROWN is already set and saved,
        // emote 10 said): place the banner.
        virtual void OnBannerThrown(Creature* grimstone) = 0;
        // An attempt starts with the banner thrown (burned or not): put it back if it is gone (a reload, a despawn).
        virtual void OnAttemptStart(Creature* grimstone) = 0;
        // The title holder died with the banner burned on heroic; after the 15 s beat Grimstone says line 12 and calls
        // this: the leap (Theldren's stock line 0, the five land; JoinRing each; the hard mode loot bit on Theldren).
        // Grimstone's JustSummoned engages every summon of his inside SummonCreature, before the leap starts: a
        // leaping unit must ignore that engage (no fight, no chase) until it lands.
        // False: the Encore cannot run now (Grimstone credits the Ring without it).
        virtual bool Start(Creature* grimstone, RingFrame& frame) = 0;
        // Every Grimstone update while the Encore runs (Step::Encore).
        virtual void Update(Creature* grimstone, RingFrame& frame, uint32 diff) = 0;
        // The attempt ends: a wipe (`won` false: every member, totem and trap gone, every aura of the Encore off) or
        // the credit (`won` true: called from inside your own RingFrame::EncoreWon() call, so finish your bookkeeping
        // before calling it). Grimstone drops the object with the attempt (his despawn).
        virtual void Stop(Creature* grimstone, bool won) = 0;
    };

    using EncoreFactory = std::function<std::unique_ptr<EncoreScript>()>;
    // D6 calls this once from AddSC_brd_ring_encore_hard_mode (the last registration wins).
    void RegisterEncore(EncoreFactory factory);
}

#endif
