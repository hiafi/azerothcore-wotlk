/*
 * mod-dungeon-bosses, Scarlet Monastery D13: the Last Stand, Scarlet Commander Mograine (3976) and the Crusade's
 * companies (300950-300955) (HUB rulings 45, 46). Build spec CATH "The Last Stand" (docs/dungeons/
 * scarlet-monastery-4-cathedral.md, LS0-LS7), handoff sections 3.5 (row D13), 3.6, 3.8 (NM: the nave, the crossing, the
 * arm ends), 7 #16 A (the Ashbringer sweep leaves every rework entry out: S0's AshbringerSweeps), #19 A (the nave's
 * stock spawns removed: rev_last_stand_scarlet_monastery.sql), #20 A (the chest), #33 A (the charge lines). Replaces
 * his SmartAI (W2-SETUP's rev drops rows 0-28 and the lists 397600-397602) and the stock Cathedral pull. Re-implements
 * the stock fake death (SmartAI 3976 row 9 / list 397600: invincible at 1%, the dead stand state, evade off) from the
 * stock AzerothCore data; the instance keeps the stock event state split in two (S0). The stock Ashbringer cameo (rows
 * 0, 25-27, list 397602) lives here too, armed by the instance only when it accepts the Ashbringer (HANDOFF s10,
 * STAGE-R-1-KIT m-1 default c: ArmAshbringerCameo / SpellHit). Bound by apps/dbc-tools
 * source/npcs/scarlet_monastery/last_stand.py. Pure rules: LastStandLogic.h; the finale's hooks: MograineFight.h.
 *
 *   LS0  The Chapel Door  the instance's go_sm_chapel_door (or the crossing restart after a wipe) writes slot 5
 *                         IN_PROGRESS and sends ACTION_SM_LAST_STAND_START: he yells (line 7) from the altar steps and,
 *                         2 s later, calls the first company. A pull of him before that starts the stand too
 *   LS1  The Companies    three, called in order (line 8 / 9 / 10): the Chapel Guard from the north arm, the Pyre
 *                         Brethren from the south, the Clergy from both. Each marches from its arm end to the arm's
 *                         mouth (about 4 s at 8 yd/s), then falls on the group wherever it stands (the nearest tank,
 *                         else the nearest player; every player on the stand's floor at 0 threat, rule 11). The next is
 *                         called when the current one falls or 30 s (heroic 25 s) after it arrived. He waits on the
 *                         altar steps, passive and attackable: a pull brings him down early, the companies keep coming
 *   LS1a Devotion Aura    the Captain re-applies it every second to every company unit within 15 yd (himself too):
 *                         30% / 40% less damage taken, gone with him
 *   LS1b Consecration     each Monk, 4 s after arriving and every 12 s: 6 yd under itself for 8 s, 10% / 15% Holy a
 *                         second (registry persistent Zone, tank row on the tank)
 *   LS1c Fireball         each Wizard, 3 s after arriving and every 8 s: a 2.5 s Fire cast at a random player,
 *                         15% / 20% (the kit's refflat damage); interruptible (a reward)
 *   LS2  Purifying Flame  each Wizard, 6 s after arriving and every 12 s: a 2.5 s Fire cast marking a 5 yd circle at
 *                         a random player's spot; on the cast's end 30% / 45% plus Weakened, then fire 6 / 10 s at
 *                         10% / 15% a second. Interrupted: no circle
 *   LS3  Greater Heal     one cast per company every 10 s (5 s after it arrives): the Chapel Guard's (and the Last
 *                         Reserve's) Chaplain, the Clergy's Abbots taking turns; 3 s Holy, the most hurt member +30%.
 *                         Heroic: a kick is expected; a cast that lands heals every member of the company 50%
 *   LS4  Hammer of Justice from his descent (M) + 8 s, every 20 s: a 5 yd circle on a random player (heroic two), 2 s;
 *                         everyone in it is stunned 2 s and takes 20% / 30% Holy (others caught: Weakened too)
 *   LS5  Divine Storm     M + 12 s, every 15 s: a 2 s wind-up, then 8 / 10 yd round him: others 30% / 45% plus
 *                         Weakened, the tank its own 15% / 25% of the tank row
 *   LS6  Charge (heroic)  every Champion of the Chapel Guard (and the Last Reserve) stops at its arm's mouth: a 3 yd
 *                         line from there to a random player in its line of sight, 2 s, then it charges along it: 45%
 *                         plus Weakened
 *   LS7  Last Reserve (H) at his 50%: line 11 and one more Chapel Guard from both arms
 *   End  the third company falls: line 0, he comes down and fights at the crossing (Crusader Strike, Retribution Aura,
 *        the Hammer, Divine Storm). At 1% he falls, once no company is left to call or alive (until then he holds at
 *        1% and fights on): he walks to his body spot before the altar and lies there (not selectable, immune); slot 5
 *        DONE (the instance credits 212301, opens the High Inquisitor's Door and wakes Whitemane's vigil); the chest
 *        (301330 / heroic 301331) appears at the altar steps
 *   Wipe his evade, or nobody alive on the stand's floor for 5 s while he waits: the companies go, he stands on the
 *        altar again, slot 5 back to NOT_STARTED (the door stays open; the instance's crossing restart re-arms)
 *
 * The companies' registry mechanics are owned by a hidden conductor (the wave 2 generic stalker 300958, its level set
 * to his, combat disallowed) so their hits never pull Mograine into combat (a registry hit's original caster is the
 * owner) and their Weakened lasts the stand; until that template exists each company unit owns its own (logged at each
 * start). The ground and fire looks are dynamic objects of the same owner. Every firing logs one INFO line
 * "sm laststand <mechanic> ..." (module.dungeonbosses). Bot sensitive geometry (RB-8): every planned spot keeps to the
 * stand's floor (LastStandLogic.h StandFloor: landing, nave, crossing, altar platform).
 */

#include "ArenaGuard.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Containers.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "LastStandLogic.h"
#include "Map.h"
#include "MograineFight.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScarletMonasteryKit.h"
#include "ScarletMonasteryRework.h"
#include "ScarletMonasteryTestCommand.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <memory>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace ScarletMonasteryRework;
using namespace SmLastStand;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;
using DungeonKit::IsHeroicMap;

namespace
{
    char const* const kBoss = "laststand";

    uint32 constexpr POINT_MOUTH = 1;           // a company unit at its arm's mouth
    uint32 constexpr POINT_CHARGE = 2;          // a Champion's charge along its line (heroic)
    uint32 constexpr POINT_BODY = 3;            // Mograine's walk to his body spot

    uint32 constexpr GROUP_STAND = 1;           // the first call
    uint32 constexpr GROUP_KIT = 2;             // his kit's delayed parts (the hammer's throw and hits, the storm)

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    void LogLs(char const* mechanic, std::string const& detail = {})
    {
        DungeonKit::LogMechanic(kLogDungeon, kBoss, mechanic, detail);
    }

    // The bots' hard bounds while a mechanic of the stand is in view: LastStandLogic.h StandFloor.
    BossMechanics::SpotBounds StandFloorBounds()
    {
        BossMechanics::SpotBounds bounds;
        for (Box const& b : kFloorBoxes)
            bounds.Polygon({ Position(b.minX, b.minY, kCrossingCenter.z, 0.f),
                Position(b.maxX, b.minY, kCrossingCenter.z, 0.f), Position(b.maxX, b.maxY, kCrossingCenter.z, 0.f),
                Position(b.minX, b.maxY, kCrossingCenter.z, 0.f) }, kFloorZMin, kFloorZMax);
        return bounds;
    }

    bool IsTankFor(Unit const* owner, Player const* p)
    {
        return BossMechanics::GetRoleProvider().Get(owner, p) == BossMechanics::Role::Tank;
    }

    // The players of the stand: alive, not game masters, on its zone (the landing, the nave, the crossing, the altar).
    std::vector<Player*> PlayersOnTheStand(Map* map)
    {
        std::vector<Player*> out;
        if (!map)
            return out;
        for (auto const& ref : map->GetPlayers())
        {
            Player* p = ref.GetSource();
            if (!p || !p->IsAlive() || p->IsGameMaster() || !p->IsInWorld())
                continue;
            if (InStandZone({ p->GetPositionX(), p->GetPositionY() }, p->GetPositionZ()))
                out.push_back(p);
        }
        return out;
    }

    // Whom `unit` attacks when it arrives (rule 19): the nearest tank on the stand, else the nearest player there.
    Player* ArrivalTarget(Creature* unit)
    {
        std::vector<Player*> players;
        std::vector<ArrivalCandidate> candidates;
        for (Player* p : PlayersOnTheStand(unit->GetMap()))
        {
            if (!unit->IsValidAttackTarget(p))
                continue;
            ArrivalCandidate c;
            c.distance = unit->GetDistance(p);
            c.tank = IsTankFor(unit, p);
            players.push_back(p);
            candidates.push_back(c);
        }
        int const pick = PickArrival(candidates);
        return pick < 0 ? nullptr : players[static_cast<std::size_t>(pick)];
    }

    // Every player of the stand at 0 threat (rule 11: a unit with one threat entry evades when it drops), the target
    // on top.
    void JoinStand(Creature* unit, Player* target)
    {
        for (Player* p : PlayersOnTheStand(unit->GetMap()))
            if (unit->IsValidAttackTarget(p))
                unit->AddThreat(p, 0.f);
        if (target)
            unit->AddThreat(target, 10.f);
    }

    // The test commands' forced mechanics (`.dbtest sm laststand ...`).
    enum class TestKind : uint8
    {
        Start,
        Call,
        Descend,
        Hammer,
        Storm,
        Reserve,
        Fall,
        Chest,
        Clear,
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// What a company unit asks of Mograine's AI (the summoner): the stand's state, the mechanics' owner, the company lists.
// ---------------------------------------------------------------------------------------------------------------------
class LastStandHost
{
public:
    virtual ~LastStandHost() = default;

