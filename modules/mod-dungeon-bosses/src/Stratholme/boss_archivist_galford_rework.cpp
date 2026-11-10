/*
 * mod-dungeon-bosses, Stratholme S6: Archivist Galford (10811), "the Crusade burns heresy, and you are the heresy"
 * (ruling 25). Build spec ST 1707-1765 (docs/dungeons/stratholme-rework.md, the whole "Archivist Galford" section),
 * handoff sections 3.4 rows GF, 3.5 row S6, 3.6 and 3.8. Replaces his SmartAI (Burning Winds 17293, Fire Nova 17366,
 * Pyroblast 17274: data/sql/updates/pending_db_world/rev_archivist_galford_stratholme.sql drops it); bound by
 * apps/dbc-tools source/npcs/stratholme/archivist_galford.py. Pure rules: GalfordLogic.h.
 *
 *   GF1  Holy Fire       5 s, then every 8 s (heroic: three different non-tanks every 12 s): a 6 s burn (206520, 10%,
 *                        no dispel type) on a random non-tank; a 4 yd circle follows them (DungeonKit::FollowThenLand)
 *                        with X2's drop spot rule for a bot carrier: onto the rim of old fire, the archive or the
 *                        alcove, else the hall's edge, behind the group's march north, away from it
 *   GF2  The landing     where they stand when the burn ends: 30% Holy + Weakened to anyone else inside (206521), then
 *                        a 4 yd puddle
 *   GF3  Pyroblast       15 s, then every 20 s: a 4 s kickable cast at the tank (206522; descriptor priority 3), 35% /
 *                        45% of the tank row (x 1.25 while Kindled); a telegraph-only circle of the puddle-to-be
 *                        follows the tank with the same drop spot rule (X2: a tank carrier gets the rule, not Park)
 *   GF4  Its puddle      6 / 8 yd where the tank stands when it hits; a kick stops both
 *   GF5  Fire Nova       12 s, then every 15 s: a 2 s cast (206523, emote line 1) and a 10 yd circle on him, the tank
 *                        too: 30% Fire + Weakened (206524)
 *   GF6  Its puddle      5 yd under his feet at the burst
 *   GF7  Holy fire       every puddle stays until he dies or the group wipes (DungeonKit::PuddleField: telegraph-only
 *                        persistent zones, armed 1 s after they land); once a second each player in any of them takes
 *                        8% x (1 + 0.25 per Scorched stack), however many overlap (206526)
 *   GF8  Scorched        a stack per tick (206527); all fall off 4 s after leaving the fire
 *   GF9  Kindled         while he stands in armed fire (206528): +25% damage done, -50% damage taken (yell line 2 the
 *                        first time). The bots' tank rule: a hidden tank-only Park circle on clean floor when he stands
 *                        in or by a puddle
 *   GF10 The walls       at the pull the Pyre (the hall's south end, x 3444) and the north wall (x 3500) light: KT-2's
 *                        DungeonKit::LethalWall on X4's never-cross, the shared strike 206400, armed 2 s after the pull
 *                        grip (section 10); a row of Pyre stalkers (300607) carries the fire and delivers the strike
 *   GF11 Burning Winds   heroic, 20 s, then every 25 s: a 2 s cast (206529, yell line 5); while he casts every puddle
 *                        reaches 8 yd north as a telegraph-only zone; then everyone is thrown 8 yd south (no damage),
 *                        each throw cut 2 yd short of the Pyre's strip (KT-2: a wall strikes any crossing,
 *                        knockbacks included; GalfordLogic.h GustDistance)
 *   Arena                StratholmeRework::LeashOptions on GalfordLogic.h GuardArena() with the pull grip (section
 *                        10: only The Unforgiven and Galford grip, once): a unit off the arena at the pull lands on the
 *                        nearest of four measured spots 7 yd or more inside the walls; no grip back
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler (a cast bar pauses that one): Holy Fire, the fire
 * ticks, Kindled, the Park and the gust keep running through his casts. His casts go through a DungeonKit::CastQueue.
 * Every firing logs one INFO line "strat galford <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitWalls.h"
#include "GalfordLogic.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratGalford;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "galford";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    bool CountsAsPlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }

    Position At(Vec2 p, float z)
    {
        return Position(p.x, p.y, z, 0.f);
    }

    std::vector<Position> HallRoomPositions()
    {
        std::vector<Position> out;
        out.reserve(kHallRoom.size());
        for (Vec2 const& p : kHallRoom)
            out.push_back(At(p, kHallFloorZ));
        return out;
    }

    // Where a bot may plan to stand for his mechanics: the hall, the archive's drop area and the alcove (F-1b).
    BossMechanics::SpotBounds FightBounds()
    {
        BossMechanics::SpotBounds b;
        b.Polygon(HallRoomPositions(), kHallZMin, kHallZMax);
        b.Rect(kArchiveDrop.minX, kArchiveDrop.minY, kArchiveDrop.maxX, kArchiveDrop.maxY, kHallZMin, kHallZMax);
        b.Rect(kAlcoveDrop.minX, kAlcoveDrop.minY, kAlcoveDrop.maxX, kAlcoveDrop.maxY, kHallZMin, kHallZMax);
        return b;
    }

    // The leash, plus the pull grip (section 10) onto the measured landings, nearest first.
    DungeonKit::ArenaGuardOptions GuardOptions()
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(kBossLogName);
        o.gripOnPull = true;
        o.gripBack = false;
        o.maxGripYd = kPullRadiusYd;    // the pull's reach (JustEngagedWith): no one in combat beyond the grip
        o.landing = [](Creature const* /*boss*/, Unit const* unit)
        {
            return At(GripLanding(DungeonKit::PlaneOf(unit)), kHallFloorZ);
        };
        return o;
    }
}

