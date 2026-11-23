/*
 * mod-dungeon-bosses, Scarlet Monastery D5:
 * Houndmaster Loksey (3974), Loksey's Tracking Hound (300908) and the Kennel Pup (300909), the pure, host-testable
 * part (no engine headers). Build spec LIB "Houndmaster Loksey" (docs/dungeons/scarlet-monastery-2-library.md, LK1-LK6;
 * HUB ruling 20), handoff sections 3.4 (F5), 3.5 (row D5), 3.6, 3.8 (NM: the alcove, the neck, the kennel hall and its
 * two entries), 3.9 (G1's `mark-trail` row). Tested by tests/sm_loksey_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsLoksey (212540-212569), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/loksey.py
 *   Tuning     NH<> constants straight from the build spec (normal / heroic); the unset cells (the dogs' melee, the
 *              Fetch speed, the Heel run) are this WP's defaults (report, designer questions)
 *   Rounds     LK1 the Whistle (Called Rounds): Release, Mark, Heel (heroic: then Fetch), one round every 15 s / 12 s
 *   Release    LK2: the pull is the first round (his hounds); every later one brings pups, capped on normal
 *   Mark       LK3: a Scent on 1 / 2 players, then a trail of 5 yd markers, one per living dog, every 0.5 s
 *   Heel       LK4: every dog runs to him; the dog with the most health is whipped into a frenzy
 *   Fetch      LK6 (heroic): the stick lands 15-25 yd out; a catcher cows the dogs, a miss frenzies them all
 *   Geometry   the pack at his feet, the two hall entries, the bots' floor (alcove, neck, hall)
 */

#ifndef MOD_DUNGEON_BOSSES_SM_LOKSEY_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_LOKSEY_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>

