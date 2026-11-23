// Host tests for LokseyLogic.h (D5: Houndmaster Loksey, his Tracking Hounds and the Kennel Pups).
// The slice and the arena (WP-S0's), the rounds' order, the pup cap, the Mark trail's plan and timing against its
// round, the marker offsets, the Heel's pick, the Fetch ring and its throw, the tuning table, and the room's points.
#include "DungeonKitLogic.h"
#include "LokseyLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <string>

using namespace ScarletMonasteryRework;
using namespace SmLoksey;

namespace
{
    float Dist(Vec2 a, Vec2 b)
    {
        return DungeonKit::Distance(a, b);
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation; contiguous from the slice's first id.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 212540 && kSpellSlice.last == 212569);
        std::uint32_t const spells[] = { SPELL_LK_RELEASE_CAST, SPELL_LK_WHISTLE, SPELL_LK_SCENT, SPELL_LK_SCENT_FLASH,
            SPELL_LK_HOUND_LEAP, SPELL_LK_WHIPPED_FRENZY, SPELL_LK_LOKSEY_FRENZY, SPELL_LK_CORRECTION_CAST,
            SPELL_LK_CORRECTION_HIT, SPELL_LK_CORRECTION_TANK, SPELL_LK_FETCH_THROW, SPELL_LK_COWED };
        std::uint32_t expected = kSpellSlice.first;
        for (std::uint32_t const id : spells)
        {
            CHECK(id == expected);
            CHECK(kSpellSlice.Contains(id));
            ++expected;
        }
        CHECK(kLastSpell == expected - 1);
        // The creature ids are S0's (300908 hound, 300909 pup) and sit in the dungeon's reservation.
        CHECK(NPC_SM_TRACKING_HOUND == 300908 && NPC_SM_KENNEL_PUP == 300909);
        CHECK(kCreaturesReservation.Contains(NPC_SM_TRACKING_HOUND));
        CHECK(kCreaturesReservation.Contains(NPC_SM_KENNEL_PUP));
        // The texts: groups 1-4 are his new lines (0 is stock); the S0 range for him is 0-4, 0 stock.
        bool found = false;
        for (TextRange const& r : kTextRanges)
            if (r.entry == NPC_LOKSEY)
            {
                found = true;
                CHECK(r.first == 0 && r.last == EMOTE_LOKSEY_FETCH && r.firstNew == 1);
            }
        CHECK(found);
        CHECK(SAY_LOKSEY_RELEASE == 0 && EMOTE_LOKSEY_MARK == 1 && EMOTE_LOKSEY_HEEL == 2 && EMOTE_LOKSEY_FRENZY == 3
            && EMOTE_LOKSEY_FETCH == 4);
        // Wave 1, slot 2.
        CHECK(BOSS_LOKSEY == 2);
        CHECK(!IsWave2Boss(BOSS_LOKSEY));
    }

    void TestArena()
    {
        // Loksey spawns kLokseySpawn, inside the arena and on the bots' floor; so do his hounds and both pup entries.
        CHECK(LokseyArena().Contains(kLokseySpawn.XY(), kLokseySpawn.z));
        CHECK(ArenaFor(BOSS_LOKSEY).Contains(kLokseySpawn.XY(), kLokseySpawn.z));
        DungeonKit::Arena const floor = BotFloor();
        CHECK(floor.Contains(kLokseySpawn.XY(), kLokseySpawn.z));
        for (Point4 const& hound : kPackSpots)
        {
            CHECK(LokseyArena().Contains(hound.XY(), hound.z));
            CHECK(floor.Contains(hound.XY(), hound.z));
            // "within 4 yd of him" (LIB: the three hounds stand 3.4-4 yd from him)
            CHECK(Dist(hound.XY(), kLokseySpawn.XY()) <= 4.5f);
        }
        for (Point3 const& entry : kHallEntries)
        {
            CHECK(LokseyArena().Contains(entry.XY(), entry.z));
            CHECK(floor.Contains(entry.XY(), entry.z));
        }
        // NAVMESH: the entries are 80 and 82 yd from him by the mesh (straight lines 83 and 76), 37 yd from the hall
        // center.
        for (Point3 const& entry : kHallEntries)
            CHECK(Dist(entry.XY(), kLokseySpawn.XY()) > 70.f && Dist(entry.XY(), kLokseySpawn.XY()) < 90.f);
        CHECK(std::fabs(Dist(kHallEntries[0].XY(), kHallCenter.XY()) - 37.f) < 3.f);
        CHECK(std::fabs(Dist(kHallEntries[1].XY(), kHallCenter.XY()) - 37.f) < 3.f);
        CHECK(floor.Contains(kHallCenter.XY(), kHallCenter.z));
        // Pups alternate between the two entries.
        CHECK(PupEntry(0).x == kHallEntries[0].x && PupEntry(1).x == kHallEntries[1].x
            && PupEntry(2).x == PupEntry(0).x);
        // The bots' floor is inside the leash arena: every vertex of every polygon.
        for (std::array<Vec2, 4> const* polygon : { &kAlcovePolygon, &kNeckPolygon, &kHallPolygon })
            for (Vec2 const& v : *polygon)
                CHECK(LokseyArena().Contains({ v.x, v.y }, 19.f));
        // A point in the wall between the alcove and the hall, or beside the neck, is off the floor.
        CHECK(!floor.Contains({ 150.f, -250.f }, 19.f));
        CHECK(!floor.Contains({ 150.f, -275.f }, 19.f));
        // Wrong floor: a point above the band is not on it.
        CHECK(!floor.Contains(kHallCenter.XY(), 40.f));
    }

