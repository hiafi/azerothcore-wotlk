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

#include "RogueMechanics.h"
#include "DataMap.h"
#include "GameTime.h"
#include "Item.h"
#include "ItemTemplate.h"
#include "ObjectGuid.h"
#include "Player.h"
#include "Random.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <unordered_map>

/*
 * RG0a block (docs/reworks/rogue-shared-rework.md "Energy and haste", "Poisons"): energy x (1 + spell haste) for every
 * energy user, the six poisons as self auras (two slots, the roll, the once-per-cast guard, the one application
 * helper, the weapon glow). Per-player state lives in CustomData: it belongs to the player's map thread, needs no lock,
 * and dies with the object (a relog builds a new Player), so nothing can go stale across sessions.
 */
namespace
{
    // Fan of Knives main-hand spread (one HIT event per target already; the off-hand copy 52874 is triggered and never
    // reaches the guard). Local: the generated header name of the stock spell is not part of the RG0a contract.
    constexpr uint32 FAN_OF_KNIVES_SPELL_ID = 51723;
    // Triggered spells allowed to roll: Mutilate's two halves, whose parent cast raises no proc of its own. Every
    // other triggered spell (Killing Spree's strikes, ...) rolls nothing (WP-R W1). Stock Shiv's 5940 never reaches
    // the guard (5938 suppresses its procs, 5940 is dropped by GetProcEffectMask); RG0b's Shiv calls ApplyPoison.
    constexpr uint32 TRIGGERED_ROLLERS[] = { 5374, 27576 };

    constexpr std::array<uint32, 3> LETHAL_POISON_AURAS =
    {
        RogueData::SPELL_INSTANT_POISON_203701,
        RogueData::SPELL_DEADLY_POISON_203702,
        RogueData::SPELL_WOUND_POISON_203703
    };

    constexpr std::array<uint32, 6> POISON_AURAS =
    {
        RogueData::SPELL_INSTANT_POISON_203701,
        RogueData::SPELL_DEADLY_POISON_203702,
        RogueData::SPELL_WOUND_POISON_203703,
        RogueData::SPELL_CRIPPLING_POISON_203704,
        RogueData::SPELL_MIND_NUMBING_POISON_203705,
        RogueData::SPELL_ANESTHETIC_POISON_203706
    };

    constexpr std::array<uint8, 2> GLOW_SLOTS = { EQUIPMENT_SLOT_MAINHAND, EQUIPMENT_SLOT_OFFHAND };

    // Base chance per poison aura (shared doc "Poisons": Lethal 20% flat, Crippling 30%, Mind-numbing 50%, Anesthetic
    // 50%); 0 for anything else.
    int32 GetPoisonBaseChancePct(uint32 auraId)
    {
        switch (auraId)
        {
            case RogueData::SPELL_INSTANT_POISON_203701:
            case RogueData::SPELL_DEADLY_POISON_203702:
            case RogueData::SPELL_WOUND_POISON_203703:
                return RogueData::POISON_LETHAL_CHANCE_PCT;
            case RogueData::SPELL_CRIPPLING_POISON_203704:
                return RogueData::POISON_CRIPPLING_CHANCE_PCT;
            case RogueData::SPELL_MIND_NUMBING_POISON_203705:
                return RogueData::POISON_MIND_NUMBING_CHANCE_PCT;
            case RogueData::SPELL_ANESTHETIC_POISON_203706:
                return RogueData::POISON_ANESTHETIC_CHANCE_PCT;
            default:
                return 0;
        }
    }

    // Once-per-cast record, one entry per poison aura: the game-time ms and the target of the last spell hit that
    // rolled.
    struct PoisonCastEntry
    {
        int64 timeMs = -1;
        ObjectGuid target;
    };

    struct PoisonCastGuard : DataMap::Base
    {
        std::unordered_map<uint32, PoisonCastEntry> byAura;
    };

    constexpr char const* POISON_CAST_GUARD_KEY = "rogue_poison_cast_guard";

    int64 NowMs()
    {
        return int64(GameTime::GetGameTimeMS().count());
    }

    bool IsWeapon(Item const* item)
    {
        return item && item->GetTemplate()->Class == ITEM_CLASS_WEAPON;
    }
}

namespace Rogue
{
    // ---- RG0a: energy haste ----

    bool IsEnergyUser(Player const* player)
    {
        if (!player)
            return false;

        // The one Classless change point (PLAN 1D.14): rogues and druids (Cat Form spends energy) regenerate faster.
        return player->IsClass(CLASS_ROGUE, CLASS_CONTEXT_ABILITY) ||
            player->IsClass(CLASS_DRUID, CLASS_CONTEXT_ABILITY);
    }

