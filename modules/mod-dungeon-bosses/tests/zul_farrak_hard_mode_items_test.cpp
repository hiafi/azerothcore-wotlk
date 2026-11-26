// Host tests for ZulFarrakHardModeItemsLogic.h (the Zul'Farrak gear stage): the ids sit in the `zul_farrak_items`
// reservation and clear the item spell copy ranges and the neighbors, the Scale's charge and discharge events, the
// Fang's action and its once-per-cast stamp, the Whistle's single target test, share and health order, and the crew's
// look table. The generated ItemSpellCopies.h lookup gives each tier's own copies and leaves the charge buffs and The
// Crew's Aid shared.
#include "../src/ZulFarrak/ZulFarrakHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace ZulFarrakHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsZulFarrakItems.first == 213800u);
        CHECK(kSpellsZulFarrakItems.last == 213839u);
        CHECK(kSpellsZulFarrakItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsZulFarrakItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = kSpellsDeclared.first;
        for (std::uint32_t id : { SPELL_SCALE_OF_THE_STORM_GOD, SPELL_STATIC_CHARGE, SPELL_STATIC_DISCHARGE,
                 SPELL_STORMCHARGED_FANG, SPELL_STORMCHARGED, SPELL_STORM_ARC, SPELL_SERGEANTS_WHISTLE,
                 SPELL_THE_CREWS_AID })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(!(id >= 205410u && id <= 205599u));       // the item spell copy block
            CHECK(!(id >= 219000u && id <= 219399u));       // ... and its second range
            CHECK(id > 213799u && id < 213840u);            // Ragefire Chasm's build before, the dungeon build after
        }
        CHECK(expected == kSpellsDeclared.last + 1);
    }

    // Holds before the write run (no copies yet: every lookup gives the base) and after it (81, 91 and 101 each carry
    // their own).
    void TestCopies()
    {
        CHECK(ItemSpellCopies::Resolve(SPELL_SCALE_OF_THE_STORM_GOD, SPELL_STATIC_DISCHARGE) == SPELL_STATIC_DISCHARGE);
        CHECK(ItemSpellCopies::Resolve(SPELL_STORMCHARGED_FANG, SPELL_STORM_ARC) == SPELL_STORM_ARC);
        CHECK(ItemSpellCopies::Resolve(SPELL_SERGEANTS_WHISTLE, SPELL_THE_CREWS_AID) == SPELL_THE_CREWS_AID);
        std::uint32_t scales = 0;
        std::uint32_t fangs = 0;
        std::uint32_t whistles = 0;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
        {
            CHECK(copy.base != SPELL_STATIC_CHARGE && copy.base != SPELL_STORMCHARGED);
            CHECK(copy.base != SPELL_THE_CREWS_AID);
            if (copy.base == SPELL_SCALE_OF_THE_STORM_GOD)
            {
                ++scales;
                std::uint32_t const discharge = ItemSpellCopies::Resolve(copy.copy, SPELL_STATIC_DISCHARGE);
                CHECK(discharge != SPELL_STATIC_DISCHARGE);
                CHECK(ItemSpellCopies::GroupOf(discharge) == copy.group);
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_STATIC_CHARGE) == SPELL_STATIC_CHARGE);
            }
            if (copy.base == SPELL_STORMCHARGED_FANG)
            {
                ++fangs;
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_STORM_ARC) != SPELL_STORM_ARC);
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_STORMCHARGED) == SPELL_STORMCHARGED);
            }
            if (copy.base == SPELL_SERGEANTS_WHISTLE)
            {
                ++whistles;
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_THE_CREWS_AID) == SPELL_THE_CREWS_AID);
            }
        }
        CHECK(scales == 0u || scales == 3u);
        CHECK(fangs == scales);
        CHECK(whistles == scales);
    }

    void TestScale()
    {
        // a hit taken: one charge for each kind, none for a periodic tick or the wearer's own event
        for (std::uint32_t flag : { 0x8u, 0x20u, 0x80u, 0x200u, 0x2000u, 0x20000u })
            CHECK(HitCharges(flag, 1, false));
        CHECK(!HitCharges(0x80000u, 500, false));           // a periodic tick taken
        CHECK(!HitCharges(0x10u, 500, false));              // a strike done
        CHECK(!HitCharges(0x4u, 500, false));
        CHECK(!HitCharges(0x8u, 0, false));                 // fully absorbed: no damage taken
        CHECK(!HitCharges(0x20000u, 500, true));            // the wearer's own (a self-damage spell)

        // the strike that discharges
        CHECK(AbilityDischarges(0x10u, false, false, 10, 10, 1000, 0));
        CHECK(!AbilityDischarges(0x10u, false, false, 9, 10, 1000, 0));
        CHECK(AbilityDischarges(0x10u, false, false, 12, 10, 1000, 0));
        CHECK(!AbilityDischarges(0x4u, false, false, 10, 10, 1000, 0));       // an auto attack
        CHECK(!AbilityDischarges(0x10000u, false, false, 10, 10, 1000, 0));   // a spell
        CHECK(!AbilityDischarges(0x20u, false, false, 10, 10, 1000, 0));      // a strike taken
        CHECK(!AbilityDischarges(0x30u, false, false, 10, 10, 1000, 0));
        CHECK(!AbilityDischarges(0x10u, true, false, 10, 10, 1000, 0));       // a triggered strike rolls nothing
        CHECK(AbilityDischarges(0x10u, true, true, 10, 10, 1000, 0));         // ... unless the data says it counts
        CHECK(!AbilityDischarges(0x10u, false, false, 10, 10, 6999, 7000));   // the cooldown
        CHECK(AbilityDischarges(0x10u, false, false, 10, 10, 7000, 7000));
        CHECK(!AbilityDischarges(0x10u, false, false, 0, 0, 1000, 0));        // no data, no discharge
        // the same event never does both
        for (std::uint32_t mask : { 0x8u, 0x10u, 0x20u, 0x30u, 0x20000u })
            CHECK(!(HitCharges(mask, 1, false) && AbilityDischarges(mask, false, false, 10, 10, 1, 0)));
    }

    void TestFang()
    {
        CHECK(DecideFang(0, 5, true, false) == FangAction::Charge);
        CHECK(DecideFang(4, 5, true, true) == FangAction::Charge);
        CHECK(DecideFang(4, 5, false, true) == FangAction::None);
        CHECK(DecideFang(5, 5, false, true) == FangAction::Arc);
        CHECK(DecideFang(5, 5, true, true) == FangAction::Arc);               // arcs first, does not charge too
        CHECK(DecideFang(5, 5, false, false) == FangAction::None);            // nobody to arc to: kept
        CHECK(DecideFang(5, 5, true, false) == FangAction::Charge);           // ... and renewed by a crit
        CHECK(DecideFang(0, 0, false, true) == FangAction::None);             // no data, no arc

        int a = 0;
        int b = 0;
        CastStamp const first{ &a, 10, 1, CastMoment(0, 1000) };
        CHECK(CastMoment(0, 1000) == 1000u);                // an immediate spell: the update's game time
        CHECK(CastMoment(950, 1000) == 950u);               // a traveling spell: its launch moment
        CHECK(!SameCast(CastStamp{}, first));
        CHECK(SameCast(first, first));                      // a later target of the same area spell
        CHECK(!SameCast(first, CastStamp{ &a, 10, 1, 1100 }));  // the address reused by a later cast
        CHECK(!SameCast(first, CastStamp{ &b, 10, 1, 1000 }));
        CHECK(!SameCast(first, CastStamp{ &a, 11, 1, 1000 }));
        CHECK(!SameCast(first, CastStamp{ &a, 10, 2, 1000 }));
        CHECK(!SameCast(CastStamp{}, CastStamp{}));         // no spell: never the same cast
    }

    HealShape Heal(bool area = false, bool onCaster = false, std::uint32_t chain = 0)
    {
        return HealShape{ true, area, onCaster, chain };
    }

    void TestWhistle()
    {
        HealShape const other{};
        CHECK(IsSingleTargetHeal({ Heal(), other, other }));                  // Flash Heal
        CHECK(IsSingleTargetHeal({ other, Heal(), other }));
        CHECK(IsSingleTargetHeal({ Heal(), Heal(), other }));                 // Regrowth: direct and over time
        CHECK(IsSingleTargetHeal({ Heal(false, true), other, other }));       // a heal on the caster
        CHECK(IsSingleTargetHeal({ Heal(false, false, 1), other, other }));
        CHECK(!IsSingleTargetHeal({ Heal(false, false, 3), other, other }));  // Chain Heal
        CHECK(!IsSingleTargetHeal({ Heal(true), other, other }));             // Prayer of Healing
        CHECK(!IsSingleTargetHeal({ Heal(), Heal(true), other }));
        CHECK(!IsSingleTargetHeal({ Heal(), Heal(false, true), other }));     // Binding Heal
        CHECK(!IsSingleTargetHeal({ other, other, other }));
        HealShape const areaOther{ false, true, false, 0 };
        CHECK(IsSingleTargetHeal({ Heal(), areaOther, other }));              // an area effect that does not heal

        // heals a script casts on several targets
        CHECK(IsScriptSpreadHeal(200160));
        CHECK(IsScriptSpreadHeal(56161));
        for (std::uint32_t id : { 0u, 200159u, 200161u, 47750u, 56160u, 596u, 2061u, 139u })
            CHECK(!IsScriptSpreadHeal(id));

        // the healed target's healing taken comes off, heal absorbs come back
        CHECK(HealBeforeTaken(5000, 0, kTakenProbe) == 5000u);                // no modifier
        CHECK(HealBeforeTaken(2500, 0, kTakenProbe / 2) == 5000u);            // healing taken halved
        CHECK(HealBeforeTaken(7000, 0, 1400000) == 5000u);                    // Guardian Spirit: 40% more
        CHECK(HealBeforeTaken(6000, 0, 1199999) == 5000u);                    // the probe's own rounding
        CHECK(HealBeforeTaken(6000, 0, 1200001) == 5000u);
        CHECK(HealBeforeTaken(3000, 2000, kTakenProbe) == 5000u);             // a heal absorb ate 2000
        CHECK(HealBeforeTaken(500, 2000, kTakenProbe / 2) == 5000u);          // both
        CHECK(HealBeforeTaken(5000, 1000, 0) == 6000u);                       // nothing to undo it with
        CHECK(HealBeforeTaken(0, 0, kTakenProbe) == 0u);
        CHECK(HealBeforeTaken(4294967295u, 4294967295u, 1) == 4294967295u);   // capped
        CHECK(HealBeforeTaken(4294967295u, 1, 0) == 4294967295u);

        CHECK(ShareOfHeal(5000, 40) == 2000);
        CHECK(ShareOfHeal(5001, 40) == 2000);
        CHECK(ShareOfHeal(2, 40) == 0);
        CHECK(ShareOfHeal(0, 40) == 0);
        CHECK(ShareOfHeal(5000, 0) == 0);
        CHECK(ShareOfHeal(5000, -5) == 0);
        CHECK(ShareOfHeal(4294967295u, 100) == 0x7FFFFFFF);

        CHECK(IsInjured(1, 100));
        CHECK(!IsInjured(100, 100));
        CHECK(!IsInjured(0, 100));
        CHECK(LowerHealthFraction(40, 100, 500, 1000));
        CHECK(!LowerHealthFraction(50, 100, 500, 1000));
        CHECK(!LowerHealthFraction(600, 1000, 50, 100));
        CHECK(LowerHealthFraction(4294967294u, 4294967295u, 1, 1));           // no overflow
    }

    void TestCrew()
    {
        CHECK(kCrew.size() == 5u);
        std::uint32_t seen = 0;
        for (CrewLook const& look : kCrew)
        {
            CHECK(kCreaturesZulFarrakItems.Contains(look.entry));
            seen |= 1u << (look.entry - kCreaturesZulFarrakItems.first);
            CHECK(look.mainHand != 0u);
            CHECK(look.angle > 1.5f && look.angle < 4.8f);                    // beside or behind the wearer
        }
        CHECK(seen == 0x1Fu);                                                 // each of the five once
        for (std::size_t i = 1; i < kCrew.size(); ++i)
            CHECK(kCrew[i].angle - kCrew[i - 1].angle > 0.6f);                // spread out
        CHECK(kCrewStayMs > 12000u);                                          // outlasts the Use
    }
}

int main()
{
    TestIds();
    TestCopies();
    TestScale();
    TestFang();
    TestWhistle();
    TestCrew();
    return Report("zul_farrak_hard_mode_items_test");
}
