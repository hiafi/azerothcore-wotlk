/*
 * mod-dungeon-bosses, the shared dungeon kit: the flex wrapper over mod-dungeon-difficulties (DungeonKitFlex.h,
 * WP-KT-B1). mod-dungeon-bosses.cmake refuses to configure without mod-dungeon-difficulties' FlexScale.h.
 */

#include "DungeonKitFlex.h"
#include "Creature.h"
#include "FlexScale.h"
#include "SharedDefines.h"

static_assert(DungeonKit::Flex::kLootModeFlex == LOOT_MODE_HARD_MODE_2, "the flex copy's LootMode is 4");
static_assert(DungeonKit::Flex::kLootModeFlexHardMode == LOOT_MODE_HARD_MODE_3, "the hard mode flex copy's is 8");
static_assert((DungeonKit::Flex::kLootModeFlexMask & LOOT_MODE_HARD_MODE_1) == 0, "never the hard mode list's bit");

namespace DungeonKit::Flex
{
    bool IsFlexMap(WorldObject const* obj)
    {
        return obj && obj->FindMap() && DungeonDifficulties::Flex::IsFlexMap(obj->FindMap());
    }

    uint8 Count(Creature* me)
    {
        if (!me)
            return kMinPlayers;
        return DungeonDifficulties::Flex::PullCount(me);
    }

    uint8 Held(Creature const* me)
    {
        return me ? DungeonDifficulties::Flex::HeldCount(me) : 0;
    }

    uint8 Targets(Creature* me, uint8 a, uint8 b)
    {
        return TargetCount(Count(me), a, b);
    }

    void SetHealth(Creature* me, uint32 base, bool full)
    {
        if (!me || !base)
            return;
        DungeonDifficulties::Flex::SetScaledMaxHealth(me, base);
        if (full)
            me->SetFullHealth();
    }

    void SetFlexLoot(Creature* boss, uint8 count, bool hardMode)
    {
        if (!boss)
            return;
        boss->RemoveLootMode(kLootModeFlexMask);
        if (uint16 const bits = LootBits(count, hardMode))
            boss->AddLootMode(bits);
    }

    uint8 OnPull(Creature* boss, bool hardMode)
    {
        uint8 const n = Count(boss);
        SetFlexLoot(boss, n, hardMode);
        return n;
    }
}
