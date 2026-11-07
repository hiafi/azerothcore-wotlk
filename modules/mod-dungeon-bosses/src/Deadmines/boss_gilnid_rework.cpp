/*
 * mod-dungeon-bosses, Deadmines: Gilnid, the iron shot and the land mine (WP-B4). Build spec: DM 'Gilnid' Build spec
 * GI1-GI7; handoff section 3.4 rows GI, section 3.8 (the foundry), section 7 #6 (Hot shot as lane segments).
 *
 * Replaces SmartAI 1763 (Molten Metal on the victim, the out of combat say every 120 s, the Foundry Door on death:
 * the door now opens through instance_deadmines_rework's door data on BOSS_GILNID DONE).
 *
 *   GI1 Molten Metal   stock 5213 on the victim, 1-6 s then 15-25 s; an interrupt entry in the descriptor
 *   GI2 Roll Out       yell, a random pot pours, one shot per target rolls from the pot through the target to the
 *                      measured wall and 30 yd on (playtest 1; Line + Projectile + ProjectileUnit(ball), 30% Physical
 *                      + Weakened). The shot looks like stock Flame Blast (an invisible carrier, a Flame Blast burst at
 *                      its feet every 0.4 s) and rolls along the floor (a ground-sampled spline path)
 *   GI3 Bowled Over    a rolling ball passing through Gilnid: 2 s stun (mechanic 0) + 5% of his health, once per ball
 *   GI4 Hot shot (H)   4 yd persistent segments of each lane, registered as the ball passes each (DeadminesKit::Linger)
 *   GI5 Double shift   heroic below 50%: the shot every 10 s
 *   GI6/7 Landmine (H) Mine(pos, 4, 3 s, 0.5 s).Cap(group, 6), 35% Fire + Weakened; a ball over an armed mine sets
 *                      it off (Mechanic::Detonate)
 *
 * Every firing logs one "dm-pilot gilnid <mechanic>" line (module.dungeonbosses, INFO). `.dmtest gilnid ...` fires one
 * mechanic on demand.
 */

#include "Chat.h"
#include "Creature.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "GameTime.h"
#include "GilnidLogic.h"
#include "Log.h"
#include "Map.h"
#include "MoveSpline.h"
#include "MoveSplineInit.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TemporarySummon.h"
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;

namespace
{
    char constexpr kLogCategory[] = "module.dungeonbosses";

    enum GilnidEvents : uint32
    {
        EVENT_MOLTEN_METAL = 1,
        EVENT_ROLL_OUT,
        EVENT_LANDMINE,
    };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    DeadminesKit::Vec2 ToVec(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }
}

// iron shot 300423 (summoned by Gilnid at a pot; an invisible carrier since playtest 1). Sits at the pot while its lane
// marker shows (pour visual), then rolls to the lane's end at 10 yd per s along the floor path Gilnid gives it (a
// spline through ground-sampled points, no pathing: the pot block is a navmesh hole), casting a Flame Blast burst at
// its feet every 0.4 s on the way (the projectile's look), and goes shortly after. Gilnid's script reads its position
// every update (Bowled Over, the mine sweep, Hot shot segments); the registry tracks it as the lane's projectile.
struct npc_dm_iron_shot : public ScriptedAI
{
    explicit npc_dm_iron_shot(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void Reset() override { }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    // Shows the pour now and rolls along `path` (its first point is the pot) after `warn` (the lane marker's warning).
    void Launch(std::vector<Gilnid::PathPoint> const& path, Milliseconds warn)
    {
        _path.clear();
        for (Gilnid::PathPoint const& p : path)
            _path.emplace_back(p.x, p.y, p.z);
        DoCastSelf(Gilnid::SPELL_RED_HOT, true);
        DoCastSelf(Gilnid::SPELL_SHOT_POUR, true);
        scheduler.Schedule(warn, [this](TaskContext /*ctx*/)
        {
            DoCastSelf(Gilnid::SPELL_SHOT_LAUNCH, true);
            FlameBlast();
            if (_path.size() < 2)
            {
                _atWall = true;
                me->DespawnOrUnsummon(Ms(Gilnid::kShotLingerMs));
                return;
            }
            Movement::MoveSplineInit init(me);
            init.MovebyPath(_path);
            init.SetVelocity(Gilnid::kShotSpeed);
            init.Launch();
            _rolling = true;
            _pulseMs = Gilnid::kFlameBlastPulseMs;
        });
    }

    bool IsRolling() const { return _rolling; }
    bool AtWall() const { return _atWall; }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);
        if (!_rolling)
            return;
        if (me->movespline->Finalized())
        {
            _rolling = false;
            _atWall = true;
            FlameBlast();
            me->DespawnOrUnsummon(Ms(Gilnid::kShotLingerMs));
            return;
        }
        if (_pulseMs > diff)
        {
            _pulseMs -= diff;
            return;
        }
        _pulseMs = Gilnid::kFlameBlastPulseMs;
        FlameBlast();
    }

