/*
 * mod-dungeon-bosses, Ragefire Chasm D4: Taragaman the Hungerer (11520), the pure, host-testable part (no engine
 * headers; tests/rfc_taragaman_test.cpp). The numbers of the build spec are RagefireChasmRework::Taragaman (`Tune`
 * below): nothing here restates one. What is here is what the spec does not set (the leaps' flight, the backstops, the
 * floor probe) and the rules:
 *
 *   Timeline        the three beats (Felstorm, Searing Nova, Feast): one at a time, the one due longest first; a Feast
 *                   waits kFeastAfterSetPieceMs after a set piece (TG1, section 3.5 rule 24)
 *   PickPrey        the player with the lowest health percent among the eligible ones, ties at random
 *   Gorges          whether the landing Gorges him; DamageMult what his Gorged stacks do to every percent hit of his
 *   PickSpikes      three of the four points at random, or an opposite pair (heroic, hard mode)
 *   SpotRotation    the fel spots' shuffled rotation of the players
 *   ReachArena, EdgeSpot   his arena and the rim band he reaches from its edge
 *   LeapLanding, LeapMs, the Felstorm's tick arithmetic
 */

#ifndef MOD_DUNGEON_BOSSES_RFC_TARAGAMAN_LOGIC_H
#define MOD_DUNGEON_BOSSES_RFC_TARAGAMAN_LOGIC_H

#include "RagefireChasmRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <vector>

namespace RfcTaragaman
{
    namespace Tune = RagefireChasmRework::Taragaman;
    using RagefireChasmRework::Mode;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (RagefireChasmRework.h; ids.yaml reservation `ragefire_chasm`).
    inline constexpr RagefireChasmRework::IdSlice kSpellSlice = RagefireChasmRework::kSpellsTaragaman;

    // Declared in apps/dbc-tools source/npcs/ragefire_chasm/taragaman.py (the same ids, tested). 213669-213689 spare.
    enum TaragamanSpells : std::uint32_t
    {
        SPELL_TG_FEAST_MARK     = kSpellSlice.first + 0,    // 213650 TG1 the 3 s (hard mode 2 s) mark on the prey
        SPELL_TG_LEAP_LOOK      = kSpellSlice.first + 1,    // 213651 a leap's look, at the start and at the landing
        SPELL_TG_BITE           = kSpellSlice.first + 2,    // 213652 TG1 the bite (the script's base point)
        SPELL_TG_GORGED         = kSpellSlice.first + 3,    // 213653 his +10% damage dealt per stack
        SPELL_TG_GORGE_HEAL     = kSpellSlice.first + 4,    // 213654 the Gorge's heal (the script's base point)
        SPELL_TG_DEVOUR         = kSpellSlice.first + 5,    // 213655 TG2 the 5 s kickable channel (Shadow: rule 25)
        SPELL_TG_DEVOUR_TICK    = kSpellSlice.first + 6,    // 213656 TG2 its tick (Physical, the script's base point)
        SPELL_TG_DEVOUR_HEAL    = kSpellSlice.first + 7,    // 213657 TG2 his heal per tick
        SPELL_TG_FELSTORM_CAST  = kSpellSlice.first + 8,    // 213658 TG3 the 2 s bar (Fire)
        SPELL_TG_FELSTORM_SPIN  = kSpellSlice.first + 9,    // 213659 TG3 the spin's look, an aura on him
        SPELL_TG_FELSTORM       = kSpellSlice.first + 10,   // 213660 TG3 the ring's tick (resolve copy, Physical)
        SPELL_TG_FEL_PULSE      = kSpellSlice.first + 11,   // 213661 TG4 a pulse on one player (base point)
        SPELL_TG_FEL_SPOT       = kSpellSlice.first + 12,   // 213662 TG5 a spot's hit (resolve copy, Fire)
        SPELL_TG_FEL_SPOT_LOOK  = kSpellSlice.first + 13,   // 213663 TG5 its eruption, the spot's stalker on itself
        SPELL_TG_SPIKE_LOOK     = kSpellSlice.first + 14,   // 213664 TG6 a spike rises: the rock burst at its point
        SPELL_TG_SPIKE_DIRT     = kSpellSlice.first + 15,   // 213665 TG6 and the dirt under it
        SPELL_TG_NOVA_CAST      = kSpellSlice.first + 16,   // 213666 TG6 the 4 s bar (Fire)
        SPELL_TG_NOVA_CAST_HM   = kSpellSlice.first + 17,   // 213667 TG6 the hard mode's 3 s bar
        SPELL_TG_NOVA           = kSpellSlice.first + 18,   // 213668 TG6 the Nova's hit (resolve copy, Fire)
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_TG_NOVA;
    static_assert(kLastSpell <= kSpellSlice.last, "Taragaman's spells stay in the D4 slice");

