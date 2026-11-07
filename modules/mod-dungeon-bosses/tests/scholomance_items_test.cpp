// Host tests for ScholomanceItemsLogic.h (wave 1 dungeon items, Scholomance): the ids sit in their reservation, clear
// of the Deadmines item effects and the per-tier copy block; the portal's distance; the Phylactery Shard's tally and
// heal; the Bonechill Blade's once-per-cast stamp; the Transfer Papers' target rules; and the Portal Rod's barrage
// lookup in the generated ItemSpellCopies.h (each tier's rod casts its own tier's barrage).
#include "../src/Scholomance/ScholomanceItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cmath>
#include <cstdint>
#include <limits>

using namespace ScholomanceItems;

namespace
{
    bool Near(float a, float b, float eps = 0.001f)
    {
        return std::fabs(a - b) <= eps;
    }

    std::uint32_t constexpr kAllSpells[] = {
        SPELL_SPARE_RIB, SPELL_JAR_OF_TORN_SOULS, SPELL_TORN_SOUL, SPELL_RIB_SPREADER, SPELL_OPEN_WOUND,
        SPELL_SPECIMEN_LAUNCHER, SPELL_SPECIMEN_ACID, SPELL_THE_DEANS_ROD, SPELL_DEMERIT, SPELL_SUTURE_KIT,
        SPELL_STITCHES, SPELL_PHYLACTERY_SHARD, SPELL_PHYLACTERY_MEND, SPELL_FROSTWHISPERS_CHILLBAND, SPELL_CHILL,
        SPELL_BONECHILL_BLADE, SPELL_BONECHILL_FROST_BLAST, SPELL_TRANSFER_PAPERS, SPELL_HONOR_ROLL_RIBBON,
        SPELL_HONOR_ROLL, SPELL_DARKMASTERS_PORTAL_ROD, SPELL_PORTAL_BARRAGE, SPELL_DARKMASTERS_PORTAL_LOOK,
    };

    void TestIds()
    {
        CHECK(kSpellsScholomanceItems.first == 205620u);
        CHECK(kSpellsScholomanceItems.last == 205659u);
        IdSlice constexpr deadminesItems{ 205400, 205409 };   // the Deadmines hard mode item effects
        IdSlice constexpr copyBlock{ 205410, 205599 };        // ids.yaml `item_spell_copy`: the per-tier copies
        std::uint32_t expected = 205620;
        for (std::uint32_t id : kAllSpells)
        {
            CHECK(id == expected++);                            // one block, in order, no gap
            CHECK(kSpellsScholomanceItems.Contains(id));
            CHECK(!deadminesItems.Contains(id));
            CHECK(!copyBlock.Contains(id));
        }
        CHECK(expected == 205643u);                             // 205643-205659 spare
    }

    void TestPortal()
    {
        CHECK(Near(PortalDistance(1.5f), 3.5f));
        CHECK(Near(PortalDistance(0.0f), kPortalGap));
        CHECK(Near(PortalDistance(-1.0f), kPortalGap));         // a bad reach never puts it in front of the target
        CHECK(NPC_DARKMASTERS_PORTAL == 300465u);               // ids.yaml `scholomance_items` creature 300465-300469
        CHECK(kPortalStayMs >= 3000u);                          // outlasts the 3 sec barrage
    }

    void TestPhylactery()
    {
        CHECK(PhylacteryTally(0, 500) == 500u);
        CHECK(PhylacteryTally(500, 1250) == 1750u);
        std::uint64_t constexpr top = std::numeric_limits<std::uint64_t>::max();
        CHECK(PhylacteryTally(top - 10, 100) == top);           // saturates, never wraps

        CHECK(PhylacteryHeal(10000, 30) == 3000);
        CHECK(PhylacteryHeal(1001, 30) == 300);                 // rounded down
        CHECK(PhylacteryHeal(0, 30) == 0);                      // nothing taken, nothing healed
        CHECK(PhylacteryHeal(10000, 0) == 0);
        CHECK(PhylacteryHeal(10000, -5) == 0);
        std::int32_t constexpr cap = std::numeric_limits<std::int32_t>::max();
        CHECK(PhylacteryHeal(top, 100) == cap);                 // fits a spell value
        CHECK(PhylacteryHeal(top, 30) == static_cast<std::int32_t>(static_cast<std::uint64_t>(cap) * 30 / 100));
        static_assert(PhylacteryHeal(2000, 30) == 600);
    }

