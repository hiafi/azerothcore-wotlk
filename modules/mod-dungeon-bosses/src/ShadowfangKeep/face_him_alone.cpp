/*
 * mod-dungeon-bosses, Shadowfang Keep: Arugal's hard mode "Face Him Alone" (WP-S10, heroic only). Build spec: SK
 * 1491-1511 (hard mode), SK 1627-1649 (texts, gossip); handoff section 3.6 row S10.
 *
 * STUB from WP-K (the SFK layer): only `.sfktest hardmode info`. WP-S10 owns this file, FaceHimAloneLogic.h,
 * tests/sfk_face_him_alone_test.cpp, apps/dbc-tools source/npcs/shadowfang_keep/face_him_alone.py and its own SQL rev
 * (spells 206085-206089 only, the last five of Arugal's slice).
 *
 * What the instance already does (instance_shadowfang_keep_rework.cpp): DATA_HARD_MODE (22) is chosen once with
 * SetData(DATA_HARD_MODE, 1) while Arugal is alive, saved, cleared only by an instance reset; while it is lit Arugal
 * carries LOOT_MODE_HARD_MODE_1 (his heroic lootid's group 2, LootMode 2: WP-L); his DONE with it lit sets
 * BOSS_FACE_HIM_ALONE DONE (GetData(DATA_HARD_MODE_KILLED) = 1). `.sfktest instance hardmode <0|1>` sets it by hand.
 *
 * TODO(WP-S10), handoff section 3.6 row S10:
 *   - The lair prisoner's gossip option, heroic (and empowered) only: "Stay behind. We will face Arugal alone."
 *     (npc_sfk_lair_prisoner is S9's, in boss_archmage_arugal_rework.cpp: S10 either asks S9 for a hook there or
 *     exposes a function from this file that the prisoner's gossip calls). On the choice: SetData(DATA_HARD_MODE, 1),
 *     SAY_PRISONER_HARD_MODE (7), the prisoner leaves.
 *   - Arugal with the hard mode: no wards, interrupts required (Void Bolt), the Moonrise burn (SK 1491-1511).
 *   - SQL rev: the prisoners' line 7, the gossip option rows (and their heroic-only condition).
 *   - Tests in tests/sfk_face_him_alone_test.cpp.
 */

#include "Chat.h"
#include "FaceHimAloneLogic.h"
#include "InstanceScript.h"
#include "Player.h"
#include "ShadowfangKeepRework.h"
#include "ShadowfangKeepTestCommand.h"

using namespace Acore::ChatCommands;
using namespace ShadowfangKeepRework;

namespace
{
    bool HandleInfo(ChatHandler* handler)
    {
        if (!SfkTest::RequireShadowfangKeep(handler))
            return false;
        InstanceScript* instance = handler->GetPlayer()->GetInstanceScript();
        if (!instance)
        {
            handler->SendErrorMessage("No instance script on this map.");
            return false;
        }
        handler->PSendSysMessage("Face Him Alone: chosen {}, kill flag {}, heroic map {}",
            instance->GetData(DATA_HARD_MODE), instance->GetData(DATA_HARD_MODE_KILLED),
            handler->GetPlayer()->GetMap()->IsHeroic() ? "yes" : "no");
        return true;
    }

    ChatCommandTable const& FaceHimAloneTestCommands()
    {
        static ChatCommandTable const commands =
        {
            { "info", HandleInfo, SEC_GAMEMASTER, Console::No },
        };
        return commands;
    }
}

void AddSC_sfk_face_him_alone()
{
    SfkTest::RegisterBoss("hardmode", FaceHimAloneTestCommands());
}
