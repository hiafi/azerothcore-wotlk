/*
 * mod-dungeon-bosses, Scarlet Monastery D1: Interrogator Vishas (3983), "an interrogation you are losing". Build spec:
 * docs/dungeons/scarlet-monastery-1-graveyard.md "Interrogator Vishas" (VI1-VI4), handoff section 3.5 row D1, 3.6,
 * 3.8 (his H-shaped hall), 3.10 (VR). Replaces SmartAI 3983 (rows 0-5, dropped by WP-S0's rev; the template is bound
 * by apps/dbc-tools source/npcs/scarlet_monastery/vishas.py); Shadow Word: Pain 2767 is retired as his cast (a live
 * player override: his Pain is a copy, rule 15). Pure rules: VishasLogic.h.
 *
 *   Phases          1 The Question to 70%, 2 Hot Irons to 30% (yell line 1, emote line 5, he takes his stock Hot
 *                   Iron Poker 5532 into the main hand: he starts unarmed), 3 Rip the Secrets (yell line 2: shorter
 *                   Interrogation and Branding Iron cadences; heroic: two Interrogations at once)
 *   VI1 Interrogation at 6 s, then every 18 s (phase 3: 14 s): a 1.5 s bar, then emote line 4 and a 6 s debuff on a
 *                   random non-tank (the tank is the carried-spread exemption), 4% a second; a registry RunOut (8 yd)
 *                   from the bar's start: every 2 s anyone within 8 yd of the carrier is an accomplice and takes 12%
 *                   (heroic 20%), three pulses, no Weakened (L7). Heroic phase 3: two carriers, 8 yd from each other
 *                   too
 *   VI2 Branding Iron from 70%: 3 s after the yell, then every 12 s (phase 3: 10 s): a 2 s bar; he turns to a random
 *                   player (the tank included) and a 90 degree, 15 yd cone is fixed toward that player's spot at the
 *                   bar's start: 35% (heroic 45%) and Weakened
 *   VI3 Pain        at 3-7 s, then every 10-14 s on a random player (the tank included): 2% (heroic 4%) a 3 s tick for
 *                   18 s; Magic, a dispel is the reward (the bots' dispel list)
 *   VI4 Torment     heroic, at 10 s then every 25 s: emote line 6 and a channeled beam to a random player (the tank
 *                   included, an Interrogation carrier only when nobody else is left), not interruptible; a
 *                   registry line Soak (SM-BM F2: the targeted tank backs off 10 yd, the tank soaks in the first 4 yd);
 *                   1.5 s on, then each second 20% of the non-tank row split evenly
 *                   among every player on the line, the target included (alone the target dies: hub ruling 12). He
 *                   stands still and does not melee while he channels; his other tools wait
 *
 * Kill line 3 (5 s lockout); his death makes Vorrel Sengutz 3981 say his stock line 0 (SmartAI 3983 row 5). Boss data:
 * no kill order, no interrupt (nothing of his makes sense to stop), Pain on the dispel list. Every timer runs on the
 * AI's own clock. Every firing logs one INFO line "sm vishas <mechanic> ..." (module.dungeonbosses);
 * `.dbtest sm vishas ...` fires one mechanic on demand.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "ThreatManager.h"
#include "VishasLogic.h"
#include <algorithm>
#include <functional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmVishas;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "vishas";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The bots' hard bounds: the two chambers of his hall (VishasLogic.h kFloor).
    BossMechanics::SpotBounds FloorBounds()
    {
        BossMechanics::SpotBounds bounds;
        for (FloorRect const& r : kFloor)
            bounds.Polygon({ Position(r.minX, r.minY, 0.f), Position(r.maxX, r.minY, 0.f),
                Position(r.maxX, r.maxY, 0.f), Position(r.minX, r.maxY, 0.f) }, kFloorZMin, kFloorZMax);
        return bounds;
    }
}

// Interrogator Vishas 3983
struct boss_interrogator_vishas_rework : public BossAI
{
    explicit boss_interrogator_vishas_rework(Creature* creature)
        : BossAI(creature, BOSS_VISHAS), _arena(VishasArena(), LeashOptions(kBossLogName)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
        Unarm();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();      // a `.dbtest` mechanic out of combat may have left something behind
        Unarm();
        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_VISHAS;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(SAY_PULL);

        _phase = 1;
        _interrogationClock.Start(_clockMs, kInterrogationBeat.firstMs);
        _painClock.Start(_clockMs, urand(kPainFirstMinMs, kPainFirstMaxMs));
        if (_heroic)
            _tormentClock.Start(_clockMs, kTormentBeat.firstMs);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f})", _heroic ? 1 : 0, me->GetPositionX(),
                me->GetPositionY(), me->GetPositionZ()));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Cleanup();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death",
            Acore::StringFormat("phase={} interrogations={} accomplices={} brands={} pains={} torments={} killer={}",
                _phase, _interrogations, _accomplices, _brands, _pains, _torments,
                killer ? killer->GetName() : "none"));
        Cleanup();
        // Stock (SmartAI 3983 row 5, dropped by S0's rev): Vorrel says his line 0 when Vishas dies.
        if (Creature* vorrel = me->FindNearestCreature(NPC_VORREL, kVorrelRange))
            if (vorrel->IsAIEnabled && vorrel->AI())
                vorrel->AI()->Talk(SAY_VORREL_DEATH);
    }

    // Stock (SmartAI 3983 row 1): "Purged by pain!" on a kill, at most every 5 s.
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

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading

        UpdatePhase();
        UpdateInterrogation();
        UpdateTorment();
        UpdateBeats();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Phases (exactly at 70% and 30%, one step at a time)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdatePhase()
    {
        for (uint32 next = NextPhase(_phase, me->GetHealthPct()); next != _phase;
            next = NextPhase(_phase, me->GetHealthPct()))
            EnterPhase(next);
    }

    void EnterPhase(uint32 phase)
    {
        _phase = phase;
        Mechanic::SetPhase(me, phase);
        if (phase == 2)
        {
            // Hot Irons: the yell, the emote and the iron in his hand; Branding Iron joins 3 s after the yell.
            Talk(SAY_HOT_IRONS);
            Talk(EMOTE_IRONS);
            me->SetVirtualItem(0, kItemHotIronPoker);
            _brandClock.Start(_clockMs, kBrandBeat.firstMs);
        }
        else if (phase == 3)
        {
            // Rip the Secrets: both tools on their shorter cadences from now on.
            Talk(SAY_RIP_SECRETS);
            _interrogationClock.Shorten(_clockMs, Cadence(kInterrogationBeat, phase));
            _brandClock.Shorten(_clockMs, Cadence(kBrandBeat, phase));
        }
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "phase",
            Acore::StringFormat("phase={} health={:.1f}", phase, me->GetHealthPct()));
    }

    // He starts unarmed (VR): the stock equipment (the poker in both hands) is cleared on every reset.
    void Unarm()
    {
        me->SetVirtualItem(0, 0);
        me->SetVirtualItem(1, 0);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The beats
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateBeats()
    {
        // His other tools wait while he channels Torment (GY VI4).
        if (TormentActive())
            return;
        // Pain is triggered: it never waits for a cast bar and never breaks one.
        if (_painClock.Due(_clockMs))
        {
            _painClock.Fired(_clockMs, urand(kPainEveryMinMs, kPainEveryMaxMs));
            CastPain(nullptr);
        }
        // One cast bar at a time; a due beat stays due.
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_heroic && _tormentClock.Due(_clockMs))
        {
            if (StartTorment(nullptr))
                _tormentClock.Fired(_clockMs, Cadence(kTormentBeat, _phase));
            else
                _tormentClock.Start(_clockMs, kRetryMs);
            return;
        }
        if (_phase >= 2 && _brandClock.Due(_clockMs))
        {
            if (StartBrand(nullptr))
                _brandClock.Fired(_clockMs, Cadence(kBrandBeat, _phase));
            else
                _brandClock.Start(_clockMs, kRetryMs);
            return;
        }
        if (_interrogationClock.Due(_clockMs))
        {
            if (StartInterrogation(nullptr))
                _interrogationClock.Fired(_clockMs, Cadence(kInterrogationBeat, _phase));
            else
                _interrogationClock.Start(_clockMs, kRetryMs);
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VI1 Interrogation
    // ----------------------------------------------------------------------------------------------------------------

    // `forced`: the `.dbtest` target (else random non-tanks; two in heroic phase 3). The RunOut is registered with the
    // bar so the carriers (and the bots) have the bar and 2 s to walk out before the first pulse.
    bool StartInterrogation(Player* forced)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = true;        // the tank is never interrogated (carried-spread exemption)
            rule.tankIfAlone = false;
            targets = DungeonKit::PickPlayers(me, rule, InterrogationCount(_heroic, _phase));
        }
        if (targets.empty())
            return false;

        DungeonKit::CastBar(me, SPELL_VI_INTERROGATION_CAST);
        GuidSet carriers;
        std::string names;
        for (Player* player : targets)
        {
            carriers.insert(player->GetGUID());
            names += " " + player->GetName();
        }
        float const pct = kAccomplicePct(_heroic);
        MechanicRef ref = Mechanic::RunOut(me, targets.front(), kAccompliceRadius, Ms(AccompliceWarnMs()));
        ref.Targets(carriers).Damage(pct).TankDamage(pct).Spell(SPELL_VI_ACCOMPLICE)
            .Persistent(Ms(AccomplicePersistMs()), Ms(kAccomplicePulseMs)).Within(FloorBounds()).Tag(VI1);
        ref.OnResolve(OnVishas([](boss_interrogator_vishas_rework& ai, BossMechanics::ResolveResult const& result)
        {
            ai.AccomplicePass(result);
        }));
        Track(ref.Handle());

        _interrogation = InterrogationState();
        _interrogation.pending = true;
        _interrogation.carriers = carriers;
        _interrogation.applyAtMs = _clockMs + kInterrogationCastMs;
        ++_interrogations;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "interrogation",
            Acore::StringFormat("count={} phase={} pct={:.0f} targets:{}", targets.size(), _phase, pct, names));
        return true;
    }

    // The bar has ended: the emote and the debuff on every carrier still standing.
    void UpdateInterrogation()
    {
        if (!_interrogation.pending || _clockMs < _interrogation.applyAtMs)
            return;
        _interrogation.pending = false;
        for (ObjectGuid const& guid : _interrogation.carriers)
        {
            Player* player = ObjectAccessor::GetPlayer(*me, guid);
            if (!CountsAsPlayer(player))
                continue;
            me->CastSpell(player, SPELL_VI_INTERROGATION, true);
            Talk(EMOTE_CONFESSION, player);
        }
    }

    // A pulse: anyone within 8 yd of a carrier took it (the registry dealt it); the log names them.
    void AccomplicePass(BossMechanics::ResolveResult const& result)
    {
        if (result.hits.empty())
            return;
        std::string names;
        for (ObjectGuid const& guid : result.hits)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                names += " " + player->GetName();
        _accomplices += static_cast<uint32>(result.hits.size());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "accomplice",
            Acore::StringFormat("pass={} hits={}:{}", result.pass, result.hits.size(), names));
    }

    bool Interrogated(ObjectGuid guid) const
    {
        if (_interrogation.pending && _interrogation.carriers.count(guid))
            return true;
        Player* player = ObjectAccessor::GetPlayer(*me, guid);
        return player && player->HasAura(SPELL_VI_INTERROGATION, me->GetGUID());
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VI2 Branding Iron
    // ----------------------------------------------------------------------------------------------------------------

    bool StartBrand(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;       // the tank included
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return false;
        float const facing = BrandFacing(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(target), me->GetOrientation());
        me->StopMoving();
        me->SetFacingTo(facing);
        DungeonKit::CastBar(me, SPELL_VI_BRANDING_IRON_CAST);
        // The cone is fixed at the bar's start: a point anchor with the facing toward the player's spot then.
        Position const apex(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
        float const pct = kBrandPct(_heroic);
        MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(BossMechanics::Anchor(apex), kBrandAngleDeg,
            kBrandLength), Ms(kBrandCastMs));
        ref.Damage(pct).TankDamage(pct).Spell(SPELL_VI_BRANDING_IRON).Weakened().Within(FloorBounds()).Tag(VI2);
        Track(ref.Handle());
        ++_brands;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "brand",
            Acore::StringFormat("target={} tank={} facing={:.2f} pct={:.0f} phase={}", target->GetName(),
                target == me->GetVictim() ? 1 : 0, facing, pct, _phase));
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VI3 Pain
    // ----------------------------------------------------------------------------------------------------------------

    void CastPain(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;       // the tank included
            target = DungeonKit::PickPlayer(me, rule);
        }
        if (!target)
            return;
        me->CastSpell(target, SPELL_VI_PAIN, true);
        ++_pains;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "pain",
            Acore::StringFormat("target={} tank={}", target->GetName(), target == me->GetVictim() ? 1 : 0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VI4 Torment (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    bool TormentActive() const
    {
        return _torment.active;
    }

    // Everyone of the fight but the target and the interrogated (a carrier keeps its 8 yd before it soaks: the bots
    // leave them out; a human carrier on the line still takes a share).
    GuidSet AvailableBut(Player const* target) const
    {
        GuidSet out;
        for (Player* player : FightPlayers())
            if (player != target && !Interrogated(player->GetGUID()))
                out.insert(player->GetGUID());
        if (out.empty() && target)
            out.insert(target->GetGUID());     // nobody else: a non-empty set (empty would mean everyone)
        return out;
    }

    bool StartTorment(Player* forced)
    {
        Player* target = forced;
        if (!target)
        {
            // Not an Interrogation carrier while anyone else qualifies (MN-4).
            std::vector<uint64> carriers;
            for (Player* player : FightPlayers())
                if (Interrogated(player->GetGUID()))
                    carriers.push_back(player->GetGUID().GetRawValue());
            target = DungeonKit::PickPlayer(me, TormentRule(carriers));
            if (!target && !carriers.empty())
                target = DungeonKit::PickPlayer(me, TormentRule({}));
        }
        if (!target)
            return false;
        // He stands still for the beam (the channel's flags hold nothing, so nothing of his own breaks it).
        me->StopMoving();
        SpellCastResult const result = me->CastSpell(target, SPELL_VI_TORMENT, false);
        if (result != SPELL_CAST_OK)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torment-failed",
                Acore::StringFormat("target={} result={}", target->GetName(), static_cast<uint32>(result)));
            return false;
        }
        Talk(EMOTE_TORMENT, target);

        // SM-BM's F2 registration (G1's `torment` drill row mirrors it): everyone available but the target soaks;
        // the targeted tank backs off along the line, the tank soaks at his end.
        BossMechanics::Eligibility soakers;
        soakers.carriers = AvailableBut(target);
        _torment = TormentState();
        _torment.active = true;
        _torment.target = target->GetGUID();
        _torment.endMs = _clockMs + TormentChannelMs();
        _torment.handle = Mechanic::Soak(me, BossMechanics::Shapes::Line(BossMechanics::Anchor(me),
            BossMechanics::Anchor(target), kTormentWidth), uint8(soakers.carriers.size()), Ms(kTormentWarnMs))
            .Eligible(soakers).Persistent(Ms(kTormentMs), Ms(kTormentTickMs)).EndBacksOff(kTormentBackOffYd)
            .TankNearSource(kTormentTankNearYd).MissedSoak(BossMechanics::MissedSoakMode::Never).Tag(VI4)
            .OnResolve(OnVishas([](boss_interrogator_vishas_rework& ai, BossMechanics::ResolveResult const& result)
            {
                ai.TormentPass(result);
            }));
        ++_torments;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torment",
            Acore::StringFormat("target={} tank={} soakers={} phase={}", target->GetName(),
                target == me->GetVictim() ? 1 : 0, soakers.carriers.size(), _phase));
        return true;
    }

    // A second of the beam: 20% of the non-tank row split evenly among the target and every player on the line (the
    // registry's hitbox, eligible or not).
    void TormentPass(BossMechanics::ResolveResult const& result)
    {
        if (!_torment.active || result.mechanicId != _torment.handle.id)
            return;
        Player* target = ObjectAccessor::GetPlayer(*me, _torment.target);
        std::vector<Unit*> takers;
        if (CountsAsPlayer(target))
            takers.push_back(target);
        for (Player* player : FightPlayers())
            if (player != target && Mechanic::Contains(me, _torment.handle, player))
                takers.push_back(player);
        float const pct = kTormentTickPct(_heroic);
        for (auto const& [guid, share] : DungeonKit::SplitShares(me, takers, pct))
            if (share)
                if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                    me->CastCustomSpell(SPELL_VI_TORMENT_SHARE, SPELLVALUE_BASE_POINT0, static_cast<int32>(share),
                        player, TRIGGERED_FULL_MASK);
        uint32 const onLine = static_cast<uint32>(takers.size());
        ++_torment.ticks;
        _torment.onLineSum += onLine;
        _torment.onLineMin = _torment.ticks == 1 ? onLine : std::min(_torment.onLineMin, onLine);
    }

    // The beam ends: its 8 ticks are done, or its target is gone (dead, released, out of the map).
    void UpdateTorment()
    {
        if (!_torment.active)
            return;
        if (_clockMs >= _torment.endMs)
        {
            EndTorment("done");
            return;
        }
        Player* target = ObjectAccessor::GetPlayer(*me, _torment.target);
        if (!CountsAsPlayer(target) || !target->IsInMap(me))
            EndTorment("target-gone");
    }

    void EndTorment(char const* how)
    {
        if (!_torment.active)
            return;
        TormentState const torment = _torment;
        _torment = TormentState();
        if (torment.handle)
            Mechanic::Cancel(me, torment.handle);
        if (me->FindCurrentSpellBySpellId(SPELL_VI_TORMENT))
            me->InterruptSpell(CURRENT_CHANNELED_SPELL);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "torment-end",
            Acore::StringFormat("how={} ticks={} on-line-min={} on-line-avg={:.1f}", how, torment.ticks,
                torment.onLineMin, torment.ticks ? float(torment.onLineSum) / float(torment.ticks) : 0.f));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data (GY "Bots"): no kill order; interrupt list none; Pain on the dispel list (a reward)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.dispels.push_back(BossMechanics::DispelEntry(SPELL_VI_PAIN, 1));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm vishas` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Interrogation,
        Brand,
        Pain,
        Torment,
        Phase,
    };

    // An empty string when fired; otherwise why not. `who` is the GM's selected player (or the GM), `n` a count.
    std::string TestFire(TestMechanic mechanic, Player* who, uint32 n)
    {
        if (!me->IsEngaged())
            return "Vishas must be in combat (the picks read his threat list, the mechanics his encounter).";
        Player* forced = CountsAsPlayer(who) ? who : nullptr;
        switch (mechanic)
        {
            case TestMechanic::Interrogation:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting already.";
                if (forced && forced == me->GetVictim())
                    forced = nullptr;   // never the tank: a random non-tank instead
                if (!StartInterrogation(forced))
                    return "Nobody to interrogate (a non-tank on his threat list).";
                break;
            case TestMechanic::Brand:
                if (me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting already.";
                if (!StartBrand(forced))
                    return "Nobody to brand.";
                break;
            case TestMechanic::Pain:
                CastPain(forced);
                break;
            case TestMechanic::Torment:
                if (TormentActive() || me->HasUnitState(UNIT_STATE_CASTING))
                    return "He is casting or channeling already.";
                if (!StartTorment(forced))
                    return "Torment did not start (see the log).";
                break;
            case TestMechanic::Phase:
                if (n < 2 || n > 3)
                    return "Phase 2 or 3.";
                while (_phase < n)
                    EnterPhase(_phase + 1);
                break;
        }
        return {};
    }

    bool HeroicMap() const { return IsHeroicMap(me); }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} phase={} health={:.1f} interrogations={} accomplices={} "
            "brands={} pains={} torments={} torment={} live={}", _clockMs / 1000, _heroic ? 1 : 0, _phase,
            me->GetHealthPct(), _interrogations, _accomplices, _brands, _pains, _torments, _torment.active ? 1 : 0,
            _live.size());
    }

private:
    static constexpr uint32 kRetryMs = 1000;

    struct InterrogationState
    {
        bool pending = false;       // the bar runs: the debuff lands at applyAtMs
        GuidSet carriers;
        uint64 applyAtMs = 0;
    };

    struct TormentState
    {
        bool active = false;
        ObjectGuid target;
        uint64 endMs = 0;
        MechanicHandle handle;
        uint32 ticks = 0;
        uint32 onLineSum = 0;
        uint32 onLineMin = 0;
    };

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
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

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnVishas(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (boss_interrogator_vishas_rework* ai = From(map, guid))
                fn(*ai, result);
        };
    }

    static boss_interrogator_vishas_rework* From(Map* map, ObjectGuid guid)
    {
        if (!map)
            return nullptr;
        Creature* boss = map->GetCreature(guid);
        if (!boss || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_interrogator_vishas_rework*>(boss->AI());
    }

    // A mechanic of the fight (an Interrogation's RunOut, a Branding Iron cone): kept to cancel it on a reset.
    void Track(MechanicHandle handle)
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 64)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 32);
    }

    // The pull's state: nothing registered, no aura of his on anyone, no beam, clocks stopped (reset, evade, death, a
    // new pull). The Torment state goes first, so the engine's interrupt of the channel never runs EndTorment twice.
    void Cleanup()
    {
        if (_torment.handle)
            Mechanic::Cancel(me, _torment.handle);
        _torment = TormentState();
        if (me->FindCurrentSpellBySpellId(SPELL_VI_TORMENT))
            me->InterruptSpell(CURRENT_CHANNELED_SPELL);
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _interrogation = InterrogationState();
        _clockMs = 0;
        _phase = 1;
        _interrogationClock.Stop();
        _brandClock.Stop();
        _painClock.Stop();
        _tormentClock.Stop();
        _interrogations = 0;
        _accomplices = 0;
        _brands = 0;
        _pains = 0;
        _torments = 0;
        _yelledKill = false;
        _lastKillYellMs = 0;
        _arena.Reset();
        if (instance)
            for (uint32 const spell : { uint32(SPELL_VI_INTERROGATION), uint32(SPELL_VI_PAIN),
                uint32(SPELL_VI_TORMENT) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
    }

    DungeonKit::ArenaGuard _arena;
    BeatClock _interrogationClock;
    BeatClock _brandClock;
    BeatClock _painClock;
    BeatClock _tormentClock;
    InterrogationState _interrogation;
    TormentState _torment;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint64 _lastKillYellMs = 0;
    uint32 _phase = 1;
    uint32 _interrogations = 0;
    uint32 _accomplices = 0;
    uint32 _brands = 0;
    uint32 _pains = 0;
    uint32 _torments = 0;
    bool _yelledKill = false;
    bool _heroic = false;
};

namespace
{
    boss_interrogator_vishas_rework* FindVishasAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_VISHAS);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_interrogator_vishas_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Vishas is not running boss_interrogator_vishas_rework (check the "
                "ScriptName).");
        return ai;
    }

    bool Fire(ChatHandler* handler, boss_interrogator_vishas_rework::TestMechanic mechanic, char const* what,
        uint32 n = 0)
    {
        boss_interrogator_vishas_rework* ai = FindVishasAI(handler);
        if (!ai)
            return false;
        Player* who = handler->GetSession() ? handler->getSelectedPlayerOrSelf() : nullptr;
        std::string const error = ai->TestFire(mechanic, who, n);
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Vishas: {} fired ({}).", what, ai->HeroicMap() ? "heroic numbers" : "normal numbers");
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_VISHAS, BOSS_VISHAS);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_interrogator_vishas_rework* ai = FindVishasAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Vishas: {}", ai->TestState());
        return true;
    }

    bool HandleInterrogation(ChatHandler* handler)
    {
        return Fire(handler, boss_interrogator_vishas_rework::TestMechanic::Interrogation,
            "Interrogation (VI1: the selected non-tank, else random; 8 yd, three pulses)");
    }

    bool HandleBrand(ChatHandler* handler)
    {
        return Fire(handler, boss_interrogator_vishas_rework::TestMechanic::Brand,
            "Branding Iron (VI2: a 90 degree, 15 yd cone toward the selected player, else random)");
    }

    bool HandlePain(ChatHandler* handler)
    {
        return Fire(handler, boss_interrogator_vishas_rework::TestMechanic::Pain,
            "Pain (VI3: the selected player, else random; Magic)");
    }

    bool HandleTorment(ChatHandler* handler)
    {
        return Fire(handler, boss_interrogator_vishas_rework::TestMechanic::Torment,
            "Torment (VI4: a beam to the selected player, else random; any difficulty)");
    }

    bool HandlePhase(ChatHandler* handler, uint32 phase)
    {
        return Fire(handler, boss_interrogator_vishas_rework::TestMechanic::Phase,
            "the phase change (his health is unchanged)", phase);
    }

    // `.dbtest sm vishas <sub>`: the numbers are the map's difficulty.
    ChatCommandTable const& BossInterrogatorVishasTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",          HandleInfo,          SEC_GAMEMASTER, Console::No },
            { "state",         HandleState,         SEC_GAMEMASTER, Console::No },
            { "interrogation", HandleInterrogation, SEC_GAMEMASTER, Console::No },
            { "brand",         HandleBrand,         SEC_GAMEMASTER, Console::No },
            { "pain",          HandlePain,          SEC_GAMEMASTER, Console::No },
            { "torment",       HandleTorment,       SEC_GAMEMASTER, Console::No },
            { "phase",         HandlePhase,         SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_interrogator_vishas_rework()
{
    RegisterDungeonReworkCreatureAI(boss_interrogator_vishas_rework, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("vishas", BossInterrogatorVishasTestCommands());
}
