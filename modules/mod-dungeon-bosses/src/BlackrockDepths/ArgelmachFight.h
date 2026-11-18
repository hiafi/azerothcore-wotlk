/*
 * mod-dungeon-bosses, Blackrock Depths D15: Golem Lord Argelmach's hard mode hooks (engine side). WP-D15 owns this
 * file (the IncendiusFight.h / Blackrock Spire WyrmthalakFight.h pattern).
 *
 * The hard mode, the Prototype (WP-D16, heroic only; S3 "Hard mode", AR11-AR13, section 3.7), fights on D15's AI,
 * boss_golem_lord_argelmach_rework. D15 keeps the golems D16 shares (the three pedestal golems, their signatures, the
 * chemical clouds); D16 adds Magmatron on the fourth pedestal, Incineration, the Flamethrower, the Salvaged Cores and
 * the hard mode's health through two interfaces and one idle hook:
 *
 *   ArgelmachHardMode   D16's per-pull object. D16 registers a factory once, from AddSC_brd_argelmach_hard_mode:
 *                           BrdArgelmach::RegisterArgelmachHardMode([](Creature*) { return std::make_unique<X>(); });
 *                       On every pull that is heroic with DATA_CONSOLE_ARMED lit, D15 asks the factory for one and
 *                       calls its hooks; on any other pull none is made (an armed console with no factory runs the
 *                       normal heroic and logs a warning).
 *   ArgelmachFight      what D15's AI offers the hard mode during the pull (passed to every hook).
 *   ArgelmachIdleHook   D16, out of combat: called every AI tick while he is alive, not engaged and not evading (the
 *                       fourth statue on its pedestal, the console's look; a reload or a wipe: rule 7). Registered once
 *                       with RegisterArgelmachIdleHook. D15's own idle work (the three dormant statues) runs first.
 *
 * What D15 already does on a hard mode pull: reads DATA_CONSOLE_ARMED at the pull (heroic only); OnBossPull(me, key,
 * true); the instance keeps the hard mode loot bit while the console is armed, records BOSS_PROTOTYPE on the kill and
 * clears the flag when the attempt ends (a wipe: the console is usable again). A dead golem stays on its pedestal as a
 * wreck (a corpse) for the rest of the pull: the Salvaged Core's spot (AR13).
 *
 * Hook order: OnEngage after D15's own engage (encounter begun, descriptor set, beats started; D16: 500k, Magmatron).
 * WakePct when the pull reads the thresholds (once, at the pull). OnGolemWoken right after a golem wakes (D16: 50k).
 * OnGolemDied once, the tick D15 sees a golem dead (D16: the Salvaged Core). OnUpdate every AI tick in combat, after
 * D15's beats. OnDamageTaken from DamageTaken. ConfigureDescriptor before D15's descriptor is set (D16: Magmatron in
 * the kill order). OnEnd from D15's cleanup (death, evade, reset; `died` on the death), before it
 * despawns its golems, orbs, clouds and summons: undo every change made to him here (health, auras).
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_ARGELMACH_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRD_ARGELMACH_FIGHT_H

#include "ArgelmachLogic.h"
#include "BossMechanics.h"
#include "Define.h"
#include "Position.h"
#include <functional>
#include <memory>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace BrdArgelmach
{
    class ArgelmachHardMode;

    // D15's AI, as the hard mode sees it during one pull.
    class ArgelmachFight
    {
    public:
        virtual ~ArgelmachFight() = default;

        virtual Creature* Boss() = 0;
        virtual bool Heroic() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): D16's `.dbtest brd prototype`
        // reaches it through his AI (dynamic_cast<BrdArgelmach::ArgelmachFight*>(boss->AI())).
        virtual ArgelmachHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock.
        virtual uint64 FightMs() const = 0;
        // The players of the fight: alive, not game masters, on his threat list.
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- the golems ----
        // The golem on its pedestal now (dormant, awake or its wreck; nullptr between a cleanup and the next idle
        // tick).
        virtual Creature* GolemUnit(Golem g) = 0;
        virtual bool GolemAwake(Golem g) const = 0;
        virtual bool GolemDead(Golem g) const = 0;
        // Wakes it now (AR4's yell, the look, its beats), whatever his health. False when already awake or not there.
        virtual bool WakeGolem(Golem g, char const* why) = 0;
        // A unit of the fight's side that stands still and casts like a golem (D16's Magmatron, a Salvaged Core's
        // stalker): every fight player at 0 threat, so it stays in combat with the group (rule 11).
        virtual void JoinFight(Creature* unit) = 0;

        // ---- the signatures (each fires one now; `source` casts the looks: a golem, its wreck or a core stalker) ----
        // AR5: `count` marks (random players, the tank included; `forced`: that player is the first). The clouds drop
        // 4 s later. Returns the marks placed.
        virtual uint32 ChemicalBomb(Unit* source, uint32 count, Player* forced) = 0;
        // AR7: a tether on two random players (`forced`: that player is one of them). False with fewer than two.
        virtual bool LethalAttraction(Unit* source, Player* forced) = 0;
        // AR9: an Arcane Orb from `from` that drifts to him in 10 s. False when refused.
        virtual bool PowerGenerator(Position const& from) = 0;

        // ---- the clouds (AR5; D16's Incineration detonates them) ----
        // Where every live Chemical Bomb cloud lies now.
        virtual std::vector<Position> Clouds() const = 0;
        // Ends every live cloud now (zone, look) and returns where they were (D16 bursts them there).
        virtual std::vector<Position> TakeClouds(char const* why) = 0;

        // ---- bookkeeping ----
        // A registry handle cancelled with the fight (D15's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // A unit of D16's that belongs to the fight (Magmatron, a core's stalker): despawned by D15's cleanup.
        virtual void TrackSummon(Creature* summon) = 0;
        // One INFO line "brd argelmach <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D16's hard mode for one pull. Every hook has a do-nothing default (the normal heroic fight).
    class ArgelmachHardMode
    {
    public:
        virtual ~ArgelmachHardMode() = default;

        // The pull (D16: 500k health, Magmatron awake on the fourth pedestal).
        virtual void OnEngage(ArgelmachFight& /*fight*/) { }
        // AR4: the health percent at which `g` wakes (D16: Toxitron 80, Electron 60, Arcanoton 40).
        virtual float WakePct(ArgelmachFight const& /*fight*/, Golem /*g*/, float base) const { return base; }
        // Right after a golem woke (D16: its 50k health).
        virtual void OnGolemWoken(ArgelmachFight& /*fight*/, Golem /*g*/, Creature* /*golem*/) { }
        // Once, the tick D15 sees the golem dead; `wreck` is its corpse on the pedestal (nullptr when it is gone; the
        // spot is PedestalOf(g)). D16: the Salvaged Core.
        virtual void OnGolemDied(ArgelmachFight& /*fight*/, Golem /*g*/, Creature* /*wreck*/) { }
        virtual void OnUpdate(ArgelmachFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(ArgelmachFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // Before D15 sets the descriptor (D16: Magmatron in the kill order).
        virtual void ConfigureDescriptor(ArgelmachFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }

        // Death (died), evade or reset. Undo every change made to him here.
        virtual void OnEnd(ArgelmachFight& /*fight*/, bool /*died*/) { }
    };

    using ArgelmachHardModeFactory = std::function<std::unique_ptr<ArgelmachHardMode>(Creature* boss)>;
    using ArgelmachIdleHook = std::function<void(Creature* boss, uint32 diff)>;

    // D16, from its AddSC_ function (once; a second call replaces the first).
    void RegisterArgelmachHardMode(ArgelmachHardModeFactory factory);
    void RegisterArgelmachIdleHook(ArgelmachIdleHook hook);
    // D15, on a heroic pull with DATA_CONSOLE_ARMED lit: nullptr when nothing is registered.
    std::unique_ptr<ArgelmachHardMode> CreateArgelmachHardMode(Creature* boss);
}

#endif
