// Host tests for GnomereganHardModeItemsLogic.h (the Gnomeregan gear stage): the ids sit in the `gnomeregan_items`
// reservation and clear the item spell copy ranges and the neighbors, the Launcher's one roll per cast and the bomb's
// steps, the Punch Card's punch rule, memory, lock and clearing. The generated ItemSpellCopies.h lookup gives each
// tier's own copies (Meltdown's pulse, the mark and its blast, Clearance) and leaves Punched shared.
#include "../src/Gnomeregan/GnomereganHardModeItemsLogic.h"
#include "ItemSpellCopies.h"
#include "check.h"
#include <cstdint>
#include <initializer_list>

using namespace GnomereganHardModeItems;

namespace
{
    void TestIds()
    {
        CHECK(kSpellsGnomereganItems.first == 214240u);
        CHECK(kSpellsGnomereganItems.last == 214279u);
        CHECK(kSpellsGnomereganItems.Contains(kSpellsDeclared.first));
        CHECK(kSpellsGnomereganItems.Contains(kSpellsDeclared.last));
        std::uint32_t expected = kSpellsDeclared.first;
        for (std::uint32_t id : { SPELL_REACTOR_CORE_MELTDOWN, SPELL_REACTOR_CORE_PULSE, SPELL_BOMB_LAUNCHER,
                 SPELL_BOMB_LAUNCHER_MARK, SPELL_BOMB_LAUNCHER_BLAST, SPELL_PUNCH_CARD, SPELL_PUNCH_CARD_PUNCHED,
                 SPELL_PUNCH_CARD_CLEARANCE })
        {
            CHECK(id == expected);                          // contiguous, in declaration order
            ++expected;
            CHECK(kSpellsDeclared.Contains(id));
            CHECK(IsItemSpell(id));
            CHECK(!(id >= 205410u && id <= 205599u));       // the item spell copy block
            CHECK(!(id >= 219000u && id <= 219399u));       // ... and its second range
            CHECK(id > 214239u && id < 214280u);            // the Zul'Farrak build before, the Gnomeregan build after
        }
        CHECK(expected == kSpellsDeclared.last + 1);
        CHECK(kCreaturesGnomereganItems.first == 301100u);
        CHECK(kCreaturesGnomereganItems.last == 301104u);
        CHECK(kCreaturesGnomereganItems.Contains(NPC_LAUNCHER_WALKING_BOMB));
        CHECK(NPC_LAUNCHER_WALKING_BOMB > 301099u);         // after the Zul'Farrak build's creatures
        for (std::uint32_t id : { 0u, 214239u, 214248u, 214279u, 213800u, 205410u })
            CHECK(!IsItemSpell(id));                        // spare, the neighbors, another item's copy
    }

