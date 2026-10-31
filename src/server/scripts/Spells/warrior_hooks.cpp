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
 * Warrior rework - ScriptMgr handlers (warrior-rework S1, S2, S3). Bodies: WarriorMechanics.
 * One WarriorPlayerScript and one WarriorUnitScript for every spec: S2 / S3 append their hooks here, never fork them.
 */

#include "Item.h"
#include "Player.h"
#include "PlayerScript.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "UnitScript.h"
#include "WarriorMechanics.h"
#include <array>

namespace
{
    // S2 (D17): Weapon Specialization's talent ranks (stock ids, kept as DUMMY markers) and the nine hidden per-weapon
    // passives (axe/polearm, mace, sword x rank 1-3) that Warrior::UpdateWeaponSpecialization swaps.
    constexpr std::array<uint32, 3> WeaponSpecializationRanks = { WarriorData::SPELL_WEAPON_SPECIALIZATION,
        WarriorData::SPELL_WEAPON_SPECIALIZATION_12812, WarriorData::SPELL_WEAPON_SPECIALIZATION_12813 };
    constexpr std::array<uint32, 9> WeaponSpecializationPassives = {
        WarriorData::SPELL_WEAPON_SPECIALIZATION_AXE_R1, WarriorData::SPELL_WEAPON_SPECIALIZATION_MACE_R1,
        WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R1, WarriorData::SPELL_WEAPON_SPECIALIZATION_AXE_R2,
        WarriorData::SPELL_WEAPON_SPECIALIZATION_MACE_R2, WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R2,
        WarriorData::SPELL_WEAPON_SPECIALIZATION_AXE_R3, WarriorData::SPELL_WEAPON_SPECIALIZATION_MACE_R3,
        WarriorData::SPELL_WEAPON_SPECIALIZATION_SWORD_R3 };

    bool IsWeaponSpecializationRank(uint32 spellId)
    {
        for (uint32 rankId : WeaponSpecializationRanks)
            if (spellId == rankId)
                return true;

        return false;
    }

    // Tests the spell, not the class: a Classless character can learn the talent too. A player who no longer knows a
    // rank but still carries a passive (reset, spec swap, unlearn) also counts, so the swap can remove it.
    bool HasWeaponSpecializationState(Player const* player)
    {
        for (uint32 rankId : WeaponSpecializationRanks)
            if (player->HasTalent(rankId, player->GetActiveSpec()) || player->HasSpell(rankId))
                return true;

        for (uint32 passiveId : WeaponSpecializationPassives)
            if (player->HasAura(passiveId))
                return true;

        return false;
    }

    // ---- Custom: warrior-rework S3 (D3, D31, D32): Titan's Grip's penalty aura, Two-Handed Weapon Mastery's gate
    // and the Enrage meter's reset. Tests the spell / aura state, not the class (a Classless character can hold the
    // talents), and so that a swap that took the talent away still reaches the update that removes the penalty. ----
    bool IsTitansGripOrMasterySpell(uint32 spellId)
    {
        return spellId == WarriorData::SPELL_TITAN_S_GRIP || spellId == WarriorData::SPELL_TWO_HANDED_WEAPON_MASTERY ||
            spellId == WarriorData::SPELL_TWO_HANDED_WEAPON_MASTERY_204525;
    }

    bool HasTitansGripOrMasteryState(Player const* player)
    {
        return player->CanTitanGrip() || player->HasAura(WarriorData::SPELL_TITANS_GRIP_PENALTY) ||
            player->HasAura(WarriorData::SPELL_TWO_HANDED_WEAPON_MASTERY) ||
            player->HasAura(WarriorData::SPELL_TWO_HANDED_WEAPON_MASTERY_204525);
    }

    // The meter lives in the player's CustomData with the 204635 display aura only while it holds stacks, so a
    // warrior always counts; anyone else only while the display aura is up.
    bool MayHoldEnrageMeter(Player const* player)
    {
        return player->getClass() == CLASS_WARRIOR || player->HasAura(WarriorData::SPELL_ENRAGE_METER);
    }

    // One deferred pass for everything the S2 / S3 hooks keep in sync. Every update is idempotent, so a burst of
    // calls in one update is harmless, and none of them runs inside a calc hook (the slot hook fires from
    // SetVisibleItemSlot, DestroyItem calls it before clearing m_items[slot], and a talent reset removes its auras
    // after the hook). The event list dies with the Player, so capturing it is safe.
    void ScheduleWarriorUpdates(Player* player, bool weaponSpecialization, bool titansGripAndMastery,
        bool resetEnrageMeter)
    {
        player->m_Events.AddEventAtOffset([player, weaponSpecialization, titansGripAndMastery, resetEnrageMeter]()
        {
            if (weaponSpecialization)
                Warrior::UpdateWeaponSpecialization(player);

            if (titansGripAndMastery)
            {
                Warrior::UpdateTitansGripPenalty(player);
                Warrior::UpdateTwoHandedWeaponMastery(player);
            }

            if (resetEnrageMeter)
                Warrior::ResetEnrageMeter(player);
        }, 1ms);
    }
}

