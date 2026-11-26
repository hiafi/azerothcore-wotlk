/*
 * mod-dungeon-bosses, Zul'Farrak D7Hb: the Deluge, phase 3 of the hard mode "The Crew at the Pool" (GZ22-GZ24), the
 * pure, host-testable part (no engine headers). Build spec: docs/dungeons/zul-farrak-rework.md "Hard mode: the crew at
 * the pool", Phase 3 and rows GZ22-GZ24 (rulings 42, 43); handoff sections 3.5 row D7Hb, 3.7, 3.8 (the pool), 3.9
 * rows 9 and 10, 7 #36-#38, #43 (f), #58 and section 10. Tested by tests/zf_deluge_test.cpp; apps/dbc-tools
 * lib/test_zul_farrak_deluge.py pins the spell rows against this file.
 *
 *   DelugeSpells / Tags   the spells (kSpellsDeluge 214190-214209) and the registry tags (G1's drill row 10: 37, 38)
 *   Tune                  every number of the phase (rule 32)
 *   The trigger           DelugeDue: Gahz'rilla at or under 40% after a hit, once a pull
 *   The rise              DelugeRadiusAt: the look sheet (V's water disc) grows from scale 1 to 8 in 0.5 s steps over
 *                         5 s; then the cover strip makes the whole shore water for the rest of the fight
 *   Floes                 FloeRules, FloeRadius, FloeSpot: every Icicle (8 yd) and Freeze Solid (12 yd) in the phase
 *                         freezes a floe where it lands (a swimmer's at the nearest shore point: the pool never
 *                         freezes, section 7 #37 A); floes thaw away after 30 s (ice wins over the flood, KT)
 *   The flood             PlanFlood: D7's puddles are swallowed by the flood; a Call the Waters that lands in the
 *                         phase floods the floe under each of its puddles (designer question 1)
 *   Bot bounds            FloeCircles / IceIds: every ice sheet is a Strict SpotBounds circle (the drill's `floes`)
 *   The pin               PinSpotFor: his spot at the pool's edge, nearest the fight (section 7 #38 A)
 *   Storm Strikes         StrikeClock (three a second), StrikePoint (0 to 10 yd from a random player)
 *
 * Health is ZulFarrakRework.h Health (never restated here). Every water rule is KT's WaterField and D7's PoolFight.
 */

#ifndef MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_DELUGE_LOGIC_H
#define MOD_DUNGEON_BOSSES_ZF_GAHZRILLA_DELUGE_LOGIC_H

#include "DungeonKitMath.h"
#include "DungeonKitWaterLogic.h"
#include "GahzrillaLogic.h"
#include "ZulFarrakRework.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <vector>

namespace ZfDeluge
{
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (ZulFarrakRework.h; ids.yaml reservation `zul_farrak`).
    inline constexpr ZulFarrakRework::IdSlice kSpellSlice = ZulFarrakRework::kSpellsDeluge;

    // apps/dbc-tools source/npcs/zul_farrak/gahzrilla_deluge.py declares them (its test pins these ids).
    enum DelugeSpells : std::uint32_t
    {
        SPELL_DELUGE_STORM_STRIKE       = kSpellSlice.first + 0,    // GZ24: the registry's resolve copy (Nature)
        SPELL_DELUGE_STORM_STRIKE_LOOK  = kSpellSlice.first + 1,    // GZ24: the bolt at the point (the strike stalker)
    };
    // The first id D7Hb leaves free (214192-214209: spare).
    inline constexpr std::uint32_t kFirstSpareSpell = kSpellSlice.first + 2;
    static_assert(kFirstSpareSpell <= kSpellSlice.last + 1);

    // Registry tags: G1's zul-farrak-shapes row 10 uses the same (kZfTagFloe 37, kZfTagStrike 38).
    enum DelugeTags : std::uint32_t
    {
        TAG_DELUGE_FLOE     = 37,   // GZ22 / GZ23: the floes' Strict bounds (a Spot with no spots)
        TAG_DELUGE_STRIKE   = 38,   // GZ24: the 3 yd Storm Strikes
    };

