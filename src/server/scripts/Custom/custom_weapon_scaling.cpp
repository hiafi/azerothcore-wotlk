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

// Weapon scaling (plan: .agents/plans/weapon-scaling/weapon-scaling.PLAN.md, stages WS0a, WS0 fixes and WSH0).
//
// Druids in Cat, Bear and Moonkin forms get attack power from their weapon. The stock formula is
// 14 x DPS - 767 (ItemTemplate::getFeralBonus): zero for every weapon under 54.8 DPS, so it only matters at the
// top of the item ladder. With WeaponScaling.FeralApPerDps (k_f) above 0, the form attack power of a weapon is
// instead proportional to its DPS, with no threshold: k_f x DPS, so a weapon upgrade matters at every tier.
// Rulings (user, 2026-11-17): with k_f above 0 only the main-hand (or two-hand) weapon counts, and only in Cat and
// Bear/Dire Bear form; an off-hand and Moonkin form get nothing. With k_f at 0 everything stays stock.
//
// - The per-item value goes through PlayerScript::OnPlayerGetFeralApBonus, called from Player::_ApplyItemBonuses
//   with the item's equipment slot for each item a druid equips or unequips. The core adds and removes it from
//   Player::m_baseFeralAP, so apply and unapply stay symmetric as long as k_f does not change while players are
//   online: it is read at startup only, never on .reload config.
// - Moonkin form: StatSystem.cpp adds Druid::GetMoonkinWeaponFormAp(m_baseFeralAP), which is 0 with k_f above 0.
//
// Hunters (stage WSH0, user ruling 2026-11-17): with WeaponScaling.RangedApPerDps (k_h) above 0, the weapon in the
// ranged slot (bow, gun, crossbow, thrown) gives ranged attack power k_h x DPS. The value goes through
// PlayerScript::OnPlayerGetWeaponRangedApBonus, called from Player::_ApplyItemBonuses for a hunter's ranged-slot item;
// the core adds it to (and on unequip removes it from) the UNIT_MOD_ATTACK_POWER_RANGED flat modifier, the same one
// ITEM_MOD_RANGED_ATTACK_POWER uses. Melee attack power is untouched. The hunter's pet inherits it through its owner
// ranged attack power share. Like k_f, k_h is read at startup only; with k_h at 0 the hook leaves the value at 0 and
// the core does nothing.
//
// Custom: gear-scaling GS2 D (.agents/plans/gear-scaling): WeaponScaling.ApPotencyReferenceItemLevel turns on the
// attack power potency weapon factor (SpellPotency::Apply). Read at startup only, like k_f and k_h; the reference DPS
// cache is built from it at OnStartup (custom_spell_potency.cpp).

#include "Config.h"
#include "DruidMechanics.h"
#include "HunterMechanics.h"
#include "ItemTemplate.h"
#include "Log.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellPotency.h"
#include <cmath>

namespace
{
    // Same inventory types ItemTemplate::getFeralBonus accepts.
    constexpr uint32 FERAL_AP_INVENTORY_TYPE_MASK = 1 << INVTYPE_WEAPON | 1 << INVTYPE_2HWEAPON |
        1 << INVTYPE_WEAPONMAINHAND | 1 << INVTYPE_WEAPONOFFHAND;
}

class Custom_WeaponScalingConfig : public WorldScript
{
public:
    Custom_WeaponScalingConfig() : WorldScript("Custom_WeaponScalingConfig", { WORLDHOOK_ON_AFTER_CONFIG_LOAD }) { }

