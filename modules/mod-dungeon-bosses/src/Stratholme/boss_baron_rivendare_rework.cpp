/*
 * mod-dungeon-bosses, Stratholme S14: Baron Rivendare (10440), normal and heroic. Build spec: ST 3842-3906 (build
 * spec), ST 3487-3841 (design: pitch B "Lord of the Dead", the core loop "pick a graveyard", rulings 55-59); handoff
 * section 3.4 rows BR, section 3.5 row S14, section 3.6, section 3.8 (the room). Replaces SmartAI 10440 (twenty rows:
 * the spell timers, Raise Dead and Death Pact, the door rows, the leash and the summon cleanup) and SmartAI 11197
 * (three rows); WP-S14's SQL rev drops them. Bound by apps/dbc-tools source/npcs/stratholme/baron_rivendare.py.
 *
 *   BR1 Raise Dead       first at 6 s, then every 20 s: 3 Mindless Skeletons 11197 at the three stock points of one
 *                        wall (spell_target_position 17475-17480), walls alternating (emote line 7). They run at his
 *                        victim on normal threat and strike it every 2 s (206711: 2% / 2.5% of the reference row,
 *                        about 1% / 1.25% a second). Normal caps the living pile at 6 (a wave rises short); heroic has
 *                        no cap.
 *   BR2 Bone piles       every skeleton that dies leaves a pile (gameobject 301207) where it fell, until raised or the
 *                        fight ends. Bots: a hidden Park zone walks him off a pile within 4 yd (the tank's reposition).
 *   BR3 Death and Decay  first at 12 s, then every 15 s: a 6 yd circle follows a random non-tank for 3 s (206708,
 *                        emote line 10; X2's drop spot: the room's edge, away from the group, and on heroic off the
 *                        piles), then the ground rots there (rot stalker 300588, 206710's look): 10 s / 15 s, 4% / 5%
 *                        Shadow a second, one Weakened per player, a 1 s grace. Heroic: every pile inside rises, at the
 *                        landing and every second while it lasts.
 *   BR4 Unholy Aura      206705 on him from the pull: every 2 s a Shadow pulse (206706) on everyone in his fight within
 *                        100 yd, 1% / 1.5% of the reference row +0.5% per living servant.
 *   BR5 Stock tank kit   Shadow Bolt 17393 (a 2 s cast on his victim every 6 to 9 s; the cast queue: it waits for the
 *                        hard mode's casts), Mortal Strike 15708 (9 to 15 s), Cleave 15284 (7 to 11 s; live at 10%),
 *                        melee (DamageModifier 8, the DT file).
 *   Leash                BaronArena() with LeashOptions (no grips; he holds at the edge, evades after 10 s with nobody
 *                        on it) plus the stock leash (21 yd from Ramstein's door 175405, or 4 yd from his own door
 *                        while 13 yd or more from Menethil's Gift).
 *   Death                yell line 15; a living Ysida is freed (her SmartAI's SetData(2, 2), the stock row 13). The
 *                        instance opens the exit gate when she is dead and settles the Ultimatum.
 *
 * Every timer runs on the AI's own clock (BaronLogic.h Timeline), never on BossAI's scheduler that a cast bar pauses.
 * The hard mode (WP-S15, the Ultimatum) fights on this AI through BaronFight.h (BaronHardMode hooks; this class is its
 * BaronFight). Every firing logs one INFO line "strat baron <mechanic> ..." (module.dungeonbosses); `.dbtest strat
 * baron <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BaronFight.h"
#include "BaronLogic.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeKit.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <list>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratBaron;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kBossLogName = "baron";

    // Ysida Harmon's SmartAI (16031 rows 2-8): SetData(2, 2) frees her (the cage, her thanks, the quest credit, the
    // exit gate), what the stock row 13 of 10440 did on his death.
    enum YsidaData : uint32
    {
        YSIDA_DATA_FREE         = 2,
        YSIDA_DATA_FREE_VALUE   = 2,
    };

    float constexpr kFloorZ = 115.2f;               // the room's floor (the arena's z band is 115..117.5)
    float constexpr kFloorProbeUpYd = 2.f;
    float constexpr kFloorMaxDropYd = 4.f;

    BaronHardModeFactory& HardModeFactory()
    {
        static BaronHardModeFactory factory;
        return factory;
    }

    // The floor under a point; falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + kFloorProbeUpYd);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > kFloorMaxDropYd) ? z : floor;
    }

    Point3 ToPoint3(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY(), p.GetPositionZ() };
    }
}

void StratBaron::RegisterBaronHardMode(BaronHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

std::unique_ptr<BaronHardMode> StratBaron::CreateBaronHardMode(Creature* baron)
{
    BaronHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(baron) : nullptr;
}

// Baron Rivendare 10440
struct boss_baron_rivendare_rework : public BossAI, public BaronFight
{
    explicit boss_baron_rivendare_rework(Creature* creature)
        : BossAI(creature, BOSS_BARON), _arena(BaronArena(), LeashOptions(kBossLogName)), _queue(kCastSpacingMs) { }

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);       // DoZoneInCombat, BOSS_BARON IN_PROGRESS (the instance shuts his door)
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup(false);     // a `.dbtest strat baron` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _raiseForm = _heroic;
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_BARON;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        DoCastSelf(SPELL_BR_UNHOLY_AURA, true);
        _queue.Schedule(CAST_SHADOW_BOLT, _timeline.now + kShadowBoltFirstMs, 0);

        bool const hardMode = _heroic && instance && instance->GetData(DATA_ULTIMATUM) != 0;
        if (hardMode)
            _hardMode = CreateBaronHardMode(me);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} hardmode={} handler={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0,
                hardMode ? 1 : 0, _hardMode ? 1 : 0, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
        if (_hardMode)
            _hardMode->OnEngage(*this);     // S15 says its own pull yell (line 11)
        else
            Talk(YELL_BARON_AGGRO);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_BARON_DEATH);
        Cleanup(true);      // first: the hard mode settles a fallen (hidden, living) Ysida, so she is never freed
        FreeYsida();
        BossAI::JustDied(killer);           // BOSS_BARON DONE: the instance settles the Ultimatum and the exit gate
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    // His summons: the skeletons (and S15's servants) join his fight; the rot stalkers are invisible helpers.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
        if (summon->GetEntry() != NPC_ST_ROT && me->IsEngaged())
            DoZoneInCombat(summon);
    }

    // BR2: every skeleton that dies leaves a pile where it fell.
    void SummonedCreatureDies(Creature* summon, Unit* /*killer*/) override
    {
        if (summon && summon->GetEntry() == NPC_MINDLESS_SKELETON)
            AddPile(summon->GetPosition(), "death");
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    void UpdateAI(uint32 diff) override
    {
        // Out of combat too: a `.dbtest` rot ticks and raises.
        _clockMs += diff;
        UpdateRots(diff);

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _timeline.Advance(diff);
        if (CheckStockLeash(diff))
            return;     // evading
        if (_hardMode)
        {
            _hardMode->OnUpdate(*this, diff);
            if (!_engaged || !me->IsAlive())
                return;     // the hook ended the fight
        }

        if (_timeline.Due(Beat::RaiseDead))
            RaiseDead(std::nullopt);
        if (_timeline.Due(Beat::DeathAndDecay))
            DeathAndDecay(nullptr, _heroic);
        UpdatePark(diff);

        if (Busy())
            return;
        RunQueue();
        if (Busy())
            return;
        StockMelee();
        DoMeleeAttackIfReady();
    }

    // ---- BaronFight (the hard mode's view of the pull, BaronFight.h) ------------------------------------------------

    Creature* Baron() override
    {
        return me;
    }

    bool Heroic() const override
    {
        return _heroic;
    }

    BaronHardMode* ActiveHardMode() override
    {
        return _hardMode.get();
    }

    uint64 FightMs() const override
    {
        return _timeline.now;
    }

    uint64 ClockMs() const override
    {
        return _clockMs;
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

    std::vector<Creature*> Servants() override
    {
        std::vector<Creature*> out;
        for (ObjectGuid const& guid : summons)
            if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                if (add->IsAlive() && add->GetEntry() == NPC_MINDLESS_SKELETON)
                    out.push_back(add);
        for (ObjectGuid const& guid : _servants)
            if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                if (add->IsAlive() && std::find(out.begin(), out.end(), add) == out.end())
                    out.push_back(add);
        return out;
    }

    void TrackServant(Creature* servant) override
    {
        if (servant && std::find(_servants.begin(), _servants.end(), servant->GetGUID()) == _servants.end())
            _servants.push_back(servant->GetGUID());
    }

    std::vector<Position> Piles() const override
    {
        std::vector<Position> out;
        out.reserve(_piles.size());
        for (Pile const& pile : _piles)
            out.emplace_back(pile.at.x, pile.at.y, pile.at.z, 0.f);
        return out;
    }

    uint32 RaisePilesWithin(Position const& center, float radius, char const* why) override
    {
        std::vector<Point3> spots;
        spots.reserve(_piles.size());
        for (Pile const& pile : _piles)
            spots.push_back(pile.at);
        std::vector<std::size_t> const inside = PilesInRot(spots, ToPoint3(center), radius);
        if (inside.empty())
            return 0;

        std::vector<Position> at;
        for (std::size_t i : inside)
        {
            Pile const& pile = _piles[i];
            at.emplace_back(pile.at.x, pile.at.y, pile.at.z, frand(0.f, DungeonKit::kTwoPi));
            if (GameObject* go = me->GetMap()->GetGameObject(pile.go))
                go->Delete();
        }
        for (auto it = inside.rbegin(); it != inside.rend(); ++it)
            _piles.erase(_piles.begin() + static_cast<std::ptrdiff_t>(*it));
        std::size_t const risen = SummonSkeletons(at).size();
        Log("raise-piles", Acore::StringFormat("why={} at=({:.1f},{:.1f}) r={:.1f} risen={} piles={}", why,
            center.GetPositionX(), center.GetPositionY(), radius, risen, _piles.size()));
        return uint32(risen);
    }

    ObjectGuid SpawnRot(RotSpec const& spec) override
    {
        if (spec.radius <= 0.f || spec.life.count() <= 0)
            return ObjectGuid::Empty;
        float const z = FloorZ(me, spec.at.GetPositionX(), spec.at.GetPositionY(), spec.at.GetPositionZ());
        Position const at(spec.at.GetPositionX(), spec.at.GetPositionY(), z, 0.f);
        uint32 const lifeMs = uint32(spec.life.count());

        ObjectGuid stalkerGuid;
        if (Creature* stalker = me->SummonCreature(NPC_ST_ROT, at, TEMPSUMMON_TIMED_DESPAWN, lifeMs))
        {
            stalker->SetReactState(REACT_PASSIVE);
            if (spec.lookSpell)
                stalker->CastSpell(stalker, spec.lookSpell, true);
            stalkerGuid = stalker->GetGUID();
        }

        if (spec.tickPct > 0.f && lifeMs > kRotGraceMs)
        {
            DungeonKit::LingerSpec linger;
            linger.duration = Milliseconds(lifeMs - kRotGraceMs);
            linger.tick = Milliseconds(kRotTickMs);         // the grace: the first tick one tick after the landing
            linger.pct = spec.tickPct;
            linger.school = SPELL_SCHOOL_SHADOW;
            linger.spellId = SPELL_BR_ROT;
            linger.slow = false;
            linger.tag = spec.tag;
            MechanicRef ref = DungeonKit::Linger(me, BossMechanics::Shapes::Circle(at, spec.radius), linger);
            ref.WeakenedOncePerPlayer().Within(RoomBounds());
            Track(ref.Handle());
        }

        Rot rot;
        rot.info = { stalkerGuid, at, spec.radius, spec.tag, _clockMs, _clockMs + lifeMs };
        rot.raises = spec.raises && _raiseForm;
        _rots.push_back(rot);
        Log("rot", Acore::StringFormat("at=({:.1f},{:.1f}) r={:.1f} life={}ms pct={:.1f} raises={} tag={}",
            at.GetPositionX(), at.GetPositionY(), spec.radius, lifeMs, spec.tickPct, rot.raises ? 1 : 0, spec.tag));
        if (rot.raises)
            RaisePilesWithin(at, spec.radius, "rot-landing");
        return stalkerGuid;
    }

    std::vector<RotInfo> Rots() const override
    {
        std::vector<RotInfo> out;
        for (Rot const& rot : _rots)
            out.push_back(rot.info);
        return out;
    }

    bool InAnyRot(Position const& p) const override
    {
        for (Rot const& rot : _rots)
            if (PileInRot(ToPoint3(p), ToPoint3(rot.info.center), rot.info.radius))
                return true;
        return false;
    }

    BossMechanics::SpotBounds RoomBounds() const override
    {
        std::vector<Position> points;
        for (Vec2 const& p : BoundsPolygon())
            points.emplace_back(p.x, p.y, kFloorZ, 0.f);
        BossMechanics::SpotBounds bounds;
        bounds.Polygon(std::move(points), kBoundsZMin, kBoundsZMax)
            .KeepOut(Position(kBaronDoor.x, kBaronDoor.y, kBaronDoor.z, 0.f), kOwnDoorKeepOutYd)
            .KeepOut(Position(kRamsteinDoor.x, kRamsteinDoor.y, kRamsteinDoor.z, 0.f), kRamsteinDoorKeepOutYd)
            .PathInside();
        return bounds;
    }

    BossMechanics::DropSpotRule RoomDropRule(bool avoidPiles) const override
    {
        // No Room: the bounds' single polygon is the drop's room (its edge candidates follow the real walls).
        BossMechanics::DropSpotRule rule;
        rule.Edge().Away().Within(RoomBounds());
        if (avoidPiles)
            for (Pile const& pile : _piles)
                rule.Avoid(Position(pile.at.x, pile.at.y, pile.at.z, 0.f), kPileAvoidRadius);
        return rule;
    }

    bool CanStandAt(Position const& p) const override
    {
        Vec2 const at{ p.GetPositionX(), p.GetPositionY() };
        return p.GetPositionZ() >= kBoundsZMin && p.GetPositionZ() <= kBoundsZMax && InBounds(at);
    }

    void ScheduleCast(uint32 id, uint32 inMs, uint8 priority) override
    {
        if (id < kHardModeCastBase)
            return;
        _queue.Schedule(id, _timeline.now + inMs, priority);
        if (std::find(_hardModeCasts.begin(), _hardModeCasts.end(), id) == _hardModeCasts.end())
            _hardModeCasts.push_back(id);
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

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // ---- BR4 Unholy Aura --------------------------------------------------------------------------------------------

    // The percent one pulse deals now (the pulse's SpellScript reads it at launch).
    float UnholyAuraPctNow()
    {
        return UnholyAuraPct(_heroic, uint32(Servants().size()));
    }

    // ---- BR1 Raise Dead ---------------------------------------------------------------------------------------------

    // `wall`: that wall (a test), else the next in turn. Returns how many rose.
    uint32 RaiseDead(std::optional<Wall> wall)
    {
        _timeline.Done(Beat::RaiseDead);
        Wall const w = wall ? *wall : _nextWall;
        _nextWall = OtherWall(w);
        uint32 const alive = uint32(LivingSkeletons());
        uint32 const count = WaveCount(alive, _heroic);
        if (!count)
        {
            Log("raise-dead", Acore::StringFormat("wall={} capped alive={}", WallName(w), alive));
            return 0;
        }
        Talk(EMOTE_BARON_RAISE_DEAD);
        std::vector<Position> at;
        for (Point3 const& p : WallPoints(w))
        {
            if (at.size() >= count)
                break;
            at.emplace_back(p.x, p.y, p.z, me->GetAngle(p.x, p.y) + float(M_PI));
        }
        std::size_t const risen = SummonSkeletons(at).size();
        Log("raise-dead", Acore::StringFormat("wall={} risen={} alive={} heroic={}", WallName(w), risen, alive,
            _heroic ? 1 : 0));
        return uint32(risen);
    }

    // ---- BR2 Bone piles ---------------------------------------------------------------------------------------------

    void AddPile(Position const& where, char const* why)
    {
        float const z = FloorZ(me, where.GetPositionX(), where.GetPositionY(), where.GetPositionZ());
        Pile pile;
        pile.at = { where.GetPositionX(), where.GetPositionY(), z };
        if (GameObject* go = me->SummonGameObject(GO_ST_BONE_PILE, pile.at.x, pile.at.y, z,
            frand(0.f, DungeonKit::kTwoPi), 0.f, 0.f, 0.f, 0.f, kPileLifeSecs))
            pile.go = go->GetGUID();
        _piles.push_back(pile);
        Log("pile", Acore::StringFormat("why={} at=({:.1f},{:.1f}) piles={}", why, pile.at.x, pile.at.y,
            _piles.size()));
    }

    // ---- BR3 Death and Decay ----------------------------------------------------------------------------------------

    // `forced`: on that player, else a random non-tank. `heroicForm`: the rot's heroic numbers and raise.
    bool DeathAndDecay(Player* forced, bool heroicForm)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;
            rule.tankIfAlone = true;        // a solo tank (a test) still gets it
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
        {
            _timeline.Retry(Beat::DeathAndDecay);
            return false;
        }
        _timeline.Done(Beat::DeathAndDecay);
        me->CastSpell(target, SPELL_BR_DEATH_AND_DECAY, true);
        Talk(EMOTE_BARON_ROT, target);

        DungeonKit::ImpactSpec impact;      // telegraph only: the rot it leaves owns the damage
        impact.pct = 0.f;
        impact.weakened = false;
        impact.tag = TAG_DEATH_AND_DECAY;
        MechanicRef ref = DungeonKit::FollowThenLand(me, target, kRotRadius, Milliseconds(kDeathAndDecayWarnMs),
            impact, [heroicForm](Creature* owner, Position const& spot, BossMechanics::ResolveResult const& /*r*/)
            {
                if (!owner || !owner->IsAlive() || !owner->IsAIEnabled)
                    return;
                if (auto* ai = dynamic_cast<boss_baron_rivendare_rework*>(owner->AI()))
                    ai->LandDeathAndDecay(spot, heroicForm);
            });
        // X2's drop spot: the carrier takes it to the room's edge, away from the group; on heroic off the piles too.
        ref.DropSpot(RoomDropRule(heroicForm)).Within(RoomBounds());
        Track(ref.Handle());
        Log("death-and-decay", Acore::StringFormat("target={} heroic={} piles={}", target->GetName(),
            heroicForm ? 1 : 0, _piles.size()));
        return true;
    }

    // The circle landed: the ground rots there (10 s / 15 s, the hard mode's length from S15's hook).
    void LandDeathAndDecay(Position const& spot, bool heroicForm)
    {
        uint32 lifeMs = kRotLifeMs(heroicForm);
        if (_hardMode)
            lifeMs = _hardMode->DeathAndDecayLifeMs(*this, lifeMs);
        RotSpec spec;
        spec.at = spot;
        spec.radius = kRotRadius;
        spec.life = Milliseconds(lifeMs);
        spec.tickPct = kRotPct(heroicForm);
        spec.tag = TAG_ROT;
        spec.raises = true;
        bool const wasRaiseForm = _raiseForm;
        _raiseForm = heroicForm;
        SpawnRot(spec);
        _raiseForm = wasRaiseForm;
    }

    // ---- `.dbtest strat baron` entry points -------------------------------------------------------------------------

    bool HeroicMap() const
    {
        return DungeonKit::IsHeroicMap(me);
    }

    void TestPrepare()
    {
        if (!_engaged)
        {
            _heroic = HeroicMap();
            _raiseForm = _heroic;
        }
    }

    uint32 TestRaiseDead(std::optional<Wall> wall)
    {
        TestPrepare();
        return RaiseDead(wall);
    }

    bool TestDeathAndDecay(Player* target, bool heroicForm)
    {
        TestPrepare();
        return DeathAndDecay(target, heroicForm);
    }

    void TestPile(Position const& at)
    {
        AddPile(at, "test");
    }

    uint32 TestRise(Position const& at)
    {
        TestPrepare();
        return RaisePilesWithin(at, kRotRadius, "test");
    }

    bool TestPark()
    {
        return Park(true);
    }

    std::string TestState()
    {
        std::string out = Acore::StringFormat("engaged={} heroic={} hardmode={} t={}ms next raise/rot/ms/cleave="
            "{}/{}/{}/{}ms next wall={} skeletons={} servants={} piles={} rots={} aura={:.1f}%", _engaged ? 1 : 0,
            _heroic ? 1 : 0, _hardMode ? 1 : 0, _timeline.now, _timeline.NextAt(Beat::RaiseDead),
            _timeline.NextAt(Beat::DeathAndDecay), _timeline.NextAt(Beat::MortalStrike),
            _timeline.NextAt(Beat::Cleave), WallName(_nextWall), LivingSkeletons(), Servants().size(),
            _piles.size(), _rots.size(), UnholyAuraPctNow());
        for (Pile const& pile : _piles)
            out += Acore::StringFormat("\n  pile ({:.1f}, {:.1f}, {:.1f})", pile.at.x, pile.at.y, pile.at.z);
        for (Rot const& rot : _rots)
            out += Acore::StringFormat("\n  rot ({:.1f}, {:.1f}) r {:.1f} left {}ms raises {} tag {}",
                rot.info.center.GetPositionX(), rot.info.center.GetPositionY(), rot.info.radius,
                rot.info.untilMs > _clockMs ? rot.info.untilMs - _clockMs : 0, rot.raises ? 1 : 0, rot.info.tag);
        return out;
    }

private:
    struct Pile
    {
        ObjectGuid go;
        Point3 at;
    };

    struct Rot
    {
        RotInfo info;
        bool raises = false;
    };

    void Describe()
    {
        // Boss data (build spec): kill the skeletons (AoE welcome: they stack on the tank), then him. No interrupts,
        // no dispels. S15 adds Ysida, Risen above them (Mechanic::EditDescriptor).
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_MINDLESS_SKELETON, 2).AoeOk());
        Mechanic::Describe(me, std::move(d));
    }

    std::size_t LivingSkeletons()
    {
        std::size_t n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                if (add->IsAlive() && add->GetEntry() == NPC_MINDLESS_SKELETON)
                    ++n;
        return n;
    }

    // Skeletons at `at` (a wave or risen piles): each runs at his victim with a little threat on it and rises with
    // the Raise Dead look. Health is the template's (normal 6,000, the heroic copy 7,500).
    std::vector<Creature*> SummonSkeletons(std::vector<Position> const& at)
    {
        DungeonKit::WaveSpec spec;
        spec.entry = NPC_MINDLESS_SKELETON;
        spec.type = TEMPSUMMON_CORPSE_TIMED_DESPAWN;
        spec.despawn = Milliseconds(kSkeletonCorpseMs);
        ObjectGuid const victimGuid = me->GetVictim() ? me->GetVictim()->GetGUID() : ObjectGuid::Empty;
        spec.onSummon = [this, victimGuid](Creature* add)
        {
            add->CastSpell(add, SPELL_BR_RISE, true);
            Unit* victim = victimGuid ? ObjectAccessor::GetUnit(*me, victimGuid) : nullptr;
            if (victim && victim->IsAlive() && add->IsAIEnabled)
            {
                add->AddThreat(victim, kSkeletonOpeningThreat);
                add->AI()->AttackStart(victim);
            }
        };
        return DungeonKit::SummonWave(me, spec, at, summons);
    }

    // A second of the rots: expired ones go; the piles inside a raising rot rise; S15's tick (the heal).
    void UpdateRots(uint32 diff)
    {
        if (_rots.empty())
        {
            _rotTickMs = 0;
            return;
        }
        _rotTickMs += diff;
        if (_rotTickMs < kRotTickMs)
            return;
        _rotTickMs -= kRotTickMs;

        std::vector<Rot> live;
        for (Rot const& rot : _rots)
        {
            if (_clockMs >= rot.info.untilMs)
            {
                if (Creature* stalker = ObjectAccessor::GetCreature(*me, rot.info.stalker))
                    stalker->DespawnOrUnsummon();
                continue;
            }
            live.push_back(rot);
        }
        _rots = live;
        for (Rot const& rot : live)
        {
            if (rot.raises)
                RaisePilesWithin(rot.info.center, rot.info.radius, "rot");
            if (_hardMode && _engaged)
                _hardMode->OnRotTick(*this, rot.info);
        }
    }

    // BR2 for the bots: when a pile lies within 4 yd of him, a hidden tank-only Park zone on a clean floor spot.
    void UpdatePark(uint32 diff)
    {
        _parkCheckMs += diff;
        if (_parkCheckMs < kParkCheckMs)
            return;
        _parkCheckMs = 0;
        Park(false);
    }

    bool Park(bool force)
    {
        if (!force && (_timeline.now < _parkUntil || _piles.empty()))
            return false;
        std::vector<Point3> spots;
        for (Pile const& pile : _piles)
            spots.push_back(pile.at);
        if (!force && !ShouldPark(DungeonKit::PlaneOf(me), spots))
            return false;

        // R-1-B B-1: on the room's floor inside the bounds (ParkArena, not the r 25 leash circle that reaches through
        // the east wall), reachable on the navmesh, off both doors; a best-effort pick outside the bounds is refused.
        std::vector<DungeonKit::AvoidCircle> rots;
        for (Rot const& rot : _rots)
            rots.push_back({ Vec2{ rot.info.center.GetPositionX(), rot.info.center.GetPositionY() }, rot.info.radius });
        DungeonKit::FloorSpotRules const rules = ParkRules(DungeonKit::PlaneOf(me), spots, rots);
        DungeonKit::FloorProbe probe;
        probe.z = me->GetPositionZ();
        probe.reachable = true;
        DungeonKit::Arena const room = ParkArena();
        std::optional<Position> const spot = DungeonKit::PickFloorSpot(me, &room, rules, probe);
        _parkUntil = _timeline.now + kParkHoldMs + kParkCooldownMs;
        if (!spot || !InBounds(Vec2{ spot->GetPositionX(), spot->GetPositionY() }))
        {
            Log("park", spot ? "spot out of bounds" : "no floor spot");
            return false;
        }
        BossMechanics::Eligibility tankOnly;
        tankOnly.roles = BossMechanics::Role::Tank;
        MechanicRef ref = Mechanic::Circle(me, *spot, kParkRadius, Milliseconds(kParkHoldMs));
        ref.Park(me).NoTelegraph().Eligible(tankOnly).Within(RoomBounds()).Tag(TAG_PARK);
        Track(ref.Handle());
        Log("park", Acore::StringFormat("to=({:.1f},{:.1f}) piles={}", spot->GetPositionX(), spot->GetPositionY(),
            _piles.size()));
        return true;
    }

    // True when he is evading.
    bool CheckStockLeash(uint32 diff)
    {
        _leashCheckMs += diff;
        if (_leashCheckMs < kLeashCheckMs)
            return false;
        _leashCheckMs = 0;
        if (!StockLeashBreached(DungeonKit::PlaneOf(me)))
            return false;
        Log("leash", Acore::StringFormat("at=({:.1f},{:.1f})", me->GetPositionX(), me->GetPositionY()));
        EnterEvadeMode(EVADE_REASON_BOUNDARY);
        return true;
    }

    // A cast bar of his, or a hard mode cast holding him (the charge).
    bool Busy() const
    {
        return me->HasUnitState(UNIT_STATE_CASTING) || _timeline.now < _holdUntil;
    }

    // The cast queue: the Shadow Bolt (the filler) and S15's casts, one at a time.
    void RunQueue()
    {
        uint64 const now = _timeline.now;
        std::optional<uint32> const next = _queue.Next(now);
        if (!next)
            return;
        if (*next == CAST_SHADOW_BOLT)
        {
            // It waits for the hard mode's casts (R-1-B N-1): never started when one falls due within its cast time,
            // so the execution and the charge start on time and their cadence never drifts.
            for (uint32 id : _hardModeCasts)
                if (std::optional<uint64> const due = _queue.DueAt(id); due && FillerWaits(now, *due))
                    return;
            Unit* victim = me->GetVictim();
            SpellCastResult const result = victim ? me->CastSpell(victim, SPELL_SHADOW_BOLT_BARON, false)
                : SPELL_FAILED_BAD_TARGETS;
            if (result == SPELL_CAST_OK)
            {
                _queue.Started(CAST_SHADOW_BOLT, now, kShadowBoltCastMs, false);
                _queue.Schedule(CAST_SHADOW_BOLT, now + urand(kShadowBoltMinMs, kShadowBoltMaxMs), 0);
            }
            else
                _queue.Schedule(CAST_SHADOW_BOLT, now + kRetryMs, 0);
            return;
        }
        std::optional<uint32> const holdMs = _hardMode ? _hardMode->OnCast(*this, *next) : std::nullopt;
        if (!holdMs)
        {
            _queue.Cancel(*next);
            return;
        }
        _queue.Started(*next, now, *holdMs);
        _holdUntil = now + *holdMs;
    }

    // BR5: Mortal Strike and Cleave on his victim in melee range.
    void StockMelee()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return;
        bool const inReach = me->IsWithinMeleeRange(victim);
        if (_timeline.Due(Beat::MortalStrike))
        {
            if (inReach && DoCastVictim(SPELL_MORTAL_STRIKE) == SPELL_CAST_OK)
                _timeline.Done(Beat::MortalStrike, urand(kMortalStrikeMinMs, kMortalStrikeMaxMs));
            else
                _timeline.Retry(Beat::MortalStrike, kMeleeRetryMs);
            return;
        }
        if (_timeline.Due(Beat::Cleave))
        {
            if (inReach && DoCastVictim(SPELL_CLEAVE) == SPELL_CAST_OK)
                _timeline.Done(Beat::Cleave, urand(kCleaveMinMs, kCleaveMaxMs));
            else
                _timeline.Retry(Beat::Cleave, kMeleeRetryMs);
        }
    }

    // Stock row 13 of 10440: his death frees a living Ysida (she opens the exit gate herself).
    void FreeYsida()
    {
        if (!instance)
            return;
        if (Creature* ysida = instance->GetCreature(DATA_YSIDA_GUID))
            if (ysida->IsAlive() && ysida->IsAIEnabled && ysida->AI())
            {
                ysida->AI()->SetData(YSIDA_DATA_FREE, YSIDA_DATA_FREE_VALUE);
                Log("ysida", "freed");
            }
    }

    // The pull's state, gone: the hard mode's own end first, every mechanic, the piles, the rots, every servant.
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
        for (Pile const& pile : _piles)
            if (GameObject* go = me->GetMap()->GetGameObject(pile.go))
                go->Delete();
        _piles.clear();
        for (Rot const& rot : _rots)
            if (Creature* stalker = ObjectAccessor::GetCreature(*me, rot.info.stalker))
                stalker->DespawnOrUnsummon();
        _rots.clear();
        for (ObjectGuid const& guid : _servants)
            if (Creature* servant = ObjectAccessor::GetCreature(*me, guid))
                servant->DespawnOrUnsummon();
        _servants.clear();
        summons.DespawnAll();
        _queue.Reset();
        _hardModeCasts.clear();
        _timeline = Timeline{};
        _nextWall = Wall::South;
        _holdUntil = 0;
        _parkUntil = 0;
        _parkCheckMs = 0;
        _leashCheckMs = 0;
        _rotTickMs = 0;
        _engaged = false;
        _arena.Reset();
        me->RemoveAurasDueToSpell(SPELL_BR_UNHOLY_AURA);
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_BR_DEATH_AND_DECAY);
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CastQueue _queue;
    Timeline _timeline;
    std::unique_ptr<BaronHardMode> _hardMode;
    std::vector<uint32> _hardModeCasts;     // the cast queue ids the hard mode has scheduled (the Shadow Bolt's wait)
    std::vector<MechanicHandle> _live;
    std::vector<Pile> _piles;
    std::vector<Rot> _rots;
    std::vector<ObjectGuid> _servants;
    Wall _nextWall = Wall::South;
    uint64 _clockMs = 0;            // ms the AI has run (the rots' clock; never held)
    uint64 _holdUntil = 0;          // _timeline.now: a hard mode cast holds him until then
    uint64 _parkUntil = 0;          // _timeline.now: no new Park zone before then
    uint32 _parkCheckMs = 0;
    uint32 _leashCheckMs = 0;
    uint32 _rotTickMs = 0;
    bool _heroic = false;
    bool _raiseForm = false;        // the rots raise piles (heroic; a test may force it)
    bool _engaged = false;
};

