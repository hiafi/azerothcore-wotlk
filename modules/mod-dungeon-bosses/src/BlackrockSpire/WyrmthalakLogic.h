/*
 * mod-dungeon-bosses, Blackrock Spire B8:
 * Overlord Wyrmthalak (9568), the pure, host-testable part (no engine headers). WP-B8 owns this file: its spell ids
 * (inside kSpellsWyrmthalak of BlackrockSpireRework.h, 210250-210289), tuning constants, flex target pairs, text
 * groups, timers, picks and geometry, tested by tests/brs_wyrmthalak_test.cpp. The engine side is
 * boss_overlord_wyrmthalak_rework.cpp; the hard mode hooks (WP-B9) are WyrmthalakFight.h.
 *
 * Build spec: SP 2436-2521 (WT1-WT8, WT18; WT9-WT17 are the hard mode's, B9). Damage is a percent of the reference
 * row (N = level 60 normal, H = level 60 heroic); counts "a / b" are 5 players / 6 or more (FlexAB).
 */

#ifndef MOD_DUNGEON_BOSSES_BRS_WYRMTHALAK_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRS_WYRMTHALAK_LOGIC_H

#include "BlackrockSpireRework.h"
#include "DungeonKitFlexRules.h"
#include "DungeonKitFlow.h"
#include "DungeonKitMath.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrsWyrmthalak
{
    using DungeonKit::NH;
    using DungeonKit::Vec2;
    using BlackrockSpireRework::FlexAB;
    using BlackrockSpireRework::Point3;

    // Every spell of this WP sits in this slice (BlackrockSpireRework.h; ids.yaml reservation `blackrock_spire`).
    inline constexpr BlackrockSpireRework::IdSlice kSpellSlice = BlackrockSpireRework::kSpellsWyrmthalak;

    // apps/dbc-tools source/npcs/blackrock_spire/wyrmthalak.py declares every one of them.
    enum WyrmthalakSpells : std::uint32_t
    {
        SPELL_WT_DRAGONFIRE_CAST    = 210250,   // WT1 the 2 s rear-up bar (Fire; Shadow Flame 22539's SV 6559)
        SPELL_WT_BLACK_DRAGONFIRE   = 210251,   // WT1 the breath's hit (resolve copy, Fire)
        SPELL_WT_DRAGONFIRE_BURN    = 210252,   // WT1b the burn's tick (resolve copy, Fire; heroic)
        SPELL_WT_BLACK_FLAME_PATCH  = 210253,   // WT1b the burning ground look on a stalker (V-1's SV 90601; B9's
                                                // Shadowflame Spit patches reuse it)
        SPELL_WT_TAIL_SWIPE         = 210254,   // WT2 the swipe's hit (resolve copy, Physical)
        SPELL_WT_TAIL_SWEEP_LOOK    = 210255,   // WT2 his tail sweep (Tail Sweep 15847's SV 3879, on him)
        SPELL_WT_BOULDER            = 210256,   // WT5 a boulder's landing (resolve copy, Physical)
        SPELL_WT_BOULDER_MISSILE    = 210257,   // WT5 the boulder in flight (Boulder 9483's SV 1506, a dest missile)
        SPELL_WT_AXE_VOLLEY         = 210258,   // WT6 the axes' landing (resolve copy, Physical)
        SPELL_WT_AXE_MARK           = 210259,   // WT6 the spinning axe on a marked player (Axe Flurry's SV 7163)
        SPELL_WT_THROW_AXE          = 210260,   // WT6 an axe in flight (Throw Axe 16075's SV 3962, a unit missile)
        SPELL_WT_WORG_RIDERS        = 210261,   // WT7 a rider's lane (resolve copy, Physical)
        SPELL_WT_WORG_CHARGE_LOOK   = 210262,   // WT7 the rider's charge (Charge 22911's SV 3783, on the rider)
        SPELL_WT_OVERLORDS_FURY     = 210263,   // WT8 heroic: +15% damage, +10% attack speed per stack (SV 8581)
        SPELL_WT_MORTAL_STRIKE      = 210264,   // WT18 at 10 players: 30% of the tank row (the kit's percent spell)
        SPELL_WT_MORTAL_WOUNDS      = 210265,   // WT18 -10% healing taken per stack, 15 s, refreshed, no cap
    };
    // 210266-210289 spare (ask B8 before taking one).
    std::uint32_t constexpr kFirstSpell = SPELL_WT_DRAGONFIRE_CAST;
    std::uint32_t constexpr kLastSpell = SPELL_WT_MORTAL_WOUNDS;

    std::uint32_t constexpr SPELL_WT_CLEAVE = 20691;    // WT3, stock (up to 5 targets in front)

    // ----------------------------------------------------------------------------------------------------------------
    // Texts (creature_text 9568; the SQL rev rev_wyrmthalak_blackrock_spire.sql). Lines 7-9 are the hard mode's (B9).
    // ----------------------------------------------------------------------------------------------------------------
    enum WyrmthalakTexts : std::uint8_t
    {
        YELL_WT_PULL            = 0,    // "You stand in the citadel of the Black Flight..." (replaces the stock emote)
        EMOTE_WT_BREATH         = 1,    // "%s draws a breath of black flame!"
        YELL_WT_SPIRESTONE      = 2,    // WT4 orders, one per tribe
        YELL_WT_SMOLDERTHORN    = 3,
        YELL_WT_BLOODAXE        = 4,
        EMOTE_WT_UNANSWERED     = 5,    // a dead champion's tribe
        YELL_WT_DEATH           = 6,
        EMOTE_WT_HORN           = 7,    // B9 (WT9)
        EMOTE_WT_CAUSTIC_ROAR   = 8,    // B9 (WT14)
        EMOTE_WT_SPEAR          = 9,    // B9 (WT15)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The tribes and their champions (WT4)
    // ----------------------------------------------------------------------------------------------------------------
    enum class Tribe : std::uint8_t
    {
        Spirestone = 0,         // ogres: Boulders (WT5)
        Smolderthorn = 1,       // trolls: Axe Volley (WT6)
        Bloodaxe = 2,           // orcs on worgs: Worg Riders (WT7)
    };
    std::size_t constexpr kTribeCount = 3;
    inline constexpr std::array<Tribe, kTribeCount> kTribes{ { Tribe::Spirestone, Tribe::Smolderthorn,
        Tribe::Bloodaxe } };

    constexpr std::size_t Index(Tribe t) { return static_cast<std::size_t>(t); }

    constexpr Tribe NextTribe(Tribe t) { return kTribes[(Index(t) + 1) % kTribeCount]; }

    constexpr std::uint32_t ChampionEntry(Tribe t)
    {
        switch (t)
        {
            case Tribe::Spirestone:     return BlackrockSpireRework::NPC_BRS_SPIRESTONE_CHAMPION;
            case Tribe::Smolderthorn:   return BlackrockSpireRework::NPC_BRS_SMOLDERTHORN_CHAMPION;
            case Tribe::Bloodaxe:       return BlackrockSpireRework::NPC_BRS_BLOODAXE_CHAMPION;
        }
        return 0;
    }

    constexpr std::optional<Tribe> TribeOfEntry(std::uint32_t entry)
    {
        for (Tribe t : kTribes)
            if (ChampionEntry(t) == entry)
                return t;
        return std::nullopt;
    }

    constexpr std::uint8_t OrderText(Tribe t)
    {
        return static_cast<std::uint8_t>(YELL_WT_SPIRESTONE + Index(t));
    }

    constexpr char const* TribeName(Tribe t)
    {
        switch (t)
        {
            case Tribe::Spirestone:     return "spirestone";
            case Tribe::Smolderthorn:   return "smolderthorn";
            case Tribe::Bloodaxe:       return "bloodaxe";
        }
        return "?";
    }

    inline std::optional<Tribe> TribeByName(char const* name)
    {
        if (!name)
            return std::nullopt;
        for (Tribe t : kTribes)
        {
            char const* a = TribeName(t);
            char const* b = name;
            while (*a && *a == *b)
            {
                ++a;
                ++b;
            }
            if (!*a && !*b)
                return t;
        }
        return std::nullopt;
    }

    // The tribes one order calls: `count` in turn from `next` (normal and heroic 1; the hard mode 2). Dead tribes stay
    // in the turn (their order goes unanswered, line 5).
    inline std::vector<Tribe> OrderTribes(Tribe next, std::uint8_t count)
    {
        std::vector<Tribe> out;
        Tribe t = next;
        for (std::uint8_t i = 0; i < count && i < kTribeCount; ++i)
        {
            out.push_back(t);
            t = NextTribe(t);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms since the pull, on the AI's own clock: a cast bar never pauses them)
    // ----------------------------------------------------------------------------------------------------------------
    std::uint32_t constexpr kBreathFirstMs = 8000;              // WT1: 8 s, then every 15 s
    std::uint32_t constexpr kBreathEveryMs = 15000;
    std::uint32_t constexpr kBreathCastMs = 2000;               // the rear-up (the bar and the cone's warning)
    std::uint32_t constexpr kTailFirstMs = 5000;                // WT2: 5 s, then every 12 s
    std::uint32_t constexpr kTailEveryMs = 12000;
    std::uint32_t constexpr kCleaveFirstMs = 6000;              // WT3: stock 6 s, every 7 s
    std::uint32_t constexpr kCleaveEveryMs = 7000;
    std::uint32_t constexpr kOrderFirstMs = 10000;              // WT4: 10 s, then N 30 s / H 25 s
    inline constexpr NH<std::uint32_t> kOrderEveryMs{ 30000, 25000 };
    std::uint32_t constexpr kMortalStrikeFirstMs = 8000;        // WT18: 8 s, every 8 s (10 players only)
    std::uint32_t constexpr kMortalStrikeEveryMs = 8000;
    std::uint32_t constexpr kRetryMs = 1000;                    // no target / out of reach: try again in 1 s
    std::uint32_t constexpr kFightLongMs = 30 * 60 * 1000;      // a persistent zone's "for the fight" (cancelled at
                                                                // the end)

    // The cast queue (DungeonKit::CastQueue): the breath, and B9's casts (ids from kHardModeCastBase).
    std::uint32_t constexpr CAST_BREATH = 1;
    std::uint32_t constexpr kHardModeCastBase = 100;
    std::uint8_t constexpr kBreathPriority = 2;
    std::uint32_t constexpr kCastSpacingMs = 1000;
    // An id no cast uses: CastQueue::Started on it holds the queue without touching an entry.
    std::uint32_t constexpr kHeldCastId = 0;

    // A hard mode cast comes up (B9's request, R-1 F-1d): its entry is consumed BEFORE the hook runs, so a next cast
    // the hook schedules for the same id (WyrmthalakFight::ScheduleCast inside OnCast) stays on the queue; the hold
    // then starts without cancelling anything. `onCast` answers the hold in ms (nullopt: it could not start). Returns
    // that answer.
    template <class OnCast>
    std::optional<std::uint32_t> StartHardModeCast(DungeonKit::CastQueue& queue, std::uint32_t id,
        DungeonKit::CastQueue::Ms now, OnCast&& onCast)
    {
        queue.Cancel(id);
        std::optional<std::uint32_t> const holdMs = onCast();
        if (holdMs)
            queue.Started(kHeldCastId, now, *holdMs);
        return holdMs;
    }

    // A hard mode cast bar ended early (kicked) at `now` while its hold runs to `holdUntil`: the hold ends now and the
    // queue's spacing counts from now (he does not stand idle for the rest of the bar). Returns the new hold end.
    inline DungeonKit::CastQueue::Ms EndHoldEarly(DungeonKit::CastQueue& queue, DungeonKit::CastQueue::Ms holdUntil,
        DungeonKit::CastQueue::Ms now)
    {
        if (now >= holdUntil)
            return holdUntil;
        queue.Interrupted(now);
        return now;
    }

    // WT1 at 10 players: the breath spares both tanks (SP: "tank-exempt for both tanks"; R-1-B M3); below 10 only his
    // victim, the registry's TankExempt.
    constexpr bool BreathSparesBothTanks(std::uint32_t players)
    {
        return DungeonKit::Flex::TankSwapOn(players);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WT1 Black Dragonfire, WT1b the burn (heroic)
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kBreathAngleDeg = 60.f;
    float constexpr kBreathLength = 25.f;
    inline constexpr NH<float> kBreathPct{ 35.f, 45.f };        // non-tanks; Weakened (both under 50%)
    float constexpr kBurnLength = 20.f;                         // heroic: the cone keeps burning
    std::uint32_t constexpr kBurnLifeMs = 8000;                 // from its appearance (the breath's landing)
    std::uint32_t constexpr kBurnGraceMs = 3000;                // its first tick 3 s after it appears
    std::uint32_t constexpr kBurnTickMs = 1000;
    float constexpr kBurnPct = 5.f;                             // per second, the tank too (ruling 49)

    // The burn's look: a few stalkers with the black flame patch (V-1's quad, about 8.9 yd across at scale 0.5) spread
    // over the cone, at fractions of its length; a spot over the open edge (no floor near the ledge's height) is
    // skipped by the AI.
    struct PatchSpot
    {
        float along;    // fraction of the length, along the axis
        float side;     // fraction of the distance along, sideways (the cone's half-width at d is d x tan 30)
    };
    inline constexpr std::array<PatchSpot, 4> kBurnPatchSpots{ { { 0.25f, 0.f }, { 0.55f, 0.f },
        { 0.8f, -0.32f }, { 0.8f, 0.32f } } };

    inline std::array<Vec2, kBurnPatchSpots.size()> BurnPatchPoints(Vec2 origin, float facing, float length)
    {
        std::array<Vec2, kBurnPatchSpots.size()> out{};
        for (std::size_t i = 0; i < kBurnPatchSpots.size(); ++i)
        {
            float const d = kBurnPatchSpots[i].along * length;
            Vec2 const onAxis = DungeonKit::Advance(origin, facing, d);
            out[i] = DungeonKit::Advance(onAxis, facing + DungeonKit::kPi / 2.f, kBurnPatchSpots[i].side * d);
        }
        return out;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WT2 Tail Swipe: a persistent rear cone on him, resolved every 12 s (the bots keep off his back the whole time)
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kTailAngleDeg = 120.f;
    float constexpr kTailLength = 15.f;
    inline constexpr NH<float> kTailPct{ 20.f, 25.f };
    // A 10 yd knockback away from him (Unit::KnockbackFrom: about speedXY x 2 speedZ / g yd).
    float constexpr kTailKnockSpeedXY = 12.f;
    float constexpr kTailKnockSpeedZ = 8.f;

    // ----------------------------------------------------------------------------------------------------------------
    // WT5 Boulders (Spirestone), WT6 Axe Volley (Smolderthorn), WT7 Worg Riders (Bloodaxe)
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr FlexAB kBoulderTargets{ 3, 6 };
    float constexpr kBoulderRadius = 4.f;
    std::uint32_t constexpr kBoulderWarnMs = 2500;
    inline constexpr NH<float> kBoulderPct{ 25.f, 30.f };
    float constexpr kBoulderMissileSpeed = 25.f;                // SPELL_WT_BOULDER_MISSILE's Speed (yd/s)

    inline constexpr FlexAB kAxeTargets{ 2, 4 };
    float constexpr kAxeRadius = 6.f;
    std::uint32_t constexpr kAxeWarnMs = 4000;
    inline constexpr NH<float> kAxePct{ 25.f, 30.f };           // everyone but the marked player within 6 yd
    float constexpr kAxeMissileSpeed = 20.f;                    // SPELL_WT_THROW_AXE's Speed (yd/s)

    inline constexpr FlexAB kRiderTargets{ 2, 4 };
    float constexpr kRiderLaneWidth = 4.f;
    std::uint32_t constexpr kRiderWarnMs = 3000;                // the lane marker, the riders pawing at the ramp head
    inline constexpr NH<float> kRiderPct{ 30.f, 35.f };
    float constexpr kRiderSpeed = 25.f;                         // yd/s across the ledge (the projectile and the run)
    float constexpr kRiderLaneInset = 1.f;                      // the lane stops this short of the ledge's rim
    float constexpr kRiderMinLane = 8.f;                        // a lane shorter than this is pushed to this length
    // Knocked 5 yd aside (perpendicular to the lane).
    float constexpr kRiderKnockSpeedXY = 9.f;
    float constexpr kRiderKnockSpeedZ = 5.5f;
    std::uint32_t constexpr kRiderLifeMs = 15000;               // a rider despawns by then whatever happens

    // A missile cast `delay` ms after the marker appears lands as the marker resolves (never negative).
    constexpr std::uint32_t MissileDelayMs(float distance, float speed, std::uint32_t warnMs)
    {
        if (speed <= 0.f)
            return 0;
        float const flightMs = distance / speed * 1000.f;
        return flightMs >= float(warnMs) ? 0u : warnMs - static_cast<std::uint32_t>(flightMs);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // WT8 Overlord's Fury (heroic, not the hard mode)
    // ----------------------------------------------------------------------------------------------------------------
    std::int32_t constexpr kFuryDamagePct = 15;
    std::int32_t constexpr kFuryHastePct = 10;
    std::uint8_t constexpr kFuryMaxStacks = 3;

    // ----------------------------------------------------------------------------------------------------------------
    // WT18 Mortal Strike and Mortal Wounds (10 players only, rulings 63-64; the taunt swap at 3)
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kMortalStrikeTankPct = 30.f;                // of the tank row: 1,113 N / 1,233 H
    std::uint32_t constexpr kMortalWoundsMs = 15000;
    std::int32_t constexpr kMortalWoundsHealingPct = -10;       // per stack
    std::uint8_t constexpr kMortalWoundsSwapAt = 3;

    // The user ruling (2026-11-15): a tank taunts only once the debuff has fallen off it. The old holder's last stack
    // lands just before the swap; the new holder reaches the swap count (swapAt - 1) strikes later at the earliest,
    // so the debuff must run out before that.
    constexpr bool DebuffFallsOffBeforeNextSwap(std::uint32_t everyMs, std::uint32_t durationMs, std::uint8_t swapAt)
    {
        return swapAt >= 2 && durationMs < static_cast<std::uint32_t>(swapAt - 1) * everyMs;
    }
    static_assert(DebuffFallsOffBeforeNextSwap(kMortalStrikeEveryMs, kMortalWoundsMs, kMortalWoundsSwapAt),
        "Mortal Wounds must fall off the old tank before the new one reaches the swap count");

    // ----------------------------------------------------------------------------------------------------------------
    // The room (handoff section 3.8, NM 8)
    // ----------------------------------------------------------------------------------------------------------------
    // The ledge hull [navmesh estimate] (9 vertices): the bots' spot bounds and the riders' lanes.
    inline constexpr std::array<Vec2, 9> kLedgeHull{ { { -52.8f, -501.8f }, { -42.8f, -511.2f }, { -10.8f, -504.2f },
        { -6.2f, -489.2f }, { -7.2f, -477.2f }, { -20.2f, -462.2f }, { -29.2f, -462.2f }, { -41.2f, -479.2f },
        { -47.2f, -488.8f } } };
    float constexpr kLedgeZMin = 87.f;
    float constexpr kLedgeZMax = 95.f;
    float constexpr kLedgeZ = 90.8f;                            // his spawn height (it tilts 89.3 .. 91.5)

    // Champions start on the ramp's foot (the navmesh path to the ramp head is about 45 yd: about 5 s at a run) and
    // walk up to a landing on the ledge's shoulder; a fallback engages them if the walk stalls.
    inline constexpr Point3 kChampionStart{ -73.8f, -500.0f, 79.1f };
    inline constexpr Point3 kChampionLanding{ -43.5f, -493.5f, 89.8f };
    std::uint32_t constexpr kChampionEngageFallbackMs = 12000;
    float constexpr kChampionStartSpread = 2.5f;                // a second one in the same order starts beside it

    // The boulder throwers stand in the lower hall under the open edge; the axe throwers on the ramp's upper bend.
    inline constexpr Point3 kBoulderThrowerSpot{ -49.2f, -468.0f, 78.1f };
    inline constexpr Point3 kAxeThrowerSpot{ -60.8f, -505.2f, 87.7f };
    std::uint32_t constexpr kThrowerLifeMs = 8000;

    // The riders burst off the ramp head onto the ledge here.
    inline constexpr Point3 kRiderOrigin{ -49.0f, -500.0f, 89.5f };

    // A rider's lane: from the ramp head through `through` to the ledge's far rim (kRiderLaneInset short of it), at
    // least kRiderMinLane long. `through` outside the hull, or a ray that meets no rim: through + 5 yd.
    struct Lane
    {
        Vec2 from;
        Vec2 to;
        float length = 0.f;
    };

    inline Lane RiderLane(Vec2 origin, Vec2 through)
    {
        Lane lane;
        lane.from = origin;
        float const o = DungeonKit::BearingTo(origin, through);
        std::optional<Vec2> const end = DungeonKit::PointInPolygon(kLedgeHull, through)
            ? DungeonKit::LaneEndAtWall(kLedgeHull, origin, through, kRiderLaneInset) : std::nullopt;
        lane.to = end ? *end : DungeonKit::Advance(through, o, 5.f);
        lane.length = DungeonKit::Distance(origin, lane.to);
        if (lane.length < kRiderMinLane)
        {
            lane.to = DungeonKit::Advance(origin, o, kRiderMinLane);
            lane.length = kRiderMinLane;
        }
        return lane;
    }

    // The point on the lane's line nearest `p`.
    inline Vec2 NearestOnLine(Lane const& lane, Vec2 p)
    {
        float const dx = lane.to.x - lane.from.x;
        float const dy = lane.to.y - lane.from.y;
        float const len2 = dx * dx + dy * dy;
        if (len2 <= 1e-6f)
            return lane.from;
        float const t = ((p.x - lane.from.x) * dx + (p.y - lane.from.y) * dy) / len2;
        return { lane.from.x + t * dx, lane.from.y + t * dy };
    }

    // The knock-aside origin for a hit at `p` (the hit is pushed away from it, sideways): the nearest point on the
    // lane's line, or, for a hit on the line itself, a point 0.5 yd to the lane's left of it.
    inline Vec2 KnockAsideOrigin(Lane const& lane, Vec2 p)
    {
        Vec2 const q = NearestOnLine(lane, p);
        if (DungeonKit::Distance(q, p) > 0.05f)
            return q;
        float const o = DungeonKit::BearingTo(lane.from, lane.to);
        return DungeonKit::Advance(p, o + DungeonKit::kPi / 2.f, 0.5f);
    }
}

#endif
