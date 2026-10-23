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
#include "Creature.h"
#include "DataMap.h"
#include "GameTime.h"
#include "HealMechanics.h"
#include "Item.h"
#include "ItemTemplate.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "Spell.h"
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

    // Maelstrom Weapon talent ranks (S3: three ranks, 51531/51532 dropped from the talent).
    constexpr std::array<uint32, 3> MAELSTROM_WEAPON_RANKS =
    {
        ShamanData::SPELL_MAELSTROM_WEAPON,
        ShamanData::SPELL_MAELSTROM_WEAPON_51529,
        ShamanData::SPELL_MAELSTROM_WEAPON_51530
    };

    // S3 Toughness talent ranks and the rank whose capstone slows Stoneskin erosion.
    constexpr std::array<uint32, 3> TOUGHNESS_RANKS =
    {
        ShamanData::SPELL_TOUGHNESS,
        ShamanData::SPELL_TOUGHNESS_16306,
        ShamanData::SPELL_TOUGHNESS_16307
    };
    constexpr uint8 TOUGHNESS_CAPSTONE_RANK = 3;

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

    // S2: drops the Restoration state (defined in the S2 block); called by Shaman::ClearState.
    void ClearRestorationState(Player* player);

    // S3 (defined in the S3 block): writes the Mastery-scaled Stoneskin amount after a stack change; drops the
    // Enhancement state (ClearState); Earth's Grasp absorb percent; drops the Enhancement auras before the logout save.
    void RefreshStoneskinAmount(Player* player);
    void ClearEnhancementState(Player* player);
    float GetEarthsGraspAbsorbPct(Player const* player);
    void DropEnhancementAuras(Player* player);
    void ApplyGuardianTotemsCapstone(Player* player, Creature* totem);
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

        // L-8 / NOTES 8.2 item 14: the talent in the active spec (or its passive aura), never HasSpell.
        return GetTalentRank(player, MAELSTROM_WEAPON_RANKS) > 0;
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

        // S3: every stack change recalculates the amount as per-stack x stacks; put the Mastery scaling back.
        RefreshStoneskinAmount(shaman);

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

        // S3 Earthen Ascendance: "your Stoneskin does not erode".
        if (Shaman::IsEarthenAscendant(victim))
            return;

        uint32 const maxHealth = victim->GetMaxHealth();
        uint8 const stacks = aura->GetStackAmount();
        if (!maxHealth || !stacks)
            return;

        // The hit before Stoneskin's own reduction (after armor, absorbs and every other reduction), as a share
        // of max health, strips the same share of current stacks.
        double const base = double(landedDamage) / (1.0 - GetStoneskinReduction(aura));
        double lost = double(stacks) * base / double(maxHealth);

        // S3 Toughness capstone: below TOUGHNESS_THRESHOLD_PCT health each hit strips TOUGHNESS_ERODE_PCT fewer stacks.
        // The hook runs before the hit leaves health, so this is the health the hit lands on.
        if (Shaman::GetTalentRank(victim, TOUGHNESS_RANKS) >= TOUGHNESS_CAPSTONE_RANK &&
            victim->GetHealthPct() < float(ShamanData::TOUGHNESS_THRESHOLD_PCT))
            lost *= 1.0 - double(ShamanData::TOUGHNESS_ERODE_PCT) / 100.0;

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
        if (removed && !aura->ModStackAmount(-int32(removed)))
            RefreshStoneskinAmount(victim);
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

        // S2: the Cloudburst store and the Improved Chain Heal count (player CustomData, no lock needed).
        ClearRestorationState(player);

        // S3: the swap stash, the banked charges and the out-of-combat timer generations (player CustomData).
        ClearEnhancementState(player);

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

/*
 * S2 block: Restoration (docs/reworks/shaman-restoration-rework.md). Totemic Resonance (counted totems and the live
 * Mastery part), the Totemic Focus placement heal, the Earthen Wall absorb, Tidal Waves charges with the Improved Chain
 * Heal count, Cloudburst (store, release, cooldown) and the Tidal Force extension. The Cloudburst store and the
 * Improved Chain Heal count live in the player's CustomData (one map thread; ClearState drops them); everything else is
 * read from the shaman's own talents, auras and slots.
 */
namespace
{
    // The stock Healing Stream Totem creature: 5394's summon (shaman_spells.py), not declared in the DSL.
    constexpr uint32 NPC_HEALING_STREAM_TOTEM = 3527;

    constexpr std::array<uint32, 3> TOTEMIC_FOCUS_RANKS =
    {
        ShamanData::SPELL_TOTEMIC_FOCUS,
        ShamanData::SPELL_TOTEMIC_FOCUS_16222,
        ShamanData::SPELL_TOTEMIC_FOCUS_16223
    };

    constexpr std::array<uint32, 2> IMPROVED_CHAIN_HEAL_RANKS =
    {
        ShamanData::SPELL_IMPROVED_CHAIN_HEAL,
        ShamanData::SPELL_IMPROVED_CHAIN_HEAL_30873
    };

    constexpr uint8 TOTEMIC_FOCUS_CAPSTONE_RANK = 3;
    constexpr uint8 IMPROVED_CHAIN_HEAL_CAPSTONE_RANK = 2;

    // The Cloudburst release splits among every injured player in range: a full raid (MAXRAIDSIZE).
    constexpr uint8 CLOUDBURST_MAX_TARGETS = 40;

    struct RestorationState : DataMap::Base
    {
        bool cloudburstActive = false;   // a Cloudburst placed by this player is recorded and not yet released
        ObjectGuid cloudburstTotem;      // that totem
        uint32 cloudburstPlacedMs = 0;   // GameTime ms of its placement (the cooldown runs from here)
        double cloudburstStored = 0.0;   // already scaled by CLOUDBURST_STORE_PCT
        uint8 chainHealCount = 0;        // Tidal Waves charges consumed toward the Improved Chain Heal buff
    };

    constexpr char const* RESTORATION_STATE_KEY = "shaman_restoration_state";

    RestorationState* GetRestorationState(Player* player)
    {
        return player->CustomData.GetDefault<RestorationState>(RESTORATION_STATE_KEY);
    }

    RestorationState* FindRestorationState(Player const* player)
    {
        return player->CustomData.Get<RestorationState>(RESTORATION_STATE_KEY);
    }

    uint32 NowMs()
    {
        return uint32(GameTime::GetGameTimeMS().count());
    }

    void LogRestoCastFailure(char const* what, uint32 spellId, Unit const* caster, Unit const* target,
        SpellCastResult result)
    {
        if (result == SPELL_CAST_OK || result == SPELL_FAILED_LINE_OF_SIGHT)
            return;

        LOG_ERROR("scripts.spells", "Shaman S2 {}: cast of {} by {} at {} failed (result {})", what, spellId,
            caster ? caster->GetGUID().ToString() : "none", target ? target->GetGUID().ToString() : "none",
            uint32(result));
    }

    // The player's living totem in `slot` (SUMMON_SLOT_TOTEM_*), or nullptr.
    Creature* GetSlotTotem(Player const* player, uint8 slot)
    {
        ObjectGuid const guid = player->m_SummonSlot[slot];
        if (guid.IsEmpty())
            return nullptr;

        Creature* creature = ObjectAccessor::GetCreature(*player, guid);
        if (!creature || !creature->IsTotem() || !creature->IsInWorld() || !creature->IsAlive())
            return nullptr;

        return creature;
    }

    // Totemic Focus capstone: 1 ms after the placement (the totem is in the grid by then), the totem heals up to
    // TOTEMIC_FOCUS_TARGETS injured players around it. The event lives on the totem, so it dies with it. Cast by the
    // totem (A11): it rolls none of the shaman's procs.
    void QueuePlacementHeal(Player* player, Creature* totem)
    {
        if (Shaman::GetTalentRank(player, TOTEMIC_FOCUS_RANKS) < TOTEMIC_FOCUS_CAPSTONE_RANK)
            return;

        ObjectGuid const ownerGuid = player->GetGUID();
        totem->m_Events.AddEventAtOffset([totem, ownerGuid]()
        {
            if (!totem->IsInWorld() || !totem->IsAlive())
                return;

            Player* owner = Shaman::GetOwningPlayer(totem);
            if (!owner || owner->GetGUID() != ownerGuid)
                return;

            // Lowest health percent first, so the injured come before anyone at full health.
            std::vector<Unit*> allies;
            Heal::SelectMostInjured(owner, totem, ShamanData::TOTEMIC_FOCUS_RADIUS_YD,
                uint8(ShamanData::TOTEMIC_FOCUS_TARGETS), allies);
            for (Unit* ally : allies)
            {
                if (ally->IsFullHealth())
                    continue;

                LogRestoCastFailure("Totemic Focus", ShamanData::SPELL_TOTEMIC_FOCUS_HEAL, totem, ally,
                    totem->CastSpell(ally, ShamanData::SPELL_TOTEMIC_FOCUS_HEAL, TRIGGERED_FULL_MASK));
            }
        }, Milliseconds(ShamanData::TOTEMIC_FOCUS_DELAY_MS));
    }

