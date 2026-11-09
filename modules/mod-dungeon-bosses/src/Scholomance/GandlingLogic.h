/*
 * mod-dungeon-bosses, Scholomance S11:
 * Darkmaster Gandling, the pure, host-testable part (no engine headers): his spell ids (inside kSpellsGandling of
 * ScholomanceRework.h), tuning, timers, the detention room cycle, the target picks, the lane / swap timing rule, the
 * Volley geometry and the fight modes S13 switches between. Tested by tests/scholo_gandling_test.cpp.
 *
 * Build spec: docs/dungeons/scholomance-rework.md SC 3034-3101 (Build spec), SC 2944-3023 (core loop, numbers, the
 * six lessons), the "Detention" notes at each instructor; handoff sections 3.5 row S11, 3.6, 3.7, 3.8.
 */

#ifndef MOD_DUNGEON_BOSSES_SCHOLOMANCE_GANDLING_LOGIC_H
#define MOD_DUNGEON_BOSSES_SCHOLOMANCE_GANDLING_LOGIC_H

#include "DungeonKitLogic.h"
#include "ScholomanceRework.h"
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

namespace ScholoGandling
{
    using DungeonKit::NH;
    using ScholomanceRework::Classroom;
    using ScholomanceRework::kClassroomCount;

    // Every spell of this WP sits in this slice (ScholomanceRework.h; ids.yaml reservation `scholomance`).
    inline constexpr ScholomanceRework::IdSlice kSpellSlice = ScholomanceRework::kSpellsGandling;

    // apps/dbc-tools source/npcs/scholomance/darkmaster_gandling.py declares each one.
    enum GandlingSpells : std::uint32_t
    {
        SPELL_GD_DETENTION_CAST     = 206330,   // GD1: his 1 s cast bar on the student (yell line 1)
        SPELL_GD_PORTAL_FLASH       = 206331,   // GD1 / GD4b: the portal flash on a player as they go and land
        SPELL_GD_HONOR_ROLL         = 206332,   // GD2: +100% damage and healing done for 15 s (self-applied)
        SPELL_GD_VOLLEY_CAST        = 206333,   // GD4: his 2 s cast bar (emote line 2)
        SPELL_GD_VOLLEY_HIT         = 206334,   // GD4: a lane's hit, the registry's resolve copy (Arcane)
        SPELL_GD_VOLLEY_STREAM      = 206335,   // GD4: a missile out of a portal at a player its lane hit (look)
        SPELL_GD_VOLLEY_LINGER      = 206336,   // GD4 heroic: the lane's lingering tick (resolve copy, Arcane)
        SPELL_GD_EXPELLED_GROWTH    = 206337,   // GD3 heroic: +10% damage done (and a little bigger) a stack
        SPELL_GD_TRANSFER_MARK      = 206338,   // GD4b: the linked-portal mark on both players (2 s)
        SPELL_GD_VOLLEY_STREAM_GROUND = 206339, // GD4: the stream down a lane as it fires (look only, at a point)
    };
    inline std::array<std::uint32_t, 10> constexpr kGandlingSpells{ {
        SPELL_GD_DETENTION_CAST, SPELL_GD_PORTAL_FLASH, SPELL_GD_HONOR_ROLL, SPELL_GD_VOLLEY_CAST, SPELL_GD_VOLLEY_HIT,
        SPELL_GD_VOLLEY_STREAM, SPELL_GD_VOLLEY_LINGER, SPELL_GD_EXPELLED_GROWTH, SPELL_GD_TRANSFER_MARK,
        SPELL_GD_VOLLEY_STREAM_GROUND } };

    // Registry tags (the ledger and the bot report name the mechanic by these).
    enum GandlingTags : std::uint32_t
    {
        TAG_GD_VOLLEY        = 1,
        TAG_GD_VOLLEY_LINGER = 2,
    };

