/*
 * mod-dungeon-bosses, Scarlet Monastery D11: Herod's hard mode hooks (engine side). WP-D11 owns this file (the
 * ThalnosFight.h / DoanFight.h pattern).
 *
 * The hard mode, Call to Arms (WP-D11H, heroic only; ARM "Hard mode: Call to Arms", HM0-HM3; handoff section 3.7),
 * fights on D11's AI, boss_herod_rework, without editing it. D11 keeps the whole normal and heroic kit (the door, the
 * spins and their blades, the throws and the whirling axe, the cleave, Frenzy, the trainees on his death); D11H adds
 * the trigger, the prayer and the garrison, the planted axe's beams and Consecrated Hall through four interfaces:
 *
 *   HerodHardMode       D11H's per-pull object. D11H registers a factory once, from AddSC_sm_herod_hard_mode:
 *                           SmHerod::RegisterHerodHardMode([](Creature*) { return std::make_unique<X>(); });
 *                       On every pull that is heroic with DATA_HARD_MODE_HEROD lit (the instance's saved flag), D11
 *                       asks the factory for one and calls its hooks; on any other pull none is made (a lit flag with
 *                       no factory runs the plain heroic and logs a warning).
 *   HerodFight          what D11's AI offers the hard mode (passed to every hook, and to the two static hooks below).
 *   HerodTauntHandler   HM0 The Real Challenge: every /taunt text emote aimed at Herod (TEXT_EMOTE_TAUNT 136, from
 *                       CreatureAI::ReceiveEmote: no range check) reaches it, in or out of combat, on any difficulty;
 *                       D11H judges it (ScarletMonasteryRework::HerodTauntAllowed, then
 *                       SetData(DATA_HARD_MODE_HEROD, 1): the instance refuses off heroic, in combat, dead or unbound),
 *                       answers with line 5 or 6 (Say) and puts the red aura on him. Registered once with
 *                       RegisterHerodTauntHandler. D11 never answers a taunt itself.
 *   HerodIdleHook       out of combat: called every AI tick while he is alive, not engaged and not evading (the red
 *                       aura while the flag is lit, after a wipe or a cold load). Registered once with
 *                       RegisterHerodIdleHook.
 *
 * What D11 already does on a hard mode pull: reads the flag at the pull (heroic only) and logs the pull with
 * hardmode=1 (OnBossPull); the instance keeps the hard mode loot bit, records BOSS_CALL_TO_ARMS on the kill and opens
 * the door on his death. D11 does NOT set his 400k: D11H does it in OnEngage (SetCreateHealth + UpdateMaxHealth +
 * SetFullHealth, the Baron / Ras precedent) and puts the template value back in OnEnd.
 *
 * Hook order: OnEngage after D11's own engage (encounter begun, descriptor set (ConfigureDescriptor first), the door's
 * 3 s seal started, beats started). ThresholdPct read once at the pull: a value replaces D11's Frenzy at 50% (HB4) with
 * OnThreshold, called once, the first tick his health is at or below it while he is home and holds his axe (not
 * spinning, the axe not out: a threshold crossed mid-spin waits for his return). OnUpdate every AI tick in combat,
 * before D11's beats. OnDamageTaken from DamageTaken (the prayer: unharmable). OnSpinStart at each "Blades of light!"
 * yell (HM3: the beams flip), OnSpinEnd when he is home again. OnThrow when Ravager leaves his hand, OnAxeHome when it
 * is back. ConfigureDescriptor before D11 sets his descriptor at the pull and on every RefreshDescriptor (the
 * garrison's kill order). OnEnd from D11's cleanup (death, evade, reset; `died` on the death), before D11 despawns its
 * summons: undo every change made to him here (health, auras); D11's cleanup then restores Ravager to his hand, removes
 * the cyclone and Frenzy, despawns every summon he owns (JustSummoned: Summon below, his stalkers) and every unit
 * passed to TrackSummon, cancels every handle passed to Track, gives back his kit (HoldKit off), and opens the door.
 *
 * The prayer (HM2) with these hooks: OnThreshold -> HoldKit(true) (no spin, throw or cleave beat, no melee, no chase:
 * he is passive and D11H moves him: MovePoint to the center), Say(SAY_STRENGTH), OpenDoor (the march), the garrison
 * from Summon on HerodLogic.h kGarrisonMarch, SealDoor about 12 s later (it shuts 3 s after the call and pulls
 * stragglers in), then at the rising Frenzy(.., false) + Say(SAY_RISING), SetWeapon(the Crusader's blade),
 * ThrowAllowed false from then (the axe stays planted), RestartBeats, HoldKit(false).
 */

