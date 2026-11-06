/*
 * mod-dungeon-bosses, Deadmines: VanCleef's hard mode, Burn It Down (WP-B9), the pure, host-testable part (no engine
 * headers): spell ids, tuning numbers, the 3:00 schedule, the fire front's stripes, the powder placement rule, the
 * mainmast, the keg's use rule and the ship's bounds. Build spec: DM 'Hard mode: Burn It Down' and Build spec
 * VC10-VC13; handoff sections 3.4 (VC10-VC13 rows), 3.7, 3.8 (deck frame, stripe depth), 3.10 gap 6, 6 (solver cost).
 *
 * Hard mode is heroic only (the keg is spawned on heroic alone), so its numbers are plain constants, not NH pairs.
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum.
 * Coordinates: map plane, +x north (stern), +y west; the bow points south (-x).
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_HARD_MODE_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_HARD_MODE_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <optional>
#include <vector>

namespace HardMode
{
    using DeadminesKit::Vec2;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsHardMode;

    // Declared in apps/dbc-tools source/npcs/deadmines/vancleef_hard_mode.py. The 3:00 clock aura is the shared
    // SPELL_DM_HARD_MODE_TIMER (205202, K's shared.py); the lingering zones' slow rider is SPELL_DM_STANDING_IN_IT.
    enum HardModeSpells : std::uint32_t
    {
        SPELL_FIRE_FRONT_HIT        = 205380,   // VC10 a stripe lands: resolve copy, Fire (registry 30% + Weakened)
        SPELL_BURNING_DECK_TICK     = 205381,   // VC10 / VC11 / VC12 burning deck, planks and wall: resolve copy, Fire
        SPELL_POWDER_BLAST_HIT      = 205382,   // VC11 the blast: resolve copy, Fire (registry 40% + Weakened)
        SPELL_MAINMAST_HIT          = 205383,   // VC12 the fall: resolve copy, Physical (registry 60%, no Weakened)
        SPELL_POWDER_SPARKS         = 205384,   // VC11 the 2 s sparking marker look: aura on the stalker (SV 6944)
        SPELL_POWDER_BLAST_VISUAL   = 205385,   // VC11 the blast look: self (SV 148, Detonation 4043)
        SPELL_BURNING_LOOK          = 205386,   // VC10-VC12 burning look: aura on the stalkers (SV 4101, On Fire)
        SPELL_MAINMAST_CRASH        = 205387,   // VC12 the landing look: self (SV 9548, Cosmetic - Cannon Impact)
        SPELL_SHIP_EXPLOSION        = 205388,   // VC13 the explosion look: self (SV 13122, Big Bang 64443)
        // 205389 spare
    };

    // Registry tags (the ledger's mechanic id: the build spec's VC number; the burns share their mechanic's tag).
    enum HardModeTags : std::uint32_t
    {
        TAG_FIRE_FRONT  = 10,   // VC10: the landing stripe and the burning deck behind the front
        TAG_POWDER      = 11,   // VC11: the blast and the burning planks
        TAG_MAINMAST    = 12,   // VC12: the fall and the burning wall
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (DM Build spec VC10-VC13; handoff section 3.8 stripe depth, decided by section 7 #10)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kFuseHealth = 500000;            // VanCleef's health while lit (heroic: 340k)
    inline constexpr std::uint32_t kTimerMs = 180000;               // VC13: the ship blows at 3:00

    // VC10 Fire front: a stripe every 10 s from 5 s, 2 s marker, 30% Fire + 1 Weakened on landing, then the deck
    // behind the front burns 10% Fire per second for the rest of the fight.
    inline constexpr std::uint32_t kFrontFirstMs = 5000;
    inline constexpr std::uint32_t kFrontEveryMs = 10000;
    inline constexpr std::uint32_t kFrontWarnMs = 2000;
    inline constexpr float kFrontPct = 30.f;
    inline constexpr float kBurnPct = 10.f;                         // every burn: deck, planks, wall
    inline constexpr std::uint32_t kBurnTickMs = 1000;
    inline constexpr float kStripeDepth = DeadminesRework::kFireFrontStripeDepth;  // 2.73 yd
    // The first stripe's aft edge: the sterncastle face (the keg stands just forward of it, inside stripe 0).
    inline constexpr float kFrontStartX = DeadminesRework::kDeckSternCenter.x;     // -53.5
    // The main-deck side walkways beside the sterncastle (navmesh report: x -39.2 .. -53.5, z ~43, two 4-9 yd strips
    // at y -802.5 .. -811 and -828.5 .. -837): aft of the first stripe, so they burn as one zone of their own from the
    // moment stripe 0 lands (else the group could stand there out of every stripe, blast and the mast). The
    // sterncastle top (z 50-53) stays out of it through the zone's height tolerance.
    inline constexpr float kAftWalkwayX = -39.2f;
    // The burning deck and the wall are replaced at each landing; the old zone is cancelled this long after the new one
    // is registered, so its pass due at the landing still fires and no tick is lost (the new one's first pass is one
    // tick after registration).
    inline constexpr std::uint32_t kRetireDelayMs = 500;
    // Rail to rail: the stripes run across the deck (constant x) from just past the west rail to past the east rail
    // (navmesh deck y -802.5 .. -840, about 1 yd more for real; the narrow bow is overhung, which touches nobody).
    inline constexpr float kStripeWestY = -799.5f;
    inline constexpr float kStripeLength = 42.f;
    inline constexpr float kAcrossFacing = 4.71238898f;             // 3 pi / 2: toward -y (east)

    // VC11 Powder below: every 10 s from 10 s (5 s out of step with the front), 2 s sparking marker, 6 yd, 40% Fire
    // + 1 Weakened, then the planks burn 15 s. A random deck spot ahead of the front, never within 6 yd of a player
    // when placed; skipped when there is none.
    inline constexpr std::uint32_t kPowderFirstMs = 10000;
    inline constexpr std::uint32_t kPowderEveryMs = 10000;
    inline constexpr std::uint32_t kPowderWarnMs = 2000;
    inline constexpr float kPowderRadius = 6.f;
    inline constexpr float kPowderPct = 40.f;
    inline constexpr std::uint32_t kPowderBurnMs = 15000;
    inline constexpr float kPowderMinPlayerYd = 6.f;
    // "Ahead of the front": the spot is at least this far bow-ward of the front as it will be after the next stripe
    // lands (7 s after the blast), so a blast is never placed on deck that is about to burn anyway.
    inline constexpr float kPowderAheadYd = 3.f;

    // VC12 The mainmast: at 2:00 (yell 8), a 4 s creak, a 6 yd line across the deck just ahead of the front, 60%
    // Physical (no Weakened: ruling 15, over 50%); it lands burning and stays a wall, 10% Fire per second.
    inline constexpr std::uint32_t kMastMs = 120000;
    inline constexpr std::uint32_t kMastWarnMs = 4000;
    inline constexpr float kMastWidth = 6.f;
    inline constexpr float kMastPct = 60.f;
    inline constexpr float kMastGapYd = 1.f;                        // between the front at 2:00 and the mast's aft edge

    // VC13: yell 9 at 2:45, the explosion at 3:00.
    inline constexpr std::uint32_t kOffMyShipMs = 165000;

    // Visual stalkers on each landed stripe and on the mast (the burning look), across the deck.
    inline constexpr std::array<float, 3> kBurningLookY{ -806.f, -820.f, -834.f };

    // ----------------------------------------------------------------------------------------------------------------
    // The schedule (from the fuse, t = 0)
    // ----------------------------------------------------------------------------------------------------------------
    enum class BeatKind : std::uint8_t
    {
        FrontLanded,    // stripe `index` landed: the burning deck now covers stripes 0..index
        FrontMarker,    // stripe `index`'s 2 s marker
        MastWarn,       // yell 8, the 4 s creak and the line
        MastLanded,     // the mast lies across the deck: the wall
        Powder,         // blast `index`'s 2 s sparking marker
        OffMyShip,      // yell 9
        Explosion,      // the ship blows
    };

    struct Beat
    {
        std::uint32_t atMs = 0;
        BeatKind kind = BeatKind::FrontMarker;
        std::uint32_t index = 0;
    };

    inline constexpr std::uint32_t FrontMarkerMs(std::uint32_t k) { return kFrontFirstMs + k * kFrontEveryMs; }
    inline constexpr std::uint32_t FrontLandMs(std::uint32_t k) { return FrontMarkerMs(k) + kFrontWarnMs; }
    inline constexpr std::uint32_t PowderMs(std::uint32_t k) { return kPowderFirstMs + k * kPowderEveryMs; }

    // Markers before the explosion: 18 stripes (5 .. 175 s), 17 blasts (10 .. 170 s).
    inline constexpr std::uint32_t kStripeCount = (kTimerMs - kFrontFirstMs - 1) / kFrontEveryMs + 1;
    inline constexpr std::uint32_t kPowderCount = (kTimerMs - kPowderFirstMs - 1) / kPowderEveryMs + 1;
    static_assert(kStripeCount == 18 && kPowderCount == 17, "DM: about 18 stripes by 3:00, a blast every 10 s");
    static_assert(FrontLandMs(kStripeCount - 1) < kTimerMs, "the last stripe lands before the explosion");

    // Stripes landed by `ms` (0 .. kStripeCount).
    inline std::uint32_t StripesLandedBy(std::uint32_t ms)
    {
        if (ms < FrontLandMs(0))
            return 0;
        return std::min(kStripeCount, (ms - FrontLandMs(0)) / kFrontEveryMs + 1);
    }

    // Every beat with prevMs < atMs <= nowMs, in time order (ties in BeatKind order: a landing before the next
    // marker, the mast before a blast at the same moment, so the blast can avoid it). Splitting a span into any steps
    // gives the same beats once each.
    inline std::vector<Beat> BeatsBetween(std::uint32_t prevMs, std::uint32_t nowMs)
    {
        std::vector<Beat> out;
        if (nowMs <= prevMs)
            return out;
        auto add = [&](std::uint32_t at, BeatKind kind, std::uint32_t index)
        {
            if (at > prevMs && at <= nowMs)
                out.push_back({ at, kind, index });
        };
        for (std::uint32_t k = 0; k < kStripeCount; ++k)
        {
            add(FrontMarkerMs(k), BeatKind::FrontMarker, k);
            add(FrontLandMs(k), BeatKind::FrontLanded, k);
        }
        for (std::uint32_t k = 0; k < kPowderCount; ++k)
            add(PowderMs(k), BeatKind::Powder, k);
        add(kMastMs, BeatKind::MastWarn, 0);
        add(kMastMs + kMastWarnMs, BeatKind::MastLanded, 0);
        add(kOffMyShipMs, BeatKind::OffMyShip, 0);
        add(kTimerMs, BeatKind::Explosion, 0);
        std::stable_sort(out.begin(), out.end(), [](Beat const& a, Beat const& b)
        {
            if (a.atMs != b.atMs)
                return a.atMs < b.atMs;
            return static_cast<std::uint8_t>(a.kind) < static_cast<std::uint8_t>(b.kind);
        });
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Deck geometry
    // ----------------------------------------------------------------------------------------------------------------

    // A strip across the deck between two x stations: a registry LineFacing from `from` along `facing` (east),
    // `length` long and `width` (= xHi - xLo) wide.
    struct Strip
    {
        float xLo = 0.f;    // bow-ward edge
        float xHi = 0.f;    // stern-ward edge
        Vec2 from;          // the west end of the centreline
        float facing = kAcrossFacing;
        float length = kStripeLength;
        float width = 0.f;

        float CenterX() const { return (xLo + xHi) * 0.5f; }
        bool Contains(Vec2 p) const
        {
            return p.x >= xLo && p.x <= xHi && p.y <= kStripeWestY && p.y >= kStripeWestY - kStripeLength;
        }
    };

    inline Strip StripAcross(float xLo, float xHi)
    {
        Strip s;
        s.xLo = std::min(xLo, xHi);
        s.xHi = std::max(xLo, xHi);
        s.width = s.xHi - s.xLo;
        s.from = { s.CenterX(), kStripeWestY };
        return s;
    }

    // The front (its bow-ward edge) once `stripes` stripes have landed.
    inline float FrontX(std::uint32_t stripes)
    {
        return kFrontStartX - static_cast<float>(stripes) * kStripeDepth;
    }

    // Stripe k (0 = at the keg): from FrontX(k) toward the bow by one depth.
    inline Strip StripeRect(std::uint32_t k)
    {
        return StripAcross(FrontX(k + 1), FrontX(k));
    }

    // The whole burning deck once `stripes` stripes have landed: one rectangle from the sterncastle face to the front
    // (handoff section 6: the merged form, cancelled and re-registered at each landing). nullopt before the first.
    inline std::optional<Strip> BurntDeck(std::uint32_t stripes)
    {
        if (!stripes)
            return std::nullopt;
        return StripAcross(FrontX(stripes), kFrontStartX);
    }

    // The aft walkways (kAftWalkwayX): one zone from the sterncastle face aft, burning from the first landing on.
    inline Strip AftWalkways()
    {
        return StripAcross(kFrontStartX, kAftWalkwayX);
    }

    // The mast falls just ahead of the front at 2:00: its aft edge kMastGapYd bow-ward of the front, kMastWidth wide.
    inline Strip MastRect(std::uint32_t stripesAtFall)
    {
        float const hi = FrontX(stripesAtFall) - kMastGapYd;
        return StripAcross(hi - kMastWidth, hi);
    }

    // The part of the burning wall still ahead of the front (the burning deck covers the rest, so no spot ever
    // burns twice). nullopt once the front has passed it (or a sliver under 0.25 yd is left).
    inline std::optional<Strip> WallAhead(Strip const& mast, float frontX)
    {
        float const hi = std::min(mast.xHi, frontX);
        if (hi - mast.xLo < 0.25f)
            return std::nullopt;
        return StripAcross(mast.xLo, hi);
    }

    // Deck height along the slope: z 43 at the sterncastle face to 38 at the bow tip (navmesh); a start for a ground
    // probe, never the final height.
    inline float DeckZ(float x)
    {
        float constexpr sternX = -53.5f;
        float constexpr bowX = -107.5f;
        float const t = std::clamp((x - sternX) / (bowX - sternX), 0.f, 1.f);
        return 43.f + t * (38.f - 43.f);
    }

    // The main deck's walkable cells, 1 yd each, from the map 36 navmesh (deadmines-pilot.NAVMESH-REPORT.md section
    // 2, "Map: deck"): row r is x = -55 - r, column c is y = -798 - c. '#' = deck, '.' = none (beyond the rails, the
    // forward holes, the overhead structure at x -66..-73 on the west side). [navmesh estimate]
    inline constexpr int kDeckMaskTopX = -55;
    inline constexpr int kDeckMaskWestY = -798;
    inline constexpr std::size_t kDeckMaskColumns = 45;
    inline constexpr std::array<char const*, 54> kDeckMask{ {
        "....#####################################....",  // x -55
        ".....####################################....",  // x -56
        ".....####################################....",  // x -57
        ".....#####################################...",  // x -58
        "....#.####################################...",  // x -59
        "....###.##################################...",  // x -60
        "....##.###################################...",  // x -61
        ".......###################################...",  // x -62
        "....######################################...",  // x -63
        "....######################################...",  // x -64
        "....#######.##############################...",  // x -65
        "............##############################...",  // x -66
        "............##############################...",  // x -67
        "............##############################...",  // x -68
        "............##############################...",  // x -69
        "............##############################...",  // x -70
        "............##############################...",  // x -71
        "............##############################...",  // x -72
        "............##############################...",  // x -73
        "......###...##############################...",  // x -74
        "......####################################...",  // x -75
        "......#######.......####..################...",  // x -76
        ".....#.######.......####........##########...",  // x -77
        "....#########...###########.....##########...",  // x -78
        "....#########...############...###########...",  // x -79
        "....##########..############..###########....",  // x -80
        "....#########...############..###########....",  // x -81
        ".....#########..############..###########....",  // x -82
        "......########..############..##########.....",  // x -83
        ".....########...#########.....##########.....",  // x -84
        "......######....#########......#########.....",  // x -85
        "......######....#########.......#######......",  // x -86
        "......######....#########......########......",  // x -87
        "....##.#####....#########......#######.......",  // x -88
        "....##.#####....#########......#######.......",  // x -89
        "....########....#########......#######.......",  // x -90
        "....###.####...................######........",  // x -91
        "....###.#####.............##...######........",  // x -92
        "....##..######............##########.........",  // x -93
        "........######..#.........##########.........",  // x -94
        "........#########..........########..........",  // x -95
        "........#########..........########..........",  // x -96
        "........#########..........#######...........",  // x -97
        ".........########.........########...........",  // x -98
        ".........#########################...........",  // x -99
        "...........######################............",  // x -100
        "..........######################.............",  // x -101
        "...........#####################.............",  // x -102
        "............####################.............",  // x -103
        "............###################..............",  // x -104
        ".............#################...............",  // x -105
        ".............#################...............",  // x -106
        "..............###############................",  // x -107
        "................###########..................",  // x -108
    } };

    // The cell centre of row r, column c.
    inline Vec2 DeckCell(std::size_t row, std::size_t col)
    {
        return { static_cast<float>(kDeckMaskTopX - static_cast<int>(row)),
                 static_cast<float>(kDeckMaskWestY - static_cast<int>(col)) };
    }

    // Is `p` on the main deck between the sterncastle face and the bow (nearest cell)?
    inline bool OnDeck(Vec2 p)
    {
        long const row = std::lround(static_cast<float>(kDeckMaskTopX) - p.x);
        long const col = std::lround(static_cast<float>(kDeckMaskWestY) - p.y);
        if (row < 0 || row >= static_cast<long>(kDeckMask.size()) || col < 0
            || col >= static_cast<long>(kDeckMaskColumns))
            return false;
        return kDeckMask[static_cast<std::size_t>(row)][static_cast<std::size_t>(col)] == '#';
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC11 Powder below: the placement rule
    // ----------------------------------------------------------------------------------------------------------------

    // Every deck cell a blast may use now: on the deck, at least kPowderAheadYd bow-ward of the front after the next
    // stripe (`stripesLanded` + 1), at least kPowderMinPlayerYd from every player, outside the mast's strip
    // (`blocked`, once it is falling or down).
    inline std::vector<Vec2> PowderCandidates(std::uint32_t stripesLanded, std::vector<Vec2> const& players,
        std::optional<Strip> const& blocked = std::nullopt)
    {
        std::vector<Vec2> out;
        float const maxX = FrontX(stripesLanded + 1) - kPowderAheadYd;
        float const minPlayer2 = kPowderMinPlayerYd * kPowderMinPlayerYd;
        for (std::size_t row = 0; row < kDeckMask.size(); ++row)
        {
            for (std::size_t col = 0; col < kDeckMaskColumns; ++col)
            {
                if (kDeckMask[row][col] != '#')
                    continue;
                Vec2 const c = DeckCell(row, col);
                if (c.x > maxX)
                    continue;
                if (blocked && blocked->Contains(c))
                    continue;
                bool nearPlayer = false;
                for (Vec2 const& p : players)
                {
                    float const dx = c.x - p.x;
                    float const dy = c.y - p.y;
                    if (dx * dx + dy * dy < minPlayer2)
                    {
                        nearPlayer = true;
                        break;
                    }
                }
                if (!nearPlayer)
                    out.push_back(c);
            }
        }
        return out;
    }

    // One blast spot, uniform over PowderCandidates; nullopt (skipped) when there is none. `rng(n)` returns [0, n).
    inline std::optional<Vec2> PickPowderSpot(std::uint32_t stripesLanded, std::vector<Vec2> const& players,
        std::optional<Strip> const& blocked, std::function<std::uint32_t(std::uint32_t)> const& rng)
    {
        std::vector<Vec2> const candidates = PowderCandidates(stripesLanded, players, blocked);
        if (candidates.empty())
            return std::nullopt;
        std::uint32_t const n = static_cast<std::uint32_t>(candidates.size());
        std::uint32_t pick = rng(n);
        if (pick >= n)
            pick = n - 1;
        return candidates[pick];
    }

    // ----------------------------------------------------------------------------------------------------------------
    // VC13 The ship: who the explosion kills
    // ----------------------------------------------------------------------------------------------------------------

    // On board: the hull from the stern gallery (x -17) to the bowsprit's end (x -128), rail to rail with the
    // gangplank, at deck height or above (main deck z 37.8-43, the sterncastle top 50-53). The dock and the water
    // below are not.
    inline constexpr float kShipMinX = -128.f;
    inline constexpr float kShipMaxX = -17.f;
    inline constexpr float kShipMinY = -846.f;
    inline constexpr float kShipMaxY = -795.f;
    inline constexpr float kShipMinZ = 33.f;

    inline bool OnShip(float x, float y, float z)
    {
        return x >= kShipMinX && x <= kShipMaxX && y >= kShipMinY && y <= kShipMaxY && z >= kShipMinZ;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The powder keg (gameobject 301000): when a use is accepted (handoff section 3.7)
    // ----------------------------------------------------------------------------------------------------------------
    enum class KegRefusal : std::uint8_t
    {
        None,               // usable
        NotHeroic,
        AlreadyLit,
        NoVanCleef,         // not found, or dead
        VanCleefHidden,     // Greenskin still alive (ruling 26), or in the rigging
        VanCleefInCombat,   // in combat or evading home
        EncounterClosed,    // VanCleef's boss state is not NOT_STARTED / FAIL (DONE, IN_PROGRESS)
    };

    struct KegInputs
    {
        bool heroic = false;
        bool hardModeLit = false;       // DATA_HARD_MODE
        bool vanCleefFound = false;
        bool vanCleefAlive = false;
        bool vanCleefVisible = false;   // visible and selectable
        bool vanCleefInCombat = false;  // in combat or evading
        bool encounterOpen = false;     // VanCleef's boss state NOT_STARTED (or FAIL)
    };

    inline KegRefusal KegUse(KegInputs const& in)
    {
        if (!in.heroic)
            return KegRefusal::NotHeroic;
        if (in.hardModeLit)
            return KegRefusal::AlreadyLit;
        if (!in.vanCleefFound || !in.vanCleefAlive)
            return KegRefusal::NoVanCleef;
        if (!in.vanCleefVisible)
            return KegRefusal::VanCleefHidden;
        if (in.vanCleefInCombat)
            return KegRefusal::VanCleefInCombat;
        if (!in.encounterOpen)
            return KegRefusal::EncounterClosed;
        return KegRefusal::None;
    }

    inline char const* KegRefusalName(KegRefusal r)
    {
        switch (r)
        {
            case KegRefusal::None:
                return "usable";
            case KegRefusal::NotHeroic:
                return "not-heroic";
            case KegRefusal::AlreadyLit:
                return "already-lit";
            case KegRefusal::NoVanCleef:
                return "no-vancleef";
            case KegRefusal::VanCleefHidden:
                return "vancleef-hidden";
            case KegRefusal::VanCleefInCombat:
                return "vancleef-in-combat";
            case KegRefusal::EncounterClosed:
                return "encounter-closed";
        }
        return "unknown";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The run's state, held by boss_edwin_vancleef_rework (one per VanCleef; plain values only)
    // ----------------------------------------------------------------------------------------------------------------
    struct State
    {
        bool lit = false;
        std::uint32_t elapsedMs = 0;            // since the fuse
        std::uint32_t stripesLanded = 0;
        std::uint32_t burntDeckHandle = 0;      // BossMechanics::MechanicHandle id of the merged burning deck (0: none)
        std::uint32_t wallHandle = 0;           // the mast's burning wall (0: none)
        std::uint32_t walkwayHandle = 0;        // the aft walkways' burn, from stripe 0's landing (0: none)
        std::uint32_t retiredDeckHandle = 0;    // the replaced burning deck, cancelled at retireAtMs (0: none)
        std::uint32_t retiredWallHandle = 0;    // the replaced wall, cancelled at retireAtMs (0: none)
        std::uint32_t retireAtMs = 0;           // elapsedMs when the retired handles go (0: nothing pending)
        bool mastFalling = false;               // from MastWarn: `mast` holds its strip
        bool mastDown = false;                  // from MastLanded
        Strip mast;
        std::uint32_t baseCreateHealth = 0;     // his health before the fuse (heroic 340k), restored on reset
    };
}

// ---------------------------------------------------------------------------------------------------------------------
// Engine half (declarations only: the definitions need engine headers). Defined in vancleef_hard_mode.cpp, except
// StateOf, which boss_edwin_vancleef_rework.cpp defines (it knows the boss AI's type). The boss file calls these from
// the hooks WP-B8 left (OnHardModeLit, OnEncounterReset), its UpdateAI and JustDied.
// ---------------------------------------------------------------------------------------------------------------------
class Creature;
class Player;

namespace HardMode::Script
{
    // The fuse is lit (DoAction ACTION_HARD_MODE_LIT): 500k, yell 7, the clock aura on the players, the 3:00 clock.
    void OnLit(Creature* vanCleef, State& state);
    // Every UpdateAI while lit, before anything else (it runs while he is in the rigging too). True when the run
    // ended inside the call (the explosion evaded him): the caller returns at once.
    bool Update(Creature* vanCleef, State& state, std::uint32_t diff);
    // Reset() (evade, wipe, the explosion, a respawn): his health back, the keg re-armed, DATA_HARD_MODE 0, the
    // visuals gone.
    void OnReset(Creature* vanCleef, State& state);
    // He died with the hard mode lit (the instance marks BOSS_BURN_IT_DOWN DONE itself): the visuals and clocks go.
    void OnDied(Creature* vanCleef, State& state);
    // `who` lights the fuse (the keg, or `.dmtest hardmode light`): DATA_HARD_MODE 1, VanCleef engages `who`, then
    // ACTION_HARD_MODE_LIT. False (nothing changed) when he does not run boss_edwin_vancleef_rework.
    bool Light(Creature* vanCleef, Player* who);
    // The run of `vanCleef`, or nullptr when he does not run boss_edwin_vancleef_rework.
    State* StateOf(Creature* vanCleef);
}

#endif
