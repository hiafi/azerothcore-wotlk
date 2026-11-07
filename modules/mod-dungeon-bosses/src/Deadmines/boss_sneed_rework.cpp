/*
 * mod-dungeon-bosses, Deadmines: Sneed's Shredder and Sneed (WP-B3). Build spec: DM 'Sneed's Shredder and Sneed' Build
 * spec SN1-SN12, with the handoff's section 3.4 rows SN. Replaces SmartAI 642 (Terrify 7399, Distracting Pain 3603 and
 * the on-death Eject Sneed 5141) and 643 (Disarm 6713 and the Mast Room door on death): Terrify, Distracting Pain and
 * Disarm are removed (ruling 21); the eject and the door are here and in the instance's door data. The Shredder's
 * patrol (creature_addon path 792230) is data and stays; its spawn 79223 anchors mod-dungeon-clear's Sneed encounter.
 *
 * One encounter, BOSS_SNEED, owned by the Shredder: every registry mechanic of the fight (Sneed's included) is
 * registered with the Shredder as owner, so the encounter, its ledger and its Weakened stacks live from the pull to
 * Sneed's death. Sneed is tracked into it (Mechanic::TrackUnit) on every eject.
 *
 *   Shredder (642), stage 1:
 *   SN1-SN3 Haywire       every 15 s from 8 s (also after each reboot): an emote, the Malfunction visual and a 2 s
 *                         cast bar, then one of Saw Spin (circle 8 on the Shredder, 40%), Splinter Spray (frontal
 *                         90 / 10 yd, TankExempt, 30% + the tank's own 30% of tank health, 205253) or Runaway (line
 *                         4 yd through a random non-tank to 30 yd, 4 yd excluded, 35%; it charges along it), never the
 *                         same twice in a row (Sneed::PickMalfunction); all Weakened
 *   SN4 Chained (heroic)  a second, different malfunction registered as the first resolves, landing 1.5 s later
 *   Breakdown             at 1 health it does not die: the wreck (Broken Down 205254, unselectable, passive), Sneed
 *                         ejected with the Shredder's threat list (stock 5141's SpellVisual 148)
 *   SN9 Wreck Overload    the third breakdown (after both reboots): 3 s sparks, circle 10 on the wreck, 60% Fire
 *   Sneed (643), stage 2, one cast queue (Sneed::CastQueue: 3 s spacing, nothing during a repair, Tazer first):
 *   SN6 Saw Boomerang     3 s after each eject, every 15 s: 2 s cast bar, projectile line out and back, 25% per pass
 *   SN7 Repairs           8 s after each eject, every 20 s: runs to the wreck, channels 6 s / 4 s; a kick, a silence
 *                         or 10% of his health in damage stops it; completed, the Shredder reboots (SN8)
 *   SN8 Reboot            30% then 15% (normal) / 40% then 20% (heroic) of the Shredder's health; Sneed despawns
 *   SN5 Tazer             12 s after each channel begins (skipped on a completed repair); after the blast 9 s, 15 s.
 *                         Chain 3 / 4: 20/14/10% / 35/25/18/12% (spell_dm_sneed_tazer)
 *   SN10, SN11 Cluster Bomb (heroic) 10 s after each eject, every 20 s: circle 5 at a non-tank, 30% Fire; as it blows,
 *                         3 bomblets (circle 4, 6 to 10 yd away), 30% each
 *   SN12 Salvaged Saw     after the blast: Saw Spin on Sneed, 6 s, every 15 s
 *
 * Deviation (report): the wreck is killed when Sneed dies, not right after the blast, so the Shredder (the encounter
 * owner) lives for the whole fight; its loot drops at the end either way.
 *
 * Every mechanic logs one INFO line in `module.dungeonbosses`, prefix "dm-pilot sneed <mechanic>" (acceptance
 * section 1 #4).
 */

#include "Chat.h"
#include "Creature.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "GameTime.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SneedLogic.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
#include <array>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace Sneed;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    enum SneedActions : int32
    {
        ACTION_REBOOT       = 1,    // Sneed -> Shredder: a repair channel completed
        ACTION_SNEED_DIED,          // Sneed -> Shredder: the fight is won, kill the wreck
        ACTION_SNEED_EVADED,        // Sneed -> Shredder: wipe
        ACTION_WRECK_BLOWN,         // Shredder -> Sneed: the overload went off (Salvaged Saw from now on)
    };

    enum SneedData : uint32
    {
        DATA_OVERLOADING    = 1,    // Shredder GetData: 1 when this eject is the third breakdown (no repairs left)
        DATA_BROKEN         = 2,    // Shredder GetData: 1 while it is the wreck
    };

    enum SneedTaskGroups : uint32
    {
        GROUP_HAYWIRE       = 1,
    };

    enum SneedPoints : uint32
    {
        POINT_RUNAWAY_END   = 1,
        POINT_WRECK         = 2,
    };

    char const* DifficultyName(bool heroic)
    {
        return heroic ? "heroic" : "normal";
    }

    Milliseconds ToMs(Ms ms)
    {
        return Milliseconds(ms);
    }

    Ms Now()
    {
        return static_cast<Ms>(GameTime::GetGameTimeMS().count());
    }

    Vec2 ToVec2(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    void LogMechanic(Creature const* who, char const* mechanic, std::string const& detail = {})
    {
        LOG_INFO(kLog, "dm-pilot sneed {} ({}, {} {}){}{}", mechanic, DifficultyName(DeadminesKit::IsHeroicMap(who)),
            who->GetName(), who->GetGUID().ToString(), detail.empty() ? "" : ": ", detail);
    }

    // A random non-tank player on `me`'s threat list; the victim when there is none (a solo GM).
    Unit* RandomNonTank(Creature* me)
    {
        if (Unit* target = me->AI()->SelectTarget(SelectTargetMethod::Random, 0, NonTankTargetSelector(me, true)))
            return target;
        return me->GetVictim();
    }

    // Sneed inherits the Shredder's threat list (ruling 21), and the Shredder Sneed's on a reboot. Returns the unit
    // with the most threat on `from`.
    Unit* CopyThreat(Unit* from, Creature* to)
    {
        Unit* top = nullptr;
        float best = -1.f;
        for (ThreatReference* ref : from->GetThreatMgr().GetModifiableThreatList())
        {
            Unit* victim = ref->GetVictim();
            if (!victim || !victim->IsAlive())
                continue;
            float const threat = ref->GetThreat();
            to->GetThreatMgr().AddThreat(victim, threat, nullptr, true, true);
            if (threat > best)
            {
                best = threat;
                top = victim;
            }
        }
        return top;
    }
}

