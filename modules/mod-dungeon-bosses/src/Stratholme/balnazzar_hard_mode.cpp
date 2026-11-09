/*
 * mod-dungeon-bosses, Stratholme S8: Balnazzar's hard mode, the Grand Lie (heroic only). WP-S8 owns this file.
 * Build spec: docs/dungeons/stratholme-rework.md ST 1920-1999 (Hard mode), ST 2107-2120 (the HM rows); handoff section
 * 3.7, section 3.5 row S8, section 3.6 (600k), section 7 #9 (bots never use the relics) and #10 (the Letter is not
 * consumed). Pure part: GrandLieLogic.h (tests/strat_grand_lie_test.cpp). Data: apps/dbc-tools source/npcs/stratholme/
 * balnazzar_hard_mode.py (the spells 206575-206588, the relics' use spells among them; the swarm stalker 300609),
 * source/items/stratholme_relics.py (the relics' table) and source/items.csv (their Item.dbc rows), and WP-S8's SQL
 * rev (the relic items 70600-70603, the four gameobjects 301203-301206 and their heroic spawns, texts 8-16).
 *
 * The opt-in: on heroic, once Galford is dead, the Letter of Proof lies by the Scarlet Archive (gameobject 301203);
 * a click gives everyone in the group a Letter (item 70600). Using it within 30 yd of Dathrohan out of combat lights
 * DATA_GRAND_LIE (the instance refuses it otherwise, saves it, keeps it through wipes, records BOSS_GRAND_LIE on a lit
 * kill and rides the loot bit); he says line 8, then 2.5 s later yells line 9, the mask burns away (S7's Unmask, no
 * stun) and he attacks the reader. A retry pull with the flag still lit starts the same way (line 9, the unmask).
 *
 * The fight (TheGrandLie, a GrandLie on S7's AI through DathrohanFight.h; S7 makes one per heroic pull with the flag
 * lit):
 *   pull         600k (create health, back to the template's on a wipe), the loot bit (LootMode 2), act 1.
 *   acts         by health, 100-70-40%; never back.
 *   HM1-HM4      the calls: act 1 one twin every 10 s (Cleave, Ring, Mark in turn), act 2 a pair every 12 s, act 3
 *                all three every 15 s, from 8 s. Each piece is a yell, 1 s apart; truth rolled per piece; all land 4 s
 *                after the call's first yell. The real hit is registered NoTelegraph (bots read it); the claimed
 *                marker is a Decoy drawn alike for truth and lie (the S7 heroic pattern: the yell is the only tell).
 *                Cleave: a 180 degree cone from the brazier over half the room (the measured frame), the half with
 *                more swarms struck (true: the claimed half; lie: the other). Ring: a 10 yd circle on him (true) or
 *                the 10-40 yd donut (lie). Mark: a 6 yd Stack on a random non-tank, 100% split (true) or a 7 yd Spread
 *                on every non-tank, 50% (lie). 50% to the non-tanks; the tank is exempt from all three.
 *   HM5 swarms   a stalker (300609) out of the wall every 20 s from 15 s (cap 2 / 3 / 4 by act), crawling in
 *                straight lines at 3 yd/s and turning off the wall, gone at 30 s; a persistent 5 yd circle (2.5 yd
 *                radius) on it, 10% a second and Weakened on everyone inside after a 1 s grace; the Standard's ward
 *                spares its holders. During a call (its last 4 s) no swarm crosses the middle: it turns off it.
 *                Blessed Holy Water's splash disperses a swarm.
 *   HM6 cones    act 2 on: S7's Carrion Swarm, two cones, 25% / 50%, every 20 s on its own timer; the Standard's ward.
 *   HM7 meteor   act 2 on: S7's Inferno every 30 s, the 25k stoking Infernal; never landing in a call's window.
 *   HM8 sleep    acts 1-2: S7's heroic Sleep. Act 3: Sleep is held; Dread Slumber every 30 s, a 3 s cast that cannot
 *                be interrupted, landing 2 s after a call: every player without the Medallion's ward sleeps 5 s
 *                (S7's Sleep aura, then Nightmare); the next call's first yell 3 s after it lands.
 *   HM10         Vampiric Aura heals 3% per hit landed (every twin, swarm, cone and Infernal hit).
 *   cleanup      death, evade, reset: the swarms and their zones, the marks, the 600k (a wipe only). The flag stays
 *                with the instance (section 7 #10).
 *
 * The relics (HM9; heroic only, spawnMask 2, shown when their boss is dead): the Scarlet Standard (301204, Willey's
 * yard), the Medallion's light (301205, Malor's strongbox) and the blessed crate (301206, Crusaders' Square, from the
 * start). A click gives one copy to everyone in the group on the map (KT-2's RelicDispenserAI; bots get theirs and
 * never use them, section 7 #9). Each copy keeps its own cooldown (ruling 33).
 *
 * Every firing logs one INFO line "strat balnazzar hm-<mechanic> ..." (S7's DathrohanFight::Log, module.dungeonbosses).
 * `.dbtest strat grandlie <sub>` drives it.
 */

#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "DathrohanFight.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "DungeonKitWalls.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GrandLieLogic.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <cmath>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace StratholmeRework;
using namespace StratGrandLie;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using StratDathrohan::DathrohanFight;
using StratDathrohan::GrandLie;

namespace
{
    float constexpr kFloorProbeUpYd = 2.f;
    float constexpr kFloorMaxDropYd = 4.f;
    float constexpr kChamberFloorZ = 136.8f;            // StratDathrohan::kFloorZ
    uint32 constexpr kRelicPollMs = 1000;
    uint32 constexpr kMinLegMs = 200;                   // a swarm leg shorter than this waits that long

