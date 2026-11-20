/*
 * mod-dungeon-bosses, Blackrock Depths D16: Golem Lord Argelmach's hard mode, the Prototype (heroic only). Build spec:
 * docs/dungeons/blackrock-depths-3-manufactory.md "Hard mode" and "Build spec" (AR4, AR11-AR13; rulings 57, 58, 88),
 * handoff sections 3.6, 3.7 row D16, 3.8, 7 #15. It fights on D15's AI (boss_golem_lord_argelmach_rework) through
 * ArgelmachFight.h: D15 makes one Prototype per heroic pull with DATA_CONSOLE_ARMED lit and calls its hooks; the idle
 * hook keeps the fourth statue on its pedestal out of combat. Pure rules and numbers: ArgelmachHardModeLogic.h.
 *
 *   Trigger          the Activation Console (GO 301284, go_brd_activation_console, by the passage mouth; heroic only
 *                    by its spawn mask): out of combat, before the pull, it lights DATA_CONSOLE_ARMED (the instance's
 *                    per-pull flag; refused otherwise) and he yells line 4. The console stays lit (GO state active,
 *                    not selectable) until the attempt ends.
 *   The statue       Magmatron (300836, display 8179) dormant on the fourth pedestal (GO 301288, P4) on heroic while
 *                    he is idle: summoned by the map (not by him, so a pull without the console leaves it standing).
 *   The pull         500k; Magmatron wakes on P4 (100k, joins the fight); Toxitron wakes at 80%, Electron at 60%,
 *                    Arcanoton at 40% (each 50k); the hard mode loot bit (the instance keeps it too).
 *   AR11 Incineration Magmatron, 10 s, then every 25 s: a 3 s Fire bar (line 5); at its start every Chemical Bomb
 *                    cloud ignites (TakeClouds: the cloud is gone, an 8 yd circle shows); at its end 15% to everyone
 *                    and 30% + Weakened within 8 yd of each ignited cloud. Magmatron dying mid-bar puts it out.
 *   AR12 Flamethrower Magmatron, 6 s, then every 15 s: a 2 s Fire bar and a 60 degree, 25 yd cone fixed toward a
 *                    random player (the tank too, ruling 88); 35% + Weakened; it burns Poison Mist off whoever it hits.
 *   AR13 Salvaged    a dead golem (or Magmatron) leaves its wreck (the corpse) on its pedestal and a Salvaged Core
 *        Cores       (300838) runs there (line 6): 10 s later, then at half rate, the core fires the signature, no
 *                    second attack: Chemical Bomb on 1 player every 30 s, Lethal Attraction every 30 s, an Arcane Orb
 *                    every 30 s, Incineration every 50 s (still igniting the clouds).
 *   The end          death: the instance records BOSS_PROTOTYPE (22) and clears the flag; D15's cleanup despawns
 *                    Magmatron, the cores, the wrecks and the statues; the console's poll removes a dormant statue
 *                    left after a kill without the console. Wipe or evade: his heroic health back, the registry
 *                    shapes cancelled (D15), Magmatron and the cores despawned (his summons), the instance clears the
 *                    flag (the console is usable again), the idle hook puts the statue back. A reload: the flag is
 *                    not saved; the idle hook puts the statue back.
 *
 * Every firing logs one INFO line "brd argelmach prototype-<mechanic> ..." (module.dungeonbosses); `.dbtest brd
 * prototype <...>` fires them.
 */

#include "ArgelmachFight.h"
#include "ArgelmachHardModeLogic.h"
#include "ArgelmachLogic.h"
#include "BlackrockDepthsKit.h"
#include "BlackrockDepthsRework.h"
#include "BlackrockDepthsTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DataMap.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitFlex.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "WorldSession.h"
#include <array>
#include <cmath>
#include <list>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockDepthsRework;
using namespace BrdPrototype;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using BrdArgelmach::ArgelmachFight;
using BrdArgelmach::ArgelmachHardMode;
using BrdArgelmach::Beat;

