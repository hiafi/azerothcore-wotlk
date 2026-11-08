/*
 * mod-dungeon-bosses, Scholomance S3: Marduk Blackpool (10433) and Vectus (10432), one encounter on BOSS_MARDUK_VECTUS
 * with one shared health pool, the Scholomance Students 10475 as props and the Graduate 300533.
 * Build spec: SC 934-991 (docs/dungeons/scholomance-rework.md), MV1-MV7; handoff section 3.5 row S3, section 3.6.
 * Replaces SmartAI 10433, 10432 and 10475 (the WP-S3 SQL rev deletes them); the stock behaviors kept are carried here:
 * Marduk's Defiling Aura, Vectus's Blast Wave and idle lecture, and Dawn's Gambit (quest 4771: Marduk's "We are
 * betrayed!", Vectus's yell, the students' fall and transform).
 *
 *   The encounter   a pull of either brings in the other; damage to either comes off both (the Twin Val'kyr pattern,
 *                   boss_twin_valkyr.cpp UpdateSharedHealth), the bars always match, and the first death kills the
 *                   other (the encounter goes DONE on the second). Vectus owns the registry encounter (Marduk is a
 *                   tracked unit), so one descriptor and one failure ledger serve both.
 *   Syllabus        Vectus calls a lesson every 12 s (normal: Drill, Group Exercise, Pop Quiz in order) or 10 s
 *                   (heroic: shuffled), first at 8 s; each call is a yell naming it. Heroic double period: below 50%
 *                   of the shared health every call names two lessons (yell 5 the first time).
 *   MV1 Drill       6 / 9 students cast a 3 s Flamestrike at random floor points, never on a player: 6 yd circles,
 *                   45% / 60% Fire, no Weakened; heroic, the circles burn 10 s (ImpactThenLinger).
 *   MV2 Exercise    a 6 yd Stack on a marked non-tank (4 s); the students fire Shadow Bolts at the target: 160% / 240%
 *                   split among the players inside, at most 75% each (DungeonKit::SplitShares).
 *   MV3 Pop Quiz    one student stands (attackable, 8k / 12k) and casts a 5 s interruptible volley; finished, it hits
 *                   everyone for 30% / 50% and the student graduates: a Graduate (15k / 22k, Shadow Bolt on random
 *                   players) joins the fight, at most 3 alive at once; interrupted, the student sits back down.
 *   MV4 Ebon Sweep  Marduk: every 15 s from 10 s, a 2 s wind-up and emote, then a 10 yd Frontal of 90 / 120 degrees,
 *                   60% / 70% Shadow to everyone in it but his target; the tank takes his own heavy hit (R2 S-1).
 *   MV5 Fireball    Vectus casts it at random players between everything else (a real 3 s cast, do-not-kick).
 *   MV6 Whirlwind   heroic: every 30 s from 20 s, a 2 s cast and emote, then a 4 s rooted spin, an 8 yd circle on
 *                   Marduk ticking 20% Physical every 1 s, one Weakened on a player's first tick per spin. Ebon Sweep
 *                   waits for the spin.
 *   MV7 Blast Wave  stock 17277 from Vectus when anyone stands within 10 yd (the cost of stacking the two).
 *
 * Pilot lessons: the custom damage spells ignore caster modifiers (registry resolve copies; the script hits set their
 * value at launch, so the target's defensives count); every timer runs on `_timers` / `_followups` (never on
 * BossAI::scheduler or events, which a cast pauses); mechanic emotes are type 41; every hit has a look on the player
 * (impact visuals on every copy); the bosses cannot be kited off the Viewing Room (ArenaGuard, MardukVectusArena()).
 * Each firing logs `scholo vectus|marduk <mechanic> ...` (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MardukVectusLogic.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TaskScheduler.h"
#include <algorithm>
#include <list>
#include <string>
#include <string_view>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoMardukVectus;
using BossMechanics::MechanicRef;

namespace
{
    using Ms = Milliseconds;

    // SetGUID ids on Vectus: a quiz student reports how its quiz ended.
    int32 constexpr kGuidQuizFinished = 0x4D560301;
    int32 constexpr kGuidQuizStopped = 0x4D560302;
    int32 constexpr kGuidQuizKilled = 0x4D560303;

    // DoAction ids on a student.
    int32 constexpr kActionStudentQuiz = 0x4D560311;      // stand and take the quiz
    int32 constexpr kActionStudentRestore = 0x4D560312;   // back to its desk as a prop (visible)
    int32 constexpr kActionStudentGraduate = 0x4D560313;  // graduated: hidden until the class is reset

    uint32 constexpr kPropFlags = UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE;

    Ms RandomMs(uint32 min, uint32 max)
    {
        return Ms(urand(min, max));
    }

    float Rand01()
    {
        return static_cast<float>(rand_norm());
    }

    Vec2 PlaneOf(WorldObject const* o)
    {
        return DungeonKit::PlaneOf(o);
    }

    void LogMV(char const* boss, char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, boss, mechanic, detail);
    }

    Creature* FindByData(WorldObject* from, uint32 dataId)
    {
        InstanceScript* instance = from ? from->GetInstanceScript() : nullptr;
        return instance ? instance->GetCreature(dataId) : nullptr;
    }

    bool EncounterRunning(WorldObject* from)
    {
        InstanceScript* instance = from ? from->GetInstanceScript() : nullptr;
        return instance && instance->GetBossState(BOSS_MARDUK_VECTUS) == IN_PROGRESS;
    }

    // The registry encounter's owner: Vectus while he lives (he calls the lessons), else the caller itself.
    Unit* EncounterOwner(Creature* caller)
    {
        if (Creature* vectus = FindByData(caller, DATA_VECTUS_GUID); vectus && vectus->IsAlive() && vectus->IsInWorld())
            return vectus;
        return caller;
    }

    // The students of the hall (dead and hidden ones too).
    std::vector<Creature*> Students(WorldObject* center)
    {
        std::vector<Creature*> out;
        if (!center || !center->IsInWorld())
            return out;
        std::list<Creature*> found;
        center->GetCreatureListWithEntryInGrid(found, NPC_SCHOLOMANCE_STUDENT, kStudentSearchYd);
        out.assign(found.begin(), found.end());
        return out;
    }

    // The living, alive players of the map (no game masters): the Drill keeps its circles off them.
    std::vector<Vec2> PlayerSpots(Map* map)
    {
        std::vector<Vec2> out;
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource(); player && player->IsAlive() && !player->IsGameMaster())
                out.push_back(PlaneOf(player));
        return out;
    }

    // A resolve callback that reaches the AI of `guid` on `map` (capture guids only, never a Unit*).
    template <class AI, class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnAI(Map* map, ObjectGuid guid, Fn fn)
    {
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            Creature* creature = map ? map->GetCreature(guid) : nullptr;
            if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
                return;
            if (AI* ai = dynamic_cast<AI*>(creature->AI()))
                fn(*ai, result);
        };
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Scholomance Student 10475 (32 spawns in the Viewing Room): a prop at its desk. Not selectable and not attackable
// (also set by the template; the script enforces it, since a heroic template copies the stock row), never aggroes and
// never swings. It casts the lessons Vectus calls; the quiz student stands, becomes attackable and casts the Pop Quiz.
// Dawn's Gambit (SetData(2, 3) and (2, 4) from GO 176110) still makes the class fall and rise as skeletons.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sc_student : public ScriptedAI
{
    enum class State : uint8
    {
        Prop,
        Quiz,
        Graduated,      // hidden until the class is reset
    };

    explicit npc_sc_student(Creature* creature) : ScriptedAI(creature)
    {
        CreatureAddon const* addon = creature->GetCreatureAddon();
        _homeStand = addon ? static_cast<uint8>(addon->bytes1 & 0xFF) : static_cast<uint8>(UNIT_STAND_STATE_STAND);
    }

    void Reset() override
    {
        if (_state == State::Graduated)
        {
            ApplyPropFlags();
            return;
        }
        BackToDesk();
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (_hideInMs)
        {
            _hideInMs = _hideInMs > diff ? _hideInMs - diff : 0;
            if (!_hideInMs && _state == State::Graduated)
                me->SetVisible(false);
        }
        // A student a lesson put in combat (its bolts, a quiz) leaves it when the encounter is over.
        if (me->IsInCombat() && !EncounterRunning(me) && !me->IsNonMeleeSpellCast(false))
            EnterEvadeMode(EVADE_REASON_OTHER);
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case kActionStudentQuiz:
                StartQuiz();
                break;
            case kActionStudentRestore:
                _state = State::Prop;
                _hideInMs = 0;
                me->SetVisible(true);
                BackToDesk();
                break;
            case kActionStudentGraduate:
                // Hidden a moment later, so the volley it just cast leaves its hands first.
                _state = State::Graduated;
                me->RemoveAurasDueToSpell(SPELL_MV_ON_THE_SPOT);
                ApplyPropFlags();
                _hideInMs = kGraduateHideMs;
                break;
            default:
                break;
        }
    }

    // Dawn's Gambit (stock SmartAI 10475 rows 1-5): the students fall (Resurrection 58854's look, dead stand state),
    // then rise as skeletons (Viewing Room Student Transform 18115). They stay props: the stock faction change (21)
    // is not carried, since a prop never fights (the lessons are boss spells, so the transform's -75% damage done
    // never touches them; SC "Stock kit").
    void SetData(uint32 id, uint32 value) override
    {
        if (id != kGambitDataId)
            return;
        if (value == kGambitStudentsFall)
        {
            DoCastSelf(SPELL_GAMBIT_RESURRECTION, true);
            me->SetStandState(UNIT_STAND_STATE_DEAD);
        }
        else if (value == kGambitStudentsRise)
        {
            DoCastSelf(SPELL_GAMBIT_TRANSFORM, true);
            me->SetStandState(_homeStand == UNIT_STAND_STATE_DEAD ? uint8(UNIT_STAND_STATE_STAND) : _homeStand);
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_MV_POP_QUIZ && _state == State::Quiz)
            Report(kGuidQuizFinished);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_MV_POP_QUIZ && _state == State::Quiz)
            Report(kGuidQuizStopped);
    }

    void JustDied(Unit* /*killer*/) override
    {
        if (_state == State::Quiz)
            Report(kGuidQuizKilled);
        _state = State::Prop;
    }

    // A free student: a prop at its desk, alive, visible, standing still (never the one patrolling student) and not
    // casting a lesson.
    bool Free() const
    {
        return _state == State::Prop && me->IsAlive() && me->IsVisible() && !me->IsNonMeleeSpellCast(false)
            && me->GetDefaultMovementType() == IDLE_MOTION_TYPE;
    }

    bool InQuiz() const { return _state == State::Quiz; }

