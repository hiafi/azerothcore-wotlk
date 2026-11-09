// Host tests for MalekiLogic.h (S12: Maleki the Pallid).
// STUB written by WP-S0: the slice and the arena; WP-S12 grows it with its mechanics' pure logic.
#include "MalekiLogic.h"
#include "check.h"

using namespace StratholmeRework;

int main()
{
    // The WP's spells sit in its slice, inside the dungeon's reservation.
    CHECK(kSpellsReservation.Contains(StratMaleki::kSpellSlice.first));
    CHECK(kSpellsReservation.Contains(StratMaleki::kSpellSlice.last));
    // The boss spawns inside his arena.
    CHECK(MalekiArena().Contains(kMalekiSpawn.XY(), kMalekiSpawn.z));
    CHECK(ArenaFor(BOSS_MALEKI).Contains(kMalekiSpawn.XY(), kMalekiSpawn.z));

    return Report("strat_maleki_test");
}
