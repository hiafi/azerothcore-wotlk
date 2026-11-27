/*
 * mod-dungeon-bosses, Gnomeregan D4: the Mobile Alert System (301110, a new boss: a copy of the stock alarm bot 7849 at
 * scale 3), section 2's teaching boss, normal and heroic; its Security Assistant (301111, a copy of 7603) and Security
 * Defender (301112, a copy of 6223); the light stalker 301113 (KT-G's TurningLights). Build spec: SP 1008-1224 (MA1 to
 * MA10, Build spec 1167), rulings 25-30, 66, 67; handoff section 3.5 row D4 (rules 1-38, the kick and dispel table:
 * nothing kickable, nothing dispellable), 3.6, 3.8 (the hall: a 125 x 32 yd diagonal band, him 22.6 yd off its
 * middle), 3.9 row 6, section 7 #15 A, #16 B, #21 A, #22 A, #36-#38 A, section 10. Bound by apps/dbc-tools
 * source/npcs/gnomeregan/mobile_alert_system.py; texts and the Defender's gun in
 * rev_mobile_alert_system_gnomeregan.sql; numbers in MobileAlertSystemLogic.h, health in GnomereganRework.h Health;
 * the lights are the LightsMachine (MobileAlertSystemMachine.{h,cpp}; the hard mode's MT23 calls the same machine).
 *
 *   Pull     he never moves or melees (rooted by SetControlled, combat movement off; no Stealth Detection, section
 *            7 #38 e). Normal: line 0. Heroic: line 4 and the Self-destruct clock.
 *   MA1      normal, first at 8 s, then every 10 s: line 1 names a random player within 30 yd on the hall (the tank
 *            included); the lock-on pillar on them; the machine's Sweep: a dim 40 degree, 30 yd cone at them for
 *            2 s, then lit, 60 degrees clockwise in 3 s; the swept floor is drawn at once (the bots' sector).
 *   MA2/MA4  heroic: two opposite 30 degree cones, dim 3 s from the pull, then always lit, 12 degrees a second; every
 *            15 to 25 s they stop 2 s (line 3) and turn the other way; +10% speed per Spotted, no cap.
 *   MA3      Spotted (a lit cone, or the cameras: in combat with him past 30 yd, section 7 #21 A; once per 3 s per
 *            player): line 2 (cameras line 8), the red beam, 20% (heroic 50%) of the reference row (the tank row on
 *            the tank) by the registry, Weakened on normal; a Response Team 3 s later; heroic: 5 s off the clock
 *            (line 6) and the lights faster (the machine).
 *   MA5      the Response Team from the door corridor, starting on its Spotted player: one Defender (normal: at most
 *            4 alive), heroic plus one Assistant.
 *   MA6      every 30 s (heroic 20 s), two Assistants from the door corridor; they take the tank (line 0 again).
 *   MA7      heroic: 120 s on a clock aura on him; line 5 at 20 s left; at zero he blows: everyone in combat with him
 *            and anyone on the hall floor dies, and he resets.
 *   MA8      every 5 s, 5% (heroic 8%) to everyone in his fight, the tank included.
 *   MA9      heroic Assistants: Net, a 3 s root on a random player in 20 yd (first 6 s, every 12 s); the net drops
 *            when its Assistant dies or is stunned (section 7 #38 f); the netting Assistant is the bots' first kill.
 *   MA10     death: line 7; the adds despawn and the lights go dark; slot 0 DONE opens the Workshop Door (the
 *            instance: section 7 #15 A); encounter credit 1107 is WP-H's DBC row.
 *
 * Every firing logs one INFO line "gnomer-build alert <mechanic> ..." (the machine's "gnomer-build alert lights-..."),
 * plus the pull line. `.dbtest gnomer alert info|state|sweep|spot|patrol|response|alarm|reverse|clock <s>`.
 *
 * Mirrored stock code (AGENTS.md credit rule): none. The stock alarm bot is SmartAI data (7849's rows, its summons of
 * 7603 and 6223 and the Defender's Shoot / Multi-Shot cadence are re-implemented from the rows' numbers).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MobileAlertSystemLogic.h"
#include "MobileAlertSystemMachine.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <memory>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerAlert;
using GnomereganMachines::SpotSource;

namespace
{
    char const* const kKey = "alert";
    uint8 constexpr kSchoolNature = 3;      // SPELL_SCHOOL_NATURE
    uint8 constexpr kSchoolArcane = 6;      // SPELL_SCHOOL_ARCANE
    float constexpr kArrivalThreat = 1000.f;    // an arriving add starts on its target; a taunt takes it

    void AlertLog(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kKey, mechanic, detail);
    }

    bool Fighting(Player const* p)
    {
        return p && p->IsInWorld() && p->IsAlive() && !p->IsGameMaster();
    }

    bool OnHallFloor(WorldObject const* o)
    {
        return HallArena().Contains({ o->GetPositionX(), o->GetPositionY() }, o->GetPositionZ());
    }

    // Player-side auras of this fight: every way out of it removes them (RB-1).
    uint32 constexpr kPlayerAuras[] = { SPELL_MA_LOCK_ON, SPELL_MA_NET };

    void StripPlayerAuras(Map* map)
    {
        if (!map)
            return;
        for (auto const& ref : map->GetPlayers())
            if (Player* p = ref.GetSource())
                for (uint32 aura : kPlayerAuras)
                    p->RemoveAurasDueToSpell(aura);
    }

    // The boss of this map's instance (for the adds' walk-in fallback).
    Creature* AlertBoss(WorldObject const* o)
    {
        InstanceScript* instance = GnomereganInstance(o);
        if (!instance)
            return nullptr;
        return ObjectAccessor::GetCreature(*o, instance->GetGuidData(kGuidBossBase + BOSS_ALERT_SYSTEM));
    }
}

// The Mobile Alert System 301110
struct boss_mobile_alert_system_rework : public BossAI
{
    enum class TestMechanic : uint8
    {
        Sweep,
        Spot,
        Patrol,
        Response,
        Alarm,
        Reverse,
    };

    explicit boss_mobile_alert_system_rework(Creature* creature)
        : BossAI(creature, BOSS_ALERT_SYSTEM), _arena(HallArena(), LeashOptions(kKey)) { }

    void Reset() override
    {
        Cleanup("reset");
        _Reset();
        _arena.Reset();
        Hold();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup("pull");
        Hold();
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _clockMs = 0;
        _searchAt = Tune::kSearchFirstMs;
        _patrolAt = Tune::kPatrolEveryMs(_heroic);
        _alarmAt = Tune::kAlarmFirstMs;
        _selfDestructLeftMs = Tune::kSelfDestructMs;
        _reassertAt = Tune::kClockReassertMs;
        _warned = false;
        _spot = me->GetPosition();

        OnBossPull(me, kKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ALERT_SYSTEM;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        StartLights();
        if (_heroic)
        {
            Talk(YELL_MA_SELF_DESTRUCT);
            ReassertClock();
        }
        else
            Talk(YELL_MA_ALARM);
        AlertLog("engage", Acore::StringFormat("heroic={} who={} spot={:.1f},{:.1f}", _heroic ? 1 : 0,
            who ? who->GetName() : "-", _spot.GetPositionX(), _spot.GetPositionY()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        AlertLog("evade", Acore::StringFormat("reason={} clock={}s spotted={}", uint32(why), _clockMs / 1000,
            _lights ? _lights->SpottedCount() : 0));
        Cleanup("evade");
        _arena.Reset();
        me->SetControlled(false, UNIT_STATE_ROOT);     // he walks nowhere, but the evade must reach home; Reset roots
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Talk(YELL_MA_CANCELED);
        AlertLog("death", Acore::StringFormat(
            "killer={} clock={}s spotted={} patrols={} responses={} pulses={} left={}s",
            killer ? killer->GetName() : "-", _clockMs / 1000, _lights ? _lights->SpottedCount() : 0, _patrols,
            _responses, _pulses, _heroic ? _selfDestructLeftMs / 1000 : 0));
        Cleanup("death");
        _arena.Reset();
        BossAI::JustDied(killer);   // slot 0 DONE: the instance opens the Workshop Door; the adds despawn
    }

    void JustSummoned(Creature* summon) override
    {
        if (!summon)
            return;
        if (summon->GetEntry() == NPC_LIGHT_STALKER)
        {
            // The machine owns its stalkers (passive, not in combat, despawned by its Clear).
            if (kUseConeDisplay)
                summon->SetDisplayId(DISPLAY_LIGHT_CONE_ID, LIGHT_CONE_SCALE);
            return;
        }
        BossAI::JustSummoned(summon);
        Mechanic::TrackUnit(me, summon);
    }

    void UpdateAI(uint32 diff) override
    {
        GnomereganRework::NoAssist(me);     // rule 29, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        _clockMs += diff;

        if (_lights)
            _lights->Update(diff);      // the judge: Spotted calls OnSpotted
        if (!me->IsAlive() || !me->IsEngaged())
            return;

        if (_heroic && UpdateClock(diff))
            return;     // he blew up and is resetting

        if (!_heroic && _clockMs >= _searchAt)
            Searchlight();
        if (_clockMs >= _patrolAt)
        {
            Patrol();
            _patrolAt = NextDue(_patrolAt, Tune::kPatrolEveryMs(_heroic), _clockMs);
        }
        if (_clockMs >= _alarmAt)
        {
            Alarm();
            _alarmAt = NextDue(_alarmAt, Tune::kAlarmEveryMs, _clockMs);
        }
        SendResponses();
        // MA10 / SP: he never melees.
    }

    // --- `.dbtest gnomer alert` --------------------------------------------------------------------------------------

    bool HeroicMap() const { return DungeonKit::IsHeroicMap(me); }

    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!_engaged || !me->IsEngaged())
            return "the Mobile Alert System is not fighting: pull him first";
        switch (mechanic)
        {
            case TestMechanic::Sweep:
                if (_heroic)
                    return "heroic has no lock-on sweep (MA2's lights are always on)";
                if (!SweepAt(who && Fighting(who) ? who : PickSearchTarget()))
                    return "the sweep was refused (one runs, or nobody to lock on)";
                return {};
            case TestMechanic::Spot:
                if (!who || !Fighting(who))
                    return "select a living player";
                if (!_lights || !_lights->Spot(who, SpotSource::Script))
                    return "refused (that player was Spotted under 3 s ago)";
                return {};
            case TestMechanic::Patrol:
                Patrol();
                return {};
            case TestMechanic::Response:
                if (!who || !Fighting(who))
                    return "select a living player";
                _pending.push_back({ _clockMs, who->GetGUID() });
                SendResponses();
                return {};
            case TestMechanic::Alarm:
                Alarm();
                return {};
            case TestMechanic::Reverse:
                if (!_heroic || !_lights)
                    return "the reversal is heroic only";
                _lights->Reverse();
                return {};
        }
        return "unknown mechanic";
    }

    std::string TestClock(uint32 seconds)
    {
        if (!_engaged || !_heroic)
            return "the Self-destruct runs on a heroic pull only";
        _selfDestructLeftMs = seconds * IN_MILLISECONDS;
        _warned = false;
        ReassertClock();
        AlertLog("clock-set", Acore::StringFormat("left={}s", seconds));
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} engaged={} next-search={}ms next-patrol={}ms next-alarm={}ms "
            "self-destruct={}s pending={} defenders={} assistants={} patrols={} responses={} pulses={} capped={} | {}",
            _clockMs / 1000, _heroic ? 1 : 0, _engaged ? 1 : 0, Until(_searchAt), Until(_patrolAt), Until(_alarmAt),
            _heroic ? _selfDestructLeftMs / 1000 : 0, _pending.size(), Alive(NPC_SECURITY_DEFENDER),
            Alive(NPC_SECURITY_ASSISTANT), _patrols, _responses, _pulses, _capped,
            _lights ? _lights->Describe() : std::string("lights off"));
    }

private:
    struct PendingResponse
    {
        uint32 dueMs = 0;
        ObjectGuid player;
    };

    // The light stalkers' look when the optional cone display is on (_visuals.py MA_CONE_LIGHT, light_cone_scale).
    static uint32 constexpr DISPLAY_LIGHT_CONE_ID = 90856;
    static float constexpr LIGHT_CONE_SCALE = 0.79f;

    uint32 Until(uint32 atMs) const { return atMs > _clockMs ? atMs - _clockMs : 0; }

    // He never moves (rule 8: a root by SetControlled; 1972 holds root immunity).
    void Hold()
    {
        me->SetCombatMovement(false);
        me->SetControlled(true, UNIT_STATE_ROOT);
    }

    // RB-1: every way out of the fight (reset, evade, death, a new pull) undoes all of it.
    void Cleanup(char const* why)
    {
        if (_lights)
        {
            _lights->Clear();
            _lights.reset();
        }
        me->RemoveAurasDueToSpell(SPELL_MA_SELF_DESTRUCT);
        StripPlayerAuras(me->GetMap());
        _pending.clear();
        if (_engaged)
            AlertLog("cleanup", why);
        _engaged = false;
        _patrols = 0;
        _responses = 0;
        _pulses = 0;
        _capped = 0;
    }

    // The bots' boss data (SP "Boss data"; FF 2.4): no interrupts, no dispels (Net is Physical, dispel none).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.targets.emplace_back(NPC_SECURITY_DEFENDER, Tune::kDefenderPriority);
        d.targets.emplace_back(NPC_SECURITY_ASSISTANT, Tune::kAssistantPriority);
        if (_heroic)
            d.targets.emplace_back(NPC_SECURITY_ASSISTANT, Tune::kNettingPriority, BossMechanics::Who::Dps,
                BossMechanics::Condition::HasAura(SPELL_MA_NETTING));
        d.rangeBands.emplace_back(Tune::kBandMinYd, Tune::kBandMaxYd);
        Mechanic::Describe(me, std::move(d));
    }

    void StartLights()
    {
        GnomereganMachines::MachineOwner owner{ me, kKey, _heroic };
        GnomereganMachines::LightsAnchor anchor;
        anchor.point = _spot;

        GnomereganMachines::LightsSpec spec;
        spec.rangeYd = Tune::kLightReachYd;
        spec.latchMs = Tune::kSpottedLatchMs;
        spec.floor = HallArena();
        if (_heroic)
        {
            spec.mode = GnomereganMachines::LightsSpec::Mode::Turning;
            spec.cones = Tune::kLightsCount;
            spec.coneDeg = Tune::kLightsConeDeg;
            spec.turnDegPerSec = Tune::kLightsDegPerSec;
            spec.speedUpPctPerSpotted = Tune::kLightsSpeedUpPct;
            spec.reverseMinMs = Tune::kReverseMinMs;
            spec.reverseMaxMs = Tune::kReverseMaxMs;
            spec.reverseStopMs = Tune::kReverseStopMs;
            spec.reverseEmoteGroup = EMOTE_MA_REVERSE;
        }
        else
        {
            spec.mode = GnomereganMachines::LightsSpec::Mode::Sweep;
            spec.cones = 1;
            spec.coneDeg = Tune::kSearchConeDeg;
            spec.sweepDeg = Tune::kSearchSweepDeg;
            spec.dimMs = Tune::kSearchDimMs;
            spec.sweepMs = Tune::kSearchSweepMs;
        }
        // Section 7 #21 A: the cameras see anyone in combat with him past the light's reach.
        ObjectGuid const self = me->GetGUID();
        Position const spot = _spot;
        spec.alsoSpotted = [self, spot](Player* p)
        {
            Creature* boss = ObjectAccessor::GetCreature(*p, self);
            if (!boss || !boss->IsAlive())
                return false;
            return CameraSees(p->GetExactDist2d(spot.GetPositionX(), spot.GetPositionY()),
                boss->GetThreatMgr().IsThreatenedBy(p));
        };

        GnomereganMachines::LightsExtras extras;
        extras.tag = LightTag(_heroic);
        extras.litAfterMs = _heroic ? Tune::kLightsDarkMs : 0;
        extras.direction = kLightsStartDirection;
        extras.startBearing = _spot.GetOrientation();
        extras.bounds = BoundsOf(FightFloorArena({ _spot.GetPositionX(), _spot.GetPositionY() }, Tune::kBotFloorYd));
        extras.alsoEveryMs = Tune::kCameraEveryMs;
        extras.onSpottedBy = [self](Player* who, SpotSource source, uint8 /*light*/)
        {
            Creature* boss = ObjectAccessor::GetCreature(*who, self);
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_mobile_alert_system_rework*>(boss->AI()))
                ai->OnSpotted(who, source);
        };

        _lights = GnomereganMachines::MakeAlertLightsMachine(owner, anchor, std::move(spec), std::move(extras));
        _lights->Start();
    }

    // The players in his fight: on his threat list, alive, no GM.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (Fighting(p) && me->GetThreatMgr().IsThreatenedBy(p))
                out.push_back(p);
        }
        return out;
    }

    // MA1: a random player within the light's reach on the hall, the tank included.
    Player* PickSearchTarget() const
    {
        std::vector<Player*> pool;
        for (Player* p : FightPlayers())
            if (p->GetExactDist2d(&_spot) <= Tune::kLightReachYd && OnHallFloor(p))
                pool.push_back(p);
        if (pool.empty())
            return nullptr;
        return pool[urand(0, uint32(pool.size()) - 1)];
    }

    bool SweepAt(Player* target)
    {
        if (!_lights || !target || !_lights->Sweep(target))
            return false;
        me->CastSpell(target, SPELL_MA_LOCK_ON, true);
        Talk(EMOTE_MA_LOCK_ON, target);
        AlertLog("searchlight", Acore::StringFormat("target={} tank={}", target->GetName(),
            me->GetVictim() == target ? 1 : 0));
        return true;
    }

    void Searchlight()
    {
        if (SweepAt(PickSearchTarget()))
            _searchAt = NextDue(_searchAt, Tune::kSearchEveryMs, _clockMs);
        else
            _searchAt = _clockMs + Tune::kSearchRetryMs;
    }

    // MA3: the machine judged a Spotted (a lit cone or the cameras) through its 3 s latch.
    void OnSpotted(Player* who, SpotSource source)
    {
        if (!_engaged || !Fighting(who))
            return;
        bool const camera = source == SpotSource::Also;
        Talk(camera ? EMOTE_MA_CAMERAS : EMOTE_MA_SPOTTED, who);
        me->CastSpell(who, SPELL_MA_SPOTTED_BEAM, true);
        DungeonKit::RegistryHitSpec hit;
        hit.pct = Tune::kSpottedPct(_heroic);
        hit.tankPct = hit.pct;      // rule 17: the tank's own row
        hit.school = kSchoolArcane;
        hit.spellId = SPELL_MA_SPOTTED;
        hit.weakened = kSpottedWeakened(_heroic);
        hit.tag = camera ? uint32(TAG_MA_CAMERAS) : LightTag(_heroic);
        DungeonKit::RegistryHit(me, GuidSet{ who->GetGUID() }, hit);
        _pending.push_back({ _clockMs + Tune::kResponseDelayMs, who->GetGUID() });
        if (_heroic)
        {
            _selfDestructLeftMs = ClockAfterSpotted(_selfDestructLeftMs);
            Talk(EMOTE_MA_SKIPS_AHEAD);
            ReassertClock();
        }
        AlertLog("spotted", Acore::StringFormat("player={} by={} pct={:.0f} weakened={} count={} left={}s",
            who->GetName(), GnomereganMachines::SpotSourceName(source), hit.pct, hit.weakened ? 1 : 0,
            _lights ? _lights->SpottedCount() : 0, _heroic ? _selfDestructLeftMs / 1000 : 0));
    }

    uint32 Alive(uint32 entry) const
    {
        uint32 n = 0;
        for (ObjectGuid const& guid : summons)
            if (Creature* c = ObjectAccessor::GetCreature(*me, guid))
                if (c->IsAlive() && c->GetEntry() == entry)
                    ++n;
        return n;
    }

    // Rule 19 (R-1-B m4): an arriving patrol takes the tank, else the nearest player to the door; never simply his
    // top threat, which is often a damage dealer. The role is asked with no owner: with him as the owner the role
    // provider calls his victim the tank, the very pick this replaces; without one it reads the talent spec (a
    // protection tree, a bear).
    Unit* TankTarget() const
    {
        std::vector<Player*> const players = FightPlayers();
        std::vector<ArrivalCandidate> candidates;
        candidates.reserve(players.size());
        for (Player* p : players)
        {
            ArrivalCandidate c;
            c.tank = BossMechanics::GetRoleProvider().Get(nullptr, p) == BossMechanics::Role::Tank;
            c.distanceYd = p->GetExactDist2d(kEntrySpot.x, kEntrySpot.y);
            candidates.push_back(c);
        }
        std::size_t const pick = PickArrival(candidates);
        return pick < players.size() ? players[pick] : nullptr;
    }

    // One add from the door corridor, the i-th of a wave of n, sent at `target`.
    Creature* SummonAdd(uint32 entry, uint32 i, uint32 n, Unit* target)
    {
        Vec2 const at = EntryPoint(i, n);
        Creature* add = me->SummonCreature(entry, at.x, at.y, kEntrySpot.z, kEntrySpot.o,
            TEMPSUMMON_CORPSE_TIMED_DESPAWN, 10000);
        if (!add)
            return nullptr;
        if (target && target->IsAlive() && add->IsAIEnabled && add->AI())
        {
            add->GetThreatMgr().AddThreat(target, kArrivalThreat);
            add->AI()->AttackStart(target);
        }
        return add;
    }

    // MA6: two Security Assistants from the door corridor, whatever the group does.
    void Patrol()
    {
        Unit* target = TankTarget();
        uint32 made = 0;
        for (uint32 i = 0; i < Tune::kPatrolSize; ++i)
            if (SummonAdd(NPC_SECURITY_ASSISTANT, i, Tune::kPatrolSize, target))
                ++made;
        ++_patrols;
        if (kAlarmYellWithPatrol)
            Talk(YELL_MA_ALARM);
        AlertLog("patrol", Acore::StringFormat("n={} made={} target={}", _patrols, made,
            target ? target->GetName() : "-"));
    }

    // MA5: each Spotted's Response Team, 3 s after it, starting on that player.
    void SendResponses()
    {
        if (_pending.empty())
            return;
        std::vector<PendingResponse> due;
        auto it = std::stable_partition(_pending.begin(), _pending.end(),
            [this](PendingResponse const& r) { return r.dueMs > _clockMs; });
        due.assign(it, _pending.end());
        _pending.erase(it, _pending.end());
        for (PendingResponse const& r : due)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, r.player);
            Unit* target = Fighting(player) ? static_cast<Unit*>(player) : TankTarget();
            uint32 const extra = ResponseAssistants(_heroic);
            uint32 const n = 1 + extra;
            bool defender = false;
            if (DefenderAllowed(_heroic, Alive(NPC_SECURITY_DEFENDER)))
                defender = SummonAdd(NPC_SECURITY_DEFENDER, 0, n, target) != nullptr;
            else
                ++_capped;
            for (uint32 i = 0; i < extra; ++i)
                SummonAdd(NPC_SECURITY_ASSISTANT, 1 + i, n, target);
            ++_responses;
            AlertLog("response", Acore::StringFormat("player={} target={} defender={} assistants={} capped={}",
                player ? player->GetName() : "-", target ? target->GetName() : "-", defender ? 1 : 0, extra,
                defender ? 0 : 1));
        }
    }

    // MA8: the siren, every player in his fight, the tank included.
    void Alarm()
    {
        GuidSet targets;
        for (Player* p : FightPlayers())
            targets.insert(p->GetGUID());
        if (targets.empty())
            return;
        DungeonKit::RegistryHitSpec hit;
        hit.pct = Tune::kAlarmPct(_heroic);
        hit.tankPct = hit.pct;
        hit.school = kSchoolNature;
        hit.spellId = SPELL_MA_ALARM;
        hit.weakened = false;
        DungeonKit::RegistryHit(me, targets, hit);
        me->CastSpell(me, SPELL_MA_ALARM_LOOK, true);
        ++_pulses;
        AlertLog("alarm", Acore::StringFormat("n={} players={} pct={:.0f}", _pulses, targets.size(), hit.pct));
    }

    // MA7: the clock aura follows the clock (rule 25: every second and on every change).
    void ReassertClock()
    {
        if (!_heroic)
            return;
        Aura* aura = me->GetAura(SPELL_MA_SELF_DESTRUCT);
        if (!aura)
            aura = me->AddAura(SPELL_MA_SELF_DESTRUCT, me);
        if (!aura)
            return;
        aura->SetMaxDuration(int32(Tune::kSelfDestructMs));
        aura->SetDuration(int32(std::max<uint32>(_selfDestructLeftMs, 1)));
    }

    // True when he blew up (the caller stops: he is resetting).
    bool UpdateClock(uint32 diff)
    {
        _selfDestructLeftMs = _selfDestructLeftMs > diff ? _selfDestructLeftMs - diff : 0;
        if (WarnNow(_selfDestructLeftMs, _warned))
        {
            _warned = true;
            Talk(YELL_MA_TWENTY);
            AlertLog("self-destruct-warning", Acore::StringFormat("left={}s", _selfDestructLeftMs / 1000));
        }
        if (_selfDestructLeftMs == 0)
        {
            Explode();
            return true;
        }
        if (_clockMs >= _reassertAt)
        {
            ReassertClock();
            _reassertAt = NextDue(_reassertAt, Tune::kClockReassertMs, _clockMs);
        }
        return false;
    }

    // MA7 at zero: everyone in combat with him and anyone on the hall floor dies (section 7 #21 A), then he resets.
    void Explode()
    {
        me->CastSpell(me, SPELL_MA_BLAST_LOOK, true);
        std::vector<ObjectGuid> doomed;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (Fighting(p) && (me->GetThreatMgr().IsThreatenedBy(p) || OnHallFloor(p)))
                doomed.push_back(p->GetGUID());
        }
        uint32 killed = 0;
        for (ObjectGuid const& guid : doomed)
        {
            Player* p = ObjectAccessor::GetPlayer(*me, guid);
            if (!p || !p->IsAlive())
                continue;
            if (Pet* pet = p->GetPet())
                if (pet->IsAlive())
                    Unit::Kill(nullptr, pet);
            Unit::Kill(nullptr, p);
            ++killed;
        }
        AlertLog("self-destruct", Acore::StringFormat("killed={} clock={}s spotted={}", killed, _clockMs / 1000,
            _lights ? _lights->SpottedCount() : 0));
        EnterEvadeMode(EVADE_REASON_OTHER);
    }

    DungeonKit::ArenaGuard _arena;
    std::unique_ptr<GnomereganMachines::AlertLightsMachine> _lights;
    std::vector<PendingResponse> _pending;
    Position _spot;
    uint32 _clockMs = 0;
    uint32 _searchAt = 0;
    uint32 _patrolAt = 0;
    uint32 _alarmAt = 0;
    uint32 _reassertAt = 0;
    uint32 _selfDestructLeftMs = Tune::kSelfDestructMs;
    uint32 _patrols = 0;
    uint32 _responses = 0;
    uint32 _pulses = 0;
    uint32 _capped = 0;
    bool _heroic = false;
    bool _engaged = false;
    bool _warned = false;
};