private:
    void ApplyPropFlags()
    {
        me->SetUnitFlag(UnitFlags(kPropFlags));
        me->SetReactState(REACT_PASSIVE);
    }

    void BackToDesk()
    {
        _state = State::Prop;
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        me->RemoveAurasDueToSpell(SPELL_MV_ON_THE_SPOT);
        ApplyPropFlags();
        if (me->IsAlive())
        {
            me->SetFullHealth();
            me->SetStandState(_homeStand);
        }
    }

    // MV3: stand, become the class's target and cast the volley (5 s, interruptible).
    void StartQuiz()
    {
        if (!me->IsAlive())
            return;
        _state = State::Quiz;
        me->RemoveUnitFlag(UnitFlags(kPropFlags));
        me->SetStandState(UNIT_STAND_STATE_STAND);
        DoCastSelf(SPELL_MV_ON_THE_SPOT, true);
        if (me->CastSpell(me, SPELL_MV_POP_QUIZ, false) != SPELL_CAST_OK)
            Report(kGuidQuizStopped);
    }

    void Report(int32 how)
    {
        _state = State::Prop;
        if (Creature* vectus = FindByData(me, DATA_VECTUS_GUID); vectus && vectus->IsAIEnabled)
            vectus->AI()->SetGUID(me->GetGUID(), how);
        else
            BackToDesk();
    }

    static uint32 constexpr kGraduateHideMs = 800;

    State _state = State::Prop;
    uint8 _homeStand = UNIT_STAND_STATE_STAND;
    uint32 _hideInMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// The Graduate 300533: a student whose quiz finished. Stays where it stood and casts Shadow Bolt (206166, a real 2 s
