/*
 * mod-dungeon-bosses, Stratholme S1: The Unforgiven (10516), "a ghost story in a burning street". Build spec ST
 * 616-676 (docs/dungeons/stratholme-rework.md), handoff section 3.4 rows UF, 3.5 row S1, 3.8 #1 (the plaza: two
 * lanes, two cordons, five bays). Replaces his SmartAI (the invisibility roll, Incorporeal Defense, the four phantoms
 * on aggro, the 8 s Frost Nova) and the phantom 10387's (Frost Shock): the templates are rebound by apps/dbc-tools
 * source/npcs/stratholme/the_unforgiven.py. Pure rules: UnforgivenLogic.h.
 *
 *   UF12 The Cordon        at the pull (after the pull grip, the only grip: user ruling on section 7 #16) a rank of
 *                          Spectral Footmen (300600) stands across each street mouth; the kit's LethalWall on each
 *                          line arms 2 s later: crossing is death (the shared strike 206400), pets too
 *   UF1  The March         20 s, then every 40 s: yell line 1, a rank forms at one street's cordon, a 3 s line marker
 *                          (the street's full width), then the rank marches it in 2 s: 40% (heroic 45%) + Weakened
 *                          (a projectile Line tracking the rank's middle footman). The lanes alternate. Heroic: the
 *                          crossing rank down the other street, its marker 1.5 s after the first passed
 *   UF2  House fire        8 s, then every 25 s (heroic 20 s), at most 3 burning: emote line 3, a 2 s 5 yd circle at a
 *                          free bay, 25% + Weakened
 *   UF3  Burning house     the same circle for 60 s, 5% a second (the kit's ImpactThenLinger), the stock "Big Barracks
 *                          Flame" gameobject on the doorway
 *   UF4  Firelight         5 to 10 yd around each burning house: a telegraph-only Soak the accused claim (FlameZone
 *                          glow on the fire stalker 300601); a phantom within 10 yd of a fire carries In the Firelight
 *   UF5  The Accusation    15 s, then every 35 s until the Last Soul: yell line 2, Accused on a random non-tank, 3
 *                          phantoms (heroic 4) rise around him and drift to the accused (60% walk), 20 s each
 *   UF6  Freed             a phantom killed in the firelight: 2% of his maximum health torn away, Soul Freed
 *   UF7  Grief             a phantom reached its accused: 30% on them
 *   UF8  Grudge            a phantom Bound (killed in the dark, 20 s up, or reached): +10% damage done per stack
 *   UF9  The Last Soul     at 25%, once: yell line 4, accusations stop, every Grudge stack rises again as a phantom
 *                          on a random non-tank; freeing one removes its stack
 *   UF10 Frost Nova        every 15 to 20 s while a player is within 10 yd: 8% Frost and a 1.5 s root, never in the
 *                          6 s before a March lands nor while a rank is on the floor
 *   UF11 Haunting Memory   heroic, 12 s then every 30 s, 2 random non-tanks, 8 s Magic DoT 3%/s; it runs out: a
 *                          phantom rises 6 yd from that player, fixated on them
 *   UF13 Arena             StratholmeRework::LeashOptions on UnforgivenArena() (the plaza polygon) plus the pull grip
 *
 * Every timer runs on the AI's own clock, never on BossAI's scheduler. Every firing logs one INFO line
 * "strat unforgiven <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitWalls.h"
#include "GameObject.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "UnforgivenLogic.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratUnforgiven;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "unforgiven";

    enum UnforgivenActions : int32
    {
        ACTION_PHANTOM_FIXATE   = 1,
    };

    enum UnforgivenPoints : uint32
    {
        POINT_PHANTOM_DRIFT     = 1,
    };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // The floor under (x, y) near `guess` (the measured height when the probe finds nothing close).
    float FloorZ(WorldObject const* ref, float x, float y, float guess)
    {
        float const h = ref->GetMapHeight(x, y, guess + 4.f);
        if (h <= INVALID_HEIGHT + 1.f || std::fabs(h - guess) > 8.f)
            return guess;
        return h;
    }

    // Accused players (the firelight Soak's claimers).
    BossMechanics::Eligibility AccusedOnly()
    {
        BossMechanics::Eligibility e;
        e.auraSpell = SPELL_UF_ACCUSED;
        e.minStacks = 1;
        e.maxStacks = 255;
        return e;
    }

    // The leash, plus the pull grip (the Cordon is a lethal wall: section 10); never a grip back.
    DungeonKit::ArenaGuardOptions UnforgivenGuardOptions()
    {
        DungeonKit::ArenaGuardOptions o = LeashOptions(kBossLogName);
        o.gripOnPull = true;
        o.gripBack = false;
        return o;
    }
}

// The Unforgiven 10516
struct boss_the_unforgiven_rework : public BossAI
{
    explicit boss_the_unforgiven_rework(Creature* creature)
        : BossAI(creature, BOSS_UNFORGIVEN), _arena(UnforgivenArena(), UnforgivenGuardOptions()) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_UNFORGIVEN;
        Mechanic::BeginEncounter(me, options);

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        _marchNominalMs = kMarch.first;
        _nextMarchMs = kMarch.first;
        _nextLane = urand(0, 1);
        _fireNominalMs = kFireFirstMs;
        _nextFireMs = kFireFirstMs;
        _accuseNominalMs = kAccusation.first;
        _nextAccuseMs = kAccusation.first;
        _hauntNominalMs = kHaunting.first;
        _nextHauntMs = kHaunting.first;
        _nextNovaMs = urand(kNovaMinMs, kNovaMaxMs);

        _arena.Engage(me);      // the pull grip: everyone in the fight onto the plaza
        GripOffTheCordon();     // the safety net: nobody left standing in (or by) a strip
        RaiseCordon();          // the walls arm 2 s after the grip
        Describe(_heroic);
        Talk(YELL_UNFORGIVEN_AGGRO);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) walls={} firstLane={}", _heroic ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), _walls.Count(), kLanes[_nextLane].name));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        uint32 const freed = _freed;
        uint32 const bound = _bound;
        LowerCordon(true);          // the cordon lowers its spears and fades (out of the summon list first)
        BossAI::JustDied(killer);   // DONE (the instance's rule), the encounter ends, the summons go
        Cleanup();
        Talk(YELL_UNFORGIVEN_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("killer={} freed={} bound={}", killer ? killer->GetName() : "none", freed, bound));
    }

    // Phantoms join the fight; footmen and fire stalkers never do (they are not attackable).
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        if (summon->GetEntry() == NPC_VENGEFUL_PHANTOM && me->IsEngaged())
            DoZoneInCombat(summon);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        _phantoms.erase(summon->GetGUID());     // gone without an end (a reset): nothing more to settle
        BossAI::SummonedCreatureDespawn(summon);
    }

    // UF6 / UF8: a phantom killed in the firelight is freed, in the dark it is bound.
    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (summon->GetEntry() != NPC_VENGEFUL_PHANTOM)
            return;
        bool const light = InLight(DungeonKit::PlaneOf(summon));
        EndPhantom(summon->GetGUID(), light ? PhantomEnd::DiedInLight : PhantomEnd::DiedInDark, summon);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdateMarch();
        UpdateRanks();
        UpdateFires();
        UpdateAccusation();
        UpdateHaunting();
        UpdateHousekeeping();
        UpdateNova();
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The players of the fight
    // ----------------------------------------------------------------------------------------------------------------

    std::vector<Player*> AlivePlayers() const
    {
        std::vector<Player*> out;
        Map* map = me->FindMap();
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (player && player->IsAlive() && !player->IsGameMaster())
                out.push_back(player);
        }
        return out;
    }

    // A random non-tank of his threat list (a lone tank when nobody else is there).
    Player* PickNonTank() const
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        return DungeonKit::PickPlayer(me, rule);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF12 The Cordon
    // ----------------------------------------------------------------------------------------------------------------

    Creature* SummonFootman(Vec2 at, float z, float facing)
    {
        Creature* footman = me->SummonCreature(NPC_ST_SPECTRAL_FOOTMAN, at.x, at.y, FloorZ(me, at.x, at.y, z), facing,
            TEMPSUMMON_MANUAL_DESPAWN);
        if (!footman)
            return nullptr;
        footman->SetReactState(REACT_PASSIVE);
        return footman;
    }

    // R-2-A A-1 (acceptance #8, "never kill a player who stood inside at the pull"): after the guard's pull grip,
    // grip every unit of the fight it left on the plaza that stands within kCordonGripClearanceYd of a cordon's strip
    // (the polygon edge inside a strip, a pet parked by the line): the walls arm 2 s later and would strike it.
    void GripOffTheCordon()
    {
        std::vector<Unit*> near;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref ? ref->GetVictim() : nullptr;
            // Off the arena: the guard's pull grip has it (a second grip would cut that jump short).
            if (unit && _arena.Grippable(me, unit) && _arena.Contains(unit)
                && NeedsCordonGrip(DungeonKit::PlaneOf(unit)))
                near.push_back(unit);
        }
        for (Unit* unit : near)
            _arena.Grip(me, unit, "cordon");
        if (!near.empty())
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cordon-grip", Acore::StringFormat("units={}",
                near.size()));
    }

    void RaiseCordon()
    {
        for (std::size_t c = 0; c < kCordonCount; ++c)
        {
            WallLine const line = CordonWall(c);
            std::vector<ObjectGuid> rank;
            for (uint32 k = 0; k < kCordonFootmen[c]; ++k)
            {
                Vec2 const at = CordonPoint(c, k);
                if (Creature* footman = SummonFootman(at, kCordonZ[c], DungeonKit::BearingTo(at, kPlazaCenter)))
                {
                    footman->SetEmoteState(EMOTE_STATE_READY1H);     // shields up
                    rank.push_back(footman->GetGUID());
                    _cordonFootmen.push_back(footman->GetGUID());
                }
            }
            DungeonKit::LethalWallSpec w;
            w.from = DungeonKit::ToPosition(line.from, FloorZ(me, line.from.x, line.from.y, kCordonZ[c]));
            w.to = DungeonKit::ToPosition(line.to, FloorZ(me, line.to.x, line.to.y, kCordonZ[c]));
            w.width = line.width;
            w.killSpell = SPELL_ST_CROSSED_THE_LINE;
            w.strikers = rank;
            w.tag = TAG_CORDON;
            w.dungeon = kLogDungeon;
            w.boss = kBossLogName;
            _walls.Add(me, w);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cordon",
            Acore::StringFormat("walls={} footmen={}", _walls.Count(), _cordonFootmen.size()));
    }

    // `fade`: his death: the footmen kneel and fade; otherwise they go at once.
    void LowerCordon(bool fade)
    {
        _walls.Clear(me);
        for (ObjectGuid const& guid : _cordonFootmen)
        {
            Creature* footman = ObjectAccessor::GetCreature(*me, guid);
            if (!footman)
                continue;
            summons.Despawn(footman);       // out of BossAI's list: its DespawnAll would not let them fade
            if (fade)
            {
                footman->SetEmoteState(EMOTE_ONESHOT_NONE);
                footman->HandleEmoteCommand(EMOTE_ONESHOT_KNEEL);
                footman->DespawnOrUnsummon(2500ms);
            }
            else
                footman->DespawnOrUnsummon();
        }
        _cordonFootmen.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF1 The March
    // ----------------------------------------------------------------------------------------------------------------

    struct Rank
    {
        std::size_t lane = 0;
        bool crossing = false;
        bool marching = false;
        uint64 marchAtMs = 0;
        uint64 endAtMs = 0;
        std::vector<ObjectGuid> footmen;
        std::vector<std::vector<DungeonKit::FloorPathPoint>> paths;
        MechanicHandle line;
    };

    // How long a rank's pass lasts on the registry (the body's half length is half the street's width).
    static uint32 PassMs(MarchLane const& lane)
    {
        HitLine const hit = MarchHitLine(lane);
        float const v = MarchSpeed(lane);
        return static_cast<uint32>(std::ceil((hit.Length() + hit.width * 0.5f) / v * 1000.f));
    }

    void UpdateMarch()
    {
        if (_clockMs < _nextMarchMs)
            return;
        std::size_t const lane = _nextLane;
        if (StartMarch(lane, false, kMarchWarnMs))
            _nextLane = OtherLane(lane);
        _marchNominalMs = NextOnCadence(_marchNominalMs, _clockMs, kMarch.every);
        _nextMarchMs = _marchNominalMs;
    }

    // One rank on `laneIndex`: it forms at the cordon, steps out during the `warnMs` marker, then marches. False when
    // no footman could be summoned.
    bool StartMarch(std::size_t laneIndex, bool crossing, uint32 warnMs)
    {
        MarchLane const& lane = kLanes[laneIndex];
        bool const heroic = _heroic;
        float const guessZ = kUnforgivenSpawn.z;
        float const v = MarchSpeed(lane);
        HitLine const hit = MarchHitLine(lane);

        Rank rank;
        rank.lane = laneIndex;
        rank.crossing = crossing;
        rank.marchAtMs = _clockMs + warnMs;
        rank.endAtMs = rank.marchAtMs + PassMs(lane);
        Creature* leader = nullptr;
        uint32 const stepMs = warnMs > 500 ? warnMs - 250 : warnMs;
        for (uint32 i = 0; i < lane.footmen; ++i)
        {
            Vec2 const form = RankPoint(lane, i, lane.formX);
            Vec2 const start = RankPoint(lane, i, lane.startX);
            Vec2 const end = RankPoint(lane, i, lane.frame.sizeX);
            Creature* footman = SummonFootman(form, guessZ, lane.frame.angle);
            if (!footman)
                continue;
            footman->SetWalk(false);
            float const z = footman->GetPositionZ();
            std::vector<DungeonKit::FloorPathPoint> const step = DungeonKit::FloorPathOnMap(me, form, start, z);
            float const stepSpeed = DungeonKit::Distance(form, start) * 1000.f / static_cast<float>(stepMs);
            DungeonKit::MoveAlongFloor(footman, step, std::max(1.f, stepSpeed));
            float const startZ = step.empty() ? z : step.back().z;
            rank.paths.push_back(DungeonKit::FloorPathOnMap(me, start, end, startZ));
            rank.footmen.push_back(footman->GetGUID());
            if (i == RankLeader(lane))
                leader = footman;
        }
        if (rank.footmen.empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "march-fail", lane.name);
            return false;
        }
        if (!leader)
            leader = ObjectAccessor::GetCreature(*me, rank.footmen.front());

        Position const from = DungeonKit::ToPosition(hit.from, FloorZ(me, hit.from.x, hit.from.y, guessZ));
        Position const to = DungeonKit::ToPosition(hit.to, FloorZ(me, hit.to.x, hit.to.y, guessZ));
        float const pct = kMarchPct(heroic);
        MechanicRef ref = Mechanic::Line(me, from, to, hit.width, Ms(warnMs));
        ref.Projectile(v).ProjectileUnit(leader).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_SHADOW)
            .Spell(SPELL_UF_MARCH_HIT).Weakened().Tag(crossing ? TAG_MARCH_CROSSING : TAG_MARCH);
        if (heroic && !crossing)
            ref.OnResolve(OnUnforgiven([gen = _generation, laneIndex](boss_the_unforgiven_rework& ai,
                BossMechanics::ResolveResult const& result)
            {
                if (gen != ai._generation)
                    return;
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "march-passed",
                    Acore::StringFormat("lane={} hits={}", kLanes[laneIndex].name, result.hits.size()));
                ai.StartMarch(OtherLane(laneIndex), true, kMarchChainWarnMs);
            }));
        rank.line = ref.Handle();
        Track(rank.line);

        // The nova's gate: the floor is busy until this pass (and, heroic, the crossing rank's) is over.
        uint64 busy = rank.endAtMs;
        if (heroic && !crossing)
            busy += kMarchChainWarnMs + PassMs(kLanes[OtherLane(laneIndex)]);
        _busyUntilMs = std::max(_busyUntilMs, busy);

        if (!crossing)
            Talk(YELL_UNFORGIVEN_MARCH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, crossing ? "march-crossing" : "march",
            Acore::StringFormat("heroic={} lane={} footmen={} pct={:.0f} warn={}ms speed={:.1f} length={:.1f}",
                heroic ? 1 : 0, lane.name, rank.footmen.size(), pct, warnMs, v, hit.Length()));
        _ranks.push_back(std::move(rank));
        return true;
    }

    void UpdateRanks()
    {
        for (auto it = _ranks.begin(); it != _ranks.end();)
        {
            Rank& rank = *it;
            if (!rank.marching && _clockMs >= rank.marchAtMs)
            {
                rank.marching = true;
                float const v = MarchSpeed(kLanes[rank.lane]);
                for (std::size_t i = 0; i < rank.footmen.size(); ++i)
                    if (Creature* footman = ObjectAccessor::GetCreature(*me, rank.footmen[i]))
                    {
                        footman->StopMoving();
                        DungeonKit::MoveAlongFloor(footman, rank.paths[i], v);
                    }
            }
            if (_clockMs >= rank.endAtMs + kRankFadeMs)
            {
                DespawnRank(rank);
                it = _ranks.erase(it);
            }
            else
                ++it;
        }
    }

    void DespawnRank(Rank const& rank)
    {
        for (ObjectGuid const& guid : rank.footmen)
            if (Creature* footman = ObjectAccessor::GetCreature(*me, guid))
                footman->DespawnOrUnsummon();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF2-UF4 Fires
    // ----------------------------------------------------------------------------------------------------------------

    struct Fire
    {
        std::size_t spot = 0;
        bool landed = false;
        uint64 landAtMs = 0;
        uint64 endAtMs = 0;
        ObjectGuid stalker;
        ObjectGuid flames;
        MechanicHandle soak;
    };

    std::array<bool, kFireSpotCount> BurningSpots() const
    {
        std::array<bool, kFireSpotCount> burning{};
        for (Fire const& fire : _fires)
            burning[fire.spot] = true;
        return burning;
    }

    // The burning houses (landed fires): the firelight's centers.
    std::vector<Vec2> LitFires() const
    {
        std::vector<Vec2> lit;
        for (Fire const& fire : _fires)
            if (fire.landed)
                lit.push_back(FireSpot(fire.spot));
        return lit;
    }

    bool InLight(Vec2 p) const
    {
        return InFirelight(p, LitFires());
    }

    void UpdateFires()
    {
        if (_clockMs >= _nextFireMs)
        {
            bool started = false;
            if (FireCanLight(static_cast<uint32>(_fires.size())))
                started = StartFire(std::nullopt);
            if (started)
            {
                _fireNominalMs = NextOnCadence(_fireNominalMs, _clockMs, kFireEveryMs(_heroic));
                _nextFireMs = _fireNominalMs;
            }
            else
                _nextFireMs = _clockMs + kFireRetryMs;
        }
        for (auto it = _fires.begin(); it != _fires.end();)
        {
            Fire& fire = *it;
            if (!fire.landed && _clockMs >= fire.landAtMs)
                LandFire(fire);
            if (_clockMs >= fire.endAtMs)
            {
                EndFire(fire);
                it = _fires.erase(it);
            }
            else
                ++it;
        }
    }

    // UF2: a fire at `spot` (none: a random free bay). False when that bay burns, every bay burns or the stalker
    // failed.
    bool StartFire(std::optional<std::size_t> spot)
    {
        if (!spot)
            spot = PickFireSpot(BurningSpots(), [](uint32 n) { return urand(0, n - 1); });
        if (!spot || BurningSpots()[*spot])
            return false;
        Vec2 const at = FireSpot(*spot);
        float const z = FloorZ(me, at.x, at.y, kFireSpotZ[*spot]);
        Creature* stalker = me->SummonCreature(NPC_ST_HOUSE_FIRE, at.x, at.y, z, 0.f, TEMPSUMMON_MANUAL_DESPAWN);
        if (!stalker)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fire-fail", "no stalker");
            return false;
        }
        stalker->SetReactState(REACT_PASSIVE);
        Position const pos(at.x, at.y, z, 0.f);

        DungeonKit::ImpactSpec impact;
        impact.shape = BossMechanics::Shapes::Circle(BossMechanics::Anchor(pos), kFireRadius);
        impact.warn = Ms(kFireWarnMs);
        impact.pct = kFireLandPct;
        impact.tankPct = kFireLandPct;
        impact.school = SPELL_SCHOOL_FIRE;
        impact.spellId = SPELL_UF_HOUSE_FIRE;
        impact.weakened = true;
        impact.tag = TAG_HOUSE_FIRE;
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(kFireBurnMs);
        linger.tick = Ms(kFireTickMs);
        linger.pct = kFireBurnPct;
        linger.school = SPELL_SCHOOL_FIRE;
        linger.spellId = SPELL_UF_BURNING_HOUSE;
        linger.slow = false;
        linger.tag = TAG_BURNING_HOUSE;
        MechanicHandle const impactHandle = DungeonKit::ImpactThenLinger(me, impact, linger);
        Track(impactHandle);

        Fire fire;
        fire.spot = *spot;
        fire.landAtMs = _clockMs + kFireWarnMs;
        fire.endAtMs = fire.landAtMs + kFireBurnMs;
        fire.stalker = stalker->GetGUID();
        _fires.push_back(fire);
        Talk(EMOTE_UNFORGIVEN_HOUSE_FIRE);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fire",
            Acore::StringFormat("heroic={} spot={} burning={} pct={:.0f}", _heroic ? 1 : 0, *spot, _fires.size(),
                kFireLandPct));
        return true;
    }

    // UF3 / UF4: the house burns; its firelight is the accused's place.
    void LandFire(Fire& fire)
    {
        fire.landed = true;
        Vec2 const at = FireSpot(fire.spot);
        Creature* stalker = ObjectAccessor::GetCreature(*me, fire.stalker);
        float const z = stalker ? stalker->GetPositionZ() : kFireSpotZ[fire.spot];
        if (stalker)
        {
            stalker->CastSpell(stalker, SPELL_UF_FIRELIGHT, TRIGGERED_FULL_MASK);
            if (GameObject* flames = stalker->SummonGameObject(GO_UF_HOUSE_FIRE_STOCK, at.x, at.y, z, 0.f, 0.f, 0.f,
                0.f, 0.f, kFireBurnMs / IN_MILLISECONDS))
                fire.flames = flames->GetGUID();
        }
        Position const pos(at.x, at.y, z, 0.f);
        MechanicRef ref = Mechanic::Soak(me, BossMechanics::Shapes::Donut(BossMechanics::Anchor(pos), kFirelightInner,
            kFirelightOuter), kFirelightSoakers, Ms(kFirelightSoakWarnMs));
        ref.Eligible(AccusedOnly()).Persistent(Ms(kFireBurnMs - kFirelightSoakWarnMs), Ms(kFireTickMs))
            .OneClaimPerBot().MissedSoak(BossMechanics::MissedSoakMode::OnChange).Tag(TAG_FIRELIGHT);
        fire.soak = ref.Handle();
        Track(fire.soak);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fire-landed",
            Acore::StringFormat("spot={} flames={}", fire.spot, fire.flames ? 1 : 0));
    }

    void EndFire(Fire const& fire)
    {
        if (fire.soak)
            Mechanic::Cancel(me, fire.soak);
        if (Map* map = me->FindMap())
            if (GameObject* flames = map->GetGameObject(fire.flames))
                flames->Delete();
        if (Creature* stalker = ObjectAccessor::GetCreature(*me, fire.stalker))
            stalker->DespawnOrUnsummon();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF5-UF9, UF11 Phantoms
    // ----------------------------------------------------------------------------------------------------------------

    struct PhantomRec
    {
        ObjectGuid accused;
        uint64 bornMs = 0;
        bool returning = false;
    };

    // A phantom at `at`, fixated on `accused` (who carries Accused while it hunts them).
    bool RaisePhantom(Vec2 at, Player* accused, bool returning)
    {
        if (!accused)
            return false;
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_VENGEFUL_PHANTOM;
        spec.passive = true;
        spec.type = TEMPSUMMON_CORPSE_TIMED_DESPAWN;
        spec.despawn = 5000ms;
        std::vector<Position> const where{ Position(at.x, at.y, FloorZ(me, at.x, at.y, me->GetPositionZ()),
            DungeonKit::BearingTo(at, DungeonKit::PlaneOf(accused))) };
        std::vector<Creature*> const wave = DungeonKit::SummonWave(me, spec, where, summons);
        if (wave.empty())
            return false;
        Creature* phantom = wave.front();
        PhantomRec rec;
        rec.accused = accused->GetGUID();
        rec.bornMs = _clockMs;
        rec.returning = returning;
        _phantoms[phantom->GetGUID()] = rec;
        if (phantom->IsAIEnabled)
            phantom->AI()->SetGUID(accused->GetGUID(), ACTION_PHANTOM_FIXATE);
        Accuse(accused);
        return true;
    }

    void Accuse(Player* player)
    {
        if (!player->HasAura(SPELL_UF_ACCUSED))
        {
            me->AddAura(SPELL_UF_ACCUSED, player);
            me->CastSpell(player, SPELL_UF_ACCUSED_FLASH, TRIGGERED_FULL_MASK);
        }
    }

    // Accused lasts while a phantom still hunts its bearer.
    void ReleaseAccused(ObjectGuid accused)
    {
        for (auto const& [guid, rec] : _phantoms)
            if (rec.accused == accused)
                return;
        if (Player* player = ObjectAccessor::GetPlayer(*me, accused))
            player->RemoveAurasDueToSpell(SPELL_UF_ACCUSED);
    }

    void UpdateAccusation()
    {
        if (_lastSoul || _clockMs < _nextAccuseMs)
            return;
        if (StartAccusation())
        {
            _accuseNominalMs = NextOnCadence(_accuseNominalMs, _clockMs, kAccusation.every);
            _nextAccuseMs = _accuseNominalMs;
        }
        else
            _nextAccuseMs = _clockMs + kFireRetryMs;
    }

    // UF5: Accused on a random non-tank and 3 (heroic 4) phantoms around him.
    bool StartAccusation()
    {
        Player* accused = PickNonTank();
        if (!accused)
            return false;
        uint32 const n = kPhantomCount(_heroic);
        uint32 raised = 0;
        for (uint32 i = 0; i < n; ++i)
            if (RaisePhantom(PhantomRisePoint(DungeonKit::PlaneOf(me), i, n), accused, false))
                ++raised;
        Talk(YELL_UNFORGIVEN_ACCUSED, accused);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "accusation",
            Acore::StringFormat("heroic={} accused={} phantoms={} lit={}", _heroic ? 1 : 0, accused->GetName(), raised,
                LitFires().size()));
        return raised > 0;
    }

    // UF9: every Grudge stack rises again, each on a random non-tank.
    void StartLastSoul()
    {
        _lastSoul = true;
        Talk(YELL_UNFORGIVEN_LAST_SOUL);
        uint32 const n = LastSoulPhantoms(DungeonKit::Stacks(me, SPELL_UF_GRUDGE));
        uint32 raised = 0;
        for (uint32 i = 0; i < n; ++i)
            if (RaisePhantom(PhantomRisePoint(DungeonKit::PlaneOf(me), i, n), PickNonTank(), true))
                ++raised;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "last-soul",
            Acore::StringFormat("health={:.1f}% grudge={} phantoms={}", me->GetHealthPct(), n, raised));
    }

    void UpdateHaunting()
    {
        if (!_heroic || _clockMs < _nextHauntMs)
            return;
        StartHaunting();
        _hauntNominalMs = NextOnCadence(_hauntNominalMs, _clockMs, kHaunting.every);
        _nextHauntMs = _hauntNominalMs;
    }

    // UF11: the Magic DoT on 2 random non-tanks.
    uint32 StartHaunting()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;
        std::string names;
        uint32 count = 0;
        for (Player* player : DungeonKit::PickPlayers(me, rule, kHauntingCount))
        {
            me->CastSpell(player, SPELL_UF_HAUNTING_MEMORY, TRIGGERED_FULL_MASK);
            names += " " + player->GetName();
            ++count;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "haunting-memory",
            Acore::StringFormat("count={}{}", count, names));
        return count;
    }

    // UF11: the aura ran out on `player` (spell_st_unforgiven_haunting_memory): a phantom rises by them.
    void HauntingExpired(Player* player)
    {
        if (!player || !player->IsAlive() || !me->IsEngaged())
            return;
        bool const raised = RaisePhantom(HauntingRisePoint(DungeonKit::PlaneOf(player)), player, false);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "haunting-expired",
            Acore::StringFormat("{} phantom={}", player->GetName(), raised ? 1 : 0));
    }

    // UF6: the tear, taken by the script and logged under Freed (R-2-A A-4): the exact amount from his maximum health,
    // never scaled by a damage-taken debuff on him (a spell cast goes through his taken modifiers, DealDamage through
    // the damage hooks) and never his last point (FreedAmount caps it at his health - 1; ModifyHealth cannot kill).
    void TearFreed(uint32 tear)
    {
        if (!tear)
            return;
        SpellInfo const* info = sSpellMgr->GetSpellInfo(SPELL_UF_FREED);
        if (!info)
            return;
        SpellNonMeleeDamage log(me, me, info, info->GetSchoolMask());
        log.damage = tear;
        me->SendSpellNonMeleeDamageLog(&log);
        me->ModifyHealth(-static_cast<int32>(tear));
    }

    // How a phantom ends (UnforgivenLogic.h Outcome). `phantom` may be null (gone).
    void EndPhantom(ObjectGuid guid, PhantomEnd end, Creature* phantom)
    {
        auto it = _phantoms.find(guid);
        if (it == _phantoms.end())
            return;
        PhantomRec const rec = it->second;
        _phantoms.erase(it);
        PhantomOutcome const o = Outcome(end, rec.returning);
        Player* accused = ObjectAccessor::GetPlayer(*me, rec.accused);
        uint32 tear = 0;
        if (o.freed)
        {
            ++_freed;
            tear = FreedAmount(me->GetMaxHealth(), me->GetHealth());
            TearFreed(tear);
        }
        else
            ++_bound;
        if (o.grief && accused && accused->IsAlive())
            me->CastSpell(accused, SPELL_UF_GRIEF, TRIGGERED_FULL_MASK);
        if (o.grudgeDelta > 0)
            me->CastSpell(me, SPELL_UF_BOUND, TRIGGERED_FULL_MASK);
        if (o.grudgeDelta)
            DungeonKit::AddStacks(me, SPELL_UF_GRUDGE, o.grudgeDelta, me, kGrudgeMaxStacks);
        if (!o.freed && phantom && phantom->IsAlive())
            phantom->DespawnOrUnsummon();
        ReleaseAccused(rec.accused);
        static char const* const kEnds[] = { "freed", "bound-dark", "bound-expired", "grief" };
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "phantom",
            Acore::StringFormat("{} returning={} accused={} tear={} grudge={}", kEnds[static_cast<uint8>(end)],
                rec.returning ? 1 : 0, accused ? accused->GetName() : "gone", tear,
                DungeonKit::Stacks(me, SPELL_UF_GRUDGE)));
    }

    // Every 250 ms: the firelight marks, the phantoms' ends, the Last Soul's trigger.
    void UpdateHousekeeping()
    {
        if (_clockMs < _housekeepMs)
            return;
        _housekeepMs = _clockMs + kHousekeepingMs;

        std::vector<Vec2> const lit = LitFires();
        std::vector<std::pair<ObjectGuid, PhantomEnd>> ends;
        for (auto& [guid, rec] : _phantoms)
        {
            Creature* phantom = ObjectAccessor::GetCreature(*me, guid);
            if (!phantom || !phantom->IsAlive())
                continue;       // a death is settled by SummonedCreatureDies
            bool const light = InFirelight(DungeonKit::PlaneOf(phantom), lit);
            if (light && !phantom->HasAura(SPELL_UF_IN_FIRELIGHT))
                me->AddAura(SPELL_UF_IN_FIRELIGHT, phantom);
            else if (!light && phantom->HasAura(SPELL_UF_IN_FIRELIGHT))
                phantom->RemoveAurasDueToSpell(SPELL_UF_IN_FIRELIGHT);

            if (_clockMs >= rec.bornMs + kPhantomLifeMs)
            {
                ends.emplace_back(guid, PhantomEnd::Expired);
                continue;
            }
            Player* accused = ObjectAccessor::GetPlayer(*me, rec.accused);
            if (!accused || !accused->IsAlive() || accused->IsGameMaster())
            {
                // Its accused is gone: it hunts another non-tank (who becomes accused).
                Player* next = PickNonTank();
                if (!next)
                {
                    ends.emplace_back(guid, PhantomEnd::Expired);
                    continue;
                }
                ObjectGuid const old = rec.accused;
                rec.accused = next->GetGUID();
                if (phantom->IsAIEnabled)
                    phantom->AI()->SetGUID(rec.accused, ACTION_PHANTOM_FIXATE);
                Accuse(next);
                _releaseLater.push_back(old);
                continue;
            }
            if (_clockMs >= rec.bornMs + kPhantomRiseMs && phantom->GetExactDist2d(accused) <= kPhantomReachYd)
                ends.emplace_back(guid, PhantomEnd::Reached);
        }
        for (auto const& [guid, end] : ends)
            EndPhantom(guid, end, ObjectAccessor::GetCreature(*me, guid));
        for (ObjectGuid const& old : _releaseLater)
            ReleaseAccused(old);
        _releaseLater.clear();

        if (LastSoulDue(me->GetHealthPct(), _lastSoul))
            StartLastSoul();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF10 Frost Nova
    // ----------------------------------------------------------------------------------------------------------------

    bool PlayerNear() const
    {
        for (Player* player : AlivePlayers())
            if (me->GetExactDist2d(player) <= kNovaRadius)
                return true;
        return false;
    }

    void UpdateNova()
    {
        if (_clockMs < _nextNovaMs)
            return;
        if (!NovaAllowed(_clockMs, _nextMarchMs + kMarchWarnMs, _busyUntilMs) || !PlayerNear())
        {
            _nextNovaMs = _clockMs + kNovaRetryMs;
            return;
        }
        CastNova();
    }

    void CastNova()
    {
        me->CastSpell(me, SPELL_UF_FROST_NOVA, TRIGGERED_FULL_MASK);
        _nextNovaMs = _clockMs + urand(kNovaMinMs, kNovaMaxMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "frost-nova",
            Acore::StringFormat("pct={:.0f} root={}ms next={}s", kNovaPct, kNovaRootMs, _nextNovaMs / 1000));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ST): phantoms in the firelight are kill targets (AoE fine), outside it they are left alone; heroic:
    // dispel Haunting Memory. No interrupt list.
    // ----------------------------------------------------------------------------------------------------------------

    void Describe(bool heroic)
    {
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_VENGEFUL_PHANTOM, 2, BossMechanics::Who::Dps,
            BossMechanics::Condition::HasAura(SPELL_UF_IN_FIRELIGHT)).AoeOk());
        d.ignores.emplace_back(NPC_VENGEFUL_PHANTOM, BossMechanics::Condition::LacksAura(SPELL_UF_IN_FIRELIGHT));
        if (heroic)
            d.dispels.emplace_back(SPELL_UF_HAUNTING_MEMORY, kHauntingDispelPriority, false,
                Ms(kHauntingDeadlineMs));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest strat unforgiven` entry points (`heroic` forces the heroic form on a normal map until the next pull)
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestMarch(std::optional<std::size_t> lane, bool heroic)
    {
        if (!me->IsEngaged())
            return "The Unforgiven must be in combat.";
        _heroic = heroic;
        std::size_t const l = lane ? std::min<std::size_t>(*lane, kLaneCount - 1) : _nextLane;
        if (!StartMarch(l, false, kMarchWarnMs))
            return "No footman could be summoned.";
        return {};
    }

    std::string TestFire(std::optional<std::size_t> spot, bool heroic)
    {
        if (!me->IsEngaged())
            return "The Unforgiven must be in combat.";
        _heroic = heroic;
        if (spot && *spot >= kFireSpotCount)
            return "Fire spots are 0 to 4 (F1, F2, F3, F4, F6).";
        if (!StartFire(spot))
            return "That bay burns already, or every bay burns (or no stalker).";
        return {};
    }

    std::string TestAccuse(bool heroic)
    {
        if (!me->IsEngaged())
            return "The Unforgiven must be in combat (the accused is picked from his threat list).";
        _heroic = heroic;
        if (!StartAccusation())
            return "Nobody to accuse.";
        return {};
    }

    std::string TestNova()
    {
        if (!me->IsEngaged())
            return "The Unforgiven must be in combat.";
        CastNova();
        return {};
    }

    std::string TestHaunting()
    {
        if (!me->IsEngaged())
            return "The Unforgiven must be in combat.";
        if (!StartHaunting())
            return "Nobody to haunt.";
        return {};
    }

    std::string TestLastSoul()
    {
        if (!me->IsEngaged())
            return "The Unforgiven must be in combat.";
        if (_lastSoul)
            return "The Last Soul already rose this pull.";
        StartLastSoul();
        return {};
    }

    uint32 TestGrudge(int32 delta)
    {
        return DungeonKit::AddStacks(me, SPELL_UF_GRUDGE, delta, me, kGrudgeMaxStacks);
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} walls={} ranks={} fires={} (lit {}) phantoms={} grudge={} "
            "lastSoul={} next march/fire/accuse/nova/haunt={}/{}/{}/{}/{}s nextLane={} freed={} bound={}",
            _clockMs / 1000, _heroic ? 1 : 0, _walls.Count(), _ranks.size(), _fires.size(), LitFires().size(),
            _phantoms.size(), DungeonKit::Stacks(me, SPELL_UF_GRUDGE), _lastSoul ? 1 : 0, _nextMarchMs / 1000,
            _nextFireMs / 1000, _lastSoul ? int64(-1) : int64(_nextAccuseMs / 1000), _nextNovaMs / 1000,
            _heroic ? int64(_nextHauntMs / 1000) : int64(-1), kLanes[_nextLane].name, _freed, _bound);
    }

    // The phantom's look as its killing blow lands (npc_st_vengeful_phantom): is it in the firelight?
    bool PhantomInLight(Creature const* phantom) const
    {
        return InLight(DungeonKit::PlaneOf(phantom));
    }

private:
    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnUnforgiven(Fn fn)
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
            if (auto* ai = dynamic_cast<boss_the_unforgiven_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // The pull's state: no walls, ranks, fires or phantoms, no Accused, Haunting Memory or Grudge (Reset, evade, death,
    // a new pull).
    void Cleanup()
    {
        ++_generation;      // a chained crossing rank of an older pull stops
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        LowerCordon(false);
        for (Rank const& rank : _ranks)
            DespawnRank(rank);
        _ranks.clear();
        for (Fire const& fire : _fires)
            EndFire(fire);
        _fires.clear();
        std::vector<ObjectGuid> phantoms;
        for (auto const& [guid, rec] : _phantoms)
            phantoms.push_back(guid);
        _phantoms.clear();
        for (ObjectGuid const& guid : phantoms)
            if (Creature* phantom = ObjectAccessor::GetCreature(*me, guid))
                phantom->DespawnOrUnsummon();
        _releaseLater.clear();
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                {
                    player->RemoveAurasDueToSpell(SPELL_UF_ACCUSED);
                    player->RemoveAurasDueToSpell(SPELL_UF_HAUNTING_MEMORY);
                }
        me->RemoveAurasDueToSpell(SPELL_UF_GRUDGE);
        _clockMs = 0;
        _marchNominalMs = _nextMarchMs = 0;
        _fireNominalMs = _nextFireMs = 0;
        _accuseNominalMs = _nextAccuseMs = 0;
        _hauntNominalMs = _nextHauntMs = 0;
        _nextNovaMs = 0;
        _busyUntilMs = 0;
        _housekeepMs = 0;
        _lastSoul = false;
        _freed = 0;
        _bound = 0;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::LethalWalls _walls;
    std::vector<ObjectGuid> _cordonFootmen;
    std::vector<Rank> _ranks;
    std::vector<Fire> _fires;
    std::unordered_map<ObjectGuid, PhantomRec> _phantoms;
    std::vector<ObjectGuid> _releaseLater;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _marchNominalMs = 0;                 // planned starts (start to start)
    uint64 _nextMarchMs = 0;
    uint64 _fireNominalMs = 0;
    uint64 _nextFireMs = 0;
    uint64 _accuseNominalMs = 0;
    uint64 _nextAccuseMs = 0;
    uint64 _hauntNominalMs = 0;
    uint64 _nextHauntMs = 0;
    uint64 _nextNovaMs = 0;
    uint64 _busyUntilMs = 0;                    // ranks on the floor until then (the nova's gate)
    uint64 _housekeepMs = 0;
    std::size_t _nextLane = 0;
    uint32 _generation = 0;
    uint32 _freed = 0;
    uint32 _bound = 0;
    bool _heroic = false;
    bool _lastSoul = false;
};

namespace
{
    boss_the_unforgiven_rework* UnforgivenAI(Unit* unit)
    {
        Creature* boss = unit ? unit->ToCreature() : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_the_unforgiven_rework*>(boss->AI());
    }
}

// Vengeful Phantom 10387 (UF5-UF9): rises, then drifts at 60% walk to its accused. It never fights and cannot be
// taunted; the boss settles its end (UnforgivenLogic.h Outcome).
struct npc_st_vengeful_phantom : public ScriptedAI
{
    explicit npc_st_vengeful_phantom(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        ScriptedAI::InitializeAI();
        me->SetReactState(REACT_PASSIVE);
        me->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TAUNT, true);
        me->ApplySpellImmune(0, IMMUNITY_EFFECT, SPELL_EFFECT_ATTACK_ME, true);
    }

    void Reset() override { }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    void SetGUID(ObjectGuid const& guid, int32 id) override
    {
        if (id != ACTION_PHANTOM_FIXATE)
            return;
        bool const first = _accused.IsEmpty();
        _accused = guid;
        if (first)
            _riseMs = kPhantomRiseMs;
        _repathMs = 0;
    }

    // UF6: the killing blow in the firelight plays Soul Freed (while it still stands).
    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (_lookPlayed || damage < me->GetHealth())
            return;
        TempSummon* summon = me->ToTempSummon();
        if (auto* ai = summon ? UnforgivenAI(summon->GetSummonerUnit()) : nullptr)
            if (ai->PhantomInLight(me))
            {
                _lookPlayed = true;
                me->CastSpell(me, SPELL_UF_SOUL_FREED, TRIGGERED_FULL_MASK);
            }
    }

    void UpdateAI(uint32 diff) override
    {
        if (_accused.IsEmpty())
            return;
        if (_riseMs)
        {
            _riseMs = _riseMs > diff ? _riseMs - diff : 0;
            return;
        }
        if (_repathMs > diff)
        {
            _repathMs -= diff;
            return;
        }
        _repathMs = kPhantomRepathMs;
        Unit* target = ObjectAccessor::GetUnit(*me, _accused);
        if (!target || !target->IsAlive())
        {
            me->StopMoving();
            return;
        }
        me->GetMotionMaster()->MovePoint(POINT_PHANTOM_DRIFT, target->GetPositionX(), target->GetPositionY(),
            target->GetPositionZ(), FORCED_MOVEMENT_WALK, kPhantomSpeedYd);
    }

private:
    ObjectGuid _accused;
    uint32 _riseMs = 0;
    uint32 _repathMs = 0;
    bool _lookPlayed = false;
};

// Spectral Footman 300600 (UF1, UF12): stands in the cordon or marches in a rank; the boss moves it. Never fights.
struct npc_st_spectral_footman : public NullCreatureAI
{
    explicit npc_st_spectral_footman(Creature* creature) : NullCreatureAI(creature) { }
};

// UF11 Haunting Memory (206432): run out (not dispelled, not a death): the boss raises a phantom by the carrier. The
// tick is the kit's spell_dungeon_refflat_periodic (bound beside this one).
class spell_st_unforgiven_haunting_memory : public AuraScript
{
    PrepareAuraScript(spell_st_unforgiven_haunting_memory);

    void OnRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_EXPIRE)
            return;
        Player* carrier = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (auto* ai = UnforgivenAI(GetCaster()))
            ai->HauntingExpired(carrier);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_st_unforgiven_haunting_memory::OnRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

namespace
{
    boss_the_unforgiven_rework* FindUnforgivenAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_UNFORGIVEN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_the_unforgiven_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Unforgiven is not running boss_the_unforgiven_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Done(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("The Unforgiven: {} fired.", what);
        return true;
    }

    bool Heroic(boss_the_unforgiven_rework* ai, Optional<uint32> heroic)
    {
        return heroic ? *heroic != 0 : ai->HeroicMap();
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_UNFORGIVEN, BOSS_UNFORGIVEN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("The Unforgiven: {}", ai->TestState());
        return true;
    }

    // `.dbtest strat unforgiven march [lane 0|1] [heroic]`: 0 Market Row, 1 the passage (default: the next lane).
    bool HandleMarch(ChatHandler* handler, Optional<uint32> lane, Optional<uint32> heroic)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        std::optional<std::size_t> l;
        if (lane)
            l = *lane;
        return Done(handler, ai->TestMarch(l, Heroic(ai, heroic)),
            "the March (UF1; heroic: the crossing rank after it)");
    }

    // `.dbtest strat unforgiven fire [spot 0-4] [heroic]`
    bool HandleFire(ChatHandler* handler, Optional<uint32> spot, Optional<uint32> heroic)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        std::optional<std::size_t> s;
        if (spot)
            s = *spot;
        return Done(handler, ai->TestFire(s, Heroic(ai, heroic)), "a house fire (UF2-UF4)");
    }

    bool HandleAccuse(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        return Done(handler, ai->TestAccuse(Heroic(ai, heroic)), "the Accusation (UF5-UF8)");
    }

    bool HandleNova(ChatHandler* handler)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        return Done(handler, ai->TestNova(), "Frost Nova (UF10)");
    }

    bool HandleHaunt(ChatHandler* handler)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        return Done(handler, ai->TestHaunting(), "Haunting Memory (UF11)");
    }

    bool HandleLastSoul(ChatHandler* handler)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        return Done(handler, ai->TestLastSoul(), "the Last Soul (UF9)");
    }

    // `.dbtest strat unforgiven grudge <n>`: n Grudge stacks on him (negative removes).
    bool HandleGrudge(ChatHandler* handler, int32 delta)
    {
        boss_the_unforgiven_rework* ai = FindUnforgivenAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("The Unforgiven: now {} stack(s) of Grudge.", ai->TestGrudge(delta));
        return true;
    }

    ChatCommandTable const& UnforgivenTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "march",      HandleMarch,        SEC_GAMEMASTER, Console::No },
            { "fire",       HandleFire,         SEC_GAMEMASTER, Console::No },
            { "accuse",     HandleAccuse,       SEC_GAMEMASTER, Console::No },
            { "nova",       HandleNova,         SEC_GAMEMASTER, Console::No },
            { "haunt",      HandleHaunt,        SEC_GAMEMASTER, Console::No },
            { "lastsoul",   HandleLastSoul,     SEC_GAMEMASTER, Console::No },
            { "grudge",     HandleGrudge,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_the_unforgiven_rework()
{
    RegisterDungeonReworkCreatureAI(boss_the_unforgiven_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_vengeful_phantom, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_spectral_footman, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_st_unforgiven_haunting_memory);
    StratTest::RegisterBoss("unforgiven", UnforgivenTestCommands());
}
