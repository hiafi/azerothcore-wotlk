/*
 * mod-dungeon-bosses, Scarlet Monastery D4: Bloodmage Thalnos's hard mode hooks (engine side). WP-D4 owns this file
 * (the Blackrock Depths ArgelmachFight.h / EmperorFight.h pattern).
 *
 * The hard mode, the Desecration (WP-D4H, heroic only; GY "Hard mode", TH7, TH8, RH1-RH6; handoff section 3.7),
 * fights on D4's AI, boss_bloodmage_thalnos_rework, without editing it. Three interfaces:
 *
 *   ThalnosHardMode     D4H's per-pull object. D4H registers a factory once, from AddSC_sm_thalnos_hard_mode:
 *                           SmThalnos::RegisterThalnosHardMode([](Creature*) { return std::make_unique<X>(); });
 *                       On every pull that is heroic with DATA_HARD_MODE_THALNOS lit (the instance's saved flag), D4
 *                       asks the factory for one and calls its hooks; on any other pull none is made (a lit flag with
 *                       no factory runs the normal heroic and logs a warning).
 *   ThalnosFight        what D4's AI offers the hard mode during the pull (passed to every hook).
 *   ThalnosIdleHook     D4H, out of combat: called every AI tick while he is alive, not engaged and not evading (the
 *                       red aura while the flag is lit, after a wipe or a cold load). Registered once with
 *                       RegisterThalnosIdleHook.
 *
 * What D4 already does on a hard mode pull: reads the flag at the pull (heroic only) and logs the pull with
 * hardmode=1 (OnBossPull); his arena guard is the Desecration's (the crypt and the lawn, DesecrationArena) until
 * SetGround(Ground::Lawn) narrows it to the lawn; he does NOT yell line 1 at his first empowered spell (that line is
 * the teleport's on hard mode: D4H says it with Say(SAY_NO_REST)); the instance keeps the hard mode loot bit, records
 * BOSS_DESECRATION on the kill and stands portal P1h instead of P1. D4's kit runs on the lawn unchanged ("he keeps
 * casting his full kit in the yard"): Blood Nova hits every player on his ground, Blood Lance reaches 30 yd there,
 * Flame Spike's drop room and every bot bound follow the ground; the crypt's pools stay behind and burn out.
 *
 * Hook order: OnEngage after D4's own engage (encounter begun, descriptor set, beats started; D4H: 360k, the red aura,
 * Blood Pact's ward). ThresholdPct read once at the pull. OnThreshold once, the first tick his health is at or below
 * it (D4H: line 1, the 3 s teleport: HoldBeats / StopCasting, NearTeleportTo, SetGround(Ground::Lawn) in the tick he
 * moves, then the risen). OnUpdate every AI tick in combat, after D4's beats. OnDamageTaken from DamageTaken (Blood
 * Pact). ConfigureDescriptor before D4's descriptor is set at the pull and on every RefreshDescriptor (the kill order,
 * Repent / Greater Heal on the interrupt list, the Shield on the purge list). OnEnd from D4's cleanup (death, evade,
 * reset; `died` on the death), before D4 despawns its summons: undo every change made to him here (health, auras);
 * D4's cleanup then despawns every summon he owns (JustSummoned) and every unit passed to TrackSummon, cancels every
 * handle passed to Track, and on an evade on the lawn puts him back on his crypt spawn.
 */

#ifndef MOD_DUNGEON_BOSSES_SM_THALNOS_FIGHT_H
#define MOD_DUNGEON_BOSSES_SM_THALNOS_FIGHT_H

#include "BossMechanics.h"
#include "Define.h"
#include "ThalnosLogic.h"
#include <functional>
#include <memory>
#include <string>
#include <vector>

class Creature;
class Player;
class Unit;
class WorldObject;

namespace SmThalnos
{
    class ThalnosHardMode;

    // The mechanics D4 fires on demand (FireNow).
    enum class Kit : uint8
    {
        BloodBolt,      // TH2 (Blood Lance when he holds 3)
        FlameSpike,     // TH3
        BoilingBlood,   // TH4
        BloodNova,      // TH5
        BloodBrand,     // TH6 (any difficulty when fired by hand)
    };

    // D4's AI, as the hard mode sees it during one pull.
    class ThalnosFight
    {
    public:
        virtual ~ThalnosFight() = default;

        virtual Creature* Thalnos() = 0;
        virtual bool Heroic() const = 0;
        // The pull's hard mode object (nullptr on a pull without it, or out of combat): D4H's `.dbtest sm desecration`
        // reaches it through his AI (dynamic_cast<SmThalnos::ThalnosFight*>(boss->AI())).
        virtual ThalnosHardMode* ActiveHardMode() = 0;
        // ms since the pull, on the AI's own clock (never paused by a cast bar or a hold).
        virtual uint64 FightMs() const = 0;
        // The players of the fight: alive, not game masters, on his threat list.
        virtual std::vector<Player*> FightPlayers() = 0;
        // The fight's players standing on his ground now (Blood Nova's targets).
        virtual std::vector<Player*> PlayersOnGround() = 0;

