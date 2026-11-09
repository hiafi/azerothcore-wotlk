/*
 * mod-dungeon-bosses, Scholomance S11:
 * Darkmaster Gandling (1853), normal and heroic, and the detention cycle that runs the six instructors' solo lessons.
 * Build spec: docs/dungeons/scholomance-rework.md SC 3034-3101 (Build spec), SC 2944-3023 (core loop, numbers and the
 * six lessons), each instructor's "Detention" notes; handoff sections 3.5 row S11, 3.6, 3.7, 3.8. The hard mode (the
 * Graduate Exam) is S13's: graduate_exam.cpp drives this AI through GandlingFight.h.
 *
 * Hidden until the sixth instructor dies: Reset applies the instance's DATA_GANDLING_REVEALED (ApplyGandlingReveal);
 * the instance says "School is in session!" through this AI and calls DoAction(kActionGandlingRevealed). The
 * instance's door data shuts the entrance 177374 and the six classroom gates while he fights and opens them on his
 * death, a wipe or an evade.
 *
 *   GD1 Detention       first at 15 s, every 25 s: a 1 s cast bar on a random player in the study (never the tank,
 *                       never the player just back, never one under Honor Roll; yell line 1), then the portal: the
 *                       student lands on the stock landing point of a classroom (spell_target_position of 17863,
 *                       17939, 17943, 17944, 17946, 17948; kClassroomLandings) that has not held detention this cycle,
 *                       behind its shut gate. The room's lesson (the instructor WPs' TimedSoloLesson, CreateSoloLesson)
 *                       runs 15 s under a lesson stalker (300546), then a portal brings the student back to the spot
 *                       they left, held until no lane fires within 1.5 s of their landing (R-C GANDLING S-3). The
 *                       six rooms reopen in a new random order once all six were used. A room is passed over while
 *                       its instructor or a Graduate Examiner fights in it (F-B1) or another player stands on its
 *                       side of the gate (its arena or the corridor to it, ClassroomSide). The student's pet and
 *                       guardians go with them as they land and come back with them (a creature would walk through
 *                       the shut gate). Never a vehicle passenger (the Work Bench patient).
 *   GD2 Honor Roll      a passed lesson: +100% damage and healing done for 15 s (206332, self-applied).
 *   GD3 Expelled        a failed lesson: an Expelled Student (300544; heroic copy 310119) rises beside the student,
 *                       fixated on them and not tauntable, until killed. Heroic: +10% damage every 10 s alive.
 *   GD4 Portal Volley   first at 10 s, every 20 s: a 2 s cast bar (emote line 2), then 2 / 3 portals (300547) open on
 *                       the study's edge, each lane (4 yd) aimed through a random non-tank player to the far wall,
 *                       2 s warning, 30% / 40% Arcane + Weakened. Heroic: the lanes linger 4 s.
 *   GD4b Transfer (H)   first at 20 s, every 30 s: two random players in the study (the tank too) are marked (2 s,
 *                       emote line 3), then swap places; a swapped tank takes Gandling along (onto the study's
 *                       floor). No lane fires within 1.5 s after a swap (the swap waits). Never a vehicle passenger.
 *
 * Detention safety (handoff 3.7): who is detained where is the instance's DataDetained(room), written before the
 * teleport and cleared when the lesson ends (the playerbots strategy vanilla-scholo keys on it). A lesson that ends
 * with no verdict (the student died, left, is the last one alive) opens the room's gate. A wipe, his evade or his death
 * aborts the lesson (its OnEnd ejects the Work Bench seat and despawns its units), sends a living student (and their
 * pets) back to the spot they left at once, and the door data opens every gate.
 * The lesson stalker is summoned but never zoned into combat, and its own summons (the fortunes, specimens, the bench,
 * the echo) are never zoned either (F-B3): npc_sc_lesson_stalker does nothing at all.
 *
 * Retired from the stock kit: Shadow Portal 17950 and the Risen Guardians 11598, Arcane Missiles 15790, Curse of the
 * Darkmaster 18702, Shadow Shield 12040; his 12 dormant SmartAI rows go in this WP's SQL rev. The stock
 * boss_darkmaster_gandling file stays untouched (this is a new script name).
 *
 * Pilot lessons: the timeline runs on events processed while he casts (only a cast bar waits for another); the lanes
 * are the registry's (custom resolve copies, Weakened); every lane hit shows a missile out of its portal.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureTextMgr.h"
#include "DungeonKit.h"
#include "GandlingFight.h"
#include "GandlingLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SoloLesson.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <cmath>
#include <memory>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoGandling;

namespace
{
    char const* const kBossLogName = "gandling";
    char const* const kDetentionLogName = "detention";

    uint32 constexpr kStalkerLifeMs = 30000;        // backstop: a lesson stalker outlives no lesson by long
    uint32 constexpr kExpelledCorpseMs = 10000;
    uint8 constexpr kExpelledRiseText = 0;          // creature_text 300544 group 0: the rise emote (type 41)

    enum GandlingEvents : uint32
    {
        EVENT_DETENTION = 1,
        EVENT_DETENTION_SEND,
        EVENT_VOLLEY,
        EVENT_VOLLEY_OPEN,
        EVENT_VOLLEY_FIRE,
        EVENT_VOLLEY_STREAM,
        EVENT_TRANSFER,
        EVENT_TRANSFER_SWAP,
    };

    std::size_t RandIndex(std::size_t n)
    {
        return n ? std::size_t(urand(0, uint32(n) - 1)) : 0;
    }

    Position ToPos(DungeonKit::Vec2 p, float z, float o = 0.f)
    {
        return DungeonKit::ToPosition(p, z, o);
    }
}

// ---- The lesson and portal stalkers (300546, 300547): no AI at all ------------------------------------------------
// A lesson's owner: its spells hit the student (hostile faction 14), its summons are the lesson's units. It never
// zones anything into combat and never fights (F-B3, STAGE-S5 "For S11").
struct npc_sc_lesson_stalker : public NullCreatureAI
{
    explicit npc_sc_lesson_stalker(Creature* creature) : NullCreatureAI(creature) { }
    void JustSummoned(Creature* /*summon*/) override { }
};

// A portal on the study's edge (GD4) or the detention return (look only).
struct npc_sc_portal_stalker : public NullCreatureAI
{
    explicit npc_sc_portal_stalker(Creature* creature) : NullCreatureAI(creature) { }
};

