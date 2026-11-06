/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * mod-dungeon-bosses, Deadmines: Mr. Smite (WP-B5). Build spec: DM 'Mr. Smite' Build spec SM1-SM13; handoff
 * deadmines-pilot.HANDOFF.md section 3.4 rows SM and section 3.5 row B5.
 *
 * The weapon swap (the stomp at 67% and 34%, the run to the chest, the kneel, the new weapon 1.5 s later, back in the
 * fight 3 s after the kneel) mirrors AzerothCore's stock boss_mr_smite.cpp (src/server/scripts/EasternKingdoms/
 * Deadmines/), which stays untouched and unbound: data binds entry 646 to this script instead. What changed: the
 * stomp's stun is cut to 2 s, the pull starts with the dual cutlasses, the hammer and the new harpoon come in a random
 * order, and every weapon brings two registry mechanics (mod-boss-mechanics), with a follow-up each on heroic.
 *
 *   SM1  Smite Stomp       stock 6432, its stun cut to 2 s per target (DeadminesKit::ShortenAura)
 *   SM2  Sweeping Slash    Frontal cone 90 / 8 yd, 2 s          SM3  Backswing (H): the same cone behind him, 1.5 s
 *                          both cones skip the tank (TankExempt); the tank in the arc takes 205303, 30% of the tank row
 *   SM4  Reckless Charge   line 3 yd to a non-tank, 2 s; H: a chain of 3, each from the last end, 1.5 s
 *   SM5  Hammer Drop       circle 6 yd on a non-tank, 2.5 s, he leaps there   SM6  debris (H): 3 x circle 4 yd, 2 s
 *   SM7  Shockwave         line 25 x 4 yd ahead, 2 s           SM8  aftershocks (H): +-30 degrees, 1.5 s
 *   SM9  Smite Slam        205298, a 1.5 s tank hit, no stun (stock 6435 is instant and stuns: see the DT file)
 *   SM10 Harpoon Sweep     donut 5 / 14 yd, 2 s                SM11 Haft Slam (H): circle 6 yd on him, 1.5 s
 *   SM12 Harpoon Volley    Spread 6 yd (H 8) on every non-tank, 2.5 s; each carrier takes 15% (RefFlat)
 *   SM13 Thrash            stock aura 3417 from creature_template_addon (untouched)
 *
 * Every mechanic firing logs one INFO line "dm-pilot smite <mechanic> ..." (module.dungeonbosses).
 */

#include "Chat.h"
#include "CreatureAIImpl.h"
#include "DeadminesKit.h"
#include "DeadminesTestCommand.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "MrSmiteLogic.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptedCreature.h"
#include "SpellInfo.h"
#include <array>
#include <functional>
#include <optional>
#include <string>
#include <vector>

using namespace Acore::ChatCommands;
using namespace DeadminesRework;
using namespace MrSmite;
using BossMechanics::MechanicRef;
using DeadminesKit::IsHeroicMap;

namespace
{
    char const* const kLogCategory = "module.dungeonbosses";

    std::size_t RandomIndex(std::size_t n)
    {
        return n ? static_cast<std::size_t>(urand(0, static_cast<uint32>(n - 1))) : 0;
    }

    Vec2 ToVec(Position const& p)
    {
        return { p.GetPositionX(), p.GetPositionY() };
    }

    char const* WeaponName(Weapon weapon)
    {
        switch (weapon)
        {
            case Weapon::Cutlasses:
                return "cutlasses";
            case Weapon::Hammer:
                return "hammer";
            case Weapon::Harpoon:
                return "harpoon";
        }
        return "?";
    }
}

// Mr. Smite 646
struct boss_mr_smite_rework : public BossAI
{
    enum SmiteEvents : uint32
    {
        EVENT_CHECK_HEALTH = 1,
        EVENT_SWEEPING_SLASH,
        EVENT_RECKLESS_CHARGE,
        EVENT_SMITE_SLAM,
        EVENT_HAMMER_DROP,
        EVENT_HAMMER_LEAP,
        EVENT_SHOCKWAVE,
        EVENT_HARPOON_SWEEP,
        EVENT_HARPOON_VOLLEY,
        EVENT_END_MANEUVER,     // a dash chain or a leap is over: back to the tank
        EVENT_RELEASE_HOLD,     // a heroic follow-up window is over
        EVENT_KNEEL_FALLBACK,   // the chest was never reached: kneel where he stands
        EVENT_SWAP_WEAPON,
        EVENT_RESTORE_COMBAT,
    };

    enum SmiteGroups : uint32
    {
        GROUP_WEAPON = 1,       // the current weapon's abilities and maneuvers (cancelled by a swap)
        GROUP_SWAP = 2,
    };

    enum SmitePoints : uint32
    {
        POINT_CHEST = 6460,
        POINT_LEAP = 6461,
    };

    explicit boss_mr_smite_rework(Creature* creature) : BossAI(creature, BOSS_MR_SMITE) { }

    void Reset() override
    {
        _Reset();
        ResetWeapons();
    }

