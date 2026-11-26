/*
 * mod-dungeon-bosses, Zul'Farrak D4b: the Stair (stage 2 of the Pyramid) and the Altar's director (stage 3), normal and
 * heroic. Build spec: SP 1346-1432 (PY4-PY11, PY14, PY16), design SP 1180-1281 (rulings 21-23, 46); handoff section
 * 3.5 row D4b and its kick and dispel table, sections 3.6, 3.8 (the stair, the landing, the plaza), section 7 #11 A,
 * #20 A, #31 A, #32 A, #44 A. Replaces the stock instance_zulfarrak waves (the S0 instance replaces the stock
 * instance; its stage machine runs the directors registered here). Bound by apps/dbc-tools
 * source/npcs/zul_farrak/pyramid_stair.py; numbers in StairLogic.h and SezzzizLogic.h; the Pyramid-wide pieces
 * (Grievous Wound, Offerings, Blood Price, the director base) in PyramidFight.h; Sezz'ziz and Nekrum in
 * boss_sezzziz_rework.cpp. The crew are CR's (BlyCrew.h): this file only answers their places on the Stair and keeps
 * them off the plaza (an Ally handler), and Weegli yells through his own AI (rule 28).
 *
 *   Stage 2       starts when a cage opens (the instance) and again 10 s after a living player stands on the landing
 *                 after a wipe or a reload. Wave 1 (23: 4 Berserkers, 4 Hexmasters, 4 Witch Doctors, 11 fodder) gathers
 *                 on the plaza and climbs the stair path 81553 in groups of 3, 4, 5, 6 and the rest, one every 8 s;
 *                 10 s after its last troll, wave 2 (24) does the same; wave 2's last troll wins the stage
 *                 (DATA_PYRAMID_COMPLETE 2). Every climber carries the bots' landing hold (strict bounds: the landing
 *                 and the top).
 *   PY4 Barrels   every 15 s (heroic 12 s) Weegli yells line 3 and a barrel is lit at the lip; the lane (the stair from
 *                 y 1227 to 1259 at its true width) is drawn for 3 s (four strips up the slope; eleven telegraph-only
 *                 tiles steer the bots); then the barrel slides down and goes off at the foot: players on the lane
 *                 take 40% (heroic 50%) Fire, Weakened and a 2 s Knockdown; trolls on it lose 50% of their health and
 *                 are knocked down the stair.
 *   PY5 Crew      Bly at the lip, Raven, Oro and Murta on the landing's platform, Weegli by the lip (CR walks them).
 *   PY6 / PY7     Berserker: a charge at a player 8 to 25 yd away every 12 to 16 s, a 2% bleed for 12 s; heroic: the
 *                 path drawn 1.5 s ahead (30% Physical + Weakened on anyone but the target) and Grievous Wound.
 *   PY8 / PY9     Hexmaster: Shadow Bolt, Curse of Blood (+10% Physical taken, a Curse); heroic: Sandfury Hex (a
 *                 stack every 4 s, Hexed for 2 s at 5).
 *   PY10 / PY11   Witch Doctor: Flash Heal (kickable, a reward), Healing Ward; heroic: a Lava Spout Totem on the
 *                 landing every 20 s, an 8 yd zone of 6% Fire every 3 s.
 *   Stage 3       the Altar: wave 3 (5), Sezz'ziz and Nekrum gather on the plaza when stage 2 is won, idle and out of
 *                 the crew's reach (immune to NPCs) until the stage starts (5 s later, or a player's pull after a wipe
 *                 or a reload); one pull brings the whole Altar.
 *
 * Every firing logs one INFO line "zf-build stair <mechanic> ..." (the Altar's director "zf-build altar ...");
 * `.dbtest zf stair <subcommand>` fires one (README rows: the report's shared-file requests).
 *
 * Mirrored stock code (AGENTS.md credit rule): the wave tables, their gathering and the climb up path 81553 follow the
 * stock instance_zulfarrak.cpp (c9315e3ec moostigre <moostigre@proton.me>, 048025ceb UltraNix
 * <80540499+UltraNix@users.noreply.github.com>), re-implemented (the stock pace changed to the spec's).
 */

#include "ArenaGuard.h"
#include "BlyCrew.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFields.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MechanicDescriptor.h"
#include "MechanicProviders.h"
#include "MechanicRegistry.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "PassiveAI.h"
#include "Player.h"
#include "PyramidFight.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SezzzizLogic.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StairLogic.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include "ZulFarrakKit.h"
#include "ZulFarrakRework.h"
#include "ZulFarrakTestCommand.h"
#include <algorithm>
#include <cmath>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ZulFarrakRework;
using namespace ZfStair;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kStairKey = "stair";
    char const* const kAltarKey = "altar";
    uint8 constexpr kSchoolPhysical = 0;    // SPELL_SCHOOL_NORMAL
    uint8 constexpr kSchoolFire = 2;        // SPELL_SCHOOL_FIRE
    int32 constexpr ACTION_BARREL_ROLL = 20941;
    uint32 constexpr kBarrelPoint = 1;

    void StairLog(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kStairKey, mechanic, detail);
    }

    void AltarLog(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kAltarKey, mechanic, detail);
    }

    Position ToPos(Point3 const& p)
    {
        return Position(p.x, p.y, p.z, p.o);
    }

    bool LivingPlayer(Player const* player)
    {
        return player && player->IsInWorld() && player->IsAlive() && !player->IsGameMaster();
    }

    // Rule 19: an arriving troll takes the tank first (the module's role provider), then the nearest living player
    // in the Pyramid's region.
    Player* ArrivalTarget(Creature* unit)
    {
        Player* tank = nullptr;
        Player* nearest = nullptr;
        float best = 1.0e9f;
        for (auto const& ref : unit->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!LivingPlayer(player) || !InPyramidRegion({ player->GetPositionX(), player->GetPositionY() }))
                continue;
            if (!tank && BossMechanics::GetRoleProvider().Get(unit, player) == BossMechanics::Role::Tank)
                tank = player;
            float const d = unit->GetExactDist(player);
            if (d < best)
            {
                best = d;
                nearest = player;
            }
        }
        return tank ? tank : nearest;
    }

    // A unit the stock SmartAI walks while it should wait (Slaves and Drudges: "Is Summoned By: Move Random 10",
    // "Out of Combat: Move Point" to the landing after 8 to 90 s, each once): back home and standing.
    void HoldWaiting(Creature* unit)
    {
        if (!unit || unit->IsInCombat())
            return;
        MovementGeneratorType const type = unit->GetMotionMaster()->GetCurrentMovementGeneratorType();
        if (type == POINT_MOTION_TYPE || type == RANDOM_MOTION_TYPE || type == WAYPOINT_MOTION_TYPE)
            unit->GetMotionMaster()->MoveTargetedHome();
    }

    BossMechanics::Eligibility EveryPlayerBut(Map* map, ObjectGuid const& exempt)
    {
        BossMechanics::Eligibility who;
        who.playersOnly = true;
        for (auto const& ref : map->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->GetGUID() != exempt)
                    who.carriers.insert(player->GetGUID());
        if (who.carriers.empty())
            who.carriers.insert(ObjectGuid::Empty);     // nobody but the target: a set naming no player
        return who;
    }
}