// ---- GD3 the Expelled Student (300544) -----------------------------------------------------------------------------
struct npc_sc_expelled_student : public ScriptedAI
{
    explicit npc_sc_expelled_student(Creature* creature) : ScriptedAI(creature) { }

    // Gandling raises it beside `student` (fixated, not tauntable) on a failed detention or a final-phase swap.
    void Configure(Player* student, bool heroic)
    {
        _student = student ? student->GetGUID() : ObjectGuid::Empty;
        _heroic = heroic;
        _aliveMs = 0;
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_ATTACK_ME, true);
        me->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TAUNT, true);
        if (!student)
            return;
        if (sCreatureTextMgr->TextExist(me->GetEntry(), kExpelledRiseText))
            Talk(kExpelledRiseText, student);
        me->GetThreatMgr().FixateTarget(student);
        AttackStart(student);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        _aliveMs += diff;
        if (_heroic && ExpelledGrowthStacks(_aliveMs) > me->GetAuraCount(SPELL_GD_EXPELLED_GROWTH))
            me->CastSpell(me, SPELL_GD_EXPELLED_GROWTH, true);

        // Its student gone (dead, released, out of the map): it turns on the group like any add. Its student detained
        // again: it never follows them through the shut gate (the navmesh does not know the gate); it holds the
        // nearest player in the study until they are back.
        _checkMs += diff;
        if (_checkMs >= 1000)
        {
            _checkMs = 0;
            Player* student = _student ? ObjectAccessor::GetPlayer(*me, _student) : nullptr;
            if (!student || !student->IsAlive())
            {
                _student.Clear();
                me->GetThreatMgr().ClearFixate();
            }
            else if (IsDetained(student->GetGUID()))
            {
                if (Player* other = NearestFreePlayer())
                    me->GetThreatMgr().FixateTarget(other);
            }
            else
                me->GetThreatMgr().FixateTarget(student);
        }

        DoMeleeAttackIfReady();
    }

private:
    bool IsDetained(ObjectGuid guid) const
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return false;
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            if (instance->GetGuidData(DataDetained(Classroom(i))) == guid)
                return true;
        return false;
    }

    Player* NearestFreePlayer() const
    {
        Player* best = nullptr;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsAlive() || p->IsGameMaster() || IsDetained(p->GetGUID())
                || !GandlingArena().Contains(DungeonKit::PlaneOf(p), p->GetPositionZ()))
                continue;
            if (!best || me->GetExactDist2d(p) < me->GetExactDist2d(best))
                best = p;
        }
        return best;
    }

    ObjectGuid _student;
    bool _heroic = false;
    uint32 _aliveMs = 0;
    uint32 _checkMs = 0;
};

// ---- Darkmaster Gandling --------------------------------------------------------------------------------------------
struct boss_darkmaster_gandling_rework : public BossAI, public GandlingFightApi
{
    explicit boss_darkmaster_gandling_rework(Creature* creature)
        : BossAI(creature, BOSS_GANDLING), _arena(GandlingArena(), LeashOptions(kBossLogName)),
        _region(StudyRegion()), _mode(FightMode(false)) { }

    // ---- GandlingFightApi (S13) -------------------------------------------------------------------------------------
    void SetMode(GandlingMode const& mode) override
    {
        _mode = mode;
        events.Reset();
        _volleyPortals.clear();
        // A bar in flight loses its follow-up event: drop it (a student already sent keeps their lesson).
        if (_det.phase == DetentionPhase::Casting)
            _det = Detention();
        ClearTransferMarks();
        if (_mode.detention)
            events.ScheduleEvent(EVENT_DETENTION, Milliseconds(_mode.detentionFirstMs));
        if (_mode.volley)
            events.ScheduleEvent(EVENT_VOLLEY, Milliseconds(_mode.volleyFirstMs));
        if (_mode.transfer)
            events.ScheduleEvent(EVENT_TRANSFER, Milliseconds(_mode.transferFirstMs));
    }

    GandlingMode const& Mode() const override { return _mode; }

    void SetRegion(GandlingRegion const& region) override { _region = region; }

    void SetTankProvider(std::function<ObjectGuid()> tank) override { _tankProvider = std::move(tank); }

    void Abort() override
    {
        AbortDetention("abort");
        events.CancelEvent(EVENT_VOLLEY_OPEN);
        events.CancelEvent(EVENT_VOLLEY_FIRE);
        events.CancelEvent(EVENT_VOLLEY_STREAM);
        events.CancelEvent(EVENT_TRANSFER_SWAP);
        _volleyPortals.clear();
        _laneFires.clear();
        ClearTransferMarks();
    }

    bool DetentionRunning() const override { return _det.phase != DetentionPhase::Idle; }

    void SetEngageMode(std::optional<GandlingMode> mode) override { _engageMode = mode; }

    void RaiseExpelled(ObjectGuid studentGuid) override
    {
        Player* student = ObjectAccessor::GetPlayer(*me, studentGuid);
        if (student)
            RaiseExpelledAt(student, student->GetPosition());
    }

    // ---- BossAI ---------------------------------------------------------------------------------------------------
    void Reset() override
    {
        Abort();
        _Reset();
        _arena.Reset();
        _cycle.Reset();
        _lastBack.Clear();
        _victim.Clear();
        _prevVictim.Clear();
        _region = StudyRegion();
        _mode = FightMode(DungeonKit::IsHeroicMap(me));
        _engageMode.reset();
        _clockMs = 0;
        // Hidden until the six instructors are DONE (stock: Reset read the raw counter).
        ApplyGandlingReveal(me, instance && instance->GetData(DATA_GANDLING_REVEALED));
        // _Reset's ResetLootMode drops the instance's hard mode loot bit; put it back while the honors are signed.
        if (instance && instance->GetData(DATA_GANDLING_HARD_MODE) && instance->GetBossState(BOSS_GANDLING) != DONE)
            DungeonKit::SetHardModeLoot(me, true);
    }