namespace
{
    char const* const kBossLogName = "argelmach";
    char const* const kIdleKey = "brd-prototype";

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(ms);
    }

    void LogPt(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, mechanic, detail);
    }

    // The chamber's floor under (x, y) near its height; the chamber's height when the probe finds nothing close.
    float FloorZ(WorldObject const* ref, float x, float y)
    {
        float const z = ref->GetMap()->GetHeight(ref->GetPhaseMask(), x, y, BrdArgelmach::kChamberZ + 3.f, true,
            10.f);
        return (z > INVALID_HEIGHT && std::fabs(z - BrdArgelmach::kChamberZ) <= 4.f) ? z : BrdArgelmach::kChamberZ;
    }

    Position OnPedestal(WorldObject const* ref, Point3 p, float o)
    {
        return Position(p.x, p.y, FloorZ(ref, p.x, p.y), o);
    }

    // The bots' hard bounds while a shape of the fight is in view: the chamber's floor (as D15's).
    BossMechanics::SpotBounds ChamberBounds()
    {
        std::vector<Position> room;
        room.reserve(BrdArgelmach::kChamber.size());
        for (Vec2 const& p : BrdArgelmach::kChamber)
            room.emplace_back(p.x, p.y, BrdArgelmach::kChamberZ, 0.f);
        return BossMechanics::SpotBounds().Polygon(room, BrdArgelmach::kChamberZMin, BrdArgelmach::kChamberZMax);
    }

    bool StalkerExists()
    {
        return sObjectMgr->GetCreatureTemplate(NPC_BRD_STALKER) != nullptr;
    }

    // Argelmach of `where`'s instance (alive or dead), or nullptr.
    Creature* ArgelmachOf(WorldObject* where)
    {
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        return where->GetMap()->GetCreature(instance->GetGuidData(kGuidBossBase + BOSS_ARGELMACH));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The dormant Magmatron statue on the fourth pedestal (kept on his creature, DataMap: the idle hook and the pull)
    // ----------------------------------------------------------------------------------------------------------------

    struct IdleState : public DataMap::Base
    {
        ObjectGuid statue;
        uint32 checkMs = 0;
    };

    IdleState* IdleOf(Creature* boss)
    {
        return boss->CustomData.GetDefault<IdleState>(kIdleKey);
    }

    bool IsDormant(Creature const* golem)
    {
        return golem
            && StatueDormant(golem->IsAlive(), golem->IsInCombat(), golem->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE));
    }

    // Dormant as D15's statues: passive, rooted, not selectable, not attackable, the statue look (SPELL_AR_STATUE).
    void MakeDormant(Creature* golem)
    {
        golem->SetReactState(REACT_PASSIVE);
        golem->SetCombatMovement(false);
        golem->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        golem->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        golem->SetControlled(true, UNIT_STATE_ROOT);
        if (!golem->HasAura(BrdArgelmach::SPELL_AR_STATUE))
            golem->AddAura(BrdArgelmach::SPELL_AR_STATUE, golem);
    }

    Creature* StatueOf(Creature* boss)
    {
        IdleState* st = IdleOf(boss);
        return st->statue && boss->IsInWorld() ? boss->GetMap()->GetCreature(st->statue) : nullptr;
    }

    void RemoveStatue(Creature* boss)
    {
        if (Creature* statue = StatueOf(boss))
            statue->DespawnOrUnsummon();
        IdleOf(boss)->statue.Clear();
    }

    // The statue on P4, dormant: one left awake, dead or fighting by anything else is replaced. Summoned by the map, so
    // his pull's summon cleanup leaves it standing through a pull without the console (TEMPSUMMON_MANUAL_DESPAWN).
    Creature* EnsureStatue(Creature* boss)
    {
        Creature* statue = StatueOf(boss);
        if (IsDormant(statue))
            return statue;
        RemoveStatue(boss);
        TempSummon* summon = boss->GetMap()->SummonCreature(NPC_BRD_MAGMATRON, OnPedestal(boss,
            BrdArgelmach::kPedestal4, MagmatronFacing()));
        if (!summon)
            return nullptr;
        summon->SetTempSummonType(TEMPSUMMON_MANUAL_DESPAWN);
        MakeDormant(summon);
        IdleOf(boss)->statue = summon->GetGUID();
        return summon;
    }

    // The idle hook (D15: alive, not engaged, not evading): the statue on heroic once wave 2 is bound, none otherwise.
    void StatueIdle(Creature* boss, uint32 diff)
    {
        IdleState* st = IdleOf(boss);
        if (st->checkMs > diff)
        {
            st->checkMs -= diff;
            return;
        }
        st->checkMs = kStatueCheckMs;
        if (!boss->IsInWorld())
            return;
        if (!kWave2Bound || !boss->GetMap()->IsHeroic())
        {
            RemoveStatue(boss);
            return;
        }
        EnsureStatue(boss);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Activation Console
    // ----------------------------------------------------------------------------------------------------------------

    ConsoleRefusal RefusalAt(WorldObject* where)
    {
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (!instance)
            return ConsoleRefusal::NotHeroic;
        ConsoleCheck c;
        c.heroic = where->GetMap()->IsHeroic();
        c.wave2Bound = kWave2Bound;
        c.armed = instance->GetData(DATA_CONSOLE_ARMED) != 0;
        Creature* boss = ArgelmachOf(where);
        c.argelmachAlive = boss && boss->IsAlive();
        c.argelmachBusy = boss && (boss->IsEngaged() || boss->IsInCombat() || boss->IsInEvadeMode());
        c.argelmachState = static_cast<uint32>(instance->GetBossState(BOSS_ARGELMACH));
        return ConsoleRefusalFor(c);
    }

    // Arms the Prototype for `player` at `where` (the console, or the GM). Returns the refusal (None: armed).
    ConsoleRefusal ArmConsole(WorldObject* where, Player* player)
    {
        ConsoleRefusal refusal = RefusalAt(where);
        InstanceScript* instance = where ? where->GetInstanceScript() : nullptr;
        if (refusal == ConsoleRefusal::None && instance)
        {
            instance->SetData(DATA_CONSOLE_ARMED, 1);
            if (!instance->GetData(DATA_CONSOLE_ARMED))
                refusal = ConsoleRefusal::ArgelmachFighting;    // the instance refused it (ConsoleAllowed)
        }
        if (refusal != ConsoleRefusal::None)
        {
            if (player && player->GetSession())
                ChatHandler(player->GetSession()).SendNotification(ConsoleRefusalText(refusal));
            LogPt("prototype-console-refused", Acore::StringFormat("by={} why={}",
                player ? player->GetName() : std::string("none"), uint32(refusal)));
            return refusal;
        }
        Creature* boss = ArgelmachOf(where);
        if (boss && boss->IsAlive() && boss->IsAIEnabled)
        {
            boss->AI()->Talk(BrdArgelmach::YELL_AR_CONSOLE);
            DungeonKit::SetHardModeLoot(boss, true);            // rule 1 (the instance sets it too)
        }
        LogPt("prototype-armed", Acore::StringFormat("by={}", player ? player->GetName() : std::string("none")));
        return ConsoleRefusal::None;
    }
}