    virtual bool StandRunning() const = 0;
    virtual bool StandHeroic() const = 0;
    // The owner of the companies' registry mechanics: the conductor (nullptr when it could not be summoned: the unit
    // then owns its own).
    virtual Unit* MechanicOwner() = 0;
    // The living units of company `index` (-1: of every company).
    virtual std::vector<Creature*> CompanyUnits(int index) = 0;
    // LS6: a charge target for a Champion of company `index` at its arm's mouth, one the company has not taken yet when
    // possible (in line of sight of the Champion).
    virtual Player* PickChargeTarget(int index, Creature* champion) = 0;
    virtual void MemberArrived(int index, Creature* unit) = 0;
};

namespace
{
    LastStandHost* HostOf(Creature const* unit)
    {
        TempSummon const* summon = unit ? unit->ToTempSummon() : nullptr;
        Unit* summoner = summon ? summon->GetSummonerUnit() : nullptr;
        Creature* boss = summoner ? summoner->ToCreature() : nullptr;
        if (!boss || !boss->IsAlive() || !boss->IsAIEnabled)
            return nullptr;
        return dynamic_cast<LastStandHost*>(boss->AI());
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// The companies: one AI for the six entries (the role follows the entry). The march, the arrival, the stock trash kit
// the build spec keeps (Holy Strike, Kick, Thrash, Fire Shield, Renew, Power Word: Shield, Frenzy) and LS1a-LS3, LS6.
// ---------------------------------------------------------------------------------------------------------------------
struct npc_sm_last_stand_company : public ScriptedAI
{
    explicit npc_sm_last_stand_company(Creature* creature) : ScriptedAI(creature) { }

    void Reset() override
    {
        Equipment const e = EquipmentOf(me->GetEntry());
        me->SetVirtualItem(0, e.mainHand);
        me->SetVirtualItem(1, e.offHand);
    }

    // Mograine's summon: company `index` of kind `kind`, marching from `arm`'s end to its mouth.
    void Setup(int index, Company kind, Arm arm, bool heroic, bool charges)
    {
        _index = index;
        _kind = kind;
        _arm = arm;
        _heroic = heroic;
        _charges = charges;
        _arrived = false;
        _setupAt = _clockMs;
        me->SetReactState(REACT_DEFENSIVE);
        me->SetWalk(false);
        Point3 const mouth = ArmMouth(arm);
        me->GetMotionMaster()->MovePoint(POINT_MOUTH, mouth.x, mouth.y, mouth.z);
    }

    // A Champion holding its charge line keeps its spot until the charge (2 s); anything else fights at once.
    void AttackStart(Unit* who) override
    {
        if (_chargeAtMs != 0)
            return;
        ScriptedAI::AttackStart(who);
    }

    // A unit attacked on its march fights at once (its arrival).
    void JustEngagedWith(Unit* /*who*/) override
    {
        if (!_arrived && _chargeAtMs == 0)
            Arrive("engaged");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE && type != EFFECT_MOTION_TYPE)
            return;
        if (id == POINT_MOUTH && !_arrived)
        {
            if (_charges && _chargeAtMs == 0)
                BeginCharge();
            else if (_chargeAtMs == 0)
                Arrive("mouth");
        }
        else if (id == POINT_CHARGE && _chargeAtMs != 0)
            EndCharge("landed");
    }

    // While the stand runs, a unit that lost its target picks another player of the stand instead of walking home.
    void EnterEvadeMode(EvadeReason why) override
    {
        if (LastStandHost* host = HostOf(me))
            if (host->StandRunning() && me->IsAlive())
                if (Player* target = ArrivalTarget(me))
                {
                    JoinStand(me, target);
                    ScriptedAI::AttackStart(target);
                    return;
                }
        ScriptedAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* /*killer*/) override
    {
        // A Purifying Flame still on its cast bar draws no circle (the cast died with it).
        CancelFlame("died");
        LogLs("member-died", Acore::StringFormat("company={} {} guid={}", _index, MemberName(me->GetEntry()),
            me->GetGUID().GetCounter()));
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        switch (spell->Id)
        {
            case SPELL_LS_PURIFYING_FLAME_CAST:
                // The cast ran: the circle lands now (the registry resolves it on its next tick).
                if (_flame)
                    if (Unit* owner = FlameOwner())
                        Mechanic::Detonate(owner, _flame);
                LogLs("flame-landed", Acore::StringFormat("wizard={}", me->GetGUID().GetCounter()));
                _flame = MechanicHandle();
                break;
            case SPELL_LS_GREATER_HEAL_H:
                HealCompany();
                break;
            case SPELL_LS_GREATER_HEAL:
                LogLs("greater-heal-landed", Acore::StringFormat("healer={} pct={}", me->GetGUID().GetCounter(),
                    kGreaterHealPct));
                break;
            default:
                break;
        }
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (!spell)
            return;
        switch (spell->Id)
        {
            case SPELL_LS_PURIFYING_FLAME_CAST:
                CancelFlame("kicked");
                break;
            case SPELL_LS_GREATER_HEAL:
            case SPELL_LS_GREATER_HEAL_H:
                LogLs("greater-heal-kicked", Acore::StringFormat("healer={}", me->GetGUID().GetCounter()));
                break;
            case SPELL_LS_FIREBALL:
                LogLs("fireball-kicked", Acore::StringFormat("wizard={}", me->GetGUID().GetCounter()));
                break;
            default:
                break;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;

        if (!_arrived)
        {
            if (_chargeAtMs != 0)
            {
                UpdateCharge();
                return;
            }
            // A company that never reaches its mouth (a blocked path) fights where it stands.
            if (_index >= 0 && _clockMs >= _setupAt + kMarchGiveUpMs)
                Arrive("give-up");
            return;
        }

        // LS1a: the Captain's aura runs whether he has a victim or not.
        if (me->GetEntry() == NPC_SM_CAPTAIN_OF_THE_GUARD && _clockMs >= _nextDevotionMs)
        {
            _nextDevotionMs = _clockMs + kDevotionPulseMs;
            PulseDevotion();
        }

        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        UpdateKit();
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Orders from Mograine
    // ----------------------------------------------------------------------------------------------------------------

    bool Arrived() const { return _arrived; }

    // Free to start a cast now: alive, arrived, not casting and not stopped (stun, silence, pacify).
    bool FreeToCast() const
    {
        return me->IsAlive() && _arrived && !me->HasUnitState(UNIT_STATE_CASTING)
            && !me->HasUnitState(UNIT_STATE_CONTROLLED) && !me->HasUnitFlag(UNIT_FLAG_SILENCED)
            && !me->HasUnitFlag(UNIT_FLAG_PACIFIED);
    }

    // LS3: the company's heal this turn on `target` (normal: 30% of it; heroic: the bar of the company heal).
    bool CastGreaterHeal(Creature* target)
    {
        if (!target || !FreeToCast())
            return false;
        me->StopMoving();
        uint32 const spell = _heroic ? SPELL_LS_GREATER_HEAL_H : SPELL_LS_GREATER_HEAL;
        return me->CastSpell(target, spell, false) == SPELL_CAST_OK;
    }

    int Index() const { return _index; }

private:
    // ----------------------------------------------------------------------------------------------------------------
    // The arrival and the heroic charge
    // ----------------------------------------------------------------------------------------------------------------

    void Arrive(char const* why)
    {
        if (_arrived)
            return;
        _arrived = true;
        _arrivedAt = _clockMs;
        me->SetReactState(REACT_AGGRESSIVE);
        switch (me->GetEntry())
        {
            case NPC_SM_COMPANY_MONK:
                me->CastSpell(me, SPELL_THRASH, true);
                _nextConsecrationMs = _clockMs + kConsecrationFirstMs;
                break;
            case NPC_SM_COMPANY_WIZARD:
                me->CastSpell(me, SPELL_FIRE_SHIELD, true);
                _nextFireShieldMs = _clockMs + kFireShieldEveryMs;
                _nextFireballMs = _clockMs + kFireballFirstMs;
                _nextFlameMs = _clockMs + kFlameFirstMs;
                break;
            case NPC_SM_CAPTAIN_OF_THE_GUARD:
                me->CastSpell(me, SPELL_LS_DEVOTION_PULSE, true);
                _nextDevotionMs = _clockMs;
                break;
            case NPC_SM_CHAPEL_GUARD_CHAMPION:
                _nextHolyStrikeMs = _clockMs + urand(kHolyStrikeFirstMinMs, kHolyStrikeFirstMaxMs);
                break;
            case NPC_SM_COMPANY_CHAPLAIN:
            case NPC_SM_COMPANY_ABBOT:
                _nextRenewMs = _clockMs + kRenewEveryMs / 2;
                _nextShieldMs = _clockMs + kShieldEveryMs / 4;
                break;
            default:
                break;
        }
        Player* target = ArrivalTarget(me);
        JoinStand(me, target);
        if (target)
            ScriptedAI::AttackStart(target);
        if (LastStandHost* host = HostOf(me))
            host->MemberArrived(_index, me);
        LogLs("member-arrived", Acore::StringFormat("company={} {} why={} target={}", _index,
            MemberName(me->GetEntry()), why, target ? target->GetName() : std::string("none")));
    }

    // LS6 (heroic): a 3 yd line from the mouth to a player in sight, 2 s, then the charge along it.
    void BeginCharge()
    {
        LastStandHost* host = HostOf(me);
        Player* target = host ? host->PickChargeTarget(_index, me) : nullptr;
        if (!target)
        {
            LogLs("charge-none", Acore::StringFormat("champion={} nobody in sight of the mouth",
                me->GetGUID().GetCounter()));
            Arrive("no-charge");
            return;
        }
        Unit* owner = host->MechanicOwner();
        if (!owner)
            owner = me;
        DungeonKit::LineStrikeSpec spec;
        spec.width = kChargeWidthYd;
        spec.overrun = kChargeOverrunYd;
        spec.warn = Ms(kChargeWarnMs);
        spec.pct = kChargePct;
        spec.tankPct = kChargePct;
        spec.spellId = SPELL_LS_CHARGE_HIT;
        spec.weakened = true;
        spec.tag = TAG_LS_CHARGE;
        Position const from = me->GetPosition();
        Position const to = target->GetPosition();
        DungeonKit::LineStrikeResult const line = DungeonKit::LineStrike(owner, from, to, spec);
        if (!line.handle)
        {
            Arrive("charge-refused");
            return;
        }
        _chargeEnd = line.end;
        _chargeAtMs = _clockMs + kChargeWarnMs;
        _chargeGiveUpMs = _chargeAtMs + 4000;
        _charging = false;
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->SetFacingToObject(target);
        LogLs("charge", Acore::StringFormat("champion={} target={} length={:.1f} pct={:.0f}",
            me->GetGUID().GetCounter(), target->GetName(), line.length, kChargePct));
    }

    void UpdateCharge()
    {
        if (!_charging && _clockMs >= _chargeAtMs)
        {
            _charging = true;
            me->CastSpell(me, SPELL_LS_CHARGE_LOOK, true);
            me->GetMotionMaster()->MoveCharge(_chargeEnd.GetPositionX(), _chargeEnd.GetPositionY(),
                _chargeEnd.GetPositionZ(), kChargeSpeed, POINT_CHARGE);
        }
        else if (_clockMs >= _chargeGiveUpMs)
            EndCharge("give-up");
    }

    void EndCharge(char const* why)
    {
        _chargeAtMs = 0;
        _charging = false;
        Arrive(why);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The kit
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateKit()
    {
        switch (me->GetEntry())
        {
            case NPC_SM_CHAPEL_GUARD_CHAMPION:
                if (_clockMs >= _nextHolyStrikeMs)
                {
                    Unit* victim = me->GetVictim();
                    if (victim && me->IsWithinMeleeRange(victim)
                        && me->CastSpell(victim, SPELL_HOLY_STRIKE, false) == SPELL_CAST_OK)
                        _nextHolyStrikeMs = _clockMs + urand(kHolyStrikeEveryMinMs, kHolyStrikeEveryMaxMs);
                    else
                        _nextHolyStrikeMs = _clockMs + kRetryMs;
                }
                break;
            case NPC_SM_COMPANY_MONK:
                UpdateKick();
                if (_clockMs >= _nextConsecrationMs)
                {
                    LayConsecration();
                    _nextConsecrationMs = _clockMs + kConsecrationEveryMs;
                }
                break;
            case NPC_SM_COMPANY_WIZARD:
                if (_clockMs >= _nextFireShieldMs)
                {
                    if (!me->HasAura(SPELL_FIRE_SHIELD))
                        me->CastSpell(me, SPELL_FIRE_SHIELD, true);
                    _nextFireShieldMs = _clockMs + kFireShieldEveryMs;
                }
                if (_clockMs >= _nextFlameMs)
                    _nextFlameMs = _clockMs + (CastFlame() ? kFlameEveryMs : kRetryMs);
                else if (_clockMs >= _nextFireballMs)
                    _nextFireballMs = _clockMs + (CastFireball() ? kFireballEveryMs : kRetryMs);
                break;
            case NPC_SM_COMPANY_CHAPLAIN:
                if (_kind == Company::Clergy && _clockMs >= _nextShieldMs)
                    _nextShieldMs = _clockMs + (CastShield() ? kShieldEveryMs : kRetryMs * 2);
                else if (_clockMs >= _nextRenewMs)
                    _nextRenewMs = _clockMs + (CastRenew() ? kRenewEveryMs : kRetryMs * 2);
                break;
            case NPC_SM_COMPANY_ABBOT:
                if (!_frenzied && me->GetHealthPct() <= kFrenzyBelowPct)
                {
                    _frenzied = true;
                    me->CastSpell(me, SPELL_FRENZY, true);
                    LogLs("abbot-frenzy", Acore::StringFormat("abbot={}", me->GetGUID().GetCounter()));
                }
                if (_clockMs >= _nextRenewMs)
                    _nextRenewMs = _clockMs + (CastRenew() ? kRenewEveryMs : kRetryMs * 2);
                break;
            default:
                break;
        }
    }

    // Stock Monk row 2: Kick a casting victim (7 s cooldown).
    void UpdateKick()
    {
        if (_clockMs < _kickReadyMs)
            return;
        Unit* victim = me->GetVictim();
        if (!victim || !victim->HasUnitState(UNIT_STATE_CASTING) || !me->IsWithinMeleeRange(victim))
            return;
        if (me->CastSpell(victim, SPELL_KICK, false) == SPELL_CAST_OK)
            _kickReadyMs = _clockMs + kKickCooldownMs;
    }

    Unit* MechanicOwnerOrMe()
    {
        LastStandHost* host = HostOf(me);
        Unit* owner = host ? host->MechanicOwner() : nullptr;
        return owner ? owner : me;
    }

    // LS1b: 6 yd of Consecration under the Monk for 8 s.
    void LayConsecration()
    {
        Unit* owner = MechanicOwnerOrMe();
        Position const spot = me->GetPosition();
        float const pct = kConsecrationPct(_heroic);
        MechanicRef zone = Mechanic::Circle(owner, BossMechanics::Anchor(spot), kConsecrationRadiusYd,
            Ms(kConsecrationTickMs));
        zone.Persistent(Ms(kConsecrationMs), Ms(kConsecrationTickMs)).Damage(pct).TankDamage(pct)
            .Spell(SPELL_LS_CONSECRATION_HIT).NoFillTimer().Within(StandFloorBounds()).Tag(TAG_LS_CONSECRATION);
        owner->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), SPELL_LS_CONSECRATION_GROUND,
            true);
        LogLs("consecration", Acore::StringFormat("monk={} at=({:.1f}, {:.1f}) pct={:.0f}/s owner={}",
            me->GetGUID().GetCounter(), spot.GetPositionX(), spot.GetPositionY(), pct,
            owner == me ? "self" : "conductor"));
    }

    // A random player of the stand within 40 yd and in sight (the tank too).
    Player* RandomTarget()
    {
        DungeonKit::PickRule rule;
        rule.nonTank = false;
        rule.maxRange = 40.f;
        rule.requireLos = true;
        return DungeonKit::PickPlayer(me, rule);
    }

    // LS1c: the 2.5 s Fireball at a random player (refflat 15% / 20%, the kit's script).
    bool CastFireball()
    {
        Player* target = RandomTarget();
        if (!target)
            return false;
        me->StopMoving();
        if (me->CastSpell(target, SPELL_LS_FIREBALL, false) != SPELL_CAST_OK)
            return false;
        Mechanic::NoteNextCastIn(me, SPELL_LS_FIREBALL, Ms(kFireballEveryMs));
        LogLs("fireball", Acore::StringFormat("wizard={} target={}", me->GetGUID().GetCounter(), target->GetName()));
        return true;
    }

    // LS2: the 2.5 s cast and its 5 yd circle at the target's spot; the circle lands when the cast ends (OnSpellCast),
    // a kick takes it away (OnSpellFailed). On the landing the fire stays 6 / 10 s.
    bool CastFlame()
    {
        Player* target = RandomTarget();
        if (!target)
            return false;
        me->StopMoving();
        if (me->CastSpell(target, SPELL_LS_PURIFYING_FLAME_CAST, false) != SPELL_CAST_OK)
            return false;
        Unit* owner = MechanicOwnerOrMe();
        Position const spot = target->GetPosition();
        float const pct = kFlamePct(_heroic);
        MechanicRef circle = Mechanic::Circle(owner, BossMechanics::Anchor(spot), kFlameRadiusYd, Ms(kFlameCastMs));
        circle.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_LS_PURIFYING_FLAME_HIT).Within(StandFloorBounds())
            .Tag(TAG_LS_FLAME);
        Map* map = me->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        bool const heroic = _heroic;
        circle.OnResolve([map, ownerGuid, spot, heroic](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* source = map->GetCreature(ownerGuid);
            if (!source || !source->IsAlive())
                return;
            float const tick = kFlameFirePct(heroic);
            MechanicRef fire = Mechanic::Circle(source, BossMechanics::Anchor(spot), kFlameRadiusYd,
                Ms(kFlameFireTickMs));
            fire.Persistent(Ms(kFlameFireMs(heroic)), Ms(kFlameFireTickMs)).Damage(tick).TankDamage(tick)
                .Spell(SPELL_LS_PURIFYING_FLAME_FIRE).Rider(DungeonKit::SPELL_KIT_STANDING_IN_IT).NoFillTimer()
                .Within(StandFloorBounds()).Tag(TAG_LS_FLAME_FIRE);
            source->CastSpell(spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(),
                heroic ? SPELL_LS_PURIFYING_FLAME_POOL_H : SPELL_LS_PURIFYING_FLAME_POOL, true);
            DungeonKit::LogMechanic(kLogDungeon, kBoss, "flame-fire", Acore::StringFormat(
                "at=({:.1f}, {:.1f}) hits={} fire={}ms", spot.GetPositionX(), spot.GetPositionY(),
                result.hits.size(), kFlameFireMs(heroic)));
        });
        _flame = circle.Handle();
        _flameOwner = ownerGuid;
        Mechanic::NoteNextCastIn(me, SPELL_LS_PURIFYING_FLAME_CAST, Ms(kFlameEveryMs));
        LogLs("flame", Acore::StringFormat("wizard={} target={} pct={:.0f}", me->GetGUID().GetCounter(),
            target->GetName(), pct));
        return true;
    }

    Unit* FlameOwner()
    {
        if (_flameOwner.IsEmpty())
            return nullptr;
        if (_flameOwner == me->GetGUID())
            return me;
        return ObjectAccessor::GetCreature(*me, _flameOwner);
    }

    void CancelFlame(char const* why)
    {
        if (!_flame)
            return;
        if (Unit* owner = FlameOwner())
            Mechanic::Cancel(owner, _flame);
        _flame = MechanicHandle();
        LogLs("flame-cancelled", Acore::StringFormat("wizard={} why={}", me->GetGUID().GetCounter(), why));
    }

    // LS3 heroic: a Greater Heal that ran heals every living member of the company 50%.
    void HealCompany()
    {
        LastStandHost* host = HostOf(me);
        if (!host)
            return;
        uint32 healed = 0;
        for (Creature* unit : host->CompanyUnits(_index))
        {
            me->CastSpell(unit, SPELL_LS_GREATER_HEAL_PULSE, true);
            ++healed;
        }
        LogLs("greater-heal-missed", Acore::StringFormat("healer={} company={} healed={} pct={}",
            me->GetGUID().GetCounter(), _index, healed, kMissedHealPct));
    }

    // Stock Renew (8362) on the company's most hurt member missing 400 health without it.
    bool CastRenew()
    {
        Creature* pick = nullptr;
        LastStandHost* host = HostOf(me);
        if (!host)
            return false;
        for (Creature* unit : host->CompanyUnits(-1))
        {
            if (unit->GetMaxHealth() - unit->GetHealth() < kRenewMissingHealth || unit->HasAura(SPELL_RENEW)
                || !me->IsWithinDistInMap(unit, 40.f))
                continue;
            if (!pick || unit->GetHealthPct() < pick->GetHealthPct())
                pick = unit;
        }
        return pick && me->CastSpell(pick, SPELL_RENEW, false) == SPELL_CAST_OK;
    }

    // The Clergy's Chaplain: stock Power Word: Shield (6066) on a member of the company without it, the most hurt
    // first.
    bool CastShield()
    {
        Creature* pick = nullptr;
        LastStandHost* host = HostOf(me);
        if (!host)
            return false;
        for (Creature* unit : host->CompanyUnits(_index))
        {
            if (unit->HasAura(SPELL_POWER_WORD_SHIELD) || !me->IsWithinDistInMap(unit, 40.f))
                continue;
            if (!pick || unit->GetHealthPct() < pick->GetHealthPct())
                pick = unit;
        }
        return pick && me->CastSpell(pick, SPELL_POWER_WORD_SHIELD, false) == SPELL_CAST_OK;
    }

    // LS1a: every company unit within 15 yd (himself too) takes 30% / 40% less damage while he lives.
    void PulseDevotion()
    {
        LastStandHost* host = HostOf(me);
        if (!host)
            return;
        CastSpellExtraArgs args(TRIGGERED_FULL_MASK);
        args.AddSpellBP0(-kDevotionPct(_heroic));
        for (Creature* unit : host->CompanyUnits(-1))
            if (me->IsWithinDistInMap(unit, kDevotionRadiusYd))
                me->CastSpell(unit, SPELL_LS_DEVOTION_AURA, args);
    }

    int _index = -1;
    Company _kind = Company::ChapelGuard;
    Arm _arm = Arm::North;
    bool _heroic = false;
    bool _charges = false;
    bool _arrived = false;
    bool _charging = false;
    bool _frenzied = false;
    uint64 _clockMs = 0;
    uint64 _setupAt = 0;
    uint64 _arrivedAt = 0;
    uint64 _chargeAtMs = 0;
    uint64 _chargeGiveUpMs = 0;
    uint64 _nextHolyStrikeMs = 0;
    uint64 _nextConsecrationMs = 0;
    uint64 _nextFireballMs = 0;
    uint64 _nextFlameMs = 0;
    uint64 _nextFireShieldMs = 0;
    uint64 _nextDevotionMs = 0;
    uint64 _nextRenewMs = 0;
    uint64 _nextShieldMs = 0;
    uint64 _kickReadyMs = 0;
    Position _chargeEnd;
    MechanicHandle _flame;
    ObjectGuid _flameOwner;
};

namespace
{
    npc_sm_last_stand_company* CompanyAI(Creature* creature)
    {
        if (!creature || !creature->IsAlive() || !creature->IsAIEnabled)
            return nullptr;
        return dynamic_cast<npc_sm_last_stand_company*>(creature->AI());
    }