class WarriorPlayerScript : public PlayerScript
{
public:
    WarriorPlayerScript() : PlayerScript("WarriorPlayerScript",
        { PLAYERHOOK_ON_SPELL_CAST, PLAYERHOOK_ON_LOGIN, PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT,
          PLAYERHOOK_ON_PLAYER_LEARN_TALENTS, PLAYERHOOK_ON_TALENTS_RESET, PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED,
          PLAYERHOOK_ON_LEARN_SPELL, PLAYERHOOK_ON_FORGOT_SPELL }) { }

    // S1: the one cast-start dispatcher (Warrior::OnSpellCast, before effects, resources not yet spent). Its branches:
    // Sword and Board's roll (any rage-cost cast), Improved Bloodrage (Bloodrage), the Revenge cast stamp for Incite
    // and Empowered Revenge's shield (Revenge), Last Stand's cast record for the Unrelenting floor (Last Stand).
    // S2 / S3 append branches to it in WarriorMechanics, never add a second dispatcher here.
    // Bloodrage and Last Stand are the two non-Warrior-family spells the dispatcher needs (a Classless character
    // using warrior abilities is covered by the family check too). The hook runs for every cast by every player,
    // so every reject comes before any call out.
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        if (!player || !spell || spell->IsTriggered())
            return;

        // Custom: warrior-rework S3 (D3, R1): any non-triggered rage-cost cast of any family also reaches the
        // dispatcher, where the Enrage meter branch runs first and every other branch keeps its own family filter.
        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (spellInfo->SpellFamilyName != SPELLFAMILY_WARRIOR && spellInfo->Id != WarriorData::SPELL_BLOODRAGE &&
            spellInfo->Id != WarriorData::SPELL_LAST_STAND &&
            (spellInfo->PowerType != POWER_RAGE || spell->GetPowerCost() <= 0))
            return;

        Warrior::OnSpellCast(player, spell);
    }

    // ---- S2 (D17, Q3): Weapon Specialization keeps exactly one hidden passive matching the main hand. The hooks
    // below are the only callers of Warrior::UpdateWeaponSpecialization (login, main-hand change, talent change). ----

    // The inventory load (VisualizeItem while not in the world) is skipped by the slot hook; this pass covers it.
    void OnPlayerLogin(Player* player) override
    {
        if (!player)
            return;

        // Custom: warrior-rework S3 (D31, D32): the same pass for Titan's Grip's penalty and the mastery gate.
        if (HasTitansGripOrMasteryState(player))
            ScheduleWarriorUpdates(player, false, true, false);

        if (!HasWeaponSpecializationState(player))
            return;

        Warrior::UpdateWeaponSpecialization(player);
    }

    // SetVisibleItemSlot runs on every equip, swap, unequip, destroy and enchant of the slot. DestroyItem calls it
    // before clearing m_items[slot], so the swap waits one update to read the new main hand.
    void OnPlayerAfterSetVisibleItemSlot(Player* player, uint8 slot, Item* /*item*/) override
    {
        if ((slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND) || !player || !player->IsInWorld())
            return;

        // Custom: warrior-rework S3 (D31, D32): the off hand also drives Titan's Grip's penalty (an off-hand
        // two-hander) and the mastery gate (any off-hand weapon); Weapon Specialization stays main-hand driven. One
        // deferred event covers both.
        bool const weaponSpecialization = slot == EQUIPMENT_SLOT_MAINHAND && HasWeaponSpecializationState(player);
        bool const titansGripAndMastery = HasTitansGripOrMasteryState(player);
        if (weaponSpecialization || titansGripAndMastery)
            ScheduleWarriorUpdates(player, weaponSpecialization, titansGripAndMastery, false);
    }

    // Player::LearnTalent: the new rank is in m_talents and its aura applied (the old rank's removed) by now.
    void OnPlayerLearnTalents(Player* player, uint32 /*talentId*/, uint32 /*talentRank*/, uint32 spellId) override
    {
        if (!player)
            return;

        // Custom: warrior-rework S3 (D31, D32): Titan's Grip and the mastery gate (deferred: the talent's cast
        // that sets CanTitanGrip may still be on its way).
        if (IsTitansGripOrMasterySpell(spellId))
            ScheduleWarriorUpdates(player, false, true, false);

        if (!IsWeaponSpecializationRank(spellId))
            return;

        Warrior::UpdateWeaponSpecialization(player);
    }

    // Player::resetTalents calls this before it removes anything, so the swap waits one update.
    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        if (!player)
            return;

        // Custom: warrior-rework S3 (D3, D31, D32): also clears the Enrage meter (state tested now, the removal
        // happens after the hook).
        ScheduleWarriorUpdates(player, HasWeaponSpecializationState(player), HasTitansGripOrMasteryState(player),
            MayHoldEnrageMeter(player));
    }

    // Dual-spec swap: the new spec's talents are active by now.
    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        if (!player)
            return;

        // Custom: warrior-rework S3 (D3, D31, D32): the swap drops the Enrage meter too; the old spec's penalty /
        // gate state is checked by aura, so it still reaches the update that removes it.
        ScheduleWarriorUpdates(player, false, HasTitansGripOrMasteryState(player), MayHoldEnrageMeter(player));

        if (!HasWeaponSpecializationState(player))
            return;

        Warrior::UpdateWeaponSpecialization(player);
    }

    // A rank learnt or removed as a spell (Classless, GM .learn / .unlearn) rather than through the talent tree.
    void OnPlayerLearnSpell(Player* player, uint32 spellId) override
    {
        if (player)
            ScheduleSpellStateUpdates(player, spellId);
    }

    void OnPlayerForgotSpell(Player* player, uint32 spellId) override
    {
        if (player)
            ScheduleSpellStateUpdates(player, spellId);
    }