    int32 GetEnergyHastePct(Unit const* unit)
    {
        if (!unit)
            return 0;

        // A rate, not a cooldown cut: energy fills 1 + h times as fast, so the regen bonus is 100 / castSpeed - 100.
        // UNIT_MOD_CAST_SPEED holds haste rating, casting-speed and combat-speed auras (the custom_haste_gcd.cpp read),
        // so melee-only attack speed (Slice and Dice) never counts. A net slow clamps to 0.
        float const castSpeed = unit->GetFloatValue(UNIT_MOD_CAST_SPEED);
        if (castSpeed <= 0.0f)
            return 0;

        int32 const maxPct = std::max<int32>(RogueData::ENERGY_HASTE_MAX_PCT, 0);
        return std::clamp<int32>(int32(std::lround(100.0f / castSpeed - 100.0f)), 0, maxPct);
    }

    void EnsureEnergyHaste(Player* player)
    {
        if (!player)
            return;

        uint32 const spellId = RogueData::SPELL_ENERGY_HASTE;
        if (!IsEnergyUser(player))
        {
            // A class change (GM, Classless) left it behind: removeSpell also drops the owned aura.
            if (player->HasSpell(spellId))
                player->removeSpell(spellId, SPEC_MASK_ALL, false);
            else if (player->HasAura(spellId))
                player->RemoveAurasDueToSpell(spellId);

            return;
        }

        if (player->HasAura(spellId))
            return;

        // The EnsureHasteGcdAura shape: teach silently (addSpell casts the passive; learnSpell would announce it), or
        // recast if known but the aura is gone (mod-playerbots Randomize strips auras).
        if (!player->HasSpell(spellId))
            player->addSpell(spellId, SPEC_MASK_ALL, true);
        else
            player->CastSpell(player, spellId, true);
    }

    void SyncEnergyHaste(Unit* owner, AuraEffect* regen)
    {
        if (!owner || !regen)
            return;

        // CHANGE_AMOUNT -> HandleModPowerRegen -> UpdateEnergyRegen writes the regen modifier the client predicts from.
        int32 const pct = GetEnergyHastePct(owner);
        if (regen->GetAmount() != pct)
            regen->ChangeAmount(pct, false);
    }

    // ---- RG0a: poisons as self auras ----

    PoisonSlot GetPoisonSlot(uint32 auraSpellId)
    {
        switch (auraSpellId)
        {
            case RogueData::SPELL_INSTANT_POISON_203701:
            case RogueData::SPELL_DEADLY_POISON_203702:
            case RogueData::SPELL_WOUND_POISON_203703:
                return PoisonSlot::Lethal;
            case RogueData::SPELL_CRIPPLING_POISON_203704:
            case RogueData::SPELL_MIND_NUMBING_POISON_203705:
            case RogueData::SPELL_ANESTHETIC_POISON_203706:
                return PoisonSlot::NonLethal;
            default:
                return PoisonSlot::None;
        }
    }

    uint8 GetLethalSlots(Player const* /*rogue*/)
    {
        return uint8(std::max<int32>(RogueData::POISON_LETHAL_SLOTS, 1));
    }

    void EnforceLethalSlots(Player* rogue, uint32 keptAuraId)
    {
        if (!rogue)
            return;

        uint8 const slots = GetLethalSlots(rogue);
        while (true)
        {
            uint8 held = 0;
            Aura* oldest = nullptr;
            for (uint32 const auraId : LETHAL_POISON_AURAS)
            {
                Aura* aura = rogue->GetAura(auraId, rogue->GetGUID());
                if (!aura)
                    continue;

                ++held;
                if (auraId == keptAuraId)
                    continue;

                // GetApplyTime() is in seconds, so ties are common (a two-poison macro lands in one second): the
                // array is in ascending id order and only a strictly older aura replaces the pick, so a tie keeps the
                // lowest id.
                if (!oldest || aura->GetApplyTime() < oldest->GetApplyTime())
                    oldest = aura;
            }

            if (held <= slots || !oldest)
                return;

            oldest->Remove();
        }
    }

