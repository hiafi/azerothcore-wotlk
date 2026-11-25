/*
 * mod-dungeon-bosses, Ragefire Chasm (map 389): the shared ids, boss states, data ids, texts, measured points, arenas,
 * tuning numbers and the instance's pure rules of the Ragefire Chasm build
 * (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md sections 3.2, 3.3, 3.6, 3.7, 3.8; build spec
 * docs/dungeons/ragefire-chasm-rework.md, "SP", whose rulings 15 and 16 win over older text in it).
 *
 * Pure: no engine headers (only the shared kit's pure DungeonKit*.h), so every <Boss>Logic.h and its host test can
 * include it. Engine glue is RagefireChasmKit.h and the shared kit (src/Kit/).
 *
 * Ownership: this file belongs to WP-S0 until it reports, then to the orchestrator. A boss WP keeps its spell ids
 * (inside its slice below) and its script-local enums in its own <Boss>Logic.h, reads every number from the tuning
 * block at the end of this file (one table per boss, so a retune is one line), and asks for a change here in its
 * report ("Shared-file request").
 *
 * Frame (NAVMESH-REPORT): +x is SP's "east" and +y its "north"; in WoW's own compass +x is north and +y is west. DB
 * positions are exact, every other point and polygon is [navmesh estimate] (the mesh sits about 0.53 yd inside every
 * wall and edge). The polygons were cut from the 389 mmtiles on a 0.5 yd raster (WP-S0): the playtest checks the key
 * points with `.dbtest rfc instance where` and .gps.
 */

#ifndef MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_REWORK_H
#define MOD_DUNGEON_BOSSES_RAGEFIRE_CHASM_REWORK_H

#include "DungeonKitArena.h"
#include "DungeonKitEdgeLogic.h"
#include "DungeonKitMath.h"
#include "DungeonKitState.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <vector>

namespace RagefireChasmRework
{
    using DungeonKit::Arena;
    using DungeonKit::ArenaRegion;
    using DungeonKit::NH;
    using DungeonKit::Vec2;

    std::uint32_t constexpr kMapRagefireChasm = 389;
    // The stock instance name (section 7 #1 A): modules load after the core scripts, and a database-bound script
    // registered later under the same name replaces the earlier one, so instance_template is untouched.
    char constexpr kInstanceScriptName[] = "instance_ragefire_chasm";
    // `.dbtest rfc <boss> <mechanic>`: the kit shell's command name, nested under the shared `.dbtest` root.
    char constexpr kTestCommand[] = "dbtest rfc";
    char constexpr kLogDungeon[] = "rfc";       // DungeonKit::LogMechanic("rfc", "<boss>", "<mechanic>", ...)

    // ----------------------------------------------------------------------------------------------------------------
    // Boss states (InstanceScript::SetBossNumber(kBossCount)); also the `bossStateId` each boss passes to
    // Mechanic::BeginEncounter. The order is fixed: the save string stores them by position. It is the KILL order
    // (ruling 2), not the DungeonEncounter bit order (430 bit 0, 431 bit 1 = Taragaman, 432 bit 2, 433 bit 3).
    // ----------------------------------------------------------------------------------------------------------------
    enum RfcBosses : std::uint32_t
    {
        BOSS_OGGLEFLINT     = 0,    // D1, encounter 430
        BOSS_JERGOSH        = 1,    // D2, encounter 432
        BOSS_BAZZALAN       = 2,    // D3, encounter 433
        BOSS_TARAGAMAN      = 3,    // D4, encounter 431 (the Dungeon Finder credit); gated on 0 to 2
        BOSS_STARVING       = 4,    // D4H: the hard mode kill slot (DONE = Taragaman died with DATA_HARD_MODE)
    };
    std::uint32_t constexpr kBossCount = 5;
    std::uint32_t constexpr kGateBossCount = 3;     // slots 0 to 2 open the gate

    inline std::array<char const*, kBossCount> constexpr kBossNames{ {
        "Oggleflint", "Jergosh the Invoker", "Bazzalan", "Taragaman the Hungerer", "Starving (hard mode)",
    } };

    // InstanceScript::SetData / GetData ids (a namespace of their own, apart from the boss state ids; the stock
    // instance has none, and nothing on map 389 reads or writes instance data: handoff section 2.2).
    enum RfcData : std::uint32_t
    {
        DATA_HARD_MODE          = 20,   // Get / Set(0|1): Starving is armed (the pour GO, D4H); saved, holds through
                                        // wipes; Set is refused by HardModeChangeAllowed
        DATA_HARD_MODE_KILLED   = 21,   // Get only: 1 when BOSS_STARVING is DONE
        DATA_GATE_OPEN          = 22,   // Get only: 1 when slots 0 to 2 are all DONE (derived, never saved)
        DATA_TARAGAMAN_DORMANT  = 23,   // Get only: TaragamanDormant(): what his Reset applies (ApplyTaragamanGate)
    };

    // GetGuidData ids: kGuidBossBase + slot for the four bosses, and nothing else (never a summoned unit:
    // cpp-scripts.md, the ObjectData pitfall).
    std::uint32_t constexpr kGuidBossBase = 100;

    // DoAction values the instance sends to Taragaman's AI (D4 handles them in DoAction; the instance has already set
    // his flags, said line 0 and set the loot bit).
    enum RfcActions : std::int32_t
    {
        ACTION_RFC_GATE_OPENED          = 38901,    // the third of slots 0 to 2 went DONE, live (never on a load)
        ACTION_RFC_HARD_MODE_ARMED      = 38902,    // DATA_HARD_MODE went 0 -> 1 (health, SV 90554, line 9: D4 / D4H)
        ACTION_RFC_HARD_MODE_CLEARED    = 38903,    // DATA_HARD_MODE went 1 -> 0 (a GM; undo the above)
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Creatures. Script names in the comments are fixed: a boss stub's is bound by its DT file; an add's is registered
    // by its WP in the same change that declares the creature (a registered name no creature_template row names logs
    // "not assigned" at boot).
    // ----------------------------------------------------------------------------------------------------------------
    enum RfcCreatures : std::uint32_t
    {
        NPC_OGGLEFLINT          = 11517,    // boss_oggleflint_rework
        NPC_JERGOSH             = 11518,    // boss_jergosh_rework
        NPC_BAZZALAN            = 11519,    // boss_bazzalan_rework
        NPC_TARAGAMAN           = 11520,    // boss_taragaman_rework

        // stock units the scripts may meet (all stay stock, SmartAI included)
        NPC_EARTHBORER          = 11320,
        NPC_MAUR_GRIMTOTEM      = 11834,    // the body in Oggleflint's den (quest object)
        NPC_ZELEMAR             = 17830,    // out of scope (ruling 5)

        // boss kit (creature 300985-300999, ids.yaml reservation `ragefire_chasm`)
        NPC_RFC_BORER           = 300985,   // D1 declares; npc_rfc_borer (boss_oggleflint_rework.cpp)
        NPC_RFC_SOUL_WISP       = 300986,   // D2 declares; npc_rfc_soul_wisp (boss_jergosh_rework.cpp)
        NPC_RFC_BLOOD_GLOBULE   = 300987,   // D4H declares; npc_rfc_blood_globule (taragaman_hard_mode.cpp)
        NPC_RFC_STALKER         = 300988,   // S0 declares (kit_helpers.py); no script: the generic visual stalker
        NPC_RFC_ENTRANCE_ORC    = 300989,   // the quests WP declares; data only
        // 300990-300999 spare (ask the orchestrator)
    };