    // Create health is the base the engine rebuilds max health from (the Deadmines, Ras and Ultimatum hard modes).
    void SetCreatureHealth(Creature* creature, uint32 health)
    {
        creature->SetCreateHealth(health);
        creature->SetStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, static_cast<float>(health));
        creature->UpdateMaxHealth();
        creature->SetHealth(creature->GetMaxHealth());
    }

    float FloorZ(WorldObject const* ref, float x, float y, float z)
    {
        float const floor = ref->GetMapHeight(x, y, z + kFloorProbeUpYd);
        return (floor <= INVALID_HEIGHT + 1.f || std::fabs(floor - z) > kFloorMaxDropYd) ? z : floor;
    }

    // The non-tanks (the tank is exempt from the twins).
    BossMechanics::Eligibility NonTanks()
    {
        BossMechanics::Eligibility e;
        e.roles = BossMechanics::Role::Healer | BossMechanics::Role::Damage;
        return e;
    }

    // Everyone but the Standard's ring (the swarms, HM5; the cones read the same aura through S7's CarrionSpec).
    BossMechanics::Eligibility Unwarded()
    {
        BossMechanics::Eligibility e;
        e.auraSpell = SPELL_GL_STANDARD;
        e.maxStacks = 0;
        return e;
    }

    // S7's fight object of the boss with this guid, from anything on his map.
    DathrohanFight* FightOf(WorldObject const& near, ObjectGuid boss)
    {
        Creature* creature = boss ? ObjectAccessor::GetCreature(near, boss) : nullptr;
        if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
            return nullptr;
        return dynamic_cast<DathrohanFight*>(creature->AI());
    }

    // BZ5 / HM10 on a registry hit: the hit heals him (S7's VampiricHit, the hard mode's 3%).
    std::function<void(Unit*)> VampiricOnHit(Creature* boss, char const* source)
    {
        ObjectGuid const guid = boss->GetGUID();
        return [guid, source](Unit* hit)
        {
            if (!hit)
                return;
            if (DathrohanFight* fight = FightOf(*hit, guid))
                fight->VampiricHit(hit, source);
        };
    }

    Player* PickNonTank(Creature* boss)
    {
        DungeonKit::PickRule rule;
        rule.nonTank = true;
        rule.tankIfAlone = true;        // a solo tank (a test) still gets the mark
        return DungeonKit::PickPlayer(boss, rule);
    }

    std::string Guids(std::vector<ObjectGuid> const& guids)
    {
        return std::to_string(guids.size());
    }
}

// -------------------------------------------------------------------------------------------------------------------
// HM5 the moving swarm (300609): an invisible stalker wearing the cloud, crawling in straight legs (GrandLieLogic.h
// PlanLeg): to the wall and off it like a mirror, or, while the middle is closed (a call's last 4 s), short of the
// split line and off it. Its zone is the hard mode's (a registry circle anchored on it).
// -------------------------------------------------------------------------------------------------------------------

struct npc_st_moving_swarm : public ScriptedAI
{
    explicit npc_st_moving_swarm(Creature* creature) : ScriptedAI(creature)
    {
        me->SetReactState(REACT_PASSIVE);
    }

    void Reset() override { }
    void AttackStart(Unit* /*who*/) override { }
    void MoveInLineOfSight(Unit* /*who*/) override { }

    void Launch(Vec2 dir)
    {
        float const len = std::sqrt(dir.x * dir.x + dir.y * dir.y);
        _dir = len > 0.001f ? Vec2{ dir.x / len, dir.y / len } : Vec2{ 1.f, 0.f };
        _launched = true;
        DoCastSelf(SPELL_GL_SWARM_CLOUD, true);
        NextLeg();
    }

    // HM5: no crossing of the middle for the next `ms` (the running call's last 4 s). A leg already heading across is
    // cut short now.
    void CloseMiddle(uint32 ms)
    {
        bool const wasClosed = MiddleClosed();
        _middleUntil = std::max<uint64>(_middleUntil, _clockMs + ms);
        if (!wasClosed && _launched)
            NextLeg();
    }

    // Blessed Holy Water's splash.
    void Disperse()
    {
        _launched = false;
        me->GetMotionMaster()->Clear();
        me->DespawnOrUnsummon(Milliseconds(100));
    }

    bool MiddleClosed() const
    {
        return _clockMs < _middleUntil;
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (!_launched || !me->IsAlive())
            return;
        if (_clockMs >= _legEndAt)
        {
            _dir = _leg.dirAfter;
            NextLeg();
        }
    }

private:
    void NextLeg()
    {
        Vec2 const pos = DungeonKit::PlaneOf(me);
        _leg = PlanLeg(pos, _dir, MiddleClosed());
        _dir = Vec2{ _leg.end.x - pos.x, _leg.end.y - pos.y };
        float const len = std::sqrt(_dir.x * _dir.x + _dir.y * _dir.y);
        _dir = len > 0.001f ? Vec2{ _dir.x / len, _dir.y / len } : _leg.dirAfter;
        uint32 const ms = std::max<uint32>(kMinLegMs, uint32(_leg.length / kSwarmSpeed * 1000.f));
        _legEndAt = _clockMs + ms;
        if (_leg.length < 0.05f)
            return;
        float const z = FloorZ(me, _leg.end.x, _leg.end.y, kChamberFloorZ);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(1, _leg.end.x, _leg.end.y, z, FORCED_MOVEMENT_NONE, kSwarmSpeed, 0.f, false,
            true);
    }

    Vec2 _dir{ 1.f, 0.f };
    SwarmLeg _leg;
    bool _launched = false;
    uint64 _clockMs = 0;
    uint64 _legEndAt = 0;
    uint64 _middleUntil = 0;
};

// -------------------------------------------------------------------------------------------------------------------
// TheGrandLie: the hard mode for one pull
// -------------------------------------------------------------------------------------------------------------------

class TheGrandLie : public GrandLie
{
public:
    void OnEngage(DathrohanFight& fight) override
    {
        Creature* boss = fight.Boss();
        _instance = boss->GetInstanceScript();
        if (!fight.Heroic())
            return;

        // A retry with the flag still lit (section 7 #10), or a pull while the Letter's speech ran: the mask comes
        // off at the pull, as the Letter does it.
        if (fight.CurrentStage() == StratDathrohan::Stage::Dathrohan)
        {
            boss->AI()->Talk(YELL_DATHROHAN_MASK);
            StratDathrohan::UnmaskOptions unmask;
            unmask.stun = false;
            unmask.marks = false;
            unmask.yell = false;
            fight.Unmask(unmask);
        }
        if (fight.CurrentStage() != StratDathrohan::Stage::Balnazzar)
        {
            fight.Log("hm-engage", Acore::StringFormat("refused stage={}",
                StratDathrohan::StageName(fight.CurrentStage())));
            return;
        }

        _active = true;
        _baseCreateHealth = boss->GetCreateHealth();
        SetCreatureHealth(boss, kHardModeHealth);
        // The instance already rides the bit while the flag is lit; set again here so the hard mode fight carries it
        // after the entry change (LOOT_MODE_HARD_MODE_1: L-2's hard mode list on Balnazzar's heroic lootid).
        DungeonKit::SetHardModeLoot(boss, true);

        uint64 const now = fight.FightMs();
        _act = Act::Lies;
        _nextCallAt = now + kFirstCallMs;
        _callIndex = 0;
        _call.reset();
        _nextSwarmAt = now + kSwarmFirstMs;
        _nextConeAt = now + kConeFirstInActMs;
        _nextInfernoAt = now + kInfernoFirstInActMs;
        _slumberDueAt = 0;
        _slumberLandAt.reset();
        _slumberQueued = false;
        _swarms.clear();
        fight.Log("hm-engage", Acore::StringFormat("health={} was_create={} loot_mode={}", boss->GetMaxHealth(),
            _baseCreateHealth, uint32(boss->GetLootMode())));
    }