    // The finale's factory (MograineFight.h): D14 registers it from its AddSC_.
    SmLastStand::MograineRisenFactory& RisenFactory()
    {
        static SmLastStand::MograineRisenFactory factory;
        return factory;
    }
}

namespace SmLastStand
{
    void RegisterMograineRisen(MograineRisenFactory factory)
    {
        RisenFactory() = std::move(factory);
    }

    bool HasMograineRisen()
    {
        return static_cast<bool>(RisenFactory());
    }

    std::unique_ptr<MograineRisen> CreateMograineRisen(Creature* mograine)
    {
        return RisenFactory() ? RisenFactory()(mograine) : nullptr;
    }

    MograineFight* MograineFightOf(Creature* mograine)
    {
        if (!mograine || !mograine->IsAIEnabled)
            return nullptr;
        return dynamic_cast<MograineFight*>(mograine->AI());
    }
}

// ---------------------------------------------------------------------------------------------------------------------
// Scarlet Commander Mograine 3976. A ScriptedAI on the slot's registry encounter: the instance writes BOSS_LAST_STAND
// (the door, the crossing restart, DATA_LAST_STAND), never this script's BossAI.
// ---------------------------------------------------------------------------------------------------------------------
struct boss_mograine_rework : public ScriptedAI, public LastStandHost, public MograineFight
{
    explicit boss_mograine_rework(Creature* creature)
        : ScriptedAI(creature), instance(creature->GetInstanceScript()), _arena(StandFloor(), LeashOptions(kBoss)) { }

