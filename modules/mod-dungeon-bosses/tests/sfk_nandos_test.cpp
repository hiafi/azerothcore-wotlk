// Host tests for Wolf Master Nandos (WP-S8): NandosLogic.h. The slice and spell ids, the pack roster and kill order,
// Pack Bond's steps, the Mark the Prey split and cap (normal and heroic reference rows), the lunge, Acid Slaver and
// Guardian Howl numbers, the delusion rule, the Alpha's Inheritance bookkeeping, the timers and the arena.
#include "NandosLogic.h"
#include "ShadowfangKeepRework.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <numeric>
#include <set>
#include <vector>

using namespace ShadowfangKeepRework;
using namespace Nandos;

namespace
{
    // The reference rows (BM MapLevels 33:20 33h:60): non-tank health at level 20 and 60.
    std::uint32_t constexpr kRefNormal = 1300;
    std::uint32_t constexpr kRefHeroic = 4120;

    bool Near(float a, float b, float eps = 0.01f)
    {
        return std::fabs(a - b) <= eps;
    }

    std::uint32_t Sum(std::vector<std::uint32_t> const& v)
    {
        return std::accumulate(v.begin(), v.end(), 0u);
    }

    void TestSliceAndSpells()
    {
        CHECK(kSpellsReservation.Contains(kSlice.first));
        CHECK(kSpellsReservation.Contains(kSlice.last));
        CHECK(kSlice.first == 206040u);
        CHECK(kSlice.last == 206059u);
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : kAllSpells)
        {
            CHECK(kSlice.Contains(id));
            CHECK(seen.insert(id).second);
        }
        CHECK(kHowlSpell(false) == SPELL_NANDOS_GUARDIAN_HOWL);
        CHECK(kHowlSpell(true) == SPELL_NANDOS_GUARDIAN_HOWL_HEROIC);
        CHECK(SPELL_WAVERING_WILL == 7127u);
        CHECK(SPELL_SUMMON_LUPINE_DELUSIONS == 7132u);
    }

    void TestPackRoster()
    {
        std::set<std::uint32_t> entries;
        for (std::size_t i = 0; i < kWolfCount; ++i)
        {
            Wolf const w = static_cast<Wolf>(i);
            CHECK(kCreaturesReservation.Contains(EntryOf(w)));
            CHECK(entries.insert(EntryOf(w)).second);
            CHECK(WolfOf(EntryOf(w)) == w);
            CHECK(WolfByName(WolfName(w)) == w);
            CHECK(!WolfOf(kStockEntries[i]).has_value());       // the stock trash stays stock
        }
        CHECK(EntryOf(Wolf::Bleak) == 300509u);
        CHECK(EntryOf(Wolf::Lupine) == 300510u);
        CHECK(EntryOf(Wolf::Slavering) == 300511u);
        CHECK(EntryOf(Wolf::Wolfguard) == 300512u);
        CHECK(kStockEntries[Index(Wolf::Bleak)] == 3861u);
        CHECK(kStockEntries[Index(Wolf::Lupine)] == 3863u);
        CHECK(kStockEntries[Index(Wolf::Slavering)] == 3862u);
        CHECK(kStockEntries[Index(Wolf::Wolfguard)] == 5058u);
        CHECK(kDisplays[Index(Wolf::Bleak)] == 801u);
        CHECK(kDisplays[Index(Wolf::Lupine)] == 2446u);
        CHECK(kDisplays[Index(Wolf::Slavering)] == 11421u);
        CHECK(kDisplays[Index(Wolf::Wolfguard)] == 246u);
        CHECK(kPackSpawnGuids[Index(Wolf::Lupine)] == 16238u);
        CHECK(kPackSpawnGuids[Index(Wolf::Bleak)] == 16239u);
        CHECK(kPackSpawnGuids[Index(Wolf::Slavering)] == 16240u);
        CHECK(kPackSpawnGuids[Index(Wolf::Wolfguard)] == 16241u);
        CHECK(!WolfOf(NPC_NANDOS).has_value());
        CHECK(!WolfOf(NPC_LUPINE_DELUSION).has_value());
        CHECK(!WolfByName("nandos").has_value());

        // Kill order (SK 1368): Wolfguard, Slavering, Bleak, Lupine, then Nandos at 0; delusions above all.
        CHECK(KillPriority(Wolf::Wolfguard) > KillPriority(Wolf::Slavering));
        CHECK(KillPriority(Wolf::Slavering) > KillPriority(Wolf::Bleak));
        CHECK(KillPriority(Wolf::Bleak) > KillPriority(Wolf::Lupine));
        CHECK(KillPriority(Wolf::Lupine) > 0);
        CHECK(kDelusionPriority > KillPriority(Wolf::Wolfguard));

        // Every pack spawn is within the pack search from Nandos.
        for (Point3 const& p : kPackSpawns)
            CHECK(DungeonKit::Distance(p.XY(), kNandosSpawn.XY()) < kPackSearchYd);
    }

    void TestPackBond()
    {
        CHECK(PackBondAmount(4) == -40);
        CHECK(PackBondAmount(3) == -30);
        CHECK(PackBondAmount(2) == -20);
        CHECK(PackBondAmount(1) == -10);
        CHECK(PackBondAmount(0) == 0);
        CHECK(PackBondAmount(9) == -40);     // never past the four wolves
    }

    void TestMarkThePrey()
    {
        CHECK(kPreyFirstMs == 10000u);
        CHECK(kPreyEveryMs == 18000u);
        CHECK(kPreyWarnMs == 4000u);
        CHECK(Near(kPreyRadiusYd, 6.f));
        CHECK(kPreyWarnMs < kPreyEveryMs);
        CHECK(!PreyActive(0));
        CHECK(PreyActive(1));
        CHECK(Near(PreyTotalPct(4), 100.f));
        CHECK(Near(PreyTotalPct(1), 25.f));
        CHECK(Near(PreyTotalPct(0), 0.f));

        // SK: 4 wolves = 100% total, 20% each for a group of five.
        std::vector<std::uint32_t> s = PreyShares(kRefNormal, 4, 5);
        CHECK(s.size() == 5u);
        for (std::uint32_t v : s)
            CHECK(v == 260u);
        s = PreyShares(kRefHeroic, 4, 5);
        for (std::uint32_t v : s)
            CHECK(v == 824u);

        // A prey left alone takes at most 75% (and survives at full health).
        CHECK(PreyShares(kRefNormal, 4, 1).front() == 975u);
        CHECK(PreyShares(kRefHeroic, 4, 1).front() == 3090u);
        CHECK(PreyShares(kRefNormal, 3, 1).front() == 975u);
        CHECK(PreyShares(kRefNormal, 2, 1).front() == 650u);     // under the cap
        CHECK(PreyShares(kRefNormal, 1, 1).front() == 325u);

        // Killing wolves shrinks the lunge; the shares never add up past the total.
        for (std::uint32_t wolves = 1; wolves <= 4; ++wolves)
            for (std::uint32_t inside = 1; inside <= 5; ++inside)
            {
                std::vector<std::uint32_t> const shares = PreyShares(kRefNormal, wolves, inside);
                CHECK(shares.size() == inside);
                CHECK(Sum(shares) <= kRefNormal * wolves / 4);
                for (std::uint32_t v : shares)
                    CHECK(v <= 975u);
            }
        CHECK(Sum(PreyShares(kRefNormal, 3, 5)) == 975u);   // 75% of the row, split five ways
        CHECK(PreyShares(kRefNormal, 4, 0).empty());

        // Every wolf lunges once the ring holds at least as many players as wolves.
        for (std::size_t wolves = 1; wolves <= kWolfCount; ++wolves)
        {
            std::set<std::size_t> used;
            for (std::size_t share = 0; share < 5; ++share)
            {
                std::size_t const w = LungeWolfFor(share, wolves);
                CHECK(w < wolves);
                used.insert(w);
            }
            CHECK(used.size() == wolves);
        }
        CHECK(LungeWolfFor(3, 0) == 0u);

        // The lunge lands 1.5 yd short of the prey, on the wolf's side.
        Vec2 const prey{ 0.f, 0.f };
        Vec2 const land = LungeLanding({ 20.f, 0.f }, prey, kLungeOffsetYd);
        CHECK(Near(land.x, 1.5f));
        CHECK(Near(land.y, 0.f));
        Vec2 const close = LungeLanding({ 1.f, 0.f }, prey, kLungeOffsetYd);
        CHECK(Near(close.x, 1.f));

        // The most open point holds a whole 6 yd ring (clearance 9.4 yd, NAVMESH-REPORT s8).
        CHECK(kPreyRadiusYd < 9.4f);
    }

    void TestAcidSlaverAndHowl()
    {
        CHECK(Near(SlaverLength(false), 8.f));
        CHECK(Near(SlaverLength(true), 20.f));
        CHECK(Near(kSlaverAngleDeg, 90.f));
        CHECK(Near(kSlaverPct, 35.f));
        CHECK(kSlaverWarnMs == 2000u);
        CHECK(kSlaverFirstMs == 6000u);
        CHECK(kSlaverEveryMs == 15000u);
        CHECK(kSlaverWarnMs < kSlaverEveryMs);

        CHECK(kHowlCastMs == 2000u);
        CHECK(kHowlFirstMs == 8000u);
        CHECK(kHowlEveryMs == 20000u);
        CHECK(kHowlHealPct == 5u);
        CHECK(kHowlDamagePct == 15u);
        CHECK(kHowlBuffMs == 10000u);
        CHECK(kHowlCastMs < kHowlFirstMs);
        CHECK(HowlTouches(NPC_NANDOS));
        for (std::uint32_t entry : kPackEntries)
            CHECK(HowlTouches(entry));
        for (std::uint32_t entry : kStockEntries)
            CHECK(!HowlTouches(entry));
        CHECK(!HowlTouches(NPC_LUPINE_DELUSION));
        CHECK(!HowlTouches(NPC_ARUGAL));
        // The howl reaches the whole room from any wolf spawn.
        for (Point3 const& p : kPackSpawns)
            CHECK(DungeonKit::Distance(p.XY(), kNandosSpawn.XY()) < kHowlRadiusYd);
    }

    void TestWaveringWillAndDelusions()
    {
        CHECK(kWillFirstMinMs == 2000u && kWillFirstMaxMs == 10000u);
        CHECK(kWillEveryMinMs == 15000u && kWillEveryMaxMs == 20000u);
        CHECK(kAlphaWillEveryMs == 15000u);
        CHECK(Near(kAlphaWillPctPerStack, 2.f));
        CHECK(kAlphaWillTickMs == 2000u);
        CHECK(kAlphaWillMaxStacks == 5u);
        CHECK(kAlphaWillMs == 60000u);
        // Five stacks: 10% of reference health every 2 s (130 normal, 412 heroic).
        CHECK(DungeonKit::RefFlatValue(kRefNormal, kRefNormal, kAlphaWillPctPerStack, false) * kAlphaWillMaxStacks
            == 130u);
        CHECK(DungeonKit::RefFlatValue(kRefHeroic, kRefHeroic, kAlphaWillPctPerStack, false) * kAlphaWillMaxStacks
            == 410u);

        CHECK(kDelusionsFirstMinMs == 4000u && kDelusionsFirstMaxMs == 12000u);
        CHECK(kDelusionsEveryMs == 60000u);
        CHECK(kAlphaDelusionsEveryMs == 20000u);
        CHECK(Near(kTerrorRadiusYd, 5.f));
        CHECK(kTerrorWarnMs == 2000u);
        CHECK(kTerrorFearMs == 2000u);     // the shared 2 s loss of control limit

        CHECK(VanishedByHit(false, 0, 400));
        CHECK(VanishedByHit(true, 399, 400));
        CHECK(!VanishedByHit(true, 400, 400));
    }

    void TestInheritance()
    {
        CHECK(InheritedEveryMs(Wolf::Bleak) == 15000u);
        CHECK(InheritedEveryMs(Wolf::Lupine) == 20000u);
        CHECK(InheritedEveryMs(Wolf::Slavering) == 15000u);
        CHECK(InheritedEveryMs(Wolf::Wolfguard) == 20000u);
        for (std::size_t i = 0; i < kWolfCount; ++i)
            CHECK(kInheritFirstMs < InheritedEveryMs(static_cast<Wolf>(i)));

        Inheritance held;
        CHECK(held.Count() == 0u);
        CHECK(held.Take(Wolf::Wolfguard));
        CHECK(!held.Take(Wolf::Wolfguard));     // a wolf's death hands its ability over once
        CHECK(held.Has(Wolf::Wolfguard));
        CHECK(!held.Has(Wolf::Bleak));
        CHECK(held.Take(Wolf::Slavering));
        CHECK(held.Take(Wolf::Bleak));
        CHECK(held.Take(Wolf::Lupine));
        CHECK(held.Count() == 4u);
        CHECK(held.Mask() == 0x0Fu);
        held.Clear();
        CHECK(held.Count() == 0u);
        CHECK(held.Take(Wolf::Lupine));
    }

    void TestArena()
    {
        Arena const arena = NandosArena();
        CHECK(arena.Contains(kNandosSpawn.XY(), kNandosSpawn.z));
        CHECK(arena.Contains(kNandosOpenPoint.XY(), kNandosOpenPoint.z));
        for (Point3 const& p : kPackSpawns)
            CHECK(arena.Contains(p.XY(), p.z));
        CHECK(!arena.Contains(kArugalSpawn.XY(), kArugalSpawn.z));

        // A player gripped back lands near the open point, inside the room, from beyond the lair door or the south
        // exits toward Fenrus's stair.
        Vec2 const from[] = { { -110.f, 2162.f }, { -150.f, 2150.f }, { -160.f, 2175.f }, { -128.8f, 2165.2f },
            { -60.f, 2152.f } };
        for (Vec2 const& f : from)
        {
            Vec2 const land = GripLanding(f);
            CHECK(arena.Contains(land, kNandosOpenPoint.z));
            CHECK(DungeonKit::Distance(land, kNandosOpenPoint.XY()) <= kGripLandYd + 0.01f);
        }
        // The grip reaches the whole room from Nandos, but not Arugal's platform.
        for (Point3 const& p : kPackSpawns)
            CHECK(DungeonKit::Distance(p.XY(), kNandosSpawn.XY()) < kGripMaxYd);
        CHECK(DungeonKit::Distance(kNandosOpenPoint.XY(), kNandosSpawn.XY()) < kGripMaxYd);
    }
}

int main()
{
    TestSliceAndSpells();
    TestPackRoster();
    TestPackBond();
    TestMarkThePrey();
    TestAcidSlaverAndHowl();
    TestWaveringWillAndDelusions();
    TestInheritance();
    TestArena();
    return Report("sfk_nandos_test");
}
