#include "ScriptMgr.h"
#include "Creature.h"
#include "dungeon_checkpoint_mgr.h"

class dungeon_checkpoint_unitscript : public UnitScript
{
public:
    dungeon_checkpoint_unitscript() : UnitScript("dungeon_checkpoint_unitscript", true,
        {
            UNITHOOK_ON_UNIT_DEATH
        })
    {
    }

    void OnUnitDeath(Unit* unit, Unit* /*killer*/) override
    {
        if (!sDungeonCheckpointMgr->IsEnabled())
            return;

        Creature* creature = unit->ToCreature();
        if (!creature || !creature->IsDungeonBoss())
            return;

        sDungeonCheckpointMgr->OnBossDeath(creature);
    }
};

void AddSC_dungeon_checkpoint_unitscript()
{
    new dungeon_checkpoint_unitscript();
}
