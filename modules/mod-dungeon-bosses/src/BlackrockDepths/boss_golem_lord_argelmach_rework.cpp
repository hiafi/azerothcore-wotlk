/*
 * mod-dungeon-bosses, Blackrock Depths D15: Golem Lord Argelmach (8983), "the dead dwarf's assembly line, one golem at
 * a time" (rulings 55, 56, 88, 91). Build spec: docs/dungeons/blackrock-depths-3-manufactory.md "Golem Lord Argelmach"
 * (AR1-AR10), handoff sections 3.4 rows D15, 3.5 row D15, 3.6, 3.8, 3.10, 7 #20, 8 #20. Replaces his SmartAI (rows
 * 0-13, dropped by rev_argelmach_blackrock_depths.sql) and the stock hall release (instance data 31 / 32: the rework
 * instance keeps it only while wave 2 is unbound; ruling 56 removes it); bound by apps/dbc-tools
 * source/npcs/blackrock_depths/argelmach.py once BIND_WAVE_2 flips. Pure rules and the chamber: ArgelmachLogic.h. The
 * hard mode (D16, the Prototype) fights on this AI through ArgelmachFight.h.
 *
 * Three golem statues stand on pedestals on the chamber's rim (P1-P3, NAVMESH 3.2): dormant, the statue look (211349),
 * not selectable. He summons them himself whenever he is alive and idle (a reload, a wipe: rule 7) and despawns them
 * with every end of the fight. Golems stand still and never melee: the tank only ever holds Argelmach.
 *
 *   AR1 Chain Lightning  at 14 s, then every 15 s: a 3 s cast on his victim, 5 targets, 12% / 15% each; kickable (a
 *                        reward on normal, expected on heroic: the interrupt list)
 *   AR2 Shock            at 6 s, then every 7 s: instant on the tank, 20% / 25% of the tank row
 *   AR3 Lightning Shield at the pull, then every 45 s: 3 charges striking attackers; Magic (a purge is a reward)
 *   AR4 Golem wakes      at 90%, 65% and 40% of his health (the hard mode: D16's thresholds) one golem wakes in a fixed
 *                        order with a yell; each is expected to be killed (the bots' kill order)
 *   AR5 Chemical Bomb    Toxitron, 5 s after its wake, then every 15 s (heroic 12 s): 2 players marked 4 s, then a 5 yd
 *                        cloud where each stands for 30 s, 6% / 9% a second; carry it to the edge
 *   AR6 Poison Mist      Toxitron (heroic), 8 s after its wake, then every 20 s: 2 s cast, 25% to everyone and a Poison
 *                        DoT (a removal is a reward)
 *   AR7 Lethal           Electron, 5 s after its wake, then every 20 s (heroic 15 s): two players tethered; after 8 s,
 *       Attraction       more than 5 yd apart, both take 40% / 60%
 *   AR8 Livewire         Electron (heroic), 8 s after its wake, then every 20 s: a Magic debuff (never the tank) for
 *                        12 s; everyone within 8 yd of the carrier (the carrier too) takes 4% every 2 s; a dispel
 *                        bursts for 30% on everyone else within 8 yd (the bots dispel once nobody is within 8 yd)
 *   AR9 Power Generator  Arcanoton, 5 s after its wake, then every 20 s (heroic 15 s): an Arcane Orb drifts from the
 *                        golem to him in 10 s; walking into it pops it (the popper takes 10% / 15% and gains
 *                        Overcharged, +10% damage, 30 s, 3 stacks); an orb that arrives gives him Empowered (+15%
 *                        damage, 30 s, 5)
 *   AR10 Arcane          Arcanoton (heroic), 8 s after its wake, then every 20 s: a bomb lands on a spot after 4 s;
 *        Overcharge      one player catches it for 30%, or everyone takes 40%
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "brd argelmach <mechanic> ..."
 * (module.dungeonbosses); `.dbtest brd argelmach <mechanic>` fires one on demand.
 */

#include "ArenaGuard.h"
#include "ArgelmachFight.h"
#include "ArgelmachLogic.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DungeonKit.h"
#include "DungeonKitChase.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WorldSession.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdArgelmach;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "argelmach";
    uint32 constexpr kIdleCheckMs = 1000;
    uint32 constexpr kRetryMs = 1000;       // a cast refused (busy): the beat tries again this soon

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    ArgelmachHardModeFactory& HardModeFactory()
    {
        static ArgelmachHardModeFactory factory;
        return factory;
    }

    ArgelmachIdleHook& IdleHook()
    {
        static ArgelmachIdleHook hook;
        return hook;
    }

    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_BRD_STALKER) != nullptr;
    }

    // The chamber's floor under (x, y) near its height; the chamber's height when the probe finds nothing close.
    float FloorZ(WorldObject const* ref, float x, float y)
    {
        float const z = ref->GetMap()->GetHeight(ref->GetPhaseMask(), x, y, kChamberZ + 3.f, true, 10.f);
        return (z > INVALID_HEIGHT && std::fabs(z - kChamberZ) <= 4.f) ? z : kChamberZ;
    }

    std::vector<Position> ChamberPositions()
    {
        std::vector<Position> out;
        out.reserve(kChamber.size());
        for (Vec2 const& p : kChamber)
            out.emplace_back(p.x, p.y, kChamberZ, 0.f);
        return out;
    }

    // The bots' hard bounds while a mechanic of the fight is in view: the chamber's floor (the passage south is out).
    BossMechanics::SpotBounds ChamberBounds()
    {
        return BossMechanics::SpotBounds().Polygon(ChamberPositions(), kChamberZMin, kChamberZMax);
    }

    // AR5's carrier rule: to the chamber's edge, away from the group, never onto a pedestal (its golem's melee).
    BossMechanics::DropSpotRule BombDropRule()
    {
        BossMechanics::DropSpotRule rule;
        rule.Room(ChamberPositions()).Edge().Away().Within(ChamberBounds());
        for (Point3 const& pedestal : kPedestals)
            rule.Avoid(Position(pedestal.x, pedestal.y, pedestal.z, 0.f), kBombPedestalAvoidYd);
        return rule;
    }

    void RemoveFromMap(Map* map, uint32 spellId)
    {
        if (!map)
            return;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                player->RemoveAurasDueToSpell(spellId);
    }
}

void BrdArgelmach::RegisterArgelmachHardMode(ArgelmachHardModeFactory factory)
{
    HardModeFactory() = std::move(factory);
}

void BrdArgelmach::RegisterArgelmachIdleHook(ArgelmachIdleHook hook)
{
    IdleHook() = std::move(hook);
}

std::unique_ptr<ArgelmachHardMode> BrdArgelmach::CreateArgelmachHardMode(Creature* boss)
{
    ArgelmachHardModeFactory const& factory = HardModeFactory();
    return factory ? factory(boss) : nullptr;
}