private:
    // The projectile's look: stock Flame Blast's visual at its feet (a point cast, so the burst sits on the floor).
    void FlameBlast()
    {
        me->CastSpell(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), Gilnid::SPELL_SHOT_FLAME_BLAST, true);
    }

    Movement::PointsArray _path;
    uint32 _pulseMs = 0;
    bool _rolling = false;
    bool _atWall = false;
};

// Goblin land mine 300424 (summoned, heroic): the model and its arming look. The registry's Mine owns the hitbox,
// the arming, the grace and the blast; Gilnid's script plays the blast or fizzle look and despawns it.
struct npc_dm_land_mine : public ScriptedAI
{
    explicit npc_dm_land_mine(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void Reset() override { }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        DoCastSelf(Gilnid::SPELL_LAND_MINE_ARMING, true);
    }

    void UpdateAI(uint32 /*diff*/) override { }
};

// Gilnid 1763
struct boss_gilnid_rework : public BossAI
{
    explicit boss_gilnid_rework(Creature* creature) : BossAI(creature, BOSS_GILNID)
    {
        ScheduleOutOfCombatSay();
    }

    // ---------------------------------------------------------------------------------------------------------------
    // Encounter
    // ---------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        BossAI::Reset();
        ClearMechanicState();
        _doubleShift = false;
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (me->IsInEvadeMode())
            return;     // the instance refused the pull (CheckRequiredBosses)
        Talk(YELL_GILNID_AGGRO);

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GILNID;
        Mechanic::BeginEncounter(me, options);
        Describe();

