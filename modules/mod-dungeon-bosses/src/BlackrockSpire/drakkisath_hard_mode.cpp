/*
 * mod-dungeon-bosses, Blackrock Spire B15:
 * General Drakkisath's hard mode, the General's Army.
 * STUB written by WP-S0 (the Blackrock Spire skeleton); WP-B15 owns this file from now on.
 *
 * What the stub does: `.dbtest brs army info` (the flag, its kill slot and the boss's state).
 *
 * TODO(WP-B15):
 * - SP 3828-3937, 3990-4082; handoff section 3.7, section 3.5 row B15.
 * - Wave 2 (the instance refuses DATA_GENERALS_ARMY while kWave2Bound is false). Section 3.7: the insult
 *   (B12's Nefarius copy, DATA_NEF_INSULTED, saved), the herald 300740 at the throne room's south entrance
 *   (a placeholder: walk it first) with "Let them come" (SetData(DATA_GENERALS_ARMY, 1)), phase 1 (1:30,
 *   squads 300736-300739 every 20 s through the side gates), phase 2 (squads every 45 s, the Champion's
 *   Call and Challenge, the ring 300741, 18,000 at every size; drill t 30 gates the heroic sign-off).
 * - Wipe (DR19): squads despawn, gates close, Guards respawn; the insult stays saved, the herald returns.
 * - The instance already: stores the insult (saved) and the arming (per pull), records BOSS_GENERALS_ARMY
 *   DONE on an armed kill and sets the loot bit while armed.
 * - Host-testable logic in DrakkisathHardModeLogic.h (spell ids in kSpellsGeneralsArmy); `.dbtest brs army <...>`.
 */

#include "BlackrockSpireRework.h"
#include "BlackrockSpireTestCommand.h"
#include "Chat.h"
#include "InstanceScript.h"
#include "Player.h"
#include "DrakkisathHardModeLogic.h"

using namespace Acore::ChatCommands;
using namespace BlackrockSpireRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        if (!BrsTest::RequireBlackrockSpire(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        handler->PSendSysMessage("army: flag {}, kill {}, boss {}", instance->GetData(DATA_GENERALS_ARMY),
            DungeonTest::StateName(instance->GetBossState(BOSS_GENERALS_ARMY)),
            DungeonTest::StateName(instance->GetBossState(BOSS_DRAKKISATH)));
        return true;
    }

    ChatCommandTable const& GeneralsArmyTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_brs_drakkisath_hard_mode()
{
    BrsTest::RegisterBoss("army", GeneralsArmyTestCommands());
}
