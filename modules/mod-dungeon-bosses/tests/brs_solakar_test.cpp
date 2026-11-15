// Host tests for SolakarLogic.h (B11: Solakar Flamewreath).
// STUB written by WP-S0: the slice and the arena; WP-B11 grows it with its mechanics' pure logic.
#include "SolakarLogic.h"
#include "check.h"

using namespace BlackrockSpireRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(BrsSolakar::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(BrsSolakar::kSpellSlice.last));
    // He is summoned at kSolakarPosBoss, inside his arena.
    CHECK(SolakarArena().Contains(kSolakarPosBoss.XY(), kSolakarPosBoss.z));
    CHECK(ArenaFor(BOSS_SOLAKAR).Contains(kSolakarPosBoss.XY(), kSolakarPosBoss.z));

    return Report("brs_solakar_test");
}
