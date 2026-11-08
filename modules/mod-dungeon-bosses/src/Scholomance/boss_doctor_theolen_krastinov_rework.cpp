/*
 * mod-dungeon-bosses, Scholomance S6: Doctor Theolen Krastinov (11261), "Open-Heart Surgery". Build spec SC 1703-1764
 * (docs/dungeons/scholomance-rework.md), handoff section 3.4 rows KR and 3.5 row S6. Replaces stock SmartAI 11261
 * (Backhand 18103, Rend 16509, Frenzy 8269 and his texts: WP-S6's SQL rev drops it); bound by apps/dbc-tools
 * source/npcs/scholomance/doctor_theolen_krastinov.py. Pure rules: KrastinovLogic.h. He stays civilian (flags_extra
 * INSTANCE_BIND | CIVILIAN): the tank attacks first.
 *
 *   KR1  Operation         15 s, then every 30 s (start to start, 5 s after the last one at the soonest): emote line 5,
 *                          a 1 s hook (206225) on a random DPS (heroic: anyone but the tank, the healer too), who is
 *                          strapped into the Work Bench's seat (300538, VehicleId 6, seat 441); he walks to the bench
 *                          (kOperatingSpot) and operates there, attackable and passive (the tank loses his melee)
 *   KR2  Wrench Free       the bench's one button (206227, 3 s cooldown): during a cut's cast it interrupts the cut;
 *                          in a pause it is wasted (and its cooldown makes the next cut land)
 *   KR3  Incision          his 1.5 s cast bar (206229) with the bench's 1.5 s window aura (206231), then a 2-3 s
 *                          pause; a landed cut (206230) hits the patient for 20% / 30%
 *   KR4  Escape            3 interrupts (4 after the eyes): the straps snap, the patient is ejected and stabs him for
 *                          5% of his health (206232)
 *   KR5  Success           3 landed cuts (heroic 2), or 25 s on the bench: yell line 2, the patient is ejected with a
 *                          Stitched Wound stack (206233, max health -15%, the fight), and he takes the next graft
 *   KR6  Grafts            hands (Killing Frenzy 206234, +25% / +40% attack speed, emote 4), eyes (206235, emote 6:
 *                          escapes need 4), then a heart for every later success (206236 heals 10% / 15%, emote 7)
 *   KR7  Failed Patients   2 / 3 (300539) rise in the south alcove as the patient is seated: normal, on random
 *                          players; heroic (The Waiting Room Wants In), fixated on the patient and not tauntable, and
 *                          each one at the bench claws back one interrupt every 3 s (206241); after the operation the
 *                          survivors turn on random players. Their melee carries a light bleed (206240, 1% per 2 s)
 *   KR8  Backhand          10 s, then every 15 s, never during an operation: a 2 s cast (206238), then 40% / 55% of the
 *                          tank row, Physical
 *   KR9  Butcher's Rend    3-7 s, then every 14-18 s: a bleed on the tank (206239), 2% of the tank row per stack per
 *                          3 s, 5 stacks, 15 s
 *   Arena                  ScholomanceRework::LeashOptions on KrastinovFightArena() (the room's circle plus his apse,
 *                          where the bench stands)
 *
 * The same operation runs the detention lesson of the Hall of the Damned (HallOfTheDamnedLesson, SC 2966): the bench
 * operates itself (its own saw window aura, three cuts), the student interrupts with the same button. The hard mode
 * examiner (S13) runs this fight on a ScriptedAI (npc_sc_examiner_krastinov, registered once wave C binds:
 * kWaveCBound) at heroic values.
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one). Every firing logs
 * one INFO line "scholo krastinov <mechanic> ..." (module.dungeonbosses).
 *
 * The seat and every eject are the kit's (DungeonKit::SeatInVehicle / EjectAll, kit helper #8); the bench's own AI is
 * the dead-man switch (DungeonKit::ReleaseOrphanedVehicle) when the operation that owns it is gone.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureTextMgr.h"
#include "DungeonKit.h"
#include "KrastinovLogic.h"
#include "Map.h"
#include "MechanicWeakened.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SoloLesson.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "Vehicle.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoKrastinov;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kLogBoss = "krastinov";
    char const* const kLogExaminer = "krastinov-examiner";
    char const* const kLogLesson = "krastinov-lesson";

    uint32 constexpr POINT_OPERATE = 1;
    uint32 constexpr kBenchWatchMs = 500;       // the bench's dead-man switch poll

    float Rand01()
    {
        return std::min(0.9999f, static_cast<float>(rand_norm()));
    }

    char const* OutcomeName(OpOutcome o)
    {
        switch (o)
        {
            case OpOutcome::None:     return "none";
            case OpOutcome::Escape:   return "escape";
            case OpOutcome::Success:  return "success";
            case OpOutcome::Finished: return "finished";
            case OpOutcome::Aborted:  return "aborted";
        }
        return "?";
    }

    char const* WrenchName(WrenchResult r)
    {
        switch (r)
        {
            case WrenchResult::NotSeated:   return "not-seated";
            case WrenchResult::OnCooldown:  return "on-cooldown";
            case WrenchResult::Wasted:      return "wasted";
            case WrenchResult::Interrupted: return "interrupted";
            case WrenchResult::Escaped:     return "escaped";
        }
        return "?";
    }

    // The players of the fight: alive, not game masters, on `arena`.
    std::vector<Player*> FightPlayers(Creature const* me, DungeonKit::Arena const& arena)
    {
        std::vector<Player*> players;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (p && p->IsAlive() && !p->IsGameMaster() && arena.Contains(DungeonKit::PlaneOf(p), p->GetPositionZ()))
                players.push_back(p);
        }
        return players;
    }

    Player* RandomPlayer(std::vector<Player*> const& players, ObjectGuid except)
    {
        std::vector<Player*> pool;
        for (Player* p : players)
            if (p->GetGUID() != except && !p->GetVehicle())
                pool.push_back(p);
        if (pool.empty())
            return nullptr;
        return pool[std::min<std::size_t>(pool.size() - 1, static_cast<std::size_t>(Rand01() * pool.size()))];
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The operation on the Work Bench (KR1-KR5), the boss's and the detention lesson's: the pure Operation plus the engine
// glue (the seat, the cast bar and window aura, the hits, the eject). Shared between its driver (the boss's fight or
// the lesson) and the bench's AI (Wrench Free and the claws reach it through a weak pointer).
// ---------------------------------------------------------------------------------------------------------------------
class BenchOperation
{
public:
    enum class Mode : uint8
    {
        Boss,       // Krastinov (or his examiner) operates: his cast bar, his hits, the escape stab, the wound
        Lesson,     // detention: the bench operates itself; the lesson owner deals the hits
    };

    struct Tick
    {
        uint32 landed = 0;          // cuts that landed this tick
        bool seated = false;        // the patient was strapped in this tick
        bool ended = false;         // the operation ended this tick (Outcome())
    };

    // `operatorUnit`: Krastinov (Boss) or nullptr (Lesson); `hitCaster`: who deals the cuts (Krastinov, or the lesson
    // owner); `logBoss`: the log name.
    void Begin(Mode mode, Creature* bench, Player* patient, Creature* operatorUnit, Creature* hitCaster,
        OperationRules const& rules, bool heroic, char const* logBoss)
    {
        _map = bench ? bench->GetMap() : nullptr;
        _mode = mode;
        _bench = bench ? bench->GetGUID() : ObjectGuid::Empty;
        _patient = patient ? patient->GetGUID() : ObjectGuid::Empty;
        _operator = operatorUnit ? operatorUnit->GetGUID() : ObjectGuid::Empty;
        _hitCaster = hitCaster ? hitCaster->GetGUID() : ObjectGuid::Empty;
        _heroic = heroic;
        _logBoss = logBoss;
        _endHandled = false;
        _seatRefused = false;
        _op.Start(rules);
        Log("operation-begin", Acore::StringFormat("mode={} heroic={} patient={} escape={} succeed={} maxCuts={}",
            mode == Mode::Boss ? "boss" : "lesson", heroic ? 1 : 0, patient ? patient->GetName() : "none",
            rules.interruptsToEscape, rules.cutsToSucceed, rules.maxCuts));
        if (!bench || !patient)
            Abort("no bench or patient");
    }

    Tick Update(uint32 diff)
    {
        Tick tick;
        if (!_op.Active())
        {
            // An end decided outside the tick (Wrench Free's last interrupt) is carried out here, never inside the
            // bench's own spell: the eject uncharms the bench, which stops its casts.
            if (_op.Done() && !_endHandled)
            {
                HandleEnd();
                tick.ended = true;
            }
            return tick;
        }

        Creature* bench = Bench();
        Player* patient = Patient();
        if (!bench || !bench->IsAlive())
        {
            Abort("the bench is gone");
            tick.ended = true;
            return tick;
        }
        if (_op.IsSeated() && (!patient || !patient->IsAlive() || patient->GetVehicleBase() != bench))
        {
            Abort("the patient left the bench");
            tick.ended = true;
            return tick;
        }

        OpStep const step = _op.Update(diff, Rand01());
        if (step.seat)
        {
            if (!patient || !patient->IsAlive())
            {
                Abort("the patient died before the seat");
                tick.ended = true;
                return tick;
            }
            if (DungeonKit::SeatInVehicle(patient, bench, kBenchSeat))
            {
                _op.Seated();
                tick.seated = true;
                // The patient now controls the bench: hold it where it stands.
                bench->SetControlled(false, UNIT_STATE_ROOT);
                bench->SetControlled(true, UNIT_STATE_ROOT);
                UpdateStraps();
                Log("seat", Acore::StringFormat("patient={}", patient->GetName()));
            }
            else if (_op.ElapsedMs() >= _op.Rules().seatDelayMs + kSeatGiveUpMs)
            {
                _seatRefused = true;
                Abort("the seat was refused");
                tick.ended = true;
                return tick;
            }
        }
        if (step.startCut)
            StartCut();
        if (step.cutLanded)
        {
            LandCut();
            ++tick.landed;
        }
        if (step.ended || _op.Done())
        {
            HandleEnd();
            tick.ended = true;
        }
        return tick;
    }

    // KR2 from the bench's Wrench Free (its spell script). `presser`: the passenger who pressed it. Runs inside the
    // bench's spell: an escape only ends the operation's state here; the next Update ejects.
    WrenchResult WrenchFree(Player* presser)
    {
        if (!presser || presser->GetGUID() != _patient)
            return WrenchResult::NotSeated;
        WrenchResult const result = _op.WrenchFree(Rand01());
        Creature* bench = Bench();
        Log("wrench-free", Acore::StringFormat("result={} straps={} landed={} interrupts={} wasted={}",
            WrenchName(result), _op.StrapsLeft(), _op.Landed(), _op.TotalInterrupts(), _op.WastedPresses()));
        if (result == WrenchResult::Interrupted || result == WrenchResult::Escaped)
        {
            StopCut();
            // The jolt shows on whoever holds the saw: him (Boss) or the bench (Lesson); a self cast, so the bench
            // never starts a fight of its own.
            Unit* jolted = Operator() ? static_cast<Unit*>(Operator()) : static_cast<Unit*>(bench);
            if (jolted)
                jolted->CastSpell(jolted, SPELL_KR_WRENCH_IMPACT, true);
            UpdateStraps();
        }
        return result;
    }

    // KR7 heroic: a Failed Patient at the bench. True when it undid an interrupt.
    bool Claw(Creature* ghoul)
    {
        if (!_op.Claw())
            return false;
        if (Player* patient = Patient())
            if (ghoul)
                ghoul->CastSpell(patient, SPELL_KR_CLAW_AT_STRAPS, true);
        UpdateStraps();
        Log("claw", Acore::StringFormat("straps={} claws={}", _op.StrapsLeft(), _op.Claws()));
        return true;
    }

    // His walk ended at the bench (Boss).
    void Arrived()
    {
        _op.Arrived();
    }

    // Ends it now: the patient comes off the bench (no stab, no wound).
    void Abort(char const* why)
    {
        if (!_op.Active())
        {
            if (_op.Done() && !_endHandled)
                HandleEnd();
            return;
        }
        Log("operation-abort", why);
        _op.Abort();
        HandleEnd();
    }

    bool Active() const { return _op.Active(); }
    // The patient could not be seated (kSeatGiveUpMs after it was due): the boss picks someone else, the lesson fails.
    bool SeatRefused() const { return _seatRefused; }
    // The end (the eject) has run.
    bool EndHandled() const { return _endHandled; }
    Operation const& State() const { return _op; }
    ObjectGuid PatientGuid() const { return _patient; }
    ObjectGuid BenchGuid() const { return _bench; }
    bool Heroic() const { return _heroic; }

    Creature* Bench() const { return _map ? _map->GetCreature(_bench) : nullptr; }
    Player* Patient() const { return _map ? ObjectAccessor::GetPlayer(_map, _patient) : nullptr; }
    Creature* Operator() const { return _map && !_operator.IsEmpty() ? _map->GetCreature(_operator) : nullptr; }
    Creature* HitCaster() const { return _map && !_hitCaster.IsEmpty() ? _map->GetCreature(_hitCaster) : nullptr; }

private:
    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, _logBoss, mechanic, detail);
    }

    // KR3: his cast bar (Boss) and the bench's window aura (both): the window the patient's Wrench Free must hit.
    void StartCut()
    {
        Creature* bench = Bench();
        Player* patient = Patient();
        if (bench)
            bench->CastSpell(bench, SPELL_KR_SAW_DESCENDING, true);
        if (_mode == Mode::Boss)
            if (Creature* surgeon = Operator())
                if (patient && surgeon->IsAlive())
                {
                    surgeon->GetMotionMaster()->Clear();
                    surgeon->StopMoving();
                    surgeon->SetFacingToObject(patient);
                    surgeon->CastSpell(patient, SPELL_KR_INCISION, false);  // not triggered: the bar shows
                }
        Log("incision", Acore::StringFormat("cut={} straps={}", _op.Cuts() + 1, _op.StrapsLeft()));
    }

    void StopCut()
    {
        if (Creature* bench = Bench())
            bench->RemoveAurasDueToSpell(SPELL_KR_SAW_DESCENDING);
        if (Creature* surgeon = Operator())
            if (Spell* current = surgeon->GetCurrentSpell(CURRENT_GENERIC_SPELL))
                if (current->m_spellInfo->Id == SPELL_KR_INCISION)
                    surgeon->InterruptSpell(CURRENT_GENERIC_SPELL, false, true);
    }

    // KR3: the cut lands: 20% / 30% (Boss) or the lesson's failure hit, 15% / 25% + Weakened (Lesson).
    void LandCut()
    {
        if (Creature* bench = Bench())
            bench->RemoveAurasDueToSpell(SPELL_KR_SAW_DESCENDING);
        Player* patient = Patient();
        Creature* caster = HitCaster();
        if (!patient || !caster)
            return;
        float const pct = _mode == Mode::Boss ? kIncisionPct(_heroic) : LessonFailurePct(_heroic);
        caster->CastCustomSpell(SPELL_KR_INCISION_HIT, SPELLVALUE_BASE_POINT0, static_cast<int32>(pct), patient,
            TRIGGERED_FULL_MASK);
        if (_mode == Mode::Lesson)
            BossMechanics::Weakened::AddStack(patient);
        UpdateStraps();
        Log("incision-landed", Acore::StringFormat("landed={} pct={}", _op.Landed(), pct));
    }

    // The bench's Strapped Down stacks: straps left (Boss), cuts left (Lesson).
    void UpdateStraps()
    {
        Creature* bench = Bench();
        if (!bench)
            return;
        int32 const want = _op.IsSeated() ? static_cast<int32>(_op.StrapsLeft()) : 0;
        int32 const have = static_cast<int32>(DungeonKit::Stacks(bench, SPELL_KR_STRAPPED_DOWN));
        if (want != have)
            DungeonKit::AddStacks(bench, SPELL_KR_STRAPPED_DOWN, want - have, bench);
    }

    // Every way out: the window aura and the bar stop, the patient comes off the bench; the escape stab (KR4) and the
    // Stitched Wound (KR5) for the boss's operation.
    void HandleEnd()
    {
        if (_endHandled)
            return;
        _endHandled = true;
        StopCut();
        Creature* bench = Bench();
        Player* patient = Patient();
        if (bench)
            bench->RemoveAurasDueToSpell(SPELL_KR_STRAPPED_DOWN);
        DungeonKit::EjectAll(bench);
        // The patient held a control seat (the root stops moving, not turning): the bench faces the hall again.
        if (bench && bench->IsAlive())
            bench->SetFacingTo(kWorkBenchGo.o);

        OpOutcome const outcome = _op.Outcome();
        Creature* surgeon = Operator();
        if (_mode == Mode::Boss && patient && patient->IsAlive() && surgeon && surgeon->IsAlive())
        {
            if (outcome == OpOutcome::Escape)
            {
                int32 const stab = static_cast<int32>(surgeon->CountPctFromMaxHealth(kScalpelStabPct));
                patient->CastCustomSpell(SPELL_KR_SCALPEL_STAB, SPELLVALUE_BASE_POINT0, stab, surgeon,
                    TRIGGERED_FULL_MASK);
            }
            else if (outcome == OpOutcome::Success)
                DungeonKit::AddStacks(patient, SPELL_KR_STITCHED_WOUND, 1, surgeon);
        }
        Log("operation-end", Acore::StringFormat("outcome={} landed={} interrupts={} wasted={} claws={} seconds={:.1f}",
            OutcomeName(outcome), _op.Landed(), _op.TotalInterrupts(), _op.WastedPresses(), _op.Claws(),
            _op.ElapsedMs() / 1000.f));
    }

    Map* _map = nullptr;
    Mode _mode = Mode::Boss;
    ObjectGuid _bench;
    ObjectGuid _patient;
    ObjectGuid _operator;
    ObjectGuid _hitCaster;
    bool _heroic = false;
    bool _endHandled = false;
    bool _seatRefused = false;
    char const* _logBoss = kLogBoss;
    Operation _op;
};

// The Work Bench (300538): the vehicle. Never fights, never evades, stays itself while charmed (NullCreatureAI: the
// default CreatureAI::OnCharmed would swap in a PossessedAI and engage its last charmer). Holds the running operation
// for Wrench Free and the claws.
//
// The dead-man switch (R-B K-1): the seat has no exit of its own, so only the server frees the patient. Every 500 ms:
// someone aboard while no running operation owns the bench (the fight or the lesson that held it went away without
// its cleanup: a GM despawn, a dropped lesson) ejects them and despawns the bench; an empty bench whose summoner left
// the map despawns too.
struct npc_sc_work_bench : public NullCreatureAI
{
    explicit npc_sc_work_bench(Creature* creature) : NullCreatureAI(creature) { }

    void Bind(std::shared_ptr<BenchOperation> const& op) { _op = op; }
    std::shared_ptr<BenchOperation> Op() const { return _op.lock(); }

    void UpdateAI(uint32 diff) override
    {
        _watchMs += diff;
        if (_watchMs < kBenchWatchMs)
            return;
        _watchMs = 0;
        std::shared_ptr<BenchOperation> const op = _op.lock();
        // An operation that ended inside the bench's own spell (the escape) is ejected by its driver's next tick: only
        // a gone one, or one whose end already ran, leaves the passenger to this switch.
        if (DungeonKit::ReleaseOrphanedVehicle(me, !op || op->EndHandled()))
        {
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "bench-orphaned", "passenger ejected, bench despawned");
            return;
        }
        TempSummon* summon = me->ToTempSummon();
        Unit* summoner = summon ? summon->GetSummonerUnit() : nullptr;
        if (!op && (!summoner || !summoner->IsInWorld()))
        {
            DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "bench-orphaned", "summoner gone, bench despawned");
            me->DespawnOrUnsummon();
        }
    }

private:
    std::weak_ptr<BenchOperation> _op;
    uint32 _watchMs = 0;
};

namespace
{
    npc_sc_work_bench* BenchAI(Creature* bench)
    {
        return bench && bench->IsAIEnabled ? dynamic_cast<npc_sc_work_bench*>(bench->AI()) : nullptr;
    }

    Creature* SummonBench(Creature* summoner)
    {
        Creature* bench = summoner->SummonCreature(NPC_SC_WORK_BENCH, kWorkBenchGo.x, kWorkBenchGo.y, kWorkBenchGo.z,
            kWorkBenchGo.o, TEMPSUMMON_MANUAL_DESPAWN);
        if (bench)
        {
            bench->SetReactState(REACT_PASSIVE);
            bench->SetControlled(true, UNIT_STATE_ROOT);
        }
        return bench;
    }

    void DespawnBench(Map* map, ObjectGuid& guid)
    {
        if (Creature* bench = map && !guid.IsEmpty() ? map->GetCreature(guid) : nullptr)
        {
            DungeonKit::EjectAll(bench);
            bench->DespawnOrUnsummon();
        }
        guid.Clear();
    }
}

// The Failed Patient (300539), KR7: a past patient. Normal: engaged on the player it is sent at, tauntable. Heroic (The
// Waiting Room Wants In): fixated on the patient on the bench, not tauntable, and at the bench each one claws back an
// interrupt every 3 s unless crowd-controlled; once the operation ends it turns on a random player. Melee with a light
// bleed. Its pace (about 6 s to the bench) is its template's speed_run: the chase runs. Despawns when its summoner is
// gone.
struct npc_sc_failed_patient : public ScriptedAI
{
    explicit npc_sc_failed_patient(Creature* creature) : ScriptedAI(creature) { }

    // Called by the fight right after the summon.
    void Configure(ObjectGuid patient, ObjectGuid bench, bool fixate, Unit* target)
    {
        _patient = patient;
        _bench = bench;
        _fixated = fixate;
        _claws.Reset();
        _bleedMs = InRange(kInfectedClawsEveryMinMs, kInfectedClawsEveryMaxMs, Rand01()) / 2;
        if (fixate)
        {
            me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_ATTACK_ME, true);
            me->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TAUNT, true);
            if (Player* p = Patient())
                Fixate(p);
        }
        else if (target)
        {
            // Unit::Attack adds no threat, and UpdateVictim ends a fight that has none: engage first.
            me->EngageWithTarget(target);
            AttackStart(target);
        }
    }

    // The operation ended: survivors turn on a random player, as on normal (tauntable again).
    void Release(Unit* target)
    {
        if (!_fixated)
            return;
        _fixated = false;
        me->GetThreatMgr().ClearFixate();
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_ATTACK_ME, false);
        me->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TAUNT, false);
        if (target && target->IsAlive())
        {
            me->EngageWithTarget(target);
            AttackStart(target);
        }
    }

    bool Fixated() const { return _fixated; }

    void Reset() override
    {
        _claws.Reset();
    }

    // A summon of a fight: it never walks home.
    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();
    }

    void UpdateAI(uint32 diff) override
    {
        _ownerCheckMs += diff;
        if (_ownerCheckMs >= kFailedPatientOwnerCheckMs)
        {
            _ownerCheckMs = 0;
            TempSummon* summon = me->ToTempSummon();
            Unit* summoner = summon ? summon->GetSummonerUnit() : nullptr;
            if (!summoner || !summoner->IsAlive())
            {
                me->DespawnOrUnsummon();
                return;
            }
        }

        if (_fixated)
        {
            Player* patient = Patient();
            Creature* bench = Bench();
            // Off the bench (the end of the operation): the fight releases the survivors onto random players.
            if (patient && patient->IsAlive() && bench && patient->GetVehicleBase() == bench)
            {
                if (me->GetVictim() != patient)
                    Fixate(patient);
                bool const atBench = me->GetExactDist2d(bench) <= kClawReach;
                uint32 const claws = _claws.Update(diff, ClawsWork(atBench, CrowdControlled()));
                if (claws)
                    if (npc_sc_work_bench* ai = BenchAI(bench))
                        if (std::shared_ptr<BenchOperation> op = ai->Op())
                            for (uint32 i = 0; i < claws; ++i)
                                op->Claw(me);
            }
        }

        if (!UpdateVictim())
            return;

        if (_bleedMs > diff)
            _bleedMs -= diff;
        else if (me->IsWithinMeleeRange(me->GetVictim()))
        {
            me->CastSpell(me->GetVictim(), SPELL_KR_INFECTED_CLAWS, true);
            _bleedMs = InRange(kInfectedClawsEveryMinMs, kInfectedClawsEveryMaxMs, Rand01());
        }
        DoMeleeAttackIfReady();
    }

private:
    Player* Patient() const { return ObjectAccessor::GetPlayer(me->GetMap(), _patient); }
    Creature* Bench() const { return me->GetMap()->GetCreature(_bench); }

    // KR7: stunned (Shackle Undead too), incapacitated (polymorph), feared or pacified: no claws.
    bool CrowdControlled() const
    {
        return me->HasUnitState(UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED | UNIT_STATE_FLEEING)
            || me->HasAuraType(SPELL_AURA_MOD_PACIFY) || me->HasAuraType(SPELL_AURA_MOD_PACIFY_SILENCE);
    }

    void Fixate(Player* patient)
    {
        me->EngageWithTarget(patient);
        me->GetThreatMgr().FixateTarget(patient);
        AttackStart(patient);
    }

    ObjectGuid _patient;
    ObjectGuid _bench;
    bool _fixated = false;
    ClawTicker _claws;
    uint32 _bleedMs = 0;
    uint32 _ownerCheckMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// The fight (KR1-KR9), shared by the boss and his hard mode examiner (S13): the bench, the operations, the grafts, the
// Failed Patients, Backhand and Butcher's Rend. Owned by the AI; `me` lives as long as it.
// ---------------------------------------------------------------------------------------------------------------------
class KrastinovFight
{
public:
    KrastinovFight(Creature* me, bool examiner) : _me(me), _examiner(examiner) { }

    // Heroic numbers: the heroic map, or the examiner (always heroic, SC GD5).
    bool Heroic() const { return _examiner || IsHeroicMap(_me); }
    char const* LogName() const { return _examiner ? kLogExaminer : kLogBoss; }

    void Engage()
    {
        Cleanup();
        _clockMs = 0;
        _nextOperationMs = kOperationFirstMs;
        _nextBackhandMs = kBackhandFirstMs;
        _nextRendMs = InRange(kRendFirstMinMs, kRendFirstMaxMs, Rand01());
        Creature* bench = SummonBench(_me);
        _bench = bench ? bench->GetGUID() : ObjectGuid::Empty;
        Log("engage", Acore::StringFormat("heroic={} examiner={} bench={} at=({:.1f}, {:.1f}, {:.1f})",
            Heroic() ? 1 : 0, _examiner ? 1 : 0, bench ? 1 : 0, _me->GetPositionX(), _me->GetPositionY(),
            _me->GetPositionZ()));
    }

    // Every tick in combat (after UpdateVictim, or instead of it while he operates). True: he may melee.
    bool Update(uint32 diff)
    {
        _clockMs += diff;
        if (_op)
        {
            std::shared_ptr<BenchOperation> const op = _op;     // alive through a death or evade inside the tick
            BenchOperation::Tick const tick = op->Update(diff);
            if (!_op)
                return false;                                   // cleaned up during the tick (he died or evaded)
            if (tick.seated)
                OnSeated();
            if (_op->Active() && _op->State().Phase() == OpPhase::Approach && !_walking)
                WalkToBench();
            if (!_op->Active())
                FinishOperation();
            return false;
        }

        if (_me->HasUnitState(UNIT_STATE_CASTING))
            return false;

        if (_clockMs >= _nextOperationMs)
        {
            if (StartOperation(nullptr, Heroic()))
                return false;
            if (_repick)
            {
                // Nobody left to re-pick after a refused seat: the slot is spent, the next one comes on time.
                _nextOperationMs = NextOperationAt(_opStartMs, _clockMs);
                _repick = false;
                _refused.clear();
            }
            else
                _nextOperationMs = _clockMs + kOperationMinGapMs;     // nobody to operate on: try again shortly
        }

        Unit* victim = _me->GetVictim();
        if (BackhandMayStart(_clockMs, _nextBackhandMs, false, _nextOperationMs) && victim)
        {
            // Not triggered: the 2 s bar shows. Base point 0 is the percent of the tank row
            // (spell_sc_krastinov_ref_hit). The timer moves on only for a cast that started (R-A S-8).
            SpellCastResult const result = _me->CastCustomSpell(SPELL_KR_BACKHAND, SPELLVALUE_BASE_POINT0,
                static_cast<int32>(kBackhandPct(Heroic())), victim, TRIGGERED_NONE);
            if (result == SPELL_CAST_OK)
            {
                _nextBackhandMs = _clockMs + kBackhandEveryMs;
                Log("backhand", Acore::StringFormat("{} pct={}", victim->GetName(), kBackhandPct(Heroic())));
                return false;
            }
            _nextBackhandMs = _clockMs + kBackhandRetryMs;
            Log("backhand-refused", Acore::StringFormat("{} result={}", victim->GetName(), int(result)));
        }
        if (_clockMs >= _nextRendMs && victim && _me->IsWithinMeleeRange(victim))
        {
            _me->CastSpell(victim, SPELL_KR_BUTCHERS_REND, true);
            _nextRendMs = _clockMs + InRange(kRendEveryMinMs, kRendEveryMaxMs, Rand01());
            Log("butchers-rend", Acore::StringFormat("{} stacks={}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_KR_BUTCHERS_REND)));
        }
        return true;
    }

    void MovementInform(uint32 type, uint32 id)
    {
        if (type == POINT_MOTION_TYPE && id == POINT_OPERATE && _op)
            Arrive();
    }

    // Evade, death, reset: every operation off, the patient off the bench, every summon gone, every aura of the fight
    // off the players and him.
    void Cleanup()
    {
        if (_op)
        {
            _op->Abort("cleanup");
            _op.reset();
        }
        DespawnBench(_me->GetMap(), _bench);
        for (ObjectGuid const& guid : _patients)
            if (Creature* ghoul = _me->GetMap()->GetCreature(guid))
                ghoul->DespawnOrUnsummon();
        _patients.clear();
        for (auto const& ref : _me->GetMap()->GetPlayers())
            if (Player* p = ref.GetSource())
            {
                p->RemoveAurasDueToSpell(SPELL_KR_STITCHED_WOUND);
                p->RemoveAurasDueToSpell(SPELL_KR_BUTCHERS_REND);
                p->RemoveAurasDueToSpell(SPELL_KR_INFECTED_CLAWS);
                // A pet tank keeps no bleed past the fight either.
                if (Pet* pet = p->GetPet())
                {
                    pet->RemoveAurasDueToSpell(SPELL_KR_BUTCHERS_REND);
                    pet->RemoveAurasDueToSpell(SPELL_KR_INFECTED_CLAWS);
                }
            }
        _me->RemoveAurasDueToSpell(SPELL_KR_KILLING_FRENZY);
        _me->RemoveAurasDueToSpell(SPELL_KR_GRAFTED_EYES);
        _me->RemoveAurasDueToSpell(SPELL_KR_GRAFTED_HEART);
        _successes = 0;
        _eyes = false;
        _walking = false;
        _opStartMs = 0;
        _repick = false;
        _refused.clear();
        if (_me->IsAlive() && _me->HasReactState(REACT_PASSIVE))
            _me->SetReactState(REACT_AGGRESSIVE);
    }

    bool Operating() const { return _op != nullptr; }

    // KR1 now (also the test command). `forced`: that player instead of the pick. False: nobody to operate on.
    bool StartOperation(Player* forced, bool heroic)
    {
        if (_op)
            return false;
        Creature* bench = _me->GetMap()->GetCreature(_bench);
        if (!bench)
        {
            bench = SummonBench(_me);
            _bench = bench ? bench->GetGUID() : ObjectGuid::Empty;
            if (!bench)
                return false;
        }
        Player* patient = forced ? forced : PickPatientNow(heroic);
        if (!patient)
        {
            Log("operation-skip", "nobody but the tank");
            return false;
        }
        _opHeroic = heroic;
        if (!_repick)
            _opStartMs = _clockMs;      // a re-pick keeps its slot's start (the next one comes on time)
        _walking = false;
        _patientsOut = false;
        _me->InterruptNonMeleeSpells(false);
        _me->AttackStop();
        _me->SetReactState(REACT_PASSIVE);
        _me->StopMoving();
        _me->GetMotionMaster()->Clear();
        Say(EMOTE_KRASTINOV_STRAPS, patient);
        _me->CastSpell(patient, SPELL_KR_HOOK, false);
        _op = std::make_shared<BenchOperation>();
        _op->Begin(BenchOperation::Mode::Boss, bench, patient, _me, _me, BossOperationRules(heroic, _eyes), heroic,
            LogName());
        if (npc_sc_work_bench* ai = BenchAI(bench))
            ai->Bind(_op);
        return true;
    }

    // KR7 now (also the test command): the Failed Patients of an operation, on `patient` (heroic: fixated).
    void ReleasePatients(Player* patient, bool heroic)
    {
        std::vector<Player*> const players = FightPlayers(_me, KrastinovFightArena());
        uint32 const count = kFailedPatientsPerOperation(heroic);
        for (uint32 i = 0; i < count; ++i)
        {
            float const angle = DungeonKit::kPi * 2.f * static_cast<float>(i) / static_cast<float>(count);
            float const x = kFailedPatientRise.x + kFailedPatientSpread * std::cos(angle);
            float const y = kFailedPatientRise.y + kFailedPatientSpread * std::sin(angle);
            float z = _me->GetMapHeight(x, y, kFailedPatientRise.z + 2.f);
            if (z <= INVALID_HEIGHT + 1.f || std::fabs(z - kFailedPatientRise.z) > 3.f)
                z = kFailedPatientRise.z;
            Creature* ghoul = _me->SummonCreature(NPC_SC_FAILED_PATIENT, x, y, z,
                std::atan2(kWorkBenchGo.y - y, kWorkBenchGo.x - x), TEMPSUMMON_CORPSE_TIMED_DESPAWN, 10000);
            if (!ghoul)
                continue;
            _patients.push_back(ghoul->GetGUID());
            if (auto* ai = dynamic_cast<npc_sc_failed_patient*>(ghoul->AI()))
            {
                // Normal: a random player off the bench; nobody else on the arena: the patient.
                Unit* target = RandomPlayer(players, patient ? patient->GetGUID() : ObjectGuid::Empty);
                if (!target)
                    target = patient;
                ai->Configure(patient ? patient->GetGUID() : ObjectGuid::Empty, _bench, heroic && patient, target);
            }
        }
        Log("failed-patients", Acore::StringFormat("count={} heroic={} fixated={}", count, heroic ? 1 : 0,
            heroic && patient ? 1 : 0));
    }

    // KR6 now (also the test command): the next graft.
    void TakeGraft(bool heroic)
    {
        ++_successes;
        Graft const graft = GraftFor(_successes);
        switch (graft)
        {
            case Graft::Hands:
                _me->CastCustomSpell(SPELL_KR_KILLING_FRENZY, SPELLVALUE_BASE_POINT0, kKillingFrenzyPct(heroic), _me,
                    TRIGGERED_FULL_MASK);
                Say(EMOTE_KRASTINOV_HANDS);
                break;
            case Graft::Eyes:
                _eyes = true;
                _me->CastSpell(_me, SPELL_KR_GRAFTED_EYES, true);
                Say(EMOTE_KRASTINOV_EYES);
                break;
            case Graft::Heart:
            {
                int32 const heal = static_cast<int32>(_me->CountPctFromMaxHealth(kHeartHealPct(heroic)));
                _me->CastCustomSpell(SPELL_KR_GRAFTED_HEART_HEAL, SPELLVALUE_BASE_POINT0, heal, _me,
                    TRIGGERED_FULL_MASK);
                DungeonKit::AddStacks(_me, SPELL_KR_GRAFTED_HEART, 1, _me);
                Say(EMOTE_KRASTINOV_HEART);
                break;
            }
        }
        Log("graft", Acore::StringFormat("success={} graft={} heroic={}", _successes,
            graft == Graft::Hands ? "hands" : graft == Graft::Eyes ? "eyes" : "heart", heroic ? 1 : 0));
    }

    std::shared_ptr<BenchOperation> Op() const { return _op; }

    std::string State() const
    {
        std::string op = "none";
        if (_op)
        {
            Operation const& s = _op->State();
            op = Acore::StringFormat("phase={} left={}ms straps={} landed={} interrupts={} wasted={} claws={} "
                "wrenchCd={}ms seated={:.1f}s", int(s.Phase()), s.PhaseLeftMs(), s.StrapsLeft(), s.Landed(),
                s.TotalInterrupts(), s.WastedPresses(), s.Claws(), s.WrenchCooldownMs(), s.SeatedMs() / 1000.f);
        }
        return Acore::StringFormat("clock={}s nextOperation={}s nextBackhand={}s nextRend={}s successes={} eyes={} "
            "failedPatients={} bench={} op=[{}]", _clockMs / 1000, _nextOperationMs / 1000, _nextBackhandMs / 1000,
            _nextRendMs / 1000, _successes, _eyes ? 1 : 0, _patients.size(), _bench.IsEmpty() ? 0 : 1, op);
    }

    // `.dbtest` Backhand / Rend now.
    void TestBackhand()
    {
        _nextBackhandMs = 0;
        _nextOperationMs = std::max<uint64>(_nextOperationMs, _clockMs + kBackhandOperationGuardMs + 1000);
    }
    void TestRend() { _nextRendMs = 0; }

private:
    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, LogName(), mechanic, detail);
    }

    // His text groups (ScholomanceRework.h KrastinovTexts) on his entry; the examiner says them only when S13 gives
    // its entry the same groups (no "missing text" error otherwise).
    void Say(uint8 group, WorldObject const* target = nullptr)
    {
        if (sCreatureTextMgr->TextExist(_me->GetEntry(), group))
            _me->AI()->Talk(group, target);
    }

    Player* PickPatientNow(bool heroic)
    {
        std::vector<Player*> const players = FightPlayers(_me, KrastinovFightArena());
        std::vector<PatientCandidate> candidates;
        for (Player* p : players)
        {
            PatientCandidate c;
            c.id = p->GetGUID().GetRawValue();
            c.alive = p->IsAlive();
            c.isVictim = _me->GetVictim() == p;
            c.tankSpec = p->HasTankSpec();
            c.healSpec = p->HasHealSpec();
            c.unavailable = p->GetVehicle() || p->IsBeingTeleported() || p->IsInFlight()
                || std::find(_refused.begin(), _refused.end(), p->GetGUID()) != _refused.end();
            candidates.push_back(c);
        }
        std::optional<uint64> const id = PickPatient(candidates, heroic, Rand01());
        if (!id)
            return nullptr;
        for (Player* p : players)
            if (p->GetGUID().GetRawValue() == *id)
                return p;
        return nullptr;
    }

    // The patient is on the bench: the waiting room opens.
    void OnSeated()
    {
        if (_patientsOut || !_op)
            return;
        _patientsOut = true;
        ReleasePatients(_op->Patient(), _opHeroic);
    }

    void WalkToBench()
    {
        _walking = true;
        Position const spot(kOperatingSpot.x, kOperatingSpot.y, kOperatingSpot.z, 0.f);
        if (_me->GetExactDist2d(spot.GetPositionX(), spot.GetPositionY()) <= 1.f)
        {
            Arrive();
            return;
        }
        _me->GetMotionMaster()->Clear();
        _me->GetMotionMaster()->MovePoint(POINT_OPERATE, spot);
    }

    void Arrive()
    {
        if (!_op)
            return;
        _me->StopMoving();
        if (Creature* bench = _me->GetMap()->GetCreature(_bench))
            _me->SetFacingToObject(bench);
        _op->Arrived();
    }

    void FinishOperation()
    {
        std::shared_ptr<BenchOperation> const op = _op;
        _op.reset();
        OpOutcome const outcome = op->State().Outcome();
        // A refused seat (R-B K-3): no penalty for the group, and he picks another patient at once.
        bool const refused = op->SeatRefused();
        if (refused)
        {
            _refused.push_back(op->PatientGuid());
            _repick = true;
            Log("operation-repick", Acore::StringFormat("refused={}", _refused.size()));
        }
        else
        {
            _repick = false;
            _refused.clear();
        }
        if (outcome == OpOutcome::Success && _me->IsAlive())
        {
            Say(YELL_KRASTINOV_SUCCESS);
            TakeGraft(_opHeroic);
        }
        // KR7: the survivors turn on random players.
        std::vector<Player*> const players = FightPlayers(_me, KrastinovFightArena());
        for (ObjectGuid const& guid : _patients)
            if (Creature* ghoul = _me->GetMap()->GetCreature(guid))
                if (auto* ai = dynamic_cast<npc_sc_failed_patient*>(ghoul->AI()))
                    if (ai->Fixated())
                        ai->Release(RandomPlayer(players, ObjectGuid::Empty));
        _nextOperationMs = refused ? _clockMs : NextOperationAt(_opStartMs, _clockMs);
        _nextBackhandMs = std::max<uint64>(_nextBackhandMs, _clockMs + kBackhandAfterOperationMs);
        _walking = false;
        if (!_me->IsAlive())
            return;
        _me->SetReactState(REACT_AGGRESSIVE);
        _me->GetMotionMaster()->Clear();
        if (Unit* target = _me->SelectVictim())
            _me->AI()->AttackStart(target);
    }

    Creature* _me;
    bool _examiner;
    std::shared_ptr<BenchOperation> _op;
    ObjectGuid _bench;
    std::vector<ObjectGuid> _patients;
    uint64 _clockMs = 0;
    uint64 _nextOperationMs = 0;
    uint64 _nextBackhandMs = 0;
    uint64 _nextRendMs = 0;
    uint64 _opStartMs = 0;
    uint32 _successes = 0;
    bool _eyes = false;
    bool _walking = false;
    bool _patientsOut = false;
    bool _opHeroic = false;
    bool _repick = false;                   // the last operation's seat was refused: the next pick is now
    std::vector<ObjectGuid> _refused;       // refused this slot: not picked again in it
};

namespace
{
    // Boss data (SC): target priority the Failed Patients above him; no interrupts for the group (Incision is the
    // patient's, through the bench: do-not-kick); no dispels. The bench is never a target.
    void DescribeKrastinov(Creature* me, uint32 bossEntry)
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(bossEntry, SPELL_KR_INCISION, 0);
        d.interrupts.emplace_back(bossEntry, SPELL_KR_BACKHAND, 0);
        d.targets.emplace_back(NPC_SC_FAILED_PATIENT, 2, Who::Any);
        d.targets.emplace_back(bossEntry, 1, Who::Any);
        d.ignores.emplace_back(NPC_SC_WORK_BENCH);
        Mechanic::Describe(me, std::move(d));
    }

    bool ShouldRunInCombat(Creature* me, KrastinovFight const& fight)
    {
        // Operating (passive, no victim): a wipe still resets him.
        return fight.Operating() && me->IsEngaged() && !me->GetThreatMgr().IsThreatListEmpty();
    }
}

class HallOfTheDamnedLesson;

// Doctor Theolen Krastinov 11261
struct boss_doctor_theolen_krastinov_rework : public BossAI
{
    explicit boss_doctor_theolen_krastinov_rework(Creature* creature)
        : BossAI(creature, BOSS_KRASTINOV), _arena(KrastinovFightArena(), LeashOptions(kLogBoss)),
        _fight(creature, false) { }

    void Reset() override
    {
        _Reset();
        AbortTestLesson();
        _fight.Cleanup();
        _arena.Reset();
        _grades.Reset();
    }

    // Stock SmartAI 11261 row 8: out of combat, the first player in sight (60 yd) gets emote line 0, once per spawn.
    void MoveInLineOfSight(Unit* who) override
    {
        if (!_oocEmoteDone && !me->IsInCombat() && who && who->IsPlayer() && !who->ToPlayer()->IsGameMaster()
            && me->IsWithinDistInMap(who, 60.f) && me->IsWithinLOSInMap(who))
        {
            _oocEmoteDone = true;
            Talk(EMOTE_KRASTINOV_FRENZY_OOC);
        }
        BossAI::MoveInLineOfSight(who);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        AbortTestLesson();
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_KRASTINOV;
        Mechanic::BeginEncounter(me, options);
        DescribeKrastinov(me, NPC_KRASTINOV);
        _grades.Begin(me, Instructor::Krastinov);
        _arena.Engage(me);
        _fight.Engage();
        Talk(YELL_KRASTINOV_AGGRO);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _fight.Cleanup();
        _arena.Reset();
        _grades.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        AbortTestLesson();
        _fight.Cleanup();
        Talk(YELL_KRASTINOV_DEATH);
        _grades.AwardAtDeath(me);
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kLogBoss, "death", killer ? killer->GetName() : "none");
    }

    void KilledUnit(Unit* victim) override
    {
        if (victim && victim->IsPlayer())
            Talk(YELL_KRASTINOV_SUCCESS);
    }

    // The bench and the Failed Patients are the fight's: never zoned into combat by BossAI (the patients attack on
    // their own; the bench is a vehicle prop). Tracked so BossAI's summon cleanup also catches them.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        _fight.MovementInform(type, id);
    }

    void UpdateAI(uint32 diff) override
    {
        UpdateTestLesson(diff);

        if (!_fight.Operating())
        {
            if (!UpdateVictim())
                return;
        }
        else if (!ShouldRunInCombat(me, _fight))
        {
            EnterEvadeMode(EVADE_REASON_NO_HOSTILES);
            return;
        }

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (!_fight.Update(diff))
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    KrastinovFight& Fight() { return _fight; }

    // `.dbtest scholo krastinov lesson`: the Hall of the Damned lesson on `student`, owned by him (out of combat).
    std::string StartTestLesson(Player* student, bool heroic);
    std::string TestLessonState() const;

private:
    void AbortTestLesson();
    void UpdateTestLesson(uint32 diff);

    DungeonKit::ArenaGuard _arena;
    GradeWatch _grades;
    KrastinovFight _fight;
    std::unique_ptr<SoloLesson> _testLesson;
    bool _oocEmoteDone = false;
};

// The Graduate Examiner Krastinov (S13's 300549, ScriptName npc_sc_examiner_krastinov; registered once wave C binds):
// the same fight at heroic values, on no boss state (the instructor is already dead), no grades, no texts of the boss.
struct npc_sc_examiner_krastinov : public ScriptedAI
{
    explicit npc_sc_examiner_krastinov(Creature* creature)
        : ScriptedAI(creature), _arena(KrastinovFightArena(), LeashOptions(kLogExaminer)), _fight(creature, true) { }

    void Reset() override
    {
        _fight.Cleanup();
        _arena.Reset();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        Mechanic::BeginEncounter(me);
        DescribeKrastinov(me, me->GetEntry());
        _arena.Engage(me);
        _fight.Engage();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _fight.Cleanup();
        _arena.Reset();
        Mechanic::EndEncounter(me);
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _fight.Cleanup();
        _arena.Reset();
        Mechanic::EndEncounter(me);
        DungeonKit::LogMechanic(kLogDungeon, kLogExaminer, "death");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        _fight.MovementInform(type, id);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_fight.Operating())
        {
            if (!UpdateVictim())
                return;
        }
        else if (!ShouldRunInCombat(me, _fight))
        {
            EnterEvadeMode(EVADE_REASON_NO_HOSTILES);
            return;
        }
        if (!_arena.Update(me, diff))
            return;
        if (!_fight.Update(diff))
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    DungeonKit::ArenaGuard _arena;
    KrastinovFight _fight;
};

// ---------------------------------------------------------------------------------------------------------------------
// Detention: the Hall of the Damned (SC 2966, handoff section 3.7). The empty bench straps the student in and its saw
// makes 3 cuts (the bench's own window aura; no cast bar: a cast by the student's own vehicle would block Wrench
// Free); the student interrupts with Wrench Free. A landed cut is the lesson's failure hit (15% / 25% + Weakened);
// at most 1 may land on normal, none on heroic. The cuts are dealt by the lesson owner (S11's stalker).
// ---------------------------------------------------------------------------------------------------------------------
class HallOfTheDamnedLesson : public TimedSoloLesson
{
public:
    HallOfTheDamnedLesson() : TimedSoloLesson(Classroom::HallOfTheDamned) { }

    // `.dbtest` and S11's status line.
    std::string Describe() const
    {
        if (!_op)
            return "not started";
        Operation const& s = _op->State();
        return Acore::StringFormat("phase={} cutsLeft={} landed={} interrupts={} wasted={} elapsed={:.1f}s",
            int(s.Phase()), s.StrapsLeft(), s.Landed(), s.TotalInterrupts(), s.WastedPresses(),
            Clock().ElapsedMs() / 1000.f);
    }

protected:
    uint32 AllowedFailures(bool heroic) const override { return kLessonAllowedLanded(heroic); }

    void OnStart(Creature* owner, Player* student, bool heroic) override
    {
        Creature* bench = SummonBench(owner);
        _bench = bench ? bench->GetGUID() : ObjectGuid::Empty;
        _map = owner->GetMap();
        _op = std::make_shared<BenchOperation>();
        _op->Begin(BenchOperation::Mode::Lesson, bench, student, nullptr, owner, LessonOperationRules(), heroic,
            kLogLesson);
        if (npc_sc_work_bench* ai = BenchAI(bench))
            ai->Bind(_op);
    }

    void OnUpdate(uint32 diff, Creature* /*owner*/, Player* /*student*/) override
    {
        std::shared_ptr<BenchOperation> const op = _op;
        if (!op)
            return;
        BenchOperation::Tick const tick = op->Update(diff);
        for (uint32 i = 0; i < tick.landed; ++i)
            FailStudent();
        // The three cuts are resolved: the lesson ends with its verdict.
        if (!op->Active() && op->State().Outcome() == OpOutcome::Finished)
            FinishEarly();
        // A student the bench could not seat fails the lesson (R-B K-3: never a free pass). No hits: no cut came down.
        // Any other abort leaves the lesson to its clock (a safety end comes from the base when the student died or
        // left).
        else if (!op->Active() && op->SeatRefused() && !_refusalCounted)
        {
            _refusalCounted = true;
            for (uint32 i = 0; i < RefusedSeatFailures(Heroic()); ++i)
                FailStudent();
            FinishEarly();
        }
    }

    void OnEnd(LessonEnd /*why*/, Creature* /*owner*/) override
    {
        if (_op)
            _op->Abort("lesson end");
        DespawnBench(_map, _bench);
    }

