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

#include "ShamanMechanics.h"
#include "Item.h"
#include "ItemTemplate.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <mutex>
#include <unordered_map>
#include <vector>

/*
 * Shaman rework - shared mechanics (shaman-rework SH0). SH0a block: owner/actor helpers, Proc Chance rolls, imbue
 * lookup and weapon glow, Stoneskin (grant, erosion, out-of-combat timer), attunement level refresh and the
 * Reincarnation reagent aura.
 */
namespace
{
    // The Stoneskin stack aura (202206). Stock 8072 (Stoneskin Totem's armor buff) keeps the short header name
    // SPELL_STONESKIN, so the DSL variable stoneskin_202206 is emitted under its unstripped name.
    constexpr uint32 SPELL_STONESKIN_STACKS = ShamanData::SPELL_STONESKIN_202206;

    // Stock spells the DSL never declares.
    constexpr uint32 SPELL_GLYPH_OF_RENEWED_LIFE = 58059;   // aura 256: Reincarnation needs no Ankh (Player.cpp:13194)

    // SpellItemEnchantment ids whose ItemVisual draws each imbue's glow (SH0a 0-verify table 6).
    constexpr uint16 ENCHANT_ROCKBITER = 29;      // ItemVisual 61
    constexpr uint16 ENCHANT_FLAMETONGUE = 5;     // ItemVisual 32
    constexpr uint16 ENCHANT_FROSTBRAND = 2;      // ItemVisual 33
    constexpr uint16 ENCHANT_WINDFURY = 283;      // ItemVisual 81
    constexpr uint16 ENCHANT_EARTHLIVING = 3345;  // ItemVisual 106

    constexpr std::array<uint32, 5> IMBUE_AURAS =
    {
        ShamanData::SPELL_ROCKBITER_WEAPON,
        ShamanData::SPELL_FLAMETONGUE_WEAPON,
        ShamanData::SPELL_FROSTBRAND_WEAPON,
        ShamanData::SPELL_WINDFURY_WEAPON,
        ShamanData::SPELL_EARTHLIVING_WEAPON
    };

    // Stock Maelstrom Weapon talent ranks (the Enhancement stage replaces them).
    constexpr std::array<uint32, 5> MAELSTROM_WEAPON_RANKS =
    {
        ShamanData::SPELL_MAELSTROM_WEAPON,
        ShamanData::SPELL_MAELSTROM_WEAPON_51529,
        ShamanData::SPELL_MAELSTROM_WEAPON_51530,
        ShamanData::SPELL_MAELSTROM_WEAPON_51531,
        ShamanData::SPELL_MAELSTROM_WEAPON_51532
    };

    constexpr std::array<uint32, 4> ATTUNEMENT_PARENTS =
    {
        ShamanData::SPELL_EARTH_ATTUNEMENT,
        ShamanData::SPELL_WATER_ATTUNEMENT,
        ShamanData::SPELL_FIRE_ATTUNEMENT,
        ShamanData::SPELL_AIR_ATTUNEMENT
    };

    constexpr std::array<uint32, 2> ATTUNEMENT_CHILDREN =
    {
        ShamanData::SPELL_EARTH_ATTUNEMENT_ARMOR,
        ShamanData::SPELL_FIRE_ATTUNEMENT_SPELL_POWER
    };

    constexpr std::array<uint8, 2> GLOW_SLOTS = { EQUIPMENT_SLOT_MAINHAND, EQUIPMENT_SLOT_OFFHAND };

    // Per-player Stoneskin state. Maps update on several threads, so every access holds stateLock; aura calls are
    // made with the lock released (aura scripts may call back into Shaman::).
    struct StoneskinState
    {
        double erosionRemainder = 0.0;  // fractional stacks carried to the next hit (B15)
        uint32 oocGeneration = 0;       // bumped on every arm/cancel; a pending timer with an older value is stale
    };

    std::mutex stateLock;
    std::unordered_map<ObjectGuid, StoneskinState> stoneskinStates;

    bool IsWeapon(Item const* item)
    {
        return item && item->GetTemplate()->Class == ITEM_CLASS_WEAPON;
    }

    void ResetErosionRemainder(ObjectGuid guid)
    {
        std::lock_guard<std::mutex> lock(stateLock);
        auto itr = stoneskinStates.find(guid);
        if (itr != stoneskinStates.end())
            itr->second.erosionRemainder = 0.0;
    }

    // Fraction of damage Stoneskin currently removes: the sum of its MOD_DAMAGE_PERCENT_TAKEN amounts (negative),
    // so a later Mastery scaling of the amount is honoured. Clamped below 1 so the rescale never divides by zero.
    double GetStoneskinReduction(Aura const* aura)
    {
        int32 amount = 0;
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect const* effect = aura->GetEffect(i))
                if (effect->GetAuraType() == SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN)
                    amount += effect->GetAmount();