// The adds' shared walk in (LESSONS RB-31): a stuck add is put beside him; an add that loses its fight leaves.
struct npc_gnomer_alert_add : public ScriptedAI
{
    explicit npc_gnomer_alert_add(Creature* creature) : ScriptedAI(creature) { }

    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        me->DespawnOrUnsummon();    // nothing to walk home to: the corridor is the boss's door
    }

protected:
    void WatchWalkIn(uint32 diff)
    {
        if (diff < _checkInMs)
        {
            _checkInMs -= diff;
            return;
        }
        _checkInMs = Tune::kStuckCheckMs;
        Unit* victim = me->GetVictim();
        if (!victim || me->GetExactDist2d(victim) <= Tune::kStuckNearYd + me->GetCombatReach()
            || me->HasUnitState(UNIT_STATE_ROOT | UNIT_STATE_STUNNED) || IsHoldingRange(victim))
        {
            _stuckMs = 0;
            _last = me->GetPosition();
            return;
        }
        if (me->GetExactDist2d(&_last) < Tune::kStuckMoveYd)
            _stuckMs += Tune::kStuckCheckMs;
        else
            _stuckMs = 0;
        _last = me->GetPosition();
        if (_stuckMs < Tune::kStuckMs)
            return;
        _stuckMs = 0;
        Position to(kAlertSystemSpawn.x, kAlertSystemSpawn.y, kAlertSystemSpawn.z, kAlertSystemSpawn.o);
        if (Creature* boss = AlertBoss(me))
            to = boss->GetPosition();
        me->NearTeleportTo(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), me->GetOrientation());
        AlertLog("add-unstuck", Acore::StringFormat("entry={} target={}", me->GetEntry(), victim->GetName()));
    }

    // A ranged add standing off on purpose is not stuck.
    virtual bool IsHoldingRange(Unit* /*victim*/) const { return false; }

    bool _heroic = false;

