/*
 * mod-dungeon-bosses, Blackrock Depths D19:
 * Phalanx (9502) and the heroic Rowdy Patrons (300841), the pure, host-testable part (no engine headers). Build spec
 * S4 "Phalanx" (docs/dungeons/blackrock-depths-4-imperial-seat.md, PH1-PH6; rulings 63-66), handoff sections 3.4 (row
 * D19), 3.5, 3.8 (NM: the bar's upper floor, the seven tables, the tank's Spot by the door), 3.10 and 3.11 (KT-D2's
 * DamageLedger). Tested by tests/brd_phalanx_test.cpp.
 *
 *   Spells       the WP's ids, inside kSpellsPhalanx (211460-211489), declared in apps/dbc-tools
 *                source/npcs/blackrock_depths/phalanx.py
 *   Tuning       NH<> constants straight from the build spec (normal / heroic); the "stock rescaled" cells (Mighty
 *                Blow, Thunderclap, Fireball Volley) and the knockback speeds are this WP's defaults (report, designer
 *                questions)
 *   State        the stock DORMANT / MOVING_TO_DOOR / ACTIVE machine (BrdGuzzler::PhalanxState, D17's model), its
 *                path, door node, factions and the new gossip start
 *   Geometry     the throw floor (the main upper floor from the navmesh, 1.5-2 yd inside its edges, the drop to the
 *                lower level and the door alcove left out), the seven tables (NM 4.2) with their chairs [db], a
 *                pillar, the fixed fallback landings, the tank's Spot
 *   Timeline     the five clocks (Throw Out, Last Call, Thunderclap, Mighty Blow, Fireball Volley) and the rule that a
 *                throw and Last Call never run at once. The engine runs this very struct; the test replays 300 s
 *   Property Damage (heroic) which table a knocked player smashes, the Outrage scale
 *
 * Axes: x north, y west (NAVMESH-REPORT). The floor's +y edge (y about -170 to -195) is the rail over the lower level
 * (z -50), its -y edge the wall with the Bar Door.
 */

#ifndef MOD_DUNGEON_BOSSES_BRD_PHALANX_LOGIC_H
#define MOD_DUNGEON_BOSSES_BRD_PHALANX_LOGIC_H

