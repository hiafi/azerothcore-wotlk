/*
 * mod-dungeon-bosses, Scarlet Monastery D14: High Inquisitor Whitemane's hard mode hooks (engine side). WP-D14 owns
 * this file (the ThalnosFight.h / HerodFight.h pattern).
 *
 * The hard mode, The Truth (WP-D14H, heroic only; CATH "Hard mode: The Truth", HM0-HM5; handoff section 3.7), fights on
 * D14's AI, boss_whitemane_rework, without editing it. D14 keeps the whole normal and heroic fight (the vigil, the
 * rising, both saves, To Her Side, Penance, Heal, the shield, Holy Smite, the Vigil Flame; Mograine's risen kit through
 * D13's MograineFight.h); D14H adds the Torch's trigger, the vigil Fairbanks, the spirit of Alexandros and the father's
 * judgment through three hooks:
 *
 *   WhitemaneHardMode   D14H's per-pull object. D14H registers a factory once, from AddSC_sm_whitemane_hard_mode:
 *                           SmWhitemane::RegisterWhitemaneHardMode([](Creature*) { return std::make_unique<X>(); });
 *                       On every pull that is heroic with DATA_HARD_MODE_WHITEMANE lit (the instance's saved flag),
 *                       D14 asks the factory for one and calls its hooks; on any other pull none is made (a lit flag
 *                       with no factory runs the plain heroic and logs a warning).
 *   WhitemaneFight      what D14's AI offers the hard mode (passed to every hook; D14H's `.dbtest sm truth` and its
 *                       units reach it with dynamic_cast<SmWhitemane::WhitemaneFight*>(whitemane->AI())).
 *   WhitemaneIdleHook   out of combat: every AI tick while she is alive and not engaged (at her vigil, walking out,
 *                       in her chamber): the vigil Fairbanks kneeling beside her after the Torch, after a wipe and
 *                       after a cold load. Registered once with RegisterWhitemaneIdleHook.
 *
 * What D14 already does on a hard mode pull: logs the pull with hardmode=1 (OnBossPull); the instance keeps the loot
 * bit (DungeonKit::SetHardModeLoot at the Torch and at the pull) and records BOSS_THE_TRUTH when she dies. D14 does NOT
 * set her 340k: D14H sets it (at the Torch, HM0, and again in OnEngage: SetCreateHealth + UpdateMaxHealth +
 * SetFullHealth, the Herod / Baron precedent) and puts the template value back in OnEnd and after a wipe. Mograine's
 * 280k comes through RisenMaxHealth (D14 passes it to MograineFight::Rise at the rising).
 *
 * Hook order: OnEngage after D14's own engage (the encounter begun, the descriptor set: ConfigureDescriptor first, the
 * timeline armed). OnUpdate every AI tick in combat, before D14's timeline (also while she lies as a body).
 * OnDamageTaken for both of the pair, before D14's own handling (the heroic body shield, the lethal rules): the
 * Inquisitor's Ward scales `damage` here. OnRise once Mograine stands (`first`: the rising at P + 15 s; later ones are
 * her saves). OnSaveStart when a save begins (`fallen` is the one held at 1 health; `windowMs` the channel's length as
 * D14 timed it, SaveWindowMs applied), OnSaveEnd when it ends (`rose`: the channel finished and the fallen stood up at
 * 50%; false: the pair died, or the attempt ended). OnToHerSide when Mograine arrives beside her (WM2). OnEnd from
 * D14's cleanup (her death `died`, evade, reset), before D14 despawns its summons and clears its auras: undo every
 * change made here (health, auras, objects); D14's cleanup then removes the flame, Seared and the Penance marks from
 * every player, cancels every handle passed to Track, despawns every unit from Summon or JoinFight, sends Mograine back
 * to his body (a wipe) and re-describes nothing.
 *
 * D14H's phases with these hooks:
 * - HM1 (Fairbanks at the vigil): ConfigureDescriptor adds him first; ToHerSideEveryMs 20 s, FlameEveryMs 8 s and
 *   SearedMs 15 s while he lives; his Heal and Shield are his own casts on Whitemane / Mograine (fight.Whitemane(),
 *   fight.Mograine(); "the lower of the pair": fight.LowerOfPair()). JoinFight(fairbanks) puts every fight player on
 *   his threat list (rule 11) and counts him as a unit of her encounter.
 * - HM2 (the Truth, at his death): HoldMechanics(true) for the transition (no mechanic fires, due ones wait; her
 *   casts go on), Say(SAY_WHITEMANE_LIES), MograineFightOf(fight.Mograine())->Kneel(3000, ...) and his lines 4 and 5,
 *   then HoldMechanics(false) and RestartTimer for the new cadences.
 * - HM3 (the father's judgment): the light's kneel is MograineFight::Kneel; the Verdict's root is MograineFight::
 *   HoldControl (check SaveInProgress() and LaneInProgress() first: D14 drives him through HoldControl in his save and
 *   in To Her Side); ToHerSideAllowed false while a Verdict marker is up; a Verdict through her calls BreakCast (her
 *   cast breaks; a save channel in progress starts over: "a Verdict landed through her mid-save buys the window
 *   back").
 * - HM4 (Guilt and Denial): SaveWindowMs 6 s (her channel) / 4 s (his), ToHerSideEveryMs back to nullopt (25 s), the
 *   flame back to 10 s with SearedMs 15 s, his storm every 10 s through MograineFight::SetCadence.
 * - HM5 (the ending): OnEnd(died = true): the spirit speaks and fades.
 */

