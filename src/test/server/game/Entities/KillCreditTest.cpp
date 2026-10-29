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

#include "KillCredit.h"
#include "gtest/gtest.h"

// The kill credit window's per-victim record (warrior-rework KC). RecordHit's type filters (white swings, DoT ticks,
// damage shields, player victims, attackers with no player behind them) need the game library and are review-only.

using KillCredit::Assist;
using KillCredit::HitLog;

namespace
{
    // The inline (HighGuid, counter) constructor keeps the record type testable without ObjectGuid.cpp.
    ObjectGuid const PLAYER_A(HighGuid::Player, uint32(1));
    ObjectGuid const PLAYER_B(HighGuid::Player, uint32(2));
    ObjectGuid const PLAYER_C(HighGuid::Player, uint32(3));
    constexpr uint32 SPELL_X = 100;
    constexpr uint32 SPELL_Y = 200;
}

TEST(KillCreditHitLogTest, HitInsideWindowIsReturned)
{
    HitLog log;
    log.Record(PLAYER_A, SPELL_X, Milliseconds(10000));

    std::vector<Assist> const assists = log.Collect(Milliseconds(11000));
    ASSERT_EQ(assists.size(), 1u);
    EXPECT_EQ(assists[0].player, PLAYER_A);
    EXPECT_EQ(assists[0].ownSpellId, SPELL_X);
    EXPECT_EQ(assists[0].lastHit, Milliseconds(10000));
}

TEST(KillCreditHitLogTest, WindowEdgeIsInclusive)
{
    HitLog log;
    log.Record(PLAYER_A, SPELL_X, Milliseconds(10000));

    EXPECT_EQ(log.Collect(Milliseconds(12000)).size(), 1u); // exactly 2000 ms: inside
    EXPECT_TRUE(log.Collect(Milliseconds(12001)).empty());  // 2001 ms: outside
}

TEST(KillCreditHitLogTest, SecondHitOverwrites)
{
    HitLog log;
    log.Record(PLAYER_A, SPELL_X, Milliseconds(10000));
    log.Record(PLAYER_A, SPELL_Y, Milliseconds(10500));

    EXPECT_EQ(log.Size(), 1u);
    std::vector<Assist> const assists = log.Collect(Milliseconds(11000));
    ASSERT_EQ(assists.size(), 1u);
    EXPECT_EQ(assists[0].ownSpellId, SPELL_Y);
    EXPECT_EQ(assists[0].ownSpellAt, Milliseconds(10500));
    EXPECT_EQ(assists[0].lastHit, Milliseconds(10500));
}

TEST(KillCreditHitLogTest, PetHitKeepsOwnSpellAndRefreshesLastHit)
{
    HitLog log;
    log.Record(PLAYER_A, SPELL_X, Milliseconds(10000));
    log.Record(PLAYER_A, 0, Milliseconds(11000)); // pet hit

    std::vector<Assist> const assists = log.Collect(Milliseconds(11500));
    ASSERT_EQ(assists.size(), 1u);
    EXPECT_EQ(assists[0].ownSpellId, SPELL_X);
    EXPECT_EQ(assists[0].ownSpellAt, Milliseconds(10000));
    EXPECT_EQ(assists[0].lastHit, Milliseconds(11000));
}

TEST(KillCreditHitLogTest, StaleOwnSpellReportedAsZeroWhilePetHitKeepsEntry)
{
    HitLog log;
    log.Record(PLAYER_A, SPELL_X, Milliseconds(10000));
    log.Record(PLAYER_A, 0, Milliseconds(12500)); // pet hit

    std::vector<Assist> const assists = log.Collect(Milliseconds(13000)); // own spell 3000 ms old, pet hit 500 ms
    ASSERT_EQ(assists.size(), 1u);
    EXPECT_EQ(assists[0].player, PLAYER_A);
    EXPECT_EQ(assists[0].ownSpellId, 0u);
}

TEST(KillCreditHitLogTest, PetOnlyEntryHasNoOwnSpell)
{
    HitLog log;
    log.Record(PLAYER_A, 0, Milliseconds(10000));

    std::vector<Assist> const assists = log.Collect(Milliseconds(10100));
    ASSERT_EQ(assists.size(), 1u);
    EXPECT_EQ(assists[0].ownSpellId, 0u);
}

TEST(KillCreditHitLogTest, RecordPrunesStalePlayers)
{
    HitLog log;
    log.Record(PLAYER_A, SPELL_X, Milliseconds(10000));
    log.Record(PLAYER_B, SPELL_X, Milliseconds(11000));
    EXPECT_EQ(log.Size(), 2u);

    log.Record(PLAYER_C, SPELL_Y, Milliseconds(12500)); // A is 2500 ms old: pruned; B 1500 ms: kept
    EXPECT_EQ(log.Size(), 2u);

    std::vector<Assist> const assists = log.Collect(Milliseconds(12500));
    ASSERT_EQ(assists.size(), 2u);
    for (Assist const& assist : assists)
        EXPECT_NE(assist.player, PLAYER_A);
}

TEST(KillCreditHitLogTest, SeveralPlayersEachReturnedOnce)
{
    HitLog log;
    log.Record(PLAYER_A, SPELL_X, Milliseconds(10000));
    log.Record(PLAYER_B, SPELL_Y, Milliseconds(10100));
    log.Record(PLAYER_A, SPELL_Y, Milliseconds(10200));
    log.Record(PLAYER_C, 0, Milliseconds(10300));
    log.Record(PLAYER_B, 0, Milliseconds(10400));

    std::vector<Assist> const assists = log.Collect(Milliseconds(11000));
    ASSERT_EQ(assists.size(), 3u);

    uint32 seenA = 0, seenB = 0, seenC = 0;
    for (Assist const& assist : assists)
    {
        if (assist.player == PLAYER_A)
        {
            ++seenA;
            EXPECT_EQ(assist.ownSpellId, SPELL_Y);
        }
        else if (assist.player == PLAYER_B)
        {
            ++seenB;
            EXPECT_EQ(assist.ownSpellId, SPELL_Y);
            EXPECT_EQ(assist.lastHit, Milliseconds(10400));
        }
        else if (assist.player == PLAYER_C)
        {
            ++seenC;
            EXPECT_EQ(assist.ownSpellId, 0u);
        }
    }
    EXPECT_EQ(seenA, 1u);
    EXPECT_EQ(seenB, 1u);
    EXPECT_EQ(seenC, 1u);
}

TEST(KillCreditHitLogTest, CollectOnEmptyLog)
{
    HitLog log;
    EXPECT_TRUE(log.Empty());
    EXPECT_TRUE(log.Collect(Milliseconds(10000)).empty());
}