    // WaterField SheetRules::kind of D7Hb's sheets (the packages use 10 and up; D7Hb takes 30 to 39).
    enum DelugeSheetKind : std::uint32_t
    {
        SHEET_DELUGE        = 30,   // the look sheet: V's water disc rising from the pool's middle
        SHEET_DELUGE_COVER  = 31,   // the strip that makes the whole shore water once the rise is done (no disc)
        SHEET_FLOE          = 32,   // GZ23: ice that thaws away
    };

    // Text groups (0-based, rule 34): Gahz'rilla 7273 group 1 is D7Hb's (D7 has 0, D7Ha 2).
    enum DelugeTexts : std::uint8_t
    {
        EMOTE_GAHZRILLA_DELUGE  = 1,    // "%s sinks into the sacred pool, and the waters rise!" (GZ22)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (rule 32). Damage percents are of the reference row (the registry's Damage / TankDamage).
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // GZ22 the Deluge: at his 40%, emote line 1, 5 s of rising water, then the whole shore is water.
        inline constexpr float kDelugeHealthPct = 40.f;
        inline constexpr std::uint32_t kRiseMs = 5000;
        inline constexpr std::uint32_t kRiseStepMs = 500;       // the disc's scale steps (the client blends them)
        inline constexpr float kRiseStartScale = 1.f;           // V's DELUGE_DISC_START_SCALE
        inline constexpr float kRiseEndScale = 8.f;             // V's DELUGE_DISC_SCALE (a 77 yd disc)
        static_assert(kRiseMs % kRiseStepMs == 0);

        // GZ23 floes: every Icicle and Freeze Solid in the phase; Icicle twice as often (D7's 10 s to 5 s).
        inline constexpr std::uint32_t kIcicleEveryMs = 5000;
        inline constexpr float kIcicleFloeYd = 8.f;
        inline constexpr float kFreezeSolidFloeYd = 12.f;
        inline constexpr std::uint32_t kFloeThawMs = 30000;
        inline constexpr float kFloeZBandYd = 6.f;              // KT's default band
        static_assert(kIcicleEveryMs * 2 == ZfPool::Tune::kIcicleEveryMs, "SP: Icicle comes twice as often");
        static_assert(kIcicleEveryMs >= ZfPool::Tune::kIcicleCastMs + ZfPool::Tune::kBeatMarginMs);
        // A Call the Waters that lands in the phase floods the floe under each of its puddles (designer question 1).
        inline constexpr bool kCallFloodsFloe = true;

        // The bots' floe bounds: each ice sheet a Strict circle this much smaller (a bot stands inside, not on the
        // rim), never under the minimum; registered for kFloeBoundsMs, renewed on every change or after the refresh.
        inline constexpr float kFloeBoundsInsetYd = 1.f;
        inline constexpr float kFloeBoundsMinYd = 1.5f;
        inline constexpr std::uint32_t kFloeBoundsMs = 40000;
        inline constexpr std::uint32_t kFloeBoundsRefreshMs = 30000;
        static_assert(kFloeBoundsRefreshMs < kFloeBoundsMs);

        // GZ24 Storm Strikes (ruling 43): three a second in all, each a 3 yd Circle AoE 0 to 10 yd from a random
        // player in a random direction, a 1.5 s warning, 30% Nature and Weakened. From the end of the rise.
        inline constexpr std::uint32_t kStrikesPerSecond = 3;
        inline constexpr float kStrikeRadiusYd = 3.f;
        inline constexpr float kStrikeScatterYd = 10.f;
        inline constexpr std::uint32_t kStrikeWarnMs = 1500;
        inline constexpr float kStrikePct = 30.f;
        inline constexpr float kStrikeZBandYd = 5.f;
        inline constexpr std::uint32_t kStrikeTries = 4;        // a point off the room is drawn again, then the player
        inline constexpr std::uint32_t kStrikeLogEvery = 30;    // one INFO line per 30 strikes (10 s)

        // GZ22 his pin (section 7 #38 A): the pool's edge, on the dry floor beside the water, nearest the fight. The
        // spots stand kPinAxisOffsetYd from the pool strip's axis (the water reaches 8 to 10 yd, the dry floor starts
        // a median 3.5 yd past it: NAVMESH), every kPinAlongStepYd along it.
        inline constexpr float kPinAxisOffsetYd = 13.f;
        inline constexpr float kPinAlongFirstYd = 8.f;
        inline constexpr float kPinAlongLastYd = 52.f;
        inline constexpr float kPinAlongStepYd = 4.f;
        inline constexpr float kShoreZ = 9.5f;                  // the shore's floor near the pool (a z hint to snap)