class StairStage;
class AltarStage;

namespace
{
    // `.dbtest zf stair` reaches the running directors of an instance (the instance owns them; they register here
    // while they live).
    std::unordered_map<InstanceScript const*, StairStage*>& StairDirectors()
    {
        static std::unordered_map<InstanceScript const*, StairStage*> directors;
        return directors;
    }

    std::unordered_map<InstanceScript const*, AltarStage*>& AltarDirectors()
    {
        static std::unordered_map<InstanceScript const*, AltarStage*> directors;
        return directors;
    }
}

// ====================================================================================================================
// The wave specialists (301015-301017): the dungeon's Sandfury copies (SP mechanic 4)
// ====================================================================================================================

// What the three share: the assist calls off (a fighting climber never pulls the trolls still gathering below), the
// fight clock, the heroic flag, a reset of every per-pull field.
struct npc_zf_sandfury_add : public ScriptedAI
{
    explicit npc_zf_sandfury_add(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        _now = 0;
        _engaged = false;
        ResetKit();
    }

    void JustEngagedWith(Unit* who) override
    {
        ScriptedAI::JustEngagedWith(who);
        _heroic = DungeonKit::IsHeroicMap(me);
        _engaged = true;
        _now = 0;
        ResetKit();
        StartKit();
    }

    void JustDied(Unit* /*killer*/) override
    {
        ResetKit();
    }

    void UpdateAI(uint32 diff) override
    {
        ZulFarrak::NoAssist(me);
        if (!UpdateVictim())
            return;
        _now += diff;
        if (UpdateKit())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

protected:
    virtual void ResetKit() { }
    virtual void StartKit() { }
    // True: the tick is the kit's (no melee).
    virtual bool UpdateKit() { return false; }

    void Log(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kStairKey, mechanic, detail);
    }

    uint32 _now = 0;
    bool _heroic = false;
    bool _engaged = false;
};

// Sandfury Berserker 301015 (Blood Drinker's look): PY6 the charge and its bleed; heroic PY7 Trampling Charge and
// Grievous Wound in place of the bleed.
struct npc_zf_sandfury_berserker : public npc_zf_sandfury_add
{
    explicit npc_zf_sandfury_berserker(Creature* creature) : npc_zf_sandfury_add(creature) { }

    void EnterEvadeMode(EvadeReason why) override
    {
        CancelCharge();
        npc_zf_sandfury_add::EnterEvadeMode(why);
    }

    void MovementInform(uint32 /*type*/, uint32 id) override
    {
        if (id == EVENT_CHARGE && _step == Step::Charging)
            EndCharge(true);
    }

protected:
    enum class Step : uint8
    {
        Idle,
        Trampling,  // heroic: the path drawn, he stands
        Charging,
    };

    void ResetKit() override
    {
        CancelCharge();
        _chargeAt = 0;
    }

    void StartKit() override
    {
        _chargeAt = Tune::kChargeFirstMs;
    }

    bool UpdateKit() override
    {
        switch (_step)
        {
            case Step::Idle:
                if (_now >= _chargeAt && !me->HasUnitState(UNIT_STATE_CASTING))
                    TryCharge();
                return _step != Step::Idle;
            case Step::Trampling:
                if (_now >= _stepAt)
                    Launch();
                return true;
            case Step::Charging:
                if (_now >= _stepAt)
                    EndCharge(false);
                return true;
        }
        return false;
    }

private:
    void TryCharge()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;       // tank included (SP PY6)
        rule.minRange = Tune::kChargeMinYd;
        rule.maxRange = Tune::kChargeMaxYd;
        rule.requireLos = true;
        Player* target = DungeonKit::PickPlayer(me, rule);
        if (!target)
        {
            _chargeAt = _now + Tune::kChargeRetryMs;
            return;
        }
        _target = target->GetGUID();
        _targetName = target->GetName();
        _dest = target->GetPosition();
        if (!_heroic)
        {
            Launch();
            return;
        }
        // PY7: the path drawn 1.5 s ahead; he stands and faces it.
        me->GetMotionMaster()->Clear();
        me->StopMoving();
        me->SetFacingToObject(target);
        Position const from = me->GetPosition();
        _trample = Mechanic::Line(me, from, _dest, Tune::kTramplingWidthYd, Milliseconds(Tune::kTramplingWarnMs))
            .Damage(Tune::kTramplingPct).TankDamage(Tune::kTramplingPct).School(kSchoolPhysical)
            .Spell(SPELL_TRAMPLING).Weakened().Eligible(EveryPlayerBut(me->GetMap(), _target))
            .Tag(TAG_TRAMPLING);
        _step = Step::Trampling;
        _stepAt = _now + Tune::kTramplingWarnMs;
        Log("trample", Acore::StringFormat("target={} from=({:.1f}, {:.1f}) to=({:.1f}, {:.1f}) length={:.1f}",
            _targetName, from.GetPositionX(), from.GetPositionY(), _dest.GetPositionX(), _dest.GetPositionY(),
            from.GetExactDist2d(&_dest)));
    }

    void Launch()
    {
        Position dest = _dest;
        if (!_heroic)
            if (Unit* target = ObjectAccessor::GetUnit(*me, _target))
                dest = target->GetPosition();
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveCharge(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(),
            Tune::kChargeSpeed);
        _step = Step::Charging;
        _stepAt = _now + Tune::kChargeTimeoutMs;
    }

    // At the end of the charge: the target close by takes the bleed (heroic: the wound), then back to the fight.
    void EndCharge(bool arrived)
    {
        _step = Step::Idle;
        _trample = MechanicHandle();
        _chargeAt = _now + urand(Tune::kChargeMinMs, Tune::kChargeMaxMs);
        Unit* target = ObjectAccessor::GetUnit(*me, _target);
        bool hit = false;
        if (target && target->IsAlive() && me->IsWithinDist(target, Tune::kChargeHitYd))
        {
            if (_heroic)
                hit = ZfPyramid::ApplyGrievousWound(me, target);
            else
            {
                me->CastSpell(target, SPELL_BERSERKER_LOOK, true);
                me->CastSpell(target, SPELL_BERSERKER_BLEED, true);
                hit = true;
            }
        }
        Log("charge", Acore::StringFormat("target={} arrived={} hit={} heroic={} next_in={}", _targetName,
            arrived ? 1 : 0, hit ? 1 : 0, _heroic ? 1 : 0, _chargeAt - _now));
        _target.Clear();
        if (Unit* victim = me->GetVictim())
        {
            me->GetMotionMaster()->Clear();
            me->GetMotionMaster()->MoveChase(victim);
        }
    }

    void CancelCharge()
    {
        if (_trample)
            Mechanic::Cancel(me, _trample);
        _trample = MechanicHandle();
        _step = Step::Idle;
        _target.Clear();
    }

    Step _step = Step::Idle;
    uint32 _chargeAt = 0;
    uint32 _stepAt = 0;
    ObjectGuid _target;
    std::string _targetName;
    Position _dest;
    MechanicHandle _trample;
};

