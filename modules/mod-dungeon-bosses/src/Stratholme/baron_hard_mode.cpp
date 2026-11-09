/*
 * mod-dungeon-bosses, Stratholme S15: Baron Rivendare's hard mode, the Ultimatum (heroic only). WP-S15 owns this file.
 * Build spec: docs/dungeons/stratholme-rework.md ST 3709-3747 (Hard mode), ST 3807-3828 (Implementation), ST 3868-3871
 * (the HM rows); handoff section 3.7, section 3.5 row S15, section 3.6 (500k), section 11 #1 (two "Condemned" names
 * kept; the boss's is its own id in 206720-206734). Pure part: BaronHardModeLogic.h (tests/strat_ultimatum_test.cpp).
 * Data: apps/dbc-tools source/npcs/stratholme/baron_hard_mode.py (spells 206720-206734, Ysida, Risen 300589) and
 * WP-S15's SQL rev (Ysida's gossip option and its conditions, her SmartAI select row, texts 11-14 and her line 2).
 *
 * The opt-in: on heroic, while the Baron Run's clock runs and he neither fights nor is dead, Ysida's gossip offers the
 * Ultimatum; choosing it sets DATA_ULTIMATUM (her SmartAI's SetData(20, 1); the instance refuses it otherwise, saves
 * it, keeps it through wipes while the clock runs, clears it when the clock runs out or he dies, records BOSS_ULTIMATUM
 * on a lit kill, rides the loot bit and opens the exit gate on his death when Ysida is dead).
 *
 * The fight (UltimatumFight, a BaronHardMode on S14's AI through BaronFight.h; S14 makes one per heroic pull with the
 * flag lit):
 *   pull             500k (create health, restored on a wipe), mounted on the Deathcharger (display 10718), yell 11,
 *                    the loot bit, Ysida, Risen above the skeletons in the kill order.
 *   HM1 Execution    first at 15 s, then every 25 s on a fixed cadence (S14's cast queue; the charge waits for it
 *                    and it for the charge, the Shadow Bolt for both; a late start never pushes the next one):
 *                    a 3 s channel at Ysida (emote line 12, the purple beam) and a registry line Soak (2 yd, him to
 *                    her; the fewest Condemned stacks first) for the bots. At its end the first player on the line (by
 *                    distance from him) takes 30% Shadow x (1 + their Condemned stacks) (206721) and a Condemned
 *                    stack. Nobody: Ysida loses a third of her life (206722's look). The third miss and she falls:
 *                    she is hidden (alive, out of sight: never killed mid-attempt, so a wipe needs no corpse and no
 *                    respawn), her cage opens, Ysida, Risen (300589, 40k) rises at her spot (yell 14) and he gains
 *                    the Price of Defiance (+200% damage, 206725). No executions after that.
 *   HM2 Condemned    206723, a stack per execution taken, the whole fight, no cap; 206724, 1% Shadow a second, 10 s.
 *   HM3 Deathcharger first at 22 s, then every 30 s (a fixed cadence): the farthest non-tank is marked (206726,
 *                    emote line 13) and a 6 yd lane follows them from him for 3 s (a telegraph-only registry line
 *                    Zone aimed at them, X2's drop spot: the room's edge, away from the group, off the bone piles;
 *                    everyone but the target eligible). At the lock he charges down the drawn lane (a charge, not a
 *                    teleport; the end clamped with S14's CanStandAt along the whole path, so he never leaves his
 *                    arena or trips the stock leash): the lane's hit rides with him (a static registry projectile
 *                    line at his charge speed, 50% Physical and Weakened on everyone else as he passes, 206728's
 *                    hit flash on each), the target takes 20% (206727, lands as he does), and when he
 *                    lands the lane rots for 20 s: rot stalkers every 5 yd (S14's SpawnRot, 3 yd: they raise the
 *                    piles there and heal, HM4) and a persistent 6 yd line (5% Shadow a second, one Weakened per
 *                    player, a 1 s grace).
 *   HM4 rot          Death and Decay lasts 45 s (DeathAndDecayLifeMs); every live rot (Death and Decay's and the
 *                    trail's) heals him 1% of his maximum health and each undead of his (skeletons, Ysida, Risen) 5%
 *                    of theirs a second while they stand inside, once a second per unit (206731).
 *   cleanup          death, evade, reset: the Price, the mount, the 500k (a wipe only), Condemned on every player; on
 *                    a wipe a fallen Ysida shows again in her closed cage at full health (S14 despawns Ysida, Risen,
 *                    the piles, the rots and the skeletons); on a kill a fallen Ysida dies before the instance reads
 *                    her (the exit gate). The flag stays with the instance (ruling 60).
 *
 * Every firing logs one INFO line "strat baron hm-<mechanic> ..." (S14's BaronFight::Log, module.dungeonbosses).
 * `.dbtest strat ultimatum <sub>` drives it.
 */