// Sneed's Shredder 642. A ScriptedAI (its death is not the encounter's): BOSS_SNEED goes IN_PROGRESS when it engages
// and DONE on Sneed's death (Sneed's BossAI).
struct boss_sneeds_shredder_rework : public ScriptedAI
{
    explicit boss_sneeds_shredder_rework(Creature* creature) : ScriptedAI(creature),
        _instance(creature->GetInstanceScript()) { }

    void Reset() override
    {
        scheduler.CancelAll();
        DespawnSneed();
        ClearWreck();
        _ladder = {};
        _lastMalfunction.reset();
        _haywire.clear();
        _overloading = false;
        _blown = false;
        _charging = false;
        _allowDeath = false;
        me->SetFullHealth();
    }

    void JustEngagedWith(Unit* who) override
    {
        if (_instance)
            _instance->SetBossState(BOSS_SNEED, IN_PROGRESS);
        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_SNEED;
        Mechanic::BeginEncounter(me, options);
        Mechanic::Describe(me, BuildDescriptor());
        ScheduleHaywire(kHaywireFirstMs(Heroic()));
        LogMechanic(me, "engage", who ? std::string("pulled by ") + who->GetName() : std::string());
    }

    void EnterEvadeMode(EvadeReason why) override
    {
        if (_instance && _instance->GetBossState(BOSS_SNEED) != DONE)
        {
            _instance->SetBossState(BOSS_SNEED, NOT_STARTED);
            _instance->SaveToDB();
        }
        if (_broken || _ladder.breakdowns)
            LogMechanic(me, "reset", "wipe after " + std::to_string(_ladder.breakdowns) + " breakdown(s)");
        DespawnSneed();
        ClearWreck();
        ScriptedAI::EnterEvadeMode(why);
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*school*/) override
    {
        if (_allowDeath)
            return;
        if (_broken)
        {
            damage = 0;     // the wreck takes nothing (DoTs, area damage)
            return;
        }
        if (damage < me->GetHealth())
            return;
        damage = me->GetHealth() > 1 ? me->GetHealth() - 1 : 0;
        BreakDown();
    }

    // A ScriptedAI keeps CreatureAI's "always respawn"; BossAI's version refuses a DONE boss. Without this, a Shredder
    // respawned in a long-lived instance would set BOSS_SNEED IN_PROGRESS again and a wipe would re-close the door.
    bool CanRespawn() override
    {
        return !_instance || _instance->GetBossState(BOSS_SNEED) != DONE;
    }

    void JustDied(Unit* /*killer*/) override
    {
        scheduler.CancelAll();
        LogMechanic(me, "wreck-killed", _allowDeath ? "Sneed is dead, the wreck's loot drops" : "killed directly");
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_RUNAWAY_END)
            EndCharge();
    }

    uint32 GetData(uint32 id) const override
    {
        if (id == DATA_OVERLOADING)
            return (_overloading || _blown) ? 1 : 0;
        if (id == DATA_BROKEN)
            return _broken ? 1 : 0;
        return 0;
    }

    void DoAction(int32 action) override
    {
        switch (action)
        {
            case ACTION_REBOOT:
                Reboot();
                break;
            case ACTION_SNEED_DIED:
                if (me->IsAlive())
                {
                    _allowDeath = true;
                    ClearWreck();       // a NOT_SELECTABLE corpse cannot be looted (Sprecklesprocket, quest 2040)
                    me->KillSelf();
                }
                break;
            case ACTION_SNEED_EVADED:
                if (me->IsAlive() && !me->IsInEvadeMode())
                    EnterEvadeMode(EVADE_REASON_OTHER);
                break;
            default:
                break;
        }
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);

        if (_broken)
        {
            // The wreck neither fights nor picks a victim (UpdateVictim would evade it: it threatens nobody). It
            // resets when the encounter does: Sneed's evade calls ACTION_SNEED_EVADED; this catches the rest.
            if (_instance && _instance->GetBossState(BOSS_SNEED) == NOT_STARTED)
                EnterEvadeMode(EVADE_REASON_OTHER);
            else if (!GetSneed() && !_allowDeath)
                EnterEvadeMode(EVADE_REASON_OTHER);
            return;
        }

        if (!UpdateVictim())
            return;
        if (_charging || me->HasUnitState(UNIT_STATE_CASTING))
            return;
        DoMeleeAttackIfReady();
    }

    // ---- .dmtest hooks ---------------------------------------------------------------------------------------------

    bool TestMalfunction(Malfunction m, bool chained)
    {
        if (_broken)
            return false;
        Fire(m, !chained, ToMs(chained ? kChainWarnMs(Heroic()) : kHaywireWarnMs(Heroic())), chained);
        return true;
    }

    bool TestHaywire()
    {
        if (_broken)
            return false;
        DoHaywire();
        return true;
    }

    // Break down now; `toOverload` first spends both reboots, so this breakdown is the third (SN9).
    bool TestBreakdown(bool toOverload)
    {
        if (_broken || !me->IsInCombat())
            return false;
        if (toOverload)
            while (_ladder.RepairsLeft())
                _ladder.OnReboot(Heroic());
        me->SetHealth(1);
        BreakDown();
        return true;
    }

    bool IsBroken() const { return _broken; }