// Sandfury Hexmaster 301016 (Shadowcaster's look): PY8 Curse of Blood (heroic PY9 Sandfury Hex), Shadow Bolt from
// range.
struct npc_zf_sandfury_hexmaster : public npc_zf_sandfury_add
{
    explicit npc_zf_sandfury_hexmaster(Creature* creature) : npc_zf_sandfury_add(creature) { }

    void AttackStart(Unit* who) override
    {
        AttackStartCaster(who, Tune::kCasterRangeYd);
    }

protected:
    void ResetKit() override
    {
        _curseAt = 0;
        _boltAt = 0;
    }

    void StartKit() override
    {
        _curseAt = Tune::kCurseFirstMs;
        _boltAt = urand(0, Tune::kBoltFirstMaxMs);
    }

    bool UpdateKit() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return true;
        if (_now >= _curseAt)
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;       // tank included (SP PY8)
            rule.maxRange = Tune::kCurseRangeYd;
            rule.requireLos = true;
            _curseAt = _now + urand(Tune::kCurseMinMs, Tune::kCurseMaxMs);
            if (Player* target = DungeonKit::PickPlayer(me, rule))
            {
                uint32 const spell = _heroic ? uint32(SPELL_SANDFURY_HEX) : uint32(SPELL_CURSE_OF_BLOOD);
                DoCast(target, spell);
                Log(_heroic ? "hex" : "curse", Acore::StringFormat("target={}", target->GetName()));
                return true;
            }
        }
        if (_now >= _boltAt && me->GetVictim())
        {
            DoCastVictim(SPELL_HEX_SHADOW_BOLT);
            _boltAt = _now + urand(Tune::kBoltMinMs, Tune::kBoltMaxMs);
            return true;
        }
        return false;
    }

private:
    uint32 _curseAt = 0;
    uint32 _boltAt = 0;
};

// Sandfury Witch Doctor 301017 (the Witch Doctor's look and kit): PY10 Flash Heal and Healing Ward; heroic PY11 the
// Lava Spout Totem.
struct npc_zf_sandfury_witch_doctor : public npc_zf_sandfury_add
{
    explicit npc_zf_sandfury_witch_doctor(Creature* creature) : npc_zf_sandfury_add(creature) { }

    void AttackStart(Unit* who) override
    {
        AttackStartCaster(who, Tune::kCasterRangeYd);
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (spell && spell->Id == SPELL_LAVA_TOTEM_BAR)
            PlaceTotem();
    }

protected:
    void ResetKit() override
    {
        _healAt = 0;
        _wardAt = 0;
        _totemAt = 0;
    }

    void StartKit() override
    {
        _healAt = urand(Tune::kFlashHealMinMs / 4, Tune::kFlashHealMinMs);
        _wardAt = Tune::kWardFirstMs;
        _totemAt = Tune::kTotemFirstMs;
    }

    bool UpdateKit() override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return true;
        if (_now >= _wardAt)
        {
            _wardAt = _now + Tune::kWardEveryMs;
            DoCastSelf(SPELL_HEALING_WARD);
            return true;
        }
        if (_heroic && _now >= _totemAt)
        {
            _totemAt = _now + Tune::kTotemEveryMs;
            DoCastSelf(SPELL_LAVA_TOTEM_BAR);
            return true;
        }
        if (_now >= _healAt)
        {
            if (Unit* hurt = DoSelectLowestHpFriendly(Tune::kFlashHealRangeYd, Tune::kFlashHealMissing))
            {
                _healAt = _now + urand(Tune::kFlashHealMinMs, Tune::kFlashHealMaxMs);
                DoCast(hurt, SPELL_FLASH_HEAL);
                return true;
            }
            _healAt = _now + 1000;
        }
        return false;
    }

private:
    // PY11: the totem (the stock Lava Spout Totem's look, 6017) on the landing: at her feet when she stands on the
    // landing or the top (or the plaza at the Altar), at the lip when she casts from the stair. Its 8 yd zone is a
    // registry Zone the totem owns: it goes with the totem (killed or timed out).
    void PlaceTotem()
    {
        Position at = me->GetPosition();
        bool const onStair = StairArena().Contains({ me->GetPositionX(), me->GetPositionY() }, me->GetPositionZ());
        if (onStair)
            at = Position(kTotemLip.x + frand(-2.f, 2.f), kTotemLip.y + frand(0.f, 2.f), kTotemLip.z);
        Creature* totem = me->SummonCreature(NPC_LAVA_SPOUT_TOTEM, at, TEMPSUMMON_TIMED_DESPAWN, Tune::kTotemLifeMs);
        if (!totem)
            return;
        totem->SetFaction(me->GetFaction());
        totem->SetReactState(REACT_PASSIVE);
        totem->SetControlled(true, UNIT_STATE_ROOT);
        totem->CastSpell(totem, SPELL_LAVA_GLOW, true);
        Mechanic::Circle(totem, totem, Tune::kTotemRadiusYd, Milliseconds(Tune::kTotemArmMs))
            .Persistent(Milliseconds(Tune::kTotemLifeMs - Tune::kTotemArmMs), Milliseconds(Tune::kTotemTickMs))
            .Damage(Tune::kTotemPct).TankDamage(Tune::kTotemPct).School(kSchoolFire).Spell(SPELL_LAVA_SPOUT)
            .Tag(TAG_TOTEM);
        Log("totem", Acore::StringFormat("at=({:.1f}, {:.1f}, {:.1f}) lip={}", at.GetPositionX(), at.GetPositionY(),
            at.GetPositionZ(), onStair ? 1 : 0));
    }

    uint32 _healAt = 0;
    uint32 _wardAt = 0;
    uint32 _totemAt = 0;
};

// Weegli's barrel 301018 (the fused keg, sliding upright: no stock barrel rolls): lit at the lip, it slides down the
// lane when the lane resolves and goes off at the foot (SV 889).
struct npc_zf_weegli_barrel : public NullCreatureAI
{
    explicit npc_zf_weegli_barrel(Creature* creature) : NullCreatureAI(creature) { }

    void DoAction(int32 action) override
    {
        if (action != ACTION_BARREL_ROLL)
            return;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(kBarrelPoint, ToPos(kBarrelFoot), FORCED_MOVEMENT_RUN, Tune::kBarrelSlideSpeed,
            false);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE || id != kBarrelPoint)
            return;
        me->CastSpell(me, SPELL_BARREL_BLAST, true);
        me->DespawnOrUnsummon(Milliseconds(1000));
    }
};