    // ---- Timers (SC GD1-GD4b "First, cooldown") ---------------------------------------------------------------------
    std::uint32_t constexpr kDetentionFirstMs = 15000;
    std::uint32_t constexpr kDetentionEveryMs = 25000;
    std::uint32_t constexpr kDetentionCastMs = 1000;
    std::uint32_t constexpr kDetentionRetryMs = 3000;       // nobody (or no room) to detain now: look again
    std::uint32_t constexpr kArrivalTimeoutMs = 4000;       // the student must land in the room (or back) by then
    std::uint32_t constexpr kVolleyFirstMs = 10000;
    std::uint32_t constexpr kVolleyEveryMs = 20000;
    std::uint32_t constexpr kVolleyCastMs = 2000;
    std::uint32_t constexpr kVolleyWarnMs = 2000;           // the lanes show as the portals open, 2 s before the fire
    std::uint32_t constexpr kTransferFirstMs = 20000;
    std::uint32_t constexpr kTransferEveryMs = 30000;
    std::uint32_t constexpr kTransferWarnMs = 2000;
    std::uint32_t constexpr kLaneGapAfterSwapMs = 1500;     // SC GD4b: no lane fires within 1.5 s after a swap
    std::uint32_t constexpr kBarRetryMs = 500;              // a cast bar due while another bar runs waits this long
    std::uint32_t constexpr kHonorRollMs = 15000;           // SC GD2 (the spell's duration; the pytest pins it)
    std::uint32_t constexpr kExpelledGrowthEveryMs = 10000; // SC GD3 heroic: +10% damage every 10 s alive
    std::uint32_t constexpr kPortalStreamMissiles = 3;      // GD4: missiles per portal as its lane fires
    std::uint32_t constexpr kPortalStreamGapMs = 150;
    // R-C GANDLING N-5: the player he hit until this long ago still counts as the tank (a DPS who pulls him for a
    // moment as a Detention bar starts never makes the real tank a student).
    std::uint32_t constexpr kRecentTankMs = 2000;

    // ---- Numbers (SC "Numbers", handoff 3.6) ------------------------------------------------------------------------
    inline constexpr NH<std::uint32_t> kVolleyPortals{ 2, 3 };
    inline constexpr NH<float> kVolleyPct{ 30.f, 40.f };            // + Weakened (ruling 21)
    inline constexpr NH<std::uint32_t> kVolleyLingerMs{ 0, 4000 };  // heroic: the lanes stay 4 s after the fire
    std::uint32_t constexpr kVolleyLingerTickMs = 1000;
    // PROVISIONAL (designer default; SC gives no number): a heroic lane's lingering tick, % of the reference row, with
    // the kit's Standing in It slow. The impact is the lane's real cost; a tick only punishes staying in it.
    float constexpr kVolleyLingerPct = 10.f;
    float constexpr kLaneWidthYd = 4.f;
    float constexpr kLaneOverrunYd = 80.f;      // through the player to the far wall (the region clips it)
    std::uint32_t constexpr kExpelledGrowthPct = 10;
    float constexpr kExpelledSpawnYd = 3.f;     // beside its student

    // ---- Where the fight happens --------------------------------------------------------------------------------
    // Gandling's mechanics run in a region: the players they read (players), the walls a lane stops at (clip) and the
    // portal points on its edge. The fight's region is the Headmaster's Study; S13's gauntlet hands him a classroom's.
    struct GandlingRegion
    {
        DungeonKit::Arena players;
        DungeonKit::Arena clip;
        std::vector<DungeonKit::Vec2> portalPoints;
        float floorZ = 0.f;
        float zTolerance = 6.f;     // how far above or below floorZ a lane hits (the registry's shape band)
    };