#ifndef MOD_DUNGEON_BOSSES_SM_WHITEMANE_FIGHT_H
#define MOD_DUNGEON_BOSSES_SM_WHITEMANE_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "Position.h"
#include "WhitemaneLogic.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;
class WorldObject;

namespace SmLastStand
{
    class MograineFight;
}

namespace SmWhitemane
{
    class WhitemaneHardMode;

    // One of the pair.
    enum class PairUnit : uint8
    {
        Whitemane,
        Mograine,
    };

    // Her timers a hook may restart (RestartTimer).
    enum class WhitemaneTimer : uint8
    {
        ToHerSide,      // WM2
        Penance,        // WM3
        Heal,           // WM4
        Shield,         // WM4a
        VigilFlame,     // WM5 (heroic): the next flare
        Smite,          // WM6
    };

    // D14's AI, as the hard mode sees it (during a pull; the idle hook sees it out of combat too).
    class WhitemaneFight
    {
    public:
        virtual ~WhitemaneFight() = default;

        virtual Creature* Whitemane() = 0;
        // Mograine (alive or dead; nullptr when he is not in the map).
        virtual Creature* Mograine() = 0;
        // D13's AI on him (nullptr when he does not run boss_mograine_rework).
        virtual SmLastStand::MograineFight* MograineAI() = 0;
        virtual bool Heroic() const = 0;
        virtual WhitemaneState State() const = 0;
        virtual PairStage Stage() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat).
        virtual WhitemaneHardMode* ActiveHardMode() = 0;
        // ms since the pull and since the rising (R = P + 15 s; 0 before it), on the AI's own clock.
        virtual uint64 FightMs() const = 0;
        virtual uint64 RisingMs() const = 0;
        // A save channel or its run is in progress (WM1a / WM1b).
        virtual bool SaveInProgress() const = 0;
        // To Her Side, from his line to his arrival (he is driven through MograineFight::HoldControl).
        virtual bool LaneInProgress() const = 0;
        // The one of the pair with the lower percent of health that still stands (nullptr when neither does).
        virtual Creature* LowerOfPair() = 0;
        // The players of the fight: alive, not game masters, on her threat list.
        virtual std::vector<Player*> FightPlayers() = 0;
        // The fight's tank: the role provider on Mograine while he is risen and alive (down in her save included: then
        // the real tank, not her top-threat player); on her once he is gone.
        virtual bool IsTank(Player const* player) = 0;

        // ---- control ----
        // Pulls her (and the fight) as if `who` attacked her at the vigil (the vigil Fairbanks pulled first).
        virtual void StartFight(Unit* who, char const* why) = 0;
        // HM3a: her current cast breaks (Holy Smite, Heal); a save channel in progress starts over (its window again
        // from now). Nothing when she casts nothing.
        virtual void BreakCast(char const* why) = 0;
        // Her mechanics hold (`hold`): no Penance, To Her Side or flare starts (due ones wait); Smite, Heal, Shield and
        // a save still run. Releasing lets the due ones fire (a carried flame's flare no sooner than kFlameRewarnMs,
        // its soak registered again).
        virtual void HoldMechanics(bool hold, char const* why) = 0;
        virtual bool MechanicsHeld() const = 0;
        // The next `timer` fires `inMs` from now (a new cadence; the rows' own cadence follows from there).
        virtual void RestartTimer(WhitemaneTimer timer, uint32 inMs) = 0;