        bool const heroic = Heroic();
        events.ScheduleEvent(EVENT_MOLTEN_METAL, Ms(Gilnid::kMoltenMetalFirstMinMs),
            Ms(Gilnid::kMoltenMetalFirstMaxMs));
        events.ScheduleEvent(EVENT_ROLL_OUT, Ms(Gilnid::kShotFirstMs));
        if (Gilnid::kLandmine(heroic))
            events.ScheduleEvent(EVENT_LANDMINE, Ms(Gilnid::kMineFirstMs));
        Log("engage", heroic ? "heroic" : "normal");
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        summons.DespawnAll();
        ClearMechanicState();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        ClearMechanicState();
        Log("death");
    }

    // Helpers never join the fight (BossAI's JustSummoned would zone them into combat).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (!_doubleShift && Gilnid::kDoubleShift(Heroic()) && me->IsInCombat()
            && me->HealthBelowPctDamaged(static_cast<int32>(Gilnid::kDoubleShiftHealthPct), damage))
            StartDoubleShift();
    }

    void UpdateAI(uint32 diff) override
    {
        // Balls and mines are tracked on every update, also while he is stunned or casting (and for .dmtest out of
        // combat).
        TrackBalls();
        TrackMines();

        if (!UpdateVictim())
        {
            if (!me->IsInCombat())
                _outOfCombat.Update(diff);
            return;
        }

        events.Update(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING | UNIT_STATE_STUNNED))
            return;

        while (uint32 const eventId = events.ExecuteEvent())
        {
            switch (eventId)
            {
                case EVENT_MOLTEN_METAL:
                    MoltenMetal(me->GetVictim());
                    events.ScheduleEvent(EVENT_MOLTEN_METAL, Ms(Gilnid::kMoltenMetalRepeatMinMs),
                        Ms(Gilnid::kMoltenMetalRepeatMaxMs));
                    break;
                case EVENT_ROLL_OUT:
                    RollOutTheShot();
                    events.ScheduleEvent(EVENT_ROLL_OUT, Ms(Gilnid::ShotCooldownMs(Heroic(), _doubleShift)));
                    break;
                case EVENT_LANDMINE:
                    TossLandmine();
                    events.ScheduleEvent(EVENT_LANDMINE, Ms(Gilnid::kMineCooldownMs));
                    break;
                default:
                    break;
            }
            if (me->HasUnitState(UNIT_STATE_CASTING))
                return;
        }

        DoMeleeAttackIfReady();
    }

    // ---------------------------------------------------------------------------------------------------------------
    // Mechanics (public: the .dmtest subcommands call them)
    // ---------------------------------------------------------------------------------------------------------------

    // GI1: stock Molten Metal, 2 s interruptible cast (the descriptor lists it).
    void MoltenMetal(Unit* target)
    {
        if (!target)
            return;
        me->CastSpell(target, SPELL_MOLTEN_METAL, false);
        Mechanic::NoteNextCastIn(me, SPELL_MOLTEN_METAL, Ms(Gilnid::kMoltenMetalRepeatMinMs));
        Log("molten-metal", target->GetName());
    }

    // GI2: one batch at the picked targets.
    void RollOutTheShot()
    {
        std::vector<Gilnid::Candidate<ObjectGuid>> const candidates = Candidates();
        std::vector<ObjectGuid> const targets = Gilnid::SelectShotTargets(candidates, Heroic(),
            [](uint32 n) { return urand(0, n - 1); });
        std::vector<Position> points;
        for (ObjectGuid const& guid : targets)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                points.push_back(player->GetPosition());
        RollOutAt(points, Gilnid::kHotShot(Heroic()));
    }

    // GI2 at the given points (a lane per point, all from one random pot).
    void RollOutAt(std::vector<Position> const& points, bool hot)
    {
        if (points.empty())
            return;
        Talk(YELL_GILNID_ROLL_OUT);
        DeadminesKit::Vec2 const pot = kPots[urand(0, static_cast<uint32>(kPots.size()) - 1)];
        uint32 launched = 0;
        for (Position const& point : points)
            if (LaunchBall(pot, ToVec(point), hot))
                ++launched;
        Log("roll-out", Acore::StringFormat("{} ball(s) from pot ({:.1f}, {:.1f}){}, lanes +{:.0f} yd past the wall",
            launched, pot.x, pot.y, hot ? ", hot shot" : "", Gilnid::kLaneExtraYd));
    }

    // One ball from `pot` through `target` to the wall. False when the lane or the ball cannot be made.
    bool LaunchBall(DeadminesKit::Vec2 pot, DeadminesKit::Vec2 target, bool hot)
    {
        std::optional<Gilnid::Lane> const lane = Gilnid::ComputeLane(pot, target, ToVec(me->GetPosition()));
        if (!lane)
            return false;
        float const facing = DeadminesKit::BearingTo(lane->from, lane->to);
        // The rolling path hugs the floor (the old straight spline from the dais floated over the floor below it).
        std::vector<Gilnid::PathPoint> const path = Gilnid::FloorPath(*lane, kFoundryPotZ,
            [this](float x, float y, float z) -> Optional<float>
            {
                float const h = me->GetMapHeight(x, y, z + Gilnid::kFloorPathMaxStepZ);
                return h > INVALID_HEIGHT ? Optional<float>(h) : std::nullopt;
            });
        Position const from = DeadminesKit::ToPosition(lane->from, kFoundryPotZ, facing);
        Position const to = DeadminesKit::ToPosition(lane->to, path.back().z, facing);

        TempSummon* ball = me->SummonCreature(NPC_DM_IRON_SHOT, from, TEMPSUMMON_TIMED_DESPAWN, 15000);
        npc_dm_iron_shot* ballAI = ball ? CAST_AI(npc_dm_iron_shot, ball->AI()) : nullptr;
        if (!ballAI)
        {
            if (ball)
                ball->DespawnOrUnsummon();
            return false;
        }

        BossMechanics::MechanicHandle const handle = Mechanic::Line(me, from, to, Gilnid::kLaneWidth,
            Ms(Gilnid::kLaneWarnMs)).Projectile(Gilnid::kShotSpeed).ProjectileUnit(ball).Damage(Gilnid::kShotPct)
            .Spell(Gilnid::SPELL_ROLL_OUT_THE_SHOT).Weakened().Tag(Gilnid::kTagRollOut);
        if (!handle)
        {
            ball->DespawnOrUnsummon();
            return false;
        }
        ballAI->Launch(path, Ms(Gilnid::kLaneWarnMs));

        Ball state;
        state.guid = ball->GetGUID();
        state.lane = *lane;
        state.hot = hot;
        state.last = lane->from;
        // Hot shot trails cover the in-room part only (the extension past the wall has no floor to burn).
        if (hot)
            state.segments = Gilnid::HotShotSegments(lane->wallLength, Gilnid::BlockExit(*lane, kPotBlock));
        _balls.push_back(std::move(state));
        return true;
    }

    // GI3: knocked down for 2 s (a stun with no mechanic, so the stun immunity does not stop it) and 5% of his health,
    // dealt by the script and logged under Bowled Over. Never the killing blow (he keeps 1 health).
    void BowledOver()
    {
        DoCastSelf(Gilnid::SPELL_BOWLED_OVER, true);
        uint32 damage = me->CountPctFromMaxHealth(static_cast<int32>(Gilnid::kBowledOverHealthPct));
        damage = me->GetHealth() > 1 ? std::min<uint32>(damage, me->GetHealth() - 1) : 0;
        if (damage)
            if (SpellInfo const* info = sSpellMgr->GetSpellInfo(Gilnid::SPELL_BOWLED_OVER))
            {
                SpellNonMeleeDamage log(me, me, info, SPELL_SCHOOL_MASK_NORMAL);
                log.damage = damage;
                me->SendSpellNonMeleeDamageLog(&log);
                me->DealSpellDamage(&log, false);
            }
        Milliseconds const now = GameTime::GetGameTimeMS();
        if (_lastBowledYell == Milliseconds::zero() || now - _lastBowledYell >= Ms(Gilnid::kBowledOverYellCooldownMs))
        {
            _lastBowledYell = now;
            Talk(YELL_GILNID_BOWLED_OVER);
        }
        Log("bowled-over", Acore::StringFormat("{} damage", damage));
    }

    // GI5: heroic below 50%; the shot every 10 s from now on (the next one at most 10 s away).
    void StartDoubleShift()
    {
        if (_doubleShift)
            return;
        _doubleShift = true;
        Talk(YELL_GILNID_DOUBLE_SHIFT);
        if (events.GetTimeUntilEvent(EVENT_ROLL_OUT) > Ms(Gilnid::kDoubleShiftCooldownMs))
            events.RescheduleEvent(EVENT_ROLL_OUT, Ms(Gilnid::kDoubleShiftCooldownMs));
        Log("double-shift");
    }

    // GI6: a mine at a random non-tank's feet.
    void TossLandmine()
    {
        std::optional<ObjectGuid> const target = Gilnid::SelectMineTarget(Candidates(),
            [](uint32 n) { return urand(0, n - 1); });
        if (!target)
            return;
        if (Player* player = ObjectAccessor::GetPlayer(*me, *target))
            PlaceMine(player->GetPosition());
    }

    void PlaceMine(Position const& pos)
    {
        Talk(EMOTE_GILNID_LANDMINE);
        DoCastSelf(Gilnid::SPELL_TOSS_LANDMINE, true);
        TempSummon* mine = me->SummonCreature(NPC_DM_LAND_MINE, pos, TEMPSUMMON_MANUAL_DESPAWN);
        if (!mine)
            return;

        // The lambda keeps the map and guids only (STAGE-M5-R-REPORT m-4): the registry calls it when the mine goes
        // off (players or a ball), never for a fizzle (the cap fizzles without a resolve).
        Map* map = me->GetMap();
        ObjectGuid const mineGuid = mine->GetGUID();
        uint32 const instanceId = me->GetInstanceId();
        BossMechanics::MechanicHandle const handle = Mechanic::Mine(me, pos, Gilnid::kMineRadius,
            Ms(Gilnid::kMineArmMs), Ms(Gilnid::kMineGraceMs)).Cap(Gilnid::kMineCapGroup, Gilnid::kMineCap)
            .Damage(Gilnid::kMinePct).School(SPELL_SCHOOL_FIRE).Spell(Gilnid::SPELL_LAND_MINE_DETONATION).Weakened()
            .Tag(Gilnid::kTagLandmine)
            .OnResolve([map, mineGuid, instanceId](BossMechanics::ResolveResult const& result)
            {
                if (result.fizzled)
                    return;
                if (Creature* unit = map ? map->GetCreature(mineGuid) : nullptr)
                {
                    unit->CastSpell(unit, Gilnid::SPELL_LAND_MINE_BLAST, true);
                    unit->DespawnOrUnsummon(1s);
                }
                LOG_INFO(kLogCategory, "dm-pilot gilnid landmine-detonated instance {}: {} player(s) hit", instanceId,
                    result.hits.size());
            });
        if (!handle)
        {
            mine->DespawnOrUnsummon();
            return;
        }

        for (MineEntry const& old : _mines.Add({ mineGuid, handle, ToVec(pos) }))
        {
            if (Creature* unit = ObjectAccessor::GetCreature(*me, old.unit))
            {
                unit->CastSpell(unit, Gilnid::SPELL_LAND_MINE_FIZZLE, true);
                unit->DespawnOrUnsummon(1s);
            }
            Log("landmine-fizzle", "the cap pushed out the oldest mine");
        }
        Log("landmine", Acore::StringFormat("at ({:.1f}, {:.1f}), {} live", pos.GetPositionX(), pos.GetPositionY(),
            _mines.Size()));
    }

