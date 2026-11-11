#include "dungeon_checkpoint_mgr.h"
#include "Config.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "Log.h"
#include "Map.h"
#include "QueryResult.h"
#include "Timer.h"
#include <algorithm>

DungeonCheckpointMgr* DungeonCheckpointMgr::instance()
{
    static DungeonCheckpointMgr instance;
    return &instance;
}

void DungeonCheckpointMgr::ProcessConfig(bool /*reload*/)
{
    _enabled = sConfigMgr->GetOption<bool>("DungeonCheckpoint.Enable", true);
}

void DungeonCheckpointMgr::LoadLocationsFromDB()
{
    uint32 oldMSTime = getMSTime();

    _locationsByMap.clear();

    //                                                 0        1                2                  3            4            5            6
    QueryResult result = WorldDatabase.Query("SELECT map_id, creature_entry, checkpoint_order, position_x, position_y, position_z, orientation FROM dungeon_checkpoint_location");
    if (!result)
    {
        LOG_INFO("server.loading", ">> Loaded 0 dungeon checkpoint locations. Table is empty!");
        return;
    }

    uint32 count = 0;
    do
    {
        Field* fields = result->Fetch();

        uint32 mapId = fields[0].Get<uint32>();

        DungeonCheckpointLocation location;
        location.creatureEntry = fields[1].Get<uint32>();
        location.checkpointOrder = fields[2].Get<uint8>();
        location.loc = WorldLocation(mapId, fields[3].Get<float>(), fields[4].Get<float>(), fields[5].Get<float>(), fields[6].Get<float>());

        _locationsByMap[mapId].push_back(location);
        ++count;
    } while (result->NextRow());

    for (auto& [mapId, locations] : _locationsByMap)
    {
        std::sort(locations.begin(), locations.end(), [](DungeonCheckpointLocation const& a, DungeonCheckpointLocation const& b)
        {
            return a.checkpointOrder < b.checkpointOrder;
        });
    }

    LOG_INFO("server.loading", ">> Loaded {} dungeon checkpoint locations for {} dungeon(s) in {} ms", count, _locationsByMap.size(), GetMSTimeDiffToNow(oldMSTime));
}

void DungeonCheckpointMgr::Update(uint32 diff)
{
    static constexpr uint32 PRUNE_INTERVAL = 10 * 60 * 1000; // 10 minutes

    _pruneTimer += diff;
    if (_pruneTimer < PRUNE_INTERVAL)
        return;

    _pruneTimer = 0;

    // Backstop for OnInstanceReset - catches anything that slipped past it.
    PruneOrphanedState(false);
}

void DungeonCheckpointMgr::PruneOrphanedState(bool sync)
{
    // Persisted checkpoint rows outlive the in-memory cache (they belong to the instance save,
    // not the map's lifetime in memory) - sweep out any left behind by an instance that has
    // since reset/expired.
    static constexpr char const* PRUNE_SQL =
        "DELETE FROM dungeon_checkpoint_instance WHERE instance_id NOT IN (SELECT id FROM instance)";

    if (sync)
        CharacterDatabase.DirectExecute(PRUNE_SQL);
    else
        CharacterDatabase.Execute(PRUNE_SQL);
}

DungeonCheckpointState* DungeonCheckpointMgr::GetOrLoadState(uint32 instanceId, uint32 mapId)
{
    auto itr = _stateByInstance.find(instanceId);
    if (itr != _stateByInstance.end())
        return &itr->second;

    // Recover state persisted before a worldserver restart. Matching map_id too means a stale row
    // from a different dungeon that once held this (reused) instance id is never applied here.
    QueryResult result = CharacterDatabase.Query(
        "SELECT position_x, position_y, position_z, orientation, checkpoint_order FROM dungeon_checkpoint_instance "
        "WHERE instance_id = {} AND map_id = {}",
        instanceId, mapId);
    if (!result)
        return nullptr;

    Field* fields = result->Fetch();

    DungeonCheckpointState state;
    state.loc = WorldLocation(mapId, fields[0].Get<float>(), fields[1].Get<float>(), fields[2].Get<float>(), fields[3].Get<float>());
    state.checkpointOrder = fields[4].Get<uint8>();

    return &_stateByInstance.emplace(instanceId, state).first->second;
}