// cast, 10% of the reference row) at random players in sight.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sc_graduate : public ScriptedAI
{
    explicit npc_sc_graduate(Creature* creature) : ScriptedAI(creature)
    {
        me->SetCombatMovement(false);
    }

    void Reset() override
    {
        _timers.CancelAll();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _timers.CancelAll();
        _timers.Schedule(Ms(kGraduateBoltFirstMs), [this](TaskContext context)
        {
            if (me->IsNonMeleeSpellCast(false))
            {
                context.Repeat(Ms(kBusyRetryMs));
                return;
            }
            Bolt();
            context.Repeat(RandomMs(kGraduateBoltMinMs, kGraduateBoltMaxMs));
        });
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        _timers.Update(diff);
    }

    void Bolt()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kGraduateRangeYd;
        rule.requireLos = true;
        if (Player* target = DungeonKit::PickPlayer(me, rule))
            me->CastSpell(target, SPELL_MV_GRADUATE_BOLT, false);
    }

private:
    TaskScheduler _timers;
};

// ---------------------------------------------------------------------------------------------------------------------
// Marduk and Vectus: the shared part (one encounter, the shared pool, the pull, the evade, the deaths, the arena)
// ---------------------------------------------------------------------------------------------------------------------
struct boss_marduk_vectus_rework_base : public BossAI
{
    boss_marduk_vectus_rework_base(Creature* creature, char const* logName, uint32 partnerGuidData)
        : BossAI(creature, BOSS_MARDUK_VECTUS), _logName(logName), _partnerGuidData(partnerGuidData),
        _arena(MardukVectusArena(), LeashOptions(logName)) { }