#include "BaronFight.h"
#include "BaronHardModeLogic.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <limits>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratUltimatum;
using BossMechanics::MechanicRef;
using StratBaron::BaronFight;
using StratBaron::BaronHardMode;
using StratBaron::RotInfo;
using StratBaron::RotSpec;

namespace
{
    float constexpr kFloorProbeUpYd = 2.f;
    float constexpr kFloorMaxDropYd = 4.f;
    float constexpr kNearestPlayerYd = 100.f;

    // Create health is the base the engine rebuilds max health from (the Deadmines and Ras hard modes' SetBossHealth).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + kFloorProbeUpYd);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > kFloorMaxDropYd) ? z : floor;
    }

    Point3 Point3Of(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY(), p.GetPositionZ() };
    }

    // A unit of the fight stands in a rot: within its radius on the plane, on the same floor (S14's pile rule).
    bool InRot(Unit const* unit, RotInfo const& rot)
    {
        return unit && StratBaron::PileInRot(Point3Of(unit->GetPosition()), Point3Of(rot.center), rot.radius);
    }

    // The living players of the map, not game masters (Ysida, Risen's pick, the test commands).
    std::vector<Player*> LivingPlayers(Map* map)
    {
        std::vector<Player*> out;
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->IsAlive() && player->IsInWorld() && !player->IsGameMaster())
                    out.push_back(player);
        return out;
    }
}

// -------------------------------------------------------------------------------------------------------------------
// UltimatumFight: the hard mode for one pull
// -------------------------------------------------------------------------------------------------------------------

class UltimatumFight : public BaronHardMode
{
public:
    void OnEngage(BaronFight& fight) override
    {
        Creature* baron = fight.Baron();
        _instance = baron->GetInstanceScript();
        _baseCreateHealth = baron->GetCreateHealth();
        SetCreatureHealth(baron, kHardModeHealth);
        baron->Mount(kDeathchargerDisplay);
        // The instance already rides the bit while the flag is lit; set again here so the hard mode fight carries it.
        DungeonKit::SetHardModeLoot(baron, true);
        baron->AI()->Talk(YELL_BARON_HARD_MODE_PULL);
        Mechanic::EditDescriptor(baron, [](BossMechanics::Descriptor& d)
        {
            // Kill order (ST "Boss data"): Ysida, Risen first, then the skeletons (2), then him.
            d.targets.push_back(BossMechanics::TargetEntry(NPC_ST_YSIDA_RISEN, kRisenTargetPriority));
        });

        _nextExecutionAt = kExecutionFirstMs;
        _nextChargeAt = kChargeFirstMs;
        _executionQueued = false;
        _chargeQueued = false;
        _misses = 0;
        _ysidaFell = false;
        _heal.Reset();
        if (Creature* ysida = Ysida())
        {
            ysida->SetRegeneratingHealth(false);    // a third per miss must stick (out of combat she regenerates fast)
            if (ysida->IsAlive())
                ysida->SetHealth(ysida->GetMaxHealth());
        }
        QueueCasts(fight);
        fight.Log("hm-engage", Acore::StringFormat("health={} was_create={} loot_mode={} ysida={}",
            baron->GetMaxHealth(), _baseCreateHealth, uint32(baron->GetLootMode()), Ysida() ? 1 : 0));
    }

    void OnUpdate(BaronFight& fight, uint32 /*diff*/) override
    {
        uint64 const now = fight.FightMs();
        // The queue cancels an id when it starts it (CastQueue::Started), so the next one is queued here, after it.
        QueueCasts(fight);
        if (_execution && now >= _execution->resolveAt)
            ResolveExecution(fight);
        if (_lane && !_lane->locked)
        {
            if (Player* target = ObjectAccessor::GetPlayer(*fight.Baron(), _lane->target))
                if (target->IsAlive())
                    _lane->lastTarget = DungeonKit::PlaneOf(target);
            if (now >= _lane->lockAt)
                LockLane(fight);
        }
        if (_lane && _lane->locked && now >= _lane->landAt)
            LandCharge(fight);
    }

    std::optional<uint32> OnCast(BaronFight& fight, uint32 id) override
    {
        switch (id)
        {
            case CAST_EXECUTION:
                return StartExecution(fight);
            case CAST_DEATHCHARGER:
                return StartLane(fight, nullptr);
            default:
                return std::nullopt;
        }
    }

    uint32 DeathAndDecayLifeMs(BaronFight const& /*fight*/, uint32 /*baseMs*/) const override
    {
        return kRotLifeMs;     // HM4: 45 s
    }

    // HM4: him 1%, his undead 5% a second inside any rot (Death and Decay's or the trail's), once a second each.
    void OnRotTick(BaronFight& fight, RotInfo const& rot) override
    {
        uint64 const clock = fight.ClockMs();
        Creature* baron = fight.Baron();
        if (baron->IsAlive() && InRot(baron, rot) && _heal.Take(clock, baron->GetGUID().GetRawValue()))
            Heal(fight, baron, kRotHealBossPct, rot);
        for (Creature* servant : fight.Servants())
            if (InRot(servant, rot) && _heal.Take(clock, servant->GetGUID().GetRawValue()))
                Heal(fight, servant, kRotHealServantPct, rot);
    }

