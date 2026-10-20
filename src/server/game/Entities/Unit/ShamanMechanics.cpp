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
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TemporarySummon.h"
#include "Totem.h"
#include "TotemPackets.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <list>
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
        // Later sections add their Clear* calls here; removal paths use find-only map access. The SH0b and S1 blocks
        // keep no per-player state (Elemental buffs left by a logout are reconciled on the next map entry).
        if (!player)
            return;

        std::lock_guard<std::mutex> lock(stateLock);
        auto itr = stoneskinStates.find(player->GetGUID());
        if (itr != stoneskinStates.end())
            stoneskinStates.erase(itr);
    }
}

/*
 * SH0b block: the four elementals. Shared lockout (CORE-AUDIT-A A14, P0 spike shape), elemental death empties its
 * totem slot (A5 step 2) and the owner-stat aura (H1). No per-player state.
 */
namespace
{
    constexpr uint32 SPELL_WATER_ELEMENTAL_SUMMON = ShamanData::SPELL_WATER_ELEMENTAL_TOTEM;
    constexpr uint32 SPELL_STORM_ELEMENTAL_SUMMON = ShamanData::SPELL_STORM_ELEMENTAL_TOTEM;
    constexpr uint32 SPELL_ELEMENTAL_STATS = ShamanData::SPELL_ELEMENTAL_OWNER_STATS;
    constexpr uint32 LOCKOUT_BASE_MS = ShamanData::ELEMENTAL_LOCKOUT_MS;

    // Stock guardians (entries hard-coded in Pet.cpp) and the new ones.
    constexpr uint32 NPC_GREATER_EARTH_ELEMENTAL = ShamanData::NPC_GREATER_EARTH_ELEMENTAL;
    constexpr uint32 NPC_GREATER_FIRE_ELEMENTAL = ShamanData::NPC_GREATER_FIRE_ELEMENTAL;
    constexpr uint32 NPC_WATER_ELEMENTAL = ShamanData::NPC_WATER_ELEMENTAL_GUARDIAN;
    constexpr uint32 NPC_STORM_ELEMENTAL = ShamanData::NPC_STORM_ELEMENTAL_GUARDIAN;

    // The player-side elemental totems (the stock 15430/15439 stay with NPC casters).
    constexpr uint32 NPC_EARTH_ELEMENTAL_TOTEM = ShamanData::NPC_EARTH_ELEMENTAL_TOTEM;
    constexpr uint32 NPC_FIRE_ELEMENTAL_TOTEM = ShamanData::NPC_FIRE_ELEMENTAL_TOTEM;
    constexpr uint32 NPC_WATER_ELEMENTAL_TOTEM = ShamanData::NPC_WATER_ELEMENTAL_TOTEM;
    constexpr uint32 NPC_STORM_ELEMENTAL_TOTEM = ShamanData::NPC_STORM_ELEMENTAL_TOTEM;

    struct ElementalInfo
    {
        uint32 summonSpellId;
        uint32 guardianEntry;
        uint32 totemEntry;
        uint8 slot;
    };

    constexpr std::array<ElementalInfo, 4> ELEMENTALS =
    {{
        { ShamanData::SPELL_EARTH_ELEMENTAL_TOTEM, NPC_GREATER_EARTH_ELEMENTAL, NPC_EARTH_ELEMENTAL_TOTEM,
            SUMMON_SLOT_TOTEM_EARTH },
        { ShamanData::SPELL_FIRE_ELEMENTAL_TOTEM, NPC_GREATER_FIRE_ELEMENTAL, NPC_FIRE_ELEMENTAL_TOTEM,
            SUMMON_SLOT_TOTEM_FIRE },
        { SPELL_WATER_ELEMENTAL_SUMMON, NPC_WATER_ELEMENTAL, NPC_WATER_ELEMENTAL_TOTEM, SUMMON_SLOT_TOTEM_WATER },
        { SPELL_STORM_ELEMENTAL_SUMMON, NPC_STORM_ELEMENTAL, NPC_STORM_ELEMENTAL_TOTEM, SUMMON_SLOT_TOTEM_AIR }
    }};

