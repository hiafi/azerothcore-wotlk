// Host tests for DrakkisathHardModeLogic.h (B15: General Drakkisath's hard mode, the General's Army).
// STUB written by WP-S0: the slice and the arena; WP-B15 grows it with its mechanics' pure logic.
#include "DrakkisathHardModeLogic.h"
#include "check.h"

using namespace BlackrockSpireRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(BrsGeneralsArmy::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(BrsGeneralsArmy::kSpellSlice.last));
    // The hard mode's kill slot is its own and fights in its boss's arena.
    CHECK(IsHardModeSlot(BOSS_GENERALS_ARMY));
    CHECK(!ArenaFor(BOSS_GENERALS_ARMY).Empty());

    return Report("brs_drakkisath_hard_mode_test");
}
