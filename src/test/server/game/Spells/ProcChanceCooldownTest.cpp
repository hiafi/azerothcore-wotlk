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
 * @file ProcChanceCooldownTest.cpp
 * @brief gear-scaling GS2 (docs/Systems.md section 5): Proc Chance shortens a class proc's internal cooldown,
 *        ICD / (1 + Proc Chance), the same shape as Cooldown Haste.
 */

#include "ProcChanceCooldown.h"
#include "gtest/gtest.h"

using namespace std::chrono_literals;

TEST(ProcChanceCooldownTest, NoProcChanceKeepsTheListedCooldown)
{
    EXPECT_EQ(ProcChanceCooldown::Scale(6000u, 0.0f), 6000u);
    EXPECT_EQ(ProcChanceCooldown::Scale(6000ms, 0.0f), 6000ms);
}

TEST(ProcChanceCooldownTest, DividesByOnePlusProcChance)
{
    EXPECT_EQ(ProcChanceCooldown::Scale(6000u, 100.0f), 3000u);    // The Art of War at +100%: 3 s
    EXPECT_EQ(ProcChanceCooldown::Scale(10000u, 25.0f), 8000u);    // Demonic Calling at +25%: 8 s
    EXPECT_EQ(ProcChanceCooldown::Scale(1500u, 50.0f), 1000u);     // the tentacle ICD at +50%: 1 s
    EXPECT_EQ(ProcChanceCooldown::Scale(5000ms, 100.0f), 2500ms);  // Nightfall's spell_proc row at +100%
}

TEST(ProcChanceCooldownTest, NeverReachesZero)
{
    // Like Cooldown Haste: 100% halves, 200% leaves a third; no finite rating removes the ICD.
    EXPECT_EQ(ProcChanceCooldown::Scale(3000u, 200.0f), 1000u);
    EXPECT_GT(ProcChanceCooldown::Scale(1000u, 10000.0f), 0u);
}

TEST(ProcChanceCooldownTest, NoCooldownOrNegativeProcChanceIsUnchanged)
{
    EXPECT_EQ(ProcChanceCooldown::Scale(0u, 50.0f), 0u);
    EXPECT_EQ(ProcChanceCooldown::Scale(0ms, 50.0f), 0ms);
    EXPECT_EQ(ProcChanceCooldown::Scale(6000u, -20.0f), 6000u);
}

TEST(ProcChanceCooldownTest, OnlyProcsWithAChanceRollScale)
{
    // User ruling 2026-11-27: a listed chance under 100% scales; 100% procs (capstones, spreads) and
    // charge-spending auras keep the listed ICD.
    EXPECT_EQ(ProcChanceCooldown::IsScaledProc(30.0f), true);          // The Art of War rank 3
    EXPECT_EQ(ProcChanceCooldown::IsScaledProc(0.0f), true);           // a PPM row passes 0: it rolls
    EXPECT_EQ(ProcChanceCooldown::IsScaledProc(99.9f), true);
    EXPECT_EQ(ProcChanceCooldown::IsScaledProc(100.0f), false);        // Nature's Reach, Improved Moonfire
    EXPECT_EQ(ProcChanceCooldown::IsScaledProc(101.0f), false);        // DBC "always"
    EXPECT_EQ(ProcChanceCooldown::IsScaledProc(10.0f, true), false);   // spends charges
}