private:
    bool Heroic() const { return DeadminesKit::IsHeroicMap(me); }

    Creature* GetSneed() const
    {
        return _sneed.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, _sneed);
    }

    void DespawnSneed()
    {
        if (Creature* sneed = GetSneed())
            sneed->DespawnOrUnsummon(100ms);
        _sneed.Clear();
    }

    void ClearWreck()
    {
        _broken = false;
        me->RemoveAurasDueToSpell(SPELL_BROKEN_DOWN);
        me->RemoveUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    BossMechanics::Descriptor BuildDescriptor() const
    {
        using BossMechanics::Condition;
        using BossMechanics::Who;
        BossMechanics::Descriptor d;
        // Interrupts, in priority: Emergency Repairs above Tazer (DM boss data; the class tool pass).
        d.interrupts.emplace_back(NPC_SNEED, SPELL_EMERGENCY_REPAIRS, 2, ToMs(kRepairEveryMs(false)));
        d.interrupts.emplace_back(NPC_SNEED, SPELL_EMERGENCY_REPAIRS_FAST, 2, ToMs(kRepairEveryMs(true)));
        d.interrupts.emplace_back(NPC_SNEED, SPELL_TAZER, 1, ToMs(kRepairEveryMs(false)));
        d.interrupts.emplace_back(NPC_SNEED, SPELL_TAZER_HEROIC, 1, ToMs(kRepairEveryMs(true)));
        // Kill order: the Shredder while it is up (it leaves as the wreck and comes back on a reboot), then Sneed.
        // Who::Any: the tank switches with the damage dealers.
        d.targets.emplace_back(NPC_SNEEDS_SHREDDER, 1, Who::Any, Condition::LacksAura(SPELL_BROKEN_DOWN));
        d.targets.emplace_back(NPC_SNEED, 1, Who::Any);
        d.ignores.emplace_back(NPC_SNEEDS_SHREDDER, Condition::HasAura(SPELL_BROKEN_DOWN));
        // Dispels and purges: none (build spec boss data).
        return d;
    }

    // ---- Haywire (SN1-SN4) -----------------------------------------------------------------------------------------

    void ScheduleHaywire(Ms first)
    {
        scheduler.Schedule(ToMs(first), GROUP_HAYWIRE, [this](TaskContext ctx)
        {
            DoHaywire();
            ctx.Repeat(ToMs(kHaywireEveryMs(Heroic())));
        });
    }

    void DoHaywire()
    {
        bool const heroic = Heroic();
        Malfunction const first = PickMalfunction(_lastMalfunction, urand(0, 0xFFFF));
        _lastMalfunction = first;
        Fire(first, true, ToMs(kHaywireWarnMs(heroic)), false);
        if (!kChainedHaywire(heroic))
            return;
        // SN4: registered as the first resolves (its warning), landing 1.5 s later.
        Malfunction const second = PickChained(first, urand(0, 0xFFFF));
        _lastMalfunction = second;
        scheduler.Schedule(ToMs(kHaywireWarnMs(heroic)), GROUP_HAYWIRE, [this, second](TaskContext /*ctx*/)
        {
            if (!_broken)
                Fire(second, false, ToMs(kChainWarnMs(Heroic())), true);
        });
    }

    // One malfunction: emote, visual, (cast bar), the registry zone, and its scripted follow-through at the resolve.
    void Fire(Malfunction m, bool castBar, Milliseconds warn, bool chained)
    {
        bool const heroic = Heroic();
        DoCastSelf(SPELL_MALFUNCTION, true);
        std::string detail = chained ? "chained" : "first";
        switch (m)
        {
            case Malfunction::SawSpin:
            {
                Talk(EMOTE_SHREDDER_SAW_SPIN);
                if (castBar)
                    DoCastSelf(SPELL_SAW_SPIN_CAST);
                _haywire.push_back(Mechanic::Circle(me, me, kSawSpinRadius(heroic), warn)
                    .Damage(kSawSpinPct(heroic)).Spell(SPELL_SAW_SPIN_HIT).Weakened().Tag(TAG_SAW_SPIN));
                break;
            }
            case Malfunction::SplinterSpray:
            {
                Talk(EMOTE_SHREDDER_SPLINTER_SPRAY);
                if (castBar)
                    DoCastSelf(SPELL_SPLINTER_SPRAY_CAST);
                _haywire.push_back(Mechanic::Cone(me, me, kSprayAngleDeg(heroic), kSprayLength(heroic), warn,
                    BossMechanics::TankExempt::Yes)
                    .Damage(kSprayPct(heroic)).TankDamage(kSprayTankPct(heroic)).Spell(SPELL_SPLINTER_SPRAY_HIT)
                    .Weakened().Tag(TAG_SPLINTER_SPRAY));
                scheduler.Schedule(warn, GROUP_HAYWIRE, [this](TaskContext /*ctx*/) { SprayTankHit(); });
                break;
            }
            case Malfunction::Runaway:
            {
                Unit* target = RandomNonTank(me);
                if (!target)
                    return;
                Talk(EMOTE_SHREDDER_RUNAWAY);
                if (castBar)
                    DoCastSelf(SPELL_RUNAWAY_CAST);
                Vec2 const end = LineEnd(ToVec2(me->GetPosition()), ToVec2(target->GetPosition()),
                    kRunawayLength(heroic), me->GetOrientation());
                Position const endPos(end.x, end.y, target->GetPositionZ());
                // A fixed line (point anchors, as the gap-8 drill's `fix=1` Runaway): it charges along it later.
                Position const from = me->GetPosition();
                _haywire.push_back(Mechanic::Line(me, from, endPos, kRunawayWidth(heroic), warn)
                    .ExcludeSourceEnd(kRunawayExclude(heroic)).Damage(kRunawayPct(heroic)).Spell(SPELL_RUNAWAY_HIT)
                    .Weakened().Tag(TAG_RUNAWAY));
                scheduler.Schedule(warn, GROUP_HAYWIRE, [this, endPos](TaskContext /*ctx*/) { Charge(endPos); });
                detail += std::string(", through ") + target->GetName();
                break;
            }
        }
        if (_haywire.size() > 8)
            _haywire.erase(_haywire.begin(), _haywire.end() - 4);     // resolved long ago; keep the recent ones
        LogMechanic(me, chained ? "chained-haywire" : "haywire", std::string(MalfunctionName(m)) + " (" + detail + ")");
    }

    // SN2: the frontal skips the tank (TankExempt); the tank takes its own 30% of tank health if it stands in front.
    void SprayTankHit()
    {
        if (_broken)
            return;
        Unit* tank = me->GetVictim();
        if (!tank)
            return;
        bool const heroic = Heroic();
        if (!InFrontalCone(ToVec2(me->GetPosition()), me->GetOrientation(), ToVec2(tank->GetPosition()),
            kSprayAngleDeg(heroic), kSprayLength(heroic), me->GetCombatReach() + tank->GetCombatReach()))
            return;
        DoCast(tank, SPELL_SPLINTER_SPRAY_TANK, true);
        LogMechanic(me, "splinter-spray-tank", std::string("hit ") + tank->GetName());
    }

    // SN3: charges along the line after it resolves, then back to the tank.
    void Charge(Position const& endPos)
    {
        if (_broken)
            return;
        Position const dest = me->GetFirstCollisionPosition(endPos.GetPositionX(), endPos.GetPositionY(),
            endPos.GetPositionZ());
        _charging = true;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveCharge(dest.GetPositionX(), dest.GetPositionY(), dest.GetPositionZ(),
            kRunawayChargeSpeed(Heroic()), POINT_RUNAWAY_END);
        uint32 const charge = ++_chargeId;
        scheduler.Schedule(ToMs(kRunawayReturnMs(Heroic())), GROUP_HAYWIRE, [this, charge](TaskContext /*ctx*/)
        {
            if (_charging && charge == _chargeId)
                EndCharge();
        });
    }

    void EndCharge()
    {
        if (!_charging)
            return;
        _charging = false;
        if (_broken)
            return;
        if (Unit* victim = me->GetVictim())
        {
            me->GetMotionMaster()->Clear();
            me->GetMotionMaster()->MoveChase(victim);
        }
    }

    void CancelHaywire()
    {
        scheduler.CancelGroup(GROUP_HAYWIRE);
        for (BossMechanics::MechanicHandle const& h : _haywire)
            Mechanic::Cancel(me, h);
        _haywire.clear();
        _charging = false;
    }

    // ---- Breakdown, reboot, overload (SN7-SN9) ---------------------------------------------------------------------

    void BreakDown()
    {
        if (_broken)
            return;
        _broken = true;
        CancelHaywire();
        Breakdown const outcome = _ladder.OnBreakdown();
        _overloading = outcome == Breakdown::EjectAndOverload;

        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        me->StopMoving();
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->SetUnitFlag(UNIT_FLAG_NOT_SELECTABLE);
        DoCastSelf(SPELL_BROKEN_DOWN, true);
        me->SendPlaySpellVisual(kEjectSpellVisual);

        LogMechanic(me, "breakdown", "breakdown " + std::to_string(_ladder.breakdowns) + ", reboots used "
            + std::to_string(_ladder.reboots) + (_overloading ? ", overload" : ", Sneed will repair"));
        EjectSneed();
        if (_overloading)
            StartOverload();
    }

    void EjectSneed()
    {
        Position const pos = me->GetNearPosition(me->GetCombatReach() + 1.f, float(M_PI) / 2.f);
        // A corpse that stays for his loot; the Shredder despawns him on a reboot or a reset.
        TempSummon* sneed = me->SummonCreature(NPC_SNEED, pos, TEMPSUMMON_CORPSE_TIMED_DESPAWN,
            10 * MINUTE * IN_MILLISECONDS);
        if (!sneed)
        {
            LOG_ERROR(kLog, "dm-pilot sneed: could not summon Sneed (643) at the wreck {}", me->GetGUID().ToString());
            return;
        }
        _sneed = sneed->GetGUID();
        Mechanic::TrackUnit(me, sneed);
        Unit* top = CopyThreat(me, sneed);
        if (top && sneed->IsAIEnabled)
            sneed->AI()->AttackStart(top);
        LogMechanic(me, "eject", std::string("Sneed ") + sneed->GetGUID().ToString());
    }

    void Reboot()
    {
        if (!_broken || _overloading || _blown)
            return;
        float const pct = _ladder.OnReboot(Heroic());
        if (pct <= 0.f)
            return;
        Creature* sneed = GetSneed();
        ClearWreck();
        me->SetHealth(std::max<uint32>(1, me->CountPctFromMaxHealth(static_cast<int32>(pct))));
        Unit* top = sneed ? CopyThreat(sneed, me) : nullptr;
        if (!top)
            top = SelectTarget(SelectTargetMethod::MaxThreat, 0);
        DespawnSneed();
        me->GetMotionMaster()->Clear();
        if (top)
            AttackStart(top);
        ScheduleHaywire(kHaywireFirstMs(Heroic()));
        LogMechanic(me, "reboot", "reboot " + std::to_string(_ladder.reboots) + " at " + std::to_string(int(pct))
            + "% health");
    }

    void StartOverload()
    {
        bool const heroic = Heroic();
        Talk(EMOTE_SHREDDER_OVERLOAD);
        DoCastSelf(SPELL_OVERLOAD_SPARKS);
        Mechanic::Circle(me, me, kOverloadRadius(heroic), ToMs(kOverloadWarnMs(heroic)))
            .Damage(kOverloadPct(heroic)).School(SPELL_SCHOOL_FIRE).Spell(SPELL_WRECK_OVERLOAD_HIT)
            .Tag(TAG_WRECK_OVERLOAD);
        LogMechanic(me, "wreck-overload", "sparks, blast in 3 s");
        scheduler.Schedule(ToMs(kOverloadWarnMs(heroic)), [this](TaskContext /*ctx*/)
        {
            _overloading = false;
            _blown = true;
            DoCastSelf(SPELL_OVERLOAD_BLAST, true);
            LogMechanic(me, "wreck-overload-blast");
            if (Creature* sneed = GetSneed())
                if (sneed->IsAIEnabled)
                    sneed->AI()->DoAction(ACTION_WRECK_BLOWN);
        });
    }

    InstanceScript* _instance;
    ObjectGuid _sneed;
    RebootLadder _ladder;
    std::optional<Malfunction> _lastMalfunction;
    std::vector<BossMechanics::MechanicHandle> _haywire;
    uint32 _chargeId = 0;
    bool _broken = false;
    bool _overloading = false;
    bool _blown = false;
    bool _charging = false;
    bool _allowDeath = false;
};