    // The healing-done effect(s) of the Totemic Resonance aura take `amount` (live); only a moved value is written.
    void SetResonanceAmount(Aura* aura, int32 amount)
    {
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (effect && effect->GetAuraType() == SPELL_AURA_MOD_HEALING_DONE_PERCENT && effect->GetAmount() != amount)
                effect->ChangeAmount(amount);
        }
    }

    // Cloudburst cooldown (known-hard 1): the castable has no DBC cooldown, so the button recalls while the totem
    // stands; any release sets max(0, CLOUDBURST_COOLDOWN_MS / (1 + Cooldown Haste) - time since placement). One tick
    // later (A14 shape), so the packets of the cast or the unsummon that released it land first; clear-then-set resend
    // so the button greys. Never shortens a longer cooldown.
    void ApplyCloudburstCooldown(Player* player, uint32 placedMs, bool immediate = false)
    {
        float const cooldownHastePct = std::max(0.0f, player->GetCooldownHastePercentage());
        uint32 const fullMs = uint32(float(ShamanData::CLOUDBURST_COOLDOWN_MS) / (1.0f + cooldownHastePct / 100.0f));
        uint32 const elapsedMs = NowMs() - placedMs;
        if (elapsedMs >= fullMs)
            return;

        uint32 const remainingMs = fullMs - elapsedMs;
        if (immediate)
        {
            // Logout / teleport in progress: no later tick will run, and the saved cooldown must survive (WP-R L6).
            if (player->GetSpellCooldownDelay(ShamanData::SPELL_CLOUDBURST_TOTEM) < remainingMs)
                player->AddSpellCooldown(ShamanData::SPELL_CLOUDBURST_TOTEM, 0, remainingMs, true);
            return;
        }

        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid, remainingMs]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!self || self->GetSpellCooldownDelay(ShamanData::SPELL_CLOUDBURST_TOTEM) >= remainingMs)
                return;

            self->AddSpellCooldown(ShamanData::SPELL_CLOUDBURST_TOTEM, 0, remainingMs, true);
            self->ResendSpellCooldown(ShamanData::SPELL_CLOUDBURST_TOTEM);
        }, 1ms);
    }

    // The store split evenly among the injured players within CLOUDBURST_RADIUS_YD of the totem (never pets; line of
    // sight from the totem). Cast by the player with its own id: the release has no family bits and ignores caster
    // modifiers (no Purification, no Totemic Resonance, no crit), it is not a totem heal (no OnHeal store) and the
    // store buff is already gone (no proc store).
    void HealFromCloudburst(Player* player, Creature* totem, double stored)
    {
        std::vector<Unit*> allies;
        Heal::SelectMostInjured(player, totem, ShamanData::CLOUDBURST_RADIUS_YD, CLOUDBURST_MAX_TARGETS, allies);
        std::erase_if(allies, [totem](Unit const* ally)
        {
            return ally->IsFullHealth() || !totem->IsWithinLOSInMap(ally);
        });

        if (allies.empty())
            return;

        int32 const share = int32(stored / double(allies.size()));
        if (share <= 0)
            return;

        // SPELLVALUE_BASE_POINT0 takes the live amount (SKILL "Sign convention").
        for (Unit* ally : allies)
            LogRestoCastFailure("Cloudburst release", ShamanData::SPELL_CLOUDBURST_RELEASE, player, ally,
                player->CastCustomSpell(ShamanData::SPELL_CLOUDBURST_RELEASE, SPELLVALUE_BASE_POINT0, share, ally,
                    TRIGGERED_FULL_MASK));
    }

    // Ends the recorded Cloudburst. The state is cleared first, so the store buff's own remove handler (or a second
    // release path for the same totem) finds nothing to release. `totem` may be nullptr (gone, another map): then
    // nothing heals.
    void ReleaseCloudburstAt(Player* player, Creature* totem, bool discard, bool applyCooldown)
    {
        RestorationState* state = FindRestorationState(player);
        if (!state || !state->cloudburstActive)
            return;

        double const stored = state->cloudburstStored;
        uint32 const placedMs = state->cloudburstPlacedMs;
        state->cloudburstActive = false;
        state->cloudburstTotem.Clear();
        state->cloudburstStored = 0.0;

        player->RemoveAurasDueToSpell(ShamanData::SPELL_CLOUDBURST_STORE, player->GetGUID());

        // Recall (recast) and a store-buff release: the totem still holds the Air slot. Totem::UnSummon clears the slot
        // and defers the removal; the remove hook then finds no recorded Cloudburst.
        if (totem && player->m_SummonSlot[SUMMON_SLOT_TOTEM_AIR] == totem->GetGUID())
            if (Totem* summon = totem->ToTotem())
                summon->UnSummon();

        if (!discard && totem && stored >= 1.0)
            HealFromCloudburst(player, totem, stored);

        if (applyCooldown)
            ApplyCloudburstCooldown(player, placedMs);
    }

    // A new Cloudburst: records the placement and shows the store buff for as long as the totem stands (added here if
    // the cast did not apply it already). A Cloudburst still recorded (no recall ran) releases first, without a
    // cooldown on the button of the new one.
    void RecordCloudburstPlacement(Player* player, Creature* totem)
    {
        RestorationState* state = GetRestorationState(player);
        if (state->cloudburstActive && state->cloudburstTotem != totem->GetGUID())
        {
            Creature* previous = ObjectAccessor::GetCreature(*player, state->cloudburstTotem);
            ReleaseCloudburstAt(player, previous, !player->IsAlive(), false);
        }

        state->cloudburstActive = true;
        state->cloudburstTotem = totem->GetGUID();
        state->cloudburstPlacedMs = NowMs();
        state->cloudburstStored = 0.0;

        Aura* store = player->GetAura(ShamanData::SPELL_CLOUDBURST_STORE, player->GetGUID());
        if (!store)
            store = player->AddAura(ShamanData::SPELL_CLOUDBURST_STORE, player);

        // The buff is infinite: the release (any way the totem goes) removes it.
        if (!store || store->IsRemoved())
            LOG_ERROR("scripts.spells", "Shaman S2: could not apply Cloudburst store {} to {}",
                ShamanData::SPELL_CLOUDBURST_STORE, player->GetGUID().ToString());
    }

    void ClearRestorationState(Player* player)
    {
        player->CustomData.Erase(RESTORATION_STATE_KEY);
    }
}

namespace Shaman
{
    bool IsHealingTotemEntry(uint32 entry)
    {
        switch (entry)
        {
            case NPC_HEALING_STREAM_TOTEM:
            case ShamanData::NPC_HEALING_TIDE_TOTEM:
            case ShamanData::NPC_EARTHEN_WALL_TOTEM:
            case ShamanData::NPC_UNDULATING_CURRENTS_TOTEM:
            case ShamanData::NPC_CLOUDBURST_TOTEM:
            case ShamanData::NPC_SPIRIT_LINK_TOTEM:
            case ShamanData::NPC_WATER_ELEMENTAL_TOTEM:
                return true;
            default:
                return false;
        }
    }

    uint8 GetRestorationTotemCount(Player const* player)
    {
        if (!player)
            return 0;

        uint8 count = 0;
        for (uint8 slot = SUMMON_SLOT_TOTEM_FIRE; slot < MAX_TOTEM_SLOT; ++slot)
            if (Creature const* totem = GetSlotTotem(player, slot))
                if (IsHealingTotemEntry(totem->GetEntry()))
                    ++count;

        return std::min<uint8>(count, uint8(ShamanData::TR_MAX_COUNT));
    }