    void JustEngagedWith(Unit* who) override
    {
        BossAI::JustEngagedWith(who);
        if (!me->IsEngaged())
            return;     // BossAI evaded (a required boss is not done)

        BossMechanics::EncounterOptions options;
        options.bossStateId = BOSS_MR_SMITE;
        Mechanic::BeginEncounter(me, options);

        // Boss data (build spec): kill order Smite; no interrupts, dispels or purges.
        BossMechanics::Descriptor descriptor;
        descriptor.targets.emplace_back(NPC_MR_SMITE, 0);
        Mechanic::Describe(me, std::move(descriptor));

        // a `.dmtest` swap or maneuver out of combat may have left a weapon or a state behind
        events.Reset();
        ResetWeapons();
        events.ScheduleEvent(EVENT_CHECK_HEALTH, Milliseconds(kHealthCheckMs));
        ScheduleWeapon(Weapon::Cutlasses);
        LOG_INFO(kLogCategory, "dm-pilot smite engage heroic={} order={},{},{}", IsHeroicMap(me),
            WeaponName(_order[0]), WeaponName(_order[1]), WeaponName(_order[2]));
    }

    void JustDied(Unit* killer) override
    {
        BossAI::JustDied(killer);
        CancelLive();
        LOG_INFO(kLogCategory, "dm-pilot smite death phase={}", _phase);
    }

    void SpellHitTarget(Unit* target, SpellInfo const* spell) override
    {
        // SM1: the stock 10 s stun becomes 2 s on every target (handoff section 7 #3: keep the stock id).
        if (spell && spell->Id == SPELL_SMITE_STOMP)
            DeadminesKit::ShortenAura(target, SPELL_SMITE_STOMP, me->GetGUID(), Milliseconds(kStompStunMs));
    }

    void MovementInform(uint32 type, uint32 point) override
    {
        if (type == POINT_MOTION_TYPE && point == POINT_CHEST && _swapping)
            Kneel();
    }

    void UpdateAI(uint32 diff) override
    {
        bool const engaged = UpdateVictim();
        // `.dmtest` can start a swap or a maneuver out of combat: keep its events running until it ends.
        if (!engaged && !_busy && !_swapping)
            return;

        events.Update(diff);
        if (me->IsActionPreventedByCasting())
            return;

        while (uint32 const eventId = events.ExecuteEvent())
        {
            ExecuteEvent(eventId);
            if (me->IsActionPreventedByCasting())
                return;
        }

        if (engaged && !me->HasUnitFlag(UNIT_FLAG_PACIFIED))
            DoMeleeAttackIfReady();
    }