#ifndef MOD_DUNGEON_BOSSES_SM_HEROD_FIGHT_H
#define MOD_DUNGEON_BOSSES_SM_HEROD_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "HerodLogic.h"
#include "Position.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;
class WorldObject;

namespace SmHerod
{
    class HerodHardMode;

    // D11's hits whose percent the hard mode may raise (HitPct).
    enum class HerodHit : uint8
    {
        Out,        // HB1a the out lane
        Lap,        // HB1b his spin passing a player
        Blade,      // HB1c a blade of light
        Home,       // HB1d the home lane
        Throw,      // HB2 the throw's circle
        Return,     // HB2a the axe's return line
        Whirl,      // HB2w the whirling axe
        Cleave,     // HB3 the cleave on others (the tank's share stays kCleaveTankPct)
    };

    // D11's AI, as the hard mode sees it (during a pull; the taunt and idle hooks see it out of combat too).
    class HerodFight
    {
    public:
        virtual ~HerodFight() = default;

        virtual Creature* Herod() = 0;
        virtual bool Heroic() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): D11H's `.dbtest sm calltoarms`
        // and its adds reach it through his AI (dynamic_cast<SmHerod::HerodFight*>(boss->AI())).
        virtual HerodHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock (0 out of combat).
        virtual uint64 FightMs() const = 0;
        // The players of the fight: alive, not game masters, on his threat list.
        virtual std::vector<Player*> FightPlayers() = 0;

        // ---- his state ----
        // HB1: from the "Blades of light!" yell to his return to the pit's center.
        virtual bool Spinning() const = 0;
        // HB2: from the throw until Ravager is back in his hand.
        virtual bool AxeOut() const = 0;
        virtual bool Frenzied() const = 0;
        virtual uint32 SpinsStarted() const = 0;
        virtual bool KitHeld() const = 0;

        // ---- control ----
        // Holds his kit (`hold`): no new spin, throw or cleave beat (due ones stay due), no melee, and he is passive
        // (no target, no chase, the motion master cleared) so the hard mode moves him. A spin or a throw in progress
        // finishes first (OnThreshold never comes during one). Releasing gives him back his kit: aggressive, attacking
        // his top-threat unit, the next cleave kCleaveAfterHoldMs later.
        virtual void HoldKit(bool hold, char const* why) = 0;
        // The next spin `spinInMs` and the next throw `throwInMs` from now (the hard mode's rising: its own cadence).
        virtual void RestartBeats(uint32 spinInMs, uint32 throwInMs) = 0;
        // HB4's buff now (once per pull; a second call does nothing); `announce`: yell 2 and emote 4 as at 50%.
        virtual void Frenzy(char const* why, bool announce) = 0;
        // The weapon in his hand (`itemEntry` 0: Ravager, his stock axe). D11's cleanup gives Ravager back.
        virtual void SetWeapon(uint32 itemEntry, char const* why) = 0;

        // ---- Herod's Door (HB0, KT-SM SealedArena) ----
        // Opens it now (HM2: the door bursts open for the march).
        virtual void OpenDoor(char const* why) = 0;
        // Seals it again: it shuts kSealDelayMs (3 s) after the call and every straggler within 60 yd in the Armory is
        // moved inside (HM2: the door closes behind the last squad).
        virtual void SealDoor(char const* why) = 0;
        virtual bool DoorSealed() const = 0;