    float GetTotemicResonancePct(Player const* player)
    {
        if (!player || !GetTalentRank(player, { ShamanData::SPELL_TOTEMIC_RESONANCE }))
            return 0.0f;

        uint8 const count = GetRestorationTotemCount(player);
        if (!count)
            return 0.0f;

        // One rank, so the capstone (the Mastery part) is always on.
        float const mastery = std::max(0.0f, player->GetMasteryPercentage());
        float const perCount = float(ShamanData::TR_PCT_PER_COUNT) +
            float(ShamanData::TR_MASTERY_COEFF_PCT) / 100.0f * mastery;
        return float(count) * perCount;
    }

    void RecountTotemicResonance(Player* player)
    {
        if (!IsUsablePlayer(player))
            return;

        ObjectGuid const guid = player->GetGUID();
        uint8 const count = GetTalentRank(player, { ShamanData::SPELL_TOTEMIC_RESONANCE }) ?
            GetRestorationTotemCount(player) : 0;

        Aura* aura = player->GetAura(ShamanData::SPELL_TOTEMIC_RESONANCE_AURA, guid);
        if (!count)
        {
            if (aura)
                player->RemoveAurasDueToSpell(ShamanData::SPELL_TOTEMIC_RESONANCE_AURA, guid);

            return;
        }

        if (!aura)
        {
            aura = player->AddAura(ShamanData::SPELL_TOTEMIC_RESONANCE_AURA, player);
            if (!aura)
            {
                LOG_ERROR("scripts.spells", "Shaman::RecountTotemicResonance: could not apply aura {} to {}",
                    ShamanData::SPELL_TOTEMIC_RESONANCE_AURA, guid.ToString());
                return;
            }
        }

        if (aura->IsRemoved())
            return;

        // A stack change recalculates every effect from the row (base x stacks); the live amount is written after.
        if (aura->GetStackAmount() != count)
            aura->SetStackAmount(count);

        SetResonanceAmount(aura, int32(std::lround(GetTotemicResonancePct(player))));
    }

    uint32 GetEarthenWallAbsorb(Player const* owner, SpellInfo const* shield, uint8 effIndex)
    {
        if (!owner || !shield || effIndex >= MAX_SPELL_EFFECTS)
            return 0;

        // Absorbs get no engine spell power (potency.md): base (level scaling and SpellMods through the owner, the
        // totem's mod owner and level) plus the owner's healing power times the generated coefficient. The power
        // getter is non-const only because it caches nothing; it reads the owner's auras and stats.
        Player* source = const_cast<Player*>(owner);
        SpellEffectInfo const& effect = shield->Effects[effIndex];

        float bonus = effect.BonusMultiplier * float(source->SpellBaseHealingBonusDone(shield->GetSchoolMask()));
        bonus *= owner->CalculateLevelPenalty(shield);

        float amount = float(effect.CalcValue(owner)) + bonus;

        // Totemic Resonance raises absorbs too; the aura's healing-done percent never reaches an absorb.
        amount *= 1.0f + GetTotemicResonancePct(owner) / 100.0f;

        // S3 Earth's Grasp: the main shield (and so Earthen Bulwark's share of it) x (1 + rank %).
        amount *= 1.0f + GetEarthsGraspAbsorbPct(owner) / 100.0f;
        return uint32(std::max(0.0f, amount));
    }

    void GrantTidalWaves(Player* player, uint8 amount)
    {
        if (!player || !amount)
            return;

        int32 const cap = int32(ShamanData::TIDAL_WAVES_MAX);
        int32 const grant = std::min<int32>(amount, cap);

        Aura* aura = player->GetAura(ShamanData::SPELL_TIDAL_WAVES_BUFF, player->GetGUID());
        if (aura)
        {
            // Raise to the grant, never lower; a delta of 0 still refreshes (ModStackAmount's refresh branch).
            int32 const delta = std::max(0, grant - int32(aura->GetStackAmount()));
            aura->ModStackAmount(delta);
        }
        else
        {
            aura = player->AddAura(ShamanData::SPELL_TIDAL_WAVES_BUFF, player);
            if (!aura)
            {
                LOG_ERROR("scripts.spells", "Shaman::GrantTidalWaves: could not apply aura {} to {}",
                    ShamanData::SPELL_TIDAL_WAVES_BUFF, player->GetGUID().ToString());
                return;
            }

            // A new aura starts at one stack.
            if (grant > 1)
                aura->ModStackAmount(grant - 1);
        }

        if (aura->IsRemoved())
            return;

        int32 const duration = int32(ShamanData::TIDAL_WAVES_DURATION_MS);
        if (aura->GetMaxDuration() != duration)
            aura->SetMaxDuration(duration);

        aura->SetDuration(duration);
    }

    bool ConsumeTidalWaves(Player* player)
    {
        if (!player)
            return false;

        Aura* aura = player->GetAura(ShamanData::SPELL_TIDAL_WAVES_BUFF, player->GetGUID());
        if (!aura || aura->IsRemoved() || !aura->GetStackAmount())
            return false;

        // A negative ModStackAmount neither refreshes the duration nor the timers, and removes the aura at 0.
        aura->ModStackAmount(-1);

        // Improved Chain Heal capstone: the count resets when the buff is used, so consumptions while it is up do not
        // count; the next count starts once the Chain Heal has spent it.
        if (GetTalentRank(player, IMPROVED_CHAIN_HEAL_RANKS) < IMPROVED_CHAIN_HEAL_CAPSTONE_RANK ||
            player->HasAura(ShamanData::SPELL_IMPROVED_CHAIN_HEAL_BUFF, player->GetGUID()))
            return true;

        RestorationState* state = GetRestorationState(player);
        if (++state->chainHealCount < uint8(ShamanData::ICH_CHARGES_NEEDED))
            return true;

        state->chainHealCount = 0;
        if (!player->AddAura(ShamanData::SPELL_IMPROVED_CHAIN_HEAL_BUFF, player))
            LOG_ERROR("scripts.spells", "Shaman::ConsumeTidalWaves: could not apply aura {} to {}",
                ShamanData::SPELL_IMPROVED_CHAIN_HEAL_BUFF, player->GetGUID().ToString());

        return true;
    }

    uint8 GetTidalWavesCharges(Player const* player)
    {
        if (!player)
            return 0;

        Aura const* aura = player->GetAura(ShamanData::SPELL_TIDAL_WAVES_BUFF, player->GetGUID());
        return (aura && !aura->IsRemoved()) ? aura->GetStackAmount() : 0;
    }

    void AddCloudburstStore(Player* player, uint32 effectiveHeal)
    {
        if (!player || !effectiveHeal)
            return;

        RestorationState* state = FindRestorationState(player);
        if (!state || !state->cloudburstActive)
            return;

        state->cloudburstStored += double(effectiveHeal) * double(ShamanData::CLOUDBURST_STORE_PCT) / 100.0;
    }

    void ReleaseCloudburst(Player* player, bool discard)
    {
        if (!player)
            return;

        RestorationState const* state = FindRestorationState(player);
        if (!state || !state->cloudburstActive)
            return;

        // The recorded totem, when it is still on the player's map (the remove hook runs while it is in the store).
        Creature* totem = ObjectAccessor::GetCreature(*player, state->cloudburstTotem);
        ReleaseCloudburstAt(player, totem, discard || !player->IsAlive(), true);
    }

    void OnPlayerBeforeLogout(Player* player)
    {
        if (!player)
            return;

        // S3 (D9): charges, singles, both Ascendances, the bank and the Unleashed Rage clause never reach the save.
        DropEnhancementAuras(player);

        // The totem's removal is deferred past the Player's deletion (Totem::UnSummon -> AddObjectToRemoveList), so its
        // remove hook finds no owner, and WorldSession::LogoutPlayer saves right after this hook: add the remaining
        // cooldown now. The record stays; OnPlayerLogout's ClearState drops it.
        RestorationState const* state = FindRestorationState(player);
        if (!state || !state->cloudburstActive)
            return;

        ApplyCloudburstCooldown(player, state->cloudburstPlacedMs, true);
    }

    void ExtendTidalForce(Player* player, uint32 ms)
    {
        if (!player || !ms)
            return;

        Aura* aura = player->GetAura(ShamanData::SPELL_TIDAL_FORCE_AURA, player->GetGUID());
        if (!aura || aura->IsRemoved() || aura->GetDuration() <= 0)
            return;

        // The max duration grows with it, so the client's timer shows the longer window.
        int32 const duration = aura->GetDuration() + int32(ms);
        if (duration > aura->GetMaxDuration())
            aura->SetMaxDuration(duration);

        aura->SetDuration(duration);
    }