// -------------------------------------------------------------------------------------------------------------------
// The golems (Toxitron 300833, Electron 300834, Arcanoton 300835; D16's Magmatron 300836 may use it too): they stand
// on their pedestals, never move, never melee and never pick a fight. Argelmach drives them: he wakes them, casts their
// signatures through them and despawns them with the fight. Dormant (not selectable, not attackable, the statue look
// SPELL_AR_STATUE) until woken.
// -------------------------------------------------------------------------------------------------------------------

struct npc_brd_argelmach_golem : public ScriptedAI
{
    explicit npc_brd_argelmach_golem(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetCombatMovement(false);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    // Argelmach owns its life: it never walks home and never resets on its own (his cleanup despawns it).
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// The Arcane Orb 300837 (AR9): the kit's CrawlPickups moves it and pops it; it only stays out of every fight.
struct npc_brd_argelmach_arcane_orb : public ScriptedAI
{
    explicit npc_brd_argelmach_arcane_orb(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }
    void EnterEvadeMode(EvadeReason /*why*/) override { }
    void UpdateAI(uint32 /*diff*/) override { }
};

// -------------------------------------------------------------------------------------------------------------------
// Golem Lord Argelmach 8983
// -------------------------------------------------------------------------------------------------------------------

struct boss_golem_lord_argelmach_rework : public BossAI, public ArgelmachFight
{
    explicit boss_golem_lord_argelmach_rework(Creature* creature)
        : BossAI(creature, BOSS_ARGELMACH), _arena(ArgelmachArena(), LeashOptions(kBossLogName)) { }

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

        Cleanup(false, false);  // a `.dbtest` mechanic out of combat may have left something behind (statues stay)
        EnsureStatues();
        _heroic = IsHeroicMap(me);
        bool hardMode = _heroic && instance && instance->GetData(DATA_CONSOLE_ARMED) != 0;
        if (hardMode)
        {
            // The handler first: an armed console with no handler registered runs the normal heroic.
            _hardMode = CreateArgelmachHardMode(me);
            if (!_hardMode)
            {
                LOG_WARN("module", "brd argelmach: the console is armed but no hard mode handler is registered; the "
                    "pull runs as a normal heroic");
                hardMode = false;
            }
        }
        OnBossPull(me, kBossLogName, hardMode);
        _engaged = true;

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ARGELMACH;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);

        for (Golem g : kGolems)
            _wakeAt[IndexOf(g)] = _hardMode ? _hardMode->WakePct(*this, g, kWakePct[IndexOf(g)])
                : kWakePct[IndexOf(g)];

        Talk(YELL_AR_AGGRO);
        LightningShield();
        _shield.Start(_clockMs, kShieldEveryMs);
        _chain.Start(_clockMs, kChainFirstMs);
        _shock.Start(_clockMs, kShockFirstMs);

        Log("engage", Acore::StringFormat("heroic={} hardmode={} handler={} health={} wake={:.0f}/{:.0f}/{:.0f}",
            _heroic ? 1 : 0, hardMode ? 1 : 0, _hardMode ? 1 : 0, me->GetMaxHealth(), _wakeAt[0], _wakeAt[1],
            _wakeAt[2]));
        if (_hardMode)
        {
            _hardMode->OnEngage(*this);
            // The kit's `pull` line above logs his health before the hard mode changes it.
            Log("pull-health", Acore::StringFormat("health={} hardmode=1", me->GetMaxHealth()));
        }
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup(false);
        BossAI::EnterEvadeMode(why);
    }

    // The credit and the loot (filled by Unit::Kill before this runs; the hard mode bit is the instance's, set at the
    // console and the pull).
    void JustDied(Unit* killer) override
    {
        Talk(YELL_AR_DEATH);
        BossAI::JustDied(killer);
        uint32 killed = 0;
        for (GolemState const& s : _golems)
            killed += s.dead ? 1 : 0;
        Log("death", Acore::StringFormat("golems-killed={} orbs-arrived={} orbs-popped={} hardmode={} killer={}",
            killed, _orbsArrived, _orbsPopped, _hardMode ? 1 : 0, killer ? killer->GetName() : "none"));
        Cleanup(true);
    }

    // The golems are his own (never zoned in here: they join the fight when they wake); everything else he summons
    // (orbs, looks) goes with his summon list.
    void JustSummoned(Creature* summon) override
    {
        if (GolemOfEntry(summon->GetEntry()))
            return;
        summons.Summon(summon);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageTaken(attacker, damage, type, mask);
        if (_hardMode && _engaged)
            _hardMode->OnDamageTaken(*this, attacker, damage);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (spell->Id == SPELL_AR_CHAIN_LIGHTNING)
            Log("chain-lightning-interrupted");
    }

    void UpdateAI(uint32 diff) override
    {
        if (!me->IsEngaged())
        {
            if (me->IsAlive() && !me->IsInEvadeMode())
            {
                _idleMs += diff;
                if (_idleMs >= kIdleCheckMs)
                {
                    _idleMs = 0;
                    EnsureStatues();
                }
                if (IdleHook())
                    IdleHook()(me, diff);
            }
            return;
        }
        if (!UpdateVictim())
            return;

        _clockMs += diff;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        _orbs.Update(me, diff);
        UpdateGolems();
        UpdateTethers();
        UpdateLivewires();
        PruneClouds();
        UpdateBeats();
        if (_hardMode)
            _hardMode->OnUpdate(*this, diff);

        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // His own kit: AR1 Chain Lightning, AR2 Shock, AR3 Lightning Shield
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        if (_shield.Due(_clockMs))
        {
            _shield.Fired(_clockMs, kShieldEveryMs);
            LightningShield();
        }
        if (_shock.Due(_clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
            _shock.Start(_clockMs, Shock() ? kShockEveryMs : kRetryMs);
        if (_chain.Due(_clockMs) && !me->HasUnitState(UNIT_STATE_CASTING))
            _chain.Start(_clockMs, ChainLightning() ? kChainEveryMs : kRetryMs);

        for (Golem g : kGolems)
        {
            GolemState& s = _golems[IndexOf(g)];
            if (!s.awake || s.dead)
                continue;
            if (s.signature.Due(_clockMs))
                FireSignature(g);
            if (s.second.Due(_clockMs))
                FireSecond(g);
        }
    }

    // AR3: the copy of Lightning Shield (triggered); each strike a percent of the non-tank row, set now.
    void LightningShield()
    {
        int32 const strike = static_cast<int32>(DungeonKit::RefFlat(me, kShieldStrikePct(_heroic)));
        me->CastCustomSpell(me, SPELL_AR_LIGHTNING_SHIELD, &strike, nullptr, nullptr, true);
        Log("lightning-shield", Acore::StringFormat("strike={}", strike));
    }

    // AR2: instant on the tank (spell_brd_argelmach_hit sets the percent at launch, times Empowered).
    bool Shock()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        bool const cast = me->CastSpell(victim, SPELL_AR_SHOCK, true) == SPELL_CAST_OK;
        if (cast)
            Log("shock", Acore::StringFormat("on={} pct={:.0f}", victim->GetName(),
                ScaledPct(SPELL_AR_SHOCK, _heroic, Empowered())));
        return cast;
    }

    // AR1: the 3 s cast on his victim (kickable), chaining to 5.
    bool ChainLightning()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        bool const cast = me->CastSpell(victim, SPELL_AR_CHAIN_LIGHTNING, false) == SPELL_CAST_OK;
        if (cast)
            Log("chain-lightning", Acore::StringFormat("on={} pct={:.0f}", victim->GetName(),
                ScaledPct(SPELL_AR_CHAIN_LIGHTNING, _heroic, Empowered())));
        return cast;
    }