        // ---- units and bookkeeping ----
        // A summon of Herod's for the fight: despawned by D11's cleanup (wipe, evade, death). nullptr when refused.
        // `despawnMs` 0: manual despawn.
        virtual Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs = 0) = 0;
        // A unit of the attempt not summoned by him (the planted axe as a GO stand-in's helper): despawned by D11's
        // cleanup.
        virtual void TrackSummon(Creature* unit) = 0;
        // A unit of the hard mode's that belongs to the fight (a garrison trainee): every fight player at 0 threat on
        // it (rule 11) and the registry counts it as a unit of his encounter.
        virtual void JoinFight(Creature* unit) = 0;
        // A registry handle cancelled with the attempt (D11's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // Re-sets his descriptor now (ConfigureDescriptor runs again).
        virtual void RefreshDescriptor() = 0;
        // His creature_text line `group` (HerodTexts), aimed at `target` when given.
        virtual void Say(uint8 group, WorldObject const* target = nullptr) = 0;
        // One INFO line "sm herod <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D11H's hard mode for one pull. Every hook has a do-nothing default; every tuning query's nullopt keeps D11's
    // heroic value.
    class HerodHardMode
    {
    public:
        virtual ~HerodHardMode() = default;

        // After D11's engage (the hard mode's 400k, the red aura).
        virtual void OnEngage(HerodFight& /*fight*/) { }
        // The transition point, read once at the pull. nullopt: D11's Frenzy at 50% (HB4). A value: OnThreshold there
        // instead of Frenzy (HM2 the Garrison Answers, at 50%).
        virtual std::optional<float> ThresholdPct(HerodFight const& /*fight*/) const { return std::nullopt; }
        // Once, the first tick his health is at or below ThresholdPct while he is home and holds his axe.
        virtual void OnThreshold(HerodFight& /*fight*/) { }
        // Every AI tick in combat, before D11's beats.
        virtual void OnUpdate(HerodFight& /*fight*/, uint32 /*diff*/) { }
        // From DamageTaken (the prayer: he cannot be harmed).
        virtual void OnDamageTaken(HerodFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // HB1: the yell (`index` 1 for the first spin; `clockwise` the lap's direction). HM3: the beams flip here.
        virtual void OnSpinStart(HerodFight& /*fight*/, uint32 /*index*/, bool /*clockwise*/) { }
        // HB1: he is home at the pit's center again.
        virtual void OnSpinEnd(HerodFight& /*fight*/, uint32 /*index*/) { }
        // HB2: Ravager left his hand / is back in it.
        virtual void OnThrow(HerodFight& /*fight*/) { }
        virtual void OnAxeHome(HerodFight& /*fight*/) { }
        // A unit he summoned (JustSummoned; D11 already tracks it for the cleanup) and its death.
        virtual void OnSummoned(HerodFight& /*fight*/, Creature* /*summon*/) { }
        virtual void OnSummonDied(HerodFight& /*fight*/, Creature* /*summon*/, Unit* /*killer*/) { }
        // Before D11 sets his descriptor (D11's entries are in `d`; D11H adds the garrison ahead of Herod).
        virtual void ConfigureDescriptor(HerodFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }
        // Death (died), evade or reset. Undo every change made to him here (health, auras, objects).
        virtual void OnEnd(HerodFight& /*fight*/, bool /*died*/) { }

        // ---- tuning (read when D11 needs the value) ----
        // HB1: the spins' cadence after the first (heroic 32 s; the hard mode's 28.16 s) and the lap's speed (12; 14).
        virtual std::optional<uint32> SpinEveryMs(HerodFight const& /*fight*/) const { return std::nullopt; }
        virtual std::optional<float> LapSpeedYd(HerodFight const& /*fight*/) const { return std::nullopt; }
        // HB1c: the blades' cadence and count at once (heroic 1.5 s x 1, after Frenzy 1 s x 2; the hard mode 1.5 s x 2
        // all fight).
        virtual std::optional<BladePlan> Blades(HerodFight const& /*fight*/) const { return std::nullopt; }
        // HB2: the throws' cadence after the first (heroic 32 s; 28.16 s), the whirl's length (heroic 5 s; 6 s), and
        // whether he throws at all (false: the second half, Ravager planted).
        virtual std::optional<uint32> ThrowEveryMs(HerodFight const& /*fight*/) const { return std::nullopt; }
        virtual std::optional<uint32> WhirlMs(HerodFight const& /*fight*/) const { return std::nullopt; }
        virtual bool ThrowAllowed(HerodFight const& /*fight*/) const { return true; }
        // Any hit's percent of the reference row (heroic 45; the hard mode's 60).
        virtual std::optional<float> HitPct(HerodFight const& /*fight*/, HerodHit /*hit*/) const
        {
            return std::nullopt;
        }
    };

    using HerodHardModeFactory = std::function<std::unique_ptr<HerodHardMode>(Creature* herod)>;
    // `inCombat`: he is engaged (HM0 refuses then). `player` sent the /taunt with Herod as the target.
    using HerodTauntHandler = std::function<void(HerodFight& fight, Player* player, bool inCombat)>;
    using HerodIdleHook = std::function<void(HerodFight& fight)>;

    // D11H, from its AddSC_ function (once each; a second call replaces the first).
    void RegisterHerodHardMode(HerodHardModeFactory factory);
    void RegisterHerodTauntHandler(HerodTauntHandler handler);
    void RegisterHerodIdleHook(HerodIdleHook hook);
    // D11: the branch exists (a factory is registered).
    bool HasHerodHardMode();
    // D11, at a hard mode pull: nullptr when nothing is registered.
    std::unique_ptr<HerodHardMode> CreateHerodHardMode(Creature* herod);
}

#endif
