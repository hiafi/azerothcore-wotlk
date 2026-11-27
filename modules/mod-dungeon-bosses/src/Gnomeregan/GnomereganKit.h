/*
 * mod-dungeon-bosses, Gnomeregan: the engine glue of the Gnomeregan skeleton (WP-S0; handoff section 3.2). The pure
 * half is GnomereganRework.h; the five machines' contract is GnomereganMachines.h; the shared kit (src/Kit/) is under
 * all of it. Owned by WP-S0 until it reports, then by the orchestrator (a WP asks for a change in its report).
 *
 *   NoAssist              section 3.2 item 9, section 3.5 rule 29, LESSONS L1: SetAssistanceTimer(0) every UpdateAI,
 *                         before UpdateVictim() (the template's DONT_CALL_ASSISTANCE stops only the first call). Every
 *                         boss, called qualified: `GnomereganRework::NoAssist(me);` (tests/gnomeregan_test.cpp checks
 *                         every `struct boss_` of every boss file).
 *   LeashOptions          the arena guard of a Gnomeregan boss: the arena leash, no grips (the kit's LeashPreset with
 *                         the Ragefire / Zul'Farrak values). A victim off the arena is off the room: the boss turns to
 *                         the top-threat unit on it.
 *   OnBossPull            the pull line: "gnomer-build <boss> pull health=<max> heroic=<0|1> hardmode=<0|1>".
 *   <Room>FloorBounds     the bots' hard bounds (`.Within(...)`, section 3.5 rule 14): a room's arena with its z band.
 *   Instance helpers      GnomereganInstance (the instance or nullptr off map 90), SlotState, IsHardModeArmed.
 *
 * The instance (instance_gnomeregan_rework.cpp) owns: the 7 slots, the Workshop Door and the Final Chamber, the End
 * NPCs, Crowd Pummeler's chest, the hard mode flag, its verdict, its kill slot and loot bit, the Finder section, and
 * the "GNR" save. A boss reads its data with GetData (GnomereganRework.h GnomereganData) and reports with SetData.
 */

#ifndef MOD_DUNGEON_BOSSES_GNOMEREGAN_KIT_H
#define MOD_DUNGEON_BOSSES_GNOMEREGAN_KIT_H

#include "ArenaGuard.h"
#include "Define.h"
#include "GnomereganRework.h"
#include "MechanicRegistry.h"
#include <string>

class Creature;
class InstanceScript;
class WorldObject;

namespace GnomereganRework
{
    // Section 3.2 item 9 (LESSONS L1): no assist calls, every tick. Call first thing in UpdateAI, before
    // UpdateVictim(), always qualified (the host test greps for "GnomereganRework::NoAssist(me);").
    void NoAssist(Creature* me);

    uint32 constexpr kLeashNoTargetMs = 10000;      // evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long
    bool constexpr kLeashSwitchToInside = true;

    // The arena guard options of a Gnomeregan boss; `boss` names the log prefix "gnomer-build <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);

    // The pull of a reworked boss, from JustEngagedWith once the boss is engaged (after the health is set).
    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode = false);

    // The bots' bounds of a room (polygons and circles of the arena, with their z bands).
    BossMechanics::SpotBounds BoundsOf(Arena const& arena);
    BossMechanics::SpotBounds TechbotFloorBounds();         // the dish
    BossMechanics::SpotBounds FalloutFloorBounds();         // the cave
    BossMechanics::SpotBounds ElectrocutionerFloorBounds(); // the pick disc (r 21), not the 30 yd platform arena
    BossMechanics::SpotBounds AlertSystemFloorBounds();     // the hall
    BossMechanics::SpotBounds PummelerFloorBounds();        // the pocket floor
    BossMechanics::SpotBounds ThermapluggFloorBounds();     // the room (the bowl and the arms' roots)

    // The instance script of `o`'s map when it is Gnomeregan's, else nullptr.
    InstanceScript* GnomereganInstance(WorldObject const* o);

    // A slot's state (TO_BE_DECIDED read as NOT_STARTED); NOT_STARTED without an instance.
    uint32 SlotState(InstanceScript const* instance, uint32 slot);

    // Thermaplugg's pull is armed (heroic, the flag, the armed verdict): the hard mode packages read this.
    bool IsHardModeArmed(InstanceScript const* instance);
}

#endif
