/*
 * mod-dungeon-bosses, Scarlet Monastery D13: Scarlet Commander Mograine's risen state, the hooks D14 (High Inquisitor
 * Whitemane, with Mograine risen) builds on (engine side). WP-D13 owns this file (the ThalnosFight.h / BRD
 * ArgelmachFight.h pattern); D14 attaches the finale without editing boss_mograine_rework.cpp.
 *
 * D13's AI (boss_mograine_rework) runs Mograine through MograineState (LastStandLogic.h): Altar, Stand, Fight, then
 * Falling and Fallen when he falls at 1% (the Last Stand DONE: the instance sends the credit 212301, opens the High
 * Inquisitor's Door, sends ACTION_SM_MOGRAINE_FALLEN to him and ACTION_SM_WHITEMANE_VIGIL to Whitemane). Fallen, he
 * lies at kMograineBody (1154, 1398.4, 33.0), passive, not selectable and immune (rule 10: nothing to hit), the home
 * position of every later evade; a cold load with slot 5 DONE (DATA_CATHEDRAL_STAGE 2 or 3) puts him there in Reset.
 *
 * D14 takes over from there with two interfaces:
 *
 *   MograineFight   what D13's AI offers the finale (MograineFightOf(creature) finds it). Rise() turns a Fallen
 *                   Mograine into the Risen state; every other call is for the Risen state.
 *   MograineRisen   D14's object for one rising (from the scarlet resurrection until the pair dies, or her fight
 *                   wipes). D14 registers a factory once from its AddSC_ function:
 *                       SmLastStand::RegisterMograineRisen([](Creature*) { return std::make_unique<X>(); });
 *                   Rise() asks the factory for one and calls OnRise; with no factory registered he rises with D13's
 *                   default risen kit only (and logs a warning).
 *
 * What D13 does in the Risen state: selectable and attackable, aggressive, melee on his victim, Retribution Aura on
 * every rise, and his risen kit on the AI's own clock (CATH WM "Mograine, risen"): Crusader Strike (first 3 s, then
 * every 10 s) and Divine Storm (LS5's numbers: first 12 s, then every 15 s; 8 / 10 yd, 30 / 45% plus Weakened, the
 * tank 15 / 25%). SetCadence changes either (the Truth's 10 s storm), HoldKit pauses the kit (a save channel, To Her
 * Side), HoldControl hands D14 the AI entirely for a while (the charge to her side: no victim updates, no chase, no
 * melee, no kit). No lethal guard of his own: D14's OnDamageTaken keeps him alive for the saves (a LethalGuard of
 * D14's) and lets the killing blow through when the pair dies together; JustDied then calls OnDied and OnEnd(true).
 * His encounter in the finale is D14's: D13 registers his risen Divine Storm with him as the owner and does not
 * Describe anything in the Risen state.
 *
 * Every hook has a do-nothing default. Hook order: OnRise after D13's rise (health set, flags cleared, aura cast,
 * kit armed); OnUpdate every AI tick in the Risen state, after D13's kit (also while held); OnDamageTaken from
 * DamageTaken (before the damage lands); OnEngage from JustEngagedWith; OnEvade from EnterEvadeMode (return true to
 * keep him where he is: D14 handled it; false: D13 ends the rising and sends him back to his body); OnAction from
 * DoAction (D13's own actions are handled first); OnMovementInform, OnSpellCast and OnSpellFailed from the AI hooks of
 * the same name; OnDied from JustDied; OnEnd once when the rising ends (BackToBody, an unhandled evade, his death,
 * the stand's reset), after which the object is destroyed.
 */

#ifndef MOD_DUNGEON_BOSSES_SM_MOGRAINE_FIGHT_H
#define MOD_DUNGEON_BOSSES_SM_MOGRAINE_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "LastStandLogic.h"
#include <functional>
#include <memory>
#include <string>

class Creature;
class Player;
class SpellInfo;
class Unit;
class WorldObject;

namespace SmLastStand
{
    class MograineRisen;

    // His kit, as the finale may pace or fire it.
    enum class MograineKit : uint8
    {
        CrusaderStrike,     // stock 14518 on his victim
        DivineStorm,        // LS5: the 2 s wind-up, then the whirl (TankExempt circle + the tank's own hit)
        HammerOfJustice,    // LS4: the thrown hammer (off in the Risen state unless D14 sets a cadence)
    };
    inline constexpr std::size_t kMograineKitCount = 3;

    // D13's AI, as the finale sees it.
    class MograineFight
    {
    public:
        virtual ~MograineFight() = default;

        virtual Creature* Mograine() = 0;
        virtual bool Heroic() const = 0;
        virtual MograineState State() const = 0;
        // The rising's object (nullptr outside the Risen state or with no factory registered).
        virtual MograineRisen* ActiveRisen() = 0;
        // ms since the current rising, on the AI's own clock (0 outside the Risen state).
        virtual uint64 RisenMs() const = 0;

