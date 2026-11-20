// Host tests for ZealotSetLogic.h (dungeon sets, the Zealot's set bonuses): the ids sit in the `zealot_set`
// reservation, the four Fervor lines then ten per set with the 3 piece at +0, clear of the Haunted and Molten slices;
// the trigger kind of each 3 piece (ruling 59); Zealot's Fervor's slope (nothing at full health, the full value at
// 40% or below, straight between) and how it scales an amount; the 35% crossing and the heal line; Blood Offering's
// price; the script numbers the tooltips print; the hound angles; which periodic ticks are heals.
#include "../src/DungeonSets/HauntedSetLogic.h"
#include "../src/DungeonSets/MoltenSetLogic.h"
#include "../src/DungeonSets/ZealotSetLogic.h"
#include "check.h"
#include <cstdint>
#include <set>

using namespace ZealotSet;

namespace
{
    std::uint32_t constexpr kAllSpells[] = {
        SPELL_FERVOR_DAMAGE, SPELL_FERVOR_HEALING, SPELL_FERVOR_TANK, SPELL_FERVOR_HYBRID,
        SPELL_UNBROKEN_ZEAL, SPELL_UNBROKEN_ZEAL_BUFF, SPELL_UNBROKEN_ZEAL_HEAL,
        SPELL_HOLD_THE_LINE, SPELL_HOLD_THE_LINE_BUFF,
        SPELL_KINDLED_VIGIL, SPELL_KINDLED_VIGIL_AURA, SPELL_KINDLED_VIGIL_BURN,
        SPELL_KENNEL_CALL, SPELL_KENNEL_CALL_BUFF, SPELL_KENNEL_CALL_BITE, SPELL_KENNEL_CALL_BITE_RANGED,
        SPELL_LAST_PAGE, SPELL_LAST_PAGE_BUFF,
        SPELL_EXTRACT_CONFESSION, SPELL_EXTRACT_CONFESSION_DEBUFF, SPELL_EXTRACT_CONFESSION_HEAL,
        SPELL_BONE_CAGE, SPELL_BONE_CAGE_BUFF, SPELL_BONE_CAGE_SPIKE,
        SPELL_HALLOWED_THORNS, SPELL_HALLOWED_THORNS_BUFF, SPELL_HALLOWED_THORNS_STRIKE,
        SPELL_ARCANISTS_WARD, SPELL_ARCANISTS_WARD_ABSORB, SPELL_ARCANISTS_WARD_DETONATION,
        SPELL_BLOOD_OFFERING, SPELL_BLOOD_OFFERING_HEAL,
    };

    void TestIds()
    {
        std::set<std::uint32_t> seen;
        for (std::uint32_t id : kAllSpells)
        {
            CHECK(kSpellsZealotSet.Contains(id));
            CHECK(!HauntedSet::kSpellsHauntedSet.Contains(id));
            CHECK(!MoltenSet::kSpellsMoltenSet.Contains(id));
            CHECK(seen.insert(id).second);
        }
        CHECK(seen.size() == sizeof(kAllSpells) / sizeof(kAllSpells[0]));
        // The Fervor lines first, then set k owns 212110 + 10k with its 3 piece at +0 (the hub table's order).
        CHECK(SPELL_FERVOR_DAMAGE == 212100 && SPELL_FERVOR_HYBRID == 212103);
        std::uint32_t k = 0;
        for (Martyr const& martyr : kMartyrs)
        {
            CHECK(martyr.bonus == 212110 + 10 * k);
            ++k;
        }
        CHECK(k == 10);
        CHECK(NPC_SCARLET_TRACKING_HOUND >= 300890 && NPC_SCARLET_TRACKING_HOUND <= 300899);
    }

