/*
 * mod-dungeon-bosses, the shared dungeon kit: a damage meter over a sliding window (Blackrock Depths WP-KT-D2,
 * handoff section 3.11 #5; Phalanx's Throw Out). The pure rules are DungeonKitPoolLogic.h (DamageTally).
 *
 *   DamageLedger   damage taken by one unit (or a few: feed every unit's DamageTaken into one ledger), credited to the
 *                  player behind each hit (a pet's, a guardian's or a totem's hits count for its player; hits from
 *                  units no player controls are not counted), kept for the last `window` (10 s); Top gives the player
 *                  with the most damage in the window, alive and on the map, skipping an exclusion list (the current
 *                  victim, the last one thrown) or a predicate. A tie goes to the one who reached the total first.
 *
 * Owned by the AI whose DamageTaken feeds it:
 *
 *     DungeonKit::DamageLedger _ledger;       // 10 s
 *     void Reset() override { _ledger.Clear(); ... }
 *     void DamageTaken(Unit* who, uint32& damage, DamageEffectType, SpellSchoolMask) override
 *     {
 *         _ledger.Record(who, damage);        // after any clamp of your own: what the hit really took
 *         ...
 *     }
 *     // Throw Out: never the current victim, never the last one thrown
 *     Player* p = _ledger.Top(me, { me->GetVictim() ? me->GetVictim()->GetGUID() : ObjectGuid::Empty, _lastThrown });
 *     // none (only the excluded dealt damage): the caller's fallback (a random player, or skip the cast)
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LEDGER_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_LEDGER_H

#include "DungeonKitPoolLogic.h"
#include "Duration.h"
#include "ObjectGuid.h"
#include <functional>
#include <initializer_list>
#include <utility>
#include <vector>

class Player;
class Unit;
class WorldObject;

namespace DungeonKit
{
    class DamageLedger
    {
    public:
        explicit DamageLedger(Milliseconds window = Milliseconds(kTallyWindowMs));

        // One hit: `damage` credited to the player behind `attacker` (itself, its owner or charmer). No player: false.
        bool Record(Unit const* attacker, uint32 damage);
        // A hit credited by hand (a player guid).
        void Record(ObjectGuid player, uint32 damage);

        // The player in the window with the most damage, not in `exclude`, alive, on `ref`'s map and, when given,
        // accepted by `eligible`; null when none.
        Player* Top(WorldObject const* ref, std::initializer_list<ObjectGuid> exclude = {},
            std::function<bool(Player*)> const& eligible = {});
        Player* Top(WorldObject const* ref, std::vector<ObjectGuid> const& exclude,
            std::function<bool(Player*)> const& eligible = {});

        // Damage in the window (the player's own plus everything credited to them).
        uint64 Total(ObjectGuid player);
        // Every credited player in the window, most damage first (ties: who reached it first).
        std::vector<std::pair<ObjectGuid, uint64>> Ranking();

        // Reset / JustDied / EnterEvadeMode.
        void Clear() { _tally.Clear(); }
        DamageTally& Tally() { return _tally; }

    private:
        DamageTally _tally;
    };
}

#endif
