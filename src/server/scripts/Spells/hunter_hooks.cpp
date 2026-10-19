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
 * every hunter stage extends HunterPlayerScript and HunterPetScript, and S1b adds HunterUnitScript. Every hook
 * returns early on the cheapest check (class, pet type); HunterNoAmmoGrant is the only all-class hook.
 */

#include "HunterMechanics.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "PetScript.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "UnitScript.h"

class HunterPlayerScript : public PlayerScript
{
public:
    HunterPlayerScript() : PlayerScript("HunterPlayerScript",
        { PLAYERHOOK_ON_LOGOUT, PLAYERHOOK_ON_PLAYER_LEARN_TALENTS, PLAYERHOOK_ON_TALENTS_RESET,
          PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED, PLAYERHOOK_ON_SPELL_CAST, PLAYERHOOK_ON_PLAYER_RESURRECT }) { }

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

    // S2a (MARKSMANSHIP §4.3, A3): mark stack gain, once per non-triggered cast (Spell.cpp, before the completion
    // CheckCast). Independent of HunterNoAmmoGrant's own cast hook; OnHunterSpellCast does the class check first.
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        Hunter::OnHunterSpellCast(player, spell);
    }

    // S2b (S2a review n-1): Falcon's Haste 201942 is a non-passive buff, so death removes it while a Falcon's Mark may
    // still be up; re-add it at once instead of at the next mark stack change. Player::ResurrectPlayer calls this
    // after setDeathState(Alive), so AddAura accepts the player.
    void OnPlayerResurrect(Player* player, float /*restore_percent*/, bool& /*applySickness*/) override
    {
        if (player && player->getClass() == CLASS_HUNTER)
            Hunter::RefreshFalconHaste(player);
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

        // ---- S2: Lone Survivor refresh (after H0; MARKSMANSHIP §10.4). ----
        // The hunter pet is back: drop 201950 at once. SetMinion runs before AddToMap on the call/load and summon
        // paths, so owner->GetPet() already returns this pet.
        Hunter::RefreshLoneSurvivor(owner);
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

// S1b (SHARED §A5): the one hunter UnitScript. OnUnitDeath runs for every death in the world, so each branch starts
// with its cheapest guard (unit->IsPet() first, inside Hunter::OnPhoenixPlumePetDeath). S2 adds
// UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN and a second, independent death branch (Lone Survivor) to this class.
class HunterUnitScript : public UnitScript
{
public:
    HunterUnitScript() : UnitScript("HunterUnitScript", true,
        { UNITHOOK_ON_UNIT_DEATH, UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN }) { }

    void OnUnitDeath(Unit* unit, Unit* /*killer*/) override
    {
        // ---- S1b: Phoenix's Plume revive (BEAST-MASTERY §4.10). ----
        Hunter::OnPhoenixPlumePetDeath(unit);

        // ---- S2: Lone Survivor refresh on hunter pet death (MARKSMANSHIP §10.4, M-m8). ----
        // Independent of the Phoenix's Plume branch (no order between them). Type checks first: every death in the
        // world reaches this. setDeathState(JustDied) already ran, so the dead pet no longer counts as active. A
        // Phoenix's Plume revive (54114) does not re-add the pet to the world: the 500 ms tick drops 201950 again.
        // Pet::GetOwner reads the stored Player*.
        if (unit && unit->IsPet())
        {
            Pet* pet = unit->ToPet();
            Player* owner = pet->getPetType() == HUNTER_PET ? pet->GetOwner() : nullptr;
            if (owner && owner->getClass() == CLASS_HUNTER)
                Hunter::RefreshLoneSurvivor(owner);
        }
    }

    // ---- S2b: Rapid Killing's execute clause (MARKSMANSHIP §10.4, B8). ----
    // Unit::CalculateSpellDamageTaken, before armor and crit, for every direct spell hit in the world; the body's
    // checks run cheapest first.
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        Hunter::ApplyMarksmanshipTakenMods(target, attacker, damage, spellInfo);
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
    new HunterUnitScript();
    new HunterNoAmmoGrant();
}
