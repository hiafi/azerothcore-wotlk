/*
 * mod-dungeon-bosses, Zul'Farrak CR: Sergeant Bly's crew (Bly 7604, Raven 7605, Oro 7606, Weegli 7607, Murta 7608).
 * WP-CR owns this file and BlyCrew.cpp (handoff section 3.12). Every other WP moves, heals, damages, kills and
 * restores a crew member only through this header (section 3.5 rule 28) and never writes a crew template or faction.
 * The interface is documented in .agents/plans/zul-farrak-build/zul-farrak-build.STAGE-CR-REPORT.md section 1.
 *
 * Who does what:
 *   the instance          stores each member's CrewMode, the living mask, the path, the Test's key; respawns the
 *                         fallen by spawn id (RB-20); logs every mode change ("zf-build crew <entry> <old> <new>");
 *                         sends ACTION_ZF_CREW_MODE / _PYRAMID_STAGE / _CREW_FIGHT / _POOL_RESET
 *   BlyCrewAI (here)      applies the mode: faction, react state, gossip flag, where the member stands (the stock
 *                         stair, descent and gather walks, the pool), the stock kits (casts on timers, Murta's script
 *                         heals), Weegli's 1 health floor and his End Door walk, the Block's prisoner machine, Bly's
 *                         gossip (betrayal first, the Test second) and the default fight start, the default Test yield
 *   a CrewModeHandler     a later WP's behavior in one mode (D4b Ally, D5 Boss and Yielded, D7Ha PoolAlly):
 *                         RegisterCrewModeHandler from the WP's AddSC_; it is asked first and may replace CR's default
 *
 * Mirrored stock code (AGENTS.md credit rule): the crew's walks, Bly's betrayal sequence and gossip gates, Weegli's
 * door walk (spot, plant, escape path 815530) and the kits' timers follow zulfarrak.cpp and instance_zulfarrak.cpp:
 * c9315e3ec moostigre <moostigre@proton.me> (#27731), 048025ceb UltraNix <80540499+UltraNix@users.noreply.github.com>
 * (#7855).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_BLY_CREW_H
#define MOD_DUNGEON_BOSSES_ZF_BLY_CREW_H

#include "BlyCrewLogic.h"
#include "Define.h"
#include "EventMap.h"
#include "ObjectGuid.h"
#include "Position.h"
#include "ScriptedCreature.h"
#include "ZulFarrakRework.h"
#include <array>
#include <functional>
#include <memory>
#include <optional>

class Creature;
class InstanceScript;
class Player;
class SpellInfo;
class Unit;

namespace ZfCrew
{
    struct BlyCrewAI;

    // Movement point ids the crew AI uses; a handler's own MovePoint / WalkTo ids start at kPointHandlerBase (CR
    // ignores those and forwards them to OnMovementInform).
    enum CrewPoints : uint32
    {
        POINT_CREW_SPOT         = 1,    // a rest spot (BlyCrewAI::Spot() says which)
        POINT_PRISONER_CHAIN    = 2,    // the Block: the jump to the chain spot
        POINT_PRISONER_CAGE     = 3,    // the Block: the jump back into the cage
        POINT_WEEGLI_DOOR       = 4,    // Weegli's barrel spot at the End Door
        kPointHandlerBase       = 100,
    };

    // Bly's and Weegli's text groups (creature_text 7604, 7607; 0-based as SP prints them, rule 34). 0-2 are stock;
    // CR's rev inserts the new ones, which their WPs say.
    enum CrewTexts : uint8
    {
        SAY_BLY_BETRAYAL_1      = 0,    // stock "What? How dare you say that to me?!?"
        SAY_BLY_BETRAYAL_2      = 1,    // stock "After all we've been through? ..."
        SAY_BLY_FORWARD         = 2,    // stock "Let's move forward!" (CR: the walk down to the stair's foot)
        YELL_BLY_GANG_UP        = 3,    // D5 BC1 "Get $n, lads!"
        SAY_BLY_TEST_DONE       = 4,    // D5 BC11 "Enough! You've proven yourselves. ..." (CR's default yield says it)
        YELL_BLY_BEHIND_ME      = 5,    // D7Ha GZ17 "Behind me, $n!"
        SAY_WEEGLI_OH_NO        = 0,    // stock "Oh no! Here they come!" (CR: arriving at the stair, stage 2 running)
        SAY_WEEGLI_HERE_I_GO    = 1,    // stock "Ok, here I go!" (CR: the Test path's door walk)
        SAY_WEEGLI_OUT_OF_HERE  = 2,    // stock "I'm out of here!" (CR: the betrayal's door walk)
        YELL_WEEGLI_BARRELS     = 3,    // D4b PY4 "Fire in the hole! Get off the stairs!"
        YELL_WEEGLI_CHARGE      = 4,    // D7Ha GZ16 "Fire in the hole!"
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Handlers: a later WP's behavior for the crew in one mode. One factory per (mode, member); the AI makes the
    // handler the first time the member enters the mode and keeps it for the AI's life (state survives a mode change:
    // reset per attempt in OnEnter). Every hook has a do-nothing default. "Return true" means "handled: skip CR's
    // default for this call".
    // ----------------------------------------------------------------------------------------------------------------
    class CrewModeHandler
    {
    public:
        virtual ~CrewModeHandler() = default;

        // The member entered the mode (`from`: the previous mode; from == the mode after a create, a respawn or a
        // reload). Called after CR's default (faction, react state, the spot), so a handler may move the member on.
        virtual void OnEnter(BlyCrewAI& /*ai*/, CrewMode /*from*/) { }
        // The member leaves the mode (before CR's default for the new one).
        virtual void OnLeave(BlyCrewAI& /*ai*/, CrewMode /*to*/) { }
        // Every UpdateAI tick in the mode, before CR's kit. True: the tick is the handler's (no kit, no melee).
        virtual bool OnUpdate(BlyCrewAI& /*ai*/, uint32 /*diff*/) { return false; }
        // A DoAction (the instance's ACTION_ZF_* or a WP's own). True: CR's default for it is skipped.
        virtual bool OnAction(BlyCrewAI& /*ai*/, int32 /*action*/) { return false; }
        virtual void OnEngage(BlyCrewAI& /*ai*/, Unit* /*who*/) { }
        // Before CR's floors (Weegli's 1 health, the Test's default 30% yield). True: CR's floors are skipped (the
        // handler owns the floor; Weegli's floor still holds, see WeegliFloorHolds).
        virtual bool OnDamageTaken(BlyCrewAI& /*ai*/, Unit* /*attacker*/, uint32& /*damage*/,
            DamageEffectType /*type*/, SpellSchoolMask /*school*/) { return false; }
        virtual void OnHealReceived(BlyCrewAI& /*ai*/, Unit* /*healer*/, uint32& /*heal*/) { }
        virtual void OnSpellHit(BlyCrewAI& /*ai*/, Unit* /*caster*/, SpellInfo const* /*spell*/) { }
        virtual void OnDied(BlyCrewAI& /*ai*/, Unit* /*killer*/) { }
        // Before CR's evade. True: the handler evaded (or refused to) itself. CR's default in Boss mode reports a
        // crew wipe (SetData(DATA_CREW_FIGHT, NOT_STARTED)) after the base evade.
        virtual bool OnEvade(BlyCrewAI& /*ai*/, CreatureAI::EvadeReason /*why*/) { return false; }
        // From Reset (also inside every evade): undo per-pull state.
        virtual void OnReset(BlyCrewAI& /*ai*/) { }
        // A movement of the member ended (CR's own ids are handled first; a handler's ids are >= kPointHandlerBase).
        virtual void OnMovementInform(BlyCrewAI& /*ai*/, uint32 /*type*/, uint32 /*id*/) { }
        // Where the member stands for `spot` in this mode; nullopt: CR's point (SpotPoint). E.g. D4b's crew
        // placement on the Stair (PY5) answers CrewSpot::Stair.
        virtual std::optional<Position> RestSpot(BlyCrewAI& /*ai*/, CrewSpot /*spot*/) { return std::nullopt; }
    };

    using CrewModeHandlerFactory = std::function<std::unique_ptr<CrewModeHandler>(BlyCrewAI& ai)>;

    // From the owner's AddSC_ (before any map loads). `members`: the CrewMember bits it applies to (a later call for
    // the same mode and member replaces the earlier one).
    void RegisterCrewModeHandler(CrewMode mode, CrewModeHandlerFactory factory,
        uint32 members = ZulFarrakRework::kCrewAll);
    bool HasCrewModeHandler(CrewMode mode, uint32 member);

    // Bly's fight start, after his gossip set the path (DATA_CREW_PATH 1 or 2). CR's default: on the betrayal the stock
    // lines (0 at 1.5 s, 1 three seconds later), then SetData(DATA_CREW_FIGHT, IN_PROGRESS) (the instance turns the
    // four to Boss) and the four attack the chooser (else the nearest player); on the Test the same after 3 s with no
    // line. A starter set here replaces all of that (D5); it must send IN_PROGRESS itself.
    using CrewFightStarter = std::function<void(Creature* bly, Player* chooser, uint32 path)>;
    void SetCrewFightStarter(CrewFightStarter starter);

    // ----------------------------------------------------------------------------------------------------------------
    // The AI every crew member runs (one registered script per member: npc_bly_crew_bly, _raven, _oro, _weegli,
    // _murta). Never subclassed by another WP: plug a CrewModeHandler in instead.
    // ----------------------------------------------------------------------------------------------------------------
    struct BlyCrewAI : public ScriptedAI
    {
        BlyCrewAI(Creature* creature, uint32 member);
        ~BlyCrewAI() override;

        // --- engine hooks (CR's; handlers see them through CrewModeHandler) ---
        void InitializeAI() override;
        void JustRespawned() override;
        void Reset() override;
        void DoAction(int32 action) override;
        void UpdateAI(uint32 diff) override;
        void JustEngagedWith(Unit* who) override;
        void AttackStart(Unit* who) override;
        void EnterEvadeMode(EvadeReason why = EVADE_REASON_OTHER) override;
        void JustReachedHome() override;
        void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask school) override;
        void HealReceived(Unit* healer, uint32& heal) override;
        void SpellHit(Unit* caster, SpellInfo const* spell) override;
        void JustDied(Unit* killer) override;
        void MovementInform(uint32 type, uint32 id) override;
        void PathEndReached(uint32 pathId) override;
        void sGossipHello(Player* player) override;
        void sGossipSelect(Player* player, uint32 menuId, uint32 gossipListId) override;

        // --- what a handler or a WP reads ---
        Creature* Me() const { return me; }
        InstanceScript* Instance() const;
        uint32 Member() const { return _member; }
        bool IsWeegli() const { return _member == ZulFarrakRework::CREW_WEEGLI; }
        // The mode this AI applied last (the instance's DATA_CREW_MODE_BASE + member, read at every change).
        CrewMode Mode() const { return _mode; }
        // The rest spot the member was last sent to.
        CrewSpot Spot() const { return _spot; }
        PrisonerState Prisoner() const { return _prisoner; }
        DoorWalk Door() const { return _door; }
        bool ArrivedAtPool() const { return _atPool; }
        // Bly: the player who chose the path (empty before; cleared at a crew wipe).
        ObjectGuid Chooser() const { return _chooser; }

        // --- what a handler or a WP does ---
        // Walk (or run) to `pos`; the home position moves there too (an evade comes back to it). `pointId` >=
        // kPointHandlerBase for a handler's own moves (forwarded to OnMovementInform). A walk that never arrives is
        // finished by a teleport after Tune::kWalkTimeoutMs.
        void WalkTo(Position const& pos, uint32 pointId, bool run);
        // Teleport to `pos` (dropped to the ground) and make it home.
        void PlaceAt(Position const& pos);
        // Send the member to a rest spot of this mode (the handler's RestSpot, else SpotPoint): travel as TravelTo
        // says, or a teleport with `place`.
        void GoToSpot(CrewSpot spot, bool place);
        // The stock kit of this member for one tick (casts on its timers, then melee): what CR runs in Ally and Boss
        // when the handler's OnUpdate returns false. Needs a victim (UpdateVictim first). ResetKit re-arms the timers.
        void RunKit(uint32 diff);
        void ResetKit();
        // CreatureAI::UpdateVictim for a handler's OnUpdate (it is protected on the AI): false = no victim.
        bool UpdateCrewVictim() { return UpdateVictim(); }
        // The position of `spot` for this member in this mode (the handler's RestSpot, else SpotPoint).
        Position SpotPosition(CrewSpot spot);
        // Out of every fight now: combat, threat and the victim dropped (no evade, no walk home).
        void StopFighting();

        // The Block (D4a). Take: a Caged fighter is torn from the cage and jumps to `chain` (mode Prisoner), then
        // rooted and kneeling there (Chained). Spare: back into the cage (Returning, then mode Caged). Execute: killed
        // by `executioner` (the instance counts the Offering / Blood Price). Each returns false when refused.
        bool TakePrisoner(Position const& chain);
        bool SparePrisoner();
        bool ExecutePrisoner(Unit* executioner);

    protected:
        // The member's own stock kit (BlyCrew.cpp's per-member classes).
        virtual void KitReset() { }
        virtual void KitUpdate(uint32 /*diff*/) { }
        EventMap _kit;

    private:
        CrewModeHandler* Handler(CrewMode mode);
        CrewModeHandler* Handler() { return Handler(_mode); }
        void Init();
        void ApplyLook();
        void ChangeMode(CrewMode mode);
        void EnterMode(CrewMode from, bool placed);
        void LeaveMode(CrewMode to);
        void OnStageAction();
        void OnFightAction();
        void OnPoolReset();
        void ReachedSpot();
        void OnFlowEvent(uint32 eventId);
        void SetPrisoner(PrisonerState state, char const* how);
        void FinishPrisonerMove(uint32 pointId);
        bool PathsOffered() const;
        void CheckYields();
        void StartFight();
        void StartDoorWalk();
        void ArriveAtDoor();
        void PlantBarrel();
        void LightFuse();
        void DoorBlown();
        void AbortDoorWalk();
        void DepartToPool();
        void ArriveAtPool();
        void LeaveForGood(bool now);
        void Kneel(bool kneel);

        uint32 _member;
        CrewMode _mode = CrewMode::Caged;
        CrewSpot _spot = CrewSpot::None;
        PrisonerState _prisoner = PrisonerState::Free;
        DoorWalk _door = DoorWalk::Idle;
        Position _walkTarget;
        Position _chain;
        bool _initPending = false;
        bool _madeActive = false;
        bool _atPool = false;
        bool _departing = false;
        bool _kneeling = false;
        bool _yieldPending = false;
        bool _starting = false;
        uint32 _walkId = 0;
        ObjectGuid _chooser;
        EventMap _flow;
        std::array<std::unique_ptr<CrewModeHandler>, ZulFarrakRework::kCrewModeCount> _handlers;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The crew by member (rule 28: the only way other WPs touch them)
    // ----------------------------------------------------------------------------------------------------------------
    // The member's crew AI (nullptr: not in the world, dead with its AI off, or not a crew member).
    BlyCrewAI* CrewAI(Creature* creature);
    BlyCrewAI* CrewAI(InstanceScript* instance, uint32 member);

    // Walk a member to `pos` (BlyCrewAI::WalkTo). False when the member is not there or dead.
    bool MoveCrew(InstanceScript* instance, uint32 member, Position const& pos, uint32 pointId, bool run);
    // A script heal (no spell; healing never reaches an NPC through the registry, rule 29). Returns the health added.
    uint32 HealCrew(Creature* crew, Unit* healer, uint32 amount);
    // A script hit (Unit::DealDamage: the AI's floors and the handler's OnDamageTaken apply). Returns the health taken.
    uint32 DamageCrew(Creature* crew, Unit* attacker, uint32 amount,
        SpellSchoolMask school = SPELL_SCHOOL_MASK_NORMAL, SpellInfo const* spell = nullptr);
    // Kill a member (D4b's Blood Offering, D7Ha's devoured crew). Weegli is refused while his floor holds.
    bool KillCrew(Creature* crew, Unit* killer);

    // The Block (D4a): the fighters it may take now (CrewMember bits: alive, Caged, not a prisoner; never Weegli), the
    // member chained or on the way (if any), and the machine's three calls by member.
    uint32 PrisonerCandidates(InstanceScript* instance);
    std::optional<uint32> CurrentPrisoner(InstanceScript* instance);
    bool TakePrisoner(InstanceScript* instance, uint32 member, Position const& chain);
    bool SparePrisoner(InstanceScript* instance, uint32 member);
    bool ExecutePrisoner(InstanceScript* instance, uint32 member, Unit* executioner);
}

#endif
