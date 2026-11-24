/*
 * mod-dungeon-bosses, Scarlet Monastery D5: Houndmaster Loksey (3974), his Tracking Hounds (300908) and the Kennel
 * Pups (300909), "The Hunt" (HUB ruling 20). Build spec LIB "Houndmaster Loksey" (docs/dungeons/
 * scarlet-monastery-2-library.md, LK1-LK6), handoff sections 3.4 (F5), 3.5 (row D5), 3.6, 3.8 (NM: the alcove, the
 * neck, the kennel hall and its two entries), 3.9 (G1's `mark-trail` row). Replaces his SmartAI (WP-S0's rev drops its
 * two rows; Bloodlust 6742 retired). The three stock Tracking Hounds at his feet (guids 40089-40091) are deleted by
 * rev_loksey_scarlet_monastery.sql; this script summons three of its own there. Bound by apps/dbc-tools
 * source/npcs/scarlet_monastery/loksey.py. Pure rules: LokseyLogic.h.
 *
 *   LK1  The Whistle      Called Rounds, a round every 15 s (heroic 12 s): Release, Mark, Heel (heroic: then Fetch);
 *                         the pull is the first Release. Each round is a whistle (look and sound, 8839) and an emote
 *   LK2  Release          the pull: his three hounds attack (yell 0). Every later Release: 3 pups from the hall's NE
 *                         and SE entries, normal never more than 6 alive; heroic a 2.5 s interruptible whistle, 3 pups
 *                         when kicked, 6 when it ran, no cap. Pups pick the tank first (rule 19)
 *   LK3  Mark             the Scent on a random player (never the tank or
 *                         the healer), 5 s (heroic two players, the dogs split); then
 *                         from each carrier a 5 yd marker every 0.5 s, 0-2 yd from them, one per free dog; a dog leaps
 *                         onto its marker 1.5 s later: 35% / 45% + Weakened to everyone inside (registry Circles; the
 *                         carrier's walk away from the group is a registry Bait on the carrier alone: F5, composed of
 *                         existing kinds, no new BM option)
 *   LK4  Heel             every free dog runs to him; 2.5 s later the dog with the most health is whipped into a
 *                         frenzy (+50% attack speed and damage, 30 s; heroic until it dies, stacking); no dog: his own
 *                         frenzy (+30% attack speed, 15 s). Whipped Frenzy and his own are Magic: a purge is a reward
 *   LK5  Correction       a 2 s cast, then a 90 degree, 8 yd cone in front of him: 30% / 40% + Weakened to everyone
 *                         but the tank (registry Frontal, TankExempt), the tank his own hit of 20% / 30% of tank
 *                         health when he stands in it. First at 6 s, every 10 s
 *   LK6  Fetch (heroic)   the stick lands a 3 yd circle 15-25 yd from him, 3 s after the whistle; every free dog races
 *                         for it. A player in the circle at the landing catches it (registry Soak, 1 body): every dog
 *                         sits and cowers for 6 s (pacified and rooted, +25% damage taken). Missed: every living dog
 *                         is whipped into a frenzy until it dies
 *
 * Every firing logs one INFO line "sm loksey <mechanic> ..." (module.dungeonbosses). Timers run on the scheduler (the
 * AI's own clock; a cast bar never pauses one). Bot sensitive geometry (RB-8): the markers, the Scent's walk and the
 * Fetch circle carry the bots' floor (LokseyLogic.h BotFloor: alcove, neck, hall).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "LokseyLogic.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmLoksey;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "loksey";

    uint32 constexpr POINT_ORDER = 1;           // a dog's run to a spot (the Heel, the race for the stick)
    uint32 constexpr GROUP_ROUND = 1;
    uint32 constexpr GROUP_CORRECTION = 2;
    uint32 constexpr GROUP_MARK = 3;
    uint32 constexpr GROUP_HEEL = 4;
    uint32 constexpr GROUP_FETCH = 5;
    float constexpr kFrenzySizeMult = 1.3f;     // LK4: a whipped dog is 30% bigger (a look, set by the dog's AI)

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogLk(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    float GroundZ(WorldObject const* probe, float x, float y, float refZ)
    {
        float const h = probe->GetMapHeight(x, y, refZ + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - refZ) > kGroundBandYd)
            return refZ;
        return h;
    }

    // The bots' hard bounds while a mechanic of the fight is in view (the markers, the Scent's walk, the Fetch circle):
    // LokseyLogic.h BotFloor, the alcove, its neck and the kennel hall on the floor's height band.
    BossMechanics::SpotBounds BotFloorBounds()
    {
        BossMechanics::SpotBounds bounds;
        for (std::array<Vec2, 4> const* polygon : { &kAlcovePolygon, &kNeckPolygon, &kHallPolygon })
        {
            std::vector<Position> points;
            for (Vec2 const& v : *polygon)
                points.emplace_back(v.x, v.y, kHallCenter.z, 0.f);
            bounds.Polygon(std::move(points), kFloorZMin, kFloorZMax);
        }
        return bounds;
    }

    // The test commands' forced mechanics (`.dbtest sm loksey ...`; out of combat the GM stands in for the group).
    enum class TestKind : uint8
    {
        Release,
        Mark,
        Heel,
        Fetch,
        Correction,
        Pack,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// The dogs: Loksey's Tracking Hound 300908 and the Kennel Pup 300909 (one behavior, two entries). Melee while they
// fight; the rest is on his orders: a leap onto a marker, the run to him, the race for the stick, the cower.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sm_loksey_dog : public ScriptedAI
{
    explicit npc_sm_loksey_dog(Creature* creature) : ScriptedAI(creature) { }

    enum class State : uint8
    {
        Fight,      // melee
        Hold,       // LK3: standing still until the take-off
        Leap,       // LK3: in the air
        Heel,       // LK4: running to him
        Fetch,      // LK6: racing for the stick
        Cower,      // LK6: sitting, pacified and rooted
    };

    void Reset() override
    {
        _state = State::Fight;
        _chaseAfterCc = false;
        _line = MechanicHandle();
        _scaled = false;
        me->SetReactState(REACT_AGGRESSIVE);
        me->RemoveAurasDueToSpell(SPELL_LK_WHIPPED_FRENZY);
        me->RemoveAurasDueToSpell(SPELL_LK_COWED);
        me->SetStandState(UNIT_STAND_STATE_STAND);
    }

    // A dog pulled before him pulls him (and so the pack).
    void JustEngagedWith(Unit* who) override
    {
        if (Creature* boss = Boss())
            if (boss->IsAlive() && !boss->IsInCombat() && boss->IsAIEnabled && who)
                boss->AI()->AttackStart(who);
    }

    // While Loksey fights, a dog never walks home on its own (a target lost for a moment): back into his fight.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (Creature* boss = Boss())
            if (boss->IsAlive() && boss->IsEngaged())
            {
                DoZoneInCombat();
                if (me->IsEngaged())
                    return;
            }
        ScriptedAI::EnterEvadeMode(why);
    }

    // Orders move it; a new target never pulls it off one.
    void AttackStart(Unit* who) override
    {
        if (_state == State::Fight)
            ScriptedAI::AttackStart(who);
    }

    void JustDied(Unit* /*killer*/) override
    {
        // A dog that dies before its leap draws no hit: its marker goes with it.
        if (_line)
            if (Creature* boss = Boss())
                Mechanic::Cancel(boss, _line);
        _line = MechanicHandle();
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        // LK4: a whipped dog is 30% bigger (a look; Whipped Frenzy is the mechanic).
        bool const frenzied = me->HasAura(SPELL_LK_WHIPPED_FRENZY);
        if (frenzied != _scaled)
        {
            _scaled = frenzied;
            me->SetObjectScale(me->GetNativeObjectScale() * (frenzied ? kFrenzySizeMult : 1.f));
        }

        switch (_state)
        {
            case State::Hold:
                if (CrowdControlled())
                    DropLeap();     // CC'd on its marker before the take-off: no leap, its marker goes
                else if (_clockMs >= _takeOffMs)
                    TakeOff();
                return;
            case State::Leap:
                if (_clockMs >= _landMs)
                    Land();
                return;
            case State::Heel:
                if (_clockMs >= _stateUntilMs)
                    BackToFight();  // nobody whipped it in time: back to the tank
                return;
            case State::Fetch:
                if (_clockMs >= _stateUntilMs)
                    BackToFight();  // the circle never resolved
                return;
            case State::Cower:
                if (_clockMs >= _stateUntilMs || !me->HasAura(SPELL_LK_COWED))
                    BackToFight();
                else if (me->getStandState() != UNIT_STAND_STATE_SIT)
                    me->SetStandState(UNIT_STAND_STATE_SIT);
                return;
            case State::Fight:
                break;
        }

        if (!UpdateVictim())
            return;
        if (_chaseAfterCc && !CrowdControlled())
        {
            _chaseAfterCc = false;
            BackToFight();
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Loksey's orders
    // ----------------------------------------------------------------------------------------------------------------

    // Free for an order: alive, fighting (not holding, leaping, running or cowering) and not crowd-controlled.
    bool Free() const
    {
        return me->IsAlive() && _state == State::Fight && !CrowdControlled();
    }

    // Feared, confused, stunned (traps, saps, incapacitates), rooted, banished or under a damage-breakable CC.
    bool CrowdControlled() const
    {
        return me->HasUnitState(UNIT_STATE_CONTROLLED | UNIT_STATE_ROOT)
            || me->HasAuraWithMechanic(1 << MECHANIC_BANISH) || me->HasBreakableByDamageCrowdControlAura();
    }

    // LK3: hold where it stands, take off `takeOffInMs` from now, land on `landing` `landInMs` from now.
    void HoldForLeap(Position const& landing, uint32 takeOffInMs, uint32 landInMs, MechanicHandle line)
    {
        _state = State::Hold;
        _landing = landing;
        _takeOffMs = _clockMs + takeOffInMs;
        _landMs = _clockMs + landInMs;
        _line = line;
        me->GetMotionMaster()->Clear();
        me->StopMoving();
    }

    // LK4: run to `spot` at his feet and wait for the whip.
    void Heel(Position const& spot)
    {
        if (_state != State::Fight || CrowdControlled())
            return;
        _state = State::Heel;
        _stateUntilMs = _clockMs + kHeelGiveUpMs;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_ORDER, spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ());
    }

    // The whip (or the give-up): the dogs that ran to him go back to the fight.
    void EndHeel()
    {
        if (_state == State::Heel)
            BackToFight();
    }

    // LK6: race for the stick (until the circle resolves; the give-up covers a circle that never does).
    void RaceTo(Position const& spot)
    {
        if (_state != State::Fight || CrowdControlled())
            return;
        _state = State::Fetch;
        _stateUntilMs = _clockMs + kFetchFlightMs + kHeelGiveUpMs;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_ORDER, spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ());
    }

    // LK6: the stick was caught: sit and cower (the Cowed aura pacifies and roots it and raises the damage it takes).
    void Cower(uint32 ms)
    {
        if (!me->IsAlive())
            return;
        _state = State::Cower;
        _stateUntilMs = _clockMs + ms;
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        me->AttackStop();
        me->CastSpell(me, SPELL_LK_COWED, true);
        me->SetStandState(UNIT_STAND_STATE_SIT);
    }

    // The stick was missed: back to the fight (the frenzy is Loksey's).
    void EndFetch()
    {
        if (_state == State::Fetch)
            BackToFight();
    }

    // A pup out of the kennels: into the fight on `target` (the tank first, rule 19).
    void BoundIn(Unit* target)
    {
        DoZoneInCombat();
        if (target)
        {
            me->AddThreat(target, kOpeningThreat);
            AttackStart(target);
        }
    }

    char const* StateName() const
    {
        switch (_state)
        {
            case State::Fight: return "fight";
            case State::Hold:  return "hold";
            case State::Leap:  return "leap";
            case State::Heel:  return "heel";
            case State::Fetch: return "fetch";
            case State::Cower: return "cower";
        }
        return "?";
    }

