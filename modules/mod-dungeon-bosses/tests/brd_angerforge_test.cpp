// Host tests for AngerforgeLogic.h (D14: General Angerforge and his squads).
// The slice and the arena (WP-S0's), the tuning table against the build spec, the squad plans and the Officer cap, the
// mole spots and the formation around the machine, the six-yard rule, the Commanding Aura's reach, the Medic's heal and
// the kill order, the grenade's marks, and a replay of the fight's timeline against the spec's "about 100 s with 4
// squads" and "about 115 s with 5".
#include "AngerforgeLogic.h"
#include "check.h"
#include <cmath>
#include <set>
#include <vector>

using namespace BlackrockDepthsRework;
using namespace BrdAngerforge;

namespace
{
    float Dist(Point3 const& a, Point3 const& b)
    {
        return DungeonKit::Distance(a.XY(), b.XY());
    }

    void TestSlice()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211300 && kSpellSlice.last == 211329);
        // Contiguous from the slice's first id, every one inside it.
        std::uint32_t const spells[] = { SPELL_AF_MIGHTY_BLOW, SPELL_AF_CLEAVE, SPELL_AF_COMMANDING_AURA,
            SPELL_AF_COMMANDED, SPELL_AF_COMMANDING_SHOUT, SPELL_AF_HEAL, SPELL_AF_GRENADE_MARK,
            SPELL_AF_GRENADE_MARKED, SPELL_AF_GRENADE, SPELL_AF_GRENADE_LOOK, SPELL_AF_MOLE_DEPLOY_LOOK,
            SPELL_AF_MOLE_RETREAT_LOOK };
        std::uint32_t expected = kSpellSlice.first;
        for (std::uint32_t const id : spells)
        {
            CHECK(id == expected);
            CHECK(kSpellSlice.Contains(id));
            ++expected;
        }
        CHECK(kLastSpell == expected - 1);
        // The Mind Blast is the stock spell (outside every custom block).
        CHECK(!kSpellsReservation.Contains(SPELL_STOCK_MIND_BLAST));
        // The creature ids and the object are the ones S0 reserved.
        CHECK(NPC_BRD_SQUAD_OFFICER == 300830 && NPC_BRD_SQUAD_RESERVIST == 300831 && NPC_BRD_SQUAD_MEDIC == 300832);
        CHECK(GO_BRD_MOLE_MACHINE == 301289);
        // His four texts (S0's table: 9033, groups 0-3).
        CHECK(SAY_AF_PULL == 0 && SAY_AF_REINFORCE == 1 && EMOTE_AF_GRENADE == 2 && SAY_AF_DEATH == 3);
    }

    void TestArena()
    {
        // General Angerforge spawns kAngerforgeSpawn, inside the arena.
        CHECK(AngerforgeArena().Contains(kAngerforgeSpawn.XY(), kAngerforgeSpawn.z));
        CHECK(ArenaFor(BOSS_ANGERFORGE).Contains(kAngerforgeSpawn.XY(), kAngerforgeSpawn.z));
        // The four mole spots are on the hall (inside the leash) and on its far side from the drop behind him (the
        // drop is at x < 651: every spot is 11-30 yd north of it).
        for (Point3 const& spot : kMoleSpots)
        {
            CHECK(AngerforgeArena().Contains(spot.XY(), spot.z));
            CHECK(spot.x > 651.f + 10.f);
            CHECK(Dist(spot, Point3{ kAngerforgeSpawn.x, kAngerforgeSpawn.y, kAngerforgeSpawn.z }) > 20.f);
        }
        // NM: 23 to 44 yd from him.
        CHECK(Dist(kMoleSpots[0], kAngerforgeSpawn) > 42.f && Dist(kMoleSpots[0], kAngerforgeSpawn) < 44.f);
        CHECK(Dist(kMoleSpots[1], kAngerforgeSpawn) > 44.f && Dist(kMoleSpots[1], kAngerforgeSpawn) < 46.f);
        CHECK(Dist(kMoleSpots[2], kAngerforgeSpawn) > 22.f && Dist(kMoleSpots[2], kAngerforgeSpawn) < 24.f);
        CHECK(Dist(kMoleSpots[3], kAngerforgeSpawn) > 23.f && Dist(kMoleSpots[3], kAngerforgeSpawn) < 25.f);
        // The spots are at least 15 yd apart (a squad and its machine never overlap another spot).
        for (std::uint32_t a = 0; a < kMoleSpotCount; ++a)
            for (std::uint32_t b = a + 1; b < kMoleSpotCount; ++b)
                CHECK(Dist(kMoleSpots[a], kMoleSpots[b]) > 15.f);
    }

    void TestTuning()
    {
        // The spec's numbers (S3 "Build spec").
        CHECK(kGrenadeMarkedPct.normal == 15.f && kGrenadeMarkedPct.heroic == 25.f);
        CHECK(kGrenadeOthersPct.normal == 25.f && kGrenadeOthersPct.heroic == 40.f);
        CHECK(kGrenadeCount.normal == 2 && kGrenadeCount.heroic == 3);
        CHECK(kGrenadeRadius == 8.f);
        CHECK(kGrenadeWarnMs == 5000);
        CHECK(kGrenadeFirstMs == 15000);
        CHECK(kGrenadeEveryMs.normal == 20000 && kGrenadeEveryMs.heroic == 15000);
        CHECK(kSquadFirstMs == 10000);
        CHECK(kSquadEveryMs.normal == 30000 && kSquadEveryMs.heroic == 25000);
        CHECK(kRumbleMs == 2000 && kMachineWaitMs == 3000);
        CHECK(kOfficerCap == 2);
        CHECK(kCommandingRadiusYd == 15.f && kCommandedDamageTakenPct == -50);
        CHECK(kHealCastMs == 3000 && kHealFirstMs == 6000 && kHealEveryMs == 12000 && kHealPctOfBoss == 5);
        CHECK(kOfficerHealth.normal == 10000 && kOfficerHealth.heroic == 15000);
        CHECK(kReservistHealth.normal == 3000 && kReservistHealth.heroic == 4500);
        CHECK(kMedicHealth.normal == 5000 && kMedicHealth.heroic == 7500);
        // The stock timers of the kept spells.
        CHECK(kMightyBlowFirstMs == 8000 && kMightyBlowEveryMs == 18000);
        CHECK(kCleaveFirstMs == 16000 && kCleaveEveryMs == 9000);
        // The defaults of the unset cells: heroic never below normal; a swing is a share of one row, never a pulse of
        // the group's.
        CHECK(kMightyBlowPct.heroic >= kMightyBlowPct.normal && kMightyBlowPct.normal >= 20.f
            && kMightyBlowPct.heroic <= 30.f);
        CHECK(kCleavePct.heroic >= kCleavePct.normal && kCleavePct.normal >= 10.f && kCleavePct.heroic <= 15.f);
        // The grenade never overlaps the next throw; the carrier's own hit is below the others' (the spec's cells).
        CHECK(kGrenadeWarnMs < kGrenadeEveryMs.heroic);
        CHECK(kGrenadeMarkedPct.normal < kGrenadeOthersPct.normal);
        CHECK(kGrenadeMarkedPct.heroic < kGrenadeOthersPct.heroic);
    }

    void TestSquads()
    {
        // Normal: an Officer and 2 Reservists; every other squad swaps a Reservist for a Medic.
        for (std::uint32_t i = 0; i < 8; ++i)
        {
            SquadPlan const plan = SquadFor(i, false);
            CHECK(plan.officers == 1);
            CHECK(plan.Total() == 3);
            if (i % 2 == 0)
                CHECK(plan.reservists == 2 && plan.medics == 0);
            else
                CHECK(plan.reservists == 1 && plan.medics == 1);
        }
        // Heroic: an Officer, 2 Reservists and a Medic, every squad.
        for (std::uint32_t i = 0; i < 8; ++i)
        {
            SquadPlan const plan = SquadFor(i, true);
            CHECK(plan.officers == 1 && plan.reservists == 2 && plan.medics == 1 && plan.Total() == 4);
        }
        // The entries: Officer first, then the Medic, then the Reservists; exactly the plan.
        for (bool const heroic : { false, true })
            for (std::uint32_t i = 0; i < 4; ++i)
            {
                SquadPlan const plan = SquadFor(i, heroic);
                auto const entries = SquadEntries(plan);
                CHECK(entries[0] == NPC_BRD_SQUAD_OFFICER);
                std::uint32_t officers = 0, reservists = 0, medics = 0;
                for (std::uint32_t n = 0; n < plan.Total(); ++n)
                {
                    officers += entries[n] == NPC_BRD_SQUAD_OFFICER;
                    reservists += entries[n] == NPC_BRD_SQUAD_RESERVIST;
                    medics += entries[n] == NPC_BRD_SQUAD_MEDIC;
                }
                CHECK(officers == plan.officers && reservists == plan.reservists && medics == plan.medics);
                for (std::uint32_t n = plan.Total(); n < kSquadMaxSize; ++n)
                    CHECK(entries[n] == 0);
            }
        CHECK(SquadEntries(SquadFor(1, false))[1] == NPC_BRD_SQUAD_MEDIC);
        CHECK(SquadEntries(SquadFor(0, false))[1] == NPC_BRD_SQUAD_RESERVIST);
        CHECK(SquadFor(0, true).Total() <= kSquadMaxSize && SquadFor(0, false).Total() <= kSquadMaxSize);

        // The Officer cap: no drill while 2 Officers live.
        CHECK(DropAllowed(0) && DropAllowed(1));
        CHECK(!DropAllowed(2) && !DropAllowed(3));
    }

    void TestSpotPick()
    {
        // Never the same spot twice in a row, from any last spot with any roll; each of the other three is reachable
        // and equally often over the roll range.
        for (std::uint32_t last = 0; last < kMoleSpotCount; ++last)
        {
            std::uint32_t counts[kMoleSpotCount] = {};
            for (std::uint32_t roll = 0; roll < kSpotRolls; ++roll)
            {
                std::uint32_t const next = NextSpot(last, roll);
                CHECK(next < kMoleSpotCount);
                CHECK(next != last);
                ++counts[next];
            }
            for (std::uint32_t spot = 0; spot < kMoleSpotCount; ++spot)
                CHECK(counts[spot] == (spot == last ? 0u : kSpotRolls / (kMoleSpotCount - 1)));
        }
        // The first drop: any of the four, equally likely.
        std::uint32_t first[kMoleSpotCount] = {};
        for (std::uint32_t roll = 0; roll < kSpotRolls; ++roll)
            ++first[NextSpot(kNoSpot, roll)];
        for (std::uint32_t const n : first)
            CHECK(n == kSpotRolls / kMoleSpotCount);
    }

    void TestMachineRule()
    {
        // A player within 6 yd keeps the machine (and its collision) away; at 6 yd or more it comes up.
        CHECK(kMachineClearYd == 6.f);
        CHECK(!MachineMayStand(0.f));
        CHECK(!MachineMayStand(4.5f));
        CHECK(!MachineMayStand(5.99f));
        CHECK(MachineMayStand(6.f));
        CHECK(MachineMayStand(30.f));
        // The footprint (about 7 yd square) fits inside the clearance: half of it plus a yard.
        CHECK(kMachineClearYd >= 7.f / 2.f + 1.f);
    }

    void TestFormation()
    {
        CHECK(SlotAngleDeg(0) == 0.f);
        CHECK(SlotAngleDeg(1) == -kSlotStepDeg && SlotAngleDeg(2) == kSlotStepDeg);
        CHECK(SlotAngleDeg(3) == -2.f * kSlotStepDeg);
        for (std::uint32_t spotIndex = 0; spotIndex < kMoleSpotCount; ++spotIndex)
        {
            Point3 const& spot = kMoleSpots[spotIndex];
            float const toward = DungeonKit::BearingTo(spot.XY(), kAngerforgeSpawn.XY());
            std::vector<Vec2> points;
            for (std::uint32_t slot = 0; slot < kSquadMaxSize; ++slot)
            {
                Vec2 const p = SlotPoint(spot.XY(), toward, slot);
                points.push_back(p);
                // On the ring around the machine, outside its footprint, inside the hall.
                CHECK(std::fabs(DungeonKit::Distance(spot.XY(), p) - kSlotRadiusYd) < 0.01f);
                CHECK(kSlotRadiusYd > 7.f / 2.f + 1.f);
                CHECK(AngerforgeArena().Contains(p, spot.z));
            }
            // The Officer's slot (0) is the one that points at him: the nearest to him of the four.
            for (std::uint32_t slot = 1; slot < kSquadMaxSize; ++slot)
                CHECK(DungeonKit::Distance(points[0], kAngerforgeSpawn.XY())
                    <= DungeonKit::Distance(points[slot], kAngerforgeSpawn.XY()) + 0.01f);
            // Nobody stands on anybody: slots are at least 3 yd apart.
            for (std::size_t a = 0; a < points.size(); ++a)
                for (std::size_t b = a + 1; b < points.size(); ++b)
                    CHECK(DungeonKit::Distance(points[a], points[b]) > 3.f);
        }
    }

    void TestCommanding()
    {
        // The Officer shields the other adds within 15 yd, never Angerforge, never itself.
        CHECK(IsShielded(NPC_BRD_SQUAD_OFFICER) && IsShielded(NPC_BRD_SQUAD_RESERVIST)
            && IsShielded(NPC_BRD_SQUAD_MEDIC) && IsShielded(NPC_ANVILRAGE_RESERVIST));
        CHECK(!IsShielded(NPC_ANGERFORGE));
        CHECK(!IsShielded(8894) && !IsShielded(8895));       // the stock trash Medic and Officer are not his army
        CHECK(!IsShielded(0));
        CHECK(ShieldReaches(NPC_BRD_SQUAD_MEDIC, false, 0.f));
        CHECK(ShieldReaches(NPC_BRD_SQUAD_MEDIC, false, 15.f));
        CHECK(!ShieldReaches(NPC_BRD_SQUAD_MEDIC, false, 15.01f));
        CHECK(!ShieldReaches(NPC_BRD_SQUAD_OFFICER, true, 0.f));         // itself
        CHECK(ShieldReaches(NPC_BRD_SQUAD_OFFICER, false, 10.f));        // the other Officer
        CHECK(!ShieldReaches(NPC_ANGERFORGE, false, 3.f));
        // The shield outlives a pulse (no flicker) and ends within 2.5 s of the Officer going.
        CHECK(kCommandedMs > kCommandingPulseMs && kCommandedMs <= 3000);
        // The ring is renewed before it pops.
        CHECK(kCommandingRingMs > 2000);
    }

    void TestMedic()
    {
        // The heal bar: not worth casting while he misses under 5%.
        CHECK(!HealWanted(100.f));
        CHECK(!HealWanted(96.f));
        CHECK(HealWanted(95.f));
        CHECK(HealWanted(40.f));
        // The kick is a reward on normal and expected on heroic.
        CHECK(kHealKickPriorityNormal < kHealKickPriorityHeroic);
        CHECK(kHealCastMs == 3000 && kHealFirstMs > kHealCastMs && kHealEveryMs > kHealCastMs);
        CHECK(kMindBlastMinMs <= kMindBlastMaxMs);
        // One Medic's heals are 12 s apart, 5% of 150k = 7,500 each: a stack of unkicked heals at 2 Medics outpaces
        // nothing here (the spec's soft limit is the cap on Officers, not on Medics), but one heal is bounded.
        CHECK(kHealPctOfBoss * 150000 / 100 == 7500);
        // R-2-A MI-1: it walks back to him before he leaves its heal's range, and whenever it cannot see him.
        CHECK(kMedicHealRangeYd == 40.f);
        CHECK(!MedicMustCloseIn(kMedicRangeYd, true));
        CHECK(!MedicMustCloseIn(kMedicLeashYd, true));
        CHECK(MedicMustCloseIn(kMedicLeashYd + 0.1f, true));
        CHECK(MedicMustCloseIn(kMedicHealRangeYd, true));
        CHECK(MedicMustCloseIn(55.f, true));                    // the reviewer's case: 28 yd beyond a far healer
        CHECK(MedicMustCloseIn(10.f, false));                   // a pillar between them
    }

    void TestKillOrder()
    {
        CHECK(kOfficerPriority > kMedicPriority);
        CHECK(kMedicPriority > kReservistPriority);
        CHECK(kReservistPriority > kAngerforgePriority);
    }

    void TestGrenade()
    {
        // 2 (heroic 3) marked, never more than the group.
        CHECK(GrenadeMarks(false, 5) == 2 && GrenadeMarks(true, 5) == 3);
        CHECK(GrenadeMarks(false, 1) == 1 && GrenadeMarks(true, 2) == 2);
        CHECK(GrenadeMarks(true, 0) == 0);
        CHECK(kGrenadeLookLeadMs < kGrenadeWarnMs);

        // Never the tank (orchestrator default 2026-11-17): the pick rule over a tank and two others marks the two,
        // whatever the dice, even on heroic's 3 marks; a tank alone in the fight is still marked (the fallback rule).
        CHECK(!kGrenadeMarksTank);
        DungeonKit::PickRule const rule = GrenadePickRule();
        std::vector<DungeonKit::PickCandidate> group(3);
        group[0].id = 1;
        group[0].tank = true;
        group[1].id = 2;
        group[2].id = 3;
        for (std::uint32_t roll = 0; roll < 3; ++roll)
        {
            auto const picks = DungeonKit::PickDistinctFrom(group, rule, kGrenadeCount.heroic,
                [roll](std::uint32_t n) { return roll % n; });
            CHECK(picks.size() == 2);
            for (std::size_t i : picks)
                CHECK(!group[i].tank);
        }
        std::vector<DungeonKit::PickCandidate> alone(1);
        alone[0].id = 1;
        alone[0].tank = true;
        CHECK(DungeonKit::PickDistinctFrom(alone, rule, kGrenadeCount.normal, [](std::uint32_t) { return 0u; })
            .empty());
        auto const solo = DungeonKit::PickDistinctFrom(alone, GrenadeTankAloneRule(), 1,
            [](std::uint32_t) { return 0u; });
        CHECK(solo.size() == 1 && solo[0] == 0);
    }

    // The fight's timeline: the squads at their spec cadence against the spec's fight length ("about 100 s with 4
    // squads" normal, "about 115 s with 5" heroic), and the cap holding squads at 2 Officers.
    void TestTimeline()
    {
        for (bool const heroic : { false, true })
        {
            std::uint64_t t = 0;
            std::uint32_t squads = 0;
            std::uint64_t at[8] = {};
            while (squads < 6)
            {
                t += NextSquadDelayMs(squads, heroic);
                at[squads++] = t;
            }
            CHECK(at[0] == 10000);
            CHECK(at[1] == (heroic ? 35000u : 40000u));
            // Normal: the fourth squad lands at 100 s (the fight's length); heroic: the fifth at 110 s.
            CHECK(heroic ? at[4] == 110000 : at[3] == 100000);
        }

        // Nobody kills an Officer: two squads come, then the cap holds the third until one dies; the timer is not
        // restarted by the wait (the drop happens the moment an Officer dies, and the next is a full period later).
        std::uint32_t officers = 0;
        std::uint32_t drops = 0;
        for (std::uint32_t second = 10; second < 200; ++second)
        {
            // a due drop each period, held while 2 Officers live
            if (second >= 10 && (second - 10) % 30 == 0 && DropAllowed(officers))
            {
                ++drops;
                ++officers;
            }
        }
        CHECK(drops == 2 && officers == 2);

        // The grenade timeline: 15 s, then every 20 s (heroic 15 s), each over before the next.
        std::uint64_t throwAt = kGrenadeFirstMs;
        for (int i = 0; i < 5; ++i)
        {
            CHECK(throwAt + kGrenadeWarnMs < throwAt + kGrenadeEveryMs.heroic);
            throwAt += kGrenadeEveryMs.normal;
        }
        CHECK(throwAt == 15000 + 5 * 20000);
    }
}

int main()
{
    TestSlice();
    TestArena();
    TestTuning();
    TestSquads();
    TestSpotPick();
    TestMachineRule();
    TestFormation();
    TestCommanding();
    TestMedic();
    TestKillOrder();
    TestGrenade();
    TestTimeline();

    return Report("brd_angerforge_test");
}
