/*
 * mod-dungeon-bosses, Ragefire Chasm D4: Taragaman's hard mode hooks (engine side). Owned by WP-D4; D4H never edits
 * D4's .cpp.
 *
 * The hard mode, Starving (WP-D4H, heroic only; SP 812-878, handoff section 3.7), fights on D4's AI,
 * boss_taragaman_rework. D4 keeps the whole normal and heroic kit and reads its tuning from
 * RagefireChasmRework::Taragaman's Tri<> tables with FightMode(): the hard mode column already holds HM's Feast mark,
 * bite and Devour, the Felstorm, pulses and spots, the Nova's 3 s bar, spikes and 90%. D4H adds the rest through:
 *
 *   TaragamanHardMode    D4H's per-pull object. D4H registers a factory once, from AddSC_rfc_taragaman_hard_mode:
 *                            RfcTaragaman::RegisterTaragamanHardMode([](Creature*) { return std::make_unique<X>(); });
 *                        On every pull that is heroic with DATA_HARD_MODE set D4 asks the factory for one and calls its
 *                        hooks; on any other pull none is made. No factory: the pull is plain heroic (logged).
 *   TaragamanFight       what D4's AI offers the hard mode (passed to every hook; also
 *                        dynamic_cast<RfcTaragaman::TaragamanFight*>(boss->AI()) for the globules' AI and `.dbtest`).
 *   TaragamanIdleHook    every AI tick while he is alive, not engaged and not evading, and once at once after
 *                        ACTION_RFC_HARD_MODE_ARMED / _CLEARED: the hard mode's health and look whenever
 *                        instance->GetData(DATA_HARD_MODE) is set (a wipe, a respawn, a cold load), and their undoing
 *                        when it is not. Idempotent: D4 calls it at the AI's rate.
 *   TaragamanActionHook  the instance's DoAction values, as they arrive (ACTION_RFC_GATE_OPENED,
 *                        ACTION_RFC_HARD_MODE_ARMED / _CLEARED): one-shot things (line 9 at the pour).
 *
 * Hook order on a pull: the registry's encounter, then (hard mode) OnEngage, then the descriptor (DescribeExtra), then
 * D4's pull line, so the pull line logs the health OnEngage left. In combat, every tick: OnUpdate first (StartFeast
 * from its poll wins over a beat due on the same tick), then D4's running beat, then the beats due by their timers,
 * then Uppercut and melee. OnEnd runs first in D4's cleanup (death, evade, reset), with the fight object still usable.
 *
 * A pull of the hard mode:
 *   phase 1   OnUpdate polls LowestPrey() for anyone under 30% and calls StartFeast, at least kStarvingGapMs after
 *             LastFeastMs; FeastByTimer only once that gap passed too (D4's own timer, at its own pace in its queue)
 *             and, in phase 2, with no combo due.
 *             D4's timers start the Felstorm and the Nova. FelstormSpot places him for the bar (a leap first when he
 *             is off it), DriftTarget moves the ring.
 *   phase 2   NotePhaseChange() and HoldSetPieces(true); the combo: StartFelstorm every kComboEveryMs, StartNova
 *             kComboNovaAfterSpinMs after OnFelstormEnd; SetFeastHold(the phase's shorter one); globules
 *             from Summon, Gorge(kGlobuleDrunkHealPct) for a
 *             drunk one. A refused start (false) is tried again on the next tick.
 *
 * Everything the hard mode changes on Taragaman (his health, auras) it undoes in OnEnd or the idle hook. Units it
 * summons come from Summon, handles go to Track: D4's cleanup takes both away (RB-1).
 */

#ifndef MOD_DUNGEON_BOSSES_RFC_TARAGAMAN_FIGHT_H
#define MOD_DUNGEON_BOSSES_RFC_TARAGAMAN_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "ObjectGuid.h"
#include "Position.h"
#include "RagefireChasmRework.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;
class WorldObject;

namespace RfcTaragaman
{
    class TaragamanHardMode;

    // D4's AI, as the hard mode sees it during one pull.
    class TaragamanFight
    {
    public:
        virtual ~TaragamanFight() = default;

        virtual Creature* Taragaman() = 0;
        virtual RagefireChasmRework::Mode FightMode() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat).
        virtual TaragamanHardMode* ActiveHardMode() = 0;

        // The players of the fight: alive, not game masters, on his threat list.
        virtual std::vector<Player*> FightPlayers() = 0;
        virtual uint64 ClockMs() const = 0;                     // since the pull

        // TG1. FeastEligible: alive, on the plateau's floor, within kFeastRangeYd of the hub (section 7 #24 A).
        // LowestPrey: the eligible player with the lowest health percent, ties at random (nullptr: nobody).
        // StartFeast: mark `prey` now; refused (false) while any beat runs, while a set piece of D4's timers is due, in
        // the hold after a set piece, in a phase's first 2 s, or for a player who is not eligible.
        virtual bool FeastEligible(Player const* player) const = 0;
        virtual Player* LowestPrey() = 0;
        virtual bool StartFeast(Player* prey) = 0;
        virtual bool FeastActive() const = 0;                   // from the mark to the end of its Devour
        virtual uint64 LastFeastMs() const = 0;                 // ClockMs of the last mark; 0: none yet

