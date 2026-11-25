// Host tests for SulthrazeJoinLogic.h (the Zul'Farrak gear stage, user ruling 2026-11-25 option A): the tier table,
// every pair of tiers (only the same step joins), what else is carried, unknown and wrong cast items, and broken data.
#include "../src/ZulFarrak/SulthrazeJoinLogic.h"
#include "../src/ZulFarrak/ZulFarrakHardModeItemsLogic.h"
#include "check.h"
#include <cstdint>
#include <vector>

using namespace ZulFarrakSulthraze;

namespace
{
    std::uint32_t constexpr kJang = 11086;
    std::uint32_t constexpr kSang = 9379;
    std::uint32_t constexpr kSul = 9372;
    std::uint32_t constexpr kSteps = 5;

    // Not the minted ids (the write run mints those): step s of a blade.
    std::uint32_t Minted(std::uint32_t base, std::uint32_t step)
    {
        if (step == 0)
            return base;
        return 1000000 + (base == kJang ? 100 : base == kSang ? 200 : 300) + step;
    }

    JoinTable FullTable()
    {
        JoinTable table;
        for (std::uint32_t base : { kJang, kSang, kSul })
            for (std::uint32_t step = 1; step < kSteps; ++step)
                CHECK(table.AddVariant(Minted(base, step), base, step));
        return table;
    }

    void TestIds()
    {
        CHECK(SPELL_CALL_OF_SULTHRAZE == 213808u);
        CHECK(ZulFarrakHardModeItems::kSpellsZulFarrakItems.Contains(SPELL_CALL_OF_SULTHRAZE));
        CHECK(!ZulFarrakHardModeItems::kSpellsDeclared.Contains(SPELL_CALL_OF_SULTHRAZE));
        CHECK(BaseBladeOf(kJang) == Blade::Jangthraze);
        CHECK(BaseBladeOf(kSang) == Blade::Sangthraze);
        CHECK(BaseBladeOf(kSul) == Blade::Sulthraze);
        CHECK(!BaseBladeOf(0) && !BaseBladeOf(11654));
    }

    void TestTable()
    {
        JoinTable base;                                         // before the write run: the Normal swords only
        CHECK(base.Size() == 3 && base.CompleteSteps() == 1);
        CHECK(base.Find(kJang) == (BladeTier{ Blade::Jangthraze, 0 }));
        CHECK(base.EntryOf(Blade::Sulthraze, 0) == kSul);
        CHECK(base.EntryOf(Blade::Sulthraze, 1) == 0);
        CHECK(!base.Find(0) && !base.Find(Minted(kJang, 1)));

        JoinTable table = FullTable();
        CHECK(table.Size() == 3 * kSteps && table.CompleteSteps() == kSteps);
        for (std::uint32_t step = 0; step < kSteps; ++step)
        {
            CHECK(table.Find(Minted(kJang, step)) == (BladeTier{ Blade::Jangthraze, step }));
            CHECK(table.Find(Minted(kSang, step)) == (BladeTier{ Blade::Sangthraze, step }));
            CHECK(table.EntryOf(Blade::Sulthraze, step) == Minted(kSul, step));
        }
        // refused rows change nothing
        CHECK(!table.AddVariant(5000, 11654, 1));               // another base
        CHECK(!table.AddVariant(5000, kSul, 1));                // the step is taken
        CHECK(!table.AddVariant(5000, kSul, 0));                // the base's own step
        CHECK(!table.AddVariant(Minted(kJang, 1), kSang, 9));   // the entry is known
        CHECK(!table.AddVariant(kSul, kSul, 9));
        CHECK(!table.AddVariant(0, kSul, 9));
        CHECK(table.Size() == 3 * kSteps && table.EntryOf(Blade::Sulthraze, 1) == Minted(kSul, 1));
        CHECK(!table.Find(5000));
    }