// Archivist Galford 10811
struct boss_archivist_galford_rework : public BossAI
{
    explicit boss_archivist_galford_rework(Creature* creature)
        : BossAI(creature, BOSS_GALFORD), _arena(GuardArena(), GuardOptions()), _fire(Ms(kFireTickMs)) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    // Not BossAI::JustEngagedWith: its zone-in and its 5 s combat pulse reach 250 yd, past the pull grip (F-2
    // ruling: the pull reaches as far as the grip, kPullRadiusYd). The rest is BossAI's: active, the required
    // bosses, IN_PROGRESS.
    void JustEngagedWith(Unit* /*who*/) override
    {
        me->setActive(true);
        DoZoneInCombat(me, kPullRadiusYd);
        if (instance)
        {
            if (!instance->CheckRequiredBosses(BOSS_GALFORD))
            {
                EnterEvadeMode(EVADE_REASON_OTHER);
                return;
            }
            instance->SetBossState(BOSS_GALFORD, IN_PROGRESS);
        }
        if (!me->IsEngaged())
            return;     // evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GALFORD;
        Mechanic::BeginEncounter(me, options);
        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        Describe();
        _arena.Engage(me);      // the pull grip first: the walls arm 2 s after it (section 10)
        RaiseWalls();

        _nextHolyFireMs = kHolyFireFirstMs;
        _queue.Schedule(CAST_PYROBLAST, kPyroFirstMs, kPriorityPyro);
        _queue.Schedule(CAST_NOVA, kNovaFirstMs, kPriorityNova);
        if (_heroic)
            _queue.Schedule(CAST_WINDS, kWindsFirstMs, kPriorityWinds);
        Mechanic::NoteNextCastIn(me, SPELL_GF_PYROBLAST, Ms(kPyroFirstMs));
        Talk(YELL_GALFORD_AGGRO);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) walls={}", _heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ(), _walls.Count()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_GALFORD_DEATH);
        BossAI::JustDied(killer);   // DONE (heroic: the instance lays the Letter of Proof), the summons despawn
        std::size_t const puddles = _puddles.size();
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("puddles={} killer={}", puddles, killer ? killer->GetName() : "none"));
    }

    // The puddle and wall stalkers are props: never zoned into combat (BossAI::JustSummoned would).
    void JustSummoned(Creature* summon) override
    {
        if (summon->GetEntry() == NPC_ST_HOLY_FIRE_PUDDLE || summon->GetEntry() == NPC_ST_PYRE_WALL)
        {
            summons.Summon(summon);
            return;
        }
        BossAI::JustSummoned(summon);
    }

    // GF4: the Pyroblast hit leaves its puddle where the tank stands.
    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (spell->Id != SPELL_GF_PYROBLAST || !_pyro || !target)
            return;
        Position const spot = target->GetPosition();
        bool const kindled = me->HasAura(SPELL_GF_KINDLED);
        EndPyro();
        AddPuddle(spot, kPyroPuddleRadius(_heroic), "pyroblast");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pyroblast-lands",
            Acore::StringFormat("target={} pct={:.2f} at=({:.1f}, {:.1f})", target->GetName(),
                PyroPct(_heroic, kindled), spot.GetPositionX(), spot.GetPositionY()));
    }

    // GF3: a kick stops the hit and the puddle.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id != SPELL_GF_PYROBLAST)
            return;
        _queue.Interrupted(_clockMs);
        if (_pyro)
        {
            EndPyro();
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pyroblast-interrupted");
        }
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        _fire.Update(me, diff, [this](Player* player, uint32 /*msInside*/) { OnFireTick(player); });
        UpdateKindled(diff);
        UpdatePark(diff);
        UpdatePyro();
        UpdateWinds();

        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_clockMs >= _nextHolyFireMs)
        {
            _nextHolyFireMs = _clockMs + kHolyFireEveryMs(_heroic);
            StartHolyFire(false);
        }

        StartQueuedCast();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The cast queue: Pyroblast, Fire Nova, Burning Winds never overlap
    // ----------------------------------------------------------------------------------------------------------------

    void StartQueuedCast()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING) || _pyro || _windsAt)
            return;
        std::optional<uint32> const next = _queue.Next(_clockMs);
        if (!next)
            return;
        switch (*next)
        {
            case CAST_PYROBLAST:
                _queue.Schedule(CAST_PYROBLAST, _clockMs + kPyroEveryMs, kPriorityPyro);
                if (StartPyroblast())
                    _queue.Started(CAST_PYROBLAST, _clockMs, kPyroCastMs);
                break;
            case CAST_NOVA:
                _queue.Started(CAST_NOVA, _clockMs, kNovaCastMs);
                _queue.Schedule(CAST_NOVA, _clockMs + kNovaEveryMs, kPriorityNova);
                StartNova();
                break;
            case CAST_WINDS:
                _queue.Started(CAST_WINDS, _clockMs, kWindsCastMs);
                _queue.Schedule(CAST_WINDS, _clockMs + kWindsEveryMs, kPriorityWinds);
                StartWinds();
                break;
            default:
                _queue.Cancel(*next);
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF7 the puddles
    // ----------------------------------------------------------------------------------------------------------------

    struct Puddle
    {
        uint32 id = 0;
        Position center;
        float radius = 0.f;
        ObjectGuid stalker;
    };

    void AddPuddle(Position const& spot, float radius, char const* why)
    {
        DungeonKit::PuddleSpec spec;
        spec.radius = radius;
        spec.armAfter = Ms(kFireArmMs);
        spec.merge = false;     // every puddle is drawn; the union burns once (the field's tick)
        spec.tag = TAG_FIRE;
        DungeonKit::PuddleSet::AddResult const added = _fire.Add(me, spot, spec);
        if (!added.id)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "puddle-refused", why);
            return;
        }
        Puddle puddle{ added.id, spot, radius, ObjectGuid::Empty };
        if (TempSummon* stalker = me->SummonCreature(NPC_ST_HOLY_FIRE_PUDDLE, spot, TEMPSUMMON_MANUAL_DESPAWN))
        {
            stalker->CastSpell(stalker, PuddleLookFor(radius), true);
            puddle.stalker = stalker->GetGUID();
        }
        _puddles.push_back(puddle);
        if (!_yelledArchive && kArchiveRoom.Contains({ spot.GetPositionX(), spot.GetPositionY() }))
        {
            _yelledArchive = true;
            Talk(YELL_GALFORD_ARCHIVE);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "puddle",
            Acore::StringFormat("{} id={} at=({:.1f}, {:.1f}) r={:.0f} puddles={} floor={:.0f}", why, added.id,
                spot.GetPositionX(), spot.GetPositionY(), radius, _puddles.size(), _fire.CoveredArea(0.5f)));
    }

    // GF7 / GF8: once a second for each player inside the union of armed puddles. The tick reads the Scorched stacks
    // at launch (spell_st_galford_holy_fire_tick), then the stack is added.
    void OnFireTick(Player* player)
    {
        me->CastSpell(player, SPELL_GF_HOLY_FIRE_TICK, true);
        DungeonKit::AddStacks(player, SPELL_GF_SCORCHED, 1, me, kScorchedMaxStacks);
    }

    std::vector<PuddleSpot> PuddleSpots() const
    {
        std::vector<PuddleSpot> out;
        out.reserve(_puddles.size());
        for (Puddle const& p : _puddles)
            out.push_back({ { p.center.GetPositionX(), p.center.GetPositionY() }, p.radius });
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF9 Kindled and the tank rule
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateKindled(uint32 diff)
    {
        _kindledPollMs += diff;
        if (_kindledPollMs < kKindledPollMs)
            return;
        _kindledPollMs = 0;
        bool const inFire = _fire.Contains(me);
        if (inFire)
            me->CastSpell(me, SPELL_GF_KINDLED, true);   // 1 s: refreshed while he stands in it
        if (inFire == _kindled)
            return;
        _kindled = inFire;
        if (inFire && !_yelledKindled)
        {
            _yelledKindled = true;
            Talk(YELL_GALFORD_KINDLED);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, inFire ? "kindled" : "kindled-ends",
            Acore::StringFormat("at=({:.1f}, {:.1f})", me->GetPositionX(), me->GetPositionY()));
    }

    // The bots' tank rule: he stands in or by a puddle: a hidden tank-only Park circle on clean hall floor. Never
    // while a Pyroblast puddle-to-be rides the tank (X2: a tank carrier gets the drop rule, not Park).
    void UpdatePark(uint32 diff)
    {
        _parkCheckMs += diff;
        if (_parkCheckMs < kParkCheckMs)
            return;
        _parkCheckMs = 0;
        if (_pyro || _clockMs < _parkUntilMs)
            return;
        std::vector<PuddleSpot> const spots = PuddleSpots();
        if (!ShouldPark(DungeonKit::PlaneOf(me), spots))
            return;
        Park();
    }

    bool Park()
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = DungeonKit::PlaneOf(me);
        rules.minRange = kParkMinYd;
        rules.maxRange = kParkMaxYd;
        for (Puddle const& p : _puddles)
            rules.avoid.push_back({ { p.center.GetPositionX(), p.center.GetPositionY() }, p.radius });
        rules.avoidMargin = kParkClearYd;
        DungeonKit::FloorProbe probe;
        probe.z = kHallFloorZ;
        probe.reachable = true;
        DungeonKit::Arena const hall(DungeonKit::ArenaRegion::Polygon(
            std::vector<Vec2>(kHallRoom.begin(), kHallRoom.end()), kHallZMin, kHallZMax));
        std::optional<Position> const spot = DungeonKit::PickFloorSpot(me, &hall, rules, probe);
        _parkUntilMs = _clockMs + kParkHoldMs + kParkCooldownMs;
        if (!spot || !InHallRoom({ spot->GetPositionX(), spot->GetPositionY() }))
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "park", "no clean floor");
            return false;
        }
        if (_park)
            Mechanic::Cancel(me, _park);
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Circle(me, *spot, kParkRadius, Ms(kParkHoldMs));
        ref.Park(me).NoTelegraph().Eligible(tankOnly).Within(FightBounds()).Tag(TAG_PARK);
        _park = ref.Handle();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "park",
            Acore::StringFormat("to=({:.1f}, {:.1f}) puddles={}", spot->GetPositionX(), spot->GetPositionY(),
                _puddles.size()));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF1 / GF2 Holy Fire
    // ----------------------------------------------------------------------------------------------------------------

    struct Carrier
    {
        ObjectGuid target;
        uint64 landAt = 0;
        MechanicHandle handle;
    };

    // X2's drop spot rule for a carrier bot (Holy Fire's target, Pyroblast's tank): the rim of old fire (it lands
    // overlapping it, never inside), the archive or the alcove, else the hall's edge; behind the march north (bearing
    // 0), away from the group; always inside the fight's floor.
    BossMechanics::DropSpotRule DropRule() const
    {
        BossMechanics::DropSpotRule rule;
        rule.Room(HallRoomPositions()).Edge().Behind(0.f).Away().Within(FightBounds());
        for (Puddle const& p : _puddles)
            rule.Prefer(p.center, p.radius + kDropRimReachYd, 0);
        rule.Prefer(At(kArchiveDrop.Center(), 137.0f), kDropRoomPreferYd, 0);
        rule.Prefer(At(kAlcoveDrop.Center(), 137.0f), kDropRoomPreferYd, 0);
        return rule;
    }

    GuidSet Busy() const
    {
        GuidSet busy;
        for (Carrier const& c : _carriers)
            busy.insert(c.target);
        return busy;
    }

    // `test`: a solo tester may be the target. Returns the number of burns started.
    uint32 StartHolyFire(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = test;
        DungeonKit::ExcludeGuids(rule, Busy());
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, kHolyFireCount(_heroic));
        uint32 started = 0;
        for (Player* target : targets)
        {
            DungeonKit::ImpactSpec impact;
            impact.pct = kHolyFireLandingPct;
            impact.school = SPELL_SCHOOL_HOLY;
            impact.spellId = SPELL_GF_HOLY_FIRE_LANDING;
            impact.weakened = true;
            impact.tag = TAG_HOLY_FIRE;

            Map* map = me->GetMap();
            ObjectGuid const bossGuid = me->GetGUID();
            ObjectGuid const targetGuid = target->GetGUID();
            uint32 const gen = _generation;
            MechanicRef ref = DungeonKit::FollowThenLand(me, target, kHolyFireRadius, Ms(kHolyFireBurnMs), impact,
                [map, bossGuid, targetGuid, gen](Creature* /*owner*/, Position const& spot,
                    BossMechanics::ResolveResult const& result)
                {
                    if (result.fizzled)
                        return;
                    if (boss_archivist_galford_rework* ai = AIOf(map, bossGuid, gen))
                        ai->HolyFireLanded(targetGuid, spot, result.hits.size());
                });
            if (!ref.IsValid())
            {
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-fire-refused", target->GetName());
                continue;
            }
            ref.DropSpot(DropRule());
            _carriers.push_back({ targetGuid, _clockMs + kHolyFireBurnMs, ref.Handle() });
            me->CastSpell(target, SPELL_GF_HOLY_FIRE, true);
            ++started;
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-fire",
                Acore::StringFormat("heroic={} target={} puddles={}", _heroic ? 1 : 0, target->GetName(),
                    _puddles.size()));
        }
        if (!started)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-fire-skipped", "no non-tank");
        return started;
    }

    void HolyFireLanded(ObjectGuid targetGuid, Position const& spot, std::size_t hits)
    {
        std::erase_if(_carriers, [targetGuid](Carrier const& c) { return c.target == targetGuid; });
        AddPuddle(spot, kHolyFireRadius, "holy-fire");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "holy-fire-lands",
            Acore::StringFormat("at=({:.1f}, {:.1f}) others={}", spot.GetPositionX(), spot.GetPositionY(), hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF3 / GF4 Pyroblast
    // ----------------------------------------------------------------------------------------------------------------

    struct Pyro
    {
        ObjectGuid target;
        uint64 giveUpAt = 0;
        MechanicHandle marker;
    };

    bool StartPyroblast()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        if (me->CastSpell(victim, SPELL_GF_PYROBLAST, false) != SPELL_CAST_OK)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pyroblast-refused", victim->GetName());
            return false;
        }
        Mechanic::NoteNextCastIn(me, SPELL_GF_PYROBLAST, Ms(kPyroEveryMs));
        // The puddle-to-be on the tank: telegraph-only, follows them through the cast; the tank's drop spot rule.
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(victim, kPyroPuddleRadius(_heroic)),
            Ms(kPyroCastMs + kPyroMarkerTailMs));
        ref.Tag(TAG_PYROBLAST);
        if (victim->IsPlayer())
            ref.DropSpot(DropRule());
        _pyro = Pyro{ victim->GetGUID(), _clockMs + kPyroCastMs + kPyroLandGraceMs, ref.Handle() };
        if (PyroYells(++_pyroCasts))
            Talk(YELL_GALFORD_PYROBLAST);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pyroblast",
            Acore::StringFormat("heroic={} target={} cast={}ms", _heroic ? 1 : 0, victim->GetName(), kPyroCastMs));
        return true;
    }

    void EndPyro()
    {
        if (_pyro)
            Mechanic::Cancel(me, _pyro->marker);
        _pyro.reset();
    }

    // A hit that never came (the tank died mid-flight, the missile was lost): free the marker and the queue.
    void UpdatePyro()
    {
        if (_pyro && _clockMs >= _pyro->giveUpAt)
        {
            EndPyro();
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pyroblast-lost");
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF5 / GF6 Fire Nova
    // ----------------------------------------------------------------------------------------------------------------

    void StartNova()
    {
        DungeonKit::CastBar(me, SPELL_GF_FIRE_NOVA_CAST, nullptr, EMOTE_GALFORD_FIRE_NOVA);
        MechanicRef ref = Mechanic::Circle(me, me, kNovaRadius, Ms(kNovaCastMs));
        ref.Damage(kNovaPct).TankDamage(kNovaPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_GF_FIRE_NOVA).Weakened()
            .Tag(TAG_NOVA);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        ref.OnResolve([map, bossGuid, gen](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled)
                return;
            if (boss_archivist_galford_rework* ai = AIOf(map, bossGuid, gen))
                ai->NovaLanded(result.hits.size());
        });
        _nova = ref.Handle();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fire-nova",
            Acore::StringFormat("pct={:.0f} radius={:.0f}", kNovaPct, kNovaRadius));
    }

    void NovaLanded(std::size_t hits)
    {
        _nova = {};
        me->CastSpell(me, SPELL_GF_FIRE_NOVA_LOOK, true);
        AddPuddle(me->GetPosition(), kNovaPuddleRadius, "fire-nova");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fire-nova-lands", Acore::StringFormat("hits={}", hits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF11 Burning Winds (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void StartWinds()
    {
        DungeonKit::CastBar(me, SPELL_GF_BURNING_WINDS, nullptr, YELL_GALFORD_BURNING_WINDS);
        // Each puddle reaches 8 yd north while he casts (the bots stand where the throw lands on clean floor): a
        // line north from its center as wide as the puddle, plus the puddle shifted 8 yd north. Telegraph-only.
        std::size_t n = 0;
        for (Puddle const& p : _puddles)
        {
            if (n++ >= kWindsMaxPuddles)
                break;
            MechanicRef line = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(p.center, kWindsShiftFacing,
                kWindsPushYd, p.radius * 2.f), Ms(kWindsCastMs));
            line.NoFillTimer().Tag(TAG_WINDS);
            _windsShapes.push_back(line.Handle());
            Position const shifted(p.center.GetPositionX() + kWindsPushYd, p.center.GetPositionY(),
                p.center.GetPositionZ(), 0.f);
            MechanicRef circle = Mechanic::Zone(me, BossMechanics::Shapes::Circle(shifted, p.radius),
                Ms(kWindsCastMs));
            circle.NoFillTimer().Tag(TAG_WINDS);
            _windsShapes.push_back(circle.Handle());
        }
        _windsAt = _clockMs + kWindsCastMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "burning-winds",
            Acore::StringFormat("puddles={} shapes={}", _puddles.size(), _windsShapes.size()));
    }

    void UpdateWinds()
    {
        if (!_windsAt || _clockMs < *_windsAt)
            return;
        _windsAt.reset();
        _windsShapes.clear();   // they resolve (telegraph-only) with the cast
        Gust();
    }

    // Everyone on his arena is thrown south, each throw cut short of the Pyre (GustDistance; the wall would strike
    // a throw across it).
    uint32 Gust()
    {
        uint32 thrown = 0;
        uint32 held = 0;
        DungeonKit::Arena const arena = GuardArena();
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!CountsAsPlayer(player) || !arena.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                continue;
            float const d = GustDistance(player->GetPositionX());
            if (d <= 0.f)
            {
                ++held;
                continue;
            }
            me->CastSpell(player, SPELL_GF_GUST, true);
            player->KnockbackFrom(player->GetPositionX() + 1.f, player->GetPositionY(), KnockbackSpeedXY(d),
                kGustSpeedZ);
            ++thrown;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "gust",
            Acore::StringFormat("thrown={} held-at-pyre={}", thrown, held));
        return thrown;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // GF10 the walls
    // ----------------------------------------------------------------------------------------------------------------

    void RaiseWalls()
    {
        RaiseWall(PyreLine(), kPyreFloorZ, "pyre");
        RaiseWall(NorthLine(), kNorthFloorZ, "north");
    }

    void RaiseWall(WallLine const& line, float z, char const* which)
    {
        DungeonKit::LethalWallSpec spec;
        spec.from = At(line.from, z);
        spec.to = At(line.to, z);
        spec.width = line.width;
        spec.killSpell = SPELL_ST_CROSSED_THE_LINE;
        spec.tag = TAG_WALL;
        spec.dungeon = kLogDungeon;
        spec.boss = kBossLogName;
        float const facing = std::atan2(line.to.y - line.from.y, line.to.x - line.from.x);
        for (Vec2 const& p : WallStalkerSpots(line))
            if (TempSummon* stalker = me->SummonCreature(NPC_ST_PYRE_WALL, Position(p.x, p.y, z, facing),
                TEMPSUMMON_MANUAL_DESPAWN))
            {
                stalker->CastSpell(stalker, SPELL_GF_WALL_LOOK, true);
                spec.strikers.push_back(stalker->GetGUID());
            }
        MechanicHandle const handle = _walls.Add(me, spec);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "wall",
            Acore::StringFormat("{} ok={} stalkers={} from=({:.1f}, {:.1f}) to=({:.1f}, {:.1f})", which,
                handle.IsValid() ? 1 : 0, spec.strikers.size(), line.from.x, line.from.y, line.to.x, line.to.y));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): interrupt Pyroblast; no dispels; kill order him
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_GALFORD, 0, Who::Any);
        d.ignores.emplace_back(NPC_ST_HOLY_FIRE_PUDDLE);
        d.ignores.emplace_back(NPC_ST_PYRE_WALL);
        d.interrupts.emplace_back(NPC_GALFORD, SPELL_GF_PYROBLAST, kPyroKickPriority, Ms(kPyroEveryMs));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat galford` entry points (`heroic` forces the heroic form until the next pull)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        HolyFire,
        Pyroblast,
        Nova,
        Winds,
        Gust,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged())
            return "Galford must be in combat (the fire, the walls and the timers run only in the fight).";
        _heroic = heroic;
        if (mechanic == TestMechanic::HolyFire)
            return StartHolyFire(true) ? std::string() : "No target for Holy Fire.";
        if (mechanic == TestMechanic::Gust)
        {
            Gust();
            return {};
        }
        if (me->HasUnitState(UNIT_STATE_CASTING) || _pyro || _windsAt)
            return "Galford is casting; try again in a moment.";
        switch (mechanic)
        {
            case TestMechanic::Pyroblast:
                if (!StartPyroblast())
                    return "Pyroblast was refused (no victim, or out of range).";
                _queue.Started(CAST_PYROBLAST, _clockMs, kPyroCastMs, false);
                break;
            case TestMechanic::Nova:
                StartNova();
                _queue.Started(CAST_NOVA, _clockMs, kNovaCastMs, false);
                break;
            case TestMechanic::Winds:
                StartWinds();
                _queue.Started(CAST_WINDS, _clockMs, kWindsCastMs, false);
                break;
            default:
                break;
        }
        return {};
    }

    std::string TestPuddle(Position const& at, float radius)
    {
        if (!me->IsEngaged())
            return "Galford must be in combat (the fire is cleared with the fight).";
        AddPuddle(at, radius, "test");
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        auto at = [this](uint32 id)
        {
            std::optional<uint64> const due = _queue.DueAt(id);
            return due ? Acore::StringFormat("{}s", int64(*due / 1000)) : std::string("-");
        };
        return Acore::StringFormat("clock={}s heroic={} holyfire@{}s pyro@{} nova@{} winds@{} carriers={} pyroLive={} "
            "kindled={} walls={} puddles={} inside={} floor={:.0f} sq yd", _clockMs / 1000, _heroic ? 1 : 0,
            _nextHolyFireMs / 1000, at(CAST_PYROBLAST), at(CAST_NOVA), at(CAST_WINDS), _carriers.size(),
            _pyro ? 1 : 0, _kindled ? 1 : 0, _walls.Count(), _puddles.size(), _fire.Inside().size(),
            _fire.CoveredArea(0.5f));
    }

private:
    static float constexpr kDropRimReachYd = 2.5f;      // a carrier lands within this of old fire's edge (overlapping)
    static float constexpr kDropRoomPreferYd = 3.f;     // the archive's and the alcove's preferred circles

    // The live AI of this boss on `map`, if it is still the same pull (`gen`). Captures are the map and guids only.
    static boss_archivist_galford_rework* AIOf(Map* map, ObjectGuid bossGuid, uint32 gen)
    {
        Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<boss_archivist_galford_rework*>(boss->AI());
        return ai && ai->_generation == gen ? ai : nullptr;
    }

    // The pull's state: no walls, fire, carriers, casts or pending throws (Reset, evade, death, a new pull).
    void Cleanup()
    {
        ++_generation;      // callbacks of an older pull stop
        for (Carrier const& c : _carriers)
            Mechanic::Cancel(me, c.handle);
        _carriers.clear();
        EndPyro();
        if (_nova)
            Mechanic::Cancel(me, _nova);
        _nova = {};
        for (MechanicHandle const& h : _windsShapes)
            Mechanic::Cancel(me, h);
        _windsShapes.clear();
        _windsAt.reset();
        if (_park)
            Mechanic::Cancel(me, _park);
        _park = {};
        _walls.Clear(me);
        _fire.Clear(me);
        _puddles.clear();
        summons.DespawnEntry(NPC_ST_HOLY_FIRE_PUDDLE);
        summons.DespawnEntry(NPC_ST_PYRE_WALL);
        me->RemoveAurasDueToSpell(SPELL_GF_KINDLED);
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* p = ref.GetSource())
                {
                    p->RemoveAurasDueToSpell(SPELL_GF_HOLY_FIRE, me->GetGUID());
                    p->RemoveAurasDueToSpell(SPELL_GF_SCORCHED, me->GetGUID());
                }
        _queue.Reset();
        _clockMs = 0;
        _nextHolyFireMs = kHolyFireFirstMs;
        _kindledPollMs = 0;
        _parkCheckMs = 0;
        _parkUntilMs = 0;
        _pyroCasts = 0;
        _kindled = false;
        _yelledKindled = false;
        _yelledArchive = false;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::PuddleField _fire;
    DungeonKit::LethalWalls _walls;
    DungeonKit::CastQueue _queue;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _nextHolyFireMs = kHolyFireFirstMs;
    uint64 _parkUntilMs = 0;
    uint32 _kindledPollMs = 0;
    uint32 _parkCheckMs = 0;
    uint32 _generation = 0;
    uint32 _pyroCasts = 0;
    bool _heroic = false;
    bool _kindled = false;
    bool _yelledKindled = false;
    bool _yelledArchive = false;
    std::vector<Puddle> _puddles;
    std::vector<Carrier> _carriers;
    std::optional<Pyro> _pyro;
    MechanicHandle _nova;
    MechanicHandle _park;
    std::vector<MechanicHandle> _windsShapes;
    std::optional<uint64> _windsAt;
};

// The holy fire puddle stalker (300606): an invisible prop that carries a puddle's look (206531-206534).
struct npc_st_holy_fire_puddle : public NullCreatureAI
{
    explicit npc_st_holy_fire_puddle(Creature* creature) : NullCreatureAI(creature) { }
};

// The Pyre stalker (300607): an invisible prop along a wall: the fire (206535) and the lethal strike's caster.
struct npc_st_pyre_wall : public NullCreatureAI
{
    explicit npc_st_pyre_wall(Creature* creature) : NullCreatureAI(creature) { }
};

// GF3 Pyroblast 206522: 35% / 45% of the tank row on its target (the row by the target's role), x 1.25 while he is
// Kindled (the spell ignores caster modifiers, so Kindled's damage done would not reach it).
class spell_st_galford_pyroblast : public SpellScript
{
    PrepareSpellScript(spell_st_galford_pyroblast);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float const pct = PyroPct(IsHeroicMap(caster), caster->HasAura(SPELL_GF_KINDLED));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_st_galford_pyroblast::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// GF7 the holy fire tick 206526: 8% x (1 + 0.25 per Scorched stack the target carries before this tick).
class spell_st_galford_holy_fire_tick : public SpellScript
{
    PrepareSpellScript(spell_st_galford_holy_fire_tick);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;
        float const pct = FireTickPct(DungeonKit::Stacks(target, SPELL_GF_SCORCHED));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, target, pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_st_galford_holy_fire_tick::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_archivist_galford_rework* FindGalfordAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_GALFORD);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_archivist_galford_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Archivist Galford is not running boss_archivist_galford_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_archivist_galford_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_archivist_galford_rework* ai = FindGalfordAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Archivist Galford: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_GALFORD, BOSS_GALFORD);
    }

    bool HandleHolyFire(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_archivist_galford_rework::TestMechanic::HolyFire, heroic,
            "Holy Fire (GF1, its landing GF2 and puddle)");
    }

    bool HandlePyroblast(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_archivist_galford_rework::TestMechanic::Pyroblast, heroic,
            "Pyroblast (GF3, its puddle GF4)");
    }

    bool HandleNova(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_archivist_galford_rework::TestMechanic::Nova, heroic,
            "Fire Nova (GF5, its puddle GF6)");
    }

    bool HandleWinds(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_archivist_galford_rework::TestMechanic::Winds, heroic,
            "Burning Winds (GF11: the shifted puddles, then the gust)");
    }

    bool HandleGust(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_archivist_galford_rework::TestMechanic::Gust, heroic,
            "the gust alone (GF11, cut short of the Pyre)");
    }

    // `.dbtest strat galford puddle [radius]`: a holy fire puddle under the GM (default 4 yd).
    bool HandlePuddle(ChatHandler* handler, Optional<float> radius)
    {
        boss_archivist_galford_rework* ai = FindGalfordAI(handler);
        Player* gm = handler->GetPlayer();
        if (!ai || !gm)
            return false;
        float const r = std::clamp(radius ? *radius : kHolyFireRadius, 1.f, 10.f);
        std::string const error = ai->TestPuddle(gm->GetPosition(), r);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Archivist Galford: a {:.0f} yd holy fire puddle under you.", r);
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_archivist_galford_rework* ai = FindGalfordAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Archivist Galford: {}", ai->TestState());
        return true;
    }

    // `.dbtest strat galford <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& GalfordTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "holyfire",  HandleHolyFire,  SEC_GAMEMASTER, Console::No },
            { "pyroblast", HandlePyroblast, SEC_GAMEMASTER, Console::No },
            { "nova",      HandleNova,      SEC_GAMEMASTER, Console::No },
            { "winds",     HandleWinds,     SEC_GAMEMASTER, Console::No },
            { "gust",      HandleGust,      SEC_GAMEMASTER, Console::No },
            { "puddle",    HandlePuddle,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_archivist_galford_rework()
{
    RegisterDungeonReworkCreatureAI(boss_archivist_galford_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_holy_fire_puddle, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_pyre_wall, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_st_galford_pyroblast);
    RegisterSpellScript(spell_st_galford_holy_fire_tick);
    StratTest::RegisterBoss("galford", GalfordTestCommands());
}