    // Holds before the write run (no copies yet: every lookup gives the base) and after it (81, 91 and 101 each carry
    // their own).
    void TestCopies()
    {
        CHECK(ItemSpellCopies::Resolve(SPELL_REACTOR_CORE_MELTDOWN, SPELL_REACTOR_CORE_PULSE)
            == SPELL_REACTOR_CORE_PULSE);
        CHECK(ItemSpellCopies::Resolve(SPELL_BOMB_LAUNCHER, SPELL_BOMB_LAUNCHER_MARK) == SPELL_BOMB_LAUNCHER_MARK);
        CHECK(ItemSpellCopies::Resolve(SPELL_BOMB_LAUNCHER_MARK, SPELL_BOMB_LAUNCHER_BLAST)
            == SPELL_BOMB_LAUNCHER_BLAST);
        CHECK(ItemSpellCopies::Resolve(SPELL_PUNCH_CARD, SPELL_PUNCH_CARD_CLEARANCE) == SPELL_PUNCH_CARD_CLEARANCE);
        CHECK(ItemSpellCopies::Resolve(SPELL_PUNCH_CARD, SPELL_PUNCH_CARD_PUNCHED) == SPELL_PUNCH_CARD_PUNCHED);
        std::uint32_t cores = 0;
        std::uint32_t launchers = 0;
        std::uint32_t marks = 0;
        std::uint32_t cards = 0;
        for (ItemSpellCopies::Copy const& copy : ItemSpellCopies::kCopies)
        {
            CHECK(copy.base != SPELL_PUNCH_CARD_PUNCHED);
            if (kSpellsDeclared.Contains(copy.base))
                CHECK(IsItemSpell(copy.copy));
            if (copy.base == SPELL_REACTOR_CORE_MELTDOWN)
            {
                ++cores;
                std::uint32_t const pulse = ItemSpellCopies::Resolve(copy.copy, SPELL_REACTOR_CORE_PULSE);
                CHECK(pulse != SPELL_REACTOR_CORE_PULSE);
                CHECK(ItemSpellCopies::GroupOf(pulse) == copy.group);
            }
            if (copy.base == SPELL_BOMB_LAUNCHER)
            {
                ++launchers;
                std::uint32_t const mark = ItemSpellCopies::Resolve(copy.copy, SPELL_BOMB_LAUNCHER_MARK);
                CHECK(mark != SPELL_BOMB_LAUNCHER_MARK);
                CHECK(ItemSpellCopies::GroupOf(mark) == copy.group);
            }
            if (copy.base == SPELL_BOMB_LAUNCHER_MARK)
            {
                ++marks;
                // the tier's mark blows the tier's blast
                std::uint32_t const blast = ItemSpellCopies::Resolve(copy.copy, SPELL_BOMB_LAUNCHER_BLAST);
                CHECK(blast != SPELL_BOMB_LAUNCHER_BLAST);
                CHECK(ItemSpellCopies::GroupOf(blast) == copy.group);
            }
            if (copy.base == SPELL_PUNCH_CARD)
            {
                ++cards;
                std::uint32_t const clearance = ItemSpellCopies::Resolve(copy.copy, SPELL_PUNCH_CARD_CLEARANCE);
                CHECK(clearance != SPELL_PUNCH_CARD_CLEARANCE);
                CHECK(ItemSpellCopies::GroupOf(clearance) == copy.group);
                CHECK(ItemSpellCopies::Resolve(copy.copy, SPELL_PUNCH_CARD_PUNCHED) == SPELL_PUNCH_CARD_PUNCHED);
            }
        }
        CHECK(cores == 0u || cores == 3u);
        CHECK(launchers == cores);
        CHECK(marks == cores);
        CHECK(cards == cores);
    }

    void TestOneRollPerCast()
    {
        int a = 0;
        int b = 0;
        CastStamp const first{ &a, 49048, 1, CastMoment(0, 1000) };
        CHECK(CastMoment(0, 1000) == 1000u);                // an immediate spell: the update's game time
        CHECK(CastMoment(950, 1000) == 950u);               // a traveling shot: its launch moment
        CHECK(!SameCast(CastStamp{}, first));
        CHECK(SameCast(first, first));                      // Multi-Shot's second target
        CHECK(!SameCast(first, CastStamp{ &a, 49048, 1, 1100 }));  // the address reused by a later cast
        CHECK(!SameCast(first, CastStamp{ &b, 49048, 1, 1000 }));
        CHECK(!SameCast(first, CastStamp{ &a, 49045, 1, 1000 }));
        CHECK(!SameCast(first, CastStamp{ &a, 49048, 2, 1000 }));
        CHECK(!SameCast(CastStamp{}, CastStamp{}));         // an auto shot has no spell: always rolls
    }

    void TestBomb()
    {
        CHECK(kRangedHitFlags == 0x140u);
        CHECK(!(kRangedHitFlags & 0x4u));                   // never a melee auto attack
        CHECK(!(kRangedHitFlags & 0x10u));                  // never a melee ability

        CHECK(StepBomb(true, true, true, false) == BombStep::Walk);
        CHECK(StepBomb(true, true, true, true) == BombStep::Blast);
        CHECK(StepBomb(false, true, true, true) == BombStep::FallApart);    // the target died: no blast
        CHECK(StepBomb(false, true, true, false) == BombStep::FallApart);
        CHECK(StepBomb(true, false, true, true) == BombStep::FallApart);    // the wearer died or left: no blast
        CHECK(StepBomb(true, true, false, false) == BombStep::FallApart);   // the bomb is gone
        CHECK(StepBomb(true, true, false, true) == BombStep::FallApart);

        CHECK(kBombLaunchDistance > 0.0f && kBombLaunchDistance < 5.0f);
        // the bomb outlives its 8 sec mark only by the tail, and the Launcher's 10 sec cooldown outlasts both
        CHECK(kBombTailMs > 0u && 8000u + kBombTailMs < 10000u);
    }