private:
    Creature* Boss() const
    {
        if (TempSummon const* summon = me->ToTempSummon())
            if (Unit* summoner = summon->GetSummonerUnit())
                return summoner->ToCreature();
        return nullptr;
    }

    void DropLeap()
    {
        if (_line)
            if (Creature* boss = Boss())
                Mechanic::Cancel(boss, _line);
        _line = MechanicHandle();
        _state = State::Fight;
        _chaseAfterCc = true;   // its hold cleared the chase: back on its victim once the CC breaks
        LogLk("leap-dropped", Acore::StringFormat("dog={} cc=1", me->GetGUID().GetCounter()));
    }

    void TakeOff()
    {
        _state = State::Leap;
        float const dist = me->GetExactDist2d(_landing.GetPositionX(), _landing.GetPositionY());
        uint64 const flightMs = _landMs > _clockMs ? _landMs - _clockMs : 1;
        float const speedXY = std::max(kLeapMinSpeedXY, dist * 1000.f / static_cast<float>(flightMs));
        DungeonKit::JumpTo(me, _landing, speedXY, kLeapMinSpeedZ);
    }

    void Land()
    {
        _line = MechanicHandle();
        BackToFight();
    }

    void BackToFight()
    {
        _state = State::Fight;
        me->SetReactState(REACT_AGGRESSIVE);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        if (!me->IsEngaged())
            return;
        Unit* target = me->GetVictim();
        if (!target)
            target = me->SelectVictim();
        if (target)
        {
            me->GetMotionMaster()->Clear();
            ScriptedAI::AttackStart(target);
            me->GetMotionMaster()->MoveChase(target);
        }
    }

    State _state = State::Fight;
    bool _chaseAfterCc = false;
    bool _scaled = false;
    uint64 _clockMs = 0;
    uint64 _takeOffMs = 0;
    uint64 _landMs = 0;
    uint64 _stateUntilMs = 0;
    Position _landing;
    MechanicHandle _line;
};

