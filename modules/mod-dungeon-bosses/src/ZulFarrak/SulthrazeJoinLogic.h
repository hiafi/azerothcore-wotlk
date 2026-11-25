/*
 * mod-dungeon-bosses, Zul'Farrak: the tier rule of the Sul'thraze join (user ruling 2026-11-25, option A). The Use of
 * Jang'thraze (spell 213808, apps/dbc-tools/source/items/zul_farrak_effects.py) joins Jang'thraze and Sang'thraze of
 * the same tier into the Sul'thraze of that tier; mixed tiers are refused. The engine glue is sulthraze_join.cpp.
 *
 * Pure: no engine headers, so the host test (tests/zul_farrak_sulthraze_join_test.cpp) includes it. The tiers are data
 * (`item_budget_variant`), so no minted item id is written here: a base entry is step 0, a variant its `tier` column.
 */

#ifndef MOD_DUNGEON_BOSSES_SULTHRAZE_JOIN_LOGIC_H
#define MOD_DUNGEON_BOSSES_SULTHRAZE_JOIN_LOGIC_H

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <map>
#include <optional>
#include <utility>
#include <vector>

namespace ZulFarrakSulthraze
{
    std::uint32_t constexpr SPELL_CALL_OF_SULTHRAZE = 213808;

    enum class Blade : std::uint8_t
    {
        Jangthraze,     // carries the Use, used up by the engine (spellcharges -1)
        Sangthraze,     // the other half, used up by the script
        Sulthraze,      // what they join into
    };

    // The stock entries, step 0 (Normal) of each ladder (source/items/zul_farrak.py `base=`).
    struct BaseBlade
    {
        std::uint32_t entry;
        Blade blade;
    };
    std::array<BaseBlade, 3> constexpr kBaseBlades{ {
        { 11086, Blade::Jangthraze },
        { 9379, Blade::Sangthraze },
        { 9372, Blade::Sulthraze },
    } };

    std::uint32_t constexpr kBaseStep = 0;

    constexpr std::optional<Blade> BaseBladeOf(std::uint32_t baseEntry)
    {
        for (BaseBlade const& base : kBaseBlades)
            if (base.entry == baseEntry)
                return base.blade;
        return std::nullopt;
    }

    struct BladeTier
    {
        Blade blade;
        std::uint32_t step;

        bool operator==(BladeTier const&) const = default;
    };

    // Which item is which blade of which tier. Starts with the three stock entries; AddVariant takes the rows of
    // `item_budget_variant`.
    class JoinTable
    {
    public:
        JoinTable()
        {
            for (BaseBlade const& base : kBaseBlades)
                Add(base.entry, { base.blade, kBaseStep });
        }

        // False: not one of the three bases, or the entry or that blade's step is already known (the first one stays).
        bool AddVariant(std::uint32_t entry, std::uint32_t baseEntry, std::uint32_t step)
        {
            std::optional<Blade> const blade = BaseBladeOf(baseEntry);
            return blade && Add(entry, { *blade, step });
        }

        std::optional<BladeTier> Find(std::uint32_t entry) const
        {
            auto const itr = _tiers.find(entry);
            return itr == _tiers.end() ? std::nullopt : std::optional<BladeTier>(itr->second);
        }

        // 0: no such item.
        std::uint32_t EntryOf(Blade blade, std::uint32_t step) const
        {
            auto const itr = _entries.find({ blade, step });
            return itr == _entries.end() ? 0 : itr->second;
        }

        // The steps at which all three blades exist.
        std::size_t CompleteSteps() const
        {
            return static_cast<std::size_t>(std::count_if(_tiers.begin(), _tiers.end(), [this](auto const& known)
            {
                return known.second.blade == Blade::Jangthraze && EntryOf(Blade::Sangthraze, known.second.step) != 0
                    && EntryOf(Blade::Sulthraze, known.second.step) != 0;
            }));
        }

        std::size_t Size() const { return _tiers.size(); }

    private:
        bool Add(std::uint32_t entry, BladeTier tier)
        {
            if (entry == 0 || _tiers.contains(entry) || _entries.contains({ tier.blade, tier.step }))
                return false;
            _tiers.emplace(entry, tier);
            _entries.emplace(std::make_pair(tier.blade, tier.step), entry);
            return true;
        }

        std::map<std::uint32_t, BladeTier> _tiers;
        std::map<std::pair<Blade, std::uint32_t>, std::uint32_t> _entries;
    };

    enum class JoinVerdict : std::uint8_t
    {
        Join,
        NotJangthraze,      // the cast item is none of the known Jang'thraze tiers (or there is none)
        NoSangthraze,       // no tier of Sang'thraze is carried
        MixedTiers,         // a Sang'thraze is carried, none of this tier
        NoResult,           // this tier has no Sul'thraze (a data error)
    };

    struct JoinDecision
    {
        JoinVerdict verdict = JoinVerdict::NotJangthraze;
        std::uint32_t step = 0;
        std::uint32_t sangthraze = 0;   // the entry to use up (Join only)
        std::uint32_t sulthraze = 0;    // the entry to make (Join only)
    };

    // `castEntry`: the item whose Use runs. `carried`: the entries the player carries; anything that is not a
    // Sang'thraze is ignored. Only the same step joins, whatever else is carried, so no join ever takes the better half
    // of a mixed pair.
    inline JoinDecision DecideJoin(JoinTable const& table, std::uint32_t castEntry,
        std::vector<std::uint32_t> const& carried)
    {
        JoinDecision decision;
        std::optional<BladeTier> const cast = table.Find(castEntry);
        if (!cast || cast->blade != Blade::Jangthraze)
            return decision;

        decision.step = cast->step;
        bool anyTier = false;
        bool sameTier = false;
        for (std::uint32_t const entry : carried)
        {
            std::optional<BladeTier> const other = table.Find(entry);
            if (!other || other->blade != Blade::Sangthraze)
                continue;
            anyTier = true;
            sameTier = sameTier || other->step == cast->step;
        }

        if (!sameTier)
        {
            decision.verdict = anyTier ? JoinVerdict::MixedTiers : JoinVerdict::NoSangthraze;
            return decision;
        }

        std::uint32_t const result = table.EntryOf(Blade::Sulthraze, cast->step);
        if (result == 0)
        {
            decision.verdict = JoinVerdict::NoResult;
            return decision;
        }

        decision.verdict = JoinVerdict::Join;
        decision.sangthraze = table.EntryOf(Blade::Sangthraze, cast->step);
        decision.sulthraze = result;
        return decision;
    }
}

#endif