    void Reset() override
    {
        _Reset();
        EndFight();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _arena.Engage(me);
        // One encounter: the partner joins the pull.
        if (Creature* partner = Partner(); partner && partner->IsAlive() && !partner->IsInCombat() && who
            && partner->IsAIEnabled)
            partner->AI()->AttackStart(who);
        OnEngage(DungeonKit::IsHeroicMap(me));
        LogMV(_logName, "engage", Acore::StringFormat("heroic={} health={} at=({:.1f}, {:.1f}, {:.1f})",
            DungeonKit::IsHeroicMap(me) ? 1 : 0, me->GetMaxHealth(), me->GetPositionX(), me->GetPositionY(),
            me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        EndFight();
        BossAI::EnterEvadeMode(why);
        // One encounter: the partner leaves with him (its own evade finds this one out of combat and stops there).
        if (Creature* partner = Partner(); partner && partner->IsAlive() && partner->IsInCombat()
            && partner->IsAIEnabled)
            partner->AI()->EnterEvadeMode(why);
    }

    // The shared pool: whatever this one takes, the partner takes (no threat, no procs: the health only, plus the
    // loot and reward bookkeeping Unit::DealDamage would do, so damage on either counts for both kills).
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*damageType*/,
        SpellSchoolMask /*schoolMask*/) override
    {
        Creature* partner = Partner();
        if (!damage || !partner || !partner->IsAlive())
            return;
        uint32 const partnerHealth = partner->GetHealth();
        switch (MirrorFor(me->GetHealth(), partnerHealth, damage))
        {
            case Mirror::Apply:
                partner->ModifyHealth(-static_cast<int32>(damage));
                break;
            case Mirror::Clamp:
                partner->SetHealth(1);
                break;
            case Mirror::LetDie:    // this one dies; JustDied kills the partner
            case Mirror::None:
                break;
        }
        if (!attacker)
            return;
        if (!partner->hasLootRecipient())
            partner->SetLootRecipient(attacker);
        if (Player* player = attacker->GetCharmerOrOwnerPlayerOrPlayerItself())
            partner->LowerPlayerDamageReq(std::min(partnerHealth, damage), true, player->GetLevel());
    }

    void JustDied(Unit* killer) override
    {
        EndFight();
        LogMV(_logName, "death");
        if (Creature* partner = Partner(); partner && partner->IsAlive())
        {
            // The pool is empty: the partner falls with him and its death finishes the encounter (DONE). His own
            // summons go now (the partner's go with its own death).
            events.Reset();
            scheduler.CancelAll();
            summons.DespawnAll();
            Unit::Kill(killer ? killer : partner, partner);
            return;
        }
        BossAI::JustDied(killer);
    }

protected:
    virtual void OnEngage(bool heroic) = 0;
    virtual void OnEndFight() { }

    void EndFight()
    {
        _timers.CancelAll();
        _followups.CancelAll();
        _arena.Reset();
        OnEndFight();
    }

    Creature* Partner() const
    {
        return instance ? instance->GetCreature(_partnerGuidData) : nullptr;
    }

public:
    Creature* Self() const { return me; }

protected:

    // The bars always match (a heal or a regen tick on one is undone).
    void SyncHealth()
    {
        Creature* partner = Partner();
        if (!partner || !partner->IsAlive() || !me->IsAlive())
            return;
        uint32 const health = SyncedHealth(me->GetHealth(), partner->GetHealth());
        if (me->GetHealth() != health)
            me->SetHealth(health);
        if (partner->GetHealth() != health)
            partner->SetHealth(health);
    }

    char const* _logName;
    uint32 _partnerGuidData;
    DungeonKit::ArenaGuard _arena;
    // Every timer lives here, never on BossAI::scheduler or events (a cast pauses those).
    TaskScheduler _timers;
    TaskScheduler _followups;   // follow-ups scheduled from inside a `_timers` task
    uint32 _clockMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Marduk Blackpool 10433: tanked. Defiling Aura on the pull, MV4 Ebon Sweep, heroic MV6 Whirlwind, stock melee.
// ---------------------------------------------------------------------------------------------------------------------
struct boss_marduk_blackpool_rework : public boss_marduk_vectus_rework_base
{
    explicit boss_marduk_blackpool_rework(Creature* creature)
        : boss_marduk_vectus_rework_base(creature, "marduk", DATA_VECTUS_GUID) { }

    // Dawn's Gambit: "We are betrayed!" (stock SmartAI 10433 rows 0 and 1).
    void SetData(uint32 id, uint32 value) override
    {
        if (id != kGambitDataId)
            return;
        if (value == kGambitMardukFirst)
            Talk(SAY_MARDUK_BETRAYED);
        else if (value == kGambitMardukSecond)
            Talk(SAY_MARDUK_BETRAYED_2);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // Out of combat too: a `.dbtest scholo marduk` mechanic's follow-ups. Never paused by a cast.
        _timers.Update(diff);
        _followups.Update(diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off the Viewing Room, or nobody in it for 10 s: evading
        SyncHealth();

        if (_spinning || me->IsActionPreventedByCasting())
            return;
        DoMeleeAttackIfReady();
    }

    // MV4: the wind-up now (cast bar and emote), the Frontal on him; its resolve hits the tank with his own spell.
    void EbonSweep()
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        Unit* owner = EncounterOwner(me);
        if (Unit* victim = me->GetVictim())
            me->SetFacingToObject(victim);
        _busyUntilMs = _clockMs + kSweepWarnMs;
        DungeonKit::CastBar(me, SPELL_MV_EBON_SWEEP_BAR, nullptr, EMOTE_MARDUK_EBON_SWEEP);
        float const angle = kSweepAngleDeg(heroic);
        Mechanic::Cone(owner, me, angle, kSweepLengthYd, Ms(kSweepWarnMs), BossMechanics::TankExempt::Yes)
            .Damage(kSweepPct(heroic)).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_MV_EBON_SWEEP).Tag(TAG_MV_EBON_SWEEP)
            .OnResolve(OnAI<boss_marduk_blackpool_rework>(me->GetMap(), me->GetGUID(),
                [](boss_marduk_blackpool_rework& ai, BossMechanics::ResolveResult const& result)
                {
                    ai.SweepResolved(result);
                }));
        LogMV("marduk", "ebon-sweep", Acore::StringFormat("heroic={} angle={:.0f} pct={:.0f}", heroic ? 1 : 0, angle,
            kSweepPct(heroic)));
    }

    // MV6 (heroic; `.dbtest scholo marduk whirlwind` on any difficulty): the cast bar now, the spin as it ends; the
    // registry circle on him owns the ticks.
    void Whirlwind()
    {
        Unit* owner = EncounterOwner(me);
        _busyUntilMs = _clockMs + kWhirlwindCastMs + kWhirlwindSpinMs;
        DungeonKit::CastBar(me, SPELL_MV_WHIRLWIND_BAR, nullptr, EMOTE_MARDUK_WHIRLWIND);
        Mechanic::Circle(owner, me, kWhirlwindRadiusYd, Ms(kWhirlwindCastMs))
            .Persistent(Ms(kWhirlwindSpinMs), Ms(kWhirlwindTickMs)).Damage(kWhirlwindPct)
            .School(SPELL_SCHOOL_NORMAL).Spell(SPELL_MV_WHIRLWIND).WeakenedOncePerPlayer().Tag(TAG_MV_WHIRLWIND);
        _followups.Schedule(Ms(kWhirlwindCastMs), [this](TaskContext)
        {
            StartSpin();
        });
        _followups.Schedule(Ms(kWhirlwindCastMs + kWhirlwindSpinMs), [this](TaskContext)
        {
            EndSpin();
        });
        LogMV("marduk", "whirlwind", Acore::StringFormat("radius={:.0f} pct={:.0f}", kWhirlwindRadiusYd,
            kWhirlwindPct));
    }

    uint32 BusyForMs() const { return MoveWaitMs(_clockMs, _busyUntilMs); }
    bool Spinning() const { return _spinning; }

private:
    void OnEngage(bool heroic) override
    {
        DoCastSelf(SPELL_DEFILING_AURA, true);
        _timers.Schedule(Ms(kSweepFirstMs), [this](TaskContext context)
        {
            if (uint32 const wait = BusyForMs())
            {
                context.Repeat(Ms(wait + kBusyRetryMs));
                return;
            }
            if (me->IsNonMeleeSpellCast(false))
            {
                context.Repeat(Ms(kBusyRetryMs));
                return;
            }
            EbonSweep();
            context.Repeat(Ms(kSweepEveryMs));
        });
        if (heroic)
            _timers.Schedule(Ms(kWhirlwindFirstMs), [this](TaskContext context)
            {
                if (BusyForMs() || me->IsNonMeleeSpellCast(false))
                {
                    context.Repeat(Ms(kBusyRetryMs));
                    return;
                }
                Whirlwind();
                context.Repeat(Ms(kWhirlwindEveryMs));
            });
    }

    void OnEndFight() override
    {
        EndSpin();
        _busyUntilMs = 0;
    }

    // The cone skipped the tank (TankExempt): his target takes the heavy hit if it stands in the arc.
    void SweepResolved(BossMechanics::ResolveResult const& result)
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        Unit* tank = me->GetVictim();
        bool hitTank = false;
        if (tank && tank->IsAlive() && DungeonKit::InFrontalCone(PlaneOf(me), me->GetOrientation(), PlaneOf(tank),
            kSweepAngleDeg(heroic), kSweepLengthYd, me->GetCombatReach() + tank->GetCombatReach()))
        {
            me->CastSpell(tank, SPELL_MV_EBON_SWEEP_TANK, true);
            hitTank = true;
        }
        LogMV("marduk", "ebon-sweep-resolve", Acore::StringFormat("hit={} tank={}", result.hits.size(),
            hitTank ? tank->GetName() : std::string("none")));
    }

    void StartSpin()
    {
        if (!me->IsAlive())
            return;
        me->CastSpell(me, SPELL_MV_WHIRLWIND_SPIN, true);
        me->SetControlled(true, UNIT_STATE_ROOT);
        _spinning = true;
        LogMV("marduk", "whirlwind-spin", Acore::StringFormat("ms={}", kWhirlwindSpinMs));
    }

    void EndSpin()
    {
        if (!_spinning)
            return;
        _spinning = false;
        me->SetControlled(false, UNIT_STATE_ROOT);
        me->RemoveAurasDueToSpell(SPELL_MV_WHIRLWIND_SPIN);
    }

    uint32 _busyUntilMs = 0;
    bool _spinning = false;
};

