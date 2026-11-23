/*
 * mod-dungeon-bosses, Scarlet Monastery: the engine glue of the Scarlet Monastery skeleton (WP-S0; handoff section
 * 3.2). The pure half is ScarletMonasteryRework.h; the shared kit (src/Kit/) is under all of it.
 *
 *   LeashOptions   the arena guard of every Scarlet Monastery boss: the arena leash everywhere, no pull grips; the boss
 *                  never chases a victim off his arena (kLeashSwitchToInside: he turns to the top-threat unit on it;
 *                  nobody there: he holds at the edge), evades when he has been off it for kLeashBossGraceMs, and
 *                  evades when nobody in combat with him has been on it for kLeashNoTargetMs. The Stratholme,
 *                  Blackrock Spire and Blackrock Depths values, through the kit's DungeonKit::LeashPreset (handoff
 *                  section 1 #9: every boss stops at its arena edge and evades if dragged out).
 *   OnBossPull     the pull line of a reworked boss: "sm <boss> pull health=<max> heroic=<0|1> hardmode=<0|1>"
 *                  (section 3.5). Scarlet Monastery is not flex: no count is held.
 *   UseWingPortal  a wing portal's use (section 7 #15 A): the user plus every living group member within 20 yd who is
 *                  out of combat go to the next section's start, through the kit's DungeonKit::PortalTravel (KT-SM,
 *                  section 3.11 #2). The instance spawns and restores the portal objects itself (RefreshPortals).
 *
 * A Scarlet Monastery boss, in short (the S0 stubs already do this):
 *
 *     boss_x_rework(Creature* c) : BossAI(c, BOSS_X), _arena(XArena(), ScarletMonasteryRework::LeashOptions("x")) { }
 *     JustEngagedWith: BossAI::JustEngagedWith(who); if (!me->IsEngaged()) return;
 *                      ScarletMonasteryRework::OnBossPull(me, "x");
 *                      Mechanic::BeginEncounter(me, { bossStateId = BOSS_X }); _arena.Engage(me);
 *     UpdateAI:        if (!UpdateVictim()) return; if (!_arena.Update(me, diff)) return; ...
 *     Reset / EnterEvadeMode / JustDied: _arena.Reset();
 *
 * The instance (instance_scarlet_monastery_rework.cpp) owns the doors, the portals, the Cathedral pair's stages, the
 * Ashbringer guard, the Horseman's private field and the four hard mode flags; a boss reads them with GetData
 * (ScarletMonasteryRework.h SmData) and never opens a door itself.
 */

#ifndef MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_KIT_H
#define MOD_DUNGEON_BOSSES_SCARLET_MONASTERY_KIT_H

#include "ArenaGuard.h"
#include "Define.h"
#include "ScarletMonasteryRework.h"
#include <string>

class Creature;
class GameObject;
class Player;

namespace ScarletMonasteryRework
{
    uint32 constexpr kLeashNoTargetMs = 10000;      // evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long (a charge or a knockback that
                                                    // ends outside does not reset him at once)
    bool constexpr kLeashSwitchToInside = true;     // the Scholomance, Stratholme, BRS and BRD rule

    // The arena guard options of a Scarlet Monastery boss: no grips, never chase off the arena, the boss leash and the
    // no-target leash. `boss` names the log prefix "sm <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);

    // The pull of a reworked boss, from JustEngagedWith once the boss is engaged: logs "sm <boss> pull health=<max>
    // heroic=<0|1> hardmode=<0|1>".
    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode = false);

    // A wing portal's use by `user` (section 7 #15 A): moves the user and every group member within kPortalGroupRange
    // who is alive, free and out of combat to `portal`'s destination (the next section's start); refused while the
    // user is in combat. Returns how many players moved (0 when refused). One log line "sm portal <name> use ...".
    uint32 UseWingPortal(WingPortal const& portal, GameObject* portalObject, Player* user);
}

#endif
