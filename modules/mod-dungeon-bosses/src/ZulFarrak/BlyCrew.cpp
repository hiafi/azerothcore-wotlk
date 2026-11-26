/*
 * mod-dungeon-bosses, Zul'Farrak CR: Sergeant Bly's crew (BlyCrew.h). Bound by the S0 rev (npc_bly_crew_bly, _raven,
 * _oro, _weegli, _murta in place of npc_sergeant_bly, npc_weegli_blastfuse and the SmartAI of 7605, 7606, 7608).
 *
 * One AI per member on BlyCrewAI: the mode the instance stores is applied here (faction, react state, gossip flag,
 * rest spot), each member runs its stock kit in Ally and Boss, Murta heals by script, Weegli holds at 1 health until
 * the pool and walks to the End Door, the Block's prisoner machine, Bly's gossip and the default fight start and yield.
 * Later WPs plug CrewModeHandlers in (BlyCrew.h); `.dbtest zf band` tests it.
 *
 * Mirrored stock code (AGENTS.md credit rule): the stair, descent and gather walks (instance_zulfarrak.cpp
 * MoveNPCIfAlive), Bly's betrayal sequence and gossip gates (npc_sergeant_bly), Weegli's door walk
 * (npc_weegli_blastfuse: the spot, the plant 2 s after arriving, the escape path) and the kits' timers:
 * c9315e3ec moostigre <moostigre@proton.me> (#27731), 048025ceb UltraNix <80540499+UltraNix@users.noreply.github.com>
 * (#7855).
 */

#include "BlyCrew.h"
#include "BlyCrewLogic.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GossipDef.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MapReference.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedGossip.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakTestCommand.h"
#include <algorithm>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;

namespace ZfCrew
{
    namespace
    {
        // The flows every member may run (the kits use their own EventMap, _kit).
        enum FlowEvents : uint32
        {
            EVENT_WALK_TIMEOUT = 1,     // a walk that never arrived: teleport and arrive
            EVENT_PRISONER_TIMEOUT,     // a prisoner's jump that never landed
            EVENT_BETRAYAL_LINE_0,      // Bly: stock line 0
            EVENT_BETRAYAL_LINE_1,      // Bly: stock line 1
            EVENT_FIGHT_START,          // Bly: the fight starts (DATA_CREW_FIGHT IN_PROGRESS)
            EVENT_CHECK_YIELDS,         // the default Test end: all four yielded or dead
            EVENT_PLANT,                // Weegli: the barrel goes down
            EVENT_FUSE,                 // Weegli: the fuse burnt out
            EVENT_ESCAPE_DESPAWN,       // Weegli: gone even if his escape path never ends
            EVENT_STAND,                // Weegli: stands up after kneeling at 1 health
            EVENT_DEPART,               // the Test path: Band's Escape toward the pool
            EVENT_ARRIVE_POOL,          // the Test path: at the shore
            EVENT_GONE_DESPAWN,         // a Gone fighter still alive
        };

        // Stock gossip (zulfarrak.cpp): menu 941 texts and option, menu 940 texts.
        uint32 constexpr kTextBlyCaged = 1515;
        uint32 constexpr kTextBlyBusy = 1516;
        uint32 constexpr kTextBlyPaths = 1517;
        uint32 constexpr kTextWeegliCaged = 1511;
        uint32 constexpr kTextWeegliBusy = 1513;
        uint32 constexpr kTextWeegliAfter = 1514;
        uint32 constexpr kGossipActionBetrayal = GOSSIP_ACTION_INFO_DEF + 1;
        uint32 constexpr kGossipActionTest = GOSSIP_ACTION_INFO_DEF + 2;
        char constexpr kGossipBetrayal[] =
            "That's it!  I'm tired of helping you out.  It's time we settled things on the battlefield!";
        char constexpr kGossipTest[] = "Put us to your test, Bly. Your whole crew against us, until one side yields.";
        char constexpr kGossipTestConfirm[] = "Bly's Test: the crew fight you and each yields at 30% health. Win, and "
            "all five join you at the sacred pool, where Gahz'rilla waits stronger than ever. Begin the Test?";

        // R-1-FW M4: a player the crew fight may engage: alive, not a GM, on the plaza (rule 5: never a corpse runner
        // or a player up the stair), not feigning death, seen by `me` (a vanished rogue is not) and attackable.
        bool CrewFightTarget(Creature* me, Player* player)
        {
            return player && player->IsAlive() && !player->IsGameMaster() && player->IsInMap(me)
                && !player->HasUnitFlag2(UNIT_FLAG2_FEIGN_DEATH)
                && PlazaArena().Contains(DungeonKit::PlaneOf(player), player->GetPositionZ())
                && me->CanSeeOrDetect(player) && me->IsValidAttackTarget(player);
        }

        // The crew fight's players on the plaza, nearest to `me` first.
        std::vector<Player*> CrewFightTargets(Creature* me)
        {
            std::vector<Player*> out;
            for (MapReference const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource(); CrewFightTarget(me, player))
                    out.push_back(player);
            std::sort(out.begin(), out.end(), [me](Player* a, Player* b)
                { return me->GetExactDist2dSq(a) < me->GetExactDist2dSq(b); });
            return out;
        }

        using FactoryTable = std::array<std::array<CrewModeHandlerFactory, kCrewCount>, kCrewModeCount>;

        FactoryTable& Factories()
        {
            static FactoryTable factories;
            return factories;
        }

        CrewFightStarter& Starter()
        {
            static CrewFightStarter starter;
            return starter;
        }

        Milliseconds Ms(uint32 ms)
        {
            return Milliseconds(ms);
        }

        Milliseconds Rand(Window w)
        {
            return Milliseconds(InWindow(w, float(rand_norm())));
        }

        Position ToPosition(Point3 const& p)
        {
            return Position(p.x, p.y, p.z, p.o);
        }

        void Log(char const* mechanic, std::string const& detail = {})
        {
            DungeonKit::LogMechanic(kLogDungeon, "crew", mechanic, detail);
        }

        // Weegli's barrel (spell 10772 summons GO 141612 as a wild object: not owned by him, so found and despawned;
        // no DB spawn of 141612 exists on map 209).
        void RemoveBarrel(Creature* me)
        {
            if (GameObject* barrel = me->FindNearestGameObject(GO_WEEGLIS_BARREL, 15.f))
                barrel->DespawnOrUnsummon();
        }

