// Host tests for VaultLogic.h (D9: the Vault, Watchman Doomgrip and the Vault Sentinels): the ids and texts, the build
// spec numbers (SP 640-687), the wake schedule, the fields, the link, the draught thresholds, the loot clock and the
// Secret Safe's contents, and the lockdown's corridor strip against the room's floor.
#include "DungeonKitArena.h"
#include "VaultLogic.h"
#include "check.h"
#include <array>
#include <cmath>
#include <set>

using namespace BlackrockDepthsRework;
using namespace BrdVault;

namespace
{
    void TestIdsAndTexts()
    {
        // The WP's spells sit in its slice, inside the dungeon's reservation.
        CHECK(kSpellsReservation.Contains(kSpellSlice.first));
        CHECK(kSpellsReservation.Contains(kSpellSlice.last));
        CHECK(kSpellSlice.first == 211090 && kSpellSlice.last == 211119);
        CHECK(SPELL_VA_LOCKDOWN == 211090);
        CHECK(SPELL_VA_FIELD_9 == SPELL_VA_FIELD_6 + 3);
        CHECK(SPELL_VA_WATCHMANS_DRAUGHT == 211102 && kSpellSlice.Contains(SPELL_VA_WATCHMANS_DRAUGHT));
        // The creature texts of 9476: group 0 stock, 1-5 new.
        CHECK(YELL_VA_ALARM == 0 && EMOTE_VA_SENTINEL == 1 && EMOTE_VA_SEAL_LAST_BAG == 4 && YELL_VA_DEATH == 5);
        bool found = false;
        for (TextRange const& range : kTextRanges)
            if (range.entry == NPC_DOOMGRIP)
            {
                found = true;
                CHECK(range.first == 0 && range.last == YELL_VA_DEATH && range.firstNew == 1);
            }
        CHECK(found);
        CHECK(kSealText[0] == EMOTE_VA_SEAL_BAG && kSealText[1] == EMOTE_VA_SEAL_GEAR
            && kSealText[2] == EMOTE_VA_SEAL_LAST_BAG);
        // The sentinel's entry and the requested data id.
        CHECK(NPC_BRD_VAULT_SENTINEL == 300793);
        CHECK(kDataVaultDoomgripItem == 67);
    }

    void TestSpecNumbers()
    {
        // SP Build spec: VA2 5 s then 20 s (heroic 15 s); VA3 6 yd, 5% / 8% a second, heroic +1 yd per 10 s to 9 yd;
        // VA4 25% a link, 75% at most; VA5 8 s then 15 s / 12 s, 2 s, 90 degrees, 10 yd, 25% / 40%; VA6 5 stacks of
        // 5%, 30 s; VA7 60% and 30%, 5% heal, +20% damage, 15 s.
        CHECK(kWakeFirstMs == 5000 && kWakeEveryMs.normal == 20000 && kWakeEveryMs.heroic == 15000);
        CHECK(kFieldBaseYd == 6.f && kFieldMaxYd == 9.f && kFieldGrowEveryMs == 10000);
        CHECK(kFieldPct.normal == 5.f && kFieldPct.heroic == 8.f && kFieldTickMs == 1000);
        CHECK(kFieldHoleYd == 0.f);     // the spec's circle (designer question 1)
        CHECK(kLinkPctPerSentinel == 25 && kLinkMaxStacks == 3);
        CHECK(kSweepFirstMs == 8000 && kSweepEveryMs.normal == 15000 && kSweepEveryMs.heroic == 12000);
        CHECK(kSweepWarnMs == 2000 && kSweepAngleDeg == 90.f && kSweepLengthYd == 10.f);
        CHECK(kSweepPct.normal == 25.f && kSweepPct.heroic == 40.f);
        CHECK(kSunderArmorPct == 5 && kSunderMaxStacks == 5 && kSunderMs == 30000);
        CHECK(kSunderFirstMs == 1000 && kSunderEveryMinMs == 6000 && kSunderEveryMaxMs == 8000);
        CHECK(kDraughtAtPct[0] == 60.f && kDraughtAtPct[1] == 30.f);
        CHECK(kDraughtHealPct == 5 && kDraughtDamagePct == 20 && kDraughtMs == 15000);
        // VA8: 75 / 90 / 110 s (the header's, shared with the instance's VaultSafeFor).
        CHECK(kSealAtS[0] == 75 && kSealAtS[1] == 90 && kSealAtS[2] == 110);
    }