private:
    struct Ball
    {
        ObjectGuid guid;
        Gilnid::Lane lane;
        DeadminesKit::Vec2 last;
        std::vector<Gilnid::Segment> segments;
        std::size_t nextSegment = 0;
        bool hot = false;
        bool bowled = false;
    };

    struct MineEntry
    {
        ObjectGuid unit;
        BossMechanics::MechanicHandle handle;
        DeadminesKit::Vec2 pos;
    };

    bool Heroic() const
    {
        return DeadminesKit::IsHeroicMap(me);
    }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        LOG_INFO(kLogCategory, "dm-pilot gilnid {} instance {}{}{}", mechanic, me->GetInstanceId(),
            detail.empty() ? "" : ": ", detail);
    }

    void ScheduleOutOfCombatSay()
    {
        _outOfCombat.Schedule(Ms(Gilnid::kOutOfCombatSayMs), [this](TaskContext ctx)
        {
            if (me->IsAlive() && !me->IsInCombat())
                Talk(SAY_GILNID_OUT_OF_COMBAT);
            ctx.Repeat();
        });
    }

    // Live players near him, the victim marked as the tank.
    std::vector<Gilnid::Candidate<ObjectGuid>> Candidates() const
    {
        std::vector<Gilnid::Candidate<ObjectGuid>> out;
        Unit const* victim = me->GetVictim();
        ObjectGuid const tank = victim ? victim->GetGUID() : ObjectGuid::Empty;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsInWorld() || !player->IsAlive() || player->IsGameMaster()
                || me->GetExactDist2d(player) > Gilnid::kShotTargetRange)
                continue;
            out.push_back({ player->GetGUID(), player->GetGUID() == tank });
        }
        return out;
    }

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.push_back({ NPC_GILNID, SPELL_MOLTEN_METAL, 1, Ms(Gilnid::kMoltenMetalEveryMs) });
        d.targets.push_back({ NPC_GILNID, 0 });
        d.ignores.push_back({ NPC_DM_IRON_SHOT });
        d.ignores.push_back({ NPC_DM_LAND_MINE });
        Mechanic::Describe(me, std::move(d));
    }

    void ClearMechanicState()
    {
        _balls.clear();
        _mines.Clear();
    }

    // Every rolling ball: Bowled Over (once per ball), the mine sweep, Hot shot segments it has passed. A ball that
    // reached the wall releases its last segments; a ball that vanished early (a reset) registers nothing more.
    void TrackBalls()
    {
        if (_balls.empty())
            return;
        DeadminesKit::Vec2 const self = ToVec(me->GetPosition());
        for (auto it = _balls.begin(); it != _balls.end();)
        {
            Ball& ball = *it;
            Creature* unit = ObjectAccessor::GetCreature(*me, ball.guid);
            npc_dm_iron_shot const* ai = unit ? CAST_AI(npc_dm_iron_shot, unit->AI()) : nullptr;
            if (!ai)
            {
                it = _balls.erase(it);
                continue;
            }
            bool const moving = ai->IsRolling() || ai->AtWall();
            DeadminesKit::Vec2 const now = ToVec(unit->GetPosition());
            if (moving)
            {
                if (!ball.bowled && me->IsAlive() && !me->IsInEvadeMode()
                    && Gilnid::SweptWithin(ball.last, now, self, Gilnid::kBowledOverRadius))
                {
                    ball.bowled = true;
                    BowledOver();
                }
                SweepMines(ball.last, now);
                if (ball.hot)
                    RegisterPassedSegments(ball, Gilnid::AlongLane(ball.lane, now), ai->AtWall(),
                        unit->GetPositionZ());
            }
            ball.last = now;
            if (ai->AtWall() && ball.nextSegment >= ball.segments.size())
                it = _balls.erase(it);
            else
                ++it;
        }
    }

    void RegisterPassedSegments(Ball& ball, float nowS, bool done, float z)
    {
        std::size_t const upTo = Gilnid::SegmentsPassed(ball.segments, ball.nextSegment, nowS, done);
        if (upTo > ball.nextSegment && ball.nextSegment == 0)
            Log("hot-shot", Acore::StringFormat("{} segment(s) on a {:.1f} yd lane", ball.segments.size(),
                ball.lane.length));
        for (; ball.nextSegment < upTo; ++ball.nextSegment)
        {
            Gilnid::Segment const& seg = ball.segments[ball.nextSegment];
            float const facing = DeadminesKit::BearingTo(ball.lane.from, ball.lane.to);
            Position const a = DeadminesKit::ToPosition(Gilnid::PointOnLane(ball.lane, seg.s0), z, facing);
            Position const b = DeadminesKit::ToPosition(Gilnid::PointOnLane(ball.lane, seg.s1), z, facing);
            DeadminesKit::LingerSpec linger;
            linger.duration = Ms(Gilnid::kHotShotDurationMs);
            linger.tick = Ms(Gilnid::kHotShotTickMs);
            linger.pct = Gilnid::kHotShotPct;
            linger.school = SPELL_SCHOOL_FIRE;
            linger.spellId = Gilnid::SPELL_HOT_SHOT;
            linger.slow = true;
            linger.color = BossMechanics::Color::Orange;
            linger.tag = Gilnid::kTagHotShot;
            DeadminesKit::Linger(me, BossMechanics::Shapes::Line(a, b, Gilnid::kLaneWidth), linger);
            // the slag look over the same 6 s (a dynamic object at the segment's middle)
            DeadminesKit::Vec2 const mid = Gilnid::PointOnLane(ball.lane, (seg.s0 + seg.s1) * 0.5f);
            me->CastSpell(mid.x, mid.y, z, Gilnid::SPELL_HOT_SHOT_GROUND, true);
        }
    }

    // A ball rolling over an armed mine sets it off (the registry resolves it on its next tick).
    void SweepMines(DeadminesKit::Vec2 from, DeadminesKit::Vec2 to)
    {
        if (_mines.Size() == 0)
            return;
        BossMechanics::Registry const* registry = Mechanic::Read(me->GetMap());
        if (!registry)
            return;
        for (MineEntry const& entry : _mines.Live())
        {
            if (!Gilnid::SweptWithin(from, to, entry.pos, Gilnid::kBallMineRadius))
                continue;
            BossMechanics::ActiveMechanic const* m = registry->Find(entry.handle.id);
            if (!m || !m->mine || !m->mine->armed || m->mine->spent || m->finished || m->cancelled)
                continue;
            Mechanic::Detonate(me, entry.handle);
            _sweptMines.push_back(entry.handle.id);
            Log("landmine-swept", "a ball set off an armed mine");
        }
        for (uint32 id : _sweptMines)
            _mines.RemoveIf([id](MineEntry const& e) { return e.handle.id == id; });
        _sweptMines.clear();
    }

    // Mines the registry is done with (set off, or ended with the encounter) leave the ledger; their unit goes too.
    void TrackMines()
    {
        if (_mines.Size() == 0)
            return;
        BossMechanics::Registry const* registry = Mechanic::Read(me->GetMap());
        std::vector<MineEntry> const gone = _mines.RemoveIf([registry](MineEntry const& e)
        {
            BossMechanics::ActiveMechanic const* m = registry ? registry->Find(e.handle.id) : nullptr;
            return !m || m->finished || m->cancelled;
        });
        for (MineEntry const& entry : gone)
            if (Creature* unit = ObjectAccessor::GetCreature(*me, entry.unit))
                unit->DespawnOrUnsummon(1s);
    }

    TaskScheduler _outOfCombat;
    std::vector<Ball> _balls;
    Gilnid::MineLedger<MineEntry> _mines;
    std::vector<uint32> _sweptMines;
    Milliseconds _lastBowledYell{ 0 };
    bool _doubleShift = false;
};

