/*
 * mod-dungeon-bosses, Deadmines: the shared kit's engine glue (handoff section 3.2 item 3). Boss scripts include this
 * (it pulls in DeadminesRework.h and mod-boss-mechanics' BossMechanics.h).
 *
 *   RefFlat(owner, pct, tank)       a percent of the reference row for a script's own spell (SpellScript damage)
 *   ImpactThenLinger(owner, ...)    an impact Zone plus, on its resolve, a persistent Zone with its own tick damage
 *                                   and the shared "Standing in it hurts" slow rider
 *   CastBar(...)                    the boss casts a no-effect spell for the bar (and says an emote); the registry
 *                                   owns the hit
 *   IsHeroicMap(me)                 the map is the heroic difficulty
 *   ShortenAura(...)                cut a stock aura's duration and keep its id (handoff section 7 #3)
 *   ToPosition / DeckFrame()        the measured frames of DeadminesRework.h as engine types
 */

#ifndef MOD_DUNGEON_BOSSES_DEADMINES_KIT_H
#define MOD_DUNGEON_BOSSES_DEADMINES_KIT_H

#include "BossMechanics.h"
#include "CreatureAIImpl.h"
#include "CreatureScript.h"
#include "DeadminesRework.h"
#include "Duration.h"
#include "GameObjectScript.h"
#include "Position.h"
#include <optional>

class Creature;
class Unit;
class WorldObject;

// The AI runs only inside an instance bound to instance_deadmines_rework (the stock GetDeadminesAI pattern):
//     void AddSC_boss_rhahk_zor_rework() { RegisterDeadminesReworkCreatureAI(boss_rhahk_zor_rework); }
template <class AI, class T>
inline AI* GetDeadminesReworkAI(T* obj)
{
    return GetInstanceAI<AI>(obj, DeadminesRework::kInstanceScriptName);
}

#define RegisterDeadminesReworkCreatureAI(ai_name) RegisterCreatureAIWithFactory(ai_name, GetDeadminesReworkAI)
#define RegisterDeadminesReworkGameObjectAI(ai_name) RegisterGameObjectAIWithFactory(ai_name, GetDeadminesReworkAI)

namespace DeadminesKit
{
    // `pct` percent of the reference health row the registry would pick for `owner` on its current map (its content
    // key: difficulty, the MapLevels pin, else its level): the tank row with `tank`, else the non-tank row. Rounded and
    // clamped like Damage(pct) / TankDamage(pct), so the same percent deals the same number. A null owner or one not
    // in the world returns 0. Call it at cast or hit time, e.g. in a SpellScript:
    //     SetHitDamage(DeadminesKit::RefFlat(GetCaster(), 40.f));
    // Same signature as mod-boss-mechanics' Mechanic::RefFlat (WP-X); boss WPs call only this one.
    uint32 RefFlat(Unit const* owner, float pct, bool tank = false);

    // The map is a heroic difficulty (Map::IsHeroic). False without a map.
    bool IsHeroicMap(WorldObject const* me);

    // The lingering half of ImpactThenLinger.
    struct LingerSpec
    {
        Milliseconds duration{ 10000 };
        Milliseconds tick{ 1000 };
        float pct = 5.f;                                        // per tick, % of reference non-tank health
        uint8 school = 0;                                       // SpellSchools: 0 physical .. 6 arcane
        uint32 spellId = 0;                                     // a dungeon copy of the resolve spell (0 = by school)
        bool slow = true;                                       // rider SPELL_DM_STANDING_IN_IT on every tick hit
        std::optional<BossMechanics::ZoneSpec> shape;           // default: the impact's shape
        std::optional<BossMechanics::Color> color;              // default: the encounter's get-out color
        uint32 tag = 0;
    };

    // The impact half.
    struct ImpactSpec
    {
        BossMechanics::ZoneSpec shape;
        Milliseconds warn{ 2000 };
        float pct = 20.f;                                       // % of reference non-tank health
        float tankPct = -1.f;                                   // >= 0: the tank takes this % of tank health instead
        uint8 school = 0;
        uint32 spellId = 0;
        bool weakened = true;                                   // ruling 15: avoidable single hits apply Weakened
        uint32 tag = 0;
    };

    // Registers the impact Zone and, in its OnResolve, the lingering persistent Zone (one DamageSpec per mechanic, so
    // impact and linger are two registrations; handoff section 3.4 gap 2). The linger's first tick lands one tick
    // after the impact, and it shows its outline only until then (NoFillTimer). The impact's other options can still be
    // chained on the returned ref (it commits at the end of the calling statement); do not replace its OnResolve.
    // Returns an invalid ref when the registry refuses the impact.
    BossMechanics::MechanicRef ImpactThenLinger(Unit* owner, ImpactSpec const& impact, LingerSpec const& linger);

    // Just the lingering zone, now (Fire Bomb on a Blackguard's death, Hot shot segments): the persistent Zone with
    // LingerSpec's numbers on `shape`, its first tick one tick from now.
    BossMechanics::MechanicRef Linger(Unit* owner, BossMechanics::ZoneSpec const& shape, LingerSpec const& linger);

    // The boss casts `spellId` (a no-effect spell with the cast time of the warning: SPELL_DM_CAST_BAR, or the boss's
    // own named copy) on `target` (nullptr: itself) so players see a cast bar, and says `textGroup` (an emote line)
    // when given. Not triggered, so the cast bar shows; the registry mechanic registered beside it owns the hit.
    void CastBar(Creature* caster, uint32 spellId, Unit* target = nullptr, std::optional<uint8> textGroup = {},
        WorldObject const* textTarget = nullptr);

    // Cuts the aura `spellId` that `caster` put on `target` to `duration` (current and max), keeping the stock spell
    // so DD's heroic scaling still applies. Call it right after the cast lands (e.g. from SpellHitTarget). False when
    // the aura is not there.
    bool ShortenAura(Unit* target, uint32 spellId, ObjectGuid caster, Milliseconds duration);

    // A DeadminesRework.h frame point at height `z`.
    Position ToPosition(Vec2 p, float z, float orientation = 0.f);

    // The Juggernaut's deck as a mod-boss-mechanics room frame (DeadminesRework.h kDeck*).
    BossMechanics::RoomFrame DeckFrame();
}

#endif