    constexpr bool IsRfcBossEntry(std::uint32_t entry)
    {
        return entry == NPC_OGGLEFLINT || entry == NPC_JERGOSH || entry == NPC_BAZZALAN || entry == NPC_TARAGAMAN;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Gameobjects (gameobject 301340-301359)
    // ----------------------------------------------------------------------------------------------------------------
    enum RfcGameObjects : std::uint32_t
    {
        GO_BLOOD_FILLED_ORB     = 182024,   // stock (quest 9692, Zelemar): untouched
        GO_RFC_BLOOD_SHRINE     = 301340,   // D4H: go_rfc_blood_shrine, display 328 (heroic spawn only)
        GO_RFC_POUR_SPOT        = 301341,   // D4H: go_rfc_pour_spot, display 216 (heroic spawn only)
        GO_RFC_SEARING_SPIKE    = 301342,   // D4: display 5073, size 2.0; no script, spawned per Nova
        // 301343-301359 spare
    };

    // ----------------------------------------------------------------------------------------------------------------
    // Spells (spell 213540-213799; the gear stage's `ragefire_chasm_items` 213500-213539 and its spell_rfc_* script
    // names are not ours). Each boss names its own ids, inside its slice, in its own <Boss>Logic.h.
    // ----------------------------------------------------------------------------------------------------------------
    struct IdSlice
    {
        std::uint32_t first;
        std::uint32_t last;

        constexpr bool Contains(std::uint32_t id) const { return id >= first && id <= last; }
        constexpr std::uint32_t Size() const { return last - first + 1; }
    };

    IdSlice constexpr kSpellsReservation{ 213540, 213799 };
    IdSlice constexpr kSpellsShared{ 213540, 213549 };          // S0 / orchestrator: none declared yet
    IdSlice constexpr kSpellsOggleflint{ 213550, 213579 };      // D1
    IdSlice constexpr kSpellsJergosh{ 213580, 213609 };         // D2
    IdSlice constexpr kSpellsBazzalan{ 213610, 213649 };        // D3
    IdSlice constexpr kSpellsTaragaman{ 213650, 213689 };       // D4
    IdSlice constexpr kSpellsStarving{ 213690, 213719 };        // D4H
    IdSlice constexpr kSpellsSpare{ 213720, 213799 };

    inline std::array<IdSlice, 6> constexpr kSpellSlices{ {
        kSpellsShared, kSpellsOggleflint, kSpellsJergosh, kSpellsBazzalan, kSpellsTaragaman, kSpellsStarving,
    } };

    IdSlice constexpr kCreaturesReservation{ 300985, 300999 };
    IdSlice constexpr kGameObjectsReservation{ 301340, 301359 };

    // Stock spells the build specs keep as stock casts (never rescaled copies: section 3.5 rule 15).
    enum RfcStockSpells : std::uint32_t
    {
        SPELL_CURSE_OF_WEAKNESS = 18267,    // Jergosh JR3
        SPELL_UPPERCUT          = 18072,    // Taragaman TG10
    };

    // ----------------------------------------------------------------------------------------------------------------
    // creature_text groups, 0-based (SP "Text" tables; section 3.5 rule 32). Emotes are type 41. Each owner's SQL rev
    // inserts its rows.
    // ----------------------------------------------------------------------------------------------------------------
    enum OggleflintTexts : std::uint8_t
    {
        EMOTE_OGGLEFLINT_HUNT       = 0,    // OG1, $n: "%s bellows, and the ground churns toward $n!"
        EMOTE_OGGLEFLINT_SWING      = 1,    // OG3: "%s raises his club high!"
        EMOTE_OGGLEFLINT_BEATING    = 2,    // OG4 (heroic), $n: "%s glares at $n and hefts his club!"
    };
    enum JergoshTexts : std::uint8_t
    {
        YELL_JERGOSH_AGGRO          = 0,    // "The Searing Blade will purge you in fire!"
        EMOTE_JERGOSH_CONFLAGRATE   = 1,    // JR2: "%s spreads his hands, and the flames on his victims flare!"
        EMOTE_JERGOSH_DRAIN_SOUL    = 2,    // JR4 (heroic), $n: "%s begins to tear the soul from $n!"
        EMOTE_JERGOSH_EATEN         = 3,    // JR5 (heroic): "The Hungerer feeds, and %s grows stronger!"
    };
    enum BazzalanTexts : std::uint8_t
    {
        YELL_BAZZALAN_AGGRO         = 0,    // "Thrall's pups come sniffing? The Blade cuts both ways!"
        EMOTE_BAZZALAN_EVISCERATE   = 1,    // BZ3: "%s readies an Eviscerate!"
        EMOTE_BAZZALAN_RUPTURE      = 2,    // BZ4, $n: "%s readies a Rupture on $n!"
        EMOTE_BAZZALAN_FAN          = 3,    // BZ5: "%s readies a Fan of Knives!"
        EMOTE_BAZZALAN_ENVENOM      = 4,    // BZ6 (heroic): "%s readies an Envenom!"
        EMOTE_BAZZALAN_SHADOWSTEP   = 5,    // BZ7 (heroic), $n, each landing: "%s vanishes and appears behind $n!"
    };
    enum TaragamanTexts : std::uint8_t
    {
        YELL_TARAGAMAN_GATE         = 0,    // TG0, said by the INSTANCE on the third kill; type 14, TextRange 2 (zone)
        YELL_TARAGAMAN_AGGRO        = 1,    // "The Hungerer feeds!"
        EMOTE_TARAGAMAN_FEAST       = 2,    // TG1, $n: "%s smells blood on $n!"
        EMOTE_TARAGAMAN_FELSTORM    = 3,    // TG3: "%s raises his blade and begins to spin!"
        EMOTE_TARAGAMAN_NOVA        = 4,    // TG6: "%s leaps to the center stone, and spikes of rock heave ..."
        EMOTE_TARAGAMAN_DEVOUR      = 5,    // TG2 (heroic), $n: "%s begins to devour $n!"
        YELL_TARAGAMAN_DEATH        = 6,    // "The hunger... never ends..."
        YELL_TARAGAMAN_BLOOD_LAKE   = 7,    // D4H: phase 2 at 30%, "The lake bleeds for me! Drink, drink!"
        EMOTE_TARAGAMAN_GLOBULES    = 8,    // D4H: TG8, "Blood crawls up from the lake toward %s!"
        YELL_TARAGAMAN_POURED       = 9,    // D4H: the hard mode set, "That taste... MORE! Bring me MORE!"
    };

    // ----------------------------------------------------------------------------------------------------------------
    // The gate and the hard mode: the instance's pure rules (handoff section 3.2 items 3 and 4; section 7 #8, #9, #17)
    // ----------------------------------------------------------------------------------------------------------------
    using BossStates = std::array<std::uint32_t, kBossCount>;

    // The gate is open once slots 0 to 2 are all DONE. Derived from the saved slots only: there is no gate flag, so a
    // reload recomputes it and nothing can disagree with the kills.
    constexpr bool GateOpen(BossStates const& states)
    {
        for (std::uint32_t i = 0; i < kGateBossCount; ++i)
            if (states[i] != DungeonKit::State::Done)
                return false;
        return true;
    }

    // Whether Taragaman stands dormant (passive, immune to all, not selectable, visible): the gate is closed and he is
    // neither dead nor fighting. A lieutenant's slot that goes back to NOT_STARTED (a GM's respawn) never freezes him
    // mid fight: his own Reset reads this again.
    constexpr bool TaragamanDormant(BossStates const& states)
    {
        return !GateOpen(states) && states[BOSS_TARAGAMAN] != DungeonKit::State::Done
            && states[BOSS_TARAGAMAN] != DungeonKit::State::InProgress;
    }

    // Whether a LIVE change of slot `id` to `state` opens the gate now (`states` after the change): one of slots 0 to 2
    // went DONE and the other two are DONE already. The line 0 yell plays on exactly this. A load never asks: the base
    // SetBossState stores a state onto a TO_BE_DECIDED slot and returns false.
    constexpr bool GateOpensOn(std::uint32_t id, std::uint32_t state, BossStates const& states)
    {
        return id < kGateBossCount && state == DungeonKit::State::Done && GateOpen(states);
    }

    // Whether a boss that comes into the world dead (a corpse kept by its saved respawn time) settles its slot `id` as
    // DONE: one of slots 0 to 2 whose own save does not say so. An instance from before the rework (the stock script
    // saved no slots) or a save lost in a crash would otherwise keep the gate closed until the reset. Quiet: no yell.
    constexpr bool DeadLoadSettles(std::uint32_t id, std::uint32_t state)
    {
        return id < kGateBossCount && state != DungeonKit::State::Done;
    }

    // Whether the instance accepts SetData(DATA_HARD_MODE, value) (section 3.2 item 4): arming needs a heroic map; no
    // change once Taragaman fights or is dead. The gate's state does not matter (section 7 #17 A).
    constexpr bool HardModeChangeAllowed(bool heroic, std::uint32_t taragamanState, std::uint32_t value)
    {
        if (taragamanState == DungeonKit::State::Done || taragamanState == DungeonKit::State::InProgress)
            return false;
        return value == 0 || heroic;
    }

    // Whether the hard mode loot bit rides Taragaman now: the flag is lit and he is not dead (his loot is filled in
    // Unit::Kill, before JustDied).
    constexpr bool HardModeLootLit(std::uint32_t hardMode, std::uint32_t taragamanState)
    {
        return hardMode != 0 && taragamanState != DungeonKit::State::Done;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Measured points (handoff section 3.8)
    // ----------------------------------------------------------------------------------------------------------------
    struct Point3
    {
        float x = 0.f;
        float y = 0.f;
        float z = 0.f;
        float o = 0.f;

        constexpr Vec2 XY() const { return { x, y }; }
    };

    Point3 constexpr kFinderStart{ 3.81f, -14.82f, -17.84f, 4.39f };            // [DB] areatrigger 2230
    Point3 constexpr kEntranceOrc{ 8.24f, -22.39f, -19.71f, 2.89f };            // [user] .gps, the quests WP
    // Section 7 #14 A: the one "reached only" checkpoint (mod-dungeon-checkpoint), on the route before the lava lake.
    Point3 constexpr kCheckpoint{ -154.8f, 70.2f, -21.1f, 2.68f };
    float constexpr kCheckpointReachYd = 10.f;

    // --- Oggleflint's den ---
    Point3 constexpr kOggleflintSpawn{ -147.548f, 38.7127f, -38.8039f, 4.39823f };  // [DB] guid 48644
    Point3 constexpr kDenTankSpot{ -150.0f, 45.0f, -38.55f };                   // at the +y wall, clearance 2.6
    Point3 constexpr kDenDisc{ -150.2f, 34.8f, -38.6f };                        // the largest clear disc
    float constexpr kDenDiscRadius = 11.2f;
    float constexpr kDenFloorZ = -38.5f;                                        // flat, -38.1 to -38.7
    Point3 constexpr kDenNeck{ -149.0f, 10.0f, -38.68f };                       // the neck's narrow part (3.5 yd)

    // --- Jergosh's hall ---
    Point3 constexpr kJergoshSpawn{ -376.811f, 209.224f, -21.801f, 5.91667f };  // [DB] guid 48740
    Point3 constexpr kOfferingSpot{ -328.0f, 218.0f, -20.5f };                  // section 7 #21 A: 50 yd, 16.5 s
    Point3 constexpr kHallDisc{ -365.8f, 202.8f, -22.0f };
    float constexpr kHallDiscRadius = 19.4f;
    Point3 constexpr kHallStrip{ -312.2f, 214.8f, -23.0f };                     // the way in from the west bank
    Point3 constexpr kOrb{ -370.13f, 162.52f, -21.13f };                        // [DB] GO 182024
    Point3 constexpr kBloodShrine{ -367.5f, 165.0f, -21.0f };                   // section 7 #15 A, GO 301340

    // --- Bazzalan's ridge ---
    Point3 constexpr kBazzalanSpawn{ -384.867f, 146.045f, 7.82184f, 2.51327f }; // [DB] guid 48750
    Point3 constexpr kRidgeSafeDisc{ -394.2f, 153.2f, 8.0f };                   // clear of lethal edges
    float constexpr kRidgeSafeDiscRadius = 14.8f;
    Point3 constexpr kRidgeNeck{ -408.0f, 190.0f, 5.3f };                       // the way in from the north shelf

    // --- Taragaman's plateau ---
    Point3 constexpr kTaragamanSpawn{ -244.743f, 150.085f, -18.7494f, 4.28461f };   // [DB] guid 48706
    Point3 constexpr kHub{ -244.74f, 150.09f, -18.5f };                         // the Nova's leap target (mesh floor)
    float constexpr kLavaZ = -28.0f;
    // Section 7 #19 A, #20 A: the spike points 10 yd from the hub (the -y one moved to bearing 255 off the lava notch);
    // z is the mesh floor. Hide spots are kSpikeHideYd behind the center, on the line from the hub.
    enum SpikePoint : std::uint8_t
    {
        SPIKE_PLUS_X    = 0,
        SPIKE_MINUS_X   = 1,
        SPIKE_PLUS_Y    = 2,
        SPIKE_MINUS_Y   = 3,
    };
    std::size_t constexpr kSpikePointCount = 4;
    inline std::array<Point3, kSpikePointCount> constexpr kSpikePoints{ {
        { -234.74f, 150.09f, -18.55f }, { -254.74f, 150.09f, -18.48f },
        { -244.74f, 160.09f, -17.77f }, { -247.3f, 140.4f, -18.47f },
    } };
    // Section 7 #22 A: the four globule starts, 32 yd out on floor (12.8 s at 2.5 yd/s), in SpikePoint's arm order.
    inline std::array<Point3, 4> constexpr kGlobuleStarts{ {
        { -214.2f, 157.2f, -20.9f }, { -275.2f, 142.8f, -21.3f },
        { -241.2f, 181.2f, -19.7f }, { -252.8f, 120.2f, -20.6f },
    } };
    // Section 7 #16 A: the pour spot at the -x arm foot (GO 301341) and the lava cell its look plays at.
    Point3 constexpr kPourSpot{ -276.8f, 144.8f, -22.7f };
    Point3 constexpr kPourLava{ -276.2f, 143.8f, -28.0f };

    // The hide spot behind a spike: `behindYd` past it on the line from the hub.
    inline Vec2 SpikeHideSpot(std::size_t point, float behindYd)
    {
        Vec2 const spike = kSpikePoints[point].XY();
        return DungeonKit::Advance(spike, DungeonKit::BearingTo(kHub.XY(), spike), behindYd);
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Arenas. The leash arena of each boss (RagefireChasmKit.h LeashOptions): 2 yd short of a lethal drop, 4 yd on
    // Bazzalan's ridge (section 3.5 rule 5, section 7 #23 A, #24 A), about 1 yd past the mesh at a wall. The z bands
    // reach 8 yd or more over the floor, so a knocked up player is still inside, and exclude every other level.
    // ----------------------------------------------------------------------------------------------------------------
    // The den's floor (y 22 and up; mesh edge): Beating landings, Borer spots. 521 sq yd.
    inline std::array<Vec2, 11> constexpr kDenFloorPolygon{ {
        { -154.5f, 47.5f }, { -159.0f, 45.5f }, { -160.5f, 43.5f }, { -162.5f, 36.0f }, { -162.5f, 29.0f },
        { -161.0f, 28.0f }, { -159.0f, 22.0f }, { -143.0f, 22.0f }, { -139.0f, 27.0f }, { -139.0f, 41.5f },
        { -147.0f, 47.0f },
    } };
    // The den and its neck to y 5 (section 7 #13 A). The jump-in ledges (z -21 to -18) are above the z band.
    inline std::array<Vec2, 20> constexpr kDenArenaPolygon{ {
        { -160.0f, 22.5f }, { -157.5f, 19.5f }, { -154.5f, 18.5f }, { -151.5f, 9.0f }, { -151.5f, 7.0f },
        { -153.5f, 6.5f }, { -153.5f, 4.5f }, { -146.0f, 4.0f }, { -146.5f, 18.0f }, { -141.0f, 22.0f },
        { -138.0f, 26.5f }, { -138.0f, 42.0f }, { -142.5f, 46.0f }, { -148.0f, 48.5f }, { -156.0f, 48.5f },
        { -159.5f, 46.5f }, { -161.5f, 44.0f }, { -163.5f, 36.5f }, { -163.5f, 28.5f }, { -162.0f, 27.5f },
    } };
    float constexpr kDenZMin = -41.5f;
    float constexpr kDenZMax = -28.0f;

    // The hall, its neck to the Orb and the strip to x -318 (the ramp to the north shelf is cut at its foot). 2,940 sq
    // yd of floor; walls all round, no drop inside.
    inline std::array<Vec2, 33> constexpr kHallArenaPolygon{ {
        { -332.5f, 230.0f }, { -359.0f, 223.0f }, { -361.5f, 231.5f }, { -350.5f, 231.0f }, { -335.0f, 238.0f },
        { -349.5f, 244.5f }, { -367.0f, 236.0f }, { -364.0f, 233.0f }, { -364.0f, 225.0f }, { -372.0f, 230.5f },
        { -375.5f, 224.0f }, { -385.0f, 215.5f }, { -387.5f, 203.5f }, { -393.0f, 196.5f }, { -379.5f, 186.5f },
        { -377.5f, 173.5f }, { -380.5f, 164.0f }, { -373.5f, 161.0f }, { -369.0f, 155.5f }, { -362.0f, 155.0f },
        { -357.0f, 158.0f }, { -360.0f, 162.0f }, { -357.0f, 176.0f }, { -347.0f, 189.5f }, { -342.0f, 191.5f },
        { -344.0f, 193.5f }, { -341.0f, 194.0f }, { -337.5f, 200.0f }, { -327.5f, 201.0f }, { -324.5f, 205.5f },
        { -325.0f, 211.5f }, { -317.5f, 214.0f }, { -317.5f, 231.5f },
    } };
    float constexpr kHallZMin = -25.5f;
    float constexpr kHallZMax = -12.0f;

    // The ridge's whole floor to its rims (z 5 to 12; the north end at y 195): the rim distance (RimDistance).
    inline std::array<Vec2, 30> constexpr kRidgeFloorPolygon{ {
        { -396.5f, 177.0f }, { -395.5f, 179.5f }, { -401.0f, 185.0f }, { -400.5f, 192.0f }, { -403.0f, 193.0f },
        { -403.5f, 195.5f }, { -405.0f, 195.0f }, { -405.5f, 192.5f }, { -415.5f, 193.5f }, { -416.0f, 181.0f },
        { -410.0f, 158.0f }, { -411.5f, 150.0f }, { -409.0f, 145.0f }, { -400.0f, 138.5f }, { -395.0f, 131.0f },
        { -387.5f, 127.5f }, { -382.5f, 127.5f }, { -378.0f, 129.0f }, { -371.0f, 136.5f }, { -366.5f, 145.5f },
        { -371.0f, 149.5f }, { -366.5f, 147.5f }, { -365.5f, 151.5f }, { -370.5f, 153.0f }, { -374.5f, 158.5f },
        { -377.5f, 157.5f }, { -377.5f, 160.5f }, { -383.0f, 163.5f }, { -391.0f, 173.5f }, { -397.5f, 174.5f },
    } };
    // 4 yd inside every edge (the north neck cut at y 184, its floor open): 856 sq yd. Shadowstep landings, the leash.
    inline std::array<Vec2, 22> constexpr kRidgeArenaPolygon{ {
        { -407.0f, 184.0f }, { -411.0f, 184.0f }, { -411.0f, 182.5f }, { -405.0f, 159.5f }, { -405.0f, 152.5f },
        { -406.0f, 150.5f }, { -404.5f, 147.5f }, { -397.5f, 143.0f }, { -389.5f, 133.5f }, { -384.0f, 132.5f },
        { -380.0f, 134.0f }, { -372.5f, 143.5f }, { -376.5f, 147.5f }, { -376.0f, 152.5f }, { -380.0f, 153.0f },
        { -382.5f, 157.0f }, { -392.0f, 165.5f }, { -394.5f, 169.5f }, { -398.5f, 170.0f }, { -401.5f, 172.5f },
        { -402.0f, 177.0f }, { -401.0f, 178.5f },
    } };
    float constexpr kRidgeZMin = 2.0f;
    float constexpr kRidgeZMax = 22.0f;

    // The plateau's whole floor above z -22.5 (hub and arms, 0.75 yd past the mesh): the fel pulses, "on the plateau".
    inline std::array<Vec2, 45> constexpr kPlateauFloorPolygon{ {
        { -251.0f, 169.0f }, { -254.5f, 166.0f }, { -258.0f, 157.5f }, { -267.5f, 157.5f }, { -279.5f, 154.5f },
        { -277.0f, 149.5f }, { -277.0f, 144.0f }, { -280.0f, 143.5f }, { -279.5f, 141.0f }, { -258.0f, 144.0f },
        { -253.5f, 142.0f }, { -254.0f, 137.5f }, { -255.5f, 137.5f }, { -257.5f, 133.5f }, { -261.0f, 122.5f },
        { -265.5f, 116.5f }, { -265.5f, 114.0f }, { -263.5f, 114.0f }, { -261.0f, 118.5f }, { -259.0f, 118.0f },
        { -256.5f, 116.0f }, { -255.5f, 110.5f }, { -252.5f, 111.5f }, { -252.0f, 116.5f }, { -245.0f, 128.0f },
        { -241.5f, 138.5f }, { -238.0f, 139.0f }, { -237.0f, 137.0f }, { -235.0f, 137.0f }, { -228.0f, 145.0f },
        { -211.0f, 149.5f }, { -207.0f, 149.0f }, { -209.0f, 154.5f }, { -206.5f, 159.5f }, { -232.0f, 159.5f },
        { -230.5f, 169.5f }, { -231.5f, 172.5f }, { -233.5f, 171.0f }, { -234.0f, 172.0f }, { -232.0f, 174.0f },
        { -231.0f, 184.0f }, { -240.5f, 191.0f }, { -243.5f, 188.5f }, { -244.5f, 177.0f }, { -247.0f, 172.0f },
    } };
    // 2 yd short of every true edge, the arm ends open (cut at z -22.5): 1,020 sq yd. The leash, every landing (Feast,
    // hub leap) and every spot center (section 7 #24 A).
    inline std::array<Vec2, 58> constexpr kPlateauArenaPolygon{ {
        { -242.0f, 175.5f }, { -245.0f, 169.0f }, { -249.0f, 167.0f }, { -252.0f, 164.0f }, { -255.5f, 155.0f },
        { -262.5f, 154.5f }, { -263.0f, 152.0f }, { -264.5f, 151.0f }, { -268.5f, 152.0f }, { -270.0f, 150.5f },
        { -272.0f, 150.5f }, { -273.0f, 151.5f }, { -277.0f, 150.5f }, { -275.5f, 149.5f }, { -276.5f, 147.0f },
        { -274.5f, 147.0f }, { -273.0f, 145.5f }, { -255.0f, 147.0f }, { -251.0f, 144.0f }, { -251.0f, 134.0f },
        { -252.5f, 132.0f }, { -255.0f, 131.0f }, { -258.0f, 121.5f }, { -259.5f, 120.0f }, { -259.5f, 118.5f },
        { -256.0f, 117.0f }, { -256.0f, 115.0f }, { -255.0f, 115.5f }, { -254.0f, 119.5f }, { -248.0f, 129.0f },
        { -246.0f, 134.5f }, { -246.5f, 138.0f }, { -244.5f, 140.5f }, { -241.5f, 142.0f }, { -235.0f, 141.5f },
        { -234.5f, 143.0f }, { -229.5f, 147.5f }, { -229.5f, 149.5f }, { -227.5f, 151.5f }, { -221.0f, 151.5f },
        { -219.5f, 153.0f }, { -215.0f, 154.0f }, { -209.5f, 153.5f }, { -209.0f, 155.0f }, { -209.0f, 156.5f },
        { -216.5f, 155.5f }, { -233.0f, 155.5f }, { -234.5f, 156.5f }, { -234.5f, 167.5f }, { -237.0f, 168.5f },
        { -237.5f, 172.0f }, { -235.0f, 175.5f }, { -234.5f, 181.5f }, { -233.0f, 185.5f }, { -234.5f, 185.5f },
        { -237.0f, 188.0f }, { -239.5f, 189.0f }, { -240.5f, 187.5f },
    } };
    float constexpr kPlateauZMin = -23.5f;
    float constexpr kPlateauZMax = -8.0f;

    template <std::size_t N>
    inline Arena PolygonArena(std::array<Vec2, N> const& polygon, float zMin, float zMax)
    {
        return Arena(ArenaRegion::Polygon(std::vector<Vec2>(polygon.begin(), polygon.end()), zMin, zMax));
    }

    inline Arena OggleflintArena() { return PolygonArena(kDenArenaPolygon, kDenZMin, kDenZMax); }
    inline Arena DenFloor() { return PolygonArena(kDenFloorPolygon, kDenZMin, kDenZMax); }
    inline Arena JergoshArena() { return PolygonArena(kHallArenaPolygon, kHallZMin, kHallZMax); }
    inline Arena BazzalanArena() { return PolygonArena(kRidgeArenaPolygon, kRidgeZMin, kRidgeZMax); }
    inline Arena RidgeFloor() { return PolygonArena(kRidgeFloorPolygon, kRidgeZMin, kRidgeZMax); }
    inline Arena TaragamanArena() { return PolygonArena(kPlateauArenaPolygon, kPlateauZMin, kPlateauZMax); }
    inline Arena PlateauFloor() { return PolygonArena(kPlateauFloorPolygon, kPlateauZMin, kPlateauZMax); }

    // The leash arena of a slot (the hard mode kill slot fights in Taragaman's).
    inline Arena ArenaFor(std::uint32_t slot)
    {
        switch (slot)
        {
            case BOSS_OGGLEFLINT:
                return OggleflintArena();
            case BOSS_JERGOSH:
                return JergoshArena();
            case BOSS_BAZZALAN:
                return BazzalanArena();
            case BOSS_TARAGAMAN:
            case BOSS_STARVING:
                return TaragamanArena();
            default:
                return {};
        }
    }

    // `p` itself when `polygon` holds it, else its nearest boundary point moved `insetYd` straight inward (a landing
    // that would leave the floor: the Beating, the Feast, the Shadowstep; section 7 #23 A, #24 A).
    inline Vec2 ClampInto(std::span<Vec2 const> polygon, Vec2 p, float insetYd = 0.25f)
    {
        if (DungeonKit::PointInPolygon(polygon, p))
            return p;
        auto const edge = DungeonKit::NearestEdge(polygon, p);
        if (!edge)
            return p;
        Vec2 const in = DungeonKit::InwardNormal(polygon, edge->edge);
        Vec2 const moved{ edge->point.x + in.x * insetYd, edge->point.y + in.y * insetYd };
        return DungeonKit::PointInPolygon(polygon, moved) ? moved : edge->point;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // A boss at the edge of his arena (Bazzalan, Taragaman): a target on the band past it is still his, he stands on
    // his own side of the edge and reaches it. The engine half is RagefireChasmKit.h ArenaEdge.
    // ----------------------------------------------------------------------------------------------------------------
    float constexpr kEdgeReachYd = 4.5f;            // the band's width: melee range is 5 yd or more, 3D
    float constexpr kStandInsetYd = 0.25f;          // where he stands is this far inside his arena ...
    float constexpr kStandMarginYd = 0.15f;         // ... and never nearer to its boundary than this
    float constexpr kStandSearchYd = 4.f;           // how far a corner's spot may be from its edge point

    // How far `p` is inside `polygon`; 0 off it.
    inline float InsideBy(std::span<Vec2 const> polygon, Vec2 p)
    {
        if (!DungeonKit::PointInPolygon(polygon, p))
            return 0.f;
        auto const edge = DungeonKit::NearestEdge(polygon, p);
        return edge ? edge->distance : 0.f;
    }

    // Where a boss may stand for `p`: `p` itself when it is strictly inside, else the nearest edge point moved straight
    // in, else (a corner, a narrow end) the nearest point round it that is strictly inside. On the boundary itself, or
    // at a corner's bare edge point (ClampInto), the leash would count him as off it.
    inline Vec2 StandSpot(std::span<Vec2 const> polygon, Vec2 p)
    {
        if (InsideBy(polygon, p) >= kStandMarginYd)
            return p;
        auto const edge = DungeonKit::NearestEdge(polygon, p);
        if (!edge)
            return p;
        Vec2 const in = DungeonKit::InwardNormal(polygon, edge->edge);
        Vec2 const straight{ edge->point.x + in.x * kStandInsetYd, edge->point.y + in.y * kStandInsetYd };
        if (InsideBy(polygon, straight) >= kStandMarginYd)
            return straight;
        int constexpr bearings = 32;
        for (float r = kStandInsetYd; r <= kStandSearchYd; r += 0.125f)
        {
            Vec2 best{};
            float deepest = 0.f;
            for (int i = 0; i < bearings; ++i)
            {
                Vec2 const at = DungeonKit::Advance(edge->point, 2.f * DungeonKit::kPi * float(i) / float(bearings), r);
                float const inside = InsideBy(polygon, at);
                if (inside > deepest)
                {
                    best = at;
                    deepest = inside;
                }
            }
            if (deepest >= kStandMarginYd)
                return best;
        }
        return edge->point;
    }

    // Back onto the arena with the target in melee range, straight toward it: in range all the way.
    inline Vec2 BackSpot(std::span<Vec2 const> polygon, Vec2 self, Vec2 target)
    {
        float const distance = DungeonKit::Distance(self, target);
        float const bearing = DungeonKit::BearingTo(self, target);
        for (float d = kStandInsetYd; d < distance; d += kStandInsetYd)
        {
            Vec2 const at = DungeonKit::Advance(self, bearing, d);
            if (InsideBy(polygon, at) >= kStandMarginYd)
                return at;
        }
        return StandSpot(polygon, self);
    }

    // Whether the engine's own step back (MotionMaster::MoveBackwards: `distance` from the target on his side of it)
    // ends strictly inside.
    inline bool BackstepStays(std::span<Vec2 const> polygon, Vec2 self, Vec2 target, float distance)
    {
        return InsideBy(polygon, DungeonKit::Advance(target, DungeonKit::BearingTo(target, self), distance))
            >= kStandMarginYd;
    }

    enum class EdgeAct : std::uint8_t
    {
        Chase,          // the engine's own chase
        Stand,          // where he is
        Walk,           // to `spot`
    };

    struct EdgeView
    {
        Vec2 self;
        Vec2 target;
        bool selfInside = true;     // he is on his arena
        bool targetInside = true;   // his target is on it
        bool targetInReach = true;  // his target is on the reach arena
        bool inMelee = false;
    };

    struct EdgeStep
    {
        EdgeAct act = EdgeAct::Chase;
        Vec2 spot;
    };

    // Off his arena he walks back first, whatever else holds (the leash counts; only a chase of a target inside, which
    // brings him back by itself, goes on until he is in range). Then: a target inside is chased, one out of reach is
    // the reach guard's, one on the band in melee range is fought from where he is, else he walks to its stand spot.
    inline EdgeStep NextEdgeStep(std::span<Vec2 const> polygon, EdgeView const& v)
    {
        if (!v.selfInside && !v.targetInside)
            return { EdgeAct::Walk, StandSpot(polygon, v.self) };
        if (!v.selfInside && v.inMelee)
            return { EdgeAct::Walk, BackSpot(polygon, v.self, v.target) };
        if (v.targetInside)
            return { EdgeAct::Chase, v.self };
        if (!v.targetInReach || v.inMelee)
            return { EdgeAct::Stand, v.self };
        return { EdgeAct::Walk, StandSpot(polygon, v.target) };
    }

    // Where the floor past an edge climbs, how far over the edge's own floor a target may stand: a target `band` yd off
    // the edge is in melee range (3D) of the spot inside it up to here.
    inline float constexpr kReachMelee3dYd = 5.f;
    inline std::array<float, 4> constexpr kReachBandsYd{ 1.5f, 2.5f, 3.5f, kEdgeReachYd };

    inline float ReachRiseYd(float bandYd)
    {
        float const plane = bandYd + kStandInsetYd + 0.1f;      // 0.1: a corner's spot is a little farther in
        return std::sqrt(kReachMelee3dYd * kReachMelee3dYd - plane * plane);
    }

    // `own` grown by kEdgeReachYd: a quad beside every edge, a circle at every corner, in the z band [zMin, zMax]. An
    // edge whose floor `climbFloorOf(edge)` gives (its lowest height; nullopt: level floor) grows in kReachBandsYd
    // steps, each up to its own ReachRiseYd over that floor; a corner takes the lower of its two edges.
    template <typename ClimbFloorOf>
    inline Arena EdgeReachArena(Arena own, std::span<Vec2 const> polygon, float zMin, float zMax,
        ClimbFloorOf&& climbFloorOf)
    {
        std::size_t const n = polygon.size();
        for (std::size_t i = 0; i < n; ++i)
        {
            Vec2 const a = polygon[i];
            Vec2 const b = polygon[(i + 1) % n];
            Vec2 const in = DungeonKit::InwardNormal(polygon, i);
            std::optional<float> const climb = climbFloorOf(i);
            std::optional<float> corner = climbFloorOf((i + n - 1) % n);
            if (climb)
                corner = corner ? std::min(*corner, *climb) : *climb;
            auto grow = [&](float yd, float quadZ, float circleZ)
            {
                Vec2 const off{ -in.x * yd, -in.y * yd };
                own.regions.push_back(ArenaRegion::Polygon({ a, b, { b.x + off.x, b.y + off.y },
                    { a.x + off.x, a.y + off.y } }, zMin, quadZ));
                own.regions.push_back(ArenaRegion::Circle(a, yd, zMin, circleZ));
            };
            if (!climb && !corner)
            {
                grow(kEdgeReachYd, zMax, zMax);
                continue;
            }
            for (float const yd : kReachBandsYd)
                grow(yd, climb ? *climb + ReachRiseYd(yd) : zMax, *corner + ReachRiseYd(yd));
        }
        return own;
    }

    // How far `p` (on the ridge) is from the nearest rim; 0 off it. Section 7 #23 A: a player within
    // Bazzalan::kRimSkipYd of a rim is never a Shadowstep target.
    inline float RimDistance(Vec2 p)
    {
        std::span<Vec2 const> const floor(kRidgeFloorPolygon);
        if (!DungeonKit::PointInPolygon(floor, p))
            return 0.f;
        auto const edge = DungeonKit::NearestEdge(floor, p);
        return edge ? edge->distance : 0.f;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // The instance save string (section 3.2 item 2): header "RFC", the 5 boss states, then the hard mode flag. The
    // stock instance saves no header and no data, so any other string is ignored.
    // ----------------------------------------------------------------------------------------------------------------
    char constexpr kSaveHeader[] = "RFC";

    enum SaveExtra : std::size_t
    {
        EXTRA_HARD_MODE = 0,
    };
    std::size_t constexpr kSaveExtraCount = 1;

    struct RfcSave
    {
        BossStates states{};
        std::uint32_t hardMode = 0;
    };

    inline std::string FormatRfcSave(RfcSave const& s)
    {
        std::vector<std::uint32_t> const states(s.states.begin(), s.states.end());
        std::vector<std::uint32_t> extras(kSaveExtraCount, 0);
        extras[EXTRA_HARD_MODE] = s.hardMode;
        return DungeonKit::FormatStates(kSaveHeader, states, extras);
    }

    // False on a missing or foreign header: the save is ignored. Loaded values are sanitized: states through
    // SanitizeLoadedState, the flag to 0 / 1, and the hard mode kill slot needs Taragaman DONE.
    inline bool ParseRfcSave(std::string const& in, RfcSave& out)
    {
        out = RfcSave{};
        DungeonKit::StateSave raw;
        if (!DungeonKit::ParseStates(in, kSaveHeader, kBossCount, kSaveExtraCount, raw))
            return false;
        for (std::size_t i = 0; i < kBossCount; ++i)
            out.states[i] = raw.states[i];
        out.hardMode = raw.extras[EXTRA_HARD_MODE] ? 1 : 0;
        if (out.states[BOSS_TARAGAMAN] != DungeonKit::State::Done)
            out.states[BOSS_STARVING] = DungeonKit::State::NotStarted;
        return true;
    }

    // ----------------------------------------------------------------------------------------------------------------
    // Tuning (handoff sections 3.5 rule 36, 3.6, 3.7, 7 #35; SP Build specs). One table per boss. NH<T>{ normal,
    // heroic } reads with (IsHeroicMap(me)); Tri<T>{ normal, heroic, hard mode } reads with (ModeFor(heroic, hard)).
    // Damage is percent of the reference row (DungeonKit::RefFlat / RefFlatOn with the boss as the owner) unless the
    // name says Flat or Tank; times are milliseconds; ranges yards.
    // ----------------------------------------------------------------------------------------------------------------
    enum class Mode : std::uint8_t
    {
        Normal,
        Heroic,
        HardMode,
    };

    constexpr Mode ModeFor(bool heroic, bool hardMode)
    {
        return !heroic ? Mode::Normal : hardMode ? Mode::HardMode : Mode::Heroic;
    }

    template <typename T>
    struct Tri
    {
        T normal;
        T heroic;
        T hardMode;

        constexpr T Get(Mode mode) const
        {
            return mode == Mode::Normal ? normal : mode == Mode::Heroic ? heroic : hardMode;
        }
        constexpr T operator()(Mode mode) const { return Get(mode); }
    };

    // Section 3.5 rule 30: no hit under a 1.5 s warning on normal (bosses level 16).
    std::uint32_t constexpr kNormalWarningFloorMs = 1500;

    // Reference rows the percents mean (non-tank, tank): BM conf `16:1100:1080` (section 7 #3 A) and `389h:60`
    // 4,120 / 4,110. Host arithmetic only: the scripts read BM's provider.
    struct ReferenceRow
    {
        std::uint32_t nonTank;
        std::uint32_t tank;
    };
    ReferenceRow constexpr kReferenceNormal{ 1100, 1080 };
    ReferenceRow constexpr kReferenceHeroic{ 4120, 4110 };

    namespace Oggleflint
    {
        NH<std::uint32_t> constexpr kHealth{ 21360, 317408 };           // HealthModifier 60 on 356; WP-H's override

        // OG1 Borer Hunt, the chase (marks nothing: no damage, no telegraph)
        NH<std::uint32_t> constexpr kHuntFirstMs{ 10000, 10000 };
        NH<std::uint32_t> constexpr kHuntEveryMs{ 15000, 12000 };
        std::uint32_t constexpr kHuntSwingGapMs = 3000;                 // a hunt and a swing never start within 3 s
        std::uint32_t constexpr kChaseMs = 4000;
        NH<float> constexpr kChaseSpeed{ 4.f, 5.f };
        float constexpr kChaseRadius = 3.f;
        // Ruling 15 (heroic): a Borer joins at 40 s and every 40 s after, no cap, while an unhunted, unbeaten, living
        // player exists (else it waits for the next mark; section 7 #28 A).
        std::uint32_t constexpr kExtraBorerEveryMs = 40000;

        // OG2 the eruption
        std::uint32_t constexpr kEruptionWarnMs = 2000;
        float constexpr kEruptionRadius = 4.f;
        NH<float> constexpr kEruptionPct{ 30.f, 45.f };                 // Physical, vertical knock-up, Weakened

        // OG3 Club Swing
        NH<std::uint32_t> constexpr kSwingFirstMs{ 6000, 6000 };
        NH<std::uint32_t> constexpr kSwingEveryMs{ 12000, 12000 };
        std::uint32_t constexpr kSwingWarnMs = 2000;
        float constexpr kSwingAngleDeg = 90.f;
        float constexpr kSwingLength = 8.f;
        NH<float> constexpr kSwingPct{ 30.f, 40.f };                    // Weakened (not the tank)
        float constexpr kSwingTankPct = 10.f;                           // of the tank row, both difficulties (#35)

        // OG4 the Beating (heroic)
        std::uint32_t constexpr kBeatingFirstMs = 15000;
        std::uint32_t constexpr kBeatingEveryMs = 20000;
        std::uint32_t constexpr kBeatingBlows = 3;
        std::uint32_t constexpr kBeatingBlowMs = 1500;                  // the next marker appears as the last lands
        float constexpr kBeatingRadius = 3.f;
        float constexpr kBeatingPct = 35.f;                             // Weakened per blow

        static_assert(kEruptionWarnMs >= kNormalWarningFloorMs && kSwingWarnMs >= kNormalWarningFloorMs);
    }

    namespace Jergosh
    {
        NH<std::uint32_t> constexpr kHealth{ 21490, 335352 };           // HealthModifier 70 on 307; WP-H's override

        // JR1 Immolate (kickable; never one already burning; none while kImmolateMaxBurning players burn)
        NH<std::uint32_t> constexpr kImmolateFirstMs{ 3000, 3000 };
        NH<std::uint32_t> constexpr kImmolateEveryMs{ 3000, 3000 };
        std::uint32_t constexpr kImmolateCastMs = 2000;
        std::uint32_t constexpr kImmolateMaxBurning = 3;
        // Immolate and Drain Soul: a kick locks the school this long, whatever the kick's own lockout is (4 to 8 s).
        std::uint32_t constexpr kKickLockMs = 2000;
        std::uint32_t constexpr kImmolateDurationMs = 21000;
        std::uint32_t constexpr kImmolateTickMs = 3000;
        std::uint32_t constexpr kImmolateFlatDirect = 56;               // normal: stock values (#35)
        std::uint32_t constexpr kImmolateFlatTick = 16;
        float constexpr kImmolateHeroicDirectPct = 5.f;
        float constexpr kImmolateHeroicTickPct = 5.f;

        // JR2 Conflagrate (not interruptible; every burn is consumed, then heroic re-lights whom another's ring hit)
        NH<std::uint32_t> constexpr kConflagrateFirstMs{ 16000, 16000 };
        NH<std::uint32_t> constexpr kConflagrateEveryMs{ 20000, 20000 };
        std::uint32_t constexpr kConflagrateCastMs = 2500;
        NH<float> constexpr kConflagrateRadius{ 5.f, 6.f };
        NH<float> constexpr kConflagrateBearerPct{ 15.f, 20.f };        // no Weakened
        NH<float> constexpr kConflagrateOthersPct{ 35.f, 45.f };        // Weakened

        // JR3 Curse of Weakness 18267 (stock cast)
        std::uint32_t constexpr kCurseFirstMs = 1000;
        std::uint32_t constexpr kCurseEveryMs = 30000;

        // JR4 Drain Soul and JR5 the wisp (heroic; section 7 #21 A, #29 A)
        std::uint32_t constexpr kDrainSoulFirstMs = 10000;
        std::uint32_t constexpr kDrainSoulEveryMs = 20000;
        std::uint32_t constexpr kDrainSoulChannelMs = 3000;
        float constexpr kSoulTearPct = 25.f;                            // Shadow, the owner
        float constexpr kWispSpawnAheadYd = 4.f;                        // toward kOfferingSpot: no catch on spawn
        float constexpr kWispSpeed = 3.f;
        float constexpr kWispTouchYd = 2.f;
        float constexpr kWispScale = 1.75f;
        float constexpr kSoulSickHealingPct = 25.f;                     // less healing taken
        std::uint32_t constexpr kSoulSickMs = 30000;
        float constexpr kTithePct = 15.f;                               // damage dealt per stack, no cap (ruling 15)
        float constexpr kTitheScaleStep = 0.04f;                        // the look: at most kTitheScaleSteps
        std::uint32_t constexpr kTitheScaleSteps = 5;

        static_assert(kConflagrateCastMs >= kNormalWarningFloorMs && kImmolateCastMs >= kNormalWarningFloorMs);
    }

    namespace Bazzalan
    {
        NH<std::uint32_t> constexpr kHealth{ 23140, 332668 };           // HealthModifier 65 on 356; WP-H's override

        // BZ1 Sinister Strike and combo points, BZ2 the finisher bag
        std::uint32_t constexpr kStrikeFirstMs = 2000;
        NH<std::uint32_t> constexpr kStrikeEveryMs{ 3000, 2000 };
        std::uint32_t constexpr kComboMax = 5;
        std::uint32_t constexpr kFinisherCastMs = 2000;

        // BZ3 Eviscerate (kickable)
        NH<float> constexpr kEvisceratePctTank{ 35.f, 50.f };

        // BZ4 Rupture: normal 40% in all over 12 s, heroic 2% every 2 s until the end of the fight
        std::uint32_t constexpr kRuptureTickMs = 2000;
        std::uint32_t constexpr kRuptureNormalMs = 12000;
        float constexpr kRuptureNormalTotalPct = 40.f;
        float constexpr kRuptureHeroicTickPct = 2.f;
        constexpr float RuptureTickPct(bool heroic)
        {
            return heroic ? kRuptureHeroicTickPct
                : kRuptureNormalTotalPct / float(kRuptureNormalMs / kRuptureTickMs);
        }

        // BZ5 Fan of Knives (normal only)
        float constexpr kFanRadius = 8.f;
        std::uint32_t constexpr kFanWarnMs = 2000;
        float constexpr kFanPct = 35.f;                                 // Weakened

        // BZ6 Envenom (heroic, kickable): tank row per Deadly Poison stack consumed
        float constexpr kEnvenomPctPerStackTank = 10.f;

        // BZ7 Shadowstep and Fan of Knives (heroic)
        std::uint32_t constexpr kShadowstepCount = 3;                   // three different players
        float constexpr kShadowstepBehindYd = 2.f;
        std::uint32_t constexpr kShadowstepWarnMs = 2000;
        float constexpr kShadowstepRadius = 6.f;
        float constexpr kShadowstepPct = 45.f;                          // Weakened and Crippling Poison per spin
        float constexpr kRimSkipYd = 2.f;                               // section 7 #23 A (RimDistance)

        // BZ8 poisons
        std::uint32_t constexpr kDeadlyEveryMs = 2000;
        std::uint32_t constexpr kDeadlyChancePct = 50;
        std::uint32_t constexpr kDeadlyStacks = 5;
        std::uint32_t constexpr kDeadlyMs = 12000;
        std::uint32_t constexpr kDeadlyTickMs = 3000;
        std::uint32_t constexpr kDeadlyFlatPerStack = 6;                // normal: stock value (#35)
        float constexpr kDeadlyHeroicTankPctPerStack = 0.5f;            // of the tank row (#35)
        float constexpr kWoundHealingPctPerStack = 10.f;                // heroic
        std::uint32_t constexpr kWoundStacks = 3;
        std::uint32_t constexpr kWoundMs = 15000;
        float constexpr kCripplingSlowPct = 50.f;                       // heroic, a spin hit
        std::uint32_t constexpr kCripplingMs = 8000;

        static_assert(kFanWarnMs >= kNormalWarningFloorMs && kFinisherCastMs >= kNormalWarningFloorMs);
    }

    namespace Taragaman
    {
        Tri<std::uint32_t> constexpr kHealth{ 24351, 418124, 814884 };  // HealthModifier 68.4 on 356; WP-H; the pour

        // TG1 Feast (section 7 #30 A)
        Tri<std::uint32_t> constexpr kFeastFirstMs{ 18000, 16000, 15000 };
        Tri<std::uint32_t> constexpr kFeastEveryMs{ 20000, 15000, 15000 };  // hard mode: the fallback (ruling 16)
        Tri<std::uint32_t> constexpr kFeastMarkMs{ 3000, 3000, 2000 };      // ruling 12
        Tri<float> constexpr kFeastBitePct{ 25.f, 40.f, 45.f };             // Physical, not avoidable: no Weakened
        float constexpr kFeastRangeYd = 40.f;                               // of the hub, on PlateauFloor()
        std::uint32_t constexpr kFeastAfterSetPieceMs = 4000;               // a Feast due during TG3 / TG6 waits
        // Phase 2's hold: the Feast and the combo both keep heroic's pace (R-1-TG Q1 C, host-tested). Never under
        // kComboNovaAfterSpinMs less the last spots' 0.75 s: no Feast inside a combo.
        std::uint32_t constexpr kPhase2FeastHoldMs = 2000;
        std::uint32_t constexpr kFeastAfterPhaseMs = 2000;
        float constexpr kGorgeBelowPct = 50.f;                              // the prey's health at the landing
        float constexpr kGorgeHealPct = 3.f;                                // of his max health
        float constexpr kGorgedPct = 10.f;                                  // damage dealt per stack
        Tri<std::uint32_t> constexpr kGorgedCap{ 3, 0, 0 };                 // 0: no cap (ruling 15)
        // Hard mode: no timer, the moment a player drops under the line (polled), at least the gap apart
        float constexpr kStarvingLinePct = 30.f;
        std::uint32_t constexpr kStarvingPollMs = 250;
        std::uint32_t constexpr kStarvingGapMs = 6000;

        // TG2 Devour (heroic, hard mode; kickable)
        std::uint32_t constexpr kDevourTicks = 5;
        std::uint32_t constexpr kDevourTickMs = 1000;                       // the first at 1 s
        Tri<float> constexpr kDevourTickPct{ 0.f, 14.f, 16.f };
        float constexpr kDevourHealPct = 1.f;                               // of his max health per tick
        float constexpr kDevourRangeYd = 100.f;
        std::uint32_t constexpr kDevourInterruptEveryMs = 15000;            // InterruptEntry `every`

        // TG3 Felstorm's ring
        Tri<std::uint32_t> constexpr kFelstormFirstMs{ 12000, 10000, 10000 };
        Tri<std::uint32_t> constexpr kFelstormEveryMs{ 30000, 25000, 25000 };
        std::uint32_t constexpr kFelstormCastMs = 2000;
        Tri<std::uint32_t> constexpr kFelstormSpinMs{ 6000, 5000, 5000 };
        Tri<float> constexpr kFelstormRadius{ 8.f, 10.f, 10.f };
        std::uint32_t constexpr kFelstormTickMs = 1000;
        Tri<float> constexpr kFelstormTickPct{ 8.f, 20.f, 20.f };           // Physical, lingering: no Weakened
        // Hard mode drift (section 7 #25 A)
        float constexpr kDriftSpeed = 3.f;
        float constexpr kDriftClampYd = 8.f;                                // the ring's center, of his spawn
        std::uint32_t constexpr kDriftRepickMs = 2000;

        // TG4 fel pulses: everyone on PlateauFloor()
        Tri<float> constexpr kPulsePct{ 0.f, 4.f, 5.f };                    // per kFelstormTickMs, Fire, no Weakened

        // TG5 fel spots
        std::uint32_t constexpr kSpotEveryMs = 500;
        std::uint32_t constexpr kSpotCount = 10;                            // per spin
        Tri<float> constexpr kSpotRadius{ 0.f, 4.f, 5.f };
        Tri<float> constexpr kSpotOffsetMax{ 0.f, 4.f, 3.f };               // of the next player of the rotation
        Tri<std::uint32_t> constexpr kSpotWarnMs{ 0, 1500, 1250 };
        Tri<float> constexpr kSpotPct{ 0.f, 35.f, 45.f };                   // Fire, Weakened
        std::uint32_t constexpr kSpotRerolls = 8;

        // TG6 Searing Nova (section 7 #19 A)
        Tri<std::uint32_t> constexpr kNovaFirstMs{ 25000, 22000, 22000 };
        Tri<std::uint32_t> constexpr kNovaEveryMs{ 30000, 25000, 25000 };
        Tri<std::uint32_t> constexpr kNovaCastMs{ 4000, 4000, 3000 };
        Tri<float> constexpr kNovaPct{ 50.f, 75.f, 90.f };                  // Fire, no Weakened
        Tri<std::uint32_t> constexpr kNovaSpikes{ 3, 2, 2 };
        float constexpr kNovaRangeYd = 60.f;
        float constexpr kNovaEyeYd = 3.05f;                                 // HideSpec.Eye, fixed (rule 29)
        float constexpr kSpikeBlockerYd = 2.f;                              // HideSpec blocker radius
        float constexpr kSpikeGoSize = 2.f;
        float constexpr kSpikeHideYd = 5.f;                                 // behind the spike's center

        // TG7 / TG8 / TG9 the blood lake (hard mode phase 2; section 7 #22 A, #27 A)
        float constexpr kPhase2Pct = 30.f;
        std::uint32_t constexpr kComboEveryMs = 25000;
        std::uint32_t constexpr kComboNovaAfterSpinMs = 2000;
        std::uint32_t constexpr kGlobuleEveryMs = 20000;                    // the first wave at the phase's start
        std::uint32_t constexpr kGlobuleHealth = 6000;
        float constexpr kGlobuleSpeed = 2.5f;
        float constexpr kGlobuleReachYd = 2.f;
        float constexpr kGlobuleDrunkHealPct = 2.f;                         // of his max health, plus a Gorged stack
        float constexpr kGlobuleBurstRadius = 6.f;
        std::uint32_t constexpr kGlobuleBurstWarnMs = 1500;
        float constexpr kGlobuleBurstPct = 30.f;                            // Shadow, Weakened

        // TG10 Uppercut 18072 (stock cast)
        std::uint32_t constexpr kUppercutFirstMinMs = 3000;
        std::uint32_t constexpr kUppercutFirstMaxMs = 5000;
        std::uint32_t constexpr kUppercutEveryMs = 10000;

        // The trigger: "Hungerer's Blood" (section 7 #15 A, #17 A)
        std::uint32_t constexpr kHungerersBloodMs = 10 * 60 * 1000;

        static_assert(kFelstormCastMs >= kNormalWarningFloorMs && kNovaCastMs.normal >= kNormalWarningFloorMs
            && kFeastMarkMs.normal >= kNormalWarningFloorMs);
    }
}

#endif