    bool PoisonRollAllowed(Unit const* rogue, ProcEventInfo& eventInfo, uint32 auraId)
    {
        // 1. Only the rogue's own action rolls (a pet's or anyone else's hit never does).
        Unit* actor = eventInfo.GetActor();
        if (!rogue || !actor || actor != rogue)
            return false;

        // 2. A valid, living, hostile target other than the rogue: a melee-class spell with a self-targeted effect
        // (Feint, P0 M1) makes the caster a hit target of its own cast.
        Unit* target = eventInfo.GetActionTarget();
        if (!target || target == actor || !target->IsAlive() || !actor->IsValidAttackTarget(target))
            return false;

        if (Spell const* spell = eventInfo.GetProcSpell())
        {
            SpellInfo const* spellInfo = spell->GetSpellInfo();
            if (!spellInfo)
                return false;

            // 3a. U2: Sap, Gouge, Blind (and anything else that breaks on damage or suppresses weapon procs) never
            // poison. Load-bearing: the aura-proc path ignores the stock item-enchant exemption (0-verify C3).
            if (spellInfo->HasAttribute(SPELL_ATTR0_CANCELS_AUTO_ATTACK_COMBAT) ||
                spellInfo->HasAttribute(SPELL_ATTR4_SUPPRESS_WEAPON_PROCS))
                return false;

            // 3a'. Triggered casts roll nothing, except the allow-listed halves above.
            if (spell->IsTriggered() &&
                std::find(std::begin(TRIGGERED_ROLLERS), std::end(TRIGGERED_ROLLERS), spellInfo->Id) ==
                    std::end(TRIGGERED_ROLLERS))
                return false;

            // 3b. Fan of Knives: one HIT event per target already, every target rolls.
            if (spellInfo->Id == FAN_OF_KNIVES_SPELL_ID)
                return true;

            // 3c. A targeted cast rolls only on its own target.
            if (Unit const* castTarget = spell->m_targets.GetUnitTarget())
                if (castTarget != target)
                    return false;

            // 3d. Once per cast per aura: a second event on the same target at the same game time is the same cast
            // or a sibling of it (Mutilate's two halves). Accepted edge: the clock only advances once per world
            // update, so two different casts landing on one target in the same update roll once per aura.
            PoisonCastGuard* guard = actor->CustomData.GetDefault<PoisonCastGuard>(POISON_CAST_GUARD_KEY);
            PoisonCastEntry& entry = guard->byAura[auraId];
            int64 const now = NowMs();
            ObjectGuid const targetGuid = target->GetGUID();
            if (entry.timeMs == now && entry.target == targetGuid)
                return false;

            entry.timeMs = now;
            entry.target = targetGuid;
            return true;
        }

        // 4. Auto attack: extra attacks (Sword Specialization, Hack and Slash, ...) roll nothing.
        return actor->GetLastExtraAttackSpell() == 0;
    }

    bool RollPoison(Player* rogue, uint32 auraId, ProcEventInfo& eventInfo)
    {
        if (!rogue)
            return false;

        int32 const baseChance = GetPoisonBaseChancePct(auraId);
        if (baseChance <= 0)
            return false;

        // Points first: base + SPELLMOD_CHANCE_OF_SUCCESS mods on the aura id (Improved Poisons and later talents).
        float chance = float(baseChance);
        rogue->ApplySpellMod(auraId, SPELLMOD_CHANCE_OF_SUCCESS, chance);

        // Then the speed factor, melee auto attacks only: the hitting hand's unhasted speed / 2600 (GetAttackTime
        // divides the hasted field by m_modAttackSpeedPct), so a slow weapon does not lose poison applications.
        if (!eventInfo.GetProcSpell() && (eventInfo.GetTypeMask() & PROC_FLAG_DONE_MELEE_AUTO_ATTACK))
        {
            DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
            WeaponAttackType const attType = damageInfo ? damageInfo->GetAttackType() : BASE_ATTACK;
            int32 const referenceMs = std::max<int32>(RogueData::POISON_REFERENCE_WEAPON_SPEED_MS, 1);
            chance *= float(rogue->GetAttackTime(attType)) / float(referenceMs);
        }

        // Then Proc Chance (the native roll's multiplier never matters: spell_proc Chance 100 always passes it).
        chance *= 1.0f + rogue->GetProcChancePercentage() / 100.0f;

        return roll_chance_f(std::min(chance, 100.0f));
    }

    void ApplyPoison(Player* rogue, Unit* target, uint32 payloadId, AuraEffect const* triggeredBy,
        PoisonSource /*source*/)
    {
        if (!rogue || !target || !payloadId)
            return;

        // The source is the hook point for later stages (Shiv, Kingsbane, Deadly Brew, Venomous Fan); RG0a casts the
        // payload the same way for all of them. Every payload is 100 yd: a script cast is range-checked (C4).
        rogue->CastSpell(target, payloadId, TRIGGERED_FULL_MASK, nullptr, triggeredBy);
    }

    bool HasAnyPoison(Player const* rogue)
    {
        if (!rogue)
            return false;

        return std::any_of(POISON_AURAS.begin(), POISON_AURAS.end(), [rogue](uint32 auraId)
        {
            return rogue->HasAura(auraId);
        });
    }

    void ApplyPoisonGlow(Player* player)
    {
        if (!player)
            return;

        for (uint8 const slot : GLOW_SLOTS)
            WritePoisonGlow(player, slot);
    }

    void WritePoisonGlow(Player* player, uint8 slot)
    {
        if (!player || (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND))
            return;

        if (!IsWeapon(player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot)) || !HasAnyPoison(player))
            return;

        // Only the temp half of the visible-item enchant field (PlayerStorage.cpp SetVisibleItemSlot): no item or DB
        // change, the item's real enchants stay on it. A real temp enchant (stone, oil) may hide the glow (P0-RESULTS).
        player->SetUInt16Value(PLAYER_VISIBLE_ITEM_1_ENCHANTMENT + (slot * 2), 1,
            uint16(RogueData::POISON_GLOW_ENCHANT));
    }

    void RestorePoisonGlow(Player* player)
    {
        if (!player)
            return;

        // SetVisibleItemSlot rewrites the real values; the visible-slot hook then re-applies the glow while another
        // poison is still up (the removed aura is already gone when AfterEffectRemove runs).
        for (uint8 const slot : GLOW_SLOTS)
            if (Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot))
                player->SetVisibleItemSlot(slot, item);
    }
}
