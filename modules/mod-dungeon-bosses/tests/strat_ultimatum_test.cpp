// Host tests for BaronHardModeLogic.h (S15: Baron Rivendare's hard mode, the Ultimatum).
// STUB written by WP-S0: the slice and the arena; WP-S15 grows it with its mechanics' pure logic.
#include "BaronHardModeLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratUltimatum::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratUltimatum::kSpellSlice.last));
    // The hard mode's kill slot is its own and fights in its boss's arena.
    CHECK(IsHardModeSlot(BOSS_ULTIMATUM));
    CHECK(!ArenaFor(BOSS_ULTIMATUM).Empty());

    return Report("strat_ultimatum_test");
}