// PY9 Sandfury Hex 213998 (heroic): a stack every 4 s (its periodic dummy); the stack that would make 5 turns the
// carrier into a frog for 2 s (Hexed, Magic) and the curse clears. A cure (Curse) ends it at any stack.
class spell_zf_sandfury_hex : public AuraScript
{
    PrepareAuraScript(spell_zf_sandfury_hex);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Aura* aura = GetAura();
        Unit* owner = GetUnitOwner();
        if (!aura || !owner || !owner->IsAlive())
            return;
        uint32 const next = uint32(aura->GetStackAmount()) + 1;
        if (!HexTurnsToFrog(next))
        {
            aura->ModStackAmount(1);
            return;
        }
        Unit* caster = GetCaster();
        (caster && caster->IsInWorld() ? caster : owner)->CastSpell(owner, SPELL_HEXED, true);
        DungeonKit::LogMechanic(kLogDungeon, kStairKey, "hexed", Acore::StringFormat("target={}", owner->GetName()));
        Remove(AURA_REMOVE_BY_DEFAULT);
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_zf_sandfury_hex::HandlePeriodic, EFFECT_0,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

// ====================================================================================================================
// PY5 the crew on the Stair (CR's Ally mode): their places, and the fighters kept off the plaza while stage 2 runs
// ====================================================================================================================
class StairAllyHandler : public ZfCrew::CrewModeHandler
{
public:
    std::optional<Position> RestSpot(ZfCrew::BlyCrewAI& ai, ZfCrew::CrewSpot spot) override
    {
        if (spot != ZfCrew::CrewSpot::Stair || ai.Member() >= kCrewCount || !kCrewStairSpots[ai.Member()])
            return std::nullopt;
        return ToPos(*kCrewStairSpots[ai.Member()]);
    }

    bool OnUpdate(ZfCrew::BlyCrewAI& ai, uint32 diff) override
    {
        _leashMs += diff;
        if (_leashMs < Tune::kPollMs)
            return false;
        _leashMs = 0;
        Creature* me = ai.Me();
        if (ai.IsWeegli() || ai.Spot() != ZfCrew::CrewSpot::Stair || !me->IsInCombat()
            || me->GetPositionY() >= Tune::kCrewLeashY)
            return false;
        ai.StopFighting();
        ai.GoToSpot(ZfCrew::CrewSpot::Stair, false);
        StairLog("crew-leash", Acore::StringFormat("member={} y={:.1f}", kCrewNames[ai.Member()], me->GetPositionY()));
        return true;
    }

    void OnReset(ZfCrew::BlyCrewAI& /*ai*/) override
    {
        _leashMs = 0;
    }

private:
    uint32 _leashMs = 0;
};

// ====================================================================================================================
// Stage 2, the Stair (ZulFarrakKit.h PyramidStageDirector; D4a's PyramidStage base runs the Sandfury watch)
// ====================================================================================================================
class StairStage : public ZfPyramid::PyramidStage
{
public:
    explicit StairStage(InstanceScript* instance) : ZfPyramid::PyramidStage(instance, PYRAMID_STAGE_STAIR),
        _hold(BoundsOf(HoldArena()).Strict())
    {
        StairDirectors()[instance] = this;
    }

    ~StairStage() override
    {
        StairDirectors().erase(Instance());
    }

    void OnStart(bool restart) override
    {
        ZfPyramid::PyramidStage::OnStart(restart);     // first: the watch tracks the Sandfury made from here on
        DespawnAll("start");
        _heroic = Heroic();
        _running = true;
        _now = 0;
        _pollMs = 0;
        _wave = 0;
        _nextWaveAt = 0;
        _completeDue = false;
        _barrels = 0;
        _barrelAt = Tune::kBarrelEveryMs.Get(_heroic);
        _barrelResolveAt = 0;
        SummonStalker();
        StartWave(1);
        ZfPyramid::PyramidRead const r = ZfPyramid::ReadPyramid(Instance());
        StairLog("stage-start", Acore::StringFormat("restart={} heroic={} offerings={} bloodprice={} crew={}",
            restart ? 1 : 0, _heroic ? 1 : 0, r.offerings, r.bloodPrice, Instance()->GetData(DATA_CREW_ALIVE)));
    }

    // In play and idle (the Block won, a wipe, a reload): nothing stands; the instance restarts the stage from the
    // landing.
    void OnWait() override
    {
        if (_running)
            return;
        DespawnAll("wait");
        StairLog("stage-wait", "the landing restarts it");
    }

    void OnUpdate(uint32 diff) override
    {
        ZfPyramid::PyramidStage::OnUpdate(diff);
        if (!_running)
            return;
        _now += diff;
        UpdateSends();
        UpdateBarrel();
        _pollMs += diff;
        if (_pollMs >= Tune::kPollMs)
        {
            _pollMs = 0;
            Poll();
        }
        if (_nextWaveAt && _now >= _nextWaveAt)
        {
            _nextWaveAt = 0;
            StartWave(2);
        }
        if (_completeDue)
        {
            _completeDue = false;
            _running = false;
            StairLog("won", Acore::StringFormat("time={} barrels={}", _now, _barrels));
            // Last: the instance ends this director inside the call (OnEnd, then it is dropped).
            Instance()->SetData(DATA_PYRAMID_COMPLETE, PYRAMID_STAGE_STAIR);
            return;
        }
    }

    void OnEnd(bool won) override
    {
        ZfPyramid::PyramidStage::OnEnd(won);
        _running = false;
        DespawnAll(won ? "won" : "lost");
        StairLog("stage-end", won ? "won" : "lost");
    }

    void OnCreatureDeath(Creature* creature) override
    {
        for (Climber& c : _climbers)
            if (c.guid == creature->GetGUID())
                c.state = ClimberState::Gone;
    }

    // ---- `.dbtest zf stair` ----------------------------------------------------------------------------------------

    bool Running() const { return _running; }

    bool TestBarrel()
    {
        if (!_running || _barrelResolveAt)
            return false;
        _barrelAt = _now;
        return true;
    }

    bool TestSend()
    {
        if (!_running || !CountWaiting(States()))
            return false;
        uint32 const waiting = CountWaiting(States());
        SendGroup(SendGroupSize(_sends, waiting), "gm");
        ++_sends;
        return true;
    }

    std::string State()
    {
        std::vector<ClimberState> const states = States();
        uint32 sent = 0;
        uint32 gone = 0;
        for (ClimberState s : states)
        {
            sent += s == ClimberState::Sent ? 1 : 0;
            gone += s == ClimberState::Gone ? 1 : 0;
        }
        return Acore::StringFormat("running={} heroic={} now={} wave={} sends={} waiting={} sent={} gone={} "
            "nextwave_in={} barrels={} barrel_in={} resolving={} tracked={} bleeding={}", _running ? 1 : 0,
            _heroic ? 1 : 0, _now, _wave, _sends, CountWaiting(states), sent, gone,
            _nextWaveAt ? _nextWaveAt - _now : 0, _barrels, _barrelAt > _now ? _barrelAt - _now : 0,
            _barrelResolveAt ? 1 : 0, Buffs().Tracked(), Buffs().Bleeding());
    }

private:
    struct Climber
    {
        ObjectGuid guid;
        uint32 entry = 0;
        ClimberState state = ClimberState::Waiting;
    };

    std::vector<ClimberState> States() const
    {
        std::vector<ClimberState> out;
        out.reserve(_climbers.size());
        for (Climber const& c : _climbers)
            out.push_back(c.state);
        return out;
    }

    Map* GetMap() const { return Instance()->instance; }
    Creature* Stalker() const { return _stalker.IsEmpty() ? nullptr : GetMap()->GetCreature(_stalker); }

