/*
 * mod-dungeon-bosses, Deadmines (map 36): the shared ids, boss states, texts and measured frames of the Deadmines
 * Pilot (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md sections 3.2, 3.3, 3.8; build spec
 * docs/dungeons/deadmines-rework.md, "DM").
 *
 * Pure: no engine headers, so every <Boss>Logic.h and its host test can include it. Engine glue lives in
 * DeadminesKit.h.
 *
 * Ownership: this file belongs to the shared kit (WP-K). A boss WP keeps its own spell ids, tuning constants and
 * script-local enums in its own <Boss>Logic.h (convention: `enum <Boss>Spells : uint32 { SPELL_<BOSS>_... = <id in its
 * slice> }` and `inline constexpr DeadminesKit::NH<...> k<Name>{ normal, heroic };`), and asks the orchestrator, in its
 * report, for any change here.
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_REWORK_H
#define MOD_DUNGEON_BOSSES_DEADMINES_REWORK_H

#include "DeadminesKitMath.h"
#include <array>
#include <cstdint>

namespace DeadminesRework
{
    using DeadminesKit::Box2;
    using DeadminesKit::Vec2;

    std::uint32_t constexpr kMapDeadmines = 36;
    char constexpr kInstanceScriptName[] = "instance_deadmines_rework";

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. The order is fixed: the save string stores them by position (DeadminesKitMath.h), and
    // BOSS_RHAHKZOR must stay 0 (the stock save's first field).
    // ----------------------------------------------------------------------------------------------------------------
    enum DeadminesBosses : std::uint32_t
    {
        BOSS_RHAHKZOR           = 0,
        BOSS_MINER_JOHNSON      = 1,
        BOSS_SNEED              = 2,    // Sneed's Shredder and Sneed: one encounter, DONE on Sneed's death
        BOSS_GILNID             = 3,
        BOSS_MR_SMITE           = 4,
        BOSS_COOKIE             = 5,
        BOSS_CAPTAIN_GREENSKIN  = 6,
        BOSS_EDWIN_VANCLEEF     = 7,
        BOSS_BURN_IT_DOWN       = 8,    // VanCleef's hard mode (heroic): DONE = he died with DATA_HARD_MODE lit (E5)
    };
    std::uint32_t constexpr kBossCount = 9;
    static_assert(kBossCount == DeadminesKit::kSaveBossCount, "the save string stores every boss state");

    // InstanceScript::SetData / GetData ids (a namespace of their own, apart from the boss state ids above).
    enum DeadminesData : std::uint32_t
    {
        // The stock TYPE_CANNON id, kept: the Defias Cannon's SmartAI actionlist 1639800 sets instance data 1 to DONE
        // (3) when the Iron Clad Door is blown.
        DATA_CANNON             = 1,
        DATA_HARD_MODE          = 21,   // 1 while VanCleef's hard mode is lit (B9 sets it; never survives a reload)
        DATA_JOHNSON_ROLL       = 22,   // GetData: DeadminesKit::JohnsonRoll::{Unrolled, Present, Absent}
        DATA_HARD_MODE_KILLED   = 23,   // GetData: 1 when BOSS_BURN_IT_DOWN is DONE (the hard mode kill flag E5 reads)
    };

    // ObjectData slots (InstanceScript::GetCreature / GetGameObject). ObjectData only for units that are never summoned
    // twice (cpp-scripts.md, the ObjectData pitfall): the spawned bosses and the keg. Sneed (re-summoned on every
    // eject), the Working Miners, Blackguards, iron shot, mines and images are tracked by their summoner.
    enum DeadminesObjects : std::uint32_t
    {
        DATA_RHAHKZOR_GUID          = 100,
        DATA_MINER_JOHNSON_GUID     = 101,
        DATA_SNEEDS_SHREDDER_GUID   = 102,
        DATA_GILNID_GUID            = 103,
        DATA_MR_SMITE_GUID          = 104,
        DATA_COOKIE_GUID            = 105,
        DATA_GREENSKIN_GUID         = 106,
        DATA_VANCLEEF_GUID          = 107,
        DATA_POWDER_KEG_GUID        = 108,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures
    // ----------------------------------------------------------------------------------------------------------------
    enum DeadminesCreatures : std::uint32_t
    {
        // bosses (stock entries; script names in the comments, bound by apps/dbc-tools source/npcs/deadmines/)
        NPC_RHAHKZOR            = 644,      // boss_rhahk_zor_rework
        NPC_MINER_JOHNSON       = 3586,     // boss_miner_johnson_rework
        NPC_SNEEDS_SHREDDER     = 642,      // boss_sneeds_shredder_rework
        NPC_SNEED               = 643,      // boss_sneed_rework
        NPC_GILNID              = 1763,     // boss_gilnid_rework
        NPC_MR_SMITE            = 646,      // boss_mr_smite_rework
        NPC_COOKIE              = 645,      // boss_cookie_rework
        NPC_CAPTAIN_GREENSKIN   = 647,      // boss_captain_greenskin_rework
        NPC_EDWIN_VANCLEEF      = 639,      // boss_edwin_vancleef_rework

        // boss kit (new entries, creature 300420-300449, ids.yaml reservation `deadmines`)
        NPC_DM_WATCHMAN         = 300420,   // npc_dm_watchman (B1), copy of 1725
        NPC_DM_EVOKER           = 300421,   // npc_dm_evoker (B1), copy of 1729
        NPC_DM_WORKING_MINER    = 300422,   // npc_dm_working_miner (B2), copy of 598
        NPC_DM_IRON_SHOT        = 300423,   // npc_dm_iron_shot (B4)
        NPC_DM_LAND_MINE        = 300424,   // npc_dm_land_mine (B4, heroic)
        NPC_DM_HARPOON_ROPE_ANCHOR = 300425, // B7: invisible rope anchor, channels the beam (the rope is GO 301001)
        NPC_DM_BLACKGUARD       = 300426,   // npc_dm_blackguard (B8), copy of 636
        NPC_DM_SHADOW_IMAGE     = 300427,   // npc_dm_shadow_image (B8)
        // 300428 reserved: the mainmast is a gameobject (GO_DM_MAINMAST)
        NPC_DM_POWDER_STALKER   = 300429,   // invisible stalker for hard mode effects (B9), no script
        // 300430 Blackguard (hard mode Signet look, item-variants IV6); 300431-300449 spare

        // stock creatures the scripts refer to
        NPC_DEFIAS_MINER        = 598,
        NPC_DEFIAS_BLACKGUARD   = 636,
        NPC_DEFIAS_WATCHMAN     = 1725,
        NPC_DEFIAS_EVOKER       = 1729,
        NPC_DEFIAS_SQUALLSHAPER = 1732,
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects
    // ----------------------------------------------------------------------------------------------------------------
    enum DeadminesGameObjects : std::uint32_t
    {
        GO_FACTORY_DOOR         = 13965,    // opens on BOSS_RHAHKZOR DONE (door data); lever 101831
        GO_HEAVY_DOOR_1         = 17153,
        GO_HEAVY_DOOR_2         = 17154,
        GO_IRON_CLAD_DOOR       = 16397,    // blown by the cannon (DATA_CANNON)
        GO_DOOR_LEVER_FACTORY   = 101831,
        GO_DOOR_LEVER_MAST_ROOM = 101832,
        GO_DOOR_LEVER_IRON_CLAD = 101833,
        GO_DOOR_LEVER_FOUNDRY   = 101834,
        GO_DEFIAS_CANNON        = 16398,
        GO_FOUNDRY_DOOR         = 16399,    // opens on BOSS_GILNID DONE (door data); lever 101834
        GO_MAST_ROOM_DOOR       = 16400,    // opens on BOSS_SNEED DONE (door data); lever 101832
        GO_DEFIAS_GUNPOWDER     = 17155,
        GO_SMELTING_POT_NORTH   = 123207,   // (-205.664, -574.581); Gilnid's pots, spell focus, no script
        GO_SMELTING_POT_WEST    = 123208,   // (-210.428, -579.201)
        GO_SMELTING_POT_EAST    = 123209,   // (-201.043, -579.374)
        GO_SMELTING_POT_SOUTH   = 123210,   // (-205.805, -583.964)

        // new (gameobject 301000-301099, ids.yaml reservation `deadmines`; rows in core pending SQL)
        GO_DM_POWDER_KEG        = 301000,   // go_dm_powder_keg (B9), heroic only (spawnMask 2)
        GO_DM_HARPOON_ROPE      = 301001,   // go_dm_harpoon_rope (B7), summoned at the rope's midpoint
        GO_DM_MAINMAST          = 301002,   // B9, summoned lying across the deck (no script)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 205200-205399, ids.yaml reservation `deadmines`; declared in apps/dbc-tools
    // source/npcs/deadmines/). Shared ids are named here; each boss names its own ids, inside its slice, in its own
    // <Boss>Logic.h.
    // ----------------------------------------------------------------------------------------------------------------
    enum DeadminesSharedSpells : std::uint32_t
    {
        SPELL_DM_CAST_BAR           = 205200,   // generic 2 s no-effect cast bar (DeadminesKit::CastBar)
        SPELL_DM_STANDING_IN_IT     = 205201,   // "Standing in it hurts." slow rider of every lingering zone
        SPELL_DM_HARD_MODE_TIMER    = 205202,   // Burn It Down's 3:00 timer aura (B9)
        // 205203-205209 spare (shared)
    };
    // 205200 and 205201 are the shared dungeon kit's (WP-K0): every reworked dungeon uses them.
    static_assert(std::uint32_t(SPELL_DM_CAST_BAR) == std::uint32_t(DungeonKit::SPELL_KIT_CAST_BAR), "kit cast bar");
    static_assert(std::uint32_t(SPELL_DM_STANDING_IN_IT) == std::uint32_t(DungeonKit::SPELL_KIT_STANDING_IN_IT),
        "kit slow rider");

    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
    };

    // Per-boss spell slices (handoff section 3.3). The boss WP declares spells only inside its own slice.
    IdSlice constexpr kSpellsShared{ 205200, 205209 };
    IdSlice constexpr kSpellsRhahkZor{ 205210, 205229 };      // B1
    IdSlice constexpr kSpellsMinerJohnson{ 205230, 205239 };  // B2
    IdSlice constexpr kSpellsSneed{ 205240, 205269 };         // B3 (Shredder and Sneed)
    IdSlice constexpr kSpellsGilnid{ 205270, 205289 };        // B4
    IdSlice constexpr kSpellsMrSmite{ 205290, 205319 };       // B5
    IdSlice constexpr kSpellsCookie{ 205320, 205339 };        // B6
    IdSlice constexpr kSpellsGreenskin{ 205340, 205359 };     // B7
    IdSlice constexpr kSpellsVanCleef{ 205360, 205379 };      // B8 (the handoff's VC 205360-205389, split with B9)
    IdSlice constexpr kSpellsHardMode{ 205380, 205389 };      // B9
    IdSlice constexpr kSpellsSpare{ 205390, 205399 };

    // Stock spells the build specs keep (DD scales them on heroic; handoff section 7 #3: shorten the aura, keep the
    // id).
    enum DeadminesStockSpells : std::uint32_t
    {
        SPELL_RHAHKZOR_SLAM         = 6304,     // RZ5, stun cut to 1.5 s by the script
        SPELL_SHOOT                 = 6660,     // Watchman
        SPELL_FLAMESTRIKE           = 11829,    // Evoker RZ6
        SPELL_FIREBALL              = 11839,    // Evoker RZ7
        SPELL_QUICK_FLAME_WARD      = 4979,     // Evoker (purge list)
        SPELL_FROST_ARMOR           = 12544,    // Evoker
        SPELL_PIERCE_ARMOR_MINER    = 6016,     // Working Miner MJ3
        SPELL_PIERCE_ARMOR          = 12097,    // Johnson MJ4, cut to 10 s
        SPELL_EJECT_SNEED           = 5141,     // SN eject
        SPELL_MOLTEN_METAL          = 5213,     // Gilnid GI1
        SPELL_SMITE_STOMP           = 6432,     // SM1, stun cut to 2 s
        SPELL_SMITE_SLAM            = 6435,     // SM9 stock id, unused: B5 casts the no-stun copy 205298
        SPELL_THRASH_AURA           = 3417,     // Smite, VanCleef
        SPELL_THRASH                = 3391,
        SPELL_ACID_SPLASH           = 6306,     // Cookie CK1
        SPELL_CLEAVE                = 40505,    // Greenskin GS1
        SPELL_POISONED_HARPOON      = 5208,     // Greenskin GS5
        SPELL_DUAL_WIELD            = 674,      // VanCleef
        SPELL_CHEAP_SHOT            = 1833,     // Blackguard VC5, stun cut to 2 s
        SPELL_RUPTURE               = 14903,    // Blackguard VC6
        SPELL_DEFIAS_CANNON_BLAST   = 6250,     // item 5397 on the cannon (Iron Clad Door event)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // creature_text groups (build spec "Text" tables). Texts are inserted by each boss WP's own SQL rev.
    // ----------------------------------------------------------------------------------------------------------------
    enum RhahkZorTexts : std::uint8_t
    {
        SAY_RHAHKZOR_AGGRO              = 0,    // stock yell
        EMOTE_RHAHKZOR_CAVE_IN          = 1,
        EMOTE_RHAHKZOR_WHIRLWIND        = 2,
    };
    enum EvokerTexts : std::uint8_t
    {
        EMOTE_EVOKER_VOLLEY             = 0,    // heroic
    };
    enum WatchmanTexts : std::uint8_t
    {
        EMOTE_WATCHMAN_LOOKOUT          = 0,    // heroic, with RZ1
    };
    enum MinerJohnsonTexts : std::uint8_t
    {
        SAY_JOHNSON_AGGRO               = 0,
        EMOTE_JOHNSON_PAYDAY            = 1,
        EMOTE_JOHNSON_NO_CREW           = 2,
    };
    enum WorkingMinerTexts : std::uint8_t
    {
        EMOTE_WORKING_MINER_PAID        = 0,
    };
    enum SneedsShredderTexts : std::uint8_t
    {
        EMOTE_SHREDDER_SAW_SPIN         = 0,
        EMOTE_SHREDDER_SPLINTER_SPRAY   = 1,
        EMOTE_SHREDDER_RUNAWAY          = 2,
        EMOTE_SHREDDER_OVERLOAD         = 3,
    };
    enum SneedTexts : std::uint8_t
    {
        SAY_SNEED_EJECT                 = 0,
        EMOTE_SNEED_REPAIRS             = 1,
        EMOTE_SNEED_BACK_IN_BUSINESS    = 2,
        EMOTE_SNEED_SALVAGED_SAW        = 3,
    };
    enum GilnidTexts : std::uint8_t
    {
        SAY_GILNID_OUT_OF_COMBAT        = 0,    // stock, every 2 min out of combat
        YELL_GILNID_ROLL_OUT            = 1,
        YELL_GILNID_DOUBLE_SHIFT        = 2,
        EMOTE_GILNID_LANDMINE           = 3,
        YELL_GILNID_AGGRO               = 4,
        YELL_GILNID_BOWLED_OVER         = 5,
    };
    enum MrSmiteTexts : std::uint8_t
    {
        YELL_SMITE_ALARM                = 0,    // stock, Iron Clad Door event
        YELL_SMITE_REPEL                = 1,    // stock, Iron Clad Door event
        SAY_SMITE_FIRST_SWAP            = 2,    // stock
        SAY_SMITE_SECOND_SWAP           = 3,    // stock
        EMOTE_SMITE_HAMMER              = 4,
        EMOTE_SMITE_HARPOON             = 5,
    };
    enum CookieTexts : std::uint8_t
    {
        EMOTE_COOKIE_FEED               = 0,    // the chowder dish (B6: one group per dish)
        YELL_COOKIE_AGGRO               = 1,
        EMOTE_COOKIE_FEED_STEW          = 2,
        EMOTE_COOKIE_FEED_GUT_BOMB      = 3,
    };
    enum GreenskinTexts : std::uint8_t
    {
        YELL_GREENSKIN_FIRE_ON_MY_MARK  = 0,
        EMOTE_GREENSKIN_HARPOON         = 1,
        YELL_GREENSKIN_REEL             = 2,
        YELL_GREENSKIN_AGGRO            = 3,
    };
    enum VanCleefTexts : std::uint8_t
    {
        YELL_VANCLEEF_AGGRO             = 0,    // stock
        YELL_VANCLEEF_GUNS              = 1,    // stock, 66%
        EMOTE_VANCLEEF_ALLIES           = 2,    // stock, 50%
        YELL_VANCLEEF_IMAGE             = 3,    // stock, 33%
        YELL_VANCLEEF_KILL              = 4,    // stock
        YELL_VANCLEEF_DEATH             = 5,    // stock
        EMOTE_VANCLEEF_AMBUSH           = 6,
        YELL_VANCLEEF_FUSE              = 7,    // hard mode
        YELL_VANCLEEF_MAST              = 8,    // hard mode, 2:00
        YELL_VANCLEEF_OFF_MY_SHIP       = 9,    // hard mode, 2:45
        YELL_VANCLEEF_ARRIVAL           = 10,   // the instance says it on Greenskin's DONE (ruling 26)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Measured frames (handoff section 3.8; deadmines-pilot.NAVMESH-REPORT.md). All [navmesh estimate]: the mesh sits
    // about 0.53 yd inside every wall. Axes: +x north, +y west. WP-P's playtest guide checks the corners with .gps.
    // ----------------------------------------------------------------------------------------------------------------

    // Gilnid's foundry. Floor z 19-20 (spawn 19.3); the pot dais z 21.
    Vec2 constexpr kGilnidSpawn{ -177.4f, -574.5f };
    float constexpr kFoundryFloorZ = 19.3f;
    float constexpr kFoundryPotZ = 21.0f;
    Vec2 constexpr kPotCenter{ -205.7f, -579.3f };
    std::array<Vec2, 4> constexpr kPots{ {
        { -205.664f, -574.581f },   // GO_SMELTING_POT_NORTH (guid 26191)
        { -210.428f, -579.201f },   // GO_SMELTING_POT_WEST (26194)
        { -201.043f, -579.374f },   // GO_SMELTING_POT_EAST (26195)
        { -205.805f, -583.964f },   // GO_SMELTING_POT_SOUTH (26193)
    } };
    // The pot block: a hole in the floor (about 9 x 9 yd), lanes start at its edge.
    Box2 constexpr kPotBlock{ -209.5f, -200.5f, -583.5f, -574.5f };
    // Wall polygon of the main floor (navmesh edge), counterclockwise from the northeast corner. The north and west
    // vertices are the measured ends of the rays from kPotCenter (0, 9.6 through Gilnid, 15 .. 105 degrees); the
    // south and east sides follow the wall table (south x -213.5, the floor behind the pots to x -218, the platform
    // edge y -594, the east wall y -588.5 at Gilnid's row). Lanes aimed north or west run 34 to 37.5 yd; east or
    // south only 8 to 17 yd.
    std::array<Vec2, 16> constexpr kFoundryWalls{ {
        { -172.0f, -588.5f },   // northeast corner
        { -168.2f, -583.0f },   // Foundry Door gap, east post (door at x -168.5)
        { -168.2f, -576.0f },   // Foundry Door gap, west post
        { -170.2f, -573.3f },   // north wall where the lane through Gilnid ends (36.0 yd from kPotCenter)
        { -170.7f, -569.9f },   // ray 15 deg
        { -174.1f, -561.0f },   // ray 30 deg
        { -180.1f, -553.7f },   // ray 45 deg
        { -187.7f, -548.1f },   // ray 60 deg
        { -197.0f, -546.7f },   // ray 75 deg
        { -205.7f, -545.0f },   // ray 90 deg (west)
        { -213.5f, -550.3f },   // ray 105 deg
        { -213.5f, -572.0f },   // south wall, west half
        { -218.0f, -580.0f },   // floor behind the pots
        { -213.0f, -594.0f },   // southeast, behind the platform
        { -180.0f, -594.0f },   // platform edge, east side
        { -180.0f, -588.5f },   // east wall at Gilnid's row
    } };

    // The Defias Juggernaut's main deck (Greenskin and VanCleef). One sloped deck, z 43 at the stern to 38 at the bow;
    // the long axis is the map x axis, the bow points south (-x; confirm with .gps). The frame for
    // BossMechanics::RoomFrame: origin = a corner (the west rail at the sterncastle face), X along `angle` toward the
    // bow for kDeckLength, Y along angle + 90 deg (toward -y, east) for kDeckWidth. Bow-ward of x -89 the hull narrows
    // (16 to 20 yd) and the deck splits into strips: across-deck lanes overhang the rails there (section 3.8).
    Vec2 constexpr kDeckSternCenter{ -53.5f, -820.0f };     // the sterncastle face on the centerline
    Vec2 constexpr kDeckOrigin{ -53.5f, -802.0f };          // RoomFrame origin (corner)
    float constexpr kDeckAngle = 3.14159265f;               // toward the bow (-x)
    float constexpr kDeckLength = 54.f;                     // sterncastle face to the bow tip
    float constexpr kDeckWidth = 36.f;                      // rail to rail at the open stern half
    float constexpr kDeckZ = 41.f;                          // frame height; the deck runs 43 (stern) to 38 (bow)
    Vec2 constexpr kDeckBowTip{ -107.5f, -819.5f };
    Vec2 constexpr kGreenskinSpawn{ -59.6f, -820.1f };      // z 41.6
    Vec2 constexpr kVanCleefSpawn{ -87.4f, -819.9f };       // z 39.3, on the 9 yd center strip (dead-ends at x -89.5)
    // Hard mode (B9): the fire front's stripe depth for about 10 yd of bow left at 2:40, measured from the sterncastle
    // face where the first stripe lands (section 3.8, section 7 #10). The keg (spawn 3010000) stands on the west stern
    // walkway beside the sterncastle since playtest 1 (the user's spot), aft of the first stripe: the walkway burns
    // with stripe 0 (HardModeLogic kAftWalkwayX).
    Vec2 constexpr kPowderKegSpot{ -48.148335f, -812.0548f };
    float constexpr kPowderKegZ = 42.69199f;
    float constexpr kFireFrontStripeDepth = 2.73f;

    // Mr. Smite's chest (weapon swaps).
    Vec2 constexpr kSmiteChest{ 1.9f, -780.7f };
    float constexpr kSmiteChestZ = 9.8f;
}

#endif
