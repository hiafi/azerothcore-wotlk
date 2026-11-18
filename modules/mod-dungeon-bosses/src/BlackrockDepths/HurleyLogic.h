/*
 * mod-dungeon-bosses, Blackrock Depths D18:
 * Hurley Blackbreath (9537), his Blackbreath Cronies (9541), the Thunderbrew Lager Kegs (300839) and the Lager Puddles
 * (300840), the pure, host-testable part (no engine headers). Build spec S4 "Hurley Blackbreath"
 * (docs/dungeons/blackrock-depths-4-imperial-seat.md, HU1-HU8; rulings 59-60, 88), handoff sections 3.4 (rows D18),
 * 3.5 (row D18), 3.6, 3.8 (NM: one open hall, the six keg spots), 7 #13 (the Cronies on C++, the 43,200 s respawn).
 * Tested by tests/brd_hurley_test.cpp.
 *
 *   Spells         the WP's ids, inside kSpellsHurley (211430-211459), declared in apps/dbc-tools
 *                  source/npcs/blackrock_depths/hurley.py
 *   Tuning         NH<> constants from the build spec (normal / heroic); the unset "stock rescaled" cell (Mortal
 *                  Strike) and the breath's width are this WP's defaults (report, designer questions)
 *   Wake           the stock wake-up (the third keg GO 164911 sends SetData 1,1): the escort path, the Cronies' copy
 *   KegRun         HU3 / HU4 as a small state machine (which keg is marked, the walk, the drink, the stacks)
 *   Geometry       the six keg spots (NM), the breath cone and the puddles in it (HU6), the walk's deadline
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_HURLEY_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_HURLEY_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitMath.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace BrdHurley
{
    using BlackrockDepthsRework::Point3;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsHurley;

    enum HurleySpells : std::uint32_t
    {
        SPELL_HU_MORTAL_STRIKE      = kSpellSlice.first + 0,    // 211430 HU1 the stock 16856 rescaled (-50% healing)
        SPELL_HU_FLAME_BREATH_BAR   = kSpellSlice.first + 1,    // 211431 HU2 the 2 s cast bar (not interruptible)
        SPELL_HU_FLAME_BREATH       = kSpellSlice.first + 2,    // 211432 HU2 the cone's hit, the others (resolve copy)
        SPELL_HU_FLAME_BREATH_TANK  = kSpellSlice.first + 3,    // 211433 HU2 the tank's own hit (refflat, tank row)
        SPELL_HU_FLAME_BREATH_LOOK  = kSpellSlice.first + 4,    // 211434 look: Breath of Fire's cone
        SPELL_HU_DRINK              = kSpellSlice.first + 5,    // 211435 HU3 the 3 s drink at the keg (the bar + look)
        SPELL_HU_LIQUID_COURAGE     = kSpellSlice.first + 6,    // 211436 HU4 +15% damage, +10% attack speed a stack
        SPELL_HU_COURAGE_FLASH      = kSpellSlice.first + 7,    // 211437 look: Drunken Rage's flash on each drink
        SPELL_HU_KEG_MARK           = kSpellSlice.first + 8,    // 211438 HU3 the marked keg's ring (the kill order key)
        SPELL_HU_LAGER_BUZZ         = kSpellSlice.first + 9,    // 211439 HU5 +10% damage done, 5 s after leaving
        SPELL_HU_TIPSY              = kSpellSlice.first + 10,   // 211440 HU5 -30% movement speed while inside
        SPELL_HU_LAGER_PUDDLE       = kSpellSlice.first + 11,   // 211441 HU5 the puddle's amber state on its stalker
        SPELL_HU_BURNING_LAGER      = kSpellSlice.first + 12,   // 211442 HU6 a burning puddle's tick (resolve copy)
        SPELL_HU_BURNING_LAGER_LOOK = kSpellSlice.first + 13,   // 211443 HU6 the burning state on the stalker
        SPELL_HU_BOTTLE_TOSS        = kSpellSlice.first + 14,   // 211444 HU8 the circle's hit (resolve copy)
        SPELL_HU_BOTTLE_TOSS_LOOK   = kSpellSlice.first + 15,   // 211445 look: the thrown bottle at the spot
        // 211446-211459 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_HU_BOTTLE_TOSS_LOOK;
    static_assert(kLastSpell <= kSpellSlice.last, "Hurley's spells must stay in his slice");

    // The Cronies' kept stock spells (S4 "Stock kit": Sinister Strike kept, Rupture heroic only; not rescaled, so the
    // stock ids, DD-scaled on heroic; neither is on DD's double-use list).
    inline constexpr std::uint32_t SPELL_STOCK_SINISTER_STRIKE = 15581;
    inline constexpr std::uint32_t SPELL_STOCK_RUPTURE = 15583;

    // Registry tags (per encounter; no drill row names Hurley).
    enum HurleyTags : std::uint32_t
    {
        TAG_HU_FLAME_BREATH  = 1,   // HU2
        TAG_HU_BURNING_LAGER = 2,   // HU6 (heroic)
        TAG_HU_BOTTLE_TOSS   = 3,   // HU8 (heroic)
    };

    // creature_text groups of 9537 (S4 "Text"; S0 range 0-5, 0-1 stock). Yells and a say; the drink is a boss emote
    // (type 41, rule 2).
    enum HurleyTexts : std::uint8_t
    {
        SAY_HURLEY_WAKE         = 0,    // stock yell "Get away from those kegs!"
        SAY_HURLEY_ARRIVE       = 1,    // stock say "You'll pay for that!" (now he attacks)
        SAY_HURLEY_THIRSTY      = 2,    // HU3 "All this fighting's made me thirsty!"
        EMOTE_HURLEY_DRINK      = 3,    // HU4 "%s drains the keg and roars with Liquid Courage!"
        SAY_HURLEY_KEG_SMASHED  = 4,    // HU3 "That was good ale, you fools!"
        SAY_HURLEY_DEATH        = 5,    // "Tell Ragnar... it was... delicious..."
    };

    // The keg GOs' SmartAI (164911 rows 0-2, kept) sends SetData(1, 1) to 9537 within 50 yd on the third keg; Hurley
    // passes the same call to his Cronies. Not DATA_DARK_IRON_ALE (1 with value 4: the patrons' id, GuzzlerLogic.h).
    inline constexpr std::uint32_t DATA_HURLEY_WAKE = 1;
    inline constexpr std::uint32_t DATA_HURLEY_WAKE_VALUE = 1;
    // GetData on Hurley's AI: 1 once he is awake (the Cronies' Reset reads it).
    inline constexpr std::uint32_t DATA_HURLEY_AWAKE = 2;

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S4 "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr NH<float> kBreathPct{ 30.f, 45.f };            // HU2 everyone but the tank in the cone, Weakened
    inline constexpr NH<float> kBreathTankPct{ 10.f, 15.f };        // HU2 the tank (tank row), no Weakened
    inline constexpr float kBurningLagerPct = 8.f;                  // HU6 heroic only, a second
    inline constexpr float kBottleTossPct = 25.f;                   // HU8 heroic only, Weakened
    // Unset in the spec ("stock rescaled", gaps 8 / 36): this WP's default, a designer question in the report.
    inline constexpr NH<float> kMortalStrikePct{ 20.f, 25.f };      // HU1 on the tank (tank row), -50% healing 5 s

    inline constexpr std::int32_t kDrinkHealPct = 10;               // HU3 of his maximum health
    inline constexpr std::int32_t kCourageDamagePct = 15;           // HU4 a stack
    inline constexpr std::int32_t kCourageHastePct = 10;            // HU4 a stack
    inline constexpr std::int32_t kLagerBuzzPct = 10;               // HU5 damage done
    inline constexpr std::int32_t kTipsyPct = 30;                   // HU5 movement speed
    inline constexpr std::int32_t kMortalStrikeHealingPct = 50;     // HU1 healing taken

    // Health at 5 players (handoff 3.6; heroic by WP-H's overrides and the keg's heroic template).
    inline constexpr NH<std::uint32_t> kHurleyHealth{ 140000, 200000 };
    inline constexpr NH<std::uint32_t> kCronyHealth{ 8000, 12000 };
    inline constexpr NH<std::uint32_t> kKegHealth{ 6000, 9000 };

    // ----------------------------------------------------------------------------------------------------------------
    // Timers (ms). The pull is t = 0.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint32_t kKegRunFirstMs = 15000;              // HU3
    inline constexpr NH<std::uint32_t> kKegRunEveryMs{ 25000, 20000 };  // HU3, from the previous lurch's start
    inline constexpr std::uint32_t kDrinkMs = 3000;                     // HU3 the drink at the keg
    inline constexpr std::uint32_t kLurchSlackMs = 4000;                // the walk's deadline past its plain time

    inline constexpr std::uint32_t kBreathFirstMs = 8000;               // HU2
    inline constexpr std::uint32_t kBreathEveryMs = 15000;
    inline constexpr std::uint32_t kBreathCastMs = 2000;

    inline constexpr std::uint32_t kMortalStrikeFirstMinMs = 5000;      // HU1 (stock event 14: 5-8 s, then 8-13 s)
    inline constexpr std::uint32_t kMortalStrikeFirstMaxMs = 8000;
    inline constexpr std::uint32_t kMortalStrikeEveryMinMs = 8000;
    inline constexpr std::uint32_t kMortalStrikeEveryMaxMs = 13000;
    inline constexpr std::uint32_t kMortalStrikeMs = 5000;              // the healing debuff
    inline constexpr float kMeleeRangeYd = 5.f;

    inline constexpr std::uint32_t kPuddleLifeMs = 30000;               // HU5
    inline constexpr std::uint32_t kPuddleTickMs = 1000;
    inline constexpr std::uint32_t kLagerBuzzMs = 5000;                 // refreshed each tick inside
    inline constexpr std::uint32_t kTipsyMs = 1500;                     // refreshed each tick inside: ends on leaving
    inline constexpr std::uint32_t kBurningLagerMs = 20000;             // HU6
    inline constexpr std::uint32_t kBurningLagerTickMs = 1000;
    static_assert(kTipsyMs > kPuddleTickMs, "Tipsy outlasts one tick, so it holds while the player stays inside");

    inline constexpr std::uint32_t kBottleTossFirstMs = 6000;           // HU8 heroic
    inline constexpr std::uint32_t kBottleTossEveryMs = 12000;
    inline constexpr std::uint32_t kBottleTossWarnMs = 1500;
    inline constexpr std::uint32_t kSinisterStrikeFirstMinMs = 1000;    // the Cronies (stock 9541: 1-3 s, then 4-7 s)
    inline constexpr std::uint32_t kSinisterStrikeFirstMaxMs = 3000;
    inline constexpr std::uint32_t kSinisterStrikeEveryMinMs = 4000;
    inline constexpr std::uint32_t kSinisterStrikeEveryMaxMs = 7000;
    inline constexpr std::uint32_t kRuptureFirstMs = 2000;              // HU7 heroic (stock 2 s, then 11-12 s)
    inline constexpr std::uint32_t kRuptureEveryMinMs = 11000;
    inline constexpr std::uint32_t kRuptureEveryMaxMs = 12000;

    inline constexpr std::uint32_t kWakeCheckMs = 2000;     // hidden: are the keg GOs all used (a cold restart)?
    inline constexpr std::uint32_t kRetryMs = 500;          // a due move that cannot start yet

    // ----------------------------------------------------------------------------------------------------------------
    // HU3 / HU4 the Keg Run: one keg marked at a time; smashed first, he turns back; reached, he drinks for 3 s (heal,
    // a Liquid Courage stack, the keg is gone, no puddle). A keg smashed while he drinks stops the drink (no heal, no
    // stack: the grace is the 3 s bar). No keg left: no more lurches.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr std::uint8_t kKegCount = 6;
    inline constexpr std::uint8_t kAllKegs = (1u << kKegCount) - 1u;

    enum class LurchPhase : std::uint8_t
    {
        None,       // fighting the tank
        Walking,    // walking to the marked keg (passive)
        Drinking,   // the 3 s drink at the keg
    };

    enum class KegEnd : std::uint8_t
    {
        Ignored,    // not a keg of this run (or already gone)
        Smashed,    // the marked keg, killed in time: he turns back
        Spilled,    // another keg (an AoE that reached an unmarked one): a puddle, nothing else
    };

    struct KegRun
    {
        std::uint8_t alive = kAllKegs;      // bit i: keg spot i still stands
        std::int8_t marked = -1;            // the keg he goes for (-1: none)
        LurchPhase phase = LurchPhase::None;
        std::uint32_t stacks = 0;           // Liquid Courage stacks (drinks finished)
        std::uint32_t smashed = 0;          // marked kegs the group killed first

        constexpr std::uint32_t Left() const
        {
            std::uint32_t n = 0;
            for (std::uint8_t i = 0; i < kKegCount; ++i)
                n += (alive >> i) & 1u;
            return n;
        }

        constexpr bool Alive(std::uint8_t index) const
        {
            return index < kKegCount && ((alive >> index) & 1u);
        }

        constexpr bool CanStart() const
        {
            return phase == LurchPhase::None && alive != 0;
        }

        // The lurch starts on keg `index`. False when it cannot (busy, no such keg).
        constexpr bool Start(std::uint8_t index)
        {
            if (!CanStart() || !Alive(index))
                return false;
            marked = static_cast<std::int8_t>(index);
            phase = LurchPhase::Walking;
            return true;
        }

        // He reached the marked keg: the drink starts. False when he was not walking to one.
        constexpr bool Arrived()
        {
            if (phase != LurchPhase::Walking)
                return false;
            phase = LurchPhase::Drinking;
            return true;
        }

        // The drink finished: the keg is drained (gone, no puddle), one more stack. False when there was no drink.
        constexpr bool DrinkDone()
        {
            if (phase != LurchPhase::Drinking || marked < 0)
                return false;
            alive = static_cast<std::uint8_t>(alive & ~(1u << marked));
            marked = -1;
            phase = LurchPhase::None;
            ++stacks;
            return true;
        }

        // Keg `index` died (players killed it).
        constexpr KegEnd Died(std::uint8_t index)
        {
            if (!Alive(index))
                return KegEnd::Ignored;
            alive = static_cast<std::uint8_t>(alive & ~(1u << index));
            if (marked != static_cast<std::int8_t>(index))
                return KegEnd::Spilled;
            marked = -1;
            phase = LurchPhase::None;
            ++smashed;
            return KegEnd::Smashed;
        }

        // The walk ran past its deadline (a path he cannot finish): he turns back. The keg stays marked and
        // attackable; the next lurch goes for it again (Restart).
        constexpr bool GiveUp()
        {
            if (phase != LurchPhase::Walking)
                return false;
            phase = LurchPhase::None;
            return true;
        }

        // The next lurch: the keg still marked from a walk he gave up, else -1 (a fresh pick).
        constexpr std::int8_t Pending() const
        {
            return phase == LurchPhase::None && marked >= 0 && Alive(static_cast<std::uint8_t>(marked)) ? marked : -1;
        }

        // A lurch on the pending keg (after GiveUp).
        constexpr bool Restart()
        {
            if (Pending() < 0)
                return false;
            phase = LurchPhase::Walking;
            return true;
        }
    };

    // The keg a lurch goes for: the `roll`-th (modulo the count) of the standing kegs, by spot order; -1 when none.
    inline constexpr std::int8_t PickKeg(std::uint8_t alive, std::uint32_t roll)
    {
        std::uint32_t n = 0;
        for (std::uint8_t i = 0; i < kKegCount; ++i)
            n += (alive >> i) & 1u;
        if (!n)
            return -1;
        std::uint32_t k = roll % n;
        for (std::uint8_t i = 0; i < kKegCount; ++i)
            if ((alive >> i) & 1u)
            {
                if (!k)
                    return static_cast<std::int8_t>(i);
                --k;
            }
        return -1;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Geometry [navmesh estimate] (handoff 3.8, NAVMESH 4.1; [db] where marked). Axes: +x north, +y west.
    // ----------------------------------------------------------------------------------------------------------------
    inline constexpr float kFloorZ = -49.7f;

    // The six keg spots (NM 4.1; K4 moved to (883, -163) for clearance 4, handoff 3.8). K6 is the stock keg cluster
    // (the three GOs 164911, consumed by the wake-up before the pull). Legs 17-25 yd: 7-10 s at his walk.
    inline constexpr std::array<Point3, kKegCount> kKegSpots{ {
        { 910.2f, -133.2f, -49.7f },    // K1
        { 893.2f, -130.8f, -49.7f },    // K2
        { 895.2f, -152.8f, -49.7f },    // K3
        { 883.0f, -163.0f, -49.7f },    // K4
        { 910.8f, -171.2f, -49.7f },    // K5
        { 916.7f, -150.0f, -49.7f },    // K6
    } };

    // The stock escort path (`waypoints` entry 9537, run) [db], ported: he runs it on the wake, the last node is home.
    inline constexpr std::array<Point3, 3> kWakePath{ {
        { 886.917f, -149.176f, -49.760f },
        { 897.699f, -137.324f, -49.752f },
        { 898.570f, -141.831f, -49.755f },
    } };
    inline constexpr float kCronyWakeRangeYd = 50.f;    // the stock SetData 1,1 to 9541 within 50 yd
    inline constexpr float kKegGoScanYd = 60.f;         // the keg GOs (37-41 yd from his spawn) for the wake check
    inline constexpr std::uint32_t kStockKegGos = 3;

    // Hidden, the wake check: every stock keg GO there and none of them standing means the kegs were used before a
    // reload (they respawn in 12 h, Hurley's wake is not saved): he wakes at once, without the yell.
    inline constexpr bool WakeFromUsedKegs(std::uint32_t found, std::uint32_t standing)
    {
        return found >= kStockKegGos && standing == 0;
    }

    // A Crony's copy of the path: Hurley's nodes shifted by the Crony's own offset from Hurley's spawn (the stock
    // per-guid paths 9541 / 9541000 / 9541001 keep the trio about this shape; this needs no guid).
    inline constexpr Point3 CronyNode(Point3 node, Point3 cronySpawn, Point3 hurleySpawn)
    {
        return { node.x + (cronySpawn.x - hurleySpawn.x), node.y + (cronySpawn.y - hurleySpawn.y), node.z };
    }

    inline constexpr float kWalkSpeedYd = 2.5f;         // his speed_walk 1.0 [db]
    inline constexpr float kKegStandOffYd = 3.0f;       // he stops this far from the keg's center to drink

    // The point he walks to: `standOff` short of the keg on the line from where he stands (where he stands when he is
    // already that close).
    inline Vec2 ApproachPoint(Vec2 from, Vec2 keg, float standOff)
    {
        float const dx = from.x - keg.x;
        float const dy = from.y - keg.y;
        float const d = std::sqrt(dx * dx + dy * dy);
        if (d <= standOff || d <= 0.f)
            return from;
        return { keg.x + dx / d * standOff, keg.y + dy / d * standOff };
    }

    // The walk's deadline: the plain walk at his speed plus the slack (a detour around a table, the turn).
    inline constexpr std::uint32_t LurchDeadlineMs(float distanceYd)
    {
        float const d = distanceYd > 0.f ? distanceYd : 0.f;
        return static_cast<std::uint32_t>(d / kWalkSpeedYd * 1000.f) + kLurchSlackMs;
    }

    // HU2 / HU6: the stock 15 yd cone (60 degrees, this WP's default: the spec gives the radius only); after a drink on
    // heroic his next breath is twice as wide.
    inline constexpr float kBreathLengthYd = 15.f;
    inline constexpr float kBreathAngleDeg = 60.f;
    inline constexpr float BreathAngleDeg(bool heroic, bool afterDrink)
    {
        return heroic && afterDrink ? 2.f * kBreathAngleDeg : kBreathAngleDeg;
    }

    inline constexpr float kPuddleRadius = 5.f;         // HU5 / HU6
    inline constexpr float kBottleRadius = 3.f;         // HU8

    // A circle (center `p`, radius `r`) touches the cone from `apex` along `facing` (radians), `angleDeg` wide and
    // `length` long: its center within length + r, and inside the half-angle widened by the circle's own angular size.
    // HU6 a puddle the breath ignites; HU2 the tank in the arc (r = his reach).
    inline bool CircleInCone(Vec2 apex, float facing, float angleDeg, float length, Vec2 p, float r)
    {
        float const dx = p.x - apex.x;
        float const dy = p.y - apex.y;
        float const d = std::sqrt(dx * dx + dy * dy);
        if (d > length + r)
            return false;
        if (d <= r)
            return true;    // the circle covers the apex
        float diff = std::atan2(dy, dx) - facing;
        while (diff > DungeonKit::kPi)
            diff -= DungeonKit::kTwoPi;
        while (diff < -DungeonKit::kPi)
            diff += DungeonKit::kTwoPi;
        float const half = angleDeg * DungeonKit::kPi / 360.f;
        float const widen = std::asin(std::min(1.f, r / d));
        return std::fabs(diff) <= half + widen;
    }
}

#endif
