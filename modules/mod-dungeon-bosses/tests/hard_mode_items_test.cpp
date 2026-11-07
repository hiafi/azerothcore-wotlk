// Host tests for HardModeItemsLogic.h (item variants IV6): the ids sit in their reservations and clear every Deadmines
// slice and kit creature, the keg's blast only goes off where it landed, the keg's flight time, the Blackguard's
// distance, the fuse fallback. IV10: the generated ItemSpellCopies.h lookup the scripts use to cast their own tier's
// copies.
#include "HardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cmath>
#include <cstdint>

using namespace HardModeItems;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }

    void TestIds()
    {
        CHECK(kSpellsItems.first == 205400u);
        CHECK(kSpellsItems.last == 205599u);
        CHECK(kSpellsItems.Contains(kSpellsDeadminesHardModeItems.first));
        CHECK(kSpellsItems.Contains(kSpellsDeadminesHardModeItems.last));
        using namespace DeadminesRework;
        for (std::uint32_t id : { SPELL_POWDER_KEG_FUSE, SPELL_POWDER_KEG_FUSE_LOOK, SPELL_POWDER_KEG_BLAST,
                 SPELL_BLACKGUARDS_SIGNET, SPELL_BLACKGUARD_STRIKE, SPELL_BLACKGUARD_AMBUSH_LOOK,
                 SPELL_LANTERN_OF_ROARING_FLAME, SPELL_ROARING_FLAME_ZONE })
        {
            CHECK(kSpellsDeadminesHardModeItems.Contains(id));
            for (IdSlice slice : { kSpellsShared, kSpellsRhahkZor, kSpellsMinerJohnson, kSpellsSneed, kSpellsGilnid,
                     kSpellsMrSmite, kSpellsCookie, kSpellsGreenskin, kSpellsVanCleef, kSpellsHardMode,
                     kSpellsSpare })
                CHECK(!slice.Contains(id));
        }

        // the first id of the `deadmines` creature spare (300430-300449), clear of every kit creature
        CHECK(NPC_SIGNET_BLACKGUARD == 300430u);
        for (std::uint32_t kit : { NPC_DM_WATCHMAN, NPC_DM_EVOKER, NPC_DM_WORKING_MINER, NPC_DM_IRON_SHOT,
                 NPC_DM_LAND_MINE, NPC_DM_HARPOON_ROPE_ANCHOR, NPC_DM_BLACKGUARD, NPC_DM_SHADOW_IMAGE,
                 NPC_DM_POWDER_STALKER })
        {
            CHECK(kit != NPC_SIGNET_BLACKGUARD);
            CHECK(kit >= 300420u && kit < 300430u);
        }
    }

    void TestKeg()
    {
        Place const lit{ 36, 7 };
        CHECK(KegStillLive(true, lit, Place{ 36, 7 }));
        CHECK(!KegStillLive(false, lit, Place{ 36, 7 }));   // logged out or removed
        CHECK(!KegStillLive(true, lit, Place{ 0, 0 }));     // teleported out
        CHECK(!KegStillLive(true, lit, Place{ 36, 8 }));    // another copy of the dungeon

        CHECK(KegFuseMs(2000) == 2000u);
        CHECK(KegFuseMs(3500) == 3500u);                    // the spell data wins
        CHECK(KegFuseMs(0) == kKegFuseFallbackMs);
        CHECK(KegFuseMs(-1) == kKegFuseFallbackMs);         // an endless duration is never a fuse
        CHECK(kKegFuseFallbackMs == 2000u);

        // the missile's flight, as the engine times it (5 yd at least, floored): 30 yd at speed 20 is 1.5 s
        CHECK(KegFlightMs(30.0f, 20.0f) == 1500u);
        CHECK(KegFlightMs(10.0f, 20.0f) == 500u);
        CHECK(KegFlightMs(2.0f, 20.0f) == 250u);            // under 5 yd counts as 5
        CHECK(KegFlightMs(0.0f, 20.0f) == 250u);
        CHECK(KegFlightMs(7.0f, 20.0f) == 350u);
        CHECK(KegFlightMs(12.3f, 20.0f) == 615u);
        CHECK(KegFlightMs(30.0f, 0.0f) == 0u);              // no speed, no flight
        CHECK(KegFlightMs(30.0f, -1.0f) == 0u);
    }

    void TestBlackguard()
    {
        CHECK(Near(BlackguardDistance(1.5f), 2.5f));
        CHECK(Near(BlackguardDistance(0.0f), kBlackguardGap));
        CHECK(Near(BlackguardDistance(-3.0f), kBlackguardGap));
        CHECK(BlackguardDistance(10.0f) > BlackguardDistance(1.0f));
        CHECK(kBlackguardStayMs >= 1000u && kBlackguardStayMs <= 5000u);
    }

    // IV10: each tier above 71 carries its own copies; a script resolves the spell it casts from the spell or aura it
    // runs for.
    void TestTierSpells()
    {
        using ItemSpellCopies::Resolve;
        // the declared (71) spells resolve to themselves
        for (std::uint32_t base : { SPELL_POWDER_KEG_FUSE, SPELL_BLACKGUARDS_SIGNET, SPELL_LANTERN_OF_ROARING_FLAME })
        {
            CHECK(Resolve(base, SPELL_POWDER_KEG_BLAST) == SPELL_POWDER_KEG_BLAST);
            CHECK(Resolve(base, SPELL_ROARING_FLAME_ZONE) == SPELL_ROARING_FLAME_ZONE);
        }
        CHECK(Resolve(0, SPELL_BLACKGUARD_STRIKE) == SPELL_BLACKGUARD_STRIKE);

        // three tiers (81 / 91 / 101) of three families: keg (use, look, blast), signet (aura, strike), lantern
        // (use, zone). The header holds every dungeon's copies; these checks take the Deadmines ones.
        int deadmines = 0;
        for (std::size_t i = 0; i < ItemSpellCopies::kCopyCount; ++i)
            if (kSpellsDeadminesHardModeItems.Contains(ItemSpellCopies::kCopies[i].base))
                ++deadmines;
        CHECK(deadmines == 21);
        int roots = 0;
        for (std::size_t i = 0; i < ItemSpellCopies::kCopyCount; ++i)
        {
            ItemSpellCopies::Copy const& c = ItemSpellCopies::kCopies[i];
            CHECK(c.copy > kSpellsDeadminesHardModeItems.last);         // a copy never takes a declared id
            CHECK(kSpellsItems.Contains(c.copy));
            if (!kSpellsDeadminesHardModeItems.Contains(c.base))
                continue;                                               // another dungeon's copy
            CHECK(c.base != SPELL_BLACKGUARD_AMBUSH_LOOK);               // the Blackguard's own look is not copied
            CHECK(ItemSpellCopies::GroupOf(c.copy) == c.group);
            CHECK(Resolve(c.copy, c.base) == c.copy);                   // a copy resolves itself
            // every spell of the tier resolves from every other spell of the same tier
            for (std::size_t j = 0; j < ItemSpellCopies::kCopyCount; ++j)
            {
                ItemSpellCopies::Copy const& d = ItemSpellCopies::kCopies[j];
                if (d.group == c.group)
                    CHECK(Resolve(c.copy, d.base) == d.copy);
                else if (d.base == c.base)
                    CHECK(Resolve(c.copy, d.base) != d.copy);           // never another tier's copy
            }
            CHECK(Resolve(c.copy, SPELL_BLACKGUARD_AMBUSH_LOOK) == SPELL_BLACKGUARD_AMBUSH_LOOK);
            if (c.base == SPELL_POWDER_KEG_FUSE || c.base == SPELL_BLACKGUARDS_SIGNET
                || c.base == SPELL_LANTERN_OF_ROARING_FLAME)
            {
                ++roots;
                CHECK(c.group == c.copy);                               // the item spell is its tier's first copy
            }
        }
        CHECK(roots == 9);
        // the first keg tier, spelled out: its use, look and blast are 205410-205412
        CHECK(Resolve(205410u, SPELL_POWDER_KEG_FUSE_LOOK) == 205411u);
        CHECK(Resolve(205410u, SPELL_POWDER_KEG_BLAST) == 205412u);
        CHECK(Resolve(205413u, SPELL_POWDER_KEG_BLAST) == 205415u);
        static_assert(ItemSpellCopies::Resolve(205410u, SPELL_POWDER_KEG_BLAST) == 205412u);
    }
}

int main()
{
    TestIds();
    TestKeg();
    TestBlackguard();
    TestTierSpells();
    return Report("hard_mode_items_test");
}
