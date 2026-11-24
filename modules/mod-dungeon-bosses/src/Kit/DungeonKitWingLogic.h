/*
 * mod-dungeon-bosses, the shared dungeon kit (Scarlet Monastery WP-KT-SM, handoff section 3.11 #2 to #5): pure rules
 * for a dungeon of several wings. No engine headers; host-tested by tests/dungeon_kit_test.cpp. The engine halves are
 * DungeonKitWings.h (WingPortals, SealedArena, CreditEncounterBySpell) and DungeonKitWard.h (WardOfTheLiving).
 *
 *   JudgeTraveler       who a wing portal takes (section 7 #15): the user, and every group member on the map who is
 *                       alive, out of combat, free to move and within escortYd of the portal (of the user when there
 *                       is no portal object: a `.dbtest` use)
 *   NearestTrigger,     a spot's distance to the nearest of a list of area trigger centers (the wing exits), and the
 *   ClearOfTriggers     "at least minYd from every one" rule for portal spots and landings
 *   SealClock           a sealed arena's door (section 7 #22): open, closing `delayMs` after the pull, sealed; Update
 *                       says once when it closes; Release opens it again
 *   IsStraggler         at the close: a living group member outside the arena, in the same wing, within pullInYd of
 *                       the arena's entry spot, is moved to that spot
 *   CreditLatch         an encounter whose credit needs several deaths (the council: Azshir and the Fallen Champion):
 *                       true exactly once, at the death that completes the set
 *   WardRule            Ward of the Living (L38): a set share less damage per living add, capped; stacks and scaling
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WING_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WING_LOGIC_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <span>
#include <utility>
#include <vector>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Wing portals
    // ----------------------------------------------------------------------------------------------------------------

    // Section 7 #15: a use takes the user plus every living group member within 20 yd who is out of combat.
    float constexpr kPortalEscortYd = 20.f;

    enum class TravelVerdict : std::uint8_t
    {
        Go,
        OtherMap,       // not on the portal's map (or not in the world)
        Dead,           // dead or a ghost
        InCombat,
        Busy,           // teleporting, on a taxi or in a vehicle
        TooFar          // an escort farther than escortYd from the portal
    };

    struct TravelerFacts
    {
        bool isUser = false;
        bool sameMap = true;
        bool alive = true;
        bool inCombat = false;
        bool busy = false;
        float distYd = 0.f;     // from the portal object (the user's own never counts)
    };

    // `userInCombatGoes`: the user travels while in combat (default no: a portal is not a way out of a fight; the
    // escorts are always held to "out of combat").
    inline TravelVerdict JudgeTraveler(TravelerFacts const& f, float escortYd = kPortalEscortYd,
        bool userInCombatGoes = false)
    {
        if (!f.sameMap)
            return TravelVerdict::OtherMap;
        if (!f.alive)
            return TravelVerdict::Dead;
        if (f.busy)
            return TravelVerdict::Busy;
        if (f.inCombat && !(f.isUser && userInCombatGoes))
            return TravelVerdict::InCombat;
        if (!f.isUser && f.distYd > escortYd)
            return TravelVerdict::TooFar;
        return TravelVerdict::Go;
    }

    inline char const* TravelVerdictName(TravelVerdict v)
    {
        switch (v)
        {
            case TravelVerdict::Go:
                return "go";
            case TravelVerdict::OtherMap:
                return "other-map";
            case TravelVerdict::Dead:
                return "dead";
            case TravelVerdict::InCombat:
                return "in-combat";
            case TravelVerdict::Busy:
                return "busy";
            case TravelVerdict::TooFar:
                return "too-far";
        }
        return "?";
    }

    // The 2D distance from `spot` to the nearest of `triggers` (area trigger centers); +infinity with none.
    inline float NearestTrigger(Vec2 spot, std::span<Vec2 const> triggers)
    {
        float best = std::numeric_limits<float>::infinity();
        for (Vec2 const& t : triggers)
            best = std::min(best, Distance(spot, t));
        return best;
    }

    // A portal spot or landing keeps `minYd` from every trigger center (section 7 #15: 8 yd from the wing exits).
    // The trigger's own radius is the caller's to add to minYd.
    inline bool ClearOfTriggers(Vec2 spot, std::span<Vec2 const> triggers, float minYd)
    {
        return NearestTrigger(spot, triggers) >= minYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Sealed arena
    // ----------------------------------------------------------------------------------------------------------------

    // Section 7 #22: the seal closes 3 s after the pull; stragglers within 60 yd are moved in.
    std::uint32_t constexpr kSealDelayMs = 3000;
    float constexpr kSealPullInYd = 60.f;

    class SealClock
    {
    public:
        enum class State : std::uint8_t
        {
            Open,
            Closing,    // pulled; the door shuts when the delay runs out
            Sealed
        };

        // The pull: Closing for `delayMs` (0: Sealed at the next Update). A second Engage while Closing or Sealed
        // changes nothing (a re-engage mid-fight never re-opens the door or restarts the delay).
        void Engage(std::uint32_t delayMs)
        {
            if (_state != State::Open)
                return;
            _state = State::Closing;
            _leftMs = delayMs;
        }

        // True exactly once: the tick the door shuts.
        bool Update(std::uint32_t diff)
        {
            if (_state != State::Closing)
                return false;
            if (diff < _leftMs)
            {
                _leftMs -= diff;
                return false;
            }
            _leftMs = 0;
            _state = State::Sealed;
            return true;
        }

        // Death, reset or evade: Open again. True when it was not Open (the door, or its pending close, to undo).
        bool Release()
        {
            bool const was = _state != State::Open;
            _state = State::Open;
            _leftMs = 0;
            return was;
        }

        State Get() const { return _state; }
        bool IsOpen() const { return _state == State::Open; }
        bool IsClosing() const { return _state == State::Closing; }
        bool IsSealed() const { return _state == State::Sealed; }
        std::uint32_t LeftMs() const { return _leftMs; }

    private:
        State _state = State::Open;
        std::uint32_t _leftMs = 0;
    };

    struct StragglerFacts
    {
        bool alive = true;
        bool inArena = false;
        bool sameWing = true;   // the dungeon's wing test (no test: true)
        bool busy = false;      // teleporting, on a taxi or in a vehicle
        bool gameMaster = false;
        float distYd = 0.f;     // 3D, from the arena's entry spot
    };

    inline bool IsStraggler(StragglerFacts const& f, float pullInYd = kSealPullInYd)
    {
        return f.alive && !f.inArena && f.sameWing && !f.busy && !f.gameMaster && f.distYd <= pullInYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Encounter credit
    // ----------------------------------------------------------------------------------------------------------------

    // The deaths an encounter's credit waits for (keys: creature entries, never positions: RB-3). MarkDead returns true
    // exactly once, at the death that completes the set (a key it does not expect, or a second death of one, changes
    // nothing). A latch with no keys never fires. Reset (a wipe) forgets the deaths; Restore (a reload with the
    // encounter DONE) marks it fired without firing.
    class CreditLatch
    {
    public:
        CreditLatch() = default;
        explicit CreditLatch(std::vector<std::uint64_t> keys) : _keys(std::move(keys)), _dead(_keys.size(), false) { }

        bool MarkDead(std::uint64_t key)
        {
            if (_fired)
                return false;
            bool any = false;
            for (std::size_t i = 0; i < _keys.size(); ++i)
                if (_keys[i] == key && !_dead[i])
                {
                    _dead[i] = true;
                    any = true;
                    break;
                }
            if (!any || _keys.empty())
                return false;
            if (std::find(_dead.begin(), _dead.end(), false) != _dead.end())
                return false;
            _fired = true;
            return true;
        }

        bool IsDead(std::uint64_t key) const
        {
            for (std::size_t i = 0; i < _keys.size(); ++i)
                if (_keys[i] == key && _dead[i])
                    return true;
            return false;
        }

        std::size_t DeadCount() const { return static_cast<std::size_t>(std::count(_dead.begin(), _dead.end(), true)); }
        bool Fired() const { return _fired; }

        void Reset()
        {
            std::fill(_dead.begin(), _dead.end(), false);
            _fired = false;
        }

        void Restore()
        {
            std::fill(_dead.begin(), _dead.end(), true);
            _fired = true;
        }

    private:
        std::vector<std::uint64_t> _keys;
        std::vector<bool> _dead;
        bool _fired = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Ward of the Living (L38)
    // ----------------------------------------------------------------------------------------------------------------

    // The boss takes pctPerAdd % less damage per living add, at most capPct % (never full immunity: capPct is held
    // below 100). Blood Pact 20 / 80, Reader's Ward 25 / 50 (heroic 75), Inquisitor's Ward 50 / 50.
    struct WardRule
    {
        float pctPerAdd = 0.f;
        float capPct = 0.f;

        float Cap() const { return std::clamp(capPct, 0.f, 95.f); }

        // The reduction with `living` adds up.
        float ReductionPct(std::uint32_t living) const
        {
            if (pctPerAdd <= 0.f)
                return 0.f;
            return std::min(Cap(), pctPerAdd * static_cast<float>(living));
        }

        // The ward's stacks (one per living add, held at the cap's count: an aura of -pctPerAdd % per stack then
        // carries the reduction exactly).
        std::uint32_t Stacks(std::uint32_t living) const
        {
            if (pctPerAdd <= 0.f)
                return 0;
            std::uint32_t const capStacks = static_cast<std::uint32_t>(std::floor(Cap() / pctPerAdd + 1e-4f));
            return std::min(living, capStacks);
        }

        // `damage` after the reduction (rounded to nearest; a hit that was > 0 stays >= 1).
        std::uint32_t Scale(std::uint32_t damage, std::uint32_t living) const
        {
            float const pct = ReductionPct(living);
            if (damage == 0 || pct <= 0.f)
                return damage;
            auto const out = static_cast<std::uint32_t>(std::lround(static_cast<double>(damage) * (100.0 - pct)
                / 100.0));
            return std::max<std::uint32_t>(1, out);
        }
    };
}

#endif
