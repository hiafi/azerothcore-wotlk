/*
 * mod-dungeon-bosses, Blackrock Depths, dungeon quests stage Q4 (.agents/plans/dungeon-quests/, plan section 8):
 * Marshal Windsor's escort for Jail Break! (quest 4322), a neutral dungeon quest ended by the Thorium Brotherhood dwarf
 * at the entrance. Bound by data: `creature_template.ScriptName` of 9023 (rev_dungeon_quests_blackrock_depths.sql).
 *
 * Source: the Jail Break! parts Blaymoira added to TrinityCore in 22413c016e (2008-12-22, "Adding parts for quest 4322
 * for future development": npc_marshal_windsor, npc_marshal_reginald_windsor, npc_dughal_stormwing,
 * npc_tobias_seecher and their instance data). They never ran: TrinityCore and AzerothCore kept them commented out
 * until AzerothCore deleted them in 6a95e6180 (#3229, 2020-12-24). This file is a rewrite on that base for the current
 * npc_escortAI: the original's lines, its two waypoint lists (re-checked against the map 230 navmesh, the long legs
 * split into navmesh points) and its flow, in one script on 9023 instead of two creatures (the geared Windsor is the
 * same unit, not a summoned 9682; it takes 9682's look and weapons).
 *
 * The flow (the original's, with the gaps filled in):
 *   Accept       4322 accepted at Windsor (or a holder of an incomplete 4322 standing next to him, e.g. after an
 *                instance reload): after kStartDelay, so the rest of the group can accept too, his cell opens and he
 *                runs. He refuses while High Interrogator Gerstahn, Lord Roccor or Houndmaster Grebmar is alive: the
 *                route crosses their rooms and Roccor's path, and a reworked boss must not be pulled by an NPC alone.
 *   Dughal       his first stop: the group opens Dughal Stormwing's cell (the Prison Cell Key, or a picked lock);
 *                Dughal thanks them and runs.
 *   Supply room  Windsor opens the supply room, the first ambush (three Anvilrage) runs in from the east hall, and he
 *                takes his gear from the crate (Reginald Windsor's look and weapons).
 *   Prisoners    four more cells. Jaz and Ograbisi, Shill Dinger and Crest Killer turn on the group the moment their
 *                cell opens and must die; the second ambush arrives with Crest Killer; Tobias Seecher thanks them and
 *                runs. At every cell Windsor waits for the group, and after kDoorWait he forces the door himself, so
 *                a group without the key or a rogue is never stuck.
 *   Exit         the Detention Block entrance, next to the Thorium Brotherhood dwarf: 4322 completes for every holder
 *                within kCreditRange (alive, or dead but not released), and Windsor leaves.
 *   Fail         Windsor dies, or no holder of the quest is within kLeashRange (alive or not released) for
 *                kLeashGrace (a wipe, everyone left): 4322 fails for every holder in the instance, the ambushers
 *                despawn, the seven doors close, the six prisoners respawn in their cells, and Windsor is back in his
 *                cell after kFailRespawn. Abandon and take the quest again to retry.
 *
 * Every step logs one INFO line "brd windsor <step>" (module.dungeonbosses).
 */

