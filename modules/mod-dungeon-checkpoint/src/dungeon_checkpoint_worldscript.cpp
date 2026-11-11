#include "ScriptMgr.h"
#include "dungeon_checkpoint_mgr.h"

class dungeon_checkpoint_worldscript : public WorldScript
{
public:
    dungeon_checkpoint_worldscript() : WorldScript("dungeon_checkpoint_worldscript",
        {
            WORLDHOOK_ON_BEFORE_WORLD_INITIALIZED,
            WORLDHOOK_ON_UPDATE,
            WORLDHOOK_ON_AFTER_CONFIG_LOAD
        })
    {
    }

    void OnBeforeWorldInitialized() override
    {
        sDungeonCheckpointMgr->LoadLocationsFromDB();

        // Runs after the engine's own startup instance cleanup (InstanceSaveMgr::LoadInstances),
        // so rows for instances that expired while the server was down are gone before anyone
        // can enter a dungeon and reuse their id.
        sDungeonCheckpointMgr->PruneOrphanedState(true);
    }

    void OnUpdate(uint32 diff) override
    {
        sDungeonCheckpointMgr->Update(diff);
    }

    void OnAfterConfigLoad(bool reload) override
    {
        sDungeonCheckpointMgr->ProcessConfig(reload);
    }
};

void AddSC_dungeon_checkpoint_worldscript()
{
    new dungeon_checkpoint_worldscript();
}