    void TestRounds()
    {
        // Release, Mark, Heel; heroic adds Fetch; both loop.
        CHECK(NextRound(Round::Release, false) == Round::Mark);
        CHECK(NextRound(Round::Mark, false) == Round::Heel);
        CHECK(NextRound(Round::Heel, false) == Round::Release);
        CHECK(NextRound(Round::Heel, true) == Round::Fetch);
        CHECK(NextRound(Round::Fetch, true) == Round::Release);
        // Normal never reaches Fetch.
        Round r = Round::Release;
        std::set<std::uint8_t> seen;
        for (int i = 0; i < 12; ++i)
        {
            seen.insert(static_cast<std::uint8_t>(r));
            r = NextRound(r, false);
        }
        CHECK(seen == (std::set<std::uint8_t>{ 0, 1, 2 }));
        // The rounds come every 15 s / 12 s: each command every 45 s / 48 s (LIB "First, cooldown"); round 4 only on
        // heroic. The pull is round 1 (Release at 0).
        CHECK(kRoundEveryMs(false) == 15000 && kRoundEveryMs(true) == 12000);
        CHECK(CycleMs(false) == 45000 && CycleMs(true) == 48000);
        CHECK(RoundCount(false) == 3 && RoundCount(true) == 4);
        CHECK(std::string(RoundName(Round::Mark)) == "mark");
    }

    void TestPups()
    {
        // Normal: 3 pups a Release, never more than 6 alive; a Release with 6 up brings none.
        CHECK(PupsToSummon(false, false, 0) == 3);
        CHECK(PupsToSummon(false, false, 3) == 3);
        CHECK(PupsToSummon(false, false, 4) == 2);
        CHECK(PupsToSummon(false, false, 5) == 1);
        CHECK(PupsToSummon(false, false, 6) == 0);
        CHECK(PupsToSummon(false, false, 20) == 0);
        // The cap never exceeds 6 alive, whatever is up.
        for (std::uint32_t alive = 0; alive <= 8; ++alive)
            CHECK(alive + PupsToSummon(false, false, alive) <= std::max(alive, kPupCapNormal));
        // Heroic: 3 when interrupted, 6 when it ran; no cap.
        CHECK(PupsToSummon(true, true, 0) == 3);
        CHECK(PupsToSummon(true, false, 0) == 6);
        CHECK(PupsToSummon(true, false, 30) == 6);
        CHECK(PupsToSummon(true, true, 30) == 3);
        // The interrupt halves the pack.
        CHECK(PupsToSummon(true, true, 0) * 2 == PupsToSummon(true, false, 0));
    }

