/*
 * mod-dungeon-bosses, Stratholme: the engine glue of the Stratholme skeleton (WP-S0; handoff section 3.2). The pure
 * half is StratholmeRework.h; the shared kit (src/Kit/) is under all of it.
 *
 *   LeashOptions       the arena guard of every Stratholme boss (user ruling on section 7 #16): no grips; the boss
 *                      never chases a victim off his arena (kLeashSwitchToInside: he turns to the top-threat unit on
 *                      it; nobody there: he holds at the edge), evades when he has been off it for kLeashBossGraceMs,
 *                      and evades when nobody in combat with him has been on it for kLeashNoTargetMs. The Scholomance
 *                      LeashOptions' values, through KT-1's DungeonKit::LeashPreset.
 *                      The Unforgiven and Galford add the pull grip on top (S1 / S6, with their lethal walls).
 *
 * A Stratholme boss, in short (the S0 stubs already do this):
 *
 *     boss_x_rework(Creature* c) : BossAI(c, BOSS_X), _arena(XArena(), StratholmeRework::LeashOptions("x")) { }
 *     JustEngagedWith: BossAI::JustEngagedWith(who); Mechanic::BeginEncounter(me, { bossStateId = BOSS_X });
 *                      _arena.Engage(me);
 *     UpdateAI:        if (!UpdateVictim()) return; if (!_arena.Update(me, diff)) return; ...
 *     Reset / EnterEvadeMode / JustDied: _arena.Reset();
 *
 * The instance (instance_stratholme_rework.cpp) owns the doors, the ziggurats, the slaughter event, the Baron Run and
 * both hard mode flags; a boss reads them with GetData (StratholmeRework.h StratholmeData) and never opens a door
 * itself (Barthilas's portcullises are door data on his boss state; the Baron's door follows BOSS_BARON).
 */

#ifndef MOD_DUNGEON_BOSSES_STRATHOLME_KIT_H
#define MOD_DUNGEON_BOSSES_STRATHOLME_KIT_H

#include "ArenaGuard.h"
#include "Define.h"
#include "StratholmeRework.h"
#include <string>

namespace StratholmeRework
{
    uint32 constexpr kLeashNoTargetMs = 10000;      // evade after 10 s with no target inside
    uint32 constexpr kLeashBossGraceMs = 2000;      // the boss himself off it this long (a charge or a knockback that
                                                    // ends outside does not reset him at once)
    // The Scholomance rule (F-A, R-A Q1): while his victim stands off the arena the boss turns to the highest-threat
    // unit on it (false: he holds at the edge, swinging at nothing, until the victim comes back or the no-target
    // leash).
    bool constexpr kLeashSwitchToInside = true;

    // The arena guard options of a Stratholme boss: no grips (no pull grip, no grip back), never chase off the arena,
    // the boss leash and the no-target leash. `boss` names the log prefix "strat <boss> arena".
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss);
}

#endif
