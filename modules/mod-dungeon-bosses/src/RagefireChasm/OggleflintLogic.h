/*
 * mod-dungeon-bosses, Ragefire Chasm D1:
 * Oggleflint, the pure, host-testable part (no engine headers): spell ids, registry tags, the timeline (which beat may
 * start when), the Borer count, the target picks, the Beating's chain. The numbers of the build spec are
 * RagefireChasmRework::Oggleflint (`Tune` below) and are never restated here; a constant of this file is one the spec
 * leaves open. Tested by tests/rfc_oggleflint_test.cpp.
 */

#ifndef MOD_DUNGEON_BOSSES_RFC_OGGLEFLINT_LOGIC_H
#define MOD_DUNGEON_BOSSES_RFC_OGGLEFLINT_LOGIC_H

#include "RagefireChasmRework.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace RfcOggleflint
{
    namespace Tune = RagefireChasmRework::Oggleflint;

    // Every spell of this WP sits in this slice (RagefireChasmRework.h; ids.yaml reservation `ragefire_chasm`).
    inline constexpr RagefireChasmRework::IdSlice kSpellSlice = RagefireChasmRework::kSpellsOggleflint;

    // apps/dbc-tools source/npcs/ragefire_chasm/oggleflint.py declares each.
    enum OggleflintSpells : std::uint32_t
    {
        SPELL_OG_ERUPTION           = kSpellSlice.first + 0,    // OG2 resolve copy
        SPELL_OG_ERUPTION_LOOK      = kSpellSlice.first + 1,    // OG2 the dirt burst, cast by the Borer at its spot
        SPELL_OG_TUNNEL             = kSpellSlice.first + 2,    // OG1 the Borer's trail (state aura on itself)
        SPELL_OG_SWING_BAR          = kSpellSlice.first + 3,    // OG3 the 2 s wind-up bar
        SPELL_OG_SWING              = kSpellSlice.first + 4,    // OG3 resolve copy (everyone but the tank)
        SPELL_OG_SWING_TANK         = kSpellSlice.first + 5,    // OG3 the tank's hit
        SPELL_OG_SWING_LOOK         = kSpellSlice.first + 6,    // OG3 the arc when no tank stands in the cone
        SPELL_OG_BLOW               = kSpellSlice.first + 7,    // OG4 resolve copy
    };
    static_assert(SPELL_OG_BLOW <= kSpellSlice.last);

    // Registry tags. 1 to 3 are the drill's (mod-boss-mechanics MechanicDrill.h kRfcTagChase, kRfcTagErupt,
    // kRfcTagBlow: rows borer-den and beating-chain); the swing is not drilled: the first tag past the drill's.
    enum OggleflintTags : std::uint32_t
    {
        TAG_OG_CHASE    = 1,
        TAG_OG_ERUPTION = 2,
        TAG_OG_BLOW     = 3,
        TAG_OG_SWING    = 18,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Values the build spec leaves open
    // ----------------------------------------------------------------------------------------------------------------
    // OG1: the chase circle arms this long after the summon and stands for the rest of the Borer's life, so it ends
    // with the chase (the drill's kMoundArmMs).
    std::uint32_t constexpr kChaseArmMs = 500;
    std::uint32_t constexpr kChaseStandsMs = Tune::kChaseMs - kChaseArmMs;
    static_assert(kChaseArmMs < Tune::kChaseMs);
    // The Borer's creature goes at the latest this long after its summon (the chase, the ring, the worm's moment).
    std::uint32_t constexpr kBorerLifeMs = 12000;
    static_assert(kBorerLifeMs > Tune::kChaseMs + Tune::kEruptionWarnMs);

    // OG2: the throw, straight up (speed up, yd/s; no sideways speed).
    float constexpr kKnockUpSpeedZ = 10.f;
    float constexpr kGravity = 19.29110527038574f;                  // Movement::gravity
    constexpr float KnockUpPeakYd(float speedZ) { return speedZ * speedZ / (2.f * kGravity); }
    constexpr float KnockUpAirSec(float speedZ) { return 2.f * speedZ / kGravity; }
    // The worm: display 11010 at this scale for a moment, then it sinks again (_visuals.py DISPLAY_BORER_ERUPT,
    // BORER_ERUPT_SCALE_RANGE).
    std::uint32_t constexpr kWormDisplay = 11010;
    float constexpr kWormScale = 0.6f;
    std::uint32_t constexpr kWormMs = 1500;

    // OG4: he glares, then takes off this long before the blow lands.
    std::uint32_t constexpr kLeapMs = 800;
    static_assert(kLeapMs < Tune::kBeatingBlowMs);
    float constexpr kLeapMinYd = 0.5f;              // already on the spot: no leap
    // A blow that never came back from the registry ends the Beating this long after its time.
    std::uint32_t constexpr kBlowGraceMs = 1000;
    // OG3: no swing starts until he has been back on his target this long (a swing never opens on the player he just
    // beat).
    std::uint32_t constexpr kSwingAfterBeatingMs = 1500;
    // A swing's cone has landed this long after its wind-up for sure (the registry's tick is not the AI's).
    std::uint32_t constexpr kSwingTailMs = 250;

    // The leap's speed over the floor: it lands `flightMs` after the take-off.
    constexpr float LeapSpeedXY(float distYd, std::uint32_t flightMs)
    {
        float const ms = static_cast<float>(std::max<std::uint32_t>(1, flightMs));
        return std::max(1.f, distYd * 1000.f / ms);
    }

    // The Beating's total length.
    std::uint32_t constexpr kBeatingMs = Tune::kBeatingBlows * Tune::kBeatingBlowMs;

    // ----------------------------------------------------------------------------------------------------------------
    // Timeline
    // ----------------------------------------------------------------------------------------------------------------
    // A beat on a fixed grid: the next one is `everyMs` after this one's due time, never in the past (a wait never
    // shifts the rhythm).
    class BeatClock
    {
    public:
        void Start(std::uint32_t firstMs, std::uint32_t everyMs)
        {
            _on = true;
            _dueMs = firstMs;
            _everyMs = everyMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }
        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        void Fired(std::uint64_t nowMs)
        {
            _dueMs += _everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + _everyMs;
        }

    private:
        bool _on = false;
        std::uint32_t _everyMs = 0;
        std::uint64_t _dueMs = 0;
    };

    // Which beat may start (times in ms since the pull). The rules:
    //   - a hunt and a swing never start within Tune::kHuntSwingGapMs of each other (the later one waits);
    //   - no swing while the Beating runs or for kSwingAfterBeatingMs after it; no Beating while a swing winds up (it
    //     waits: rule 24, host-tested that no beat starves); hunts and the Beating run side by side;
    //   - heroic only: the Beating, and a Borer mark every Tune::kExtraBorerEveryMs.
    class Timeline
    {
    public:
        void Start(bool heroic)
        {
            *this = Timeline();
            _on = true;
            _swing.Start(Tune::kSwingFirstMs(heroic), Tune::kSwingEveryMs(heroic));
            _hunt.Start(Tune::kHuntFirstMs(heroic), Tune::kHuntEveryMs(heroic));
            if (heroic)
            {
                _beating.Start(Tune::kBeatingFirstMs, Tune::kBeatingEveryMs);
                _join.Start(Tune::kExtraBorerEveryMs, Tune::kExtraBorerEveryMs);
            }
        }

        void Stop() { *this = Timeline(); }
        bool On() const { return _on; }

        bool HuntMayStart(std::uint64_t nowMs) const { return _hunt.Due(nowMs) && GapOver(_lastSwingMs, nowMs); }

        bool SwingMayStart(std::uint64_t nowMs) const
        {
            return _swing.Due(nowMs) && GapOver(_lastHuntMs, nowMs) && !_beatingOn && nowMs >= _swingFreeMs
                && !SwingWindingUp(nowMs);
        }

        bool BeatingMayStart(std::uint64_t nowMs) const
        {
            return _beating.Due(nowMs) && !_beatingOn && !SwingWindingUp(nowMs);
        }

        bool BorerMark(std::uint64_t nowMs) const { return _join.Due(nowMs); }

        bool SwingWindingUp(std::uint64_t nowMs) const
        {
            return _lastSwingMs != kNever && nowMs < _lastSwingMs + Tune::kSwingWarnMs + kSwingTailMs;
        }

        bool BeatingOn() const { return _beatingOn; }

        // `beat`: the timeline's own (it takes the grid on); a forced one (`.dbtest`) only counts for the spacing.
        void HuntStarted(std::uint64_t nowMs, bool beat = true)
        {
            _lastHuntMs = nowMs;
            if (beat)
                _hunt.Fired(nowMs);
        }

        void SwingStarted(std::uint64_t nowMs, bool beat = true)
        {
            _lastSwingMs = nowMs;
            if (beat)
                _swing.Fired(nowMs);
        }

        void BeatingBeat(std::uint64_t nowMs) { _beating.Fired(nowMs); }    // started or skipped
        void BeatingStarted() { _beatingOn = true; }

        void BeatingEnded(std::uint64_t nowMs)
        {
            _beatingOn = false;
            _swingFreeMs = nowMs + kSwingAfterBeatingMs;
        }

        void BorerMarkPassed(std::uint64_t nowMs) { _join.Fired(nowMs); }

    private:
        static std::uint64_t constexpr kNever = ~std::uint64_t(0);

        static bool GapOver(std::uint64_t otherMs, std::uint64_t nowMs)
        {
            return otherMs == kNever || nowMs >= otherMs + Tune::kHuntSwingGapMs;
        }

        BeatClock _swing;
        BeatClock _hunt;
        BeatClock _beating;
        BeatClock _join;
        std::uint64_t _lastHuntMs = kNever;
        std::uint64_t _lastSwingMs = kNever;
        std::uint64_t _swingFreeMs = 0;
        bool _beatingOn = false;
        bool _on = false;
    };

    // Ruling 15 / section 7 #28 A: at a 40 s mark a Borer joins while a player is left that neither the Borers there
    // are nor the Beating takes; else the join waits for the next mark. Nothing is removed once it joined.
    constexpr bool BorerMayJoin(std::uint32_t borers, std::uint32_t livingPlayers, bool beating)
    {
        return borers + (beating ? 1u : 0u) < livingPlayers;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------
    // Up to `count` distinct entries of `ids` in random order, none of `excluded`. `rand(n)` returns [0, n).
    template <typename Id, typename Rand>
    std::vector<Id> PickDistinctIds(std::vector<Id> const& ids, std::vector<Id> const& excluded, std::size_t count,
        Rand&& rand)
    {
        std::vector<Id> pool;
        for (Id const& id : ids)
            if (std::find(excluded.begin(), excluded.end(), id) == excluded.end())
                pool.push_back(id);
        count = std::min(count, pool.size());
        for (std::size_t i = 0; i < count; ++i)
            std::swap(pool[i], pool[i + rand(static_cast<std::uint32_t>(pool.size() - i))]);
        pool.resize(count);
        return pool;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OG4 the Beating's chain
    // ----------------------------------------------------------------------------------------------------------------
    // Blow after blow: marked at `markMs`, taken off for kLeapMs before it lands, landed kBeatingBlowMs after the mark;
    // the next is marked in the tick the last one lands (the registry's callback).
    struct BeatingChain
    {
        bool active = false;
        bool leapt = false;
        std::uint32_t blow = 0;         // 1 to kBeatingBlows: the marked one
        std::uint64_t markMs = 0;

        void Start() { *this = BeatingChain(); active = true; }
        void Stop() { *this = BeatingChain(); }

        void Marked(std::uint64_t nowMs)
        {
            ++blow;
            leapt = false;
            markMs = nowMs;
        }

        std::uint64_t LandMs() const { return markMs + Tune::kBeatingBlowMs; }
        bool LeapDue(std::uint64_t nowMs) const
        {
            return active && blow && !leapt && nowMs + kLeapMs >= LandMs();
        }
        // The flight left at `nowMs` (a late tick lands on time).
        std::uint32_t FlightMs(std::uint64_t nowMs) const
        {
            return LandMs() > nowMs ? static_cast<std::uint32_t>(LandMs() - nowMs) : 1u;
        }
        bool Last() const { return blow >= Tune::kBeatingBlows; }
        bool Overdue(std::uint64_t nowMs) const { return active && blow && nowMs >= LandMs() + kBlowGraceMs; }
    };
}

#endif