    // The lane stalker (D4a's 301019) at the lip: the Stair's registry owner (the lane, its hit) and its descriptor
    // (the bots' kicks, cures and kill order for the waves), the summoner of the waves and the barrels.
    void SummonStalker()
    {
        TempSummon* stalker = GetMap()->SummonCreature(NPC_ZF_PYRAMID_STALKER, ToPos(kLaneStalker));
        if (!stalker)
        {
            StairLog("stalker-failed");
            return;
        }
        _stalker = stalker->GetGUID();
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_PYRAMID;
        Mechanic::BeginEncounter(stalker, options);
        BossMechanics::Descriptor d;
        d.interrupts.emplace_back(NPC_ZF_SANDFURY_WITCH_DOCTOR, SPELL_FLASH_HEAL, uint8(1));
        d.dispels.emplace_back(SPELL_HEXED, uint8(3), true);
        d.dispels.emplace_back(SPELL_CURSE_OF_BLOOD, uint8(1));
        d.dispels.emplace_back(SPELL_SANDFURY_HEX, uint8(1));
        d.targets.emplace_back(NPC_ZF_SANDFURY_WITCH_DOCTOR, int8(4));
        d.targets.emplace_back(NPC_HEALING_WARD, int8(3));
        d.targets.emplace_back(NPC_ZF_SANDFURY_HEXMASTER, int8(2));
        d.targets.emplace_back(NPC_ZF_SANDFURY_BERSERKER, int8(1));
        d.targets.emplace_back(NPC_SANDFURY_SLAVE, int8(1));
        d.targets.emplace_back(NPC_SANDFURY_DRUDGE, int8(1));
        ZfPyramid::AddWoundHealRule(d, _heroic);
        Mechanic::Describe(stalker, std::move(d));
    }

    // ---- the waves --------------------------------------------------------------------------------------------------

    void StartWave(uint32 wave)
    {
        _wave = wave;
        _waveAt = _now;
        _sends = 0;
        _waveCleared = false;
        _climbers.clear();
        Creature* stalker = Stalker();
        uint32 specialists = 0;
        for (std::size_t index : WaveIndexes(wave))
        {
            uint32 const entry = WaveEntry(index);
            Position const at = ToPos(kWaveSpawns[index].at);
            TempSummon* unit = stalker
                ? stalker->SummonCreature(entry, at, TEMPSUMMON_CORPSE_TIMED_DESPAWN, Tune::kCorpseMs)
                : GetMap()->SummonCreature(entry, at);
            if (!unit)
                continue;
            unit->SetHomePosition(at);
            unit->GetMotionMaster()->Clear();      // the stock Slaves' and Drudges' summon walk
            unit->GetMotionMaster()->MoveIdle();
            unit->SetReactState(REACT_AGGRESSIVE);
            if (stalker)
                Mechanic::TrackUnit(stalker, unit);
            _climbers.push_back({ unit->GetGUID(), entry, ClimberState::Waiting });
            specialists += IsSpecialist(entry) ? 1 : 0;
        }
        StairLog("wave", Acore::StringFormat("wave={} trolls={} specialists={} heroic={}", wave, _climbers.size(),
            specialists, _heroic ? 1 : 0));
    }

    void UpdateSends()
    {
        if (!_wave)
            return;
        std::vector<ClimberState> const states = States();
        uint32 waiting = CountWaiting(states);
        uint32 const due = SendsDue(_now - _waveAt);
        while (_sends < due && waiting)
        {
            uint32 const n = SendGroupSize(_sends, waiting);
            SendGroup(n, "pace");
            ++_sends;
            waiting = CountWaiting(States());
        }
    }

    void SendGroup(uint32 n, char const* why)
    {
        std::vector<std::size_t> const picks = NextSend(States(), n);
        for (std::size_t i : picks)
            if (Creature* unit = GetMap()->GetCreature(_climbers[i].guid))
                Send(_climbers[i], unit);
            else
                _climbers[i].state = ClimberState::Gone;
        StairLog("send", Acore::StringFormat("wave={} send={} size={} why={} waiting={}", _wave, _sends + 1,
            picks.size(), why, CountWaiting(States())));
    }

    // Up the stair (stock path 81553: the foot, then the lip), with the bots' landing hold on him.
    void Send(Climber& c, Creature* unit)
    {
        c.state = ClimberState::Sent;
        unit->SetReactState(REACT_AGGRESSIVE);
        if (!unit->IsInCombat())
            unit->GetMotionMaster()->MoveWaypoint(kWavePath, false);
        Mechanic::Spot(unit, {}, Milliseconds(Tune::kHoldCarrierMs)).NoTelegraph().Within(_hold).Tag(TAG_HOLD);
    }

    // Every kPollMs: the dead are gone; a waiting troll pulled early is sent, one the stock SmartAI walks goes back;
    // a sent troll standing out of combat (a knockback, an evade home, the path's end) is set on the tank on the
    // landing (rule 19) or sent up again. A cleared wave starts the next one 10 s later, or wins the stage.
    void Poll()
    {
        for (Climber& c : _climbers)
        {
            if (c.state == ClimberState::Gone)
                continue;
            Creature* unit = GetMap()->GetCreature(c.guid);
            if (!unit || !unit->IsAlive())
            {
                c.state = ClimberState::Gone;
                continue;
            }
            if (c.state == ClimberState::Waiting)
            {
                if (unit->IsInCombat())
                    Send(c, unit);
                else
                    HoldWaiting(unit);
                continue;
            }
            if (unit->IsInCombat() || unit->isMoving())
                continue;
            if (unit->GetPositionY() >= kStairLaneYMax)
            {
                if (Player* target = ArrivalTarget(unit))
                    unit->AI()->AttackStart(target);
            }
            else
                unit->GetMotionMaster()->MoveWaypoint(kWavePath, false);
        }
        if (_waveCleared || _climbers.empty() || !WaveCleared(States()))
            return;
        _waveCleared = true;
        if (_wave == 1)
        {
            _nextWaveAt = _now + Tune::kWaveGapMs;
            StairLog("wave-cleared", Acore::StringFormat("wave=1 time={} next_in={}", _now - _waveAt,
                Tune::kWaveGapMs));
        }
        else
        {
            StairLog("wave-cleared", Acore::StringFormat("wave=2 time={}", _now - _waveAt));
            _completeDue = true;
        }
    }

    // ---- PY4 Weegli's Barrels ---------------------------------------------------------------------------------------

    void UpdateBarrel()
    {
        if (_barrelResolveAt)
        {
            if (_now >= _barrelResolveAt)
                ResolveBarrel();
            return;
        }
        if (_now >= _barrelAt)
            StartBarrel();
    }

