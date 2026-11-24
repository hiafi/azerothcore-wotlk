/*
 * mod-dungeon-bosses, Scarlet Monastery D4: Bloodmage Thalnos (4543), "Blood Ritual". Build spec:
 * docs/dungeons/scarlet-monastery-1-graveyard.md "Bloodmage Thalnos" (TH1-TH6), handoff section 3.5 row D4, 3.6 (48k
 * normal, 300k heroic), 3.8 (the crypt: NAVMESH "Thalnos"), 3.10 (VR). Replaces SmartAI 4543 (rows 0-7, dropped by
 * WP-S0's rev; the template is bound by apps/dbc-tools source/npcs/scarlet_monastery/thalnos.py); Shadow Bolt 9613,
 * Flame Spike 8814, Flame Shock 8053 and Fire Nova 12470 are retired as his casts (his versions are copies in his
 * slice, rule 15). Pure rules: ThalnosLogic.h. The hard mode (the Desecration, WP-D4H) fights on this AI through
 * ThalnosFight.h.
 *
 *   TH1 Blood Ritual  each player a plain spell of his hits gives him a stack (once per player per cast; pool ticks
 *                     none); when a spell comes up and he holds its threshold he casts the empowered version (emote
 *                     line 3, his hands run red; the first one on normal and heroic also yells line 1) and spends
 *                     part of it: Lance needs 3 spends 1, Spike 3 / 2, Boiling Blood 4 / 2, Nova 5 / 3. Normal caps
 *                     at 10; heroic has no cap
 *   TH2 Blood Bolt    at 2 s, then every 8 s (heroic 6 s): a 2.5 s Shadow cast on the tank, 20% (heroic 30%) of the
 *                     tank row; kickable (no hit, no stack). Empowered, Blood Lance: the same cast, 30% / 40% on the
 *                     tank, and a 4 yd line from him through the tank to the crypt's wall (clipped by the floor, at
 *                     most 30 yd): everyone else in it 35% / 45% and Weakened (the tank exempt: the bolt is its hit)
 *   TH3 Flame Spike   at 6 s, then every 15 s: a 2 s bar; a random player (the tank included) carries a debuff and a
 *                     4 yd circle that follows them (the bots carry it to the edge); at the bar's end it lands, 1.5 s
 *                     later the pillar (35% / 45% and Weakened, anyone inside, the carrier too), then a pool of 5% /
 *                     8% a second for 20 s / 30 s. Empowered: three carriers
 *   TH4 Boiling Blood at 10 s, then every 15 s: a 5 s debuff on a random non-tank (the large-spread exemption), a
 *                     RunOut of 8 / 10 yd: the carrier 25% / 35%, everyone else inside 35% / 45% and Weakened.
 *                     Empowered: two carriers, apart from each other too
 *   TH5 Blood Nova    at 15 s, then every 20 s: a 3 s Shadow cast that hits every player on his ground for 15% / 20%
 *                     (designer question 1); kicked: nothing. Empowered: 25% / 35%; the first kick strips the blood
 *                     and he restarts it at once as a plain 2 s nova (a Physical bar, so the Shadow lockout of the
 *                     first kick does not stop it); a second kick stops it
 *   TH6 Blood Brand   heroic, at 12 s then every 20 s: a 12 s Magic debuff on a random player (the tank included);
 *                     each time the carrier takes damage he gains a stack, at most one a second (the dispel list)
 *
 * Kill line 2 (5 s lockout). Scorn 14693 rises on his death while game event 120 runs, normal only (SmartAI 4543 row
 * 7, section 7 #35). Boss data: Blood Nova (normal a reward, heroic expected), the empowered nova and its restart, the
 * Lance and the Bolt on the interrupt list; Blood Brand on the dispel list (heroic). Every timer runs on the AI's own
 * clock. Every firing logs one INFO line "sm thalnos <mechanic> ..." (module.dungeonbosses); `.dbtest sm thalnos ...`
 * fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "GameEventMgr.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MechanicRegistry.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ThalnosFight.h"
#include "ThalnosLogic.h"
#include "ThreatManager.h"
#include <algorithm>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmThalnos;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "thalnos";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    ThalnosHardModeFactory& HardModeFactory()
    {
        static ThalnosHardModeFactory factory;
        return factory;
    }

    ThalnosIdleHook& IdleHook()
    {
        static ThalnosIdleHook hook;
        return hook;
    }

    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_SM_STALKER) != nullptr;
    }

    // The lawn the hard mode moves the fight to (the Desecration's lawn region: the cut disc, RF-1 m-4).
    Arena LawnArena()
    {
        return Arena(CouncilLawnRegion());
    }

    std::vector<Position> CryptPositions()
    {
        std::vector<Position> out;
        out.reserve(kCryptFloor.size());
        for (Vec2 const& p : kCryptFloor)
            out.emplace_back(p.x, p.y, kThalnosSpawn.z, 0.f);
        return out;
    }

    Position LawnCenter()
    {
        return Position(kLawnCenter.x, kLawnCenter.y, kCouncilLawn.z, 0.f);
    }

    // The bots' hard bounds on a ground: the crypt's floor (his nook in, the stair out) or the lawn's disc.
    BossMechanics::SpotBounds BoundsFor(Ground ground)
    {
        if (ground == Ground::Lawn)
            return BossMechanics::SpotBounds().Circle(LawnCenter(), kLawnBoundsYd, kLawnZMin, kLawnZMax);
        return BossMechanics::SpotBounds().Polygon(CryptPositions(), kCryptZMin, kCryptZMax);
    }

    // Players only (a resolve's hits may list a pet).
    uint32 PlayersIn(std::vector<ObjectGuid> const& guids)
    {
        return static_cast<uint32>(std::count_if(guids.begin(), guids.end(), [](ObjectGuid const& g)
        {
            return g.IsPlayer();
        }));
    }
}

void SmThalnos::RegisterThalnosHardMode(ThalnosHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

void SmThalnos::RegisterThalnosIdleHook(ThalnosIdleHook hook)
{
    IdleHook() = std::move(hook);
}

bool SmThalnos::HasThalnosHardMode()
{
    return static_cast<bool>(HardModeFactory());
}

std::unique_ptr<ThalnosHardMode> SmThalnos::CreateThalnosHardMode(Creature* boss)
{
    ThalnosHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(boss) : nullptr;
}

// Bloodmage Thalnos 4543
struct boss_bloodmage_thalnos_rework : public BossAI, public ThalnosFight
{
    explicit boss_bloodmage_thalnos_rework(Creature* creature)
        : BossAI(creature, BOSS_THALNOS), _arena(ThalnosArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup(false);
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup(false);     // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = IsHeroicMap(me);
        bool hardMode = _heroic && instance && instance->GetData(DATA_HARD_MODE_THALNOS) != 0;
        if (hardMode)
        {
            // The handler first: a lit flag with no handler registered runs the normal heroic.
            _hardMode = CreateThalnosHardMode(me);
            if (!_hardMode)
            {
                LOG_WARN("module", "sm thalnos: the Desecration is answered but no hard mode handler is registered; "
                    "the pull runs as a normal heroic");
                hardMode = false;
            }
        }
        OnBossPull(me, kBossLogName, hardMode);
        _engaged = true;
        _ritual.Reset(_heroic);
        _ground = Ground::Crypt;
        // The hard mode's arena holds the crypt and the lawn until SetGround narrows it (no leash race at the
        // teleport).
        _arena.Configure(_hardMode ? DesecrationArena() : ThalnosArena(), LeashOptions(kBossLogName));

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_THALNOS;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_AGGRO);

        _boltClock.Start(_clockMs, kBoltBeat.firstMs);
        _spikeClock.Start(_clockMs, kSpikeBeat.firstMs);
        _boilClock.Start(_clockMs, kBoilBeat.firstMs);
        _novaClock.Start(_clockMs, kNovaBeat.firstMs);
        if (_heroic)
            _brandClock.Start(_clockMs, kBrandBeat.firstMs);
        _thresholdPct = _hardMode ? _hardMode->ThresholdPct(*this) : 0.f;

        Log("engage", Acore::StringFormat("heroic={} hardmode={} health={} threshold={:.0f} at=({:.1f}, {:.1f}, "
            "{:.1f})", _heroic ? 1 : 0, _hardMode ? 1 : 0, me->GetMaxHealth(), _thresholdPct, me->GetPositionX(),
            me->GetPositionY(), me->GetPositionZ()));
        if (_hardMode)
        {
            _hardMode->OnEngage(*this);
            // The kit's `pull` line above logs his health before the hard mode changes it.
            Log("pull-health", Acore::StringFormat("health={} hardmode=1", me->GetMaxHealth()));
        }
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        bool const lawn = _ground == Ground::Lawn;
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
        // The hard mode wipe on the lawn: he returns to the crypt (GY "the risen despawn and Thalnos returns").
        if (lawn && me->IsAlive())
        {
            Position const& home = me->GetHomePosition();
            me->NearTeleportTo(home.GetPositionX(), home.GetPositionY(), home.GetPositionZ(), home.GetOrientation());
            Log("home", "from=lawn");
        }
    }

    // The credit and the loot (filled by Unit::Kill before this runs; the hard mode bit is the instance's).
    void JustDied(Unit* killer) override
    {
        Log("death", Acore::StringFormat("stacks={} gained={} spent={} bolts={} bolts-kicked={} lances={} spikes={} "
            "spikes-empowered={} boils={} boils-empowered={} novas={} novas-kicked={} novas-empowered={} restarts={} "
            "brands={} hardmode={} ground={} killer={}", _ritual.Stacks(), _ritual.Gained(), _ritual.Spent(), _bolts,
            _boltsKicked, _lances, _spikes, _spikesEmpowered, _boils, _boilsEmpowered, _novas, _novasKicked,
            _novasEmpowered, _restarts, _brands, _hardMode ? 1 : 0, GroundName(_ground),
            killer ? killer->GetName() : "none"));
        Cleanup(true);      // the hard mode's OnEnd before his summons go
        BossAI::JustDied(killer);
        // Stock (SmartAI 4543 row 7 and its condition, dropped by S0's rev): Scorn rises at his stock spot while the
        // Scourge Invasion boss event (120) runs; normal only (section 7 #35).
        if (!IsHeroicMap(me) && sGameEventMgr->IsActiveEvent(kGameEventScourgeBossInInstance))
            me->SummonCreature(NPC_SCORN, kScornSummon.x, kScornSummon.y, kScornSummon.z, kScornSummon.o,
                TEMPSUMMON_MANUAL_DESPAWN);
    }

    // Stock (SmartAI 4543 row 1): "More... More souls!" on a kill, at most every 5 s.
    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer())
            return;
        if (_yelledKill && _clockMs < _lastKillYellMs + kKillYellGapMs)
            return;
        Talk(SAY_KILL);
        _yelledKill = true;
        _lastKillYellMs = _clockMs;
    }

    // His summons (the pools' looks; the hard mode's risen) go with his summon list. Scorn (after his death) is
    // stock's: left alone.
    void JustSummoned(Creature* summon) override
    {
        if (!summon || summon->GetEntry() == NPC_SCORN)
            return;
        summons.Summon(summon);
        if (_hardMode && _engaged)
            _hardMode->OnSummoned(*this, summon);
    }

    void SummonedCreatureDies(Creature* summon, Unit* killer) override
    {
        BossAI::SummonedCreatureDies(summon, killer);
        if (_hardMode && _engaged)
            _hardMode->OnSummonDied(*this, summon, killer);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
    }

    // TH1: a plain Blood Bolt on its target, a plain Blood Nova on each player: one stack per player hit.
    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (!_engaged || !spell || !target || !target->IsPlayer())
            return;
        if (spell->Id == SPELL_TH_BLOOD_BOLT)
            AddRitualStacks(1, "bolt");
        else if (spell->Id == SPELL_TH_BLOOD_NOVA)
            AddRitualStacks(1, "nova");
    }

    // A bar finished casting.
    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (!spell || !_engaged)
            return;
        NovaStage const stage = NovaStageOf(spell->Id);
        if (stage != NovaStage::Idle)
        {
            NovaOutcome const outcome = _nova.Finished(stage);
            if (outcome == NovaOutcome::PlainLands || outcome == NovaOutcome::EmpoweredLands)
            {
                if (_bar == spell->Id)
                    _bar = 0;
                NovaLands(outcome == NovaOutcome::EmpoweredLands, stage == NovaStage::Restart);
            }
            return;
        }
        if (_bar == spell->Id)
        {
            _bar = 0;
            if (spell->Id == SPELL_TH_BLOOD_LANCE)
                _lanceLine = MechanicHandle();      // its line resolves on its own just after
            else if (spell->Id == SPELL_TH_FLAME_SPIKE_CAST)
                _spikeCarries.clear();              // the carries land now (FollowThenLand)
        }
    }

    // A bar was kicked (or silenced). His own stops are guarded by _ownStop (StopCasting, the cleanup).
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (_ownStop || !spell || !_engaged || !me->IsAlive())
            return;
        NovaStage const stage = NovaStageOf(spell->Id);
        if (stage != NovaStage::Idle)
        {
            NovaOutcome const outcome = _nova.Kicked(stage);
            if (outcome == NovaOutcome::None)
                return;     // a bar that already ended, reported again
            if (_bar == spell->Id)
                _bar = 0;
            if (outcome == NovaOutcome::Restart)
                Log("nova-stripped", Acore::StringFormat("stacks={} (the restart follows)", _ritual.Stacks()));
            else
            {
                ++_novasKicked;
                Log("nova-kicked", Acore::StringFormat("restart={} stacks={}", stage == NovaStage::Restart ? 1 : 0,
                    _ritual.Stacks()));
            }
            return;
        }
        if (_bar != spell->Id)
            return;         // a bar that already ended, reported again
        _bar = 0;
        if (spell->Id == SPELL_TH_BLOOD_BOLT)
        {
            ++_boltsKicked;
            Log("bolt-kicked", Acore::StringFormat("stacks={}", _ritual.Stacks()));
        }
        else if (spell->Id == SPELL_TH_BLOOD_LANCE)
        {
            CancelLance();
            Log("lance-kicked", Acore::StringFormat("stacks={}", _ritual.Stacks()));
        }
        else if (spell->Id == SPELL_TH_FLAME_SPIKE_CAST)
        {
            CancelSpikeCarries();
            Log("spike-stopped");
        }
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!me->IsEngaged())
        {
            // D4H, out of combat: the red aura while the flag is lit (a wipe, a cold load).
            if (me->IsAlive() && !me->IsInEvadeMode())
                if (ThalnosIdleHook const& hook = IdleHook())
                    hook(me);
        }
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        UpdateThreshold();
        UpdateBarWatch();
        UpdateRestart();
        UpdateBeats();
        PrunePools();
        if (_hardMode)
            _hardMode->OnUpdate(*this, diff);
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        if (_clockMs < _holdUntilMs)
            return;
        // The debuffs are instant (triggered): they never wait for a bar and never break one.
        if (_boilClock.Due(_clockMs))
        {
            if (StartBoil(nullptr))
                _boilClock.Fired(_clockMs, kBoilBeat.everyMs(_heroic));
            else
                _boilClock.Start(_clockMs, kRetryMs);
        }
        if (_heroic && _brandClock.Due(_clockMs))
        {
            if (CastBrand(nullptr))
                _brandClock.Fired(_clockMs, kBrandBeat.everyMs(_heroic));
            else
                _brandClock.Start(_clockMs, kRetryMs);
        }
        // One bar at a time; a due beat stays due (a kick's Shadow lockout too: the cast is refused, retried).
        if (Casting() || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_novaClock.Due(_clockMs))
        {
            if (StartNova())
                _novaClock.Fired(_clockMs, kNovaBeat.everyMs(_heroic));
            else
                _novaClock.Start(_clockMs, kRetryMs);
            return;
        }
        if (_spikeClock.Due(_clockMs))
        {
            if (StartSpike(nullptr))
                _spikeClock.Fired(_clockMs, kSpikeBeat.everyMs(_heroic));
            else
                _spikeClock.Start(_clockMs, kRetryMs);
            return;
        }
        if (_boltClock.Due(_clockMs))
        {
            if (StartBolt(nullptr))
                _boltClock.Fired(_clockMs, kBoltBeat.everyMs(_heroic));
            else
                _boltClock.Start(_clockMs, kRetryMs);
        }
    }

    // A bar the engine ended without a callback (its target gone, a failed launch): free the beats.
    void UpdateBarWatch()
    {
        if (!_bar || me->HasUnitState(UNIT_STATE_CASTING) || _clockMs < _barEndMs + kBarLostMs)
            return;
        Log("bar-lost", Acore::StringFormat("spell={}", _bar));
        if (NovaStageOf(_bar) != NovaStage::Idle)
            _nova.Clear();
        if (_bar == SPELL_TH_BLOOD_LANCE)
            CancelLance();
        _bar = 0;
    }

    // Starts a bar: he stands still for it (the Bolt, the Lance and the novas are kickable; a cast started on the move
    // is not broken by it, but the bots read the bar better with him planted).
    bool StartBar(Unit* target, uint32 spellId, uint32 castMs)
    {
        // A kick's school lockout (a kicked Shadow cast locks the Bolt, the Lance and the novas a few seconds): the
        // beat stays due, quietly.
        if (SpellInfo const* info = sSpellMgr->GetSpellInfo(spellId))
            if (me->IsSpellProhibited(info->GetSchoolMask()))
                return false;
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(target ? target : me, spellId, false);
        if (result != SPELL_CAST_OK)
        {
            Log("cast-refused", Acore::StringFormat("spell={} result={}", spellId, static_cast<uint32>(result)));
            return false;
        }
        _bar = spellId;
        _barEndMs = _clockMs + castMs;
        return true;
    }

    // TH1: an empowered cast starts (after its bar or debuff went out): the cost, the emote, the hands.
    void Empower(Empowered e, char const* what)
    {
        uint32 const before = _ritual.Stacks();
        _ritual.Spend(e);
        SyncRitualAura();
        Talk(EMOTE_HANDS_RUN_RED);
        me->CastSpell(me, SPELL_TH_HANDS_RUN_RED, true);
        // The stock 0-40% line moves to his first empowered spell on normal and heroic (the teleport's on hard mode).
        if (!_yelledNoRest && !_hardMode)
        {
            Talk(SAY_NO_REST);
            _yelledNoRest = true;
        }
        Log("empowered", Acore::StringFormat("spell={} stacks={}->{}", what, before, _ritual.Stacks()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH1 Blood Ritual
    // ----------------------------------------------------------------------------------------------------------------

    void SyncRitualAura()
    {
        uint32 const want = std::min(_ritual.Stacks(), kAuraStackLimit);
        uint32 const have = DungeonKit::Stacks(me, SPELL_TH_BLOOD_RITUAL, me->GetGUID());
        if (want != have)
            DungeonKit::AddStacks(me, SPELL_TH_BLOOD_RITUAL, static_cast<int32>(want) - static_cast<int32>(have), me,
                kAuraStackLimit);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH2 Blood Bolt / TH2e Blood Lance
    // ----------------------------------------------------------------------------------------------------------------

    bool StartBolt(Unit* forced)
    {
        Unit* target = forced ? forced : me->GetVictim();
        if (!target || !target->IsAlive())
            return false;
        bool const lance = _ritual.Holds(Empowered::Lance);
        uint32 const spellId = lance ? SPELL_TH_BLOOD_LANCE : SPELL_TH_BLOOD_BOLT;
        if (!StartBar(target, spellId, kBoltCastMs))
            return false;
        if (!lance)
        {
            ++_bolts;
            Log("bolt", Acore::StringFormat("target={} pct={:.0f} stacks={}", target->GetName(),
                kBoltTankPct(_heroic), _ritual.Stacks()));
            return true;
        }

        Empower(Empowered::Lance, "lance");
        // The line from him through the tank to the wall, fixed at the bar's start; the tank is exempt (the bolt is its
        // hit), everyone else in it takes the line's hit.
        Vec2 const from = DungeonKit::PlaneOf(me);
        Vec2 const to = DungeonKit::PlaneOf(target);
        float const facing = DungeonKit::BearingTo(from, to);
        float const length = LanceLength(_ground, from, to);
        Position const apex(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
        float const pct = kLanceLinePct(_heroic);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::LineFacing(BossMechanics::Anchor(apex), facing,
            length, kLanceWidth), Ms(kBoltCastMs + kLanceResolveLagMs));
        ref.Damage(pct).TankDamage(pct).Weakened().TankExempt().Spell(SPELL_TH_BLOOD_LANCE_LINE)
            .Within(BoundsFor(_ground)).Tag(TH2)
            .OnResolve(OnThalnos([](boss_bloodmage_thalnos_rework& ai, BossMechanics::ResolveResult const& result)
            {
                ai.LanceResolved(result);
            }));
        _lanceLine = ref.Handle();
        TrackOnGround(_lanceLine);
        ++_lances;
        Log("lance", Acore::StringFormat("target={} length={:.1f} tank-pct={:.0f} line-pct={:.0f} ground={}",
            target->GetName(), length, kLanceTankPct(_heroic), pct, GroundName(_ground)));
        return true;
    }

    void LanceResolved(BossMechanics::ResolveResult const& result)
    {
        if (result.hits.empty())
            return;
        Log("lance-line", Acore::StringFormat("hits={}", PlayersIn(result.hits)));
    }

    void CancelLance()
    {
        if (_lanceLine)
            Mechanic::Cancel(me, _lanceLine);
        _lanceLine = MechanicHandle();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH3 Flame Spike
    // ----------------------------------------------------------------------------------------------------------------

    // The carrier's drop: the ground's edge, away from the group, never onto a live pool (bots only).
    BossMechanics::DropSpotRule SpikeDropRule() const
    {
        BossMechanics::DropSpotRule rule;
        if (_ground == Ground::Lawn)
            rule.Room(LawnCenter(), kLawnBoundsYd);
        else
            rule.Room(CryptPositions());
        rule.Edge().Away().Within(BoundsFor(_ground));
        for (Pool const& pool : _pools)
            rule.Avoid(pool.at, kSpikeAvoidPoolYd);
        return rule;
    }

    bool StartSpike(Player* forced)
    {
        bool const empowered = _ritual.Holds(Empowered::Spike);
        uint32 const count = SpikeTargets(empowered);
        std::vector<Player*> targets;
        if (CountsAsPlayer(forced))
            targets.push_back(forced);
        if (targets.size() < count)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;       // the tank included
            if (forced)
                rule.exclude.push_back(forced->GetGUID().GetRawValue());
            for (Player* player : DungeonKit::PickPlayers(me, rule, count - static_cast<uint32>(targets.size())))
                targets.push_back(player);
        }
        if (targets.empty())
            return false;
        if (!StartBar(me, SPELL_TH_FLAME_SPIKE_CAST, kSpikeCastMs))
            return false;
        if (empowered)
            Empower(Empowered::Spike, "spike");

        _spikeCarries.clear();
        std::string names;
        for (Player* target : targets)
        {
            me->CastSpell(target, SPELL_TH_FLAME_SPIKE, true);
            DungeonKit::ImpactSpec impact;
            impact.pct = 0.f;           // the carry is the marker only: the pillar is the hit
            impact.weakened = false;
            impact.tag = TH3;
            Map* map = me->GetMap();
            ObjectGuid const guid = me->GetGUID();
            MechanicRef ref = DungeonKit::FollowThenLand(me, target, kSpikeRadius, Ms(kSpikeCastMs), impact,
                [map, guid, empowered](Creature* /*owner*/, Position const& spot,
                    BossMechanics::ResolveResult const& result)
                {
                    if (result.fizzled)
                        return;
                    if (boss_bloodmage_thalnos_rework* ai = From(map, guid))
                        ai->SpikeLanded(spot, empowered);
                });
            if (!ref.IsValid())
                continue;
            ref.DropSpot(SpikeDropRule()).Within(BoundsFor(_ground));
            _spikeCarries.push_back(ref.Handle());
            TrackOnGround(ref.Handle());
            names += " " + target->GetName();
        }
        ++_spikes;
        if (empowered)
            ++_spikesEmpowered;
        Log("spike", Acore::StringFormat("count={} empowered={} pct={:.0f} pool={:.0f}%/{}s targets:{}", targets.size(),
            empowered ? 1 : 0, kSpikePillarPct(_heroic), kSpikePoolPct(_heroic), kSpikePoolMs(_heroic) / 1000,
            names));
        return true;
    }

    // The bar has ended: the marker lands where the carrier stood; 1.5 s later the pillar.
    void SpikeLanded(Position const& spot, bool empowered)
    {
        if (!_engaged)
            return;
        float const pct = kSpikePillarPct(_heroic);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Circle(BossMechanics::Anchor(spot), kSpikeRadius),
            Ms(kSpikeMarkerMs));
        ref.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_TH_FLAME_SPIKE_PILLAR).Within(BoundsFor(_ground))
            .Tag(TH3).OnResolve(OnThalnos([spot, empowered](boss_bloodmage_thalnos_rework& ai,
                BossMechanics::ResolveResult const& result)
            {
                ai.PillarErupted(spot, empowered, result);
            }));
        TrackOnGround(ref.Handle());
    }

    // The pillar: its hits feed the ritual (plain only), then the pool burns where it stood.
    void PillarErupted(Position const& spot, bool empowered, BossMechanics::ResolveResult const& result)
    {
        if (!_engaged || result.fizzled)
            return;
        uint32 const hits = PlayersIn(result.hits);
        if (hits && !empowered)
            AddRitualStacks(hits, "spike");

        uint32 const poolMs = kSpikePoolMs(_heroic);
        float const pct = kSpikePoolPct(_heroic);
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(poolMs);
        linger.tick = Ms(kSpikePoolTickMs);
        linger.pct = pct;
        linger.school = SPELL_SCHOOL_FIRE;
        linger.spellId = SPELL_TH_FLAME_SPIKE_POOL;
        linger.tag = TH3;
        MechanicRef ref = DungeonKit::Linger(me, BossMechanics::Shapes::Circle(BossMechanics::Anchor(spot),
            kSpikeRadius), linger);
        ref.TankDamage(pct).Within(BoundsFor(_ground));
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return;
        TrackOnGround(handle);
        Pool pool;
        pool.at = spot;
        pool.zone = handle;
        pool.endMs = _clockMs + poolMs;
        if (StalkerExists())
            if (TempSummon* look = me->SummonCreature(NPC_SM_STALKER, spot, TEMPSUMMON_TIMED_DESPAWN, poolMs))
            {
                look->CastSpell(look, SPELL_TH_FLAME_SPIKE_ERUPT, true);
                look->CastSpell(look, SPELL_TH_FLAME_SPIKE_LOOK, true);
                pool.look = look->GetGUID();
            }
        _pools.push_back(pool);
        Log("spike-pillar", Acore::StringFormat("at=({:.1f}, {:.1f}) hits={} empowered={} pools={}",
            spot.GetPositionX(), spot.GetPositionY(), hits, empowered ? 1 : 0, _pools.size()));
    }

    void CancelSpikeCarries()
    {
        for (MechanicHandle const& handle : _spikeCarries)
            Mechanic::Cancel(me, handle);
        _spikeCarries.clear();
    }

    void PrunePools()
    {
        std::erase_if(_pools, [this](Pool const& p) { return _clockMs >= p.endMs; });
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH4 Boiling Blood
    // ----------------------------------------------------------------------------------------------------------------

    bool StartBoil(Player* forced)
    {
        bool const empowered = _ritual.Holds(Empowered::Boil);
        uint32 const count = BoilCarriers(empowered);
        std::vector<Player*> targets;
        if (CountsAsPlayer(forced) && forced != me->GetVictim())
            targets.push_back(forced);
        if (targets.size() < count)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;        // the tank is left out (the large-spread exemption)
            rule.tankIfAlone = false;
            if (!targets.empty())
                rule.exclude.push_back(targets.front()->GetGUID().GetRawValue());
            for (Player* player : DungeonKit::PickPlayers(me, rule, count - static_cast<uint32>(targets.size())))
                targets.push_back(player);
        }
        if (targets.empty())
            return false;
        if (empowered)
            Empower(Empowered::Boil, "boil");

        GuidSet carriers;
        std::string names;
        for (Player* player : targets)
        {
            me->CastSpell(player, SPELL_TH_BOILING_BLOOD, true);
            carriers.insert(player->GetGUID());
            names += " " + player->GetName();
        }
        float const radius = kBoilRadius(_heroic);
        float const pct = kBoilSplashPct(_heroic);
        MechanicRef ref = Mechanic::RunOut(me, targets.front(), radius, Ms(kBoilMs));
        ref.Targets(carriers).Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_TH_BOILING_BLOOD_SPLASH)
            .Within(BoundsFor(_ground)).Tag(TH4)
            .OnResolve(OnThalnos([carriers, empowered](boss_bloodmage_thalnos_rework& ai,
                BossMechanics::ResolveResult const& result)
            {
                ai.BoilErupted(carriers, empowered, result);
            }));
        TrackOnGround(ref.Handle());
        ++_boils;
        if (empowered)
            ++_boilsEmpowered;
        Log("boil", Acore::StringFormat("count={} empowered={} radius={:.0f} carrier-pct={:.0f} splash-pct={:.0f} "
            "targets:{}", targets.size(), empowered ? 1 : 0, radius, kBoilCarrierPct(_heroic), pct, names));
        return true;
    }

    // The eruption: each carrier takes its own hit (it cannot avoid it: always a stack); the registry dealt the splash.
    void BoilErupted(GuidSet const& carriers, bool empowered, BossMechanics::ResolveResult const& result)
    {
        if (!_engaged)
            return;
        uint32 carriersHit = 0;
        for (ObjectGuid const& guid : carriers)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, guid);
            if (!CountsAsPlayer(player) || !player->IsInMap(me))
                continue;
            me->CastSpell(player, SPELL_TH_BOILING_BLOOD_BURST, true);
            ++carriersHit;
        }
        uint32 splashed = 0;
        for (ObjectGuid const& guid : result.hits)
            if (guid.IsPlayer() && !carriers.count(guid))
                ++splashed;
        if (!empowered && carriersHit + splashed)
            AddRitualStacks(carriersHit + splashed, "boil");
        Log("boil-erupt", Acore::StringFormat("carriers={} splashed={} empowered={}", carriersHit, splashed,
            empowered ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH5 Blood Nova
    // ----------------------------------------------------------------------------------------------------------------

    bool StartNova()
    {
        bool const empowered = _ritual.Holds(Empowered::Nova);
        uint32 const spellId = empowered ? SPELL_TH_EMPOWERED_NOVA_CAST : SPELL_TH_BLOOD_NOVA_CAST;
        if (!StartBar(me, spellId, kNovaCastMs))
            return false;
        if (empowered)
        {
            _nova.StartEmpowered();
            Empower(Empowered::Nova, "nova");
            ++_novasEmpowered;
        }
        else
            _nova.StartPlain();
        ++_novas;
        Log("nova", Acore::StringFormat("empowered={} pct={:.0f} stacks={}", empowered ? 1 : 0,
            empowered ? kEmpoweredNovaPct(_heroic) : kNovaPct(_heroic), _ritual.Stacks()));
        return true;
    }

    // The empowered nova was kicked: the plain 2 s restart, on the tick after the kick (never from inside the engine's
    // interrupt callback).
    void UpdateRestart()
    {
        if (_nova.Stage() != NovaStage::RestartPending)
            return;
        if (!StartBar(me, SPELL_TH_BLOOD_NOVA_RESTART, kNovaRestartCastMs))
        {
            _nova.RestartFailed();
            Log("nova-restart-failed");
            return;
        }
        _nova.StartRestart();
        ++_restarts;
        Log("nova-restart", Acore::StringFormat("pct={:.0f}", kNovaPct(_heroic)));
    }

    // A nova landed: every player on his ground takes it (a plain hit gives a stack each: SpellHitTarget).
    void NovaLands(bool empowered, bool restart)
    {
        uint32 const spellId = empowered ? SPELL_TH_EMPOWERED_NOVA : SPELL_TH_BLOOD_NOVA;
        std::vector<Player*> const players = PlayersOnGround();
        for (Player* player : players)
            me->CastSpell(player, spellId, true);
        Log("nova-lands", Acore::StringFormat("empowered={} restart={} players={} pct={:.0f} stacks={}",
            empowered ? 1 : 0, restart ? 1 : 0, players.size(),
            empowered ? kEmpoweredNovaPct(_heroic) : kNovaPct(_heroic), _ritual.Stacks()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TH6 Blood Brand (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool CastBrand(Player* forced)
    {
        Player* target = CountsAsPlayer(forced) ? forced : nullptr;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;       // the tank included
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        me->CastSpell(target, SPELL_TH_BLOOD_BRAND, true);
        _brandGates[target->GetGUID()] = BrandGate();
        ++_brands;
        Log("brand", Acore::StringFormat("target={} tank={}", target->GetName(), target == me->GetVictim() ? 1 : 0));
        return true;
    }

    // The UnitScript below: the branded player took damage.
    void BrandHit(Player* victim)
    {
        if (!_engaged || !victim)
            return;
        if (!_brandGates[victim->GetGUID()].Take(_clockMs))
            return;
        AddRitualStacks(1, "brand");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data: the interrupt list (the novas first), Blood Brand on the dispel list (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        // Blood Nova: a reward on normal, expected on heroic; the empowered nova's restart is the second interrupt.
        d.interrupts.push_back(BossMechanics::InterruptEntry(NPC_THALNOS, SPELL_TH_BLOOD_NOVA_CAST, _heroic ? 3 : 2,
            Ms(kNovaBeat.everyMs(_heroic))));
        d.interrupts.push_back(BossMechanics::InterruptEntry(NPC_THALNOS, SPELL_TH_EMPOWERED_NOVA_CAST, 3));
        d.interrupts.push_back(BossMechanics::InterruptEntry(NPC_THALNOS, SPELL_TH_BLOOD_NOVA_RESTART, 3));
        d.interrupts.push_back(BossMechanics::InterruptEntry(NPC_THALNOS, SPELL_TH_BLOOD_LANCE, 2));
        d.interrupts.push_back(BossMechanics::InterruptEntry(NPC_THALNOS, SPELL_TH_BLOOD_BOLT, 1,
            Ms(kBoltBeat.everyMs(_heroic))));
        if (_heroic)
            d.dispels.push_back(BossMechanics::DispelEntry(SPELL_TH_BLOOD_BRAND, 2));
        if (_hardMode)
            _hardMode->ConfigureDescriptor(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The hard mode's threshold (75%)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateThreshold()
    {
        if (!_hardMode || _thresholdDone || me->GetHealthPct() > _thresholdPct)
            return;
        _thresholdDone = true;
        Log("threshold", Acore::StringFormat("pct={:.0f} health={:.1f}", _thresholdPct, me->GetHealthPct()));
        _hardMode->OnThreshold(*this);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ThalnosFight (D4H's view)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Thalnos() override { return me; }
    bool Heroic() const override { return _heroic; }
    ThalnosHardMode* ActiveHardMode() override { return _hardMode.get(); }
    uint64 FightMs() const override { return _clockMs; }

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() override
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

    std::vector<Player*> PlayersOnGround() override
    {
        Arena const ground = _ground == Ground::Lawn ? LawnArena() : ThalnosArena();
        std::vector<Player*> out;
        for (Player* player : FightPlayers())
            if (ground.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                out.push_back(player);
        return out;
    }

    Ground CurrentGround() const override { return _ground; }

    void SetGround(Ground ground, char const* why) override
    {
        if (ground == _ground)
            return;
        // The old ground's mechanics go (MJ-1): their bounds would hold every bot to the old ground. Their debuffs go
        // with them (a boil cancelled here never erupts; the carrier stood in the crypt a tick ago).
        uint32 cancelled = 0;
        for (MechanicHandle const& handle : _grounded.Leave(ground))
        {
            Mechanic::Cancel(me, handle);
            ++cancelled;
        }
        _lanceLine = MechanicHandle();
        _spikeCarries.clear();
        _pools.clear();
        if (instance && cancelled)
            for (uint32 const spell : { uint32(SPELL_TH_FLAME_SPIKE), uint32(SPELL_TH_BOILING_BLOOD) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _ground = ground;
        _arena.Configure(ground == Ground::Lawn ? LawnArena() : (_hardMode ? DesecrationArena() : ThalnosArena()),
            LeashOptions(kBossLogName));
        Log("ground", Acore::StringFormat("to={} why={} cancelled={}", GroundName(ground), why ? why : "-",
            cancelled));
    }

    void HoldBeats(uint64 untilMs) override
    {
        _holdUntilMs = std::max(_holdUntilMs, untilMs);
    }

    bool Casting() const override
    {
        return _bar != 0 || _nova.Busy();
    }

    void StopCasting(char const* why) override
    {
        _ownStop = true;
        me->InterruptNonMeleeSpells(false);
        _ownStop = false;
        CancelLance();
        CancelSpikeCarries();
        _nova.Clear();
        _bar = 0;
        Log("stop", Acore::StringFormat("why={}", why ? why : "-"));
    }

    bool FireNow(Kit mechanic, Player* forced) override
    {
        switch (mechanic)
        {
            case Kit::BloodBolt:
                return !Casting() && StartBolt(forced ? static_cast<Unit*>(forced) : nullptr);
            case Kit::FlameSpike:
                return !Casting() && StartSpike(forced);
            case Kit::BoilingBlood:
                return StartBoil(forced);
            case Kit::BloodNova:
                return !Casting() && StartNova();
            case Kit::BloodBrand:
                return CastBrand(forced);
        }
        return false;
    }

    uint32 RitualStacks() const override { return _ritual.Stacks(); }

    uint32 AddRitualStacks(uint32 n, char const* why) override
    {
        if (!n || !_engaged)
            return _ritual.Stacks();
        uint32 const before = _ritual.Stacks();
        _ritual.Add(n);
        SyncRitualAura();
        Log("ritual", Acore::StringFormat("from={} hits={} stacks={}->{}", why ? why : "-", n, before,
            _ritual.Stacks()));
        return _ritual.Stacks();
    }

    void JoinFight(Creature* unit) override
    {
        if (!unit)
            return;
        Mechanic::TrackUnit(me, unit);
        // Everyone in the fight at 0 (a one-entry threat list evades).
        for (Player* player : FightPlayers())
            unit->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
    }

    // A mechanic of the fight: kept to cancel it on a reset.
    void Track(MechanicHandle handle) override
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)      // drop only the resolved ones (a hard mode attempt keeps many live; N-1)
        {
            Map const* map = me->GetMap();
            std::erase_if(_live, [map](MechanicHandle const& h) { return !LiveIn(map, h); });
            _grounded.Prune([map](MechanicHandle const& h) { return LiveIn(map, h); });
        }
    }

    // A mechanic registered with the current ground's bounds (BoundsFor(_ground)): cancelled when the ground changes.
    void TrackOnGround(MechanicHandle handle)
    {
        if (!handle)
            return;
        Track(handle);
        _grounded.Add(_ground, handle);
    }

    // A registry mechanic that has not finished or been cancelled.
    static bool LiveIn(Map const* map, MechanicHandle handle)
    {
        BossMechanics::Registry const* registry = handle ? Mechanic::Read(map) : nullptr;
        BossMechanics::ActiveMechanic const* m = registry ? registry->Find(handle.id) : nullptr;
        return m && !m->finished && !m->cancelled;
    }

    void TrackSummon(Creature* summon) override
    {
        if (summon)
            _extraSummons.push_back(summon->GetGUID());
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
    // `.dbtest sm thalnos` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Bolt,
        Spike,
        Boil,
        Nova,
        Brand,
        Stacks,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM), `n` a count.
    std::string TestFire(TestMechanic mechanic, Player* who, uint32 n)
    {
        if (!me->IsEngaged() || !_engaged)
            return "Thalnos must be in combat (the picks read his threat list, the mechanics his encounter).";
        Player* forced = CountsAsPlayer(who) ? who : nullptr;
        switch (mechanic)
        {
            case TestMechanic::Bolt:
                if (Casting())
                    return "He is casting already.";
                if (!StartBolt(nullptr))
                    return "The bolt did not start (see the log).";
                break;
            case TestMechanic::Spike:
                if (Casting())
                    return "He is casting already.";
                if (!StartSpike(forced))
                    return "The spike did not start (see the log).";
                break;
            case TestMechanic::Boil:
                if (!StartBoil(forced))
                    return "Nobody to boil (a non-tank on his threat list).";
                break;
            case TestMechanic::Nova:
                if (Casting())
                    return "He is casting already.";
                if (!StartNova())
                    return "The nova did not start (see the log).";
                break;
            case TestMechanic::Brand:
                if (!CastBrand(forced))
                    return "Nobody to brand.";
                break;
            case TestMechanic::Stacks:
                _ritual.Set(n);
                SyncRitualAura();
                Log("ritual", Acore::StringFormat("from=gm stacks={}", _ritual.Stacks()));
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} hardmode={} ground={} health={:.1f} stacks={} (gained {} spent "
            "{}) bar={} nova={} pools={} bolts={}/{} kicked lances={} spikes={} boils={} novas={} kicked={} "
            "restarts={} brands={} live={}", _clockMs / 1000, _heroic ? 1 : 0, _hardMode ? 1 : 0, GroundName(_ground),
            me->GetHealthPct(), _ritual.Stacks(), _ritual.Gained(), _ritual.Spent(), _bar,
            static_cast<uint32>(_nova.Stage()), _pools.size(), _bolts, _boltsKicked, _lances, _spikes, _boils, _novas,
            _novasKicked, _restarts, _brands, _live.size());
    }

private:
    static constexpr uint32 kRetryMs = 1000;
    static constexpr uint32 kBarLostMs = 1500;

    struct Pool
    {
        Position at;
        MechanicHandle zone;
        ObjectGuid look;
        uint64 endMs = 0;
    };

    static char const* GroundName(Ground ground)
    {
        return ground == Ground::Lawn ? "lawn" : "crypt";
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnThalnos(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_bloodmage_thalnos_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_bloodmage_thalnos_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_bloodmage_thalnos_rework*>(boss->AI());
    }

    // The pull's state: the hard mode ended (its OnEnd first), no bar, nothing registered, no aura of his on anyone,
    // no pool or look, no extra summon, clocks stopped, the crypt's arena (reset, evade, death, a new pull).
    void Cleanup(bool died)
    {
        if (_hardMode)
        {
            std::unique_ptr<ThalnosHardMode> const hardMode = std::move(_hardMode);
            hardMode->OnEnd(*this, died);
        }
        _engaged = false;
        _ownStop = true;
        if (me->IsAlive())
            me->InterruptNonMeleeSpells(false);
        _ownStop = false;
        _bar = 0;
        _nova.Clear();
        _lanceLine = MechanicHandle();
        _spikeCarries.clear();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _grounded.Clear();
        _pools.clear();
        summons.DespawnAll();
        for (ObjectGuid const& guid : _extraSummons)
            if (Creature* unit = me->GetMap()->GetCreature(guid))
                unit->DespawnOrUnsummon();
        _extraSummons.clear();
        _brandGates.clear();
        _boltClock.Stop();
        _spikeClock.Stop();
        _boilClock.Stop();
        _novaClock.Stop();
        _brandClock.Stop();
        _ritual.Reset(false);
        me->RemoveAurasDueToSpell(SPELL_TH_BLOOD_RITUAL);
        _clockMs = 0;
        _holdUntilMs = 0;
        _barEndMs = 0;
        _thresholdPct = 0.f;
        _thresholdDone = false;
        _yelledNoRest = false;
        _yelledKill = false;
        _lastKillYellMs = 0;
        _bolts = _boltsKicked = _lances = _spikes = _spikesEmpowered = _boils = _boilsEmpowered = 0;
        _novas = _novasKicked = _novasEmpowered = _restarts = _brands = 0;
        if (_ground != Ground::Crypt)
            _arena.Configure(ThalnosArena(), LeashOptions(kBossLogName));
        _ground = Ground::Crypt;
        _arena.Reset();
        if (instance)
            for (uint32 const spell : { uint32(SPELL_TH_FLAME_SPIKE), uint32(SPELL_TH_BOILING_BLOOD),
                uint32(SPELL_TH_BLOOD_BRAND) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    DungeonKit::ArenaGuard _arena;
    std::unique_ptr<ThalnosHardMode> _hardMode;
    Ritual _ritual;
    NovaState _nova;
    BeatClock _boltClock;
    BeatClock _spikeClock;
    BeatClock _boilClock;
    BeatClock _novaClock;
    BeatClock _brandClock;
    std::vector<MechanicHandle> _live;
    GroundedHandles<MechanicHandle> _grounded;
    std::vector<MechanicHandle> _spikeCarries;
    MechanicHandle _lanceLine;
    std::vector<Pool> _pools;
    std::vector<ObjectGuid> _extraSummons;
    std::unordered_map<ObjectGuid, BrandGate> _brandGates;
    Ground _ground = Ground::Crypt;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint64 _holdUntilMs = 0;
    uint64 _barEndMs = 0;
    uint64 _lastKillYellMs = 0;
    uint32 _bar = 0;                // the bar he started and that has not ended yet
    float _thresholdPct = 0.f;
    uint32 _bolts = 0;
    uint32 _boltsKicked = 0;
    uint32 _lances = 0;
    uint32 _spikes = 0;
    uint32 _spikesEmpowered = 0;
    uint32 _boils = 0;
    uint32 _boilsEmpowered = 0;
    uint32 _novas = 0;
    uint32 _novasKicked = 0;
    uint32 _novasEmpowered = 0;
    uint32 _restarts = 0;
    uint32 _brands = 0;
    bool _engaged = false;
    bool _heroic = false;
    bool _ownStop = false;
    bool _thresholdDone = false;
    bool _yelledNoRest = false;
    bool _yelledKill = false;
};

// TH6: each time a Blood Branded player takes damage (from any source), the Thalnos who branded them gains a stack (at
// most one a second, his AI's gate).
class thalnos_blood_brand_hook : public UnitScript
{
public:
    thalnos_blood_brand_hook() : UnitScript("thalnos_blood_brand_hook", true, { UNITHOOK_ON_DAMAGE }) { }

    void OnDamage(Unit* /*attacker*/, Unit* victim, uint32& damage) override
    {
        if (!damage || !victim || !victim->IsPlayer())
            return;
        Aura const* brand = victim->GetAura(SPELL_TH_BLOOD_BRAND);
        if (!brand)
            return;
        Creature* boss = ObjectAccessor::GetCreature(*victim, brand->GetCasterGUID());
        if (!boss || !boss->IsAIEnabled)
            return;
        if (auto* ai = dynamic_cast<boss_bloodmage_thalnos_rework*>(boss->AI()))
            ai->BrandHit(victim->ToPlayer());
    }
};

namespace
{
    boss_bloodmage_thalnos_rework* FindThalnosAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_THALNOS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_bloodmage_thalnos_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Thalnos is not running boss_bloodmage_thalnos_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_bloodmage_thalnos_rework::TestMechanic mechanic, char const* what,
        uint32 n = 0)
    {
        boss_bloodmage_thalnos_rework* ai = FindThalnosAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who, n);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Thalnos: {} fired ({}).", what,
            ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_THALNOS, BOSS_THALNOS);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_bloodmage_thalnos_rework* ai = FindThalnosAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Thalnos: {}", ai->TestState());
        return true;
    }

    bool HandleBolt(ChatHandler* handler)
    {
        return Fire(handler, boss_bloodmage_thalnos_rework::TestMechanic::Bolt,
            "Blood Bolt (TH2, on his victim; Blood Lance when he holds 3 stacks)");
    }

    bool HandleSpike(ChatHandler* handler)
    {
        return Fire(handler, boss_bloodmage_thalnos_rework::TestMechanic::Spike,
            "Flame Spike (TH3, the selected player first; three carriers when he holds 3 stacks)");
    }

    bool HandleBoil(ChatHandler* handler)
    {
        return Fire(handler, boss_bloodmage_thalnos_rework::TestMechanic::Boil,
            "Boiling Blood (TH4, the selected non-tank first; two carriers when he holds 4 stacks)");
    }

    bool HandleNova(ChatHandler* handler)
    {
        return Fire(handler, boss_bloodmage_thalnos_rework::TestMechanic::Nova,
            "Blood Nova (TH5; empowered when he holds 5 stacks)");
    }

    bool HandleBrand(ChatHandler* handler)
    {
        return Fire(handler, boss_bloodmage_thalnos_rework::TestMechanic::Brand,
            "Blood Brand (TH6, the selected player, else random; any difficulty)");
    }

    bool HandleStacks(ChatHandler* handler, uint32 stacks)
    {
        return Fire(handler, boss_bloodmage_thalnos_rework::TestMechanic::Stacks,
            "Blood Ritual's count (TH1, at the difficulty's cap)", stacks);
    }

    // Handoff section 3.7: `.dbtest sm thalnos hardmode` arms the hard mode past its trigger (GM).
    bool HandleHardMode(ChatHandler* handler)
    {
        return SmTest::ArmHardMode(handler, BOSS_DESECRATION);
    }

    // `.dbtest sm thalnos <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossBloodmageThalnosTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "bolt",     HandleBolt,     SEC_GAMEMASTER, Console::No },
            { "spike",    HandleSpike,    SEC_GAMEMASTER, Console::No },
            { "boil",     HandleBoil,     SEC_GAMEMASTER, Console::No },
            { "nova",     HandleNova,     SEC_GAMEMASTER, Console::No },
            { "brand",    HandleBrand,    SEC_GAMEMASTER, Console::No },
            { "stacks",   HandleStacks,   SEC_GAMEMASTER, Console::No },
            { "hardmode", HandleHardMode, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_bloodmage_thalnos_rework()
{
    RegisterDungeonReworkCreatureAI(boss_bloodmage_thalnos_rework, ScarletMonasteryRework::kInstanceScriptName);
    new thalnos_blood_brand_hook();
    SmTest::RegisterBoss("thalnos", BossBloodmageThalnosTestCommands());
}