    void TestBonechill()
    {
        int spellA = 0;
        int spellB = 0;
        CastStamp const none{};
        CastStamp const cast{ &spellA, 116, 3 };
        CHECK(!SameCast(none, cast));                           // the first cast rolls
        CHECK(SameCast(cast, cast));                            // its second target does not
        CHECK(!SameCast(cast, CastStamp{ &spellB, 116, 3 }));   // another cast object rolls
        CHECK(!SameCast(cast, CastStamp{ &spellA, 116, 4 }));   // the address reused by the next cast rolls
        CHECK(!SameCast(cast, CastStamp{ &spellA, 133, 3 }));   // another spell rolls
        CHECK(!SameCast(none, none));                           // no spell, no match
    }

    void TestTransferPapers()
    {
        SwapCheck const ok{ true, false, true, true, false, false, false, false };
        CHECK(CanSwap(ok));
        SwapCheck c = ok;
        c.targetIsPlayer = false;
        CHECK(!CanSwap(c));                                     // a pet or a creature
        c = ok;
        c.targetIsCaster = true;
        CHECK(!CanSwap(c));
        c = ok;
        c.targetAlive = false;
        CHECK(!CanSwap(c));
        c = ok;
        c.sameGroup = false;
        CHECK(!CanSwap(c));
        c = ok;
        c.casterInFlight = true;
        CHECK(!CanSwap(c));
        c = ok;
        c.targetInFlight = true;
        CHECK(!CanSwap(c));
        c = ok;
        c.casterOnVehicle = true;
        CHECK(!CanSwap(c));
        c = ok;
        c.targetOnVehicle = true;
        CHECK(!CanSwap(c));
    }

    // The rod's tiers each cast their own barrage: the 71 tier the declared one, every copied tier the copy in its
    // own group. Holds for whatever the generated header holds (the copies appear after a full generate run).
    void TestPortalRodTiers()
    {
        using ItemSpellCopies::Resolve;
        CHECK(Resolve(SPELL_DARKMASTERS_PORTAL_ROD, SPELL_PORTAL_BARRAGE) == SPELL_PORTAL_BARRAGE);
        CHECK(Resolve(SPELL_DARKMASTERS_PORTAL_ROD, SPELL_DARKMASTERS_PORTAL_LOOK) == SPELL_DARKMASTERS_PORTAL_LOOK);
        int rods = 0;
        for (ItemSpellCopies::Copy const& c : ItemSpellCopies::kCopies)
        {
            CHECK(c.base != SPELL_DARKMASTERS_PORTAL_LOOK);     // the look is cast by its own id on every tier
            if (c.base != SPELL_DARKMASTERS_PORTAL_ROD)
                continue;
            ++rods;
            std::uint32_t const barrage = Resolve(c.copy, SPELL_PORTAL_BARRAGE);
            CHECK(barrage != SPELL_PORTAL_BARRAGE);
            bool found = false;
            for (ItemSpellCopies::Copy const& b : ItemSpellCopies::kCopies)
                if (b.copy == barrage)
                    found = b.base == SPELL_PORTAL_BARRAGE && b.group == c.group;
            CHECK(found);
        }
        CHECK(rods == 0 || rods == 3);                          // none yet, or the 81 / 91 / 101 tiers
    }
}

int main()
{
    TestIds();
    TestPortal();
    TestPhylactery();
    TestBonechill();
    TestTransferPapers();
    TestPortalRodTiers();
    return Report("scholomance_items_test");
}
