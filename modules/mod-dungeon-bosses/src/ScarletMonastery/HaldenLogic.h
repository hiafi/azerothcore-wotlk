/*
 * mod-dungeon-bosses, Scarlet Monastery D10:
 * Drillmaster Corin Halden, the Master-at-Arms (300942), the pure, host-testable part (no engine headers). Build spec:
 * docs/dungeons/scarlet-monastery-3-armory.md "Drillmaster Corin Halden, the Master-at-Arms" (MA0-MA4, Build spec),
 * handoff section 3.5 row D10, 3.6, 3.8 (three rooms in a row), 3.9 (the `close-ranks` row of
 * `scarlet-monastery-shapes-2`), 7 #30 A (he faces north or south only, the lanes stop at the walls, the ring is 5 to
 * 11 yd). Tested by tests/sm_halden_test.cpp.
 *
 *   Spells     the WP's ids, inside kSpellsHalden (212950-212979), declared in apps/dbc-tools
 *              source/npcs/scarlet_monastery/halden.py
 *   The Drill  MA0 the command order and its clock: normal one command every 10 s; heroic a pair every 12 s, the
 *              second 2 s after the first lands, the next pair 2 s after the ring of a Javelins and Close Ranks pair
 *              (a 31 s drill)
 *   Rooms      the three rooms (NAVMESH: the south band, the middle chamber he spawns in, the north room) and the
 *              rank behind him along the 40 yd axis, its outer recruits closing in at a wall
 *   Shapes     MA1 the lanes clipped at the room's far wall, MA2 the cones, MA3 the javelin picks and the heroic
 *              offset, MA4 the ring the recruits run round him
 *   Tuning     NH<> percents and timings straight from the build spec (percents of the reference row: N level 37
 *              normal, H level 60 heroic)
 */

#ifndef MOD_DUNGEON_BOSSES_SM_HALDEN_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_HALDEN_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <utility>
#include <vector>