// BR1 the skeletons (11197, the Baron's only): no auto attack; one strike every 2 s on their victim in melee range
// (206711, the kit's percent spell: 2% / 2.5% of the reference row, the tank row on the tank). Crowd control works
// (immunity set -122 kept): a stunned, feared or shackled skeleton does not strike.
struct npc_st_mindless_skeleton : public ScriptedAI
{
    explicit npc_st_mindless_skeleton(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _swingMs = kSkeletonFirstSwingMs;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        _swingMs = _swingMs > diff ? _swingMs - diff : 0;
        if (_swingMs || me->HasUnitState(UNIT_STATE_CASTING | UNIT_STATE_LOST_CONTROL))
            return;
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return;     // the swing waits for reach
        me->CastSpell(victim, SPELL_BR_SKELETON_STRIKE, true);
        _swingMs = kSkeletonSwingMs;
    }

private:
    uint32 _swingMs = kSkeletonFirstSwingMs;
};

// BR4 the Unholy Aura pulse 206706 (every 2 s from 206705 on him): everyone in his fight within 100 yd takes
// 1% / 1.5% of the reference row +0.5% per living servant (RefFlat at launch, so the target's defensives count; the
// spell ignores caster modifiers). Units not in combat with him (outside his room) are left out.
class spell_strat_baron_unholy_aura_pulse : public SpellScript
{
    PrepareSpellScript(spell_strat_baron_unholy_aura_pulse);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        Unit* caster = GetCaster();
        targets.remove_if([caster](WorldObject* object)
        {
            Unit* unit = object ? object->ToUnit() : nullptr;
            return !caster || !unit || !unit->IsInCombatWith(caster);
        });
    }

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float pct = UnholyAuraPct(DungeonKit::IsHeroicMap(caster), 0);
        if (Creature* baron = caster->ToCreature())
            if (baron->IsAIEnabled)
                if (auto* ai = dynamic_cast<boss_baron_rivendare_rework*>(baron->AI()))
                    pct = ai->UnholyAuraPctNow();
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_strat_baron_unholy_aura_pulse::FilterTargets,
            EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY);
        OnEffectLaunchTarget += SpellEffectFn(spell_strat_baron_unholy_aura_pulse::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_baron_rivendare_rework* FindBaronAI(ChatHandler* handler)
    {
        Creature* boss = StratTest::FindBoss(handler, NPC_BARON);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_baron_rivendare_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Baron is not running boss_baron_rivendare_rework (check the "
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

    bool HandleInfo(ChatHandler* handler)
    {
        return StratTest::ShowBossInfo(handler, NPC_BARON, BOSS_BARON);
    }

    // `.dbtest strat baron state`: the clock, the skeletons, the piles, the rots and the aura's percent now.
    bool HandleState(ChatHandler* handler)
    {
        boss_baron_rivendare_rework* ai = FindBaronAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Baron: {}", ai->TestState());
        return true;
    }

    // `.dbtest strat baron raise [north|south]`: a Raise Dead wave now (BR1; the normal cap holds).
    bool HandleRaise(ChatHandler* handler, Optional<std::string> wall)
    {
        boss_baron_rivendare_rework* ai = FindBaronAI(handler);
        if (!ai)
            return false;
        std::optional<Wall> w;
        if (wall && *wall == "north")
            w = Wall::North;
        else if (wall && *wall == "south")
            w = Wall::South;
        uint32 const risen = ai->TestRaiseDead(w);
        handler->PSendSysMessage("Baron: Raise Dead, {} risen (BR1).", risen);
        return true;
    }

    // `.dbtest strat baron rot [0|1]`: Death and Decay on the selected player (or you); 1 = the heroic form (15 s,
    // 5%, the piles inside rise), 0 = normal; default the map's (BR3).
    bool HandleRot(ChatHandler* handler, Optional<uint32> heroic)
    {
        boss_baron_rivendare_rework* ai = FindBaronAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        ai->TestDeathAndDecay(target, isHeroic);
        handler->PSendSysMessage("Baron: Death and Decay ({}) on {} (BR3).", isHeroic ? "heroic" : "normal",
            target->GetName());
        return true;
    }

    // `.dbtest strat baron pile`: a bone pile at the selected player's (or your) feet (BR2).
    bool HandlePile(ChatHandler* handler)
    {
        boss_baron_rivendare_rework* ai = FindBaronAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        ai->TestPile(target->GetPosition());
        handler->PSendSysMessage("Baron: a bone pile at {}'s feet (BR2).", target->GetName());
        return true;
    }

    // `.dbtest strat baron rise`: the piles within 6 yd of the selected player (or you) rise now (heroic BR3).
    bool HandleRise(ChatHandler* handler)
    {
        boss_baron_rivendare_rework* ai = FindBaronAI(handler);
        Player* target = TestTarget(handler);
        if (!ai || !target)
            return false;
        uint32 const risen = ai->TestRise(target->GetPosition());
        handler->PSendSysMessage("Baron: {} pile(s) rose (BR2 / BR3).", risen);
        return true;
    }

    // `.dbtest strat baron park`: the bot tank's reposition now (a hidden Park zone on a clean spot; BR2 bots).
    bool HandlePark(ChatHandler* handler)
    {
        boss_baron_rivendare_rework* ai = FindBaronAI(handler);
        if (!ai)
            return false;
        bool const parked = ai->TestPark();
        handler->PSendSysMessage("Baron: {}", parked ? "Park zone registered (bots only)." : "no floor spot found.");
        return true;
    }

    ChatCommandTable const& BaronTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",  HandleInfo,  SEC_GAMEMASTER, Console::No },
            { "state", HandleState, SEC_GAMEMASTER, Console::No },
            { "raise", HandleRaise, SEC_GAMEMASTER, Console::No },
            { "rot",   HandleRot,   SEC_GAMEMASTER, Console::No },
            { "pile",  HandlePile,  SEC_GAMEMASTER, Console::No },
            { "rise",  HandleRise,  SEC_GAMEMASTER, Console::No },
            { "park",  HandlePark,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_baron_rivendare_rework()
{
    RegisterDungeonReworkCreatureAI(boss_baron_rivendare_rework, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_st_mindless_skeleton, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_strat_baron_unholy_aura_pulse);
    StratTest::RegisterBoss("baron", BaronTestCommands());
}
