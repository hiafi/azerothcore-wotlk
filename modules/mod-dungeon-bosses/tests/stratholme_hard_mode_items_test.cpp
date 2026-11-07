// Host tests for StratholmeHardModeItemsLogic.h (wave 1 dungeon items): the ids sit in the `stratholme_items`
// reservation and clear the Deadmines item ids and the item spell copy block, Ysida's Locket's health threshold and
// pick, the Two-Faced Tome's share, the Condemned damage and its reset rule. The generated ItemSpellCopies.h lookup
// returns the base id for a spell with no copy.
#include "../src/Stratholme/StratholmeHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace StratholmeHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsStratholmeItems.first == 205660u);
        CHECK(kSpellsStratholmeItems.last == 205699u);
        CHECK(kSpellsStratholmeItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsStratholmeItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = 205660;
        for (std::uint32_t id : { SPELL_CARRION_SIGNET, SPELL_CARRION_SWARM, SPELL_DUST_OF_THE_NATHREZIM,
                 SPELL_TWO_FACED_TOME, SPELL_THE_LIE, SPELL_YSIDAS_LOCKET, SPELL_YSIDAS_WARD,
                 SPELL_YSIDAS_LOCKET_LOCKOUT, SPELL_BLADE_OF_THE_CONDEMNED, SPELL_CONDEMNED, SPELL_DEATHCHARGERS_SPUR,
                 SPELL_DEATHCHARGER_TRAMPLE, SPELL_SPECTRAL_DEATHCHARGER })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(!(id >= 205400u && id <= 205409u));       // the Deadmines hard mode item effects
            CHECK(!(id >= 205410u && id <= 205599u));       // the item spell copy block
        }
        CHECK(expected == kSpellsDeclared.last + 1);
    }

    void TestCopies()
    {
        // A spell with no copy resolves to itself (the 71 tier, or an unscaled effect such as the Condemned debuff).
        CHECK(ItemSpellCopies::Resolve(SPELL_CONDEMNED, SPELL_CONDEMNED) == SPELL_CONDEMNED);
        CHECK(ItemSpellCopies::Resolve(SPELL_YSIDAS_LOCKET, SPELL_YSIDAS_WARD) == SPELL_YSIDAS_WARD);
        CHECK(ItemSpellCopies::Resolve(SPELL_DEATHCHARGERS_SPUR, SPELL_DEATHCHARGER_TRAMPLE)
            == SPELL_DEATHCHARGER_TRAMPLE);
    }

    void TestLocket()
    {
        CHECK(BelowHealthPct(19, 100, 20));
        CHECK(!BelowHealthPct(20, 100, 20));                // "falls below 20%": exactly 20% is not below
        CHECK(!BelowHealthPct(21, 100, 20));
        CHECK(BelowHealthPct(1999, 10000, 20));
        CHECK(!BelowHealthPct(2000, 10000, 20));
        CHECK(!BelowHealthPct(0, 100, 20));                 // dead
        CHECK(!BelowHealthPct(10, 0, 20));                  // no maximum
        CHECK(!BelowHealthPct(10, 100, 0));                 // no threshold
        CHECK(!BelowHealthPct(10, 100, -5));
        CHECK(BelowHealthPct(4000000000u, 4294967295u, 100)); // no overflow near the top

        CHECK(LowerHealthFraction(10, 100, 15, 100));
        CHECK(!LowerHealthFraction(15, 100, 10, 100));
        CHECK(!LowerHealthFraction(10, 100, 10, 100));      // a tie keeps the first pick
        CHECK(LowerHealthFraction(1500, 10000, 300, 1000)); // 15% before 30%, whatever the pools
        CHECK(!LowerHealthFraction(300, 1000, 1500, 10000));
    }

    void TestLie()
    {
        CHECK(LieDamage(1000, 25) == 250);
        CHECK(LieDamage(1001, 25) == 250);                  // rounded down
        CHECK(LieDamage(3, 25) == 0);
        CHECK(LieDamage(0, 25) == 0);
        CHECK(LieDamage(1000, 0) == 0);
        CHECK(LieDamage(1000, -10) == 0);
        CHECK(LieDamage(4294967295u, 100) == 0x7FFFFFFF);   // clamped to an int32 spell value
    }

    void TestCondemned()
    {
        CHECK(CondemnedDamage(1000, 1) == 1010);            // one stack
        CHECK(CondemnedDamage(1000, 5) == 1050);            // five stacks (the engine multiplies the amount)
        CHECK(CondemnedDamage(999, 5) == 1048);             // rounded down
        CHECK(CondemnedDamage(1000, 0) == 1000);
        CHECK(CondemnedDamage(1000, -3) == 1000);
        CHECK(CondemnedDamage(0, 5) == 0);
        CHECK(CondemnedDamage(4294967295u, 5) == 4294967295u); // clamped

        CHECK(!CondemnResets(0, 42));                       // the first target
        CHECK(!CondemnResets(42, 42));                      // the same target
        CHECK(CondemnResets(42, 43));                       // another target
    }
}

int main()
{
    TestIds();
    TestCopies();
    TestLocket();
    TestLie();
    TestCondemned();
    return Report("stratholme_hard_mode_items_test");
}