// Sneed 643: summoned by the Shredder on every breakdown, despawned on every reboot. A BossAI for BOSS_SNEED's DONE
// (BossAI::_JustDied); its Reset never runs BossAI::_Reset, which would set the encounter NOT_STARTED on every eject.
struct boss_sneed_rework : public BossAI
{
    explicit boss_sneed_rework(Creature* creature) : BossAI(creature, BOSS_SNEED) { }

    void Reset() override { }

    void IsSummonedBy(WorldObject* summoner) override
    {
        _shredder = summoner ? summoner->GetGUID() : ObjectGuid::Empty;
        Creature* shredder = summoner ? summoner->ToCreature() : nullptr;
        _noRepairs = shredder && shredder->IsAIEnabled && shredder->AI()->GetData(DATA_OVERLOADING) != 0;
        bool const heroic = Heroic();
        Ms const now = Now();
        _queue.Reset();
        _queue.Schedule(Cast::SawBoomerang, now + kBoomerangFirstMs(heroic));
        if (!_noRepairs)
        {
            _queue.Schedule(Cast::RepairRun, now + kRepairFirstMs(heroic));
            Mechanic::NoteNextCastIn(me, RepairSpell(), ToMs(kRepairFirstMs(heroic)));
        }
        if (kClusterBomb(heroic))
            _queue.Schedule(Cast::ClusterBomb, now + kClusterFirstMs(heroic));
        Talk(SAY_SNEED_EJECT);
    }

