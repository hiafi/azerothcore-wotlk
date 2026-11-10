/*
 * mod-dungeon-bosses, Stratholme S7: Balnazzar's hard mode hooks (engine side). WP-S7 owns this file (the BaronFight.h
 * and Scholomance RasFight.h pattern).
 *
 * The hard mode "the Grand Lie" (WP-S8, heroic only) fights on S7's AI, boss_dathrohan_balnazzar_rework. S7 keeps the
 * whole normal and heroic kit (stage 1 Dathrohan: Sacred Ground, Judgment, the stock strikes; the Unmasking; stage 2
 * Balnazzar: Carrion Swarm, Inferno and the Infernals, Sleep and Nightmare, Vampiric Aura, Mind Blast); S8 adds the
 * twins, the acts, the moving swarms, Dread Slumber and the relics through two interfaces:
 *
 *   GrandLie        S8's per-pull object. S8 registers a factory once, from AddSC_strat_balnazzar_hard_mode:
 *                       StratDathrohan::RegisterGrandLie([](Creature*) { return std::make_unique<TheGrandLie>(); });
 *                   On every heroic pull with DATA_GRAND_LIE lit, S7 asks the factory for one and calls its hooks
 *                   below; on any other pull none is made.
 *   DathrohanFight  what S7's AI offers (passed to every hook; also reachable out of combat through
 *                   dynamic_cast<StratDathrohan::DathrohanFight*>(boss->AI()), for the Letter of Proof).
 *
 * Starting the hard mode (S8, the Letter's spell script, Dathrohan out of combat on heroic): set DATA_GRAND_LIE 1 on
 * the instance, say line 8 and yell line 9 (Dathrohan's entry, 10812), then call fight.Unmask({ .stun = false, .marks =
 * false, .yell = false }) (the entry becomes Balnazzar at full health with Vampiric Aura on) and attack the letter's
 * user (boss->AI()->AttackStart(player)). S7's engage sees Balnazzar and starts stage 2 at once (no transform), makes
 * the GrandLie object and calls OnEngage, where S8 sets the 600k (SetMaxHealth / SetFullHealth) and starts act 1.
 * A heroic pull with the flag lit while he is still Dathrohan (the letter not shown on this pull) also makes the
 * object: OnEngage then sees CurrentStage() == Stage::Dathrohan and may Unmask() itself or leave the normal heroic
 * fight running.
 *
 * Hook order: OnEngage after S7's own engage (encounter begun, descriptor set, the stage's timeline queued; S7 does
 * not yell its aggro line when he engages as Balnazzar). OnUpdate every AI tick in combat, before S7's beats. AllowBeat
 * when one of S7's stage 2 beats falls due (false: S7 asks again in a second); BeatEveryMs when it fired (the next
 * one's cadence). TuneCarrion / TuneInferno before each Carrion Swarm / Inferno. OnCast when the cast queue picks one
 * of S8's ids (kHardModeCastBase on). VampiricPct on every Vampiric Aura heal. OnDamageTaken before BossAI's. OnEnd
 * from S7's cleanup (death, evade, reset; `died` on the death), before S7 despawns its Infernals and reverts him to
 * Dathrohan (UpdateEntry 10812 resets the template health, so S8's 600k needs no undo). The instance already stores
 * DATA_GRAND_LIE (it stays lit through wipes), records BOSS_GRAND_LIE and sets the loot bit on a lit kill.
 *
 * Seams S8 fills (not S7's): the relics (KT-2's RelicDispenser, not built yet) and the Counter response (deferred,
 * handoff section 7 #9).
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_DATHROHAN_FIGHT_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_DATHROHAN_FIGHT_H

#include "BossMechanics.h"
#include "DathrohanLogic.h"
#include "Define.h"
#include "ObjectGuid.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace StratDathrohan
{
    class GrandLie;

    // Unmask: how the mask comes off. The 40% transform of a normal or heroic pull is { true, true, true }: the stock
    // 17288 (full heal and the 5 s stun on everyone), the entry change 1.5 s in, the reveal yell, the Unmasking marks
    // as the stun ends. The hard mode's start is { false, false, false }: the entry changes now, at full health.
    struct UnmaskOptions
    {
        bool stun = true;       // 17288 and its 5 s stun (the entry changes 1.5 s later); false: at once
        bool marks = true;      // DB3 the Unmasking marks as the stun ends (with `stun` only)
        bool yell = true;       // Balnazzar's reveal (line 5)
    };

    // S7's AI, as the hard mode sees it.
    class DathrohanFight
    {
    public:
        virtual ~DathrohanFight() = default;

        virtual Creature* Boss() = 0;
        virtual bool Heroic() const = 0;
        virtual Stage CurrentStage() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat).
        virtual GrandLie* ActiveHardMode() = 0;
        // ms since the pull and since stage 2 began (0 before), on the AI's own clock (never paused by a cast bar).
        virtual uint64 FightMs() const = 0;
        virtual uint64 StageTwoMs() const = 0;

        // The players of the fight: alive, not game masters, in combat with him or on his arena.
        virtual std::vector<Player*> FightPlayers() = 0;

        // The mask comes off (in or out of combat). False when he is already Balnazzar, transforming, or dead.
        virtual bool Unmask(UnmaskOptions const& options) = 0;

        // S7's stage 2 kit on demand (each also fires on its own beat unless AllowBeat holds it). `forced`: aim at
        // those players (empty / nullptr: S7's random non-tank picks). Each reads TuneCarrion / TuneInferno.
        virtual bool CarrionSwarm(std::vector<Player*> const& forced) = 0;
        virtual bool Inferno(Player* forced) = 0;
        // Puts `player` to sleep with S7's Sleep aura (206566: 5 s, Magic, not broken by damage); its end applies
        // Nightmare like a landed Sleep (`pulses`: the heroic miss's pulses). Dread Slumber's sleeps (S8) use it.
        virtual bool SleepPlayer(Player* player, bool pulses) = 0;
        // The live Infernals.
        virtual std::vector<Creature*> Infernals() = 0;

        // BZ5: a hit of the hard mode's own kit landed on `victim` (a swarm tick, a twin): Vampiric Aura heals him
        // (VampiricPct). Players only; ignored before stage 2.
        virtual void VampiricHit(Unit* victim, char const* source) = 0;

        // The bots' spot bounds in his chamber (DathrohanLogic.h kBoundsRadius around the brazier, the walked path kept
        // inside). Every mechanic of the fight carries it (MechanicRef::Within).
        virtual BossMechanics::SpotBounds RoomBounds() const = 0;

        // The cast queue: ids from kHardModeCastBase. When `id` comes up S7 calls GrandLie::OnCast. Higher priority
        // first (S7's: Sacred Ground and Inferno 3, the cones 2, Sleep 1, Mind Blast 0). Stage 2's start resets the
        // queue: schedule once CurrentStage() is Stage::Balnazzar (in OnEngage after an unmasked pull, or from
        // OnUpdate after an Unmask() with the stun).
        virtual void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) = 0;
        virtual void CancelCast(uint32 id) = 0;

        // A registry handle cancelled with the fight (S7's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // One INFO line "strat balnazzar <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // S8's hard mode for one pull. Every hook has a do-nothing default.
    class GrandLie
    {
    public:
        virtual ~GrandLie() = default;

        virtual void OnEngage(DathrohanFight& /*fight*/) { }
        virtual void OnUpdate(DathrohanFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(DathrohanFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // The queue picked `id` (one of S8's): start the cast now. Return how long it holds him (ms); nullopt: it could
        // not start (S7 drops the entry; reschedule it yourself).
        virtual std::optional<uint32> OnCast(DathrohanFight& /*fight*/, uint32 /*id*/) { return std::nullopt; }
        // One of S7's stage 2 beats is due (Beat::CarrionSwarm, Inferno, Sleep, MindBlast): false holds it (S7 asks
        // again in a second: act 1 has no cones or Infernals, act 3 replaces Sleep, no meteor in a call's last 4 s).
        virtual bool AllowBeat(DathrohanFight& /*fight*/, Beat /*beat*/) { return true; }
        // The cadence after a beat fired (the hard mode's cones every 20 s).
        virtual uint32 BeatEveryMs(DathrohanFight const& /*fight*/, Beat /*beat*/, uint32 baseMs) const
        {
            return baseMs;
        }
        // Before each call: the cones (two at once, 25% / 50%, the Standard's ward) and the Inferno (the 25k Infernal).
        virtual void TuneCarrion(DathrohanFight const& /*fight*/, CarrionSpec& /*spec*/) const { }
        virtual void TuneInferno(DathrohanFight const& /*fight*/, InfernoSpec& /*spec*/) const { }
        // BZ5's percent per hit (the hard mode's 3%).
        virtual float VampiricPct(DathrohanFight const& /*fight*/, float basePct) const { return basePct; }
        // Death (died), evade or reset. Undo every change made here that the entry's revert does not (auras, units).
        virtual void OnEnd(DathrohanFight& /*fight*/, bool /*died*/) { }
    };

    using GrandLieFactory = std::function<std::unique_ptr<GrandLie>(Creature* boss)>;

    // S8, from its AddSC_ function (once; a second call replaces the first).
    void RegisterGrandLie(GrandLieFactory factory);
    // S7, on a heroic pull with DATA_GRAND_LIE lit: nullptr when nothing is registered.
    std::unique_ptr<GrandLie> CreateGrandLie(Creature* boss);
}

#endif