    void StartBarrel()
    {
        _barrelAt = _now + Tune::kBarrelEveryMs.Get(_heroic);
        _barrelResolveAt = _now + Tune::kBarrelWarnMs;
        ++_barrels;
        bool yelled = false;
        if (Creature* weegli = CrewCreature(Instance(), CREW_WEEGLI))
            if (weegli->IsAlive() && weegli->IsAIEnabled && weegli->AI())
            {
                weegli->AI()->Talk(ZfCrew::YELL_WEEGLI_BARRELS);
                yelled = true;
            }
        Creature* stalker = Stalker();
        if (!stalker)
            return;
        if (Creature* barrel = stalker->SummonCreature(NPC_ZF_WEEGLI_BARREL, ToPos(kBarrelLit),
            TEMPSUMMON_TIMED_DESPAWN, Tune::kBarrelLifeMs))
            _barrel = barrel->GetGUID();
        for (LaneTile const& t : LaneTiles())
        {
            MechanicRef ref = Mechanic::Line(stalker, ToPos(t.from), ToPos(t.to), t.width,
                Milliseconds(Tune::kBarrelWarnMs));
            ref.ZTolerance(Tune::kTileZToleranceYd).Tag(TAG_BARREL_TILE);
            if (!t.drawn)
                ref.NoTelegraph();
            if (ref.IsValid())
                _tiles.push_back(ref.Handle());
        }
        StairLog("barrel", Acore::StringFormat("n={} yelled={} tiles={} warn={} next_in={} heroic={}", _barrels,
            yelled ? 1 : 0, _tiles.size(), Tune::kBarrelWarnMs, _barrelAt - _now, _heroic ? 1 : 0));
    }

    // The barrel rolls: the players on the lane take the hit, the trolls on it lose half their health and go down
    // the stair; the barrel slides to the foot and goes off there.
    void ResolveBarrel()
    {
        _barrelResolveAt = 0;
        _tiles.clear();         // telegraph only: they resolve on their own this tick
        Creature* stalker = Stalker();
        GuidSet players;
        std::string names;
        for (auto const& ref : GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (!LivingPlayer(player)
                || !InBarrelLane(player->GetPositionX(), player->GetPositionY(), player->GetPositionZ()))
                continue;
            players.insert(player->GetGUID());
            names += (names.empty() ? "" : ",") + player->GetName();
        }
        if (stalker && !players.empty())
        {
            float const pct = Tune::kBarrelPct.Get(_heroic);
            DungeonKit::RegistryHitSpec spec;
            spec.pct = pct;
            spec.tankPct = pct;
            spec.school = kSchoolFire;
            spec.spellId = SPELL_BARREL_HIT;
            spec.weakened = true;           // ruling 23: both difficulties
            spec.rider = SPELL_KNOCKDOWN;
            spec.tag = TAG_BARREL;
            DungeonKit::RegistryHit(stalker, players, spec);
        }
        Creature* barrel = _barrel.IsEmpty() ? nullptr : GetMap()->GetCreature(_barrel);
        Unit* source = barrel ? static_cast<Unit*>(barrel) : static_cast<Unit*>(stalker);
        SpellInfo const* trollSpell = sSpellMgr->GetSpellInfo(SPELL_BARREL_TROLL);
        uint32 trolls = 0;
        for (Climber const& c : _climbers)
        {
            Creature* unit = c.state == ClimberState::Gone ? nullptr : GetMap()->GetCreature(c.guid);
            if (!unit || !unit->IsAlive()
                || !InBarrelLane(unit->GetPositionX(), unit->GetPositionY(), unit->GetPositionZ()))
                continue;
            ++trolls;
            uint32 const damage = uint32(TrollBarrelDamage(float(unit->GetMaxHealth())));
            if (source)
                Unit::DealDamage(source, unit, damage, nullptr, SPELL_DIRECT_DAMAGE, SPELL_SCHOOL_MASK_FIRE, trollSpell,
                    false);
            if (unit->IsAlive())
                unit->KnockbackFrom(kKnockSource.x, kKnockSource.y, Tune::kTrollKnockXY, Tune::kTrollKnockZ);
        }
        if (barrel && barrel->IsAIEnabled && barrel->AI())
            barrel->AI()->DoAction(ACTION_BARREL_ROLL);
        _barrel.Clear();
        StairLog("barrel-rolls", Acore::StringFormat("n={} players={} hit={} trolls={} pct={:.0f}", _barrels,
            players.size(), names.empty() ? "-" : names, trolls, Tune::kBarrelPct.Get(_heroic)));
    }

    // Everything this stage put in the world, gone (RB-1): the lane's tiles, the barrel, the trolls still standing,
    // the stalker (its encounter ends with it).
    void DespawnAll(char const* why)
    {
        Creature* stalker = Stalker();
        if (stalker)
            for (MechanicHandle const& h : _tiles)
                Mechanic::Cancel(stalker, h);
        _tiles.clear();
        if (Creature* barrel = _barrel.IsEmpty() ? nullptr : GetMap()->GetCreature(_barrel))
            barrel->DespawnOrUnsummon(Milliseconds(1));
        _barrel.Clear();
        uint32 removed = 0;
        for (Climber const& c : _climbers)
            if (Creature* unit = GetMap()->GetCreature(c.guid))
                if (unit->IsAlive())
                {
                    unit->DespawnOrUnsummon(Milliseconds(1));
                    ++removed;
                }
        _climbers.clear();
        if (stalker)
            stalker->DespawnOrUnsummon(Milliseconds(1));
        _stalker.Clear();
        _barrelResolveAt = 0;
        _wave = 0;
        _nextWaveAt = 0;
        if (removed)
            StairLog("despawn", Acore::StringFormat("why={} trolls={}", why, removed));
    }

    BossMechanics::SpotBounds _hold;
    ObjectGuid _stalker;
    ObjectGuid _barrel;
    std::vector<Climber> _climbers;
    std::vector<MechanicHandle> _tiles;
    uint32 _now = 0;
    uint32 _pollMs = 0;
    uint32 _wave = 0;
    uint32 _waveAt = 0;
    uint32 _sends = 0;
    uint32 _nextWaveAt = 0;
    uint32 _barrelAt = 0;
    uint32 _barrelResolveAt = 0;
    uint32 _barrels = 0;
    bool _waveCleared = false;
    bool _completeDue = false;
    bool _running = false;
    bool _heroic = false;
};

// ====================================================================================================================
// Stage 3, the Altar's director: wave 3, Sezz'ziz and Nekrum on the plaza (their fight is boss_sezzziz_rework.cpp)
// ====================================================================================================================
class AltarStage : public ZfPyramid::PyramidStage
{
public:
    explicit AltarStage(InstanceScript* instance) : ZfPyramid::PyramidStage(instance, PYRAMID_STAGE_ALTAR)
    {
        AltarDirectors()[instance] = this;
    }

    ~AltarStage() override
    {
        AltarDirectors().erase(Instance());
    }

    // In play and idle (stage 2 won, a wipe, a reload): the Altar gathers on the plaza, out of the crew's reach
    // (immune to NPCs: the crew at the stair's foot never start it), until the stage starts.
    void OnWait() override
    {
        if (_running)
            return;
        Spawn("wait");
        for (ObjectGuid const& guid : _units)
            if (Creature* unit = GetMap()->GetCreature(guid))
                if (unit->IsAlive() && !unit->IsInCombat())
                    unit->SetImmuneToNPC(true);
    }