    void OnUpdate(DathrohanFight& fight, uint32 /*diff*/) override
    {
        if (!_active)
            return;
        Creature* boss = fight.Boss();
        uint64 const now = fight.FightMs();

        Act const act = NextAct(_act, boss->GetHealthPct());
        if (act != _act)
            EnterAct(fight, act);

        UpdateSwarms(fight);
        if (now >= _nextSwarmAt)
            _nextSwarmAt = now + (SpawnSwarm(fight, nullptr) ? kSwarmEveryMs : kSwarmRetryMs);

        if (!_call && now >= _nextCallAt)
            StartCall(fight, std::nullopt, std::nullopt);
        if (_call)
        {
            for (Piece& piece : _call->pieces)
                if (!piece.fired && now >= piece.yellAt)
                    FirePiece(fight, piece);
            if (now >= _call->landAt + kPieceGapMs)
                _call.reset();
        }

        if (_slumberLandAt && now >= *_slumberLandAt)
            LandSlumber(fight);
    }

    std::optional<uint32> OnCast(DathrohanFight& fight, uint32 id) override
    {
        if (id != CAST_DREAD_SLUMBER || !_active)
            return std::nullopt;
        Creature* boss = fight.Boss();
        uint64 const now = fight.FightMs();
        _slumberQueued = false;
        DungeonKit::CastBar(boss, SPELL_GL_DREAD_SLUMBER, nullptr, YELL_BALNAZZAR_DREAD_SLUMBER);
        _slumberLandAt = now + kSlumberCastMs;
        _slumberDueAt = now + kSlumberEveryMs;
        _nextCallAt = now + kSlumberCastMs + kCallAfterSlumberMs;     // the next call's first yell 3 s after it lands
        fight.Log("hm-dread-slumber", Acore::StringFormat("cast lands={}ms next call={}ms", *_slumberLandAt,
            _nextCallAt));
        return kSlumberCastMs;
    }

    // HM6 / HM7 / HM8: act 1 has no cones or Infernals; act 3 replaces Sleep; no meteor lands in a call's window.
    bool AllowBeat(DathrohanFight& fight, StratDathrohan::Beat beat) override
    {
        if (!_active)
            return true;
        uint64 const now = fight.FightMs();
        switch (beat)
        {
            case StratDathrohan::Beat::CarrionSwarm:
                return _act != Act::Lies && now >= _nextConeAt;
            case StratDathrohan::Beat::Inferno:
            {
                if (_act == Act::Lies || now < _nextInfernoAt)
                    return false;
                std::optional<Window> running;
                if (_call)
                    running = CallWindow(_call->start);
                return !MeteorBlocked(now, running, CallWindow(_nextCallAt));
            }
            case StratDathrohan::Beat::Sleep:
                return _act != Act::GrandLie;
            default:
                return true;
        }
    }

    uint32 BeatEveryMs(DathrohanFight const& fight, StratDathrohan::Beat beat, uint32 baseMs) const override
    {
        if (!_active)
            return baseMs;
        uint64 const now = fight.FightMs();
        switch (beat)
        {
            case StratDathrohan::Beat::CarrionSwarm:
                _nextConeAt = now + kConeEveryMs;
                return kConeEveryMs;
            case StratDathrohan::Beat::Inferno:
                _nextInfernoAt = now + kInfernoEveryMs;
                return kInfernoEveryMs;
            default:
                return baseMs;
        }
    }

    void TuneCarrion(DathrohanFight const& /*fight*/, StratDathrohan::CarrionSpec& spec) const override
    {
        if (!_active)
            return;
        spec.cones = kConeCount;
        spec.targetPct = kConeTargetPct;
        spec.othersPct = kConeOthersPct;
        spec.wardAura = SPELL_GL_STANDARD;
    }

    void TuneInferno(DathrohanFight const& /*fight*/, StratDathrohan::InfernoSpec& spec) const override
    {
        if (!_active)
            return;
        spec.infernalHealth = kInfernalHealth;
        spec.stokes = true;
    }

    float VampiricPct(DathrohanFight const& /*fight*/, float basePct) const override
    {
        return _active ? kVampiricPct : basePct;
    }

    void OnEnd(DathrohanFight& fight, bool died) override
    {
        Creature* boss = fight.Boss();
        for (Swarm const& s : _swarms)
        {
            if (s.zone)
                Mechanic::Cancel(boss, s.zone);
            if (Creature* swarm = ObjectAccessor::GetCreature(*boss, s.guid))
                swarm->DespawnOrUnsummon();
        }
        if (_instance)
            _instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_GL_MARK);
        if (_active && !died && boss->IsAlive() && _baseCreateHealth)
            SetCreatureHealth(boss, _baseCreateHealth);
        fight.Log("hm-end", Acore::StringFormat("died={} act={} calls={} swarms={} slumbers={}", died ? 1 : 0,
            ActName(_act), _callIndex, _swarmsMade, _slumbers));
        _swarms.clear();
        _call.reset();
        _slumberLandAt.reset();
        _active = false;
    }

    // ---- `.dbtest strat grandlie` entry points ------------------------------------------------------------------

    bool Active() const
    {
        return _active;
    }

    bool TestCall(DathrohanFight& fight, std::optional<Twin> twin, std::optional<bool> truth)
    {
        if (!_active || _call)
            return false;
        StartCall(fight, twin, truth);
        return true;
    }

    bool TestSwarm(DathrohanFight& fight, Player* near)
    {
        return _active && SpawnSwarm(fight, near);
    }

    bool TestSlumber(DathrohanFight& fight)
    {
        if (!_active || _slumberQueued || _slumberLandAt)
            return false;
        fight.ScheduleCast(CAST_DREAD_SLUMBER, 0, kSlumberPriority);
        _slumberQueued = true;
        return true;
    }

    bool TestAct(DathrohanFight& fight, Act act)
    {
        if (!_active || static_cast<uint8>(act) <= static_cast<uint8>(_act))
            return false;
        EnterAct(fight, act);
        return true;
    }

    std::string TestState(DathrohanFight& fight)
    {
        Creature* boss = fight.Boss();
        uint64 const now = fight.FightMs();
        std::string out = Acore::StringFormat("t={}ms act={} health={}/{} ({:.1f}%) next call={}ms swarm={}ms "
            "cones={}ms infernal={}ms slumber due={}ms calls={} swarms={}/{}", now, ActName(_act), boss->GetHealth(),
            boss->GetMaxHealth(), boss->GetHealthPct(), _nextCallAt, _nextSwarmAt, _nextConeAt, _nextInfernoAt,
            _slumberDueAt, _callIndex, _swarms.size(), SwarmCap(_act));
        if (_call)
            for (Piece const& p : _call->pieces)
                out += Acore::StringFormat("\n  {} {} yell={}ms fired={}", TwinName(p.twin), p.isTrue ? "true" : "lie",
                    p.yellAt, p.fired ? 1 : 0);
        for (Swarm const& s : _swarms)
            if (Creature* swarm = ObjectAccessor::GetCreature(*boss, s.guid))
                out += Acore::StringFormat("\n  swarm at ({:.1f}, {:.1f}) half {} age {}ms", swarm->GetPositionX(),
                    swarm->GetPositionY(), HalfName(HalfOf(DungeonKit::PlaneOf(swarm))), now - s.bornAt);
        return out;
    }

