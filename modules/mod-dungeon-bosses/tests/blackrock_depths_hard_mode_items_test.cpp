// Host tests for BlackrockDepthsHardModeItemsLogic.h (wave 2 dungeon items): the ids sit in the
// `blackrock_depths_items` reservation and clear the item spell copy block, Theldren's threshold and damage, Korv's
// share and pick, the Power Core's orb targets, the Orb's beam test and the look ownership rule. The generated
// ItemSpellCopies.h lookup returns the base id for a spell with no copy.
#include "../src/BlackrockDepths/BlackrockDepthsHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace BlackrockDepthsHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsBlackrockDepthsItems.first == 206830u);
        CHECK(kSpellsBlackrockDepthsItems.last == 206899u);
        CHECK(kSpellsBlackrockDepthsItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsBlackrockDepthsItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = 206830;
        for (std::uint32_t id : { SPELL_THELDRENS_EXECUTIONER, SPELL_LEFTYS_SHIV, SPELL_VICIOUS_WOUND,
                 SPELL_KORVS_SPIRIT_FETISH, SPELL_SPIRIT_CHAIN, SPELL_BLACK_ANVIL_BULWARK, SPELL_ANVIL_ERUPTION,
                 SPELL_FIST_OF_THE_LAKE_LORD, SPELL_LAKE_LORDS_SLAM, SPELL_SCEPTER_OF_THE_MOLTEN_LAKE,
                 SPELL_LAVA_SPAWN, SPELL_MOLTEN_HURL, SPELL_PROTOTYPE_POWER_CORE, SPELL_ARCANE_ORB_STRIKE,
                 SPELL_GOLEMWRIGHTS_MENDING_ROD, SPELL_MENDING_SERVO, SPELL_SERVO_MEND, SPELL_ELECTRONS_LETHAL_COIL,
                 SPELL_LETHAL_ATTRACTION, SPELL_LETHAL_ARC, SPELL_VOLCANIC_HEARTSTONE, SPELL_HEARTSTONE_ERUPTION,
                 SPELL_ORB_OF_THE_SORCERER_THANE, SPELL_SHADOW_BEAM })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(!(id >= 205410u && id <= 205599u));       // the item spell copy block
            CHECK(!(id >= 206800u && id <= 206829u));       // Blackrock Spire's items
            CHECK(!(id >= 206900u && id <= 206999u));       // the Molten set
        }
        CHECK(expected == kSpellsDeclared.last + 1);

        CHECK(kCreaturesBlackrockDepthsItems.Contains(NPC_LAVA_SPAWN));
        CHECK(kCreaturesBlackrockDepthsItems.Contains(NPC_MENDING_SERVO));
        CHECK(NPC_LAVA_SPAWN == 300655u);
        CHECK(NPC_MENDING_SERVO == 300656u);
    }

    void TestCopies()
    {
        // A spell with no copy resolves to itself (the 71 tier, or an unscaled effect such as the Spirit Chain).
        CHECK(ItemSpellCopies::Resolve(SPELL_KORVS_SPIRIT_FETISH, SPELL_SPIRIT_CHAIN) == SPELL_SPIRIT_CHAIN);
        CHECK(ItemSpellCopies::Resolve(SPELL_SCEPTER_OF_THE_MOLTEN_LAKE, SPELL_LAVA_SPAWN) == SPELL_LAVA_SPAWN);
        CHECK(ItemSpellCopies::Resolve(SPELL_ELECTRONS_LETHAL_COIL, SPELL_LETHAL_ARC) == SPELL_LETHAL_ARC);
    }

    void TestLookTimes()
    {
        CHECK(kLookStayMs > 10000u);                        // outlasts the 10 sec buff it fights under
        CHECK(kLookStayMs < 25000u);                        // gone before the 25 sec proc cooldown ends
        CHECK(kLookSearchRange >= 40.0f);
        CHECK(IsOwnLook(42, 42));
        CHECK(!IsOwnLook(42, 43));
        CHECK(!IsOwnLook(0, 0));                            // no summoner is nobody's look
    }

    void TestExecutioner()
    {
        CHECK(BelowHealthPct(29, 100, 30));
        CHECK(!BelowHealthPct(30, 100, 30));                // "below 30%": exactly 30% is not below
        CHECK(!BelowHealthPct(0, 100, 30));                 // dead
        CHECK(!BelowHealthPct(10, 0, 30));
        CHECK(!BelowHealthPct(10, 100, 0));
        CHECK(BelowHealthPct(4000000000u, 4294967295u, 100)); // no overflow near the top

        CHECK(GrownDamage(1000, 10) == 1100);
        CHECK(GrownDamage(999, 10) == 1098);                // rounded down
        CHECK(GrownDamage(1000, 0) == 1000);
        CHECK(GrownDamage(1000, -5) == 1000);
        CHECK(GrownDamage(0, 10) == 0);
        CHECK(GrownDamage(4294967295u, 10) == 4294967295u); // clamped
    }

    void TestFetish()
    {
        CHECK(ShareOfHeal(1000, 50) == 500);
        CHECK(ShareOfHeal(1001, 50) == 500);                // rounded down
        CHECK(ShareOfHeal(1, 50) == 0);
        CHECK(ShareOfHeal(1000, 0) == 0);
        CHECK(ShareOfHeal(1000, -10) == 0);
        CHECK(ShareOfHeal(4294967295u, 100) == 0x7FFFFFFF); // clamped to an int32 spell value

        CHECK(IsInjured(99, 100));
        CHECK(!IsInjured(100, 100));                        // full health is not injured
        CHECK(!IsInjured(0, 100));                          // dead

        CHECK(LowerHealthFraction(10, 100, 15, 100));
        CHECK(!LowerHealthFraction(15, 100, 10, 100));
        CHECK(!LowerHealthFraction(10, 100, 10, 100));      // a tie keeps the first pick
        CHECK(LowerHealthFraction(1500, 10000, 300, 1000)); // 15% before 30%, whatever the pools
    }

    void TestPowerCore()
    {
        CHECK(OrbTargetIndex(0, 0) == -1);                  // nothing to strike
        CHECK(OrbTargetIndex(2, 0) == -1);
        CHECK(OrbTargetIndex(0, 1) == 0);                   // one enemy: every orb on it
        CHECK(OrbTargetIndex(1, 1) == 0);
        CHECK(OrbTargetIndex(2, 1) == 0);
        CHECK(OrbTargetIndex(0, 2) == 0);                   // two enemies: the third orb goes back to the first
        CHECK(OrbTargetIndex(1, 2) == 1);
        CHECK(OrbTargetIndex(2, 2) == 0);
        CHECK(OrbTargetIndex(0, 5) == 0);                   // enough enemies: three different ones
        CHECK(OrbTargetIndex(1, 5) == 1);
        CHECK(OrbTargetIndex(2, 5) == 2);
    }

    void TestBeam()
    {
        // From (0, 0) to (10, 0), 2 yd half width.
        CHECK(OnBeam(5.0f, 0.0f, 0.0f, 0.0f, 10.0f, 0.0f, 2.0f));      // on the line
        CHECK(OnBeam(5.0f, 1.9f, 0.0f, 0.0f, 10.0f, 0.0f, 2.0f));      // inside the width
        CHECK(OnBeam(5.0f, -2.0f, 0.0f, 0.0f, 10.0f, 0.0f, 2.0f));     // on the edge
        CHECK(!OnBeam(5.0f, 2.1f, 0.0f, 0.0f, 10.0f, 0.0f, 2.0f));     // outside the width
        CHECK(!OnBeam(-1.0f, 0.0f, 0.0f, 0.0f, 10.0f, 0.0f, 2.0f));    // behind the wearer
        CHECK(!OnBeam(11.0f, 0.0f, 0.0f, 0.0f, 10.0f, 0.0f, 2.0f));    // past the target
        CHECK(OnBeam(10.0f, 0.0f, 0.0f, 0.0f, 10.0f, 0.0f, 2.0f));     // the target itself
        // A diagonal beam from (0, 0) to (10, 10): (5, 6) is about 0.71 yd off the line.
        CHECK(OnBeam(5.0f, 6.0f, 0.0f, 0.0f, 10.0f, 10.0f, 2.0f));
        CHECK(!OnBeam(2.0f, 8.0f, 0.0f, 0.0f, 10.0f, 10.0f, 2.0f));    // about 4.2 yd off
        // A zero-length beam holds only its own end.
        CHECK(OnBeam(1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 2.0f));
        CHECK(!OnBeam(4.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 2.0f));
    }
}

int main()
{
    TestIds();
    TestCopies();
    TestLookTimes();
    TestExecutioner();
    TestFetish();
    TestPowerCore();
    TestBeam();
    return Report("blackrock_depths_hard_mode_items_test");
}
