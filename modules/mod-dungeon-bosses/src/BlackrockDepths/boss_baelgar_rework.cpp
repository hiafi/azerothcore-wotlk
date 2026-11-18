/*
 * mod-dungeon-bosses, Blackrock Depths D13: Bael'Gar (9016), "the Breaking Floor" (ruling 49). Build spec S2
 * "Bael'Gar" (docs/dungeons/blackrock-depths-2-shadowforge-city.md, BG1-BG6; rulings 49-51, 88), handoff sections 3.4
 * (row D13), 3.5, 3.6, 3.8 (NM: the cavern, the fight spot), 3.9 (the `hide` drill row, tag 16). Replaces his SmartAI
 * (WP-S0's rev drops the five rows): Summon Spawn of Bael'Gar is retired, Magma Splash kept as a copy in his slice.
 * Bound by apps/dbc-tools source/npcs/blackrock_depths/baelgar.py. Pure rules (the clocks, the cracks): BaelgarLogic.h.
 *
 *   BG1  Magma Splash    8 s, then every 10-14 s, on his victim: a Fire hit, a 30 s Fire DoT and -250 armor
 *   BG2  Rockfall        5 s, then every 15 s (heroic 12 s): five 3 yd circles, a 1.5 s marker, 15% / 25% + Weakened;
 *                        three (heroic four) under distinct random players (the tank too), the rest on random floor
 *                        spots off the cracks
 *   BG3  Falling Boulder with each Rockfall: an 8 yd circle that follows a random player (never hit by it; the bots
 *                        carry it to open floor) for 3 s, then lands: 40% / 60%. A Fallen Boulder (GO 301281) stays
 *                        where it lands, unless it lands on a crack (BG6), where it falls in and is lost
 *   BG4  Molten Furnace  40 s, then every 40 s (heroic 35 s): a 5 s cast (boss emote), then a wave on everyone he can
 *                        see: 80% / 95%. The BM Hide kind judges real line of sight from him (IsWithinLOSInMap), so a
 *                        Boulder's collision model shelters whoever stands behind it; the live Boulders are the
 *                        blockers the bots hide behind
 *   BG5  Boulders melt   when the wave ends every Boulder goes (emote line 1, a melt look at each base)
 *   BG6  Fissure         15 s, then every 30 s (heroic 20 s): a 2 s stomp (emote line 2), then a 4 yd crack about 40 yd
 *                        long (floor and leash circle permitting) in a bearing chosen among eight by length and
 *                        spread: 25% / 40% + Weakened, and it stays as a lava line, 6% a second, for the fight
 *        "Nothing lands during the cast": a Rockfall or Fissure due during the Furnace's cast (or whose marker would
 *        still be up when it starts) waits for the wave's end (BaelgarLogic.h Timeline).
 *        No adds (the Spawns are removed), no interrupt, dispel or kill order lists (the descriptor is empty).
 *
 * Every timer runs on the AI's own clock (a cast bar never pauses one). Every firing logs one INFO line
 * "brd baelgar <mechanic> ..." (module.dungeonbosses). Lambdas the registry keeps capture guids and values only.
 */

#include "ArenaGuard.h"
#include "BaelgarLogic.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdBaelgar;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "baelgar";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogBg(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // The floor under a point: the map's height within kFloorProbeBandYd of `refZ`, else `refZ`.
    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kFloorProbeBandYd)
            return refZ;
        return h;
    }

    // The test commands' forced mechanics (`.dbtest brd baelgar ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Rockfall,
        Boulder,
        Furnace,
        Fissure,
        Splash,
        Melt,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Bael'Gar 9016
