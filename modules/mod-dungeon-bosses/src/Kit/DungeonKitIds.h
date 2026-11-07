/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): the kit-wide spell ids (pure, so host tests and the dungeons'
 * pure headers can name them).
 *
 * Declared in apps/dbc-tools source/npcs/deadmines/shared.py with the builders of lib/dsl/dungeon_kit.py. Their ids sit
 * in the Deadmines reservation because the Pilot minted them first; every dungeon uses these two and never declares a
 * copy. A boss whose bar should name its mechanic declares its own named cast bar (lib/dsl/dungeon_kit.py cast_bar())
 * in its own dungeon's slice.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_IDS_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_IDS_H

#include <cstdint>

namespace DungeonKit
{
    enum KitSpells : std::uint32_t
    {
        SPELL_KIT_CAST_BAR          = 205200,   // "Preparing": a 2 s no-effect cast bar, not interruptible
        SPELL_KIT_STANDING_IN_IT    = 205201,   // "Standing in It": -30% movement 2 s, the lingering zones' rider
    };
}

#endif