    // The descent (5 s after stage 2, the instance) or a pull of the idle Altar: the Altar fights, carrying every stack
    // of Offerings or Blood Price collected so far.
    void OnStart(bool restart) override
    {
        ZfPyramid::PyramidStage::OnStart(restart);
        Spawn("start");
        _running = true;
        _linkMs = 0;
        uint32 n = 0;
        for (ObjectGuid const& guid : _units)
            if (Creature* unit = GetMap()->GetCreature(guid))
                if (unit->IsAlive())
                {
                    unit->SetImmuneToNPC(false);
                    Buffs().Track(unit);
                    ++n;
                }
        ZfPyramid::PyramidRead const r = ZfPyramid::ReadPyramid(Instance());
        AltarLog("stage-start", Acore::StringFormat("restart={} units={} heroic={} offerings={} bloodprice={} crew={}",
            restart ? 1 : 0, n, Heroic() ? 1 : 0, r.offerings, r.bloodPrice, Instance()->GetData(DATA_CREW_ALIVE)));
    }

    void OnUpdate(uint32 diff) override
    {
        ZfPyramid::PyramidStage::OnUpdate(diff);
        _linkMs += diff;
        if (_linkMs < ZfAltar::Tune::kLinkPollMs)
            return;
        _linkMs = 0;
        Link();
    }

    void OnEnd(bool won) override
    {
        ZfPyramid::PyramidStage::OnEnd(won);
        _running = false;
        if (won)
        {
            // The Pyramid is done: every wound closes; whoever still stands of the Altar is plain trash now.
            ZfPyramid::ClearWounds(Instance());
            uint32 left = 0;
            for (ObjectGuid const& guid : AllUnits())
                if (Creature* unit = GetMap()->GetCreature(guid))
                    if (unit->IsAlive())
                    {
                        unit->SetImmuneToNPC(false);
                        ++left;
                    }
            AltarLog("stage-end", Acore::StringFormat("won left={}", left));
        }
        else
        {
            uint32 const removed = DespawnAll();
            AltarLog("stage-end", Acore::StringFormat("lost removed={}", removed));
        }
        _units.clear();
        _adds.clear();
        if (Creature* stalker = _stalker.IsEmpty() ? nullptr : GetMap()->GetCreature(_stalker))
            stalker->DespawnOrUnsummon(Milliseconds(1));
        _stalker.Clear();
    }

    // Sezz'ziz's adds (and any Sandfury of the encounter made while the Altar is in play) go with the Altar on a wipe.
    void OnCreatureCreate(Creature* creature) override
    {
        ZfPyramid::PyramidStage::OnCreatureCreate(creature);
        if (_spawning || !creature || !IsSpecialist(creature->GetEntry()))
            return;
        if (std::find(_units.begin(), _units.end(), creature->GetGUID()) == _units.end())
            _adds.push_back(creature->GetGUID());
    }

    bool Running() const { return _running; }

    std::string State()
    {
        uint32 alive = 0;
        uint32 fighting = 0;
        for (ObjectGuid const& guid : AllUnits())
            if (Creature* unit = GetMap()->GetCreature(guid))
                if (unit->IsAlive())
                {
                    ++alive;
                    fighting += unit->IsInCombat() ? 1 : 0;
                }
        return Acore::StringFormat("running={} units={} adds={} alive={} fighting={} tracked={} bleeding={}",
            _running ? 1 : 0, _units.size(), _adds.size(), alive, fighting, Buffs().Tracked(), Buffs().Bleeding());
    }

private:
    Map* GetMap() const { return Instance()->instance; }

    std::vector<ObjectGuid> AllUnits() const
    {
        std::vector<ObjectGuid> all(_units.begin(), _units.end());
        all.insert(all.end(), _adds.begin(), _adds.end());
        return all;
    }

    // Wave 3 (5 trolls), Sezz'ziz and Nekrum at the stock wave 3 points, once (the living ones are kept). The trolls'
    // corpses stay kCorpseMs; Sezz'ziz's and Nekrum's stay (his carries the Pyramid's loot).
    void Spawn(char const* why)
    {
        bool any = false;
        for (ObjectGuid const& guid : _units)
            if (Creature* unit = GetMap()->GetCreature(guid))
                if (unit->IsAlive())
                    any = true;
        if (any)
            return;
        _units.clear();
        if (_stalker.IsEmpty())
            if (TempSummon* stalker = GetMap()->SummonCreature(NPC_ZF_PYRAMID_STALKER, ToPos(kPlazaCenter)))
                _stalker = stalker->GetGUID();
        Creature* stalker = _stalker.IsEmpty() ? nullptr : GetMap()->GetCreature(_stalker);
        _spawning = true;
        for (std::size_t index : WaveIndexes(3))
        {
            uint32 const entry = WaveEntry(index);
            bool const boss = entry == NPC_SEZZZIZ || entry == NPC_NEKRUM;
            Position const at = ToPos(kWaveSpawns[index].at);
            TempSummon* unit = nullptr;
            if (stalker)
                unit = stalker->SummonCreature(entry, at, boss ? TEMPSUMMON_MANUAL_DESPAWN
                    : TEMPSUMMON_CORPSE_TIMED_DESPAWN, boss ? 0 : Tune::kCorpseMs);
            else
                unit = GetMap()->SummonCreature(entry, at);
            if (!unit)
                continue;
            unit->SetHomePosition(at);
            unit->GetMotionMaster()->Clear();
            unit->GetMotionMaster()->MoveIdle();
            unit->SetReactState(REACT_AGGRESSIVE);
            _units.push_back(unit->GetGUID());
        }
        _spawning = false;
        AltarLog("spawn", Acore::StringFormat("why={} units={}", why, _units.size()));
    }

    // Every kLinkPollMs: an Altar unit out of combat joins a fellow that fights (the whole Altar is one pull, as
    // Sezz'ziz's stock CallAssistance made it); an idle one the stock SmartAI walks goes back.
    void Link()
    {
        Unit* foe = nullptr;
        Creature* fighter = nullptr;
        std::vector<Creature*> idle;
        for (ObjectGuid const& guid : AllUnits())
        {
            Creature* unit = GetMap()->GetCreature(guid);
            if (!unit || !unit->IsAlive())
                continue;
            if (unit->IsInCombat())
            {
                if (!foe && unit->GetVictim())
                {
                    foe = unit->GetVictim();
                    fighter = unit;
                }
                continue;
            }
            idle.push_back(unit);
        }
        for (Creature* unit : idle)
        {
            if (!foe || !foe->IsAlive() || !unit->IsWithinDist(foe, ZfAltar::Tune::kLinkRangeYd))
            {
                HoldWaiting(unit);
                continue;
            }
            if (unit->IsImmuneToNPC() && !foe->IsPlayer())
                continue;       // idle and the foe a crew member: the Altar has not started
            if (unit->IsAIEnabled && unit->AI())
                unit->AI()->AttackStart(foe);
        }
        if (foe && !idle.empty() && !_linkedLogged)
        {
            _linkedLogged = true;
            AltarLog("link", Acore::StringFormat("first={} foe={} joined={}", fighter->GetEntry(), foe->GetName(),
                idle.size()));
        }
        if (!foe)
            _linkedLogged = false;
    }

    uint32 DespawnAll()
    {
        uint32 removed = 0;
        for (ObjectGuid const& guid : AllUnits())
            if (Creature* unit = GetMap()->GetCreature(guid))
            {
                unit->DespawnOrUnsummon(Milliseconds(1));
                ++removed;
            }
        return removed;
    }