        // TG3 / TG6: start one now (phase 2's combo); refused (false) while any beat runs, a Feast included.
        virtual bool StartFelstorm() = 0;
        virtual bool StartNova() = 0;
        // TG3 (from the cast until its last spot has erupted, up to 1 s past the spin) or TG6 is running.
        virtual bool SetPieceActive() const = 0;
        // Phase 2: D4's own Felstorm and Nova timers stop while held (the hard mode starts them).
        virtual void HoldSetPieces(bool hold) = 0;
        // The Feast's hold after a set piece (kFeastAfterSetPieceMs at every pull); phase 2 shortens it.
        virtual void SetFeastHold(uint32 ms) = 0;
        // A phase starts now: no Feast in its first 2 s. Also sets the bots' phase (Mechanic::SetPhase).
        virtual void NotePhaseChange(uint32 phase) = 0;

        // A Gorged stack (no cap on heroic and in the hard mode) and a heal of `healPct` percent of his maximum health.
        virtual void Gorge(float healPct) = 0;
        virtual uint32 GorgedStacks() const = 0;
        // What his stacks do to his percent hits (1 + 10% per stack): for a hard mode hit that is his.
        virtual float DamageFactor() const = 0;

        // A summon of his for the fight: despawned by D4's cleanup (wipe, evade, death). nullptr when refused.
        // `despawnMs` 0: manual despawn. D4 does not zone it into combat.
        virtual Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs = 0) = 0;
        // A registry handle cancelled with the fight (D4's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // Describe again (DescribeExtra included): the kill order of a new phase.
        virtual void RefreshDescriptor() = 0;
        virtual void Say(uint8 group, WorldObject const* target = nullptr) = 0;
        // One INFO line "rfc taragaman <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D4H's hard mode for one pull. Every hook has a do-nothing default.
    class TaragamanHardMode
    {
    public:
        virtual ~TaragamanHardMode() = default;

        virtual void OnEngage(TaragamanFight& /*fight*/) { }
        virtual void OnUpdate(TaragamanFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(TaragamanFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // A Feast's mark went out on `prey` / the Feast is over (its Devour done, kicked, or the Feast cancelled).
        virtual void OnFeastStart(TaragamanFight& /*fight*/, Player* /*prey*/) { }
        virtual void OnFeastEnd(TaragamanFight& /*fight*/) { }
        // The spin starts (after the 2 s cast) / ends (he fights again; the last spots may still be on the floor).
        virtual void OnFelstormStart(TaragamanFight& /*fight*/) { }
        virtual void OnFelstormEnd(TaragamanFight& /*fight*/) { }
        // The Nova starts (he leaps to the hub) / is over.
        virtual void OnNovaStart(TaragamanFight& /*fight*/) { }
        virtual void OnNovaEnd(TaragamanFight& /*fight*/) { }
        virtual void OnSummonDied(TaragamanFight& /*fight*/, Creature* /*summon*/) { }
        // Death (died), evade or reset. Undo every change made to him here.
        virtual void OnEnd(TaragamanFight& /*fight*/, bool /*died*/) { }

        // Extra entries for the bots' boss data (the globules' kill order); D4's are already in `d`.
        virtual void DescribeExtra(TaragamanFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }

        // TG1: D4's own Feast timer may fire now (the hard mode: only a Feast gap after the last mark).
        virtual bool FeastByTimer(TaragamanFight const& /*fight*/) const { return true; }
        // TG3: asked as a Felstorm starts (either phase): where he must stand for its bar. He leaps there first, before
        // the bar and the ring exist; nullopt: the bar starts where he stands. Return it on the arena's floor.
        // (WP-D4H's one addition, section 7 #25 A: the center of the ring stays within 8 yd of his spawn.)
        virtual std::optional<Position> FelstormSpot(TaragamanFight& /*fight*/) { return std::nullopt; }
        // TG3: asked at the spin's start and every kDriftRepickMs of it: the point he (and the ring on him) drifts to
        // now, in a straight floor line at kDriftSpeed. Return it already clamped (kDriftClampYd of his spawn, on the
        // arena); nullopt: he stays where he is.
        virtual std::optional<Position> DriftTarget(TaragamanFight& /*fight*/) { return std::nullopt; }
    };

    using TaragamanHardModeFactory = std::function<std::unique_ptr<TaragamanHardMode>(Creature* taragaman)>;
    using TaragamanIdleHook = std::function<void(Creature* taragaman)>;
    using TaragamanActionHook = std::function<void(Creature* taragaman, int32 action)>;

    // D4H, from its AddSC_ function (once each; a second call replaces the first; any AddSC_ order).
    void RegisterTaragamanHardMode(TaragamanHardModeFactory factory);
    void RegisterTaragamanIdleHook(TaragamanIdleHook hook);
    void RegisterTaragamanActionHook(TaragamanActionHook hook);
    // D4, on a heroic pull with DATA_HARD_MODE set: nullptr when nothing is registered.
    std::unique_ptr<TaragamanHardMode> CreateTaragamanHardMode(Creature* taragaman);
}

#endif
