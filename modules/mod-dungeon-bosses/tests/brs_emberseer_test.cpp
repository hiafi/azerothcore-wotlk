// Host tests for EmberseerLogic.h (B10: Pyroguard Emberseer).
// STUB written by WP-S0: the slice and the arena; WP-B10 grows it with its mechanics' pure logic.
#include "EmberseerLogic.h"
#include "check.h"

using namespace BlackrockSpireRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(BrsEmberseer::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(BrsEmberseer::kSpellSlice.last));
    // He spawns kEmberseerSpawn, inside his arena.
    CHECK(EmberseerArena().Contains(kEmberseerSpawn.XY(), kEmberseerSpawn.z));
    CHECK(ArenaFor(BOSS_EMBERSEER).Contains(kEmberseerSpawn.XY(), kEmberseerSpawn.z));

    return Report("brs_emberseer_test");
}