struct npc_sm_loksey_hound : public npc_sm_loksey_dog
{
    explicit npc_sm_loksey_hound(Creature* creature) : npc_sm_loksey_dog(creature) { }
};

struct npc_sm_kennel_pup : public npc_sm_loksey_dog
{
    explicit npc_sm_kennel_pup(Creature* creature) : npc_sm_loksey_dog(creature) { }
};

namespace
{
    npc_sm_loksey_dog* DogAI(Creature* creature)
    {
        if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
            return nullptr;
        return dynamic_cast<npc_sm_loksey_dog*>(creature->AI());
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Houndmaster Loksey 3974
// ---------------------------------------------------------------------------------------------------------------------
struct boss_houndmaster_loksey_rework : public BossAI
{
    explicit boss_houndmaster_loksey_rework(Creature* creature)
        : BossAI(creature, BOSS_LOKSEY), _arena(LokseyArena(), LeashOptions(kBoss)) { }

    // The AI behind a lambda's captured guid (registry callbacks capture guids only).
    static boss_houndmaster_loksey_rework* From(Map* map, ObjectGuid guid)
    {
        Creature* boss = map ? map->GetCreature(guid) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_houndmaster_loksey_rework*>(boss->AI());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();       // despawns the dogs (BossAI summons)
        Cleanup();
        _packDue = true;    // a fresh pack once he stands at home (UpdateAI)
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
        LogLk("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Cleanup();
        BossAI::JustDied(killer);   // the dogs despawn with him
        LogLk("death", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
    }

    void JustSummoned(Creature* summon) override
    {
        BossAI::JustSummoned(summon);   // into his fight when he is in one
        if (summon && IsDog(summon->GetEntry()) && me->IsEngaged())
            Mechanic::TrackUnit(me, summon);
    }

    // LK2 heroic: a whistle that ran its 2.5 s brings 6 pups.
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && spell->Id == SPELL_LK_RELEASE_CAST && Active())
            ReleaseLanded(false);
    }

    // LK2 heroic: a kicked (or silenced) whistle brings 3.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell && spell->Id == SPELL_LK_RELEASE_CAST && Active() && me->IsAlive())
            ReleaseLanded(true);
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);
        if (_packDue && me->IsAlive() && !me->IsInCombat() && !me->HasUnitState(UNIT_STATE_EVADE))
            SummonPack("home");

        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_fighting)
            return;

        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull, the pack
    // ----------------------------------------------------------------------------------------------------------------

    void StartFight()
    {
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        _testPlayer.Clear();
        OnBossPull(me, kBoss);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_LOKSEY;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        _fighting = true;
        _last = Round::Release;
        _pupDoor = 0;

        if (AliveDogs().empty())
            SummonPack("pull");
        summons.DoZoneInCombat(NPC_SM_TRACKING_HOUND);
        for (Creature* dog : AliveDogs())
            Mechanic::TrackUnit(me, dog);
        Describe();

        // LK1: the pull is the first Release (the yell, the whistle, the hounds on the group); the next round follows
        // one cadence later. LK5 first at 6 s.
        Talk(SAY_LOKSEY_RELEASE);
        me->CastSpell(me, SPELL_LK_WHISTLE, true);
        if (_heroic)
            Mechanic::NoteNextCastIn(me, SPELL_LK_RELEASE_CAST, Ms(CycleMs(true)));
        ScheduleRound(kRoundEveryMs(_heroic));
        ScheduleCorrection(kCorrectionFirstMs);
        LogLk("engage", Acore::StringFormat("heroic={} hounds={}", _heroic ? 1 : 0, AliveDogs().size()));
    }