private:
    struct Piece
    {
        Twin twin = Twin::Cleave;
        bool isTrue = true;
        uint64 yellAt = 0;
        bool fired = false;
    };

    struct Call
    {
        uint64 start = 0;
        uint64 landAt = 0;
        std::vector<Piece> pieces;
    };

    struct Swarm
    {
        ObjectGuid guid;
        MechanicHandle zone;
        uint64 bornAt = 0;
    };

    void EnterAct(DathrohanFight& fight, Act act)
    {
        uint64 const now = fight.FightMs();
        Act const from = _act;
        _act = act;
        if (from == Act::Lies)
        {
            // Act 2's layer: the cones and the Infernals, on their own timers from here.
            _nextConeAt = now + kConeFirstInActMs;
            _nextInfernoAt = now + kInfernoFirstInActMs;
        }
        if (act == Act::GrandLie)
            _slumberDueAt = now + kSlumberFirstInActMs;
        fight.Log("hm-act", Acore::StringFormat("{} -> {} health={:.1f}% cap={}", ActName(from), ActName(act),
            fight.Boss()->GetHealthPct(), SwarmCap(act)));
    }

    // ---- HM1-HM4 the calls ----------------------------------------------------------------------------------------

    void StartCall(DathrohanFight& fight, std::optional<Twin> forcedTwin, std::optional<bool> forcedTruth)
    {
        uint64 const now = fight.FightMs();
        Call call;
        call.start = now;
        call.landAt = now + kCallLandMs;
        std::vector<Twin> const twins = forcedTwin ? std::vector<Twin>{ *forcedTwin } : CallTwins(_act, _callIndex);
        std::string detail;
        for (uint32 i = 0; i < twins.size(); ++i)
        {
            Piece piece;
            piece.twin = twins[i];
            piece.isTrue = forcedTruth ? *forcedTruth : RollTrue(urand(0, 99));
            piece.yellAt = PieceYellAt(now, i);
            call.pieces.push_back(piece);
            detail += Acore::StringFormat(" {}:{}", TwinName(piece.twin), piece.isTrue ? "true" : "lie");
        }
        if (!forcedTwin)
        {
            ++_callIndex;
            _nextCallAt = now + CallEveryMs(_act);
        }
        // HM5: no swarm crosses the middle until the call lands.
        for (Swarm const& s : _swarms)
            if (npc_st_moving_swarm* ai = SwarmAI(fight, s.guid))
                ai->CloseMiddle(kCallLandMs);
        // HM8: the slumber's cast starts 3 s in and lands 2 s after the call.
        bool const slumber = !_slumberQueued && !_slumberLandAt && CallCarriesSlumber(_act, _slumberDueAt, now);
        if (slumber)
        {
            fight.ScheduleCast(CAST_DREAD_SLUMBER, SlumberCastInMs(), kSlumberPriority);
            _slumberQueued = true;
        }
        _call = std::move(call);
        fight.Log("hm-call", Acore::StringFormat("act={} pieces={}{} slumber={}", ActName(_act), twins.size(), detail,
            slumber ? 1 : 0));
    }

    void FirePiece(DathrohanFight& fight, Piece& piece)
    {
        piece.fired = true;
        uint64 const now = fight.FightMs();
        Milliseconds const warn(std::max<int64>(500, int64(_call->landAt) - int64(now)));
        switch (piece.twin)
        {
            case Twin::Cleave: Cleave(fight, piece.isTrue, warn); break;
            case Twin::Ring: Ring(fight, piece.isTrue, warn); break;
            case Twin::Mark: Mark(fight, piece.isTrue, warn); break;
        }
    }

    // HM1: half the room, from the brazier on the measured frame; the struck half is the one with more swarms.
    void Cleave(DathrohanFight& fight, bool isTrue, Milliseconds warn)
    {
        Creature* boss = fight.Boss();
        uint32 inA = 0;
        uint32 inB = 0;
        for (Swarm const& s : _swarms)
            if (Creature* swarm = ObjectAccessor::GetCreature(*boss, s.guid))
                ++(HalfOf(DungeonKit::PlaneOf(swarm)) == Half::A ? inA : inB);
        Half const struck = StruckHalf(inA, inB, urand(0, 1) == 0);
        Half const claimed = ClaimedHalf(struck, isTrue);
        boss->AI()->Talk(YellOf(Twin::Cleave, isTrue));

        Position const struckApex(kDathrohanBrazier.x, kDathrohanBrazier.y, kChamberFloorZ, HalfFacing(struck));
        MechanicRef hit = Mechanic::Zone(boss, BossMechanics::Shapes::Cone(struckApex, kCleaveAngleDeg,
            kCleaveLengthYd), warn);
        hit.Damage(kTwinPct).School(isTrue ? SPELL_SCHOOL_HOLY : SPELL_SCHOOL_SHADOW)
            .Spell(isTrue ? SPELL_GL_CLEAVE_LIGHT : SPELL_GL_CLEAVE_BLADE).Eligible(NonTanks())
            .Within(fight.RoomBounds()).NoTelegraph().Tag(TAG_GL_CLEAVE).OnHit(VampiricOnHit(boss, "hm-cleave"));
        fight.Track(hit.Handle());

        Position const claimApex(kDathrohanBrazier.x, kDathrohanBrazier.y, kChamberFloorZ, HalfFacing(claimed));
        MechanicRef claim = Mechanic::Zone(boss, BossMechanics::Shapes::Cone(claimApex, kCleaveAngleDeg,
            kCleaveLengthYd), warn);
        claim.Decoy().Color(BossMechanics::Color::Yellow).Tag(TAG_GL_CLAIM);
        fight.Track(claim.Handle());
        fight.Log("hm-cleave", Acore::StringFormat("{} struck={} claimed={} swarms A={} B={} warn={}ms",
            isTrue ? "true" : "lie", HalfName(struck), HalfName(claimed), inA, inB, warn.count()));
    }

    // HM2: the 10 yd circle on him (true) or the 10-40 yd donut (lie); the claim is the circle either way.
    void Ring(DathrohanFight& fight, bool isTrue, Milliseconds warn)
    {
        Creature* boss = fight.Boss();
        boss->AI()->Talk(YellOf(Twin::Ring, isTrue));
        if (isTrue)
        {
            MechanicRef hit = Mechanic::Circle(boss, boss, kRingRadius, warn);
            hit.Damage(kTwinPct).School(SPELL_SCHOOL_HOLY).Spell(SPELL_GL_RING_LIGHT).Eligible(NonTanks())
                .Within(fight.RoomBounds()).NoTelegraph().Tag(TAG_GL_RING).OnHit(VampiricOnHit(boss, "hm-ring"));
            fight.Track(hit.Handle());
        }
        else
        {
            MechanicRef hit = Mechanic::Donut(boss, boss, kRingRadius, kRingOuter, warn);
            hit.Damage(kTwinPct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_GL_RING_DARK).Eligible(NonTanks())
                .Within(fight.RoomBounds()).NoTelegraph().Tag(TAG_GL_RING).OnHit(VampiricOnHit(boss, "hm-ring"));
            fight.Track(hit.Handle());
        }
        MechanicRef claim = Mechanic::Circle(boss, boss, kRingRadius, warn);
        claim.Decoy().Color(BossMechanics::Color::Red).Tag(TAG_GL_CLAIM);
        fight.Track(claim.Handle());
        fight.Log("hm-ring", Acore::StringFormat("{} warn={}ms", isTrue ? "true" : "lie", warn.count()));
    }

    // HM3: a stack marker on a random non-tank; true, the 6 yd Stack and the 100% split; lie, a 7 yd Spread on every
    // non-tank at 50%.
    void Mark(DathrohanFight& fight, bool isTrue, Milliseconds warn)
    {
        Creature* boss = fight.Boss();
        Player* target = PickNonTank(boss);
        if (!target)
        {
            fight.Log("hm-mark", "no target");
            return;
        }
        boss->AI()->Talk(YellOf(Twin::Mark, isTrue), target);
        boss->CastSpell(target, SPELL_GL_MARK, true);
        DungeonKit::ShortenAura(target, SPELL_GL_MARK, boss->GetGUID(), warn);
        ObjectGuid const targetGuid = target->GetGUID();
        if (isTrue)
        {
            MechanicRef hit = Mechanic::Stack(boss, target, kMarkStackRadius, warn);
            hit.Eligible(NonTanks()).Within(fight.RoomBounds()).NoTelegraph().Tag(TAG_GL_MARK)
                .OnResolve(OnGrandLie(boss, [targetGuid](TheGrandLie& gl, DathrohanFight& f,
                    BossMechanics::ResolveResult const& r)
                {
                    gl.MarkShares(f, targetGuid, r);
                }));
            fight.Track(hit.Handle());
        }
        else
        {
            MechanicRef hit = Mechanic::Spread(boss, kMarkSpreadRadius, warn);
            hit.Damage(kTwinPct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_GL_MARK_BURST).Eligible(NonTanks())
                .Within(fight.RoomBounds()).NoTelegraph().Tag(TAG_GL_MARK).OnHit(VampiricOnHit(boss, "hm-mark"));
            fight.Track(hit.Handle());
        }
        MechanicRef claim = Mechanic::Circle(boss, target, kMarkStackRadius, warn);
        claim.Decoy().Color(BossMechanics::Color::Blue).Tag(TAG_GL_CLAIM);
        fight.Track(claim.Handle());
        fight.Log("hm-mark", Acore::StringFormat("{} target={} warn={}ms", isTrue ? "true" : "lie", target->GetName(),
            warn.count()));
    }

