/*
 * mod-dungeon-bosses, Gnomeregan D3: Electrocutioner 6000 (6235), the pure, host-testable part (no engine headers).
 * The spell ids of kSpellsElectrocutioner (214380-214419), the registry tags (the drill's block 40-49, LESSONS A.3 #4),
 * the text groups, the tuning (`namespace Tune`, handoff section 3.5 rule 24), and the rules a host test pins for the
 * boss and the hard mode alike: the Voltage meter and its Justice cadence (VoltageClock, the VoltageMeter machine's
 * pure half, GnomereganMachines.h), the Justice shape in turn, the damage multiplier, the Chain Bolt's jumps and their
 * percents, the Static meter and its discharge partner, the donut's outer reach over a floor and the blast ring.
 * Build spec: SP 803-1006 (EL1-EL6, Build spec 958), rulings 21-24; handoff section 3.5 row D3 and its kick and dispel
 * table, sections 3.6, 3.8 (the platform), 3.9 row 5, section 7 #9 A, #12 A, #20 A, #36-#38 A, section 10. Tested by
 * tests/gnomer_electro_test.cpp. Health is GnomereganRework.h Health: never restated here.
 *
 * No stock code is mirrored: the stock unit ran SmartAI 6235 (dropped by rev_skeleton_gnomeregan.sql); its spells are
 * re-made as copies in the slice (rule 16), its numbers read from the stock DBC (handoff section 3.6).
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_ELECTROCUTIONER_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_ELECTROCUTIONER_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "GnomereganRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace GnomerElectro
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using GnomereganRework::kWarningFloorMs;

    // Every spell of this WP sits in this slice (GnomereganRework.h; ids.yaml reservation `gnomeregan`).
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsElectrocutioner;

    // Declared in apps/dbc-tools source/npcs/gnomeregan/electrocutioner.py (same ids; lib/test_gnomeregan_
    // electrocutioner.py pins each name to its offset).
    enum ElectroSpells : std::uint32_t
    {
        SPELL_VOLTAGE               = kSpellSlice.first + 0,    // EL1 the meter on him: a DUMMY aura, 1 stack = 1,000 V
        SPELL_VOLTAGE_CHARGED       = kSpellSlice.first + 1,    // EL1 the brighter crackle at 3 stacks and up (a look)
        SPELL_JUSTICE_BAR           = kSpellSlice.first + 2,    // EL2 the 4 s bar: Physical, InterruptFlags 0
        SPELL_JUSTICE_HIT           = kSpellSlice.first + 3,    // EL2 the donut or circle: resolve copy (Nature)
        SPELL_JUSTICE_BLAST         = kSpellSlice.first + 4,    // EL2 the blast look, cast by a blast stalker
        SPELL_MEGAVOLT_BAR          = kSpellSlice.first + 5,    // EL3 the 2 s bar: Physical, InterruptFlags 0
        SPELL_MEGAVOLT_HIT          = kSpellSlice.first + 6,    // EL3 the cone: resolve copy (Nature)
        SPELL_CHAIN_BOLT            = kSpellSlice.first + 7,    // EL4 the 2.5 s cast: Nature, kickable (the reward)
        SPELL_CHAIN_BOLT_HIT        = kSpellSlice.first + 8,    // EL4 each struck player: resolve copy (Nature)
        SPELL_SHOCK                 = kSpellSlice.first + 9,    // EL5 the instant: Nature, a kick's lockout stops it
        SPELL_SHOCK_HIT             = kSpellSlice.first + 10,   // EL5 the hit: resolve copy (Nature)
        SPELL_STATIC                = kSpellSlice.first + 11,   // EL6 heroic: the stacks on a player (DUMMY aura)
        SPELL_DISCHARGE_HIT         = kSpellSlice.first + 12,   // EL6 the discharge: resolve copy (Nature)
        SPELL_DISCHARGE_LOOK        = kSpellSlice.first + 13,   // EL6 the discharge look, cast by a blast stalker
        // kSpellSlice.first + 14 .. kSpellSlice.last (214394-214419): spare
    };
    std::uint32_t constexpr kSpellCount = 14;
    static_assert(kSpellSlice.Contains(SPELL_VOLTAGE) && kSpellSlice.Contains(SPELL_DISCHARGE_LOOK),
        "Electrocutioner's spells sit in the slice");

    // Registry tags: the gnomeregan-shapes drill's Electrocutioner block (BM MechanicDrill.h kGnTag* 40-49, WP-G1;
    // change both together, LESSONS A.3 #4). 43 (a Chain Bolt nobody kicked), 47 (the healer's band) and 48 (a
    // carrier's dodge) are the drill's own judges: the live fight registers nothing under them.
    enum ElectroTags : std::uint32_t
    {
        TAG_JUSTICE_DONUT       = 40,   // EL2: the floor outside 8 yd of him
        TAG_JUSTICE_CIRCLE      = 41,   // EL2 heroic: the 15 yd circle on him, in turn with the donut
        TAG_MEGAVOLT            = 42,   // EL3: the 40 degree, 30 yd cone at a player
        TAG_CHAIN_BOLT_KICK     = 43,   // drill only
        TAG_CHAIN_BOLT          = 44,   // EL4 heroic: the 10 yd spread and the jumps' hits
        TAG_CHAIN_BOLT_NORMAL   = 45,   // EL4 normal: the 6 yd spread and the jumps' hits
        TAG_DISCHARGE           = 46,   // EL6 heroic: a Static discharge (the carrier and the nearest ally)
        TAG_BAND                = 47,   // drill only
        TAG_CARRIER_DODGE       = 48,   // drill only
        TAG_SHOCK               = 49,   // EL5: the Shock hit (not drilled)
    };

    // The tag table the drill shares (lib/test_gnomeregan_electrocutioner.py diffs it against MechanicDrill.h when
    // BM_SRC is set).
    struct DrillTag
    {
        std::uint32_t tag;
        char const* drillName;
    };
    inline constexpr std::array<DrillTag, 9> kDrillTags{ {
        { TAG_JUSTICE_DONUT, "kGnTagJusticeDonut" },
        { TAG_JUSTICE_CIRCLE, "kGnTagJusticeCircle" },
        { TAG_MEGAVOLT, "kGnTagMegavolt" },
        { TAG_CHAIN_BOLT_KICK, "kGnTagChainBoltKick" },
        { TAG_CHAIN_BOLT, "kGnTagChainBolt" },
        { TAG_CHAIN_BOLT_NORMAL, "kGnTagChainBoltNormal" },
        { TAG_DISCHARGE, "kGnTagDischarge" },
        { TAG_BAND, "kGnTagBand" },
        { TAG_CARRIER_DODGE, "kGnTagCarrierDodge" },
    } };

    // Texts (creature_text 6235). Group 0 is the stock row ("Electric justice!", sound 5811, broadcast 6177), kept as
    // it is (rule 35: stock groups stay); SP's other lines are new rows after it (rev_electrocutioner_gnomeregan.sql):
    // SP line 0 is group 1, SP lines 2 and 3 keep their numbers.
    enum ElectroTexts : std::uint8_t
    {
        SAY_JUSTICE             = 0,    // SP line 1: "Electric justice!" (yell, stock; EL2)
        SAY_AGGRO               = 1,    // SP line 0: "Court is in session!" (yell, new)
        EMOTE_JUSTICE_DONUT     = 2,    // SP line 2: "%s reaches 6000 volts! Get under the machine!" (41)
        EMOTE_JUSTICE_CIRCLE    = 3,    // SP line 3, heroic: "%s overloads! Get away from the machine!" (41)
    };

    // `.dbtest gnomer electro <mechanic>` (DoAction) and the test reads (GetData) of the boss AI.
    enum ElectroActions : std::int32_t
    {
        ACTION_TEST_JUSTICE     = 1,    // the meter to the next Justice now
        ACTION_TEST_MEGAVOLT    = 2,
        ACTION_TEST_CHAIN_BOLT  = 3,
        ACTION_TEST_SHOCK       = 4,
        ACTION_TEST_VOLTAGE     = 5,    // +1 stack
        ACTION_TEST_STATIC      = 6,    // heroic: every carrier one yard short of the discharge
    };

    enum ElectroData : std::uint32_t
    {
        DATA_TEST_ENGAGED       = 1,
        DATA_TEST_STACKS        = 2,
        DATA_TEST_JUSTICES      = 3,
        DATA_TEST_MEGAVOLTS     = 4,
        DATA_TEST_CHAIN_BOLTS   = 5,
        DATA_TEST_KICKED        = 6,
        DATA_TEST_DISCHARGES    = 7,
    };

    std::uint32_t constexpr kPointCenter = 1;   // MovePoint id of the walk to the platform's center

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP Build spec 958-1006 and "Tuning starting points"; rulings 22-24; section 7 #37 A: the guesses as
    // written; rule 24)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // EL1 Voltage: 1,000 volts a stack, +1 every 5 s by itself (ruling 23); +1 per player a Megavolt hits (heroic
        // +2), +1 per Chain Bolt jump, heroic +1 per Static discharge. Normal: back to 0 after the Justice, no climb
        // during its bar or for 10 s after it (the group failure cap: executions at least 25 s apart). Heroic: never
        // resets, no pause, +3% to all his lightning per stack, no cap (ruling 23: down from 5%).
        std::uint32_t constexpr kVoltageTickMs = 5000;
        std::uint32_t constexpr kJusticeEvery = 6;
        inline constexpr NH<std::uint32_t> kJusticePauseAfterMs{ 10000, 0 };
        // SP EL2 "executions are at least 25 sec apart however badly it goes" (normal): the pause alone allows 19 s
        // (a Megavolt through five players right after it), so the gap between two bars' starts is also a floor.
        inline constexpr NH<std::uint32_t> kJusticeMinGapMs{ 25000, 0 };
        inline constexpr NH<float> kLightningPctPerStack{ 0.f, 3.f };
        std::uint32_t constexpr kVoltageStackLimit = 255;       // the client's counter (rule 25)
        std::uint32_t constexpr kVoltageChargedAt = 3;          // V: SV 37 at 1-2 stacks, SV 7867 from 3
        std::uint32_t constexpr kReassertMs = 1000;             // rule 25

        // EL2 Electric Justice: a 4 s bar (Physical, InterruptFlags 0: section 7 #9 A), the yell (group 0) and the
        // emote; the donut safe within 8 yd of him over the platform; heroic in turn with a 15 yd circle on him (donut
        // first), the emote naming which. 75% of the reference row (the tank row on the tank), no Weakened; heroic
        // plus Voltage.
        std::uint32_t constexpr kJusticeCastMs = 4000;
        static_assert(kJusticeCastMs >= kWarningFloorMs, "Justice meets the warning floor");
        float constexpr kJusticeSafeYd = 8.f;
        float constexpr kJusticeCircleYd = 15.f;
        float constexpr kJusticePct = 75.f;
        float constexpr kJusticeOuterMarginYd = 2.f;            // past the floor's farthest point from him
        std::uint32_t constexpr kJusticeLandGraceMs = 1500;     // no resolve this long after the bar: land without one
        std::uint32_t constexpr kBarRetryMs = 1000;             // a refused bar is retried (rule 15)
        // The blast look (SV 3 on a blast stalker): six points on a ring through the donut, one on him for the circle.
        std::uint32_t constexpr kBlastPoints = 6;
        float constexpr kBlastRingYd = 14.f;
        std::uint32_t constexpr kBlastStalkerMs = 3000;
        // Heroic: thresholds crossed while a bar runs fold into it (no back-to-back execution). Designer question.
        bool constexpr kFoldThresholdsDuringBar = true;

        // EL3 Megavolt: every 12 s (first at 10 s, a guess) he turns to a random player on the platform, tank
        // included, and charges 2 s (a Physical bar, not interruptible: the dodge); a 40 degree, 30 yd cone fixed at
        // the bar's start. Normal one player, 40% and Weakened, +1 V per player hit; heroic two players at once, 60%
        // and Weakened (plus Voltage), +2 V per player hit.
        std::uint32_t constexpr kMegavoltFirstMs = 10000;
        std::uint32_t constexpr kMegavoltEveryMs = 12000;
        std::uint32_t constexpr kMegavoltCastMs = 2000;
        static_assert(kMegavoltCastMs >= kWarningFloorMs, "Megavolt meets the warning floor");
        float constexpr kMegavoltAngleDeg = 40.f;
        float constexpr kMegavoltLengthYd = 30.f;
        inline constexpr NH<float> kMegavoltPct{ 40.f, 60.f };
        inline constexpr NH<std::uint32_t> kMegavoltTargets{ 1, 2 };
        inline constexpr NH<std::uint32_t> kMegavoltVoltsPerHit{ 1, 2 };

        // EL4 Chain Bolt: first at 3 s, then every 20 s, a 2.5 s Nature cast at a random player on the platform, tank
        // included (kickable: a kick stops it, no hit and no charge). It strikes the target, then jumps to the
        // nearest player within 6 yd (heroic 10) of the last one struck, at most 2 jumps (heroic no limit), +1 V a
        // jump. Normal 20% on each; heroic 40% on the target and each jump 25% more than the last (plus Voltage).
        // No Weakened (a spacing failure the group shares).
        std::uint32_t constexpr kChainFirstMs = 3000;
        std::uint32_t constexpr kChainEveryMs = 20000;
        std::uint32_t constexpr kChainCastMs = 2500;
        static_assert(kChainCastMs >= kWarningFloorMs, "Chain Bolt meets the warning floor");
        inline constexpr NH<float> kChainJumpYd{ 6.f, 10.f };
        inline constexpr NH<std::uint32_t> kChainMaxJumps{ 2, 0 };     // 0: no limit
        inline constexpr NH<float> kChainPct{ 20.f, 40.f };
        inline constexpr NH<float> kChainJumpGrowth{ 1.f, 1.25f };
        std::uint32_t constexpr kChainVoltsPerJump = 1;
        std::uint8_t constexpr kChainKickPriority = 2;          // the descriptor's interrupt entry (expected on H)

        // EL5 Shock: first at 6 s (a guess), then every 8 s, an instant Nature cast at a random player within 20 yd
        // (a kick's Nature lockout swallows it: the reward). 10% (heroic 15% plus Voltage); no charge.
        std::uint32_t constexpr kShockFirstMs = 6000;
        std::uint32_t constexpr kShockEveryMs = 8000;
        float constexpr kShockRangeYd = 20.f;
        inline constexpr NH<float> kShockPct{ 10.f, 15.f };

        // EL6 Static (heroic): every yard a player moves (horizontal, section 7 #38 A d) adds 1; standing still drains
        // 2 a second. At 20 the player discharges: 40% to them (with Weakened) and to the nearest ally within 10 yd
        // (plus Voltage), +1 V to him, and their Static resets. A step longer than kStaticMaxStepYd in one sample is
        // a teleport or a snap-back and adds nothing.
        std::uint32_t constexpr kStaticSampleMs = 250;
        // STAGE-R-1-A DQ2: the meter counts from 5 s after the pull (walking in and taking the band is free), and only
        // on the platform (R-1-A m4: a player who fell off pays the fall, not the group's Voltage).
        std::uint32_t constexpr kStaticGraceMs = 5000;
        float constexpr kStaticPerYd = 1.f;
        float constexpr kStaticDrainPerSec = 2.f;
        float constexpr kStaticDischargeAt = 20.f;
        float constexpr kStaticStillYd = 0.1f;                  // less than this in a sample is standing still
        float constexpr kStaticMaxStepYd = 8.f;                 // 32 yd/s: a teleport, not a run
        float constexpr kDischargePct = 40.f;
        float constexpr kDischargeAllyYd = 10.f;
        std::uint32_t constexpr kDischargeVolts = 1;
        // BM-G (section 7 #12 A): a bot with more than 12 Static makes no optional move; ranged bots prefer 11 to
        // 12 yd from him (heroic only, BM-G Q1; healers included, Q2).
        std::uint32_t constexpr kStaticBotStandAbove = 12;
        float constexpr kRangedBandMinYd = 11.f;
        float constexpr kRangedBandMaxYd = 12.f;

        // Section 7 #20 A: he walks to the platform's center at the pull and is held there (a root by SetControlled,
        // rule 8). A walk that does not arrive in kCenterWalkMs is finished by a teleport (LESSONS A.2 #11).
        float constexpr kCenterArriveYd = 1.f;
        std::uint32_t constexpr kCenterWalkMs = 5000;
        // RB-4: a held boss answers. When his victim is out of his melee reach for kNoReachGraceMs, he Shocks it
        // every kNoReachShockMs (the Shock spell and numbers). A named switch (not in the spec).
        bool constexpr kNoReachShock = true;
        std::uint32_t constexpr kNoReachGraceMs = 5000;
        std::uint32_t constexpr kNoReachShockMs = 3000;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Beats: RB-17, no beat starves another. The next due time after a beat that was due at `due` and fired at `now`.
    // ----------------------------------------------------------------------------------------------------------------
    constexpr std::uint32_t NextDue(std::uint32_t due, std::uint32_t now, std::uint32_t period)
    {
        return std::max(due + period, now + period / 2);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EL1 / EL2: the Voltage meter (the VoltageMeter machine's pure half; the hard mode's numbers come in the rules)
    // ----------------------------------------------------------------------------------------------------------------
    struct VoltageRules
    {
        std::uint32_t tickMs = Tune::kVoltageTickMs;
        std::uint32_t every = Tune::kJusticeEvery;
        bool resetAfterJustice = false;
        std::uint32_t pauseAfterMs = 0;
        std::uint32_t minGapMs = 0;         // from one bar's start to the next (0: none)
        bool foldDuringBar = Tune::kFoldThresholdsDuringBar;
    };

    // The next Justice threshold strictly above `stacks` (heroic: 6, 12, 18 ...).
    constexpr std::uint32_t NextJusticeAt(std::uint32_t stacks, std::uint32_t every)
    {
        return every == 0 ? 0 : (stacks / every + 1) * every;
    }

    // 1 + stacks x pct / 100: what every lightning hit is multiplied by (heroic 3% a stack, no cap).
    constexpr float DamageMultiplier(std::uint32_t stacks, float pctPerStack)
    {
        return 1.f + float(stacks) * pctPerStack / 100.f;
    }

    // The look's tier (V): 0 none, 1 the orbs (1-2 stacks), 2 the brighter crackle (3 and up).
    constexpr std::uint32_t VoltageTier(std::uint32_t stacks)
    {
        return stacks == 0 ? 0 : (stacks < Tune::kVoltageChargedAt ? 1 : 2);
    }

    enum class JusticeShape : std::uint8_t
    {
        Donut,      // safe within the hole
        Circle,     // safe outside it (heroic)
    };

    // The shape of Justice number `index` (0-based): the donut first, then in turn when `alternate`.
    constexpr JusticeShape JusticeShapeFor(std::uint32_t index, bool alternate)
    {
        return alternate && (index % 2) == 1 ? JusticeShape::Circle : JusticeShape::Donut;
    }

    // The meter: stacks, the climb, the pause and the Justice cadence. Time comes in through Advance; the engine half
    // (ElectrocutionerMachine.cpp) draws, casts and hits.
    class VoltageClock
    {
    public:
        VoltageClock() = default;
        explicit VoltageClock(VoltageRules rules) : _rules(rules), _tickLeft(rules.tickMs), _nextAt(rules.every) { }

        VoltageRules const& Rules() const { return _rules; }
        std::uint32_t Stacks() const { return _stacks; }
        std::uint32_t Justices() const { return _justices; }
        std::uint32_t PauseLeft() const { return _pauseLeft; }
        std::uint32_t TickLeft() const { return _tickLeft; }
        std::uint32_t NextAt() const { return _nextAt; }
        bool Running() const { return _running; }
        bool Paused() const { return _pauseLeft > 0; }

        // The climb by itself: the pause runs down first (the tick restarts when it ends), then one stack a tick.
        // Returns the stacks gained.
        std::uint32_t Advance(std::uint32_t diff)
        {
            _gapLeft = _gapLeft > diff ? _gapLeft - diff : 0;
            if (_rules.tickMs == 0)
                return 0;
            if (_pauseLeft > 0)
            {
                if (diff < _pauseLeft)
                {
                    _pauseLeft -= diff;
                    return 0;
                }
                diff -= _pauseLeft;
                _pauseLeft = 0;
                _tickLeft = _rules.tickMs;
            }
            std::uint32_t gained = 0;
            while (diff >= _tickLeft)
            {
                diff -= _tickLeft;
                _tickLeft = _rules.tickMs;
                ++gained;
            }
            _tickLeft -= diff;
            return Grow(gained);
        }

        // A mistake's charge: refused while paused. Returns the stacks gained.
        std::uint32_t Add(std::uint32_t n)
        {
            if (_pauseLeft > 0)
                return 0;
            return Grow(n);
        }

        // The floor between two bars' starts (normal Electrocutioner; see Tune::kJusticeMinGapMs).
        void SetMinGap(std::uint32_t ms) { _rules.minGapMs = ms; }

        // No climb for `ms` (a longer pause already running is kept).
        void Pause(std::uint32_t ms) { _pauseLeft = std::max(_pauseLeft, ms); }

        bool JusticeDue() const { return !_running && _rules.every > 0 && _stacks >= _nextAt && _gapLeft == 0; }
        std::uint32_t GapLeft() const { return _gapLeft; }

        // The bar starts: normal pauses for the bar and the rest after it; heroic aims at the next threshold.
        void StartJustice(std::uint32_t castMs)
        {
            _running = true;
            _gapLeft = _rules.minGapMs;
            if (_rules.pauseAfterMs > 0 || _rules.resetAfterJustice)
                Pause(castMs + _rules.pauseAfterMs);
            if (!_rules.resetAfterJustice)
                _nextAt = NextJusticeAt(_stacks, _rules.every);
        }

        // It lands (or its zone is gone): normal back to 0; heroic the next threshold (folded past any the bar
        // crossed when foldDuringBar).
        void LandJustice()
        {
            if (!_running)
                return;
            _running = false;
            ++_justices;
            if (_rules.resetAfterJustice)
            {
                _stacks = 0;
                _nextAt = _rules.every;
            }
            else if (_rules.foldDuringBar)
                _nextAt = std::max(_nextAt, NextJusticeAt(_stacks, _rules.every));
        }

        // The stacks still missing to the next Justice (0: due or running).
        std::uint32_t ToNext() const { return _running || _stacks >= _nextAt ? 0 : _nextAt - _stacks; }

        void Reset() { *this = VoltageClock(_rules); }

    private:
        std::uint32_t Capped(std::uint32_t stacks) const
        {
            // Normal never shows more than the threshold (it resets there); the client counter caps at 255.
            if (_rules.resetAfterJustice && _rules.every > 0)
                stacks = std::min(stacks, _rules.every);
            return std::min(stacks, Tune::kVoltageStackLimit);
        }

        std::uint32_t Grow(std::uint32_t n)
        {
            std::uint32_t const before = _stacks;
            _stacks = Capped(_stacks + n);
            return _stacks - before;
        }

        VoltageRules _rules{};
        std::uint32_t _stacks = 0;
        std::uint32_t _tickLeft = Tune::kVoltageTickMs;
        std::uint32_t _pauseLeft = 0;
        std::uint32_t _gapLeft = 0;
        std::uint32_t _nextAt = Tune::kJusticeEvery;
        std::uint32_t _justices = 0;
        bool _running = false;
    };

    // The boss's rules by difficulty.
    inline VoltageRules BossVoltageRules(bool heroic)
    {
        VoltageRules r;
        r.tickMs = Tune::kVoltageTickMs;
        r.every = Tune::kJusticeEvery;
        r.resetAfterJustice = !heroic;
        r.pauseAfterMs = Tune::kJusticePauseAfterMs(heroic);
        r.minGapMs = Tune::kJusticeMinGapMs(heroic);
        return r;
    }

    // The farthest a floor reaches from `from` (the donut's outer edge): polygon and box corners, a circle's far side.
    inline float FarthestReach(DungeonKit::Arena const& floor, Vec2 from)
    {
        float best = 0.f;
        for (DungeonKit::ArenaRegion const& r : floor.regions)
        {
            switch (r.kind)
            {
                case DungeonKit::ArenaRegion::Kind::Polygon:
                    for (Vec2 const& p : r.polygon)
                        best = std::max(best, DungeonKit::Distance(from, p));
                    break;
                case DungeonKit::ArenaRegion::Kind::Circle:
                    best = std::max(best, DungeonKit::Distance(from, r.center) + r.radius);
                    break;
                case DungeonKit::ArenaRegion::Kind::FrameBox:
                {
                    std::array<Vec2, 4> const corners{ {
                        DungeonKit::FramePoint(r.frame, r.frameBox.minX, r.frameBox.minY),
                        DungeonKit::FramePoint(r.frame, r.frameBox.maxX, r.frameBox.minY),
                        DungeonKit::FramePoint(r.frame, r.frameBox.maxX, r.frameBox.maxY),
                        DungeonKit::FramePoint(r.frame, r.frameBox.minX, r.frameBox.maxY),
                    } };
                    for (Vec2 const& p : corners)
                        best = std::max(best, DungeonKit::Distance(from, p));
                    break;
                }
            }
        }
        return best;
    }

    // The donut's outer radius: the farthest floor point plus the margin, at least past the hole (an empty floor: a
    // 60 yd reach).
    inline float JusticeOuterYd(DungeonKit::Arena const& floor, Vec2 from, float safeYd)
    {
        float const reach = floor.Empty() ? 60.f : FarthestReach(floor, from) + Tune::kJusticeOuterMarginYd;
        return std::max(reach, safeYd + 1.f);
    }

    // The blast look's points: `count` points on a ring of `radius` around `center`, the first due east of it.
    inline std::vector<Vec2> RingPoints(Vec2 center, float radius, std::uint32_t count)
    {
        std::vector<Vec2> out;
        out.reserve(count);
        for (std::uint32_t i = 0; i < count; ++i)
            out.push_back(DungeonKit::Advance(center, DungeonKit::kTwoPi * float(i) / float(count), radius));
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EL4 Chain Bolt: the jumps
    // ----------------------------------------------------------------------------------------------------------------
    struct ChainNode
    {
        std::uint64_t key = 0;
        Vec2 at;
    };

    // The struck order: `first` (the target), then the nearest node not yet struck within `jumpYd` of the last one
    // struck, until none is in reach or `maxJumps` jumps (0: no limit). Ties go to the lower index.
    inline std::vector<std::size_t> ChainOrder(std::vector<ChainNode> const& nodes, std::size_t first, float jumpYd,
        std::uint32_t maxJumps)
    {
        std::vector<std::size_t> order;
        if (first >= nodes.size())
            return order;
        std::vector<bool> struck(nodes.size(), false);
        order.push_back(first);
        struck[first] = true;
        while (maxJumps == 0 || order.size() <= maxJumps)
        {
            Vec2 const from = nodes[order.back()].at;
            std::optional<std::size_t> next;
            float best = 0.f;
            for (std::size_t i = 0; i < nodes.size(); ++i)
            {
                if (struck[i])
                    continue;
                float const d = DungeonKit::Distance(from, nodes[i].at);
                if (d > jumpYd)
                    continue;
                if (!next || d < best)
                {
                    next = i;
                    best = d;
                }
            }
            if (!next)
                break;
            struck[*next] = true;
            order.push_back(*next);
        }
        return order;
    }

    // The percent of hit `index` of a chain (0: the target): base x growth^index (normal 20 each; heroic 40, then each
    // jump 25% more than the last).
    inline float ChainHitPct(std::size_t index, float basePct, float growth)
    {
        return basePct * std::pow(growth, float(index));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // EL6 Static (heroic): the meter on one player
    // ----------------------------------------------------------------------------------------------------------------
    struct StaticRules
    {
        float perYd = Tune::kStaticPerYd;
        float drainPerSec = Tune::kStaticDrainPerSec;
        float dischargeAt = Tune::kStaticDischargeAt;
        float stillYd = Tune::kStaticStillYd;
        float maxStepYd = Tune::kStaticMaxStepYd;
    };

    class StaticCharge
    {
    public:
        // One sample `diffMs` after the last at `at` (the player's map position). True when it reaches the discharge:
        // the charge is then 0 again. The first sample only remembers the spot.
        bool Step(Vec2 at, std::uint32_t diffMs, StaticRules const& rules = {})
        {
            if (!_seen)
            {
                _seen = true;
                _last = at;
                return false;
            }
            float const moved = DungeonKit::Distance(_last, at);
            _last = at;
            if (moved > rules.maxStepYd)
                return false;                   // a teleport or a snap-back: adds nothing, drains nothing
            if (moved >= rules.stillYd)
                _value += moved * rules.perYd;
            else
                _value = std::max(0.f, _value - rules.drainPerSec * float(diffMs) / 1000.f);
            if (_value + 1e-4f >= rules.dischargeAt)
            {
                _value = 0.f;
                return true;
            }
            return false;
        }

        // The stack count the aura shows.
        std::uint32_t Shown() const { return std::uint32_t(std::floor(_value + 1e-4f)); }
        float Value() const { return _value; }
        void Set(float value) { _value = std::max(0.f, value); }
        // A teleport or a death: the next sample starts again from where the player is.
        void Forget() { _seen = false; }

    private:
        Vec2 _last;
        float _value = 0.f;
        bool _seen = false;
    };

    // The discharge's partner: the nearest other node within `rangeYd` of node `carrier` (nullopt: nobody).
    inline std::optional<std::size_t> NearestWithin(std::vector<ChainNode> const& nodes, std::size_t carrier,
        float rangeYd)
    {
        if (carrier >= nodes.size())
            return std::nullopt;
        std::optional<std::size_t> best;
        float bestD = 0.f;
        for (std::size_t i = 0; i < nodes.size(); ++i)
        {
            if (i == carrier)
                continue;
            float const d = DungeonKit::Distance(nodes[carrier].at, nodes[i].at);
            if (d <= rangeYd && (!best || d < bestD))
            {
                best = i;
                bestD = d;
            }
        }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Section 7 #20 A: the platform's picks
    // ----------------------------------------------------------------------------------------------------------------

    // Rule 5 and section 3.8 (the guard and pick polygon): a pick stands on the platform arena (the disc, its rim and
    // the walkway mouth, the platform's z band): a player who fell off is never picked. The 21 yd pick disc is the
    // bots' bounds only (ElectrocutionerFloorBounds: their spots, dodges and the band), never who can be targeted.
    inline bool OnPickFloor(Vec2 at, float z)
    {
        return GnomereganRework::PlatformArena().Contains(at, z);
    }

    // The walkway past the platform polygon's mouth (NAVMESH 3: x -550.2 to -534.2, y 535.2 to 547.8, rails on both
    // sides, z -218.2 to -216.5; the slope band from z -222.5).
    inline std::array<Vec2, 7> constexpr kWalkwayPolygon{ {
        { -551.0f, 533.0f }, { -536.0f, 529.5f }, { -534.0f, 536.0f }, { -534.0f, 543.0f }, { -536.0f, 549.0f },
        { -549.0f, 549.0f }, { -551.0f, 541.0f },
    } };
    float constexpr kWalkwayZMin = -223.f;

    // The Justice's floor (the donut's outer reach and the blast ring's ground): the platform plus the walkway, so a
    // player on the walkway (to about 46 yd from the center) stands in the donut too (R-1-A M1: SP's pull in two
    // directions holds for the ranged; the 30 yd platform alone left the walkway past 31 yd safe).
    inline DungeonKit::Arena JusticeFloor()
    {
        DungeonKit::Arena floor = GnomereganRework::PlatformArena();
        floor.Add(GnomereganRework::PolygonRegion(kWalkwayPolygon, kWalkwayZMin, GnomereganRework::kPlatformZMax));
        return floor;
    }
}

#endif