#include "BlackrockDepthsRework.h"
#include "Creature.h"
#include "CreatureData.h"
#include "DungeonKit.h"
#include "GameObject.h"
#include "InstanceScript.h"
#include "Log.h"
#include "Map.h"
#include "MotionMaster.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "QuestDef.h"
#include "ScriptedCreature.h"
#include "ScriptedEscortAI.h"
#include "SharedDefines.h"
#include "TemporarySummon.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace BrdWindsor
{
    enum Quests : uint32
    {
        QUEST_JAIL_BREAK                = 4322,
    };

    enum Creatures : uint32
    {
        NPC_MARSHAL_WINDSOR             = 9023,
        NPC_REGINALD_WINDSOR            = 9682,     // the geared Windsor of the original: his look and weapons
        NPC_DUGHAL_STORMWING            = 9022,     // friendly prisoner, cell 170562
        NPC_OGRABISI                    = 9677,     // hostile prisoner, cell 170568 (with Jaz)
        NPC_SHILL_DINGER                = 9678,     // hostile prisoner, cell 170569
        NPC_TOBIAS_SEECHER              = 9679,     // friendly prisoner, cell 170566
        NPC_CREST_KILLER                = 9680,     // hostile prisoner, cell 170567
        NPC_JAZ                         = 9681,     // hostile prisoner, cell 170568 (with Ograbisi)
        NPC_ANVILRAGE_WARDEN            = 8890,     // the ambushes: stock Detention Block guards
        NPC_ANVILRAGE_GUARDSMAN         = 8891,
        NPC_ANVILRAGE_OFFICER           = 8895,
    };

    enum GameObjects : uint32
    {
        GO_CELL_WINDSOR                 = 170563,
        GO_CELL_DUGHAL                  = 170562,
        GO_CELL_JAZ                     = 170568,
        GO_CELL_SHILL                   = 170569,
        GO_CELL_CREST                   = 170567,
        GO_CELL_TOBIAS                  = 170566,
        GO_SUPPLY_ROOM_DOOR             = 170561,
    };

    // creature_text groups of 9023 (rev_dungeon_quests_blackrock_depths.sql). The original's lines, with the last one
    // rewritten for the entrance turn-in (it sent the player to Marshal Maxwell).
    enum WindsorTexts : uint8
    {
        SAY_AGGRO                       = 0,    // three lines, one at random
        SAY_NOT_YET                     = 1,    // a boss of the route is alive
        SAY_ACCEPT                      = 2,    // the start delay
        SAY_START                       = 3,
        SAY_DUGHAL_CELL                 = 4,
        SAY_GET_HIM_OUT                 = 5,    // Dughal's and Tobias's cells open
        SAY_DUGHAL_FREED                = 6,
        SAY_SUPPLY_ROOM                 = 7,
        SAY_FOUND_GEAR                  = 8,
        SAY_GEARED_1                    = 9,
        SAY_GEARED_2                    = 10,
        SAY_JAZ_CELL                    = 11,
        SAY_JAZ_DEAD                    = 12,
        SAY_SHILL_CELL                  = 13,
        SAY_SHILL_DEAD_1                = 14,
        SAY_SHILL_DEAD_2                = 15,
        SAY_CREST_CELL                  = 16,
        SAY_CREST_FIGHT                 = 17,
        SAY_CREST_DEAD                  = 18,
        SAY_TOBIAS_FREED                = 19,
        SAY_EXIT_1                      = 20,
        SAY_EXIT_2                      = 21,
        SAY_FORCE_DOOR                  = 22,
    };

    // creature_text group 0 of the prisoners that speak (Dughal, Tobias, Ograbisi).
    uint8 constexpr SAY_PRISONER                    = 0;

    enum WindsorEvents : uint32
    {
        EVENT_BEGIN                     = 1,
        EVENT_GEAR_FOUND,
        EVENT_GEAR_ON,
        EVENT_GEAR_DONE,
        EVENT_SHILL_DONE,
        EVENT_EXIT_SPEECH,
        EVENT_EXIT_LEAVE,
        EVENT_AUTO_START_CHECK,     // every kAutoStartCheck while idle: a holder of an incomplete 4322 next to him
        EVENT_LEASH_CHECK,          // every kLeashCheck while pending or escorting: a holder within kLeashRange
        EVENT_LEASH_FAIL,           // armed by the first leash miss, cancelled by the next hit: fails the escort
        EVENT_FORCE_DOOR,           // kDoorWait after he reaches a closed cell: he opens it himself
        EVENT_AGGRO_COOLDOWN,       // no-op marker: while it is pending, no aggro line
    };

    // The stops of the route: what Windsor waits for at the last point of each leg.
    enum class Stop : uint8
    {
        None,
        DughalCell,
        SupplyDoor,
        Crate,
        JazCell,
        ShillCell,
        CrestCell,
        TobiasCell,
        Exit,
    };

    // What a cell stop is waiting for.
    enum class CellWait : uint8
    {
        None,
        Door,       // the group opens the cell (or Windsor forces it after kDoorWait)
        Prisoners,  // the hostile prisoners are dead
    };

    Milliseconds constexpr kStartDelay = 8s;
    Milliseconds constexpr kDoorWait = 30s;
    Milliseconds constexpr kLeashCheck = 1s;
    Milliseconds constexpr kLeashGrace = 15s;
    Milliseconds constexpr kAggroCooldown = 15s;
    Milliseconds constexpr kAutoStartCheck = 2s;
    float constexpr kLeashRange = 100.f;        // npc_escortAI's DEFAULT_MAX_PLAYER_DISTANCE
    float constexpr kCreditRange = 100.f;
    float constexpr kAutoStartRange = 10.f;     // the original's MoveInLineOfSight radius
    float constexpr kCellSearchRange = 30.f;    // a prisoner from Windsor's cell stop (16-23 yd, measured)
    float constexpr kPrisonerHomeSlack = 3.f;
    uint32 constexpr kAmbushCorpseMs = 300000;
    Seconds constexpr kFailRespawn = 60s;
    Seconds constexpr kDoneRespawn = 120s;

    // The Detention Block bosses on or beside the route (boss states of the rework instance).
    std::array<uint32, 3> constexpr kRouteBosses{ {
        BlackrockDepthsRework::BOSS_GERSTAHN, BlackrockDepthsRework::BOSS_ROCCOR,
        BlackrockDepthsRework::BOSS_GREBMAR } };

    std::array<uint32, 6> constexpr kPrisoners{ {
        NPC_DUGHAL_STORMWING, NPC_OGRABISI, NPC_SHILL_DINGER, NPC_TOBIAS_SEECHER, NPC_CREST_KILLER, NPC_JAZ } };

    std::array<uint32, 7> constexpr kDoors{ {
        GO_CELL_WINDSOR, GO_CELL_DUGHAL, GO_CELL_JAZ, GO_CELL_SHILL, GO_CELL_CREST, GO_CELL_TOBIAS,
        GO_SUPPLY_ROOM_DOOR } };

    struct RoutePoint
    {
        float x;
        float y;
        float z;
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The route, leg by leg; the last point of each leg is a stop. Windsor starts at his spawn (316.34, -225.53,
    // -77.73), so no leg repeats the previous leg's last point. The original's points are kept where the straight line
    // between two of them stays on the map 230 navmesh (mmtiles of ac-worldserver, read offline 2026-11-24) and the
    // original's long segments are split into navmesh points no more than 9 yd apart, each z on the navmesh's detail
    // surface, every segment checked at 0.25 yd steps (on the mesh, connected polygons, z within 1.5 yd). One repair:
    // the original's 156 yd line from the supply room to Jaz's cell crosses walls and follows the navmesh's path now.
    // ----------------------------------------------------------------------------------------------------------------
    std::array<RoutePoint, 21> constexpr kLegCellToDughal{ {
        { 318.54f, -219.40f, -77.69f }, { 320.75f, -213.26f, -77.91f }, { 322.96f, -207.13f, -77.51f },
        { 316.97f, -202.13f, -76.99f }, { 310.99f, -197.14f, -76.43f }, { 305.00f, -192.14f, -76.10f },
        { 299.01f, -187.15f, -75.85f }, { 293.02f, -182.15f, -75.74f }, { 287.04f, -177.16f, -75.48f },
        { 281.05f, -172.16f, -74.74f }, { 278.84f, -163.91f, -72.76f }, { 276.62f, -155.65f, -71.06f },
        { 274.40f, -147.39f, -70.80f }, { 272.19f, -139.14f, -70.58f }, { 276.00f, -131.46f, -69.24f },
        { 279.81f, -123.77f, -69.54f }, { 283.62f, -116.09f, -69.88f }, { 287.81f, -108.83f, -70.95f },
        { 291.99f, -101.56f, -71.98f }, { 296.18f, -94.30f, -73.41f }, { 294.57f, -93.11f, -74.17f },
    } };
    std::array<RoutePoint, 16> constexpr kLegDughalToSupplyDoor{ {
        { 299.50f, -88.41f, -75.02f }, { 304.44f, -83.71f, -75.67f }, { 309.38f, -79.01f, -75.76f },
        { 314.31f, -74.31f, -75.71f }, { 321.96f, -72.41f, -73.86f }, { 329.61f, -70.52f, -72.21f },
        { 337.26f, -68.62f, -70.71f }, { 344.92f, -66.72f, -68.95f }, { 352.57f, -64.83f, -67.82f },
        { 360.22f, -62.93f, -66.62f }, { 367.94f, -65.09f, -65.24f }, { 375.66f, -67.24f, -63.82f },
        { 383.38f, -69.40f, -62.85f }, { 389.99f, -67.86f, -62.30f }, { 395.49f, -69.94f, -62.12f },
        { 400.98f, -72.01f, -61.94f },
    } };
    std::array<RoutePoint, 5> constexpr kLegSupplyDoorToCrate{ {
        { 402.60f, -67.16f, -62.94f }, { 404.22f, -62.30f, -63.46f }, { 405.94f, -57.08f, -63.82f },
        { 407.65f, -51.86f, -63.82f }, { 403.61f, -51.71f, -63.82f },
    } };
    std::array<RoutePoint, 34> constexpr kLegCrateToJaz{ {
        { 406.33f, -54.87f, -63.82f }, { 404.40f, -61.60f, -63.56f }, { 406.19f, -67.75f, -62.96f },
        { 407.99f, -73.91f, -62.06f }, { 414.00f, -79.62f, -62.32f }, { 420.00f, -85.33f, -63.02f },
        { 424.67f, -86.80f, -62.81f }, { 429.34f, -88.27f, -64.09f }, { 437.27f, -88.73f, -62.97f },
        { 445.20f, -89.20f, -62.36f }, { 448.00f, -90.53f, -62.36f }, { 455.11f, -92.35f, -61.53f },
        { 462.22f, -94.18f, -61.43f }, { 469.33f, -96.00f, -61.42f }, { 476.44f, -96.00f, -62.09f },
        { 483.56f, -96.00f, -61.93f }, { 490.67f, -96.00f, -62.16f }, { 497.78f, -96.00f, -62.22f },
        { 504.89f, -96.00f, -62.22f }, { 512.00f, -96.00f, -62.49f }, { 519.11f, -96.00f, -62.73f },
        { 526.22f, -96.00f, -62.80f }, { 533.33f, -96.00f, -63.02f }, { 536.87f, -101.34f, -62.13f },
        { 540.40f, -106.67f, -61.42f }, { 546.87f, -112.80f, -62.24f }, { 553.34f, -118.94f, -61.82f },
        { 557.03f, -119.71f, -61.62f }, { 565.21f, -122.05f, -62.67f }, { 573.40f, -124.39f, -64.58f },
        { 580.24f, -126.36f, -66.64f }, { 587.07f, -128.32f, -68.15f }, { 593.91f, -130.29f, -68.86f },
        { 593.21f, -132.16f, -68.91f },
    } };
    std::array<RoutePoint, 8> constexpr kLegJazToShill{ {
        { 600.61f, -133.01f, -69.59f }, { 608.01f, -133.86f, -70.44f }, { 615.41f, -134.70f, -70.47f },
        { 622.81f, -135.55f, -71.76f }, { 626.77f, -140.80f, -71.40f }, { 630.72f, -146.04f, -70.42f },
        { 634.68f, -151.29f, -69.83f }, { 635.06f, -153.25f, -70.20f },
    } };
    std::array<RoutePoint, 28> constexpr kLegShillToCrest{ {
        { 640.11f, -158.03f, -70.63f }, { 645.15f, -162.82f, -70.82f }, { 650.20f, -167.60f, -71.67f },
        { 655.25f, -172.39f, -73.32f }, { 655.17f, -181.38f, -74.33f }, { 655.10f, -190.36f, -75.59f },
        { 655.02f, -199.34f, -76.67f }, { 654.94f, -208.33f, -77.89f }, { 654.87f, -217.31f, -80.19f },
        { 654.79f, -226.30f, -82.62f }, { 649.47f, -233.39f, -83.27f }, { 644.14f, -240.48f, -83.35f },
        { 638.82f, -247.58f, -83.27f }, { 633.50f, -254.67f, -83.27f }, { 628.17f, -261.76f, -83.41f },
        { 622.85f, -268.85f, -83.54f }, { 614.17f, -270.19f, -83.44f }, { 605.49f, -271.53f, -83.18f },
        { 596.81f, -272.88f, -82.36f }, { 588.13f, -274.22f, -81.21f }, { 579.45f, -275.56f, -80.13f },
        { 573.36f, -272.66f, -78.59f }, { 567.28f, -269.75f, -76.92f }, { 561.19f, -266.85f, -75.09f },
        { 556.76f, -262.54f, -72.86f }, { 552.34f, -258.23f, -71.44f }, { 547.91f, -253.92f, -70.10f },
        { 549.20f, -252.40f, -70.28f },
    } };
    std::array<RoutePoint, 3> constexpr kLegCrestToTobias{ {
        { 552.27f, -260.78f, -71.44f }, { 555.33f, -269.16f, -73.93f }, { 554.31f, -270.88f, -74.05f },
    } };
    std::array<RoutePoint, 39> constexpr kLegTobiasToExit{ {
        { 549.76f, -265.56f, -72.06f }, { 545.20f, -260.24f, -70.38f }, { 540.65f, -254.92f, -68.70f },
        { 536.10f, -249.60f, -66.96f }, { 533.07f, -243.01f, -66.41f }, { 530.04f, -236.42f, -64.26f },
        { 527.00f, -229.83f, -61.44f }, { 523.97f, -223.24f, -60.07f }, { 520.94f, -216.65f, -58.65f },
        { 519.07f, -208.16f, -58.27f }, { 517.20f, -199.67f, -58.88f }, { 515.33f, -191.18f, -58.85f },
        { 513.47f, -182.69f, -59.08f }, { 511.60f, -174.21f, -60.55f }, { 509.73f, -165.72f, -61.64f },
        { 507.86f, -157.23f, -61.98f }, { 505.99f, -148.74f, -61.96f }, { 504.01f, -140.33f, -61.83f },
        { 502.03f, -131.92f, -61.97f }, { 500.05f, -123.51f, -62.22f }, { 498.07f, -115.10f, -62.16f },
        { 496.09f, -106.69f, -62.03f }, { 494.11f, -98.29f, -62.16f }, { 492.13f, -89.88f, -62.22f },
        { 490.15f, -81.47f, -62.14f }, { 488.17f, -73.06f, -61.90f }, { 486.19f, -64.65f, -61.72f },
        { 484.21f, -56.24f, -62.00f }, { 481.91f, -47.87f, -62.83f }, { 479.60f, -39.50f, -64.22f },
        { 477.30f, -31.12f, -65.42f }, { 475.00f, -22.75f, -66.86f }, { 472.69f, -14.38f, -68.83f },
        { 470.39f, -6.01f, -69.83f }, { 466.57f, 1.36f, -70.49f }, { 462.74f, 8.73f, -70.62f },
        { 458.92f, 16.11f, -70.65f }, { 455.09f, 23.48f, -70.36f }, { 451.27f, 30.85f, -69.86f },
    } };

    // The ambushes: three Anvilrage each, on route points 25-30 yd from where Windsor stands, running at him. The
    // first comes from the east hall while he is in the supply room, the second down the ramp to Crest Killer's cell.
    struct AmbushSpawn
    {
        uint32 entry;
        RoutePoint at;
    };
    std::array<AmbushSpawn, 3> constexpr kSupplyAmbush{ {
        { NPC_ANVILRAGE_GUARDSMAN, { 420.00f, -85.33f, -63.02f } },
        { NPC_ANVILRAGE_GUARDSMAN, { 424.67f, -86.80f, -62.81f } },
        { NPC_ANVILRAGE_WARDEN, { 414.00f, -79.62f, -62.32f } },
    } };
    std::array<AmbushSpawn, 3> constexpr kCrestAmbush{ {
        { NPC_ANVILRAGE_GUARDSMAN, { 527.00f, -229.83f, -61.44f } },
        { NPC_ANVILRAGE_GUARDSMAN, { 523.97f, -223.24f, -60.07f } },
        { NPC_ANVILRAGE_OFFICER, { 530.04f, -236.42f, -64.26f } },
    } };

    // Where the freed friendly prisoners run before they vanish (route points outside their cells).
    RoutePoint constexpr kDughalRunTo{ 309.38f, -79.01f, -75.76f };
    RoutePoint constexpr kTobiasRunTo{ 540.65f, -254.92f, -68.70f };
}

using namespace BrdWindsor;

struct npc_brd_marshal_windsor : public npc_escortAI
{
    explicit npc_brd_marshal_windsor(Creature* creature) : npc_escortAI(creature), _summons(creature)
    {
        AddLeg(kLegCellToDughal, Stop::DughalCell);
        AddLeg(kLegDughalToSupplyDoor, Stop::SupplyDoor);
        AddLeg(kLegSupplyDoorToCrate, Stop::Crate);
        AddLeg(kLegCrateToJaz, Stop::JazCell);
        AddLeg(kLegJazToShill, Stop::ShillCell);
        AddLeg(kLegShillToCrest, Stop::CrestCell);
        AddLeg(kLegCrestToTobias, Stop::TobiasCell);
        AddLeg(kLegTobiasToExit, Stop::Exit);
        SetDespawnAtEnd(false);     // the exit speech, the credit and the leave are this script's
        SetDespawnAtFar(false);     // the leash below fails the quest and resets the cell block instead
    }

    void JustRespawned() override
    {
        _finished = false;
        npc_escortAI::JustRespawned();
        ResetCellBlock();   // back in a closed cell, the prisoners in theirs (after a success too)
    }

    void Reset() override
    {
        // Not while escorting, nor between the exit and the leave (an evade there must not drop the leave event).
        if (HasEscortState(STATE_ESCORT_ESCORTING) || _finished)
            return;

        _events.Reset();
        _pendingStart = false;
        _starter.Clear();
        _stop = Stop::None;
        _wait = CellWait::None;
        _waitDoor = 0;
        _waitDoorGuid.Clear();
        _lastAmbush.clear();
        _events.ScheduleEvent(EVENT_AUTO_START_CHECK, kAutoStartCheck);
        // Ungeared: his own look and no weapons (the geared look is 9682's, set at the crate).
        me->SetDisplayId(me->GetNativeDisplayId());
        me->LoadEquipment(0, true);
    }

    void sQuestAccept(Player* player, Quest const* quest) override
    {
        if (quest->GetQuestId() == QUEST_JAIL_BREAK)
            RequestStart(player, true);
    }

    void JustEngagedWith(Unit* /*who*/) override
    {
        if (!HasEscortState(STATE_ESCORT_ESCORTING) || _events.HasTimeUntilEvent(EVENT_AGGRO_COOLDOWN))
            return;
        Talk(SAY_AGGRO, GetPlayerForEscort());
        _events.ScheduleEvent(EVENT_AGGRO_COOLDOWN, kAggroCooldown);
    }

    void JustSummoned(Creature* summon) override
    {
        _summons.Summon(summon);
    }

    void SummonedCreatureDespawn(Creature* summon) override
    {
        _summons.Despawn(summon);
    }

    void JustDied(Unit* /*killer*/) override
    {
        // Not npc_escortAI::JustDied: Fail() fails the quest for every holder in the instance, not only the starter's
        // group.
        if (HasEscortState(STATE_ESCORT_ESCORTING) || _pendingStart)
            Fail("died");
    }

    void WaypointReached(uint32 pointId) override
    {
        Stop const stop = pointId < _stopAt.size() ? _stopAt[pointId] : Stop::None;
        if (stop == Stop::None)
            return;

        _stop = stop;
        Player* player = GetPlayerForEscort();
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor stop {} (waypoint {})", static_cast<uint32>(stop), pointId);
        switch (stop)
        {
            case Stop::DughalCell:
                Talk(SAY_DUGHAL_CELL, player);
                WaitForDoor(GO_CELL_DUGHAL);
                break;
            case Stop::SupplyDoor:
                Talk(SAY_SUPPLY_ROOM, player);
                SetDoor(GO_SUPPLY_ROOM_DOOR, true);
                SpawnAmbush(kSupplyAmbush);
                break;
            case Stop::Crate:
                SetEscortPaused(true);
                me->SetEmoteState(EMOTE_STATE_USE_STANDING);
                _events.ScheduleEvent(EVENT_GEAR_FOUND, 2s);
                break;
            case Stop::JazCell:
                Talk(SAY_JAZ_CELL, player);
                WaitForDoor(GO_CELL_JAZ);
                break;
            case Stop::ShillCell:
                Talk(SAY_SHILL_CELL, player);
                WaitForDoor(GO_CELL_SHILL);
                break;
            case Stop::CrestCell:
                Talk(SAY_CREST_CELL, player);
                WaitForDoor(GO_CELL_CREST);
                break;
            case Stop::TobiasCell:
                Talk(SAY_GET_HIM_OUT, player);
                WaitForDoor(GO_CELL_TOBIAS);
                break;
            case Stop::Exit:
                SetEscortPaused(true);
                Finish();
                break;
            default:
                break;
        }
    }

    void UpdateEscortAI(uint32 diff) override
    {
        _events.Update(diff);
        while (uint32 eventId = _events.ExecuteEvent())
            HandleEvent(eventId);

        if (HasEscortState(STATE_ESCORT_ESCORTING) && _wait != CellWait::None)
            UpdateCellWait();

        if (!UpdateVictim())
            return;

        DoMeleeAttackIfReady();
    }

private:
    template <std::size_t N>
    void AddLeg(std::array<RoutePoint, N> const& leg, Stop stop)
    {
        for (RoutePoint const& p : leg)
        {
            uint32 const id = static_cast<uint32>(_stopAt.size());
            AddWaypoint(id, p.x, p.y, p.z);
            _stopAt.push_back(Stop::None);
        }
        _stopAt.back() = stop;
    }

    // An eligible player: holds an incomplete 4322 and is alive, or dead but not released (no corpse yet).
    static bool IsEscortee(Player const* player)
    {
        return player && player->GetQuestStatus(QUEST_JAIL_BREAK) == QUEST_STATUS_INCOMPLETE
            && (player->IsAlive() || !player->GetCorpse());
    }

    bool RouteClear() const
    {
        InstanceScript* instance = me->GetInstanceScript();
        if (!instance)
            return true;
        for (uint32 boss : kRouteBosses)
            if (instance->GetBossState(boss) != DONE)
                return false;
        return true;
    }

    // `speak`: say why he refuses (only on an accept, the player's own interaction; the auto-start stays silent).
    void RequestStart(Player* player, bool speak)
    {
        if (HasEscortState(STATE_ESCORT_ESCORTING) || _pendingStart || !me->IsAlive() || me->IsInCombat())
            return;

        if (!RouteClear())
        {
            if (speak)
            {
                Talk(SAY_NOT_YET, player);
                LOG_INFO(DungeonKit::kLogCategory, "brd windsor refused {}: a Detention Block boss is alive",
                    player->GetName());
            }
            return;
        }

        _pendingStart = true;
        _starter = player->GetGUID();
        _events.CancelEvent(EVENT_LEASH_FAIL);
        _events.RescheduleEvent(EVENT_LEASH_CHECK, kLeashCheck);
        Talk(SAY_ACCEPT, player);
        _events.ScheduleEvent(EVENT_BEGIN, kStartDelay);
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor accepted by {}, start in {} ms", player->GetName(),
            kStartDelay.count());
    }

    void Begin()
    {
        _pendingStart = false;
        Player* starter = ObjectAccessor::GetPlayer(*me, _starter);
        if (!IsEscortee(starter) || !me->IsWithinDistInMap(starter, kLeashRange))
            starter = FindEscortee(kLeashRange);
        if (!starter)
        {
            LOG_INFO(DungeonKit::kLogCategory, "brd windsor start dropped: no holder of 4322 near him");
            return;
        }

        ResetCellBlock();
        SetDoor(GO_CELL_WINDSOR, true);
        me->SetWalk(false);
        Start(true, starter->GetGUID(), sObjectMgr->GetQuestTemplate(QUEST_JAIL_BREAK));
        if (!HasEscortState(STATE_ESCORT_ESCORTING))
        {
            LOG_INFO(DungeonKit::kLogCategory, "brd windsor start refused by the escort base (in combat?)");
            return;
        }
        me->SetFaction(FACTION_ESCORTEE_N_NEUTRAL_ACTIVE);
        Talk(SAY_START, starter);
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor start, escorting {}", starter->GetName());
    }

    Player* FindEscortee(float range) const
    {
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (IsEscortee(player) && me->IsWithinDistInMap(player, range))
                return player;
        }
        return nullptr;
    }

    // After an instance reload or a lost start, a holder of an incomplete 4322 standing next to him starts it again.
    void CheckAutoStart()
    {
        if (HasEscortState(STATE_ESCORT_ESCORTING) || _pendingStart || !me->IsAlive())
            return;
        if (Player* player = FindEscortee(kAutoStartRange))
            RequestStart(player, false);
    }

    // A holder in range cancels the pending fail; the first miss arms it, so kLeashGrace of misses in a row fails.
    void CheckLeash()
    {
        if (FindEscortee(kLeashRange))
            _events.CancelEvent(EVENT_LEASH_FAIL);
        else if (!_events.HasTimeUntilEvent(EVENT_LEASH_FAIL))
            _events.ScheduleEvent(EVENT_LEASH_FAIL, kLeashGrace);
    }

    GameObject* FindDoor(uint32 entry) const
    {
        for (auto const& [spawnId, go] : me->GetMap()->GetGameObjectBySpawnIdStore())
            if (go && go->GetEntry() == entry)
                return go;
        return nullptr;
    }

    void SetDoor(uint32 entry, bool open)
    {
        if (GameObject* door = FindDoor(entry))
            door->SetGoState(open ? GO_STATE_ACTIVE : GO_STATE_READY);
    }

    // The door Windsor waits at is open (a missing door counts as open: nothing to wait for).
    bool WaitDoorOpen() const
    {
        GameObject const* door = ObjectAccessor::GetGameObject(*me, _waitDoorGuid);
        return !door || door->GetGoState() != GO_STATE_READY;
    }

    void WaitForDoor(uint32 entry)
    {
        SetEscortPaused(true);
        _wait = CellWait::Door;
        _waitDoor = entry;
        GameObject const* door = FindDoor(entry);
        _waitDoorGuid = door ? door->GetGUID() : ObjectGuid::Empty;
        _events.RescheduleEvent(EVENT_FORCE_DOOR, kDoorWait);
    }

    void UpdateCellWait()
    {
        if (_wait == CellWait::Door)
        {
            if (!WaitDoorOpen())
                return;     // EVENT_FORCE_DOOR opens it after kDoorWait
            _events.CancelEvent(EVENT_FORCE_DOOR);
            CellOpened();
            return;
        }

        if (_wait == CellWait::Prisoners && !AnyHostilePrisonerAlive())
            PrisonersDead();
    }

    void CellOpened()
    {
        Player* player = GetPlayerForEscort();
        switch (_stop)
        {
            case Stop::DughalCell:
                FreePrisoner(NPC_DUGHAL_STORMWING, kDughalRunTo, player);
                Talk(SAY_GET_HIM_OUT, player);
                Talk(SAY_DUGHAL_FREED, player, 4s);
                Resume();
                break;
            case Stop::JazCell:
                TurnPrisoner(NPC_OGRABISI, player, true);
                TurnPrisoner(NPC_JAZ, player, false);
                _wait = CellWait::Prisoners;
                break;
            case Stop::ShillCell:
                TurnPrisoner(NPC_SHILL_DINGER, player, false);
                _wait = CellWait::Prisoners;
                break;
            case Stop::CrestCell:
                TurnPrisoner(NPC_CREST_KILLER, player, false);
                Talk(SAY_CREST_FIGHT, player);
                SpawnAmbush(kCrestAmbush);
                _wait = CellWait::Prisoners;
                break;
            case Stop::TobiasCell:
                FreePrisoner(NPC_TOBIAS_SEECHER, kTobiasRunTo, player);
                Talk(SAY_TOBIAS_FREED, player, 4s);
                Resume();
                break;
            default:
                Resume();
                break;
        }
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor cell open at stop {}", static_cast<uint32>(_stop));
    }

    void PrisonersDead()
    {
        Player* player = GetPlayerForEscort();
        switch (_stop)
        {
            case Stop::JazCell:
                Talk(SAY_JAZ_DEAD, player);
                Resume();
                break;
            case Stop::ShillCell:
                Talk(SAY_SHILL_DEAD_1, player);
                _wait = CellWait::None;
                _events.ScheduleEvent(EVENT_SHILL_DONE, 4s);
                return;
            case Stop::CrestCell:
                Talk(SAY_CREST_DEAD, player);
                Resume();
                break;
            default:
                Resume();
                break;
        }
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor prisoners dead at stop {}", static_cast<uint32>(_stop));
    }

    void Resume()
    {
        _wait = CellWait::None;
        _waitDoor = 0;
        _waitDoorGuid.Clear();
        SetEscortPaused(false);
    }

    // The prisoners of the current cell stop that turn on the group and must die (the Crest stop also counts its
    // ambush, so Windsor moves on once the hall is quiet).
    bool AnyHostilePrisonerAlive() const
    {
        std::array<uint32, 2> entries{ { 0, 0 } };
        switch (_stop)
        {
            case Stop::JazCell:
                entries = { { NPC_OGRABISI, NPC_JAZ } };
                break;
            case Stop::ShillCell:
                entries = { { NPC_SHILL_DINGER, 0 } };
                break;
            case Stop::CrestCell:
                entries = { { NPC_CREST_KILLER, 0 } };
                break;
            default:
                break;
        }
        for (uint32 entry : entries)
            if (Creature* prisoner = entry ? me->FindNearestCreature(entry, kCellSearchRange * 2.f, true) : nullptr)
                if (prisoner->GetFaction() == FACTION_MONSTER)
                    return true;
        if (_stop == Stop::CrestCell)
            for (ObjectGuid const& guid : _lastAmbush)
                if (Creature* add = ObjectAccessor::GetCreature(*me, guid))
                    if (add->IsAlive())
                        return true;
        return false;
    }

    void TurnPrisoner(uint32 entry, Player* player, bool speaks)
    {
        Creature* prisoner = me->FindNearestCreature(entry, kCellSearchRange, true);
        if (!prisoner)
            return;
        prisoner->SetFaction(FACTION_MONSTER);
        if (speaks && prisoner->IsAIEnabled)
            prisoner->AI()->Talk(SAY_PRISONER, player);
        Unit* target = prisoner->SelectNearestPlayer(kCellSearchRange * 2.f);
        if (!target)
            target = me;
        if (prisoner->IsAIEnabled)
            prisoner->AI()->AttackStart(target);
    }

    void FreePrisoner(uint32 entry, RoutePoint const& runTo, Player* player)
    {
        Creature* prisoner = me->FindNearestCreature(entry, kCellSearchRange, true);
        if (!prisoner)
            return;
        if (prisoner->IsAIEnabled)
            prisoner->AI()->Talk(SAY_PRISONER, player);
        prisoner->SetWalk(false);
        prisoner->GetMotionMaster()->MovePoint(0, runTo.x, runTo.y, runTo.z);
        prisoner->DespawnOrUnsummon(6s);
    }

    template <std::size_t N>
    void SpawnAmbush(std::array<AmbushSpawn, N> const& ambush)
    {
        _lastAmbush.clear();
        for (AmbushSpawn const& spawn : ambush)
        {
            float const o = me->GetAngle(spawn.at.x, spawn.at.y) + float(M_PI);
            Creature* add = me->SummonCreature(spawn.entry, spawn.at.x, spawn.at.y, spawn.at.z, o,
                TEMPSUMMON_CORPSE_TIMED_DESPAWN, kAmbushCorpseMs);
            if (!add)
                continue;
            _lastAmbush.push_back(add->GetGUID());
            if (add->IsAIEnabled)
                add->AI()->AttackStart(me);
        }
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor ambush at stop {}", static_cast<uint32>(_stop));
    }

    void HandleEvent(uint32 eventId)
    {
        Player* player = GetPlayerForEscort();
        switch (eventId)
        {
            case EVENT_BEGIN:
                Begin();
                break;
            case EVENT_AUTO_START_CHECK:
                if (_finished)
                    break;
                CheckAutoStart();
                _events.Repeat(kAutoStartCheck);
                break;
            case EVENT_LEASH_CHECK:
                if (_finished || (!HasEscortState(STATE_ESCORT_ESCORTING) && !_pendingStart))
                    break;
                CheckLeash();
                _events.Repeat(kLeashCheck);
                break;
            case EVENT_LEASH_FAIL:
                if (!_finished && (HasEscortState(STATE_ESCORT_ESCORTING) || _pendingStart))
                    Fail("no holder of the quest within range");
                break;
            case EVENT_FORCE_DOOR:
                if (!HasEscortState(STATE_ESCORT_ESCORTING) || _wait != CellWait::Door || WaitDoorOpen())
                    break;
                Talk(SAY_FORCE_DOOR, player);
                SetDoor(_waitDoor, true);   // UpdateCellWait sees it open on the next tick
                LOG_INFO(DungeonKit::kLogCategory, "brd windsor forced cell {}", _waitDoor);
                break;
            case EVENT_GEAR_FOUND:
                Talk(SAY_FOUND_GEAR, player);
                _events.ScheduleEvent(EVENT_GEAR_ON, 2s);
                break;
            case EVENT_GEAR_ON:
                GearUp();
                me->SetEmoteState(EMOTE_ONESHOT_NONE);
                Talk(SAY_GEARED_1, player);
                _events.ScheduleEvent(EVENT_GEAR_DONE, 4s);
                break;
            case EVENT_GEAR_DONE:
                Talk(SAY_GEARED_2, player);
                SetEscortPaused(false);
                break;
            case EVENT_SHILL_DONE:
                Talk(SAY_SHILL_DEAD_2, player);
                Resume();
                break;
            case EVENT_EXIT_SPEECH:
                Talk(SAY_EXIT_2, player);
                _events.ScheduleEvent(EVENT_EXIT_LEAVE, 10s);
                break;
            case EVENT_EXIT_LEAVE:
                _summons.DespawnAll();
                me->DespawnOrUnsummon(0ms, kDoneRespawn);
                break;
            default:
                break;
        }
    }

    // The original swapped Windsor for a summoned Marshal Reginald Windsor (9682) at the crate; here he keeps his unit
    // and takes 9682's look and weapons (creature_template_model and creature_equip_template of 9682).
    void GearUp()
    {
        if (CreatureTemplate const* geared = sObjectMgr->GetCreatureTemplate(NPC_REGINALD_WINDSOR))
            if (CreatureModel const* model = geared->GetFirstValidModel())
                me->SetDisplayId(model->CreatureDisplayID);
        int8 equipmentId = 1;
        if (EquipmentInfo const* gear = sObjectMgr->GetEquipmentInfo(NPC_REGINALD_WINDSOR, equipmentId))
            for (uint8 slot = 0; slot < MAX_EQUIPMENT_ITEMS; ++slot)
                me->SetVirtualItem(slot, gear->ItemEntry[slot]);
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor geared");
    }

    void Finish()
    {
        _finished = true;
        Talk(SAY_EXIT_1, GetPlayerForEscort());
        uint32 credited = 0;
        for (auto const& ref : me->GetMap()->GetPlayers())
        {
            Player* player = ref.GetSource();
            if (IsEscortee(player) && me->IsWithinDistInMap(player, kCreditRange))
            {
                player->AreaExploredOrEventHappens(QUEST_JAIL_BREAK);
                ++credited;
            }
        }
        RemoveEscortState(STATE_ESCORT_ESCORTING);
        _events.ScheduleEvent(EVENT_EXIT_SPEECH, 4s);
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor reached the exit, {} player(s) credited", credited);
    }

    void Fail(char const* why)
    {
        LOG_INFO(DungeonKit::kLogCategory, "brd windsor failed: {}", why);
        for (auto const& ref : me->GetMap()->GetPlayers())
            if (Player* player = ref.GetSource())
                if (player->GetQuestStatus(QUEST_JAIL_BREAK) == QUEST_STATUS_INCOMPLETE)
                    player->FailQuest(QUEST_JAIL_BREAK);

        _summons.DespawnAll();
        ResetCellBlock();
        _events.Reset();
        _pendingStart = false;
        _finished = true;
        RemoveEscortState(STATE_ESCORT_ESCORTING | STATE_ESCORT_PAUSED | STATE_ESCORT_RETURNING);
        me->DespawnOrUnsummon(me->IsAlive() ? 1s : 5s, kFailRespawn);
    }

    // The prisoners' spawn ids on map 230 (creature data, read once: the stock spawns 47623-47629).
    static std::vector<ObjectGuid::LowType> const& PrisonerSpawnIds()
    {
        static std::vector<ObjectGuid::LowType> const ids = []
        {
            std::vector<ObjectGuid::LowType> found;
            for (auto const& [spawnId, data] : sObjectMgr->GetAllCreatureData())
                if (data.mapid == BlackrockDepthsRework::kMapBlackrockDepths
                    && std::find(kPrisoners.begin(), kPrisoners.end(), data.id) != kPrisoners.end())
                    found.push_back(spawnId);
            return found;
        }();
        return ids;
    }

    // The cell block as stock: the seven doors closed, the six prisoners alive in their cells with their own faction.
    // Run at every start, on a failure and when Windsor is (re)created. This core spawns creatures dynamically: a freed
    // prisoner (despawned) or a killed one whose corpse decayed has left the map and would only come back at its DB
    // respawn time (2 hours), so a prisoner spawn with no creature on the map gets a forced respawn (queued by the map,
    // so the store is not touched while it is walked here).
    void ResetCellBlock()
    {
        for (uint32 entry : kDoors)
            SetDoor(entry, false);

        Map* map = me->GetMap();
        auto const& store = map->GetCreatureBySpawnIdStore();
        for (ObjectGuid::LowType spawnId : PrisonerSpawnIds())
            if (store.find(spawnId) == store.end())
            {
                map->ForceCreatureRespawn(spawnId);
                LOG_INFO(DungeonKit::kLogCategory, "brd windsor forced the respawn of prisoner spawn {}", spawnId);
            }

        for (auto const& [spawnId, creature] : store)
        {
            if (!creature || std::find(kPrisoners.begin(), kPrisoners.end(), creature->GetEntry()) == kPrisoners.end())
                continue;
            float x = 0.f, y = 0.f, z = 0.f, o = 0.f;
            creature->GetRespawnPosition(x, y, z, &o);
            bool const moved = creature->GetExactDist(x, y, z) > kPrisonerHomeSlack;
            if (!creature->IsAlive() || moved || creature->GetFaction() != creature->GetCreatureTemplate()->faction)
            {
                creature->Respawn(true);
                creature->RestoreFaction();
            }
        }
    }

    SummonList _summons;
    GuidVector _lastAmbush;     // the latest ambush (the Crest stop waits for it)
    EventMap _events;
    std::vector<Stop> _stopAt;
    ObjectGuid _starter;
    Stop _stop = Stop::None;
    CellWait _wait = CellWait::None;
    uint32 _waitDoor = 0;
    ObjectGuid _waitDoorGuid;
    bool _pendingStart = false;
    bool _finished = false;
};

void AddSC_npc_brd_marshal_windsor()
{
    RegisterDungeonReworkCreatureAI(npc_brd_marshal_windsor, BlackrockDepthsRework::kInstanceScriptName);
}
