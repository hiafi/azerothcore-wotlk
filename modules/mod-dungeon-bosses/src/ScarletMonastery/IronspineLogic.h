/*
 * mod-dungeon-bosses, Scarlet Monastery D2: Ironspine (6489), "Spare Parts in a rotting yard", the pure, host-testable
 * part (no engine headers). Build spec GY 378-433 (docs/dungeons/scarlet-monastery-1-graveyard.md "Ironspine"), handoff
 * section 3.5 row D2, section 3.6, section 3.8 row D2 and section 7 #24 A (his home is the open lawn). Tested by
 * tests/sm_ironspine_test.cpp.
 *
 *   Spells          the WP's ids, inside kSpellsIronspine (212350-212389), declared in apps/dbc-tools
 *                   source/npcs/scarlet_monastery/ironspine.py
 *   Tuning          NH<> constants: one number per difficulty, straight from the build spec
 *   RotEveryMs      IR1 Grave Rot's cadence: 14 s, 2 s less per part killed for good, never under 8 s
 *   ShatterQueue    IR2 the order the parts break off in: Fist, Ribcage, Eye; a returned part goes to the back
 *   NextHop         IR3 the Fist's next landing: 6 yd toward him, the last one at his edge
 *   CrushTickPct    IR4 the rising squeeze: 6 ticks weighted 1 to 6, 50% / 120% in all
 *   LandingRing     IR2 where a part lands: 15 to 20 yd from him, on the lawn, clear of pools and other parts
 *   FightArena      the lawn disc around his home (section 7 #24 A; the walled plot is gone)
 */