    void DoAction(int32 action) override
    {
        if (action == kActionGandlingRevealed)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "revealed");
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GANDLING;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        bool const heroic = DungeonKit::IsHeroicMap(me);
        _region = StudyRegion();
        // S13's final phase hands its own mode (FinalExamMode) before the pull.
        SetMode(_engageMode ? *_engageMode : FightMode(heroic));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} hardmode={} at=({:.1f}, {:.1f}, {:.1f})", heroic ? 1 : 0,
                instance ? instance->GetData(DATA_GANDLING_HARD_MODE) : 0, me->GetPositionX(), me->GetPositionY(),
                me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Abort();
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Abort();
        Talk(YELL_GANDLING_DEATH);
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death", killer ? killer->GetName() : "none");
    }

    // The stalkers never fight (and never zone their own summons): only the Expelled Students join his combat.
    void JustSummoned(Creature* summon) override
    {
        if (summon && summon->GetEntry() == NPC_SC_EXPELLED_STUDENT)
            BossAI::JustSummoned(summon);
        else
            summons.Summon(summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // The lesson runs on its own clock, whatever he does (casting, holding at the edge).
        UpdateDetention(diff);

        if (_mode.needsVictim)
        {
            if (!UpdateVictim())
                return;
            NoteVictim();
            if (!_arena.Update(me, diff))
                return;     // off the study, or nobody in it for 10 s: evading
        }

        events.Update(diff);
        while (uint32 const id = events.ExecuteEvent())
            ExecuteFightEvent(id);

        if (!_mode.needsVictim || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- `.dbtest scholo gandling` ----------------------------------------------------------------------------------
    std::string StateLine() const
    {
        std::string left;
        for (Classroom c : _cycle.Left())
            left += Acore::StringFormat("{}{}", left.empty() ? "" : ",", uint32(c));
        return Acore::StringFormat("mode: detention={} volley={}x{}{} linger={}ms transfer={}{} | detention phase={} "
            "room={} student={} | cycle left=[{}] last back={} | lanes pending={}",
            _mode.detention ? 1 : 0, _mode.volley ? 1 : 0, _mode.volleyPortals,
            _mode.lanesThroughEveryone ? " (everyone)" : "", _mode.lingerMs, _mode.transfer ? 1 : 0,
            _mode.transferRaisesExpelled ? " (raises)" : "", PhaseName(_det.phase),
            _det.room ? kClassroomNames[std::size_t(*_det.room)] : "-", _det.student.ToString(), left,
            _lastBack.ToString(), _volleyPortals.size());
    }

    // Forces the next detention now (on `student` when given, into `room` when given). Empty: started.
    std::string ForceDetention(Player* student, Optional<uint32> room)
    {
        if (!me->IsEngaged())
            return "Gandling must be in combat.";
        if (_det.phase != DetentionPhase::Idle)
            return "A detention is already running.";
        if (room && *room >= kClassroomCount)
            return "Room 0-5 (ShadowVault, BarovVault, RavenianVault, HallOfSecrets, HallOfTheDamned, Coven).";
        _forcedRoom.reset();
        if (room)
            _forcedRoom = Classroom(*room);
        if (BeginDetention(student))
            return std::string();
        _forcedRoom.reset();        // R-C GANDLING N-7: a failed force never restricts the next natural detention
        return std::string("No student or room qualifies now.");
    }

    void ForceVolley() { events.RescheduleEvent(EVENT_VOLLEY, 0ms); }

    void ForceTransfer() { StartTransfer(); }

    void ForceHonorRoll(Player* player)
    {
        if (player)
            player->CastSpell(player, SPELL_GD_HONOR_ROLL, true);
    }

private:
    enum class DetentionPhase : uint8
    {
        Idle,
        Casting,        // his 1 s bar on the student
        Arriving,       // teleported, not yet in the room
        Running,        // the lesson runs
        Holding,        // the verdict is in; the return waits for the lane gap (ReturnHoldMs), still detained
        Returning,      // back through the portal, not yet in the study
    };

    static char const* PhaseName(DetentionPhase p)
    {
        switch (p)
        {
            case DetentionPhase::Idle:      return "idle";
            case DetentionPhase::Casting:   return "casting";
            case DetentionPhase::Arriving:  return "arriving";
            case DetentionPhase::Running:   return "running";
            case DetentionPhase::Holding:   return "holding";
            case DetentionPhase::Returning: return "returning";
        }
        return "?";
    }

    struct Detention
    {
        DetentionPhase phase = DetentionPhase::Idle;
        ObjectGuid student;
        ObjectGuid stalker;
        std::optional<Classroom> room;
        Position departure;
        uint32 timerMs = 0;
        bool passed = false;
    };

    struct VolleyPortal
    {
        ObjectGuid portal;
        Position end;
    };

    // Boss data (SC): target priority the Expelled Students over him; no interrupts (the bench in detention has its
    // own button), no dispels; the stalkers are never targets.
    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_SC_EXPELLED_STUDENT, 2, Who::Any);
        d.targets.emplace_back(NPC_GANDLING, 1, Who::Any);
        d.ignores.emplace_back(NPC_SC_LESSON_STALKER);
        d.ignores.emplace_back(NPC_SC_PORTAL_STALKER);
        Mechanic::Describe(me, std::move(d));
    }

    ObjectGuid TankGuid() const
    {
        if (_tankProvider)
            return _tankProvider();
        Unit const* victim = me->GetVictim();
        return victim ? victim->GetGUID() : ObjectGuid::Empty;
    }

    // R-C GANDLING N-5: whom he hit until a moment ago (the real tank, while a DPS holds him for a second).
    void NoteVictim()
    {
        Unit const* victim = me->GetVictim();
        ObjectGuid const now = victim ? victim->GetGUID() : ObjectGuid::Empty;
        if (now == _victim)
            return;
        _prevVictim = _victim;
        _victim = now;
        _victimChangedMs = _clockMs;
    }

    // The tank for the picks: TankGuid(), or (his own fight) the victim he had until kRecentTankMs ago.
    bool CountsAsTank(ObjectGuid guid, ObjectGuid tank) const
    {
        if (guid == tank)
            return true;
        return !_tankProvider && _prevVictim && guid == _prevVictim && _clockMs - _victimChangedMs < kRecentTankMs;
    }

    bool InRegion(WorldObject const* o) const
    {
        return o && _region.players.Contains(DungeonKit::PlaneOf(o), o->GetPositionZ());
    }

    // On the classroom's side of its gate (its arena or the corridor to it), alive or dead.
    static bool OnRoomSide(WorldObject const* o, Classroom room)
    {
        return o && ClassroomSide(room).Contains(DungeonKit::PlaneOf(o), o->GetPositionZ());
    }

    bool IsDetainedNow(ObjectGuid guid) const
    {
        if (_det.phase != DetentionPhase::Idle && guid == _det.student)
            return true;
        if (!instance)
            return false;
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            if (instance->GetGuidData(DataDetained(Classroom(i))) == guid)
                return true;
        return false;
    }

    // Every non-GM player on the map, with the pick rules' flags; `guids` parallel.
    std::vector<Candidate> Candidates(std::vector<ObjectGuid>& guids) const
    {
        std::vector<Candidate> out;
        guids.clear();
        ObjectGuid const tank = TankGuid();
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsInWorld() || p->IsGameMaster())
                continue;
            Candidate c;
            c.id = p->GetGUID().GetRawValue();
            c.inRegion = InRegion(p) && !p->IsBeingTeleported();
            c.onFloor = _region.clip.Contains(DungeonKit::PlaneOf(p), p->GetPositionZ());
            c.passenger = p->GetVehicle() != nullptr;
            c.alive = p->IsAlive();
            c.tank = CountsAsTank(p->GetGUID(), tank);
            c.detained = IsDetainedNow(p->GetGUID());
            c.justBack = p->GetGUID() == _lastBack;
            c.honorRoll = p->HasAura(SPELL_GD_HONOR_ROLL);
            out.push_back(c);
            guids.push_back(p->GetGUID());
        }
        return out;
    }

    // ---- GD1 Detention ----------------------------------------------------------------------------------------------
    RoomState RoomStateOf(Classroom room, ObjectGuid student) const
    {
        RoomState s;
        s.hasLesson = HasSoloLesson(room);
        if (instance)
            s.instructorFighting = instance->GetBossState(InstructorBoss(ClassroomInstructor(room))) == IN_PROGRESS;
        // The examiners exist only in the Graduate Exam: look only while it is signed.
        if (instance && instance->GetData(DATA_GANDLING_HARD_MODE))
            for (uint32 const entry : ExaminersOf(room))
                if (Creature* examiner = me->FindNearestCreature(entry, 250.f, true))
                    s.examinerFighting = s.examinerFighting || examiner->IsInCombat();
        // Its side of the gate, the corridor too (R-C GANDLING S-2: a healer gone through an opened gate to a body).
        Arena const side = ClassroomSide(room);
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (p && p->IsAlive() && !p->IsGameMaster() && p->GetGUID() != student
                && side.Contains(DungeonKit::PlaneOf(p), p->GetPositionZ()))
                s.othersInside = true;
        }
        return s;
    }

    bool RoomOpen(Classroom room, ObjectGuid student) const
    {
        return RoomOpenForDetention(RoomStateOf(room, student));
    }

    // Starts the 1 s cast on `forced` (or a random qualifying student). False: nobody or no room qualifies now.
    bool BeginDetention(Player* forced = nullptr)
    {
        std::vector<ObjectGuid> guids;
        std::vector<Candidate> const c = Candidates(guids);
        Player* student = forced;
        if (!student)
        {
            std::optional<std::size_t> const i = PickDetentionStudent(c, RandIndex);
            if (!i)
                return false;
            student = ObjectAccessor::GetPlayer(*me, guids[*i]);
        }
        if (!student || !student->IsAlive() || student->GetVehicle())
            return false;
        // Some room must be able to take them (the room itself is picked as they go).
        bool anyRoom = false;
        for (std::size_t r = 0; r < kClassroomCount && !anyRoom; ++r)
            anyRoom = RoomOpen(Classroom(r), student->GetGUID()) && (!_forcedRoom || *_forcedRoom == Classroom(r));
        if (!anyRoom)
            return false;

        _det = Detention();
        _det.phase = DetentionPhase::Casting;
        _det.student = student->GetGUID();
        DungeonKit::CastBar(me, SPELL_GD_DETENTION_CAST, student, uint8(YELL_GANDLING_DETENTION), student);
        events.ScheduleEvent(EVENT_DETENTION_SEND, Milliseconds(kDetentionCastMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "detention-cast", student->GetName());
        return true;
    }

    void SendStudent()
    {
        Player* student = ObjectAccessor::GetPlayer(*me, _det.student);
        if (!student || !student->IsAlive() || !InRegion(student) || student->IsBeingTeleported()
            || student->GetVehicle())
        {
            DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "cancelled", "the student is gone");
            CancelSend();
            return;
        }

        std::optional<Classroom> room;
        if (_forcedRoom)
        {
            if (RoomOpen(*_forcedRoom, _det.student))
                room = _forcedRoom;
            _forcedRoom.reset();
        }
        else
            room = _cycle.Next([this](Classroom c) { return RoomOpen(c, _det.student); }, RandIndex);
        if (!room)
        {
            DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "cancelled", "no room open");
            CancelSend();
            return;
        }

        Point4 const& landing = kClassroomLandings[std::size_t(*room)];
        Position const at(landing.x, landing.y, landing.z, landing.o);
        _det.room = room;
        _det.departure = student->GetPosition();
        // PB contract: the detained slot is set before the teleport (the bot strategy stops following through the
        // gate); the gate is shut already (door data), shut it again in case a safety end left it open.
        if (instance)
        {
            instance->SetGuidData(DataDetained(*room), _det.student);
            instance->SetData(DataClassroomGate(*room), 0);
        }
        if (Creature* stalker = me->SummonCreature(NPC_SC_LESSON_STALKER, at, TEMPSUMMON_TIMED_DESPAWN,
            kStalkerLifeMs))
            _det.stalker = stalker->GetGUID();
        student->CastSpell(student, SPELL_GD_PORTAL_FLASH, true);
        student->NearTeleportTo(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), at.GetOrientation());
        _det.phase = DetentionPhase::Arriving;
        _det.timerMs = 0;
        DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "send",
            Acore::StringFormat("student={} room={}", student->GetName(), kClassroomNames[std::size_t(*room)]));
    }

    // R-C GANDLING N-4: a send that found no student or room looks again soon, not a whole cooldown later.
    void CancelSend()
    {
        _det = Detention();
        if (_mode.detention)
            events.RescheduleEvent(EVENT_DETENTION, Milliseconds(kDetentionRetryMs));
    }

    void UpdateDetention(uint32 diff)
    {
        switch (_det.phase)
        {
            case DetentionPhase::Idle:
            case DetentionPhase::Casting:
                return;
            case DetentionPhase::Arriving:
            {
                _det.timerMs += diff;
                Player* student = ObjectAccessor::GetPlayer(*me, _det.student);
                if (!student || !student->IsAlive())
                {
                    EndWithoutVerdict("the student died or left before the lesson");
                    return;
                }
                Arena const arena = ClassroomArena(*_det.room);
                bool const landed = !student->IsBeingTeleported()
                    && arena.Contains(DungeonKit::PlaneOf(student), student->GetPositionZ());
                if (landed)
                {
                    // Their pet and guardians join them now (the server moves the student only here, so until now
                    // the pets had no reason to walk at the gate).
                    MovePets(student, student->GetPosition());
                    StartLesson(student);
                    return;
                }
                if (_det.timerMs >= kArrivalTimeoutMs)
                    EndWithoutVerdict("the student never reached the room");
                return;
            }
            case DetentionPhase::Running:
            {
                if (!_lesson)
                {
                    EndWithoutVerdict("no lesson");
                    return;
                }
                _lesson->Update(diff);
                if (_lesson->Done())
                    LessonDone();
                return;
            }
            case DetentionPhase::Holding:
            {
                Player* student = ObjectAccessor::GetPlayer(*me, _det.student);
                if (!student || !student->IsAlive())
                {
                    ClearDetained();
                    OpenGate();
                    DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "ended",
                        "the student died or left before the return: the gate opens");
                    _det = Detention();
                    return;
                }
                if (ReturnHoldMs(_clockMs, _laneFires) == 0)
                    ReturnStudent(student);
                return;
            }
            case DetentionPhase::Returning:
            {
                _det.timerMs += diff;
                Player* student = ObjectAccessor::GetPlayer(*me, _det.student);
                if (!student)
                {
                    _det = Detention();
                    return;
                }
                bool const back = !student->IsBeingTeleported() && InRegion(student);
                if (back)
                {
                    MovePets(student, student->GetPosition());
                    ReportCard(student);
                    return;
                }
                if (_det.timerMs < kArrivalTimeoutMs)
                    return;
                // R-C GANDLING N-3: the return never landed (a client stall). Still behind the gate: open it, and no
                // report card (an Expelled Student would rise in the room and run through the gate).
                if (_det.room && OnRoomSide(student, *_det.room))
                {
                    OpenGate();
                    DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "ended",
                        "the return never landed: the gate opens");
                    _det = Detention();
                    return;
                }
                ReportCard(student);
                return;
            }
        }
    }

    void StartLesson(Player* student)
    {
        Creature* stalker = me->GetMap()->GetCreature(_det.stalker);
        _lesson = CreateSoloLesson(*_det.room);
        if (!_lesson || !stalker)
        {
            EndWithoutVerdict(!stalker ? "no lesson stalker" : "no lesson registered");
            return;
        }
        _det.phase = DetentionPhase::Running;
        _lesson->Start(stalker, student, DungeonKit::IsHeroicMap(me));
    }

    void LessonDone()
    {
        bool const passed = _lesson->Passed();
        bool const verdict = passed || _lesson->Failed();
        _lesson.reset();
        DespawnStalker();

        Player* student = ObjectAccessor::GetPlayer(*me, _det.student);
        if (!verdict || !student || !student->IsAlive())
        {
            // A safety end (the student died, left, is the last one alive): no report card; the gate opens so the
            // group can reach them (or they can walk out).
            ClearDetained();
            OpenGate();
            DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "ended", "no verdict: the gate opens");
            _det = Detention();
            return;
        }

        // The verdict is in: they go back once no lane fires within 1.5 s of their landing (R-C GANDLING S-3). They
        // stay detained meanwhile (the bots keep still), at most a lane's 1.6 s.
        _det.passed = passed;
        _det.phase = DetentionPhase::Holding;
        if (ReturnHoldMs(_clockMs, _laneFires) == 0)
            ReturnStudent(student);
        else
            DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "return-held", student->GetName());
    }

    // The portal back to where they stood. The detained slot clears before the teleport (PB contract).
    void ReturnStudent(Player* student)
    {
        ClearDetained();
        _det.phase = DetentionPhase::Returning;
        _det.timerMs = 0;
        Position const& back = _det.departure;
        if (Creature* portal = me->SummonCreature(NPC_SC_PORTAL_STALKER, student->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, 2000))
            portal->SetFacingToObject(student);
        student->CastSpell(student, SPELL_GD_PORTAL_FLASH, true);
        student->NearTeleportTo(back.GetPositionX(), back.GetPositionY(), back.GetPositionZ(), back.GetOrientation());
        DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "return",
            Acore::StringFormat("student={} verdict={}", student->GetName(), _det.passed ? "pass" : "fail"));
    }

    // F-C ruling: a detained student's pet and guardians go with them and come back with them (a creature walks
    // through a shut gate: the navmesh does not know it). Called once the student has landed (the server moves
    // them only then), or at once on an abort. Their totems stay; a charmed unit is not theirs.
    void MovePets(Player* student, Position const& to)
    {
        if (!student)
            return;
        std::vector<Unit*> const units(student->m_Controlled.begin(), student->m_Controlled.end());
        for (Unit* u : units)
        {
            Creature* c = u ? u->ToCreature() : nullptr;
            if (!c || !c->IsInWorld() || !c->IsAlive() || c->IsTotem() || c->GetOwnerGUID() != student->GetGUID()
                || c->GetMap() != student->GetMap())
                continue;
            c->AttackStop();        // never chase a target on the other side of the gate
            c->NearTeleportTo(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), to.GetOrientation());
        }
    }

    // GD2 / GD3 once the student stands in the study again.
    void ReportCard(Player* student)
    {
        if (!student->IsAlive())
        {
            _det = Detention();
            return;
        }
        student->CastSpell(student, SPELL_GD_PORTAL_FLASH, true);
        if (_det.passed)
        {
            student->CastSpell(student, SPELL_GD_HONOR_ROLL, true);
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "honor-roll", student->GetName());
        }
        else
            RaiseExpelledAt(student, student->GetPosition());
        _lastBack = student->GetGUID();
        _det = Detention();
    }

    void EndWithoutVerdict(char const* why)
    {
        if (_lesson && !_lesson->Done())
            _lesson->Abort();
        _lesson.reset();
        DespawnStalker();
        ClearDetained();
        // R-C GANDLING N-2: the gate opens only for a student behind it (alive or not); a lower gate is inside his
        // arena, so an open one lets the group kite him into an empty vault.
        Player* student = ObjectAccessor::GetPlayer(*me, _det.student);
        if (_det.room && OnRoomSide(student, *_det.room))
            OpenGate();
        DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "ended", why);
        _det = Detention();
    }

    // A wipe, his evade or death, a phase change (S13): the lesson stops now (its OnEnd ejects the bench and despawns
    // its units). F-C ruling: a living student goes back to the spot they left at once, with their pets; a dead one
    // stays, and their gate opens (the door data opens every gate as well when his boss state leaves IN_PROGRESS).
    void AbortDetention(char const* why)
    {
        events.CancelEvent(EVENT_DETENTION_SEND);
        if (_det.phase == DetentionPhase::Idle)
            return;
        bool const sent = _det.phase == DetentionPhase::Arriving || _det.phase == DetentionPhase::Running
            || _det.phase == DetentionPhase::Holding;
        if (_lesson && !_lesson->Done())
            _lesson->Abort();
        _lesson.reset();
        DespawnStalker();
        ClearDetained();
        if (sent)
        {
            Player* student = ObjectAccessor::GetPlayer(*me, _det.student);
            if (student && student->IsAlive() && student->IsInWorld())
            {
                Position const& back = _det.departure;
                student->CastSpell(student, SPELL_GD_PORTAL_FLASH, true);
                student->NearTeleportTo(back.GetPositionX(), back.GetPositionY(), back.GetPositionZ(),
                    back.GetOrientation());
                MovePets(student, back);
                DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "sent-back", student->GetName());
            }
            else
                OpenGate();
        }
        DungeonKit::LogMechanic(kLogDungeon, kDetentionLogName, "aborted", why);
        _det = Detention();
        _forcedRoom.reset();
    }

    void ClearDetained()
    {
        if (instance && _det.room && instance->GetGuidData(DataDetained(*_det.room)) == _det.student)
            instance->SetGuidData(DataDetained(*_det.room), ObjectGuid::Empty);
    }

    void OpenGate()
    {
        if (instance && _det.room)
            instance->SetData(DataClassroomGate(*_det.room), 1);
    }

    void DespawnStalker()
    {
        if (Creature* stalker = me->GetMap()->GetCreature(_det.stalker))
            stalker->DespawnOrUnsummon();
        _det.stalker.Clear();
    }

    void RaiseExpelledAt(Player* student, Position const& at)
    {
        if (!student)
            return;
        float const angle = frand(0.f, 2.f * float(M_PI));
        Position const pos(at.GetPositionX() + kExpelledSpawnYd * std::cos(angle),
            at.GetPositionY() + kExpelledSpawnYd * std::sin(angle), at.GetPositionZ(), angle + float(M_PI));
        Creature* expelled = me->SummonCreature(NPC_SC_EXPELLED_STUDENT, pos, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
            kExpelledCorpseMs);
        if (!expelled)
            return;
        if (npc_sc_expelled_student* ai = dynamic_cast<npc_sc_expelled_student*>(expelled->AI()))
            ai->Configure(student, DungeonKit::IsHeroicMap(me));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "expelled", student->GetName());
    }

    // ---- GD4 Portal Volley ------------------------------------------------------------------------------------------
    void OpenPortals()
    {
        PruneLaneFires();       // R-C GANDLING N-8: the list stays short without a Transfer too
        std::vector<ObjectGuid> guids;
        std::vector<Candidate> const c = Candidates(guids);
        std::vector<std::size_t> const targets = _mode.lanesThroughEveryone ? EveryLaneTarget(c)
            : PickLaneTargets(c, _mode.volleyPortals, false, RandIndex);
        if (targets.empty() || _region.portalPoints.empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "portal-volley", "no target");
            return;
        }
        std::vector<std::size_t> const points = PickPortalPoints(_region.portalPoints.size(), targets.size(),
            RandIndex);
        bool const heroic = DungeonKit::IsHeroicMap(me);
        uint32 const lingerMs = _mode.lingerMs;
        Map* map = me->GetMap();
        _volleyPortals.clear();
        for (std::size_t i = 0; i < targets.size(); ++i)
        {
            Player* target = ObjectAccessor::GetPlayer(*me, guids[targets[i]]);
            if (!target)
                continue;
            DungeonKit::Vec2 const from = _region.portalPoints[points[i]];
            DungeonKit::LinePath const path = VolleyLane(_region, from, DungeonKit::PlaneOf(target));
            if (path.length <= 0.f)
                continue;
            float const z = _region.floorZ;
            Position const start = ToPos(path.from, z, path.facing);
            Creature* portal = me->SummonCreature(NPC_SC_PORTAL_STALKER, start, TEMPSUMMON_TIMED_DESPAWN,
                kVolleyWarnMs + lingerMs + 1500);
            ObjectGuid const portalGuid = portal ? portal->GetGUID() : ObjectGuid::Empty;
            // Every hit shows a missile out of its portal (capture guids only).
            auto onHit = [map, portalGuid](Unit* hit)
            {
                if (Creature* p = map->GetCreature(portalGuid))
                    if (hit)
                        p->CastSpell(hit, SPELL_GD_VOLLEY_STREAM, true);
            };
            if (lingerMs > 0)
            {
                DungeonKit::ImpactSpec impact;
                impact.shape = BossMechanics::Shapes::LineFacing(start, path.facing, path.length, kLaneWidthYd);
                impact.shape.shape.zTolerance = _region.zTolerance;    // the linger copies impact.shape
                impact.warn = Milliseconds(kVolleyWarnMs);
                impact.pct = kVolleyPct(heroic);
                impact.school = SPELL_SCHOOL_ARCANE;
                impact.spellId = SPELL_GD_VOLLEY_HIT;
                impact.weakened = true;
                impact.tag = TAG_GD_VOLLEY;
                DungeonKit::LingerSpec linger;
                linger.duration = Milliseconds(lingerMs);
                linger.tick = Milliseconds(kVolleyLingerTickMs);
                linger.pct = kVolleyLingerPct;
                linger.school = SPELL_SCHOOL_ARCANE;
                linger.spellId = SPELL_GD_VOLLEY_LINGER;
                linger.tag = TAG_GD_VOLLEY_LINGER;
                DungeonKit::ImpactThenLinger(me, impact, linger).OnHit(onHit);
            }
            else
                Mechanic::Line(me, start, path.facing, path.length, kLaneWidthYd, Milliseconds(kVolleyWarnMs))
                    .ZTolerance(_region.zTolerance).Damage(kVolleyPct(heroic)).School(SPELL_SCHOOL_ARCANE)
                    .Spell(SPELL_GD_VOLLEY_HIT).Weakened().Tag(TAG_GD_VOLLEY).OnHit(onHit);
            _volleyPortals.push_back({ portalGuid, ToPos(path.end, z, path.facing) });
        }
        _laneFires.push_back(_clockMs + kVolleyWarnMs);
        _streamLeft = kPortalStreamMissiles;
        events.ScheduleEvent(EVENT_VOLLEY_FIRE, Milliseconds(kVolleyWarnMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "portal-volley",
            Acore::StringFormat("lanes={} heroic={} linger={}ms", _volleyPortals.size(), heroic ? 1 : 0, lingerMs));
    }

    // The streams pour down the lanes as they fire (the registry deals the hits on its own clock).
    void StreamVolley()
    {
        for (VolleyPortal const& v : _volleyPortals)
            if (Creature* portal = me->GetMap()->GetCreature(v.portal))
                portal->CastSpell(v.end.GetPositionX(), v.end.GetPositionY(), v.end.GetPositionZ() + 1.f,
                    SPELL_GD_VOLLEY_STREAM_GROUND, true);
        if (_streamLeft > 0 && --_streamLeft > 0)
            events.ScheduleEvent(EVENT_VOLLEY_STREAM, Milliseconds(kPortalStreamGapMs));
        else
            _volleyPortals.clear();
    }

    // ---- GD4b Transfer ----------------------------------------------------------------------------------------------
    void StartTransfer()
    {
        std::vector<ObjectGuid> guids;
        std::vector<Candidate> const c = Candidates(guids);
        std::optional<std::pair<std::size_t, std::size_t>> const pair =
            PickTransferPair(c, _mode.transferTankEligible, RandIndex);
        if (!pair)
            return;
        _transferA = guids[pair->first];
        _transferB = guids[pair->second];
        Talk(EMOTE_GANDLING_TRANSFER);
        MarkTransfer();
        events.ScheduleEvent(EVENT_TRANSFER_SWAP, Milliseconds(kTransferWarnMs));
    }

    void MarkTransfer()
    {
        for (ObjectGuid const g : { _transferA, _transferB })
            if (Player* p = ObjectAccessor::GetPlayer(*me, g))
                me->CastSpell(p, SPELL_GD_TRANSFER_MARK, true);
    }

    void ClearTransferMarks()
    {
        for (ObjectGuid const g : { _transferA, _transferB })
            if (Player* p = ObjectAccessor::GetPlayer(*me, g))
                p->RemoveAurasDueToSpell(SPELL_GD_TRANSFER_MARK);
        _transferA.Clear();
        _transferB.Clear();
    }

    void Swap()
    {
        // No lane fires within 1.5 s after a swap: hold it past them (the marks stay up meanwhile).
        PruneLaneFires();
        if (uint32 const hold = SwapHoldMs(_clockMs, _laneFires))
        {
            MarkTransfer();
            events.ScheduleEvent(EVENT_TRANSFER_SWAP, Milliseconds(hold));
            return;
        }
        Player* a = ObjectAccessor::GetPlayer(*me, _transferA);
        Player* b = ObjectAccessor::GetPlayer(*me, _transferB);
        bool const ok = a && b && a->IsAlive() && b->IsAlive() && InRegion(a) && InRegion(b)
            && !a->IsBeingTeleported() && !b->IsBeingTeleported() && !IsDetainedNow(a->GetGUID())
            && !IsDetainedNow(b->GetGUID()) && !a->GetVehicle() && !b->GetVehicle();
        if (!ok)
        {
            ClearTransferMarks();
            return;
        }
        Position const pa = a->GetPosition();
        Position const pb = b->GetPosition();
        ObjectGuid const tank = TankGuid();
        a->CastSpell(a, SPELL_GD_PORTAL_FLASH, true);
        b->CastSpell(b, SPELL_GD_PORTAL_FLASH, true);
        a->NearTeleportTo(pb.GetPositionX(), pb.GetPositionY(), pb.GetPositionZ(), a->GetOrientation());
        b->NearTeleportTo(pa.GetPositionX(), pa.GetPositionY(), pa.GetPositionZ(), b->GetOrientation());

        // A swapped tank takes him along (SC GD4b): the same offset from the tank's new spot, on the study's floor
        // (R-C GANDLING S-1: the leash circle runs past the walls and into the gate alcoves; the floor box does not).
        if (_mode.needsVictim && (a->GetGUID() == tank || b->GetGUID() == tank))
        {
            Position const& tankFrom = a->GetGUID() == tank ? pa : pb;
            Position const& tankTo = a->GetGUID() == tank ? pb : pa;
            Position dest(tankTo.GetPositionX() + (me->GetPositionX() - tankFrom.GetPositionX()),
                tankTo.GetPositionY() + (me->GetPositionY() - tankFrom.GetPositionY()), tankTo.GetPositionZ());
            if (!_region.clip.Contains({ dest.GetPositionX(), dest.GetPositionY() }, dest.GetPositionZ()))
                dest = tankTo;
            dest.SetOrientation(dest.GetAbsoluteAngle(&tankTo));
            me->NearTeleportTo(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(), dest.GetOrientation());
        }

        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "transfer",
            Acore::StringFormat("{} <-> {}{}", a->GetName(), b->GetName(),
                (a->GetGUID() == tank || b->GetGUID() == tank) ? " (tank: he follows)" : ""));
        // HM final phase: every swap raises an Expelled Student on one of the two, where they land.
        if (_mode.transferRaisesExpelled)
        {
            bool const first = urand(0, 1) == 0;
            RaiseExpelledAt(first ? a : b, first ? pb : pa);
        }
        ClearTransferMarks();
    }

    void PruneLaneFires()
    {
        std::erase_if(_laneFires, [this](uint32 fire) { return fire + kLaneGapAfterSwapMs < _clockMs; });
    }

    // ---- The timeline -----------------------------------------------------------------------------------------------
    void ExecuteFightEvent(uint32 id)
    {
        switch (id)
        {
            case EVENT_DETENTION:
                if (!_mode.detention)
                    return;
                if (_det.phase != DetentionPhase::Idle)
                {
                    events.ScheduleEvent(EVENT_DETENTION, 1s);
                    return;
                }
                if (me->HasUnitState(UNIT_STATE_CASTING))
                {
                    events.ScheduleEvent(EVENT_DETENTION, Milliseconds(kBarRetryMs));
                    return;
                }
                if (!BeginDetention())
                {
                    events.ScheduleEvent(EVENT_DETENTION, Milliseconds(kDetentionRetryMs));
                    return;
                }
                events.ScheduleEvent(EVENT_DETENTION, Milliseconds(_mode.detentionEveryMs));
                return;
            case EVENT_DETENTION_SEND:
                SendStudent();
                return;
            case EVENT_VOLLEY:
                if (!_mode.volley)
                    return;
                if (me->HasUnitState(UNIT_STATE_CASTING))
                {
                    events.ScheduleEvent(EVENT_VOLLEY, Milliseconds(kBarRetryMs));
                    return;
                }
                DungeonKit::CastBar(me, SPELL_GD_VOLLEY_CAST, nullptr, uint8(EMOTE_GANDLING_PORTAL_VOLLEY));
                events.ScheduleEvent(EVENT_VOLLEY_OPEN, Milliseconds(kVolleyCastMs));
                events.ScheduleEvent(EVENT_VOLLEY, Milliseconds(_mode.volleyEveryMs));
                return;
            case EVENT_VOLLEY_OPEN:
                OpenPortals();
                return;
            case EVENT_VOLLEY_FIRE:
            case EVENT_VOLLEY_STREAM:
                StreamVolley();
                return;
            case EVENT_TRANSFER:
                if (!_mode.transfer)
                    return;
                StartTransfer();
                events.ScheduleEvent(EVENT_TRANSFER, Milliseconds(_mode.transferEveryMs));
                return;
            case EVENT_TRANSFER_SWAP:
                Swap();
                return;
            default:
                return;
        }
    }

    DungeonKit::ArenaGuard _arena;
    GandlingRegion _region;
    GandlingMode _mode;
    std::optional<GandlingMode> _engageMode;
    std::function<ObjectGuid()> _tankProvider;
    uint32 _clockMs = 0;

    Detention _det;
    std::unique_ptr<SoloLesson> _lesson;
    RoomCycle _cycle;
    ObjectGuid _lastBack;
    ObjectGuid _victim;             // his victim now and the one before it (CountsAsTank)
    ObjectGuid _prevVictim;
    uint32 _victimChangedMs = 0;
    std::optional<Classroom> _forcedRoom;

    std::vector<VolleyPortal> _volleyPortals;
    std::vector<uint32> _laneFires;
    uint32 _streamLeft = 0;

    ObjectGuid _transferA;
    ObjectGuid _transferB;
};