// ---------------------------------------------------------------------------------------------------------------------
struct boss_baelgar_rework : public BossAI
{
    explicit boss_baelgar_rework(Creature* creature)
        : BossAI(creature, BOSS_BAELGAR), _arena(BaelgarArena(), LeashOptions(kBoss)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the summon list (the lava stalkers)
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
        LogBg("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Cleanup();
        BossAI::JustDied(killer);
        LogBg("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
    }

    // The lava stalkers join the summon list (BossAI despawns it) but not the fight.
    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        summons.Summon(summon);
        summon->SetReactState(REACT_PASSIVE);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // The wave's backstop also runs out of combat (`.dbtest` on an idle boss).
        if (_meltBackstopMs && _clockMs >= _meltBackstopMs)
        {
            LogBg("furnace-backstop", "the wave's resolve was not seen: melting the Boulders");
            WaveEnds(nullptr);
        }

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        RunTimers();
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
        options.bossStateId = BOSS_BAELGAR;
        Mechanic::BeginEncounter(me, options);
        _registered = true;
        _arena.Engage(me);
        _fighting = true;
        _timeline.Start(_heroic, _clockMs);
        _splashAtMs = _clockMs + kMagmaSplashFirstMs;
        // No kill order, interrupt, dispel or purge list (S2 "Boss data"): an empty descriptor says so to the bots.
        Mechanic::Describe(me, BossMechanics::Descriptor{});
        LogBg("engage", Acore::StringFormat("heroic={} rockfall={}s fissure={}s furnace={}s", _heroic ? 1 : 0,
            kRockfallFirstMs / 1000, kFissureFirstMs / 1000, kFurnaceFirstMs / 1000));
    }

    void RunTimers()
    {
        bool const casting = me->HasUnitState(UNIT_STATE_CASTING);

        // BG4 first: it never waits for anything but a cast already going on.
        if (_timeline.Due(Beat::Furnace, _clockMs) && !casting)
        {
            if (StartFurnace())
                _timeline.Fired(Beat::Furnace, _clockMs);
            else
                _timeline.Retry(Beat::Furnace, _clockMs);
        }
        // BG2 + BG3 (a Rockfall is not a cast: nothing here waits for a bar, only for the Furnace's window)
        if (_timeline.Due(Beat::Rockfall, _clockMs))
        {
            if (Rockfall())
                _timeline.Fired(Beat::Rockfall, _clockMs);
            else
                _timeline.Retry(Beat::Rockfall, _clockMs);
        }
        // BG6 (a 2 s stomp bar: not while another cast is going on)
        if (_timeline.Due(Beat::Fissure, _clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (StartFissure())
                _timeline.Fired(Beat::Fissure, _clockMs);
            else
                _timeline.Retry(Beat::Fissure, _clockMs);
        }
        RunSplash();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BG1 Magma Splash
    // ----------------------------------------------------------------------------------------------------------------

    void RunSplash()
    {
        if (_clockMs < _splashAtMs)
            return;
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
        {
            _splashAtMs = _clockMs + kRetryMs;
            return;
        }
        me->CastSpell(victim, SPELL_BG_MAGMA_SPLASH, true);
        _splashAtMs = _clockMs + urand(kMagmaSplashEveryMinMs, kMagmaSplashEveryMaxMs);
        LogBg("magma-splash", Acore::StringFormat("target={} hit={:.0f}% tick={:.1f}%", victim->GetName(),
            kMagmaSplashHitPct(_heroic), kMagmaSplashTickPct(_heroic)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    // Up to `count` distinct players of the fight, the tank too (ruling 88) unless `nonTank`, never one of `exclude`.
    // Out of combat the GM of a test command stands in for the group.
    std::vector<Player*> FightPlayers(GuidSet const& exclude, uint32 count, bool nonTank = false)
    {
        if (!me->IsEngaged())
        {
            std::vector<Player*> out;
            Player* gm = _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer);
            if (gm && count && !exclude.count(gm->GetGUID()))
                out.push_back(gm);
            return out;
        }
        DungeonKit::PickRule rule;
        rule.nonTank = nonTank;
        DungeonKit::ExcludeGuids(rule, exclude);
        return DungeonKit::PickPlayers(me, rule, count);
    }

    static uint32 constexpr kPickAll = 40;      // everyone on the threat list (a raid never reaches it)

    // ----------------------------------------------------------------------------------------------------------------
    // BG2 Rockfall + BG3 Falling Boulder
    // ----------------------------------------------------------------------------------------------------------------

    // One Rockfall beat: the Falling Boulder's carrier first (never under a circle), then the five circles. False:
    // nobody to fall on.
    bool Rockfall()
    {
        // The carrier is never the tank (orchestrator default after R-1-B m11: an 8 yd Boulder on the tank drags him
        // off the group or lands its rock in the melee ring); the circles stay tank-inclusive (ruling 88). Nobody but
        // the tank left: no Boulder this beat.
        std::vector<Player*> const carrierPick = FightPlayers({}, 1, kBoulderCarrierNonTank);
        Player* carrier = carrierPick.empty() ? nullptr : carrierPick.front();
        std::size_t const onFight = FightPlayers({}, kPickAll).size();
        if (!carrier && !onFight)
        {
            LogBg("rockfall-none", "nobody in the fight");
            return false;
        }

        uint32 const wanted = RockfallPlayerCircles(_heroic, static_cast<uint32>(onFight), carrier != nullptr);
        GuidSet exclude;
        if (carrier)
            exclude.insert(carrier->GetGUID());
        std::vector<Player*> const under = FightPlayers(exclude, wanted, kRockfallNonTank);

        std::vector<Position> spots;
        for (Player* player : under)
            spots.emplace_back(player->GetPositionX(), player->GetPositionY(),
                GroundZ(me, player->GetPositionX(), player->GetPositionY(), player->GetPositionZ()), 0.f);
        uint32 const onPlayers = static_cast<uint32>(spots.size());
        uint32 randomSpots = 0;
        for (uint32 i = RockfallSpotCircles(onPlayers); i > 0; --i)
            if (std::optional<Position> const spot = PickRockfallSpot(spots))
            {
                spots.push_back(*spot);
                ++randomSpots;
            }

        float const pct = kRockfallPct(_heroic);
        uint32 landed = 0;
        for (Position const& spot : spots)
        {
            MechanicRef ref = Mechanic::Circle(me, spot, kRockfallRadiusYd, Ms(kRockfallWarnMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_BG_ROCKFALL).Weakened()
                .Tag(TAG_BG_ROCKFALL)
                .OnResolve(OnBaelgar([spot](boss_baelgar_rework& ai, BossMechanics::ResolveResult const& r)
                {
                    ai.RockfallLands(spot, r);
                }));
            if (ref.IsValid())
            {
                Track(ref.Handle());
                ++landed;
            }
        }

        bool boulder = false;
        if (carrier)
            boulder = StartBoulder(carrier);
        LogBg("rockfall", Acore::StringFormat("heroic={} circles={} onPlayers={} random={} pct={:.0f} carrier={}",
            _heroic ? 1 : 0, landed, onPlayers, randomSpots, pct, boulder ? carrier->GetName() : std::string("none")));
        return landed > 0 || boulder;
    }

    // A random floor spot of the cavern, off the cracks and 4 yd from the circles so far; nullopt when no floor.
    std::optional<Position> PickRockfallSpot(std::vector<Position> const& chosen)
    {
        DungeonKit::FloorSpotRules rules;
        rules.near = kBaelgarFightSpot.XY();
        rules.minRange = 0.f;
        rules.maxRange = kRockfallSpotRangeYd;
        rules.avoid = CrackAvoidCircles(_cracks, kFissureWidthYd / 2.f + kRockfallRadiusYd);
        rules.minFromAway = kRockfallSpotApartYd;
        for (Position const& p : chosen)
            rules.awayFrom.push_back({ p.GetPositionX(), p.GetPositionY() });
        DungeonKit::FloorProbe probe;
        probe.z = kBaelgarFightSpot.z;
        probe.zBand = 4.f;
        DungeonKit::Arena const arena = BaelgarArena();
        return DungeonKit::PickFloorSpot(me, &arena, rules, probe);
    }

    void RockfallLands(Position const& spot, BossMechanics::ResolveResult const& r)
    {
        if (r.fizzled)
            return;
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_BG_ROCKFALL_LOOK, true);
    }

    // BG3: the carrier takes the circle where they will; it lands where they stand. The bots' drop spot rule: the open
    // floor of the cavern, away from the group, off the cracks and the Boulders already standing.
    BossMechanics::DropSpotRule BoulderDropRule()
    {
        BossMechanics::DropSpotRule rule;
        rule.Room(Position(kBaelgarFightSpot.x, kBaelgarFightSpot.y, kBaelgarFightSpot.z, 0.f), 30.f).Away();
        for (Crack const& crack : _cracks)
            for (DungeonKit::AvoidCircle const& c : CrackAvoidCircles({ crack }, kBoulderRadiusYd, kBoulderRadiusYd))
                rule.Avoid(Position(c.center.x, c.center.y, kBaelgarFightSpot.z, 0.f), c.radius);
        for (ObjectGuid const& guid : _boulders)
            if (GameObject* go = me->GetMap()->GetGameObject(guid))
                rule.Avoid(go->GetPosition(), kBoulderRadiusYd);
        return rule;
    }

    bool StartBoulder(Player* carrier)
    {
        DungeonKit::ImpactSpec impact;
        impact.pct = kBoulderPct(_heroic);
        impact.tankPct = impact.pct;
        impact.school = SPELL_SCHOOL_NORMAL;
        impact.spellId = SPELL_BG_FALLING_BOULDER;
        impact.weakened = false;
        impact.tag = TAG_BG_BOULDER;
        MechanicRef ref = DungeonKit::FollowThenLand(me, carrier, kBoulderRadiusYd, Ms(kBoulderWarnMs), impact,
            [](Creature* owner, Position const& spot, BossMechanics::ResolveResult const& r)
            {
                if (!owner || r.fizzled || !owner->IsAIEnabled)
                    return;
                if (auto* ai = dynamic_cast<boss_baelgar_rework*>(owner->AI()))
                    ai->BoulderLands(spot, r.hits.size());
            });
        if (!ref.IsValid())
        {
            LogBg("boulder-refused", carrier->GetName());
            return false;
        }
        ref.DropSpot(BoulderDropRule());
        Track(ref.Handle());
        Talk(EMOTE_BAELGAR_BOULDER);
        return true;
    }

    // The impact: the look, then the Boulder (unless it fell into a crack).
    void BoulderLands(Position const& spot, std::size_t hits)
    {
        float const x = spot.GetPositionX();
        float const y = spot.GetPositionY();
        float const z = GroundZ(me, x, y, spot.GetPositionZ());
        me->CastSpell(x, y, z, SPELL_BG_BOULDER_LAND_LOOK, true);
        if (BoulderLost(_cracks, { x, y }))
        {
            LogBg("boulder-lost", Acore::StringFormat("at=({:.1f}, {:.1f}) hits={} fell into a crack", x, y, hits));
            return;
        }
        PruneBoulders();
        if (_boulders.size() >= kBoulderCap)
        {
            LogBg("boulder-capped", Acore::StringFormat("at=({:.1f}, {:.1f}) standing={}", x, y, _boulders.size()));
            return;
        }
        // The orientation is random: a rock of 5 by 5 yd looks different turned.
        GameObject* go = me->SummonGameObject(GO_BRD_FALLEN_BOULDER, x, y, z, frand(0.f, DungeonKit::kTwoPi), 0.f, 0.f,
            0.f, 0.f, kBoulderBackstopSec);
        if (!go)
        {
            LogBg("boulder-refused", Acore::StringFormat("at=({:.1f}, {:.1f}) the object was not created", x, y));
            return;
        }
        // One C++ constant decides the model (kBoulderDisplay; the template's displayId equals it, tested).
        if (!go->GetGOInfo() || go->GetGOInfo()->displayId != kBoulderDisplay)
            go->SetDisplayId(kBoulderDisplay);
        _boulders.push_back(go->GetGUID());
        LogBg("boulder", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) hits={} standing={} display={}", x, y, z,
            hits, _boulders.size(), kBoulderDisplay));
    }

    // Boulders the map still has (a backstop despawn or a delete took the others).
    void PruneBoulders()
    {
        Map* map = me->GetMap();
        std::erase_if(_boulders, [map](ObjectGuid const& guid) { return !map || !map->GetGameObject(guid); });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BG4 Molten Furnace + BG5 the Boulders melt
    // ----------------------------------------------------------------------------------------------------------------

    // The cast bar (boss emote) and the Hide: the live Boulders are the blockers, he is the source. False: a cast is
    // going on (the clock tries again).
    bool StartFurnace()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        PruneBoulders();
        BossMechanics::HideSpec spec(me);
        uint32 blockers = 0;
        for (ObjectGuid const& guid : _boulders)
            if (GameObject* go = me->GetMap()->GetGameObject(guid))
            {
                spec.Blocker(go->GetGUID(), go->GetPosition(), kBoulderFootprintYd);
                ++blockers;
            }
        spec.Range(kFurnaceRangeYd);

        float const pct = kFurnacePct(_heroic);
        DungeonKit::CastBar(me, SPELL_BG_MOLTEN_FURNACE_CAST, nullptr, EMOTE_BAELGAR_FURNACE);
        MechanicRef ref = Mechanic::Hide(me, spec, Ms(kFurnaceCastMs));
        if (!ref.IsValid())
        {
            LogBg("furnace-refused", "the registry refused the Hide");
            return false;
        }
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_BG_MOLTEN_FURNACE).Tag(TAG_BG_FURNACE)
            .OnResolve(OnBaelgar([](boss_baelgar_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.WaveEnds(&r);
            }));
        Track(ref.Handle());
        _meltBackstopMs = _clockMs + kFurnaceCastMs + kMeltBackstopMs;
        LogBg("furnace", Acore::StringFormat("heroic={} boulders={} pct={:.0f} cast={}s", _heroic ? 1 : 0, blockers,
            pct, kFurnaceCastMs / 1000));
        return true;
    }

    // The wave resolved (the registry judged line of sight before this runs): the Boulders melt. `r` is null for the
    // script's own backstop.
    void WaveEnds(BossMechanics::ResolveResult const* r)
    {
        _timeline.WaveEnded();
        _meltBackstopMs = 0;
        if (r)
            LogBg("furnace-wave", Acore::StringFormat("seen={} hidden={}", r->hits.size(), r->cleared.size()));
        Melt();
    }

    // BG5: every Boulder goes, with a melt look at its base; the emote when any stood.
    void Melt()
    {
        uint32 melted = 0;
        for (ObjectGuid const& guid : _boulders)
            if (GameObject* go = me->GetMap()->GetGameObject(guid))
            {
                me->CastSpell(go->GetPositionX(), go->GetPositionY(), go->GetPositionZ(),
                    SPELL_BG_BOULDER_MELT_LOOK, true);
                go->Delete();
                ++melted;
            }
        _boulders.clear();
        if (melted)
            Talk(EMOTE_BAELGAR_MELT);
        LogBg("melt", Acore::StringFormat("boulders={}", melted));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BG6 Fissure
    // ----------------------------------------------------------------------------------------------------------------

    // The stomp (emote 2, a 2 s bar) and the crack's marker; the bearing is among eight, chosen by floor length and
    // spread from the cracks so far. False: no bearing opens (a cast is going on, or no floor).
    bool StartFissure()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        Vec2 const origin = DungeonKit::PlaneOf(me);
        float const z = me->GetPositionZ();
        Vec2 const center = kBaelgarFightSpot.XY();

        std::vector<FissureCandidate> candidates;
        float const offset = frand(0.f, DungeonKit::kTwoPi / static_cast<float>(kFissureCandidates));
        for (uint32 i = 0; i < kFissureCandidates; ++i)
        {
            float const bearing = offset + static_cast<float>(i) * DungeonKit::kTwoPi
                / static_cast<float>(kFissureCandidates);
            float const onFloor = FloorLengthAlong(origin, bearing, kFissureLengthYd, kFloorProbeStepYd, z,
                kFloorProbeBandYd, [this, z](Vec2 p) -> std::optional<float>
                {
                    float const h = me->GetMapHeight(p.x, p.y, z + 3.f);
                    if (h <= INVALID_HEIGHT + 1.f)
                        return std::nullopt;
                    return h;
                });
            candidates.push_back({ bearing, CrackLength(onFloor,
                DungeonKit::RayToCircleEdge(center, kArenaRadiusYd, origin, bearing)) });
        }
        std::vector<float> priors;
        for (Crack const& crack : _cracks)
            priors.push_back(crack.bearing);
        std::optional<std::size_t> const pick = ChooseFissure(candidates, priors, urand(0, 1000));
        if (!pick)
        {
            LogBg("fissure-none", "no bearing with floor");
            return false;
        }

        Crack const crack{ origin, candidates[*pick].bearing, candidates[*pick].length };
        _cracks.push_back(crack);
        Position const from(origin.x, origin.y, z, crack.bearing);

        float const pct = kFissurePct(_heroic);
        DungeonKit::CastBar(me, SPELL_BG_FISSURE_CAST, nullptr, EMOTE_BAELGAR_FISSURE);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(from, crack.bearing, crack.length,
            kFissureWidthYd), Ms(kFissureWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_BG_FISSURE).Weakened()
            .Tag(TAG_BG_FISSURE)
            .OnResolve(OnBaelgar([crack, z](boss_baelgar_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai.FissureLands(crack, z, r);
            }));
        if (ref.IsValid())
            Track(ref.Handle());
        LogBg("fissure", Acore::StringFormat("heroic={} from=({:.1f}, {:.1f}) bearing={:.0f} length={:.1f} pct={:.0f} "
            "cracks={}", _heroic ? 1 : 0, origin.x, origin.y, crack.bearing * 180.f / DungeonKit::kPi, crack.length,
            pct, _cracks.size()));
        return true;
    }

    // The crack opens: the burst, the lasting lava (one persistent line for the fight) and a lava look every 6 yd.
    void FissureLands(Crack const& crack, float z, BossMechanics::ResolveResult const& r)
    {
        if (r.fizzled)
            return;
        me->CastSpell(crack.from.x, crack.from.y, z, SPELL_BG_FISSURE_BURST_LOOK, true);

        float const pct = kLavaPctPerTick(_heroic);
        Position const from(crack.from.x, crack.from.y, z, crack.bearing);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(from, crack.bearing, crack.length,
            kFissureWidthYd), Ms(kLavaTickMs));
        ref.Persistent(Ms(kLavaLifeMs), Ms(kLavaTickMs)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_FIRE)
            .Spell(SPELL_BG_FISSURE_LAVA).NoFillTimer().Tag(TAG_BG_LAVA);
        if (ref.IsValid())
            Track(ref.Handle());

        uint32 looks = 0;
        for (float s = 0.f; s <= crack.length + 1e-3f; s += kLavaLookEveryYd)
        {
            Vec2 const p = DungeonKit::Advance(crack.from, crack.bearing, s);
            Creature* stalker = me->SummonCreature(NPC_BRD_STALKER,
                Position(p.x, p.y, GroundZ(me, p.x, p.y, z), 0.f), TEMPSUMMON_MANUAL_DESPAWN);
            if (!stalker)
                continue;
            stalker->CastSpell(stalker, SPELL_BG_FISSURE_LAVA_LOOK, true);
            _stalkers.push_back(stalker->GetGUID());
            ++looks;
        }
        LogBg("fissure-lands", Acore::StringFormat("hits={} lava={:.0f}%/s looks={}", r.hits.size(), pct, looks));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // State
    // ----------------------------------------------------------------------------------------------------------------

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBaelgar(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_baelgar_rework*>(boss->AI()))
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
            _live.erase(_live.begin(), _live.begin() + 48);     // a trimmed lasting lava line still ends with the
                                                                // encounter (Cleanup's EndEncounter), R-1-B n2
    }

    // The pull's state: nothing pending, no Boulder, crack, stalker or aura of the fight left (Reset, evade, death, a
    // new pull). The registry's encounter ends too: the lasting lava lines are its mechanics.
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
        if (Map* map = me->GetMap())
        {
            for (ObjectGuid const& guid : _boulders)
                if (GameObject* go = map->GetGameObject(guid))
                    go->Delete();
            for (ObjectGuid const& guid : _stalkers)
                if (Creature* stalker = ObjectAccessor::GetCreature(*me, guid))
                    stalker->DespawnOrUnsummon();
        }
        _boulders.clear();
        _stalkers.clear();
        _cracks.clear();
        _fighting = false;
        _timeline = Timeline{};
        _splashAtMs = 0;
        _meltBackstopMs = 0;
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_BG_MAGMA_SPLASH);
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brd baelgar` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm)
    {
        _testPlayer = gm ? gm->GetGUID() : ObjectGuid::Empty;
        switch (kind)
        {
            case TestKind::Rockfall:
                if (!Rockfall())
                    return "Nobody to fall on.";
                break;
            case TestKind::Boulder:
                if (!gm)
                    return "No player to carry it.";
                if (!StartBoulder(gm))
                    return "The Falling Boulder was refused.";
                break;
            case TestKind::Furnace:
                if (!StartFurnace())
                    return "Busy casting; try again in a moment.";
                if (_fighting)
                    _timeline.Fired(Beat::Furnace, _clockMs);
                break;
            case TestKind::Fissure:
                if (!StartFissure())
                    return "Busy casting, or no floor to crack.";
                break;
            case TestKind::Splash:
                if (Unit* victim = me->GetVictim())
                    me->CastSpell(victim, SPELL_BG_MAGMA_SPLASH, true);
                else if (gm)
                    me->CastSpell(gm, SPELL_BG_MAGMA_SPLASH, true);
                else
                    return "Nobody to splash.";
                break;
            case TestKind::Melt:
                Melt();
                break;
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest brd baelgar heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
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
        return Acore::StringFormat("baelgar heroic={} fighting={} rockfall={} fissure={} furnace={} live={} "
            "boulders={} cracks={} stalkers={} splash={}", _heroic ? 1 : 0, _fighting ? 1 : 0,
            left(_timeline.rockfallAt), left(_timeline.fissureAt), left(_timeline.furnaceAt),
            _timeline.furnaceLive ? 1 : 0, _boulders.size(), _cracks.size(), _stalkers.size(), left(_splashAtMs));
    }

private:
    DungeonKit::ArenaGuard _arena;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _registered = false;       // a registry encounter of ours exists
    uint64 _clockMs = 0;            // the AI's own clock: nothing here waits for a cast bar
    uint64 _splashAtMs = 0;         // BG1
    uint64 _meltBackstopMs = 0;     // BG5: melt the Boulders ourselves if the wave's resolve is never seen
    Timeline _timeline;             // BG2, BG4, BG6
    std::vector<Crack> _cracks;     // BG6: the Boulder check, the Rockfall spots and the lava share it
    std::vector<ObjectGuid> _boulders;
    std::vector<ObjectGuid> _stalkers;
    std::vector<MechanicHandle> _live;
    ObjectGuid _testPlayer;
};

namespace
{
    boss_baelgar_rework* BaelgarAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_BAELGAR);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_baelgar_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_baelgar_rework* ai = BaelgarAI(handler);
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

    // `.dbtest brd baelgar info`
    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_BAELGAR, BOSS_BAELGAR);
    }

    // `.dbtest brd baelgar state`: his clocks and what stands.
    bool HandleState(ChatHandler* handler)
    {
        boss_baelgar_rework* ai = BaelgarAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest brd baelgar rockfall`: BG2 + BG3 now (out of combat: you carry the Boulder, five circles on the floor).
    bool HandleRockfall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Rockfall, "Rockfall: circles (1.5 s) and a Falling Boulder on you (3 s).");
    }

    // `.dbtest brd baelgar boulder`: BG3 now, on you.
    bool HandleBoulder(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Boulder, "Falling Boulder: it follows you for 3 s, then lands and stands.");
    }

    // `.dbtest brd baelgar furnace`: BG4 now (the live Boulders are the blockers).
    bool HandleFurnace(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Furnace, "Molten Furnace: a 5 s cast, then the wave on everyone he can see.");
    }

    // `.dbtest brd baelgar fissure`: BG6 now, from his spot.
    bool HandleFissure(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Fissure, "Fissure: a 2 s stomp, then a crack and lasting lava.");
    }

    // `.dbtest brd baelgar splash`: BG1 now, on his victim (or you).
    bool HandleSplash(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Splash, "Magma Splash.");
    }

    // `.dbtest brd baelgar melt`: BG5 now (every Boulder goes).
    bool HandleMelt(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Melt, "The Boulders melt.");
    }

    // `.dbtest brd baelgar clear`: every zone, Boulder, crack and lava stalker goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest brd baelgar heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_baelgar_rework* ai = BaelgarAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossBaelgarTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "rockfall", HandleRockfall, SEC_GAMEMASTER, Console::No },
            { "boulder",  HandleBoulder,  SEC_GAMEMASTER, Console::No },
            { "furnace",  HandleFurnace,  SEC_GAMEMASTER, Console::No },
            { "fissure",  HandleFissure,  SEC_GAMEMASTER, Console::No },
            { "splash",   HandleSplash,   SEC_GAMEMASTER, Console::No },
            { "melt",     HandleMelt,     SEC_GAMEMASTER, Console::No },
            { "clear",    HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic",   HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_baelgar_rework()
{
    RegisterDungeonReworkCreatureAI(boss_baelgar_rework, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("baelgar", BossBaelgarTestCommands());
}