    void OnPlayerTotemAdded(Player* player, Creature* totem)
    {
        if (!IsUsablePlayer(player) || !totem)
            return;

        RecountTotemicResonance(player);
        QueuePlacementHeal(player, totem);

        if (totem->GetEntry() == ShamanData::NPC_CLOUDBURST_TOTEM)
            RecordCloudburstPlacement(player, totem);

        // S3: Guardian Totems capstone.
        ApplyGuardianTotemsCapstone(player, totem);
    }

    void OnPlayerTotemRemoved(Player* player, Creature* totem)
    {
        if (!player || !totem)
            return;

        if (totem->GetEntry() == ShamanData::NPC_CLOUDBURST_TOTEM)
        {
            RestorationState* state = FindRestorationState(player);
            if (state && state->cloudburstActive && state->cloudburstTotem == totem->GetGUID())
            {
                // Expiry, Totemic Recall, Air replacement, right-click and death. A logout never gets here: the totem's
                // removal is deferred past the Player's deletion (no owner), so OnPlayerBeforeLogout applies the
                // cooldown. The branch below covers only a removal that runs while the Player leaves the world: the
                // record drops quietly (nothing can be healed) and the cooldown is applied at once.
                if (IsUsablePlayer(player))
                    ReleaseCloudburstAt(player, totem, !player->IsAlive(), true);
                else
                {
                    ApplyCloudburstCooldown(player, state->cloudburstPlacedMs, true);
                    state->cloudburstActive = false;
                    state->cloudburstTotem.Clear();
                    state->cloudburstStored = 0.0;
                }
            }
        }

        RecountTotemicResonance(player);
    }
}

/*
 * S3 block: Enhancement (docs/reworks/shaman-enhancement-rework.md). Elemental Charge and Earth Charge (grants, the
 * imbue-swap transform, the out-of-combat timers, Shamanistic Rage's bank), the Bursts, the single and Elemental
 * Ascendances with their live Mastery amounts, Stoneskin's Mastery amount, Earth Charge spending, the Unleashed Rage
 * clause, the Frost Spirit's Stormstrike copy, the Rockbiter children (Spirit Guard parry, Improved Lightning Shield
 * threat), Earth's Grasp and the Guardian Totems capstone. Per-player state lives in CustomData (the player's map
 * thread only, no lock).
 *
 * Lifecycles (L-11):
 * - Charges, singles, Elemental and Earthen Ascendance are auras. Death: the engine removes them (not death-persistent,
 *   D9); OnEnhPlayerDied drops the bank and the swap stash. Logout: OnPlayerBeforeLogout drops them before the save,
 *   ClearState erases the state. Map change: auras, state and the m_Events timers travel with the player, nothing to
 *   do. Talent reset, spec swap, talent learn: OnEnhTalentsChanged one tick later. Imbue right-click or expiry: the
 *   stash is never consumed, so no transform; the charges stay under the 2 min rule.
 * - Out-of-combat timers: a generation per kind in the state; combat entry bumps both, leaving combat or a grant out of
 *   combat arms one; a stale event finds its generation moved (or no state after ClearState) and returns.
 * - Bank: filled only by Shamanistic Rage while an Ascendance blocks charges; added to the active imbue's element once
 *   free (UpdateUnleashedRage, RefreshAscendance, SpendEarthCharge, AddCharge and a check scheduled at the end of the
 *   Ascendance); dropped on death and logout.
 * - The Rockbiter children (passive, hidden) follow Rockbiter and the talents: OnRockbiterChanged and
 *   OnEnhTalentsChanged (login included); Parry itself stays until relog (engine, 0-verify item e).
 */
namespace
{
    struct EnhancementState : DataMap::Base
    {
        uint32 stashedImbue = 0;    // imbue removed in tick `stashTick` (group 1251 eviction or a cancel), 0 when none
        uint32 stashTick = 0;       // GameTime ms of that removal
        uint8 bankedCharges = 0;    // Shamanistic Rage's charges granted while an Ascendance blocked them
        uint32 chargeTimerGen = 0;  // out-of-combat timer generations: charges (EC_OOC_MS) and singles (ASC_OOC_MS)
        uint32 singleTimerGen = 0;
        uint32 refreshGen = 0;      // live-Mastery refresh loop generation (a newer start retires an older loop)
        bool refreshRunning = false;
    };

    constexpr char const* ENHANCEMENT_STATE_KEY = "shaman_enhancement_state";

    constexpr std::array<uint32, 4> CHARGE_SPELLS =
    {
        ShamanData::SPELL_FIRE_CHARGE,
        ShamanData::SPELL_FROST_CHARGE,
        ShamanData::SPELL_WIND_CHARGE,
        ShamanData::SPELL_EARTH_CHARGE
    };

    constexpr std::array<uint32, 3> SINGLE_ASCENDANCES =
    {
        ShamanData::SPELL_FIRE_ASCENDANCE,
        ShamanData::SPELL_FROST_ASCENDANCE,
        ShamanData::SPELL_WIND_ASCENDANCE
    };

    constexpr std::array<Shaman::EnhElement, 3> TRANSFORM_ELEMENTS =
    {
        Shaman::EnhElement::Fire,
        Shaman::EnhElement::Frost,
        Shaman::EnhElement::Wind
    };

    constexpr std::array<uint32, 1> ELEMENTAL_CHARGE_RANKS = { ShamanData::SPELL_ELEMENTAL_CHARGE };
    constexpr std::array<uint32, 1> ASCENDANCE_RANKS = { ShamanData::SPELL_ASCENDANCE };

    constexpr std::array<uint32, 3> SPIRIT_GUARD_RANKS =
    {
        ShamanData::SPELL_SPIRIT_GUARD_RANK1,
        ShamanData::SPELL_SPIRIT_GUARD_RANK2,
        ShamanData::SPELL_SPIRIT_GUARD_RANK3
    };

    // Improved Lightning Shield (the stock Improved Shields ranks, rewritten in place).
    constexpr std::array<uint32, 3> IMPROVED_LIGHTNING_SHIELD_RANKS =
    {
        ShamanData::SPELL_IMPROVED_SHIELDS,
        ShamanData::SPELL_IMPROVED_SHIELDS_16290,
        ShamanData::SPELL_IMPROVED_SHIELDS_51881
    };

    // Unleashed Rage. Its ranks are raid area auras, so every party member carries the rank id: read with
    // GetOwnTalentRank (the talent map), never GetTalentRank (which also accepts the aura), WP-R m2.
    constexpr std::array<uint32, 3> UNLEASHED_RAGE_RANKS =
    {
        ShamanData::SPELL_UNLEASHED_RAGE,
        ShamanData::SPELL_UNLEASHED_RAGE_30808,
        ShamanData::SPELL_UNLEASHED_RAGE_30809
    };

    // Interval of the live-Mastery refresh while an Ascendance or Stoneskin is up (WP-R m1; RefreshEmpowerment's
    // periodic dummy ticks the same way).
    constexpr int32 ASCENDANCE_REFRESH_MS = 1000;

    constexpr std::array<int32, 3> UNLEASHED_RAGE_CLAUSE_PCT =
    {
        int32(ShamanData::UR_R1),
        int32(ShamanData::UR_R2),
        int32(ShamanData::UR_R3)
    };

    constexpr std::array<uint32, 2> EARTHS_GRASP_RANKS =
    {
        ShamanData::SPELL_EARTH_S_GRASP,
        ShamanData::SPELL_EARTH_S_GRASP_16130
    };

    constexpr std::array<uint32, 2> GUARDIAN_TOTEMS_RANKS =
    {
        ShamanData::SPELL_GUARDIAN_TOTEMS,
        ShamanData::SPELL_GUARDIAN_TOTEMS_16293
    };

    constexpr uint8 GUARDIAN_TOTEMS_CAPSTONE_RANK = 2;

    // Spirit Guard's parry bonus under Rockbiter is 1/2/3% (doc [fixed]): the rank itself. The brief names no const
    // for it (local fallback).
    constexpr int32 SPIRIT_GUARD_PARRY_PCT_PER_RANK = 1;

    // Re-check interval of a bank waiting on an Ascendance without a finite duration.
    constexpr int32 BANK_FLUSH_POLL_MS = 1000;