        // ---- the ground ----
        virtual Ground CurrentGround() const = 0;
        // Moves the fight's frame to `ground`: the arena leash (the lawn: 40 yd round kLawnCenter), the bots' bounds,
        // Flame Spike's drop room, Blood Lance's wall and Blood Nova's targets. Call it in the tick that moves him.
        virtual void SetGround(Ground ground, char const* why) = 0;

        // ---- the kit ----
        // No new cast, beat or instant debuff of D4's until FightMs() >= `untilMs` (the teleport's 3 s cast); due beats
        // stay due and fire after it.
        virtual void HoldBeats(uint64 untilMs) = 0;
        // A bar of his is running (a bolt, a lance, a spike, a nova or its pending restart).
        virtual bool Casting() const = 0;
        // Ends his current bar as his own stop (no kick: no restart, no stacks, a Lance's line and a spike's carry
        // cancelled).
        virtual void StopCasting(char const* why) = 0;
        // Fires one of D4's mechanics now as the fight would (empowered when he holds its threshold); `forced`: that
        // player as the (first) target. False when refused (casting, nobody to target).
        virtual bool FireNow(Kit mechanic, Player* forced) = 0;

        // ---- TH1 Blood Ritual ----
        virtual uint32 RitualStacks() const = 0;
        // The risen's hits count as his spells (GY "The fallen of the Crusade"): `n` players hit, at the cap (heroic
        // none). Returns the new count. `why` goes in the log.
        virtual uint32 AddRitualStacks(uint32 n, char const* why) = 0;

        // ---- units and bookkeeping ----
        // A unit of the hard mode's that fights for him (a risen hero): every fight player at 0 threat on it, so it
        // stays in combat with the group (rule 11), and the registry counts it as a unit of his encounter.
        virtual void JoinFight(Creature* unit) = 0;
        // A registry handle cancelled with the attempt (D4's cleanup).
        virtual void Track(BossMechanics::MechanicHandle handle) = 0;
        // A unit of the attempt (a risen, the banner, a stalker) not summoned by him: despawned by D4's cleanup.
        virtual void TrackSummon(Creature* summon) = 0;
        // Re-sets his descriptor now (ConfigureDescriptor runs again): a risen rose or fell.
        virtual void RefreshDescriptor() = 0;
        // His creature_text line `group` (ThalnosTexts), aimed at `target` when given.
        virtual void Say(uint8 group, WorldObject const* target = nullptr) = 0;
        // One INFO line "sm thalnos <mechanic> <detail>" in module.dungeonbosses.
        virtual void Log(char const* mechanic, std::string const& detail = {}) = 0;
    };

    // D4H's hard mode for one pull. Every hook has a do-nothing default.
    class ThalnosHardMode
    {
    public:
        virtual ~ThalnosHardMode() = default;

        // After D4's engage (the hard mode's health, aura, ward).
        virtual void OnEngage(ThalnosFight& /*fight*/) { }
        // The transition point, read once at the pull (default 75%: GY TH7).
        virtual float ThresholdPct(ThalnosFight const& /*fight*/) const { return kNoRestPct; }
        // Once, the first tick his health is at or below ThresholdPct (the teleport and the first risen).
        virtual void OnThreshold(ThalnosFight& /*fight*/) { }
        // Every AI tick in combat, after D4's beats.
        virtual void OnUpdate(ThalnosFight& /*fight*/, uint32 /*diff*/) { }
        // From DamageTaken (Blood Pact: 20% less per living risen).
        virtual void OnDamageTaken(ThalnosFight& /*fight*/, Unit* /*attacker*/, uint32& /*damage*/) { }
        // A unit he summoned (JustSummoned; D4 already tracks it for the cleanup).
        virtual void OnSummoned(ThalnosFight& /*fight*/, Creature* /*summon*/) { }
        // A unit he summoned died (SummonedCreatureDies): "the first dead one rises again".
        virtual void OnSummonDied(ThalnosFight& /*fight*/, Creature* /*summon*/, Unit* /*killer*/) { }
        // Before D4 sets his descriptor (D4's own entries are in `d`; D4H adds the kill order and the risen's casts).
        virtual void ConfigureDescriptor(ThalnosFight& /*fight*/, BossMechanics::Descriptor& /*d*/) { }
        // Death (died), evade or reset. Undo every change made to him here (health, auras, objects).
        virtual void OnEnd(ThalnosFight& /*fight*/, bool /*died*/) { }
    };

    using ThalnosHardModeFactory = std::function<std::unique_ptr<ThalnosHardMode>(Creature* boss)>;
    using ThalnosIdleHook = std::function<void(Creature* boss)>;

    // D4H, from its AddSC_ function (once; a second call replaces the first).
    void RegisterThalnosHardMode(ThalnosHardModeFactory factory);
    void RegisterThalnosIdleHook(ThalnosIdleHook hook);
    // D4: the branch exists (a factory is registered).
    bool HasThalnosHardMode();
    // D4, at a hard mode pull: nullptr when nothing is registered.
    std::unique_ptr<ThalnosHardMode> CreateThalnosHardMode(Creature* boss);
}

#endif
