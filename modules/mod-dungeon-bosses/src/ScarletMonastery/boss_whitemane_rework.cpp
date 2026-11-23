/*
 * mod-dungeon-bosses, Scarlet Monastery D14: High Inquisitor Whitemane (3977), with Mograine risen (3976), "Till
 * Death", normal and heroic. Build spec: docs/dungeons/scarlet-monastery-4-cathedral.md "High Inquisitor Whitemane,
 * with Mograine risen" (WM0-WM6, LS5); handoff section 3.5 row D14, section 3.6, section 3.8 row D14, section 7 #33 A
 * (the vigil and the fight on the crossing before the altar: her chamber cannot hold Penance or the Truth). Replaces
 * SmartAI 3977 rows 0-19 and the action lists 397700-397701 (W2-SETUP's rev drops them); bound by apps/dbc-tools
 * source/npcs/scarlet_monastery/whitemane.py. Pure rules: WhitemaneLogic.h. The hard mode (The Truth, WP-D14H) attaches
 * through WhitemaneFight.h; Mograine's risen self is D13's AI, driven through MograineFight.h (no edit of
 * boss_mograine_rework.cpp).
 *
 * One encounter, slot 6 (BOSS_WHITEMANE): her BossAI writes IN_PROGRESS at the pull and DONE at her death (the
 * instance refuses both until the Last Stand is DONE). Her real death always comes last, so the stock credit row 450
 * (her kill) lands after his; the instance records BOSS_THE_TRUTH on a hard mode kill. This file never sends a credit.
 *
 *   WM0  The vigil      the instance's ACTION_SM_WHITEMANE_VIGIL (the Last Stand DONE) or a cold load with the
 *                       Cathedral at the vigil stage: line 3, she comes out of her chamber to kneel at the vigil
 *                       (1146, 1398, 32.1) facing his body (1154, 1398.4, 33.0); passive (no proximity aggro),
 *                       attackable: damage or a hostile cast on her pulls her (rule 10: no free damage window)
 *   WM1  The rising     P + 15 s: Deep Sleep on every player within 100 yd (3 s, damage wakes), she runs to his body,
 *                       line 2 and a 2 s raise (Physical: a Smite kick never locks it); he rises at the finale's
 *                       health (45k / 200k) and says his line 2. R = the Deep Sleep: every risen timer counts from it
 *   WM1a Her save       a lethal hit on him while she stands and has a save left (2 normal, uncapped heroic): he is
 *                       held at 1 health and goes down (MograineFight::Down); line 4, she runs to him, kneels and
 *                       channels 10 s / 8 s (not interruptible; she takes damage as normal); at the end he rises at
 *                       50%. Her lethal hit meanwhile: both die (him first, then her). Her saves spent: his death is
 *                       real and she fights on alone
 *   WM1b His save       a lethal hit on her while he stands and has a save left: she lies as a held body (kit
 *                       HeldBody), he says line 12, comes to her, kneels and channels Lay on Hands 6 s / 5 s; at the
 *                       end she rises at 50%. His lethal hit meanwhile: both die. His saves spent: she lies until he
 *                       dies (he fights on alone), then her death follows his
 *   WM2  To Her Side    R + 20 s, every 25 s, never during a save: his line 13, a 4 yd lane from him to 3 yd beside
 *                       her (2 s marker), 30% / 45% Physical + Weakened (the tank too), then his charge; heroic: for
 *                       6 s after he arrives half the damage she takes goes to him (WM2a). No lane without sight
 *                       (the altar steps) or within 8 yd
 *   WM3  Penance        R + 10 s, every 20 s: 2 / 3 random non-tank players marked (3 s), then a 6 yd pillar on each:
 *                       the marked 20% / 30%, anyone else inside 30% / 45% Holy + Weakened (registry Spread)
 *   WM4  Heal           R + 5 s, every 15 s: a 3 s Holy cast on him, 6% / 20% of his health; interruptible (normal a
 *                       reward, heroic expected). WM4a Power Word: Shield on him every 20 s (R + 8 s): absorbs 5% of
 *                       his health; purgeable
 *   WM5  Vigil Flame    heroic, R + 20 s: a random non-tank carries it; every 10 s it flares for 110% Holy split
 *                       between the carrier and the nearest other player within 6 yd (55% each; unshared 110%; a
 *                       Seared player double), passes to that partner (line 7, raid emote) and Sears the old carrier
 *                       19 s; registry Soak on the carrier, count 1, the unseared others eligible, the tank last
 *                       (SM-BM F7, Ordering::roleLast) plus a no-damage circle that keeps the Seared off it (G2's
 *                       drill)
 *   WM6  Holy Smite     her filler on her target, 2.5 s Holy, 10% / 15%, interruptible, every 4 s when nothing else
 *                       casts (gap 20); she holds her ground within 25 yd of her target
 *   LS5  Divine Storm   his (D13's risen kit), re-paced to R + 12 s, every 15 s
 *   Boss data           kill together by percent of health while both stand; the channeler first in a save window;
 *                       the tank keeps Mograine; Heal (2 / 4) and Holy Smite (1) on the interrupt list; his Power Word:
 *                       Shield on the purge list
 *   Arena               S0's WhitemaneArena (the nave, the crossing, the platform and her chamber), no grips
 *
 * The registry mechanics that must know the fight's tank (the lane, Penance, the flame's tank-last order) are owned by
 * Mograine while he stands (the stub role provider names the owner's victim the tank: his victim is the group's
 * tank); with him down or dead, by her. Every timer runs on the AI's own clock. Cross-unit news from his AI (his
 * lethal hit, his death) is handled at once only to clamp the damage; deaths are queued for her next tick. Every firing
 * logs one INFO line "sm whitemane <mechanic> ..." (module.dungeonbosses); `.dbtest sm whitemane <mechanic>` fires
 * one.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitBodies.h"
#include "InstanceScript.h"
#include "LastStandLogic.h"
#include "Map.h"
#include "MograineFight.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "WhitemaneFight.h"
#include "WhitemaneLogic.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmWhitemane;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;
using SmLastStand::MograineFight;
using SmLastStand::MograineKit;

namespace
{
    char const* const kBoss = "whitemane";

    uint32 constexpr POINT_VIGIL = 1;           // her walk out to the vigil
    uint32 constexpr POINT_RAISE = 2;           // her run to his body (the rising, her save)
    uint32 constexpr POINT_LAY_HANDS = 0x574D01; // his run to her body (his save; on his MovementInform)
    uint32 constexpr POINT_LANE = 0x574D02;     // his charge to her side (WM2)

    Milliseconds Ms(uint64 ms)
    {
        return Milliseconds(static_cast<int64>(ms));
    }

    void LogWm(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // The bots' hard bounds while a mechanic of the fight is in view (WhitemaneLogic.h kFloorBoxes).
    BossMechanics::SpotBounds FloorBounds()
    {
        BossMechanics::SpotBounds bounds;
        float const z = ScarletMonasteryRework::kWhitemaneVigil.z;
        for (Box const& b : kFloorBoxes)
            bounds.Polygon({ Position(b.minX, b.minY, z, 0.f), Position(b.maxX, b.minY, z, 0.f),
                Position(b.maxX, b.maxY, z, 0.f), Position(b.minX, b.maxY, z, 0.f) }, kFloorZMin, kFloorZMax);
        return bounds;
    }

    // `pct` of the reference row (the tank row with `tankRow`) on `target` through one of our script-amount spells.
    void CastPercent(Unit* caster, Unit* target, uint32 spellId, float pct, bool tankRow)
    {
        if (!caster || !target)
            return;
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlat(caster, pct, tankRow)));
        caster->CastSpell(target, spellId, args);
    }

    std::string Names(std::vector<Player*> const& players)
    {
        std::string out;
        for (Player const* p : players)
            out += Acore::StringFormat("{}{}", out.empty() ? "" : ",", p->GetName());
        return out.empty() ? "-" : out;
    }

    char const* UnitName(PairUnit u)
    {
        return u == PairUnit::Whitemane ? "whitemane" : "mograine";
    }

    // The test commands' forced mechanics (`.dbtest sm whitemane ...`).
    enum class TestKind : uint8
    {
        Vigil,
        Rise,
        Lane,
        Penance,
        Heal,
        Shield,
        Smite,
        Flame,
        HisFall,
        HerFall,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// The hooks D14H registers (WhitemaneFight.h)
// ---------------------------------------------------------------------------------------------------------------------
namespace SmWhitemane
{
    namespace
    {
        WhitemaneHardModeFactory& HardModeFactory()
        {
            static WhitemaneHardModeFactory factory;
            return factory;
        }

        WhitemaneIdleHook& IdleHook()
        {
            static WhitemaneIdleHook hook;
            return hook;
        }
    }

    void RegisterWhitemaneHardMode(WhitemaneHardModeFactory factory)
    {
        HardModeFactory() = std::move(factory);
    }

    void RegisterWhitemaneIdleHook(WhitemaneIdleHook hook)
    {
        IdleHook() = std::move(hook);
    }

    bool HasWhitemaneHardMode()
    {
        return static_cast<bool>(HardModeFactory());
    }

    std::unique_ptr<WhitemaneHardMode> CreateWhitemaneHardMode(Creature* whitemane)
    {
        return HardModeFactory() ? HardModeFactory()(whitemane) : nullptr;
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// High Inquisitor Whitemane 3977: the BossAI on slot 6, and the pair's conductor
// ---------------------------------------------------------------------------------------------------------------------
struct boss_whitemane_rework : public BossAI, public WhitemaneFight
{
    explicit boss_whitemane_rework(Creature* creature)
        : BossAI(creature, BOSS_WHITEMANE), _arena(WhitemaneArena(), LeashOptions(kBoss)), _body(BodySpec()) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    // Spawn, respawn and every evade: where the Cathedral's stage puts her (placed on the next idle tick: an evade
    // walks her home to the vigil first).
    void Reset() override
    {
        _Reset();
        if (_state == WhitemaneState::Fight)
            EndFight(false, "reset");
        _body.Reset(me);
        _arena.Reset();
        _placePending = true;
        if (_state != WhitemaneState::Walking)
            me->SetReactState(REACT_PASSIVE);
    }

    void JustEngagedWith(Unit* who) override
    {
        if (_state == WhitemaneState::Chamber && !_testForced)
        {
            // Behind her door before the Last Stand is DONE: never pulled (she is immune to players there).
            LogWm("pull-refused", "the Last Stand is not DONE");
            EnterEvadeMode(EVADE_REASON_OTHER);
            return;
        }
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded
        BeginFight(who);
    }

    // A hostile cast at the vigil that started no combat (a debuff from range): it pulls her too (WM0).
    void AttackedBy(Unit* attacker) override
    {
        if (_state != WhitemaneState::Vigil || !attacker || me->IsEngaged())
            return;
        if (!attacker->GetCharmerOrOwnerPlayerOrPlayerItself())
            return;
        me->EngageWithTarget(attacker);
    }

    void AttackStart(Unit* who) override
    {
        if (!who || _state != WhitemaneState::Fight || Holding() || _body.Fallen())
            return;
        if (me->Attack(who, true))
            me->GetMotionMaster()->MoveChase(who, ChaseRange(0.f, kChaseRangeYd));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_state == WhitemaneState::Fight)
            EndFight(false, Acore::StringFormat("evade reason={}", uint32(why)).c_str());
        _body.Reset(me);
        _arena.Reset();
        BossAI::EnterEvadeMode(why);
    }

    void JustReachedHome() override
    {
        BossAI::JustReachedHome();
        _placePending = false;
        PlaceForStage(false, "home");
    }

    // Her summons (the hard mode's light stalker, the vigil Fairbanks) join no fight by themselves (no zone combat):
    // the hard mode calls JoinFight for the ones that fight.
    void JustSummoned(Creature* summon) override
    {
        summons.Summon(summon);
    }

    // Her death is the encounter's (slot 6 DONE, the credit row 450): it always comes after his. The hard mode's OnEnd
    // runs first (EndFight), while its summons still stand (the spirit speaks over the pair), then BossAI's DONE.
    void JustDied(Unit* killer) override
    {
        _arena.Reset();
        bool const pair = _stage != PairStage::Alone;
        // A GM kill (or any death) while he still stands: he follows her (his quests credit his real death).
        if (Creature* m = MograineCreature())
            if (m->IsAlive())
            {
                if (MograineFight* f = MograineAI(); f && f->State() == SmLastStand::MograineState::Risen)
                    f->KillForGood(killer);
            }
        if (pair)
            Talk(SAY_WHITEMANE_TOGETHER);
        LogWm("death", Acore::StringFormat("killer={} stage={} saves={}/{}", killer ? killer->GetName() : "none",
            StageName(_stage), _herSaves, _hisSaves));
        if (_state == WhitemaneState::Fight)
            EndFight(true, "death");
        _state = WhitemaneState::Dead;
        BossAI::JustDied(killer);
    }

    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer() || _clockMs < _killLineReadyMs)
            return;
        _killLineReadyMs = _clockMs + kKillLineCooldownMs;
        Talk(SAY_WHITEMANE_KILL, victim);
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        if (_state != WhitemaneState::Fight)
            return;
        if (_hardMode)
            _hardMode->OnDamageTaken(*this, PairUnit::Whitemane, attacker, damage);
        if (_body.Fallen())
        {
            _body.Intercept(me, damage);
            return;
        }
        // WM2a (heroic): half of it goes to him while he shields her; dealt on the next tick (never inside this chain).
        if (damage && _clockMs < _bodyShieldUntil && MograineUp() && attacker)
        {
            uint32 const share = static_cast<uint32>(static_cast<float>(damage) * kBodyShieldShare);
            damage -= share;
            _shieldDebt += share;
            _shieldDebtFrom = attacker->GetGUID();
        }
        if (damage < me->GetHealth())
            return;
        Lethal const answer = OnHerLethal(_stage, _hisSaves, SaveCap(), MograineUp());
        LogWm("her-lethal", Acore::StringFormat("stage={} answer={} saves={}", StageName(_stage), LethalName(answer),
            _hisSaves));
        switch (answer)
        {
            case Lethal::Through:
                return;
            case Lethal::Save:
                _body.Intercept(me, damage);
                StartHisSave();
                return;
            case Lethal::Spent:
                _body.Intercept(me, damage);
                if (_stage == PairStage::Pair)
                    BecomeSpent();
                return;
            case Lethal::PairDeath:
                _body.Intercept(me, damage);
                QueuePairDeath(attacker, "her-fall");
                return;
        }
    }

    void DoAction(int32 action) override
    {
        if (action != ACTION_SM_WHITEMANE_VIGIL)
            return;
        if (_state == WhitemaneState::Chamber || _state == WhitemaneState::Vigil)
            WalkToVigil(true, "last-stand-done");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE)
            return;
        if (id == POINT_VIGIL && _state == WhitemaneState::Walking)
            ArriveAtVigil("arrived");
        else if (id == POINT_RAISE && _state == WhitemaneState::Fight)
        {
            if (_stage == PairStage::Rising && _rise == RiseStep::Run)
                BeginRaiseCast("arrived");
            else if (_save.active && _save.fallen == PairUnit::Mograine && !_save.channeling)
                StartChannel("arrived");
        }
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (!spell || _state != WhitemaneState::Fight)
            return;
        switch (spell->Id)
        {
            case SPELL_WM_RAISE:
                if (_stage == PairStage::Rising)
                    RaiseNow("cast");
                break;
            case SPELL_WM_HOLY_SMITE:
            case SPELL_WM_HEAL:
                _nextSmite = _clockMs + kSmiteGapMs;
                break;
            default:
                break;
        }
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell || _state != WhitemaneState::Fight)
            return;
        switch (spell->Id)
        {
            case SPELL_WM_RAISE:
                if (_stage == PairStage::Rising && _rise == RiseStep::Cast)
                    _rise = RiseStep::Retry;
                break;
            case SPELL_WM_HEAL:
                LogWm(_selfBreak ? "heal-broken" : "heal-kicked", _heroic ? "expected" : "reward");
                _nextSmite = _clockMs + kSmiteGapMs;
                break;
            case SPELL_WM_HOLY_SMITE:
                LogWm(_selfBreak ? "smite-broken" : "smite-kicked", "reward");
                _nextSmite = _clockMs + kSmiteGapMs;
                break;
            default:
                break;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!me->IsAlive())
            return;
        if (_state != WhitemaneState::Fight)
        {
            UpdateIdle();
            return;
        }
        if (_hardMode)
            _hardMode->OnUpdate(*this, diff);
        FlushQueued();
        if (_state != WhitemaneState::Fight || !me->IsAlive())
            return;
        bool const body = _body.Fallen();
        if (body)
        {
            _body.Update(me, diff);
            if (!WipeWatch(diff))
                return;
        }
        else
        {
            if (!UpdateVictim())
                return;
            if (!_arena.Update(me, diff))
                return;     // off her arena, or nobody on it for 10 s: evading
        }
        UpdateRising();
        UpdateSave();
        UpdateLane();
        UpdateFlame();
        if (body || Holding())
            return;
        UpdateInstants();   // triggered: never wait for a cast
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        UpdateCasts();
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // From Mograine's AI (WhitemaneRisen below; MograineFight.h hook order)
    // ----------------------------------------------------------------------------------------------------------------

    // WM1: he stood up from his body (the rising).
    void OnMograineRise(MograineFight& f, bool first)
    {
        if (_state != WhitemaneState::Fight)
            return;
        f.Say(SAY_MOGRAINE_AT_YOUR_SIDE);
        if (Creature* m = f.Mograine())
            m->CastSpell(m, SPELL_WM_RISE_LOOK, true);
        uint64 const r = _risingAt ? _risingAt : _clockMs;
        _risingAt = r;
        _stage = PairStage::Pair;
        _rise = RiseStep::Done;
        _nextHeal = r + kHealFirstMs;
        _nextShield = r + kShieldFirstMs;
        _nextPenance = r + kPenanceFirstMs;
        _nextLane = r + kLaneFirstMs;
        _nextFlame = _heroic ? r + kFlameFirstMs : 0;
        uint64 const stormAt = r + kStormFromRisingMs;
        f.SetCadence(MograineKit::DivineStorm, stormAt > _clockMs ? static_cast<uint32>(stormAt - _clockMs) : 0,
            kStormEveryMs);
        ReleaseHold("risen");
        Describe();
        if (Creature* m = f.Mograine())
            Mechanic::TrackUnit(me, m);
        if (_hardMode)
            _hardMode->OnRise(*this, true);
        LogWm("risen", Acore::StringFormat("max={} first={} r+{}ms", f.Mograine() ? f.Mograine()->GetMaxHealth() : 0,
            first ? 1 : 0, _clockMs - r));
    }

    // His damage (MograineRisen::OnDamageTaken; D13 zeroes it while he is down).
    void OnMograineDamage(MograineFight& f, Unit* attacker, uint32& damage)
    {
        if (_state != WhitemaneState::Fight)
            return;
        if (_hardMode)
            _hardMode->OnDamageTaken(*this, PairUnit::Mograine, attacker, damage);
        Creature* m = f.Mograine();
        if (!m || damage == 0 || damage < m->GetHealth())
            return;
        Lethal const answer = OnHisLethal(_stage, _herSaves, SaveCap());
        LogWm("his-lethal", Acore::StringFormat("stage={} answer={} saves={}", StageName(_stage), LethalName(answer),
            _herSaves));
        switch (answer)
        {
            case Lethal::Save:
                damage = m->GetHealth() > 1 ? m->GetHealth() - 1 : 0;
                if (_stage == PairStage::Pair)
                    StartHerSave(f);
                return;
            case Lethal::PairDeath:
                _pairDeathKiller = attacker ? attacker->GetGUID() : ObjectGuid::Empty;
                return;     // his death goes through; OnMograineDied queues hers
            case Lethal::Through:
            case Lethal::Spent:
                return;
        }
    }

    // His real death (MograineRisen::OnDied).
    void OnMograineDied(MograineFight& /*f*/, Unit* killer)
    {
        if (_state != WhitemaneState::Fight)
            return;
        CancelLane("his-death");
        if (_pairDeathQueued)
            return;     // the pair's death in progress: hers follows on its own
        if (HisDeathEndsHer(_stage))
        {
            QueuePairDeath(killer, "his-death");
            return;
        }
        if (_stage == PairStage::Pair)
        {
            _stage = PairStage::HisDead;
            ClearFlame("his-death");
            Describe();
            LogWm("vow-spent", Acore::StringFormat("he dies (her saves {} spent); she fights on alone", _herSaves));
        }
    }

    // His rising ended (MograineRisen::OnEnd): his death, his walk back to his body, the stand's reset.
    void OnMograineEnd(MograineFight& f, bool died)
    {
        if (Creature* m = f.Mograine())
        {
            m->RemoveAurasDueToSpell(SPELL_WM_POWER_WORD_SHIELD);
            m->RemoveAurasDueToSpell(SPELL_WM_BODY_SHIELD);
            m->RemoveAurasDueToSpell(SPELL_WM_LAY_ON_HANDS);
        }
        if (!died && _state == WhitemaneState::Fight && !_ending)
            LogWm("mograine-gone", "his rising ended while she fights (his own evade)");
    }

    // His evade while risen (MograineRisen::OnEvade): true keeps him (she runs the fight and its wipe).
    bool KeepsMograine() const
    {
        return _state == WhitemaneState::Fight && !_ending && me->IsAlive() && me->IsInCombat();
    }

    void OnMograineMovement(MograineFight& f, uint32 /*type*/, uint32 id)
    {
        if (_state != WhitemaneState::Fight)
            return;
        if (id == POINT_LANE && _lane.active && _lane.charging)
            LaneArrived(f, "arrived");
        else if (id == POINT_LAY_HANDS && _save.active && _save.fallen == PairUnit::Whitemane && !_save.channeling)
            StartChannel("arrived");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WhitemaneFight (D14H's hard mode)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Whitemane() override { return me; }

    Creature* Mograine() override { return MograineCreature(); }

    MograineFight* MograineAI() override
    {
        return SmLastStand::MograineFightOf(MograineCreature());
    }

    bool Heroic() const override { return _heroic; }
    WhitemaneState State() const override { return _state; }
    PairStage Stage() const override { return _stage; }
    WhitemaneHardMode* ActiveHardMode() override { return _hardMode.get(); }
    uint64 FightMs() const override { return _state == WhitemaneState::Fight ? _clockMs - _pullAt : 0; }
    uint64 RisingMs() const override { return _risingAt ? _clockMs - _risingAt : 0; }
    bool SaveInProgress() const override { return _save.active; }
    bool LaneInProgress() const override { return _lane.active; }

    Creature* LowerOfPair() override
    {
        bool const herUp = me->IsAlive() && !_body.Fallen();
        Creature* m = MograineUp() ? MograineCreature() : nullptr;
        if (!herUp)
            return m;
        if (!m)
            return me;
        return m->GetHealthPct() < me->GetHealthPct() ? m : me;
    }

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

    bool IsTank(Player const* player) override
    {
        if (!player)
            return false;
        return BossMechanics::GetRoleProvider().Get(MechanicOwner(), player) == BossMechanics::Role::Tank;
    }

    void StartFight(Unit* who, char const* why) override
    {
        if (_state == WhitemaneState::Fight || !who)
            return;
        LogWm("start-fight", why);
        me->EngageWithTarget(who);
    }

    void BreakCast(char const* why) override
    {
        if (_save.active && _save.channeling)
        {
            // HM3a: the save starts over (its window again from now).
            _save.endsAt = _clockMs + _save.windowMs;
            if (_save.fallen == PairUnit::Whitemane)
                if (MograineFight* f = MograineAI())
                    f->HoldControl(f->RisenMs() + _save.windowMs + 5000);
            LogWm("save-restarted", Acore::StringFormat("why={} fallen={} window={}ms", why, UnitName(_save.fallen),
                _save.windowMs));
            return;
        }
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            return;
        StopMyCast();
        LogWm("cast-broken", why);
    }

    void HoldMechanics(bool hold, char const* why) override
    {
        if (_kitHeld == hold)
            return;
        _kitHeld = hold;
        LogWm(hold ? "mechanics-held" : "mechanics-released", why);
        if (!hold)
            RefreshFlameAfterHold(why);
    }

    bool MechanicsHeld() const override { return _kitHeld; }

    void RestartTimer(WhitemaneTimer timer, uint32 inMs) override
    {
        uint64 const at = _clockMs + inMs;
        switch (timer)
        {
            case WhitemaneTimer::ToHerSide:  _nextLane = at; break;
            case WhitemaneTimer::Penance:    _nextPenance = at; break;
            case WhitemaneTimer::Heal:       _nextHeal = at; break;
            case WhitemaneTimer::Shield:     _nextShield = at; break;
            case WhitemaneTimer::VigilFlame: if (_heroic) _nextFlame = at; break;
            case WhitemaneTimer::Smite:      _nextSmite = at; break;
        }
    }

    Creature* Summon(uint32 entry, Position const& at, uint32 despawnMs) override
    {
        return me->SummonCreature(entry, at, despawnMs ? TEMPSUMMON_TIMED_DESPAWN : TEMPSUMMON_MANUAL_DESPAWN,
            despawnMs);
    }

    void JoinFight(Creature* unit, bool keep) override
    {
        if (!unit)
            return;
        for (Player* p : FightPlayers())
            if (unit->IsValidAttackTarget(p))
                unit->AddThreat(p, 0.f);
        Mechanic::TrackUnit(me, unit);
        if (!keep)
            _joined.push_back(unit->GetGUID());
    }

    void Track(MechanicHandle handle) override
    {
        if (handle)
            _handles.push_back({ me->GetGUID(), handle });
    }

    void RefreshDescriptor() override { Describe(); }

    void Say(uint8 group, WorldObject const* target) override { Talk(group, target); }

    void Log(char const* mechanic, std::string const& detail) override { LogWm(mechanic, detail); }

private:
    enum class RiseStep : uint8
    {
        None,
        Run,
        Cast,
        Retry,
        Waiting,    // the raise is cast; he is not lying at his body yet (a quick re-pull): Rise again each tick
        Done,
    };

    struct Save
    {
        bool active = false;
        PairUnit fallen = PairUnit::Mograine;
        bool channeling = false;
        uint32 windowMs = 0;
        uint64 runGiveUpAt = 0;
        uint64 endsAt = 0;
    };

    struct Lane
    {
        bool active = false;
        bool charging = false;
        uint64 chargeAt = 0;
        uint64 giveUpAt = 0;
        Position arrival;
        MechanicHandle handle;
        ObjectGuid owner;
    };

    struct OwnedHandle
    {
        ObjectGuid owner;
        MechanicHandle handle;
    };

    static DungeonKit::HeldBodySpec BodySpec()
    {
        DungeonKit::HeldBodySpec spec;
        spec.holds = 255;               // D14 decides each fall (WhitemaneLogic.h OnHerLethal)
        spec.revivePct = kSaveReturnPct;
        spec.dungeon = kLogDungeon;
        spec.boss = kBoss;
        return spec;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Small helpers
    // ----------------------------------------------------------------------------------------------------------------

    Creature* MograineCreature() const
    {
        return instance ? ObjectAccessor::GetCreature(*me, instance->GetGuidData(DATA_MOGRAINE)) : nullptr;
    }

    // His spawn id (stock guid 40029): the live object's when there is one (cached), else his creature row on this map.
    ObjectGuid::LowType MograineSpawnId()
    {
        if (Creature* m = MograineCreature())
            if (m->GetSpawnId())
                _mograineSpawnId = m->GetSpawnId();
        if (!_mograineSpawnId)
            for (auto const& [spawnId, data] : sObjectMgr->GetAllCreatureData())
                if (data.id == NPC_MOGRAINE && data.mapid == me->GetMapId())
                {
                    _mograineSpawnId = spawnId;
                    break;
                }
        return _mograineSpawnId;
    }

    // He stands in the finale: alive, risen, not down.
    bool MograineUp() const
    {
        Creature* m = MograineCreature();
        if (!m || !m->IsAlive())
            return false;
        MograineFight* f = SmLastStand::MograineFightOf(m);
        return f && f->State() == SmLastStand::MograineState::Risen && !f->IsDown();
    }

    uint8 SaveCap() const { return kSaveCap(_heroic); }

    bool Due(uint64 at) const { return at != 0 && _clockMs >= at; }

    // Her own holds: the rising, her save (she is passive, the chase off).
    bool Holding() const
    {
        return _stage == PairStage::Rising || (_save.active && _save.fallen == PairUnit::Mograine);
    }

    // The registry owner whose victim is the fight's tank: Mograine while he is risen and alive, down in her save
    // included (the role provider then finds the real tank, not her top-threat player); her once he is gone.
    Unit* MechanicOwner()
    {
        Creature* m = MograineCreature();
        MograineFight* f = MograineAI();
        if (m && MograineOwnsMechanics(m->IsAlive(), f && f->State() == SmLastStand::MograineState::Risen))
            return m;
        return me;
    }

    // Who voices the flame and the pillars' script hits: her while she stands, else him.
    Unit* HitCaster()
    {
        if (!_body.Fallen())
            return me;
        Creature* m = MograineCreature();
        return m && m->IsAlive() ? static_cast<Unit*>(m) : me;
    }

    uint32 SaveWindow(PairUnit fallen) const
    {
        std::optional<uint32> const custom = _hardMode ? _hardMode->SaveWindowMs(*this, fallen) : std::nullopt;
        if (custom)
            return *custom;
        return fallen == PairUnit::Mograine ? kHerSaveMs(_heroic) : kHisSaveMs(_heroic);
    }

    uint32 LaneEvery() const
    {
        std::optional<uint32> const custom = _hardMode ? _hardMode->ToHerSideEveryMs(*this) : std::nullopt;
        return custom ? *custom : kLaneEveryMs;
    }

    uint32 FlameEvery() const
    {
        std::optional<uint32> const custom = _hardMode ? _hardMode->FlameEveryMs(*this) : std::nullopt;
        return custom ? *custom : kFlameEveryMs;
    }

    uint32 SearedFor() const
    {
        std::optional<uint32> const custom = _hardMode ? _hardMode->SearedMs(*this) : std::nullopt;
        return custom ? *custom : kSearedMs;
    }

    // His hold ends: D13 re-attacks his victim on its next tick (MograineFight::HoldControl).
    static void ReleaseMograine(MograineFight& f)
    {
        f.HoldControl(f.RisenMs() + 1);
    }

    // Her own cast stops (not a kick: no "kicked" line).
    void StopMyCast()
    {
        _selfBreak = true;
        me->InterruptNonMeleeSpells(false);
        _selfBreak = false;
    }

    void Cancel(OwnedHandle& h)
    {
        if (!h.handle)
            return;
        if (Unit* owner = ObjectAccessor::GetUnit(*me, h.owner))
            Mechanic::Cancel(owner, h.handle);
        h = {};
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WM0: the chamber, the walk out, the vigil
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateIdle()
    {
        if (_placePending && !me->IsInEvadeMode())
        {
            _placePending = false;
            PlaceForStage(false, "reset");
        }
        if (_state == WhitemaneState::Walking && _clockMs >= _walkGiveUpAt)
        {
            Point4 const v = VigilSpot();
            me->NearTeleportTo(v.x, v.y, v.z, v.o);
            ArriveAtVigil("teleported");
        }
        if (IdleHook() && !me->IsEngaged())
            IdleHook()(*this);
    }

    void PlaceForStage(bool yell, char const* why)
    {
        if (_state == WhitemaneState::Fight || !me->IsAlive())
            return;
        CathedralStage const stage = instance ? static_cast<CathedralStage>(instance->GetData(DATA_CATHEDRAL_STAGE))
            : CathedralStage::BeforeStand;
        if (!AtVigilForStage(stage))
        {
            BecomeChamber(why);
            return;
        }
        Point4 const v = VigilSpot();
        if (me->GetExactDist2d(v.x, v.y) <= 3.f)
            ArriveAtVigil(why);
        else if (_state != WhitemaneState::Walking)
            WalkToVigil(yell, why);
    }

    void BecomeChamber(char const* why)
    {
        _state = WhitemaneState::Chamber;
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToPC(true);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        LogWm("chamber", why);
    }

    void WalkToVigil(bool yell, char const* why)
    {
        _state = WhitemaneState::Walking;
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToPC(false);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        if (yell)
            Talk(SAY_WHITEMANE_FALLEN);
        Point4 const v = VigilSpot();
        _walkGiveUpAt = _clockMs + kVigilWalkGiveUpMs;
        me->SetWalk(false);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_VIGIL, v.x, v.y, v.z);
        LogWm("to-vigil", Acore::StringFormat("why={} yell={}", why, yell ? 1 : 0));
    }

    void ArriveAtVigil(char const* why)
    {
        Point4 const v = VigilSpot();
        _state = WhitemaneState::Vigil;
        me->StopMoving();
        me->SetHomePosition(v.x, v.y, v.z, v.o);
        me->SetFacingTo(v.o);
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToPC(false);
        me->SetStandState(UNIT_STAND_STATE_KNEEL);
        LogWm("vigil", Acore::StringFormat("why={} at=({:.1f}, {:.1f})", why, me->GetPositionX(),
            me->GetPositionY()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pull and the end of an attempt
    // ----------------------------------------------------------------------------------------------------------------

    void BeginFight(Unit* who)
    {
        _state = WhitemaneState::Fight;
        _stage = PairStage::Alone;
        _rise = RiseStep::None;
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _pullAt = _clockMs;
        _risingAt = 0;
        _herSaves = 0;
        _hisSaves = 0;
        _save = {};
        _lane = {};
        _kitHeld = false;
        _pairDeathQueued = false;
        _pairDeathKiller.Clear();
        _bodyShieldUntil = 0;
        _shieldDebt = 0;
        _nextSmite = _clockMs + kSmiteFirstMs;
        _nextHeal = _nextShield = _nextPenance = _nextLane = _nextFlame = 0;
        _riseAt = _clockMs + kRisingAtMs;
        _flameCarrier.Clear();
        me->SetStandState(UNIT_STAND_STATE_STAND);
        me->SetReactState(REACT_AGGRESSIVE);

        bool const hardMode = _heroic && instance && instance->GetData(DATA_HARD_MODE_WHITEMANE) != 0;
        if (hardMode)
        {
            _hardMode = CreateWhitemaneHardMode(me);
            if (!_hardMode)
                LogWm("hardmode-no-hooks", "the Torch is lit but no WhitemaneHardMode factory is registered");
        }
        OnBossPull(me, kBoss, hardMode);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_WHITEMANE;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        Describe();
        if (_hardMode)
            _hardMode->OnEngage(*this);
        AttackStart(who);
        LogWm("engage", Acore::StringFormat("heroic={} hardmode={} saves-cap={} rising-at=P+{}s", _heroic ? 1 : 0,
            hardMode ? 1 : 0, SaveCap(), kRisingAtMs / 1000));
    }

    // Every way an attempt ends (death `died`, evade, reset): her looks and his, every handle and mark, the hard mode.
    void EndFight(bool died, char const* why)
    {
        if (_ending)
            return;
        _ending = true;
        if (_hardMode)
        {
            _hardMode->OnEnd(*this, died);
            _hardMode.reset();
        }
        CancelLane(why);
        ClearFlame(why);
        for (OwnedHandle& h : _handles)
            Cancel(h);
        _handles.clear();
        Cancel(_penance);
        ClearPlayerAuras();
        for (ObjectGuid const& guid : _joined)
            if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
                unit->DespawnOrUnsummon();
        _joined.clear();
        me->RemoveAurasDueToSpell(SPELL_WM_RESURRECTION);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        if (!died)
        {
            // A wipe returns him to his body (the Last Stand stays DONE); dead for good (her saves spent), he is
            // respawned: his Reset reads the Vigil stage and lies him at his body for the next pull's rising.
            // With his dead object gone (dynamic respawn mode: corpse decayed, or looted 30 s ago) the respawn goes
            // by spawn id; the queue skips it if a live Mograine already stands.
            Creature* const mograine = MograineCreature();
            switch (MograineRespawnRoute(died, mograine != nullptr, mograine && mograine->IsAlive()))
            {
                case MograineRespawn::Object:
                    mograine->Respawn(true);
                    LogWm("mograine-respawned", why);
                    break;
                case MograineRespawn::SpawnId:
                    if (ObjectGuid::LowType const spawnId = MograineSpawnId())
                    {
                        me->GetMap()->ForceCreatureRespawn(spawnId);
                        LogWm("mograine-respawned", Acore::StringFormat("{} spawn={}", why, spawnId));
                    }
                    else
                        LogWm("mograine-respawn-failed", Acore::StringFormat("{} no spawn row", why));
                    break;
                case MograineRespawn::None:
                    break;
            }
            if (MograineFight* f = MograineAI())
                if (f->State() == SmLastStand::MograineState::Risen)
                {
                    if (f->IsDown())
                        f->GetUp(100.f, "wipe");
                    f->BackToBody("whitemane-wipe");
                }
            if (Creature* m = MograineCreature())
                if (m->IsAlive())
                    m->SetStandState(UNIT_STAND_STATE_STAND);
            Mechanic::EndEncounter(me);
        }
        _save = {};
        _stage = PairStage::Over;
        _rise = RiseStep::None;
        _nextSmite = _nextHeal = _nextShield = _nextPenance = _nextLane = _nextFlame = _riseAt = 0;
        _kitHeld = false;
        _shieldDebt = 0;
        _bodyShieldUntil = 0;
        _state = died ? WhitemaneState::Dead : WhitemaneState::Vigil;
        LogWm("end", Acore::StringFormat("why={} died={} saves={}/{}", why, died ? 1 : 0, _herSaves, _hisSaves));
        _ending = false;
    }

    void ClearPlayerAuras()
    {
        Map* map = me->GetMap();
        if (!map)
            return;
        for (auto const& ref : map->GetPlayers())
            if (Player* p = ref.GetSource())
            {
                p->RemoveAurasDueToSpell(SPELL_WM_VIGIL_FLAME);
                p->RemoveAurasDueToSpell(SPELL_WM_SEARED);
                p->RemoveAurasDueToSpell(SPELL_WM_PENANCE_MARK);
                p->RemoveAurasDueToSpell(SPELL_WM_DEEP_SLEEP);
            }
    }

    // A held body never calls UpdateVictim: the wipe is nobody alive on her floor for 3 s.
    bool WipeWatch(uint32 diff)
    {
        bool anyone = false;
        if (Map* map = me->GetMap())
            for (auto const& ref : map->GetPlayers())
            {
                Player* p = ref.GetSource();
                if (CountsAsPlayer(p) && WhitemaneArena().Contains(PlaneOf(p), p->GetPositionZ()))
                {
                    anyone = true;
                    break;
                }
            }
        if (anyone)
        {
            _wipeMs = 0;
            return true;
        }
        _wipeMs += diff;
        if (_wipeMs < kWipeWatchMs)
            return true;
        _wipeMs = 0;
        LogWm("wipe", "nobody alive on her floor while she lies");
        EnterEvadeMode(EVADE_REASON_NO_HOSTILES);
        return false;
    }

    static Vec2 PlaneOf(WorldObject const* o)
    {
        return { o->GetPositionX(), o->GetPositionY() };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The descriptor (boss data)
    // ----------------------------------------------------------------------------------------------------------------

    void Describe()
    {
        if (_state != WhitemaneState::Fight || !me->IsAlive())
            return;
        KillOrder const order = KillOrderFor(_stage);
        BossMechanics::Descriptor d;
        bool const sheCasts = !_body.Fallen() && _stage != PairStage::Over;
        if (sheCasts)
        {
            d.interrupts.emplace_back(NPC_WHITEMANE, SPELL_WM_HEAL, kHealKickPriority(_heroic), Ms(kHealEveryMs));
            d.interrupts.emplace_back(NPC_WHITEMANE, SPELL_WM_HOLY_SMITE, kSmiteKickPriority);
        }
        if (_stage != PairStage::HisDead)
            d.purges.emplace_back(NPC_MOGRAINE, SPELL_WM_POWER_WORD_SHIELD, kShieldPurgePriority);
        if (order.together)
        {
            d.targets.push_back(BossMechanics::TargetEntry(NPC_WHITEMANE, 1).KillTogether(NPC_MOGRAINE,
                kKillTogetherPct));
            d.targets.push_back(BossMechanics::TargetEntry(NPC_MOGRAINE, 1).KillTogether(NPC_WHITEMANE,
                kKillTogetherPct));
        }
        else
        {
            if (order.whitemane)
                d.targets.emplace_back(NPC_WHITEMANE, 2);
            if (order.mograine)
                d.targets.emplace_back(NPC_MOGRAINE, 2);
        }
        if (order.tankOnMograine)
            d.targets.emplace_back(NPC_MOGRAINE, 3, BossMechanics::Who::Tank);
        if (_hardMode)
            _hardMode->ConfigureDescriptor(*this, d);
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WM1 the rising
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateRising()
    {
        if (_stage == PairStage::Alone && Due(_riseAt) && !_kitHeld)
        {
            StartRising("timer");
            return;
        }
        if (_stage != PairStage::Rising)
            return;
        if (_rise == RiseStep::Run && _clockMs >= _riseRunGiveUpAt)
            BeginRaiseCast("run-give-up");
        else if (_rise == RiseStep::Retry && !me->HasUnitState(UNIT_STATE_CASTING))
            BeginRaiseCast("retry");
        else if (_rise == RiseStep::Waiting)
            RaiseNow("waiting");
        if (_stage == PairStage::Rising && _rise != RiseStep::Waiting && _clockMs >= _risingAt + kRaiseGiveUpMs)
            RaiseNow("give-up");
    }

    void StartRising(char const* why)
    {
        Creature* m = MograineCreature();
        _stage = PairStage::Rising;
        _risingAt = _clockMs;
        _riseAt = 0;
        StopMyCast();
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->CastSpell(me, SPELL_WM_DEEP_SLEEP, true);
        _rise = RiseStep::Run;
        _riseRunGiveUpAt = _clockMs + kRaiseRunGiveUpMs;
        Describe();
        LogWm("rising", Acore::StringFormat("why={} deep-sleep={}ms mograine={}", why, kDeepSleepMs,
            m ? "found" : "missing"));
        if (!m)
            return;
        Vec2 const spot = ShortOf(PlaneOf(me), PlaneOf(m), kRaiseStandoffYd);
        if (me->GetExactDist2d(m) <= kRaiseStandoffYd + 1.f)
        {
            BeginRaiseCast("beside");
            return;
        }
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_RAISE, spot.x, spot.y, m->GetPositionZ());
    }

    void BeginRaiseCast(char const* why)
    {
        if (_stage != PairStage::Rising)
            return;
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        if (Creature* m = MograineCreature())
            me->SetFacingToObject(m);
        if (_rise != RiseStep::Retry)
            Talk(SAY_WHITEMANE_ARISE);
        _rise = RiseStep::Cast;
        if (me->CastSpell(me, SPELL_WM_RAISE, false) != SPELL_CAST_OK)
            _rise = RiseStep::Retry;
        LogWm("raise", why);
    }

    void RaiseNow(char const* why)
    {
        if (_stage != PairStage::Rising)
            return;
        MograineFight* f = MograineAI();
        std::optional<uint32> const custom = _hardMode ? _hardMode->RisenMaxHealth(*this) : std::nullopt;
        uint32 const maxHealth = custom ? *custom : kMograineRisenHealth(_heroic);
        if (!f || !f->Rise(maxHealth, 100.f, why))
        {
            if (_clockMs < _risingAt + kRaiseGiveUpMs + kRaiseGiveUpMs)
            {
                _rise = RiseStep::Waiting;
                return;     // he is still walking back to his body (a quick re-pull): again next tick
            }
            // Nobody to raise (wave 2 unbound, a stock Mograine): she fights on alone.
            _stage = PairStage::HisDead;
            _rise = RiseStep::Done;
            ReleaseHold("no-mograine");
            Describe();
            LogWm("rise-failed", "no risen Mograine: she fights alone");
        }
        // OnMograineRise (from Rise) armed the timeline.
    }

    void ReleaseHold(char const* why)
    {
        if (_body.Fallen() || !me->IsAlive())
            return;
        me->SetStandState(UNIT_STAND_STATE_STAND);
        me->SetReactState(REACT_AGGRESSIVE);
        if (Unit* victim = me->SelectVictim())
            AttackStart(victim);
        if (_nextSmite < _clockMs + kRetryMs)
            _nextSmite = _clockMs + kRetryMs;
        LogWm("hold-released", why);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WM1a / WM1b the saves
    // ----------------------------------------------------------------------------------------------------------------

    // WM1a: he fell; she runs to him and channels.
    void StartHerSave(MograineFight& f)
    {
        _stage = PairStage::HerSave;
        ++_herSaves;
        CancelLane("her-save");
        f.Down("her-save");
        StopMyCast();
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        Talk(SAY_WHITEMANE_NOT_YET);
        _save = {};
        _save.active = true;
        _save.fallen = PairUnit::Mograine;
        _save.windowMs = SaveWindow(PairUnit::Mograine);
        _save.runGiveUpAt = _clockMs + kSaveRunGiveUpMs;
        Describe();
        if (_hardMode)
            _hardMode->OnSaveStart(*this, PairUnit::Mograine, _save.windowMs);
        LogWm("her-save", Acore::StringFormat("save={}/{} window={}ms", _herSaves, SaveCap(), _save.windowMs));
        Creature* m = f.Mograine();
        if (!m || me->GetExactDist2d(m) <= kSaveStandoffYd + 1.f)
        {
            StartChannel("beside");
            return;
        }
        Vec2 const spot = ShortOf(PlaneOf(me), PlaneOf(m), kSaveStandoffYd);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_RAISE, spot.x, spot.y, m->GetPositionZ());
    }

    // WM1b: she fell (a held body); he comes to her and lays hands on her.
    void StartHisSave()
    {
        _stage = PairStage::HisSave;
        ++_hisSaves;
        CancelLane("his-save");
        _bodyShieldUntil = 0;
        _save = {};
        _save.active = true;
        _save.fallen = PairUnit::Whitemane;
        _save.windowMs = SaveWindow(PairUnit::Whitemane);
        _save.runGiveUpAt = _clockMs + kSaveRunGiveUpMs;
        Describe();
        if (_hardMode)
            _hardMode->OnSaveStart(*this, PairUnit::Whitemane, _save.windowMs);
        LogWm("his-save", Acore::StringFormat("save={}/{} window={}ms", _hisSaves, SaveCap(), _save.windowMs));
        MograineFight* f = MograineAI();
        Creature* m = f ? f->Mograine() : nullptr;
        if (!f || !m)
            return;
        f->Say(SAY_MOGRAINE_NOT_WHILE);
        f->HoldControl(f->RisenMs() + kSaveRunGiveUpMs + _save.windowMs + 5000);
        m->InterruptNonMeleeSpells(false);
        m->AttackStop();
        m->StopMoving();
        m->GetMotionMaster()->Clear();
        if (m->GetExactDist2d(me) <= kSaveStandoffYd + 1.f)
        {
            StartChannel("beside");
            return;
        }
        Vec2 const spot = ShortOf(PlaneOf(m), PlaneOf(me), kSaveStandoffYd);
        m->GetMotionMaster()->MovePoint(POINT_LAY_HANDS, spot.x, spot.y, me->GetPositionZ());
    }

    void StartChannel(char const* why)
    {
        if (!_save.active || _save.channeling)
            return;
        _save.channeling = true;
        _save.endsAt = _clockMs + _save.windowMs;
        if (_save.fallen == PairUnit::Mograine)
        {
            me->StopMoving();
            me->GetMotionMaster()->Clear();
            if (Creature* m = MograineCreature())
                me->SetFacingToObject(m);
            me->SetStandState(UNIT_STAND_STATE_KNEEL);
            me->CastSpell(me, SPELL_WM_RESURRECTION, false);
        }
        else if (Creature* m = MograineCreature())
        {
            m->StopMoving();
            m->GetMotionMaster()->Clear();
            m->SetFacingToObject(me);
            m->SetStandState(UNIT_STAND_STATE_KNEEL);
            m->CastSpell(m, SPELL_WM_LAY_ON_HANDS, false);
        }
        LogWm("channel", Acore::StringFormat("why={} fallen={} window={}ms", why, UnitName(_save.fallen),
            _save.windowMs));
    }

    void UpdateSave()
    {
        if (!_save.active)
            return;
        if (!_save.channeling)
        {
            if (_clockMs >= _save.runGiveUpAt)
                StartChannel("run-give-up");
            return;
        }
        if (_clockMs >= _save.endsAt)
            CompleteSave();
    }

    // The channel finished with the saver alive: the fallen stands at 50%.
    void CompleteSave()
    {
        PairUnit const fallen = _save.fallen;
        MograineFight* f = MograineAI();
        Creature* m = f ? f->Mograine() : nullptr;
        _save = {};
        _stage = PairStage::Pair;
        if (fallen == PairUnit::Mograine)
        {
            me->InterruptNonMeleeSpells(false);
            if (f)
                f->GetUp(kSaveReturnPct, "her-save");
            if (m)
                m->CastSpell(m, SPELL_WM_RISE_LOOK, true);
            ReleaseHold("her-save");
        }
        else
        {
            if (m)
            {
                m->InterruptNonMeleeSpells(false);
                m->SetStandState(UNIT_STAND_STATE_STAND);
            }
            if (f)
                ReleaseMograine(*f);    // he goes back to his victim
            _body.Revive(me, kSaveReturnPct);
            me->CastSpell(me, SPELL_WM_LAY_ON_HANDS_LOOK, true);
            ReleaseHold("his-save");
        }
        Describe();
        if (_hardMode)
        {
            _hardMode->OnSaveEnd(*this, fallen, true);
            if (fallen == PairUnit::Mograine)
                _hardMode->OnRise(*this, false);
        }
        LogWm("saved", Acore::StringFormat("fallen={} at={:.0f}%", UnitName(fallen), kSaveReturnPct));
    }

    // WM1b's cap spent (normal): she lies until he dies; he fights on alone.
    void BecomeSpent()
    {
        _stage = PairStage::HerSpent;
        CancelLane("spent");
        _bodyShieldUntil = 0;
        Describe();
        LogWm("vow-spent", Acore::StringFormat("she falls (his saves {} spent); he fights on alone", _hisSaves));
    }

    // Both die: him first (his quests credit his real death), then her (her death is the encounter's credit).
    void QueuePairDeath(Unit* killer, char const* why)
    {
        if (_pairDeathQueued)
            return;
        _pairDeathQueued = true;
        if (killer)
            _pairDeathKiller = killer->GetGUID();
        LogWm("pair-death", Acore::StringFormat("why={} stage={}", why, StageName(_stage)));
    }

    void FlushQueued()
    {
        if (_shieldDebt)
        {
            uint32 const share = _shieldDebt;
            _shieldDebt = 0;
            Creature* m = MograineCreature();
            Unit* from = ObjectAccessor::GetUnit(*me, _shieldDebtFrom);
            if (m && m->IsAlive() && from && from->IsAlive() && MograineUp())
                Unit::DealDamage(from, m, share, nullptr, DIRECT_DAMAGE, SPELL_SCHOOL_MASK_NORMAL, nullptr, false);
        }
        if (!_pairDeathQueued)
            return;
        _pairDeathQueued = false;
        Unit* killer = ObjectAccessor::GetUnit(*me, _pairDeathKiller);
        if (!killer)
        {
            std::vector<Player*> const players = FightPlayers();
            killer = players.empty() ? nullptr : players.front();
        }
        PairStage const was = _stage;
        _stage = PairStage::Over;
        if (_save.active && _save.fallen == PairUnit::Whitemane)
            if (MograineFight* f = MograineAI())
                ReleaseMograine(*f);
        _save = {};
        if (Creature* m = MograineCreature())
            if (m->IsAlive())
            {
                if (MograineFight* f = MograineAI())
                    f->KillForGood(killer);
                else
                    Unit::Kill(killer ? killer : me, m);
            }
        LogWm("pair-dies", Acore::StringFormat("was={} killer={}", StageName(was),
            killer ? killer->GetName() : std::string("none")));
        if (me->IsAlive())
            _body.Finish(me, killer);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WM2 To Her Side
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateLane()
    {
        if (_lane.active)
        {
            MograineFight* f = MograineAI();
            if (!f || !MograineUp())
            {
                CancelLane("mograine-gone");
                return;
            }
            if (!_lane.charging && _clockMs >= _lane.chargeAt)
                BeginCharge(*f);
            else if (_lane.charging && _clockMs >= _lane.giveUpAt)
                LaneArrived(*f, "give-up");
            return;
        }
        if (!Due(_nextLane) || _stage != PairStage::Pair || _kitHeld || _save.active || _body.Fallen())
            return;
        if (_hardMode && !_hardMode->ToHerSideAllowed(*this))
            return;
        MograineFight* f = MograineAI();
        Creature* m = f ? f->Mograine() : nullptr;
        if (!f || !m || !MograineUp() || f->Casting())
            return;
        if (m->GetExactDist2d(me) < kLaneMinYd)
        {
            _nextLane = _clockMs + kRetryMs;
            return;
        }
        if (!m->IsWithinLOSInMap(me))
        {
            if (!_laneBlockedSince)
                _laneBlockedSince = _clockMs;
            if (_clockMs - _laneBlockedSince >= kLaneNoSightGiveUpMs)
            {
                _laneBlockedSince = 0;
                _nextLane = _clockMs + LaneEvery();
                LogWm("lane-no-sight", "no line of sight for 5 s: this charge is skipped");
            }
            return;
        }
        _laneBlockedSince = 0;
        StartLane(*f, m);
    }

    void StartLane(MograineFight& f, Creature* m)
    {
        Vec2 const end = LaneArrival(PlaneOf(me), PlaneOf(m));
        float const length = Distance2d(PlaneOf(m), end);
        uint32 const flight = ChargeFlightMs(length);
        _lane = {};
        _lane.active = true;
        _lane.chargeAt = _clockMs + kLaneWarnMs;
        _lane.arrival = Position(end.x, end.y, me->GetPositionZ(), FacingTo(PlaneOf(m), PlaneOf(me)));
        _lane.owner = m->GetGUID();
        _nextLane = _clockMs + LaneEvery();
        f.HoldControl(f.RisenMs() + kLaneWarnMs + flight + kChargeGraceMs + 500);
        m->InterruptNonMeleeSpells(false);
        m->StopMoving();
        m->GetMotionMaster()->Clear();
        m->SetFacingToObject(me);
        f.Say(SAY_MOGRAINE_MILADY);
        float const pct = kLanePct(_heroic);
        MechanicRef ref = Mechanic::Line(m, BossMechanics::Anchor(m->GetPosition()),
            BossMechanics::Anchor(_lane.arrival), kLaneWidthYd, Ms(kLaneWarnMs));
        ref.Damage(pct).TankDamage(pct).Weakened().School(SPELL_SCHOOL_NORMAL).Spell(SPELL_WM_LANE_HIT)
            .Within(FloorBounds()).Tag(TAG_WM_LANE);
        _lane.handle = ref.Handle();
        f.Track(_lane.handle);
        LogWm("lane", Acore::StringFormat("length={:.1f}yd pct={:.0f} warn={}ms charge={}ms", length, pct,
            kLaneWarnMs, flight));
    }

    void BeginCharge(MograineFight& f)
    {
        Creature* m = f.Mograine();
        if (!m)
            return;
        _lane.charging = true;
        float const length = m->GetExactDist2d(_lane.arrival.GetPositionX(), _lane.arrival.GetPositionY());
        _lane.giveUpAt = _clockMs + ChargeFlightMs(length) + kChargeGraceMs;
        m->CastSpell(m, SPELL_WM_CHARGE_LOOK, true);
        m->GetMotionMaster()->MoveCharge(_lane.arrival.GetPositionX(), _lane.arrival.GetPositionY(),
            _lane.arrival.GetPositionZ(), kChargeSpeed, POINT_LANE, nullptr, true);
    }

    void LaneArrived(MograineFight& f, char const* why)
    {
        _lane.active = false;
        _lane.charging = false;
        ReleaseMograine(f);     // the tank picks him up beside her
        if (_heroic)
        {
            if (Creature* m = f.Mograine())
                m->CastSpell(m, SPELL_WM_BODY_SHIELD, true);
            _bodyShieldUntil = _clockMs + kBodyShieldMs;
        }
        if (_hardMode)
            _hardMode->OnToHerSide(*this);
        LogWm("lane-arrived", Acore::StringFormat("why={} body-shield={}", why, _heroic ? 1 : 0));
    }

    void CancelLane(char const* why)
    {
        if (!_lane.active)
            return;
        if (Unit* owner = ObjectAccessor::GetUnit(*me, _lane.owner))
            Mechanic::Cancel(owner, _lane.handle);
        if (_lane.charging || _clockMs < _lane.chargeAt)
            if (MograineFight* f = MograineAI())
                if (f->State() == SmLastStand::MograineState::Risen)
                    ReleaseMograine(*f);
        _lane = {};
        LogWm("lane-cancelled", why);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WM3 Penance, WM4 Heal, WM4a Power Word: Shield, WM6 Holy Smite
    // ----------------------------------------------------------------------------------------------------------------

    // WM4a and WM3: instant and triggered.
    void UpdateInstants()
    {
        Creature* m = _stage == PairStage::Pair && MograineUp() ? MograineCreature() : nullptr;
        if (Due(_nextShield))
        {
            if (m)
            {
                CastShield(m);
                _nextShield = _clockMs + kShieldEveryMs;
            }
            else
                _nextShield = _clockMs + kRetryMs;
        }
        if (Due(_nextPenance) && !_kitHeld)
        {
            if (_stage == PairStage::Pair || _stage == PairStage::HisDead)
            {
                MarkPenance("timer");
                _nextPenance = _clockMs + kPenanceEveryMs;
            }
            else
                _nextPenance = _clockMs + kRetryMs;
        }
    }

    // WM4 and WM6: the cast bars (one at a time; Heal first).
    void UpdateCasts()
    {
        Creature* m = _stage == PairStage::Pair && MograineUp() ? MograineCreature() : nullptr;
        if (Due(_nextHeal))
        {
            if (m && me->IsWithinDistInMap(m, kCastRangeYd) && me->IsWithinLOSInMap(m) && CastHeal(m))
            {
                _nextHeal = _clockMs + kHealEveryMs;
                Mechanic::NoteNextCastIn(me, SPELL_WM_HEAL, Ms(kHealEveryMs));
                return;
            }
            _nextHeal = _clockMs + kRetryMs;
        }
        if (Due(_nextSmite))
        {
            Unit* victim = me->GetVictim();
            if (victim && CastSmite(victim))
                _nextSmite = 0;     // the next one 4 s after this cast ends (OnSpellCast / OnSpellFailed)
            else
                _nextSmite = _clockMs + kRetryMs;
        }
    }

    bool CastHeal(Creature* m)
    {
        me->StopMoving();
        uint32 const pct = kHealPct(_heroic);
        CastSpellExtraArgs args;
        args.AddSpellBP0(static_cast<int32>(pct));
        SpellCastResult const result = me->CastSpell(m, SPELL_WM_HEAL, args);
        if (result != SPELL_CAST_OK)
        {
            LogWm("heal-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        LogWm("heal", Acore::StringFormat("pct={} cast={}ms on={:.0f}%", pct, kHealCastMs, m->GetHealthPct()));
        return true;
    }

    void CastShield(Creature* m)
    {
        uint32 const amount = static_cast<uint32>(static_cast<float>(m->GetMaxHealth()) * kShieldPct / 100.f);
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(static_cast<int32>(amount));
        me->CastSpell(m, SPELL_WM_POWER_WORD_SHIELD, args);
        LogWm("shield", Acore::StringFormat("absorb={} ({:.0f}% of {})", amount, kShieldPct, m->GetMaxHealth()));
    }

    bool CastSmite(Unit* victim)
    {
        Player* player = victim->ToPlayer();
        if (!player || !me->IsWithinDistInMap(victim, kCastRangeYd))
            return false;
        if (!me->IsWithinLOSInMap(victim))
        {
            me->GetMotionMaster()->MoveChase(victim);    // no sight: close in until she has it
            return false;
        }
        me->StopMoving();
        float const pct = kSmitePct(_heroic);
        CastSpellExtraArgs args;
        args.AddSpellBP0(static_cast<int32>(DungeonKit::RefFlat(me, pct, IsTank(player))));
        SpellCastResult const result = me->CastSpell(victim, SPELL_WM_HOLY_SMITE, args);
        if (result != SPELL_CAST_OK)
            return false;
        me->GetMotionMaster()->MoveChase(victim, ChaseRange(0.f, kChaseRangeYd));
        return true;
    }

    void MarkPenance(char const* why)
    {
        std::vector<Player*> const players = FightPlayers();
        std::vector<PenanceCandidate> candidates;
        for (Player* p : players)
            candidates.push_back({ p->GetGUID().GetRawValue(), IsTank(p), p->IsAlive() });
        std::vector<std::uint64_t> const picks = PickPenance(candidates, kPenanceCount(_heroic),
            [](std::uint32_t n) { return n ? urand(0, n - 1) : 0u; });
        if (picks.empty())
        {
            LogWm("penance-none", why);
            return;
        }
        GuidSet targets;
        std::vector<Player*> marked;
        for (Player* p : players)
            if (std::find(picks.begin(), picks.end(), p->GetGUID().GetRawValue()) != picks.end())
            {
                targets.insert(p->GetGUID());
                marked.push_back(p);
                me->CastSpell(p, SPELL_WM_PENANCE_MARK, true);
            }
        me->CastSpell(me, SPELL_WM_PENANCE_HANDS, true);
        Unit* owner = MechanicOwner();
        float const others = kPenanceOthersPct(_heroic);
        Cancel(_penance);
        MechanicRef ref = Mechanic::Spread(owner, kPenanceRadiusYd, Ms(kPenanceWarnMs));
        ref.Targets(targets).Damage(others).TankDamage(others).Weakened().School(SPELL_SCHOOL_HOLY)
            .Spell(SPELL_WM_PENANCE_HIT).Within(FloorBounds()).Tag(TAG_WM_PENANCE);
        std::vector<ObjectGuid> const guids(targets.begin(), targets.end());
        ObjectGuid const self = me->GetGUID();
        Map* map = me->GetMap();
        ref.OnResolve([map, self, guids](BossMechanics::ResolveResult const&)
        {
            Creature* her = map ? map->GetCreature(self) : nullptr;
            auto* ai = her && her->IsAlive() && her->IsAIEnabled ? dynamic_cast<boss_whitemane_rework*>(her->AI())
                : nullptr;
            if (ai)
                ai->PenanceLands(guids);
        });
        _penance = { owner->GetGUID(), ref.Handle() };
        LogWm("penance", Acore::StringFormat("why={} marked={} others={:.0f}% marked-hit={:.0f}%", why,
            Names(marked), others, kPenanceMarkedPct(_heroic)));
    }

public:
    // WM3: the pillars fall; each marked player takes its own hit (the registry's Spread hits only the others).
    void PenanceLands(std::vector<ObjectGuid> const& guids)
    {
        if (_state != WhitemaneState::Fight)
            return;
        Unit* caster = HitCaster();
        float const pct = kPenanceMarkedPct(_heroic);
        uint32 hit = 0;
        for (ObjectGuid const& guid : guids)
        {
            Player* p = ObjectAccessor::GetPlayer(*me, guid);
            if (!CountsAsPlayer(p))
                continue;
            caster->CastSpell(p, SPELL_WM_PENANCE_PILLAR, true);
            CastPercent(caster, p, SPELL_WM_PENANCE_STRIKE, pct, IsTank(p));
            ++hit;
        }
        LogWm("penance-lands", Acore::StringFormat("marked={} pct={:.0f}", hit, pct));
    }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // WM5 the Vigil Flame (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateFlame()
    {
        if (!_heroic || !Due(_nextFlame) || _kitHeld)
            return;
        if (_stage == PairStage::Alone || _stage == PairStage::Rising || _stage == PairStage::Over)
            return;
        _nextFlame = _clockMs + FlameEvery();
        Player* carrier = ObjectAccessor::GetPlayer(*me, _flameCarrier);
        if (!_flameCarrier)
        {
            FirstCarrier("first");
            return;
        }
        if (!CountsAsPlayer(carrier))
        {
            FirstCarrier("orphaned");
            return;
        }
        Flare(carrier);
    }

    std::vector<FlameCandidate> FlameOthers(Player const* carrier, std::vector<Player*>& players)
    {
        players.clear();
        std::vector<FlameCandidate> out;
        for (Player* p : FightPlayers())
        {
            if (p == carrier)
                continue;
            FlameCandidate c;
            c.id = p->GetGUID().GetRawValue();
            c.alive = p->IsAlive();
            c.seared = p->HasAura(SPELL_WM_SEARED);
            c.tank = IsTank(p);
            c.distanceYd = carrier ? carrier->GetExactDist2d(p) : 0.f;
            if (carrier && std::fabs(carrier->GetPositionZ() - p->GetPositionZ()) > 5.f)
                c.distanceYd = 1000.f;
            out.push_back(c);
            players.push_back(p);
        }
        return out;
    }

    void FirstCarrier(char const* why)
    {
        std::vector<Player*> players;
        std::vector<FlameCandidate> const others = FlameOthers(nullptr, players);
        std::optional<std::size_t> const pick = PickCarrier(others,
            [](std::uint32_t n) { return n ? urand(0, n - 1) : 0u; });
        if (!pick)
        {
            LogWm("flame-none", why);
            return;
        }
        GiveFlame(players[*pick], why);
    }

    void Flare(Player* carrier)
    {
        std::vector<Player*> players;
        std::vector<FlameCandidate> others = FlameOthers(carrier, players);
        std::optional<std::size_t> const partner = FlarePartner(others);
        bool const carrierSeared = carrier->HasAura(SPELL_WM_SEARED);
        bool const partnerSeared = partner && others[*partner].seared;
        FlareShares const shares = FlareSplit(partner.has_value(), carrierSeared, partnerSeared);
        Unit* caster = HitCaster();
        Player* partnerPlayer = partner ? players[*partner] : nullptr;
        CastPercent(caster, carrier, SPELL_WM_VIGIL_FLARE, shares.carrierPct, IsTank(carrier));
        if (partnerPlayer)
            CastPercent(caster, partnerPlayer, SPELL_WM_VIGIL_FLARE, shares.partnerPct, IsTank(partnerPlayer));
        LogWm("flare", Acore::StringFormat("carrier={} {:.0f}% partner={} {:.0f}%", carrier->GetName(),
            shares.carrierPct, partnerPlayer ? partnerPlayer->GetName() : std::string("none"), shares.partnerPct));

        // The pass: to the partner when it can carry it, else a fresh unseared carrier (the tank last).
        Player* next = nullptr;
        if (partnerPlayer)
        {
            others[*partner].alive = partnerPlayer->IsAlive();
            if (PartnerCarriesOn(others[*partner]))
                next = partnerPlayer;
        }
        if (!next)
        {
            for (std::size_t i = 0; i < others.size(); ++i)
                others[i].alive = players[i]->IsAlive();
            std::optional<std::size_t> const pick = PickCarrier(others,
                [](std::uint32_t n) { return n ? urand(0, n - 1) : 0u; });
            next = pick ? players[*pick] : nullptr;
        }
        if (!next)
        {
            if (CountsAsPlayer(carrier))
                RegisterFlameSoak(carrier);     // nobody else can take it: it stays
            else
                ClearFlame("no-carrier");
            return;
        }
        carrier->RemoveAurasDueToSpell(SPELL_WM_VIGIL_FLAME);
        if (carrier->IsAlive())
            if (Aura* seared = me->AddAura(SPELL_WM_SEARED, carrier))
            {
                seared->SetMaxDuration(static_cast<int32>(SearedFor()));
                seared->SetDuration(static_cast<int32>(SearedFor()));
            }
        GiveFlame(next, "pass");
    }

    void GiveFlame(Player* carrier, char const* why)
    {
        ObjectGuid const old = _flameCarrier;
        if (Player* before = ObjectAccessor::GetPlayer(*me, old))
            if (before != carrier)
                before->RemoveAurasDueToSpell(SPELL_WM_VIGIL_FLAME);
        _flameCarrier = carrier->GetGUID();
        me->AddAura(SPELL_WM_VIGIL_FLAME, carrier);
        HitCaster()->CastSpell(carrier, SPELL_WM_FLAME_PASS, true);
        Talk(EMOTE_WHITEMANE_FLAME, carrier);
        RegisterFlameSoak(carrier);
        LogWm("flame", Acore::StringFormat("why={} carrier={} next-flare={}ms", why, carrier->GetName(),
            _nextFlame > _clockMs ? _nextFlame - _clockMs : 0));
    }

    // The 1-body soak on the carrier (G2's vigil-flame row: the unseared others eligible, the tank last) and the
    // no-damage circle that keeps the Seared off it; both live until the next flare.
    void RegisterFlameSoak(Player* carrier)
    {
        Cancel(_flameSoak);
        Cancel(_flameKeepOff);
        Unit* owner = MechanicOwner();
        uint64 const warn = _nextFlame > _clockMs ? _nextFlame - _clockMs : FlameEvery();
        BossMechanics::Eligibility flame;
        for (Player* p : FightPlayers())
            if (p != carrier)
                flame.carriers.insert(p->GetGUID());
        flame.auraSpell = SPELL_WM_SEARED;
        flame.maxStacks = 0;
        BossMechanics::Ordering tankLast;
        tankLast.roleLast = BossMechanics::Role::Tank;
        MechanicRef soak = Mechanic::Soak(owner, BossMechanics::Anchor(carrier), kFlameRadiusYd, 1, Ms(warn));
        soak.Eligible(flame).Order(tankLast).MissedSoak(BossMechanics::MissedSoakMode::Never).Within(FloorBounds())
            .Tag(TAG_WM_FLAME);
        _flameSoak = { owner->GetGUID(), soak.Handle() };
        BossMechanics::Eligibility seared;
        seared.auraSpell = SPELL_WM_SEARED;
        seared.minStacks = 1;
        MechanicRef keepOff = Mechanic::Circle(owner, BossMechanics::Anchor(carrier), kFlameRadiusYd, Ms(warn));
        keepOff.Eligible(seared).Within(FloorBounds()).Tag(TAG_WM_SEARED_OFF);
        _flameKeepOff = { owner->GetGUID(), keepOff.Handle() };
    }

    // The hold released: a carried flame's flare no sooner than kFlameRewarnMs from now, and its soak again (the one
    // registered before the hold resolved, harmlessly, on the old timing).
    void RefreshFlameAfterHold(char const* why)
    {
        if (!_heroic || !_flameCarrier)
            return;
        Player* carrier = ObjectAccessor::GetPlayer(*me, _flameCarrier);
        if (!CountsAsPlayer(carrier))
            return;     // UpdateFlame picks a new carrier when the flare comes
        _nextFlame = FlareAfterHold(_nextFlame, _clockMs);
        RegisterFlameSoak(carrier);
        LogWm("flame-rewarn", Acore::StringFormat("why={} carrier={} next-flare={}ms", why, carrier->GetName(),
            _nextFlame > _clockMs ? _nextFlame - _clockMs : 0));
    }

    void ClearFlame(char const* why)
    {
        Cancel(_flameSoak);
        Cancel(_flameKeepOff);
        if (!_flameCarrier)
            return;
        if (Player* carrier = ObjectAccessor::GetPlayer(*me, _flameCarrier))
            carrier->RemoveAurasDueToSpell(SPELL_WM_VIGIL_FLAME);
        _flameCarrier.Clear();
        _nextFlame = 0;
        LogWm("flame-out", why);
    }

public:
    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm whitemane` entry points
    // ----------------------------------------------------------------------------------------------------------------

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestKind kind, Player* gm)
    {
        bool const fighting = _state == WhitemaneState::Fight;
        MograineFight* f = MograineAI();
        switch (kind)
        {
            case TestKind::Vigil:
                if (fighting)
                    return "She is fighting.";
                WalkToVigil(true, "test");
                return {};
            case TestKind::Clear:
                if (fighting)
                    EnterEvadeMode(EVADE_REASON_OTHER);
                else
                    PlaceForStage(false, "test");
                return {};
            default:
                break;
        }
        if (!fighting)
            return "She is not fighting: pull her at the vigil first.";
        switch (kind)
        {
            case TestKind::Rise:
                if (_stage != PairStage::Alone)
                    return Acore::StringFormat("The rising is past ({}).", StageName(_stage));
                StartRising("test");
                return {};
            case TestKind::Lane:
                if (_stage != PairStage::Pair || !f || !MograineUp())
                    return "Both must stand (after the rising).";
                if (_lane.active)
                    return "A charge is in progress.";
                StartLane(*f, f->Mograine());
                return {};
            case TestKind::Penance:
                MarkPenance("test");
                return {};
            case TestKind::Heal:
                if (!MograineUp())
                    return "Mograine does not stand.";
                return CastHeal(MograineCreature()) ? std::string() : std::string("Refused (casting?).");
            case TestKind::Shield:
                if (!MograineUp())
                    return "Mograine does not stand.";
                CastShield(MograineCreature());
                return {};
            case TestKind::Smite:
                return gm && CastSmite(gm) ? std::string() : std::string("Refused (range, sight, casting).");
            case TestKind::Flame:
                if (!_heroic)
                    return "The Vigil Flame is heroic only (`heroic 1` first).";
                if (_stage == PairStage::Alone || _stage == PairStage::Rising)
                    return "After the rising.";
                _nextFlame = _clockMs;
                return {};
            case TestKind::HisFall:
            {
                if (_stage != PairStage::Pair || !f || !MograineUp())
                    return "Both must stand.";
                Creature* m = f->Mograine();
                uint32 damage = m->GetHealth();
                OnMograineDamage(*f, gm, damage);
                if (damage < m->GetHealth())
                    m->SetHealth(m->GetHealth() - damage);
                return {};
            }
            case TestKind::HerFall:
            {
                if (_stage != PairStage::Pair)
                    return "Both must stand.";
                uint32 damage = me->GetHealth();
                DamageTaken(gm, damage, DIRECT_DAMAGE, SPELL_SCHOOL_MASK_NORMAL);
                if (damage < me->GetHealth())
                    me->SetHealth(me->GetHealth() - damage);
                return {};
            }
            default:
                break;
        }
        return {};
    }

    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
    }

    std::string TestState()
    {
        auto in = [this](uint64 at) -> std::string
        {
            return at ? Acore::StringFormat("{}ms", at > _clockMs ? at - _clockMs : 0) : std::string("off");
        };
        Player* carrier = ObjectAccessor::GetPlayer(*me, _flameCarrier);
        CathedralStage const stage = instance ? static_cast<CathedralStage>(instance->GetData(DATA_CATHEDRAL_STAGE))
            : CathedralStage::BeforeStand;
        return Acore::StringFormat("Whitemane: state={} stage={} heroic={} hardmode={} saves her={} his={} cap={} "
            "body={} save={} lane={} rising={} | next: smite={} heal={} shield={} penance={} lane={} flame={} | "
            "carrier={} | mograine={} up={} | slot6={} cathedral-stage={} hooks: risen={} hardmode={}",
            StateName(_state), StageName(_stage), _heroic ? 1 : 0, _hardMode ? 1 : 0, _herSaves, _hisSaves,
            SaveCap(), _body.Fallen() ? 1 : 0, _save.active ? UnitName(_save.fallen) : "none", _lane.active ? 1 : 0,
            in(_riseAt), in(_nextSmite), in(_nextHeal), in(_nextShield), in(_nextPenance), in(_nextLane),
            in(_nextFlame), carrier ? carrier->GetName() : std::string("none"),
            MograineAI() ? SmLastStand::StateName(MograineAI()->State()) : "no-ai", MograineUp() ? 1 : 0,
            instance ? instance->GetBossState(BOSS_WHITEMANE) : 0, uint32(stage),
            SmLastStand::HasMograineRisen() ? 1 : 0, HasWhitemaneHardMode() ? 1 : 0);
    }

    void TestForce(bool on)
    {
        _testForced = on;
    }

private:
    DungeonKit::ArenaGuard _arena;
    DungeonKit::HeldBody _body;
    std::unique_ptr<WhitemaneHardMode> _hardMode;
    WhitemaneState _state = WhitemaneState::Chamber;
    PairStage _stage = PairStage::Over;
    RiseStep _rise = RiseStep::None;
    Save _save;
    Lane _lane;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next pull
    bool _testForced = false;
    bool _placePending = true;
    bool _kitHeld = false;
    bool _pairDeathQueued = false;
    bool _ending = false;
    bool _selfBreak = false;
    uint8 _herSaves = 0;
    uint8 _hisSaves = 0;
    uint32 _wipeMs = 0;
    uint32 _shieldDebt = 0;
    uint64 _clockMs = 0;
    uint64 _pullAt = 0;
    uint64 _riseAt = 0;
    uint64 _risingAt = 0;
    uint64 _riseRunGiveUpAt = 0;
    uint64 _walkGiveUpAt = 0;
    uint64 _killLineReadyMs = 0;
    uint64 _nextSmite = 0;
    uint64 _nextHeal = 0;
    uint64 _nextShield = 0;
    uint64 _nextPenance = 0;
    uint64 _nextLane = 0;
    uint64 _nextFlame = 0;
    uint64 _laneBlockedSince = 0;
    uint64 _bodyShieldUntil = 0;
    ObjectGuid::LowType _mograineSpawnId = 0;   // see MograineSpawnId
    ObjectGuid _pairDeathKiller;
    ObjectGuid _shieldDebtFrom;
    ObjectGuid _flameCarrier;
    OwnedHandle _penance;
    OwnedHandle _flameSoak;
    OwnedHandle _flameKeepOff;
    std::vector<OwnedHandle> _handles;
    std::vector<ObjectGuid> _joined;
};

// ---------------------------------------------------------------------------------------------------------------------
// Mograine's rising, as D14 runs it (MograineFight.h MograineRisen; D13 makes one per rising and calls its hooks)
// ---------------------------------------------------------------------------------------------------------------------
namespace
{
    boss_whitemane_rework* WhitemaneOf(Creature* mograine)
    {
        InstanceScript* instance = mograine ? mograine->GetInstanceScript() : nullptr;
        if (!instance)
            return nullptr;
        Creature* her = ObjectAccessor::GetCreature(*mograine, instance->GetGuidData(DATA_WHITEMANE));
        if (!her || !her->IsAIEnabled)
            return nullptr;
        return dynamic_cast<boss_whitemane_rework*>(her->AI());
    }

    class WhitemaneRisen final : public SmLastStand::MograineRisen
    {
    public:
        void OnRise(MograineFight& fight, bool first) override
        {
            if (boss_whitemane_rework* ai = WhitemaneOf(fight.Mograine()))
                ai->OnMograineRise(fight, first);
        }

        void OnDamageTaken(MograineFight& fight, Unit* attacker, uint32& damage) override
        {
            if (boss_whitemane_rework* ai = WhitemaneOf(fight.Mograine()))
                ai->OnMograineDamage(fight, attacker, damage);
        }

        bool OnEvade(MograineFight& fight) override
        {
            boss_whitemane_rework* ai = WhitemaneOf(fight.Mograine());
            return ai && ai->KeepsMograine();
        }

        void OnMovementInform(MograineFight& fight, uint32 type, uint32 id) override
        {
            if (boss_whitemane_rework* ai = WhitemaneOf(fight.Mograine()))
                ai->OnMograineMovement(fight, type, id);
        }

        void OnDied(MograineFight& fight, Unit* killer) override
        {
            if (boss_whitemane_rework* ai = WhitemaneOf(fight.Mograine()))
                ai->OnMograineDied(fight, killer);
        }

        void OnEnd(MograineFight& fight, bool died) override
        {
            if (boss_whitemane_rework* ai = WhitemaneOf(fight.Mograine()))
                ai->OnMograineEnd(fight, died);
            else if (Creature* m = fight.Mograine())
            {
                m->RemoveAurasDueToSpell(SPELL_WM_POWER_WORD_SHIELD);
                m->RemoveAurasDueToSpell(SPELL_WM_BODY_SHIELD);
            }
        }
    };

    // ---- `.dbtest sm whitemane` ----

    boss_whitemane_rework* WhitemaneAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_WHITEMANE);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_whitemane_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_whitemane_rework* ai = WhitemaneAI(handler);
        if (!ai)
            return false;
        std::string const error = ai->TestFire(kind, handler->GetPlayer());
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->SendSysMessage(ok);
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_WHITEMANE, BOSS_WHITEMANE);
    }

    // `.dbtest sm whitemane state`: her state, the pair's stage, the saves, the timers, the carrier, Mograine.
    bool HandleState(ChatHandler* handler)
    {
        boss_whitemane_rework* ai = WhitemaneAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    // Handoff section 3.7: `.dbtest sm whitemane hardmode` arms the hard mode past its trigger (GM).
    bool HandleHardMode(ChatHandler* handler)
    {
        return SmTest::ArmHardMode(handler, BOSS_THE_TRUTH);
    }

    bool HandleVigil(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Vigil, "Whitemane walks out to her vigil (line 3).");
    }

    bool HandleRise(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Rise, "The rising now: Deep Sleep, the run, the raise.");
    }

    bool HandleLane(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Lane, "To Her Side: the 2 s lane, then his charge.");
    }

    bool HandlePenance(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Penance, "Penance: the marks (3 s), then the pillars.");
    }

    bool HandleHeal(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Heal, "Heal on Mograine (3 s, interruptible).");
    }

    bool HandleShield(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Shield, "Power Word: Shield on Mograine.");
    }

    bool HandleSmite(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Smite, "Holy Smite on you (2.5 s).");
    }

    bool HandleFlame(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Flame, "The Vigil Flame: the next flare (or the first carrier) now.");
    }

    bool HandleHisFall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::HisFall, "Mograine falls: her save (or his real death).");
    }

    bool HandleHerFall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::HerFall, "Whitemane falls: his save (or the vow is spent).");
    }

    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared (a running fight wipes; else she is placed again).");
    }

    // `.dbtest sm whitemane heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_whitemane_rework* ai = WhitemaneAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the next pull ends.");
        return true;
    }

    // `.dbtest sm whitemane force [0|1]`: she may be pulled before the Last Stand is DONE (the instance still refuses
    // her slot then).
    bool HandleForce(ChatHandler* handler, Optional<uint32> on)
    {
        boss_whitemane_rework* ai = WhitemaneAI(handler);
        if (!ai)
            return false;
        ai->TestForce(!on || *on != 0);
        handler->SendSysMessage("Pull guard set.");
        return true;
    }

    ChatCommandTable const& BossWhitemaneTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,    SEC_GAMEMASTER, Console::No },
            { "hardmode",   HandleHardMode, SEC_GAMEMASTER, Console::No },
            { "vigil",      HandleVigil,    SEC_GAMEMASTER, Console::No },
            { "rise",       HandleRise,     SEC_GAMEMASTER, Console::No },
            { "lane",       HandleLane,     SEC_GAMEMASTER, Console::No },
            { "penance",    HandlePenance,  SEC_GAMEMASTER, Console::No },
            { "heal",       HandleHeal,     SEC_GAMEMASTER, Console::No },
            { "shield",     HandleShield,   SEC_GAMEMASTER, Console::No },
            { "smite",      HandleSmite,    SEC_GAMEMASTER, Console::No },
            { "flame",      HandleFlame,    SEC_GAMEMASTER, Console::No },
            { "hisfall",    HandleHisFall,  SEC_GAMEMASTER, Console::No },
            { "herfall",    HandleHerFall,  SEC_GAMEMASTER, Console::No },
            { "clear",      HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic",     HandleHeroic,   SEC_GAMEMASTER, Console::No },
            { "force",      HandleForce,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_whitemane_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_whitemane_rework, ScarletMonasteryRework::kInstanceScriptName);
    // Mograine's rising is D14's on every wave: D13's AI asks for it only when it runs (wave 2 bound).
    SmLastStand::RegisterMograineRisen([](Creature*) { return std::make_unique<WhitemaneRisen>(); });
    SmTest::RegisterBoss("whitemane", BossWhitemaneTestCommands());
}
