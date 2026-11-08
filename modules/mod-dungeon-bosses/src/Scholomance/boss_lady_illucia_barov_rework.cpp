/*
 * mod-dungeon-bosses, Scholomance S10: Lady Illucia Barov (10502), normal and heroic, her Graduate Examiner mode and
 * the Shadow Vault's solo lesson. Build spec: SC 2695-2741 (build spec), SC 2548-2694 (design: pitch A "Foresight"),
 * IB1-IB5; handoff section 3.4 rows IB, section 3.5 row S10, section 3.6 (normal 160k, heroic 250k, examiner 80k),
 * section 3.7, section 3.8 and section 7 #14 (the fight belongs in the hall). Replaces SmartAI 10502 (WP-S10's SQL rev
 * drops the five rows: Fear 12542 changed, Silence 15487 retired, Shadow Shock 19460 and Curse of Agony 18266 kept
 * here, the death's SetData(1,1) replaced by the boss state). Bound by apps/dbc-tools
 * source/npcs/scholomance/lady_illucia_barov.py.
 *
 *   IB1 Foresight        8 s, then every 20 s: a 1.5 s cast names the read player (yell line 1; the read debuff
 *                        206316); as it ends a 4 yd marker lands on them in 1.5 s, and as each marker lands the next
 *                        appears where they will be 1.5 s later at their heading and speed (on them when they stand),
 *                        sampled every 200 ms (the kit's MotionTrack). 30% / 40% Shadow (206317) and Weakened per
 *                        marker (ruling 20). Normal 1 player x 3 markers, heroic 2 x 5; any player, the tank too. The
 *                        yell names every read player.
 *   IB2 Memory trail     heroic: a read player's path during their chain lingers behind them, 3 yd wide, 4 s, 10%
 *                        Shadow a second (206318), laid in 4 yd pieces once they are 2.5 yd past each (the kit's
 *                        TrailRecorder; DungeonKit::Linger).
 *   IB3 Fear             18 s, then every 20 s: a 1.5 s interruptible cast (206319) on a random non-tank in sight,
 *                        not being read, emote line 2; it lands a 2 s Magic fear whose run is scripted straight away
 *                        from her (spell_scholo_illucia_fear: a point move in the controlled slot that keeps the
 *                        fear's fleeing flag and state, so the player cannot act), and a 4 yd marker lands at the
 *                        run's end as the fear ends: 15% / 50% Shadow (206320), no Weakened, and it never costs the
 *                        feared player the Passing Grade (GradeWatch::Exempt). A kick stops the cast; a dispel stops
 *                        the run short. Bots: the interrupt and dispel lists.
 *   IB4 Shadow Shock     stock 19460 on the tank: 1 to 2 s, then every 10 s.
 *   IB5 Curse of Agony   stock 18266 on a random player within 30 yd and in sight: 1 to 10 s, then every 14 to 24 s
 *                        (the dispel list). A cast that fails (any of the three) tries again 2 s later.
 *   Melee                DamageModifier 3.5 (the stock value, set by the DT file); heroic is the heroic template's.
 *   Arena                IlluciaArena() with LeashOptions (no grips; holds at the edge, evades after 10 s with nobody
 *                        on it). Pulled in her inner room, she first steps out to kIlluciaHallPoint (section 7 #14).
 *
 * Examiner mode (S13, the Graduate Exam): npc_sc_examiner_illucia (IlluciaLogic.h kExaminerScriptName) runs the same
 * fight (IlluciaFight) at heroic values on any map, with 80k health set by the script, no boss state, no Passing
 * Grade and no text. S13 declares the entry (NPC_SC_EXAMINER_ILLUCIA 300554) with that ScriptName and summons it; the
 * script is registered once wave C binds (kWaveCBound), so wave B's boot names no unbound script.
 *
 * Solo lesson (S11's detention, SoloLesson.h): ShadowVaultLesson, registered for Classroom::ShadowVault. The vault
 * reads the student at once and runs one Foresight chain of 3 / 5 markers on them under the lesson stalker; any marker
 * hit fails it (15% / 25% plus Weakened).
 *
 * Every timer runs on the AI's own clock (IlluciaLogic.h Timeline, the chains' own clock), never on BossAI's scheduler
 * that a cast bar pauses. Every firing logs one INFO line "scholo illucia <mechanic> ..." (module.dungeonbosses);
 * `.dbtest scholo illucia <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "IlluciaLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "PointMovementGenerator.h"
#include "Random.h"
#include "ScholomanceKit.h"
#include "ScholomanceRework.h"
#include "ScholomanceTestCommand.h"
#include "ScriptedCreature.h"
#include "SoloLesson.h"
#include "SpellAuraEffects.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScholomanceRework;
using namespace ScholoIllucia;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "illucia";
    char const* const kExaminerLogName = "illucia-examiner";
    char const* const kLessonLogName = "detention-shadow-vault";
    uint32 constexpr kPointHall = 1;                // her step out to the hall
    uint32 constexpr kPointFearRun = 0x49424633;    // a feared player's scripted run ("IBF3")
    uint32 constexpr kTestLessonOwnerEntry = 12999; // stock World Invisible Trigger: the `.dbtest` lesson's owner
    uint32 constexpr kTestLessonOwnerMs = 20000;

    // The point `dist` yd from `from` along `bearing` (absolute), stopped at the first wall and set on the floor; the
    // unit's own spot when the map refuses the move.
    Position ReachablePoint(Unit* from, float bearing, float dist)
    {
        if (dist < 0.1f)
            return from->GetPosition();
        Position at = from->GetFirstCollisionPosition(dist, bearing - from->GetOrientation());
        at.SetOrientation(bearing);
        return at;
    }

    Position ReachablePoint(Unit* from, Vec2 to)
    {
        Vec2 const here = DungeonKit::PlaneOf(from);
        return ReachablePoint(from, DungeonKit::BearingTo(here, to), DungeonKit::Distance(here, to));
    }

    bool IsExaminer(Unit const* unit)
    {
        return unit && unit->GetEntry() == NPC_SC_EXAMINER_ILLUCIA;
    }

    // The auras `caster` put on the map's players (a cleanup sweep that works without an instance script); another
    // owner's (the Shadow Vault lesson's stalker, an examiner) stay.
    void RemoveAurasFromMapPlayers(Unit* caster, std::initializer_list<uint32> spells)
    {
        Map* map = caster ? caster->GetMap() : nullptr;
        if (!map)
            return;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                for (uint32 spell : spells)
                    player->RemoveAurasDueToSpell(spell, caster->GetGUID());
    }
}

// ---- IB1 / IB2: Foresight chains and the Memory trail ---------------------------------------------------------------

// What one chain's markers do.
struct MarkerSpec
{
    float pct = 30.f;               // % of the reference non-tank row, per marker
    bool weakened = true;           // ruling 20: both difficulties
    bool trail = false;             // IB2: the Memory trail behind the read player (heroic)
    uint32 tag = TAG_FORESIGHT;
    char const* logName = kBossLogName;
};

// Every live Foresight chain of one owner (Illucia, an examiner or the lesson stalker), on its own clock: the motion
// samples, the markers, the trail. Stores guids only.
class ForesightChains
{
public:
    // Reads `player`: the read debuff now, the first marker `delayMs` from now on them, then `markers` - 1 more, every
    // 1.5 s, each where they will be 1.5 s later. False when the player is gone or already read.
    bool Start(Creature* owner, Player* player, uint32 delayMs, uint8 markers, MarkerSpec const& spec)
    {
        if (!owner || !player || !player->IsAlive() || !markers || Reading(player->GetGUID()))
            return false;
        _map = owner->GetMap();
        Chain chain;
        chain.player = player->GetGUID();
        chain.schedule.start = _now + delayMs;
        chain.schedule.total = markers;
        chain.spec = spec;
        _chains.push_back(std::move(chain));
        MotionTrack& track = _tracks[player->GetGUID()];
        track.Clear();
        track.Add(_now, DungeonKit::PlaneOf(player));
        owner->CastSpell(player, SPELL_IB_READ, true);     // cast, not added: its look plays as it lands
        DungeonKit::LogMechanic(kLogDungeon, spec.logName, "foresight-read",
            Acore::StringFormat("player={} markers={} pct={:.0f} trail={}", player->GetName(), markers, spec.pct,
                spec.trail ? 1 : 0));
        return true;
    }

    // Every tick, in or out of combat (a `.dbtest` chain runs out of combat).
    void Update(Creature* owner, uint32 diff)
    {
        if (_chains.empty())
            return;
        _now += diff;
        _sampleMs += diff;
        bool const sample = _sampleMs >= kSampleEveryMs;
        if (sample)
            _sampleMs = 0;

        for (auto it = _chains.begin(); it != _chains.end();)
        {
            Player* player = _map ? ObjectAccessor::GetPlayer(_map, it->player) : nullptr;
            if (!owner || !player || !player->IsAlive() || player->GetMap() != _map)
            {
                // Gone, dead or left: no more markers (the placed ones still land).
                Finish(owner, *it, player, false);
                it = _chains.erase(it);
                continue;
            }
            Chain& chain = *it;
            Vec2 const here = DungeonKit::PlaneOf(player);
            if (sample)
            {
                _tracks[chain.player].Add(_now, here);
                if (chain.spec.trail && chain.schedule.placed > 0)
                    LayTrail(owner, chain.trail.Feed(here), player->GetPositionZ(), chain.spec.logName);
            }
            while (chain.schedule.PlaceDue(_now))
                PlaceMarker(owner, player, chain);
            if (chain.schedule.Ended(_now))
            {
                Finish(owner, chain, player, true);
                it = _chains.erase(it);
                continue;
            }
            ++it;
        }
    }

    // The fight is over: every live marker and trail piece cancelled, every read debuff gone. `owner` may be null
    // (then any caster's read on a chain's player goes).
    void Clear(Creature* owner)
    {
        if (owner)
            for (MechanicHandle const& handle : _live)
                Mechanic::Cancel(owner, handle);
        ObjectGuid const caster = owner ? owner->GetGUID() : ObjectGuid::Empty;
        for (Chain const& chain : _chains)
            if (Player* player = _map ? ObjectAccessor::GetPlayer(_map, chain.player) : nullptr)
                player->RemoveAurasDueToSpell(SPELL_IB_READ, caster);
        _live.clear();
        _chains.clear();
        _tracks.clear();
        _now = 0;
        _sampleMs = 0;
    }

    bool Reading(ObjectGuid player) const
    {
        return std::any_of(_chains.begin(), _chains.end(), [player](Chain const& c) { return c.player == player; });
    }

    GuidSet ReadGuids() const
    {
        GuidSet out;
        for (Chain const& chain : _chains)
            out.insert(chain.player);
        return out;
    }

    std::size_t Count() const { return _chains.size(); }

    std::string State() const
    {
        std::string out = Acore::StringFormat("chains={} live={}", _chains.size(), _live.size());
        for (Chain const& chain : _chains)
            out += Acore::StringFormat(" [{} {}/{} trail={}]", chain.player.ToString(), chain.schedule.placed,
                chain.schedule.total, chain.spec.trail ? 1 : 0);
        return out;
    }

private:
    struct Chain
    {
        ObjectGuid player;
        ChainSchedule schedule;
        MarkerSpec spec;
        TrailRecorder trail = MemoryTrailRecorder();
    };

    void PlaceMarker(Creature* owner, Player* player, Chain& chain)
    {
        uint8 const index = chain.schedule.placed;
        Position at = player->GetPosition();
        Prediction prediction;
        if (chain.schedule.NextIsPredicted())
        {
            MotionTrack& track = _tracks[chain.player];
            track.Add(_now, DungeonKit::PlaneOf(player));
            prediction = PredictSpot(track, kForesightMarkerMs);
            if (!prediction.still)
                at = ReachablePoint(player, prediction.at);
        }
        MechanicRef ref = Mechanic::Circle(owner, at, kForesightRadius, Milliseconds(kForesightMarkerMs));
        ref.Damage(chain.spec.pct).Spell(SPELL_IB_FORESIGHT).Tag(chain.spec.tag);
        if (chain.spec.weakened)
            ref.Weakened();
        if (ref.IsValid())
            _live.push_back(ref.Handle());
        ++chain.schedule.placed;
        DungeonKit::LogMechanic(kLogDungeon, chain.spec.logName, "foresight-marker",
            Acore::StringFormat("player={} n={}/{} {} speed={:.1f} at=({:.1f}, {:.1f})", player->GetName(), index + 1,
                chain.schedule.total, chain.schedule.placed == 1 ? "on" : (prediction.still ? "still" : "ahead"),
                prediction.speed, at.GetPositionX(), at.GetPositionY()));
    }

    void LayTrail(Creature* owner, std::vector<TrailSegment> const& pieces, float z, char const* logName)
    {
        for (TrailSegment const& piece : pieces)
        {
            DungeonKit::LingerSpec linger;
            linger.duration = Milliseconds(kTrailLingerMs);
            linger.tick = Milliseconds(kTrailTickMs);
            linger.pct = kTrailPct;
            linger.school = SPELL_SCHOOL_SHADOW;
            linger.spellId = SPELL_IB_MEMORY;
            linger.slow = false;            // SC IB2: 10% a second, no slow
            linger.tag = TAG_MEMORY;
            Position const from = DungeonKit::ToPosition(piece.from, z);
            Position const to = DungeonKit::ToPosition(piece.to, z);
            MechanicRef ref = DungeonKit::Linger(owner, BossMechanics::Shapes::Line(from, to, kTrailWidth), linger);
            if (ref.IsValid())
                _live.push_back(ref.Handle());
        }
        if (!pieces.empty())
            DungeonKit::LogMechanic(kLogDungeon, logName, "memory-trail", Acore::StringFormat("pieces={}",
                pieces.size()));
    }

    // The chain ends (`landed`: its last marker landed) or stops: the trail's last pieces, the read debuff off.
    void Finish(Creature* owner, Chain& chain, Player* player, bool landed)
    {
        if (player)
        {
            if (owner && landed && chain.spec.trail && chain.trail.Started())
                LayTrail(owner, chain.trail.Flush(DungeonKit::PlaneOf(player)), player->GetPositionZ(),
                    chain.spec.logName);
            player->RemoveAurasDueToSpell(SPELL_IB_READ, owner ? owner->GetGUID() : ObjectGuid::Empty);
        }
        DungeonKit::LogMechanic(kLogDungeon, chain.spec.logName, "foresight-end",
            Acore::StringFormat("player={} placed={}/{} reason={}",
                player ? player->GetName() : chain.player.ToString(), chain.schedule.placed, chain.schedule.total,
                landed ? "landed" : "stopped"));
        _tracks.erase(chain.player);
    }

    Map* _map = nullptr;
    std::vector<Chain> _chains;
    std::unordered_map<ObjectGuid, MotionTrack> _tracks;
    std::vector<MechanicHandle> _live;
    uint32 _now = 0;
    uint32 _sampleMs = 0;
};

// ---- The fight, shared by Illucia and her examiner -----------------------------------------------------------------

class IlluciaFight
{
public:
    explicit IlluciaFight(bool examiner) : _examiner(examiner) { }

    void Engage(Creature* me)
    {
        Cleanup(me);
        _heroic = HeroicValues(DungeonKit::IsHeroicMap(me), _examiner);
        _engaged = true;
        _timeline.Start(urand(kShadowShockFirstMinMs, kShadowShockFirstMaxMs),
            urand(kCurseFirstMinMs, kCurseFirstMaxMs));
        Describe(me);
    }

    // Every tick, before UpdateVictim: the chains run out of combat too (a `.dbtest` chain).
    void UpdateChains(Creature* me, uint32 diff)
    {
        _chains.Update(me, diff);
    }

    // After UpdateVictim and the arena: the fight's clock and its beats. A beat that comes due while she casts waits.
    void UpdateBeats(Creature* me, uint32 diff)
    {
        if (!_engaged)
            return;
        _timeline.Advance(diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (_timeline.Due(Beat::Foresight))
            Foresight(me, {}, 0, std::nullopt);
        else if (_timeline.Due(Beat::Fear))
            Fear(me, nullptr);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;

        if (_timeline.Due(Beat::ShadowShock))
            ShadowShock(me);
        if (_timeline.Due(Beat::Curse))
            Curse(me);
    }

    void Cleanup(Creature* me)
    {
        _chains.Clear(me);
        _timeline = Timeline{};
        _engaged = false;
        if (me)
            RemoveAurasFromMapPlayers(me, { uint32(SPELL_IB_READ), uint32(SPELL_IB_FEAR) });
    }

    // IB1: `forced` empty picks the build spec's reads; `markers` 0 and `trail` empty use the difficulty's.
    bool Foresight(Creature* me, std::vector<Player*> forced, uint8 markers, std::optional<bool> trail)
    {
        bool const heroic = _engaged ? _heroic : HeroicValues(DungeonKit::IsHeroicMap(me), _examiner);
        std::vector<Player*> reads = std::move(forced);
        if (reads.empty())
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;           // SC IB1: any player, the tank included
            reads = DungeonKit::PickPlayers(me, rule, kForesightReads(heroic));
        }
        if (reads.empty())
        {
            _timeline.Retry(Beat::Foresight);
            return false;
        }
        _timeline.Done(Beat::Foresight, kForesightEveryMs);

        MarkerSpec spec;
        spec.pct = kForesightPct(heroic);
        spec.trail = trail.value_or(kMemoryTrail(heroic));
        spec.logName = _examiner ? kExaminerLogName : kBossLogName;
        uint8 const count = markers ? markers : kForesightMarkers(heroic);

        DungeonKit::CastBar(me, SPELL_IB_FORESIGHT_CAST);
        std::vector<Player*> started;
        std::string names;
        for (Player* player : reads)
            if (_chains.Start(me, player, kForesightCastMs, count, spec))
            {
                started.push_back(player);
                names += (names.empty() ? "" : ",") + player->GetName();
            }
        YellReads(me, started.empty() ? reads : started);
        DungeonKit::LogMechanic(kLogDungeon, spec.logName, "foresight",
            Acore::StringFormat("reads={} markers={} heroic={}", names, count, heroic ? 1 : 0));
        return true;
    }

    // IB3: `forced` casts on that player, else a random non-tank not being read.
    bool Fear(Creature* me, Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = false;       // SC IB3: never the tank
            rule.maxRange = kFearRange;
            rule.requireLos = true;         // a pillar or the inner room's neck would fail the cast
            DungeonKit::ExcludeGuids(rule, _chains.ReadGuids());
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
        {
            _timeline.Retry(Beat::Fear);
            return false;
        }
        SpellCastResult const result = me->CastSpell(target, SPELL_IB_FEAR, false);
        // A failed cast tries again soon; a silence is the counterplay and costs her the Fear.
        if (result == SPELL_CAST_OK || result == SPELL_FAILED_SILENCED)
            _timeline.Done(Beat::Fear, kFearEveryMs);
        else
            _timeline.Retry(Beat::Fear);
        if (result == SPELL_CAST_OK)
        {
            Mechanic::NoteNextCastIn(me, SPELL_IB_FEAR, Milliseconds(kFearEveryMs));
            Talk(me, EMOTE_ILLUCIA_FEAR, target);
        }
        DungeonKit::LogMechanic(kLogDungeon, _examiner ? kExaminerLogName : kBossLogName, "fear-cast",
            Acore::StringFormat("target={} result={}", target->GetName(), uint32(result)));
        return result == SPELL_CAST_OK;
    }

    bool Engaged() const { return _engaged; }
    bool Heroic() const { return _heroic; }
    bool Examiner() const { return _examiner; }

    std::string State() const
    {
        return Acore::StringFormat("engaged={} heroic={} examiner={} t={}ms next foresight/fear/shock/curse="
            "{}/{}/{}/{}ms {}", _engaged ? 1 : 0, _heroic ? 1 : 0, _examiner ? 1 : 0, _timeline.now,
            _timeline.next[0], _timeline.next[1], _timeline.next[2], _timeline.next[3], _chains.State());
    }

private:
    void ShadowShock(Creature* me)
    {
        Unit* victim = me->GetVictim();
        if (!victim)
        {
            _timeline.Retry(Beat::ShadowShock);
            return;
        }
        if (me->CastSpell(victim, SPELL_SHADOW_SHOCK, false) == SPELL_CAST_OK)
            _timeline.Done(Beat::ShadowShock, kShadowShockEveryMs);
        else
            _timeline.Retry(Beat::ShadowShock);
    }

    void Curse(Creature* me)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = kCurseRange;
        rule.requireLos = true;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            _timeline.Retry(Beat::Curse);
            return;
        }
        if (me->CastSpell(target, SPELL_CURSE_OF_AGONY, false) == SPELL_CAST_OK)
            _timeline.Done(Beat::Curse, urand(kCurseEveryMinMs, kCurseEveryMaxMs));
        else
            _timeline.Retry(Beat::Curse);
    }

    // Boss data (build spec): no target priority; interrupt the Fear; dispel the Fear (Magic, a loss of control) and
    // Curse of Agony (Curse).
    void Describe(Creature* me)
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(me->GetEntry(), SPELL_IB_FEAR, 2, Milliseconds(kFearEveryMs));
        d.dispels.emplace_back(SPELL_IB_FEAR, 3, true);
        d.dispels.emplace_back(SPELL_CURSE_OF_AGONY, 1);
        Mechanic::Describe(me, std::move(d));
    }

    // Her lines; the examiner has none (its entry has no creature_text).
    void Talk(Creature* me, uint8 group, WorldObject const* target)
    {
        if (!_examiner && me->IsAIEnabled && me->AI())
            me->AI()->Talk(group, target);
    }

    // IB1's yell names the read player (line 1, "I know where you will go, $n."); with two reads (heroic) both are
    // named, in the same words (creature_text's $n takes one target).
    void YellReads(Creature* me, std::vector<Player*> const& reads)
    {
        if (_examiner || reads.empty())
            return;
        if (reads.size() == 1)
            Talk(me, YELL_ILLUCIA_FORESIGHT, reads.front());
        else
            me->Yell(Acore::StringFormat("I know where you will go, {} and {}.", reads[0]->GetName(),
                reads[1]->GetName()), LANG_UNIVERSAL);
    }

    ForesightChains _chains;
    Timeline _timeline;
    bool _examiner;
    bool _heroic = false;
    bool _engaged = false;
};

// The step out of her inner room (section 7 #14), shared by both AIs.
class StepOut
{
public:
    void Begin(Creature* me)
    {
        _ms = 0;
        if (!InInnerRoom(DungeonKit::PlaneOf(me)))
            return;
        _active = true;
        Walk(me);
    }

    // True while she is still walking out. The pull's AttackStart (or a new victim) may put her chase back in the
    // movement slot: the walk is issued again until she arrives or gives up.
    bool Update(Creature* me, uint32 diff)
    {
        if (!_active)
            return false;
        _ms += diff;
        if (_ms >= kStepOutTimeoutMs)
            Arrive(me, "timeout");
        else if (me->GetExactDist2d(kIlluciaHallPoint.x, kIlluciaHallPoint.y) < 1.f)
            Arrive(me, "arrived");
        else if (me->GetMotionMaster()->GetCurrentMovementGeneratorType() != POINT_MOTION_TYPE)
            Walk(me);
        return _active;
    }

    void MovementInform(Creature* me, uint32 type, uint32 id)
    {
        if (_active && type == POINT_MOTION_TYPE && id == kPointHall)
            Arrive(me, "arrived");
    }

    void Reset()
    {
        _active = false;
        _ms = 0;
    }

private:
    void Walk(Creature* me)
    {
        Position const hall = DungeonKit::ToPosition({ kIlluciaHallPoint.x, kIlluciaHallPoint.y }, kIlluciaHallPoint.z,
            me->GetOrientation());
        me->GetMotionMaster()->MovePoint(kPointHall, hall);
    }

    void Arrive(Creature* me, char const* why)
    {
        _active = false;
        if (Unit* victim = me->GetVictim())
            me->GetMotionMaster()->MoveChase(victim);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "step-out", Acore::StringFormat("{} after={}ms at=({:.1f}, "
            "{:.1f})", why, _ms, me->GetPositionX(), me->GetPositionY()));
    }

    bool _active = false;
    uint32 _ms = 0;
};

// Lady Illucia Barov 10502
struct boss_lady_illucia_barov_rework : public BossAI
{
    explicit boss_lady_illucia_barov_rework(Creature* creature)
        : BossAI(creature, BOSS_ILLUCIA), _arena(IlluciaArena(), LeashOptions(kBossLogName)), _fight(false) { }

    void Reset() override
    {
        _Reset();
        _fight.Cleanup(me);
        _step.Reset();
        _arena.Reset();
        _grades.Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ILLUCIA;
        Mechanic::BeginEncounter(me, options);
        _grades.Begin(me, Instructor::Illucia);
        _arena.Engage(me);
        _fight.Engage(me);
        Talk(YELL_ILLUCIA_AGGRO);
        _step.Begin(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _fight.Heroic() ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={}", uint32(why)));
        _fight.Cleanup(me);
        _step.Reset();
        _arena.Reset();
        _grades.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        _grades.AwardAtDeath(me);
        _fight.Cleanup(me);
        _step.Reset();
        Talk(YELL_ILLUCIA_DEATH);
        BossAI::JustDied(killer);
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        _step.MovementInform(me, type, id);
    }

    void UpdateAI(uint32 diff) override
    {
        _fight.UpdateChains(me, diff);
        UpdateTestLesson(diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off her arena, or nobody on it for 10 s: evading

        bool const walking = _step.Update(me, diff);
        _fight.UpdateBeats(me, diff);
        if (walking || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- `.dbtest scholo illucia` entry points ----------------------------------------------------------------------

    IlluciaFight& Fight() { return _fight; }
    Creature* Me() const { return me; }

    // IB3: the feared player keeps the Passing Grade through their own end marker (they could not dodge it; F-B
    // ruling 2026-11-08). Everyone else it hits still fails.
    void ExemptFearEnd(MechanicHandle marker, ObjectGuid feared)
    {
        _grades.Exempt(marker, feared);
    }

    // The Shadow Vault lesson on `student`, owned by a temporary trigger the GM summons; this AI ticks it.
    bool TestLesson(Creature* owner, Player* student, bool heroic)
    {
        if (_testLesson)
            _testLesson->Abort();
        _testLesson = CreateSoloLesson(Classroom::ShadowVault);
        if (!_testLesson || !owner || !student)
            return false;
        _testLesson->Start(owner, student, heroic);
        return true;
    }

    std::string TestState() const
    {
        return Acore::StringFormat("{} lesson={}", _fight.State(), !_testLesson ? "none" : _testLesson->Done()
            ? (_testLesson->Passed() ? "passed" : _testLesson->Failed() ? "failed" : "ended") : "running");
    }

private:
    void UpdateTestLesson(uint32 diff)
    {
        if (_testLesson && !_testLesson->Done())
            _testLesson->Update(diff);
    }

    DungeonKit::ArenaGuard _arena;
    GradeWatch _grades;
    IlluciaFight _fight;
    StepOut _step;
    std::unique_ptr<SoloLesson> _testLesson;
};

// The Graduate Examiner, Illucia (S13's gauntlet, heroic hard mode): her fight at heroic values, 80k, no boss state.
struct npc_sc_examiner_illucia : public ScriptedAI
{
    explicit npc_sc_examiner_illucia(Creature* creature)
        : ScriptedAI(creature), _arena(IlluciaArena(), LeashOptions(kExaminerLogName)), _fight(true) { }

    void Reset() override
    {
        _fight.Cleanup(me);
        _step.Reset();
        _arena.Reset();
        ApplyExaminerHealth();
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        Mechanic::BeginEncounter(me);
        _arena.Engage(me);
        _fight.Engage(me);
        _step.Begin(me);
        DungeonKit::LogMechanic(kLogDungeon, kExaminerLogName, "engage",
            Acore::StringFormat("health={} at=({:.1f}, {:.1f}, {:.1f})", me->GetMaxHealth(), me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        _fight.Cleanup(me);
        _step.Reset();
        _arena.Reset();
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        _fight.Cleanup(me);
        _step.Reset();
        _arena.Reset();
        DungeonKit::LogMechanic(kLogDungeon, kExaminerLogName, "death");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        _step.MovementInform(me, type, id);
    }

    void UpdateAI(uint32 diff) override
    {
        _fight.UpdateChains(me, diff);
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;

        bool const walking = _step.Update(me, diff);
        _fight.UpdateBeats(me, diff);
        if (walking || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

private:
    // Create health is the base the engine rebuilds max health from (the Deadmines hard mode's SetBossHealth).
    void ApplyExaminerHealth()
    {
        me->SetCreateHealth(kExaminerHealth);
        me->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(kExaminerHealth));
        me->UpdateMaxHealth();
        me->SetHealth(me->GetMaxHealth());
    }

    DungeonKit::ArenaGuard _arena;
    IlluciaFight _fight;
    StepOut _step;
};

// IB3 Fear 206319: a 2 s Magic fear whose run is scripted: straight away from the caster, at the player's run speed,
// stopped at the first wall (a point move in the controlled slot, in place of the random flee). A 4 yd marker owned by
// the caster's encounter lands at the run's end as the fear ends (15% / 50%; heroic values for the examiner); it never
// costs the feared player the Passing Grade. A dispel ends the run where the player stands.
class spell_scholo_illucia_fear : public AuraScript
{
    PrepareAuraScript(spell_scholo_illucia_fear);

    void AfterApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        Unit* caster = GetCaster();
        if (!target || !caster)
            return;
        float const bearing = FearRunBearing(DungeonKit::PlaneOf(caster), DungeonKit::PlaneOf(target),
            caster->GetOrientation());
        float const run = FearRunYd(target->GetSpeed(MOVE_RUN));
        Position const end = ReachablePoint(target, bearing, run);

        // Feared (not stunned first): the flee generator holds the controlled slot; the straight run replaces it.
        MotionMaster* motion = target->GetMotionMaster();
        bool const running = motion->GetMotionSlotType(MOTION_SLOT_CONTROLLED) == FLEEING_MOTION_TYPE;
        if (running)
        {
            motion->MovePoint(kPointFearRun, end.GetPositionX(), end.GetPositionY(), end.GetPositionZ(),
                FORCED_MOVEMENT_NONE, 0.f, bearing, true, true, MOTION_SLOT_CONTROLLED);
            // The flee generator's finalize lifted the fear's loss of control (the flag blocks casting, the state
            // gates bots and the client): the run keeps both until the fear ends (AfterRemove).
            target->SetUnitFlag(UNIT_FLAG_FLEEING);
            target->AddUnitState(UNIT_STATE_FLEEING);
            _scripted = true;
            _runEnd = end;
        }

        Creature* owner = caster->ToCreature();
        if (!owner || !owner->IsAlive())
            return;
        bool const heroic = HeroicValues(DungeonKit::IsHeroicMap(owner), IsExaminer(owner));
        MechanicRef ref = Mechanic::Circle(owner, end, kFearRadius, Milliseconds(kFearMs));
        ref.Damage(kFearEndPct(heroic)).Spell(SPELL_IB_FEAR_END).Tag(TAG_FEAR_END);
        if (ref.IsValid() && owner->IsAIEnabled)
            if (auto* ai = dynamic_cast<boss_lady_illucia_barov_rework*>(owner->AI()))
                ai->ExemptFearEnd(ref.Handle(), target->GetGUID());
        DungeonKit::LogMechanic(kLogDungeon, IsExaminer(owner) ? kExaminerLogName : kBossLogName, "fear",
            Acore::StringFormat("target={} run={:.1f}yd scripted={} end=({:.1f}, {:.1f}) pct={:.0f}",
                target->GetName(), target->GetExactDist2d(&end), running ? 1 : 0, end.GetPositionX(),
                end.GetPositionY(), kFearEndPct(heroic)));
    }

    // Unit::SetFeared(false) has already given control back (it only stops a flee generator): stop the scripted run
    // (only this aura's own, never a charge or another point move that holds the slot now) and lift the loss of
    // control this script kept, unless another fear holds the player.
    void AfterRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (!target || !_scripted)
            return;
        _scripted = false;
        MotionMaster* motion = target->GetMotionMaster();
        if (target->IsAlive() && OwnRunHoldsSlot(target))
        {
            motion->MovementExpired();
            target->StopMoving();
        }
        if (!target->HasAuraType(SPELL_AURA_MOD_FEAR))
        {
            target->RemoveUnitFlag(UNIT_FLAG_FLEEING);
            target->ClearUnitState(UNIT_STATE_FLEEING);
        }
        else if (target->IsAlive() && !target->HasUnitState(UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED)
            && motion->GetMotionSlotType(MOTION_SLOT_CONTROLLED) == NULL_MOTION_TYPE)
        {
            // Another fear still holds them: its random flee takes over where the run stopped.
            Unit* source = ObjectAccessor::GetUnit(*target,
                target->GetAuraEffectsByType(SPELL_AURA_MOD_FEAR).front()->GetCasterGUID());
            motion->MoveFleeing(source ? source : target->getAttackerForHelper(), 0);
        }
        if (GetTargetApplication() && GetTargetApplication()->GetRemoveMode() == AURA_REMOVE_BY_ENEMY_SPELL)
            DungeonKit::LogMechanic(kLogDungeon, GetCasterGUID().GetEntry() == NPC_SC_EXAMINER_ILLUCIA
                ? kExaminerLogName : kBossLogName, "fear-dispelled", Acore::StringFormat("target={}",
                target->GetName()));
    }

    // The controlled slot still holds this aura's point move (its destination is the run's end).
    bool OwnRunHoldsSlot(Unit* target) const
    {
        MotionMaster* motion = target->GetMotionMaster();
        if (!target->IsPlayer() || motion->GetMotionSlotType(MOTION_SLOT_CONTROLLED) != POINT_MOTION_TYPE)
            return false;
        auto const* point = dynamic_cast<PointMovementGenerator<Player> const*>(
            motion->GetMotionSlot(MOTION_SLOT_CONTROLLED));
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
        return point && point->GetDestination(x, y, z) && std::fabs(x - _runEnd.GetPositionX()) < 0.1f
            && std::fabs(y - _runEnd.GetPositionY()) < 0.1f;
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_scholo_illucia_fear::AfterApply, EFFECT_0, SPELL_AURA_MOD_FEAR,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_scholo_illucia_fear::AfterRemove, EFFECT_0, SPELL_AURA_MOD_FEAR,
            AURA_EFFECT_HANDLE_REAL);
    }

    bool _scripted = false;
    Position _runEnd;
};

// ---- The Shadow Vault's solo lesson (S11's detention; handoff section 3.7, SC 2960-2971) ----------------------------

// The vault reads the lone student: one Foresight chain of 3 / 5 markers under the lesson stalker; any marker hit
// fails the lesson (15% / 25% plus Weakened). No Memory trail, no Fear (the lesson table names only the chain).
class ShadowVaultLesson : public TimedSoloLesson
{
public:
    ShadowVaultLesson() : TimedSoloLesson(Classroom::ShadowVault) { }

protected:
    void OnStart(Creature* owner, Player* student, bool heroic) override
    {
        MarkerSpec spec;
        spec.pct = LessonMarkerPct(heroic);
        spec.weakened = true;
        spec.trail = false;
        spec.logName = kLessonLogName;
        _chains.Start(owner, student, kLessonReadAtMs, kLessonMarkers(heroic), spec);
    }

    void OnUpdate(uint32 diff, Creature* owner, Player* /*student*/) override
    {
        _chains.Update(owner, diff);
    }

    void OnEnd(LessonEnd /*why*/, Creature* owner) override
    {
        _chains.Clear(owner);
    }