    void TestWakes()
    {
        // Normal 5, 25, 45, 65 s; heroic 5, 20, 35, 50 s.
        std::array<std::uint32_t, 4> const normal{ { 5000, 25000, 45000, 65000 } };
        std::array<std::uint32_t, 4> const heroic{ { 5000, 20000, 35000, 50000 } };
        for (std::size_t i = 0; i < kSentinelCount; ++i)
        {
            CHECK(WakeDueMs(i, false) == normal[i]);
            CHECK(WakeDueMs(i, true) == heroic[i]);
        }
        // On time, not before; never a fifth.
        CHECK(!WakeNow(0, 4999, false, true));
        CHECK(WakeNow(0, 5000, false, true));
        CHECK(!WakeNow(1, 24999, false, true));
        CHECK(WakeNow(1, 25000, false, true));
        CHECK(WakeNow(1, 20000, true, true));
        CHECK(!WakeNow(4, 999999, false, false));
        // Nothing awake left: the next one wakes at once (but never before the first wake's time).
        CHECK(WakeNow(2, 30000, false, false));
        CHECK(!WakeNow(2, 30000, false, true));
        CHECK(!WakeNow(0, 3000, false, false));
        // Every roll gives a permutation of the four; the rolls reach all 24.
        std::set<std::array<std::uint8_t, 4>> seen;
        for (std::uint32_t roll = 0; roll < 2000; ++roll)
        {
            std::array<std::uint8_t, 4> const order = WakeOrder(roll * 2654435761u);
            std::set<std::uint8_t> const each(order.begin(), order.end());
            CHECK(each.size() == 4 && *each.begin() == 0 && *each.rbegin() == 3);
            seen.insert(order);
        }
        CHECK(seen.size() == 24);
    }

    void TestFields()
    {
        // Normal: 6 yd for life. Heroic: 6, 7 at 10 s, 8 at 20 s, 9 at 30 s, 9 after.
        CHECK(FieldRadius(false, 0) == 6.f && FieldRadius(false, 120000) == 6.f);
        CHECK(FieldRadius(true, 0) == 6.f && FieldRadius(true, 9999) == 6.f);
        CHECK(FieldRadius(true, 10000) == 7.f && FieldRadius(true, 20000) == 8.f);
        CHECK(FieldRadius(true, 30000) == 9.f && FieldRadius(true, 600000) == 9.f);
        // The look: the rung at or above the radius.
        CHECK(FieldLookFor(6.f) == SPELL_VA_FIELD_6 && FieldLookFor(7.f) == SPELL_VA_FIELD_7);
        CHECK(FieldLookFor(8.f) == SPELL_VA_FIELD_8 && FieldLookFor(9.f) == SPELL_VA_FIELD_9);
        CHECK(FieldLookFor(6.5f) == SPELL_VA_FIELD_7 && FieldLookFor(12.f) == SPELL_VA_FIELD_9);
        // The posts are the four construct spots, 5.8 to 6.1 yd from the center: a 6 yd field reaches the middle (the
        // handoff's frame, section 3.8; designer question 2).
        for (Point3 const& post : kVaultSentinelPosts)
        {
            float const d = std::hypot(post.x - kVaultCenter.x, post.y - kVaultCenter.y);
            CHECK(d > 5.5f && d < 6.5f);
        }
    }