public:
    // HM3 true: 100% split evenly among the non-tanks inside the stack and the marked player.
    void MarkShares(DathrohanFight& fight, ObjectGuid targetGuid, BossMechanics::ResolveResult const& result)
    {
        Creature* boss = fight.Boss();
        Player* target = ObjectAccessor::GetPlayer(*boss, targetGuid);
        if (target)
            target->RemoveAurasDueToSpell(SPELL_GL_MARK);
        std::vector<Unit*> takers;
        for (ObjectGuid const& g : result.hits)
            if (Player* p = ObjectAccessor::GetPlayer(*boss, g))
                if (p->IsAlive())
                    takers.push_back(p);
        if (target && target->IsAlive() && std::find(takers.begin(), takers.end(), target) == takers.end())
            takers.push_back(target);
        std::vector<std::pair<ObjectGuid, uint32>> const shares = DungeonKit::SplitShares(boss, takers,
            kMarkSplitPct);
        std::string detail;
        for (std::size_t i = 0; i < takers.size() && i < shares.size(); ++i)
        {
            detail += Acore::StringFormat(" {}:{}", takers[i]->GetName(), shares[i].second);
            if (!shares[i].second)
                continue;
            boss->CastCustomSpell(SPELL_GL_MARK_SHARE, SPELLVALUE_BASE_POINT0, static_cast<int32>(shares[i].second),
                takers[i], TRIGGERED_FULL_MASK);
            fight.VampiricHit(takers[i], "hm-mark-share");
        }
        fight.Log("hm-mark-share", Acore::StringFormat("takers={}{}", takers.size(), detail));
    }

    // Blessed Holy Water landed at `at`: every swarm within the splash disperses.
    uint32 Splash(DathrohanFight& fight, Position const& at, Player* thrower)
    {
        Creature* boss = fight.Boss();
        uint32 dispersed = 0;
        for (auto it = _swarms.begin(); it != _swarms.end();)
        {
            Creature* swarm = ObjectAccessor::GetCreature(*boss, it->guid);
            if (!swarm || swarm->GetExactDist2d(at.GetPositionX(), at.GetPositionY()) > kHolyWaterSplashYd)
            {
                ++it;
                continue;
            }
            if (it->zone)
                Mechanic::Cancel(boss, it->zone);
            if (auto* ai = dynamic_cast<npc_st_moving_swarm*>(swarm->AI()))
                ai->Disperse();
            else
                swarm->DespawnOrUnsummon();
            it = _swarms.erase(it);
            ++dispersed;
        }
        fight.Log("hm-holy-water", Acore::StringFormat("by={} at=({:.1f}, {:.1f}) dispersed={} left={}",
            thrower ? thrower->GetName() : "?", at.GetPositionX(), at.GetPositionY(), dispersed, _swarms.size()));
        return dispersed;
    }

