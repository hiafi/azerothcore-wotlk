/*
 * mod-dungeon-bosses, Scarlet Monastery D10: Drillmaster Corin Halden, the Master-at-Arms (300942), "The Drill". Build
 * spec: docs/dungeons/scarlet-monastery-3-armory.md "Drillmaster Corin Halden, the Master-at-Arms" (MA0-MA4, Build
 * spec), handoff section 3.5 row D10, 3.6, 3.8, 3.9 (the `close-ranks` row), 7 #30 A. A new boss (no stock script to
 * replace). Pure rules: HaldenLogic.h. Wave 2: the AI registers only once kWave2Bound flips (W2-SETUP);
 * `.dbtest sm halden` registers now.
 *
 * He fights with a squad of Drill Recruits (300943: not selectable, cannot be harmed) drawn up in a rank 8 yd behind
 * him, 8 yd apart (heroic seven, 7 yd apart). Section 7 #30 A: the rank stands only north or south of him (along the
 * middle chamber's 40 yd axis): it turns to keep the tank in front of him, and where a wall cuts it the outer recruits
 * close in. He himself only melees the tank; the squad is his kit.
 *
 *   MA0 The Drill       at 8 s, then every 10 s, he yells a command and the rank readies 2.5 s (the marker), in the
 *                       fixed order Charge, Spears, Javelins, Close Ranks. Heroic: a pair every 12 s ("Charge, then
 *                       spears!"), the second 2 s after the first lands; after a Javelins and Close Ranks pair the next
 *                       waits until 2 s after the ring (a 31 s drill)
 *   MA1 Charge!         a 4 yd lane ahead of each recruit, from the rank to 35 yd ahead, clipped at the room's far wall
 *                       (8 to 10 yd past him): 30% (45%) Physical and Weakened; the recruits charge down it
 *   MA2 Spears, level!  a 60 degree cone 10 yd ahead of each recruit (a band from the rank to 2 yd past him): 30% (45%)
 *                       Physical and Weakened
 *   MA3 Javelins!       his 2 s interruptible cast, then each recruit throws at a different player: a 5 yd circle at
 *                       the player's spot, 2.5 s flight, 30% (45%) and Weakened. Kicked on normal: the recruits fumble,
 *                       no volley. Heroic: two more at random players, each within 5 yd of its player; kicked, one
 *                       volley; missed, a second volley (MA3a) 1.5 s after the first lands, at the players' new spots
 *   MA4 Close Ranks!    the squad wheels round him for 6 s (heroic 8 s): a band 5 to 11 yd round him (section 7 #30 A),
 *                       10% (12%) Physical a second, lingering; melee hug him, ranged stay out
 *
 * A wipe resets him and the squad to rank and the drill to its first command; the encounter completes on his death and
 * the recruits go with him. Every percent hit is a percent of the reference row (his spells ignore caster modifiers),
 * landed by the registry. Boss data: kill order Halden (the recruits are ignored: not selectable); interrupt list:
 * Javelins (normal a reward, heroic expected); no dispels, no purges. Every firing logs one INFO line "sm halden
 * <mechanic> ..." (module.dungeonbosses); `.dbtest sm halden ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "HaldenLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmHalden;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "halden";

    // The squad re-checks its rank twice a second (out of combat too: he walks home after a wipe).
    constexpr uint32 kReformTickMs = 500;
    // A recruit farther than this from its spot runs to it.
    constexpr float kReformSlackYd = 1.0f;
    // The cast has not taken yet this long after the call (UpdateJavelins waits before calling it done).
    constexpr uint32 kCastStartGraceMs = 250;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    Vec2 PlaneOf(WorldObject const* o)
    {
        return { o->GetPositionX(), o->GetPositionY() };
    }

    float Rand01()
    {
        return frand(0.f, 0.9999f);
    }

    // The three rooms and their necks: every spot the bots plan for a lane, a cone, a javelin or the ring stays on
    // their floor (rule 12).
    BossMechanics::SpotBounds HallBounds()
    {
        BossMechanics::SpotBounds bounds;
        for (Room const& r : kWalkable)
            bounds.Rect(r.xMin, r.yMin, r.xMax, r.yMax, kZMin, kZMax);
        return bounds;
    }
}

// Drillmaster Corin Halden 300942
struct boss_drillmaster_corin_halden_rework : public BossAI
{
    explicit boss_drillmaster_corin_halden_rework(Creature* creature)
        : BossAI(creature, BOSS_HALDEN), _arena(RoomsArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
        me->SetVirtualItem(0, kItemHaldenMainHand);
        me->SetVirtualItem(1, kItemHaldenOffHand);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _heroic = IsHeroicMap(me);
        if (!_squadBuilt)
            BuildSquad();       // pulled in the tick he was created
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_HALDEN;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_PULL);

        _fightMs = 0;
        _nextCall = 0;
        _drillOn = true;
        if (Unit* victim = me->GetVictim())
            _facing = ChooseFacing(PlaneOf(me), PlaneOf(victim), _facing);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} recruits={} facing={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0,
                LiveRecruits(), FacingName(_facing), me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        Talk(SAY_DEATH);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("commands={} charges={} spears={} javelins={} kicked={} volleys={} second-volleys={} "
                "rings={} fight={}s killer={}", _nextCall, _charges, _spears, _javelinCasts, _javelinKicks, _volleys,
                _secondVolleys, _rings, _fightMs / 1000, killer ? killer->GetName() : "none"));
        Cleanup();
    }

    // A 5 s cooldown (Herod's stock row 7 shape): a wipe says "Dismissed." once, not five times.
    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer() || _clockMs < _killLineReadyMs)
            return;
        _killLineReadyMs = _clockMs + kKillLineCooldownMs;
        Talk(SAY_KILL);
    }

    // The recruits are his: they go with his reset and death and never join a fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // MA3: a kick or a silence stopped Javelins. His own stops (an evade, his death, a reset) are not interrupts:
    // Cleanup drops the cast's state before the engine interrupts it.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_MA_JAVELINS && _javelinCast.active)
            JavelinsEnded(true, "interrupted");
    }

    // MA3: the cast went off.
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && spell->Id == SPELL_MA_JAVELINS && _javelinCast.active)
            JavelinsEnded(false, "landed");
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!_squadBuilt)
            BuildSquad();
        UpdateSquad();
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        _fightMs += diff;
        UpdateDrill();
        UpdateCharge();
        UpdateSpears();
        UpdateJavelins();
        UpdateRing();
        UpdateLooks();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The squad
    // ----------------------------------------------------------------------------------------------------------------

    // Five recruits (heroic seven) in rank behind him: built when he stands in his hall, and again after every reset.
    void BuildSquad()
    {
        if (_squadBuilt || !me->IsInWorld() || !me->IsAlive())
            return;
        _squadBuilt = true;
        _recruitCount = kRecruits(IsHeroicMap(me));
        if (!me->IsEngaged())
            _facing = SnapFacing(me->GetOrientation());
        std::vector<Vec2> const rank = Rank();
        uint32 made = 0;
        for (uint32 i = 0; i < _recruitCount && i < rank.size(); ++i)
        {
            Position const at(rank[i].x, rank[i].y, me->GetPositionZ(), FacingAngle(_facing));
            TempSummon* recruit = me->SummonCreature(NPC_SM_DRILL_RECRUIT, at, TEMPSUMMON_MANUAL_DESPAWN);
            if (!recruit)
                continue;
            recruit->SetReactState(REACT_PASSIVE);
            recruit->SetWalk(false);
            recruit->SetVirtualItem(0, kItemRecruitSpear);
            recruit->SetVirtualItem(1, 0);
            _recruits[i] = recruit->GetGUID();
            ++made;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "squad",
            Acore::StringFormat("recruits={} of {} facing={}", made, _recruitCount, FacingName(_facing)));
    }

    Creature* Recruit(uint32 i) const
    {
        if (i >= _recruitCount || !_recruits[i])
            return nullptr;
        Creature* recruit = ObjectAccessor::GetCreature(*me, _recruits[i]);
        return recruit && recruit->IsAlive() ? recruit : nullptr;
    }

    uint32 LiveRecruits() const
    {
        uint32 n = 0;
        for (uint32 i = 0; i < _recruitCount; ++i)
            n += Recruit(i) ? 1 : 0;
        return n;
    }

    // The rank behind him now (section 7 #30 A: north or south of him, along the long axis).
    std::vector<Vec2> Rank() const
    {
        return RankSpots(PlaneOf(me), _facing, _recruitCount, kRankSpacingYd(IsHeroicMap(me)));
    }

    // Twice a second: unless a command holds them (a charge, the ring), the recruits jog back into rank behind him (to
    // the command's frozen spots while it readies) and face his way. In combat the rank turns with the tank between
    // commands; out of combat it follows his own facing.
    void UpdateSquad()
    {
        if (!_squadBuilt || _clockMs < _nextReformMs)
            return;
        _nextReformMs = _clockMs + kReformTickMs;
        if (_drillOn && _fightMs < _squadBusyUntilMs)
            return;
        bool const frozen = _drillOn && _fightMs < _rankFrozenUntilMs && !_frozenRank.empty();
        if (!frozen)
        {
            Facing const before = _facing;
            if (!me->IsEngaged())
                _facing = SnapFacing(me->GetOrientation());
            else if (Unit* victim = me->GetVictim())
                _facing = ChooseFacing(PlaneOf(me), PlaneOf(victim), _facing);
            if (_facing != before && me->IsEngaged())
                DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "facing",
                    Acore::StringFormat("facing={} at=({:.1f}, {:.1f})", FacingName(_facing), me->GetPositionX(),
                        me->GetPositionY()));
        }
        std::vector<Vec2> const spots = frozen ? _frozenRank : Rank();
        float const z = me->GetPositionZ();
        for (uint32 i = 0; i < _recruitCount && i < spots.size(); ++i)
        {
            Creature* recruit = Recruit(i);
            if (!recruit)
                continue;
            if (recruit->GetExactDist2d(spots[i].x, spots[i].y) > kReformSlackYd)
            {
                recruit->GetMotionMaster()->MovePoint(1, spots[i].x, spots[i].y, z);
                continue;
            }
            if (!recruit->isMoving() && std::fabs(recruit->GetOrientation() - FacingAngle(_facing)) > 0.2f)
                recruit->SetFacingTo(FacingAngle(_facing));
        }
    }

    // The rank's spots for a command: computed at the yell and held until it lands; the recruits run to them.
    std::vector<Vec2> FreezeRank(uint64 untilMs)
    {
        _frozenRank = Rank();
        _rankFrozenUntilMs = untilMs;
        float const z = me->GetPositionZ();
        for (uint32 i = 0; i < _recruitCount && i < _frozenRank.size(); ++i)
            if (Creature* recruit = Recruit(i))
                recruit->GetMotionMaster()->MovePoint(1, _frozenRank[i].x, _frozenRank[i].y, z);
        return _frozenRank;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA0 The Drill
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateDrill()
    {
        if (!_drillOn)
            return;
        DrillCall const call = CallAt(_nextCall, _heroic);
        if (_fightMs < call.yellMs)
            return;
        ++_nextCall;
        FireCommand(call);
    }

    // The facing (unless the ring still holds the squad), the yell (heroic: the pair's yell on its first command, the
    // command's own on the second), the command.
    void FireCommand(DrillCall const& call)
    {
        if (_fightMs >= _squadBusyUntilMs)
            if (Unit* victim = me->GetVictim())
                _facing = ChooseFacing(PlaneOf(me), PlaneOf(victim), _facing);
        Talk(call.pairFirst ? PairText(call.command) : CommandText(call.command));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "command",
            Acore::StringFormat("n={} command={} pair={} facing={} at={}ms", _nextCall, CommandName(call.command),
                call.pairFirst ? "first" : call.pairSecond ? "second" : "none", FacingName(_facing), _fightMs));
        Start(call.command);
    }

    void Start(Command command)
    {
        switch (command)
        {
            case Command::Charge:       StartCharge(); break;
            case Command::Spears:       StartSpears(); break;
            case Command::Javelins:     StartJavelins(); break;
            case Command::CloseRanks:   StartCloseRanks(); break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA1 Charge!
    // ----------------------------------------------------------------------------------------------------------------

    // One lane per recruit, 4 yd wide, from its rank spot straight ahead to the room's far wall (35 yd at most), a
    // 2.5 s marker: 30% (45%) Physical and Weakened to anyone in a lane, the tank included (the middle lane runs
    // through him and the tank).
    void StartCharge()
    {
        std::vector<Vec2> const rank = FreezeRank(_fightMs + kReadyMs);
        Room const room = RoomAt(PlaneOf(me));
        float const z = me->GetPositionZ();
        float const pct = kHitPct(_heroic);
        _laneEnds.clear();
        float shortest = kChargeLengthYd;
        for (Vec2 const& spot : rank)
        {
            Lane const lane = ChargeLane(spot, _facing, room);
            Position const from(lane.from.x, lane.from.y, z, FacingAngle(_facing));
            Position const to(lane.to.x, lane.to.y, z, FacingAngle(_facing));
            MechanicRef ref = Mechanic::Line(me, from, to, kChargeWidthYd, Ms(kReadyMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_MA_CHARGE).Weakened()
                .Within(HallBounds()).Tag(TAG_MA_CHARGE);
            if (ref.IsValid())
                Track(ref.Handle());
            _laneEnds.push_back(lane.to);
            shortest = std::min(shortest, DungeonKit::Distance(lane.from, lane.to));
        }
        _chargeLand.Start(_fightMs, kReadyMs);
        ++_charges;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "charge",
            Acore::StringFormat("lanes={} facing={} rank-x={:.1f} shortest={:.1f} pct={:.0f}", rank.size(),
                FacingName(_facing), rank.empty() ? 0.f : rank.front().x, shortest, pct));
    }

    // The lanes land: the recruits charge down them (Charge's look), stand a moment and jog back.
    void UpdateCharge()
    {
        if (!_chargeLand.Due(_fightMs))
            return;
        _chargeLand.Stop();
        _squadBusyUntilMs = _fightMs + kChargeBackMs;
        float const z = me->GetPositionZ();
        for (uint32 i = 0; i < _recruitCount && i < _laneEnds.size(); ++i)
        {
            Creature* recruit = Recruit(i);
            if (!recruit)
                continue;
            recruit->CastSpell(recruit, SPELL_MA_CHARGE_LOOK, true);
            recruit->GetMotionMaster()->MoveCharge(_laneEnds[i].x, _laneEnds[i].y, z, kChargeRunSpeed);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA2 Spears, level!
    // ----------------------------------------------------------------------------------------------------------------

    // A 60 degree cone ahead of each recruit, to 2 yd past him (10 yd from the full 8 yd rank; shorter when a wall
    // behind him pulls the rank in: SpearsLengthYd), a band over his back and flanks, a 2.5 s marker: 30% (45%)
    // Physical and Weakened. Melee step to his front corners.
    void StartSpears()
    {
        std::vector<Vec2> const rank = FreezeRank(_fightMs + kReadyMs);
        float const z = me->GetPositionZ();
        float const pct = kHitPct(_heroic);
        float const length = rank.empty() ? kSpearsLengthYd
            : SpearsLengthYd(rank.front().x, me->GetPositionX(), _facing);
        for (Vec2 const& spot : rank)
        {
            Position const apex(spot.x, spot.y, z, FacingAngle(_facing));
            MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(apex, kSpearsAngleDeg, length),
                Ms(kReadyMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_MA_SPEARS).Weakened()
                .Within(HallBounds()).Tag(TAG_MA_SPEARS);
            if (ref.IsValid())
                Track(ref.Handle());
        }
        _spearsLand.Start(_fightMs, kReadyMs);
        ++_spears;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spears",
            Acore::StringFormat("cones={} facing={} rank-x={:.1f} length={:.1f} pct={:.0f}", rank.size(),
                FacingName(_facing), rank.empty() ? 0.f : rank.front().x, length, pct));
    }

    // The cones land: every recruit thrusts.
    void UpdateSpears()
    {
        if (!_spearsLand.Due(_fightMs))
            return;
        _spearsLand.Stop();
        for (uint32 i = 0; i < _recruitCount; ++i)
            if (Creature* recruit = Recruit(i))
                recruit->CastSpell(recruit, SPELL_MA_SPEARS_LOOK, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA3 Javelins! (MA3a the heroic second volley)
    // ----------------------------------------------------------------------------------------------------------------

    // His 2 s cast (interruptible: a kick or a silence). Failing to start (silenced) counts as a kick.
    bool StartJavelins()
    {
        ++_javelinCasts;
        me->StopMoving();
        Mechanic::NoteNextCastIn(me, SPELL_MA_JAVELINS, Ms(DrillLengthMs(_heroic)));
        _javelinCast = JavelinCast();
        _javelinCast.active = true;
        _javelinCast.startedMs = _fightMs;
        SpellCastResult const result = me->CastSpell(me, SPELL_MA_JAVELINS, false);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "javelins",
            Acore::StringFormat("cast={}ms result={}", kJavelinCastMs, static_cast<uint32>(result)));
        if (result != SPELL_CAST_OK)
        {
            if (_javelinCast.active)
                JavelinsEnded(true, "not-started");
            return false;
        }
        return true;
    }

    // The cast ended without a hook (it went off, or he lost it): a cast that ran its time threw. Then the throws.
    void UpdateJavelins()
    {
        if (_javelinCast.active && !me->FindCurrentSpellBySpellId(SPELL_MA_JAVELINS)
            && _fightMs >= _javelinCast.startedMs + kCastStartGraceMs)
            JavelinsEnded(_fightMs < _javelinCast.startedMs + kJavelinCastMs, "no-hook");
        if (_throw.Due(_fightMs))
        {
            _throw.Stop();
            Volley(false, _throwSecond);
        }
        if (_secondVolley.Due(_fightMs))
        {
            _secondVolley.Stop();
            Volley(true, false);
        }
    }

    // Normal: kicked, the recruits fumble and nothing comes; else one volley. Heroic: kicked, one volley at the cast's
    // planned end (the rhythm holds); missed, the volley and the second one 1.5 s after it lands.
    void JavelinsEnded(bool kicked, char const* how)
    {
        uint64 const startedMs = _javelinCast.startedMs;
        _javelinCast = JavelinCast();
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        if (kicked)
            ++_javelinKicks;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, kicked ? "javelins-kicked" : "javelins-thrown",
            Acore::StringFormat("how={} heroic={} kicked={}", how, _heroic ? 1 : 0, _javelinKicks));
        if (kicked && !_heroic)
        {
            Talk(EMOTE_FUMBLE);
            return;
        }
        uint64 const throwAt = startedMs + kJavelinCastMs;
        _throwSecond = _heroic && !kicked;
        _throw.Start(_fightMs, throwAt > _fightMs ? static_cast<uint32>(throwAt - _fightMs) : 0u);
    }

    // A volley: each recruit at a player (normal a different one each; heroic two more at random players, every one
    // within 5 yd of its player), a 5 yd circle fixed at the throw, 2.5 s flight (the second volley 1.5 s): 30% (45%)
    // Physical and Weakened, the tank included. Two players together take two.
    uint32 Volley(bool second, bool thenSecond)
    {
        std::vector<Player*> players = FightPlayers();
        Acore::Containers::RandomShuffle(players);
        std::vector<uint32> const picks = JavelinPicks(static_cast<uint32>(players.size()), _recruitCount, _heroic,
            Rand01);
        uint32 const warn = second ? kSecondVolleyWarnMs : kJavelinFlightMs;
        float const pct = kHitPct(_heroic);
        for (uint32 r = 0; r < picks.size(); ++r)
        {
            Player* target = players[picks[r]];
            Vec2 const spot = JavelinSpot(PlaneOf(target), _heroic, Rand01);
            Position const at(spot.x, spot.y, target->GetPositionZ(), 0.f);
            MechanicRef ref = Mechanic::Circle(me, at, kJavelinRadiusYd, Ms(warn));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_MA_JAVELIN).Weakened()
                .Within(HallBounds()).Tag(second ? TAG_MA_SECOND_VOLLEY : TAG_MA_JAVELIN);
            if (ref.IsValid())
                Track(ref.Handle());
            if (Creature* recruit = Recruit(r))
                _looks.push_back({ _fightMs + LookDelayMs(recruit->GetExactDist2d(spot.x, spot.y), warn),
                    recruit->GetGUID(), at });
        }
        if (second)
            ++_secondVolleys;
        else
            ++_volleys;
        if (thenSecond && !picks.empty())
            _secondVolley.Start(_fightMs, warn);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, second ? "second-volley" : "volley",
            Acore::StringFormat("javelins={} players={} warn={}ms pct={:.0f} second-next={}", picks.size(),
                players.size(), warn, pct, thenSecond ? 1 : 0));
        return static_cast<uint32>(picks.size());
    }

    // The javelins' flights: each leaves its recruit so that it lands with its hit.
    void UpdateLooks()
    {
        for (auto it = _looks.begin(); it != _looks.end();)
        {
            if (_fightMs < it->dueMs)
            {
                ++it;
                continue;
            }
            if (Creature* recruit = ObjectAccessor::GetCreature(*me, it->recruit))
                if (recruit->IsAlive())
                    recruit->CastSpell(it->at.GetPositionX(), it->at.GetPositionY(), it->at.GetPositionZ(),
                        SPELL_MA_JAVELIN_LOOK, true);
            it = _looks.erase(it);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA4 Close Ranks!
    // ----------------------------------------------------------------------------------------------------------------

    // The rank breaks into a ring (2.5 s) and wheels round him for 6 s (heroic 8 s): a band 5 to 11 yd round him
    // (section 7 #30 A), a tick a second of 10% (12%) Physical, lingering (no Weakened). It moves with him.
    void StartCloseRanks()
    {
        uint32 const ringMs = kRingMs(_heroic);
        float const pct = kRingPct(_heroic);
        MechanicRef ref = Mechanic::Donut(me, me, kRingInnerYd, kRingOuterYd, Ms(kReadyMs));
        ref.Persistent(Ms(ringMs), Ms(kRingTickMs)).Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL)
            .Spell(SPELL_MA_CLOSE_RANKS).Within(HallBounds()).Tag(TAG_MA_CLOSE_RANKS);
        if (ref.IsValid())
            Track(ref.Handle());
        _squadBusyUntilMs = _fightMs + kReadyMs + ringMs;
        _ringTurned = 0.f;
        MoveRing();
        _ringStep.Start(_fightMs, kReadyMs);
        _ringLook.Start(_fightMs, kReadyMs);
        _ringEnd.Start(_fightMs, kReadyMs + ringMs);
        ++_rings;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "close-ranks",
            Acore::StringFormat("band={:.0f}-{:.0f} ring={}ms pct={:.0f}", kRingInnerYd, kRingOuterYd, ringMs, pct));
    }

    void MoveRing()
    {
        float const z = me->GetPositionZ();
        for (uint32 i = 0; i < _recruitCount; ++i)
            if (Creature* recruit = Recruit(i))
            {
                Vec2 const s = RingSpot(PlaneOf(me), _facing, i, _recruitCount, _ringTurned);
                recruit->GetMotionMaster()->MovePoint(2, s.x, s.y, z);
            }
    }

    void UpdateRing()
    {
        if (_ringEnd.Due(_fightMs))
        {
            _ringEnd.Stop();
            _ringStep.Stop();
            _ringLook.Stop();
            return;     // the squad is free: UpdateSquad takes it back into rank
        }
        if (_ringStep.Due(_fightMs))
        {
            _ringStep.Start(_fightMs, kRingStepMs);
            _ringTurned += RingStepRad(_heroic);
            MoveRing();
        }
        if (_ringLook.Due(_fightMs))
        {
            _ringLook.Start(_fightMs, kRingLookEveryMs);
            for (uint32 i = 0; i < _recruitCount; ++i)
                if (Creature* recruit = Recruit(i))
                {
                    recruit->CastSpell(recruit, SPELL_MA_CLOSE_RANKS_LOOK, true);
                    if (_heroic)        // heroic: they face out and thrust as they pass
                        recruit->CastSpell(recruit, SPELL_MA_SPEARS_LOOK, true);
                }
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ARM "Boss data")
    // ----------------------------------------------------------------------------------------------------------------

    // Kill order: Halden (the recruits are not selectable: ignored). Interrupt list: Javelins (normal a reward,
    // heroic expected), once a drill. Dispel list: none. Purge list: none.
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.ignores.emplace_back(NPC_SM_DRILL_RECRUIT);
        d.interrupts.emplace_back(NPC_SM_HALDEN, SPELL_MA_JAVELINS, _heroic ? 3 : 2, Ms(DrillLengthMs(_heroic)));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm halden` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Next,
        Charge,
        Spears,
        Javelins,
        CloseRanks,
        Volley,
        SecondVolley,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic)
    {
        if (!me->IsEngaged())
            return "Halden must be in combat (the picks read his threat list, the mechanics his encounter).";
        switch (mechanic)
        {
            case TestMechanic::Next:
                if (!_drillOn)
                    return "The drill is not running.";
                _fightMs = std::max<uint64>(_fightMs, CallAt(_nextCall, _heroic).yellMs);
                UpdateDrill();
                break;
            case TestMechanic::Charge:
                StartCharge();
                break;
            case TestMechanic::Spears:
                StartSpears();
                break;
            case TestMechanic::Javelins:
                if (_javelinCast.active || me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting already.";
                StartJavelins();
                break;
            case TestMechanic::CloseRanks:
                StartCloseRanks();
                break;
            case TestMechanic::Volley:
                if (!Volley(false, false))
                    return "No player to throw at.";
                break;
            case TestMechanic::SecondVolley:
                if (!Volley(true, false))
                    return "No player to throw at.";
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        DrillCall const next = CallAt(_nextCall, _heroic);
        return Acore::StringFormat("fight={}s heroic={} drill={} next={} ({} at {}s) facing={} recruits={}/{} "
            "busy-until={}s charges={} spears={} javelins={} kicked={} volleys={} second={} rings={} live-handles={}",
            _fightMs / 1000, _heroic ? 1 : 0, _drillOn ? 1 : 0, _nextCall, CommandName(next.command),
            next.yellMs / 1000, FacingName(_facing), LiveRecruits(), _recruitCount, _squadBusyUntilMs / 1000, _charges,
            _spears, _javelinCasts, _javelinKicks, _volleys, _secondVolleys, _rings, _live.size());
    }

private:
    struct JavelinCast
    {
        bool active = false;
        uint64 startedMs = 0;
    };

    struct PendingLook
    {
        uint64 dueMs = 0;
        ObjectGuid recruit;
        Position at;
    };

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            out.push_back(player);
        }
        return out;
    }

    // A mechanic of the fight: kept to cancel it on a reset.
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // The pull's state: nothing registered, no recruit, no clock (Reset, evade, death, a new pull). The squad is
    // rebuilt in rank on the next tick he stands alive in his hall.
    void Cleanup()
    {
        _javelinCast = JavelinCast();       // before the engine interrupts a cast, so it never reads as a kick
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        summons.DespawnAll();
        _recruits.fill(ObjectGuid::Empty);
        _squadBuilt = false;
        _recruitCount = 0;
        _drillOn = false;
        _fightMs = 0;
        _nextCall = 0;
        _squadBusyUntilMs = 0;
        _rankFrozenUntilMs = 0;
        _frozenRank.clear();
        _laneEnds.clear();
        _looks.clear();
        _chargeLand.Stop();
        _spearsLand.Stop();
        _throw.Stop();
        _secondVolley.Stop();
        _ringStep.Stop();
        _ringLook.Stop();
        _ringEnd.Stop();
        _throwSecond = false;
        _ringTurned = 0.f;
        _charges = 0;
        _spears = 0;
        _javelinCasts = 0;
        _javelinKicks = 0;
        _volleys = 0;
        _secondVolleys = 0;
        _rings = 0;
        _facing = Facing::North;
        _arena.Reset();
    }

    DungeonKit::ArenaGuard _arena;
    std::array<ObjectGuid, kMaxRecruits> _recruits{};
    std::vector<Vec2> _frozenRank;
    std::vector<Vec2> _laneEnds;
    std::vector<PendingLook> _looks;
    std::vector<MechanicHandle> _live;
    Timer _chargeLand;
    Timer _spearsLand;
    Timer _throw;
    Timer _secondVolley;
    Timer _ringStep;
    Timer _ringLook;
    Timer _ringEnd;
    JavelinCast _javelinCast;
    uint64 _clockMs = 0;            // ms since the AI started: the squad's reform tick
    uint64 _killLineReadyMs = 0;    // the clock is never reset, so neither is this
    uint64 _fightMs = 0;            // ms since the pull: the drill and every command
    uint64 _nextReformMs = 0;
    uint64 _squadBusyUntilMs = 0;   // a charge or the ring holds the squad until then
    uint64 _rankFrozenUntilMs = 0;  // a readying command holds the rank's spots until then
    uint32 _recruitCount = 0;
    uint32 _nextCall = 0;
    uint32 _charges = 0;
    uint32 _spears = 0;
    uint32 _javelinCasts = 0;
    uint32 _javelinKicks = 0;
    uint32 _volleys = 0;
    uint32 _secondVolleys = 0;
    uint32 _rings = 0;
    float _ringTurned = 0.f;
    Facing _facing = Facing::North;
    bool _squadBuilt = false;
    bool _drillOn = false;
    bool _throwSecond = false;
    bool _heroic = false;
};

namespace
{
    using Mech = boss_drillmaster_corin_halden_rework::TestMechanic;

    boss_drillmaster_corin_halden_rework* FindHaldenAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_SM_HALDEN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_drillmaster_corin_halden_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Halden is not running boss_drillmaster_corin_halden_rework (check the "
                "ScriptName and the wave switch).");
        return ai;
    }

    bool Fire(ChatHandler* handler, Mech mechanic, char const* what)
    {
        boss_drillmaster_corin_halden_rework* ai = FindHaldenAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Halden: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_SM_HALDEN, BOSS_HALDEN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_drillmaster_corin_halden_rework* ai = FindHaldenAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Halden: {}", ai->TestState());
        return true;
    }

    bool HandleNext(ChatHandler* handler)
    {
        return Fire(handler, Mech::Next, "the drill's next command now (MA0; the clock jumps to it)");
    }

    bool HandleCharge(ChatHandler* handler)
    {
        return Fire(handler, Mech::Charge, "Charge! (MA1: the lanes, a 2.5 s marker)");
    }

    bool HandleSpears(ChatHandler* handler)
    {
        return Fire(handler, Mech::Spears, "Spears, level! (MA2: the cones, a 2.5 s marker)");
    }

    bool HandleJavelins(ChatHandler* handler)
    {
        return Fire(handler, Mech::Javelins, "Javelins! (MA3: his 2 s cast, kick it)");
    }

    bool HandleCloseRanks(ChatHandler* handler)
    {
        return Fire(handler, Mech::CloseRanks, "Close ranks! (MA4: the 5-11 yd ring)");
    }

    bool HandleVolley(ChatHandler* handler)
    {
        return Fire(handler, Mech::Volley, "a javelin volley now (MA3, no cast, no second volley)");
    }

    bool HandleSecond(ChatHandler* handler)
    {
        return Fire(handler, Mech::SecondVolley, "a second volley now (MA3a: the 1.5 s javelins)");
    }

    // `.dbtest sm halden <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossDrillmasterCorinHaldenTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "next",       HandleNext,         SEC_GAMEMASTER, Console::No },
            { "charge",     HandleCharge,       SEC_GAMEMASTER, Console::No },
            { "spears",     HandleSpears,       SEC_GAMEMASTER, Console::No },
            { "javelins",   HandleJavelins,     SEC_GAMEMASTER, Console::No },
            { "closeranks", HandleCloseRanks,   SEC_GAMEMASTER, Console::No },
            { "volley",     HandleVolley,       SEC_GAMEMASTER, Console::No },
            { "second",     HandleSecond,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_drillmaster_corin_halden_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_drillmaster_corin_halden_rework,
            ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("halden", BossDrillmasterCorinHaldenTestCommands());
}