    void TestLink()
    {
        CHECK(LinkStacks(0) == 0 && LinkStacks(1) == 1 && LinkStacks(3) == 3 && LinkStacks(4) == 3);
        CHECK(LinkTakenReductionPct(0) == 0 && LinkTakenReductionPct(1) == 25 && LinkTakenReductionPct(2) == 50);
        CHECK(LinkTakenReductionPct(3) == 75 && LinkTakenReductionPct(9) == 75);
        // Ignoring one sentinel makes him about 37k tougher on normal: 110k / 0.75 - 110k.
        double const tougher = 110000.0 / (1.0 - LinkTakenReductionPct(1) / 100.0) - 110000.0;
        CHECK(tougher > 36000.0 && tougher < 37500.0);
        CHECK(NextDue(8000, 15000, 9000) == 23000);
        CHECK(NextDue(8000, 15000, 30000) == 30001);
    }

    void TestDraught()
    {
        CHECK(!DraughtDue(100.f, 0).has_value());
        CHECK(!DraughtDue(60.1f, 0).has_value());
        CHECK(DraughtDue(60.f, 0) == std::optional<std::uint8_t>(0));
        CHECK(!DraughtDue(45.f, 1).has_value());
        CHECK(DraughtDue(30.f, 1) == std::optional<std::uint8_t>(1));
        // A burst past both thresholds drinks the deeper one first, then the other.
        CHECK(DraughtDue(25.f, 0) == std::optional<std::uint8_t>(1));
        CHECK(DraughtDue(25.f, 2) == std::optional<std::uint8_t>(0));
        CHECK(!DraughtDue(10.f, 3).has_value());
    }

    void TestClockAndSafe()
    {
        // The seals at 75, 90 and 110 s.
        CHECK(SealsPassed(0) == 0 && SealsPassed(74999) == 0);
        CHECK(SealsPassed(75000) == 1 && SealsPassed(89999) == 1);
        CHECK(SealsPassed(90000) == 3 && SealsPassed(110000) == 7);
        CHECK(FinishedSeconds(0) == 1 && FinishedSeconds(74999) == 74 && FinishedSeconds(75000) == 75);
        // What the Safe holds against the finishing time: an emote at 75.0 s and a finish at 75.0 s agree.
        for (std::uint64_t ms = 1000; ms < 130000; ms += 500)
        {
            VaultSafe const safe = VaultSafeFor(FinishedSeconds(ms));
            std::uint8_t const sealed = SealsPassed(ms);
            CHECK(safe.cinder);
            CHECK(safe.gear == !(sealed & 2));
            CHECK(safe.bags == 2u - ((sealed & 1) ? 1u : 0u) - ((sealed & 4) ? 1u : 0u));
        }
        // Nothing before the end.
        CHECK(SafeItemsFor(0, false, 0, 0).count == 0);
        // A fast clear: the Cinder, the gear, two bags; the tier and the bag follow the difficulty.
        SafeItems const fast = SafeItemsFor(60, false, 0, 0);
        CHECK(fast.count == 4 && fast.items[0] == kItemCinder && fast.items[1] == kGearNormal[0]);
        CHECK(fast.items[2] == 70620 && fast.items[3] == 70620);
        SafeItems const fastH = SafeItemsFor(60, true, 0, 1);
        CHECK(fastH.count == 4 && fastH.items[1] == kGearHeroic[1] && fastH.items[2] == 70623);
        // 80 s: one bag sealed. 95 s: the gear too. 120 s: only the Cinder.
        CHECK(SafeItemsFor(80, false, 0, 0).count == 3);
        SafeItems const slow = SafeItemsFor(95, false, 0, 0);
        CHECK(slow.count == 2 && slow.items[0] == kItemCinder && slow.items[1] == 70620);
        SafeItems const slowest = SafeItemsFor(120, true, 0, 0);
        CHECK(slowest.count == 1 && slowest.items[0] == kItemCinder);
        // The gear is never Doomgrip's (either tier names the same item), and every other one comes up.
        for (std::size_t dropped = 0; dropped < kGearNormal.size(); ++dropped)
            for (bool heroic : { false, true })
            {
                std::uint32_t const his = heroic ? kGearHeroic[dropped] : kGearNormal[dropped];
                std::set<std::uint32_t> picks;
                for (std::uint32_t roll = 0; roll < 30; ++roll)
                {
                    std::uint32_t const pick = PickSafeGear(heroic, his, roll);
                    std::optional<std::size_t> const index = GearIndexOf(pick);
                    CHECK(index.has_value() && *index != dropped);
                    CHECK(index && pick == (heroic ? kGearHeroic[*index] : kGearNormal[*index]));
                    picks.insert(pick);
                }
                CHECK(picks.size() == 3);
                // His normal-tier id excludes the heroic twin too.
                CHECK(GearIndexOf(PickSafeGear(true, kGearNormal[dropped], 7)) != std::optional<std::size_t>(dropped));
            }
        std::set<std::uint32_t> anyPick;
        for (std::uint32_t roll = 0; roll < 40; ++roll)
            anyPick.insert(PickSafeGear(false, 0, roll));
        CHECK(anyPick.size() == 4);
        // The managed set: the Cinder, both bags, both tiers of the four; nothing else.
        CHECK(IsSafeManagedItem(kItemCinder) && IsSafeManagedItem(70620) && IsSafeManagedItem(70623));
        for (std::size_t i = 0; i < kGearNormal.size(); ++i)
            CHECK(IsSafeManagedItem(kGearNormal[i]) && IsSafeManagedItem(kGearHeroic[i]));
        CHECK(!IsSafeManagedItem(70622) && !IsSafeManagedItem(11078) && !IsSafeManagedItem(11197));
        CHECK(kItemBagNormal == 70620 && kItemCinder == 70621);
    }

