/*
 * mod-dungeon-bosses, Stratholme S4: Malor the Zealous (11032), the pure, host-testable part (no engine headers).
 * Build spec ST 1239-1289 (docs/dungeons/stratholme-rework.md), design ST 1150-1238, handoff section 3.4 rows MZ,
 * section 3.5 row S4, section 3.6 (normal 175k, heroic 230k), section 3.8 (his arena and the tank spots). Tested by
 * tests/strat_malor_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsMalor (206480-206499), declared in apps/dbc-tools
 *                  source/npcs/stratholme/malor_the_zealous.py
 *   Tuning         NH<> constants and Cadence{first, every}: one number per difficulty, straight from the build spec
 *   InBeam         MZ2 the lane from the strongbox to him: who stands in it (flat ends, 3 yd wide)
 *   Blockers       MZ2 / MZ4 the non-tanks in the lane (the tank never blocks)
 *   FadeDue        MZ3 / MZ4 a stack that fades on a clock (one per 8 s on him, one per 2 s on a blocker once out)
 *   UncleanTrack   MZ5 / MZ6 the 8 s debuff: two beam seconds purify it, running out is a Judgment
 *   Heal rules     MZ9 / MZ10 the Faith-scaled heals
 *   CastPlan       MZ7 / MZ9 / MZ10 the cast queue, so his casts never overlap
 *
 * Damage percentages are of the reference health row (normal 3,670 / 3,710 tank, heroic 4,120 / 4,110, the 329:60
 * pins): the build spec gives N / H percents.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_MALOR_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_MALOR_LOGIC_H

#include "DungeonKitFlow.h"
#include "DungeonKitMath.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace StratMalor
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsMalor;

    // Declared in apps/dbc-tools source/npcs/stratholme/malor_the_zealous.py (same ids).
    enum MalorSpells : std::uint32_t
    {
        SPELL_MZ_BLAZE              = kSpellSlice.first + 0,    // MZ1 the beam: the stalker's 12 s channel at him
        SPELL_MZ_FAITH              = kSpellSlice.first + 1,    // MZ3 his buff: +5% damage done per stack
        SPELL_MZ_SEARING_FAITH      = kSpellSlice.first + 2,    // MZ4 the blocker's Holy DoT, per stack
        SPELL_MZ_SEARING_LOOK       = kSpellSlice.first + 3,    // MZ4 the look each second a blocker burns
        SPELL_MZ_UNCLEAN            = kSpellSlice.first + 4,    // MZ5 the 8 s debuff
        SPELL_MZ_JUDGMENT           = kSpellSlice.first + 5,    // MZ6 the hit when Unclean runs out
        SPELL_MZ_SMASH_BAR          = kSpellSlice.first + 6,    // MZ7 the 2 s windup bar
        SPELL_MZ_SMASH_HIT          = kSpellSlice.first + 7,    // MZ7 the circle's hit (resolve copy)
        SPELL_MZ_STUNNED            = kSpellSlice.first + 8,    // MZ7 the 1 s stun rider
        SPELL_MZ_AFTERSHOCK_HIT     = kSpellSlice.first + 9,    // MZ8 heroic: the ring's hit (resolve copy)
        SPELL_MZ_HOLY_LIGHT         = kSpellSlice.first + 10,   // MZ9 the 2.5 s interruptible cast
        SPELL_MZ_HOLY_LIGHT_HEAL    = kSpellSlice.first + 11,   // MZ9 his heal (base point 0 = the amount)
        SPELL_MZ_MIRACLE            = kSpellSlice.first + 12,   // MZ10 the 3 s cast bar
        SPELL_MZ_MIRACLE_HEAL       = kSpellSlice.first + 13,   // MZ10 his heal (base point 0 = the amount)
        // 206494-206499 spare
    };
    static_assert(SPELL_MZ_MIRACLE_HEAL <= kSpellSlice.last, "Malor's spells must stay in his slice");

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum MalorTags : std::uint32_t
    {
        TAG_BEAM_UNCLEAN    = 1,    // MZ2 the lane for the Unclean (they claim it first)
        TAG_BEAM_FREE       = 2,    // MZ2 the lane for the other non-tanks, rotating by Searing Faith
        TAG_SMASH           = 3,    // MZ7
        TAG_AFTERSHOCK      = 4,    // MZ8
        TAG_PARK            = 5,    // the tank's spot at the dais mouth
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry (handoff section 3.8: the dais mouth is where he is fought; the strongbox is the beam's fixed end)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kBeamSource = StratholmeRework::kMalorsStrongbox.XY();    // the stalker stands here
    inline constexpr Vec2 kFightSpot = StratholmeRework::kMalorDaisMouth;           // the tank's spot for him
    inline constexpr float kBeamWidth = 3.f;                                        // the lane, ST MZ2
    inline constexpr float kBeamHalfWidth = kBeamWidth / 2.f;
    // The Park circle: the tank holds him inside it (NoTelegraph, tank only; the Baron's pattern).
    inline constexpr float kParkRadius = 4.f;
    inline constexpr std::uint32_t kParkHoldMs = 7000;      // below the bots' Park.HoldCapMs (8 s); re-registered
    inline constexpr std::uint32_t kParkRefreshLeadMs = 500;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST "Build spec" and "Heroic", approved 2026-11-03)
    // ----------------------------------------------------------------------------------------------------------------

    struct Cadence
    {
        std::uint32_t first;
        std::uint32_t every;
    };

    // MZ1 The blaze: first at 10 s, every 30 s (start to start), 12 s long, judged each second.
    inline constexpr Cadence kBlaze{ 10000, 30000 };
    inline constexpr std::uint32_t kBlazeMs = 12000;
    inline constexpr std::uint32_t kBlazeTickMs = 1000;
    // The lane's soak waits this long before it is judged (the first tick); its lifetime is the blaze's.
    inline constexpr std::uint32_t kBeamWarnMs = 1000;
    // The registered lane keeps the length it had when it was made: re-register when he is this much nearer or
    // farther (a tank who moves him).
    inline constexpr float kBeamRefreshYd = 3.f;
    // Do not re-register a lane that has less than this left.
    inline constexpr std::uint32_t kBeamRefreshMinLeftMs = 2500;
    inline constexpr std::uint32_t kBeamRefreshWarnMs = 250;

    // MZ3 Faith: +5% damage done per stack (the aura's own amount, times its stack count). An unblocked second gives 1
    // stack (heroic 2), up to 10; one stack fades every 8 s.
    inline constexpr NH<std::uint32_t> kFaithPerSecond{ 1, 2 };
    inline constexpr std::uint32_t kFaithMax = 10;
    inline constexpr std::uint32_t kFaithFadeMs = 8000;
    inline constexpr float kFaithDamagePct = 5.f;

    // MZ4 Searing Faith: a stack per second in the beam, Holy damage every second per stack (2%, heroic 3%), a stack
    // fades every 2 s once out of the beam. Capped at the blaze's own length (12 s = 12 stacks), which is not a limit a
    // fair rotation reaches. A player at kSearingClaimCap or more never claims the lane for the bots (ST: "so the bots
    // rotate").
    inline constexpr NH<float> kSearingPct{ 2.f, 3.f };
    inline constexpr std::uint32_t kSearingFadeMs = 2000;
    inline constexpr std::uint32_t kSearingMaxStacks = 12;
    inline constexpr std::uint8_t kSearingClaimCap = 6;

    // MZ5 Unclean: at each blaze's start, on 1 (heroic 2) random non-tanks, 8 s; two seconds in the beam purify it
    // (cumulative); if the 8 s run out, MZ6 Judgment.
    inline constexpr NH<std::uint32_t> kUncleanCount{ 1, 2 };
    inline constexpr std::uint32_t kUncleanMs = 8000;
    inline constexpr std::uint32_t kUncleanPurifySeconds = 2;
    inline constexpr NH<float> kJudgmentPct{ 40.f, 50.f };
    // The free blockers' lane waits for the Unclean to claim the beam first, at most this long into the blaze.
    inline constexpr std::uint32_t kFreeBlockersGraceMs = 3000;

    // MZ7 Ground Smash: first at 15 s, every 15 s; a 2 s windup (emote line 3), an 8 yd circle on him, tank included:
    // 30% + Weakened + a 1 s stun.
    inline constexpr Cadence kSmash{ 15000, 15000 };
    inline constexpr std::uint32_t kSmashCastMs = 2000;
    inline constexpr float kSmashRadius = 8.f;
    inline constexpr float kSmashPct = 30.f;
    inline constexpr std::uint32_t kSmashStunMs = 1000;

    // MZ8 Aftershock (heroic): 1.5 s after the Smash resolves, a ring from 8 to 14 yd on him, 30% + Weakened.
    inline constexpr float kAftershockInner = 8.f;
    inline constexpr float kAftershockOuter = 14.f;
    inline constexpr std::uint32_t kAftershockWarnMs = 1500;
    inline constexpr float kAftershockPct = 30.f;

    // MZ9 Holy Light: first at 20 s, every 15 s; a 2.5 s interruptible cast. Heals 1% of his maximum health per Faith
    // stack (heroic: 3% plus 1% per stack).
    inline constexpr Cadence kHolyLight{ 20000, 15000 };
    inline constexpr std::uint32_t kHolyLightCastMs = 2500;
    inline constexpr NH<float> kHolyLightBasePct{ 0.f, 3.f };
    inline constexpr float kHolyLightPerStackPct = 1.f;
    // The interrupt list entry (the descriptor): a reward on normal, expected on heroic.
    inline constexpr NH<std::uint8_t> kHolyLightKickPriority{ 1, 3 };

    // MZ10 Miracle: once, at 10% health or lower; a 3 s cast he kneels for, not interruptible; heals 8% of his maximum
    // health per Faith stack.
    inline constexpr float kMiracleHealthPct = 10.f;
    inline constexpr std::uint32_t kMiracleCastMs = 3000;
    inline constexpr float kMiracleHealPerStackPct = 8.f;

    // His casts never overlap: the second waits for the first, then this long. A refused cast tries again soon.
    inline constexpr std::uint32_t kCastSpacingMs = 300;
    inline constexpr std::uint32_t kCastRetryMs = 1000;

    // The AI's slow tick (fades, the park circle): every 500 ms.
    inline constexpr std::uint32_t kHousekeepingMs = 500;

    // ----------------------------------------------------------------------------------------------------------------
    // MZ2 / MZ4 The beam: who stands in the lane
    // ----------------------------------------------------------------------------------------------------------------

    struct Candidate
    {
        std::uint64_t id = 0;
        Vec2 pos;
        bool tank = false;
    };

    // Inside the lane from `from` (the strongbox) to `to` (him), `halfWidth` either side of the line, with flat ends
    // at both points (the registry's Line shape: a player behind the box or behind him is not in it).
    inline bool InBeam(Vec2 from, Vec2 to, float halfWidth, Vec2 p)
    {
        float const dx = to.x - from.x;
        float const dy = to.y - from.y;
        float const len = std::hypot(dx, dy);
        if (len < 0.001f)
            return false;
        float const ux = dx / len;
        float const uy = dy / len;
        float const px = p.x - from.x;
        float const py = p.y - from.y;
        float const along = px * ux + py * uy;
        float const across = std::fabs(px * uy - py * ux);
        return along >= 0.f && along <= len && across <= halfWidth;
    }

    // The non-tanks in the lane (indices into `c`): they block it. The tank never does (ST MZ2).
    inline std::vector<std::size_t> Blockers(Vec2 from, Vec2 to, float halfWidth, std::vector<Candidate> const& c)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (!c[i].tank && InBeam(from, to, halfWidth, c[i].pos))
                out.push_back(i);
        return out;
    }

    // The lane was registered with `registered` yd of length; he is `current` yd from the box now.
    inline bool BeamNeedsRefresh(float registered, float current)
    {
        return std::fabs(current - registered) > kBeamRefreshYd;
    }

    // MZ2 "Unclean first": the free blockers' lane opens when no Unclean player is left, or `ageMs` into the blaze at
    // the latest.
    inline bool FreeBlockersDue(std::uint32_t ageMs, std::size_t uncleanLeft)
    {
        return uncleanLeft == 0 || ageMs >= kFreeBlockersGraceMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MZ3 Faith, MZ4 Searing Faith: stacks, gains and the fade clock
    // ----------------------------------------------------------------------------------------------------------------

    // Faith after an unblocked second.
    inline std::uint32_t FaithAfter(std::uint32_t current, std::uint32_t gain)
    {
        return std::min(kFaithMax, current + gain);
    }

    inline std::uint32_t SearingAfter(std::uint32_t current)
    {
        return std::min(kSearingMaxStacks, current + 1);
    }

    // A stack that fades on a clock. `stacks` are held now; `nextMs` is when the next one goes (0: not started).
    // Returns how many stacks fade at `now` and moves the clock: the clock starts at the first look at a held stack
    // and runs on (a new stack does not restart it); with no stacks it stops.
    inline std::uint32_t FadeDue(std::uint32_t stacks, std::uint64_t now, std::uint64_t& nextMs, std::uint64_t everyMs)
    {
        if (!stacks)
        {
            nextMs = 0;
            return 0;
        }
        if (!nextMs)
        {
            nextMs = now + everyMs;
            return 0;
        }
        std::uint32_t lost = 0;
        while (lost < stacks && now >= nextMs)
        {
            ++lost;
            nextMs += everyMs;
        }
        if (lost >= stacks)
            nextMs = 0;
        return lost;
    }

    // A blocker still in the beam does not fade: the clock restarts (stacks fade "once out").
    inline void HoldFade(std::uint64_t now, std::uint64_t& nextMs, std::uint64_t everyMs)
    {
        nextMs = now + everyMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MZ5 / MZ6 Unclean
    // ----------------------------------------------------------------------------------------------------------------

    struct UncleanTrack
    {
        std::uint64_t endMs = 0;                // the aura's end on the AI's clock
        std::uint32_t beamSeconds = 0;          // seconds spent in the beam so far
    };

    // One second of the blaze: true once the bearer has spent enough seconds in the beam (purified).
    inline bool UncleanTick(UncleanTrack& t, bool inBeam)
    {
        if (inBeam)
            ++t.beamSeconds;
        return t.beamSeconds >= kUncleanPurifySeconds;
    }

    inline bool UncleanExpired(UncleanTrack const& t, std::uint64_t now)
    {
        return now >= t.endMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MZ9 / MZ10 The heals
    // ----------------------------------------------------------------------------------------------------------------

    inline float HolyLightHealPct(bool heroic, std::uint32_t faith)
    {
        return kHolyLightBasePct(heroic) + kHolyLightPerStackPct * static_cast<float>(faith);
    }

    inline float MiracleHealPct(std::uint32_t faith)
    {
        return kMiracleHealPerStackPct * static_cast<float>(faith);
    }

    // `pct` percent of his maximum health, rounded (an exact amount for the heal spell's base point 0).
    inline std::uint32_t HealAmount(std::uint32_t maxHealth, float pct)
    {
        double const v = std::max(0.f, pct) / 100.0 * static_cast<double>(maxHealth);
        return static_cast<std::uint32_t>(std::max<long>(0, std::lround(v)));
    }

    // MZ10: at 10% health or lower, once.
    inline bool MiracleDue(float healthPct, bool done)
    {
        return !done && healthPct <= kMiracleHealthPct;
    }

    // The next start of a cadence that counts from the planned time, not from a late start.
    inline std::uint64_t NextOnCadence(std::uint64_t planned, std::uint64_t now, std::uint32_t every)
    {
        return std::max<std::uint64_t>(planned + every, now + 1);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The cast plan: MZ7 Ground Smash, MZ9 Holy Light, MZ10 Miracle on one queue (the CastQueue of the kit)
    // ----------------------------------------------------------------------------------------------------------------

    class CastPlan
    {
    public:
        using Ms = std::uint64_t;

        enum Cast : std::uint32_t
        {
            Smash       = 1,
            HolyLight   = 2,
            Miracle     = 3,
        };

        static constexpr std::uint8_t kPrioritySmash = 2;
        static constexpr std::uint8_t kPriorityHolyLight = 3;   // the interruptible cast goes first when two are due
        static constexpr std::uint8_t kPriorityMiracle = 4;     // the once-per-fight heal goes before both

        CastPlan() : _queue(kCastSpacingMs) { Reset(); }

        // The pull (or a reset): the first casts at their ST times; the Miracle waits for his health.
        void Reset()
        {
            _queue = DungeonKit::CastQueue(kCastSpacingMs);
            _nominal.fill(0);
            _miracleUsed = false;
            Arm(Smash, kSmash.first);
            Arm(HolyLight, kHolyLight.first);
        }

        static constexpr Ms CastMs(Cast c)
        {
            switch (c)
            {
                case Smash:     return kSmashCastMs;
                case HolyLight: return kHolyLightCastMs;
                case Miracle:   return kMiracleCastMs;
            }
            return 0;
        }

        static constexpr Ms Every(Cast c)
        {
            switch (c)
            {
                case Smash:     return kSmash.every;
                case HolyLight: return kHolyLight.every;
                case Miracle:   return 0;
            }
            return 0;
        }

        // He is at 10% health: the Miracle is due now (once; never again after it started).
        void ArmMiracle(Ms now)
        {
            if (_miracleUsed || _queue.Queued(Miracle))
                return;
            _queue.Schedule(Miracle, now, kPriorityMiracle);
        }

        bool MiracleUsed() const { return _miracleUsed; }

        // The cast to start now, if any.
        std::optional<Cast> Next(Ms now) const
        {
            std::optional<std::uint32_t> const next = _queue.Next(now);
            if (!next)
                return std::nullopt;
            return static_cast<Cast>(*next);
        }

        // `cast` began at `now`: it holds him for its cast time, and the next one is booked from its planned time (a
        // start that slipped behind another cast does not push the cadence). The Miracle never repeats.
        void Started(Cast cast, Ms now)
        {
            _queue.Started(cast, now, CastMs(cast), true);
            if (cast == Miracle)
            {
                _miracleUsed = true;
                return;
            }
            Ms next = _nominal[cast] + Every(cast);
            if (next < now)
                next = now;
            Arm(cast, next);
        }

        // The cast was refused (a silence, no target): try again soon, the cadence unchanged.
        void Refused(Cast cast, Ms now)
        {
            _queue.Schedule(cast, now + kCastRetryMs, PriorityOf(cast));
        }

        // His current cast ended early at `now` (interrupted, cancelled).
        void Interrupted(Ms now) { _queue.Interrupted(now); }

        std::optional<Ms> DueAt(Cast cast) const { return _queue.DueAt(cast); }

    private:
        static constexpr std::uint8_t PriorityOf(Cast c)
        {
            return c == Miracle ? kPriorityMiracle : (c == HolyLight ? kPriorityHolyLight : kPrioritySmash);
        }

        void Arm(Cast cast, Ms at)
        {
            _nominal[cast] = at;
            _queue.Schedule(cast, at, PriorityOf(cast));
        }

        DungeonKit::CastQueue _queue;
        std::array<Ms, 4> _nominal{};
        bool _miracleUsed = false;
    };
}

#endif