        // ---- the rising (from Fallen) ----
        // He rises where he lies: `maxHealth` (the finale's: 45k / 200k, the hard mode 280k; 0 keeps his template
        // health) at `healthPct` of it, selectable, attackable and aggressive; Retribution Aura; the risen kit armed;
        // the rising's object created (OnRise with `first` = the first rising since the stand). D14 says his line 2
        // ("At your side, milady!"). False when he is not Fallen (or not alive).
        virtual bool Rise(uint32 maxHealth, float healthPct, char const* why) = 0;
        // His fall inside the finale (WM1a: her save window): the fallen look where he stands, no attacks, no kit, not
        // selectable and immune until GetUp or KillForGood. Health is D14's (keep him at 1 with a LethalGuard).
        virtual void Down(char const* why) = 0;
        virtual bool IsDown() const = 0;
        // The save finished: up at `healthPct` of his maximum, back on his victim.
        virtual void GetUp(float healthPct, char const* why) = 0;
        // Kneels `ms` (the Truth: the father's light, the Verdict, the transition): no attacks, no kit, still
        // attackable (a designed window); back on his victim after.
        virtual void Kneel(uint32 ms, char const* why) = 0;
        // Back to his body spot, Fallen (her fight wiped or reset; never the Last Stand's reset): OnEnd(false), his
        // template health back, the vigil look once he arrives.
        virtual void BackToBody(char const* why) = 0;
        // Dies for real (the pair died together): `killer` gets the kill (quests 1048 / 1053 credit his real death;
        // his own loot, Heart of Zeal and cloth, drops then). Clears Down and the immunity first.
        virtual void KillForGood(Unit* killer) = 0;

        // ---- the kit ----
        // The risen cadence of `kit`: first `firstMs` after now, then every `everyMs` (everyMs 0: off).
        virtual void SetCadence(MograineKit kit, uint32 firstMs, uint32 everyMs) = 0;
        // No new kit cast and no melee until RisenMs() >= untilMs; due casts wait and fire after it.
        virtual void HoldKit(uint64 untilMs) = 0;
        // D14 drives him until RisenMs() >= untilMs: no victim update, no chase, no melee, no kit (a charge, a
        // channel). D14 restarts his chase (AttackStart) when it is done; the hold ending re-attacks his victim.
        virtual void HoldControl(uint64 untilMs) = 0;
        virtual bool Casting() const = 0;
        virtual void StopCasting(char const* why) = 0;
        // Fires one of his kit now (his victim; `forced`: that player for the Hammer). False when refused (casting,
        // held, down, nobody to target).
        virtual bool FireNow(MograineKit kit, Player* forced = nullptr) = 0;

        // ---- bookkeeping ----
        // A registry handle cancelled when the rising ends.
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // His creature_text line `group` (MograineTexts; D14's 12-13), aimed at `target` when given.
        virtual void Say(uint8 group, WorldObject const* target = nullptr) = 0;
        // One INFO line "sm laststand <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D14's object for one rising. Every hook has a do-nothing default.
    class MograineRisen
    {
    public:
        virtual ~MograineRisen() = default;

        virtual void OnRise(MograineFight& /*fight*/, bool /*first*/) { }
        virtual void OnUpdate(MograineFight& /*fight*/, uint32 /*diff*/) { }
        virtual void OnDamageTaken(MograineFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        virtual void OnEngage(MograineFight& /*fight*/, Unit* /*who*/) { }
        // True: handled (he stays risen); false: D13 ends the rising and sends him back to his body.
        virtual bool OnEvade(MograineFight& /*fight*/) { return false; }
        virtual void OnAction(MograineFight& /*fight*/, int32 /*action*/) { }
        virtual void OnMovementInform(MograineFight& /*fight*/, uint32 /*type*/, uint32 /*id*/) { }
        virtual void OnSpellCast(MograineFight& /*fight*/, SpellInfo const* /*spell*/) { }
        virtual void OnSpellFailed(MograineFight& /*fight*/, SpellInfo const* /*spell*/) { }
        virtual void OnDied(MograineFight& /*fight*/, Unit* /*killer*/) { }
        // Once, when the rising ends (`died`: his real death). Undo what the object changed on him (auras).
        virtual void OnEnd(MograineFight& /*fight*/, bool /*died*/) { }
    };

    using MograineRisenFactory = std::function<std::unique_ptr<MograineRisen>(Creature* mograine)>;

    // D14, from its AddSC_ function (once; a second call replaces the first).
    void RegisterMograineRisen(MograineRisenFactory factory);
    bool HasMograineRisen();
    // D13, at Rise: nullptr when nothing is registered.
    std::unique_ptr<MograineRisen> CreateMograineRisen(Creature* mograine);
    // D14's way in: Mograine's AI as the finale sees it (nullptr when he does not run boss_mograine_rework).
    MograineFight* MograineFightOf(Creature* mograine);
}

#endif