void DungeonCheckpointMgr::SaveState(uint32 instanceId, uint32 mapId, DungeonCheckpointState const& state)
{
    _stateByInstance[instanceId] = state;

    CharacterDatabase.Execute(
        "REPLACE INTO dungeon_checkpoint_instance (instance_id, map_id, position_x, position_y, position_z, orientation, checkpoint_order) VALUES ({}, {}, {}, {}, {}, {}, {})",
        instanceId, mapId, state.loc.GetPositionX(), state.loc.GetPositionY(), state.loc.GetPositionZ(), state.loc.GetOrientation(), state.checkpointOrder);
}

void DungeonCheckpointMgr::OnPlayerEnterMap(Map* map)
{
    if (!map->IsDungeon())
        return;

    uint32 mapId = map->GetId();

    auto mapItr = _locationsByMap.find(mapId);
    if (mapItr == _locationsByMap.end())
        return; // this dungeon has no checkpoints configured - leave it untouched

    uint32 instanceId = map->GetInstanceId();
    if (GetOrLoadState(instanceId, mapId))
        return; // already have live or persisted state for this instance

    // Brand new instance - seed the entrance checkpoint, if one is configured for this dungeon.
    for (DungeonCheckpointLocation const& location : mapItr->second)
    {
        if (location.creatureEntry != 0)
            continue;

        DungeonCheckpointState state;
        state.checkpointOrder = location.checkpointOrder;
        state.loc = location.loc;
        SaveState(instanceId, mapId, state);
        break;
    }
}

void DungeonCheckpointMgr::OnBossDeath(Creature* boss)
{
    Map* map = boss->GetMap();
    if (!map->IsDungeon())
        return;

    uint32 mapId = map->GetId();

    auto mapItr = _locationsByMap.find(mapId);
    if (mapItr == _locationsByMap.end())
        return;

    DungeonCheckpointLocation const* location = nullptr;
    for (DungeonCheckpointLocation const& candidate : mapItr->second)
    {
        if (candidate.creatureEntry == boss->GetEntry())
        {
            location = &candidate;
            break;
        }
    }

    if (!location)
        return; // this creature isn't a checkpoint boss

    uint32 instanceId = map->GetInstanceId();
    DungeonCheckpointState* state = GetOrLoadState(instanceId, mapId);
    if (state && state->checkpointOrder >= location->checkpointOrder)
        return; // already at or past this checkpoint

    DungeonCheckpointState newState;
    newState.checkpointOrder = location->checkpointOrder;
    newState.loc = location->loc;
    SaveState(instanceId, mapId, newState);
}

void DungeonCheckpointMgr::OnInstanceDestroyed(uint32 instanceId)
{
    _stateByInstance.erase(instanceId);
}

void DungeonCheckpointMgr::OnInstanceReset(uint32 instanceId)
{
    _stateByInstance.erase(instanceId);

    // Synchronous: GetOrLoadState() reads with a blocking query, so a queued async delete could
    // still lose the race against a new instance that immediately reuses this id.
    CharacterDatabase.DirectExecute("DELETE FROM dungeon_checkpoint_instance WHERE instance_id = {}", instanceId);
}

WorldLocation const* DungeonCheckpointMgr::GetRespawnLocation(Map const* map, Position const& deathPos) const
{
    auto itr = _stateByInstance.find(map->GetInstanceId());
    if (itr == _stateByInstance.end())
        return nullptr;

    DungeonCheckpointState const& state = itr->second;

    auto mapItr = _locationsByMap.find(map->GetId());
    if (mapItr == _locationsByMap.end())
        return &state.loc; // locations table changed since this state was saved - use it as-is

    // Several spots can share one checkpoint (e.g. Scarlet Monastery's four wing entrances, all
    // on one map) - pick the one nearest where the player died, so they stay in their own wing.
    WorldLocation const* nearest = nullptr;
    float nearestDistSq = 0.0f;
    for (DungeonCheckpointLocation const& location : mapItr->second)
    {
        if (location.checkpointOrder != state.checkpointOrder)
            continue;

        float distSq = location.loc.GetExactDistSq(deathPos);
        if (!nearest || distSq < nearestDistSq)
        {
            nearest = &location.loc;
            nearestDistSq = distSq;
        }
    }

    return nearest ? nearest : &state.loc;
}