    void TestTrail()
    {
        // The spec: three hounds make a 1.5 s trail, three hounds and six pups 4.5 s (a marker every 0.5 s).
        CHECK(TrailDropMs(3, 1) == 1500);
        CHECK(TrailDropMs(9, 1) == 4500);
        std::vector<TrailSlot> const nine = PlanTrail(9, 1);
        CHECK(nine.size() == 9);
        for (std::uint32_t i = 0; i < 9; ++i)
        {
            CHECK(nine[i].dog == i);
            CHECK(nine[i].carrier == 0);
            CHECK(nine[i].atMs == i * 500);
        }
        CHECK(nine.back().atMs == 4000);                // the 9th marker drops 4 s in; it lands 1.5 s later
        CHECK(TrailMs(9, 1) == 4000 + 1500);
        CHECK(TrailMs(3, 1) == 1000 + 1500);
        // Roughly 30 yd of running at 7 yd/s over the 4.5 s trail (the spec's number).
        CHECK(std::fabs(static_cast<float>(TrailDropMs(9, 1)) / 1000.f * 7.f - 30.f) < 2.f);
        // Two carriers (heroic): the dogs alternate, each trail 0.5 s apart; the trails run in parallel.
        std::vector<TrailSlot> const two = PlanTrail(9, 2);
        CHECK(two.size() == 9);
        for (TrailSlot const& s : two)
        {
            CHECK(s.carrier == s.dog % 2);
            CHECK(s.atMs == (s.dog / 2) * 500);
        }
        CHECK(TrailMs(9, 2) == 4 * 500 + 1500);         // 5 markers on the longest trail
        CHECK(TrailMs(9, 2) < TrailMs(9, 1));
        // A missed Release adds six pups: three more markers on each of two trails.
        CHECK(TrailMs(9 + 6, 2) - TrailMs(9, 2) == 1500);
        // No dog, no carrier: nothing leaps.
        CHECK(PlanTrail(0, 1).empty());
        CHECK(PlanTrail(5, 0).empty());
        CHECK(TrailMs(0, 1) == 0 && TrailMs(4, 0) == 0 && TrailDropMs(0, 1) == 0 && TrailDropMs(4, 0) == 0);
        // Every slot of every plan is a dog of the list and a carrier of the set.
        for (std::uint32_t dogs = 1; dogs <= 20; ++dogs)
            for (std::uint32_t carriers = 1; carriers <= 3; ++carriers)
            {
                std::vector<TrailSlot> const plan = PlanTrail(dogs, carriers);
                CHECK(plan.size() == dogs);
                std::set<std::uint32_t> used;
                std::uint32_t last = 0;
                for (TrailSlot const& s : plan)
                {
                    CHECK(s.carrier < carriers);
                    used.insert(s.dog);
                    last = std::max(last, s.atMs);
                }
                CHECK(used.size() == dogs);
                CHECK(last + kMarkerWarnMs == TrailMs(dogs, carriers));
                // The trail fits its round next to the 5 s Scent for the pack sizes the spec's caps allow.
                if (carriers == 1 && dogs <= 3 + kPupCapNormal)
                    CHECK(kScentMs + TrailMs(dogs, carriers) < kRoundEveryMs.normal);
                if (carriers == 2 && dogs <= 3 + 12)
                    CHECK(kScentMs + TrailMs(dogs, carriers) < kRoundEveryMs.heroic);
            }
        CHECK(kScentCarriers(false) == 1 && kScentCarriers(true) == 2);
        // STAGE-R-1-LIB Q1: the tank never carries the Scent (the Bait keeps the carrier off Loksey, on the tank).
        CHECK(kScentTankExempt);
        {
            DungeonKit::PickRule rule;
            rule.nonTank = kScentTankExempt;
            rule.tankIfAlone = false;
            std::vector<DungeonKit::PickCandidate> tankOnly(1);
            tankOnly[0].tank = true;
            CHECK(!DungeonKit::PickFrom(tankOnly, rule, [](std::size_t) { return std::size_t(0); }).has_value());
            std::vector<DungeonKit::PickCandidate> two(2);
            two[0].tank = true;
            auto const pick = DungeonKit::PickFrom(two, rule, [](std::size_t) { return std::size_t(0); });
            CHECK(pick.has_value() && *pick == 1);
        }
        // F-4b: nor the healer (the 22 yd walk took her out of the tank's line of sight through the alcove's neck).
        CHECK(kScentHealerExempt);
        {
            DungeonKit::PickRule rule;
            rule.nonTank = kScentTankExempt;
            rule.tankIfAlone = false;
            rule.nonHealer = kScentHealerExempt;
            DungeonKit::PickCandidate tank;
            tank.id = 1;
            tank.tank = true;
            DungeonKit::PickCandidate healer;
            healer.id = 2;
            healer.healer = true;
            DungeonKit::PickCandidate dps;
            dps.id = 3;
            for (std::uint32_t r = 0; r < 12; ++r)
            {
                std::vector<DungeonKit::PickCandidate> const group{ tank, healer, dps };
                auto const pick = DungeonKit::PickFrom(group, rule, [r](std::size_t n) { return std::size_t(r) % n; });
                CHECK(pick.has_value() && group[*pick].id == 3);
            }
            // Heroic wants two: with one dps only that one carries.
            std::vector<DungeonKit::PickCandidate> const group{ tank, healer, dps };
            CHECK(DungeonKit::PickDistinctFrom(group, rule, kScentCarriers(true), [](std::size_t) { return 0u; })
                .size() == 1u);
            // Tank and healer alone: no Mark (the tank's own fallback).
            std::vector<DungeonKit::PickCandidate> const pair{ tank, healer };
            CHECK(!DungeonKit::PickFrom(pair, rule, [](std::size_t) { return std::size_t(0); }).has_value());
        }
        CHECK(kScentMs == 5000 && kMarkerWarnMs == 1500 && kMarkerEveryMs == 500);
        // A dog takes off 0.5 s before its marker resolves (1 s after it drops).
        CHECK(kMarkerWarnMs - kLeapFlightMs == 1000);
    }

