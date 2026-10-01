/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// Custom: potency-system (docs/potency-system.md) - loads `spell_potency_correction` into
// SpellPotency's in-memory table and validates it once SpellMgr is available. The hook that reads
// this table lives in SpellEffectInfo::CalcValue (SpellInfo.cpp), marked the same way.

#include "Chat.h"
#include "CommandScript.h"
#include "RBAC.h"
#include "ScriptMgr.h"
#include "SpellPotency.h"

using namespace Acore::ChatCommands;

class Custom_SpellPotencyLoader : public WorldScript
{
public:
    Custom_SpellPotencyLoader() : WorldScript("Custom_SpellPotencyLoader") { }

    // Runs before DBC stores / SpellMgr load (World.cpp), so only the raw table load happens here.
    void OnLoadCustomDatabaseTable() override
    {
        SpellPotency::Load();
    }

    // Runs once SpellMgr/DBC stores are available (Main.cpp), so cross-checking loaded rows
    // against real spell data only happens here.
    void OnStartup() override
    {
        SpellPotency::Validate();
    }
};

class Custom_spell_potency_commandscript : public CommandScript
{
public:
    Custom_spell_potency_commandscript() : CommandScript("Custom_spell_potency_commandscript") { }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable reloadCommandTable =
        {
            { "spell_potency_correction", HandleReloadSpellPotencyCorrectionCommand, rbac::RBAC_PERM_COMMAND_RELOAD, Console::Yes },
        };
        static ChatCommandTable commandTable =
        {
            { "reload", reloadCommandTable },
        };
        return commandTable;
    }

    static bool HandleReloadSpellPotencyCorrectionCommand(ChatHandler* handler)
    {
        LOG_INFO("server.loading", "Reloading spell_potency_correction...");
        SpellPotency::Load();
        SpellPotency::Validate();
        handler->SendGlobalGMSysMessage("DB table `spell_potency_correction` (potency-system low-level correction) reloaded.");
        return true;
    }
};

void AddSC_custom_spell_potency()
{
    new Custom_SpellPotencyLoader();
    new Custom_spell_potency_commandscript();
}