        // ---- units and bookkeeping ----
        // A summon of hers for the fight: despawned by D14's cleanup (wipe, evade, death). nullptr when refused.
        // `despawnMs` 0: manual despawn.
        virtual Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs = 0) = 0;
        // A unit of the hard mode's that fights (the vigil Fairbanks): every fight player at 0 threat on it (rule 11),
        // the registry counts it as a unit of her encounter, and D14's cleanup despawns it unless `keep`.
        virtual void JoinFight(Creature* unit, bool keep = false) = 0;
        // A registry handle cancelled with the attempt (D14's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // Re-sets her descriptor now (ConfigureDescriptor runs again).
        virtual void RefreshDescriptor() = 0;
        // Her creature_text line `group` (WhitemaneTexts), aimed at `target` when given.
        virtual void Say(uint8 group, WorldObject const* target = nullptr) = 0;
        // One INFO line "sm whitemane <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D14H's hard mode for one pull. Every hook has a do-nothing default; every tuning query's nullopt keeps D14's
    // heroic value.
    class WhitemaneHardMode
    {
    public:
        virtual ~WhitemaneHardMode() = default;

        // After D14's engage (her 340k, the vigil Fairbanks into the fight).
        virtual void OnEngage(WhitemaneFight& /*fight*/) { }
        // Every AI tick in combat, before D14's timeline.
        virtual void OnUpdate(WhitemaneFight& /*fight*/, uint32 /*diff*/) { }
        // Damage to either of the pair, before D14's own handling (HM1 Inquisitor's Ward: half while Fairbanks lives).
        virtual void OnDamageTaken(WhitemaneFight& /*fight*/, PairUnit /*unit*/, Unit* /*attacker*/,
            uint32& /*damage*/) { }
        // Mograine stands (`first`: the rising; later: her saves).
        virtual void OnRise(WhitemaneFight& /*fight*/, bool /*first*/) { }
        // WM1a / WM1b: `fallen` is held at 1 health; the other channels for `windowMs`.
        virtual void OnSaveStart(WhitemaneFight& /*fight*/, PairUnit /*fallen*/, uint32 /*windowMs*/) { }
        virtual void OnSaveEnd(WhitemaneFight& /*fight*/, PairUnit /*fallen*/, bool /*rose*/) { }
        // WM2: Mograine arrived beside her.
        virtual void OnToHerSide(WhitemaneFight& /*fight*/) { }
        // Before D14 sets her descriptor (D14's entries are in `d`; D14H adds Fairbanks first, his Heal and Curse).
        virtual void ConfigureDescriptor(WhitemaneFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }
        // Her death (`died`), evade or reset. Undo every change made to her and him here.
        virtual void OnEnd(WhitemaneFight& /*fight*/, bool /*died*/) { }

        // ---- tuning (read when D14 needs the value) ----
        // WM1a / WM1b: the channel of the one saving `fallen` (heroic 8 s / 5 s; HM4 6 s / 4 s).
        virtual std::optional<uint32> SaveWindowMs(WhitemaneFight const& /*fight*/, PairUnit /*fallen*/) const
        {
            return std::nullopt;
        }
        // WM2: the cadence after each charge (heroic 25 s; HM1 20 s). False: not now (a Verdict marker is up).
        virtual std::optional<uint32> ToHerSideEveryMs(WhitemaneFight const& /*fight*/) const { return std::nullopt; }
        virtual bool ToHerSideAllowed(WhitemaneFight const& /*fight*/) const { return true; }
        // WM5: the flare's cadence (heroic 10 s; HM1 8 s) and Seared's length (19 s; the hard mode's 15 s).
        virtual std::optional<uint32> FlameEveryMs(WhitemaneFight const& /*fight*/) const { return std::nullopt; }
        virtual std::optional<uint32> SearedMs(WhitemaneFight const& /*fight*/) const { return std::nullopt; }
        // WM1: Mograine's maximum health at the rising (heroic 200k; the hard mode 280k).
        virtual std::optional<uint32> RisenMaxHealth(WhitemaneFight const& /*fight*/) const { return std::nullopt; }
    };

    using WhitemaneHardModeFactory = std::function<std::unique_ptr<WhitemaneHardMode>(Creature* whitemane)>;
    using WhitemaneIdleHook = std::function<void(WhitemaneFight& fight)>;

    // D14H, from its AddSC_ function (once each; a second call replaces the first).
    void RegisterWhitemaneHardMode(WhitemaneHardModeFactory factory);
    void RegisterWhitemaneIdleHook(WhitemaneIdleHook hook);
    // D14: the branch exists (a factory is registered).
    bool HasWhitemaneHardMode();
    // D14, at a hard mode pull: nullptr when nothing is registered.
    std::unique_ptr<WhitemaneHardMode> CreateWhitemaneHardMode(Creature* whitemane);
}

#endif