private:
    ForesightChains _chains;
};

namespace
{
    boss_lady_illucia_barov_rework* FindIlluciaAI(ChatHandler* handler)
    {
        Creature* boss = ScholoTest::FindBoss(handler, NPC_ILLUCIA);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_lady_illucia_barov_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Illucia is not running boss_lady_illucia_barov_rework (check the "
                "ScriptName).");
        return ai;
    }

    Creature* IlluciaOf(boss_lady_illucia_barov_rework* ai)
    {
        return ai ? ai->Me() : nullptr;
    }

    // The selected player, else the GM.
    Player* TestTarget(ChatHandler* handler)
    {
        if (Player* selected = handler->getSelectedPlayer())
            return selected;
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ScholoTest::ShowBossInfo(handler, NPC_ILLUCIA, BOSS_ILLUCIA);
    }

    // `.dbtest scholo illucia state`: the clock, the beats and the live chains.
    bool HandleState(ChatHandler* handler)
    {
        boss_lady_illucia_barov_rework* ai = FindIlluciaAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Illucia: {}", ai->TestState());
        return true;
    }

    // `.dbtest scholo illucia foresight [markers] [trail 0|1]`: a Foresight chain on the selected player (or you);
    // defaults are the map's (normal 3 markers, heroic 5 and the Memory trail) (IB1, IB2).
    bool HandleForesight(ChatHandler* handler, Optional<uint32> markers, Optional<uint32> trail)
    {
        boss_lady_illucia_barov_rework* ai = FindIlluciaAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        Creature* boss = IlluciaOf(ai);
        if (boss->HasUnitState(UNIT_STATE_CASTING))
        {
            handler->SendErrorMessage("{}", "Illucia is casting; try again in a moment.");
            return false;
        }
        uint8 const count = markers ? uint8(std::clamp<uint32>(*markers, 1, 10)) : 0;
        std::optional<bool> withTrail;
        if (trail)
            withTrail = *trail != 0;
        ai->Fight().Foresight(boss, { target }, count, withTrail);
        handler->PSendSysMessage("Illucia: Foresight on {} (IB1{}).", target->GetName(),
            withTrail.value_or(DungeonKit::IsHeroicMap(boss)) ? ", Memory trail IB2" : "");
        return true;
    }

