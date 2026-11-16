/*
 * mod-dungeon-bosses, Blackrock Spire B12: Gyth (10339), Rend Blackhand's drake, normal and heroic. One encounter with
 * Warchief Rend Blackhand (boss_rend_blackhand_rework.cpp runs the show: the acts, the rounds, the Mark and the
 * Freezing Sweep it hangs on Gyth; RendGythFight.h is how the two AIs talk). Build spec SP "Warchief Rend Blackhand and
 * Gyth" (RG2, RG6, RG9, RG10, RG14, RG16; "Tank swap at 10"), handoff section 3.4 rows RG, section 3.5 row B12.
 * Replaces the stock boss_gyth (still registered, unbound by apps/dbc-tools source/npcs/blackrock_spire/rend_gyth.py):
 * the 25% floor, Freeze 16350 and the random Flame Breath 16390 are gone; Corrosive Acid Breath 16359, Knock Away 10101
 * and Chromatic Protection stay.
 *
 *   RG2  The Drake         summoned by Rend's show at act 2 behind the drake portcullis with Rend in the saddle (Rend
 *                          Mounts 16167, the stock model swap); he walks in to his ground point inside the portcullis
 *                          (passive and immune until he is there, so the leash never sees him outside) and engages.
 *   RG6  Freezing Sweep    on the show's call he rises over the portcullis end (6 yd up, attackable from range: SP)
 *                          and breathes the walls (Freezing Breath's look, Chromatic Protection: Frost); he lands once
 *                          the last wall is past and takes his tank back. The walls are the show's (its FrontDirector,
 *                          with Gyth as the owner); the wall IS his answer while he hovers (wave 2 lesson 2).
 *   RG9  Rend's Mark       the show registers the RunOut and the aimed cone on him; at the resolve he turns on the
 *                          marked player and breathes (Flame Breath 16390's look, Chromatic Protection: Fire).
 *   RG10 Riderless         act 3 with Gyth alive: 5 s after Rend lands, then every 15 s, a 2 s bar and a 60 degree,
 *                          20 yd breath down his front (a Frontal: his tank is exempt): 40%, Weakened.
 *   RG14 Tank kit          stock Corrosive Acid Breath (8-16 s, then 10-16 s) and Knock Away (12-18 s, then 14-20 s);
 *                          Chromatic Protection: Nature after each acid breath.
 *   RG16 Corrosive Acid    10 players only: every 8 s on his tank, 15 s (stock 30), each stack +10% of his damage on
 *                          that player (his DamageDealt); the bots' taunt swap at 3 (the entry is the show's
 *                          descriptor; heroic: the tanks trade Gyth and Rend). His target's stacks hold while he cannot
 *                          breathe on it (hovering, a bar, out of reach): RendGythLogic.h.
 *   Leash                  RendGythArena() with LeashOptions (no grips), off while he hovers.
 *
 * Every timer runs on the AI's own clock. Every firing logs one INFO line "brs gyth <mechanic> ..."
 * (module.dungeonbosses); `.dbtest brs gyth <mechanic>` fires one.
 */

#include "ArenaGuard.h"
#include "BlackrockSpireKit.h"
#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "BossMechanics.h"
#include "Chat.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "InstanceScript.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RendGythFight.h"
#include "RendGythLogic.h"
#include "ScriptedCreature.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringFormat.h"
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;
using namespace BrsRendGyth;
using BossMechanics::MechanicHandle;
using BossMechanics::MechanicRef;

namespace
{
    char const* const kGythLogName = "gyth";

    enum GythTags : uint32
    {
        TAG_RG_RIDERLESS    = 10,
    };

    enum GythPoints : uint32
    {
        POINT_GYTH_ARRIVE   = 1,
        POINT_GYTH_HOVER    = 2,
        POINT_GYTH_LAND     = 3,
    };

    Milliseconds Ms(uint32 ms)
    {
        return Milliseconds(ms);
    }

    Position Ground()
    {
        return Position(kGythHoverGround.x, kGythHoverGround.y, kGythHoverGround.z, DungeonKit::kPi);
    }
}

struct boss_gyth_rework : public BossAI, public GythDrake
{
    explicit boss_gyth_rework(Creature* creature)
        : BossAI(creature, BOSS_GYTH), _arena(RendGythArena(), LeashOptions(kGythLogName)) { }