    void TestLockdown()
    {
        DungeonKit::ArenaRegion const fence = DungeonKit::ArenaRegion::Polygon(FencePolygon(), kFenceZMin, kFenceZMax);
        // The doorway's middle is about 16.7 yd out, along the way out.
        Vec2 const door = DoorwayCenter();
        float const doorAlong = AlongDoorway(door);
        CHECK(doorAlong > 16.f && doorAlong < 17.5f);
        CHECK(std::hypot(kDoorwayA.x - kDoorwayB.x, kDoorwayA.y - kDoorwayB.y) > 7.f);
        CHECK(std::fabs(std::hypot(kDoorwayOut.x, kDoorwayOut.y) - 1.f) < 0.001f);
        CHECK(std::fabs(kDoorwayOut.x * kDoorwayAcross.x + kDoorwayOut.y * kDoorwayAcross.y) < 0.001f);
        // Nothing in the room is in the fence: the center, the posts, Doomgrip's summon (the put-out spot), the coffer
        // doors, the Dark Coffer, the Safe, the doorway's own ends.
        std::array<Vec2, 22> const inside{ {
            kVaultCenter, { 813.6f, -341.8f }, { 819.5f, -349.0f }, { 813.6f, -353.7f }, { 808.0f, -345.9f },
            { kDoomgripSummon.x, kDoomgripSummon.y }, { 802.0f, -353.5f }, { 797.8f, -349.0f }, { 797.9f, -343.7f },
            { 802.3f, -339.5f }, { 811.1f, -331.4f }, { 806.7f, -358.6f }, { 810.9f, -363.1f }, { 816.4f, -363.6f },
            { 820.8f, -359.5f }, { 825.3f, -355.3f }, { 829.6f, -351.3f }, { 806.8f, -335.4f }, { 804.3f, -356.1f },
            { 803.5f, -357.4f }, kDoorwayA, kDoorwayB } };
        for (Vec2 const& p : inside)
        {
            CHECK(!fence.Contains(p, -50.f));
            CHECK(AlongDoorway(p) < kFenceNearYd - 0.5f);
        }
        // The room's rim at its farthest (18.4 yd at bearing 0) is not in it either.
        CHECK(!fence.Contains(Vec2{ kVaultCenter.x + 18.4f, kVaultCenter.y }, -50.f));
        // The corridor past the doorway is: 4 yd past its middle, the hall's near trash spot (828.2, -326.8).
        Vec2 const past{ door.x + kDoorwayOut.x * 4.f, door.y + kDoorwayOut.y * 4.f };
        CHECK(fence.Contains(past, -50.f));
        CHECK(fence.Contains(Vec2{ 828.2f, -326.8f }, -50.2f));
        // Not another floor.
        CHECK(!fence.Contains(past, -70.f));
        // The put-out spot is in the room and in the leash arena.
        CHECK(BlackVaultArena().Contains(Vec2{ kDoomgripSummon.x, kDoomgripSummon.y }, kDoomgripSummon.z));
    }

