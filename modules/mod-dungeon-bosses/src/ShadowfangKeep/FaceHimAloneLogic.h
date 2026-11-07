/*
 * mod-dungeon-bosses, Shadowfang Keep: Arugal's hard mode "Face Him Alone" (WP-S10), the pure, host-testable part.
 * Build spec: SK 1491-1511.
 *
 * STUB from WP-K. Spell ids only inside the slice below (the last five of Arugal's slice, handoff section 3.4: "AR
 * 206060-206089, AR hard mode included"); apps/dbc-tools source/npcs/shadowfang_keep/face_him_alone.py declares them.
 *
 * TODO(WP-S10): the spell enum and the pure logic its host test covers (tests/sfk_face_him_alone_test.cpp).
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_FACE_HIM_ALONE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_FACE_HIM_ALONE_LOGIC_H

#include "ShadowfangKeepRework.h"
#include <cstdint>

namespace FaceHimAlone
{
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsFaceHimAlone;
}

#endif
