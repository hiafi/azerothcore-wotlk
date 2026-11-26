/*
 * mod-dungeon-bosses, Zul'Farrak D4a: the Sandfury Executioner (7274), the Block (stage 1 of the Pyramid) and the
 * Pyramid-wide pieces every stage shares (Grievous Wound, Offerings, Blood Price): the pure, host-testable part (no
 * engine headers). The spell ids, the registry tags, the texts, the tuning (`namespace Tune`, handoff section 3.5 rule
 * 32), the Block's clock, the prisoner and soaker picks, the chain spot candidates, the Behead's percent, the Sandfury
 * entries, the wound's end, the Blood Price arithmetic and its bleed meter. Build spec: SP 1346-1432 (PY1-PY3, PY16),
 * design SP 1180-1281; handoff section 3.5 row D4a, sections 3.6, 3.8 (the top), section 7 #11 A, #12 A, #32 A, #43 A
 * (a, c), #44 A. Tested by tests/zf_block_test.cpp. Health is ZulFarrakRework.h Health: never restated here.
 *
 * Damage percentages are of the reference health row (209:46 = 2,655 non-tank / 2,717 tank, 209h:60 = 4,120 / 4,110,
 * section 7 #4 A).
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_BLOCK_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_BLOCK_LOGIC_H

#include "DungeonKitMath.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace ZfBlock
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsBlock;

    // Declared in apps/dbc-tools source/npcs/zul_farrak/sandfury_executioner.py (same ids).
    enum BlockSpells : std::uint32_t
    {
        SPELL_PY_BEHEAD_BAR     = kSpellSlice.first + 0,    // PY1 the 4 s bar (Physical, not kickable)
        SPELL_PY_BEHEAD         = kSpellSlice.first + 1,    // PY1 the soaker's hit: resolve copy (Physical)
        SPELL_PY_BEHEAD_LOOK    = kSpellSlice.first + 2,    // PY1 the axe on the prisoner as it falls (SV 39)
        SPELL_PY_GRIEVOUS_WOUND = kSpellSlice.first + 3,    // PY2 heroic bleed, 3% a second until healed to 95%
        SPELL_PY_GRIEVOUS_LOOK  = kSpellSlice.first + 4,    // PY2 the one-shot as a wound opens (SV 121)
        SPELL_PY_OFFERINGS      = kSpellSlice.first + 5,    // PY3 normal: +10% damage done a stack, 4 stacks
        SPELL_PY_BLOOD_PRICE    = kSpellSlice.first + 6,    // PY16 heroic: +0.5% damage done a stack, no cap
        SPELL_PY_CHAIN          = kSpellSlice.first + 7,    // PY1 the rope (SV 9275): a channel field, never cast
        // kSpellSlice.first + 8 .. last: spare (D4b has its own slice)
    };
    static_assert(kSpellSlice.Contains(SPELL_PY_BEHEAD_BAR), "the Block's spells sit in its slice");
    static_assert(kSpellSlice.Contains(SPELL_PY_CHAIN), "the Block's spells sit in its slice");

    // Stock, cast as they are (SP "Stock kit": Keep): the stance on aggro, Cleave between Blocks.
    std::uint32_t constexpr SPELL_BERSERKER_STANCE = 7366;
    std::uint32_t constexpr SPELL_CLEAVE = 15496;

    // Registry tags (the build spec's PY numbers; 10+ for the helpers).
    enum BlockTags : std::uint32_t
    {
        TAG_BLOCK       = 1,    // PY1 the Soak on the prisoner
        TAG_BEHEAD_HIT  = 11,   // PY1 the axe on the soaker (the kit's RegistryHit)
    };

    // Texts (creature_text 7274; groups as SP prints them, rule 34): 0-1 stock, 2 new (the SQL rev).
    enum BlockTexts : std::uint8_t
    {
        SAY_AGGRO   = 0,    // "Let the executions begin!" (stock, yell)
        SAY_KILL    = 1,    // "Justice is done!" (stock, yell; a player or a prisoner)
        YELL_BLOCK  = 2,    // "To the block, $n!" (PY1, names the prisoner)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (SP Build spec 1346-1432, "Tuning starting points"; section 7 #43 A, #44 A; section 3.5 rule 32)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // PY1 the Block: first at 10 s, then every 20 s on normal; heroic gaps 18 s, 16 s, 14 s ... (each 2 s
        // shorter, ruling 46: no floor of its own). Section 7 #43 A (a): a new Block never starts before the last one
        // ends, so the practical floor is the cast plus a second: kBlockGapFloorMs.
        std::uint32_t constexpr kBlockFirstMs = 10000;
        std::uint32_t constexpr kBlockEveryMs = 20000;
        std::uint32_t constexpr kBlockGapFirstMsH = 18000;
        std::uint32_t constexpr kBlockGapStepMsH = 2000;
        // The 4 s Behead bar (both difficulties), not kickable, Physical (he has no kickable cast at all).
        std::uint32_t constexpr kBeheadCastMs = 4000;
        std::uint32_t constexpr kBlockGapFloorMs = kBeheadCastMs + 1000;
        static_assert(kBeheadCastMs >= ZulFarrakRework::kWarningFloorMs, "the Behead bar meets the warning floor");
        static_assert(kBlockGapFirstMsH >= kBlockGapFloorMs, "the heroic gaps shrink toward the floor");
        // The prisoner is torn from the cage and jumps to the chain (CR, about 1 s; CR's own timeout teleports at
        // 3 s): the bar starts when CR reports Chained, at the latest after kChainWaitMs.
        std::uint32_t constexpr kChainWaitMs = 3500;
        // A Block due while every living fighter is busy (one jumping back to the cage) waits this long.
        std::uint32_t constexpr kBlockRetryMs = 500;

        // PY1 the soak: 2 yd around the prisoner (the Soak's marker), one body, tank included. The axe hits one
        // soaker: a soaker without a wound first, then the nearest. Normal 40%, heroic 60% (the tank row on the
        // tank); heroic, a soaker still carrying Grievous Wound takes 150% (section 7 #43 A (c): the bots refuse
        // them, a human may still take it). A soak: no Weakened.
        float constexpr kSoakRadiusYd = 2.f;
        float constexpr kSoakZToleranceYd = 3.f;
        inline constexpr NH<float> kBeheadPct{ 40.f, 60.f };
        float constexpr kBeheadWoundedPctH = 150.f;

        // Where the prisoner is chained: kChainDistYd from him, behind him (away from his victim) first, then
        // turning by kChainStepDeg either way, on the top's floor within kChainZBandYd of his height.
        float constexpr kChainDistYd = 2.5f;
        float constexpr kChainStepDeg = 45.f;
        float constexpr kChainZBandYd = 1.5f;

        // PY2 Grievous Wound (heroic): Physical, 3% of the reference row a second (the kit's
        // spell_dungeon_refflat_periodic: 300 hundredths), until the carrier is healed to 95% or more.
        std::uint32_t constexpr kWoundTickHundredths = 300;
        std::uint32_t constexpr kWoundTickMs = 1000;
        float constexpr kWoundClearPct = 95.f;

        // PY3 Offerings (normal): +10% damage done a stack, one per crew member lost on the Block, cap 4
        // (ZulFarrakRework.h kOfferingsCap).
        std::int32_t constexpr kOfferingsPctPerStack = 10;
        // PY16 Blood Price (heroic): +0.5% damage done a stack, one stack a second while any player bleeds, no cap
        // (30 at once per crew member lost on the Block: the instance). The aura shows at most 255 stacks.
        float constexpr kBloodPricePctPerStack = 0.5f;
        std::uint32_t constexpr kBloodPriceTickMs = 1000;
        std::uint32_t constexpr kAuraStackLimit = 255;
        std::uint32_t constexpr kBloodPriceLogEvery = 10;

        // The Sandfury watch (PyramidFight.h PyramidBuffs): wound polls and buff refreshes.
        std::uint32_t constexpr kWoundPollMs = 250;
        std::uint32_t constexpr kBuffRefreshMs = 1000;
        static_assert(kBloodPriceTickMs % kWoundPollMs == 0, "the bleed meter counts whole polls");

        // PY15 steady pressure: stock Cleave (SmartAI 7274: first 3 to 8 s, then every 7 to 11 s); stock "Justice
        // is done!" at most every 5 s.
        std::uint32_t constexpr kCleaveFirstMinMs = 3000;
        std::uint32_t constexpr kCleaveFirstMaxMs = 8000;
        std::uint32_t constexpr kCleaveMinMs = 7000;
        std::uint32_t constexpr kCleaveMaxMs = 11000;
        std::uint32_t constexpr kKillLineCooldownMs = 5000;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Block's clock (PY1). One Block at a time: due at kBlockFirstMs, the next one a gap after each start (the gap
    // shrinks on heroic), never while one is running; a due Block with nobody free to take waits kBlockRetryMs.
    // ----------------------------------------------------------------------------------------------------------------

    // The gap from the start of Block number `gapIndex` (0 = the first Block) to the start of the next one.
    constexpr std::uint32_t BlockGapMs(std::uint32_t gapIndex, bool heroic)
    {
        if (!heroic)
            return Tune::kBlockEveryMs;
        std::uint32_t const room = Tune::kBlockGapFirstMsH - Tune::kBlockGapFloorMs;
        if (gapIndex > room / Tune::kBlockGapStepMsH)
            return Tune::kBlockGapFloorMs;      // past the floor (no unsigned wrap in a long fight)
        return std::max(Tune::kBlockGapFirstMsH - Tune::kBlockGapStepMsH * gapIndex, Tune::kBlockGapFloorMs);
    }

    // How many Blocks have started by `ms` into the pull, by the gaps alone (a Block running past its successor's due
    // time only delays it). The handoff's timelines (section 3.6) read it.
    constexpr std::uint32_t BlocksBy(std::uint32_t ms, bool heroic)
    {
        std::uint32_t n = 0;
        for (std::uint32_t at = Tune::kBlockFirstMs; at <= ms; at += BlockGapMs(n - 1, heroic))
            ++n;
        return n;
    }

    struct BlockClock
    {
        std::uint32_t now = 0;
        std::uint32_t nextDue = Tune::kBlockFirstMs;
        std::uint32_t started = 0;      // Blocks begun this pull
        bool busy = false;              // a Block is running (from the tear to the axe)
        bool exhausted = false;         // no fighter left to take: no more Blocks this pull

        void Advance(std::uint32_t diff) { now += diff; }
        constexpr bool Due() const { return !busy && !exhausted && now >= nextDue; }

        // A Block begins now: the next one is due a gap after this start.
        void Start(bool heroic)
        {
            busy = true;
            nextDue = now + BlockGapMs(started, heroic);
            ++started;
        }

        // The axe fell (or the Block was given up): the next one may start once due.
        void End() { busy = false; }

        // Due, but nobody is free (a prisoner on the way back): try again shortly.
        void Retry() { nextDue = now + Tune::kBlockRetryMs; }

        // Every fighter is dead: the Executioner just fights.
        void Exhaust() { exhausted = true; }
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    // The prisoner among the CrewMember bits of `candidates` (BlyCrew.h PrisonerCandidates: alive, Caged, free; never
    // Weegli): the `roll`-th set bit (roll taken modulo the count). Nothing when the mask is empty.
    constexpr std::optional<std::uint32_t> PickPrisoner(std::uint32_t candidates, std::uint32_t roll)
    {
        candidates &= ZulFarrakRework::kCrewFighters;
        std::uint32_t count = 0;
        for (std::uint32_t m = 0; m < ZulFarrakRework::kCrewCount; ++m)
            if (candidates & ZulFarrakRework::CrewBit(m))
                ++count;
        if (!count)
            return std::nullopt;
        std::uint32_t n = roll % count;
        for (std::uint32_t m = 0; m < ZulFarrakRework::kCrewCount; ++m)
        {
            if (!(candidates & ZulFarrakRework::CrewBit(m)))
                continue;
            if (!n)
                return m;
            --n;
        }
        return std::nullopt;
    }

    // A player near the prisoner when the axe falls.
    struct SoakerCandidate
    {
        float distance = 0.f;       // 2D, to the prisoner
        float dz = 0.f;             // height difference
        bool wounded = false;       // carries Grievous Wound
    };

    struct SoakerPick
    {
        std::size_t index = 0;
        bool wounded = false;
    };

    constexpr bool InsideSoak(SoakerCandidate const& c)
    {
        return c.distance <= Tune::kSoakRadiusYd && (c.dz < 0.f ? -c.dz : c.dz) <= Tune::kSoakZToleranceYd;
    }

    // The one body the axe falls on: inside the 2 yd, a soaker without a wound before a wounded one, then the nearest
    // (ties to the lower index). Nothing: nobody soaked, the prisoner dies.
    inline std::optional<SoakerPick> PickSoaker(std::vector<SoakerCandidate> const& candidates)
    {
        std::optional<SoakerPick> best;
        float bestDistance = 0.f;
        for (std::size_t i = 0; i < candidates.size(); ++i)
        {
            SoakerCandidate const& c = candidates[i];
            if (!InsideSoak(c))
                continue;
            bool const better = !best || (best->wounded && !c.wounded)
                || (best->wounded == c.wounded && c.distance < bestDistance);
            if (better)
            {
                best = SoakerPick{ i, c.wounded };
                bestDistance = c.distance;
            }
        }
        return best;
    }

    // The Behead on its soaker, percent of the reference row (the tank row on the tank).
    constexpr float BeheadPct(bool heroic, bool wounded)
    {
        if (heroic && wounded)
            return Tune::kBeheadWoundedPctH;
        return Tune::kBeheadPct(heroic);
    }

    // The chain spot candidates, in order: kChainDistYd from `boss`, first at `away` (the bearing from his victim to
    // him: behind him), then kChainStepDeg either way, 2 x, 3 x, and straight at the victim last. The engine keeps the
    // first one on the top's floor and near his height.
    inline std::array<Vec2, 8> ChainSpotCandidates(Vec2 boss, float away)
    {
        float const step = Tune::kChainStepDeg * DungeonKit::kPi / 180.f;
        std::array<float, 8> constexpr turns{ { 0.f, 1.f, -1.f, 2.f, -2.f, 3.f, -3.f, 4.f } };
        std::array<Vec2, 8> out{};
        for (std::size_t i = 0; i < turns.size(); ++i)
            out[i] = DungeonKit::Advance(boss, away + turns[i] * step, Tune::kChainDistYd);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The Pyramid-wide pieces (PyramidFight.h is their engine half)
    // ----------------------------------------------------------------------------------------------------------------

    // The Sandfury of the encounter that carry Offerings / Blood Price (SP PY3, PY16: "the climbers, Sezz'ziz,
    // Nekrum"; the Executioner from PY1 on). GetEntry() is the normal entry on heroic too. Never the barrel 301018 or
    // the stalker 301019.
    std::uint32_t constexpr kSandfurySlave = 7787;
    std::uint32_t constexpr kSandfuryDrudge = 7788;
    inline std::array<std::uint32_t, 8> constexpr kPyramidSandfury{ {
        ZulFarrakRework::NPC_EXECUTIONER, ZulFarrakRework::NPC_SEZZZIZ, ZulFarrakRework::NPC_NEKRUM, kSandfurySlave,
        kSandfuryDrudge, ZulFarrakRework::NPC_ZF_SANDFURY_BERSERKER, ZulFarrakRework::NPC_ZF_SANDFURY_HEXMASTER,
        ZulFarrakRework::NPC_ZF_SANDFURY_WITCH_DOCTOR,
    } };

    constexpr bool IsPyramidSandfury(std::uint32_t entry)
    {
        for (std::uint32_t e : kPyramidSandfury)
            if (e == entry)
                return true;
        return false;
    }

    // PY2: the wound ends once the carrier is healed to 95% or more.
    constexpr bool WoundClears(float healthPct)
    {
        return healthPct >= Tune::kWoundClearPct;
    }

    // PY3: the stacks the Offerings aura shows (the instance's count, at most its cap).
    constexpr std::uint32_t OfferingsStacks(std::uint32_t offerings)
    {
        return std::min(offerings, ZulFarrakRework::kOfferingsCap);
    }

    // PY16: the damage done percent of `total` Blood Price stacks (0.5% each, rounded down: an aura amount is whole),
    // and the stacks the aura shows (its counter stops at 255; the damage does not).
    constexpr std::int32_t BloodPriceDamagePct(std::uint32_t total)
    {
        return std::int32_t(total / 2u);
    }
    static_assert(Tune::kBloodPricePctPerStack == 0.5f, "BloodPriceDamagePct halves the stacks");

    constexpr std::uint32_t BloodPriceShownStacks(std::uint32_t total)
    {
        return std::min(total, Tune::kAuraStackLimit);
    }

    // PY16: one stack for each full second of bleeding (any player carrying a wound), counted at the watch's polls.
    // A poll without bleeding keeps the partial second (a wound healed and a new one opened soon after count on).
    struct BleedMeter
    {
        std::uint32_t ms = 0;

        // The stacks this poll earned.
        std::uint32_t Advance(std::uint32_t diff, bool bleeding)
        {
            if (!bleeding)
                return 0;
            ms += diff;
            std::uint32_t const stacks = ms / Tune::kBloodPriceTickMs;
            ms %= Tune::kBloodPriceTickMs;
            return stacks;
        }

        void Reset() { ms = 0; }
    };

    // A Blood Price total crossing a multiple of kBloodPriceLogEvery (the log line's pace).
    constexpr bool BloodPriceLogs(std::uint32_t before, std::uint32_t after)
    {
        return after / Tune::kBloodPriceLogEvery != before / Tune::kBloodPriceLogEvery;
    }
}

#endif
