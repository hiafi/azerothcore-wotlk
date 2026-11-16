/*
 * mod-dungeon-bosses, Blackrock Spire B1: Highlord Omokk (9196), "Might Makes Right" (ruling 15). Build spec SP
 * "Highlord Omokk" (docs/dungeons/blackrock-spire-rework.md, rulings 15-23, Build spec OM1-OM11), handoff sections
 * 3.4 rows OM, 3.5 row B1, 3.6, 3.8 (NM 1), 3.9 (drill row 0) and 3.10 gap 6. Replaces the stock boss_highlord_omokk
 * (Frenzy 8269, Knock Away 10101; unbound by apps/dbc-tools source/npcs/blackrock_spire/omokk.py, which binds this
 * script). The SQL rev rev_highlord_omokk_blackrock_spire.sql gives him his texts and removes the Mystic 43514 and
 * the Ogre Magus 43515 beside him. Pure rules: OmokkLogic.h.
 *
 *   OM1  The Ring          at the pull he yells and 18 Spirestone Brawl Fans (300700) run in from the doorway to the
 *                          stands (the north alcoves, the rock pile, the doorway). The band, 3 s later: a persistent
 *                          2 yd registry Line per strip (OmokkLogic.h kHallBand), red, ticking every 0.5 s: Crowd
 *                          Shove 25% / 35% + Weakened, 8 yd thrown toward the ring's middle, a Roar stack. A player
 *                          on the pile (OnThePile, polled every 0.5 s) gets the same shove from the script (210021)
 *   OM2  Haymaker          10 s, then every 15 s: a 2.5 s cast bar (emote line 1 per target) and one 5 x 30 yd line
 *                          from him toward each of 1 / 2 random non-tanks' spots at the cast start: 40% / 50%, thrown
 *                          15 yd along the line, a Roar stack per player hit. Heroic: in the first line's resolve a
 *                          second line toward the same player's new spot, 1.5 s (the blackrock-spire-followups drill,
 *                          row 0 / tag 2)
 *   OM3  Pelting           6 s, then every 12 s / 10 s: a 4 yd circle under each of 2 / 4 (heroic 3 / 6) random
 *                          players and under every Weakened player, 2 s: 25% / 30% + Weakened. A fan throws a bottle
 *                          at each (one of the six bottle looks), timed to land with it. Never lands while a Haymaker
 *                          line is down, nor within 1 s after the last punch (FirstClearStart)
 *   OM4  Crowd's Roar      +10% damage and attack speed a stack, 5 at most, for the fight (CrowdBook::Feed)
 *   OM5  The judge         every 30 s: fed, the crowd roars (emote line 2); not fed, one Roar stack off, one Booed
 *                          on (+10% damage taken, 3 at most), a rock from the crowd, emote line 3; the third Booed:
 *                          yell line 4
 *   OM6  Mojo (heroic)     20 s, then every 25 s: 1 / 2 Spirestone Mojo Mystics (300702, 12k) step out of the crowd
 *                          and chant Ogre Mojo at him (3 s, kickable; emote line 6). Landed: Mojo Frenzy (+50% damage,
 *                          +60% attack speed, 15 s) and 2 Roar stacks. Kicked, killed or landed, it goes back. Boss
 *                          data: interrupt priority 3, first in kill order
 *   OM7  To the bridge     heroic, 25%: yell line 5; Haymaker and Pelting stop, the hall's band goes; every player
 *                          and pet on his threat list jumps (2 s) to the bridge's landings (5 / 7), his victim to the
 *                          span's north end; he lands mid-bridge; the crowd moves to both doors (a strip in front of
 *                          each); the living bridge ogres (43519, 43520, 43506, 43523) step aside into the crowd
 *   OM8  Belly Slam        3 s after landing, then every 15 s: a 2 s cast bar and an 8 yd circle on him, the tank
 *                          too: 15% + Weakened, 20 yd thrown away from him
 *   OM9  Bull Rush         5 s after landing, then every 8 s, the doors in turn: 1 / 2 Spirestone Brawlers (300701)
 *                          paw at a door (2 s bar) and charge a 3 x 20 yd lane toward a random non-tank's spot: 15% +
 *                          Weakened, thrown sideways past the near edge (SideThrowAt). Never during a Belly Slam cast
 *   OM10 Pit Drop          the kit's FallWatch under the bridge: 8 yd under the deck (see OmokkLogic.h
 *                          kPitDropBelowYd: the server's view of a falling client lags) a player is caught: 70% (35%
 *                          under Slow Fall or Levitate; 210042), a Roar stack, and jumped (2 s) to the nearer door's
 *                          haul-up spot; a pet is only hauled up
 *   OM11 Reset             wipe or evade: the crowd, Brawlers and Mystics despawn, the bridge ogres go back to their
 *                          posts, his auras go, he walks home
 *   Arena                  BlackrockSpireRework::LeashOptions on OmokkArena() (the hall, the pile and ledge, the
 *                          bridge): no grips; not updated during the 2 s trip
 *
 * Every timer runs on the AI's own clock (a cast bar never pauses one). Every firing logs one INFO line
 * "brs omokk <mechanic> ..." (module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "Map.h"
#include "MechanicWeakened.h"
#include "ObjectAccessor.h"
#include "OmokkLogic.h"
#include "PassiveAI.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraDefines.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <optional>
#include <span>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsOmokk;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "omokk";

    enum MysticPoints : uint32
    {
        POINT_MYSTIC_STEP_OUT   = 1,
        POINT_MYSTIC_BACK       = 2,
    };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    Position At(Vec2 p, float z, float o = 0.f)
    {
        return Position(p.x, p.y, z, o);
    }

    // A measured spot dropped onto the floor under its probe height (kept when the floor is not found near it).
    Position Grounded(WorldObject const* ref, Point3 p, float o = 0.f)
    {
        float z = ref->GetMapHeight(p.x, p.y, p.z + 3.f);
        if (z < p.z - 8.f || z > p.z + 4.f)
            z = p.z;
        return Position(p.x, p.y, z, o);
    }

    bool CountsAsPlayer(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }

    void Throw(Unit* unit, Vec2 source, float distance, float speedZ)
    {
        if (unit && unit->IsAlive())
            unit->KnockbackFrom(source.x, source.y, KnockbackSpeedXY(distance, speedZ), speedZ);
    }

    float Distance3d(Position const& a, Position const& b)
    {
        float const dx = a.GetPositionX() - b.GetPositionX();
        float const dy = a.GetPositionY() - b.GetPositionY();
        float const dz = a.GetPositionZ() - b.GetPositionZ();
        return std::sqrt(dx * dx + dy * dy + dz * dz);
    }

    // The band's eligibility: nobody wearing the shove's lockout (OM1, SPELL_OM_SHOVED).
    BossMechanics::Eligibility NotShoved()
    {
        BossMechanics::Eligibility e;
        e.auraSpell = SPELL_OM_SHOVED;
        e.minStacks = 0;
        e.maxStacks = 0;
        return e;
    }

    DungeonKit::Arena PitRegion()
    {
        return DungeonKit::Arena(BoxRegion(kPitMinX, kPitMaxX, kPitMinY, kPitMaxY, kPitMinZ, kPitMaxZ));
    }

    std::string Where(Position const& p)
    {
        return Acore::StringFormat("({:.1f}, {:.1f}, {:.1f})", p.GetPositionX(), p.GetPositionY(), p.GetPositionZ());
    }
}

// Highlord Omokk 9196
struct boss_highlord_omokk_rework : public BossAI
{
    enum class Stage : uint8
    {
        Hall,
        Trip,       // OM7: the 2 s jump to the bridge
        Bridge,
    };

    explicit boss_highlord_omokk_rework(Creature* creature)
        : BossAI(creature, BOSS_OMOKK), _arena(OmokkArena(), LeashOptions(kBossLogName)) { }

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

        _players = OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_OMOKK;
        Mechanic::BeginEncounter(me, options);
        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        Describe();
        _arena.Engage(me);

        Talk(SAY_OM_PULL);
        SpawnHallCrowd();
        RaiseBand(kHallBand, Ms(kBandWarnMs), "hall");
        _nextHaymakerMs = kHaymakerFirstMs;
        _nextPeltingMs = kPeltingFirstMs;
        _nextJudgeMs = kJudgeEveryMs;
        _nextMojoMs = _heroic ? kMojoFirstMs : 0;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} players={} fans={} at={}", _heroic ? 1 : 0, _players, _fans.size(),
                Where(me->GetPosition())));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(SAY_OM_DEATH);
        // The crowd cheers its next highlord, then goes (BossAI::JustDied despawns the summons still listed).
        for (ObjectGuid const& guid : _fans)
            if (Creature* fan = ObjectAccessor::GetCreature(*me, guid))
            {
                fan->HandleEmoteCommand(EMOTE_ONESHOT_CHEER);
                summons.Despawn(fan);
                fan->DespawnOrUnsummon(Ms(4000));
            }
        _fans.clear();
        uint8 const roar = _crowd.Roar();
        uint8 const booed = _crowd.Booed();
        BossAI::JustDied(killer);
        Cleanup();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("roar={} booed={} stage={} killer={}", roar, booed, uint32(_stageAtDeath),
                killer ? killer->GetName() : "none"));
    }

    // The crowd and the Brawlers are props: never zoned into combat (BossAI::JustSummoned would). The Mystic is a
    // combat add of the encounter (the flex scaler holds it at its pull; the bots' interrupt and kill entries).
    void JustSummoned(Creature* summon) override
    {
        uint32 const entry = summon->GetEntry();
        if (entry == NPC_BRS_BRAWL_FAN || entry == NPC_BRS_BRAWLER)
        {
            summons.Summon(summon);
            return;
        }
        BossAI::JustSummoned(summon);
        if (entry == NPC_BRS_MOJO_MYSTIC)
            Mechanic::TrackUnit(me, summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        BossAI::SummonedCreatureDies(summon, killer);
        if (summon->GetEntry() == NPC_BRS_MOJO_MYSTIC)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mojo-killed",
                Acore::StringFormat("killer={}", killer ? killer->GetName() : "none"));
    }

    // OM6: Ogre Mojo landed on him.
    void SpellHit(Unit* caster, SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_OM_OGRE_MOJO)
            MojoLanded(caster);
    }

    // A cast bar of his broken (the showdown interrupts it): nothing to free; the registry owns the hits.
    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType damageType, SpellSchoolMask schoolMask) override
    {
        BossAI::DamageTaken(attacker, damage, damageType, schoolMask);
        if (_heroic && _stage == Stage::Hall && !_showdownQueued && me->HealthBelowPctDamaged(
            static_cast<int32>(kShowdownHealthPct), damage))
            _showdownQueued = true;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;

        // The AI's own clock: nothing below waits for a cast bar.
        _clockMs += diff;
        UpdateThrows();
        UpdateFrenzyLook(diff);
        _fall.Update(me, diff);

        if (_stage == Stage::Trip)
        {
            if (_clockMs >= _landAt)
                Land();
            return;     // no leash, no melee mid-air
        }
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        if (_showdownQueued && _stage == Stage::Hall)
        {
            StartShowdown();
            return;
        }

        if (_clockMs >= _nextJudgeMs)
        {
            _nextJudgeMs = _clockMs + kJudgeEveryMs;
            Judge();
        }
        if (_heroic && _nextMojoMs && _clockMs >= _nextMojoMs)
        {
            _nextMojoMs = _clockMs + kMojoEveryMs;
            StartMojo(false);
        }

        if (_stage == Stage::Hall)
            UpdateHall(diff);
        else
            UpdateBridge();

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    void UpdateHall(uint32 diff)
    {
        _pileCheckMs += diff;
        if (_pileCheckMs >= kPileCheckMs)
        {
            _pileCheckMs = 0;
            if (_clockMs >= kBandWarnMs)
                CheckPile();
        }
        if (_clockMs >= _nextHaymakerMs)
        {
            if (me->HasUnitState(UNIT_STATE_CASTING))
                _nextHaymakerMs = _clockMs + 250;
            else
            {
                _nextHaymakerMs = _clockMs + kHaymakerEveryMs;
                StartHaymaker(false);
            }
        }
        if (_clockMs >= _nextPeltingMs)
        {
            uint64 const start = PeltingStart(_clockMs);
            if (start > _clockMs)
                _nextPeltingMs = start;
            else
            {
                _nextPeltingMs = _clockMs + kPeltingEveryMs(_heroic);
                StartPelting(false);
            }
        }
    }

    void UpdateBridge()
    {
        if (_clockMs >= _nextSlamMs)
        {
            if (me->HasUnitState(UNIT_STATE_CASTING))
                _nextSlamMs = _clockMs + 250;
            else
            {
                _nextSlamMs = _clockMs + kBellySlamEveryMs;
                StartBellySlam();
            }
        }
        if (_clockMs >= _nextRushMs)
        {
            uint64 const start = RushStart(_clockMs);
            if (start > _clockMs)
                _nextRushMs = start;
            else
            {
                _nextRushMs = _clockMs + kBullRushEveryMs;
                StartBullRush(false);
            }
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The crowd (OM1)
    // ----------------------------------------------------------------------------------------------------------------

    void SpawnHallCrowd()
    {
        Position const from = Grounded(me, kFansRunInFrom);
        for (Point3 const& stand : kHallStands)
        {
            Position const to = Grounded(me, stand);
            TempSummon* fan = me->SummonCreature(NPC_BRS_BRAWL_FAN, from, TEMPSUMMON_MANUAL_DESPAWN);
            if (!fan)
                continue;
            fan->GetMotionMaster()->MovePoint(0, to, FORCED_MOVEMENT_RUN);
            _fans.push_back(fan->GetGUID());
        }
    }

    // OM7: the hall's crowd goes; a crowd stands at both bridge doors.
    void MoveCrowdToDoors()
    {
        for (ObjectGuid const& guid : _fans)
            if (Creature* fan = ObjectAccessor::GetCreature(*me, guid))
            {
                summons.Despawn(fan);
                fan->DespawnOrUnsummon();
            }
        _fans.clear();
        for (Point3 const& stand : kDoorStands)
        {
            float const facing = stand.y > kBridgeMiddle.y ? -float(M_PI) / 2.f : float(M_PI) / 2.f;
            if (TempSummon* fan = me->SummonCreature(NPC_BRS_BRAWL_FAN, Grounded(me, stand, facing),
                TEMPSUMMON_MANUAL_DESPAWN))
                _fans.push_back(fan->GetGUID());
        }
    }

    Creature* RandomFan()
    {
        std::vector<Creature*> live;
        for (ObjectGuid const& guid : _fans)
            if (Creature* fan = ObjectAccessor::GetCreature(*me, guid))
                if (fan->IsAlive())
                    live.push_back(fan);
        return live.empty() ? nullptr : Acore::Containers::SelectRandomContainerElement(live);
    }

    void CrowdEmote(uint32 emote, std::size_t max = 0)
    {
        std::size_t n = 0;
        for (ObjectGuid const& guid : _fans)
        {
            if (max && n >= max)
                break;
            if (Creature* fan = ObjectAccessor::GetCreature(*me, guid))
            {
                fan->HandleEmoteCommand(emote);
                ++n;
            }
        }
    }

    // The band: one persistent registry Line per strip (2 yd), red (the telegraph kit's line ladder: 92048 / 93048
    // at aspect 32 for the long pile strip, V-1 gap 6). Every player inside at a tick is shoved.
    void RaiseBand(std::span<Strip const> strips, Milliseconds warn, char const* where)
    {
        ClearBand();
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        bool const bridge = _stage != Stage::Hall;
        float const z = bridge ? kOmokkBridgeDeckZ : kHallFloorZ;
        for (Strip const& s : strips)
        {
            MechanicRef ref = Mechanic::Line(me, At(s.from, z), At(s.to, z), kBandWidth, warn);
            ref.Persistent(Ms(kBandLifeMs), Ms(kBandTickMs))
                .Damage(kCrowdShovePct(_heroic)).TankDamage(kCrowdShovePct(_heroic)).School(SPELL_SCHOOL_NORMAL)
                .Spell(SPELL_OM_CROWD_SHOVE).Weakened().Color(BossMechanics::Color::Red).NoFillTimer()
                .Eligible(NotShoved()).Tag(TAG_OM_BAND)
                .OnHit([map, bossGuid, gen, bridge](Unit* hit)
                {
                    if (boss_highlord_omokk_rework* ai = AIOf(map, bossGuid, gen))
                        ai->Shoved(hit, bridge, "band");
                });
            if (ref.IsValid())
                _band.push_back(ref.Handle());
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "band",
            Acore::StringFormat("{} strips={} pct={:.0f}", where, _band.size(), kCrowdShovePct(_heroic)));
    }

    void ClearBand()
    {
        for (MechanicHandle const& h : _band)
            Mechanic::Cancel(me, h);
        _band.clear();
    }

    // OM1: thrown back toward the middle, Weakened came with the registry's hit (the pile's script hit adds its own),
    // a Roar stack. Pets are only thrown.
    void Shoved(Unit* hit, bool bridge, char const* why)
    {
        if (!hit || !hit->IsAlive())
            return;
        Vec2 const at = DungeonKit::PlaneOf(hit);
        Vec2 const toward = bridge ? kBridgeMiddle : HallShoveToward(at);
        Throw(hit, KnockSourceToward(at, toward), kCrowdShoveKnockYd, kCrowdShoveSpeedZ);
        _shovedUntil[hit->GetGUID()] = _clockMs + kShoveLockoutMs;
        if (Aura* lockout = hit->AddAura(SPELL_OM_SHOVED, hit))
        {
            lockout->SetMaxDuration(static_cast<int32>(kShoveLockoutMs));
            lockout->SetDuration(static_cast<int32>(kShoveLockoutMs));
        }
        if (Player* player = hit->ToPlayer())
            Feed(player, "crowd-shove");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "crowd-shove",
            Acore::StringFormat("{} target={} at=({:.1f}, {:.1f})", why, hit->GetName(), at.x, at.y));
    }

    // OM1: whoever climbs the pile (walked or thrown there) is shoved back by the script.
    void CheckPile()
    {
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || player->IsFalling())
                continue;
            if (!OnThePile(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                continue;
            auto it = _shovedUntil.find(player->GetGUID());
            if (it != _shovedUntil.end() && _clockMs < it->second)
                continue;
            PileShove(player);
        }
    }

    void PileShove(Player* player)
    {
        me->CastSpell(player, SPELL_OM_PILE_SHOVE, true);
        BossMechanics::Weakened::AddStack(player);
        Shoved(player, false, "pile");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM4 / OM5 the crowd's favor
    // ----------------------------------------------------------------------------------------------------------------

    void Feed(Player* player, char const* why)
    {
        uint8 const roar = _crowd.Feed();
        SyncRoar();
        CrowdEmote(EMOTE_ONESHOT_CHEER, 4);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "roar",
            Acore::StringFormat("{} by={} stacks={}", why, player ? player->GetName() : "none", roar));
    }

    // His Crowd's Roar aura follows the book.
    void SyncRoar()
    {
        int32 const have = static_cast<int32>(DungeonKit::Stacks(me, SPELL_OM_CROWDS_ROAR, me->GetGUID()));
        int32 const want = _crowd.Roar();
        if (want != have)
            DungeonKit::AddStacks(me, SPELL_OM_CROWDS_ROAR, want - have, me, kRoarMaxStacks);
    }

    void Judge()
    {
        JudgeResult const r = _crowd.Judge();
        SyncRoar();
        if (r.verdict == Verdict::Cheered)
        {
            Talk(EMOTE_OM_CROWD_ROARS);
            CrowdEmote(EMOTE_ONESHOT_CHEER);
        }
        else
        {
            if (r.booedAdded)
                DungeonKit::AddStacks(me, SPELL_OM_BOOED, 1, me, kBooedMaxStacks);
            if (Creature* fan = RandomFan())
                fan->CastSpell(me, SPELL_OM_CROWD_ROCK, true);
            Talk(EMOTE_OM_CROWD_JEERS);
            CrowdEmote(EMOTE_ONESHOT_RUDE);
            if (r.yell)
                Talk(SAY_OM_STILL_STRONGEST);
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "judge",
            Acore::StringFormat("verdict={} roar={} booed={}", r.verdict == Verdict::Cheered ? "cheer" : "boo", r.roar,
                r.booed));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM2 Haymaker
    // ----------------------------------------------------------------------------------------------------------------

    struct Punch
    {
        ObjectGuid target;
        MechanicHandle line;
    };

    uint64 HaymakerSpanMs() const
    {
        return kHaymakerCastMs + (_heroic ? kHaymakerTwoMs : 0) + kPeltingAfterPunchMs;
    }

    // `test`: a solo tester may be the target. Returns the number of lines.
    uint32 StartHaymaker(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = test;
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, kHaymakerTargets.At(_players));
        if (targets.empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "haymaker-skipped", "no non-tank");
            return 0;
        }
        CancelPunches();
        ++_volley;
        _secondCastDone = false;
        Position const from = me->GetPosition();
        me->SetFacingToObject(targets.front());
        DungeonKit::CastBar(me, SPELL_OM_HAYMAKER_CAST, nullptr, EMOTE_OM_HAYMAKER, targets.front());
        for (std::size_t i = 1; i < targets.size(); ++i)
            Talk(EMOTE_OM_HAYMAKER, targets[i]);
        uint32 lines = 0;
        for (Player* target : targets)
            if (RegisterPunch(from, target, target->GetPosition(), Ms(kHaymakerCastMs), false))
                ++lines;
        _haymakerWindow = Window{ _clockMs, _clockMs + HaymakerSpanMs() };
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "haymaker",
            Acore::StringFormat("heroic={} lines={} pct={:.0f} first={}", _heroic ? 1 : 0, lines,
                kHaymakerPct(_heroic), targets.front()->GetName()));
        return lines;
    }

    // One line from `from` toward `aim` (frozen now), kHaymakerLength long.
    bool RegisterPunch(Position const& from, Player* target, Position const& aim, Milliseconds warn, bool second)
    {
        Vec2 const start{ from.GetPositionX(), from.GetPositionY() };
        Vec2 const end = HaymakerEnd(start, { aim.GetPositionX(), aim.GetPositionY() }, me->GetOrientation());
        Position const to = At(end, from.GetPositionZ());
        MechanicRef ref = Mechanic::Line(me, from, to, kHaymakerWidth, warn);
        float const pct = kHaymakerPct(_heroic);
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        ObjectGuid const targetGuid = target->GetGUID();
        uint32 const gen = _generation;
        uint32 const volley = _volley;
        bool const oneTwo = _heroic && !second;
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_OM_HAYMAKER)
            .Tag(second ? TAG_OM_HAYMAKER_TWO : TAG_OM_HAYMAKER)
            .OnHit([map, bossGuid, gen, start, end](Unit* hit)
            {
                if (boss_highlord_omokk_rework* ai = AIOf(map, bossGuid, gen))
                    ai->Punched(hit, start, end);
            })
            .OnResolve([map, bossGuid, gen, targetGuid, volley, oneTwo](BossMechanics::ResolveResult const& result)
            {
                if (boss_highlord_omokk_rework* ai = AIOf(map, bossGuid, gen))
                    ai->PunchLanded(targetGuid, volley, oneTwo, result.hits.size());
            });
        if (!ref.IsValid())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "haymaker-refused", target->GetName());
            return false;
        }
        _punches.push_back({ targetGuid, ref.Handle() });
        return true;
    }

    // OM2 hit: thrown 15 yd along the line, a Roar stack.
    void Punched(Unit* hit, Vec2 lineFrom, Vec2 lineTo)
    {
        if (!hit || !hit->IsAlive())
            return;
        Vec2 const at = DungeonKit::PlaneOf(hit);
        Vec2 const along{ at.x + (lineTo.x - lineFrom.x), at.y + (lineTo.y - lineFrom.y) };
        Throw(hit, KnockSourceToward(at, along), kHaymakerKnockYd, kHaymakerSpeedZ);
        if (Player* player = hit->ToPlayer())
            Feed(player, "haymaker");
    }

    // The heroic one-two: the second line toward the same player's new spot, 1.5 s (drill row 0, tag 2).
    void PunchLanded(ObjectGuid targetGuid, uint32 volley, bool oneTwo, std::size_t hits)
    {
        me->CastSpell(me, SPELL_OM_HAYMAKER_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "haymaker-lands",
            Acore::StringFormat("hits={} second={}", hits, oneTwo ? 0 : 1));
        if (!oneTwo || volley != _volley || _stage != Stage::Hall)
            return;
        Player* target = ObjectAccessor::GetPlayer(*me, targetGuid);
        if (!CountsAsPlayer(target) || target->GetMap() != me->GetMap())
            return;
        if (!_secondCastDone)
        {
            _secondCastDone = true;
            me->SetFacingToObject(target);
            DungeonKit::CastBar(me, SPELL_OM_HAYMAKER_TWO_CAST);
        }
        RegisterPunch(me->GetPosition(), target, target->GetPosition(), Ms(kHaymakerTwoMs), true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "haymaker-two", target->GetName());
    }

    void CancelPunches()
    {
        for (Punch const& p : _punches)
            Mechanic::Cancel(me, p.line);
        _punches.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM3 Pelting
    // ----------------------------------------------------------------------------------------------------------------

    struct BottleThrow
    {
        ObjectGuid fan;
        Position spot;
        uint64 at = 0;
        uint32 spell = 0;
    };

    // The earliest start for a volley due at `due`: its landing is off the open Haymaker's window and the next one's.
    uint64 PeltingStart(uint64 due) const
    {
        std::vector<Window> windows;
        if (_haymakerWindow)
            windows.push_back(*_haymakerWindow);
        windows.push_back({ _nextHaymakerMs, _nextHaymakerMs + HaymakerSpanMs() });
        return FirstClearStart(due, kPeltingFlightMs, windows);
    }

    uint32 StartPelting(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        std::vector<Player*> targets = DungeonKit::PickPlayers(me, rule, PeltingTargets(_players, _heroic));
        // Plus every Weakened player (the crowd picks on the weak).
        std::size_t const picked = targets.size();
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || !BossMechanics::Weakened::GetStacks(player))
                continue;
            if (std::find(targets.begin(), targets.end(), player) == targets.end())
                targets.push_back(player);
        }
        if (test && targets.empty())
            if (Player* gm = me->SelectNearestPlayer(100.f))
                targets.push_back(gm);
        float const pct = kPeltingPct(_heroic);
        uint32 circles = 0;
        for (Player* target : targets)
        {
            Position const spot = target->GetPosition();
            MechanicRef ref = Mechanic::Circle(me, spot, kPeltingRadius, Ms(kPeltingFlightMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_OM_PELTING).Weakened()
                .Tag(TAG_OM_PELTING);
            if (!ref.IsValid())
                continue;
            ++circles;
            if (Creature* fan = RandomFan())
            {
                float const d = fan->GetExactDist(&spot);
                _throws.push_back({ fan->GetGUID(), spot, _clockMs + BottleLaunchDelayMs(d),
                    SPELL_OM_BOTTLE_FIRST + urand(0, kBottleCount - 1) });
            }
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pelting",
            Acore::StringFormat("heroic={} circles={} picked={} weakened={} pct={:.0f}", _heroic ? 1 : 0, circles,
                picked, targets.size() - picked, pct));
        return circles;
    }

    // The bottles leave their fans so they land with the circles.
    void UpdateThrows()
    {
        for (auto it = _throws.begin(); it != _throws.end();)
        {
            if (_clockMs < it->at)
            {
                ++it;
                continue;
            }
            if (Creature* fan = ObjectAccessor::GetCreature(*me, it->fan))
                fan->CastSpell(it->spot.GetPositionX(), it->spot.GetPositionY(), it->spot.GetPositionZ(), it->spell,
                    true);
            it = _throws.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM6 Mojo (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    uint32 StartMojo(bool test)
    {
        if (_stage == Stage::Trip)
        {
            _nextMojoMs = _landAt + 1000;
            return 0;
        }
        std::span<MysticPost const> const posts = _stage == Stage::Hall
            ? std::span<MysticPost const>(kHallMysticPosts) : std::span<MysticPost const>(kBridgeMysticPosts);
        uint8 const count = test ? std::max<uint8>(1, kMojoTargets.At(_players)) : kMojoTargets.At(_players);
        uint32 const first = urand(0, uint32(posts.size()) - 1);
        uint32 sent = 0;
        for (uint8 i = 0; i < count; ++i)
        {
            MysticPost const& post = posts[(first + i) % posts.size()];
            TempSummon* mystic = me->SummonCreature(NPC_BRS_MOJO_MYSTIC, Grounded(me, post.crowd),
                TEMPSUMMON_MANUAL_DESPAWN);
            if (!mystic)
                continue;
            StartMystic(mystic, Grounded(me, post.stepOut), Grounded(me, post.crowd));
            ++sent;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mojo",
            Acore::StringFormat("mystics={} stage={}", sent, _stage == Stage::Hall ? "hall" : "bridge"));
        return sent;
    }

    // Defined after the Mystic's AI.
    void StartMystic(Creature* mystic, Position const& stepOut, Position const& crowd);

    void MojoChanting(Creature* mystic)
    {
        Talk(EMOTE_OM_MOJO);
        Mechanic::NoteNextCastIn(mystic, SPELL_OM_OGRE_MOJO, Ms(kMojoEveryMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mojo-chant", Where(mystic->GetPosition()));
    }

    void MojoLanded(Unit* caster)
    {
        me->CastSpell(me, SPELL_OM_MOJO_FRENZY, true);
        me->CastSpell(me, SPELL_OM_MOJO_FRENZY_LOOK, true);
        _frenzyLookMs = 0;
        uint8 const roar = _crowd.Grant(kMojoRoarStacks);
        SyncRoar();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mojo-frenzy",
            Acore::StringFormat("by={} roar={}", caster ? caster->GetName() : "test", roar));
    }

    void MojoFailed(char const* why)
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "mojo-ends", why);
    }

    // Mojo Madness's look is a one-shot burst: re-cast while the frenzy lasts.
    void UpdateFrenzyLook(uint32 diff)
    {
        if (!me->HasAura(SPELL_OM_MOJO_FRENZY))
            return;
        _frenzyLookMs += diff;
        if (_frenzyLookMs < kMojoFrenzyLookEveryMs)
            return;
        _frenzyLookMs = 0;
        me->CastSpell(me, SPELL_OM_MOJO_FRENZY_LOOK, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM7 To the bridge (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void StartShowdown()
    {
        _showdownQueued = false;
        me->InterruptNonMeleeSpells(false);
        CancelPunches();
        _haymakerWindow.reset();
        _throws.clear();
        ClearBand();
        _stage = Stage::Trip;
        uint64 const tripMs = kShowdownJumpMs + kShowdownSettleMs;
        _landAt = _clockMs + tripMs;
        _nextSlamMs = _clockMs + kShowdownJumpMs + kBellySlamAfterLandMs;
        _nextRushMs = _clockMs + kShowdownJumpMs + kBullRushAfterLandMs;
        Talk(SAY_OM_TO_THE_BRIDGE);
        MoveCrowdToDoors();
        StepAsideBridgeOgres();
        uint32 const jumped = JumpEveryoneToBridge();
        Position const landing = Grounded(me, kOmokkShowdownLanding, float(M_PI) * 1.5f);
        DungeonKit::JumpTo(me, landing, TripSpeedXY(Distance3d(me->GetPosition(), landing), kShowdownJumpMs),
            kShowdownMinSpeedZ);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "to-the-bridge",
            Acore::StringFormat("health={:.1f}% jumped={} landings={} ogres={}", me->GetHealthPct(), jumped,
                LandingCount(_players), _steppedAside.size()));
    }

    uint32 JumpEveryoneToBridge()
    {
        std::vector<Player*> jumpers;
        Unit* victim = me->GetVictim();
        if (Player* tank = victim ? victim->ToPlayer() : nullptr)
            if (CountsAsPlayer(tank))
                jumpers.push_back(tank);
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && player->IsInMap(me)
                && std::find(jumpers.begin(), jumpers.end(), player) == jumpers.end())
                jumpers.push_back(player);
        }
        uint8 const count = LandingCount(_players);
        for (std::size_t i = 0; i < jumpers.size(); ++i)
        {
            Landing const l = LandingFor(i, count);
            Point3 const spot = kOmokkLandings[l.spot];
            // The deck is z 31.8 to 32.5 (the cross platform): each landing is dropped onto it.
            Position const dest = Grounded(me, { spot.x, spot.y + l.yOffset, spot.z }, float(M_PI) * 1.5f);
            JumpOne(jumpers[i], dest);
            float petOffset = 1.5f;
            for (Unit* pet : jumpers[i]->m_Controlled)
                if (pet && pet->IsInWorld() && pet->IsAlive())
                {
                    JumpOne(pet, Position(dest.GetPositionX() + petOffset, dest.GetPositionY(), dest.GetPositionZ()));
                    petOffset = -petOffset;
                }
        }
        return uint32(jumpers.size());
    }

    void JumpOne(Unit* unit, Position const& dest)
    {
        DungeonKit::JumpTo(unit, dest, TripSpeedXY(Distance3d(unit->GetPosition(), dest), kShowdownJumpMs),
            kShowdownMinSpeedZ);
    }

    void Land()
    {
        _stage = Stage::Bridge;
        RaiseBand(kBridgeBand, Ms(0), "bridge");
        DungeonKit::FallWatchSpec spec;
        spec.deckZ = kOmokkBridgeDeckZ;
        spec.below = kPitDropBelowYd;
        spec.region = PitRegion();
        spec.grace = Ms(kPitDropGraceMs);
        spec.pets = true;
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        spec.onCatch = [map, bossGuid, gen](Unit* caught)
        {
            if (boss_highlord_omokk_rework* ai = AIOf(map, bossGuid, gen))
                ai->PitCatch(caught);
        };
        _fall.Arm(std::move(spec));
        if (Unit* victim = me->GetVictim())
            me->GetMotionMaster()->MoveChase(victim);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "landed", Where(me->GetPosition()));
    }

    // The bridge's Spirestone ogres, alive and not fighting, step aside into the door crowds.
    void StepAsideBridgeOgres()
    {
        auto& store = me->GetMap()->GetCreatureBySpawnIdStore();
        for (StepAside const& s : kBridgeOgres)
        {
            auto const range = store.equal_range(s.spawnId);
            for (auto it = range.first; it != range.second; ++it)
            {
                Creature* ogre = it->second;
                if (!ogre || !ogre->IsAlive() || ogre->IsInCombat())
                    continue;
                Aside aside{ ogre->GetGUID(), ogre->HasUnitFlag(UNIT_FLAG_NON_ATTACKABLE),
                    ogre->HasUnitFlag(UNIT_FLAG_IMMUNE_TO_PC), ogre->GetReactState() };
                ogre->SetReactState(REACT_PASSIVE);
                ogre->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
                ogre->SetImmuneToPC(true);
                ogre->GetMotionMaster()->MovePoint(0, Grounded(me, s.to), FORCED_MOVEMENT_RUN);
                _steppedAside.push_back(aside);
            }
        }
    }

    // OM11: back to their posts (the flags and reaction they had before), walking home in evade state: an evading
    // creature starts no fight (Creature::CanCreatureAttack), so the ogres pass the players at the doors without
    // pulling, and SmartAI's JustReachedHome resumes the patrol rare's path (R-1-A m2).
    void RestoreBridgeOgres()
    {
        for (Aside const& a : _steppedAside)
        {
            Creature* ogre = ObjectAccessor::GetCreature(*me, a.guid);
            if (!ogre || !ogre->IsAlive())
                continue;
            if (!a.hadNonAttackable)
                ogre->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
            if (!a.hadImmuneToPc)
                ogre->SetImmuneToPC(false);
            ogre->SetReactState(a.react);
            if (ogre->IsAIEnabled && ogre->AI() && !ogre->IsInEvadeMode())
                ogre->AI()->EnterEvadeMode(CreatureAI::EVADE_REASON_OTHER);
            else
                ogre->GetMotionMaster()->MoveTargetedHome();
        }
        _steppedAside.clear();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM8 Belly Slam, OM9 Bull Rush
    // ----------------------------------------------------------------------------------------------------------------

    void StartBellySlam()
    {
        DungeonKit::CastBar(me, SPELL_OM_BELLY_SLAM_CAST);
        MechanicRef ref = Mechanic::Circle(me, me, kBellySlamRadius, Ms(kBellySlamCastMs));
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        ref.Damage(kBellySlamPct).TankDamage(kBellySlamPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_OM_BELLY_SLAM)
            .Weakened().Tag(TAG_OM_BELLY_SLAM)
            .OnHit([map, bossGuid, gen](Unit* hit)
            {
                if (boss_highlord_omokk_rework* ai = AIOf(map, bossGuid, gen))
                    ai->Slammed(hit);
            })
            .OnResolve([map, bossGuid, gen](BossMechanics::ResolveResult const& result)
            {
                if (boss_highlord_omokk_rework* ai = AIOf(map, bossGuid, gen))
                    ai->SlamLanded(result.hits.size());
            });
        _slamWindow = Window{ _clockMs, _clockMs + kBellySlamCastMs };
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "belly-slam",
            Acore::StringFormat("ok={} at={}", ref.IsValid() ? 1 : 0, Where(me->GetPosition())));
    }

    void SlamLanded(std::size_t hits)
    {
        me->CastSpell(me, SPELL_OM_BELLY_SLAM_LOOK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "belly-slam-lands", Acore::StringFormat("hits={}", hits));
    }

    void Slammed(Unit* hit)
    {
        if (!hit || !hit->IsAlive())
            return;
        Throw(hit, DungeonKit::PlaneOf(me), kBellySlamKnockYd, kBellySlamSpeedZ);
    }

    // No lane is down during a Belly Slam cast (the open one, the next one).
    uint64 RushStart(uint64 due) const
    {
        std::vector<Window> windows;
        if (_slamWindow)
            windows.push_back({ _slamWindow->from, _slamWindow->to + kBullRushWarnMs });
        windows.push_back({ _nextSlamMs, _nextSlamMs + kBellySlamCastMs + kBullRushWarnMs });
        return FirstClearStart(due, kBullRushWarnMs, windows);
    }

    uint32 StartBullRush(bool test)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = test;
        std::vector<Player*> const targets = DungeonKit::PickPlayers(me, rule, kBullRushTargets.At(_players));
        bool const west = _rushWest;
        _rushWest = !_rushWest;
        if (targets.empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bull-rush-skipped", "no non-tank");
            return 0;
        }
        Vec2 const door = west ? kWestDoor : kEastDoor;
        Point3 const pen = west ? kWestBrawler : kEastBrawler;
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        uint32 const gen = _generation;
        uint32 lanes = 0;
        float side = 0.f;
        for (Player* target : targets)
        {
            Vec2 const end = BullRushEnd(door, DungeonKit::PlaneOf(target));
            Position const from = At(door, kOmokkBridgeDeckZ);
            Position const to = At(end, kOmokkBridgeDeckZ);
            ObjectGuid brawlerGuid;
            Point3 const spot{ pen.x + side, pen.y, pen.z };
            side = side > 0.f ? -side : side - 1.5f;
            float const facing = std::atan2(end.y - pen.y, end.x - pen.x);
            if (TempSummon* brawler = me->SummonCreature(NPC_BRS_BRAWLER, Grounded(me, spot, facing),
                TEMPSUMMON_TIMED_DESPAWN, kBrawlerLifeMs))
            {
                brawler->CastSpell(brawler, SPELL_OM_BULL_RUSH_CAST, false);
                brawler->HandleEmoteCommand(EMOTE_ONESHOT_ROAR);
                brawlerGuid = brawler->GetGUID();
            }
            MechanicRef ref = Mechanic::Line(me, from, to, kBullRushWidth, Ms(kBullRushWarnMs));
            ref.Damage(kBullRushPct).TankDamage(kBullRushPct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_OM_BULL_RUSH)
                .Weakened().Tag(TAG_OM_BULL_RUSH)
                .OnHit([map, bossGuid, gen](Unit* hit)
                {
                    if (boss_highlord_omokk_rework* ai = AIOf(map, bossGuid, gen))
                        ai->Rushed(hit);
                })
                .OnResolve([map, brawlerGuid, to](BossMechanics::ResolveResult const& /*result*/)
                {
                    Creature* brawler = map ? map->GetCreature(brawlerGuid) : nullptr;
                    if (brawler && brawler->IsAlive())
                        brawler->GetMotionMaster()->MoveCharge(to.GetPositionX(), to.GetPositionY(),
                            to.GetPositionZ(), kBullRushChargeSpeed);
                });
            if (ref.IsValid())
                ++lanes;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bull-rush",
            Acore::StringFormat("door={} lanes={} first={}", west ? "west" : "east", lanes,
                targets.front()->GetName()));
        return lanes;
    }

    // OM9: thrown sideways past the near edge of the deck.
    void Rushed(Unit* hit)
    {
        if (!hit || !hit->IsAlive())
            return;
        Vec2 const at = DungeonKit::PlaneOf(hit);
        SideThrow const t = SideThrowAt(at);
        Throw(hit, { at.x - t.sign, at.y }, t.distance, kBullRushSpeedZ);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "bull-rush-hit",
            Acore::StringFormat("target={} side={} yd={:.1f}", hit->GetName(), t.sign > 0.f ? "north" : "south",
                t.distance));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM10 Pit Drop
    // ----------------------------------------------------------------------------------------------------------------

    // The crowd catches a falling unit: a player takes Pit Drop and feeds the crowd; both are jumped to the nearer
    // door's haul-up spot. The watch reset the player's fall first (no fall damage on the haul-up's landing).
    void PitCatch(Unit* caught)
    {
        if (!caught || !caught->IsAlive())
            return;
        Player* player = caught->ToPlayer();
        if (player)
            me->CastSpell(player, SPELL_OM_PIT_DROP, true);
        Point3 const spot = HaulUpFor(caught->GetPositionY());
        Position const dest = Grounded(me, spot, caught->GetPositionY() > kBridgeMiddle.y ? float(M_PI) * 1.5f
            : float(M_PI) / 2.f);
        if (caught->IsAlive())
            DungeonKit::JumpTo(caught, dest, TripSpeedXY(Distance3d(caught->GetPosition(), dest), kHaulUpMs),
                kHaulUpMinSpeedZ);
        if (player)
            Feed(player, "pit-drop");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pit-drop",
            Acore::StringFormat("unit={} z={:.1f} slowed={} to={}", caught->GetName(), caught->GetPositionZ(),
                caught->HasAuraType(SPELL_AURA_FEATHER_FALL) || caught->HasAuraType(SPELL_AURA_HOVER) ? 1 : 0,
                Where(dest)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data: kill order (heroic) the Mojo Mystic, then Omokk; interrupt Ogre Mojo (heroic, expected); no dispels
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_OMOKK, kOmokkKillPriority, Who::Any);
        d.ignores.emplace_back(NPC_BRS_BRAWL_FAN);
        d.ignores.emplace_back(NPC_BRS_BRAWLER);
        if (_heroic)
        {
            d.targets.emplace_back(NPC_BRS_MOJO_MYSTIC, kMojoKillPriority, Who::Dps);
            d.interrupts.emplace_back(NPC_BRS_MOJO_MYSTIC, SPELL_OM_OGRE_MOJO, kMojoKickPriority, Ms(kMojoEveryMs));
        }
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest brs omokk` entry points (`heroic` forces the heroic form until the next pull)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Haymaker,
        Pelting,
        Judge,
        Mojo,
        Showdown,
        BellySlam,
        BullRush,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (!me->IsEngaged())
            return "Omokk must be in combat (the crowd, the band and the timers run only in the fight).";
        if (_heroic != heroic)
        {
            _heroic = heroic;
            Describe();
        }
        bool const bridge = _stage == Stage::Bridge;
        switch (mechanic)
        {
            case TestMechanic::Haymaker:
                if (bridge)
                    return "Haymaker is a hall mechanic (he is on the bridge).";
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "Omokk is casting; try again in a moment.";
                return StartHaymaker(true) ? std::string() : "No target for Haymaker.";
            case TestMechanic::Pelting:
                if (bridge)
                    return "Pelting stops on the bridge.";
                return StartPelting(true) ? std::string() : "No target for Pelting.";
            case TestMechanic::Judge:
                Judge();
                return {};
            case TestMechanic::Mojo:
                return StartMojo(true) ? std::string() : "No Mojo Mystic was summoned.";
            case TestMechanic::Showdown:
                if (_stage != Stage::Hall)
                    return "The showdown already ran this pull.";
                _showdownQueued = true;
                return {};
            case TestMechanic::BellySlam:
                if (!bridge)
                    return "Belly Slam runs on the bridge (`.dbtest brs omokk showdown 1` first).";
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "Omokk is casting; try again in a moment.";
                StartBellySlam();
                return {};
            case TestMechanic::BullRush:
                if (!bridge)
                    return "Bull Rush runs on the bridge (`.dbtest brs omokk showdown 1` first).";
                return StartBullRush(true) ? std::string() : "No target for Bull Rush.";
        }
        return "Unknown mechanic.";
    }

    std::string TestShove(Player* gm)
    {
        if (!me->IsEngaged())
            return "Omokk must be in combat.";
        PileShove(gm);
        return {};
    }

    std::string TestPitDrop(Player* gm)
    {
        if (!me->IsEngaged())
            return "Omokk must be in combat.";
        gm->SetFallInformation(0, gm->GetPositionZ());
        PitCatch(gm);
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        char const* stage = _stage == Stage::Hall ? "hall" : (_stage == Stage::Trip ? "trip" : "bridge");
        return Acore::StringFormat("clock={}s heroic={} players={} stage={} roar={} booed={} fed={} haymaker@{}s "
            "pelting@{}s judge@{}s mojo@{}s slam@{}s rush@{}s next-door={} band={} punches={} throws={} fans={} "
            "aside={} fall={}", _clockMs / 1000, _heroic ? 1 : 0, _players, stage, _crowd.Roar(), _crowd.Booed(),
            _crowd.FeedsThisWindow(), _nextHaymakerMs / 1000, _nextPeltingMs / 1000, _nextJudgeMs / 1000,
            _nextMojoMs / 1000, _nextSlamMs / 1000, _nextRushMs / 1000, _rushWest ? "west" : "east", _band.size(),
            _punches.size(), _throws.size(), _fans.size(), _steppedAside.size(), _fall.Armed() ? 1 : 0);
    }

private:
    struct Aside
    {
        ObjectGuid guid;
        bool hadNonAttackable = false;
        bool hadImmuneToPc = false;
        ReactStates react = REACT_AGGRESSIVE;
    };

    // The live AI of this boss on `map`, if it is still the same pull (`gen`). Captures are the map and guids only.
    static boss_highlord_omokk_rework* AIOf(Map* map, ObjectGuid bossGuid, uint32 gen)
    {
        Creature* boss = map ? map->GetCreature(bossGuid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        auto* ai = dynamic_cast<boss_highlord_omokk_rework*>(boss->AI());
        return ai && ai->_generation == gen ? ai : nullptr;
    }

public:
    // The living Omokk that summoned `summon` (any pull) when he runs this AI, for the Mystic.
    static Creature* SummonerOmokk(Creature const* summon)
    {
        TempSummon const* temp = summon ? summon->ToTempSummon() : nullptr;
        Unit* summoner = temp ? temp->GetSummonerUnit() : nullptr;
        Creature* boss = summoner ? summoner->ToCreature() : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled
            || !dynamic_cast<boss_highlord_omokk_rework*>(boss->AI()))
            return nullptr;
        return boss;
    }

    static boss_highlord_omokk_rework* AIOfSummoner(Creature const* summon)
    {
        Creature* boss = SummonerOmokk(summon);
        return boss ? dynamic_cast<boss_highlord_omokk_rework*>(boss->AI()) : nullptr;
    }

private:
    // The fight ends with someone still falling into the pit (his death, an evade): the crowd hauls them up anyway, no
    // Pit Drop, so the end of the watch never drops a player into the Firebrand camp.
    void RescueFalling()
    {
        DungeonKit::Arena const pit = PitRegion();
        std::vector<Unit*> falling;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!CountsAsPlayer(player))
                continue;
            falling.push_back(player);
            for (Unit* pet : player->m_Controlled)
                if (pet && pet->IsInWorld() && pet->IsAlive())
                    falling.push_back(pet);
        }
        uint32 rescued = 0;
        for (Unit* unit : falling)
        {
            float const z = unit->GetPositionZ();
            if (!pit.Contains(DungeonKit::PlaneOf(unit), z) || z < kOmokkPitFloorZ + 2.f)
                continue;   // on the deck, or already down in the camp (not falling any more)
            if (Player* player = unit->ToPlayer())
                player->SetFallInformation(0, z);
            Position const dest = Grounded(me, HaulUpFor(unit->GetPositionY()));
            DungeonKit::JumpTo(unit, dest, TripSpeedXY(Distance3d(unit->GetPosition(), dest), kHaulUpMs),
                kHaulUpMinSpeedZ);
            ++rescued;
        }
        if (rescued)
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pit-rescue", Acore::StringFormat("units={}", rescued));
    }

    // The pull's state: no crowd, band, lines, throws, watch or auras (Reset, evade, death, a new pull).
    void Cleanup()
    {
        _stageAtDeath = _stage;
        ++_generation;      // callbacks of an older pull stop
        if (_fall.Armed())
            RescueFalling();
        ClearBand();
        CancelPunches();
        _throws.clear();
        _fall.Disarm();
        RestoreBridgeOgres();
        summons.DespawnEntry(NPC_BRS_BRAWL_FAN);
        summons.DespawnEntry(NPC_BRS_BRAWLER);
        summons.DespawnEntry(NPC_BRS_MOJO_MYSTIC);
        _fans.clear();
        me->RemoveAurasDueToSpell(SPELL_OM_CROWDS_ROAR);
        me->RemoveAurasDueToSpell(SPELL_OM_BOOED);
        me->RemoveAurasDueToSpell(SPELL_OM_MOJO_FRENZY);
        _crowd.Reset();
        _shovedUntil.clear();
        _haymakerWindow.reset();
        _slamWindow.reset();
        _stage = Stage::Hall;
        _showdownQueued = false;
        _clockMs = 0;
        _landAt = 0;
        _nextHaymakerMs = kHaymakerFirstMs;
        _nextPeltingMs = kPeltingFirstMs;
        _nextJudgeMs = kJudgeEveryMs;
        _nextMojoMs = 0;
        _nextSlamMs = 0;
        _nextRushMs = 0;
        _pileCheckMs = 0;
        _frenzyLookMs = 0;
        _rushWest = true;
        _secondCastDone = false;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::FallWatch _fall;
    CrowdBook _crowd;
    uint64 _clockMs = 0;                        // ms since the pull: every timer of the fight
    uint64 _landAt = 0;
    uint64 _nextHaymakerMs = kHaymakerFirstMs;
    uint64 _nextPeltingMs = kPeltingFirstMs;
    uint64 _nextJudgeMs = kJudgeEveryMs;
    uint64 _nextMojoMs = 0;
    uint64 _nextSlamMs = 0;
    uint64 _nextRushMs = 0;
    uint32 _pileCheckMs = 0;
    uint32 _frenzyLookMs = 0;
    uint32 _generation = 0;
    uint32 _volley = 0;
    uint8 _players = 0;                         // the flex count held at the pull (5..10)
    bool _heroic = false;
    bool _showdownQueued = false;
    bool _rushWest = true;
    bool _secondCastDone = false;
    Stage _stage = Stage::Hall;
    Stage _stageAtDeath = Stage::Hall;
    std::optional<Window> _haymakerWindow;
    std::optional<Window> _slamWindow;
    std::vector<MechanicHandle> _band;
    std::vector<Punch> _punches;
    std::vector<BottleThrow> _throws;
    GuidVector _fans;
    std::vector<Aside> _steppedAside;
    std::unordered_map<ObjectGuid, uint64> _shovedUntil;
};

// The Spirestone Brawl Fan (300700): the crowd. Not selectable, not attackable; the boss moves it, makes it cheer,
// jeer and throw (bottles, the rock).
struct npc_brs_brawl_fan : public NullCreatureAI
{
    explicit npc_brs_brawl_fan(Creature* creature) : NullCreatureAI(creature) { }
};

// The Spirestone Brawler (300701): Bull Rush's charger (heroic showdown). The boss gives it its bar and its charge.
struct npc_brs_brawler : public NullCreatureAI
{
    explicit npc_brs_brawler(Creature* creature) : NullCreatureAI(creature) { }
};

// The Spirestone Mojo Mystic (300702, heroic): steps out of the crowd, chants Ogre Mojo at Omokk once (3 s, kickable),
// then walks back into the crowd and is gone. Never fights back.
struct npc_brs_mojo_mystic : public ScriptedAI
{
    enum class Phase : uint8
    {
        Idle,
        Walking,
        Chanting,
        Leaving,
    };

    explicit npc_brs_mojo_mystic(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void JustDied(Unit* /*killer*/) override
    {
        me->DespawnOrUnsummon(Milliseconds(5000));
    }

    void Begin(Position const& stepOut, Position const& crowd)
    {
        _crowd = crowd;
        _phase = Phase::Walking;
        _ageMs = 0;
        me->GetMotionMaster()->MovePoint(POINT_MYSTIC_STEP_OUT, stepOut, FORCED_MOVEMENT_RUN);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE)
            return;
        if (id == POINT_MYSTIC_STEP_OUT && _phase == Phase::Walking)
            Chant();
        else if (id == POINT_MYSTIC_BACK)
            me->DespawnOrUnsummon();
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_OM_OGRE_MOJO && _phase == Phase::Chanting)
            Leave("interrupted");
    }

    void SpellHitTarget(Unit* /*target*/, SpellInfo const* spell) override
    {
        if (spell->Id == SPELL_OM_OGRE_MOJO && _phase == Phase::Chanting)
            Leave("landed");
    }

    void UpdateAI(uint32 diff) override
    {
        _ageMs += diff;
        if (_phase == Phase::Walking && _ageMs >= kMojoGiveUpMs)
            Leave("gave-up");
        else if (_phase == Phase::Chanting && !me->HasUnitState(UNIT_STATE_CASTING)
            && _ageMs >= _chantAt + kMojoCastMs + 1000)
            Leave("lost");
    }

private:
    void Chant()
    {
        Creature* omokk = boss_highlord_omokk_rework::SummonerOmokk(me);
        boss_highlord_omokk_rework* boss = boss_highlord_omokk_rework::AIOfSummoner(me);
        if (!omokk || !boss)
        {
            Leave("no-omokk");
            return;
        }
        me->SetFacingToObject(omokk);
        if (me->CastSpell(omokk, SPELL_OM_OGRE_MOJO, false) != SPELL_CAST_OK)
        {
            Leave("refused");
            return;
        }
        _phase = Phase::Chanting;
        _chantAt = _ageMs;
        boss->MojoChanting(me);
    }

    void Leave(char const* why)
    {
        if (_phase == Phase::Leaving)
            return;
        _phase = Phase::Leaving;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            me->InterruptNonMeleeSpells(false);
        if (boss_highlord_omokk_rework* boss = boss_highlord_omokk_rework::AIOfSummoner(me))
            boss->MojoFailed(why);
        if (me->IsAlive())
            me->GetMotionMaster()->MovePoint(POINT_MYSTIC_BACK, _crowd, FORCED_MOVEMENT_NONE);
    }

    Position _crowd;
    Phase _phase = Phase::Idle;
    uint32 _ageMs = 0;
    uint32 _chantAt = 0;
};

void boss_highlord_omokk_rework::StartMystic(Creature* mystic, Position const& stepOut, Position const& crowd)
{
    if (auto* ai = dynamic_cast<npc_brs_mojo_mystic*>(mystic->AI()))
        ai->Begin(stepOut, crowd);
    else
        mystic->DespawnOrUnsummon();
}

// OM10 Pit Drop 210042: 70% of the target's reference row, half under Slow Fall or Levitate (feather fall or hover).
class spell_brs_omokk_pit_drop : public SpellScript
{
    PrepareSpellScript(spell_brs_omokk_pit_drop);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;
        bool const slowed = target->HasAuraType(SPELL_AURA_FEATHER_FALL) || target->HasAuraType(SPELL_AURA_HOVER);
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, target, PitDropPct(slowed))));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_brs_omokk_pit_drop::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_highlord_omokk_rework* FindOmokkAI(ChatHandler* handler)
    {
        Creature* boss = BrsTest::FindBoss(handler, NPC_OMOKK);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_highlord_omokk_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}",
                "Highlord Omokk is not running boss_highlord_omokk_rework (check the ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_highlord_omokk_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_highlord_omokk_rework* ai = FindOmokkAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        std::string const error = ai->TestFire(mechanic, isHeroic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Highlord Omokk: {} fired ({}).", what, isHeroic ? "heroic" : "normal");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_OMOKK, BOSS_OMOKK);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_highlord_omokk_rework* ai = FindOmokkAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Highlord Omokk: {}", ai->TestState());
        return true;
    }

    bool HandleHaymaker(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_highlord_omokk_rework::TestMechanic::Haymaker, heroic,
            "Haymaker (OM2; heroic: the one-two)");
    }

    bool HandlePelting(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_highlord_omokk_rework::TestMechanic::Pelting, heroic, "Pelting (OM3)");
    }

    bool HandleJudge(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_highlord_omokk_rework::TestMechanic::Judge, heroic, "the crowd's judge (OM5)");
    }

    bool HandleMojo(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_highlord_omokk_rework::TestMechanic::Mojo, heroic, "Mojo (OM6)");
    }

    bool HandleShowdown(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_highlord_omokk_rework::TestMechanic::Showdown, heroic,
            "To the bridge (OM7, on his next tick)");
    }

    bool HandleBellySlam(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_highlord_omokk_rework::TestMechanic::BellySlam, heroic, "Belly Slam (OM8)");
    }

    bool HandleBullRush(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_highlord_omokk_rework::TestMechanic::BullRush, heroic, "Bull Rush (OM9)");
    }

    // `.dbtest brs omokk shove`: the GM takes a Crowd Shove (the pile's script hit).
    bool HandleShove(ChatHandler* handler)
    {
        boss_highlord_omokk_rework* ai = FindOmokkAI(handler);
        Player* gm = handler->GetPlayer();
        if (!ai || !gm)
            return false;
        std::string const error = ai->TestShove(gm);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Highlord Omokk: Crowd Shove on you (OM1).");
        return true;
    }

    // `.dbtest brs omokk pitdrop`: the GM is caught as if falling (Pit Drop, the haul-up to the nearer door).
    bool HandlePitDrop(ChatHandler* handler)
    {
        boss_highlord_omokk_rework* ai = FindOmokkAI(handler);
        Player* gm = handler->GetPlayer();
        if (!ai || !gm)
            return false;
        std::string const error = ai->TestPitDrop(gm);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Highlord Omokk: Pit Drop on you (OM10), hauled up to the nearer door.");
        return true;
    }

    // `.dbtest brs omokk <sub> [1]`: the optional 1 forces the heroic form (0 forces normal); default: the map's.
    ChatCommandTable const& OmokkTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "haymaker",  HandleHaymaker,  SEC_GAMEMASTER, Console::No },
            { "pelting",   HandlePelting,   SEC_GAMEMASTER, Console::No },
            { "judge",     HandleJudge,     SEC_GAMEMASTER, Console::No },
            { "mojo",      HandleMojo,      SEC_GAMEMASTER, Console::No },
            { "showdown",  HandleShowdown,  SEC_GAMEMASTER, Console::No },
            { "bellyslam", HandleBellySlam, SEC_GAMEMASTER, Console::No },
            { "bullrush",  HandleBullRush,  SEC_GAMEMASTER, Console::No },
            { "shove",     HandleShove,     SEC_GAMEMASTER, Console::No },
            { "pitdrop",   HandlePitDrop,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_highlord_omokk_rework()
{
    RegisterDungeonReworkCreatureAI(boss_highlord_omokk_rework, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_brawl_fan, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_brawler, BlackrockSpireRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brs_mojo_mystic, BlackrockSpireRework::kInstanceScriptName);
    RegisterSpellScript(spell_brs_omokk_pit_drop);
    BrsTest::RegisterBoss("omokk", OmokkTestCommands());
}