private:
    // ---- HM5 the swarms --------------------------------------------------------------------------------------------

    npc_st_moving_swarm* SwarmAI(DathrohanFight& fight, ObjectGuid guid)
    {
        Creature* swarm = ObjectAccessor::GetCreature(*fight.Boss(), guid);
        return swarm && swarm->IsAlive() && swarm->IsAIEnabled ? dynamic_cast<npc_st_moving_swarm*>(swarm->AI())
            : nullptr;
    }

    // A new swarm out of the wall (at the act's cap: none). `near` (a test): from the wall nearest that player.
    bool SpawnSwarm(DathrohanFight& fight, Player* near)
    {
        if (_swarms.size() >= SwarmCap(_act))
            return false;
        Creature* boss = fight.Boss();
        float bearing = SpawnBearing(float(urand(0, 9999)) / 10000.f);
        if (near)
            bearing = std::atan2(near->GetPositionY() - kDathrohanBrazier.y,
                near->GetPositionX() - kDathrohanBrazier.x);
        SwarmStart const start = SwarmSpawn(bearing, frand(0.f, 6.2831853f), frand(0.f, kSwarmAimRadius));
        float const z = FloorZ(boss, start.at.x, start.at.y, kChamberFloorZ);
        float const facing = std::atan2(start.dir.y, start.dir.x);
        Creature* swarm = boss->SummonCreature(NPC_ST_SWARM, start.at.x, start.at.y, z, facing,
            TEMPSUMMON_TIMED_DESPAWN, kSwarmLifeMs + 1000);
        if (!swarm)
            return false;
        auto* ai = dynamic_cast<npc_st_moving_swarm*>(swarm->AI());
        if (ai)
        {
            ai->Launch(start.dir);
            if (_call && fight.FightMs() < _call->landAt)
                ai->CloseMiddle(uint32(_call->landAt - fight.FightMs()));
        }
        MechanicRef zone = Mechanic::Circle(boss, swarm, kSwarmRadius, Milliseconds(kSwarmGraceMs));
        zone.Persistent(Milliseconds(kSwarmLifeMs - kSwarmGraceMs), Milliseconds(kSwarmTickMs))
            .Damage(kSwarmTickPct).TankDamage(kSwarmTickPct).School(SPELL_SCHOOL_SHADOW).Spell(SPELL_GL_SWARM_BITE)
            .Weakened().Eligible(Unwarded()).Within(fight.RoomBounds()).Tag(TAG_GL_SWARM)
            .OnHit(VampiricOnHit(boss, "hm-swarm"));
        _swarms.push_back({ swarm->GetGUID(), zone.Handle(), fight.FightMs() });
        ++_swarmsMade;
        fight.Log("hm-swarm", Acore::StringFormat("at=({:.1f}, {:.1f}) half={} dir={:.2f} live={}/{} ai={}",
            start.at.x, start.at.y, HalfName(HalfOf(start.at)), facing, _swarms.size(), SwarmCap(_act), ai ? 1 : 0));
        return true;
    }

    // The swarms that broke up (30 s), were dispersed or despawned: their zones go with them.
    void UpdateSwarms(DathrohanFight& fight)
    {
        Creature* boss = fight.Boss();
        uint64 const now = fight.FightMs();
        for (auto it = _swarms.begin(); it != _swarms.end();)
        {
            Creature* swarm = ObjectAccessor::GetCreature(*boss, it->guid);
            bool const gone = !swarm || !swarm->IsAlive() || !swarm->IsInWorld();
            if (!gone && now < it->bornAt + kSwarmLifeMs)
            {
                ++it;
                continue;
            }
            if (it->zone)
                Mechanic::Cancel(boss, it->zone);
            if (!gone)
                swarm->DespawnOrUnsummon();
            fight.Log("hm-swarm-gone", Acore::StringFormat("why={} live={}", gone ? "dispersed" : "broke-up",
                _swarms.size() - 1));
            it = _swarms.erase(it);
        }
    }

    // ---- HM8 Dread Slumber -----------------------------------------------------------------------------------------

    void LandSlumber(DathrohanFight& fight)
    {
        _slumberLandAt.reset();
        ++_slumbers;
        std::vector<ObjectGuid> slept;
        uint32 warded = 0;
        for (Player* p : fight.FightPlayers())
        {
            if (p->HasAura(SPELL_GL_MEDALLION))
            {
                ++warded;
                continue;
            }
            if (fight.SleepPlayer(p, false))
                slept.push_back(p->GetGUID());
        }
        fight.Log("hm-dread-slumber-land", Acore::StringFormat("slept={} warded={}", Guids(slept), warded));
    }

    // Runs `fn(grandLie, fight, result)` when a mechanic resolves, if this pull's hard mode is still there. Captures
    // the map and the boss's guid only (a lambda the registry keeps must not hold a pointer).
    template <typename Fn>
    static std::function<void(BossMechanics::ResolveResult const&)> OnGrandLie(Creature* boss, Fn fn)
    {
        Map* map = boss->GetMap();
        ObjectGuid const guid = boss->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* creature = map->GetCreature(guid);
            if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
                return;
            auto* fight = dynamic_cast<DathrohanFight*>(creature->AI());
            auto* gl = fight ? dynamic_cast<TheGrandLie*>(fight->ActiveHardMode()) : nullptr;
            if (gl && gl->Active())
                fn(*gl, *fight, result);
        };
    }

    InstanceScript* _instance = nullptr;
    bool _active = false;
    Act _act = Act::Lies;
    std::optional<Call> _call;
    std::vector<Swarm> _swarms;
    std::optional<uint64> _slumberLandAt;
    uint64 _nextCallAt = 0;
    uint64 _nextSwarmAt = 0;
    mutable uint64 _nextConeAt = 0;         // BeatEveryMs (const) moves them when the beat fires
    mutable uint64 _nextInfernoAt = 0;
    uint64 _slumberDueAt = 0;
    uint32 _callIndex = 0;
    uint32 _swarmsMade = 0;
    uint32 _slumbers = 0;
    uint32 _baseCreateHealth = 0;
    bool _slumberQueued = false;
};

namespace
{
    // The pull's hard mode, from anything on the map (the relic spell scripts, the test commands).
    TheGrandLie* GrandLieOf(WorldObject const& near, DathrohanFight*& fight)
    {
        fight = nullptr;
        InstanceScript* instance = near.GetInstanceScript();
        Creature* boss = instance ? instance->GetCreature(DATA_DATHROHAN_GUID) : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        fight = dynamic_cast<DathrohanFight*>(boss->AI());
        auto* gl = fight ? dynamic_cast<TheGrandLie*>(fight->ActiveHardMode()) : nullptr;
        return gl && gl->Active() ? gl : nullptr;
    }

    // The Letter of Proof's checks, from `reader` (a player in the instance).
    LetterRefusal CheckLetterFor(Player* reader, Creature*& dathrohan)
    {
        InstanceScript* instance = reader->GetInstanceScript();
        dathrohan = instance ? instance->GetCreature(DATA_DATHROHAN_GUID) : nullptr;
        LetterCheck c;
        c.heroic = instance && DungeonKit::IsHeroicMap(reader);
        c.wave2Bound = kWave2Bound;
        c.dathrohanHere = dathrohan && dathrohan->IsAlive() && dathrohan->GetEntry() == NPC_DATHROHAN;
        c.distance = dathrohan ? reader->GetDistance(dathrohan) : 0.f;
        c.inSight = !dathrohan || reader->IsWithinLOSInMap(dathrohan);
        c.inCombat = dathrohan && dathrohan->IsInCombat();
        c.balnazzarState = instance ? uint32(instance->GetBossState(BOSS_BALNAZZAR)) : 0;
        return CheckLetter(c);
    }

