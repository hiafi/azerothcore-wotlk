// Host tests for HauntedSetLogic.h (dungeon sets, the Haunted set bonuses): the ids sit in the `haunted_set`
// reservation, ten per set, clear of every other item effect block; the Proc Chance scaling of a script roll; Wraith
// Volley's two chances; Lingering Death's longer duration; the Gathering Chorus multiplier; Unbroken Faith's mana
// threshold; Bone Ward's absorb; Deathless's 35% crossing; and the most injured ally order.
#include "../src/DungeonSets/HauntedSetLogic.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <set>

using namespace HauntedSet;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }

    std::uint32_t constexpr kAllSpells[] = {
        SPELL_WRAITH_VOLLEY, SPELL_WRAITH_VOLLEY_BOLT, SPELL_SOUL_REND, SPELL_SOUL_REND_DEBUFF,
        SPELL_SOUL_SHROUD, SPELL_SOUL_SHROUD_BUFF, SPELL_WRAITH_OF_SOLACE, SPELL_WRAITH_OF_SOLACE_HEAL,
        SPELL_LINGERING_DEATH, SPELL_GRAVE_BLOOM, SPELL_GRAVE_BLOOM_HEAL, SPELL_GRAVE_BLOOM_DAMAGE,
        SPELL_FROZEN_CHORUS, SPELL_FROZEN_CHORUS_DAMAGE, SPELL_FROZEN_CHORUS_HEAL, SPELL_GATHERING_CHORUS,
        SPELL_GATHERING_CHORUS_STACK, SPELL_UNBROKEN_FAITH, SPELL_UNBROKEN_FAITH_BUFF, SPELL_SOUL_RELEASED,
        SPELL_SOUL_RELEASED_HEAL, SPELL_SOUL_RELEASED_DAMAGE, SPELL_BONE_SHATTER, SPELL_BONE_SHATTER_BURST,
        SPELL_BROKEN_BONES, SPELL_BROKEN_BONES_BUFF, SPELL_HAUNTING_MARK, SPELL_HAUNTING_MARK_DEBUFF,
        SPELL_GRASP_OF_THE_DEAD, SPELL_GRASP_OF_THE_DEAD_MELEE, SPELL_GRASP_OF_THE_DEAD_RANGED, SPELL_WRAITH_VENOM,
        SPELL_WRAITH_VENOM_DOT, SPELL_GRAVE_ROT, SPELL_GRAVE_ROT_STRIKE, SPELL_GRAVE_HIDE, SPELL_BONE_WARD,
        SPELL_BONE_WARD_ABSORB, SPELL_SPIRIT_BULWARK, SPELL_SPIRIT_BULWARK_HEAL, SPELL_DEATHLESS, SPELL_DEATHLESS_HOT,
    };

    // The 3 and 5 piece bonus of every set: the decade's first two-ish ids, never a payout.
    std::uint32_t constexpr kBonuses[] = {
        SPELL_WRAITH_VOLLEY, SPELL_SOUL_REND, SPELL_SOUL_SHROUD, SPELL_WRAITH_OF_SOLACE, SPELL_LINGERING_DEATH,
        SPELL_GRAVE_BLOOM, SPELL_FROZEN_CHORUS, SPELL_GATHERING_CHORUS, SPELL_UNBROKEN_FAITH, SPELL_SOUL_RELEASED,
        SPELL_BONE_SHATTER, SPELL_BROKEN_BONES, SPELL_HAUNTING_MARK, SPELL_GRASP_OF_THE_DEAD, SPELL_WRAITH_VENOM,
        SPELL_GRAVE_ROT, SPELL_GRAVE_HIDE, SPELL_BONE_WARD, SPELL_SPIRIT_BULWARK, SPELL_DEATHLESS,
    };

    void TestIds()
    {
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : kAllSpells)
        {
            CHECK(kSpellsHauntedSet.Contains(id));
            CHECK(kSpellsHauntedSetBonuses.Contains(id));
            CHECK(seen.insert(id).second);
        }
        CHECK(seen.size() == 42);
        // Ten per set: 20 bonuses, two per decade 205700-205799.
        std::set<std::uint32_t> decades;
        for (std::uint32_t id : kBonuses)
            decades.insert((id - kSpellsHauntedSet.first) / 10);
        CHECK(decades.size() == 10);
        // Clear of the item effect blocks below it (items 205400-205599, scholomance and stratholme items
        // 205620-205699) and of the Deadmines kit.
        CHECK(kSpellsHauntedSet.first > 205699);
        CHECK(kSpellsHauntedSet.last == 205899);
    }

    void TestProcChance()
    {
        CHECK(Near(ProcChancePct(10.0f, 0.0f), 10.0f));
        CHECK(Near(ProcChancePct(10.0f, 25.0f), 12.5f));
        CHECK(Near(ProcChancePct(8.0f, 50.0f), 12.0f));
        CHECK(Near(ProcChancePct(60.0f, 100.0f), 100.0f));  // capped
        CHECK(Near(ProcChancePct(10.0f, -5.0f), 10.0f));    // a negative Proc Chance never lowers it
        CHECK(WraithVolleyBasePct(false) == 10);
        CHECK(WraithVolleyBasePct(true) == 4);
    }

    void TestLingeringDeath()
    {
        CHECK(LingeringDeathDuration(12000) == 13200);
        CHECK(LingeringDeathDuration(15000) == 16500);
        CHECK(LingeringDeathDuration(18000) == 19800);
        CHECK(LingeringDeathDuration(-1) == -1);   // permanent
        CHECK(LingeringDeathDuration(0) == 0);
        CHECK(LingeringDeathDuration(0x7FFFFFFF) == 0x7FFFFFFF);  // no overflow
    }

    void TestGatheringChorus()
    {
        CHECK(GatheringChorusPct(0, 20) == 100);
        CHECK(GatheringChorusPct(1, 20) == 120);
        CHECK(GatheringChorusPct(5, 20) == 200);
        CHECK(GatheringChorusPct(9, 20) == 200);  // at most 5 count
        CHECK(GatheringChorusPct(3, -20) == 100);
        CHECK(ScalePct(1000, 200) == 2000);
        CHECK(ScalePct(999, 115) == 1148);
        CHECK(ScalePct(0, 150) == 0);
        CHECK(ScalePct(-5, 150) == 0);
        CHECK(ScalePct(0x7FFFFFFF, 200) == 0x7FFFFFFF);
    }

    void TestUnbrokenFaith()
    {
        CHECK(UnbrokenFaithHolds(8001, 10000));
        CHECK(!UnbrokenFaithHolds(8000, 10000));  // strictly above 80%
        CHECK(!UnbrokenFaithHolds(0, 10000));
        CHECK(!UnbrokenFaithHolds(0, 0));         // no mana pool
        CHECK(UnbrokenFaithHolds(10000, 10000));
    }

    void TestBoneWard()
    {
        CHECK(BoneWardAmount(10000, 1) == 300);
        CHECK(BoneWardAmount(10000, 3) == 900);
        CHECK(BoneWardAmount(10000, 0) == 300);   // a fresh ward is one stack
        CHECK(BoneWardAmount(0xFFFFFFFFu, 3) > 0);
    }

    void TestDeathless()
    {
        // 10,000 health: 3,500 is the line.
        CHECK(DeathlessCrossed(3400, 1000, 10000));    // 4,400 -> 3,400
        CHECK(DeathlessCrossed(3499, 1, 10000));       // 3,500 -> 3,499
        CHECK(!DeathlessCrossed(3500, 1000, 10000));   // still at 35%
        CHECK(!DeathlessCrossed(3000, 400, 10000));    // already below before the hit
        CHECK(!DeathlessCrossed(0, 5000, 10000));      // dead
        CHECK(!DeathlessCrossed(3000, 0, 10000));      // no damage
        CHECK(!DeathlessCrossed(3000, 1000, 0));
    }

    void TestGraveRotCap()
    {
        // 2 s a time, 6 s at most per application.
        CHECK(GraveRotGrantMs(0) == 2000);
        CHECK(GraveRotGrantMs(4000) == 2000);
        CHECK(GraveRotGrantMs(5000) == 1000);  // the last 1 s of the cap
        CHECK(GraveRotGrantMs(6000) == 0);
        CHECK(GraveRotGrantMs(9000) == 0);
        CHECK(GraveRotGrantMs(-50) == 2000);

        // One application, extended four times: 2 + 2 + 2 + 0.
        GraveRotRecord record;
        std::int64_t const applied = 1000;
        std::int32_t maxDuration = 16000;  // a Rupture
        std::uint32_t tick = 1;
        std::int32_t total = 0;
        for (int n = 0; n < 4; ++n)
        {
            std::int32_t const soFar = GraveRotExtendedSoFar(n ? &record : nullptr, applied, maxDuration, tick);
            std::int32_t const grant = GraveRotGrantMs(soFar);
            total += grant;
            maxDuration += grant;
            ++tick;
            record = GraveRotRecord{ applied, maxDuration, tick - 1, soFar + grant };
        }
        CHECK(total == 6000);
        CHECK(maxDuration == 22000);

        // A refresh: the maximum duration goes back to the spell's and the tick count to 0 -> a fresh 6 s.
        CHECK(GraveRotExtendedSoFar(&record, applied, 16000, 0) == 0);
        // The same maximum duration again but the ticks start over (a refresh that lands on the same number).
        CHECK(GraveRotExtendedSoFar(&record, applied, maxDuration, 0) == 0);
        // A new application: another apply time.
        CHECK(GraveRotExtendedSoFar(&record, applied + 5, maxDuration, tick) == 0);
        // Untouched since the last extension: the budget stays spent.
        CHECK(GraveRotExtendedSoFar(&record, applied, maxDuration, tick) == 6000);
        CHECK(GraveRotGrantMs(GraveRotExtendedSoFar(&record, applied, maxDuration, tick)) == 0);
        CHECK(kGraveRotExtendCapMs == 3 * kGraveRotExtendMs);
    }

    void TestMostInjured()
    {
        CHECK(MoreInjured(500, 1000, 600, 1000));
        CHECK(!MoreInjured(600, 1000, 500, 1000));
        CHECK(MoreInjured(4000, 10000, 500, 1000));  // 40% before 50%
        CHECK(!MoreInjured(500, 1000, 500, 1000));   // a tie keeps the first
    }

    void TestScriptNumbers()
    {
        // The tooltip literals of haunted_set_bonuses.py (lib/test_haunted_set.py reads them back from this header).
        CHECK(kWraithVolleyExtraTargets == 2);
        CHECK(Near(kWraithVolleyRadius, 10.0f));
        CHECK(Near(kSolaceRange, 30.0f));
        CHECK(Near(kGraveBloomRadius, 15.0f));
        CHECK(kGatheringChorusMaxStacks == 5);
        CHECK(kUnbrokenFaithManaPct == 80);
        CHECK(Near(kSoulReleasedHealRange, 30.0f));
        CHECK(Near(kSoulReleasedEnemyRange, 20.0f));
        CHECK(kWraithVenomPct == 8 && kWraithVenomCooldownMs == 2000);
        CHECK(kGraveRotPct == 6 && kGraveRotCooldownMs == 3000 && kGraveRotExtendMs == 2000);
        CHECK(kBoneWardPctPerStack == 3);
        CHECK(kDeathlessHealthPct == 35);
        CHECK(kLingeringDeathPct == 10);
    }
}

int main()
{
    TestIds();
    TestProcChance();
    TestLingeringDeath();
    TestGatheringChorus();
    TestUnbrokenFaith();
    TestBoneWard();
    TestDeathless();
    TestGraveRotCap();
    TestMostInjured();
    TestScriptNumbers();
    return Report("haunted_set_test");
}