    void ExecuteEvent(uint32 eventId) override
    {
        bool const heroic = IsHeroicMap(me);
        switch (eventId)
        {
            case EVENT_CHECK_HEALTH:
                if (!_swapping)
                    if (std::optional<std::size_t> swap = SwapDue(me->GetHealthPct(), _phase))
                        StartSwap(*swap, WeaponForPhase(_order, *swap + 1));
                events.ScheduleEvent(EVENT_CHECK_HEALTH, Milliseconds(kHealthCheckMs));
                break;
            case EVENT_SWEEPING_SLASH:
                if (RetryIfBusy(eventId))
                    break;
                SweepingSlash(heroic);
                events.ScheduleEvent(eventId, Milliseconds(kSlashEveryMs), GROUP_WEAPON);
                break;
            case EVENT_RECKLESS_CHARGE:
                if (RetryIfBusy(eventId))
                    break;
                RecklessCharge(heroic, false);
                events.ScheduleEvent(eventId, Milliseconds(kDashEveryMs), GROUP_WEAPON);
                break;
            case EVENT_SMITE_SLAM:
                if (RetryIfBusy(eventId))
                    break;
                SmiteSlam();
                events.ScheduleEvent(eventId, Milliseconds(kSlamEveryMs), GROUP_WEAPON);
                break;
            case EVENT_HAMMER_DROP:
                if (RetryIfBusy(eventId))
                    break;
                HammerDrop(heroic, false);
                events.ScheduleEvent(eventId, Milliseconds(kHammerDropEveryMs), GROUP_WEAPON);
                break;
            case EVENT_HAMMER_LEAP:
                Leap();
                break;
            case EVENT_SHOCKWAVE:
                if (RetryIfBusy(eventId))
                    break;
                Shockwave(heroic);
                events.ScheduleEvent(eventId, Milliseconds(kShockwaveEveryMs), GROUP_WEAPON);
                break;
            case EVENT_HARPOON_SWEEP:
                if (RetryIfBusy(eventId))
                    break;
                HarpoonSweep(heroic);
                events.ScheduleEvent(eventId, Milliseconds(kSweepEveryMs), GROUP_WEAPON);
                break;
            case EVENT_HARPOON_VOLLEY:
                if (RetryIfBusy(eventId))
                    break;
                HarpoonVolley(heroic, false);
                events.ScheduleEvent(eventId, Milliseconds(kVolleyEveryMs), GROUP_WEAPON);
                break;
            case EVENT_END_MANEUVER:
                EndManeuver();
                break;
            case EVENT_RELEASE_HOLD:
                _busy = false;
                break;
            case EVENT_KNEEL_FALLBACK:
                Kneel();
                break;
            case EVENT_SWAP_WEAPON:
                SwapWeapon();
                break;
            case EVENT_RESTORE_COMBAT:
                RestoreCombat();
                break;
            default:
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // SM1: the stomp and the weapon swap (stock boss_mr_smite's sequence)
    // ----------------------------------------------------------------------------------------------------------------

    void Stomp()
    {
        DoCastSelf(SPELL_SMITE_STOMP, true);
        LOG_INFO(kLogCategory, "dm-pilot smite stomp stun={}ms", kStompStunMs);
    }

    // Swap `index` (0 at 67%, 1 at 34%) to `weapon`.
    void StartSwap(std::size_t index, Weapon weapon)
    {
        _swapping = true;
        _kneeling = false;
        _busy = false;
        _nextWeapon = weapon;
        events.CancelEventGroup(GROUP_WEAPON);
        events.CancelEventGroup(GROUP_SWAP);
        CancelLive();
        me->InterruptNonMeleeSpells(false);

        Stomp();
        Talk(index == 0 ? SAY_SMITE_FIRST_SWAP : SAY_SMITE_SECOND_SWAP);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MovePoint(POINT_CHEST, kSmiteChest.x, kSmiteChest.y, kSmiteChestZ);
        me->SetUnitFlag(UNIT_FLAG_PACIFIED);
        me->SetReactState(REACT_PASSIVE);
        events.ScheduleEvent(EVENT_KNEEL_FALLBACK, Milliseconds(kSwapFallbackMs), GROUP_SWAP);
        LOG_INFO(kLogCategory, "dm-pilot smite weapon-swap swap={} health={:.1f}% to={}", index + 1,
            me->GetHealthPct(), WeaponName(weapon));
    }

    void Kneel()
    {
        if (!_swapping || _kneeling)
            return;
        _kneeling = true;
        events.CancelEvent(EVENT_KNEEL_FALLBACK);
        me->GetMotionMaster()->Clear();
        me->SetTarget();
        me->SetFacingTo(kChestFacing);
        if (me->GetVictim())
            me->SendMeleeAttackStop(me->GetVictim());
        me->SetStandState(UNIT_STAND_STATE_KNEEL);
        events.ScheduleEvent(EVENT_SWAP_WEAPON, Milliseconds(kSwapWeaponMs), GROUP_SWAP);
        events.ScheduleEvent(EVENT_RESTORE_COMBAT, Milliseconds(kSwapResumeMs), GROUP_SWAP);
    }

    void SwapWeapon()
    {
        me->LoadEquipment(static_cast<int8>(_nextWeapon), true);
        me->SetCanDualWield(false);
        Talk(_nextWeapon == Weapon::Hammer ? EMOTE_SMITE_HAMMER : EMOTE_SMITE_HARPOON);
    }

    void RestoreCombat()
    {
        _swapping = false;
        _kneeling = false;
        ++_phase;
        me->SetReactState(REACT_AGGRESSIVE);
        me->RemoveUnitFlag(UNIT_FLAG_PACIFIED);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        if (Unit* victim = me->GetVictim())
        {
            me->GetMotionMaster()->MoveChase(victim);
            me->SetTarget(victim->GetGUID());
        }
        if (me->IsEngaged())
            ScheduleWeapon(_nextWeapon);
        else
            me->GetMotionMaster()->MoveTargetedHome();
    }

    // The first casts of a weapon, from the pull (cutlasses) or from the resume (hammer, harpoon).
    void ScheduleWeapon(Weapon weapon)
    {
        switch (weapon)
        {
            case Weapon::Cutlasses:
                events.ScheduleEvent(EVENT_SWEEPING_SLASH, Milliseconds(kSlashFirstMs), GROUP_WEAPON);
                events.ScheduleEvent(EVENT_RECKLESS_CHARGE, Milliseconds(kDashFirstMs), GROUP_WEAPON);
                break;
            case Weapon::Hammer:
                events.ScheduleEvent(EVENT_SMITE_SLAM, Milliseconds(kSlamFirstMs), GROUP_WEAPON);
                events.ScheduleEvent(EVENT_HAMMER_DROP, Milliseconds(kHammerDropFirstMs), GROUP_WEAPON);
                events.ScheduleEvent(EVENT_SHOCKWAVE, Milliseconds(kShockwaveFirstMs), GROUP_WEAPON);
                break;
            case Weapon::Harpoon:
                events.ScheduleEvent(EVENT_HARPOON_SWEEP, Milliseconds(kSweepFirstMs), GROUP_WEAPON);
                events.ScheduleEvent(EVENT_HARPOON_VOLLEY, Milliseconds(kVolleyFirstMs), GROUP_WEAPON);
                break;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Cutlasses: SM2-SM4
    // ----------------------------------------------------------------------------------------------------------------

    void SweepingSlash(bool heroic)
    {
        FaceVictim();
        DeadminesKit::CastBar(me, SPELL_SMITE_SWEEPING_SLASH);
        MechanicRef ref = Mechanic::Cone(me, me, kSlashAngle, kSlashLength, Milliseconds(kSlashWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Damage(kSlashPct).TankDamage(kSlashPct).Weakened().Tag(TAG_SWEEPING_SLASH);
        bool const backswing = kBackswing(heroic);
        if (backswing)
            Hold(kSlashWarnMs + kFollowUpWarnMs);
        ref.OnResolve(OnSmite([backswing](boss_mr_smite_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.SlashTankHit(false);
            if (backswing)
                ai.Backswing();
        }));
        Track(ref.Handle());
        LOG_INFO(kLogCategory, "dm-pilot smite sweeping-slash heroic={}", heroic);
    }

    void Backswing()
    {
        DeadminesKit::CastBar(me, SPELL_SMITE_BACKSWING);
        MechanicRef ref = Mechanic::Cone(me, me, kSlashAngle, kSlashLength, Milliseconds(kFollowUpWarnMs),
            BossMechanics::TankExempt::Yes);
        ref.Rear().Damage(kSlashPct).TankDamage(kSlashPct).Weakened().Tag(TAG_BACKSWING);
        ref.OnResolve(OnSmite([](boss_mr_smite_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.SlashTankHit(true);
        }));
        Track(ref.Handle());
        LOG_INFO(kLogCategory, "dm-pilot smite backswing");
    }

    // SM2 / SM3: the TankExempt cone skipped the victim; it takes its own 30% of the tank row if it stands in the arc
    // (in front, or behind for Backswing). Base point 0 at cast keeps its damage-taken modifiers; armor applies.
    void SlashTankHit(bool rear)
    {
        Unit* tank = me->GetVictim();
        if (!tank || !tank->IsAlive())
            return;
        if (!InSlashArc(ToVec(me->GetPosition()), me->GetOrientation(), ToVec(tank->GetPosition()), rear,
            me->GetCombatReach() + tank->GetCombatReach()))
            return;
        int32 const damage = static_cast<int32>(DeadminesKit::RefFlat(me, kSlashPct, true));
        me->CastCustomSpell(SPELL_SMITE_SLASH_TANK, SPELLVALUE_BASE_POINT0, damage, tank, TRIGGERED_FULL_MASK);
        LOG_INFO(kLogCategory, "dm-pilot smite sweeping-slash-tank {} on {} damage={}", rear ? "backswing" : "front",
            tank->GetName(), damage);
    }

    // SM4: false when nobody can be dashed at.
    bool RecklessCharge(bool heroic, bool widen)
    {
        std::vector<Player*> const targets = NonTanks(widen);
        if (targets.empty())
        {
            LOG_INFO(kLogCategory, "dm-pilot smite reckless-charge skipped (no non-tank)");
            return false;
        }
        uint8 const dashes = kDashCount(heroic);
        _busy = true;
        events.ScheduleEvent(EVENT_END_MANEUVER, Milliseconds(DashChainMs(dashes) + 2 * kReturnDelayMs), GROUP_WEAPON);
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        DeadminesKit::CastBar(me, SPELL_SMITE_RECKLESS_CHARGE);
        if (!Dash(0, dashes, me->GetPosition(), {}, widen))
            EndManeuverSoon();
        return true;
    }

    // One dash of the chain: from `from` to a non-tank not yet in `chain`; on its resolve Smite charges along it and
    // the next dash (heroic) starts from its end.
    bool Dash(uint8 step, uint8 dashes, Position const& from, std::vector<uint64> chain, bool widen)
    {
        std::vector<Player*> const targets = NonTanks(widen);
        std::vector<Candidate> const candidates = ToCandidates(targets);
        std::optional<std::size_t> const pick = PickDashTarget(candidates, ToVec(from), chain, kDashMinDistance,
            RandomIndex);
        if (!pick)
            return false;

        Player* target = targets[*pick];
        Vec2 const end = DashEnd(ToVec(from), ToVec(target->GetPosition()), kDashMinDistance, me->GetOrientation());
        bool const onTarget = end.x == target->GetPositionX() && end.y == target->GetPositionY();
        Position const to(end.x, end.y, onTarget ? target->GetPositionZ() : from.GetPositionZ());
        chain.push_back(candidates[*pick].id);
        if (step == 0)
            me->SetFacingTo(from.GetAngle(&to));

        Milliseconds const warn(step == 0 ? kDashWarnMs : kDashFollowWarnMs);
        MechanicRef ref = Mechanic::Line(me, from, to, kDashWidth, warn);
        ref.ExcludeSourceEnd(kDashExclude).Damage(kDashPct).Weakened().Tag(TAG_RECKLESS_CHARGE);
        ref.OnResolve(OnSmite([to, step, dashes, chain, widen](boss_mr_smite_rework& ai,
            BossMechanics::ResolveResult const&)
        {
            ai.DashResolved(to, step, dashes, chain, widen);
        }));
        Track(ref.Handle());
        LOG_INFO(kLogCategory, "dm-pilot smite reckless-charge dash={}/{} target={} length={:.1f}", step + 1, dashes,
            target->GetName(), from.GetExactDist2d(to.GetPositionX(), to.GetPositionY()));
        return true;
    }

    void DashResolved(Position const& to, uint8 step, uint8 dashes, std::vector<uint64> const& chain, bool widen)
    {
        me->GetMotionMaster()->MoveCharge(to.GetPositionX(), to.GetPositionY(), to.GetPositionZ(), kDashSpeed,
            EVENT_CHARGE, nullptr, true);
        if (step + 1 < dashes && Dash(step + 1, dashes, to, chain, widen))
            return;
        EndManeuverSoon();
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Hammer: SM5-SM9
    // ----------------------------------------------------------------------------------------------------------------

    bool HammerDrop(bool heroic, bool widen)
    {
        std::vector<Player*> const targets = NonTanks(widen);
        std::vector<Candidate> const candidates = ToCandidates(targets);
        std::optional<std::size_t> const pick = PickLeapTarget(candidates, ToVec(me->GetPosition()),
            kHammerDropMinDistance, RandomIndex);
        if (!pick)
        {
            LOG_INFO(kLogCategory, "dm-pilot smite hammer-drop skipped (no non-tank)");
            return false;
        }

        Player* target = targets[*pick];
        _leapTo = target->GetPosition();
        uint64 const targetId = candidates[*pick].id;
        _busy = true;
        me->GetMotionMaster()->Clear();
        me->GetMotionMaster()->MoveIdle();
        me->SetFacingToObject(target);
        DeadminesKit::CastBar(me, SPELL_SMITE_HAMMER_DROP);
        events.ScheduleEvent(EVENT_HAMMER_LEAP, Milliseconds(kHammerDropCastMs), GROUP_WEAPON);
        events.ScheduleEvent(EVENT_END_MANEUVER, Milliseconds(kHammerDropWarnMs + 2 * kReturnDelayMs), GROUP_WEAPON);

        Position const at = _leapTo;
        MechanicRef ref = Mechanic::Circle(me, at, kHammerDropRadius, Milliseconds(kHammerDropWarnMs));
        ref.Damage(kHammerDropPct).Weakened().Tag(TAG_HAMMER_DROP);
        ref.OnResolve(OnSmite([targetId, heroic, widen](boss_mr_smite_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.HammerLanded(targetId, heroic, widen);
        }));
        Track(ref.Handle());
        LOG_INFO(kLogCategory, "dm-pilot smite hammer-drop target={} distance={:.1f}", target->GetName(),
            me->GetExactDist2d(target));
        return true;
    }

    void Leap()
    {
        float const distance = me->GetExactDist2d(_leapTo.GetPositionX(), _leapTo.GetPositionY());
        // one second in the air, whatever the distance
        float const speed = std::max(kHammerLeapMinSpeed, distance);
        me->GetMotionMaster()->MoveJump(_leapTo, speed, kHammerLeapSpeedZ, POINT_LEAP);
    }

    void HammerLanded(uint64 targetId, bool heroic, bool widen)
    {
        DoCastSelf(SPELL_SMITE_HAMMER_LANDING, true);
        uint8 const debris = kDebrisCount(heroic);
        if (debris)
        {
            std::vector<Player*> const targets = NonTanks(widen);
            std::vector<Candidate> const candidates = ToCandidates(targets);
            std::vector<std::size_t> const picks = PickOthers(candidates, targetId, debris, RandomIndex);
            for (std::size_t i : picks)
            {
                Position const at = targets[i]->GetPosition();
                MechanicRef ref = Mechanic::Circle(me, at, kDebrisRadius, Milliseconds(kDebrisWarnMs));
                ref.Damage(kDebrisPct).Weakened().Tag(TAG_DEBRIS);
                ref.OnResolve(OnSmite([at](boss_mr_smite_rework& ai, BossMechanics::ResolveResult const&)
                {
                    ai.me->CastSpell(at.GetPositionX(), at.GetPositionY(), at.GetPositionZ(), SPELL_SMITE_DEBRIS,
                        true);
                }));
                Track(ref.Handle());
            }
            LOG_INFO(kLogCategory, "dm-pilot smite debris circles={}", picks.size());
        }
        EndManeuverSoon();
    }

    void Shockwave(bool heroic)
    {
        FaceVictim();
        Position const from = me->GetPosition();
        float const facing = me->GetOrientation();
        DeadminesKit::CastBar(me, SPELL_SMITE_SHOCKWAVE);
        MechanicRef ref = Mechanic::Line(me, from, facing, kShockwaveLength, kShockwaveWidth,
            Milliseconds(kShockwaveWarnMs));
        ref.TankExempt().Damage(kShockwavePct).Weakened().Tag(TAG_SHOCKWAVE);
        if (kAftershocks(heroic))
        {
            Hold(kShockwaveWarnMs + kFollowUpWarnMs);
            ref.OnResolve(OnSmite([from, facing](boss_mr_smite_rework& ai, BossMechanics::ResolveResult const&)
            {
                ai.Aftershocks(from, facing);
            }));
        }
        Track(ref.Handle());
        LOG_INFO(kLogCategory, "dm-pilot smite shockwave heroic={} facing={:.2f}", heroic, facing);
    }

    void Aftershocks(Position const& from, float facing)
    {
        DeadminesKit::CastBar(me, SPELL_SMITE_AFTERSHOCKS);
        for (float offset : { kAftershockOffsetDeg, -kAftershockOffsetDeg })
            Track(Mechanic::Line(me, from, facing, kShockwaveLength, kShockwaveWidth, Milliseconds(kFollowUpWarnMs))
                .FacingOffset(offset).TankExempt().Damage(kShockwavePct).Weakened().Tag(TAG_AFTERSHOCKS));
        LOG_INFO(kLogCategory, "dm-pilot smite aftershocks lines=2");
    }

    // SM9: the 205298 copy (no stun, 1.5 s cast), its damage the tank row's share of stock 6435.
    bool SmiteSlam()
    {
        Unit* victim = me->GetVictim();
        if (!victim)
            return false;
        int32 const damage = static_cast<int32>(DeadminesKit::RefFlat(me, kSlamTankPct, true));
        me->CastCustomSpell(SPELL_SMITE_SLAM_NO_STUN, SPELLVALUE_BASE_POINT0, damage, victim, TRIGGERED_NONE);
        LOG_INFO(kLogCategory, "dm-pilot smite smite-slam target={} damage={}", victim->GetName(), damage);
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Harpoon: SM10-SM12
    // ----------------------------------------------------------------------------------------------------------------

    void HarpoonSweep(bool heroic)
    {
        DeadminesKit::CastBar(me, SPELL_SMITE_HARPOON_SWEEP);
        MechanicRef ref = Mechanic::Donut(me, me, kSweepInner, kSweepOuter, Milliseconds(kSweepWarnMs));
        ref.Damage(kSweepPct).Weakened().Tag(TAG_HARPOON_SWEEP);
        if (kHaftSlam(heroic))
        {
            Hold(kSweepWarnMs + kFollowUpWarnMs);
            ref.OnResolve(OnSmite([](boss_mr_smite_rework& ai, BossMechanics::ResolveResult const&)
            {
                ai.HaftSlam();
            }));
        }
        Track(ref.Handle());
        LOG_INFO(kLogCategory, "dm-pilot smite harpoon-sweep heroic={}", heroic);
    }

    void HaftSlam()
    {
        DeadminesKit::CastBar(me, SPELL_SMITE_HAFT_SLAM);
        Track(Mechanic::Circle(me, me, kHaftSlamRadius, Milliseconds(kFollowUpWarnMs)).Damage(kHaftSlamPct)
            .Weakened().Tag(TAG_HAFT_SLAM));
        LOG_INFO(kLogCategory, "dm-pilot smite haft-slam");
    }

    // The carriers are fixed at registration (the non-tanks then; `widen`: everyone when nobody else is there) and
    // passed as Targets, so the splash keeps Role::Any eligibility and hits anyone else in range, the tank included
    // (DM SM12), and the carriers' own 15% goes to exactly the players who wore the marker.
    void HarpoonVolley(bool heroic, bool widen)
    {
        float const radius = kVolleyRadius(heroic);
        GuidSet carriers;
        for (Player* p : NonTanks(widen))
            carriers.insert(p->GetGUID());
        if (carriers.empty())
        {
            LOG_INFO(kLogCategory, "dm-pilot smite harpoon-volley skipped (no non-tank to carry)");
            return;
        }
        DeadminesKit::CastBar(me, SPELL_SMITE_HARPOON_VOLLEY);
        MechanicRef ref = Mechanic::Spread(me, radius, Milliseconds(kVolleyWarnMs));
        ref.Targets(carriers).Damage(kVolleySplashPct).Weakened().Tag(TAG_HARPOON_VOLLEY);
        ref.OnResolve(OnSmite([carriers](boss_mr_smite_rework& ai, BossMechanics::ResolveResult const&)
        {
            ai.VolleyLanded(carriers);
        }));
        Track(ref.Handle());
        LOG_INFO(kLogCategory, "dm-pilot smite harpoon-volley radius={:.0f} carriers={}", radius, carriers.size());
    }

    // The carriers' own hits: 15% each, unavoidable (no Weakened), through the 205302 copy; the registration's set.
    void VolleyLanded(GuidSet const& carriers)
    {
        int32 const damage = static_cast<int32>(DeadminesKit::RefFlat(me, kVolleyCarrierPct));
        std::size_t hit = 0;
        for (ObjectGuid const& guid : carriers)
        {
            Player* carrier = ObjectAccessor::GetPlayer(*me, guid);
            if (!carrier || !carrier->IsAlive() || carrier->GetMap() != me->GetMap())
                continue;
            me->CastCustomSpell(SPELL_SMITE_HARPOON_IMPACT, SPELLVALUE_BASE_POINT0, damage, carrier,
                TRIGGERED_FULL_MASK);
            ++hit;
        }
        LOG_INFO(kLogCategory, "dm-pilot smite harpoon-impact carriers={} damage={}", hit, damage);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // `.dmtest smite` entry points (one mechanic on demand; `heroic` forces the follow-ups on a normal map)
    // ----------------------------------------------------------------------------------------------------------------

    enum class TestMechanic : uint8
    {
        Slash,
        Charge,
        Drop,
        Shockwave,
        Slam,
        Sweep,
        Volley,
    };

    // An empty string when fired; otherwise why not.
    std::string TestFire(TestMechanic mechanic, bool heroic)
    {
        if (_swapping || _busy || me->IsNonMeleeSpellCast(false))
            return "Mr. Smite is busy (swapping, dashing, leaping or casting); try again in a few seconds.";
        switch (mechanic)
        {
            case TestMechanic::Slash:
                SweepingSlash(heroic);
                break;
            case TestMechanic::Charge:
                if (!RecklessCharge(heroic, true))
                    return "No player to dash at (.gm off, alive, within 100 yd).";
                break;
            case TestMechanic::Drop:
                if (!HammerDrop(heroic, true))
                    return "No player to leap at (.gm off, alive, within 100 yd).";
                break;
            case TestMechanic::Shockwave:
                Shockwave(heroic);
                break;
            case TestMechanic::Slam:
                if (!SmiteSlam())
                    return "Smite Slam needs a victim: pull him first.";
                break;
            case TestMechanic::Sweep:
                HarpoonSweep(heroic);
                break;
            case TestMechanic::Volley:
                HarpoonVolley(heroic, true);
                break;
        }
        return {};
    }

    bool HeroicMap() const
    {
        return IsHeroicMap(me);
    }

    std::string TestStomp()
    {
        Stomp();
        return {};
    }

    // The next swap (or the weapon given), with the stomp and the chest run.
    std::string TestSwap(std::optional<uint32> weapon)
    {
        if (_swapping)
            return "Mr. Smite is already swapping.";
        Weapon next = WeaponForPhase(_order, _phase + 1);
        if (weapon)
        {
            if (*weapon < static_cast<uint32>(Weapon::Cutlasses) || *weapon > static_cast<uint32>(Weapon::Harpoon))
                return "Weapon must be 2 (cutlasses), 3 (hammer) or 4 (harpoon).";
            next = static_cast<Weapon>(*weapon);
        }
        StartSwap(std::min<std::size_t>(_phase, 1), next);
        return {};
    }

private:
    // The pull's state: the cutlasses, a new weapon order, nothing pending (stock Reset, with the cutlasses).
    void ResetWeapons()
    {
        CancelLive();
        _phase = 0;
        _swapping = false;
        _kneeling = false;
        _busy = false;
        _order = WeaponOrder(urand(0, 1) == 0);
        _nextWeapon = _order[1];
        me->LoadEquipment(static_cast<int8>(Weapon::Cutlasses), true);
        me->SetCanDualWield(true);
        me->SetStandState(UNIT_STAND_STATE_STAND);
        me->RemoveUnitFlag(UNIT_FLAG_PACIFIED);
        me->SetReactState(REACT_AGGRESSIVE);
    }

    // Runs `fn(ai, result)` on this boss when a mechanic resolves, if it is still there. Captures the map and the guid
    // only (a lambda the registry keeps must not hold a Unit*; STAGE-M5-R-REPORT m-4).
    template <typename Fn>
    std::function<void(BossMechanics::ResolveResult const&)> OnSmite(Fn fn)
    {
        Map* map = me->GetMap();
        ObjectGuid const guid = me->GetGUID();
        return [map, guid, fn](BossMechanics::ResolveResult const& result)
        {
            if (result.fizzled || !map)
                return;
            Creature* smite = map->GetCreature(guid);
            if (!smite || !smite->IsAlive() || !smite->IsAIEnabled)
                return;
            if (auto* ai = dynamic_cast<boss_mr_smite_rework*>(smite->AI()))
                fn(*ai, result);
        };
    }

    // Players the picks may choose: alive, not GMs, within 100 yd, and not the tank (the registry's role provider:
    // with a victim, the victim is the tank). `widen` (`.dmtest`): everyone, when nobody but a tank is there.
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

    static std::vector<Candidate> ToCandidates(std::vector<Player*> const& players)
    {
        std::vector<Candidate> out;
        out.reserve(players.size());
        for (Player const* player : players)
            out.push_back({ player->GetGUID().GetRawValue(), ToVec(player->GetPosition()) });
        return out;
    }

    void FaceVictim()
    {
        if (Unit* victim = me->GetVictim())
            me->SetFacingToObject(victim);
    }

    // Nothing new starts while a heroic follow-up is pending (its cast bar would fail on a running cast).
    void Hold(uint32 ms)
    {
        _busy = true;
        events.ScheduleEvent(EVENT_RELEASE_HOLD, Milliseconds(ms), GROUP_WEAPON);
    }

    bool RetryIfBusy(uint32 eventId)
    {
        if (!_busy)
            return false;
        events.ScheduleEvent(eventId, Milliseconds(kBusyRetryMs), GROUP_WEAPON);
        return true;
    }

    void EndManeuverSoon()
    {
        events.RescheduleEvent(EVENT_END_MANEUVER, Milliseconds(kReturnDelayMs), GROUP_WEAPON);
    }

    void EndManeuver()
    {
        _busy = false;
        me->GetMotionMaster()->Clear();
        if (Unit* victim = me->GetVictim())
            me->GetMotionMaster()->MoveChase(victim);
        else if (!me->IsEngaged())
            me->GetMotionMaster()->MoveTargetedHome();
    }

    void Track(BossMechanics::MechanicHandle handle)
    {
        if (handle)
            _live.push_back(handle);
    }

    // A swap or a reset drops every mechanic still warning (their follow-ups never run: a cancelled mechanic never
    // resolves).
    void CancelLive()
    {
        for (BossMechanics::MechanicHandle const& handle : _live)
            Mechanic::Cancel(me, handle);
        _live.clear();
    }

    std::array<Weapon, kWeaponCount> _order = WeaponOrder(true);
    Weapon _nextWeapon = Weapon::Hammer;
    std::size_t _phase = 0;
    bool _swapping = false;
    bool _kneeling = false;
    bool _busy = false;
    Position _leapTo;
    std::vector<BossMechanics::MechanicHandle> _live;
};

namespace
{
    boss_mr_smite_rework* FindSmiteAI(ChatHandler* handler)
    {
        Creature* smite = DeadminesTest::FindBoss(handler, NPC_MR_SMITE);
        if (!smite)
            return nullptr;
        auto* ai = smite->IsAIEnabled ? dynamic_cast<boss_mr_smite_rework*>(smite->AI()) : nullptr;
        if (!ai)
            handler->SendErrorMessage("{}", "Mr. Smite is not running boss_mr_smite_rework (check the ScriptName).");
        return ai;
    }

    bool Report(ChatHandler* handler, std::string const& error, char const* what)
    {
        if (!error.empty())
        {
            handler->SendErrorMessage("{}", error);
            return false;
        }
        handler->PSendSysMessage("Mr. Smite: {} fired.", what);
        return true;
    }

    bool Fire(ChatHandler* handler, boss_mr_smite_rework::TestMechanic mechanic, Optional<uint32> heroic,
        char const* what)
    {
        boss_mr_smite_rework* ai = FindSmiteAI(handler);
        if (!ai)
            return false;
        bool const isHeroic = heroic ? *heroic != 0 : ai->HeroicMap();
        return Report(handler, ai->TestFire(mechanic, isHeroic), what);
    }

    bool HandleInfo(ChatHandler* handler)
    {
        return DeadminesTest::ShowBossInfo(handler, NPC_MR_SMITE, BOSS_MR_SMITE);
    }

    bool HandleStomp(ChatHandler* handler)
    {
        boss_mr_smite_rework* ai = FindSmiteAI(handler);
        return ai && Report(handler, ai->TestStomp(), "Smite Stomp (SM1)");
    }

    bool HandleSwap(ChatHandler* handler, Optional<uint32> weapon)
    {
        boss_mr_smite_rework* ai = FindSmiteAI(handler);
        return ai && Report(handler, ai->TestSwap(weapon), "the weapon swap (SM1)");
    }

    bool HandleSlash(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_mr_smite_rework::TestMechanic::Slash, heroic, "Sweeping Slash (SM2/SM3)");
    }

    bool HandleCharge(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_mr_smite_rework::TestMechanic::Charge, heroic, "Reckless Charge (SM4)");
    }

    bool HandleDrop(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_mr_smite_rework::TestMechanic::Drop, heroic, "Hammer Drop (SM5/SM6)");
    }

    bool HandleShockwave(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_mr_smite_rework::TestMechanic::Shockwave, heroic, "Shockwave (SM7/SM8)");
    }

    bool HandleSlam(ChatHandler* handler)
    {
        return Fire(handler, boss_mr_smite_rework::TestMechanic::Slam, {}, "Smite Slam (SM9)");
    }

    bool HandleSweep(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_mr_smite_rework::TestMechanic::Sweep, heroic, "Harpoon Sweep (SM10/SM11)");
    }

    bool HandleVolley(ChatHandler* handler, Optional<uint32> heroic)
    {
        return Fire(handler, boss_mr_smite_rework::TestMechanic::Volley, heroic, "Harpoon Volley (SM12)");
    }

    // `.dmtest smite <sub> [1]`: the optional 1 forces the heroic follow-up (0 forces normal); default: the map's.
    ChatCommandTable const& MrSmiteTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info",      HandleInfo,      SEC_GAMEMASTER, Console::No },
            { "stomp",     HandleStomp,     SEC_GAMEMASTER, Console::No },
            { "swap",      HandleSwap,      SEC_GAMEMASTER, Console::No },
            { "slash",     HandleSlash,     SEC_GAMEMASTER, Console::No },
            { "charge",    HandleCharge,    SEC_GAMEMASTER, Console::No },
            { "drop",      HandleDrop,      SEC_GAMEMASTER, Console::No },
            { "shockwave", HandleShockwave, SEC_GAMEMASTER, Console::No },
            { "slam",      HandleSlam,      SEC_GAMEMASTER, Console::No },
            { "sweep",     HandleSweep,     SEC_GAMEMASTER, Console::No },
            { "volley",    HandleVolley,    SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_boss_mr_smite_rework()
{
    RegisterDeadminesReworkCreatureAI(boss_mr_smite_rework);
    DeadminesTest::RegisterBoss("smite", MrSmiteTestCommands());
}
