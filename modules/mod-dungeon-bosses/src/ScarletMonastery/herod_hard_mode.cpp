/*
 * mod-dungeon-bosses, Scarlet Monastery D11H: Herod's hard mode, Call to Arms (heroic only). Build spec:
 * docs/dungeons/scarlet-monastery-3-armory.md "Hard mode: Call to Arms" (HM0-HM3, the Build spec rows), handoff
 * section 3.7, 3.5 row D11H, 7 #31 A. Pure rules: HerodHardModeLogic.h. It fights on D11's AI (boss_herod_rework)
 * through HerodFight.h and never edits it.
 *
 *   HM0 the trigger   a player targets Herod and uses /taunt (text emote 136, D11's ReceiveEmote routes it here, no
 *                     range check). Heroic, out of combat, flag not yet lit: the instance lights DATA_HARD_MODE_HEROD
 *                     (saved; it also sets the loot bit), he yells line 5 and takes the red aura (it holds a wipe; the
 *                     idle hook puts it back after a cold load). Anything else: line 6 "Words. Show me steel." (30 s
 *                     cooldown), no change
 *   The pull          400k (back to his heroic health on a wipe), the red aura; D11's tuning queries: spins and throws
 *                     every 28.16 s, the lap at 14 yd/s, two blades every 1.5 s, the 6 s whirl, every hit 60%
 *   HM2 at 50%        (in place of Frenzy) the prayer: he walks to the pillar 3 yd short of the pit's center, plants
 *                     Ravager at the center (the planted Ravager 300945 and its prop GO 301329), kneels in a pillar of
 *                     Light, cannot be harmed and heals to full over 20 s. Herod's Door bursts open (line 2, emote 8);
 *                     three squads of four Garrison Trainees (300944) at 0, 5 and 10 s march the section 7 #31 A line
 *                     (through the door, along the spur, a jump down into the pit, on to the pillar) at 2.5 yd/s; each
 *                     that arrives kneels, fades into the Light and gives him a stack of Zeal; the door is sealed again
 *                     at 12 s (it shuts 3 s later)
 *   The rising        at 20 s: line 7, frenzied (D11's Frenzy, no yell), the Crusader's blade in hand, the beats
 *                     restarted, no more throws (the axe is planted)
 *   HM3 the beacon    two beams round the planted axe (KT-SM TurningBeams): 30 degrees every 1.5 s, each next step
 *                     marked 1.5 s ahead, 45% Holy and Weakened, the turn flipping at every Blades of Light
 *   HM1 the hall      Consecrated Hall from his rising: every 2 s 4% of the reference row (Holy) on every player in
 *                     the hall; the floor's look on the planted axe
 *
 * Every unit comes from HerodFight::Summon (D11's cleanup despawns it), the beams' handles are the kit's (stopped in
 * OnEnd). OnEnd puts his health back (a wipe) and clears the prayer, the pillar and Zeal. Every firing logs one INFO
 * line "sm herod calltoarms-<mechanic> ..." (module.dungeonbosses); `.dbtest sm calltoarms ...` fires one on demand.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitZones.h"
#include "GameObject.h"
#include "GameTime.h"
#include "HerodFight.h"
#include "HerodHardModeLogic.h"
#include "HerodLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmCallToArms;
using SmHerod::HerodFight;
using SmHerod::HerodHit;

namespace
{
    // The planted Ravager's point id for Herod's walk to the pillar (MovePoint), the trainees' legs use their index.
    uint32 constexpr kKneelPointId = 1;

    // Create health is the base the engine rebuilds max health from (the Baron's and Ras's hard mode pattern).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    // The floor under a point; falls back to the given height.
    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + 2.f);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > 4.f) ? z : floor;
    }

    // D11's zone anchor height (boss_herod_rework.cpp kZoneAnchorZ): one shape covers the pit, the ledge and the spur.
    float constexpr kHallAnchorZ = 12.3f;

    // Where the bots plan the beams' escapes (rule 12): the whole hall, D11's HallBounds (the pit, the ledge and the
    // door spur). The beams never reach past the pit, and the spec opens the ledge between laps (R-2-ARM m-5: the pit
    // disc held every bot in the pit for the whole second half); during a lap D11's band and blades keep them down.
    BossMechanics::SpotBounds HallBounds()
    {
        std::vector<Position> spur;
        for (Vec2 const& p : SmHerod::kDoorSpur)
            spur.emplace_back(p.x, p.y, 17.f);
        return BossMechanics::SpotBounds().Circle(Position(SmHerod::kPitCenter.x, SmHerod::kPitCenter.y,
            kHallAnchorZ), SmHerod::kHallRadiusYd - 0.5f, SmHerod::kHallZMin, SmHerod::kHallZMax)
            .Polygon(std::move(spur), 14.f, SmHerod::kHallZMax);
    }

    // The hard mode's red aura on him (a wipe keeps it: AURA_STAYS_AFTER_COMBAT; the idle hook after a cold load).
    void ApplyRedAura(Creature* herod)
    {
        if (herod && herod->IsAlive() && !herod->HasAura(SPELL_CTA_AURA))
            herod->CastSpell(herod, SPELL_CTA_AURA, true);
    }

    // "Words. Show me steel." once per kWordsCooldownMs per Herod (by guid; the map keeps a handful of entries).
    std::unordered_map<ObjectGuid, uint64>& WordsReadyAt()
    {
        static std::unordered_map<ObjectGuid, uint64> readyAt;
        return readyAt;
    }

    uint64 NowMs()
    {
        return static_cast<uint64>(GameTime::GetGameTimeMS().count());
    }

    // HM0: a /taunt aimed at Herod (D11's ReceiveEmote, or the GM test). Returns what he answered.
    TauntAnswer AnswerTaunt(HerodFight& fight, Player* player, bool inCombat)
    {
        Creature* herod = fight.Herod();
        InstanceScript* instance = herod ? herod->GetInstanceScript() : nullptr;
        if (!herod || !instance || !player)
            return TauntAnswer::None;
        bool const lit = instance->GetData(DATA_HARD_MODE_HEROD) != 0;
        TauntAnswer answer = TauntAnswerFor(herod->IsAlive(), fight.Heroic(), inCombat, lit,
            static_cast<uint32>(instance->GetBossState(BOSS_HEROD)));
        if (answer == TauntAnswer::Challenge)
        {
            instance->SetData(DATA_HARD_MODE_HEROD, 1);
            if (instance->GetData(DATA_HARD_MODE_HEROD) != 0)
            {
                fight.Say(SmHerod::SAY_TAUNT_ANSWERED, player);
                ApplyRedAura(herod);
                fight.Log("calltoarms-lit", Acore::StringFormat("by={}", player->GetName()));
                return TauntAnswer::Challenge;
            }
            answer = TauntAnswer::Words;        // the instance refused it
        }
        if (answer == TauntAnswer::Words)
        {
            uint64& readyAt = WordsReadyAt()[herod->GetGUID()];
            uint64 const now = NowMs();
            bool const spoke = WordsReady(now, readyAt);
            if (spoke)
            {
                readyAt = now + kWordsCooldownMs;
                fight.Say(SmHerod::SAY_TAUNT_WORDS, player);
            }
            fight.Log("calltoarms-words", Acore::StringFormat("by={} in-combat={} heroic={} lit={} spoke={}",
                player->GetName(), inCombat ? 1 : 0, fight.Heroic() ? 1 : 0, lit ? 1 : 0, spoke ? 1 : 0));
        }
        return answer;
    }

    // Out of combat: the red aura while the flag is lit (a cold load; a respawn never keeps it).
    void IdleRedAura(HerodFight& fight)
    {
        Creature* herod = fight.Herod();
        if (!herod || herod->HasAura(SPELL_CTA_AURA) || !fight.Heroic())
            return;
        if (InstanceScript* instance = herod->GetInstanceScript())
            if (instance->GetData(DATA_HARD_MODE_HEROD) != 0)
                ApplyRedAura(herod);
    }
}

// -------------------------------------------------------------------------------------------------------------------
// Scarlet Garrison Trainee 300944 (HM2a): marches its lane's route (HerodHardModeLogic.h MarchRoute) at the drill pace,
// jumps off the landing's lip into the pit, walks on to the pillar, kneels there and fades. Never attacks, never
// chases, never evades on its own (its fight is Herod's; D11's cleanup despawns it). A stun, root, fear or knockback
// holds it (it re-aims every kReaimMs), a slow cuts its pace; one dropped into the pit before its jump walks straight
// to the pillar. The hard mode reads its arrival (ConsumeArrival).
// -------------------------------------------------------------------------------------------------------------------

struct npc_sm_garrison_trainee : public ScriptedAI
{
    explicit npc_sm_garrison_trainee(Creature* creature) : ScriptedAI(creature) { }

    void InitializeAI() override
    {
        me->SetReactState(REACT_PASSIVE);
        ScriptedAI::InitializeAI();
    }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }

    // The hard mode starts it on lane `lane` (0-3).
    void March(std::size_t lane)
    {
        std::array<MarchPoint, kRoutePoints> const route = MarchRoute(lane);
        for (std::size_t i = 0; i < kRoutePoints; ++i)
            _route[i] = Position(route[i].x, route[i].y, FloorZ(me, route[i].x, route[i].y, route[i].z), 0.f);
        _leg = 1;
        _marching = true;
        _aimMs = kReaimMs;      // the first step on the next tick
    }

    bool Arrived() const { return _arrived; }

    // True once, on the tick after it arrived (the hard mode's Zeal).
    bool ConsumeArrival()
    {
        if (!_arrived || _arrivalRead)
            return false;
        _arrivalRead = true;
        return true;
    }

    std::size_t Leg() const { return _leg; }

    void UpdateAI(uint32 diff) override
    {
        if (!_marching || !me->IsAlive())
            return;
        if (_arrived)
        {
            if (_fadeMs > diff)
                _fadeMs -= diff;
            else if (_arrivalRead)
                me->DespawnOrUnsummon();
            return;
        }
        _jumpMs += diff;
        _aimMs += diff;
        if (_aimMs < kReaimMs)
            return;
        _aimMs = 0;
        Step();
    }

private:
    void Step()
    {
        if (me->HasUnitState(UNIT_STATE_ROOT | UNIT_STATE_STUNNED | UNIT_STATE_CONFUSED | UNIT_STATE_FLEEING
            | UNIT_STATE_DISTRACTED))
            return;
        if (_jumping)
        {
            // The jump ends on the landing, or its budget runs out (then the pit rule below takes it on).
            bool const landed = me->GetExactDist2d(_route[kJumpToIndex].GetPositionX(),
                _route[kJumpToIndex].GetPositionY()) <= kLegReachYd + 1.f;
            if (!landed && _jumpMs < 3 * kJumpMs && !me->movespline->Finalized())
                return;
            _jumping = false;
            _leg = kLastIndex;
            Walk();
            return;
        }
        // A knockback (or any other forced move) in flight: let it land first.
        if (me->HasUnitState(UNIT_STATE_JUMPING) || (!me->movespline->Finalized()
            && me->GetMotionMaster()->GetCurrentMovementGeneratorType() == EFFECT_MOTION_TYPE))
            return;

        std::size_t const leg = NextLeg(_leg, me->GetPositionZ());
        if (leg != _leg)
        {
            _leg = leg;
            Walk();
            return;
        }
        Position const& to = _route[_leg];
        float const dist = me->GetExactDist2d(to.GetPositionX(), to.GetPositionY());
        if (_leg == kLastIndex && SmCallToArms::Arrived(dist))
        {
            Arrive();
            return;
        }
        if (dist <= kLegReachYd)
        {
            ++_leg;
            if (_leg == kJumpToIndex)
                Jump();
            else
                Walk();
            return;
        }
        // Keep walking (a spline cut by a stun, a root or a knockback is relaunched; a new slow sets a new pace).
        float const rate = PaceRate();
        if (me->movespline->Finalized() || std::fabs(rate - _rate) > 0.05f
            || me->GetMotionMaster()->GetCurrentMovementGeneratorType() != POINT_MOTION_TYPE)
            Walk();
    }

    // Its run speed against the template's: a slow on it cuts the march's pace.
    float PaceRate() const
    {
        float rate = 1.f;
        if (CreatureTemplate const* t = me->GetCreatureTemplate())
            if (t->speed_run > 0.f)
                rate = std::clamp(me->GetSpeedRate(MOVE_RUN) / t->speed_run, 0.1f, 1.5f);
        return rate;
    }

    // A straight line to the leg's point (section 7 #31 A: scripted, no path).
    void Walk()
    {
        _rate = PaceRate();
        Position const& to = _route[_leg];
        me->GetMotionMaster()->MovePoint(static_cast<uint32>(_leg), to.GetPositionX(), to.GetPositionY(),
            to.GetPositionZ(), FORCED_MOVEMENT_WALK, kMarchPaceYd * _rate, 0.f, false, true);
    }

    void Jump()
    {
        Position const& to = _route[kJumpToIndex];
        me->GetMotionMaster()->MoveJump(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), kJumpSpeedXY,
            kJumpSpeedZ, static_cast<uint32>(kJumpToIndex));
        _jumping = true;
        _jumpMs = 0;
    }

    // At the pillar: it kneels and fades into the Light (gone kFadeMs later), out of the fight.
    void Arrive()
    {
        _arrived = true;
        _fadeMs = kFadeMs;
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->SetFacingTo(kKneelFacing);
        me->SetStandState(UNIT_STAND_STATE_KNEEL);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetImmuneToAll(true);
        me->CastSpell(me, SPELL_CTA_FADE, true);
    }

    std::array<Position, kRoutePoints> _route{};
    std::size_t _leg = 1;
    uint32 _aimMs = 0;
    uint32 _jumpMs = 0;
    uint32 _fadeMs = 0;
    float _rate = 1.f;
    bool _marching = false;
    bool _jumping = false;
    bool _arrived = false;
    bool _arrivalRead = false;
};

// -------------------------------------------------------------------------------------------------------------------
// The hard mode for one pull (HerodFight.h HerodHardMode)
// -------------------------------------------------------------------------------------------------------------------

class CallToArmsFight : public SmHerod::HerodHardMode
{
public:
    CallToArmsFight() : _pitArena(SmHerod::PitArena()) { }

    void OnEngage(HerodFight& fight) override
    {
        Creature* herod = fight.Herod();
        _baseCreateHealth = herod->GetCreateHealth();
        SetCreatureHealth(herod, kHerodHealth);
        ApplyRedAura(herod);
        fight.Log("calltoarms-engage", Acore::StringFormat("health={} base-create={} spins={}ms lap={:.1f}yd/s "
            "blades={}ms x{} throws={}ms whirl={}ms hits={:.0f}% threshold={:.0f}%", herod->GetMaxHealth(),
            _baseCreateHealth, kSpinEveryMs, kLapSpeedYd, kBlades.everyMs, kBlades.count, kThrowEveryMs, kWhirlMs,
            kHitPct, kThresholdPct));
    }

    std::optional<float> ThresholdPct(HerodFight const& /*fight*/) const override { return kThresholdPct; }

    void OnThreshold(HerodFight& fight) override
    {
        StartPrayer(fight);
    }

    void OnUpdate(HerodFight& fight, uint32 diff) override
    {
        UpdateGarrison(fight);
        if (_half == Half::Prayer)
            UpdatePrayer(fight);
        else if (_half == Half::Second)
            UpdateSecondHalf(fight, diff);
    }

    // HM2: he cannot be harmed while he prays (the prayer's school immunity; anything that still lands is zeroed).
    void OnDamageTaken(HerodFight& /*fight*/, Unit* /*attacker*/, uint32& damage) override
    {
        if (_half == Half::Prayer)
            damage = 0;
    }

    // HM3: the beams' turn flips at every Blades of Light of the second half.
    void OnSpinStart(HerodFight& /*fight*/, uint32 /*index*/, bool /*clockwise*/) override
    {
        if (BeamsFlipOnSpin(_half))
            _beams.Flip();
    }

    void OnSummonDied(HerodFight& fight, Creature* summon, Unit* killer) override
    {
        if (!summon || summon->GetEntry() != NPC_SM_GARRISON_TRAINEE)
            return;
        ++_killed;
        fight.Log("calltoarms-trainee-killed", Acore::StringFormat("killed={} arrived={} by={}", _killed, _arrived,
            killer ? killer->GetName() : "none"));
    }

    // The bots: the garrison ahead of Herod for every role, AoE welcome; Herod ignored while he prays (unharmable);
    // the planted axe never a target.
    void ConfigureDescriptor(HerodFight& /*fight*/, BossMechanics::Descriptor& d) override
    {
        using BossMechanics::Condition;
        using BossMechanics::TargetEntry;
        using BossMechanics::Who;
        d.targets.push_back(TargetEntry(NPC_SM_GARRISON_TRAINEE, kGarrisonPriority, Who::Any).AoeOk());
        d.ignores.emplace_back(NPC_HEROD, Condition::HasAura(SPELL_CTA_PRAYER));
        d.ignores.emplace_back(NPC_SM_PLANTED_RAVAGER);
    }

    // Death, evade or reset: the beams stopped, the prayer, the pillar and Zeal off, his heroic health back (not on the
    // death), the prop gone. The units (garrison, planted axe, beam ends) are D11's cleanup (HerodFight::Summon).
    void OnEnd(HerodFight& fight, bool died) override
    {
        Creature* herod = fight.Herod();
        _beams.Stop(herod);
        for (uint32 const spell : { uint32(SPELL_CTA_PRAYER), uint32(SPELL_CTA_PILLAR), uint32(SPELL_CTA_ZEAL) })
            herod->RemoveAurasDueToSpell(spell);
        if (herod->IsAlive())
        {
            herod->SetStandState(UNIT_STAND_STATE_STAND);
            if (!died && _baseCreateHealth)
                SetCreatureHealth(herod, _baseCreateHealth);
        }
        if (GameObject* prop = _axeProp ? ObjectAccessor::GetGameObject(*herod, _axeProp) : nullptr)
            prop->DespawnOrUnsummon();
        fight.Log("calltoarms-end", Acore::StringFormat("died={} half={} squads={} arrived={} killed={} zeal={} "
            "hall-ticks={} beam-steps={}", died ? 1 : 0, HalfName(), _squadsSent, _arrived, _killed,
            DungeonKit::Stacks(herod, SPELL_CTA_ZEAL), _hallTicks, _beams.Clock().Steps()));
        _half = Half::First;
        _garrison.clear();
        _axe.Clear();
        _axeProp.Clear();
    }

    // ---- tuning (D11's heroic values, harder; HerodHardModeLogic.h) ----
    std::optional<uint32> SpinEveryMs(HerodFight const& /*fight*/) const override { return kSpinEveryMs; }
    std::optional<float> LapSpeedYd(HerodFight const& /*fight*/) const override { return kLapSpeedYd; }
    std::optional<SmHerod::BladePlan> Blades(HerodFight const& /*fight*/) const override { return kBlades; }
    std::optional<uint32> ThrowEveryMs(HerodFight const& /*fight*/) const override { return kThrowEveryMs; }
    std::optional<uint32> WhirlMs(HerodFight const& /*fight*/) const override { return kWhirlMs; }
    bool ThrowAllowed(HerodFight const& /*fight*/) const override { return ThrowsAllowed(_half); }
    std::optional<float> HitPct(HerodFight const& /*fight*/, HerodHit /*hit*/) const override { return kHitPct; }

    // ---- `.dbtest sm calltoarms` entry points ----
    std::string TestPrayer(HerodFight& fight)
    {
        if (_half != Half::First)
            return "The prayer ran already this pull.";
        if (fight.Spinning() || fight.AxeOut())
            return "He is spinning or his axe is out: try again when he is home with Ravager in hand.";
        StartPrayer(fight);
        return {};
    }

    std::string TestSquad(HerodFight& fight)
    {
        SendSquad(fight, _squadsSent < kSquadCount ? _squadsSent : kSquadCount - 1, true);
        return {};
    }

    void TestZeal(HerodFight& fight)
    {
        AddZeal(fight, "gm");
    }

    std::string TestBeams(HerodFight& fight)
    {
        if (_beams.Active())
            return "The beams are already turning.";
        PlantAxe(fight);
        StartBeams(fight);
        return _beams.Active() ? std::string() : std::string("The beams did not start (see the log).");
    }

    void TestHall(HerodFight& fight)
    {
        PlantAxe(fight);
        if (!_hallOn)
            StartHall(fight);
        HallTick(fight);
    }

    std::string State(HerodFight& fight) const
    {
        Creature* herod = fight.Herod();
        uint32 marching = 0;
        for (ObjectGuid const& guid : _garrison)
            if (Creature* trainee = ObjectAccessor::GetCreature(*herod, guid))
                if (trainee->IsAlive())
                    ++marching;
        uint64 const prayerMs = _half == Half::Prayer ? fight.FightMs() - _prayerStartMs : 0;
        return Acore::StringFormat("half={} health={}/{} prayer={}ms kneeled={} squads={} marching={} arrived={} "
            "killed={} zeal={} door={} beams={} (steps {}, dir {}) hall={} (ticks {}) axe={}", HalfName(),
            herod->GetHealth(), herod->GetMaxHealth(), prayerMs, _kneeled ? 1 : 0, _squadsSent, marching, _arrived,
            _killed, DungeonKit::Stacks(herod, SPELL_CTA_ZEAL), fight.DoorSealed() ? "sealed" : "open",
            _beams.Active() ? "on" : "off", _beams.Clock().Steps(), _beams.Clock().Direction(), _hallOn ? "on" : "off",
            _hallTicks, _axe ? "planted" : "none");
    }