    void TestMarkerSpot()
    {
        Vec2 const carrier{ 170.f, -270.f };
        // u1 = 0: on the carrier; u1 = 1: 2 yd away; always 0-2 yd, at the bearing u2 * 2 pi.
        CHECK(Dist(MarkerSpot(carrier, 0.f, 0.37f), carrier) < 0.001f);
        CHECK(std::fabs(Dist(MarkerSpot(carrier, 1.f, 0.37f), carrier) - kMarkerOffsetMaxYd) < 0.001f);
        float lo = 99.f;
        float hi = 0.f;
        std::set<int> octants;
        for (int i = 0; i <= 100; ++i)
            for (int j = 0; j < 100; ++j)
            {
                float const u1 = static_cast<float>(i) / 100.f;
                float const u2 = static_cast<float>(j) / 100.f;
                Vec2 const spot = MarkerSpot(carrier, u1, u2);
                float const d = Dist(spot, carrier);
                lo = std::min(lo, d);
                hi = std::max(hi, d);
                float const bearing = std::atan2(spot.y - carrier.y, spot.x - carrier.x);
                int const octant = static_cast<int>(std::floor((bearing + DungeonKit::kPi) / (DungeonKit::kPi / 4.f)));
                octants.insert(octant % 8);
            }
        CHECK(lo < 0.01f && hi <= kMarkerOffsetMaxYd + 0.001f);
        CHECK(octants.size() == 8);                     // any direction: the trail cannot be walked on a fixed line
        // The carrier is always inside its own marker, so it has to leave: 5 yd + 2 yd = at most 7 yd to get clear of
        // the marker's far edge, about 1 s at 7 yd/s, inside the 1.5 s warning (LIB "Space math").
        CHECK(kMarkerRadiusYd + kMarkerOffsetMaxYd == 7.f);
        CHECK((kMarkerRadiusYd + kMarkerOffsetMaxYd) / 7.f <= static_cast<float>(kMarkerWarnMs) / 1000.f);
        // Out-of-range uniforms clamp.
        CHECK(std::fabs(Dist(MarkerSpot(carrier, 5.f, 0.f), carrier) - kMarkerOffsetMaxYd) < 0.001f);
        CHECK(Dist(MarkerSpot(carrier, -3.f, 0.f), carrier) < 0.001f);
    }