// -------------------------------------------------------------------------------------------------------------------
// The hard mode of one pull (D15 makes it at a heroic pull with the console armed and ends it with the pull)
// -------------------------------------------------------------------------------------------------------------------

class Prototype final : public ArgelmachHardMode
{
public:
    // ---- the policy hooks -------------------------------------------------------------------------------------------

    float WakePct(ArgelmachFight const& /*fight*/, Golem g, float /*base*/) const override
    {
        return BrdPrototype::WakePct(g);
    }

    void ConfigureDescriptor(ArgelmachFight& /*fight*/, BossMechanics::Descriptor& d) override
    {
        // The kill order: the freshly woken golem (D15's priority 2) before Magmatron, then him.
        d.targets.push_back(BossMechanics::TargetEntry(NPC_BRD_MAGMATRON, 1, BossMechanics::Who::Dps,
            BossMechanics::Condition::LacksAura(BrdArgelmach::SPELL_AR_STATUE)));
    }

    // ---- the pull ---------------------------------------------------------------------------------------------------

    void OnEngage(ArgelmachFight& fight) override
    {
        Creature* boss = fight.Boss();
        _baseHealth = boss->GetMaxHealth();
        DungeonKit::Flex::SetHealth(boss, kBossHealth, true);
        DungeonKit::SetHardModeLoot(boss, true);            // rule 1: at the pull (the instance keeps it too)
        Creature* magmatron = WakeMagmatron(fight);
        uint64 const now = fight.FightMs();
        _incineration.Start(now, kIncinerationFirstMs);
        _flame.Start(now, kFlameFirstMs);
        fight.Log("prototype-engage", Acore::StringFormat("health={} base={} magmatron={} wake={:.0f}/{:.0f}/{:.0f} "
            "players={}", boss->GetMaxHealth(), _baseHealth, magmatron ? magmatron->GetMaxHealth() : 0,
            kWakePct[0], kWakePct[1], kWakePct[2], fight.FightPlayers().size()));
    }

    void OnGolemWoken(ArgelmachFight& fight, Golem g, Creature* golem) override
    {
        if (!golem)
            return;
        DungeonKit::Flex::SetHealth(golem, kGolemHealth, true);
        fight.Log("prototype-golem-health", Acore::StringFormat("golem={} health={}", BrdArgelmach::NameOf(g),
            golem->GetMaxHealth()));
    }

    void OnGolemDied(ArgelmachFight& fight, Golem g, Creature* /*wreck*/) override
    {
        StartCore(fight, WreckOf(g));
    }

    void OnUpdate(ArgelmachFight& fight, uint32 /*diff*/) override
    {
        uint64 const now = fight.FightMs();
        Creature* magmatron = Magmatron(fight);
        if (_magmatron && !_magmatronDead && (!magmatron || !magmatron->IsAlive()))
            MagmatronDied(fight);

        UpdateIncineration(fight, now);
        UpdateFlame(fight, now);

        if (_incineration.Due(now))
            _incineration.Start(now, Incinerate(fight, magmatron, false) ? kIncinerationEveryMs : kRetryMs);
        if (_flame.Due(now))
            _flame.Start(now, Flamethrower(fight, magmatron, nullptr) ? kFlameEveryMs : kRetryMs);

        for (Wreck w : kWrecks)
        {
            CoreState& c = _cores[IndexOf(w)];
            if (!c.running || !c.beat.Due(now))
                continue;
            if (FireCore(fight, w))
                c.beat.Fired(now, CoreEveryMs(w));
            else
                c.beat.Start(now, kRetryMs);
        }
    }