namespace ScholoGandling
{
    GandlingFightApi* GetGandlingFight(Creature* gandling)
    {
        if (!gandling || !gandling->IsAIEnabled || !gandling->AI())
            return nullptr;
        return dynamic_cast<GandlingFightApi*>(gandling->AI());
    }
}

namespace
{
    boss_darkmaster_gandling_rework* FindGandlingAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_GANDLING);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_darkmaster_gandling_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Gandling does not run boss_darkmaster_gandling_rework.");
        return ai;
    }

    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetPlayer();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_GANDLING, BOSS_GANDLING);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_darkmaster_gandling_rework* ai = FindGandlingAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Gandling: {}", ai->StateLine());
        for (std::size_t i = 0; i < kClassroomCount; ++i)
            handler->PSendSysMessage("{} {}: lesson {}", i, kClassroomNames[i],
                HasSoloLesson(Classroom(i)) ? "registered" : "MISSING");
        return true;
    }

    // `.dbtest scholo gandling detention [room 0-5]`: detains the selected player (or a random one if you select
    // nobody or yourself as a GM) now, into that room or the cycle's next. He must be in combat.
    bool HandleDetention(ChatHandler* handler, Optional<uint32> room)
    {
        boss_darkmaster_gandling_rework* ai = FindGandlingAI(handler);
        if (!ai)
            return false;
        Player* selected = handler->getSelectedPlayer();
        if (selected && selected->IsGameMaster())
            selected = nullptr;
        std::string const err = ai->ForceDetention(selected, room);
        if (!err.empty())
        {
            handler->SendErrorMessage("{}", err);
            return false;
        }
        handler->PSendSysMessage("{}", "Gandling: detention cast; `state` follows it.");
        return true;
    }

    bool HandleVolley(ChatHandler* handler)
    {
        boss_darkmaster_gandling_rework* ai = FindGandlingAI(handler);
        if (!ai)
            return false;
        ai->ForceVolley();
        handler->PSendSysMessage("{}", "Gandling: Portal Volley now (he must be in combat).");
        return true;
    }

    bool HandleTransfer(ChatHandler* handler)
    {
        boss_darkmaster_gandling_rework* ai = FindGandlingAI(handler);
        if (!ai)
            return false;
        ai->ForceTransfer();
        handler->PSendSysMessage("{}", "Gandling: Transfer marks (two players in the study, GMs excluded).");
        return true;
    }

    bool HandleExpelled(ChatHandler* handler)
    {
        boss_darkmaster_gandling_rework* ai = FindGandlingAI(handler);
        Player* student = TestTarget(handler);
        if (!ai || !student)
            return false;
        ai->RaiseExpelled(student->GetGUID());
        handler->PSendSysMessage("Gandling: an Expelled Student on {}.", student->GetName());
        return true;
    }

    bool HandleHonorRoll(ChatHandler* handler)
    {
        boss_darkmaster_gandling_rework* ai = FindGandlingAI(handler);
        Player* student = TestTarget(handler);
        if (!ai || !student)
            return false;
        ai->ForceHonorRoll(student);
        handler->PSendSysMessage("Gandling: Honor Roll on {}.", student->GetName());
        return true;
    }

    ChatCommandTable const& GandlingTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "detention", HandleDetention, SEC_GAMEMASTER, Console::No },
            { "volley",    HandleVolley,    SEC_GAMEMASTER, Console::No },
            { "transfer",  HandleTransfer,  SEC_GAMEMASTER, Console::No },
            { "expelled",  HandleExpelled,  SEC_GAMEMASTER, Console::No },
            { "honorroll", HandleHonorRoll, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_darkmaster_gandling_rework()
{
    RegisterDungeonReworkCreatureAI(boss_darkmaster_gandling_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_expelled_student, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_lesson_stalker, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_portal_stalker, ScholomanceRework::kInstanceScriptName);
    ScholoTest::RegisterBoss("gandling", GandlingTestCommands());
}
