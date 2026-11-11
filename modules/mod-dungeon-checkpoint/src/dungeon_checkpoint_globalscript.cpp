#include "ScriptMgr.h"
#include "dungeon_checkpoint_mgr.h"

class dungeon_checkpoint_globalscript : public GlobalScript
{
public:
    dungeon_checkpoint_globalscript() : GlobalScript("dungeon_checkpoint_globalscript",
        {
            GLOBALHOOK_ON_INSTANCEID_REMOVED
        })
    {
    }

    // The instance save was reset/expired and its id freed. Runs even while the module is
    // disabled, so no stale row is waiting for a reused id once it's re-enabled.
    void OnInstanceIdRemoved(uint32 instanceId) override
    {
        sDungeonCheckpointMgr->OnInstanceReset(instanceId);
    }
};

void AddSC_dungeon_checkpoint_globalscript()
{
    new dungeon_checkpoint_globalscript();
}
