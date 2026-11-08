/*
 * mod-dungeon-bosses, Shadowfang Keep: Deathsworn Captain (WP-S6). Build spec: SK 1044-1083 (build spec), SK 956-1043
 * (design), DC1-DC5; handoff shadowfang-keep-build.HANDOFF.md section 3.5 rows DC, section 3.6 row S6, section 7 #14
 * (boss tier on heroic) and #25 (his arena). The pure part is DeathswornCaptainLogic.h.
 *
 * The optional rare (15%): the instance rolls him once per instance and despawns him on Absent
 * (instance_shadowfang_keep_rework.cpp, DATA_CAPTAIN_ROLL); this AI replaces his stock SmartAI (Battle Stance, Cleave,
 * Hamstring are gone; WP-S6's SQL rev drops the rows). His patrol (path 1345170, 164 yd out and back over the north
 * hall and his walkway, turning in Odo's doorway) is the creature's own waypoint movement, untouched.
 *
 *   DC1  Deathsworn Charge  2 s cast bar + emote 0 ($n = the target); a 3 yd line to a random non-tank at least 8 yd
 *                           away, 5 yd past them, the first 4 yd excluded, 35% + Weakened; he charges along it on the
 *                           resolve. First 8 s, every 15 s.
 *   DC2  Chain Charge (H)   from DC1's landing spot to another non-tank, the same line on a 1.5 s marker
 *   DC3  Sweeping Cleave    2 s cast bar + emote 1; a 90 degree, 10 yd cone in front of him, tank exempt (a Frontal for
 *                           the bots): non-tanks 40% + Weakened, the tank (in the arc) takes two swings (206015). First
 *                           5 s, every 12 s; never while a charge runs nor within 4 s after the last landing.
 *   DC4  Last Stand (H)     below 30% health, +30% attack speed for the rest of the fight (206016)
 *   DC5  Melee              stock (DamageModifier 1.7, 2.0 s); heroic from the heroic template (boss tier)
 *
 * The arena (section 7 #25, ShadowfangKeepRework.h DeathswornCaptainArena()): the north hall plus the walkway. A
 * charge that starts on the walkway runs only along it, and every line stops short of the arena's edge (never over the
 * 16-20 yd drop into the inner yard). DungeonKit::ArenaGuard grips back anyone off it for 1.5 s (a fall into the yard,
 * a step into Odo's room) onto the nearest point of his patrol line, holds his chase of a victim who is off it, and
 * evades him if he leaves it. Nothing links him to Odo (the stock Call for Help is gone with the SmartAI); while Odo
 * fights, an unpulled Captain holds his patrol short of Odo's doorway, passive and immune to players (R2 S-2,
 * UpdateOdoHold), and neither guard grips a unit in combat with the other boss (IsSfkBossEntry).
 *
 * Pilot lessons: custom damage spells carry SPELL_ATTR3_IGNORE_CASTER_MODIFIERS and the tank's hit is set in
 * OnEffectLaunchTarget; the charge chain rides the registry's resolves and the fight clock rides UpdateAI, never a
 * scheduler the cast bar pauses; mechanic emotes are type 41; every hit has an impact visual (the resolve copies and
 * the tank hit carry Cleave's SpellVisual 219). Every firing logs one INFO line "sfk captain <mechanic> ..."
 * (DungeonKit::LogMechanic, module.dungeonbosses).
 */

#include "ArenaGuard.h"
#include "Chat.h"
#include "Creature.h"
#include "DeathswornCaptainLogic.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;
using namespace DeathswornCaptain;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "captain";

    std::size_t RandomIndex(std::size_t n)
    {
        return n ? static_cast<std::size_t>(urand(0, static_cast<uint32>(n - 1))) : 0;
    }

    Vec2 ToVec(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    DungeonKit::ArenaGuardOptions CaptainGuardOptions()
    {
        DungeonKit::ArenaGuardOptions o;
        // A unit in combat with another live boss is left to that boss: no two guards grip it to and fro (R2 S-2).
        o.skipGrip = DungeonKit::SkipEngagedWithOtherBoss(ShadowfangKeepRework::IsSfkBossEntry);
        o.jumpSpeedXY = kGripJumpSpeedXY;
        o.minJumpSpeedZ = kGripMinSpeedZ;
        // The nearest point of his patrol line: the floor he walks, never over the drop (DeathswornCaptainLogic.h).
        o.landing = [](Creature const* /*boss*/, Unit const* unit)
        {
            Point3 const p = PatrolLanding({ unit->GetPositionX(), unit->GetPositionY() });
            return Position(p.x, p.y, p.z);
        };
        o.landingKeepsZ = true;
        o.logPrefix = "sfk captain arena";
        return o;
    }
}

