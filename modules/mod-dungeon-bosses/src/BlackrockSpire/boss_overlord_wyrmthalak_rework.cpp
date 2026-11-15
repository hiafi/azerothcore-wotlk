/*
 * mod-dungeon-bosses, Blackrock Spire B8: Overlord Wyrmthalak (9568), normal and heroic, the Lower Spire's final boss.
 * Build spec SP 2436-2521 (design SP 2175-2435: theme A "Overlord of the Three Tribes", rulings 47-49; the tank swap at
 * 10, rulings 63-64); handoff section 3.4 rows WT, section 3.5 row B8, section 3.6, section 3.8 (NM 8, the ledge).
 * Replaces the stock boss_overlord_wyrmthalak (still registered, unbound by apps/dbc-tools
 * source/npcs/blackrock_spire/wyrmthalak.py): Demoralizing Shout, both Knock Aways and the 51% summons are retired
 * (the stock pair 9216 / 9268 stays trash); Cleave stays.
 *
 *   WT1  Black Dragonfire  8 s, then every 15 s (the cast queue): a 2 s rear-up bar (line 1) and a 60 degree, 25 yd
 *                          Frontal (the tank exempt): 35% / 45% Fire, Weakened.
 *   WT1b The burn          heroic: the breath's cone keeps burning 8 s (20 yd), its first tick 3 s after it appears,
 *                          5% a second, the tank too; black flame patches show it.
 *   WT2  Tail Swipe        a persistent 120 degree, 15 yd rear cone on him (the bots keep off his back the whole
 *                          time), resolved at 5 s and every 12 s: 20% / 25%, Weakened, a 10 yd knockback (off the
 *                          ledge along its open edge).
 *   WT3  Cleave            stock 20691, 6 s then every 7 s, on his victim in reach.
 *   WT4  Orders            10 s, then every 30 s (heroic 25 s): the next tribe in turn (Spirestone, Smolderthorn,
 *                          Bloodaxe; lines 2-4). A tribe's first call brings its champion up the ramp (about 5 s);
 *                          while the champion lives the tribe answers (WT5-WT7), once it is dead its orders go
 *                          unanswered (line 5).
 *   WT5  Boulders          3 / 6 circles of 4 yd at random players' spots, 2.5 s, 25% / 30%, Weakened; the boulders fly
 *                          from a thrower in the lower hall.
 *   WT6  Axe Volley        2 / 4 random non-tanks marked 4 s, then the axes land: everyone else within 6 yd of a marked
 *                          player, 25% / 30%, Weakened (a RunOut); the axes fly from a thrower on the ramp.
 *   WT7  Worg Riders       2 / 4 riders paw at the ramp head 3 s, then charge 4 yd lanes through random players' spots
 *                          across the ledge: 30% / 35%, Weakened, knocked 5 yd aside; they ride back down.
 *   WT8  Overlord's Fury   heroic (not the hard mode): each champion's death, a permanent stack on him (+15% damage,
 *                          +10% attack speed).
 *   WT18 Mortal Strike     10 players only: 8 s, then every 8 s on his victim, 30% of the tank row and a Mortal Wounds
 *                          stack (-10% healing taken, 15 s, refreshed, no cap); the bots' taunt swap at 3 (the user
 *                          ruling: a tank taunts once its own stacks are gone; 15 s < 2 x 8 s, WyrmthalakLogic.h).
 *   Leash                  WyrmthalakArena() with LeashOptions (no grips).
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler that a cast bar pauses. The hard mode (WP-B9, the
 * war horn) fights on this AI through WyrmthalakFight.h (WyrmthalakHardMode hooks; this class is its WyrmthalakFight).
 * Every firing logs one INFO line "brs wyrmthalak <mechanic> ..." (module.dungeonbosses); `.dbtest brs wyrmthalak
 * <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "DungeonKitFlow.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WyrmthalakFight.h"
#include "WyrmthalakLogic.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsWyrmthalak;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "wyrmthalak";

    // Registry tags (bookkeeping; per encounter).
    enum WyrmthalakTags : uint32
    {
        TAG_WT_BREATH   = 1,
        TAG_WT_BURN     = 2,
        TAG_WT_TAIL     = 3,
        TAG_WT_BOULDER  = 4,
        TAG_WT_AXES     = 5,
        TAG_WT_RIDER    = 6,
    };

    // Movement ids of his adds.
    enum WyrmthalakPoints : uint32
    {
        POINT_CHAMPION_LANDING  = 1,
        POINT_RIDER_END         = 2,
        POINT_RIDER_HOME        = 3,
    };

    uint32 constexpr kRiderMountDisplay = 14334;    // PvPRidingDireWolf (V-1: DISPLAY_RIDING_DIRE_WOLF)
    float constexpr kFloorProbeUpYd = 2.f;
    float constexpr kFloorMaxDropYd = 4.f;
    float constexpr kChampionOpeningThreat = 100.f;

    WyrmthalakHardModeFactory& HardModeFactory()
    {
        static WyrmthalakHardModeFactory factory;
        return factory;
    }

    // The floor under a point within kFloorMaxDropYd; nullopt over a drop (the open edge) or off the mesh.
    std::optional<float> FloorNear(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + kFloorProbeUpYd);
        if (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > kFloorMaxDropYd)
            return std::nullopt;
        return floor;
    }

    Position At(Point3 const& p, float o = 0.f)
    {
        return Position(p.x, p.y, p.z, o);
    }

    Vec2 XY(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }
}

void BrsWyrmthalak::RegisterWyrmthalakHardMode(WyrmthalakHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

std::unique_ptr<WyrmthalakHardMode> BrsWyrmthalak::CreateWyrmthalakHardMode(Creature* boss)
{
    WyrmthalakHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(boss) : nullptr;
}

// Overlord Wyrmthalak 9568
struct boss_overlord_wyrmthalak_rework : public BossAI, public WyrmthalakFight
{
    explicit boss_overlord_wyrmthalak_rework(Creature* creature)
        : BossAI(creature, BOSS_WYRMTHALAK), _arena(WyrmthalakArena(), LeashOptions(kBossLogName)),
          _queue(kCastSpacingMs) { }

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

        Cleanup(false);     // a `.dbtest brs wyrmthalak` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        bool hardMode = _heroic && instance && instance->GetData(DATA_WAR_HORN) != 0;
        if (hardMode)
        {
            // The handler first: a lit horn with no handler registered runs the normal heroic, without the hard
            // mode's loot bits (R-1-B n6).
            _hardMode = CreateWyrmthalakHardMode(me);
            if (!_hardMode)
            {
                LOG_WARN("module", "brs wyrmthalak: the war horn is lit but no hard mode handler is registered; "
                    "the pull runs as a normal heroic");
                hardMode = false;
            }
        }
        _players = OnBossPull(me, kBossLogName, hardMode);
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_WYRMTHALAK;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        _nextOrderAt = kOrderFirstMs;
        _nextCleaveAt = kCleaveFirstMs;
        _nextMortalAt = kMortalStrikeFirstMs;
        _queue.Schedule(CAST_BREATH, kBreathFirstMs, kBreathPriority);
        RegisterTailSwipe();
        Talk(YELL_WT_PULL);

        Log("engage", Acore::StringFormat("players={} heroic={} hardmode={} handler={} tankswap={}", _players,
            _heroic ? 1 : 0, hardMode ? 1 : 0, _hardMode ? 1 : 0, DungeonKit::Flex::TankSwapOn(_players) ? 1 : 0));
        if (_hardMode)
        {
            _hardMode->OnEngage(*this);
            // The kit's `pull` line above logs his health before the hard mode raises it (R-1-B n5).
            Log("pull-health", Acore::StringFormat("health={} hardmode=1", me->GetMaxHealth()));
        }
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_WT_DEATH);
        Cleanup(true);      // champions, riders and throwers go with him (stock note 2: the adds outlived him)
        BossAI::JustDied(killer);
        Log("death");
    }

    // Everything he summons is his fight's (despawned with it); champions join the fight when they reach the ledge.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (!summon)
            return;
        if (std::optional<Tribe> const tribe = TribeOfEntry(summon->GetEntry()))
            ChampionDied(*tribe, summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    // WT14 (B9): Cleave counts as one of his abilities.
    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (_hardMode && _engaged && spell && spell->Id == SPELL_WT_CLEAVE && target && target->IsPlayer())
            _hardMode->OnAbilityHit(*this, Ability::Cleave, target);
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.dbtest` missile or rider still flies.
        _clockMs += diff;
        RunPending();

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _now += diff;
        PruneBurns();
        if (_hardMode)
        {
            _hardMode->OnUpdate(*this, diff);
            if (!_engaged || !me->IsAlive())
                return;     // the hook ended the fight
        }

        if (_now >= _nextOrderAt)
            Order();
        if (DungeonKit::Flex::TankSwapOn(_players) && _now >= _nextMortalAt)
            MortalStrike();

        if (Busy())
            return;
        RunQueue();
        if (Busy())
            return;
        Cleave();
        DoMeleeAttackIfReady();
    }

    // ---- WyrmthalakFight (the hard mode's view of the pull, WyrmthalakFight.h) --------------------------------------

    Creature* Boss() override
    {
        return me;
    }

    bool Heroic() const override
    {
        return _heroic;
    }

    uint8 Players() const override
    {
        return _players;
    }

    WyrmthalakHardMode* ActiveHardMode() override
    {
        return _hardMode.get();
    }

    uint64 FightMs() const override
    {
        return _now;
    }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !player->IsInWorld())
                continue;
            if (!me->IsInCombatWith(player) && !_arena.Contains(player))
                continue;
            out.push_back(player);
        }
        return out;
    }

    Creature* Champion(Tribe tribe) override
    {
        ChampionState const& c = _champions[Index(tribe)];
        if (c.dead || c.guid.IsEmpty())
            return nullptr;
        Creature* champion = ObjectAccessor::GetCreature(*me, c.guid);
        return champion && champion->IsAlive() ? champion : nullptr;
    }

    bool ChampionCalled(Tribe tribe) const override
    {
        return _champions[Index(tribe)].called;
    }

    bool ChampionDead(Tribe tribe) const override
    {
        return _champions[Index(tribe)].dead;
    }

    Creature* SummonChampion(Tribe tribe) override
    {
        ChampionState& c = _champions[Index(tribe)];
        if (c.called)
            return Champion(tribe);
        float const offset = (float(Index(tribe)) - 1.f) * kChampionStartSpread;
        Position const start(kChampionStart.x + offset, kChampionStart.y, kChampionStart.z,
            DungeonKit::BearingTo(kChampionStart.XY(), kChampionLanding.XY()));
        Creature* champion = me->SummonCreature(ChampionEntry(tribe), start, TEMPSUMMON_MANUAL_DESPAWN);
        if (!champion)
        {
            Log("champion", Acore::StringFormat("tribe={} summon failed", TribeName(tribe)));
            return nullptr;
        }
        c.called = true;
        c.guid = champion->GetGUID();
        champion->SetReactState(REACT_PASSIVE);
        float const landZ = FloorNear(me, kChampionLanding.x, kChampionLanding.y, kChampionLanding.z)
            .value_or(kChampionLanding.z);
        champion->GetMotionMaster()->MovePoint(POINT_CHAMPION_LANDING, kChampionLanding.x + offset * 0.5f,
            kChampionLanding.y, landZ);
        Mechanic::TrackUnit(me, champion);      // the taunt swap's assist-tank entries see it (TS report)
        Log("champion", Acore::StringFormat("tribe={} up the ramp", TribeName(tribe)));
        if (_hardMode && _engaged)
            _hardMode->OnChampionSummoned(*this, tribe, champion);
        return champion;
    }

    void IssueOrder(std::vector<Tribe> const& tribes, char const* why) override
    {
        for (Tribe tribe : tribes)
        {
            ChampionState const& c = _champions[Index(tribe)];
            if (c.dead)
            {
                Talk(EMOTE_WT_UNANSWERED);
                Log("order", Acore::StringFormat("tribe={} why={} unanswered", TribeName(tribe), why));
                continue;
            }
            Talk(OrderText(tribe));
            bool const first = !c.called;
            if (first)
                SummonChampion(tribe);
            Log("order", Acore::StringFormat("tribe={} why={} first={}", TribeName(tribe), why, first ? 1 : 0));
            Answer(tribe);
        }
    }

    std::vector<Position> Boulders(uint8 count) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // random players: the tank too
        return BouldersAt(DungeonKit::PickPlayers(me, rule, count));
    }

    GuidSet AxeVolley(uint8 count) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        return AxeVolleyOn(DungeonKit::PickPlayers(me, rule, count));
    }

    std::vector<ObjectGuid> WorgRiders(uint8 count) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        return WorgRidersThrough(DungeonKit::PickPlayers(me, rule, count));
    }

    MechanicHandle SpawnBurn(Position const& apex, BurnSpec const& spec) override
    {
        if (spec.length <= 0.f || spec.lifeMs <= spec.graceMs)
            return {};
        Position const at(apex.GetPositionX(), apex.GetPositionY(), apex.GetPositionZ(), apex.GetOrientation());
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(at, spec.angleDeg, spec.length),
            Milliseconds(spec.graceMs));
        ref.Persistent(Milliseconds(spec.lifeMs - spec.graceMs), Milliseconds(kBurnTickMs)).Damage(kBurnPct)
            .TankDamage(kBurnPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_WT_DRAGONFIRE_BURN).NoFillTimer()
            .Within(LedgeBounds()).Tag(TAG_WT_BURN);
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return {};
        Track(handle);

        Burn burn;
        burn.info.apex = at;
        burn.info.length = spec.length;
        burn.info.angleDeg = spec.angleDeg;
        burn.info.bornMs = _now;
        burn.info.untilMs = _now + spec.lifeMs;
        burn.info.handle = handle;
        for (Vec2 const& p : BurnPatchPoints(XY(at), at.GetOrientation(), spec.length))
        {
            ObjectGuid const stalker = SpawnFlamePatch(Position(p.x, p.y, at.GetPositionZ(), 0.f), spec.lifeMs);
            if (!stalker.IsEmpty())
                burn.stalkers.push_back(stalker);
        }
        std::size_t const patches = burn.stalkers.size();
        _burns.push_back(std::move(burn));
        if (spec.maxAlive && _burns.size() > spec.maxAlive)
        {
            EndBurn(_burns.front());
            _burns.erase(_burns.begin());
        }
        Log("burn", Acore::StringFormat("at=({:.1f},{:.1f}) o={:.2f} len={:.0f} life={}ms patches={} alive={}",
            at.GetPositionX(), at.GetPositionY(), at.GetOrientation(), spec.length, spec.lifeMs, patches,
            _burns.size()));
        return handle;
    }

    std::vector<BurnInfo> Burns() const override
    {
        std::vector<BurnInfo> out;
        for (Burn const& burn : _burns)
            out.push_back(burn.info);
        return out;
    }

    ObjectGuid SpawnFlamePatch(Position const& at, uint32 lifeMs) override
    {
        std::optional<float> const z = FloorNear(me, at.GetPositionX(), at.GetPositionY(), at.GetPositionZ());
        if (!z || !lifeMs)
            return ObjectGuid::Empty;
        Creature* stalker = me->SummonCreature(NPC_BRS_TRIBE_THROWER, Position(at.GetPositionX(),
            at.GetPositionY(), *z, 0.f), TEMPSUMMON_TIMED_DESPAWN, lifeMs);
        if (!stalker)
            return ObjectGuid::Empty;
        stalker->SetReactState(REACT_PASSIVE);
        stalker->CastSpell(stalker, SPELL_WT_BLACK_FLAME_PATCH, true);
        return stalker->GetGUID();
    }

    BossMechanics::SpotBounds LedgeBounds() const override
    {
        std::vector<Position> points;
        for (Vec2 const& p : kLedgeHull)
            points.emplace_back(p.x, p.y, kLedgeZ, 0.f);
        BossMechanics::SpotBounds bounds;
        bounds.Polygon(std::move(points), kLedgeZMin, kLedgeZMax);
        return bounds;
    }

    void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) override
    {
        if (id < kHardModeCastBase)
            return;
        _queue.Schedule(id, _now + inMs, priority);
    }

    void CancelCast(uint32 id) override
    {
        _queue.Cancel(id);
    }

    void Track(MechanicHandle handle) override
    {
        if (handle)
            _live.push_back(handle);
    }

    void TrackSummon(Creature* summon) override
    {
        if (summon)
            summons.Summon(summon);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // ---- his adds call back -----------------------------------------------------------------------------------------

    // A rider reached its lane's end: the hard mode may keep it (WT12), else it rides back down the ramp.
    void RiderArrived(Creature* rider);

    // ---- `.dbtest brs wyrmthalak` entry points ----------------------------------------------------------------------

    bool HeroicMap() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

    void TestBreath(bool heroicForm)
    {
        StartBreath(heroicForm);
    }

    void TestBurn()
    {
        SpawnBurn(me->GetPosition(), BurnSpec{});
    }

    void TestOrder(Tribe tribe)
    {
        IssueOrder({ tribe }, "test");
    }

    void TestBoulders(Player* target)
    {
        BouldersAt({ target });
    }

    void TestAxes(Player* target)
    {
        AxeVolleyOn({ target });
    }

    void TestRiders(Player* target)
    {
        WorgRidersThrough({ target });
    }

    void TestMortalStrike(Player* target)
    {
        StrikeAndWound(target);
    }

    std::string TestState()
    {
        std::string out = Acore::StringFormat("engaged={} heroic={} hardmode={} players={} tankswap={} t={}ms "
            "next order/cleave/ms={}/{}/{}ms next tribe={} burns={} riders={} fury={}", _engaged ? 1 : 0,
            _heroic ? 1 : 0, _hardMode ? 1 : 0, _players, DungeonKit::Flex::TankSwapOn(_players) ? 1 : 0, _now,
            _nextOrderAt, _nextCleaveAt, _nextMortalAt, TribeName(_nextTribe), _burns.size(), _riders.size(),
            DungeonKit::Stacks(me, SPELL_WT_OVERLORDS_FURY));
        if (std::optional<uint64> const breath = _queue.DueAt(CAST_BREATH))
            out += Acore::StringFormat(" next breath={}ms", *breath);
        for (Tribe t : kTribes)
        {
            ChampionState const& c = _champions[Index(t)];
            out += Acore::StringFormat("\n  {}: called={} dead={} alive={}", TribeName(t), c.called ? 1 : 0,
                c.dead ? 1 : 0, Champion(t) ? 1 : 0);
        }
        if (Unit* victim = me->GetVictim())
            out += Acore::StringFormat("\n  victim {} mortal wounds {}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_WT_MORTAL_WOUNDS, me->GetGUID()));
        return out;
    }

private:
    struct ChampionState
    {
        ObjectGuid guid;
        bool called = false;
        bool dead = false;
    };

    struct Burn
    {
        BurnInfo info;
        std::vector<ObjectGuid> stalkers;
    };

    struct Rider
    {
        ObjectGuid guid;
        Lane lane;
    };

    struct Pending
    {
        uint64 atMs = 0;                                    // _clockMs
        std::function<void(boss_overlord_wyrmthalak_rework&)> fn;
    };

    // A resolve callback that finds his AI again (never a captured `this`: the registry may outlive it).
    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBoss(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_overlord_wyrmthalak_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    template <class Fn>
    std::function<void(Unit*)> OnBossHit(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](Unit* hit)
        {
            if (!hit || !map)
                return;
            Creature* boss = map->GetCreature(guid);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_overlord_wyrmthalak_rework*>(boss->AI()))
                fn(*ai, hit);
        };
    }

    // A look or a move on the AI's own clock (the missiles timed to their markers, the riders' charge).
    void Later(uint32 inMs, std::function<void(boss_overlord_wyrmthalak_rework&)> fn)
    {
        _pending.push_back({ _clockMs + inMs, std::move(fn) });
    }

    void RunPending()
    {
        if (_pending.empty())
            return;
        std::vector<Pending> due;
        std::vector<Pending> later;
        for (Pending& p : _pending)
            (p.atMs <= _clockMs ? due : later).push_back(std::move(p));
        _pending = std::move(later);
        for (Pending& p : due)
            p.fn(*this);
    }

    void Describe()
    {
        // Boss data (build spec): normal, the champions as they arrive; heroic lean, the Smolderthorn Champion only
        // (the other two below him, left alive) [to tune in playtest]. At 10 the taunt swap at 3 Mortal Wounds and the
        // assist tank picks up the champions. B9 edits it for the hard mode (Mechanic::EditDescriptor).
        BossMechanics::Descriptor d;
        for (Tribe t : kTribes)
        {
            int8 const priority = (!_heroic || t == Tribe::Smolderthorn) ? 1 : -1;
            d.targets.push_back(BossMechanics::TargetEntry(ChampionEntry(t), priority));
        }
        if (DungeonKit::Flex::TankSwapOn(_players))
        {
            d.tauntSwaps.push_back(BossMechanics::TauntSwapEntry(0, SPELL_WT_MORTAL_WOUNDS, kMortalWoundsSwapAt));
            for (Tribe t : kTribes)
                d.targets.push_back(BossMechanics::TargetEntry(ChampionEntry(t), 1,
                    BossMechanics::Who::AssistTank));
        }
        Mechanic::Describe(me, std::move(d));
    }

    // A cast bar of his, or a hard mode cast holding him.
    bool Busy() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING) || _now < _holdUntil;
    }

    // The cast queue: the breath and B9's casts, one at a time.
    void RunQueue()
    {
        std::optional<uint32> const next = _queue.Next(_now);
        if (!next)
            return;
        if (*next == CAST_BREATH)
        {
            if (!me->GetVictim())
            {
                _queue.Schedule(CAST_BREATH, _now + kRetryMs, kBreathPriority);
                return;
            }
            _queue.Started(CAST_BREATH, _now, kBreathCastMs);
            _queue.Schedule(CAST_BREATH, _now + kBreathEveryMs, kBreathPriority);
            StartBreath(_heroic);
            return;
        }
        // The entry is consumed before OnCast: a next cast the hook schedules for the same id stays queued.
        uint32 const id = *next;
        std::optional<uint32> const holdMs = StartHardModeCast(_queue, id, _now, [this, id]()
        {
            return _hardMode ? _hardMode->OnCast(*this, id) : std::nullopt;
        });
        if (holdMs)
            _holdUntil = _now + *holdMs;
    }

    // A hard mode cast bar kicked (Caustic Roar): the hold it set ends with it (B9's request).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!_engaged || _now >= _holdUntil)
            return;
        _holdUntil = EndHoldEarly(_queue, _holdUntil, _now);
        Log("hold-ended", Acore::StringFormat("spell={}", spell ? spell->Id : 0));
    }

    // ---- WT1 Black Dragonfire, WT1b the burn ------------------------------------------------------------------------

    void StartBreath(bool heroicForm)
    {
        DungeonKit::CastBar(me, SPELL_WT_DRAGONFIRE_CAST, nullptr, EMOTE_WT_BREATH);
        MechanicRef ref = Mechanic::Cone(me, me, kBreathAngleDeg, kBreathLength, Milliseconds(kBreathCastMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(kBreathPct(heroicForm)).School(SPELL_SCHOOL_FIRE).Spell(SPELL_WT_BLACK_DRAGONFIRE).Weakened()
            .Within(LedgeBounds()).Tag(TAG_WT_BREATH);
        if (BreathSparesBothTanks(_players))
        {
            // At 10 players the breath is tank-exempt for both tanks (SP: the waiting one too, R-1-B M3): only healers
            // and damage dealers are hit. The heroic burn it leaves (WT1b) has no tank exemption by design.
            BossMechanics::Eligibility nonTank;
            nonTank.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
            ref.Eligible(nonTank);
        }
        ref.OnHit(OnBossHit([](boss_overlord_wyrmthalak_rework& ai, Unit* hit)
        {
            if (ai._hardMode && ai._engaged && hit->IsPlayer())
                ai._hardMode->OnAbilityHit(ai, Ability::BlackDragonfire, hit);
        }));
        ref.OnResolve(OnBoss([heroicForm](boss_overlord_wyrmthalak_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.Log("breath-landed", Acore::StringFormat("hits={} heroic={}", r.hits.size(), heroicForm ? 1 : 0));
            if (heroicForm)
                ai.BreathBurn();
        }));
        Track(ref.Handle());
        Log("breath", Acore::StringFormat("heroic={} o={:.2f}", heroicForm ? 1 : 0, me->GetOrientation()));
    }

    // The breath landed: its cone keeps burning where he faced (heroic; the hard mode's own length and life).
    void BreathBurn()
    {
        BurnSpec spec;
        if (_hardMode)
            spec = _hardMode->Burn(*this, spec);
        SpawnBurn(me->GetPosition(), spec);
    }

    void EndBurn(Burn const& burn)
    {
        Mechanic::Cancel(me, burn.info.handle);
        for (ObjectGuid const& guid : burn.stalkers)
            if (Creature* stalker = ObjectAccessor::GetCreature(*me, guid))
                stalker->DespawnOrUnsummon();
    }

    void PruneBurns()
    {
        std::erase_if(_burns, [this](Burn const& burn) { return _now >= burn.info.untilMs; });
    }

    // ---- WT2 Tail Swipe ---------------------------------------------------------------------------------------------

    void RegisterTailSwipe()
    {
        MechanicRef ref = Mechanic::Cone(me, me, kTailAngleDeg, kTailLength, Milliseconds(kTailFirstMs));
        ref.Rear().Persistent(Milliseconds(kFightLongMs), Milliseconds(kTailEveryMs)).Damage(kTailPct(_heroic))
            .TankDamage(kTailPct(_heroic)).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_WT_TAIL_SWIPE).Weakened()
            .Within(LedgeBounds()).Tag(TAG_WT_TAIL);
        ref.OnHit(OnBossHit([](boss_overlord_wyrmthalak_rework& ai, Unit* hit)
        {
            // 10 yd away from him, backwards: off the ledge where its open edge is behind him.
            hit->KnockbackFrom(ai.me->GetPositionX(), ai.me->GetPositionY(), kTailKnockSpeedXY, kTailKnockSpeedZ);
            if (ai._hardMode && ai._engaged && hit->IsPlayer())
                ai._hardMode->OnAbilityHit(ai, Ability::TailSwipe, hit);
        }));
        ref.OnResolve(OnBoss([](boss_overlord_wyrmthalak_rework& ai, BossMechanics::ResolveResult const& r)
        {
            ai.me->CastSpell(ai.me, SPELL_WT_TAIL_SWEEP_LOOK, true);
            ai.Log("tail-swipe", Acore::StringFormat("pass={} hits={}", r.pass, r.hits.size()));
        }));
        Track(ref.Handle());
    }

    // ---- WT3 Cleave -------------------------------------------------------------------------------------------------

    void Cleave()
    {
        if (_now < _nextCleaveAt)
            return;
        Unit* victim = me->GetVictim();
        if (victim && me->IsWithinMeleeRange(victim) && DoCastVictim(SPELL_WT_CLEAVE) == SPELL_CAST_OK)
            _nextCleaveAt = _now + kCleaveEveryMs;
        else
            _nextCleaveAt = _now + kRetryMs;
    }

    // ---- WT18 Mortal Strike (10 players) ----------------------------------------------------------------------------

    void MortalStrike()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
        {
            _nextMortalAt = _now + kRetryMs;
            return;
        }
        _nextMortalAt = _now + kMortalStrikeEveryMs;
        StrikeAndWound(victim);
    }

    void StrikeAndWound(Unit* victim)
    {
        if (!victim || !victim->IsAlive())
            return;
        me->CastSpell(victim, SPELL_WT_MORTAL_STRIKE, true);       // 30% of the tank row (RefFlatOn at launch)
        me->CastSpell(victim, SPELL_WT_MORTAL_WOUNDS, true);       // a stack, the duration refreshed
        Log("mortal-strike", Acore::StringFormat("on={} stacks={}", victim->GetName(),
            DungeonKit::Stacks(victim, SPELL_WT_MORTAL_WOUNDS, me->GetGUID())));
    }

    // ---- WT4 Orders and the champions -------------------------------------------------------------------------------

    void Order()
    {
        uint32 const every = _hardMode ? _hardMode->OrderEveryMs(*this, kOrderEveryMs(_heroic))
            : kOrderEveryMs(_heroic);
        _nextOrderAt = _now + every;
        uint8 const count = _hardMode ? _hardMode->TribesPerOrder(*this) : 1;
        std::vector<Tribe> tribes = OrderTribes(_nextTribe, count);
        for (uint8 i = 0; i < count && i < kTribeCount; ++i)
            _nextTribe = NextTribe(_nextTribe);
        if (_hardMode)
            _hardMode->OnOrder(*this, tribes);
        bool const firstOrder = !_ordered;
        _ordered = true;
        if (firstOrder && _hardMode && _hardMode->AllChampionsAtFirstOrder(*this))
            for (Tribe t : kTribes)
                SummonChampion(t);
        IssueOrder(tribes, "timer");
    }

    void Answer(Tribe tribe)
    {
        switch (tribe)
        {
            case Tribe::Spirestone:
                Boulders(kBoulderTargets.At(_players));
                break;
            case Tribe::Smolderthorn:
                AxeVolley(kAxeTargets.At(_players));
                break;
            case Tribe::Bloodaxe:
                WorgRiders(kRiderTargets.At(_players));
                break;
        }
    }

    void ChampionDied(Tribe tribe, Creature* champion)
    {
        ChampionState& c = _champions[Index(tribe)];
        c.dead = true;
        c.guid.Clear();
        uint32 fury = 0;
        if (_heroic && _engaged && !_hardMode)      // WT8: the hard mode's unlocks replace it
            fury = DungeonKit::AddStacks(me, SPELL_WT_OVERLORDS_FURY, 1, me, kFuryMaxStacks);
        Log("champion-died", Acore::StringFormat("tribe={} fury={}", TribeName(tribe), fury));
        if (_hardMode && _engaged)
            _hardMode->OnChampionDied(*this, tribe, champion);
    }

    Creature* SummonThrower(Point3 const& spot)
    {
        Creature* thrower = me->SummonCreature(NPC_BRS_TRIBE_THROWER, At(spot), TEMPSUMMON_TIMED_DESPAWN,
            kThrowerLifeMs);
        if (thrower)
            thrower->SetReactState(REACT_PASSIVE);
        return thrower;
    }

    // ---- WT5 Boulders -----------------------------------------------------------------------------------------------

    std::vector<Position> BouldersAt(std::vector<Player*> const& players)
    {
        std::vector<Position> spots;
        Creature* thrower = players.empty() ? nullptr : SummonThrower(kBoulderThrowerSpot);
        ObjectGuid const throwerGuid = thrower ? thrower->GetGUID() : ObjectGuid::Empty;
        for (Player* player : players)
        {
            if (!player)
                continue;
            Position const at = player->GetPosition();
            MechanicRef ref = Mechanic::Circle(me, at, kBoulderRadius, Milliseconds(kBoulderWarnMs));
            ref.Damage(kBoulderPct(_heroic)).TankDamage(kBoulderPct(_heroic)).School(SPELL_SCHOOL_NORMAL)
                .Spell(SPELL_WT_BOULDER).Weakened().Within(LedgeBounds()).Tag(TAG_WT_BOULDER);
            ref.OnResolve(OnBoss([at](boss_overlord_wyrmthalak_rework& ai, BossMechanics::ResolveResult const&)
            {
                if (ai._hardMode && ai._engaged)
                    ai._hardMode->OnBoulderLanded(ai, at);
            }));
            Track(ref.Handle());
            spots.push_back(at);

            float const distance = DungeonKit::Distance(kBoulderThrowerSpot.XY(), XY(at));
            Later(MissileDelayMs(distance, kBoulderMissileSpeed, kBoulderWarnMs),
                [throwerGuid, at](boss_overlord_wyrmthalak_rework& ai)
                {
                    if (Creature* t = ObjectAccessor::GetCreature(*ai.me, throwerGuid))
                        t->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(),
                            SPELL_WT_BOULDER_MISSILE, true);
                });
        }
        Log("boulders", Acore::StringFormat("count={} heroic={}", spots.size(), _heroic ? 1 : 0));
        return spots;
    }

    // ---- WT6 Axe Volley ---------------------------------------------------------------------------------------------

    GuidSet AxeVolleyOn(std::vector<Player*> const& players)
    {
        GuidSet marked;
        for (Player* player : players)
            if (player)
            {
                marked.insert(player->GetGUID());
                me->CastSpell(player, SPELL_WT_AXE_MARK, true);
            }
        if (marked.empty())
        {
            Log("axe-volley", "no target");
            return marked;
        }

        MechanicRef ref = Mechanic::RunOut(me, nullptr, kAxeRadius, Milliseconds(kAxeWarnMs));
        ref.Targets(marked).Damage(kAxePct(_heroic)).TankDamage(kAxePct(_heroic)).School(SPELL_SCHOOL_NORMAL)
            .Spell(SPELL_WT_AXE_VOLLEY).Weakened().Within(LedgeBounds()).Tag(TAG_WT_AXES);
        ref.OnResolve(OnBoss([marked](boss_overlord_wyrmthalak_rework& ai, BossMechanics::ResolveResult const&)
        {
            std::vector<Position> spots;
            for (ObjectGuid const& guid : marked)
                if (Player* p = ObjectAccessor::GetPlayer(*ai.me, guid))
                    spots.push_back(p->GetPosition());
            ai.Log("axes-landed", Acore::StringFormat("axes={}", spots.size()));
            if (ai._hardMode && ai._engaged)
                ai._hardMode->OnAxesLanded(ai, spots);
        }));
        Track(ref.Handle());

        Creature* thrower = (_hardMode && _engaged) ? _hardMode->AxeThrower(*this) : nullptr;
        bool const champion = thrower != nullptr;
        if (!thrower)
            thrower = SummonThrower(kAxeThrowerSpot);
        if (thrower)
        {
            ObjectGuid const throwerGuid = thrower->GetGUID();
            for (Player* player : players)
            {
                if (!player)
                    continue;
                ObjectGuid const target = player->GetGUID();
                float const distance = DungeonKit::Distance(DungeonKit::PlaneOf(thrower), DungeonKit::PlaneOf(player));
                Later(MissileDelayMs(distance, kAxeMissileSpeed, kAxeWarnMs),
                    [throwerGuid, target](boss_overlord_wyrmthalak_rework& ai)
                    {
                        Creature* t = ObjectAccessor::GetCreature(*ai.me, throwerGuid);
                        Player* p = ObjectAccessor::GetPlayer(*ai.me, target);
                        if (t && t->IsAlive() && p && p->IsAlive())
                            t->CastSpell(p, SPELL_WT_THROW_AXE, true);
                    });
            }
        }
        Log("axe-volley", Acore::StringFormat("marked={} thrower={} heroic={}", marked.size(),
            champion ? "champion" : "ramp", _heroic ? 1 : 0));
        return marked;
    }

    // ---- WT7 Worg Riders --------------------------------------------------------------------------------------------

    std::vector<ObjectGuid> WorgRidersThrough(std::vector<Player*> const& players)
    {
        std::vector<ObjectGuid> out;
        uint32 i = 0;
        for (Player* player : players)
        {
            if (!player)
                continue;
            Lane const lane = RiderLane(kRiderOrigin.XY(), DungeonKit::PlaneOf(player));
            float const z = kRiderOrigin.z;
            float const facing = DungeonKit::BearingTo(lane.from, lane.to);
            // They paw side by side at the ramp head (the look); the lanes start at the one origin.
            Vec2 const stand = DungeonKit::Advance(lane.from, facing + DungeonKit::kPi / 2.f,
                (float(i % 2) - 0.5f) * 2.f * float(1 + i / 2));
            ++i;
            Creature* rider = me->SummonCreature(NPC_BRS_BLOODAXE_WORG_RIDER, Position(stand.x, stand.y, z, facing),
                TEMPSUMMON_TIMED_DESPAWN, kRiderLifeMs);

            MechanicRef ref = Mechanic::Line(me, Position(lane.from.x, lane.from.y, z, facing),
                Position(lane.to.x, lane.to.y, z, facing), kRiderLaneWidth, Milliseconds(kRiderWarnMs));
            ref.Projectile(kRiderSpeed).Damage(kRiderPct(_heroic)).TankDamage(kRiderPct(_heroic))
                .School(SPELL_SCHOOL_NORMAL).Spell(SPELL_WT_WORG_RIDERS).Weakened().Within(LedgeBounds())
                .Tag(TAG_WT_RIDER);
            ref.OnHit(OnBossHit([lane](boss_overlord_wyrmthalak_rework& /*ai*/, Unit* hit)
            {
                Vec2 const from = KnockAsideOrigin(lane, DungeonKit::PlaneOf(hit));
                hit->KnockbackFrom(from.x, from.y, kRiderKnockSpeedXY, kRiderKnockSpeedZ);
            }));
            Track(ref.Handle());

            if (!rider)
                continue;
            rider->SetReactState(REACT_PASSIVE);
            ObjectGuid const riderGuid = rider->GetGUID();
            out.push_back(riderGuid);
            _riders.push_back({ riderGuid, lane });
            Later(kRiderWarnMs, [riderGuid, lane, z](boss_overlord_wyrmthalak_rework& ai)
            {
                if (Creature* r = ObjectAccessor::GetCreature(*ai.me, riderGuid))
                {
                    r->CastSpell(r, SPELL_WT_WORG_CHARGE_LOOK, true);
                    r->GetMotionMaster()->MoveCharge(lane.to.x, lane.to.y, z, kRiderSpeed, POINT_RIDER_END);
                }
            });
        }
        Log("worg-riders", Acore::StringFormat("riders={} heroic={}", out.size(), _heroic ? 1 : 0));
        return out;
    }

    // ---- cleanup ----------------------------------------------------------------------------------------------------

    // The pull's state, gone: the hard mode's own end first, every mechanic, the burns, every summon.
    void Cleanup(bool died)
    {
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        for (Burn const& burn : _burns)
            EndBurn(burn);
        _burns.clear();
        _riders.clear();
        _pending.clear();
        summons.DespawnAll();
        _queue.Reset();
        _champions = {};
        _nextTribe = Tribe::Spirestone;
        _ordered = false;
        _now = 0;
        _holdUntil = 0;
        _nextOrderAt = 0;
        _nextCleaveAt = 0;
        _nextMortalAt = 0;
        _players = 0;
        _engaged = false;
        _arena.Reset();
        me->RemoveAurasDueToSpell(SPELL_WT_OVERLORDS_FURY);
        if (instance)
        {
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_WT_MORTAL_WOUNDS);
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_WT_AXE_MARK);
        }
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CastQueue _queue;
    std::unique_ptr<WyrmthalakHardMode> _hardMode;
    std::vector<MechanicHandle> _live;
    std::vector<Burn> _burns;
    std::vector<Rider> _riders;
    std::vector<Pending> _pending;
    std::array<ChampionState, kTribeCount> _champions{};
    Tribe _nextTribe = Tribe::Spirestone;
    uint64 _clockMs = 0;            // ms the AI has run (the pending looks' clock; never held)
    uint64 _now = 0;                // ms since the pull
    uint64 _holdUntil = 0;          // _now: a hard mode cast holds him until then
    uint64 _nextOrderAt = 0;
    uint64 _nextCleaveAt = 0;
    uint64 _nextMortalAt = 0;
    uint8 _players = 0;             // the flex count held at the pull (5..10)
    bool _heroic = false;
    bool _engaged = false;
    bool _ordered = false;
};