    // The study floor as a box (the lanes run to its walls; GandlingArena() is his leash circle).
    inline DungeonKit::Arena StudyFloorArena()
    {
        using ScholomanceRework::kStudyFloor;
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Frame(kStudyFloor,
            DungeonKit::Box2{ 0.f, kStudyFloor.sizeX, 0.f, kStudyFloor.sizeY }, 73.0f, 84.0f));
    }

    inline GandlingRegion StudyRegion()
    {
        GandlingRegion r;
        r.players = ScholomanceRework::GandlingArena();
        r.clip = StudyFloorArena();
        r.portalPoints.assign(ScholomanceRework::kStudyPortalPoints.begin(),
            ScholomanceRework::kStudyPortalPoints.end());
        r.floorZ = ScholomanceRework::kStudyFloorZ;
        return r;
    }

    // ---- Fight modes (S13's hooks; GandlingFight.h) -----------------------------------------------------------------
    struct GandlingMode
    {
        bool detention = true;
        std::uint32_t detentionFirstMs = kDetentionFirstMs;
        std::uint32_t detentionEveryMs = kDetentionEveryMs;
        bool volley = true;
        std::uint32_t volleyFirstMs = kVolleyFirstMs;
        std::uint32_t volleyEveryMs = kVolleyEveryMs;
        std::uint32_t volleyPortals = 2;        // the lanes; ignored when lanesThroughEveryone
        bool lanesThroughEveryone = false;      // HM final phase: one lane through every player, the tank too
        std::uint32_t lingerMs = 0;
        bool transfer = false;
        std::uint32_t transferFirstMs = kTransferFirstMs;
        std::uint32_t transferEveryMs = kTransferEveryMs;
        bool transferTankEligible = true;       // SC GD4b heroic: the tank can be picked (and takes him along)
        bool transferRaisesExpelled = false;    // HM final phase: every swap raises an Expelled Student
        bool needsVictim = true;                // false: the mechanics run while he has no victim (S13's gauntlet)
    };

    // The normal and heroic fight (SC GD1-GD4b; Transfer is heroic only).
    constexpr GandlingMode FightMode(bool heroic)
    {
        GandlingMode m;
        m.volleyPortals = kVolleyPortals(heroic);
        m.lingerMs = kVolleyLingerMs(heroic);
        m.transfer = heroic;
        return m;
    }

    // The Graduate Exam's final phase (SC GD6, approved answers): no Detention, a lane through every player every
    // 20 s (lingering as on heroic), Transfer every 15 s raising an Expelled Student each. S13 starts it.
    constexpr GandlingMode FinalExamMode()
    {
        GandlingMode m = FightMode(true);
        m.detention = false;
        m.lanesThroughEveryone = true;
        m.transferFirstMs = 15000;
        m.transferEveryMs = 15000;
        m.transferRaisesExpelled = true;
        return m;
    }

    // ---- GD1: the room cycle ----------------------------------------------------------------------------------------
    // Each detention takes a room that has not held detention this cycle; once all six have, a new cycle starts in a
    // new random order. No room runs twice in a row unless it is the only room that can take a student (R-C GANDLING
    // N-1: the room just used is passed over in a new cycle wherever it falls, not only at its front). A room that
    // cannot take a student now (eligible() false) is passed over; when every room left in the cycle is blocked, the
    // cycle restarts early rather than stall (the blocked rooms come round again later).
    class RoomCycle
    {
    public:
        void Reset()
        {
            _left.clear();
            _last.reset();
        }

        // `eligible(room)`; `rand(n)` returns [0, n). nullopt: no room can take a student now.
        template <class Eligible, class Rand>
        std::optional<Classroom> Next(Eligible&& eligible, Rand&& rand)
        {
            for (int pass = 0; pass < 2; ++pass)
            {
                if (_left.empty() || pass == 1)
                    NewCycle(rand);
                if (std::optional<Classroom> const room = Take(eligible, false))
                    return room;
            }
            // Only the room just used can take a student: it runs again rather than nobody.
            return Take(eligible, true);
        }

        std::vector<Classroom> const& Left() const { return _left; }
        std::optional<Classroom> Last() const { return _last; }

    private:
        template <class Eligible>
        std::optional<Classroom> Take(Eligible& eligible, bool allowLast)
        {
            for (std::size_t i = 0; i < _left.size(); ++i)
            {
                if ((!allowLast && _last && _left[i] == *_last) || !eligible(_left[i]))
                    continue;
                Classroom const room = _left[i];
                _left.erase(_left.begin() + static_cast<std::ptrdiff_t>(i));
                _last = room;
                return room;
            }
            return std::nullopt;
        }

        template <class Rand>
        void NewCycle(Rand&& rand)
        {
            _left.clear();
            for (std::size_t i = 0; i < kClassroomCount; ++i)
                _left.push_back(Classroom(i));
            for (std::size_t i = _left.size(); i > 1; --i)     // Fisher-Yates
                std::swap(_left[i - 1], _left[rand(i)]);
            if (_last && _left.front() == *_last)
                std::swap(_left.front(), _left.back());
        }

        std::vector<Classroom> _left;
        std::optional<Classroom> _last;
    };

    // Whether a room can take a detained student now (S11's eligible() for RoomCycle):
    // - an instructor WP registered its lesson;
    // - its instructor is not fighting in it (F-B1: never a Coven lesson while Malicia fights there), nor a Graduate
    //   Examiner of that room (S13's gauntlet);
    // - no other living player stands in it (a gate opened for safety lets players in; never shut one on them).
    struct RoomState
    {
        bool hasLesson = false;
        bool instructorFighting = false;
        bool examinerFighting = false;
        bool othersInside = false;
    };

    constexpr bool RoomOpenForDetention(RoomState const& s)
    {
        return s.hasLesson && !s.instructorFighting && !s.examinerFighting && !s.othersInside;
    }

    // The Graduate Examiner entries whose fight happens in `room` (the Ravenian's vault holds two).
    inline std::vector<std::uint32_t> ExaminersOf(Classroom room)
    {
        using namespace ScholomanceRework;
        switch (room)
        {
            case Classroom::Coven:           return { NPC_SC_EXAMINER_MALICIA };
            case Classroom::HallOfTheDamned: return { NPC_SC_EXAMINER_KRASTINOV };
            case Classroom::HallOfSecrets:   return { NPC_SC_EXAMINER_POLKELT };
            case Classroom::RavenianVault:   return { NPC_SC_EXAMINER_RAVENIAN, NPC_SC_EXAMINER_CORVANE };
            case Classroom::BarovVault:      return { NPC_SC_EXAMINER_ALEXEI };
            case Classroom::ShadowVault:     return { NPC_SC_EXAMINER_ILLUCIA };
        }
        return {};
    }

    // ---- Target picks -------------------------------------------------------------------------------------------
    struct Candidate
    {
        std::uint64_t id = 0;
        bool inRegion = false;      // in the study (or S13's region)
        bool onFloor = false;       // on the region's floor box, where a lane reaches (R-C GANDLING N-6)
        bool passenger = false;     // a vehicle passenger (the Work Bench patient): never moved (F-C ruling)
        bool alive = false;
        bool tank = false;          // his victim
        bool detained = false;      // in a classroom now
        bool justBack = false;      // the last student back from detention
        bool honorRoll = false;     // under Honor Roll
    };

    // GD1: a living player in the study, never the tank, never the player just back, never one under Honor Roll, never
    // one already detained, never a vehicle passenger. nullopt: nobody qualifies (no detention this time).
    template <class Rand>
    std::optional<std::size_t> PickDetentionStudent(std::vector<Candidate> const& c, Rand&& rand)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (c[i].inRegion && c[i].alive && !c[i].tank && !c[i].detained && !c[i].justBack && !c[i].honorRoll
                && !c[i].passenger)
                pool.push_back(i);
        if (pool.empty())
            return std::nullopt;
        return pool[rand(pool.size())];
    }

    // A player a lane may aim through: in the region and on its floor (a lane stops at the floor's walls, so it never
    // reaches a player in a gate alcove), alive, not detained, not strapped into a vehicle (they cannot step out).
    constexpr bool LaneTarget(Candidate const& c)
    {
        return c.inRegion && c.onFloor && c.alive && !c.detained && !c.passenger;
    }

    // GD4: the players the lanes aim through, one per lane: `lanes` distinct players while they last (then repeats),
    // never the tank unless `tankToo`. Empty when nobody qualifies.
    template <class Rand>
    std::vector<std::size_t> PickLaneTargets(std::vector<Candidate> const& c, std::size_t lanes, bool tankToo,
        Rand&& rand)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (LaneTarget(c[i]) && (tankToo || !c[i].tank))
                pool.push_back(i);
        std::vector<std::size_t> out;
        if (pool.empty())
            return out;
        std::vector<std::size_t> bag;
        while (out.size() < lanes)
        {
            if (bag.empty())
                bag = pool;
            std::size_t const k = rand(bag.size());
            out.push_back(bag[k]);
            bag.erase(bag.begin() + static_cast<std::ptrdiff_t>(k));
        }
        return out;
    }

    // HM final phase: every player in the region, the tank too, one lane each.
    inline std::vector<std::size_t> EveryLaneTarget(std::vector<Candidate> const& c)
    {
        std::vector<std::size_t> out;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (LaneTarget(c[i]))
                out.push_back(i);
        return out;
    }

    // GD4b: two distinct players in the region (the tank too when `tankToo`), never a vehicle passenger (F-C ruling:
    // the Work Bench patient stays strapped in). nullopt: fewer than two qualify.
    template <class Rand>
    std::optional<std::pair<std::size_t, std::size_t>> PickTransferPair(std::vector<Candidate> const& c, bool tankToo,
        Rand&& rand)
    {
        std::vector<std::size_t> pool;
        for (std::size_t i = 0; i < c.size(); ++i)
            if (c[i].inRegion && c[i].alive && !c[i].detained && !c[i].passenger && (tankToo || !c[i].tank))
                pool.push_back(i);
        if (pool.size() < 2)
            return std::nullopt;
        std::size_t const a = rand(pool.size());
        std::size_t b = rand(pool.size() - 1);
        if (b >= a)
            ++b;
        return std::make_pair(pool[a], pool[b]);
    }

    // GD4: `count` portal points out of `points`, distinct while they last.
    template <class Rand>
    std::vector<std::size_t> PickPortalPoints(std::size_t points, std::size_t count, Rand&& rand)
    {
        std::vector<std::size_t> out;
        if (points == 0)
            return out;
        std::vector<std::size_t> bag;
        while (out.size() < count)
        {
            if (bag.empty())
                for (std::size_t i = 0; i < points; ++i)
                    bag.push_back(i);
            std::size_t const k = rand(bag.size());
            out.push_back(bag[k]);
            bag.erase(bag.begin() + static_cast<std::ptrdiff_t>(k));
        }
        return out;
    }

    // ---- GD4 / GD4b: the lane gap after a swap ---------------------------------------------------------------------
    // A swap due at `nowMs` may not leave a lane firing within kLaneGapAfterSwapMs after it (SC GD4b: "no lane fires
    // within 1.5 s of a swap"). Returns how long to hold the swap: 0 = swap now, else until just past the latest
    // conflicting fire, so the swap lands after those lanes (the floor is read again at the next Volley).
    inline std::uint32_t SwapHoldMs(std::uint32_t nowMs, std::vector<std::uint32_t> const& laneFireMs)
    {
        std::uint32_t hold = 0;
        for (std::uint32_t const fire : laneFireMs)
            if (fire >= nowMs && fire - nowMs <= kLaneGapAfterSwapMs)
                hold = std::max(hold, fire - nowMs + 100);
        return hold;
    }

    // GD1: a detention's return is a forced move too (R-C GANDLING S-3): the student waits in the room until no lane
    // fires within kLaneGapAfterSwapMs of their landing. Same rule as the swap; 0 = send them back now.
    inline std::uint32_t ReturnHoldMs(std::uint32_t nowMs, std::vector<std::uint32_t> const& laneFireMs)
    {
        return SwapHoldMs(nowMs, laneFireMs);
    }

    // ---- GD4: one lane ------------------------------------------------------------------------------------------
    // From the portal point through the aimed player to the region's wall (DungeonKit::LineStrikePath).
    inline DungeonKit::LinePath VolleyLane(GandlingRegion const& region, DungeonKit::Vec2 portal,
        DungeonKit::Vec2 through)
    {
        return DungeonKit::LineStrikePath(portal, through, kLaneOverrunYd, 0.f, &region.clip, region.floorZ, 0.5f);
    }

    // ---- GD3 heroic: Expelled Student growth --------------------------------------------------------------------
    // Stacks after `aliveMs` (one every 10 s, from the 10th second).
    constexpr std::uint32_t ExpelledGrowthStacks(std::uint32_t aliveMs)
    {
        return aliveMs / kExpelledGrowthEveryMs;
    }

    // Damage done factor of an Expelled Student with `stacks` (the aura's +10% each, added by the engine).
    constexpr float ExpelledDamageFactor(std::uint32_t stacks)
    {
        return 1.f + float(kExpelledGrowthPct * stacks) / 100.f;
    }
}

#endif