    // ---- the end ----------------------------------------------------------------------------------------------------

    // D15 then cancels the tracked shapes and despawns his summons (Magmatron, the cores, the looks).
    void OnEnd(ArgelmachFight& fight, bool died) override
    {
        Creature* boss = fight.Boss();
        if (_pending)
            for (MechanicHandle const& h : _pending->bursts)
                Mechanic::Cancel(boss, h);
        if (_flameHandle)
            Mechanic::Cancel(boss, _flameHandle);
        if (!died && _baseHealth)
            DungeonKit::Flex::SetHealth(boss, _baseHealth, true);
        uint32 cores = 0;
        for (CoreState const& c : _cores)
            cores += c.running ? 1 : 0;
        fight.Log("prototype-end", Acore::StringFormat("died={} magmatron-killed={} incinerations={} bursts={} "
            "flames={} cores={} core-firings={}", died ? 1 : 0, _magmatronDead ? 1 : 0, _incinerations, _bursts,
            _flames, cores, _coreFirings));
        _pending.reset();
        _flameHandle = {};
    }

    // ---- `.dbtest brd prototype` -----------------------------------------------------------------------------------

    bool TestIncinerate(ArgelmachFight& fight)
    {
        Creature* magmatron = Magmatron(fight);
        if (magmatron && magmatron->IsAlive())
            return Incinerate(fight, magmatron, false);
        CoreState const& c = _cores[IndexOf(Wreck::Magmatron)];
        return c.running && Incinerate(fight, fight.Boss()->GetMap()->GetCreature(c.guid), true);
    }

    bool TestFlame(ArgelmachFight& fight, Player* on)
    {
        return Flamethrower(fight, Magmatron(fight), on);
    }

    bool TestCore(ArgelmachFight& fight, Wreck w)
    {
        if (!_cores[IndexOf(w)].running)
            StartCore(fight, w);
        return FireCore(fight, w);
    }

    std::string TestState(ArgelmachFight& fight)
    {
        Creature* magmatron = Magmatron(fight);
        std::string cores;
        for (Wreck w : kWrecks)
        {
            CoreState const& c = _cores[IndexOf(w)];
            cores += Acore::StringFormat("{}{}={}", cores.empty() ? "" : " ", NameOf(w), c.running
                ? Acore::StringFormat("next {}s", c.beat.DueMs() > fight.FightMs() ? (c.beat.DueMs() -
                    fight.FightMs()) / 1000 : 0) : std::string("off"));
        }
        return Acore::StringFormat("clock={}s health={}/{} magmatron={} incineration={} flame={} pending={} {}",
            fight.FightMs() / 1000, fight.Boss()->GetHealth(), fight.Boss()->GetMaxHealth(),
            magmatron && magmatron->IsAlive() ? Acore::StringFormat("{}/{}", magmatron->GetHealth(),
                magmatron->GetMaxHealth()) : std::string(_magmatronDead ? "dead" : "missing"),
            _incineration.On() ? "on" : "off", _flame.On() ? "on" : "off", _pending ? 1 : 0, cores);
    }

private:
    struct CoreState
    {
        ObjectGuid guid;
        Beat beat;
        bool running = false;
    };

    // An Incineration bar in progress: who casts it, when it lands, the ignited clouds' circles.
    struct PendingIncineration
    {
        ObjectGuid caster;
        uint64 resolveMs = 0;
        bool fromCore = false;
        std::vector<MechanicHandle> bursts;
        std::vector<Position> spots;
    };

    Creature* Magmatron(ArgelmachFight& fight) const
    {
        return _magmatron ? fight.Boss()->GetMap()->GetCreature(_magmatron) : nullptr;
    }