    ElementalInfo const* FindElementalByGuardian(uint32 guardianEntry)
    {
        for (ElementalInfo const& info : ELEMENTALS)
            if (info.guardianEntry == guardianEntry)
                return &info;

        return nullptr;
    }

    // The owner's spell power for the schools in `schoolMask` (0 = every magic school): the best single school in the
    // mask. A guardian passes its bolt's own school, so a school-only bonus (+40 Fire Spell Damage) counts for that
    // school's bolt and never for another guardian's.
    int32 GetOwnerSpellDamage(Player* owner, uint32 schoolMask)
    {
        if (!schoolMask)
            schoolMask = SPELL_SCHOOL_MASK_MAGIC;

        int32 best = 0;
        for (uint8 school = SPELL_SCHOOL_HOLY; school < MAX_SPELL_SCHOOL; ++school)
            if (schoolMask & (1 << school))
                best = std::max(best, owner->SpellBaseDamageBonusDone(SpellSchoolMask(1 << school)));

        return best;
    }

    // The school of the guardian's bolt (read from the bolt spell, so it follows the DSL): Frost for the Water
    // Elemental, Nature for the Storm Elemental. 0 for any other creature.
    uint32 GetElementalBoltSchoolMask(uint32 guardianEntry)
    {
        uint32 boltSpellId;
        switch (guardianEntry)
        {
            case NPC_WATER_ELEMENTAL:
                boltSpellId = ShamanData::SPELL_WATER_BOLT;
                break;
            case NPC_STORM_ELEMENTAL:
                boltSpellId = ShamanData::SPELL_STORM_BOLT;
                break;
            default:
                return 0;
        }

        SpellInfo const* boltInfo = sSpellMgr->GetSpellInfo(boltSpellId);
        return boltInfo ? boltInfo->GetSchoolMask() : 0;
    }

    int32 GetOwnerSpellHealing(Player* owner, uint32 schoolMask)
    {
        if (!schoolMask)
            schoolMask = SPELL_SCHOOL_MASK_ALL;

        return std::max(0, owner->SpellBaseHealingBonusDone(SpellSchoolMask(schoolMask)));
    }
}

namespace Shaman
{
    uint32 GetElementalLockoutBaseMs(Player const* player)
    {
        // Elemental's Conduit of the Elements (S1): the shorter lockout. The elementals' own 2 min stay.
        if (GetTalentRank(player, { ShamanData::SPELL_CONDUIT_OF_THE_ELEMENTS }))
            return uint32(ShamanData::CONDUIT_LOCKOUT_MS);

        return LOCKOUT_BASE_MS;
    }

    bool IsElementalSummonSpell(uint32 spellId)
    {
        return std::any_of(ELEMENTALS.begin(), ELEMENTALS.end(),
            [spellId](ElementalInfo const& info) { return info.summonSpellId == spellId; });
    }

