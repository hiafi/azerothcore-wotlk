/*
 * mod-dungeon-bosses, Scholomance S13:
 * Darkmaster Gandling's hard mode, "the Graduate Exam" (heroic only). Build spec: docs/dungeons/scholomance-rework.md
 * SC 2909-3006 (the honors program, the gauntlet, its numbers and approved answers), SC 3046-3063 (GD5, GD6, the
 * examiners, the paper); handoff sections 3.5 row S13, 3.6, 3.7, 3.10. The pure half is GraduateExamLogic.h; the
 * instance owns the driver (GraduateExam.h).
 *
 *   Passing Grades   (ruling 22) the instance holds them (the instructors' GradeWatch awards them, saved); this file
 *                    only shows them: one aura per instructor (206365-206370) on every player of the map who holds
 *                    it, re-shown every kGradeSweepMs (a death keeps them; a map change drops them, and the engine
 *                    strips CHANGE_MAP auras at every logout and login, so the sweep shows them again inside).
 *   The paper        go_sc_honors_paper, GO 301153 on the study's upper floor (kHonorsPaper, heroic spawn only): a
 *                    click with the honors program open (every instructor graded by 3 players), Gandling revealed and
 *                    idle signs it (DATA_GANDLING_HARD_MODE) and starts the gauntlet; otherwise it says why not.
 *                    Bots never click it (no DungeonEvent, handoff 3.12).
 *   GD5 the gauntlet Gandling yells line 4 and stays in the study, not selectable or attackable and with no combat
 *                    of his own; his boss state goes IN_PROGRESS (the door data shuts the six gates and the entrance).
 *                    5 s later the group is portaled into the first of the six classrooms (a random order) and that
 *                    room's Graduate Examiner (300548-300554, the instructor's own AI in examiner mode: heroic values,
 *                    80k; the Ravenian 60k with his own Corvane 20k) is raised and pulled once the whole group is in
 *                    the room (F-B1; the pull is retried every tick until it engages, R-C EXAM SF-1). Gandling's
 *                    Portal Volley and Transfer reach into the room at heroic values (GauntletMode: lanes from the
 *                    room's walls, the examiner's victim as the tank); no Detention. 5 s after each kill a portal
 *                    takes the group on, and the lanes' Weakened is cleared (orchestrator ruling 2026-11-08). A
 *                    player who missed a portal (offline, released, a late zone-in) is brought to the group's room
 *                    (or the study) as soon as they are back on the map, alive or not yet released.
 *   GD6 the final    after the sixth room the portal returns the group to the study: yell line 5, Gandling at 200k
 *                    and attackable, pulled at once in FinalExamMode (no Detention, a lane through every player every
 *                    20 s, a swap every 15 s raising an Expelled Student).
 *   A wipe           (nobody alive; an examiner or Gandling out of combat after its pull engaged, or never engaged
 *                    within kPullTimeoutMs) puts everything back: the examiner's fight is ended before it despawns
 *                    (F-B1), Gandling's flags, health and mode return, his state goes NOT_STARTED (the gates open)
 *                    and the signature is cleared, so the paper can be signed again; the grades stay. The hard mode
 *                    loot bit rides Gandling while the signature is lit (the instance and his Reset), so only a kill
 *                    in the final phase drops it.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GandlingFight.h"
#include "GraduateExam.h"
#include "GraduateExamLogic.h"
#include "InstanceScript.h"
#include "MechanicWeakened.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WorldSession.h"
#include <algorithm>
#include <memory>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoGraduateExam;
using ScholoGandling::GandlingFightApi;
using ScholoGandling::GetGandlingFight;

namespace
{
    char const* const kLogName = "exam";
    uint32 constexpr kPaperPollMs = 1000;

    // Gandling's flags while the group sits the exams: not selectable and not attackable (the mod-boss-mechanics marker
    // precedent, apps/dbc-tools lib/dsl/dungeon_kit.py kit_helper). No combat of his own (SetIsCombatDisallowed, the
    // stock Lich King and Nexus precedent): his lanes still hit with him as their original caster.
    std::array<UnitFlags, 2> constexpr kUnreachableFlags{ { UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE } };

    std::size_t RandIndex(std::size_t n)
    {
        return n ? std::size_t(urand(0, uint32(n) - 1)) : 0;
    }

    void ExamLog(char const* what, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kLogName, what, detail);
    }

    void ExamNotify(Map* map, std::string const& text)
    {
        if (!map)
            return;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (WorldSession* session = player->GetSession())
                    ChatHandler(session).SendNotification(text);
    }

    // The players the gauntlet moves: everyone on the map but GMs and released ghosts (a dead player who has not
    // released goes along, so a battle resurrection still works in the next room).
    bool Movable(Player const* player)
    {
        return player && player->IsInWorld() && !player->IsGameMaster() && !player->HasPlayerFlag(PLAYER_FLAGS_GHOST);
    }

    bool Fighting(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // Create health is the base the engine rebuilds max health from (the Deadmines hard mode's SetBossHealth).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, float(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    bool AnyFightingIn(Map* map, Arena const& arena)
    {
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (Fighting(player) && arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                return true;
        }
        return false;
    }

    // Every player of `arena` goes on `unit`'s threat list (its pull), the nearest first as its victim.
    bool PullInto(Creature* unit, Arena const& arena)
    {
        Player* nearest = nullptr;
        for (auto const& ref : unit->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!Fighting(player) || !arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                continue;
            unit->GetThreatMgr().AddThreat(player, 1.0f);
            if (!nearest || unit->GetExactDist2d(player) < unit->GetExactDist2d(nearest))
                nearest = player;
        }
        if (nearest && unit->IsAIEnabled)
            unit->AI()->AttackStart(nearest);
        return nearest != nullptr;
    }
}

namespace ScholoGraduateExam
{
    char const* PaperRefusalText(PaperRefusal why)
    {
        switch (why)
        {
            case PaperRefusal::None:         return "";
            case PaperRefusal::NotHeroic:    return "The honors program admits heroic students only.";
            case PaperRefusal::GandlingDone: return "The headmaster is dead. Nobody is left to examine you.";
            case PaperRefusal::NotRevealed:  return "The headmaster has not shown himself yet.";
            case PaperRefusal::GandlingBusy: return "Class is in session.";
            case PaperRefusal::HonorsClosed:
                return "The honors program needs Passing Grades from three students for every instructor.";
        }
        return "";
    }
}

// ---- The driver -----------------------------------------------------------------------------------------------------
class GraduateExamDriver final : public GraduateExam
{
public:
    explicit GraduateExamDriver(InstanceScript* instance)
        : _instance(instance), _examinerRef(std::make_shared<ObjectGuid>()) { }

    void Update(uint32 diff) override
    {
        if (!_staleChecked)
        {
            _staleChecked = true;
            ClearStaleSignature();
        }
        _sweepMs += diff;
        if (_sweepMs >= kGradeSweepMs)
        {
            _sweepMs = 0;
            SweepGrades();
        }
        if (!_run.Running())
            return;

        switch (_run.Update(diff, Inputs()))
        {
            case ExamAction::SendToRoom:    SendToRoom();          break;
            case ExamAction::PullExaminer:  PullExaminer();        break;
            case ExamAction::RetryPull:     RetryPull();           break;
            case ExamAction::RoomCleared:   RoomCleared();         break;
            case ExamAction::ReturnToStudy: ReturnToStudy();       break;
            case ExamAction::StartFinal:    StartFinal();          break;
            case ExamAction::Wipe:          Reset("wipe");         break;
            case ExamAction::Passed:        Passed();              break;
            case ExamAction::None:                                 break;
        }
        if (_run.Running())
            CollectStragglers();
    }

    void SyncGrades(Player* player) override
    {
        InstanceApi* api = GetInstanceApi(_instance);
        if (!api || !player || !player->IsInWorld())
            return;
        uint32 shown = 0;
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            if (player->HasAura(PassingGradeSpell(Instructor(i))))
                shown |= 1u << i;
        GradeAuraChange const change = GradeAuraDiff(api->Grades().MaskOf(player->GetGUID().GetCounter()), shown);
        for (std::size_t i = 0; i < kInstructorCount; ++i)
        {
            uint32 const bit = 1u << i;
            uint32 const spell = PassingGradeSpell(Instructor(i));
            if ((change.add & bit) && player->IsAlive())
                player->AddAura(spell, player);
            if (change.remove & bit)
                player->RemoveAurasDueToSpell(spell);
        }
    }

    PaperRefusal Check() const override
    {
        Creature* gandling = Gandling();
        PaperState s;
        s.heroic = _instance->instance->IsHeroic();
        s.revealed = _instance->GetData(DATA_GANDLING_REVEALED) != 0;
        s.gandlingState = uint32(_instance->GetBossState(BOSS_GANDLING));
        if (gandling && gandling->isDead())
            s.gandlingState = DungeonKit::State::Done;
        // Not loaded (his grid asleep): nothing to start yet, read as not revealed.
        s.revealed = s.revealed && gandling;
        // Busy while he walks home from a wipe too (R-C EXAM N-4: JustReachedHome would undo setActive mid-exam).
        s.gandlingEngaged = gandling && (gandling->IsEngaged() || gandling->IsInEvadeMode());
        s.examRunning = _run.Running();
        s.honorsOpen = _instance->GetData(DATA_HONORS_OPEN) != 0;
        return CheckPaper(s);
    }

    bool TrySign(Player* by, std::optional<Classroom> firstRoom) override
    {
        if (Check() != PaperRefusal::None)
            return false;
        Creature* gandling = Gandling();
        GandlingFightApi* fight = GetGandlingFight(gandling);
        if (!fight)
        {
            ExamLog("sign-refused", "Gandling does not run boss_darkmaster_gandling_rework");
            return false;
        }
        _instance->SetData(DATA_GANDLING_HARD_MODE, 1);
        if (!_instance->GetData(DATA_GANDLING_HARD_MODE))
        {
            ExamLog("sign-refused", "the instance refused the signature");
            return false;
        }

        // He stays in the study, out of reach, his state IN_PROGRESS (the door data shuts the gates and the
        // entrance); his registry encounter is the whole hard mode (his lanes' Weakened ends with it).
        _flagsAdded.clear();
        for (UnitFlags const flag : kUnreachableFlags)
        {
            if (gandling->HasUnitFlag(flag))
                continue;
            gandling->SetUnitFlag(flag);
            _flagsAdded.push_back(flag);
        }
        gandling->SetIsCombatDisallowed(true);
        gandling->setActive(true);
        _instance->SetBossState(BOSS_GANDLING, IN_PROGRESS);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GANDLING;
        Mechanic::BeginEncounter(gandling, options);

        fight->Abort();
        fight->SetRegion(ScholoGandling::StudyRegion());
        fight->SetMode(IdleMode());
        Map* map = _instance->instance;
        std::shared_ptr<ObjectGuid> const examiner = _examinerRef;
        fight->SetTankProvider([map, examiner]()
        {
            Creature* unit = examiner->IsEmpty() ? nullptr : map->GetCreature(*examiner);
            Unit const* victim = unit && unit->IsAlive() ? unit->GetVictim() : nullptr;
            return victim ? victim->GetGUID() : ObjectGuid::Empty;
        });
        if (gandling->IsAIEnabled)
            gandling->AI()->Talk(YELL_GANDLING_HARD_MODE);

        _run.Start(ExamOrder(RandIndex, firstRoom ? int(*firstRoom) : -1));
        std::string order;
        for (Classroom const c : _run.Order())
            order += Acore::StringFormat("{}{}", order.empty() ? "" : ",", uint32(c));
        ExamLog("signed", Acore::StringFormat("by={} order=[{}]", by ? by->GetName() : "none", order));
        return true;
    }

    bool Running() const override
    {
        return _run.Running();
    }

    std::string SkipRoom() override
    {
        if (_run.Phase() != ExamPhase::Examining)
            return "No examiner fights now.";
        Creature* examiner = Examiner();
        if (!examiner || !examiner->IsAlive())
            return "The examiner is gone.";
        // The Ravenian's examiner dies for real only with his Corvane (user ruling: he collapses at 1 HP).
        if (Creature* corvane = examiner->FindNearestCreature(NPC_SC_EXAMINER_CORVANE, 100.f, true))
            corvane->KillSelf();
        if (examiner->IsAlive())
            examiner->KillSelf();
        return {};
    }

    std::string SkipToFinal() override
    {
        if (!_run.Running() || _run.Phase() == ExamPhase::Final || _run.Phase() == ExamPhase::Returning)
            return "The gauntlet is not under way.";
        DespawnExaminer();
        if (GandlingFightApi* fight = GetGandlingFight(Gandling()))
        {
            fight->Abort();
            fight->SetMode(IdleMode());
        }
        _run.SkipToStudy();
        return {};
    }

    void Stop(char const* why) override
    {
        if (_run.Running())
            Reset(why);
    }

    std::string StateLine() const override
    {
        std::string order;
        for (Classroom const c : _run.Order())
            order += Acore::StringFormat("{}{}", order.empty() ? "" : ",", uint32(c));
        Creature* examiner = Examiner();
        return Acore::StringFormat("phase={} room={} ({} of {}) cleared={} order=[{}] examiner={} ({}) sent={} "
            "signed={} flags={}", PhaseName(_run.Phase()), _run.Running() ? kClassroomNames[std::size_t(_run.Room())]
            : "-", _run.RoomIndex() + 1, kClassroomCount, _run.RoomsCleared(), order,
            examiner ? examiner->GetEntry() : 0, !examiner ? "none" : examiner->IsAlive() ? "alive" : "dead",
            _sent.size(), _instance->GetData(DATA_GANDLING_HARD_MODE), _flagsAdded.size());
    }

private:
    Map* GetMap() const
    {
        return _instance->instance;
    }

    Creature* Gandling() const
    {
        return _instance->GetCreature(DATA_GANDLING_GUID);
    }

    Creature* Examiner() const
    {
        return _examiner.IsEmpty() ? nullptr : GetMap()->GetCreature(_examiner);
    }

    // ---- Inputs -----------------------------------------------------------------------------------------------------
    ExamInputs Inputs() const
    {
        ExamInputs in;
        in.anyAlive = false;
        for (auto const& ref : GetMap()->GetPlayers())
            if (Fighting(ref.GetSource()))
                in.anyAlive = true;
        switch (_run.Phase())
        {
            case ExamPhase::Arriving:
                in.arrived = GroupArrived(ClassroomArena(_run.Room()));
                break;
            case ExamPhase::Returning:
                in.arrived = GroupArrived(GandlingArena());
                break;
            case ExamPhase::Examining:
            {
                Creature* examiner = Examiner();
                in.examinerDead = examiner && examiner->isDead();
                in.examinerGone = !examiner;
                in.examinerEngaged = examiner && examiner->IsAlive() && examiner->IsEngaged();
                in.anyInside = AnyFightingIn(GetMap(), ClassroomArena(_run.Room()));
                break;
            }
            case ExamPhase::Final:
            {
                Creature* gandling = Gandling();
                in.gandlingDead = _instance->GetBossState(BOSS_GANDLING) == DONE || (gandling && gandling->isDead());
                in.gandlingGone = !gandling;
                in.gandlingEngaged = gandling && gandling->IsAlive() && gandling->IsEngaged();
                in.anyInside = AnyFightingIn(GetMap(), GandlingArena());
                break;
            }
            default:
                break;
        }
        return in;
    }

    // Every player sent is in `arena` and done teleporting (or gone, or dead).
    bool GroupArrived(Arena const& arena) const
    {
        for (ObjectGuid const& guid : _sent)
        {
            Player* player = ObjectAccessor::GetPlayer(GetMap(), guid);
            if (!player || !player->IsInWorld() || !player->IsAlive())
                continue;
            if (player->IsBeingTeleported() || !arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                return false;
        }
        return true;
    }

    // ---- The steps --------------------------------------------------------------------------------------------------
    void SendGroup(Point4 const& at)
    {
        _sent.clear();
        for (auto const& ref : GetMap()->GetPlayers())
            if (Player* player = ref.GetSource(); Movable(player))
                SendOne(player, at);
    }

    void SendOne(Player* player, Point4 const& at)
    {
        if (player->GetVehicle())
            player->ExitVehicle();
        Point4 const spot = SpreadLanding(at, _sent.size());
        if (player->IsAlive())
            player->CastSpell(player, ScholoGandling::SPELL_GD_PORTAL_FLASH, true);
        player->NearTeleportTo(spot.x, spot.y, spot.z, spot.o);
        _sent.push_back(player->GetGUID());
    }

    // R-C EXAM N-5: a player who missed a portal (offline or released at the time, or a late zone-in) joins the group
    // as soon as they are back on the map, alive or not yet released, so nobody waits behind a shut gate. Players who
    // left the map or released drop off the list (they are collected again when they come back); one already in the
    // group's arena only joins the list.
    void CollectStragglers()
    {
        Point4 at;
        Arena arena;
        switch (_run.Phase())
        {
            case ExamPhase::Arriving:
            case ExamPhase::Examining:
                at = ExamRoomOf(_run.Room()).groupLanding;
                arena = ClassroomArena(_run.Room());
                break;
            case ExamPhase::Returning:
            case ExamPhase::Final:
                at = kStudyReturn;
                arena = GandlingArena();
                break;
            default:
                return;     // Opening and Portal: the next send takes everyone
        }
        Map* map = GetMap();
        std::erase_if(_sent, [map](ObjectGuid const& guid)
        {
            Player* player = ObjectAccessor::GetPlayer(map, guid);
            return !player || player->HasPlayerFlag(PLAYER_FLAGS_GHOST);
        });
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!Movable(player) || player->IsBeingTeleported()
                || std::find(_sent.begin(), _sent.end(), player->GetGUID()) != _sent.end())
                continue;
            if (arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
            {
                _sent.push_back(player->GetGUID());
                continue;
            }
            SendOne(player, at);
            ExamLog("straggler", Acore::StringFormat("player={} phase={}", player->GetName(),
                PhaseName(_run.Phase())));
        }
    }

    void SendToRoom()
    {
        Classroom const room = _run.Room();
        DespawnExaminer();
        if (GandlingFightApi* fight = GetGandlingFight(Gandling()))
        {
            fight->Abort();
            fight->SetMode(IdleMode());
            fight->SetRegion(RoomRegion(room));
        }
        SendGroup(ExamRoomOf(room).groupLanding);
        ExamNotify(GetMap(), Acore::StringFormat("Examination {} of {}: {}.", _run.RoomIndex() + 1, kClassroomCount,
            kClassroomNames[std::size_t(room)]));
        ExamLog("send", Acore::StringFormat("room={} ({} of {}) players={}", kClassroomNames[std::size_t(room)],
            _run.RoomIndex() + 1, kClassroomCount, _sent.size()));
    }

    // The whole group is in the room (or 4 s passed): the examiner rises and fights everyone in the room's arena; his
    // lanes and swaps reach in from now (their first casts at GauntletMode's 10 s and 20 s).
    void PullExaminer()
    {
        Classroom const room = _run.Room();
        ExamRoom const& r = ExamRoomOf(room);
        Creature* gandling = Gandling();
        if (!gandling)
        {
            ExamLog("pull-failed", "no Gandling");
            return;
        }
        Position const at(r.examinerSpawn.x, r.examinerSpawn.y, r.examinerSpawn.z, r.examinerSpawn.o);
        Creature* examiner = gandling->SummonCreature(r.examiner, at, TEMPSUMMON_MANUAL_DESPAWN);
        if (!examiner)
        {
            ExamLog("pull-failed", Acore::StringFormat("no examiner {}", r.examiner));
            return;
        }
        _examiner = examiner->GetGUID();
        *_examinerRef = _examiner;
        examiner->setActive(true);
        if (!examiner->HasAura(SPELL_GHOST_VISUAL))
            examiner->AddAura(SPELL_GHOST_VISUAL, examiner);
        bool const pulled = PullInto(examiner, ClassroomArena(room));   // nobody in yet: RetryPull, every tick
        if (GandlingFightApi* fight = GetGandlingFight(gandling))
        {
            fight->SetRegion(RoomRegion(room));
            fight->SetMode(GauntletMode());
        }
        ExamLog("pull", Acore::StringFormat("room={} examiner={} health={} pulled={}",
            kClassroomNames[std::size_t(room)], r.examiner, examiner->GetMaxHealth(), pulled ? 1 : 0));
    }

    // SF-1: the step's unit was never engaged yet (nobody was in the arena at its pull): pull the arena again.
    void RetryPull()
    {
        Creature* unit = _run.Phase() == ExamPhase::Final ? Gandling() : Examiner();
        if (!unit || !unit->IsAlive() || unit->IsEngaged())
            return;
        Arena const arena = _run.Phase() == ExamPhase::Final ? GandlingArena() : ClassroomArena(_run.Room());
        if (PullInto(unit, arena))
            ExamLog("pull-retry", Acore::StringFormat("phase={} unit={}", PhaseName(_run.Phase()), unit->GetEntry()));
    }

    void RoomCleared()
    {
        Classroom const room = _run.Room();
        Creature* gandling = Gandling();
        if (GandlingFightApi* fight = GetGandlingFight(gandling))
        {
            fight->Abort();
            fight->SetMode(IdleMode());
        }
        // Orchestrator ruling 2026-11-08: his lanes' Weakened ends with each room (as each examiner's does), never
        // stacking across the exam. The examiner's own encounter ended at its death; no other encounter runs here.
        BossMechanics::Weakened::Clear(GetMap());
        Point4 const& at = ExamRoomOf(room).groupLanding;
        if (gandling)
            gandling->SummonCreature(NPC_SC_PORTAL_STALKER, Position(at.x, at.y, at.z, at.o),
                TEMPSUMMON_TIMED_DESPAWN, kPortalDelayMs + 1000);
        bool const last = _run.RoomIndex() + 1 >= kClassroomCount;
        ExamNotify(GetMap(), last ? std::string("A portal opens back to the Headmaster's Study.")
            : Acore::StringFormat("Passed. A portal opens to {}.",
                kClassroomNames[std::size_t(_run.Order()[_run.RoomIndex() + 1])]));
        ExamLog("room-cleared", Acore::StringFormat("room={} cleared={}", kClassroomNames[std::size_t(room)],
            _run.RoomsCleared()));
    }

    // GD6: the group comes back; Gandling at 200k, attackable, yell line 5, his next pull in FinalExamMode.
    void ReturnToStudy()
    {
        DespawnExaminer();
        Creature* gandling = Gandling();
        if (GandlingFightApi* fight = GetGandlingFight(gandling))
        {
            fight->Abort();
            fight->SetMode(IdleMode());
            fight->SetRegion(ScholoGandling::StudyRegion());
            fight->SetTankProvider({});
            fight->SetEngageMode(ScholoGandling::FinalExamMode());
        }
        if (gandling && gandling->IsAlive())
        {
            RestoreReach(gandling);
            if (!_savedCreateHealth)
                _savedCreateHealth = gandling->GetCreateHealth();
            SetCreatureHealth(gandling, kFinalHealth);
            if (gandling->IsAIEnabled)
                gandling->AI()->Talk(YELL_GANDLING_FINAL_EXAM);
        }
        SendGroup(kStudyReturn);
        ExamLog("return", Acore::StringFormat("players={} health={}", _sent.size(),
            gandling ? gandling->GetMaxHealth() : 0));
    }

    void StartFinal()
    {
        Creature* gandling = Gandling();
        bool const pulled = gandling && gandling->IsAlive() && PullInto(gandling, GandlingArena());
        ExamLog("final", Acore::StringFormat("pulled={}", pulled ? 1 : 0));
    }

    void Passed()
    {
        _sent.clear();
        _flagsAdded.clear();
        _savedCreateHealth = 0;
        *_examinerRef = ObjectGuid::Empty;
        ExamNotify(GetMap(), "The Graduate Exam is passed.");
        ExamLog("passed");
    }

    // A wipe (or `.dbtest scholo exam stop`): everything as it was before the paper; the grades stay and the paper can
    // be signed again.
    void Reset(char const* why)
    {
        _run.Stop();
        DespawnExaminer();
        Creature* gandling = Gandling();
        if (gandling && gandling->IsAlive())
        {
            if (GandlingFightApi* fight = GetGandlingFight(gandling))
            {
                fight->Abort();
                fight->SetTankProvider({});
                fight->SetEngageMode(std::nullopt);
            }
            RestoreReach(gandling);
            if (_savedCreateHealth)
                SetCreatureHealth(gandling, _savedCreateHealth);
            gandling->setActive(false);
            // His Reset: the study region, his fight's mode, the summons gone, NOT_STARTED (the gates open).
            if (gandling->IsEngaged())
                gandling->AI()->EnterEvadeMode();
            else if (gandling->IsAIEnabled)
                gandling->AI()->Reset();
        }
        _savedCreateHealth = 0;
        if (_instance->GetBossState(BOSS_GANDLING) == IN_PROGRESS)
            _instance->SetBossState(BOSS_GANDLING, NOT_STARTED);
        _instance->SetData(DATA_GANDLING_HARD_MODE, 0);
        _sent.clear();
        ExamNotify(GetMap(), "The Graduate Exam is over. The honors program may be signed again.");
        ExamLog("reset", why);
    }

    // Gandling within reach again: the flags this exam added come off, combat is his again.
    void RestoreReach(Creature* gandling)
    {
        for (UnitFlags const flag : _flagsAdded)
            gandling->RemoveUnitFlag(flag);
        _flagsAdded.clear();
        gandling->SetIsCombatDisallowed(false);
    }

    // F-B1: an examiner still fighting ends its fight (its evade cleans its own units, the bench and the Soul meters)
    // before it despawns; a dead one only leaves.
    void DespawnExaminer()
    {
        if (Creature* examiner = Examiner())
        {
            if (examiner->IsAlive() && examiner->IsEngaged() && examiner->IsAIEnabled)
                examiner->AI()->EnterEvadeMode();
            examiner->DespawnOrUnsummon();
        }
        _examiner.Clear();
        *_examinerRef = ObjectGuid::Empty;
    }

    // ---- Grades and the stale signature -----------------------------------------------------------------------------
    void SweepGrades()
    {
        for (auto const& ref : GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsInWorld() && !player->IsBeingTeleported())
                SyncGrades(player);
        }
    }

    // A signature saved without its gauntlet (a restart mid-exam) would light the hard mode loot on a plain pull: the
    // first tick after the instance loads clears it.
    void ClearStaleSignature()
    {
        if (_run.Running() || !_instance->GetData(DATA_GANDLING_HARD_MODE)
            || _instance->GetBossState(BOSS_GANDLING) == DONE)
            return;
        _instance->SetData(DATA_GANDLING_HARD_MODE, 0);
        ExamLog("stale-signature", "cleared at load (the gauntlet did not survive the restart)");
    }

    InstanceScript* _instance;
    GauntletRun _run;
    std::shared_ptr<ObjectGuid> _examinerRef;   // the tank provider's view of the room's examiner
    ObjectGuid _examiner;
    std::vector<ObjectGuid> _sent;
    std::vector<UnitFlags> _flagsAdded;
    uint32 _savedCreateHealth = 0;
    uint32 _sweepMs = 0;
    bool _staleChecked = false;
};

namespace ScholoGraduateExam
{
    std::unique_ptr<GraduateExam> CreateGraduateExam(InstanceScript* instance)
    {
        return std::make_unique<GraduateExamDriver>(instance);
    }

    GraduateExam* GetGraduateExam(InstanceScript* instance)
    {
        InstanceApi* api = GetInstanceApi(instance);
        return api ? api->Exam() : nullptr;
    }
}

// ---- The honors program paper (301153) ------------------------------------------------------------------------------
struct go_sc_honors_paper : public GameObjectAI
{
    explicit go_sc_honors_paper(GameObject* go) : GameObjectAI(go) { }

    // Selectable while there is something to tell (the refusals too); not once he is dead or the exam runs.
    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kPaperPollMs;
        GraduateExam* exam = GetGraduateExam(me->GetInstanceScript());
        PaperRefusal const why = exam ? exam->Check() : PaperRefusal::GandlingDone;
        bool const selectable = why != PaperRefusal::GandlingDone && why != PaperRefusal::GandlingBusy;
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (selectable && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!selectable && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        InstanceScript* instance = me->GetInstanceScript();
        GraduateExam* exam = GetGraduateExam(instance);
        if (!exam)
            return true;
        PaperRefusal const why = exam->Check();
        if (why != PaperRefusal::None)
        {
            ChatHandler handler(player->GetSession());
            handler.SendNotification(PaperRefusalText(why));
            if (why == PaperRefusal::HonorsClosed)
            {
                std::string grades;
                for (std::size_t i = 0; i < kInstructorCount; ++i)
                    grades += Acore::StringFormat("{}{} {}/{}", grades.empty() ? "" : ", ", kInstructorNames[i],
                        instance->GetData(DataGradeHolders(Instructor(i))), kHonorsMinHolders);
                handler.PSendSysMessage("Passing Grades: {}.", grades);
            }
            ExamLog("paper-refused", Acore::StringFormat("by={} reason={}", player->GetName(), uint32(why)));
            return true;
        }
        exam->TrySign(player);
        return true;
    }

private:
    uint32 _pollMs = 0;
};

// ---- `.dbtest scholo exam` ------------------------------------------------------------------------------------------
namespace
{
    GraduateExam* FindExam(ChatHandler* handler)
    {
        if (!ScholoTest::RequireScholomance(handler))
            return nullptr;
        GraduateExam* exam = GetGraduateExam(handler->GetPlayer()->GetInstanceScript());
        if (!exam)
            handler->SendErrorMessage("{}", "This instance does not run instance_scholomance_rework.");
        return exam;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        GraduateExam* exam = FindExam(handler);
        if (!exam)
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        handler->PSendSysMessage("The Graduate Exam: honors program {}, signed {}, killed {}, paper: {}",
            instance->GetData(DATA_HONORS_OPEN) ? "open" : "closed", instance->GetData(DATA_GANDLING_HARD_MODE),
            instance->GetData(DATA_GANDLING_HARD_MODE_KILLED), exam->Check() == PaperRefusal::None ? "ready"
            : PaperRefusalText(exam->Check()));
        for (std::size_t i = 0; i < kInstructorCount; ++i)
            handler->PSendSysMessage("{}: {} holder(s)", kInstructorNames[i],
                instance->GetData(DataGradeHolders(Instructor(i))));
        handler->PSendSysMessage("Gauntlet: {}", exam->StateLine());
        return true;
    }

    // `.dbtest scholo exam start [room 0-5]`: signs the paper as the GM would (the same checks; grant grades first
    // with `.dbtest scholo instance grade all`), the room first when given.
    bool HandleStart(ChatHandler* handler, Optional<uint32> room)
    {
        GraduateExam* exam = FindExam(handler);
        if (!exam)
            return false;
        if (room && *room >= kClassroomCount)
        {
            handler->SendErrorMessage("{}", "Room 0-5 (ShadowVault, BarovVault, RavenianVault, HallOfSecrets, "
                "HallOfTheDamned, Coven).");
            return false;
        }
        // R-C EXAM N-2: the gauntlet moves and counts no GM (a lone tester in GM mode would wipe it on its first tick).
        if (handler->GetPlayer()->IsGameMaster())
        {
            handler->SendErrorMessage("{}", "Turn GM mode off first (.gm off): the gauntlet neither moves nor counts "
                "GMs.");
            return false;
        }
        PaperRefusal const why = exam->Check();
        if (why != PaperRefusal::None)
        {
            handler->SendErrorMessage("{}", PaperRefusalText(why));
            return false;
        }
        std::optional<Classroom> first;
        if (room)
            first = Classroom(*room);
        if (!exam->TrySign(handler->GetPlayer(), first))
        {
            handler->SendErrorMessage("{}", "The signature was refused (see the log).");
            return false;
        }
        handler->PSendSysMessage("Graduate Exam: {}", exam->StateLine());
        return true;
    }

    bool HandleSkip(ChatHandler* handler)
    {
        GraduateExam* exam = FindExam(handler);
        if (!exam)
            return false;
        std::string const err = exam->SkipRoom();
        if (!err.empty())
        {
            handler->SendErrorMessage("{}", err);
            return false;
        }
        handler->PSendSysMessage("{}", "Graduate Exam: the examiner dies; the portal follows.");
        return true;
    }

    bool HandleFinal(ChatHandler* handler)
    {
        GraduateExam* exam = FindExam(handler);
        if (!exam)
            return false;
        std::string const err = exam->SkipToFinal();
        if (!err.empty())
        {
            handler->SendErrorMessage("{}", err);
            return false;
        }
        handler->PSendSysMessage("{}", "Graduate Exam: back to the study for the final phase.");
        return true;
    }

    bool HandleStop(ChatHandler* handler)
    {
        GraduateExam* exam = FindExam(handler);
        if (!exam)
            return false;
        exam->Stop("test command");
        handler->PSendSysMessage("Graduate Exam: {}", exam->StateLine());
        return true;
    }

    bool HandleGrades(ChatHandler* handler)
    {
        GraduateExam* exam = FindExam(handler);
        if (!exam)
            return false;
        for (auto const& ref : handler->GetPlayer()->GetMap()->GetPlayers())
            exam->SyncGrades(ref.GetSource());
        handler->PSendSysMessage("{}", "Graduate Exam: Passing Grade auras synced on every player of the map.");
        return true;
    }

    ChatCommandTable const& ExamTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "start",  HandleStart,  SEC_GAMEMASTER, Console::No },
            { "skip",   HandleSkip,   SEC_GAMEMASTER, Console::No },
            { "final",  HandleFinal,  SEC_GAMEMASTER, Console::No },
            { "stop",   HandleStop,   SEC_GAMEMASTER, Console::No },
            { "grades", HandleGrades, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_scholo_graduate_exam()
{
    RegisterDungeonReworkGameObjectAI(go_sc_honors_paper, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("exam", ExamTestCommands());
}