    void OnEnd(BaronFight& fight, bool died) override
    {
        Creature* baron = fight.Baron();
        if (baron->IsAlive())
            baron->RemoveAurasDueToSpell(SPELL_HM_PRICE_OF_DEFIANCE);
        baron->Dismount();
        if (!died && baron->IsAlive() && _baseCreateHealth)
            SetCreatureHealth(baron, _baseCreateHealth);
        if (_instance)
        {
            _instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_HM_CONDEMNED);
            _instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_HM_CONDEMNED_DOT);
            _instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_HM_DEATHCHARGER_MARK);
        }
        if (died)
            SettleYsidaOnKill(fight);
        else
            RestoreYsida(fight);
        _execution.reset();
        _lane.reset();
        fight.Log("hm-end", Acore::StringFormat("died={} misses={} fell={}", died ? 1 : 0, _misses,
            _ysidaFell ? 1 : 0));
    }

    // ---- `.dbtest strat ultimatum` entry points -----------------------------------------------------------------

    void TestExecute(BaronFight& fight)
    {
        _nextExecutionAt = fight.FightMs();
        fight.ScheduleCast(CAST_EXECUTION, 0, kCastPriority);
        _executionQueued = true;
    }

    bool TestCharge(BaronFight& fight, Player* target)
    {
        if (_lane)
            return false;
        if (target)
            return StartLane(fight, target).has_value();
        _nextChargeAt = fight.FightMs();
        fight.ScheduleCast(CAST_DEATHCHARGER, 0, kCastPriority);
        _chargeQueued = true;
        return true;
    }

    void TestMiss(BaronFight& fight)
    {
        if (Creature* ysida = Ysida())
            Miss(fight, ysida);
    }

    std::string TestState(BaronFight& fight)
    {
        uint64 const now = fight.FightMs();
        Creature* ysida = Ysida();
        std::string out = Acore::StringFormat("t={}ms health={}/{} next execution={}ms charge={}ms misses={} fell={} "
            "ysida={} execution={} lane={}", now, fight.Baron()->GetHealth(), fight.Baron()->GetMaxHealth(),
            _nextExecutionAt, _nextChargeAt, _misses, _ysidaFell ? 1 : 0,
            ysida ? (ysida->IsAlive() ? Acore::StringFormat("{}/{}", ysida->GetHealth(), ysida->GetMaxHealth())
                : std::string("dead")) : std::string("none"),
            _execution ? 1 : 0, _lane ? (_lane->locked ? 2 : 1) : 0);
        for (Player* player : fight.FightPlayers())
            if (uint32 stacks = DungeonKit::Stacks(player, SPELL_HM_CONDEMNED))
                out += Acore::StringFormat("\n  {} Condemned {}", player->GetName(), stacks);
        return out;
    }