    // Magmatron wakes on P4: the idle statue when it stands there, else a fresh one (his summon).
    Creature* WakeMagmatron(ArgelmachFight& fight)
    {
        Creature* boss = fight.Boss();
        Creature* magmatron = StatueOf(boss);
        IdleOf(boss)->statue.Clear();       // the fight's now (the idle hook puts a new one up after the pull)
        if (IsDormant(magmatron))
            fight.TrackSummon(magmatron);   // the map's summon: D15's cleanup despawns it with his own
        else
        {
            if (magmatron)
                magmatron->DespawnOrUnsummon();
            magmatron = boss->SummonCreature(NPC_BRD_MAGMATRON, OnPedestal(boss, BrdArgelmach::kPedestal4,
                MagmatronFacing()), TEMPSUMMON_MANUAL_DESPAWN);
        }
        if (!magmatron)
        {
            fight.Log("prototype-magmatron", "no Magmatron (summon refused)");
            return nullptr;
        }
        _magmatron = magmatron->GetGUID();
        magmatron->SetReactState(REACT_PASSIVE);
        magmatron->SetCombatMovement(false);
        magmatron->SetControlled(true, UNIT_STATE_ROOT);
        magmatron->RemoveAurasDueToSpell(BrdArgelmach::SPELL_AR_STATUE);
        magmatron->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        magmatron->RemoveUnitFlag(UNIT_FLAG_NON_ATTACKABLE);
        DungeonKit::Flex::SetHealth(magmatron, kMagmatronHealth, true);
        magmatron->CastSpell(magmatron, BrdArgelmach::SPELL_AR_GOLEM_WAKES, true);
        fight.JoinFight(magmatron);
        fight.Log("prototype-magmatron-wakes", Acore::StringFormat("health={}", magmatron->GetMaxHealth()));
        return magmatron;
    }

    // Magmatron is dead: its bars stop (a bar in progress goes out), its core runs.
    void MagmatronDied(ArgelmachFight& fight)
    {
        Creature* boss = fight.Boss();
        _magmatronDead = true;
        _incineration.Stop();
        _flame.Stop();
        if (_flameHandle)
        {
            Mechanic::Cancel(boss, _flameHandle);
            _flameHandle = {};
        }
        fight.Log("prototype-magmatron-killed", Acore::StringFormat("health={:.0f}%", boss->GetHealthPct()));
        StartCore(fight, Wreck::Magmatron);
    }

    // ---- AR11 Incineration ------------------------------------------------------------------------------------------

    // The bar on `caster` (Magmatron, or its wreck's core): the clouds ignite now and burst as it ends. False when the
    // caster cannot start it (busy, gone, a bar already in progress).
    bool Incinerate(ArgelmachFight& fight, Creature* caster, bool fromCore)
    {
        if (!caster || !caster->IsAlive() || _pending || caster->HasUnitState(UNIT_STATE_CASTING))
            return false;
        bool const bar = caster->CastSpell(caster, SPELL_PT_INCINERATION, false) == SPELL_CAST_OK;
        if (!bar && !fromCore)
            return false;
        Creature* boss = fight.Boss();
        if (boss->IsAIEnabled)
            boss->AI()->Talk(BrdArgelmach::EMOTE_AR_INCINERATE);

        PendingIncineration p;
        p.caster = caster->GetGUID();
        p.resolveMs = fight.FightMs() + kIncinerationCastMs;
        p.fromCore = fromCore;
        for (Position const& at : fight.TakeClouds("incineration"))
        {
            MechanicHandle handle;
            {
                MechanicRef ref = Mechanic::Circle(boss, BossMechanics::Anchor(at), kBurstRadiusYd,
                    Ms(kIncinerationCastMs));
                ref.Damage(kBurstPct).TankDamage(kBurstPct)
                    .Spell(SPELL_PT_CLOUD_BURST).Weakened().Within(ChamberBounds())
                    .Tag(kTagIncineration);
                handle = ref.Handle();
            }
            if (!handle)
                continue;
            fight.Track(handle);
            p.bursts.push_back(handle);
            p.spots.push_back(at);
        }
        fight.Log("prototype-incineration", Acore::StringFormat("source={} core={} bar={} clouds={} pct={:.0f} "
            "burst={:.0f}/{:.0f}yd", caster->GetName(), fromCore ? 1 : 0, bar ? 1 : 0, p.spots.size(),
            kIncinerationPct, kBurstPct, kBurstRadiusYd));
        _pending = std::move(p);
        ++_incinerations;
        return true;
    }

