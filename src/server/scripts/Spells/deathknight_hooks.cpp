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
 * Death Knight rework - ScriptMgr handlers (death-knight-rework DK0a, DK0b). Bodies live in DeathKnightMechanics.
 */

#include "AreaDefines.h"
#include "Creature.h"
#include "DeathKnightMechanics.h"
#include "Item.h"
#include "Pet.h"
#include "PetScript.h"
#include "Player.h"
#include "PlayerScript.h"
#include "ScriptMgr.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include "UnitScript.h"

// ScriptMgr::DealDamage calls every UnitScript's DealDamage with no hook-enable check (there is no DealDamage
// UnitHook); an empty enable list would enable every UnitHook entry, so the list names one cheap, rare hook instead
// (shaman_hooks.cpp ShamanUnitScript precedent; the P0 Purgatory spike used the same entry, and S1 may override it).
class DeathKnightUnitScript : public UnitScript
{
public:
    DeathKnightUnitScript() : UnitScript("DeathKnightUnitScript", true, { UNITHOOK_ON_UNIT_DEATH }) { }

    // Death Strike damage-taken record. Unit::DealDamage calls this for every hit in the world after armor, reductions
    // and all absorbs, so the checks run cheapest first. The amount is never changed in DK0a.
    uint32 DealDamage(Unit* /*attacker*/, Unit* victim, uint32 damage, DamageEffectType damagetype) override
    {
        if (!damage || !victim || !victim->IsPlayer())
            return damage;

        if (damagetype == SELF_DAMAGE || damagetype == NODAMAGE)
            return damage;

        Player* player = victim->ToPlayer();
        if (!DeathKnight::TracksDamageTaken(player))
            return damage;

        DeathKnight::RecordDamageTaken(player, damage);

        // S1 Purgatory goes here, after the record line, so the damage it prevents is already counted
        // (p0-spike-ref/custom_dk_p0_spike.cpp p0_dk_purgatory shape; needs the attacker parameter back).
        return damage;
    }
};

class DeathKnightPlayerScript : public PlayerScript
{
public:
    DeathKnightPlayerScript() : PlayerScript("DeathKnightPlayerScript",
        { PLAYERHOOK_ON_CALCULATE_TALENTS_POINTS, PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT,
          PLAYERHOOK_ON_CREATURE_KILL, PLAYERHOOK_ON_PVP_KILL }) { }

    // U4: Player::CalculateTalentsPoints gives a DK on Ebon Hold (map 609) level - 55 points plus quest talents. The
    // rework starts DKs at level 1, so on that map they earn the normal curve like anywhere else (insurance: Death
    // Gate lands on map 0 today). m_extraBonusTalentCount is always 0, so overwriting drops nothing.
    void OnPlayerCalculateTalentsPoints(Player const* player, uint32& talentPointsForLevel) override
    {
        // Same test as the core branch (Player.cpp CalculateTalentsPoints), so Classless/Freepick behave alike.
        if (!player->IsClass(CLASS_DEATH_KNIGHT, CLASS_CONTEXT_TALENT_POINT_CALC) ||
            player->GetMapId() != MAP_EBON_HOLD)
            return;

        uint8 const level = player->GetLevel();
        talentPointsForLevel = level < 10 ? 0 : level - 9;
    }

    // Rune glow (P0 item 3, shaman imbue-glow clone): SetVisibleItemSlot (equip, swap, enchant, login inventory load)
    // just rewrote the slot's real enchant visuals; write the active rune's glow back over the temp half. Auras load
    // before the inventory at login, so this hook draws the login glow (L5). No rune glow up: keep the real values.
    void OnPlayerAfterSetVisibleItemSlot(Player* player, uint8 slot, Item* item) override
    {
        if (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND)
            return;

        if (!item || item->GetTemplate()->Class != ITEM_CLASS_WEAPON || !player)
            return;

        if (DeathKnight::GetRuneGlowEnchant(DeathKnight::GetActiveRune(player)))
            DeathKnight::WriteRuneGlow(player, slot);
    }

    // U14 Unending Thirst: the DK's own killing blows. Unit::Kill fires this only when the killer itself is the
    // player, so pet and minion kills never reach it (B4). Critters and totems do not count.
    void OnPlayerCreatureKill(Player* killer, Creature* killed) override
    {
        if (!killer || !killed || killed->IsCritter() || killed->IsTotem())
            return;

        DeathKnight::OnRuneKillingBlow(killer, killed);
    }

    void OnPlayerPVPKill(Player* killer, Player* killed) override
    {
        if (!killer || !killed || killer == killed)
            return;

        DeathKnight::OnRuneKillingBlow(killer, killed);
    }
};

// Minion stat mirror (P0 item 8): the mirror auras go on right after the stock scaling auras installed their immunity
// block (Pet.cpp InitStatsForLevel); the mirrors are ALWAYS_HIT, so they pass it. Guardians (Army ghouls, the
// Gargoyle, Bloodworms, the plain Raise Dead ghoul) are handled at InitStatsForLevel; a pet (Master of Ghouls ghoul)
// once it is in the world (P0 spike shape; hunter_hooks.cpp HunterPetScript does the same).
class DeathKnightPetScript : public PetScript
{
public:
    DeathKnightPetScript() : PetScript("DeathKnightPetScript",
        { PETHOOK_ON_INIT_STATS_FOR_LEVEL, PETHOOK_ON_PET_ADD_TO_WORLD }) { }

    // Every Guardian, pets included (Pet.cpp InitStatsForLevel); pets are left to OnPetAddToWorld.
    void OnInitStatsForLevel(Guardian* guardian, uint8 /*petlevel*/) override
    {
        if (guardian && !guardian->IsPet())
            ApplyMirror(guardian);
    }

    void OnPetAddToWorld(Pet* pet) override
    {
        if (pet)
            ApplyMirror(pet);
    }

private:
    static void ApplyMirror(Guardian* minion)
    {
        if (DeathKnight::GetMinionKind(minion) == DeathKnight::MinionKind::None)
            return;

        // GetOwner() only, never GetOwningPlayer: that one is null until SetMinion (bug 3040).
        if (!DeathKnight::GetMinionOwner(minion))
            return;

        DeathKnight::ApplyMinionMirror(minion);
    }
};

void AddSC_deathknight_hooks()
{
    new DeathKnightUnitScript();
    new DeathKnightPlayerScript();
    new DeathKnightPetScript();
}