    void ApplyElementalLockout(Player* player, uint32 castSpellId)
    {
        if (!player || !IsElementalSummonSpell(castSpellId))
            return;

        float const cooldownHastePct = std::max(0.0f, player->GetCooldownHastePercentage());
        uint32 const lockMs = uint32(float(GetElementalLockoutBaseMs(player)) / (1.0f + cooldownHastePct / 100.0f));
        if (!lockMs)
            return;

        // One tick later, after SMSG_SPELL_GO and the cast spell's own Cooldown Haste correction (P0 spike,
        // spell_pal_aura_press::FireBurst). The cast spell's own button, and so its GCD sweep, is never touched.
        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid, castSpellId, lockMs]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!self)
                return;

            for (ElementalInfo const& info : ELEMENTALS)
            {
                // Never shorten a longer cooldown (the other elemental's own 2 min, or a longer lockout).
                if (info.summonSpellId == castSpellId || self->GetSpellCooldownDelay(info.summonSpellId) >= lockMs)
                    continue;

                // End = now + lockMs. The send flag keeps the entry in the login packet and the save (m1).
                self->AddSpellCooldown(info.summonSpellId, 0, lockMs, true);
                self->ResendSpellCooldown(info.summonSpellId);         // clear-then-set, so the button greys
            }
        }, 1ms);
    }

    void OnElementalDied(Creature* guardian)
    {
        if (!guardian)
            return;

        ElementalInfo const* info = FindElementalByGuardian(guardian->GetEntry());
        if (!info)
            return;

        // SummonGuardian remaps a totem caster to its owner, so the guardian's owner is the slot holder.
        Unit* owner = guardian->GetOwner();
        if (!owner)
            return;

        ObjectGuid const slotGuid = owner->m_SummonSlot[info->slot];
        if (slotGuid.IsEmpty())
            return;

        Creature* occupant = ObjectAccessor::GetCreature(*guardian, slotGuid);
        if (!occupant || occupant->GetEntry() != info->totemEntry)
            return;

        // Totem::UnSummon clears the slot and defers the removal (AddObjectToRemoveList), so it is safe inside the
        // guardian's JustDied.
        if (Totem* totem = occupant->ToTotem())
            totem->UnSummon();
    }

    void RefreshElementalAuras(Player* owner, Unit* guardian)
    {
        if (!owner || !guardian || !guardian->IsAlive())
            return;

        Aura* aura = guardian->GetAura(SPELL_ELEMENTAL_STATS);
        if (!aura)
            aura = guardian->AddAura(SPELL_ELEMENTAL_STATS, guardian);

        if (!aura || aura->IsRemoved())
        {
            LOG_ERROR("scripts.spells", "Shaman::RefreshElementalAuras: could not apply aura {} to {} (owner {})",
                SPELL_ELEMENTAL_STATS, guardian->GetGUID().ToString(), owner->GetGUID().ToString());
            return;
        }

        // The aura's damage effect covers every magic school (one spell row serves both guardians), so the amount is
        // taken from the guardian's own bolt school: the other schools stay unused by that guardian.
        uint32 const boltSchoolMask = GetElementalBoltSchoolMask(guardian->GetEntry());

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (!effect)
                continue;

            int32 amount;
            switch (effect->GetAuraType())
            {
                case SPELL_AURA_MOD_DAMAGE_DONE:
                    amount = GetOwnerSpellDamage(owner,
                        boltSchoolMask ? boltSchoolMask : uint32(effect->GetMiscValue()));
                    break;
                case SPELL_AURA_MOD_HEALING_DONE:
                    amount = GetOwnerSpellHealing(owner, uint32(effect->GetMiscValue()));
                    break;
                default:
                    continue;
            }

            if (effect->GetAmount() != amount)
                effect->ChangeAmount(amount);
        }
    }
}

/*
 * S1 block: Elemental (docs/reworks/shaman-elemental-rework.md). Talent ranks, the active elementals, Power of the
 * Elements' Empowerment buffs and guardian auras, Gathering Flames clearing, the Elemental Warding capstone, the
 * Conduit of the Elements Mastery amount, Echo, the Call of the Elements extension, the Thunderstorm stun rank and the
 * Lava Flows haste map. No per-player state: everything is reconciled from the shaman's own auras, talents and slots.
 */
namespace
{
    struct EmpowermentBuff
    {
        uint8 elementalBit;
        uint32 spellId;
    };

    constexpr std::array<EmpowermentBuff, 4> EMPOWERMENT_BUFFS =
    {{
        { Shaman::ELEMENTAL_MASK_EARTH, ShamanData::SPELL_EMPOWERMENT_EARTH },
        { Shaman::ELEMENTAL_MASK_FIRE, ShamanData::SPELL_EMPOWERMENT_FIRE },
        { Shaman::ELEMENTAL_MASK_WATER, ShamanData::SPELL_EMPOWERMENT_WATER },
        { Shaman::ELEMENTAL_MASK_STORM, ShamanData::SPELL_EMPOWERMENT_STORM }
    }};

    constexpr std::array<uint32, 3> OVERLOAD_COPIES =
    {
        ShamanData::SPELL_LIGHTNING_BOLT_OVERLOAD,
        ShamanData::SPELL_CHAIN_LIGHTNING_OVERLOAD,
        ShamanData::SPELL_LAVA_BURST_OVERLOAD
    };