// ---------------------------------------------------------------------------------------------------------------------
// Vectus 10432: not tanked; stays at his lectern (no combat movement, no melee), owns the registry encounter, calls
// the lessons, casts Fireball between them and Blast Wave at anyone close; keeps his idle lecture out of combat.
// ---------------------------------------------------------------------------------------------------------------------
struct boss_vectus_rework : public boss_marduk_vectus_rework_base
{
    explicit boss_vectus_rework(Creature* creature)
        : boss_marduk_vectus_rework_base(creature, "vectus", DATA_MARDUK_GUID)
    {
        me->SetCombatMovement(false);
    }

    void Reset() override
    {
        boss_marduk_vectus_rework_base::Reset();
        _lectureMs = urand(kLectureFirstMinMs, kLectureFirstMaxMs);
        ResetClass(true);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        boss_marduk_vectus_rework_base::EnterEvadeMode(why);
        ResetClass(true);
    }

    void JustDied(Unit* killer) override
    {
        boss_marduk_vectus_rework_base::JustDied(killer);
        ResetClass(false);
    }

    // Dawn's Gambit: "What is this?! How dare you!" (stock SmartAI 10432 row 0).
    void SetData(uint32 id, uint32 value) override
    {
        if (id == kGambitDataId && value == kGambitVectus)
            Talk(YELL_VECTUS_AGGRO);
    }

    // A quiz student reports how its quiz ended.
    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        switch (id)
        {
            case kGuidQuizFinished:
                QuizEnded(guid, FinishedQuiz(LivingGraduates()));
                break;
            case kGuidQuizStopped:
                QuizEnded(guid, QuizEnd::Stopped);
                break;
            case kGuidQuizKilled:
                QuizEnded(guid, QuizEnd::Killed);
                break;
            default:
                break;
        }
    }

    void JustSummoned(Creature* summon) override
    {
        BossAI::JustSummoned(summon);
        if (summon->GetEntry() == NPC_SC_GRADUATE)
            Mechanic::TrackUnit(me, summon);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // Out of combat too: a `.dbtest scholo marduk` lesson's follow-ups. Never paused by a cast.
        _timers.Update(diff);
        _followups.Update(diff);

        if (!me->IsInCombat())
        {
            UpdateLecture(diff);
            return;
        }
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // nobody in the Viewing Room for 10 s: evading
        SyncHealth();
        UpdateBlastWave(diff);
        UpdateFireball(diff);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The syllabus
    // ----------------------------------------------------------------------------------------------------------------

    void CallLesson()
    {
        bool const heroic = DungeonKit::IsHeroicMap(me);
        auto rand = [](uint32 n) { return n ? urand(0, n - 1) : 0u; };
        if (DoublePeriod(heroic, me->GetHealthPct()))
        {
            if (!_doubleAnnounced)
            {
                Talk(YELL_VECTUS_DOUBLE_PERIOD);
                _doubleAnnounced = true;
                LogMV("vectus", "double-period", Acore::StringFormat("health={:.1f}%", me->GetHealthPct()));
            }
            for (Lesson l : _syllabus.NextTwo(rand))
                Teach(l, heroic);
            return;
        }
        Teach(_syllabus.Next(rand), heroic);
    }

    // One lesson: the yell names it, then the class does it.
    void Teach(Lesson lesson, bool heroic)
    {
        Talk(LessonYell(lesson));
        switch (lesson)
        {
            case Lesson::Drill:
                Drill(heroic);
                break;
            case Lesson::GroupExercise:
                GroupExercise(heroic, nullptr);
                break;
            case Lesson::PopQuiz:
                PopQuiz();
                break;
        }
    }

    // MV1: the free students nearest each point cast the 3 s Flamestrike there; the registry circle owns the hit.
    void Drill(bool heroic)
    {
        Map* map = me->GetMap();
        uint32 const phase = me->GetPhaseMask();
        auto floorZ = [map, phase](Vec2 p) -> std::optional<float>
        {
            float const z = map->GetHeight(phase, p.x, p.y, kViewingFloorProbeZ, true, 15.f);
            if (z < kViewingFloorZMin || z > kViewingFloorZMax)
                return std::nullopt;
            return z;
        };
        std::vector<Vec2> const points = PickDrillPoints(kDrillCount(heroic), PlayerSpots(map), Rand01,
            [&floorZ](Vec2 p) { return floorZ(p).has_value(); });

        std::vector<Creature*> students = FreeStudents();
        uint32 cast = 0;
        for (Vec2 const& p : points)
        {
            Position const at = DungeonKit::ToPosition(p, floorZ(p).value_or(100.f));
            if (heroic)
            {
                DungeonKit::ImpactSpec impact;
                impact.shape = BossMechanics::Shapes::Circle(at, kDrillRadiusYd);
                impact.warn = Ms(kDrillWarnMs);
                impact.pct = kDrillPct(true);
                impact.school = SPELL_SCHOOL_FIRE;
                impact.spellId = SPELL_MV_DRILL;
                impact.weakened = false;
                impact.tag = TAG_MV_DRILL;
                DungeonKit::LingerSpec burn;
                burn.duration = Ms(kDrillBurnMs);
                burn.tick = Ms(kDrillBurnTickMs);
                burn.pct = kDrillBurnPct;
                burn.school = SPELL_SCHOOL_FIRE;
                burn.spellId = SPELL_MV_DRILL_BURN;
                burn.tag = TAG_MV_DRILL_BURN;
                DungeonKit::ImpactThenLinger(me, impact, burn);
            }
            else
                Mechanic::Circle(me, at, kDrillRadiusYd, Ms(kDrillWarnMs)).Damage(kDrillPct(false))
                    .School(SPELL_SCHOOL_FIRE).Spell(SPELL_MV_DRILL).Tag(TAG_MV_DRILL);

            uint32 const lookSpell = heroic ? SPELL_MV_DRILL_CAST_HEROIC : SPELL_MV_DRILL_CAST;
            if (Creature* student = TakeNearest(students, p))
            {
                student->SetFacingTo(DungeonKit::BearingTo(PlaneOf(student), p));
                student->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), lookSpell, false);
                ++cast;
            }
            else    // no student left: the fire still shows when the circle lands
                _followups.Schedule(Ms(kDrillWarnMs), [this, at, lookSpell](TaskContext)
                {
                    me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), lookSpell, true);
                });
        }
        LogMV("vectus", "drill", Acore::StringFormat("heroic={} circles={} students={} pct={:.0f}", heroic ? 1 : 0,
            points.size(), cast, kDrillPct(heroic)));
    }

    // MV2: the marker and the Stack ring on a non-tank (`forced`: a `.dbtest` pick); the students fire at its resolve.
    void GroupExercise(bool heroic, Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            rule.maxRange = kExercisePickRangeYd;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return;
        me->CastSpell(target, SPELL_MV_GROUP_EXERCISE_MARK, true);
        ObjectGuid const targetGuid = target->GetGUID();
        Mechanic::Stack(me, target, kExerciseRadiusYd, Ms(kExerciseWarnMs)).Tag(TAG_MV_GROUP_EXERCISE)
            .OnResolve(OnAI<boss_vectus_rework>(me->GetMap(), me->GetGUID(),
                [targetGuid, heroic](boss_vectus_rework& ai, BossMechanics::ResolveResult const& result)
                {
                    ai.ExerciseVolley(targetGuid, result.hits, heroic);
                }));
        LogMV("vectus", "group-exercise", Acore::StringFormat("target={} heroic={} total_pct={:.0f}", target->GetName(),
            heroic ? 1 : 0, kExerciseTotalPct(heroic)));
    }

    // MV3: a free student stands and casts the volley.
    void PopQuiz()
    {
        std::vector<Creature*> students = FreeStudents();
        if (students.empty())
        {
            LogMV("vectus", "pop-quiz", "skipped (no free student)");
            return;
        }
        Creature* student = students[urand(0, static_cast<uint32>(students.size() - 1))];
        Mechanic::TrackUnit(me, student);
        student->AI()->DoAction(kActionStudentQuiz);
        LogMV("vectus", "pop-quiz", Acore::StringFormat("student={} at=({:.1f}, {:.1f}) graduates={}",
            student->GetSpawnId(), student->GetPositionX(), student->GetPositionY(), LivingGraduates()));
    }

    // MV5
    bool Fireball(Unit* forced)
    {
        Unit* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            rule.maxRange = kFireballRangeYd;
            rule.requireLos = true;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        return me->CastSpell(target, SPELL_MV_FIREBALL, false) == SPELL_CAST_OK;
    }

    Syllabus const& GetSyllabus() const { return _syllabus; }
    uint32 LivingGraduates() const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature* summon = ObjectAccessor::GetCreature(*me, guid); summon && summon->IsAlive()
                && summon->GetEntry() == NPC_SC_GRADUATE)
                ++n;
        return n;
    }

