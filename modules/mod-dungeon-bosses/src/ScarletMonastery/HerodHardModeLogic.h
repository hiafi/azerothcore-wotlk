/*
 * mod-dungeon-bosses, Scarlet Monastery D11H:
 * Herod's hard mode, Call to Arms (heroic only), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-3-armory.md "Hard mode: Call to Arms" (HM0-HM3) and the Build spec rows; handoff
 * section 3.7, 3.5 row D11H, 3.6, 7 #31 A (the garrison's scripted straight march). Tested by
 * tests/sm_herod_hard_mode_test.cpp. The engine side is herod_hard_mode.cpp, on D11's HerodFight.h hooks.
 *
 *   Spells     the WP's ids, inside kSpellsCallToArms (213020-213059), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/herod_hard_mode.py
 *   Trigger    HM0 The Real Challenge: the answer to a /taunt (the instance makes the final call), the 30 s cooldown of
 *              "Words. Show me steel."
 *   Tuning     the hard mode's numbers as ratios of D11's heroic values (HerodLogic.h), so a retune of D11's heroic
 *              cadence carries over: spins and throws every 28.16 s (32 x 0.88), the lap at 14 yd/s (12 x 7 / 6), two
 *              blades every 1.5 s (heroic's cadence before Frenzy, two at once), the 6 s whirl (5 x 1.2), 60% hits (45
 *              x 4 / 3), the beams at heroic's 45%, 400k (320k x 1.25)
 *   HM2        the prayer (20 s, unharmable, heals to full), three squads of four Garrison Trainees at 0, 5 and 10 s
 *              marching the section 7 #31 A line (HerodLogic.h kGarrisonMarch) at 2.5 yd/s, the door sealed again at
 *              12 s (it shuts 3 s later, about 15 s in), Zeal per arrival (six at most)
 *   HM3        Ravager's Beacon: two beams round the planted axe (KT-SM TurningBeams), 3 yd off it to the pit's edge
 *   HM1        Consecrated Hall: 2% of the reference row a second, a tick every 2 s
 *
 * Compass (NAVMESH): +x is north, +y is west; a bearing is measured from +x toward +y (radians, as WoW's orientation).
 */

