/*
 * mod-dungeon-bosses, Zul'Farrak: the engine glue of the Zul'Farrak skeleton (WP-S0; handoff section 3.2). The pure
 * half is ZulFarrakRework.h; the shared kit (src/Kit/) is under all of it. Owned by WP-S0 until it reports, then by the
 * orchestrator (a WP asks for a change in its report).
 *
 *   NoAssist              section 3.5 rule 27, LESSONS L1: SetAssistanceTimer(0) every UpdateAI, before
 *                         UpdateVictim() (the template's DONT_CALL_ASSISTANCE stops only the first call). Every boss;
 *                         the crew are exempt (they help each other). tests/zul_farrak_test.cpp checks every boss file.
 *   LeashOptions          the arena guard of a Zul'Farrak boss: the arena leash, no grips (the kit's LeashPreset with
 *                         the Ragefire values). The arenas are the rooms' whole floors (ZulFarrakRework.h), so a victim
 *                         off the arena is off the room: the boss turns to the top-threat unit on it.
 *   OnBossPull            the pull line: "zf-build <boss> pull health=<max> heroic=<0|1> hardmode=<0|1>" (section 3.5).
 *   <Room>FloorBounds     the bots' hard bounds (`.Within(...)`, section 3.5 rule 14): a room's arena with its z band.
 *   Crew                  the crew's mode through the instance (CrewCreature, GetCrewMode, SetCrewMode): CR's
 *                         BlyCrew.h builds on these; no other WP writes a crew member's faction (rule 28).
 *   PyramidStageDirector  the Pyramid's stage hooks: D4a registers stage 1 (the Block), D4b stages 2 and 3 (the Stair,
 *                         the Altar), each from its AddSC_ function; the instance runs the one in play (below).
 *
 * The instance (instance_zulfarrak_rework.cpp) owns: the 9 slots, the Pyramid's stage machine (starts, wins, wipes,
 * snapshots, the crew's restore), slot 5 and slot 6 (never a BossAI), the crew's modes and mask, the paths and the
 * Test's key, the End Door, Gahz'rilla's summon, the hard mode flag, its kill slot and loot bit, and the "ZFR" save.
 * A boss reads its data with GetData (ZulFarrakRework.h ZfData) and reports with SetData.
 */

#ifndef MOD_DUNGEON_BOSSES_ZUL_FARRAK_KIT_H
#define MOD_DUNGEON_BOSSES_ZUL_FARRAK_KIT_H

#include "ArenaGuard.h"
#include "Define.h"
#include "MechanicRegistry.h"
#include "ZulFarrakRework.h"
#include <functional>
#include <memory>
#include <optional>
#include <string>

class Creature;
class InstanceScript;

namespace ZulFarrak
{
    // Section 3.5 rule 27 (LESSONS L1): no assist calls, every tick. Call first thing in UpdateAI, before
    // UpdateVictim().
    void NoAssist(Creature* me);
}

namespace ZulFarrakRework
{
    uint32 constexpr kLeashNoTargetMs = 10000;      // evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long
    bool constexpr kLeashSwitchToInside = true;

    // The arena guard options of a Zul'Farrak boss; `boss` names the log prefix "zf-build <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);

