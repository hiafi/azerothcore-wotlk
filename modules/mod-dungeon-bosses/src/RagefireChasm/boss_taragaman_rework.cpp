/*
 * mod-dungeon-bosses, Ragefire Chasm D4: Taragaman the Hungerer (11520, boss_taragaman_rework), the end boss. Build
 * spec: docs/dungeons/ragefire-chasm-rework.md "Taragaman the Hungerer" (TG0-TG6, TG10; rulings 15 and 16), handoff
 * sections 3.5 row D4, 3.6, 3.8, 3.12, 7 and 10. Replaces his stock SmartAI (WP-S0's rev drops it): Fire Nova 11970 is
 * retired, Uppercut 18072 stays a stock cast. Pure rules: TaragamanLogic.h; every spec number is the tuning block
 * RagefireChasmRework::Taragaman. The hard mode (Starving, D4H) fights on this AI through TaragamanFight.h; this file
 * never needs an edit for it.
 *
 *   TG0  The gate        the instance's (he stands dormant until slots 0 to 2 are done, and says line 0); Reset applies
 *                        ApplyTaragamanGate last
 *   TG1  Feast           a mark on the player with the lowest health percent on the plateau (tank included, 3 s, hard
 *                        mode 2 s); then he leaps to them (kept on the arena) and bites. Under 50% at the landing he
 *                        Gorges: +3% health and a Gorged stack (+10% damage; cap 3 on normal, none on heroic). 18 s,
 *                        every 20 s (heroic 16 s, 15 s); waits until 4 s after a Felstorm or a Nova
 *   TG2  Devour          heroic, right after the bite: a 5 s channel on the prey, kickable (Shadow, so a kick locks
 *                        none of his bars: rule 25), 14% a second and +1% of his health each
 *   TG3  Felstorm        a 2 s cast, then 6 s (heroic 5 s) spinning where he stands: an 8 yd (10) ring, 8% (20%) a
 *                        second. 12 s, every 30 s (heroic 10 s, 25 s)
 *   TG4  Fel pulses      heroic: 4% a second to everyone on the plateau while he spins (the script's hit, never a Zone)
 *   TG5  Fel spots       heroic: every 0.5 s of the spin a 4 yd circle 0 to 4 yd off the next player of a shuffled
 *                        rotation (tank included), 1.5 s, 35% and Weakened
 *   TG6  Searing Nova    he leaps to the hub, three Searing Spikes (GO 301342; heroic an opposite pair) rise 10 yd from
 *                        it, and a 4 s cast hits everyone within 60 yd he can see (BM's Hide): 50% (75%). 25 s, every
 *                        30 s (heroic 22 s, 25 s)
 *   TG10 Uppercut        the stock cast on his target every 10 s
 *
 * Never two of Felstorm, Nova and Feast at once: Timeline (TaragamanLogic.h) starts the one due longest. While he
 * leaps, channels, spins or casts he holds no target (passive, his threat list untouched) and goes back to his threat
 * target at the end (rule 35). His percent hits are percents of the reference row with the Gorged stacks' factor on
 * top; they all carry IGNORE_CASTER_MODIFIERS, so the aura itself only raises his melee and Uppercut. His scale never
 * changes (rule 29: the Nova's eye).
 *
 * A wipe, an evade or his death clears the spikes, the spots and their stalkers, every registry handle, the marks, the
 * channel and his auras. A target on the rim band past his arena (a tank out of the ring) is still his: he walks to
 * his edge and reaches it (ArenaEdge); only one out of that reach (ReachArena) turns him. Boss data: Devour
 * on the interrupt list (heroic), the stalkers ignored. Every firing logs one
 * INFO line "rfc taragaman <mechanic> ..." (module.dungeonbosses); `.dbtest rfc taragaman ...` fires one on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MoveSpline.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RagefireChasmKit.h"
#include "RagefireChasmRework.h"
#include "RagefireChasmTestCommand.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TaragamanFight.h"
#include "TaragamanLogic.h"
#include "TemporarySummon.h"
#include "ThreatManager.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace RagefireChasmRework;
using namespace RfcTaragaman;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "taragaman";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    uint32 RandBelow(uint32 n)
    {
        return n > 1 ? urand(0, n - 1) : 0;
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // "On the plateau": its whole floor, a knocked up player included (the z band).
    bool OnPlateau(Player const* player)
    {
        static DungeonKit::Arena const floor = PlateauFloor();
        return floor.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ());
    }

    TaragamanHardModeFactory& Factory()
    {
        static TaragamanHardModeFactory factory;
        return factory;
    }

    TaragamanIdleHook& IdleHook()
    {
        static TaragamanIdleHook hook;
        return hook;
    }

    TaragamanActionHook& ActionHook()
    {
        static TaragamanActionHook hook;
        return hook;
    }
}

void RfcTaragaman::RegisterTaragamanHardMode(TaragamanHardModeFactory factory)
{
    Factory() = std::move(factory);
}

void RfcTaragaman::RegisterTaragamanIdleHook(TaragamanIdleHook hook)
{
    IdleHook() = std::move(hook);
}

void RfcTaragaman::RegisterTaragamanActionHook(TaragamanActionHook hook)
{
    ActionHook() = std::move(hook);
}

std::unique_ptr<TaragamanHardMode> RfcTaragaman::CreateTaragamanHardMode(Creature* taragaman)
{
    return Factory() ? Factory()(taragaman) : nullptr;
}

// Taragaman the Hungerer 11520
struct boss_taragaman_rework : public BossAI, public TaragamanFight
{
private:
    // What he is doing; the timeline's running beat spans several of these.
    enum class Act : uint8
    {
        None,           // fighting
        FeastMark,      // TG1 the mark is out: he still fights
        FeastLeap,      // TG1 in the air
        Devour,         // TG2 the channel
        FelstormLeap,   // TG3 in the air to where the hard mode places him (TaragamanFight.h FelstormSpot)
        FelstormCast,   // TG3 the 2 s bar
        FelstormSpin,   // TG3 to TG5
        FelstormTail,   // TG5 the last spots are still on the floor: he fights
        NovaLeap,       // TG6 in the air to the hub
        NovaCast,       // TG6 the bar
    };

    struct FeastState
    {
        ObjectGuid prey;
        uint64 devourStartMs = 0;
        uint32 devourTicks = 0;
        bool channelDone = false;       // the channel ran its full time (OnChannelFinished)
    };

    struct StormState
    {
        uint64 startMs = 0;             // the spin's start
        uint64 nextDriftMs = 0;
        uint32 pulses = 0;
        uint32 spots = 0;
        uint32 spotsRefused = 0;
        uint32 ringHits = 0;
        uint32 spotHits = 0;
        MechanicHandle ring;
        SpotRotation rotation;
    };

    struct NovaState
    {
        MechanicHandle hide;
        bool resolved = false;
        uint32 seen = 0;
        uint32 hidden = 0;
    };

public:
    explicit boss_taragaman_rework(Creature* creature)
        : BossAI(creature, BOSS_TARAGAMAN), _arena(TaragamanArena(), SelfLeash(kBoss)),
            _reach(ReachArena(), ReachLeash(kBoss)),
            _edge(kPlateauArenaPolygon, [this](Vec2 p, float) { return FloorAt(p); }) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
        // Last: never an attackable state behind a closed gate, never a closed one after it opened (section 3.2 item
        // 3).
        ApplyTaragamanGate(me);
    }

    void DoAction(int32 action) override
    {
        if (ActionHook())
            ActionHook()(me, action);
        if ((action == ACTION_RFC_HARD_MODE_ARMED || action == ACTION_RFC_HARD_MODE_CLEARED) && !me->IsEngaged()
            && IdleHook())
            IdleHook()(me);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        bool const heroic = IsHeroicMap(me);
        bool const armed = heroic && instance && instance->GetData(DATA_HARD_MODE) != 0;
        _engaged = true;
        _clockMs = 0;
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_TARAGAMAN;
        Mechanic::BeginEncounter(me, options);
        if (armed)
        {
            _hardMode = CreateTaragamanHardMode(me);
            if (!_hardMode)
                Log("hardmode-missing", "the flag is set but no hard mode is registered: plain heroic");
        }
        _mode = ModeFor(heroic, _hardMode != nullptr);
        _timeline.Start(_mode, _clockMs);
        _uppercutAtMs = urand(Tune::kUppercutFirstMinMs, Tune::kUppercutFirstMaxMs);
        _arena.Engage(me);
        Talk(YELL_TARAGAMAN_AGGRO);
        if (_hardMode)
            _hardMode->OnEngage(*this);
        Describe();
        OnBossPull(me, kBoss, _hardMode != nullptr);    // after OnEngage: the health the hard mode set
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        uint32 const stacks = _gorged;      // his auras are gone already
        Cleanup(true);
        BossAI::JustDied(killer);
        Talk(YELL_TARAGAMAN_DEATH);
        Log("death", Acore::StringFormat("gorged={} killer={}", stacks,
            killer ? killer->GetName() : std::string("none")));
    }

    // The spots' stalkers and the hard mode's units join the summon list (despawned on reset, evade and death) but not
    // the fight: the hard mode decides what its own units do.
    void JustSummoned(Creature* summon) override
    {
        if (summon)
            summons.Summon(summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        BossAI::SummonedCreatureDies(summon, killer);
        if (_hardMode && _engaged && summon)
            _hardMode->OnSummonDied(*this, summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
        BossAI::DamageTaken(attacker, damage, type, mask);
    }

    // A kick (or a silence) on Devour ends it (rule 13); his own stops are guarded by _ownInterrupt.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!_ownInterrupt && spell && spell->Id == SPELL_TG_DEVOUR && _act == Act::Devour)
            EndFeast("interrupted");
    }

    // The channel ran out: the last tick is due on this update (UpdateDevour).
    void OnChannelFinished(SpellInfo const* spell) override
    {
        BossAI::OnChannelFinished(spell);
        if (spell && spell->Id == SPELL_TG_DEVOUR && _act == Act::Devour)
            _feast.channelDone = true;
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsEngaged() && me->IsAlive() && !me->IsInEvadeMode() && IdleHook())
            IdleHook()(me);

        me->SetAssistanceTimer(0);      // no assist calls (R-1-FW MAJ-1; before UpdateVictim, every tick)
        if (!UpdateVictim())
            return;
        _clockMs += diff;
        // While he holds no target the leap, the spin and the cast place him (every one of them ends within 8 s) and
        // the guards wait, or they would turn him meanwhile.
        if (!HoldsNoTarget() && (!_arena.Update(me, diff) || !_reach.Update(me, diff)))
            return;     // off his arena, or nobody in reach for 10 s: evading
        if (!_engaged)
            return;
        _edge.HoldBackstep(me);

        if (_hardMode)
            _hardMode->OnUpdate(*this, diff);
        UpdateAct();
        if (!_engaged)
            return;
        StartDueBeat();

        if (HoldsNoTarget() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        _edge.Update(me, _arena, _reach);
        UpdateUppercut();
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    bool HoldsNoTarget() const
    {
        switch (_act)
        {
            case Act::None:
            case Act::FeastMark:
            case Act::FelstormTail:
                return false;
            default:
                return true;
        }
    }

    void StartDueBeat()
    {
        std::optional<Beat> const beat = _timeline.Next(_clockMs, !_hardMode || _hardMode->FeastByTimer(*this));
        if (!beat)
            return;
        switch (*beat)
        {
            case Beat::Felstorm:
                BeginFelstorm();
                break;
            case Beat::Nova:
                BeginNova();
                break;
            case Beat::Feast:
                if (Player* prey = LowestPrey())
                    BeginFeast(prey);
                else
                {
                    // Section 7 #24 A: nobody on the plateau within reach, no Feast until its next time.
                    _timeline.Skip(Beat::Feast, _clockMs);
                    Log("feast-skip", "no prey on the plateau");
                }
                break;
        }
    }

    void UpdateAct()
    {
        switch (_act)
        {
            case Act::None:
                break;
            case Act::FeastMark:
                UpdateFeastMark();
                break;
            case Act::FeastLeap:
                if (Landed())
                    FeastLands();
                break;
            case Act::Devour:
                UpdateDevour();
                break;
            case Act::FelstormLeap:
                if (Landed())
                {
                    me->CastSpell(me, SPELL_TG_LEAP_LOOK, true);
                    me->StopMoving();
                    CastFelstorm();
                }
                break;
            case Act::FelstormCast:
                if (_clockMs >= _actUntilMs)
                    StartSpin();
                break;
            case Act::FelstormSpin:
                UpdateSpin();
                break;
            case Act::FelstormTail:
                if (_clockMs >= _actUntilMs)
                    EndFelstorm();
                break;
            case Act::NovaLeap:
                if (Landed())
                    NovaLands();
                break;
            case Act::NovaCast:
                if (_nova.resolved)
                    EndNova("resolved");
                else if (_clockMs >= _actUntilMs)
                    EndNova("backstop");
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG1 Feast
    // ----------------------------------------------------------------------------------------------------------------

    void BeginFeast(Player* prey)
    {
        uint32 const markMs = Tune::kFeastMarkMs(_mode);
        _timeline.Fired(Beat::Feast, _clockMs);
        _act = Act::FeastMark;
        _actUntilMs = _clockMs + markMs;
        _feast = FeastState{};
        _feast.prey = prey->GetGUID();
        _lastFeastMs = std::max<uint64>(1, _clockMs);
        me->CastSpell(prey, SPELL_TG_FEAST_MARK, true);
        DungeonKit::ShortenAura(prey, SPELL_TG_FEAST_MARK, me->GetGUID(), Ms(markMs));
        Talk(EMOTE_TARAGAMAN_FEAST, prey);
        if (HasDevour(_mode))
            Mechanic::NoteNextCastIn(me, SPELL_TG_DEVOUR, Ms(markMs + kLeapMinMs));
        Log("feast", Acore::StringFormat("prey={} health={:.0f}% mark={}ms bite={:.0f}% gorged={}", prey->GetName(),
            prey->GetHealthPct(), markMs, Tune::kFeastBitePct(_mode), GorgedStacks()));
        if (_hardMode)
            _hardMode->OnFeastStart(*this, prey);
    }

    void UpdateFeastMark()
    {
        Player* prey = Prey();
        if (!prey || !FeastEligible(prey))
        {
            EndFeast("prey dead or off the plateau");   // section 7 #30 A: the next one on its timer
            return;
        }
        if (_clockMs < _actUntilMs)
            return;
        Vec2 const to = LeapLanding(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(prey));
        StopFighting();
        _act = Act::FeastLeap;
        Leap(to, FloorAt(to).value_or(kHub.z), "feast");
    }

    void FeastLands()
    {
        me->CastSpell(me, SPELL_TG_LEAP_LOOK, true);
        Player* prey = Prey();
        if (!prey)
        {
            EndFeast("prey gone in flight");
            return;
        }
        float const health = prey->GetHealthPct();      // at the landing, before the bite
        bool const gorges = Gorges(health);
        uint32 const bite = ScriptHit(prey, SPELL_TG_BITE, Tune::kFeastBitePct(_mode));
        Log("bite", Acore::StringFormat("prey={} health={:.0f}% damage={} gorge={} distance={:.1f}", prey->GetName(),
            health, bite, gorges ? 1 : 0, me->GetExactDist2d(prey)));
        if (gorges)
            Gorge(Tune::kGorgeHealPct);
        if (!_engaged || _act != Act::FeastLeap)
            return;     // the bite ended the fight
        if (HasDevour(_mode) && prey->IsAlive())
            StartDevour(prey);
        else
            EndFeast("bitten");
    }

    Player* Prey() const
    {
        Player* prey = ObjectAccessor::GetPlayer(*me, _feast.prey);
        return CountsAsPlayer(prey) ? prey : nullptr;
    }

    // The Feast is over, however it ends: the mark and the channel off, back to his threat target.
    void EndFeast(char const* why)
    {
        bool const held = HoldsNoTarget();
        StopDevourChannel();
        if (Player* prey = ObjectAccessor::GetPlayer(*me, _feast.prey))
        {
            prey->RemoveAurasDueToSpell(SPELL_TG_FEAST_MARK, me->GetGUID());
            prey->RemoveAurasDueToSpell(SPELL_TG_DEVOUR, me->GetGUID());
        }
        Log("feast-end", Acore::StringFormat("why={} devour-ticks={} health={:.1f}%", why, _feast.devourTicks,
            me->GetHealthPct()));
        _act = Act::None;
        _feast = FeastState{};
        _timeline.Ended(_clockMs);
        if (held)
            ResumeFighting();
        if (_hardMode)
            _hardMode->OnFeastEnd(*this);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG2 Devour (heroic, hard mode)
    // ----------------------------------------------------------------------------------------------------------------

    // A real channel (not triggered), so it shows, can be kicked, and a kick's lockout counts. The ticks run on his own
    // clock while the channel lives.
    void StartDevour(Player* prey)
    {
        me->StopMoving();
        _act = Act::Devour;
        _feast.devourStartMs = _clockMs;
        SpellCastResult const result = me->CastSpell(prey, SPELL_TG_DEVOUR, false);
        if (result != SPELL_CAST_OK)
        {
            EndFeast("devour refused (a lockout, or no target)");
            return;
        }
        Talk(EMOTE_TARAGAMAN_DEVOUR, prey);
        Log("devour", Acore::StringFormat("prey={} health={:.0f}% tick={:.0f}% heal={:.0f}%", prey->GetName(),
            prey->GetHealthPct(), Tune::kDevourTickPct(_mode), Tune::kDevourHealPct));
    }

    bool Channeling() const
    {
        Spell const* channel = me->GetCurrentSpell(CURRENT_CHANNELED_SPELL);
        return channel && channel->GetSpellInfo()->Id == SPELL_TG_DEVOUR && channel->getState() != SPELL_STATE_FINISHED;
    }

    void UpdateDevour()
    {
        Player* prey = Prey();
        if (!prey)
        {
            EndFeast("prey dead");
            return;
        }
        bool const alive = Channeling() || _feast.channelDone;
        while (alive && _feast.devourTicks < Tune::kDevourTicks
            && (_feast.channelDone || _clockMs >= _feast.devourStartMs
                + uint64(_feast.devourTicks + 1) * Tune::kDevourTickMs))
        {
            ++_feast.devourTicks;
            uint32 const damage = ScriptHit(prey, SPELL_TG_DEVOUR_TICK, Tune::kDevourTickPct(_mode));
            if (!_engaged || _act != Act::Devour)
                return;     // the tick ended the fight or the Feast
            Heal(SPELL_TG_DEVOUR_HEAL, Tune::kDevourHealPct);
            Log("devour-tick", Acore::StringFormat("tick={} prey={} damage={}", _feast.devourTicks, prey->GetName(),
                damage));
            if (!prey->IsAlive())
            {
                EndFeast("prey eaten");
                return;
            }
        }
        if (_feast.devourTicks >= Tune::kDevourTicks)
            EndFeast("devoured");
        else if (!alive)
            EndFeast("channel lost");   // Divine Shield, Ice Block, out of its 100 yd
    }

    void StopDevourChannel()
    {
        if (!Channeling())
            return;
        _ownInterrupt = true;
        me->InterruptSpell(CURRENT_CHANNELED_SPELL, true);
        _ownInterrupt = false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG3 Felstorm, TG4 fel pulses, TG5 fel spots
    // ----------------------------------------------------------------------------------------------------------------

    void BeginFelstorm()
    {
        _timeline.Fired(Beat::Felstorm, _clockMs);
        _storm = StormState{};
        StopFighting();
        if (_hardMode)
            if (std::optional<Position> const spot = _hardMode->FelstormSpot(*this))
            {
                _act = Act::FelstormLeap;
                Leap({ spot->GetPositionX(), spot->GetPositionY() }, spot->GetPositionZ(), "felstorm");
                return;
            }
        CastFelstorm();
    }

    // The bar and the ring, where he stands.
    void CastFelstorm()
    {
        _act = Act::FelstormCast;
        _actUntilMs = _clockMs + Tune::kFelstormCastMs;
        DungeonKit::CastBar(me, SPELL_TG_FELSTORM_CAST, nullptr, EMOTE_TARAGAMAN_FELSTORM);

        float const pct = Tune::kFelstormTickPct(_mode) * DamageFactor();
        MechanicRef ring = Mechanic::Circle(me, me, Tune::kFelstormRadius(_mode), Ms(Tune::kFelstormCastMs));
        ring.Persistent(Ms(Tune::kFelstormSpinMs(_mode)), Ms(Tune::kFelstormTickMs)).Damage(pct).TankDamage(pct)
            .School(SPELL_SCHOOL_NORMAL).Spell(SPELL_TG_FELSTORM).Within(TaragamanFloorBounds()).Tag(TAG_TG_RING)
            .OnResolve(OnTaragaman([](boss_taragaman_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai._storm.ringHits += static_cast<uint32>(r.hits.size());
            }));
        if (ring.IsValid())
        {
            _storm.ring = ring.Handle();
            Track(_storm.ring);
        }
        Log("felstorm", Acore::StringFormat("radius={:.0f} tick={:.1f}% spin={}ms at=({:.1f}, {:.1f}) registered={}",
            Tune::kFelstormRadius(_mode), pct, Tune::kFelstormSpinMs(_mode), me->GetPositionX(), me->GetPositionY(),
            ring.IsValid() ? 1 : 0));
    }

    void StartSpin()
    {
        _act = Act::FelstormSpin;
        _storm.startMs = _clockMs;
        _storm.nextDriftMs = _clockMs;
        _actUntilMs = _clockMs + Tune::kFelstormSpinMs(_mode);
        me->CastSpell(me, SPELL_TG_FELSTORM_SPIN, true);
        std::vector<uint64> keys;
        for (Player* player : FightPlayers())
            keys.push_back(player->GetGUID().GetRawValue());
        _storm.rotation.Shuffle(std::move(keys), RandBelow);
        if (_hardMode)
            _hardMode->OnFelstormStart(*this);
        UpdateSpin();
    }

    void UpdateSpin()
    {
        while (_storm.spots < SpotCount(_mode) && _clockMs >= _storm.startMs + SpotAtMs(_storm.spots))
        {
            ++_storm.spots;
            FelSpot(nullptr);
        }
        while (_storm.pulses < PulseCount(_mode)
            && _clockMs >= _storm.startMs + uint64(_storm.pulses + 1) * Tune::kFelstormTickMs)
        {
            ++_storm.pulses;
            FelPulse();
            if (_act != Act::FelstormSpin)
                return;     // a pulse ended the fight
        }
        if (_clockMs >= _actUntilMs)
        {
            EndSpin();
            return;
        }
        if (_hardMode && _clockMs >= _storm.nextDriftMs)
        {
            _storm.nextDriftMs = _clockMs + Tune::kDriftRepickMs;
            Drift();
        }
    }

    // TG4: everyone on the plateau, unavoidable (no Weakened, nothing registered: bots must not flee it).
    void FelPulse()
    {
        float const pct = Tune::kPulsePct(_mode);
        uint32 hit = 0;
        for (Player* player : FightPlayers())
            if (OnPlateau(player))
            {
                ScriptHit(player, SPELL_TG_FEL_PULSE, pct);
                ++hit;
            }
        Log("pulse", Acore::StringFormat("pulse={}/{} hit={} pct={:.1f}", _storm.pulses, PulseCount(_mode), hit,
            pct * DamageFactor()));
    }

    // TG5: one spot off the next player of the rotation (or `forced`, the GM test), its center on the arena's floor.
    bool FelSpot(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            std::optional<uint64> const key = _storm.rotation.Next([this](uint64 raw)
            {
                Player* player = ObjectAccessor::GetPlayer(*me, ObjectGuid(raw));
                return CountsAsPlayer(player) && player->IsInCombatWith(me) && OnPlateau(player);
            });
            if (key)
                target = ObjectAccessor::GetPlayer(*me, ObjectGuid(*key));
        }
        if (!target)
        {
            ++_storm.spotsRefused;
            return false;
        }

        Vec2 const at = DungeonKit::PlaneOf(target);
        DungeonKit::FloorSpotRules rules;
        rules.near = at;
        rules.minRange = 0.f;
        rules.maxRange = Tune::kSpotOffsetMax(_mode);
        rules.tries = Tune::kSpotRerolls;
        DungeonKit::FloorProbe probe;
        probe.z = kFloorMidZ;
        probe.zBand = kFloorBandYd;
        probe.probeUp = kFloorProbeUpYd;
        static DungeonKit::Arena const arena = TaragamanArena();
        std::optional<Position> spot = DungeonKit::PickFloorSpot(me, &arena, rules, probe);
        if (!spot)
        {
            // Standing at a rim: the nearest point of the arena (2 yd in) instead.
            Vec2 const in = ClampInto(kPlateauArenaPolygon, at);
            spot = DungeonKit::ToPosition(in, FloorAt(in).value_or(kHub.z));
        }

        float const pct = Tune::kSpotPct(_mode) * DamageFactor();
        uint32 const warn = Tune::kSpotWarnMs(_mode);
        ObjectGuid stalkerGuid;
        if (Creature* stalker = me->SummonCreature(NPC_RFC_STALKER, *spot, TEMPSUMMON_TIMED_DESPAWN,
            warn + kSpotStalkerMs))
            stalkerGuid = stalker->GetGUID();
        MechanicRef ref = Mechanic::Circle(me, *spot, Tune::kSpotRadius(_mode), Ms(warn));
        ref.School(SPELL_SCHOOL_FIRE).Spell(SPELL_TG_FEL_SPOT).Damage(pct).TankDamage(pct).Weakened()
            .Within(TaragamanFloorBounds()).Tag(TAG_TG_SPOT)
            .OnResolve(OnTaragaman([stalkerGuid](boss_taragaman_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai._storm.spotHits += static_cast<uint32>(r.hits.size());
                Creature* stalker = r.fizzled ? nullptr : ObjectAccessor::GetCreature(*ai.me, stalkerGuid);
                if (stalker)
                    stalker->CastSpell(stalker, SPELL_TG_FEL_SPOT_LOOK, true);
            }));
        if (!ref.IsValid())
        {
            ++_storm.spotsRefused;
            return false;
        }
        Track(ref.Handle());
        return true;
    }

    // The hard mode's ring drift: he (and the ring on him) walks a straight floor line.
    void Drift()
    {
        std::optional<Position> const to = _hardMode->DriftTarget(*this);
        me->StopMoving();
        if (!to)
            return;
        std::vector<DungeonKit::FloorPathPoint> const path = DungeonKit::FloorPathOnMap(me, DungeonKit::PlaneOf(me),
            { to->GetPositionX(), to->GetPositionY() }, me->GetPositionZ());
        DungeonKit::MoveAlongFloor(me, path, Tune::kDriftSpeed);
    }

    void EndSpin()
    {
        me->RemoveAurasDueToSpell(SPELL_TG_FELSTORM_SPIN);
        me->StopMoving();
        Log("felstorm-end", Acore::StringFormat("ring-hits={} pulses={} spots={} refused={}", _storm.ringHits,
            _storm.pulses, _storm.spots, _storm.spotsRefused));
        _act = Act::FelstormTail;
        _actUntilMs = _storm.startMs + FelstormOverMs(_mode);
        ResumeFighting();
        if (_hardMode)
            _hardMode->OnFelstormEnd(*this);
        if (_act == Act::FelstormTail && _clockMs >= _actUntilMs)
            EndFelstorm();
    }

    void EndFelstorm()
    {
        _act = Act::None;
        _timeline.Ended(_clockMs);
        if (SpotCount(_mode))
            Log("spots-end", Acore::StringFormat("spots={} hits={}", _storm.spots - _storm.spotsRefused,
                _storm.spotHits));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG6 Searing Nova
    // ----------------------------------------------------------------------------------------------------------------

    void BeginNova()
    {
        _timeline.Fired(Beat::Nova, _clockMs);
        _nova = NovaState{};
        StopFighting();
        _act = Act::NovaLeap;
        Talk(EMOTE_TARAGAMAN_NOVA);
        Vec2 const hub = kHub.XY();
        Leap(hub, FloorAt(hub).value_or(kHub.z), "nova");
        if (_hardMode)
            _hardMode->OnNovaStart(*this);
    }

    // At the hub: the spikes rise, the Hide is registered (after the landing: rule 26) and the bar starts.
    void NovaLands()
    {
        me->CastSpell(me, SPELL_TG_LEAP_LOOK, true);
        if (me->GetExactDist2d(kHub.x, kHub.y) > kLeapSkipYd * 2.f)
        {
            // The jump did not take (rule 26: the Hide's source is the hub).
            me->NearTeleportTo(kHub.x, kHub.y, kHub.z, me->GetOrientation());
            Log("nova-teleport", "the leap to the hub did not land");
        }
        me->StopMoving();

        std::vector<std::size_t> const points = PickSpikes(Tune::kNovaSpikes(_mode), RandBelow);
        BossMechanics::HideSpec spec(me);
        spec.Range(Tune::kNovaRangeYd).Eye(Tune::kNovaEyeYd);
        std::string where;
        for (std::size_t const point : points)
        {
            GameObject* spike = RaiseSpike(point);
            if (!spike)
                continue;
            spec.Blocker(spike->GetGUID(), spike->GetPosition(), Tune::kSpikeBlockerYd);
            where += (where.empty() ? "" : ",") + std::to_string(point);
        }

        uint32 const castMs = Tune::kNovaCastMs(_mode);
        float const pct = Tune::kNovaPct(_mode) * DamageFactor();
        MechanicRef ref = Mechanic::Hide(me, spec, Ms(castMs));
        ref.School(SPELL_SCHOOL_FIRE).Spell(SPELL_TG_NOVA).Damage(pct).TankDamage(pct).Within(TaragamanFloorBounds())
            .Tag(NovaTag(_mode))
            .OnResolve(OnTaragaman([](boss_taragaman_rework& ai, BossMechanics::ResolveResult const& r)
            {
                ai._nova.resolved = true;
                ai._nova.seen = static_cast<uint32>(r.hits.size());
                ai._nova.hidden = static_cast<uint32>(r.cleared.size());
            }));
        if (!ref.IsValid())
        {
            EndNova("refused");
            return;
        }
        _nova.hide = ref.Handle();
        Track(_nova.hide);
        _act = Act::NovaCast;
        _actUntilMs = _clockMs + castMs + kNovaBackstopMs;
        DungeonKit::CastBar(me, NovaBarSpell(_mode));
        Log("nova", Acore::StringFormat("spikes=[{}] cast={}ms pct={:.1f} at=({:.1f}, {:.1f}, {:.1f})", where, castMs,
            pct, me->GetPositionX(), me->GetPositionY(), me->GetPositionZ()));
    }

    // One Searing Spike at its point, its rock burst and dirt over the pop.
    GameObject* RaiseSpike(std::size_t point)
    {
        Point3 const& p = kSpikePoints[point];
        float const z = FloorAt(p.XY()).value_or(p.z);
        GameObject* spike = me->SummonGameObject(GO_RFC_SEARING_SPIKE, p.x, p.y, z, kSpikeYaw, 0.f, 0.f, 0.f, 0.f,
            kSpikeBackstopSec);
        if (!spike)
        {
            Log("spike-refused", Acore::StringFormat("point={} the object was not created", point));
            return nullptr;
        }
        _spikes.push_back(spike->GetGUID());
        me->CastSpell(p.x, p.y, z, SPELL_TG_SPIKE_LOOK, true);
        me->CastSpell(p.x, p.y, z, SPELL_TG_SPIKE_DIRT, true);
        return spike;
    }

    void ClearSpikes()
    {
        if (Map* map = me->GetMap())
            for (ObjectGuid const& guid : _spikes)
                if (GameObject* spike = map->GetGameObject(guid))
                    spike->Delete();
        _spikes.clear();
    }

    void EndNova(char const* why)
    {
        if (!_nova.resolved && _nova.hide)
            Mechanic::Cancel(me, _nova.hide);
        Log("nova-end", Acore::StringFormat("why={} seen={} hidden={}", why, _nova.seen, _nova.hidden));
        ClearSpikes();
        _act = Act::None;
        _nova = NovaState{};
        _timeline.Ended(_clockMs);
        ResumeFighting();
        if (_hardMode)
            _hardMode->OnNovaEnd(*this);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG10 Uppercut
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateUppercut()
    {
        if (_clockMs < _uppercutAtMs)
            return;
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
        {
            _uppercutAtMs = _clockMs + kUppercutRetryMs;
            return;
        }
        _uppercutAtMs = _clockMs + Tune::kUppercutEveryMs;
        Uppercut(victim);
    }

    void Uppercut(Unit* target)
    {
        SpellCastResult const result = me->CastSpell(target, SPELL_UPPERCUT, false);
        Log("uppercut", Acore::StringFormat("target={} result={}", target->GetName(), uint32(result)));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Moves, hits, heals
    // ----------------------------------------------------------------------------------------------------------------

    // The plateau's floor under a point (the mesh floor's band; nullopt: none there).
    std::optional<float> FloorAt(Vec2 p) const
    {
        float const h = me->GetMapHeight(p.x, p.y, kFloorMidZ + kFloorProbeUpYd);
        if (h <= INVALID_HEIGHT || !OnFloorBand(h))
            return std::nullopt;
        return h;
    }

    // A leap to a floor point (the look now, and again at the landing).
    void Leap(Vec2 to, float z, char const* what)
    {
        Vec2 const from = DungeonKit::PlaneOf(me);
        float const distance = DungeonKit::Distance(from, to);
        _leap = distance > kLeapSkipYd;
        if (_leap)
        {
            uint32 const flightMs = LeapMs(distance);
            me->CastSpell(me, SPELL_TG_LEAP_LOOK, true);
            DungeonKit::JumpTo(me, DungeonKit::ToPosition(to, z), distance * 1000.f / static_cast<float>(flightMs));
            _landAtMs = _clockMs + flightMs;
        }
        else
            _landAtMs = _clockMs;
        Log("leap", Acore::StringFormat("for={} from=({:.1f}, {:.1f}) to=({:.1f}, {:.1f}, {:.1f}) flight={}ms", what,
            from.x, from.y, to.x, to.y, z, _landAtMs - _clockMs));
    }

    bool Landed() const
    {
        if (_clockMs < _landAtMs)
            return false;
        return !_leap || me->movespline->Finalized() || _clockMs >= _landAtMs + kLeapGraceMs;
    }

    // He lets go of his target: passive, no chase, his threat list untouched (rule 35).
    void StopFighting()
    {
        _edge.Reset();
        me->SetReactState(REACT_PASSIVE);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
    }

    // Back to his top-threat unit, never to whoever the reach guard had turned him to.
    void ResumeFighting()
    {
        if (!me->IsAlive() || !me->IsEngaged())
            return;
        me->SetReactState(REACT_AGGRESSIVE);
        Unit* const fixed = me->GetThreatMgr().GetFixateTarget();
        if (fixed && fixed->GetGUID() == _reach.SwitchedTo())
            me->GetThreatMgr().ClearFixate();
        if (Unit* victim = me->SelectVictim())
            AttackStart(victim);
    }

    // A percent of the reference row (the tank's on the tank) on one player, with the Gorged factor; the amount is the
    // spell's base point. Returns it.
    uint32 ScriptHit(Player* target, uint32 spellId, float pct)
    {
        uint32 const amount = DungeonKit::RefFlatOn(me, target, pct * DamageFactor());
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(amount));
        me->CastSpell(target, spellId, args);
        return amount;
    }

    void Heal(uint32 spellId, float pct)
    {
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(PctOfHealth(me->GetMaxHealth(), pct)));
        me->CastSpell(me, spellId, args);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        if (HasDevour(_mode))
            d.interrupts.emplace_back(NPC_TARAGAMAN, SPELL_TG_DEVOUR, kDevourKickPriority,
                Ms(DevourInterruptEveryMs(_mode)));
        d.ignores.emplace_back(NPC_RFC_STALKER);
        if (_hardMode)
            _hardMode->DescribeExtra(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TaragamanFight (the hard mode's view, TaragamanFight.h)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Taragaman() override { return me; }
    Mode FightMode() const override { return _mode; }
    TaragamanHardMode* ActiveHardMode() override { return _hardMode.get(); }
    uint64 ClockMs() const override { return _engaged ? _clockMs : 0; }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> out;
        if (!me->IsEngaged())
            return out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && player->IsInMap(me))
                out.push_back(player);
        }
        return out;
    }

    bool FeastEligible(Player const* player) const override
    {
        return player && player->IsInMap(me) && PreyEligible(CountsAsPlayer(player), OnPlateau(player),
            player->GetExactDist2d(kHub.x, kHub.y));
    }

    Player* LowestPrey() override
    {
        std::vector<Player*> eligible;
        std::vector<float> health;
        for (Player* player : FightPlayers())
            if (FeastEligible(player))
            {
                eligible.push_back(player);
                health.push_back(player->GetHealthPct());
            }
        std::optional<std::size_t> const pick = PickPrey(health, RandBelow);
        return pick ? eligible[*pick] : nullptr;
    }

    bool StartFeast(Player* prey) override
    {
        if (!_engaged || !_timeline.MayStart(Beat::Feast, _clockMs) || _timeline.SetPieceDue(_clockMs)
            || !FeastEligible(prey))
            return false;
        BeginFeast(prey);
        return true;
    }

    bool FeastActive() const override
    {
        return _act == Act::FeastMark || _act == Act::FeastLeap || _act == Act::Devour;
    }

    uint64 LastFeastMs() const override { return _lastFeastMs; }

    bool StartFelstorm() override
    {
        if (!_engaged || !_timeline.MayStart(Beat::Felstorm, _clockMs))
            return false;
        BeginFelstorm();
        return true;
    }

    bool StartNova() override
    {
        if (!_engaged || !_timeline.MayStart(Beat::Nova, _clockMs))
            return false;
        BeginNova();
        return true;
    }

    bool SetPieceActive() const override { return _timeline.SetPieceRunning(); }

    void HoldSetPieces(bool hold) override
    {
        _timeline.HoldSetPieces(hold, _clockMs);
        Log(hold ? "setpieces-held" : "setpieces-released");
    }

    void SetFeastHold(uint32 ms) override
    {
        _timeline.SetFeastHold(ms);
    }

    void NotePhaseChange(uint32 phase) override
    {
        _timeline.PhaseChanged(_clockMs);
        Mechanic::SetPhase(me, phase);
        Log("phase", Acore::StringFormat("phase={} health={:.1f}%", phase, me->GetHealthPct()));
    }

    void Gorge(float healPct) override
    {
        if (!_engaged || !me->IsAlive())
            return;
        Heal(SPELL_TG_GORGE_HEAL, healPct);
        _gorged = DungeonKit::AddStacks(me, SPELL_TG_GORGED, 1, me, Tune::kGorgedCap(_mode));
        Log("gorge", Acore::StringFormat("stacks={} heal={:.0f}% health={:.1f}%", _gorged, healPct,
            me->GetHealthPct()));
    }

    uint32 GorgedStacks() const override
    {
        return DungeonKit::Stacks(me, SPELL_TG_GORGED, me->GetGUID());
    }

    float DamageFactor() const override
    {
        return DamageMult(GorgedStacks());
    }

    Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs) override
    {
        return despawnMs ? me->SummonCreature(entry, at, TEMPSUMMON_TIMED_DESPAWN, despawnMs)
            : me->SummonCreature(entry, at, TEMPSUMMON_MANUAL_DESPAWN);
    }

    void Track(MechanicHandle handle) override
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 48);
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
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest rfc taragaman` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Feast,
        Felstorm,
        Nova,
        Spot,
        Gorge,
        Uppercut,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM).
    std::string TestFire(TestMechanic mechanic, Player* who)
    {
        if (!me->IsEngaged() || !_engaged)
            return "Taragaman must be in combat (the picks read his threat list, the mechanics his encounter).";
        bool const starts = mechanic == TestMechanic::Feast || mechanic == TestMechanic::Felstorm
            || mechanic == TestMechanic::Nova;
        if (starts && _timeline.Running())
            return "A Feast, Felstorm or Nova is running; try again when it ends.";
        switch (mechanic)
        {
            case TestMechanic::Feast:
            {
                Player* prey = who && FeastEligible(who) ? who : LowestPrey();
                if (!prey)
                    return "Nobody alive (and not .gm on) on the plateau within 40 yd of the hub.";
                BeginFeast(prey);
                break;
            }
            case TestMechanic::Felstorm:
                BeginFelstorm();
                break;
            case TestMechanic::Nova:
                BeginNova();
                break;
            case TestMechanic::Spot:
                if (!SpotCount(_mode))
                    return "No fel spots on normal (.dbtest rfc taragaman heroic 1).";
                if (!CountsAsPlayer(who) || !FelSpot(who))
                    return "The spot needs a living player (.gm off).";
                break;
            case TestMechanic::Gorge:
                Gorge(Tune::kGorgeHealPct);
                break;
            case TestMechanic::Uppercut:
                if (!me->GetVictim())
                    return "He holds no target now.";
                Uppercut(me->GetVictim());
                break;
        }
        return {};
    }

    // The heroic form on any map until the end of the pull (the reference row stays the map's). False: not fighting, or
    // a beat is running.
    bool TestHeroic(bool heroic)
    {
        if (!_engaged || _hardMode || _timeline.Running())
            return false;
        _mode = ModeFor(heroic, false);
        _timeline.SetMode(_mode);
        Describe();
        return true;
    }

    std::string TestState() const
    {
        auto in = [this](Beat beat) -> int64
        {
            return static_cast<int64>(_timeline.DueMs(beat)) - static_cast<int64>(_clockMs);
        };
        return Acore::StringFormat("clock={}s mode={} hardmode={} act={} gorged={} next felstorm={}ms nova={}ms "
            "feast={}ms feast-hold={}ms held={} spikes={} handles={}", _clockMs / 1000, uint32(_mode),
            _hardMode ? 1 : 0, uint32(_act), GorgedStacks(), in(Beat::Felstorm), in(Beat::Nova), in(Beat::Feast),
            _timeline.FeastHoldUntilMs() > _clockMs ? _timeline.FeastHoldUntilMs() - _clockMs : 0,
            _timeline.Held() ? 1 : 0, _spikes.size(), _live.size());
    }

private:
    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still in the same fight. Captures the
    // map, the guid and the cleanup count only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnTaragaman(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        uint32 const generation = _generation;
        return [map, guid, generation, fn](BossMechanics::ResolveResult const& result)
        {
            Creature* boss = map ? map->GetCreature(guid) : nullptr;
            auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_taragaman_rework*>(boss->AI()) : nullptr;
            if (ai && ai->_generation == generation)
                fn(*ai, result);
        };
    }

    // The fight's state: nothing registered, no spike, stalker, mark, channel or aura of it, his kit given back (Reset,
    // evade, death). The hard mode undoes its own changes in OnEnd first.
    void Cleanup(bool died)
    {
        ++_generation;
        _engaged = false;
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        StopDevourChannel();
        ClearSpikes();
        summons.DespawnAll();
        if (instance)
            for (uint32 const spell : { uint32(SPELL_TG_FEAST_MARK), uint32(SPELL_TG_DEVOUR) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        for (uint32 const spell : { uint32(SPELL_TG_GORGED), uint32(SPELL_TG_FELSTORM_SPIN) })
            me->RemoveAurasDueToSpell(spell);
        if (me->IsAlive())
            me->SetReactState(REACT_AGGRESSIVE);    // Reset's gate check comes after
        _arena.Reset();
        _reach.Reset();
        _edge.Reset();
        _timeline.Stop();
        _act = Act::None;
        _feast = FeastState{};
        _storm = StormState{};
        _nova = NovaState{};
        _mode = Mode::Normal;
        _clockMs = 0;
        _actUntilMs = 0;
        _landAtMs = 0;
        _lastFeastMs = 0;
        _uppercutAtMs = 0;
        _gorged = 0;
        _leap = false;
    }

    DungeonKit::ArenaGuard _arena;  // himself on his arena
    DungeonKit::ArenaGuard _reach;  // whom he can reach from it
    ArenaEdge _edge;                // ... and how he fights at its edge
    std::unique_ptr<TaragamanHardMode> _hardMode;
    Timeline _timeline;
    FeastState _feast;
    StormState _storm;
    NovaState _nova;
    std::vector<ObjectGuid> _spikes;
    std::vector<MechanicHandle> _live;
    Mode _mode = Mode::Normal;
    Act _act = Act::None;
    uint64 _clockMs = 0;            // ms since the pull: every timer of the fight
    uint64 _actUntilMs = 0;
    uint64 _landAtMs = 0;
    uint64 _lastFeastMs = 0;
    uint64 _uppercutAtMs = 0;
    uint32 _gorged = 0;             // the last Gorge's stacks (the death line)
    uint32 _generation = 0;         // bumped by every cleanup: a stale callback does nothing
    bool _engaged = false;
    bool _leap = false;             // the current leap left the floor
    bool _ownInterrupt = false;
};

namespace
{
    boss_taragaman_rework* TaragamanAI(ChatHandler* handler)
    {
        Creature* boss = RfcTest::FindBoss(handler, NPC_TARAGAMAN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_taragaman_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_taragaman_rework::TestMechanic mechanic, char const* what)
    {
        boss_taragaman_rework* ai = TaragamanAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(mechanic, handler->getSelectedPlayerOrSelf());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Taragaman: {}.", what);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return RfcTest::ShowBossInfo(handler, NPC_TARAGAMAN, BOSS_TARAGAMAN);
    }

    // Handoff section 3.7: the hard mode past the shrine and the pour (GM), through the instance's rules.
    bool HandleHardMode(ChatHandler* handler, Optional<uint32> lit)
    {
        return RfcTest::ArmHardMode(handler, lit.value_or(1) != 0);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_taragaman_rework* ai = TaragamanAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Taragaman: {}", ai->TestState());
        return true;
    }

    bool HandleFeast(ChatHandler* handler)
    {
        return Fire(handler, boss_taragaman_rework::TestMechanic::Feast,
            "Feast on the selected player, else the lowest (TG1: the mark, the leap, the bite; heroic TG2 Devour)");
    }

    bool HandleFelstorm(ChatHandler* handler)
    {
        return Fire(handler, boss_taragaman_rework::TestMechanic::Felstorm,
            "Felstorm (TG3: the cast and the ring; heroic TG4 pulses and TG5 spots)");
    }

    bool HandleNova(ChatHandler* handler)
    {
        return Fire(handler, boss_taragaman_rework::TestMechanic::Nova,
            "Searing Nova (TG6: the leap to the hub, the spikes, the cast)");
    }

    bool HandleSpot(ChatHandler* handler)
    {
        return Fire(handler, boss_taragaman_rework::TestMechanic::Spot, "one fel spot at the selected player (TG5)");
    }

    bool HandleGorge(ChatHandler* handler)
    {
        return Fire(handler, boss_taragaman_rework::TestMechanic::Gorge, "a Gorge (3% health and a Gorged stack)");
    }

    bool HandleUppercut(ChatHandler* handler)
    {
        return Fire(handler, boss_taragaman_rework::TestMechanic::Uppercut, "Uppercut on his target (TG10)");
    }

    // `.dbtest rfc taragaman heroic [0|1]`: the heroic form on a normal map until the end of the pull.
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_taragaman_rework* ai = TaragamanAI(handler);
        if (!ai)
            return false;
        if (!ai->TestHeroic(on.value_or(1) != 0))
        {
            handler->SendErrorMessage("Only in combat, with nothing running and not in the hard mode.");
            return false;
        }
        handler->SendSysMessage("Set until the end of the pull (the reference row stays the map's).");
        return true;
    }

    ChatCommandTable const& TaragamanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "hardmode", HandleHardMode, SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "feast",    HandleFeast,    SEC_GAMEMASTER, Console::No },
            { "felstorm", HandleFelstorm, SEC_GAMEMASTER, Console::No },
            { "nova",     HandleNova,     SEC_GAMEMASTER, Console::No },
            { "spot",     HandleSpot,     SEC_GAMEMASTER, Console::No },
            { "gorge",    HandleGorge,    SEC_GAMEMASTER, Console::No },
            { "uppercut", HandleUppercut, SEC_GAMEMASTER, Console::No },
            { "heroic",   HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_taragaman_rework()
{
    RegisterDungeonReworkCreatureAI(boss_taragaman_rework, RagefireChasmRework::kInstanceScriptName);
    RfcTest::RegisterBoss("taragaman", TaragamanTestCommands());
}