namespace
{
    boss_gilnid_rework* GilnidAI(ChatHandler* handler)
    {
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_GILNID);
        if (!boss)
            return nullptr;
        boss_gilnid_rework* ai = CAST_AI(boss_gilnid_rework, boss->AI());
        if (!ai)
            handler->SendErrorMessage("Gilnid does not run boss_gilnid_rework (is the instance bound to {}?).",
                kInstanceScriptName);
        return ai;
    }

    bool IsHot(Optional<std::string> const& arg)
    {
        return arg && *arg == "hot";
    }

    // `.dmtest gilnid info`
    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_GILNID, BOSS_GILNID);
    }

    // `.dmtest gilnid shot [hot]`: one ball from a random pot through the GM's spot (hot: with the Hot shot trail).
    bool HandleShot(ChatHandler* handler, Optional<std::string> hot)
    {
        boss_gilnid_rework* ai = GilnidAI(handler);
        if (!ai)
            return false;
        ai->RollOutAt({ handler->GetPlayer()->GetPosition() }, IsHot(hot));
        return true;
    }

    // `.dmtest gilnid batch`: one batch at the targets the fight would pick (heroic: everyone).
    bool HandleBatch(ChatHandler* handler)
    {
        boss_gilnid_rework* ai = GilnidAI(handler);
        if (!ai)
            return false;
        ai->RollOutTheShot();
        return true;
    }

    // `.dmtest gilnid bowled [hot]`: one ball through Gilnid's spot (Bowled Over if he stays in its lane).
    bool HandleBowled(ChatHandler* handler, Optional<std::string> hot)
    {
        boss_gilnid_rework* ai = GilnidAI(handler);
        if (!ai)
            return false;
        Creature const* boss = DeadminesTest::FindBoss(handler, NPC_GILNID);
        ai->RollOutAt({ boss->GetPosition() }, IsHot(hot));
        return true;
    }

    // `.dmtest gilnid mine`: one land mine at the GM's feet (any difficulty).
    bool HandleMine(ChatHandler* handler)
    {
        boss_gilnid_rework* ai = GilnidAI(handler);
        if (!ai)
            return false;
        ai->PlaceMine(handler->GetPlayer()->GetPosition());
        return true;
    }

    // `.dmtest gilnid doubleshift`: Double shift now (the shot every 10 s; heroic timers only matter in combat).
    bool HandleDoubleShift(ChatHandler* handler)
    {
        boss_gilnid_rework* ai = GilnidAI(handler);
        if (!ai)
            return false;
        ai->StartDoubleShift();
        return true;
    }

    // `.dmtest gilnid molten`: Molten Metal on his victim, else on the GM.
    bool HandleMolten(ChatHandler* handler)
    {
        boss_gilnid_rework* ai = GilnidAI(handler);
        if (!ai)
            return false;
        Creature* boss = DeadminesTest::FindBoss(handler, NPC_GILNID);
        Unit* target = boss->GetVictim() ? boss->GetVictim() : handler->GetPlayer();
        ai->MoltenMetal(target);
        return true;
    }

    ChatCommandTable const& GilnidTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
            { "shot", HandleShot, SEC_GAMEMASTER, Console::No },
            { "batch", HandleBatch, SEC_GAMEMASTER, Console::No },
            { "bowled", HandleBowled, SEC_GAMEMASTER, Console::No },
            { "mine", HandleMine, SEC_GAMEMASTER, Console::No },
            { "doubleshift", HandleDoubleShift, SEC_GAMEMASTER, Console::No },
            { "molten", HandleMolten, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_gilnid_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_gilnid_rework);
    RegisterDeadminesReworkCreatureAI(npc_dm_iron_shot);
    RegisterDeadminesReworkCreatureAI(npc_dm_land_mine);
    DeadminesTest::RegisterBoss("gilnid", GilnidTestCommands());
}
