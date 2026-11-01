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

// Custom: every class automatically knows every weapon type it is allowed to equip, instead of
// having to buy the proficiency from a weapon trainer. "Allowed" is whatever SkillRaceClassInfo.dbc
// lists for the player's race/class, i.e. exactly what the trainers would have offered.
// Runs on login, so existing characters are caught up too; already-known spells are skipped.
//
// The same script grants Plate (Warrior, Paladin) and Mail (Hunter, Shaman) from level 1 instead of level 40, from an
// explicit list so no other armor skill is granted. The equip check is skill-only and ignores the
// SkillRaceClassInfo MinLevel, and the level-40 trainer rows are removed in dbc-tools (dungeon-prereqs S1).

#include "DBCStores.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellInfo.h"
#include "SpellMgr.h"

namespace
{
    enum ArmorProficiency
    {
        SPELL_PLATE_MAIL_PROFICIENCY = 750,
        SPELL_MAIL_PROFICIENCY       = 8737,
    };

    struct ArmorGrant
    {
        uint32 classId;
        uint32 skillId;
        uint32 spellId;
    };

    ArmorGrant const ArmorGrants[] =
    {
        { CLASS_WARRIOR, SKILL_PLATE_MAIL, SPELL_PLATE_MAIL_PROFICIENCY },
        { CLASS_PALADIN, SKILL_PLATE_MAIL, SPELL_PLATE_MAIL_PROFICIENCY },
        { CLASS_HUNTER,  SKILL_MAIL,       SPELL_MAIL_PROFICIENCY       },
        { CLASS_SHAMAN,  SKILL_MAIL,       SPELL_MAIL_PROFICIENCY       },
    };

    struct WeaponProficiency
    {
        uint32 skillId;
        uint32 spellId;
    };

    // Weapon-skill proficiency spells (SPELL_EFFECT_PROFICIENCY on ITEM_CLASS_WEAPON), built once.
    std::vector<WeaponProficiency> const& GetWeaponProficiencies()
    {
        static std::vector<WeaponProficiency> const proficiencies = []
        {
            std::vector<WeaponProficiency> result;
            for (SkillLineAbilityEntry const* ability : sSkillLineAbilityStore)
            {
                if (!ability)
                    continue;

                SkillLineEntry const* skill = sSkillLineStore.LookupEntry(ability->SkillLine);
                if (!skill || skill->categoryId != SKILL_CATEGORY_WEAPON)
                    continue;

                SpellInfo const* spell = sSpellMgr->GetSpellInfo(ability->Spell);
                if (!spell || spell->EquippedItemClass != ITEM_CLASS_WEAPON)
                    continue;

                // The proficiency effect is not always first: e.g. 2H Axes is WEAPON, then PROFICIENCY.
                bool hasProficiency = false;
                for (SpellEffectInfo const& effect : spell->GetEffects())
                    hasProficiency |= effect.IsEffect(SPELL_EFFECT_PROFICIENCY);

                if (!hasProficiency)
                    continue;

                result.push_back({ ability->SkillLine, ability->Spell });
            }
            return result;
        }();
        return proficiencies;
    }
}

class Custom_WeaponProficiency : public PlayerScript
{
public:
    Custom_WeaponProficiency() : PlayerScript("Custom_WeaponProficiency") { }

    void OnPlayerLogin(Player* player) override
    {
        for (WeaponProficiency const& proficiency : GetWeaponProficiencies())
        {
            if (player->HasSpell(proficiency.spellId))
                continue;

            if (!GetSkillRaceClassInfo(proficiency.skillId, player->getRace(), player->getClass()))
                continue;

            if (!player->HasSkill(proficiency.skillId))
                player->LearnDefaultSkill(proficiency.skillId, 0);

            player->learnSpell(proficiency.spellId);
        }

        for (ArmorGrant const& grant : ArmorGrants)
        {
            if (grant.classId != player->getClass() || player->HasSpell(grant.spellId))
                continue;

            if (!GetSkillRaceClassInfo(grant.skillId, player->getRace(), player->getClass()))
                continue;

            if (!player->HasSkill(grant.skillId))
                player->LearnDefaultSkill(grant.skillId, 0);

            player->learnSpell(grant.spellId);
        }
    }
};

void AddSC_custom_weapon_proficiency()
{
    new Custom_WeaponProficiency();
}