#ifndef MOD_DUNGEON_BOSSES_SM_IRONSPINE_LOGIC_H
#define MOD_DUNGEON_BOSSES_SM_IRONSPINE_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ScarletMonasteryRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace SmIronspine
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ScarletMonasteryRework.h; ids.yaml reservation `scarlet_monastery`).
    inline constexpr ScarletMonasteryRework::IdSlice kSpellSlice = ScarletMonasteryRework::kSpellsIronspine;

    enum IronspineSpells : std::uint32_t
    {
        SPELL_IR_GRAVE_ROT_CAST     = kSpellSlice.first + 0,    // 212350 IR1 the 1.5 s cast bar (Nature)
        SPELL_IR_GRAVE_ROT          = kSpellSlice.first + 1,    // 212351 IR1 / IR5 a pool's tick (resolve copy, Nature)
        SPELL_IR_GRAVE_ROT_LOOK_7   = kSpellSlice.first + 2,    // 212352 IR1 the pool's look at 7 yd (stalker aura)
        SPELL_IR_GRAVE_ROT_LOOK_8   = kSpellSlice.first + 3,    // 212353 ... 8 yd (heroic growth)
        SPELL_IR_GRAVE_ROT_LOOK_9   = kSpellSlice.first + 4,    // 212354 ... 9 yd
        SPELL_IR_GRAVE_ROT_LOOK_10  = kSpellSlice.first + 5,    // 212355 ... 10 yd
        SPELL_IR_SHATTER            = kSpellSlice.first + 6,    // 212356 IR2 the bone burst on him (look only)
        SPELL_IR_REASSEMBLED        = kSpellSlice.first + 7,    // 212357 IR2 +10% damage done per stack
        SPELL_IR_REASSEMBLE_HEAL    = kSpellSlice.first + 8,    // 212358 IR2 a part reattaches: heal (base point 0)
        SPELL_IR_FIST_SLAM          = kSpellSlice.first + 9,    // 212359 IR3 a hop's landing (resolve copy, Physical)
        SPELL_IR_FIST_LANDING       = kSpellSlice.first + 10,   // 212360 IR3 the landing's look (the Fist on itself)
        SPELL_IR_CRUSH              = kSpellSlice.first + 11,   // 212361 IR4 the cage's hold: a root (root mechanic)
        SPELL_IR_CRUSH_TICK         = kSpellSlice.first + 12,   // 212362 IR4 a squeeze (base point 0, ignores armor)
        SPELL_IR_RIBCAGE_CLOSED     = kSpellSlice.first + 13,   // 212363 IR4 on the cage while it holds anyone
        SPELL_IR_EYE_SIGHT          = kSpellSlice.first + 14,   // 212364 IR5 the 2 s mark on a player a pool targets
        SPELL_IR_GLARE_CAST         = kSpellSlice.first + 15,   // 212365 IR6 the Eye's 2 s cast bar (heroic)
        SPELL_IR_GLARE              = kSpellSlice.first + 16,   // 212366 IR6 the 2 s stun on a player facing the Eye
        // 212367-212389 spare
    };
    static_assert(SPELL_IR_GLARE <= kSpellSlice.last, "Ironspine's spells must stay in his slice");

    // The rung looks of a pool, by radius (WP-V's SV_GRAVE_ROT 90550-90553 on the spells above).
    struct RotRung
    {
        float radiusYd;
        std::uint32_t spellId;
    };
    inline constexpr std::array<RotRung, 4> kRotRungs{ {
        { 7.f, SPELL_IR_GRAVE_ROT_LOOK_7 },
        { 8.f, SPELL_IR_GRAVE_ROT_LOOK_8 },
        { 9.f, SPELL_IR_GRAVE_ROT_LOOK_9 },
        { 10.f, SPELL_IR_GRAVE_ROT_LOOK_10 },
    } };

    // Registry tags (one per mechanic; the failure ledger and the playtest greps key on them).
    enum IronspineTags : std::uint32_t
    {
        TAG_IR_GRAVE_ROT    = 1,    // IR1 a pool under him
        TAG_IR_CRUMBLE      = 2,    // IR2 a killed part's pool
        TAG_IR_FIST         = 3,    // IR3 a hop's landing
        TAG_IR_EYE_POOL     = 5,    // IR5 a pool under a player while the Eye is loose
        TAG_IR_GLARE        = 6,    // IR6 heroic
    };

    // Text groups (ScarletMonasteryRework.h kTextRanges: 6489 0-3, the Eye 300902 0; all new boss emotes, type 41).
    enum IronspineTexts : std::uint8_t
    {
        EMOTE_IR_GRAVE_ROT  = 0,    // "%s retches up grave rot."
        EMOTE_IR_SHATTER    = 1,    // "%s's bones crack apart!"
        EMOTE_IR_BARE       = 2,    // "%s is nothing but rot and iron!" (all three parts killed)
        EMOTE_IR_RIBCAGE    = 3,    // "The ribcage closes over $n!"
    };
    enum IronspineEyeTexts : std::uint8_t
    {
        EMOTE_IR_EYE_GLARE  = 0,    // "%s opens wide!" (heroic)
    };

    // MovePoint ids.
    inline constexpr std::uint32_t POINT_IR_EYE_HOME = 1;   // the Eye floating to him

    // ----------------------------------------------------------------------------------------------------------------
    // The parts (IR2): his three named drops, each its own entry
    // ----------------------------------------------------------------------------------------------------------------

    enum class Part : std::uint8_t
    {
        Fist,
        Ribcage,
        Eye,
    };
    inline constexpr std::size_t kPartCount = 3;
    inline constexpr std::array<Part, kPartCount> kShatterOrder{ { Part::Fist, Part::Ribcage, Part::Eye } };

    constexpr std::uint32_t PartEntry(Part part)
    {
        switch (part)
        {
            case Part::Fist:    return ScarletMonasteryRework::NPC_SM_IRONSPINE_FIST;
            case Part::Ribcage: return ScarletMonasteryRework::NPC_SM_IRONSPINE_RIBCAGE;
            case Part::Eye:     return ScarletMonasteryRework::NPC_SM_IRONSPINE_EYE;
        }
        return 0;
    }

    constexpr std::optional<Part> PartOf(std::uint32_t entry)
    {
        for (Part part : kShatterOrder)
            if (PartEntry(part) == entry)
                return part;
        return std::nullopt;
    }

    constexpr std::size_t PartIndex(Part part)
    {
        return static_cast<std::size_t>(part);
    }

    constexpr char const* PartName(Part part)
    {
        switch (part)
        {
            case Part::Fist:    return "fist";
            case Part::Ribcage: return "ribcage";
            case Part::Eye:     return "eye";
        }
        return "?";
    }

    constexpr std::uint8_t PartBit(Part part)
    {
        return static_cast<std::uint8_t>(1u << PartIndex(part));
    }

    inline constexpr std::uint8_t kAllPartsMask = 0x7;

    constexpr std::uint32_t PartsKilled(std::uint8_t killedMask)
    {
        std::uint32_t n = 0;
        for (Part part : kShatterOrder)
            if (killedMask & PartBit(part))
                ++n;
        return n;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (GY 391-401 Build spec; percents of the reference row: N level 32, H level 60 heroic)
    // ----------------------------------------------------------------------------------------------------------------

    // IR1 Grave Rot: a 1.5 s cast (emote line 0), then a 7 yd pool under him; first at 6 s, then every 14 s, 2 s less
    // for each part killed for good (14, 12, 10, 8 s). 5% / 8% Nature a second, no Weakened (a lingering patch).
    // Normal pools stay for the fight; heroic pools grow from 7 to 10 yd over 30 s and fade at 60 s.
    inline constexpr std::uint32_t kRotFirstMs = 6000;
    inline constexpr std::uint32_t kRotBaseEveryMs = 14000;
    inline constexpr std::uint32_t kRotStepPerKillMs = 2000;
    inline constexpr std::uint32_t kRotMinEveryMs = 8000;
    inline constexpr std::uint32_t kRotCastMs = 1500;
    inline constexpr std::uint32_t kRotTickMs = 1000;
    inline constexpr NH<float> kRotPct{ 5.f, 8.f };
    inline constexpr float kRotFromYd = 7.f;
    inline constexpr NH<float> kRotToYd{ 7.f, 10.f };
    inline constexpr std::uint32_t kRotGrowOverMs = 30000;       // heroic
    inline constexpr std::uint32_t kRotGrowStepMs = 10000;       // heroic: 7 -> 8 -> 9 -> 10 yd
    inline constexpr NH<std::uint32_t> kRotLifeMs{ 0, 60000 };  // 0: the whole fight
    // A killed part crumbles into a pool where it dies (the same rot), warned like his own.
    inline constexpr std::uint32_t kCrumbleWarnMs = 1500;

    constexpr std::uint32_t RotEveryMs(std::uint32_t partsKilled)
    {
        std::uint32_t const cut = kRotStepPerKillMs * partsKilled;
        return cut + kRotMinEveryMs >= kRotBaseEveryMs ? kRotMinEveryMs : kRotBaseEveryMs - cut;
    }

    // IR5: while the Eye is loose, each Grave Rot also drops a pool under 2 random players (tank included), a 2 s
    // marker first; then it is a pool like his.
    inline constexpr std::uint32_t kEyePools = 2;
    inline constexpr std::uint32_t kEyePoolWarnMs = 2000;

    // IR2 Shatter: first at 12 s, then every 22 s (heroic 20 s), one part (heroic two) in the order Fist, Ribcage,
    // Eye. A part flies 15 to 20 yd from him to open floor (emote line 1).
    inline constexpr std::uint32_t kShatterFirstMs = 12000;
    inline constexpr NH<std::uint32_t> kShatterEveryMs{ 22000, 20000 };
    inline constexpr NH<std::uint32_t> kPartsPerShatter{ 1, 2 };
    inline constexpr float kLandMinYd = 15.f;
    inline constexpr float kLandMaxYd = 20.f;
    inline constexpr float kLandShortestYd = 13.f;      // a landing a wall cut shorter than this is refused
    inline constexpr float kFlySpeedYdPerSec = 20.f;    // the throw out (and the Ribcage's spring home): about 1 s
    inline constexpr float kFlyMinSpeedZ = 8.f;
    inline constexpr std::uint32_t kLandSlackMs = 200;  // after the computed flight time, the part counts as landed

    // Flight time of a jump of `distYd` at `speedXY` (MoveJump: horizontal speed), plus the slack.
    inline std::uint32_t FlightMs(float distYd, float speedXY = kFlySpeedYdPerSec)
    {
        if (speedXY <= 0.f)
            return kLandSlackMs;
        return static_cast<std::uint32_t>(std::lround(std::max(0.f, distYd) / speedXY * 1000.f)) + kLandSlackMs;
    }

    // Reaching him: he heals 10% / 15% of his maximum health and gains a Reassembled stack (+10% damage done; 3 at
    // most on normal, the group-failure cap below 60; no cap on heroic). The part goes to the back of the queue.
    inline constexpr NH<float> kReattachHealPct{ 10.f, 15.f };
    inline constexpr NH<std::uint32_t> kReassembledCap{ 3, 0 };   // 0: no cap
    inline constexpr std::uint32_t kReassembledAuraMax = 99;      // the aura's own StackAmount (DT)
    // A part arrives when it is this close to his combat reach (2D).
    inline constexpr float kArriveSlackYd = 2.5f;

    constexpr std::uint32_t ReassembledCap(bool heroic)
    {
        std::uint32_t const cap = heroic ? kReassembledCap.heroic : kReassembledCap.normal;
        return cap ? cap : kReassembledAuraMax;
    }

    constexpr std::uint32_t ReassembledAfter(std::uint32_t before, bool heroic)
    {
        std::uint32_t const top = ReassembledCap(heroic);
        return before >= top ? top : before + 1;
    }

    inline bool Arrived(float dist2d, float bossReach)
    {
        return dist2d <= bossReach + kArriveSlackYd;
    }

    inline std::uint32_t PctOfMax(std::uint32_t maxHealth, float pct)
    {
        return static_cast<std::uint32_t>(std::lround(static_cast<double>(maxHealth) * pct / 100.0));
    }

    // IR3 the Fist: knuckle-hops home, 6 yd every 3 s (2 yd/s); a 5 yd marker at the next landing 2 s before it lands;
    // 35% / 45% Physical plus Weakened to everyone under it, the tank included. The last hop lands at his edge (in
    // the melee around him). The model has no walk: each hop is a jump arc (VISUALS).
    inline constexpr float kFistHopYd = 6.f;
    inline constexpr std::uint32_t kFistHopEveryMs = 3000;
    inline constexpr std::uint32_t kFistMarkerWarnMs = 2000;
    inline constexpr std::uint32_t kFistFirstMarkerMs = kFistHopEveryMs - kFistMarkerWarnMs;    // after it lands
    inline constexpr std::uint32_t kFistJumpLeadMs = 500;       // the jump leaves this long before the landing
    inline constexpr float kFistMarkerYd = 5.f;
    inline constexpr NH<float> kFistPct{ 35.f, 45.f };
    inline constexpr float kFistStopBeyondReachYd = 0.5f;       // the last hop lands this far outside his reach

    struct Hop
    {
        Vec2 to;
        bool last = false;      // it lands at his edge: the Fist arrives
    };

    // The next hop from `from` toward `boss`: kFistHopYd along the line, or (when no more than that is left to his edge
    // at `stopYd`) the edge point itself.
    inline Hop NextHop(Vec2 from, Vec2 boss, float stopYd, float hopYd = kFistHopYd)
    {
        float const dist = DungeonKit::Distance(from, boss);
        if (dist <= stopYd + hopYd)
        {
            if (dist <= stopYd || dist < 0.001f)
                return { from, true };
            float const back = DungeonKit::BearingTo(boss, from);
            return { DungeonKit::Advance(boss, back, stopYd), true };
        }
        return { DungeonKit::Advance(from, DungeonKit::BearingTo(from, boss), hopYd), false };
    }

    // How many hops a Fist landing `distToEdgeYd` from his edge takes home (the 8 to 13 s of GY 291 at 15-20 yd).
    inline std::uint32_t HopsHome(float distToEdgeYd, float hopYd = kFistHopYd)
    {
        if (distToEdgeYd <= 0.f)
            return 0;
        return static_cast<std::uint32_t>(std::ceil(distToEdgeYd / hopYd));
    }

    // IR4 the Ribcage: it flies onto a random non-tank (heroic: also everyone within 6 yd of them, the tank too) and
    // closes over them. The prisoners are rooted for up to 12 s and keep every other action; each has a Crush: a tick
    // every 2 s weighted 1 to 6 that totals 50% (heroic 120%) of the reference row by the timeout. Killing the cage
    // (3k / 20k) frees them and kills the part for good; a root break frees that player only. At 12 s the cage springs
    // home and reattaches.
    inline constexpr std::uint32_t kCageHoldMs = 12000;
    inline constexpr std::uint32_t kCageHoldSlackMs = 1000;     // HoldInUnit's own timeout: after the script's
    inline constexpr std::uint32_t kCrushTickMs = 2000;
    inline constexpr std::uint32_t kCrushTicks = 6;
    inline constexpr NH<float> kCrushTotalPct{ 50.f, 120.f };
    inline constexpr NH<float> kCageNearbyYd{ 0.f, 6.f };       // heroic: everyone within 6 yd of the target too
    inline constexpr float kCageCloseReachYd = 8.f;             // the target must still be this close at the landing

    constexpr std::uint32_t CrushWeightSum()
    {
        return kCrushTicks * (kCrushTicks + 1) / 2;     // 21
    }

    // The percent of tick `tick` (1-based, 1..6); 0 outside.
    constexpr float CrushTickPct(bool heroic, std::uint32_t tick)
    {
        if (tick == 0 || tick > kCrushTicks)
            return 0.f;
        return kCrushTotalPct(heroic) * static_cast<float>(tick) / static_cast<float>(CrushWeightSum());
    }

    // IR5 / IR6 the Eye: floats home at 1.5 yd/s (re-aimed every second). Heroic Glare: every 6 s while it is loose
    // (first 6 s after it lands), a 2 s cast (the Eye's line 0); anyone facing the Eye within 40 yd when it lands is
    // stunned 2 s (look away).
    inline constexpr float kEyeSpeedYdPerSec = 1.5f;
    inline constexpr std::uint32_t kEyeRepathMs = 1000;
    inline constexpr std::uint32_t kGlareFirstMs = 6000;
    inline constexpr std::uint32_t kGlareEveryMs = 6000;
    inline constexpr std::uint32_t kGlareCastMs = 2000;
    inline constexpr float kGlareRangeYd = 40.f;

    // ----------------------------------------------------------------------------------------------------------------
    // ShatterQueue (IR2)
    // ----------------------------------------------------------------------------------------------------------------

    // The parts at home, in the order they break off next. A part leaves the queue when it breaks off, comes back at
    // the back when it reattaches, and never comes back once killed.
    class ShatterQueue
    {
    public:
        ShatterQueue() { Reset(); }

        void Reset()
        {
            _queue.assign(kShatterOrder.begin(), kShatterOrder.end());
            _killed = 0;
        }

        // Up to `count` parts off the front.
        std::vector<Part> Take(std::uint32_t count)
        {
            std::vector<Part> out;
            while (out.size() < count && !_queue.empty())
            {
                out.push_back(_queue.front());
                _queue.erase(_queue.begin());
            }
            return out;
        }

        // One named part out of the queue (`.dbtest`): false when it is not at home.
        bool TakePart(Part part)
        {
            auto it = std::find(_queue.begin(), _queue.end(), part);
            if (it == _queue.end())
                return false;
            _queue.erase(it);
            return true;
        }

        // A part reattached: to the back (unless it is already queued or killed).
        void Return(Part part)
        {
            if ((_killed & PartBit(part)) || Queued(part))
                return;
            _queue.push_back(part);
        }

        // A part killed for good: out of the queue for the rest of the fight.
        void Kill(Part part)
        {
            _killed = static_cast<std::uint8_t>(_killed | PartBit(part));
            _queue.erase(std::remove(_queue.begin(), _queue.end(), part), _queue.end());
        }

        bool Queued(Part part) const { return std::find(_queue.begin(), _queue.end(), part) != _queue.end(); }
        bool Killed(Part part) const { return (_killed & PartBit(part)) != 0; }
        std::uint8_t KilledMask() const { return _killed; }
        std::uint32_t KilledCount() const { return PartsKilled(_killed); }
        bool AllKilled() const { return _killed == kAllPartsMask; }
        std::vector<Part> const& Order() const { return _queue; }

    private:
        std::vector<Part> _queue;
        std::uint8_t _killed = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The lawn (section 3.8 row D2, section 7 #24 A): his home (1796.5, 1285.5, 18.8), clearance 18.3, 1,242 sq yd
    // within 20 yd (99% floor), 4,586 within 40; the yard 18,737 sq yd [navmesh estimate]
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr Vec2 kHome = ScarletMonasteryRework::kIronspineHome.XY();
    inline constexpr float kHomeZ = ScarletMonasteryRework::kIronspineHome.z;
    inline constexpr float kArenaRadiusYd = 40.f;
    inline constexpr float kArenaZMin = 14.f;
    inline constexpr float kArenaZMax = 26.f;
    // The bots' planned spots stay this far from his home; a landing stays kLandingInsetYd inside the arena's edge.
    inline constexpr float kBoundsRadiusYd = 38.f;
    inline constexpr float kLandingInsetYd = 3.f;
    // His facing at home: toward the yard's entry from the Graveyard's start (south-west).
    inline constexpr float kHomeFacing = 4.28f;

    // The yard's north cut (R-1-GY MN-3): the council fights 63 yd north on the same lawn and both fights are optional,
    // so the disc stops at this y, 31.5 yd short of the council's spot (and of the Anguished Dead by it): a tank
    // dragging him to the arena's edge, a part landing at the ring's edge and the bots chasing it stay that far off.
    inline constexpr float kYardNorthY = 1317.f;
    // The bots' planned spots and the landings keep these yards inside the cut (as the disc's 2 / 3 yd insets).
    inline constexpr float kBoundsNorthInsetYd = 2.f;

    // The yard: the disc of `radius` round his home, cut at y = northY (32 corners on the circle, those north of the
    // cut moved onto it; convex, inside the disc).
    inline std::vector<Vec2> YardPolygon(float radius, float northY)
    {
        std::uint32_t constexpr kCorners = 32;
        std::vector<Vec2> out;
        out.reserve(kCorners);
        for (std::uint32_t i = 0; i < kCorners; ++i)
        {
            Vec2 p = DungeonKit::Advance(kHome, DungeonKit::kTwoPi * static_cast<float>(i) / kCorners, radius);
            p.y = std::min(p.y, northY);
            out.push_back(p);
        }
        return out;
    }

    // In the yard with `inset` yards to spare: within the disc less the inset and south of the cut less the inset.
    inline bool InYard(Vec2 p, float inset)
    {
        return DungeonKit::Distance(p, kHome) <= kArenaRadiusYd - inset && p.y <= kYardNorthY - inset;
    }

    // The leash frame: the lawn disc, cut short of the council (the walled plot of the stock spawn is no longer his).
    inline ScarletMonasteryRework::Arena FightArena()
    {
        return ScarletMonasteryRework::Arena(
            ScarletMonasteryRework::ArenaRegion::Polygon(YardPolygon(kArenaRadiusYd, kYardNorthY), kArenaZMin,
                kArenaZMax));
    }

    struct Circle2
    {
        Vec2 center;
        float radius = 0.f;
    };

    // The landing candidates around `boss`: 12 bearings from `startAngle` (radians), each at 17.5, then 15, then 20 yd,
    // kept inside the arena (with the inset); the ones clear of every `pool` (its radius + 1 yd) and every other part
    // (`taken`, 6 yd) first, then the rest in the same order. The engine takes the first whose collision-checked spot
    // is still far enough out.
    inline std::vector<Vec2> LandingRing(Vec2 boss, float startAngle, std::vector<Circle2> const& pools,
        std::vector<Vec2> const& taken)
    {
        std::array<float, 3> constexpr kRadii{ { 17.5f, kLandMinYd, kLandMaxYd } };
        std::uint32_t constexpr kBearings = 12;
        std::vector<Vec2> clear;
        std::vector<Vec2> blocked;
        for (float radius : kRadii)
            for (std::uint32_t i = 0; i < kBearings; ++i)
            {
                float const angle = startAngle + DungeonKit::kTwoPi * static_cast<float>(i) / kBearings;
                Vec2 const p = DungeonKit::Advance(boss, angle, radius);
                if (!InYard(p, kLandingInsetYd))
                    continue;
                bool ok = true;
                for (Circle2 const& pool : pools)
                    if (DungeonKit::Distance(p, pool.center) <= pool.radius + 1.f)
                        ok = false;
                for (Vec2 const& t : taken)
                    if (DungeonKit::Distance(p, t) <= 6.f)
                        ok = false;
                (ok ? clear : blocked).push_back(p);
            }
        clear.insert(clear.end(), blocked.begin(), blocked.end());
        return clear;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The bots' kill order (GY "Bots"): the Ribcage while it holds a player, then loose parts by distance to him
    // (Stratholme addition 11), then him. A loose part within kNearTiers[i].withinYd of him has that tier's priority.
    // ----------------------------------------------------------------------------------------------------------------

    struct NearTier
    {
        float withinYd;
        std::int8_t priority;
    };
    inline constexpr std::int8_t kCagePriority = 5;
    inline constexpr std::array<NearTier, 3> kNearTiers{ { { 8.f, 4 }, { 14.f, 3 }, { 100.f, 2 } } };

    // The priority a loose part at `distYd` from him gets (the highest tier it is inside).
    constexpr std::int8_t PartPriority(float distYd)
    {
        for (NearTier const& tier : kNearTiers)
            if (distYd <= tier.withinYd)
                return tier.priority;
        return 1;
    }
}

#endif
