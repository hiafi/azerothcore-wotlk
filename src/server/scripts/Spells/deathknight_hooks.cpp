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
#include "Spell.h"
#include "SpellInfo.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include "UnitScript.h"

// ScriptMgr::DealDamage calls every UnitScript's DealDamage with no hook-enable check (there is no DealDamage
// UnitHook); an empty enable list would enable every UnitHook entry, so the list names the hooks S1 overrides plus
// one cheap, rare hook (shaman_hooks.cpp ShamanUnitScript precedent). Every hook here runs for every unit in the world:
// cheapest checks first, no lookups before the early-outs.
class DeathKnightUnitScript : public UnitScript
{
public:
    DeathKnightUnitScript() : UnitScript("DeathKnightUnitScript", true,
        { UNITHOOK_ON_UNIT_DEATH, UNITHOOK_ON_DAMAGE, UNITHOOK_MODIFY_HEAL_RECEIVED, UNITHOOK_ON_HEAL_FINAL,
          UNITHOOK_MODIFY_MELEE_DAMAGE }) { }

    // Death Strike damage-taken record, then Purgatory (U9). Unit::DealDamage calls this for every hit in the world
    // after armor, reductions and all absorbs, so the checks run cheapest first.
    uint32 DealDamage(Unit* attacker, Unit* victim, uint32 damage, DamageEffectType damagetype) override
    {
        if (!damage || !victim || !victim->IsPlayer())
            return damage;

        if (damagetype == SELF_DAMAGE || damagetype == NODAMAGE)
            return damage;

        Player* player = victim->ToPlayer();
        if (!DeathKnight::TracksDamageTaken(player))
            return damage;

        DeathKnight::RecordDamageTaken(player, damage);

        // Purgatory after the record, so the damage it prevents is already counted. It lowers damage in place to
        // health - 1 on a lethal hit and checks the talent, lockout, duel and CHEAT_GOD itself.
        DeathKnight::TryPurgatory(player, attacker, damage);
        return damage;
    }

    // U5 Voracious and Crimson Communion leech (Unit::DealDamage, post-absorb damage). Only a player's own damage
    // leeches: minion, pet and Rune Weapon damage never does; self-damage is skipped.
    void OnDamage(Unit* attacker, Unit* victim, uint32& damage) override
    {
        if (!damage || !attacker || !victim || attacker == victim || !attacker->IsPlayer())
            return;

        DeathKnight::OnDamageDealt(attacker, victim, damage);
    }

    // U6 Voracious capstone. The direct path (Unit::HealBySpell) passes (healer, target) and the periodic path
    // (AuraEffect::HandlePeriodicHealAurasTick) passes (target, caster): the hook cannot tell them apart, so both units
    // go through in the order given and ApplyVoraciousCapstone resolves the receiver.
    void ModifyHealReceived(Unit* target, Unit* healer, uint32& heal, SpellInfo const* spellInfo) override
    {
        if (!heal || !spellInfo || !target || !healer)
            return;

        if (!target->IsPlayer() && !healer->IsPlayer())
            return;

        DeathKnight::ApplyVoraciousCapstone(target, healer, heal, spellInfo, false);
    }

    // U7 Blood Shield: Death Strike's self-heal overheal (OnDeathStrikeHealFinal gates itself on 62908).
    void OnHealFinal(Unit* healer, Unit* target, SpellInfo const* spellInfo, uint32 heal, uint32 effective,
        uint32 healAbsorbed, bool /*isCrit*/, bool /*isPeriodic*/) override
    {
        if (!spellInfo || spellInfo->Id != DeathKnightData::SPELL_DEATH_STRIKE_HEAL || !healer || healer != target)
            return;

        if (Player* player = healer->ToPlayer())
            DeathKnight::OnDeathStrikeHealFinal(player, heal, effective, healAbsorbed);
    }

    // U17 Bloodworm white swings take the owner's damage multiplier (Unit::CalculateMeleeDamage passes the target
    // first). Worms only melee, so this covers all their damage.
    void ModifyMeleeDamage(Unit* /*target*/, Unit* attacker, uint32& damage) override
    {
        if (!damage || !attacker || DeathKnight::GetMinionKind(attacker) != DeathKnight::MinionKind::Bloodworm)
            return;

        Player* owner = DeathKnight::GetMinionOwner(attacker);
        if (!owner)
            return;

        damage = uint32(float(damage) * DeathKnight::GetMinionDamageMultiplier(owner, attacker, nullptr));
    }
};

class DeathKnightPlayerScript : public PlayerScript
{
public:
    DeathKnightPlayerScript() : PlayerScript("DeathKnightPlayerScript",
        { PLAYERHOOK_ON_CALCULATE_TALENTS_POINTS, PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT,
          PLAYERHOOK_ON_CREATURE_KILL, PLAYERHOOK_ON_PVP_KILL, PLAYERHOOK_ON_SPELL_CAST }) { }

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

    // U22 Red Thirst: Spell::_cast fires this for every player cast, before TakePower (m_powerCost is already set).
    // Only Runic Power costs pass here; OnRunicPowerSpent checks triggered casts and the 203126 marker.
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        if (!player || !spell || spell->GetSpellInfo()->PowerType != POWER_RUNIC_POWER || spell->GetPowerCost() <= 0)
            return;

        DeathKnight::OnRunicPowerSpent(player, spell);
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
