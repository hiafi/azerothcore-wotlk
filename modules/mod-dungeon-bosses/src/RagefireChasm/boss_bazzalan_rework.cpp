/*
 * mod-dungeon-bosses, Ragefire Chasm D3: Bazzalan (11519), the cult's rogue, normal and heroic. Build spec:
 * docs/dungeons/ragefire-chasm-rework.md "Bazzalan" (BZ1-BZ8), handoff section 3.5 row D3 (rules 1-36), 3.6, 3.8 (his
 * ridge), 3.10, 3.12. Replaces SmartAI 11519 (dropped by WP-S0's rev; the template is bound by apps/dbc-tools
 * source/npcs/ragefire_chasm/bazzalan.py); Sinister Strike 14873 and Deadly Poison 2818 are retired as his casts (they
 * carry live rogue rework rows: his are copies). Pure rules: BazzalanLogic.h.
 *
 *   BZ1 Combo points     a Sinister Strike on his target at 2 s, then every 3 s (heroic 2 s), in melee range only; each
 *                        adds a point, a stacking aura on him (1 to 5). Cast triggered: a kicked Eviscerate's Physical
 *                        lockout never eats it (rule 25)
 *   BZ2 Finisher         at 5 points: an emote and a 2 s bar that roots him, then the points are spent. Normal: a
 *                        shuffled bag of BZ3-BZ5; heroic: {BZ3, BZ6}, then {BZ4, BZ7}, at random within each half
 *   BZ3 Eviscerate       his target: 35% / 50% of the tank row, Physical; kickable (the points go for nothing)
 *   BZ4 Rupture          a random player, the tank included (heroic: one without a Rupture): 40% over 12 s (heroic 2%
 *                        every 2 s to the end of the fight); not interruptible
 *   BZ5 Fan of Knives    normal: an 8 yd registry circle on him for the bar, 35% and Weakened, the tank included
 *   BZ6 Envenom          heroic: his target, 10% of the tank row per Deadly Poison stack consumed; kickable
 *   BZ7 Shadowstep       heroic: after the bar three landings 2.5 s apart, each behind a different player (the tank
 *                        included) with a 6 yd registry circle on him for 2 s: 45%, Weakened and Crippling Poison; then
 *                        back to the tank, threat unchanged (AttackStop and passive meanwhile, rule 35)
 *   BZ8 Poisons          a landed swing: Deadly Poison 50% of the time (his swing is 2.0 s: "50% every 2 s"), heroic
 *                        also a Wound Poison
 *
 * Bars that must play (Rupture, Fan, Shadowstep) are Shadow (rule 25: never the school of a kickable cast).
 *
 * Where he fights (R-1-BOSS M-1): he never leaves his arena (4 yd inside the rims), but a target on the rim band keeps
 * him: he stands at his edge and reaches it (ArenaEdge). Only a target out of that reach (ReachArena) turns him to
 * someone inside, and neither guard runs during the chain.
 */

#include "ArenaGuard.h"
#include "BazzalanLogic.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFlow.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RagefireChasmKit.h"
#include "RagefireChasmRework.h"
#include "RagefireChasmTestCommand.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringFormat.h"
#include "ThreatManager.h"
#include <algorithm>
#include <cmath>
#include <functional>
#include <optional>
#include <string>
#include <utility>
#include <vector>

using namespace Acore::ChatCommands;
using namespace RagefireChasmRework;
using namespace RfcBazzalan;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBossLogName = "bazzalan";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    uint32 RandomBelow(uint32 n)
    {
        return n ? urand(0, n - 1) : 0;
    }

    // A player the fight acts on: in the world, alive, not a game master.
    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }
}

// Bazzalan 11519
struct boss_bazzalan_rework : public BossAI
{
    explicit boss_bazzalan_rework(Creature* creature)
        : BossAI(creature, BOSS_BAZZALAN), _arena(BazzalanArena(), SelfLeash(kBossLogName)),
          _reach(ReachArena(), ReachLeash(kBossLogName)),
          _edge(kRidgeArenaPolygon, [this](Vec2 p, float z) { return FloorZ(p, z); }) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter
    // ----------------------------------------------------------------------------------------------------------------

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup();
        _heroic = IsHeroicMap(me);
        OnBossPull(me, kBossLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_BAZZALAN;
        Mechanic::BeginEncounter(me, options);
        Describe();
        _arena.Engage(me);
        Talk(YELL_BAZZALAN_AGGRO);

        _bag.Reset(_heroic);
        _next = _bag.Draw(RandomBelow);
        _strike.Start(_clockMs + Tune::kStrikeFirstMs);
        NoteNext();
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
            Acore::StringFormat("clock={}s strikes={} finishers={} kicked={} fan-hits={} step-hits={} deadly={} "
                "killer={}", _clockMs / 1000, _strikes, _finishers, _kicked, _fanHits, _stepHits, _deadly,
                killer ? killer->GetName() : "none"));
        Cleanup();
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        me->SetAssistanceTimer(0);      // section 7 #12 A: the flag stops the first call only
        if (!UpdateVictim())
            return;
        // The chain (no victim, every landing on his arena): the guards wait, or they would turn him meanwhile.
        // A jump takes nobody out of his reach (RF2-m1): the reach is not asked meanwhile.
        Unit const* victim = me->GetVictim();
        bool const jump = _jump.Skip(victim && victim->HasUnitMovementFlag(MOVEMENTFLAG_FALLING), diff);
        if (!_state.passive && (!_arena.Update(me, diff) || (!jump && !_reach.Update(me, diff))))
            return;     // off his arena, or nobody in reach for 10 s: evading
        _edge.HoldBackstep(me);

