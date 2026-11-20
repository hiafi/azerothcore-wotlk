/*
 * mod-dungeon-bosses, Blackrock Depths D22: Magmus (9938) and the six Ironhand Guardians (8982), "the Iron Hall"
 * (ruling 75: the statues become the fight). Build spec S4 "Magmus"
 * (docs/dungeons/blackrock-depths-4-imperial-seat.md, MG1-MG5; rulings 75, 76, 88), handoff sections 3.4 (row D22),
 * 3.5, 3.8 (NM: the hall is 39 yd wide), 3.9 (the `crossfire` row of `blackrock-depths-shapes-2`), section 8 #25 and
 * #26. Replaces stock `boss_magmus` and `brd_ironhand_guardian` (the statues' own Gout of Flame timer is gone): the
 * statues are unselectable scenery that turn, glow and breathe on his order. He has no SmartAI (verified live: none
 * for 9938 or 8982). Bound by apps/dbc-tools source/npcs/blackrock_depths/magmus.py. Pure rules (the clocks, the lane,
 * the strips, the pools): MagmusLogic.h.
 *
 *   MG1  War Stomp       stock copy: first at 8-12 s, every 8-12 s, a hit and a 2 s stun (was 8 s) on everyone
 *                        within 5 yd
 *   MG2  Fiery Burst     6 s, then every 10 s: a 2 s interruptible cast on a random player (the tank too, ruling
 *                        88), an 8 yd circle fixed where they stand when the cast starts: 25% / 40% + Weakened. A
 *                        kick cancels the circle (the descriptor's interrupt list: a reward)
 *   MG3  Crossfire       8 s, then every 15 s (heroic 12 s): he raises a fist (boss emote 1), the statue pair
 *                        nearest his y turns to the lane and glows 3 s, then a 10 yd lane wall to wall at his y
 *                        (locked when the fist goes up) ignites, 30% / 45% + Weakened, and burns 10% / 15% a
 *                        second. G2's drill shapes: the ignition (tag 25), the burn from 1 s later for 5 s (tag
 *                        26); the statues breathe from the ignition on
 *   MG4  Flame Wall      20 s, then every 30 s (heroic 25 s): yell 2; one statue row (never the side he stands on)
 *                        glows 3 s, then breathes along the hall; the 12 yd strip of floor along that wall burns
 *                        8 s, 10% / 15% a second (tag 27)
 *   MG5  Dripping Magma  heroic only: every 3 s of walking a 4 yd pool under him, 30 s, 8% a second, at most 6
 *
 *        "The tank can always walk him out": a stomp (a stun on the tank too) or a Fiery Burst cast never starts
 *        while a Crossfire's glow is up or would be when the stun ends; a Crossfire due waits for a cast in progress
 *        (MagmusLogic.h Timeline). No adds, no kill order, no dispel list; the descriptor holds the Fiery Burst kick.
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "brd magmus <mechanic> ..."
 * (module.dungeonbosses). Lambdas the registry keeps capture guids and values only. The throne door opens on his
 * death and his Lyceum yell (group 0) is the instance's (stock): neither is touched here.
 */

#include "ArenaGuard.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MagmusLogic.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <list>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdMagmus;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "magmus";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogMg(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // The floor under a point: the map's height within 6 yd of `refZ`, else `refZ`.
    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > 6.f)
            return refZ;
        return h;
    }

    // The test commands' forced mechanics (`.dbtest brd magmus ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Stomp,
        Burst,
        Crossfire,
        FlameWall,
        Pool,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Ironhand Guardian 8982: scenery. It never fights (the stock flags already forbid it); Magmus's script tells it to