    // The bar's end: 15% to everyone (the circles resolve themselves); a dead caster puts the fire out.
    void UpdateIncineration(ArgelmachFight& fight, uint64 now)
    {
        if (!_pending)
            return;
        Creature* boss = fight.Boss();
        Creature* caster = boss->GetMap()->GetCreature(_pending->caster);
        if (!caster || !caster->IsAlive())
        {
            for (MechanicHandle const& h : _pending->bursts)
                Mechanic::Cancel(boss, h);
            fight.Log("prototype-incineration-out", Acore::StringFormat("clouds={}", _pending->spots.size()));
            _pending.reset();
            return;
        }
        if (now < _pending->resolveMs)
            return;
        GuidSet everyone;
        for (Player* player : fight.FightPlayers())
            everyone.insert(player->GetGUID());
        DungeonKit::RegistryHitSpec hit;
        hit.pct = kIncinerationPct;
        hit.school = SPELL_SCHOOL_FIRE;
        hit.spellId = SPELL_PT_INCINERATION_HIT;
        hit.weakened = false;
        hit.tag = kTagIncineration;
        fight.Track(DungeonKit::RegistryHit(boss, everyone, hit));
        caster->CastSpell(caster, SPELL_PT_INCINERATION_LOOK, true);
        if (StalkerExists())
            for (Position const& at : _pending->spots)
                if (TempSummon* look = boss->SummonCreature(NPC_BRD_STALKER, at, TEMPSUMMON_TIMED_DESPAWN,
                    kBurstLookMs))
                    look->CastSpell(look, SPELL_PT_INCINERATION_LOOK, true);
        _bursts += static_cast<uint32>(_pending->spots.size());
        fight.Log("prototype-incineration-lands", Acore::StringFormat("hit={} bursts={} pct={:.0f}", everyone.size(),
            _pending->spots.size(), kIncinerationPct));
        _pending.reset();
    }

    // ---- AR12 Flamethrower ------------------------------------------------------------------------------------------

    // The cone toward a random player (`forced`: that one), fixed now, landing in 2 s. False when Magmatron is busy
    // (the beat tries again); true with nobody to aim at (the beat waits its full turn).
    bool Flamethrower(ArgelmachFight& fight, Creature* magmatron, Player* forced)
    {
        if (!magmatron || !magmatron->IsAlive() || _flameHandle || magmatron->HasUnitState(UNIT_STATE_CASTING))
            return false;
        Creature* boss = fight.Boss();
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // the tank too (ruling 88)
        Player* target = forced ? forced : DungeonKit::PickPlayer(boss, rule);
        if (!target)
        {
            fight.Log("prototype-flamethrower", "no target");
            return true;
        }
        Vec2 const apex = DungeonKit::PlaneOf(magmatron);
        float const bearing = DungeonKit::BearingTo(apex, DungeonKit::PlaneOf(target));
        Position const at(apex.x, apex.y, magmatron->GetPositionZ(), bearing);
        magmatron->SetFacingTo(bearing);
        magmatron->CastSpell(magmatron, SPELL_PT_FLAMETHROWER, false);
        {
            MechanicRef ref = Mechanic::Zone(boss, BossMechanics::Shapes::Cone(BossMechanics::Anchor(at),
                kFlameAngleDeg, kFlameLengthYd), Ms(kFlameWarnMs));
            ref.Damage(kFlamePct).TankDamage(kFlamePct)
                .Spell(SPELL_PT_FLAMETHROWER_HIT).Weakened().Within(ChamberBounds())
                .Tag(kTagFlamethrower).OnHit([](Unit* hit)
                {
                    // It burns Poison Mist's DoT off whoever it hits (S3 "Hard mode").
                    if (hit)
                        hit->RemoveAurasDueToSpell(BrdArgelmach::SPELL_AR_POISON_MIST);
                });
            _flameHandle = ref.Handle();
        }
        if (!_flameHandle)
        {
            fight.Log("prototype-flamethrower", "refused");
            return true;
        }
        fight.Track(_flameHandle);
        _flameResolveMs = fight.FightMs() + kFlameWarnMs;
        ++_flames;
        fight.Log("prototype-flamethrower", Acore::StringFormat("on={} tank={} bearing={:.2f} pct={:.0f} cone={:.0f}/"
            "{:.0f}yd", target->GetName(), boss->GetVictim() == target ? 1 : 0, bearing, kFlamePct, kFlameAngleDeg,
            kFlameLengthYd));
        return true;
    }

    // The breath's look as the cone lands (the registry resolves the hit).
    void UpdateFlame(ArgelmachFight& fight, uint64 now)
    {
        if (!_flameHandle || now < _flameResolveMs)
            return;
        _flameHandle = {};
        if (Creature* magmatron = Magmatron(fight))
            if (magmatron->IsAlive())
                magmatron->CastSpell(magmatron, SPELL_PT_FLAMETHROWER_LOOK, true);
    }

    // ---- AR13 Salvaged Cores ----------------------------------------------------------------------------------------