#include "BlackrockDepthsRework.h"
#include "DungeonKitArena.h"
#include "DungeonKitMath.h"
#include "GuzzlerLogic.h"
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace BrdPhalanx
{
    using BlackrockDepthsRework::Point3;
    using BlackrockDepthsRework::Point4;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    // Every spell of this WP sits in this slice (BlackrockDepthsRework.h; ids.yaml reservation `blackrock_depths`).
    inline constexpr BlackrockDepthsRework::IdSlice kSpellSlice = BlackrockDepthsRework::kSpellsPhalanx;

    enum PhalanxSpells : std::uint32_t
    {
        SPELL_PH_MIGHTY_BLOW      = kSpellSlice.first + 0,     // 211460 PH1 stock 14099 rescaled: tank hit + knockback
        SPELL_PH_THUNDERCLAP      = kSpellSlice.first + 1,     // 211461 PH2 stock 15588 rescaled: 10 yd, Magic slow
        SPELL_PH_FIREBALL_VOLLEY  = kSpellSlice.first + 2,     // 211462 PH3 stock 15285 rescaled: 20 yd, from 50%
        SPELL_PH_GRAB             = kSpellSlice.first + 3,     // 211463 PH4 the 1 s hold on the player (SV 12139)
        SPELL_PH_THROW_LOOK       = kSpellSlice.first + 4,     // 211464 PH4 look: his throw (SV 12140) at the player
        SPELL_PH_THROW_OUT        = kSpellSlice.first + 5,     // 211465 PH4 the landing circle's hit (resolve copy)
        SPELL_PH_THROWN           = kSpellSlice.first + 6,     // 211466 PH4 the thrown player's hit (resolve copy)
        SPELL_PH_SLAM_LOOK        = kSpellSlice.first + 7,     // 211467 look: Ground Slam at a point (SV 8083)
        SPELL_PH_LAST_CALL_CAST   = kSpellSlice.first + 8,     // 211468 PH5 the 3 s bar (the bell, SV 215)
        SPELL_PH_LAST_CALL        = kSpellSlice.first + 9,     // 211469 PH5 the pulse's hit (resolve copy)
        SPELL_PH_OUTRAGE          = kSpellSlice.first + 10,    // 211470 PH6 +15% damage done a stack, 5 at most
        SPELL_PH_TABLE_SMASH      = kSpellSlice.first + 11,    // 211471 PH6 the smasher's hit (resolve copy)
        SPELL_PH_TABLE_SPLINTERS  = kSpellSlice.first + 12,    // 211472 PH6 look: wood chips at the table (SV 90344)
        // 211473-211489 spare
    };
    inline constexpr std::uint32_t kLastSpell = SPELL_PH_TABLE_SPLINTERS;
    static_assert(kLastSpell <= kSpellSlice.last, "Phalanx's spells must stay in his slice");

    // Registry tags (this fight's own; no G1/G2 drill row names Phalanx).
    enum PhalanxTags : std::uint32_t
    {
        TAG_PH_THROW_OUT = 1,       // PH4 the landing circle (everyone but the thrown player)
        TAG_PH_LAST_CALL = 2,       // PH5
        TAG_PH_THROWN    = 3,       // PH4 the thrown player's hit (RegistryHit)
        TAG_PH_SMASH     = 4,       // PH6 the smasher's hit (RegistryHit)
        TAG_PH_PARK      = 5,       // the tank's Spot by the door (a hidden tank-only Park circle)
    };

    // creature_text groups of 9502 (S4 "Text"): 0 is the stock wake-up yell, 1-4 are new. 1 is a boss emote (type 41,
    // rule 2), 2-4 yells.
    enum PhalanxTexts : std::uint8_t
    {
        SAY_PH_DOOR             = 0,    // stock "Violence!  Property damage!  None shall pass!!"
        EMOTE_PH_GRAB           = 1,    // PH4 "%s grabs $n by the collar!"
        YELL_PH_LAST_CALL       = 2,    // PH5 "Last call! Everybody out!"
        YELL_PH_PROPERTY_DAMAGE = 3,    // PH6 "PROPERTY DAMAGE!"
        YELL_PH_DEATH           = 4,    // "Closing... time..."
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The state machine (stock npc_phalanx, blackrock_depths.cpp 405-598; D17's BarModel is the whole room's model)
    // ----------------------------------------------------------------------------------------------------------------

    using BrdGuzzler::PhalanxRequest;
    using BrdGuzzler::PhalanxState;

    inline constexpr std::uint32_t kPathDoor = 95020;              // waypoint_data, 2 nodes, run
    inline constexpr std::uint32_t kFactionAwake = 54;           // stock FACTION_PHALANX_HOSTILE (Dark Iron)
    inline constexpr std::uint32_t kFactionPluggerDeath = BrdGuzzler::kFactionAllHostile;   // 14: Plugger's death
    inline constexpr std::uint32_t kYellDelayMs = 200;             // the wake-up yell after the walk starts
    inline constexpr std::uint32_t kWalkWatchdogMs = 15000;        // a stalled walk activates him where he stands
    // The door node: path 95020's last node [db waypoint_data]; his home once he is awake.
    inline constexpr Point4 kDoorNode{ 867.295f, -222.645f, -43.7259f, 2.00713f };
    // The new gossip start (ruling 66): stock menu 2283 ("I do not enjoy conversation.", text 2973) gets option 0.
    inline constexpr std::uint32_t kGossipMenu = 2283;
    inline constexpr std::uint32_t kGossipOption = 0;

    // Plugger's death reaches Phalanx only through his faction (SmartAI 9499 ids 9-12: SET_FACTION 14 within 100 yd;
    // D17 section 0): seen in his UpdateAI while he is dormant.
    constexpr bool PluggerDeathSeen(PhalanxState state, std::uint32_t faction)
    {
        return state == PhalanxState::Dormant && faction == kFactionPluggerDeath;
    }

    // Damage on him while he walks to the door (the Plugger route: faction 14, passive) wakes him at once (rule 10).
    constexpr bool WakesOnDamage(PhalanxState state)
    {
        return state == PhalanxState::MovingToDoor;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (S4 "Build spec"; damage in percent of the reference row, "N / H")
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr std::uint32_t kRetryMs = 500;      // a beat that cannot start now tries again this soon

    // PH1 Mighty Blow: stock 14099 (+25 weapon, 75-125, a knockback), rescaled: a tank swing-class hit (the BRS
    // convention, gap 36: this WP's default, designer question). Stock timers: first at 15 s, then every 10 s.
    inline constexpr NH<float> kMightyBlowPct{ 25.f, 30.f };
    inline constexpr std::uint32_t kMightyBlowFirstMs = 15000;
    inline constexpr std::uint32_t kMightyBlowEveryMs = 10000;

    // PH2 Thunderclap: stock 15588 (10 yd, -40% movement, about -34% attack speed for 10 s, Magic), rescaled: a group
    // pulse on everyone in melee (gap 36 default). Stock timers: first at 12 s, then every 10 s.
    inline constexpr NH<float> kThunderclapPct{ 10.f, 12.f };
    inline constexpr std::uint32_t kThunderclapFirstMs = 12000;
    inline constexpr std::uint32_t kThunderclapEveryMs = 10000;
    inline constexpr float kThunderclapRadiusYd = 10.f;
    inline constexpr std::int32_t kThunderclapSlowPct = -40;
    inline constexpr std::int32_t kThunderclapAttackSpeedPct = -34;
    inline constexpr std::uint32_t kThunderclapMs = 10000;

    // PH3 Fireball Volley: stock 15285 (20 yd), rescaled: healer load in the second half (gap 36 default). From 50%
    // health (stock HealthBelowPct(51)): the first at once, then every 10 s.
    inline constexpr NH<float> kVolleyPct{ 10.f, 15.f };
    inline constexpr std::uint32_t kVolleyEveryMs = 10000;
    inline constexpr float kVolleyHealthPct = 51.f;            // HealthBelowPct(51): at or below 50%
    inline constexpr float kVolleyRadiusYd = 20.f;

    // PH4 Throw Out: first at 10 s, then every 20 s (heroic 15 s). He grabs the top damage dealer of the last 10 s (the
    // ledger: pets count for their owner; never his current victim, never the last one thrown), holds them 1 s and
    // throws them 15-25 yd onto open floor (never onto a table). The 6 yd landing circle shows as the grab starts;
    // grab and flight total 2 s. The thrown player 15% / 25% (no Weakened: not a failure); anyone else in the circle
    // 30% / 45% + Weakened.
    inline constexpr std::uint32_t kThrowFirstMs = 10000;
    inline constexpr NH<std::uint32_t> kThrowEveryMs{ 20000, 15000 };
    inline constexpr std::uint32_t kLedgerWindowMs = 10000;
    inline constexpr std::uint32_t kGrabMs = 1000;
    inline constexpr std::uint32_t kFlightMs = 1000;
    inline constexpr std::uint32_t kThrowWarnMs = kGrabMs + kFlightMs;
    inline constexpr std::uint32_t kGrabAuraMs = 1500;           // the hold's aura (removed at the throw)
    inline constexpr float kThrowMinYd = 15.f;
    inline constexpr float kThrowMaxYd = 25.f;
    inline constexpr float kLandingRadiusYd = 6.f;
    inline constexpr NH<float> kThrownPct{ 15.f, 25.f };
    inline constexpr NH<float> kLandingPct{ 30.f, 45.f };
    inline constexpr float kThrowMinSpeedXY = 8.f;

    // The flight's horizontal speed: `distance` covered in kFlightMs (at least kThrowMinSpeedXY). The kit's JumpTo
    // then arcs it so it lands in that time.
    constexpr float ThrowSpeedXY(float distance)
    {
        float const s = distance * 1000.f / float(kFlightMs);
        return s < kThrowMinSpeedXY ? kThrowMinSpeedXY : s;
    }

    // Who may be thrown (the ledger's filter): not his current victim, not the player thrown last, on the bar floor.
    constexpr bool ThrowEligible(bool isVictim, bool isLastThrown, bool onFloor)
    {
        return !isVictim && !isLastThrown && onFloor;
    }

    // PH5 Last Call: first at 20 s, then every 30 s (heroic 25 s): yell line 2 and a 3 s cast while he stands still,
    // then a pulse that knocks back everyone within 10 yd (heroic 12 yd), the tank included: 25% / 40% + Weakened. The
    // knockback (this WP's default speeds, designer question) carries a player about 12 yd.
    inline constexpr std::uint32_t kLastCallFirstMs = 20000;
    inline constexpr NH<std::uint32_t> kLastCallEveryMs{ 30000, 25000 };
    inline constexpr std::uint32_t kLastCallCastMs = 3000;
    inline constexpr NH<float> kLastCallRadiusYd{ 10.f, 12.f };
    inline constexpr NH<float> kLastCallPct{ 25.f, 40.f };
    inline constexpr float kLastCallKnockSpeedXY = 15.f;
    inline constexpr float kLastCallKnockSpeedZ = 8.f;

    // PH6 Property Damage (heroic): a player knocked (Last Call or Mighty Blow) to within about 2 yd of a table
    // smashes it: 25% + Weakened to that player, one Outrage stack on Phalanx (+15% damage for the fight, 5 at most),
    // two Rowdy Patrons (8,000) at the table, the table's chairs gone until the fight ends. Each table breaks once.
    inline constexpr float kSmashPct = 25.f;
    inline constexpr float kTableRadiusYd = 1.5f;              // a table's top around its spot
    inline constexpr float kSmashReachYd = 2.f;                // "within about 2 yd of a table"
    inline constexpr float kSmashZBandYd = 3.f;                // on the bar floor's height (in the air too)
    inline constexpr std::uint32_t kSmashGraceMs = 200;        // the knock has started to move them
    inline constexpr std::uint32_t kSmashWindowMs = 2500;      // the flight and the landing
    inline constexpr std::int32_t kOutragePctPerStack = 15;
    inline constexpr std::uint32_t kOutrageCap = 5;
    inline constexpr std::uint32_t kPatronsPerTable = 2;
    inline constexpr NH<std::uint32_t> kPatronHealth{ 8000, 8000 };    // spawned on heroic only; the normal row too
    inline constexpr std::uint32_t kPatronDespawnMs = 10000;   // a dead patron's corpse
    inline constexpr std::uint32_t kSplintersLookMs = 3000;    // the stalker that carries the wood chips

    // Outrage's scale on his damage (S4: "+15% damage for the fight"): the aura raises his melee; the script scales the
    // two new mechanics' percents by the same factor (the kept stock spells ignore caster modifiers, rule 2).
    constexpr float OutrageScale(std::uint32_t stacks)
    {
        std::uint32_t const n = stacks < kOutrageCap ? stacks : kOutrageCap;
        return 1.f + float(kOutragePctPerStack) / 100.f * float(n);
    }

    // The tank's open Spot by the door (NM 4.2 / spec gap 30): 5.5 yd from the door node, 9 yd from T2; no table
    // behind the tank while he faces Phalanx coming from the door. Bots: a hidden tank-only Park circle.
    inline constexpr Point3 kTankSpot{ 864.8f, -217.8f, -43.6f };
    inline constexpr float kParkRadiusYd = 4.f;
    inline constexpr std::uint32_t kParkRenewMs = 20000;

    // ----------------------------------------------------------------------------------------------------------------
    // The bar's upper floor (NM 4.2: z -46 to -41; the floor at -43.6 to -43.8)
    // ----------------------------------------------------------------------------------------------------------------

    inline constexpr float kBarFloorZ = -43.65f;
    inline constexpr float kFloorZBandYd = 1.5f;               // the lower level is 6 yd below: never this floor
    inline constexpr float kBarFloorZMin = kBarFloorZ - kFloorZBandYd;
    inline constexpr float kBarFloorZMax = kBarFloorZ + kFloorZBandYd;

    // The throw floor: the main upper floor from the navmesh component around (870, -210), 1.5-2 yd inside its edges,
    // x 850-900 (about 1,640 sq yd of the 1,945 within 30 yd). The +y edge is the rail over the lower level; the door
    // alcove (x 867-876, y -223 to -236) and the corner where Phalanx stands are left out.
    inline constexpr std::array<Vec2, 22> kThrowFloorPolygon{ {
        { 900.f, -188.f }, { 895.f, -179.f }, { 890.f, -171.f }, { 885.f, -174.f }, { 880.f, -177.f },
        { 875.f, -179.f }, { 870.f, -182.f }, { 865.f, -185.f }, { 860.f, -188.f }, { 855.f, -191.f },
        { 850.f, -194.f }, { 850.f, -229.f }, { 855.f, -226.f }, { 860.f, -223.f }, { 865.f, -221.f },
        { 870.f, -217.f }, { 875.f, -214.f }, { 880.f, -211.f }, { 885.f, -209.f }, { 890.f, -206.f },
        { 895.f, -203.f }, { 900.f, -200.f },
    } };

    // The throw pick's floor.
    inline DungeonKit::Arena ThrowFloor()
    {
        return DungeonKit::Arena(DungeonKit::ArenaRegion::Polygon(
            std::vector<Vec2>(kThrowFloorPolygon.begin(), kThrowFloorPolygon.end()), kBarFloorZMin, kBarFloorZMax));
    }

    // The door alcove (navmesh, on the bar floor's height, x 867-881, y -224 to -236): out of the throw floor, but the
    // short Last Call escape for melee behind him while he is tanked at the door node (R-FIXES MN-1).
    inline constexpr std::array<Vec2, 4> kDoorAlcovePolygon{ {
        { 867.f, -224.f }, { 881.f, -229.f }, { 881.f, -236.f }, { 869.f, -236.f },
    } };

    // The bots' hard bounds (npc_phalanx_rework.cpp BarFloorBounds: Last Call, the Throw Out landing, the tank's Park):
    // the throw floor plus the door alcove, both on the bar floor's z band, so a planned spot never leaves the upper
    // floor (the stairs and the lower level below it are out of the healer's range and sight of the tank;
    // PHALANX-DIAG).
    inline DungeonKit::Arena BotFloor()
    {
        DungeonKit::Arena floor = ThrowFloor();
        floor.Add(DungeonKit::ArenaRegion::Polygon(
            std::vector<Vec2>(kDoorAlcovePolygon.begin(), kDoorAlcovePolygon.end()), kBarFloorZMin, kBarFloorZMax));
        return floor;
    }

    // The seven tables (NM 4.2, the chair clusters at z -43.7 [db]). Index 0-6 = T1-T7.
    inline constexpr std::size_t kTableCount = 7;
    inline constexpr std::array<Vec2, kTableCount> kTables{ {
        { 862.2f, -197.5f }, { 874.4f, -213.5f }, { 884.7f, -209.0f }, { 890.0f, -205.9f }, { 876.1f, -203.7f },
        { 855.0f, -205.0f }, { 896.0f, -201.5f },
    } };

    // A pillar on the floor's south end (a navmesh hole about (850-854, -208 to -213)): no landing there.
    inline constexpr Vec2 kPillar{ 852.0f, -210.5f };
    inline constexpr float kPillarRadiusYd = 2.5f;

    // A landing keeps this far from a table's spot (the table and its chairs; "never onto a table").
    inline constexpr float kTableAvoidYd = 3.5f;

    // Measured open spots (navmesh, 6+ yd from every table, 3+ yd inside the floor): the floor pick's fallbacks.
    inline constexpr std::array<Vec2, 8> kFixedLandings{ {
        { 885.f, -189.f }, { 875.f, -191.f }, { 865.f, -208.f }, { 857.f, -214.f }, { 884.f, -199.f },
        { 889.f, -179.f }, { 895.f, -190.f }, { 854.f, -197.f },
    } };

    // The chairs [db gameobject, type 7, z -43.7]: one spawn per entry, each beside the table it belongs to (the
    // nearest table spot, within 6.5 yd). A smashed table's chairs despawn until the fight ends.
    struct Chair
    {
        std::uint32_t entry = 0;
        Vec2 at;
        std::uint8_t table = 0;     // 0-6
    };

    inline constexpr std::array<Chair, 31> kChairs{ {
        { 170454, { 861.9f, -198.1f }, 0 }, { 174537, { 862.5f, -196.1f }, 0 }, { 174536, { 864.6f, -195.5f }, 0 },
        { 170453, { 864.7f, -197.9f }, 0 }, { 174522, { 857.5f, -199.7f }, 0 },
        { 174518, { 871.0f, -211.2f }, 1 }, { 174519, { 872.1f, -213.2f }, 1 }, { 174514, { 873.2f, -214.9f }, 1 },
        { 174515, { 874.4f, -216.9f }, 1 }, { 174513, { 874.8f, -211.6f }, 1 }, { 174512, { 875.8f, -213.3f }, 1 },
        { 174516, { 877.0f, -215.3f }, 1 }, { 174517, { 873.6f, -209.6f }, 1 },
        { 174528, { 883.0f, -208.1f }, 2 }, { 174523, { 884.4f, -210.9f }, 2 }, { 174526, { 885.1f, -207.0f }, 2 },
        { 174524, { 886.5f, -209.8f }, 2 },
        { 174529, { 888.2f, -205.1f }, 3 }, { 174525, { 889.6f, -207.8f }, 3 }, { 174527, { 890.3f, -204.0f }, 3 },
        { 174530, { 891.7f, -206.7f }, 3 },
        { 174538, { 875.0f, -203.6f }, 4 }, { 170455, { 877.2f, -203.7f }, 4 },
        { 174521, { 852.3f, -205.1f }, 5 }, { 174520, { 853.4f, -208.0f }, 5 }, { 170451, { 857.4f, -203.2f }, 5 },
        { 174534, { 891.7f, -198.8f }, 6 }, { 174532, { 894.6f, -203.4f }, 6 }, { 174533, { 894.6f, -197.7f }, 6 },
        { 174531, { 897.5f, -202.3f }, 6 }, { 174535, { 902.3f, -200.2f }, 6 },
    } };
    inline constexpr float kChairSearchYd = 80.f;      // from Phalanx: every chair of the floor

    inline std::vector<std::uint32_t> ChairEntriesOf(std::size_t table)
    {
        std::vector<std::uint32_t> out;
        for (Chair const& c : kChairs)
            if (c.table == table)
                out.push_back(c.entry);
        return out;
    }

    inline std::vector<std::uint32_t> AllChairEntries()
    {
        std::vector<std::uint32_t> out;
        for (Chair const& c : kChairs)
            out.push_back(c.entry);
        return out;
    }

    // The nearest table's index to `p`.
    inline std::size_t NearestTable(Vec2 p)
    {
        std::size_t best = 0;
        for (std::size_t i = 1; i < kTableCount; ++i)
            if (DungeonKit::Distance(kTables[i], p) < DungeonKit::Distance(kTables[best], p))
                best = i;
        return best;
    }

    // The broken tables of a fight (bit i = T(i+1)).
    struct TableState
    {
        std::uint8_t broken = 0;

        constexpr bool Broken(std::size_t i) const { return i < kTableCount && ((broken >> i) & 1u); }
        constexpr void Break(std::size_t i)
        {
            if (i < kTableCount)
                broken = std::uint8_t(broken | (1u << i));
        }
        constexpr std::uint32_t Count() const
        {
            std::uint32_t n = 0;
            for (std::size_t i = 0; i < kTableCount; ++i)
                n += Broken(i) ? 1u : 0u;
            return n;
        }
    };

    // The table a knocked unit at (p, z) smashes: the nearest unbroken one whose spot is within kTableRadiusYd +
    // kSmashReachYd, the unit on the bar floor's height (kSmashZBandYd: in the air too). nullopt: none.
    inline std::optional<std::size_t> SmashedTable(Vec2 p, float z, TableState const& tables)
    {
        if (std::fabs(z - kBarFloorZ) > kSmashZBandYd)
            return std::nullopt;
        std::optional<std::size_t> best;
        float bestD = kTableRadiusYd + kSmashReachYd;
        for (std::size_t i = 0; i < kTableCount; ++i)
        {
            if (tables.Broken(i))
                continue;
            float const d = DungeonKit::Distance(kTables[i], p);
            if (d <= bestD)
            {
                best = i;
                bestD = d;
            }
        }
        return best;
    }

    // A knock is watched from kSmashGraceMs after it to kSmashWindowMs after it.
    constexpr bool KnockWatched(std::uint64_t nowMs, std::uint64_t knockMs)
    {
        return nowMs >= knockMs + kSmashGraceMs && nowMs <= knockMs + kSmashWindowMs;
    }

    constexpr bool KnockExpired(std::uint64_t nowMs, std::uint64_t knockMs)
    {
        return nowMs > knockMs + kSmashWindowMs;
    }

    // Where a smashed table's two Rowdy Patrons appear: either side of its spot, along x.
    inline std::array<Vec2, kPatronsPerTable> PatronSpots(std::size_t table)
    {
        Vec2 const t = kTables[table < kTableCount ? table : 0];
        return { { { t.x + 1.f, t.y }, { t.x - 1.f, t.y } } };
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Timeline: the five clocks on the AI's own clock
    // ----------------------------------------------------------------------------------------------------------------

    enum class Beat : std::uint8_t
    {
        ThrowOut,
        LastCall,
        Thunderclap,
        MightyBlow,
        Volley,
    };
    inline constexpr std::size_t kBeatCount = 5;

    constexpr std::uint32_t EveryMs(Beat beat, bool heroic)
    {
        switch (beat)
        {
            case Beat::ThrowOut:    return kThrowEveryMs(heroic);
            case Beat::LastCall:    return kLastCallEveryMs(heroic);
            case Beat::Thunderclap: return kThunderclapEveryMs;
            case Beat::MightyBlow:  return kMightyBlowEveryMs;
            case Beat::Volley:      return kVolleyEveryMs;
        }
        return kRetryMs;
    }

    // Throw Out and Last Call never run at once: neither starts while the other is going on (a throw from the grab to
    // the landing, Last Call for its cast). The three stock casts wait for Last Call's bar only.
    constexpr bool MayStart(Beat beat, bool throwing, bool castingLastCall)
    {
        switch (beat)
        {
            case Beat::ThrowOut:
            case Beat::LastCall:
                return !throwing && !castingLastCall;
            default:
                return !castingLastCall;
        }
    }

    struct Timeline
    {
        bool heroic = false;
        std::array<std::uint64_t, kBeatCount> at{};     // 0: not armed (the Volley until 50%)

        constexpr std::uint64_t& Slot(Beat beat) { return at[std::size_t(beat)]; }
        constexpr std::uint64_t At(Beat beat) const { return at[std::size_t(beat)]; }

        // The pull: Throw Out at 10 s, Thunderclap at 12 s, Mighty Blow at 15 s, Last Call at 20 s; the Volley waits.
        constexpr void Start(bool isHeroic, std::uint64_t nowMs)
        {
            heroic = isHeroic;
            at = {};
            Slot(Beat::ThrowOut) = nowMs + kThrowFirstMs;
            Slot(Beat::LastCall) = nowMs + kLastCallFirstMs;
            Slot(Beat::Thunderclap) = nowMs + kThunderclapFirstMs;
            Slot(Beat::MightyBlow) = nowMs + kMightyBlowFirstMs;
        }

        constexpr bool Due(Beat beat, std::uint64_t nowMs) const
        {
            std::uint64_t const t = At(beat);
            return t && nowMs >= t;
        }

        constexpr void Fired(Beat beat, std::uint64_t nowMs) { Slot(beat) = nowMs + EveryMs(beat, heroic); }
        constexpr void Retry(Beat beat, std::uint64_t nowMs) { Slot(beat) = nowMs + kRetryMs; }

        // The Volley from 50% health: the first one at once (stock 1 ms), once a pull. False when already armed.
        constexpr bool ArmVolley(std::uint64_t nowMs)
        {
            if (At(Beat::Volley))
                return false;
            Slot(Beat::Volley) = nowMs ? nowMs : 1;
            return true;
        }
    };
}

#endif