    constexpr std::array<uint32, 3> ELEMENTAL_WARDING_RANKS =
    {
        ShamanData::SPELL_ELEMENTAL_WARDING,
        ShamanData::SPELL_ELEMENTAL_WARDING_28997,
        ShamanData::SPELL_ELEMENTAL_WARDING_28998
    };

    constexpr std::array<uint32, 3> CALL_OF_THUNDER_RANKS =
    {
        ShamanData::SPELL_CALL_OF_THUNDER,
        ShamanData::SPELL_CALL_OF_THUNDER_RANK2,
        ShamanData::SPELL_CALL_OF_THUNDER_RANK3
    };

    constexpr uint8 ELEMENTAL_WARDING_CAPSTONE_RANK = 3;
    constexpr uint8 CALL_OF_THUNDER_CAPSTONE_RANK = 3;

    uint8 GetElementalBit(ElementalInfo const& info)
    {
        switch (info.totemEntry)
        {
            case NPC_EARTH_ELEMENTAL_TOTEM:
                return Shaman::ELEMENTAL_MASK_EARTH;
            case NPC_FIRE_ELEMENTAL_TOTEM:
                return Shaman::ELEMENTAL_MASK_FIRE;
            case NPC_WATER_ELEMENTAL_TOTEM:
                return Shaman::ELEMENTAL_MASK_WATER;
            case NPC_STORM_ELEMENTAL_TOTEM:
                return Shaman::ELEMENTAL_MASK_STORM;
            default:
                return 0;
        }
    }

    // The player's elemental totem in `info`'s slot, or nullptr (empty slot, another totem, despawning).
    Creature* GetElementalTotem(Player const* player, ElementalInfo const& info)
    {
        ObjectGuid const guid = player->m_SummonSlot[info.slot];
        if (guid.IsEmpty())
            return nullptr;

        Creature* creature = ObjectAccessor::GetCreature(*player, guid);
        if (!creature || creature->GetEntry() != info.totemEntry || !creature->IsTotem() || !creature->IsInWorld() ||
            !creature->IsAlive())
            return nullptr;

        return creature;
    }

    bool IsUsablePlayer(Player const* player)
    {
        return player && player->IsInWorld() && !player->IsDuringRemoveFromWorld();
    }

    // A self-cast aura kept on or off: added by the player when wanted and missing, removed (this caster's only)
    // when not wanted. `target` is the player itself or one of its guardians (owner-cast aura, L5).
    void SetOwnerAura(Player* owner, Unit* target, uint32 spellId, bool wanted)
    {
        ObjectGuid const ownerGuid = owner->GetGUID();
        if (!wanted)
        {
            target->RemoveAurasDueToSpell(spellId, ownerGuid);
            return;
        }

        if (target->HasAura(spellId, ownerGuid))
            return;

        if (!owner->AddAura(spellId, target))
            LOG_ERROR("scripts.spells", "Shaman S1: could not apply aura {} to {} (owner {})", spellId,
                target->GetGUID().ToString(), ownerGuid.ToString());
    }

    // Empowerment: EMPOWERMENT_PCT, plus the live Mastery with Conduit of the Elements' capstone (rounded). Scripts
    // pass live values (SKILL "Sign convention").
    int32 GetEmpowermentAmount(Player const* player)
    {
        int32 amount = int32(ShamanData::EMPOWERMENT_PCT);
        if (Shaman::GetTalentRank(player, { ShamanData::SPELL_CONDUIT_OF_THE_ELEMENTS }))
            amount += std::max<int32>(0, int32(std::lround(player->GetMasteryPercentage())));

        return amount;
    }