    EnhancementState* GetEnhancementState(Player* player)
    {
        return player->CustomData.GetDefault<EnhancementState>(ENHANCEMENT_STATE_KEY);
    }

    EnhancementState* FindEnhancementState(Player const* player)
    {
        return player->CustomData.Get<EnhancementState>(ENHANCEMENT_STATE_KEY);
    }

    uint32 GetChargeSpell(Shaman::EnhElement element)
    {
        switch (element)
        {
            case Shaman::EnhElement::Fire:
                return ShamanData::SPELL_FIRE_CHARGE;
            case Shaman::EnhElement::Frost:
                return ShamanData::SPELL_FROST_CHARGE;
            case Shaman::EnhElement::Wind:
                return ShamanData::SPELL_WIND_CHARGE;
            case Shaman::EnhElement::Earth:
                return ShamanData::SPELL_EARTH_CHARGE;
            default:
                return 0;
        }
    }

    uint32 GetSingleAscendance(Shaman::EnhElement element)
    {
        switch (element)
        {
            case Shaman::EnhElement::Fire:
                return ShamanData::SPELL_FIRE_ASCENDANCE;
            case Shaman::EnhElement::Frost:
                return ShamanData::SPELL_FROST_ASCENDANCE;
            case Shaman::EnhElement::Wind:
                return ShamanData::SPELL_WIND_ASCENDANCE;
            default:
                return 0;
        }
    }

    uint32 GetBurstSpell(Shaman::EnhElement element)
    {
        switch (element)
        {
            case Shaman::EnhElement::Fire:
                return ShamanData::SPELL_FLAME_BURST;
            case Shaman::EnhElement::Frost:
                return ShamanData::SPELL_STORM_BURST;
            case Shaman::EnhElement::Wind:
                return ShamanData::SPELL_WIND_BURST;
            default:
                return 0;
        }
    }

    uint32 GetAscendanceVisualSpell(Shaman::EnhElement element)
    {
        switch (element)
        {
            case Shaman::EnhElement::Fire:
                return ShamanData::SPELL_ASCENDANCE_FIRE_NOVA;
            case Shaman::EnhElement::Frost:
                return ShamanData::SPELL_ASCENDANCE_FROST_NOVA;
            case Shaman::EnhElement::Wind:
                return ShamanData::SPELL_ASCENDANCE_WIND_BURST;
            case Shaman::EnhElement::Earth:
                return ShamanData::SPELL_ASCENDANCE_EARTH_STOMP;
            default:
                return 0;
        }
    }

    int32 GetChargeCap(Shaman::EnhElement element)
    {
        return element == Shaman::EnhElement::Earth ? int32(ShamanData::CHARGE_CAP_EARTH) :
            int32(ShamanData::CHARGE_CAP_ELEMENT);
    }

    bool IsTransformElement(Shaman::EnhElement element)
    {
        return element == Shaman::EnhElement::Fire || element == Shaman::EnhElement::Frost ||
            element == Shaman::EnhElement::Wind;
    }

    bool IsElementalAscendant(Player const* player)
    {
        return player->HasAura(ShamanData::SPELL_ELEMENTAL_ASCENDANCE);
    }

    bool IsChargeBlocked(Player const* player)
    {
        return IsElementalAscendant(player) || Shaman::IsEarthenAscendant(player);
    }

    void RemoveOwnAura(Player* player, uint32 spellId)
    {
        player->RemoveAurasDueToSpell(spellId, player->GetGUID());
    }

    bool HasAnyOwnAura(Player const* player, std::span<uint32 const> spellIds)
    {
        ObjectGuid const guid = player->GetGUID();
        return std::any_of(spellIds.begin(), spellIds.end(),
            [player, guid](uint32 spellId) { return player->HasAura(spellId, guid); });
    }

    void LogEnhCastFailure(char const* what, uint32 spellId, Unit const* caster, Unit const* target,
        SpellCastResult result)
    {
        switch (result)
        {
            case SPELL_CAST_OK:
            case SPELL_FAILED_LINE_OF_SIGHT:
            case SPELL_FAILED_OUT_OF_RANGE:
            case SPELL_FAILED_BAD_TARGETS:
            case SPELL_FAILED_BAD_IMPLICIT_TARGETS:
                return;
            default:
                break;
        }

        LOG_ERROR("scripts.spells", "Shaman S3 {}: cast of {} by {} at {} failed (result {})", what, spellId,
            caster ? caster->GetGUID().ToString() : "none", target ? target->GetGUID().ToString() : "none",
            uint32(result));
    }

    // Live Mastery percent the Ascendance capstone adds (the talent has one rank, so the capstone is on with it); 0
    // without the talent. Negative Mastery never lowers a bonus.
    float GetAscendanceMasteryPct(Player const* player)
    {
        if (!Shaman::GetTalentRank(player, ASCENDANCE_RANKS))
            return 0.0f;

        return std::max(0.0f, player->GetMasteryPercentage());
    }

    // Integer percent, rounded to MASTERY_ROUND_PCT steps.
    int32 RoundMasteryPct(float pct)
    {
        double const step = std::max(1.0, double(ShamanData::MASTERY_ROUND_PCT));
        return int32(std::lround(double(pct) / step) * step);
    }

    // The highest known rank's first DUMMY effect value (per-rank percents live there, L-8); 0 without the talent.
    int32 GetRankDummyValue(Player const* player, std::span<uint32 const> rankIds)
    {
        uint8 const rank = Shaman::GetTalentRank(player, rankIds);
        if (!rank)
            return 0;

        SpellInfo const* info = sSpellMgr->GetSpellInfo(rankIds[rank - 1]);
        if (!info)
            return 0;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (info->Effects[i].IsAura(SPELL_AURA_DUMMY))
                return info->Effects[i].CalcValue(player);

        return 0;
    }