        UpdateFinisher();
        if (_state.active)
            return;     // a bar or the chain: he stands and does not swing
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        _edge.Update(me, _arena, _reach);
        UpdateStrike();
        // Never a 2 s bar while off his arena: he walks back first (RF-1 RF-M1).
        if (Points() >= Tune::kComboMax && _clockMs >= _retryAtMs && _arena.Contains(me))
        {
            StartFinisher(Finisher::None);
            if (_state.active)
                return;
        }
        DoMeleeAttackIfReady();
    }

    // A kick or a silence stopped a kickable finisher. His own stops (an evade, his death, a reset) drop the state
    // before the engine interrupts the cast, so they are never read as a kick.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        BossAI::OnSpellFailed(spell);
        if (!spell || !_state.active || !me->IsAlive() || spell->Id != SpellOf(_state.kind) || !Kickable(_state.kind))
            return;
        ++_kicked;
        EndFinisher("kicked");
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        BossAI::OnSpellCast(spell);
        if (spell && _state.active && Kickable(_state.kind) && spell->Id == SpellOf(_state.kind))
            EndFinisher("landed");
    }

    // BZ8: a landed swing on his target (a miss, a dodge and a full absorb deal 0).
    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType type, SpellSchoolMask mask) override
    {
        BossAI::DamageDealt(victim, damage, type, mask);
        if (type != DIRECT_DAMAGE || !damage || !victim || !victim->IsPlayer() || victim != me->GetVictim()
            || !me->IsEngaged())
            return;
        if (urand(1, 100) <= Tune::kDeadlyChancePct)
            ApplyDeadly(victim);
        if (_heroic)
            me->CastSpell(victim, SPELL_BZ_WOUND_POISON, true);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BZ1 Sinister Strike and combo points
    // ----------------------------------------------------------------------------------------------------------------

    uint32 Points() const
    {
        return DungeonKit::Stacks(me, SPELL_BZ_COMBO_POINTS, me->GetGUID());
    }

    // In melee range only (no points while the tank is out of it, section 7 #34 A): a due strike stays due.
    void UpdateStrike()
    {
        if (!_strike.Due(_clockMs))
            return;
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return;
        _strike.Fired(_clockMs, Tune::kStrikeEveryMs(_heroic));
        Strike(victim);
    }

    // The point comes with the strike, hit or not: the tank's avoidance never slows the fight's clock.
    void Strike(Unit* victim)
    {
        ++_strikes;
        me->CastSpell(victim, SPELL_BZ_SINISTER_STRIKE, true);
        uint32 const points = DungeonKit::AddStacks(me, SPELL_BZ_COMBO_POINTS, 1, me, Tune::kComboMax);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "strike", Acore::StringFormat("target={} points={}",
            victim->GetName(), points));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BZ2 the finishers
    // ----------------------------------------------------------------------------------------------------------------

    static uint32 SpellOf(Finisher f)
    {
        switch (f)
        {
            case Finisher::Eviscerate:
                return SPELL_BZ_EVISCERATE;
            case Finisher::Rupture:
                return SPELL_BZ_RUPTURE_CAST;
            case Finisher::Fan:
                return SPELL_BZ_FAN_CAST;
            case Finisher::Envenom:
                return SPELL_BZ_ENVENOM;
            case Finisher::Shadowstep:
                return SPELL_BZ_SHADOWSTEP_CAST;
            default:
                return 0;
        }
    }

    // The drawn finisher, else the first one of its attempt order someone can take. `forced` (the `.dbtest` command):
    // that one only. Nothing starts: the points stay and he tries again in a second.
    bool StartFinisher(Finisher forced)
    {
        std::vector<Finisher> const order = forced != Finisher::None ? std::vector<Finisher>{ forced }
            : AttemptOrder(_next, _heroic);
        for (Finisher f : order)
            if (TryFinisher(f))
            {
                ++_finishers;
                return true;
            }
        _retryAtMs = _clockMs + kRetryMs;
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "finisher-refused", NameOf(order.front()));
        return false;
    }

    bool TryFinisher(Finisher f)
    {
        me->StopMoving();
        switch (f)
        {
            case Finisher::Eviscerate:
                return StartKickable(f, EMOTE_BAZZALAN_EVISCERATE);
            case Finisher::Envenom:
                return StartKickable(f, EMOTE_BAZZALAN_ENVENOM);
            case Finisher::Rupture:
                return StartRupture();
            case Finisher::Fan:
                return StartFan();
            case Finisher::Shadowstep:
                return StartShadowstep();
            default:
                return false;
        }
    }

    // BZ3 and BZ6: a real 2 s cast on his target, kickable; its SpellScript sets the hit at launch.
    bool StartKickable(Finisher f, uint8 emote)
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        // The state first: an instant failure inside CastSpell must find it.
        BeginState(f);
        SpellCastResult const result = me->CastSpell(victim, SpellOf(f), false);
        if (result != SPELL_CAST_OK)
        {
            _state = FinisherState();
            DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "cast-refused",
                Acore::StringFormat("{} result={}", NameOf(f), static_cast<uint32>(result)));
            return false;
        }
        Talk(emote);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, NameOf(f),
            Acore::StringFormat("target={} deadly={}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_BZ_DEADLY_POISON, me->GetGUID())));
        return true;
    }

    // BZ4: the player is named at the bar's start (the tank included; never one who bleeds already).
    bool StartRupture()
    {
        Player* target = PickRuptureTarget(nullptr);
        if (!target)
            return false;
        BeginState(Finisher::Rupture);
        _state.target = target->GetGUID();
        DungeonKit::CastBar(me, SPELL_BZ_RUPTURE_CAST, nullptr, uint8(EMOTE_BAZZALAN_RUPTURE), target);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rupture", Acore::StringFormat("target={} tank={}",
            target->GetName(), target == me->GetVictim() ? 1 : 0));
        return true;
    }

    bool Bleeding(Player const* player) const
    {
        return player->HasAura(SPELL_BZ_RUPTURE, me->GetGUID())
            || player->HasAura(SPELL_BZ_RUPTURE_HEROIC, me->GetGUID());
    }

    Player* PickRuptureTarget(Player const* skip) const
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // the tank included
        static DungeonKit::Arena const ridge = RidgeFloor();
        std::vector<std::pair<std::uint64_t, bool>> players;
        for (Player* player : FightPlayers())
        {
            players.emplace_back(player->GetGUID().GetRawValue(),
                ridge.Contains(DungeonKit::PlaneOf(player), player->GetPositionZ()));
            if (player == skip || Bleeding(player))
                rule.exclude.push_back(player->GetGUID().GetRawValue());
        }
        // Nobody in the tunnels or the hall below (a free Rupture, and one target fewer later).
        for (std::uint64_t const guid : Outsiders(players))
            rule.exclude.push_back(guid);
        return DungeonKit::PickPlayer(me, rule);
    }

    // The bar is over: the cut, then the bleed. The named player died meanwhile: someone else takes it.
    void LandRupture()
    {
        Player* target = ObjectAccessor::GetPlayer(*me, _state.target);
        if (!CountsAsPlayer(target) || !target->IsInMap(me))
            target = PickRuptureTarget(target);
        if (!target)
        {
            EndFinisher("no-target");
            return;
        }
        uint32 const bleed = _heroic ? SPELL_BZ_RUPTURE_HEROIC : SPELL_BZ_RUPTURE;
        me->CastSpell(target, SPELL_BZ_RUPTURE_LOOK, true);
        me->CastSpell(target, bleed, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "rupture-lands",
            Acore::StringFormat("target={} applied={} tick={}", target->GetName(),
                target->HasAura(bleed, me->GetGUID()) ? 1 : 0,
                DungeonKit::RefFlatOn(me, target, Tune::RuptureTickPct(_heroic))));
        EndFinisher("landed");
    }

    // BZ5 (normal): the circle on him for the bar, the tank included; he stands, so the melee steps out with the tank.
    bool StartFan()
    {
        BeginState(Finisher::Fan);
        DungeonKit::CastBar(me, SPELL_BZ_FAN_CAST, nullptr, uint8(EMOTE_BAZZALAN_FAN));
        uint32 const gen = _generation;
        MechanicRef ref = Mechanic::Circle(me, me, Tune::kFanRadius, Ms(Tune::kFanWarnMs));
        ref.Damage(Tune::kFanPct).TankDamage(Tune::kFanPct).Spell(SPELL_BZ_FAN).Weakened()
            .Within(BazzalanFloorBounds()).Tag(TAG_BZ_FAN)
            .OnResolve(OnBazzalan([gen](boss_bazzalan_rework& ai, BossMechanics::ResolveResult const& result)
            {
                if (ai._generation == gen && !result.fizzled)
                    ai.FanLanded(result);
            }));
        if (ref.IsValid())
            Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fan", Acore::StringFormat("pct={:.0f} r={:.0f}",
            Tune::kFanPct, Tune::kFanRadius));
        return true;
    }

    void FanLanded(BossMechanics::ResolveResult const& result)
    {
        _fanHits += static_cast<uint32>(result.hits.size());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "fan-lands",
            Acore::StringFormat("hits={}:{}", result.hits.size(), Names(result.hits)));
    }

    void BeginState(Finisher f)
    {
        _state = FinisherState();
        _state.active = true;
        _state.kind = f;
        _state.barEndMs = _clockMs + Tune::kFinisherCastMs;
    }

    // The bar's end (by the fight's clock) and the chain's steps.
    void UpdateFinisher()
    {
        if (!_state.active)
            return;
        if (Kickable(_state.kind))
        {
            // The cast ends through OnSpellCast or OnSpellFailed; a target that died under it ends it silently.
            if (_clockMs >= _state.barEndMs + kCastGraceMs && !me->HasUnitState(UNIT_STATE_CASTING))
                EndFinisher("lost");
            return;
        }
        if (_state.kind == Finisher::Shadowstep)
        {
            UpdateShadowstep();
            return;
        }
        if (_clockMs < _state.barEndMs || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (_state.kind == Finisher::Rupture)
            LandRupture();
        else
            EndFinisher("landed");
    }

    // The points are spent (a kick spends them for nothing); the strikes go on from the finisher's nominal end, so a
    // kick never brings the next finisher forward.
    void EndFinisher(char const* how)
    {
        FinisherState const state = _state;
        _state = FinisherState();
        DungeonKit::AddStacks(me, SPELL_BZ_COMBO_POINTS, -static_cast<int32>(Tune::kComboMax), me, Tune::kComboMax);
        if (state.forced)
            return;     // `.dbtest`: the bag's own order goes on
        _next = _bag.Draw(RandomBelow);
        _strike.Start(std::max(_clockMs, state.barEndMs) + kStrikeAfterFinisherMs(_heroic));
        NoteNext();
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "finisher-end",
            Acore::StringFormat("{} how={} next={}", NameOf(state.kind), how, NameOf(_next)));
    }

    // The overload hold of the bots' interrupters reads when the next kickable bar starts.
    void NoteNext()
    {
        if (Kickable(_next))
            Mechanic::NoteNextCastIn(me, SpellOf(_next),
                Ms(NextFinisherInMs(_heroic, Points(), _strike.InMs(_clockMs))));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BZ7 Shadowstep and Fan of Knives (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // Needs someone to appear behind now; the steps pick their players as they land.
    bool StartShadowstep()
    {
        if (!PickStep())
            return false;
        BeginState(Finisher::Shadowstep);
        _state.nextStepMs = _state.barEndMs;
        DungeonKit::CastBar(me, SPELL_BZ_SHADOWSTEP_CAST);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shadowstep", Acore::StringFormat("steps={} every={}ms",
            Tune::kShadowstepCount, kShadowstepEveryMs));
        return true;
    }

    struct Step
    {
        Player* player = nullptr;
        Position at;
    };

    // A random player (the tank included) this chain has not visited, whose landing is on the ridge.
    std::optional<Step> PickStep() const
    {
        std::vector<Step> pool;
        for (Player* player : FightPlayers())
        {
            if (_state.visited.count(player->GetGUID()))
                continue;
            if (std::optional<Position> const at = LandingBehind(player))
                pool.push_back({ player, *at });
        }
        if (pool.empty())
            return std::nullopt;
        return pool[RandomBelow(static_cast<uint32>(pool.size()))];
    }

    std::optional<Position> LandingBehind(Player const* player) const
    {
        Vec2 const at = DungeonKit::PlaneOf(player);
        float const z = player->GetPositionZ();
        if (z < kRidgeZMin || z > kRidgeZMax)
            return std::nullopt;    // off the ridge (the hall below), or far over it
        std::optional<Vec2> const landing = ShadowstepLanding(at, player->GetOrientation());
        if (!landing)
            return std::nullopt;
        std::optional<float> const floor = FloorZ(*landing, z);
        if (!floor)
            return std::nullopt;
        return DungeonKit::ToPosition(*landing, *floor, DungeonKit::BearingTo(*landing, at));
    }

    // The floor under `p` near height `z`; nothing when there is none there.
    std::optional<float> FloorZ(Vec2 p, float z) const
    {
        float const floor = me->GetMapHeight(p.x, p.y, z + 3.f);
        if (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > kLandingZBandYd)
            return std::nullopt;
        return floor;
    }

    void UpdateShadowstep()
    {
        if (_clockMs < _state.nextStepMs || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        if (!_state.passive)
        {
            // He leaves his target: threat unchanged, no chase until he is back (rule 35).
            _state.passive = true;
            _edge.Reset();
            me->SetReactState(REACT_PASSIVE);
            me->AttackStop();
            me->GetMotionMaster()->Clear();
            me->GetMotionMaster()->MoveIdle();
            _state.from = DungeonKit::PlaneOf(me);
        }
        if (_state.steps < Tune::kShadowstepCount)
            if (std::optional<Step> const step = PickStep())
            {
                Land(*step);
                return;
            }
        EndChain();
    }

    void Land(Step const& step)
    {
        ++_state.steps;
        _state.visited.insert(step.player->GetGUID());
        _state.nextStepMs = _clockMs + kShadowstepEveryMs;
        me->CastSpell(me, SPELL_BZ_SHADOWSTEP_LOOK, true);
        me->StopMoving();
        me->NearTeleportTo(step.at.GetPositionX(), step.at.GetPositionY(), step.at.GetPositionZ(),
            step.at.GetOrientation());
        me->CastSpell(me, SPELL_BZ_SHADOWSTEP_LOOK, true);
        Talk(EMOTE_BAZZALAN_SHADOWSTEP, step.player);
        DungeonKit::CastBar(me, SPELL_BZ_FAN_CAST);
        uint32 const gen = _generation;
        MechanicRef ref = Mechanic::Circle(me, me, Tune::kShadowstepRadius, Ms(Tune::kShadowstepWarnMs));
        ref.Damage(Tune::kShadowstepPct).TankDamage(Tune::kShadowstepPct).Spell(SPELL_BZ_FAN).Weakened()
            .Rider(SPELL_BZ_CRIPPLING_POISON).Within(BazzalanFloorBounds()).Tag(TAG_BZ_STEP_FAN)
            .OnResolve(OnBazzalan([gen](boss_bazzalan_rework& ai, BossMechanics::ResolveResult const& result)
            {
                if (ai._generation == gen && !result.fizzled)
                    ai.StepLanded(result);
            }));
        if (ref.IsValid())
            Track(ref.Handle());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shadowstep-lands",
            Acore::StringFormat("step={} target={} at=({:.1f}, {:.1f}, {:.1f}) rim={:.1f}", _state.steps,
                step.player->GetName(), step.at.GetPositionX(), step.at.GetPositionY(), step.at.GetPositionZ(),
                RimDistance(DungeonKit::PlaneOf(step.player))));
    }

    void StepLanded(BossMechanics::ResolveResult const& result)
    {
        _stepHits += static_cast<uint32>(result.hits.size());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "shadowstep-fan",
            Acore::StringFormat("hits={}:{}", result.hits.size(), Names(result.hits)));
    }

    // Back to the tank with the threat he left (his top threat target; he stays where he is when it has no spot).
    void EndChain()
    {
        bool const passive = _state.passive;
        Vec2 const from = _state.from;
        uint32 const steps = _state.steps;
        _state.barEndMs = _clockMs;
        EndFinisher(steps ? "landed" : "no-target");
        if (!passive)
            return;
        me->SetReactState(REACT_AGGRESSIVE);
        // Back to the tank (SP BZ7), never to whoever the guard turned him to before the chain.
        if (!_reach.SwitchedTo().IsEmpty() && me->GetThreatMgr().GetFixateTarget()
            && me->GetThreatMgr().GetFixateTarget()->GetGUID() == _reach.SwitchedTo())
            me->GetThreatMgr().ClearFixate();
        Unit* victim = me->SelectVictim();
        if (!victim)
            return;         // UpdateVictim decides next tick
        if (steps)
        {
            Vec2 const spot = ReturnSpot(DungeonKit::PlaneOf(victim), from);
            if (std::optional<float> const floor = FloorZ(spot, victim->GetPositionZ()))
            {
                me->CastSpell(me, SPELL_BZ_SHADOWSTEP_LOOK, true);
                me->NearTeleportTo(spot.x, spot.y, *floor, DungeonKit::BearingTo(spot, DungeonKit::PlaneOf(victim)));
                me->CastSpell(me, SPELL_BZ_SHADOWSTEP_LOOK, true);
            }
        }
        AttackStart(victim);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // BZ8 Deadly Poison
    // ----------------------------------------------------------------------------------------------------------------

    void ApplyDeadly(Unit* victim)
    {
        ++_deadly;
        me->CastSpell(victim, SPELL_BZ_DEADLY_POISON, true);
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "deadly-poison",
            Acore::StringFormat("target={} stacks={}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_BZ_DEADLY_POISON, me->GetGUID())));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data: no kill order; Eviscerate and Envenom on the interrupt list, the poisons on the dispel list
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_BAZZALAN, SPELL_BZ_EVISCERATE, kKickPriority(_heroic),
            Ms(_heroic ? kKickEveryHeroicMs : 0));
        d.dispels.push_back(BossMechanics::DispelEntry(SPELL_BZ_DEADLY_POISON, kDispelPriority));
        if (_heroic)
        {
            d.interrupts.emplace_back(NPC_BAZZALAN, SPELL_BZ_ENVENOM, kKickPriority(_heroic),
                Ms(kKickEveryHeroicMs));
            d.dispels.push_back(BossMechanics::DispelEntry(SPELL_BZ_WOUND_POISON, kDispelPriority));
            d.dispels.push_back(BossMechanics::DispelEntry(SPELL_BZ_CRIPPLING_POISON, kCripplingDispelPriority));
        }
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest rfc bazzalan` entry points (the numbers are the map's difficulty)
    // ----------------------------------------------------------------------------------------------------------------

    // An empty string when fired; otherwise why not.
    std::string TestFinisher(Finisher f)
    {
        if (!me->IsEngaged() || !me->GetVictim())
            return "Bazzalan must be in combat (the picks read his threat list, the mechanics his encounter).";
        if (_state.active || me->HasUnitState(UNIT_STATE_CASTING))
            return "He is casting already.";
        if (!StartFinisher(f))
            return "It did not start (see the log).";
        if (_state.active)
            _state.forced = true;
        return {};
    }

    std::string TestPoints(uint32 points)
    {
        if (!me->IsEngaged())
            return "Bazzalan must be in combat.";
        DungeonKit::AddStacks(me, SPELL_BZ_COMBO_POINTS, static_cast<int32>(points) - static_cast<int32>(Points()),
            me, Tune::kComboMax);
        return {};
    }

    std::string TestPoison()
    {
        Unit* victim = me->GetVictim();
        if (!me->IsEngaged() || !victim || !victim->IsPlayer())
            return "Bazzalan must fight a player.";
        ApplyDeadly(victim);
        if (_heroic)
            me->CastSpell(victim, SPELL_BZ_WOUND_POISON, true);
        return {};
    }

    std::string TestState() const
    {
        return Acore::StringFormat("clock={}s heroic={} points={} active={} next={} strikes={} finishers={} kicked={} "
            "fan-hits={} step-hits={} deadly={} on-arena={}", _clockMs / 1000, _heroic ? 1 : 0, Points(),
            NameOf(_state.active ? _state.kind : Finisher::None), NameOf(_next), _strikes, _finishers, _kicked,
            _fanHits, _stepHits, _deadly, _arena.Contains(me) ? 1 : 0);
    }

private:
    static constexpr uint32 kRetryMs = 1000;
    static constexpr uint32 kCastGraceMs = 300;

    struct FinisherState
    {
        bool active = false;
        bool forced = false;            // started by `.dbtest`
        Finisher kind = Finisher::None;
        uint64 barEndMs = 0;
        ObjectGuid target;              // BZ4
        // BZ7
        bool passive = false;           // AttackStop and passive until he is back
        uint32 steps = 0;
        uint64 nextStepMs = 0;
        GuidSet visited;
        Vec2 from;
    };

    // The players on his threat list the fight acts on.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (ThreatReference const* ref : me->GetThreatMgr().GetUnsortedThreatList())
        {
            Unit* unit = ref->GetVictim();
            Player* player = unit ? unit->ToPlayer() : nullptr;
            if (CountsAsPlayer(player) && player->IsInMap(me))
                out.push_back(player);
        }
        return out;
    }

    template <class Guids>
    std::string Names(Guids const& guids) const
    {
        std::string names;
        for (ObjectGuid const& guid : guids)
            if (Player* player = ObjectAccessor::GetPlayer(*me, guid))
                names += " " + player->GetName();
        return names;
    }

    // Runs `fn(ai, result)` on this boss when the registry calls back, if he is still there. Captures the map and the
    // guid only (a lambda the registry keeps must not hold a Unit*).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBazzalan(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            Creature* boss = map ? map->GetCreature(guid) : nullptr;
            if (!boss || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_bazzalan_rework*>(boss->AI()))
                fn(*ai, result);
        };
    }

    // A circle of the fight, kept to cancel it on a reset.
    void Track(MechanicHandle handle)
    {
        _live.push_back(handle);
        if (_live.size() > 32)      // the oldest ones resolved long ago
            _live.erase(_live.begin(), _live.begin() + 16);
    }

    // Nothing of the fight stays (reset, evade, death, a new pull): no cast, circle, point, bleed or poison, he fights
    // again. The finisher's state goes first, so his own interrupt is never read as a kick.
    void Cleanup()
    {
        ++_generation;
        bool const passive = _state.passive;
        _state = FinisherState();
        if (me->IsNonMeleeSpellCast(false))
            me->InterruptNonMeleeSpells(false);
        if (passive)
            me->SetReactState(REACT_AGGRESSIVE);
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        me->RemoveAurasDueToSpell(SPELL_BZ_COMBO_POINTS);
        if (instance)
            for (uint32 const spell : { uint32(SPELL_BZ_RUPTURE), uint32(SPELL_BZ_RUPTURE_HEROIC),
                uint32(SPELL_BZ_DEADLY_POISON), uint32(SPELL_BZ_WOUND_POISON), uint32(SPELL_BZ_CRIPPLING_POISON) })
                instance->DoRemoveAurasDueToSpellOnPlayers(spell);
        _strike.Stop();
        _next = Finisher::None;
        _clockMs = 0;
        _retryAtMs = 0;
        _strikes = 0;
        _finishers = 0;
        _kicked = 0;
        _fanHits = 0;
        _stepHits = 0;
        _deadly = 0;
        _edge.Reset();
        _arena.Reset();
        _reach.Reset();
        _jump.Reset();
    }

    DungeonKit::ArenaGuard _arena;  // himself on his arena
    DungeonKit::ArenaGuard _reach;  // whom he can reach from it
    JumpGrace _jump;                // ... not asked while the victim jumps
    ArenaEdge _edge;                // ... and how he fights at its edge
    StrikeClock _strike;
    FinisherBag _bag;
    FinisherState _state;
    Finisher _next = Finisher::None;
    std::vector<MechanicHandle> _live;
    uint64 _clockMs = 0;            // ms since the reset: every timer of the fight
    uint64 _retryAtMs = 0;
    uint32 _generation = 0;
    uint32 _strikes = 0;
    uint32 _finishers = 0;
    uint32 _kicked = 0;
    uint32 _fanHits = 0;
    uint32 _stepHits = 0;
    uint32 _deadly = 0;
    bool _heroic = false;
};

// 213610 Sinister Strike: one of his swings (Unit::CalculateDamage of his main hand: the template's weapon damage and
// DamageModifier, so heroic reads the heroic template: half the tier's melee, so a swing and a strike together are one
// swing of the tier, STAGE-D3 Q2 A) plus kStrikeBonus. Set at launch so the target's damage-taken
// modifiers apply; Physical, so armor does too.
class spell_rfc_bazzalan_sinister_strike : public SpellScript
{
    PrepareSpellScript(spell_rfc_bazzalan_sinister_strike);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            SetEffectValue(static_cast<int32>(caster->CalculateDamage(BASE_ATTACK, false, true) + kStrikeBonus));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_rfc_bazzalan_sinister_strike::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 213612 Eviscerate: kEvisceratePctTank of the tank row, whoever holds him.
class spell_rfc_bazzalan_eviscerate : public SpellScript
{
    PrepareSpellScript(spell_rfc_bazzalan_eviscerate);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetCaster())
            SetEffectValue(static_cast<int32>(DungeonKit::RefFlat(caster,
                Tune::kEvisceratePctTank(IsHeroicMap(caster)), true)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_rfc_bazzalan_eviscerate::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

// 213619 Envenom: kEnvenomPctPerStackTank of the tank row per stack of his Deadly Poison on the target, read as it
// lands (a cure during the cast counts) and consumed by the hit.
class spell_rfc_bazzalan_envenom : public SpellScript
{
    PrepareSpellScript(spell_rfc_bazzalan_envenom);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;
        _stacks = DungeonKit::Stacks(target, SPELL_BZ_DEADLY_POISON, caster->GetGUID());
        SetEffectValue(_stacks ? static_cast<int32>(DungeonKit::RefFlat(caster, EnvenomPctTank(_stacks), true)) : 0);
    }

    void Consume()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;
        target->RemoveAurasDueToSpell(SPELL_BZ_DEADLY_POISON, caster->GetGUID());
        DungeonKit::LogMechanic(kLogDungeon, kBossLogName, "envenom-lands",
            Acore::StringFormat("target={} stacks={} pct={:.0f}", target->GetName(), _stacks,
                EnvenomPctTank(_stacks)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_rfc_bazzalan_envenom::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
        AfterHit += SpellHitFn(spell_rfc_bazzalan_envenom::Consume);
    }

    uint32 _stacks = 0;
};

// 213622 Deadly Poison: a tick per stack of kDeadlyFlatPerStack (normal, the stock value) or
// kDeadlyHeroicTankPctPerStack of the tank row (heroic). The engine multiplies the hook's amount by the stacks; the
// per-stack amount is cached for a recalculation without its caster (DungeonKitFlow.h PerStackAmount).
class spell_rfc_bazzalan_deadly_poison : public AuraScript
{
    PrepareAuraScript(spell_rfc_bazzalan_deadly_poison);

    static int32 PerStack(Unit const* ref)
    {
        return IsHeroicMap(ref)
            ? static_cast<int32>(DungeonKit::RefFlat(ref, Tune::kDeadlyHeroicTankPctPerStack, true))
            : static_cast<int32>(Tune::kDeadlyFlatPerStack);
    }

    void CalcAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        std::optional<int32> withCaster;
        std::optional<int32> fromOwner;
        if (Unit* caster = GetCaster())
            withCaster = PerStack(caster);
        else if (Unit* owner = GetUnitOwner())
            fromOwner = PerStack(owner);
        amount = _perStack.Resolve(withCaster, fromOwner);
        canBeRecalculated = true;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_rfc_bazzalan_deadly_poison::CalcAmount, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE);
    }

    DungeonKit::PerStackAmount _perStack;
};

namespace
{
    boss_bazzalan_rework* FindBazzalanAI(ChatHandler* handler)
    {
        Creature* boss = RfcTest::FindBoss(handler, NPC_BAZZALAN);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_bazzalan_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Bazzalan is not running boss_bazzalan_rework (check the ScriptName).");
        return ai;
    }

    bool Report(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Bazzalan: {}", what);
        return true;
    }

    bool FireFinisher(ChatHandler* handler, Finisher f)
    {
        boss_bazzalan_rework* ai = FindBazzalanAI(handler);
        return ai && Report(handler, ai->TestFinisher(f), NameOf(f));
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return RfcTest::ShowBossInfo(handler, NPC_BAZZALAN, BOSS_BAZZALAN);
    }

    bool HandleState(ChatHandler* handler)
    {
        boss_bazzalan_rework* ai = FindBazzalanAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("{}", ai->TestState());
        return true;
    }

    bool HandlePoints(ChatHandler* handler, Optional<uint32> points)
    {
        boss_bazzalan_rework* ai = FindBazzalanAI(handler);
        return ai && Report(handler, ai->TestPoints(std::min<uint32>(points.value_or(Tune::kComboMax),
            Tune::kComboMax)), "points set");
    }

    bool HandlePoison(ChatHandler* handler)
    {
        boss_bazzalan_rework* ai = FindBazzalanAI(handler);
        return ai && Report(handler, ai->TestPoison(), "poison");
    }

    bool HandleEviscerate(ChatHandler* handler) { return FireFinisher(handler, Finisher::Eviscerate); }
    bool HandleRupture(ChatHandler* handler) { return FireFinisher(handler, Finisher::Rupture); }
    bool HandleFan(ChatHandler* handler) { return FireFinisher(handler, Finisher::Fan); }
    bool HandleEnvenom(ChatHandler* handler) { return FireFinisher(handler, Finisher::Envenom); }
    bool HandleShadowstep(ChatHandler* handler) { return FireFinisher(handler, Finisher::Shadowstep); }

    ChatCommandTable const& BazzalanTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,       SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,      SEC_GAMEMASTER, Console::No },
            { "points",     HandlePoints,     SEC_GAMEMASTER, Console::No },
            { "poison",     HandlePoison,     SEC_GAMEMASTER, Console::No },
            { "eviscerate", HandleEviscerate, SEC_GAMEMASTER, Console::No },
            { "rupture",    HandleRupture,    SEC_GAMEMASTER, Console::No },
            { "fan",        HandleFan,        SEC_GAMEMASTER, Console::No },
            { "envenom",    HandleEnvenom,    SEC_GAMEMASTER, Console::No },
            { "shadowstep", HandleShadowstep, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_bazzalan_rework()
{
    RegisterDungeonReworkCreatureAI(boss_bazzalan_rework, RagefireChasmRework::kInstanceScriptName);
    RegisterSpellScript(spell_rfc_bazzalan_sinister_strike);
    RegisterSpellScript(spell_rfc_bazzalan_eviscerate);
    RegisterSpellScript(spell_rfc_bazzalan_envenom);
    RegisterSpellScript(spell_rfc_bazzalan_deadly_poison);
    RfcTest::RegisterBoss("bazzalan", BazzalanTestCommands());
}