    void Reset() override
    {
        _Reset();
        Cleanup();
    }

    // Rend's show summons him (RG2): Rend in the saddle, a walk in through the portcullis, then the fight.
    void IsSummonedBy(WorldObject* /*summoner*/) override
    {
        me->AddAura(SPELL_RG_REND_MOUNTS, me);
        me->SetReactState(REACT_PASSIVE);
        me->SetImmuneToAll(true);
        _arriving = true;
        me->GetMotionMaster()->MovePoint(POINT_GYTH_ARRIVE, kGythHoverGround.x, kGythHoverGround.y,
            kGythHoverGround.z);
        Log("arrive");
    }

    // The frost wall carriers of his Sweeps (the kit's FrontDirector summons them through him): never put in combat;
    // they despawn on their own timer.
    void JustSummoned(Creature* summon) override
    {
        if (summon && summon->GetEntry() == NPC_BRS_FROST_WALL)
            return;
        BossAI::JustSummoned(summon);
    }

    void JoinShow(ObjectGuid rend, uint8 players) override
    {
        _rend = rend;
        _showPlayers = players;
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type != POINT_MOTION_TYPE && type != EFFECT_MOTION_TYPE)
            return;
        switch (id)
        {
            case POINT_GYTH_ARRIVE:
                Arrived();
                break;
            case POINT_GYTH_HOVER:
                me->SetFacingTo(DungeonKit::kPi);
                break;
            case POINT_GYTH_LAND:
                Landed();
                break;
            default:
                break;
        }
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded

