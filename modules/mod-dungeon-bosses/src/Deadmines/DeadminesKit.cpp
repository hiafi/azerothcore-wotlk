/*
 * mod-dungeon-bosses, Deadmines: the shared kit's engine glue (DeadminesKit.h). The generic helpers moved to the shared
 * dungeon kit (src/Kit/DungeonKit.cpp) with WP-K0; the deck frame stays.
 */

#include "DeadminesKit.h"

namespace DeadminesKit
{
    BossMechanics::RoomFrame DeckFrame()
    {
        return DungeonKit::ToRoomFrame({ DeadminesRework::kDeckOrigin, DeadminesRework::kDeckAngle,
            DeadminesRework::kDeckLength, DeadminesRework::kDeckWidth }, DeadminesRework::kDeckZ);
    }
}
