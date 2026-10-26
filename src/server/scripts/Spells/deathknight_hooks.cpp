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
 * Death Knight rework - ScriptMgr handlers (death-knight-rework DK0a, DK0b, S1-S3). Bodies: DeathKnightMechanics.
 */

#include "AllCreatureScript.h"
#include "AreaDefines.h"
#include "Creature.h"
#include "DeathKnightMechanics.h"
#include "Item.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "PetScript.h"
#include "Player.h"
#include "PlayerScript.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include "UnitScript.h"
#include <algorithm>

// ScriptMgr::DealDamage calls every UnitScript's DealDamage with no hook-enable check (there is no DealDamage
// UnitHook); an empty enable list would enable every UnitHook entry, so the list names the hooks S1 overrides plus
// one cheap, rare hook (shaman_hooks.cpp ShamanUnitScript precedent). Every hook here runs for every unit in the world:
// cheapest checks first, no lookups before the early-outs.
class DeathKnightUnitScript : public UnitScript
{
public:
    DeathKnightUnitScript() : UnitScript("DeathKnightUnitScript", true,
        { UNITHOOK_ON_UNIT_DEATH, UNITHOOK_ON_DAMAGE, UNITHOOK_MODIFY_HEAL_RECEIVED, UNITHOOK_ON_HEAL_FINAL,
          UNITHOOK_MODIFY_MELEE_DAMAGE, UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN }) { }

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

    // The minion damage seam on white swings (Unit::CalculateMeleeDamage passes the target first): S1 U17
    // Bloodworms, S3 U16 every Unholy minion kind. GetMinionDamageMultiplier is 1.0 for anything else.
    void ModifyMeleeDamage(Unit* /*target*/, Unit* attacker, uint32& damage) override
    {
        if (!damage || !attacker || !attacker->IsCreature() ||
            DeathKnight::GetMinionKind(attacker) == DeathKnight::MinionKind::None)
            return;

        Player* owner = DeathKnight::GetMinionOwner(attacker);
        if (!owner)
            return;

        float const multiplier = DeathKnight::GetMinionDamageMultiplier(owner, attacker, nullptr);
        if (multiplier != 1.0f)
            damage = uint32(std::max(0.0f, float(damage) * multiplier));
    }

    // S3 U16 (D11): the same seam on a minion's direct spell hits (Claw, Gargoyle Strike, the cloud tick, the
    // detonation). Unit::CalculateSpellDamageTaken calls this for every direct spell hit in the world, before armor
    // and crit (periodic ticks never reach it), so the cheapest checks come first. The Dancing Rune Weapon passes its
    // owner as the attacker and is MinionKind::None anyway.
    void ModifySpellDamageTaken(Unit* /*target*/, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (damage <= 0 || !attacker || !spellInfo || !attacker->IsCreature())
            return;

        if (DeathKnight::GetMinionKind(attacker) == DeathKnight::MinionKind::None)
            return;

        // The hook honours IGNORE_CASTER_MODIFIERS itself (HunterMechanics.cpp / druid_hooks.cpp precedent).
        if (spellInfo->HasAttribute(SPELL_ATTR3_IGNORE_CASTER_MODIFIERS))
            return;

        Player* owner = DeathKnight::GetMinionOwner(attacker);
        if (!owner)
            return;

        float const multiplier = DeathKnight::GetMinionDamageMultiplier(owner, attacker, spellInfo);
        if (multiplier != 1.0f)
            damage = int32(std::max(0.0f, float(damage) * multiplier));
    }
};

class DeathKnightPlayerScript : public PlayerScript
{
public:
    DeathKnightPlayerScript() : PlayerScript("DeathKnightPlayerScript",
        { PLAYERHOOK_ON_CALCULATE_TALENTS_POINTS, PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT,
          PLAYERHOOK_ON_CREATURE_KILL, PLAYERHOOK_ON_PVP_KILL, PLAYERHOOK_ON_SPELL_CAST,
          PLAYERHOOK_ON_PLAYER_LEARN_TALENTS, PLAYERHOOK_ON_TALENTS_RESET, PLAYERHOOK_ON_AFTER_SPEC_SLOT_CHANGED,
          PLAYERHOOK_ON_MAP_CHANGED }) { }

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

    // U22 Red Thirst and S3 U18 the Gargoyle's ramp: Spell::_cast fires this for every player cast, before TakePower
    // (m_powerCost is already set). Only Runic Power costs pass here; OnRunicPowerSpent checks triggered casts, then
    // ramps the Gargoyle, then checks the 203126 marker. A free (Harbinger) Coil reports 0 and never ramps (D10).
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        if (!player || !spell || spell->GetSpellInfo()->PowerType != POWER_RUNIC_POWER || spell->GetPowerCost() <= 0)
            return;

