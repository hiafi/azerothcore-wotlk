/*
 * mod-dungeon-bosses, Stratholme: the Stratholme skeleton's engine glue (StratholmeKit.h).
 */

#include "StratholmeKit.h"

namespace StratholmeRework
{
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss)
    {
        DungeonKit::LeashSpec spec;
        spec.bossGraceMs = kLeashBossGraceMs;
        spec.noTargetInsideMs = kLeashNoTargetMs;
        spec.switchToInside = kLeashSwitchToInside;
        return DungeonKit::LeashPreset(std::string(kLogDungeon) + " " + boss + " arena", spec);
    }
}
