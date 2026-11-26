/*
 * mod-dungeon-bosses, the shared dungeon kit (Zul'Farrak WP-KT, handoff section 3.11, F41; SP GZ2-GZ8, GZ13, GZ15,
 * GZ22, GZ23): pure rules for ground sheets of water that freeze, thaw and grow (Gahz'rilla's pool). No engine headers;
 * host-tested by tests/kit_water_test.cpp. The engine half is DungeonKitWater.h (WaterField: registry zones and discs).
 *
 *   WaterSheet    one sheet: a circle (a puddle, a floe, a spring) or a strip (the pool: a two-point line, the
 *                 registry's Line rectangle), its height and z band, its state (water or ice), its rules
 *   WaterSheets   the set on its own clock: add, freeze (at a point: the sheet the target stands in; within a reach:
 *                 every sheet that close), thaw on the clock (back to water at the size it froze, or gone), grow the
 *                 water (frozen sheets keep their radius, section 7 #43 f), the queries (water here? which sheet?)
 *   DiscFor       the disc look of a sheet: the display of its state (the storm disc during a Discharge tell) and the
 *                 creature scale radius / ydPerScale (appendix C: 4.8 yd per unit of scale, continuous, no ladder)
 *
 * Ice wins: a point on any ice sheet is dry, whatever water lies under it (a floe on the Deluge, a frozen puddle over a
 * newer one). No cap on a radius unless a sheet's rules set one (section 7 #36 A).
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WATER_LOGIC_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_WATER_LOGIC_H

#include "DungeonKitMath.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace DungeonKit
{
    enum class SheetState : std::uint8_t
    {
        Water,
        Ice
    };

    // What a thawing ice sheet becomes.
    enum class ThawTo : std::uint8_t
    {
        Water,      // back to water at the radius it froze (GZ8)
        Gone        // removed (a Deluge floe, GZ23)
    };

    struct SheetRules
    {
        bool canFreeze = true;          // false: the pool (section 7 #37 A), a Wellspring (GZ15)
        bool grows = true;              // false: GrowWater skips it (the pool, the Deluge sheet); Grow still works
        bool avoid = true;              // engine: a persistent telegraph-only Zone while water (the bots stay out)
        bool discharge = true;          // engine: RegisterDischarge registers it while water
        std::uint32_t thawMs = 45000;   // ice lasts this long (GZ8: 45 s normal, 30 s heroic); 0: until Thaw
        ThawTo thawTo = ThawTo::Water;
        float zBand = 6.f;              // yd above or below the sheet's height that still stand in it
        float maxRadiusYd = 0.f;        // 0: no cap (section 7 #36 A)
        float minRadiusYd = 0.5f;       // a shrink never goes below this
        std::uint32_t kind = 0;         // the caller's own tag (puddle, Meltwater, spring, pool, floe)
    };

    struct WaterSheet
    {
        std::uint32_t id = 0;
        Vec2 center;                    // a circle's center; a strip's first end
        std::optional<Vec2> end;        // a strip's second end (radius = half its width)
        float z = 0.f;
        float radius = 0.f;
        SheetState state = SheetState::Water;
        SheetRules rules;
        std::uint64_t thawAt = 0;       // the clock's ms at which the ice thaws (0: never)

        bool IsStrip() const { return end.has_value(); }
        bool IsWater() const { return state == SheetState::Water; }
        bool InBand(float pz) const { return std::fabs(pz - z) <= rules.zBand; }

        // Plane distance from `p` to the sheet's edge, 0 on or inside it. A strip is the registry's rectangle: from
        // `center` to `end`, `radius` either side, square ends.
        float EdgeDistance(Vec2 p) const
        {
            if (!end)
                return std::max(0.f, Distance(center, p) - radius);
            float const len = Distance(center, *end);
            if (len < 1e-4f)
                return std::max(0.f, Distance(center, p) - radius);
            float const ux = (end->x - center.x) / len;
            float const uy = (end->y - center.y) / len;
            float const along = (p.x - center.x) * ux + (p.y - center.y) * uy;
            float const side = std::fabs(-(p.x - center.x) * uy + (p.y - center.y) * ux);
            float const outAlong = std::max({ 0.f, -along, along - len });
            float const outSide = std::max(0.f, side - radius);
            return std::sqrt(outAlong * outAlong + outSide * outSide);
        }

        bool Contains(Vec2 p, float pz) const
        {
            return InBand(pz) && EdgeDistance(p) <= 0.f;
        }

        // A strip's middle, else the center.
        Vec2 Middle() const
        {
            return end ? Vec2{ (center.x + end->x) / 2.f, (center.y + end->y) / 2.f } : center;
        }
    };

    struct SheetChange
    {
        enum class Kind : std::uint8_t
        {
            Thawed,     // ice back to water
            Gone        // removed by its thaw
        };

        std::uint32_t id = 0;
        Kind kind = Kind::Thawed;
    };

    struct FreezeResult
    {
        std::vector<std::uint32_t> frozen;
        // The point stood in water that cannot freeze (the pool): the caller's rule decides (section 7 #37 A: nothing
        // freezes; on heroic a puddle spills at the nearest shore point).
        bool unfreezable = false;
        // Nothing froze and the point is in no water at all (GZ13: a Meltwater puddle under the target).
        bool Meltwater() const { return frozen.empty() && !unfreezable; }
    };

    class WaterSheets
    {
    public:
        std::uint32_t Add(Vec2 center, float z, float radius, SheetRules const& rules = {},
            SheetState state = SheetState::Water)
        {
            if (radius <= 0.f)
                return 0;
            WaterSheet s;
            s.id = _nextId++;
            s.center = center;
            s.z = z;
            s.rules = rules;
            s.radius = Clamp(rules, radius);
            s.state = state;
            if (state == SheetState::Ice)
                s.thawAt = ThawAt(rules);
            _sheets.push_back(s);
            return s.id;
        }

        // A strip from `from` to `to`, `halfWidth` either side (the pool: a 57 by 15 yd Line).
        std::uint32_t AddStrip(Vec2 from, Vec2 to, float z, float halfWidth, SheetRules const& rules = {},
            SheetState state = SheetState::Water)
        {
            std::uint32_t const id = Add(from, z, halfWidth, rules, state);
            if (WaterSheet* s = Mutable(id))
                s->end = to;
            return id;
        }

        bool Remove(std::uint32_t id)
        {
            auto it = std::find_if(_sheets.begin(), _sheets.end(), [id](WaterSheet const& s) { return s.id == id; });
            if (it == _sheets.end())
                return false;
            _sheets.erase(it);
            return true;
        }

        void Clear()
        {
            _sheets.clear();
        }

        WaterSheet const* Find(std::uint32_t id) const
        {
            for (WaterSheet const& s : _sheets)
                if (s.id == id)
                    return &s;
            return nullptr;
        }

        std::vector<WaterSheet> const& All() const { return _sheets; }
        std::size_t Count() const { return _sheets.size(); }

        std::size_t CountIn(SheetState state) const
        {
            return static_cast<std::size_t>(std::count_if(_sheets.begin(), _sheets.end(),
                [state](WaterSheet const& s) { return s.state == state; }));
        }

        std::uint64_t NowMs() const { return _nowMs; }

        // Water to ice (a sheet that may freeze). True when it froze.
        bool Freeze(std::uint32_t id)
        {
            WaterSheet* s = Mutable(id);
            if (!s || !s->IsWater() || !s->rules.canFreeze)
                return false;
            s->state = SheetState::Ice;
            s->thawAt = ThawAt(s->rules);
            return true;
        }

        // Ice back to water (thawTo Water) or removed (thawTo Gone), now. Nothing for a sheet that is not ice.
        std::optional<SheetChange> Thaw(std::uint32_t id)
        {
            WaterSheet* s = Mutable(id);
            if (!s || s->IsWater())
                return std::nullopt;
            if (s->rules.thawTo == ThawTo::Gone)
            {
                Remove(id);
                return SheetChange{ id, SheetChange::Kind::Gone };
            }
            s->state = SheetState::Water;
            s->thawAt = 0;
            return SheetChange{ id, SheetChange::Kind::Thawed };
        }

        // Icicle (GZ8): the water sheet the target stands in freezes, the nearest middle when several hold the point.
        FreezeResult FreezeAt(Vec2 p, float z)
        {
            FreezeResult r;
            WaterSheet const* best = nullptr;
            float bestD = 0.f;
            for (WaterSheet const& s : _sheets)
            {
                if (!s.IsWater() || !s.Contains(p, z))
                    continue;
                if (!s.rules.canFreeze)
                {
                    r.unfreezable = true;
                    continue;
                }
                float const d = Distance(s.Middle(), p);
                if (!best || d < bestD)
                {
                    best = &s;
                    bestD = d;
                }
            }
            if (best)
            {
                std::uint32_t const id = best->id;
                if (Freeze(id))
                    r.frozen.push_back(id);
                r.unfreezable = false;
            }
            return r;
        }

        // Freeze Solid (GZ8): every water sheet whose edge is within `yd` of the target (in its z band).
        FreezeResult FreezeWithin(Vec2 p, float z, float yd)
        {
            FreezeResult r;
            std::vector<std::uint32_t> ids;
            for (WaterSheet const& s : _sheets)
            {
                if (!s.IsWater() || !s.InBand(z) || s.EdgeDistance(p) > yd)
                    continue;
                if (!s.rules.canFreeze)
                {
                    r.unfreezable = r.unfreezable || s.EdgeDistance(p) <= 0.f;
                    continue;
                }
                ids.push_back(s.id);
            }
            for (std::uint32_t const id : ids)
                if (Freeze(id))
                    r.frozen.push_back(id);
            if (!r.frozen.empty())
                r.unfreezable = false;
            return r;
        }

        // Rising Water (GZ4): every water sheet that grows, by `deltaYd`. Frozen sheets keep their radius. Returns the
        // ids that changed.
        std::vector<std::uint32_t> GrowWater(float deltaYd)
        {
            std::vector<std::uint32_t> changed;
            for (WaterSheet& s : _sheets)
                if (s.IsWater() && s.rules.grows && Resize(s, s.radius + deltaYd))
                    changed.push_back(s.id);
            return changed;
        }

        // One sheet by hand, whatever its state or rules (a Wellspring's own 2 yd every 5 s).
        bool Grow(std::uint32_t id, float deltaYd)
        {
            WaterSheet* s = Mutable(id);
            return s && Resize(*s, s->radius + deltaYd);
        }

        bool SetRadius(std::uint32_t id, float radiusYd)
        {
            WaterSheet* s = Mutable(id);
            return s && Resize(*s, radiusYd);
        }

        // The clock: thaws every ice sheet whose time is up.
        std::vector<SheetChange> Advance(std::uint32_t diffMs)
        {
            _nowMs += diffMs;
            std::vector<std::uint32_t> due;
            for (WaterSheet const& s : _sheets)
                if (!s.IsWater() && s.thawAt && _nowMs >= s.thawAt)
                    due.push_back(s.id);
            std::vector<SheetChange> changes;
            for (std::uint32_t const id : due)
                if (std::optional<SheetChange> const c = Thaw(id))
                    changes.push_back(*c);
            return changes;
        }

        // Milliseconds until sheet `id` thaws (nullopt: not ice, or no thaw clock).
        std::optional<std::uint64_t> ThawInMs(std::uint32_t id) const
        {
            WaterSheet const* s = Find(id);
            if (!s || s->IsWater() || !s->thawAt)
                return std::nullopt;
            return s->thawAt > _nowMs ? s->thawAt - _nowMs : 0;
        }

        bool IsIce(Vec2 p, float z) const
        {
            for (WaterSheet const& s : _sheets)
                if (!s.IsWater() && s.Contains(p, z))
                    return true;
            return false;
        }

        // Water here: inside a water sheet and on no ice sheet (ice wins).
        bool IsWater(Vec2 p, float z) const
        {
            return WaterSheetAt(p, z).has_value();
        }

        // The water sheet a point stands in (nearest middle when several hold it); none on ice.
        std::optional<std::uint32_t> WaterSheetAt(Vec2 p, float z) const
        {
            if (IsIce(p, z))
                return std::nullopt;
            std::optional<std::uint32_t> best;
            float bestD = 0.f;
            for (WaterSheet const& s : _sheets)
            {
                if (!s.IsWater() || !s.Contains(p, z))
                    continue;
                float const d = Distance(s.Middle(), p);
                if (!best || d < bestD)
                {
                    best = s.id;
                    bestD = d;
                }
            }
            return best;
        }

        // Whether `p` stands in sheet `id` and counts as wet there (on no ice sheet). Conductive's "everyone in that
        // Puddle" (GZ14).
        bool InWaterSheet(std::uint32_t id, Vec2 p, float z) const
        {
            WaterSheet const* s = Find(id);
            return s && s->IsWater() && s->Contains(p, z) && !IsIce(p, z);
        }

        // The sheet nearest `p` by edge distance, any state, in the z band (a drop spot's preferred puddle).
        std::optional<std::uint32_t> NearestSheet(Vec2 p, float z, std::optional<SheetState> state = std::nullopt) const
        {
            std::optional<std::uint32_t> best;
            float bestD = 0.f;
            for (WaterSheet const& s : _sheets)
            {
                if ((state && s.state != *state) || !s.InBand(z))
                    continue;
                float const d = s.EdgeDistance(p);
                if (!best || d < bestD)
                {
                    best = s.id;
                    bestD = d;
                }
            }
            return best;
        }

    private:
        static float Clamp(SheetRules const& rules, float radius)
        {
            float r = std::max(radius, rules.minRadiusYd);
            if (rules.maxRadiusYd > 0.f)
                r = std::min(r, rules.maxRadiusYd);
            return r;
        }

        std::uint64_t ThawAt(SheetRules const& rules) const
        {
            return rules.thawMs ? _nowMs + rules.thawMs : 0;
        }

        static bool Resize(WaterSheet& s, float radius)
        {
            float const r = Clamp(s.rules, radius);
            if (std::fabs(r - s.radius) < 0.01f)
                return false;
            s.radius = r;
            return true;
        }

        WaterSheet* Mutable(std::uint32_t id)
        {
            for (WaterSheet& s : _sheets)
                if (s.id == id)
                    return &s;
            return nullptr;
        }

        std::vector<WaterSheet> _sheets;
        std::uint32_t _nextId = 1;
        std::uint64_t _nowMs = 0;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Disc looks (appendix C1, C2: CDI 90830 water, 90831 ice, 90832 storm; creature scale = radius / 4.8)
    // ----------------------------------------------------------------------------------------------------------------

    struct DiscLooks
    {
        std::uint32_t water = 0;        // 0: no disc at all
        std::uint32_t ice = 0;          // 0: the water display
        std::uint32_t storm = 0;        // 0: no Discharge tell (the water display stays)
        float ydPerScale = 4.8f;        // the model is 9.6 yd across at scale 1
        float minScale = 0.05f;
    };

    struct DiscLook
    {
        std::uint32_t display = 0;
        float scale = 1.f;

        bool operator==(DiscLook const& o) const { return display == o.display && std::fabs(scale - o.scale) < 1e-3f; }
    };

    // The disc a sheet wears: its state's display (the storm disc while `storming` and water), at radius /
    // ydPerScale. Nothing for a strip (the pool is real water) or with no water display.
    inline std::optional<DiscLook> DiscFor(WaterSheet const& s, bool storming, DiscLooks const& looks)
    {
        if (s.IsStrip() || !looks.water || looks.ydPerScale <= 0.f)
            return std::nullopt;
        DiscLook out;
        if (!s.IsWater())
            out.display = looks.ice ? looks.ice : looks.water;
        else if (storming && looks.storm)
            out.display = looks.storm;
        else
            out.display = looks.water;
        out.scale = std::max(looks.minScale, s.radius / looks.ydPerScale);
        return out;
    }
}

#endif