    // `.dbtest scholo illucia fear`: the Fear cast on the selected player (or you); kick or dispel it (IB3).
    bool HandleFear(ChatHandler* handler)
    {
        boss_lady_illucia_barov_rework* ai = FindIlluciaAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        Creature* boss = IlluciaOf(ai);
        if (boss->HasUnitState(UNIT_STATE_CASTING))
        {
            handler->SendErrorMessage("{}", "Illucia is casting; try again in a moment.");
            return false;
        }
        bool const cast = ai->Fight().Fear(boss, target);
        handler->PSendSysMessage("Illucia: Fear on {} (IB3){}.", target->GetName(), cast ? "" : ": the cast failed");
        return true;
    }

    // `.dbtest scholo illucia lesson [heroic 0|1]`: the Shadow Vault lesson on the selected player (or you), owned by a
    // temporary trigger at their feet. The lesson's safety rule ends it at once when nobody else (a living non-GM
    // player) is in the instance: select a bot, or `.gm off` with a second character.
    bool HandleLesson(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_lady_illucia_barov_rework* ai = FindIlluciaAI(handler);
        Player* student = TestTarget(handler);
        if (!ai || !student)
            return false;
        Creature* owner = student->SummonCreature(kTestLessonOwnerEntry, student->GetPosition(),
            TEMPSUMMON_TIMED_DESPAWN, kTestLessonOwnerMs);
        if (!owner)
        {
            handler->SendErrorMessage("{}", "Could not summon the lesson's owner.");
            return false;
        }
        bool const isHeroic = heroic ? *heroic != 0 : DungeonKit::IsHeroicMap(student);
        if (!ai->TestLesson(owner, student, isHeroic))
        {
            handler->SendErrorMessage("{}", "No Shadow Vault lesson is registered.");
            return false;
        }
        handler->PSendSysMessage("Illucia: the Shadow Vault lesson ({}) on {}; `state` shows the verdict.",
            isHeroic ? "heroic, 5 markers" : "normal, 3 markers", student->GetName());
        return true;
    }

    ChatCommandTable const& IlluciaTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "foresight", HandleForesight, SEC_GAMEMASTER, Console::No },
            { "fear",      HandleFear,      SEC_GAMEMASTER, Console::No },
            { "lesson",    HandleLesson,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_lady_illucia_barov_rework()
{
    RegisterDungeonReworkCreatureAI(boss_lady_illucia_barov_rework, ScholomanceRework::kInstanceScriptName);
    // The examiner's script name is IlluciaLogic.h kExaminerScriptName; S13 binds the entry in wave C.
    if (kWaveCBound)
        RegisterDungeonReworkCreatureAI(npc_sc_examiner_illucia, ScholomanceRework::kInstanceScriptName);
    RegisterSpellScript(spell_scholo_illucia_fear);
    RegisterSoloLesson(Classroom::ShadowVault, [] { return std::unique_ptr<SoloLesson>(new ShadowVaultLesson()); });
    ScholoTest::RegisterBoss("illucia", IlluciaTestCommands());
}