private:
    void OnEngage(bool heroic) override
    {
        Talk(YELL_VECTUS_AGGRO);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_MARDUK_VECTUS;
        Mechanic::BeginEncounter(me, options);
        if (Creature* marduk = Partner(); marduk && marduk->IsAlive())
            Mechanic::TrackUnit(me, marduk);
        Describe(heroic);

        _syllabus.Reset(heroic);
        _doubleAnnounced = false;
        _fireballMs = kFireballFirstMs;
        _blastWaveMs = urand(kBlastWaveFirstMinMs, kBlastWaveFirstMaxMs);
        _timers.Schedule(Ms(kLessonFirstMs), [this, heroic](TaskContext context)
        {
            CallLesson();
            context.Repeat(Ms(kLessonEveryMs(heroic)));
        });
    }

    // Boss data: the quiz student first, then graduates, then either boss (one shared pool); ignore the props; kick
    // the Pop Quiz, never Vectus's Fireball.
    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_SCHOLOMANCE_STUDENT, kQuizStudentPriority, BossMechanics::Who::Dps,
            BossMechanics::Condition::HasAura(SPELL_MV_ON_THE_SPOT));
        d.targets.emplace_back(NPC_SC_GRADUATE, kGraduatePriority);
        d.targets.emplace_back(NPC_MARDUK, 0);
        d.targets.emplace_back(NPC_VECTUS, 0, BossMechanics::Who::Ranged);
        d.ignores.emplace_back(NPC_SCHOLOMANCE_STUDENT, BossMechanics::Condition::LacksAura(SPELL_MV_ON_THE_SPOT));
        uint32 const cycle = kLessonEveryMs(heroic) * static_cast<uint32>(kLessonCount);
        d.interrupts.emplace_back(NPC_SCHOLOMANCE_STUDENT, SPELL_MV_POP_QUIZ, kQuizInterruptPriority, Ms(cycle));
        d.interrupts.emplace_back(NPC_VECTUS, SPELL_MV_FIREBALL, 0);
        Mechanic::Describe(me, std::move(d));
    }

    void OnEndFight() override
    {
        _doubleAnnounced = false;
    }

    // MV2 resolve: the shares (160% / 240% split among the players inside, 75% cap), each a bolt from a student; the
    // students left over fire a bolt with no damage at the target, so the whole class is seen to volley.
    void ExerciseVolley(ObjectGuid targetGuid, std::vector<ObjectGuid> const& hits, bool heroic)
    {
        std::vector<Unit*> inside;
        for (ObjectGuid const& guid : hits)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid); player && player->IsAlive())
                inside.push_back(player);
        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::SplitShares(me, inside,
            kExerciseTotalPct(heroic), kExerciseCapPct);

        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        Vec2 const focus = target ? PlaneOf(target) : PlaneOf(me);
        std::vector<Creature*> pool = FreeStudents();
        std::vector<Creature*> shooters;
        while (shooters.size() < kExerciseStudents)
            if (Creature* s = TakeNearest(pool, focus))
                shooters.push_back(s);
            else
                break;

        for (std::size_t i = 0; i < shares.size(); ++i)
        {
            Unit* victim = ObjectAccessor::GetUnit(*me, shares[i].first);
            if (!victim || !victim->IsAlive())
                continue;
            Unit* caster = shooters.empty() ? static_cast<Unit*>(me) : shooters[ShareStudentFor(i, shooters.size())];
            caster->CastCustomSpell(SPELL_MV_GROUP_EXERCISE, SPELLVALUE_BASE_POINT0,
                static_cast<int32>(shares[i].second), victim, TRIGGERED_FULL_MASK);
        }
        if (target && target->IsAlive())
            for (std::size_t i = shares.size(); i < shooters.size(); ++i)
                shooters[i]->CastSpell(target, SPELL_MV_GROUP_EXERCISE_LOOK, true);
        LogMV("vectus", "group-exercise-volley", Acore::StringFormat("inside={} share={} students={}", inside.size(),
            shares.empty() ? 0 : shares.front().second, shooters.size()));
    }

    // MV3 end: graduate (a Graduate takes the student's place), or the student sits back down.
    void QuizEnded(ObjectGuid studentGuid, QuizEnd how)
    {
        Creature* student = ObjectAccessor::GetCreature(*me, studentGuid);
        LogMV("vectus", "pop-quiz-end", Acore::StringFormat("how={} graduates={}", QuizEndName(how),
            LivingGraduates()));
        if (!student)
            return;
        switch (how)
        {
            case QuizEnd::Graduated:
                if (me->IsAlive() && me->IsInCombat())
                {
                    if (Creature* graduate = me->SummonCreature(NPC_SC_GRADUATE, student->GetPosition(),
                        TEMPSUMMON_CORPSE_TIMED_DESPAWN, 10000))
                    {
                        if (Unit* victim = me->GetVictim())
                            graduate->AI()->AttackStart(victim);
                        student->AI()->DoAction(kActionStudentGraduate);
                        Cheer();
                        break;
                    }
                }
                student->AI()->DoAction(kActionStudentRestore);
                break;
            case QuizEnd::Capped:
            case QuizEnd::Stopped:
                if (student->IsAlive())
                    student->AI()->DoAction(kActionStudentRestore);
                break;
            case QuizEnd::Killed:
                break;
        }
    }

    // "The class cheers": a few students cheer when one graduates.
    void Cheer()
    {
        std::vector<Creature*> students = FreeStudents();
        Acore::Containers::RandomShuffle(students);
        for (std::size_t i = 0; i < students.size() && i < 6; ++i)
            students[i]->HandleEmoteCommand(EMOTE_ONESHOT_CHEER);
    }

    std::vector<Creature*> FreeStudents()
    {
        std::vector<Creature*> out;
        for (Creature* student : Students(me))
            if (npc_sc_student* ai = student->IsAIEnabled ? dynamic_cast<npc_sc_student*>(student->AI()) : nullptr;
                ai && ai->Free())
                out.push_back(student);
        return out;
    }

    // Takes the student nearest `p` out of `pool`.
    static Creature* TakeNearest(std::vector<Creature*>& pool, Vec2 p)
    {
        if (pool.empty())
            return nullptr;
        auto it = std::min_element(pool.begin(), pool.end(), [p](Creature* a, Creature* b)
        {
            return DungeonKit::Distance(PlaneOf(a), p) < DungeonKit::Distance(PlaneOf(b), p);
        });
        Creature* s = *it;
        pool.erase(it);
        return s;
    }

    // Every student back at its desk (a wipe brings the killed ones back too, until the encounter is DONE).
    void ResetClass(bool respawnDead)
    {
        bool const done = instance && instance->GetBossState(BOSS_MARDUK_VECTUS) == DONE;
        for (Creature* student : Students(me))
        {
            if (!student->IsAlive())
            {
                if (respawnDead && !done)
                    student->Respawn(true);
                continue;
            }
            if (student->IsAIEnabled)
                student->AI()->DoAction(kActionStudentRestore);
        }
    }

    void UpdateLecture(uint32 diff)
    {
        if (_lectureMs > diff)
        {
            _lectureMs -= diff;
            return;
        }
        _lectureMs = urand(kLectureMinMs, kLectureMaxMs);
        if (me->IsAlive())
            Talk(SAY_VECTUS_IDLE);
    }

    // MV7: stock Blast Wave at anyone within 10 yd (triggered, so it never cuts a Fireball short).
    void UpdateBlastWave(uint32 diff)
    {
        if (_blastWaveMs > diff)
        {
            _blastWaveMs -= diff;
            return;
        }
        if (!me->SelectNearestPlayer(kBlastWaveRadiusYd))
        {
            _blastWaveMs = 1000;
            return;
        }
        DoCastSelf(SPELL_BLAST_WAVE, true);
        _blastWaveMs = urand(kBlastWaveMinMs, kBlastWaveMaxMs);
        LogMV("vectus", "blast-wave");
    }

    // MV5: back to back, a short gap after each.
    void UpdateFireball(uint32 diff)
    {
        if (_fireballMs > diff)
        {
            _fireballMs -= diff;
            return;
        }
        if (me->IsNonMeleeSpellCast(false) || !Fireball(nullptr))
        {
            _fireballMs = kBusyRetryMs;
            return;
        }
        _fireballMs = 3000 + urand(kFireballGapMinMs, kFireballGapMaxMs);
    }

    Syllabus _syllabus;
    bool _doubleAnnounced = false;
    uint32 _lectureMs = kLectureFirstMaxMs;
    uint32 _fireballMs = kFireballFirstMs;
    uint32 _blastWaveMs = kBlastWaveFirstMaxMs;

};