private:
    uint32 _checkInMs = Tune::kStuckCheckMs;
    uint32 _stuckMs = 0;
    Position _last;
};

// Security Assistant 301111 (a copy of 7603): melee; heroic Net (MA9).
struct npc_gnomer_security_assistant : public npc_gnomer_alert_add
{
    explicit npc_gnomer_security_assistant(Creature* creature) : npc_gnomer_alert_add(creature) { }

    void Reset() override
    {
        _clockMs = 0;
        _netAt = Tune::kNetFirstMs;
        _stunned = false;
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _heroic = DungeonKit::IsHeroicMap(me);
        _clockMs = 0;
        _netAt = Tune::kNetFirstMs;
    }

    void JustDied(Unit* /*killer*/) override
    {
        DropNets("died");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        _clockMs += diff;
        WatchWalkIn(diff);
        if (_heroic)
        {
            // Section 7 #38 f: a stun on the Assistant frees its netted player (the reward).
            bool const stunned = me->HasUnitState(UNIT_STATE_STUNNED);
            if (stunned && !_stunned)
                DropNets("stunned");
            _stunned = stunned;
            if (!stunned && _clockMs >= _netAt && !me->HasUnitState(UNIT_STATE_CASTING))
                TryNet();
        }
        DoMeleeAttackIfReady();
    }

private:
    void TryNet()
    {
        std::vector<Player*> pool;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (Fighting(p) && me->GetThreatMgr().IsThreatenedBy(p) && me->GetExactDist(p) <= Tune::kNetRangeYd
                && me->IsWithinLOSInMap(p))
                pool.push_back(p);
        }
        if (pool.empty())
        {
            _netAt = _clockMs + Tune::kNetRetryMs;
            return;
        }
        Player* target = pool[urand(0, uint32(pool.size()) - 1)];
        if (me->CastSpell(target, SPELL_MA_NET, false) != SPELL_CAST_OK)
        {
            _netAt = _clockMs + Tune::kNetRetryMs;
            return;
        }
        me->CastSpell(me, SPELL_MA_NETTING, true);
        _netAt = NextDue(_netAt, Tune::kNetEveryMs, _clockMs);
        AlertLog("net", Acore::StringFormat("assistant={} target={}", me->GetGUID().GetCounter(), target->GetName()));
    }

    void DropNets(char const* why)
    {
        uint32 dropped = 0;
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* p = ref.GetSource())
                if (Aura* net = p->GetAura(SPELL_MA_NET, me->GetGUID()))
                {
                    net->Remove();
                    ++dropped;
                }
        me->RemoveAurasDueToSpell(SPELL_MA_NETTING);
        if (dropped)
            AlertLog("net-dropped", Acore::StringFormat("assistant={} why={} freed={}", me->GetGUID().GetCounter(), why,
                dropped));
    }

    uint32 _clockMs = 0;
    uint32 _netAt = Tune::kNetFirstMs;
    bool _stunned = false;
};

