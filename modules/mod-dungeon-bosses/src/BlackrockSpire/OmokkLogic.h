/*
 * mod-dungeon-bosses, Blackrock Spire B1: Highlord Omokk (9196), the pure, host-testable part (no engine headers).
 * Build spec SP "Highlord Omokk" (docs/dungeons/blackrock-spire-rework.md, rulings 15-23; Build spec OM1-OM11),
 * handoff sections 3.4 rows OM, 3.5 row B1, 3.6, 3.8 (NM 1) and 3.10 gap 6. Tested by tests/brs_omokk_test.cpp; the
 * data side is apps/dbc-tools source/npcs/blackrock_spire/omokk.py (lib/test_blackrock_spire_omokk.py pins both).
 *
 *   Spells         the WP's ids, inside kSpellsOmokk (210020-210059)
 *   Texts          creature_text groups 0-7 of 9196 (SQL rev rev_highlord_omokk_blackrock_spire.sql)
 *   Tuning         NH<> constants and FlexAB pairs, straight from the build spec
 *   The Ring       OM1 the band strips (hall and, heroic, the bridge doors), the pile, the shove's direction
 *   Haymaker       OM2 the line's far end and its knockback
 *   Pelting        OM3 the volley's start, held off every Haymaker line (FirstClearStart)
 *   CrowdBook      OM4 / OM5 Crowd's Roar, the judge, Booed
 *   The bridge     OM7 the landings, OM9 the lanes and their sideways throw (BridgeExtentAt), OM10 the haul-up
 *   Knockbacks     Unit::KnockbackFrom's speeds for a throw of a given length
 *
 * Every point is [navmesh estimate] (blackrock-spire-build.NAVMESH-REPORT.md section 1) unless marked [db] or
 * [designer]; the playtest's `.gps` walk confirms them (section 7 #28). Axes: +x north, +y west; the hall runs along y
 * (Omokk at its west end, y -300.7; it opens east into the big room at y -340..-358), the bridge along y too
 * (west door y -397.75, east door y -441.87 [designer]).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_OMOKK_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_OMOKK_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <span>

namespace BrsOmokk
{
    using BlackrockSpireRework::FlexAB;
    using BlackrockSpireRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsOmokk;

    enum OmokkSpells : std::uint32_t
    {
        SPELL_OM_CROWD_SHOVE        = kSpellSlice.first + 0,    // 210020 OM1 the band's hit (resolve copy, Physical)
        SPELL_OM_PILE_SHOVE         = kSpellSlice.first + 1,    // 210021 OM1 a climber's hit (kit refflat damage)
        SPELL_OM_HAYMAKER_CAST      = kSpellSlice.first + 2,    // 210022 OM2 the 2.5 s wind-up (cast bar)
        SPELL_OM_HAYMAKER_TWO_CAST  = kSpellSlice.first + 3,    // 210023 OM2 heroic: the 1.5 s second punch (bar)
        SPELL_OM_HAYMAKER           = kSpellSlice.first + 4,    // 210024 OM2 the punch (resolve copy, Physical)
        SPELL_OM_PELTING            = kSpellSlice.first + 5,    // 210025 OM3 the bottle's landing (resolve copy)
        SPELL_OM_BOTTLE_FIRST       = kSpellSlice.first + 6,    // 210026 OM3 the six bottles in flight (looks)
        SPELL_OM_BOTTLE_LAST        = kSpellSlice.first + 11,   // 210031
        SPELL_OM_CROWDS_ROAR        = kSpellSlice.first + 12,   // 210032 OM4 +10% damage, +10% attack speed a stack
        SPELL_OM_BOOED              = kSpellSlice.first + 13,   // 210033 OM5 +10% damage taken a stack
        SPELL_OM_CROWD_ROCK         = kSpellSlice.first + 14,   // 210034 OM5 the rock from the crowd (look)
        SPELL_OM_OGRE_MOJO          = kSpellSlice.first + 15,   // 210035 OM6 the Mojo Mystic's 3 s kickable chant
        SPELL_OM_MOJO_FRENZY        = kSpellSlice.first + 16,   // 210036 OM6 +50% damage, +60% attack speed, 15 s
        SPELL_OM_MOJO_FRENZY_LOOK   = kSpellSlice.first + 17,   // 210037 OM6 its look, re-cast every 3 s
        SPELL_OM_BELLY_SLAM_CAST    = kSpellSlice.first + 18,   // 210038 OM8 the 2 s cast bar
        SPELL_OM_BELLY_SLAM         = kSpellSlice.first + 19,   // 210039 OM8 the slam (resolve copy, Physical)
        SPELL_OM_BULL_RUSH_CAST     = kSpellSlice.first + 20,   // 210040 OM9 the Brawler pawing the ground (bar)
        SPELL_OM_BULL_RUSH          = kSpellSlice.first + 21,   // 210041 OM9 the charge (resolve copy, Physical)
        SPELL_OM_PIT_DROP           = kSpellSlice.first + 22,   // 210042 OM10 the catch: 70% (35% slowed)
        SPELL_OM_BELLY_SLAM_LOOK    = kSpellSlice.first + 23,   // 210043 OM8 the slam's look on him (hit or miss)
        SPELL_OM_HAYMAKER_LOOK      = kSpellSlice.first + 24,   // 210044 OM2 the punch's look on him (hit or miss)
        SPELL_OM_SHOVED             = kSpellSlice.first + 25,   // 210045 OM1 the shove's 1.5 s lockout (the band skips)
        // 210046-210059 spare
    };
    static_assert(SPELL_OM_SHOVED <= kSpellSlice.last, "Omokk's spells must stay in his slice");
    inline constexpr std::uint32_t kBottleCount = SPELL_OM_BOTTLE_LAST - SPELL_OM_BOTTLE_FIRST + 1;
    static_assert(kBottleCount == 6, "the six bottle looks (V-1 OM_PELTING)");

    // creature_text groups of 9196 (SP "Text"; none stock).
    enum OmokkTexts : std::uint8_t
    {
        SAY_OM_PULL             = 0,    // yell: the pull, the fans run in
        EMOTE_OM_HAYMAKER       = 1,    // boss emote: "%s winds up a haymaker at $n!"
        EMOTE_OM_CROWD_ROARS    = 2,    // boss emote: the judge, the crowd was fed
        EMOTE_OM_CROWD_JEERS    = 3,    // boss emote: the judge, booed
        SAY_OM_STILL_STRONGEST  = 4,    // yell: the third Booed stack
        SAY_OM_TO_THE_BRIDGE    = 5,    // yell: heroic, 25%
        EMOTE_OM_MOJO           = 6,    // boss emote: a Mojo Mystic starts chanting (heroic)
        SAY_OM_DEATH            = 7,    // yell: death
    };
    static_assert(SAY_OM_DEATH == 7, "texts 0-7 (BlackrockSpireRework.h kTextRanges)");

    // Registry tags (bookkeeping and `.mech list`; the heroic second punch is the drill's tag 2 too).
    enum OmokkTags : std::uint32_t
    {
        TAG_OM_HAYMAKER     = 1,
        TAG_OM_HAYMAKER_TWO = 2,
        TAG_OM_PELTING      = 3,
        TAG_OM_BAND         = 4,
        TAG_OM_BELLY_SLAM   = 5,
        TAG_OM_BULL_RUSH    = 6,
    };

    inline constexpr float kHallFloorZ = 31.8f;                 // [db] his spawn

    // ----------------------------------------------------------------------------------------------------------------
    // OM1 The Ring: the band (2 yd strips at the stands), the pile, the shove
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kCrowdShovePct{ 25.f, 35.f };
    inline constexpr float kCrowdShoveKnockYd = 8.f;
    inline constexpr float kCrowdShoveSpeedZ = 6.f;
    inline constexpr std::uint32_t kBandWarnMs = 3000;          // the fans run in, then the band is live
    inline constexpr std::uint32_t kBandTickMs = 500;           // a shove carries the player out before the next tick
    inline constexpr std::uint32_t kBandLifeMs = 20 * 60 * 1000;    // the fight; cancelled at the showdown and reset
    inline constexpr float kBandWidth = 2.f;
    inline constexpr std::uint32_t kPileCheckMs = 500;
    inline constexpr std::uint32_t kShoveLockoutMs = 1500;      // a shoved player is not shoved again this soon
    // The band's registry line hits before the script's throw is seen (the server learns the new position from the
    // next movement packet), so a shoved unit wears SPELL_OM_SHOVED for kShoveLockoutMs and the band skips it
    // (Eligibility maxStacks 0): no second 25% / 35%, Weakened and Roar stack from one shove (R-1-A m1).
    static_assert(kShoveLockoutMs > kBandTickMs, "the lockout must cover the band's next tick");

    struct Strip
    {
        Vec2 from;
        Vec2 to;
        char const* name;
    };

    // The hall's band (NM 1): the rock pile's foot along the hall's south edge (x -26.8; the strip x -27..-25), the two
    // north alcove mouths (x -14.8; the strip x -15.6..-13.6) and the east doorway into the big room (y -357; the
    // strip y -358..-356). The west end is his back wall (no doorway on the mesh): designer question 1 in the report.
    inline constexpr std::array<Strip, 4> kHallBand{ {
        { { -26.0f, -296.0f }, { -26.0f, -352.0f }, "pile" },
        { { -14.6f, -310.8f }, { -14.6f, -331.2f }, "alcove-west" },
        { { -14.6f, -345.2f }, { -14.6f, -355.0f }, "alcove-east" },
        { { -26.8f, -357.0f }, { -14.8f, -357.0f }, "doorway" },
    } };

    // Heroic, on the bridge: a strip just outside each door, in front of the door crowds. The haul-up spots
    // (kOmokkHaulUpWest / East) stay 1.8 and 1.5 yd clear of them.
    inline constexpr std::array<Strip, 2> kBridgeBand{ {
        { { -41.0f, -397.0f }, { -33.0f, -397.0f }, "west-door" },
        { { -41.0f, -443.3f }, { -32.5f, -443.3f }, "east-door" },
    } };

    // The ring's middle line: the hall's centre (x -26.8..-14.8) between the band ends. A shove throws toward the
    // nearest point on it.
    inline constexpr float kRingMidX = -20.8f;
    inline constexpr float kRingMidYMax = -300.0f;
    inline constexpr float kRingMidYMin = -352.0f;

    // Climbing the pile (x -45..-26, z 36..42; NM 1): south of the band's strip and up off the floor.
    inline constexpr float kPileMinX = -45.5f;
    inline constexpr float kPileMaxX = -27.0f;
    inline constexpr float kPileMinY = -356.0f;
    inline constexpr float kPileMaxY = -294.0f;
    inline constexpr float kPileClimbZ = kHallFloorZ + 1.5f;

    constexpr bool OnThePile(Vec2 p, float z)
    {
        return p.x >= kPileMinX && p.x <= kPileMaxX && p.y >= kPileMinY && p.y <= kPileMaxY && z >= kPileClimbZ;
    }

    // Where a hall shove throws toward: the nearest point of the ring's middle line.
    constexpr Vec2 HallShoveToward(Vec2 p)
    {
        return { kRingMidX, std::clamp(p.y, kRingMidYMin, kRingMidYMax) };
    }

    // The bridge: a door strip throws back toward the middle of the bridge.
    inline constexpr Vec2 kBridgeMiddle{ -37.2f, -418.2f };

    // ----------------------------------------------------------------------------------------------------------------
    // Knockbacks (MotionMaster::MoveKnockbackFrom: distance = 2 x speedXY x speedZ / gravity)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kGravity = 19.29110527038574f;      // Movement::gravity

    constexpr float KnockbackSpeedXY(float distance, float speedZ)
    {
        return speedZ > 0.f ? distance * kGravity / (2.f * speedZ) : 0.f;
    }

    constexpr float KnockbackDistance(float speedXY, float speedZ)
    {
        return 2.f * speedXY * speedZ / kGravity;
    }

    // The source point Unit::KnockbackFrom pushes away from, so `at` flies toward `toward` (1 yd behind it; 1 yd south
    // of it when the two coincide).
    inline Vec2 KnockSourceToward(Vec2 at, Vec2 toward)
    {
        float const dx = toward.x - at.x;
        float const dy = toward.y - at.y;
        float const d = std::sqrt(dx * dx + dy * dy);
        if (d < 0.01f)
            return { at.x - 1.f, at.y };
        return { at.x - dx / d, at.y - dy / d };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM2 Haymaker
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kHaymakerPct{ 40.f, 50.f };
    inline constexpr float kHaymakerWidth = 5.f;
    inline constexpr float kHaymakerLength = 30.f;
    inline constexpr std::uint32_t kHaymakerCastMs = 2500;
    inline constexpr std::uint32_t kHaymakerTwoMs = 1500;      // heroic: the second line after the first resolves
    inline constexpr std::uint32_t kHaymakerFirstMs = 10000;
    inline constexpr std::uint32_t kHaymakerEveryMs = 15000;
    inline constexpr FlexAB kHaymakerTargets{ 1, 2 };
    inline constexpr float kHaymakerKnockYd = 15.f;
    inline constexpr float kHaymakerSpeedZ = 7.f;

    // The far end of a Haymaker line: kHaymakerLength from `from` toward `target` (along `facing`, radians, when the
    // two coincide).
    inline Vec2 HaymakerEnd(Vec2 from, Vec2 target, float facing)
    {
        float const dx = target.x - from.x;
        float const dy = target.y - from.y;
        float const d = std::sqrt(dx * dx + dy * dy);
        if (d < 0.01f)
            return DungeonKit::Advance(from, facing, kHaymakerLength);
        return { from.x + dx / d * kHaymakerLength, from.y + dy / d * kHaymakerLength };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM3 Pelting
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kPeltingPct{ 25.f, 30.f };
    inline constexpr float kPeltingRadius = 4.f;
    inline constexpr std::uint32_t kPeltingFlightMs = 2000;
    inline constexpr std::uint32_t kPeltingFirstMs = 6000;
    inline constexpr NH<std::uint32_t> kPeltingEveryMs{ 12000, 10000 };
    inline constexpr FlexAB kPeltingTargetsNormal{ 2, 4 };
    inline constexpr FlexAB kPeltingTargetsHeroic{ 3, 6 };
    inline constexpr std::uint32_t kPeltingAfterPunchMs = 1000;     // a volley lands no sooner after the last punch
    inline constexpr float kBottleSpeed = 10.f;                     // the bottle looks' Speed (yd/s; stock 39146)

    constexpr std::uint8_t PeltingTargets(std::uint32_t players, bool heroic)
    {
        return heroic ? kPeltingTargetsHeroic.At(players) : kPeltingTargetsNormal.At(players);
    }

    // When a bottle leaves a fan `distance` yd from its circle so it lands with the circle: this many ms after the
    // volley starts (0 when the flight is longer than the warning).
    constexpr std::uint32_t BottleLaunchDelayMs(float distance)
    {
        float const flightMs = distance / kBottleSpeed * 1000.f;
        return flightMs >= static_cast<float>(kPeltingFlightMs) ? 0u
            : static_cast<std::uint32_t>(static_cast<float>(kPeltingFlightMs) - flightMs);
    }

    // A span of time (absolute ms on the AI's clock, both ends included) in which something must not land.
    struct Window
    {
        std::uint64_t from = 0;
        std::uint64_t to = 0;
    };

    // The earliest start s >= `due` whose landing (s + `leadMs`) falls in none of `windows`. Pelting: a Haymaker's
    // window is [its registration, its last punch + kPeltingAfterPunchMs]. Bull Rush: the Belly Slam's is
    // [its cast start - kBullRushWarnMs, its slam], so no lane is down during the cast.
    inline std::uint64_t FirstClearStart(std::uint64_t due, std::uint32_t leadMs, std::span<Window const> windows)
    {
        std::uint64_t s = due;
        for (std::size_t pass = 0; pass < 2 * windows.size() + 2; ++pass)
        {
            bool moved = false;
            for (Window const& w : windows)
            {
                std::uint64_t const landing = s + leadMs;
                if (landing >= w.from && landing <= w.to)
                {
                    s = std::max(due, w.to + 1 >= leadMs ? w.to + 1 - leadMs : std::uint64_t(0));
                    moved = true;
                }
            }
            if (!moved)
                break;
        }
        return s;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM4 Crowd's Roar, OM5 the judge and Booed
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint8_t kRoarMaxStacks = 5;
    inline constexpr std::int32_t kRoarDamagePct = 10;
    inline constexpr std::int32_t kRoarHastePct = 10;
    inline constexpr std::uint8_t kBooedMaxStacks = 3;
    inline constexpr std::int32_t kBooedTakenPct = 10;
    inline constexpr std::uint32_t kJudgeEveryMs = 30000;

    enum class Verdict : std::uint8_t
    {
        Cheered,        // fed in the window: emote line 2
        Booed,          // not fed: one Roar off, one Booed on, the rock, emote line 3
    };

    struct JudgeResult
    {
        Verdict verdict = Verdict::Cheered;
        std::uint8_t roar = 0;          // the stacks after the judge
        std::uint8_t booed = 0;
        bool booedAdded = false;        // a Booed stack went on now (not at the cap already)
        bool yell = false;              // Booed reached its cap now: yell line 4 (once a pull)
    };

    // The crowd's ledger for one pull: the Roar stacks it gave (OM4: Feed; OM6: Grant), the feeds in the open judge
    // window and the Booed stacks.
    class CrowdBook
    {
    public:
        // A player fed the crowd (a Haymaker hit, a Crowd Shove, a Pit Drop catch): one Roar stack (capped), and the
        // window counts as fed. Returns the stacks now.
        std::uint8_t Feed()
        {
            ++_feeds;
            _roar = std::min<std::uint8_t>(kRoarMaxStacks, static_cast<std::uint8_t>(_roar + 1));
            return _roar;
        }

        // Roar stacks that are not a feed (the Mojo Frenzy's two): capped, the window untouched.
        std::uint8_t Grant(std::uint8_t stacks)
        {
            _roar = static_cast<std::uint8_t>(std::min<std::uint32_t>(kRoarMaxStacks, std::uint32_t(_roar) + stacks));
            return _roar;
        }

        // The 30 s judge: fed, the crowd cheers; not fed, one Roar stack comes off and Booed goes up one (to the cap).
        // The window restarts either way.
        JudgeResult Judge()
        {
            JudgeResult r;
            if (_feeds > 0)
                r.verdict = Verdict::Cheered;
            else
            {
                r.verdict = Verdict::Booed;
                if (_roar > 0)
                    --_roar;
                if (_booed < kBooedMaxStacks)
                {
                    ++_booed;
                    r.booedAdded = true;
                    if (_booed == kBooedMaxStacks && !_yelled)
                    {
                        _yelled = true;
                        r.yell = true;
                    }
                }
            }
            _feeds = 0;
            r.roar = _roar;
            r.booed = _booed;
            return r;
        }

        void Reset() { *this = CrowdBook(); }

        std::uint8_t Roar() const { return _roar; }
        std::uint8_t Booed() const { return _booed; }
        std::uint32_t FeedsThisWindow() const { return _feeds; }

    private:
        std::uint32_t _feeds = 0;
        std::uint8_t _roar = 0;
        std::uint8_t _booed = 0;
        bool _yelled = false;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // OM6 Mojo (heroic)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kMojoFirstMs = 20000;
    inline constexpr std::uint32_t kMojoEveryMs = 25000;
    inline constexpr std::uint32_t kMojoCastMs = 3000;
    inline constexpr FlexAB kMojoTargets{ 1, 2 };
    inline constexpr std::uint32_t kMojoMysticHealth = 12000;      // the template's 5-player value (DT, WP-H heroic)
    inline constexpr std::uint32_t kMojoFrenzyMs = 15000;
    inline constexpr std::int32_t kMojoFrenzyDamagePct = 50;        // the stock Frenzy 8269 values
    inline constexpr std::int32_t kMojoFrenzyHastePct = 60;
    inline constexpr std::uint8_t kMojoRoarStacks = 2;
    inline constexpr std::uint32_t kMojoFrenzyLookEveryMs = 3000;  // Mojo Madness's look is a one-shot burst
    inline constexpr std::uint8_t kMojoKickPriority = 3;            // expected interrupt
    inline constexpr std::int8_t kMojoKillPriority = 3;             // kill order: the Mystic first
    inline constexpr std::uint32_t kMojoGiveUpMs = 10000;           // a Mystic that never started its chant leaves
    inline constexpr float kMojoRangeYd = 60.f;                     // the chant's range (Ogre Mojo, ignores LoS)

    // A Mystic's crowd spot (where it is summoned and walks back to) and the spot it steps out to and chants from.
    struct MysticPost
    {
        Point3 crowd;
        Point3 stepOut;
    };

    inline constexpr std::array<MysticPost, 2> kHallMysticPosts{ {
        { { -12.0f, -321.0f, 31.8f }, { -17.5f, -321.0f, 31.8f } },     // the west alcove
        { { -30.0f, -326.0f, 34.5f }, { -24.0f, -326.0f, 31.8f } },     // the pile's foot
    } };
    inline constexpr std::array<MysticPost, 2> kBridgeMysticPosts{ {
        { { -37.2f, -394.0f, 31.8f }, { -37.2f, -402.5f, 31.8f } },     // the west door
        { { -37.0f, -446.0f, 32.0f }, { -37.0f, -438.0f, 32.5f } },     // the east door
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // The crowd's stands (the Brawl Fans, OM1; summoned on the pull, they run in from the hall's doorway)
    // ----------------------------------------------------------------------------------------------------------------

    // z is a probe height: the AI drops each spot onto the floor below it (WorldObject::GetMapHeight).
    inline constexpr Point3 kFansRunInFrom{ -20.8f, -357.5f, 31.8f };
    inline constexpr std::array<Point3, 18> kHallStands{ {
        // west alcove (x -14.8..-10.2, y -331.2..-310.8)
        { -12.0f, -313.0f, 31.8f }, { -12.0f, -317.0f, 31.8f }, { -12.0f, -321.0f, 31.8f }, { -12.0f, -325.0f, 31.8f },
        { -12.0f, -329.0f, 31.8f },
        // east alcove (y -359.8..-345.2)
        { -12.0f, -347.5f, 31.8f }, { -12.0f, -351.0f, 31.8f }, { -12.0f, -354.5f, 31.8f },
        // the rock pile (x -45..-26, z 36..42)
        { -30.0f, -300.0f, 38.0f }, { -30.0f, -308.0f, 38.0f }, { -30.0f, -316.0f, 38.0f }, { -30.0f, -324.0f, 38.0f },
        { -30.0f, -332.0f, 38.0f }, { -30.0f, -340.0f, 38.0f }, { -30.0f, -348.0f, 38.0f },
        // the doorway into the big room
        { -24.0f, -360.5f, 31.8f }, { -20.8f, -360.5f, 31.8f }, { -17.5f, -360.5f, 31.8f },
    } };

    // Heroic: the crowd at both bridge doors (outside each doorway).
    inline constexpr std::array<Point3, 10> kDoorStands{ {
        { -35.7f, -394.5f, 31.8f }, { -37.2f, -394.5f, 31.8f }, { -38.7f, -394.5f, 31.8f }, { -36.4f, -392.8f, 31.8f },
        { -38.0f, -392.8f, 31.8f },
        { -35.2f, -445.6f, 32.0f }, { -37.0f, -445.6f, 32.0f }, { -38.8f, -445.6f, 32.0f }, { -36.1f, -447.3f, 32.0f },
        { -37.9f, -447.3f, 32.0f },
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // OM7 To the bridge (heroic, 25%)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kShowdownHealthPct = 25.f;
    inline constexpr std::uint32_t kShowdownJumpMs = 2000;          // the trip (players, pets, Omokk)
    inline constexpr std::uint32_t kShowdownSettleMs = 300;         // he resumes the fight this long after landing
    inline constexpr float kShowdownMinSpeedZ = 20.f;               // the arc clears the walls between hall and bridge
    inline constexpr std::uint8_t kLandingsSmall = 5;               // at 5 players; 7 at 6 or more
    inline constexpr std::uint8_t kLandingVictim = 1;               // his victim lands at the span's north end
    inline constexpr float kLandingShareOffsetYd = 1.5f;            // a second player on one spot stands off it

    constexpr std::uint8_t LandingCount(std::uint32_t players)
    {
        return players <= 5 ? kLandingsSmall
            : static_cast<std::uint8_t>(BlackrockSpireRework::kOmokkLandings.size());
    }

    // The landing of the i-th jumper (0-based; his victim goes first) when `count` spots are in use: its spot and, for
    // a spot already taken, an offset along the bridge (+1.5, -1.5, +3, -3 ... yd in y).
    struct Landing
    {
        std::uint8_t spot = 0;
        float yOffset = 0.f;
    };

    constexpr Landing LandingFor(std::size_t index, std::uint8_t count)
    {
        if (count == 0)
            return {};
        // The victim takes kLandingVictim; the others fill the rest in order, then wrap.
        std::size_t const order = index == 0 ? kLandingVictim : (index <= kLandingVictim ? index - 1 : index);
        std::size_t const spot = order % count;
        std::size_t const round = order / count;
        float const step = static_cast<float>((round + 1) / 2) * kLandingShareOffsetYd;
        return { static_cast<std::uint8_t>(spot), round == 0 ? 0.f : (round % 2 ? step : -step) };
    }

    // The jump's horizontal speed for a trip of `distance3d` yd in `ms` (at least 8 yd/s: MoveJump's duration follows
    // the path length, so a near-vertical haul-up still takes about `ms`).
    constexpr float TripSpeedXY(float distance3d, std::uint32_t ms)
    {
        float const s = ms ? distance3d * 1000.f / static_cast<float>(ms) : distance3d;
        return std::max(8.f, s);
    }

    // The living Spirestone ogres on the bridge [db spawns]: they step aside into the crowd for the showdown and go
    // back to their posts after the fight (the rares stay stock, ruling 2).
    struct StepAside
    {
        std::uint32_t spawnId;
        Point3 to;
    };

    inline constexpr std::array<StepAside, 4> kBridgeOgres{ {
        { 43519, { -34.2f, -392.5f, 31.8f } },      // Spirestone Battle Lord 9218 (rare), mid-bridge
        { 43520, { -40.5f, -448.5f, 32.0f } },      // Spirestone Battle Mage 9197, the cross platform
        { 43506, { -33.5f, -448.5f, 32.0f } },      // Spirestone Enforcer 9199, the cross platform
        { 43523, { -37.0f, -450.0f, 32.0f } },      // Spirestone Butcher 9219 (rare, patrol), the east door
    } };

    // ----------------------------------------------------------------------------------------------------------------
    // OM8 Belly Slam, OM9 Bull Rush (heroic showdown)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kBellySlamPct = 15.f;
    inline constexpr float kBellySlamRadius = 8.f;
    inline constexpr std::uint32_t kBellySlamCastMs = 2000;
    inline constexpr std::uint32_t kBellySlamAfterLandMs = 3000;
    inline constexpr std::uint32_t kBellySlamEveryMs = 15000;
    inline constexpr float kBellySlamKnockYd = 20.f;
    inline constexpr float kBellySlamSpeedZ = 8.f;

    inline constexpr float kBullRushPct = 15.f;
    inline constexpr float kBullRushWidth = 3.f;
    inline constexpr float kBullRushLength = 20.f;
    inline constexpr std::uint32_t kBullRushWarnMs = 2000;
    inline constexpr std::uint32_t kBullRushAfterLandMs = 5000;
    inline constexpr std::uint32_t kBullRushEveryMs = 8000;
    inline constexpr FlexAB kBullRushTargets{ 1, 2 };
    inline constexpr float kBullRushChargeSpeed = 30.f;
    inline constexpr float kBullRushOverEdgeYd = 3.f;               // the throw ends this far past the near edge
    inline constexpr float kBullRushSpeedZ = 6.f;
    inline constexpr std::uint32_t kBrawlerLifeMs = 6000;           // paw, charge, then back into the crowd

    // The lanes start at the doors [designer .gps].
    inline constexpr Vec2 kWestDoor{ -36.95f, -397.75f };
    inline constexpr Vec2 kEastDoor{ -36.63f, -441.87f };
    // The Brawlers wait in the door crowds.
    inline constexpr Point3 kWestBrawler{ -37.0f, -394.0f, 31.8f };
    inline constexpr Point3 kEastBrawler{ -36.8f, -446.0f, 32.0f };

    // The far end of a Bull Rush lane: kBullRushLength from the door toward the target (straight down the bridge
    // when they coincide).
    inline Vec2 BullRushEnd(Vec2 door, Vec2 target)
    {
        float const dx = target.x - door.x;
        float const dy = target.y - door.y;
        float const d = std::sqrt(dx * dx + dy * dy);
        if (d < 0.01f)
        {
            float const down = door.y > kBridgeMiddle.y ? -1.f : 1.f;
            return { door.x, door.y + down * kBullRushLength };
        }
        return { door.x + dx / d * kBullRushLength, door.y + dy / d * kBullRushLength };
    }

    // The bridge deck's x extent at `y` (NM 1 table, one layer at z 31.8; the mesh edge, about 0.5 yd inside the real
    // one). Off the table's rows: the main span's.
    struct Extent
    {
        float minX;
        float maxX;
    };

    constexpr Extent BridgeExtentAt(float y)
    {
        if (y <= -397.f && y > -401.f)
            return { -39.2f, -35.2f };      // the west doorway
        if (y <= -401.f && y > -403.f)
            return { -41.0f, -33.0f };      // widening
        if (y <= -403.f && y > -408.5f)
            return { -45.2f, -29.8f };      // the west side bay
        if (y <= -408.5f && y > -427.f)
            return { -41.2f, -33.8f };      // the main span
        if (y <= -427.f && y > -431.f)
            return { -45.8f, -28.8f };      // the cross platform, near half
        if (y <= -431.f && y > -438.5f)
            return { -52.2f, -22.2f };      // the cross platform, wide part
        if (y <= -438.5f && y > -440.5f)
            return { -47.8f, -26.8f };      // tapers
        if (y <= -440.5f && y > -443.f)
            return { -39.8f, -34.2f };      // the east doorway
        return { -41.2f, -33.8f };
    }

    // Bull Rush's sideways throw (OM9): toward the nearer edge of the deck at the player's y, kBullRushOverEdgeYd past
    // it. `sign` is +1 (north, +x) or -1 (south).
    struct SideThrow
    {
        float sign = 1.f;
        float distance = 0.f;
    };

    constexpr SideThrow SideThrowAt(Vec2 p)
    {
        Extent const e = BridgeExtentAt(p.y);
        float const toMax = std::max(0.f, e.maxX - p.x);
        float const toMin = std::max(0.f, p.x - e.minX);
        if (toMax <= toMin)
            return { 1.f, toMax + kBullRushOverEdgeYd };
        return { -1.f, toMin + kBullRushOverEdgeYd };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // OM10 Pit Drop
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kPitDropPct = 70.f;
    inline constexpr float kPitDropSlowedPct = 35.f;                // Slow Fall or Levitate halves it
    // The catch line: the deck less 8 yd (z 23.8). The server sees a falling client's z only from its movement packets
    // (about every 0.5 s while falling: KT-B1's risk), so a catch fires up to about 0.5 s and 7 yd late: an 8 yd line
    // lands near the build spec's "15 yd, about 1.5 s into the fall", and 35 yd or more above the pit floor (50.8 yd
    // down).
    inline constexpr float kPitDropBelowYd = 8.f;
    inline constexpr std::uint32_t kPitDropGraceMs = 3000;
    inline constexpr std::uint32_t kHaulUpMs = 2000;
    inline constexpr float kHaulUpMinSpeedZ = 10.f;
    // The watch's region: the whole chasm under the bridge (the Firebrand camp floor runs x -72..3, NAVMESH-REPORT),
    // from just under the deck down past the pit floor. A knockback keeps its horizontal speed until it lands, so a
    // thrown player is still flying sideways when he reaches the catch line: the box spans the widest throw's reach
    // (PitThrowReachYd: Belly Slam about 46 yd from any deck point, the platform's ends x -52.2 / -22.2 included; a
    // Bull Rush off the platform's middle about 51 yd), so x -98.4..24.0 plus margin (R-1-A M1; the old x -56..-18
    // lost Belly Slam victims). The chasm's rock stops a real flight sooner. Along y the bridge's own deck and the
    // door walls stop a throw; a diagonal one drops at the chasm's end walls (y about -397 / -446).
    inline constexpr float kPitMinX = -100.f;
    inline constexpr float kPitMaxX = 30.f;
    inline constexpr float kPitMinY = -455.f;
    inline constexpr float kPitMaxY = -390.f;
    // The server learns a falling client's position about every 0.5 s (see kPitDropBelowYd).
    inline constexpr float kPitCatchLagSec = 0.5f;
    inline constexpr float kPitMinZ = BlackrockSpireRework::kOmokkPitFloorZ - 6.f;
    inline constexpr float kPitMaxZ = BlackrockSpireRework::kOmokkBridgeDeckZ - 1.f;

    static_assert(BlackrockSpireRework::kOmokkBridgeDeckZ - kPitDropBelowYd
        > BlackrockSpireRework::kOmokkPitFloorZ + 30.f, "the catch line must leave margin above the pit floor");

    // How far a knockback launched on the deck (`distance` on flat ground at `speedZ`) has carried a player sideways by
    // the time the server sees him under the catch line: the rise, the fall to kPitDropBelowYd under the deck, and
    // the packet lag. Not constexpr (sqrt); the host test checks the box against it.
    inline float PitThrowReachYd(float distance, float speedZ)
    {
        float const fallSec = (speedZ + std::sqrt(speedZ * speedZ + 2.f * kGravity * kPitDropBelowYd)) / kGravity;
        return KnockbackSpeedXY(distance, speedZ) * (fallSec + kPitCatchLagSec);
    }

    constexpr float PitDropPct(bool slowed)
    {
        return slowed ? kPitDropSlowedPct : kPitDropPct;
    }

    // The haul-up spot nearer to `y`: the west door's or the east door's.
    constexpr Point3 HaulUpFor(float y)
    {
        float const mid = (BlackrockSpireRework::kOmokkHaulUpWest.y + BlackrockSpireRework::kOmokkHaulUpEast.y) * 0.5f;
        return y >= mid ? BlackrockSpireRework::kOmokkHaulUpWest : BlackrockSpireRework::kOmokkHaulUpEast;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Boss data
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::int8_t kOmokkKillPriority = 0;
}

#endif