// The champions 300708-300710: they walk up the ramp passive (about 5 s), then fight on the ledge; struck on the way,
// they turn and fight at once. Melee only (the hard mode's Smolderthorn Champion throws through B8's AxeVolley).
struct npc_brs_wyrmthalak_champion : public ScriptedAI
{
    explicit npc_brs_wyrmthalak_champion(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _fallbackMs = kChampionEngageFallbackMs;
        // SP: "an orc on a worg" (Bloodaxe Raider 9602 on the riders' dire wolf).
        if (me->GetEntry() == NPC_BRS_BLOODAXE_CHAMPION && !me->IsMounted())
            me->Mount(kRiderMountDisplay);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_CHAMPION_LANDING)
            Engage("landed");
    }

    void DamageTaken(Unit* /*attacker*/, uint32& /*damage*/, DamageEffectType /*type*/, SpellSchoolMask /*mask*/)
        override
    {
        if (!_engaged)
            Engage("struck");
    }

    void AttackStart(Unit* who) override
    {
        if (_engaged)
            ScriptedAI::AttackStart(who);
    }

    void MoveInLineOfSight(Unit* who) override
    {
        if (_engaged)
            ScriptedAI::MoveInLineOfSight(who);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!_engaged)
        {
            _fallbackMs = _fallbackMs > diff ? _fallbackMs - diff : 0;
            if (!_fallbackMs)
                Engage("fallback");
            return;
        }
        if (!UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    // On the ledge: into his fight, on his victim first (the tank picks it up; the assist tank at 10).
    void Engage(char const* why)
    {
        if (_engaged)
            return;
        _engaged = true;
        me->SetReactState(REACT_AGGRESSIVE);
        Creature* boss = nullptr;
        if (TempSummon* summon = me->ToTempSummon())
            if (Unit* summoner = summon->GetSummonerUnit())
                boss = summoner->ToCreature();
        Unit* victim = (boss && boss->IsAlive() && boss->IsEngaged()) ? boss->GetVictim() : nullptr;
        DoZoneInCombat();
        if (victim)
        {
            me->AddThreat(victim, kChampionOpeningThreat);
            AttackStart(victim);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "champion-engage", Acore::StringFormat("entry={} why={} "
            "victim={}", me->GetEntry(), why, victim ? victim->GetName() : std::string("none")));
    }

    uint32 _fallbackMs = kChampionEngageFallbackMs;
    bool _engaged = false;
};