    void OnAfterConfigLoad(bool reload) override
    {
        float const feralValue = sConfigMgr->GetOption<float>("WeaponScaling.FeralApPerDps", 0.0f);
        float const rangedValue = sConfigMgr->GetOption<float>("WeaponScaling.RangedApPerDps", 0.0f);
        uint32 const apReferenceItemLevel =
            sConfigMgr->GetOption<uint32>("WeaponScaling.ApPotencyReferenceItemLevel", 0);

        // Changing k_f or k_h with players online would unapply a different value than was applied (m_baseFeralAP, the
        // ranged attack power flat modifier), so a reload keeps the startup values.
        if (reload)
        {
            WarnIfChanged("WeaponScaling.FeralApPerDps", Druid::GetWeaponFeralApPerDps(), feralValue);
            WarnIfChanged("WeaponScaling.RangedApPerDps", Hunter::GetWeaponRangedApPerDps(), rangedValue);
            WarnIfChanged("WeaponScaling.ApPotencyReferenceItemLevel",
                float(SpellPotency::GetApWeaponReferenceItemLevel()), float(apReferenceItemLevel));
            return;
        }

        Druid::SetWeaponFeralApPerDps(feralValue);
        Hunter::SetWeaponRangedApPerDps(rangedValue);
        SpellPotency::SetApWeaponReferenceItemLevel(apReferenceItemLevel);
    }

private:
    static void WarnIfChanged(char const* key, float current, float value)
    {
        float const wanted = value > 0.0f ? value : 0.0f;
        if (wanted != current)
            LOG_WARN("server.loading", "{} changed from {} to {}: it is read at startup only, restart the worldserver "
                "to apply it", key, current, wanted);
    }
};

class Custom_WeaponScalingFeralAp : public PlayerScript
{
public:
    Custom_WeaponScalingFeralAp() :
        PlayerScript("Custom_WeaponScalingFeralAp", { PLAYERHOOK_ON_GET_FERAL_AP_BONUS }) { }

    void OnPlayerGetFeralApBonus(Player* /*player*/, int32& feral_bonus, int32 dpsMod, ItemTemplate const* proto,
        ScalingStatValuesEntry const* /*ssv*/, uint8 slot) override
    {
        float const perDps = Druid::GetWeaponFeralApPerDps();
        if (perDps <= 0.0f || !proto)
            return;

        // Only a weapon the stock formula covers; anything else keeps whatever the core computed.
        if (proto->Class != ITEM_CLASS_WEAPON || !((1u << proto->InventoryType) & FERAL_AP_INVENTORY_TYPE_MASK))
            return;

        // Only the main-hand (or two-hand) weapon gives form attack power; an off-hand gives none. `slot` is the
        // same on apply and unapply, so this stays symmetric.
        if (slot != EQUIPMENT_SLOT_MAINHAND)
        {
            feral_bonus = 0;
            return;
        }

        // dpsMod is the heirloom ScalingStatValues DPS bonus. ScalingStatValuesEntry::getFeralBonus is a stub
        // that returns 0 in 3.3.5, so replacing feral_bonus loses nothing on a heirloom.
        float const dps = proto->getDPS() + float(dpsMod);
        feral_bonus = dps > 0.0f ? int32(std::lround(perDps * dps)) : 0;
    }
};

class Custom_WeaponScalingRangedAp : public PlayerScript
{
public:
    Custom_WeaponScalingRangedAp() :
        PlayerScript("Custom_WeaponScalingRangedAp", { PLAYERHOOK_ON_GET_WEAPON_RANGED_AP_BONUS }) { }

    // The core calls this only for a hunter's ranged-slot item, with the same arguments on equip and unequip, so the
    // value it applies is the value it removes (k_h is startup-only).
    void OnPlayerGetWeaponRangedApBonus(Player* /*player*/, int32& ranged_ap, int32 dpsMod, ItemTemplate const* proto,
        uint8 slot) override
    {
        float const perDps = Hunter::GetWeaponRangedApPerDps();
        if (perDps <= 0.0f || !proto || slot != EQUIPMENT_SLOT_RANGED || proto->Class != ITEM_CLASS_WEAPON)
            return;

        // dpsMod is the heirloom ScalingStatValues DPS bonus, as in the druid hook.
        float const dps = proto->getDPS() + float(dpsMod);
        ranged_ap = dps > 0.0f ? int32(std::lround(perDps * dps)) : 0;
    }
};

void AddSC_custom_weapon_scaling()
{
    new Custom_WeaponScalingConfig();
    new Custom_WeaponScalingFeralAp();
    new Custom_WeaponScalingRangedAp();
}
