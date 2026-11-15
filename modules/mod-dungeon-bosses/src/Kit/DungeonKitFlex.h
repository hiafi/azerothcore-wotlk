/*
 * mod-dungeon-bosses, the shared dungeon kit (Blackrock Spire WP-KT-B1, handoff section 3.11 #1-#2): the thin wrapper
 * over mod-dungeon-difficulties' flex scaler (DD `src/FlexScale.h`, namespace DungeonDifficulties::Flex). DD owns the
 * count, the hold and the health; boss scripts call this wrapper. The pure rules (TargetCount, HealthAt, LootRolls,
 * TankSwapOn, LootBits) are DungeonKitFlexRules.h, included here.
 *
 * In a boss (the whole flex contract of a reworked boss):
 *
 *     void JustEngagedWith(Unit* who) override
 *     {
 *         BossAI::JustEngagedWith(who);
 *         _n = DungeonKit::Flex::OnPull(me, _hardMode);    // holds the count, scales health, sets the flex loot bits
 *         ...
 *     }
 *     uint8 const targets = DungeonKit::Flex::TargetCount(_n, 1, 2);
 *     if (DungeonKit::Flex::TankSwapOn(_n)) { ... the taunt swap entry ... }
 *
 * Timing (DD STAGE-FLEX report section 0): JustEngagedWith runs before DD's OnUnitEnterCombat hook, and PullCount holds
 * at the first caller, so a boss's count is held first and the hook reads the same number. The loot is filled before
 * JustDied, so the flex loot bits are set at the pull (OnPull / SetFlexLoot), never in JustDied. Kit adds summoned
 * through SummonWave take the encounter's count at their own pull (DD's summoner rule); their `health` goes through
 * SetHealth on a flex map, so the ladder applies to it.
 *
 * Off a flex map (every dungeon but those in DungeonDifficulties.Flex.Maps), Count is 5, SetHealth sets the base
 * unscaled and SetFlexLoot clears the flex bits: one code path for every dungeon.
 */

#ifndef MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLEX_H
#define MOD_DUNGEON_BOSSES_KIT_DUNGEON_KIT_FLEX_H

#include "Define.h"
#include "DungeonKitFlexRules.h"

class Creature;
class WorldObject;

namespace DungeonKit::Flex
{
    // `obj`'s map is a flex map (listed in DungeonDifficulties.Flex.Maps, Flex.Enable on). False without a map.
    bool IsFlexMap(WorldObject const* obj);

    // The count held for `me`'s fight: holds it now when `me` is engaged and not yet held (DD PullCount; health is
    // scaled at the same time). Call it from JustEngagedWith or later; on a unit that is not engaged it is a preview
    // that holds nothing. Off a flex map: 5. Null: 5.
    uint8 Count(Creature* me);

    // The held count without holding: 0 when not held (still valid in JustDied). The pure rules read 0 as 5.
    uint8 Held(Creature const* me);

    // TargetCount(Count(me), a, b): the mechanic's target count for `me`'s fight.
    uint8 Targets(Creature* me, uint8 a, uint8 b);

    // Script-set health (hard modes, a late arrival, Gizrul, Solakar, squads): `base` is the 5-player value. Held: max
    // health becomes base x ladder now; not held: base, and the next pull scales it; off a flex map: base. Keeps the
    // health percent: with `full`, the unit is set to full health after it. Use it instead of SetMaxHealth /
    // SetCreateHealth on a flex map, or the next pull scales from the wrong base.
    void SetHealth(Creature* me, uint32 base, bool full = false);

    // The flex loot bits on `boss` for a kill at `count` players: clears LootMode 4 and 8, then adds 4 (and 8 with
    // `hardMode`) when the kill rolls twice (LootRolls == 2). Call it at the pull, right after Count, and again when
    // the hard mode bit changes during the fight (the loot is filled before JustDied). The hard mode list's own bit
    // stays SetHardModeLoot's.
    void SetFlexLoot(Creature* boss, uint8 count, bool hardMode = false);

    // The pull in one call: Count(boss), then SetFlexLoot(boss, count, hardMode). Returns the count.
    uint8 OnPull(Creature* boss, bool hardMode = false);
}

#endif
