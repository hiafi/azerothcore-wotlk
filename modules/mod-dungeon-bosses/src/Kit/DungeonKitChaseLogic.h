/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Spire WP-KT-B1, handoff section 3.11 #3-#5): pure rules for
 * the movers wave 1 adds (no engine headers; host-tested by tests/dungeon_kit_test.cpp). The engine halves are in
 * DungeonKitChase.h.
 *
 *   ChaseClock     a chaser's step each update: move, hold after a toss or a stun, retarget, arrive, expire (#3)
 *   CrawlClock     a pickup's wait, then its crawl to a goal, and its arrival (#4)
 *   FallCatchBook  who is below the deck now and may be caught (with a grace after each catch) (#5)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_CHASE_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_CHASE_LOGIC_H

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <unordered_map>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // ChaseClock (#3)
    // ----------------------------------------------------------------------------------------------------------------

    enum class ChaseStep : std::uint8_t
    {
        Move,       // keep after the target (re-aim when due)
        Hold,       // stopped: tossed or stunned now, or within the pause that follows
        Retarget,   // the target is gone (dead, left), or the retarget period ran out: pick another
        Arrive,     // within reach of the target (with endOnArrive the chase is over; else once per contact)
        Expire      // the chase's life ran out
    };

    struct ChaseTuning
    {
        std::uint32_t pauseMs = 1000;       // a toss or a stun stops it at least this long from its start
        std::uint32_t retargetEveryMs = 0;  // no-threat mode: a new pick every this long (0: only when the target goes)
        std::uint32_t lifeMs = 0;           // 0: no end but an arrival or Stop
        float reach = 2.f;                  // yd (2D) from the target that count as arrived
        bool endOnArrive = true;            // false: keeps chasing; Arrive again only after it left reach + kLeaveSlack
    };

    // Feed it every update with the chaser's state; it answers the step. Precedence: Expire, Hold, Retarget, Arrive,
    // Move. A hold ignores the target until it ends (a chaser stunned while its target dies retargets after the stun).
    class ChaseClock
    {
    public:
        static constexpr float kLeaveSlack = 1.f;   // yd past reach that end a contact (endOnArrive false)

        explicit ChaseClock(ChaseTuning tuning = {}) : _t(tuning) { }

        void Restart()
        {
            _elapsedMs = 0;
            _sinceRetargetMs = 0;
            _holdLeftMs = 0;
            _wasControlled = false;
            _inContact = false;
            _done = false;
        }

        // `controlled`: tossed or stunned now. `targetValid`: the target is alive, on the map, attackable. `dist`:
        // 2D distance to the target (ignored when it is not valid).
        ChaseStep Update(std::uint32_t diffMs, bool controlled, bool targetValid, float dist)
        {
            if (_done)
                return ChaseStep::Expire;
            _elapsedMs += diffMs;
            _sinceRetargetMs += diffMs;
            if (_t.lifeMs && _elapsedMs >= _t.lifeMs)
            {
                _done = true;
                return ChaseStep::Expire;
            }

            if (controlled)
            {
                if (!_wasControlled)
                    _holdLeftMs = _t.pauseMs;
                else
                    _holdLeftMs = _holdLeftMs > diffMs ? _holdLeftMs - diffMs : 0;
                _wasControlled = true;
                _inContact = false;
                return ChaseStep::Hold;
            }
            if (_wasControlled)
            {
                // The control just ended: the rest of the pause counts from its start.
                _wasControlled = false;
                _holdLeftMs = _holdLeftMs > diffMs ? _holdLeftMs - diffMs : 0;
                if (_holdLeftMs)
                    return ChaseStep::Hold;
            }
            else if (_holdLeftMs)
            {
                _holdLeftMs = _holdLeftMs > diffMs ? _holdLeftMs - diffMs : 0;
                if (_holdLeftMs)
                    return ChaseStep::Hold;
            }

            if (!targetValid)
            {
                _inContact = false;
                return ChaseStep::Retarget;
            }
            if (_t.retargetEveryMs && _sinceRetargetMs >= _t.retargetEveryMs)
            {
                _inContact = false;
                return ChaseStep::Retarget;
            }
            if (dist <= _t.reach)
            {
                if (_t.endOnArrive)
                {
                    _done = true;
                    return ChaseStep::Arrive;
                }
                if (!_inContact)
                {
                    _inContact = true;
                    return ChaseStep::Arrive;
                }
                return ChaseStep::Move;
            }
            if (_inContact && dist > _t.reach + kLeaveSlack)
                _inContact = false;
            return ChaseStep::Move;
        }

        // The caller picked a new target (or kept the old one when nobody else qualifies): the period restarts.
        void Retargeted()
        {
            _sinceRetargetMs = 0;
            _inContact = false;
        }

        bool Done() const { return _done; }
        bool Holding() const { return _wasControlled || _holdLeftMs > 0; }
        std::uint32_t ElapsedMs() const { return _elapsedMs; }
        ChaseTuning const& Tuning() const { return _t; }

    private:
        ChaseTuning _t;
        std::uint32_t _elapsedMs = 0;
        std::uint32_t _sinceRetargetMs = 0;
        std::uint32_t _holdLeftMs = 0;
        bool _wasControlled = false;
        bool _inContact = false;
        bool _done = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // CrawlClock (#4)
    // ----------------------------------------------------------------------------------------------------------------

    enum class CrawlStep : std::uint8_t
    {
        Wait,       // lying where it fell
        Crawl,      // on its way to the goal (re-path when due)
        Reach,      // at the goal: the pickup is spent
        Expire      // its life ran out (a safety; 0 = none)
    };

    // A pickup's crawl: `waitMs` lying still, then crawling until it is within `reach` of its goal. A pickup with no
    // goal (or crawl off) waits until taken or expired.
    class CrawlClock
    {
    public:
        CrawlClock() = default;
        CrawlClock(std::uint32_t waitMs, std::uint32_t lifeMs, float reach, bool crawl = true)
            : _waitMs(waitMs), _lifeMs(lifeMs), _reach(reach), _crawl(crawl) { }

        // `hasGoal`: a goal unit or point is known now. `dist`: 2D distance to it (ignored without one).
        CrawlStep Update(std::uint32_t diffMs, bool hasGoal, float dist)
        {
            if (_done)
                return _last;
            _ageMs += diffMs;
            if (_lifeMs && _ageMs >= _lifeMs)
                return Finish(CrawlStep::Expire);
            if (!_crawl || !hasGoal || _ageMs < _waitMs)
                return CrawlStep::Wait;
            if (dist <= _reach)
                return Finish(CrawlStep::Reach);
            return CrawlStep::Crawl;
        }

        std::uint32_t AgeMs() const { return _ageMs; }
        bool Crawling() const { return _crawl && !_done && _ageMs >= _waitMs; }
        bool Done() const { return _done; }

    private:
        CrawlStep Finish(CrawlStep step)
        {
            _done = true;
            _last = step;
            return step;
        }

        std::uint32_t _waitMs = 10000;
        std::uint32_t _lifeMs = 0;
        float _reach = 1.5f;
        bool _crawl = true;
        std::uint32_t _ageMs = 0;
        bool _done = false;
        CrawlStep _last = CrawlStep::Expire;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // FallCatchBook (#5)
    // ----------------------------------------------------------------------------------------------------------------

    // Below the deck: `z` at least `below` yd under `deckZ`.
    constexpr bool BelowDeck(float z, float deckZ, float below)
    {
        return z <= deckZ - below;
    }

    // Which of a player's controlled units (Unit::m_Controlled) a pet-watching FallWatch watches: pets and guardians
    // only. Totems (minions, rooted: a jump back cannot move them) and charmed creatures (a mind-controlled mob is
    // not the player's pet; the pit rule is for the party) are skipped (R-1-KIT K-m5).
    constexpr bool WatchesControlled(bool pet, bool guardian, bool totem, bool charmed)
    {
        return (pet || guardian) && !totem && !charmed;
    }

    // Who was caught when (raw guids, the caller's clock in ms): a unit just caught is still below the deck while its
    // jump back climbs, so it is not caught again within `graceMs` of the last catch.
    class FallCatchBook
    {
    public:
        explicit FallCatchBook(std::uint32_t graceMs = 3000) : _graceMs(graceMs) { }

        // True when the unit `id` at height `z` (inside the watched region: `inRegion`) is to be caught now; it is
        // then booked at `nowMs`.
        bool Check(std::uint64_t id, float z, bool inRegion, float deckZ, float below, std::uint64_t nowMs)
        {
            if (!inRegion || !BelowDeck(z, deckZ, below))
                return false;
            auto it = _last.find(id);
            if (it != _last.end() && nowMs < it->second + _graceMs)
                return false;
            _last[id] = nowMs;
            return true;
        }

        // Drops every entry whose grace ended before `nowMs` (call it now and then; the book stays small).
        void Prune(std::uint64_t nowMs)
        {
            for (auto it = _last.begin(); it != _last.end();)
            {
                if (nowMs >= it->second + _graceMs)
                    it = _last.erase(it);
                else
                    ++it;
            }
        }

        void Clear() { _last.clear(); }
        std::size_t Size() const { return _last.size(); }
        std::uint32_t GraceMs() const { return _graceMs; }

    private:
        std::uint32_t _graceMs;
        std::unordered_map<std::uint64_t, std::uint64_t> _last;
    };
}

#endif
