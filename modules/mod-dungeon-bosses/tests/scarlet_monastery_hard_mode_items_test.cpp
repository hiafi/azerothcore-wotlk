// Host tests for ScarletMonasteryHardModeItemsLogic.h (the Scarlet Monastery gear stage): the ids sit in the
// `scarlet_monastery_items` reservation and clear the item spell copy block and the neighbors, the Rallying Standard's
// lockout rule, the Verdict's target count, the Rosary's health check, the one-roll-per-cast stamp and the banner
// ownership rule. The generated ItemSpellCopies.h lookup returns the base id for a spell with no copy.
#include "../src/ScarletMonastery/ScarletMonasteryHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace ScarletMonasteryHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsScarletMonasteryItems.first == 212000u);
        CHECK(kSpellsScarletMonasteryItems.last == 212099u);
        CHECK(kSpellsScarletMonasteryItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsScarletMonasteryItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = 212000;
        for (std::uint32_t id : { SPELL_PUREBLOODS_RALLYING_STANDARD, SPELL_RALLIED, SPELL_RECENTLY_RALLIED,
                 SPELL_FAIRBELLS_CENSER, SPELL_PENITENT_FIRE, SPELL_VOSSS_BLESSED_SIGNET, SPELL_VOSSS_BLESSING,
                 SPELL_SHARD_OF_THE_PHYLACTERY, SPELL_HERETICS_WAND, SPELL_ICY_DEATH, SPELL_FISSURE_TOUCHED_GRIPS,
                 SPELL_SHADOW_FISSURE, SPELL_SCARLET_GARRISON_RIFLE, SPELL_GARRISON_VOLLEY, SPELL_GARRISON_BULWARK,
                 SPELL_PILLAR_OF_LIGHT, SPELL_STAFF_OF_THE_CONSECRATED_HALL, SPELL_CONSECRATED_PILLAR,
                 SPELL_FATHERS_VERDICT, SPELL_VERDICT, SPELL_TREADS_OF_DENIAL, SPELL_DENIAL, SPELL_INQUISITORS_ROSARY,
                 SPELL_INQUISITORS_RESOLVE })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(!(id >= 205410u && id <= 205599u));       // the item spell copy block
            CHECK(!(id >= 212100u && id <= 212299u));       // the Zealot's set
            CHECK(id < 212300u);                            // the dungeon build's block starts there
        }
        CHECK(expected == kSpellsDeclared.last + 1);

        CHECK(kCreaturesScarletMonasteryItems.Contains(NPC_RALLYING_STANDARD));
        CHECK(NPC_RALLYING_STANDARD == 300880u);
        CHECK(kCreaturesScarletMonasteryItems.last < 300890u);  // the Zealot's vendors start there
    }

    void TestCopies()
    {
        // A base spell (the 71 tier) resolves to the base; an unscaled effect (the Rosary's Resolve) has no copy.
        CHECK(ItemSpellCopies::Resolve(SPELL_FATHERS_VERDICT, SPELL_VERDICT) == SPELL_VERDICT);
        CHECK(ItemSpellCopies::Resolve(SPELL_PUREBLOODS_RALLYING_STANDARD, SPELL_RALLIED) == SPELL_RALLIED);
        CHECK(ItemSpellCopies::Resolve(SPELL_INQUISITORS_ROSARY, SPELL_INQUISITORS_RESOLVE)
            == SPELL_INQUISITORS_RESOLVE);

        // Review m5: the Standard is scaled (three tier copies, each with its own Rallied); Recently Rallied is one
        // spell for every tier, so any standard's lockout blocks every other. Treads of Denial: each tier its Denial.
        std::uint32_t standards = 0;
        std::uint32_t treads = 0;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
        {
            CHECK(copy.base != SPELL_RECENTLY_RALLIED);
            CHECK(copy.base != SPELL_INQUISITORS_ROSARY && copy.base != SPELL_INQUISITORS_RESOLVE);
            if (copy.base == SPELL_PUREBLOODS_RALLYING_STANDARD)
            {
                ++standards;
                std::uint32_t const rallied = ItemSpellCopies::Resolve(copy.copy, SPELL_RALLIED);
                CHECK(rallied != SPELL_RALLIED);
                CHECK(ItemSpellCopies::GroupOf(rallied) == copy.group);
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_RECENTLY_RALLIED) == SPELL_RECENTLY_RALLIED);
            }
            if (copy.base == SPELL_TREADS_OF_DENIAL)
            {
                ++treads;
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_DENIAL) != SPELL_DENIAL);
            }
        }
        CHECK(standards == 3u);
        CHECK(treads == 3u);
    }

    // Review m2: the Haunting Mark skips every Scarlet Monastery hard mode item spell, the declared ones and their
    // tier copies (Garrison Volley's above all), and nothing else.
    void TestIsItemSpell()
    {
        CHECK(IsItemSpell(SPELL_GARRISON_VOLLEY));
        CHECK(IsItemSpell(kSpellsScarletMonasteryItems.first));
        CHECK(IsItemSpell(kSpellsScarletMonasteryItems.last));
        CHECK(!IsItemSpell(kSpellsScarletMonasteryItems.last + 1));     // the Zealot's set
        CHECK(!IsItemSpell(kSpellsScarletMonasteryItems.first - 1));
        CHECK(!IsItemSpell(205761u));                                   // the Haunting Mark itself
        std::uint32_t volleys = 0;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
        {
            bool const ours = kSpellsScarletMonasteryItems.Contains(copy.base);
            CHECK(IsItemSpell(copy.copy) == ours);
            if (copy.base == SPELL_GARRISON_VOLLEY)
                ++volleys;
        }
        CHECK(volleys == 3u);                                           // 81, 91 and 101
    }

    void TestBanner()
    {
        CHECK(kStandardStayMs > 15000u);                    // outlasts the 15 sec Use
        CHECK(kStandardStayMs < 120000u);                   // gone long before the 2 min cooldown ends
        CHECK(kLookSearchRange >= 30.0f);
        CHECK(IsOwnLook(42, 42));
        CHECK(!IsOwnLook(42, 43));
        CHECK(!IsOwnLook(0, 0));                            // no summoner is nobody's look
    }

    void TestRally()
    {
        CHECK(CanRally(false, 0, 7));                       // no lockout: rallied (and locked out by this wearer)
        CHECK(CanRally(true, 7, 7));                        // this wearer's own lockout: still rallied by this banner
        CHECK(!CanRally(true, 8, 7));                       // another wearer's lockout: two standards never stack
        CHECK(!CanRally(true, 0, 7));                       // a lockout with no known caster blocks too
    }

    void TestVerdict()
    {
        CHECK(VerdictExtraTargets(2, 5) == 2u);             // "up to 2 other enemies"
        CHECK(VerdictExtraTargets(2, 1) == 1u);
        CHECK(VerdictExtraTargets(2, 0) == 0u);             // the target alone
        CHECK(VerdictExtraTargets(0, 5) == 0u);
        CHECK(VerdictExtraTargets(-3, 5) == 0u);
        CHECK(kVerdictArc > 3.14f && kVerdictArc < 3.15f);  // the front half
    }

    void TestRosary()
    {
        CHECK(BelowThresholdBeforeHeal(700, 300, 1000, 50));   // 40% before the heal
        CHECK(!BelowThresholdBeforeHeal(800, 300, 1000, 50));  // exactly 50% before: not below
        CHECK(!BelowThresholdBeforeHeal(900, 300, 1000, 50));  // 60% before
        CHECK(BelowThresholdBeforeHeal(499, 0, 1000, 50));     // a fully overhealed heal still reads the health
        CHECK(!BelowThresholdBeforeHeal(300, 300, 1000, 50));  // 0 before: never qualifies
        CHECK(!BelowThresholdBeforeHeal(300, 400, 1000, 50));  // inconsistent input never qualifies
        CHECK(!BelowThresholdBeforeHeal(100, 0, 0, 50));
        CHECK(!BelowThresholdBeforeHeal(100, 0, 1000, 0));
        CHECK(BelowThresholdBeforeHeal(4000000000u, 1u, 4294967295u, 100));  // no overflow near the top
    }

    void TestOneRollPerCast()
    {
        int a = 0;
        int b = 0;
        CastStamp const first{ &a, 2061, 1, CastMoment(0, 1000) };
        CHECK(CastMoment(0, 1000) == 1000u);                // an immediate spell: the update's game time
        CHECK(CastMoment(950, 1000) == 950u);               // a travelling spell: its launch moment
        CHECK(!SameCast(CastStamp{}, first));               // nothing rolled yet
        CHECK(SameCast(first, first));                      // a later target of the same cast
        CHECK(!SameCast(first, CastStamp{ &a, 2061, 1, 1100 }));  // the address reused by a later cast
        CHECK(!SameCast(first, CastStamp{ &b, 2061, 1, 1000 }));  // another cast in the same update
        CHECK(!SameCast(first, CastStamp{ &a, 2060, 1, 1000 }));
        CHECK(!SameCast(first, CastStamp{ &a, 2061, 2, 1000 }));
        CastStamp const autoAttack{};
        CHECK(!SameCast(autoAttack, autoAttack));           // an event without a spell always rolls
    }
}

int main()
{
    TestIds();
    TestCopies();
    TestIsItemSpell();
    TestBanner();
    TestRally();
    TestVerdict();
    TestRosary();
    TestOneRollPerCast();
    return Report("scarlet_monastery_hard_mode_items_test");
}
