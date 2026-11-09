/*
 * mod-dungeon-bosses, Shadowfang Keep: Deathsworn Captain (WP-S6), the pure, host-testable part (no engine headers):
 * spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: SK 1044-1083 (build spec),
 * SK 956-1043 (design), DC1-DC5; handoff section 3.5 rows DC, section 3.6 row S6, section 7 #14 and #25.
 *
 * Conventions (ShadowfangKeepRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum
 * (apps/dbc-tools source/npcs/shadowfang_keep/deathsworn_captain.py declares the same ids); tuning numbers as
 * `inline constexpr DungeonKit::NH<T> kName{ normal, heroic };`. The damage percents are the same on both
 * difficulties: the reference row (normal 1,300 / heroic 4,120) makes the difference.
 *
 * Random picks take a `pick(n)` callable that returns a uniform index in [0, n) (the script passes urand, the tests a
 * fixed sequence), so every rule here runs on the host.
 *
 * The arena (handoff section 7 #25): the north hall plus his walkway (ShadowfangKeepRework.h
 * DeathswornCaptainArena(): region 0 the hall, region 1 the walkway, region 2 Odo's ESE alcove behind the door he
 * turns in). A charge that starts on the walkway runs only along it (the walkway's long axis, toward the side its
 * target is on); every charge line stops short of the arena's edge, so he never charges off the walkway's 16-20 yd
 * drop. The alcove is its own pocket: a charge that starts in it stays in it, a charge from the hall or the walkway
 * never enters it (the wall between them has only the 3.4 yd door).
 */

#ifndef MOD_DUNGEON_BOSSES_SFK_DEATHSWORNCAPTAIN_LOGIC_H
#define MOD_DUNGEON_BOSSES_SFK_DEATHSWORNCAPTAIN_LOGIC_H

