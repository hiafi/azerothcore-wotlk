#include "ScriptMgr.h"
#include "Map.h"
#include "Player.h"
#include "dungeon_checkpoint_mgr.h"

class dungeon_checkpoint_mapscript : public AllMapScript
{
public:
    dungeon_checkpoint_mapscript() : AllMapScript("dungeon_checkpoint_mapscript",
        {
            ALLMAPHOOK_ON_PLAYER_ENTER_ALL,
            ALLMAPHOOK_ON_DESTROY_INSTANCE
        })
    {
    }

    void OnPlayerEnterAll(Map* map, Player* /*player*/) override
    {
        if (!sDungeonCheckpointMgr->IsEnabled())
            return;

        sDungeonCheckpointMgr->OnPlayerEnterMap(map);
    }

    void OnDestroyInstance(MapInstanced* /*mapInstanced*/, Map* map) override
    {
        sDungeonCheckpointMgr->OnInstanceDestroyed(map->GetInstanceId());
    }
};

void AddSC_dungeon_checkpoint_mapscript()
{
    new dungeon_checkpoint_mapscript();
}
