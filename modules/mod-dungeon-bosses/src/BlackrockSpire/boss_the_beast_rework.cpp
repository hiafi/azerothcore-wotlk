/*
 * mod-dungeon-bosses, Blackrock Spire B13: The Beast (10430), "a monster so bad its keepers kill themselves" (SP
 * 3465-3698, BE1-BE10, rulings 65-67; handoff section 3.4 rows BE, 3.5 row B13, 3.6, 3.8). Replaces the stock
 * boss_the_beast (Flamebreak, Immolate, Terrifying Roar, Berserker Charge, Fireball, Fire Blast); bound by
 * apps/dbc-tools source/npcs/blackrock_spire/the_beast.py. Pure rules: BeastLogic.h.
 *
 * The wake, the Elites' panic and the evade line are the stock script's (boss_the_beast.cpp at 3da6e3019, by Andrew,
 * Francesco Borzi, killerwife, the Chinese contributors and the AzerothCore team), re-implemented here the same way:
 * the area triggers 2066 and 2067 (at_trigger_the_beast_movement and at_the_beast_room, still registered by the stock
 * file) call this AI's SetData(1 | 2) through the instance's GetGuidData(BOSS_BEAST); the skinning hook that frees
 * Finkle Einhorn stays in the instance.
 *
 *   BE1 The wake     SetData(1): he walks path 1379690 out of the pit (and again after every reset); SetData(2): the
 *                    Elites by the pit yell "We're doomed!", run and kill themselves 9 s later (stock)
 *   BE2 Heat         a stack at 20 s (heroic 15 s), then every 20 s (15 s): +10% damage done (his melee, Fire Blast and
 *                    Immolate by the aura; Magma Split's own percents by DamageMult), half a yard on every NEW pool,
 *                    no cap; emote line 1, a chest flash; at 3 stacks the roar comes every 15 s, at 5 Magma Split does
 *   BE3 Molten Blood a pool for every 4% of his health lost (25 in all) in a random direction, its near edge 5 yd from
 *                    him, on open floor (the hall's rectangle or the pit's disc); a 1.5 s marker, then 10% Fire a
 *                    second to anyone inside (once, however many overlap: the puddle field), for the whole fight;
 *                    5 yd (heroic 4.5) + half a yard a Heat stack; a lava look on a stalker as the marker arms
 *   BE4 Molten Fury  while he stands in lava, +10% damage done every 2 s of unbroken time, kept to the end
 *   BE5 Dread        at 10 s, then every 20 s (15 s from Heat 3): a 2 s roar (emote line 0); everyone with fewer than
 *                    2 other players within 6 yd gains a Dread stack (30 s after the last); at 3 stacks (heroic 2) they
 *                    panic: a 2 s flee, the stacks clear. The tank counts like anyone: pack on the tank
 *   BE6 Magma Split  at 20 s, then every 20 s (15 s from Heat 5): a 2 s cast, a 6 yd circle on 2 random non-tanks (4 at
 *                    6 or more); the target takes 15% Fire, anyone else inside 30% + Weakened and a 5 yd throw away
 *                    from the target; heroic: a 4 yd pool where the target stood
 *   BE7 Eruption     at 2:00 (heroic 1:40) the whole floor is lava: 10% Fire a second to everyone, until the wipe
 *   BE8 Immolate     stock 15570 at a random player at 3 s, every 8 s (a Magic dispel, a reward); heroic casts its own
 *                    copy: 3% a second for the stock 21 s, an expected dispel, and a 4 yd pool where it runs out
 *   BE9 Fire Blast   stock 16144 on his target every 5 to 8 s (a filler: it never delays a mechanic)
 *   BE10 Reset       evade, wipe or death: the pools, the stalkers, Heat, Fury, Dread, Panic and Immolate go
 *
 * Boss data: kill order the boss only; no interrupts; dispel list Immolate (priority 1 normal, 3 heroic). No tank swap
 * (not on ruling 63's list), no G1 follow-up. Every timer runs on the AI's own clock, never on BossAI's scheduler.
 * Every firing logs one INFO line "brs beast <mechanic> ..." (module.dungeonbosses); `.dbtest brs beast ...` fires
 * one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BeastLogic.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <list>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsBeast;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "beast";

    // The Elites' run-to spot (stock).
    Position const kOrcsRunawayPosition = { 34.163567f, -536.852356f, 110.935196f, 6.056306f };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    Vec2 PlaneOfPoint(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    // Where a bot may plan to stand: the hall's rectangle and the pit's disc (the walls' shrink included).
    BossMechanics::SpotBounds FightBounds()
    {
        BossMechanics::SpotBounds bounds;
        bounds.Rect(kHallMinX - 0.5f, kHallMinY - 0.5f, kHallMaxX + 0.5f, kHallMaxY + 0.5f, kHallZMin, kHallZMax);
        bounds.Circle(Position(kPitCenter.x, kPitCenter.y, 108.f, 0.f), kPitRadiusYd + 0.5f, kPitZMin, kPitZMax);
        return bounds;
    }

    // The hall's outline for a drop spot rule's room (the edge walk of a Magma Split target).
    std::vector<Position> HallRoom()
    {
        return { Position(kHallMinX, kHallMinY, 111.f, 0.f), Position(kHallMaxX, kHallMinY, 111.f, 0.f),
            Position(kHallMaxX, kHallMaxY, 111.f, 0.f), Position(kHallMinX, kHallMaxY, 111.f, 0.f) };
    }

    // The stock Elites' end: run for 9 s, then die (boss_the_beast.cpp OrcMoveEvent / OrcDeathEvent).
    class OrcMoveEvent : public BasicEvent
    {
    public:
        explicit OrcMoveEvent(Creature* me) : _me(me) { }

        bool Execute(uint64 /*time*/, uint32 /*diff*/) override
        {
            _me->SetReactState(REACT_PASSIVE);
            Position movePos = _me->GetRandomPoint(kOrcsRunawayPosition, kElitesRunRadiusYd);
            _me->GetMotionMaster()->MovePoint(1, movePos);
            return true;
        }

    private:
        Creature* _me;
    };

    class OrcDeathEvent : public BasicEvent
    {
    public:
        explicit OrcDeathEvent(Creature* me) : _me(me) { }

        bool Execute(uint64 /*time*/, uint32 /*diff*/) override
        {
            _me->CastSpell(_me, SPELL_BE_SUICIDE, true);
            return true;
        }

    private:
        Creature* _me;
    };
}