    // The damage effects of an Empowerment aura (player side: SPELLMOD_DAMAGE / SPELLMOD_DOT percent modifiers;
    // guardian side: MOD_DAMAGE_PERCENT_DONE) take `amount`; other effects (the Storm buff's jump modifier) are left
    // alone. Changing a spell mod re-sends it to the client, so only a moved value is written.
    void SetEmpowermentAmount(Aura* aura, int32 amount)
    {
        if (!aura || aura->IsRemoved())
            return;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (!effect)
                continue;

            bool isDamage = false;
            switch (effect->GetAuraType())
            {
                case SPELL_AURA_ADD_PCT_MODIFIER:
                    isDamage = effect->GetMiscValue() == int32(SPELLMOD_DAMAGE) ||
                        effect->GetMiscValue() == int32(SPELLMOD_DOT);
                    break;
                case SPELL_AURA_MOD_DAMAGE_PERCENT_DONE:
                    isDamage = true;
                    break;
                default:
                    break;
            }

            if (isDamage && effect->GetAmount() != amount)
                effect->ChangeAmount(amount, false);
        }
    }

    // Guardian auras added by the owner (L5): the guardian-side Empowerment on every elemental and the Water
    // Elemental's bonus damage and the Earth Elemental's no-threat aura (Power of the Elements); the Earth Elemental's
    // bonus damage (Elemental Warding capstone).
    void SyncGuardianAuras(Player* player)
    {
        bool const powerOfTheElements = Shaman::GetTalentRank(player,
            { ShamanData::SPELL_POWER_OF_THE_ELEMENTS }) > 0;
        bool const wardingCapstone = Shaman::GetTalentRank(player, ELEMENTAL_WARDING_RANKS) >=
            ELEMENTAL_WARDING_CAPSTONE_RANK;
        int32 const amount = GetEmpowermentAmount(player);

        for (ElementalInfo const& info : ELEMENTALS)
        {
            std::list<Creature*> guardians;
            player->GetAllMinionsByEntry(guardians, info.guardianEntry);
            for (Creature* guardian : guardians)
            {
                if (!guardian || !guardian->IsInWorld() || !guardian->IsAlive())
                    continue;

                SetOwnerAura(player, guardian, ShamanData::SPELL_ELEMENTAL_EMPOWERED, powerOfTheElements);
                if (powerOfTheElements)
                    SetEmpowermentAmount(guardian->GetAura(ShamanData::SPELL_ELEMENTAL_EMPOWERED, player->GetGUID()),
                        amount);

                if (info.guardianEntry == NPC_WATER_ELEMENTAL)
                    SetOwnerAura(player, guardian, ShamanData::SPELL_WATER_ELEMENTAL_DAMAGE, powerOfTheElements);
                else if (info.guardianEntry == NPC_GREATER_EARTH_ELEMENTAL)
                {
                    SetOwnerAura(player, guardian, ShamanData::SPELL_EARTH_ELEMENTAL_NO_THREAT, powerOfTheElements);
                    SetOwnerAura(player, guardian, ShamanData::SPELL_EARTH_ELEMENTAL_DAMAGE, wardingCapstone);
                }
            }
        }
    }

    // Player-side state against the slots: Empowerment buffs (Power of the Elements), Gathering Flames (cleared
    // whenever no Fire Elemental is active, so an extension never clears it and any removal path does), the
    // Elemental Warding capstone health aura, then the live Empowerment amount.
    void SyncElementalState(Player* player)
    {
        uint8 const active = Shaman::GetActiveElementals(player);
        bool const powerOfTheElements = Shaman::GetTalentRank(player,
            { ShamanData::SPELL_POWER_OF_THE_ELEMENTS }) > 0;
        bool const wardingCapstone = Shaman::GetTalentRank(player, ELEMENTAL_WARDING_RANKS) >=
            ELEMENTAL_WARDING_CAPSTONE_RANK;

        for (EmpowermentBuff const& buff : EMPOWERMENT_BUFFS)
            SetOwnerAura(player, player, buff.spellId, powerOfTheElements && (active & buff.elementalBit));

        if (!(active & Shaman::ELEMENTAL_MASK_FIRE))
            player->RemoveAurasDueToSpell(ShamanData::SPELL_GATHERING_FLAMES);

        SetOwnerAura(player, player, ShamanData::SPELL_WARDING_HEALTH,
            wardingCapstone && (active & Shaman::ELEMENTAL_MASK_EARTH));

        Shaman::RefreshEmpowerment(player);
    }

    // SMSG_TOTEM_CREATED for an extended totem (same fields as Totem::InitStats). P0 2d: a plain re-send retimes the
    // bar text but not the swipe, so the slot is first cleared (empty GUID, 0 duration) and then re-sent.
    void SendTotemTimer(Player* player, Totem* totem, uint8 slot, uint32 duration)
    {
        uint8 const barSlot = uint8(slot - SUMMON_SLOT_TOTEM_FIRE);

        WorldPackets::Totem::TotemCreated clear;
        clear.Slot = barSlot;
        player->SendDirectMessage(clear.Write());

        WorldPackets::Totem::TotemCreated data;
        data.Totem = totem->GetGUID();
        data.Slot = barSlot;
        data.Duration = duration;
        data.SpellID = totem->GetUInt32Value(UNIT_CREATED_BY_SPELL);
        player->SendDirectMessage(data.Write());
    }
}

