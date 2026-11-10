/*
 * mod-dungeon-bosses, Stratholme S3: Timmy the Cruel (10808), the pure, host-testable part (no engine headers).
 * Build spec ST 1035-1090 (docs/dungeons/stratholme-rework.md; design ST 886-1034), handoff section 3.4 rows TC and
 * 3.5 row S3. Tested by tests/strat_timmy_test.cpp.
 *
 *   Spells          the WP's ids, inside kSpellsTimmy (206460-206479), declared in apps/dbc-tools
 *                   source/npcs/stratholme/timmy_the_cruel.py
 *   Tuning          NH<> constants: one number per difficulty, straight from the build spec
 *   Playtime        TC1 the timers (never health): Freeze Tag at 8 s, then every 40 s; a game slot every 15 s from
 *                   20 s, rotating Guess Who, Jump Rope, Patty Cake (heroic: two at once, GW+JR, PC+GW, JR+PC)
 *   GamesOfSlot     TC1 which game(s) a slot plays
 *   CastOrder       TC1 a slot's casting games, one after another (a unit holds one cast): Patty Cake first
 *   FreezeRound     TC2-TC5 a 15 s round: a tag every 3 s (5 tags, each bursts 2 s later, inside the round), the
 *                   round ends on its timer or when everyone is frozen at once (Gotcha)
 *   PickTag         TC2 a random player who is not frozen, tank included
 *   BurstVictims    TC3 who a burst freezes: the tagged player and everyone inside
 *   PlaymateFocus   TC7 the playmates go for the nearest frozen player first
 *   PlaymateSpots   TC7 where the playmates burst up (the square's edges; heroic one more)
 *   SkipsOf         TC8 the rope's casts: three 2 s skips (the heroic fallback Double Dutch: 2, 2, 1.5, 1.5, 1.5)
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_TIMMY_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_TIMMY_LOGIC_H

#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace StratTimmy
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsTimmy;

    enum TimmySpells : std::uint32_t
    {
        SPELL_TC_TAGGED             = kSpellSlice.first + 0,    // 206460 TC2 "Tag!": the 2 s debuff on the tagged
        SPELL_TC_FROZEN             = kSpellSlice.first + 1,    // 206461 TC3 -70% speed, 2% Frost a second
        SPELL_TC_SHATTER            = kSpellSlice.first + 2,    // 206462 TC5 the shatter (resolve copy, Frost)
        SPELL_TC_PATTY_CAKE         = kSpellSlice.first + 3,    // 206463 TC6 the 4 s channel (interruptible)
        SPELL_TC_CLAP               = kSpellSlice.first + 4,    // 206464 TC6 a clap: the square, 10% / 20% Physical
        SPELL_TC_JUMP_ROPE          = kSpellSlice.first + 5,    // 206465 TC8 a 2 s skip (cast bar)
        SPELL_TC_JUMP_ROPE_FAST     = kSpellSlice.first + 6,    // 206466 TC8 a 1.5 s skip (Double Dutch)
        SPELL_TC_TRIP               = kSpellSlice.first + 7,    // 206467 TC9 the trip (resolve copy, Physical)
        SPELL_TC_TRIPPED            = kSpellSlice.first + 8,    // 206468 TC9 the 1 s knockdown (the trip's rider)
        // 206469-206479 spare
    };
    static_assert(SPELL_TC_TRIPPED <= kSpellSlice.last, "Timmy's spells must stay in his slice");

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum TimmyTags : std::uint32_t
    {
        TAG_TAG         = 1,    // TC2 the 6 yd tag marker (telegraph-only RunOut)
        TAG_THAW        = 2,    // TC4 the 3 yd touch on a frozen player (telegraph-only Soak)
        TAG_SHATTER     = 3,    // TC5 the shatter (RegistryHit)
        TAG_JUMP_ROPE   = 4,    // TC8 / TC9 the rope's sweep (Jump)
    };

    // Stock path 2472270 (23 points round the square; SmartAI 10808 / actionlist 1080800, now C++).
    inline constexpr std::uint32_t kPatrolPath = 2472270;
    // The stock gate (conditions SourceType 22 group 7 on 10808): no living Crimson Guardsman, Conjuror, Initiate or
    // Gallant within 70 yd, checked every 10 s out of combat; then the emerge (emote state 449 for 3.5 s) and the path.
    inline constexpr std::array<std::uint32_t, 4> kGateEntries{ { 10418, 10419, 10420, 10424 } };
    inline constexpr float kGateRangeYd = 70.f;
    inline constexpr std::uint32_t kGateCheckMs = 10000;
    inline constexpr std::uint32_t kEmergeMs = 3500;
    inline constexpr std::uint32_t kEmoteEmerge = 449;          // EMOTE_ONESHOT_EMERGE (V-2 EMOTE_ONESHOT_EMERGE)

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST 1035-1090; percents of the reference row: N 3,670 / 3,710, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Game : std::uint8_t
    {
        GuessWho,
        JumpRope,
        PattyCake,
    };

    inline constexpr char const* GameName(Game game)
    {
        return game == Game::GuessWho ? "guess-who" : (game == Game::JumpRope ? "jump-rope" : "patty-cake");
    }

    // TC1 Playtime: Freeze Tag first at 8 s, then every 40 s; the other games take a 15 s slot each from 20 s.
    inline constexpr std::uint32_t kFreezeFirstMs = 8000;
    inline constexpr std::uint32_t kFreezeEveryMs = 40000;
    inline constexpr std::uint32_t kSlotFirstMs = 20000;
    inline constexpr std::uint32_t kSlotEveryMs = 15000;

    // TC2-TC5 Freeze Tag: a 15 s round; a tag every 3 s from the round's start, a 6 yd marker for 2 s, then the burst
    // freezes the tagged player and everyone inside. Frozen: -70% speed, 2% Frost a second; a touch (3 yd) by an
    // unfrozen player thaws at once; whoever is still frozen at the round's end shatters for 30% + Weakened.
    inline constexpr std::uint32_t kRoundMs = 15000;
    inline constexpr std::uint32_t kTagEveryMs = 3000;
    inline constexpr std::uint32_t kTagWarnMs = 2000;
    inline constexpr float kTagRadius = 6.f;
    // Every tag bursts inside its round: tags at 0, 3, 6, 9, 12 s, the last burst at 14 s.
    inline constexpr std::uint32_t kTagsPerRound = (kRoundMs - kTagWarnMs) / kTagEveryMs + 1;
    static_assert(kTagsPerRound == 5, "five tags a round (ST TC2)");
    static_assert((kTagsPerRound - 1) * kTagEveryMs + kTagWarnMs <= kRoundMs, "the last burst lands in the round");
    inline constexpr std::int32_t kFrozenSlowPct = 70;
    inline constexpr float kFrozenTickPct = 2.f;
    inline constexpr std::uint32_t kFrozenMs = 16000;           // the aura outlasts a round; the script removes it
    static_assert(kFrozenMs > kRoundMs, "Frozen never falls off before the round's end");
    inline constexpr float kThawRadius = 3.f;
    inline constexpr std::uint32_t kThawTickMs = 250;
    inline constexpr float kShatterPct = 30.f;

    // TC6 Patty Cake: a 4 s channel, a clap a second over the whole square; 10% (heroic 20%, expected to be kicked).
    inline constexpr std::uint32_t kPattyCakeMs = 4000;
    inline constexpr std::uint32_t kClapEveryMs = 1000;
    inline constexpr std::uint32_t kClaps = kPattyCakeMs / kClapEveryMs;
    static_assert(kClaps == 4, "four claps (ST TC6)");
    inline constexpr NH<float> kClapPct{ 10.f, 20.f };

    // TC7 Guess Who: 3 playmates at 5,000 (heroic 4 at 7,000: the heroic template's health); they burst up with his
    // emerge emote and fight after it.
    inline constexpr NH<std::uint32_t> kPlaymates{ 3, 4 };
    inline constexpr NH<std::uint32_t> kPlaymateHealth{ 5000, 7000 };
    inline constexpr std::uint32_t kPlaymateEmergeMs = 2500;
    inline constexpr std::uint32_t kPlaymateFocusMs = 1000;
    inline constexpr std::uint32_t kPlaymateCap = 16;          // safety valve against a wipe loop (ST has no cap)

    // TC8 / TC9 Jump Rope: three 2 s skips back to back; at each cast's end the rope sweeps the square and trips
    // everyone on the ground for 25% + Weakened and a 1 s knockdown (the registry's Jump kind, Stratholme X3).
    inline constexpr std::uint32_t kSkipMs = 2000;
    inline constexpr std::uint32_t kFastSkipMs = 1500;
    inline constexpr std::array<std::uint32_t, 3> kSkips{ { kSkipMs, kSkipMs, kSkipMs } };
    inline constexpr std::array<std::uint32_t, 5> kDoubleDutchSkips{ { kSkipMs, kSkipMs, kFastSkipMs, kFastSkipMs,
        kFastSkipMs } };
    inline constexpr float kTripPct = 25.f;
    inline constexpr std::uint32_t kTrippedMs = 1000;
    // The rope sweeps the whole square: the arena circle (StratholmeRework TimmyArena, r 52 round (3668, -3176)).
    inline constexpr float kRopeRadius = 52.f;
    // The square's floor runs from z 126.3 (its middle) to 130.7 (his spawn corner); the sweep's height band covers
    // the arena's z band 126..136.
    inline constexpr float kRopeZ = 128.f;
    inline constexpr float kRopeZTolerance = 8.f;
    // The heroic fallback (ST: "if two games at once doesn't carry heroic in playtest"): off until the designer calls
    // it; `.dbtest strat timmy rope 1` plays it on demand.
    inline constexpr bool kHeroicDoubleDutch = false;

    // TC10 the stock kit: Ravenous Claw 17470 every 10 to 15 s, Enrage 8599 once at 50%.
    inline constexpr std::uint32_t kClawMinMs = 10000;
    inline constexpr std::uint32_t kClawMaxMs = 15000;
    inline constexpr float kEnrageAtPct = 50.f;

    // ----------------------------------------------------------------------------------------------------------------
    // TC1 Playtime
    // ----------------------------------------------------------------------------------------------------------------

    struct SlotGames
    {
        std::array<Game, 2> games{ { Game::GuessWho, Game::GuessWho } };
        std::uint8_t count = 0;
    };

    // Normal: one game a slot, Guess Who, Jump Rope, Patty Cake, around again. Heroic: two at once, rotating pairs
    // Guess Who + Jump Rope, Patty Cake + Guess Who, Jump Rope + Patty Cake.
    inline constexpr SlotGames GamesOfSlot(std::uint32_t slot, bool heroic)
    {
        SlotGames out;
        if (!heroic)
        {
            constexpr std::array<Game, 3> rotation{ { Game::GuessWho, Game::JumpRope, Game::PattyCake } };
            out.games[0] = rotation[slot % 3];
            out.count = 1;
            return out;
        }
        constexpr std::array<std::array<Game, 2>, 3> pairs{ { { { Game::GuessWho, Game::JumpRope } },
            { { Game::PattyCake, Game::GuessWho } }, { { Game::JumpRope, Game::PattyCake } } } };
        out.games = pairs[slot % 3];
        out.count = 2;
        return out;
    }

    inline constexpr bool IsCast(Game game)
    {
        return game != Game::GuessWho;
    }

    inline constexpr bool HasGame(SlotGames const& slot, Game game)
    {
        for (std::uint8_t i = 0; i < slot.count; ++i)
            if (slot.games[i] == game)
                return true;
        return false;
    }

    // The slot's casting games in the order he plays them: one cast at a time, so a pair of casts (heroic Jump Rope
    // + Patty Cake) plays back to back, Patty Cake first (a kick ends it early). Guess Who is not a cast.
    inline std::vector<Game> CastOrder(SlotGames const& slot)
    {
        std::vector<Game> out;
        if (HasGame(slot, Game::PattyCake))
            out.push_back(Game::PattyCake);
        if (HasGame(slot, Game::JumpRope))
            out.push_back(Game::JumpRope);
        return out;
    }

    // The fight's timers, on the AI's own clock (never the boss's scheduler, which a cast bar pauses).
    class Playtime
    {
    public:
        struct Event
        {
            enum class Kind : std::uint8_t
            {
                FreezeTag,
                Slot,
            };

            Kind kind = Kind::FreezeTag;
            std::uint32_t index = 0;        // the round's or the slot's number, from 0
            std::uint64_t at = 0;           // when it was due
        };

        void Reset()
        {
            _nextRound = kFreezeFirstMs;
            _nextSlot = kSlotFirstMs;
            _rounds = 0;
            _slots = 0;
        }

        // The rounds and slots due by `now`, in time order (a round and a slot due together: the round first).
        std::vector<Event> Advance(std::uint64_t now)
        {
            std::vector<Event> out;
            while (_nextRound <= now || _nextSlot <= now)
            {
                if (_nextRound <= _nextSlot)
                {
                    out.push_back({ Event::Kind::FreezeTag, _rounds++, _nextRound });
                    _nextRound += kFreezeEveryMs;
                }
                else
                {
                    out.push_back({ Event::Kind::Slot, _slots++, _nextSlot });
                    _nextSlot += kSlotEveryMs;
                }
            }
            return out;
        }

        std::uint64_t NextRoundAt() const { return _nextRound; }
        std::uint64_t NextSlotAt() const { return _nextSlot; }
        std::uint32_t Rounds() const { return _rounds; }
        std::uint32_t Slots() const { return _slots; }

    private:
        std::uint64_t _nextRound = kFreezeFirstMs;
        std::uint64_t _nextSlot = kSlotFirstMs;
        std::uint32_t _rounds = 0;
        std::uint32_t _slots = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // TC2-TC5 Freeze Tag
    // ----------------------------------------------------------------------------------------------------------------

    class FreezeRound
    {
    public:
        void Begin(std::uint64_t now)
        {
            _active = true;
            _start = now;
            _tags = 0;
        }

        void End() { _active = false; }
        bool Active() const { return _active; }
        std::uint64_t StartedAt() const { return _start; }
        std::uint64_t EndsAt() const { return _start + kRoundMs; }
        std::uint32_t Tags() const { return _tags; }

        // True once per tag: at the round's start and every 3 s after, five times.
        bool TagDue(std::uint64_t now)
        {
            if (!_active || _tags >= kTagsPerRound || now < _start + std::uint64_t(_tags) * kTagEveryMs)
                return false;
            ++_tags;
            return true;
        }

        // Gotcha: the round's 15 s ran out, or everyone in the fight is frozen at once.
        bool Over(std::uint64_t now, std::uint32_t alive, std::uint32_t frozen) const
        {
            if (!_active)
                return false;
            return now >= EndsAt() || (alive > 0 && frozen >= alive);
        }

    private:
        bool _active = false;
        std::uint64_t _start = 0;
        std::uint32_t _tags = 0;
    };

    struct TagCandidate
    {
        std::uint64_t id = 0;
        bool frozen = false;
    };

    // TC2: a random candidate who is not frozen (the tank too); nullopt when everyone is. `rand(n)` returns [0, n).
    template <class Rand>
    std::optional<std::uint64_t> PickTag(std::vector<TagCandidate> const& candidates, Rand&& rand)
    {
        std::vector<std::uint64_t> pool;
        for (TagCandidate const& c : candidates)
            if (!c.frozen)
                pool.push_back(c.id);
        if (pool.empty())
            return std::nullopt;
        std::size_t const i = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool.size())));
        return pool[i < pool.size() ? i : pool.size() - 1];
    }

    // TC3: who a burst freezes: the tagged player (when still there) and every player its circle caught, once each.
    inline std::vector<std::uint64_t> BurstVictims(std::optional<std::uint64_t> tagged,
        std::vector<std::uint64_t> const& inside)
    {
        std::vector<std::uint64_t> out;
        if (tagged)
            out.push_back(*tagged);
        for (std::uint64_t id : inside)
        {
            bool seen = false;
            for (std::uint64_t o : out)
                seen = seen || o == id;
            if (!seen)
                out.push_back(id);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC7 Guess Who
    // ----------------------------------------------------------------------------------------------------------------

    // Where they burst up: the measured spots at the square's edges (T3, T4, T8; heroic adds T5).
    inline std::vector<Vec2> PlaymateSpots(bool heroic)
    {
        std::vector<Vec2> out(StratholmeRework::kTimmyBursts.begin(), StratholmeRework::kTimmyBursts.end());
        if (heroic)
            out.push_back(StratholmeRework::kTimmyHeroicBurst);
        return out;
    }

    // How many burst up now (the cap keeps a long wipe loop bounded).
    inline constexpr std::uint32_t PlaymatesToSummon(bool heroic, std::uint32_t alive)
    {
        std::uint32_t const want = kPlaymates(heroic);
        if (alive >= kPlaymateCap)
            return 0;
        return want < kPlaymateCap - alive ? want : kPlaymateCap - alive;
    }

    struct FocusCandidate
    {
        std::uint64_t id = 0;
        bool frozen = false;
        float distance = 0.f;
    };

    // TC7: a playmate goes for the nearest frozen player; nullopt when nobody is frozen (it keeps its victim, or the
    // caller picks a random player).
    inline std::optional<std::uint64_t> PlaymateFocus(std::vector<FocusCandidate> const& candidates)
    {
        std::optional<std::uint64_t> best;
        float bestDist = 0.f;
        for (FocusCandidate const& c : candidates)
            if (c.frozen && (!best || c.distance < bestDist))
            {
                best = c.id;
                bestDist = c.distance;
            }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TC8 Jump Rope
    // ----------------------------------------------------------------------------------------------------------------

    // The skips' cast times, in order.
    inline std::vector<std::uint32_t> SkipsOf(bool doubleDutch)
    {
        if (doubleDutch)
            return std::vector<std::uint32_t>(kDoubleDutchSkips.begin(), kDoubleDutchSkips.end());
        return std::vector<std::uint32_t>(kSkips.begin(), kSkips.end());
    }

    inline std::uint32_t RopeMs(bool doubleDutch)
    {
        std::uint32_t total = 0;
        for (std::uint32_t ms : SkipsOf(doubleDutch))
            total += ms;
        return total;
    }

    // The cast spell of a skip of `ms` (the DBC holds the cast time: 2 s or 1.5 s).
    inline constexpr std::uint32_t SkipSpell(std::uint32_t ms)
    {
        return ms == kFastSkipMs ? SPELL_TC_JUMP_ROPE_FAST : SPELL_TC_JUMP_ROPE;
    }

    // The heroic pair Jump Rope + Patty Cake plays back to back and must fit its 15 s slot, Double Dutch included.
    static_assert(kPattyCakeMs + 2 * kSkipMs + 3 * kFastSkipMs < kSlotEveryMs, "a slot holds Patty Cake + the rope");
}

#endif