    ObjectGuid _stalker;
    GuidVector _units;
    GuidVector _adds;
    uint32 _linkMs = 0;
    bool _running = false;
    bool _spawning = false;
    bool _linkedLogged = false;
};

// ====================================================================================================================
// `.dbtest zf stair`
// ====================================================================================================================
namespace
{
    StairStage* StairOf(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return nullptr;
        auto it = StairDirectors().find(instance);
        if (it == StairDirectors().end())
        {
            handler->SendErrorMessage("{}", "The Stair is not in play (see `.dbtest zf state`; `.dbtest zf stage 2`).");
            return nullptr;
        }
        return it->second;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return ZfTest::ShowBossInfo(handler, NPC_SEZZZIZ, BOSS_PYRAMID);
    }

    // `.dbtest zf stair state`: the Stair's waves and barrels, the Altar's units, the Pyramid's counts.
    bool HandleState(ChatHandler* handler)
    {
        InstanceScript* instance = ZfTest::GmInstance(handler);
        if (!instance)
            return false;
        ZfPyramid::PyramidRead const r = ZfPyramid::ReadPyramid(instance);
        handler->PSendSysMessage("Pyramid: stage={} running={} offerings={} bloodprice={} crew={}",
            kPyramidStageNames[std::min<uint32>(r.stage, PYRAMID_STAGE_DONE)], r.running ? 1 : 0, r.offerings,
            r.bloodPrice, instance->GetData(DATA_CREW_ALIVE));
        if (auto it = StairDirectors().find(instance); it != StairDirectors().end())
            handler->PSendSysMessage("Stair: {}", it->second->State());
        if (auto it = AltarDirectors().find(instance); it != AltarDirectors().end())
            handler->PSendSysMessage("Altar: {}", it->second->State());
        return true;
    }

    // `.dbtest zf stair barrel`: a barrel now (PY4).
    bool HandleBarrel(ChatHandler* handler)
    {
        StairStage* stair = StairOf(handler);
        if (!stair)
            return false;
        if (!stair->TestBarrel())
        {
            handler->SendErrorMessage("{}", "Refused: the Stair is not running, or a barrel is already lit.");
            return false;
        }
        handler->PSendSysMessage("{}", "Stair: a barrel (PY4).");
        return true;
    }

    // `.dbtest zf stair send`: the next group up the stair now.
    bool HandleSend(ChatHandler* handler)
    {
        StairStage* stair = StairOf(handler);
        if (!stair)
            return false;
        if (!stair->TestSend())
        {
            handler->SendErrorMessage("{}", "Refused: the Stair is not running, or nobody is waiting.");
            return false;
        }
        handler->PSendSysMessage("{}", "Stair: a group sent.");
        return true;
    }

    // Sezz'ziz's and Nekrum's mechanics through their AI (boss_sezzziz_rework.cpp): DoAction, in combat only.
    bool AltarAction(ChatHandler* handler, uint32 entry, int32 action, char const* what)
    {
        Creature* unit = ZfTest::FindBoss(handler, entry);
        if (!unit)
            return false;
        if (!unit->IsAIEnabled || !unit->AI() || !unit->AI()->GetData(ZfAltar::DATA_TEST_ENGAGED))
        {
            handler->SendErrorMessage("{}", "It must be in combat (and running its rework script).");
            return false;
        }
        unit->AI()->DoAction(action);
        handler->PSendSysMessage("{}: {} on its next tick.", unit->GetName(), what);
        return true;
    }

    bool HandleOffering(ChatHandler* handler)
    {
        return AltarAction(handler, NPC_SEZZZIZ, ZfAltar::ACTION_TEST_OFFERING, "Blood Offering (PY12)");
    }

    bool HandleScream(ChatHandler* handler)
    {
        return AltarAction(handler, NPC_SEZZZIZ, ZfAltar::ACTION_TEST_SCREAM, "Psychic Scream (PY13)");
    }

    bool HandleAdds(ChatHandler* handler)
    {
        return AltarAction(handler, NPC_SEZZZIZ, ZfAltar::ACTION_TEST_ADDS, "the next add set (PY14)");
    }

    bool HandleGutchew(ChatHandler* handler)
    {
        if (InstanceScript* instance = ZfTest::GmInstance(handler); instance && !instance->instance->IsHeroic())
        {
            handler->SendErrorMessage("{}", "Gutchew is heroic only.");
            return false;
        }
        return AltarAction(handler, NPC_NEKRUM, ZfAltar::ACTION_TEST_GUTCHEW, "Gutchew");
    }

    // `.dbtest zf stair sezzziz`: his counters.
    bool HandleSezzziz(ChatHandler* handler)
    {
        Creature* unit = ZfTest::FindBoss(handler, NPC_SEZZZIZ);
        if (!unit || !unit->IsAIEnabled || !unit->AI())
            return false;
        CreatureAI* ai = unit->AI();
        handler->PSendSysMessage("Sezz'ziz: engaged={} adds={} calls={} offerings={} frenzy={}",
            ai->GetData(ZfAltar::DATA_TEST_ENGAGED), ai->GetData(ZfAltar::DATA_TEST_ADDS),
            ai->GetData(ZfAltar::DATA_TEST_CALLS), ai->GetData(ZfAltar::DATA_TEST_OFFERINGS),
            ai->GetData(ZfAltar::DATA_TEST_FRENZY));
        return true;
    }

    ChatCommandTable const& StairTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",     HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",    HandleState,    SEC_GAMEMASTER, Console::No },
            { "barrel",   HandleBarrel,   SEC_GAMEMASTER, Console::No },
            { "send",     HandleSend,     SEC_GAMEMASTER, Console::No },
            { "offering", HandleOffering, SEC_GAMEMASTER, Console::No },
            { "scream",   HandleScream,   SEC_GAMEMASTER, Console::No },
            { "adds",     HandleAdds,     SEC_GAMEMASTER, Console::No },
            { "gutchew",  HandleGutchew,  SEC_GAMEMASTER, Console::No },
            { "sezzziz",  HandleSezzziz,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_pyramid_stair_rework()
{
    RegisterDungeonReworkCreatureAI(npc_zf_sandfury_berserker, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_sandfury_hexmaster, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_sandfury_witch_doctor, ZulFarrakRework::kInstanceScriptName);
    RegisterDungeonReworkCreatureAI(npc_zf_weegli_barrel, ZulFarrakRework::kInstanceScriptName);
    RegisterSpellScript(spell_zf_sandfury_hex);
    RegisterPyramidStage(PYRAMID_STAGE_STAIR, [](InstanceScript* instance)
    {
        return std::make_unique<StairStage>(instance);
    });
    RegisterPyramidStage(PYRAMID_STAGE_ALTAR, [](InstanceScript* instance)
    {
        return std::make_unique<AltarStage>(instance);
    });
    ZfCrew::RegisterCrewModeHandler(CrewMode::Ally, [](ZfCrew::BlyCrewAI&)
    {
        return std::make_unique<StairAllyHandler>();
    }, kCrewFighters);
    ZfTest::RegisterBoss("stair", StairTestCommands());
}
