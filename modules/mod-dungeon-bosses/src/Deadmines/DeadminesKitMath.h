/*
 * mod-dungeon-bosses, Deadmines: the shared kit's pure part (no engine headers; host-tested by tests/kit_test.cpp).
 *
 * Since WP-K0 the generic pieces live in the shared dungeon kit (src/Kit/DungeonKitMath.h, DungeonKitState.h): NH<T>,
 * RefFlatValue, Vec2 and the map-plane geometry, Box2, the State constants and SanitizeLoadedState. DeadminesKit names
 * them through a using-directive, so every `DeadminesKit::X` of the Pilot still compiles to the generic X.
 *
 * What stays here is Deadmines' own: Miner Johnson's spawn roll and the instance save string (Save / FormatSave /
 * ParseSave), backward compatible with the stock instance_deadmines "D E <rhahkzor> <cannon>" string.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_KIT_MATH_H
#define MOD_DUNGEON_BOSSES_DEADMINES_KIT_MATH_H

#include "DungeonKitIds.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace DeadminesKit
{
    using namespace DungeonKit;

    // Miner Johnson's spawn roll (handoff section 7 #15): rolled once per instance and saved.
    namespace JohnsonRoll
    {
        std::uint32_t constexpr Unrolled = DungeonKit::Roll::Unrolled;
        std::uint32_t constexpr Present = DungeonKit::Roll::Present;
        std::uint32_t constexpr Absent = DungeonKit::Roll::Absent;
        std::uint32_t constexpr PresentChancePct = 40;  // stock SmartAI 3586: 60% despawn on AI init
    }

    // `roll` in [0, 100): Present below PresentChancePct.
    inline std::uint32_t ResolveJohnsonRoll(std::uint32_t roll)
    {
        return DungeonKit::ResolveRoll(roll, JohnsonRoll::PresentChancePct);
    }

    std::size_t constexpr kSaveBossCount = 9;   // the instance's SetBossNumber, in DeadminesRework.h order

    struct Save
    {
        std::array<std::uint32_t, kSaveBossCount> bosses{};     // EncounterState per boss state id
        std::uint32_t cannon = State::NotStarted;               // the stock TYPE_CANNON field (Iron Clad Door event)
        std::uint32_t hardMode = 0;                             // DATA_HARD_MODE (1 while lit)
        std::uint32_t johnsonRoll = JohnsonRoll::Unrolled;
    };

    // "D E <boss 0> <cannon> <boss 1> .. <boss 8> <hardMode> <johnsonRoll>". The first two numbers are the stock
    // instance_deadmines fields (TYPE_RHAHK_ZOR, TYPE_CANNON), and boss 0 is Rhahk'Zor, so a save written by the stock
    // script reads as Rhahk'Zor and the cannon with everything else unset.
    char constexpr kSaveHeader[] = "DE";
    // Field layout: boss 0, the cannon, bosses 1 .. 8, hard mode, Johnson's roll.
    std::size_t constexpr kSaveFields = kSaveBossCount + 3;

    inline std::string FormatSave(Save const& s)
    {
        std::vector<std::uint32_t> fields;
        fields.reserve(kSaveFields);
        fields.push_back(s.bosses[0]);
        fields.push_back(s.cannon);
        for (std::size_t i = 1; i < kSaveBossCount; ++i)
            fields.push_back(s.bosses[i]);
        fields.push_back(s.hardMode);
        fields.push_back(s.johnsonRoll);
        return DungeonKit::FormatSave(kSaveHeader, fields);
    }

    // False on a missing or wrong header or a missing stock field (the save is then ignored, like the stock script).
    // A short tail (a stock save) leaves the rest at its defaults. Loaded states pass SanitizeLoadedState; the stock
    // script also reset an IN_PROGRESS cannon, so the cannon does too. A lit hard mode never survives a reload.
    inline bool ParseSave(std::string const& in, Save& out)
    {
        out = Save{};
        std::vector<std::uint32_t> fields;
        if (!DungeonKit::ReadSaveFields(in, kSaveHeader, 2, kSaveFields, fields))
            return false;
        out.bosses[0] = SanitizeLoadedState(fields[0]);
        out.cannon = SanitizeLoadedState(fields[1]);
        for (std::size_t i = 1; i < kSaveBossCount && i + 1 < fields.size(); ++i)
            out.bosses[i] = SanitizeLoadedState(fields[i + 1]);
        // fields[kSaveBossCount + 1] is the hard mode flag: never restored (out.hardMode stays 0).
        if (fields.size() > kSaveBossCount + 2)
            out.johnsonRoll = DungeonKit::SanitizeLoadedRoll(fields[kSaveBossCount + 2]);
        return true;
    }
}

#endif