    void TestPunchRule()
    {
        CHECK(kOwnCastFlags == 0x15510u);
        CHECK(!(kOwnCastFlags & 0x4u));                     // no melee auto attack
        CHECK(!(kOwnCastFlags & 0x40u));                    // no ranged auto attack
        CHECK(CountsAsPunch(false, false, false, false));
        CHECK(!CountsAsPunch(true, false, false, false));   // triggered
        CHECK(!CountsAsPunch(false, true, false, false));   // an item's Use
        CHECK(!CountsAsPunch(false, false, true, false));   // Auto Shot, Shoot, Throw
        CHECK(!CountsAsPunch(false, false, false, true));   // passive
    }

    void TestPunchCard()
    {
        PunchCard card;
        CHECK(card.count == 0u);
        CHECK(Punch(card, 133, 5, 1000, 0) == PunchResult::Punched);
        CHECK(card.count == 1u);
        CHECK(IsPunched(card, 133));
        CHECK(Punch(card, 133, 5, 1100, 0) == PunchResult::None);           // the same spell punches once
        CHECK(card.count == 1u);
        CHECK(Punch(card, 116, 5, 1200, 0) == PunchResult::Punched);
        CHECK(Punch(card, 2136, 5, 1300, 0) == PunchResult::Punched);
        CHECK(Punch(card, 2948, 5, 1400, 0) == PunchResult::Punched);
        CHECK(card.count == 4u);
        CHECK(Punch(card, 116, 5, 1500, 0) == PunchResult::None);
        CHECK(Punch(card, 120, 5, 1600, 0) == PunchResult::Clearance);      // the fifth different spell
        CHECK(card.count == 0u);                                            // ... clears the card
        CHECK(!IsPunched(card, 133));
        CHECK(!IsPunched(card, 120));

        // the lock after Clearance: nothing punches until it ends, then the same spells punch again
        CHECK(Punch(card, 133, 5, 31599, 31600) == PunchResult::None);
        CHECK(card.count == 0u);
        CHECK(Punch(card, 133, 5, 31600, 31600) == PunchResult::Punched);

        // no data, no spell
        PunchCard blank;
        CHECK(Punch(blank, 133, 0, 1000, 0) == PunchResult::None);
        CHECK(Punch(blank, 0, 5, 1000, 0) == PunchResult::None);
        CHECK(blank.count == 0u);

        // a single punch card (data 1) clears at once; a card asking for more than it holds clears when full
        CHECK(Punch(blank, 133, 1, 1000, 0) == PunchResult::Clearance);
        PunchCard big;
        for (std::uint32_t i = 1; i < kMaxPunches; ++i)
            CHECK(Punch(big, i, 50, 1000, 0) == PunchResult::Punched);
        CHECK(Punch(big, kMaxPunches, 50, 1000, 0) == PunchResult::Clearance);
        CHECK(big.count == 0u);

        // the stacks are the card's face: fewer stacks than punches clears the memory, as many or more keeps it
        PunchCard face;
        Punch(face, 133, 5, 1000, 0);
        Punch(face, 116, 5, 1000, 0);
        SyncCard(face, 2);
        CHECK(face.count == 2u);
        SyncCard(face, 3);
        CHECK(face.count == 2u);
        SyncCard(face, 0);                                                  // died, or canceled the stacks
        CHECK(face.count == 0u);
        CHECK(!IsPunched(face, 133));
        CHECK(Punch(face, 133, 5, 1000, 0) == PunchResult::Punched);

        ClearCard(face);
        CHECK(face.count == 0u);
        for (std::uint32_t spell : face.spells)
            CHECK(spell == 0u);
    }
}

int main()
{
    TestIds();
    TestCopies();
    TestOneRollPerCast();
    TestBomb();
    TestPunchRule();
    TestPunchCard();
    return Report("gnomeregan_hard_mode_items_test");
}