private:
    struct Execution
    {
        uint64 resolveAt = 0;
        BossMechanics::MechanicHandle soak;
    };

    struct Lane
    {
        ObjectGuid target;
        Vec2 lastTarget;
        float length = 0.f;
        uint64 lockAt = 0;
        bool locked = false;
        uint64 landAt = 0;
        Position start;
        Position end;
    };

    Creature* Ysida() const
    {
        return _instance ? _instance->GetCreature(DATA_YSIDA_GUID) : nullptr;
    }

    // A cast that could not start now: queued again kCastRetryMs from now, off the cadence (its due time stays).
    void RetryCast(BaronFight& fight, uint32 id, bool& queued)
    {
        fight.ScheduleCast(id, kCastRetryMs, kCastPriority);
        queued = true;
    }

    // Queues the next execution and charge when the queue holds none of ours (they start from the queue).
    void QueueCasts(BaronFight& fight)
    {
        uint64 const now = fight.FightMs();
        if (!_executionQueued && !_ysidaFell && !_execution)
        {
            fight.ScheduleCast(CAST_EXECUTION, uint32(_nextExecutionAt > now ? _nextExecutionAt - now : 0),
                kCastPriority);
            _executionQueued = true;
        }
        if (!_chargeQueued && !_lane)
        {
            fight.ScheduleCast(CAST_DEATHCHARGER, uint32(_nextChargeAt > now ? _nextChargeAt - now : 0),
                kCastPriority);
            _chargeQueued = true;
        }
    }

    // ---- HM1 / HM2 the execution ----------------------------------------------------------------------------------

    std::optional<uint32> StartExecution(BaronFight& fight)
    {
        _executionQueued = false;
        uint64 const now = fight.FightMs();
        Creature* baron = fight.Baron();
        Creature* ysida = Ysida();
        if (_ysidaFell)
            return std::nullopt;     // no prisoner left: no more executions
        if (_execution)
        {
            RetryCast(fight, CAST_EXECUTION, _executionQueued);     // one still running (a test): this one waits
            return std::nullopt;
        }
        if (!ysida || !ysida->IsAlive() || !ysida->IsInWorld())
        {
            RetryCast(fight, CAST_EXECUTION, _executionQueued);
            fight.Log("hm-execution", "no prisoner (retry)");
            return std::nullopt;
        }
        // The cadence counts from when it was due, not from this start (a cast that waited never pushes the next).
        _nextExecutionAt = NextOnCadence(_nextExecutionAt, now, kExecutionEveryMs);

        // The bar and the beam: a channel at her (not triggered, so the bar shows); the hit is the script's at 3 s.
        SpellCastResult result = baron->CastSpell(ysida, SPELL_HM_EXECUTION, false);
        if (result != SPELL_CAST_OK)
            result = baron->CastSpell(ysida, SPELL_HM_EXECUTION, true);
        baron->AI()->Talk(EMOTE_BARON_EXECUTION);

        // The bots: a 2 yd line Soak from him to her (the length fixed now; both hold still), one body, the fewest
        // Condemned stacks first. Telegraph only: the script deals the blow to the first player on the line.
        BossMechanics::Ordering fewest;
        fewest.auraSpell = SPELL_HM_CONDEMNED;
        fewest.ascending = true;
        MechanicRef ref = Mechanic::Soak(baron, BossMechanics::Shapes::Line(BossMechanics::Anchor(baron),
            BossMechanics::Anchor(ysida), kExecutionLineWidth), 1, Milliseconds(kExecutionCastMs));
        ref.Order(fewest).Tag(TAG_EXECUTION);
        Execution exec;
        exec.resolveAt = now + kExecutionCastMs;
        exec.soak = ref.Handle();
        fight.Track(exec.soak);
        _execution = exec;
        fight.Log("hm-execution", Acore::StringFormat("start cast={} line={:.1f}yd misses={}", uint32(result),
            baron->GetDistance2d(ysida), _misses));
        return kExecutionCastMs;
    }

    void ResolveExecution(BaronFight& fight)
    {
        _execution.reset();
        Creature* baron = fight.Baron();
        Creature* ysida = Ysida();
        if (!ysida || !ysida->IsAlive())
        {
            fight.Log("hm-execution", "resolve: no prisoner");
            return;
        }
        std::vector<Player*> const players = fight.FightPlayers();
        std::vector<Vec2> points;
        points.reserve(players.size());
        for (Player* p : players)
            points.push_back(DungeonKit::PlaneOf(p));
        std::optional<std::size_t> const first = FirstOnLine(DungeonKit::PlaneOf(baron), DungeonKit::PlaneOf(ysida),
            kExecutionLineWidth, points);
        if (!first)
        {
            Miss(fight, ysida);
            return;
        }
        Player* taker = players[*first];
        uint32 const stacks = DungeonKit::Stacks(taker, SPELL_HM_CONDEMNED);
        // The blow reads the stacks at launch (spell_strat_ultimatum_execution), then the taker gains one.
        baron->CastSpell(taker, SPELL_HM_EXECUTION_HIT, true);
        uint32 const after = DungeonKit::AddStacks(taker, SPELL_HM_CONDEMNED, 1, baron, kCondemnedMaxStacks);
        baron->CastSpell(taker, SPELL_HM_CONDEMNED_DOT, true);
        fight.Log("hm-execution", Acore::StringFormat("taken by={} stacks={}->{} pct={:.0f}", taker->GetName(),
            stacks, after, ExecutionPct(stacks)));
    }

    // Nobody on the line: Ysida loses a third of her life; the third miss and she falls.
    void Miss(BaronFight& fight, Creature* ysida)
    {
        Creature* baron = fight.Baron();
        ++_misses;
        ysida->SetRegeneratingHealth(false);    // she may have been missing at the pull (OnEngage)
        baron->CastSpell(ysida, SPELL_HM_EXECUTION_YSIDA, true);
        if (YsidaFalls(_misses))
        {
            Fall(fight, ysida);
            return;
        }
        uint32 const left = std::max<uint32>(1, uint32(float(ysida->GetMaxHealth()) * YsidaLifeShare(_misses)));
        ysida->SetHealth(left);
        fight.Log("hm-execution", Acore::StringFormat("missed misses={} ysida={}/{}", _misses, ysida->GetHealth(),
            ysida->GetMaxHealth()));
    }

    // The third miss: she falls. She is hidden, alive (R-1-B B-2): never killed mid-attempt, so a wipe shows her again
    // where she stood (no corpse to keep, no respawn queue) and the instance's own execution at the clock's end still
    // finds her; a kill settles her (SettleYsidaOnKill). Her cage opens, Ysida, Risen rises there and he gains the
    // Price.
    void Fall(BaronFight& fight, Creature* ysida)
    {
        Creature* baron = fight.Baron();
        _ysidaFell = true;
        if (_executionQueued)
        {
            fight.CancelCast(CAST_EXECUTION);
            _executionQueued = false;
        }
        Position const spot = ysida->GetPosition();
        ysida->SetHealth(1);
        ysida->SetVisible(false);
        if (_instance)
            if (GameObject* cage = _instance->GetGameObject(DATA_YSIDA_CAGE_GUID))
                cage->SetGoState(GO_STATE_ACTIVE);

        Creature* risen = baron->SummonCreature(NPC_ST_YSIDA_RISEN, spot, TEMPSUMMON_CORPSE_TIMED_DESPAWN, 5000);
        if (risen)
        {
            SetCreatureHealth(risen, kRisenHealth);
            fight.TrackServant(risen);
        }
        baron->CastSpell(baron, SPELL_HM_PRICE_OF_DEFIANCE, true);
        baron->AI()->Talk(YELL_BARON_YSIDA_RISES);
        fight.Log("hm-ysida-falls", Acore::StringFormat("risen={} at=({:.1f},{:.1f}) price={}", risen ? 1 : 0,
            spot.GetPositionX(), spot.GetPositionY(), baron->HasAura(SPELL_HM_PRICE_OF_DEFIANCE) ? 1 : 0));
    }

    // ---- HM3 the Deathcharger ------------------------------------------------------------------------------------

    // `forced`: that player (a test), else the farthest non-tank (a solo tank still gets it).
    std::optional<uint32> StartLane(BaronFight& fight, Player* forced)
    {
        _chargeQueued = false;
        uint64 const now = fight.FightMs();
        Creature* baron = fight.Baron();
        if (_lane)
        {
            RetryCast(fight, CAST_DEATHCHARGER, _chargeQueued);     // one still running (a test): this one waits
            return std::nullopt;
        }
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;
            rule.farthest = true;
            target = DungeonKit::PickPlayer(baron, rule);
        }
        if (!target)
        {
            RetryCast(fight, CAST_DEATHCHARGER, _chargeQueued);
            fight.Log("hm-deathcharger", "no target (retry)");
            return std::nullopt;
        }
        if (!forced)
            _nextChargeAt = NextOnCadence(_nextChargeAt, now, kChargeEveryMs);

        float const dist = baron->GetDistance2d(target);
        Lane lane;
        lane.target = target->GetGUID();
        lane.lastTarget = DungeonKit::PlaneOf(target);
        lane.length = LaneLength(dist);
        lane.lockAt = now + kLaneWarnMs;

        baron->CastSpell(target, SPELL_HM_DEATHCHARGER_MARK, true);
        baron->AI()->Talk(EMOTE_BARON_DEATHCHARGER, target);

        // The lane: a 6 yd line from him aimed at the target (it follows them; its length fixed now), everyone but
        // the target eligible. Telegraph only: the hit rides with the charge (LockLane). The target's bot carries it
        // by X2's drop spot rule (the room's edge, away from the group, off the piles); the others' bots leave it
        // before the lock, so they are clear when he passes.
        BossMechanics::ZoneSpec spec{ BossMechanics::Anchor(baron),
            BossMechanics::Shape::Line(lane.length, kLaneWidth), BossMechanics::Anchor(target) };
        MechanicRef ref = Mechanic::Zone(baron, spec, Milliseconds(kLaneWarnMs));
        ref.Eligible(Others(fight, target->GetGUID())).DropSpot(fight.RoomDropRule(true)).Tag(TAG_LANE_WARN);
        fight.Track(ref.Handle());
        _lane = lane;
        fight.Log("hm-deathcharger", Acore::StringFormat("target={} dist={:.1f} lane={:.1f} piles={}",
            target->GetName(), dist, lane.length, fight.Piles().size()));
        return kLaneWarnMs + ChargeTravelMs(lane.length) + kChargeHoldExtraMs;
    }

    // Everyone in the fight but `target` (a lane's eligibility).
    BossMechanics::Eligibility Others(BaronFight& fight, ObjectGuid target)
    {
        BossMechanics::Eligibility others;
        for (Player* p : fight.FightPlayers())
            if (p->GetGUID() != target)
                others.carriers.insert(p->GetGUID());
        if (others.carriers.empty())
            others.carriers.insert(ObjectGuid::Empty);     // nobody else: an empty set would mean everyone
        return others;
    }

    // The lock: he charges down the drawn lane toward where the target stands, clamped to where he may stand.
    void LockLane(BaronFight& fight)
    {
        Creature* baron = fight.Baron();
        Lane& lane = *_lane;
        lane.locked = true;
        Vec2 const start = DungeonKit::PlaneOf(baron);
        Vec2 const wanted = ChargeEnd(start, lane.lastTarget, lane.length);
        float const z = baron->GetPositionZ();
        Vec2 const end = ClampCharge(start, wanted, [&fight, z](Vec2 p)
        {
            return fight.CanStandAt(Position(p.x, p.y, z, 0.f));
        });
        float const run = DungeonKit::Distance(start, end);
        lane.start = Position(start.x, start.y, z, 0.f);
        lane.end = Position(end.x, end.y, FloorZ(baron, end.x, end.y, z), 0.f);
        lane.landAt = fight.FightMs() + ChargeTravelMs(run);

        Player* target = ObjectAccessor::GetPlayer(*baron, lane.target);
        if (target && target->IsAlive() && target->IsInWorld())
            baron->CastSpell(target, SPELL_HM_TRAMPLE, true);     // not avoidable; its speed lands it as he does
        float hitLength = 0.f;
        if (run >= kLaneProbeStepYd)
        {
            baron->GetMotionMaster()->MoveCharge(lane.end.GetPositionX(), lane.end.GetPositionY(),
                lane.end.GetPositionZ(), kChargeSpeed);
            hitLength = LaneHitLength(run, lane.length);
            LaneHit(fight, lane, Position(start.x, start.y, z, 0.f), LaneFacing(start, lane.lastTarget), hitLength);
        }
        fight.Log("hm-charge", Acore::StringFormat("target={} from=({:.1f},{:.1f}) to=({:.1f},{:.1f}) run={:.1f} "
            "wanted={:.1f} clamped={} hit={:.1f}", target ? target->GetName() : std::string("gone"), start.x, start.y,
            end.x, end.y, run, DungeonKit::Distance(start, wanted), DungeonKit::Distance(end, wanted) > 0.05f ? 1 : 0,
            hitLength));
    }

    // The lane's hit (R-1-B B-5, ORCH ruling): it lands as the charge reaches each player, not at the lock. A static
    // line from his start along the charge, swept at his charge speed (a registry projectile line: the body is the
    // lane's width), as far as he runs plus the lane's reach past his stop; 50% Physical and Weakened on everyone but
    // the target (who takes 206727), 206728's hit flash on each.
    void LaneHit(BaronFight& fight, Lane const& lane, Position const& from, float facing, float length)
    {
        Creature* baron = fight.Baron();
        MechanicRef ref = Mechanic::Line(baron, BossMechanics::Anchor(from), facing, length, kLaneWidth,
            Milliseconds(0));
        ref.Projectile(kChargeSpeed).Damage(kLaneHitPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_HM_LANE).Weakened()
            .Eligible(Others(fight, lane.target)).Tag(TAG_LANE);
        fight.Track(ref.Handle());
    }

    // He landed: the lane rots for 20 s (rot stalkers every 5 yd and the trail's persistent line), then he goes back
    // to his threat target (the charge's movement ends and his chase resumes).
    void LandCharge(BaronFight& fight)
    {
        Creature* baron = fight.Baron();
        Lane const lane = *_lane;
        _lane.reset();
        Vec2 const from{ lane.start.GetPositionX(), lane.start.GetPositionY() };
        Vec2 const to{ lane.end.GetPositionX(), lane.end.GetPositionY() };
        std::vector<Vec2> const spots = TrailSpots(from, to);
        uint32 raised = 0;
        uint32 const pilesBefore = uint32(fight.Piles().size());
        for (Vec2 const& s : spots)
        {
            RotSpec rot;
            rot.at = Position(s.x, s.y, lane.start.GetPositionZ(), 0.f);
            rot.radius = kTrailRadius;
            rot.life = Milliseconds(kTrailLifeMs);
            rot.tickPct = 0.f;              // the trail's own line below owns the damage
            rot.lookSpell = SPELL_HM_TRAIL_LOOK;
            rot.raises = true;              // every pile it crosses rises (heroic: S14 raises at the spawn and each s)
            rot.tag = TAG_TRAIL_ROT;
            fight.SpawnRot(rot);
        }
        raised = pilesBefore - std::min<uint32>(pilesBefore, uint32(fight.Piles().size()));
        if (!spots.empty())
        {
            DungeonKit::LingerSpec linger;
            linger.duration = Milliseconds(kTrailLifeMs - kTrailGraceMs);
            linger.tick = Milliseconds(kTrailGraceMs);
            linger.pct = kTrailPct;
            linger.school = SPELL_SCHOOL_SHADOW;
            linger.spellId = SPELL_HM_TRAIL;
            linger.slow = false;
            linger.tag = TAG_TRAIL;
            MechanicRef ref = DungeonKit::Linger(baron, BossMechanics::Shapes::Line(BossMechanics::Anchor(lane.start),
                BossMechanics::Anchor(lane.end), kLaneWidth), linger);
            ref.WeakenedOncePerPlayer();
            fight.Track(ref.Handle());
        }
        fight.Log("hm-trail", Acore::StringFormat("spots={} length={:.1f} raised={}", spots.size(),
            DungeonKit::Distance(from, to), raised));
    }

    // ---- HM4 the rot heal --------------------------------------------------------------------------------------

    void Heal(BaronFight& fight, Creature* unit, float pct, RotInfo const& rot)
    {
        uint32 const amount = RotHealAmount(unit->GetMaxHealth(), pct);
        if (!amount || unit->GetHealth() >= unit->GetMaxHealth())
            return;
        unit->CastCustomSpell(SPELL_HM_ROT_HEAL, SPELLVALUE_BASE_POINT0, int32(amount), unit, true);
        fight.Log("hm-rot-heal", Acore::StringFormat("unit={} amount={} tag={}", unit->GetEntry(), amount, rot.tag));
    }

    // ---- Ysida at the fight's end --------------------------------------------------------------------------------

    // His death (S14 calls OnEnd before it frees a living Ysida and before BossAI::JustDied): a fallen Ysida dies now,
    // so S14 does not free her and the instance finds her dead (the exit gate), and her body goes (no wipe will need
    // it back). A living one keeps her life for S14's free. Her regeneration is her template's again.
    void SettleYsidaOnKill(BaronFight& fight)
    {
        Creature* ysida = Ysida();
        if (ysida)
        {
            ysida->SetRegeneratingHealth(ysida->GetCreatureTemplate()->RegenHealth);
            if (_ysidaFell)
            {
                if (ysida->IsAlive())
                    ysida->KillSelf();      // he is already dead: no killer
                ysida->DespawnOrUnsummon();
            }
        }
        fight.Log("hm-ysida-settled", Acore::StringFormat("found={} fell={}", ysida ? 1 : 0, _ysidaFell ? 1 : 0));
    }

    // A wipe (ruling 60): a fallen Ysida shows again in her closed cage at full health (she was only hidden); Ysida,
    // Risen is S14's to despawn. A dead Ysida is not this attempt's doing (the hard mode never kills her before his
    // death): she stays dead.
    void RestoreYsida(BaronFight& fight)
    {
        Creature* ysida = Ysida();
        if (ysida)
        {
            ysida->SetRegeneratingHealth(ysida->GetCreatureTemplate()->RegenHealth);
            if (ysida->IsAlive())
            {
                ysida->SetVisible(true);
                ysida->SetHealth(ysida->GetMaxHealth());
            }
        }
        if (_ysidaFell && _instance)
            if (GameObject* cage = _instance->GetGameObject(DATA_YSIDA_CAGE_GUID))
                cage->SetGoState(GO_STATE_READY);
        fight.Log("hm-ysida-restored", Acore::StringFormat("found={} alive={} fell={}", ysida ? 1 : 0,
            ysida && ysida->IsAlive() ? 1 : 0, _ysidaFell ? 1 : 0));
    }

    InstanceScript* _instance = nullptr;
    uint32 _baseCreateHealth = 0;
    uint64 _nextExecutionAt = 0;
    uint64 _nextChargeAt = 0;
    bool _executionQueued = false;
    bool _chargeQueued = false;
    uint32 _misses = 0;
    bool _ysidaFell = false;
    std::optional<Execution> _execution;
    std::optional<Lane> _lane;
    RotHealBook _heal;
};