    // Sets every effect of `aura` with `auraType` (and, for spell modifiers, a SPELLMOD_DAMAGE / SPELLMOD_DOT op) to
    // its row value plus `bonus`; only a moved value is written (a spell modifier change is re-sent to the client).
    void SetLiveAmounts(Player* player, Aura* aura, AuraType auraType, int32 bonus)
    {
        if (!aura || aura->IsRemoved())
            return;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (!effect || effect->GetAuraType() != auraType)
                continue;

            if (auraType == SPELL_AURA_ADD_PCT_MODIFIER && effect->GetMiscValue() != int32(SPELLMOD_DAMAGE) &&
                effect->GetMiscValue() != int32(SPELLMOD_DOT))
                continue;

            int32 const amount = aura->GetSpellInfo()->Effects[i].CalcValue(player) + bonus;
            if (effect->GetAmount() != amount)
                effect->ChangeAmount(amount, false);
        }
    }

    // A buff the player owns, refreshed to `durationMs` (the const is the source of truth for the window), or added.
    Aura* RefreshOwnBuff(Player* player, uint32 spellId, int32 durationMs)
    {
        Aura* aura = player->GetAura(spellId, player->GetGUID());
        if (!aura)
            aura = player->AddAura(spellId, player);

        if (!aura || aura->IsRemoved())
        {
            LOG_ERROR("scripts.spells", "Shaman S3: could not apply aura {} to {}", spellId,
                player->GetGUID().ToString());
            return nullptr;
        }

        if (aura->GetMaxDuration() != durationMs)
            aura->SetMaxDuration(durationMs);

        aura->SetDuration(durationMs);
        return aura;
    }

    // Starts (or restarts) one out-of-combat timer: the charges (EC_OOC_MS) or the singles (ASC_OOC_MS). A newer arm,
    // a combat entry or ClearState makes the pending event stale.
    void ArmEnhTimer(Player* player, bool singles)
    {
        EnhancementState* state = GetEnhancementState(player);
        uint32 const generation = singles ? ++state->singleTimerGen : ++state->chargeTimerGen;
        uint32 const delayMs = uint32(singles ? ShamanData::ASC_OOC_MS : ShamanData::EC_OOC_MS);

        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid, generation, singles]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!self || self->IsInCombat())
                return;

            EnhancementState const* current = FindEnhancementState(self);
            if (!current || (singles ? current->singleTimerGen : current->chargeTimerGen) != generation)
                return;

            if (singles)
            {
                for (uint32 const spellId : SINGLE_ASCENDANCES)
                    RemoveOwnAura(self, spellId);
            }
            else
            {
                for (uint32 const spellId : CHARGE_SPELLS)
                    RemoveOwnAura(self, spellId);
            }
        }, Milliseconds(delayMs));
    }

    // Adds `amount` stacks to the element's charge buff (cap per element; a delta of 0 at the cap still refreshes) and
    // arms the out-of-combat timer for a grant out of combat.
    void AddChargeStacks(Player* player, Shaman::EnhElement element, uint8 amount)
    {
        uint32 const spellId = GetChargeSpell(element);
        if (!spellId || !amount)
            return;

        int32 const cap = GetChargeCap(element);
        int32 const grant = std::min<int32>(amount, cap);

        if (Aura* aura = player->GetAura(spellId, player->GetGUID()))
        {
            int32 const delta = std::max(0, std::min(grant, cap - int32(aura->GetStackAmount())));
            aura->ModStackAmount(delta);
        }
        else
        {
            Aura* created = player->AddAura(spellId, player);
            if (!created)
            {
                LOG_ERROR("scripts.spells", "Shaman::AddCharge: could not apply aura {} to {}", spellId,
                    player->GetGUID().ToString());
                return;
            }

            // A new aura starts at one stack.
            if (grant > 1)
                created->ModStackAmount(grant - 1);
        }

        if (!player->IsInCombat())
            ArmEnhTimer(player, false);
    }

    // Adds the banked Shamanistic Rage charges to the active imbue's element once no Ascendance blocks them (alive,
    // with Elemental Charge; Earthliving or no imbue: the bank is lost).
    void FlushBank(Player* player)
    {
        if (!IsUsablePlayer(player) || !player->IsAlive() || IsChargeBlocked(player))
            return;

        EnhancementState* state = FindEnhancementState(player);
        if (!state || !state->bankedCharges)
            return;

        uint8 const banked = state->bankedCharges;
        state->bankedCharges = 0;

        Shaman::EnhElement const element = Shaman::GetImbueElement(Shaman::GetActiveImbue(player));
        if (element == Shaman::EnhElement::None || !Shaman::GetTalentRank(player, ELEMENTAL_CHARGE_RANKS))
            return;

        AddChargeStacks(player, element, banked);
    }

    // Checks again when the blocking Ascendance should have ended (its remaining duration, or a poll for one without a
    // finite duration); still blocked: once more, else the bank is added.
    void ScheduleBankFlush(Player* player)
    {
        int32 delayMs = 0;
        for (uint32 const spellId : { uint32(ShamanData::SPELL_ELEMENTAL_ASCENDANCE),
            uint32(ShamanData::SPELL_EARTHEN_ASCENDANCE) })
            if (Aura const* aura = player->GetAura(spellId))
                delayMs = std::max(delayMs, aura->GetDuration() > 0 ? aura->GetDuration() : BANK_FLUSH_POLL_MS);

        if (!delayMs)
            delayMs = BANK_FLUSH_POLL_MS;

        ObjectGuid const guid = player->GetGUID();
        player->m_Events.AddEventAtOffset([guid]()
        {
            Player* self = ObjectAccessor::FindPlayer(guid);
            if (!IsUsablePlayer(self))
                return;

            EnhancementState const* state = FindEnhancementState(self);
            if (!state || !state->bankedCharges)
                return;

            if (IsChargeBlocked(self))
                ScheduleBankFlush(self);
            else
                FlushBank(self);
        }, Milliseconds(delayMs + 50));
    }

    // Spirit Guard's parry child (rank %) and the Improved Lightning Shield threat child, on while Rockbiter is up and
    // the talent is known. Both are passive and hidden; the parry amount is set live (it is not a row value).
    void SyncRockbiterChildren(Player* player, bool rockbiter)
    {
        uint8 const spiritGuardRank = Shaman::GetTalentRank(player, SPIRIT_GUARD_RANKS);
        bool const parryWanted = rockbiter && spiritGuardRank > 0;
        SetOwnerAura(player, player, ShamanData::SPELL_SPIRIT_GUARD_PARRY, parryWanted);

        if (parryWanted)
        {
            int32 const parryPct = int32(spiritGuardRank) * SPIRIT_GUARD_PARRY_PCT_PER_RANK;
            if (Aura* aura = player->GetAura(ShamanData::SPELL_SPIRIT_GUARD_PARRY, player->GetGUID()))
                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                    if (AuraEffect* effect = aura->GetEffect(i))
                        if (effect->GetAuraType() == SPELL_AURA_MOD_PARRY_PERCENT && effect->GetAmount() != parryPct)
                            effect->ChangeAmount(parryPct);     // marked: a recalculation keeps the live value
        }

        SetOwnerAura(player, player, ShamanData::SPELL_ROCKBITER_ILS_THREAT,
            rockbiter && Shaman::GetTalentRank(player, IMPROVED_LIGHTNING_SHIELD_RANKS) > 0);
    }

    // 1-based rank of the highest rank in the player's talent map for the active spec (no aura fallback); 0 if none.
    uint8 GetOwnTalentRank(Player const* player, std::span<uint32 const> rankIds)
    {
        uint8 const spec = player->GetActiveSpec();
        for (size_t i = rankIds.size(); i > 0; --i)
            if (rankIds[i - 1] && player->HasTalent(rankIds[i - 1], spec))
                return uint8(i);

        return 0;
    }

    // Whether the live-Mastery refresh has something to keep live: the Ascendance talent and a single, Elemental
    // Ascendance or Stoneskin.
    bool NeedsAscendanceRefresh(Player const* player)
    {
        if (!Shaman::GetTalentRank(player, ASCENDANCE_RANKS))
            return false;

        ObjectGuid const guid = player->GetGUID();
        return HasAnyOwnAura(player, SINGLE_ASCENDANCES) ||
            player->HasAura(ShamanData::SPELL_ELEMENTAL_ASCENDANCE, guid) ||
            player->HasAura(ShamanData::SPELL_STONESKIN_202206, guid);
    }

    // WP-R m1: Mastery moves with gear, buffs and Enhanced Elements without an event, so while NeedsAscendanceRefresh
    // holds, RefreshAscendance runs every ASCENDANCE_REFRESH_MS (it writes only moved values). One loop per player: a
    // running loop is kept unless `restart` (map change, login, talent sync: a teleport may have killed the player's
    // events, CleanupBeforeRemoveFromMap), which retires the old loop through the generation.
    void StartAscendanceRefresh(Player* player, bool restart)
    {
        EnhancementState* state = GetEnhancementState(player);
        if (state->refreshRunning && !restart)
            return;

        if (!NeedsAscendanceRefresh(player))
        {
            state->refreshRunning = false;
            ++state->refreshGen;
            return;
        }

        state->refreshRunning = true;
        uint32 const generation = ++state->refreshGen;
        ObjectGuid const guid = player->GetGUID();

        // A named recursive lambda: each tick re-queues itself while it is the current generation and still needed.
        struct Tick
        {
            static void Queue(Player* owner, ObjectGuid ownerGuid, uint32 gen)
            {
                owner->m_Events.AddEventAtOffset([ownerGuid, gen]()
                {
                    Player* self = ObjectAccessor::FindPlayer(ownerGuid);
                    if (!self)
                        return;

                    EnhancementState* current = FindEnhancementState(self);
                    if (!current || current->refreshGen != gen)
                        return;

                    if (!IsUsablePlayer(self) || !NeedsAscendanceRefresh(self))
                    {
                        current->refreshRunning = false;
                        return;
                    }

                    Shaman::RefreshAscendance(self);
                    Queue(self, ownerGuid, gen);
                }, Milliseconds(ASCENDANCE_REFRESH_MS));
            }
        };

        Tick::Queue(player, guid, generation);
    }

    // Declared in the SH0a block.
    void RefreshStoneskinAmount(Player* player)
    {
        Aura* aura = player->GetAura(ShamanData::SPELL_STONESKIN_202206, player->GetGUID());
        if (!aura || aura->IsRemoved())
            return;

        int32 const amount = Shaman::GetStoneskinAmount(player, aura->GetStackAmount());
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            AuraEffect* effect = aura->GetEffect(i);
            if (effect && effect->GetAuraType() == SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN && effect->GetAmount() != amount)
                effect->ChangeAmount(amount, false);
        }

        // Keeps the Mastery part live from here on (no-op while a loop runs).
        StartAscendanceRefresh(player, false);
    }

    void ClearEnhancementState(Player* player)
    {
        player->CustomData.Erase(ENHANCEMENT_STATE_KEY);
    }

    float GetEarthsGraspAbsorbPct(Player const* player)
    {
        return float(std::max(0, GetRankDummyValue(player, EARTHS_GRASP_RANKS)));
    }

    void DropEnhancementAuras(Player* player)
    {
        // The bank first: removing an Ascendance runs its scripts, which would add the bank back.
        if (EnhancementState* state = FindEnhancementState(player))
        {
            state->bankedCharges = 0;
            state->stashedImbue = 0;
        }

        for (uint32 const spellId : CHARGE_SPELLS)
            RemoveOwnAura(player, spellId);

        for (uint32 const spellId : SINGLE_ASCENDANCES)
            RemoveOwnAura(player, spellId);

        RemoveOwnAura(player, ShamanData::SPELL_ELEMENTAL_ASCENDANCE);
        RemoveOwnAura(player, ShamanData::SPELL_EARTHEN_ASCENDANCE);
        RemoveOwnAura(player, ShamanData::SPELL_UNLEASHED_RAGE_CLAUSE);

        // The Elemental Spirits timer (S3a code review n1): a saved copy would outlive the wolves it counts down for.
        RemoveOwnAura(player, ShamanData::SPELL_ELEMENTAL_SPIRITS_TIMER);
    }

    void ApplyGuardianTotemsCapstone(Player* player, Creature* totem)
    {
        if (!player->IsAlive() ||
            Shaman::GetTalentRank(player, GUARDIAN_TOTEMS_RANKS) < GUARDIAN_TOTEMS_CAPSTONE_RANK)
            return;

        // L-12 / D15: totems a shaman spell created (the elemental totems included); a Freepick Lightwell is a Totem
        // too and does not count.
        SpellInfo const* creator = sSpellMgr->GetSpellInfo(totem->GetUInt32Value(UNIT_CREATED_BY_SPELL));
        if (!creator || creator->SpellFamilyName != SPELLFAMILY_SHAMAN)
            return;

        RefreshOwnBuff(player, ShamanData::SPELL_GUARDIAN_TOTEMS_ARMOR,
            int32(ShamanData::GUARDIAN_TOTEMS_ARMOR_DURATION_MS));
    }
}