        _heroic = DungeonKit::IsHeroicMap(me);
        _players = OnBossPull(me, kGythLogName);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_GYTH;
        Mechanic::BeginEncounter(me, options);
        _arena.Engage(me);
        _engaged = true;
        _now = 0;
        bool const swap = DungeonKit::Flex::TankSwapOn(_players);
        _nextAcidAt = swap ? kAcidSwapEveryMs : urand(kAcidFirstMinMs, kAcidFirstMaxMs);
        _nextKnockAt = urand(kKnockFirstMinMs, kKnockFirstMaxMs);
        Log("engage", Acore::StringFormat("players={} heroic={} tankswap={} mounted={}", _players, _heroic ? 1 : 0,
            swap ? 1 : 0, _riderless ? 0 : 1));
        if (RendShow* show = Show())
            show->OnGythEngaged(me);
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        Log("evade", Acore::StringFormat("reason={}", uint32(why)));
        bool const wasEngaged = _engaged;
        Cleanup();
        if (wasEngaged)
            if (RendShow* show = Show())
                show->OnGythEvaded(me);
        BossAI::EnterEvadeMode(why);
    }

    void JustDied(Unit* killer) override
    {
        Cleanup();
        BossAI::JustDied(killer);
        Log("death");
        if (RendShow* show = Show())
            show->OnGythDied(me);
    }

    // RG16: his hits on a player carrying his Corrosive Acid are 10% harder per stack (10 players). Nefarius's
    // Shadowflame, owned by him while he fights (R-2 M-2), is not his and never grows.
    void DamageDealt(Unit* victim, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask mask) override
    {
        if (!victim || !damage || !DungeonKit::Flex::TankSwapOn(_players) || (mask & SPELL_SCHOOL_MASK_SHADOW))
            return;
        if (uint32 const stacks = DungeonKit::Stacks(victim, SPELL_RG_CORROSIVE_ACID, me->GetGUID()))
            damage = AcidDamage(damage, stacks);
    }

    // RG16: at 10 the acid lasts 15 s (stock 30), on whoever the breath reached.
    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        if (!target || !spell || spell->Id != SPELL_RG_CORROSIVE_ACID)
            return;
        if (DungeonKit::Flex::TankSwapOn(_players))
            DungeonKit::ShortenAura(target, SPELL_RG_CORROSIVE_ACID, me->GetGUID(), Ms(kAcidMs));
        if (target == me->GetVictim())
        {
            if (target->GetGUID() == _acidHeldOn)
                _acidHeldMs = 0;    // the breath sets the duration afresh
            Log("corrosive-acid", Acore::StringFormat("on={} stacks={}", target->GetName(),
                DungeonKit::Stacks(target, SPELL_RG_CORROSIVE_ACID, me->GetGUID())));
        }
    }

    void UpdateAI(uint32 diff) override
    {
        _clockMs += diff;
        if (_hovering && _clockMs >= _hoverUntil && !_landing)
            Land();
        else if (_landing && _clockMs >= _hoverUntil + kLandFallbackMs)
        {
            // The land motion never reported (cleared or interrupted): put him down now (R-2 m-4).
            Log("land-fallback");
            me->GetMotionMaster()->Clear();
            Position ground = Ground();
            me->NearTeleportTo(ground);
            Landed();
        }

        if (!UpdateVictim())
            return;
        if (!_hovering && !_arena.Update(me, diff))
            return;     // off his arena, or nobody on it for 10 s: evading
        if (!_engaged)
            return;

        _now += diff;
        bool const swap = DungeonKit::Flex::TankSwapOn(_players);
        if (swap)
            HoldAcid(diff);
        if (Busy())
            return;

        if (_now >= _nextAcidAt)
            Acid(swap);
        if (Busy())
            return;
        if (_now >= _nextKnockAt)
        {
            _nextKnockAt = _now + urand(kKnockEveryMinMs, kKnockEveryMaxMs);
            if (me->GetVictim() && me->IsWithinMeleeRange(me->GetVictim()))
            {
                DoCastVictim(SPELL_RG_KNOCK_AWAY);
                Log("knock-away");
            }
        }
        if (_riderless && _now >= _nextBreathAt)
            RiderlessBreath();
        if (Busy())
            return;
        DoMeleeAttackIfReady();
    }

    // ---- GythDrake (the show's view of him, RendGythFight.h) ------------------------------------------------------

    bool Hover(uint32 ms) override
    {
        if (!me->IsAlive())
            return false;
        if (_arriving)
        {
            // Still walking in through the portcullis (passive, immune): a takeoff would clear his arrival point and
            // leave him passive for good (R-2 m-4). The walls roll without him.
            Log("hover-refused", "arriving");
            return false;
        }
        _hoverUntil = _clockMs + ms;
        if (_hovering)
            return true;
        _hovering = true;
        _landing = false;
        // The tank he leaves: its Corrosive Acid holds while he is aloft (he has no victim then: R-2 M-1), and he
        // takes it back when he lands.
        _hoverTank = me->GetVictim() ? me->GetVictim()->GetGUID() : ObjectGuid::Empty;
        // A riderless breath in its bar goes with the bar: no cone may resolve from the climbing drake (R-2 m-3).
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->SetCanFly(true);
        me->SetDisableGravity(true);
        Position const up(kGythHoverGround.x, kGythHoverGround.y, kGythHoverGround.z + kHoverHeightYd,
            DungeonKit::kPi);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveTakeoff(POINT_GYTH_HOVER, up);
        Log("hover", Acore::StringFormat("for={}ms tank={}", ms, _hoverTank.IsEmpty() ? 0 : 1));
        return true;
    }

    bool Hovering() const override
    {
        return _hovering;
    }

    bool Fighting() const override
    {
        return _engaged && !_arriving && me->IsAlive() && me->IsInCombat();
    }

    void BreatheWall() override
    {
        me->SetFacingTo(DungeonKit::kPi);
        me->CastSpell(me, SPELL_RG_FREEZING_BREATH, true);
        me->CastSpell(me, SPELL_RG_PROTECTION_FROST, true);
    }

    void BreatheAt(Unit* target) override
    {
        if (target)
            me->SetFacingToObject(target);
        me->CastSpell(me, SPELL_RG_FLAME_BREATH_LOOK, true);
        me->CastSpell(me, SPELL_RG_PROTECTION_FIRE, true);
        // He turns back to his tank on his next swing.
    }

    void Dismount() override
    {
        if (_riderless)
            return;
        _riderless = true;
        me->RemoveAurasDueToSpell(SPELL_RG_REND_MOUNTS);
        _nextBreathAt = _now + kRiderlessFirstMs;
        Log("dismount");
    }

    bool Riderless() const override
    {
        return _riderless;
    }

    // R-2 m-1: Rend is dead and Gyth fights on alone. The show's descriptor lived on Nefarius's encounter (it ends with
    // Rend's DONE), so his own encounter takes his kill entry and, at 10, the taunt swap on his Corrosive Acid.
    void RendFell() override
    {
        if (!_engaged || !me->IsAlive())
            return;
        BossMechanics::Descriptor d;
        d.targets.push_back(BossMechanics::TargetEntry(NPC_GYTH, 1));
        bool const swap = DungeonKit::Flex::TankSwapOn(_players);
        if (swap)
            d.tauntSwaps.emplace_back(NPC_GYTH, SPELL_RG_CORROSIVE_ACID, kSwapAt);
        Mechanic::Describe(me, std::move(d));
        Log("rend-fell", Acore::StringFormat("tankswap={}", swap ? 1 : 0));
    }

    // ---- `.dbtest brs gyth` entry points ----------------------------------------------------------------------------

    void TestAcid()
    {
        Acid(DungeonKit::Flex::TankSwapOn(_players));
    }

    void TestBreath()
    {
        RiderlessBreath();
    }

    std::string TestState() const
    {
        std::string out = Acore::StringFormat("engaged={} heroic={} players={} show-players={} tankswap={} t={}ms "
            "hovering={} riderless={} next acid/knock/breath={}/{}/{} held={}ms", _engaged ? 1 : 0, _heroic ? 1 : 0,
            _players, _showPlayers, DungeonKit::Flex::TankSwapOn(_players) ? 1 : 0, _now, _hovering ? 1 : 0,
            _riderless ? 1 : 0, _nextAcidAt, _nextKnockAt, _nextBreathAt, _acidHeldMs);
        if (Unit* victim = me->GetVictim())
            out += Acore::StringFormat("\n  victim {} corrosive acid {}", victim->GetName(),
                DungeonKit::Stacks(victim, SPELL_RG_CORROSIVE_ACID, me->GetGUID()));
        return out;
    }

