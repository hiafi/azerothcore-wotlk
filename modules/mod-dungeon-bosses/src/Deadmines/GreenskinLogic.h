/*
 * mod-dungeon-bosses, Deadmines: Captain Greenskin and the harpoon rope (WP-B7), the pure, host-testable part (no
 * engine headers): spell ids, per-difficulty tuning numbers, timers, target picks and geometry. Build spec: DM 'Captain
 * Greenskin' Build spec GS1-GS5.
 *
 * Conventions (DeadminesRework.h): spell ids only inside the slice below, as `SPELL_...` entries of the enum; tuning
 * numbers as `inline constexpr DeadminesKit::NH<T> kName{ normal, heroic };`.
 *
 * The lane volley (LaneVolley, kFireOnMyMark, the deck frame math) is shared with VanCleef's "The guns" (VC3, WP-B8):
 * B8 builds its own LaneVolley and fires it with GreenskinLanes::Fire (GreenskinLanes.h).
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_GREENSKIN_LOGIC_H
#define MOD_DUNGEON_BOSSES_DEADMINES_GREENSKIN_LOGIC_H

#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <unordered_map>
#include <utility>
#include <vector>

namespace Greenskin
{
    using DeadminesKit::NH;
    using DeadminesKit::Vec2;

    // This boss's spell slice (handoff section 3.3).
    inline constexpr DeadminesRework::IdSlice kSlice = DeadminesRework::kSpellsGreenskin;

    // Declared in apps/dbc-tools source/npcs/deadmines/captain_greenskin.py.
    enum GreenskinSpells : std::uint32_t
    {
        SPELL_FIRE_ON_MY_MARK_HIT   = 205340,   // GS2 lane hit: resolve copy (Physical), + spell_dm_greenskin_lane_hit
        SPELL_CROSSFIRE_HIT         = 205341,   // GS3 bow-to-stern lane hit: resolve copy (Physical), same scripts
        SPELL_BURNING_DECK          = 205342,   // GS4 crossing tick: resolve copy (Fire)
        SPELL_FIRE_ON_MY_MARK_CAST  = 205343,   // GS2 cast bar, 2 s, no effect, not interruptible
        SPELL_CROSSFIRE_CAST        = 205344,   // GS2 + GS3 heroic cast bar, 2.5 s, no effect, not interruptible
        SPELL_REEL_EM_IN            = 205345,   // GS5 cast: 2 s, interruptible, the harpoon throw (stock 5208's hit)
        SPELL_HARPOONED             = 205346,   // GS5 rope: channeled beam from the rope anchor, the target's debuff
        SPELL_REEL_HIT              = 205347,   // GS5 reel: resolve copy (Physical) of the RunOut's 30%
        SPELL_GRAPPLING_HOOK        = 205348,   // playtest 1: the grip onto the deck (Death Grip's look, no effect)
        // 205349-205359 spare
    };

    // The invisible unit the rope beam is channeled from (it follows Greenskin): creature 300425, the handoff's
    // "harpoon rope unit" slot. A stand-in until DeadminesRework.h names it (report: requests for the orchestrator).
    inline constexpr std::uint32_t kNpcRopeAnchor = DeadminesRework::NPC_DM_HARPOON_ROPE_ANCHOR;

    // Registry tags (the build spec's mechanic ids).
    enum GreenskinTags : std::uint32_t
    {
        TAG_FIRE_ON_MY_MARK     = 2,    // GS2
        TAG_CROSSFIRE           = 3,    // GS3
        TAG_BURNING_CROSSING    = 4,    // GS4
        TAG_REEL_EM_IN          = 5,    // GS5
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kCleaveFirstMinMs = 1000;    // GS1: 1 to 7 s, then 10 to 15 s (stock)
    inline constexpr std::uint32_t kCleaveFirstMaxMs = 7000;
    inline constexpr std::uint32_t kCleaveMinMs = 10000;
    inline constexpr std::uint32_t kCleaveMaxMs = 15000;
    inline constexpr std::uint32_t kFireFirstMs = 8000;         // GS2: first at 8 s, then every 20 s
    inline constexpr std::uint32_t kFireEveryMs = 20000;
    inline constexpr std::uint32_t kReelFirstMs = 12000;        // GS5: first at 12 s, then every 20 s
    inline constexpr std::uint32_t kReelEveryMs = 20000;
    inline constexpr std::uint32_t kReelCastMs = 2000;          // SPELL_REEL_EM_IN's cast (stock 5208's 2 s)
    inline constexpr std::uint32_t kRopeMs = 4000;              // the rope holds 4 s, then he reels
    inline constexpr std::uint32_t kRopeCleanupMs = 1500;       // after the reel resolves: drop what is left
    inline constexpr std::uint32_t kRetryNoTargetMs = 5000;     // no harpoon target: try again soon
    inline constexpr std::uint32_t kReelYellCooldownMs = 3000;  // two ropes reeled together: one yell

    // ----------------------------------------------------------------------------------------------------------------
    // GS2-GS4: the lane volley on the deck frame (shared with VanCleef's VC3)
    // ----------------------------------------------------------------------------------------------------------------

    // One volley. `across` lanes run rail to rail (mod-boss-mechanics Axis::Y of the deck frame; their offsets spread
    // along the deck), `along` lanes run bow to stern (Axis::X). Crossing cells burn only when both are present.
    struct LaneVolley
    {
        std::uint32_t across = 0;
        std::uint32_t along = 0;
        float width = 4.f;              // yd
        float minGap = 6.f;             // yd between neighbouring lanes of one axis
        std::uint32_t warnMs = 2000;    // marker time, both axes
        float lanePct = 40.f;           // % of reference non-tank health per lane hit, plus 1 Weakened
        bool burnCrossings = false;
        std::uint32_t burnMs = 20000;
        std::uint32_t burnTickMs = 1000;
        float burnPct = 10.f;           // per tick, Fire
        std::uint32_t acrossTag = TAG_FIRE_ON_MY_MARK;
        std::uint32_t alongTag = TAG_CROSSFIRE;
        std::uint32_t cellTag = TAG_BURNING_CROSSING;

        constexpr std::uint32_t Lanes() const { return across + along; }
        constexpr std::uint32_t Crossings() const { return burnCrossings && across && along ? across * along : 0; }
    };

    // GS2 (normal): 4 lanes across, 2 s. GS2 + GS3 + GS4 (heroic): 4 across and 2 bow to stern, 2.5 s, and the 8
    // crossings burn 20 s at 10% Fire per second.
    inline constexpr NH<LaneVolley> kFireOnMyMark{
        LaneVolley{ 4, 0, 4.f, 6.f, 2000, 40.f, false, 20000, 1000, 10.f, TAG_FIRE_ON_MY_MARK, TAG_CROSSFIRE,
            TAG_BURNING_CROSSING },
        LaneVolley{ 4, 2, 4.f, 6.f, 2500, 40.f, true, 20000, 1000, 10.f, TAG_FIRE_ON_MY_MARK, TAG_CROSSFIRE,
            TAG_BURNING_CROSSING },
    };

    // A player in two lanes of one volley (a crossing) is hit once (ruling 15): hits from the same owner within this
    // window count as one volley. Every lane of a volley resolves on the same registry tick; volleys are 20 s apart.
    inline constexpr std::uint64_t kVolleyWindowMs = 1000;

    // The deck as a rectangle frame (mod-boss-mechanics' RoomFrame math: origin a corner, X along `angle` for sizeX,
    // Y along angle + 90 degrees for sizeY).
    struct FrameRect
    {
        Vec2 origin;
        float angle = 0.f;
        float sizeX = 0.f;
        float sizeY = 0.f;
    };

    inline constexpr FrameRect kDeck{ DeadminesRework::kDeckOrigin, DeadminesRework::kDeckAngle,
        DeadminesRework::kDeckLength, DeadminesRework::kDeckWidth };

    inline Vec2 FramePoint(FrameRect const& f, float fx, float fy)
    {
        float const c = std::cos(f.angle);
        float const s = std::sin(f.angle);
        return { f.origin.x + c * fx - s * fy, f.origin.y + s * fx + c * fy };
    }

    // A map point in frame coordinates (x along X, y along Y).
    inline Vec2 ToFrame(FrameRect const& f, Vec2 p)
    {
        float const c = std::cos(f.angle);
        float const s = std::sin(f.angle);
        float const dx = p.x - f.origin.x;
        float const dy = p.y - f.origin.y;
        return { c * dx + s * dy, -s * dx + c * dy };
    }

    inline bool InsideFrame(FrameRect const& f, Vec2 p, float eps = 0.01f)
    {
        Vec2 const q = ToFrame(f, p);
        return q.x >= -eps && q.x <= f.sizeX + eps && q.y >= -eps && q.y <= f.sizeY + eps;
    }

    enum class LaneAxis : std::uint8_t
    {
        Along,      // bow to stern: Axis::X (runs sizeX, offsets across sizeY)
        Across      // rail to rail: Axis::Y (runs sizeY, offsets across sizeX)
    };

    // The span the lane offsets of `axis` spread over.
    inline float SpanFor(FrameRect const& f, LaneAxis axis)
    {
        return axis == LaneAxis::Along ? f.sizeY : f.sizeX;
    }

    // `count` lanes of `width` with gaps >= minGap fit across `span` (else the registry spaces them evenly and warns).
    inline bool LanesFit(float span, std::uint32_t count, float width, float minGap)
    {
        if (count == 0)
            return true;
        return count * width + (count - 1) * minGap <= span + 1e-4f;
    }

    // A lane's centreline on the map (mod-boss-mechanics PlaceLane): `offset` is its low edge across the axis.
    struct LaneSegment
    {
        Vec2 from;
        Vec2 to;
        float width = 0.f;
    };

    inline LaneSegment LaneOnFrame(FrameRect const& f, LaneAxis axis, float offset, float width)
    {
        float const mid = offset + width * 0.5f;
        if (axis == LaneAxis::Along)
            return { FramePoint(f, 0.f, mid), FramePoint(f, f.sizeX, mid), width };
        return { FramePoint(f, mid, 0.f), FramePoint(f, mid, f.sizeY), width };
    }

    // Who a volley already hit (the once-per-volley rule at crossings). Keys are raw guids.
    class VolleyMemory
    {
    public:
        bool AlreadyHit(std::uint64_t owner, std::uint64_t unit, std::uint64_t nowMs) const
        {
            auto const it = _byOwner.find(owner);
            if (it == _byOwner.end() || nowMs - it->second.startMs > kVolleyWindowMs)
                return false;
            std::vector<std::uint64_t> const& hit = it->second.hit;
            return std::find(hit.begin(), hit.end(), unit) != hit.end();
        }

        void Record(std::uint64_t owner, std::uint64_t unit, std::uint64_t nowMs)
        {
            Entry& e = _byOwner[owner];
            if (e.hit.empty() || nowMs - e.startMs > kVolleyWindowMs)
            {
                e.startMs = nowMs;
                e.hit.clear();
            }
            if (std::find(e.hit.begin(), e.hit.end(), unit) == e.hit.end())
                e.hit.push_back(unit);
        }

        void Forget(std::uint64_t owner)
        {
            _byOwner.erase(owner);
        }

        std::size_t Owners() const { return _byOwner.size(); }

    private:
        struct Entry
        {
            std::uint64_t startMs = 0;
            std::vector<std::uint64_t> hit;
        };

        std::unordered_map<std::uint64_t, Entry> _byOwner;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // GS5: Reel 'Em In
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<std::uint32_t> kHarpoonCount{ 1, 2 };     // two at once on heroic, on different players
    inline constexpr NH<float> kReelPct{ 30.f, 30.f };            // reeled: % of reference non-tank health + Weakened
    inline constexpr float kHarpoonMinYd = 10.f;                  // a random non-tank at least 10 yd away
    inline constexpr float kHarpoonMaxYd = 40.f;                  // SPELL_REEL_EM_IN's range
    inline constexpr float kSnapYd = 25.f;                        // the target snaps the rope at 25 yd from him
    inline constexpr float kRopeStandYd = 1.25f;                  // "standing on the rope": this close to it
    inline constexpr float kRopeBossClearYd = 5.f;                // the part next to him does not count (the tank)
    inline constexpr float kRopeTargetClearYd = 1.5f;             // nor the target's own end
    inline constexpr std::uint32_t kRopeCutMs = 1000;             // standing on it 1 s cuts it
    inline constexpr float kRopeObjectDriftYd = 3.f;              // the click object follows the midpoint
    inline constexpr float kReelFrontYd = 2.5f;                   // reeled to his feet, in front of him

    struct HarpoonCandidate
    {
        std::uint64_t id = 0;
        float distance = 0.f;
        bool tank = false;
    };

    // Up to `count` different non-tanks: first from those kHarpoonMinYd to kHarpoonMaxYd away, then (when too few)
    // from the closer ones. Never the tank, never past the cast's range. `rand(n)` returns [0, n).
    template <class Rand>
    std::vector<std::uint64_t> PickHarpoonTargets(std::vector<HarpoonCandidate> const& candidates, std::uint32_t count,
        Rand&& rand)
    {
        std::vector<std::uint64_t> far;
        std::vector<std::uint64_t> near;
        for (HarpoonCandidate const& c : candidates)
        {
            if (c.tank || c.distance > kHarpoonMaxYd)
                continue;
            (c.distance >= kHarpoonMinYd ? far : near).push_back(c.id);
        }
        std::vector<std::uint64_t> out;
        for (std::vector<std::uint64_t>* pool : { &far, &near })
        {
            while (out.size() < count && !pool->empty())
            {
                std::size_t const i = static_cast<std::size_t>(rand(static_cast<std::uint32_t>(pool->size())))
                    % pool->size();
                out.push_back((*pool)[i]);
                pool->erase(pool->begin() + static_cast<std::ptrdiff_t>(i));
            }
        }
        return out;
    }

    // Distance from p to the segment a-b; `along` (optional) gets the distance from a to p's projection, clamped.
    inline float DistanceToSegment(Vec2 a, Vec2 b, Vec2 p, float* along = nullptr)
    {
        float const dx = b.x - a.x;
        float const dy = b.y - a.y;
        float const len2 = dx * dx + dy * dy;
        float t = 0.f;
        if (len2 > 1e-6f)
            t = std::clamp(((p.x - a.x) * dx + (p.y - a.y) * dy) / len2, 0.f, 1.f);
        if (along)
            *along = t * std::sqrt(len2);
        return DeadminesKit::Distance(p, { a.x + t * dx, a.y + t * dy });
    }

    // `p` stands on the rope from the boss to the target: within kRopeStandYd of it, away from both ends.
    inline bool StandsOnRope(Vec2 boss, Vec2 target, Vec2 p)
    {
        float const len = DeadminesKit::Distance(boss, target);
        if (len <= kRopeBossClearYd + kRopeTargetClearYd)
            return false;
        float along = 0.f;
        float const d = DistanceToSegment(boss, target, p, &along);
        return d <= kRopeStandYd && along >= kRopeBossClearYd && along <= len - kRopeTargetClearYd;
    }

    inline bool RopeSnapped(float targetDistance)
    {
        return targetDistance >= kSnapYd;
    }

    inline Vec2 RopeMidpoint(Vec2 boss, Vec2 target)
    {
        return { (boss.x + target.x) * 0.5f, (boss.y + target.y) * 0.5f };
    }

    inline bool RopeObjectNeedsMove(Vec2 placedAt, Vec2 midpoint)
    {
        return DeadminesKit::Distance(placedAt, midpoint) > kRopeObjectDriftYd;
    }

    inline Vec2 ReelDestination(Vec2 boss, float orientation)
    {
        return DeadminesKit::Advance(boss, orientation, kReelFrontYd);
    }

    // Who has stood on one rope for how long, without a break. Update every candidate each tick; a player off the
    // rope starts again from 0.
    class RopeStanders
    {
    public:
        // True once `id` has stood on the rope kRopeCutMs without a break.
        bool Update(std::uint64_t id, bool onRope, std::uint32_t diffMs)
        {
            auto it = std::find_if(_ms.begin(), _ms.end(), [id](auto const& p) { return p.first == id; });
            if (!onRope)
            {
                if (it != _ms.end())
                    _ms.erase(it);
                return false;
            }
            if (it == _ms.end())
            {
                _ms.emplace_back(id, diffMs);
                return diffMs >= kRopeCutMs;
            }
            it->second += diffMs;
            return it->second >= kRopeCutMs;
        }

        void Clear() { _ms.clear(); }

    private:
        std::vector<std::pair<std::uint64_t, std::uint32_t>> _ms;
    };

    // How a rope ended (the log line, the reel yell).
    enum class RopeEnd : std::uint8_t
    {
        Snapped,    // the target got kSnapYd away
        Stood,      // another player stood on it for kRopeCutMs
        Clicked,    // someone clicked the rope object
        Reeled,     // the RunOut hit: pulled in
        Expired,    // resolved without a reel (the target was out of reach at the end)
        Lost        // the target died or left, or the encounter ended
    };

    inline char const* RopeEndName(RopeEnd end)
    {
        switch (end)
        {
            case RopeEnd::Snapped:
                return "snapped";
            case RopeEnd::Stood:
                return "cut-by-standing";
            case RopeEnd::Clicked:
                return "cut-by-click";
            case RopeEnd::Reeled:
                return "reeled";
            case RopeEnd::Expired:
                return "expired";
            case RopeEnd::Lost:
                return "lost";
        }
        return "?";
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Playtest 1: the fight stays on the ship. Greenskin stands still (no patrol), everyone in combat with him who is
    // off the ship is gripped onto the deck at the pull, anyone who stays off it during the fight for kGripGraceMs is
    // gripped back, and he never follows his victim off it (he holds, and evades if he is ever off it himself).
    // ----------------------------------------------------------------------------------------------------------------

    // "On the ship", in deck frame coordinates (kDeck: x from the sterncastle face toward the bow, y from the west rail
    // toward the east rail), plus a z band. Stern: the side walkways beside the sterncastle reach x -39.2 (frame
    // -14.3); bow: the tip at x -107.5 (frame 54). West: the rail at y -802.5 (the gangplank and the scaffold beyond
    // it, y -800 and west, are off); east: the deck reaches y -840 at x -59..-64 (frame 38), past the 36 yd frame. Each
    // side gets about 1.5 yd past the navmesh edge (the real rail is ~0.5 yd past it). z: the deck runs 37.8 (bow) to
    // 44 (stern walkways); 36 to 48 keeps a jump on the deck and puts the water, the dock, the rigging (44-64, not
    // floor) and the sterncastle top (50-53, not linked) off. Navmesh report section 2.
    inline constexpr float kShipFrameMinX = -16.f;      // map x -37.5
    inline constexpr float kShipFrameMaxX = 56.f;       // map x -109.5
    inline constexpr float kShipFrameMinY = -1.5f;      // map y -800.5
    inline constexpr float kShipFrameMaxY = 40.f;       // map y -842
    inline constexpr float kShipMinZ = 36.f;
    inline constexpr float kShipMaxZ = 48.f;

    inline bool OnShip(Vec2 p, float z)
    {
        if (z < kShipMinZ || z > kShipMaxZ)
            return false;
        Vec2 const q = ToFrame(kDeck, p);
        return q.x >= kShipFrameMinX && q.x <= kShipFrameMaxX && q.y >= kShipFrameMinY && q.y <= kShipFrameMaxY;
    }

    // A unit off the ship this long (continuously) is gripped back. 1.5 s: Greenskin's own kit has no knockback (the
    // reel lands on the deck), so this only forgives a class's own leap or blink over the rail and a stray knockback;
    // someone who jumps overboard is still mid-fall when it fires (a 40 yd drop takes about 2 s).
    inline constexpr std::uint32_t kGripGraceMs = 1500;
    // After a grip the unit is left alone this long (the jump takes about 1 to 2 s; no second grip mid-air).
    inline constexpr std::uint32_t kGripCooldownMs = 3000;
    // How often the script sweeps everyone in combat with him.
    inline constexpr std::uint32_t kGripCheckMs = 250;
    inline constexpr float kGripJumpSpeedXY = 25.f;     // as the reel
    inline constexpr float kGripMinSpeedZ = 8.f;        // a short grip still arcs

    // Where a gripped unit lands: kGripLandYd from Greenskin toward where it was, clamped into the open stern deck
    // (x -56..-74, y -811..-837: full-width deck, no holes and no overhead structure; navmesh map), so it always lands
    // on planks even if he stands by the forward holes.
    inline constexpr float kGripLandYd = 8.f;
    inline constexpr DeadminesKit::Box2 kGripLandBox{ -74.f, -56.f, -837.f, -811.f };

    inline Vec2 GripLanding(Vec2 boss, Vec2 from)
    {
        float const dx = from.x - boss.x;
        float const dy = from.y - boss.y;
        float const d = std::hypot(dx, dy);
        Vec2 p = d > 0.01f ? Vec2{ boss.x + dx / d * kGripLandYd, boss.y + dy / d * kGripLandYd } : boss;
        p.x = std::clamp(p.x, kGripLandBox.minX, kGripLandBox.maxX);
        p.y = std::clamp(p.y, kGripLandBox.minY, kGripLandBox.maxY);
        return p;
    }

    // Per unit: how long it has been off the ship, and its post-grip cooldown. Keys are raw guids.
    class GripTracker
    {
    public:
        // `unit` was seen on (or off) the ship `diff` ms after its last update. True: grip it now (then call Gripped).
        bool Update(std::uint64_t unit, bool onShip, std::uint32_t diff)
        {
            Entry& e = _units[unit];
            e.cooldownMs = e.cooldownMs > diff ? e.cooldownMs - diff : 0;
            if (onShip)
            {
                e.offMs = 0;
                return false;
            }
            e.offMs += diff;
            return !e.cooldownMs && e.offMs >= kGripGraceMs;
        }

        // The pull: grip anyone off the ship at once (no grace), unless just gripped.
        bool PullNow(std::uint64_t unit, bool onShip) const
        {
            auto const it = _units.find(unit);
            return !onShip && (it == _units.end() || !it->second.cooldownMs);
        }

        void Gripped(std::uint64_t unit)
        {
            Entry& e = _units[unit];
            e.offMs = 0;
            e.cooldownMs = kGripCooldownMs;
        }

        void Clear() { _units.clear(); }
        std::size_t Size() const { return _units.size(); }

    private:
        struct Entry
        {
            std::uint32_t offMs = 0;
            std::uint32_t cooldownMs = 0;
        };
        std::unordered_map<std::uint64_t, Entry> _units;
    };
}

#endif
