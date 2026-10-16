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

/*
 * Hunter rework - ScriptMgr handlers (hunter-rework.SHARED.md §A4 / §A5 / §C2 / §C4). One class per hook kind:
 * every hunter stage extends HunterPlayerScript and HunterPetScript, and S1 adds HunterUnitScript. Every hook
 * returns early on the cheapest check (class, pet type); HunterNoAmmoGrant is the only all-class hook.
 */

#include "HunterMechanics.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "PetScript.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"

class HunterPlayerScript : public PlayerScript
{
public:
    HunterPlayerScript() : PlayerScript("HunterPlayerScript",
        { PLAYERHOOK_ON_LOGOUT, PLAYERHOOK_ON_PLAYER_LEARN_TALENTS, PLAYERHOOK_ON_TALENTS_RESET,
          PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED }) { }

    void OnPlayerLogout(Player* player) override
    {
        if (player && player->getClass() == CLASS_HUNTER)
            Hunter::ClearState(player);
    }

    // S1a (BM A8): the one hunter talent-change path. The rank's passive is applied before this hook
    // (Player::LearnTalent adds the talent first); the pet may not exist, every step null-checks it.
    void OnPlayerLearnTalents(Player* player, uint32 /*talentId*/, uint32 /*talentRank*/, uint32 /*spellid*/) override
    {
        if (player && player->getClass() == CLASS_HUNTER)
            Hunter::OnBeastMasteryTalentsChanged(player);
    }

    // Fires BEFORE the talents are removed (Player.cpp:3902), so the refresh is deferred to the next update; only
    // the GUID is captured and the player is re-resolved (it may have logged out).
    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        if (!player || player->getClass() != CLASS_HUNTER)
            return;

        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid]()
        {
            Player* hunter = ObjectAccessor::FindPlayer(guid);
            if (hunter && hunter->getClass() == CLASS_HUNTER)
                Hunter::OnBeastMasteryTalentsChanged(hunter);
        }, Milliseconds(0));
    }

    // Fires after the spec's auras were swapped.
    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        if (player && player->getClass() == CLASS_HUNTER)
            Hunter::OnBeastMasteryTalentsChanged(player);
    }
};

class HunterPetScript : public PetScript
{
public:
    HunterPetScript() : PetScript("HunterPetScript",
        { PETHOOK_ON_PET_ADD_TO_WORLD, PETHOOK_ON_INIT_STATS_FOR_LEVEL }) { }

    void OnPetAddToWorld(Pet* pet) override
    {
        if (!pet || pet->getPetType() != HUNTER_PET)
            return;

        // Pet::GetOwner reads the stored owner: the charmer/owner GUID is empty until SetMinion, which runs after
        // AddToMap on the taming paths.
        Player* owner = pet->GetOwner();
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return;

        // Filled in order: H0-P (passthrough, kit, pin) -> H0 (Monkey re-apply) -> S2 (Lone Survivor).

        // ---- H0-P: kit swap, passthrough, pin, default bar (PET first). ----
        // The passthrough is refreshed on the pet directly: owner->m_Controlled holds it only after SetMinion, which
        // may not have run yet. On the load path the pet's spells are not loaded yet (the 34902 tick seats the bar),
        // and the taming paths do not reach this hook at all (the owner GUID is empty until SetMinion): the tick covers
        // both within 2 s.
        Hunter::ApplyPetKit(owner, pet);
        Hunter::RefreshPetPassthrough(owner, pet);
        Hunter::PinPetPowers(pet);
        Hunter::SeatDefaultPetBar(pet);

        // ---- H0: Aspect of the Monkey re-apply (SHARED §B6.6), the pet was summoned after the aspect. ----
        Hunter::ReapplyPetMonkeyAura(owner, pet);

        // ---- S2 slot: Lone Survivor refresh (after H0). ----
    }

    void OnInitStatsForLevel(Guardian* guardian, uint8 /*petlevel*/) override
    {
        if (!guardian)
            return;

        // A hunter pet or any hunter-owned guardian (Stampede beasts must reach this hook); H0-P narrows it.
        // Minion::GetOwner uses the owner GUID stored at construction: the charmer/owner GUID is empty before
        // SetMinion, and this hook runs before it (Pet::LoadPetFromDB, InitTamedPet).
        Unit* ownerUnit = guardian->GetOwner();
        Player* owner = ownerUnit ? ownerUnit->ToPlayer() : nullptr;
        if (!owner || owner->getClass() != CLASS_HUNTER)
            return;

        // H0-P: the hunter pet and Stampede beasts only (snakes, charmed beasts and other pets stay out). The hook
        // runs before UpdateAllStats() (Pet.cpp:1434-1436), so the type stats need no update call.
        if (Hunter::GetPassthroughKind(owner, guardian) == Hunter::PassthroughKind::None)
            return;

        Hunter::ApplyPetTypeStats(guardian);
    }
};

// Every class and every player, bots included (Q3): 46699 skips SPELL_FAILED_NO_AMMO server-side. The ammo_type 0
// rows on bows, guns and crossbows are the client half (SHARED §C2).
class HunterNoAmmoGrant : public PlayerScript
{
public:
    HunterNoAmmoGrant() : PlayerScript("HunterNoAmmoGrant",
        { PLAYERHOOK_ON_LOGIN, PLAYERHOOK_ON_LEVEL_CHANGED, PLAYERHOOK_ON_SPELL_CAST }) { }

    void OnPlayerLogin(Player* player) override
    {
        Hunter::EnsureNoAmmoAura(player);
    }

    void OnPlayerLevelChanged(Player* player, uint8 /*oldLevel*/) override
    {
        Hunter::EnsureNoAmmoAura(player);
    }

    // mod-playerbots' Randomize strips auras while a bot is in the world.
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        if (spell->IsTriggered() || spell->GetSpellInfo()->Id == Hunter::SPELL_REQUIRES_NO_AMMO)
            return;

        Hunter::EnsureNoAmmoAura(player);
    }
};

void AddSC_hunter_hooks()
{
    new HunterPlayerScript();
    new HunterPetScript();
    new HunterNoAmmoGrant();
}