// The Beast 10430
struct boss_the_beast_rework : public BossAI
{
    explicit boss_the_beast_rework(Creature* creature)
        : BossAI(creature, BOSS_BEAST), _arena(BeastArena(), LeashOptions(kBossLogName)),
          _pools(Ms(kPoolTickMs), 5.f) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
        // The stock rule: once the first area trigger has sent him out of the pit, he patrols the path out of combat.
        if (_beastReached)
            me->GetMotionMaster()->MoveWaypoint(BEAST_MOVEMENT_ID, true);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _players = OnBossPull(me, kBossLogName);
        _heroic = IsHeroicMap(me);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_BEAST;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        _nextHeatMs = kHeatEveryMs(_heroic);
        _beats.Start(0, FireBlastRollMs());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} heat@{}s roar@{}s split@{}s eruption@{}s at=({:.1f}, {:.1f}, "
            "{:.1f})", _heroic ? 1 : 0, _players, _nextHeatMs / 1000, kRoarFirstMs / 1000, kSplitFirstMs / 1000,
            kEruptionAtMs(_heroic) / 1000, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("heat={} fury={} pools={} laid={} floor={:.0f} erupted={} killer={}", _heat, _fury,
            _poolList.size(), _poolsLaid, _pools.CoveredArea(0.5f), _erupted ? 1 : 0,
            killer ? killer->GetName() : "none"));
        Cleanup();
    }

    // The pool stalkers are props: never zoned into combat (BossAI::JustSummoned would).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // A broken cast ends the queue's hold on him (no cast of his is interruptible, but a displacement could still end
    // one).
    void OnSpellFailed(SpellInfo const* /*spell*/) override
    {
        _beats.Interrupted(_clockMs);
    }

    // BE1: the stock wake protocol, called by the area triggers 2066 (reached) and 2067 (room).
    void SetData(uint32 type, uint32 /*data*/) override
    {
        switch (type)
        {
            case DATA_BEAST_ROOM:
                if (!_orcYelled)
                {
                    if (_nearbyOrcs.empty())
                        FindNearbyOrcs();
                    if (_nearbyOrcs.empty())
                        return;     // the Elites are missing
                    _orcYelled = true;
                    bool yelled = false;
                    for (ObjectGuid const& guid : _nearbyOrcs)
                        if (Creature* orc = ObjectAccessor::GetCreature(*me, guid))
                        {
                            if (!yelled)
                            {
                                yelled = true;
                                orc->AI()->Talk(SAY_BLACKHAND_DOOMED);
                            }
                            orc->m_Events.AddEventAtOffset(new OrcMoveEvent(orc), Ms(kElitesMoveMs));
                            orc->m_Events.AddEventAtOffset(new OrcDeathEvent(orc), Ms(kElitesDieMs));
                        }
                    DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "elites",
                        Acore::StringFormat("count={}", _nearbyOrcs.size()));
                }
                break;
            case DATA_BEAST_REACHED:
                if (!_beastReached)
                {
                    _beastReached = true;
                    me->GetMotionMaster()->MoveWaypoint(BEAST_MOVEMENT_ID, true);
                    DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wake");
                    // A player may have logged in between the triggers (a crash or a restart): run the room part too,
                    // so the second trigger never finds dead Elites yelling.
                    SetData(DATA_BEAST_ROOM, DATA_BEAST_ROOM);
                }
                break;
            default:
                break;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        // The AI's own clock: nothing below waits for a cast bar, and the delayed looks run out of combat too (a
        // `.dbtest` mechanic out of combat).
        _clockMs += diff;
        UpdateLater();
        if (!UpdateVictim())
            return;

        if (me->GetPositionY() > kEvadeLineY)
        {
            EnterEvadeMode(EVADE_REASON_OTHER);     // the stock line: past the hall's far side
            return;
        }

        _pools.Update(me, diff, [this](Player* player, uint32 /*msInside*/) { OnLavaTick(player); });
        UpdatePools();
        UpdateFury(diff);
        UpdateHeat();
        UpdateEruption();
        UpdatePark(diff);

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        RunBeats();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE2 Heat, BE4 Molten Fury
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateHeat()
    {
        while (_clockMs >= _nextHeatMs)
        {
            _nextHeatMs += kHeatEveryMs(_heroic);
            AddHeat();
        }
    }

    void AddHeat()
    {
        _heat = DungeonKit::AddStacks(me, SPELL_BE_HEAT, 1, me);
        me->CastSpell(me, SPELL_BE_HEAT_FLASH, true);
        Talk(TEXT_HEAT);
        _beats.OnHeat(_heat, _clockMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "heat",
            Acore::StringFormat("stacks={} pool={:.1f}yd roar={}s split={}s next@{}s", _heat,
            PoolRadius(_heroic, _heat), RoarEveryMs(_heat) / 1000, SplitEveryMs(_heat) / 1000,
            _nextHeatMs / 1000));
    }

    // Every 250 ms: his own unbroken time in lava, a stack for each 2 s of it.
    void UpdateFury(uint32 diff)
    {
        _furyPollMs += diff;
        if (_furyPollMs < kFuryPollMs)
            return;
        uint32 const dt = _furyPollMs;
        _furyPollMs = 0;
        for (uint32 n = _furyClock.Advance(_pools.Contains(me), dt); n > 0; --n)
            AddFury();
    }

    void AddFury()
    {
        _fury = DungeonKit::AddStacks(me, SPELL_BE_MOLTEN_FURY, 1, me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fury",
            Acore::StringFormat("stacks={} at=({:.1f}, {:.1f})", _fury, me->GetPositionX(), me->GetPositionY()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE3 Molten Blood
    // ----------------------------------------------------------------------------------------------------------------

    struct Pool
    {
        uint32 id = 0;
        Position center;
        float radius = 0.f;
        ObjectGuid stalker;
    };

    // A pool for each 4% of health lost since the last one (a burst lays them 250 ms apart).
    void UpdatePools()
    {
        if (_clockMs < _nextPoolMs)
            return;
        if (PoolsOwed(me->GetHealthPct(), _poolsLaid) == 0)
            return;
        if (PlaceHealthPool())
            _nextPoolMs = _clockMs + kPoolStaggerMs;
        else
            _nextPoolMs = _clockMs + kPoolRetryMs;
    }

    // One pool in a random direction, its near edge 5 yd from him, on the hall or the pit floor, off the old pools when
    // there is room (else the best floor there is). False: no floor found (try again).
    bool PlaceHealthPool()
    {
        float const radius = PoolRadius(_heroic, _heat);
        DungeonKit::FloorSpotRules rules;
        rules.near = DungeonKit::PlaneOf(me);
        rules.minRange = PoolRingYd(radius);
        rules.maxRange = PoolRingYd(radius);
        rules.tries = 48;
        for (Pool const& p : _poolList)
            rules.avoid.push_back({ PlaneOfPoint(p.center), p.radius });
        Arena const arena = PoolArena(radius);
        DungeonKit::FloorProbe probe;
        probe.z = me->GetPositionZ();
        probe.zBand = 4.f;
        probe.probeUp = 3.f;
        std::optional<Position> const spot = DungeonKit::PickFloorSpot(me, &arena, rules, probe);
        if (!spot)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pool-no-floor",
                Acore::StringFormat("owed={} at=({:.1f}, {:.1f})", PoolsOwed(me->GetHealthPct(), _poolsLaid),
                me->GetPositionX(), me->GetPositionY()));
            return false;
        }
        ++_poolsLaid;
        AddPool(*spot, radius, kPoolMarkMs, "blood");
        return true;
    }

    // A pool, `why`: the puddle field (the marker, the union, the damage tick) and its look on a stalker once armed.
    uint32 AddPool(Position const& spot, float radius, uint32 markMs, char const* why)
    {
        DungeonKit::PuddleSpec spec;
        spec.radius = radius;
        spec.armAfter = Ms(markMs);
        spec.merge = false;     // every pool is drawn; the union burns once (the field's tick)
        spec.tag = TAG_POOL;
        DungeonKit::PuddleSet::AddResult const added = _pools.Add(me, spot, spec);
        if (!added.id)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pool-refused", why);
            return 0;
        }
        Pool pool;
        pool.id = added.id;
        pool.center = spot;
        pool.radius = radius;
        if (TempSummon* stalker = me->SummonCreature(NPC_BRS_MOLTEN_BLOOD, spot, TEMPSUMMON_MANUAL_DESPAWN))
        {
            pool.stalker = stalker->GetGUID();
            ObjectGuid const guid = pool.stalker;
            uint32 const look = PoolLookSpell(radius);
            Later(markMs, [this, guid, look]()
            {
                if (Creature* s = me->GetMap()->GetCreature(guid))
                    s->CastSpell(s, look, true);
            });
        }
        _poolList.push_back(pool);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pool",
            Acore::StringFormat("{} id={} at=({:.1f}, {:.1f}) r={:.1f} pools={} floor={:.0f} sq yd", why, added.id,
            spot.GetPositionX(), spot.GetPositionY(), radius, _poolList.size(), _pools.CoveredArea(0.5f)));
        return added.id;
    }

    // Once a second, for each player inside any armed pool: 10% Fire (once however many overlap).
    void OnLavaTick(Player* player)
    {
        me->CastSpell(player, SPELL_BE_MOLTEN_BLOOD, true);
    }

    std::vector<PoolSpot> PoolSpots() const
    {
        std::vector<PoolSpot> out;
        out.reserve(_poolList.size());
        for (Pool const& p : _poolList)
            out.push_back({ PlaneOfPoint(p.center), p.radius });
        return out;
    }

    // The bots' tank rule: lava all around him, so a hidden tank-only Park circle on clean floor draws the boss out
    // (no wall preference: PARTIAL, the framework has none).
    void UpdatePark(uint32 diff)
    {
        _parkCheckMs += diff;
        if (_parkCheckMs < kParkCheckMs)
            return;
        _parkCheckMs = 0;
        if (_clockMs < _parkUntilMs || _poolList.size() < kCrowdPools)
            return;
        std::vector<PoolSpot> const spots = PoolSpots();
        if (!ShouldPark(DungeonKit::PlaneOf(me), spots))
            return;
        Park(spots);
    }

    void Park(std::vector<PoolSpot> const& spots)
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = DungeonKit::PlaneOf(me);
        rules.minRange = kParkMinYd;
        rules.maxRange = kParkMaxYd;
        for (PoolSpot const& p : spots)
            rules.avoid.push_back({ p.center, p.radius });
        rules.avoidMargin = kParkClearYd;
        rules.tries = 48;
        Arena const arena = PoolArena(kParkRadiusYd);
        DungeonKit::FloorProbe probe;
        probe.z = me->GetPositionZ();
        probe.zBand = 4.f;
        probe.probeUp = 3.f;
        std::optional<Position> const spot = DungeonKit::PickFloorSpot(me, &arena, rules, probe);
        _parkUntilMs = _clockMs + kParkHoldMs + kParkCooldownMs;
        if (!spot)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "park", "no clean floor");
            return;
        }
        if (_park)
            Mechanic::Cancel(me, _park);
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Circle(me, *spot, kParkRadiusYd, Ms(kParkHoldMs));
        ref.Park(me).NoTelegraph().Eligible(tankOnly).Within(FightBounds()).Tag(TAG_PARK);
        _park = ref.Handle();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "park",
            Acore::StringFormat("to=({:.1f}, {:.1f}) pools={}", spot->GetPositionX(), spot->GetPositionY(),
            spots.size()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats: the roar, Magma Split, Immolate, the Fire Blast filler
    // ----------------------------------------------------------------------------------------------------------------

    uint32 FireBlastRollMs() const
    {
        return urand(kFireBlastMinMs, kFireBlastMaxMs);
    }

    void RunBeats()
    {
        _beats.DropStale(_clockMs, FireBlastRollMs());
        std::optional<uint32> const next = _beats.Next(_clockMs);
        if (!next)
            return;
        switch (*next)
        {
            case CAST_ROAR:
                StartRoar();
                break;
            case CAST_SPLIT:
                StartMagmaSplit(false);
                break;
            case CAST_IMMOLATE:
                CastImmolate(false);
                break;
            case CAST_FIRE_BLAST:
                DoCastVictim(SPELL_BE_FIRE_BLAST);
                break;
            default:
                break;
        }
        _beats.Started(*next, _clockMs, _heat, FireBlastRollMs());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE5 Dread and Panic
    // ----------------------------------------------------------------------------------------------------------------

    // A 2 s roar (the cast bar and emote line 0) with a Stack for the bots: everyone with fewer than 2 other players
    // within 6 yd at its end gains a Dread stack. No marker on the boss (a ring around him would read as "stand in
    // it"); the bots read the registry, humans the bar, the emote and the Dread tooltip.
    void StartRoar()
    {
        DungeonKit::CastBar(me, SPELL_BE_ROAR, nullptr, TEXT_ROAR);
        BossMechanics::Eligibility who;
        who.playersOnly = true;
        MechanicRef ref = Mechanic::Stack(me, me, kDreadRadiusYd, Ms(kRoarCastMs));
        ref.Cluster(kDreadMinOthers).Eligible(who).NoTelegraph().Tag(TAG_DREAD);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        ref.OnResolve([map, bossGuid, gen](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled)
                return;
            if (boss_the_beast_rework* ai = AIOf(map, bossGuid, gen))
                ai->RoarLanded(result);
        });
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "roar",
            Acore::StringFormat("heat={} next={}s", _heat, RoarEveryMs(_heat) / 1000));
    }

    // The roar ends: every fight player the registry did not list as sheltered gains a stack.
    void RoarLanded(BossMechanics::ResolveResult const& result)
    {
        std::vector<ObjectGuid> const& sheltered = result.hits;
        uint32 alone = 0;
        uint32 panicked = 0;
        for (Player* player : FightPlayers())
        {
            if (std::find(sheltered.begin(), sheltered.end(), player->GetGUID()) != sheltered.end())
                continue;
            ++alone;
            if (AddDread(player))
                ++panicked;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "roar-lands",
            Acore::StringFormat("together={} alone={} panicked={}", sheltered.size(), alone, panicked));
    }

    // +1 Dread; at the threshold it clears and the player panics. True: panic.
    bool AddDread(Player* player)
    {
        uint32 const threshold = kDreadPanicAt(_heroic);
        uint32 const stacks = DungeonKit::AddStacks(player, SPELL_BE_DREAD, 1, me, threshold);
        if (!Panics(stacks, _heroic))
            return false;
        player->RemoveAurasDueToSpell(SPELL_BE_DREAD, me->GetGUID());
        me->CastSpell(player, SPELL_BE_PANIC, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "panic",
            Acore::StringFormat("target={} at=({:.1f}, {:.1f})", player->GetName(), player->GetPositionX(),
            player->GetPositionY()));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE6 Magma Split
    // ----------------------------------------------------------------------------------------------------------------

    // The bots' drop rule for a carrier: the hall's edge and away from the group, off old lava (heroic: onto old
    // lava's edge: its splash pool lands there, on a floor already burning).
    BossMechanics::DropSpotRule SplitDropRule() const
    {
        BossMechanics::DropSpotRule rule;
        rule.Room(HallRoom()).Edge().Away().Within(FightBounds());
        std::size_t preferred = 0;
        for (auto it = _poolList.rbegin(); it != _poolList.rend(); ++it)
        {
            if (_heroic)
            {
                if (preferred++ < kSplitPreferMax)
                    rule.Prefer(it->center, it->radius + 2.5f, 0);
            }
            else
                rule.Avoid(it->center, it->radius);
        }
        return rule;
    }

    // `test`: a solo tester may be the target. True: a cast bar went up.
    bool StartMagmaSplit(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = test;
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, kSplitTargets.At(_players));
        if (targets.empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "split-skipped", "no non-tank");
            return false;
        }
        float const mult = DamageMult(_heat, _fury);
        DungeonKit::CastBar(me, SPELL_BE_MAGMA_SPLIT_BAR);
        std::string who;
        for (Player* target : targets)
        {
            DungeonKit::ImpactSpec impact;
            impact.pct = kSplitOthersPct * mult;
            impact.school = SPELL_SCHOOL_FIRE;
            impact.spellId = SPELL_BE_MAGMA_SPLIT;
            impact.weakened = true;
            impact.tag = TAG_SPLIT;

            Map* map = me->GetMap();
            ObjectGuid const bossGuid = me->GetGUID();
            ObjectGuid const targetGuid = target->GetGUID();
            uint32 const gen = _generation;
            MechanicRef ref = DungeonKit::FollowThenLand(me, target, kSplitRadiusYd, Ms(kSplitCastMs), impact,
                [map, bossGuid, targetGuid, gen, mult](Creature* /*owner*/, Position const& spot,
                    BossMechanics::ResolveResult const& result)
                {
                    if (result.fizzled)
                        return;
                    if (boss_the_beast_rework* ai = AIOf(map, bossGuid, gen))
                        ai->SplitLanded(targetGuid, spot, result, mult);
                });
            if (!ref.IsValid())
            {
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "split-refused", target->GetName());
                continue;
            }
            ref.DropSpot(SplitDropRule());
            who += (who.empty() ? "" : ",") + target->GetName();
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "split",
            Acore::StringFormat("targets={} mult={:.1f} next={}s", who, mult, SplitEveryMs(_heat) / 1000));
        return true;
    }

    // The circle lands where the target stands: its own 15%, the others thrown 5 yd away from it, heroic a 4 yd pool.
    void SplitLanded(ObjectGuid targetGuid, Position const& spot, BossMechanics::ResolveResult const& result,
        float mult)
    {
        for (ObjectGuid const& guid : result.hits)
            Throw(ObjectAccessor::GetUnit(*me, guid), PlaneOfPoint(spot), kSplitKnockYd, kSplitKnockSpeedZ);
        bool targetHit = false;
        if (Player* target = ObjectAccessor::GetPlayer(*me, targetGuid))
            if (target->IsAlive() && target->IsInWorld())
            {
                DungeonKit::RegistryHitSpec spec;
                spec.pct = kSplitTargetPct * mult;
                spec.school = SPELL_SCHOOL_FIRE;
                spec.spellId = SPELL_BE_MAGMA_SPLIT_TARGET;
                spec.weakened = false;
                spec.tag = TAG_SPLIT;
                DungeonKit::RegistryHit(me, GuidSet{ targetGuid }, spec);
                targetHit = true;
            }
        if (_heroic)
            AddPool(spot, kSplitPoolRadiusYd, kSplitPoolMarkMs, "split");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "split-lands",
            Acore::StringFormat("at=({:.1f}, {:.1f}) others={} target={} pool={}", spot.GetPositionX(),
            spot.GetPositionY(), result.hits.size(), targetHit ? 1 : 0, _heroic ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE7 Eruption
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateEruption()
    {
        if (!_erupted)
        {
            if (!EruptionDue(_heroic, _clockMs))
                return;
            StartEruption();
        }
        while (_clockMs >= _nextEruptionTickMs)
        {
            _nextEruptionTickMs += kEruptionTickMs;
            for (Player* player : FightPlayers())
                me->CastSpell(player, SPELL_BE_ERUPTION, true);
        }
    }

    void StartEruption()
    {
        _erupted = true;
        _nextEruptionTickMs = _clockMs + kEruptionTickMs;
        Talk(TEXT_ERUPTION);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "eruption",
            Acore::StringFormat("heat={} fury={} pools={} floor={:.0f} sq yd", _heat, _fury, _poolList.size(),
            _pools.CoveredArea(0.5f)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BE8 Immolate
    // ----------------------------------------------------------------------------------------------------------------

    // Stock 15570 (normal), or the heroic copy (3% a second, a pool where it runs out) on a random player, any role.
    bool CastImmolate(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
            return false;
        if (_heroic)
            me->CastSpell(target, SPELL_BE_IMMOLATE, true);
        else
            DoCast(target, SPELL_BE_IMMOLATE_STOCK);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "immolate",
            Acore::StringFormat("target={} heroic={}{}", target->GetName(), _heroic ? 1 : 0, test ? " test" : ""));
        return true;
    }

    // The heroic copy ran out on a living player (not a dispel, not a death): a 4 yd pool where they stand.
    void ImmolateEnded(Position const& at)
    {
        if (!_heroic || !me->IsEngaged())
            return;
        Position spot = at;
        float const z = me->GetMapHeight(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ() + 2.f);
        if (z > INVALID_HEIGHT + 1.f && std::fabs(z - at.GetPositionZ()) < 4.f)
            spot.Relocate(at.GetPositionX(), at.GetPositionY(), z);
        AddPool(spot, kImmolatePoolRadiusYd, kImmolatePoolMarkMs, "immolate");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data: kill order the boss only, no interrupts, Immolate on the dispel list
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.dispels.emplace_back(_heroic ? static_cast<uint32>(SPELL_BE_IMMOLATE) : SPELL_BE_IMMOLATE_STOCK,
            static_cast<uint8>(_heroic ? 3 : 1));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs beast` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Heat,
        Fury,
        Pool,
        Roar,
        Split,
        Immolate,
        Eruption,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic)
    {
        if (!me->IsEngaged())
            return "The Beast must be in combat (the pools, the roar, the split and the rest run only in the fight).";
        switch (mechanic)
        {
            case TestMechanic::Heat:
                AddHeat();
                break;
            case TestMechanic::Fury:
                AddFury();
                break;
            case TestMechanic::Pool:
                if (!PlaceHealthPool())
                    return "No floor for a pool here (see the `pool-no-floor` log line).";
                break;
            case TestMechanic::Roar:
                StartRoar();
                break;
            case TestMechanic::Split:
                if (!StartMagmaSplit(true))
                    return "No player to aim Magma Split at.";
                break;
            case TestMechanic::Immolate:
                if (!CastImmolate(true))
                    return "No player to Immolate.";
                break;
            case TestMechanic::Eruption:
                if (_erupted)
                    return "The floor has already erupted.";
                StartEruption();
                break;
        }
        return {};
    }

    void TestWake(bool room)
    {
        SetData(room ? DATA_BEAST_ROOM : DATA_BEAST_REACHED, 0);
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        auto at = [this](uint32 id)
        {
            std::optional<uint64> const due = _beats.DueAt(id);
            return due ? Acore::StringFormat("{}s", int64(*due / 1000)) : std::string("-");
        };
        return Acore::StringFormat("clock={}s players={} heroic={} heat={} fury={} pools={} laid={} floor={:.0f} sq yd "
            "inside={} roar@{} split@{} immolate@{} blast@{} eruption@{}s({}) park={} reached={} orcs={}",
            _clockMs / 1000, _players, _heroic ? 1 : 0, _heat, _fury, _poolList.size(), _poolsLaid,
            _pools.CoveredArea(0.5f), _pools.Inside().size(), at(CAST_ROAR), at(CAST_SPLIT), at(CAST_IMMOLATE),
            at(CAST_FIRE_BLAST), kEruptionAtMs(_heroic) / 1000, _erupted ? "on" : "off", _park ? 1 : 0,
            _beastReached ? 1 : 0, _orcYelled ? 1 : 0);
    }

private:
    struct Pending
    {
        uint64 dueMs = 0;
        std::function<void()> fn;
    };

    // The live AI of this boss on `map`, if it is still the same pull (`gen`). Captures are the map and guids only.
    static boss_the_beast_rework* AIOf(Map* map, ObjectGuid bossGuid, uint32 gen)
    {
        Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<boss_the_beast_rework*>(boss->AI());
        return ai && ai->_generation == gen ? ai : nullptr;
    }

    // The players the fight counts: on his threat list, alive, in the world, not game masters.
    std::vector<Player*> FightPlayers()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = 300.f;
        return DungeonKit::PickPlayers(me, rule, 40);
    }

    static void Throw(Unit* unit, Vec2 source, float distance, float speedZ)
    {
        if (unit && unit->IsAlive())
            unit->KnockbackFrom(source.x, source.y, KnockbackSpeedXY(distance, speedZ), speedZ);
    }

    void FindNearbyOrcs()
    {
        std::list<Creature*> found;
        me->GetCreatureListWithEntryInGrid(found, NPC_BLACKHAND_ELITE, kElitesFindYd);
        for (Creature* creature : found)
            if (creature->IsAlive())
                _nearbyOrcs.push_back(creature->GetGUID());
    }

    // `fn` after `delayMs` on the AI's own clock (in or out of combat); a Cleanup drops what is pending.
    void Later(uint32 delayMs, std::function<void()> fn)
    {
        _later.push_back({ _clockMs + delayMs, std::move(fn) });
    }

    void UpdateLater()
    {
        if (_later.empty())
            return;
        std::vector<Pending> due;
        for (auto it = _later.begin(); it != _later.end();)
        {
            if (_clockMs >= it->dueMs)
            {
                due.push_back(std::move(*it));
                it = _later.erase(it);
            }
            else
                ++it;
        }
        for (Pending& p : due)
            p.fn();
    }

    // The pull's state: no pools, stalkers, Heat, Fury, Dread, Panic, Immolate or pending look (Reset, evade, death, a
    // new pull). The wake state (_beastReached, _orcYelled) is the world's, not the pull's: it stays.
    void Cleanup()
    {
        ++_generation;      // callbacks of an older pull stop
        _pools.Clear(me);
        _poolList.clear();
        summons.DespawnAll();
        _later.clear();
        if (_park)
            Mechanic::Cancel(me, _park);
        _park = {};
        me->RemoveAurasDueToSpell(SPELL_BE_HEAT);
        me->RemoveAurasDueToSpell(SPELL_BE_MOLTEN_FURY);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                {
                    p->RemoveAurasDueToSpell(SPELL_BE_DREAD, me->GetGUID());
                    p->RemoveAurasDueToSpell(SPELL_BE_PANIC, me->GetGUID());
                    p->RemoveAurasDueToSpell(SPELL_BE_IMMOLATE, me->GetGUID());
                    p->RemoveAurasDueToSpell(SPELL_BE_IMMOLATE_STOCK, me->GetGUID());
                }
        _beats.Reset();
        _furyClock.Reset();
        _clockMs = 0;
        _nextHeatMs = kHeatEveryMs(false);
        _nextPoolMs = 0;
        _nextEruptionTickMs = 0;
        _furyPollMs = 0;
        _parkCheckMs = 0;
        _parkUntilMs = 0;
        _heat = 0;
        _fury = 0;
        _poolsLaid = 0;
        _erupted = false;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::PuddleField _pools;
    Beats _beats;
    FuryClock _furyClock;
    std::vector<Pool> _poolList;
    std::vector<Pending> _later;
    GuidVector _nearbyOrcs;
    MechanicHandle _park;
    uint64 _clockMs = 0;            // ms since the pull: every timer of the fight
    uint64 _nextHeatMs = 0;
    uint64 _nextPoolMs = 0;
    uint64 _nextEruptionTickMs = 0;
    uint64 _parkUntilMs = 0;
    uint32 _furyPollMs = 0;
    uint32 _parkCheckMs = 0;
    uint32 _generation = 0;
    uint32 _heat = 0;               // Heat stacks
    uint32 _fury = 0;               // Molten Fury stacks
    uint32 _poolsLaid = 0;          // health pools laid (the 4% pools only)
    uint8 _players = 0;             // the flex count held at the pull (5..10)
    bool _heroic = false;
    bool _erupted = false;
    bool _beastReached = false;     // the stock wake flags
    bool _orcYelled = false;
};

// Molten Blood (300735): an invisible prop that carries one pool's lava look (210502-210508 by radius).
struct npc_brs_molten_blood : public NullCreatureAI
{
    explicit npc_brs_molten_blood(Creature* creature) : NullCreatureAI(creature) { }
};

// BE8 the heroic Immolate (210500): when it runs out on a living player a pool lies where they stand; a dispel, a death
// or a map change leaves none. The tick is the kit's spell_dungeon_refflat_periodic (bound beside this one).
class spell_brs_beast_immolate : public AuraScript
{
    PrepareAuraScript(spell_brs_beast_immolate);

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        AuraApplication const* application = GetTargetApplication();
        if (!application || application->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;
        Unit* target = GetTarget();
        Unit* caster = GetCaster();
        Creature* boss = caster ? caster->ToCreature() : nullptr;
        if (!target || !target->IsAlive() || !boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return;
        if (auto* ai = dynamic_cast<boss_the_beast_rework*>(boss->AI()))
            ai->ImmolateEnded(target->GetPosition());
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_brs_beast_immolate::OnRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

namespace
{
    boss_the_beast_rework* FindBeastAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_BEAST);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_the_beast_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Beast is not running boss_the_beast_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_the_beast_rework::TestMechanic mechanic, char const* what)
    {
        boss_the_beast_rework* ai = FindBeastAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("The Beast: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_BEAST, BOSS_BEAST);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_the_beast_rework* ai = FindBeastAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("The Beast: {}", ai->TestState());
        return true;
    }

    bool HandleHeat(ChatHandler* handler)
    {
        return Fire(handler, boss_the_beast_rework::TestMechanic::Heat, "a Heat stack (BE2)");
    }

    bool HandleFury(ChatHandler* handler)
    {
        return Fire(handler, boss_the_beast_rework::TestMechanic::Fury, "a Molten Fury stack (BE4)");
    }

    bool HandlePool(ChatHandler* handler)
    {
        return Fire(handler, boss_the_beast_rework::TestMechanic::Pool, "a Molten Blood pool (BE3: 5 yd off him)");
    }

    bool HandleRoar(ChatHandler* handler)
    {
        return Fire(handler, boss_the_beast_rework::TestMechanic::Roar, "the Dread roar (BE5)");
    }

    bool HandleSplit(ChatHandler* handler)
    {
        return Fire(handler, boss_the_beast_rework::TestMechanic::Split, "Magma Split (BE6; `.gm off` to be picked)");
    }

    bool HandleImmolate(ChatHandler* handler)
    {
        return Fire(handler, boss_the_beast_rework::TestMechanic::Immolate, "Immolate (BE8)");
    }

    bool HandleEruption(ChatHandler* handler)
    {
        return Fire(handler, boss_the_beast_rework::TestMechanic::Eruption, "the Eruption (BE7: 10% a second)");
    }

    // `.dbtest brs beast wake`: the first area trigger (the walk out of the pit); `elites`: the second (the panic).
    bool HandleWake(ChatHandler* handler)
    {
        boss_the_beast_rework* ai = FindBeastAI(handler);
        if (!ai)
            return false;
        ai->TestWake(false);
        handler->PSendSysMessage("The Beast: the wake (area trigger 2066) run.");
        return true;
    }

    bool HandleElites(ChatHandler* handler)
    {
        boss_the_beast_rework* ai = FindBeastAI(handler);
        if (!ai)
            return false;
        ai->TestWake(true);
        handler->PSendSysMessage("The Beast: the Elites' panic (area trigger 2067) run.");
        return true;
    }

    // `.dbtest brs beast <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BeastTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "heat",     HandleHeat,     SEC_GAMEMASTER, Console::No },
            { "fury",     HandleFury,     SEC_GAMEMASTER, Console::No },
            { "pool",     HandlePool,     SEC_GAMEMASTER, Console::No },
            { "roar",     HandleRoar,     SEC_GAMEMASTER, Console::No },
            { "split",    HandleSplit,    SEC_GAMEMASTER, Console::No },
            { "immolate", HandleImmolate, SEC_GAMEMASTER, Console::No },
            { "eruption", HandleEruption, SEC_GAMEMASTER, Console::No },
            { "wake",     HandleWake,     SEC_GAMEMASTER, Console::No },
            { "elites",   HandleElites,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_the_beast_rework()
{
    // The boss AI binds only once wave 2 does (an unbound registered name logs "not assigned" at boot); the stalker and
    // the spell are declared now, so their scripts register now.
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_the_beast_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_molten_blood, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_beast_immolate);
    BrsTest::RegisterBoss("beast", BeastTestCommands());
}