// -------------------------------------------------------------------------------------------------------------------
// Ysida, Risen 300589
// -------------------------------------------------------------------------------------------------------------------

// She fixes on the nearest player every second (ST: "attacks the nearest player"), strikes her victim every 2 s
// (206733, 3% of the reference row; no auto attack) and throws a Death Coil (206732, 15%) at a random player within
// 30 yd every 10 s. Stun immune (1972). The Baron's servant: summoned by him (his fight, his cleanup), counted by
// Unholy Aura and healed by the hard mode's rot.
struct npc_st_ysida_risen : public ScriptedAI
{
    explicit npc_st_ysida_risen(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _swingMs = kRisenFirstSwingMs;
        _coilMs = kDeathCoilFirstMs;
        _retargetMs = 0;
    }

    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        DoCastSelf(SPELL_HM_RISEN_LOOK, true);
        Retarget();
    }

    void UpdateAI(uint32 diff) override
    {
        _retargetMs = _retargetMs > diff ? _retargetMs - diff : 0;
        if (!_retargetMs)
        {
            Retarget();
            _retargetMs = kRisenRetargetMs;
        }
        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING | UNIT_STATE_LOST_CONTROL))
            return;

        _coilMs = _coilMs > diff ? _coilMs - diff : 0;
        if (!_coilMs)
        {
            _coilMs = kDeathCoilEveryMs;
            std::vector<Player*> inRange;
            for (Player* p : LivingPlayers(me->GetMap()))
                if (me->IsWithinDist(p, kDeathCoilRangeYd) && me->IsInCombatWith(p))
                    inRange.push_back(p);
            if (!inRange.empty())
            {
                me->CastSpell(Acore::Containers::SelectRandomContainerElement(inRange), SPELL_HM_DEATH_COIL, true);
                return;
            }
        }

        _swingMs = _swingMs > diff ? _swingMs - diff : 0;
        if (_swingMs)
            return;
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return;     // the swing waits for reach
        me->CastSpell(victim, SPELL_HM_RISEN_STRIKE, true);
        _swingMs = kRisenSwingMs;
    }

