// Host tests for GrandLieLogic.h (S8: Balnazzar's hard mode, the Grand Lie).
// STUB written by WP-S0: the slice and the arena; WP-S8 grows it with its mechanics' pure logic.
#include "GrandLieLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratGrandLie::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratGrandLie::kSpellSlice.last));
    // The hard mode's kill slot is its own and fights in its boss's arena.
    CHECK(IsHardModeSlot(BOSS_GRAND_LIE));
    CHECK(!ArenaFor(BOSS_GRAND_LIE).Empty());

    return Report("strat_grand_lie_test");
}
