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

// Weapon scaling (plan: .agents/plans/weapon-scaling/weapon-scaling.PLAN.md, stages WS0a and WS0 fixes).
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

#include "Config.h"
#include "DruidMechanics.h"
#include "ItemTemplate.h"
#include "Log.h"
#include "Player.h"
#include "ScriptMgr.h"
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
        float const value = sConfigMgr->GetOption<float>("WeaponScaling.FeralApPerDps", 0.0f);

        // Changing k_f with druids online would unapply a different value than was applied (m_baseFeralAP), so a
        // reload keeps the startup value.
        if (reload)
        {
            float const current = Druid::GetWeaponFeralApPerDps();
            float const wanted = value > 0.0f ? value : 0.0f;
            if (wanted != current)
                LOG_WARN("server.loading", "WeaponScaling.FeralApPerDps changed from {} to {}: it is read at startup "
                    "only, restart the worldserver to apply it", current, wanted);
            return;
        }

        Druid::SetWeaponFeralApPerDps(value);
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

void AddSC_custom_weapon_scaling()
{
    new Custom_WeaponScalingConfig();
    new Custom_WeaponScalingFeralAp();
}