private:
    char const* HalfName() const
    {
        switch (_half)
        {
            case Half::First:   return "first";
            case Half::Prayer:  return "prayer";
            case Half::Second:  return "second";
        }
        return "?";
    }

    // HM2: the prayer begins (D11 calls OnThreshold once he is home with Ravager in hand, at 50%).
    void StartPrayer(HerodFight& fight)
    {
        Creature* herod = fight.Herod();
        _half = Half::Prayer;
        _prayerStartMs = fight.FightMs();
        _prayerStartHealth = herod->GetHealth();
        _nextPrayerTickMs = _prayerStartMs + kPrayerTickMs;
        _kneeled = false;
        _resealed = false;
        fight.HoldKit(true, "prayer");
        herod->CastSpell(herod, SPELL_CTA_PRAYER, true);
        fight.Say(SmHerod::SAY_STRENGTH);
        fight.Say(SmHerod::EMOTE_GARRISON);
        fight.OpenDoor("garrison");
        float const z = FloorZ(herod, kKneelSpot.x, kKneelSpot.y, kKneelSpot.z);
        herod->GetMotionMaster()->MovePoint(kKneelPointId, kKneelSpot.x, kKneelSpot.y, z);
        fight.Log("calltoarms-prayer", Acore::StringFormat("health={:.0f}% ({}) heal-to={} over={}ms squads={} x{} "
            "every={}ms", herod->GetHealthPct(), _prayerStartHealth, herod->GetMaxHealth(), kPrayerMs, kSquadCount,
            kSquadSize, kSquadEveryMs));
    }

    void UpdatePrayer(HerodFight& fight)
    {
        Creature* herod = fight.Herod();
        uint64 const elapsed = fight.FightMs() - _prayerStartMs;
        if (!_kneeled && (herod->GetExactDist2d(kKneelSpot.x, kKneelSpot.y) <= kKneelReachYd
            || elapsed >= kKneelWalkMaxMs))
            Kneel(fight);
        while (_squadsSent < SquadsDue(elapsed))
            SendSquad(fight, _squadsSent, false);
        if (!_resealed && elapsed >= kResealAtMs)
        {
            _resealed = true;
            fight.SealDoor("garrison passed");
        }
        if (fight.FightMs() >= _nextPrayerTickMs)
        {
            _nextPrayerTickMs += kPrayerTickMs;
            herod->SetHealth(PrayerHealth(_prayerStartHealth, herod->GetMaxHealth(), elapsed));
        }
        if (elapsed >= kPrayerMs)
            Rise(fight);
    }

    // He kneels on the pillar facing the planted axe (placed there if his walk did not get him there).
    void Kneel(HerodFight& fight)
    {
        Creature* herod = fight.Herod();
        _kneeled = true;
        float const z = FloorZ(herod, kKneelSpot.x, kKneelSpot.y, kKneelSpot.z);
        bool const placed = herod->GetExactDist2d(kKneelSpot.x, kKneelSpot.y) > kKneelReachYd;
        herod->StopMoving();
        herod->GetMotionMaster()->Clear();
        if (placed)
            herod->NearTeleportTo(kKneelSpot.x, kKneelSpot.y, z, kKneelFacing);
        herod->SetFacingTo(kKneelFacing);
        herod->SetStandState(UNIT_STAND_STATE_KNEEL);
        herod->CastSpell(herod, SPELL_CTA_PILLAR, true);
        PlantAxe(fight);
        fight.Log("calltoarms-kneel", Acore::StringFormat("placed={} health={:.0f}%", placed ? 1 : 0,
            herod->GetHealthPct()));
    }

    // Ravager into the floor at the pit's center: his hand empty, the planted Ravager (300945, the beams' anchor and
    // the hall's look) and the stuck-axe prop (GO 301329, owned by the planted Ravager: it goes with it).
    void PlantAxe(HerodFight& fight)
    {
        if (_axe)
            return;
        Creature* herod = fight.Herod();
        herod->SetVirtualItem(0, 0);
        float const z = FloorZ(herod, kAxeSpot.x, kAxeSpot.y, kAxeSpot.z);
        _axeSpot = Position(kAxeSpot.x, kAxeSpot.y, z, 0.f);
        Creature* axe = fight.Summon(NPC_SM_PLANTED_RAVAGER, _axeSpot);
        if (!axe)
        {
            fight.Log("calltoarms-axe-refused", "the planted Ravager 300945 could not be summoned");
            return;
        }
        _axe = axe->GetGUID();
        if (GameObject* prop = axe->SummonGameObject(GO_SM_PLANTED_AXE, _axeSpot.GetPositionX(),
            _axeSpot.GetPositionY(), _axeSpot.GetPositionZ(), 0.f, 0.f, 0.f, 0.f, 1.f, 0))
            _axeProp = prop->GetGUID();
        fight.Log("calltoarms-axe", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) prop={}", _axeSpot.GetPositionX(),
            _axeSpot.GetPositionY(), _axeSpot.GetPositionZ(), _axeProp ? 1 : 0));
    }

    // HM2a: one squad of four through the door, each on its lane.
    void SendSquad(HerodFight& fight, uint32 squad, bool test)
    {
        Creature* herod = fight.Herod();
        uint32 sent = 0;
        for (std::size_t lane = 0; lane < kSquadSize; ++lane)
        {
            MarchPoint const start = MarchRoute(lane)[0];
            Position const at(start.x, start.y, FloorZ(herod, start.x, start.y, start.z), kGarrisonFacing);
            Creature* trainee = fight.Summon(NPC_SM_GARRISON_TRAINEE, at, kMarchLifeMs);
            if (!trainee)
                continue;
            trainee->SetVirtualItem(0, kItemTraineeMace);
            fight.JoinFight(trainee);
            if (auto* ai = trainee->IsAIEnabled ? dynamic_cast<npc_sm_garrison_trainee*>(trainee->AI()) : nullptr)
                ai->March(lane);
            _garrison.push_back(trainee->GetGUID());
            ++sent;
        }
        if (!test)
            ++_squadsSent;
        fight.Log("calltoarms-squad", Acore::StringFormat("squad={} sent={} of {} march={}ms test={}", squad + 1, sent,
            kSquadSize, MarchMs(), test ? 1 : 0));
    }

    // A trainee that reached the pillar: one stack of Zeal. The dead and the gone leave the list.
    void UpdateGarrison(HerodFight& fight)
    {
        if (_garrison.empty())
            return;
        Creature* herod = fight.Herod();
        for (auto it = _garrison.begin(); it != _garrison.end();)
        {
            Creature* trainee = ObjectAccessor::GetCreature(*herod, *it);
            if (!trainee || !trainee->IsAlive())
            {
                it = _garrison.erase(it);
                continue;
            }
            auto* ai = trainee->IsAIEnabled ? dynamic_cast<npc_sm_garrison_trainee*>(trainee->AI()) : nullptr;
            if (ai && ai->ConsumeArrival())
            {
                ++_arrived;
                AddZeal(fight, "arrival");
                it = _garrison.erase(it);
                continue;
            }
            ++it;
        }
    }

    void AddZeal(HerodFight& fight, char const* why)
    {
        Creature* herod = fight.Herod();
        uint32 const stacks = DungeonKit::AddStacks(herod, SPELL_CTA_ZEAL, 1, herod, kZealMax);
        fight.Log("calltoarms-zeal", Acore::StringFormat("why={} stacks={} arrived={} killed={} melee-load={:.2f}x",
            why, stacks, _arrived, _killed, MeleeLoad(stacks, true)));
    }

    // The rising: the second half begins.
    void Rise(HerodFight& fight)
    {
        Creature* herod = fight.Herod();
        if (!_kneeled)
            Kneel(fight);
        _half = Half::Second;
        herod->RemoveAurasDueToSpell(SPELL_CTA_PRAYER);
        herod->RemoveAurasDueToSpell(SPELL_CTA_PILLAR);
        herod->SetStandState(UNIT_STAND_STATE_STAND);
        herod->SetHealth(herod->GetMaxHealth());
        fight.SetWeapon(kItemCrusaderBlade, "rising");
        fight.Frenzy("rising", false);
        fight.Say(SmHerod::SAY_RISING);
        StartHall(fight);
        StartBeams(fight);
        fight.RestartBeats(kSpinAfterRisingMs, kThrowAfterRisingMs);
        fight.HoldKit(false, "rising");
        fight.Log("calltoarms-rising", Acore::StringFormat("health={} zeal={} arrived={} killed={} still-marching={}",
            herod->GetHealth(), DungeonKit::Stacks(herod, SPELL_CTA_ZEAL), _arrived, _killed, _garrison.size()));
    }

    // HM3: two beams round the planted axe, clipped at the pit's edge, a random start and turn.
    void StartBeams(HerodFight& fight)
    {
        Creature* herod = fight.Herod();
        DungeonKit::TurningBeamsSpec spec;
        spec.anchor = _axe ? _axeSpot : Position(kAxeSpot.x, kAxeSpot.y, kAxeSpot.z, 0.f);
        spec.count = kBeamCount;
        spec.startBearing = frand(0.f, 2.f * DungeonKit::kPi);
        spec.stepDeg = kBeamStepDeg;
        spec.stepMs = kBeamStepMs;
        spec.direction = urand(0, 1) ? 1 : -1;
        spec.innerYd = kBeamInnerYd;
        spec.lengthYd = kBeamLengthYd;
        spec.clip = &_pitArena;
        spec.inset = kBeamInsetYd;
        spec.widthYd = kBeamWidthYd;
        spec.pct = kBeamPct;
        spec.tankPct = kBeamPct;
        spec.school = SPELL_SCHOOL_HOLY;
        spec.spellId = SPELL_CTA_BEAM;
        spec.weakened = true;
        spec.tag = TAG_HM_BEAM;
        spec.endEntry = sObjectMgr->GetCreatureTemplate(NPC_SM_STALKER_WAVE2) ? uint32(NPC_SM_STALKER_WAVE2) : 0u;
        spec.beamSpell = SPELL_CTA_BEAM_LOOK;
        spec.beamSource = _axe;
        spec.configure = [](BossMechanics::MechanicRef& ref) { ref.Within(HallBounds()); };
        spec.dungeon = kLogDungeon;
        spec.boss = "herod";
        spec.name = "calltoarms-beacon";
        bool const started = _beams.Start(herod, std::move(spec));
        if (!started)
            fight.Log("calltoarms-beacon-refused");
    }

    // HM1: the floor's look on the planted axe, the first tick one interval after the rising.
    void StartHall(HerodFight& fight)
    {
        _hallOn = true;
        _nextHallMs = fight.FightMs() + kHallTickMs;
        _nextGlowMs = fight.FightMs();
        if (Creature* axe = _axe ? ObjectAccessor::GetCreature(*fight.Herod(), _axe) : nullptr)
            axe->CastSpell(axe, SPELL_CTA_HALL_LOOK, true);
        fight.Log("calltoarms-hall", Acore::StringFormat("every={}ms pct={} hundredths a tick", kHallTickMs,
            kHallHundredths));
    }

    // Every player of the fight inside the hall (the pit, the ledge, the door spur).
    void HallTick(HerodFight& fight)
    {
        Creature* herod = fight.Herod();
        DungeonKit::Arena const hall = HerodArena();
        uint32 hit = 0;
        for (Player* player : fight.FightPlayers())
            if (hall.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
            {
                herod->CastSpell(player, SPELL_CTA_HALL, true);
                ++hit;
            }
        ++_hallTicks;
        if (_hallTicks == 1 || _hallTicks % 15 == 0)
            fight.Log("calltoarms-hall-tick", Acore::StringFormat("ticks={} hit={}", _hallTicks, hit));
    }

    void UpdateSecondHalf(HerodFight& fight, uint32 diff)
    {
        Creature* herod = fight.Herod();
        _beams.Update(herod, diff);
        uint64 const now = fight.FightMs();
        if (_hallOn && now >= _nextHallMs)
        {
            _nextHallMs += kHallTickMs;
            HallTick(fight);
        }
        if (now >= _nextGlowMs)
        {
            _nextGlowMs = now + kGlowEveryMs;
            if (Creature* axe = _axe ? ObjectAccessor::GetCreature(*herod, _axe) : nullptr)
                axe->CastSpell(axe, SPELL_CTA_GLOW, true);
        }
    }

    DungeonKit::Arena _pitArena;
    DungeonKit::TurningBeams _beams;
    std::vector<ObjectGuid> _garrison;
    ObjectGuid _axe;
    ObjectGuid _axeProp;
    Position _axeSpot;
    Half _half = Half::First;
    uint64 _prayerStartMs = 0;
    uint64 _nextPrayerTickMs = 0;
    uint64 _nextHallMs = 0;
    uint64 _nextGlowMs = 0;
    uint32 _baseCreateHealth = 0;
    uint32 _prayerStartHealth = 0;
    uint32 _squadsSent = 0;
    uint32 _arrived = 0;
    uint32 _killed = 0;
    uint32 _hallTicks = 0;
    bool _kneeled = false;
    bool _resealed = false;
    bool _hallOn = false;
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest sm calltoarms`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    // Herod's AI as the hard mode sees it (an error and nullptr when he is not running D11's AI).
    HerodFight* FindFight(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_HEROD);
        if (!boss)
            return nullptr;
        auto* fight = boss->IsAIEnabled ? dynamic_cast<HerodFight*>(boss->AI()) : nullptr;
        if (!fight)
            handler->SendErrorMessage("{}", "Herod is not running boss_herod_rework (check the ScriptName; wave 2 "
                "binds it).");
        return fight;
    }

    // The running pull's hard mode (an error and nullptr when there is none).
    CallToArmsFight* FindCallToArms(ChatHandler* handler, HerodFight*& fight)
    {
        fight = FindFight(handler);
        if (!fight)
            return nullptr;
        auto* hardMode = dynamic_cast<CallToArmsFight*>(fight->ActiveHardMode());
        if (!hardMode)
            handler->SendErrorMessage("{}", "No Call to Arms pull is running (heroic: /taunt Herod or "
                "`.dbtest sm herod hardmode`, then pull him).");
        return hardMode;
    }

    bool Reply(ChatHandler* handler, std::string const& error, char const* done)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("{}", done);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowHardModeInfo(handler, "calltoarms", DATA_HARD_MODE_HEROD, BOSS_CALL_TO_ARMS);
    }

    bool HandleState(ChatHandler* handler)
    {
        InstanceScript* instance = SmTest::GmInstance(handler);
        if (!instance)
            return false;
        handler->PSendSysMessage("calltoarms: lit={} herod={} kill-slot={}", instance->GetData(DATA_HARD_MODE_HEROD),
            uint32(instance->GetBossState(BOSS_HEROD)), uint32(instance->GetBossState(BOSS_CALL_TO_ARMS)));
        Creature* boss = SmTest::FindBoss(handler, NPC_HEROD);
        auto* fight = boss && boss->IsAIEnabled ? dynamic_cast<HerodFight*>(boss->AI()) : nullptr;
        auto* hardMode = fight ? dynamic_cast<CallToArmsFight*>(fight->ActiveHardMode()) : nullptr;
        handler->PSendSysMessage("calltoarms pull: {}", hardMode ? hardMode->State(*fight) : std::string("none"));
        return true;
    }

    // `.dbtest sm calltoarms taunt`: the GM's /taunt at Herod (the same judgement and answer as the emote's).
    bool HandleTaunt(ChatHandler* handler)
    {
        Player* gm = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        HerodFight* fight = gm ? FindFight(handler) : nullptr;
        if (!fight)
            return false;
        TauntAnswer const answer = AnswerTaunt(*fight, gm, fight->Herod()->IsEngaged());
        handler->PSendSysMessage("calltoarms: taunt answered with {}", answer == TauntAnswer::Challenge
            ? "the challenge (line 5, the red aura, the flag lit)" : answer == TauntAnswer::Words
            ? "words (line 6, no change)" : "nothing");
        return true;
    }

    bool HandlePrayer(ChatHandler* handler)
    {
        HerodFight* fight = nullptr;
        CallToArmsFight* hardMode = FindCallToArms(handler, fight);
        return hardMode && Reply(handler, hardMode->TestPrayer(*fight),
            "calltoarms: the prayer now (HM2: kneel, unharmable, heal to full over 20 s, the garrison marches).");
    }

    bool HandleSquad(ChatHandler* handler)
    {
        HerodFight* fight = nullptr;
        CallToArmsFight* hardMode = FindCallToArms(handler, fight);
        return hardMode && Reply(handler, hardMode->TestSquad(*fight),
            "calltoarms: a squad of four Garrison Trainees through the door (HM2a; open the door to watch).");
    }

    bool HandleZeal(ChatHandler* handler)
    {
        HerodFight* fight = nullptr;
        CallToArmsFight* hardMode = FindCallToArms(handler, fight);
        if (!hardMode)
            return false;
        hardMode->TestZeal(*fight);
        handler->PSendSysMessage("{}", "calltoarms: one stack of Zeal on Herod (HM2b).");
        return true;
    }

    bool HandleBeams(ChatHandler* handler)
    {
        HerodFight* fight = nullptr;
        CallToArmsFight* hardMode = FindCallToArms(handler, fight);
        return hardMode && Reply(handler, hardMode->TestBeams(*fight),
            "calltoarms: Ravager's Beacon (HM3: two beams round the planted axe, 30 degrees every 1.5 s).");
    }

    bool HandleHall(ChatHandler* handler)
    {
        HerodFight* fight = nullptr;
        CallToArmsFight* hardMode = FindCallToArms(handler, fight);
        if (!hardMode)
            return false;
        hardMode->TestHall(*fight);
        handler->PSendSysMessage("{}", "calltoarms: Consecrated Hall on (HM1: 4% every 2 s) and one tick now.");
        return true;
    }

    ChatCommandTable const& CallToArmsTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "taunt",  HandleTaunt,  SEC_GAMEMASTER, Console::No },
            { "prayer", HandlePrayer, SEC_GAMEMASTER, Console::No },
            { "squad",  HandleSquad,  SEC_GAMEMASTER, Console::No },
            { "zeal",   HandleZeal,   SEC_GAMEMASTER, Console::No },
            { "beams",  HandleBeams,  SEC_GAMEMASTER, Console::No },
            { "hall",   HandleHall,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_sm_herod_hard_mode()
{
    // The hooks are D11's statics: harmless while wave 2 is unbound (D11's AI does not run then).
    SmHerod::RegisterHerodHardMode([](Creature* /*herod*/) { return std::make_unique<CallToArmsFight>(); });
    SmHerod::RegisterHerodTauntHandler([](HerodFight& fight, Player* player, bool inCombat)
    {
        AnswerTaunt(fight, player, inCombat);
    });
    SmHerod::RegisterHerodIdleHook([](HerodFight& fight) { IdleRedAura(fight); });
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(npc_sm_garrison_trainee, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("calltoarms", CallToArmsTestCommands());
}
