/*
 * mod-dungeon-bosses, Zul'Farrak D1: Theka the Martyr (7272), the pure, host-testable part (no engine headers): spell
 * ids, texts, registry tags, the build spec's numbers (`namespace Tune`, section 3.5 rule 32), the timeline, the rise
 * point picks, the swarm's closing and turning rules, the stacks, the Penitent Hunt's stagger and the stack math the
 * design leans on. Tested by tests/zf_theka_test.cpp. Health is ZulFarrakRework.h Health::kTheka; the rise points,
 * the spawn and the courtyard are ZulFarrakRework.h (section 3.8, section 7 #27 A).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_THEKA_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_THEKA_LOGIC_H

#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace ZfTheka
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsTheka;

    // apps/dbc-tools source/npcs/zul_farrak/theka.py declares each (lib/test_zul_farrak_theka.py pins the offsets).
    enum ThekaSpells : std::uint32_t
    {
        SPELL_TK_BITE               = kSpellSlice.first + 0,    // TK1 Persecutors' Bite: resolve copy (Nature)
        SPELL_TK_DEVOUR             = kSpellSlice.first + 1,    // TK2 Devouring Swarm: resolve copy (Nature)
        SPELL_TK_HALLOWED           = kSpellSlice.first + 2,    // TK3 Hallowed Suffering: his stacking buff
        SPELL_TK_PLAGUE             = kSpellSlice.first + 3,    // TK4 Fevered Plague, normal: 4 s, kickable Nature
        SPELL_TK_PLAGUE_HEROIC      = kSpellSlice.first + 4,    // TK4 heroic: 2 s, the spreading one
        SPELL_TK_PLAGUE_SPREAD      = kSpellSlice.first + 5,    // TK4 heroic: the copy (a DoT that never spreads)
        SPELL_TK_PLAGUE_LOOK        = kSpellSlice.first + 6,    // TK4: the lasting state on the carrier (look only)
        SPELL_TK_RISING             = kSpellSlice.first + 7,    // TK5 Martyr's Rising: the flash (look only)
        SPELL_TK_ERUPTION           = kSpellSlice.first + 8,    // TK7 Penitent Eruption: resolve copy (Nature)
        SPELL_TK_LAMENT             = kSpellSlice.first + 9,    // TK8 Martyr's Lament (heroic): the script's amount
        SPELL_TK_SWARM_AURA         = kSpellSlice.first + 10,   // both swarms' cloud (look only)
        SPELL_TK_RISE_BURST         = kSpellSlice.first + 11,   // TK1 the rise burst at a point (look only)
        SPELL_TK_ERUPTION_LOOK      = kSpellSlice.first + 12,   // TK7 the burst where a hunt stopped (look only)
        SPELL_TK_SWARM_ON_THEKA     = kSpellSlice.first + 13,   // TK2 the swarm boiling on him, 2.5 s (look only)
        SPELL_TK_HUNT_TRAIL         = kSpellSlice.first + 14,   // TK6 the Penitent Swarm burrowing (look only)
    };
    static_assert(SPELL_TK_HUNT_TRAIL <= kSpellSlice.last);

    // creature_text 7272 (rev_theka_zul_farrak.sql), 0-based as SP prints them (rule 34).
    enum ThekaTexts : std::uint8_t
    {
        YELL_THEKA_AGGRO    = 0,    // "Who disturbs da Martyr's tomb?"
        EMOTE_THEKA_SWARM   = 1,    // TK1
        EMOTE_THEKA_DEVOUR  = 2,    // TK2
        YELL_THEKA_RISING   = 3,    // TK5
        EMOTE_THEKA_HUNT    = 4,    // TK6, names the player
    };

    // Registry tags. 1 to 5 are the drill's (mod-boss-mechanics MechanicDrill.h kZfTagSwarm, kZfTagReaim,
    // kZfTagDevour, kZfTagSwarmNormal, kZfTagDevourNormal: row 1 of zul-farrak-shapes); the hunt and the spread are
    // not drilled: the first tags past the drill's 40.
    enum ThekaTags : std::uint32_t
    {
        TAG_TK_SWARM_HEROIC     = 1,
        TAG_TK_REAIM            = 2,
        TAG_TK_DEVOUR_HEROIC    = 3,
        TAG_TK_SWARM_NORMAL     = 4,
        TAG_TK_DEVOUR_NORMAL    = 5,
        TAG_TK_CHASE            = 41,
        TAG_TK_ERUPTION         = 42,
        TAG_TK_SPREAD           = 43,
    };

    constexpr std::uint32_t SwarmTag(bool heroic) { return heroic ? TAG_TK_SWARM_HEROIC : TAG_TK_SWARM_NORMAL; }
    constexpr std::uint32_t DevourTag(bool heroic) { return heroic ? TAG_TK_DEVOUR_HEROIC : TAG_TK_DEVOUR_NORMAL; }

    // ----------------------------------------------------------------------------------------------------------------
    // The build spec's numbers (SP Theka "Build spec", "Heroic", "Tuning starting points"; rulings 12, 25, 45)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // TK1 Persecutors' Swarm: phase 1 only.
        inline constexpr NH<std::uint32_t> kSwarmFirstMs{ 12000, 20000 };
        inline constexpr std::uint32_t kSwarmEveryMs = 20000;
        inline constexpr NH<std::uint32_t> kSwarmsPerRise{ 1, 2 };          // heroic: one NW, one NE (section 7 #27 A)
        inline constexpr NH<float> kSwarmSpeed{ 4.f, 5.f };                 // yd/s
        inline constexpr float kSwarmWidth = 4.f;
        inline constexpr std::uint32_t kRiseMs = 2000;                      // the burst, then it crawls
        inline constexpr NH<float> kBitePct{ 30.f, 45.f };                  // + Weakened, tank included
        // TK2 the swarm reaches him: the circle is drawn 2.5 s before the arrival (10 yd out at 4 yd/s, 12.5 at 5).
        inline constexpr std::uint32_t kArrivalWarnMs = 2500;
        inline constexpr float kDevourRadius = 6.f;
        inline constexpr NH<float> kDevourPct{ 40.f, 60.f };                // + Weakened (ruling 25), tank included
        inline constexpr std::uint32_t kHoldMs = 2500;                      // held in place, still casting
        // TK3 Hallowed Suffering: cap 5 on normal, none on heroic (ruling 45; the aura's CumulativeAura 99 is out of
        // reach: a pair every 20 s).
        inline constexpr std::uint32_t kStackCapNormal = 5;
        inline constexpr std::uint32_t kStackCapHeroic = 99;
        // TK4 Fevered Plague: both phases, a random player within 30 yd, the tank included.
        inline constexpr std::uint32_t kPlagueFirstMs = 8000;
        inline constexpr std::uint32_t kPlagueEveryMinMs = 12000;
        inline constexpr std::uint32_t kPlagueEveryMaxMs = 16000;
        inline constexpr NH<std::uint32_t> kPlagueCastMs{ 4000, 2000 };
        inline constexpr float kPlagueRangeYd = 30.f;
        inline constexpr NH<float> kPlagueHitPct{ 10.f, 20.f };
        inline constexpr NH<float> kPlagueDotPct{ 15.f, 40.f };             // over the whole DoT
        inline constexpr NH<std::uint32_t> kPlagueMs{ 12000, 10000 };
        inline constexpr NH<std::uint32_t> kPlagueTickMs{ 3000, 2000 };
        inline constexpr float kSpreadYd = 6.f;                             // heroic: every 2 s, copies never spread
        inline constexpr std::uint32_t kSpreadEveryMs = 2000;
        // TK5 Martyr's Rising at 30%.
        inline constexpr float kRisingPct = 30.f;
        inline constexpr std::uint32_t kRisingMs = 2000;
        // TK6 / TK7 Penitent Hunt: one swarm per stack, each every 15 s (heroic 12), staggered evenly.
        inline constexpr NH<std::uint32_t> kHuntEveryMs{ 15000, 12000 };
        inline constexpr std::uint32_t kChaseMs = 5000;
        inline constexpr float kChaseSpeed = 5.f;                           // a player runs 7
        inline constexpr float kChaseRadius = 3.f;
        inline constexpr std::uint32_t kEruptionWarnMs = 1500;
        inline constexpr float kEruptionRadius = 5.f;
        inline constexpr NH<float> kEruptionPct{ 30.f, 45.f };              // + Weakened, tank included
        // TK8 Martyr's Lament (heroic, phase 2): 1.5% a stack every 3 s to everyone, no cap (ruling 45).
        inline constexpr std::uint32_t kLamentEveryMs = 3000;
        inline constexpr float kLamentPctPerStack = 1.5f;

        // Section 3.5 rule 32 (SYS 4): no hit under a 1.5 s warning on normal.
        static_assert(kRiseMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kArrivalWarnMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kEruptionWarnMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kPlagueCastMs.normal >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kPlagueCastMs.heroic >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kChaseMs + kEruptionWarnMs < kHuntEveryMs.heroic);    // a swarm's hunts never overlap
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Values the build spec leaves open (the report lists each)
    // ----------------------------------------------------------------------------------------------------------------
    // TK1: a swarm whose line ends where Theka no longer stands turns there and crawls on in a new line (SP "turns at
    // the line's end"). The new line is drawn this long before the body moves on (G1's drill models 0.5 s as
    // kZfReaimMs; this build's live value wins and meets the 1.5 s floor: a turn is a new warning).
    std::uint32_t constexpr kReaimMs = 1500;
    static_assert(kReaimMs >= ZulFarrakRework::kWarningFloorMs);
    // The body has reached its line's end within this (2D).
    float constexpr kSegmentEndYd = 1.f;
    // He still stands on the line's way if he is within this of what is left of it.
    float constexpr kOnLineYd = 3.f;
    // The body stops this far from his center (his hit box); the closing distance adds it.
    float constexpr kArriveReachYd = 1.5f;
    // A swarm that has crawled this long without arriving sinks (a tank who never stops walking him).
    std::uint32_t constexpr kSwarmLifeMs = 60000;
    // The swarm's object scale (_visuals.py SWARM_SCALE_RANGE 1.3 to 2.0; the cloud SV 10986 grows with the unit and
    // is 4.3 x 4.7 yd at 1.0, so the low end matches the 4 yd line). theka.py sets it on both swarms' model rows.
    float constexpr kSwarmScale = 1.3f;
    // Martyr's Rising: display 6697 is TrollMale with its own CreatureDisplayInfo scale 1.2 [verified: DBC], so the
    // object scale stays 1 (stock Theka Transform used creature 7791 at scale 1).
    std::uint32_t constexpr kRisenDisplay = 6697;
    float constexpr kRisenObjectScale = 1.f;
    // The first Penitent Hunt this long after the rising ends.
    std::uint32_t constexpr kHuntFirstMs = 3000;
    // The heroic Lament's first pulse this long after the rising ends.
    std::uint32_t constexpr kLamentFirstMs = Tune::kLamentEveryMs;
    // The courtyard's Scarabs (section 7 #22 A) within this of his spawn burrow for the fight: section 7 #22 counts 17
    // within 40 yd; 45 also takes the wanderers a few yd past it near rise points C and D (wander 5).
    float constexpr kBurrowRadiusYd = 45.f;
    // A fallen plague cast (a kick, a lock, out of range) tries again this long after.
    std::uint32_t constexpr kPlagueRetryMs = 1000;
    // TK2's emote at most once in this (a heroic pair closes together).
    std::uint32_t constexpr kDevourEmoteGapMs = 2000;

    // The rise points' sectors (section 7 #27 A): A and B face north-west, C and D north-east.
    inline constexpr std::array<std::size_t, 2> kNorthWest{ { 0, 1 } };
    inline constexpr std::array<std::size_t, 2> kNorthEast{ { 2, 3 } };

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------
    // The rise points of one beat: normal one of the four, heroic one of each sector (so the lines cross only at
    // Theka). `rand(n)` returns [0, n).
    template <typename Rand>
    std::vector<std::size_t> RisePicks(bool heroic, Rand&& rand)
    {
        if (!heroic)
            return { static_cast<std::size_t>(rand(4u)) };
        std::size_t const nw = kNorthWest[rand(2u)];
        std::size_t const ne = kNorthEast[rand(2u)];
        return { nw, ne };
    }

    // Up to `count` distinct entries of `ids` in random order, none of `excluded` first; when that leaves fewer than
    // `count`, the excluded ones fill up (a hunt never waits for a free player). `rand(n)` returns [0, n).
    template <typename Id, typename Rand>
    std::vector<Id> PickPreferring(std::vector<Id> const& ids, std::vector<Id> const& excluded, std::size_t count,
        Rand&& rand)
    {
        std::vector<Id> free;
        std::vector<Id> taken;
        for (Id const& id : ids)
            (std::find(excluded.begin(), excluded.end(), id) == excluded.end() ? free : taken).push_back(id);
        auto shuffle = [&rand](std::vector<Id>& v)
        {
            for (std::size_t i = 0; i + 1 < v.size(); ++i)
                std::swap(v[i], v[i + rand(static_cast<std::uint32_t>(v.size() - i))]);
        };
        shuffle(free);
        shuffle(taken);
        free.insert(free.end(), taken.begin(), taken.end());
        free.resize(std::min(count, free.size()));
        return free;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The swarm's crawl (TK1, TK2)
    // ----------------------------------------------------------------------------------------------------------------
    // How close (2D, body to his center) the body is when TK2's circle is drawn: the 2.5 s warning at its speed, plus
    // his hit box.
    constexpr float ClosingYd(bool heroic)
    {
        return Tune::kSwarmSpeed(heroic) * static_cast<float>(Tune::kArrivalWarnMs) / 1000.f + kArriveReachYd;
    }

    // TK2 is drawn when the body is within the closing distance of him and he stands on what is left of its line (he
    // has not been walked off it): it then goes straight for him and lands 2.5 s later.
    inline bool Closing(Vec2 body, Vec2 lineEnd, Vec2 theka, bool heroic)
    {
        return DungeonKit::Distance(body, theka) <= ClosingYd(heroic)
            && DungeonKit::SegmentDistance(body, lineEnd, theka) <= kOnLineYd;
    }

    // The body is at its line's end without having closed: it turns after him (a new line from here to him).
    inline bool AtLineEnd(Vec2 body, Vec2 lineEnd)
    {
        return DungeonKit::Distance(body, lineEnd) <= kSegmentEndYd;
    }

    // The closing walk's speed: the body covers `distYd` (less his hit box) in the 2.5 s warning, never slower than 1.
    constexpr float ClosingSpeed(float distYd)
    {
        return std::max(1.f, (distYd - kArriveReachYd) * 1000.f / static_cast<float>(Tune::kArrivalWarnMs));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Stacks, hunts, the Lament, the plague
    // ----------------------------------------------------------------------------------------------------------------
    constexpr std::uint32_t StackCap(bool heroic) { return heroic ? Tune::kStackCapHeroic : Tune::kStackCapNormal; }

    // TK3: one more stack per arrival, at the cap no more.
    constexpr std::uint32_t AddStack(std::uint32_t stacks, bool heroic)
    {
        return std::min(stacks + 1, StackCap(heroic));
    }

    // TK6: penitent swarm `index` of `count` hunts first at `startMs` + kHuntFirstMs + its share of one period
    // (staggered evenly), then every period.
    constexpr std::uint64_t HuntFirstDueMs(std::uint64_t startMs, std::uint32_t index, std::uint32_t count, bool heroic)
    {
        std::uint32_t const every = Tune::kHuntEveryMs(heroic);
        return startMs + kHuntFirstMs + (count ? std::uint64_t(every) * index / count : 0);
    }

    // TK8: the pulse's percent of the reference row.
    constexpr float LamentPct(std::uint32_t stacks) { return Tune::kLamentPctPerStack * static_cast<float>(stacks); }

    // TK4: the DoT's tick in hundredths of a percent (spell_dungeon_refflat_periodic's effect value), so the ticks of
    // one plague add up to the spec's percent.
    constexpr std::int32_t PlagueTickHundredths(bool heroic)
    {
        std::uint32_t const ticks = Tune::kPlagueMs(heroic) / Tune::kPlagueTickMs(heroic);
        return static_cast<std::int32_t>(Tune::kPlagueDotPct(heroic) * 100.f / static_cast<float>(ticks) + 0.5f);
    }

    // TK4: the direct hit in hundredths (spell_dungeon_refflat_damage's effect value).
    constexpr std::int32_t PlagueHitHundredths(bool heroic)
    {
        return static_cast<std::int32_t>(Tune::kPlagueHitPct(heroic) * 100.f + 0.5f);
    }

    // TK4: the next cast `rollMs` (kPlagueEveryMinMs to kPlagueEveryMaxMs) after this one.
    constexpr std::uint32_t PlagueGapMs(std::uint32_t rollMs)
    {
        return std::clamp(rollMs, Tune::kPlagueEveryMinMs, Tune::kPlagueEveryMaxMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timeline
    // ----------------------------------------------------------------------------------------------------------------
    // A beat on a fixed grid: the next one is `everyMs` after this one's due time, never in the past.
    class BeatClock
    {
    public:
        void Start(std::uint64_t firstMs, std::uint32_t everyMs)
        {
            _on = true;
            _dueMs = firstMs;
            _everyMs = everyMs;
        }

        void Stop() { *this = BeatClock(); }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }
        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // `everyMs` 0: the clock's own period.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs = 0)
        {
            std::uint32_t const every = everyMs ? everyMs : _everyMs;
            _dueMs += every;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + every;
        }

        // Not before `atMs` (a beat that fell inside the rising waits for its end; rule 11: max(due, ...)).
        void NotBefore(std::uint64_t atMs) { _dueMs = std::max(_dueMs, atMs); }

    private:
        bool _on = false;
        std::uint32_t _everyMs = 0;
        std::uint64_t _dueMs = 0;
    };

    // The phase-1 swarm beats and the both-phase plague (times in ms since the pull). The rising stops the swarms; a
    // plague that falls inside the rising waits for its end.
    class Timeline
    {
    public:
        void Start(bool heroic)
        {
            *this = Timeline();
            _swarm.Start(Tune::kSwarmFirstMs(heroic), Tune::kSwarmEveryMs);
            _plague.Start(Tune::kPlagueFirstMs, Tune::kPlagueEveryMinMs);
        }

        void Stop() { *this = Timeline(); }
        bool On() const { return _plague.On(); }

        bool SwarmDue(std::uint64_t nowMs) const { return _swarm.Due(nowMs); }
        void SwarmRose(std::uint64_t nowMs) { _swarm.Fired(nowMs); }
        std::uint64_t SwarmDueMs() const { return _swarm.DueMs(); }

        bool PlagueDue(std::uint64_t nowMs) const { return _plague.Due(nowMs); }
        // Cast: the next one `rollMs` (12 to 16 s) on. Refused: again in kPlagueRetryMs.
        void PlagueCast(std::uint64_t nowMs, std::uint32_t rollMs) { _plague.Fired(nowMs, PlagueGapMs(rollMs)); }
        void PlagueRetry(std::uint64_t nowMs) { _plague.Fired(nowMs, kPlagueRetryMs); }
        std::uint64_t PlagueDueMs() const { return _plague.DueMs(); }

        // TK5: no more swarms; the plague waits for the rising's end.
        void Rising(std::uint64_t riseEndMs)
        {
            _swarm.Stop();
            _plague.NotBefore(riseEndMs);
        }

    private:
        BeatClock _swarm;
        BeatClock _plague;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Stack math (SP "Stack math"; section 3.6; rule 26): a group that never drags him, lines of `lineYd`. The stacks
    // he holds when phase 1 ends after `phase1Ms`.
    // ----------------------------------------------------------------------------------------------------------------
    constexpr std::uint64_t ArrivalMs(std::uint32_t beat, float lineYd, bool heroic)
    {
        return Tune::kSwarmFirstMs(heroic) + std::uint64_t(beat) * Tune::kSwarmEveryMs + Tune::kRiseMs
            + static_cast<std::uint64_t>(lineYd / Tune::kSwarmSpeed(heroic) * 1000.f);
    }

    constexpr std::uint32_t StacksAtRising(std::uint64_t phase1Ms, float lineYd, bool heroic)
    {
        std::uint32_t stacks = 0;
        for (std::uint32_t beat = 0; ArrivalMs(beat, lineYd, heroic) <= phase1Ms; ++beat)
            for (std::uint32_t i = 0; i < Tune::kSwarmsPerRise(heroic); ++i)
                stacks = AddStack(stacks, heroic);
        return stacks;
    }

    // Phase 1's length at `groupDps` (70% of his health).
    constexpr std::uint64_t Phase1Ms(std::uint32_t health, float groupDps)
    {
        return static_cast<std::uint64_t>(static_cast<float>(health) * (1.f - Tune::kRisingPct / 100.f) / groupDps
            * 1000.f);
    }
}

#endif