        // The warning floor (section 3.5 rule 32, SYS 4).
        static_assert(kStrikeWarnMs >= ZulFarrakRework::kWarningFloorMs);
        static_assert(kRiseMs >= ZulFarrakRework::kWarningFloorMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The trigger and the rise (GZ22)
    // ----------------------------------------------------------------------------------------------------------------

    // Gahz'rilla's health after a hit is at or under 40%: the Deluge starts (once a pull).
    constexpr bool DelugeDue(float healthPctAfterHit, bool started)
    {
        return !started && healthPctAfterHit <= Tune::kDelugeHealthPct;
    }

    inline constexpr std::uint32_t kRiseSteps = Tune::kRiseMs / Tune::kRiseStepMs;

    // The step of the rise `elapsedMs` in (0 at the start, kRiseSteps at its end).
    constexpr std::uint32_t RiseStep(std::uint32_t elapsedMs)
    {
        return std::min(elapsedMs / Tune::kRiseStepMs, kRiseSteps);
    }

    constexpr bool RiseDone(std::uint32_t elapsedMs)
    {
        return elapsedMs >= Tune::kRiseMs;
    }

    // The look sheet's radius at a step (the disc wears scale = radius / ZfPool::kDiscYdPerScale).
    constexpr float DelugeRadiusAtStep(std::uint32_t step)
    {
        float const s = Tune::kRiseStartScale
            + (Tune::kRiseEndScale - Tune::kRiseStartScale) * float(std::min(step, kRiseSteps)) / float(kRiseSteps);
        return s * ZfPool::kDiscYdPerScale;
    }

    constexpr float DelugeRadiusAt(std::uint32_t elapsedMs)
    {
        return DelugeRadiusAtStep(RiseStep(elapsedMs));
    }

    // The look sheet's middle: the pool's (on its surface).
    inline constexpr Vec2 kDelugeMiddle{ (ZfPool::kPoolAxisFrom.x + ZfPool::kPoolAxisTo.x) / 2.f,
        (ZfPool::kPoolAxisFrom.y + ZfPool::kPoolAxisTo.y) / 2.f };

    // The cover strip: an axis-aligned rectangle over the whole shore polygon (x 1615-1730, y 1125-1250) and its z band
    // (kShoreZMin to kShoreZMax), so every spot of the pool's arena is water once the rise is done. No disc (a strip);
    // the look is the risen disc.
    inline constexpr Vec2 kCoverFrom{ 1610.f, 1187.5f };
    inline constexpr Vec2 kCoverTo{ 1735.f, 1187.5f };
    inline constexpr float kCoverHalfWidthYd = 65.f;
    inline constexpr float kCoverZ = (ZulFarrakRework::kShoreZMin + ZulFarrakRework::kShoreZMax) / 2.f;
    inline constexpr float kCoverZBandYd = (ZulFarrakRework::kShoreZMax - ZulFarrakRework::kShoreZMin) / 2.f + 0.5f;
    // The look sheet's band: from the pool's surface over the shore's whole height.
    inline constexpr float kDelugeZBandYd = std::max(ZfPool::kPoolSurfaceZ - ZulFarrakRework::kShoreZMin,
        ZulFarrakRework::kShoreZMax - ZfPool::kPoolSurfaceZ) + 0.5f;

    // The flood's sheets (the look and the cover): never freeze, never grow, no avoid zone (a room-wide one would
    // send the bots off the map; the floes' Strict bounds hold them instead), no Discharge zone (KT's recipe).
    inline DungeonKit::SheetRules DelugeRules(std::uint32_t kind, float zBand)
    {
        DungeonKit::SheetRules rules;
        rules.canFreeze = false;
        rules.grows = false;
        rules.avoid = false;
        rules.discharge = false;
        rules.thawMs = 0;
        rules.zBand = zBand;
        rules.kind = kind;
        return rules;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Floes (GZ23)
    // ----------------------------------------------------------------------------------------------------------------

    // A floe: added as ice, thaws away after `thawMs` (KT: ThawTo::Gone).
    inline DungeonKit::SheetRules FloeRules(std::uint32_t thawMs = Tune::kFloeThawMs)
    {
        DungeonKit::SheetRules rules;
        rules.canFreeze = false;
        rules.grows = false;
        rules.avoid = false;
        rules.discharge = false;
        rules.thawMs = thawMs;
        rules.thawTo = DungeonKit::ThawTo::Gone;
        rules.zBand = Tune::kFloeZBandYd;
        rules.kind = SHEET_FLOE;
        return rules;
    }

    // An Icicle's floe or a Freeze Solid's (PoolFight.h FreezeKind is engine side).
    constexpr float FloeRadius(bool icicle)
    {
        return icicle ? Tune::kIcicleFloeYd : Tune::kFreezeSolidFloeYd;
    }

    // Where a freeze's floe forms: under the target, or at the nearest shore point when the target swims (the pool
    // never freezes, section 7 #37 A; D7's own shore spill uses the same point).
    inline Vec2 FloeSpot(Vec2 at, bool swimming)
    {
        return swimming ? ZfPool::ShoreSpotFor(at) : at;
    }

    // D7's puddles (GahzrillaLogic.h SheetKind; the pool itself is never one).
    constexpr bool IsPoolPuddle(std::uint32_t kind)
    {
        return kind == ZfPool::SHEET_SPILL || kind == ZfPool::SHEET_CALL || kind == ZfPool::SHEET_MELTWATER
            || kind == ZfPool::SHEET_GM;
    }

    // What the flood does to the water field this tick (after the rise): every water puddle of D7's is swallowed by
    // the flood (removed: the shore is water already, and its avoid zone would only fight the floes' bounds); a Call
    // the Waters puddle that landed after the flood (`floodFromId` and up) floods the ice its middle lies on.
    struct FloodPlan
    {
        std::vector<std::uint32_t> swallowed;   // D7's water puddles to remove
        std::vector<std::uint32_t> flooded;     // ice sheets a new Call puddle landed on (removed)
    };

    inline FloodPlan PlanFlood(DungeonKit::WaterSheets const& sheets, std::uint32_t floodFromId)
    {
        FloodPlan plan;
        for (DungeonKit::WaterSheet const& s : sheets.All())
        {
            if (!s.IsWater() || s.IsStrip() || !IsPoolPuddle(s.rules.kind))
                continue;
            plan.swallowed.push_back(s.id);
            if (!Tune::kCallFloodsFloe || s.rules.kind != ZfPool::SHEET_CALL || s.id < floodFromId)
                continue;
            for (DungeonKit::WaterSheet const& ice : sheets.All())
                if (!ice.IsWater() && !ice.IsStrip() && ice.Contains(s.center, s.z)
                    && std::find(plan.flooded.begin(), plan.flooded.end(), ice.id) == plan.flooded.end())
                    plan.flooded.push_back(ice.id);
        }
        return plan;
    }

    // The highest sheet id in the field (0: none): sheets added later have higher ids (KT's counter).
    inline std::uint32_t MaxSheetId(DungeonKit::WaterSheets const& sheets)
    {
        std::uint32_t id = 0;
        for (DungeonKit::WaterSheet const& s : sheets.All())
            id = std::max(id, s.id);
        return id;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The bots' floe bounds (G1 row 10: strict bounds of 6 to 8 circles changing every 5 to 10 s)
    // ----------------------------------------------------------------------------------------------------------------

    struct FloeCircle
    {
        std::uint32_t id = 0;
        Vec2 center;
        float z = 0.f;
        float radius = 0.f;     // inset (Tune::kFloeBoundsInsetYd), never under Tune::kFloeBoundsMinYd
        float zBand = 0.f;
    };

    // Every ice circle (a floe or a frozen puddle: ice wins, so both are dry ground), in id order.
    inline std::vector<FloeCircle> FloeCircles(DungeonKit::WaterSheets const& sheets)
    {
        std::vector<FloeCircle> out;
        for (DungeonKit::WaterSheet const& s : sheets.All())
        {
            if (s.IsWater() || s.IsStrip())
                continue;
            FloeCircle c;
            c.id = s.id;
            c.center = s.center;
            c.z = s.z;
            c.radius = std::max(Tune::kFloeBoundsMinYd, s.radius - Tune::kFloeBoundsInsetYd);
            c.zBand = s.rules.zBand;
            out.push_back(c);
        }
        std::sort(out.begin(), out.end(), [](FloeCircle const& a, FloeCircle const& b) { return a.id < b.id; });
        return out;
    }

    // The ids of FloeCircles: the bounds are registered again when they change.
    inline std::vector<std::uint32_t> IceIds(DungeonKit::WaterSheets const& sheets)
    {
        std::vector<std::uint32_t> ids;
        for (FloeCircle const& c : FloeCircles(sheets))
            ids.push_back(c.id);
        return ids;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // His pin at the pool's edge (GZ22, section 7 #38 A)
    // ----------------------------------------------------------------------------------------------------------------

    // The pin spots: both sides of the pool strip's axis, kPinAxisOffsetYd out, every kPinAlongStepYd from
    // kPinAlongFirstYd to kPinAlongLastYd (host-tested: on the shore, clear of the water by 4 yd, within reach of it).
    inline std::vector<Vec2> PinSpots()
    {
        float const len = DungeonKit::Distance(ZfPool::kPoolAxisFrom, ZfPool::kPoolAxisTo);
        float const ux = (ZfPool::kPoolAxisTo.x - ZfPool::kPoolAxisFrom.x) / len;
        float const uy = (ZfPool::kPoolAxisTo.y - ZfPool::kPoolAxisFrom.y) / len;
        std::vector<Vec2> out;
        for (float const side : { 1.f, -1.f })
            for (float t = Tune::kPinAlongFirstYd; t <= Tune::kPinAlongLastYd + 0.01f; t += Tune::kPinAlongStepYd)
                out.push_back({ ZfPool::kPoolAxisFrom.x + ux * t - uy * Tune::kPinAxisOffsetYd * side,
                    ZfPool::kPoolAxisFrom.y + uy * t + ux * Tune::kPinAxisOffsetYd * side });
        return out;
    }

    // The pin spot nearest `from` (where the group fought him).
    inline Vec2 PinSpotFor(Vec2 from)
    {
        std::vector<Vec2> const spots = PinSpots();
        Vec2 best = spots.front();
        float bestD = std::numeric_limits<float>::max();
        for (Vec2 const& s : spots)
        {
            float const d = DungeonKit::Distance(s, from);
            if (d < bestD)
            {
                best = s;
                bestD = d;
            }
        }
        return best;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Storm Strikes (GZ24)
    // ----------------------------------------------------------------------------------------------------------------

    // Three a second on an even beat (one every 333 ms, the drill's `every=333`), from Start.
    class StrikeClock
    {
    public:
        void Start()
        {
            _running = true;
            _elapsed = 0;
            _fired = 0;
        }
        void Stop() { *this = StrikeClock(); }
        bool Running() const { return _running; }
        std::uint64_t Fired() const { return _fired; }

        // Advances the clock; returns how many strikes are due now.
        std::uint32_t Advance(std::uint32_t diff)
        {
            if (!_running)
                return 0;
            _elapsed += diff;
            std::uint64_t const due = _elapsed * Tune::kStrikesPerSecond / 1000;
            std::uint32_t const n = due > _fired ? std::uint32_t(due - _fired) : 0;
            _fired = std::max(_fired, due);
            return n;
        }

    private:
        bool _running = false;
        std::uint64_t _elapsed = 0;
        std::uint64_t _fired = 0;
    };

    // A strike's middle: `distFrac` x kStrikeScatterYd from the player, `angleFrac` of a full turn (both in [0, 1]).
    inline Vec2 StrikePoint(Vec2 player, float distFrac, float angleFrac)
    {
        float constexpr kTwoPi = 6.28318530718f;
        float const d = std::clamp(distFrac, 0.f, 1.f) * Tune::kStrikeScatterYd;
        float const a = std::clamp(angleFrac, 0.f, 1.f) * kTwoPi;
        return { player.x + d * std::cos(a), player.y + d * std::sin(a) };
    }
}

#endif
