#ifndef _DUNGEON_CHECKPOINT_MGR_H_
#define _DUNGEON_CHECKPOINT_MGR_H_

#include "Position.h"
#include <unordered_map>
#include <unordered_set>
#include <vector>

class Creature;
class Map;

// Static, content-authored checkpoint location for one dungeon map.
// creatureEntry == 0 means "entrance checkpoint" - active as soon as the instance is created,
// before any boss has been killed. Rows sharing a checkpointOrder are alternative spots for the
// same checkpoint (e.g. one per wing entrance); the player respawns at the one nearest their death.
//
// reachRadius > 0 makes the spot "reached only": it is a respawn candidate only once a living member of the
// instance has come within reachRadius yards of it (e.g. the extra Dungeon Finder starts of Blackrock Depths, which
// a group that never went there must not respawn at). 0 = always a candidate, which is how every row behaved before
// the column existed.
struct DungeonCheckpointLocation
{
    uint32 creatureEntry = 0;
    uint8 locationIndex = 0;
    uint8 checkpointOrder = 0;
    float reachRadius = 0.0f;
    WorldLocation loc;

    // Identifies the spot inside its dungeon for the per-instance "reached" set.
    [[nodiscard]] uint32 ReachKey() const { return (uint32(checkpointOrder) << 8) | locationIndex; }
};

// Live, per-instance checkpoint progress.
struct DungeonCheckpointState
{
    uint8 checkpointOrder = 0;
    WorldLocation loc;

    // ReachKey()s of the "reached only" spots a member of this instance has been near. Persisted in
    // dungeon_checkpoint_reached; carried over unchanged when the checkpoint advances.
    std::unordered_set<uint32> reached;
    uint32 reachTimer = 0;
};

// Drives dungeon checkpoint respawn: which boss kills (per dungeon map) advance the checkpoint,
// and where a player resurrects when they release spirit inside a dungeon that has one active.
// Built entirely on existing engine hooks (AllMapScript / UnitScript / PlayerScript) - see
// dungeon_checkpoint_mapscript.cpp, dungeon_checkpoint_unitscript.cpp and
// dungeon_checkpoint_playerscript.cpp for the wiring.
class DungeonCheckpointMgr
{
private:
    DungeonCheckpointMgr() = default;
    ~DungeonCheckpointMgr() = default;

public:
    DungeonCheckpointMgr(DungeonCheckpointMgr const&) = delete;
    DungeonCheckpointMgr& operator=(DungeonCheckpointMgr const&) = delete;

    static DungeonCheckpointMgr* instance();

    // Loads dungeon_checkpoint_location (world DB) into memory. Call once at startup.
    void LoadLocationsFromDB();

    // Re-reads config values. Call at startup and on config reload.
    void ProcessConfig(bool reload);

    [[nodiscard]] bool IsEnabled() const { return _enabled; }

    // Periodic maintenance (orphaned-row cleanup). Call from a WorldScript::OnUpdate.
    void Update(uint32 diff);

    // Deletes persisted checkpoint rows whose instance save no longer exists. `sync` blocks
    // until done - used at startup so a reused instance id can't load a dead instance's row.
    void PruneOrphanedState(bool sync);

    // A player entered `map`. If it's a dungeon with checkpoints configured and this instance
    // has no checkpoint yet, seeds either persisted state (server restart case) or the
    // entrance checkpoint (brand new instance).
    void OnPlayerEnterMap(Map* map);

    // `boss` just died. If it has a configured checkpoint and it's further along than the
    // instance's current one, advances the instance's checkpoint.
    void OnBossDeath(Creature* boss);

    // Map tick for dungeons that have "reached only" spots: about once a second, marks the spots a living instance
    // member is now within reachRadius of. Does nothing for every other map. Runs on the map update thread and reads
    // the shared per-instance cache unguarded: safe with MapUpdate.Threads = 1 (live), see the README.
    void OnMapUpdate(Map* map, uint32 diff);

    // The instance map unloaded - drop the in-memory cache entry. Persisted state is left
    // alone; it belongs to the instance save, not the map's lifetime in memory.
    void OnInstanceDestroyed(uint32 instanceId);

    // The instance save was reset/expired, so its id is free for reuse by a brand new instance -
    // drop both the cached and the persisted checkpoint state.
    void OnInstanceReset(uint32 instanceId);

    // Returns where a player who died at `deathPos` in `map` should respawn: the spot of the
    // instance's active checkpoint nearest to `deathPos`, or nullptr if no checkpoint is set.
    [[nodiscard]] WorldLocation const* GetRespawnLocation(Map const* map, Position const& deathPos) const;

private:
    // Looks up live state for `instanceId`, recovering it from the characters DB (e.g. after a
    // worldserver restart) if it isn't cached yet. Returns nullptr if there's no state at all.
    DungeonCheckpointState* GetOrLoadState(uint32 instanceId, uint32 mapId);

    // Writes new checkpoint state to the cache and persists it (write-through).
    void SaveState(uint32 instanceId, uint32 mapId, DungeonCheckpointState const& state);

    // Records that a member of the instance has been near the spot `key`, and persists it.
    void MarkReached(uint32 instanceId, uint32 mapId, DungeonCheckpointState& state,
        DungeonCheckpointLocation const& location);

    bool _enabled = true;
    uint32 _pruneTimer = 0;

    std::unordered_map<uint32 /*mapId*/, std::vector<DungeonCheckpointLocation>> _locationsByMap;
    std::unordered_map<uint32 /*instanceId*/, DungeonCheckpointState> _stateByInstance;
    std::unordered_set<uint32 /*mapId*/> _reachMaps; // maps with at least one reachRadius > 0 row
};

#define sDungeonCheckpointMgr DungeonCheckpointMgr::instance()

#endif
