/*
 * mod-dungeon-bosses, Scarlet Monastery D11: Herod (3975), "Blades of Light", the Armory's end boss. Build spec:
 * docs/dungeons/scarlet-monastery-3-armory.md "Herod" (HB0-HB5, Heroic, Build spec), handoff section 3.5 row D11, 3.6,
 * 3.8 (the hall, NAVMESH), 7 #22 A (the seal), 7 #31 A (the lap drilled by G2's herod-lap row). Replaces his stock
 * SmartAI (rows 0-9, dropped by W2-SETUP's rev): Cleave 15496, Whirlwind 8989 (its tick 15578 and its magic immunity)
 * and Frenzy 8269 are gone as his casts, reworked as below; the aggro and kill lines, summon group 1 on his death
 * (row 8) and the closest trainee's line (row 9) are re-implemented here; the trainees keep their own SmartAI ("Set In
 * Combat With Zone"). Pure rules: HerodLogic.h. The hard mode (Call to Arms, D11H) fights on this AI through
 * HerodFight.h; this file never needs an edit for it. Wave 2: the AI registers only once kWave2Bound flips
 * (W2-SETUP); `.dbtest sm herod` registers now.
 *
 *   HB0 Herod's Door      3 s after the pull the door (GO 101854) shuts and every living group member outside the
 *                         hall, in the Armory, within 60 yd of the spot inside the door is moved in (KT-SM SealedArena,
 *                         section 7 #22 A); it opens on his death, a wipe or an evade (the instance makes the Lever
 *                         unselectable while he fights and opens the door on his death too)
 *   HB1 Blades of Light   15 s, then every 30 s (heroic 32 s): he yells and becomes a cyclone (a 5 yd spin). The whole
 *                         ledge band is marked from the yell (everyone goes down into the pit); the out lane (10 yd,
 *                         2.5 s) to a random point of the ledge, which he dashes; one lap of the ledge in a random
 *                         direction at 10 yd/s (heroic 12), hitting once anyone his spin passes; blades of light from
 *                         him across the pit toward random players (4 yd lanes, 1.5 s: normal every 2 s, after Frenzy
 *                         1.5 s; heroic every 1.5 s, after Frenzy two at once every 1 s); the home lane (10 yd, 1.5 s)
 *                         back to the pit's center, where the tank picks him up. 30% (heroic 45%) and Weakened each
 *   HB2 Ravager's Throw   6 s, then every 30 s (heroic 32 s), never during a spin: a 5 yd circle at a random player's
 *                         spot (2 s). Normal: the axe spins where it lands while its way home shows as a 3 yd line to
 *                         his hand (1.5 s), then flies home along it. Heroic: it first whirls on its own 5 s toward a
 *                         random player (a 4 yd spin at 5 yd/s, its path shown 1.5 s ahead, once per player). 30% (45%)
 *                         and Weakened; while it is out he punches the tank and never cleaves
 *   HB3 Champion's Cleave every 6 s while he holds a weapon in melee: a 90 degree cone 8 yd ahead (1.5 s): the tank 15%
 *                         (heroic 25%) of the tank row, anyone else 30% (45%) and Weakened
 *   HB4 Frenzy            once at 50%: yell 2 and emote 4, +30% attack speed and +20% Physical damage for the rest of
 *                         the fight; the blades quicken (the hard mode replaces it with its prayer)
 *   HB5 The Trainees      on his death his stock summon group 1: twenty Scarlet Trainees (6575: 400 each, heroic
 *                         2.5k) behind the door, 60 s summons that fight to the last; the closest one yells
 *
 * A wipe resets him to his spawn with Ravager in hand, opens the door, removes the cyclone and Frenzy and despawns his
 * stalkers (and the hard mode's units); the encounter completes on his death (the instance stands portal P3 on DONE).
 * Every percent hit is a percent of the reference row (the tank row on the tank) through the registry; the cleave's
 * tank hit through the kit's spell_dungeon_refflat_damage. Boss data: no kill order, interrupt, dispel or purge (the
 * hard mode adds the garrison); the look stalkers ignored. Every firing logs one INFO line "sm herod <mechanic> ..."
 * (module.dungeonbosses); `.dbtest sm herod ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitWings.h"
#include "GameObject.h"
#include "HerodFight.h"
#include "HerodLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
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
#include <cmath>
#include <functional>
#include <list>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmHerod;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "herod";

    // The hall's registry shapes are anchored at this height with this band, so one shape covers the pit floor (z
    // 6.4), the ledge's steps and the door spur (z 18.2), and its markers settle on whichever floor is under them.
    float constexpr kZoneAnchorZ = 12.3f;
    float constexpr kZoneZToleranceYd = 7.f;
    // A spin's band and circle live until his return cancels them (longer than any spin).
    uint32 constexpr kSpinZoneLifeMs = 60000;
    // The telegraph-only zones (the band, the circles on him and the axe) re-check at this rate (no hit of their own).
    uint32 constexpr kTelegraphTickMs = 1000;

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    Position At(Vec2 p, float z, float o = 0.f)
    {
        return Position(p.x, p.y, z, o);
    }

    Position PitCenter()
    {
        return Position(kPitCenter.x, kPitCenter.y, kPitCenter.z, 0.f);
    }

    // Every spot the bots plan for the fight's zones stays in the hall: the pit and the ledge, and the door spur
    // (rule 12).
    BossMechanics::SpotBounds HallBounds()
    {
        std::vector<Position> spur;
        for (Vec2 const& p : kDoorSpur)
            spur.emplace_back(p.x, p.y, 17.f);
        return BossMechanics::SpotBounds().Circle(Position(kPitCenter.x, kPitCenter.y, kZoneAnchorZ),
            kHallRadiusYd - 0.5f, kHallZMin, kHallZMax).Polygon(std::move(spur), 14.f, kHallZMax);
    }

    // While the ledge band is up (a spin), the bots' spots stay on the pit floor.
    BossMechanics::SpotBounds PitBounds()
    {
        return BossMechanics::SpotBounds().Circle(PitCenter(), kPitSafeRadiusYd, kPitZMin, kPitZMax);
    }

    // HB0: the seal's spec (KT-SM SealedArena, section 7 #22 A): Herod's Door shuts 3 s after the pull with a boss
    // emote (the pit is 25-30 yd from the door), stragglers in the Armory within 60 yd of the spot inside the door are
    // moved there. D11H's re-seal after the garrison says it again.
    DungeonKit::SealedArenaSpec SealSpec()
    {
        DungeonKit::SealedArenaSpec spec;
        spec.arena = HerodArena();
        spec.entry = Position(kHallEntry.x, kHallEntry.y, kHallEntry.z, kHallEntryFacing);
        spec.sameWing = [](Creature const* boss, Player const* player)
        {
            return WingOf(DungeonKit::PlaneOf(player)) == WingOf(DungeonKit::PlaneOf(boss));
        };
        spec.doorEntry = GO_HERODS_DOOR;
        spec.emoteGroup = EMOTE_SEAL;
        spec.dungeon = kLogDungeon;
        spec.boss = kBossLogName;
        return spec;
    }

    // D11H's hooks (HerodFight.h), set once from AddSC_sm_herod_hard_mode whatever the AddSC order.
    HerodHardModeFactory& HardModeFactory()
    {
        static HerodHardModeFactory factory;
        return factory;
    }

    HerodTauntHandler& TauntHandler()
    {
        static HerodTauntHandler handler;
        return handler;
    }

    HerodIdleHook& IdleHook()
    {
        static HerodIdleHook hook;
        return hook;
    }
}

void SmHerod::RegisterHerodHardMode(HerodHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

void SmHerod::RegisterHerodTauntHandler(HerodTauntHandler handler)
{
    TauntHandler() = std::move(handler);
}

void SmHerod::RegisterHerodIdleHook(HerodIdleHook hook)
{
    IdleHook() = std::move(hook);
}

bool SmHerod::HasHerodHardMode()
{
    return static_cast<bool>(HardModeFactory());
}

std::unique_ptr<HerodHardMode> SmHerod::CreateHerodHardMode(Creature* herod)
{
    HerodHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(herod) : nullptr;
}

// Herod 3975
struct boss_herod_rework : public BossAI, public HerodFight
{
private:
    enum class SpinStage : uint8
    {
        None,
        OutMarked,      // HB1a the out lane's marker; he spins in place
        OutDash,        // he dashes the out lane
        Lap,            // HB1b the lap (HB1c blades, his spin's hits)
        HomeMarked,     // HB1d the home lane's marker; he spins in place on the ledge
        HomeDash,       // he dashes home
    };

    struct SpinState
    {
        bool active = false;
        SpinStage stage = SpinStage::None;
        uint32 index = 0;
        bool clockwise = false;
        std::size_t start = 0;              // the lap's start (and end) point
        uint64 stageUntilMs = 0;
        uint64 moveEndMs = 0;
        uint64 lapStartMs = 0;
        uint64 lapEndMs = 0;
        uint64 nextBladeMs = 0;             // 0: no more blades this lap
        uint64 nextScanMs = 0;
        MechanicHandle band;
        MechanicHandle circle;
        GuidSet hit;                        // players his spin hit this lap
        uint32 blades = 0;
    };

    enum class AxeStage : uint8
    {
        None,
        Flying,         // HB2 the throw's marker; the axe in the air
        Whirl,          // HB2w the axe whirls on its own (heroic)
        ReturnMarked,   // HB2a the line home
    };

    struct AxeState
    {
        bool active = false;
        AxeStage stage = AxeStage::None;
        Position spot;
        ObjectGuid stalker;
        uint64 stageUntilMs = 0;
        uint64 nextScanMs = 0;
        MechanicHandle whirl;
        MechanicHandle ahead;
        GuidSet hit;                        // players the whirl hit
        // HB2w the whirl's straight path (the stalker, when there is one, only shows it: the hits read this)
        Vec2 whirlFrom;
        Vec2 whirlEnd;
        float whirlEndZ = 0.f;
        uint64 whirlStartMs = 0;
        bool whirled = false;
    };

public:
    explicit boss_herod_rework(Creature* creature)
        : BossAI(creature, BOSS_HEROD), _arena(HerodArena(), LeashOptions(kBossLogName)), _seal(SealSpec()) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false, "reset");
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _heroic = IsHeroicMap(me);
        _hardModeLit = _heroic && instance && instance->GetData(DATA_HARD_MODE_HEROD) != 0;
        _engaged = true;
        _clockMs = 0;
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_HEROD;
        Mechanic::BeginEncounter(me, options);
        if (_hardModeLit)
        {
            _hardMode = CreateHerodHardMode(me);
            if (!_hardMode)
                Log("hardmode-missing", "the flag is lit but no hard mode is registered: plain heroic");
        }
        _thresholdPct = _hardMode ? _hardMode->ThresholdPct(*this) : std::nullopt;
        Describe();
        _arena.Engage(me);
        if (instance)
        {
            ObjectGuid const door = instance->GetGuidData(GO_HERODS_DOOR);
            if (!door.IsEmpty())
                _seal.SetDoor(door);
        }
        _seal.Engage(me);
        Talk(SAY_AGGRO);

        _spinClock.Start(_clockMs, kSpinBeat(_heroic).firstMs);
        _throwClock.Start(_clockMs, kThrowBeat(_heroic).firstMs);
        _cleaveClock.Start(_clockMs, kCleaveBeat.firstMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} hardmode={} handler={} threshold={:.0f} at=({:.1f}, {:.1f}, {:.1f})",
                _heroic ? 1 : 0, _hardModeLit ? 1 : 0, _hardMode ? 1 : 0, _thresholdPct.value_or(kFrenzyAtPct),
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
        if (_hardMode)
            _hardMode->OnEngage(*this);
        // The rule-23 pull line last: a hard mode pull logs the health its OnEngage set (400k, not the heroic 320k).
        OnBossPull(me, kBossLogName, _hardModeLit);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false, "evade");
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("spins={} blades={} lap-hits={} throws={} whirls={} cleaves={} frenzy={} hardmode={} "
                "killer={}", _spinsStarted, _bladesTotal, _lapHitsTotal, _throws, _whirls, _cleaves, _frenzied ? 1 : 0,
                _hardMode ? 1 : 0, killer ? killer->GetName() : "none"));
        Cleanup(true, "death");
        SummonTrainees();
    }

    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer() || _clockMs < _killLineReadyMs)
            return;
        _killLineReadyMs = _clockMs + kKillLineCooldownMs;
        Talk(SAY_KILL);
    }

    // His stalkers and the hard mode's units are his (they go with his reset and death). The trainees of his death
    // are not: they outlive him (HB5).
    void JustSummoned(Creature* summon) override
    {
        if (!summon || summon->GetEntry() == NPC_SCARLET_TRAINEE)
            return;
        summons.Summon(summon);
        if (_hardMode && _engaged)
            _hardMode->OnSummoned(*this, summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        BossAI::SummonedCreatureDies(summon, killer);
        if (_hardMode && _engaged && summon)
            _hardMode->OnSummonDied(*this, summon, killer);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    // HM0 The Real Challenge: a /taunt aimed at him reaches D11H's handler (no range check; in or out of combat, any
    // difficulty: D11H judges it and answers). D11 never answers a taunt itself.
    void ReceiveEmote(Player* player, uint32 emote) override
    {
        if (emote != kTextEmoteTaunt || !player)
            return;
        HerodTauntHandler const& handler = TauntHandler();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "taunt",
            Acore::StringFormat("player={} in-combat={} heroic={} handler={}", player->GetName(),
                me->IsEngaged() ? 1 : 0, IsHeroicMap(me) ? 1 : 0, handler ? 1 : 0));
        if (handler)
            handler(*this, player, me->IsEngaged());
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsEngaged())
        {
            // D11H, out of combat: the red aura while the flag is lit (a wipe, a cold load).
            if (me->IsAlive() && !me->IsInEvadeMode())
                if (HerodIdleHook const& hook = IdleHook())
                    hook(*this);
        }
        if (!UpdateVictim())
            return;
        _clockMs += diff;
        _seal.Update(me, diff);     // HB0
        // The guard turns him to a target on his arena; while he spins or the hard mode holds him he holds no target
        // (the spin and the hard mode move him).
        if (!_spin.active && !_held && !_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        if (_hardMode)
            _hardMode->OnUpdate(*this, diff);
        UpdateThreshold();
        UpdateSpin();
        UpdateAxe();
        UpdateThreshold();      // a spin or throw that ended this tick: the threshold goes before the next beat

        // A cleave's marker is out, or the threshold waits for him to come home: the spin and throw wait.
        float const thresholdAt = _thresholdPct.value_or(kFrenzyAtPct);
        bool const busy = _clockMs < _cleaveBusyUntilMs
            || !BeatMayStart(ThresholdPending(me->GetHealthPct(), thresholdAt, _thresholdDone));
        if (!_spin.active && !busy && SpinAllowed(_axe.active, _held) && _spinClock.Due(_clockMs))
        {
            _spinClock.Fired(_clockMs, SpinEveryMs());
            StartSpin();
        }
        else if (!_axe.active && !busy && SmHerod::ThrowAllowed(_spin.active, _held, HardModeAllowsThrow())
            && _throwClock.Due(_clockMs))
        {
            _throwClock.Fired(_clockMs, ThrowEveryMs());
            StartThrow(nullptr);
        }
        if (CleaveAllowed(_spin.active, _axe.active, _held) && _cleaveClock.Due(_clockMs))
            if (Unit* victim = me->GetVictim())
                if (me->IsWithinMeleeRange(victim))
                {
                    _cleaveClock.Fired(_clockMs, kCleaveBeat.everyMs);
                    Cleave();
                }
        if (_spin.active || _held)
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (D11H's overrides through HerodFight.h, else the build spec's normal / heroic value)
    // ----------------------------------------------------------------------------------------------------------------

    float HitPct(HerodHit hit) const
    {
        if (_hardMode)
            if (std::optional<float> const pct = _hardMode->HitPct(*this, hit))
                return *pct;
        return kHitPct(_heroic);
    }

    uint32 SpinEveryMs() const
    {
        if (_hardMode)
            if (std::optional<uint32> const every = _hardMode->SpinEveryMs(*this))
                return *every;
        return kSpinBeat(_heroic).everyMs;
    }

    uint32 ThrowEveryMs() const
    {
        if (_hardMode)
            if (std::optional<uint32> const every = _hardMode->ThrowEveryMs(*this))
                return *every;
        return kThrowBeat(_heroic).everyMs;
    }

    float LapSpeed() const
    {
        if (_hardMode)
            if (std::optional<float> const speed = _hardMode->LapSpeedYd(*this))
                return *speed;
        return kLapSpeedYd(_heroic);
    }

    BladePlan Blades() const
    {
        if (_hardMode)
            if (std::optional<BladePlan> const plan = _hardMode->Blades(*this))
                return *plan;
        return BladePlanFor(_heroic, _frenzied);
    }

    uint32 WhirlMs() const
    {
        if (_hardMode)
            if (std::optional<uint32> const ms = _hardMode->WhirlMs(*this))
                return *ms;
        return kWhirlMs(_heroic);
    }

    bool HardModeAllowsThrow() const
    {
        return !_hardMode || _hardMode->ThrowAllowed(*this);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HB4 Frenzy (or the hard mode's threshold)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateThreshold()
    {
        if (_thresholdDone)
            return;
        float const at = _thresholdPct.value_or(kFrenzyAtPct);
        if (!ThresholdReady(me->GetHealthPct(), at, _spin.active, _axe.active))
            return;
        _thresholdDone = true;
        if (_thresholdPct && _hardMode)
        {
            Log("threshold", Acore::StringFormat("pct={:.0f} health={:.0f}%", at, me->GetHealthPct()));
            _hardMode->OnThreshold(*this);
        }
        else
            Frenzy("50%", true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HB1 Blades of Light
    // ----------------------------------------------------------------------------------------------------------------

    // The floor height of lap point `i` (probed once in its band, LapZBandOf; the map does not change).
    float LapZ(std::size_t i)
    {
        if (!_lapZReady)
        {
            for (std::size_t k = 0; k < kLapPointCount; ++k)
            {
                Vec2 const p = LapPoint(k);
                LapZBand const band = LapZBandOf(k);
                float const z = me->GetMapHeight(p.x, p.y, band.ProbeZ());
                _lapZ[k] = band.Pick(z);    // INVALID_HEIGHT is below every band: the estimate
            }
            _lapZReady = true;
        }
        return _lapZ[i % kLapPointCount];
    }

    // The yell, the cyclone, the band and the circle on him, and the out lane to a random point of the lap.
    void StartSpin()
    {
        _spin = SpinState();
        _spin.active = true;
        _spin.index = ++_spinsStarted;
        _spin.clockwise = urand(0, 1) == 1;
        _spin.start = urand(0, kLapPointCount - 1);
        StopFighting();
        Talk(SAY_BLADES);
        me->CastSpell(me, SPELL_HB_CYCLONE, true);

        // HB1b the ledge band from the yell (a telegraph: his spin is the hit), HB1 the 5 yd circle following him.
        MechanicRef band = Mechanic::Donut(me, Position(kPitCenter.x, kPitCenter.y, kZoneAnchorZ), kBandInnerYd,
            kBandOuterYd, Ms(kOutWarnMs));
        band.Persistent(Ms(kSpinZoneLifeMs), Ms(kTelegraphTickMs)).ZTolerance(kZoneZToleranceYd)
            .Within(HallBounds()).Tag(TAG_HB_LAP);
        _spin.band = band.Handle();
        Track(_spin.band);
        MechanicRef circle = Mechanic::Circle(me, me, kSpinRadiusYd, Ms(kTelegraphTickMs));
        circle.Persistent(Ms(kSpinZoneLifeMs), Ms(kTelegraphTickMs)).ZTolerance(kZoneZToleranceYd)
            .Within(HallBounds()).Tag(TAG_HB_SPIN);
        _spin.circle = circle.Handle();
        Track(_spin.circle);

        // HB1a the out lane: from where he stands to the lap's start point.
        Vec2 const from = DungeonKit::PlaneOf(me);
        Vec2 const to = LapPoint(_spin.start);
        float const pct = HitPct(HerodHit::Out);
        MechanicRef lane = Mechanic::Line(me, At(from, kZoneAnchorZ), At(to, kZoneAnchorZ), kLaneWidthYd,
            Ms(kOutWarnMs));
        lane.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_HB_OUT).Weakened()
            .ZTolerance(kZoneZToleranceYd).Within(HallBounds()).Tag(TAG_HB_OUT)
            .OnResolve(OnHerod([gen = _generation](boss_herod_rework& ai, BossMechanics::ResolveResult const& r)
            {
                if (ai._generation == gen)
                    ai.LaneLanded("out", r);
            }));
        if (lane.IsValid())
            Track(lane.Handle());
        _spin.stage = SpinStage::OutMarked;
        _spin.stageUntilMs = _clockMs + kOutWarnMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spin",
            Acore::StringFormat("index={} start={} clockwise={} speed={:.0f} lap={}ms pct={:.0f} frenzied={}",
                _spin.index, _spin.start, _spin.clockwise ? 1 : 0, LapSpeed(), LapMs(LapSpeed()), pct,
                _frenzied ? 1 : 0));
        if (_hardMode)
            _hardMode->OnSpinStart(*this, _spin.index, _spin.clockwise);
    }

    void LaneLanded(char const* lane, BossMechanics::ResolveResult const& result)
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lane-lands",
            Acore::StringFormat("lane={} spin={} hits={}", lane, _spin.index, result.hits.size()));
    }

    // The spin's stages on the AI's clock: the out lane's marker, the dash, the lap (blades, the spin's hits), the
    // home lane's marker, the dash home.
    void UpdateSpin()
    {
        if (!_spin.active)
            return;
        switch (_spin.stage)
        {
            case SpinStage::OutMarked:
                if (_clockMs >= _spin.stageUntilMs)
                {
                    Vec2 const to = LapPoint(_spin.start);
                    Dash(At(to, LapZ(_spin.start)), SpinStage::OutDash);
                }
                break;
            case SpinStage::OutDash:
                if (MoveEnded())
                    StartLap();
                break;
            case SpinStage::Lap:
                UpdateBlades();
                ScanSpin();
                if (MoveEnded())
                    MarkHome();
                break;
            case SpinStage::HomeMarked:
                ScanSpin();
                if (_clockMs >= _spin.stageUntilMs)
                    Dash(PitCenter(), SpinStage::HomeDash);
                break;
            case SpinStage::HomeDash:
                if (MoveEnded())
                    EndSpin("home");
                break;
            default:
                break;
        }
    }

    // A straight dash along a lane (his spin, faster than the lap).
    void Dash(Position const& to, SpinStage stage)
    {
        std::vector<DungeonKit::FloorPathPoint> path{
            { me->GetPositionX(), me->GetPositionY(), me->GetPositionZ() },
            { to.GetPositionX(), to.GetPositionY(), to.GetPositionZ() } };
        float const yd = me->GetExactDist(&to);
        _spin.stage = stage;
        _spin.moveEndMs = _clockMs + TravelMs(yd, kDashSpeedYd);
        if (yd < 0.5f || !DungeonKit::MoveAlongFloor(me, path, kDashSpeedYd))
            _spin.moveEndMs = _clockMs;     // already there (or he cannot move): the next stage at once
    }

    // The planned end of the current move has passed and the spline reports done (or is long overdue).
    bool MoveEnded() const
    {
        if (_clockMs < _spin.moveEndMs)
            return false;
        return me->movespline->Finalized() || _clockMs >= _spin.moveEndMs + kMoveGraceMs;
    }

    // HB1b one lap of the ledge from the lap's start point, back to it.
    void StartLap()
    {
        float const speed = LapSpeed();
        std::vector<Vec2> const route = LapRoute(_spin.start, _spin.clockwise);
        std::vector<DungeonKit::FloorPathPoint> path;
        path.reserve(route.size() + 1);
        path.push_back({ me->GetPositionX(), me->GetPositionY(), me->GetPositionZ() });
        for (std::size_t k = 1; k < route.size(); ++k)
        {
            std::size_t const step = k % kLapPointCount;
            std::size_t const i = _spin.clockwise ? (_spin.start + kLapPointCount - step) % kLapPointCount
                : (_spin.start + step) % kLapPointCount;
            path.push_back({ route[k].x, route[k].y, LapZ(i) });
        }
        uint32 const lapMs = LapMs(speed);
        _spin.stage = SpinStage::Lap;
        _spin.lapStartMs = _clockMs;
        _spin.lapEndMs = _clockMs + lapMs;
        _spin.moveEndMs = _spin.lapEndMs;
        BladePlan const plan = Blades();
        _spin.nextBladeMs = _clockMs + plan.everyMs;
        _spin.nextScanMs = _clockMs;
        if (!DungeonKit::MoveAlongFloor(me, path, speed))
            Log("lap-refused", "he cannot move: the lap is skipped");
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lap",
            Acore::StringFormat("spin={} speed={:.0f} lap={}ms blades-every={}ms x{} clockwise={}", _spin.index, speed,
                lapMs, plan.everyMs, plan.count, _spin.clockwise ? 1 : 0));
    }

    // HB1c: a wave of blades every interval of the lap, the last one resolving before the lap ends.
    void UpdateBlades()
    {
        if (!_spin.nextBladeMs || _clockMs < _spin.nextBladeMs)
            return;
        if (_spin.nextBladeMs + kBladeWarnMs > _spin.lapEndMs)
        {
            _spin.nextBladeMs = 0;      // no more this lap
            return;
        }
        BladePlan const plan = Blades();
        FireBlades(plan.count, nullptr);
        _spin.nextBladeMs += plan.everyMs ? plan.everyMs : kBladeWarnMs;
    }

    // `count` blades at different random players (the tank included), each a 4 yd lane from him across the pit;
    // `forced`: one blade at that player (the GM test). Returns how many flew.
    uint32 FireBlades(uint32 count, Player* forced)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;           // "random player" includes the tank
            targets = DungeonKit::PickPlayers(me, rule, count);
        }
        float const pct = HitPct(HerodHit::Blade);
        Vec2 const from = DungeonKit::PlaneOf(me);
        uint32 flown = 0;
        std::string who;
        for (Player* target : targets)
        {
            if (!CountsAsPlayer(target))
                continue;
            Vec2 const aim = DungeonKit::PlaneOf(target);
            float const facing = DungeonKit::BearingTo(from, aim);
            float const length = BladeLengthYd(from, aim);
            MechanicRef ref = Mechanic::Line(me, At(from, kZoneAnchorZ, facing), facing, length, kBladeWidthYd,
                Ms(kBladeWarnMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_HOLY).Spell(SPELL_HB_BLADE).Weakened()
                .ZTolerance(kZoneZToleranceYd).Within(PitBounds()).Tag(TAG_HB_BLADE);
            if (!ref.IsValid())
                continue;
            Track(ref.Handle());
            Vec2 const end = DungeonKit::Advance(from, facing, length);
            me->CastSpell(end.x, end.y, kPitCenter.z, SPELL_HB_BLADE_LOOK, true);
            ++flown;
            who += (who.empty() ? "" : ",") + target->GetName();
        }
        _spin.blades += flown;
        _bladesTotal += flown;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, flown ? "blade" : "blade-skipped",
            Acore::StringFormat("spin={} targets=[{}] pct={:.0f} at=({:.1f}, {:.1f}) blades={}", _spin.index, who, pct,
                from.x, from.y, _spin.blades));
        return flown;
    }

    // HB1b his spin passing a player: once per lap each (the lap and the wait at its end).
    void ScanSpin()
    {
        if (_clockMs < _spin.nextScanMs)
            return;
        _spin.nextScanMs = _clockMs + kLapScanMs;
        GuidSet fresh;
        for (Player* player : FightPlayers())
        {
            if (_spin.hit.count(player->GetGUID()))
                continue;
            if (me->GetExactDist2d(player) > kSpinRadiusYd
                || std::fabs(player->GetPositionZ() - me->GetPositionZ()) > kSpinZBandYd)
                continue;
            fresh.insert(player->GetGUID());
        }
        if (fresh.empty())
            return;
        for (ObjectGuid const& guid : fresh)
            _spin.hit.insert(guid);
        float const pct = HitPct(HerodHit::Lap);
        DungeonKit::RegistryHitSpec spec;
        spec.pct = pct;
        spec.tankPct = pct;
        spec.school = SPELL_SCHOOL_NORMAL;
        spec.spellId = SPELL_HB_LAP;
        spec.weakened = true;
        spec.tag = TAG_HB_LAP;
        Track(DungeonKit::RegistryHit(me, fresh, spec));
        _lapHitsTotal += static_cast<uint32>(fresh.size());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "lap-hit",
            Acore::StringFormat("spin={} hit={} pct={:.0f} at=({:.1f}, {:.1f}, {:.1f})", _spin.index, fresh.size(), pct,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    // HB1d the home lane: from his spot on the ledge to the pit's center (a chained follow-up on 1.5 s).
    void MarkHome()
    {
        Vec2 const from = DungeonKit::PlaneOf(me);
        float const pct = HitPct(HerodHit::Home);
        MechanicRef lane = Mechanic::Line(me, At(from, kZoneAnchorZ),
            Position(kPitCenter.x, kPitCenter.y, kZoneAnchorZ), kLaneWidthYd, Ms(kHomeWarnMs));
        lane.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_HB_HOME).Weakened()
            .ZTolerance(kZoneZToleranceYd).Within(PitBounds()).Tag(TAG_HB_HOME)
            .OnResolve(OnHerod([gen = _generation](boss_herod_rework& ai, BossMechanics::ResolveResult const& r)
            {
                if (ai._generation == gen)
                    ai.LaneLanded("home", r);
            }));
        if (lane.IsValid())
            Track(lane.Handle());
        _spin.stage = SpinStage::HomeMarked;
        _spin.stageUntilMs = _clockMs + kHomeWarnMs;
        Log("home", Acore::StringFormat("spin={} from=({:.1f}, {:.1f}) blades={} lap-hits={}", _spin.index, from.x,
            from.y, _spin.blades, _spin.hit.size()));
    }

    // Home at the pit's center: the band and the circle off, the cyclone off, he takes up the tank again.
    void EndSpin(char const* why)
    {
        if (!_spin.active)
            return;
        uint32 const index = _spin.index;
        for (MechanicHandle const& handle : { _spin.band, _spin.circle })
            if (handle)
                Mechanic::Cancel(me, handle);
        me->RemoveAurasDueToSpell(SPELL_HB_CYCLONE);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "spin-end",
            Acore::StringFormat("index={} why={} blades={} lap-hits={} took={}ms", index, why, _spin.blades,
                _spin.hit.size(), _clockMs >= _spin.lapStartMs ? _clockMs - _spin.lapStartMs : 0));
        _spin = SpinState();
        if (!_held)
            ResumeFighting();
        _cleaveClock.Start(_clockMs, kCleaveAfterHoldMs);
        if (_hardMode)
            _hardMode->OnSpinEnd(*this, index);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HB2 Ravager's Throw (and HB2w the whirling axe, heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // A 5 yd circle at a random player's spot; the axe leaves his hand.
    bool StartThrow(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!CountsAsPlayer(target))
        {
            Log("throw-skipped", "no player to throw at");
            return false;
        }
        Position const spot = target->GetPosition();
        float const pct = HitPct(HerodHit::Throw);
        MechanicRef ref = Mechanic::Circle(me, spot, kThrowRadiusYd, Ms(kThrowWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_HB_THROW).Weakened()
            .Within(HallBounds()).Tag(TAG_HB_THROW);
        if (!ref.IsValid())
        {
            Log("throw-refused", target->GetName());
            return false;
        }
        Track(ref.Handle());
        _axe = AxeState();
        _axe.active = true;
        _axe.stage = AxeStage::Flying;
        _axe.spot = spot;
        _axe.stageUntilMs = _clockMs + kThrowWarnMs;
        me->SetVirtualItem(0, 0);
        me->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_HB_THROW_LOOK, true);
        ++_throws;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "throw",
            Acore::StringFormat("target={} at=({:.1f}, {:.1f}, {:.1f}) pct={:.0f} whirl={}ms throws={}",
                target->GetName(), spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), pct, WhirlMs(),
                _throws));
        if (_hardMode)
            _hardMode->OnThrow(*this);
        return true;
    }

    void UpdateAxe()
    {
        if (!_axe.active)
            return;
        switch (_axe.stage)
        {
            case AxeStage::Flying:
                if (_clockMs >= _axe.stageUntilMs)
                    AxeLanded();
                break;
            case AxeStage::Whirl:
                ScanWhirl();
                if (_clockMs >= _axe.stageUntilMs)
                    MarkReturn();
                break;
            case AxeStage::ReturnMarked:
                if (_clockMs >= _axe.stageUntilMs)
                    AxeHome("caught");
                break;
            default:
                break;
        }
    }

    // The axe lands: it spins on the floor (a stalker with the floor spin), then whirls (heroic) or flies home.
    void AxeLanded()
    {
        if (Creature* axe = SummonLook(_axe.spot, 0))
        {
            _axe.stalker = axe->GetGUID();
            axe->CastSpell(axe, SPELL_HB_AXE_SPIN, true);
        }
        uint32 const whirl = WhirlMs();
        if (whirl && StartWhirl(whirl))
            return;
        MarkReturn();
    }

    // HB2w: the axe whirls toward a random player for `ms` along a straight path: a circle following it and its path
    // shown 1.5 s ahead (telegraphs: the script hits each player it passes once). Without its stalker (a missing
    // template) the whole path is marked instead and the whirl runs on the same clock.
    bool StartWhirl(uint32 ms)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        Player* target = DungeonKit::PickPlayer(me, rule);
        Vec2 const from{ _axe.spot.GetPositionX(), _axe.spot.GetPositionY() };
        Vec2 const aim = CountsAsPlayer(target) ? DungeonKit::PlaneOf(target) : Vec2{ kPitCenter.x, kPitCenter.y };
        float const pathYd = kWhirlSpeedYd * static_cast<float>(ms) / 1000.f;
        float const spotZ = _axe.spot.GetPositionZ();
        Vec2 const end = WhirlEnd(from, aim, pathYd, WhirlRoomYd(from, LandedInPit(spotZ)));
        float const facing = DungeonKit::BearingTo(from, end);
        // Probed from under the spur's roof (the hall is open above the pit and the ledge).
        float const endZ = WhirlEndZ(me->GetMapHeight(end.x, end.y, kSpurZBand.ProbeZ()), spotZ);
        _axe.whirlFrom = from;
        _axe.whirlEnd = end;
        _axe.whirlEndZ = endZ;
        _axe.whirlStartMs = _clockMs;
        _axe.whirled = true;
        // Both are telegraphs for the whole whirl (persistent, no hit of their own).
        auto lasting = [this, ms](MechanicRef& ref) -> MechanicHandle
        {
            if (!ref.IsValid())
                return MechanicHandle();
            ref.Persistent(Ms(ms), Ms(kTelegraphTickMs)).Within(HallBounds()).Tag(TAG_HB_WHIRL);
            Track(ref.Handle());
            return ref.Handle();
        };
        if (Creature* axe = ObjectAccessor::GetCreature(*me, _axe.stalker))
        {
            std::vector<DungeonKit::FloorPathPoint> path{ { axe->GetPositionX(), axe->GetPositionY(),
                axe->GetPositionZ() }, { end.x, end.y, endZ } };
            DungeonKit::MoveAlongFloor(axe, path, kWhirlSpeedYd);
            MechanicRef circle = Mechanic::Circle(me, axe, kWhirlRadiusYd, Ms(kTelegraphTickMs));
            _axe.whirl = lasting(circle);
            float const aheadYd = kWhirlSpeedYd * static_cast<float>(kWhirlAheadMs) / 1000.f + kWhirlRadiusYd;
            MechanicRef ahead = Mechanic::Line(me, axe, facing, aheadYd, kWhirlPathWidthYd, Ms(kTelegraphTickMs));
            _axe.ahead = lasting(ahead);
        }
        else
        {
            MechanicRef path = Mechanic::Line(me, _axe.spot, Position(end.x, end.y, endZ),
                kWhirlPathWidthYd, Ms(kTelegraphTickMs));
            _axe.ahead = lasting(path);
        }
        _axe.stage = AxeStage::Whirl;
        _axe.stageUntilMs = _clockMs + ms;
        _axe.nextScanMs = _clockMs;
        ++_whirls;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "whirl",
            Acore::StringFormat("toward={} from=({:.1f}, {:.1f}) to=({:.1f}, {:.1f}) for={}ms pct={:.0f} look={}",
                CountsAsPlayer(target) ? target->GetName() : "center", from.x, from.y, end.x, end.y, ms,
                HitPct(HerodHit::Whirl), _axe.stalker.IsEmpty() ? 0 : 1));
        return true;
    }

    // Where the whirling axe is now (on its path at 5 yd/s, its height along the path; its landing spot before or
    // without a whirl).
    Position AxeNow() const
    {
        if (!_axe.whirled)
            return _axe.spot;
        Vec2 const p = WhirlPosAt(_axe.whirlFrom, _axe.whirlEnd, kWhirlSpeedYd, _clockMs - _axe.whirlStartMs);
        return Position(p.x, p.y, WhirlZAt(_axe.whirlFrom, _axe.spot.GetPositionZ(), _axe.whirlEnd, _axe.whirlEndZ,
            p));
    }

    // HB2w: each player within the whirling axe's 4 yd spin is hit once per whirl.
    void ScanWhirl()
    {
        if (_clockMs < _axe.nextScanMs)
            return;
        _axe.nextScanMs = _clockMs + kLapScanMs;
        Position const axe = AxeNow();
        GuidSet fresh;
        for (Player* player : FightPlayers())
        {
            if (_axe.hit.count(player->GetGUID()))
                continue;
            if (player->GetExactDist2d(axe.GetPositionX(), axe.GetPositionY()) > kWhirlRadiusYd
                || std::fabs(player->GetPositionZ() - axe.GetPositionZ()) > kSpinZBandYd)
                continue;
            fresh.insert(player->GetGUID());
        }
        if (fresh.empty())
            return;
        for (ObjectGuid const& guid : fresh)
            _axe.hit.insert(guid);
        float const pct = HitPct(HerodHit::Whirl);
        DungeonKit::RegistryHitSpec spec;
        spec.pct = pct;
        spec.tankPct = pct;
        spec.school = SPELL_SCHOOL_NORMAL;
        spec.spellId = SPELL_HB_WHIRL;
        spec.weakened = true;
        spec.tag = TAG_HB_WHIRL;
        Track(DungeonKit::RegistryHit(me, fresh, spec));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "whirl-hit",
            Acore::StringFormat("hit={} pct={:.0f} whirl-hits={}", fresh.size(), pct, _axe.hit.size()));
    }

    // HB2a: the axe's way home, a 3 yd line from where it is to his hand, 1.5 s.
    void MarkReturn()
    {
        for (MechanicHandle const& handle : { _axe.whirl, _axe.ahead })
            if (handle)
                Mechanic::Cancel(me, handle);
        _axe.whirl = MechanicHandle();
        _axe.ahead = MechanicHandle();
        Position const from = AxeNow();
        if (Creature* axe = ObjectAccessor::GetCreature(*me, _axe.stalker))
            axe->StopMoving();
        float const pct = HitPct(HerodHit::Return);
        MechanicRef ref = Mechanic::Line(me, from, me, kReturnWidthYd, Ms(kReturnWarnMs));
        ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_HB_RETURN).Weakened()
            .ZTolerance(kZoneZToleranceYd).Within(HallBounds()).Tag(TAG_HB_RETURN);
        if (ref.IsValid())
            Track(ref.Handle());
        _axe.stage = AxeStage::ReturnMarked;
        _axe.stageUntilMs = _clockMs + kReturnWarnMs;
        Log("return", Acore::StringFormat("from=({:.1f}, {:.1f}) pct={:.0f} whirl-hits={}", from.GetPositionX(),
            from.GetPositionY(), pct, _axe.hit.size()));
    }

    // The axe flies home along its line: back in his hand, the cleave a moment later.
    void AxeHome(char const* why)
    {
        if (!_axe.active)
            return;
        if (Creature* axe = ObjectAccessor::GetCreature(*me, _axe.stalker))
        {
            axe->RemoveAurasDueToSpell(SPELL_HB_AXE_SPIN);
            axe->CastSpell(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), SPELL_HB_THROW_LOOK, true);
            axe->DespawnOrUnsummon(Ms(kAxeFlightMs));
        }
        _axe = AxeState();
        SetWeapon(0, why);
        _cleaveClock.Start(_clockMs, kCleaveAfterHoldMs);
        Log("axe-home", why);
        if (_hardMode)
            _hardMode->OnAxeHome(*this);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HB3 Champion's Cleave
    // ----------------------------------------------------------------------------------------------------------------

    // A 90 degree cone 8 yd ahead of him (1.5 s): others through the registry (the tank exempt), the tank his own hit
    // at the resolve when still in front of him.
    bool Cleave()
    {
        float const pct = HitPct(HerodHit::Cleave);
        MechanicRef ref = Mechanic::Cone(me, me, kCleaveAngleDeg, kCleaveLengthYd, Ms(kCleaveWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(pct).School(SPELL_SCHOOL_NORMAL).Spell(SPELL_HB_CLEAVE).Weakened().Within(HallBounds())
            .Tag(TAG_HB_CLEAVE)
            .OnResolve(OnHerod([gen = _generation](boss_herod_rework& ai, BossMechanics::ResolveResult const& r)
            {
                if (ai._generation == gen)
                    ai.CleaveLands(r);
            }));
        if (!ref.IsValid())
            return false;
        Track(ref.Handle());
        _cleaveBusyUntilMs = _clockMs + kCleaveWarnMs;
        ++_cleaves;
        return true;
    }

    void CleaveLands(BossMechanics::ResolveResult const& result)
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        Unit* victim = me->GetVictim();
        bool tankHit = false;
        if (victim && DungeonKit::InFrontalCone(DungeonKit::PlaneOf(me), me->GetOrientation(),
            DungeonKit::PlaneOf(victim), kCleaveAngleDeg, kCleaveLengthYd, me->GetCombatReach()))
        {
            me->CastSpell(victim, SPELL_HB_CLEAVE_TANK, true);
            tankHit = true;
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cleave",
            Acore::StringFormat("hits={} tank={} pct={:.0f} tank-pct={:.0f} cleaves={}", result.hits.size(),
                tankHit ? 1 : 0, HitPct(HerodHit::Cleave), kCleaveTankPct(_heroic), _cleaves));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HB5 The Trainees
    // ----------------------------------------------------------------------------------------------------------------

    // Stock SmartAI 3975 rows 8-9: summon group 1 (twenty Scarlet Trainees behind the door, 60 s summons), and the
    // closest one yells. The trainees' own SmartAI puts them in combat with the zone.
    void SummonTrainees()
    {
        std::list<TempSummon*> trainees;
        me->SummonCreatureGroup(kTraineeSummonGroup, &trainees);
        TempSummon* closest = nullptr;
        for (TempSummon* trainee : trainees)
            if (trainee && (!closest || me->GetExactDist(trainee) < me->GetExactDist(closest)))
                closest = trainee;
        if (closest && closest->AI() && me->GetExactDist(closest) <= kTraineeSayRangeYd)
            closest->AI()->Talk(SAY_TRAINEE_AVENGE);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "trainees",
            Acore::StringFormat("summoned={} of {} speaker={}", trainees.size(), kTraineeCount, closest ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (ARM "Boss data")
    // ----------------------------------------------------------------------------------------------------------------

    // No kill order, interrupt, dispel or purge of his own (the hard mode adds the garrison); the look stalkers are
    // ignored. The trainees come after his death (no descriptor then: bots fight them as any pack).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.ignores.emplace_back(NPC_SM_STALKER_WAVE2);
        if (_hardMode)
            _hardMode->ConfigureDescriptor(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HerodFight (the hard mode's view, HerodFight.h)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Herod() override { return me; }
    bool Heroic() const override { return _engaged ? _heroic : IsHeroicMap(me); }
    HerodHardMode* ActiveHardMode() override { return _hardMode.get(); }
    uint64 FightMs() const override { return _engaged ? _clockMs : 0; }

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        if (!me->IsEngaged())
            return out;
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

    bool Spinning() const override { return _spin.active; }
    bool AxeOut() const override { return _axe.active; }
    bool Frenzied() const override { return _frenzied; }
    uint32 SpinsStarted() const override { return _spinsStarted; }
    bool KitHeld() const override { return _held; }

    void HoldKit(bool hold, char const* why) override
    {
        if (hold == _held)
            return;
        _held = hold;
        if (hold)
        {
            if (!_spin.active)
                StopFighting();     // a spin in progress keeps its moves and leaves him passive at its end
        }
        else
        {
            if (!_spin.active)
                ResumeFighting();
            _cleaveClock.Start(_clockMs, kCleaveAfterHoldMs);
        }
        Log(hold ? "kit-held" : "kit-released", why ? why : "?");
    }

    void RestartBeats(uint32 spinInMs, uint32 throwInMs) override
    {
        _spinClock.Start(_clockMs, spinInMs);
        _throwClock.Start(_clockMs, throwInMs);
        Log("beats-restarted", Acore::StringFormat("spin-in={}ms throw-in={}ms", spinInMs, throwInMs));
    }

    void Frenzy(char const* why, bool announce) override
    {
        if (_frenzied || !me->IsAlive())
            return;
        _frenzied = true;
        me->CastSpell(me, SPELL_HB_FRENZY, true);
        if (announce)
        {
            Talk(SAY_STRENGTH);
            Talk(EMOTE_ENRAGED);
        }
        BladePlan const plan = Blades();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "frenzy",
            Acore::StringFormat("why={} health={:.0f}% haste={:.0f} damage={:.0f} blades-every={}ms x{}",
                why ? why : "?", me->GetHealthPct(), kFrenzyHastePct, kFrenzyDamagePct, plan.everyMs, plan.count));
    }

    void SetWeapon(uint32 itemEntry, char const* why) override
    {
        uint32 const item = itemEntry ? itemEntry : kItemRavager;
        me->SetVirtualItem(0, item);
        _weapon = item;
        if (itemEntry)
            Log("weapon", Acore::StringFormat("item={} why={}", item, why ? why : "?"));
    }

    void OpenDoor(char const* why) override
    {
        _seal.Release(me, why);
    }

    void SealDoor(char const* why) override
    {
        _seal.Engage(me);
        Log("door-reseal", why ? why : "?");
    }

    bool DoorSealed() const override { return _seal.IsSealed(); }

    Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs) override
    {
        return despawnMs ? me->SummonCreature(entry, at, TEMPSUMMON_TIMED_DESPAWN, despawnMs)
            : me->SummonCreature(entry, at, TEMPSUMMON_MANUAL_DESPAWN);
    }

    void TrackSummon(Creature* unit) override
    {
        if (unit)
            _extraSummons.push_back(unit->GetGUID());
    }

    void JoinFight(Creature* unit) override
    {
        if (!unit)
            return;
        Mechanic::TrackUnit(me, unit);
        // Everyone in the fight at 0 (a one-entry threat list evades: rule 11).
        for (Player* player : FightPlayers())
            unit->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
    }

    // A mechanic of the fight (a lane, a blade, a throw, a hit): kept to cancel it on a reset.
    void Track(MechanicHandle handle) override
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 160)     // the oldest resolved long ago (the spin's band and circle end with each spin)
            _live.erase(_live.begin(), _live.begin() + 60);
    }

    void RefreshDescriptor() override
    {
        if (_engaged)
            Describe();
    }

    void Say(uint8 group, WorldObject const* target) override
    {
        Talk(group, target);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm herod` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Spin,
        Blade,
        Throw,
        Cleave,
        Frenzy,
        Seal,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!me->IsEngaged() || !_engaged)
            return "Herod must be in combat (the picks read his threat list, the mechanics his encounter).";
        switch (mechanic)
        {
            case TestMechanic::Spin:
                if (_spin.active || _axe.active)
                    return "He is spinning or the axe is out already.";
                StartSpin();
                break;
            case TestMechanic::Blade:
                if (!FireBlades(1, CountsAsPlayer(who) ? who : nullptr))
                    return "No player to throw a blade at.";
                break;
            case TestMechanic::Throw:
                if (_spin.active || _axe.active)
                    return "He is spinning or the axe is out already.";
                if (!StartThrow(CountsAsPlayer(who) ? who : nullptr))
                    return "No player to throw at (see the log).";
                break;
            case TestMechanic::Cleave:
                if (!CleaveAllowed(_spin.active, _axe.active, _held))
                    return "He cannot cleave now (spinning, the axe out, or held).";
                if (!Cleave())
                    return "The cleave was refused (see the log).";
                break;
            case TestMechanic::Frenzy:
                if (_frenzied)
                    return "He is frenzied already.";
                _thresholdDone = true;
                Frenzy("gm", true);
                break;
            case TestMechanic::Seal:
                if (!_seal.IsSealed())
                    return "The door is not sealed (it shuts 3 s after the pull).";
                _seal.PullIn(me);
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} hardmode={} handler={} spin={} (index {}, stage {}, blades {}, "
            "lap-hits {}) axe={} (stage {}) frenzied={} held={} threshold={:.0f}/{} next spin={}ms throw={}ms "
            "cleave={}ms spins={} throws={} whirls={} cleaves={} blades={} door={} weapon={} live-handles={}",
            _clockMs / 1000, _heroic ? 1 : 0, _hardModeLit ? 1 : 0, _hardMode ? 1 : 0, _spin.active ? 1 : 0,
            _spin.index, uint32(_spin.stage), _spin.blades, _spin.hit.size(), _axe.active ? 1 : 0, uint32(_axe.stage),
            _frenzied ? 1 : 0, _held ? 1 : 0, _thresholdPct.value_or(kFrenzyAtPct), _thresholdDone ? "done" : "armed",
            InMs(_spinClock), InMs(_throwClock), InMs(_cleaveClock), _spinsStarted, _throws, _whirls, _cleaves,
            _bladesTotal, _seal.IsSealed() ? "sealed" : _seal.IsClosing() ? "closing" : "open", _weapon,
            _live.size());
    }

private:
    static uint64 InMsOf(BeatClock const& clock, uint64 now)
    {
        return clock.On() && clock.DueMs() > now ? clock.DueMs() - now : 0;
    }

    uint64 InMs(BeatClock const& clock) const
    {
        return InMsOf(clock, _clockMs);
    }

    // He lets go of the tank: passive, no target, no chase (a spin, the hard mode's hold).
    void StopFighting()
    {
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
    }

    // He takes up his top-threat unit again.
    void ResumeFighting()
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        me->SetReactState(REACT_AGGRESSIVE);
        if (Unit* victim = me->SelectVictim())
            AttackStart(victim);
    }

    // A look stalker (the wave 2 generic stalker 300958); `ms` 0: until the fight's cleanup or the axe's flight home.
    // nullptr when its template is missing (the fight plays without the look; the axe's timeline runs on).
    Creature* SummonLook(Position const& at, uint32 ms)
    {
        if (!sObjectMgr->GetCreatureTemplate(NPC_SM_STALKER_WAVE2))
            return nullptr;
        return ms ? me->SummonCreature(NPC_SM_STALKER_WAVE2, at, TEMPSUMMON_TIMED_DESPAWN, ms)
            : me->SummonCreature(NPC_SM_STALKER_WAVE2, at, TEMPSUMMON_MANUAL_DESPAWN);
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnHerod(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_herod_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_herod_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_herod_rework*>(boss->AI());
    }

    // The pull's state: nothing registered, no summon of his, no aura of his, Ravager in his hand, the door open, his
    // kit given back (Reset, evade, death). The hard mode undoes its own changes in OnEnd first.
    void Cleanup(bool dead, char const* why)
    {
        ++_generation;
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, dead);
            _hardMode.reset();
        }
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        summons.DespawnAll();
        for (ObjectGuid const& guid : _extraSummons)
            if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
                unit->DespawnOrUnsummon();
        _extraSummons.clear();
        _spin = SpinState();
        _axe = AxeState();
        for (uint32 const spell : { uint32(SPELL_HB_CYCLONE), uint32(SPELL_HB_FRENZY) })
            me->RemoveAurasDueToSpell(spell);
        if (me->IsAlive())
        {
            me->SetVirtualItem(0, kItemRavager);
            me->SetReactState(REACT_AGGRESSIVE);
        }
        _weapon = kItemRavager;
        _seal.Release(me, why);
        _arena.Reset();
        _spinClock.Stop();
        _throwClock.Stop();
        _cleaveClock.Stop();
        _clockMs = 0;
        _cleaveBusyUntilMs = 0;
        _killLineReadyMs = 0;
        _spinsStarted = 0;
        _throws = 0;
        _whirls = 0;
        _cleaves = 0;
        _bladesTotal = 0;
        _lapHitsTotal = 0;
        _thresholdPct.reset();
        _thresholdDone = false;
        _frenzied = false;
        _held = false;
        _engaged = false;
        _hardModeLit = false;
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::SealedArena _seal;
    std::unique_ptr<HerodHardMode> _hardMode;
    BeatClock _spinClock;
    BeatClock _throwClock;
    BeatClock _cleaveClock;
    SpinState _spin;
    AxeState _axe;
    std::vector<MechanicHandle> _live;
    std::vector<ObjectGuid> _extraSummons;
    std::array<float, kLapPointCount> _lapZ{};
    bool _lapZReady = false;
    std::optional<float> _thresholdPct;     // the hard mode's transition point (nullopt: Frenzy at 50%)
    uint64 _clockMs = 0;                    // ms since the pull: every timer of the fight
    uint64 _cleaveBusyUntilMs = 0;          // a cleave's marker is out until then
    uint64 _killLineReadyMs = 0;
    uint32 _generation = 0;                 // bumped by every cleanup: a stale callback does nothing
    uint32 _weapon = kItemRavager;
    uint32 _spinsStarted = 0;
    uint32 _throws = 0;
    uint32 _whirls = 0;
    uint32 _cleaves = 0;
    uint32 _bladesTotal = 0;
    uint32 _lapHitsTotal = 0;
    bool _heroic = false;
    bool _hardModeLit = false;
    bool _engaged = false;
    bool _thresholdDone = false;
    bool _frenzied = false;
    bool _held = false;
};

namespace
{
    boss_herod_rework* FindHerodAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_HEROD);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_herod_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Herod is not running boss_herod_rework (check the ScriptName; wave 2 "
                "binds it).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_herod_rework::TestMechanic mechanic, char const* what)
    {
        boss_herod_rework* ai = FindHerodAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Herod: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_HEROD, BOSS_HEROD);
    }

    // Handoff section 3.7: `.dbtest sm herod hardmode` arms the hard mode past its trigger (GM).
    bool HandleHardMode(ChatHandler* handler)
    {
        return SmTest::ArmHardMode(handler, BOSS_CALL_TO_ARMS);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_herod_rework* ai = FindHerodAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Herod: {}", ai->TestState());
        return true;
    }

    bool HandleSpin(ChatHandler* handler)
    {
        return Fire(handler, boss_herod_rework::TestMechanic::Spin,
            "Blades of Light (HB1: the band, the out lane, the lap and its blades, home)");
    }

    bool HandleBlade(ChatHandler* handler)
    {
        return Fire(handler, boss_herod_rework::TestMechanic::Blade,
            "a blade of light at the selected player (HB1c: a 4 yd lane from him, 1.5 s)");
    }

    bool HandleThrow(ChatHandler* handler)
    {
        return Fire(handler, boss_herod_rework::TestMechanic::Throw,
            "Ravager's Throw at the selected player (HB2: 5 yd, 2 s; heroic the whirl; the line home)");
    }

    bool HandleCleave(ChatHandler* handler)
    {
        return Fire(handler, boss_herod_rework::TestMechanic::Cleave,
            "Champion's Cleave (HB3: 90 degrees, 8 yd, 1.5 s)");
    }

    bool HandleFrenzy(ChatHandler* handler)
    {
        return Fire(handler, boss_herod_rework::TestMechanic::Frenzy, "Frenzy (HB4: the 50% buff now)");
    }

    bool HandleSeal(ChatHandler* handler)
    {
        return Fire(handler, boss_herod_rework::TestMechanic::Seal,
            "the door's pull-in (HB0: stragglers within 60 yd moved inside)");
    }

    // `.dbtest sm herod <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossHerodTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "hardmode", HandleHardMode, SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "spin",     HandleSpin,     SEC_GAMEMASTER, Console::No },
            { "blade",    HandleBlade,    SEC_GAMEMASTER, Console::No },
            { "throw",    HandleThrow,    SEC_GAMEMASTER, Console::No },
            { "cleave",   HandleCleave,   SEC_GAMEMASTER, Console::No },
            { "frenzy",   HandleFrenzy,   SEC_GAMEMASTER, Console::No },
            { "seal",     HandleSeal,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_herod_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_herod_rework, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("herod", BossHerodTestCommands());
}
