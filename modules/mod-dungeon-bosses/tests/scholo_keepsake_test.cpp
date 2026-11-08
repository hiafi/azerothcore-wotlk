// Host tests for RasHardModeLogic.h (S12: Ras Frostwhisper's hard mode, the Torn Keepsake).
// STUB written by WP-KS: the slice and the arena; WP-S12 grows it with its mechanics' pure logic.
#include "RasHardModeLogic.h"
#include "check.h"

using namespace ScholomanceRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(ScholoRasHardMode::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(ScholoRasHardMode::kSpellSlice.last));
    CHECK(KeepsakeBindAllowed(kKeepsakeAllPages, true, DungeonKit::State::NotStarted));

    return Report("scholo_keepsake_test");
}