namespace Shaman
{
    uint8 GetTalentRank(Player const* player, std::span<uint32 const> rankIds)
    {
        if (!player)
            return 0;

        uint8 const spec = player->GetActiveSpec();
        for (size_t i = rankIds.size(); i > 0; --i)
        {
            uint32 const spellId = rankIds[i - 1];
            if (spellId && (player->HasTalent(spellId, spec) || player->HasAura(spellId)))
                return uint8(i);
        }

        return 0;
    }

    uint8 GetTalentRank(Player const* player, std::initializer_list<uint32> rankIds)
    {
        return GetTalentRank(player, std::span<uint32 const>(rankIds.begin(), rankIds.size()));
    }

    uint8 GetActiveElementals(Player const* player)
    {
        if (!player)
            return 0;

        uint8 mask = 0;
        for (ElementalInfo const& info : ELEMENTALS)
            if (GetElementalTotem(player, info))
                mask |= GetElementalBit(info);

        return mask;
    }

    void OnElementalAdded(Player* player, Creature* totem)
    {
        // The slot already holds the new totem (TempSummon::InitStats runs before AddToMap), so the reconcile reads
        // it; the totem pointer only tells a real Earth Elemental summon from a plain reconcile (nullptr).
        if (!IsUsablePlayer(player))
            return;

        SyncElementalState(player);

        // Booming Echoes capstone: every Earth Elemental summon (Call of the Elements' included) grants Echoes,
        // capped at ECHO_MAX by AddEcho (2026-10-20 Earth Shock burst).
        if (totem && totem->GetEntry() == NPC_EARTH_ELEMENTAL_TOTEM &&
            Shaman::GetTalentRank(player, { ShamanData::SPELL_BOOMING_ECHOES_RANK3 }) > 0)
            Shaman::AddEcho(player, uint8(ShamanData::ECHO_EARTH_ELEMENTAL_GRANT));

        // The totem's passive summons the guardian in Totem::InitSummon, after the add hook: add its auras one tick
        // later (the ApplyElementalLockout shape).
        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!IsUsablePlayer(self))
                return;