// ---------------------------------------------------------------------------------------------------------------------
// Spell scripts
// ---------------------------------------------------------------------------------------------------------------------

// The script hits of this encounter: a percent of the reference row, set at launch on each target (RefFlatOn: the
// tank row on the registry's tank), so the target's defensives count; the spells ignore caster modifiers.
//   206158 Pop Quiz (30% / 50%), 206162 Fireball (10%), 206166 the Graduate's Shadow Bolt (10%),
//   206161 Ebon Sweep on the tank (35% / 40% of the tank row).
class spell_sc_mv_ref_flat : public SpellScript
{
    PrepareSpellScript(spell_sc_mv_ref_flat);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;
        bool const heroic = DungeonKit::IsHeroicMap(caster);
        uint32 value = 0;
        switch (GetSpellInfo()->Id)
        {
            case SPELL_MV_POP_QUIZ:
                value = DungeonKit::RefFlatOn(caster, target, kQuizPct(heroic));
                break;
            case SPELL_MV_FIREBALL:
                value = DungeonKit::RefFlatOn(caster, target, kFireballPct);
                break;
            case SPELL_MV_GRADUATE_BOLT:
                value = DungeonKit::RefFlatOn(caster, target, kGraduateBoltPct);
                break;
            case SPELL_MV_EBON_SWEEP_TANK:
                value = DungeonKit::RefFlat(caster, kSweepTankPct(heroic), true);
                break;
            default:
                return;
        }
        SetEffectValue(static_cast<int32>(value));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sc_mv_ref_flat::SetDamage, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// ---------------------------------------------------------------------------------------------------------------------
// `.dbtest scholo marduk ...`
// ---------------------------------------------------------------------------------------------------------------------
struct MardukVectusTest
{
    static boss_vectus_rework* Vectus(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_VECTUS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_vectus_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Vectus is not running boss_vectus_rework (instance not bound?).");
        return ai;
    }