namespace SmLoksey
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ScarletMonasteryRework::Point3;
    using ScarletMonasteryRework::Point4;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsLoksey;

    enum LokseySpells : std::uint32_t
    {
        SPELL_LK_RELEASE_CAST       = kSpellSlice.first + 0,    // 212540 LK2 heroic: the 2.5 s interruptible whistle
        SPELL_LK_WHISTLE            = kSpellSlice.first + 1,    // 212541 LK1 look: the whistle (visual 8839, PetCall)
        SPELL_LK_SCENT              = kSpellSlice.first + 2,    // 212542 LK3 the 5 s debuff on the carrier
        SPELL_LK_SCENT_FLASH        = kSpellSlice.first + 3,    // 212543 LK3 look: the scent pouch's flash
        SPELL_LK_HOUND_LEAP         = kSpellSlice.first + 4,    // 212544 LK3 a marker's landing hit (resolve copy)
        SPELL_LK_WHIPPED_FRENZY     = kSpellSlice.first + 5,    // 212545 LK4 / LK6 +50% attack speed and damage a stack
        SPELL_LK_LOKSEY_FRENZY      = kSpellSlice.first + 6,    // 212546 LK4 his own frenzy when no dog lives
        SPELL_LK_CORRECTION_CAST    = kSpellSlice.first + 7,    // 212547 LK5 the 2 s cast bar
        SPELL_LK_CORRECTION_HIT     = kSpellSlice.first + 8,    // 212548 LK5 the cone's hit (resolve copy)
        SPELL_LK_CORRECTION_TANK    = kSpellSlice.first + 9,    // 212549 LK5 the tank's own hit (% of tank health)
        SPELL_LK_FETCH_THROW        = kSpellSlice.first + 10,   // 212550 LK6 the thrown stick (a missile, look only)
        SPELL_LK_COWED              = kSpellSlice.first + 11,   // 212551 LK6 a caught Fetch: the dogs sit, 6 s
        // 212552-212569 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_LK_COWED;
    static_assert(kLastSpell <= kSpellSlice.last, "Loksey's spells must stay in his slice");

    // Registry tags (the script's own mechanic ids: LK3 = 3, LK5 = 5, LK6 = 6; the Scent's Bait is its own tag so the
    // ledger can tell the carrier's walk from the landings).
    enum LokseyTags : std::uint32_t
    {
        TAG_LK_MARK_LANDING = 3,    // LK3 a marker
        TAG_LK_CORRECTION   = 5,    // LK5 the cone
        TAG_LK_FETCH        = 6,    // LK6 the catch circle
        TAG_LK_SCENT        = 33,   // LK3 the carrier's walk away from the group (a Bait)
    };

    // creature_text groups of 3974 (LIB "Text"; S0 range 0-4, group 0 stock).
    enum LokseyTexts : std::uint8_t
    {
        SAY_LOKSEY_RELEASE      = 0,    // stock yell "Release the hounds!": the pull and every Release (LK2)
        EMOTE_LOKSEY_MARK       = 1,    // "%s whistles: Mark!" (LK3)
        EMOTE_LOKSEY_HEEL       = 2,    // "%s whistles: Heel!" (LK4)
        EMOTE_LOKSEY_FRENZY     = 3,    // "%s works himself into a frenzy!" (LK4, no dog alive)
        EMOTE_LOKSEY_FETCH      = 4,    // "%s whistles: Fetch!" (LK6, heroic)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // LK1 the Whistle: the rounds
    // ----------------------------------------------------------------------------------------------------------------
    enum class Round : std::uint8_t
    {
        Release = 0,
        Mark = 1,
        Heel = 2,
        Fetch = 3,      // heroic only
    };

    inline constexpr std::uint8_t kRoundsNormal = 3;
    inline constexpr std::uint8_t kRoundsHeroic = 4;

    inline constexpr std::uint8_t RoundCount(bool heroic)
    {
        return heroic ? kRoundsHeroic : kRoundsNormal;
    }

    // The round after `last`: Release, Mark, Heel, (Fetch,) Release again.
    inline constexpr Round NextRound(Round last, bool heroic)
    {
        std::uint8_t const next = static_cast<std::uint8_t>((static_cast<std::uint8_t>(last) + 1) % RoundCount(heroic));
        return static_cast<Round>(next);
    }

    inline constexpr char const* RoundName(Round r)
    {
        switch (r)
        {
            case Round::Release: return "release";
            case Round::Mark:    return "mark";
            case Round::Heel:    return "heel";
            case Round::Fetch:   return "fetch";
        }
        return "?";
    }

    inline constexpr NH<std::uint32_t> kRoundEveryMs{ 15000, 12000 };           // LK1: the cadence of one round
    // Each command comes round every 45 s / 48 s (LIB "First, cooldown").
    inline constexpr std::uint32_t CycleMs(bool heroic)
    {
        return RoundCount(heroic) * kRoundEveryMs(heroic);
    }
    static_assert(CycleMs(false) == 45000 && CycleMs(true) == 48000, "the spec's 45 s / 48 s per command");

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (LIB "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<float> kMarkLandingPct{ 35.f, 45.f };       // LK3 a marker's landing, the tank's row too
    inline constexpr NH<float> kCorrectionPct{ 30.f, 40.f };        // LK5 everyone but the tank
    inline constexpr NH<float> kCorrectionTankPct{ 20.f, 30.f };    // LK5 the tank, % of tank health
    inline constexpr std::int32_t kFetchCowedTakenPct = 25;         // LK6: the cowed dogs take 25% more damage
    inline constexpr std::int32_t kWhippedFrenzyPct = 50;           // LK4 / LK6: +50% attack speed and damage a stack
    inline constexpr std::int32_t kLokseyFrenzyHastePct = 30;       // LK4: his own frenzy when no dog lives

    // Health at 5 players (handoff 3.6; heroic by WP-H's overrides). Loksey's own is the S0 boss column.
    inline constexpr NH<std::uint32_t> kBossHealth{ 38000, 210000 };
    inline constexpr NH<std::uint32_t> kHoundHealth{ 3000, 15000 };
    inline constexpr NH<std::uint32_t> kPupHealth{ 800, 4000 };

    // Kill order (the descriptor): the frenzied dog, the pups (cleaved), the hounds, then Loksey (0).
    inline constexpr std::int8_t kFrenziedKillPriority = 3;
    inline constexpr std::int8_t kPupKillPriority = 2;
    inline constexpr std::int8_t kHoundKillPriority = 1;
    inline constexpr std::int8_t kTankDogPriority = -1;             // the tank picks dogs up when nothing else needs it
    inline constexpr std::uint8_t kReleaseKickPriority = 3;         // heroic: the expected interrupt
    inline constexpr std::uint8_t kFrenzyPurgePriority = 1;         // a reward on both difficulties

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms). The pull is t = 0.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kCorrectionFirstMs = 6000;       // LK5
    inline constexpr std::uint32_t kCorrectionEveryMs = 10000;
    inline constexpr std::uint32_t kCorrectionCastMs = 2000;        // the cast bar and the warning
    inline constexpr float kCorrectionAngleDeg = 90.f;
    inline constexpr float kCorrectionLengthYd = 8.f;

    inline constexpr std::uint32_t kReleaseCastMs = 2500;           // LK2 heroic: the whistle's cast bar
    inline constexpr std::uint32_t kRetryMs = 500;                  // a due cast that cannot start yet

    // LK2: pups per Release. Normal: 3, never more than 6 alive (a Release with 6 up brings none); heroic: 3 when the
    // whistle was interrupted, 6 when it ran, no cap.
    inline constexpr std::uint32_t kPupsPerRelease = 3;
    inline constexpr std::uint32_t kPupsPerMissedRelease = 6;
    inline constexpr std::uint32_t kPupCapNormal = 6;

    inline constexpr std::uint32_t PupsToSummon(bool heroic, bool interrupted, std::uint32_t pupsAlive)
    {
        if (heroic)
            return interrupted ? kPupsPerRelease : kPupsPerMissedRelease;
        if (pupsAlive >= kPupCapNormal)
            return 0;
        return std::min(kPupsPerRelease, kPupCapNormal - pupsAlive);
    }

    // LK3: the Scent, then the trail.
    inline constexpr std::uint32_t kScentMs = 5000;                 // the debuff, 5 s
    inline constexpr std::uint32_t kMarkerEveryMs = 500;            // a marker every 0.5 s a trail
    inline constexpr std::uint32_t kMarkerWarnMs = 1500;            // a dog leaps onto a marker 1.5 s after it drops
    inline constexpr std::uint32_t kLeapFlightMs = 500;             // the dog takes off this long before it lands
    inline constexpr float kMarkerRadiusYd = 5.f;
    inline constexpr float kMarkerOffsetMaxYd = 2.f;                // 0-2 yd from the carrier, a random direction
    inline constexpr NH<std::uint32_t> kScentCarriers{ 1, 2 };      // heroic: two players, the dogs split
    // The tank never carries the Scent (HANDOFF §10 STAGE-R-1-LIB Q1, 2026-11-20): a tank carrier would drag Loksey
    // and the dogs off position, and could never keep kScentFarYd from the boss chasing it. A tank-only group gets no
    // Mark.
    inline constexpr bool kScentTankExempt = true;
    // Nor the healer (F-4b, orchestrator default 2026-11-23): the 22 yd walk took the healer through the alcove's 3 yd
    // neck and out of line of sight of the tank, who then died unhealed (STAGE-CLEAR-DIAG §1). A group of tank and
    // healer alone gets no Mark, the same fallback as the tank's exemption.
    inline constexpr bool kScentHealerExempt = true;
    // The carrier walks this far from Loksey during the Scent (the registry Bait's `othersRange`): clear of the group
    // and of the tank's side of the hall, inside the 58 yd wall the trail runs along.
    inline constexpr float kScentFarYd = 22.f;
    static_assert(kLeapFlightMs < kMarkerWarnMs, "a dog takes off after its marker drops");

    // One marker of a trail: dog `dog` leaps onto the marker its carrier `carrier` drops `atMs` after the Scent ends.
    struct TrailSlot
    {
        std::uint32_t dog = 0;
        std::uint32_t carrier = 0;
        std::uint32_t atMs = 0;
    };

    // The dogs split round-robin between the carriers; each trail drops one marker every 0.5 s.
    inline std::vector<TrailSlot> PlanTrail(std::uint32_t dogs, std::uint32_t carriers)
    {
        std::vector<TrailSlot> out;
        if (carriers == 0)
            return out;
        out.reserve(dogs);
        for (std::uint32_t i = 0; i < dogs; ++i)
            out.push_back({ i, i % carriers, (i / carriers) * kMarkerEveryMs });
        return out;
    }

    // From the end of the Scent to the last landing (ms): the trail's length in time.
    inline constexpr std::uint32_t TrailMs(std::uint32_t dogs, std::uint32_t carriers)
    {
        if (dogs == 0 || carriers == 0)
            return 0;
        std::uint32_t const longest = (dogs + carriers - 1) / carriers;     // markers on the longest trail
        return (longest - 1) * kMarkerEveryMs + kMarkerWarnMs;
    }
    // How long the longest trail keeps dropping markers (the spec's "three hounds make a 1.5 s trail, three hounds and
    // six pups 4.5 s": a marker every 0.5 s, one per dog on the trail).
    inline constexpr std::uint32_t TrailDropMs(std::uint32_t dogs, std::uint32_t carriers)
    {
        if (dogs == 0 || carriers == 0)
            return 0;
        return ((dogs + carriers - 1) / carriers) * kMarkerEveryMs;
    }
    // The longest trail of a normal fight (3 hounds + the 6-pup cap) fits its round with the Scent; heroic's too at
    // the 15 dogs a missed Release brings on top of his hounds.
    static_assert(kScentMs + TrailMs(3 + kPupCapNormal, 1) < kRoundEveryMs.normal, "the trail fits its round (N)");
    static_assert(kScentMs + TrailMs(3 + 12, 2) < kRoundEveryMs.heroic, "the trail fits its round (H)");

    // A marker's spot: 0-2 yd from the carrier at a random bearing (u1 and u2 are uniform in [0, 1]).
    inline Vec2 MarkerSpot(Vec2 carrier, float u1, float u2)
    {
        float const d = kMarkerOffsetMaxYd * std::clamp(u1, 0.f, 1.f);
        float const bearing = DungeonKit::kTwoPi * std::clamp(u2, 0.f, 1.f);
        return DungeonKit::Advance(carrier, bearing, d);
    }

    // LK4: the dog with the most health is whipped (a tie: the first of the list, which the script sorts by guid). The
    // index into the list, or -1 when empty.
    inline int WhippedDog(std::vector<std::uint32_t> const& health)
    {
        int best = -1;
        for (std::size_t i = 0; i < health.size(); ++i)
            if (best < 0 || health[i] > health[static_cast<std::size_t>(best)])
                best = static_cast<int>(i);
        return best;
    }

    inline constexpr std::uint32_t kHeelRunMs = 2500;               // LK4: the dogs reach him, then the whip
    inline constexpr std::uint32_t kHeelGiveUpMs = 4000;            // a dog that never arrives goes back to the fight
    inline constexpr float kHeelRadiusYd = 3.f;
    inline constexpr std::uint32_t kFrenzyNormalMs = 30000;         // LK4 normal: 30 s, one dog (45 s cycle)
    inline constexpr std::uint32_t kLokseyFrenzyMs = 15000;         // LK4: his own, 15 s, purgeable
    static_assert(kFrenzyNormalMs < CycleMs(false), "a normal frenzy never outlasts the round cycle");

    inline Vec2 HeelSpot(Vec2 center, std::uint32_t index, std::uint32_t count)
    {
        float const n = static_cast<float>(std::max<std::uint32_t>(count, 1));
        float const bearing = DungeonKit::kTwoPi * static_cast<float>(index) / n;
        return DungeonKit::Advance(center, bearing, kHeelRadiusYd);
    }

    // LK6 Fetch (heroic): the stick lands a 3 yd circle 15 to 25 yd from Loksey, 3 s after the whistle.
    inline constexpr float kFetchMinYd = 15.f;
    inline constexpr float kFetchMaxYd = 25.f;
    inline constexpr float kFetchRadiusYd = 3.f;
    inline constexpr std::uint32_t kFetchFlightMs = 3000;           // the whistle to the landing (the circle's warning)
    inline constexpr std::uint32_t kCowedMs = 6000;                 // a caught Fetch: the dogs sit
    inline constexpr float kFetchMissileSpeed = 10.f;               // yd/s (the throw spell's Speed)
    inline constexpr float kFetchEdgeMarginYd = 3.f;                // the circle sits this far inside the floor
    inline constexpr std::uint32_t kFetchSpotTries = 24;            // random rings tried before the fallback
    static_assert(kFetchMaxYd / kFetchMissileSpeed < static_cast<float>(kFetchFlightMs) / 1000.f,
        "the stick lands inside its warning");

    inline constexpr bool FetchRangeOk(float distanceYd)
    {
        return distanceYd >= kFetchMinYd && distanceYd <= kFetchMaxYd;
    }

    // ms after the whistle that the throw leaves, so the missile lands as the circle resolves.
    inline std::uint32_t FetchLaunchDelayMs(float distanceYd, float speed = kFetchMissileSpeed)
    {
        float const flightMs = distanceYd / std::max(speed, 0.1f) * 1000.f;
        return flightMs >= static_cast<float>(kFetchFlightMs) ? 0u
            : static_cast<std::uint32_t>(static_cast<float>(kFetchFlightMs) - flightMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The dogs
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kHoundCount = 3;                 // his own, at his feet (stock guids 40089-40091)
    inline constexpr float kLeapMinSpeedXY = 4.f;
    inline constexpr float kLeapMinSpeedZ = 6.f;
    inline constexpr float kGroundBandYd = 6.f;                     // a ground probe further off than this is a hole
    inline constexpr float kOpeningThreat = 10.f;                   // a pup's first target

    // The three stock hound spots (guids 40089-40091 [db]; their spawn rows are deleted by rev_loksey).
    inline constexpr std::array<Point4, kHoundCount> kPackSpots{ {
        { 123.754f, -261.435f, 18.6299f, 2.96706f },
        { 120.958f, -257.75f, 18.6299f, 4.43314f },
        { 123.09f, -258.452f, 18.6299f, 3.80482f },
    } };

    // LK2: the kennel hall's two entries (NAVMESH: 80 and 82 yd from him by the mesh, 37 yd from the hall center; the
    // spec's "east archway" is these two). Pup i comes in at entry i % 2.
    inline constexpr std::array<Point3, 2> kHallEntries{ {
        { 200.8f, -243.2f, 19.5f },     // NE
        { 180.8f, -306.2f, 18.8f },     // SE
    } };

    inline constexpr Point3 PupEntry(std::uint32_t index)
    {
        return kHallEntries[index % kHallEntries.size()];
    }

    // Where the floor is (NM, [navmesh estimate]): the alcove x 119-145, the 3 yd neck x 146-152, the hall x 155-208 by
    // y -310 to -240. The pup entries are on its rim; the trail runs along its 58 yd wall.
    inline constexpr Point3 kHallCenter{ 175.f, -270.f, 19.f };
    inline constexpr float kFloorZMin = 15.f;
    inline constexpr float kFloorZMax = 24.f;

    inline constexpr std::array<Vec2, 4> kAlcovePolygon{ {
        { 119.f, -265.f }, { 145.f, -265.f }, { 145.f, -249.f }, { 119.f, -249.f },
    } };
    inline constexpr std::array<Vec2, 4> kNeckPolygon{ {
        { 144.f, -263.f }, { 156.f, -263.f }, { 156.f, -258.f }, { 144.f, -258.f },
    } };
    inline constexpr std::array<Vec2, 4> kHallPolygon{ {
        { 155.f, -310.f }, { 208.f, -310.f }, { 208.f, -240.f }, { 155.f, -240.f },
    } };

    // The bots' floor (BotFloorBounds in the script): where a planned spot may be while a mechanic of this fight is in
    // view (the markers, the carrier's walk, the Fetch circle). The arena (ScarletMonasteryRework.h LokseyArena) is
    // the leash frame, a little wider.
    inline DungeonKit::Arena BotFloor()
    {
        DungeonKit::Arena floor;
        for (std::array<Vec2, 4> const* polygon : { &kAlcovePolygon, &kNeckPolygon, &kHallPolygon })
            floor.Add(DungeonKit::ArenaRegion::Polygon(std::vector<Vec2>(polygon->begin(), polygon->end()),
                kFloorZMin, kFloorZMax));
        return floor;
    }

    // A Fetch spot is usable when its center and the four points 3 yd round it are on the bots' floor.
    inline bool FetchSpotOnFloor(DungeonKit::Arena const& floor, Vec2 spot, float z)
    {
        if (!floor.Contains(spot, z))
            return false;
        for (int i = 0; i < 4; ++i)
        {
            Vec2 const rim = DungeonKit::Advance(spot, DungeonKit::kPi * 0.5f * static_cast<float>(i),
                kFetchEdgeMarginYd);
            if (!floor.Contains(rim, z))
                return false;
        }
        return true;
    }
}

#endif