    // The Letter read to Dathrohan: the flag, line 8; 2.5 s later line 9, the mask off (no stun), and he attacks the
    // reader. A pull in between starts the hard mode at the pull (TheGrandLie::OnEngage); the speech then stops.
    bool ReadLetter(Player* reader, Creature* dathrohan)
    {
        InstanceScript* instance = reader->GetInstanceScript();
        if (!instance || !dathrohan)
            return false;
        instance->SetData(DATA_GRAND_LIE, 1);
        if (instance->GetData(DATA_GRAND_LIE) != 1)
            return false;
        dathrohan->SetFacingToObject(reader);
        dathrohan->AI()->Talk(SAY_DATHROHAN_LETTER, reader);
        DungeonKit::LogMechanic(kLogDungeon, "balnazzar", "hm-letter", Acore::StringFormat("reader={}",
            reader->GetName()));
        ObjectGuid const readerGuid = reader->GetGUID();
        dathrohan->m_Events.AddEventAtOffset([dathrohan, readerGuid]()
        {
            if (!dathrohan->IsAlive() || dathrohan->IsInCombat() || dathrohan->GetEntry() != NPC_DATHROHAN ||
                !dathrohan->IsAIEnabled)
                return;
            InstanceScript* inst = dathrohan->GetInstanceScript();
            if (!inst || inst->GetData(DATA_GRAND_LIE) != 1)
                return;
            auto* fight = dynamic_cast<DathrohanFight*>(dathrohan->AI());
            if (!fight)
                return;
            dathrohan->AI()->Talk(YELL_DATHROHAN_MASK);
            StratDathrohan::UnmaskOptions unmask;
            unmask.stun = false;
            unmask.marks = false;
            unmask.yell = false;
            if (!fight->Unmask(unmask))
                return;
            Player* who = ObjectAccessor::GetPlayer(*dathrohan, readerGuid);
            if (who && who->IsAlive() && !who->IsGameMaster() && who->GetMap() == dathrohan->GetMap())
                dathrohan->AI()->AttackStart(who);
            else if (Player* nearest = dathrohan->SelectNearestPlayer(60.f))
                dathrohan->AI()->AttackStart(nearest);
        }, Milliseconds(kLetterSpeechMs));
        return true;
    }
}

// -------------------------------------------------------------------------------------------------------------------
// The relic spots (301203-301206, heroic spawns): hidden and not clickable until their boss is dead (RelicShown); a
// click gives one copy of the spot's item to everyone in the group on the map (KT-2's RelicDispenserAI).
// -------------------------------------------------------------------------------------------------------------------

struct go_st_grand_lie_relic : public DungeonKit::RelicDispenserAI
{
    explicit go_st_grand_lie_relic(GameObject* go) : RelicDispenserAI(go, RelicItem(go->GetEntry()), kLogDungeon) { }

    bool CanBeSeen(Player const* /*seer*/) override
    {
        return Shown();
    }

    bool CanDispense(Player* /*user*/) override
    {
        return Shown();
    }

    void UpdateAI(uint32 diff) override
    {
        if (_pollMs > diff)
        {
            _pollMs -= diff;
            return;
        }
        _pollMs = kRelicPollMs;
        bool const shown = Shown();
        bool const flagged = me->HasGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (shown && flagged)
            me->RemoveGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        else if (!shown && !flagged)
            me->SetGameObjectFlag(GO_FLAG_NOT_SELECTABLE);
        if (!_synced || shown != _lastShown)
        {
            _synced = true;
            _lastShown = shown;
            me->UpdateObjectVisibility(true);
            if (shown)
                DungeonKit::LogMechanic(kLogDungeon, "balnazzar", "hm-relic-shown", Acore::StringFormat(
                    "go={} item={}", me->GetEntry(), ItemId()));
        }
    }

private:
    bool Shown() const
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return false;
        std::optional<uint32> const boss = RelicBoss(me->GetEntry());
        uint32 const state = boss ? uint32(instance->GetBossState(*boss)) : 0;
        return RelicShown(me->GetEntry(), DungeonKit::IsHeroicMap(me), kWave2Bound, state);
    }

    uint32 _pollMs = 0;
    bool _synced = false;
    bool _lastShown = false;
};

// -------------------------------------------------------------------------------------------------------------------
// The relic and Letter use spells (their items' spellid_1; declared in apps/dbc-tools
// source/npcs/stratholme/balnazzar_hard_mode.py)
// -------------------------------------------------------------------------------------------------------------------

// 206585 the Letter of Proof: on the reader (a DUMMY on the caster, so no hostile hit starts the fight early); the
// checks name Dathrohan within 30 yd, out of combat, on heroic.
class spell_strat_grand_lie_letter : public SpellScript
{
    PrepareSpellScript(spell_strat_grand_lie_letter);