// turn, glow and breathe. Stock `brd_ironhand_guardian`'s Gout of Flame timer, and the instance's SetData(0, 1) switch
// for it, are gone: SetData is ignored.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_ironhand_guardian_rework : public ScriptedAI
{
    explicit npc_ironhand_guardian_rework(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        Rest();
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void SetData(uint32 /*type*/, uint32 /*data*/) override { }

    void UpdateAI(uint32 diff) override
    {
        if (!_turned)
            return;
        _turnedMs += diff;
        if (_turnedMs >= _holdMs)
            Rest();
    }

    // Faces `point` for `holdMs`, then turns back to where it stood.
    void TurnTo(DungeonKit::Vec2 point, uint32 holdMs)
    {
        me->SetFacingTo(DungeonKit::BearingTo(DungeonKit::PlaneOf(me), point));
        _turned = true;
        _turnedMs = 0;
        _holdMs = holdMs;
    }

    // The glow: a 3 s state on the statue (a self aura of 3 s).
    void Glow()
    {
        me->CastSpell(me, SPELL_MG_STATUE_GLOW, true);
    }

    // One breath at a point (a look; the damage is the registry's).
    void Breathe(DungeonKit::Vec2 point)
    {
        me->CastSpell(point.x, point.y, me->GetPositionZ(), SPELL_MG_STATUE_BREATH, true);
    }

    // Back to rest: no glow, facing where it stood.
    void Rest()
    {
        me->RemoveAurasDueToSpell(SPELL_MG_STATUE_GLOW);
        if (_turned)
            me->SetFacingTo(me->GetHomePosition().GetOrientation());
        _turned = false;
        _turnedMs = 0;
        _holdMs = 0;
    }

private:
    bool _turned = false;
    uint32 _turnedMs = 0;
    uint32 _holdMs = 0;
};

// ---------------------------------------------------------------------------------------------------------------------
// Magmus 9938
// ---------------------------------------------------------------------------------------------------------------------
struct boss_magmus_rework : public BossAI
{
private:
    struct LiveLane
    {
        bool active = false;
        Lane lane;
        CrossfirePlan plan;
        float z = 0.f;
        uint64 lastBreathMs = 0;
        std::vector<ObjectGuid> pair;
    };

    struct WallStatue
    {
        ObjectGuid guid;
        std::size_t row = 0;
    };

    struct LiveWall
    {
        bool active = false;
        Side side = Side::LowX;
        uint64 startMs = 0;
        float z = 0.f;
        uint64 lastBreathMs = 0;
        std::vector<WallStatue> row;
    };

    struct Burst
    {
        bool active = false;
        MechanicHandle handle;
        uint64 endMs = 0;       // the bar's end on the AI's clock
    };

    struct Pool
    {
        MechanicHandle handle;
        ObjectGuid stalker;
        uint64 expiresMs = 0;
    };

public:
    explicit boss_magmus_rework(Creature* creature)
        : BossAI(creature, BOSS_MAGMUS), _arena(MagmusArena(), LeashOptions(kBoss)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the summon list (the pool stalkers)
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        StartFight();
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogMg("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_MAGMUS_DEATH);
        Cleanup();
        BossAI::JustDied(killer);       // TYPE_IRON_HALL = DONE: the instance opens the throne door 170575
        LogMg("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
    }

    // The pool stalkers join the summon list (BossAI despawns it) but not the fight.
    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        summons.Summon(summon);
        summon->SetReactState(REACT_PASSIVE);
    }

    // MG2: a kick (or a stun) that ends the cast ends the circle with it ("an interrupted cast ends any hold it
    // started", rule 13).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || spell->Id != SPELL_MG_FIERY_BURST_CAST || !_burst.active)
            return;
        Mechanic::Cancel(me, _burst.handle);
        _burst = Burst{};
        LogMg("fiery-burst-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        UpdateLooks();      // the statues' breaths and the pools' life run out of combat too (`.dbtest`)

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        RunTimers();
        if (_heroic && _drip.Step(_clockMs, DungeonKit::PlaneOf(me), diff))
            DropPool();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull, the clocks
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight()
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_MAGMUS;
        Mechanic::BeginEncounter(me, options);
        _registered = true;
        _arena.Engage(me);
        _fighting = true;
        uint32 const firstStomp = urand(kStompEveryMinMs, kStompEveryMaxMs);
        _timeline.Start(_heroic, _clockMs, firstStomp);
        _drip.Start(_clockMs, DungeonKit::PlaneOf(me));
        Describe();
        LogMg("engage", Acore::StringFormat("heroic={} stomp={}s burst={}s crossfire={}s wall={}s", _heroic ? 1 : 0,
            firstStomp / 1000, kBurstFirstMs / 1000, kCrossfireFirstMs / 1000, kWallFirstMs / 1000));
    }

    // Boss data (S4 "Boss data"): no kill order, no dispel list; the Fiery Burst kick (a reward) is the one entry.
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_MAGMUS, SPELL_MG_FIERY_BURST_CAST, 1, Ms(kBurstEveryMs));
        Mechanic::Describe(me, std::move(d));
    }

    void RunTimers()
    {
        // MG3 first: it waits only for a cast already going on (a lane needs him free to walk).
        if (_timeline.Due(Beat::Crossfire, _clockMs))
        {
            if (!me->HasUnitState(UNIT_STATE_CASTING) && StartCrossfire())
                _timeline.Fired(Beat::Crossfire, _clockMs);
            else
                _timeline.Retry(Beat::Crossfire, _clockMs);
        }
        // MG4 (not a cast: nothing here waits for a bar)
        if (_timeline.Due(Beat::FlameWall, _clockMs))
        {
            if (StartFlameWall())
                _timeline.Fired(Beat::FlameWall, _clockMs);
            else
                _timeline.Retry(Beat::FlameWall, _clockMs);
        }
        // MG1 and MG2 are not started while a cast is going on, and wait out a Crossfire's glow
        if (_timeline.Due(Beat::Stomp, _clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (CastStomp())
                _timeline.Fired(Beat::Stomp, _clockMs, urand(kStompEveryMinMs, kStompEveryMaxMs));
            else
                _timeline.Retry(Beat::Stomp, _clockMs);
        }
        if (_timeline.Due(Beat::Burst, _clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (StartBurst())
                _timeline.Fired(Beat::Burst, _clockMs);
            else
                _timeline.Retry(Beat::Burst, _clockMs);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MG1 War Stomp
    // ----------------------------------------------------------------------------------------------------------------

    // Everyone within 5 yd, the tank too (stock): the hit and the 2 s stun are the spell's own.
    bool CastStomp()
    {
        if (me->CastSpell(me, SPELL_MG_WAR_STOMP, false) != SPELL_CAST_OK)
            return false;
        LogMg("war-stomp", Acore::StringFormat("heroic={} pct={:.0f} stun={}s", _heroic ? 1 : 0,
            kStompPct(_heroic), kStompStunMs / 1000));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MG2 Fiery Burst
    // ----------------------------------------------------------------------------------------------------------------

    // The target: a random player of the fight, the tank included (ruling 88), in range and in sight. Out of combat the
    // GM of a test command stands in for the group.
    Player* PickBurstTarget()
    {
        if (!me->IsEngaged())
            return _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer);
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kBurstRangeYd;
        rule.requireLos = true;
        return DungeonKit::PickPlayer(me, rule);
    }

    // The 2 s bar on the target (interruptible) and the 8 yd circle where they stand, landing as the bar ends. False:
    // nobody to pick, or a cast is going on.
    bool StartBurst()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING) || _burst.active)
            return false;
        Player* target = PickBurstTarget();
        if (!target)
            return false;
        if (me->CastSpell(target, SPELL_MG_FIERY_BURST_CAST, false) != SPELL_CAST_OK)
            return false;

        Position const spot(target->GetPositionX(), target->GetPositionY(),
            GroundZ(me, target->GetPositionX(), target->GetPositionY(), target->GetPositionZ()), 0.f);
        float const pct = kBurstPct(_heroic);
        MechanicRef ref = Mechanic::Circle(me, spot, kBurstRadiusYd, Ms(kBurstCastMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_MG_FIERY_BURST).Weakened()
            .Tag(TAG_MG_FIERY_BURST)
            .OnResolve(OnMagmus([spot](boss_magmus_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.BurstLands(spot, r);
            }));
        if (!ref.IsValid())
        {
            me->InterruptNonMeleeSpells(false);
            LogMg("fiery-burst-refused", target->GetName());
            return false;
        }
        _burst.active = true;
        _burst.handle = ref.Handle();
        _burst.endMs = _clockMs + kBurstCastMs;
        Track(ref.Handle());
        Mechanic::NoteNextCastIn(me, SPELL_MG_FIERY_BURST_CAST, Ms(kBurstEveryMs));
        LogMg("fiery-burst", Acore::StringFormat("heroic={} on={} at=({:.1f}, {:.1f}) pct={:.0f} r={:.0f}",
            _heroic ? 1 : 0, target->GetName(), spot.GetPositionX(), spot.GetPositionY(), pct, kBurstRadiusYd));
        return true;
    }

    // The circle landed (the bar finished): the blast look at the spot.
    void BurstLands(Position const& spot, BossMechanics::ResolveResult const& r)
    {
        _burst = Burst{};
        if (r.fizzled)
            return;
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_MG_FIERY_BURST_LOOK, true);
        LogMg("fiery-burst-lands", Acore::StringFormat("hits={}", r.hits.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The statues
    // ----------------------------------------------------------------------------------------------------------------

    struct StatueRef
    {
        ObjectGuid guid;
        std::size_t row = 0;
        Side side = Side::LowX;
    };

    // The six statues in the grid (found each time: a handful per fight, never held between two).
    std::vector<StatueRef> Statues()
    {
        std::list<Creature*> found;
        me->GetCreatureListWithEntryInGrid(found, NPC_IRONHAND_GUARDIAN, 150.f);
        std::vector<StatueRef> out;
        for (Creature* statue : found)
            if (statue && statue->IsInWorld())
                out.push_back({ statue->GetGUID(), NearestStatueRow(statue->GetPositionY()),
                    StatueSideOf(statue->GetPositionX()) });
        return out;
    }

    // Its AI when it runs this script (an unbound statue, wave 2 off, has none of it and does nothing).
    npc_ironhand_guardian_rework* StatueAI(ObjectGuid guid)
    {
        Creature* statue = ObjectAccessor::GetCreature(*me, guid);
        if (!statue || !statue->IsAIEnabled)
            return nullptr;
        return dynamic_cast<npc_ironhand_guardian_rework*>(statue->AI());
    }

    void AllStatuesRest()
    {
        for (StatueRef const& ref : Statues())
            if (npc_ironhand_guardian_rework* ai = StatueAI(ref.guid))
                ai->Rest();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MG3 Crossfire
    // ----------------------------------------------------------------------------------------------------------------

    // The fist (emote 1, the statue pair of the lane's row turns to the lane's center and glows) and the lane's two
    // mechanics: the ignition at the glow's end and the burn from a second later. The lane is where he stands now (its
    // y is locked here: walking him away is the answer). False: the registry refused it.
    bool StartCrossfire()
    {
        float const z = me->GetPositionZ();
        Lane const lane = LaneAt(me->GetPositionY());
        Position const from(lane.from.x, lane.from.y, z, lane.facing);

        float const ignitionPct = kCrossfireIgnitionPct(_heroic);
        float const burnPct = kCrossfireBurnPct(_heroic);
        {
            MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(from, lane.facing, lane.length,
                lane.width), Ms(kGlowMs));
            ref.Damage(ignitionPct).TankDamage(ignitionPct).School(SPELL_SCHOOL_FIRE)
                .Spell(SPELL_MG_CROSSFIRE_IGNITION).Weakened().Tag(TAG_MG_CROSSFIRE_IGNITION);
            if (!ref.IsValid())
            {
                LogMg("crossfire-refused", "the registry refused the ignition");
                return false;
            }
            Track(ref.Handle());
        }
        {
            MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(from, lane.facing, lane.length,
                lane.width), Ms(kBurnWarnMs));
            ref.Persistent(Ms(kBurnLifeMs), Ms(kBurnTickMs)).Damage(burnPct).TankDamage(burnPct)
                .School(SPELL_SCHOOL_FIRE).Spell(SPELL_MG_CROSSFIRE_BURN).NoFillTimer().Tag(TAG_MG_CROSSFIRE_BURN);
            if (ref.IsValid())
                Track(ref.Handle());
        }

        _lane = LiveLane{};
        _lane.active = true;
        _lane.lane = lane;
        _lane.plan = PlanCrossfire(_clockMs);
        _lane.z = z;
        std::string turned;
        for (StatueRef const& statue : Statues())
        {
            if (statue.row != lane.row)
                continue;
            if (npc_ironhand_guardian_rework* ai = StatueAI(statue.guid))
            {
                ai->TurnTo(lane.center, kCrossfireEndMs);
                ai->Glow();
                _lane.pair.push_back(statue.guid);
                turned += Acore::StringFormat(" {}", statue.side == Side::LowX ? "low-x" : "high-x");
            }
        }
        Talk(EMOTE_MAGMUS_FIST);
        LogMg("crossfire", Acore::StringFormat("heroic={} y={:.1f} row={} length={:.1f} ignition={:.0f}% "
            "burn={:.0f}%/s statues{}", _heroic ? 1 : 0, lane.center.y, lane.row, lane.length, ignitionPct, burnPct,
            turned.empty() ? " none" : turned));
        return true;
    }

    // One breath of the pair, and at the first one the burst at both lane ends.
    void LaneBreath(bool first)
    {
        for (ObjectGuid const& guid : _lane.pair)
            if (npc_ironhand_guardian_rework* ai = StatueAI(guid))
                ai->Breathe(_lane.lane.center);
        if (!first)
            return;
        me->CastSpell(_lane.lane.from.x, _lane.lane.from.y, _lane.z, SPELL_MG_CROSSFIRE_END_LOOK, true);
        me->CastSpell(_lane.lane.to.x, _lane.lane.to.y, _lane.z, SPELL_MG_CROSSFIRE_END_LOOK, true);
        LogMg("crossfire-ignites", Acore::StringFormat("y={:.1f}", _lane.lane.center.y));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MG4 Flame Wall
    // ----------------------------------------------------------------------------------------------------------------

    // The yell, one row glowing and turning down the hall, and the strip along that wall (a persistent line). False:
    // the registry refused it.
    bool StartFlameWall()
    {
        float const z = me->GetPositionZ();
        Side const side = ChooseWallSide(me->GetPositionX(), _lastWallSide, urand(0, 1));
        Strip const strip = StripOf(side);
        Position const from(strip.from.x, strip.from.y, z, strip.facing);
        float const pct = kWallPct(_heroic);
        {
            MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(from, strip.facing, strip.length,
                strip.width), Ms(kGlowMs));
            ref.Persistent(Ms(kWallLifeMs), Ms(kWallTickMs)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE)
                .Spell(SPELL_MG_FLAME_WALL).Tag(TAG_MG_FLAME_WALL);
            if (!ref.IsValid())
            {
                LogMg("flame-wall-refused", "the registry refused the strip");
                return false;
            }
            Track(ref.Handle());
        }
        _lastWallSide = side;
        _wall = LiveWall{};
        _wall.active = true;
        _wall.side = side;
        _wall.startMs = _clockMs;
        _wall.z = z;
        uint32 turned = 0;
        for (StatueRef const& statue : Statues())
        {
            if (statue.side != side)
                continue;
            if (npc_ironhand_guardian_rework* ai = StatueAI(statue.guid))
            {
                ai->TurnTo(WallBreathPoint(side, statue.row), kWallEndMs);
                ai->Glow();
                _wall.row.push_back({ statue.guid, statue.row });
                ++turned;
            }
        }
        Talk(YELL_MAGMUS_WALL);
        LogMg("flame-wall", Acore::StringFormat("heroic={} side={} strip=x{:.1f}..{:.1f} floor={:.0f}yd left "
            "pct={:.0f}%/s statues={}", _heroic ? 1 : 0, side == Side::LowX ? "low-x" : "high-x", strip.outerX,
            strip.innerX, FloorLeftYd(), pct, turned));
        return true;
    }

    void WallBreath()
    {
        for (WallStatue const& statue : _wall.row)
            if (npc_ironhand_guardian_rework* ai = StatueAI(statue.guid))
                ai->Breathe(WallBreathPoint(_wall.side, statue.row));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MG5 Dripping Magma (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // A 4 yd pool under him: the cap retires the oldest first; a stalker carries the lava look.
    void DropPool()
    {
        for (std::size_t retire = PoolsToRetire(_pools.size()); retire > 0 && !_pools.empty(); --retire)
        {
            RetirePool(_pools.front());
            _pools.erase(_pools.begin());
        }
        float const x = me->GetPositionX();
        float const y = me->GetPositionY();
        Position const at(x, y, GroundZ(me, x, y, me->GetPositionZ()), 0.f);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(at, kPoolRadiusYd), Ms(kPoolWarnMs));
        ref.Persistent(Ms(PoolLifeAfterWarnMs()), Ms(kPoolTickMs)).Damage(kPoolPct).TankDamage(kPoolPct)
            .School(SPELL_SCHOOL_FIRE).Spell(SPELL_MG_DRIPPING_MAGMA).NoFillTimer().Tag(TAG_MG_DRIPPING_MAGMA);
        if (!ref.IsValid())
        {
            LogMg("pool-refused", "the registry refused the pool");
            return;
        }
        Pool pool;
        pool.handle = ref.Handle();
        pool.expiresMs = _clockMs + kPoolLifeMs;
        Track(pool.handle);
        if (Creature* stalker = me->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_MANUAL_DESPAWN))
        {
            stalker->CastSpell(stalker, SPELL_MG_POOL_LOOK, true);
            pool.stalker = stalker->GetGUID();
        }
        _pools.push_back(pool);
        LogMg("dripping-magma", Acore::StringFormat("at=({:.1f}, {:.1f}) pct={:.0f}%/s standing={}", x, y, kPoolPct,
            _pools.size()));
    }

    void RetirePool(Pool const& pool)
    {
        Mechanic::Cancel(me, pool.handle);
        if (Creature* stalker = pool.stalker ? ObjectAccessor::GetCreature(*me, pool.stalker) : nullptr)
            stalker->DespawnOrUnsummon();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The looks that run on the clock
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateLooks()
    {
        if (_lane.active)
        {
            if (_clockMs > _lane.plan.endMs + kBreathEveryMs)
            {
                _lane = LiveLane{};
            }
            else if (_clockMs >= _lane.plan.ignitionMs)
            {
                uint64 const due = NextBreathMs(_lane.plan.ignitionMs, _lane.lastBreathMs, _lane.plan.endMs);
                if (due && _clockMs >= due)
                {
                    LaneBreath(_lane.lastBreathMs == 0);
                    _lane.lastBreathMs = due;
                }
            }
        }
        if (_wall.active)
        {
            uint64 const igniteMs = _wall.startMs + kGlowMs;
            uint64 const endMs = _wall.startMs + kWallEndMs;
            if (_clockMs > endMs + kBreathEveryMs)
            {
                _wall = LiveWall{};
            }
            else if (_clockMs >= igniteMs)
            {
                uint64 const due = NextBreathMs(igniteMs, _wall.lastBreathMs, endMs);
                if (due && _clockMs >= due)
                {
                    WallBreath();
                    _wall.lastBreathMs = due;
                }
            }
        }
        // A circle whose resolve was never seen (the registry dropped it): the next Fiery Burst may start.
        if (_burst.active && _clockMs > _burst.endMs + 3000)
            _burst = Burst{};
        // The pools that ran out: their stalkers go (the registry's persistence ends on its own).
        while (!_pools.empty() && _pools.front().expiresMs <= _clockMs)
        {
            RetirePool(_pools.front());
            _pools.erase(_pools.begin());
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // State
    // ----------------------------------------------------------------------------------------------------------------

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnMagmus(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (!map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_magmus_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _registered = true;     // a registry encounter of ours exists now (a `.dbtest` one included)
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // The pull's state: nothing pending, no pool, stalker, glow, stun or lane left (Reset, evade, death, a new pull).
    // The registry's encounter ends too: the pools and the burn are its mechanics.
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        if (_registered)
        {
            Mechanic::EndEncounter(me);
            _registered = false;
        }
        if (_burst.active)
            me->InterruptNonMeleeSpells(false);
        for (Pool const& pool : _pools)
            if (Creature* stalker = pool.stalker ? ObjectAccessor::GetCreature(*me, pool.stalker) : nullptr)
                stalker->DespawnOrUnsummon();
        _pools.clear();
        AllStatuesRest();
        _lane = LiveLane{};
        _wall = LiveWall{};
        _burst = Burst{};
        _lastWallSide.reset();
        _fighting = false;
        _timeline = Timeline{};
        _drip = DripTracker{};
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_MG_WAR_STOMP);
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd magmus` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        switch (kind)
        {
            case TestKind::Stomp:
                if (!CastStomp())
                    return "The stomp was refused (a cast is going on).";
                break;
            case TestKind::Burst:
                if (!StartBurst())
                    return "No Fiery Burst: nobody to pick (out of combat the GM is the target), or casting.";
                break;
            case TestKind::Crossfire:
                if (!StartCrossfire())
                    return "The registry refused the lane.";
                if (_fighting)
                    _timeline.Fired(Beat::Crossfire, _clockMs);
                break;
            case TestKind::FlameWall:
                if (!StartFlameWall())
                    return "The registry refused the strip.";
                if (_fighting)
                    _timeline.Fired(Beat::FlameWall, _clockMs);
                break;
            case TestKind::Pool:
                DropPool();
                break;
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd magmus heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
        if (_fighting)
            _timeline.heroic = heroic;
    }

    std::string TestState()
    {
        auto left = [this](uint64 at) -> std::string
        {
            return at ? std::to_string(at > _clockMs ? (at - _clockMs) / 1000 : 0) + "s" : "-";
        };
        return Acore::StringFormat("magmus heroic={} fighting={} stomp={} burst={} crossfire={} wall={} lane={} "
            "wall-live={} pools={} burst-live={} live={}", _heroic ? 1 : 0, _fighting ? 1 : 0,
            left(_timeline.stompAt), left(_timeline.burstAt), left(_timeline.crossfireAt), left(_timeline.wallAt),
            _lane.active ? 1 : 0, _wall.active ? 1 : 0, _pools.size(), _burst.active ? 1 : 0, _live.size());
    }

private:
    DungeonKit::ArenaGuard _arena;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _registered = false;       // a registry encounter of ours exists
    uint64 _clockMs = 0;            // the AI's own clock: nothing here waits for a cast bar
    Timeline _timeline;             // MG1-MG4
    DripTracker _drip;              // MG5
    LiveLane _lane;
    LiveWall _wall;
    std::optional<Side> _lastWallSide;
    Burst _burst;
    std::vector<Pool> _pools;
    std::vector<MechanicHandle> _live;
    ObjectGuid _testPlayer;
};

namespace
{
    boss_magmus_rework* MagmusAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_MAGMUS);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_magmus_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_magmus_rework* ai = MagmusAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(kind, handler->GetPlayer());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    // `.dbtest brd magmus info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_MAGMUS, BOSS_MAGMUS);
    }

    // `.dbtest brd magmus state`: his clocks and what stands.
    bool HandleState(ChatHandler* handler)
    {
        boss_magmus_rework* ai = MagmusAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd magmus stomp`: MG1 now (the hit and the 2 s stun on everyone within 5 yd of him).
    bool HandleStomp(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Stomp, "War Stomp: everyone within 5 yd takes the hit and a 2 s stun.");
    }

    // `.dbtest brd magmus burst`: MG2 now (out of combat you are the target).
    bool HandleBurst(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Burst, "Fiery Burst: a 2 s cast, an 8 yd circle where the target stands.");
    }

    // `.dbtest brd magmus crossfire`: MG3 now, at his y.
    bool HandleCrossfire(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Crossfire, "Crossfire: a fist, a 3 s glow on the statue pair, then the lane.");
    }

    // `.dbtest brd magmus flamewall`: MG4 now.
    bool HandleFlameWall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::FlameWall, "Flame Wall: a statue row glows 3 s, then the strip burns 8 s.");
    }

    // `.dbtest brd magmus pool`: MG5 now, a pool under him (any difficulty).
    bool HandlePool(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Pool, "Dripping Magma: a pool under him (the cap is 6).");
    }

    // `.dbtest brd magmus clear`: every zone, pool, stalker and glow goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest brd magmus heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_magmus_rework* ai = MagmusAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossMagmusTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "stomp",     HandleStomp,     SEC_GAMEMASTER, Console::No },
            { "burst",     HandleBurst,     SEC_GAMEMASTER, Console::No },
            { "crossfire", HandleCrossfire, SEC_GAMEMASTER, Console::No },
            { "flamewall", HandleFlameWall, SEC_GAMEMASTER, Console::No },
            { "pool",      HandlePool,      SEC_GAMEMASTER, Console::No },
            { "clear",     HandleClear,     SEC_GAMEMASTER, Console::No },
            { "heroic",    HandleHeroic,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_magmus_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_magmus_rework, BlackrockDepthsRework::kInstanceScriptName);
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_ironhand_guardian_rework, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("magmus", BossMagmusTestCommands());
}