            SyncGuardianAuras(self);
        }, 1ms);
    }

    void OnElementalRemoved(Player* player, uint32 /*totemEntry*/)
    {
        // Totem::UnSummon and TempSummon::RemoveFromWorld clear the slot before the remove hook, and a replacing
        // totem already holds it: reading the slots is right for death, expiry, dismissal, Recall and replacement.
        // A Call of the Elements extension removes nothing, so Gathering Flames survives it.
        if (!IsUsablePlayer(player))
            return;

        SyncElementalState(player);
    }

    void RefreshEmpowerment(Player* player)
    {
        if (!player)
            return;

        int32 const amount = GetEmpowermentAmount(player);
        ObjectGuid const guid = player->GetGUID();

        for (EmpowermentBuff const& buff : EMPOWERMENT_BUFFS)
            SetEmpowermentAmount(player->GetAura(buff.spellId, guid), amount);

        for (ElementalInfo const& info : ELEMENTALS)
        {
            std::list<Creature*> guardians;
            player->GetAllMinionsByEntry(guardians, info.guardianEntry);
            for (Creature* guardian : guardians)
                if (guardian && guardian->IsInWorld())
                    SetEmpowermentAmount(guardian->GetAura(ShamanData::SPELL_ELEMENTAL_EMPOWERED, guid), amount);
        }
    }

    bool IsOverloadCopy(uint32 spellId)
    {
        return std::find(OVERLOAD_COPIES.begin(), OVERLOAD_COPIES.end(), spellId) != OVERLOAD_COPIES.end();
    }

    void AddEcho(Player* player, uint8 stacks)
    {
        if (!player || !stacks)
            return;

        int32 const cap = int32(ShamanData::ECHO_MAX);
        int32 const grant = std::min<int32>(stacks, cap);

        Aura* aura = player->GetAura(ShamanData::SPELL_BOOMING_ECHO, player->GetGUID());
        if (aura)
        {
            // At the cap the delta is 0, which still refreshes the aura (ModStackAmount's refresh branch).
            int32 const delta = std::max(0, std::min(grant, cap - int32(aura->GetStackAmount())));
            aura->ModStackAmount(delta);
        }
        else
        {
            aura = player->AddAura(ShamanData::SPELL_BOOMING_ECHO, player);
            if (!aura)
            {
                LOG_ERROR("scripts.spells", "Shaman::AddEcho: could not apply aura {} to {}",
                    ShamanData::SPELL_BOOMING_ECHO, player->GetGUID().ToString());
                return;
            }

            // A new aura starts at one stack.
            if (grant > 1)
                aura->ModStackAmount(grant - 1);
        }

        if (aura->IsRemoved())
            return;

        // The const is the source of truth for the window, whatever the row's duration says.
        int32 const duration = int32(ShamanData::ECHO_DURATION_MS);
        if (aura->GetMaxDuration() != duration)
            aura->SetMaxDuration(duration);

        aura->SetDuration(duration);
    }

    void ExtendElementals(Player* player, uint32 ms)
    {
        if (!player || !ms)
            return;

        for (ElementalInfo const& info : ELEMENTALS)
        {
            Creature* creature = GetElementalTotem(player, info);
            Totem* totem = creature ? creature->ToTotem() : nullptr;
            if (!totem)
                continue;

            uint32 const remaining = totem->GetTotemDuration() + ms;
            totem->SetTotemDuration(remaining);
            SendTotemTimer(player, totem, info.slot, remaining);

            // The guardian keeps its own summon timer (P0 2d): raise it when shorter, so it outlives nothing it
            // should not (the totem leaving the world still takes it).
            std::list<Creature*> guardians;
            player->GetAllMinionsByEntry(guardians, info.guardianEntry);
            for (Creature* guardian : guardians)
                if (TempSummon* summon = guardian ? guardian->ToTempSummon() : nullptr)
                    if (summon->GetTimer() < remaining)
                        summon->SetTimer(remaining);
        }
    }

    void SyncThunderstormRank(Player* player)
    {
        if (!player)
            return;

        // Thunderstorm is a talent rank put in the spellbook: the talent in the active spec, or the spell itself
        // (learned by a command).
        bool const knowsThunderstorm = GetTalentRank(player, { ShamanData::SPELL_THUNDERSTORM }) > 0 ||
            player->HasSpell(ShamanData::SPELL_THUNDERSTORM);
        bool const wanted = knowsThunderstorm &&
            GetTalentRank(player, CALL_OF_THUNDER_RANKS) >= CALL_OF_THUNDER_CAPSTONE_RANK;
        bool const known = player->HasSpell(ShamanData::SPELL_THUNDERSTORM_RANK2);

        // Rank 2 is no talent: learnSpell gives it every spec, and a spec swap re-runs this sync.
        if (wanted && !known)
            player->learnSpell(ShamanData::SPELL_THUNDERSTORM_RANK2);
        else if (!wanted && known)
            player->removeSpell(ShamanData::SPELL_THUNDERSTORM_RANK2, SPEC_MASK_ALL, false);
    }

    uint32 LavaFlowsHasteSpell(uint8 rank)
    {
        switch (rank)
        {
            case 1:
                return ShamanData::SPELL_LAVA_FLOWS_HASTE;
            case 2:
                return ShamanData::SPELL_LAVA_FLOWS_HASTE_65263;
            case 3:
                return ShamanData::SPELL_LAVA_FLOWS_HASTE_65264;
            default:
                return 0;
        }
    }
}