        // A point 2.5 yd in front of the Executioner (a GM's prisoner test; D4a passes its own spot).
        Position GmChainSpot(InstanceScript* instance)
        {
            Point3 at = kExecutionerSpawn;
            if (instance)
                if (Creature* executioner = instance->GetCreature(kGuidExecutioner))
                    at = { executioner->GetPositionX(), executioner->GetPositionY(), executioner->GetPositionZ(),
                        executioner->GetOrientation() };
            float constexpr reach = 2.5f;
            return Position(at.x + reach * std::cos(at.o), at.y + reach * std::sin(at.o), at.z, at.o + float(M_PI));
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Registry
    // ----------------------------------------------------------------------------------------------------------------
    void RegisterCrewModeHandler(CrewMode mode, CrewModeHandlerFactory factory, uint32 members)
    {
        if (uint32(mode) >= kCrewModeCount)
            return;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (members & CrewBit(m))
                Factories()[uint32(mode)][m] = factory;
    }

    bool HasCrewModeHandler(CrewMode mode, uint32 member)
    {
        return uint32(mode) < kCrewModeCount && member < kCrewCount && Factories()[uint32(mode)][member];
    }

    void SetCrewFightStarter(CrewFightStarter starter)
    {
        Starter() = std::move(starter);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BlyCrewAI: setup, modes
    // ----------------------------------------------------------------------------------------------------------------
    BlyCrewAI::BlyCrewAI(Creature* creature, uint32 member) : ScriptedAI(creature), _member(member) { }

    BlyCrewAI::~BlyCrewAI() = default;

    InstanceScript* BlyCrewAI::Instance() const
    {
        return me->GetInstanceScript();
    }

    CrewModeHandler* BlyCrewAI::Handler(CrewMode mode)
    {
        uint32 const index = uint32(mode);
        if (index >= kCrewModeCount || _member >= kCrewCount)
            return nullptr;
        if (!_handlers[index])
            if (CrewModeHandlerFactory const& factory = Factories()[index][_member])
                _handlers[index] = factory(*this);
        return _handlers[index].get();
    }

    void BlyCrewAI::InitializeAI()
    {
        Init();
    }

    void BlyCrewAI::JustRespawned()
    {
        Init();
    }

    // A create, a respawn or a reload: the mode the instance holds now; the member is placed on its first tick (made
    // an active object until then, so a member far from every player, e.g. a reload with the crew at the pool, is
    // placed anyway).
    void BlyCrewAI::Init()
    {
        _flow.Reset();
        _kit.Reset();
        _spot = CrewSpot::None;
        _prisoner = PrisonerState::Free;
        _door = DoorWalk::Idle;
        _atPool = false;
        _departing = false;
        _kneeling = false;
        _yieldPending = false;
        _starting = false;
        _walkId = 0;
        _chooser.Clear();
        _mode = GetCrewMode(Instance(), _member);
        if (me->isDead())
            return;
        _initPending = true;
        if (!me->isActiveObject())
        {
            me->setActive(true);
            _madeActive = true;
        }
        Reset();
    }

    void BlyCrewAI::ApplyLook()
    {
        me->SetFaction(FactionFor(_mode));
        // Weegli never fights (his barrels are D4b's); his floor keeps him standing.
        me->SetReactState(FightsIn(_mode) && !IsWeegli() ? REACT_AGGRESSIVE : REACT_PASSIVE);
        if (GossipIn(_member, _mode))
            me->SetNpcFlag(UNIT_NPC_FLAG_GOSSIP);
        else
            me->RemoveNpcFlag(UNIT_NPC_FLAG_GOSSIP);
    }

    void BlyCrewAI::Reset()
    {
        ApplyLook();
        ResetKit();
        if (_kneeling && _prisoner != PrisonerState::Chained)
            Kneel(false);
        if (CrewModeHandler* handler = Handler())
            handler->OnReset(*this);
    }

    void BlyCrewAI::ChangeMode(CrewMode mode)
    {
        if (_initPending)
        {
            _mode = mode;       // the first tick enters it
            ApplyLook();
            return;
        }
        if (mode == _mode)
        {
            ApplyLook();
            return;
        }
        CrewMode const from = _mode;
        if (CrewModeHandler* handler = Handler(from))
            handler->OnLeave(*this, mode);
        LeaveMode(mode);
        _mode = mode;
        ApplyLook();
        EnterMode(from, false);
    }

    void BlyCrewAI::LeaveMode(CrewMode /*to*/)
    {
        if (_mode == CrewMode::Prisoner && _prisoner != PrisonerState::Free && _prisoner != PrisonerState::Executed)
        {
            _flow.CancelEvent(EVENT_PRISONER_TIMEOUT);
            me->SetControlled(false, UNIT_STATE_ROOT);
            Kneel(false);
            SetPrisoner(PrisonerNext(_prisoner, PrisonerEvent::Reset), "mode");
        }
        if (_mode == CrewMode::Boss)
            _yieldPending = false;
    }

    // `placed`: a create, a respawn or a reload (teleport to the spot); else the member travels as stock.
    void BlyCrewAI::EnterMode(CrewMode from, bool placed)
    {
        if (!FightsIn(_mode) && (me->IsEngaged() || me->IsInCombat()))
            StopFighting();
        InstanceScript* instance = Instance();
        uint32 const stage = instance ? instance->GetData(DATA_PYRAMID_STAGE) : 0;

        switch (_mode)
        {
            case CrewMode::Caged:
            case CrewMode::Gather:
            case CrewMode::Yielded:
                GoToSpot(RestSpotFor(_mode, stage), placed);
                if (_mode == CrewMode::Yielded && !HasCrewModeHandler(CrewMode::Boss, _member))
                    _flow.RescheduleEvent(EVENT_CHECK_YIELDS, Ms(0));
                break;
            case CrewMode::Prisoner:
                if (placed)     // never saved: a GM's mode on a fresh create; back into the cage
                    GoToSpot(CrewSpot::Cage, true);
                break;
            case CrewMode::Ally:
                GoToSpot(RestSpotFor(_mode, stage), placed);
                break;
            case CrewMode::Boss:
                _yieldPending = false;
                ResetKit();
                if (placed)
                    GoToSpot(CrewSpot::Gather, true);
                break;
            case CrewMode::PoolAlly:
                if (placed)
                    GoToSpot(CrewSpot::Pool, true);
                else if (IsWeegli() && instance && instance->GetData(DATA_END_DOOR) != DungeonKit::State::Done)
                    StartDoorWalk();
                else
                    _flow.RescheduleEvent(EVENT_DEPART, Ms(Tune::kPoolDepartDelayMs));
                break;
            case CrewMode::Gone:
                if (!IsWeegli())
                {
                    _flow.RescheduleEvent(EVENT_GONE_DESPAWN, Ms(placed ? 0 : Tune::kGoneDespawnMs));
                    break;
                }
                if (placed)
                {
                    LeaveForGood(true);
                    break;
                }
                if (_door == DoorWalk::Planted)
                    LightFuse();
                else if (_door == DoorWalk::Idle)
                    StartDoorWalk();
                break;
            default:
                break;
        }

        if (CrewModeHandler* handler = Handler())
            handler->OnEnter(*this, from);
    }

    void BlyCrewAI::DoAction(int32 action)
    {
        if (action == ACTION_ZF_CREW_MODE)
        {
            ChangeMode(GetCrewMode(Instance(), _member));
            return;
        }
        if (CrewModeHandler* handler = Handler(); handler && handler->OnAction(*this, action))
            return;
        switch (action)
        {
            case ACTION_ZF_PYRAMID_STAGE:
                OnStageAction();
                break;
            case ACTION_ZF_CREW_FIGHT:
                OnFightAction();
                break;
            case ACTION_ZF_POOL_RESET:
                OnPoolReset();
                break;
            default:
                break;
        }
    }

    // A stage began, was won or was lost: an Ally member follows the stage (the stair, then its foot).
    void BlyCrewAI::OnStageAction()
    {
        if (_initPending || _mode != CrewMode::Ally)
            return;
        InstanceScript* instance = Instance();
        GoToSpot(RestSpotFor(_mode, instance ? instance->GetData(DATA_PYRAMID_STAGE) : 0), false);
    }

    // Slot 6 changed (D5's fight, or CR's default start / end).
    void BlyCrewAI::OnFightAction()
    {
        InstanceScript* instance = Instance();
        if (!instance)
            return;
        uint32 const slot = instance->GetData(DATA_CREW_FIGHT);
        uint32 const path = instance->GetData(DATA_CREW_PATH);
        if (slot == DungeonKit::State::NotStarted)
        {
            _starting = false;
            _chooser.Clear();
            _yieldPending = false;
            _flow.CancelEvent(EVENT_BETRAYAL_LINE_0);
            _flow.CancelEvent(EVENT_BETRAYAL_LINE_1);
            _flow.CancelEvent(EVENT_FIGHT_START);
            _flow.CancelEvent(EVENT_CHECK_YIELDS);
            if (IsWeegli())
                AbortDoorWalk();
            return;
        }
        if (!IsWeegli())
            return;
        if (slot == DungeonKit::State::InProgress && path == CREW_PATH_BETRAYAL)
            StartDoorWalk();
        else if (slot == DungeonKit::State::Done && _door == DoorWalk::Planted)
            LightFuse();
    }

    // A pool wipe: the living back on their spots at full health (the respawned are placed by Init).
    void BlyCrewAI::OnPoolReset()
    {
        if (_initPending || _mode != CrewMode::PoolAlly)
            return;
        StopFighting();
        Kneel(false);
        me->SetFullHealth();
        if (_atPool)
        {
            _spot = CrewSpot::Pool;
            WalkTo(SpotPosition(CrewSpot::Pool), POINT_CREW_SPOT, true);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Movement
    // ----------------------------------------------------------------------------------------------------------------
    Position BlyCrewAI::SpotPosition(CrewSpot spot)
    {
        if (CrewModeHandler* handler = Handler())
            if (std::optional<Position> pos = handler->RestSpot(*this, spot))
                return *pos;
        return ToPosition(SpotPoint(spot, _member));
    }

    void BlyCrewAI::WalkTo(Position const& pos, uint32 pointId, bool run)
    {
        me->SetWalk(!run);
        me->SetHomePosition(pos);
        _walkId = pointId;
        _walkTarget = pos;
        me->GetMotionMaster()->MovePoint(pointId, pos);
        _flow.RescheduleEvent(EVENT_WALK_TIMEOUT, Ms(Tune::kWalkTimeoutMs));
    }

    void BlyCrewAI::PlaceAt(Position const& pos)
    {
        float x = pos.GetPositionX();
        float y = pos.GetPositionY();
        float z = pos.GetPositionZ();
        me->UpdateGroundPositionZ(x, y, z);
        me->SetHomePosition(x, y, z, pos.GetOrientation());
        me->GetMotionMaster()->Clear();
        me->NearTeleportTo(x, y, z, pos.GetOrientation());
        _flow.CancelEvent(EVENT_WALK_TIMEOUT);
        _walkId = 0;
    }

    void BlyCrewAI::GoToSpot(CrewSpot spot, bool place)
    {
        if (spot == CrewSpot::None)
            return;
        Position const pos = SpotPosition(spot);
        CrewSpot const previous = _spot;
        float const distance = me->GetExactDist(&pos);
        bool const there = distance <= Tune::kPlaceSnapYd;
        if (spot == previous && !place && (there || _walkId == POINT_CREW_SPOT || _departing))
            return;     // already there, or on the way
        _spot = spot;

        if (place || there)
        {
            if (there)
                me->SetHomePosition(pos);
            else
                PlaceAt(pos);
            ReachedSpot();
            return;
        }
        switch (TravelTo(spot))
        {
            case SpotTravel::Jump:
                me->SetHomePosition(pos);
                _walkId = POINT_CREW_SPOT;
                _walkTarget = pos;
                me->GetMotionMaster()->Clear();
                me->GetMotionMaster()->MoveJump(pos, Tune::kPrisonerJumpSpeedXY, Tune::kPrisonerJumpSpeedZ,
                    POINT_CREW_SPOT);
                _flow.RescheduleEvent(EVENT_WALK_TIMEOUT, Ms(Tune::kPrisonerMoveTimeoutMs));
                break;
            case SpotTravel::Depart:
                DepartToPool();
                break;
            default:
                // Stock (instance_zulfarrak.cpp PYRAMID_PRE_WAVE_3): Bly says "Let's move forward!" going down.
                if (_member == CREW_BLY && previous == CrewSpot::Stair && spot == CrewSpot::Descent)
                    Talk(SAY_BLY_FORWARD);
                WalkTo(pos, POINT_CREW_SPOT, false);
                break;
        }
    }

    void BlyCrewAI::ReachedSpot()
    {
        _walkId = 0;
        _flow.CancelEvent(EVENT_WALK_TIMEOUT);
        if (me->GetHomePosition().GetOrientation() != 0.f && !me->IsEngaged())
            me->SetFacingTo(me->GetHomePosition().GetOrientation());
        InstanceScript* instance = Instance();
        switch (_spot)
        {
            case CrewSpot::Stair:
                // Stock (Weegli's arrival at the stair): "Oh no! Here they come!" while the waves run.
                if (IsWeegli() && instance && instance->GetData(DATA_PYRAMID_RUNNING)
                    && instance->GetData(DATA_PYRAMID_STAGE) == PYRAMID_STAGE_STAIR)
                    Talk(SAY_WEEGLI_OH_NO);
                break;
            case CrewSpot::Pool:
                ArriveAtPool();
                break;
            default:
                break;
        }
    }

    void BlyCrewAI::MovementInform(uint32 type, uint32 id)
    {
        if (type == POINT_MOTION_TYPE || type == EFFECT_MOTION_TYPE)
        {
            switch (id)
            {
                case POINT_CREW_SPOT:
                    if (_walkId == POINT_CREW_SPOT)
                        ReachedSpot();
                    break;
                case POINT_PRISONER_CHAIN:
                case POINT_PRISONER_CAGE:
                    FinishPrisonerMove(id);
                    break;
                case POINT_WEEGLI_DOOR:
                    if (_walkId == POINT_WEEGLI_DOOR)
                        ArriveAtDoor();
                    break;
                default:
                    if (id >= kPointHandlerBase && _walkId == id)
                    {
                        _walkId = 0;
                        _flow.CancelEvent(EVENT_WALK_TIMEOUT);
                    }
                    break;
            }
        }
        if (CrewModeHandler* handler = Handler())
            handler->OnMovementInform(*this, type, id);
    }

    // An evade (or a walk the fight broke off) came home: home is the spot or the door.
    void BlyCrewAI::JustReachedHome()
    {
        if (_walkId == POINT_CREW_SPOT)
            ReachedSpot();
        else if (_walkId == POINT_WEEGLI_DOOR)
            ArriveAtDoor();
    }

    void BlyCrewAI::PathEndReached(uint32 pathId)
    {
        if (IsWeegli() && pathId == kWeegliEscapePath && _door == DoorWalk::Leaving)
            LeaveForGood(true);
    }

    void BlyCrewAI::StopFighting()
    {
        me->CombatStop(true);
        me->GetThreatMgr().ClearAllThreat();
        if (me->GetMotionMaster()->GetCurrentMovementGeneratorType() == CHASE_MOTION_TYPE)
            me->GetMotionMaster()->Clear();
    }

    void BlyCrewAI::Kneel(bool kneel)
    {
        _kneeling = kneel;
        me->SetStandState(kneel ? UNIT_STAND_STATE_KNEEL : UNIT_STAND_STATE_STAND);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The tick
    // ----------------------------------------------------------------------------------------------------------------
    void BlyCrewAI::UpdateAI(uint32 diff)
    {
        if (_initPending)
        {
            _initPending = false;
            EnterMode(_mode, true);
            if (_madeActive)
            {
                _madeActive = false;
                me->setActive(false);
            }
        }

        _flow.Update(diff);
        while (uint32 const eventId = _flow.ExecuteEvent())
            OnFlowEvent(eventId);

        if (_yieldPending)
        {
            _yieldPending = false;
            if (_mode == CrewMode::Boss)
            {
                Log("yield", kCrewNames[_member]);
                SetCrewMode(Instance(), _member, CrewMode::Yielded);
            }
        }

        if (CrewModeHandler* handler = Handler(); handler && handler->OnUpdate(*this, diff))
            return;
        if (!FightsIn(_mode) || IsWeegli())
            return;
        if (!UpdateVictim())
            return;
        RunKit(diff);
    }

    void BlyCrewAI::OnFlowEvent(uint32 eventId)
    {
        switch (eventId)
        {
            case EVENT_WALK_TIMEOUT:
                if (!_walkId)
                    break;
                if (me->IsEngaged())
                {
                    // The fight broke the walk off: the evade brings the member home (the target) afterwards.
                    _flow.ScheduleEvent(EVENT_WALK_TIMEOUT, Ms(Tune::kWalkTimeoutMs));
                    break;
                }
                {
                    uint32 const id = _walkId;
                    Log("walk-timeout", Acore::StringFormat("{} point={}", kCrewNames[_member], id));
                    PlaceAt(_walkTarget);
                    _walkId = id;
                    MovementInform(POINT_MOTION_TYPE, id);
                    _walkId = 0;
                }
                break;
            case EVENT_PRISONER_TIMEOUT:
                if (_prisoner == PrisonerState::Torn)
                {
                    PlaceAt(_chain);
                    FinishPrisonerMove(POINT_PRISONER_CHAIN);
                }
                else if (_prisoner == PrisonerState::Returning)
                {
                    PlaceAt(ToPosition(kCrewSpawns[_member]));
                    FinishPrisonerMove(POINT_PRISONER_CAGE);
                }
                break;
            case EVENT_BETRAYAL_LINE_0:
                Talk(SAY_BLY_BETRAYAL_1, ObjectAccessor::GetPlayer(*me, _chooser));
                _flow.ScheduleEvent(EVENT_BETRAYAL_LINE_1, Ms(Tune::kBetrayalLine1Ms));
                break;
            case EVENT_BETRAYAL_LINE_1:
                Talk(SAY_BLY_BETRAYAL_2, ObjectAccessor::GetPlayer(*me, _chooser));
                _flow.ScheduleEvent(EVENT_FIGHT_START, Ms(Tune::kBetrayalHostileMs));
                break;
            case EVENT_FIGHT_START:
                StartFight();
                break;
            case EVENT_CHECK_YIELDS:
                CheckYields();
                break;
            case EVENT_PLANT:
                PlantBarrel();
                break;
            case EVENT_FUSE:
                DoorBlown();
                break;
            case EVENT_ESCAPE_DESPAWN:
                LeaveForGood(true);
                break;
            case EVENT_STAND:
                if (_kneeling && _prisoner != PrisonerState::Chained)
                    Kneel(false);
                break;
            case EVENT_DEPART:
                DepartToPool();
                break;
            case EVENT_ARRIVE_POOL:
                _departing = false;
                me->SetFullHealth();
                _spot = CrewSpot::Pool;
                PlaceAt(SpotPosition(CrewSpot::Pool));
                ReachedSpot();
                break;
            case EVENT_GONE_DESPAWN:
                if (_mode == CrewMode::Gone && me->IsAlive())
                {
                    Log("gone", kCrewNames[_member]);
                    me->DespawnOrUnsummon();
                }
                break;
            default:
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Combat hooks
    // ----------------------------------------------------------------------------------------------------------------
    void BlyCrewAI::AttackStart(Unit* who)
    {
        if (!FightsIn(_mode) || IsWeegli() || _initPending)
            return;
        ScriptedAI::AttackStart(who);
    }

    void BlyCrewAI::JustEngagedWith(Unit* who)
    {
        if (CrewModeHandler* handler = Handler())
            handler->OnEngage(*this, who);
    }

    void BlyCrewAI::EnterEvadeMode(EvadeReason why)
    {
        // R-1-FW M4: one fighter's emptied threat list (its target died, fed or vanished) or a lost path no longer
        // wipes the fight while the group still fights on the plaza: it turns to the nearest plaza player instead.
        InstanceScript* instance = Instance();
        bool const running = instance && instance->GetData(DATA_CREW_FIGHT) == DungeonKit::State::InProgress;
        std::vector<Player*> const targets = (_mode == CrewMode::Boss && running && me->IsAlive())
            ? CrewFightTargets(me) : std::vector<Player*>{};
        CrewEvade const verdict = CrewEvadeVerdict(_mode == CrewMode::Boss, running, why == EVADE_REASON_NO_HOSTILES,
            !targets.empty(), OtherFighterEngaged());
        if (verdict == CrewEvade::Reengage)
        {
            Player* target = targets.front();
            Log("fight-reengage", Acore::StringFormat("{} reason={} target={}", kCrewNames[_member], uint32(why),
                target->GetName()));
            me->GetThreatMgr().AddThreat(target, 0.f, nullptr, true, true);
            ScriptedAI::AttackStart(target);
            return;
        }

        if (CrewModeHandler* handler = Handler(); handler && handler->OnEvade(*this, why))
            return;
        ScriptedAI::EnterEvadeMode(why);
        if (verdict != CrewEvade::Wipe)
            return;
        // Nobody left to fight on the plaza (or the last fighter cannot reach anyone): the group is gone; the
        // instance restores all five.
        Log("fight-wipe", Acore::StringFormat("evade={} reason={}", kCrewNames[_member], uint32(why)));
        instance->SetData(DATA_CREW_FIGHT, DungeonKit::State::NotStarted);
    }

    // Another Boss-mode fighter, alive, fighting a living plaza player (R-1-FW M4).
    bool BlyCrewAI::OtherFighterEngaged() const
    {
        InstanceScript* instance = Instance();
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            if (m == _member || !(CrewBit(m) & kCrewFighters))
                continue;
            BlyCrewAI* other = CrewAI(instance, m);
            if (!other || other->_mode != CrewMode::Boss || !other->me->IsAlive() || !other->me->IsEngaged())
                continue;
            Player* victim = other->me->GetVictim() ? other->me->GetVictim()->ToPlayer() : nullptr;
            if (victim && CrewFightTarget(other->me, victim))
                return true;
        }
        return false;
    }

    void BlyCrewAI::DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask school)
    {
        CrewModeHandler* handler = Handler();
        bool const handled = handler && handler->OnDamageTaken(*this, attacker, damage, type, school);

        // Section 7 #13 A: Weegli cannot die until he stands at the pool; at 1 health he kneels for a while.
        if (IsWeegli() && WeegliFloorHolds(_mode, _atPool))
        {
            uint32 const allowed = FlooredDamage(me->GetHealth(), damage, 1);
            if (allowed < damage)
            {
                damage = allowed;
                if (!_kneeling)
                {
                    Kneel(true);
                    Log("weegli-floor", Acore::StringFormat("mode={}", kCrewModeNames[uint32(_mode)]));
                }
                _flow.RescheduleEvent(EVENT_STAND, Ms(Tune::kWeegliStandMs));
            }
            return;
        }
        if (handled || _mode != CrewMode::Boss)
            return;

        // The Test's default yield (SP BC11): the floor at 30%, the yield on the next tick (never inside DealDamage).
        InstanceScript* instance = Instance();
        if (!instance || instance->GetData(DATA_CREW_PATH) != CREW_PATH_TEST)
            return;
        uint32 const floor = PctOf(me->GetMaxHealth(), Tune::kYieldPct);
        damage = FlooredDamage(me->GetHealth(), damage, floor);
        if (me->GetHealth() - damage <= floor)
            _yieldPending = true;
    }

    void BlyCrewAI::HealReceived(Unit* healer, uint32& heal)
    {
        if (CrewModeHandler* handler = Handler())
            handler->OnHealReceived(*this, healer, heal);
    }

    void BlyCrewAI::SpellHit(Unit* caster, SpellInfo const* spell)
    {
        if (CrewModeHandler* handler = Handler())
            handler->OnSpellHit(*this, caster, spell);
    }

    void BlyCrewAI::JustDied(Unit* killer)
    {
        if (_prisoner == PrisonerState::Torn || _prisoner == PrisonerState::Chained)
            SetPrisoner(PrisonerNext(_prisoner, PrisonerEvent::Execute), "death");
        if (IsWeegli() && (_door == DoorWalk::Walking || _door == DoorWalk::Planted))
        {
            // Stock: a dead Weegli frees the door data (the instance's fallback still opens the door).
            if (InstanceScript* instance = Instance())
                instance->SetData(DATA_END_DOOR, DungeonKit::State::NotStarted);
            _door = DoorWalk::Idle;
        }
        _flow.Reset();
        _yieldPending = false;
        if (CrewModeHandler* handler = Handler())
            handler->OnDied(*this, killer);
        // The default Test end counts the dead with the yielded (a fighter killed by a stray hit under the floor): a
        // living fighter checks on its next tick.
        if (!HasCrewModeHandler(CrewMode::Boss, _member) && _mode == CrewMode::Boss)
            for (uint32 m = 0; m < kCrewCount; ++m)
                if (BlyCrewAI* other = CrewAI(Instance(), m); other && other != this && other->me->IsAlive()
                    && (CrewBit(m) & kCrewFighters))
                {
                    other->_flow.RescheduleEvent(EVENT_CHECK_YIELDS, Ms(0));
                    break;
                }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The kits
    // ----------------------------------------------------------------------------------------------------------------
    void BlyCrewAI::ResetKit()
    {
        _kit.Reset();
        KitReset();
    }

    void BlyCrewAI::RunKit(uint32 diff)
    {
        _kit.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        KitUpdate(diff);
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Block's prisoner (D4a)
    // ----------------------------------------------------------------------------------------------------------------
    void BlyCrewAI::SetPrisoner(PrisonerState state, char const* how)
    {
        if (state == _prisoner)
            return;
        _prisoner = state;
        Log("prisoner", Acore::StringFormat("{} {} ({})", kCrewNames[_member],
            kPrisonerStateNames[uint32(state)], how));
    }

    bool BlyCrewAI::TakePrisoner(Position const& chain)
    {
        InstanceScript* instance = Instance();
        if (!instance || _initPending || !PrisonerEligible(_member, me->IsAlive(), _mode, _prisoner))
            return false;
        SetCrewMode(instance, _member, CrewMode::Prisoner);
        if (_mode != CrewMode::Prisoner)
            return false;
        SetPrisoner(PrisonerNext(_prisoner, PrisonerEvent::Take), "take");
        _chain = chain;
        _walkId = 0;
        _spot = CrewSpot::None;
        me->SetHomePosition(chain);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveJump(chain, Tune::kPrisonerJumpSpeedXY, Tune::kPrisonerJumpSpeedZ,
            POINT_PRISONER_CHAIN);
        _flow.RescheduleEvent(EVENT_PRISONER_TIMEOUT, Ms(Tune::kPrisonerMoveTimeoutMs));
        return true;
    }

    bool BlyCrewAI::SparePrisoner()
    {
        PrisonerState const next = PrisonerNext(_prisoner, PrisonerEvent::Spare);
        if (next == _prisoner || !me->IsAlive())
            return false;
        me->SetControlled(false, UNIT_STATE_ROOT);
        Kneel(false);
        SetPrisoner(next, "spare");
        Position const cage = ToPosition(kCrewSpawns[_member]);
        me->SetHomePosition(cage);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveJump(cage, Tune::kPrisonerJumpSpeedXY, Tune::kPrisonerJumpSpeedZ,
            POINT_PRISONER_CAGE);
        _flow.RescheduleEvent(EVENT_PRISONER_TIMEOUT, Ms(Tune::kPrisonerMoveTimeoutMs));
        return true;
    }

    bool BlyCrewAI::ExecutePrisoner(Unit* executioner)
    {
        PrisonerState const next = PrisonerNext(_prisoner, PrisonerEvent::Execute);
        if (next == _prisoner || !me->IsAlive())
            return false;
        _flow.CancelEvent(EVENT_PRISONER_TIMEOUT);
        me->SetControlled(false, UNIT_STATE_ROOT);
        SetPrisoner(next, "execute");
        Unit::Kill(executioner && executioner->IsInWorld() ? executioner : me, me);
        return true;
    }

    void BlyCrewAI::FinishPrisonerMove(uint32 pointId)
    {
        if (pointId == POINT_PRISONER_CHAIN && _prisoner == PrisonerState::Torn)
        {
            _flow.CancelEvent(EVENT_PRISONER_TIMEOUT);
            me->SetControlled(true, UNIT_STATE_ROOT);
            Kneel(true);
            SetPrisoner(PrisonerNext(_prisoner, PrisonerEvent::Arrived), "chained");
        }
        else if (pointId == POINT_PRISONER_CAGE && _prisoner == PrisonerState::Returning)
        {
            _flow.CancelEvent(EVENT_PRISONER_TIMEOUT);
            SetPrisoner(PrisonerNext(_prisoner, PrisonerEvent::Home), "home");
            SetCrewMode(Instance(), _member, CrewMode::Caged);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Bly's gossip and the fight (section 7 #18 A)
    // ----------------------------------------------------------------------------------------------------------------
    // The paths are offered: the Pyramid won, the path open, the fight neither running nor done.
    bool BlyCrewAI::PathsOffered() const
    {
        InstanceScript const* instance = me->GetInstanceScript();
        if (!instance || _mode != CrewMode::Gather || _starting || me->IsInCombat())
            return false;
        uint32 const slot = instance->GetData(DATA_CREW_FIGHT);
        return instance->GetData(DATA_PYRAMID_STAGE) == PYRAMID_STAGE_DONE
            && instance->GetData(DATA_CREW_PATH) == CREW_PATH_OPEN && slot != DungeonKit::State::InProgress
            && slot != DungeonKit::State::Done;
    }

    void BlyCrewAI::sGossipHello(Player* player)
    {
        InstanceScript* instance = Instance();
        if (!player || !instance)
            return;
        if (IsWeegli())
        {
            // Stock texts only; the door is no longer his to offer before the fight (section 7 #13 A).
            uint32 const text = _mode == CrewMode::Caged ? kTextWeegliCaged
                : _mode == CrewMode::Ally ? kTextWeegliBusy : kTextWeegliAfter;
            ClearGossipMenuFor(player);
            SendGossipMenuFor(player, text, me->GetGUID());
            return;
        }
        if (_member != CREW_BLY)
            return;

        ClearGossipMenuFor(player);
        uint32 text = _mode == CrewMode::Caged ? kTextBlyCaged : kTextBlyBusy;
        if (PathsOffered())
        {
            // Option 0 is the betrayal (bots take option 0); the Test only while its key holds, with a confirmation.
            AddGossipItemFor(player, GOSSIP_ICON_CHAT, kGossipBetrayal, GOSSIP_SENDER_MAIN, kGossipActionBetrayal);
            if (instance->GetData(DATA_TEST_KEY))
                AddGossipItemFor(player, GOSSIP_ICON_CHAT, kGossipTest, GOSSIP_SENDER_MAIN, kGossipActionTest,
                    kGossipTestConfirm, 0, false);
            text = kTextBlyPaths;
        }
        SendGossipMenuFor(player, text, me->GetGUID());
    }

    void BlyCrewAI::sGossipSelect(Player* player, uint32 /*menuId*/, uint32 gossipListId)
    {
        if (!player || _member != CREW_BLY)
            return;
        uint32 const action = player->PlayerTalkClass->GetGossipOptionAction(gossipListId);
        ClearGossipMenuFor(player);
        CloseGossipMenuFor(player);

        uint32 const path = action == kGossipActionBetrayal ? uint32(CREW_PATH_BETRAYAL)
            : action == kGossipActionTest ? uint32(CREW_PATH_TEST) : uint32(CREW_PATH_OPEN);
        InstanceScript* instance = Instance();
        if (path == CREW_PATH_OPEN || !instance || !PathsOffered())
            return;
        if (player->IsInCombat())
        {
            ChatHandler(player->GetSession()).SendNotification("Sergeant Bly won't talk while you're fighting.");
            return;
        }
        instance->SetData(DATA_CREW_PATH, path);
        if (instance->GetData(DATA_CREW_PATH) != path)
        {
            ChatHandler(player->GetSession()).SendNotification("Sergeant Bly has nothing to say to that now.");
            return;
        }
        _chooser = player->GetGUID();
        _starting = true;
        Log("path", Acore::StringFormat("chosen={} by={}", path == CREW_PATH_TEST ? "test" : "betrayal",
            player->GetName()));
        if (CrewFightStarter const& starter = Starter())
        {
            _starting = false;
            starter(me, player, path);
            return;
        }
        if (path == CREW_PATH_BETRAYAL)
            _flow.ScheduleEvent(EVENT_BETRAYAL_LINE_0, Ms(Tune::kBetrayalLine0Ms));
        else
            _flow.ScheduleEvent(EVENT_FIGHT_START, Ms(Tune::kTestStartMs));
    }

    // CR's default start: IN_PROGRESS (the instance turns the four to Boss), then the four attack the chooser, else
    // the nearest player.
    void BlyCrewAI::StartFight()
    {
        _starting = false;
        InstanceScript* instance = Instance();
        if (!instance || instance->GetData(DATA_CREW_PATH) == CREW_PATH_OPEN)
            return;
        instance->SetData(DATA_CREW_FIGHT, DungeonKit::State::InProgress);
        if (instance->GetData(DATA_CREW_FIGHT) != DungeonKit::State::InProgress)
        {
            Log("fight-refused", Acore::StringFormat("path={}", instance->GetData(DATA_CREW_PATH)));
            return;
        }
        Player* target = ObjectAccessor::GetPlayer(*me, _chooser);
        if (!target || !target->IsAlive() || target->IsGameMaster()
            || !me->IsWithinDist(target, Tune::kFightTargetRangeYd))
            target = me->SelectNearestPlayer(Tune::kFightTargetRangeYd);
        if (!target)
            return;
        // R-1-FW M4: the four are zone-engaged on the plaza's players (threat 0), so the chooser's death, a Feign
        // Death or a Vanish leaves each of them someone to fight. AttackStart adds no threat, so each one's first
        // victim is whichever zero-threat entry the threat list picks, not always the chooser (no spec row needs it).
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (CrewBit(m) & kCrewFighters)
                if (BlyCrewAI* ai = CrewAI(instance, m); ai && ai->me->IsAlive())
                {
                    for (Player* player : CrewFightTargets(ai->me))
                        ai->me->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
                    ai->AttackStart(target);
                }
    }

    // The default Test end (no Boss handler): every fighter yielded or dead. Bly says line 4, then DONE.
    void BlyCrewAI::CheckYields()
    {
        InstanceScript* instance = Instance();
        if (!instance || instance->GetData(DATA_CREW_FIGHT) != DungeonKit::State::InProgress
            || instance->GetData(DATA_CREW_PATH) != CREW_PATH_TEST)
            return;
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            if (!(CrewBit(m) & kCrewFighters))
                continue;
            Creature* crew = CrewCreature(instance, m);
            if (crew && crew->IsAlive() && GetCrewMode(instance, m) != CrewMode::Yielded)
                return;
        }
        if (Creature* bly = CrewCreature(instance, CREW_BLY); bly && bly->IsAlive() && bly->IsAIEnabled)
            bly->AI()->Talk(SAY_BLY_TEST_DONE);
        Log("fight", "all-yielded");
        instance->SetData(DATA_CREW_FIGHT, DungeonKit::State::Done);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Weegli's End Door (section 7 #13 A, #14 A)
    // ----------------------------------------------------------------------------------------------------------------
    void BlyCrewAI::StartDoorWalk()
    {
        InstanceScript* instance = Instance();
        if (!IsWeegli() || !instance || DoorWalkNext(_door, DoorEvent::Start, false) == _door)
            return;
        if (instance->GetData(DATA_END_DOOR) == DungeonKit::State::Done)
        {
            DoorBlown();        // the fallback (or a GM) beat him to it
            return;
        }
        _door = DoorWalkNext(_door, DoorEvent::Start, false);
        instance->SetData(DATA_END_DOOR, DungeonKit::State::InProgress);
        StopFighting();
        Kneel(false);
        bool const test = instance->GetData(DATA_CREW_PATH) == CREW_PATH_TEST;
        Talk(test ? SAY_WEEGLI_HERE_I_GO : SAY_WEEGLI_OUT_OF_HERE);
        _spot = CrewSpot::None;
        Log("door", Acore::StringFormat("walk path={}", test ? "test" : "betrayal"));
        WalkTo(ToPosition(kWeegliDoorSpot), POINT_WEEGLI_DOOR, true);
    }

    void BlyCrewAI::ArriveAtDoor()
    {
        if (_door != DoorWalk::Walking)
            return;
        _walkId = 0;
        _flow.CancelEvent(EVENT_WALK_TIMEOUT);
        me->SetFacingTo(kWeegliDoorSpot.o);
        _flow.RescheduleEvent(EVENT_PLANT, Ms(Tune::kPlantDelayMs));
    }

    void BlyCrewAI::PlantBarrel()
    {
        InstanceScript* instance = Instance();
        if (_door != DoorWalk::Walking || !instance)
            return;
        if (instance->GetData(DATA_END_DOOR) == DungeonKit::State::Done)
        {
            DoorBlown();
            return;
        }
        DoCastSelf(SPELL_WEEGLIS_BARREL, true);
        bool const over = instance->GetData(DATA_CREW_FIGHT) == DungeonKit::State::Done;
        _door = DoorWalk::Planted;
        Log("door", Acore::StringFormat("planted fightover={}", over ? 1 : 0));
        if (DoorWalkNext(DoorWalk::Walking, DoorEvent::Planted, over) == DoorWalk::Fuse)
            LightFuse();
    }

    void BlyCrewAI::LightFuse()
    {
        if (DoorWalkNext(_door, DoorEvent::FightOver, true) != DoorWalk::Fuse)
            return;
        _door = DoorWalk::Fuse;
        Log("door", "fuse");
        _flow.RescheduleEvent(EVENT_FUSE, Ms(Tune::kFuseMs));
    }

    void BlyCrewAI::DoorBlown()
    {
        InstanceScript* instance = Instance();
        DoorWalk const next = DoorWalkNext(_door, DoorEvent::Blown, true);
        if (next == _door)
            return;
        _door = next;
        RemoveBarrel(me);
        if (instance && instance->GetData(DATA_END_DOOR) != DungeonKit::State::Done)
        {
            instance->SetData(DATA_END_DOOR, DungeonKit::State::Done);
            Log("door", "blown");
        }
        if (_mode == CrewMode::PoolAlly)
            DepartToPool();
        else if (_mode == CrewMode::Gone)
            LeaveForGood(false);
        else
        {
            // A GM's door outside the paths: back to his spot.
            _door = DoorWalk::Idle;
            GoToSpot(RestSpotFor(_mode, instance ? instance->GetData(DATA_PYRAMID_STAGE) : 0), false);
        }
    }

    // A crew wipe before the door went: the door data back to shut, the barrel gone, home to his spot.
    void BlyCrewAI::AbortDoorWalk()
    {
        DoorWalk const next = DoorWalkNext(_door, DoorEvent::Abort, false);
        if (next == _door)
            return;
        _door = next;
        _flow.CancelEvent(EVENT_PLANT);
        _flow.CancelEvent(EVENT_FUSE);
        RemoveBarrel(me);
        InstanceScript* instance = Instance();
        if (instance)
            instance->SetData(DATA_END_DOOR, DungeonKit::State::NotStarted);
        Log("door", "abort");
        _spot = CrewSpot::None;
        GoToSpot(RestSpotFor(_mode, instance ? instance->GetData(DATA_PYRAMID_STAGE) : 0), false);
    }

    // Weegli leaves for good (the betrayal): the stock escape path, then despawn; `now`: despawn at once (a reload,
    // the path's end).
    void BlyCrewAI::LeaveForGood(bool now)
    {
        if (now)
        {
            _door = DoorWalk::Done;
            Log("gone", kCrewNames[_member]);
            me->DespawnOrUnsummon();
            return;
        }
        me->SetWalk(false);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveWaypoint(kWeegliEscapePath, false);
        _flow.RescheduleEvent(EVENT_ESCAPE_DESPAWN, Ms(Tune::kEscapeDespawnMs));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pool (the Test path; section 7 #14 A)
    // ----------------------------------------------------------------------------------------------------------------
    // Band's Escape (Bly's stock 10 s port-out, a self dummy) at the gather spot or the door, then the shore.
    void BlyCrewAI::DepartToPool()
    {
        if (_departing || _atPool || _mode != CrewMode::PoolAlly)
            return;
        _departing = true;
        _spot = CrewSpot::Pool;
        StopFighting();
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        DoCastSelf(SPELL_BANDS_ESCAPE);
        Log("pool", Acore::StringFormat("depart {}", kCrewNames[_member]));
        _flow.RescheduleEvent(EVENT_ARRIVE_POOL, Ms(Tune::kBandsEscapeMs));
    }

    void BlyCrewAI::ArriveAtPool()
    {
        if (_mode != CrewMode::PoolAlly)
            return;
        _departing = false;
        bool const first = !_atPool;
        _atPool = true;
        if (IsWeegli())
            _door = DoorWalk::Done;
        if (first)
            Log("pool", Acore::StringFormat("arrived {}", kCrewNames[_member]));
        InstanceScript* instance = Instance();
        if (!instance || instance->GetData(DATA_CREW_AT_POOL))
            return;
        uint32 arrived = 0;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (BlyCrewAI* ai = CrewAI(instance, m); ai && ai->me->IsAlive() && ai->ArrivedAtPool())
                arrived |= CrewBit(m);
        if (AllArrived(arrived))
            instance->SetData(DATA_CREW_AT_POOL, 1);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Free functions (BlyCrew.h)
    // ----------------------------------------------------------------------------------------------------------------
    BlyCrewAI* CrewAI(Creature* creature)
    {
        if (!creature || !creature->IsAIEnabled || !CrewMemberOf(creature))
            return nullptr;
        return dynamic_cast<BlyCrewAI*>(creature->AI());
    }

    BlyCrewAI* CrewAI(InstanceScript* instance, uint32 member)
    {
        return CrewAI(CrewCreature(instance, member));
    }

    bool MoveCrew(InstanceScript* instance, uint32 member, Position const& pos, uint32 pointId, bool run)
    {
        BlyCrewAI* ai = CrewAI(instance, member);
        if (!ai || !ai->Me()->IsAlive())
            return false;
        ai->WalkTo(pos, pointId, run);
        return true;
    }

    uint32 HealCrew(Creature* crew, Unit* healer, uint32 amount)
    {
        if (!crew || !crew->IsAlive() || !amount)
            return 0;
        uint32 const before = crew->GetHealth();
        Unit::DealHeal(healer ? healer : crew, crew, amount);
        return crew->GetHealth() - before;
    }

    uint32 DamageCrew(Creature* crew, Unit* attacker, uint32 amount, SpellSchoolMask school, SpellInfo const* spell)
    {
        if (!crew || !crew->IsAlive() || !amount)
            return 0;
        uint32 const before = crew->GetHealth();
        Unit::DealDamage(attacker ? attacker : crew, crew, amount, nullptr, DIRECT_DAMAGE, school, spell, false);
        return before - (crew->IsAlive() ? crew->GetHealth() : 0);
    }

    bool KillCrew(Creature* crew, Unit* killer)
    {
        if (!crew || !crew->IsAlive())
            return false;
        BlyCrewAI* ai = CrewAI(crew);
        if (ai && ai->IsWeegli() && WeegliFloorHolds(ai->Mode(), ai->ArrivedAtPool()))
            return false;
        Unit::Kill(killer && killer->IsInWorld() ? killer : crew, crew);
        return true;
    }

    uint32 PrisonerCandidates(InstanceScript* instance)
    {
        uint32 mask = 0;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (BlyCrewAI* ai = CrewAI(instance, m))
                if (PrisonerEligible(m, ai->Me()->IsAlive(), ai->Mode(), ai->Prisoner()))
                    mask |= CrewBit(m);
        return mask;
    }

    std::optional<uint32> CurrentPrisoner(InstanceScript* instance)
    {
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (BlyCrewAI* ai = CrewAI(instance, m))
                if (ai->Prisoner() == PrisonerState::Torn || ai->Prisoner() == PrisonerState::Chained)
                    return m;
        return std::nullopt;
    }

    bool TakePrisoner(InstanceScript* instance, uint32 member, Position const& chain)
    {
        BlyCrewAI* ai = CrewAI(instance, member);
        return ai && ai->TakePrisoner(chain);
    }

    bool SparePrisoner(InstanceScript* instance, uint32 member)
    {
        BlyCrewAI* ai = CrewAI(instance, member);
        return ai && ai->SparePrisoner();
    }

    bool ExecutePrisoner(InstanceScript* instance, uint32 member, Unit* executioner)
    {
        BlyCrewAI* ai = CrewAI(instance, member);
        return ai && ai->ExecutePrisoner(executioner);
    }
}

// --------------------------------------------------------------------------------------------------------------------
// The five members and their stock kits (SmartAI 7605, 7606, 7608 before the S0 rev; npc_sergeant_bly)
// --------------------------------------------------------------------------------------------------------------------
using namespace ZfCrew;

struct npc_bly_crew_bly : public BlyCrewAI
{
    enum Kit : uint32
    {
        EV_SHIELD_BASH = 1,
        EV_REVENGE,
    };

    explicit npc_bly_crew_bly(Creature* creature) : BlyCrewAI(creature, CREW_BLY) { }

    void KitReset() override
    {
        _kit.ScheduleEvent(EV_SHIELD_BASH, Rand(Tune::kShieldBashFirst));
        _kit.ScheduleEvent(EV_REVENGE, Rand(Tune::kRevengeFirst));
    }

    void KitUpdate(uint32 /*diff*/) override
    {
        while (uint32 const eventId = _kit.ExecuteEvent())
        {
            switch (eventId)
            {
                case EV_SHIELD_BASH:
                    DoCastVictim(SPELL_SHIELD_BASH);
                    _kit.ScheduleEvent(EV_SHIELD_BASH, Rand(Tune::kShieldBash));
                    break;
                case EV_REVENGE:
                    DoCastVictim(SPELL_REVENGE);
                    _kit.ScheduleEvent(EV_REVENGE, Rand(Tune::kRevenge));
                    break;
                default:
                    break;
            }
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
    }
};

struct npc_bly_crew_raven : public BlyCrewAI
{
    enum Kit : uint32
    {
        EV_GOUGE = 1,
        EV_BACKSTAB,
    };

    explicit npc_bly_crew_raven(Creature* creature) : BlyCrewAI(creature, CREW_RAVEN) { }

    void KitReset() override
    {
        // Stock (SmartAI 7605, on reset): Dual Wield 29651, whose only effect is this (set directly: Reset also runs
        // inside AddToWorld).
        me->SetCanDualWield(true);
        _kit.ScheduleEvent(EV_GOUGE, Rand(Tune::kGougeFirst));
        _kit.ScheduleEvent(EV_BACKSTAB, Rand(Tune::kBackstab));
    }

    void KitUpdate(uint32 /*diff*/) override
    {
        while (uint32 const eventId = _kit.ExecuteEvent())
        {
            switch (eventId)
            {
                case EV_GOUGE:
                    if (Unit* target = SelectTarget(SelectTargetMethod::Random, 0, Tune::kGougeRangeYd, true))
                        DoCast(target, SPELL_GOUGE);
                    _kit.ScheduleEvent(EV_GOUGE, Rand(Tune::kGouge));
                    break;
                case EV_BACKSTAB:
                    if (Unit* victim = me->GetVictim(); victim && victim->isInBack(me))
                        DoCast(victim, SPELL_BACKSTAB);
                    _kit.ScheduleEvent(EV_BACKSTAB, Rand(Tune::kBackstab));
                    break;
                default:
                    break;
            }
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
    }
};

struct npc_bly_crew_oro : public BlyCrewAI
{
    enum Kit : uint32
    {
        EV_SHADOW_BOLT = 1,
        EV_RAIN_OF_FIRE,
        EV_IMMOLATE,
        EV_CURSE,
    };

    explicit npc_bly_crew_oro(Creature* creature) : BlyCrewAI(creature, CREW_ORO) { }

    void KitReset() override
    {
        _kit.ScheduleEvent(EV_SHADOW_BOLT, Rand(Tune::kShadowBoltFirst));
        _kit.ScheduleEvent(EV_RAIN_OF_FIRE, Rand(Tune::kRainFirst));
        _kit.ScheduleEvent(EV_IMMOLATE, Rand(Tune::kImmolateFirst));
        _kit.ScheduleEvent(EV_CURSE, Rand(Tune::kCurseFirst));
    }

    void KitUpdate(uint32 /*diff*/) override
    {
        while (uint32 const eventId = _kit.ExecuteEvent())
        {
            switch (eventId)
            {
                case EV_SHADOW_BOLT:
                    DoCastVictim(SPELL_SHADOW_BOLT);
                    _kit.ScheduleEvent(EV_SHADOW_BOLT, Rand(Tune::kShadowBolt));
                    break;
                case EV_RAIN_OF_FIRE:
                    if (Unit* target = SelectTarget(SelectTargetMethod::Random, 0, Tune::kRainRangeYd, true))
                        DoCast(target, SPELL_RAIN_OF_FIRE);
                    _kit.ScheduleEvent(EV_RAIN_OF_FIRE, Rand(Tune::kRain));
                    break;
                case EV_IMMOLATE:
                    DoCastVictim(SPELL_IMMOLATE);
                    _kit.ScheduleEvent(EV_IMMOLATE, Rand(Tune::kImmolate));
                    break;
                case EV_CURSE:
                    DoCastVictim(SPELL_CURSE_OF_WEAKNESS);
                    _kit.ScheduleEvent(EV_CURSE, Rand(Tune::kCurse));
                    break;
                default:
                    break;
            }
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
    }
};

struct npc_bly_crew_weegli : public BlyCrewAI
{
    // No kit: Weegli never fights (his barrels on the Stair are D4b's, his charges at the pool D7Ha's).
    explicit npc_bly_crew_weegli(Creature* creature) : BlyCrewAI(creature, CREW_WEEGLI) { }
};

struct npc_bly_crew_murta : public BlyCrewAI
{
    enum Kit : uint32
    {
        EV_SMITE = 1,
        EV_HEAL,
    };

    explicit npc_bly_crew_murta(Creature* creature) : BlyCrewAI(creature, CREW_MURTA) { }

    void KitReset() override
    {
        _kit.ScheduleEvent(EV_SMITE, Rand(Tune::kSmiteFirst));
        _kit.ScheduleEvent(EV_HEAL, Rand(Tune::kHealCheckFirst));
    }

    void KitUpdate(uint32 /*diff*/) override
    {
        while (uint32 const eventId = _kit.ExecuteEvent())
        {
            switch (eventId)
            {
                case EV_SMITE:
                    DoCastVictim(SPELL_HOLY_SMITE);
                    _kit.ScheduleEvent(EV_SMITE, Rand(Tune::kSmite));
                    break;
                case EV_HEAL:
                    _kit.ScheduleEvent(EV_HEAL, Heal() ? Rand(Tune::kHealCheck) : Ms(Tune::kHealRetryMs));
                    break;
                default:
                    break;
            }
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }
    }

    // Healing by script (section 3.12): the stock Heal, Shield and Renew at percent values of the target's health.
    // Ally: the group and the crew in Ally; Boss: the crew in Boss. Returns whether a spell went out.
    bool Heal()
    {
        InstanceScript* instance = Instance();
        std::vector<Unit*> candidates;
        if (instance)
            for (uint32 m = 0; m < kCrewCount; ++m)
                if (Creature* crew = CrewCreature(instance, m); crew && crew->IsAlive()
                    && GetCrewMode(instance, m) == Mode() && me->IsWithinDistInMap(crew, Tune::kHealRangeYd))
                    candidates.push_back(crew);
        if (Mode() == CrewMode::Ally)
            for (auto const& ref : me->GetMap()->GetPlayers())
                if (Player* player = ref.GetSource(); player && player->IsAlive() && !player->IsGameMaster()
                    && me->IsWithinDistInMap(player, Tune::kHealRangeYd) && me->IsFriendlyTo(player))
                    candidates.push_back(player);

        std::vector<float> pcts;
        pcts.reserve(candidates.size());
        for (Unit* unit : candidates)
            pcts.push_back(unit->GetHealthPct());
        std::optional<std::size_t> const pick = PickHealTarget(pcts, Tune::kRenewBelowPct);
        if (!pick)
            return false;
        Unit* target = candidates[*pick];
        MurtaHeal const spell = MurtaSpellFor(target->GetHealthPct(), target->HasAura(SPELL_RENEW, me->GetGUID()),
            target->HasAura(SPELL_PW_SHIELD, me->GetGUID()));
        CastSpellExtraArgs args;
        switch (spell)
        {
            case MurtaHeal::Heal:
                args.AddSpellBP0(int32(PctOf(target->GetMaxHealth(), Tune::kHealPct)));
                me->CastSpell(target, SPELL_HEAL, args);
                return true;
            case MurtaHeal::Shield:
                args.AddSpellBP0(int32(PctOf(target->GetMaxHealth(), Tune::kShieldPct)));
                me->CastSpell(target, SPELL_PW_SHIELD, args);
                return true;
            case MurtaHeal::Renew:
                args.AddSpellBP0(int32(PctOf(target->GetMaxHealth(), Tune::kRenewTickPct)));
                me->CastSpell(target, SPELL_RENEW, args);
                return true;
            default:
                return false;
        }
    }
};

// --------------------------------------------------------------------------------------------------------------------
// `.dbtest zf band`
//
//   .dbtest zf band info                          each member: alive, health, mode, spot, prisoner, door, pool
//   .dbtest zf band place                         every living member to its rest spot (a teleport)
//   .dbtest zf band prisoner <member> take|spare|execute   the Block's machine (take: 2.5 yd in front of the
//                                                 Executioner; the member must be Caged)
//   .dbtest zf band start                         Bly's default fight start now (the path must be chosen)
//   .dbtest zf band depart                        a PoolAlly member still on the plaza leaves for the pool now
// --------------------------------------------------------------------------------------------------------------------
namespace
{
    std::optional<uint32> MemberByName(std::string const& what)
    {
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            std::string name = kCrewNames[m];
            std::string lower;
            for (char c : what)
                lower += char(std::tolower(static_cast<unsigned char>(c)));
            for (char& c : name)
                c = char(std::tolower(static_cast<unsigned char>(c)));
            if (lower == name || lower == std::to_string(m))
                return m;
        }
        return std::nullopt;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        ZfTest::PrintRunState(handler, instance);
        for (uint32 m = 0; m < kCrewCount; ++m)
        {
            Creature* crew = CrewCreature(instance, m);
            BlyCrewAI* ai = CrewAI(crew);
            if (!crew)
            {
                handler->PSendSysMessage("{}: not in the world (mode {})", kCrewNames[m],
                    kCrewModeNames[uint32(GetCrewMode(instance, m))]);
                continue;
            }
            handler->PSendSysMessage("{}: {} {:.0f}% mode={} spot={} prisoner={} door={} pool={} faction={} "
                "handler={}", kCrewNames[m], crew->IsAlive() ? "alive" : "dead", crew->GetHealthPct(),
                ai ? kCrewModeNames[uint32(ai->Mode())] : "?", ai ? kCrewSpotNames[uint32(ai->Spot())] : "?",
                ai ? kPrisonerStateNames[uint32(ai->Prisoner())] : "?", ai ? kDoorWalkNames[uint32(ai->Door())] : "?",
                ai && ai->ArrivedAtPool() ? 1 : 0, crew->GetFaction(),
                ai && HasCrewModeHandler(ai->Mode(), m) ? 1 : 0);
        }
        return true;
    }

    bool HandlePlace(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        uint32 const stage = instance->GetData(DATA_PYRAMID_STAGE);
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (BlyCrewAI* ai = CrewAI(instance, m); ai && ai->Me()->IsAlive())
                ai->GoToSpot(RestSpotFor(ai->Mode(), stage), true);
        return HandleInfo(handler);
    }

    bool HandlePrisoner(ChatHandler* handler, std::string member, std::string what)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        std::optional<uint32> const m = MemberByName(member);
        if (!m)
        {
            handler->SendErrorMessage("Usage: .dbtest zf band prisoner <bly|raven|oro|murta> <take|spare|execute>");
            return false;
        }
        bool done = false;
        if (what == "take")
            done = TakePrisoner(instance, *m, GmChainSpot(instance));
        else if (what == "spare")
            done = SparePrisoner(instance, *m);
        else if (what == "execute")
            done = ExecutePrisoner(instance, *m, instance->GetCreature(kGuidExecutioner));
        if (!done)
            handler->SendErrorMessage("Refused (take: a Caged fighter, never Weegli; spare / execute: torn or "
                "chained).");
        return HandleInfo(handler);
    }

    bool HandleStart(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        if (instance->GetData(DATA_CREW_PATH) == CREW_PATH_OPEN)
        {
            handler->SendErrorMessage("Choose a path first: .dbtest zf crew path 1 (betrayal) or 2 (the Test).");
            return false;
        }
        instance->SetData(DATA_CREW_FIGHT, DungeonKit::State::InProgress);
        if (Player* gm = handler->GetPlayer())
            for (uint32 m = 0; m < kCrewCount; ++m)
                if (CrewBit(m) & kCrewFighters)
                    if (BlyCrewAI* ai = CrewAI(instance, m); ai && ai->Me()->IsAlive())
                        ai->AttackStart(gm);
        return HandleInfo(handler);
    }

    bool HandleDepart(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        for (uint32 m = 0; m < kCrewCount; ++m)
            if (BlyCrewAI* ai = CrewAI(instance, m); ai && ai->Me()->IsAlive() && ai->Mode() == CrewMode::PoolAlly
                && !ai->ArrivedAtPool())
                ai->GoToSpot(CrewSpot::Pool, false);
        return HandleInfo(handler);
    }

    ChatCommandTable const& BandTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "place",    HandlePlace,    SEC_GAMEMASTER, Console::No },
            { "prisoner", HandlePrisoner, SEC_GAMEMASTER, Console::No },
            { "start",    HandleStart,    SEC_GAMEMASTER, Console::No },
            { "depart",   HandleDepart,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_zf_bly_crew()
{
    RegisterDungeonReworkCreatureAI(npc_bly_crew_bly, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_raven, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_oro, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_weegli, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_bly_crew_murta, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("band", BandTestCommands());
}