    void TestWhip()
    {
        CHECK(WhippedDog({}) == -1);
        CHECK(WhippedDog({ 800 }) == 0);
        // The hound (3,000) beats the pups (800); a half-health hound loses to a healthier one.
        CHECK(WhippedDog({ 800, 3000, 800 }) == 1);
        CHECK(WhippedDog({ 800, 1500, 800, 2900 }) == 3);
        // A tie goes to the first of the list (the script sorts the dogs by guid).
        CHECK(WhippedDog({ 800, 800, 800 }) == 0);
        CHECK(WhippedDog({ 800, 3000, 3000 }) == 1);
        // The Heel ring: every dog on its own bearing, 3 yd from him.
        Vec2 const center{ 150.f, -260.f };
        std::set<std::pair<int, int>> spots;
        for (std::uint32_t i = 0; i < 9; ++i)
        {
            Vec2 const s = HeelSpot(center, i, 9);
            CHECK(std::fabs(Dist(s, center) - kHeelRadiusYd) < 0.001f);
            spots.insert({ static_cast<int>(std::lround(s.x * 10.f)), static_cast<int>(std::lround(s.y * 10.f)) });
        }
        CHECK(spots.size() == 9);
        CHECK(std::fabs(Dist(HeelSpot(center, 0, 0), center) - kHeelRadiusYd) < 0.001f);   // no dog: no division by 0
        // The whip lands before a dog gives up, and a normal frenzy never outlasts the 45 s cycle.
        CHECK(kHeelRunMs < kHeelGiveUpMs);
        CHECK(kFrenzyNormalMs == 30000 && kLokseyFrenzyMs == 15000);
        CHECK(kFrenzyNormalMs < CycleMs(false));
        CHECK(kWhippedFrenzyPct == 50 && kLokseyFrenzyHastePct == 30);
    }

    void TestFetch()
    {
        // The ring: 15-25 yd, the edges count.
        CHECK(!FetchRangeOk(14.9f) && FetchRangeOk(15.f) && FetchRangeOk(20.f) && FetchRangeOk(25.f)
            && !FetchRangeOk(25.1f));
        // The throw leaves so the stick lands as the 3 s circle resolves: a near spot has the shorter flight, so the
        // throw leaves later.
        CHECK(FetchLaunchDelayMs(15.f) == 3000 - 1500);
        CHECK(FetchLaunchDelayMs(25.f) == 3000 - 2500);
        CHECK(FetchLaunchDelayMs(15.f) > FetchLaunchDelayMs(25.f));
        CHECK(FetchLaunchDelayMs(500.f) == 0);          // a flight longer than the warning leaves at once
        for (float d = kFetchMinYd; d <= kFetchMaxYd; d += 0.5f)
            CHECK(FetchLaunchDelayMs(d) + static_cast<std::uint32_t>(d / kFetchMissileSpeed * 1000.f + 0.5f) <= 3001);
        // The circle is 3 yd; the spot needs 3 yd of floor all round it.
        CHECK(kFetchRadiusYd == 3.f && kFetchEdgeMarginYd == 3.f);
        DungeonKit::Arena const floor = BotFloor();
        CHECK(FetchSpotOnFloor(floor, kHallCenter.XY(), kHallCenter.z));
        CHECK(FetchSpotOnFloor(floor, { 180.f, -260.f }, 19.f));
        // Against a wall: the hall's wall is x 208: a spot 1 yd from it fails; 4 yd from it passes.
        CHECK(!FetchSpotOnFloor(floor, { 207.f, -275.f }, 19.f));
        CHECK(FetchSpotOnFloor(floor, { 204.f, -275.f }, 19.f));
        // The alcove (26 x 15) has room for the ring on its middle row.
        CHECK(FetchSpotOnFloor(floor, { 135.f, -257.f }, 18.6f));
        // The neck is 5 yd wide (y -263 to -258 in the polygon): no 3 yd margin fits.
        CHECK(!FetchSpotOnFloor(floor, { 150.f, -260.5f }, 19.f));
        // Off the floor entirely, or on the wrong level.
        CHECK(!FetchSpotOnFloor(floor, { 100.f, -260.f }, 19.f));
        CHECK(!FetchSpotOnFloor(floor, kHallCenter.XY(), 30.f));
        // From his spawn in the alcove, the 15-25 yd ring reaches floor inside the alcove: some spot exists (the
        // script's fallback is the hall center when none does).
        int usable = 0;
        for (int i = 0; i < 360; i += 5)
            for (float d : { 15.f, 20.f, 25.f })
            {
                float const bearing = static_cast<float>(i) * DungeonKit::kPi / 180.f;
                Vec2 const spot = DungeonKit::Advance(kLokseySpawn.XY(), bearing, d);
                if (FetchSpotOnFloor(floor, spot, kLokseySpawn.z))
                    ++usable;
            }
        CHECK(usable > 0);
        // From the hall (Loksey tanked at the hall's west side), the ring has plenty of floor.
        int hall = 0;
        Vec2 const tanked{ 170.f, -262.f };
        for (int i = 0; i < 360; i += 5)
            for (float d : { 15.f, 20.f, 25.f })
            {
                Vec2 const spot = DungeonKit::Advance(tanked, static_cast<float>(i) * DungeonKit::kPi / 180.f, d);
                if (FetchSpotOnFloor(floor, spot, 19.f))
                    ++hall;
            }
        CHECK(hall > 100);
    }

