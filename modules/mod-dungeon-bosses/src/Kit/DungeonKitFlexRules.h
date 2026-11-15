/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Spire WP-KT-B1, handoff section 3.11 #1-#2): the flex 5-10
 * rules as pure functions, for boss Logic headers and host tests (no engine, no mod-dungeon-difficulties include).
 * The live numbers come from mod-dungeon-difficulties (DD `src/FlexScale.h`, `src/FlexMath.h`), which owns the count,
 * the hold and the health; the engine half of the kit wrapper is DungeonKitFlex.h. These mirror DD's rules with its
 * shipped defaults (Flex.MinPlayers 5, Flex.MaxPlayers 10, Flex.HealthStep 0.25); tests/kit_flex_parity_test.cpp
 * checks them against DD's FlexMath.h when DD's source is on hand. They deliberately do not read DD's live conf:
 * boss Logic headers stay host-testable and every boss's mechanics play the designed 5-10 sizes. A live conf with
 * other Flex.* values changes the held count and the health (DD) but not these rules (the clamp below still applies
 * to the held count); DD's conf dist says so next to the keys (R-1-KIT K-m6).
 *
 * The rules (SYS section 3; Blackrock Spire rulings 7-14 and 20):
 *   count     players on the map at the pull, held for the fight, clamped to 5..10; 0 ("not held") reads as 5
 *   health    base x (1 + 0.25 x (N - 5)): 1.00, 1.25 .. 2.25
 *   targets   the normal count `a` at 5, the doubled count `b` at 6 or more
 *   loot      max(1, N / 5) items: 2 at 10. Flex copies of a loot list sit in LootMode 4 (8 for a hard mode list)
 *   taunts    a taunt swap only at 10
 *   damage    never scales
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLEX_RULES_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLEX_RULES_H

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

namespace DungeonKit::Flex
{
    constexpr std::uint8_t kMinPlayers = 5;            // DD Flex.MinPlayers default: the ladder's 1.00
    constexpr std::uint8_t kMaxPlayers = 10;           // DD Flex.MaxPlayers default
    constexpr double kHealthStep = 0.25;               // DD Flex.HealthStep default
    constexpr std::uint8_t kDoubleTargetsAt = 6;
    constexpr std::uint8_t kPlayersPerLootRoll = 5;
    constexpr std::uint8_t kTankSwapAt = 10;

    // LootMode bits of the flex copies (handoff section 3.12 / section 7 #6): the second roll of the normal list in
    // group LootMode 4, of the hard mode list in LootMode 8. Equal to LOOT_MODE_HARD_MODE_2 / _3 (static_assert in
    // DungeonKitFlex.cpp).
    constexpr std::uint16_t kLootModeFlex = 0x04;
    constexpr std::uint16_t kLootModeFlexHardMode = 0x08;
    constexpr std::uint16_t kLootModeFlexMask = kLootModeFlex | kLootModeFlexHardMode;

    // The count clamped to 5..10 (0, "not held", reads as 5).
    constexpr std::uint8_t Clamp(std::uint32_t players)
    {
        return static_cast<std::uint8_t>(std::clamp<std::uint32_t>(players, kMinPlayers, kMaxPlayers));
    }

    // 1.00 at 5 .. 2.25 at 10.
    constexpr double Ladder(std::uint32_t count)
    {
        return 1.0 + kHealthStep * (double(Clamp(count)) - double(kMinPlayers));
    }

    // A unit's health at `count` players from its 5-player `base`: rounded, at least 1, saturating (DD ScaledHealth).
    inline std::uint32_t HealthAt(std::uint32_t count, std::uint32_t base)
    {
        double const v = std::round(double(std::max<std::uint32_t>(base, 1)) * Ladder(count));
        if (v >= double(std::numeric_limits<std::uint32_t>::max()))
            return std::numeric_limits<std::uint32_t>::max();
        return std::max<std::uint32_t>(1, static_cast<std::uint32_t>(v));
    }

    // The mechanic's target count: `a` at 5, `b` (the doubled count) at 6 or more.
    constexpr std::uint8_t TargetCount(std::uint32_t count, std::uint8_t a, std::uint8_t b)
    {
        return Clamp(count) >= kDoubleTargetsAt ? b : a;
    }

    // Items per kill: max(1, N / 5).
    constexpr std::uint8_t LootRolls(std::uint32_t count)
    {
        return static_cast<std::uint8_t>(std::max<std::uint32_t>(1, Clamp(count) / kPlayersPerLootRoll));
    }

    // A taunt swap only at 10.
    constexpr bool TankSwapOn(std::uint32_t count)
    {
        return Clamp(count) >= kTankSwapAt;
    }

    // The flex LootMode bits a kill at `count` lights: 4 (and 8 with `hardMode`) when the kill rolls twice, else none.
    // SetFlexLoot clears kLootModeFlexMask first and adds these.
    constexpr std::uint16_t LootBits(std::uint32_t count, bool hardMode)
    {
        if (LootRolls(count) < 2)
            return 0;
        return static_cast<std::uint16_t>(kLootModeFlex | (hardMode ? kLootModeFlexHardMode : 0));
    }
}

namespace DungeonKit
{
    // The handoff's short name (section 3.11 #1): `a` at 5, `b` at 6 or more.
    constexpr std::uint8_t FlexCount(std::uint32_t count, std::uint8_t a, std::uint8_t b)
    {
        return Flex::TargetCount(count, a, b);
    }
}

#endif