namespace Shaman
{
    EnhElement GetImbueElement(uint32 imbueId)
    {
        switch (imbueId)
        {
            case ShamanData::SPELL_FLAMETONGUE_WEAPON:
                return EnhElement::Fire;
            case ShamanData::SPELL_FROSTBRAND_WEAPON:
                return EnhElement::Frost;
            case ShamanData::SPELL_WINDFURY_WEAPON:
                return EnhElement::Wind;
            case ShamanData::SPELL_ROCKBITER_WEAPON:
                return EnhElement::Earth;
            default:
                return EnhElement::None;
        }
    }

    uint8 GetCharge(Player const* player, EnhElement element)
    {
        uint32 const spellId = GetChargeSpell(element);
        if (!player || !spellId)
            return 0;

        Aura const* aura = player->GetAura(spellId, player->GetGUID());
        return (aura && !aura->IsRemoved()) ? aura->GetStackAmount() : 0;
    }

    void AddCharge(Player* player, uint8 amount, bool fromShamanisticRage)
    {
        if (!IsUsablePlayer(player) || !amount || !player->IsAlive())
            return;

        if (!GetTalentRank(player, ELEMENTAL_CHARGE_RANKS))
            return;

        EnhElement const element = GetImbueElement(GetActiveImbue(player));
        if (element == EnhElement::None)
            return;

        // Nothing builds during Elemental or Earthen Ascendance; Shamanistic Rage's grant waits in the bank.
        if (IsChargeBlocked(player))
        {
            if (!fromShamanisticRage)
                return;

            EnhancementState* state = GetEnhancementState(player);
            state->bankedCharges = uint8(std::min<int32>(int32(state->bankedCharges) + amount,
                int32(ShamanData::CHARGE_CAP_EARTH)));
            ScheduleBankFlush(player);
            return;
        }

        FlushBank(player);
        AddChargeStacks(player, element, amount);
    }

    void OnImbueChanged(Player* player, uint32 oldImbue, uint32 newImbue)
    {
        if (!player)
            return;

        EnhancementState* state = GetEnhancementState(player);
        uint32 const now = NowMs();

        // HandleRemove: stash. The eviction's apply follows in the same call stack (same tick); a cancel or expiry has
        // none, so its stash goes stale and transforms nothing.
        if (!newImbue)
        {
            if (oldImbue)
            {
                state->stashedImbue = oldImbue;
                state->stashTick = now;
            }

            return;
        }

        uint32 from = oldImbue;
        if (!from && state->stashedImbue && state->stashTick == now)
            from = state->stashedImbue;

        state->stashedImbue = 0;

        // Same imbue (a recast refreshes without remove/apply; this is a defensive check): nothing. Login aura load
        // (not in world): nothing to resolve, the charges were dropped at logout.
        if (from == newImbue || !player->IsInWorld())
            return;

        EnhElement const left = GetImbueElement(from);
        EnhElement const entered = GetImbueElement(newImbue);

        if (IsTransformElement(left))
        {
            bool const full = GetCharge(player, left) >= ShamanData::CHARGE_CAP_ELEMENT;
            RemoveOwnAura(player, GetChargeSpell(left));

            // Q15: only Flametongue, Frostbrand and Windfury transform; Rockbiter / Earthliving and a swap below the
            // cap reset. Out of combat the Burst finds nobody (engaged-only filter) and the single is still granted.
            if (full && IsTransformElement(entered))
            {
                CastElementalBurst(player, left);
                GrantAscendance(player, left);
            }
        }

        // Only the entered element may hold Elemental Charge now (a cancelled imbue's leftovers reset without a
        // transform). Earth Charge is a separate bank and survives imbue swaps.
        for (EnhElement const element : TRANSFORM_ELEMENTS)
            if (element != entered)
                RemoveOwnAura(player, GetChargeSpell(element));
    }

    void CastElementalBurst(Player* player, EnhElement element)
    {
        uint32 const spellId = GetBurstSpell(element);
        if (!spellId || !IsUsablePlayer(player) || !player->IsAlive())
            return;

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        if (!spellInfo)
        {
            LOG_ERROR("scripts.spells", "Shaman::CastElementalBurst: spell {} does not exist", spellId);
            return;
        }

        // The shaman's current target (selection, else victim) when it is an attackable enemy; else the shaman.
        Unit* centre = nullptr;
        if (Unit* selected = player->GetSelectedUnit())
            if (selected != player && selected->IsAlive() && player->IsValidAttackTarget(selected))
                centre = selected;

        if (!centre)
            if (Unit* victim = player->GetVictim())
                if (victim->IsAlive() && player->IsValidAttackTarget(victim))
                    centre = victim;

        SpellCastTargets targets;
        if (centre)
        {
            targets.SetUnitTarget(centre);
            targets.SetDst(*centre);
        }
        else
            targets.SetDst(*player);

        LogEnhCastFailure("Elemental Burst", spellId, player, centre,
            player->CastSpell(targets, spellInfo, nullptr, TRIGGERED_FULL_MASK));
    }

    void CastAscendanceVisual(Player* player, EnhElement element)
    {
        uint32 const spellId = GetAscendanceVisualSpell(element);
        if (!spellId || !IsUsablePlayer(player) || !player->IsAlive())
            return;

        // Cosmetic only: a self-cast DUMMY with a stock visual, no aura, no damage, no threat, no procs.
        if (player->CastSpell(player, spellId, TRIGGERED_FULL_MASK) != SPELL_CAST_OK)
            LOG_ERROR("scripts.spells", "Shaman::CastAscendanceVisual: cast of {} by {} failed", spellId,
                player->GetGUID().ToString());
    }

