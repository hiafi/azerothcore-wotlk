/*
 * mod-dungeon-bosses, Gnomeregan D4: the Mobile Alert System (301110), the pure, host-testable part (no engine
 * headers): spell ids, texts, registry tags, the build spec's numbers (`namespace Tune`, section 3.5 rule 24), the
 * timeline rules, the fight's floor (the hall within 30 yd of him, section 7 #21 A), the adds' entry spot in the door
 * corridor, and the pure half of the LightsMachine (GnomereganMachines.h): the light plans of the Sweep and Turning
 * modes, the speed after Spotted, the reversal roll. Tested by tests/gnomer_alert_test.cpp. Health is
 * GnomereganRework.h Health::kAlertSystem / kSecurityAssistant / kSecurityDefender; the spot and the hall polygon are
 * GnomereganRework.h (section 3.8, ruling 66).
 *
 * Build spec: SP 1008-1224 (MA1-MA10, Build spec 1167), rulings 25-30, 66, 67; handoff section 3.5 row D4, 3.6, 3.8,
 * 3.9 row 6, section 7 #15 A, #16 B, #21 A, #22 A, #36-#38 A, section 10.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMER_MOBILE_ALERT_SYSTEM_LOGIC_H
#define MOD_DUNGEON_BOSSES_GNOMER_MOBILE_ALERT_SYSTEM_LOGIC_H

#include "GnomereganRework.h"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <utility>
#include <vector>

namespace GnomerAlert
{
    using DungeonKit::BearingTo;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (GnomereganRework.h; ids.yaml reservation `gnomeregan`).
    inline constexpr GnomereganRework::IdSlice kSpellSlice = GnomereganRework::kSpellsAlertSystem;

    // apps/dbc-tools source/npcs/gnomeregan/mobile_alert_system.py declares each (lib/test_gnomeregan_alert.py pins
    // the offsets). 214429-214459 spare.
    enum AlertSpells : std::uint32_t
    {
        SPELL_MA_SPOTTED        = kSpellSlice.first + 0,    // MA3 Spotted: resolve copy (Arcane), the registry's hit
        SPELL_MA_ALARM          = kSpellSlice.first + 1,    // MA8 Alarm: resolve copy (Nature), the pulse's hit
        SPELL_MA_ALARM_LOOK     = kSpellSlice.first + 2,    // MA8 the pulse's ring and loop sound on him (look only)
        SPELL_MA_LOCK_ON        = kSpellSlice.first + 3,    // MA1 the lock-on light pillar on the target (5 s aura)
        SPELL_MA_SPOTTED_BEAM   = kSpellSlice.first + 4,    // MA3 the red beam from him to the Spotted (look only)
        SPELL_MA_SELF_DESTRUCT  = kSpellSlice.first + 5,    // MA7 heroic: the clock aura on him (120 s)
        SPELL_MA_BLAST_LOOK     = kSpellSlice.first + 6,    // MA7 heroic: the blast at zero (look only)
        SPELL_MA_NET            = kSpellSlice.first + 7,    // MA9 heroic: the Assistant's Net (12024 at 3 s)
        SPELL_MA_NETTING        = kSpellSlice.first + 8,    // MA9 heroic: on the Assistant while its net holds
    };
    static_assert(SPELL_MA_NETTING <= kSpellSlice.last);

    // Stock spells the Defender casts by id (rule 16: the spec keeps them as they are, so no copy).
    std::uint32_t constexpr kSpellStockShoot = 6660;
    std::uint32_t constexpr kSpellStockMultiShot = 14443;

    // creature_text 301110 (rev_mobile_alert_system_gnomeregan.sql), 0-based as SP prints them (rule 35); line 8 is
    // section 7 #21 A's "the cameras" emote (not in SP's table: designer question).
    enum AlertTexts : std::uint8_t
    {
        YELL_MA_ALARM           = 0,    // "Warning! Warning! Intruder alert! Intruder alert!" (7849's, sound 5805)
        EMOTE_MA_LOCK_ON        = 1,    // MA1, names the target
        EMOTE_MA_SPOTTED        = 2,    // MA3, names the player
        EMOTE_MA_REVERSE        = 3,    // MA4 heroic
        YELL_MA_SELF_DESTRUCT   = 4,    // MA7 heroic, on the pull (7897's line)
        YELL_MA_TWENTY          = 5,    // MA7 heroic, at 20 s left (7897's line)
        EMOTE_MA_SKIPS_AHEAD    = 6,    // MA7 heroic, on a Spotted
        YELL_MA_CANCELED        = 7,    // MA10, at death
        EMOTE_MA_CAMERAS        = 8,    // section 7 #21 A: Spotted past 30 yd, names the player
    };

    // Registry tags: mod-boss-mechanics MechanicDrill.h's gnomeregan-shapes row 6 (kGnTagSearchlight 50, kGnTagLights
    // 52, kGnTagCameras 54; the swept floor one past each: LightsFloorTag). LESSONS A.3 #4: kept equal by hand, diffed
    // at WP close (the report).
    enum AlertTags : std::uint32_t
    {
        TAG_MA_SEARCHLIGHT          = 50,
        TAG_MA_SEARCHLIGHT_FLOOR    = 51,
        TAG_MA_LIGHTS               = 52,
        TAG_MA_LIGHTS_FLOOR         = 53,
        TAG_MA_CAMERAS              = 54,
    };

    constexpr std::uint32_t LightTag(bool heroic) { return heroic ? TAG_MA_LIGHTS : TAG_MA_SEARCHLIGHT; }
    constexpr std::uint32_t FloorTag(std::uint32_t lightTag) { return lightTag + 1; }

    // ----------------------------------------------------------------------------------------------------------------
    // The build spec's numbers (SP "Build spec", "Heroic", "Tuning starting points"; section 7 #21 A, #37 A)
    // ----------------------------------------------------------------------------------------------------------------
    namespace Tune
    {
        // MA1 Searchlight (normal): a lock-on at a random player within the light's reach, the tank included.
        inline constexpr std::uint32_t kSearchFirstMs = 8000;               // SP "8 s (guess)" (section 7 #37 A)
        inline constexpr std::uint32_t kSearchEveryMs = 10000;
        inline constexpr std::uint32_t kSearchRetryMs = 1000;               // nobody to pick, or a sweep still runs
        inline constexpr float kSearchConeDeg = 40.f;
        inline constexpr float kSearchSweepDeg = 60.f;                      // clockwise
        inline constexpr std::uint32_t kSearchDimMs = 2000;                 // the dim cone points at them
        inline constexpr std::uint32_t kSearchSweepMs = 3000;
        // MA2 Lights (heroic): two opposite cones, always on.
        inline constexpr std::uint32_t kLightsCount = 2;
        inline constexpr float kLightsConeDeg = 30.f;
        inline constexpr float kLightsDegPerSec = 12.f;
        inline constexpr std::uint32_t kLightsDarkMs = 3000;                // SP "after 3 sec (guess)": a dim warning
        inline constexpr float kLightsSpeedUpPct = 10.f;                    // per Spotted, no cap
        // MA4 Reverse sweep (heroic).
        inline constexpr std::uint32_t kReverseMinMs = 15000;
        inline constexpr std::uint32_t kReverseMaxMs = 25000;
        inline constexpr std::uint32_t kReverseStopMs = 2000;
        // The light's reach (section 7 #21 A) and the bots' floor inside it.
        inline constexpr float kLightReachYd = GnomereganRework::kAlertLightReachYd;   // 30
        inline constexpr float kBotFloorYd = 28.f;                          // 2 yd inside the cameras' line
        // MA3 Spotted: per player at most once per 3 s (section 7 #37 A), players only.
        inline constexpr std::uint32_t kSpottedLatchMs = 3000;
        inline constexpr NH<float> kSpottedPct{ 20.f, 50.f };               // the tank row on the tank
        inline constexpr std::uint32_t kSpottedClockMs = 5000;              // heroic: off the Self-destruct
        // Section 7 #21 A: a player in combat with him past the light's reach is Spotted (the cameras), judged twice
        // a second through the same latch.
        inline constexpr std::uint32_t kCameraEveryMs = 500;
        // MA5 Response Team: from the door corridor 3 s after a Spotted, starting on that player.
        inline constexpr std::uint32_t kResponseDelayMs = 3000;
        inline constexpr std::uint32_t kDefenderCapNormal = 4;              // heroic: no cap (rule 23)
        // MA6 Patrol: two Security Assistants from the door corridor, whatever the group does; they take the tank.
        inline constexpr NH<std::uint32_t> kPatrolEveryMs{ 30000, 20000 };  // the first after one period
        inline constexpr std::uint32_t kPatrolSize = 2;
        // MA8 Alarm pulse: every player in his fight, the tank included (tank row).
        inline constexpr std::uint32_t kAlarmFirstMs = 5000;
        inline constexpr std::uint32_t kAlarmEveryMs = 5000;
        inline constexpr NH<float> kAlarmPct{ 5.f, 8.f };
        // MA7 Self-destruct (heroic): the enrage. "Kills everyone in the hall" = everyone in combat with him and
        // anyone on the hall floor (section 7 #21 A).
        inline constexpr std::uint32_t kSelfDestructMs = 120000;
        inline constexpr std::uint32_t kSelfDestructWarnMs = 20000;         // line 5 (the stock "t-minus 20")
        inline constexpr std::uint32_t kClockReassertMs = 1000;             // the aura's duration follows the clock
        // MA9 Net (the heroic Assistant): a 3 s root on a random player in reach (20 yd, the stock range).
        inline constexpr std::uint32_t kNetFirstMs = 6000;                  // SP "6 s (guess)"
        inline constexpr std::uint32_t kNetEveryMs = 12000;                 // SP "12 s (guess)"
        inline constexpr std::uint32_t kNetMs = 3000;
        inline constexpr float kNetRangeYd = 20.f;
        inline constexpr std::uint32_t kNetRetryMs = 1000;
        // The Security Defender: the stock 6223 SmartAI's Shoot and Multi-Shot cadence.
        inline constexpr std::uint32_t kShootFirstMinMs = 500;
        inline constexpr std::uint32_t kShootFirstMaxMs = 1000;
        inline constexpr std::uint32_t kShootEveryMinMs = 2000;
        inline constexpr std::uint32_t kShootEveryMaxMs = 2500;
        inline constexpr std::uint32_t kMultiShotFirstMinMs = 5000;
        inline constexpr std::uint32_t kMultiShotFirstMaxMs = 12000;
        inline constexpr std::uint32_t kMultiShotEveryMinMs = 9000;
        inline constexpr std::uint32_t kMultiShotEveryMaxMs = 18000;
        inline constexpr float kDefenderRangeYd = 20.f;                     // AttackStartCaster distance
        // The walk in (LESSONS RB-31): an add that makes no progress toward its target for 15 s is put beside him.
        inline constexpr std::uint32_t kStuckCheckMs = 1000;
        inline constexpr std::uint32_t kStuckMs = 15000;
        inline constexpr float kStuckMoveYd = 1.f;
        inline constexpr float kStuckNearYd = 6.f;                          // in reach of its target: never stuck

        // The bots' boss data (SP "Boss data"): kill order Defender, Assistant, the boss; heroic: a netting Assistant
        // first. Ranged and healers hold an 11 to 16 yd band round him (SP Roles: "15 yd or closer"), well inside the
        // cameras' 30 yd, and past a hunter's Auto Shot too-close line (R-1-B m1: 5 yd minimum range + his reach +
        // a player's reach + 4/3, Spell::CheckRange; his reach is 0.8 x scale 3, creature_model_info 6888 and
        // mobile_alert_system.py ALERT_SCALE; both stand on the hall floor).
        inline constexpr std::int8_t kNettingPriority = 3;
        inline constexpr std::int8_t kDefenderPriority = 2;
        inline constexpr std::int8_t kAssistantPriority = 1;
        inline constexpr float kCombatReachYd = 2.4f;
        inline constexpr float kHunterTooCloseYd = 5.f + kCombatReachYd + 1.5f + 4.f / 3.f;    // 10.23
        inline constexpr float kBandMinYd = 11.f;
        inline constexpr float kBandMaxYd = 16.f;

        // Section 3.5 rule 24 (SYS 4): no hit under a 1.5 s warning on normal.
        static_assert(kSearchDimMs >= GnomereganRework::kWarningFloorMs);
        static_assert(kLightsDarkMs >= GnomereganRework::kWarningFloorMs);
        static_assert(kReverseStopMs >= GnomereganRework::kWarningFloorMs);
        // RB-29 drill hygiene: a cadence of at least the warning plus 0.5 s; one sweep ends before the next lock-on.
        static_assert(kSearchEveryMs >= kSearchDimMs + kSearchSweepMs + 500);
        static_assert(kReverseMinMs >= kReverseStopMs + 500);
        static_assert(kReverseMinMs <= kReverseMaxMs);
        static_assert(kSpottedLatchMs >= kCameraEveryMs);
        static_assert(kBotFloorYd < kLightReachYd);
        static_assert(kBandMaxYd < kBotFloorYd);
        static_assert(kBandMinYd > kHunterTooCloseYd, "the band starts past the hunters' too-close line");
        static_assert(kBandMinYd < kBandMaxYd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Values the build spec leaves open (switch constants; the report lists each as a designer question)
    // ----------------------------------------------------------------------------------------------------------------
    // Spotted applies Weakened on normal only: SP's Penalty column says "N Weakened" and heroic's "costs everything"
    // line lists no Weakened.
    inline constexpr NH<bool> kSpottedWeakened{ true, false };
    // Line 0 (the stock alarm) is yelled at the pull and with every patrol (the stock yelled it every 10 s).
    inline constexpr bool kAlarmYellWithPatrol = true;
    // The light stalkers wear the invisible stalker (the template's display); the optional white cone display
    // (CDI 90856, not yet seen in game) is off, the BM cone marker is the look.
    inline constexpr bool kUseConeDisplay = false;
    // Heroic lights start clockwise (normal's sweep is clockwise by the spec).
    inline constexpr int kLightsStartDirection = -1;

    // ----------------------------------------------------------------------------------------------------------------
    // The hall: the adds' entry spot and the fight's floor
    // ----------------------------------------------------------------------------------------------------------------
    // The door corridor, 5 yd in from the Workshop Door toward him and 1.5 yd east of the door's line, where the cut
    // hall polygon is widest (the door is 35.9 yd from his spot, about 37 yd of walking: NAVMESH 4). Facing him. The
    // adds of a wave stand kEntrySpacingYd apart across the corridor.
    inline constexpr GnomereganRework::Point3 kEntrySpot{ -756.78f, 255.47f, -273.05f, 4.76f };
    inline constexpr float kEntrySpacingYd = 2.5f;

    // Where the i-th of n adds of one wave appears: spread across the corridor (perpendicular to its axis).
    inline Vec2 EntryPoint(std::uint32_t i, std::uint32_t n)
    {
        float const o = kEntrySpot.o;
        float const side = (static_cast<float>(i) - (static_cast<float>(n) - 1.f) / 2.f) * kEntrySpacingYd;
        return { kEntrySpot.x - std::sin(o) * side, kEntrySpot.y + std::cos(o) * side };
    }

    // Shoelace area of a polygon (sq yd).
    inline float PolygonArea(std::vector<Vec2> const& poly)
    {
        float twice = 0.f;
        for (std::size_t i = 0, n = poly.size(); i < n; ++i)
        {
            Vec2 const a = poly[i];
            Vec2 const b = poly[(i + 1) % n];
            twice += a.x * b.y - b.x * a.y;
        }
        return std::fabs(twice) / 2.f;
    }

    // The regular `segments`-gon inscribed in the circle (counter-clockwise): every point of it is within `radius`.
    inline std::vector<Vec2> DiscPolygon(Vec2 center, float radius, std::uint32_t segments)
    {
        std::vector<Vec2> out;
        out.reserve(segments);
        for (std::uint32_t i = 0; i < segments; ++i)
        {
            float const a = DungeonKit::kTwoPi * static_cast<float>(i) / static_cast<float>(segments);
            out.push_back({ center.x + radius * std::cos(a), center.y + radius * std::sin(a) });
        }
        return out;
    }

    // Sutherland-Hodgman: `subject` (any simple polygon, either winding) clipped to the convex counter-clockwise
    // `clip`. Used once per pull for the fight's floor; the hall within 28 yd of him is one piece (host test).
    inline std::vector<Vec2> ClipToConvex(std::vector<Vec2> subject, std::vector<Vec2> const& clip)
    {
        auto inside = [](Vec2 a, Vec2 b, Vec2 p)
        {
            return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x) >= 0.f;
        };
        auto meet = [](Vec2 a, Vec2 b, Vec2 p, Vec2 q)
        {
            float const a1 = b.y - a.y, b1 = a.x - b.x, c1 = a1 * a.x + b1 * a.y;
            float const a2 = q.y - p.y, b2 = p.x - q.x, c2 = a2 * p.x + b2 * p.y;
            float const det = a1 * b2 - a2 * b1;
            if (std::fabs(det) < 1e-6f)
                return p;
            return Vec2{ (b2 * c1 - b1 * c2) / det, (a1 * c2 - a2 * c1) / det };
        };
        for (std::size_t e = 0, m = clip.size(); e < m && !subject.empty(); ++e)
        {
            Vec2 const a = clip[e];
            Vec2 const b = clip[(e + 1) % m];
            std::vector<Vec2> const input = std::move(subject);
            subject.clear();
            for (std::size_t i = 0, n = input.size(); i < n; ++i)
            {
                Vec2 const cur = input[i];
                Vec2 const prev = input[(i + n - 1) % n];
                bool const curIn = inside(a, b, cur);
                bool const prevIn = inside(a, b, prev);
                if (curIn)
                {
                    if (!prevIn)
                        subject.push_back(meet(a, b, prev, cur));
                    subject.push_back(cur);
                }
                else if (prevIn)
                    subject.push_back(meet(a, b, prev, cur));
            }
        }
        return subject;
    }

    inline constexpr std::uint32_t kFloorDiscSegments = 48;

    // The fight's floor (section 7 #21 A): the hall polygon within `radius` of `center` (his spot).
    inline std::vector<Vec2> FightFloorPolygon(Vec2 center, float radius)
    {
        std::vector<Vec2> hall(GnomereganRework::kHallPolygon.begin(), GnomereganRework::kHallPolygon.end());
        return ClipToConvex(std::move(hall), DiscPolygon(center, radius, kFloorDiscSegments));
    }

    inline DungeonKit::Arena FightFloorArena(Vec2 center, float radius)
    {
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Polygon(FightFloorPolygon(center, radius),
            GnomereganRework::kHallZMin, GnomereganRework::kHallZMax));
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timeline rules
    // ----------------------------------------------------------------------------------------------------------------
    // Rule 11 (RB-17): a beat never starves another: the next one is a period after it was due, but never sooner than
    // half a period from now.
    constexpr std::uint32_t NextDue(std::uint32_t dueMs, std::uint32_t periodMs, std::uint32_t nowMs)
    {
        return std::max(dueMs + periodMs, nowMs + periodMs / 2);
    }

    // Section 7 #21 A: the cameras see a player in combat with him past the light's reach.
    constexpr bool CameraSees(float distanceYd, bool inHisFight, float reachYd = Tune::kLightReachYd)
    {
        return inHisFight && distanceYd > reachYd;
    }

    // Rule 19 (R-1-B m4): an arriving patrol or Response Team takes the tank first (the one nearest the door when
    // there are two), else the nearest player; never simply his top threat (he deals no melee, so that is often a
    // damage dealer). Returns the index into `c`, or c.size() when it is empty.
    struct ArrivalCandidate
    {
        bool tank = false;
        float distanceYd = 0.f;     // from the door corridor's entry
    };

    inline std::size_t PickArrival(std::vector<ArrivalCandidate> const& c)
    {
        std::size_t best = c.size();
        for (std::size_t i = 0; i < c.size(); ++i)
        {
            if (best == c.size())
            {
                best = i;
                continue;
            }
            ArrivalCandidate const& a = c[i];
            ArrivalCandidate const& b = c[best];
            if (a.tank != b.tank ? a.tank : a.distanceYd < b.distanceYd)
                best = i;
        }
        return best;
    }

    // MA5: one more Defender is allowed (normal: at most 4 alive; heroic: no cap).
    constexpr bool DefenderAllowed(bool heroic, std::uint32_t aliveDefenders)
    {
        return heroic || aliveDefenders < Tune::kDefenderCapNormal;
    }

    // MA5: a Response Team is one Defender, plus one Assistant on heroic.
    constexpr std::uint32_t ResponseAssistants(bool heroic) { return heroic ? 1u : 0u; }

    // MA7 (heroic): the clock after a Spotted takes its 5 s (never below 0).
    constexpr std::uint32_t ClockAfterSpotted(std::uint32_t leftMs, std::uint32_t penaltyMs = Tune::kSpottedClockMs)
    {
        return leftMs > penaltyMs ? leftMs - penaltyMs : 0;
    }

    // MA7: the 20 s line is due once, the first time the clock is at or under the mark (a Spotted can jump it).
    constexpr bool WarnNow(std::uint32_t leftMs, bool warned, std::uint32_t warnAtMs = Tune::kSelfDestructWarnMs)
    {
        return !warned && leftMs > 0 && leftMs <= warnAtMs;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The LightsMachine's pure half (GnomereganMachines.h): the numbers each mode hands to DungeonKit::TurningLights
    // ----------------------------------------------------------------------------------------------------------------
    struct LightPlan
    {
        std::uint32_t count = 1;
        float degPerSec = 0.f;
        int direction = -1;             // -1 clockwise (the map's orientation shrinks)
        std::uint32_t litAfterMs = 0;   // the dim warning
        std::uint32_t lifeMs = 0;       // 0: until stopped
        std::uint32_t lookAheadMs = 0;
        std::uint32_t lookAheadStepMs = 0;
        bool drawLookAhead = false;
    };

    // Sweep (MA1): one cone, dim for `dimMs` at the target, then `sweepDeg` clockwise over `sweepMs` and gone; the
    // whole swept floor is marked at once (one look-ahead sector for the whole life, KT-G's recipe).
    constexpr LightPlan SweepPlan(float sweepDeg, std::uint32_t dimMs, std::uint32_t sweepMs)
    {
        LightPlan p;
        p.count = 1;
        p.degPerSec = sweepMs ? sweepDeg * 1000.f / static_cast<float>(sweepMs) : 0.f;
        p.direction = -1;
        p.litAfterMs = dimMs;
        p.lifeMs = dimMs + sweepMs;
        p.lookAheadMs = dimMs + sweepMs;
        p.lookAheadStepMs = 0;
        p.drawLookAhead = true;
        return p;
    }

    // The floor one sweep covers: the cone plus the sweep (KT-G pins 100 degrees for MA1).
    constexpr float SweptDeg(float coneDeg, float sweepDeg) { return std::min(360.f, coneDeg + sweepDeg); }

    // Turning (MA2, MT23): `count` cones evenly spaced, always on after `litAfterMs`, bot look ahead 3 s re-registered
    // every 0.5 s (KT-G's defaults), not drawn (the lit cones are the marker).
    inline constexpr std::uint32_t kTurningLookAheadMs = 3000;
    inline constexpr std::uint32_t kTurningLookAheadStepMs = 500;

    constexpr LightPlan TurningPlan(std::uint32_t count, float degPerSec, int direction, std::uint32_t litAfterMs)
    {
        LightPlan p;
        p.count = count ? count : 1;
        p.degPerSec = degPerSec;
        p.direction = direction < 0 ? -1 : 1;
        p.litAfterMs = litAfterMs;
        p.lifeMs = 0;
        p.lookAheadMs = kTurningLookAheadMs;
        p.lookAheadStepMs = kTurningLookAheadStepMs;
        p.drawLookAhead = false;
        return p;
    }

    // MA2: the turn rate after `speedUpPctTotal` percent of speed-ups in all (10 per Spotted, no cap), additive on
    // the base rate (KT-G's recipe: base x (1 + 0.1 x n)).
    constexpr float SpeedAfter(float baseDegPerSec, float speedUpPctTotal)
    {
        return baseDegPerSec * (1.f + std::max(0.f, speedUpPctTotal) / 100.f);
    }

    // MA4: the next reversal, `roll` (0 to 1) of the way from min to max.
    constexpr std::uint32_t ReversalInMs(std::uint32_t minMs, std::uint32_t maxMs, float roll)
    {
        if (maxMs <= minMs)
            return minMs;
        float const r = roll < 0.f ? 0.f : roll > 1.f ? 1.f : roll;
        return minMs + static_cast<std::uint32_t>(static_cast<float>(maxMs - minMs) * r);
    }
}

#endif
