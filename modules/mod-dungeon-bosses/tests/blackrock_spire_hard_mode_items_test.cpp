// Host tests for BlackrockSpireHardModeItemsLogic.h (wave 2 dungeon items): the ids sit in the `blackrock_spire_items`
// reservation and clear the other item reservations and the item spell copy block, the Ward of the Three Tribes stack
// count, the Champion's Mark award rule. The generated ItemSpellCopies.h lookup returns the base id for a spell with no
// copy: none of the Blackrock Spire effects scales, so none has one.
#include "../src/BlackrockSpire/BlackrockSpireHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace BlackrockSpireHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsBlackrockSpireItems.first == 206800u);
        CHECK(kSpellsBlackrockSpireItems.last == 206829u);
        CHECK(kSpellsBlackrockSpireItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsBlackrockSpireItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = 206800;
        for (std::uint32_t id : { SPELL_BLOODAXE_WAR_HORN, SPELL_BLOODAXE_WAR_CRY, SPELL_WARD_OF_THE_THREE_TRIBES,
                 SPELL_WARD_BUFF, SPELL_SHARDSTAFF_OF_STOLEN_POWER, SPELL_STOLEN_POWER, SPELL_TROPHY_OF_THE_CHAMPION,
                 SPELL_CHAMPIONS_MARK, SPELL_CHAMPIONS_TROPHY, SPELL_ORDERS_OF_THE_GENERAL, SPELL_THE_HUMBLER,
                 SPELL_HUMBLED })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(!(id >= 205400u && id <= 205599u));       // the Deadmines item effects and the item spell copy block
            CHECK(!(id >= 205660u && id <= 205699u));       // the Stratholme item effects
            CHECK(!(id >= 206830u && id <= 206999u));       // the Blackrock Depths items and the Molten set
        }
        CHECK(expected == kSpellsDeclared.last + 1);
    }

    void TestNoCopies()
    {
        // None of the effects scales by item level, so each resolves to itself whatever spell it runs for.
        for (std::uint32_t id : { SPELL_BLOODAXE_WAR_HORN, SPELL_WARD_OF_THE_THREE_TRIBES, SPELL_WARD_BUFF,
                 SPELL_TROPHY_OF_THE_CHAMPION, SPELL_CHAMPIONS_MARK, SPELL_CHAMPIONS_TROPHY })
        {
            CHECK(ItemSpellCopies::Resolve(id, id) == id);
            CHECK(ItemSpellCopies::Resolve(SPELL_WARD_OF_THE_THREE_TRIBES, id) == id);
            CHECK(ItemSpellCopies::Resolve(0, id) == id);
        }
    }

    void TestWard()
    {
        CHECK(WardStacks(0, 5) == 0);                       // nobody attacking: no buff
        CHECK(WardStacks(1, 5) == 1);
        CHECK(WardStacks(3, 5) == 3);
        CHECK(WardStacks(5, 5) == 5);
        CHECK(WardStacks(6, 5) == 5);                       // up to 5
        CHECK(WardStacks(40, 5) == 5);
        CHECK(WardStacks(3, 0) == 0);                       // no cap, no stacks
        CHECK(WardStacks(3, -2) == 0);
        CHECK(WardStacks(1000, 1000) == 255);               // the aura's counter is 8 bits
        CHECK(WardStacks(4294967295u, 5) == 5);
    }

    void TestTrophy()
    {
        CHECK(ChampionEarnsTrophy(true, true, true));
        CHECK(!ChampionEarnsTrophy(false, true, true));     // ran out, was removed or the target evaded
        CHECK(!ChampionEarnsTrophy(true, false, true));     // the wearer is dead
        CHECK(!ChampionEarnsTrophy(true, true, false));     // the Trophy was taken off
        CHECK(!ChampionEarnsTrophy(false, false, false));
    }
}

int main()
{
    TestIds();
    TestNoCopies();
    TestWard();
    TestTrophy();
    return Report("blackrock_spire_hard_mode_items_test");
}