    void JustEngagedWith(Unit* /*who*/) override { }    // never BossAI::_JustEngagedWith (zone combat, state)

    void EnterEvadeMode(EvadeReason /*why*/) override
    {
        if (_evading)
            return;
        _evading = true;
        LogMechanic(me, "reset", "Sneed evaded");
        if (Creature* shredder = GetShredder(); shredder && shredder->IsAIEnabled)
            shredder->AI()->DoAction(ACTION_SNEED_EVADED);     // resets the encounter and despawns Sneed
        else
        {
            if (instance && instance->GetBossState(BOSS_SNEED) != DONE)
                instance->SetBossState(BOSS_SNEED, NOT_STARTED);
            me->DespawnOrUnsummon(100ms);
        }
    }

    void JustDied(Unit* killer) override
    {
        _JustDied();    // BOSS_SNEED DONE: the Mast Room door opens (door data), the registry encounter ends
        LogMechanic(me, "death", killer ? std::string("killed by ") + killer->GetName() : std::string());
        if (Creature* shredder = GetShredder(); shredder && shredder->IsAIEnabled)
            shredder->AI()->DoAction(ACTION_SNEED_DIED);
    }

    void DamageTaken(Unit* /*attacker*/, uint32& damage, DamageEffectType /*type*/, SpellSchoolMask /*school*/) override
    {
        if (!_channeling || _breakSent)
            return;
        _breakDamage += damage;
        if (!BreaksRepair(_breakDamage, me->GetMaxHealth(), Heroic()))
            return;
        _breakSent = true;
        LogMechanic(me, "repairs-broken", "damage " + std::to_string(_breakDamage) + " of "
            + std::to_string(RepairBreakThreshold(me->GetMaxHealth(), Heroic())));
        me->InterruptNonMeleeSpells(false);     // OnSpellFailed ends the run
    }

    void OnSpellFailed(SpellInfo const* spell) override
    {
        if (IsRepairSpell(spell->Id) && _channeling)
        {
            if (!_breakSent)
                LogMechanic(me, "repairs-interrupted");
            EndRepair(false);
        }
        else if (spell->Id == TazerSpell())
            LogMechanic(me, "tazer-interrupted");
    }

    void OnChannelFinished(SpellInfo const* spell) override
    {
        if (IsRepairSpell(spell->Id) && _channeling)
            EndRepair(true);
    }

    void MovementInform(uint32 type, uint32 id) override
    {
        if (type == POINT_MOTION_TYPE && id == POINT_WRECK)
            BeginChannel();
    }

    void DoAction(int32 action) override
    {
        if (action != ACTION_WRECK_BLOWN || _salvaged)
            return;
        bool const heroic = Heroic();
        Ms const now = Now();
        _salvaged = true;
        _noRepairs = true;
        _queue.Cancel(Cast::RepairRun);
        _queue.Schedule(Cast::SawSpin, now + kSalvagedSawFirstMs(heroic));
        _queue.Schedule(Cast::Tazer, now + kTazerSalvagedFirstMs(heroic));
        Mechanic::NoteNextCastIn(me, TazerSpell(), ToMs(kTazerSalvagedFirstMs(heroic)));
        Talk(EMOTE_SNEED_SALVAGED_SAW);
        LogMechanic(me, "salvaged-saw", "Sneed takes the saw: Saw Spin from 6 s, Tazer from 9 s");
    }

    void UpdateAI(uint32 diff) override
    {
        scheduler.Update(diff);
        if (_repairing || _handedBack)
            return;     // running to the wreck, channeling, or back in the Shredder: no victim, melee or cast
        if (!UpdateVictim())
            return;
        if (me->HasUnitState(UNIT_STATE_CASTING))
            return;
        Ms const now = Now();
        switch (_queue.Next(now))
        {
            case Cast::Tazer:
                DoTazer(now);
                break;
            case Cast::RepairRun:
                StartRepairRun(now);
                return;
            case Cast::SawSpin:
                DoSalvagedSaw(now);
                break;
            case Cast::SawBoomerang:
                DoSawBoomerang(now);
                break;
            case Cast::ClusterBomb:
                DoClusterBomb(now);
                break;
            default:
                break;
        }
        DoMeleeAttackIfReady();
    }

    // ---- .dmtest hooks ---------------------------------------------------------------------------------------------

    bool TestCast(Cast c)
    {
        if (_repairing || _handedBack || !me->IsInCombat())
            return false;
        Ms const now = Now();
        switch (c)
        {
            case Cast::Tazer:
                DoTazer(now);
                return true;
            case Cast::RepairRun:
                if (_noRepairs)
                    return false;
                StartRepairRun(now);
                return true;
            case Cast::SawSpin:
                DoSalvagedSaw(now);
                return true;
            case Cast::SawBoomerang:
                DoSawBoomerang(now);
                return true;
            case Cast::ClusterBomb:
                DoClusterBomb(now);
                return true;
            default:
                return false;
        }
    }

private:
    bool Heroic() const { return DeadminesKit::IsHeroicMap(me); }
    uint32 RepairSpell() const { return Heroic() ? SPELL_EMERGENCY_REPAIRS_FAST : SPELL_EMERGENCY_REPAIRS; }
    uint32 TazerSpell() const { return Heroic() ? SPELL_TAZER_HEROIC : SPELL_TAZER; }
    static bool IsRepairSpell(uint32 id) { return id == SPELL_EMERGENCY_REPAIRS || id == SPELL_EMERGENCY_REPAIRS_FAST; }