    static boss_marduk_blackpool_rework* Marduk(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_MARDUK);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_marduk_blackpool_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Marduk is not running boss_marduk_blackpool_rework (instance not bound?).");
        return ai;
    }
};

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_MARDUK, BOSS_MARDUK_VECTUS);
    }

    bool HandleInfoVectus(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_VECTUS, BOSS_MARDUK_VECTUS);
    }

    // `.dbtest scholo marduk lesson <drill|exercise|quiz> [heroic]`: Vectus teaches it now (the exercise marks the
    // selected player, or the GM).
    bool HandleLesson(ChatHandler* handler, std::string_view name, Optional<std::string_view> mode)
    {
        boss_vectus_rework* ai = MardukVectusTest::Vectus(handler);
        if (!ai)
            return false;
        std::optional<Lesson> const lesson = LessonByName(name);
        if (!lesson)
        {
            handler->SendErrorMessage("Use drill, exercise or quiz.");
            return false;
        }
        bool const heroic = (mode && *mode == "heroic") || DungeonKit::IsHeroicMap(handler->GetPlayer());
        switch (*lesson)
        {
            case Lesson::Drill:
                ai->Drill(heroic);
                break;
            case Lesson::GroupExercise:
                ai->GroupExercise(heroic, handler->getSelectedPlayerOrSelf());
                break;
            case Lesson::PopQuiz:
                ai->PopQuiz();
                break;
        }
        handler->PSendSysMessage("Vectus teaches the {} ({}).", LessonName(*lesson), heroic ? "heroic" : "normal");
        return true;
    }

    // `.dbtest scholo marduk call`: the next call of the syllabus (a double period below 50% on heroic).
    bool HandleCall(ChatHandler* handler)
    {
        boss_vectus_rework* ai = MardukVectusTest::Vectus(handler);
        if (!ai)
            return false;
        ai->CallLesson();
        std::optional<Lesson> const last = ai->GetSyllabus().Last();
        handler->PSendSysMessage("Vectus calls a lesson (last: {}).", last ? LessonName(*last) : "none");
        return true;
    }

    // `.dbtest scholo marduk syllabus`: the syllabus, the graduates and both bars.
    bool HandleSyllabus(ChatHandler* handler)
    {
        boss_vectus_rework* vectus = MardukVectusTest::Vectus(handler);
        if (!vectus)
            return false;
        Syllabus const& s = vectus->GetSyllabus();
        std::optional<Lesson> const next = s.Peek();
        std::optional<Lesson> const last = s.Last();
        handler->PSendSysMessage("Syllabus: {}; last {}, next {}; graduates alive {} (cap {}).",
            s.Heroic() ? "heroic (shuffled)" : "normal (fixed)", last ? LessonName(*last) : "none",
            next ? LessonName(*next) : "a new bag", vectus->LivingGraduates(), kGraduateCap);
        if (boss_marduk_blackpool_rework* marduk = MardukVectusTest::Marduk(handler))
            handler->PSendSysMessage("Health: Marduk {}/{}, Vectus {}/{}; Marduk busy {} ms{}.",
                marduk->Self()->GetHealth(), marduk->Self()->GetMaxHealth(), vectus->Self()->GetHealth(),
                vectus->Self()->GetMaxHealth(), marduk->BusyForMs(), marduk->Spinning() ? ", spinning" : "");
        return true;
    }

    // `.dbtest scholo marduk sweep`: Ebon Sweep now.
    bool HandleSweep(ChatHandler* handler)
    {
        boss_marduk_blackpool_rework* ai = MardukVectusTest::Marduk(handler);
        if (!ai)
            return false;
        ai->EbonSweep();
        return true;
    }

    // `.dbtest scholo marduk whirlwind`: Whirlwind now (any difficulty).
    bool HandleWhirlwind(ChatHandler* handler)
    {
        boss_marduk_blackpool_rework* ai = MardukVectusTest::Marduk(handler);
        if (!ai)
            return false;
        ai->Whirlwind();
        handler->SendSysMessage("Whirlwind: 2 s cast, then a 4 s spin; 8 yd circle on Marduk.");
        return true;
    }

    // `.dbtest scholo marduk fireball`: Vectus's Fireball at the selected unit (or the GM).
    bool HandleFireball(ChatHandler* handler)
    {
        boss_vectus_rework* ai = MardukVectusTest::Vectus(handler);
        Unit* target = handler->getSelectedUnit();
        if (!target)
            target = handler->GetPlayer();
        if (!ai || !target)
            return false;
        if (!ai->Fireball(target))
            handler->SendErrorMessage("Vectus cannot cast Fireball now.");
        return true;
    }

    ChatCommandTable const& MardukVectusTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "vectus",    HandleInfoVectus, SEC_GAMEMASTER, Console::No },
            { "lesson",    HandleLesson,     SEC_GAMEMASTER, Console::No },
            { "call",      HandleCall,       SEC_GAMEMASTER, Console::No },
            { "syllabus",  HandleSyllabus,   SEC_GAMEMASTER, Console::No },
            { "sweep",     HandleSweep,      SEC_GAMEMASTER, Console::No },
            { "whirlwind", HandleWhirlwind,  SEC_GAMEMASTER, Console::No },
            { "fireball",  HandleFireball,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_marduk_vectus_rework()
{
    RegisterDungeonReworkCreatureAI(boss_marduk_blackpool_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(boss_vectus_rework, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_student, ScholomanceRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sc_graduate, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_sc_mv_ref_flat);
    ScholoTest::RegisterBoss("marduk", MardukVectusTestCommands());
}