private:
    // The learn / forget filter: Weapon Specialization's ranks (S2) and, from S3, Titan's Grip and Two-Handed Weapon
    // Mastery. Runs for every spell every player learns or forgets, so it is two cheap id compares.
    static void ScheduleSpellStateUpdates(Player* player, uint32 spellId)
    {
        bool const weaponSpecialization = IsWeaponSpecializationRank(spellId);
        bool const titansGripAndMastery = IsTitansGripOrMasterySpell(spellId);
        if (weaponSpecialization || titansGripAndMastery)
            ScheduleWarriorUpdates(player, weaponSpecialization, titansGripAndMastery, false);
    }
};

// Every hook here runs for every hit in the world (bots and creatures included), so each override rejects on null
// pointers and a non-player attacker before any call out; every per-talent / per-spell filter lives in the
// WarriorMechanics body. The enable list names exactly the hooks overridden (an empty list would enable every
// UnitHook). S3 appends its hooks to this class and to the list, never forks it.
// S1 (Protection): Incite's capstone (OnSpellDamageTakenFinal; its warrior-family filter now lives in the body).
// S2 (Arms): Colossus Smash on all three damage paths, the Sweeping capture (ModifySpellDamageTaken) and spend,
// Exploiter, Avatar, the copy / whirl crit Deep Wounds, Seismic sums, Second Wind on Rend and Deep Wounds ticks.
class WarriorUnitScript : public UnitScript
{
public:
    WarriorUnitScript() : UnitScript("WarriorUnitScript", true,
        { UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN, UNITHOOK_MODIFY_MELEE_DAMAGE, UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK,
          UNITHOOK_ON_SPELL_DAMAGE_TAKEN_FINAL, UNITHOOK_ON_PERIODIC_DAMAGE_FINAL }) { }

    // Pre-mitigation spell damage: Sweeping capture, then Colossus Smash, then Exploiter (in the body).
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (!target || !attacker || !spellInfo || !attacker->IsPlayer())
            return;

        Warrior::ModifySpellDamageTaken(target, attacker, damage, spellInfo);
    }

    // White swings (per damage slot, before armor and the outcome roll): Colossus Smash.
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        if (!target || !attacker || !attacker->IsPlayer())
            return;

        Warrior::ModifyMeleeDamage(target, attacker, damage);
    }

    // Damage, leech and heal ticks (the body skips positive spells): Colossus Smash on Rend.
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage,
        SpellInfo const* spellInfo) override
    {
        if (!target || !attacker || !spellInfo || !attacker->IsPlayer())
            return;

        Warrior::ModifyPeriodicDamageAurasTick(target, attacker, damage, spellInfo);
    }

    // Post-mitigation, pre-absorb, carries isCrit. Incite (D11; the Revenge stamp from the dispatcher), Sweeping
    // spend, Avatar, the copy / whirl crits, Seismic sums, Second Wind on the Deep Wounds tick: all filtered inside.
    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo,
        bool isCrit) override
    {
        if (!target || !attacker || !spellInfo || !attacker->IsPlayer())
            return;

        Warrior::OnSpellDamageTakenFinal(target, attacker, damage, spellInfo, isCrit);
    }

    // Pre-absorb periodic damage: Second Wind on Rend ticks.
    void OnPeriodicDamageFinal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo,
        bool isCrit) override
    {
        if (!target || !attacker || !spellInfo || !attacker->IsPlayer())
            return;

        Warrior::OnPeriodicDamageFinal(target, attacker, damage, spellInfo, isCrit);
    }
};

void AddSC_warrior_hooks()
{
    new WarriorPlayerScript();
    new WarriorUnitScript();
}