    // Every Jang'thraze against every single Sang'thraze: the same tier joins into that tier, any other is refused.
    void TestEveryPair()
    {
        JoinTable const table = FullTable();
        for (std::uint32_t jang = 0; jang < kSteps; ++jang)
            for (std::uint32_t sang = 0; sang < kSteps; ++sang)
            {
                JoinDecision const d = DecideJoin(table, Minted(kJang, jang), { Minted(kSang, sang) });
                CHECK(d.step == jang);
                if (jang == sang)
                {
                    CHECK(d.verdict == JoinVerdict::Join);
                    CHECK(d.sangthraze == Minted(kSang, jang) && d.sulthraze == Minted(kSul, jang));
                }
                else
                {
                    CHECK(d.verdict == JoinVerdict::MixedTiers);
                    CHECK(d.sangthraze == 0 && d.sulthraze == 0);
                }
            }
    }

    void TestCarried()
    {
        JoinTable const table = FullTable();
        // nothing, other items, the other swords: no half
        CHECK(DecideJoin(table, kJang, {}).verdict == JoinVerdict::NoSangthraze);
        CHECK(DecideJoin(table, kJang, { 6948, kJang, kSul, Minted(kSul, 1) }).verdict == JoinVerdict::NoSangthraze);
        // every tier carried: always the cast item's own, wherever it stands
        std::vector<std::uint32_t> all;
        for (std::uint32_t step = 0; step < kSteps; ++step)
            all.push_back(Minted(kSang, step));
        for (std::uint32_t step = 0; step < kSteps; ++step)
        {
            JoinDecision const d = DecideJoin(table, Minted(kJang, step), all);
            CHECK(d.verdict == JoinVerdict::Join && d.sangthraze == Minted(kSang, step));
            CHECK(d.sulthraze == Minted(kSul, step));
            // every tier but its own
            std::vector<std::uint32_t> others = all;
            others.erase(others.begin() + step);
            CHECK(DecideJoin(table, Minted(kJang, step), others).verdict == JoinVerdict::MixedTiers);
            others.insert(others.begin(), Minted(kSang, step));
            CHECK(DecideJoin(table, Minted(kJang, step), others).verdict == JoinVerdict::Join);
        }
        // an owned Sul'thraze does not stop the rule (the bag check does)
        CHECK(DecideJoin(table, kJang, { kSul, kSang }).verdict == JoinVerdict::Join);
    }

    void TestCastItem()
    {
        JoinTable const table = FullTable();
        for (std::uint32_t entry : { 0u, 6948u, kSang, kSul, Minted(kSang, 2), Minted(kSul, 2) })
        {
            JoinDecision const d = DecideJoin(table, entry, { kSang, Minted(kSang, 2) });
            CHECK(d.verdict == JoinVerdict::NotJangthraze && d.sangthraze == 0 && d.sulthraze == 0);
        }
        CHECK(JoinDecision{}.verdict == JoinVerdict::NotJangthraze);
    }

    void TestBrokenData()
    {
        JoinTable table;
        CHECK(table.AddVariant(7001, kJang, 1));
        // a Heroic Jang'thraze without its other half or its result in the table
        CHECK(DecideJoin(table, 7001, { kSang }).verdict == JoinVerdict::MixedTiers);
        CHECK(table.AddVariant(7002, kSang, 1));
        CHECK(table.CompleteSteps() == 1);
        JoinDecision const d = DecideJoin(table, 7001, { 7002 });
        CHECK(d.verdict == JoinVerdict::NoResult && d.step == 1 && d.sangthraze == 0 && d.sulthraze == 0);
        CHECK(DecideJoin(table, kJang, { kSang, 7002 }).verdict == JoinVerdict::Join);
        CHECK(table.AddVariant(7003, kSul, 1));
        CHECK(table.CompleteSteps() == 2);
        CHECK(DecideJoin(table, 7001, { 7002 }).sulthraze == 7003);
        // a step the Jang'thraze has and the Sang'thraze has not
        CHECK(table.AddVariant(7004, kJang, 4));
        CHECK(table.AddVariant(7005, kSul, 4));
        CHECK(table.CompleteSteps() == 2);
        CHECK(DecideJoin(table, 7004, {}).verdict == JoinVerdict::NoSangthraze);
    }
}

int main()
{
    TestIds();
    TestTable();
    TestEveryPair();
    TestCarried();
    TestCastItem();
    TestBrokenData();
    return Report("zul_farrak_sulthraze_join_test");
}