    uint32 Empowered() const
    {
        return DungeonKit::Stacks(me, SPELL_AR_EMPOWERED);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR4 The golems: statues, wakes, deaths
    // ----------------------------------------------------------------------------------------------------------------

    // Every golem dormant on its pedestal (idle, and at the pull): a missing one is summoned, one left awake or dead by
    // anything else is replaced.
    void EnsureStatues()
    {
        if (!me->IsInWorld())
            return;
        for (Golem g : kGolems)
        {
            GolemState& s = _golems[IndexOf(g)];
            Creature* golem = s.guid ? me->GetMap()->GetCreature(s.guid) : nullptr;
            if (golem && golem->IsAlive() && !s.awake)
                continue;
            if (golem)
                golem->DespawnOrUnsummon();
            s = GolemState();
            Point3 const p = PedestalOf(g);
            Position const at(p.x, p.y, FloorZ(me, p.x, p.y), PedestalFacing(g));
            TempSummon* statue = me->SummonCreature(EntryOf(g), at, TEMPSUMMON_MANUAL_DESPAWN);
            if (!statue)
                continue;
            s.guid = statue->GetGUID();
            MakeDormant(statue);
        }
    }

    void MakeDormant(Creature* golem)
    {
        golem->SetReactState(REACT_PASSIVE);
        golem->SetCombatMovement(false);
        golem->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        golem->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        golem->SetControlled(true, UNIT_STATE_ROOT);
        if (!golem->HasAura(SPELL_AR_STATUE))
            golem->AddAura(SPELL_AR_STATUE, golem);
    }

    bool WakeGolem(Golem g, char const* why) override
    {
        GolemState& s = _golems[IndexOf(g)];
        Creature* golem = s.guid ? me->GetMap()->GetCreature(s.guid) : nullptr;
        if (s.awake || !golem || !golem->IsAlive())
            return false;
        s.awake = true;
        golem->RemoveAurasDueToSpell(SPELL_AR_STATUE);
        golem->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        golem->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        golem->CastSpell(golem, SPELL_AR_GOLEM_WAKES, true);
        JoinFight(golem);
        Talk(WakeYellOf(g));
        s.signature.Start(_clockMs, kSignatureDelayMs);
        if (_heroic)
            s.second.Start(_clockMs, SecondFirstMs(g));
        Log("golem-wakes", Acore::StringFormat("golem={} why={} health={:.0f}%", NameOf(g), why, me->GetHealthPct()));
        if (_hardMode)
            _hardMode->OnGolemWoken(*this, g, golem);
        return true;
    }

    void JoinFight(Creature* unit) override
    {
        if (!unit)
            return;
        Mechanic::TrackUnit(me, unit);
        // Everyone in the fight at 0 (a one-entry threat list evades); it never attacks.
        for (Player* player : FightPlayers())
            unit->GetThreatMgr().AddThreat(player, 0.f, nullptr, true, true);
    }

    // The wakes by his health, the deaths by the golems'.
    void UpdateGolems()
    {
        std::array<bool, kGolemCount> woken{};
        for (Golem g : kGolems)
            woken[IndexOf(g)] = _golems[IndexOf(g)].awake;
        for (Golem g : GolemsToWake(me->GetHealthPct(), _wakeAt, woken))
            WakeGolem(g, "health");

        for (Golem g : kGolems)
        {
            GolemState& s = _golems[IndexOf(g)];
            if (!s.awake || s.dead)
                continue;
            Creature* golem = s.guid ? me->GetMap()->GetCreature(s.guid) : nullptr;
            if (golem && golem->IsAlive())
                continue;
            s.dead = true;
            s.signature.Stop();
            s.second.Stop();
            Log("golem-killed", Acore::StringFormat("golem={} health={:.0f}%", NameOf(g), me->GetHealthPct()));
            if (_hardMode)
                _hardMode->OnGolemDied(*this, g, golem);
        }
    }

    static uint32 SecondFirstMs(Golem g)
    {
        switch (g)
        {
            case Golem::Toxitron:   return kMistFirstMs;
            case Golem::Electron:   return kLivewireFirstMs;
            case Golem::Arcanoton:  return kOverchargeFirstMs;
        }
        return kMistFirstMs;
    }

    void FireSignature(Golem g)
    {
        auto& s = _golems[IndexOf(g)];
        Creature* golem = me->GetMap()->GetCreature(s.guid);
        switch (g)
        {
            case Golem::Toxitron:
                s.signature.Fired(_clockMs, kBombEveryMs(_heroic));
                ChemicalBomb(golem, kBombMarks, nullptr);
                break;
            case Golem::Electron:
                s.signature.Fired(_clockMs, kTetherEveryMs(_heroic));
                LethalAttraction(golem, nullptr);
                break;
            case Golem::Arcanoton:
                s.signature.Fired(_clockMs, kOrbEveryMs(_heroic));
                if (golem)
                    PowerGenerator(golem->GetPosition());
                break;
        }
    }

    void FireSecond(Golem g)
    {
        auto& s = _golems[IndexOf(g)];
        Creature* golem = me->GetMap()->GetCreature(s.guid);
        switch (g)
        {
            case Golem::Toxitron:
                // A cast bar on the golem: a busy golem tries again in a second.
                s.second.Start(_clockMs, PoisonMist(golem) ? kMistEveryMs : kRetryMs);
                break;
            case Golem::Electron:
                s.second.Fired(_clockMs, kLivewireEveryMs);
                Livewire(golem, nullptr);
                break;
            case Golem::Arcanoton:
                s.second.Fired(_clockMs, kOverchargeEveryMs);
                ArcaneOvercharge(golem, std::nullopt);
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR5 Chemical Bomb and its clouds; AR6 Poison Mist (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    uint32 ChemicalBomb(Unit* source, uint32 count, Player* forced) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // the tank too (ruling 88)
        std::vector<Player*> targets;
        if (forced)
        {
            targets.push_back(forced);
            rule.exclude.push_back(forced->GetGUID().GetRawValue());
        }
        if (targets.size() < count)
            for (Player* p : DungeonKit::PickPlayers(me, rule, count - static_cast<uint32>(targets.size())))
                targets.push_back(p);
        uint32 marked = 0;
        for (Player* target : targets)
            if (MarkBomb(source, target))
                ++marked;
        Log("chemical-bomb", Acore::StringFormat("marks={} of={} source={}", marked, count,
            source ? source->GetName() : "none"));
        return marked;
    }

    bool MarkBomb(Unit* source, Player* target)
    {
        if (!target)
            return false;
        DungeonKit::ImpactSpec impact;
        impact.pct = 0.f;           // telegraph only: the cloud is the hit
        impact.weakened = false;
        impact.tag = TAG_AR_CHEMICAL_BOMB;
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        MechanicRef ref = DungeonKit::FollowThenLand(me, target, kCloudRadiusYd, Ms(kBombWarnMs), impact,
            [map, guid](Creature* /*owner*/, Position const& spot, BossMechanics::ResolveResult const& result)
            {
                if (result.fizzled)
                    return;
                if (boss_golem_lord_argelmach_rework* ai = AIOf(map, guid))
                    ai->CloudLanded(spot);
            });
        if (!ref.IsValid())
            return false;
        ref.DropSpot(BombDropRule()).Within(ChamberBounds());
        Track(ref.Handle());
        Unit* caster = source ? source : static_cast<Unit*>(me);
        caster->CastSpell(target, SPELL_AR_CHEMICAL_BOMB, true);
        Log("chemical-bomb-mark", Acore::StringFormat("on={} tank={}", target->GetName(),
            me->GetVictim() == target ? 1 : 0));
        return true;
    }

    // The mark's 4 s are up: the cloud lies where the carrier stood (the bots carry theirs to the edge).
    void CloudLanded(Position const& spot)
    {
        if (!_engaged)
            return;
        float const pct = kCloudPct(_heroic);
        DungeonKit::LingerSpec linger;
        linger.duration = Ms(kCloudLifeMs);
        linger.tick = Ms(kCloudTickMs);
        linger.pct = pct;
        linger.school = SPELL_SCHOOL_NATURE;
        linger.spellId = SPELL_AR_CHEMICAL_CLOUD;
        linger.tag = TAG_AR_CHEMICAL_CLOUD;
        MechanicRef ref = DungeonKit::Linger(me, BossMechanics::Shapes::Circle(BossMechanics::Anchor(spot),
            kCloudRadiusYd), linger);
        ref.Within(ChamberBounds());
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return;
        Track(handle);
        Cloud cloud;
        cloud.at = spot;
        cloud.zone = handle;
        cloud.endMs = _clockMs + kCloudLifeMs;
        if (StalkerExists())
            if (TempSummon* look = me->SummonCreature(NPC_BRD_STALKER, spot, TEMPSUMMON_TIMED_DESPAWN, kCloudLifeMs))
            {
                look->CastSpell(look, SPELL_AR_CHEMICAL_CLOUD_LOOK, true);
                cloud.look = look->GetGUID();
            }
        _clouds.push_back(cloud);
        Log("chemical-cloud", Acore::StringFormat("at=({:.1f}, {:.1f}) r={:.0f} pct={:.0f} clouds={}",
            spot.GetPositionX(), spot.GetPositionY(), kCloudRadiusYd, pct, _clouds.size()));
    }

    void PruneClouds()
    {
        std::erase_if(_clouds, [this](Cloud const& c) { return _clockMs >= c.endMs; });
    }

    std::vector<Position> Clouds() const override
    {
        std::vector<Position> out;
        for (Cloud const& c : _clouds)
            if (_clockMs < c.endMs)
                out.push_back(c.at);
        return out;
    }

    std::vector<Position> TakeClouds(char const* why) override
    {
        std::vector<Position> out;
        for (Cloud const& c : _clouds)
        {
            if (_clockMs >= c.endMs)
                continue;
            out.push_back(c.at);
            Mechanic::Cancel(me, c.zone);
            if (Creature* look = me->GetMap()->GetCreature(c.look))
                look->DespawnOrUnsummon();
        }
        _clouds.clear();
        Log("clouds-taken", Acore::StringFormat("why={} clouds={}", why, out.size()));
        return out;
    }

    // AR6 (heroic): Toxitron's 2 s cast; the spell's own area hit and Poison DoT (the kit's refflat scripts).
    bool PoisonMist(Creature* toxitron)
    {
        if (!toxitron || !toxitron->IsAlive() || toxitron->HasUnitState(UNIT_STATE_CASTING))
            return false;
        bool const cast = toxitron->CastSpell(toxitron, SPELL_AR_POISON_MIST, false) == SPELL_CAST_OK;
        if (cast)
            Log("poison-mist", Acore::StringFormat("pct={:.0f} dot={:.0f}%/{}s", kMistPct, kMistTickPct,
                kMistTickMs / 1000));
        return cast;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR7 Lethal Attraction; AR8 Livewire (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool LethalAttraction(Unit* source, Player* forced) override
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // the tank too (ruling 88)
        std::vector<Player*> pair;
        if (forced)
        {
            pair.push_back(forced);
            rule.exclude.push_back(forced->GetGUID().GetRawValue());
        }
        for (Player* p : DungeonKit::PickPlayers(me, rule, 2 - static_cast<uint32>(pair.size())))
            pair.push_back(p);
        if (pair.size() < 2 || !pair[0] || !pair[1])
        {
            Log("lethal-attraction", "fewer than two players");
            return false;
        }
        Player* a = pair[0];
        Player* b = pair[1];
        // The bot job: b stands within 5 yd of a until the jolt (telegraph only: the script judges the pair).
        BossMechanics::Eligibility who;
        who.carriers.insert(b->GetGUID());
        MechanicRef ref = Mechanic::Stack(me, a, kTetherRangeYd, Ms(kTetherMs));
        ref.Eligible(who).Within(ChamberBounds()).Tag(TAG_AR_LETHAL_ATTRACTION);
        MechanicHandle const handle = ref.Handle();
        Track(handle);
        Unit* caster = source ? source : static_cast<Unit*>(me);
        caster->CastSpell(a, SPELL_AR_LETHAL_ATTRACTION, true);
        caster->CastSpell(b, SPELL_AR_LETHAL_ATTRACTION, true);
        _tethers.push_back({ a->GetGUID(), b->GetGUID(), _clockMs + kTetherMs });
        Log("lethal-attraction", Acore::StringFormat("a={} b={} apart={:.1f}", a->GetName(), b->GetName(),
            a->GetDistance2d(b)));
        return true;
    }

    // At 8 s: more than 5 yd apart, both take the jolt.
    void UpdateTethers()
    {
        for (auto it = _tethers.begin(); it != _tethers.end();)
        {
            if (_clockMs < it->resolveMs)
            {
                ++it;
                continue;
            }
            Player* a = ObjectAccessor::GetPlayer(*me, it->a);
            Player* b = ObjectAccessor::GetPlayer(*me, it->b);
            if (a)
                a->RemoveAurasDueToSpell(SPELL_AR_LETHAL_ATTRACTION);
            if (b)
                b->RemoveAurasDueToSpell(SPELL_AR_LETHAL_ATTRACTION);
            if (a && b && a->IsAlive() && b->IsAlive() && a->GetMap() == me->GetMap() && b->GetMap() == me->GetMap())
            {
                float const apart = a->GetDistance2d(b);
                if (TetherHolds(apart))
                    Log("lethal-attraction-held", Acore::StringFormat("apart={:.1f}", apart));
                else
                {
                    DungeonKit::RegistryHitSpec hit;
                    hit.pct = kTetherPct(_heroic);
                    hit.school = SPELL_SCHOOL_NATURE;
                    hit.spellId = SPELL_AR_LETHAL_JOLT;
                    hit.weakened = false;
                    hit.tag = TAG_AR_LETHAL_ATTRACTION;
                    Track(DungeonKit::RegistryHit(me, GuidSet{ a->GetGUID(), b->GetGUID() }, hit));
                    Log("lethal-attraction-jolt", Acore::StringFormat("apart={:.1f} pct={:.0f}", apart, hit.pct));
                }
            }
            it = _tethers.erase(it);
        }
    }

    // AR8 (heroic): Electron's Magic debuff on one player (not the tank, kLivewireMarksTank); the RunOut keeps the
    // others 8 yd off it.
    bool Livewire(Unit* source, Player* forced)
    {
        DungeonKit::PickRule rule = LivewirePickRule();
        for (LivewireState const& l : _livewires)
            rule.exclude.push_back(l.carrier.GetRawValue());
        Player* carrier = forced ? forced : DungeonKit::PickPlayer(me, rule);
        if (!carrier)
        {
            Log("livewire", "no target");
            return false;
        }
        Unit* caster = source ? source : static_cast<Unit*>(me);
        caster->CastSpell(carrier, SPELL_AR_LIVEWIRE, true);
        if (!carrier->HasAura(SPELL_AR_LIVEWIRE))
        {
            Log("livewire", Acore::StringFormat("on={} refused", carrier->GetName()));
            return false;
        }
        MechanicRef ref = Mechanic::RunOut(me, carrier, kLivewireRadiusYd, Ms(kLivewireMs));
        ref.Within(ChamberBounds()).Tag(TAG_AR_LIVEWIRE);
        MechanicHandle const handle = ref.Handle();
        Track(handle);
        _livewires.push_back({ carrier->GetGUID(), _clockMs + kLivewireMs, _clockMs + kLivewirePulseMs, handle });
        Log("livewire", Acore::StringFormat("on={} tank={}", carrier->GetName(), me->GetVictim() == carrier ? 1 : 0));
        return true;
    }

    // Every 2 s while the debuff holds: everyone within 8 yd of the carrier (the carrier too) takes the pulse. Gone
    // (dispelled, run out, the carrier dead or away): the RunOut ends.
    void UpdateLivewires()
    {
        for (auto it = _livewires.begin(); it != _livewires.end();)
        {
            Player* carrier = ObjectAccessor::GetPlayer(*me, it->carrier);
            bool const holds = carrier && carrier->IsAlive() && carrier->GetMap() == me->GetMap()
                && carrier->HasAura(SPELL_AR_LIVEWIRE) && _clockMs < it->endMs;
            if (!holds)
            {
                Mechanic::Cancel(me, it->runOut);
                it = _livewires.erase(it);
                continue;
            }
            if (_clockMs >= it->nextPulseMs)
            {
                it->nextPulseMs += kLivewirePulseMs;
                LivewirePulse(carrier);
            }
            ++it;
        }
    }

    void LivewirePulse(Player* carrier)
    {
        GuidSet near;
        for (Player* player : FightPlayers())
            if (InLivewire(player->GetDistance2d(carrier), player->GetPositionZ() - carrier->GetPositionZ()))
                near.insert(player->GetGUID());
        DungeonKit::RegistryHitSpec hit;
        hit.pct = kLivewirePulsePct;
        hit.school = SPELL_SCHOOL_NATURE;
        hit.spellId = SPELL_AR_LIVEWIRE_PULSE;
        hit.weakened = false;
        hit.tag = TAG_AR_LIVEWIRE;
        Track(DungeonKit::RegistryHit(me, near, hit));
        Log("livewire-pulse", Acore::StringFormat("carrier={} hit={}", carrier->GetName(), near.size()));
    }

    // The dispel (spell_brd_argelmach_livewire): a burst on everyone else within 8 yd of the carrier.
    void LivewireDispelled(Unit* carrier)
    {
        if (!_engaged || !carrier)
            return;
        MechanicRef ref = Mechanic::RunOut(me, carrier, kLivewireRadiusYd, Ms(0));
        ref.Damage(kLivewireBurstPct).TankDamage(kLivewireBurstPct).Spell(SPELL_AR_LIVEWIRE_BURST).NoTelegraph()
            .Tag(TAG_AR_LIVEWIRE_BURST);
        Track(ref.Handle());
        std::size_t near = 0;
        for (Player* player : FightPlayers())
            if (player != carrier && InLivewire(player->GetDistance2d(carrier),
                player->GetPositionZ() - carrier->GetPositionZ()))
                ++near;
        Log("livewire-dispelled", Acore::StringFormat("carrier={} allies-near={} pct={:.0f}", carrier->GetName(), near,
            kLivewireBurstPct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AR9 Power Generator; AR10 Arcane Overcharge (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool PowerGenerator(Position const& from) override
    {
        Position const at(from.GetPositionX(), from.GetPositionY(), FloorZ(me, from.GetPositionX(),
            from.GetPositionY()) + 1.f, 0.f);
        float const distance = me->GetDistance2d(at.GetPositionX(), at.GetPositionY());
        DungeonKit::CrawlPickupSpec spec;
        spec.entry = NPC_BRD_ARCANE_ORB;
        spec.radius = kOrbRadiusYd;
        spec.wait = Ms(0);
        spec.crawlSpeed = OrbSpeed(distance);
        spec.reach = kOrbReachYd;
        spec.life = Ms(kOrbLifeMs);
        spec.who.playersOnly = true;
        spec.tag = TAG_AR_POWER_GENERATOR;
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        spec.onPick = [map, guid](Player* taker, Position const& /*at*/)
        {
            if (boss_golem_lord_argelmach_rework* ai = AIOf(map, guid))
                ai->OrbPopped(taker);
        };
        spec.onReach = [map, guid](ObjectGuid /*goal*/, Position const& /*at*/)
        {
            if (boss_golem_lord_argelmach_rework* ai = AIOf(map, guid))
                ai->OrbArrived();
        };
        spec.onExpire = [map, guid](Position const& /*at*/)
        {
            if (boss_golem_lord_argelmach_rework* ai = AIOf(map, guid))
                ai->Log("power-generator-faded");
        };
        DungeonKit::CrawlGoal goal;
        goal.unit = me->GetGUID();
        if (!_orbs.Add(me, at, std::move(spec), goal))
        {
            Log("power-generator", "refused");
            return false;
        }
        Log("power-generator", Acore::StringFormat("from=({:.1f}, {:.1f}) yd={:.1f} speed={:.2f}", at.GetPositionX(),
            at.GetPositionY(), distance, OrbSpeed(distance)));
        return true;
    }

    void OrbPopped(Player* taker)
    {
        if (!_engaged || !taker)
            return;
        ++_orbsPopped;
        DungeonKit::RegistryHitSpec hit;
        hit.pct = kOrbPopPct(_heroic);
        hit.school = SPELL_SCHOOL_ARCANE;
        hit.spellId = SPELL_AR_POWER_SURGE;
        hit.weakened = false;
        hit.tag = TAG_AR_POWER_GENERATOR;
        Track(DungeonKit::RegistryHit(me, GuidSet{ taker->GetGUID() }, hit));
        uint32 const stacks = DungeonKit::AddStacks(taker, SPELL_AR_OVERCHARGED, 1, nullptr, kOverchargedMaxStacks);
        Log("power-generator-popped", Acore::StringFormat("by={} overcharged={} pct={:.0f}", taker->GetName(), stacks,
            hit.pct));
    }

    void OrbArrived()
    {
        if (!_engaged)
            return;
        ++_orbsArrived;
        uint32 const stacks = DungeonKit::AddStacks(me, SPELL_AR_EMPOWERED, 1, me, kEmpoweredMaxStacks);
        Log("power-generator-arrived", Acore::StringFormat("empowered={}", stacks));
    }

    // AR10 (heroic): a 3 yd spot on the open floor (ArgelmachLogic.h PickOverchargeSpot), 4 s; caught: the catchers
    // take 30%; missed: everyone takes 40%. `forced`: that spot (a test).
    bool ArcaneOvercharge(Unit* source, std::optional<Vec2> forced)
    {
        Vec2 const spot = forced ? *forced : PickOverchargeSpot(DungeonKit::PlaneOf(me), []()
        {
            return static_cast<float>(rand_norm());
        });
        Position const at(spot.x, spot.y, FloorZ(me, spot.x, spot.y), 0.f);
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        ObjectGuid const from = source ? source->GetGUID() : me->GetGUID();
        MechanicRef ref = Mechanic::Soak(me, BossMechanics::Anchor(at), kOverchargeRadiusYd, 1, Ms(kOverchargeWarnMs));
        ref.Within(ChamberBounds()).Tag(TAG_AR_ARCANE_OVERCHARGE);
        ref.OnResolve([map, guid, from, at](BossMechanics::ResolveResult const& r)
        {
            if (boss_golem_lord_argelmach_rework* ai = AIOf(map, guid))
                ai->OverchargeLanded(from, at, r);
        });
        MechanicHandle const handle = ref.Handle();
        if (!handle)
            return false;
        Track(handle);
        Log("arcane-overcharge", Acore::StringFormat("at=({:.1f}, {:.1f}) boss-yd={:.1f}", spot.x, spot.y,
            DungeonKit::Distance(spot, DungeonKit::PlaneOf(me))));
        return true;
    }

    void OverchargeLanded(ObjectGuid from, Position const& at, BossMechanics::ResolveResult const& r)
    {
        if (!_engaged)
            return;
        Unit* source = from == me->GetGUID() ? static_cast<Unit*>(me) : me->GetMap()->GetCreature(from);
        if (!source || !source->IsAlive())
            source = me;
        source->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_AR_OVERCHARGE_BOMB, true);
        DungeonKit::RegistryHitSpec hit;
        hit.school = SPELL_SCHOOL_ARCANE;
        hit.weakened = false;
        hit.tag = TAG_AR_ARCANE_OVERCHARGE;
        GuidSet targets;
        if (!r.hits.empty())
        {
            hit.pct = kOverchargeCatchPct;
            hit.spellId = SPELL_AR_OVERCHARGE_CATCH;
            targets.insert(r.hits.begin(), r.hits.end());
        }
        else
        {
            hit.pct = kOverchargeBlastPct;
            hit.spellId = SPELL_AR_OVERCHARGE_BLAST;
            for (Player* player : FightPlayers())
                targets.insert(player->GetGUID());
        }
        Track(DungeonKit::RegistryHit(me, targets, hit));
        Log(r.hits.empty() ? "arcane-overcharge-missed" : "arcane-overcharge-caught",
            Acore::StringFormat("hit={} pct={:.0f}", targets.size(), hit.pct));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // ArgelmachFight (D16's view) and the bots
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Boss() override { return me; }
    bool Heroic() const override { return _heroic; }
    ArgelmachHardMode* ActiveHardMode() override { return _hardMode.get(); }
    uint64 FightMs() const override { return _clockMs; }

    std::vector<Player*> FightPlayers() override
    {
        std::vector<Player*> players;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
            if (Player* player = ref->GetVictim() ? ref->GetVictim()->ToPlayer() : nullptr)
                if (player->IsAlive() && !player->IsGameMaster())
                    players.push_back(player);
        return players;
    }

    Creature* GolemUnit(Golem g) override
    {
        ObjectGuid const guid = _golems[IndexOf(g)].guid;
        return guid && me->IsInWorld() ? me->GetMap()->GetCreature(guid) : nullptr;
    }

    bool GolemAwake(Golem g) const override { return _golems[IndexOf(g)].awake; }
    bool GolemDead(Golem g) const override { return _golems[IndexOf(g)].dead; }

    void Track(MechanicHandle handle) override
    {
        if (handle)
            _handles.push_back(handle);
    }

    void TrackSummon(Creature* summon) override
    {
        if (summon)
            summons.Summon(summon);
    }

    void Log(char const* mechanic, std::string const& detail = {}) override
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // Kill order: the awake golem (damage dealers; the tank keeps Argelmach), then him. Chain Lightning on the
    // interrupt list (a reward on normal, expected on heroic). Livewire on the dispel list only once no ally is within
    // 8 yd of the carrier (WP-DS: NearPlayer counts the carrier's allies), Poison Mist as a reward. Lightning Shield on
    // the purge list (a reward).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_ARGELMACH, SPELL_AR_CHAIN_LIGHTNING, _heroic ? 3 : 1);
        d.dispels.emplace_back(SPELL_AR_LIVEWIRE, 3, false, std::chrono::milliseconds(0),
            BossMechanics::Condition::Not(BossMechanics::Condition::NearPlayer(kLivewireRadiusYd)));
        d.dispels.emplace_back(SPELL_AR_POISON_MIST, 1);
        d.purges.emplace_back(NPC_ARGELMACH, SPELL_AR_LIGHTNING_SHIELD, 1);
        for (Golem g : kGolems)
            d.targets.push_back(BossMechanics::TargetEntry(EntryOf(g), 2, BossMechanics::Who::Dps,
                BossMechanics::Condition::LacksAura(SPELL_AR_STATUE)));
        if (_hardMode)
            _hardMode->ConfigureDescriptor(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest` entry points
    // ----------------------------------------------------------------------------------------------------------------

    std::string TestNeeds(char const* what) const
    {
        if (!me->IsEngaged())
            return Acore::StringFormat("Golem Lord Argelmach must be in combat ({}).", what);
        return {};
    }

    std::string TestWake(Optional<uint32> which)
    {
        if (std::string error = TestNeeds("wake"); !error.empty())
            return error;
        if (which && (*which < 1 || *which > kGolemCount))
            return "Golem 1 (Toxitron), 2 (Electron) or 3 (Arcanoton).";
        for (Golem g : kGolems)
        {
            if (which && IndexOf(g) + 1 != *which)
                continue;
            if (WakeGolem(g, "dbtest"))
                return {};
            if (which)
                return Acore::StringFormat("{} is already awake or not there.", NameOf(g));
        }
        return "Every golem is already awake.";
    }

    std::string TestGolem(Golem g, char const* what)
    {
        if (std::string error = TestNeeds(what); !error.empty())
            return error;
        if (!GolemAwake(g) || GolemDead(g))
            return Acore::StringFormat("{} is not awake (`.dbtest brd argelmach wake {}`).", NameOf(g), IndexOf(g) + 1);
        return {};
    }

    std::string TestBomb(Player* gm)
    {
        if (std::string error = TestGolem(Golem::Toxitron, "bomb"); !error.empty())
            return error;
        return ChemicalBomb(GolemUnit(Golem::Toxitron), kBombMarks, gm) ? std::string() : "No mark was placed.";
    }

    std::string TestMist()
    {
        if (std::string error = TestGolem(Golem::Toxitron, "mist"); !error.empty())
            return error;
        return PoisonMist(GolemUnit(Golem::Toxitron)) ? std::string() : "Toxitron did not cast (busy?).";
    }

    std::string TestTether(Player* gm)
    {
        if (std::string error = TestGolem(Golem::Electron, "tether"); !error.empty())
            return error;
        return LethalAttraction(GolemUnit(Golem::Electron), gm) ? std::string() : "It needs two players.";
    }

    std::string TestLivewire(Player* gm)
    {
        if (std::string error = TestGolem(Golem::Electron, "livewire"); !error.empty())
            return error;
        return Livewire(GolemUnit(Golem::Electron), gm) ? std::string() : "Livewire was refused.";
    }

    std::string TestOrb()
    {
        if (std::string error = TestGolem(Golem::Arcanoton, "orb"); !error.empty())
            return error;
        Creature* arcanoton = GolemUnit(Golem::Arcanoton);
        return arcanoton && PowerGenerator(arcanoton->GetPosition()) ? std::string() : "The orb was refused.";
    }

    std::string TestOvercharge(Player* gm)
    {
        if (std::string error = TestGolem(Golem::Arcanoton, "overcharge"); !error.empty())
            return error;
        std::optional<Vec2> spot;
        if (gm)
            spot = DungeonKit::PlaneOf(gm);
        return ArcaneOvercharge(GolemUnit(Golem::Arcanoton), spot) ? std::string() : "The bomb was refused.";
    }

    std::string TestChain()
    {
        if (std::string error = TestNeeds("chain"); !error.empty())
            return error;
        return ChainLightning() ? std::string() : "Chain Lightning did not cast (no victim, or busy).";
    }

    std::string TestState() const
    {
        std::string golems;
        for (Golem g : kGolems)
        {
            GolemState const& s = _golems[IndexOf(g)];
            golems += Acore::StringFormat("{}{}={}@{:.0f}", golems.empty() ? "" : " ", NameOf(g),
                s.dead ? "dead" : s.awake ? "awake" : s.guid ? "dormant" : "missing", _wakeAt[IndexOf(g)]);
        }
        return Acore::StringFormat("clock={}s heroic={} hardmode={} health={:.0f}% {} clouds={} tethers={} "
            "livewires={} orbs={} popped={} arrived={} empowered={}", _clockMs / 1000, _heroic ? 1 : 0,
            _hardMode ? 1 : 0, me->GetHealthPct(), golems, _clouds.size(), _tethers.size(), _livewires.size(),
            _orbs.Count(), _orbsPopped, _orbsArrived, DungeonKit::Stacks(me, SPELL_AR_EMPOWERED));
    }

    static boss_golem_lord_argelmach_rework* AIOf(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_golem_lord_argelmach_rework*>(boss->AI());
    }

    // The AI of the Argelmach of `unit`'s map (spell scripts: the Livewire dispel).
    static boss_golem_lord_argelmach_rework* AIOn(Unit const* unit)
    {
        if (!unit || !unit->IsInWorld())
            return nullptr;
        Creature* boss = unit->FindNearestCreature(NPC_ARGELMACH, 200.f, true);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_golem_lord_argelmach_rework*>(boss->AI());
    }

    void OnLivewireDispelled(Unit* carrier)
    {
        LivewireDispelled(carrier);
    }

private:
    struct GolemState
    {
        ObjectGuid guid;
        Beat signature;
        Beat second;
        bool awake = false;
        bool dead = false;
    };

    struct Cloud
    {
        Position at;
        MechanicHandle zone;
        ObjectGuid look;
        uint64 endMs = 0;
    };

    struct TetherState
    {
        ObjectGuid a;
        ObjectGuid b;
        uint64 resolveMs = 0;
    };

    struct LivewireState
    {
        ObjectGuid carrier;
        uint64 endMs = 0;
        uint64 nextPulseMs = 0;
        MechanicHandle runOut;
    };

    // Every way the fight ends (and a new pull): the hard mode undone, the zones, the orbs, the clouds, the tethers,
    // the golems (the next idle tick puts fresh statues up; `golems` false at the pull keeps the dormant statues), the
    // looks; every aura of the fight off the players and him.
    void Cleanup(bool died, bool golems = true)
    {
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        if (me->IsInWorld())
        {
            for (MechanicHandle const& h : _handles)
                Mechanic::Cancel(me, h);
            _orbs.Clear(me);
            for (Cloud const& c : _clouds)
                if (Creature* look = me->GetMap()->GetCreature(c.look))
                    look->DespawnOrUnsummon();
            if (golems)
                for (GolemState const& s : _golems)
                    if (Creature* golem = s.guid ? me->GetMap()->GetCreature(s.guid) : nullptr)
                        golem->DespawnOrUnsummon();
            summons.DespawnAll();
            for (uint32 spell : { SPELL_AR_CHEMICAL_BOMB, SPELL_AR_POISON_MIST, SPELL_AR_LETHAL_ATTRACTION,
                SPELL_AR_LIVEWIRE, SPELL_AR_OVERCHARGED })
                RemoveFromMap(me->GetMap(), spell);
        }
        _handles.clear();
        _clouds.clear();
        _tethers.clear();
        _livewires.clear();
        if (golems)
            _golems = {};
        me->RemoveAurasDueToSpell(SPELL_AR_EMPOWERED);
        me->RemoveAurasDueToSpell(SPELL_AR_LIGHTNING_SHIELD);
        if (me->IsAlive())
            me->SetReactState(REACT_AGGRESSIVE);
        _arena.Reset();
        _chain.Stop();
        _shock.Stop();
        _shield.Stop();
        _wakeAt = kWakePct;
        _engaged = false;
        _clockMs = 0;
        _idleMs = kIdleCheckMs;     // the statues go up on the next idle tick
        _orbsPopped = 0;
        _orbsArrived = 0;
    }

    DungeonKit::ArenaGuard _arena;
    DungeonKit::CrawlPickups _orbs;
    std::unique_ptr<ArgelmachHardMode> _hardMode;
    std::vector<MechanicHandle> _handles;
    std::array<GolemState, kGolemCount> _golems{};
    std::array<float, kGolemCount> _wakeAt = kWakePct;
    std::vector<Cloud> _clouds;
    std::vector<TetherState> _tethers;
    std::vector<LivewireState> _livewires;
    Beat _chain;
    Beat _shock;
    Beat _shield;
    uint64 _clockMs = 0;            // ms since the pull (every AI tick in combat)
    uint32 _idleMs = kIdleCheckMs;
    uint32 _orbsPopped = 0;
    uint32 _orbsArrived = 0;
    bool _heroic = false;
    bool _engaged = false;
};

// -------------------------------------------------------------------------------------------------------------------
// Spell scripts
// -------------------------------------------------------------------------------------------------------------------

// AR1 / AR2: Chain Lightning and Shock deal a percent of the reference row (the tank row on the tank) times his
// Empowered stacks (the spells ignore caster modifiers, so the aura alone would not raise them).
class spell_brd_argelmach_hit : public SpellScript
{
    PrepareSpellScript(spell_brd_argelmach_hit);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        float const pct = ScaledPct(GetSpellInfo()->Id, IsHeroicMap(caster),
            DungeonKit::Stacks(caster, SPELL_AR_EMPOWERED));
        SetEffectValue(static_cast<int32>(DungeonKit::RefFlatOn(caster, GetHitUnit(), pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_brd_argelmach_hit::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// AR8: a dispel of Livewire bursts on everyone else within 8 yd of the carrier (expiry does not).
class spell_brd_argelmach_livewire : public AuraScript
{
    PrepareAuraScript(spell_brd_argelmach_livewire);

    void Dispelled(DispelInfo* /*dispelInfo*/)
    {
        Unit* carrier = GetUnitOwner();
        if (boss_golem_lord_argelmach_rework* ai = boss_golem_lord_argelmach_rework::AIOn(carrier))
            ai->OnLivewireDispelled(carrier);
    }

    void Register() override
    {
        AfterDispel += AuraDispelFn(spell_brd_argelmach_livewire::Dispelled);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest brd argelmach`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    boss_golem_lord_argelmach_rework* FindArgelmachAI(ChatHandler* handler)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_ARGELMACH);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_golem_lord_argelmach_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Golem Lord Argelmach is not running boss_golem_lord_argelmach_rework "
                "(check the ScriptName; wave 2 binds it).");
        return ai;
    }

    Player* GmPlayer(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool Report(ChatHandler* handler, std::string const& error, char const* done)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Golem Lord Argelmach: {}", done);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowBossInfo(handler, NPC_ARGELMACH, BOSS_ARGELMACH);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Golem Lord Argelmach: {}", ai->TestState());
        return true;
    }

    // `.dbtest brd argelmach wake [1-3]`: AR4 now (the next dormant golem, or that one).
    bool HandleWake(ChatHandler* handler, Optional<uint32> which)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestWake(which), "a golem wakes.");
    }

    // `.dbtest brd argelmach bomb`: AR5, you first (Toxitron awake).
    bool HandleBomb(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestBomb(GmPlayer(handler)), "Chemical Bomb marks (4 s, then the clouds).");
    }

    // `.dbtest brd argelmach mist`: AR6 now (Toxitron awake; heroic's spell on any difficulty).
    bool HandleMist(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestMist(), "Poison Mist cast (2 s).");
    }

    // `.dbtest brd argelmach tether`: AR7, you and one other (Electron awake).
    bool HandleTether(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestTether(GmPlayer(handler)), "Lethal Attraction (8 s, keep within 5 yd).");
    }

