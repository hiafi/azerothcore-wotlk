/*
 * mod-dungeon-bosses, Stratholme S15:
 * Baron Rivendare's hard mode, the Ultimatum.
 * STUB written by WP-S0 (the Stratholme skeleton); WP-S15 owns this file from now on.
 *
 * What the stub does: `.dbtest strat ultimatum info` (the flag, its kill slot and the boss's state).
 *
 * TODO(WP-S15):
 * - ST 3709-3747, 3868-3871; handoff section 3.7, section 3.5 row S15.
 * - Section 3.7: the opt-in (Ysida's gossip menu 7091 gains an option on heroic, conditions type 49 / 1 /
 *   13; her SmartAI select row sets DATA_ULTIMATUM = 1 through SetData(20, 1); the instance refuses it while
 *   he fights, without the clock, or off heroic), HM1 Executions (the 2 yd line soak, Condemned in this
 *   slice, never 205669), HM2 Condemned, HM3 Deathcharger (the lane on X2's drop spot, rot stalkers 300588
 *   every 5 yd, FloorPath), HM4 the long rot that heals, Ysida, Risen 300589 (40k) and the Price of Defiance
 *   (+200%). Retries (ruling 60): a wipe keeps the flag while the clock runs; Risen despawns, Ysida respawns
 *   in her cage at full health, piles, stalkers and skeletons despawn, Condemned is removed.
 * - The instance already: stores and saves DATA_ULTIMATUM, refuses it while he fights, clears it at the
 *   execution when the clock runs out and on his death, records BOSS_ULTIMATUM DONE on a lit kill, sets the
 *   loot bit (DungeonKit::SetHardModeLoot) while lit, and opens the exit gate on his death when Ysida is
 *   dead. The fight hooks live in S14's BaronFight.h.
 * - Data: Ysida, Risen 300589 and its spells (DT baron_hard_mode.py), the gossip option, conditions,
 *   Ysida's SmartAI select row (SmartAI rows are rewritten as a full block), texts 11-14 and Ysida 2.
 * - Host-testable logic in BaronHardModeLogic.h (spell ids in kSpellsUltimatum); `.dbtest strat ultimatum <...>`.
 */

#include "Chat.h"
#include "InstanceScript.h"
#include "Player.h"
#include "BaronHardModeLogic.h"
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
        handler->PSendSysMessage("ultimatum: flag {}, kill {}, boss {}", instance->GetData(DATA_ULTIMATUM),
            DungeonTest::StateName(instance->GetBossState(BOSS_ULTIMATUM)),
            DungeonTest::StateName(instance->GetBossState(BOSS_BARON)));
        return true;
    }

    ChatCommandTable const& UltimatumTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_strat_baron_hard_mode()
{
    StratTest::RegisterBoss("ultimatum", UltimatumTestCommands());
}