    SpellCastResult CheckCast()
    {
        Player* reader = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!reader)
            return SPELL_FAILED_BAD_TARGETS;
        Creature* dathrohan = nullptr;
        LetterRefusal const why = CheckLetterFor(reader, dathrohan);
        if (why == LetterRefusal::None)
            return SPELL_CAST_OK;
        ChatHandler(reader->GetSession()).SendNotification(std::string_view(LetterRefusalText(why)));
        return SPELL_FAILED_DONT_REPORT;
    }

    void Read(SpellEffIndex /*effIndex*/)
    {
        Player* reader = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!reader)
            return;
        Creature* dathrohan = nullptr;
        if (CheckLetterFor(reader, dathrohan) == LetterRefusal::None)
            ReadLetter(reader, dathrohan);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_strat_grand_lie_letter::CheckCast);
        OnEffectHit += SpellEffectFn(spell_strat_grand_lie_letter::Read, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 206586 Blessed Holy Water: thrown at a spot (TARGET_DEST_DEST, 10 yd); the 5 yd splash disperses the swarms in it.
class spell_strat_grand_lie_holy_water : public SpellScript
{
    PrepareSpellScript(spell_strat_grand_lie_holy_water);

    void Splash(SpellEffIndex /*effIndex*/)
    {
        WorldLocation const* dest = GetHitDest();
        Unit* caster = GetCaster();
        if (!dest || !caster)
            return;
        DathrohanFight* fight = nullptr;
        if (TheGrandLie* gl = GrandLieOf(*caster, fight))
            gl->Splash(*fight, *dest, caster->ToPlayer());
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_strat_grand_lie_holy_water::Splash, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 206588 the Medallion's pulse: the 4 s sleep ward is the aura (mechanic immunity, Sleep); it also wakes every sleeper
// it reaches (S7's Sleep aura removed as a dispel would: Nightmare still follows).
class spell_strat_grand_lie_medallion : public SpellScript
{
    PrepareSpellScript(spell_strat_grand_lie_medallion);

    void Wake(SpellEffIndex /*effIndex*/)
    {
        Unit* target = GetHitUnit();
        if (target && target->HasAura(StratDathrohan::SPELL_BZ_SLEEP))
            target->RemoveAurasDueToSpell(StratDathrohan::SPELL_BZ_SLEEP, ObjectGuid::Empty, 0,
                AURA_REMOVE_BY_ENEMY_SPELL);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_strat_grand_lie_medallion::Wake, EFFECT_0, SPELL_EFFECT_APPLY_AURA);
    }
};

// -------------------------------------------------------------------------------------------------------------------
// `.dbtest strat grandlie`
// -------------------------------------------------------------------------------------------------------------------

namespace
{
    TheGrandLie* FindGrandLie(ChatHandler* handler, DathrohanFight*& fight)
    {
        fight = nullptr;
        if (!StratTest::RequireStratholme(handler))
            return nullptr;
        TheGrandLie* gl = GrandLieOf(*handler->GetPlayer(), fight);
        if (!gl)
            handler->SendErrorMessage("{}", "No Grand Lie on this pull (heroic; `.dbtest strat grandlie letter` "
                "reads the Letter to Dathrohan, or light DATA_GRAND_LIE and pull him).");
        return gl;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        if (!StratTest::RequireStratholme(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        handler->PSendSysMessage("grandlie: flag {}, kill {}, boss {}, relic bosses galford {} malor {} willey {}",
            instance->GetData(DATA_GRAND_LIE), DungeonTest::StateName(instance->GetBossState(BOSS_GRAND_LIE)),
            DungeonTest::StateName(instance->GetBossState(BOSS_BALNAZZAR)),
            DungeonTest::StateName(instance->GetBossState(BOSS_GALFORD)),
            DungeonTest::StateName(instance->GetBossState(BOSS_MALOR)),
            DungeonTest::StateName(instance->GetBossState(BOSS_WILLEY)));
        return true;
    }

    // `.dbtest strat grandlie letter`: the GM reads the Letter (the same checks and start as the item).
    bool HandleLetter(ChatHandler* handler)
    {
        if (!StratTest::RequireStratholme(handler))
            return false;
        Player* gm = handler->GetPlayer();
        Creature* dathrohan = nullptr;
        LetterRefusal const why = CheckLetterFor(gm, dathrohan);
        if (why != LetterRefusal::None)
        {
            handler->SendErrorMessage("{}", LetterRefusalText(why));
            return false;
        }
        bool const ok = ReadLetter(gm, dathrohan);
        handler->PSendSysMessage("grandlie: {}", ok ? "the Letter is read; the mask comes off in 2.5 s."
            : "the instance refused the flag.");
        return true;
    }

    bool HandleState(ChatHandler* handler)
    {
        DathrohanFight* fight = nullptr;
        TheGrandLie* gl = FindGrandLie(handler, fight);
        if (!gl)
            return false;
        handler->PSendSysMessage("Grand Lie: {}", gl->TestState(*fight));
        return true;
    }

    // `.dbtest strat grandlie call [cleave|ring|mark] [true|lie]`: one call now (no twin: the act's next call).
    bool HandleCall(ChatHandler* handler, Optional<std::string> twinArg, Optional<std::string> truthArg)
    {
        DathrohanFight* fight = nullptr;
        TheGrandLie* gl = FindGrandLie(handler, fight);
        if (!gl)
            return false;
        std::optional<Twin> twin;
        if (twinArg)
        {
            if (*twinArg == "cleave")
                twin = Twin::Cleave;
            else if (*twinArg == "ring")
                twin = Twin::Ring;
            else if (*twinArg == "mark")
                twin = Twin::Mark;
            else
            {
                handler->SendErrorMessage("{}", "twin: cleave, ring or mark");
                return false;
            }
        }
        std::optional<bool> truth;
        if (truthArg)
            truth = *truthArg == "true";
        bool const ok = gl->TestCall(*fight, twin, truth);
        handler->PSendSysMessage("Grand Lie: {}", ok ? "a call starts (HM1-HM4)." : "a call is already running.");
        return true;
    }

    // `.dbtest strat grandlie swarm`: a swarm now, out of the wall nearest the GM (at the act's cap: none).
    bool HandleSwarm(ChatHandler* handler)
    {
        DathrohanFight* fight = nullptr;
        TheGrandLie* gl = FindGrandLie(handler, fight);
        if (!gl)
            return false;
        bool const ok = gl->TestSwarm(*fight, handler->GetPlayer());
        handler->PSendSysMessage("Grand Lie: {}", ok ? "a swarm crawls out (HM5)." : "the swarm cap is reached.");
        return true;
    }

    // `.dbtest strat grandlie slumber`: Dread Slumber through his cast queue now.
    bool HandleSlumber(ChatHandler* handler)
    {
        DathrohanFight* fight = nullptr;
        TheGrandLie* gl = FindGrandLie(handler, fight);
        if (!gl)
            return false;
        bool const ok = gl->TestSlumber(*fight);
        handler->PSendSysMessage("Grand Lie: {}", ok ? "Dread Slumber is queued (HM8)." : "one is already queued.");
        return true;
    }

    // `.dbtest strat grandlie act <2|3>`: the next act now.
    bool HandleAct(ChatHandler* handler, uint8 act)
    {
        DathrohanFight* fight = nullptr;
        TheGrandLie* gl = FindGrandLie(handler, fight);
        if (!gl)
            return false;
        if (act < 2 || act > 3)
        {
            handler->SendErrorMessage("{}", "act: 2 or 3");
            return false;
        }
        bool const ok = gl->TestAct(*fight, static_cast<Act>(act));
        handler->PSendSysMessage("Grand Lie: {}", ok ? "the act begins." : "that act is behind us.");
        return true;
    }

    ChatCommandTable const& GrandLieTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",    HandleInfo,    SEC_GAMEMASTER, Console::No },
            { "letter",  HandleLetter,  SEC_GAMEMASTER, Console::No },
            { "state",   HandleState,   SEC_GAMEMASTER, Console::No },
            { "call",    HandleCall,    SEC_GAMEMASTER, Console::No },
            { "swarm",   HandleSwarm,   SEC_GAMEMASTER, Console::No },
            { "slumber", HandleSlumber, SEC_GAMEMASTER, Console::No },
            { "act",     HandleAct,     SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_strat_balnazzar_hard_mode()
{
    StratDathrohan::RegisterGrandLie([](Creature* /*boss*/) { return std::make_unique<TheGrandLie>(); });
    RegisterDungeonReworkCreatureAI(npc_st_moving_swarm, StratholmeRework::kInstanceScriptName);
    RegisterDungeonReworkGameObjectAI(go_st_grand_lie_relic, StratholmeRework::kInstanceScriptName);
    RegisterSpellScript(spell_strat_grand_lie_letter);
    RegisterSpellScript(spell_strat_grand_lie_holy_water);
    RegisterSpellScript(spell_strat_grand_lie_medallion);
    StratTest::RegisterBoss("grandlie", GrandLieTestCommands());
}