    // Registry tags: BM's drill `ragefire-chasm-shapes` rows felstorm-spots and spike-hide use the same ones (rule 34).
    enum TaragamanTags : std::uint32_t
    {
        TAG_TG_RING         = 10,       // TG3
        TAG_TG_SPOT         = 11,       // TG5
        TAG_TG_NOVA         = 12,       // TG6 normal
        TAG_TG_NOVA_PAIR    = 13,       // TG6 heroic and hard mode (two spikes)
    };

    constexpr std::uint32_t NovaTag(Mode mode)
    {
        return mode == Mode::Normal ? TAG_TG_NOVA : TAG_TG_NOVA_PAIR;
    }

    constexpr std::uint32_t NovaBarSpell(Mode mode)
    {
        return mode == Mode::HardMode ? SPELL_TG_NOVA_CAST_HM : SPELL_TG_NOVA_CAST;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // What the build spec does not set
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kLeapSpeedYd = 25.f;                    // a leap's ground speed ...
    std::uint32_t constexpr kLeapMinMs = 500;               // ... over this long at least
    std::uint32_t constexpr kLeapMaxMs = 1600;              // ... and this long at most (40 yd)
    float constexpr kLeapSkipYd = 1.5f;                     // nearer than this he lands where he stands
    float constexpr kLeapShortYd = 2.f;                     // the Feast lands this far short of the prey
    std::uint32_t constexpr kLeapGraceMs = 1000;            // a spline that never reports its end
    std::uint32_t constexpr kNovaBackstopMs = 1500;         // the Nova's resolve was never seen: end it
    std::uint32_t constexpr kSpikeBackstopSec = 20;         // a spike's own despawn (the Nova's end deletes it)
    float constexpr kSpikeYaw = 0.f;                        // fixed (section 7 #19 A)
    std::uint32_t constexpr kSpotStalkerMs = 2000;          // past the eruption
    std::uint32_t constexpr kUppercutRetryMs = 500;
    // Bot interrupt priority: expected on heroic and in the hard mode (Whitemane's Heal scale: 2 a reward, 4 expected).
    std::uint8_t constexpr kDevourKickPriority = 4;

    // The plateau's floor runs z -17.7 to -23.1 (kSpikePoints, kGlobuleStarts, the arm ends at -22.5): one probe band
    // round its middle finds it from any player's height, an airborne one's too (rule 33).
    float constexpr kFloorMidZ = -20.25f;
    float constexpr kFloorBandYd = 3.25f;
    float constexpr kFloorProbeUpYd = 6.f;

    // He stays on his arena (2 yd inside every edge), but a target on the band past it is still his: he stands at his
    // edge and reaches it (RagefireChasmRework.h EdgeReachArena). Off the grown arena a target is out of his reach (the
    // bank trail, the corner of an arm end) and he turns to someone inside.
    inline DungeonKit::Arena ReachArena()
    {
        return RagefireChasmRework::EdgeReachArena(RagefireChasmRework::TaragamanArena(),
            RagefireChasmRework::kPlateauArenaPolygon, RagefireChasmRework::kPlateauZMin,
            RagefireChasmRework::kPlateauZMax, [](std::size_t) { return std::optional<float>(); });
    }

    // Where on his arena he stands for a target at `p`: strictly inside it.
    inline Vec2 EdgeSpot(Vec2 p)
    {
        return RagefireChasmRework::StandSpot(RagefireChasmRework::kPlateauArenaPolygon, p);
    }

    constexpr bool OnFloorBand(float z)
    {
        return z >= kFloorMidZ - kFloorBandYd && z <= kFloorMidZ + kFloorBandYd;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG3 to TG5: the Felstorm's arithmetic
    // ----------------------------------------------------------------------------------------------------------------

    // The ring's passes: the first when the cast ends, then one per tick while he spins.
    constexpr std::uint32_t RingTicks(Mode mode)
    {
        return Tune::kFelstormSpinMs(mode) / Tune::kFelstormTickMs;
    }

    // Fel pulses per spin: one per tick, the first a tick after the spin starts (none on normal).
    constexpr std::uint32_t PulseCount(Mode mode)
    {
        return Tune::kPulsePct(mode) > 0.f ? Tune::kFelstormSpinMs(mode) / Tune::kFelstormTickMs : 0;
    }

    constexpr std::uint32_t SpotCount(Mode mode)
    {
        return Tune::kSpotPct(mode) > 0.f ? Tune::kSpotCount : 0;
    }

    // From the spin's start: when spot `index` is marked, and when the last one has erupted.
    constexpr std::uint32_t SpotAtMs(std::uint32_t index)
    {
        return index * Tune::kSpotEveryMs;
    }

    constexpr std::uint32_t LastSpotMs(Mode mode)
    {
        std::uint32_t const count = SpotCount(mode);
        return count ? SpotAtMs(count - 1) + Tune::kSpotWarnMs(mode) : 0;
    }

    // From the spin's start to the end of the set piece: the spin, then the last spots still on the floor. The Feast's
    // 4 s count from here (STAGE-G1, felstorm-spots).
    constexpr std::uint32_t FelstormOverMs(Mode mode)
    {
        return std::max(Tune::kFelstormSpinMs(mode), LastSpotMs(mode));
    }

    // The fel spots' rotation (TG5): the players in a shuffled order, the same order round and round for one spin, so
    // ten spots are two each for five players. Keys are raw guids; the rotation skips who is no longer eligible.
    class SpotRotation
    {
    public:
        void Clear()
        {
            _order.clear();
            _next = 0;
        }

        // `rand(n)`: uniform in [0, n).
        template <typename Rand>
        void Shuffle(std::vector<std::uint64_t> players, Rand&& rand)
        {
            _order = std::move(players);
            _next = 0;
            for (std::size_t i = _order.size(); i > 1; --i)
                std::swap(_order[i - 1], _order[rand(static_cast<std::uint32_t>(i))]);
        }

        bool Empty() const { return _order.empty(); }

        // The next player of the rotation that `eligible(key)` accepts; nullopt: none.
        template <typename Eligible>
        std::optional<std::uint64_t> Next(Eligible&& eligible)
        {
            for (std::size_t tries = 0; tries < _order.size(); ++tries)
            {
                std::uint64_t const key = _order[_next];
                _next = (_next + 1) % _order.size();
                if (eligible(key))
                    return key;
            }
            return std::nullopt;
        }

    private:
        std::vector<std::uint64_t> _order;
        std::size_t _next = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // TG1 Feast, TG2 Devour
    // ----------------------------------------------------------------------------------------------------------------

    // Who the Feast may mark (section 7 #24 A, #30 A): alive, on the plateau's floor, within 40 yd of the hub.
    constexpr bool PreyEligible(bool alive, bool onPlateau, float hubDistance)
    {
        return alive && onPlateau && hubDistance <= Tune::kFeastRangeYd;
    }

    // The index of the lowest health percent among the candidates (all eligible), ties at random; nullopt: none.
    template <typename Rand>
    std::optional<std::size_t> PickPrey(std::span<float const> healthPct, Rand&& rand)
    {
        std::vector<std::size_t> lowest;
        for (std::size_t i = 0; i < healthPct.size(); ++i)
        {
            if (!lowest.empty() && healthPct[i] > healthPct[lowest.front()])
                continue;
            if (!lowest.empty() && healthPct[i] < healthPct[lowest.front()])
                lowest.clear();
            lowest.push_back(i);
        }
        if (lowest.empty())
            return std::nullopt;
        return lowest[rand(static_cast<std::uint32_t>(lowest.size()))];
    }

    // The prey's health when he lands, before the bite.
    constexpr bool Gorges(float healthPct)
    {
        return healthPct < Tune::kGorgeBelowPct;
    }

    // Gorged: +10% damage dealt per stack. The aura raises his melee and Uppercut; his percent hits ignore caster
    // modifiers (rule 2), so the script raises them by the same factor.
    constexpr float DamageMult(std::uint32_t stacks)
    {
        return 1.f + Tune::kGorgedPct / 100.f * static_cast<float>(stacks);
    }

    constexpr bool HasDevour(Mode mode)
    {
        return Tune::kDevourTickPct(mode) > 0.f;
    }

    // The interrupt list's `every`: the hard mode's Devours come as close as its Feasts may (6 s).
    constexpr std::uint32_t DevourInterruptEveryMs(Mode mode)
    {
        return mode == Mode::HardMode ? Tune::kStarvingGapMs : Tune::kDevourInterruptEveryMs;
    }

    // `pct` percent of `maxHealth`, rounded down.
    constexpr std::uint32_t PctOfHealth(std::uint32_t maxHealth, float pct)
    {
        return static_cast<std::uint32_t>(static_cast<double>(maxHealth) * static_cast<double>(pct) / 100.0);
    }

    // A leap over `distance` takes this long.
    inline std::uint32_t LeapMs(float distance)
    {
        float const ms = distance / kLeapSpeedYd * 1000.f;
        return std::clamp(static_cast<std::uint32_t>(std::max(0.f, ms)), kLeapMinMs, kLeapMaxMs);
    }

    // Where the Feast lands (section 7 #24 A): kLeapShortYd short of the prey on his side of it, kept on the arena (2
    // yd inside every true edge), so a prey at a rim or on an arm end never draws him over the lava.
    inline Vec2 LeapLanding(Vec2 from, Vec2 prey)
    {
        float const distance = DungeonKit::Distance(from, prey);
        Vec2 const p = DungeonKit::Advance(prey, DungeonKit::BearingTo(prey, from),
            std::min(distance, kLeapShortYd));
        return EdgeSpot(p);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // TG6 Searing Nova
    // ----------------------------------------------------------------------------------------------------------------

    // The spike points of one Nova. Normal: three of the four at random. Heroic and hard mode: an opposite pair, the x
    // arms or the y arms (STAGE-G1 Q1, handoff section 10), so everyone within 18 yd reaches a spike in a 4 s cast.
    // `rand(n)`: uniform in [0, n).
    template <typename Rand>
    std::vector<std::size_t> PickSpikes(std::uint32_t count, Rand&& rand)
    {
        using namespace RagefireChasmRework;
        if (count == 2)
            return rand(2) == 0 ? std::vector<std::size_t>{ SPIKE_PLUS_X, SPIKE_MINUS_X }
                : std::vector<std::size_t>{ SPIKE_PLUS_Y, SPIKE_MINUS_Y };
        std::vector<std::size_t> points{ SPIKE_PLUS_X, SPIKE_MINUS_X, SPIKE_PLUS_Y, SPIKE_MINUS_Y };
        while (points.size() > count)
            points.erase(points.begin() + rand(static_cast<std::uint32_t>(points.size())));
        return points;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The timeline
    // ----------------------------------------------------------------------------------------------------------------
    enum class Beat : std::uint8_t
    {
        Felstorm,
        Nova,
        Feast,
    };
    std::size_t constexpr kBeatCount = 3;

    // The three beats, never two at once ("No two of the three run at once"). What is due longest goes first, so no
    // beat can push another back for good (rule 24, RB-17): a Feast that waits out its 4 s after a set piece also holds
    // a set piece that came due after it. Each beat keeps its own pace from the time it was due, a late one starting
    // again no sooner than half a period later. The fight's timers start at the pull and never pause for a cast bar.
    class Timeline
    {
    public:
        void Start(Mode mode, std::uint64_t now)
        {
            *this = Timeline{};
            _mode = mode;
            _on = true;
            for (std::size_t i = 0; i < kBeatCount; ++i)
                _due[i] = now + FirstMs(static_cast<Beat>(i));
        }

        void Stop() { *this = Timeline{}; }
        bool On() const { return _on; }
        Mode GetMode() const { return _mode; }
        void SetMode(Mode mode) { _mode = mode; }       // GM tests

        std::optional<Beat> Running() const { return _running; }
        bool SetPieceRunning() const { return _running && *_running != Beat::Feast; }
        std::uint64_t DueMs(Beat beat) const { return _due[Index(beat)]; }
        std::uint64_t FeastHoldUntilMs() const { return _feastHoldUntil; }
        bool Held() const { return _held; }
        // The hold after a set piece (kFeastAfterSetPieceMs until set; Start puts it back).
        void SetFeastHold(std::uint32_t ms) { _feastHoldMs = ms; }
        std::uint32_t FeastHoldMs() const { return _feastHoldMs; }

        // Whether `beat` may start at all now (a script's or the hard mode's own start included).
        bool MayStart(Beat beat, std::uint64_t now) const
        {
            return _on && !_running && (beat != Beat::Feast || now >= _feastHoldUntil);
        }

        // Whether a set piece of these timers is due and would start now: a Feast the hard mode's poll asks for waits
        // for it (rule 24; the set piece came due during the last Feast).
        bool SetPieceDue(std::uint64_t now) const
        {
            return Next(now, false).has_value();
        }

        // The beat to start now by its timer. `feastByTimer` false: the hard mode starts the Feasts itself.
        std::optional<Beat> Next(std::uint64_t now, bool feastByTimer) const
        {
            if (!_on || _running)
                return std::nullopt;
            std::optional<Beat> oldest;
            for (std::size_t i = 0; i < kBeatCount; ++i)
            {
                Beat const beat = static_cast<Beat>(i);
                if (_due[i] > now || (beat == Beat::Feast ? !feastByTimer : _held))
                    continue;
                if (!oldest || _due[i] < _due[Index(*oldest)])
                    oldest = beat;
            }
            if (oldest && !MayStart(*oldest, now))
                return std::nullopt;
            return oldest;
        }

        void Fired(Beat beat, std::uint64_t now)
        {
            _running = beat;
            Advance(beat, now);
        }

        // A due beat with nothing to do (a Feast with no prey): its next time.
        void Skip(Beat beat, std::uint64_t now)
        {
            Advance(beat, now);
        }

        // The running beat is over.
        void Ended(std::uint64_t now)
        {
            if (SetPieceRunning())
                _feastHoldUntil = std::max(_feastHoldUntil, now + _feastHoldMs);
            _running.reset();
        }

        // Section 7 #30 A: no Feast in a phase's first 2 s.
        void PhaseChanged(std::uint64_t now)
        {
            _feastHoldUntil = std::max(_feastHoldUntil, now + Tune::kFeastAfterPhaseMs);
        }

        // Phase 2 (hard mode): the Felstorm's and the Nova's own timers stop while held.
        void HoldSetPieces(bool hold, std::uint64_t now)
        {
            if (hold == _held)
                return;
            _held = hold;
            if (hold)
            {
                _heldAt = now;
                return;
            }
            for (Beat const beat : { Beat::Felstorm, Beat::Nova })
                _due[Index(beat)] += now - _heldAt;
        }

        std::uint32_t FirstMs(Beat beat) const
        {
            return beat == Beat::Felstorm ? Tune::kFelstormFirstMs(_mode)
                : beat == Beat::Nova ? Tune::kNovaFirstMs(_mode) : Tune::kFeastFirstMs(_mode);
        }

        std::uint32_t EveryMs(Beat beat) const
        {
            return beat == Beat::Felstorm ? Tune::kFelstormEveryMs(_mode)
                : beat == Beat::Nova ? Tune::kNovaEveryMs(_mode) : Tune::kFeastEveryMs(_mode);
        }

    private:
        static constexpr std::size_t Index(Beat beat) { return static_cast<std::size_t>(beat); }

        void Advance(Beat beat, std::uint64_t now)
        {
            std::uint64_t& due = _due[Index(beat)];
            std::uint32_t const every = EveryMs(beat);
            // Started early (a GM test, the hard mode): from now. Late: its own pace, half a period away at least, so
            // a long delay never chains two of the same beat and never piles up missed ones.
            due = due > now ? now + every : std::max<std::uint64_t>(due + every, now + every / 2);
        }

        Mode _mode = Mode::Normal;
        bool _on = false;
        bool _held = false;
        std::array<std::uint64_t, kBeatCount> _due{};
        std::optional<Beat> _running;
        std::uint64_t _feastHoldUntil = 0;
        std::uint32_t _feastHoldMs = Tune::kFeastAfterSetPieceMs;
        std::uint64_t _heldAt = 0;
    };
}

#endif
