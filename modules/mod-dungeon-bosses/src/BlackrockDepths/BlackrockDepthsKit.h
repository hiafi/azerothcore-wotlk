/*
 * mod-dungeon-bosses, Blackrock Depths: the engine glue of the Blackrock Depths skeleton (WP-S0; handoff section 3.2).
 * The pure half is BlackrockDepthsRework.h; the shared kit (src/Kit/) is under all of it.
 *
 *   LeashOptions   the arena guard of every Blackrock Depths boss: the arena leash everywhere, no pull grips; the boss
 *                  never chases a victim off his arena (kLeashSwitchToInside: he turns to the top-threat unit on it;
 *                  nobody there: he holds at the edge), evades when he has been off it for kLeashBossGraceMs, and
 *                  evades when nobody in combat with him has been on it for kLeashNoTargetMs. The Stratholme and
 *                  Blackrock Spire values, through the kit's DungeonKit::LeashPreset (handoff section 1 #9: every boss
 *                  stops at its arena edge and evades if dragged out).
 *   OnBossPull     the pull line of a reworked boss: "brd <boss> pull health=<max> heroic=<0|1> hardmode=<0|1>"
 *                  (section 3.5). Blackrock Depths is not flex (HUB ruling 3): no count is held.
 *
 * A Blackrock Depths boss, in short (the S0 stubs already do this):
 *
 *     boss_x_rework(Creature* c) : BossAI(c, BOSS_X), _arena(XArena(), BlackrockDepthsRework::LeashOptions("x")) { }
 *     JustEngagedWith: BossAI::JustEngagedWith(who); if (!me->IsEngaged()) return;
 *                      BlackrockDepthsRework::OnBossPull(me, "x");
 *                      Mechanic::BeginEncounter(me, { bossStateId = BOSS_X }); _arena.Engage(me);
 *     UpdateAI:        if (!UpdateVictim()) return; if (!_arena.Update(me, diff)) return; ...
 *     Reset / EnterEvadeMode / JustDied: _arena.Reset();
 *
 * The instance (instance_blackrock_depths_rework.cpp) owns the doors, the Ring's rolls and banner flags, the Vault, the
 * bar, the Lyceum, the Tomb, the Iron Hall, the Moira swap and the four hard mode flags; a boss reads them with
 * GetData (BlackrockDepthsRework.h BrdData) and never opens a door itself.
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_KIT_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_DEPTHS_KIT_H

#include "ArenaGuard.h"
#include "BlackrockDepthsRework.h"
#include "Define.h"
#include <string>

class Creature;

namespace BlackrockDepthsRework
{
    uint32 constexpr kLeashNoTargetMs = 10000;      // evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long (a charge or a knockback that
                                                    // ends outside does not reset him at once)
    bool constexpr kLeashSwitchToInside = true;     // the Scholomance, Stratholme and Blackrock Spire rule

    // The arena guard options of a Blackrock Depths boss: no grips, never chase off the arena, the boss leash and the
    // no-target leash. `boss` names the log prefix "brd <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);

    // The pull of a reworked boss, from JustEngagedWith once the boss is engaged: logs "brd <boss> pull health=<max>
    // heroic=<0|1> hardmode=<0|1>".
    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode = false);
}

#endif