    void TestStub()
    {
        // Doomgrip is summoned at kDoomgripSummon.P3(), inside the arena (S0's check, kept).
        CHECK(BlackVaultArena().Contains(kDoomgripSummon.P3().XY(), kDoomgripSummon.P3().z));
        CHECK(ArenaFor(BOSS_VAULT).Contains(kDoomgripSummon.P3().XY(), kDoomgripSummon.P3().z));
        CHECK(kSentinelCount == kVaultSentinelPosts.size());
    }

    // R-1-B B1: a sentinel never moves. One knocked or gripped off its post goes back (past 1 yd, checked twice a
    // second), so every warder dies on its post: inside the instance's warder radius and the bots' room bounds.
    // Doomgrip and the Safe find the four by entry alone, within kSentinelSearchYd of the room's center (the far rim
    // is 18 yd).
    void TestSentinelsStayPut()
    {
        CHECK(!OffPost(0.f));
        CHECK(!OffPost(kPostSlackYd));
        CHECK(OffPost(kPostSlackYd + 0.1f));
        CHECK(kPostCheckMs <= 1000);
        for (auto const& post : kVaultSentinelPosts)
        {
            float const d = DungeonKit::Distance(post.XY(), kVaultCenter);
            CHECK(d + kPostSlackYd <= kVaultWarderRadius);
            CHECK(d + kPostSlackYd <= kRoomBoundsYd);
        }
        CHECK(kSentinelSearchYd >= 2.f * 18.f);     // from Doomgrip or the Safe anywhere in the room to the far rim
    }

    // R-2-A MA-2: the dormant look is D9's Stoned copy, and the state is the sentinel's own flag. Once stone, the
    // alarm path stops (no per-tick Dormant / log line); an awake one made stone again cleans up once.
    void TestDormantState()
    {
        CHECK(SPELL_VA_STONED == 211103 && kSpellSlice.Contains(SPELL_VA_STONED));
        CHECK(SPELL_VA_STONED == kSpellVaultStoned);
        CHECK(SentinelNeedsStone(true, false, false));      // the alarm woke it: back to stone
        CHECK(!SentinelNeedsStone(true, true, false));      // already stone: nothing every tick
        CHECK(!SentinelNeedsStone(true, false, true));      // walking home
        CHECK(!SentinelNeedsStone(false, false, false));    // no Vault running
        CHECK(SentinelReStoned(true, true));                // the instance froze an awake one back (a reset)
        CHECK(!SentinelReStoned(true, false));
        CHECK(!SentinelReStoned(false, true));
    }
}

int main()
{
    TestIdsAndTexts();
    TestSpecNumbers();
    TestWakes();
    TestFields();
    TestLink();
    TestDraught();
    TestClockAndSafe();
    TestLockdown();
    TestStub();
    TestSentinelsStayPut();
    TestDormantState();
    return Report("brd_vault_test");
}
