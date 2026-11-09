/*
 * mod-dungeon-bosses, Stratholme S8:
 * Balnazzar's hard mode, the Grand Lie.
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S8 owns this file from now on.
 *
 * What the stub does: `.dbtest strat grandlie info` (the flag, its kill slot and the boss's state).
 *
 * TODO(WP-S8):
 * - ST 1920-1999, 2107-2120; handoff section 3.7, section 3.5 row S8.
 * - Wave 2 (the instance refuses DATA_GRAND_LIE while kWave2Bound is false). Section 3.7: the Letter of
 *   Proof (301203, spawned on heroic by Galford's DONE by the Scarlet Archive), the relics (the Standard
 *   301204 on Willey's DONE, the Medallion's light 301205 on Malor's DONE, the blessed crate 301206 with
 *   spawnMask 2; KT-2 RelicDispenser; items 70600-70603), the acts by health, the twins (NoTelegraph real
 *   hits, Decoy() claimed markers), moving swarms 300609, Infernals at 25k, Dread Slumber.
 * - The instance already: stores and saves DATA_GRAND_LIE (heroic, wave 2 bound, Balnazzar neither
 *   fighting nor dead; it stays lit through wipes, section 7 #10), records BOSS_GRAND_LIE DONE on a lit kill
 *   and sets the loot bit on Dathrohan while lit. The relic spawns on Galford's, Malor's and Willey's DONE
 *   are yours to add to the instance (ask the orchestrator: a shared file) with the spots measured in game.
 * - Host-testable logic in GrandLieLogic.h (spell ids in kSpellsGrandLie); `.dbtest strat grandlie <...>`.
 */

#include "Chat.h"
#include "InstanceScript.h"
#include "Player.h"
#include "GrandLieLogic.h"
#include "StratholmeRework.h"
#include "StratholmeTestCommand.h"

using namespace Acore::ChatCommands;
using namespace StratholmeRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        if (!StratTest::RequireStratholme(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        handler->PSendSysMessage("grandlie: flag {}, kill {}, boss {}", instance->GetData(DATA_GRAND_LIE),
            DungeonTest::StateName(instance->GetBossState(BOSS_GRAND_LIE)),
            DungeonTest::StateName(instance->GetBossState(BOSS_BALNAZZAR)));
        return true;
    }

    ChatCommandTable const& GrandLieTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_strat_balnazzar_hard_mode()
{
    StratTest::RegisterBoss("grandlie", GrandLieTestCommands());
}