    Creature* GetShredder() const
    {
        return _shredder.IsEmpty() ? nullptr : ObjectAccessor::GetCreature(*me, _shredder);
    }

    // The encounter's owner: the Shredder (alive for the whole fight); Sneed himself if it is gone (a GM kill).
    Unit* Owner()
    {
        if (Creature* shredder = GetShredder(); shredder && shredder->IsAlive())
            return shredder;
        return me;
    }

    // ---- SN7 Emergency Repairs -------------------------------------------------------------------------------------

    void StartRepairRun(Ms now)
    {
        Creature* shredder = GetShredder();
        if (!shredder || _noRepairs)
        {
            _queue.Cancel(Cast::RepairRun);
            return;
        }
        bool const heroic = Heroic();
        _repairing = true;
        _channeling = false;
        _queue.Started(Cast::RepairRun, now, kRepairEveryMs(heroic));
        _queue.SetBusy(true);
        Mechanic::NoteNextCastIn(me, RepairSpell(), ToMs(kRepairEveryMs(heroic)));
        Talk(EMOTE_SNEED_REPAIRS);
        me->InterruptNonMeleeSpells(false);
        me->AttackStop();
        me->SetReactState(REACT_PASSIVE);
        Position const spot = shredder->GetNearPosition(shredder->GetCombatReach() + 1.f,
            shredder->GetRelativeAngle(me));
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_WRECK, spot);
        uint32 const run = ++_runId;
        scheduler.Schedule(ToMs(kRepairRunTimeoutMs(heroic)), [this, run](TaskContext /*ctx*/)
        {
            if (run == _runId && _repairing && !_channeling)
                BeginChannel();
        });
        LogMechanic(me, "repairs-run", "to the wreck");
    }

    void BeginChannel()
    {
        if (!_repairing || _channeling)
            return;
        me->StopMoving();
        if (Creature* shredder = GetShredder())
            me->SetFacingToObject(shredder);
        _breakDamage = 0;
        _breakSent = false;
        _channeling = true;     // set before the cast: a failed start reports through OnSpellFailed
        SpellCastResult const result = DoCastSelf(RepairSpell());
        if (result != SPELL_CAST_OK)
        {
            if (_channeling)
            {
                LogMechanic(me, "repairs-failed", "cast result " + std::to_string(int(result)));
                EndRepair(false);
            }
            return;
        }
        Ms const now = Now();
        _queue.ChannelStarted(now, kTazerAfterChannelMs(Heroic()));
        Mechanic::NoteNextCastIn(me, TazerSpell(), ToMs(kTazerAfterChannelMs(Heroic())));
        LogMechanic(me, "repairs", "channel " + std::to_string(kRepairChannelMs(Heroic()) / 1000) + " s");
    }

    void EndRepair(bool completed)
    {
        _channeling = false;
        _repairing = false;
        _queue.SetBusy(false);
        if (completed)
        {
            _queue.RepairCompleted();
            Talk(EMOTE_SNEED_BACK_IN_BUSINESS);
            LogMechanic(me, "repairs-completed", "the Shredder reboots");
            Creature* shredder = GetShredder();
            if (shredder && shredder->IsAIEnabled)
            {
                shredder->AI()->DoAction(ACTION_REBOOT);   // despawns Sneed in 100 ms
                if (!shredder->AI()->GetData(DATA_BROKEN))
                {
                    _handedBack = true;     // nothing more until the despawn
                    return;
                }
            }
            LOG_ERROR(kLog, "dm-pilot sneed: a completed repair did not reboot the Shredder; Sneed fights on");
        }
        if (!me->IsAlive())
            return;
        me->SetReactState(REACT_AGGRESSIVE);
        if (Unit* victim = SelectTarget(SelectTargetMethod::MaxThreat, 0))
            AttackStart(victim);
    }

    // ---- SN5 Tazer -------------------------------------------------------------------------------------------------

    void DoTazer(Ms now)
    {
        bool const heroic = Heroic();
        _queue.Started(Cast::Tazer, now, _salvaged ? kTazerSalvagedEveryMs(heroic) : 0);
        if (_salvaged)
            Mechanic::NoteNextCastIn(me, TazerSpell(), ToMs(kTazerSalvagedEveryMs(heroic)));
        Unit* target = RandomNonTank(me);
        if (!target)
            return;
        DoCast(target, TazerSpell());
        LogMechanic(me, "tazer", std::string("at ") + target->GetName() + ", " + std::to_string(TazerTargets(heroic))
            + " targets");
    }

    // ---- SN6 Saw Boomerang -----------------------------------------------------------------------------------------

    void DoSawBoomerang(Ms now)
    {
        bool const heroic = Heroic();
        _queue.Started(Cast::SawBoomerang, now, kBoomerangEveryMs(heroic));
        Unit* target = RandomNonTank(me);
        if (!target)
            return;
        Unit* owner = Owner();
        Position const from = me->GetPosition();
        Vec2 const end = LineEnd(ToVec2(from), ToVec2(target->GetPosition()), kBoomerangLength(heroic),
            me->GetOrientation());
        Position const endPos(end.x, end.y, target->GetPositionZ());
        me->SetFacingToObject(target);
        DoCastSelf(SPELL_SAW_BOOMERANG_CAST);
        Milliseconds const warn = ToMs(kBoomerangWarnMs(heroic));
        Mechanic::Line(owner, from, endPos, kBoomerangWidth(heroic), warn).Projectile(kBoomerangSpeed(heroic))
            .OutAndBack().ExcludeSourceEnd(kBoomerangExclude(heroic)).Damage(kBoomerangPct(heroic))
            .Spell(SPELL_SAW_BOOMERANG_HIT).Weakened().Tag(TAG_SAW_BOOMERANG);
        // m_Events, not the BossAI scheduler: that one pauses while Sneed holds the 2 s cast bar, and the blade must
        // leave with the registry projectile.
        me->m_Events.AddEventAtOffset([this, endPos]()
        {
            if (me->IsAlive())
                me->CastSpell(endPos.GetPositionX(), endPos.GetPositionY(), endPos.GetPositionZ(),
                    SPELL_SAW_BOOMERANG_THROW, true);
        }, warn);
        LogMechanic(me, "saw-boomerang", std::string("through ") + target->GetName());
    }

    // ---- SN10, SN11 Cluster Bomb (heroic) --------------------------------------------------------------------------

    void DoClusterBomb(Ms now)
    {
        bool const heroic = Heroic();
        _queue.Started(Cast::ClusterBomb, now, kClusterEveryMs(heroic));
        Unit* target = RandomNonTank(me);
        if (!target)
            return;
        Unit* owner = Owner();
        Position const center = target->GetPosition();
        me->CastSpell(center.GetPositionX(), center.GetPositionY(), center.GetPositionZ(), SPELL_CLUSTER_BOMB_LOB,
            true);
        // The bomblets' spots are rolled now; the callback captures values and guids only (STAGE-M5-R m-4).
        std::array<float, kBombletCount> angles{};
        std::array<float, kBombletCount> dists{};
        for (std::size_t i = 0; i < kBombletCount; ++i)
        {
            angles[i] = static_cast<float>(rand_norm());
            dists[i] = static_cast<float>(rand_norm());
        }
        std::array<Vec2, kBombletCount> const spots = BombletSpots(ToVec2(center), angles, dists, heroic);
        Map* map = me->GetMap();
        ObjectGuid const ownerGuid = owner->GetGUID();
        ObjectGuid const sneedGuid = me->GetGUID();
        float const z = center.GetPositionZ();
        Mechanic::Circle(owner, center, kClusterRadius(heroic), ToMs(kClusterWarnMs(heroic)))
            .Damage(kClusterPct(heroic)).School(SPELL_SCHOOL_FIRE).Spell(SPELL_CLUSTER_BOMB_HIT).Weakened()
            .Tag(TAG_CLUSTER_BOMB)
            .OnResolve([map, ownerGuid, sneedGuid, center, spots, z, heroic](BossMechanics::ResolveResult const&)
            {
                Unit* bomber = map->GetCreature(sneedGuid);
                if (bomber)
                    bomber->CastSpell(center.GetPositionX(), center.GetPositionY(), z, SPELL_CLUSTER_BOMB_BLAST,
                        true);
                Unit* source = map->GetCreature(ownerGuid);
                if (!source)
                    return;
                for (Vec2 const& spot : spots)
                {
                    Position const p(spot.x, spot.y, z);
                    Mechanic::Circle(source, p, kBombletRadius(heroic), ToMs(kBombletWarnMs(heroic)))
                        .Damage(kBombletPct(heroic)).School(SPELL_SCHOOL_FIRE).Spell(SPELL_CLUSTER_BOMB_HIT)
                        .Weakened().Tag(TAG_BOMBLET)
                        .OnResolve([map, sneedGuid, p](BossMechanics::ResolveResult const&)
                        {
                            if (Unit* sneed = map->GetCreature(sneedGuid))
                                sneed->CastSpell(p.GetPositionX(), p.GetPositionY(), p.GetPositionZ(),
                                    SPELL_CLUSTER_BOMB_BLAST, true);
                        });
                }
                LOG_INFO(kLog, "dm-pilot sneed cluster-bomb-bomblets ({}): {} bomblets", heroic ? "heroic" : "normal",
                    kBombletCount);
            });
        LogMechanic(me, "cluster-bomb", std::string("at ") + target->GetName());
    }

    // ---- SN12 Salvaged Saw -----------------------------------------------------------------------------------------

    void DoSalvagedSaw(Ms now)
    {
        bool const heroic = Heroic();
        _queue.Started(Cast::SawSpin, now, kSalvagedSawEveryMs(heroic));
        DoCastSelf(SPELL_SAW_SPIN_CAST);
        Mechanic::Circle(Owner(), me, kSawSpinRadius(heroic), ToMs(kHaywireWarnMs(heroic)))
            .Damage(kSawSpinPct(heroic)).Spell(SPELL_SAW_SPIN_HIT).Weakened().Tag(TAG_SALVAGED_SAW);
        LogMechanic(me, "salvaged-saw-spin");
    }

    ObjectGuid _shredder;
    CastQueue _queue;
    uint32 _breakDamage = 0;
    uint32 _runId = 0;
    bool _noRepairs = false;
    bool _salvaged = false;
    bool _repairing = false;
    bool _channeling = false;
    bool _breakSent = false;
    bool _evading = false;
    bool _handedBack = false;
};

