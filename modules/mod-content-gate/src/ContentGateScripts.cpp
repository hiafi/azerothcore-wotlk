/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

// mod-content-gate hooks: one class per script type (a class deriving several script bases is freed once per base
// at shutdown, docs/bugs-and-fixes.md "mod-progression double free").

#include "Chat.h"
#include "CommandScript.h"
#include "ContentGate.h"
#include "DBCStores.h"
#include "DatabaseScript.h"
#include "Log.h"
#include "MapMgr.h"
#include "Player.h"
#include "PlayerScript.h"
#include "Transport.h"
#include "WorldScript.h"
#include "WorldSession.h"

using namespace Acore::ChatCommands;

namespace
{
    using ContentGate::Continent;
    using ContentGate::Spot;

    char const* const MSG_OUTLAND_CLOSED = "Outland is not open yet. The Dark Portal will open in a later tier.";
    char const* const MSG_NORTHREND_CLOSED = "Northrend is not open yet. The ship turns back to port.";

    bool CanBypass(Player const* player)
    {
        return player->GetSession()->HasPermission(rbac::RBAC_PERM_SKIP_CHECK_DISABLE_MAP);
    }

    uint32 ZoneOfArea(uint32 areaId)
    {
        if (AreaTableEntry const* area = sAreaTableStore.LookupEntry(areaId))
            return area->zone ? area->zone : areaId;
        return 0;
    }

    Continent ClosedContinentAt(uint32 mapId, uint32 zoneId)
    {
        return ContentGate::ClosedContinentAt(mapId, zoneId, sContentGate->IsOutlandOpen(),
            sContentGate->IsNorthrendOpen());
    }

    // The player's homebind when it is on an open continent, else their faction's capital.
    Spot SafeHome(Player const* player)
    {
        if (ClosedContinentAt(player->m_homebindMapId, ZoneOfArea(player->m_homebindAreaId)) == Continent::Allowed)
            return { player->m_homebindMapId, player->m_homebindX, player->m_homebindY, player->m_homebindZ,
                player->GetOrientation() };
        return player->GetTeamId() == TEAM_ALLIANCE ? ContentGate::STORMWIND : ContentGate::ORGRIMMAR;
    }

    void Notify(Player* player, Continent continent)
    {
        ChatHandler(player->GetSession()).SendSysMessage(continent == Continent::Outland ? MSG_OUTLAND_CLOSED :
            MSG_NORTHREND_CLOSED);
    }

    void TeleportToSpot(Player* player, Spot const& spot)
    {
        player->TeleportTo(spot.map, spot.x, spot.y, spot.z, spot.o);
    }
}

class ContentGateWorldScript : public WorldScript
{
public:
    ContentGateWorldScript() : WorldScript("ContentGateWorldScript", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD,
        WORLDHOOK_ON_BEFORE_WORLD_INITIALIZED,
        WORLDHOOK_ON_UPDATE
    }) { }

    void OnAfterConfigLoad(bool reload) override
    {
        sContentGate->LoadConfig(reload);
    }

    void OnBeforeWorldInitialized() override
    {
        sContentGate->FinishBoot();
    }

    void OnUpdate(uint32 diff) override
    {
        sContentGate->Update(diff);
    }
};

class ContentGateDatabaseScript : public DatabaseScript
{
public:
    ContentGateDatabaseScript() : DatabaseScript("ContentGateDatabaseScript", {
        DATABASEHOOK_ON_AFTER_DATABASE_LOAD_CREATURETEMPLATES
    }) { }

    // Runs right after DisableMgr::LoadDisables and before quests, game events and outdoor PvP load, so the boot
    // post-processing sees the module's disables exactly like DB rows.
    void OnAfterDatabaseLoadCreatureTemplates(std::vector<CreatureTemplate*> /*creatureTemplates*/) override
    {
        sContentGate->ApplyAtBoot();
    }
};

class ContentGatePlayerScript : public PlayerScript
{
public:
    ContentGatePlayerScript() : PlayerScript("ContentGatePlayerScript", {
        PLAYERHOOK_ON_BEFORE_TELEPORT,
        PLAYERHOOK_ON_UPDATE_ZONE
    }) { }