    // ----------------------------------------------------------------------------------------------------------------
    // Engine hooks
    // ----------------------------------------------------------------------------------------------------------------

    // Spawn, respawn and the end of every evade: back to what the instance says (a cold load with slot 5 DONE lies
    // before the altar; anything else stands on the altar steps).
    void Reset() override
    {
        if (_baseMaxHealth == 0)
            _baseMaxHealth = me->GetCreateHealth();
        CathedralStage const stage = instance ? static_cast<CathedralStage>(instance->GetData(DATA_CATHEDRAL_STAGE))
            : CathedralStage::BeforeStand;
        if (_state == MograineState::Risen)
            EndRising(false);
        if (StateForStage(stage) == MograineState::Fallen)
        {
            if (_state != MograineState::Falling)
                BecomeFallen("reset");
        }
        else
            BecomeAltar();
    }

    void JustEngagedWith(Unit* who) override
    {
        switch (_state)
        {
            case MograineState::Altar:
                // A pull before the door: the stand starts with it (the instance sends the start action back).
                if (instance)
                    instance->SetData(DATA_LAST_STAND, IN_PROGRESS);
                EnterFight(who, "pull");
                break;
            case MograineState::Stand:
                EnterFight(who, _descending ? "descent" : "early");
                break;
            case MograineState::Fight:
                break;
            case MograineState::Risen:
                if (_risen)
                    _risen->OnEngage(*this, who);
                break;
            case MograineState::Falling:
            case MograineState::Fallen:
                break;
        }
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        switch (_state)
        {
            case MograineState::Falling:
            case MograineState::Fallen:
                return;     // the stock fake death: evade disabled
            case MograineState::Risen:
                if (_risen && _risen->OnEvade(*this))
                    return;
                LogLs("risen-evade", Acore::StringFormat("reason={}", uint32(why)));
                BackToBody("evade");
                return;
            case MograineState::Stand:
                if (!PlayersOnTheStand(me->GetMap()).empty())
                    return;     // waiting on the altar is not a fight; the wipe watch ends the stand
                Wipe("evade-empty");
                return;
            case MograineState::Fight:
                Wipe(Acore::StringFormat("evade reason={}", uint32(why)).c_str());
                ScriptedAI::EnterEvadeMode(why);
                return;
            case MograineState::Altar:
                ScriptedAI::EnterEvadeMode(why);
                return;
        }
    }

    void JustDied(Unit* killer) override
    {
        if (_state == MograineState::Risen)
        {
            if (_risen)
                _risen->OnDied(*this, killer);
            EndRising(true);
            LogLs("death", Acore::StringFormat("risen killer={}", killer ? killer->GetName() : std::string("none")));
            return;
        }
        // Outside the finale he never dies (the floor): a GM kill. The stand's units and looks go with him.
        Cleanup();
        LogLs("death", Acore::StringFormat("state={} killer={} (outside the finale)", StateName(_state),
            killer ? killer->GetName() : std::string("none")));
    }

    void DamageTaken(Unit* attacker, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*mask*/) override
    {
        switch (_state)
        {
            case MograineState::Altar:
            case MograineState::Stand:
            case MograineState::Fight:
            {
                // The stock fake death (SmartAI row 9 "invincible at 1 HP"; the build spec's 1%).
                uint32 const allowed = ClampToFloor(me->GetHealth(), me->GetMaxHealth(), damage, kFallPct);
                if (allowed < damage && !_atFloorLogged)
                {
                    _atFloorLogged = true;
                    LogLs("floor", Acore::StringFormat("health={} companies-called={} alive={}", me->GetHealth(),
                        _called, AnyMemberAlive() ? 1 : 0));
                }
                damage = allowed;
                break;
            }
            case MograineState::Falling:
            case MograineState::Fallen:
                damage = 0;
                break;
            case MograineState::Risen:
                if (_down)
                    damage = 0;
                if (_risen)
                    _risen->OnDamageTaken(*this, attacker, damage);
                break;
        }
    }

    void KilledUnit(Unit* victim) override
    {
        if (!victim || !victim->IsPlayer())
            return;
        if (_state != MograineState::Fight && _state != MograineState::Risen)
            return;
        if (_clockMs < _killLineReadyMs)
            return;
        _killLineReadyMs = _clockMs + kKillLineCooldownMs;
        Talk(SAY_MOGRAINE_KILL, victim);
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case ACTION_SM_LAST_STAND_START:
                StartStand("door");
                return;
            case ACTION_SM_ASHBRINGER:
                ArmAshbringerCameo();
                return;
            case ACTION_SM_MOGRAINE_FALLEN:
                // His own fall already walks him there; a GM write (or another path) lays him down where he is.
                if (_state != MograineState::Falling && _state != MograineState::Fallen
                    && _state != MograineState::Risen)
                {
                    Cleanup();
                    BecomeFallen("action");
                }
                return;
            default:
                break;
        }
        if (_state == MograineState::Risen && _risen)
            _risen->OnAction(*this, action);
    }

    // The Ashbringer cameo, part 2 (stock SmartAI 3976 rows 25-27 and list 397602): the item's periodic effect hits
    // him once the instance armed the cameo; he kneels to its bearer and Highlord Mograine comes (his stock SmartAI).
    void SpellHit(Unit* caster, SpellInfo const* spell) override
    {
        if (!spell || spell->Id != kSpellAshbringerEffect || !_cameoArmed || _cameoPlayed)
            return;
        if (_state != MograineState::Altar)
            return;
        _cameoPlayed = true;
        me->setActive(true);
        me->SetFaction(kFactionFriendly);
        me->GetMotionMaster()->MoveIdle();
        if (caster)
            me->SetFacingToObject(caster);
        me->SetStandState(UNIT_STAND_STATE_KNEEL);
        Talk(kSayMograineAshbringerKneel, caster);
        Point4 const& p = kHighlordMograineSummon;
        Creature* highlord = me->SummonCreature(NPC_HIGHLORD_MOGRAINE, p.x, p.y, p.z, p.o, TEMPSUMMON_MANUAL_DESPAWN);
        LogLs("ashbringer-kneel", Acore::StringFormat("bearer={} highlord={}",
            caster ? caster->GetName() : std::string("none"), highlord ? 1 : 0));
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_BODY && _state == MograineState::Falling)
        {
            LieDown("arrived");
            return;
        }
        if (_state == MograineState::Risen && _risen)
            _risen->OnMovementInform(*this, type, id);
    }

    void JustReachedHome() override
    {
        if (_state == MograineState::Fallen && !_lying)
            LieDown("home");
    }

