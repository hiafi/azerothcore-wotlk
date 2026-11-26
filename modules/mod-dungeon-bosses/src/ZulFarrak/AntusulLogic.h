/*
 * mod-dungeon-bosses, Zul'Farrak D2: Antu'sul (8127) and his Servants (8156), the pure, host-testable part (no engine
 * headers): the spell ids, the registry tags, the per-difficulty tuning (`namespace Tune`, handoff section 3.5 rule
 * 32), the shatter and Shockwave arithmetic, the Servant rise pick, the gaze clock, the never-paused fight timeline and
 * the bots' dispel rule. Build spec: SP 733-807 (AS1-AS11), design SP 534-732 (rulings 13-16); handoff section 3.5
 * row D2, section 3.6 (health: ZulFarrakRework.h Health, never restated here), section 3.8 (the den, the chamber, the
 * rise points), section 7 #9 A (the bots' Calcify rule), #25 A and #28 A (the wake and the chamber fight).
 *
 * Damage percentages are of the reference health row (209:46 = 2,655 non-tank / 2,717 tank, 209h:60 = 4,120 / 4,110,
 * section 7 #4 A); the build spec gives N / H percents.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_ANTUSUL_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_ANTUSUL_LOGIC_H

#include "DungeonKitMath.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ZfAntusul
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsAntusul;

    // Declared in apps/dbc-tools source/npcs/zul_farrak/antusul.py (same ids).
    enum AntusulSpells : std::uint32_t
    {
        SPELL_AS_CALCIFY            = kSpellSlice.first + 0,    // AS3 Magic, 6 stacks, 30 s: -5% taken, -7% speed
        SPELL_AS_GAZE               = kSpellSlice.first + 1,    // AS2 the Servant's 6 s channel beam (a look)
        SPELL_AS_PETRIFIED          = kSpellSlice.first + 2,    // AS5 the 2 s stun of the statue
        SPELL_AS_SHATTERBOLT_BAR    = kSpellSlice.first + 3,    // AS6 the 2.5 s bar (Physical, not kickable)
        SPELL_AS_SHATTERBOLT_BAR_H  = kSpellSlice.first + 4,    // AS6 heroic: the 2 s bar
        SPELL_AS_SHATTERBOLT_HIT    = kSpellSlice.first + 5,    // AS6 the bolt on its target: resolve copy (Nature)
        SPELL_AS_SHATTERBOLT_LOOK   = kSpellSlice.first + 6,    // AS6 the lightning on the target (SV 36)
        SPELL_AS_SHATTER            = kSpellSlice.first + 7,    // AS7 the shrapnel: resolve copy (Physical)
        SPELL_AS_CRACK              = kSpellSlice.first + 8,    // AS5 the crack on the statue: resolve copy (Physical)
        SPELL_AS_SHOCKWAVE_BAR      = kSpellSlice.first + 9,    // AS8 the 3 s bar (Physical, not kickable)
        SPELL_AS_SHOCKWAVE_HIT      = kSpellSlice.first + 10,   // AS8 the group hit: resolve copy (Nature)
        SPELL_AS_SHOCKWAVE_LOOK     = kSpellSlice.first + 11,   // AS8 the ground slam on him (SV 8083)
        SPELL_AS_HEALING_WAVE       = kSpellSlice.first + 12,   // AS9 the 3 s heal (Nature, kickable)
        SPELL_AS_HEALING_WAVE_H     = kSpellSlice.first + 13,   // AS9 heroic: the 2 s heal
        SPELL_AS_STONEFLESH         = kSpellSlice.first + 14,   // AS10 heroic: 3 stacks on him, -10% taken each
        SPELL_AS_SERVANT_RISE       = kSpellSlice.first + 15,   // AS1 the dirt burst on a risen Servant (SV 7443)
        // kSpellSlice.first + 16 .. last: spare
    };
    static_assert(kSpellSlice.Contains(SPELL_AS_CALCIFY), "Antu'sul's spells sit in his slice");
    static_assert(kSpellSlice.Contains(SPELL_AS_SERVANT_RISE), "Antu'sul's spells sit in his slice");

    // Stock, cast as it is (AS4; DD scales it on heroic): his tank hit, now with a Calcify stack by script.
    std::uint32_t constexpr SPELL_EARTH_SHOCK = 15501;

    // Registry tags (the build spec's AS numbers; 10+ for the helpers).
    enum AntusulTags : std::uint32_t
    {
        TAG_PETRIFY         = 5,    // AS5 the statue's circle: the crack's shrapnel on everyone else
        TAG_BOLT            = 6,    // AS6 the bolt's circle on its target (the warning; the shrapnel is TAG_SHATTER)
        TAG_SHATTER         = 7,    // AS7 a bolt's or a dispel's shrapnel
        TAG_SHOCKWAVE       = 8,    // AS8 the group hit (one RegistryHit per stack count)
        TAG_STONEFLESH      = 10,   // AS10 heroic: the bots' Stack at him for 5+ stack carriers
        TAG_CRACK           = 15,   // AS5 the crack on the statue
        TAG_BOLT_HIT        = 16,   // AS6 the bolt on its target
    };

    // Texts (creature_text 8127; groups as SP prints them, rule 34): 0-2 stock, 3 new (the SQL rev).
    enum AntusulTexts : std::uint8_t
    {
        YELL_BROOD      = 0,    // "The children of Sul will protect their master..." the first time 3 are alive
        YELL_AGGRO      = 1,    // "Lunch has arrived, my beautiful children. Tear them to pieces!"
        YELL_RISE       = 2,    // "Rise and defend your master!" every rise after the pull's
        EMOTE_SHOCKWAVE = 3,    // "%s draws the stone beneath his feet!" (type 41)
    };

    // The wake (section 7 #25 A, kept stock): area trigger 1447's SmartAI (action 45, set data on guid 81519) and DC's
    // wake hook both send SetData(kWakeDataId, kWakeDataValue) to his creature AI (never the instance).
    std::uint32_t constexpr kWakeDataId = 1;
    std::uint32_t constexpr kWakeDataValue = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP Build spec 733-807 and "Tuning starting points"; rulings 14-16; section 3.5 rule 32)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // AS1 Servants: one on the pull, then one every 25 s (heroic 20 s), at most 3 alive. A rise due with 3 alive
        // is skipped (the next one stays on its grid). Stationary, no melee; stock 5,757 health (heroic 15,000: WP-H).
        std::uint32_t constexpr kRiseFirstMs = 0;
        inline constexpr NH<std::uint32_t> kRiseEveryMs{ 25000, 20000 };
        std::uint32_t constexpr kServantCap = 3;
        // Rise points (ZulFarrakRework.h kServantRisePoints): one with no living Servant within kRiseTakenYd, at least
        // kRiseClearOfBossYd from him (section 3.8: "clear of the melee around him"); else the farthest free point.
        float constexpr kRiseTakenYd = 3.f;
        float constexpr kRiseClearOfBossYd = 12.f;
        // The corpse stays this long, then goes.
        std::uint32_t constexpr kServantCorpseMs = 10000;

        // AS2 Calcifying Gaze: each Servant stares at a random player, tank included, for 6 s, a Calcify stack every
        // 2 s (heroic 1.5 s: 3 and 4 a gaze), then picks a new target 2 s later. Not kickable; a stun, fear or
        // polymorph on the Servant stops it (the crowd control reward), and the 2 s wait starts when it ends. The
        // first gaze starts kGazeFirstMs after the rise (the dirt burst plays first).
        std::uint32_t constexpr kGazeMs = 6000;
        inline constexpr NH<std::uint32_t> kGazeTickMs{ 2000, 1500 };
        std::uint32_t constexpr kGazePauseMs = 2000;
        std::uint32_t constexpr kGazeFirstMs = 1000;
        static_assert(kGazeMs % 2000 == 0 && kGazeMs % 1500 == 0, "a gaze is a whole number of ticks");

        // AS3 Calcify: Magic, up to 6 stacks, 30 s, refreshed by each stack. Per stack: 5% less damage taken, 7%
        // slower (the aura's own effects, multiplied by the stack count). The sixth petrifies (AS5).
        std::uint32_t constexpr kCalcifyMaxStacks = 6;
        std::uint32_t constexpr kCalcifyDurationMs = 30000;
        std::int32_t constexpr kCalcifyTakenPctPerStack = 5;
        std::int32_t constexpr kCalcifySlowPctPerStack = 7;

        // AS4 Earth Shock (stock 15501, triggered so a kicked Nature school never refuses it): 3 s, then every 9 to
        // 11 s on his victim, +1 Calcify. Out of its 20 yd range it waits kRetryMs.
        std::uint32_t constexpr kEarthShockFirstMs = 3000;
        std::uint32_t constexpr kEarthShockMinMs = 9000;
        std::uint32_t constexpr kEarthShockMaxMs = 11000;
        std::uint32_t constexpr kEarthShockStacks = 1;
        float constexpr kEarthShockRangeYd = 20.f;

        // AS5 Petrified: the sixth stack turns the player to stone for 2 s (a stun, the cost in place of Weakened); a
        // 6 yd circle on the statue (tank included) for the 2 s; then the crack: 25% / 35% to the player and a shatter
        // of 6 stacks on everyone else within 6 yd (AS7, no Weakened at 6).
        std::uint32_t constexpr kPetrifyMs = 2000;
        inline constexpr NH<float> kCrackPct{ 25.f, 35.f };
        static_assert(kPetrifyMs >= ZulFarrakRework::kWarningFloorMs, "the crack's circle meets the warning floor");

        // AS6 Shatterbolt: a 2.5 s / 2 s bar on a random player with Calcify (any player if nobody has a stack),
        // tank included, every 10 to 12 s / 8 to 10 s, first at 6 s; a 6 yd circle on the target for the bar (the
        // target never counted). Landed: 15% / 25% Nature to the target (cut by its own stone), then its stacks
        // shatter (AS7).
        std::uint32_t constexpr kBoltFirstMs = 6000;
        inline constexpr NH<std::uint32_t> kBoltCastMs{ 2500, 2000 };
        inline constexpr NH<std::uint32_t> kBoltMinMs{ 10000, 8000 };
        inline constexpr NH<std::uint32_t> kBoltMaxMs{ 12000, 10000 };
        inline constexpr NH<float> kBoltPct{ 15.f, 25.f };
        static_assert(kBoltCastMs.heroic >= ZulFarrakRework::kWarningFloorMs, "the bolt's circle meets the floor");

        // AS7 Shatter: every other player within 6 yd of the carrier takes 6% / 9% Physical per stack shattered (36% /
        // 54% at 6), cut by their own Calcify; Weakened up to 5 stacks (the heroic value under 50%, both difficulties:
        // rule 22). Heroic stone dust: everyone it hits gains 2 Calcify. A dispel's shatter comes with no warning (SP:
        // the healer dispels a carrier standing alone); a bolt's comes after the bolt's circle, so its own registry
        // circle only needs the registry's shortest warning.
        float constexpr kShatterRadius = 6.f;
        inline constexpr NH<float> kShatterPctPerStack{ 6.f, 9.f };
        std::uint32_t constexpr kShatterWeakenedMaxStacks = 5;
        inline constexpr NH<std::uint32_t> kStoneDustStacks{ 0, 2 };
        std::uint32_t constexpr kShatterWarnMs = 250;

        // AS8 Earthen Shockwave: a 3 s bar every 20 s / 18 s, first at 20 s (emote line 3); 50% / 70% Nature to
        // everyone, cut by 10% of the hit per Calcify stack (in place of Calcify's own 5%; ruling 15), every other
        // reduction multiplied on top. Unavoidable: no Weakened.
        std::uint32_t constexpr kShockwaveFirstMs = 20000;
        inline constexpr NH<std::uint32_t> kShockwaveEveryMs{ 20000, 18000 };
        std::uint32_t constexpr kShockwaveCastMs = 3000;
        inline constexpr NH<float> kShockwavePct{ 50.f, 70.f };
        float constexpr kShockwaveCutPctPerStack = 10.f;
        static_assert(kShockwaveCastMs >= ZulFarrakRework::kWarningFloorMs, "the Shockwave's bar meets the floor");

        // AS9 Healing Wave of Antu'sul: a 3 s / 2 s cast every 20 to 25 s, first at 15 s; heals 4% / 8% of his
        // health. Nature and kickable (the expected interrupt): every bar that must land is Physical (section 3.5
        // kick table), Earth Shock is triggered.
        std::uint32_t constexpr kHealFirstMs = 15000;
        std::uint32_t constexpr kHealMinMs = 20000;
        std::uint32_t constexpr kHealMaxMs = 25000;
        inline constexpr NH<std::uint32_t> kHealCastMs{ 3000, 2000 };
        inline constexpr NH<float> kHealPct{ 4.f, 8.f };

        // AS10 Stoneflesh (heroic): 3 stacks on him at the pull, each 10% less damage taken. A crack (AS5) whose
        // shrapnel reaches him (within 6 yd of his edge) strips one; stacks never return.
        std::uint32_t constexpr kStonefleshStacks = 3;
        std::int32_t constexpr kStonefleshTakenPctPerStack = 10;
        float constexpr kStonefleshReachYd = kShatterRadius;
        // Bots: a carrier at 5+ Calcify walks to him (a Stack at him) while he has Stoneflesh; the tank stands there
        // anyway (the tank breaks it by default). Registered in blocks of kStonefleshStackBlockMs (persistent, judged
        // every kStonefleshStackTickMs), renewed before a block ends.
        std::uint8_t constexpr kStonefleshCarrierStacks = 5;
        float constexpr kStonefleshStackYd = 4.f;
        std::uint32_t constexpr kStonefleshStackWarnMs = 1000;
        std::uint32_t constexpr kStonefleshStackBlockMs = 30000;
        std::uint32_t constexpr kStonefleshStackTickMs = 1000;

        // Bots (section 7 #9 A, the kick and dispel table): cure Calcify only on a lone carrier (no player within 6 yd)
        // with 4+ stacks, and on heroic never the tank while he has Stoneflesh. Kick Healing Wave. Servants first.
        float constexpr kDispelSpacingYd = kShatterRadius;
        std::uint32_t constexpr kDispelMinStacks = 4;
        std::uint8_t constexpr kDispelPriority = 2;
        std::uint8_t constexpr kHealKickPriority = 2;
        std::int8_t constexpr kServantTargetPriority = 2;

        // The wake (section 7 #25 A): area trigger 1447's SetData(1, 1) (and DC's hook) sends him at the nearest
        // player within the stock "Start Attacking" radius (100 yd), a player on his floor first.
        float constexpr kWakeRangeYd = 100.f;

        std::uint32_t constexpr kRetryMs = 1000;    // nobody to target, out of range: try again this soon
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Stone arithmetic
    // ----------------------------------------------------------------------------------------------------------------

    // The share of a hit a carrier of `stacks` Calcify still takes through Calcify's own aura (5% a stack).
    constexpr float CalcifyTakenFactor(std::uint32_t stacks)
    {
        float const cut = float(std::min(stacks, Tune::kCalcifyMaxStacks)) * float(Tune::kCalcifyTakenPctPerStack);
        return std::max(0.f, 1.f - cut / 100.f);
    }

    // AS7: the shrapnel's percent for `stacks` shattered (at most 6).
    constexpr float ShatterPct(std::uint32_t stacks, bool heroic)
    {
        return float(std::min(stacks, Tune::kCalcifyMaxStacks)) * Tune::kShatterPctPerStack(heroic);
    }

    // AS7: Weakened up to 5 stacks (the crack's 6 never).
    constexpr bool ShatterWeakened(std::uint32_t stacks)
    {
        return stacks > 0 && stacks <= Tune::kShatterWeakenedMaxStacks;
    }

    // AS6: the bolt's percent on its target. The registry lands it on its next tick, after the script has taken the
    // target's stacks for the shatter, so the target's own stone is applied here (Calcify's 5% a stack).
    constexpr float BoltPct(std::uint32_t stacks, bool heroic)
    {
        return Tune::kBoltPct(heroic) * CalcifyTakenFactor(stacks);
    }

    // AS8: what a carrier of `stacks` takes in the end: the hit cut by 10% of itself per stack (never below 0).
    constexpr float ShockwaveNetPct(std::uint32_t stacks, bool heroic)
    {
        float const cut = float(std::min(stacks, Tune::kCalcifyMaxStacks)) * Tune::kShockwaveCutPctPerStack;
        return Tune::kShockwavePct(heroic) * std::max(0.f, 1.f - cut / 100.f);
    }

    // AS8: the percent the script registers, so that after Calcify's own 5% a stack (still on the carrier when the
    // registry lands it) the carrier takes ShockwaveNetPct: 10% a stack in place of 5% (ruling 15).
    constexpr float ShockwaveScriptPct(std::uint32_t stacks, bool heroic)
    {
        float const own = CalcifyTakenFactor(stacks);
        return own > 0.f ? ShockwaveNetPct(stacks, heroic) / own : 0.f;
    }

    // `pct` percent of `maxHealth`, rounded (AS9's heal).
    constexpr std::uint32_t PctOf(std::uint32_t maxHealth, float pct)
    {
        return static_cast<std::uint32_t>(double(maxHealth) * double(pct) / 100.0 + 0.5);
    }

    // AS10: a crack strips a Stoneflesh stack when the statue stands within the shrapnel's reach of his edge.
    constexpr bool CrackReachesHim(float distanceYd, float combatReachYd)
    {
        return distanceYd <= Tune::kStonefleshReachYd + combatReachYd;
    }

    // Section 7 #9 A as the descriptor builds it (the host test's mirror): may a bot cure this carrier now?
    constexpr bool BotsMayDispel(std::uint32_t stacks, bool lone, bool heroic, bool isTank, bool stonefleshUp)
    {
        if (!lone || stacks < Tune::kDispelMinStacks)
            return false;
        return !(heroic && isTank && stonefleshUp);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AS1 the rise point
    // ----------------------------------------------------------------------------------------------------------------

    // A point with no living Servant within kRiseTakenYd and at least kRiseClearOfBossYd from him (random among them);
    // else the farthest free point from him; nullopt when every point is taken. `rand(n)` returns [0, n).
    template <class Rand>
    std::optional<std::size_t> PickRisePoint(std::vector<Vec2> const& points, std::vector<Vec2> const& servants,
        Vec2 boss, Rand&& rand)
    {
        std::vector<std::size_t> clear;
        std::optional<std::size_t> farthest;
        float best = -1.f;
        for (std::size_t i = 0; i < points.size(); ++i)
        {
            bool taken = false;
            for (Vec2 const& s : servants)
                if (DungeonKit::Distance(points[i], s) < Tune::kRiseTakenYd)
                    taken = true;
            if (taken)
                continue;
            float const d = DungeonKit::Distance(points[i], boss);
            if (d >= Tune::kRiseClearOfBossYd)
                clear.push_back(i);
            if (d > best)
            {
                best = d;
                farthest = i;
            }
        }
        if (!clear.empty())
            return clear[static_cast<std::size_t>(rand(static_cast<std::uint32_t>(clear.size())))];
        return farthest;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // AS2 one Servant's gaze clock
    // ----------------------------------------------------------------------------------------------------------------

    enum class GazeStage : std::uint8_t
    {
        Wait,       // the pause before the next target (also while the Servant is held by crowd control)
        Gaze,       // staring at its target
    };

    struct GazeClock
    {
        GazeStage stage = GazeStage::Wait;
        std::uint32_t waitMs = Tune::kGazeFirstMs;  // left of the pause
        std::uint32_t gazeMs = 0;                   // into the gaze
        std::uint32_t ticks = 0;                    // stacks laid this gaze

        // A new target: the gaze starts now.
        void Start()
        {
            stage = GazeStage::Gaze;
            gazeMs = 0;
            ticks = 0;
        }

        // The gaze ends (its 6 s ran out, its target is gone): the next one after the pause.
        void Stop()
        {
            stage = GazeStage::Wait;
            waitMs = Tune::kGazePauseMs;
            gazeMs = 0;
            ticks = 0;
        }

        // Held by crowd control: no gaze, and the whole pause runs again once it lets go.
        void Held()
        {
            if (stage == GazeStage::Gaze)
                Stop();
            waitMs = Tune::kGazePauseMs;
        }

        // While waiting: true when a new target is due.
        bool Advance(std::uint32_t diff)
        {
            if (stage != GazeStage::Wait)
                return false;
            waitMs = diff >= waitMs ? 0 : waitMs - diff;
            return waitMs == 0;
        }

        // While gazing: the stacks `diff` ms lays (a tick every kGazeTickMs, the last at kGazeMs); `ended` is set when
        // the gaze ran its length (the caller then Stop()s it).
        std::uint32_t Tick(std::uint32_t diff, bool heroic, bool& ended)
        {
            ended = false;
            if (stage != GazeStage::Gaze)
                return 0;
            gazeMs = std::min(gazeMs + diff, Tune::kGazeMs);
            std::uint32_t const due = gazeMs / Tune::kGazeTickMs(heroic);
            std::uint32_t const laid = due > ticks ? due - ticks : 0;
            ticks = due;
            ended = gazeMs >= Tune::kGazeMs;
            return laid;
        }
    };

    // The stacks one whole gaze lays (3 normal, 4 heroic).
    constexpr std::uint32_t StacksPerGaze(bool heroic)
    {
        return Tune::kGazeMs / Tune::kGazeTickMs(heroic);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The fight timeline: on the AI's own clock, never paused by a cast bar (the Pilot's lesson). Rises and Earth Shock
    // fire whatever he casts; the three bars (the Shockwave first, then Shatterbolt, then Healing Wave) wait until he
    // is free. A late beat keeps max(due + period, now + period / 2) (section 3.5 rule 11, LESSONS L8).
    // ----------------------------------------------------------------------------------------------------------------

    enum class Bar : std::uint8_t
    {
        None,
        Shockwave,
        Bolt,
        Heal,
    };

    struct Timeline
    {
        std::uint32_t now = 0;                                  // ms since the pull
        std::uint32_t nextRise = Tune::kRiseFirstMs;
        std::uint32_t nextEarthShock = Tune::kEarthShockFirstMs;
        std::uint32_t nextBolt = Tune::kBoltFirstMs;
        std::uint32_t nextHeal = Tune::kHealFirstMs;
        std::uint32_t nextShockwave = Tune::kShockwaveFirstMs;

        void Advance(std::uint32_t diff)
        {
            now += diff;
        }

        std::uint32_t Paced(std::uint32_t due, std::uint32_t period) const
        {
            return std::max(due + period, now + period / 2);
        }

        bool RiseDue() const { return now >= nextRise; }
        // Fired, or skipped at the cap: the next one stays on the grid.
        void RiseDone(bool heroic) { nextRise = Paced(nextRise, Tune::kRiseEveryMs(heroic)); }

        bool EarthShockDue() const { return now >= nextEarthShock; }
        void EarthShockDone(std::uint32_t period) { nextEarthShock = Paced(nextEarthShock, period); }
        void EarthShockRetry() { nextEarthShock = now + Tune::kRetryMs; }

        // The bar due now, by priority (call it when he is free).
        Bar DueBar() const
        {
            if (now >= nextShockwave)
                return Bar::Shockwave;
            if (now >= nextBolt)
                return Bar::Bolt;
            if (now >= nextHeal)
                return Bar::Heal;
            return Bar::None;
        }

        void BarDone(Bar bar, std::uint32_t period)
        {
            switch (bar)
            {
                case Bar::Shockwave:
                    nextShockwave = Paced(nextShockwave, period);
                    break;
                case Bar::Bolt:
                    nextBolt = Paced(nextBolt, period);
                    break;
                case Bar::Heal:
                    nextHeal = Paced(nextHeal, period);
                    break;
                default:
                    break;
            }
        }

        void BarRetry(Bar bar)
        {
            std::uint32_t const at = now + Tune::kRetryMs;
            if (bar == Bar::Shockwave)
                nextShockwave = at;
            else if (bar == Bar::Bolt)
                nextBolt = at;
            else if (bar == Bar::Heal)
                nextHeal = at;
        }

        // The ms until `bar` is next due (0: due now).
        std::uint32_t InMs(Bar bar) const
        {
            std::uint32_t const at = bar == Bar::Shockwave ? nextShockwave : bar == Bar::Bolt ? nextBolt : nextHeal;
            return at > now ? at - now : 0;
        }
    };
}

#endif