// Security Defender 301112 (a copy of 6223): ranged, the stock Shoot and Multi-Shot.
struct npc_gnomer_security_defender : public npc_gnomer_alert_add
{
    explicit npc_gnomer_security_defender(Creature* creature) : npc_gnomer_alert_add(creature) { }

    void Reset() override
    {
        _clockMs = 0;
    }

    void AttackStart(Unit* who) override
    {
        AttackStartCaster(who, Tune::kDefenderRangeYd);
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        _heroic = DungeonKit::IsHeroicMap(me);
        _clockMs = 0;
        _shootAt = urand(Tune::kShootFirstMinMs, Tune::kShootFirstMaxMs);
        _multiAt = urand(Tune::kMultiShotFirstMinMs, Tune::kMultiShotFirstMaxMs);
    }

    void UpdateAI(uint32 diff) override
    {
        if (!UpdateVictim())
            return;
        _clockMs += diff;
        WatchWalkIn(diff);
        if (!me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (_clockMs >= _multiAt)
            {
                if (DoCastVictim(kSpellStockMultiShot) == SPELL_CAST_OK)
                    _multiAt = _clockMs + urand(Tune::kMultiShotEveryMinMs, Tune::kMultiShotEveryMaxMs);
                else
                    _multiAt = _clockMs + 1000;
            }
            else if (_clockMs >= _shootAt)
            {
                if (DoCastVictim(kSpellStockShoot) == SPELL_CAST_OK)
                    _shootAt = _clockMs + urand(Tune::kShootEveryMinMs, Tune::kShootEveryMaxMs);
                else
                    _shootAt = _clockMs + 500;
            }
        }
        DoMeleeAttackIfReady();
    }

protected:
    bool IsHoldingRange(Unit* victim) const override
    {
        return me->GetExactDist2d(victim) <= Tune::kDefenderRangeYd + 2.f && me->IsWithinLOSInMap(victim);
    }

private:
    uint32 _clockMs = 0;
    uint32 _shootAt = 0;
    uint32 _multiAt = 0;
};