        return std::clamp(-amount / 100.0, 0.0, 0.99);
    }

    // Starts (or restarts) the 2 min out-of-combat timer. A newer arm, a combat entry or ClearState makes the
    // pending event stale through the generation counter.
    void ArmStoneskinTimer(Player* player)
    {
        ObjectGuid const guid = player->GetGUID();
        uint32 generation;
        {
            std::lock_guard<std::mutex> lock(stateLock);
            generation = ++stoneskinStates[guid].oocGeneration;
        }

        player->m_Events.AddEventAtOffset([guid, generation]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!self || self->IsInCombat())
                return;

            {
                std::lock_guard<std::mutex> lock(stateLock);
                auto itr = stoneskinStates.find(guid);
                if (itr == stoneskinStates.end() || itr->second.oocGeneration != generation)
                    return;

                itr->second.erosionRemainder = 0.0;
            }

            self->RemoveAurasDueToSpell(SPELL_STONESKIN_STACKS, guid);
        }, Milliseconds(ShamanData::STONESKIN_OOC_MS));
    }
}

namespace Shaman
{
    Player* GetOwningPlayer(Unit* unit)
    {
        return unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
    }

    Player const* GetOwningPlayer(Unit const* unit)
    {
        return unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
    }

    bool IsOwnAction(Unit const* shaman, Unit const* actor)
    {
        return shaman && actor == shaman;
    }

    float GetProcChanceMultiplier(Unit const* unit)
    {
        Player const* owner = GetOwningPlayer(unit);
        return owner ? 1.0f + owner->GetProcChancePercentage() / 100.0f : 1.0f;
    }

    bool RollProcChance(Unit const* unit, float baseChancePct)
    {
        return roll_chance_f(baseChancePct * GetProcChanceMultiplier(unit));
    }

    uint32 GetActiveImbue(Unit const* unit)
    {
        if (!unit)
            return 0;

        for (uint32 const spellId : IMBUE_AURAS)
            if (unit->HasAura(spellId))
                return spellId;

        return 0;
    }

    bool HasMaelstromWeaponTalent(Player const* player)
    {
        if (!player)
            return false;

        return std::any_of(MAELSTROM_WEAPON_RANKS.begin(), MAELSTROM_WEAPON_RANKS.end(),
            [player](uint32 spellId) { return player->HasSpell(spellId); });
    }

    uint16 GetImbueGlowEnchant(Player const* player)
    {
        switch (GetActiveImbue(player))
        {
            case ShamanData::SPELL_ROCKBITER_WEAPON:
                return ENCHANT_ROCKBITER;
            case ShamanData::SPELL_FLAMETONGUE_WEAPON:
                return ENCHANT_FLAMETONGUE;
            case ShamanData::SPELL_FROSTBRAND_WEAPON:
                return ENCHANT_FROSTBRAND;
            case ShamanData::SPELL_WINDFURY_WEAPON:
                return ENCHANT_WINDFURY;
            case ShamanData::SPELL_EARTHLIVING_WEAPON:
                return ENCHANT_EARTHLIVING;
            default:
                return 0;
        }
    }

    void WriteImbueGlow(Player* player, uint8 slot)
    {
        if (!player || (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND))
            return;

        if (!IsWeapon(player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot)))
            return;

        uint16 const enchantId = GetImbueGlowEnchant(player);
        if (!enchantId)
            return;

