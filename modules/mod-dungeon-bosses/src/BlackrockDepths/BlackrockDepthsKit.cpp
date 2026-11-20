/*
 * mod-dungeon-bosses, Blackrock Depths: the Blackrock Depths skeleton's engine glue (BlackrockDepthsKit.h).
 */

#include "BlackrockDepthsKit.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "StringFormat.h"

namespace BlackrockDepthsRework
{
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss)
    {
        DungeonKit::LeashSpec spec;
        spec.bossGraceMs = kLeashBossGraceMs;
        spec.noTargetInsideMs = kLeashNoTargetMs;
        spec.switchToInside = kLeashSwitchToInside;
        return DungeonKit::LeashPreset(std::string(kLogDungeon) + " " + boss + " arena", spec);
    }

    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode)
    {
        if (!boss)
            return;
        DungeonKit::LogMechanic(kLogDungeon, bossKey, "pull", Acore::StringFormat("health={} heroic={} hardmode={}",
            boss->GetMaxHealth(), DungeonKit::IsHeroicMap(boss) ? 1 : 0, hardMode ? 1 : 0));
    }
}
