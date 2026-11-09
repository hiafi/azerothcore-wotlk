/*
 * mod-dungeon-bosses, Scholomance S12: Ras Frostwhisper's hard mode, "the Torn Keepsake" (heroic only), the pure,
 * host-testable part (no engine headers): the spell ids, the tuning, the hard mode clock (the transition, Siphon Warmth
 * and Mortal Decay), the Siphon's numbers, and the keepsake gameobjects' rules (which page a spawn is, when a page,
 * the book and the alchemy table show or can be used). WP-S12 owns this file; tests/scholo_keepsake_test.cpp tests it.
 *
 * Build spec: docs/dungeons/scholomance-rework.md SC 1087-1121 (Hard mode, approved 2026-10-30), SC 1122-1134 (tuning),
 * SC 1207-1209 (RF9-RF11); handoff section 3.5 row S12, section 3.6 (lich 400k, human 400k, tomb 12k) and section 10
 * (the user's page, book and alchemy table spots: the table starts the hard mode, not the Embalming Fluid). The fight
 * runs on S4's AI (boss_ras_frostwhisper_rework) through RasFight.h; ras_hard_mode.cpp is the engine side.
 *
 * Damage percentages are of the heroic reference row (4,120 non-tank / 4,110 tank at level 60): the hard mode is heroic
 * only. The Siphon's heal and backfire are percentages of Ras's own (human) bar.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_RAS_HARD_MODE_LOGIC_H

#include "RasLogic.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace ScholoRasHardMode
{
    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsRasHardMode;

    // Declared in apps/dbc-tools source/npcs/scholomance/ras_hard_mode.py (same ids).
    enum RasHardModeSpells : std::uint32_t
    {
        SPELL_RK_CLINGING_TO_LIFE   = 206190,   // RF9 the 3 s transition cast bar (no effect; untargetable meanwhile)
        SPELL_RK_SIPHON_CAST        = 206191,   // RF10 the 2 s cast bar (emote line 2), not interruptible
        SPELL_RK_SIPHON_CHANNEL     = 206192,   // RF10 the 5 s channel look on Ras (not interruptible)
        SPELL_RK_SIPHONED           = 206193,   // RF10 the drain on each warm player, refreshed every tick (look)
        SPELL_RK_SIPHON_HEAL        = 206194,   // RF10 Ras heals (base point 0 = the exact amount from the script)
        SPELL_RK_SIPHON_BACKFIRE    = 206195,   // RF10 a cold player's backfire on Ras (base point 0 = the amount)
        SPELL_RK_MORTAL_DECAY       = 206196,   // RF11 the stacking Frost DoT (spell_sc_ras_mortal_decay)
        SPELL_RK_THAWING            = 206197,   // RF3 HM: the broken tomb's 1.5 s cast bar before it bursts
        // 206198-206204 spare
    };
    static_assert(kSpellSlice.Contains(SPELL_RK_CLINGING_TO_LIFE), "S12 spells sit in its slice");
    static_assert(kSpellSlice.Contains(SPELL_RK_THAWING), "S12 spells sit in its slice");

    // Ras's text group for the hard mode start (WP-S12's SQL rev; groups 0-2 are S4's). A boss emote heard on the
    // whole map, since the alchemy table is about 80 yd from his study.
    std::uint8_t constexpr EMOTE_RAS_KEEPSAKE_LIT = 3;

    // Registry tag of the Siphon's Spread (S4's tags are 1-6).
    std::uint32_t constexpr TAG_SIPHON = 10;

    // The Ice Tomb AI's GetData slot: 1 once its health ran out (it is cracking).
    std::uint32_t constexpr kTombDataCracked = 1;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SC "Tuning starting points" and the build spec table, approved 2026-10-30)
    // ----------------------------------------------------------------------------------------------------------------

    // Health: the lich 400k (set at the pull, by script), then the human form back to the same 400k.
    std::uint32_t constexpr kLichHealth = 400000;
    std::uint32_t constexpr kHumanHealth = 400000;

    // RF3 HM: the permanent tomb, a 12k unit on the frozen player. At zero it cracks (not selectable, a 1.5 s cast
    // bar and the 6 yd thaw circle on the floor), then bursts and lets the player go: the thaw's numbers are S4's
    // (RasLogic.h kThawRadius, kThawPct 45% heroic, Weakened, +3 Chill). The crack is this WP's call: S4's 250 ms
    // thaw would hit every melee player breaking the tomb with no chance to step out.
    std::uint32_t constexpr kTombHealth = 12000;
    std::uint32_t constexpr kTombCrackMs = 1500;

    // RF9 the transition: 3 s untargetable, the yell, the human form, healing to full over the 3 s.
    std::uint32_t constexpr kTransitionMs = 3000;
    std::uint32_t constexpr kHumanDisplay = 3975;                   // stock Boon of Life human form (see the report)

    // RF10 Siphon Warmth: 10 s into phase 2, then every 30 s; a 2 s cast warning, then a 5 s channel ticking every
    // second. Warm players: +3 Chill a tick (three times the cold rate) and Ras heals 1% of his bar per warm player
    // per tick, at most 10% per Siphon. Cold living players: +1 Chill a tick and he takes 1.3% of his bar per cold
    // player per tick. Entombed players are neither.
    std::uint32_t constexpr kSiphonFirstMs = 10000;
    std::uint32_t constexpr kSiphonEveryMs = 30000;
    std::uint32_t constexpr kSiphonCastMs = 2000;
    std::uint32_t constexpr kSiphonChannelMs = 5000;
    std::uint32_t constexpr kSiphonTickMs = 1000;
    std::uint32_t constexpr kSiphonTicks = kSiphonChannelMs / kSiphonTickMs;
    std::uint32_t constexpr kSiphonWarmChill = 3;
    std::uint32_t constexpr kSiphonColdChill = 1;
    float constexpr kSiphonHealPctPerWarm = 1.0f;
    float constexpr kSiphonHealCapPct = 10.0f;
    float constexpr kSiphonBackfirePctPerCold = 1.3f;
    float constexpr kSiphonSpreadRadius = 8.f;                      // bots: a registry Spread for the 5 s
    static_assert(kSiphonTicks * kSiphonTickMs == kSiphonChannelMs, "the channel ticks every second");

    // RF11 Mortal Decay: from the start of phase 2, a stack on every player each 10 s (stacks = whole 10 s elapsed:
    // 5 at 50 s, 12 at 2 min, the build spec's 2.5% / 6% a second), 0.5% of the heroic reference row per second per
    // stack. The enrage: no time limit otherwise.
    std::uint32_t constexpr kDecayEveryMs = 10000;
    float constexpr kDecayPctPerStack = 0.5f;
    std::uint32_t constexpr kDecayMaxStacks = 99;                   // the spell's CumulativeAura
    // The aura's own duration (DT 206196): every 10 s step refreshes it (DungeonKit::AddStacks), so it never runs out
    // in the fight, but a stray aura on a player who left the fight expires. It also carries the CHANGE_MAP interrupt
    // flag (dropped on a logout or a map change).
    std::uint32_t constexpr kDecayDurationMs = 15000;
    static_assert(kDecayDurationMs > kDecayEveryMs, "each 10 s step refreshes Mortal Decay before it runs out");

    // ----------------------------------------------------------------------------------------------------------------
    // The hard mode clock: the transition and phase 2 (Siphon Warmth, Mortal Decay), on the hard mode's own clock
    // (never a scheduler a cast bar pauses). S4's fight clock stands still during the transition (HoldsTimeline).
    // ----------------------------------------------------------------------------------------------------------------

    enum class Phase : std::uint8_t
    {
        Lich = 0,
        Transition = 1,
        Human = 2,
    };

    enum class SiphonStage : std::uint8_t
    {
        Idle = 0,
        Warning = 1,        // the 2 s cast bar
        Channel = 2,        // the 5 s channel
    };

    // What one Advance asks the engine side to do.
    struct ClockStep
    {
        bool transitionDone = false;    // the human form: display, flags, full health; phase 2 starts
        std::uint32_t decayTo = 0;      // > 0: every player's Mortal Decay goes to this many stacks
        bool siphonCast = false;        // the cast bar, the emote and the Spread
        bool channelStart = false;      // the channel look
        std::uint32_t siphonTicks = 0;  // Siphon ticks due now (normally 0 or 1)
        bool siphonEnd = false;         // the channel is over
    };

    // Stacks of Mortal Decay `humanMs` into phase 2: one per whole 10 s.
    constexpr std::uint32_t DecayStacksAt(std::uint32_t humanMs)
    {
        std::uint32_t const n = humanMs / kDecayEveryMs;
        return n > kDecayMaxStacks ? kDecayMaxStacks : n;
    }

    struct KeepsakeClock
    {
        Phase phase = Phase::Lich;
        std::uint32_t transitionMs = 0;
        std::uint32_t humanMs = 0;              // ms into phase 2
        std::uint32_t decayStacks = 0;          // stacks given so far
        SiphonStage siphon = SiphonStage::Idle;
        std::uint32_t siphonMs = 0;             // ms into the current stage
        std::uint32_t siphonTicks = 0;          // ticks of the current channel
        std::uint32_t nextSiphonAt = kSiphonFirstMs;
        std::uint32_t siphons = 0;              // Siphons started

        // The lich bar is empty (the first lethal hit). False when already past the lich.
        bool StartTransition()
        {
            if (phase != Phase::Lich)
                return false;
            phase = Phase::Transition;
            transitionMs = 0;
            return true;
        }

        // `siphonMayStart`: Ras is not casting and no Frost Mark is live (a due Siphon waits for both, so the mark and
        // the Siphon never overlap).
        ClockStep Advance(std::uint32_t diff, bool siphonMayStart)
        {
            ClockStep step;
            if (phase == Phase::Transition)
            {
                transitionMs += diff;
                if (transitionMs >= kTransitionMs)
                {
                    transitionMs = kTransitionMs;
                    phase = Phase::Human;
                    humanMs = 0;
                    step.transitionDone = true;
                }
                return step;
            }
            if (phase != Phase::Human)
                return step;

            humanMs += diff;
            std::uint32_t const want = DecayStacksAt(humanMs);
            if (want > decayStacks)
            {
                decayStacks = want;
                step.decayTo = want;
            }

            switch (siphon)
            {
                case SiphonStage::Idle:
                    if (humanMs >= nextSiphonAt && siphonMayStart)
                    {
                        siphon = SiphonStage::Warning;
                        siphonMs = 0;
                        ++siphons;
                        nextSiphonAt = humanMs + kSiphonEveryMs;
                        step.siphonCast = true;
                    }
                    break;
                case SiphonStage::Warning:
                    siphonMs += diff;
                    if (siphonMs >= kSiphonCastMs)
                    {
                        siphon = SiphonStage::Channel;
                        siphonMs = 0;
                        siphonTicks = 0;
                        step.channelStart = true;
                    }
                    break;
                case SiphonStage::Channel:
                    siphonMs += diff;
                    while (siphonTicks < kSiphonTicks && siphonMs >= (siphonTicks + 1) * kSiphonTickMs)
                    {
                        ++siphonTicks;
                        ++step.siphonTicks;
                    }
                    if (siphonTicks >= kSiphonTicks)
                    {
                        siphon = SiphonStage::Idle;
                        siphonMs = 0;
                        step.siphonEnd = true;
                    }
                    break;
            }
            return step;
        }

        // `.dbtest`: the next Siphon is due now (phase 2 only).
        void SiphonNow()
        {
            if (phase == Phase::Human && siphon == SiphonStage::Idle)
                nextSiphonAt = humanMs;
        }

        // RasHardMode's hold queries (RasFight.h).
        bool HoldsTimeline() const { return phase == Phase::Transition; }
        bool HoldsFrostMark() const { return siphon != SiphonStage::Idle; }
        bool HoldsChillBeat() const { return siphon == SiphonStage::Channel; }
        // S4's warm Stack (the bots' Cluster) is cancelled for the whole Siphon, cast bar and channel, so it never
        // pulls a bot into the Siphon's 8 yd Spread; S4 registers it again after.
        bool SuspendsWarmStack() const { return siphon != SiphonStage::Idle; }
        // The lethal guard stays armed until the human form is up (the lich never dies).
        bool Mortal() const { return phase == Phase::Human; }
    };

    // RF9: Ras's health `transitionMs` into the 3 s transition (healing to full like the stock Boon of Life).
    constexpr std::uint32_t TransitionHealth(std::uint32_t maxHealth, std::uint32_t transitionMs)
    {
        if (transitionMs >= kTransitionMs)
            return maxHealth;
        std::uint64_t const h = static_cast<std::uint64_t>(maxHealth) * transitionMs / kTransitionMs;
        return h < 1 ? 1u : static_cast<std::uint32_t>(h);
    }

    // RF10: the percent of his bar one tick heals with `warm` warm players, `healedPct` already healed this Siphon.
    inline float SiphonHealPct(std::uint32_t warm, float healedPct)
    {
        float const room = std::max(0.f, kSiphonHealCapPct - healedPct);
        return std::min(room, static_cast<float>(warm) * kSiphonHealPctPerWarm);
    }

    // RF10: the percent of his bar one cold player's backfire deals in one tick.
    constexpr float SiphonBackfirePct()
    {
        return kSiphonBackfirePctPerCold;
    }

    // `pct` percent of `maxHealth`, rounded.
    inline std::uint32_t PctOf(std::uint32_t maxHealth, float pct)
    {
        if (pct <= 0.f)
            return 0;
        return static_cast<std::uint32_t>(std::lround(static_cast<double>(maxHealth) * pct / 100.0));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The keepsake gameobjects (handoff section 10; ScholomanceRework.h kKeepsakePages / kKeepsakeBook /
    // kHardModeTable; the instance owns the data: DATA_KEEPSAKE_PAGE, DATA_KEEPSAKE_BOUND, DATA_RAS_HARD_MODE)
    // ----------------------------------------------------------------------------------------------------------------

    // A page spawn is the page whose measured spot is within this of it (the SQL rev spawns them exactly there).
    float constexpr kPageMatchYd = 3.f;

    // The page (0..2) a torn page spawned at (x, y, z) is, else kKeepsakePageCount.
    inline std::size_t PageAt(float x, float y, float z)
    {
        for (std::size_t i = 0; i < ScholomanceRework::kKeepsakePageCount; ++i)
        {
            ScholomanceRework::Point4 const& p = ScholomanceRework::kKeepsakePages[i];
            float const dx = p.x - x;
            float const dy = p.y - y;
            float const dz = p.z - z;
            if (std::sqrt(dx * dx + dy * dy + dz * dz) <= kPageMatchYd)
                return i;
        }
        return ScholomanceRework::kKeepsakePageCount;
    }

    // A page shows (and can be taken) on heroic, until it is found, while Ras lives.
    constexpr bool PageShows(bool heroic, std::uint32_t mask, std::size_t page, std::uint32_t rasState)
    {
        return heroic && page < ScholomanceRework::kKeepsakePageCount && !(mask & (1u << page))
            && rasState != DungeonKit::State::Done;
    }

    // The empty book shows until the keepsake is bound; the bound book from then on (one spot, two gameobjects).
    constexpr bool BookShows(bool boundBook, bool bound)
    {
        return boundBook == bound;
    }

    enum class TableRefusal : std::uint8_t
    {
        None = 0,
        NotHeroic,
        RasDead,
        AlreadyLit,
        NotBound,
        RasFighting,
    };

    // The alchemy table lights the hard mode with the bound keepsake, on heroic, while Ras neither fights nor is dead
    // (ScholomanceRework.h RasHardModeChangeAllowed, the instance's own check, says the same).
    constexpr TableRefusal TableCheck(bool heroic, bool bound, bool lit, std::uint32_t rasState)
    {
        if (!heroic)
            return TableRefusal::NotHeroic;
        if (rasState == DungeonKit::State::Done)
            return TableRefusal::RasDead;
        if (lit)
            return TableRefusal::AlreadyLit;
        if (!bound)
            return TableRefusal::NotBound;
        if (rasState == DungeonKit::State::InProgress)
            return TableRefusal::RasFighting;
        return TableRefusal::None;
    }

    // Every keepsake gameobject's line once Ras is dead (a page or a bind the instance refuses, the books, the table).
    inline constexpr char const* kRasGoneText = "Ras Frostwhisper is gone. The keepsake no longer matters.";

    // The bound book's line to the player who clicks it.
    constexpr char const* BoundBookText(bool lit, std::uint32_t rasState)
    {
        if (rasState == DungeonKit::State::Done)
            return kRasGoneText;
        return lit ? "The keepsake calls to Ras Frostwhisper."
                   : "Frostwhisper's keepsake is whole again. The alchemy apparatus down the hall awaits it.";
    }

    constexpr char const* TableRefusalText(TableRefusal why)
    {
        switch (why)
        {
            case TableRefusal::None: return "";
            case TableRefusal::NotHeroic: return "The apparatus is cold and empty.";
            case TableRefusal::RasDead: return kRasGoneText;
            case TableRefusal::AlreadyLit: return "The keepsake already calls to Ras Frostwhisper.";
            case TableRefusal::NotBound: return "Something is missing: a keepsake, bound whole again.";
            case TableRefusal::RasFighting: return "Not while Ras Frostwhisper is fighting.";
        }
        return "";
    }
}

#endif
