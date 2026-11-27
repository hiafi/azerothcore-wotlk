/*
 * mod-dungeon-bosses, Gnomeregan: the Gnomeregan skeleton's engine glue (GnomereganKit.h).
 */

#include "GnomereganKit.h"
#include "Creature.h"
#include "CreatureAIImpl.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "Map.h"
#include "StringFormat.h"
#include <utility>
#include <vector>

namespace GnomereganRework
{
    void NoAssist(Creature* me)
    {
        if (me)
            me->SetAssistanceTimer(0);
    }

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

    BossMechanics::SpotBounds BoundsOf(Arena const& arena)
    {
        BossMechanics::SpotBounds bounds;
        for (ArenaRegion const& region : arena.regions)
        {
            switch (region.kind)
            {
                case ArenaRegion::Kind::Polygon:
                {
                    std::vector<Position> points;
                    points.reserve(region.polygon.size());
                    for (Vec2 const& p : region.polygon)
                        points.emplace_back(p.x, p.y, 0.f);
                    bounds.Polygon(std::move(points), region.zMin, region.zMax);
                    break;
                }
                case ArenaRegion::Kind::Circle:
                    bounds.Circle(Position(region.center.x, region.center.y, 0.f), region.radius, region.zMin,
                        region.zMax);
                    break;
                default:
                    break;      // no Gnomeregan arena is a frame box
            }
        }
        return bounds;
    }

    BossMechanics::SpotBounds TechbotFloorBounds() { return BoundsOf(DishArena()); }
    BossMechanics::SpotBounds FalloutFloorBounds() { return BoundsOf(CaveArena()); }
    BossMechanics::SpotBounds ElectrocutionerFloorBounds() { return BoundsOf(PlatformPickArena()); }
    BossMechanics::SpotBounds AlertSystemFloorBounds() { return BoundsOf(HallArena()); }
    BossMechanics::SpotBounds PummelerFloorBounds() { return BoundsOf(PocketArena()); }
    BossMechanics::SpotBounds ThermapluggFloorBounds() { return BoundsOf(RoomArena()); }

    InstanceScript* GnomereganInstance(WorldObject const* o)
    {
        if (!o || !InstanceHasScript(o, kInstanceScriptName))
            return nullptr;
        return o->GetInstanceScript();
    }

    uint32 SlotState(InstanceScript const* instance, uint32 slot)
    {
        if (!instance || slot >= kBossCount)
            return DungeonKit::State::NotStarted;
        return SettledSlotState(uint32(instance->GetBossState(slot)));
    }

    bool IsHardModeArmed(InstanceScript const* instance)
    {
        if (!instance || !instance->instance)
            return false;
        return HardModeArmed(instance->instance->IsHeroic(), instance->GetData(DATA_HARD_MODE),
            instance->GetData(DATA_HARD_MODE_VERDICT));
    }
}