private:
    // The nearest living player within 100 yd: on her threat list, and fixed on.
    void Retarget()
    {
        Player* nearest = nullptr;
        float best = std::numeric_limits<float>::max();
        for (Player* p : LivingPlayers(me->GetMap()))
        {
            float const d = me->GetDistance(p);
            if (d <= kNearestPlayerYd && d < best)
            {
                best = d;
                nearest = p;
            }
        }
        if (!nearest)
            return;
        me->AddThreat(nearest, 0.f);
        me->GetThreatMgr().FixateTarget(nearest);
        if (me->GetVictim() != nearest)
            AttackStart(nearest);
    }

    uint32 _swingMs = kRisenFirstSwingMs;
    uint32 _coilMs = kDeathCoilFirstMs;
    uint32 _retargetMs = 0;
};

// HM1 the blow (206721): 30% of the reference row (the tank row on the tank) times (1 + the target's Condemned stacks),
// set at launch so the target's own defensives count (the spell ignores the caster's modifiers).
class spell_strat_ultimatum_execution : public SpellScript
{
    PrepareSpellScript(spell_strat_ultimatum_execution);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;
        float const pct = ExecutionPct(DungeonKit::Stacks(target, SPELL_HM_CONDEMNED));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, target, pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_strat_ultimatum_execution::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest strat ultimatum`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    // The pull's hard mode and the Baron's fight, or nullptr (an error said).
    UltimatumFight* FindFight(ChatHandler* handler, BaronFight*& fight)
    {
        fight = nullptr;
        Creature* baron = StratTest::FindBoss(handler, NPC_BARON);
        if (!baron)
            return nullptr;
        fight = baron->IsAIEnabled ? dynamic_cast<BaronFight*>(baron->AI()) : nullptr;
        if (!fight)
        {
            handler->SendErrorMessage("{}", "The Baron is not running boss_baron_rivendare_rework.");
            return nullptr;
        }
        auto* hm = dynamic_cast<UltimatumFight*>(fight->ActiveHardMode());
        if (!hm)
            handler->SendErrorMessage("{}", "No Ultimatum on this pull (heroic, DATA_ULTIMATUM lit, then pull him; "
                "`.dbtest strat instance ultimatum 1` lights it while the clock runs).");
        return hm;
    }

    Player* SelectedPlayer(ChatHandler* handler)
    {
        return handler->getSelectedPlayer();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!StratTest::RequireStratholme(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        handler->PSendSysMessage("ultimatum: flag {}, kill {}, boss {}, clock {} min",
            instance->GetData(DATA_ULTIMATUM), DungeonTest::StateName(instance->GetBossState(BOSS_ULTIMATUM)),
            DungeonTest::StateName(instance->GetBossState(BOSS_BARON)), instance->GetData(DATA_BARON_RUN_MINUTES));
        return true;
    }

    // `.dbtest strat ultimatum state`: the pull's executions, lanes, Ysida and every Condemned.
    bool HandleState(ChatHandler* handler)
    {
        BaronFight* fight = nullptr;
        UltimatumFight* hm = FindFight(handler, fight);
        if (!hm)
            return false;
        handler->PSendSysMessage("Ultimatum: {}", hm->TestState(*fight));
        return true;
    }

    // `.dbtest strat ultimatum execute`: an execution now (through his cast queue: it waits for a running cast).
    bool HandleExecute(ChatHandler* handler)
    {
        BaronFight* fight = nullptr;
        UltimatumFight* hm = FindFight(handler, fight);
        if (!hm)
            return false;
        hm->TestExecute(*fight);
        handler->PSendSysMessage("Ultimatum: an execution is queued (HM1).");
        return true;
    }

    // `.dbtest strat ultimatum charge`: a Deathcharger lane now, on the selected player or the farthest non-tank.
    bool HandleCharge(ChatHandler* handler)
    {
        BaronFight* fight = nullptr;
        UltimatumFight* hm = FindFight(handler, fight);
        if (!hm)
            return false;
        Player* target = SelectedPlayer(handler);
        bool const ok = hm->TestCharge(*fight, target);
        handler->PSendSysMessage("Ultimatum: {}", ok ? (target ? "a lane on the selected player (HM3)."
            : "a lane is queued (HM3).") : "a lane is already running.");
        return true;
    }

    // `.dbtest strat ultimatum miss`: one missed execution now (Ysida loses a third; the third: she falls).
    bool HandleMiss(ChatHandler* handler)
    {
        BaronFight* fight = nullptr;
        UltimatumFight* hm = FindFight(handler, fight);
        if (!hm)
            return false;
        hm->TestMiss(*fight);
        handler->PSendSysMessage("Ultimatum: {}", hm->TestState(*fight));
        return true;
    }

    ChatCommandTable const& UltimatumTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "execute", HandleExecute, SEC_GAMEMASTER, Console::No },
            { "charge",  HandleCharge,  SEC_GAMEMASTER, Console::No },
            { "miss",    HandleMiss,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_strat_baron_hard_mode()
{
    StratBaron::RegisterBaronHardMode([](Creature* /*baron*/) { return std::make_unique<UltimatumFight>(); });
    RegisterDungeonReworkCreatureAI(npc_st_ysida_risen, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_strat_ultimatum_execution);
    StratTest::RegisterBoss("ultimatum", UltimatumTestCommands());
}