    void OnSpellCast(SpellInfo const* spell) override
    {
        if (_state == MograineState::Risen && _risen)
            _risen->OnSpellCast(*this, spell);
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (spell && StormCancelledBy(spell->Id))
            CancelStorm("broken");
        if (_state == MograineState::Risen && _risen)
            _risen->OnSpellFailed(*this, spell);
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        scheduler.Update(diff);

        switch (_state)
        {
            case MograineState::Altar:
            case MograineState::Fallen:
                return;
            case MograineState::Falling:
                if (_clockMs >= _fallWalkGiveUpMs)
                {
                    me->NearTeleportTo(kMograineBody.x, kMograineBody.y, kMograineBody.z,
                        me->GetHomePosition().GetOrientation());
                    LieDown("teleported");
                }
                return;
            case MograineState::Stand:
                UpdateCompanies(diff);
                UpdateWipeWatch(diff);
                return;
            case MograineState::Fight:
                UpdateCompanies(diff);
                UpdateFight(diff);
                return;
            case MograineState::Risen:
                UpdateRisen(diff);
                return;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LastStandHost (the company units)
    // ----------------------------------------------------------------------------------------------------------------

    bool StandRunning() const override
    {
        return _state == MograineState::Stand || _state == MograineState::Fight;
    }

    bool StandHeroic() const override { return _heroic; }

    Unit* MechanicOwner() override
    {
        if (_conductor.IsEmpty())
            return nullptr;
        Creature* conductor = ObjectAccessor::GetCreature(*me, _conductor);
        return conductor && conductor->IsAlive() && conductor->IsInWorld() ? conductor : nullptr;
    }

    std::vector<Creature*> CompanyUnits(int index) override
    {
        std::vector<Creature*> out;
        for (std::size_t i = 0; i < _companies.size(); ++i)
        {
            if (index >= 0 && static_cast<std::size_t>(index) != i)
                continue;
            for (ObjectGuid const& guid : _companies[i].units)
                if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
                    if (unit->IsAlive() && unit->IsInWorld())
                        out.push_back(unit);
        }
        return out;
    }

    Player* PickChargeTarget(int index, Creature* champion) override
    {
        if (index < 0 || static_cast<std::size_t>(index) >= _companies.size() || !champion)
            return nullptr;
        CompanyRecord& rec = _companies[static_cast<std::size_t>(index)];
        std::vector<Player*> players;
        std::vector<bool> inLos;
        for (Player* p : PlayersOnTheStand(me->GetMap()))
        {
            players.push_back(p);
            inLos.push_back(champion->IsWithinLOSInMap(p) && rec.chargeTargets.count(p->GetGUID()) == 0);
        }
        // Everyone in sight was taken already: any player in sight again.
        if (std::none_of(inLos.begin(), inLos.end(), [](bool b) { return b; }))
            for (std::size_t i = 0; i < players.size(); ++i)
                inLos[i] = champion->IsWithinLOSInMap(players[i]);
        std::vector<std::size_t> const picks = ChargeTargets(1, inLos,
            [](std::size_t n) { return static_cast<std::size_t>(urand(0, static_cast<uint32>(n) - 1)); });
        if (picks.empty())
            return nullptr;
        Player* pick = players[picks.front()];
        rec.chargeTargets.insert(pick->GetGUID());
        return pick;
    }

    void MemberArrived(int index, Creature* /*unit*/) override
    {
        if (index < 0 || static_cast<std::size_t>(index) >= _companies.size())
            return;
        CompanyRecord& rec = _companies[static_cast<std::size_t>(index)];
        if (rec.arrivedAt != 0)
            return;
        rec.arrivedAt = _clockMs;
        rec.nextHealAt = _clockMs + kGreaterHealFirstMs;
        LogLs("company-arrived", Acore::StringFormat("company={} {} after={}ms", index, CompanyName(rec.kind),
            _clockMs - rec.calledAt));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MograineFight (D14's finale)
    // ----------------------------------------------------------------------------------------------------------------

    Creature* Mograine() override { return me; }
    bool Heroic() const override { return _heroic; }
    MograineState State() const override { return _state; }
    MograineRisen* ActiveRisen() override { return _risen.get(); }

    uint64 RisenMs() const override
    {
        return _state == MograineState::Risen ? _clockMs - _risenAt : 0;
    }

    bool Rise(uint32 maxHealth, float healthPct, char const* why) override
    {
        if (_state != MograineState::Fallen || !me->IsAlive())
            return false;
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _state = MograineState::Risen;
        _risenAt = _clockMs;
        _down = false;
        _kneelUntil = 0;
        _holdKitUntil = 0;
        _holdControlUntil = 0;
        _lying = false;
        ClearFallenLook();
        if (maxHealth)
            me->SetMaxHealth(maxHealth);
        float const pct = std::clamp(healthPct, 1.f, 100.f);
        me->SetHealth(std::max<uint32>(1, static_cast<uint32>(static_cast<float>(me->GetMaxHealth()) * pct / 100.f)));
        me->SetReactState(REACT_AGGRESSIVE);
        me->CastSpell(me, SPELL_RETRIBUTION_AURA, true);
        _cadence = { { { kCrusaderStrikeFirstMs, kCrusaderStrikeEveryMs }, { kStormFirstMs, kStormEveryMs },
            { 0, 0 } } };
        for (std::size_t i = 0; i < kMograineKitCount; ++i)
            _nextKit[i] = _cadence[i].every ? _cadence[i].first : 0;
        bool const first = !_everRisen;
        _everRisen = true;
        _risen = CreateMograineRisen(me);
        if (!_risen)
            LogLs("risen-no-hooks", "no MograineRisen factory registered: the default risen kit only");
        if (Player* target = ArrivalTarget(me))
        {
            JoinStand(me, target);
            ScriptedAI::AttackStart(target);
        }
        LogLs("rise", Acore::StringFormat("why={} max={} pct={:.0f} first={} heroic={}", why, me->GetMaxHealth(), pct,
            first ? 1 : 0, _heroic ? 1 : 0));
        if (_risen)
            _risen->OnRise(*this, first);
        return true;
    }

    void Down(char const* why) override
    {
        if (_state != MograineState::Risen || _down)
            return;
        _down = true;
        _controlHeld = false;   // a lane's or a Verdict's hold ends with him down (no re-attack while he lies)
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->SetReactState(REACT_PASSIVE);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetImmuneToAll(true, true);
        me->SetStandState(UNIT_STAND_STATE_DEAD);
        LogLs("risen-down", why);
    }

    bool IsDown() const override { return _down; }

    void GetUp(float healthPct, char const* why) override
    {
        if (_state != MograineState::Risen || !_down)
            return;
        _down = false;
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetImmuneToAll(false, true);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        float const pct = std::clamp(healthPct, 1.f, 100.f);
        me->SetHealth(std::max<uint32>(1, static_cast<uint32>(static_cast<float>(me->GetMaxHealth()) * pct / 100.f)));
        me->SetReactState(REACT_AGGRESSIVE);
        ReattackVictim();
        LogLs("risen-up", Acore::StringFormat("why={} pct={:.0f}", why, pct));
    }

    void Kneel(uint32 ms, char const* why) override
    {
        if (_state != MograineState::Risen || _down)
            return;
        _kneelUntil = RisenMs() + ms;
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->SetStandState(UNIT_STAND_STATE_KNEEL);
        LogLs("risen-kneel", Acore::StringFormat("why={} ms={}", why, ms));
    }

    void BackToBody(char const* why) override
    {
        if (_state != MograineState::Risen)
            return;
        EndRising(false);
        me->CombatStop(true);
        me->GetThreatMgr().ClearAllThreat();
        WalkToBody(why);
    }

    void KillForGood(Unit* killer) override
    {
        if (!me->IsAlive())
            return;
        // Down in her save, or still lying Fallen (the pair death before the rising): his corpse must be lootable
        // (the Heart of Zeal, the cloth).
        _down = false;
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetImmuneToAll(false, true);
        if (killer && killer->IsPlayer())
            me->SetLootRecipient(killer);
        LogLs("risen-killed", Acore::StringFormat("killer={}", killer ? killer->GetName() : std::string("none")));
        Unit::Kill(killer ? killer : me, me);
    }

    void SetCadence(MograineKit kit, uint32 firstMs, uint32 everyMs) override
    {
        std::size_t const i = static_cast<std::size_t>(kit);
        if (i >= kMograineKitCount)
            return;
        _cadence[i] = { firstMs, everyMs };
        _nextKit[i] = everyMs ? RisenMs() + firstMs : 0;
    }

    void HoldKit(uint64 untilMs) override { _holdKitUntil = untilMs; }

    void HoldControl(uint64 untilMs) override
    {
        _holdControlUntil = untilMs;
        _controlHeld = untilMs > RisenMs();
    }

    bool Casting() const override { return me->HasUnitState(UNIT_STATE_CASTING); }

    void StopCasting(char const* why) override
    {
        if (!me->HasUnitState(UNIT_STATE_CASTING))
            return;
        me->InterruptNonMeleeSpells(false);
        LogLs("stop-casting", why);
    }

    bool FireNow(MograineKit kit, Player* forced) override
    {
        if (me->HasUnitState(UNIT_STATE_CASTING) || _down)
            return false;
        switch (kit)
        {
            case MograineKit::CrusaderStrike: return DoCrusaderStrike();
            case MograineKit::DivineStorm:    return DoStorm();
            case MograineKit::HammerOfJustice: return DoHammer(forced);
        }
        return false;
    }

    void Track(MechanicHandle handle) override
    {
        if (!handle)
            return;
        _live.push_back(handle);
        if (_live.size() > 96)
            _live.erase(_live.begin(), _live.begin() + 48);
    }

    void Say(uint8 group, WorldObject const* target) override { Talk(group, target); }

    void Log(char const* mechanic, std::string const& detail) override { LogLs(mechanic, detail); }

private:
    struct CompanyRecord
    {
        Company kind = Company::ChapelGuard;
        uint64 calledAt = 0;
        uint64 arrivedAt = 0;       // 0: not yet
        uint64 nextHealAt = 0;
        uint32 healTurn = 0;
        std::vector<ObjectGuid> units;
        GuidSet chargeTargets;
    };

    struct Cadence
    {
        uint32 first = 0;
        uint32 every = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // States and looks
    // ----------------------------------------------------------------------------------------------------------------

    // The Ashbringer cameo, part 1 (HANDOFF section 10, STAGE-R-1-KIT m-1 default c; stock SmartAI 3976 row 0 and AT
    // 4089 rows 2-3, dropped by W2-SETUP's rev): the instance accepted the Ashbringer, so a refused one plays nothing.
    // Only while he waits on the altar (the instance refuses the event while a Cathedral slot fights; after his fall
    // he lies at the vigil and stays there). Once per AI, as the stock rows (no repeat).
    void ArmAshbringerCameo()
    {
        if (_state != MograineState::Altar || _cameoArmed)
        {
            LogLs("ashbringer-ignored", Acore::StringFormat("state={} armed={}", StateName(_state),
                _cameoArmed ? 1 : 0));
            return;
        }
        _cameoArmed = true;
        Talk(kSayMograineAshbringerYell);
        LogLs("ashbringer", "armed: line 6, waiting for the blade's effect");
    }

    // On the altar steps: passive (no proximity aggro, no assisting the companies), attackable; a pull starts the
    // fight (JustEngagedWith).
    void BecomeAltar()
    {
        _state = MograineState::Altar;
        _lying = false;
        ClearFallenLook();
        if (_baseMaxHealth && me->GetMaxHealth() != _baseMaxHealth)
            me->SetMaxHealth(_baseMaxHealth);
        me->SetReactState(REACT_PASSIVE);
        _atFloorLogged = false;
    }

    // Lies before the altar (the vigil): not selectable, immune, passive; walks there first when away from it.
    void BecomeFallen(char const* why)
    {
        _state = MograineState::Fallen;
        ApplyFallenFlags();
        if (_baseMaxHealth && me->GetMaxHealth() != _baseMaxHealth)
            me->SetMaxHealth(_baseMaxHealth);
        me->SetHomePosition(kMograineBody.x, kMograineBody.y, kMograineBody.z, me->GetHomePosition().GetOrientation());
        if (me->GetExactDist2d(kMograineBody.x, kMograineBody.y) <= 3.f)
            LieDown(why);
        else
            WalkToBody(why);
    }

    void ApplyFallenFlags()
    {
        me->SetReactState(REACT_PASSIVE);
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetImmuneToAll(true);
        me->RemoveAurasDueToSpell(SPELL_RETRIBUTION_AURA);
    }

    void ClearFallenLook()
    {
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetImmuneToAll(false);
        me->SetStandState(UNIT_STAND_STATE_STAND);
    }

    void WalkToBody(char const* why)
    {
        _state = MograineState::Falling;
        _lying = false;
        ApplyFallenFlags();
        me->SetHomePosition(kMograineBody.x, kMograineBody.y, kMograineBody.z, me->GetHomePosition().GetOrientation());
        _fallWalkGiveUpMs = _clockMs + kFallWalkGiveUpMs;
        me->SetWalk(true);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_BODY, kMograineBody.x, kMograineBody.y, kMograineBody.z);
        LogLs("to-body", why);
    }

    void LieDown(char const* why)
    {
        _state = MograineState::Fallen;
        _lying = true;
        me->SetWalk(false);
        me->StopMoving();
        ApplyFallenFlags();
        if (_baseMaxHealth && me->GetMaxHealth() != _baseMaxHealth)
            me->SetMaxHealth(_baseMaxHealth);
        me->SetStandState(UNIT_STAND_STATE_DEAD);
        LogLs("fallen", Acore::StringFormat("why={} at=({:.1f}, {:.1f})", why, me->GetPositionX(),
            me->GetPositionY()));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LS0 the start, the wipe, the cleanup
    // ----------------------------------------------------------------------------------------------------------------

    void StartStand(char const* how)
    {
        if (_state != MograineState::Altar)
        {
            LogLs("start-ignored", Acore::StringFormat("how={} state={}", how, StateName(_state)));
            return;
        }
        Cleanup();
        if (!_heroicForced)
            _heroic = IsHeroicMap(me);
        _heroicForced = false;
        _state = MograineState::Stand;
        _standAt = _clockMs;
        _pullLogged = false;
        SummonConductor();
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_LAST_STAND;
        Mechanic::BeginEncounter(me, options);
        Describe();
        Talk(SAY_MOGRAINE_DOOR);
        scheduler.Schedule(Ms(kFirstCallMs), GROUP_STAND, [this](TaskContext /*ctx*/)
        {
            if (StandRunning() && _called == 0)
                CallCompany(Company::ChapelGuard, "door");
        });
        LogLs("start", Acore::StringFormat("how={} heroic={} conductor={}", how, _heroic ? 1 : 0,
            _conductor.IsEmpty() ? 0 : 1));
    }

    // The stand failed: the companies go, he stands on the altar again, slot 5 NOT_STARTED (the door stays open; the
    // instance's crossing restart re-arms).
    void Wipe(char const* why)
    {
        LogLs("wipe", Acore::StringFormat("why={} called={} reserve={}", why, _called, _reserveCalled ? 1 : 0));
        Cleanup();
        Mechanic::EndEncounter(me);
        BecomeAltar();
        if (instance)
            instance->SetData(DATA_LAST_STAND, FAIL);
    }

    // Nothing pending, no company, no conductor, no look, no hold: Reset, the wipe, the fall, a GM's death.
    void Cleanup()
    {
        scheduler.CancelAll();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _storm = MechanicHandle();
        for (CompanyRecord const& rec : _companies)
            for (ObjectGuid const& guid : rec.units)
                if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
                    unit->DespawnOrUnsummon();
        _companies.clear();
        _called = 0;
        _reserveCalled = false;
        _emptyMs = 0;
        _wipeCheckMs = 0;
        _companyTickMs = 0;
        _atFloorLogged = false;
        _descentNoneLogged = false;
        DespawnConductor();
        _arena.Reset();
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_LS_HAMMER_STUN);
    }

    void SummonConductor()
    {
        DespawnConductor();
        Creature* conductor = me->SummonCreature(NPC_SM_STALKER_WAVE2, kCrossingCenter.x, kCrossingCenter.y,
            kCrossingCenter.z, 0.f, TEMPSUMMON_MANUAL_DESPAWN);
        if (!conductor)
        {
            LogLs("conductor-missing", Acore::StringFormat("no template {}: each company unit owns its mechanics",
                uint32(NPC_SM_STALKER_WAVE2)));
            return;
        }
        // His level picks the reference row (normal: no pin for map 189); never in combat, never a target.
        conductor->SetLevel(me->GetLevel());
        conductor->SetIsCombatDisallowed(true);
        conductor->SetReactState(REACT_PASSIVE);
        conductor->SetUnitFlag(UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE);
        _conductor = conductor->GetGUID();
    }

    void DespawnConductor()
    {
        if (_conductor.IsEmpty())
            return;
        if (Creature* conductor = ObjectAccessor::GetCreature(*me, _conductor))
        {
            conductor->RemoveAllDynObjects();
            conductor->DespawnOrUnsummon();
        }
        _conductor.Clear();
    }

    // Interrupt list: Greater Heal (heroic expected), Purifying Flame, Fireball. Kill order: the healers, the Captain,
    // the Wizards, the Monks, the Champions, then him (0); the tank gathers the melee (the Monks first). Dispel and
    // purge lists: none (CATH "Boss data").
    void Describe()
    {
        BossMechanics::Descriptor d;
        uint32 const heal = _heroic ? SPELL_LS_GREATER_HEAL_H : SPELL_LS_GREATER_HEAL;
        uint8 const healKick = kGreaterHealKickPriority(_heroic);
        d.interrupts.emplace_back(NPC_SM_COMPANY_CHAPLAIN, heal, healKick, Ms(kGreaterHealEveryMs));
        d.interrupts.emplace_back(NPC_SM_COMPANY_ABBOT, heal, healKick, Ms(kGreaterHealEveryMs));
        d.interrupts.emplace_back(NPC_SM_COMPANY_WIZARD, SPELL_LS_PURIFYING_FLAME_CAST, kFlameKickPriority,
            Ms(kFlameEveryMs));
        d.interrupts.emplace_back(NPC_SM_COMPANY_WIZARD, SPELL_LS_FIREBALL, kFireballKickPriority,
            Ms(kFireballEveryMs));
        for (uint32 entry = NPC_SM_CHAPEL_GUARD_CHAMPION; entry <= NPC_SM_COMPANY_ABBOT; ++entry)
        {
            BossMechanics::TargetEntry target(entry, KillPriority(entry), BossMechanics::Who::Dps);
            if (entry == NPC_SM_CHAPEL_GUARD_CHAMPION || entry == NPC_SM_COMPANY_MONK)
                target.AoeOk();
            d.targets.push_back(target);
        }
        d.targets.push_back(BossMechanics::TargetEntry(NPC_SM_COMPANY_MONK, kTankMonkPriority,
            BossMechanics::Who::Tank));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_SM_CHAPEL_GUARD_CHAMPION, kTankMeleePriority,
            BossMechanics::Who::Tank));
        d.targets.push_back(BossMechanics::TargetEntry(NPC_SM_CAPTAIN_OF_THE_GUARD, kTankMeleePriority,
            BossMechanics::Who::Tank));
        Mechanic::Describe(me, std::move(d));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // LS1 the companies
    // ----------------------------------------------------------------------------------------------------------------

    void CallCompany(Company kind, char const* why)
    {
        int const index = static_cast<int>(_companies.size());
        CompanyRecord rec;
        rec.kind = kind;
        rec.calledAt = _clockMs;
        Talk(CallLine(kind));
        std::array<uint32, 2> perArm{ { 0, 0 } };
        for (Member const& m : Members(kind, _heroic))
        {
            std::size_t const arm = static_cast<std::size_t>(m.arm);
            Point4 const spot = ColumnSpot(m.arm, perArm[arm]++);
            Creature* unit = me->SummonCreature(m.entry, spot.x, spot.y, spot.z, spot.o,
                TEMPSUMMON_CORPSE_TIMED_DESPAWN, kCorpseDespawnMs);
            if (!unit)
                continue;
            rec.units.push_back(unit->GetGUID());
            Mechanic::TrackUnit(me, unit);
            if (npc_sm_last_stand_company* ai = CompanyAI(unit))
                ai->Setup(index, kind, m.arm, _heroic, ChargesOnArrival(kind, m.entry, _heroic));
        }
        uint32 const count = static_cast<uint32>(rec.units.size());
        _companies.push_back(std::move(rec));
        if (kind == Company::LastReserve)
            _reserveCalled = true;
        else
            ++_called;
        LogLs("call", Acore::StringFormat("company={} {} why={} units={} heroic={} called={}", index,
            CompanyName(kind), why, count, _heroic ? 1 : 0, _called));
    }

    bool CompanyFallen(CompanyRecord const& rec)
    {
        for (ObjectGuid const& guid : rec.units)
            if (Creature* unit = ObjectAccessor::GetCreature(*me, guid))
                if (unit->IsAlive())
                    return false;
        return true;
    }

    // The latest of the three stand companies (the Last Reserve is not one of them).
    CompanyRecord* CurrentStandCompany()
    {
        for (auto it = _companies.rbegin(); it != _companies.rend(); ++it)
            if (it->kind != Company::LastReserve)
                return &*it;
        return nullptr;
    }

    bool StandCompaniesFallen()
    {
        for (CompanyRecord const& rec : _companies)
            if (rec.kind != Company::LastReserve && !CompanyFallen(rec))
                return false;
        return true;
    }

    bool AnyMemberAlive()
    {
        for (CompanyRecord const& rec : _companies)
            if (!CompanyFallen(rec))
                return true;
        return false;
    }

    void UpdateCompanies(uint32 diff)
    {
        _companyTickMs += diff;
        if (_companyTickMs < kCompanyTickMs)
            return;
        _companyTickMs = 0;

        // LS1: the next call.
        if (CompanyRecord* current = CurrentStandCompany())
        {
            bool const fallen = CompanyFallen(*current);
            if (NextCallDue(_called, fallen, current->arrivedAt, _clockMs, kCallEveryMs(_heroic)))
                CallCompany(static_cast<Company>(_called), fallen ? "fallen" : "timer");
        }

        // LS3: one Greater Heal per company every 10 s.
        for (std::size_t i = 0; i < _companies.size(); ++i)
        {
            CompanyRecord& rec = _companies[i];
            if (rec.kind == Company::PyreBrethren || rec.arrivedAt == 0 || _clockMs < rec.nextHealAt
                || CompanyFallen(rec))
                continue;
            rec.nextHealAt = _clockMs + (OrderGreaterHeal(static_cast<int>(i), rec) ? kGreaterHealEveryMs
                : kRetryMs * 2);
        }

        // The third company fell: he comes down.
        if (_state == MograineState::Stand && DescentDue(_called, StandCompaniesFallen(), me->IsEngaged()))
            Descend();
    }

    bool OrderGreaterHeal(int index, CompanyRecord& rec)
    {
        std::vector<Creature*> const units = CompanyUnits(index);
        std::vector<Creature*> healerUnits;
        std::vector<HealerCandidate> healers;
        std::vector<HealCandidate> hurt;
        for (Creature* unit : units)
        {
            hurt.push_back({ unit->GetHealthPct(), true });
            if (unit->GetEntry() != NPC_SM_COMPANY_CHAPLAIN && unit->GetEntry() != NPC_SM_COMPANY_ABBOT)
                continue;
            npc_sm_last_stand_company* ai = CompanyAI(unit);
            healerUnits.push_back(unit);
            healers.push_back({ unit->GetEntry(), ai && ai->FreeToCast() });
        }
        int const h = PickHealer(rec.kind, healers, rec.healTurn);
        int const t = MostHurt(hurt);
        if (h < 0 || t < 0)
            return false;
        Creature* healer = healerUnits[static_cast<std::size_t>(h)];
        Creature* target = units[static_cast<std::size_t>(t)];
        npc_sm_last_stand_company* ai = CompanyAI(healer);
        if (!ai || !ai->CastGreaterHeal(target))
            return false;
        ++rec.healTurn;
        uint32 const spell = _heroic ? SPELL_LS_GREATER_HEAL_H : SPELL_LS_GREATER_HEAL;
        Mechanic::NoteNextCastIn(healer, spell, Ms(kGreaterHealEveryMs));
        LogLs("greater-heal", Acore::StringFormat("company={} healer={} {} target={} {:.0f}% heroic={}", index,
            healer->GetGUID().GetCounter(), MemberName(healer->GetEntry()), MemberName(target->GetEntry()),
            target->GetHealthPct(), _heroic ? 1 : 0));
        return true;
    }

    // The third company fell: line 0 (on the pull), down the steps to the group at the crossing.
    void Descend()
    {
        Player* target = ArrivalTarget(me);
        if (!target)
        {
            if (!_descentNoneLogged)
                LogLs("descent-none", "nobody on the stand (the wipe watch ends it)");
            _descentNoneLogged = true;
            return;
        }
        LogLs("descent", Acore::StringFormat("target={}", target->GetName()));
        _descending = true;
        me->SetReactState(REACT_AGGRESSIVE);
        JoinStand(me, target);
        ScriptedAI::AttackStart(target);
        if (_state != MograineState::Fight)     // the threat above engaged him: JustEngagedWith ran EnterFight
            EnterFight(target, "descent");
        _descending = false;
    }

    // While he waits on the altar: nobody alive on the stand's floor for 5 s ends it.
    void UpdateWipeWatch(uint32 diff)
    {
        _wipeCheckMs += diff;
        if (_wipeCheckMs < 1000)
            return;
        uint32 const step = _wipeCheckMs;
        _wipeCheckMs = 0;
        if (PlayersOnTheStand(me->GetMap()).empty())
            _emptyMs += step;
        else
            _emptyMs = 0;
        if (WipeDue(_emptyMs))
            Wipe("nobody on the stand");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight (after the descent or an early pull)
    // ----------------------------------------------------------------------------------------------------------------

    void EnterFight(Unit* who, char const* why)
    {
        if (_state == MograineState::Fight)
            return;
        if (_state != MograineState::Stand)
        {
            // Pulled on the altar with the stand refused (wave 2 unbound, the Ashbringer): a plain fight, no company
            // to wait for at his fall.
            _heroic = _heroicForced ? _heroic : IsHeroicMap(me);
            _called = kStandCompanies;
            _reserveCalled = true;
            BossMechanics::EncounterOptions options;
            options.bossStateId = BOSS_LAST_STAND;
            Mechanic::BeginEncounter(me, options);
            Describe();
        }
        _state = MograineState::Fight;
        _fightAt = _clockMs;
        me->SetReactState(REACT_AGGRESSIVE);
        if (!_pullLogged)
        {
            _pullLogged = true;
            OnBossPull(me, kBoss);
        }
        _arena.Engage(me);
        Talk(SAY_MOGRAINE_AGGRO);
        me->CastSpell(me, SPELL_RETRIBUTION_AURA, true);
        _nextCrusaderMs = _clockMs + kCrusaderStrikeFirstMs;
        _nextHammerMs = _clockMs + kHammerFirstMs;
        _nextStormMs = _clockMs + kStormFirstMs;
        if (Player* target = who ? who->ToPlayer() : nullptr)
            JoinStand(me, target);
        LogLs("engage", Acore::StringFormat("why={} called={} heroic={} health={}", why, _called, _heroic ? 1 : 0,
            me->GetMaxHealth()));
    }

    void UpdateFight(uint32 diff)
    {
        if (!UpdateVictim())
            return;
        if (!_arena.Update(me, diff))
            return;     // off the stand's floor, or nobody on it for 10 s: evading (the wipe)

        if (ReserveDue(_heroic, _reserveCalled, me->GetHealthPct()))
            CallCompany(Company::LastReserve, "50%");

        bool const atFloor = me->GetHealth() <= FloorHealth(me->GetMaxHealth(), kFallPct);
        if (FallAllowed(atFloor, _called, AnyMemberAlive(), _heroic && !_reserveCalled))
        {
            Fall();
            return;
        }

        if (!me->HasUnitState(UNIT_STATE_CASTING))
        {
            if (_clockMs >= _nextStormMs)
                _nextStormMs = _clockMs + (DoStorm() ? kStormEveryMs : kRetryMs);
            else if (_clockMs >= _nextHammerMs)
                _nextHammerMs = _clockMs + (DoHammer(nullptr) ? kHammerEveryMs : kRetryMs);
            else if (_clockMs >= _nextCrusaderMs)
                _nextCrusaderMs = _clockMs + (DoCrusaderStrike() ? kCrusaderStrikeEveryMs : kRetryMs);
        }
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // Stock Crusader Strike on his victim.
    bool DoCrusaderStrike()
    {
        Unit* victim = me->GetVictim();
        if (!victim || !me->IsWithinMeleeRange(victim))
            return false;
        return me->CastSpell(victim, SPELL_CRUSADER_STRIKE, false) == SPELL_CAST_OK;
    }

    // LS4: a 5 yd circle on 1 / 2 random players (the tank too), 2 s; the thrown hammer lands as it resolves. Everyone
    // else caught: the hit, Weakened and the stun (the registry Spread); the marked player: the hit and the stun.
    bool DoHammer(Player* forced)
    {
        std::vector<Player*> targets;
        if (forced)
            targets.push_back(forced);
        else
        {
            DungeonKit::PickRule rule;
            rule.nonTank = false;
            rule.maxRange = 60.f;
            targets = DungeonKit::PickPlayers(me, rule, kHammerTargets(_heroic));
        }
        if (targets.empty())
            return false;
        float const pct = kHammerPct(_heroic);
        GuidSet carriers;
        for (Player* p : targets)
            carriers.insert(p->GetGUID());
        MechanicRef spread = Mechanic::Spread(me, kHammerRadiusYd, Ms(kHammerWarnMs));
        spread.Targets(carriers).Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_LS_HAMMER_HIT)
            .Rider(SPELL_LS_HAMMER_STUN).Within(StandFloorBounds()).Tag(TAG_LS_HAMMER);
        Track(spread.Handle());
        std::string names;
        for (Player* p : targets)
        {
            ObjectGuid const guid = p->GetGUID();
            scheduler.Schedule(Ms(HammerLaunchDelayMs(me->GetExactDist(p))), GROUP_KIT, [this, guid](TaskContext)
            {
                if (Player* t = ObjectAccessor::GetPlayer(*me, guid))
                    if (t->IsAlive())
                        me->CastSpell(t, SPELL_LS_HAMMER_THROW, true);
            });
            names += (names.empty() ? "" : ",") + p->GetName();
        }
        scheduler.Schedule(Ms(kHammerWarnMs), GROUP_KIT, [this, carriers](TaskContext)
        {
            for (ObjectGuid const& guid : carriers)
                if (Player* t = ObjectAccessor::GetPlayer(*me, guid))
                    if (t->IsAlive() && t->GetMap() == me->GetMap())
                    {
                        me->CastSpell(t, SPELL_LS_HAMMER_STRIKE, true);
                        me->CastSpell(t, SPELL_LS_HAMMER_STUN, true);
                    }
        });
        LogLs("hammer", Acore::StringFormat("targets=[{}] pct={:.0f} stun={}ms", names, pct, kHammerStunMs));
        return true;
    }

    // LS5: the 2 s wind-up, then the whirl round him: others the registry's circle (TankExempt), the tank his own hit.
    bool DoStorm()
    {
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return false;
        me->StopMoving();
        if (me->CastSpell(me, SPELL_LS_DIVINE_STORM_CAST, false) != SPELL_CAST_OK)
            return false;
        float const radius = kStormRadiusYd(_heroic);
        float const pct = kStormPct(_heroic);
        MechanicRef storm = Mechanic::Circle(me, BossMechanics::Anchor(me), radius, Ms(kStormCastMs));
        storm.TankExempt().Damage(pct).Weakened().Spell(SPELL_LS_DIVINE_STORM_HIT).Within(StandFloorBounds())
            .Tag(TAG_LS_DIVINE_STORM);
        MechanicHandle const handle = storm.Handle();
        Track(handle);
        _storm = handle;
        scheduler.Schedule(Ms(kStormCastMs), GROUP_KIT, [this, radius, handle](TaskContext)
        {
            if (!(_storm == handle))
                return;     // the wind-up broke: CancelStorm took the circle, no tank hit either
            _storm = MechanicHandle();
            Unit* tank = me->GetVictim();
            if (!tank || !tank->IsAlive())
                return;
            if (me->GetExactDist2d(tank) > radius + tank->GetCombatReach())
                return;
            me->CastSpell(tank, SPELL_LS_DIVINE_STORM_TANK, true);
            LogLs("storm-tank", Acore::StringFormat("hit {} pct={:.0f}", tank->GetName(), kStormTankPct(_heroic)));
        });
        LogLs("storm", Acore::StringFormat("radius={:.0f} pct={:.0f} tank={:.0f}", radius, pct,
            kStormTankPct(_heroic)));
        return true;
    }

    // LS5: a wind-up that ended early (OnSpellFailed) takes its circle with it; the tank hit sees the handle gone.
    void CancelStorm(char const* why)
    {
        if (!_storm)
            return;
        Mechanic::Cancel(me, _storm);
        _storm = MechanicHandle();
        LogLs("storm-cancelled", why);
    }

    // At 1% with nothing left to call or alive: the stock fake death (the dead stand state, evade off), walked to his
    // body spot before the altar; the Last Stand DONE (credit, door, the vigil) and the chest.
    void Fall()
    {
        LogLs("fall", Acore::StringFormat("health={} called={} reserve={}", me->GetHealth(), _called,
            _reserveCalled ? 1 : 0));
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        Cleanup();
        WalkToBody("fall");
        me->CombatStop(true);
        me->GetThreatMgr().ClearAllThreat();
        SummonChest();
        if (instance)
            instance->SetData(DATA_LAST_STAND, DONE);   // the instance credits 212301; never sent from here
    }

    // Section 7 #20 A: the chest at the altar steps, the entry of this difficulty (301330 / heroic 301331), summoned by
    // the map (it outlives his body and the finale) for a day or until looted. No spawn row: the heroic rollout widens
    // every spawn of the map to both difficulties, so two difficulty entries cannot be two spawns. Not restored after
    // an instance reload (the BRD Chest of The Seven precedent: a reload loses an unlooted chest).
    void SummonChest()
    {
        uint32 const entry = IsHeroicMap(me) ? GO_SM_LAST_STAND_CHEST_H : GO_SM_LAST_STAND_CHEST;
        if (me->FindNearestGameObject(entry, 80.f, true))
        {
            LogLs("chest-standing", Acore::StringFormat("entry={}", entry));
            return;
        }
        float const half = kChestSpot.o / 2.f;
        GameObject* chest = me->GetMap()->SummonGameObject(entry, kChestSpot.x, kChestSpot.y, kChestSpot.z,
            kChestSpot.o, 0.f, 0.f, std::sin(half), std::cos(half), DAY);
        if (!chest)
        {
            LogLs("chest-missing", Acore::StringFormat("entry={} could not be summoned (no template?)", entry));
            return;
        }
        LogLs("chest", Acore::StringFormat("entry={} at=({:.1f}, {:.1f}, {:.1f})", entry, kChestSpot.x, kChestSpot.y,
            kChestSpot.z));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Risen state (D14's finale)
    // ----------------------------------------------------------------------------------------------------------------

    void UpdateRisen(uint32 diff)
    {
        uint64 const now = RisenMs();
        if (_controlHeld)
        {
            if (now < _holdControlUntil)
            {
                if (_risen)
                    _risen->OnUpdate(*this, diff);
                return;
            }
            _controlHeld = false;
            ReattackVictim();
        }
        if (_down)
        {
            if (_risen)
                _risen->OnUpdate(*this, diff);
            return;
        }
        if (_kneelUntil != 0)
        {
            if (now < _kneelUntil)
            {
                if (_risen)
                    _risen->OnUpdate(*this, diff);
                return;
            }
            _kneelUntil = 0;
            me->SetStandState(UNIT_STAND_STATE_STAND);
            ReattackVictim();
        }
        if (!UpdateVictim())
        {
            if (_state == MograineState::Risen && _risen)
                _risen->OnUpdate(*this, diff);
            return;
        }
        if (now >= _holdKitUntil && !me->HasUnitState(UNIT_STATE_CASTING))
        {
            for (std::size_t i = 0; i < kMograineKitCount; ++i)
            {
                if (_cadence[i].every == 0 || now < _nextKit[i])
                    continue;
                bool const fired = FireNow(static_cast<MograineKit>(i), nullptr);
                _nextKit[i] = now + (fired ? _cadence[i].every : kRetryMs);
                if (fired)
                    break;
            }
        }
        if (now >= _holdKitUntil && !me->HasUnitState(UNIT_STATE_CASTING))
            DoMeleeAttackIfReady();
        if (_risen)
            _risen->OnUpdate(*this, diff);
    }

    void ReattackVictim()
    {
        if (_down)
            return;     // down in her save: GetUp re-attacks
        Unit* victim = me->GetVictim();
        if (!victim)
            victim = me->SelectVictim();
        if (!victim)
            return;
        me->GetMotionMaster()->Clear();
        ScriptedAI::AttackStart(victim);
    }

    // The rising ends: OnEnd, his kit and his handles gone, his template health back.
    void EndRising(bool died)
    {
        if (_risen)
            _risen->OnEnd(*this, died);
        _risen.reset();
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        _storm = MechanicHandle();
        scheduler.CancelGroup(GROUP_KIT);
        _down = false;
        _kneelUntil = 0;
        _controlHeld = false;
        if (!died && _baseMaxHealth)
            me->SetMaxHealth(_baseMaxHealth);
    }

public:
    // ----------------------------------------------------------------------------------------------------------------
    // `.dbtest sm laststand` entry points
    // ----------------------------------------------------------------------------------------------------------------

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestKind kind, Player* gm)
    {
        switch (kind)
        {
            case TestKind::Start:
                if (_state != MograineState::Altar)
                    return Acore::StringFormat("He is not on the altar ({}).", StateName(_state));
                if (instance)
                    instance->SetData(DATA_LAST_STAND, IN_PROGRESS);
                if (_state == MograineState::Altar)
                    StartStand("test");     // the instance refused (wave 2 unbound): a local stand
                return {};
            case TestKind::Call:
                if (!StandRunning())
                    return "The stand is not running: `start` first.";
                if (_called >= kStandCompanies)
                    return "All three companies were called.";
                CallCompany(static_cast<Company>(_called), "test");
                return {};
            case TestKind::Descend:
                if (_state != MograineState::Stand)
                    return "He is not waiting on the altar.";
                Descend();
                return {};
            case TestKind::Hammer:
                if (_state != MograineState::Fight && _state != MograineState::Risen)
                    return "He is not fighting.";
                return DoHammer(gm) ? std::string() : std::string("Nobody to throw at.");
            case TestKind::Storm:
                if (_state != MograineState::Fight && _state != MograineState::Risen)
                    return "He is not fighting.";
                return DoStorm() ? std::string() : std::string("Busy casting.");
            case TestKind::Reserve:
                if (!StandRunning())
                    return "The stand is not running.";
                if (_reserveCalled)
                    return "The Last Reserve was called already.";
                CallCompany(Company::LastReserve, "test");
                return {};
            case TestKind::Fall:
                if (!StandRunning())
                    return "The stand is not running.";
                Fall();
                return {};
            case TestKind::Chest:
                SummonChest();
                return {};
            case TestKind::Clear:
                if (StandRunning())
                    Wipe("test");
                else
                    Cleanup();
                return {};
        }
        return {};
    }

    void TestHeroic(bool heroic)
    {
        _heroic = heroic;
        _heroicForced = true;
        if (StandRunning())
            Describe();
    }

    std::string TestState()
    {
        std::string companies;
        for (std::size_t i = 0; i < _companies.size(); ++i)
        {
            CompanyRecord const& rec = _companies[i];
            companies += Acore::StringFormat(" {}:{}:alive={}:arrived={}", i, CompanyName(rec.kind),
                CompanyUnits(static_cast<int>(i)).size(), rec.arrivedAt ? 1 : 0);
        }
        return Acore::StringFormat("laststand state={} heroic={} called={} reserve={} conductor={} health={:.1f}% "
            "slot5={} stage={} companies=[{} ] risen-hooks={}", StateName(_state), _heroic ? 1 : 0, _called,
            _reserveCalled ? 1 : 0, MechanicOwner() ? 1 : 0, me->GetHealthPct(),
            instance ? instance->GetData(DATA_LAST_STAND) : 0, instance ? instance->GetData(DATA_CATHEDRAL_STAGE) : 0,
            companies, HasMograineRisen() ? 1 : 0);
    }

private:
    InstanceScript* const instance;     // the slot, the stage, the chest (ScriptedAI has none of its own)
    DungeonKit::ArenaGuard _arena;
    MograineState _state = MograineState::Altar;
    bool _heroic = false;
    bool _heroicForced = false;     // `.dbtest ... heroic`: kept through the next start
    bool _pullLogged = false;
    bool _reserveCalled = false;
    bool _atFloorLogged = false;
    bool _lying = false;
    bool _everRisen = false;
    bool _down = false;
    bool _controlHeld = false;
    bool _descending = false;
    bool _descentNoneLogged = false;
    bool _cameoArmed = false;       // the instance accepted the Ashbringer (ACTION_SM_ASHBRINGER)
    bool _cameoPlayed = false;      // he knelt and Highlord Mograine was summoned
    uint32 _called = 0;
    uint32 _baseMaxHealth = 0;
    uint32 _emptyMs = 0;
    uint32 _wipeCheckMs = 0;
    uint32 _companyTickMs = 0;
    uint64 _clockMs = 0;
    uint64 _standAt = 0;
    uint64 _fightAt = 0;
    uint64 _fallWalkGiveUpMs = 0;
    uint64 _killLineReadyMs = 0;
    uint64 _nextCrusaderMs = 0;
    uint64 _nextHammerMs = 0;
    uint64 _nextStormMs = 0;
    uint64 _risenAt = 0;
    uint64 _kneelUntil = 0;
    uint64 _holdKitUntil = 0;
    uint64 _holdControlUntil = 0;
    std::array<Cadence, kMograineKitCount> _cadence{};
    std::array<uint64, kMograineKitCount> _nextKit{};
    std::vector<CompanyRecord> _companies;
    std::vector<MechanicHandle> _live;
    MechanicHandle _storm;      // LS5: the storm on its wind-up (CancelStorm)
    ObjectGuid _conductor;
    std::unique_ptr<MograineRisen> _risen;
};

namespace
{
    boss_mograine_rework* MograineAI(ChatHandler* handler)
    {
        Creature* boss = SmTest::FindBoss(handler, NPC_MOGRAINE);
        auto* ai = boss && boss->IsAIEnabled ? dynamic_cast<boss_mograine_rework*>(boss->AI()) : nullptr;
        if (!ai && boss)
            handler->SendErrorMessage("{} does not run the reworked script.", boss->GetName());
        return ai;
    }

    bool Fire(ChatHandler* handler, TestKind kind, char const* ok)
    {
        boss_mograine_rework* ai = MograineAI(handler);
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

    // `.dbtest sm laststand info`
    bool HandleInfo(ChatHandler* handler)
    {
        return SmTest::ShowBossInfo(handler, NPC_MOGRAINE, BOSS_LAST_STAND);
    }

    // `.dbtest sm laststand state`: his state, the companies, the conductor, slot 5 and the Cathedral stage.
    bool HandleState(ChatHandler* handler)
    {
        boss_mograine_rework* ai = MograineAI(handler);
        if (!ai)
            return false;
        handler->SendSysMessage(ai->TestState());
        return true;
    }

    bool HandleStart(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Start, "The Last Stand starts (as if the Chapel Door opened).");
    }

    bool HandleCall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Call, "The next company is called now.");
    }

    bool HandleDescend(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Descend, "Mograine comes down now.");
    }

    bool HandleHammer(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Hammer, "Hammer of Justice: the circle is on you (2 s).");
    }

    bool HandleStorm(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Storm, "Divine Storm: the 2 s wind-up.");
    }

