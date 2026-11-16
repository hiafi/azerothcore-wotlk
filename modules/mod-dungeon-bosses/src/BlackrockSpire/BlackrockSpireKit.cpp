/*
 * mod-dungeon-bosses, Blackrock Spire: the Blackrock Spire skeleton's engine glue (BlackrockSpireKit.h).
 */

#include "BlackrockSpireKit.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitFlex.h"
#include "StringFormat.h"

namespace BlackrockSpireRework
{
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss)
    {
        DungeonKit::LeashSpec spec;
        spec.bossGraceMs = kLeashBossGraceMs;
        spec.noTargetInsideMs = kLeashNoTargetMs;
        spec.switchToInside = kLeashSwitchToInside;
        return DungeonKit::LeashPreset(std::string(kLogDungeon) + " " + boss + " arena", spec);
    }

    uint8 OnBossPull(Creature* boss, char const* bossKey, bool hardMode)
    {
        if (!boss)
            return DungeonKit::Flex::kMinPlayers;
        uint8 const players = DungeonKit::Flex::OnPull(boss, hardMode);
        DungeonKit::LogMechanic(kLogDungeon, bossKey, "pull", Acore::StringFormat("players={} health={} heroic={}",
            players, boss->GetMaxHealth(), DungeonKit::IsHeroicMap(boss) ? 1 : 0));
        return players;
    }
}