namespace
{
    boss_mobile_alert_system_rework* FindAlertAI(ChatHandler* handler)
    {
        Creature* boss = GnomerTest::FindBoss(handler, NPC_ALERT_SYSTEM);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_mobile_alert_system_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Mobile Alert System is not running boss_mobile_alert_system_rework.");
        return ai;
    }

    using Mech = boss_mobile_alert_system_rework::TestMechanic;

    bool Fire(ChatHandler* handler, Mech mechanic, char const* what)
    {
        boss_mobile_alert_system_rework* ai = FindAlertAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Mobile Alert System: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_ALERT_SYSTEM, BOSS_ALERT_SYSTEM);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_mobile_alert_system_rework* ai = FindAlertAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Mobile Alert System: {}", ai->TestState());
        return true;
    }

    bool HandleSweep(ChatHandler* handler)
    {
        return Fire(handler, Mech::Sweep, "a searchlight lock-on at the selected player (MA1; else a random one)");
    }

    bool HandleSpot(ChatHandler* handler)
    {
        return Fire(handler, Mech::Spot, "Spotted on the selected player (MA3, through the 3 s latch)");
    }

    bool HandlePatrol(ChatHandler* handler)
    {
        return Fire(handler, Mech::Patrol, "a patrol of two Assistants (MA6)");
    }

    bool HandleResponse(ChatHandler* handler)
    {
        return Fire(handler, Mech::Response, "a Response Team at the selected player (MA5)");
    }

    bool HandleAlarm(ChatHandler* handler)
    {
        return Fire(handler, Mech::Alarm, "one alarm pulse (MA8)");
    }

    bool HandleReverse(ChatHandler* handler)
    {
        return Fire(handler, Mech::Reverse, "a reversal of the lights (MA4)");
    }

    bool HandleClock(ChatHandler* handler, uint32 seconds)
    {
        boss_mobile_alert_system_rework* ai = FindAlertAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestClock(seconds);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Mobile Alert System: the Self-destruct clock is at {} s (MA7).", seconds);
        return true;
    }

    ChatCommandTable const& AlertTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "sweep",    HandleSweep,    SEC_GAMEMASTER, Console::No },
            { "spot",     HandleSpot,     SEC_GAMEMASTER, Console::No },
            { "patrol",   HandlePatrol,   SEC_GAMEMASTER, Console::No },
            { "response", HandleResponse, SEC_GAMEMASTER, Console::No },
            { "alarm",    HandleAlarm,    SEC_GAMEMASTER, Console::No },
            { "reverse",  HandleReverse,  SEC_GAMEMASTER, Console::No },
            { "clock",    HandleClock,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_mobile_alert_system_rework()
{
    RegisterDungeonReworkCreatureAI(boss_mobile_alert_system_rework, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_security_assistant, GnomereganRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_gnomer_security_defender, GnomereganRework::kInstanceScriptName);
    GnomerTest::RegisterBoss("alert", AlertTestCommands());
}
