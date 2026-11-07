/*
 * mod-dungeon-bosses, the shared dungeon kit (WP-K0): instance save strings and saved rolls (pure; host-tested by
 * tests/dungeon_kit_test.cpp).
 *
 * The save string of a rework instance is "<header chars, space separated> <field> <field> ...", the shape
 * AzerothCore's stock instance scripts write (Deadmines "D E 3 3"). Two layers:
 *
 *   FormatSave / ReadSaveFields     raw: a header and a list of numbers (a layout of your own, e.g. Deadmines', whose
 *                                   first two fields are the stock instance_deadmines ones)
 *   FormatStates / ParseStates      the usual layout: N boss states (sanitized on load), then M extra fields; a short
 *                                   tail leaves the defaults, a foreign header goes to an optional legacy reader (a
 *                                   stock save of the same map)
 *
 * Saved rolls (RollOnce in DungeonKit.h): a once-per-instance chance (Miner Johnson's 40% spawn, the Deathsworn
 * Captain's 15%) stored as Roll::Unrolled / Present / Absent.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_STATE_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_STATE_H

#include <cstddef>
#include <cstdint>
#include <functional>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

namespace DungeonKit
{
    // EncounterState values (InstanceScript.h); DungeonKit.cpp static_asserts they match the engine.
    namespace State
    {
        std::uint32_t constexpr NotStarted = 0;
        std::uint32_t constexpr InProgress = 1;
        std::uint32_t constexpr Fail = 2;
        std::uint32_t constexpr Done = 3;
        std::uint32_t constexpr Special = 4;
        std::uint32_t constexpr ToBeDecided = 5;
    }

    // A stored state that cannot survive a reload goes back to NOT_STARTED (InstanceScript::ReadSaveDataBossStates).
    inline std::uint32_t SanitizeLoadedState(std::uint32_t s)
    {
        if (s == State::InProgress || s == State::Fail || s == State::Special || s >= State::ToBeDecided)
            return State::NotStarted;
        return s;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Raw layer
    // ----------------------------------------------------------------------------------------------------------------

    // "H E A D f0 f1 ...": every header character followed by a space, then the fields separated by spaces.
    inline std::string FormatSave(std::string_view header, std::vector<std::uint32_t> const& fields)
    {
        std::ostringstream out;
        for (std::size_t i = 0; i < header.size(); ++i)
            out << header[i] << ' ';
        for (std::size_t i = 0; i < fields.size(); ++i)
        {
            if (i)
                out << ' ';
            out << fields[i];
        }
        return out.str();
    }

    // Reads the header (one non-blank character per header character, as `stream >> char` does) and then up to
    // `maxFields` numbers into `out`, stopping at the first one that does not read. False on a missing or wrong header
    // or fewer than `minFields` numbers (the save is then ignored, like a stock script).
    inline bool ReadSaveFields(std::string const& in, std::string_view header, std::size_t minFields,
        std::size_t maxFields, std::vector<std::uint32_t>& out)
    {
        out.clear();
        std::istringstream stream(in);
        for (char const expected : header)
        {
            char c = 0;
            if (!(stream >> c) || c != expected)
                return false;
        }
        while (out.size() < maxFields)
        {
            std::uint32_t v = 0;
            if (!(stream >> v))
                break;
            out.push_back(v);
        }
        return out.size() >= minFields;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // States + extras layer
    // ----------------------------------------------------------------------------------------------------------------

    struct StateSave
    {
        std::vector<std::uint32_t> states;     // EncounterState per boss state id
        std::vector<std::uint32_t> extras;     // the instance's own data fields, in its order
    };

    // A reader for a save written by another script of the same map (the stock one): fills `out` (already sized and
    // zeroed) and returns true, or false to ignore the save.
    using LegacySaveReader = std::function<bool(std::string const& in, StateSave& out)>;

    // "<header> <state 0> .. <state N-1> <extra 0> .. <extra M-1>". A TO_BE_DECIDED state is written as NOT_STARTED.
    inline std::string FormatStates(std::string_view header, std::vector<std::uint32_t> const& states,
        std::vector<std::uint32_t> const& extras)
    {
        std::vector<std::uint32_t> fields;
        fields.reserve(states.size() + extras.size());
        for (std::uint32_t const s : states)
            fields.push_back(s == State::ToBeDecided ? State::NotStarted : s);
        fields.insert(fields.end(), extras.begin(), extras.end());
        return FormatSave(header, fields);
    }

    // Reads FormatStates' string into `out` (`stateCount` states, `extraCount` extras, all 0 by default). A short tail
    // (a save from an older build with fewer fields) leaves the rest at 0; states pass SanitizeLoadedState. A wrong
    // header goes to `legacy` when given (false without one). At least one field must read.
    inline bool ParseStates(std::string const& in, std::string_view header, std::size_t stateCount,
        std::size_t extraCount, StateSave& out, LegacySaveReader const& legacy = {})
    {
        out.states.assign(stateCount, State::NotStarted);
        out.extras.assign(extraCount, 0);
        std::vector<std::uint32_t> fields;
        if (!ReadSaveFields(in, header, 1, stateCount + extraCount, fields))
        {
            // Only a foreign header (not a short field list under our own) goes to the legacy reader.
            std::vector<std::uint32_t> none;
            if (legacy && !ReadSaveFields(in, header, 0, 0, none))
            {
                if (!legacy(in, out))
                    return false;
                for (std::uint32_t& s : out.states)
                    s = SanitizeLoadedState(s);
                return true;
            }
            return false;
        }
        for (std::size_t i = 0; i < fields.size(); ++i)
        {
            if (i < stateCount)
                out.states[i] = SanitizeLoadedState(fields[i]);
            else
                out.extras[i - stateCount] = fields[i];
        }
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Saved rolls
    // ----------------------------------------------------------------------------------------------------------------

    namespace Roll
    {
        std::uint32_t constexpr Unrolled = 0;
        std::uint32_t constexpr Present = 1;
        std::uint32_t constexpr Absent = 2;
    }

    // `roll` in [0, 100): Present below `presentChancePct`.
    inline std::uint32_t ResolveRoll(std::uint32_t roll, std::uint32_t presentChancePct)
    {
        return roll < presentChancePct ? Roll::Present : Roll::Absent;
    }

    // A loaded roll value: Unrolled unless it is one of the three.
    inline std::uint32_t SanitizeLoadedRoll(std::uint32_t v)
    {
        return v <= Roll::Absent ? v : Roll::Unrolled;
    }
}

#endif