    void TestTriggers()
    {
        // Ruling 59: the four "an ally you heal" sets; Cloth Spirit's Blood Offering on an ally only.
        CHECK(TriggerOf(SPELL_KINDLED_VIGIL) == Trigger::SelfOrAlly);
        CHECK(TriggerOf(SPELL_LAST_PAGE) == Trigger::SelfOrAlly);
        CHECK(TriggerOf(SPELL_HALLOWED_THORNS) == Trigger::SelfOrAlly);
        CHECK(TriggerOf(SPELL_BLOOD_OFFERING) == Trigger::Ally);
        for (std::uint32_t bonus : { SPELL_UNBROKEN_ZEAL, SPELL_HOLD_THE_LINE, SPELL_KENNEL_CALL,
                 SPELL_EXTRACT_CONFESSION, SPELL_BONE_CAGE, SPELL_ARCANISTS_WARD })
            CHECK(TriggerOf(bonus) == Trigger::Self);
        CHECK(TriggersOnSelf(Trigger::Self) && !TriggersOnAlly(Trigger::Self));
        CHECK(TriggersOnSelf(Trigger::SelfOrAlly) && TriggersOnAlly(Trigger::SelfOrAlly));
        CHECK(!TriggersOnSelf(Trigger::Ally) && TriggersOnAlly(Trigger::Ally));
        CHECK(TriggerOf(12345) == Trigger::Self);
    }

    void TestFervorSlope()
    {
        // Nothing at full health (or with no maximum), the full value at 40% or below, straight between.
        CHECK(FervorShareBp(1000, 1000) == 0);
        CHECK(FervorShareBp(1200, 1000) == 0);
        CHECK(FervorShareBp(500, 0) == 0);
        CHECK(FervorShareBp(400, 1000) == 10000);
        CHECK(FervorShareBp(399, 1000) == 10000);
        CHECK(FervorShareBp(1, 1000) == 10000);
        CHECK(FervorShareBp(0, 1000) == 10000);
        CHECK(FervorShareBp(700, 1000) == 5000);   // half way down the slope
        CHECK(FervorShareBp(850, 1000) == 2500);
        CHECK(FervorShareBp(940, 1000) == 1000);
        // Smooth: one point lower never takes the share down, and never jumps by more than a step.
        std::uint32_t last = 0;
        for (std::uint32_t health = 1000; health > 0; --health)
        {
            std::uint32_t const share = FervorShareBp(health, 1000);
            CHECK(share >= last);
            CHECK(share - last <= 17);
            last = share;
        }
        // Large pools never overflow.
        CHECK(FervorShareBp(400000000u, 1000000000u) == 10000);
        CHECK(FervorShareBp(700000000u, 1000000000u) == 5000);

        // The role values: up to 6% (damage, tank) and 8% (healing).
        CHECK(FervorBonusBp(6, 1000, 1000) == 0);
        CHECK(FervorBonusBp(6, 400, 1000) == 600);
        CHECK(FervorBonusBp(8, 300, 1000) == 800);
        CHECK(FervorBonusBp(6, 700, 1000) == 300);
        CHECK(FervorBonusBp(0, 100, 1000) == 0);
        CHECK(FervorBonusBp(-6, 100, 1000) == 0);
    }

    void TestApplyBp()
    {
        CHECK(ApplyBp(10000, 600, true) == 10600);
        CHECK(ApplyBp(10000, 600, false) == 9400);
        CHECK(ApplyBp(10000, 0, true) == 10000);
        CHECK(ApplyBp(0, 600, true) == 0);
        CHECK(ApplyBp(999, 1500, false) == 849);   // Extract Confession's 15% less, rounded down
        CHECK(ApplyBp(1000, 20000, false) == 0);   // never negative
        CHECK(ApplyBp(0x7FFFFFFFu, 10000, true) == 0x7FFFFFFFu);
        CHECK(PctOf(1000, 30) == 300);
        CHECK(PctOf(999, 25) == 249);
        CHECK(PctOf(0, 25) == 0);
    }

