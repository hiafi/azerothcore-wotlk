// Host tests for KellLogic.h (D6: Ambrose Kell, the Antiquarian).
#include "KellLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace ScarletMonasteryRework;
using namespace SmKell;

namespace
{
    // A fixed pseudo-random run in [0, 1) (a linear congruential generator): the tests never depend on luck.
    struct Lcg
    {
        std::uint32_t state = 12345;

        float operator()()
        {
            state = state * 1664525u + 1013904223u;
            return static_cast<float>((state >> 8) & 0xFFFFFF) / static_cast<float>(0x1000000);
        }
    };

    constexpr float kDegToRad = 3.14159265358979f / 180.f;
}

int main()
{
    // ---- the slice and the binding ----------------------------------------------------------------------------------
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(SmKell::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(SmKell::kSpellSlice.last));
    CHECK(SPELL_AN_UNSEAL_CAST == 212570);
    CHECK(SPELL_AN_TROPHY_SKULL == 212587);
    CHECK(SPELL_AN_TROPHY_SKULL - SPELL_AN_UNSEAL_CAST == 17);       // eighteen spells, contiguous from the slice start
    CHECK(SmKell::kBound);
    // Ambrose Kell spawns kKellSpot, inside the arena.
    CHECK(KellArena().Contains(kKellSpot.XY(), kKellSpot.z));
    CHECK(ArenaFor(BOSS_KELL).Contains(kKellSpot.XY(), kKellSpot.z));
    // Wave 1.
    CHECK(!IsWave2Boss(BOSS_KELL));
    // His ids are the header's (S0): the boss, the relic trigger, the skeleton; the pedestal and three relics.
    CHECK(NPC_SM_KELL == 300910 && NPC_SM_RELIC_TRIGGER == 300911 && NPC_SM_GALLERY_SKELETON == 300912);
    CHECK(GO_SM_RELIC_PEDESTAL == 301315 && GO_SM_RELIC_CASK == 301316 && GO_SM_RELIC_STAFF == 301317
        && GO_SM_RELIC_SKULL == 301318);

    // ---- AN1 the six cases (section 7 #25 A) ------------------------------------------------------------------------
    CHECK(kCases.size() == 6);
    for (CaseSpot const& c : kCases)
    {
        // every case is in the arena (the hall), on its own floor
        CHECK(KellArena().Contains(c.spot.XY(), c.spot.z));
        // a west case is on the y -311 side, an east case on the y -340 side
        CHECK(c.west ? c.spot.y > -312.f && c.spot.y < -310.f : c.spot.y < -339.f && c.spot.y > -341.f);
        // the aisle is between them
        CHECK(c.west ? c.spot.y > kAisleY : c.spot.y < kAisleY);
    }
    // The layout table of LIB "New mechanics" 1: west S Cask, M Staff, N Skull; east S Skull, M Cask, N Staff.
    CHECK(kCases[0].relic == Relic::Cask && kCases[1].relic == Relic::Staff && kCases[2].relic == Relic::Skull);
    CHECK(kCases[3].relic == Relic::Skull && kCases[4].relic == Relic::Cask && kCases[5].relic == Relic::Staff);
    CHECK(CountOf(Relic::Cask) == 2 && CountOf(Relic::Staff) == 2 && CountOf(Relic::Skull) == 2);
    // x about 222 / 243 / 265 and the NAVMESH floor z of every spot (section 7 #25 A, NM #10)
    CHECK(kCases[0].spot.x == 222.f && kCases[1].spot.x == 243.f && kCases[2].spot.x == 265.f);
    CHECK(kCases[3].spot.x == 221.8f && kCases[4].spot.x == 243.f && kCases[5].spot.x == 265.f);
    CHECK(kCases[0].spot.z == 18.7f && kCases[1].spot.z == 20.8f && kCases[2].spot.z == 20.8f);
    CHECK(kCases[3].spot.z == 19.3f && kCases[4].spot.z == 18.7f && kCases[5].spot.z == 19.7f);
    // (222, -340) has no floor: the south east case is at (221.8, -340.3)
    CHECK(kCases[3].spot.y == -340.3f);
    // The passage to the reading hall (265, -340) is a staff case ("a staff there leaves nothing on the floor").
    CHECK(kCases[5].relic == Relic::Staff && kCases[5].spot.x == 265.f && kCases[5].spot.y == -340.f);
    // The relic sits on the pedestal: 1.2 yd up (VR: BattlemasterPedestal), displays are the VR picks.
    CHECK(kPedestalHeightYd > 1.1f && kPedestalHeightYd < 1.3f);
    CHECK(kPedestalDisplay == 7695 && RelicDisplay(Relic::Cask) == 288 && RelicDisplay(Relic::Staff) == 1708
        && RelicDisplay(Relic::Skull) == 217);
    // Facing: the west cases face -y, the east cases +y (into the aisle).
    CHECK(std::fabs(std::sin(CaseFacing(kCases[0])) + 1.f) < 1e-4f);
    CHECK(std::fabs(std::sin(CaseFacing(kCases[3])) - 1.f) < 1e-4f);
    // The Unseal's emote names the relic.
    CHECK(UnsealEmote(Relic::Cask) == EMOTE_UNSEAL_CASK && UnsealEmote(Relic::Staff) == EMOTE_UNSEAL_STAFF
        && UnsealEmote(Relic::Skull) == EMOTE_UNSEAL_SKULL);

    // ---- AN1 the nearest sealed case wakes (the tank's choice by where it holds him) --------------------------------
    // From each case's own spot, that case; at his spawn mid-aisle the nearest is a middle case.
    for (std::uint32_t i = 0; i < kCaseCount; ++i)
        CHECK(NearestSealed(0, kCases[i].spot.XY()) == static_cast<int>(i));
    int const fromSpawn = NearestSealed(0, kKellSpot.XY());
    CHECK(fromSpawn == 1 || fromSpawn == 4);
    // A woken case is skipped: from the west south end with that case awake, the next nearest is the east south end
    // (the skull across the aisle: 29 yd) or the middle west case (21 yd): the middle one.
    CHECK(NearestSealed(1u << 0, kCases[0].spot.XY()) == 1);
    CHECK(NearestSealed((1u << 0) | (1u << 1), kCases[0].spot.XY()) == 3);
    CHECK(NearestSealed(AllWokenMask(), kKellSpot.XY()) == -1);
    CHECK(AllWokenMask() == 0x3F);
    // Waking in order from a fixed point visits every case once.
    {
        std::uint32_t mask = 0;
        std::uint32_t n = 0;
        for (int i = NearestSealed(mask, kKellSpot.XY()); i >= 0; i = NearestSealed(mask, kKellSpot.XY()))
        {
            CHECK((mask & (1u << i)) == 0);
            mask |= 1u << i;
            ++n;
        }
        CHECK(n == 6 && mask == AllWokenMask());
    }
    // A tie goes to the lowest index (the mid-aisle point between the two middle cases is nearest to neither).
    CHECK(NearestSealed(0, { 243.f, -325.5f }) == 1);       // 14.5 yd from the west middle, 14.5 from the east middle

    // ---- the beats --------------------------------------------------------------------------------------------------
    CHECK(kUnsealBeat(false).firstMs == 10000 && kUnsealBeat(false).everyMs == 20000);
    CHECK(kUnsealBeat(true).firstMs == 8000 && kUnsealBeat(true).everyMs == 15000);
    // Normal: about four cases wake in a fight (the spec); the fifth and sixth only in a long one.
    CHECK(CasesWokenBy(9999, false) == 0);
    CHECK(CasesWokenBy(11999, false) == 0);
    CHECK(CasesWokenBy(12000, false) == 1);
    CHECK(CasesWokenBy(72000, false) == 4);
    CHECK(CasesWokenBy(78000, false) == 4);
    CHECK(CasesWokenBy(92000, false) == 5);
    CHECK(CasesWokenBy(112000, false) == 6);
    // Heroic: all six are awake by about 83 s ("near the end of the fight: the hall closes in").
    CHECK(UnsealStartMs(5, true) == 83000);
    CHECK(CasesWokenBy(85000, true) == 6);
    CHECK(CasesWokenBy(84999, true) == 5);
    CHECK(CasesWokenBy(92000, true) == 6);
    CHECK(kStaffBeat(false).firstMs == 2000 && kStaffBeat(false).everyMs == 8000);
    CHECK(kStaffBeat(true).everyMs == 8000);
    CHECK(kSkullBeat(false).firstMs == 2000 && kSkullBeat(false).everyMs == 12000);
    CHECK(kCaneBeat(false).firstMs == 5000 && kCaneBeat(false).everyMs == 10000);
    CHECK(kFlaskEveryMs == 12000 && kTorrentEveryMs == 15000 && kCurseEveryMs == 15000);
    CHECK(kUnsealCastMs == 2000);
    // The cadence leaves room: an Unseal bar (2 s) fits inside the Torrent's 15 s and the staff's 8 s.
    CHECK(kUnsealCastMs < kStaffBeat(true).everyMs);

    // ---- the numbers (percents of the reference row) ----------------------------------------------------------------
    CHECK(kCloudPct(false) == 6.f && kCloudPct(true) == 10.f);
    CHECK(kLinePct(false) == 35.f && kLinePct(true) == 45.f);
    CHECK(kCanePct(false) == 20.f && kCanePct(true) == 30.f);
    CHECK(kFlaskPct == 40.f && kPoolPct == 8.f && kTorrentPct == 40.f && kBurstPct == 25.f);
    CHECK(kCloudRadiusYd == 8.f && kLineWidthYd == 4.f && kLineLengthYd == 40.f && kFlaskRadiusYd == 4.f);
    CHECK(kLineWarnMs == 2000 && kFlaskFlightMs == 2000 && kTorrentCastMs == 3000 && kCurseMs == 8000
        && kPoolMs == 15000);
    // The hits against their warnings (LIB approval check): staff lines 35% on a 2 s marker, inside the 40% ladder.
    CHECK(kLinePct(false) <= 40.f);
    CHECK(kLinesPerStaff == 3);

    // ---- AN2 the cloud ----------------------------------------------------------------------------------------------
    {
        // The cloud's center is the case spot moved 4 yd toward the aisle, still in the arena.
        for (CaseSpot const& c : kCases)
        {
            Vec2 const center = CloudCenter(c);
            CHECK(center.x == c.spot.x);
            CHECK(std::fabs(std::fabs(center.y - c.spot.y) - kCloudOffsetYd) < 1e-4f);
            CHECK(std::fabs(center.y - kAisleY) < std::fabs(c.spot.y - kAisleY));
            CHECK(KellArena().Contains(center, c.spot.z));
        }
        // Both casks' clouds fit together without overlapping (the space math: two clouds, about a third of the hall).
        Vec2 const a = CloudCenter(kCases[0]);
        Vec2 const b = CloudCenter(kCases[4]);
        CHECK(DungeonKit::Distance(a, b) > 2.f * kCloudRadiusYd);
        float const area = 2.f * 3.14159265f * kCloudRadiusYd * kCloudRadiusYd;
        CHECK(area > 380.f && area < 420.f);
        // NAVMESH: the long hall is 1,742 sq yd, so two clouds leave a little over three quarters of it.
        CHECK(area / 1742.f < 0.25f);
    }

    // ---- AN3 the staff's lines --------------------------------------------------------------------------------------
    {
        Lcg rng;
        for (CaseSpot const& c : kCases)
        {
            if (c.relic != Relic::Staff)
                continue;
            float const inward = InwardBearing(c);
            for (int run = 0; run < 400; ++run)
            {
                std::array<float, kLinesPerStaff> const b = LineBearings(c, rng);
                for (std::uint32_t i = 0; i < kLinesPerStaff; ++i)
                {
                    // out of the case into the hall (never into the wall behind it) and within the spread
                    float const dir = std::sin(b[i]);
                    CHECK(c.west ? dir < -0.3f : dir > 0.3f);
                    CHECK(std::fabs(b[i] - inward) <= (kLineSpreadDeg + 0.01f) * kDegToRad);
                    for (std::uint32_t j = 0; j < i; ++j)
                        CHECK(std::fabs(b[i] - b[j]) >= (kLineMinGapDeg - 0.01f) * kDegToRad);
                }
            }
        }
        // Over many draws the fan covers both sides of the inward direction (random across the hall).
        bool left = false;
        bool right = false;
        for (int run = 0; run < 200; ++run)
        {
            std::array<float, kLinesPerStaff> const b = LineBearings(kCases[1], rng);
            for (float const v : b)
            {
                left = left || v < InwardBearing(kCases[1]);
                right = right || v > InwardBearing(kCases[1]);
            }
        }
        CHECK(left && right);
        // A generator stuck at one value cannot place three apart: the even fan (-45, 0, +45).
        std::array<float, kLinesPerStaff> const stuck = LineBearings(kCases[5], []() { return 0.5f; });
        float const inward = InwardBearing(kCases[5]);
        CHECK(std::fabs(stuck[1] - inward) < 1e-4f);
        CHECK(std::fabs((stuck[2] - stuck[0]) - 90.f * kDegToRad) < 1e-3f);
        // The line is 40 yd: from the middle west staff at (243, -311) a straight-across line (bearing -y) ends at
        // y -351, just past the east wall (the hall's y range is -300 to -349): it fills the hall across.
        CHECK(kCases[1].spot.y - kLineLengthYd < -349.f + 3.f);
    }

    // ---- AN4 the skeleton cap ---------------------------------------------------------------------------------------
    CHECK(SkeletonMayRise(0, false) && SkeletonMayRise(3, false));
    CHECK(!SkeletonMayRise(4, false) && !SkeletonMayRise(7, false));        // normal: the skull waits while 4 stand
    CHECK(SkeletonMayRise(4, true) && SkeletonMayRise(40, true));           // heroic: no cap (level 60)
    CHECK(SkeletonSeeksTank(true, 30.f) && !SkeletonSeeksTank(true, 60.f) && !SkeletonSeeksTank(false, 5.f));
    CHECK(kSkullRetryMs <= 1000);
    // F-1d: everyone joins its list at 0, so the picked target (tank, else nearest) needs real threat to stick.
    CHECK(kSkeletonOpeningThreat > 0.f);

    // ---- AN5 the Trophy Powers --------------------------------------------------------------------------------------
    CHECK(TrophySpell(Relic::Cask) == SPELL_AN_TROPHY_CASK && TrophySpell(Relic::Staff) == SPELL_AN_TROPHY_STAFF
        && TrophySpell(Relic::Skull) == SPELL_AN_TROPHY_SKULL);
    CHECK(TrophySpell(Relic::Cask) != TrophySpell(Relic::Staff)
        && TrophySpell(Relic::Staff) != TrophySpell(Relic::Skull));
    CHECK(kFlaskEveryMs < kTorrentEveryMs + 1 && kTorrentEveryMs == kCurseEveryMs);
    // F-1d: a refused Torrent (silence, lockout) retries on a short beat, not every map tick, and well inside a beat.
    CHECK(kTorrentRetryMs >= 500 && kTorrentRetryMs * 5 <= kTorrentEveryMs);

    // ---- the fight's length (Build spec "Tuning") -------------------------------------------------------------------
    // N: 44k + about 4 skeletons (4.8k) = 48.8k / 623 = about 78 s. H: 240k + about 8 skeletons (48k) = 288k / 3,145.
    CHECK(std::fabs(FightSeconds(false) - 78.3f) < 0.5f);
    CHECK(std::fabs(FightSeconds(true) - 91.6f) < 0.5f);
    // A normal fight sees about four cases wake; a heroic one all six, near its end.
    CHECK(CasesWokenBy(static_cast<std::uint32_t>(FightSeconds(false) * 1000.f), false) == 4);
    CHECK(CasesWokenBy(static_cast<std::uint32_t>(FightSeconds(true) * 1000.f), true) == 6);

    // ---- the clock --------------------------------------------------------------------------------------------------
    {
        BeatClock clock;
        CHECK(!clock.Due(100000));
        clock.Start(0, 10000);
        CHECK(!clock.Due(9999) && clock.Due(10000));
        clock.Fired(10000, 20000);
        CHECK(clock.DueMs() == 30000 && !clock.Due(29999) && clock.Due(30000));
        // A beat held back (a cast in progress) stays due; the next one is never in the past.
        clock.Fired(75000, 20000);
        CHECK(clock.DueMs() == 95000);
        clock.Stop();
        CHECK(!clock.Due(1000000) && !clock.On());
    }

    return Report("sm_kell_test");
}
