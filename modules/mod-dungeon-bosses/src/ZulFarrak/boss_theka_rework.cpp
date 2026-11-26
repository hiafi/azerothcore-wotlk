/*
 * mod-dungeon-bosses, Zul'Farrak D1: Theka the Martyr (7272). Build spec: docs/dungeons/zul-farrak-rework.md "Theka the
 * Martyr" (rulings 10 to 12, 25, 45), handoff sections 3.5 row D1, 3.6, 3.8, 3.10, section 7 #21, #22, #27 A. Pure
 * rules and every number: ThekaLogic.h (namespace Tune); health ZulFarrakRework.h Health::kTheka. Replaces his SmartAI
 * (Fevered Plague 8600 and Theka Transform 11089 are no longer cast); his patrol 814630 is stopped by
 * rev_theka_zul_farrak.sql (section 7 #21 A).
 *
 *   TK1 Persecutors' Swarm  phase 1, at 12 s then every 20 s (heroic: a pair at 20 s then every 20 s, one north-west
 *                           and one north-east): emote line 1, a 2 s burst at a rise point 30 yd out, then the swarm
 *                           (301005, not selectable, not attackable) crawls a 4 yd line to where he stood at the rise
 *                           at 4 (5) yd/s. Its body bites whoever it passes over: 30% (45%) Nature and Weakened, the
 *                           tank included. If he was walked off its way, it turns at the line's end and crawls a new
 *                           line after him (drawn 1.5 s before it moves on)
 *   TK2 the swarm reaches him  once the body is 2.5 s out (10 / 12.5 yd) with him still on its way: emote line 2, a
 *                           6 yd circle on him; 2.5 s later the swarm lands: 40% (60%) Nature and Weakened to everyone
 *                           inside, the tank included; he is held in place 2.5 s (rooted by script: 1972 holds root
 *                           immunity), still swinging and casting
 *   TK3 Hallowed Suffering  a stack per arrival (normal cap 5, heroic none); nothing in phase 1
 *   TK4 Fevered Plague      at 8 s, then every 12 to 16 s, both phases: a 4 s (heroic 2 s) kickable Nature cast on a
 *                           random player within 30 yd, the tank included: 10% and 15% over 12 s (20% and 40% over
 *                           10 s), a Disease (a dispel is the reward). Heroic: every 2 s anyone within 6 yd of the
 *                           carrier catches a copy (40% over 10 s) that never spreads; a cure stops it
 *   TK5 Martyr's Rising     at 30%: yell line 3, a 2 s rise in place, then display 6697 for the rest of the fight; the
 *                           crawling swarms sink, no more rise
 *   TK6, TK7 Penitent Hunt  phase 2: one Penitent Swarm (301006) per stack, each hunting a random player every 15 s
 *                           (heroic 12 s), staggered: emote line 4 names the player, the swarm follows at 5 yd/s for
 *                           5 s, stops, and a 5 yd circle erupts 1.5 s later: 30% (45%) Nature and Weakened
 *   TK8 Martyr's Lament     heroic, phase 2: every 3 s, 1.5% a stack to everyone (no cap)
 *
 * The courtyard's Scarabs within 45 yd burrow (hidden and untouchable) for the fight and come back after it (section 7
 * #22 A). Boss data: interrupt list the plague; dispel list the plague (a reward). Every firing logs one INFO line
 * "zf-build theka <mechanic> ..."; `.dbtest zf theka ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThekaLogic.h"
#include "ThreatManager.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <list>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfTheka;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;
using DungeonKit::PlaneOf;

namespace
{
    char const* const kBoss = "theka";

    // A probed floor farther than this from the point's measured z is another level.
    float constexpr kFloorBandYd = 3.f;
    // The closing walk and the crawl re-path this often.
    uint32 constexpr kRepathMs = 250;
    // A Persecutor Swarm's creature goes at the latest this long after its summon (the script sinks it first).
    uint32 constexpr kSwarmDespawnMs = kSwarmLifeMs + 10000;
    // A hunt's eruption that never came back from the registry is forgotten this long after its time.
    uint32 constexpr kEruptionGraceMs = 1000;

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    void LogTk(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // `p` at the floor's height near `z` (the measured z when the probe finds nothing close).
    Position FloorAt(WorldObject const* probe, Vec2 p, float z)
    {
        float const ground = probe->GetMapHeight(p.x, p.y, z + kFloorBandYd);
        bool const floor = ground > INVALID_HEIGHT && std::fabs(ground - z) <= kFloorBandYd;
        return Position(p.x, p.y, floor ? ground : z, 0.f);
    }
}

// The Persecutor Swarm 301005 and the Penitent Swarm 301006: movers of Theka's. His AI drives their crawls, chases and
// eruptions; they never fight.
struct npc_zf_theka_swarm : public ScriptedAI
{
    explicit npc_zf_theka_swarm(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

struct npc_zf_persecutor_swarm : public npc_zf_theka_swarm
{
    using npc_zf_theka_swarm::npc_zf_theka_swarm;
};

struct npc_zf_penitent_swarm : public npc_zf_theka_swarm
{
    using npc_zf_theka_swarm::npc_zf_theka_swarm;
};

// Theka the Martyr 7272
struct boss_theka_rework : public BossAI
{
    explicit boss_theka_rework(Creature* creature)
        : BossAI(creature, BOSS_THEKA), _arena(CourtyardArena(), LeashOptions(kBoss)) { }

    enum class Phase : uint8
    {
        One,        // the swarms
        Rising,     // TK5's 2 s
        Two,        // the hunts (and the heroic Lament)
    };

    // TK1 / TK2: one Persecutor Swarm, from its rise to its arrival.
    struct SwarmRun
    {
        ObjectGuid unit;
        MechanicHandle line;
        MechanicHandle circle;
        Vec2 lineEnd;
        uint64 bornMs = 0;
        uint64 moveAtMs = 0;        // the rise or the turn's warning is over: it crawls
        uint64 arriveAtMs = 0;      // closing: it lands then (TK2)
        uint32 repathMs = 0;
        uint32 turns = 0;
        std::size_t point = 0;
        bool moving = false;
        bool closing = false;
    };

    // TK6 / TK7: one Penitent Swarm, its hunts.
    struct PenitentRun
    {
        ObjectGuid unit;
        ObjectGuid target;
        DungeonKit::Chaser chase;
        MechanicHandle circle;
        MechanicHandle eruption;
        uint64 nextHuntMs = 0;
        uint64 eruptAtMs = 0;
        bool hunting = false;
    };

    // TK4: a plague carrier (both difficulties: the look; heroic: the spread).
    struct Carrier
    {
        ObjectGuid player;
        uint32 spell = 0;
        MechanicHandle runOut;
        uint64 nextSpreadMs = 0;
    };

    // A Scarab of the courtyard put under the sand for the fight (section 7 #22 A).
    struct Burrowed
    {
        ObjectGuid guid;
        ReactStates react = REACT_AGGRESSIVE;
        bool addedNotSelectable = false;
        bool addedNonAttackable = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_THEKA;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        _clockMs = 0;
        _phase = Phase::One;
        _timeline.Start(_heroic);
        Mechanic::NoteNextCastIn(me, PlagueSpell(), Ms(Tune::kPlagueFirstMs));
        Talk(YELL_THEKA_AGGRO);
        BurrowScarabs();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogTk("evade", Acore::StringFormat("reason={} clock={}s stacks={} phase={}", uint32(why), _clockMs / 1000,
            _stacks, uint32(_phase)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        LogTk("death", Acore::StringFormat("clock={}s stacks={} swarms={} arrivals={} turns={} hunts={} plagues={} "
            "kicked={} laments={} killer={}", _clockMs / 1000, _stacks, _swarmsRisen, _arrivals, _turns, _hunts,
            _plagues, _plaguesFailed, _laments, killer ? killer->GetName() : std::string("none")));
        Cleanup(true);
    }

    // The swarms are his (they go with his reset and death) and never join the fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // TK4 landed: the carrier's look and, heroic, the spread.
    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (!spell || (spell->Id != SPELL_TK_PLAGUE && spell->Id != SPELL_TK_PLAGUE_HEROIC))
            return;
        Player* player = target ? target->ToPlayer() : nullptr;
        if (!CountsAsPlayer(player) || !player->HasAura(spell->Id, me->GetGUID()))
            return;
        OnPlagueLanded(player, spell->Id);
    }

    // A kick, a silence, a stun or his own stop: the next plague comes on its grid (no hold to end: rule 15).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || (spell->Id != SPELL_TK_PLAGUE && spell->Id != SPELL_TK_PLAGUE_HEROIC) || !me->IsEngaged())
            return;
        ++_plaguesFailed;
        LogTk("plague-broken", Acore::StringFormat("clock={}s", _clockMs / 1000));
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);        // rule 27, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        _clockMs += diff;
        if (_phase == Phase::One && HealthBelowPct(static_cast<int32>(Tune::kRisingPct)))
            StartRising("health");
        UpdateRising();
        UpdateSwarms(diff);
        UpdatePenitents(diff);
        UpdateCarriers();
        UpdateTimeline();
        UpdateLament();
        UpdateRoot();
        if (_phase == Phase::Rising || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The timeline
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateTimeline()
    {
        if (!_timeline.On())
            return;
        if (_phase == Phase::One && _timeline.SwarmDue(_clockMs))
        {
            _timeline.SwarmRose(_clockMs);
            RiseBeat();
        }
        if (_phase != Phase::Rising && _timeline.PlagueDue(_clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (CastPlague(nullptr))
                _timeline.PlagueCast(_clockMs, urand(Tune::kPlagueEveryMinMs, Tune::kPlagueEveryMaxMs));
            else
                _timeline.PlagueRetry(_clockMs);
            Mechanic::NoteNextCastIn(me, PlagueSpell(), Ms(_timeline.PlagueDueMs() - _clockMs));
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TK1 Persecutors' Swarm, TK2 the arrival, TK3 the stacks
    // ----------------------------------------------------------------------------------------------------------------

    // One beat: one swarm (heroic two, one of each sector).
    void RiseBeat()
    {
        std::vector<std::size_t> const picks = RisePicks(_heroic, [](uint32 n) { return urand(0, n - 1); });
        Talk(EMOTE_THEKA_SWARM);
        uint32 risen = 0;
        for (std::size_t point : picks)
            risen += RiseAt(point) ? 1 : 0;
        LogTk("swarm-beat", Acore::StringFormat("points={} risen={} clock={}s", picks.size(), risen, _clockMs / 1000));
    }

    bool RiseAt(std::size_t point)
    {
        Point3 const& p = kThekaRisePoints[point];
        Position const at = FloorAt(me, p.XY(), p.z);
        TempSummon* swarm = me->SummonCreature(NPC_ZF_PERSECUTOR_SWARM, at, TEMPSUMMON_TIMED_DESPAWN,
            kSwarmDespawnMs);
        if (!swarm)
        {
            LogTk("swarm-failed", "no swarm (the template 301005 is missing or the summon failed)");
            return false;
        }
        swarm->SetReactState(REACT_PASSIVE);
        swarm->SetFacingTo(swarm->GetAbsoluteAngle(me));
        swarm->CastSpell(swarm, SPELL_TK_SWARM_AURA, true);
        swarm->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_TK_RISE_BURST, true);

        SwarmRun run;
        run.unit = swarm->GetGUID();
        run.point = point;
        run.bornMs = _clockMs;
        run.moveAtMs = _clockMs + Tune::kRiseMs;
        run.lineEnd = PlaneOf(me);
        run.line = RegisterLine(swarm, at, me->GetPosition(), Tune::kRiseMs, SwarmTag(_heroic));
        ++_swarmsRisen;
        LogTk("swarm", Acore::StringFormat("point={} at=({:.1f}, {:.1f}) to=({:.1f}, {:.1f}) length={:.1f} "
            "speed={:.0f} pct={:.0f}", char('A' + point), at.GetPositionX(), at.GetPositionY(), run.lineEnd.x,
            run.lineEnd.y, DungeonKit::Distance(PlaneOf(swarm), run.lineEnd), Tune::kSwarmSpeed(_heroic),
            Tune::kBitePct(_heroic)));
        _swarms.push_back(run);
        return true;
    }

    // The body's line: from `from` to `to`, drawn `warnMs` before the body moves, its hit following the swarm.
    MechanicHandle RegisterLine(Creature* swarm, Position const& from, Position const& to, uint32 warnMs, uint32 tag)
    {
        float const pct = Tune::kBitePct(_heroic);
        MechanicRef ref = Mechanic::Line(me, from, to, Tune::kSwarmWidth, Ms(warnMs));
        ref.Projectile(Tune::kSwarmSpeed(_heroic)).ProjectileUnit(swarm).Damage(pct).TankDamage(pct)
            .School(SPELL_SCHOOL_NATURE).Spell(SPELL_TK_BITE).Weakened().Within(ThekaFloorBounds()).Tag(tag);
        return ref.Handle();
    }

    void UpdateSwarms(uint32 diff)
    {
        for (std::size_t i = 0; i < _swarms.size();)
        {
            SwarmRun& run = _swarms[i];
            Creature* swarm = ObjectAccessor::GetCreature(*me, run.unit);
            if (!swarm || !swarm->IsAlive())
            {
                Drop(run.line);
                Drop(run.circle);
                _swarms.erase(_swarms.begin() + static_cast<std::ptrdiff_t>(i));
                continue;
            }
            if (run.closing && _clockMs >= run.arriveAtMs)
            {
                SwarmRun arrived = run;
                _swarms.erase(_swarms.begin() + static_cast<std::ptrdiff_t>(i));
                Arrive(arrived, swarm);
                continue;
            }
            if (!run.closing && _clockMs >= run.bornMs + kSwarmLifeMs)
            {
                SwarmRun old = run;
                _swarms.erase(_swarms.begin() + static_cast<std::ptrdiff_t>(i));
                Sink(old, swarm, "life");
                continue;
            }
            StepSwarm(run, swarm, diff);
            ++i;
        }
    }

    void StepSwarm(SwarmRun& run, Creature* swarm, uint32 diff)
    {
        Vec2 const body = PlaneOf(swarm);
        Vec2 const theka = PlaneOf(me);
        if (run.closing)
        {
            run.repathMs += diff;
            if (run.repathMs >= kRepathMs)
            {
                run.repathMs = 0;
                WalkTo(swarm, theka, ClosingSpeedNow(run, body, theka));
            }
            return;
        }
        if (!run.moving)
        {
            if (_clockMs < run.moveAtMs)
                return;
            run.moving = true;
            WalkTo(swarm, run.lineEnd, Tune::kSwarmSpeed(_heroic));
            return;
        }
        if (Closing(body, run.lineEnd, theka, _heroic))
        {
            StartClosing(run, swarm);
            return;
        }
        if (AtLineEnd(body, run.lineEnd) || swarm->movespline->Finalized())
            Turn(run, swarm);
    }

    // The walk's speed so it lands with the circle (never slower than 1 yd/s).
    float ClosingSpeedNow(SwarmRun const& run, Vec2 body, Vec2 theka) const
    {
        uint64 const left = run.arriveAtMs > _clockMs ? run.arriveAtMs - _clockMs : 1;
        float const dist = DungeonKit::Distance(body, theka) - kArriveReachYd;
        return std::max(1.f, dist * 1000.f / static_cast<float>(left));
    }

    // Walks `swarm` along the floor to `to` (stopping short of him by his hit box when `to` is his spot).
    void WalkTo(Creature* swarm, Vec2 to, float speed)
    {
        Vec2 const from = PlaneOf(swarm);
        float const dist = DungeonKit::Distance(from, to);
        Vec2 goal = to;
        if (DungeonKit::Distance(to, PlaneOf(me)) < 0.1f)
        {
            if (dist <= kArriveReachYd)
            {
                swarm->StopMoving();
                return;
            }
            float const t = (dist - kArriveReachYd) / dist;
            goal = Vec2{ from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t };
        }
        std::vector<DungeonKit::FloorPathPoint> const path = DungeonKit::FloorPathOnMap(me, from, goal,
            swarm->GetPositionZ());
        if (!DungeonKit::MoveAlongFloor(swarm, path, speed))
            swarm->StopMoving();
    }

    // TK2: the circle on him, the emote, then straight at him.
    void StartClosing(SwarmRun& run, Creature* swarm)
    {
        float const pct = Tune::kDevourPct(_heroic);
        MechanicRef ref = Mechanic::Circle(me, me, Tune::kDevourRadius, Ms(Tune::kArrivalWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_TK_DEVOUR).Weakened()
            .Within(ThekaFloorBounds()).Tag(DevourTag(_heroic));
        run.circle = ref.Handle();
        run.closing = true;
        run.arriveAtMs = _clockMs + Tune::kArrivalWarnMs;
        run.repathMs = kRepathMs;       // walk at once
        if (_clockMs >= _lastDevourEmoteMs + kDevourEmoteGapMs || !_devourEmoted)
        {
            Talk(EMOTE_THEKA_DEVOUR);
            _lastDevourEmoteMs = _clockMs;
            _devourEmoted = true;
        }
        LogTk("closing", Acore::StringFormat("point={} dist={:.1f} turns={} pct={:.0f} circle={}",
            char('A' + run.point), swarm->GetExactDist2d(me), run.turns, pct, run.circle ? 1 : 0));
    }

    // TK1: at its line's end, he is not there: a new line after him.
    void Turn(SwarmRun& run, Creature* swarm)
    {
        Drop(run.line);
        swarm->StopMoving();
        Position const from = swarm->GetPosition();
        run.lineEnd = PlaneOf(me);
        run.moving = false;
        run.moveAtMs = _clockMs + kReaimMs;
        ++run.turns;
        ++_turns;
        swarm->SetFacingTo(swarm->GetAbsoluteAngle(me));
        run.line = RegisterLine(swarm, from, me->GetPosition(), kReaimMs, TAG_TK_REAIM);
        LogTk("turn", Acore::StringFormat("point={} turn={} length={:.1f} warn={}ms", char('A' + run.point), run.turns,
            DungeonKit::Distance(PlaneOf(swarm), run.lineEnd), kReaimMs));
    }

    // TK2 lands (the registry's circle deals the hit), TK3 a stack, the hold.
    void Arrive(SwarmRun& run, Creature* swarm)
    {
        Drop(run.line);
        swarm->DespawnOrUnsummon();
        AddHallowed();
        ++_arrivals;
        me->CastSpell(me, SPELL_TK_SWARM_ON_THEKA, true);
        _holdUntilMs = std::max(_holdUntilMs, _clockMs + Tune::kHoldMs);
        LogTk("arrival", Acore::StringFormat("point={} stacks={} turns={} hold-until={}s clock={}s",
            char('A' + run.point), _stacks, run.turns, _holdUntilMs / 1000, _clockMs / 1000));
    }

    // TK3: the buff's stack count follows his count.
    void AddHallowed()
    {
        _stacks = AddStack(_stacks, _heroic);
        Aura* aura = me->GetAura(SPELL_TK_HALLOWED);
        if (!aura)
            aura = me->AddAura(SPELL_TK_HALLOWED, me);
        if (aura)
            aura->SetStackAmount(static_cast<uint8>(_stacks));
    }

    // A crawling swarm sinks back into the sand (the rising, its life, a cleanup).
    void Sink(SwarmRun& run, Creature* swarm, char const* why)
    {
        Drop(run.line);
        if (run.circle && (!run.closing || _clockMs < run.arriveAtMs))
            Drop(run.circle);
        if (swarm)
        {
            swarm->CastSpell(swarm->GetPositionX(), swarm->GetPositionY(), swarm->GetPositionZ(), SPELL_TK_RISE_BURST,
                true);
            swarm->DespawnOrUnsummon(Ms(500));
        }
        LogTk("swarm-sinks", Acore::StringFormat("point={} why={} turns={}", char('A' + run.point), why, run.turns));
    }

    void SinkAll(char const* why)
    {
        std::vector<SwarmRun> runs = std::move(_swarms);
        _swarms.clear();
        for (SwarmRun& run : runs)
            Sink(run, ObjectAccessor::GetCreature(*me, run.unit), why);
    }

    // The hold under the swarm (TK2) and the rising (TK5) by root: his immunity set 1972 holds root immunity, so no
    // root aura (rule 8). He keeps his target, his swing and his casts.
    void UpdateRoot()
    {
        bool const rooted = _phase == Phase::Rising || _clockMs < _holdUntilMs;
        if (rooted == _rooted)
            return;
        _rooted = rooted;
        me->SetControlled(rooted, UNIT_STATE_ROOT);
        if (rooted)
            me->StopMoving();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TK4 Fevered Plague
    // ----------------------------------------------------------------------------------------------------------------

    uint32 PlagueSpell() const { return _heroic ? SPELL_TK_PLAGUE_HEROIC : SPELL_TK_PLAGUE; }

    // `forced` (a test): that player. False when nobody is in range or the cast was refused (a locked school).
    bool CastPlague(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            std::vector<Player*> inRange;
            for (Player* player : FightPlayers())
                if (me->GetExactDist(player) <= Tune::kPlagueRangeYd)
                    inRange.push_back(player);
            if (inRange.empty())
            {
                LogTk("plague-skip", "nobody within 30 yd");
                return false;
            }
            target = inRange[urand(0, uint32(inRange.size()) - 1)];
        }
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(target, PlagueSpell(), TRIGGERED_NONE);
        if (result != SPELL_CAST_OK)
        {
            LogTk("plague-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        ++_plagues;
        LogTk("plague", Acore::StringFormat("target={} tank={} cast={}ms hit={:.0f} dot={:.0f} clock={}s",
            target->GetName(), target == me->GetVictim() ? 1 : 0, Tune::kPlagueCastMs(_heroic),
            Tune::kPlagueHitPct(_heroic), Tune::kPlagueDotPct(_heroic), _clockMs / 1000));
        return true;
    }

    void OnPlagueLanded(Player* player, uint32 spellId)
    {
        me->CastSpell(player, SPELL_TK_PLAGUE_LOOK, true);
        Carrier carrier;
        carrier.player = player->GetGUID();
        carrier.spell = spellId;
        if (spellId == SPELL_TK_PLAGUE_HEROIC)
        {
            // Telegraph only (the script spreads): everyone keeps 6 yd off the carrier while the plague lasts.
            MechanicRef ref = Mechanic::RunOut(me, player, Tune::kSpreadYd, Ms(Tune::kPlagueMs(true)));
            ref.Within(ThekaFloorBounds()).Tag(TAG_TK_SPREAD);
            carrier.runOut = ref.Handle();
            carrier.nextSpreadMs = _clockMs + Tune::kSpreadEveryMs;
        }
        // a second plague on the same carrier replaces the first's record
        for (Carrier& old : _carriers)
            if (old.player == carrier.player)
                Drop(old.runOut);
        std::erase_if(_carriers, [&carrier](Carrier const& c) { return c.player == carrier.player; });
        _carriers.push_back(carrier);
        LogTk("plague-landed", Acore::StringFormat("target={} spread={}", player->GetName(), carrier.runOut ? 1 : 0));
    }

    // The look follows the plague; heroic: the spread every 2 s while it lasts. A cure ends both.
    void UpdateCarriers()
    {
        for (std::size_t i = 0; i < _carriers.size();)
        {
            Carrier& carrier = _carriers[i];
            Player* player = ObjectAccessor::GetPlayer(*me, carrier.player);
            bool const sick = CountsAsPlayer(player) && player->IsInMap(me)
                && player->HasAura(carrier.spell, me->GetGUID());
            if (!sick)
            {
                Drop(carrier.runOut);
                if (player)
                    player->RemoveAurasDueToSpell(SPELL_TK_PLAGUE_LOOK, me->GetGUID());
                _carriers.erase(_carriers.begin() + static_cast<std::ptrdiff_t>(i));
                continue;
            }
            if (carrier.spell == SPELL_TK_PLAGUE_HEROIC && _clockMs >= carrier.nextSpreadMs)
            {
                carrier.nextSpreadMs += Tune::kSpreadEveryMs;
                Spread(player);
            }
            ++i;
        }
    }

    // Heroic: a copy on everyone within 6 yd of the carrier (copies never spread; a new copy refreshes an old one).
    void Spread(Player* carrier)
    {
        uint32 caught = 0;
        for (MapReference const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player == carrier || !CountsAsPlayer(player) || carrier->GetExactDist2d(player) > Tune::kSpreadYd)
                continue;
            me->CastSpell(player, SPELL_TK_PLAGUE_SPREAD, true);
            ++caught;
        }
        if (caught)
            LogTk("plague-spread", Acore::StringFormat("carrier={} caught={}", carrier->GetName(), caught));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TK5 Martyr's Rising
    // ----------------------------------------------------------------------------------------------------------------

    void StartRising(char const* why)
    {
        if (_phase != Phase::One)
            return;
        _phase = Phase::Rising;
        _risingEndMs = _clockMs + Tune::kRisingMs;
        _timeline.Rising(_risingEndMs);
        SinkAll("rising");
        me->InterruptNonMeleeSpells(false);
        Talk(YELL_THEKA_RISING);
        me->CastSpell(me, SPELL_TK_RISING, true);
        LogTk("rising", Acore::StringFormat("why={} stacks={} health={:.1f}% clock={}s", why, _stacks,
            me->GetHealthPct(), _clockMs / 1000));
    }

    void UpdateRising()
    {
        if (_phase != Phase::Rising || _clockMs < _risingEndMs)
            return;
        _phase = Phase::Two;
        me->SetDisplayId(kRisenDisplay, kRisenObjectScale);     // one call (rule 4)
        _risen = true;
        for (uint32 i = 0; i < _stacks; ++i)
            AddPenitent(i, _stacks);
        if (_heroic)
            _nextLamentMs = _clockMs + kLamentFirstMs;
        LogTk("risen", Acore::StringFormat("penitents={} lament={} clock={}s", _penitents.size(), _heroic ? 1 : 0,
            _clockMs / 1000));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TK6, TK7 Penitent Hunt
    // ----------------------------------------------------------------------------------------------------------------

    void AddPenitent(uint32 index, uint32 count)
    {
        float const angle = me->GetOrientation() + float(M_PI) * 2.f * float(index) / float(std::max<uint32>(1, count));
        Vec2 const at = DungeonKit::Advance(PlaneOf(me), angle, 2.f);
        Position const pos = FloorAt(me, at, me->GetPositionZ());
        TempSummon* swarm = me->SummonCreature(NPC_ZF_PENITENT_SWARM, pos, TEMPSUMMON_MANUAL_DESPAWN);
        if (!swarm)
        {
            LogTk("penitent-failed", "no swarm (the template 301006 is missing or the summon failed)");
            return;
        }
        swarm->SetReactState(REACT_PASSIVE);
        swarm->CastSpell(swarm, SPELL_TK_SWARM_AURA, true);
        swarm->CastSpell(pos.GetPositionX(), pos.GetPositionY(), pos.GetPositionZ(), SPELL_TK_RISE_BURST, true);
        PenitentRun run;
        run.unit = swarm->GetGUID();
        run.nextHuntMs = HuntFirstDueMs(_clockMs, index, count, _heroic);
        _penitents.push_back(std::move(run));
    }

    void UpdatePenitents(uint32 diff)
    {
        if (_phase != Phase::Two)
            return;
        for (PenitentRun& run : _penitents)
        {
            Creature* swarm = ObjectAccessor::GetCreature(*me, run.unit);
            if (!swarm || !swarm->IsAlive())
            {
                Drop(run.circle);
                Drop(run.eruption);
                run.hunting = false;
                continue;
            }
            if (run.hunting)
            {
                if (!run.eruption)
                {
                    run.chase.Update(swarm, diff);
                    if (!run.chase.Active())
                        MarkEruption(run, swarm);
                }
                else if (_clockMs >= run.eruptAtMs + kEruptionGraceMs)
                {
                    Drop(run.eruption);     // the registry never came back
                    run.hunting = false;
                }
                continue;
            }
            if (_clockMs >= run.nextHuntMs)
            {
                run.nextHuntMs += Tune::kHuntEveryMs(_heroic);
                if (run.nextHuntMs <= _clockMs)
                    run.nextHuntMs = _clockMs + Tune::kHuntEveryMs(_heroic);
                StartHunt(run, swarm, nullptr);
            }
        }
    }

    // `forced` (a test): that player.
    bool StartHunt(PenitentRun& run, Creature* swarm, Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            std::vector<ObjectGuid> const picks = PickPreferring(GuidsOf(FightPlayers()), Hunted(), 1,
                [](uint32 n) { return urand(0, n - 1); });
            target = picks.empty() ? nullptr : ObjectAccessor::GetPlayer(*me, picks.front());
        }
        if (!CountsAsPlayer(target) || !target->IsInMap(me))
        {
            LogTk("hunt-skip", "nobody to hunt");
            return false;
        }
        DungeonKit::ChaserSpec spec;
        spec.speed = Tune::kChaseSpeed;
        spec.life = Ms(Tune::kChaseMs);
        spec.endOnArrive = false;
        spec.fixate = false;        // no threat of its own: a target that goes ends the chase where it is
        if (!run.chase.Start(swarm, target, spec))
            return false;
        swarm->CastSpell(swarm, SPELL_TK_HUNT_TRAIL, true);
        {
            BossMechanics::Eligibility hunted;
            hunted.carriers = { target->GetGUID() };
            hunted.playersOnly = true;
            MechanicRef ref = Mechanic::Circle(me, swarm, Tune::kChaseRadius, Ms(kChaseArmMs));
            ref.Persistent(Ms(Tune::kChaseMs - kChaseArmMs), Milliseconds(0)).Eligible(hunted).NoTelegraph()
                .Within(ThekaFloorBounds()).Tag(TAG_TK_CHASE);
            run.circle = ref.Handle();
        }   // the ref commits here
        run.target = target->GetGUID();
        run.hunting = true;
        ++_hunts;
        Talk(EMOTE_THEKA_HUNT, target);
        LogTk("hunt", Acore::StringFormat("target={} tank={} live={} clock={}s", target->GetName(),
            target == me->GetVictim() ? 1 : 0, Hunted().size(), _clockMs / 1000));
        return true;
    }

    void MarkEruption(PenitentRun& run, Creature* swarm)
    {
        Drop(run.circle);
        swarm->StopMoving();
        swarm->RemoveAurasDueToSpell(SPELL_TK_HUNT_TRAIL);
        float const pct = Tune::kEruptionPct(_heroic);
        ObjectGuid const guid = run.unit;
        Position const at = swarm->GetPosition();
        MechanicRef ref = Mechanic::Circle(me, at, Tune::kEruptionRadius, Ms(Tune::kEruptionWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_TK_ERUPTION).Weakened()
            .Within(ThekaFloorBounds()).Tag(TAG_TK_ERUPTION)
            .OnResolve(OnTheka([guid](boss_theka_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.Erupt(guid, r);
            }));
        run.eruption = ref.Handle();
        run.eruptAtMs = _clockMs + Tune::kEruptionWarnMs;
        if (!run.eruption)
            run.hunting = false;        // refused: the swarm waits for its next hunt
        LogTk("eruption-mark", Acore::StringFormat("at=({:.1f}, {:.1f}) pct={:.0f}", at.GetPositionX(),
            at.GetPositionY(), pct));
    }

    void Erupt(ObjectGuid swarmGuid, BossMechanics::ResolveResult const& result)
    {
        for (PenitentRun& run : _penitents)
        {
            if (run.unit != swarmGuid)
                continue;
            run.eruption = MechanicHandle();
            run.hunting = false;
            run.target.Clear();
            if (Creature* swarm = ObjectAccessor::GetCreature(*me, swarmGuid))
                swarm->CastSpell(swarm->GetPositionX(), swarm->GetPositionY(), swarm->GetPositionZ(),
                    SPELL_TK_ERUPTION_LOOK, true);
        }
        LogTk("eruption", Acore::StringFormat("hits={}", result.hits.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TK8 Martyr's Lament (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateLament()
    {
        if (!_heroic || _phase != Phase::Two || !_stacks || _clockMs < _nextLamentMs)
            return;
        _nextLamentMs += Tune::kLamentEveryMs;
        if (_nextLamentMs <= _clockMs)
            _nextLamentMs = _clockMs + Tune::kLamentEveryMs;
        Lament();
    }

    void Lament()
    {
        float const pct = LamentPct(_stacks);
        uint32 hit = 0;
        for (Player* player : FightPlayers())
        {
            CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
            args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlatOn(me, player, pct)));
            me->CastSpell(player, SPELL_TK_LAMENT, args);
            ++hit;
        }
        ++_laments;
        LogTk("lament", Acore::StringFormat("stacks={} pct={:.1f} hit={}", _stacks, pct, hit));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The courtyard's Scarabs (section 7 #22 A)
    // ----------------------------------------------------------------------------------------------------------------

    void BurrowScarabs()
    {
        std::list<Creature*> scarabs;
        me->GetCreatureListWithEntryInGrid(scarabs, NPC_SCARAB, kBurrowRadiusYd);
        uint32 skipped = 0;
        for (Creature* scarab : scarabs)
        {
            if (!scarab->IsAlive() || scarab->IsInCombat() || !scarab->IsVisible())
            {
                ++skipped;
                continue;
            }
            Burrowed b;
            b.guid = scarab->GetGUID();
            b.react = scarab->GetReactState();
            b.addedNotSelectable = !scarab->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            b.addedNonAttackable = !scarab->HasUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
            scarab->StopMoving();
            scarab->GetMotionMaster()->Clear();
            scarab->GetMotionMaster()->MoveIdle();
            scarab->SetReactState(REACT_PASSIVE);
            scarab->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE | UNIT_FLAG_NON_ATTACKABLE);
            scarab->SetVisible(false);
            _burrowed.push_back(b);
        }
        LogTk("scarabs-burrow", Acore::StringFormat("burrowed={} skipped={}", _burrowed.size(), skipped));
    }

    void RestoreScarabs()
    {
        uint32 back = 0;
        for (Burrowed const& b : _burrowed)
        {
            Creature* scarab = ObjectAccessor::GetCreature(*me, b.guid);
            if (!scarab)
                continue;
            if (b.addedNotSelectable)
                scarab->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
            if (b.addedNonAttackable)
                scarab->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
            scarab->SetReactState(b.react);
            scarab->SetVisible(true);
            if (scarab->IsAlive())
                scarab->GetMotionMaster()->Initialize();
            ++back;
        }
        if (!_burrowed.empty())
            LogTk("scarabs-back", Acore::StringFormat("back={} of={}", back, _burrowed.size()));
        _burrowed.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest zf theka` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Swarm,
        Plague,
        Rise,
        Hunt,
        Stack,
        Lament,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!me->IsEngaged())
            return "Theka must be in combat (the picks read his threat list, the mechanics his encounter).";
        Player* player = CountsAsPlayer(who) ? who : nullptr;
        switch (mechanic)
        {
            case TestMechanic::Swarm:
                if (_phase != Phase::One)
                    return "The swarms rise in phase 1 only.";
                RiseBeat();
                break;
            case TestMechanic::Plague:
                if (_phase == Phase::Rising || me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting or rising.";
                if (!CastPlague(player))
                    return "The plague was not cast (see the log).";
                break;
            case TestMechanic::Rise:
                if (_phase != Phase::One)
                    return "He has risen already.";
                StartRising("test");
                break;
            case TestMechanic::Hunt:
            {
                if (_phase != Phase::Two)
                    return "The hunts run in phase 2 only.";
                for (PenitentRun& run : _penitents)
                    if (!run.hunting)
                        if (Creature* swarm = ObjectAccessor::GetCreature(*me, run.unit))
                            return StartHunt(run, swarm, player) ? std::string() : "The hunt did not start.";
                return "No idle Penitent Swarm (none, or every one is hunting).";
            }
            case TestMechanic::Stack:
                if (_phase != Phase::One)
                    return "Stacks count in phase 1 only.";
                AddHallowed();
                break;
            case TestMechanic::Lament:
                if (!_stacks)
                    return "No stack: the Lament would deal nothing.";
                Lament();
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} phase={} stacks={} swarms-live={} risen={} arrivals={} "
            "turns={} penitents={} hunts={} plagues={} broken={} carriers={} laments={} held={} burrowed={}",
            _clockMs / 1000, _heroic ? 1 : 0, uint32(_phase), _stacks, _swarms.size(), _swarmsRisen, _arrivals, _turns,
            _penitents.size(), _hunts, _plagues, _plaguesFailed, _carriers.size(), _laments,
            _clockMs < _holdUntilMs ? 1 : 0, _burrowed.size());
    }

private:
    // The bots' boss data: the plague is the fight's kick, its cure a reward (heroic: the cure also stops the spread).
    void Describe()
    {
        BossMechanics::Descriptor d;
        // caster 0: any unit of his encounter (the heroic copy's entry is WP-H's, not 7272)
        d.interrupts.emplace_back(0, PlagueSpell(), 1,
            Ms((Tune::kPlagueEveryMinMs + Tune::kPlagueEveryMaxMs) / 2));
        if (_heroic)
        {
            d.dispels.emplace_back(SPELL_TK_PLAGUE_HEROIC, 2);
            d.dispels.emplace_back(SPELL_TK_PLAGUE_SPREAD, 1);
        }
        else
            d.dispels.emplace_back(SPELL_TK_PLAGUE, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // The players on his threat list the fight acts on: on the courtyard (a corpse runner is never picked).
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && player->IsInMap(me) && _arena.Contains(player))
                out.push_back(player);
        }
        return out;
    }

    static std::vector<ObjectGuid> GuidsOf(std::vector<Player*> const& players)
    {
        std::vector<ObjectGuid> out;
        for (Player const* player : players)
            out.push_back(player->GetGUID());
        return out;
    }

    // Everyone a Penitent Swarm is after, until it erupted.
    std::vector<ObjectGuid> Hunted() const
    {
        std::vector<ObjectGuid> out;
        for (PenitentRun const& run : _penitents)
            if (run.hunting && !run.target.IsEmpty())
                out.push_back(run.target);
        return out;
    }

    // Cancels a live mechanic and forgets it.
    void Drop(MechanicHandle& handle)
    {
        if (handle)
            Mechanic::Cancel(me, handle);
        handle = MechanicHandle();
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if this pull still runs. Captures the map and
    // the guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnTheka(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn, pull = _pull](BossMechanics::ResolveResult const& result)
        {
            Creature* boss = map ? map->GetCreature(guid) : nullptr;
            if (!boss || !boss->IsAlive() || !boss->IsEngaged() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_theka_rework*>(boss->AI()))
                if (ai->_pull == pull)
                    fn(*ai, result);
        };
    }

    // Nothing left of the pull (reset, evade, death): no shape, no swarm, no hold, no plague, no burrowed Scarab
    // (RB-1). `died`: the corpse keeps the risen look.
    void Cleanup(bool died)
    {
        ++_pull;        // callbacks of the old pull drop
        _timeline.Stop();
        for (SwarmRun& run : _swarms)
        {
            Drop(run.line);
            Drop(run.circle);
        }
        _swarms.clear();
        for (PenitentRun& run : _penitents)
        {
            Drop(run.circle);
            Drop(run.eruption);
            if (Creature* swarm = ObjectAccessor::GetCreature(*me, run.unit))
                run.chase.Stop(swarm);
        }
        _penitents.clear();
        for (Carrier& carrier : _carriers)
            Drop(carrier.runOut);
        _carriers.clear();
        summons.DespawnAll();
        // the plague and its copies from everyone (an evade or a death must not leave his DoTs ticking)
        if (Map* map = me->GetMap())
            for (MapReference const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    for (uint32 spell : { uint32(SPELL_TK_PLAGUE), uint32(SPELL_TK_PLAGUE_HEROIC),
                        uint32(SPELL_TK_PLAGUE_SPREAD), uint32(SPELL_TK_PLAGUE_LOOK) })
                        player->RemoveAurasDueToSpell(spell, me->GetGUID());
        RestoreScarabs();
        if (_rooted)
            me->SetControlled(false, UNIT_STATE_ROOT);
        _rooted = false;
        me->RemoveAurasDueToSpell(SPELL_TK_HALLOWED);
        me->RemoveAurasDueToSpell(SPELL_TK_SWARM_ON_THEKA);
        if (_risen && !died && me->IsAlive())
            me->SetDisplayId(me->GetNativeDisplayId());     // the native scale too (no display scale)
        _risen = false;
        _arena.Reset();
        _phase = Phase::One;
        _clockMs = 0;
        _risingEndMs = 0;
        _holdUntilMs = 0;
        _nextLamentMs = 0;
        _lastDevourEmoteMs = 0;
        _devourEmoted = false;
        _stacks = 0;
        _swarmsRisen = 0;
        _arrivals = 0;
        _turns = 0;
        _hunts = 0;
        _plagues = 0;
        _plaguesFailed = 0;
        _laments = 0;
    }

    // TK6: the chase circle arms this long after the hunt starts and stands for the rest of the chase.
    static uint32 constexpr kChaseArmMs = 500;
    static_assert(kChaseArmMs < Tune::kChaseMs);

    DungeonKit::ArenaGuard _arena;
    Timeline _timeline;
    std::vector<SwarmRun> _swarms;
    std::vector<PenitentRun> _penitents;
    std::vector<Carrier> _carriers;
    std::vector<Burrowed> _burrowed;
    Phase _phase = Phase::One;
    uint64 _clockMs = 0;            // ms since the pull
    uint64 _risingEndMs = 0;
    uint64 _holdUntilMs = 0;
    uint64 _nextLamentMs = 0;
    uint64 _lastDevourEmoteMs = 0;
    uint32 _pull = 0;
    uint32 _stacks = 0;
    uint32 _swarmsRisen = 0;
    uint32 _arrivals = 0;
    uint32 _turns = 0;
    uint32 _hunts = 0;
    uint32 _plagues = 0;
    uint32 _plaguesFailed = 0;
    uint32 _laments = 0;
    bool _heroic = false;
    bool _rooted = false;
    bool _risen = false;
    bool _devourEmoted = false;
};

namespace
{
    boss_theka_rework* FindThekaAI(ChatHandler* handler)
    {
        Creature* boss = ZfTest::FindBoss(handler, NPC_THEKA);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_theka_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Theka is not running boss_theka_rework (check the ScriptName).");
        return ai;
    }

    using Mech = boss_theka_rework::TestMechanic;

    bool Fire(ChatHandler* handler, Mech mechanic, char const* what)
    {
        boss_theka_rework* ai = FindThekaAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Theka: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_THEKA, BOSS_THEKA);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_theka_rework* ai = FindThekaAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Theka: {}", ai->TestState());
        return true;
    }

    bool HandleSwarm(ChatHandler* handler)
    {
        return Fire(handler, Mech::Swarm, "a swarm beat (TK1, TK2; heroic a pair)");
    }

    bool HandlePlague(ChatHandler* handler)
    {
        return Fire(handler, Mech::Plague, "Fevered Plague on the selected player (TK4; a GM: a random one)");
    }

    bool HandleRise(ChatHandler* handler)
    {
        return Fire(handler, Mech::Rise, "Martyr's Rising now (TK5)");
    }

    bool HandleHunt(ChatHandler* handler)
    {
        return Fire(handler, Mech::Hunt, "a Penitent Hunt after the selected player (TK6, TK7)");
    }

    bool HandleStack(ChatHandler* handler)
    {
        return Fire(handler, Mech::Stack, "one Hallowed Suffering stack (TK3)");
    }

    bool HandleLament(ChatHandler* handler)
    {
        return Fire(handler, Mech::Lament, "one Martyr's Lament pulse (TK8)");
    }

    ChatCommandTable const& ThekaTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "swarm",  HandleSwarm,  SEC_GAMEMASTER, Console::No },
            { "plague", HandlePlague, SEC_GAMEMASTER, Console::No },
            { "rise",   HandleRise,   SEC_GAMEMASTER, Console::No },
            { "hunt",   HandleHunt,   SEC_GAMEMASTER, Console::No },
            { "stack",  HandleStack,  SEC_GAMEMASTER, Console::No },
            { "lament", HandleLament, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_theka_rework()
{
    RegisterDungeonReworkCreatureAI(boss_theka_rework, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_persecutor_swarm, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_penitent_swarm, ZulFarrakRework::kInstanceScriptName);
    ZfTest::RegisterBoss("theka", ThekaTestCommands());
}