    void TestMartyrLine()
    {
        // The hit that crosses 35%: from 35% or more to below, alive.
        CHECK(CrossedMartyrLine(340, 20, 1000));     // 360 -> 340
        CHECK(CrossedMartyrLine(349, 1, 1000));      // 350 -> 349
        CHECK(!CrossedMartyrLine(350, 10, 1000));    // still at 35%
        CHECK(!CrossedMartyrLine(300, 40, 1000));    // 340 -> 300: was already below
        CHECK(!CrossedMartyrLine(0, 500, 1000));     // a killing blow
        CHECK(!CrossedMartyrLine(340, 0, 1000));
        CHECK(!CrossedMartyrLine(340, 20, 0));
        CHECK(CrossedMartyrLine(10, 990, 1000));     // a big hit from full

        // The heal line (ruling C4: any target the heal hits, the wearer included): at or below 35% as the heal lands,
        // before its amount (health now minus the effective heal).
        CHECK(AllyAtMartyrLine(550, 200, 1000));     // 350 before
        CHECK(!AllyAtMartyrLine(551, 200, 1000));    // 351 before
        CHECK(AllyAtMartyrLine(100, 0, 1000));       // a heal absorbed whole: 100 before
        CHECK(!AllyAtMartyrLine(1000, 1000, 1000));  // nothing before the heal (it was dead)
        CHECK(!AllyAtMartyrLine(0, 0, 1000));
        CHECK(!AllyAtMartyrLine(300, 0, 0));
    }

    void TestBloodOffering()
    {
        CHECK(BloodOfferingCost(1000) == 100);
        CHECK(BloodOfferingCost(15) == 1);
        CHECK(BloodOfferingCost(9) == 0);
        CHECK(BloodOfferingCost(1) == 0);
        CHECK(BloodOfferingCost(0) == 0);
    }

    void TestHounds()
    {
        // Review n3: each hound keeps its own side, at summon and when it falls back to following.
        CHECK(HoundAngle(0) > 1.57f && HoundAngle(0) < 1.58f);
        CHECK(HoundAngle(1) == -HoundAngle(0));
    }

    void TestPeriodicTicks()
    {
        // Review m1: Kindled Vigil's OBS_MOD_HEALTH tick is a heal tick like a PERIODIC_HEAL one.
        CHECK(IsPeriodicHealAura(8));       // SPELL_AURA_PERIODIC_HEAL
        CHECK(IsPeriodicHealAura(20));      // SPELL_AURA_OBS_MOD_HEALTH
        CHECK(!IsPeriodicHealAura(3));      // PERIODIC_DAMAGE
        CHECK(!IsPeriodicHealAura(53));     // PERIODIC_LEECH
        CHECK(!IsPeriodicHealAura(0));
        // The heal half of a marked tick: same target (first), same caster (second), same spell.
        PeriodicTick const tick{ 11, 22, 212131, true };
        CHECK(IsHealTickOf(tick, 11, 22, 212131));
        CHECK(!IsHealTickOf(tick, 22, 11, 212131));         // a direct heal's order (healer first)
        CHECK(!IsHealTickOf(tick, 11, 22, 212132));
        CHECK(!IsHealTickOf(PeriodicTick{}, 0, 0, 0));      // nothing marked
        CHECK(IsHealTickOf(PeriodicTick{ 11, 11, 774, true }, 11, 11, 774));  // a self heal over time
    }

    void TestScriptNumbers()
    {
        // The tooltip literals of zealot_set_bonuses.py (lib/test_zealot_set.py reads them back from this header).
        CHECK(kFervorFullAtHealthPct == 40);
        CHECK(kMartyrHealthPct == 35);
        CHECK(kKennelCallHounds == 2);
        CHECK(kArcanistsWardHealthPct == 15);
        CHECK(kBloodOfferingCostPct == 10);
        CHECK(kKennelCallRange == 40.0f && kConfessionRange == 40.0f);
    }
}

int main()
{
    TestIds();
    TestTriggers();
    TestFervorSlope();
    TestApplyBp();
    TestMartyrLine();
    TestBloodOffering();
    TestHounds();
    TestPeriodicTicks();
    TestScriptNumbers();
    return Report("zealot_set_test");
}