    // The pull of a reworked boss, from JustEngagedWith once the boss is engaged.
    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode = false);

    // The bots' bounds of a room (polygons and circles of the arena, with their z bands).
    BossMechanics::SpotBounds BoundsOf(Arena const& arena);
    BossMechanics::SpotBounds ThekaFloorBounds();       // the courtyard
    BossMechanics::SpotBounds AntusulFloorBounds();     // the den and its chamber
    BossMechanics::SpotBounds ZumrahFloorBounds();      // the bowl and the tongue
    BossMechanics::SpotBounds BlockFloorBounds();       // the Pyramid top and the landing
    BossMechanics::SpotBounds StairFloorBounds();       // the stair
    BossMechanics::SpotBounds PlazaFloorBounds();       // the Altar and the crew's fight
    BossMechanics::SpotBounds UkorzFloorBounds();       // the mesa
    BossMechanics::SpotBounds PoolFloorBounds();        // the shore and the water

    // ----------------------------------------------------------------------------------------------------------------
    // The crew (section 3.2 item 4): the instance stores each member's CrewMode; a change goes through SetData
    // (DATA_CREW_MODE_BASE + member), which logs "zf-build crew <entry> <old> <new>" and sends ACTION_ZF_CREW_MODE to
    // the member. CR's AI applies the mode (faction, react state, gossip, movement) in its DoAction and, after a create
    // or a respawn, in Reset / JustRespawned by reading GetCrewMode.
    // ----------------------------------------------------------------------------------------------------------------
    Creature* CrewCreature(InstanceScript* instance, uint32 member);
    std::optional<uint32> CrewMemberOf(Creature const* creature);
    CrewMode GetCrewMode(InstanceScript const* instance, uint32 member);
    void SetCrewMode(InstanceScript* instance, uint32 member, CrewMode mode);

    // ----------------------------------------------------------------------------------------------------------------
    // The Pyramid's stage hooks (section 3.2 item 3). One director per stage; the instance makes it when its stage
    // comes into play (the previous stage won, a reload, a GM's `.dbtest zf stage`) and drops it when the stage is won.
    // The instance itself decides starts, wins and wipes (ZulFarrakRework.h PyramidStart / PyramidComplete /
    // PyramidWipe), restores the crew and the counters, and writes slot 5; a director spawns, moves and despawns its
    // stage's units and reports with SetData(DATA_PYRAMID_COMPLETE / _FAIL / _START, stage).
    //
    //   stage 1 (D4a)  starts at the Executioner's pull (his AI sends START 1; his evade FAIL 1); won by his death
    //                  (the instance sees it). OnWait after a wipe: nothing (he evades home himself).
    //   stage 2 (D4b)  starts when a cage opens (go_zf_troll_cage, the instance) and again 10 s after a living player
    //                  stands on the landing after a wipe or a reload; won when D4b sends COMPLETE 2 (wave 2's last
    //                  troll). OnStart spawns wave 1 (kWaveSpawns); the sends, the barrels and wave 2 are D4b's.
    //   stage 3 (D4b)  the instance starts it kAltarDelayMs after stage 2 is won (OnStart(false): wave 3, Sezz'ziz,
    //                  Nekrum); after a wipe or a reload OnWait puts them back idle at the plaza and the first pull
    //                  sends START 3; won when Sezz'ziz and Nekrum are both dead (the instance sees it: slot 5 DONE,
    //                  credit).
    //
    // A wipe (no living player in kPyramidRegion while the stage runs, or the owner's FAIL) calls OnEnd(false), then
    // restores the snapshot (crew respawned, modes, Offerings, Blood Price), then OnWait. Every hook may be called
    // after a cold load (RB-2): never assume OnStart ran.
    // ----------------------------------------------------------------------------------------------------------------
    class PyramidStageDirector
    {
    public:
        explicit PyramidStageDirector(InstanceScript* instance) : _instance(instance) { }
        virtual ~PyramidStageDirector() = default;

        // The stage began (restart: it had begun before: a wipe or a reload came between).
        virtual void OnStart(bool /*restart*/) { }
        // The stage is in play and idle (the previous stage won, a wipe, a reload).
        virtual void OnWait() { }
        // Every instance update while the stage is in play (running or idle).
        virtual void OnUpdate(uint32 /*diff*/) { }
        // The stage ended: won, or lost (before the instance restores the crew). Despawn the stage's units here.
        virtual void OnEnd(bool /*won*/) { }
        // Any creature of the map entering the world or dying (the stage's own summons included).
        virtual void OnCreatureCreate(Creature* /*creature*/) { }
        virtual void OnCreatureDeath(Creature* /*creature*/) { }

    protected:
        InstanceScript* Instance() const { return _instance; }

    private:
        InstanceScript* _instance;
    };

    using PyramidStageFactory = std::function<std::unique_ptr<PyramidStageDirector>(InstanceScript* instance)>;

    // From the owner's AddSC_ function (once per stage; a second call replaces the first).
    void RegisterPyramidStage(uint32 stage, PyramidStageFactory factory);
    // The instance: nullptr when nothing is registered for `stage` (the stage then only runs on its owners' messages).
    std::unique_ptr<PyramidStageDirector> CreatePyramidStage(uint32 stage, InstanceScript* instance);
}

#endif