    bool HandleReserve(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Reserve, "The Last Reserve is called (both arms).");
    }

    bool HandleFall(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Fall, "Mograine falls: the Last Stand is DONE.");
    }

    bool HandleChest(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Chest, "The chest appears at the altar steps (one at a time).");
    }

    bool HandleClear(ChatHandler* handler)
    {
        return Fire(handler, TestKind::Clear, "Cleared (a running stand wipes).");
    }

    // `.dbtest sm laststand heroic [0|1]`
    bool HandleHeroic(ChatHandler* handler, Optional<uint32> on)
    {
        boss_mograine_rework* ai = MograineAI(handler);
        if (!ai)
            return false;
        ai->TestHeroic(!on || *on != 0);
        handler->SendSysMessage("The heroic form is set until the next start.");
        return true;
    }

    ChatCommandTable const& BossMograineTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,     SEC_GAMEMASTER, Console::No },
            { "state",      HandleState,    SEC_GAMEMASTER, Console::No },
            { "start",      HandleStart,    SEC_GAMEMASTER, Console::No },
            { "call",       HandleCall,     SEC_GAMEMASTER, Console::No },
            { "descend",    HandleDescend,  SEC_GAMEMASTER, Console::No },
            { "hammer",     HandleHammer,   SEC_GAMEMASTER, Console::No },
            { "storm",      HandleStorm,    SEC_GAMEMASTER, Console::No },
            { "reserve",    HandleReserve,  SEC_GAMEMASTER, Console::No },
            { "fall",       HandleFall,     SEC_GAMEMASTER, Console::No },
            { "chest",      HandleChest,    SEC_GAMEMASTER, Console::No },
            { "clear",      HandleClear,    SEC_GAMEMASTER, Console::No },
            { "heroic",     HandleHeroic,   SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_mograine_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_mograine_rework, ScarletMonasteryRework::kInstanceScriptName);
    // The companies are new entries only Mograine's AI summons: their template (last_stand.py) names this script on
    // every wave, so it registers on every wave (a declared ScriptName with no script, or the reverse, is a boot
    // error).
    RegisterDungeonReworkCreatureAI(npc_sm_last_stand_company, ScarletMonasteryRework::kInstanceScriptName);
    SmTest::RegisterBoss("laststand", BossMograineTestCommands());
}
