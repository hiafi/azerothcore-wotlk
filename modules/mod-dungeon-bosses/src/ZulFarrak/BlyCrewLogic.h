/*
 * mod-dungeon-bosses, Zul'Farrak CR: Sergeant Bly's crew, the pure, host-testable part (no engine headers).
 * STUB written by WP-S0; WP-CR owns this file: the crew's factions by mode, its spell ids (the ally kits, inside
 * kSpellsCrewAlly of ZulFarrakRework.h, 213845-213859), the prisoner state machine, the restore rules and the movement
 * points' use, tested by tests/zf_crew_test.cpp. The modes, the mask and the points are ZulFarrakRework.h's.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_BLY_CREW_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_BLY_CREW_LOGIC_H

#include "ZulFarrakRework.h"
#include <cstdint>

namespace ZfCrew
{
    using ZulFarrakRework::CrewMode;

    // Every ally-kit spell of CR sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsCrewAlly;

    // Section 3.12: 35 caged, 495 ally (FACTION_ESCORTEE_N_FRIEND_ACTIVE, the stock cage script's), 41 hostile (stock
    // FACTION_BLY_HOSTILE), 35 at the pool. Weegli's stock escape faction 188 is CR's to keep or drop.
    std::uint32_t constexpr kFactionCaged = 35;
    std::uint32_t constexpr kFactionAlly = 495;
    std::uint32_t constexpr kFactionHostile = 41;
    std::uint32_t constexpr kFactionPoolAlly = 35;

    // The stub's faction by mode (CR may refine it per member).
    constexpr std::uint32_t FactionFor(CrewMode mode)
    {
        switch (mode)
        {
            case CrewMode::Ally:
                return kFactionAlly;
            case CrewMode::Boss:
                return kFactionHostile;
            case CrewMode::PoolAlly:
                return kFactionPoolAlly;
            default:
                return kFactionCaged;
        }
    }

    // Whether the mode fights (REACT_AGGRESSIVE); every other mode is passive.
    constexpr bool FightsIn(CrewMode mode)
    {
        return mode == CrewMode::Ally || mode == CrewMode::Boss || mode == CrewMode::PoolAlly;
    }
}

#endif