// The Worg Rider 300711 (normal and heroic: a passing effect, not attackable): paws at the ramp head, charges its lane
// (the registry's projectile line owns the hit), then rides back down and despawns. A rider the hard mode keeps (WT12,
// B9) stays: Keep() hands it its melee; B9 makes it attackable and drives it.
struct npc_brs_bloodaxe_worg_rider : public ScriptedAI
{
    explicit npc_brs_bloodaxe_worg_rider(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        me->Mount(kRiderMountDisplay);
        ScriptedAI::InitializeAI();
    }

    void Reset() override
    {
        if (!_kept)
            me->SetReactState(REACT_PASSIVE);
    }

    void Keep()
    {
        _kept = true;
        me->SetReactState(REACT_AGGRESSIVE);
    }

    bool Kept() const
    {
        return _kept;
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (_kept || (type != POINT_MOTION_TYPE && type != EFFECT_MOTION_TYPE))
            return;
        if (id == POINT_RIDER_END)
        {
            Creature* boss = nullptr;
            if (TempSummon* summon = me->ToTempSummon())
                if (Unit* summoner = summon->GetSummonerUnit())
                    boss = summoner->ToCreature();
            if (boss && boss->IsAlive() && boss->IsAIEnabled)
                if (auto* ai = dynamic_cast<boss_overlord_wyrmthalak_rework*>(boss->AI()))
                {
                    ai->RiderArrived(me);
                    return;
                }
            RideHome();
        }
        else if (id == POINT_RIDER_HOME)
            me->DespawnOrUnsummon();
    }

