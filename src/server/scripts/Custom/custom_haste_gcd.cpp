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

// Haste shortens the global cooldown of melee strikes, ranged shots and "ability"-flagged utility spells.
// The core only hastes the GCD of spells, so dbc-tools generates one hidden passive aura per class family
// whose FLAT SPELLMOD_GLOBAL_COOLDOWN effects cover those abilities (effect 0 the melee-class bits, effect 1
// the ranged-class bits, effect 2 is a 500ms periodic dummy). Both follow spell haste, the same value the core
// hastes spell GCDs with: melee- or ranged-only attack speed (Flurry, Slice and Dice, Windfury Totem, quivers)
// speeds up auto attacks alone. The mods are flat because Player::ApplySpellMod ignores a
// pct GCD mod unless the same aura applied another mod to the spell. This file keeps the mod amounts in sync
// with the owner's haste and teaches each player the aura of their own class (own family only: spell-mod
// packets carry just a bit index and the client applies them to its own class's spells only, plan D8),
// re-granting it if a bot randomize strips it.
// Plan: .agents/plans/melee-haste-gcd/melee-haste-gcd.PLAN.md

#include "DBCStores.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <mutex>

namespace
{
    // Keep in sync with FAMILY_AURA_IDS in apps/dbc-tools/source/gcd_haste.py.
    constexpr uint32 HASTE_GCD_AURAS[] =
    {
        201560, // Warrior
        201561, // Paladin
        201562, // Hunter
        201563, // Druid
        201564, // Shaman
        201565, // Death Knight
        201566  // Warlock
    };

    // The 1.0s GCD floor is reached at -33%, so this is only a sanity bound.
    constexpr int32 MAX_GCD_REDUCTION_PCT = 50;

    // Every masked ability has a 1500ms GCD, so each percent of haste is exactly 15ms.
    constexpr int32 GCD_MS_PER_HASTE_PCT = 15;

    // FLAT spell-mod amount in ms (-750..0) for the owner's spell haste, in 1% steps.
    int32 GetHasteGcdMs(Unit const* owner)
    {
        // UNIT_MOD_CAST_SPEED is the cast time multiplier: haste rating, casting speed auras (Heroism, Wrath of Air)
        // and combat speed auras (Berserking). A net slow is clamped so it never lengthens the GCD.
        float const castSpeed = owner->GetFloatValue(UNIT_MOD_CAST_SPEED);
        if (castSpeed <= 0.0f || castSpeed >= 1.0f)
            return 0;

        int32 const pct = std::clamp(int32(std::lround((1.0f - castSpeed) * 100.0f)), 0, MAX_GCD_REDUCTION_PCT);
        return -GCD_MS_PER_HASTE_PCT * pct;
    }
}

class spell_custom_haste_gcd : public AuraScript
{
    PrepareAuraScript(spell_custom_haste_gcd);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        amount = GetHasteGcdMs(owner);
    }

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return;

        int32 const amount = GetHasteGcdMs(owner);
        for (uint8 i = EFFECT_0; i <= EFFECT_1; ++i)
        {
            AuraEffect* modEffect = GetEffect(i);
            if (!modEffect || modEffect->GetAuraType() != SPELL_AURA_ADD_FLAT_MODIFIER)
                continue;

            // Changing the amount re-sends the spell mod to the client, so only do it when it moved.
            if (amount != modEffect->GetAmount())
                modEffect->ChangeAmount(amount, false);
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(
            spell_custom_haste_gcd::CalculateAmount, EFFECT_ALL, SPELL_AURA_ADD_FLAT_MODIFIER);
        OnEffectPeriodic += AuraEffectPeriodicFn(
            spell_custom_haste_gcd::HandlePeriodic, EFFECT_2, SPELL_AURA_PERIODIC_DUMMY);
    }
};

namespace
{
    bool IsHasteGcdAura(uint32 spellId)
    {
        return std::find(std::begin(HASTE_GCD_AURAS), std::end(HASTE_GCD_AURAS), spellId) != std::end(HASTE_GCD_AURAS);
    }

    // The aura ID for the player's class, 0 for a class without one. The one place that decides who gets which
    // family's aura: a class that needs several families (a future "Hero") changes only this function.
    uint32 GetHasteGcdAuraFor(Player const* player)
    {
        static std::array<uint32, MAX_CLASSES> auraByClass;
        static std::once_flag built;
        std::call_once(built, []
        {
            auraByClass.fill(0);
            for (uint32 classId = 1; classId < MAX_CLASSES; ++classId)
            {
                ChrClassesEntry const* classEntry = sChrClassesStore.LookupEntry(classId);
                if (!classEntry)
                    continue;

                for (uint32 const auraId : HASTE_GCD_AURAS)
                {
                    SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(auraId);
                    if (spellInfo && spellInfo->SpellFamilyName == classEntry->spellfamily)
                        auraByClass[classId] = auraId;
                }
            }
        });

        uint8 const classId = player->getClass();
        return classId < MAX_CLASSES ? auraByClass[classId] : 0;
    }

    // Teaches the aura silently (addSpell casts the passive; learnSpell would announce it and fire
    // OnPlayerLearnSpell) and re-applies it if the spell is known but the aura is gone.
    void EnsureHasteGcdAura(Player* player)
    {
        uint32 const auraId = GetHasteGcdAuraFor(player);
        if (!auraId || player->HasAura(auraId))
            return;

        if (!player->HasSpell(auraId))
            player->addSpell(auraId, SPEC_MASK_ALL, true);
        else
            player->CastSpell(player, auraId, true);
    }
}

class CustomHasteGcdGrant : public PlayerScript
{
public:
    CustomHasteGcdGrant() : PlayerScript("CustomHasteGcdGrant", { PLAYERHOOK_ON_LOGIN, PLAYERHOOK_ON_SPELL_CAST }) { }

    void OnPlayerLogin(Player* player) override
    {
        EnsureHasteGcdAura(player);

        // A GM class change or stale data left another family's aura behind.
        uint32 const ownAura = GetHasteGcdAuraFor(player);
        for (uint32 const auraId : HASTE_GCD_AURAS)
            if (auraId != ownAura && player->HasSpell(auraId))
                player->removeSpell(auraId, SPEC_MASK_ALL, false);
    }

    // mod-playerbots' Randomize strips auras (and may clear spells) while a bot is in the world.
    void OnPlayerSpellCast(Player* player, Spell* spell, bool /*skipCheck*/) override
    {
        // The heal's own triggered cast re-enters this hook before the aura exists, so only real casts heal.
        if (spell->IsTriggered() || IsHasteGcdAura(spell->GetSpellInfo()->Id))
            return;

        EnsureHasteGcdAura(player);
    }
};

void AddSC_custom_haste_gcd()
{
    RegisterSpellScript(spell_custom_haste_gcd);
    new CustomHasteGcdGrant();
}