namespace SmHalden
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsHalden;

    enum HaldenSpells : std::uint32_t
    {
        SPELL_MA_CHARGE = kSpellSlice.first + 0,              // 212950 MA1 a lane's hit (resolve copy, Physical)
        SPELL_MA_CHARGE_LOOK = kSpellSlice.first + 1,         // 212951 MA1 the charge on a recruit (Charge's SV 867)
        SPELL_MA_SPEARS = kSpellSlice.first + 2,              // 212952 MA2 a cone's hit (resolve copy, Physical)
        SPELL_MA_SPEARS_LOOK = kSpellSlice.first + 3,         // 212953 MA2 the thrust on a recruit (Thrust's SV 13365)
        SPELL_MA_JAVELINS = kSpellSlice.first + 4,            // 212954 MA3 his 2 s interruptible cast
        SPELL_MA_JAVELIN = kSpellSlice.first + 5,             // 212955 MA3, MA3a a javelin's hit (resolve copy)
        SPELL_MA_JAVELIN_LOOK = kSpellSlice.first + 6,        // 212956 MA3 the javelin's flight (SV 11993)
        SPELL_MA_CLOSE_RANKS = kSpellSlice.first + 7,         // 212957 MA4 the band's tick (resolve copy, Physical)
        SPELL_MA_CLOSE_RANKS_LOOK = kSpellSlice.first + 8,    // 212958 MA4 Shield Wall's SV 345 on a recruit
        // 212959-212979 spare
    };
    static_assert(SPELL_MA_CLOSE_RANKS_LOOK <= kSpellSlice.last, "Halden's spells must stay in his slice");

    // Registry tags (the build spec's mechanic numbers; the failure ledger and the playtest greps key on them). The
    // drill row `close-ranks` (scarlet-monastery-shapes-2) drills the same band under its own tag 27.
    enum HaldenTags : std::uint32_t
    {
        TAG_MA_CHARGE           = 1,    // MA1 a lane
        TAG_MA_SPEARS           = 2,    // MA2 a cone
        TAG_MA_JAVELIN          = 3,    // MA3 a javelin of the first volley
        TAG_MA_SECOND_VOLLEY    = 31,   // MA3a a javelin of the heroic second volley
        TAG_MA_CLOSE_RANKS      = 4,    // MA4 the ring's band
    };

    // creature_text groups of 300942 (data/sql/updates/pending_db_world/rev_halden_scarlet_monastery.sql, ARM "Text").
    enum HaldenTexts : std::uint8_t
    {
        SAY_PULL            = 0,    // yell: "Fall in! Today's lesson is live targets!"
        SAY_CHARGE          = 1,    // yell (MA1): "Charge!"
        SAY_SPEARS          = 2,    // yell (MA2): "Spears, level!"
        SAY_JAVELINS        = 3,    // yell (MA3): "Javelins!"
        SAY_CLOSE_RANKS     = 4,    // yell (MA4): "Close ranks!"
        EMOTE_FUMBLE        = 5,    // boss emote (MA3 interrupted, normal): "The recruits fumble their javelins!"
        SAY_KILL            = 6,    // yell (a player dies): "Dismissed."
        SAY_DEATH           = 7,    // yell (his death): "Hold... the line..."
        SAY_PAIR_CHARGE     = 8,    // yell (heroic pair): "Charge, then spears!"
        SAY_PAIR_JAVELINS   = 9,    // yell (heroic pair): "Javelins, then close ranks!"
    };

    // The drill recruits' spear (a creature virtual item; VR: Thrust's animation needs a polearm to read): "Monster -
    // Spear, Badass Red" (live item_template 13631, display 19804). His own weapons are the Scarlet Myrmidon's
    // (creature_equip_template of 4295: 5305 and 1895).
    inline constexpr std::uint32_t kItemRecruitSpear = 13631;
    inline constexpr std::uint32_t kItemHaldenMainHand = 5305;
    inline constexpr std::uint32_t kItemHaldenOffHand = 1895;
    inline constexpr std::uint32_t kKillLineCooldownMs = 5000;     // his "Dismissed." on a player kill, once per 5 s

    // ----------------------------------------------------------------------------------------------------------------
    // MA0 The Drill
    // ----------------------------------------------------------------------------------------------------------------

    enum class Command : std::uint8_t
    {
        Charge,
        Spears,
        Javelins,
        CloseRanks,
    };

    inline constexpr std::uint32_t kCommandCount = 4;

    // The yell of a single command (normal, and the second of a heroic pair).
    constexpr std::uint8_t CommandText(Command c)
    {
        switch (c)
        {
            case Command::Charge:   return SAY_CHARGE;
            case Command::Spears:   return SAY_SPEARS;
            case Command::Javelins: return SAY_JAVELINS;
            default:                return SAY_CLOSE_RANKS;
        }
    }

    constexpr char const* CommandName(Command c)
    {
        switch (c)
        {
            case Command::Charge:   return "charge";
            case Command::Spears:   return "spears";
            case Command::Javelins: return "javelins";
            default:                return "close-ranks";
        }
    }

    // Timings (Build spec MA0-MA4).
    inline constexpr std::uint32_t kFirstCommandMs = 8000;      // the first yell, both difficulties
    inline constexpr std::uint32_t kNormalEveryMs = 10000;      // normal: a command every 10 s
    inline constexpr std::uint32_t kPairEveryMs = 12000;        // heroic: a pair every 12 s,
    inline constexpr std::uint32_t kPairGapMs = 2000;           // the second yell 2 s after the first lands,
    inline constexpr std::uint32_t kAfterRingMs = 2000;         // and after a ring pair, 2 s after the ring ends
    inline constexpr std::uint32_t kReadyMs = 2500;             // the rank readies (the marker): Charge, Spears, ring
    inline constexpr std::uint32_t kJavelinCastMs = 2000;       // MA3 his cast (interruptible)
    inline constexpr std::uint32_t kJavelinFlightMs = 2500;     // MA3 the flight (the circles' marker)
    inline constexpr std::uint32_t kSecondVolleyWarnMs = 1500;  // MA3a heroic: 1.5 s after the first lands
    inline constexpr NH<std::uint32_t> kRingMs{ 6000, 8000 };   // MA4 the ring turns 6 s (heroic 8 s)
    inline constexpr std::uint32_t kRingTickMs = 1000;          // MA4 a tick a second
    inline constexpr std::uint32_t kReformMs = 2000;            // the recruits jog back into rank (about 2 s)
    inline constexpr std::uint32_t kChargeBackMs = 1000;        // MA1 the recruits stand at the lane's end, then jog

    // When a command's hits land, from its yell (Javelins: the first volley).
    constexpr std::uint32_t LandMs(Command c)
    {
        return c == Command::Javelins ? kJavelinCastMs + kJavelinFlightMs : kReadyMs;
    }

    // When a command is over, from its yell (Close Ranks: the ring's end).
    constexpr std::uint32_t EndMs(Command c, bool heroic)
    {
        return c == Command::CloseRanks ? kReadyMs + kRingMs(heroic) : LandMs(c);
    }

    struct DrillCall
    {
        std::uint32_t yellMs = 0;       // ms from the pull
        Command command = Command::Charge;
        bool pairFirst = false;         // heroic: the first of a pair (the pair's yell)
        bool pairSecond = false;        // heroic: the second of a pair
    };

    // The `index`-th command of the fight (0-based). Normal: Charge, Spears, Javelins, Close Ranks at 8 s, then every
    // 10 s. Heroic: pairs (Charge and Spears, Javelins and Close Ranks) from 8 s, the second 2 s after the first
    // lands; the next pair 12 s after a Charge pair starts, or 2 s after the ring of a Javelins pair ends (a 31 s
    // drill). The rhythm never moves: a kicked Javelins keeps its slot.
    constexpr DrillCall CallAt(std::uint32_t index, bool heroic)
    {
        DrillCall call;
        if (!heroic)
        {
            call.yellMs = kFirstCommandMs + index * kNormalEveryMs;
            call.command = static_cast<Command>(index % kCommandCount);
            return call;
        }
        std::uint32_t const pair = index / 2;
        std::uint32_t start = kFirstCommandMs;
        for (std::uint32_t q = 0; q < pair; ++q)
        {
            if (q % 2 == 0)
                start += kPairEveryMs;
            else
                start += LandMs(Command::Javelins) + kPairGapMs + EndMs(Command::CloseRanks, true) + kAfterRingMs;
        }
        Command const first = (pair % 2 == 0) ? Command::Charge : Command::Javelins;
        if (index % 2 == 0)
        {
            call.yellMs = start;
            call.command = first;
            call.pairFirst = true;
        }
        else
        {
            call.yellMs = start + LandMs(first) + kPairGapMs;
            call.command = static_cast<Command>(static_cast<std::uint8_t>(first) + 1);
            call.pairSecond = true;
        }
        return call;
    }

    // The heroic pair's yell (at the first command of the pair).
    constexpr std::uint8_t PairText(Command first)
    {
        return first == Command::Charge ? SAY_PAIR_CHARGE : SAY_PAIR_JAVELINS;
    }

    // One full drill (four commands), start to start: 40 s normal, 31 s heroic.
    constexpr std::uint32_t DrillLengthMs(bool heroic)
    {
        return CallAt(4, heroic).yellMs - CallAt(0, heroic).yellMs;
    }

    // Commands yelled by `ms` into the fight.
    constexpr std::uint32_t CommandsBy(std::uint32_t ms, bool heroic)
    {
        std::uint32_t n = 0;
        while (n < 1000 && CallAt(n, heroic).yellMs <= ms)
            ++n;
        return n;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Rooms (NAVMESH "Halden": three rooms in a row joined by necks; +x north, +y west; floor z 18.5 to 19)
    // ----------------------------------------------------------------------------------------------------------------

    struct Room
    {
        float xMin;
        float xMax;
        float yMin;
        float yMax;

        constexpr bool Contains(Vec2 p) const { return p.x >= xMin && p.x <= xMax && p.y >= yMin && p.y <= yMax; }
        constexpr float Area() const { return (xMax - xMin) * (yMax - yMin); }
    };

    // The mesh's walkable boxes (the NAVMESH 2 yd raster of the upper hall, navmesh/maps2.txt, re-read 2026-11-20):
    // the three rooms and the two necks between them. The rank, the lanes and the ring stay in the room he stands in;
    // the bots' bounds and his leash take all five.
    inline constexpr Room kSouthBand{ 1843.f, 1859.f, -437.f, -375.f };
    inline constexpr Room kSouthNeck{ 1859.f, 1866.f, -391.f, -379.f };
    inline constexpr Room kMiddleChamber{ 1865.f, 1885.5f, -419.f, -375.f };
    inline constexpr Room kNorthNeck{ 1885.f, 1892.f, -415.f, -403.f };
    inline constexpr Room kNorthRoom{ 1892.f, 1911.f, -417.f, -357.f };
    inline constexpr std::array<Room, 5> kWalkable{ { kSouthBand, kSouthNeck, kMiddleChamber, kNorthNeck,
        kNorthRoom } };
    inline constexpr float kZMin = 16.f;
    inline constexpr float kZMax = 23.f;

    // The room he stands in, by x (the necks split at their middles).
    constexpr Room RoomAt(Vec2 p)
    {
        if (p.x < 1862.f)
            return kSouthBand;
        if (p.x > 1888.5f)
            return kNorthRoom;
        return kMiddleChamber;
    }

    constexpr bool OnFloor(Vec2 p)
    {
        for (Room const& r : kWalkable)
            if (r.Contains(p))
                return true;
        return false;
    }

    // His leash frame: the five boxes, 1 yd wider, z 16 to 23. ScarletMonasteryRework.h's HaldenArena() is S0's stub
    // frame (its y -420 to -378 cuts the chamber's west 3 yd and both end rooms); this one follows the mesh.
    inline DungeonKit::Arena RoomsArena()
    {
        std::vector<DungeonKit::ArenaRegion> regions;
        for (Room const& r : kWalkable)
            regions.push_back(ScarletMonasteryRework::BoxRegion(r.xMin - 1.f, r.xMax + 1.f, r.yMin - 1.f,
                r.yMax + 1.f, kZMin, kZMax));
        return DungeonKit::Arena(std::move(regions));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The rank (section 7 #30 A: he faces north or south only, the rank along the 40 yd axis)
    // ----------------------------------------------------------------------------------------------------------------

    enum class Facing : std::uint8_t
    {
        North,      // +x (orientation 0)
        South,      // -x (orientation pi)
    };

    constexpr float FacingAngle(Facing f)
    {
        return f == Facing::North ? 0.f : DungeonKit::kPi;
    }

    constexpr float FacingSign(Facing f)
    {
        return f == Facing::North ? 1.f : -1.f;
    }

    constexpr char const* FacingName(Facing f)
    {
        return f == Facing::North ? "north" : "south";
    }

    // The tank turns the drill only once it stands clearly on the other side of him.
    inline constexpr float kFacingHysteresisYd = 1.5f;

    constexpr Facing ChooseFacing(Vec2 boss, Vec2 tank, Facing current)
    {
        if (tank.x > boss.x + kFacingHysteresisYd)
            return Facing::North;
        if (tank.x < boss.x - kFacingHysteresisYd)
            return Facing::South;
        return current;
    }

    // An orientation (out of combat: his own) snapped to the nearer of north and south.
    inline Facing SnapFacing(float orientation)
    {
        return std::cos(orientation) >= 0.f ? Facing::North : Facing::South;
    }

    inline constexpr NH<std::uint32_t> kRecruits{ 5, 7 };           // five recruits (heroic seven)
    inline constexpr NH<float> kRankSpacingYd{ 8.f, 7.f };          // 8 yd apart (heroic 7 yd): 32 / 42 yd wide
    inline constexpr std::uint32_t kMaxRecruits = 7;
    inline constexpr float kRankBehindYd = 8.f;                     // the rank stands 8 yd behind him
    inline constexpr float kWallMarginYd = 1.f;                     // nobody stands in a wall

    constexpr float Clamp(float v, float lo, float hi)
    {
        return v < lo ? lo : (v > hi ? hi : v);
    }

    // The rank's spots, west to east (+y first). The rank stands kRankBehindYd behind him (kept inside his room),
    // centered on his y; where a wall cuts it, that side's recruits close in toward the middle (their spacing shrinks
    // so the outermost stands at the wall), the other side keeps its spacing.
    inline std::vector<Vec2> RankSpots(Vec2 boss, Facing facing, std::uint32_t count, float spacing)
    {
        std::vector<Vec2> out;
        if (count == 0)
            return out;
        Room const room = RoomAt(boss);
        float const xLo = room.xMin + kWallMarginYd;
        float const xHi = room.xMax - kWallMarginYd;
        float const yLo = room.yMin + kWallMarginYd;
        float const yHi = room.yMax - kWallMarginYd;
        float const x = Clamp(boss.x - FacingSign(facing) * kRankBehindYd, xLo, xHi);
        float const yMid = Clamp(boss.y, yLo, yHi);
        float const half = static_cast<float>(count - 1) * 0.5f;    // spacings from the middle to an end
        float const westSpacing = half > 0.f && half * spacing > yHi - yMid ? (yHi - yMid) / half : spacing;
        float const eastSpacing = half > 0.f && half * spacing > yMid - yLo ? (yMid - yLo) / half : spacing;
        for (std::uint32_t i = 0; i < count; ++i)
        {
            float const k = half - static_cast<float>(i);     // > 0 west of the middle, < 0 east of it
            out.push_back({ x, yMid + k * (k >= 0.f ? westSpacing : eastSpacing) });
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA1 Charge! (lanes), MA2 Spears, level! (cones)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kChargeWidthYd = 4.f;
    inline constexpr float kChargeLengthYd = 35.f;      // the spec's run, clipped at the room's far wall
    inline constexpr float kChargeMinLengthYd = 2.f;
    inline constexpr float kChargeRunSpeed = 30.f;      // yd/s: the recruits' charge down the lane (a look)

    struct Lane
    {
        Vec2 from;
        Vec2 to;
    };

    // A lane straight ahead of a rank spot, kChargeLengthYd long but never past the far wall of his room (section 7
    // #30 A: in the middle chamber 8 to 10 yd of free run past him, not 35).
    inline Lane ChargeLane(Vec2 rankSpot, Facing facing, Room const& room)
    {
        float const sign = FacingSign(facing);
        float const wall = sign > 0.f ? room.xMax - kWallMarginYd * 0.5f : room.xMin + kWallMarginYd * 0.5f;
        float const free = std::max(kChargeMinLengthYd, (wall - rankSpot.x) * sign);
        float const length = std::min(kChargeLengthYd, free);
        return { rankSpot, { rankSpot.x + sign * length, rankSpot.y } };
    }

    inline constexpr float kSpearsAngleDeg = 60.f;
    inline constexpr float kSpearsLengthYd = 10.f;      // from the rank 8 yd behind him: 2 yd past him
    inline constexpr float kSpearsPastBossYd = 2.f;
    inline constexpr float kSpearsMinLengthYd = 2.f;

    // A cone's length: always 2 yd past him, never more (kSpearsLengthYd caps it). With his back near a wall the rank
    // is clamped closer than 8 yd behind him, and a full 10 yd cone would reach over his front corners where melee and
    // the tank stand (R-2-ARM m-6), so the cone shrinks with the rank's real distance behind him.
    constexpr float SpearsLengthYd(float rankX, float bossX, Facing facing)
    {
        float const behind = (bossX - rankX) * FacingSign(facing);
        float const length = behind + kSpearsPastBossYd;
        return length < kSpearsMinLengthYd ? kSpearsMinLengthYd : (length > kSpearsLengthYd ? kSpearsLengthYd : length);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA3 Javelins!
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kJavelinRadiusYd = 5.f;
    inline constexpr float kJavelinOffsetYd = 5.f;      // heroic: a random spot within 5 yd of the player
    inline constexpr float kJavelinSpeed = 18.f;        // yd/s: Throw Javelin 62778's Speed (the look's flight)

    // The javelin targets, one per recruit, as indices into the fight's players (in a shuffled order the caller
    // makes). Normal: a different player each, as many as there are players (a recruit with nobody left does not
    // throw). Heroic: the same, and every recruit past the players (two at five players) throws at a random player.
    // `rand01()` returns [0, 1).
    template <class Rand>
    std::vector<std::uint32_t> JavelinPicks(std::uint32_t players, std::uint32_t recruits, bool heroic, Rand&& rand01)
    {
        std::vector<std::uint32_t> out;
        if (players == 0)
            return out;
        for (std::uint32_t i = 0; i < recruits && i < players; ++i)
            out.push_back(i);
        if (heroic)
            for (std::uint32_t i = players; i < recruits; ++i)
                out.push_back(std::min(players - 1,
                    static_cast<std::uint32_t>(rand01() * static_cast<float>(players))));
        return out;
    }

    // Heroic: the javelin lands at a random spot within kJavelinOffsetYd of the player (uniform over the disc), on the
    // floor (a spot off it is pulled back toward the player until it is on). Normal: the player's spot.
    template <class Rand>
    Vec2 JavelinSpot(Vec2 player, bool heroic, Rand&& rand01)
    {
        if (!heroic)
            return player;
        float const angle = rand01() * 2.f * DungeonKit::kPi;
        float const r = kJavelinOffsetYd * std::sqrt(rand01());
        for (int step = 0; step < 4; ++step)
        {
            float const rr = r * static_cast<float>(4 - step) / 4.f;
            Vec2 const p{ player.x + rr * std::cos(angle), player.y + rr * std::sin(angle) };
            if (OnFloor(p))
                return p;
        }
        return player;
    }

    // How long after the throw the look leaves the recruit so that it lands with the hit (`flightMs` after the throw).
    constexpr std::uint32_t LookDelayMs(float distYd, std::uint32_t flightMs)
    {
        float const travel = distYd / kJavelinSpeed * 1000.f;
        return travel >= static_cast<float>(flightMs) ? 0u : flightMs - static_cast<std::uint32_t>(travel);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // MA4 Close Ranks!
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kRingInnerYd = 5.f;          // section 7 #30 A: 5 to 11 yd (the spec's 6 to 14 covered
    inline constexpr float kRingOuterYd = 11.f;         // half the middle chamber)
    inline constexpr float kRingPathYd = 8.f;           // the recruits run the band's middle
    inline constexpr std::uint32_t kRingStepMs = 1000;  // they move to the next point every second
    inline constexpr std::uint32_t kRingLookEveryMs = 2000;     // Shield Wall's impact, replayed (VR: an impact)

    // The ring step a second, so the recruits run one lap in the ring's time.
    constexpr float RingStepRad(bool heroic)
    {
        return 2.f * DungeonKit::kPi * static_cast<float>(kRingStepMs) / static_cast<float>(kRingMs(heroic));
    }

    // Recruit `i` of `count` on the ring round `boss`, `turned` radians on from the start (behind him), kept in his
    // room.
    inline Vec2 RingSpot(Vec2 boss, Facing facing, std::uint32_t i, std::uint32_t count, float turned)
    {
        float const angle = FacingAngle(facing) + DungeonKit::kPi
            + 2.f * DungeonKit::kPi * static_cast<float>(i) / static_cast<float>(count ? count : 1) + turned;
        Room const room = RoomAt(boss);
        return { Clamp(boss.x + kRingPathYd * std::cos(angle), room.xMin + kWallMarginYd, room.xMax - kWallMarginYd),
            Clamp(boss.y + kRingPathYd * std::sin(angle), room.yMin + kWallMarginYd, room.yMax - kWallMarginYd) };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (Build spec "Mechanics"; percents of the reference row: N level 37, H level 60)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr NH<float> kHitPct{ 30.f, 45.f };       // Charge, Spears, Javelins, the second volley: Weakened
    inline constexpr NH<float> kRingPct{ 10.f, 12.f };      // Close Ranks a second, lingering (no Weakened)

    // The fight's length (Build spec "Tuning": effective group DPS 768 N / 3,145 H; the bots do about half of it).
    inline constexpr std::uint32_t kEffectiveDpsNormal = 768;
    inline constexpr std::uint32_t kEffectiveDpsHeroic = 3145;
    inline constexpr std::uint32_t kHaldenHealthNormal = 60000;
    inline constexpr std::uint32_t kHaldenHealthHeroic = 300000;

    constexpr float FightSeconds(bool heroic, float dpsShare = 1.f)
    {
        return static_cast<float>(heroic ? kHaldenHealthHeroic : kHaldenHealthNormal)
            / (static_cast<float>(heroic ? kEffectiveDpsHeroic : kEffectiveDpsNormal) * dpsShare);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The AI's own clock
    // ----------------------------------------------------------------------------------------------------------------

    // A one-shot timer on the AI's ms clock.
    class Timer
    {
    public:
        void Start(std::uint64_t nowMs, std::uint32_t inMs)
        {
            _on = true;
            _dueMs = nowMs + inMs;
        }

        void Stop() { _on = false; }
        bool On() const { return _on; }
        bool Due(std::uint64_t nowMs) const { return _on && nowMs >= _dueMs; }
        std::uint64_t DueMs() const { return _dueMs; }

    private:
        bool _on = false;
        std::uint64_t _dueMs = 0;
    };
}

#endif
