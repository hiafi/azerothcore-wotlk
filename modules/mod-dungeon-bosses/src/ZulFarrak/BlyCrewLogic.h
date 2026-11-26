/*
 * mod-dungeon-bosses, Zul'Farrak CR: Sergeant Bly's crew, the pure, host-testable part (no engine headers). WP-CR
 * owns this file (handoff section 3.12; .agents/plans/zul-farrak-build/zul-farrak-build.STAGE-CR-REPORT.md section 1
 * is the interface the other WPs plug into). The modes, the mask, the paths and the crew's stock points are
 * ZulFarrakRework.h's; this header adds what the crew AI decides with them:
 *
 *   FactionFor / FightsIn / GossipIn   what each CrewMode looks like (section 3.12: 35 caged, 495 ally, 41 hostile,
 *                                      35 pool ally)
 *   CrewSpot / RestSpotFor / SpotPoint where a member stands in a mode (cage, stair, descent, gather, pool)
 *   kCrewPoolSpots                     the crew's waiting spots on the shore (the Test path, before Velratha's pull)
 *   PrisonerNext                       the Block's prisoner machine (D4a): torn, chained, returned, executed
 *   DoorWalkNext                       Weegli's End Door walk (section 7 #13 A, #14 A)
 *   FlooredDamage / WeegliFloorHolds   Weegli's 1 health floor until the pool; the Test's 30% yield floor
 *   PickHealTarget / MurtaSpellFor     Murta's script healing (the stock Renew, Shield and Heal at percent values)
 *   AllArrived                         the five at the pool (SetData(DATA_CREW_AT_POOL, 1))
 *   Tune                               every number of the crew module (rule 32)
 *
 * Mirrored stock behavior (AGENTS.md credit rule): the stair, descent and gather walks, Bly's betrayal lines and
 * gossip gates, Weegli's door walk (spot, plant, escape path) and the stock kits' timers are re-implemented from
 * src/server/scripts/Kalimdor/ZulFarrak/zulfarrak.cpp and instance_zulfarrak.cpp (c9315e3ec moostigre
 * <moostigre@proton.me>; 048025ceb UltraNix <80540499+UltraNix@users.noreply.github.com>) and the dropped SmartAI rows
 * of 7605, 7606 and 7608.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_BLY_CREW_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_BLY_CREW_LOGIC_H

#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ZfCrew
{
    using ZulFarrakRework::CrewMode;
    using ZulFarrakRework::Point3;

    // Every ally-kit spell of CR sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`). The
    // built kits cast stock spells with script values, so the slice holds no row yet.
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsCrewAlly;

    // ----------------------------------------------------------------------------------------------------------------
    // Stock spells the crew cast (kept as cast; the heals carry script values) [verified: Spell.dbc; the SmartAI rows
    // of 7605, 7606 and 7608 before the S0 rev; zulfarrak.cpp]
    // ----------------------------------------------------------------------------------------------------------------
    enum CrewSpells : std::uint32_t
    {
        SPELL_SHIELD_BASH       = 11972,    // Bly
        SPELL_REVENGE           = 12170,    // Bly
        SPELL_DUAL_WIELD        = 29651,    // Raven (the stock reset event)
        SPELL_GOUGE             = 12540,    // Raven
        SPELL_BACKSTAB          = 7159,     // Raven, from behind
        SPELL_SHADOW_BOLT       = 9613,     // Oro
        SPELL_RAIN_OF_FIRE      = 11990,    // Oro
        SPELL_IMMOLATE          = 11962,    // Oro
        SPELL_CURSE_OF_WEAKNESS = 12741,    // Oro
        SPELL_HOLY_SMITE        = 9734,     // Murta
        SPELL_RENEW             = 11640,    // Murta: periodic heal, effect 0 = the tick (script value)
        SPELL_PW_SHIELD         = 11974,    // Murta: absorb, effect 0 = the shield (script value)
        SPELL_HEAL              = 11642,    // Murta: effect 0 = the heal (script value)
        SPELL_BANDS_ESCAPE      = 11365,    // Bly's Band's Escape: a 10 s self dummy (the crew's departure look)
        SPELL_WEEGLIS_BARREL    = 10772,    // Plant explosives: summons GO 141612 (its SmartAI dropped by the S0 rev)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Factions and react state by mode (section 3.12)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kFactionCaged = 35;     // friendly to all: nobody attacks a caged, gathered or yielded one
    std::uint32_t constexpr kFactionAlly = 495;     // FACTION_ESCORTEE_N_FRIEND_ACTIVE (the stock cage script's)
    std::uint32_t constexpr kFactionHostile = 41;   // stock FACTION_BLY_HOSTILE
    std::uint32_t constexpr kFactionPoolAlly = 35;  // the pool: no trash attacks them; D7Ha scripts the rest

    constexpr std::uint32_t FactionFor(CrewMode mode)
    {
        switch (mode)
        {
            case CrewMode::Ally:
                return kFactionAlly;
            case CrewMode::Boss:
                return kFactionHostile;
            case CrewMode::PoolAlly:
                return kFactionPoolAlly;
            default:
                return kFactionCaged;   // Caged, Prisoner, Gather, Yielded, Gone
        }
    }

    // Whether the mode fights on its own (REACT_AGGRESSIVE); every other mode is passive. PoolAlly is passive: at the
    // pool the crew act through D7Ha's handler (their damage and healing there are script, rule 29).
    constexpr bool FightsIn(CrewMode mode)
    {
        return mode == CrewMode::Ally || mode == CrewMode::Boss;
    }

    // Whether the member shows a gossip menu: Bly (his paths) and Weegli (his stock lines) until the fight; the others
    // never.
    constexpr bool GossipIn(std::uint32_t member, CrewMode mode)
    {
        if (member != ZulFarrakRework::CREW_BLY && member != ZulFarrakRework::CREW_WEEGLI)
            return false;
        return mode == CrewMode::Caged || mode == CrewMode::Ally || mode == CrewMode::Gather;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Where a member stands (the walks of the stock instance, by mode and stage)
    // ----------------------------------------------------------------------------------------------------------------
    enum class CrewSpot : std::uint8_t
    {
        None    = 0,    // the mode places nobody (Prisoner: the chain; Gone: the door or away)
        Cage    = 1,    // kCrewSpawns (in the cages)
        Stair   = 2,    // kCrewStairPoints (the landing, stage 2)
        Descent = 3,    // kCrewDescentPoints (the stair foot, stage 3)
        Gather  = 4,    // kCrewGatherPoints (the plaza, Bly's gossip; Boss and Yielded go home here)
        Pool    = 5,    // kCrewPoolSpots (the shore, the Test path)
    };
    std::uint32_t constexpr kCrewSpotCount = 6;
    inline std::array<char const*, kCrewSpotCount> constexpr kCrewSpotNames{ {
        "none", "cage", "stair", "descent", "gather", "pool",
    } };

    // The rest spot of a mode. Ally follows the stage: the stair while stage 2 is in play (running or waiting for the
    // landing), the stair's foot from stage 3 on.
    constexpr CrewSpot RestSpotFor(CrewMode mode, std::uint32_t pyramidStage)
    {
        switch (mode)
        {
            case CrewMode::Caged:
                return CrewSpot::Cage;
            case CrewMode::Ally:
                return pyramidStage >= ZulFarrakRework::PYRAMID_STAGE_ALTAR ? CrewSpot::Descent : CrewSpot::Stair;
            case CrewMode::Gather:
            case CrewMode::Boss:
            case CrewMode::Yielded:
                return CrewSpot::Gather;
            case CrewMode::PoolAlly:
                return CrewSpot::Pool;
            default:
                return CrewSpot::None;
        }
    }

    // The crew's waiting spots at the pool: an arc of r 4 on the shore's widest open disc (1706, 1235), r 27.2
    // [navmesh estimate, NAVMESH-REPORT, the pool], 25 yd from Velratha's spawn, facing her. By CrewMember. z is the
    // disc's; the AI drops it to the ground when it places a member there.
    Point3 constexpr kPoolWaitCenter{ 1706.0f, 1235.0f, 9.5f };
    inline std::array<Point3, ZulFarrakRework::kCrewCount> constexpr kCrewPoolSpots{ {
        { 1702.0f, 1235.0f, 9.5f, 4.35f }, { 1703.2f, 1238.0f, 9.5f, 4.35f }, { 1706.0f, 1239.0f, 9.5f, 4.35f },
        { 1708.8f, 1238.0f, 9.5f, 4.35f }, { 1710.0f, 1235.0f, 9.5f, 4.35f },
    } };

    // The point of `spot` for `member` (a zero point for None or a bad member).
    constexpr Point3 SpotPoint(CrewSpot spot, std::uint32_t member)
    {
        if (member >= ZulFarrakRework::kCrewCount)
            return {};
        switch (spot)
        {
            case CrewSpot::Cage:
                return ZulFarrakRework::kCrewSpawns[member];
            case CrewSpot::Stair:
                return ZulFarrakRework::kCrewStairPoints[member];
            case CrewSpot::Descent:
                return ZulFarrakRework::kCrewDescentPoints[member];
            case CrewSpot::Gather:
                return ZulFarrakRework::kCrewGatherPoints[member];
            case CrewSpot::Pool:
                return kCrewPoolSpots[member];
            default:
                return {};
        }
    }

    // How a member reaches a spot in play (after a create, a respawn or a reload it is placed: a teleport). Into a
    // cage it jumps (the cage is a closed door); to the pool it leaves with Band's Escape and appears there (the
    // shore is 400 yd and a city of trash away: no walk); everything else walks as stock.
    enum class SpotTravel : std::uint8_t
    {
        Walk,
        Jump,
        Depart,
    };

    constexpr SpotTravel TravelTo(CrewSpot spot)
    {
        switch (spot)
        {
            case CrewSpot::Cage:
                return SpotTravel::Jump;
            case CrewSpot::Pool:
                return SpotTravel::Depart;
            default:
                return SpotTravel::Walk;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Block's prisoner (D4a, PY1): torn from the cage, chained at the Executioner's feet, then returned (soaked) or
    // executed (not). Weegli is never taken.
    // ----------------------------------------------------------------------------------------------------------------
    enum class PrisonerState : std::uint8_t
    {
        Free        = 0,    // in the cage (or not on the Block at all)
        Torn        = 1,    // on the way to the chain spot (a jump)
        Chained     = 2,    // rooted and kneeling at the chain spot: the Behead's target
        Returning   = 3,    // soaked: jumping back to the cage
        Executed    = 4,    // killed by the Behead (the instance counts the Offering or the Blood Price)
    };
    inline std::array<char const*, 5> constexpr kPrisonerStateNames{ {
        "free", "torn", "chained", "returning", "executed",
    } };

    enum class PrisonerEvent : std::uint8_t
    {
        Take,       // D4a picks the prisoner (TakePrisoner)
        Arrived,    // the jump to the chain spot landed (or its timeout)
        Spare,      // D4a: the axe was soaked (SparePrisoner)
        Home,       // the jump back to the cage landed (or its timeout)
        Execute,    // D4a: the axe was not soaked (ExecutePrisoner)
        Reset,      // a wipe, a win, a death, a respawn, the mode left Prisoner
    };

    // The next state, or the same one when the event does not apply (the caller refuses the request).
    constexpr PrisonerState PrisonerNext(PrisonerState s, PrisonerEvent e)
    {
        switch (e)
        {
            case PrisonerEvent::Take:
                return s == PrisonerState::Free ? PrisonerState::Torn : s;
            case PrisonerEvent::Arrived:
                return s == PrisonerState::Torn ? PrisonerState::Chained : s;
            case PrisonerEvent::Spare:
                return (s == PrisonerState::Torn || s == PrisonerState::Chained) ? PrisonerState::Returning : s;
            case PrisonerEvent::Home:
                return s == PrisonerState::Returning ? PrisonerState::Free : s;
            case PrisonerEvent::Execute:
                return (s == PrisonerState::Torn || s == PrisonerState::Chained) ? PrisonerState::Executed : s;
            case PrisonerEvent::Reset:
                return PrisonerState::Free;
            default:
                return s;
        }
    }

    // A crew member D4a may take now: a fighter (never Weegli), alive, Caged, not already a prisoner.
    constexpr bool PrisonerEligible(std::uint32_t member, bool alive, CrewMode mode, PrisonerState state)
    {
        return member < ZulFarrakRework::kCrewCount && member != ZulFarrakRework::CREW_WEEGLI && alive
            && mode == CrewMode::Caged && state == PrisonerState::Free;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Weegli's End Door walk (section 7 #13 A, #14 A): on the betrayal he runs to the door when the fight starts and
    // lights it when the fight ends; on the Test he goes after the last yield, lights it, then goes to the pool.
    // ----------------------------------------------------------------------------------------------------------------
    enum class DoorWalk : std::uint8_t
    {
        Idle        = 0,    // at his spot
        Walking     = 1,    // running to kWeegliDoorSpot (DATA_END_DOOR 1)
        Planted     = 2,    // the barrel is down; the fuse waits for the fight's end
        Fuse        = 3,    // the fight is over: the fuse burns (kFuseMs)
        Leaving     = 4,    // the door is blown (DATA_END_DOOR 3): the betrayal's escape path, or the Test's pool
        Done        = 5,    // gone for good, or at the pool
    };
    inline std::array<char const*, 6> constexpr kDoorWalkNames{ {
        "idle", "walking", "planted", "fuse", "leaving", "done",
    } };

    enum class DoorEvent : std::uint8_t
    {
        Start,      // the betrayal's fight started, or the Test's fight ended (and the door is shut)
        Planted,    // the barrel's cast went off (kPlantDelayMs after arriving)
        FightOver,  // slot 6 is DONE
        Blown,      // the fuse burnt out, or the door was found open (the instance's fallback)
        Left,       // the escape path ended, or he stands at the pool
        Abort,      // the fight wiped before the door went (back to his gather spot)
    };

    // The next state; `fightOver`: slot 6 is DONE now (a barrel planted after the end lights at once).
    constexpr DoorWalk DoorWalkNext(DoorWalk s, DoorEvent e, bool fightOver)
    {
        switch (e)
        {
            case DoorEvent::Start:
                return s == DoorWalk::Idle ? DoorWalk::Walking : s;
            case DoorEvent::Planted:
                if (s != DoorWalk::Walking)
                    return s;
                return fightOver ? DoorWalk::Fuse : DoorWalk::Planted;
            case DoorEvent::FightOver:
                return s == DoorWalk::Planted ? DoorWalk::Fuse : s;
            case DoorEvent::Blown:
                return (s == DoorWalk::Idle || s == DoorWalk::Walking || s == DoorWalk::Planted
                    || s == DoorWalk::Fuse) ? DoorWalk::Leaving : s;
            case DoorEvent::Left:
                return s == DoorWalk::Leaving ? DoorWalk::Done : s;
            case DoorEvent::Abort:
                return (s == DoorWalk::Walking || s == DoorWalk::Planted) ? DoorWalk::Idle : s;
            default:
                return s;
        }
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Floors: Weegli at 1 health until he stands at the pool (section 7 #13 A); the Test's 30% yield (SP BC11, the
    // default yield while D5 has not taken it over)
    // ----------------------------------------------------------------------------------------------------------------
    // The part of `damage` a unit at `health` may take without going under `floor` (0 when it is at or under it).
    constexpr std::uint32_t FlooredDamage(std::uint32_t health, std::uint32_t damage, std::uint32_t floor)
    {
        if (health <= floor)
            return 0;
        return std::min(damage, health - floor);
    }

    // Weegli cannot die until he stands at the pool (the Test path): in every other mode, and on the way there.
    constexpr bool WeegliFloorHolds(CrewMode mode, bool arrivedAtPool)
    {
        return mode != CrewMode::PoolAlly || !arrivedAtPool;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Murta's healing (script values on the stock spells; section 3.12 "healing by script")
    // ----------------------------------------------------------------------------------------------------------------
    enum class MurtaHeal : std::uint8_t
    {
        None,
        Heal,       // under kHealBelowPct: Heal 11642 for kHealPct of the target's health
        Shield,     // under kShieldBelowPct and no Shield yet: absorbs kShieldPct
        Renew,      // under kRenewBelowPct and no Renew yet: kRenewTickPct per 3 s tick
    };

    // The index of the lowest health percent under `belowPct` (ties: the first), or none.
    inline std::optional<std::size_t> PickHealTarget(std::vector<float> const& healthPcts, float belowPct)
    {
        std::optional<std::size_t> best;
        for (std::size_t i = 0; i < healthPcts.size(); ++i)
            if (healthPcts[i] < belowPct && (!best || healthPcts[i] < healthPcts[*best]))
                best = i;
        return best;
    }

    namespace Tune
    {
        // Murta (the stock SmartAI: a friend missing health within 40 yd every 8 to 11 s)
        float constexpr kHealRangeYd = 40.f;
        float constexpr kHealBelowPct = 50.f;
        float constexpr kShieldBelowPct = 65.f;
        float constexpr kRenewBelowPct = 80.f;
        float constexpr kHealPct = 25.f;            // SP BC7's landed Greater Heal on normal, as the ally's heal
        float constexpr kRenewTickPct = 3.f;        // 5 ticks over 15 s: 15%
        float constexpr kShieldPct = 15.f;
    }

    // The spell for the picked target: the heal first, then the shield, then the renew.
    constexpr MurtaHeal MurtaSpellFor(float healthPct, bool hasRenew, bool hasShield)
    {
        if (healthPct < Tune::kHealBelowPct)
            return MurtaHeal::Heal;
        if (healthPct < Tune::kShieldBelowPct && !hasShield)
            return MurtaHeal::Shield;
        if (healthPct < Tune::kRenewBelowPct && !hasRenew)
            return MurtaHeal::Renew;
        return MurtaHeal::None;
    }

    // A percent of a health pool, at least 1.
    constexpr std::uint32_t PctOf(std::uint32_t maxHealth, float pct)
    {
        float const v = float(maxHealth) * pct / 100.f;
        return v < 1.f ? 1u : std::uint32_t(v);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The pool (the Test path): once all five stand there, CR sends SetData(DATA_CREW_AT_POOL, 1) (the hard mode's
    // key needs all five)
    // ----------------------------------------------------------------------------------------------------------------
    constexpr bool AllArrived(std::uint32_t arrivedMask)
    {
        return (arrivedMask & ZulFarrakRework::kCrewAll) == ZulFarrakRework::kCrewAll;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The kits' timers and the flows' delays (rule 32)
    // ----------------------------------------------------------------------------------------------------------------
    struct Window
    {
        std::uint32_t minMs;
        std::uint32_t maxMs;
    };

    namespace Tune
    {
        // Bly (zulfarrak.cpp npc_sergeant_bly: Shield Bash 5 s then 15 s, Revenge 8 s then 10 s)
        Window constexpr kShieldBashFirst{ 5000, 5000 };
        Window constexpr kShieldBash{ 15000, 15000 };
        Window constexpr kRevengeFirst{ 8000, 8000 };
        Window constexpr kRevenge{ 10000, 10000 };
        // Raven (SmartAI 7605: Gouge 6-11 s then 23-35 s on a random within 5 yd; Backstab from behind every 6 s)
        Window constexpr kGougeFirst{ 6000, 11000 };
        Window constexpr kGouge{ 23000, 35000 };
        Window constexpr kBackstab{ 6000, 6000 };
        float constexpr kGougeRangeYd = 5.f;
        // Oro (SmartAI 7606: Shadow Bolt 0-1 s then 3-5 s; Rain of Fire 6-11 s then 23-35 s on a random within 30 yd;
        // Immolate 13-15 s then 23-35 s; Curse of Weakness 0-15 s then 60 s)
        Window constexpr kShadowBoltFirst{ 0, 1000 };
        Window constexpr kShadowBolt{ 3000, 5000 };
        Window constexpr kRainFirst{ 6000, 11000 };
        Window constexpr kRain{ 23000, 35000 };
        float constexpr kRainRangeYd = 30.f;
        Window constexpr kImmolateFirst{ 13000, 15000 };
        Window constexpr kImmolate{ 23000, 35000 };
        Window constexpr kCurseFirst{ 0, 15000 };
        Window constexpr kCurse{ 60000, 60000 };
        // Murta (SmartAI 7608: Holy Smite 1-2 s then 3-6 s; the heals every 8 to 11 s)
        Window constexpr kSmiteFirst{ 1000, 2000 };
        Window constexpr kSmite{ 3000, 6000 };
        Window constexpr kHealCheckFirst{ 2000, 4000 };
        Window constexpr kHealCheck{ 8000, 11000 };
        std::uint32_t constexpr kHealRetryMs = 1000;    // nobody hurt (or casting): look again soon

        // Bly's gossip (stock: line 0 at 1.5 s, line 1 3 s later, hostile 3 s later); the Test has no line in SP, so
        // its fight starts kTestStartMs after the choice.
        std::uint32_t constexpr kBetrayalLine0Ms = 1500;
        std::uint32_t constexpr kBetrayalLine1Ms = 3000;
        std::uint32_t constexpr kBetrayalHostileMs = 3000;
        std::uint32_t constexpr kTestStartMs = 3000;
        float constexpr kFightTargetRangeYd = 80.f;

        // The Test's default yield (SP BC11): the health floor while D5 has not taken it over
        float constexpr kYieldPct = 30.f;

        // Weegli's door (stock: the plant 2 s after arriving; the barrel's SmartAI fired 2 s after the plant)
        std::uint32_t constexpr kPlantDelayMs = 2000;
        std::uint32_t constexpr kFuseMs = 2000;
        std::uint32_t constexpr kDoorWalkTimeoutMs = 40000;     // 57 yd at run speed is about 8 s
        std::uint32_t constexpr kEscapeDespawnMs = 90000;       // the escape path's end, or this
        std::uint32_t constexpr kWeegliStandMs = 10000;         // kneeling at 1 health this long, then he stands

        // The Block's prisoner: the jumps and their safety timeouts
        float constexpr kPrisonerJumpSpeedXY = 12.f;
        float constexpr kPrisonerJumpSpeedZ = 6.f;
        std::uint32_t constexpr kPrisonerMoveTimeoutMs = 3000;

        // The Test's departure to the pool: Band's Escape (10 s cast) a little after the last yield, then the shore
        std::uint32_t constexpr kPoolDepartDelayMs = 4000;
        std::uint32_t constexpr kBandsEscapeMs = 10500;

        // Placing a member after a create, a respawn or a reload: closer than this stays where it is
        float constexpr kPlaceSnapYd = 3.f;
        // A walk that has not arrived this long is finished by a teleport (a broken path never strands a member)
        std::uint32_t constexpr kWalkTimeoutMs = 60000;
        // A Gone fighter still alive (a GM, a missed message) leaves after this long
        std::uint32_t constexpr kGoneDespawnMs = 3000;

        static_assert(kFuseMs >= 1000, "the fuse is seen");
        static_assert(kBandsEscapeMs > 10000, "the departure waits for Band's Escape's 10 s cast");
        static_assert(kYieldPct > 0.f && kYieldPct < kHealBelowPct, "Greater Heal's window sits above the yield");
        static_assert(kPrisonerMoveTimeoutMs >= 1500, "a jump of about 10 yd lands well inside its timeout");
    }

    // A delay inside a window for a random draw in [0, 1].
    constexpr std::uint32_t InWindow(Window w, float roll01)
    {
        if (w.maxMs <= w.minMs)
            return w.minMs;
        float const r = roll01 < 0.f ? 0.f : (roll01 > 1.f ? 1.f : roll01);
        return w.minMs + std::uint32_t(float(w.maxMs - w.minMs) * r);
    }
}

#endif