    // `.dbtest brd argelmach livewire`: AR8 on you (Electron awake; heroic's debuff on any difficulty).
    bool HandleLivewire(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestLivewire(GmPlayer(handler)), "Livewire on you (12 s).");
    }

    // `.dbtest brd argelmach orb`: AR9 from Arcanoton (awake).
    bool HandleOrb(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestOrb(), "an Arcane Orb drifts to him (10 s).");
    }

    // `.dbtest brd argelmach overcharge`: AR10 under you (Arcanoton awake).
    bool HandleOvercharge(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestOvercharge(GmPlayer(handler)), "Arcane Overcharge lands under you in 4 s.");
    }

    // `.dbtest brd argelmach chain`: AR1 on his victim (kick it).
    bool HandleChain(ChatHandler* handler)
    {
        boss_golem_lord_argelmach_rework* ai = FindArgelmachAI(handler);
        if (!ai)
            return false;
        return Report(handler, ai->TestChain(), "Chain Lightning started (3 s).");
    }

    ChatCommandTable const& BossGolemLordArgelmachTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "wake",       HandleWake,       SEC_GAMEMASTER, Console::No },
            { "bomb",       HandleBomb,       SEC_GAMEMASTER, Console::No },
            { "mist",       HandleMist,       SEC_GAMEMASTER, Console::No },
            { "tether",     HandleTether,     SEC_GAMEMASTER, Console::No },
            { "livewire",   HandleLivewire,   SEC_GAMEMASTER, Console::No },
            { "orb",        HandleOrb,        SEC_GAMEMASTER, Console::No },
            { "overcharge", HandleOvercharge, SEC_GAMEMASTER, Console::No },
            { "chain",      HandleChain,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_golem_lord_argelmach_rework()
{
    // The boss binds with wave 2 (an unbound registered name logs "not assigned"); the golems, the orb and the spell
    // scripts are named by their own rows (argelmach.py), declared now, so they register now.
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_golem_lord_argelmach_rework, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_argelmach_golem, BlackrockDepthsRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_brd_argelmach_arcane_orb, BlackrockDepthsRework::kInstanceScriptName);
    RegisterSpellScript(spell_brd_argelmach_hit);
    RegisterSpellScript(spell_brd_argelmach_livewire);
    BrdTest::RegisterBoss("argelmach", BossGolemLordArgelmachTestCommands());
}