    void GrantAscendance(Player* player, EnhElement element)
    {
        uint32 const single = GetSingleAscendance(element);
        if (!single || !IsUsablePlayer(player) || !player->IsAlive())
            return;

        if (!GetTalentRank(player, ASCENDANCE_RANKS))
            return;

        // One of each per cycle: a held single (or Elemental Ascendance) means Burst only.
        ObjectGuid const guid = player->GetGUID();
        if (IsElementalAscendant(player) || player->HasAura(single, guid))
            return;

        if (!player->AddAura(single, player))
        {
            LOG_ERROR("scripts.spells", "Shaman::GrantAscendance: could not apply aura {} to {}", single,
                guid.ToString());
            return;
        }

        bool const allThree = std::all_of(SINGLE_ASCENDANCES.begin(), SINGLE_ASCENDANCES.end(),
            [player, guid](uint32 spellId) { return player->HasAura(spellId, guid); });

        // The ascend burst at the shaman's feet: the element's own, the Earth stomp for Elemental Ascendance.
        CastAscendanceVisual(player, allThree ? EnhElement::Earth : element);

        if (allThree)
        {
            for (uint32 const spellId : SINGLE_ASCENDANCES)
                RemoveOwnAura(player, spellId);

            RefreshOwnBuff(player, ShamanData::SPELL_ELEMENTAL_ASCENDANCE, int32(ShamanData::ASC_DURATION_EA_MS));
            UpdateUnleashedRage(player);
        }
        else if (!player->IsInCombat())
            ArmEnhTimer(player, true);

        RefreshAscendance(player);
        StartAscendanceRefresh(player, false);
    }

    void RefreshAscendance(Player* player)
    {
        if (!IsUsablePlayer(player))
            return;

        // Singles x(1.3 + M): +M; Elemental Ascendance x(1 + 2(0.3 + M)) and Gust x2(1 + M): +2M on top of the row.
        float const mastery = GetAscendanceMasteryPct(player);
        int32 const singleBonus = RoundMasteryPct(mastery);
        int32 const elementalBonus = RoundMasteryPct(2.0f * mastery);
        ObjectGuid const guid = player->GetGUID();

        for (uint32 const spellId : SINGLE_ASCENDANCES)
            SetLiveAmounts(player, player->GetAura(spellId, guid), SPELL_AURA_ADD_PCT_MODIFIER, singleBonus);

        SetLiveAmounts(player, player->GetAura(ShamanData::SPELL_ELEMENTAL_ASCENDANCE, guid),
            SPELL_AURA_ADD_PCT_MODIFIER, elementalBonus);

        RefreshStoneskinAmount(player);
        FlushBank(player);
    }

    bool SpendEarthCharge(Player* player, uint8 amount)
    {
        if (!player || !amount)
            return false;

        FlushBank(player);

        Aura* aura = player->GetAura(ShamanData::SPELL_EARTH_CHARGE, player->GetGUID());
        if (!aura || aura->IsRemoved() || aura->GetStackAmount() < amount)
            return false;

        // A negative ModStackAmount neither refreshes the duration nor the timers, and removes the aura at 0.
        aura->ModStackAmount(-int32(amount));
        return true;
    }

    bool IsEarthenAscendant(Player const* player)
    {
        return player && player->HasAura(ShamanData::SPELL_EARTHEN_ASCENDANCE);
    }

    void UpdateUnleashedRage(Player* player)
    {
        if (!IsUsablePlayer(player))
            return;

        uint8 const rank = GetOwnTalentRank(player, UNLEASHED_RAGE_RANKS);
        bool const wanted = rank > 0 && player->IsAlive() &&
            (player->HasAura(ShamanData::SPELL_SHAMANISTIC_RAGE) || IsElementalAscendant(player));

        SetOwnerAura(player, player, ShamanData::SPELL_UNLEASHED_RAGE_CLAUSE, wanted);
        if (wanted)
        {
            // The rank's amount (UR_R1..UR_R3) replaces the row value; marked, so a recalculation keeps it.
            Aura* aura = player->GetAura(ShamanData::SPELL_UNLEASHED_RAGE_CLAUSE, player->GetGUID());
            int32 const pct = UNLEASHED_RAGE_CLAUSE_PCT[rank - 1];
            if (aura && !aura->IsRemoved())
                for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                    if (AuraEffect* effect = aura->GetEffect(i))
                        if (effect->GetAuraType() == SPELL_AURA_MOD_DAMAGE_PERCENT_DONE && effect->GetAmount() != pct)
                            effect->ChangeAmount(pct);
        }

        FlushBank(player);
    }

    void OnEnhCombatChange(Player* player, bool inCombat)
    {
        if (!player)
            return;

        if (inCombat)
        {
            // Re-entry cancels both pending timers: their generations no longer match.
            if (EnhancementState* state = FindEnhancementState(player))
            {
                ++state->chargeTimerGen;
                ++state->singleTimerGen;
            }

            return;
        }

        if (HasAnyOwnAura(player, CHARGE_SPELLS))
            ArmEnhTimer(player, false);

        if (HasAnyOwnAura(player, SINGLE_ASCENDANCES))
            ArmEnhTimer(player, true);
    }

    void OnStormstrikeLanded(Player* player, Unit* target, uint32 landedDamage)
    {
        if (!IsUsablePlayer(player) || !target || !target->IsAlive() || !landedDamage)
            return;

        int32 const amount = int32(uint64(landedDamage) * uint64(ShamanData::FROST_COPY_PCT) / 100);
        if (amount <= 0)
            return;

        // The player's own controlled minions of the Frost Spirit entry (owner and entry checked, L-12). The wolf casts
        // the copy, so it rolls none of the shaman's procs and carries no Stormstrike debuff.
        std::list<Creature*> wolves;
        player->GetAllMinionsByEntry(wolves, ShamanData::NPC_FROST_SPIRIT);
        for (Creature* wolf : wolves)
        {
            if (!wolf || !wolf->IsInWorld() || !wolf->IsAlive() || !wolf->IsValidAttackTarget(target))
                continue;

            LogEnhCastFailure("Frost Spirit copy", ShamanData::SPELL_FROST_SPIRIT_COPY, wolf, target,
                wolf->CastCustomSpell(ShamanData::SPELL_FROST_SPIRIT_COPY, SPELLVALUE_BASE_POINT0, amount, target,
                    TRIGGERED_FULL_MASK));
        }
    }

    int32 GetStoneskinAmount(Player const* player, uint8 stacks)
    {
        if (!stacks)
            return 0;

        // The row's per-stack value (-1 = 1% less damage taken per stack).
        int32 perStack = -1;
        if (SpellInfo const* info = sSpellMgr->GetSpellInfo(ShamanData::SPELL_STONESKIN_202206))
            for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
                if (info->Effects[i].IsAura(SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN))
                {
                    perStack = info->Effects[i].CalcValue(player);
                    break;
                }

        // Ascendance capstone: 1% x (1 + Mastery) per stack, rounded once on the total (the cap stays 50 stacks, so
        // the total can pass 50% at high Mastery, by design).
        double const mastery = player ? double(GetAscendanceMasteryPct(player)) : 0.0;
        return int32(std::lround(double(perStack) * double(stacks) * (1.0 + mastery / 100.0)));
    }

    void OnRockbiterChanged(Player* player, bool applied)
    {
        // Login aura load (not in world): OnPlayerLogin reconciles through OnEnhTalentsChanged.
        if (!IsUsablePlayer(player))
            return;

        SyncRockbiterChildren(player, applied);
        UpdateUnleashedRage(player);
    }

    void OnEnhTalentsChanged(Player* player)
    {
        if (!IsUsablePlayer(player))
            return;

        if (!GetTalentRank(player, ELEMENTAL_CHARGE_RANKS))
        {
            for (uint32 const spellId : CHARGE_SPELLS)
                RemoveOwnAura(player, spellId);

            if (EnhancementState* state = FindEnhancementState(player))
                state->bankedCharges = 0;
        }

        if (!GetTalentRank(player, ASCENDANCE_RANKS))
        {
            for (uint32 const spellId : SINGLE_ASCENDANCES)
                RemoveOwnAura(player, spellId);

            RemoveOwnAura(player, ShamanData::SPELL_ELEMENTAL_ASCENDANCE);
            RemoveOwnAura(player, ShamanData::SPELL_EARTHEN_ASCENDANCE);
        }

        SyncRockbiterChildren(player, player->HasAura(ShamanData::SPELL_ROCKBITER_WEAPON, player->GetGUID()));
        UpdateUnleashedRage(player);
        RefreshAscendance(player);

        // WP-R m1: (re)start the live-Mastery loop; a teleport may have killed the old one with the player's events.
        StartAscendanceRefresh(player, true);
    }

    void OnEnhPlayerDied(Player* player)
    {
        if (!player)
            return;

        if (EnhancementState* state = FindEnhancementState(player))
        {
            state->bankedCharges = 0;
            state->stashedImbue = 0;
        }

        UpdateUnleashedRage(player);
    }
}
