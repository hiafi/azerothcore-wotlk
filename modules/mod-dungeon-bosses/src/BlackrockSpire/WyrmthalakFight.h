/*
 * mod-dungeon-bosses, Blackrock Spire B8: Overlord Wyrmthalak's hard mode hooks (engine side). WP-B8 owns this file
 * (the Stratholme BaronFight.h pattern).
 *
 * The hard mode "the war horn" (WP-B9, heroic only; SP WT9-WT17) fights on B8's AI, boss_overlord_wyrmthalak_rework.
 * B8 keeps the whole normal and heroic kit (Black Dragonfire and its burns, Tail Swipe, Cleave, the Orders with their
 * champions and the three answers, Mortal Strike at 10); B9 adds the muster, the champions' new bite (the shards, the
 * chained axes, the riders that stay), Tribal Ward and the three unlocks through two interfaces:
 *
 *   WyrmthalakHardMode  B9's per-pull object. B9 registers a factory once, from AddSC_brs_wyrmthalak_hard_mode:
 *                           BrsWyrmthalak::RegisterWyrmthalakHardMode([](Creature*) { return std::make_unique<X>(); });
 *                       On every pull that is heroic with DATA_WAR_HORN lit, B8 asks the factory for one and calls its
 *                       hooks; on any other pull none is made.
 *   WyrmthalakFight     what B8's AI offers the hard mode during the pull (passed to every hook): the players, the
 *                       champions, the orders and their answers, the burns, the cast queue, the ledge bounds, the
 *                       handle list.
 *
 * What B8 already does on a hard mode pull: reads DATA_WAR_HORN at the pull (heroic only); OnBossPull(me, key, true)
 * holds the flex count and sets the flex hard mode loot bit (LootMode 8 at 10 players); the instance records
 * BOSS_WAR_HORN on the kill, keeps the hard mode loot bit (LootMode 2) while the horn is lit and clears the horn when
 * the attempt ends (WT17: blow it again). Heroic's Overlord's Fury (WT8) is not applied on a hard mode pull (SP: the
 * unlocks replace it). Everything B8 summons (champions, riders, throwers, burn stalkers) despawns with the fight.
 *
 * Hook order: OnEngage after B8's own engage (encounter begun, descriptor set, timeline started; B8 says its pull yell
 * on every pull: the horn emote, line 7, is B9's when the horn is blown). OnUpdate every AI tick in combat, before
 * B8's beats. OnOrder before an order's tribes are called. OnChampionSummoned right after a champion appears at the
 * ramp foot (B9: the 100k health, Flex::SetHealth); OnChampionDied after B8's own bookkeeping. OnBoulderLanded per
 * boulder after its hit. OnAxesLanded with the marked players' spots after the axes' hit. OnRiderCharged when a rider
 * reaches its lane's end (return true to keep it: B8 then never moves or despawns it again; B9 owns it). OnAbilityHit
 * for every player his own abilities hit (Cleave, Black Dragonfire, Tail Swipe; never a burn tick): WT14's Caustic
 * Poison. OnCast when the cast queue picks one of B9's ids. OnDamageTaken before BossAI's (WT13 Tribal Ward). OnEnd
 * from B8's cleanup (death, evade, reset; `died` on the death), before B8 despawns its summons: undo every change made
 * to him here (health, auras).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_WYRMTHALAK_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRS_WYRMTHALAK_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include "WyrmthalakLogic.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace BrsWyrmthalak
{
    class WyrmthalakHardMode;

    // His own abilities, as OnAbilityHit names them (WT14: "every ability he uses applies Caustic Poison").
    enum class Ability : uint8
    {
        Cleave = 0,             // WT3 (stock 20691, SpellHitTarget)
        BlackDragonfire = 1,    // WT1 (the breath's hit; never the burn's ticks)
        TailSwipe = 2,          // WT2
    };

    // One breath burn (WT1b): a persistent cone Zone and its look.
    struct BurnSpec
    {
        float length = kBurnLength;                         // heroic 20 yd; B9 (Smolderthorn dead): the whole 25 yd
        float angleDeg = kBreathAngleDeg;
        uint32 lifeMs = kBurnLifeMs;                        // from its appearance; B9: 120 s
        uint32 graceMs = kBurnGraceMs;                      // first tick after this
        uint32 maxAlive = 0;                                // > 0: the oldest goes out when a new one passes it (the
                                                            // cap 3 fallback, SP 2378)
    };

    // A live burn, as the hard mode sees it.
    struct BurnInfo
    {
        Position apex;                                      // his spot and facing at the breath
        float length = 0.f;
        float angleDeg = 0.f;
        uint64 bornMs = 0;                                  // WyrmthalakFight::FightMs() at its appearance
        uint64 untilMs = 0;
        BossMechanics::MechanicHandle handle;
    };

    // B8's AI, as the hard mode sees it during one pull.
    class WyrmthalakFight
    {
    public:
        virtual ~WyrmthalakFight() = default;

        virtual Creature* Boss() = 0;
        virtual bool Heroic() const = 0;
        // The flex count held at the pull (5..10): FlexAB pairs, DungeonKit::Flex::TankSwapOn.
        virtual uint8 Players() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): B9's `.dbtest brs warhorn`
        // reaches it through his AI (dynamic_cast<BrsWyrmthalak::WyrmthalakFight*>(boss->AI())).
        virtual WyrmthalakHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock (never paused by a cast bar).
        virtual uint64 FightMs() const = 0;
        // The players of the fight: alive, not game masters, in combat with him or on his ledge.
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- WT4 the champions and the orders ----
        // The tribe's champion while it lives (nullptr: not called yet, or dead).
        virtual Creature* Champion(Tribe tribe) = 0;
        virtual bool ChampionCalled(Tribe tribe) const = 0;
        virtual bool ChampionDead(Tribe tribe) const = 0;
        // Brings the tribe's champion up the ramp now (once per pull; a called tribe returns its living champion or
        // nullptr). OnChampionSummoned follows.
        virtual Creature* SummonChampion(Tribe tribe) = 0;
        // An order to these tribes now, outside the timer (the yell, a champion on its first call, the answer of each
        // tribe whose champion lives).
        virtual void IssueOrder(std::vector<Tribe> const& tribes, char const* why) = 0;

        // ---- the answers (each one also fires from an order; these fire one now) ----
        // WT5: `count` boulders at random players' spots (a thrower in the lower hall). Returns the landing spots.
        virtual std::vector<Position> Boulders(uint8 count) = 0;
        // WT6: marks `count` random non-tanks (4 s), then the axes land; the thrower is the hard mode's AxeThrower or
        // a thrower on the ramp. Returns the marked players.
        virtual GuidSet AxeVolley(uint8 count) = 0;
        // WT7: `count` riders charge lanes through random players' spots. Returns the riders.
        virtual std::vector<ObjectGuid> WorgRiders(uint8 count) = 0;

        // ---- WT1b burns ----
        // A burn now on the cone of `apex` (its orientation is the cone's facing). Returns its handle (invalid:
        // refused).
        virtual BossMechanics::MechanicHandle SpawnBurn(Position const& apex, BurnSpec const& spec) = 0;
        virtual std::vector<BurnInfo> Burns() const = 0;
        // The black flame ground look (SPELL_WT_BLACK_FLAME_PATCH on an invisible stalker) at `at` for `lifeMs`; a spot
        // with no floor near its height is refused (empty guid). B9's Shadowflame Spit patches use it.
        virtual ObjectGuid SpawnFlamePatch(Position const& at, uint32 lifeMs) = 0;

        // ---- room, queue, bookkeeping ----
        // The bots' spot bounds (the ledge hull, kLedgeHull): every mechanic of the fight carries it (Within).
        virtual BossMechanics::SpotBounds LedgeBounds() const = 0;
        // The cast queue: ids from kHardModeCastBase. When `id` comes up B8 calls WyrmthalakHardMode::OnCast. Higher
        // priority first; the breath is kBreathPriority (2).
        virtual void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) = 0;
        virtual void CancelCast(uint32 id) = 0;
        // A registry handle cancelled with the fight (B8's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // A unit of B9's that belongs to the fight (a shard, a kept rider, a chain anchor): despawned by B8's cleanup.
        virtual void TrackSummon(Creature* summon) = 0;
        // One INFO line "brs wyrmthalak <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // B9's hard mode for one pull. Every hook has a do-nothing default.
    class WyrmthalakHardMode
    {
    public:
        virtual ~WyrmthalakHardMode() = default;

        // The pull (B9: the 400k health through DungeonKit::Flex::SetHealth, Tribal Ward, the descriptor edits).
        virtual void OnEngage(WyrmthalakFight& /*fight*/) { }
        virtual void OnUpdate(WyrmthalakFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(WyrmthalakFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }

        // WT4 in the hard mode: how many tribes one order calls (B9: 2), whether the first order brings all three
        // champions (B9: true), and the cadence (normal 30 s, heroic 25 s).
        virtual uint8 TribesPerOrder(WyrmthalakFight const& /*fight*/) const { return 1; }
        virtual bool AllChampionsAtFirstOrder(WyrmthalakFight const& /*fight*/) const { return false; }
        virtual uint32 OrderEveryMs(WyrmthalakFight const& /*fight*/, uint32 baseMs) const { return baseMs; }
        // An order is about to call `tribes` (B9 may edit the list).
        virtual void OnOrder(WyrmthalakFight& /*fight*/, std::vector<Tribe>& /*tribes*/) { }
        virtual void OnChampionSummoned(WyrmthalakFight& /*fight*/, Tribe /*tribe*/, Creature* /*champion*/) { }
        virtual void OnChampionDied(WyrmthalakFight& /*fight*/, Tribe /*tribe*/, Creature* /*champion*/) { }

        // WT10: a boulder landed (its spot, after the hit): B9 leaves a Stolen Magic shard there.
        virtual void OnBoulderLanded(WyrmthalakFight& /*fight*/, Position const& /*at*/) { }
        // WT11: who throws the Axe Volley (B9: the Smolderthorn Champion while it lives; nullptr: a thrower on the
        // ramp), and the axes' landing spots (one per marked player, after the hit).
        virtual Creature* AxeThrower(WyrmthalakFight& /*fight*/) { return nullptr; }
        virtual void OnAxesLanded(WyrmthalakFight& /*fight*/, std::vector<Position> const& /*spots*/) { }
        // WT12: a rider reached its lane's end. Return true to keep it (B8 forgets it; B9 makes it an add).
        virtual bool OnRiderCharged(WyrmthalakFight& /*fight*/, Creature* /*rider*/) { return false; }

        // WT1b on the hard mode: the next breath's burn (B9 after the Smolderthorn Champion dies: 120 s, the whole
        // cone; the cap 3 fallback by maxAlive).
        virtual BurnSpec Burn(WyrmthalakFight const& /*fight*/, BurnSpec base) const { return base; }
        // WT14: a player his ability hit.
        virtual void OnAbilityHit(WyrmthalakFight& /*fight*/, Ability /*ability*/, Unit* /*hit*/) { }

        // The queue picked `id` (one of B9's): start the cast now. Return how long it holds him (ms: the cast bar),
        // during which nothing else on the queue starts and he does not melee; nullopt: it could not start. B8 takes
        // the entry off the queue before this call (StartHardModeCast), so a ScheduleCast of the same id from here
        // (the next one, or a retry) stays queued. A cast bar of his kicked during the hold ends the hold.
        virtual std::optional<uint32> OnCast(WyrmthalakFight& /*fight*/, uint32 /*id*/) { return std::nullopt; }

        // Death (died), evade or reset. Undo every change made to him here (health, auras).
        virtual void OnEnd(WyrmthalakFight& /*fight*/, bool /*died*/) { }
    };

    using WyrmthalakHardModeFactory = std::function<std::unique_ptr<WyrmthalakHardMode>(Creature* boss)>;

    // B9, from its AddSC_ function (once; a second call replaces the first).
    void RegisterWyrmthalakHardMode(WyrmthalakHardModeFactory factory);
    // B8, on a heroic pull with DATA_WAR_HORN lit: nullptr when nothing is registered.
    std::unique_ptr<WyrmthalakHardMode> CreateWyrmthalakHardMode(Creature* boss);
}

#endif
