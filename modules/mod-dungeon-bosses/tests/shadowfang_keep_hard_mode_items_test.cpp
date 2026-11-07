// Host tests for SfkHardModeItemsLogic.h (wave 1 dungeon items): the ids sit in the `shadowfang_items` reservation and
// clear the Deadmines item ids, the item spell copy block and the Deadmines creatures, the Voidwalker's distance and
// stay, and its ownership rule. The generated ItemSpellCopies.h lookup returns the base id for a spell with no copy.
#include "../src/ShadowfangKeep/SfkHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <initializer_list>

using namespace SfkHardModeItems;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestIds()
    {
        CHECK(kSpellsShadowfangItems.first == 205600u);
        CHECK(kSpellsShadowfangItems.last == 205619u);
        CHECK(kSpellsShadowfangItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsShadowfangItems.Contains(kSpellsDeclared.last));
        for (std::uint32_t id : { SPELL_VIAL_OF_THE_WORGENS_CURSE, SPELL_ARUGALS_SHADOW_TOME, SPELL_ARUGALS_VOIDWALKER,
                 SPELL_ASHCROMBES_LOCKET, SPELL_METEOR_SHARD_FIREBOLT })
        {
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(!(id >= 205400u && id <= 205599u));           // the `items` reservation (Deadmines, the copies)
            CHECK(!(id >= 205620u && id <= 205699u));           // Scholomance and Stratholme
        }

        // a creature id of its own: clear of the Deadmines kit and the Signet's Blackguard (300420-300449) and of the
        // boss mechanics creatures (300400-300419), inside the tool-wide creature block
        CHECK(NPC_TOME_VOIDWALKER == 300460u);
        CHECK(NPC_TOME_VOIDWALKER >= 300000u && NPC_TOME_VOIDWALKER <= 300999u);
        CHECK(!(NPC_TOME_VOIDWALKER >= 300400u && NPC_TOME_VOIDWALKER <= 300449u));
    }

    void TestVoidwalker()
    {
        CHECK(Near(VoidwalkerDistance(1.5f), 2.5f));
        CHECK(Near(VoidwalkerDistance(0.0f), kVoidwalkerGap));
        CHECK(Near(VoidwalkerDistance(-3.0f), kVoidwalkerGap));  // a bad hit box never puts it inside the target
        CHECK(VoidwalkerDistance(10.0f) > VoidwalkerDistance(1.0f));
        // it outlives the 10 s debuff (the debuff's end sends it away), by little
        CHECK(kVoidwalkerStayMs > 10000u && kVoidwalkerStayMs <= 12000u);
        CHECK(kVoidwalkerSearchRange >= 10.0f);

        CHECK(IsOwnVoidwalker(42u, 42u));
        CHECK(!IsOwnVoidwalker(42u, 43u));                      // another wearer's Voidwalker on the same target
        CHECK(!IsOwnVoidwalker(0u, 0u));                        // no summoner: never anyone's
        CHECK(!IsOwnVoidwalker(0u, 42u));
    }

    void TestTierSpells()
    {
        using ItemSpellCopies::Resolve;
        // a spell with no copy resolves to itself (the 71 tier, or a header generated before these items existed)
        CHECK(Resolve(SPELL_ARUGALS_SHADOW_TOME, SPELL_ARUGALS_VOIDWALKER) == SPELL_ARUGALS_VOIDWALKER);
        CHECK(Resolve(SPELL_ARUGALS_VOIDWALKER, SPELL_ARUGALS_VOIDWALKER) == SPELL_ARUGALS_VOIDWALKER);
        // every copy of a Tome spell resolves the Voidwalker to a copy of the same tier
        for (auto const& c : ItemSpellCopies::kCopies)
        {
            if (c.base != SPELL_ARUGALS_SHADOW_TOME)
                continue;
            std::uint32_t const attack = Resolve(c.copy, SPELL_ARUGALS_VOIDWALKER);
            CHECK(attack != SPELL_ARUGALS_VOIDWALKER);
            bool sameTier = false;
            for (auto const& d : ItemSpellCopies::kCopies)
                if (d.copy == attack)
                    sameTier = d.group == c.group && d.base == SPELL_ARUGALS_VOIDWALKER;
            CHECK(sameTier);
        }
    }
}

int main()
{
    TestIds();
    TestVoidwalker();
    TestTierSpells();
    return Report("shadowfang_keep_hard_mode_items_test");
}