    // The wreck's core on its pedestal (his summon: D15's cleanup despawns it), in the fight, its look running.
    void StartCore(ArgelmachFight& fight, Wreck w)
    {
        CoreState& c = _cores[IndexOf(w)];
        if (c.running)
            return;
        Creature* boss = fight.Boss();
        Point3 const p = PedestalOf(w);
        TempSummon* core = boss->SummonCreature(NPC_BRD_SALVAGED_CORE, OnPedestal(boss, p, 0.f),
            TEMPSUMMON_MANUAL_DESPAWN);
        if (core)
        {
            core->SetReactState(REACT_PASSIVE);
            core->CastSpell(core, SPELL_PT_SALVAGED_CORE, true);
            fight.JoinFight(core);
            c.guid = core->GetGUID();
        }
        c.running = true;
        c.beat.Start(fight.FightMs(), kCoreFirstMs);
        if (boss->IsAIEnabled)
            boss->AI()->Talk(BrdArgelmach::EMOTE_AR_CORE);
        uint32 running = 0;
        for (CoreState const& s : _cores)
            running += s.running ? 1 : 0;
        fight.Log("prototype-core", Acore::StringFormat("wreck={} core={} every={}s first={}s running={} "
            "health={:.0f}%", NameOf(w), core ? 1 : 0, CoreEveryMs(w) / 1000, kCoreFirstMs / 1000, running,
            boss->GetHealthPct()));
    }

    // The core's signature now (D15's, from the core: no second attack). False when it must wait (Incineration busy).
    bool FireCore(ArgelmachFight& fight, Wreck w)
    {
        Creature* boss = fight.Boss();
        CoreState const& c = _cores[IndexOf(w)];
        Creature* core = c.guid ? boss->GetMap()->GetCreature(c.guid) : nullptr;
        Unit* source = core ? static_cast<Unit*>(core) : static_cast<Unit*>(boss);
        bool fired = true;
        switch (w)
        {
            case Wreck::Toxitron:
                fight.ChemicalBomb(source, kCoreBombMarks, nullptr);
                break;
            case Wreck::Electron:
                fight.LethalAttraction(source, nullptr);
                break;
            case Wreck::Arcanoton:
            {
                Point3 const p = PedestalOf(w);
                fight.PowerGenerator(core ? core->GetPosition() : OnPedestal(boss, p, 0.f));
                break;
            }
            case Wreck::Magmatron:
                fired = Incinerate(fight, core, true);
                break;
        }
        if (!fired)
            return false;
        ++_coreFirings;
        fight.Log("prototype-core-fires", Acore::StringFormat("wreck={}", NameOf(w)));
        return true;
    }

    std::array<CoreState, kWreckCount> _cores{};
    std::optional<PendingIncineration> _pending;
    MechanicHandle _flameHandle;
    Beat _incineration;
    Beat _flame;
    ObjectGuid _magmatron;
    uint64 _flameResolveMs = 0;
    uint32 _baseHealth = 0;
    uint32 _incinerations = 0;
    uint32 _bursts = 0;
    uint32 _flames = 0;
    uint32 _coreFirings = 0;
    bool _magmatronDead = false;
};

// The Activation Console 301284 (a goober by the passage mouth; heroic only by its spawn mask): switching it on before
// the pull arms the Prototype. Not selectable while it cannot be used (he fights, he is dead, already armed); lit (GO
// state active) while armed. After his kill it also clears a dormant statue left on the fourth pedestal.
struct go_brd_activation_console : public GameObjectAI
{
    explicit go_brd_activation_console(GameObject* go) : GameObjectAI(go) { }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kConsolePollMs;
        bool const usable = RefusalAt(me) == ConsoleRefusal::None;
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (usable && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!usable && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);

        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return;
        GOState const want = instance->GetData(DATA_CONSOLE_ARMED) ? GO_STATE_ACTIVE : GO_STATE_READY;
        if (me->GetGoState() != want)
            me->SetGoState(want);
        if (instance->GetBossState(BOSS_ARGELMACH) == DONE)
        {
            std::list<Creature*> statues;
            me->GetCreatureListWithEntryInGrid(statues, NPC_BRD_MAGMATRON, kStatueSearchYd);
            for (Creature* statue : statues)
                if (IsDormant(statue))
                    statue->DespawnOrUnsummon();
        }
    }

    bool GossipHello(Player* player, bool reportUse) override
    {
        if (reportUse || !player)
            return true;
        if (ArmConsole(me, player) == ConsoleRefusal::None)
        {
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
            me->SetGoState(GO_STATE_ACTIVE);
            _pollMs = kConsolePollMs;
        }
        return true;
    }

