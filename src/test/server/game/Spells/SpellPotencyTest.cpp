/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * @file SpellPotencyTest.cpp
 * @brief Tests for the potency system's low-level correction + variance roll
 *        (docs/potency-system.md, "Implementation" / "Where potency lives").
 *
 * SpellPotency::ApplyCorrection() takes `value` as the effect's own already-computed native line
 * (SpellEffectInfo::CalcValue's existing BasePoints + level*RealPointsPerLevel + DieSides-roll
 * math, unmodified - this test does not re-derive that part, only the correction on top of it):
 *
 *   value += correction_per_level * max(0, breakpoint_level - level);
 *   if (variance_pct > 0) value *= frand(1, 1 + variance_pct / 100);
 *
 * Reference row is Frostbolt's from docs/potency-system.md's "Reference spells" table:
 * EffectBasePoints -165, EffectDieSides 1, EffectRealPointsPerLevel 11.4286, K 8.3095,
 * SpellLevel/BaseLevel 1. `native(level)` below mirrors CalcValue's own (unchanged) formula to
 * produce each level's input value, so the test only reproduces the *correction*, not the engine's
 * pre-existing level-scaling.
 */

#include "SpellPotency.h"
#include "gtest/gtest.h"

#include <cmath>

namespace
{
    constexpr int32_t FROSTBOLT_BASE_POINTS = -165;
    constexpr float FROSTBOLT_PPL = 11.4286f;
    constexpr float FROSTBOLT_K = 8.3095f;
    constexpr uint8_t BREAKPOINT = 25;

    /// Mirrors SpellEffectInfo::CalcValue's existing level-scaling + DieSides-1 roll, for
    /// BaseLevel == SpellLevel == 1 (Frostbolt's reference row) - the native line SpellPotency's
    /// hook receives as `value`, before any correction.
    float NativeValue(uint8_t level)
    {
        return float(FROSTBOLT_BASE_POINTS + int32_t(float(level - 1) * FROSTBOLT_PPL) + 1);
    }
}

TEST(SpellPotencyTest, FrostboltReferenceRow_NoVariance)
{
    // variance_pct 0 keeps this deterministic; the roll itself is covered separately below.
    struct Case { uint8_t level; int32_t expectedTruncated; };
    // Levels 1, 25, 60, 80 match docs/potency-system.md's Frostbolt table exactly (35, 110, 510,
    // 738). Level 20 lands on 94, one under the doc's published 95 - the already-accepted ±1
    // rounding drift from docs/potency-system.md's "Caveats and checks" (the doc's own reference
    // table was computed independently of this stepwise truncated arithmetic), not a bug here.
    Case const cases[] = {
        {1, 35},
        {20, 94},
        {25, 110},
        {60, 510},
        {80, 738},
    };

    for (Case const& c : cases)
    {
        float native = NativeValue(c.level);
        float corrected = SpellPotency::ApplyCorrection(native, c.level, FROSTBOLT_K, BREAKPOINT, 0.0f);
        EXPECT_EQ(int32_t(std::trunc(corrected)), c.expectedTruncated) << "level " << int(c.level);
    }
}

TEST(SpellPotencyTest, NoCorrectionAtOrAboveBreakpoint)
{
    // At and above the breakpoint, max(0, breakpoint - level) is 0, so the native line passes
    // through unchanged - this is what makes "no correction needed above 25" true at all.
    float native = NativeValue(60);
    EXPECT_FLOAT_EQ(SpellPotency::ApplyCorrection(native, 60, FROSTBOLT_K, BREAKPOINT, 0.0f), native);
    EXPECT_FLOAT_EQ(SpellPotency::ApplyCorrection(native, BREAKPOINT, FROSTBOLT_K, BREAKPOINT, 0.0f), native);
}

TEST(SpellPotencyTest, CorrectionIsExactlyLinearBelowBreakpoint)
{
    // The correction term is K per level below breakpoint - verify it's exactly that slope, not
    // just "roughly right" at the doc's own sampled levels.
    float valueAt20 = SpellPotency::ApplyCorrection(0.0f, 20, FROSTBOLT_K, BREAKPOINT, 0.0f);
    float valueAt19 = SpellPotency::ApplyCorrection(0.0f, 19, FROSTBOLT_K, BREAKPOINT, 0.0f);
    EXPECT_NEAR(valueAt19 - valueAt20, FROSTBOLT_K, 0.0001f);
}

TEST(SpellPotencyTest, VarianceRollStaysWithinBounds)
{
    // 10% variance (direct damage effects): result should land in [value, 1.1*value], matching
    // "potency sets the average; the generator bakes the minimum as value / 1.05" - the roll is
    // what draws the top of the range back up to 1.1x the stored minimum.
    constexpr float value = 510.0f;
    bool sawNonMinimum = false;
    for (int i = 0; i < 500; ++i)
    {
        float rolled = SpellPotency::ApplyCorrection(value, 60, FROSTBOLT_K, BREAKPOINT, 10.0f);
        EXPECT_GE(rolled, value);
        EXPECT_LE(rolled, value * 1.1f);
        if (rolled > value)
            sawNonMinimum = true;
    }
    EXPECT_TRUE(sawNonMinimum) << "500 rolls all landed exactly on the minimum - frand likely isn't being called";
}

TEST(SpellPotencyTest, ZeroVarianceNeverRolls)
{
    // Periodic effects (variance_pct 0): every tick repeats the same amount, no roll at all.
    constexpr float value = 123.0f;
    for (int i = 0; i < 50; ++i)
        EXPECT_FLOAT_EQ(SpellPotency::ApplyCorrection(value, 60, FROSTBOLT_K, BREAKPOINT, 0.0f), value);
}
