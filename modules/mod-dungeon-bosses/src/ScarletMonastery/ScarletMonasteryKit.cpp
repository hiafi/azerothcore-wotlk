/*
 * mod-dungeon-bosses, Scarlet Monastery: the Scarlet Monastery skeleton's engine glue (ScarletMonasteryKit.h).
 */

#include "ScarletMonasteryKit.h"
#include "Creature.h"
#include "DungeonKit.h"
#include "DungeonKitWings.h"
#include "GameObject.h"
#include "Player.h"
#include "StringFormat.h"

namespace ScarletMonasteryRework
{
    DungeonKit::ArenaGuardOptions LeashOptions(std::string const& boss)
    {
        DungeonKit::LeashSpec spec;
        spec.bossGraceMs = kLeashBossGraceMs;
        spec.noTargetInsideMs = kLeashNoTargetMs;
        spec.switchToInside = kLeashSwitchToInside;
        return DungeonKit::LeashPreset(std::string(kLogDungeon) + " " + boss + " arena", spec);
    }

    void OnBossPull(Creature* boss, char const* bossKey, bool hardMode)
    {
        if (!boss)
            return;
        DungeonKit::LogMechanic(kLogDungeon, bossKey, "pull", Acore::StringFormat("health={} heroic={} hardmode={}",
            boss->GetMaxHealth(), DungeonKit::IsHeroicMap(boss) ? 1 : 0, hardMode ? 1 : 0));
    }

    // The kit's portal travel (KT-SM, handoff section 3.11 #2; DungeonKitWings.h PortalTravel / JudgeTraveler): the
    // user must be alive, free and out of combat; each other group member on the map goes when alive, free, out of
    // combat and within kPortalGroupRange of the portal; pets travel along; one log line per use.
    uint32 UseWingPortal(WingPortal const& portal, GameObject* portalObject, Player* user)
    {
        FinderSection const* to = SectionByNumber(portal.toSection);
        if (!to || !user || !portalObject)
            return 0;
        DungeonKit::WingPortalSpec spec;
        spec.id = portal.id;
        spec.name = portal.name;
        spec.goEntry = GO_SM_WING_PORTAL;
        spec.destination = Position(to->start.x, to->start.y, to->start.z, to->start.o);
        spec.escortYd = kPortalGroupRange;
        spec.dungeon = kLogDungeon;
        return DungeonKit::PortalTravel(user, portalObject, spec);
    }
}
