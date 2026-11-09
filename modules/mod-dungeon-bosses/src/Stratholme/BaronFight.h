/*
 * mod-dungeon-bosses, Stratholme S14: Baron Rivendare's hard mode hooks (engine side). WP-S14 owns this file (the
 * Scholomance RasFight.h pattern).
 *
 * The hard mode "the Ultimatum" (WP-S15, heroic only) fights on S14's AI, boss_baron_rivendare_rework. S14 keeps the
 * whole normal and heroic kit (Raise Dead, the bone piles, Death and Decay with its rot, Unholy Aura, the stock tank
 * kit); S15 adds the executions, Condemned, the Deathcharger lanes, the long healing rot and Ysida, Risen through two
 * interfaces:
 *
 *   BaronHardMode  S15's per-pull object. S15 registers a factory once, from AddSC_strat_baron_hard_mode:
 *                      StratBaron::RegisterBaronHardMode([](Creature*) { return std::make_unique<Ultimatum>(); });
 *                  On every pull that is heroic with DATA_ULTIMATUM lit, S14 asks the factory for one and calls its
 *                  hooks below; on any other pull none is made.
 *   BaronFight     what S14's AI offers the hard mode during the pull (passed to every hook): the fight's players, the
 *                  servants, the bone piles and their raising, the rots, the cast queue, the drop spot rule, the
 *                  handle list.
 *
 * Hook order: OnEngage after S14's own engage (encounter begun, descriptor set, Unholy Aura on, the timeline and the
 * Shadow Bolt queued; S14 does not say its aggro yell on a hard mode pull: S15 says line 11). OnUpdate every AI tick
 * in combat, before S14's beats. OnCast when the cast queue picks one of S15's ids. OnRotTick once a second for every
 * live rot (S14's Death and Decay and S15's own), after S14 has raised the piles inside it. OnDamageTaken before
 * BossAI's. OnEnd from S14's cleanup (death, evade, reset; `died` on the death), before S14 despawns its summons,
 * piles and rots. The instance already stores DATA_ULTIMATUM, clears it on his death or the clock's end, records
 * BOSS_ULTIMATUM, sets the loot bit and opens the exit gate when Ysida is dead; S14 frees a living Ysida on his death
 * as the stock row did (her SmartAI's SetData(2, 2)).
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_BARON_FIGHT_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_BARON_FIGHT_H

#include "BaronLogic.h"
#include "BossMechanics.h"
#include "Define.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include "Position.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace StratBaron
{
    class BaronHardMode;

    // One rot: S14's Death and Decay, or a hard mode trail spot (S15's Deathcharger lane, rot stalkers 5 yd apart).
    // Each rot is an invisible rot stalker (NPC_ST_ROT 300588) at its spot for `life`.
    struct RotSpec
    {
        Position at;                                // its spot (S14 snaps the height to the floor)
        float radius = kRotRadius;                  // the zone's radius, the pile raise reach and S15's heal reach
        Milliseconds life{ kRotLifeMs.normal };
        // > 0: a registry persistent circle of `radius` at `tickPct` % of the reference row per second (Shadow,
        // SPELL_BR_ROT, Weakened once per player, a 1 s grace); 0: no zone (S15's lane draws its own line Zone).
        float tickPct = 0.f;
        uint32 lookSpell = SPELL_BR_ROT_LOOK;       // cast by the stalker on itself; 0: none
        bool raises = true;                         // raise the piles inside on heroic (at the spawn, then each second)
        uint32 tag = TAG_ROT;                       // the rot's kind, as OnRotTick sees it (S15: its own tags)
    };

    // A live rot, as OnRotTick sees it.
    struct RotInfo
    {
        ObjectGuid stalker;
        Position center;
        float radius = 0.f;
        uint32 tag = 0;
        uint64 bornMs = 0;                          // BaronFight::ClockMs() at its spawn
        uint64 untilMs = 0;                         // BaronFight::ClockMs() when it goes
    };

    // S14's AI, as the hard mode sees it during one pull.
    class BaronFight
    {
    public:
        virtual ~BaronFight() = default;

        virtual Creature* Baron() = 0;
        virtual bool Heroic() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): S15's `.dbtest strat ultimatum`
        // reaches it through the Baron's AI (dynamic_cast<StratBaron::BaronFight*>(baron->AI())).
        virtual BaronHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock (never paused by a cast bar).
        virtual uint64 FightMs() const = 0;
        // ms the AI has run (in or out of combat): the rots' clock (RotInfo).
        virtual uint64 ClockMs() const = 0;

        // The players of the fight: alive, not game masters, in combat with him or on his arena.
        virtual std::vector<Player*> FightPlayers() = 0;

        // BR1 / BR4: his living servants (the skeletons and every unit passed to TrackServant). Each one adds to
        // Unholy Aura (+0.5% a pulse) and S15's rot heal reads them.
        virtual std::vector<Creature*> Servants() = 0;
        // A unit of S15's that serves him (Ysida, Risen): counted by Servants() while alive, despawned by S14's
        // cleanup.
        // Summon it with the Baron as summoner (it then joins his fight); its kill target entry is S15's
        // (Mechanic::EditDescriptor).
        virtual void TrackServant(Creature* servant) = 0;

        // BR2: the bone piles now (their spots).
        virtual std::vector<Position> Piles() const = 0;
        // Raises every pile within `radius` of `center` (on the same floor) as a Mindless Skeleton, whatever the
        // difficulty (the caller decides; S15's lane spots call it at the charge's end). Returns how many rose.
        virtual uint32 RaisePilesWithin(Position const& center, float radius, char const* why) = 0;

        // BR3 / HM3 / HM4: a rot at a spot (RotSpec). Returns its stalker (empty: refused). Death and Decay's own
        // length comes from BaronHardMode::DeathAndDecayLifeMs.
        virtual ObjectGuid SpawnRot(RotSpec const& spec) = 0;
        virtual std::vector<RotInfo> Rots() const = 0;
        virtual bool InAnyRot(Position const& p) const = 0;

        // The room's drop spot rule (X2): the room (BaronLogic.h kDropRoomCenter / kDropRoomRadius), its edge, away
        // from the group; with `avoidPiles` every pile is an avoid point (heroic Death and Decay, S15's lane).
        virtual BossMechanics::DropSpotRule RoomDropRule(bool avoidPiles) const = 0;
        // He may stand at `p`: inside his arena (the r 25 leash circle; off it he evades after the 2 s grace) and clear
        // of the stock leash (BaronLogic.h StockLeashBreached: near his door or Ramstein's he evades at once). S15
        // clamps a Deathcharger lane's end with it.
        virtual bool CanStandAt(Position const& p) const = 0;

        // The cast queue: ids from kHardModeCastBase. When `id` comes up S14 calls BaronHardMode::OnCast. Higher
        // priority first; the Shadow Bolt is 0 (it waits for both the execution and the charge).
        virtual void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) = 0;
        virtual void CancelCast(uint32 id) = 0;

        // A registry handle cancelled with the fight (S14's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // One INFO line "strat baron <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // S15's hard mode for one pull. Every hook has a do-nothing default.
    class BaronHardMode
    {
    public:
        virtual ~BaronHardMode() = default;

        // The pull (S15: the 500k health, the Deathcharger display, yell 11, its first casts on the queue).
        virtual void OnEngage(BaronFight& /*fight*/) { }
        virtual void OnUpdate(BaronFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(BaronFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // The queue picked `id` (one of S15's): start the cast now. Return how long it holds him (ms: the cast bar,
        // the charge), during which nothing else on the queue starts and he does not melee; nullopt: it could not
        // start (S14 drops the entry; reschedule it yourself).
        virtual std::optional<uint32> OnCast(BaronFight& /*fight*/, uint32 /*id*/) { return std::nullopt; }
        // BR3's rot length on this pull (the hard mode's 45 s, HM4).
        virtual uint32 DeathAndDecayLifeMs(BaronFight const& /*fight*/, uint32 baseMs) const { return baseMs; }
        // Once a second for every live rot, after S14's raise (HM4: heal him 1% and his undead 5% inside).
        virtual void OnRotTick(BaronFight& /*fight*/, RotInfo const& /*rot*/) { }
        // Death (died), evade or reset. Undo every change made to the Baron here (display, health, auras).
        virtual void OnEnd(BaronFight& /*fight*/, bool /*died*/) { }
    };

    using BaronHardModeFactory = std::function<std::unique_ptr<BaronHardMode>(Creature* baron)>;

    // S15, from its AddSC_ function (once; a second call replaces the first).
    void RegisterBaronHardMode(BaronHardModeFactory factory);
    // S14, on a heroic pull with DATA_ULTIMATUM lit: nullptr when nothing is registered.
    std::unique_ptr<BaronHardMode> CreateBaronHardMode(Creature* baron);
}

#endif