    void RideHome()
    {
        me->GetMotionMaster()->MovePoint(POINT_RIDER_HOME, kRiderOrigin.x, kRiderOrigin.y, kRiderOrigin.z,
            FORCED_MOVEMENT_NONE, kRiderSpeed);
    }

    void AttackStart(Unit* who) override
    {
        if (_kept)
            ScriptedAI::AttackStart(who);
    }

    void MoveInLineOfSight(Unit* who) override
    {
        if (_kept)
            ScriptedAI::MoveInLineOfSight(who);
    }

    void UpdateAI(uint32 /*diff*/) override
    {
        if (!_kept || !UpdateVictim())
            return;
        DoMeleeAttackIfReady();
    }

private:
    bool _kept = false;
};

void boss_overlord_wyrmthalak_rework::RiderArrived(Creature* rider)
{
    if (!rider)
        return;
    auto* riderAI = rider->IsAIEnabled ? dynamic_cast<npc_brs_bloodaxe_worg_rider*>(rider->AI()) : nullptr;
    ObjectGuid const guid = rider->GetGUID();
    std::erase_if(_riders, [guid](Rider const& r) { return r.guid == guid; });
    bool const keep = _hardMode && _engaged && _hardMode->OnRiderCharged(*this, rider);
    if (keep)
    {
        if (riderAI)
            riderAI->Keep();
        Log("rider-kept", Acore::StringFormat("guid={}", guid.GetCounter()));
        return;
    }
    if (riderAI)
        riderAI->RideHome();
    else
        rider->DespawnOrUnsummon();
}

