/*
 * mod-dungeon-bosses, Deadmines: the shared kit's engine glue (handoff section 3.2 item 3). Boss scripts include this
 * (it pulls in DeadminesRework.h, the shared dungeon kit's DungeonKit.h and mod-boss-mechanics' BossMechanics.h).
 *
 * Since WP-K0 the helpers are the shared dungeon kit's (src/Kit/DungeonKit.h), unchanged: DeadminesKit names them
 * through a using-directive, so the Pilot's calls compile to the generic ones.
 *
 *   RefFlat(owner, pct, tank)       a percent of the reference row for a script's own spell (SpellScript damage)
 *   ImpactThenLinger(owner, ...)    an impact Zone plus, on its resolve, a persistent Zone with its own tick damage
 *                                   and the shared "Standing in it hurts" slow rider (205201)
 *   CastBar(...)                    the boss casts a no-effect spell for the bar (and says an emote); the registry
 *                                   owns the hit
 *   IsHeroicMap(me)                 the map is the heroic difficulty
 *   ShortenAura(...)                cut a stock aura's duration and keep its id (handoff section 7 #3)
 *   ToPosition / DeckFrame()        the measured frames of DeadminesRework.h as engine types
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_KIT_H
#define MOD_DUNGEON_BOSSES_DEADMINES_KIT_H

#include "BossMechanics.h"
#include "DeadminesKitMath.h"
#include "DeadminesRework.h"
#include "DungeonKit.h"

// The AI runs only inside an instance bound to instance_deadmines_rework (the stock GetDeadminesAI pattern):
//     void AddSC_boss_rhahk_zor_rework() { RegisterDeadminesReworkCreatureAI(boss_rhahk_zor_rework); }
template <class AI, class T>
inline AI* GetDeadminesReworkAI(T* obj)
{
    return DungeonKit::GetReworkAI<DeadminesRework::kInstanceScriptName, AI, T>(obj);
}

#define RegisterDeadminesReworkCreatureAI(ai_name) \
    RegisterDungeonReworkCreatureAI(ai_name, DeadminesRework::kInstanceScriptName)
#define RegisterDeadminesReworkGameObjectAI(ai_name) \
    RegisterDungeonReworkGameObjectAI(ai_name, DeadminesRework::kInstanceScriptName)

namespace DeadminesKit
{
    using namespace DungeonKit;

    // The Juggernaut's deck as a mod-boss-mechanics room frame (DeadminesRework.h kDeck*).
    BossMechanics::RoomFrame DeckFrame();
}

#endif
