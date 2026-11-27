/*
 * mod-dungeon-bosses, Gnomeregan D3: Electrocutioner 6000 (6235), the end of section 1, normal and heroic. Build spec:
 * SP 803-1006 (EL1-EL6, Build spec 958), rulings 21-24; handoff section 3.5 row D3, rules 1-38 and the kick and
 * dispel table, sections 3.6, 3.8 (the platform), 3.9 row 5, section 7 #9 A, #12 A, #20 A, #36-#38 A, section 10.
 * Replaces SmartAI 6235 (dropped by rev_skeleton_gnomeregan.sql: Chain Bolt 11085, Megavolt 11082, Shock 11084 and the
 * aggro yell; every stock spell is re-made as a copy in the slice, rule 16). Bound by apps/dbc-tools
 * source/npcs/gnomeregan/electrocutioner.py; numbers in ElectrocutionerLogic.h, health in GnomereganRework.h Health;
 * the texts in rev_electrocutioner_gnomeregan.sql.
 *
 *   Pull       the aggro yell (group 1); he walks to the platform's center (section 7 #20 A; his spawn is 2.3 yd off
 *              it) and is held there by SetControlled(ROOT) (rule 8); a walk that does not arrive is finished by a
 *              teleport. Every pick stands on the Justice's floor (rule 5, RF-1 DQ1: the disc, the rim and the
 *              walkway; Megavolt within its 30 yd cone, Shock within 20 yd); the bots' spots stay on the 21 yd disc.
 *   EL1, EL2   the VoltageMeter machine (ElectrocutionerMachine.h): Voltage +1 every 5 s and per mistake; Electric
 *              Justice at 6 (heroic every 6th), a 4 s Physical bar, the donut safe within 8 yd out over the platform
 *              and the walkway (heroic in turn with the 15 yd circle on him), 75%; normal resets to 0 and pauses 10 s
 *              after the bar.
 *   EL3        Megavolt: every 12 s (first 10 s) a 2 s Physical bar, the 40 degree / 30 yd cone fixed at the bar's
 *              start toward a random player (tank included; heroic two cones at two players), 40% / 60% and
 *              Weakened, +1 V (heroic +2) per player hit. HoldTankFacing: the bot tank never walks round him for it.
 *   EL4        Chain Bolt: first at 3 s, then every 20 s, a 2.5 s Nature cast (kickable: the descriptor's interrupt) at
 *              a random player, a registry Spread of 6 yd (heroic 10) for the bots meanwhile; when it lands the script
 *              jumps it (ChainOrder: the nearest unstruck player within 6 / 10 yd of the last, at most 2 jumps; heroic
 *              no limit), 20% each (heroic 40%, each jump 25% more), +1 V a jump. A kick stops it whole.
 *   EL5        Shock: first at 6 s, then every 8 s, an instant Nature cast at a random player within 20 yd, 10% / 15%
 *              (a kick's Nature lockout refuses it: the reward, not retried).
 *   EL6        Static (heroic): every player's yards moved (250 ms samples, ElectrocutionerLogic.h StaticCharge) as the
 *              stack count of SPELL_STATIC; at 20 a discharge: 40% and Weakened on the carrier, 40% on the nearest
 *              ally within 10 yd, +1 V. Counted from 5 s after the pull and on the pick floor only (the platform
 *              and the walkway; a fall holds it). The descriptor carries BM-G's move cost (above 12) and the 11-12
 *              yd band.
 *   Heroic     every lightning hit times the meter's DamageMultiplier (3% a stack, no cap), read when it is drawn.
 *   RB-4       a held boss answers: his victim out of melee reach for 5 s is Shocked every 3 s.
 *   Death      the instance unlocks the Workshop Door and summons End NPC 1 on normal (STAGE-S0 Q1): nothing here. The
 *              Workshop Key 6893 stays on his loot (ruling 58).
 *
 * Every firing logs one INFO line "gnomer-build electro <mechanic> ..."; `.dbtest gnomer electro <mechanic>` fires one
 * (justice, megavolt, chainbolt, shock, voltage, static) and `state` prints the meter.
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "ElectrocutionerLogic.h"
#include "ElectrocutionerMachine.h"
#include "GnomereganKit.h"
#include "GnomereganRework.h"
#include "GnomereganTestCommand.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace GnomereganRework;
using namespace GnomerElectro;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kKey = "electro";

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogEl(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kKey, mechanic, detail);
    }

    bool CountsAsPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }
}

// Electrocutioner 6000 6235
struct boss_electrocutioner_rework : public BossAI
{
    explicit boss_electrocutioner_rework(Creature* creature)
        : BossAI(creature, BOSS_ELECTROCUTIONER), _arena(PlatformArena(), LeashOptions(kKey)),
        _bounds(ElectrocutionerFloorBounds())
    {
    }

    void Reset() override
    {
        Cleanup("reset");
        _Reset();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        Cleanup("pull");    // a `.dbtest` mechanic out of combat may have left something behind
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _megavoltAt = Tune::kMegavoltFirstMs;
        _chainAt = Tune::kChainFirstMs;
        _shockAt = Tune::kShockFirstMs;
        GnomereganMachines::MachineOwner owner{ me, kKey, _heroic };
        _meter = GnomereganMachines::MakeElectroVoltageMeter(owner,
            GnomereganMachines::ElectrocutionerVoltageSpec(_heroic));
        _meter->SetBotBounds(_bounds);

        Talk(SAY_AGGRO);
        OnBossPull(me, kKey);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_ELECTROCUTIONER;
        Mechanic::BeginEncounter(me, options);
        Describe();
        Mechanic::NoteNextCastIn(me, SPELL_CHAIN_BOLT, Ms(Tune::kChainFirstMs));
        _arena.Engage(me);
        StartCenterWalk();
        LogEl("engage", Acore::StringFormat("heroic={} who={} from={:.1f}", _heroic ? 1 : 0, who ? who->GetName() : "-",
            DungeonKit::Distance(DungeonKit::PlaneOf(me), kPlatformCenter.XY())));
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        LogEl("evade", Acore::StringFormat("reason={} stacks={}", uint32(why), _meter ? _meter->Stacks() : 0));
        Cleanup("evade");
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        LogEl("death", Acore::StringFormat("killer={} justices={} megavolts={} chainbolts={} kicked={} shocks={} "
            "discharges={} stacks={}", killer ? killer->GetName() : "-", _meter ? _meter->Justices() : 0, _megavolts,
            _chainBolts, _kicked, _shocks, _discharges, _meter ? _meter->Stacks() : 0));
        BossAI::JustDied(killer);
        Cleanup("death");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        // Held on the next tick, outside the motion master's own update.
        if (type == POINT_MOTION_TYPE && id == kPointCenter && _walking)
            _arrived = true;
    }

    // EL4: the bar finished, the bolt lands on its target and jumps.
    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_CHAIN_BOLT)
            ResolveChainBolt();
    }

    // EL4: a kick (the reward: no hit, no charge) or anything else that ended the bar.
    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell || spell->Id != SPELL_CHAIN_BOLT || _chainTarget.IsEmpty())
            return;
        ++_kicked;
        LogEl("chain-bolt-stopped", Acore::StringFormat("target={} kicked={}", _chainName, _kicked));
        EndChainBar();
    }

    void DoAction(int32 action) override
    {
        if (!_engaged || !_meter)
            return;
        switch (action)
        {
            case ACTION_TEST_JUSTICE:
            {
                uint32 const missing = _meter->ToNext();
                if (missing > 0)
                    _meter->Add(missing, "test");
                break;
            }
            case ACTION_TEST_MEGAVOLT:
                _megavoltAt = _now;
                break;
            case ACTION_TEST_CHAIN_BOLT:
                _chainAt = _now;
                break;
            case ACTION_TEST_SHOCK:
                _shockAt = _now;
                break;
            case ACTION_TEST_VOLTAGE:
                _meter->Add(1, "test");
                break;
            case ACTION_TEST_STATIC:
                if (_heroic)
                    for (auto& [guid, charge] : _static)
                        charge.Set(Tune::kStaticDischargeAt - 1.f);
                break;
            default:
                break;
        }
    }

    uint32 GetData(uint32 id) const override
    {
        switch (id)
        {
            case DATA_TEST_ENGAGED:
                return _engaged ? 1 : 0;
            case DATA_TEST_STACKS:
                return _meter ? _meter->Stacks() : 0;
            case DATA_TEST_JUSTICES:
                return _meter ? _meter->Justices() : 0;
            case DATA_TEST_MEGAVOLTS:
                return _megavolts;
            case DATA_TEST_CHAIN_BOLTS:
                return _chainBolts;
            case DATA_TEST_KICKED:
                return _kicked;
            case DATA_TEST_DISCHARGES:
                return _discharges;
            default:
                return 0;
        }
    }

    // `.dbtest gnomer electro state`.
    std::string DescribeState() const
    {
        return Acore::StringFormat("engaged={} heroic={} holding={} now={} | {} | megavolt in {} chain in {} "
            "shock in {} | megavolts={} chainbolts={} kicked={} shocks={} discharges={} static-carriers={}",
            _engaged ? 1 : 0, _heroic ? 1 : 0, _holding ? 1 : 0, _now,
            _meter ? _meter->Describe() : std::string("voltage -"), Until(_megavoltAt), Until(_chainAt),
            Until(_shockAt), _megavolts, _chainBolts, _kicked, _shocks, _discharges, StaticCarriers());
    }

    void UpdateAI(uint32 diff) override
    {
        GnomereganRework::NoAssist(me);     // rule 29, LESSONS L1: every tick, before UpdateVictim
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        // The fight clock, the meter and Static move every tick, cast bar or not (L8).
        _now += diff;
        bool teleported = false;
        if (_walking && _arrived)
            Hold("arrived");
        else if (_walking && _now >= _walkDeadline)
        {
            Hold("teleport", true);
            teleported = true;
        }
        if (_meter)
            _meter->Update(diff);
        if (_heroic)
            UpdateStatic(diff);
        CheckChainBar();
        if (teleported)
            return;     // RB-19: no facing and no new bar in the tick of the teleport
        if (me->HasUnitState(UNIT_STATE_CASTING) || !_holding)
            return;
        if (_meter && _meter->JusticeRunning())
            return;     // the bar is his; nothing else starts until it lands

        if (_now >= _megavoltAt && StartMegavolt(nullptr))
            return;
        if (_now >= _chainAt && StartChainBolt(nullptr))
            return;
        if (_now >= _shockAt)
            CastShock(nullptr, false);
        AnswerOutOfReach();
        FaceVictim();
        DoMeleeAttackIfReady();
    }

private:
    // ---- the center (section 7 #20 A) ------------------------------------------------------------------------------

    void StartCenterWalk()
    {
        me->SetCombatMovement(false);
        Position const center(kPlatformCenter.x, kPlatformCenter.y, kPlatformCenter.z, me->GetOrientation());
        if (me->GetExactDist2d(center.GetPositionX(), center.GetPositionY()) <= Tune::kCenterArriveYd)
        {
            Hold("at-center");
            return;
        }
        _walking = true;
        _arrived = false;
        _walkDeadline = _now + Tune::kCenterWalkMs;
        me->GetMotionMaster()->MovePoint(kPointCenter, center);
    }

    void Hold(char const* how, bool teleport = false)
    {
        if (!_walking && _holding)
            return;
        _walking = false;
        _arrived = false;
        if (teleport)
            me->NearTeleportTo(kPlatformCenter.x, kPlatformCenter.y, kPlatformCenter.z, me->GetOrientation());
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->SetControlled(true, UNIT_STATE_ROOT);
        _holding = true;
        // RB-19: after a teleport FaceVictim turns him on a later tick.
        if (!teleport)
            if (Unit* victim = me->GetVictim())
                me->SetFacingToObject(victim);
        LogEl("hold", Acore::StringFormat("how={} off-center={:.1f}", how,
            DungeonKit::Distance(DungeonKit::PlaneOf(me), kPlatformCenter.XY())));
    }

    // A finished bar left him facing its target: back to his victim (rooted, so never in the tick of a move).
    void FaceVictim()
    {
        Unit* victim = me->GetVictim();
        if (victim && !me->HasInArc(float(M_PI) / 3.f, victim))
            me->SetFacingToObject(victim);
    }

    // RB-4: his victim out of melee reach for a while: a Shock at it now and then (Tune::kNoReachShock).
    void AnswerOutOfReach()
    {
        Unit* victim = me->GetVictim();
        if (!Tune::kNoReachShock || !victim || me->IsWithinMeleeRange(victim))
        {
            _noReachSince = 0;
            return;
        }
        if (_noReachSince == 0)
            _noReachSince = _now + 1;
        if (_now + 1 - _noReachSince < Tune::kNoReachGraceMs || _now < _noReachShockAt)
            return;
        _noReachShockAt = _now + Tune::kNoReachShockMs;
        CastShock(victim, true);
    }

    // ---- picks (rule 5: on the Justice's floor, walkway included; section 7 #36 A: the tank included) ------------

    // The players of the fight: alive, not GMs, in combat with him, on his map.
    std::vector<Player*> FightPlayers() const
    {
        std::vector<Player*> out;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (CountsAsPlayer(player) && me->IsInCombatWith(player))
                out.push_back(player);
        }
        return out;
    }

    std::vector<Player*> PickOnPlatform(uint32 count, float maxRangeYd = 0.f) const
    {
        std::vector<Player*> pool;
        for (Player* player : FightPlayers())
        {
            if (!CanPick(DungeonKit::PlaneOf(me), DungeonKit::PlaneOf(player), player->GetPositionZ(), maxRangeYd))
                continue;
            pool.push_back(player);
        }
        std::vector<Player*> out;
        while (out.size() < count && !pool.empty())
        {
            std::size_t const i = urand(0, uint32(pool.size() - 1));
            out.push_back(pool[i]);
            pool.erase(pool.begin() + i);
        }
        return out;
    }

    float Multiplier() const
    {
        return _meter ? _meter->DamageMultiplier() : 1.f;
    }

    // ---- EL3 Megavolt ----------------------------------------------------------------------------------------------

    bool StartMegavolt(Player* forced)
    {
        std::vector<Player*> targets = forced ? std::vector<Player*>{ forced }
            : PickOnPlatform(Tune::kMegavoltTargets(_heroic), Tune::kMegavoltPickRangeYd);
        if (targets.empty())
        {
            _megavoltAt = _now + Tune::kBarRetryMs;     // nobody in the cone's reach: look again in a second
            return false;
        }
        SpellCastResult const result = me->CastSpell(me, SPELL_MEGAVOLT_BAR, false);
        if (result != SPELL_CAST_OK)
        {
            _megavoltAt = _now + Tune::kBarRetryMs;     // rule 15: a refused bar is retried
            LogEl("megavolt-refused", Acore::StringFormat("result={}", uint32(result)));
            return false;
        }
        _megavoltAt = NextDue(_megavoltAt, Tune::kMegavoltEveryMs, _now);
        ++_megavolts;
        float const pct = Tune::kMegavoltPct(_heroic) * Multiplier();
        Vec2 const from = DungeonKit::PlaneOf(me);
        std::string names;
        for (std::size_t i = 0; i < targets.size(); ++i)
        {
            float const facing = DungeonKit::BearingTo(from, DungeonKit::PlaneOf(targets[i]));
            if (i == 0)
                me->SetFacingTo(facing);
            // The cone is fixed at the bar's start: a point anchor facing the player's spot then (the Vishas recipe).
            Position const apex(me->GetPositionX(), me->GetPositionY(), me->GetPositionZ(), facing);
            MechanicRef ref = Mechanic::Zone(me, BossMechanics::Shapes::Cone(BossMechanics::Anchor(apex),
                Tune::kMegavoltAngleDeg, Tune::kMegavoltLengthYd), Ms(Tune::kMegavoltCastMs));
            ref.Damage(pct).TankDamage(pct).School(SPELL_SCHOOL_NATURE).Spell(SPELL_MEGAVOLT_HIT).Weakened()
                .HoldTankFacing().Within(_bounds).Tag(TAG_MEGAVOLT).OnResolve(OnBoss(
                    [](boss_electrocutioner_rework& ai, BossMechanics::ResolveResult const& r) { ai.MegavoltHit(r); }));
            Track(ref.Handle());
            names += " " + targets[i]->GetName();
        }
        LogEl("megavolt", Acore::StringFormat("count={} cones={} pct={:.1f} next_in={}:{}", _megavolts, targets.size(),
            pct, _megavoltAt - _now, names));
        return true;
    }

    // A cone landed: every player in it charges him (rule 11: the meter only counts here; a Justice it makes due
    // starts on his next tick).
    void MegavoltHit(BossMechanics::ResolveResult const& result)
    {
        uint32 hit = 0;
        for (ObjectGuid const& guid : result.hits)
            if (guid.IsPlayer())
                ++hit;
        if (hit == 0 || !_meter)
            return;
        _meter->Add(hit * Tune::kMegavoltVoltsPerHit(_heroic), "megavolt");
    }

    // ---- EL4 Chain Bolt --------------------------------------------------------------------------------------------

    bool StartChainBolt(Player* forced)
    {
        std::vector<Player*> picked = forced ? std::vector<Player*>{ forced } : PickOnPlatform(1);
        if (picked.empty())
        {
            _chainAt = _now + Tune::kBarRetryMs;
            return false;
        }
        Player* target = picked.front();
        SpellCastResult const result = me->CastSpell(target, SPELL_CHAIN_BOLT, false);
        if (result != SPELL_CAST_OK)
        {
            _chainAt = _now + Tune::kBarRetryMs;    // a Nature lockout or a silence: again in a second (rule 15)
            LogEl("chain-bolt-refused", Acore::StringFormat("target={} result={}", target->GetName(), uint32(result)));
            return false;
        }
        _chainAt = NextDue(_chainAt, Tune::kChainEveryMs, _now);
        ++_chainBolts;
        _chainTarget = target->GetGUID();
        _chainName = target->GetName();
        // The bots spread for the jumps while the bar runs (no damage of its own: the script strikes).
        MechanicRef ref = Mechanic::Spread(me, Tune::kChainJumpYd(_heroic), Ms(Tune::kChainCastMs));
        ref.Within(_bounds).Tag(_heroic ? TAG_CHAIN_BOLT : TAG_CHAIN_BOLT_NORMAL);
        _chainSpread = ref.Handle();
        Track(_chainSpread);
        Mechanic::NoteNextCastIn(me, SPELL_CHAIN_BOLT, Ms(_chainAt - _now));
        LogEl("chain-bolt", Acore::StringFormat("count={} target={} tank={} jump={:.0f} next_in={}", _chainBolts,
            _chainName, target == me->GetVictim() ? 1 : 0, Tune::kChainJumpYd(_heroic), _chainAt - _now));
        return true;
    }

    // The bar ended with neither callback (LESSONS A.2 #5): the spread goes, nothing lands.
    void CheckChainBar()
    {
        if (_chainTarget.IsEmpty() || me->FindCurrentSpellBySpellId(SPELL_CHAIN_BOLT))
            return;
        LogEl("chain-bolt-lost", Acore::StringFormat("target={} (the bar ended without landing)", _chainName));
        EndChainBar();
    }

    void EndChainBar()
    {
        if (_chainSpread)
            Mechanic::Cancel(me, _chainSpread);
        _chainSpread = {};
        _chainTarget.Clear();
    }

    void ResolveChainBolt()
    {
        Unit* first = _chainTarget.IsEmpty() ? nullptr : ObjectAccessor::GetUnit(*me, _chainTarget);
        std::string const firstName = _chainName;
        EndChainBar();
        Player* target = first ? first->ToPlayer() : nullptr;
        if (!CountsAsPlayer(target))
        {
            LogEl("chain-bolt-fizzled", Acore::StringFormat("target={} (gone before the bar ended)", firstName));
            return;
        }
        std::vector<Player*> players{ target };
        for (Player* player : FightPlayers())
            if (player != target)
                players.push_back(player);
        std::vector<ChainNode> nodes;
        nodes.reserve(players.size());
        for (Player* player : players)
            nodes.push_back({ player->GetGUID().GetRawValue(), DungeonKit::PlaneOf(player) });
        std::vector<std::size_t> const order = ChainOrder(nodes, 0, Tune::kChainJumpYd(_heroic),
            Tune::kChainMaxJumps(_heroic));
        float const mult = Multiplier();
        std::string names;
        for (std::size_t i = 0; i < order.size(); ++i)
        {
            Player* struck = players[order[i]];
            float const pct = ChainHitPct(i, Tune::kChainPct(_heroic), Tune::kChainJumpGrowth(_heroic)) * mult;
            DungeonKit::RegistryHitSpec spec;
            spec.pct = pct;
            spec.tankPct = pct;
            spec.school = SPELL_SCHOOL_NATURE;
            spec.spellId = SPELL_CHAIN_BOLT_HIT;
            spec.weakened = false;      // a spacing failure the group shares (SP EL4)
            spec.tag = _heroic ? TAG_CHAIN_BOLT : TAG_CHAIN_BOLT_NORMAL;
            Track(DungeonKit::RegistryHit(me, GuidSet{ struck->GetGUID() }, spec));
            names += Acore::StringFormat(" {}:{:.1f}", struck->GetName(), pct);
        }
        uint32 const jumps = order.empty() ? 0 : uint32(order.size() - 1);
        LogEl("chain-bolt-landed", Acore::StringFormat("target={} jumps={} mult={:.2f}:{}", firstName, jumps, mult,
            names));
        if (jumps > 0 && _meter)
            _meter->Add(jumps * Tune::kChainVoltsPerJump, "chain-bolt");
    }

    // ---- EL5 Shock -------------------------------------------------------------------------------------------------

    void CastShock(Unit* forced, bool fallback)
    {
        if (!fallback)
            _shockAt = NextDue(_shockAt, Tune::kShockEveryMs, _now);
        Unit* target = forced;
        if (!target)
        {
            std::vector<Player*> picked = PickOnPlatform(1, Tune::kShockRangeYd);
            target = picked.empty() ? nullptr : picked.front();
        }
        if (!target)
            return;
        // Not triggered: a kick's Nature lockout refuses it, and that Shock is lost (the reward).
        SpellCastResult const result = me->CastSpell(target, SPELL_SHOCK, false);
        if (result != SPELL_CAST_OK)
        {
            LogEl("shock-refused", Acore::StringFormat("target={} result={} fallback={}", target->GetName(),
                uint32(result), fallback ? 1 : 0));
            return;
        }
        ++_shocks;
        float const pct = Tune::kShockPct(_heroic) * Multiplier();
        DungeonKit::RegistryHitSpec spec;
        spec.pct = pct;
        spec.tankPct = pct;
        spec.school = SPELL_SCHOOL_NATURE;
        spec.spellId = SPELL_SHOCK_HIT;
        spec.weakened = false;
        spec.tag = TAG_SHOCK;
        Track(DungeonKit::RegistryHit(me, GuidSet{ target->GetGUID() }, spec));
        LogEl("shock", Acore::StringFormat("target={} pct={:.1f} fallback={} count={}", target->GetName(), pct,
            fallback ? 1 : 0, _shocks));
    }

    // ---- EL6 Static (heroic) ---------------------------------------------------------------------------------------

    void UpdateStatic(uint32 diff)
    {
        if (_now < Tune::kStaticGraceMs)
            return;     // DQ2: the meter counts from 5 s after the pull
        _staticElapsed += diff;
        if (_staticElapsed < Tune::kStaticSampleMs)
            return;
        uint32 const sample = _staticElapsed;
        _staticElapsed = 0;

        std::vector<Player*> const players = FightPlayers();
        // Gone from the fight (dead, out of combat, off the map): their Static goes.
        for (auto it = _static.begin(); it != _static.end();)
        {
            bool const present = std::any_of(players.begin(), players.end(),
                [&it](Player const* p) { return p->GetGUID() == it->first; });
            if (present)
            {
                ++it;
                continue;
            }
            if (Player* gone = ObjectAccessor::GetPlayer(*me, it->first))
                gone->RemoveAurasDueToSpell(SPELL_STATIC, me->GetGUID());
            it = _static.erase(it);
        }
        for (Player* player : players)
        {
            StaticCharge& charge = _static[player->GetGUID()];
            // m4: only a player on the pick floor (the platform or the walkway) charges; off it (fallen) the meter
            // holds and the first sample back on it starts from where they stand.
            if (!OnPickFloor(DungeonKit::PlaneOf(player), player->GetPositionZ()))
                charge.Forget();
            else if (charge.Step(DungeonKit::PlaneOf(player), sample))
                Discharge(player);
            ShowStatic(player, charge.Shown());
        }
    }

    // Rule 25: the count on the player is the meter's, every sample; the aura's short duration is refreshed while it
    // shows, so one left behind by a crash or a relog runs out by itself.
    void ShowStatic(Player* player, uint32 shown)
    {
        uint32 const have = DungeonKit::Stacks(player, SPELL_STATIC, me->GetGUID());
        if (have != shown)
            DungeonKit::AddStacks(player, SPELL_STATIC, int32(shown) - int32(have), me, Tune::kVoltageStackLimit);
        else if (shown > 0)
            if (Aura* aura = player->GetAura(SPELL_STATIC, me->GetGUID()))
                if (aura->GetDuration() < aura->GetMaxDuration() / 2)
                    aura->RefreshDuration();
    }

    void Discharge(Player* carrier)
    {
        ++_discharges;
        std::vector<Player*> const players = FightPlayers();
        std::vector<ChainNode> nodes;
        std::size_t carrierIndex = players.size();
        for (std::size_t i = 0; i < players.size(); ++i)
        {
            nodes.push_back({ players[i]->GetGUID().GetRawValue(), DungeonKit::PlaneOf(players[i]) });
            if (players[i] == carrier)
                carrierIndex = i;
        }
        std::optional<std::size_t> const ally = carrierIndex < players.size()
            ? NearestWithin(nodes, carrierIndex, Tune::kDischargeAllyYd) : std::nullopt;
        float const pct = Tune::kDischargePct * Multiplier();
        DungeonKit::RegistryHitSpec spec;
        spec.pct = pct;
        spec.tankPct = pct;
        spec.school = SPELL_SCHOOL_NATURE;
        spec.spellId = SPELL_DISCHARGE_HIT;
        spec.weakened = true;       // SP EL6 Penalty: Weakened on the carrier
        spec.tag = TAG_DISCHARGE;
        Track(DungeonKit::RegistryHit(me, GuidSet{ carrier->GetGUID() }, spec));
        if (ally)
        {
            spec.weakened = false;
            Track(DungeonKit::RegistryHit(me, GuidSet{ players[*ally]->GetGUID() }, spec));
        }
        Position const at(carrier->GetPositionX(), carrier->GetPositionY(), carrier->GetPositionZ(), 0.f);
        if (TempSummon* stalker = me->GetMap()->SummonCreature(NPC_BLAST_STALKER, at))
        {
            stalker->CastSpell(stalker, SPELL_DISCHARGE_LOOK, true);
            stalker->DespawnOrUnsummon(Ms(Tune::kBlastStalkerMs));
        }
        LogEl("discharge", Acore::StringFormat("carrier={} ally={} pct={:.1f} count={}", carrier->GetName(),
            ally ? players[*ally]->GetName() : std::string("-"), pct, _discharges));
        if (_meter)
            _meter->Add(Tune::kDischargeVolts, "discharge");
    }

    uint32 StaticCarriers() const
    {
        uint32 n = 0;
        for (auto const& [guid, charge] : _static)
            if (charge.Shown() > 0)
                ++n;
        return n;
    }

    // ---- descriptor, bookkeeping, cleanup --------------------------------------------------------------------------

    // Boss data (SP "Boss data"; the kick and dispel table): Chain Bolt is the interrupt (a reward on normal, expected
    // on heroic; caster 0: the heroic copy has another entry, LESSONS A.3 #1). Nothing is dispelled (Static and
    // Voltage cannot be). Heroic: BM-G's move cost for Static above 12 and the 11-12 yd ranged band (section 7 #12 A,
    // BM-G Q1 / Q2: heroic only, healers included).
    void Describe()
    {
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(0u, uint32(SPELL_CHAIN_BOLT), Tune::kChainKickPriority, Ms(Tune::kChainEveryMs));
        if (_heroic)
        {
            d.moveCosts.emplace_back(uint32(SPELL_STATIC), Tune::kStaticBotStandAbove);
            d.rangeBands.emplace_back(Tune::kRangedBandMinYd, Tune::kRangedBandMaxYd);
        }
        Mechanic::Describe(me, std::move(d));
    }

    void Track(MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // A registry callback reaches the AI through the map (guids only, never a Unit*).
    template <class Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnBoss(Fn fn) const
    {
        Map* map = me->GetMap();
        ObjectGuid const self = me->GetGUID();
        return [map, self, fn](BossMechanics::ResolveResult const& r)
        {
            Creature* boss = map ? map->GetCreature(self) : nullptr;
            if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_electrocutioner_rework*>(boss->AI()))
                if (ai->_engaged)
                    fn(*ai, r);
        };
    }

    std::string Until(uint32 at) const
    {
        return at > _now ? std::to_string(at - _now) : std::string("0");
    }

    // RB-1: everything of the pull, in one place: the registry handles, the meter and its auras, every player's
    // Static, the hold and the combat movement, the clocks and the counters, the leash.
    void Cleanup(char const* why)
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _chainSpread = {};
        _chainTarget.Clear();
        _chainName.clear();
        if (_meter)
        {
            _meter->Clear();
            _meter.reset();
        }
        me->RemoveAurasDueToSpell(SPELL_VOLTAGE);
        me->RemoveAurasDueToSpell(SPELL_VOLTAGE_CHARGED);
        uint32 cleared = 0;
        if (Map* map = me->FindMap())
            for (auto const& ref : map->GetPlayers())
                if (Player* player = ref.GetSource())
                    if (player->HasAura(SPELL_STATIC))
                    {
                        player->RemoveAurasDueToSpell(SPELL_STATIC);
                        ++cleared;
                    }
        _static.clear();
        _staticElapsed = 0;
        if (_holding || _walking)
            me->SetControlled(false, UNIT_STATE_ROOT);
        me->SetCombatMovement(true);
        bool const was = _engaged;
        _holding = false;
        _walking = false;
        _arrived = false;
        _walkDeadline = 0;
        _engaged = false;
        _now = 0;
        _megavoltAt = 0;
        _chainAt = 0;
        _shockAt = 0;
        _noReachSince = 0;
        _noReachShockAt = 0;
        _megavolts = 0;
        _chainBolts = 0;
        _kicked = 0;
        _shocks = 0;
        _discharges = 0;
        _arena.Reset();
        if (was || cleared)
            LogEl("cleanup", Acore::StringFormat("why={} static-cleared={}", why, cleared));
    }

    DungeonKit::ArenaGuard _arena;
    BossMechanics::SpotBounds _bounds;
    std::unique_ptr<GnomereganMachines::ElectroVoltageMeter> _meter;
    std::vector<MechanicHandle> _live;
    std::unordered_map<ObjectGuid, StaticCharge> _static;
    MechanicHandle _chainSpread;
    ObjectGuid _chainTarget;
    std::string _chainName;
    uint32 _now = 0;
    uint32 _megavoltAt = 0;
    uint32 _chainAt = 0;
    uint32 _shockAt = 0;
    uint32 _walkDeadline = 0;
    uint32 _noReachSince = 0;
    uint32 _noReachShockAt = 0;
    uint32 _staticElapsed = 0;
    uint32 _megavolts = 0;
    uint32 _chainBolts = 0;
    uint32 _kicked = 0;
    uint32 _shocks = 0;
    uint32 _discharges = 0;
    bool _heroic = false;
    bool _engaged = false;
    bool _walking = false;
    bool _arrived = false;
    bool _holding = false;
};

namespace
{
    boss_electrocutioner_rework* ElectroAI(ChatHandler* handler, Creature*& boss)
    {
        boss = GnomerTest::FindBoss(handler, NPC_ELECTROCUTIONER);
        if (!boss)
            return nullptr;
        auto* ai = boss->IsAIEnabled ? dynamic_cast<boss_electrocutioner_rework*>(boss->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("Electrocutioner 6000 does not run boss_electrocutioner_rework.");
        return ai;
    }

    bool Fire(ChatHandler* handler, int32 action, char const* what)
    {
        Creature* boss = nullptr;
        boss_electrocutioner_rework* ai = ElectroAI(handler, boss);
        if (!ai)
            return false;
        if (!ai->GetData(DATA_TEST_ENGAGED))
        {
            handler->SendErrorMessage("Electrocutioner 6000 is not in combat: pull him first.");
            return false;
        }
        ai->DoAction(action);
        handler->PSendSysMessage("electro {}: fired. {}", what, ai->DescribeState());
        return true;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return GnomerTest::ShowBossInfo(handler, NPC_ELECTROCUTIONER, BOSS_ELECTROCUTIONER);
    }

    bool HandleState(ChatHandler* handler)
    {
        Creature* boss = nullptr;
        boss_electrocutioner_rework* ai = ElectroAI(handler, boss);
        if (!ai)
            return false;
        handler->PSendSysMessage("electro: {}", ai->DescribeState());
        return true;
    }

    bool HandleJustice(ChatHandler* handler) { return Fire(handler, ACTION_TEST_JUSTICE, "justice"); }
    bool HandleMegavolt(ChatHandler* handler) { return Fire(handler, ACTION_TEST_MEGAVOLT, "megavolt"); }
    bool HandleChainBolt(ChatHandler* handler) { return Fire(handler, ACTION_TEST_CHAIN_BOLT, "chainbolt"); }
    bool HandleShock(ChatHandler* handler) { return Fire(handler, ACTION_TEST_SHOCK, "shock"); }
    bool HandleVoltage(ChatHandler* handler) { return Fire(handler, ACTION_TEST_VOLTAGE, "voltage"); }
    bool HandleStatic(ChatHandler* handler) { return Fire(handler, ACTION_TEST_STATIC, "static"); }

    ChatCommandTable const& ElectroTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "state",     HandleState,     SEC_GAMEMASTER, Console::No },
            { "justice",   HandleJustice,   SEC_GAMEMASTER, Console::No },
            { "megavolt",  HandleMegavolt,  SEC_GAMEMASTER, Console::No },
            { "chainbolt", HandleChainBolt, SEC_GAMEMASTER, Console::No },
            { "shock",     HandleShock,     SEC_GAMEMASTER, Console::No },
            { "voltage",   HandleVoltage,   SEC_GAMEMASTER, Console::No },
            { "static",    HandleStatic,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_electrocutioner_rework()
{
    RegisterDungeonReworkCreatureAI(boss_electrocutioner_rework, GnomereganRework::kInstanceScriptName);
    GnomerTest::RegisterBoss("electro", ElectroTestCommands());
}
