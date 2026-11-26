// Host tests for StairLogic.h and SezzzizLogic.h (D4b): the Stair (stage 2 of the Pyramid) and the Altar (stage 3).
// The slice, the waves and the send pace, the barrel lane (its true width, its slope, the tiles that cover it), the
// bots' hold on the landing, the crew's places, the add sets and their cap, the Blood Offering's picks and numbers,
// the Altar's arena.
#include "SezzzizLogic.h"
#include "StairLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <set>
#include <vector>

using namespace ZulFarrakRework;

namespace
{
    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestSlice()
    {
        using namespace ZfStair;
        using namespace ZfAltar;
        CHECK(kSpellsReservation.Contains(ZfStair::kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(ZfStair::kSpellSlice.last));
        CHECK(ZfAltar::kSpellSlice.first == ZfStair::kSpellSlice.first);
        std::vector<std::uint32_t> const stair{ SPELL_BARREL_HIT, SPELL_KNOCKDOWN, SPELL_BARREL_BLAST,
            SPELL_BARREL_TROLL, SPELL_BERSERKER_BLEED, SPELL_BERSERKER_LOOK, SPELL_TRAMPLING, SPELL_CURSE_OF_BLOOD,
            SPELL_SANDFURY_HEX, SPELL_HEXED, SPELL_LAVA_SPOUT, SPELL_LAVA_TOTEM_BAR, SPELL_LAVA_GLOW };
        std::vector<std::uint32_t> const altar{ SPELL_BLOOD_OFFERING, SPELL_BLOOD_OFFERING_H,
            SPELL_BLOOD_OFFERING_HIT, SPELL_BLOOD_FRENZY, SPELL_BLOOD_FRENZY_H, SPELL_SCREAM_BAR, SPELL_SCREAM_FEAR,
            SPELL_BLOOD_OFFERING_BEAM };
        std::set<std::uint32_t> all;
        for (std::uint32_t id : stair)
        {
            CHECK(kSpellsStair.Contains(id) && id < kAltarSpellBase);
            all.insert(id);
        }
        for (std::uint32_t id : altar)
        {
            CHECK(kSpellsStair.Contains(id) && id >= kAltarSpellBase);
            all.insert(id);
        }
        CHECK(all.size() == stair.size() + altar.size());
        // consecutive from each half's first id
        CHECK(stair.back() == kSpellsStair.first + stair.size() - 1);
        CHECK(altar.back() == kAltarSpellBase + altar.size() - 1);
    }

    void TestWaves()
    {
        using namespace ZfStair;
        for (std::uint32_t wave = 1; wave <= 3; ++wave)
        {
            std::uint32_t doctors = 0, hexers = 0, berserkers = 0, fodder = 0, bosses = 0, stock = 0;
            for (std::size_t i : WaveIndexes(wave))
            {
                std::uint32_t const e = WaveEntry(i);
                if (e == NPC_ZF_SANDFURY_WITCH_DOCTOR)
                    ++doctors;
                else if (e == NPC_ZF_SANDFURY_HEXMASTER)
                    ++hexers;
                else if (e == NPC_ZF_SANDFURY_BERSERKER)
                    ++berserkers;
                else if (e == NPC_SANDFURY_SLAVE || e == NPC_SANDFURY_DRUDGE)
                    ++fodder;
                else if (e == NPC_SEZZZIZ || e == NPC_NEKRUM)
                    ++bosses;
                else
                    ++stock;
            }
            CHECK(stock == 0);  // no Cretin, Acolyte or Zealot is left (SP mechanic 4)
            if (wave == 1)
                CHECK(doctors == 4 && hexers == 4 && berserkers == 4 && fodder == 11 && bosses == 0);
            if (wave == 2)
                CHECK(doctors == 4 && hexers == 4 && berserkers == 4 && fodder == 12 && bosses == 0);
            if (wave == 3)
                CHECK(doctors == 0 && hexers == 1 && berserkers == 0 && fodder == 4 && bosses == 2);
        }
        CHECK(kWaveSpawns[kExtraDoctorIndex].wave == 1 && kWaveSpawns[kExtraDoctorIndex].entry == NPC_SANDFURY_SLAVE);
        CHECK(WaveEntry(kWaveSpawns.size()) == 0);
        CHECK(IsSpecialist(NPC_ZF_SANDFURY_BERSERKER) && !IsSpecialist(NPC_SANDFURY_SLAVE));

        // the send pace: 3, 4, 5, 6 and the rest, one every 8 s, the first at once
        auto plan = [](std::uint32_t total)
        {
            std::vector<std::uint32_t> sizes;
            std::uint32_t left = total;
            for (std::uint32_t s = 0; left; ++s)
            {
                std::uint32_t const n = SendGroupSize(s, left);
                sizes.push_back(n);
                left -= n;
            }
            return sizes;
        };
        CHECK((plan(23) == std::vector<std::uint32_t>{ 3, 4, 5, 6, 5 }));
        CHECK((plan(24) == std::vector<std::uint32_t>{ 3, 4, 5, 6, 6 }));
        CHECK((plan(5) == std::vector<std::uint32_t>{ 3, 2 }));
        CHECK(SendsDue(0) == 1 && SendsDue(7999) == 1 && SendsDue(8000) == 2 && SendsDue(32000) == 5);
        // the whole wave is on its way 32 s in (SP: about 40 s a wave at target)
        CHECK(SendsDue(4 * Tune::kSendEveryMs) == plan(23).size());

        // the wave's book-keeping
        std::vector<ClimberState> climbers(6, ClimberState::Waiting);
        CHECK(!WaveCleared(climbers) && CountWaiting(climbers) == 6);
        std::vector<std::size_t> const first = NextSend(climbers, 3);
        CHECK(first.size() == 3 && first[0] == 0 && first[2] == 2);
        for (std::size_t i : first)
            climbers[i] = ClimberState::Sent;
        CHECK(CountWaiting(climbers) == 3 && NextSend(climbers, 5).size() == 3 && NextSend(climbers, 5)[0] == 3);
        for (ClimberState& c : climbers)
            c = ClimberState::Gone;
        CHECK(WaveCleared(climbers));
        climbers[4] = ClimberState::Sent;
        CHECK(!WaveCleared(climbers));
    }

    void TestLane()
    {
        using namespace ZfStair;
        CHECK(Near(StairZAt(1227.f), 13.7f) && Near(StairZAt(1262.f), 40.f) && Near(StairZAt(1200.f), 13.7f));
        CHECK(StairZAt(1240.f) > StairZAt(1230.f));
        // the true width: 28 at the foot to 12 at the lip (section 3.8)
        StairEdges const foot = StairEdgesAt(1226.f);
        StairEdges const lip = StairEdgesAt(1261.f);
        CHECK(Near(foot.right - foot.left, 28.f) && Near(lip.right - lip.left, 12.f));
        CHECK(StairEdgesAt(1244.f).right - StairEdgesAt(1244.f).left < 20.f);

        Arena const stair = StairArena();
        Arena const landing = LandingArena();
        Arena const top = PyramidTopArena();
        Arena const hold = HoldArena();
        std::array<LaneTile, Tune::kLaneTiles> const tiles = LaneTiles();
        std::uint32_t inLane = 0;
        for (float y = 1227.f; y <= 1259.f; y += 0.5f)
        {
            StairEdges const e = StairEdgesAt(y);
            for (float f = 0.02f; f < 1.f; f += 0.12f)
            {
                float const x = e.left + f * (e.right - e.left);
                float const z = StairZAt(y);
                CHECK(InBarrelLane(x, y, z));
                ++inLane;
                // on the stair's arena, never on the landing or the bots' hold
                CHECK(stair.Contains({ x, y }, z));
                CHECK(!hold.Contains({ x, y }, z));
                // some tile covers it
                bool covered = false;
                for (LaneTile const& t : tiles)
                    if (y >= t.from.y - 0.01f && y <= t.to.y + 0.01f
                        && std::fabs(x - t.from.x) <= t.width / 2.f + 0.01f)
                        covered = true;
                CHECK(covered);
            }
            // beside the run (the side ledges) and off the slope's height: not on the lane
            CHECK(!InBarrelLane(e.left - 1.f, y, StairZAt(y)));
            CHECK(!InBarrelLane(e.right + 1.f, y, StairZAt(y)));
            CHECK(!InBarrelLane((e.left + e.right) / 2.f, y, StairZAt(y) + Tune::kLaneZBandYd + 1.f));
        }
        CHECK(inLane > 400);
        // the lane's ends: the landing from y 1260 is never hit; the plaza below the foot neither
        CHECK(!InBarrelLane(1887.5f, 1260.f, 40.f) && !InBarrelLane(1887.5f, 1259.1f, StairZAt(1259.1f)));
        CHECK(!InBarrelLane(1888.f, 1226.9f, 13.7f) && !InBarrelLane(1888.f, 1215.f, 9.3f));
        CHECK(!InBarrelLane(kLanding.x, kLanding.y, kLanding.z));
        CHECK(landing.Contains(kLanding.XY(), kLanding.z) && !InBarrelLane(kTotemLip.x, kTotemLip.y, kTotemLip.z));

        // the tiles: contiguous from 1227 to 1259, narrowing up the stair, four drawn
        CHECK(Near(tiles.front().from.y, kStairLaneYMin) && Near(tiles.back().to.y, kStairLaneYMax, 0.05f));
        std::uint32_t drawn = 0;
        for (std::size_t i = 0; i < tiles.size(); ++i)
        {
            if (i + 1 < tiles.size())
            {
                CHECK(Near(tiles[i].to.y, tiles[i + 1].from.y));
                CHECK(tiles[i].width >= tiles[i + 1].width);
            }
            CHECK(tiles[i].to.z > tiles[i].from.z && tiles[i].width >= 12.f && tiles[i].width <= 28.f);
            CHECK(tiles[i].to.y - tiles[i].from.y < 3.f);       // each strip under 3 yd up the slope
            drawn += tiles[i].drawn ? 1 : 0;
        }
        CHECK(drawn == 4);

        // the stock wave points: none on the lane (a barrel never hits a troll still waiting); the eight on the ramp's
        // foot are short of the stair's polygon too (S0's note: they sit 2.3 to 4.3 yd up the ramp, kept as they are)
        std::uint32_t rampFoot = 0;
        for (WaveSpawn const& w : kWaveSpawns)
        {
            CHECK(!InBarrelLane(w.at.x, w.at.y, w.at.z));
            CHECK(w.at.y < kStairLaneYMin);
            if (w.at.z > 11.f)
            {
                ++rampFoot;
                CHECK(!stair.Contains(w.at.XY(), w.at.z));
            }
        }
        CHECK(rampFoot > 0);

        // the barrel: lit at the lip on the landing's edge, off at the foot; the lane stalker on the top
        CHECK(kBarrelLit.y > kStairLaneYMax && kBarrelFoot.y < kStairLaneYMin);
        CHECK(top.Contains(kLaneStalker.XY(), kLaneStalker.z));
        CHECK(kKnockSource.y > kStairLaneYMax);
        CHECK(Near(TrollBarrelDamage(5346.f), 2673.f));
        CHECK(Tune::kBarrelPct.normal == 40.f && Tune::kBarrelPct.heroic == 50.f);
        CHECK(Tune::kBarrelEveryMs.Get(false) == 15000 && Tune::kBarrelEveryMs.Get(true) == 12000);
    }

    void TestHoldAndCrew()
    {
        using namespace ZfStair;
        Arena const hold = HoldArena();
        Arena const landing = LandingArena();
        Arena const top = PyramidTopArena();
        // the hold: the landing and the top, the stair's mouth pulled back to y 1261
        CHECK(hold.Contains(kLanding.XY(), kLanding.z));
        CHECK(hold.Contains(kExecutionerSpawn.XY(), kExecutionerSpawn.z));
        CHECK(hold.Contains(kTotemLip.XY(), kTotemLip.z));
        CHECK(!hold.Contains({ 1887.5f, 1260.5f }, 40.f) && top.Contains({ 1887.5f, 1260.5f }, 40.f));
        std::uint32_t moved = 0;
        auto const polygon = HoldPolygon();
        for (std::size_t i = 0; i < polygon.size(); ++i)
            if (polygon[i].y != kPyramidTopPolygon[i].y)
                ++moved;
        CHECK(moved == 2);
        // the crew's places on the Stair: on the landing and on the hold; the stock ones too
        for (std::uint32_t m = 0; m < kCrewCount; ++m)
        {
            Point3 const p = kCrewStairSpots[m] ? *kCrewStairSpots[m] : kCrewStairPoints[m];
            CHECK(landing.Contains(p.XY(), p.z));
            CHECK(hold.Contains(p.XY(), p.z));
            CHECK(!InBarrelLane(p.x, p.y, p.z) && p.y > Tune::kCrewLeashY);
        }
        CHECK(!kCrewStairSpots[CREW_BLY] && !kCrewStairSpots[CREW_WEEGLI]);
        CHECK(kCrewStairSpots[CREW_RAVEN] && kCrewStairSpots[CREW_ORO] && kCrewStairSpots[CREW_MURTA]);
        // the fighters on the platform stand farther from the lip than Bly
        CHECK(kCrewStairSpots[CREW_ORO]->y > kCrewStairPoints[CREW_BLY].y);
    }

    void TestSpecialists()
    {
        using namespace ZfStair;
        CHECK(ChargeRange(8.f) && ChargeRange(25.f) && !ChargeRange(7.9f) && !ChargeRange(25.1f));
        CHECK(!HexTurnsToFrog(4) && HexTurnsToFrog(5));
        CHECK(Tune::kHexStackMs * (Tune::kHexMaxStacks - 1) == 16000);      // a frog 16 s after the first stack
        CHECK(Tune::kBleedTickHundredths * (Tune::kBleedMs / Tune::kBleedTickMs) == 2400);   // 24% in all
        CHECK(Tune::kChargeFirstMs < Tune::kChargeMinMs && Tune::kCurseFirstMs < Tune::kCurseMinMs);
        CHECK(Tune::kTotemFirstMs < Tune::kTotemEveryMs && Tune::kTotemArmMs < Tune::kTotemLifeMs);
        CHECK(Tune::kCasterRangeYd < Tune::kCurseRangeYd);
    }

    // R-1-B MJ-1: a climbing caster stops in melee reach of the landing hold's mouth. Model: its target on the stair's
    // axis at `targetY`, the caster straight down the axis at its chase distance (range + both hitboxes, 1.5 yd each)
    // on the stair's slope (or the landing); a melee bot on the hold's mouth reaches 5 yd (NOMINAL_MELEE_RANGE).
    float CasterToMouthYd(float range, float targetY)
    {
        using namespace ZfStair;
        float const want = range + 3.f;
        float const tz = StairZAt(targetY);
        float y = targetY;
        while (y > kStairLaneYMin)
        {
            float const dy = targetY - y;
            float const dz = tz - StairZAt(y);
            if (std::sqrt(dy * dy + dz * dz) >= want)
                break;
            y -= 0.05f;
        }
        float const my = kHoldMouthY - y;
        float const mz = StairZAt(kHoldMouthY) - StairZAt(y);
        return y >= kHoldMouthY ? 0.f : std::sqrt(my * my + mz * mz);
    }

    void TestClimberCasters()
    {
        using namespace ZfStair;
        CHECK(CasterRange(false) == Tune::kCasterRangeYd && CasterRange(true) == Tune::kClimberCasterRangeYd);
        float constexpr kMeleeYd = 5.f;
        // the old range: mid-lane, out of every held melee bot's reach (fails before the fix)
        CHECK(CasterToMouthYd(Tune::kCasterRangeYd, 1271.f) > 15.f);
        // the climber's range: in reach with its target 4 yd inside the landing (y 1265) or at DC's hold (y 1271)
        CHECK(CasterToMouthYd(CasterRange(true), 1265.f) <= kMeleeYd);
        CHECK(CasterToMouthYd(CasterRange(true), 1271.f) <= kMeleeYd);
        CHECK(CasterToMouthYd(CasterRange(true), 1275.f) <= kMeleeYd);
        // still on the lane (a barrel's reach) while its target holds the lip
        CHECK(CasterToMouthYd(CasterRange(true), 1261.f) > 0.f);
    }

    // R-1-B MJ-2: a climber that comes no nearer the lip for 15 s is returned once, then removed.
    void TestClimbWatch()
    {
        using namespace ZfStair;
        ClimbWatch w;
        // progress resets the clock
        CHECK(JudgeClimb(w, false, 40.f, 0) == ClimbVerdict::Climbing);
        CHECK(JudgeClimb(w, false, 30.f, 10000) == ClimbVerdict::Climbing);
        CHECK(JudgeClimb(w, false, 29.5f, 24000) == ClimbVerdict::Climbing);    // under 1 yd: no progress
        CHECK(JudgeClimb(w, false, 29.5f, 25000) == ClimbVerdict::Return);      // 15 s since y came nearer
        CHECK(w.strikes == 1 && w.bestYd < 0.f);
        // after the return it starts over from where it stands
        CHECK(JudgeClimb(w, false, 35.f, 25500) == ClimbVerdict::Climbing);
        // fighting or walking home from an evade never counts
        CHECK(JudgeClimb(w, true, 50.f, 60000) == ClimbVerdict::Climbing);
        CHECK(JudgeClimb(w, false, 50.f, 74999) == ClimbVerdict::Climbing);
        CHECK(JudgeClimb(w, false, 50.f, 75000) == ClimbVerdict::Remove);       // the second time: gone
        // a knockback resets the watch
        ClimbWatch k;
        CHECK(JudgeClimb(k, false, 10.f, 0) == ClimbVerdict::Climbing);
        ResetClimb(k);
        CHECK(JudgeClimb(k, false, 30.f, 14000) == ClimbVerdict::Climbing);
        CHECK(JudgeClimb(k, false, 20.f, 28000) == ClimbVerdict::Climbing);
        CHECK(k.strikes == 0);
        // the path's ends: the foot below the lane, the end past it on the landing
        CHECK(kWavePathStart.y < kStairLaneYMin + 2.f && kWavePathEnd.y > kStairLaneYMax);
        CHECK(Tune::kStuckMs > 2 * Tune::kPollMs && Tune::kStuckTries >= 2);
    }

    void TestAltar()
    {
        using namespace ZfAltar;
        // the stock add sets in turn: 2, 2, 3, 4; no Zealot or Acolyte, only the specialists, at the two points
        CHECK(kAddSets[0].size == 2 && kAddSets[1].size == 2 && kAddSets[2].size == 3 && kAddSets[3].size == 4);
        for (AddSet const& set : kAddSets)
            for (std::uint8_t i = 0; i < set.size; ++i)
            {
                CHECK(set.slots[i].entry == NPC_ZF_SANDFURY_BERSERKER
                    || set.slots[i].entry == NPC_ZF_SANDFURY_HEXMASTER);
                CHECK(set.slots[i].point < kSezzzizAddPoints.size());
            }
        CHECK(&AddSetFor(0) == &kAddSets[0] && &AddSetFor(5) == &kAddSets[1] && &AddSetFor(7) == &kAddSets[3]);
        // at most 4 alive
        CHECK(AddsToSummon(4, 0) == 4 && AddsToSummon(4, 1) == 3 && AddsToSummon(3, 3) == 1);
        CHECK(AddsToSummon(2, 4) == 0 && AddsToSummon(2, 9) == 0 && AddsToSummon(2, 0) == 2);

        // Blood Offering: a fighter, never Weegli; each fighter can be picked
        CHECK(!PickOfferingCrew(0, 3));
        CHECK(!PickOfferingCrew(kCrewWeegliBit, 0));
        std::set<std::uint32_t> picked;
        for (std::uint32_t roll = 0; roll < 16; ++roll)
            if (std::optional<std::uint32_t> m = PickOfferingCrew(kCrewAll, roll))
            {
                CHECK(*m != CREW_WEEGLI);
                picked.insert(*m);
            }
        CHECK(picked.size() == 4);
        CHECK(PickOfferingCrew(CrewBit(CREW_ORO) | kCrewWeegliBit, 7) == std::optional<std::uint32_t>(CREW_ORO));
        CHECK(OfferingHeal(95938, false) == 14390 && OfferingHeal(159951, true) == 39987);
        CHECK(FrenzyDamagePct(0) == 0 && FrenzyDamagePct(3) == 150);
        CHECK(FrenzyShownStacks(300) == 255 && FrenzyShownStacks(2) == 2);
        CHECK(Tune::kOfferingCastMs.Get(false) == 3000 && Tune::kOfferingCastMs.Get(true) == 2000);
        CHECK(Tune::kOfferingFirstMs < Tune::kOfferingMinMs && Tune::kOfferingMinMs <= Tune::kOfferingMaxMs);
        // one 10 s interrupter keeps up (SP "paced for one 10 sec interrupter")
        CHECK(Tune::kOfferingMinMs >= 10000);

        // the Altar's arena: the plaza, the ramp's foot and the stair; not the landing
        Arena const altar = AltarArena();
        for (std::size_t i : ZfStair::WaveIndexes(3))
            CHECK(altar.Contains(kWaveSpawns[i].at.XY(), kWaveSpawns[i].at.z));
        for (Point3 const& p : kSezzzizAddPoints)
            CHECK(altar.Contains(p.XY(), p.z));
        for (Point3 const& p : kCrewDescentPoints)
            CHECK(altar.Contains(p.XY(), p.z));
        for (Point3 const& p : kCrewGatherPoints)
            CHECK(altar.Contains(p.XY(), p.z));
        CHECK(altar.Contains(kPlazaCenter.XY(), kPlazaCenter.z) && altar.Contains(kStairFoot.XY(), kStairFoot.z));
        CHECK(!altar.Contains(kLanding.XY(), kLanding.z) && !altar.Contains(kExecutionerSpawn.XY(),
            kExecutionerSpawn.z));
        // the Altar fights inside the Pyramid's wipe region
        for (std::size_t i : ZfStair::WaveIndexes(3))
            CHECK(InPyramidRegion(kWaveSpawns[i].at.XY()));
    }
}

int main()
{
    TestSlice();
    TestWaves();
    TestLane();
    TestHoldAndCrew();
    TestSpecialists();
    TestClimberCasters();
    TestClimbWatch();
    TestAltar();
    return Report("zf_stair_test");
}
