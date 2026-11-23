/*
 * mod-dungeon-bosses, Scarlet Monastery D12:
 * Brother Aldous Thorne, the Gardener (300946), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-4-cathedral.md "Brother Aldous Thorne, the Gardener" (GD1-GD3, Build spec), handoff
 * section 3.5 row D12, 3.6, 3.8 (the lower garden), 7 #32 A (his spot off the pond). Tested by
 * tests/sm_thorne_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsThorne (213060-213099), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/thorne.py
 *   Garden     the dry floor south of the pond (the bots' bounds), the leash frame, his spot and facing, the moved
 *              Centurion's new spot
 *   Cycle      the 20 s cycle from the first Prune (T = 5 s): the Prune every 10 s, the Sow at T+1, Bless the Harvest
 *              at T+4 (heroic), Holy Water at T+12
 *   Tuning     NH<> percents, sizes and timers straight from the build spec (percents of the reference row: N level 40
 *              normal, H level 60 heroic)
 *   Picks      the furrow's spot, the sweep's cut, the bloom's clock, the briar cap, the pollen's rise
 */

#ifndef MOD_DUNGEON_BOSSES_SM_THORNE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_THORNE_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <cstddef>
#include <cstdint>

namespace SmThorne
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsThorne;

    enum ThorneSpells : std::uint32_t
    {
        SPELL_GD_BLESSED_GRAIN = kSpellSlice.first + 0,  // 213060 GD1 the carrier's 5 s debuff (Seed Pod's look)
        SPELL_GD_PLANT_LOOK = kSpellSlice.first + 1,  // 213061 GD1 the seed taking root / budding (on the seedling)
        SPELL_GD_PRUNE = kSpellSlice.first + 2,  // 213062 GD1a the sweep on others (resolve copy, Physical)
        SPELL_GD_PRUNE_TANK = kSpellSlice.first + 3,  // 213063 GD1a the sweep on the tank (kit percent script)
        SPELL_GD_PRUNE_LOOK = kSpellSlice.first + 4,  // 213064 GD1a the scythe's sweep (a look on him)
        SPELL_GD_BLOOM = kSpellSlice.first + 5,  // 213065 GD1c the bloom's burst (resolve copy, Holy)
        SPELL_GD_BLOOM_LOOK = kSpellSlice.first + 6,  // 213066 GD1c the bloom at the seedling (a look)
        SPELL_GD_BRIAR = kSpellSlice.first + 7,  // 213067 GD1d a briar's tick (resolve copy, Nature; normal)
        SPELL_GD_BRIAR_SLOW = kSpellSlice.first + 8,  // 213068 GD1d / GD1e the briar's 50% slow (the ticks' rider)
        SPELL_GD_BRIAR_LOOK = kSpellSlice.first + 9,  // 213069 GD1d / GD1e the thorns (an aura on the briar, bramble)
        SPELL_GD_BRAMBLE_BRIAR = kSpellSlice.first + 10,  // 213070 GD1e the bramble's briar tick (resolve copy)
        SPELL_GD_POLLEN = kSpellSlice.first + 11,  // 213071 GD1f a Blessed Pollen pulse (Holy, custom value)
        SPELL_GD_POLLEN_LOOK = kSpellSlice.first + 12,  // 213072 GD1f the pollen's glow (an aura on the bramble)
        SPELL_GD_HOLY_WATER_CAST = kSpellSlice.first + 13,  // 213073 GD2 the 2.5 s bar (Holy, not interruptible)
        SPELL_GD_HOLY_WATER = kSpellSlice.first + 14,  // 213074 GD2 the splash (resolve copy, Holy)
        SPELL_GD_BLESSED_GROUND_LOOK = kSpellSlice.first + 15,  // 213075 GD2a the ground (an aura on a stalker)
        SPELL_GD_BLESSED_GROUND_HEAL = kSpellSlice.first + 16,  // 213076 GD2a his heal while he stands in it
        SPELL_GD_BLESS_THE_HARVEST = kSpellSlice.first + 17,  // 213077 GD3 the 2.5 s interruptible cast (Nature)
        // 213078-213099 spare
    };
    static_assert(SPELL_GD_BLESS_THE_HARVEST <= kSpellSlice.last, "Thorne's spells must stay in his slice");

    // Registry tags (the build spec's mechanic ids: GD1 = 1, GD1a = 11, GD1c = 13 ...; the failure ledger and the
    // playtest greps key on them).
    enum ThorneTags : std::uint32_t
    {
        TAG_GD_SOW              = 1,    // GD1 the furrow (Spot, the carriers)
        TAG_GD_PRUNE            = 11,   // GD1a the sweep (Frontal)
        TAG_GD_BLOOM            = 13,   // GD1c a bloom's burst
        TAG_GD_BRIAR            = 14,   // GD1d a briar (normal, persistent)
        TAG_GD_BRAMBLE_BRIAR    = 15,   // GD1e a bramble's briar (heroic, persistent until it dies)
        TAG_GD_HOLY_WATER       = 2,    // GD2 the splash round him
        TAG_GD_BLESSED_GROUND   = 21,   // GD2a the ground (heroic, the tank only, no damage)
    };

    // creature_text groups of 300946 (data/sql/updates/pending_db_world/rev_thorne_scarlet_monastery.sql, CATH "Text").
    enum ThorneTexts : std::uint8_t
    {
        SAY_PULL            = 0,    // yell: "Weeds in the Light's garden. I know what to do with weeds."
        SAY_SOW             = 1,    // say (GD1): "The furrow is ready. Sow!"
        SAY_BLESS           = 2,    // yell (GD3, heroic): "The Light blesses this harvest!"
        EMOTE_HOLY_WATER    = 3,    // boss emote (GD2): "%s raises the aspergillum!"
        EMOTE_BLOOM         = 4,    // boss emote (GD1c, the first bloom of a cycle): "The untended seed blooms..."
        SAY_KILL            = 5,    // yell: "Pulled up by the root."
        SAY_DEATH           = 6,    // yell: "Nothing grows... from tainted soil..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The lower garden (handoff 3.8, NAVMESH "Thorne", navmesh/maps3.txt "Thorne lower garden"; +x north, +y west).
    // A sunken garden at z 16 to 20; the pond (x 923-958, y 1387-1413, ground z 18, water to z 19.3-20) and the canal
    // (x 960-982) split it. South of the pond the dry floor runs unbroken from x 887 to 922 and y 1357 to 1441 (a few
    // trees at x 894). The raised cloister walk (z 28 to 32) is off the arena.
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kGardenFloorZ = 18.1f;

    // His spot (section 7 #32 A: clearance 14.9 yd, the doc's (932, 1400) is in the pond) and his facing: west (+y),
    // the doc's facing, along the dry floor's long axis (40 yd of floor ahead of him, 42 behind).
    inline constexpr Point3 kThorneSpawn = ScarletMonasteryRework::kThorneSpot;
    inline constexpr float kThorneSpawnFacing = 1.5708f;

    // The stock Scarlet Centurion that stood on his spot (guid 39953, (909.231, 1399.03, 18.1066), random movement
    // 5 yd) moves to the garden's west edge, 39 yd from him, between the corner Sorcerer (894.8, 1437.7) and Centurion
    // (931.6, 1437.6) spawns: the SQL rev.
    inline constexpr std::uint32_t kMovedCenturionGuid = 39953;
    inline constexpr Point3 kMovedCenturionSpot{ 908.5f, 1438.0f, 18.76f };

    // The dry floor south of the pond (the bots' planned spots stay on it, rule 12).
    struct Box
    {
        float minX;
        float maxX;
        float minY;
        float maxY;

        constexpr bool Contains(Vec2 p) const
        {
            return p.x >= minX && p.x <= maxX && p.y >= minY && p.y <= maxY;
        }
    };

    inline constexpr Box kDryFloor{ 887.f, 922.f, 1357.f, 1441.f };
    inline constexpr Box kPond{ 923.f, 958.f, 1387.f, 1413.f };
    inline constexpr float kDryZMin = 15.f;
    inline constexpr float kDryZMax = 23.f;

    constexpr float DryFloorAreaSqYd()
    {
        return (kDryFloor.maxX - kDryFloor.minX) * (kDryFloor.maxY - kDryFloor.minY);
    }

    // The point moved onto the dry floor (a furrow ahead of a boss dragged to the pond's edge).
    constexpr Vec2 ClampToDry(Vec2 p)
    {
        return { std::clamp(p.x, kDryFloor.minX, kDryFloor.maxX), std::clamp(p.y, kDryFloor.minY, kDryFloor.maxY) };
    }

    // His leash frame: the whole lower garden (the pond and the side strips included, so a tank or a player who wades
    // in still counts), z 15-25 (the cloister walk at z 28-32 and the upper garden's stairs are off it).
    inline DungeonKit::Arena GardenArena()
    {
        return DungeonKit::Arena(ScarletMonasteryRework::BoxRegion(885.f, 968.f, 1355.f, 1443.f, 15.f, 25.f));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The cycle (Build spec: "Cycle times are from the Prune that lands at 5 s (T); every later cycle repeats at
    // T + 20 s")
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kCycleMs = 20000;

    // GD1a Prune: lands at 5 s, then every 10 s; a 2 s wind-up (the cone marker) before each.
    inline constexpr std::uint32_t kPruneFirstMs = 5000;
    inline constexpr std::uint32_t kPruneEveryMs = 10000;
    inline constexpr std::uint32_t kPruneWarnMs = 2000;

    // GD1 Sow: at 6 s (T+1), then every 20 s; the debuff 5 s, the seed planted where each carrier stands as it ends.
    inline constexpr std::uint32_t kSowFirstMs = 6000;
    inline constexpr std::uint32_t kSowDebuffMs = 5000;

    // GD3 Bless the Harvest (heroic): at 9 s (T+4), then every 20 s; a 2.5 s cast that ends just after the seeds are
    // planted (T+6.5).
    inline constexpr std::uint32_t kBlessFirstMs = 9000;
    inline constexpr std::uint32_t kBlessCastMs = 2500;

    // GD2 Holy Water: at 17 s (T+12), then every 20 s; a 2.5 s cast (T+12 to T+14.5).
    inline constexpr std::uint32_t kHolyWaterFirstMs = 17000;
    inline constexpr std::uint32_t kHolyWaterCastMs = 2500;

    // The cast has not taken yet this long after the call (the AI waits before reading it as gone).
    inline constexpr std::uint32_t kCastStartGraceMs = 250;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec "Mechanics"; percents of the reference row: N level 40 normal, H level 60 heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // Health at 5 players (handoff 3.6; not flex): 60k (HealthModifier 48.940 on the level 40 paladin base 1,226) and
    // 300k heroic (WP-H's override); the Blessed Bramble 8k on heroic (HANDOFF section 10 add sizing C, 2026-11-20: was
    // 15k, a one-mistake wipe for a bot group).
    inline constexpr std::uint32_t kThorneHealthNormal = 60000;
    inline constexpr std::uint32_t kThorneHealthHeroic = 300000;
    inline constexpr std::uint32_t kBrambleHealthHeroic = 8000;

    // GD1 Sow: 2 (heroic 3) random players, the tank included; the furrow a 3 yd circle 5 yd along his facing (inside
    // the Prune's cone). The bot tank holds his facing while the seeds are out (SM-BM F6).
    inline constexpr NH<std::uint32_t> kCarriers{ 2, 3 };
    inline constexpr float kFurrowAheadYd = 5.f;
    inline constexpr float kFurrowRadiusYd = 3.f;

    // GD1a Prune: a 120 degree cone 8 yd ahead of him; the tank 15% (25%) of the tank row, anyone else 30% (45%)
    // Physical and Weakened; every seedling inside is cut.
    inline constexpr float kPruneAngleDeg = 120.f;
    inline constexpr float kPruneLengthYd = 8.f;
    inline constexpr NH<float> kPrunePct{ 30.f, 45.f };
    inline constexpr NH<float> kPruneTankPct{ 15.f, 25.f };

    // GD1c Bloom: a seedling no sweep cut blooms 15 s (heroic 10 s) after it was planted, a 2 s marker as the bud opens
    // (from 13 s / 8 s); 6 yd round it, 20% (30%) Holy and Weakened, the tank row on the tank. It sprouts, then buds at
    // half its time (the model grows from SEEDLING_SCALE_RANGE's 0.5 to 1.0).
    inline constexpr NH<std::uint32_t> kBloomAfterMs{ 15000, 10000 };
    inline constexpr std::uint32_t kBloomWarnMs = 2000;
    inline constexpr float kBloomRadiusYd = 6.f;
    inline constexpr NH<float> kBloomPct{ 20.f, 30.f };
    inline constexpr float kSeedlingSproutScale = 0.5f;
    inline constexpr float kSeedlingBudScale = 1.0f;

    // GD1d Briar (normal): a 4 yd patch at the bloom for the rest of the fight, 10% Nature a second, slowed 50% inside
    // (no Weakened); at most six, a seventh withers the oldest.
    inline constexpr float kBriarRadiusYd = 4.f;
    inline constexpr float kBriarPct = 10.f;
    inline constexpr std::uint32_t kBriarTickMs = 1000;
    inline constexpr std::uint32_t kBriarLastMs = 600000;          // "the rest of the fight": a 10 minute ceiling
    inline constexpr std::size_t kBriarCap = 6;
    inline constexpr std::uint32_t kBriarSlowPct = 50;

    // GD1e Blessed Bramble (heroic): a rooted 8k add at the bloom, a 5 yd briar round it (15% Nature a second, slowed
    // 50%) until it dies.
    inline constexpr float kBrambleBriarRadiusYd = 5.f;
    inline constexpr float kBrambleBriarPct = 15.f;

    // GD1f Blessed Pollen (heroic): every 2 s from 2 s after the bramble grows, to everyone: 1% on the first pulse, 1%
    // more each pulse, at most 20% (reached on the 20th pulse, 40 s).
    inline constexpr std::uint32_t kPollenEveryMs = 2000;
    inline constexpr std::uint32_t kPollenFirstMs = 2000;
    inline constexpr float kPollenStepPct = 1.f;
    inline constexpr float kPollenCapPct = 20.f;

    // GD2 Holy Water: 10 yd (heroic 12) round him, 30% (45%) Holy and Weakened, the tank row on the tank; he stands
    // still and keeps his facing for the cast.
    inline constexpr NH<float> kHolyWaterRadiusYd{ 10.f, 12.f };
    inline constexpr NH<float> kHolyWaterPct{ 30.f, 45.f };

    // GD2a Blessed ground (heroic): 8 yd where he stood for the Holy Water, for 8 s; nothing to players (the tank alone
    // is told to leave it, which drags him off); while he stands in it he heals 1% of his health a second.
    inline constexpr float kBlessedGroundRadiusYd = 8.f;
    inline constexpr std::uint32_t kBlessedGroundMs = 8000;
    inline constexpr std::uint32_t kBlessedGroundTickMs = 1000;
    inline constexpr float kBlessedGroundHealPct = 1.f;

    // Bots: the measured add throughput of a 3-DPS bot group at 60 (LESSONS 4.2, rule 20) against the spec's two DPS.
    inline constexpr float kBotAddDps = 700.f;
    inline constexpr float kSpecTwoDps = 1700.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Picks
    // ----------------------------------------------------------------------------------------------------------------

    // GD1: the furrow, 5 yd along his facing, kept on the dry floor.
    inline Vec2 FurrowSpot(Vec2 boss, float facing)
    {
        return ClampToDry(DungeonKit::Advance(boss, facing, kFurrowAheadYd));
    }

    // GD1b Cut: is a seedling at `seedling` inside the sweep of a boss at `boss` facing `facing` (`reach` his combat
    // reach)?
    inline bool CutBy(Vec2 boss, float facing, Vec2 seedling, float reach)
    {
        return DungeonKit::InFrontalCone(boss, facing, seedling, kPruneAngleDeg, kPruneLengthYd, reach);
    }

    // GD1c: when a seedling's bloom marker starts (from its planting).
    constexpr std::uint32_t BloomMarkerAtMs(bool heroic)
    {
        return kBloomAfterMs(heroic) - kBloomWarnMs;
    }

    // GD1c: when it buds (half its time).
    constexpr std::uint32_t BudAtMs(bool heroic)
    {
        return kBloomAfterMs(heroic) / 2;
    }

    // The Prune that lands `n` sweeps after the first one (n from 0), from the pull.
    constexpr std::uint32_t PruneLandsAtMs(std::uint32_t n)
    {
        return kPruneFirstMs + n * kPruneEveryMs;
    }

    // The Sow of cycle `n` (n from 0), from the pull, and when its seeds go into the ground.
    constexpr std::uint32_t SowAtMs(std::uint32_t n)
    {
        return kSowFirstMs + n * kCycleMs;
    }

    constexpr std::uint32_t PlantAtMs(std::uint32_t n)
    {
        return SowAtMs(n) + kSowDebuffMs;
    }

    // How many Prunes land on a seed of cycle `n` before it blooms (a Prune landing during the bloom's marker still
    // cuts it). The spec: normal two sweeps can cut it, heroic one.
    constexpr std::uint32_t SweepsBeforeBloom(std::uint32_t n, bool heroic)
    {
        std::uint32_t const plant = PlantAtMs(n);
        std::uint32_t const bloom = plant + kBloomAfterMs(heroic);
        std::uint32_t count = 0;
        for (std::uint32_t k = 0; PruneLandsAtMs(k) < bloom; ++k)
            if (PruneLandsAtMs(k) > plant)
                ++count;
        return count;
    }

    // GD1f: the pollen of the bramble's `pulse`th pulse (from 1), a percent of the reference row.
    constexpr float PollenPct(std::uint32_t pulse)
    {
        return pulse == 0 ? 0.f : std::min(kPollenStepPct * static_cast<float>(pulse), kPollenCapPct);
    }

    // The pollen one bramble has dealt to each player after `pulses` pulses.
    constexpr float PollenTotalPct(std::uint32_t pulses)
    {
        float total = 0.f;
        for (std::uint32_t k = 1; k <= pulses; ++k)
            total += PollenPct(k);
        return total;
    }

    // The pulses a bramble gets off before `dps` kills it (it pulses at 2 s, 4 s, ...).
    inline std::uint32_t PulsesBeforeKill(float dps)
    {
        if (dps <= 0.f)
            return 0;
        float const killMs = static_cast<float>(kBrambleHealthHeroic) / dps * 1000.f;
        if (killMs < static_cast<float>(kPollenFirstMs))
            return 0;
        return static_cast<std::uint32_t>((killMs - static_cast<float>(kPollenFirstMs))
            / static_cast<float>(kPollenEveryMs)) + 1u;
    }

    // GD1d: the briars to wither (the oldest first) before a new one grows while `standing` stand.
    constexpr std::size_t BriarsToWither(std::size_t standing)
    {
        return standing >= kBriarCap ? standing - kBriarCap + 1 : 0;
    }

    // GD2a: his heal a tick, from his max health.
    constexpr std::uint32_t BlessedGroundHeal(std::uint32_t maxHealth)
    {
        return static_cast<std::uint32_t>(static_cast<float>(maxHealth) * kBlessedGroundHealPct / 100.f + 0.5f);
    }

    // A recurring timer on the AI's clock (ms since the reset): due at a time, then every `everyMs` after it.
    class Clock
    {
    public:
        void Start(std::uint64_t nowMs, std::uint32_t inMs)
        {
            _on = true;
            _dueMs = nowMs + inMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        std::uint64_t DueMs() const { return _dueMs; }

        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }

        // It fired: the next one is `everyMs` after this one's due time, never in the past.
        void Fired(std::uint64_t nowMs, std::uint32_t everyMs)
        {
            _dueMs += everyMs;
            if (_dueMs <= nowMs)
                _dueMs = nowMs + everyMs;
        }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };
}

#endif