// 205247 / 205248 Tazer: each jump's damage is a percent of reference health by jump order (20/14/10% normal,
// 35/25/18/12% heroic). The value is set at launch (as spell_dm_rhahkzor_ref_flat) so the target's damage-taken
// modifiers still apply. A speed-0 chain spell launches its targets in chain order (Spell::HandleLaunchPhase walks
// m_UniqueTargetInfo, filled in jump order), so a per-cast counter is the jump index.
class spell_dm_sneed_tazer : public SpellScript
{
    PrepareSpellScript(spell_dm_sneed_tazer);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        float const pct = TazerJumpPct(DeadminesKit::IsHeroicMap(caster), _jump++);
        SetEffectValue(static_cast<int32>(DeadminesKit::RefFlat(caster, pct)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_dm_sneed_tazer::SetDamage, EFFECT_0, SPELL_EFFECT_SCHOOL_DAMAGE);
    }

    std::size_t _jump = 0;
};

// 205253 Splinter Spray, the tank's hit: 30% of the tank reference row, Physical (armor applies). Set at launch so
// the tank's damage-taken modifiers (Shield Wall, Pain Suppression, ...) apply.
class spell_dm_sneed_splinter_tank : public SpellScript
{
    PrepareSpellScript(spell_dm_sneed_splinter_tank);

