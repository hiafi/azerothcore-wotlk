/*
 * mod-dungeon-bosses, Zul'Farrak: the Zul'Farrak skeleton's engine glue (ZulFarrakKit.h).
 */

#include "ZulFarrakKit.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "InstanceScript.h"
#include "ObjectAccessor.h"
#include "StringFormat.h"
#include <array>
#include <utility>
#include <vector>

namespace ZulFarrak
{
    void NoAssist(Creature* me)
    {
        if (me)
            me->SetAssistanceTimer(0);
    }
}

namespace ZulFarrakRework
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
                    break;      // no Zul'Farrak arena is a frame box
            }
        }
        return bounds;
    }

    BossMechanics::SpotBounds ThekaFloorBounds() { return BoundsOf(CourtyardArena()); }
    BossMechanics::SpotBounds AntusulFloorBounds() { return BoundsOf(DenArena()); }
    BossMechanics::SpotBounds ZumrahFloorBounds() { return BoundsOf(BowlArena()); }
    BossMechanics::SpotBounds BlockFloorBounds() { return BoundsOf(PyramidTopArena()); }
    BossMechanics::SpotBounds StairFloorBounds() { return BoundsOf(StairArena()); }
    BossMechanics::SpotBounds PlazaFloorBounds() { return BoundsOf(PlazaArena()); }
    BossMechanics::SpotBounds UkorzFloorBounds() { return BoundsOf(MesaArena()); }
    BossMechanics::SpotBounds PoolFloorBounds() { return BoundsOf(PoolArena()); }

    Creature* CrewCreature(InstanceScript* instance, uint32 member)
    {
        if (!instance || member >= kCrewCount)
            return nullptr;
        return instance->GetCreature(kGuidCrewBase + member);
    }

    std::optional<uint32> CrewMemberOf(Creature const* creature)
    {
        if (!creature)
            return std::nullopt;
        return CrewIndexOf(creature->GetEntry());
    }

    CrewMode GetCrewMode(InstanceScript const* instance, uint32 member)
    {
        if (!instance || member >= kCrewCount)
            return CrewMode::Caged;
        uint32 const mode = instance->GetData(DATA_CREW_MODE_BASE + member);
        return ValidCrewMode(mode) ? CrewMode(mode) : CrewMode::Caged;
    }

    void SetCrewMode(InstanceScript* instance, uint32 member, CrewMode mode)
    {
        if (instance && member < kCrewCount)
            instance->SetData(DATA_CREW_MODE_BASE + member, uint32(mode));
    }

    namespace
    {
        std::array<PyramidStageFactory, PYRAMID_STAGE_DONE>& StageFactories()
        {
            static std::array<PyramidStageFactory, PYRAMID_STAGE_DONE> factories;
            return factories;
        }
    }

    void RegisterPyramidStage(uint32 stage, PyramidStageFactory factory)
    {
        if (stage >= PYRAMID_STAGE_BLOCK && stage <= PYRAMID_STAGE_ALTAR)
            StageFactories()[stage] = std::move(factory);
    }

    std::unique_ptr<PyramidStageDirector> CreatePyramidStage(uint32 stage, InstanceScript* instance)
    {
        if (stage < PYRAMID_STAGE_BLOCK || stage > PYRAMID_STAGE_ALTAR || !StageFactories()[stage])
            return nullptr;
        return StageFactories()[stage](instance);
    }
}