private:
    uint32 _pollMs = 0;
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest brd prototype`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    // The running pull's hard mode (an error and nullptr when there is none).
    Prototype* FindPrototype(ChatHandler* handler, ArgelmachFight*& fight)
    {
        Creature* boss = BrdTest::FindBoss(handler, NPC_ARGELMACH);
        if (!boss)
            return nullptr;
        fight = boss->IsAIEnabled ? dynamic_cast<ArgelmachFight*>(boss->AI()) : nullptr;
        if (!fight)
        {
            handler->SendErrorMessage("{}", "Golem Lord Argelmach is not running boss_golem_lord_argelmach_rework "
                "(wave 2 binds it).");
            return nullptr;
        }
        auto* prototype = dynamic_cast<Prototype*>(fight->ActiveHardMode());
        if (!prototype)
            handler->SendErrorMessage("{}", "No hard mode pull is running (arm the console on heroic, then pull him).");
        return prototype;
    }

    Player* Gm(ChatHandler* handler)
    {
        return handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrdTest::ShowHardModeInfo(handler, "prototype", DATA_CONSOLE_ARMED, BOSS_PROTOTYPE);
    }

    // `.dbtest brd prototype arm`: the console as a player uses it (the same refusals), from where the GM stands.
    bool HandleArm(ChatHandler* handler)
    {
        if (!BrdTest::RequireBlackrockDepths(handler))
            return false;
        Player* gm = Gm(handler);
        ConsoleRefusal const r = ArmConsole(gm, gm);
        if (r != ConsoleRefusal::None)
        {
            handler->SendErrorMessage("{}", ConsoleRefusalText(r));
            return false;
        }
        handler->PSendSysMessage("{}", "The console hums: the next pull is the Prototype.");
        return true;
    }

    // `.dbtest brd prototype clear`: the flag off (refused by the instance only when it is already off).
    bool HandleClear(ChatHandler* handler)
    {
        InstanceScript* instance = BrdTest::GmInstance(handler);
        if (!instance)
            return false;
        instance->SetData(DATA_CONSOLE_ARMED, 0);
        handler->PSendSysMessage("prototype: console {}", instance->GetData(DATA_CONSOLE_ARMED));
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        ArgelmachFight* fight = nullptr;
        Prototype* prototype = FindPrototype(handler, fight);
        if (!prototype)
            return false;
        handler->PSendSysMessage("prototype: {}", prototype->TestState(*fight));
        return true;
    }

    // `.dbtest brd prototype incinerate`: AR11 now (Magmatron, or its core once it is dead).
    bool HandleIncinerate(ChatHandler* handler)
    {
        ArgelmachFight* fight = nullptr;
        Prototype* prototype = FindPrototype(handler, fight);
        if (!prototype)
            return false;
        bool const ok = prototype->TestIncinerate(*fight);
        handler->PSendSysMessage("prototype: Incineration {}.", ok ? "starts (3 s)" : "refused (busy, or no caster)");
        return ok;
    }

    // `.dbtest brd prototype flame`: AR12 now, aimed at the GM.
    bool HandleFlame(ChatHandler* handler)
    {
        ArgelmachFight* fight = nullptr;
        Prototype* prototype = FindPrototype(handler, fight);
        if (!prototype)
            return false;
        bool const ok = prototype->TestFlame(*fight, Gm(handler));
        handler->PSendSysMessage("prototype: Flamethrower {}.", ok ? "at you (2 s)"
            : "refused (Magmatron busy or dead)");
        return ok;
    }

    // `.dbtest brd prototype core <1-4>`: that wreck's core now (1 Toxitron, 2 Electron, 3 Arcanoton, 4 Magmatron);
    // started first when it is not running (its golem alive: a test only).
    bool HandleCore(ChatHandler* handler, uint32 which)
    {
        if (which < 1 || which > kWreckCount)
        {
            handler->SendErrorMessage("{}", "Core 1 (Toxitron), 2 (Electron), 3 (Arcanoton) or 4 (Magmatron).");
            return false;
        }
        ArgelmachFight* fight = nullptr;
        Prototype* prototype = FindPrototype(handler, fight);
        if (!prototype)
            return false;
        Wreck const w = kWrecks[which - 1];
        bool const ok = prototype->TestCore(*fight, w);
        handler->PSendSysMessage("prototype: the {} core {}.", NameOf(w), ok ? "fires" : "is busy (Incineration)");
        return ok;
    }

    ChatCommandTable const& PrototypeTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "arm",        HandleArm,        SEC_GAMEMASTER, Console::No },
            { "clear",      HandleClear,      SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "incinerate", HandleIncinerate, SEC_GAMEMASTER, Console::No },
            { "flame",      HandleFlame,      SEC_GAMEMASTER, Console::No },
            { "core",       HandleCore,       SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_brd_argelmach_hard_mode()
{
    // D15 asks for a Prototype only on a heroic pull with the console armed (and only once wave 2 binds him); the
    // console's script is named by its own row (rev_argelmach_hard_mode_blackrock_depths.sql), so it registers now.
    BrdArgelmach::RegisterArgelmachHardMode([](Creature*) { return std::make_unique<Prototype>(); });
    BrdArgelmach::RegisterArgelmachIdleHook([](Creature* boss, uint32 diff) { StatueIdle(boss, diff); });
    RegisterDungeonReworkGameObjectAI(go_brd_activation_console, BlackrockDepthsRework::kInstanceScriptName);
    BrdTest::RegisterBoss("prototype", PrototypeTestCommands());
}
