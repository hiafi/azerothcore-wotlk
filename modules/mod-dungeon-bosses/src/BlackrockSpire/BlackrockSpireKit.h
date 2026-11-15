/*
 * mod-dungeon-bosses, Blackrock Spire: the engine glue of the Blackrock Spire skeleton (WP-S0; handoff section 3.2).
 * The pure half is BlackrockSpireRework.h; the shared kit (src/Kit/) is under all of it.
 *
 *   LeashOptions   the arena guard of every Blackrock Spire boss (section 7 #24): the arena leash everywhere, no pull
 *                  grips; the boss never chases a victim off his arena (kLeashSwitchToInside: he turns to the
 *                  top-threat unit on it; nobody there: he holds at the edge), evades when he has been off it for
 *                  kLeashBossGraceMs, and evades when nobody in combat with him has been on it for kLeashNoTargetMs.
 *                  The Stratholme values, through the kit's DungeonKit::LeashPreset.
 *   OnBossPull     the pull of a reworked boss: the flex count held (DungeonKit::Flex::OnPull: health scaled, the
 *                  flex loot bits set) and the "brs <boss> pull players=<n> health=<hp>" line (section 3.5).
 *
 * A Blackrock Spire boss, in short (the S0 stubs already do this):
 *
 *     boss_x_rework(Creature* c) : BossAI(c, BOSS_X), _arena(XArena(), BlackrockSpireRework::LeashOptions("x")) { }
 *     JustEngagedWith: BossAI::JustEngagedWith(who); if (!me->IsEngaged()) return;
 *                      _players = BlackrockSpireRework::OnBossPull(me, "x");
 *                      Mechanic::BeginEncounter(me, { bossStateId = BOSS_X }); _arena.Engage(me);
 *     UpdateAI:        if (!UpdateVictim()) return; if (!_arena.Update(me, diff)) return; ...
 *     Reset / EnterEvadeMode / JustDied: _arena.Reset();
 *
 * The instance (instance_blackrock_spire_rework.cpp) owns the doors, the Dragonspire room check, the altar, the Urok
 * pile, the Solakar event, Rend's respawn, the insult and both hard mode flags; a boss reads them with GetData
 * (BlackrockSpireRework.h BrsData) and never opens a door itself.
 */

#ifndef MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_KIT_H
#define MOD_DUNGEON_BOSSES_BLACKROCK_SPIRE_KIT_H

#include "ArenaGuard.h"
#include "BlackrockSpireRework.h"
#include "Define.h"
#include <string>

class Creature;

namespace BlackrockSpireRework
{
    uint32 constexpr kLeashNoTargetMs = 10000;      // evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long (a charge or a knockback that
                                                    // ends outside does not reset him at once)
    bool constexpr kLeashSwitchToInside = true;     // the Scholomance and Stratholme rule

    // The arena guard options of a Blackrock Spire boss: no grips, never chase off the arena, the boss leash and the
    // no-target leash. `boss` names the log prefix "brs <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);

    // The pull of a reworked boss, from JustEngagedWith once the boss is engaged: holds the flex count
    // (DungeonKit::Flex::OnPull with `hardMode`), logs "brs <boss> pull players=<n> health=<max> heroic=<0|1>" and
    // returns the count (5..10; 5 off a flex map). Call it again when a hard mode lights mid-pull only through
    // DungeonKit::Flex::SetFlexLoot (the count is held).
    uint8 OnBossPull(Creature* boss, char const* bossKey, bool hardMode = false);
}

#endif
