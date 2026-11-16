// Host test (Blackrock Spire WP-KT-B1): the kit's pure flex rules (src/Kit/DungeonKitFlexRules.h) against
// mod-dungeon-difficulties' own (src/FlexMath.h) with DD's shipped settings, for every count 0-40 and a spread of
// bases. tests/run.sh builds it only when DD's source is found (DD_SRC, else ../mod-dungeon-difficulties/src).
#include "DungeonKitFlexRules.h"
#include "FlexMath.h"
#include "check.h"
#include <cstdint>

namespace
{
    namespace DD = DungeonDifficulties::FlexMath;

    void TestDefaults()
    {
        DD::Settings const s;
        CHECK(s.minPlayers == DungeonKit::Flex::kMinPlayers);
        CHECK(s.maxPlayers == DungeonKit::Flex::kMaxPlayers);
        CHECK(s.healthStep == DungeonKit::Flex::kHealthStep);
        CHECK(DD::kDoubleTargetsAt == DungeonKit::Flex::kDoubleTargetsAt);
        CHECK(DD::kPlayersPerLootRoll == DungeonKit::Flex::kPlayersPerLootRoll);
        CHECK(DD::kTankSwapAt == DungeonKit::Flex::kTankSwapAt);
        CHECK(DD::kReferenceSize == DungeonKit::Flex::kMinPlayers);
    }

    void TestEveryCount()
    {
        DD::Settings const s;
        std::uint32_t const bases[] = { 0, 1, 3, 7, 3000, 10130, 100000, 400000, 0x7FFFFFFFu, 0xFFFFFFFFu };
        for (std::uint32_t n = 0; n <= 40; ++n)
        {
            CHECK(DD::Clamp(n, s) == DungeonKit::Flex::Clamp(n));
            CHECK(DD::HealthLadder(n, s) == DungeonKit::Flex::Ladder(n));
            for (std::uint32_t base : bases)
                CHECK(DD::ScaledHealth(base, n, s) == DungeonKit::Flex::HealthAt(n, base));
            for (std::uint8_t a = 0; a <= 4; ++a)
                CHECK(DD::TargetCount(n, a, std::uint8_t(a * 2), s) == DungeonKit::Flex::TargetCount(n, a,
                    std::uint8_t(a * 2)));
            CHECK(DD::LootRolls(n, s) == DungeonKit::Flex::LootRolls(n));
            CHECK(DD::TankSwap(n, s) == DungeonKit::Flex::TankSwapOn(n));
        }
    }
}

int main()
{
    TestDefaults();
    TestEveryCount();
    return Report("kit_flex_parity_test");
}
