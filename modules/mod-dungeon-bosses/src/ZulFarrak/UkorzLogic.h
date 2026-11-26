/*
 * mod-dungeon-bosses, Zul'Farrak D6: Chief Ukorz Sandscalp (7267) and Ruuzlu (7797), the pure, host-testable part (no
 * engine headers). Build spec: docs/dungeons/zul-farrak-rework.md "Chief Ukorz Sandscalp and Ruuzlu" (UK1-UK14,
 * Build spec), handoff sections 3.5 row D6, 3.6, 3.8 (the mesa), 7 #10, #34, #41 and #42 (all A), section 10.
 * Health is ZulFarrakRework.h Health: never restated here. Tested by tests/zf_ukorz_test.cpp; the spell ids and the
 * numbers apps/dbc-tools source/npcs/zul_farrak/ukorz.py pins are checked by lib/test_zul_farrak_ukorz.py.
 *
 *   FuryMeter      UK1 one boss's meter: a stack per 4% (heroic 3%) of the partner's health lost (any damage), one
 *                  stack off every 4 s (5 s) once the partner lost under 1% in the last 4 s (section 7 #41 A); with the
 *                  partner down on normal, Vengeance (UK9): no fade, a stack every 3 s. Battle Roar is due at 5, once
 *                  per fill; 10 is full (the Bladestorm empties it)
 *   PickFavored    the kill order's pick: hit the boss whose partner's Fury is lower, with a 3-stack hysteresis,
 *                  never a held boss (heroic 30%), never one more than 8% below the other (BM's KillTogether: 10%)
 *   ExecutionerFor section 7 #42 A: Ruuzlu executes while he stands; Ukorz once Ruuzlu is gone, and on heroic phase 1
 *                  the two share (one each); a lone one takes the sunk in order
 *   HoldDamage     UK9 heroic: a boss's damage clamped at the 30% line
 *   LashChain      UK12: the struck player, then every other player within 8 yd of a struck one, up to 4 jumps
 *   CreepInnerYd   UK13: the safe circle's radius, 30 yd closing 5 yd every 20 s from phase 3's start, to nothing
 *   CreepSafeFloor F-1 MI-4: the bots' planned spots while the donut is up: the safe circle clipped to the mesa
 *   NextDue        RB-17 / L8: a beat that waited keeps max(due + period, now + period / 2)
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_UKORZ_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_UKORZ_LOGIC_H

#include "DungeonKitMath.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <deque>
#include <optional>
#include <utility>
#include <vector>

namespace ZfUkorz
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsUkorz;

    // apps/dbc-tools source/npcs/zul_farrak/ukorz.py declares each (lib/test_zul_farrak_ukorz.py pins the names).
    enum UkorzSpells : std::uint32_t
    {
        SPELL_UK_FURY               = 214070,   // UK1 the meter, +3% damage done a stack (normal)
        SPELL_UK_FURY_HEROIC        = 214071,   // UK1 +4% a stack (heroic)
        SPELL_UK_FURY_FULL          = 214072,   // UK1 the full meter's look (Frenzy 3019's), with the yell
        SPELL_UK_ROAR               = 214073,   // UK2 Battle Roar of the Sandfury, 2.5 s, kickable, Fire
        SPELL_UK_ROAR_HEROIC        = 214074,   // UK2 2 s
        SPELL_UK_STORM_WINDUP       = 214075,   // UK3 the 2 s wind-up bar (Physical, not kickable)
        SPELL_UK_STORM_SPIN         = 214076,   // UK3 the spin's look, an aura on the boss
        SPELL_UK_STORM              = 214077,   // UK3 the ring's tick (resolve copy, Physical)
        SPELL_UK_STAMP              = 214078,   // UK5 the stamp's bar, 2 s (Physical, not kickable)
        SPELL_UK_STAMP_HEROIC       = 214079,   // UK5 1.5 s
        SPELL_UK_PIT_LOOK           = 214080,   // UK5 the pit's look on its stalker (301025)
        SPELL_UK_TRAIL_LOOK         = 214081,   // UK4 the trail's look on its stalker (301025)
        SPELL_UK_QUICKSAND          = 214082,   // UK4, UK5, UK13 the 50% slow rider
        SPELL_UK_SUNK               = 214083,   // UK6 the root, 8 s, not dispellable
        SPELL_UK_EXECUTE_BAR        = 214084,   // UK7 the 4 s bar on the sunk (Physical, not kickable)
        SPELL_UK_EXECUTE            = 214085,   // UK7 the hit: Physical, the script's base point
        SPELL_UK_CALL               = 214086,   // UK10 Call of Sul'thraze, the 10 s bar (Physical, not kickable)
        SPELL_UK_LASH_BAR           = 214087,   // UK12 the 2 s bar: the blade glows
        SPELL_UK_LASH_MARK          = 214088,   // UK12 the mark on the first target, 2 s
        SPELL_UK_LASH               = 214089,   // UK12 a lash: Shadow, the script's base point
        SPELL_UK_LASH_DEBUFF        = 214090,   // UK12 15% less of every stat, 15 s, not dispellable
        SPELL_UK_CREEPING           = 214091,   // UK13 the donut's tick (resolve copy, Shadow)
        SPELL_UK_HELD               = 214092,   // UK9 heroic: the 30% hold's state on the held boss
        SPELL_UK_VENGEANCE          = 214093,   // UK9 normal: Vengeance's state on the survivor
        // 214094-214109 spare.
    };

    // Stock spells kept as cast (ruling 33).
    std::uint32_t constexpr SPELL_BERSERKER_STANCE = 7366;
    std::uint32_t constexpr SPELL_CLEAVE = 15496;
    std::uint32_t constexpr SPELL_FRENZY = 8269;

    // Ruuzlu's spawn [DB guid 37997]: restored with Map::ForceCreatureRespawn when his object is gone (RB-20: a heroic
    // wipe after the transition, a reload after it).
    std::uint32_t constexpr kSpawnRuuzlu = 37997;

    // Text groups (rule 34: 0-based as SP prints them; Ukorz 0 to 3 are stock).
    enum UkorzTexts : std::uint8_t
    {
        SAY_UKORZ_KILL          = 0,    // "Die, outlander!" (stock, now said on a kill)
        SAY_UKORZ_FRENZY        = 1,    // "Feel the fury of the sands!" (stock): Frenzy
        SAY_UKORZ_AGGRO         = 2,    // "The Sandfury reign supreme!" (stock)
        SAY_UKORZ_KILL_2        = 3,    // "This desert be mine!" (stock)
        SAY_UKORZ_STORM         = 4,    // UK3, Ukorz at full Fury
        SAY_UKORZ_HOLD          = 5,    // UK9 heroic hold
        SAY_UKORZ_CALL          = 6,    // UK10
        EMOTE_UKORZ_STAMP       = 7,    // UK5, at most once every 10 s
    };

    enum RuuzluTexts : std::uint8_t
    {
        SAY_RUUZLU_STORM        = 0,    // UK3, Ruuzlu at full Fury
        SAY_RUUZLU_HOLD         = 1,    // UK9 heroic hold
        SAY_RUUZLU_CALL         = 2,    // UK10
    };

    // Which boss.
    enum class Side : std::uint8_t
    {
        Ukorz = 0,
        Ruuzlu = 1,
    };

    constexpr Side Other(Side side)
    {
        return side == Side::Ukorz ? Side::Ruuzlu : Side::Ukorz;
    }

    constexpr std::size_t Index(Side side)
    {
        return static_cast<std::size_t>(side);
    }

    namespace Tune
    {
        // --- UK1 Fury of the Sands -----------------------------------------------------------------------------------
        inline constexpr std::uint32_t kFuryMaxStacks = 10;
        inline constexpr NH<float> kFuryPartnerPctPerStack{ 4.f, 3.f };     // the partner's health lost per stack
        inline constexpr NH<std::uint32_t> kFuryDamagePctPerStack{ 3, 4 };  // the auras' own amount (ukorz.py)
        inline constexpr NH<std::uint32_t> kFuryFadeMs{ 4000, 5000 };       // a stack off, while the partner is quiet
        inline constexpr std::uint32_t kFuryQuietWindowMs = 4000;           // section 7 #41 A: "in the last 4 s"
        inline constexpr float kFuryQuietPct = 1.f;                         // ...the partner lost under 1%
        inline constexpr std::uint32_t kVengeanceStackMs = 3000;            // UK9 normal: a stack every 3 s

        // --- UK2 Battle Roar -----------------------------------------------------------------------------------------
        inline constexpr std::uint32_t kRoarAtStacks = 5;
        inline constexpr NH<std::uint32_t> kRoarCastMs{ 2500, 2000 };
        inline constexpr std::uint8_t kRoarKickPriority = 3;
        inline constexpr std::uint32_t kRoarBackstopMs = 1000;              // past the cast: the act ends anyway

        // --- UK3 Bladestorm, UK4 its trail (heroic) ------------------------------------------------------------------
        inline constexpr std::uint32_t kStormWindupMs = 2000;
        inline constexpr NH<std::uint32_t> kStormSpinMs{ 6000, 8000 };
        inline constexpr std::uint32_t kStormRoaredSpinMs = 9000;           // heroic: after a Battle Roar landed
        inline constexpr std::uint32_t kStormTickMs = 1000;
        inline constexpr float kStormRadiusYd = 8.f;
        inline constexpr NH<float> kStormTickPct{ 12.f, 15.f };
        // SP gives no speed: 5 yd/s (a player runs 7), a new player every 2 s. G1's drill 8 models the same
        // (MechanicDrill.h kZfStormSpeedYdS): this constant wins, the drill follows it.
        inline constexpr float kStormWalkYdS = 5.f;
        inline constexpr std::uint32_t kStormRepickMs = 2000;
        inline constexpr float kTrailRadiusYd = 4.f;
        inline constexpr float kTrailStepYd = 2.f;                          // one trail circle per 2 yd walked
        inline constexpr std::uint32_t kTrailLifeMs = 15000;
        inline constexpr std::size_t kTrailCap = 40;                        // live trail circles at most

        // --- UK5 Sinking Sands, UK6 Sunk and the rescue, UK11 the sands rise -----------------------------------------
        inline constexpr float kPitRadiusYd = 6.f;
        inline constexpr NH<std::uint32_t> kStampCastMs{ 2000, 1500 };      // the pit's warning
        inline constexpr NH<std::uint32_t> kPitCount{ 1, 2 };
        inline constexpr std::uint32_t kStampFirstMs = 12000;
        inline constexpr NH<std::uint32_t> kStampEveryMs{ 20000, 15000 };
        inline constexpr std::uint32_t kPitLifeMs = 30000;                  // until Frenzy on normal stops the closing
        inline constexpr std::uint32_t kPitTickMs = 1000;
        inline constexpr std::uint32_t kStampEmoteGapMs = 10000;            // the emote at most once every 10 s
        inline constexpr std::uint32_t kRiseWarnMs = 1500;                  // UK11: a pit under every player at once
        inline constexpr std::uint32_t kSunkMs = 8000;
        inline constexpr float kRescueRadiusYd = 3.f;
        inline constexpr std::uint32_t kRescueDwellMs = 2000;

        // --- UK7 Execute of the sunk ---------------------------------------------------------------------------------
        inline constexpr std::uint32_t kExecuteCastMs = 4000;
        inline constexpr NH<float> kExecutePct{ 50.f, 75.f };
        inline constexpr std::uint32_t kExecuteWalkLimitMs = 12000;         // never reached them: give up
        inline constexpr std::uint32_t kExecuteHoldSlackMs = 1000;          // the root outlasts the bar by this much
        inline constexpr std::uint32_t kExecuteBackstopMs = 1500;           // past the bar: the act ends anyway
        inline constexpr float kExecuteReachYd = 4.f;

        // --- UK8 Frenzy, UK9 the hold and Vengeance ------------------------------------------------------------------
        inline constexpr float kFrenzyAtPct = 30.f;                         // normal: Ukorz's 30%
        inline constexpr float kHoldPct = 30.f;                             // heroic: each holds here until both are

        // --- UK10 Call of Sul'thraze ---------------------------------------------------------------------------------
        inline constexpr std::uint32_t kCallCastMs = 10000;
        inline constexpr std::uint32_t kCallBackstopMs = 11000;             // phase 3 starts by then whatever happened

        // --- Phase 3 (heroic): UK12 Lash, UK13 Creeping Sands, the timers --------------------------------------------
        inline constexpr std::uint32_t kLashWarnMs = 2000;
        inline constexpr std::uint32_t kLashFirstMs = 5000;                 // after phase 3's start
        inline constexpr std::uint32_t kLashEveryMs = 10000;
        inline constexpr float kLashRadiusYd = 8.f;
        inline constexpr std::uint32_t kLashMaxJumps = 4;
        inline constexpr float kLashPct = 25.f;
        inline constexpr std::uint32_t kLashDebuffMs = 15000;
        inline constexpr std::int32_t kLashStatPct = 15;                    // the debuff's own amount (ukorz.py)
        inline constexpr std::uint32_t kPhase3StormFirstMs = 12000;
        inline constexpr std::uint32_t kPhase3StormEveryMs = 25000;
        inline constexpr std::uint32_t kPhase3StampFirstMs = 8000;
        inline constexpr float kCreepStartYd = 30.f;
        inline constexpr float kCreepStepYd = 5.f;
        inline constexpr std::uint32_t kCreepStepMs = 20000;
        inline constexpr std::uint32_t kCreepFormWarnMs = 5000;             // the sands rise during the Call
        inline constexpr std::uint32_t kCreepStepWarnMs = 2000;
        inline constexpr std::uint32_t kCreepTickMs = 1000;
        inline constexpr float kCreepPct = 8.f;
        // The donut's outer edge: past every corner of the mesa from the center (kMesaDonutCenter; host-tested
        // against kMesaPolygon). G1's drill 12 uses 45 yd; the mesa's far corners are 47 to 49 yd out.
        inline constexpr float kCreepOuterYd = 60.f;
        inline constexpr std::uint32_t kForeverMs = 600000;                 // a zone the script cancels itself

        // --- UK14 steady pressure ------------------------------------------------------------------------------------
        inline constexpr std::uint32_t kCleaveFirstMinMs = 3000;
        inline constexpr std::uint32_t kCleaveFirstMaxMs = 8000;
        inline constexpr std::uint32_t kCleaveEveryMinMs = 7000;
        inline constexpr std::uint32_t kCleaveEveryMaxMs = 11000;

        // --- Boss data -----------------------------------------------------------------------------------------------
        inline constexpr std::uint32_t kFavorMarginStacks = 3;              // the kill order's hysteresis
        inline constexpr float kFavorHealthGuardPct = 8.f;                  // ...under BM's KillTogether 10%
        inline constexpr float kKillTogetherPct = 10.f;
        inline constexpr std::uint32_t kKillLineGapMs = 5000;

        // Rule 32: no hit under the warning floor (SYS 4).
        static_assert(kStormWindupMs >= ZulFarrakRework::kWarningFloorMs, "Bladestorm's wind-up");
        static_assert(kStampCastMs.normal >= ZulFarrakRework::kWarningFloorMs, "the stamp, normal");
        static_assert(kStampCastMs.heroic >= ZulFarrakRework::kWarningFloorMs, "the stamp, heroic");
        static_assert(kRiseWarnMs >= ZulFarrakRework::kWarningFloorMs, "the sands rise");
        static_assert(kLashWarnMs >= ZulFarrakRework::kWarningFloorMs, "the Lash");
        static_assert(kCreepStepWarnMs >= ZulFarrakRework::kWarningFloorMs, "a Creeping Sands step");
        static_assert(kExecuteCastMs >= ZulFarrakRework::kWarningFloorMs, "the Execute bar");
        static_assert(kRescueDwellMs < kSunkMs, "a rescue fits in the root");
        static_assert(kCreepStepMs * 6 == 120000 && kCreepStartYd == 6 * kCreepStepYd, "shut at 120 s (UK13)");
        static_assert(kRoarAtStacks < kFuryMaxStacks, "the roar comes before the full meter");
        static_assert(kFavorHealthGuardPct < kKillTogetherPct, "the AI turns before BM's KillTogether drops one");
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UK1 the meter
    // ----------------------------------------------------------------------------------------------------------------

    // The partner's health losses in the last kFuryQuietWindowMs (section 7 #41 A).
    class LossWindow
    {
    public:
        void Add(std::uint64_t nowMs, float pct)
        {
            if (pct > 0.f)
                _losses.emplace_back(nowMs, pct);
            Trim(nowMs);
        }

        float Sum(std::uint64_t nowMs)
        {
            Trim(nowMs);
            float sum = 0.f;
            for (auto const& loss : _losses)
                sum += loss.second;
            return sum;
        }

        void Clear() { _losses.clear(); }

    private:
        void Trim(std::uint64_t nowMs)
        {
            while (!_losses.empty() && _losses.front().first + Tune::kFuryQuietWindowMs <= nowMs)
                _losses.pop_front();
        }

        std::deque<std::pair<std::uint64_t, float>> _losses;
    };

    struct FuryEvents
    {
        std::uint32_t gained = 0;
        std::uint32_t faded = 0;
        bool roarDue = false;           // at kRoarAtStacks or more, below full, no roar yet this fill
        bool full = false;              // at kFuryMaxStacks
    };

    // One boss's meter. The AI feeds it the partner's health lost since the last tick (in percent of the partner's
    // maximum health; any damage counts: section 7 #10 A, ruling 34) and applies the stack count to the aura.
    class FuryMeter
    {
    public:
        void Reset()
        {
            Empty();
            _window.Clear();
        }

        // One tick. `partnerUp`: the partner stands (alive, not lying fallen). `vengeance`: with the partner down the
        // meter fills by itself (normal); false (heroic) leaves it as it is.
        FuryEvents Update(std::uint64_t nowMs, std::uint32_t diffMs, float partnerLostPct, bool partnerUp,
            bool heroic, bool vengeance)
        {
            FuryEvents events;
            if (!partnerUp)
            {
                _fadeClockMs = 0;
                if (vengeance)
                {
                    _vengeanceClockMs += diffMs;
                    while (_vengeanceClockMs >= Tune::kVengeanceStackMs)
                    {
                        _vengeanceClockMs -= Tune::kVengeanceStackMs;
                        events.gained += Gain();
                    }
                }
            }
            else
            {
                _vengeanceClockMs = 0;
                float const perStack = Tune::kFuryPartnerPctPerStack(heroic);
                if (partnerLostPct > 0.f)
                {
                    _carryPct += partnerLostPct;
                    while (_carryPct >= perStack)
                    {
                        _carryPct -= perStack;
                        events.gained += Gain();
                    }
                    _window.Add(nowMs, partnerLostPct);
                }
                if (_window.Sum(nowMs) < Tune::kFuryQuietPct)
                {
                    _fadeClockMs += diffMs;
                    std::uint32_t const fadeMs = Tune::kFuryFadeMs(heroic);
                    while (_fadeClockMs >= fadeMs)
                    {
                        _fadeClockMs -= fadeMs;
                        if (_stacks > 0)
                        {
                            --_stacks;
                            ++events.faded;
                        }
                    }
                }
                else
                    _fadeClockMs = 0;
            }
            events.full = _stacks >= Tune::kFuryMaxStacks;
            events.roarDue = !_roarUsed && _stacks >= Tune::kRoarAtStacks && !events.full;
            return events;
        }

        std::uint32_t Stacks() const { return _stacks; }
        bool RoarUsed() const { return _roarUsed; }
        float CarryPct() const { return _carryPct; }

        // The roar was cast (landed, kicked or refused): one per fill.
        void UseRoar() { _roarUsed = true; }
        // A landed roar: the meter is full.
        void Fill() { _stacks = Tune::kFuryMaxStacks; }
        // The Bladestorm: back to 0, a new fill (a roar may come again).
        void Empty()
        {
            _stacks = 0;
            _carryPct = 0.f;
            _fadeClockMs = 0;
            _vengeanceClockMs = 0;
            _roarUsed = false;
        }
        // `.dbtest zf ukorz fury`.
        void Set(std::uint32_t stacks) { _stacks = std::min(stacks, Tune::kFuryMaxStacks); }

    private:
        std::uint32_t Gain()
        {
            if (_stacks >= Tune::kFuryMaxStacks)
                return 0;
            ++_stacks;
            return 1;
        }

        std::uint32_t _stacks = 0;
        float _carryPct = 0.f;
        std::uint32_t _fadeClockMs = 0;
        std::uint32_t _vengeanceClockMs = 0;
        bool _roarUsed = false;
        LossWindow _window;
    };

    // The aura's damage factor for a stack count: 1 + stacks x 3% (heroic 4%). The script's own hits (Execute) carry
    // IGNORE_CASTER_MODIFIERS and take it from here.
    constexpr float FuryFactor(std::uint32_t stacks, bool heroic)
    {
        return 1.f + static_cast<float>(stacks * Tune::kFuryDamagePctPerStack(heroic)) / 100.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data: the kill order's pick (UK1 bots)
    // ----------------------------------------------------------------------------------------------------------------

    struct FavorView
    {
        bool up[2] = { true, true };            // alive, not lying fallen
        bool held[2] = { false, false };        // heroic: at the 30% line, waiting for the other
        float healthPct[2] = { 100.f, 100.f };
        std::uint32_t fury[2] = { 0, 0 };
    };

    // Hitting a boss feeds his partner's meter, so the favored boss is the one whose partner's Fury is lower. It
    // changes when the current one's partner leads by kFavorMarginStacks or more (no flapping on a stack), never to a
    // boss more than kFavorHealthGuardPct below the other (BM's KillTogether would drop it at 10%: the AI turns first),
    // and never to a held one while the other is not. nullopt: neither stands.
    inline std::optional<Side> PickFavored(std::optional<Side> current, FavorView const& v)
    {
        bool const u = v.up[Index(Side::Ukorz)];
        bool const r = v.up[Index(Side::Ruuzlu)];
        if (!u && !r)
            return std::nullopt;
        if (u != r)
            return u ? Side::Ukorz : Side::Ruuzlu;
        bool const uHeld = v.held[Index(Side::Ukorz)];
        bool const rHeld = v.held[Index(Side::Ruuzlu)];
        if (uHeld != rHeld)
            return uHeld ? Side::Ruuzlu : Side::Ukorz;
        // No pick yet: the one whose partner has less Fury (Ruuzlu on a tie: Ukorz's meter is the one he feeds).
        Side const cur = current.value_or(v.fury[Index(Side::Ukorz)] <= v.fury[Index(Side::Ruuzlu)]
            ? Side::Ruuzlu : Side::Ukorz);
        Side const other = Other(cur);
        float const curPct = v.healthPct[Index(cur)];
        float const otherPct = v.healthPct[Index(other)];
        if (curPct < otherPct - Tune::kFavorHealthGuardPct)
            return other;       // the health guard: keep the two together
        std::uint32_t const curFeeds = v.fury[Index(other)];   // hitting `cur` feeds `other`
        std::uint32_t const otherFeeds = v.fury[Index(cur)];
        bool const switchByFury = curFeeds >= otherFeeds + Tune::kFavorMarginStacks;
        if (switchByFury && !(otherPct < curPct - Tune::kFavorHealthGuardPct))
            return other;
        return cur;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UK7 who executes (section 7 #42 A)
    // ----------------------------------------------------------------------------------------------------------------

    struct ExecutionerView
    {
        bool ruuzluStands = false;      // alive and in the fight
        bool ruuzluFree = false;        // no act running (no storm, roar, execute)
        bool ukorzStands = false;       // alive, not fallen
        bool ukorzFree = false;         // no act running (no storm, roar, execute, stamp, lash, the Call)
        bool heroicPhaseOne = false;    // both executioners share the sunk
    };

    inline std::optional<Side> ExecutionerFor(ExecutionerView const& v)
    {
        if (v.ruuzluStands)
        {
            if (v.ruuzluFree)
                return Side::Ruuzlu;
            if (v.heroicPhaseOne && v.ukorzStands && v.ukorzFree)
                return Side::Ukorz;
            return std::nullopt;        // normal: Ruuzlu takes them in order
        }
        if (v.ukorzStands && v.ukorzFree)
            return Side::Ukorz;
        return std::nullopt;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UK9 the heroic hold, UK10 the transition
    // ----------------------------------------------------------------------------------------------------------------

    // The health at the hold line (rounded up: never under the line).
    constexpr std::uint32_t HoldHealth(std::uint32_t maxHealth, float pct)
    {
        std::uint64_t const scaled = static_cast<std::uint64_t>(maxHealth) * static_cast<std::uint64_t>(pct * 100.f);
        return static_cast<std::uint32_t>((scaled + 9999) / 10000);
    }

    // The damage a held boss takes: what keeps it at or above the line (0 once it is there).
    constexpr std::uint32_t HoldDamage(std::uint32_t health, std::uint32_t maxHealth, std::uint32_t damage, float pct)
    {
        std::uint32_t const line = HoldHealth(maxHealth, pct);
        if (health <= line)
            return 0;
        return std::min(damage, health - line);
    }

    // At the line (the hold's test for the transition): alive, health no more than the line.
    constexpr bool AtHold(std::uint32_t health, std::uint32_t maxHealth, float pct)
    {
        return health > 0 && health <= HoldHealth(maxHealth, pct);
    }

    // UK10: Ukorz takes what life Ruuzlu had left, never past his own maximum.
    constexpr std::uint32_t CalledHealth(std::uint32_t ukorz, std::uint32_t ruuzlu, std::uint32_t ukorzMax)
    {
        std::uint64_t const sum = static_cast<std::uint64_t>(ukorz) + ruuzlu;
        return static_cast<std::uint32_t>(std::min<std::uint64_t>(sum, ukorzMax));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UK12 the Lash's chain
    // ----------------------------------------------------------------------------------------------------------------

    // The order the lash strikes: `first`, then (breadth first) every other point within `radius` of a struck one,
    // `maxJumps` more at most. Indices into `points`.
    inline std::vector<std::size_t> LashChain(std::vector<Vec2> const& points, std::size_t first, float radius,
        std::uint32_t maxJumps)
    {
        std::vector<std::size_t> struck;
        if (first >= points.size())
            return struck;
        std::vector<bool> taken(points.size(), false);
        struck.push_back(first);
        taken[first] = true;
        std::size_t const cap = static_cast<std::size_t>(maxJumps) + 1;
        for (std::size_t i = 0; i < struck.size() && struck.size() < cap; ++i)
        {
            Vec2 const from = points[struck[i]];
            for (std::size_t j = 0; j < points.size() && struck.size() < cap; ++j)
                if (!taken[j] && DungeonKit::Distance(from, points[j]) <= radius)
                {
                    taken[j] = true;
                    struck.push_back(j);
                }
        }
        return struck;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UK13 Creeping Sands
    // ----------------------------------------------------------------------------------------------------------------

    // The steps taken `sincePhaseThreeMs` after phase 3 began (0 = the 30 yd it formed at during the Call, 6 = shut).
    constexpr std::uint32_t CreepStep(std::uint64_t sincePhaseThreeMs)
    {
        std::uint64_t const steps = sincePhaseThreeMs / Tune::kCreepStepMs;
        std::uint64_t const last = static_cast<std::uint64_t>(Tune::kCreepStartYd / Tune::kCreepStepYd);
        return static_cast<std::uint32_t>(std::min(steps, last));
    }

    // The safe circle's radius after `step` steps.
    constexpr float CreepInnerYd(std::uint32_t step)
    {
        float const inner = Tune::kCreepStartYd - static_cast<float>(step) * Tune::kCreepStepYd;
        return inner > 0.f ? inner : 0.f;
    }

    // The bots' planned spots while the donut is up: inside its safe circle (a yard in), never under 3 yd.
    constexpr float CreepBoundsYd(float innerYd)
    {
        return std::max(3.f, innerYd - 1.f);
    }

    // F-1 MI-4: the safe circle of `boundsYd` round kMesaDonutCenter, clipped to the mesa's floor (kMesaPolygon), as
    // one polygon (BM's SpotBounds areas are a union, so the clip is done here). The circle is a regular
    // kCreepSafeSides-gon inscribed in it; Sutherland-Hodgman clips the non-convex mesa by that convex polygon (where
    // the mesa leaves and re-enters the circle the result runs along the circle's edge both ways: zero width, so a
    // point test is unchanged). At 29 yd (the circle at the Call) 11% of the bare circle lies past the walls; from
    // 19 yd none does and this is the polygon of the circle alone.
    inline constexpr std::size_t kCreepSafeSides = 32;

    inline std::vector<DungeonKit::Vec2> CreepSafeFloor(float boundsYd)
    {
        using DungeonKit::Vec2;
        Vec2 const c = ZulFarrakRework::kMesaDonutCenter.XY();
        std::vector<Vec2> clip;
        clip.reserve(kCreepSafeSides);
        for (std::size_t i = 0; i < kCreepSafeSides; ++i)
        {
            float const a = 6.2831853f * static_cast<float>(i) / static_cast<float>(kCreepSafeSides);
            clip.push_back({ c.x + boundsYd * std::cos(a), c.y + boundsYd * std::sin(a) });     // counter-clockwise
        }
        std::vector<Vec2> out(ZulFarrakRework::kMesaPolygon.begin(), ZulFarrakRework::kMesaPolygon.end());
        for (std::size_t e = 0; e < clip.size() && !out.empty(); ++e)
        {
            Vec2 const a = clip[e];
            Vec2 const b = clip[(e + 1) % clip.size()];
            auto inside = [a, b](Vec2 p) { return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x) >= 0.f; };
            auto cross = [a, b](Vec2 p, Vec2 q)
            {
                float const dx = q.x - p.x;
                float const dy = q.y - p.y;
                float const den = (b.x - a.x) * dy - (b.y - a.y) * dx;
                float const t = std::fabs(den) < 1e-6f ? 0.f
                    : ((b.x - a.x) * (a.y - p.y) - (b.y - a.y) * (a.x - p.x)) / den;
                return Vec2{ p.x + t * dx, p.y + t * dy };
            };
            std::vector<Vec2> const in = std::move(out);
            out.clear();
            for (std::size_t i = 0; i < in.size(); ++i)
            {
                Vec2 const cur = in[i];
                Vec2 const prev = in[(i + in.size() - 1) % in.size()];
                bool const curIn = inside(cur);
                bool const prevIn = inside(prev);
                if (curIn)
                {
                    if (!prevIn)
                        out.push_back(cross(prev, cur));
                    out.push_back(cur);
                }
                else if (prevIn)
                    out.push_back(cross(prev, cur));
            }
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UK4 the trail, the beats
    // ----------------------------------------------------------------------------------------------------------------

    // Trail circles due after `walkedYd` since the last one (one per kTrailStepYd).
    constexpr std::uint32_t TrailDrops(float walkedYd)
    {
        return walkedYd >= Tune::kTrailStepYd ? static_cast<std::uint32_t>(walkedYd / Tune::kTrailStepYd) : 0;
    }

    // RB-17 / L8: a beat that fired at `now` (it was due at `due`) is next due here.
    constexpr std::uint64_t NextDue(std::uint64_t due, std::uint64_t period, std::uint64_t now)
    {
        return std::max(due + period, now + period / 2);
    }
}

#endif