// Deathsworn Captain 3872
struct boss_deathsworn_captain_rework : public BossAI
{
    enum CaptainEvents : uint32
    {
        EVENT_CAPTAIN_CHARGE = 1,
        EVENT_CAPTAIN_CLEAVE,
        EVENT_CAPTAIN_CHECK_HEALTH,
        EVENT_CAPTAIN_END_CHARGE,       // the charge is over (or stuck): back to the tank
    };

    explicit boss_deathsworn_captain_rework(Creature* creature)
        : BossAI(creature, BOSS_DEATHSWORN_CAPTAIN), _shape(DeathswornCaptainArena()),
        _arena(DeathswornCaptainArena(), CaptainGuardOptions()) { }

    void Reset() override
    {
        _Reset();
        ResetFight();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_DEATHSWORN_CAPTAIN;
        Mechanic::BeginEncounter(me, options);

        // Boss data (build spec): no kill order, no interrupts, no dispels.
        BossMechanics::Descriptor descriptor;
        descriptor.targets.emplace_back(NPC_DEATHSWORN_CAPTAIN, 0);
        Mechanic::Describe(me, std::move(descriptor));

        ResetFight();
        _arena.Engage(me);
        bool const heroic = IsHeroicMap(me);
        events.ScheduleEvent(EVENT_CAPTAIN_CLEAVE, Milliseconds(kCleaveFirstMs));
        events.ScheduleEvent(EVENT_CAPTAIN_CHARGE, Milliseconds(kChargeFirstMs));
        if (kLastStand(heroic))
            events.ScheduleEvent(EVENT_CAPTAIN_CHECK_HEALTH, Milliseconds(kHealthCheckMs));
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "engage",
            Acore::StringFormat("heroic={} at=({:.1f}, {:.1f}, {:.1f}) walkway={}", heroic ? 1 : 0,
                me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(),
                OnWalkway(_shape, ToVec(me->GetPosition())) ? 1 : 0));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        ResetFight();
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        ResetFight();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "death");
    }

    void UpdateAI(uint32 diff) override
    {
        UpdateOdoHold(diff);
        bool const engaged = UpdateVictim();
        // `.sfktest captain charge` can start a charge out of combat: keep its events running until it ends.
        if (!engaged && !_charging)
            return;
        _clockMs += diff;

        if (engaged && !_arena.Update(me, diff))
            return;     // he left his arena: evading

        events.Update(diff);
        if (me->IsActionPreventedByCasting())
            return;

        while (uint32 const eventId = events.ExecuteEvent())
        {
            ExecuteEvent(eventId);
            if (me->IsActionPreventedByCasting())
                return;
        }

        if (engaged)
            DoMeleeAttackIfReady();
    }

    void ExecuteEvent(uint32 eventId) override
    {
        bool const heroic = IsHeroicMap(me);
        switch (eventId)
        {
            case EVENT_CAPTAIN_CHARGE:
                if (_charging || _cleaving)
                {
                    events.ScheduleEvent(EVENT_CAPTAIN_CHARGE, Milliseconds(kBusyRetryMs));
                    break;
                }
                StartCharge(kChargeLegs(heroic), false);
                events.ScheduleEvent(EVENT_CAPTAIN_CHARGE, Milliseconds(kChargeEveryMs));
                break;
            case EVENT_CAPTAIN_CLEAVE:
            {
                uint32 const wait = CleaveWaitMs(_clockMs, _charging || _cleaving, _lastLandMs);
                if (wait)
                {
                    events.ScheduleEvent(EVENT_CAPTAIN_CLEAVE, Milliseconds(wait));
                    break;
                }
                SweepingCleave();
                events.ScheduleEvent(EVENT_CAPTAIN_CLEAVE, Milliseconds(kCleaveEveryMs));
                break;
            }
            case EVENT_CAPTAIN_CHECK_HEALTH:
                if (LastStandDue(heroic, me->GetHealthPct(), _lastStand))
                    LastStand();
                if (!_lastStand)
                    events.ScheduleEvent(EVENT_CAPTAIN_CHECK_HEALTH, Milliseconds(kHealthCheckMs));
                break;
            case EVENT_CAPTAIN_END_CHARGE:
                EndCharge();
                break;
            default:
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DC1 / DC2: the charge (heroic: a chain of two legs, the second from the first's landing spot)
    // ----------------------------------------------------------------------------------------------------------------

    // False when nobody can be charged at.
    bool StartCharge(uint8 legs, bool widen)
    {
        if (NonTanks(widen).empty())
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "charge", "skipped (no non-tank)");
            return false;
        }
        _charging = true;
        // The safety net: back to the tank even if a leg is refused or cancelled (the real end comes sooner).
        events.ScheduleEvent(EVENT_CAPTAIN_END_CHARGE,
            Milliseconds(ChargeChainMs(legs) + kChargeSafetyMs + 2 * kReturnDelayMs));
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        if (!ChargeLeg(0, legs, me->GetPosition(), {}, widen))
            EndChargeSoon(0);
        return true;
    }

    // One leg: from `from` to a non-tank not yet in `chain`; on its resolve he charges along it and the next leg
    // (heroic) starts from its end.
    bool ChargeLeg(uint8 step, uint8 legs, Position const& from, std::vector<uint64> chain, bool widen)
    {
        std::vector<Player*> const players = NonTanks(widen);
        std::vector<ChargeCandidate> candidates;
        std::vector<bool> reaches;
        Vec2 const origin = ToVec(from);
        float const fallback = step == 0 ? me->GetOrientation() : from.GetOrientation();
        for (Player const* player : players)
        {
            Vec2 const at = ToVec(player->GetPosition());
            candidates.push_back({ player->GetGUID().GetRawValue(), at });
            reaches.push_back(ChargeReaches(ChargeLine(_shape, origin, at, fallback), at));
        }
        std::optional<std::size_t> const pick = PickReachableChargeTarget(candidates, origin, chain,
            kChargeMinDistance, reaches, RandomIndex);
        if (!pick)
            return false;

        Player* target = players[*pick];
        char const* const name = step == 0 ? "charge" : "chain-charge";
        ChargePath const path = ChargeLine(_shape, origin, candidates[*pick].pos, fallback);
        if (path.length < kChargeMinLength)
        {
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, name, Acore::StringFormat(
                "skipped (line {:.1f} yd at the arena's edge) target={}", path.length, target->GetName()));
            return false;
        }
        chain.push_back(candidates[*pick].id);

        Position const start(origin.x, origin.y, from.GetPositionZ(), path.facing);
        Position const to(path.end.x, path.end.y, from.GetPositionZ(), path.facing);
        if (step == 0)
        {
            me->SetFacingTo(path.facing);
            DungeonKit::CastBar(me, SPELL_CAPTAIN_CHARGE_BAR, nullptr, EMOTE_CAPTAIN_CHARGE, target);
        }

        Milliseconds const warn(step == 0 ? kChargeWarnMs : kChainWarnMs);
        MechanicRef ref = Mechanic::Line(me, start, path.facing, path.length, kChargeWidth, warn);
        ref.ExcludeSourceEnd(kChargeExclude).Damage(kChargePct).Weakened().Spell(SPELL_CAPTAIN_CHARGE_HIT)
            .Tag(step == 0 ? TAG_DEATHSWORN_CHARGE : TAG_CHAIN_CHARGE);
        float const length = path.length;
        ref.OnResolve(OnCaptain([to, step, legs, chain, widen, length](boss_deathsworn_captain_rework& ai,
            BossMechanics::ResolveResult const&)
        {
            ai.ChargeResolved(to, step, legs, chain, widen, length);
        }));
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, name, Acore::StringFormat(
            "leg={}/{} target={} length={:.1f} walkway={} clipped={} reaches={}", step + 1, legs, target->GetName(),
            path.length, path.alongWalkway ? 1 : 0, path.clipped ? 1 : 0, reaches[*pick] ? 1 : 0));
        return true;
    }

    void ChargeResolved(Position const& to, uint8 step, uint8 legs, std::vector<uint64> const& chain, bool widen,
        float length)
    {
        // DC1's look is its cast bar's own visual (it plays as the bar completes); a chained leg has no bar.
        if (step > 0)
            DoCastSelf(SPELL_CAPTAIN_CHARGE_TRAIL, true);
        me->GetMotionMaster()->MoveCharge(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), kChargeSpeed,
            EVENT_CHARGE, nullptr, true);
        uint32 const travel = ChargeTravelMs(length);
        _lastLandMs = _clockMs + travel;
        if (step + 1 < legs && ChargeLeg(step + 1, legs, to, chain, widen))
            return;
        EndChargeSoon(travel);
    }

    void EndChargeSoon(uint32 travelMs)
    {
        events.RescheduleEvent(EVENT_CAPTAIN_END_CHARGE, Milliseconds(travelMs + kReturnDelayMs));
    }

    void EndCharge()
    {
        if (!_charging)
            return;
        _charging = false;
        me->GetMotionMaster()->Clear();
        if (Unit* victim = me->GetVictim())
            me->GetMotionMaster()->MoveChase(victim);
        else if (!me->IsEngaged())
            me->GetMotionMaster()->MoveTargetedHome();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DC3: Sweeping Cleave
    // ----------------------------------------------------------------------------------------------------------------

    void SweepingCleave()
    {
        if (Unit* victim = me->GetVictim())
            me->SetFacingToObject(victim);
        DungeonKit::CastBar(me, SPELL_CAPTAIN_CLEAVE_BAR, nullptr, EMOTE_CAPTAIN_CLEAVE);
        MechanicRef ref = Mechanic::Cone(me, me, kCleaveAngle, kCleaveLength, Milliseconds(kCleaveWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(kCleavePct).Weakened().Spell(SPELL_CAPTAIN_CLEAVE_HIT).Tag(TAG_SWEEPING_CLEAVE);
        _cleaving = ref.IsValid();
        ref.OnResolve(OnCaptain([](boss_deathsworn_captain_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.CleaveResolved();
        }));
        Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sweeping-cleave",
            Acore::StringFormat("registered={}", _cleaving ? 1 : 0));
    }

    // The cone skipped the tank (TankExempt): the victim takes two swings (206015) if it stands in the arc.
    void CleaveResolved()
    {
        _cleaving = false;
        Unit* tank = me->GetVictim();
        if (!tank || !tank->IsAlive())
            return;
        if (!DungeonKit::InFrontalCone(ToVec(me->GetPosition()), me->GetOrientation(), ToVec(tank->GetPosition()),
            kCleaveAngle, kCleaveLength, me->GetCombatReach() + tank->GetCombatReach()))
            return;
        me->CastSpell(tank, SPELL_CAPTAIN_CLEAVE_TANK, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "sweeping-cleave-tank",
            Acore::StringFormat("on={}", tank->GetName()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // DC4: Last Stand (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void LastStand()
    {
        _lastStand = true;
        DoCastSelf(SPELL_CAPTAIN_LAST_STAND, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "last-stand",
            Acore::StringFormat("health={:.1f}%", me->GetHealthPct()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.sfktest captain` entry points
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Charge,
        Cleave,
        LastStand,
    };

    // An empty string when fired; otherwise why not. `heroic` forces the heroic chain on a normal map.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (_charging || _cleaving || me->IsNonMeleeSpellCast(false))
            return "The Deathsworn Captain is busy (charging or casting); try again in a few seconds.";
        switch (mechanic)
        {
            case TestMechanic::Charge:
                if (!StartCharge(kChargeLegs(heroic), true))
                    return "No player to charge at (.gm off, alive, within 100 yd).";
                break;
            case TestMechanic::Cleave:
                SweepingCleave();
                break;
            case TestMechanic::LastStand:
                if (_lastStand)
                    return "Last Stand is already up.";
                LastStand();
                break;
        }
        return {};
    }

    // The charge line from him to `player`, without firing it (the walkway check of the playtest).
    std::string PreviewLine(Player const* player) const
    {
        Vec2 const from = ToVec(me->GetPosition());
        Vec2 const at = ToVec(player->GetPosition());
        ChargePath const path = ChargeLine(_shape, from, at, me->GetOrientation());
        return Acore::StringFormat("captain walkway={} on-arena={}; you on-arena={}; line length={:.1f} "
            "facing={:.2f} along-walkway={} clipped={} reaches-you={} end=({:.1f}, {:.1f})",
            OnWalkway(_shape, from) ? 1 : 0, _arena.Contains(me) ? 1 : 0, _arena.Contains(player) ? 1 : 0,
            path.length, path.facing, path.alongWalkway ? 1 : 0, path.clipped ? 1 : 0,
            ChargeReaches(path, at) ? 1 : 0, path.end.x, path.end.y);
    }

    void TestGrip(Player* player)
    {
        _arena.Grip(me, player, "test");
    }

    bool HeroicMap() const
    {
        return IsHeroicMap(me);
    }

private:
    static constexpr uint32 kOdoHoldCheckMs = 500;
    static constexpr uint32 kOdoHoldPointId = 1;

    // R2 S-2 (orchestrator call): while Odo is IN_PROGRESS and he is out of combat, he holds his patrol short of Odo's
    // doorway, passive and immune to players (a bell ringer at bell 3 or a hunted player at the door never pulls him
    // into Odo's fight). When Odo is done, failed or reset, his patrol (the spawn's waypoint movement) resumes.
    void UpdateOdoHold(uint32 diff)
    {
        _odoHoldCheckMs += diff;
        if (_odoHoldCheckMs < kOdoHoldCheckMs)
            return;
        _odoHoldCheckMs = 0;
        bool const hold = instance && me->IsAlive() && !me->IsInCombat()
            && HoldForOdo(instance->GetBossState(BOSS_ODO));
        if (hold == _heldForOdo)
            return;
        _heldForOdo = hold;
        if (hold)
        {
            me->SetReactState(REACT_PASSIVE);
            me->SetImmuneToPC(true);
            // Idle replaces the waypoint movement in the idle slot, so a walk back ends standing, not patrolling.
            me->GetMotionMaster()->Clear();
            me->GetMotionMaster()->MoveIdle();
            bool const walkBack = HoldWalksBack(ToVec(me->GetPosition()));
            if (walkBack)
            {
                Point3 const at = OdoHoldPoint();
                me->GetMotionMaster()->MovePoint(kOdoHoldPointId, at.x, at.y, at.z);
            }
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "odo-hold", Acore::StringFormat(
                "at=({:.1f}, {:.1f}) walk-back={}", me->GetPositionX(), me->GetPositionY(), walkBack ? 1 : 0));
        }
        else
        {
            me->SetImmuneToPC(false);
            me->SetReactState(REACT_AGGRESSIVE);
            if (me->IsAlive() && !me->IsInCombat())
                me->GetMotionMaster()->Initialize();
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "odo-hold", "released");
        }
    }

    // A leg's safety margin past the chain's last resolve (the longest charge, ~40 yd, takes about 1 s at 42 yd/s).
    static constexpr uint32 kChargeSafetyMs = 2000;

    // The pull's state: nothing pending, no buff (a `.sfktest` charge out of combat may have left a state behind).
    void ResetFight()
    {
        CancelLive();
        events.Reset();
        _arena.Reset();
        _charging = false;
        _cleaving = false;
        _lastStand = false;
        _lastLandMs.reset();
        _clockMs = 0;
        me->RemoveAurasDueToSpell(SPELL_CAPTAIN_LAST_STAND);
    }

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if he is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnCaptain(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* captain = map->GetCreature(guid);
            if (!captain || !captain->IsAlive() || !captain->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_deathsworn_captain_rework*>(captain->AI()))
                fn(*ai, result);
        };
    }

    // Players the charge may choose: alive, not GMs, within 100 yd, and not the tank (the registry's role provider:
    // with a victim, the victim is the tank). `widen` (`.sfktest`): everyone, when nobody but a tank is there.
    std::vector<Player*> NonTanks(bool widen) const
    {
        std::vector<Player*> nonTanks;
        std::vector<Player*> everyone;
        BossMechanics::RoleProvider const& roles = BossMechanics::GetRoleProvider();
        Map::PlayerList const& players = me->GetMap()->GetPlayers();
        for (Map::PlayerList::const_iterator itr = players.begin(); itr != players.end(); ++itr)
        {
            Player* player = itr->GetSource();
            if (!player || !player->IsAlive() || player->IsGameMaster() || !me->IsWithinDistInMap(player, 100.f))
                continue;
            everyone.push_back(player);
            if (roles.Get(me, player) != BossMechanics::Role::Tank)
                nonTanks.push_back(player);
        }
        if (nonTanks.empty() && widen)
            return everyone;
        return nonTanks;
    }

    void Track(BossMechanics::MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // A reset or a death drops every mechanic still warning (their follow-ups never run: a cancelled mechanic never
    // resolves).
    void CancelLive()
    {
        for (BossMechanics::MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
    }

    Arena const _shape;                         // DeathswornCaptainArena(): the charge lines' floor plan
    DungeonKit::ArenaGuard _arena;
    std::vector<BossMechanics::MechanicHandle> _live;
    std::optional<uint32> _lastLandMs;          // on _clockMs: DC3's 4 s guard
    uint32 _clockMs = 0;                        // fight time (UpdateAI), never paused by a cast
    bool _charging = false;
    bool _cleaving = false;
    bool _lastStand = false;
    uint32 _odoHoldCheckMs = 0;
    bool _heldForOdo = false;                   // R2 S-2: holding short of Odo's door while Odo fights
};

// 206015 Sweeping Cleave, the tank's hit: two of his swings (Unit::CalculateDamage of his main hand: his template's
// weapon damage and DamageModifier, so heroic reads the heroic template's boss tier). Set at launch so the tank's
// damage-taken modifiers apply; Physical, so armor applies as on a swing. IGNORE_CASTER_MODIFIERS (DT) keeps the
// spell path's damage-done bonuses off the value (CalculateDamage already holds his own).
class spell_sfk_captain_cleave_tank : public SpellScript
{
    PrepareSpellScript(spell_sfk_captain_cleave_tank);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;
        uint32 damage = 0;
        for (uint32 i = 0; i < kCleaveTankSwings; ++i)
            damage += caster->CalculateDamage(BASE_ATTACK, false, true);
        SetEffectValue(static_cast<int32>(damage));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_sfk_captain_cleave_tank::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_deathsworn_captain_rework* FindCaptainAI(ChatHandler* handler)
    {
        Creature* captain = SfkTest::FindBoss(handler, NPC_DEATHSWORN_CAPTAIN);
        if (!captain)
            return nullptr;
        auto* ai = captain->IsAIEnabled ? dynamic_cast<boss_deathsworn_captain_rework*>(captain->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "The Deathsworn Captain is not running boss_deathsworn_captain_rework "
                "(check the ScriptName).");
        return ai;
    }

    bool Report(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Deathsworn Captain: {} fired.", what);
        return true;
    }

    bool Fire(ChatHandler* handler, boss_deathsworn_captain_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_deathsworn_captain_rework* ai = FindCaptainAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        return Report(handler, ai->TestFire(mechanic, isHeroic), what);
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SfkTest::ShowBossInfo(handler, NPC_DEATHSWORN_CAPTAIN, BOSS_DEATHSWORN_CAPTAIN);
    }

    bool HandleCharge(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_deathsworn_captain_rework::TestMechanic::Charge, heroic,
            "Deathsworn Charge (DC1; heroic: + Chain Charge DC2)");
    }

    bool HandleCleave(ChatHandler* handler)
    {
        return Fire(handler, boss_deathsworn_captain_rework::TestMechanic::Cleave, {}, "Sweeping Cleave (DC3)");
    }

    bool HandleLastStand(ChatHandler* handler)
    {
        return Fire(handler, boss_deathsworn_captain_rework::TestMechanic::LastStand, {}, "Last Stand (DC4)");
    }

    bool HandleLine(ChatHandler* handler)
    {
        boss_deathsworn_captain_rework* ai = FindCaptainAI(handler);
        Player* player = handler->GetPlayer();
        if (!ai || !player)
            return false;
        handler->PSendSysMessage("{}", ai->PreviewLine(player));
        return true;
    }

    bool HandleGrip(ChatHandler* handler)
    {
        boss_deathsworn_captain_rework* ai = FindCaptainAI(handler);
        Player* player = handler->GetPlayer();
        if (!ai || !player)
            return false;
        ai->TestGrip(player);
        handler->PSendSysMessage("{}", "Deathsworn Captain: gripped you onto his patrol line.");
        return true;
    }

    // `.sfktest captain <sub> [1]`: `charge 1` forces the heroic chain (0 forces normal); default: the map's.
    ChatCommandTable const& DeathswornCaptainTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "charge",    HandleCharge,    SEC_GAMEMASTER, Console::No },
            { "cleave",    HandleCleave,    SEC_GAMEMASTER, Console::No },
            { "laststand", HandleLastStand, SEC_GAMEMASTER, Console::No },
            { "line",      HandleLine,      SEC_GAMEMASTER, Console::No },
            { "grip",      HandleGrip,      SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_deathsworn_captain_rework()
{
    RegisterDungeonReworkCreatureAI(boss_deathsworn_captain_rework, ShadowfangKeepRework::kInstanceScriptName);
    RegisterSpellScript(spell_sfk_captain_cleave_tank);
    SfkTest::RegisterBoss("captain", DeathswornCaptainTestCommands());
}
