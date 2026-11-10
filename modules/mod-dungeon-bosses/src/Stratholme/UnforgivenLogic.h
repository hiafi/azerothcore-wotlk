/*
 * mod-dungeon-bosses, Stratholme S1: The Unforgiven (10516), the pure, host-testable part (no engine headers).
 * Build spec ST 616-676 (docs/dungeons/stratholme-rework.md), design ST 441-615, handoff section 3.4 rows UF, section
 * 3.5 row S1, section 3.6 (normal 185k, heroic 250k), section 3.8 #1 (the plaza: two march lanes, two cordons, five
 * bays). Tested by tests/strat_unforgiven_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsUnforgiven (206420-206439), declared in apps/dbc-tools
 *                  source/npcs/stratholme/the_unforgiven.py
 *   Tuning         NH<> constants and Cadence{first, every}: one number per difficulty, straight from the build spec
 *   Lanes          UF1 the two march lanes on their measured frames: the hit line (from past the cordon to the lane's
 *                  far end, the street's full width), the rank's footmen, the march speed
 *   Cordons        UF12 the two lethal walls and what they keep clear (the fire spots / shelters and both march lanes,
 *                  section 3.8's 5 yd placement rule, checked with the kit's KeepsClear)
 *   Fires          UF2-UF4 the spot pick, the cap of 3, the firelight test
 *   Phantoms       UF5-UF9 how a phantom ends (Freed, Bound, Grief) and what it does to Grudge; the Last Soul
 *   Nova           UF10 never in the 6 s before a March lands, nor while a rank is passing
 *
 * Damage percentages are of the reference health row (normal 3,670 / 3,710 tank, heroic 4,120 / 4,110, the 329:60
 * pins): the build spec gives N / H percents.
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_UNFORGIVEN_LOGIC_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_UNFORGIVEN_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitWallLogic.h"
#include "StratholmeRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace StratUnforgiven
{
    using DungeonKit::FrameRect;
    using DungeonKit::KeepClear;
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using DungeonKit::WallLine;

    // Every spell of this WP sits in this slice (StratholmeRework.h; ids.yaml reservation `stratholme`).
    inline constexpr StratholmeRework::IdSlice kSpellSlice = StratholmeRework::kSpellsUnforgiven;

    // Declared in apps/dbc-tools source/npcs/stratholme/the_unforgiven.py (same ids).
    enum UnforgivenSpells : std::uint32_t
    {
        SPELL_UF_MARCH_HIT          = kSpellSlice.first + 0,    // UF1 the rank's hit (resolve copy, Shadow)
        SPELL_UF_HOUSE_FIRE         = kSpellSlice.first + 1,    // UF2 the fire's landing (resolve copy, Fire)
        SPELL_UF_BURNING_HOUSE      = kSpellSlice.first + 2,    // UF3 the burning patch's tick (resolve copy, Fire)
        SPELL_UF_FIRELIGHT          = kSpellSlice.first + 3,    // UF4 the 10 yd glow on the fire stalker (aura)
        SPELL_UF_ACCUSED            = kSpellSlice.first + 4,    // UF5 the accused's debuff (the bots' soak key)
        SPELL_UF_ACCUSED_FLASH      = kSpellSlice.first + 5,    // UF5 the apply flash on the accused (look)
        SPELL_UF_GRIEF              = kSpellSlice.first + 6,    // UF7 a phantom reached its accused: 30% Shadow
        SPELL_UF_GRUDGE             = kSpellSlice.first + 7,    // UF8 his buff: +10% damage done per stack
        SPELL_UF_FREED              = kSpellSlice.first + 8,    // UF6 the tear: 2% of his health (exact amount)
        SPELL_UF_SOUL_FREED         = kSpellSlice.first + 9,    // UF6 the freed phantom's look (Soul Freed 17370)
        SPELL_UF_BOUND              = kSpellSlice.first + 10,   // UF8 a bound soul pours into him (look)
        SPELL_UF_FROST_NOVA         = kSpellSlice.first + 11,   // UF10 8% Frost in 10 yd and a 1.5 s root
        SPELL_UF_HAUNTING_MEMORY    = kSpellSlice.first + 12,   // UF11 heroic: Magic DoT 3%/s, 8 s
        SPELL_UF_IN_FIRELIGHT       = kSpellSlice.first + 13,   // UF4 on a phantom standing in firelight (bots' key)
        // 206434-206439 spare
    };
    static_assert(SPELL_UF_IN_FIRELIGHT <= kSpellSlice.last, "The Unforgiven's spells must stay in his slice");

    // The house fire on the doorway: the stock "Big Barracks Flame" (type 5 generic, GO display 4452,
    // StratholmeFireSmokeEmberM; VISUALS-REPORT "Added C" rank 1), summoned for the burn. No template of ours.
    inline constexpr std::uint32_t GO_UF_HOUSE_FIRE_STOCK = 176746;

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum UnforgivenTags : std::uint32_t
    {
        TAG_MARCH           = 1,    // UF1 the first rank
        TAG_MARCH_CROSSING  = 2,    // UF1 heroic: the crossing rank
        TAG_HOUSE_FIRE      = 3,    // UF2 the landing
        TAG_BURNING_HOUSE   = 4,    // UF3 the burning patch
        TAG_FIRELIGHT       = 5,    // UF4 / UF5 the accused's ring (a telegraph-only Soak)
        TAG_CORDON          = 6,    // UF12 the lethal walls
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (ST "Build spec", "Heroic" and "Tuning starting points", approved 2026-11-02)
    // ----------------------------------------------------------------------------------------------------------------

    struct Cadence
    {
        std::uint32_t first;
        std::uint32_t every;
    };

    // UF1 The March: first at 20 s, every 40 s (start to start). Yell line 1, a 3 s marker, then the rank marches the
    // street in about 2 s; 40% (heroic 45%) Shadow + Weakened to anyone in its path, the tank too. Heroic: the crossing
    // rank down the other lane, its marker 1.5 s after the first rank has passed.
    inline constexpr Cadence kMarch{ 20000, 40000 };
    inline constexpr std::uint32_t kMarchWarnMs = 3000;
    inline constexpr std::uint32_t kMarchPassMs = 2000;
    inline constexpr std::uint32_t kMarchChainWarnMs = 1500;
    inline constexpr NH<float> kMarchPct{ 40.f, 45.f };
    // The rank fades this long after its pass ended.
    inline constexpr std::uint32_t kRankFadeMs = 1000;

    // UF2 / UF3 House fire: first at 8 s, every 25 s (heroic 20 s). Emote line 3, a 2 s 5 yd circle at a doorway: 25%
    // Fire + Weakened; then the patch burns 60 s at 5% a second (no Weakened, no slow). At most 3 burning.
    inline constexpr std::uint32_t kFireFirstMs = 8000;
    inline constexpr NH<std::uint32_t> kFireEveryMs{ 25000, 20000 };
    inline constexpr std::uint32_t kFireWarnMs = 2000;
    inline constexpr float kFireRadius = 5.f;
    inline constexpr float kFireLandPct = 25.f;
    inline constexpr std::uint32_t kFireBurnMs = 60000;
    inline constexpr std::uint32_t kFireTickMs = 1000;
    inline constexpr float kFireBurnPct = 5.f;
    inline constexpr std::uint32_t kFireMaxBurning = 3;
    // A fire that is due while 3 burn waits this long and tries again (the cadence keeps its planned times).
    inline constexpr std::uint32_t kFireRetryMs = 1000;

    // UF4 Firelight: the ring around each burning house, 5 to 10 yd from its doorway (the accused's place). A phantom
    // counts as in the firelight anywhere within 10 yd of a burning house (the patch itself included: it is in the
    // flames).
    inline constexpr float kFirelightInner = kFireRadius;
    inline constexpr float kFirelightOuter = 10.f;
    // The accused's ring is a telegraph-only Soak per fire: up to this many accused may claim one ring (the Last Soul
    // and heroic Haunting Memory can name several at once).
    inline constexpr std::uint8_t kFirelightSoakers = 4;
    inline constexpr std::uint32_t kFirelightSoakWarnMs = 500;

    // UF5 The Accusation: first at 15 s, every 35 s, until the Last Soul. Yell line 2; Accused on a random non-tank; 3
    // phantoms (heroic 4) rise around him (6,000 / 9,000 health: the templates) and drift to the accused.
    inline constexpr Cadence kAccusation{ 15000, 35000 };
    inline constexpr NH<std::uint32_t> kPhantomCount{ 3, 4 };
    inline constexpr NH<std::uint32_t> kPhantomHealth{ 6000, 9000 };
    inline constexpr std::uint32_t kPhantomLifeMs = 20000;
    // A phantom rises (stands still) this long before it drifts.
    inline constexpr std::uint32_t kPhantomRiseMs = 1500;
    // 60% walk speed: 60% of the 2.5 yd/s walk (ST "untauntable, 60% walk speed").
    inline constexpr float kPhantomSpeedYd = 1.5f;
    // Reached: within this of its accused (a touch).
    inline constexpr float kPhantomReachYd = 2.f;
    // Where they rise: this far around him.
    inline constexpr float kPhantomSpawnYd = 3.f;
    // How often a phantom re-aims at its accused.
    inline constexpr std::uint32_t kPhantomRepathMs = 500;

    // UF6 Freed: 2% of his maximum health. UF7 Grief: 30% Shadow on the accused (no Weakened). UF8 Grudge: +10% damage
    // done per stack, uncapped (the aura's own limit, 255, is never reached).
    inline constexpr float kFreedPct = 2.f;
    inline constexpr float kGriefPct = 30.f;
    inline constexpr float kGrudgeDamagePct = 10.f;
    inline constexpr std::uint32_t kGrudgeMaxStacks = 255;

    // UF9 The Last Soul: at 25% health, once.
    inline constexpr float kLastSoulHealthPct = 25.f;

    // UF10 Frost Nova (a copy of 14907): 8% Frost in 10 yd and a 1.5 s root, every 15 to 20 s while a player stands
    // within 10 yd; never in the 6 s before a March lands, nor while a rank is on the floor.
    inline constexpr std::uint32_t kNovaMinMs = 15000;
    inline constexpr std::uint32_t kNovaMaxMs = 20000;
    inline constexpr float kNovaRadius = 10.f;
    inline constexpr float kNovaPct = 8.f;
    inline constexpr std::uint32_t kNovaRootMs = 1500;
    inline constexpr std::uint32_t kNovaQuietMs = 6000;
    inline constexpr std::uint32_t kNovaRetryMs = 500;

    // UF11 Haunting Memory (heroic): first at 12 s, every 30 s, on 2 random non-tanks, 8 s, 3% a second (Magic). Not
    // dispelled before it runs out: a phantom rises from that player, fixated on them. The bots' dispel entry: priority
    // 2, urgent with 3 s left.
    inline constexpr Cadence kHaunting{ 12000, 30000 };
    inline constexpr std::uint32_t kHauntingCount = 2;
    inline constexpr std::uint32_t kHauntingMs = 8000;
    inline constexpr float kHauntingPct = 3.f;
    inline constexpr std::uint8_t kHauntingDispelPriority = 2;
    inline constexpr std::uint32_t kHauntingDeadlineMs = 3000;
    // The phantom rises this far from the carrier, toward the plaza's middle.
    inline constexpr float kHauntingRiseYd = 6.f;

    // The AI's slow tick (phantoms, the firelight marks, the nova's gate): every 250 ms.
    inline constexpr std::uint32_t kHousekeepingMs = 250;

    // The plaza's middle (NAVMESH-REPORT section 1, "X" on its map).
    inline constexpr Vec2 kPlazaCenter{ 3697.0f, -3400.5f };

    // ----------------------------------------------------------------------------------------------------------------
    // UF1 The March: the two lanes (handoff section 3.8 #1)
    // ----------------------------------------------------------------------------------------------------------------

    // A lane on its measured frame: X runs from its cordon (X 0) into the plaza, Y across the street. The rank forms
    // at `formX` (just inside its cordon), steps out to `startX` during the marker and marches to the frame's far end.
    // The hit line starts at `startX`: section 3.8's placement rule keeps every cordon 5 yd outside every march path,
    // so the first yards past a cordon are never marched over (checked by KeepsClear in the test).
    struct MarchLane
    {
        FrameRect frame;
        float formX = 0.f;
        float startX = 0.f;
        std::uint32_t footmen = 0;
        char const* name = "";
    };

    inline constexpr std::size_t kLaneMarketRow = 0;   // L1, 25 yd wide, from the south-west cordon
    inline constexpr std::size_t kLanePassage = 1;     // L2, 12 yd wide, from the east cordon
    inline constexpr std::size_t kLaneCount = 2;

    inline constexpr std::array<MarchLane, kLaneCount> kLanes{ {
        { StratholmeRework::kUnforgivenLaneMarketRow, 1.5f, 8.f, 7, "market-row" },
        { StratholmeRework::kUnforgivenLanePassage, 4.f, 11.f, 4, "passage" },
    } };

    // The other lane (the heroic crossing rank; the normal March alternates).
    constexpr std::size_t OtherLane(std::size_t lane)
    {
        return lane == kLaneMarketRow ? kLanePassage : kLaneMarketRow;
    }

    struct HitLine
    {
        Vec2 from;
        Vec2 to;
        float width = 0.f;

        float Length() const { return DungeonKit::Distance(from, to); }
    };

    // The registry Line: from `startX` to the far end along the lane's middle, the street's full width.
    inline HitLine MarchHitLine(MarchLane const& lane)
    {
        float const mid = lane.frame.sizeY * 0.5f;
        return { DungeonKit::FramePoint(lane.frame, lane.startX, mid),
            DungeonKit::FramePoint(lane.frame, lane.frame.sizeX, mid), lane.frame.sizeY };
    }

    // The march speed: the hit line in kMarchPassMs.
    inline float MarchSpeed(MarchLane const& lane)
    {
        return MarchHitLine(lane).Length() * 1000.f / static_cast<float>(kMarchPassMs);
    }

    // The footman `i` of the lane's rank (0 .. footmen - 1) across the street, at `fx` along it: evenly spread, each in
    // the middle of its share of the width.
    inline Vec2 RankPoint(MarchLane const& lane, std::uint32_t i, float fx)
    {
        float const n = static_cast<float>(std::max<std::uint32_t>(1, lane.footmen));
        float const fy = lane.frame.sizeY * (static_cast<float>(i) + 0.5f) / n;
        return DungeonKit::FramePoint(lane.frame, fx, fy);
    }

    // The footman the registry tracks (ProjectileUnit): the middle one.
    constexpr std::uint32_t RankLeader(MarchLane const& lane)
    {
        return lane.footmen / 2;
    }

    // Is `p` in the lane's marched part (from startX to the far end, the full width)?
    inline bool InMarchPath(MarchLane const& lane, Vec2 p)
    {
        Vec2 const q = DungeonKit::ToFrame(lane.frame, p);
        return q.x >= lane.startX && q.x <= lane.frame.sizeX && q.y >= 0.f && q.y <= lane.frame.sizeY;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF12 The Cordon: the two lethal walls (handoff section 3.8 #1; the kit's LethalWall)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::size_t kCordonEast = 0;
    inline constexpr std::size_t kCordonSouthWest = 1;
    inline constexpr std::size_t kCordonCount = 2;
    inline constexpr float kCordonWidth = DungeonKit::kWallDefaultWidthYd;
    // Footmen standing along each cordon (about 2.5 yd apart): east 12.6 yd, south-west 29.5 yd.
    inline constexpr std::array<std::uint32_t, kCordonCount> kCordonFootmen{ { 5, 11 } };
    // Their floor where the probe finds nothing (NAVMESH-REPORT: east 130.9, south-west 128.5 to 131).
    inline constexpr std::array<float, kCordonCount> kCordonZ{ { 130.9f, 129.8f } };

    inline WallLine CordonWall(std::size_t i)
    {
        auto const& line = i == kCordonEast ? StratholmeRework::kUnforgivenCordonEast
                                            : StratholmeRework::kUnforgivenCordonSouthWest;
        return { line[0], line[1], kCordonWidth };
    }

    // R-2-A A-1: the pull's safety net. A unit closer than this to a cordon's strip when he is pulled (the plaza
    // polygon's edge lies inside the strip, or a pet parked in the inner half of it) is gripped onto the plaza before
    // the walls arm, whether or not the guard's own pull grip saw it as off the arena.
    inline constexpr float kCordonGripClearanceYd = 1.f;

    // Is `p` within kCordonGripClearanceYd of either cordon's strip (inside it included)?
    inline bool NeedsCordonGrip(Vec2 p)
    {
        for (std::size_t c = 0; c < kCordonCount; ++c)
            if (DungeonKit::WallClearance(CordonWall(c), p) < kCordonGripClearanceYd)
                return true;
        return false;
    }

    // The footman `k` of cordon `i`, evenly along it (half a spacing in from each end).
    inline Vec2 CordonPoint(std::size_t i, std::uint32_t k)
    {
        WallLine const w = CordonWall(i);
        float const n = static_cast<float>(std::max<std::uint32_t>(1, kCordonFootmen[i]));
        float const t = (static_cast<float>(k) + 0.5f) / n;
        return { w.from.x + (w.to.x - w.from.x) * t, w.from.y + (w.to.y - w.from.y) * t };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF2-UF4 Fires: the five bays (fire spots and shelters, NAVMESH-REPORT section 1 (c): F1-F4 and F6)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::size_t kFireSpotCount = StratholmeRework::kUnforgivenFireSpots.size();
    // The floor at each bay (the report's z column), for the stalker when the floor probe finds nothing.
    inline constexpr std::array<float, kFireSpotCount> kFireSpotZ{ { 133.0f, 132.3f, 133.1f, 133.7f, 133.1f } };
    // What each bay keeps clear for the placement rule: the fire's 5 yd circle, or the bay's own half extent when it is
    // larger (F2, the passage north bay, 6 x 10 yd).
    inline constexpr std::array<float, kFireSpotCount> kBayKeepClearYd{ { 5.f, 6.f, 5.f, 5.f, 5.f } };

    // The fire spots: the report's bays (StratholmeRework::kUnforgivenFireSpots), F2 moved 2 yd north along its bay
    // (y -3426.5 -> -3424.5, still inside the bay's -3421..-3432) so its 10 yd firelight ring, the accused's place,
    // keeps section 3.8's 5 yd from the east cordon's strip (R-2-A question 1, ORCH F-2 ruling: 3.48 -> 5.46 yd).
    inline constexpr Vec2 kFireSpotF2Moved{ 3719.5f, -3424.5f };

    inline Vec2 FireSpot(std::size_t i)
    {
        return i == 1 ? kFireSpotF2Moved : StratholmeRework::kUnforgivenFireSpots[i];
    }

    // A random free bay (rand(n) in [0, n)); nullopt when every bay burns.
    template <class Rand>
    std::optional<std::size_t> PickFireSpot(std::array<bool, kFireSpotCount> const& burning, Rand&& rand)
    {
        std::vector<std::size_t> free;
        for (std::size_t i = 0; i < kFireSpotCount; ++i)
            if (!burning[i])
                free.push_back(i);
        if (free.empty())
            return std::nullopt;
        return free[rand(static_cast<std::uint32_t>(free.size())) % free.size()];
    }

    // Another fire may light while fewer than 3 burn (a marked fire that has not landed counts).
    constexpr bool FireCanLight(std::uint32_t burningOrMarked)
    {
        return burningOrMarked < kFireMaxBurning;
    }

    // UF4: is `p` within the firelight of any burning house in `lit`?
    inline bool InFirelight(Vec2 p, std::vector<Vec2> const& lit)
    {
        for (Vec2 const& fire : lit)
            if (DungeonKit::Distance(p, fire) <= kFirelightOuter)
                return true;
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The placement rule (section 3.8): what each cordon keeps 5 yd clear of
    // ----------------------------------------------------------------------------------------------------------------

    // A lane's marched part as parallel paths of about `stripHalfWidth` (a wide street as one capsule would round its
    // ends by half the street's width; strips keep the rounding to about a yard).
    inline std::vector<KeepClear> MarchPathKeepClear(MarchLane const& lane, float stripHalfWidth = 1.f)
    {
        std::vector<KeepClear> out;
        std::uint32_t const strips = std::max<std::uint32_t>(1,
            static_cast<std::uint32_t>(std::ceil(lane.frame.sizeY / (2.f * stripHalfWidth))));
        float const hw = lane.frame.sizeY / (2.f * static_cast<float>(strips));
        for (std::uint32_t s = 0; s < strips; ++s)
        {
            float const fy = hw * (2.f * static_cast<float>(s) + 1.f);
            out.push_back(KeepClear::Path(DungeonKit::FramePoint(lane.frame, lane.startX, fy),
                DungeonKit::FramePoint(lane.frame, lane.frame.sizeX, fy), hw));
        }
        return out;
    }

    // The firelight ring of fire spot `i` (UF4: the accused stands in it, so the wall keeps 5 yd from its outer edge).
    inline KeepClear FirelightKeepClear(std::size_t i)
    {
        return KeepClear::Point(FireSpot(i), kFirelightOuter);
    }

    // The five bays (fire spots and shelters), their firelight rings and both march lanes.
    inline std::vector<KeepClear> CordonKeepClear()
    {
        std::vector<KeepClear> out;
        for (std::size_t i = 0; i < kFireSpotCount; ++i)
        {
            out.push_back(KeepClear::Point(FireSpot(i), kBayKeepClearYd[i]));
            out.push_back(FirelightKeepClear(i));
        }
        for (MarchLane const& lane : kLanes)
            for (KeepClear const& k : MarchPathKeepClear(lane))
                out.push_back(k);
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF5-UF9 Phantoms
    // ----------------------------------------------------------------------------------------------------------------

    enum class PhantomEnd : std::uint8_t
    {
        DiedInLight,    // killed within the firelight: Freed
        DiedInDark,     // killed outside it: Bound
        Expired,        // lived 20 s: Bound
        Reached,        // touched its accused: Grief, then Bound
    };

    struct PhantomOutcome
    {
        bool freed = false;         // UF6 the 2% tear and the Soul Freed look
        bool grief = false;         // UF7 30% on the accused
        int grudgeDelta = 0;        // UF8 stacks added (+1) or removed (-1)
    };

    // `returning`: one of the Last Soul's phantoms (a Grudge stack risen again): freeing it removes the stack, binding
    // it again leaves the stack where it is.
    constexpr PhantomOutcome Outcome(PhantomEnd end, bool returning)
    {
        PhantomOutcome o;
        switch (end)
        {
            case PhantomEnd::DiedInLight:
                o.freed = true;
                o.grudgeDelta = returning ? -1 : 0;
                break;
            case PhantomEnd::Reached:
                o.grief = true;
                o.grudgeDelta = returning ? 0 : 1;
                break;
            case PhantomEnd::DiedInDark:
            case PhantomEnd::Expired:
                o.grudgeDelta = returning ? 0 : 1;
                break;
        }
        return o;
    }

    // UF6: 2% of his maximum health, never his last point (the tear is not a kill: loot and the kill credit stay the
    // players').
    inline std::uint32_t FreedAmount(std::uint32_t maxHealth, std::uint32_t health)
    {
        double const v = kFreedPct / 100.0 * static_cast<double>(maxHealth);
        std::uint32_t const tear = static_cast<std::uint32_t>(std::max<long>(0, std::lround(v)));
        if (health <= 1)
            return 0;
        return std::min(tear, health - 1);
    }

    // UF9: the Last Soul starts at 25% health or lower, once.
    constexpr bool LastSoulDue(float healthPct, bool done)
    {
        return !done && healthPct <= kLastSoulHealthPct;
    }

    // UF9: every Grudge stack rises again as a phantom.
    constexpr std::uint32_t LastSoulPhantoms(std::uint32_t grudgeStacks)
    {
        return grudgeStacks;
    }

    // UF5: the rise point of phantom `i` of `n` around him (evenly on a 3 yd ring).
    inline Vec2 PhantomRisePoint(Vec2 boss, std::uint32_t i, std::uint32_t n)
    {
        float const step = DungeonKit::kTwoPi / static_cast<float>(std::max<std::uint32_t>(1, n));
        return DungeonKit::Advance(boss, step * static_cast<float>(i), kPhantomSpawnYd);
    }

    // UF11: where a Haunting Memory's phantom rises: kHauntingRiseYd from the carrier toward the plaza's middle (at
    // most the distance to it).
    inline Vec2 HauntingRisePoint(Vec2 carrier)
    {
        float const d = DungeonKit::Distance(carrier, kPlazaCenter);
        if (d < 0.01f)
            return carrier;
        float const step = std::min(d, kHauntingRiseYd);
        return DungeonKit::Advance(carrier, DungeonKit::BearingTo(carrier, kPlazaCenter), step);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // UF10 The nova's gate
    // ----------------------------------------------------------------------------------------------------------------

    // `nextLandMs`: when the next scheduled March lands (0: none planned); `busyUntilMs`: the end of the ranks on the
    // floor now (the heroic chain included; 0: none).
    constexpr bool NovaAllowed(std::uint64_t nowMs, std::uint64_t nextLandMs, std::uint64_t busyUntilMs)
    {
        if (nowMs < busyUntilMs)
            return false;
        return nextLandMs == 0 || nowMs + kNovaQuietMs < nextLandMs;
    }

    // The next start of a cadence that counts from the planned time, not from a late start.
    constexpr std::uint64_t NextOnCadence(std::uint64_t planned, std::uint64_t now, std::uint32_t every)
    {
        return std::max<std::uint64_t>(planned + every, now + 1);
    }
}

#endif