    // Three hounds at his feet (none while some are still up).
    void SummonPack(char const* why)
    {
        _packDue = false;
        if (!AliveDogs().empty())
            return;
        uint32 count = 0;
        for (Point4 const& spot : kPackSpots)
            if (me->SummonCreature(NPC_SM_TRACKING_HOUND, spot.x, spot.y, spot.z, spot.o, TEMPSUMMON_MANUAL_DESPAWN))
                ++count;
        LogLk("pack", Acore::StringFormat("why={} hounds={}", why, count));
    }

    static bool IsDog(uint32 entry)
    {
        return entry == NPC_SM_TRACKING_HOUND || entry == NPC_SM_KENNEL_PUP;
    }

    // Every living dog, hounds and pups, in guid order (the whip's tie-break, and a stable order for the trail).
    std::vector<Creature*> AliveDogs()
    {
        std::vector<Creature*> out;
        for (ObjectGuid const& guid : summons)
            if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                if (IsDog(c->GetEntry()) && c->IsAlive())
                    out.push_back(c);
        std::sort(out.begin(), out.end(), [](Creature const* a, Creature const* b)
        {
            return a->GetGUID() < b->GetGUID();
        });
        return out;
    }

    uint32 AlivePups()
    {
        uint32 n = 0;
        for (Creature* dog : AliveDogs())
            n += dog->GetEntry() == NPC_SM_KENNEL_PUP ? 1u : 0u;
        return n;
    }

