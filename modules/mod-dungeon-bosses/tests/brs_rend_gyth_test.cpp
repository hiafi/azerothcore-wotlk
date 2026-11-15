// Host tests for RendGythLogic.h (B12: Warchief Rend Blackhand).
// STUB written by WP-S0: the slice and the arena; WP-B12 grows it with its mechanics' pure logic.
#include "RendGythLogic.h"
#include "check.h"

using namespace BlackrockSpireRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(BrsRendGyth::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(BrsRendGyth::kSpellSlice.last));
    // He starts at kStadiumTrigger, inside his arena.
    CHECK(RendGythArena().Contains(kStadiumTrigger.XY(), kStadiumTrigger.z));
    CHECK(ArenaFor(BOSS_REND).Contains(kStadiumTrigger.XY(), kStadiumTrigger.z));
    // Gyth hovers inside the portcullis.
    CHECK(RendGythArena().Contains(kGythHoverGround.XY(), kGythHoverGround.z));
    CHECK(ArenaFor(BOSS_GYTH).Contains(kGythHoverGround.XY(), kGythHoverGround.z));

    return Report("brs_rend_gyth_test");
}