        DeathKnight::OnRunicPowerSpent(player, spell);
    }

    // S3 U23 Infected Claws on the Master of Ghouls pet follows the talent. The rank's passive is applied before this
    // hook (Player::LearnTalent adds the talent first).
    void OnPlayerLearnTalents(Player* player, uint32 /*talentId*/, uint32 /*talentRank*/, uint32 /*spellid*/) override
    {
        RefreshInfectedClaws(player);
    }

    // Fires BEFORE the talents are removed (Player::resetTalents), so the refresh waits for the next update; only the
    // GUID is captured and the player re-resolved (hunter_hooks.cpp shape).
    void OnPlayerTalentsReset(Player* player, bool /*noCost*/) override
    {
        if (!player || !player->GetPet())
            return;

        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid]()
        {
            if (Player* dk = ObjectAccessor::FindPlayer(guid))
                RefreshInfectedClaws(dk);
        }, Milliseconds(0));
    }

    void OnPlayerAfterSpecSlotChanged(Player* player, uint8 /*newSlot*/) override
    {
        RefreshInfectedClaws(player);
    }

    // S3: minions removed on the old map could not reach their owner; resync the Lesser Ghoul counter, the
    // Gargoyle's Necromancy stacks and the Dark Transformation marker.
    void OnPlayerMapChanged(Player* player) override
    {
        if (player)
            DeathKnight::OnDeathKnightMapChanged(player);
    }

private:
    static void RefreshInfectedClaws(Player* player)
    {
        if (!player)
            return;

        // ApplyInfectedClaws checks the kind (Master of Ghouls ghoul) and the owner itself.
        if (Pet* pet = player->GetPet())
            DeathKnight::ApplyInfectedClaws(player, pet);
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
    void OnInitStatsForLevel(Guardian* guardian, uint8 petlevel) override
    {
        if (!guardian || guardian->IsPet())
            return;

        InitUnholyMinionWeapon(guardian, petlevel);
        ApplyMirror(guardian);
    }

    void OnPetAddToWorld(Pet* pet) override
    {
        if (!pet)
            return;

        ApplyMirror(pet);

        // S3 U23: the owner-cast Infected Claws aura (and the D6 display passive) on the Master of Ghouls pet; U22:
        // the Dark Transformation marker follows the new pet's Shadow Infusion (none survives a dismiss or relog).
        if (DeathKnight::GetMinionKind(pet) != DeathKnight::MinionKind::Ghoul)
            return;

        Player* owner = DeathKnight::GetMinionOwner(pet);
        if (!owner)
            return;

        DeathKnight::ApplyInfectedClaws(owner, pet);
        Aura const* infusion = pet->GetAura(DeathKnightData::SPELL_SHADOW_INFUSION);
        DeathKnight::OnShadowInfusionChanged(pet, infusion ? infusion->GetStackAmount() : 0);
    }

private:
    // S3: the Lesser Ghoul (300320) and Abomination (300321) templates are level 1, and Guardian::InitStatsForLevel
    // sets no weapon damage for them, so they would keep a level-1 weapon. 26125 has no level formula of its own on
    // this branch (pet_levelstats min/max 0, level-1 template), so they take the generic guardian weapon
    // (Pet.cpp SUMMON_PET fallback): petlevel -/+ petlevel / 4. Runs before InitStatsForLevel's UpdateAllStats, which
    // recomputes the damage fields.
    static void InitUnholyMinionWeapon(Guardian* minion, uint8 petlevel)
    {
        DeathKnight::MinionKind const kind = DeathKnight::GetMinionKind(minion);
        if (kind != DeathKnight::MinionKind::LesserGhoul && kind != DeathKnight::MinionKind::Abomination)
            return;

        if (!DeathKnight::GetMinionOwner(minion))
            return;

        minion->SetBaseWeaponDamage(BASE_ATTACK, MINDAMAGE, float(petlevel - (petlevel / 4)));
        minion->SetBaseWeaponDamage(BASE_ATTACK, MAXDAMAGE, float(petlevel + (petlevel / 4)));
    }

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

// S3: Lesser Ghoul (300320) counter recount and timer, the Gargoyle's (27829) start time and leave fallback, creature
// CustomData cleared on removal. AllCreatureScript has no enable list (every creature in the world reaches it), so
// the bodies start with a cheap entry check. Pets never reach these hooks (Pet::AddToWorld / RemoveFromWorld bypass
// Creature's).
class DeathKnightMinionWorldScript : public AllCreatureScript
{
public:
    DeathKnightMinionWorldScript() : AllCreatureScript("DeathKnightMinionWorldScript") { }

    void OnCreatureAddWorld(Creature* creature) override
    {
        if (creature && IsTracked(creature->GetEntry()))
            DeathKnight::OnMinionAddWorld(creature);
    }

    void OnCreatureRemoveWorld(Creature* creature) override
    {
        if (creature && IsTracked(creature->GetEntry()))
            DeathKnight::OnMinionRemoveWorld(creature);
    }

private:
    static bool IsTracked(uint32 entry)
    {
        return entry == DeathKnightData::NPC_LESSER_GHOUL || entry == DeathKnightData::NPC_EBON_GARGOYLE;
    }
};

void AddSC_deathknight_hooks()
{
    new DeathKnightUnitScript();
    new DeathKnightPlayerScript();
    new DeathKnightPetScript();
    new DeathKnightMinionWorldScript();
}
