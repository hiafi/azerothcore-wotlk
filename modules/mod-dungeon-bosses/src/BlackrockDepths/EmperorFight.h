/*
 * mod-dungeon-bosses, Blackrock Depths D23: Emperor Dagran Thaurissan's hard mode hooks (engine side). WP-D23 owns this
 * file (the IncendiusFight.h / ArgelmachFight.h / Blackrock Spire WyrmthalakFight.h pattern).
 *
 * The hard mode, the Avatar of Ragnaros (WP-D24, heroic only; S4 "Hard mode", EM11-EM13, section 3.7, rulings 77-81),
 * fights on D23's AI, boss_emperor_dagran_thaurissan_rework. Nothing arms it: on heroic, lethal damage to Dagran while
 * Moira lives ("Dagran first") turns into Ragnaros Awakens instead of his death, as long as D24 registered a factory
 * (EmperorLogic.h AwakensOnLethal). Without one, or on normal, Dagran first is a real kill and Moira stands down
 * (stock). Two interfaces:
 *
 *   EmperorHardMode    D24's object for one hard mode. D24 registers a factory once, from AddSC_brd_emperor_hard_mode:
 *                          BrdEmperor::RegisterEmperorHardMode([](Creature*) { return std::make_unique<X>(); });
 *                      D23 asks the factory for one at the lethal hit (not at the pull: nothing arms it) and drops it
 *                      when the attempt ends (death, evade, reset).
 *   EmperorFight       what D23's AI offers the hard mode (passed to every hook).
 *
 * The Dagran-first branch, in order (D23 does every step but the ones named D24):
 *   1. DamageTaken, the lethal hit, AwakensOnLethal: D23 clamps him at 1 health (the kit's LethalGuard; it stays
 *      armed and clamps every hit until the Avatar rises). On the next AI tick (Awaken) D23 makes the hard mode object
 *      and calls SetData(DATA_AVATAR, 1) on the instance (the hard mode loot bit; refused off heroic, while wave 2 is
 *      unbound or while the slot is not IN_PROGRESS: then the guard is disarmed, the refusal is latched for the pull
 *      and the next hit is a real kill).
 *   2. D23, at once: the phase is Transition; every court beat stops (Nemesis cancelled, Necrosis and Mind Blast
 *      stop, the Hand and Flamestrike stop); the guards and the Ambassadors leave (they walk to their wing and
 *      despawn); Moira is caged (the fire cage, SV_MOIRA_FIRE_CAGE 90652 at her base and the flame whirl: spells
 *      211630 / 211631; NOT_SELECTABLE, no damage taken, passive, kept in combat, nothing cast; section 7 #19); yell
 *      line 10 ("Ragnaros! Your servant calls!"). Then EmperorHardMode::OnAwaken: D24's knockback, the JumpTo the
 *      throne spot, the Wrath of Ragnaros look (D24's slice).
 *   3. kTransitionMs (3 s) later: EmperorHardMode::OnRise: D24 swaps the display (11121 at the VR scale), roots him,
 *      sets the Avatar's 260k health and combat reach; then D23 disarms the lethal guard (the Avatar's death is real),
 *      the phase is Avatar, the descriptor is rebuilt (ConfigureDescriptor) and D23's own beats restart as
 *      AvatarBeat allows (default: Firestorm, heroic values, 5 s later: "Firestorm continues").
 *   4. The Avatar's turn (the Avatar phase): EmperorHardMode::OnUpdate every AI tick after D23's beats (Magma Clap,
 *      Volcanic Blast and its stones are D24's); OnDamageTaken from DamageTaken; Melee() decides whether D23 swings.
 *   5. The kill: D23's JustDied (BossAI writes slot 18 DONE; the instance records BOSS_AVATAR and DATA_MOIRA_SAVED
 *      and saves); D23 calls OnEnd(died = true) first, then breaks the cage and stands Moira down (stock line, faction
 *      35, passive: she stays friendly on every load through the instance). The Dark Keeper Key and the hard mode
 *      list are L-2's loot rows (the loot bit was set at step 1).
 *   6. A wipe or an evade in the transition or the Avatar phase: OnEnd(died = false) (D24 undoes the display, scale,
 *      root, health and its own objects), then D23's cleanup: the cage breaks, Moira evades with him (back to her spot,
 *      selectable, hostile), the guards are gone; the instance clears DATA_AVATAR when the attempt ends.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_EMPEROR_FIGHT_H
#define MOD_DUNGEON_BOSSES_BRD_EMPEROR_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "EmperorLogic.h"
#include <functional>
#include <memory>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;

namespace BrdEmperor
{
    class EmperorHardMode;

    // D23's AI, as the hard mode sees it.
    class EmperorFight
    {
    public:
        virtual ~EmperorFight() = default;

        virtual Creature* Dagran() = 0;
        // The princess on the dais (Moira, or the High Priestess standing in), alive or not; nullptr when gone.
        virtual Creature* Moira() = 0;
        virtual bool Heroic() const = 0;
        virtual Phase CurrentPhase() const = 0;
        // The hard mode object of this attempt (nullptr before the lethal hit or out of combat): D24's `.dbtest brd
        // avatar` reaches it through his AI (dynamic_cast<BrdEmperor::EmperorFight*>(boss->AI())).
        virtual EmperorHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock (never paused by a cast bar or the transition).
        virtual uint64 FightMs() const = 0;
        // ms since the transition started (0 before it).
        virtual uint64 SinceAwakenMs() const = 0;
        // The players of the fight: alive, not game masters, on his threat list.
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- Moira (the cage is D23's: step 2; D24's `.dbtest` may toggle it) ----
        virtual bool MoiraCaged() const = 0;
        virtual void CageMoira(char const* why) = 0;
        virtual void UncageMoira(char const* why) = 0;

        // ---- D23's kit (each fires one now; `forced`: that player instead of a random pick) ----
        // EM9: `count` 6 yd circles (0: the difficulty's count) under random players, the first under `forced`.
        // Returns how many were registered.
        virtual uint32 Firestorm(uint32 count, Player* forced) = 0;
        // Firestorm and the other D23 beats wait until FightMs() >= `untilMs` (D24's Magma Clap cast, say).
        virtual void HoldBeats(uint64 untilMs) = 0;

        // ---- bookkeeping ----
        // A registry handle cancelled with the attempt (D23's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // A unit of D24's that belongs to the attempt (a Volcanic Stone stalker): despawned by D23's cleanup.
        virtual void TrackSummon(Creature* summon) = 0;
        // One INFO line "brd emperor <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D24's hard mode for one attempt. Every hook has a do-nothing default (no Avatar: the fight would simply go on at
    // 1 health until the transition ends; D24 must at least set the Avatar's health in OnRise).
    class EmperorHardMode
    {
    public:
        virtual ~EmperorHardMode() = default;

        // Step 2, at the lethal hit, after D23's own transition work: the knockback, the jump to the throne spot, the
        // transition's look.
        virtual void OnAwaken(EmperorFight& /*fight*/) { }
        // Step 3, kTransitionMs later: the Avatar (display 11121 at the VR scale, root, 260k health, combat reach).
        // D23 disarms the lethal guard right after.
        virtual void OnRise(EmperorFight& /*fight*/) { }
        // The Avatar phase, every AI tick in combat, after D23's beats.
        virtual void OnUpdate(EmperorFight& /*fight*/, uint32 /*diff*/) { }
        // The transition and the Avatar phase, from DamageTaken (after the lethal guard).
        virtual void OnDamageTaken(EmperorFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // Before D23 sets the Avatar phase's descriptor (D23 leaves only what is still there: no guards, no Moira, no
        // Ambassadors; D24 adds its own entries).
        virtual void ConfigureDescriptor(EmperorFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }

        // The policies of the Avatar phase:
        // Which of D23's beats run (EmperorLogic.h Beat; default BeatRunsIn(beat, Phase::Avatar, heroic): Firestorm).
        virtual bool AvatarBeat(EmperorFight const& fight, Beat beat) const
        {
            return BeatRunsIn(beat, Phase::Avatar, fight.Heroic());
        }
        // The first Firestorm after the rise, and its cadence and count (default: 5 s, heroic values).
        virtual uint32 FirstFirestormMs(EmperorFight const& /*fight*/) const { return kFirestormAfterMs; }
        virtual uint32 FirestormEveryMs(EmperorFight const& /*fight*/, uint32 base) const { return base; }
        virtual uint32 FirestormCount(EmperorFight const& /*fight*/, uint32 base) const { return base; }
        // Does D23 swing (default yes; a rooted Avatar's reach is D24's: false hands melee to OnUpdate).
        virtual bool Melee(EmperorFight const& /*fight*/) const { return true; }

        // Death (died), evade or reset. Undo every change made to him here (display, scale, root, health, objects).
        virtual void OnEnd(EmperorFight& /*fight*/, bool /*died*/) { }
    };

    using EmperorHardModeFactory = std::function<std::unique_ptr<EmperorHardMode>(Creature* boss)>;

    // D24, from its AddSC_ function (once; a second call replaces the first).
    void RegisterEmperorHardMode(EmperorHardModeFactory factory);
    // D23: the branch exists (a factory is registered).
    bool HasEmperorHardMode();
    // D23, at the lethal hit: nullptr when nothing is registered.
    std::unique_ptr<EmperorHardMode> CreateEmperorHardMode(Creature* boss);
}

#endif
