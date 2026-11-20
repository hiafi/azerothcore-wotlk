/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Depths WP-KT-D2, handoff section 3.11 #4 and #5): pure rules
 * for a health pool shared by several units and for a sliding-window damage tally. No engine headers; host-tested by
 * tests/dungeon_kit_test.cpp. The engine halves are DungeonKitPool.h (SharedHealthPool) and DungeonKitLedger.h
 * (DamageLedger).
 *
 *   PoolHit         one hit (or heal) on a member: who did it, its kind, the member, the amount, the time
 *   HealthPool      the shared pool: Damage / Heal from the members' hits, a cleave counted once per cast (hits of
 *                   one attacker and kind on different members in one cast window count as their largest hit, not
 *                   their sum), Restore (a scripted heal of the pool), Mirror (each member's health for the pool),
 *                   Emptied (the hit that took it to 0) and TakeDeathTick (true once: every member dies now)
 *   DamageTally     per-attacker damage over a sliding window (Phalanx's "top damage dealer of the last 10 s"):
 *                   Record, Total, Ranking (most damage first; a tie goes to the one who reached it first), Top (with
 *                   an exclusion list or a predicate)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_POOL_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_POOL_LOGIC_H

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <optional>
#include <span>
#include <vector>

namespace DungeonKit
{
    // ----------------------------------------------------------------------------------------------------------------
    // Shared health pool
    // ----------------------------------------------------------------------------------------------------------------

    // What a hit is, for the once-per-cast rule. The engine maps DamageEffectType: DIRECT_DAMAGE -> Melee,
    // SPELL_DIRECT_DAMAGE -> Spell, DOT -> Periodic, a heal -> Heal, anything else (NODAMAGE, SELF_DAMAGE, no
    // attacker) -> Other.
    enum class PoolHitKind : std::uint8_t
    {
        Melee,
        Spell,
        Periodic,
        Heal,
        Other           // never grouped: always counted in full
    };

    struct PoolHit
    {
        std::uint64_t attacker = 0;     // the raw guid of whoever dealt it (0: unknown, never grouped)
        PoolHitKind kind = PoolHitKind::Other;
        std::uint64_t member = 0;       // the member it landed on
        std::uint32_t amount = 0;
        std::uint64_t atMs = 0;         // the caller's clock (game time: one world tick has one value)
    };

    std::uint32_t constexpr kPoolCastWindowMs = 250;    // a missile cleave (Multi-Shot) lands over a few hundred ms

    // Who the death tick names as the killer (R-2-FW MIN-1 / R-2-B MN-1). The pool's recorded killer when it is still
    // on the map; else a member's loot recipient on the map; else any living player on the map; only then the member
    // itself. A self-kill finds no player (no KillRewarder), so an encounter credit (the Seven's row 243 on
    // Anger'rel) and the heroic bind would be lost.
    enum class PoolKiller : std::uint8_t
    {
        Recorded,
        LootRecipient,
        MapPlayer,
        Self
    };

    constexpr PoolKiller ChoosePoolKiller(bool recordedInMap, bool recipientInMap, bool playerInMap)
    {
        if (recordedInMap)
            return PoolKiller::Recorded;
        if (recipientInMap)
            return PoolKiller::LootRecipient;
        return playerInMap ? PoolKiller::MapPlayer : PoolKiller::Self;
    }

    // A known limit (R-1-FW MIN-5): the key is (attacker, kind, window), not the spell. The creature AI's DamageTaken
    // hook carries no spell id in this core, so two different hits of one player on two members inside the window
    // count as one (the largest): an instant on one ghost while a travelling bolt lands on another, a Judgement and a
    // Seal proc, Heroic Strike plus an instant, two DoTs ticking on the same world tick (Periodic: window 0). The
    // group loses that much damage into the pool; the Seven's tuning (D21 sims) absorbs it. A spell key would need a
    // UnitScript::ModifySpellDamageTaken side channel.

    // A pool of health shared by a set of units. Rules:
    //   - A hit on any member takes its amount from the pool (at most what is left).
    //   - Once per cast: hits of one attacker and one kind on DIFFERENT members within the cast window (Periodic: the
    //     same tick only) are one cast; the pool loses the largest of them, not their sum. A second hit on a member
    //     the cast already hit starts a new cast (a new swing, a new tick). Heals follow the same rule.
    //   - The hit that takes the pool to 0 is Emptied: every member is held at 1 health from then on (every later hit
    //     is absorbed, heals are ignored) until TakeDeathTick says, once, that they all die now.
    class HealthPool
    {
    public:
        struct Result
        {
            std::uint32_t change = 0;   // what the pool lost (Damage) or gained (Heal)
            bool merged = false;        // the hit joined a cast that already hit another member
            bool emptied = false;       // this hit took the pool to 0 (the first time)
        };

        explicit HealthPool(std::uint32_t max = 0, std::uint32_t castWindowMs = kPoolCastWindowMs)
            : _castWindowMs(castWindowMs)
        {
            Start(max);
        }

        // Full again at `max` (0 keeps the old max): the pull. Clears the casts and the death latch.
        void Start(std::uint32_t max = 0)
        {
            if (max)
                _max = max;
            _current = _max;
            _emptied = false;
            _deathTaken = false;
            _casts.clear();
        }

        void SetCastWindow(std::uint32_t ms) { _castWindowMs = ms; }

        Result Damage(PoolHit const& hit)
        {
            Result r;
            if (_emptied || !_max)
                return r;
            std::uint32_t const counted = Count(hit, r.merged);
            r.change = std::min(counted, _current);
            _current -= r.change;
            if (!_current)
            {
                _emptied = true;
                r.emptied = true;
            }
            return r;
        }

        Result Heal(PoolHit const& hit)
        {
            Result r;
            if (_emptied || !_max)
                return r;
            std::uint32_t const counted = Count(hit, r.merged);
            r.change = std::min(counted, _max - _current);
            _current += r.change;
            return r;
        }

        // A scripted heal of the pool itself (Vile Communion): never grouped. Returns the gain.
        std::uint32_t Restore(std::uint32_t amount)
        {
            if (_emptied || !_max)
                return 0;
            std::uint32_t const gain = std::min(amount, _max - _current);
            _current += gain;
            return gain;
        }

        // `pct` % of the max, rounded down.
        std::uint32_t RestorePct(float pct)
        {
            if (pct <= 0.f)
                return 0;
            return Restore(static_cast<std::uint32_t>(static_cast<double>(_max) * std::min(pct, 100.f) / 100.0));
        }

        // A member's health for the pool, scaled to its own max health (round up; at least 1 while the units live).
        std::uint32_t Mirror(std::uint32_t memberMax) const
        {
            if (!memberMax)
                return 0;
            if (!_max || _current >= _max)
                return memberMax;
            if (!_current)
                return 1;
            std::uint64_t const scaled = (static_cast<std::uint64_t>(_current) * memberMax + _max - 1) / _max;
            return static_cast<std::uint32_t>(std::clamp<std::uint64_t>(scaled, 1, memberMax));
        }

        // True once after the pool emptied: kill every member now.
        bool TakeDeathTick()
        {
            if (!_emptied || _deathTaken)
                return false;
            _deathTaken = true;
            return true;
        }

        std::uint32_t Max() const { return _max; }
        std::uint32_t Current() const { return _current; }
        float Pct() const { return _max ? 100.f * static_cast<float>(_current) / static_cast<float>(_max) : 0.f; }
        bool Emptied() const { return _emptied; }
        bool DeathTaken() const { return _deathTaken; }
        std::uint32_t CastWindowMs() const { return _castWindowMs; }
        std::size_t OpenCasts() const { return _casts.size(); }

    private:
        struct Cast
        {
            std::uint64_t attacker = 0;
            PoolHitKind kind = PoolHitKind::Other;
            std::uint64_t firstMs = 0;
            std::uint32_t top = 0;              // the largest hit counted so far
            std::vector<std::uint64_t> members;
        };

        // The amount this hit adds to its cast (all of it for a new cast; only what it exceeds the cast's top by for a
        // hit that joins one).
        std::uint32_t Count(PoolHit const& hit, bool& merged)
        {
            merged = false;
            Prune(hit.atMs);
            if (!hit.attacker || hit.kind == PoolHitKind::Other)
                return hit.amount;
            std::uint32_t const window = hit.kind == PoolHitKind::Periodic ? 0 : _castWindowMs;
            // The newest open cast of this attacker and kind.
            for (auto it = _casts.rbegin(); it != _casts.rend(); ++it)
            {
                Cast& c = *it;
                if (c.attacker != hit.attacker || c.kind != hit.kind)
                    continue;
                bool const inWindow = hit.atMs >= c.firstMs && hit.atMs - c.firstMs <= window;
                bool const newMember = std::find(c.members.begin(), c.members.end(), hit.member) == c.members.end();
                if (!inWindow || !newMember)
                    break;                      // a new cast
                merged = true;
                c.members.push_back(hit.member);
                if (hit.amount <= c.top)
                    return 0;
                std::uint32_t const extra = hit.amount - c.top;
                c.top = hit.amount;
                return extra;
            }
            Cast c;
            c.attacker = hit.attacker;
            c.kind = hit.kind;
            c.firstMs = hit.atMs;
            c.top = hit.amount;
            c.members.push_back(hit.member);
            _casts.push_back(std::move(c));
            return hit.amount;
        }

        void Prune(std::uint64_t nowMs)
        {
            std::uint64_t const keep = static_cast<std::uint64_t>(_castWindowMs) + 1000;
            _casts.erase(std::remove_if(_casts.begin(), _casts.end(), [nowMs, keep](Cast const& c)
            {
                return nowMs > c.firstMs + keep;
            }), _casts.end());
        }

        std::uint32_t _max = 0;
        std::uint32_t _current = 0;
        std::uint32_t _castWindowMs;
        bool _emptied = false;
        bool _deathTaken = false;
        std::vector<Cast> _casts;               // oldest first
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Damage tally (a damage meter over a sliding window)
    // ----------------------------------------------------------------------------------------------------------------

    std::uint32_t constexpr kTallyWindowMs = 10000;     // Phalanx's Throw Out: "the last 10 s"

    struct TallyStanding
    {
        std::uint64_t who = 0;
        std::uint64_t total = 0;
        std::uint64_t lastMs = 0;       // when it reached `total` (its newest hit in the window)
        std::uint64_t firstMs = 0;      // its oldest hit in the window
    };

    // Damage per credited attacker (the engine credits a pet's, a totem's or a guardian's hits to its player) over the
    // last `windowMs`. A hit exactly `windowMs` old has left the window.
    class DamageTally
    {
    public:
        explicit DamageTally(std::uint32_t windowMs = kTallyWindowMs) : _windowMs(windowMs) { }

        void Record(std::uint64_t who, std::uint32_t amount, std::uint64_t nowMs)
        {
            if (!who || !amount)
                return;
            Prune(nowMs);
            _hits.push_back({ who, amount, nowMs });
        }

        void Prune(std::uint64_t nowMs)
        {
            while (!_hits.empty() && nowMs >= _hits.front().atMs + _windowMs)
                _hits.pop_front();
        }

        std::uint64_t Total(std::uint64_t who, std::uint64_t nowMs)
        {
            Prune(nowMs);
            std::uint64_t sum = 0;
            for (Hit const& h : _hits)
                if (h.who == who)
                    sum += h.amount;
            return sum;
        }

        // Every attacker in the window, most damage first; a tie goes to the one who reached it first (the earlier
        // newest hit), then to the earlier first hit, then to the lower id.
        std::vector<TallyStanding> Ranking(std::uint64_t nowMs)
        {
            Prune(nowMs);
            std::vector<TallyStanding> out;
            for (Hit const& h : _hits)
            {
                auto it = std::find_if(out.begin(), out.end(), [&h](TallyStanding const& s) { return s.who == h.who; });
                if (it == out.end())
                {
                    out.push_back({ h.who, h.amount, h.atMs, h.atMs });
                    continue;
                }
                it->total += h.amount;
                it->lastMs = h.atMs;
            }
            std::sort(out.begin(), out.end(), [](TallyStanding const& a, TallyStanding const& b)
            {
                if (a.total != b.total)
                    return a.total > b.total;
                if (a.lastMs != b.lastMs)
                    return a.lastMs < b.lastMs;
                if (a.firstMs != b.firstMs)
                    return a.firstMs < b.firstMs;
                return a.who < b.who;
            });
            return out;
        }

        // The top attacker that `eligible(who)` accepts (none: nobody in the window qualifies).
        template <class Pred>
        std::optional<TallyStanding> TopIf(std::uint64_t nowMs, Pred&& eligible)
        {
            for (TallyStanding const& s : Ranking(nowMs))
                if (eligible(s.who))
                    return s;
            return std::nullopt;
        }

        // The top attacker not in `exclude` (Throw Out: never the current victim, never the last one thrown).
        std::optional<TallyStanding> Top(std::uint64_t nowMs, std::span<std::uint64_t const> exclude = {})
        {
            return TopIf(nowMs, [exclude](std::uint64_t who)
            {
                return std::find(exclude.begin(), exclude.end(), who) == exclude.end();
            });
        }

        void Clear() { _hits.clear(); }
        std::size_t Size() const { return _hits.size(); }
        std::uint32_t WindowMs() const { return _windowMs; }

    private:
        struct Hit
        {
            std::uint64_t who;
            std::uint32_t amount;
            std::uint64_t atMs;
        };

        std::uint32_t _windowMs;
        std::deque<Hit> _hits;      // time order (the caller's clock never runs backwards)
    };
}

#endif