        // Only the temp half of the visible-item enchant field (PlayerStorage.cpp SetVisibleItemSlot): no item or
        // DB change, the item's real enchants stay on it.
        player->SetUInt16Value(PLAYER_VISIBLE_ITEM_1_ENCHANTMENT + (slot * 2), 1, enchantId);
    }

    void ApplyImbueGlow(Player* player)
    {
        if (!player)
            return;

        for (uint8 const slot : GLOW_SLOTS)
            WriteImbueGlow(player, slot);
    }

    void RestoreImbueGlow(Player* player)
    {
        if (!player)
            return;

        // SetVisibleItemSlot rewrites the real values; the visible-slot hook then re-applies the glow of whatever
        // imbue is still up (P0 section 5: the removed aura is already gone when AfterEffectRemove runs).
        for (uint8 const slot : GLOW_SLOTS)
            if (Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot))
                player->SetVisibleItemSlot(slot, item);
    }

    void AddStoneskin(Player* shaman, uint32 stacks)
    {
        if (!shaman || !stacks || !shaman->HasAura(ShamanData::SPELL_ROCKBITER_WEAPON))
            return;

        int32 const cap = ShamanData::STONESKIN_MAX;
        int32 const grant = int32(std::min<uint32>(stacks, uint32(cap)));

        if (Aura* aura = shaman->GetAura(SPELL_STONESKIN_STACKS, shaman->GetGUID()))
        {
            // At the cap the delta is 0, which still refreshes the aura (ModStackAmount's refresh branch).
            int32 const delta = std::max(0, std::min(grant, cap - int32(aura->GetStackAmount())));
            aura->ModStackAmount(delta);
        }
        else
        {
            Aura* created = shaman->AddAura(SPELL_STONESKIN_STACKS, shaman);
            if (!created)
                return;

            ResetErosionRemainder(shaman->GetGUID());

            // A new aura starts at one stack.
            if (grant > 1)
                created->ModStackAmount(grant - 1);
        }

        // Out-of-combat grants start the 2 min timer themselves; in combat it starts on leaving combat.
        if (!shaman->IsInCombat())
            ArmStoneskinTimer(shaman);
    }

    void ErodeStoneskin(Player* victim, uint32 landedDamage)
    {
        if (!victim || !landedDamage)
            return;

        Aura* aura = victim->GetAura(SPELL_STONESKIN_STACKS, victim->GetGUID());
        if (!aura || aura->IsRemoved())
            return;

        uint32 const maxHealth = victim->GetMaxHealth();
        uint8 const stacks = aura->GetStackAmount();
        if (!maxHealth || !stacks)
            return;

        // The hit before Stoneskin's own reduction (after armor, absorbs and every other reduction), as a share
        // of max health, strips the same share of current stacks.
        double const base = double(landedDamage) / (1.0 - GetStoneskinReduction(aura));
        double const lost = double(stacks) * base / double(maxHealth);

        uint32 removed;
        {
            std::lock_guard<std::mutex> lock(stateLock);
            StoneskinState& state = stoneskinStates[victim->GetGUID()];
            double const total = lost + state.erosionRemainder;
            double const whole = std::floor(total);

            if (whole >= double(stacks))
            {
                removed = stacks;
                state.erosionRemainder = 0.0;
            }
            else
            {
                removed = uint32(whole);
                state.erosionRemainder = total - whole;
            }
        }

        // A negative ModStackAmount neither refreshes the duration nor the timers, and removes the aura at 0.
        if (removed)
            aura->ModStackAmount(-int32(removed));
    }

    void OnCombatChange(Player* player, bool inCombat)
    {
        if (!player)
            return;

        if (inCombat)
        {
            // Re-entry cancels a pending timer: its generation no longer matches.
            std::lock_guard<std::mutex> lock(stateLock);
            auto itr = stoneskinStates.find(player->GetGUID());
            if (itr != stoneskinStates.end())
                ++itr->second.oocGeneration;

            return;
        }

        if (player->HasAura(SPELL_STONESKIN_STACKS, player->GetGUID()))
            ArmStoneskinTimer(player);
    }

    void RefreshAttunements(Player* player)
    {
        if (!player)
            return;

        ObjectGuid const casterGuid = player->GetGUID();

        // (unit, spell id, owned by the shaman). Auras are re-fetched before each recalculation, so one recalc
        // removing another aura cannot leave a dangling pointer behind.
        struct Target
        {
            Unit* unit;
            uint32 spellId;
            bool owned;
        };

        std::vector<Target> targets;

        // The shaman's own copies: parents (area auras, owned by the caster; their effects are shared by every
        // application, so one recalculation updates every raid member) and children it owns.
        for (uint32 const spellId : ATTUNEMENT_PARENTS)
            if (player->GetOwnedAura(spellId, casterGuid))
                targets.push_back({ player, spellId, true });

        for (uint32 const spellId : ATTUNEMENT_CHILDREN)
            if (player->GetOwnedAura(spellId, casterGuid))
                targets.push_back({ player, spellId, true });

        // Children this shaman cast onto the parent's other targets (owned by each target, caster = the shaman).
        for (uint32 const parentId : ATTUNEMENT_PARENTS)
        {
            Aura* parent = player->GetOwnedAura(parentId, casterGuid);
            if (!parent)
                continue;

            for (auto const& [targetGuid, application] : parent->GetApplicationMap())
            {
                Unit* target = application->GetTarget();
                if (!target || target == player)
                    continue;

                for (uint32 const childId : ATTUNEMENT_CHILDREN)
                    if (Aura* child = target->GetAura(childId, casterGuid))
                        if (child->GetOwner() != player)
                            targets.push_back({ target, childId, false });
            }
        }

        for (Target const& entry : targets)
        {
            Aura* aura = entry.owned ? entry.unit->GetOwnedAura(entry.spellId, casterGuid)
                : entry.unit->GetAura(entry.spellId, casterGuid);
            if (aura && !aura->IsRemoved())
                aura->RecalculateAmountOfEffects();
        }
    }

    void EnsureReincarnationAura(Player* player)
    {
        if (!player || !player->HasSpell(ShamanData::SPELL_REINCARNATION) ||
            player->HasAura(SPELL_GLYPH_OF_RENEWED_LIFE))
            return;

        // 58059 is passive and hidden (Attributes 0xC0), so addSpell applies the aura and nothing shows in the
        // spellbook (Hunter::EnsureNoAmmoAura shape).
        if (!player->HasSpell(SPELL_GLYPH_OF_RENEWED_LIFE))
            player->addSpell(SPELL_GLYPH_OF_RENEWED_LIFE, SPEC_MASK_ALL, true);
        else
            player->CastSpell(player, SPELL_GLYPH_OF_RENEWED_LIFE, true);
    }

    void ClearState(Player* player)
    {
        // Later sections add their Clear* calls here; removal paths use find-only map access.
        if (!player)
            return;

        std::lock_guard<std::mutex> lock(stateLock);
        auto itr = stoneskinStates.find(player->GetGUID());
        if (itr != stoneskinStates.end())
            stoneskinStates.erase(itr);
    }
}
