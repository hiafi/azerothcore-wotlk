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
 * Shaman rework - ScriptMgr handlers (shaman-rework SH0a; docs/reworks/shaman-shared-rework.md). One class per hook
 * kind: later shaman stages extend ShamanPlayerScript and ShamanUnitScript. Every per-player hook returns early
 * unless the player is a shaman; the bodies live in ShamanMechanics.
 */

#include "Item.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ShamanMechanics.h"
#include "SpellAuras.h"
#include "Unit.h"
#include "UnitScript.h"

// The new Stoneskin buff (202206). 8072 (stock Stoneskin Totem buff, `stoneskin_8072`) is still declared in the DSL
// and, as the lower id, owns the short header name SPELL_STONESKIN: use the _202206 name, fail the build on a mixup.
static_assert(ShamanData::SPELL_STONESKIN_202206 == 202206,
    "ShamanData::SPELL_STONESKIN_202206 must be the SH0a Stoneskin buff");

namespace
{
    bool IsShaman(Player const* player)
    {
        return player && player->getClass() == CLASS_SHAMAN;
    }
}

class ShamanPlayerScript : public PlayerScript
{
public:
    ShamanPlayerScript() : PlayerScript("ShamanPlayerScript",
        { PLAYERHOOK_ON_AFTER_SET_VISIBLE_ITEM_SLOT, PLAYERHOOK_ON_LEVEL_CHANGED, PLAYERHOOK_ON_LOGIN,
          PLAYERHOOK_ON_LEARN_SPELL, PLAYERHOOK_ON_PLAYER_ENTER_COMBAT, PLAYERHOOK_ON_PLAYER_LEAVE_COMBAT,
          PLAYERHOOK_ON_LOGOUT }) { }

    // Imbue glow (P0 section 5): SetVisibleItemSlot (equip, swap, enchant, login inventory load) just rewrote the
    // slot's real enchant visuals; write the active imbue's glow back over the temp half. Auras load before the
    // inventory at login (_LoadAuras before _LoadInventory), so this hook is what draws the login glow. No imbue
    // up: keep the real values (a sharpening stone or poison stays visible).
    void OnPlayerAfterSetVisibleItemSlot(Player* player, uint8 slot, Item* item) override
    {
        if (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND)
            return;

        if (!item || item->GetTemplate()->Class != ITEM_CLASS_WEAPON || !IsShaman(player))
            return;

        if (Shaman::GetActiveImbue(player))
            Shaman::WriteImbueGlow(player, slot);
    }

    // B11: attunement amounts come from the caster's level at aura creation; recalculate them on a level change.
    // mod-playerbots' level changes also strip auras, so the Reincarnation grant is re-checked here too.
    void OnPlayerLevelChanged(Player* player, uint8 /*oldLevel*/) override
    {
        if (!IsShaman(player))
            return;

        Shaman::RefreshAttunements(player);
        Shaman::EnsureReincarnationAura(player);

        // Rockbiter's attack power scales with level and is computed at aura creation (SH0a review L1).
        if (Aura* rockbiter = player->GetAura(ShamanData::SPELL_ROCKBITER_WEAPON, player->GetGUID()))
            rockbiter->RecalculateAmountOfEffects();
    }

    // Reincarnation without the Ankh: Player.cpp's resurrect-choice gate needs 58059 (0-verify surprise 4). Spells
    // loaded from the DB never reach the learn hook, so login grants it for every shaman that knows 20608.
    // The glow: auras and inventory are both loaded by now and the visible-slot hook already drew it; re-applying
    // here is idempotent and covers any slot the load path wrote without that hook.
    void OnPlayerLogin(Player* player) override
    {
        if (!IsShaman(player))
            return;

        Shaman::EnsureReincarnationAura(player);

        if (Shaman::GetActiveImbue(player))
            Shaman::ApplyImbueGlow(player);

        // Stoneskin is saved with its stacks but the 2 min timer is not: re-arm it for a shaman who logs in out of
        // combat (no-op without Stoneskin).
        if (!player->IsInCombat())
            Shaman::OnCombatChange(player, false);
    }

    // Trainer, .learn and skill-rewarded learns of Reincarnation (Player::learnSpell, after addSpell succeeded).
    void OnPlayerLearnSpell(Player* player, uint32 spellID) override
    {
        if (spellID != ShamanData::SPELL_REINCARNATION || !IsShaman(player))
            return;

        Shaman::EnsureReincarnationAura(player);
    }

    // Stoneskin's 2 min out-of-combat timer: cancelled on entry, armed on leave. OnPlayerLeaveCombat can fire twice
    // for one exit (CombatManager::UpdateOwnerCombatState and Unit::ClearInCombat); OnCombatChange re-arms.
    void OnPlayerEnterCombat(Player* player, Unit* /*enemy*/) override
    {
        if (IsShaman(player))
            Shaman::OnCombatChange(player, true);
    }

    void OnPlayerLeaveCombat(Player* player) override
    {
        if (IsShaman(player))
            Shaman::OnCombatChange(player, false);
    }

    void OnPlayerLogout(Player* player) override
    {
        if (IsShaman(player))
            Shaman::ClearState(player);
    }
};

// ScriptMgr::DealDamage calls every UnitScript's DealDamage with no hook-enable check; an empty enable list would
// enable all UnitHook entries, so the list names one rare hook this class does not override.
class ShamanUnitScript : public UnitScript
{
public:
    ShamanUnitScript() : UnitScript("ShamanUnitScript", true, { UNITHOOK_ON_UNIT_SET_SHAPESHIFT_FORM }) { }

    // B15 Stoneskin erosion. Unit::DealDamage calls this first, with the amount that lands on health: armor, every
    // % reduction (Stoneskin included), block, resilience, resist and absorbs are already taken off (melee
    // CalculateMeleeDamage, spells CalculateSpellDamageTaken, DoT ticks and damage shields all run CalcAbsorbResist
    // and pass the post-absorb amount). Misses, dodges and parries never get here; a full absorb arrives as 0.
    // Runs for every hit in the world: cheapest checks first.
    uint32 DealDamage(Unit* /*attacker*/, Unit* victim, uint32 damage, DamageEffectType damagetype) override
    {
        if (!damage || !victim || !victim->IsPlayer())
            return damage;

        // SELF_DAMAGE: environmental and fall damage (Player::EnvironmentalDamage), self mana-burn style ticks.
        // NODAMAGE: SHARE_DAMAGE_PCT copies and other health-only bookkeeping.
        if (damagetype == SELF_DAMAGE || damagetype == NODAMAGE)
            return damage;

        Player* shaman = victim->ToPlayer();
        if (shaman->getClass() != CLASS_SHAMAN || !shaman->HasAura(ShamanData::SPELL_STONESKIN_202206))
            return damage;

        Shaman::ErodeStoneskin(shaman, damage);
        return damage;
    }
};

void AddSC_shaman_hooks()
{
    new ShamanPlayerScript();
    new ShamanUnitScript();
}