    // Dogs free for an order: alive, fighting (not holding, leaping, running or cowering), not crowd-controlled.
    std::vector<Creature*> FreeDogs()
    {
        std::vector<Creature*> out;
        for (Creature* dog : AliveDogs())
            if (npc_sm_loksey_dog* ai = DogAI(dog))
                if (ai->Free())
                    out.push_back(dog);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LK1 the rounds
    // ----------------------------------------------------------------------------------------------------------------

    void ScheduleRound(uint32 delayMs)
    {
        scheduler.Schedule(Ms(delayMs), GROUP_ROUND, [this](TaskContext ctx)
        {
            if (!Active())
                return;
            Round const next = NextRound(_last, _heroic);
            if (!RunRound(next))
            {
                ctx.Repeat(Ms(kRetryMs));       // he is casting: the round waits for the bar to finish
                return;
            }
            _last = next;
            ctx.Repeat(Ms(kRoundEveryMs(_heroic)));
        });
    }

    // False when the round could not start yet (a cast bar in progress); true when it ran.
    bool RunRound(Round round)
    {
        switch (round)
        {
            case Round::Release: return DoRelease();
            case Round::Mark:    return DoMark();
            case Round::Heel:    return DoHeel();
            case Round::Fetch:   return DoFetch();
        }
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LK2 Release the Hounds
    // ----------------------------------------------------------------------------------------------------------------

    // Normal: the yell, the whistle, 3 pups at once. Heroic: the yell and a 2.5 s interruptible whistle; the pups come
    // when it ends (ReleaseLanded).
    bool DoRelease()
    {
        if (!_heroic)
        {
            Talk(SAY_LOKSEY_RELEASE);
            me->CastSpell(me, SPELL_LK_WHISTLE, true);
            LogLk("round", "release");
            SummonPups(PupsToSummon(false, false, AlivePups()), "release");
            return true;
        }
        if (me->HasUnitState(UNIT_STATE_CASTING)
            || me->CastSpell(me, SPELL_LK_RELEASE_CAST, false) != SPELL_CAST_OK)
            return false;
        Talk(SAY_LOKSEY_RELEASE);
        Mechanic::NoteNextCastIn(me, SPELL_LK_RELEASE_CAST, Ms(CycleMs(true)));
        LogLk("round", Acore::StringFormat("release cast={}ms", kReleaseCastMs));
        return true;
    }

    void ReleaseLanded(bool interrupted)
    {
        SummonPups(PupsToSummon(true, interrupted, AlivePups()), interrupted ? "release-interrupted" : "release-ran");
    }

    // `count` pups from the two hall entries, in turn; each picks the tank first (rule 19), then the nearest player.
    void SummonPups(uint32 count, char const* why)
    {
        uint32 summoned = 0;
        for (uint32 i = 0; i < count; ++i)
        {
            Point3 const entry = PupEntry(_pupDoor++);
            float const facing = DungeonKit::BearingTo(entry.XY(), DungeonKit::PlaneOf(me));
            Creature* pup = me->SummonCreature(NPC_SM_KENNEL_PUP, entry.x, entry.y, entry.z, facing,
                TEMPSUMMON_MANUAL_DESPAWN);
            if (!pup)
                continue;
            ++summoned;
            if (npc_sm_loksey_dog* ai = DogAI(pup))
                ai->BoundIn(ArriveTarget(entry));
        }
        LogLk("pups", Acore::StringFormat("why={} summoned={} alive={} heroic={}", why, summoned, AlivePups(),
            _heroic ? 1 : 0));
    }

    // Where an arriving pup goes: his victim (the tank), else the nearest player of the fight (out of combat in a test:
    // the GM).
    Unit* ArriveTarget(Point3 const& from)
    {
        if (Unit* victim = me->GetVictim())
            if (victim->IsPlayer() && victim->IsAlive())
                return victim;
        if (!me->IsEngaged())
            return _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer);
        Player* nearest = nullptr;
        float best = 1.0e9f;
        if (Map* map = me->GetMap())
            for (auto const& ref : map->GetPlayers())
            {
                Player* player = ref.GetSource();
                if (!player || !player->IsAlive() || player->IsGameMaster() || !me->IsInCombatWith(player))
                    continue;
                float const d = player->GetExactDist2d(from.x, from.y);
                if (d < best)
                {
                    best = d;
                    nearest = player;
                }
            }
        return nearest;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LK3 Mark
    // ----------------------------------------------------------------------------------------------------------------

    bool DoMark()
    {
        Talk(EMOTE_LOKSEY_MARK);
        me->CastSpell(me, SPELL_LK_WHISTLE, true);
        if (AliveDogs().empty())
        {
            LogLk("mark-off", "no dog lives: nothing to leap");        // killing the pack turns the Mark off
            return true;
        }
        std::vector<Player*> const carriers = PickCarriers(kScentCarriers(_heroic));
        if (carriers.empty())
        {
            LogLk("mark-none", "nobody to scent");
            return true;
        }
        std::vector<ObjectGuid> guids;
        std::string names;
        for (Player* carrier : carriers)
        {
            me->CastSpell(carrier, SPELL_LK_SCENT, true);
            me->CastSpell(carrier, SPELL_LK_SCENT_FLASH, true);
            RegisterScentWalk(carrier);
            guids.push_back(carrier->GetGUID());
            names += (names.empty() ? "" : ",") + carrier->GetName();
        }
        scheduler.Schedule(Ms(kScentMs), GROUP_MARK, [this, guids](TaskContext /*ctx*/) { BeginTrail(guids); });
        LogLk("mark", Acore::StringFormat("carriers=[{}] scent={}ms dogs={}", names, kScentMs, AliveDogs().size()));
        return true;
    }

    // Random players of the fight, never the tank (STAGE-R-1-LIB Q1) and never the healer (F-4b); out of combat in a
    // test: the GM.
    std::vector<Player*> PickCarriers(uint32 count)
    {
        std::vector<Player*> out;
        if (!me->IsEngaged())
        {
            if (Player* gm = _testPlayer.IsEmpty() ? nullptr : ObjectAccessor::GetPlayer(*me, _testPlayer))
                out.push_back(gm);
            return out;
        }
        DungeonKit::PickRule rule;
        rule.nonTank = kScentTankExempt;
        rule.tankIfAlone = false;
        rule.nonHealer = kScentHealerExempt;
        return DungeonKit::PickPlayers(me, rule, count);
    }

    // F5: the carrier walks away from the group during the Scent. A registry Bait whose only eligible player is the
    // carrier: no hit (no damage keys), no telegraph, the bots read it as "this player keeps `kScentFarYd` from the
    // owner" and the others as nothing. The landings are the registry Circles of BeginTrail.
    void RegisterScentWalk(Player* carrier)
    {
        BossMechanics::Eligibility only;
        only.carriers.insert(carrier->GetGUID());
        MechanicRef walk = Mechanic::Bait(me, BossMechanics::BaitRule::Farthest(), kScentFarYd, Ms(kScentMs));
        walk.Eligible(only).NoTelegraph().Within(BotFloorBounds()).Tag(TAG_LK_SCENT);
        Track(walk.Handle());
    }

    // The Scent ended: one marker per free dog, 0.5 s apart on each carrier's trail, dogs split between the carriers.
    void BeginTrail(std::vector<ObjectGuid> const& carrierGuids)
    {
        if (!Active())
            return;
        std::vector<ObjectGuid> alive;
        for (ObjectGuid const& guid : carrierGuids)
            if (Player* carrier = ObjectAccessor::GetPlayer(*me, guid))
                if (carrier->IsAlive() && carrier->GetMap() == me->GetMap())
                    alive.push_back(guid);
        std::vector<Creature*> dogs = FreeDogs();
        if (dogs.empty() || alive.empty())
        {
            LogLk("trail-none", Acore::StringFormat("dogs={} carriers={}", dogs.size(), alive.size()));
            return;
        }
        uint32 const dogCount = static_cast<uint32>(dogs.size());
        uint32 const carrierCount = static_cast<uint32>(alive.size());
        Acore::Containers::RandomShuffle(dogs);
        for (TrailSlot const& slot : PlanTrail(dogCount, carrierCount))
        {
            ObjectGuid const dog = dogs[slot.dog]->GetGUID();
            ObjectGuid const carrier = alive[slot.carrier];
            scheduler.Schedule(Ms(slot.atMs), GROUP_MARK, [this, dog, carrier, alive](TaskContext /*ctx*/)
            {
                DropMarker(dog, carrier, alive);
            });
        }
        LogLk("trail", Acore::StringFormat("dogs={} carriers={} drops={}ms ends={}ms", dogCount, carrierCount,
            TrailDropMs(dogCount, carrierCount), TrailMs(dogCount, carrierCount)));
    }

    // One marker: 5 yd, 0-2 yd from the carrier in a random direction, 1.5 s warning; its dog holds and leaps onto it.
    void DropMarker(ObjectGuid dogGuid, ObjectGuid carrierGuid, std::vector<ObjectGuid> const& carriers)
    {
        if (!Active())
            return;
        npc_sm_loksey_dog* ai = DogAI(ObjectAccessor::GetCreature(*me, dogGuid));
        if (!ai || !ai->Free())
        {
            LogLk("marker-skipped", "its dog is gone or not free");     // a dead dog shortens the trail
            return;
        }
        Player* carrier = ObjectAccessor::GetPlayer(*me, carrierGuid);
        if (!carrier || !carrier->IsAlive())
        {
            carrier = nullptr;
            for (ObjectGuid const& other : carriers)
                if (Player* p = ObjectAccessor::GetPlayer(*me, other); p && p->IsAlive())
                {
                    carrier = p;
                    break;
                }
        }
        if (!carrier)
        {
            LogLk("marker-skipped", "no carrier left");
            return;
        }
        Vec2 const spotXY = MarkerSpot(DungeonKit::PlaneOf(carrier), frand(0.f, 1.f), frand(0.f, 1.f));
        float const z = GroundZ(carrier, spotXY.x, spotXY.y, carrier->GetPositionZ());
        Position spot(spotXY.x, spotXY.y, z, 0.f);
        if (!LokseyArena().Contains(spotXY, z))
            spot = Position(carrier->GetPositionX(), carrier->GetPositionY(), carrier->GetPositionZ(), 0.f);

        float const pct = kMarkLandingPct(_heroic);
        MechanicRef marker = Mechanic::Circle(me, BossMechanics::Anchor(spot), kMarkerRadiusYd, Ms(kMarkerWarnMs));
        marker.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_LK_HOUND_LEAP).Within(BotFloorBounds())
            .Tag(TAG_LK_MARK_LANDING);
        MechanicHandle const handle = marker.Handle();
        Track(handle);
        ai->HoldForLeap(spot, kMarkerWarnMs - kLeapFlightMs, kMarkerWarnMs, handle);
        LogLk("marker", Acore::StringFormat("carrier={} dog={} at=({:.1f}, {:.1f}) pct={:.0f}", carrier->GetName(),
            dogGuid.GetCounter(), spot.GetPositionX(), spot.GetPositionY(), pct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LK4 Heel
    // ----------------------------------------------------------------------------------------------------------------

    bool DoHeel()
    {
        Talk(EMOTE_LOKSEY_HEEL);
        me->CastSpell(me, SPELL_LK_WHISTLE, true);
        std::vector<Creature*> const dogs = FreeDogs();
        Vec2 const center = DungeonKit::PlaneOf(me);
        uint32 const n = static_cast<uint32>(dogs.size());
        for (uint32 i = 0; i < n; ++i)
        {
            Vec2 const at = HeelSpot(center, i, n);
            if (npc_sm_loksey_dog* ai = DogAI(dogs[i]))
                ai->Heel(Position(at.x, at.y, GroundZ(me, at.x, at.y, me->GetPositionZ()), 0.f));
        }
        scheduler.Schedule(Ms(kHeelRunMs), GROUP_HEEL, [this](TaskContext /*ctx*/) { Whip(); });
        LogLk("heel", Acore::StringFormat("running={} alive={}", n, AliveDogs().size()));
        return true;
    }

    // The dog with the most health is whipped into a frenzy; with no dog alive he whips himself.
    void Whip()
    {
        if (!Active())
            return;
        std::vector<Creature*> const dogs = AliveDogs();
        for (Creature* dog : dogs)
            if (npc_sm_loksey_dog* ai = DogAI(dog))
                ai->EndHeel();
        std::vector<uint32> health;
        for (Creature* dog : dogs)
            health.push_back(dog->GetHealth());
        int const pick = WhippedDog(health);
        if (pick < 0)
        {
            Talk(EMOTE_LOKSEY_FRENZY);
            me->CastSpell(me, SPELL_LK_LOKSEY_FRENZY, true);
            LogLk("whip", "no dog: his own frenzy");
            return;
        }
        Creature* dog = dogs[static_cast<std::size_t>(pick)];
        Frenzy(dog);
        LogLk("whip", Acore::StringFormat("dog={} entry={} health={}", dog->GetGUID().GetCounter(), dog->GetEntry(),
            dog->GetHealth()));
    }

    // Whipped Frenzy on `dog` (a stack; heroic: until it dies).
    void Frenzy(Creature* dog)
    {
        if (!dog || !dog->IsAlive())
            return;
        me->CastSpell(dog, SPELL_LK_WHIPPED_FRENZY, true);
        if (_heroic)
            if (Aura* aura = dog->GetAura(SPELL_LK_WHIPPED_FRENZY, me->GetGUID()))
            {
                aura->SetMaxDuration(-1);
                aura->SetDuration(-1);
            }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LK5 Correction
    // ----------------------------------------------------------------------------------------------------------------

    void ScheduleCorrection(uint32 delayMs)
    {
        scheduler.Schedule(Ms(delayMs), GROUP_CORRECTION, [this](TaskContext ctx)
        {
            if (!Active())
                return;
            if (!DoCorrection())
            {
                ctx.Repeat(Ms(kRetryMs));       // a cast bar is in progress
                return;
            }
            ctx.Repeat(Ms(kCorrectionEveryMs));
        });
    }

    // The 2 s cast bar, the registry cone beside it, then the tank's own hit when he stands in it.
    bool DoCorrection()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        DungeonKit::CastBar(me, SPELL_LK_CORRECTION_CAST);
        MechanicRef cone = Mechanic::Cone(me, me, kCorrectionAngleDeg, kCorrectionLengthYd, Ms(kCorrectionCastMs),
            BossMechanics::TankExempt::Yes);
        cone.Damage(kCorrectionPct(_heroic)).TankDamage(kCorrectionTankPct(_heroic)).Weakened()
            .Spell(SPELL_LK_CORRECTION_HIT).Tag(TAG_LK_CORRECTION);
        Track(cone.Handle());
        scheduler.Schedule(Ms(kCorrectionCastMs), GROUP_CORRECTION,
            [this](TaskContext /*ctx*/) { CorrectionTankHit(); });
        LogLk("correction", Acore::StringFormat("others={:.0f}% tank={:.0f}%", kCorrectionPct(_heroic),
            kCorrectionTankPct(_heroic)));
        return true;
    }

    // The cone skipped the tank (TankExempt): his target takes the heavy hit if it stands in the arc.
    void CorrectionTankHit()
    {
        if (!Active())
            return;
        Unit* tank = me->GetVictim();
        if (!tank || !tank->IsAlive())
            return;
        if (!DungeonKit::InFrontalCone(DungeonKit::PlaneOf(me), me->GetOrientation(), DungeonKit::PlaneOf(tank),
            kCorrectionAngleDeg, kCorrectionLengthYd, me->GetCombatReach() + tank->GetCombatReach()))
            return;
        me->CastSpell(tank, SPELL_LK_CORRECTION_TANK, true);
        LogLk("correction-tank", Acore::StringFormat("hit {}", tank->GetName()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LK6 Fetch (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool DoFetch()
    {
        Talk(EMOTE_LOKSEY_FETCH);
        me->CastSpell(me, SPELL_LK_WHISTLE, true);
        Position spot;
        if (!PickFetchSpot(spot))
        {
            LogLk("fetch-none", "no floor 15-25 yd from him");
            return true;
        }
        Map* map = me->GetMap();
        ObjectGuid const bossGuid = me->GetGUID();
        MechanicRef catchCircle = Mechanic::Soak(me, BossMechanics::Anchor(spot), kFetchRadiusYd, 1,
            Ms(kFetchFlightMs));
        catchCircle.Within(BotFloorBounds()).Tag(TAG_LK_FETCH);
        catchCircle.OnResolve([map, bossGuid](BossMechanics::ResolveResult const& r)
        {
            if (boss_houndmaster_loksey_rework* ai = From(map, bossGuid))
                ai->FetchLanded(r.count >= 1, r.hits.empty() ? ObjectGuid::Empty : r.hits.front());
        });
        Track(catchCircle.Handle());

        // The stick leaves so it lands as the circle resolves (look only: the registry circle owns the catch).
        float const distance = me->GetExactDist2d(spot.GetPositionX(), spot.GetPositionY());
        scheduler.Schedule(Ms(FetchLaunchDelayMs(distance)), GROUP_FETCH, [this, spot](TaskContext /*ctx*/)
        {
            me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_LK_FETCH_THROW, true);
        });
        // Every free dog breaks off and races for it.
        uint32 racing = 0;
        for (Creature* dog : FreeDogs())
            if (npc_sm_loksey_dog* ai = DogAI(dog))
            {
                ai->RaceTo(spot);
                ++racing;
            }
        LogLk("fetch", Acore::StringFormat("at=({:.1f}, {:.1f}) dist={:.1f} racing={}", spot.GetPositionX(),
            spot.GetPositionY(), distance, racing));
        return true;
    }

    // A spot 15-25 yd from him with 3 yd of floor round it (the bots' floor); a few random rings first, then the line
    // toward the hall's center at the nearest distance that fits the ring. False when the floor has none.
    bool PickFetchSpot(Position& out)
    {
        Vec2 const from = DungeonKit::PlaneOf(me);
        DungeonKit::Arena const floor = BotFloor();
        for (uint32 i = 0; i < kFetchSpotTries; ++i)
            if (TryFetchSpot(floor, from, frand(0.f, DungeonKit::kTwoPi), frand(kFetchMinYd, kFetchMaxYd), out))
                return true;
        float const toCenter = DungeonKit::BearingTo(from, kHallCenter.XY());
        float const centerDist = DungeonKit::Distance(from, kHallCenter.XY());
        float const d = std::clamp(centerDist, kFetchMinYd, kFetchMaxYd);
        return TryFetchSpot(floor, from, toCenter, d, out);
    }

    bool TryFetchSpot(DungeonKit::Arena const& floor, Vec2 from, float bearing, float distance, Position& out)
    {
        Vec2 const p = DungeonKit::Advance(from, bearing, distance);
        float const h = me->GetMapHeight(p.x, p.y, me->GetPositionZ() + 2.f);
        if (h <= INVALID_HEIGHT || std::fabs(h - me->GetPositionZ()) > kGroundBandYd)
            return false;
        if (!FetchSpotOnFloor(floor, p, h))
            return false;
        out = Position(p.x, p.y, h, 0.f);
        return true;
    }

    // The circle resolved: caught, every dog sits and cowers; missed, every living dog is whipped into a frenzy.
    void FetchLanded(bool caught, ObjectGuid catcher)
    {
        if (!Active())
            return;
        std::vector<Creature*> const dogs = AliveDogs();
        if (caught)
        {
            for (Creature* dog : dogs)
                if (npc_sm_loksey_dog* ai = DogAI(dog))
                    ai->Cower(kCowedMs);
            LogLk("fetch-caught", Acore::StringFormat("by={} cowed={}", GuidText(catcher), dogs.size()));
            return;
        }
        for (Creature* dog : dogs)
        {
            if (npc_sm_loksey_dog* ai = DogAI(dog))
                ai->EndFetch();
            Frenzy(dog);
        }
        LogLk("fetch-missed", Acore::StringFormat("frenzied={}", dogs.size()));
    }

    static std::string GuidText(ObjectGuid guid)
    {
        return guid.IsEmpty() ? std::string("none") : std::to_string(guid.GetCounter());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The descriptor, state
    // ----------------------------------------------------------------------------------------------------------------

    // Interrupt list: Release the Hounds (heroic: expected). Purge list: Whipped Frenzy on a dog and his own frenzy
    // (a reward; both Magic). Dispel list: none. Kill order: the frenzied dog, the pups, the hounds, then him; the
    // tank picks dogs up when nothing else needs it (priority -1).
    void Describe()
    {
        BossMechanics::Descriptor d;
        if (_heroic)
            d.interrupts.emplace_back(NPC_LOKSEY, SPELL_LK_RELEASE_CAST, kReleaseKickPriority, Ms(CycleMs(true)));
        d.purges.emplace_back(NPC_SM_TRACKING_HOUND, SPELL_LK_WHIPPED_FRENZY, kFrenzyPurgePriority);
        d.purges.emplace_back(NPC_SM_KENNEL_PUP, SPELL_LK_WHIPPED_FRENZY, kFrenzyPurgePriority);
        d.purges.emplace_back(NPC_LOKSEY, SPELL_LK_LOKSEY_FRENZY, kFrenzyPurgePriority);
        for (uint32 const entry : { uint32(NPC_SM_TRACKING_HOUND), uint32(NPC_SM_KENNEL_PUP) })
        {
            std::int8_t const plain = entry == NPC_SM_KENNEL_PUP ? kPupKillPriority : kHoundKillPriority;
            d.targets.push_back(BossMechanics::TargetEntry(entry, kFrenziedKillPriority, BossMechanics::Who::Dps,
                BossMechanics::Condition::HasAura(SPELL_LK_WHIPPED_FRENZY)));
            d.targets.push_back(BossMechanics::TargetEntry(entry, plain, BossMechanics::Who::Dps,
                BossMechanics::Condition::LacksAura(SPELL_LK_WHIPPED_FRENZY)).AoeOk());
            d.targets.push_back(BossMechanics::TargetEntry(entry, kTankDogPriority, BossMechanics::Who::Tank));
        }
        Mechanic::Describe(me, std::move(d));
    }

    // Anything running: the pull's fight, or a test command's mechanic out of combat.
    bool Active() const
    {
        return _fighting || !_testPlayer.IsEmpty();
    }

    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    // Nothing pending, no zone, no Scent, every aura of the fight gone (Reset, evade, death).
    void Cleanup()
    {
        scheduler.CancelAll();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _fighting = false;
        _testPlayer.Clear();
        _last = Round::Release;
        me->RemoveAurasDueToSpell(SPELL_LK_LOKSEY_FRENZY);
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_LK_SCENT);
        _arena.Reset();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm loksey` entry points
    // ----------------------------------------------------------------------------------------------------------------
public:
    // An empty string when fired; otherwise why not. `gm` stands in for the group out of combat.
    std::string TestFire(TestKind kind, Player* gm)
    {
        if (!me->IsEngaged() && gm)
            _testPlayer = gm->GetGUID();
        switch (kind)
        {
            case TestKind::Release:
                if (!DoRelease())
                    return "Busy casting; try again in a moment.";
                break;
            case TestKind::Mark:
                DoMark();
                break;
            case TestKind::Heel:
                DoHeel();
                break;
            case TestKind::Fetch:
                if (!_heroic)
                    return "Fetch is a heroic round: `.dbtest sm loksey heroic 1` first.";
                DoFetch();
                break;
            case TestKind::Correction:
                if (!DoCorrection())
                    return "Busy casting; try again in a moment.";
                break;
            case TestKind::Pack:
                SummonPack("test");
                break;
            case TestKind::Clear:
                Cleanup();
                break;
        }
        return {};
    }

    // `.dbtest sm loksey heroic <0|1>`: the heroic form on a normal map (and back) until the end of the next pull.
    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
        if (_fighting)
            Describe();
    }

    std::string TestState()
    {
        std::string dogs;
        for (Creature* dog : AliveDogs())
            if (npc_sm_loksey_dog* ai = DogAI(dog))
                dogs += Acore::StringFormat(" {}:{}:{}:{:.0f}%", dog->GetGUID().GetCounter(),
                    dog->GetEntry() == NPC_SM_KENNEL_PUP ? "pup" : "hound", ai->StateName(), dog->GetHealthPct());
        return Acore::StringFormat("loksey heroic={} fighting={} last={} pups={} live={} dogs=[{} ]", _heroic ? 1 : 0,
            _fighting ? 1 : 0, RoundName(_last), AlivePups(), _live.size(), dogs);
    }

private:
    DungeonKit::ArenaGuard _arena;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _fighting = false;
    bool _packDue = true;
    uint32 _pupDoor = 0;            // the next hall entry (alternates NE / SE)
    Round _last = Round::Release;   // the round that ran last (the pull is the first Release)
    std::vector<MechanicHandle> _live;
    ObjectGuid _testPlayer;
};

namespace
{
    boss_houndmaster_loksey_rework* LokseyAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_LOKSEY);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_houndmaster_loksey_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_houndmaster_loksey_rework* ai = LokseyAI(handler);
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

    // `.dbtest sm loksey info`
    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_LOKSEY, BOSS_LOKSEY);
    }

    // `.dbtest sm loksey state`: the round, the pups and each dog's state.
    bool HandleState(ChatHandler* handler)
    {
        boss_houndmaster_loksey_rework* ai = LokseyAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // `.dbtest sm loksey release`: LK2 now (normal: 3 pups at once; heroic: the 2.5 s whistle).
    bool HandleRelease(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Release,
            "Release the hounds: pups from the hall's entries (heroic: a 2.5 s whistle first).");
    }

    // `.dbtest sm loksey mark`: LK3 now (out of combat: the Scent is on you).
    bool HandleMark(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Mark, "Mark! The Scent is on you for 5 s, then the dogs leap onto the trail.");
    }

    // `.dbtest sm loksey heel`: LK4 now.
    bool HandleHeel(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Heel, "Heel! Every dog runs to him; the healthiest is whipped into a frenzy.");
    }

    // `.dbtest sm loksey fetch`: LK6 now (heroic only: set `heroic 1` first).
    bool HandleFetch(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Fetch, "Fetch! The stick lands in 3 s: stand in the circle to catch it.");
    }

    // `.dbtest sm loksey correction`: LK5 now.
    bool HandleCorrection(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Correction, "Correction: a 2 s cast, then the cone.");
    }

    // `.dbtest sm loksey pack`: the three hounds at his feet (when none are up).
    bool HandlePack(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Pack, "The pack: three hounds at his feet (none while some are up).");
    }

    // `.dbtest sm loksey clear`: every marker, zone and timer goes.
    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared.");
    }

    // `.dbtest sm loksey heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_houndmaster_loksey_rework* ai = LokseyAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the end of the next pull.");
        return true;
    }

    ChatCommandTable const& BossHoundmasterLokseyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,        SEC_GAMEMASTER, Console::No },
            { "release",    HandleRelease,      SEC_GAMEMASTER, Console::No },
            { "mark",       HandleMark,         SEC_GAMEMASTER, Console::No },
            { "heel",       HandleHeel,         SEC_GAMEMASTER, Console::No },
            { "fetch",      HandleFetch,        SEC_GAMEMASTER, Console::No },
            { "correction", HandleCorrection,   SEC_GAMEMASTER, Console::No },
            { "pack",       HandlePack,         SEC_GAMEMASTER, Console::No },
            { "clear",      HandleClear,        SEC_GAMEMASTER, Console::No },
            { "heroic",     HandleHeroic,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_houndmaster_loksey_rework()
{
    RegisterDungeonReworkCreatureAI(boss_houndmaster_loksey_rework, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sm_loksey_hound, ScarletMonasteryRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_sm_kennel_pup, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("loksey", BossHoundmasterLokseyTestCommands());
}
