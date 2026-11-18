/*
 * mod-dungeon-bosses, Blackrock Depths D2: Lord Roccor (9025), "the mountain is restless" (ruling 13), the pure,
 * host-testable part (no engine headers). Build spec S1 362-410 (docs/dungeons/blackrock-depths-1-detention-block.md,
 * the whole "Lord Roccor" section), handoff sections 3.4 rows D2, 3.5 row D2, 3.6, 3.8 (the road, from the NAVMESH
 * report), 3.9 (G1's `walk` drill row), 3.10. Tested by tests/brd_roccor_test.cpp.
 *
 *   Spells        the WP's ids, inside kSpellsRoccor (210750-210779), declared in apps/dbc-tools
 *                 source/npcs/blackrock_depths/roccor.py
 *   Tuning        NH<> constants: one number per difficulty, straight from the build spec
 *   The road      RO1: a straight 61.8 yd stretch through his spawn, out and back at 1.5 yd/s. Same bearing and
 *                 length as the spec's (580, -273) to (637, -249), moved 8.6 yd onto the road's middle: the spec's
 *                 line runs 0.5-4 yd off the north wall (NAVMESH 1.2); this one has 9-17 yd of floor on both sides,
 *                 passes through his spawn and through the two widest discs, (588, -278) and (626, -263)
 *   Rampage       RO3: the lane plan (20 yd ahead along the road, clipped at the road's end, turned round when less
 *                 than 10 yd is left; handoff section 8 #3) and the lane test for the trash and the Loosed Earth in it
 *   Underfoot     RO2: the Dark Iron entries, 10% of their health a second within 6 yd
 *   Leash         G1's `walk` row (blackrock-depths-shapes, BM MechanicDrill.h): the same walk speed, the same tags
 *                 and radii (the tank 8 yd, everyone 40 yd), judged once a second
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_ROCCOR_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_ROCCOR_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace BrdRoccor
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::Arena;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsRoccor;

    enum RoccorSpells : std::uint32_t
    {
        SPELL_RO_RAMPAGE_CAST       = kSpellSlice.first + 0,    // 210750 RO3 the 2.5 s rear-up (cast bar, emote 1)
        SPELL_RO_RAMPAGE            = kSpellSlice.first + 1,    // 210751 RO3 the lane's hit (resolve copy, Physical)
        SPELL_RO_RAMPAGE_SURGE      = kSpellSlice.first + 2,    // 210752 RO3 the surge's look on him (1.5 s state)
        SPELL_RO_GROUND_TREMOR      = kSpellSlice.first + 3,    // 210753 RO4 the 2 s cue (cast bar, emote 2)
        SPELL_RO_LOOSED_EARTH_RISE  = kSpellSlice.first + 4,    // 210754 RO4 the add's rise look (on itself)
        SPELL_RO_RETURN_TO_STONE    = kSpellSlice.first + 5,    // 210755 RO4 the add crumbles or merges (on itself)
        SPELL_RO_EARTHEN_MERGE      = kSpellSlice.first + 6,    // 210756 heroic: the 3% heal on him (the merge)
        SPELL_RO_UNDERFOOT          = kSpellSlice.first + 7,    // 210757 RO2 the crush look on him (anim + sound)
        SPELL_RO_UNDERFOOT_CRACK    = kSpellSlice.first + 8,    // 210758 RO2 the crack under a crushed Dark Iron
        SPELL_RO_FLUNG_BOULDERS     = kSpellSlice.first + 9,    // 210759 RO5 heroic: a circle's hit (resolve copy)
        SPELL_RO_FLUNG_BOULDER_LOOK = kSpellSlice.first + 10,   // 210760 RO5 the boulder in flight to a circle
        SPELL_RO_FLAME_SHOCK        = kSpellSlice.first + 11,   // 210761 RO6 the stock Flame Shock's copy, rescaled
        SPELL_RO_EARTH_SHOCK        = kSpellSlice.first + 12,   // 210762 RO7 the stock Earth Shock's copy, rescaled
        SPELL_RO_HURL_STONE         = kSpellSlice.first + 13,   // 210763 rule 10: a stone at a victim out of reach
        // 210764-210779 spare
    };
    static_assert(SPELL_RO_HURL_STONE <= kSpellSlice.last, "Roccor's spells must stay in his slice");

    // Registry and ledger tags: the same numbers as G1's drill (kBrdTagRampage 1, kBrdTagTankLeash 2,
    // kBrdTagRangeLeash 3), so the guided clear's ledger reads like the sweep's.
    enum RoccorTags : std::uint32_t
    {
        TAG_RAMPAGE         = 1,    // RO3 the lane
        TAG_TANK_LEASH      = 2,    // RO1 the tank more than kTankLeashYd from him (judged, nothing registered)
        TAG_RANGE_LEASH     = 3,    // RO1 anyone more than kRangeLeashYd from him (judged, nothing registered)
        TAG_BOULDERS        = 4,    // RO5 heroic: a Flung Boulders circle
    };

    // creature_text groups (9025 0-3, BlackrockDepthsRework.h kTextRanges; boss emotes, type 41).
    enum RoccorTexts : std::uint8_t
    {
        EMOTE_ROCCOR_PULL       = 0,    // "The halls tremble beneath %s's stride."
        EMOTE_ROCCOR_RAMPAGE    = 1,    // "%s rears up and Rampages down the road!"
        EMOTE_ROCCOR_LOOSED     = 2,    // "The ground heaves around %s, and the stone stands up!"
        EMOTE_ROCCOR_DEATH      = 3,    // "%s crumbles back into the mountain."
    };

    // The Dark Iron trash on his road (S1 Route and trash; RO2 Underfoot, RO3 "Dark Irons in the lane die").
    inline constexpr std::array<std::uint32_t, 4> kDarkIronEntries{ {
        8891,   // Anvilrage Guardsman
        8892,   // Anvilrage Footman
        8909,   // Fireguard
        8921,   // Bloodhound
    } };

    constexpr bool IsDarkIron(std::uint32_t entry)
    {
        for (std::uint32_t e : kDarkIronEntries)
            if (e == entry)
                return true;
        return false;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S1 Build spec; percents of the reference row: N level 52 3,196 / 3,226, H 4,120 / 4,110)
    // ----------------------------------------------------------------------------------------------------------------

    // RO1 Restless March: about 1.5 yd/s (speed_walk 0.6 x 2.5), G1's kRoccorWalkYdS.
    inline constexpr float kWalkYdS = 1.5f;
    inline constexpr float kSpeedWalkRate = 0.6f;       // creature_template.speed_walk (dbc-tools), x 2.5 yd/s

    // RO3 Rampage: first at 12 s, then every 20 s (heroic 15 s); a 2.5 s rear-up, a 20 x 8 yd lane ahead along the
    // road; 40% / 60% Physical, no Weakened (the heroic hit is over 50%); then he surges to the lane's end.
    inline constexpr std::uint32_t kRampageFirstMs = 12000;
    inline constexpr NH<std::uint32_t> kRampageEveryMs{ 20000, 15000 };
    inline constexpr std::uint32_t kRampageWarnMs = 2500;
    inline constexpr float kRampageLengthYd = 20.f;
    inline constexpr float kRampageWidthYd = 8.f;
    inline constexpr float kRampageMinLaneYd = 10.f;    // less left ahead: he turns round first (section 8 #3)
    inline constexpr NH<float> kRampagePct{ 40.f, 60.f };
    inline constexpr float kSurgeYdS = 24.f;            // Boulder Rush 55771 charges at 28; 20 yd in under a second
    inline constexpr std::uint32_t kSurgeGiveUpMs = 3000;   // a surge that never arrives: walk on from where he is
    inline constexpr std::uint32_t kSurgeLookMs = 1500;

    // RO4 Loosed Earth: first at 18 s, then every 25 s (heroic 20 s); a 2 s Ground Tremor, then 2 (heroic 3) at his
    // feet, each on a random non-tank; they crumble after 45 s. Cap: two waves alive (the spec's normal count; the
    // heroic 20 s cadence would let a third wave up, designer question 3).
    inline constexpr std::uint32_t kLoosedFirstMs = 18000;
    inline constexpr NH<std::uint32_t> kLoosedEveryMs{ 25000, 20000 };
    inline constexpr std::uint32_t kTremorCastMs = 2000;
    inline constexpr NH<std::uint32_t> kLoosedPerWave{ 2, 3 };
    inline constexpr NH<std::uint32_t> kLoosedCap{ 4, 6 };
    inline constexpr std::uint32_t kLoosedLifeMs = 45000;
    inline constexpr std::uint32_t kLoosedFadeMs = 1500;    // the crumble or merge look before the despawn
    inline constexpr float kLoosedSpawnYd = 3.f;
    inline constexpr float kLoosedOpeningThreat = 100.f;    // on its pick: any tank's first hits take it back
    inline constexpr NH<std::uint32_t> kLoosedHealth{ 7000, 12000 };    // the templates (dbc-tools, WP-H's heroic)

    // Heroic: a Loosed Earth caught in the Rampage lane merges back into him for 3% of his health.
    inline constexpr float kMergeHealPct = 3.f;

    // RO2 Underfoot: a Dark Iron within 6 yd of him takes 10% of its health every second (dead in 10 s). The looks
    // (his crush, the crack under each one) play at most every 3 s (the crack shakes the camera).
    inline constexpr float kUnderfootYd = 6.f;
    inline constexpr float kUnderfootZYd = 5.f;
    inline constexpr std::uint32_t kUnderfootTickMs = 1000;
    inline constexpr float kUnderfootPct = 10.f;
    inline constexpr std::uint32_t kUnderfootLookEveryMs = 3000;

    // RO5 Flung Boulders (heroic): first at 10 s, then every 5 s, 3 circles of 3 yd within 8 yd of him, on floor; a
    // 2 s marker, then 25% Physical + Weakened. The boulder's look is thrown just before the hit.
    inline constexpr std::uint32_t kBouldersFirstMs = 10000;
    inline constexpr std::uint32_t kBouldersEveryMs = 5000;
    inline constexpr std::uint32_t kBouldersCount = 3;
    inline constexpr float kBoulderRadiusYd = 3.f;
    inline constexpr float kBoulderSpreadYd = 8.f;      // a circle's centre within this of him
    inline constexpr float kBoulderApartYd = 3.f;       // one volley's centres at least this far apart (best effort)
    inline constexpr std::uint32_t kBoulderWarnMs = 2000;
    inline constexpr float kBoulderPct = 25.f;
    inline constexpr std::uint32_t kBoulderLookLeadMs = 400;    // the look is thrown this long before the hit

    // RO6 Flame Shock on his victim: 8 s, then every 8-18 s, 20 yd. RO7 Earth Shock on a random player in 20 yd
    // (the tank too, ruling 88): 7 s, then every 12 s. Their percents ride in the spells (dbc-tools hundredths).
    inline constexpr std::uint32_t kFlameShockFirstMs = 8000;
    inline constexpr std::uint32_t kFlameShockMinMs = 8000;
    inline constexpr std::uint32_t kFlameShockMaxMs = 18000;
    inline constexpr std::uint32_t kEarthShockFirstMs = 7000;
    inline constexpr std::uint32_t kEarthShockEveryMs = 12000;
    inline constexpr float kShockRangeYd = 20.f;
    inline constexpr std::uint32_t kShockRetryMs = 1000;
    inline constexpr NH<float> kFlameShockPct{ 6.f, 8.f };          // the hit
    inline constexpr NH<float> kFlameShockTickPct{ 2.f, 3.f };      // every 3 s for 12 s
    inline constexpr std::uint32_t kFlameShockMs = 12000;
    inline constexpr std::uint32_t kFlameShockTickMs = 3000;
    inline constexpr NH<float> kEarthShockPct{ 10.f, 15.f };
    inline constexpr std::uint32_t kEarthShockLockoutMs = 2000;     // the stock school lockout

    // Rule 10 (no free damage window): with nobody in his melee reach for 3 s he hurls a stone at his victim every
    // 2 s (designer question 2), 15% / 20%, the tank row on a tank.
    inline constexpr std::uint32_t kHurlGraceMs = 3000;
    inline constexpr std::uint32_t kHurlEveryMs = 2000;
    inline constexpr float kHurlRangeYd = 40.f;
    inline constexpr NH<float> kHurlPct{ 15.f, 20.f };

    // RO1 leash judge (G1's walk row: `leash 8 ... role=tank tag=2`, `leash 40 ... tag=3`, 1 s ticks). After a surge
    // the tank is 20 yd behind by design: its leash waits kSurgeLeashGraceMs (a run of 20 yd takes about 3 s).
    inline constexpr float kTankLeashYd = 8.f;
    inline constexpr float kRangeLeashYd = 40.f;
    inline constexpr std::uint32_t kLeashTickMs = 1000;
    inline constexpr std::uint32_t kSurgeLeashGraceMs = 4000;

    // Rule 10's stone waits for the out-of-reach grace and the next stone's time, and never lands while the tank is
    // still catching up after a surge (R-1-A m1: the surge's 4 s grace covers the stone too).
    inline bool HurlReady(std::uint32_t outOfReachMs, std::uint64_t clockMs, std::uint64_t nextHurlMs,
        std::uint64_t tankGraceUntil)
    {
        return outOfReachMs >= kHurlGraceMs && clockMs >= nextHurlMs && clockMs >= tankGraceUntil;
    }

    // The fight leash: he evades when nobody in combat with him has been within 40 yd of the road for 10 s (S1
    // Implementation "evade when no player is within about 40 yd of the route"; the kit guard's no-target timer).
    inline constexpr float kRoadLeashYd = 40.f;

    // ----------------------------------------------------------------------------------------------------------------
    // The road (RO1; [navmesh estimate]: NAVMESH 1.2 and this WP's probe of the 230 mmtiles, floor z and 9-17 yd of
    // floor on both sides of the line from s 0 to s 62)
    // ----------------------------------------------------------------------------------------------------------------

    // The west end (s = 0) and the east end (s = RoadLength()). Out of combat the waypoint path 473040 walks the same
    // two points (the SQL rev); in combat the script does.
    inline constexpr Point3 kRoadWest{ 580.0f, -282.3f, -80.9f };
    inline constexpr Point3 kRoadEast{ 637.0f, -258.4f, -82.7f };

    inline float RoadLength()
    {
        return std::hypot(kRoadEast.x - kRoadWest.x, kRoadEast.y - kRoadWest.y);
    }

    // The unit vector west to east.
    inline Vec2 RoadAxis()
    {
        float const l = RoadLength();
        return { (kRoadEast.x - kRoadWest.x) / l, (kRoadEast.y - kRoadWest.y) / l };
    }

    // The facing (radians, [0, 2pi)) of a walk along the road: `dir` > 0 toward the east end, else toward the west.
    inline float RoadFacing(int dir)
    {
        Vec2 const a = RoadAxis();
        Vec2 const to = dir > 0 ? a : Vec2{ -a.x, -a.y };
        return DungeonKit::BearingTo({ 0.f, 0.f }, to);
    }

    // How far along the road `p` lies (its projection), clamped to [0, length].
    inline float RoadS(Vec2 p)
    {
        Vec2 const a = RoadAxis();
        float const s = (p.x - kRoadWest.x) * a.x + (p.y - kRoadWest.y) * a.y;
        return std::clamp(s, 0.f, RoadLength());
    }

    // The distance of `p` from the road's line (either side).
    inline float RoadOffset(Vec2 p)
    {
        Vec2 const a = RoadAxis();
        return std::fabs(-(p.x - kRoadWest.x) * a.y + (p.y - kRoadWest.y) * a.x);
    }

    // The road's point at `s` (clamped), its height interpolated between the ends.
    inline Point3 RoadPoint(float s)
    {
        float const l = RoadLength();
        float const t = std::clamp(s, 0.f, l) / l;
        return { kRoadWest.x + (kRoadEast.x - kRoadWest.x) * t, kRoadWest.y + (kRoadEast.y - kRoadWest.y) * t,
            kRoadWest.z + (kRoadEast.z - kRoadWest.z) * t };
    }

    // The yards left ahead of `s` walking `dir`.
    inline float RoadAhead(float s, int dir)
    {
        float const l = RoadLength();
        float const c = std::clamp(s, 0.f, l);
        return dir > 0 ? l - c : c;
    }

    // The leg's end: the road's end `dir` points to.
    inline Point3 LegEnd(int dir)
    {
        return dir > 0 ? kRoadEast : kRoadWest;
    }

    // The walk direction a unit facing `orientation` keeps (a pull mid-walk carries on the same way): +1 east, -1 west.
    inline int DirectionOf(float orientation)
    {
        Vec2 const a = RoadAxis();
        return std::cos(orientation) * a.x + std::sin(orientation) * a.y >= 0.f ? 1 : -1;
    }

    // A walk of the whole road at kWalkYdS (one leg), ms.
    inline std::uint32_t LegMs()
    {
        return static_cast<std::uint32_t>(std::lround(RoadLength() / kWalkYdS * 1000.f));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO3 Rampage: the lane plan and the lane test
    // ----------------------------------------------------------------------------------------------------------------

    struct RampagePlan
    {
        int dir = 1;            // the walk direction after the surge (turned when the road ran out ahead)
        float fromS = 0.f;
        float toS = 0.f;        // the surge's end, on the road
        float length = 0.f;     // the lane (and the surge): kRampageLengthYd, or what is left of the road
        bool turned = false;
    };

    // The lane from `s` walking `dir`: 20 yd ahead, clipped at the road's end; with less than kRampageMinLaneYd left
    // he turns round first, so a lane is never a stub (the road is 61.8 yd: the other way always has 20).
    inline RampagePlan PlanRampage(float s, int dir)
    {
        RampagePlan p;
        p.fromS = std::clamp(s, 0.f, RoadLength());
        p.dir = dir > 0 ? 1 : -1;
        if (RoadAhead(p.fromS, p.dir) < kRampageMinLaneYd)
        {
            p.dir = -p.dir;
            p.turned = true;
        }
        p.length = std::min(kRampageLengthYd, RoadAhead(p.fromS, p.dir));
        p.toS = p.fromS + p.length * static_cast<float>(p.dir);
        return p;
    }

    // Is `p` inside the lane from `origin` along `facing` (radians), `length` long and `width` wide (plus `margin` on
    // each side and at both ends: a unit's body)?
    inline bool InLane(Vec2 origin, float facing, float length, float width, Vec2 p, float margin = 0.f)
    {
        float const fx = std::cos(facing);
        float const fy = std::sin(facing);
        float const dx = p.x - origin.x;
        float const dy = p.y - origin.y;
        float const along = dx * fx + dy * fy;
        float const across = -dx * fy + dy * fx;
        return along >= -margin && along <= length + margin && std::fabs(across) <= width / 2.f + margin;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // RO2 Underfoot, RO4 the waves, the merge heal, RO6's cadence
    // ----------------------------------------------------------------------------------------------------------------

    // A tick on a Dark Iron of `maxHealth`: 10% of it, at least 1.
    inline std::uint32_t UnderfootDamage(std::uint32_t maxHealth)
    {
        return std::max<std::uint32_t>(1u, static_cast<std::uint32_t>(std::lround(maxHealth * kUnderfootPct / 100.f)));
    }

    // Is a unit at `p` (height `z`) under his feet at `boss` (height `bossZ`)?
    inline bool InUnderfoot(Vec2 boss, float bossZ, Vec2 p, float z)
    {
        return DungeonKit::Distance(boss, p) <= kUnderfootYd && std::fabs(z - bossZ) <= kUnderfootZYd;
    }

    // Heroic: the heal of one merge on a Roccor of `maxHealth`.
    inline std::uint32_t MergeHeal(std::uint32_t maxHealth)
    {
        return static_cast<std::uint32_t>(std::lround(maxHealth * kMergeHealPct / 100.f));
    }

    // RO4: how many of a wave rise with `alive` already up (the two-wave cap).
    inline std::uint32_t LoosedToRaise(bool heroic, std::uint32_t alive)
    {
        std::uint32_t const cap = kLoosedCap(heroic);
        return alive >= cap ? 0u : std::min(kLoosedPerWave(heroic), cap - alive);
    }

    // RO6: the next Flame Shock's delay from a [0, 1] roll.
    inline std::uint32_t FlameShockDelay(float roll01)
    {
        float const r = std::clamp(roll01, 0.f, 1.f);
        return kFlameShockMinMs
            + static_cast<std::uint32_t>(r * static_cast<float>(kFlameShockMaxMs - kFlameShockMinMs));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas
    // ----------------------------------------------------------------------------------------------------------------

    // A strip along the road from s `sMin` to `sMax`, `halfWidth` either side, heights [zMin, zMax].
    inline Arena RoadStrip(float sMin, float sMax, float halfWidth, float zMin, float zMax)
    {
        return Arena(BlackrockDepthsRework::StripRegion(kRoadWest.XY(), RoadAxis(), sMin, sMax, halfWidth, zMin,
            zMax));
    }

    // The fight's leash frame: within kRoadLeashYd of the road (a box round the segment: its corners reach a little
    // past 40 yd), on the road's floor band. The Ring of Law above (z -54 and up) and Grebmar's cavern (88 yd off the
    // line) stay out. He never leaves it himself (he walks the road), so only the no-target timer acts.
    inline Arena RoadArena()
    {
        return RoadStrip(-kRoadLeashYd, RoadLength() + kRoadLeashYd, kRoadLeashYd, -95.f, -68.f);
    }

    // Where Flung Boulders may land: the road's floor 16 yd either side (the probe keeps them on the mesh).
    inline Arena BoulderFloor()
    {
        return RoadStrip(-12.f, RoadLength() + 12.f, 16.f, -90.f, -74.f);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Leash judge (G1's walk row)
    // ----------------------------------------------------------------------------------------------------------------

    // The ledger tag a member `distYd` from him earns this tick (0: none). The tank is judged on 8 yd (unless the surge
    // grace runs), everyone on 40 yd; a tank past 40 yd earns the wider one.
    inline std::uint32_t LeashTag(float distYd, bool tank, bool tankGrace)
    {
        if (distYd > kRangeLeashYd)
            return TAG_RANGE_LEASH;
        if (tank && !tankGrace && distYd > kTankLeashYd)
            return TAG_TANK_LEASH;
        return 0;
    }
}

#endif