    void SetDamage(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        SetEffectValue(static_cast<int32>(DeadminesKit::RefFlat(caster,
            kSprayTankPct(DeadminesKit::IsHeroicMap(caster)), true)));
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_dm_sneed_splinter_tank::SetDamage, EFFECT_0,
            SPELL_EFFECT_SCHOOL_DAMAGE);
    }
};

namespace
{
    boss_sneeds_shredder_rework* ShredderAI(ChatHandler* handler)
    {
        Creature* shredder = DeadminesTest::FindBoss(handler, NPC_SNEEDS_SHREDDER);
        if (!shredder)
            return nullptr;
        auto* ai = dynamic_cast<boss_sneeds_shredder_rework*>(shredder->AI());
        if (!ai)
            handler->SendErrorMessage("Sneed's Shredder does not run boss_sneeds_shredder_rework.");
        return ai;
    }

    boss_sneed_rework* SneedAI(ChatHandler* handler)
    {
        Creature* sneed = DeadminesTest::FindBoss(handler, NPC_SNEED);
        if (!sneed)
            return nullptr;
        auto* ai = dynamic_cast<boss_sneed_rework*>(sneed->AI());
        if (!ai)
            handler->SendErrorMessage("Sneed does not run boss_sneed_rework.");
        return ai;
    }

    bool Done(ChatHandler* handler, bool ok, char const* what, char const* why)
    {
        if (ok)
            handler->PSendSysMessage("dmtest sneed: {} fired.", what);
        else
            handler->SendErrorMessage("dmtest sneed: {} not fired ({}).", what, why);
        return ok;
    }

    bool FireMalfunction(ChatHandler* handler, Malfunction m, char const* what)
    {
        boss_sneeds_shredder_rework* ai = ShredderAI(handler);
        return ai && Done(handler, ai->TestMalfunction(m, false), what, "the Shredder is a wreck");
    }

    // `.dmtest sneed info`
    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_SNEEDS_SHREDDER, BOSS_SNEED);
    }

    // `.dmtest sneed sawspin|spray|runaway`: one malfunction with its emote and cast bar (SN1-SN3).
    bool HandleSawSpin(ChatHandler* handler)
    {
        return FireMalfunction(handler, Malfunction::SawSpin, "Saw Spin (SN1)");
    }

    bool HandleSpray(ChatHandler* handler)
    {
        return FireMalfunction(handler, Malfunction::SplinterSpray, "Splinter Spray (SN2)");
    }

    bool HandleRunaway(ChatHandler* handler)
    {
        return FireMalfunction(handler, Malfunction::Runaway, "Runaway (SN3)");
    }

    // `.dmtest sneed haywire`: a full Haywire as the timer fires it (heroic: chained, SN4).
    bool HandleHaywire(ChatHandler* handler)
    {
        boss_sneeds_shredder_rework* ai = ShredderAI(handler);
        return ai && Done(handler, ai->TestHaywire(), "Haywire", "the Shredder is a wreck");
    }

    // `.dmtest sneed breakdown`: the Shredder breaks down now and ejects Sneed (in combat only).
    bool HandleBreakdown(ChatHandler* handler)
    {
        boss_sneeds_shredder_rework* ai = ShredderAI(handler);
        return ai && Done(handler, ai->TestBreakdown(false), "breakdown", "out of combat or already a wreck");
    }

    // `.dmtest sneed overload`: spends both reboots and breaks down: Wreck Overload (SN9), then Salvaged Saw (SN12).
    bool HandleOverload(ChatHandler* handler)
    {
        boss_sneeds_shredder_rework* ai = ShredderAI(handler);
        return ai && Done(handler, ai->TestBreakdown(true), "Wreck Overload", "out of combat or already a wreck");
    }

    bool FireSneed(ChatHandler* handler, Cast c, char const* what)
    {
        boss_sneed_rework* ai = SneedAI(handler);
        return ai && Done(handler, ai->TestCast(c), what, "Sneed is repairing, out of combat, or has no repairs left");
    }

    // `.dmtest sneed repairs|tazer|boomerang|bomb|saw`: one of Sneed's casts now (SN7, SN5, SN6, SN10, SN12).
    bool HandleRepairs(ChatHandler* handler)
    {
        return FireSneed(handler, Cast::RepairRun, "Emergency Repairs (SN7)");
    }

    bool HandleTazer(ChatHandler* handler)
    {
        return FireSneed(handler, Cast::Tazer, "Tazer (SN5)");
    }

    bool HandleBoomerang(ChatHandler* handler)
    {
        return FireSneed(handler, Cast::SawBoomerang, "Saw Boomerang (SN6)");
    }

    bool HandleBomb(ChatHandler* handler)
    {
        return FireSneed(handler, Cast::ClusterBomb, "Cluster Bomb (SN10, SN11)");
    }

    bool HandleSaw(ChatHandler* handler)
    {
        return FireSneed(handler, Cast::SawSpin, "Salvaged Saw (SN12)");
    }

    ChatCommandTable const& SneedTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",       HandleInfo,         SEC_GAMEMASTER, Console::No },
            { "sawspin",    HandleSawSpin,      SEC_GAMEMASTER, Console::No },
            { "spray",      HandleSpray,        SEC_GAMEMASTER, Console::No },
            { "runaway",    HandleRunaway,      SEC_GAMEMASTER, Console::No },
            { "haywire",    HandleHaywire,      SEC_GAMEMASTER, Console::No },
            { "breakdown",  HandleBreakdown,    SEC_GAMEMASTER, Console::No },
            { "overload",   HandleOverload,     SEC_GAMEMASTER, Console::No },
            { "repairs",    HandleRepairs,      SEC_GAMEMASTER, Console::No },
            { "tazer",      HandleTazer,        SEC_GAMEMASTER, Console::No },
            { "boomerang",  HandleBoomerang,    SEC_GAMEMASTER, Console::No },
            { "bomb",       HandleBomb,         SEC_GAMEMASTER, Console::No },
            { "saw",        HandleSaw,          SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_sneed_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_sneeds_shredder_rework);
    RegisterDeadminesReworkCreatureAI(boss_sneed_rework);
    RegisterSpellScript(spell_dm_sneed_tazer);
    RegisterSpellScript(spell_dm_sneed_splinter_tank);
    DeadminesTest::RegisterBoss("sneed", SneedTestCommands());
}