private:
    RendShow* Show() const
    {
        Creature* rend = _rend.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, _rend);
        if (!rend && instance)
            rend = instance->GetCreature(BOSS_REND);
        if (!rend || !rend->IsAIEnabled)
            return nullptr;
        return dynamic_cast<RendShow*>(rend->AI());
    }

    void Log(char const* mechanic, std::string const& detail = {}) const
    {
        DungeonKit::LogMechanic(kLogDungeon, kGythLogName, mechanic, detail);
    }

    // At his ground point: open for the fight.
    void Arrived()
    {
        if (!_arriving)
            return;
        _arriving = false;
        me->SetImmuneToAll(false);
        me->SetReactState(REACT_AGGRESSIVE);
        me->SetHomePosition(Ground());
        DoZoneInCombat();
        Log("arrived");
    }

    void Land()
    {
        _landing = true;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveLand(POINT_GYTH_LAND, Ground());
    }

    // Down again: he takes back the tank he left (R-2 M-1), else his top threat.
    void Landed()
    {
        Unit* tank = _hoverTank.IsEmpty() ? nullptr : ObjectAccessor::GetUnit(*me, _hoverTank);
        EndHover();
        if (tank && tank->IsAlive() && me->IsValidAttackTarget(tank))
            AttackStart(tank);
        else if (Unit* top = me->SelectVictim())
            AttackStart(top);
        Log("landed", Acore::StringFormat("tank-back={}", (tank && me->GetVictim() == tank) ? 1 : 0));
    }

    void EndHover()
    {
        if (!_hovering)
            return;
        _hovering = false;
        _landing = false;
        _hoverTank.Clear();
        me->SetCanFly(false);
        me->SetDisableGravity(false);
        if (me->IsAlive())
            me->SetReactState(REACT_AGGRESSIVE);
    }

    // A breath bar, the hover, or the walk in.
    bool Busy() const
    {
        return _hovering || _arriving || me->HasUnitState(UNIT_STATE_CASTING);
    }

    // RG14 / RG16: his breath reaches his tank (in reach, him free); at 10 every 8 s, else the stock cadence.
    void Acid(bool swap)
    {
        Unit* victim = me->GetVictim();
        if (!victim || Busy() || !me->IsWithinMeleeRange(victim))
        {
            if (!swap)
                _nextAcidAt = _now + kRetryMs;
            return;     // at 10: every tick until he can (the stacks hold meanwhile)
        }
        me->SetFacingToObject(victim);
        DoCast(me, SPELL_RG_CORROSIVE_ACID);
        me->CastSpell(me, SPELL_RG_PROTECTION_NATURE, true);
        _nextAcidAt = _now + (swap ? kAcidSwapEveryMs : urand(kAcidEveryMinMs, kAcidEveryMaxMs));
    }

    // His target's Corrosive Acid holds while he cannot breathe on it (B7 / B14's hold): applied a second at a time; a
    // new target drops what the old one had banked. Aloft he has no victim (passive): the tank he left holds
    // (RendGythLogic.h AcidHoldFor, R-2 M-1).
    void HoldAcid(uint32 diff)
    {
        Unit* victim = me->GetVictim();
        Unit* hoverTank = _hoverTank.IsEmpty() ? nullptr : ObjectAccessor::GetUnit(*me, _hoverTank);
        if (hoverTank && !hoverTank->IsAlive())
            hoverTank = nullptr;
        bool const canBreathe = victim && !Busy() && me->IsWithinMeleeRange(victim);
        AcidHold const hold = AcidHoldFor(_hovering, victim ? victim->GetGUID().GetRawValue() : 0,
            hoverTank ? hoverTank->GetGUID().GetRawValue() : 0, canBreathe);
        Unit* target = !hold.on ? nullptr : (_hovering ? hoverTank : victim);
        ObjectGuid const on = target ? target->GetGUID() : ObjectGuid::Empty;
        if (on != _acidHeldOn)
        {
            _acidHeldOn = on;
            _acidHeldMs = 0;
        }
        if (!target)
            return;
        bool const holding = hold.holding;
        if (holding)
            _acidHeldMs += diff;
        if (!_acidHeldMs)
            return;
        Aura* aura = target->GetAura(SPELL_RG_CORROSIVE_ACID, me->GetGUID());
        if (!aura)
        {
            _acidHeldMs = 0;
            return;
        }
        if (holding && !HoldDue(_acidHeldMs, aura->GetDuration()))
            return;
        DungeonKit::ShortenAura(target, SPELL_RG_CORROSIVE_ACID, me->GetGUID(),
            Milliseconds(aura->GetDuration() + static_cast<int32>(_acidHeldMs)));
        _acidHeldMs = 0;
    }

    // RG10: a 2 s bar, then a 60 degree, 20 yd breath down his front (his tank exempt): 40%, Weakened.
    void RiderlessBreath()
    {
        _nextBreathAt = _now + kRiderlessEveryMs;
        if (!me->GetVictim())
            return;
        DungeonKit::CastBar(me, SPELL_RG_FLAME_BREATH_BAR);
        MechanicRef ref = Mechanic::Cone(me, me, kBreathAngleDeg, kBreathLengthYd, Ms(kRiderlessCastMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(kBreathPct).School(SPELL_SCHOOL_FIRE).Spell(SPELL_RG_FLAME_BREATH).Weakened().Within(RoomBounds())
            .Tag(TAG_RG_RIDERLESS);
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        ref.OnResolve([map, guid](BossMechanics::ResolveResult const& r)
        {
            Creature* gyth = map ? map->GetCreature(guid) : nullptr;
            if (r.fizzled || !gyth || !gyth->IsAlive())
                return;
            gyth->CastSpell(gyth, SPELL_RG_FLAME_BREATH_LOOK, true);
            gyth->CastSpell(gyth, SPELL_RG_PROTECTION_FIRE, true);
            DungeonKit::LogMechanic(kLogDungeon, kGythLogName, "riderless-breath-landed",
                Acore::StringFormat("hits={}", r.hits.size()));
        });
        _live.push_back(ref.Handle());
        Log("riderless-breath");
    }

    static BossMechanics::SpotBounds RoomBounds()
    {
        BossMechanics::SpotBounds bounds;
        for (auto const& box : { kWestBay, kMainStrip, kEastBay })
        {
            std::vector<Position> points;
            for (Vec2 const& p : box)
                points.emplace_back(p.x, p.y, kFloorZ, 0.f);
            bounds.Polygon(std::move(points), kRoomZMin, kRoomZMax);
        }
        return bounds;
    }

    // The pull's state, gone (wipe rule 4): his breath zones, the acid on players, the hover, the arrival.
    void Cleanup()
    {
        for (MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
        EndHover();
        if (_arriving)
        {
            _arriving = false;
            me->SetImmuneToAll(false);
        }
        if (instance)
            instance->DoRemoveAurasDueToSpellOnPlayers(SPELL_RG_CORROSIVE_ACID);
        _arena.Reset();
        _engaged = false;
        _players = 0;
        _now = 0;
        _nextAcidAt = 0;
        _nextKnockAt = 0;
        _nextBreathAt = 0;
        _acidHeldOn.Clear();
        _acidHeldMs = 0;
        _hoverTank.Clear();
    }

    DungeonKit::ArenaGuard _arena;
    std::vector<MechanicHandle> _live;
    ObjectGuid _rend;
    ObjectGuid _acidHeldOn;
    ObjectGuid _hoverTank;          // the tank he left at the takeoff (R-2 M-1)
    uint32 _acidHeldMs = 0;
    uint64 _clockMs = 0;            // ms the AI has run (the hover's clock)
    uint64 _now = 0;                // ms since the pull
    uint64 _hoverUntil = 0;
    uint64 _nextAcidAt = 0;
    uint64 _nextKnockAt = 0;
    uint64 _nextBreathAt = 0;
    uint8 _players = 0;             // the flex count held at his pull (5..10)
    uint8 _showPlayers = 0;         // the show's count (the same unless the group changed in 30 s)
    bool _heroic = false;
    bool _engaged = false;
    bool _arriving = false;
    bool _hovering = false;
    bool _landing = false;
    bool _riderless = false;
};

namespace
{
    boss_gyth_rework* FindGythAI(ChatHandler* handler)
    {
        Creature* gyth = BrsTest::FindBoss(handler, NPC_GYTH);
        if (!gyth)
            return nullptr;
        auto* ai = gyth->IsAIEnabled ? dynamic_cast<boss_gyth_rework*>(gyth->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Gyth is not running boss_gyth_rework (check the ScriptName).");
        return ai;
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return BrsTest::ShowBossInfo(handler, NPC_GYTH, BOSS_GYTH);
    }

    // `.dbtest brs gyth state`: his clock, the hover, the acid on his target.
    bool HandleState(ChatHandler* handler)
    {
        boss_gyth_rework* ai = FindGythAI(handler);
        if (!ai)
            return false;
        handler->PSendSysMessage("Gyth: {}", ai->TestState());
        return true;
    }

    // `.dbtest brs gyth acid`: Corrosive Acid Breath at his target now (RG14 / RG16).
    bool HandleAcid(ChatHandler* handler)
    {
        boss_gyth_rework* ai = FindGythAI(handler);
        if (!ai)
            return false;
        ai->TestAcid();
        handler->PSendSysMessage("{}", "Gyth: Corrosive Acid Breath (RG16; needs his target in reach).");
        return true;
    }

    // `.dbtest brs gyth breath`: the riderless Flame Breath down his front now (RG10).
    bool HandleBreath(ChatHandler* handler)
    {
        boss_gyth_rework* ai = FindGythAI(handler);
        if (!ai)
            return false;
        ai->TestBreath();
        handler->PSendSysMessage("{}", "Gyth: Flame Breath down his front (RG10).");
        return true;
    }

    // `.dbtest brs gyth hover [ms]`: he rises over the portcullis end (RG6's hover; default the normal Sweep's).
    bool HandleHover(ChatHandler* handler, Optional<uint32> ms)
    {
        boss_gyth_rework* ai = FindGythAI(handler);
        if (!ai)
            return false;
        uint32 const forMs = ms ? *ms : HoverMs(false);
        if (!ai->Hover(forMs))
        {
            handler->SendErrorMessage("{}", "Gyth: refused (dead, or still walking in).");
            return false;
        }
        handler->PSendSysMessage("Gyth: hovering for {} ms (RG6).", forMs);
        return true;
    }

    ChatCommandTable const& GythTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "state",  HandleState,  SEC_GAMEMASTER, Console::No },
            { "acid",   HandleAcid,   SEC_GAMEMASTER, Console::No },
            { "breath", HandleBreath, SEC_GAMEMASTER, Console::No },
            { "hover",  HandleHover,  SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_gyth_rework()
{
    if (kWave2Bound)
        RegisterDungeonReworkCreatureAI(boss_gyth_rework, BlackrockSpireRework::kInstanceScriptName);
    BrsTest::RegisterBoss("gyth", GythTestCommands());
}
