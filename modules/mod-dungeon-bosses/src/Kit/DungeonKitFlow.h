/*
 * mod-dungeon-bosses, the shared dungeon kit (Stratholme WP-KT-1, handoff section 3.11 #17, #19, #22-#24): pure rules
 * for the fight's flow (no engine headers; host-tested by tests/dungeon_kit_test.cpp). The engine halves are in
 * DungeonKitFields.h and DungeonKitSpells.cpp.
 *
 *   WeightedSplit      a shared hit split evenly, then each share raised by its taker's stacks (kit #19: the
 *                      Baroness's Death Knell x (1 + Death's Echo); WeightedShares is the engine half)
 *   CappedWaveSize     how many adds a wave may add under a live cap (kit #22: the Baron's 6 skeletons)
 *   CastQueue          due casts with priorities and a minimum spacing: "casts never overlap; the second waits for the
 *                      first", stock fillers wait for the mechanics (kit #24)
 *   HoldBook           who holds whom, until when, and why each hold ended (kit #23: HoldInUnit's state)
 *   EffectPercent      the percent a generic percent spell carries in its effect (kit #17: spell_dungeon_refflat_*)
 *   PerStackAmount     spell_dungeon_refflat_periodic's cached per-stack tick for a recalculation without a caster
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLOW_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLOW_H

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <optional>
#include <vector>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Weighted split (kit #19)
    // ----------------------------------------------------------------------------------------------------------------

    // `total` split evenly among stacks.size() takers (SplitDamage's even split: the remainder one point each to the
    // first shares), then share i times (1 + perStack x stacks[i]), rounded, capped at `capEach` (0 = no cap). With
    // perStack 1 (+100% per stack) a taker with 2 stacks takes three even shares. Empty for no takers.
    inline std::vector<std::uint32_t> WeightedSplit(std::uint32_t total, std::vector<std::uint32_t> const& stacks,
        float perStack, std::uint32_t capEach = 0)
    {
        std::vector<std::uint32_t> shares;
        std::size_t const n = stacks.size();
        if (!n)
            return shares;
        std::uint32_t const count = static_cast<std::uint32_t>(n);
        std::uint32_t const base = total / count;
        std::uint32_t const rest = total % count;
        shares.reserve(n);
        for (std::size_t i = 0; i < n; ++i)
        {
            double const even = double(base + (i < rest ? 1 : 0));
            double const factor = std::max(0.0, 1.0 + double(perStack) * double(stacks[i]));
            double v = std::round(even * factor);
            if (v > double(std::numeric_limits<std::uint32_t>::max()))
                v = double(std::numeric_limits<std::uint32_t>::max());
            std::uint32_t share = static_cast<std::uint32_t>(v);
            if (capEach && share > capEach)
                share = capEach;
            shares.push_back(share);
        }
        return shares;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Waves (kit #22)
    // ----------------------------------------------------------------------------------------------------------------

    // How many of `want` adds a wave may add with `alive` of them up and a cap of `cap` live at once (0 = no cap).
    constexpr std::uint32_t CappedWaveSize(std::uint32_t want, std::uint32_t alive, std::uint32_t cap)
    {
        if (!cap)
            return want;
        return alive >= cap ? 0 : std::min(want, cap - alive);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // CastQueue (kit #24): a boss's casts, one at a time. Schedule marks a cast due at a time with a priority; Next
    // names the cast to start now: none while the caster is busy (a cast or channel it Started, or SetBusy), none
    // within `spacing` of the last spaced cast's end, else the due cast with the highest priority (ties: the earliest
    // due, then the lowest id). Started takes it off the queue and holds the caster for its cast time. A due cast may
    // carry a `dropAfter`: still waiting that long past its due time, it is dropped (a stock filler's turn that never
    // came). Ids are the script's own (an enum); times are the caller's clock in ms (GameTime, or an accumulated diff).
    //
    //     _queue.Schedule(CAST_COCOON, now + 20000, 2);           // mechanics: priority above the fillers
    //     _queue.Schedule(CAST_SHADOW_BOLT, now + 6000, 0, 4000); // the stock filler waits, or skips its turn
    //     if (std::optional<uint32> c = _queue.Next(now))  { Cast(*c); _queue.Started(*c, now, castMs); }
    // ----------------------------------------------------------------------------------------------------------------

    class CastQueue
    {
    public:
        using Ms = std::uint64_t;

        explicit CastQueue(Ms spacingMs = 0) : _spacing(spacingMs) { }

        void Reset()
        {
            _due.clear();
            _busyUntil = 0;
            _nextAllowed = 0;
            _busy = false;
        }

        // `id` is due at `at` with `priority` (higher first); replaces an earlier entry for the same id. `dropAfter`
        // > 0: dropped when still waiting `dropAfter` ms past `at`.
        void Schedule(std::uint32_t id, Ms at, std::uint8_t priority = 0, Ms dropAfter = 0)
        {
            Cancel(id);
            _due.push_back({ id, at, priority, dropAfter });
        }

        void Cancel(std::uint32_t id)
        {
            std::erase_if(_due, [id](Entry const& e) { return e.id == id; });
        }

        bool Queued(std::uint32_t id) const { return Find(id) != nullptr; }

        std::optional<Ms> DueAt(std::uint32_t id) const
        {
            Entry const* e = Find(id);
            return e ? std::optional<Ms>(e->at) : std::nullopt;
        }

        std::size_t Size() const { return _due.size(); }

        // An open-ended hold (a run, a channel of unknown length): nothing starts until SetBusy(false).
        void SetBusy(bool busy) { _busy = busy; }

        // The caster cannot start anything before `now`: busy, or within the spacing of the last cast.
        bool Waiting(Ms now) const { return _busy || now < _busyUntil || now < _nextAllowed; }

        // Drops the entries past their dropAfter; returns their ids.
        std::vector<std::uint32_t> DropStale(Ms now)
        {
            std::vector<std::uint32_t> dropped;
            std::erase_if(_due, [now, &dropped](Entry const& e)
            {
                if (!e.dropAfter || now < e.at + e.dropAfter)
                    return false;
                dropped.push_back(e.id);
                return true;
            });
            return dropped;
        }

        // The cast to start now; nullopt: nothing due, or the caster must wait. (Stale entries are skipped; call
        // DropStale to clear them.)
        std::optional<std::uint32_t> Next(Ms now) const
        {
            if (Waiting(now))
                return std::nullopt;
            Entry const* best = nullptr;
            for (Entry const& e : _due)
            {
                if (e.at > now || (e.dropAfter && now >= e.at + e.dropAfter))
                    continue;
                if (!best || e.priority > best->priority || (e.priority == best->priority
                    && (e.at < best->at || (e.at == best->at && e.id < best->id))))
                    best = &e;
            }
            return best ? std::optional<std::uint32_t>(best->id) : std::nullopt;
        }

        // `id` started at `now` and holds the caster `castMs` (0: instant). With `spaced` the next cast also waits the
        // queue's spacing after it ends (a stock filler passes false: it never delays a mechanic).
        void Started(std::uint32_t id, Ms now, Ms castMs = 0, bool spaced = true)
        {
            Cancel(id);
            _busyUntil = std::max(_busyUntil, now + castMs);
            if (spaced)
                _nextAllowed = std::max(_nextAllowed, now + castMs + _spacing);
        }

        // The caster's cast ended early (interrupted, cancelled) at `now`: the hold ends now, the spacing counts from
        // now.
        void Interrupted(Ms now)
        {
            if (_busyUntil > now)
            {
                if (_nextAllowed > now)
                    _nextAllowed = std::min(_nextAllowed, now + _spacing);
                _busyUntil = now;
            }
        }

        Ms Spacing() const { return _spacing; }

    private:
        struct Entry
        {
            std::uint32_t id = 0;
            Ms at = 0;
            std::uint8_t priority = 0;
            Ms dropAfter = 0;
        };

        Entry const* Find(std::uint32_t id) const
        {
            for (Entry const& e : _due)
                if (e.id == id)
                    return &e;
            return nullptr;
        }

        Ms _spacing;
        std::vector<Entry> _due;
        Ms _busyUntil = 0;
        Ms _nextAllowed = 0;
        bool _busy = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // HoldBook (kit #23): who holds whom (raw guids), for how much longer, and why each hold ended.
    // ----------------------------------------------------------------------------------------------------------------

    enum class HoldEnd : std::uint8_t
    {
        Timeout,        // maxHold ran out
        HolderGone,     // the holder died, despawned or left the map (broken out)
        HeldGone,       // the held unit died or left the map
        Released,       // the script let go (Release)
        Cleared         // the fight ended (Clear)
    };

    inline char const* HoldEndName(HoldEnd why)
    {
        switch (why)
        {
            case HoldEnd::Timeout:
                return "timeout";
            case HoldEnd::HolderGone:
                return "holder-gone";
            case HoldEnd::HeldGone:
                return "held-gone";
            case HoldEnd::Released:
                return "released";
            case HoldEnd::Cleared:
                return "cleared";
        }
        return "?";
    }

    class HoldBook
    {
    public:
        struct Hold
        {
            std::uint64_t holder = 0;
            std::uint64_t held = 0;
            std::uint32_t remainingMs = 0;
        };

        struct Ended
        {
            std::uint64_t holder = 0;
            std::uint64_t held = 0;
            HoldEnd why = HoldEnd::Timeout;
        };

        // False when `held` is already held (one hold per unit) or a unit would hold itself.
        bool Add(std::uint64_t holder, std::uint64_t held, std::uint32_t maxHoldMs)
        {
            if (holder == held || HolderOf(held))
                return false;
            _holds.push_back({ holder, held, maxHoldMs });
            return true;
        }

        // Advances every hold by `diffMs`; `holderOk(holder)` / `heldOk(held)` say whether each side is still there.
        // A gone holder ends the hold first, then a gone held unit, then the timeout. Returns the ended holds.
        template <class HolderOk, class HeldOk>
        std::vector<Ended> Update(std::uint32_t diffMs, HolderOk&& holderOk, HeldOk&& heldOk)
        {
            std::vector<Ended> ended;
            std::erase_if(_holds, [&](Hold& h)
            {
                std::optional<HoldEnd> why;
                if (!holderOk(h.holder))
                    why = HoldEnd::HolderGone;
                else if (!heldOk(h.held))
                    why = HoldEnd::HeldGone;
                else if (h.remainingMs <= diffMs)
                    why = HoldEnd::Timeout;
                if (!why)
                {
                    h.remainingMs -= diffMs;
                    return false;
                }
                ended.push_back({ h.holder, h.held, *why });
                return true;
            });
            return ended;
        }

        std::optional<Ended> Release(std::uint64_t held, HoldEnd why = HoldEnd::Released)
        {
            for (auto it = _holds.begin(); it != _holds.end(); ++it)
                if (it->held == held)
                {
                    Ended const e{ it->holder, it->held, why };
                    _holds.erase(it);
                    return e;
                }
            return std::nullopt;
        }

        std::vector<Ended> Clear()
        {
            std::vector<Ended> ended;
            for (Hold const& h : _holds)
                ended.push_back({ h.holder, h.held, HoldEnd::Cleared });
            _holds.clear();
            return ended;
        }

        // The holder of `held` (0: not held).
        std::uint64_t HolderOf(std::uint64_t held) const
        {
            for (Hold const& h : _holds)
                if (h.held == held)
                    return h.holder;
            return 0;
        }

        std::vector<Hold> const& All() const { return _holds; }
        std::size_t Size() const { return _holds.size(); }

    private:
        std::vector<Hold> _holds;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Generic percent spells (kit #17): spell_dungeon_refflat_damage (SPELL_EFFECT_SCHOOL_DAMAGE) and
    // spell_dungeon_refflat_periodic (SPELL_AURA_PERIODIC_DAMAGE) replace every such effect's value with RefFlatOn of a
    // percent the effect carries in hundredths: its value (EffectBasePoints + 1 as stored, i.e. the shown value) on
    // normal, its EffectMiscValueB on heroic (0: the normal value). 3000 = 30%, 50 = 0.5%.
    // ----------------------------------------------------------------------------------------------------------------

    // The effect's shown value: SpellEffectInfo::CalcValue without the level scaling, the potency roll or a random
    // spread (a DieSides range takes its low end).
    constexpr std::int32_t EffectShownValue(std::int32_t basePoints, std::int32_t dieSides)
    {
        return basePoints + (dieSides >= 1 ? 1 : (dieSides <= -1 ? -1 : 0));
    }

    // The percent (of the reference row) the effect carries: hundredths of the shown value, or of miscValueB on heroic
    // when it is set. Negative values are 0.
    constexpr float EffectPercent(std::int32_t shownValue, std::int32_t miscValueB, bool heroic)
    {
        std::int32_t const hundredths = heroic && miscValueB ? miscValueB : shownValue;
        return hundredths > 0 ? float(hundredths) / 100.f : 0.f;
    }

    // spell_dungeon_refflat_periodic's per-stack tick (R-1-KIT F1). The engine starts every (re)calculation from the
    // effect's raw value (the hundredths: 400 for 4%) and multiplies the hook's result by the stack count. A
    // recalculation without a caster (a summoned stalker despawned, then a stack change or a one-stack dispel) must not
    // leave the hundredths in place: it reuses the amount the last calculation with a caster made, or, when there was
    // none, the amount computed from the aura's owner, or 0. Never the raw value.
    class PerStackAmount
    {
    public:
        // `withCaster`: the amount computed from the caster this time, if it was there.
        // `fromOwner`: the amount computed from the aura's owner (used only when nothing was cached), if possible.
        std::int32_t Resolve(std::optional<std::int32_t> withCaster, std::optional<std::int32_t> fromOwner)
        {
            if (withCaster)
            {
                _cached = *withCaster;
                return *_cached;
            }
            if (_cached)
                return *_cached;
            return fromOwner ? *fromOwner : 0;
        }

        std::optional<std::int32_t> Cached() const { return _cached; }

    private:
        std::optional<std::int32_t> _cached;
    };
}

#endif