#ifndef MOD_DUNGEON_BOSSES_SM_HEROD_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_HEROD_HARD_MODE_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitZoneLogic.h"
#include "HerodLogic.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace SmCallToArms
{
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsCallToArms;

    enum CallToArmsSpells : std::uint32_t
    {
        SPELL_CTA_AURA = kSpellSlice.first + 0,  // 213020 HM0 the red aura on Herod (holds a wipe)
        SPELL_CTA_PRAYER = kSpellSlice.first + 1,  // 213021 HM2 Prayer of the Champion: unharmable, the kneel
        SPELL_CTA_PILLAR = kSpellSlice.first + 2,  // 213022 HM2 the pillar of Light on him (look)
        SPELL_CTA_ZEAL = kSpellSlice.first + 3,  // 213023 HM2b Zeal (+5% damage, +5% attack speed a stack, 6)
        SPELL_CTA_FADE = kSpellSlice.first + 4,  // 213024 HM2a an arrived trainee fades into the Light (look)
        SPELL_CTA_GLOW = kSpellSlice.first + 5,  // 213025 HM3 the planted axe's glow (one-shot, replayed)
        SPELL_CTA_BEAM_LOOK = kSpellSlice.first + 6,  // 213026 HM3 a beam's chain, end stalker -> the axe (channel)
        SPELL_CTA_BEAM = kSpellSlice.first + 7,  // 213027 HM3 a beam step's hit (resolve copy, Holy)
        SPELL_CTA_HALL = kSpellSlice.first + 8,  // 213028 HM1 Consecrated Hall's tick (kit percent script, Holy)
        SPELL_CTA_HALL_LOOK = kSpellSlice.first + 9,  // 213029 HM1 the consecrated floor (an aura on the axe)
        // 213030-213059 spare
    };
    static_assert(SPELL_CTA_HALL_LOOK <= kSpellSlice.last, "Call to Arms's spells must stay in its slice");

    // Registry tags (the build spec's mechanic numbers, 30 + n for HMn so they never meet D11's HB tags).
    enum CallToArmsTags : std::uint32_t
    {
        TAG_HM_BEAM         = 33,   // HM3 a beam step
    };

    // Items: the Crusader's blade he draws at his rising (V's ITEM_HEROD_BLADE, Crusader's Greatblade [DB]) and the
    // garrison's mace (V's ITEM_TRAINEE_MACE, the stock Scarlet Trainee's).
    inline constexpr std::uint32_t kItemCrusaderBlade = 39802;
    inline constexpr std::uint32_t kItemTraineeMace = 2813;

    // ----------------------------------------------------------------------------------------------------------------
    // HM0 The Real Challenge
    // ----------------------------------------------------------------------------------------------------------------

    enum class TauntAnswer : std::uint8_t
    {
        None,       // no answer (he is dead)
        Words,      // line 6 "Words. Show me steel." (30 s cooldown), no change
        Challenge,  // ask the instance to light the flag; line 5 and the red aura once it is lit
    };

    // A /taunt aimed at Herod. The instance judges the flag again (ScarletMonasteryRework::HerodTauntAllowed): a
    // Challenge it refuses is answered with Words.
    constexpr TauntAnswer TauntAnswerFor(bool alive, bool heroic, bool inCombat, bool lit, std::uint32_t herodState,
        bool wave2Bound = ScarletMonasteryRework::kWave2Bound)
    {
        if (!alive)
            return TauntAnswer::None;
        if (inCombat || !ScarletMonasteryRework::HerodTauntAllowed(heroic, herodState, lit, wave2Bound))
            return TauntAnswer::Words;
        return TauntAnswer::Challenge;
    }

    inline constexpr std::uint32_t kWordsCooldownMs = 30000;

    constexpr bool WordsReady(std::uint64_t nowMs, std::uint64_t readyAtMs)
    {
        return nowMs >= readyAtMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning: ratios of D11's heroic values (HerodLogic.h), the build spec's numbers today
    // ----------------------------------------------------------------------------------------------------------------

    // Health from the pull: 400k = D11's heroic 320k x 1.25 (set by script at the pull, his template back on a wipe).
    inline constexpr float kHealthRatio = 1.25f;
    constexpr std::uint32_t HardModeHealth(std::uint32_t heroicHealth)
    {
        return static_cast<std::uint32_t>(static_cast<float>(heroicHealth) * kHealthRatio + 0.5f);
    }
    inline constexpr std::uint32_t kHerodHealth = HardModeHealth(SmHerod::kHerodHealth.heroic);

    // HB1 / HB2: the spins' and throws' cadence after the first (heroic 32 s -> 28.16 s).
    inline constexpr float kCadenceRatio = 0.88f;
    constexpr std::uint32_t HardModeEveryMs(std::uint32_t heroicEveryMs)
    {
        return static_cast<std::uint32_t>(static_cast<float>(heroicEveryMs) * kCadenceRatio + 0.5f);
    }
    inline constexpr std::uint32_t kSpinEveryMs = HardModeEveryMs(SmHerod::kSpinBeat.heroic.everyMs);
    inline constexpr std::uint32_t kThrowEveryMs = HardModeEveryMs(SmHerod::kThrowBeat.heroic.everyMs);

    // HB1b the lap at 14 yd/s (heroic 12 x 7 / 6).
    inline constexpr float kLapSpeedRatio = 7.f / 6.f;
    inline constexpr float kLapSpeedYd = SmHerod::kLapSpeedYd.heroic * kLapSpeedRatio;

    // HB1c two blades at once every 1.5 s, the whole fight (heroic's cadence before Frenzy, two at once).
    inline constexpr std::uint32_t kBladesAtOnce = 2;
    inline constexpr SmHerod::BladePlan kBlades{ SmHerod::BladePlanFor(true, false).everyMs, kBladesAtOnce };

    // HB2w the thrown axe whirls 6 s (heroic 5 x 1.2), first half only (the second half plants the axe).
    inline constexpr float kWhirlRatio = 1.2f;
    inline constexpr std::uint32_t kWhirlMs = static_cast<std::uint32_t>(
        static_cast<float>(SmHerod::kWhirlMs.heroic) * kWhirlRatio + 0.5f);

    // Every hit of D11's kit (lanes, lap, blades, throw, return, whirl, the cleave on others): 60% (heroic 45 x 4 / 3).
    // The cleave's tank share stays D11's 25%.
    inline constexpr float kHitRatio = 4.f / 3.f;
    inline constexpr float kHitPct = SmHerod::kHitPct.heroic * kHitRatio;

    // ----------------------------------------------------------------------------------------------------------------
    // HM2 The Garrison Answers
    // ----------------------------------------------------------------------------------------------------------------

    // At 50%, in place of HB4's Frenzy (D11's ThresholdPct; D11 waits until he is home with his axe in hand).
    inline constexpr float kThresholdPct = SmHerod::kFrenzyAtPct;

    // The prayer: 20 s from the threshold (his walk to the pillar included), unharmable, from his health then to full.
    inline constexpr std::uint32_t kPrayerMs = 20000;
    // He walks to his kneeling spot (the pillar, 3 yd short of the pit's center, facing the planted axe); if he is not
    // there by kKneelWalkMaxMs he is placed there.
    inline constexpr Point3 kKneelSpot = SmHerod::kGarrisonMarch[3];
    inline constexpr float kKneelFacing = 0.f;      // north: the axe at the pit's center is 3 yd ahead
    inline constexpr std::uint32_t kKneelWalkMaxMs = 4000;
    inline constexpr float kKneelReachYd = 0.8f;
    // The planted axe: Ravager in the floor at the pit's center (the beams' anchor, the hall's look).
    inline constexpr Point3 kAxeSpot = SmHerod::kPitCenter;
    // The wall rack the Crusader's blade comes from (GO 301328, a heroic spawn of the rev): against the pit's east wall
    // (the pit floor ends at y -445.5 there [navmesh/maps3.txt]), facing the pit's center; clear of the march's lanes,
    // the Fine Chairs (97801-97803) and the lap. Scenery: the blade is in his hand at the rising.
    inline constexpr Point3 kRackSpot{ 1961.9f, -444.f, 6.3f };
    inline constexpr float kRackFacing = DungeonKit::kPi / 2.f;     // west, toward the pit's center

    // The heal ticks this often (his health moves on a straight line from its start to full over the prayer).
    inline constexpr std::uint32_t kPrayerTickMs = 500;

    // His health `elapsedMs` into the prayer: a straight line from `startHealth` to `maxHealth` at `prayerMs`.
    constexpr std::uint32_t PrayerHealth(std::uint32_t startHealth, std::uint32_t maxHealth, std::uint64_t elapsedMs,
        std::uint32_t prayerMs = kPrayerMs)
    {
        if (startHealth >= maxHealth || prayerMs == 0 || elapsedMs >= prayerMs)
            return maxHealth;
        std::uint64_t const gain = static_cast<std::uint64_t>(maxHealth - startHealth) * elapsedMs / prayerMs;
        return startHealth + static_cast<std::uint32_t>(gain);
    }

    // The march: three squads of four, one every 5 s from the threshold (0, 5, 10 s); the door is sealed again at
    // 12 s (SealedArena shuts it 3 s later, about 15 s in, behind the last squad).
    inline constexpr std::uint32_t kSquadCount = 3;
    inline constexpr std::uint32_t kSquadSize = 4;
    inline constexpr std::uint32_t kGarrisonCount = kSquadCount * kSquadSize;
    inline constexpr std::uint32_t kSquadEveryMs = 5000;
    inline constexpr std::uint32_t kResealAtMs = 12000;
    inline constexpr std::uint32_t kDoorShutDelayMs = 3000;     // D11's SealedArena delay (HB0)

    // Squads due `elapsedMs` into the prayer (the first at 0).
    constexpr std::uint32_t SquadsDue(std::uint64_t elapsedMs)
    {
        std::uint64_t const due = elapsedMs / kSquadEveryMs + 1;
        return static_cast<std::uint32_t>(std::min<std::uint64_t>(due, kSquadCount));
    }

    // Each squad steps in behind the door line (x 1933.7, on the cross hall's floor), so it marches through the opened
    // door; then the section 7 #31 A line (HerodLogic.h kGarrisonMarch: inside the door, the landing's lip, the jump
    // down into the pit, the pillar).
    inline constexpr Point3 kGarrisonSpawn{ 1931.f, -431.6f, 18.7f };
    inline constexpr float kGarrisonFacing = 0.f;       // north, into the hall
    inline constexpr float kMarchPaceYd = SmHerod::kGarrisonPaceYd;

    // The squads halt this far short of the pillar (south of it: Herod kneels on the pillar itself), four abreast.
    inline constexpr float kPillarShortYd = 1.5f;

    // One trainee's route on lane `lane` (0-3, + to the west): the spawn, then the four march points, each shifted by
    // the lane's offset across the line (the line runs north along y -431.6), the last kPillarShortYd short of it.
    struct MarchPoint
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
    };
    inline constexpr std::size_t kRoutePoints = SmHerod::kGarrisonMarch.size() + 1;
    // Route indexes: the lip (the jump leaves from it), the landing (the jump arrives there), the pillar.
    inline constexpr std::size_t kJumpFromIndex = SmHerod::kGarrisonJumpFrom + 1;
    inline constexpr std::size_t kJumpToIndex = kJumpFromIndex + 1;
    inline constexpr std::size_t kLastIndex = kRoutePoints - 1;

    constexpr std::array<MarchPoint, kRoutePoints> MarchRoute(std::size_t lane)
    {
        float const off = SmHerod::kGarrisonLaneOffsetsYd[lane % SmHerod::kGarrisonLaneOffsetsYd.size()];
        std::array<MarchPoint, kRoutePoints> route{};
        route[0] = MarchPoint{ kGarrisonSpawn.x, kGarrisonSpawn.y + off, kGarrisonSpawn.z };
        for (std::size_t i = 0; i < SmHerod::kGarrisonMarch.size(); ++i)
            route[i + 1] = MarchPoint{ SmHerod::kGarrisonMarch[i].x, SmHerod::kGarrisonMarch[i].y + off,
                SmHerod::kGarrisonMarch[i].z };
        route[kRoutePoints - 1].x -= kPillarShortYd;
        return route;
    }

    // The jump off the ledge (MotionMaster::MoveJump launch speeds): about 0.7 s for the 4 yd and 9 yd drop.
    inline constexpr float kJumpSpeedXY = 6.f;
    inline constexpr float kJumpSpeedZ = 3.f;
    inline constexpr std::uint32_t kJumpMs = 700;       // its budget in the march time; a jump not done by 3x is ended

    // The walked length of a route (the jump leg is not walked).
    inline float WalkedYd(std::array<MarchPoint, kRoutePoints> const& route)
    {
        float total = 0.f;
        for (std::size_t i = 1; i < route.size(); ++i)
        {
            if (i == kJumpToIndex)
                continue;
            total += DungeonKit::Distance({ route[i - 1].x, route[i - 1].y }, { route[i].x, route[i].y });
        }
        return total;
    }

    // Spawn to pillar: walked at the drill pace plus the jump (section 7 #31 A: about 12 s).
    inline std::uint32_t MarchMs(std::size_t lane = 0)
    {
        return SmHerod::TravelMs(WalkedYd(MarchRoute(lane)), kMarchPaceYd) + kJumpMs;
    }

    // The route index a trainee walks to next: `leg` unless it is in the pit (knocked or dropped down) before its jump,
    // then straight on to the pillar (it never climbs back).
    constexpr std::size_t NextLeg(std::size_t leg, float z)
    {
        if (leg <= kJumpToIndex && z <= SmHerod::kPitZMax)
            return kLastIndex;
        return leg;
    }

    // A trainee within kArriveYd of its pillar spot (2D) has arrived: it kneels, fades into the Light (gone kFadeMs
    // later) and Herod gains a stack of Zeal. A leg point is reached within kLegReachYd.
    inline constexpr float kArriveYd = 1.f;
    inline constexpr float kLegReachYd = 0.8f;
    inline constexpr std::uint32_t kFadeMs = 1500;
    // A trainee re-aims this often (a stun, root or knockback ended; a slow changed its pace).
    inline constexpr std::uint32_t kReaimMs = 500;
    // A trainee still marching this long after its spawn is despawned (a stuck one never holds the fight open).
    inline constexpr std::uint32_t kMarchLifeMs = 90000;

    constexpr bool Arrived(float distToPillarYd)
    {
        return distToPillarYd <= kArriveYd;
    }

    // HM2b Zeal: +5% damage and +5% attack speed a stack (one per arrived trainee), six at most: HANDOFF section 10
    // add sizing C (orchestrator default 2026-11-20; twelve took his frenzied melee to x4 of plain heroic).
    inline constexpr std::uint32_t kZealPct = 5;
    inline constexpr std::uint32_t kZealMax = 6;

    constexpr std::uint32_t ZealAfterArrival(std::uint32_t stacks)
    {
        return std::min<std::uint32_t>(stacks + 1, kZealMax);
    }

    // His melee against the tank at `stacks` of Zeal, frenzied or not (HB4: +30% attack speed, +20% Physical), as a
    // multiple of his plain heroic melee (damage per second).
    constexpr float MeleeLoad(std::uint32_t stacks, bool frenzied)
    {
        float const zeal = 1.f + static_cast<float>(kZealPct * stacks) / 100.f;
        float const haste = frenzied ? 1.f + SmHerod::kFrenzyHastePct / 100.f : 1.f;
        float const damage = frenzied ? 1.f + SmHerod::kFrenzyDamagePct / 100.f : 1.f;
        return zeal * zeal * haste * damage;
    }

    // After the rising the first spin comes D11's heroic first-spin delay later (the tank picks him up first); the
    // throw clock restarts with D11's heroic first-throw delay but never fires (the axe is planted).
    inline constexpr std::uint32_t kSpinAfterRisingMs = SmHerod::kSpinBeat.heroic.firstMs;
    inline constexpr std::uint32_t kThrowAfterRisingMs = SmHerod::kThrowBeat.heroic.firstMs;

    // Rule 20 (LESSONS 4.2): about how many trainees a group kills on the march. `dps` its damage a second on one
    // target, `aoeTargets` how many of a squad (four abreast, 1.2 yd apart) each hit lands on; the window runs from
    // the first squad's spawn to the last squad's arrival. An estimate (squads overlap, damage is spent in order).
    constexpr std::uint32_t TraineesKilled(float dps, std::uint32_t aoeTargets, std::uint32_t health,
        std::uint32_t marchMs)
    {
        if (health == 0)
            return kGarrisonCount;
        float const windowS = static_cast<float>((kSquadCount - 1) * kSquadEveryMs + marchMs) / 1000.f;
        float const damage = dps * windowS * static_cast<float>(std::max<std::uint32_t>(1, aoeTargets));
        auto const killed = static_cast<std::uint32_t>(damage / static_cast<float>(health));
        return std::min(killed, kGarrisonCount);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // HM3 Ravager's Beacon (KT-SM TurningBeams round the planted axe)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint8_t kBeamCount = 2;
    inline constexpr float kBeamStepDeg = 30.f;
    inline constexpr std::uint32_t kBeamStepMs = 1500;
    inline constexpr float kBeamInnerYd = 3.f;
    // Asked for longer than the pit: its edge clips each beam kBeamInsetYd short of it (about 9.6 yd long).
    inline constexpr float kBeamLengthYd = 14.f;
    inline constexpr float kBeamInsetYd = 0.5f;
    inline constexpr float kBeamWidthYd = 4.f;
    // 45% Holy and Weakened (heroic's hit, not the hard mode's 60%: the build spec), the tank row on the tank.
    inline constexpr float kBeamPct = SmHerod::kHitPct.heroic;
    // A full turn (360 / 30 steps of 1.5 s): 18 s.
    inline constexpr std::uint32_t kBeamTurnMs = static_cast<std::uint32_t>(360.f / kBeamStepDeg) * kBeamStepMs;

    // One beam's lane at `bearing` round the axe, clipped at the pit's edge (the circle of kPitRadiusYd round the pit's
    // center, as HerodLogic.h PitArena()).
    inline std::optional<DungeonKit::BeamLane> BeamLaneAt(float bearing)
    {
        Vec2 const anchor{ kAxeSpot.x, kAxeSpot.y };
        std::optional<float> const wall = DungeonKit::RayToCircleEdge({ SmHerod::kPitCenter.x, SmHerod::kPitCenter.y },
            SmHerod::kPitRadiusYd, anchor, bearing);
        return DungeonKit::BeamSegment(anchor, bearing, kBeamInnerYd, kBeamLengthYd, wall, kBeamInsetYd);
    }

    // The glow on the planted axe is a one-shot impact (V): replayed this often.
    inline constexpr std::uint32_t kGlowEveryMs = 4000;

    // ----------------------------------------------------------------------------------------------------------------
    // HM1 Consecrated Hall
    // ----------------------------------------------------------------------------------------------------------------

    // 2% of the reference row a second, a tick every 2 s: 4% a tick, in hundredths for the kit's percent script.
    inline constexpr float kHallPctPerSecond = 2.f;
    inline constexpr std::uint32_t kHallTickMs = 2000;
    constexpr std::uint32_t HallHundredthsPerTick(float pctPerSecond = kHallPctPerSecond,
        std::uint32_t tickMs = kHallTickMs)
    {
        return static_cast<std::uint32_t>(pctPerSecond * static_cast<float>(tickMs) / 10.f + 0.5f);
    }
    inline constexpr std::uint32_t kHallHundredths = HallHundredthsPerTick();

    // ----------------------------------------------------------------------------------------------------------------
    // The fight's halves
    // ----------------------------------------------------------------------------------------------------------------

    enum class Half : std::uint8_t
    {
        First,      // the pull to 50%: heroic's kit, harder
        Prayer,     // HM2 the Garrison Answers
        Second,     // from his rising: the beams, the hall, the blade, no throws
    };

    // Ravager's Throw only in the first half (none in the prayer; the second half's axe is planted).
    constexpr bool ThrowsAllowed(Half half)
    {
        return half == Half::First;
    }

    // HM3 flips its turn at every spin of the second half (the beams do not exist before).
    constexpr bool BeamsFlipOnSpin(Half half)
    {
        return half == Half::Second;
    }

    // The bots: the garrison ahead of Herod (his priority is 0) for every role, AoE welcome.
    inline constexpr std::int8_t kGarrisonPriority = 2;
}

#endif