    void TestTuning()
    {
        // The spec's table: Mark 35% / 45%, Correction 30% / 40% and the tank 20% / 30%, 90 degrees, 8 yd, 2 s.
        CHECK(kMarkLandingPct(false) == 35.f && kMarkLandingPct(true) == 45.f);
        CHECK(kCorrectionPct(false) == 30.f && kCorrectionPct(true) == 40.f);
        CHECK(kCorrectionTankPct(false) == 20.f && kCorrectionTankPct(true) == 30.f);
        CHECK(kCorrectionAngleDeg == 90.f && kCorrectionLengthYd == 8.f && kCorrectionCastMs == 2000);
        CHECK(kCorrectionFirstMs == 6000 && kCorrectionEveryMs == 10000);
        // Normal: Correction (30%) and Mark (35%) sit inside the 40% ladder.
        CHECK(kCorrectionPct.normal <= 40.f && kMarkLandingPct.normal <= 40.f);
        // Health (handoff 3.6): 38k / 210k, hound 3k / 15k, pup 800 / 4k.
        CHECK(kBossHealth(false) == 38000 && kBossHealth(true) == 210000);
        CHECK(kHoundHealth(false) == 3000 && kHoundHealth(true) == 15000);
        CHECK(kPupHealth(false) == 800 && kPupHealth(true) == 4000);
        // The fight (LIB "Tuning"): normal 38k + 3 hounds + two packs of 3 pups against 623 effective DPS is ~83 s.
        std::uint32_t const normalHealth = kBossHealth(false) + 3 * kHoundHealth(false) + 2 * 3 * kPupHealth(false);
        CHECK(normalHealth == 38000 + 9000 + 4800);
        CHECK(std::lround(static_cast<double>(normalHealth) / 623.0) == 83);
        // Heroic: 210k + 45k (3 hounds) + 24k of interrupted pups (6 x 4k) against 3,145 is ~89 s.
        std::uint32_t const heroicHealth = kBossHealth(true) + 3 * kHoundHealth(true) + 6 * kPupHealth(true);
        CHECK(heroicHealth == 210000 + 45000 + 24000);
        CHECK(std::lround(static_cast<double>(heroicHealth) / 3145.0) == 89);
        // Kill order: the frenzied dog first, pups before hounds, the tank picks up when nothing else needs it.
        CHECK(kFrenziedKillPriority > kPupKillPriority && kPupKillPriority > kHoundKillPriority);
        CHECK(kHoundKillPriority > 0 && kTankDogPriority < 0);
        CHECK(kReleaseKickPriority > 0 && kFrenzyPurgePriority > 0);
        // Tags are the mechanic numbers; the Scent's Bait is its own.
        CHECK(TAG_LK_MARK_LANDING == 3 && TAG_LK_CORRECTION == 5 && TAG_LK_FETCH == 6);
        CHECK(TAG_LK_SCENT != TAG_LK_MARK_LANDING);
        CHECK(kReleaseCastMs == 2500 && kFetchCowedTakenPct == 25 && kCowedMs == 6000);
        CHECK(kHoundCount == 3 && kPackSpots.size() == kHoundCount);
        // Walking away: the Scent's far distance is inside the hall (the 58 yd wall) and clear of a marker's reach.
        CHECK(kScentFarYd > kMarkerRadiusYd + kMarkerOffsetMaxYd);
        CHECK(kScentFarYd < 58.f);
    }
}

int main()
{
    TestSlice();
    TestArena();
    TestRounds();
    TestPups();
    TestTrail();
    TestMarkerSpot();
    TestWhip();
    TestFetch();
    TestTuning();
    return Report("sm_loksey_test");
}