    // Teleports into a closed continent: portals, hearthstones, summons, the Dark Portal areatrigger and transport
    // map hops. A refused transport hop drops the passenger at sea (Transport.cpp), so put them back on the dock.
    bool OnPlayerBeforeTeleport(Player* player, uint32 mapId, float x, float y, float z, float /*orientation*/,
        uint32 options, Unit* /*target*/) override
    {
        if (!sContentGate->IsEnabled() || CanBypass(player))
            return true;

        uint32 zoneId = 0;
        if (mapId == ContentGate::MAP_OUTLAND && !sContentGate->IsOutlandOpen())
            zoneId = sMapMgr->GetZoneId(PHASEMASK_NORMAL, mapId, x, y, z);

        Continent const continent = ClosedContinentAt(mapId, zoneId);
        if (continent == Continent::Allowed)
            return true;

        Notify(player, continent);
        if (sContentGate->IsDebug())
            LOG_INFO("module.content_gate", "[content-gate] refused {} teleport to map {} zone {} ({})",
                player->GetName(), mapId, zoneId, continent == Continent::Outland ? "Outland" : "Northrend");

        if ((options & TELE_TO_NOT_LEAVE_TRANSPORT) && player->GetTransport())
        {
            uint32 const transportEntry = player->GetTransport()->GetEntry();
            if (sContentGate->IsDebug())
                LOG_INFO("module.content_gate", "[content-gate] {} returns to the dock of transport {}",
                    player->GetName(), transportEntry);
            // Deferred to the player's own update: TeleportTo is on the stack right now.
            player->m_Events.AddEventAtOffset([player, transportEntry]()
            {
                if (!player->IsInWorld() || player->IsBeingTeleported())
                    return;
                std::optional<Spot> const dock = ContentGate::DockForTransport(transportEntry);
                TeleportToSpot(player, dock ? *dock : SafeHome(player));
            }, 100ms);
        }
        return false;
    }

    // Backstop: anyone standing in a closed continent (login, a path the teleport check missed) is sent back.
    void OnPlayerUpdateZone(Player* player, uint32 newZone, uint32 /*newArea*/) override
    {
        if (!sContentGate->IsEnabled() || CanBypass(player))
            return;
        if (ClosedContinentAt(player->GetMapId(), newZone) == Continent::Allowed)
            return;

        player->m_Events.AddEventAtOffset([player]()
        {
            if (!player->IsInWorld() || player->IsBeingTeleported() || !sContentGate->IsEnabled())
                return;
            Continent const continent = ClosedContinentAt(player->GetMapId(), player->GetZoneId());
            if (continent == Continent::Allowed)
                return;
            Notify(player, continent);
            if (sContentGate->IsDebug())
                LOG_INFO("module.content_gate", "[content-gate] bounced {} out of map {} zone {}", player->GetName(),
                    player->GetMapId(), player->GetZoneId());
            TeleportToSpot(player, continent == Continent::Outland ? ContentGate::DARK_PORTAL_BLASTED_LANDS :
                SafeHome(player));
        }, 1s);
    }
};

class ContentGateCommandScript : public CommandScript
{
public:
    ContentGateCommandScript() : CommandScript("ContentGateCommandScript") { }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable gateCommandTable =
        {
            { "status", HandleStatus, SEC_GAMEMASTER, Console::Yes },
            { "reload", HandleReload, SEC_GAMEMASTER, Console::Yes }
        };
        static ChatCommandTable commandTable =
        {
            { "gate", gateCommandTable }
        };
        return commandTable;
    }

    static bool HandleStatus(ChatHandler* handler)
    {
        sContentGate->PrintStatus(handler);
        return true;
    }

    static bool HandleReload(ChatHandler* handler)
    {
        sContentGate->RequestReapply();
        handler->SendSysMessage("Content gate: bundle tables re-read and the gate re-applied on the next world tick "
            "(conf changes need .reload config). Check .gate status.");
        return true;
    }
};

void AddSC_content_gate()
{
    new ContentGateWorldScript();
    new ContentGateDatabaseScript();
    new ContentGatePlayerScript();
    new ContentGateCommandScript();
}
