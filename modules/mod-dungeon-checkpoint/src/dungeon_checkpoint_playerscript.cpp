#include "ScriptMgr.h"
#include "Map.h"
#include "Player.h"
#include "dungeon_checkpoint_mgr.h"

class dungeon_checkpoint_playerscript : public PlayerScript
{
public:
    dungeon_checkpoint_playerscript() : PlayerScript("dungeon_checkpoint_playerscript",
        {
            PLAYERHOOK_CAN_REPOP_AT_GRAVEYARD
        })
    {
    }

    // Runs first inside Player::RepopAtGraveyard(), before the engine's normal graveyard
    // lookup. Returning false here skips that lookup entirely - which is what lets us resurrect
    // the player in place at the checkpoint instead of sending them through the usual
    // release-spirit / ghost-walk / graveyard-teleport flow.
    bool OnPlayerCanRepopAtGraveyard(Player* player) override
    {
        if (!sDungeonCheckpointMgr->IsEnabled())
            return true;

        // RepopAtGraveyard() is also the engine's "eject from instance" path for living players
        // (instance reset, homebind timer after leaving the group, invalid-instance logout). Only
        // intercept a real spirit release, and never one from a player who is being ejected.
        if (!player->HasPlayerFlag(PLAYER_FLAGS_GHOST) || !player->m_InstanceValid)
            return true;

        Map* map = player->GetMap();
        if (!map->IsDungeon())
            return true;

        // The player hasn't moved since BuildPlayerRepop(), so their position is the death spot.
        WorldLocation const* checkpoint = sDungeonCheckpointMgr->GetRespawnLocation(map, *player);
        if (!checkpoint)
            return true; // no checkpoint active yet - normal graveyard behavior

        player->TeleportTo(*checkpoint);
        player->ResurrectPlayer(1.0f);
        player->SpawnCorpseBones();
        player->RemovePlayerFlag(PLAYER_FLAGS_IS_OUT_OF_BOUNDS);

        return false;
    }
};

void AddSC_dungeon_checkpoint_playerscript()
{
    new dungeon_checkpoint_playerscript();
}
