// Host tests for RagefireChasmHardModeItemsLogic.h (the Ragefire Chasm gear stage): the ids sit in the
// `ragefire_chasm_items` reservation and clear the item spell copy ranges and the neighbors, the item spell test, the
// Fang's leap decision, landing watch and heal, the Heart's health check, Bloodward amount and replacement, and the
// one-roll-per-cast stamp. The generated ItemSpellCopies.h lookup gives each tier's own copies and leaves Feed and
// Bloodward shared.
#include "../src/RagefireChasm/RagefireChasmHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace RagefireChasmHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsRagefireChasmItems.first == 213500u);
        CHECK(kSpellsRagefireChasmItems.last == 213539u);
        CHECK(kSpellsRagefireChasmItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsRagefireChasmItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = kSpellsDeclared.first;
        for (std::uint32_t id : { SPELL_TARAGAMANS_FANG, SPELL_HUNGERING_BITE, SPELL_FEED, SPELL_HEART_OF_THE_STARVING,
                 SPELL_BLOODWARD, SPELL_FELSTORM_GREATBLADE, SPELL_FELSTORM, SPELL_FELSTORM_SPIN })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(!(id >= 205410u && id <= 205599u));       // the item spell copy block
            CHECK(!(id >= 219000u && id <= 219399u));       // ... and its second range
            CHECK(id < 213540u);                            // the dungeon build's block starts there
        }
        CHECK(expected == kSpellsDeclared.last + 1);
    }

    // Holds before the write run (no copies yet: every lookup gives the base) and after it (81, 91 and 101 each carry
    // their own).
    void TestCopies()
    {
        CHECK(ItemSpellCopies::Resolve(SPELL_TARAGAMANS_FANG, SPELL_HUNGERING_BITE) == SPELL_HUNGERING_BITE);
        CHECK(ItemSpellCopies::Resolve(SPELL_HUNGERING_BITE, SPELL_FEED) == SPELL_FEED);
        CHECK(ItemSpellCopies::Resolve(SPELL_HEART_OF_THE_STARVING, SPELL_BLOODWARD) == SPELL_BLOODWARD);
        std::uint32_t fangs = 0;
        std::uint32_t bites = 0;
        std::uint32_t hearts = 0;
        std::uint32_t blades = 0;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
        {
            CHECK(copy.base != SPELL_FEED && copy.base != SPELL_BLOODWARD);
            if (copy.base == SPELL_TARAGAMANS_FANG)
            {
                ++fangs;
                std::uint32_t const bite = ItemSpellCopies::Resolve(copy.copy, SPELL_HUNGERING_BITE);
                CHECK(bite != SPELL_HUNGERING_BITE);
                CHECK(ItemSpellCopies::GroupOf(bite) == copy.group);
                CHECK(ItemSpellCopies::Resolve(bite, SPELL_FEED) == SPELL_FEED);
            }
            if (copy.base == SPELL_HUNGERING_BITE)
                ++bites;
            if (copy.base == SPELL_HEART_OF_THE_STARVING)
            {
                ++hearts;
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_BLOODWARD) == SPELL_BLOODWARD);
            }
            if (copy.base == SPELL_FELSTORM_GREATBLADE)
            {
                ++blades;
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_FELSTORM) != SPELL_FELSTORM);
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_FELSTORM_SPIN) != SPELL_FELSTORM_SPIN);
            }
        }
        CHECK(fangs == 0u || fangs == 3u);
        CHECK(bites == fangs);
        CHECK(hearts == fangs);
        CHECK(blades == fangs);
    }

    void TestIsItemSpell()
    {
        CHECK(IsItemSpell(SPELL_HUNGERING_BITE));
        CHECK(IsItemSpell(SPELL_FELSTORM_SPIN));
        CHECK(IsItemSpell(kSpellsRagefireChasmItems.first));
        CHECK(IsItemSpell(kSpellsRagefireChasmItems.last));
        CHECK(!IsItemSpell(kSpellsRagefireChasmItems.last + 1));        // the dungeon build's block
        CHECK(!IsItemSpell(kSpellsRagefireChasmItems.first - 1));
        CHECK(!IsItemSpell(205761u));                                   // the Haunting Mark itself
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
            CHECK(IsItemSpell(copy.copy) == kSpellsRagefireChasmItems.Contains(copy.base));
    }

    // The engine's Unit::GetMeleeRange, for the leap decision's input.
    float MeleeRange(float wearerReach, float victimReach)
    {
        float const range = wearerReach + victimReach + 4.0f / 3.0f;
        return range > 5.0f ? range : 5.0f;
    }

    bool Leaps(float distance, float victimReach)
    {
        float const playerReach = 1.5f;
        return LeapMoves(distance < MeleeRange(playerReach, victimReach), distance, victimReach);
    }

    void TestLeap()
    {
        CHECK(!Leaps(10.0f, 18.0f));                        // inside Onyxia's reach: never dragged under her
        CHECK(!Leaps(12.0f, 20.0f));                        // ... nor to Ragnaros' center
        CHECK(!Leaps(6.0f, 8.0f));                          // Baron Geddon
        CHECK(!Leaps(2.5f, 3.0f));                          // Taragaman
        CHECK(!Leaps(0.0f, 1.5f));
        CHECK(!Leaps(4.9f, 1.5f));                          // melee range of a small target: nothing to leap
        CHECK(Leaps(5.1f, 1.5f));
        CHECK(Leaps(25.0f, 1.5f));
        CHECK(Leaps(25.0f, 18.0f));                         // from outside a big boss' melee range
        CHECK(!Leaps(19.0f, 18.0f));                        // in its melee range already
        CHECK(!LeapMoves(true, 30.0f, 3.0f));               // melee leeway counts as in range
        CHECK(!LeapMoves(false, 18.0f, 18.0f));
        // a leap never starts inside the victim's reach, where the engine would not shorten its path
        for (float reach = 0.0f; reach <= 25.0f; reach += 0.5f)
            for (float distance = 0.0f; distance <= 50.0f; distance += 0.25f)
                CHECK(!Leaps(distance, reach) || distance > reach);
        // without a leap the wearer is not charging when the hit comes and stands within the bite's reach: no wait
        CHECK(!WaitForLanding(false, 0));
        for (float reach = 0.0f; reach <= 25.0f; reach += 0.5f)
            for (float distance = 0.0f; distance <= 50.0f; distance += 0.25f)
                CHECK(Leaps(distance, reach) || distance < 1.5f + reach + kBiteReach);
    }

    void TestLanding()
    {
        CHECK(WaitForLanding(true, 0));                     // still charging when the hit arrives: wait
        CHECK(WaitForLanding(true, kLeapWaitMs - 1));
        CHECK(!WaitForLanding(true, kLeapWaitMs));          // the watch runs out
        CHECK(!WaitForLanding(false, 0));                   // landed (or never left): bite now, if it is in reach
        CHECK(kLeapPollMs > 0u);
        CHECK(kLeapWaitMs % kLeapPollMs == 0u);
        // the longest path CheckCast accepts (1.5 x 25 yd plus a huge combat reach) fits the watch at the speed the
        // spline really has (MoveSplineInit::Launch caps the charge's 42 yd/s at 28)
        CHECK(kLeapSplineSpeed == 28.0f);
        CHECK((1.5f * 25.0f + 30.0f) / kLeapSplineSpeed * 1000.0f < float(kLeapWaitMs));
        // at 25 yd the hit (distance / 42) comes before the landing, so the poll is needed
        CHECK(25.0f / 42.0f < 25.0f / kLeapSplineSpeed);
        CHECK(kBiteReach > 5.0f);                           // a target that walked on is still bitten
        CHECK(kBiteReach < 25.0f);                          // a leap that never left is not a bite
    }

    void TestBiteHeal()
    {
        CHECK(BiteHeal(1000, 5000) == 1000);
        CHECK(BiteHeal(5000, 5000) == 5000);
        CHECK(BiteHeal(6000, 5000) == 5000);                // overkill left out
        CHECK(BiteHeal(0, 5000) == 0);                      // fully absorbed, immune
        CHECK(BiteHeal(-5, 5000) == 0);
        CHECK(BiteHeal(1000, 0) == 0);
        CHECK(BiteHeal(1000, 4000000000u) == 1000);         // a boss's health above the int32 range
    }

    void TestHeart()
    {
        CHECK(BelowThresholdBeforeHeal(700, 500, 1000, 30));   // 20% before the heal
        CHECK(!BelowThresholdBeforeHeal(800, 500, 1000, 30));  // exactly 30% before: not below
        CHECK(!BelowThresholdBeforeHeal(900, 500, 1000, 30));  // 40% before
        CHECK(BelowThresholdBeforeHeal(1000, 701, 1000, 30));  // healed to full from 29.9%
        CHECK(BelowThresholdBeforeHeal(299, 0, 1000, 30));
        CHECK(!BelowThresholdBeforeHeal(300, 300, 1000, 30));  // 0 before: never qualifies
        CHECK(!BelowThresholdBeforeHeal(300, 400, 1000, 30));  // inconsistent input never qualifies
        CHECK(!BelowThresholdBeforeHeal(100, 0, 0, 30));
        CHECK(!BelowThresholdBeforeHeal(100, 0, 1000, 0));
        CHECK(BelowThresholdBeforeHeal(1200000000u, 1u, 4294967295u, 30));  // no overflow near the top

        CHECK(BloodwardAmount(5000, 40) == 2000);
        CHECK(BloodwardAmount(5001, 40) == 2000);           // rounds down
        CHECK(BloodwardAmount(0, 40) == 0);
        CHECK(BloodwardAmount(2, 40) == 0);                 // too small a heal leaves no ward
        CHECK(BloodwardAmount(5000, 0) == 0);
        CHECK(BloodwardAmount(5000, -10) == 0);
        CHECK(BloodwardAmount(4294967295u, 100) == 0x7fffffff);

        CHECK(BloodwardReplaces(2000, 0));                  // no Bloodward on the target
        CHECK(BloodwardReplaces(2000, 1999));
        CHECK(BloodwardReplaces(2000, 2000));               // an equal one renews the time
        CHECK(!BloodwardReplaces(2000, 2001));              // a larger remaining one stays, whoever cast it
        CHECK(!BloodwardReplaces(1, 0x7fffffff));
        CHECK(BloodwardReplaces(1000, 400));                // what is left counts, not what it started with
    }

    void TestOneRollPerCast()
    {
        int a = 0;
        int b = 0;
        CastStamp const first{ &a, 1680, 1, CastMoment(0, 1000) };
        CHECK(CastMoment(0, 1000) == 1000u);                // an immediate spell: the update's game time
        CHECK(CastMoment(950, 1000) == 950u);               // a traveling spell: its launch moment
        CHECK(!SameCast(CastStamp{}, first));               // nothing rolled yet
        CHECK(SameCast(first, first));                      // a later target of the same Whirlwind
        CHECK(!SameCast(first, CastStamp{ &a, 1680, 1, 1100 }));  // the address reused by a later cast
        CHECK(!SameCast(first, CastStamp{ &b, 1680, 1, 1000 }));  // another cast in the same update
        CHECK(!SameCast(first, CastStamp{ &a, 1464, 1, 1000 }));
        CHECK(!SameCast(first, CastStamp{ &a, 1680, 2, 1000 }));
        CastStamp const autoAttack{};
        CHECK(!SameCast(autoAttack, autoAttack));           // an event without a spell always rolls
    }
}

int main()
{
    TestIds();
    TestCopies();
    TestIsItemSpell();
    TestLeap();
    TestLanding();
    TestBiteHeal();
    TestHeart();
    TestOneRollPerCast();
    return Report("ragefire_chasm_hard_mode_items_test");
}