#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "ShadowfangKeepRework.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace DeathswornCaptain
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using ShadowfangKeepRework::Point3;

    // This boss's spell slice (handoff section 3.4).
    inline constexpr ShadowfangKeepRework::IdSlice kSlice = ShadowfangKeepRework::kSpellsDeathswornCaptain;

    // Declared in apps/dbc-tools source/npcs/shadowfang_keep/deathsworn_captain.py. The registry owns every avoidable
    // hit (through the named resolve copies); the tank's Sweeping Cleave and Last Stand are the script's own casts.
    enum DeathswornCaptainSpells : std::uint32_t
    {
        SPELL_CAPTAIN_CHARGE_BAR        = 206010,   // DC1 cast bar, 2 s (no effect)
        SPELL_CAPTAIN_CHARGE_TRAIL      = 206011,   // DC2 the dash look on himself (DC1: the bar's own visual)
        SPELL_CAPTAIN_CHARGE_HIT        = 206012,   // DC1 / DC2 resolve copy, Physical (the registry's 35%)
        SPELL_CAPTAIN_CLEAVE_BAR        = 206013,   // DC3 cast bar, 2 s (no effect)
        SPELL_CAPTAIN_CLEAVE_HIT        = 206014,   // DC3 resolve copy, Physical (the registry's 40%, non-tanks)
        SPELL_CAPTAIN_CLEAVE_TANK       = 206015,   // DC3 the tank's two swings (spell_sfk_captain_cleave_tank)
        SPELL_CAPTAIN_LAST_STAND        = 206016,   // DC4 heroic: +30% attack speed for the rest of the fight
    };
    static_assert(kSlice.Contains(SPELL_CAPTAIN_CHARGE_BAR) && kSlice.Contains(SPELL_CAPTAIN_LAST_STAND),
        "the Deathsworn Captain's spells stay inside his slice");

    // Registry tags (the failure ledger): the build spec ids.
    enum DeathswornCaptainTags : std::uint32_t
    {
        TAG_DEATHSWORN_CHARGE   = 1,    // DC1
        TAG_CHAIN_CHARGE        = 2,    // DC2 (heroic)
        TAG_SWEEPING_CLEAVE     = 3,    // DC3
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (build spec DC1-DC4; damage in % of the reference row, times in ms)
    // ----------------------------------------------------------------------------------------------------------------

    // DC1 Deathsworn Charge / DC2 Chain Charge: a 3 yd line from him to a random non-tank at least 8 yd away, 5 yd past
    // the target, the first 4 yd excluded; 2 s marker (DC2: 1.5 s, from DC1's landing spot), 35% + Weakened.
    inline constexpr float kChargeWidth = 3.f;
    inline constexpr float kChargeOverrun = 5.f;
    inline constexpr float kChargeExclude = 4.f;
    inline constexpr float kChargeMinDistance = 8.f;
    inline constexpr float kChargePct = 35.f;
    inline constexpr std::uint32_t kChargeWarnMs = 2000;
    inline constexpr std::uint32_t kChainWarnMs = 1500;
    inline constexpr std::uint32_t kChargeFirstMs = 8000;
    inline constexpr std::uint32_t kChargeEveryMs = 15000;
    inline constexpr NH<std::uint8_t> kChargeLegs{ 1, 2 };     // DC1, then DC2 on heroic
    inline constexpr float kChargeSpeed = 42.f;                 // SPEED_CHARGE
    // A line stops this far short of the arena's edge (the arena boxes sit about 0.75 yd past the navmesh, which sits
    // about 0.5 yd inside the walls): his landing spot stays on the floor, never over the walkway's drop.
    inline constexpr float kChargeEdgeInset = 1.5f;
    // A line no longer than the excluded part can hit nobody: the leg is skipped.
    inline constexpr float kChargeMinLength = kChargeExclude + 1.f;
    inline constexpr std::uint32_t kReturnDelayMs = 1000;      // after the last landing: back to the tank

    // DC3 Sweeping Cleave: 2 s cast, cone 90 degrees, 10 yd in front of him; non-tanks 40% + Weakened, the tank two
    // swings. Never within 4 s after the last charge lands.
    inline constexpr float kCleaveAngle = 90.f;
    inline constexpr float kCleaveLength = 10.f;
    inline constexpr float kCleavePct = 40.f;
    inline constexpr std::uint32_t kCleaveWarnMs = 2000;
    inline constexpr std::uint32_t kCleaveFirstMs = 5000;
    inline constexpr std::uint32_t kCleaveEveryMs = 12000;
    inline constexpr std::uint32_t kCleaveAfterChargeMs = 4000;
    inline constexpr std::uint32_t kCleaveTankSwings = 2;

    // DC4 Last Stand (heroic): below 30% health, +30% attack speed (the spell's aura) for the rest of the fight.
    inline constexpr NH<bool> kLastStand{ false, true };
    inline constexpr std::uint32_t kLastStandHealthPct = 30;
    inline constexpr std::uint32_t kLastStandHastePct = 30;     // deathsworn_captain.py declares the same value
    inline constexpr std::uint32_t kHealthCheckMs = 500;

    // An ability that comes due while he is busy (a charge, a cleave cast) waits this long and tries again.
    inline constexpr std::uint32_t kBusyRetryMs = 1000;

    // ArenaGuard (handoff section 7 #25): the kit defaults (1.5 s grace, 3 s cooldown), Greenskin's jump.
    inline constexpr float kGripJumpSpeedXY = 25.f;
    inline constexpr float kGripMinSpeedZ = 8.f;

    // ----------------------------------------------------------------------------------------------------------------
    // Timings
    // ----------------------------------------------------------------------------------------------------------------

    // How long a charge of `length` yd takes at `speed` (rounded up, at least 1 ms for a non-zero length).
    inline std::uint32_t ChargeTravelMs(float length, float speed = kChargeSpeed)
    {
        if (length <= 0.f || speed <= 0.f)
            return 0;
        return std::max<std::uint32_t>(1, static_cast<std::uint32_t>(std::ceil(length / speed * 1000.f)));
    }

    // From the first marker to the last leg's resolve (his last dash starts there).
    inline constexpr std::uint32_t ChargeChainMs(std::uint8_t legs)
    {
        return legs == 0 ? 0 : kChargeWarnMs + (legs - 1u) * kChainWarnMs;
    }

    // DC3's guard: how long Sweeping Cleave must still wait at `nowMs` (0: it may go now). While a charge runs it
    // retries in kBusyRetryMs; after the last landing (`lastLandMs`, on the same clock) it waits out
    // kCleaveAfterChargeMs.
    inline std::uint32_t CleaveWaitMs(std::uint32_t nowMs, bool charging, std::optional<std::uint32_t> lastLandMs)
    {
        if (charging)
            return kBusyRetryMs;
        if (lastLandMs)
        {
            std::uint32_t const freeAt = *lastLandMs + kCleaveAfterChargeMs;
            if (nowMs < freeAt)
                return freeAt - nowMs;
        }
        return 0;
    }

    // DC4: due once, on heroic, below kLastStandHealthPct.
    inline constexpr bool LastStandDue(bool heroic, float healthPct, bool alreadyUp)
    {
        return kLastStand(heroic) && !alreadyUp && healthPct < static_cast<float>(kLastStandHealthPct);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Target picks
    // ----------------------------------------------------------------------------------------------------------------

    // A non-tank player a pick may choose: an opaque id (the raw guid) and where it stands.
    struct ChargeCandidate
    {
        std::uint64_t id = 0;
        Vec2 pos;
    };

    // One leg's target (handoff section 3.5 DC; the Deadmines G8 drill's `pick=other` rule, as Mr. Smite's
    // PickDashTarget in MrSmiteLogic.h):
    //   1. a candidate not yet in `chain`, at least `minDistance` from `from`, at random;
    //   2. else the farthest candidate not yet in `chain`;
    //   3. else (everyone is in the chain) a candidate other than the chain's last pick, at random;
    //   4. else the only candidate; none when there are no candidates.
    // Returns the index into `candidates`.
    template <typename Pick>
    std::optional<std::size_t> PickChargeTarget(std::vector<ChargeCandidate> const& candidates, Vec2 from,
        std::vector<std::uint64_t> const& chain, float minDistance, Pick&& pick)
    {
        if (candidates.empty())
            return std::nullopt;

        auto inChain = [&chain](std::uint64_t id)
        {
            return std::find(chain.begin(), chain.end(), id) != chain.end();
        };

        std::vector<std::size_t> far;
        std::optional<std::size_t> farthest;
        float farthestDist = -1.f;
        for (std::size_t i = 0; i < candidates.size(); ++i)
        {
            if (inChain(candidates[i].id))
                continue;
            float const d = DungeonKit::Distance(from, candidates[i].pos);
            if (d >= minDistance)
                far.push_back(i);
            if (d > farthestDist)
            {
                farthestDist = d;
                farthest = i;
            }
        }
        if (!far.empty())
            return far[pick(far.size()) % far.size()];
        if (farthest)
            return farthest;

        std::vector<std::size_t> others;
        std::uint64_t const last = chain.empty() ? 0 : chain.back();
        for (std::size_t i = 0; i < candidates.size(); ++i)
            if (candidates[i].id != last)
                others.push_back(i);
        if (!others.empty())
            return others[pick(others.size()) % others.size()];
        return std::size_t(0);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry: the hall, the walkway and the charge lines
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::size_t kHallRegion = 0;       // DeathswornCaptainArena(): the north hall
    inline constexpr std::size_t kWalkwayRegion = 1;    // ... then the walkway
    inline constexpr std::size_t kOdoAlcoveRegion = 2;  // ... then Odo's ESE alcove, behind the door he turns in

    // On the walkway proper: inside its region and not in the hall (the two overlap where the walkway meets the hall).
    // Plane only: both are one floor (the arena's z bands hold the heights).
    inline bool OnWalkway(Arena const& arena, Vec2 p)
    {
        if (arena.regions.size() <= kWalkwayRegion)
            return false;
        return arena.regions[kWalkwayRegion].ContainsPlane(p) && !arena.regions[kHallRegion].ContainsPlane(p);
    }

    // The walkway's long axis (a WoW orientation, toward the hall) and a point's position along it (frame X: the
    // report's `v`, growing toward the hall).
    inline float WalkwayAxis(Arena const& arena)
    {
        return arena.regions[kWalkwayRegion].frame.angle;
    }

    inline float AlongWalkway(Arena const& arena, Vec2 p)
    {
        return DungeonKit::ToFrame(arena.regions[kWalkwayRegion].frame, p).x;
    }

    // In Odo's alcove proper: inside its region and on neither the walkway nor the hall (the walkway's end overlaps the
    // alcove's door line by 0.75 yd; that strip counts as walkway).
    inline bool InOdoAlcove(Arena const& arena, Vec2 p)
    {
        if (arena.regions.size() <= kOdoAlcoveRegion)
            return false;
        return arena.regions[kOdoAlcoveRegion].ContainsPlane(p) && !OnWalkway(arena, p)
            && !arena.regions[kHallRegion].ContainsPlane(p);
    }

    // How far a ray from `from` along `facing` stays on the charge's floor plan (plane only), up to `maxLen`, in `step`
    // yd steps; 0 when `from` itself is off it. The floor plan is the alcove alone for a ray from inside it, else the
    // hall plus the walkway (the wall beside Odo's door would let a line cross from one to the other).
    inline float CaptainRayInside(Arena const& arena, Vec2 from, float facing, float maxLen, float step = 0.25f)
    {
        bool const alcove = InOdoAlcove(arena, from);
        auto onFloor = [&arena, alcove](Vec2 p)
        {
            for (std::size_t i = 0; i < arena.regions.size(); ++i)
                if ((i == kOdoAlcoveRegion) == alcove && arena.regions[i].ContainsPlane(p))
                    return true;
            return false;
        };
        if (!onFloor(from))
            return 0.f;
        float d = 0.f;
        while (d + step <= maxLen && onFloor(DungeonKit::Advance(from, facing, d + step)))
            d += step;
        return d;
    }

    struct ChargePath
    {
        Vec2 from;
        Vec2 end;
        float facing = 0.f;
        float length = 0.f;
        bool alongWalkway = false;  // started on the walkway: snapped to its axis
        bool clipped = false;       // the arena's edge stopped it short of target + overrun
    };

    // One charge leg from `from` toward `target`: kChargeOverrun past the target, never shorter than
    // kChargeMinDistance + kChargeOverrun (a near target still gets the full line through it). On the walkway the line
    // runs along the walkway's axis, toward the side the target is on (its distance counted along the axis). The line
    // stops kChargeEdgeInset short of the arena's edge. A target on top of the source keeps `fallbackFacing` (on the
    // walkway: the axis direction nearer to it).
    inline ChargePath ChargeLine(Arena const& arena, Vec2 from, Vec2 target, float fallbackFacing)
    {
        ChargePath path;
        path.from = from;
        float wanted = 0.f;
        if (OnWalkway(arena, from))
        {
            path.alongWalkway = true;
            float const axis = WalkwayAxis(arena);
            float const delta = AlongWalkway(arena, target) - AlongWalkway(arena, from);
            bool toHall = delta > 0.f;
            if (std::fabs(delta) <= 0.01f)
                toHall = std::cos(fallbackFacing - axis) >= 0.f;
            float facing = toHall ? axis : axis + DungeonKit::kPi;
            while (facing < 0.f)
                facing += DungeonKit::kTwoPi;
            while (facing >= DungeonKit::kTwoPi)
                facing -= DungeonKit::kTwoPi;
            path.facing = facing;
            wanted = std::max(std::fabs(delta), kChargeMinDistance) + kChargeOverrun;
        }
        else
        {
            float const dist = DungeonKit::Distance(from, target);
            path.facing = dist > 0.01f ? DungeonKit::BearingTo(from, target) : fallbackFacing;
            wanted = std::max(dist, kChargeMinDistance) + kChargeOverrun;
        }
        float const inside = CaptainRayInside(arena, from, path.facing, wanted + kChargeEdgeInset + 1.f);
        float const limit = std::max(0.f, inside - kChargeEdgeInset);
        path.length = std::min(wanted, limit);
        path.clipped = limit < wanted;
        path.end = DungeonKit::Advance(from, path.facing, path.length);
        return path;
    }

    // The line passes level with `target`: its projection on the line falls on the hitting part (past the excluded
    // kChargeExclude yd, before the end). Off to the side does not count against it (a walkway line runs along the
    // walkway; the target may already stand beside it).
    inline bool ChargeReaches(ChargePath const& path, Vec2 target)
    {
        float const along = (target.x - path.from.x) * std::cos(path.facing)
            + (target.y - path.from.y) * std::sin(path.facing);
        return along >= kChargeExclude && along <= path.length;
    }

    // PickChargeTarget, but first among the candidates the leg's line would reach (`reaches[i]`, ChargeReaches for
    // candidate i): a random one not yet in `chain` and at least `minDistance` from `from`. Without one, the plain
    // rule. So a player the wall or the walkway would cut the line short of is picked only when nobody else fits.
    template <typename Pick>
    std::optional<std::size_t> PickReachableChargeTarget(std::vector<ChargeCandidate> const& candidates, Vec2 from,
        std::vector<std::uint64_t> const& chain, float minDistance, std::vector<bool> const& reaches, Pick&& pick)
    {
        std::vector<std::size_t> good;
        for (std::size_t i = 0; i < candidates.size() && i < reaches.size(); ++i)
            if (reaches[i] && std::find(chain.begin(), chain.end(), candidates[i].id) == chain.end()
                && DungeonKit::Distance(from, candidates[i].pos) >= minDistance)
                good.push_back(i);
        if (!good.empty())
            return good[pick(good.size()) % good.size()];
        return PickChargeTarget(candidates, from, chain, minDistance, pick);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The patrol (path 1345170, DB exact) and the grip landing
    // ----------------------------------------------------------------------------------------------------------------

    // Out and back over the north hall and the walkway; he turns in Odo's doorway (point 5).
    inline std::array<Point3, 10> constexpr kPatrol{ {
        { -191.946f, 2124.68f, 97.3899f }, { -203.288f, 2100.47f, 97.3899f }, { -213.781f, 2097.97f, 97.3899f },
        { -239.866f, 2108.05f, 97.3899f }, { -245.81f, 2110.46f, 100.031f }, { -239.837f, 2107.84f, 97.39f },
        { -212.154f, 2097.46f, 97.39f }, { -202.219f, 2102.72f, 97.39f }, { -187.112f, 2133.9f, 97.39f },
        { -189.958f, 2128.48f, 97.39f } } };

    // R2 S-2 (orchestrator call): while Odo fights (IN_PROGRESS) he holds his patrol short of Odo's doorway, passive
    // and immune to players, so a bell ringer or a hunted player never pulls him into Odo's fight. He holds where he
    // stands, or walks back to patrol point 4 (the last one before the doorway) from the stretch past it.
    constexpr bool HoldForOdo(std::uint32_t odoState)
    {
        return odoState == DungeonKit::State::InProgress;
    }

    inline constexpr std::size_t kOdoHoldPatrolIndex = 3;      // patrol point 4 (-239.9, 2108.1), 7.9 yd from the door

    inline Point3 OdoHoldPoint()
    {
        return kPatrol[kOdoHoldPatrolIndex];
    }

    // He is nearer Odo's door than the hold point: walk back to it.
    inline bool HoldWalksBack(Vec2 at)
    {
        Vec2 const door = ShadowfangKeepRework::kOdoDoor.XY();
        return DungeonKit::Distance(at, door) < DungeonKit::Distance(OdoHoldPoint().XY(), door);
    }

    // Where ArenaGuard lands a gripped unit (a fall into the inner yard, a step past the alcove toward Odo): the
    // nearest point of his patrol line (the floor he walks, so never over the drop), its height interpolated along the
    // leg.
    inline Point3 PatrolLanding(Vec2 p)
    {
        Point3 best = kPatrol[0];
        float bestDist = -1.f;
        for (std::size_t i = 0; i < kPatrol.size(); ++i)
        {
            Point3 const a = kPatrol[i];
            Point3 const b = kPatrol[(i + 1) % kPatrol.size()];
            float along = 0.f;
            float const d = DungeonKit::SegmentDistance(a.XY(), b.XY(), p, &along);
            if (bestDist < 0.f || d < bestDist)
            {
                bestDist = d;
                float const len = DungeonKit::Distance(a.XY(), b.XY());
                float const t = len > 0.f ? std::clamp(along / len, 0.f, 1.f) : 0.f;
                best = { a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t };
            }
        }
        return best;
    }
}

#endif