private:
    std::shared_ptr<BenchOperation> _op;
    ObjectGuid _bench;
    Map* _map = nullptr;
    bool _refusalCounted = false;
};

std::string boss_doctor_theolen_krastinov_rework::StartTestLesson(Player* student, bool heroic)
{
    if (me->IsInCombat())
        return "Krastinov must be out of combat (he owns the test lesson).";
    if (_testLesson)
        return "A test lesson is already running.";
    _testLesson = std::make_unique<HallOfTheDamnedLesson>();
    _testLesson->Start(me, student, heroic);
    return {};
}

std::string boss_doctor_theolen_krastinov_rework::TestLessonState() const
{
    if (!_testLesson)
        return "no test lesson";
    auto const* lesson = static_cast<HallOfTheDamnedLesson const*>(_testLesson.get());
    return lesson->Describe();
}

void boss_doctor_theolen_krastinov_rework::AbortTestLesson()
{
    if (_testLesson)
    {
        _testLesson->Abort();
        _testLesson.reset();
    }
}

void boss_doctor_theolen_krastinov_rework::UpdateTestLesson(uint32 diff)
{
    if (!_testLesson)
        return;
    _testLesson->Update(diff);
    if (_testLesson->Done())
    {
        DungeonKit::LogMechanic(kLogDungeon, kLogLesson, "test-lesson-done",
            _testLesson->Passed() ? "pass" : _testLesson->Failed() ? "fail" : "no verdict");
        _testLesson.reset();
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Spell scripts
// ---------------------------------------------------------------------------------------------------------------------

// KR2 Wrench Free 206227: the bench's vehicle button, cast by the bench (its passenger controls it). Refused while the
// bench's cooldown runs (the server never adds a cooldown to a vehicle's cast by itself; mod-playerbots reads it with
// Creature::HasSpellCooldown); on a hit, the running operation decides (interrupt, wasted, escape).
class spell_sc_krastinov_wrench_free : public SpellScript
{
    PrepareSpellScript(spell_sc_krastinov_wrench_free);

    SpellCastResult CheckCast()
    {
        Creature* bench = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!bench || bench->GetEntry() != NPC_SC_WORK_BENCH)
            return SPELL_FAILED_BAD_TARGETS;
        if (bench->HasSpellCooldown(SPELL_KR_WRENCH_FREE))
            return SPELL_FAILED_NOT_READY;
        return SPELL_CAST_OK;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Creature* bench = GetCaster() ? GetCaster()->ToCreature() : nullptr;
        if (!bench)
            return;
        bench->AddSpellCooldown(SPELL_KR_WRENCH_FREE, 0, 0);      // RecoveryTime 3 s; told to the passenger
        Player* presser = nullptr;
        if (Vehicle* kit = bench->GetVehicleKit())
            if (Unit* passenger = kit->GetPassenger(kBenchSeat))
                presser = passenger->ToPlayer();
        if (npc_sc_work_bench* ai = BenchAI(bench))
            if (std::shared_ptr<BenchOperation> op = ai->Op())
                op->WrenchFree(presser);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_sc_krastinov_wrench_free::CheckCast);
        OnEffectHitTarget += SpellEffectFn(spell_sc_krastinov_wrench_free::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// KR3 Incision 206230 and KR8 Backhand 206238: base point 0 carries the percent (die 0); the hit is that percent of
// the reference row for the target (the tank row on the tank), set at launch so the target's defensives count (the
// spells ignore caster modifiers).
class spell_sc_krastinov_ref_hit : public SpellScript
{
    PrepareSpellScript(spell_sc_krastinov_ref_hit);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float const pct = static_cast<float>(GetEffectValue());
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sc_krastinov_ref_hit::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// KR9 Butcher's Rend 206239 and KR7 Infected Claws 206240: a bleed whose tick is base point 0 percent of the reference
// row for the target (the tank row on the tank), per stack.
class spell_sc_krastinov_ref_dot : public AuraScript
{
    PrepareAuraScript(spell_sc_krastinov_ref_dot);

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        float const pct = static_cast<float>(amount);
        amount = static_cast<int32>(DungeonKit::RefFlatOn(GetCaster(), GetUnitOwner(), pct));
        canBeRecalculated = true;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_sc_krastinov_ref_dot::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest scholo krastinov <sub> [1]` (the optional 1 forces the heroic form, 0 normal; default: the map's)
// ---------------------------------------------------------------------------------------------------------------------
namespace
{
    boss_doctor_theolen_krastinov_rework* FindKrastinovAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_KRASTINOV);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_doctor_theolen_krastinov_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Krastinov is not running boss_doctor_theolen_krastinov_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool HeroicArg(boss_doctor_theolen_krastinov_rework* ai, Optional<uint32> heroic)
    {
        return heroic ? *heroic != 0 : ai->Fight().Heroic();
    }

    // The selected player, else the GM.
    Player* TargetPlayer(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetPlayer();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_KRASTINOV, BOSS_KRASTINOV);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_doctor_theolen_krastinov_rework* ai = FindKrastinovAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Krastinov: {}", ai->Fight().State());
        handler->PSendSysMessage("Test lesson: {}", ai->TestLessonState());
        return true;
    }

    // KR1: an operation now on the selected player (or the GM: a solo GM is his victim, so the pick would skip).
    bool HandleOperation(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_doctor_theolen_krastinov_rework* ai = FindKrastinovAI(handler);
        if (!ai)
            return false;
        Creature* boss = ScholoTest::FindBoss(handler, NPC_KRASTINOV);
        if (!boss || !boss->IsEngaged())
        {
            handler->SendErrorMessage("{}", "Krastinov must be in combat (the operation is part of the fight).");
            return false;
        }
        bool const isHeroic = HeroicArg(ai, heroic);
        Player* patient = TargetPlayer(handler);
        if (!ai->Fight().StartOperation(patient, isHeroic))
        {
            handler->SendErrorMessage("{}", "No operation: one is already running, or no bench.");
            return false;
        }
        handler->PSendSysMessage("Krastinov: operation on {} ({}).", patient->GetName(),
            isHeroic ? "heroic" : "normal");
        return true;
    }

    // KR7: the Failed Patients now (heroic: fixated on the patient on the bench when one is there).
    bool HandlePatients(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_doctor_theolen_krastinov_rework* ai = FindKrastinovAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = HeroicArg(ai, heroic);
        std::shared_ptr<BenchOperation> const op = ai->Fight().Op();
        ai->Fight().ReleasePatients(op ? op->Patient() : nullptr, isHeroic);
        handler->PSendSysMessage("Krastinov: Failed Patients released ({}).", isHeroic ? "heroic" : "normal");
        return true;
    }

    // KR2 as the patient: presses Wrench Free for the selected player (or the GM) on the bench (the button's own
    // path: the bench casts it).
    bool HandleWrench(ChatHandler* handler)
    {
        Player* patient = TargetPlayer(handler);
        Unit* base = patient ? patient->GetVehicleBase() : nullptr;
        if (!base || !base->IsCreature() || base->GetEntry() != NPC_SC_WORK_BENCH)
        {
            handler->SendErrorMessage("{}", "That player is not on the Work Bench.");
            return false;
        }
        SpellCastResult const result = base->CastSpell(base, SPELL_KR_WRENCH_FREE, false);
        handler->PSendSysMessage("Wrench Free: cast result {}.", int(result));
        return true;
    }

    // KR6: the next graft now.
    bool HandleGraft(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_doctor_theolen_krastinov_rework* ai = FindKrastinovAI(handler);
        if (!ai)
            return false;
        ai->Fight().TakeGraft(HeroicArg(ai, heroic));
        handler->PSendSysMessage("Krastinov: {}", ai->Fight().State());
        return true;
    }

    bool HandleBackhand(ChatHandler* handler)
    {
        boss_doctor_theolen_krastinov_rework* ai = FindKrastinovAI(handler);
        if (!ai)
            return false;
        ai->Fight().TestBackhand();
        handler->PSendSysMessage("{}", "Krastinov: Backhand at his next free moment (in combat, not operating).");
        return true;
    }

    bool HandleRend(ChatHandler* handler)
    {
        boss_doctor_theolen_krastinov_rework* ai = FindKrastinovAI(handler);
        if (!ai)
            return false;
        ai->Fight().TestRend();
        handler->PSendSysMessage("{}", "Krastinov: Butcher's Rend at his next free moment (victim in melee range).");
        return true;
    }

    // Detention: the Hall of the Damned lesson on the selected player (or the GM), owned by Krastinov (alive, out of
    // combat; S11 uses its lesson stalker instead). The lesson stops at once when nobody else in the instance is alive
    // (its safety rule): test it with a second player or a bot.
    bool HandleLesson(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_doctor_theolen_krastinov_rework* ai = FindKrastinovAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : false;
        Player* student = TargetPlayer(handler);
        std::string const error = ai->StartTestLesson(student, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Hall of the Damned lesson on {} ({}).", student->GetName(),
            isHeroic ? "heroic" : "normal");
        return true;
    }

    ChatCommandTable const& KrastinovTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "operation", HandleOperation, SEC_GAMEMASTER, Console::No },
            { "patients",  HandlePatients,  SEC_GAMEMASTER, Console::No },
            { "wrench",    HandleWrench,    SEC_GAMEMASTER, Console::No },
            { "graft",     HandleGraft,     SEC_GAMEMASTER, Console::No },
            { "backhand",  HandleBackhand,  SEC_GAMEMASTER, Console::No },
            { "rend",      HandleRend,      SEC_GAMEMASTER, Console::No },
            { "lesson",    HandleLesson,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_doctor_theolen_krastinov_rework()
{
    RegisterDungeonReworkCreatureAI(boss_doctor_theolen_krastinov_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_work_bench, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_failed_patient, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_sc_krastinov_wrench_free);
    RegisterSpellScript(spell_sc_krastinov_ref_hit);
    RegisterSpellScript(spell_sc_krastinov_ref_dot);
    ScholomanceRework::RegisterSoloLesson(Classroom::HallOfTheDamned,
        [] { return std::unique_ptr<SoloLesson>(new HallOfTheDamnedLesson()); });
    ScholoTest::RegisterBoss("krastinov", KrastinovTestCommands());
    // The Graduate Exam's examiner (S13 binds creature_template 300549 to this name): registered only once wave C
    // binds, so a wave B boot names no unassigned script.
    if (kWaveCBound)
        RegisterDungeonReworkCreatureAI(npc_sc_examiner_krastinov, ScholomanceRework::kInstanceScriptName);
}