namespace
{
    boss_overlord_wyrmthalak_rework* FindWyrmthalakAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_WYRMTHALAK);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_overlord_wyrmthalak_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Wyrmthalak is not running boss_overlord_wyrmthalak_rework (check the "
                "ScriptName).");
        return ai;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    std::optional<Tribe> ParseTribe(ChatHandler* handler, std::string const& name)
    {
        std::optional<Tribe> const tribe = TribeByName(name.c_str());
        if (!tribe)
            handler->SendErrorMessage("{}", "Tribe: spirestone, smolderthorn or bloodaxe.");
        return tribe;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_WYRMTHALAK, BOSS_WYRMTHALAK);
    }

    // `.dbtest brs wyrmthalak state`: the clock, the timers, the champions, the burns, the riders, the stacks.
    bool HandleState(ChatHandler* handler)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Wyrmthalak: {}", ai->TestState());
        return true;
    }

    // `.dbtest brs wyrmthalak breath [0|1]`: Black Dragonfire now (WT1); 1 = with the heroic burn (WT1b).
    bool HandleBreath(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        ai->TestBreath(isHeroic);
        handler->PSendSysMessage("Wyrmthalak: Black Dragonfire ({}) (WT1).", isHeroic ? "with the burn" : "normal");
        return true;
    }

    // `.dbtest brs wyrmthalak burn`: a burn on his cone now (WT1b, the heroic numbers).
    bool HandleBurn(ChatHandler* handler)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        if (!ai)
            return false;
        ai->TestBurn();
        handler->PSendSysMessage("{}", "Wyrmthalak: a burn on his cone (WT1b).");
        return true;
    }

    // `.dbtest brs wyrmthalak order <tribe>`: an order to that tribe now (WT4: its champion on the first call, its
    // answer while the champion lives).
    bool HandleOrder(ChatHandler* handler, std::string tribeName)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        std::optional<Tribe> const tribe = ParseTribe(handler, tribeName);
        if (!ai || !tribe)
            return false;
        ai->TestOrder(*tribe);
        handler->PSendSysMessage("Wyrmthalak: an order to the {} (WT4).", TribeName(*tribe));
        return true;
    }

    // `.dbtest brs wyrmthalak champion <tribe>`: that champion up the ramp now (no answer).
    bool HandleChampion(ChatHandler* handler, std::string tribeName)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        std::optional<Tribe> const tribe = ParseTribe(handler, tribeName);
        if (!ai || !tribe)
            return false;
        Creature* champion = ai->SummonChampion(*tribe);
        handler->PSendSysMessage("Wyrmthalak: the {} champion {}.", TribeName(*tribe),
            champion ? "comes up the ramp" : "was already called (or died)");
        return true;
    }

    // `.dbtest brs wyrmthalak boulders`: a boulder at the selected player's (or your) spot (WT5).
    bool HandleBoulders(ChatHandler* handler)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestBoulders(target);
        handler->PSendSysMessage("Wyrmthalak: a boulder at {}'s spot (WT5).", target->GetName());
        return true;
    }

    // `.dbtest brs wyrmthalak axes`: the selected player (or you) marked by the Axe Volley (WT6).
    bool HandleAxes(ChatHandler* handler)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestAxes(target);
        handler->PSendSysMessage("Wyrmthalak: {} is marked by the Axe Volley (WT6).", target->GetName());
        return true;
    }

    // `.dbtest brs wyrmthalak riders`: a Worg Rider's lane through the selected player's (or your) spot (WT7).
    bool HandleRiders(ChatHandler* handler)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestRiders(target);
        handler->PSendSysMessage("Wyrmthalak: a Worg Rider charges through {}'s spot (WT7).", target->GetName());
        return true;
    }

    // `.dbtest brs wyrmthalak mortal`: Mortal Strike and a Mortal Wounds stack on the selected player (or you)
    // (WT18; in the fight it runs at 10 players only).
    bool HandleMortal(ChatHandler* handler)
    {
        boss_overlord_wyrmthalak_rework* ai = FindWyrmthalakAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestMortalStrike(target);
        handler->PSendSysMessage("Wyrmthalak: Mortal Strike on {} (WT18).", target->GetName());
        return true;
    }

    ChatCommandTable const& WyrmthalakTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "breath",   HandleBreath,   SEC_GAMEMASTER, Console::No },
            { "burn",     HandleBurn,     SEC_GAMEMASTER, Console::No },
            { "order",    HandleOrder,    SEC_GAMEMASTER, Console::No },
            { "champion", HandleChampion, SEC_GAMEMASTER, Console::No },
            { "boulders", HandleBoulders, SEC_GAMEMASTER, Console::No },
            { "axes",     HandleAxes,     SEC_GAMEMASTER, Console::No },
            { "riders",   HandleRiders,   SEC_GAMEMASTER, Console::No },
            { "mortal",   HandleMortal,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_overlord_wyrmthalak_rework()
{
    RegisterDungeonReworkCreatureAI(boss_overlord_wyrmthalak_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_wyrmthalak_champion, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_bloodaxe_worg_rider, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("wyrmthalak", WyrmthalakTestCommands());
}
