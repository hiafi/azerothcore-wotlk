// Host tests for the shared dungeon kit's two-ring mines (Gnomeregan WP-KT-G, F42; SP MT5, MT14):
// DungeonKitMineLogic.h (MineRings, InBlast, MineBook).
#include "DungeonKitMineLogic.h"
#include "check.h"
#include <cstdint>
#include <vector>

using namespace DungeonKit;

namespace
{
    void TestRings()
    {
        CHECK((MineRings{ 3.f, 6.f }.Valid()));                     // MT5: trigger 3 yd, blast 6 yd
        CHECK((MineRings{ 3.f, 3.f }.Valid()));                     // the registry's one-ring mine
        CHECK(!(MineRings{ 6.f, 3.f }.Valid()));
        CHECK(!(MineRings{ 0.f, 6.f }.Valid()));
    }

    // Everyone inside the blast ring is hit, not only who set it off; the height band keeps other floors out.
    void TestBlast()
    {
        Vec2 const mine{ -531.f, 670.f };
        float const z = -326.5f;
        CHECK(InBlast(mine, z, { -531.f, 670.f }, z, 6.f, 6.f));
        CHECK(InBlast(mine, z, { -525.f, 670.f }, z, 6.f, 6.f));             // the edge
        CHECK(InBlast(mine, z, { -527.f, 673.f }, z + 2.f, 6.f, 6.f));        // 5 yd: the blast, not the trigger
        CHECK(!InBlast(mine, z, { -524.9f, 670.f }, z, 6.f, 6.f));
        CHECK(!InBlast(mine, z, { -531.f, 670.f }, z + 6.5f, 6.f, 6.f));
        CHECK(InBlast(mine, z, { -531.f, 670.f }, z - 6.f, 6.f, 6.f));
    }

    void TestBook()
    {
        MineBook b;
        b.Add(1, 0, 3000, 45000);                                   // normal: arms in 3 s, 45 s life
        b.Add(2, 1000, 3000, 60000);                                // heroic: 60 s
        b.Add(3, 2000, 3000, 0);                                    // no life
        CHECK(b.Count() == 3 && b.Has(2) && !b.Has(4));
        CHECK(!b.Armed(1, 2999) && b.Armed(1, 3000));
        CHECK(b.ArmedCount(3999) == 1 && b.ArmedCount(4000) == 2 && b.ArmedCount(5000) == 3);
        CHECK(!b.Armed(9, 100000));

        // MT14: the Detonator sets off the armed mines only (every one on request); oldest first.
        CHECK(b.Detonations(3500, true) == (std::vector<std::uint32_t>{ 1 }));
        CHECK(b.Detonations(3500, false) == (std::vector<std::uint32_t>{ 1, 2, 3 }));
        CHECK(b.Detonations(5000, true) == (std::vector<std::uint32_t>{ 1, 2, 3 }));

        // Lives run out without a blast; a mine with no life never does.
        CHECK(b.Expired(44999).empty());
        CHECK(b.Expired(45000) == (std::vector<std::uint32_t>{ 1 }));
        CHECK(b.Expired(70000) == (std::vector<std::uint32_t>{ 1, 2 }));
        CHECK(b.Remove(1) && !b.Remove(1));
        CHECK(b.Ids() == (std::vector<std::uint32_t>{ 2, 3 }));

        // Re-adding an id replaces it (its clocks restart).
        b.Add(2, 10000, 3000, 1000);
        CHECK(b.Count() == 2 && !b.Armed(2, 12000) && b.Expired(11000) == (std::vector<std::uint32_t>{ 2 }));
        b.Clear();
        CHECK(b.Count() == 0 && b.Detonations(0, false).empty());
    }
}

int main()
{
    TestRings();
    TestBlast();
    TestBook();
    return Report("kit_mines_test");
}
