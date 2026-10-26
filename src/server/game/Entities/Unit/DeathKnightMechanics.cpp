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

#include "DeathKnightMechanics.h"
#include "Creature.h"
#include "DataMap.h"
#include "GameTime.h"
#include "Item.h"
#include "ItemTemplate.h"
#include "ObjectAccessor.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "TemporarySummon.h"
#include "Unit.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <deque>
#include <initializer_list>
#include <limits>
#include <list>
#include <unordered_map>
#include <vector>

/*
 * DK0a block (docs/reworks/death-knight-shared-rework.md): the Death Strike damage-taken record and heal, the
 * Pestilence copy hook (empty until S3) and the Anti-Magic Zone shared pool (U12). Per-player and per-zone state lives
 * in CustomData: it belongs to the object's map thread, needs no lock, and dies with the object (a relog builds a new
 * Player, a recast summons a new zone), so nothing can go stale across sessions.
 */
namespace
{
    // Hits closer together than this share one record entry (the entry keeps the first hit's time). Bounds the record
    // to DEATH_STRIKE_WINDOW_MS / RECORD_COALESCE_MS + 1 entries however many hits land (AoE, DoTs, many attackers);
    // the cost is that up to this much damage at the window's far edge may drop out of the sum early.
    constexpr int64 RECORD_COALESCE_MS = 100;

    struct DamageTakenEntry
    {
        int64 timeMs;   // GameTime ms of the entry's first hit (monotonic, server-uptime based, no wrap)
        uint64 amount;
    };

    struct DamageTakenRecord : DataMap::Base
    {
        std::deque<DamageTakenEntry> entries;
    };

    constexpr char const* DAMAGE_TAKEN_RECORD_KEY = "deathknight_damage_taken_record";

    struct ZoneAbsorbPool : DataMap::Base
    {
        bool initialised = false;
        bool depleted = false;   // reached 0 and the unsummon is scheduled; every later call absorbs nothing
        uint64 remaining = 0;
    };

    constexpr char const* ZONE_ABSORB_POOL_KEY = "deathknight_amz_pool";

    // S3 helpers defined in the S3 block below (one anonymous namespace per translation unit).
    void CastOnAPaleHorse(Player* dk, Unit* target);
    void RampGargoyle(Player* dk, int32 internalRp);

    int64 NowMs()
    {
        return int64(GameTime::GetGameTimeMS().count());
    }

    void PruneRecord(DamageTakenRecord& record, int64 now)
    {
        int64 const window = int64(std::max<int32>(0, DeathKnightData::DEATH_STRIKE_WINDOW_MS));
        while (!record.entries.empty() && record.entries.front().timeMs + window < now)
            record.entries.pop_front();
    }

    uint32 ClampToUInt32(uint64 value)
    {
        return uint32(std::min<uint64>(value, std::numeric_limits<uint32>::max()));
    }

    // The pool's starting size (brief ruling 10): 50461's flat (level-scaled base through the owner, potency correction
    // included) plus the generated AP coefficient x the owner's attack power. The engine adds neither SP nor AP to a
    // SCHOOL_ABSORB amount, so both parts are read here; without the spell_bonus_data row it is the flat only.
    uint64 ComputeInitialZonePool(Player const* owner)
    {
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_ANTI_MAGIC_ZONE);
        if (!spellInfo)
            return 0;

        float amount = float(std::max<int32>(0, spellInfo->Effects[EFFECT_0].CalcValue(owner)));
        if (SpellBonusEntry const* bonus = sSpellMgr->GetSpellBonusData(DeathKnightData::SPELL_ANTI_MAGIC_ZONE))
            if (bonus->ap_bonus > 0.0f)
                amount += bonus->ap_bonus * owner->GetTotalAttackPowerValue(BASE_ATTACK);

        return uint64(std::max(0.0f, amount));
    }
}

namespace DeathKnight
{
    bool TracksDamageTaken(Player const* player)
    {
        return player && player->HasSpell(DeathKnightData::SPELL_DEATH_STRIKE);
    }

    void RecordDamageTaken(Player* player, uint32 amount)
    {
        if (!player || !amount)
            return;

        DamageTakenRecord* record = player->CustomData.GetDefault<DamageTakenRecord>(DAMAGE_TAKEN_RECORD_KEY);
        int64 const now = NowMs();
        PruneRecord(*record, now);

        if (!record->entries.empty() && record->entries.back().timeMs + RECORD_COALESCE_MS > now)
            record->entries.back().amount += amount;
        else
            record->entries.push_back({ now, amount });
    }

    uint32 GetRecordedDamage(Player* player)
    {
        if (!player)
            return 0;

        // Get, not GetDefault: a player who was never hit has no record and needs none allocated.
        DamageTakenRecord* record = player->CustomData.Get<DamageTakenRecord>(DAMAGE_TAKEN_RECORD_KEY);
        if (!record)
            return 0;

        PruneRecord(*record, NowMs());

        uint64 total = 0;
        for (DamageTakenEntry const& entry : record->entries)
            total += entry.amount;

        return ClampToUInt32(total);
    }

    uint32 ComputeDeathStrikeHeal(Player* player, int32 healPct)
    {
        if (!player)
            return 0;

        uint64 const fromRecord = uint64(GetRecordedDamage(player)) * uint64(std::max<int32>(0, healPct)) / 100;
        int32 const minPct = std::max<int32>(0, DeathKnightData::DEATH_STRIKE_MIN_HEAL_PCT);
        uint64 const floor = player->CountPctFromMaxHealth(minPct);
        return ClampToUInt32(std::max(fromRecord, floor));
    }

    void OnPestilenceCopy(Player* dk, Unit* source, Unit* target)
    {
        // Pestilence's copy rules (skip a target that already has the caster's disease, no Glyph of Disease refresh)
        // live in spell_dk_pestilence_rework, which calls this once per engaged non-primary enemy. S3 (U26): half the
        // primary's wounds (rounded down) through the helper (an overflow there deals damage only), then On a Pale
        // Horse's damage on this enemy.
        if (!dk || !source || !target || !target->IsAlive())
            return;

        uint8 const wounds = GetFesteringWounds(source, dk->GetGUID()) / 2;
        if (wounds)
            AddFesteringWounds(dk, target, wounds, WoundSource::Pestilence);

        CastOnAPaleHorse(dk, target);
    }

    uint32 ConsumeZoneAbsorb(Unit* zone, Player* owner, uint32 wanted)
    {
        if (!zone || !wanted)
            return 0;

        ZoneAbsorbPool* pool = zone->CustomData.GetDefault<ZoneAbsorbPool>(ZONE_ABSORB_POOL_KEY);
        if (pool->depleted)
            return 0;

        if (!pool->initialised)
        {
            // The first absorb sizes the pool from the owner (the DK who placed the zone). Without an owner there is
            // nothing to size it from: absorb nothing this time and try again on the next hit.
            if (!owner)
                return 0;

            pool->remaining = ComputeInitialZonePool(owner);
            pool->initialised = true;
        }

        uint64 const absorbed = std::min<uint64>(wanted, pool->remaining);
        pool->remaining -= absorbed;

        if (!pool->remaining)
        {
            pool->depleted = true;

            // Called from inside an OnEffectAbsorb handler of the zone's own area aura. TempSummon::UnSummon(0ms) goes
            // through Map::AddObjectToRemoveList -> CleanupsBeforeDelete -> RemoveAllAuras right now, which would
            // remove the very aura (and its applications on the party) whose absorb is being processed. A 1 ms delay
            // queues a ForcedUnsummonDelayEvent (ForcedDespawnDelayEvent for a non-summon) on the zone's own event
            // processor instead, so the removal runs in the zone's next Unit::Update, outside any damage/absorb stack.
            // `depleted` keeps the pool at 0 until then (the area aura may re-apply copies meanwhile).
            if (Creature* creature = zone->ToCreature())
                creature->DespawnOrUnsummon(1ms);
        }

        return uint32(absorbed);
    }
}

/*
 * DK0b block (shared doc "Haste and runes", "Runeforging and the six runes", §6): rune glows, the shared rune proc
 * guard, rune-regen haste (U4), the minion registry, live-stat mirror and damage seam (U8-U10), and Unending Thirst's
 * killing-blow grant (U14). The glow needs no state of its own: it is derived from the rune aura the player carries
 * (shaman imbue glow shape). The only DK0b state is the once-per-cast fallback below, on the rune owner's CustomData.
 */
namespace
{
    // The six rune self-auras (group 1271 rule 1: at most one is up).
    constexpr std::array<uint32, 6> RUNE_AURAS = {
        DeathKnightData::SPELL_RUNE_OF_THE_FALLEN_CRUSADER,
        DeathKnightData::SPELL_RUNE_OF_RAZORICE,
        DeathKnightData::SPELL_RUNE_OF_EXSANGUINATION,
        DeathKnightData::SPELL_RUNE_OF_BOILING_BLIGHT,
        DeathKnightData::SPELL_RUNE_OF_THE_APOCALYPSE,
        DeathKnightData::SPELL_RUNE_OF_UNENDING_THIRST,
    };

    constexpr std::array<uint8, 2> GLOW_SLOTS = { EQUIPMENT_SLOT_MAINHAND, EQUIPMENT_SLOT_OFFHAND };

    // A creature's melee crit starts at 5% (Unit::GetUnitCriticalChance); the mirror adds the owner's part above it.
    constexpr float CREATURE_BASE_CRIT_PCT = 5.0f;

    bool IsWeapon(Item const* item)
    {
        return item && item->GetTemplate()->Class == ITEM_CLASS_WEAPON;
    }

    uint16 ToGlowEnchant(int32 value)
    {
        return uint16(std::clamp<int32>(value, 0, std::numeric_limits<uint16>::max()));
    }

    // Once-per-cast fallback for a cast with no unit target (self-centred AoE such as Blood Boil): the first target
    // the calling aura's CheckProc is asked about is that aura's rolling target, every other target skips. The guard
    // is keyed by the calling aura id, so one aura's answer never claims the cast from another (an unfiltered aura
    // asking on target 1 cannot starve a crit-only aura that first asks on target 2; review S1a M2/m2). The guard
    // stores the target, not "a roll happened", so a repeated query for the same hit gets the same answer. Hits of one
    // cast land in the same server tick (Spell::DoAllEffectOnTarget), so the time stamp keeps a later cast that
    // reuses the address from matching.
    struct RuneCastEntry
    {
        Spell const* spell = nullptr;
        uint32 spellId = 0;
        int64 timeMs = -1;
        ObjectGuid firstTarget;
    };

    struct RuneCastGuard : DataMap::Base
    {
        std::unordered_map<uint32, RuneCastEntry> byAura;
    };

    constexpr char const* RUNE_CAST_GUARD_KEY = "deathknight_rune_cast_guard";

    // Amount write that re-handles the effect only when the value moved.
    void SetEffectAmount(Aura* aura, uint8 effIndex, int32 amount)
    {
        if (!aura)
            return;

        if (AuraEffect* effect = aura->GetEffect(effIndex))
            if (effect->GetAmount() != amount)
                effect->ChangeAmount(amount, false);
    }

    int32 SharePct(float value, int32 sharePct)
    {
        return int32(std::lround(value * float(sharePct) / 100.0f));
    }

    // The crit auras the minion already carries itself because the owner has them too (party buffs on a pet ghoul):
    // they already count once on the minion (hunter GetSharedCritBonus shape).
    float GetSharedCritBonus(Player const* owner, Unit const* minion)
    {
        auto const shared = [owner](AuraEffect const* auraEffect)
        {
            return auraEffect->GetId() != DeathKnightData::SPELL_MINION_MIRROR_CRIT_HASTE &&
                owner->HasAura(auraEffect->GetId());
        };

        return float(minion->GetTotalAuraModifier(SPELL_AURA_MOD_WEAPON_CRIT_PERCENT, shared) +
            minion->GetTotalAuraModifier(SPELL_AURA_MOD_CRIT_PCT, shared));
    }

    // Flat AP from auras the owner and the minion both carry (Battle Shout, Blessing of Might): they already count once
    // on a minion that isn't stat-immune. Guardians are immune to these auras, so this is 0 for them.
    float GetSharedAttackPowerBonus(Player const* owner, Unit const* minion)
    {
        auto const shared = [owner](AuraEffect const* auraEffect)
        {
            return auraEffect->GetId() != DeathKnightData::SPELL_MINION_MIRROR && owner->HasAura(auraEffect->GetId());
        };

        return float(minion->GetTotalAuraModifier(SPELL_AURA_MOD_ATTACK_POWER, shared));
    }

    // The owner's SPELL_AURA_MOD_DAMAGE_PERCENT_DONE product for one school, without weapon-restricted auras
    // (Unit::SpellPctDamageModsDone's item-class filter): what a minion hit of that school takes from the owner.
    float OwnerPctDamageDone(Player const* owner, uint32 schoolMask)
    {
        return owner->GetTotalAuraMultiplier(SPELL_AURA_MOD_DAMAGE_PERCENT_DONE, [schoolMask](AuraEffect const* aurEff)
        {
            if (aurEff->GetSpellInfo()->EquippedItemClass != -1)
                return false;

            return (uint32(aurEff->GetMiscValue()) & schoolMask) != 0;
        });
    }
}

namespace DeathKnight
{
    uint32 GetActiveRune(Player const* player)
    {
        if (!player)
            return 0;

        for (uint32 const spellId : RUNE_AURAS)
            if (player->HasAura(spellId))
                return spellId;

        return 0;
    }

    uint16 GetRuneGlowEnchant(uint32 runeSpellId)
    {
        switch (runeSpellId)
        {
            case DeathKnightData::SPELL_RUNE_OF_THE_FALLEN_CRUSADER:
                return ToGlowEnchant(DeathKnightData::RUNE_GLOW_FALLEN_CRUSADER);
            case DeathKnightData::SPELL_RUNE_OF_RAZORICE:
                return ToGlowEnchant(DeathKnightData::RUNE_GLOW_RAZORICE);
            case DeathKnightData::SPELL_RUNE_OF_EXSANGUINATION:
                return ToGlowEnchant(DeathKnightData::RUNE_GLOW_EXSANGUINATION);
            case DeathKnightData::SPELL_RUNE_OF_BOILING_BLIGHT:
                return ToGlowEnchant(DeathKnightData::RUNE_GLOW_BOILING_BLIGHT);
            case DeathKnightData::SPELL_RUNE_OF_THE_APOCALYPSE:
                return ToGlowEnchant(DeathKnightData::RUNE_GLOW_APOCALYPSE);
            case DeathKnightData::SPELL_RUNE_OF_UNENDING_THIRST:
                return ToGlowEnchant(DeathKnightData::RUNE_GLOW_UNENDING_THIRST);
            default:
                return 0;
        }
    }

    void ApplyRuneGlow(Player* player)
    {
        if (!player)
            return;

        for (uint8 const slot : GLOW_SLOTS)
            WriteRuneGlow(player, slot);
    }

    void WriteRuneGlow(Player* player, uint8 slot)
    {
        if (!player || (slot != EQUIPMENT_SLOT_MAINHAND && slot != EQUIPMENT_SLOT_OFFHAND))
            return;

        if (!IsWeapon(player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot)))
            return;

        // No rune, or a rune without a glow (U1): keep the real values (a stone or a real enchant stays visible).
        uint16 const enchantId = GetRuneGlowEnchant(GetActiveRune(player));
        if (!enchantId)
            return;

        // Only the temp half of the visible-item enchant field (PlayerStorage.cpp SetVisibleItemSlot): no item or DB
        // change, the item's real enchants stay on it.
        player->SetUInt16Value(PLAYER_VISIBLE_ITEM_1_ENCHANTMENT + (slot * 2), 1, enchantId);
    }

    void RestoreRuneGlow(Player* player)
    {
        if (!player)
            return;

        // SetVisibleItemSlot rewrites the real values; the visible-slot hook then re-applies the glow of whatever rune
        // is still up (the removed aura is already gone when AfterEffectRemove runs).
        for (uint8 const slot : GLOW_SLOTS)
            if (Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot))
                player->SetVisibleItemSlot(slot, item);
    }

    bool RuneProcAllowed(Unit const* runeOwner, ProcEventInfo& eventInfo, uint32 auraId, bool dualWieldHalf,
        bool oncePerCast)
    {
        Unit* actor = eventInfo.GetActor();
        if (!runeOwner || actor != runeOwner)
            return false;   // a minion's or anyone else's hit never rolls the DK's rune (no-proc rule, B4)

        // Periodic ticks carry no cast (GetProcSpell() is null for them and for auto attacks): every tick rolls.
        Spell const* spell = eventInfo.GetProcSpell();
        if (oncePerCast && spell && !(eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC))
        {
            if (Unit const* castTarget = spell->m_targets.GetUnitTarget())
            {
                // Heart Strike, Death's Caress, Pestilence: only the hit on the cast's own target rolls.
                if (castTarget != eventInfo.GetActionTarget())
                    return false;
            }
            else
            {
                RuneCastGuard* guard = actor->CustomData.GetDefault<RuneCastGuard>(RUNE_CAST_GUARD_KEY);
                uint32 const spellId = spell->GetSpellInfo() ? spell->GetSpellInfo()->Id : 0;
                int64 const now = NowMs();
                Unit const* actionTarget = eventInfo.GetActionTarget();
                ObjectGuid const targetGuid = actionTarget ? actionTarget->GetGUID() : ObjectGuid::Empty;
                RuneCastEntry& entry = guard->byAura[auraId];
                if (entry.spell == spell && entry.spellId == spellId && entry.timeMs == now)
                    return entry.firstTarget == targetGuid;   // same cast: only this aura's first target rolls

                entry.spell = spell;
                entry.spellId = spellId;
                entry.timeMs = now;
                entry.firstTarget = targetGuid;
            }
        }

        // Two weapons swing (and roll a PPM proc) about twice as often: halve the chance with a usable off-hand
        // weapon (a shield does not count, Unit::haveOffhandWeapon).
        if (dualWieldHalf && runeOwner->haveOffhandWeapon() && !roll_chance_i(50))
            return false;

        return true;
    }

    int32 GetRuneHastePct(Player const* player)
    {
        if (!player)
            return 0;

        // The custom_haste_gcd.cpp read: UNIT_MOD_CAST_SPEED holds haste rating, casting-speed and combat-speed auras.
        // A net slow clamps to 0 (a slow never lengthens rune regen), the cap is RUNE_HASTE_MAX_PCT.
        float const castSpeed = player->GetFloatValue(UNIT_MOD_CAST_SPEED);
        if (castSpeed <= 0.0f)
            return 0;

        int32 const maxPct = std::clamp<int32>(DeathKnightData::RUNE_HASTE_MAX_PCT, 0, 99);
        return std::clamp<int32>(int32(std::lround(100.0f - 100.0f * castSpeed)), 0, maxPct);
    }

    void SyncRuneHaste(Player* player, Aura* runeHaste)
    {
        if (!player || !runeHaste)
            return;

        // InitRunes' own test: m_runes is null for anyone else, and the rune accessors dereference it unguarded.
        if (!player->IsClass(CLASS_DEATH_KNIGHT, CLASS_CONTEXT_ABILITY))
            return;

        int32 const pct = GetRuneHastePct(player);

        // The current amount per base rune type (203052: three aura-110 effects, misc POWER_RUNE, MiscValueB 0/1/2).
        std::array<int32, NUM_RUNE_TYPES> oldPct = { };
        bool changed = false;
        for (uint8 i = EFFECT_0; i <= EFFECT_2; ++i)
        {
            AuraEffect const* effect = runeHaste->GetEffect(i);
            if (!effect || effect->GetAuraType() != SPELL_AURA_MOD_POWER_REGEN_PERCENT ||
                effect->GetMiscValue() != POWER_RUNE)
                continue;

            int32 const runeType = effect->GetMiscValueB();
            if (runeType < 0 || runeType >= NUM_RUNE_TYPES)
                continue;

            oldPct[runeType] = effect->GetAmount();
            if (effect->GetAmount() != pct)
                changed = true;
        }

        if (!changed)
            return;

        // (a) First rescale every recharging rune by its own base type's old rate, so it finishes at the new one: the
        // remaining cooldown counts down unhasted (Player::RegenerateAll), the rate lives only in the cooldown set at
        // spend time (GetRuneBaseCooldown). Death Runes use their base type. Never ResyncRunes (255 - ms x 51
        // overflows above 5 s).
        for (uint8 slot = 0; slot < MAX_RUNES; ++slot)
        {
            uint32 const cooldown = player->GetRuneCooldown(slot);
            if (!cooldown)
                continue;

            uint8 const baseRune = uint8(player->GetBaseRune(slot));
            if (baseRune >= NUM_RUNE_TYPES)
                continue;

            int32 const old = oldPct[baseRune];
            if (old == pct || old >= 100)
                continue;

            uint64 const rescaled = uint64(cooldown) * uint64(100 - pct) / uint64(100 - old);
            player->SetRuneCooldown(slot, uint32(std::clamp<uint64>(rescaled, 1, std::numeric_limits<uint32>::max())));
        }

        // (b) Then the new rate: CHANGE_AMOUNT -> HandleModPowerRegen -> UpdateRuneRegen -> PLAYER_RUNE_REGEN_n.
        for (uint8 i = EFFECT_0; i <= EFFECT_2; ++i)
            if (AuraEffect* effect = runeHaste->GetEffect(i))
                if (effect->GetAuraType() == SPELL_AURA_MOD_POWER_REGEN_PERCENT &&
                    effect->GetMiscValue() == POWER_RUNE && effect->GetAmount() != pct)
                    effect->ChangeAmount(pct, false);
    }

    MinionKind GetMinionKind(Unit const* unit)
    {
        if (!unit || !unit->IsCreature())
            return MinionKind::None;

        switch (unit->GetEntry())
        {
            case 26125:     // Risen Ghoul: Raise Dead guardian or the Master of Ghouls pet
                return MinionKind::Ghoul;
            case 24207:     // Army of the Dead ghoul
                return MinionKind::ArmyGhoul;
            case 27829:     // Ebon Gargoyle
                return MinionKind::Gargoyle;
            case 28017:     // Bloodworm
                return MinionKind::Bloodworm;
            case DeathKnightData::NPC_LESSER_GHOUL:
                return MinionKind::LesserGhoul;
            case DeathKnightData::NPC_ABOMINATION:
                return MinionKind::Abomination;
            default:        // Dancing Rune Weapon 27893 included: its damage is core-live (B6)
                return MinionKind::None;
        }
    }

    Player* GetMinionOwner(Unit const* minion)
    {
        if (!minion)
            return nullptr;

        // GetOwner, never GetOwningPlayer: that one is null until SetMinion (bug log, hunter pet hooks). No class check
        // (Classless-ready).
        Unit* owner = minion->GetOwner();
        return owner ? owner->ToPlayer() : nullptr;
    }

    void ApplyMinionMirror(Guardian* minion)
    {
        if (GetMinionKind(minion) == MinionKind::None)
            return;

        Player* owner = GetMinionOwner(minion);
        if (!owner)
            return;

        // The owner applies the auras (a minion-cast copy of a pet's aura would be saved to pet_aura). Their target is
        // the caster (TargetA 1), so a CastSpell from the owner would land on the owner: AddAura targets the minion
        // directly (hunter RefreshPetPassthrough shape). ALWAYS_HIT (AttributesEx3 0x40000) lets every effect past the
        // stock IMMUNITY_STATE block (Unit::IsImmunedToSpellEffect).
        for (uint32 const spellId : { DeathKnightData::SPELL_MINION_MIRROR,
            DeathKnightData::SPELL_MINION_MIRROR_CRIT_HASTE, DeathKnightData::SPELL_MINION_MIRROR_VERSATILITY })
            if (!minion->GetAura(spellId, owner->GetGUID()))
                owner->AddAura(spellId, minion);

        // The amounts are stored 0: fill them now instead of waiting for the first 1 s tick.
        RefreshMinionMirror(minion, owner);
    }

    void RefreshMinionMirror(Unit* minion, Player* owner)
    {
        if (!minion || !owner)
            return;

        MinionKind const kind = GetMinionKind(minion);
        if (kind == MinionKind::None)
            return;

        ObjectGuid const ownerGuid = owner->GetGUID();

        // 203056: eff0 attack power (per-kind share, S3 D12: the ghoul kind minus its own base AP), eff1 spell power
        // (Gargoyle only), both from the owner's total melee attack power.
        // The pet ghoul is a real Pet with no stat immunities, so party AP buffs the owner also has already count once
        // on it: leave them out of the copy (same shape as GetSharedCritBonus).
        float const ownerAp = std::max(0.0f, owner->GetTotalAttackPowerValue(BASE_ATTACK) -
            GetSharedAttackPowerBonus(owner, minion));
        if (Aura* mirror = minion->GetAura(DeathKnightData::SPELL_MINION_MIRROR, ownerGuid))
        {
            SetEffectAmount(mirror, EFFECT_0, GetMinionMirrorAttackPower(owner, minion));
            int32 const spellPower = kind == MinionKind::Gargoyle ?
                std::max<int32>(0, SharePct(ownerAp, DeathKnightData::MINION_SP_SHARE_PCT)) : 0;
            SetEffectAmount(mirror, EFFECT_1, spellPower);
        }

        // 203057: eff0 crit points above the creature base, minus buffs the minion carries itself; eff1 the owner's
        // spell haste (UNIT_MOD_CAST_SPEED, never attack speed). The minion's own haste buffs are blocked by the stock
        // aura 192/193 immunity the passthrough keeps, so nothing is counted twice.
        if (Aura* critHaste = minion->GetAura(DeathKnightData::SPELL_MINION_MIRROR_CRIT_HASTE, ownerGuid))
        {
            float const ownerCrit = owner->GetFloatValue(PLAYER_CRIT_PERCENTAGE);
            float const critShare = ownerCrit - CREATURE_BASE_CRIT_PCT - GetSharedCritBonus(owner, minion);
            int32 const crit = std::max<int32>(0, SharePct(critShare, DeathKnightData::MINION_CRIT_SHARE_PCT));
            SetEffectAmount(critHaste, EFFECT_0, crit);
            // D2 reversed: eff2 aura 71 (misc 126) gives the creature's magic-class spell crit the same share.
            SetEffectAmount(critHaste, EFFECT_2, crit);

            float const castSpeed = owner->GetFloatValue(UNIT_MOD_CAST_SPEED);
            float const hastePct = castSpeed > 0.0f ? (1.0f / castSpeed - 1.0f) * 100.0f : 0.0f;
            SetEffectAmount(critHaste, EFFECT_1,
                std::max<int32>(0, SharePct(hastePct, DeathKnightData::MINION_HASTE_SHARE_PCT)));
        }

        // 203058: eff0 +V damage done, eff1 -V/2 damage taken, eff2 +V healing done (hunter 201700 shape).
        if (Aura* versatility = minion->GetAura(DeathKnightData::SPELL_MINION_MIRROR_VERSATILITY, ownerGuid))
        {
            float const shared = owner->GetVersatilityPercentage() *
                float(DeathKnightData::MINION_VERSATILITY_SHARE_PCT) / 100.0f;
            SetEffectAmount(versatility, EFFECT_0, int32(std::lround(shared)));
            SetEffectAmount(versatility, EFFECT_1, -int32(std::lround(shared / 2.0f)));
            SetEffectAmount(versatility, EFFECT_2, int32(std::lround(shared)));
        }
    }

    float GetMinionDamageMultiplier(Player const* owner, Unit const* minion, SpellInfo const* spellInfo)
    {
        // U10 seam. S1 (U17): a Bloodworm's swing takes the owner's physical percent damage bonuses (Blood Gorged,
        // Bloody Vengeance, Blood Presence...) read live, skipping weapon-restricted auras such as Two-Handed Weapon
        // Specialization (Unit::SpellPctDamageModsDone's item-class filter). Versatility is mirrored separately
        // (203058). S3 (U16): the Unholy kinds take the Unholy terms (GetUnholyMinionTerms); Bloodworms and the
        // Dancing Rune Weapon (None) never do.
        if (!owner)
            return 1.0f;

        MinionKind const kind = GetMinionKind(minion);
        if (kind == MinionKind::Bloodworm)
            return OwnerPctDamageDone(owner, SPELL_SCHOOL_MASK_NORMAL);

        if (!IsUnholyMinion(kind))
            return 1.0f;

        // The Dark Transformation cleave is built from an already-boosted hit.
        if (spellInfo && spellInfo->Id == DeathKnightData::SPELL_DARK_TRANSFORMATION_CLEAVE)
            return 1.0f;

        return GetUnholyMinionTerms(owner, spellInfo);
    }

    void OnRuneKillingBlow(Player* dk, Unit* killed)
    {
        if (!dk || !killed || killed == dk)
            return;

        // U14: critters and totems are no kill, nor is the DK's own ghoul or minion (Death Pact's INSTAKILL).
        if (killed->IsCritter() || killed->IsTotem() || killed->GetCharmerOrOwnerGUID() == dk->GetGUID())
            return;

        if (!dk->HasAura(DeathKnightData::SPELL_RUNE_OF_UNENDING_THIRST))
            return;

        // "Your killing blows always" grant the buff: the rune's 30 s proc cooldown gates only the crit proc.
        dk->CastSpell(dk, DeathKnightData::SPELL_UNENDING_THIRST, true);
    }
}

// ---- S1 ----
/*
 * S1 block (docs/reworks/death-knight-blood-rework.md): Bone Shield charges, Blood Shield (U7), Purgatory (U9), the
 * Voracious capstone and the two leeches (U5, U6, U21), Red Thirst (U22), Blood Gorged (U13, U18), the Bloodworm cap
 * and damage term (U16, U17) and the Dancing Rune Weapon copy list (U15). Per-player state (Purgatory's attacker, the
 * Blood Gorged snapshots) lives on CustomData, nothing file-static.
 */
namespace
{
    // _masks.py DK_SELF_HEAL (d2 b15): the own Death Knight self-heal group the Voracious capstone reads. The generated
    // header exports no masks, so it is mirrored here.
    constexpr uint32 DK_SELF_HEAL_MASK_D2 = 0x8000;

    // Stock ids C++ reads that the DSL does not declare (brief "Other stock ids").
    constexpr uint32 SPELL_DEATH_AND_DECAY_TICK = 52212;
    constexpr uint32 SPELL_MARK_OF_BLOOD_HEAL = 61607;
    constexpr uint32 NPC_DANCING_RUNE_WEAPON = 27893;

    // The three Blood Gorged damage passives (rank 1..3), learned by the talent ranks 61154/61155/61156.
    constexpr std::array<uint32, 3> BLOOD_GORGED_PASSIVES = {
        DeathKnightData::SPELL_BLOOD_GORGED,
        DeathKnightData::SPELL_BLOOD_GORGED_50108,
        DeathKnightData::SPELL_BLOOD_GORGED_50109,
    };

    struct PurgatoryState : DataMap::Base
    {
        ObjectGuid attacker;   // the unit whose hit Purgatory stopped; the killer when the Shroud expires unhealed
    };

    constexpr char const* PURGATORY_STATE_KEY = "deathknight_purgatory";

    // U13: Blood Gorged's multiplier at the cast of Death and Decay (43265) or Bonestorm (203148), keyed by that id.
    struct BloodGorgedSnapshots : DataMap::Base
    {
        std::unordered_map<uint32, float> multiplierBySpell;
    };

    constexpr char const* BLOOD_GORGED_SNAPSHOT_KEY = "deathknight_blood_gorged_snapshots";

    int32 ClampToInt32(uint64 value)
    {
        return int32(std::min<uint64>(value, uint64(std::numeric_limits<int32>::max())));
    }

    bool KnowsVoraciousCapstone(Unit const* unit)
    {
        // Talent ranks are auras, not HasSpell (custom-spells.md); the top rank is the capstone.
        return unit && unit->IsPlayer() && unit->HasAura(DeathKnightData::SPELL_VORACIOUS_203139);
    }

    // The Blood Gorged damage multiplier the engine applies right now: the passive's MOD_DAMAGE_PERCENT_DONE counts
    // only while AURA_STATE_HEALTH_ABOVE_75_PERCENT is on (CasterAuraState 23 handles the effect in and out,
    // Unit::ModifyAuraState).
    float LiveBloodGorgedMultiplier(Unit const* dk)
    {
        if (!dk->HasAuraState(AURA_STATE_HEALTH_ABOVE_75_PERCENT))
            return 1.0f;

        float multiplier = 1.0f;
        for (uint32 const spellId : BLOOD_GORGED_PASSIVES)
            if (AuraEffect const* effect = dk->GetAuraEffect(spellId, EFFECT_0))
                AddPct(multiplier, effect->GetAmount());

        return multiplier;
    }

    // Base percent of one damage passive: its DBC value (CalcValue), never the live amount the capstone overwrites.
    int32 PassiveBasePct(Player const* dk, uint32 spellId)
    {
        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        return spellInfo ? spellInfo->Effects[EFFECT_0].CalcValue(dk) : 0;
    }
}

namespace DeathKnight
{
    uint8 GetBoneShieldCharges(Unit const* unit)
    {
        if (!unit)
            return 0;

        Aura const* aura = unit->GetAura(DeathKnightData::SPELL_BONE_SHIELD);
        return aura ? aura->GetCharges() : 0;
    }

    bool AddBoneShieldCharges(Unit* dk, uint8 add)
    {
        if (!dk || !add)
            return false;

        int32 const maxCharges = std::clamp<int32>(int32(DeathKnightData::BONE_SHIELD_MAX_CHARGES), 1,
            std::numeric_limits<uint8>::max());

        // 0-verify item 10: a re-cast resets the charges to ProcCharges (3) and ModCharges caps there too, so the count
        // is written with SetCharges. A missing shield is added as an aura (no cast: no cooldown, no rune cost) and
        // starts from 0 charges here, whatever it was created with.
        Aura* aura = dk->GetAura(DeathKnightData::SPELL_BONE_SHIELD, dk->GetGUID());
        int32 const before = aura ? aura->GetCharges() : 0;
        if (aura && before >= maxCharges)
        {
            aura->RefreshDuration();
            return true;
        }

        if (!aura)
            aura = dk->AddAura(DeathKnightData::SPELL_BONE_SHIELD, dk);

        if (!aura)
            return false;

        aura->SetCharges(uint8(std::min<int32>(before + add, maxCharges)));
        aura->RefreshDuration();
        return false;
    }

    void GrantBloodShield(Player* dk, uint32 amount)
    {
        if (!dk || !amount || !dk->IsAlive())
            return;

        // U7: the cap follows the current max health (Vampiric Blood raises it), GrantStormsBulwark shape.
        int32 const capPct = std::max<int32>(0, int32(DeathKnightData::BLOOD_SHIELD_CAP_PCT));
        int32 const cap = int32(std::min<uint32>(dk->CountPctFromMaxHealth(capPct),
            uint32(std::numeric_limits<int32>::max())));
        if (cap <= 0)
            return;

        int32 const add = ClampToInt32(amount);
        if (Aura* aura = dk->GetAura(DeathKnightData::SPELL_BLOOD_SHIELD, dk->GetGUID()))
        {
            if (AuraEffect* effect = aura->GetEffect(EFFECT_0))
            {
                // Never shrink a shield that already sits above a cap lowered since (max health fell).
                int32 const current = effect->GetAmount();
                int32 const raised = int32(std::min<int64>(int64(current) + add, cap));
                effect->SetAmount(std::max(current, raised));
            }

            aura->RefreshDuration();
            return;
        }

        // BASE_POINT0 is a live value; 203151 has DmgClass NONE and no bonus row, so nothing is added on top.
        dk->CastCustomSpell(DeathKnightData::SPELL_BLOOD_SHIELD, SPELLVALUE_BASE_POINT0, std::min(add, cap), dk,
            TRIGGERED_FULL_MASK);
    }

    void OnDeathStrikeHealFinal(Player* dk, uint32 heal, uint32 effective, uint32 healAbsorbed)
    {
        if (!dk || !heal)
            return;

        // Improved Death Strike rank 2 (62908) is the capstone; talent ranks are auras.
        if (!dk->HasAura(DeathKnightData::SPELL_IMPROVED_DEATH_STRIKE_62908))
            return;

        // A heal absorb (Purgatory's Shroud) ate part of the heal: it fills first and converts nothing.
        if (healAbsorbed > 0)
            return;

        if (heal <= effective)
            return;

        GrantBloodShield(dk, heal - effective);
    }

    bool TryPurgatory(Player* dk, Unit* attacker, uint32& damage)
    {
        if (!dk || !damage || !dk->IsAlive())
            return false;

        uint32 const health = dk->GetHealth();
        if (damage < health)
            return false;

        if (!dk->HasAura(DeathKnightData::SPELL_PURGATORY) || dk->HasAura(DeathKnightData::SPELL_PURGATORY_LOCKOUT))
            return false;

        // Unit::DealDamage ends a duel instead of killing when the opponent (or its minion) lands the hit, and
        // .cheat god never dies: both are decided later, leave them alone (P0 m3).
        if (dk->GetCommandStatus(CHEAT_GOD))
            return false;

        if (dk->duel && attacker && dk->duel->Opponent &&
            (dk->duel->Opponent == attacker || dk->duel->Opponent->GetGUID() == attacker->GetOwnerGUID()))
            return false;

        // The lockout must land, or Purgatory would save again on the next hit (NO_IMMUNITIES, P0 m3).
        dk->CastSpell(dk, DeathKnightData::SPELL_PURGATORY_LOCKOUT, TRIGGERED_FULL_MASK);
        if (!dk->HasAura(DeathKnightData::SPELL_PURGATORY_LOCKOUT))
            return false;

        uint32 const kept = health > 0 ? health - 1 : 0;
        uint64 const prevented = std::min<uint64>(uint64(damage) - kept, dk->GetMaxHealth());

        // The GM .damage path is DealDamage(player, player, ...): attacker == victim is kept as the stored killer.
        PurgatoryState* state = dk->CustomData.GetDefault<PurgatoryState>(PURGATORY_STATE_KEY);
        state->attacker = attacker ? attacker->GetGUID() : ObjectGuid::Empty;

        dk->CastCustomSpell(DeathKnightData::SPELL_SHROUD_OF_PURGATORY, SPELLVALUE_BASE_POINT0, ClampToInt32(prevented),
            dk, TRIGGERED_FULL_MASK);

        // No Shroud (an immunity): no save either, or the DK would live at 1 HP with nothing to kill them at expiry
        // (review S1a m2). The lockout stays spent.
        if (!dk->HasAura(DeathKnightData::SPELL_SHROUD_OF_PURGATORY))
        {
            dk->CustomData.Erase(PURGATORY_STATE_KEY);
            return false;
        }

        damage = kept;
        return true;
    }

    void OnShroudExpired(Unit* target, int32 unhealed)
    {
        if (!target)
            return;

        // Read and clear the stored attacker in every case, so a filled Shroud leaves nothing behind.
        ObjectGuid attackerGuid;
        if (PurgatoryState* state = target->CustomData.Get<PurgatoryState>(PURGATORY_STATE_KEY))
        {
            attackerGuid = state->attacker;
            target->CustomData.Erase(PURGATORY_STATE_KEY);
        }

        if (unhealed <= 0 || !target->IsAlive())
            return;

        Unit* killer = attackerGuid ? ObjectAccessor::GetUnit(*target, attackerGuid) : nullptr;
        Unit::Kill(killer ? killer : target, target);
    }

    bool IsOwnDeathKnightHeal(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false;

        // Mark of Blood's heal (family 4, cast by the marked enemy) and Death Pact by id; the rest by the d2 b15 group.
        if (spellInfo->Id == SPELL_MARK_OF_BLOOD_HEAL || spellInfo->Id == DeathKnightData::SPELL_DEATH_PACT)
            return true;

        return spellInfo->SpellFamilyName == SPELLFAMILY_DEATHKNIGHT &&
            (spellInfo->SpellFamilyFlags[2] & DK_SELF_HEAL_MASK_D2);
    }

    void ApplyVoraciousCapstone(Unit* first, Unit* second, uint32& heal, SpellInfo const* spellInfo, bool periodic)
    {
        if (!heal || !first || !second || !IsOwnDeathKnightHeal(spellInfo))
            return;

        // Who is the receiver? UnitScript::ModifyHealReceived(target, healer, ...) arrives swapped on the direct path
        // (Unit::HealBySpell passes `this` = the healer first) and in order on the periodic path. The caller passes
        // (first, second) exactly as the hook delivered them. Rule:
        //  0. Mark of Blood's heal 61607 (cast by the marked enemy on whoever it hit) is always a direct heal: the
        //     receiver is the second argument, whatever the first one knows (a marked capstone DK is the healer here,
        //     never the receiver); return unless the receiver knows the capstone;
        //  1. otherwise the receiver is the one of the two that knows the capstone (a player with the 203139 aura);
        //  2. when both know it (a self heal, or two capstone DKs), the periodic flag decides: periodic -> in order
        //     (first = receiver), direct -> swapped (second = receiver);
        //  3. the heal must be the receiver's own: healer == receiver (every DK self heal, Death Pact, Crimson
        //     Communion's own share) or the receiver's minion (Bloodworm 50454 is cast by the worm). Another player's
        //     DK-family heal is never raised (Classless rule).
        Unit* receiver = nullptr;
        if (spellInfo->Id == SPELL_MARK_OF_BLOOD_HEAL)
        {
            if (!KnowsVoraciousCapstone(second))
                return;

            receiver = second;
        }
        else
        {
            bool const firstKnows = KnowsVoraciousCapstone(first);
            bool const secondKnows = KnowsVoraciousCapstone(second);
            if (!firstKnows && !secondKnows)
                return;

            Unit* healer = nullptr;
            if (firstKnows && secondKnows)
            {
                receiver = periodic ? first : second;
                healer = periodic ? second : first;
            }
            else if (firstKnows)
            {
                receiver = first;
                healer = second;
            }
            else
            {
                receiver = second;
                healer = first;
            }

            if (healer != receiver && healer->GetOwnerGUID() != receiver->GetGUID())
                return;
        }

        // "Mastery raises your own healing by its full value": applied last, after every other modifier the engine
        // already folded into heal.
        float const mastery = receiver->ToPlayer()->GetMasteryPercentage();
        if (mastery <= 0.0f)
            return;

        double const raised = double(heal) * (1.0 + double(mastery) / 100.0);
        heal = uint32(std::min<double>(raised, double(std::numeric_limits<uint32>::max())));
    }

    void OnDamageDealt(Unit* attacker, Unit* victim, uint32 damage)
    {
        // Runs for every hit in the world (Unit::DealDamage -> OnDamage, post-absorb): cheapest checks first. Only a
        // player's own hits leech, so minions (Bloodworms, Dancing Rune Weapon, ghouls) never do.
        if (!damage || !attacker || !victim || attacker == victim || !attacker->IsPlayer())
            return;

        // Voracious: the rank's DUMMY value is the leech percent (203139 the capstone rank, else 203138).
        AuraEffect const* voracious = attacker->GetAuraEffect(DeathKnightData::SPELL_VORACIOUS_203139, EFFECT_0);
        if (!voracious)
            voracious = attacker->GetAuraEffect(DeathKnightData::SPELL_VORACIOUS, EFFECT_0);

        // Crimson Communion: a party buff a Death Knight (a player) applied; the leech is the wearer's own heal.
        bool communion = false;
        if (Aura const* aura = attacker->GetAura(DeathKnightData::SPELL_CRIMSON_COMMUNION))
            communion = aura->GetCasterGUID().IsPlayer();

        // Almost no attacker has either: leave before the liveness and faction checks (IsFriendlyTo resolves faction
        // templates and duel/owner reactions).
        if (!voracious && !communion)
            return;

        if (!attacker->IsAlive() || victim->IsTotem() || attacker->IsFriendlyTo(victim))
            return;

        // The leech heals are TRIGGERED_FULL_MASK and SUPPRESS_CASTER_PROCS and deal no damage, so they never come back
        // here.
        if (voracious && voracious->GetAmount() > 0)
        {
            int32 const amount = ClampToInt32(uint64(damage) * uint64(voracious->GetAmount()) / 100);
            if (amount > 0)
                attacker->CastCustomSpell(DeathKnightData::SPELL_VORACIOUS_HEAL, SPELLVALUE_BASE_POINT0, amount,
                    attacker, TRIGGERED_FULL_MASK);
        }

        if (communion)
        {
            int32 const pct = std::max<int32>(0, int32(DeathKnightData::CRIMSON_COMMUNION_LEECH_PCT));
            int32 const amount = ClampToInt32(uint64(damage) * uint64(pct) / 100);
            if (amount > 0)
                attacker->CastCustomSpell(DeathKnightData::SPELL_CRIMSON_COMMUNION_HEAL, SPELLVALUE_BASE_POINT0,
                    amount, attacker, TRIGGERED_FULL_MASK);
        }
    }

    void OnRunicPowerSpent(Player* dk, Spell const* spell)
    {
        if (!dk || !spell || spell->IsTriggered())
            return;

        SpellInfo const* spellInfo = spell->GetSpellInfo();
        if (!spellInfo || spellInfo->PowerType != POWER_RUNIC_POWER)
            return;

        // GetPowerCost is in the internal unit (x10 the displayed runic power); a free cast (Sudden Doom) costs 0.
        int32 const cost = spell->GetPowerCost();
        if (cost <= 0)
            return;

        // S3 (U18, D10): the Gargoyle's ramp comes first, before the Red Thirst gates below.
        RampGargoyle(dk, cost);

        // Thick Blood rank 3 (203126) is Red Thirst; talent ranks are auras.
        if (!dk->HasAura(DeathKnightData::SPELL_THICK_BLOOD_203126))
            return;

        if (!dk->HasSpellCooldown(DeathKnightData::SPELL_VAMPIRIC_BLOOD))
            return;

        // RED_THIRST_MS_PER_10_RP per 10 displayed runic power = per 100 internal units; real ms (U22).
        int32 const msPer10 = std::max<int32>(0, int32(DeathKnightData::RED_THIRST_MS_PER_10_RP));
        uint64 const ms = uint64(cost) * uint64(msPer10) / 100;
        if (ms)
            dk->ModifySpellCooldown(DeathKnightData::SPELL_VAMPIRIC_BLOOD, -ClampToInt32(ms));
    }

    int32 GetBloodGorgedPct(Player const* dk)
    {
        if (!dk)
            return 0;

        // The rank's damage percent whatever the health state (BloodGorgedActiveAtCast says whether it counts). Rank 3
        // is the capstone: + Mastery x BLOOD_GORGED_MASTERY_SHARE_PCT %. The talent ranks 61154-61156 are LEARN_SPELL
        // rows that are never auras (review S1a M1), so the applied damage passive (50096 / 50108 / 50109) names the
        // rank; it stays applied below 75% health (ModifyAuraState only re-handles its effect).
        if (dk->HasAura(DeathKnightData::SPELL_BLOOD_GORGED_50109))
        {
            int32 const pct = PassiveBasePct(dk, DeathKnightData::SPELL_BLOOD_GORGED_50109) + int32(std::lround(
                dk->GetMasteryPercentage() * float(DeathKnightData::BLOOD_GORGED_MASTERY_SHARE_PCT) / 100.0f));
            return std::max<int32>(0, pct);
        }

        if (dk->HasAura(DeathKnightData::SPELL_BLOOD_GORGED_50108))
            return std::max<int32>(0, PassiveBasePct(dk, DeathKnightData::SPELL_BLOOD_GORGED_50108));

        if (dk->HasAura(DeathKnightData::SPELL_BLOOD_GORGED))
            return std::max<int32>(0, PassiveBasePct(dk, DeathKnightData::SPELL_BLOOD_GORGED));

        return 0;
    }

    void RefreshBloodGorged(Player* dk)
    {
        // Rank 3's damage passive is the capstone gate (not 61156, a LEARN_SPELL rank that is never an aura).
        if (!dk || !dk->HasAura(DeathKnightData::SPELL_BLOOD_GORGED_50109))
            return;

        AuraEffect* effect = dk->GetAuraEffect(DeathKnightData::SPELL_BLOOD_GORGED_50109, EFFECT_0);
        if (!effect)
            return;

        int32 const pct = GetBloodGorgedPct(dk);
        if (effect->GetAmount() == pct)
            return;

        // U18 trap: while the health state is off the effect is handled out (Unit::ModifyAuraState), and ChangeAmount
        // would unapply/apply it as if it were in; there only the stored amount moves, picked up when the state
        // returns.
        if (dk->HasAuraState(AURA_STATE_HEALTH_ABOVE_75_PERCENT))
            effect->ChangeAmount(pct, false);
        else
            effect->SetAmount(pct);
    }

    bool BloodGorgedActiveAtCast(Unit const* dk)
    {
        if (!dk || !dk->IsAlive())
            return false;

        // The value a D&D / Bonestorm cast snapshots (SnapshotBloodGorged): a damage passive is known and health is
        // above the threshold at this instant. The engine's live state (AURA_STATE_HEALTH_ABOVE_75_PERCENT) updates
        // once per Unit::Update, so the cast reads health directly.
        bool hasPassive = false;
        for (uint32 const spellId : BLOOD_GORGED_PASSIVES)
            if (dk->HasAura(spellId))
                hasPassive = true;

        return hasPassive && dk->HealthAbovePct(int32(DeathKnightData::BLOOD_GORGED_THRESHOLD_PCT));
    }

    void SnapshotBloodGorged(Player* dk, uint32 castSpellId)
    {
        if (!dk)
            return;

        float multiplier = 1.0f;
        if (BloodGorgedActiveAtCast(dk))
            AddPct(multiplier, GetBloodGorgedPct(dk));

        BloodGorgedSnapshots* snapshots = dk->CustomData.GetDefault<BloodGorgedSnapshots>(BLOOD_GORGED_SNAPSHOT_KEY);
        snapshots->multiplierBySpell[castSpellId] = multiplier;
    }

    float GetBloodGorgedTickMultiplier(Unit const* dk, uint32 castSpellId)
    {
        if (!dk)
            return 1.0f;

        BloodGorgedSnapshots const* snapshots = dk->CustomData.Get<BloodGorgedSnapshots>(BLOOD_GORGED_SNAPSHOT_KEY);
        if (!snapshots)
            return 1.0f;

        auto const itr = snapshots->multiplierBySpell.find(castSpellId);
        if (itr == snapshots->multiplierBySpell.end())
            return 1.0f;

        float const live = LiveBloodGorgedMultiplier(dk);
        return live > 0.0f ? itr->second / live : 1.0f;
    }

    void CapBloodworms(Player* dk)
    {
        // S3: the generic cap (CapMinions) with the Bloodworm entry and cap.
        CapMinions(dk, NPC_BLOODWORM, uint32(DeathKnightData::BLOODWORM_CAP));
    }

    bool IsRuneWeapon(Unit const* unit)
    {
        return unit && unit->IsCreature() && unit->GetEntry() == NPC_DANCING_RUNE_WEAPON;
    }

    bool IsRuneWeaponExcluded(uint32 spellId)
    {
        switch (spellId)
        {
            case DeathKnightData::SPELL_BLOOD_NOVA:
            case DeathKnightData::SPELL_BLOOD_NOVA_ERUPTION:
            case DeathKnightData::SPELL_BONESTORM:
            case DeathKnightData::SPELL_BONESTORM_TICK:
            case DeathKnightData::SPELL_DEATH_AND_DECAY:
            case SPELL_DEATH_AND_DECAY_TICK:
            case DeathKnightData::SPELL_GOREFIENDS_GRASP:
            case DeathKnightData::SPELL_CRIMSON_COMMUNION:
            case DeathKnightData::SPELL_PESTILENCE:
            case DeathKnightData::SPELL_DEATH_PACT:
            // S2 (U27): Frost's area, self and channel-like spells
            case DeathKnightData::SPELL_GLACIAL_ADVANCE:
            case DeathKnightData::SPELL_GLACIAL_ERUPTION:
            case DeathKnightData::SPELL_PILLAR_OF_FROST:
            case DeathKnightData::SPELL_BREATH_OF_SINDRAGOSA:
            case DeathKnightData::SPELL_BREATH_OF_SINDRAGOSA_TICK:
            case DeathKnightData::SPELL_FINAL_ROAR_BURST:
            case DeathKnightData::SPELL_HUNGERING_COLD_STORM:
            case DeathKnightData::SPELL_HUNGERING_COLD_TICK:
            // S3 (U30): Unholy summons, minion-cast and area spells
            case DeathKnightData::SPELL_DARK_TRANSFORMATION:
            case DeathKnightData::SPELL_RAISE_ABOMINATION:
            case DeathKnightData::SPELL_CORPSE_EXPLOSION:
            case DeathKnightData::SPELL_LESSER_GHOUL_SUMMON:
            case DeathKnightData::SPELL_CORPSE_EXPLOSION_DETONATION:
            case DeathKnightData::SPELL_ON_A_PALE_HORSE_DAMAGE:
                return true;
            default:
                return false;
        }
    }

    int32 GetMinionApSharePct(MinionKind kind)
    {
        // S1 U16 (user 2026-10-24: ~4 worms = 5% of Blood damage): Bloodworms keep stock damage plus their own share.
        // S3 U15 (user 2026-10-25: Army ghouls take only part of the owner's AP): one share per kind [tune]. The
        // Gargoyle keeps the full share (its spell power is MINION_SP_SHARE_PCT).
        switch (kind)
        {
            case MinionKind::Bloodworm:
                return int32(DeathKnightData::MINION_BLOODWORM_AP_SHARE_PCT);
            case MinionKind::ArmyGhoul:
                return int32(DeathKnightData::MINION_ARMY_AP_SHARE_PCT);
            case MinionKind::Ghoul:
                return int32(DeathKnightData::MINION_GHOUL_AP_SHARE_PCT);
            case MinionKind::LesserGhoul:
                return int32(DeathKnightData::MINION_LESSER_GHOUL_AP_SHARE_PCT);
            case MinionKind::Abomination:
                return int32(DeathKnightData::MINION_ABOMINATION_AP_SHARE_PCT);
            default:
                return int32(DeathKnightData::MINION_AP_SHARE_PCT);
        }
    }
}

// ---- S2 ----
/*
 * S2 block (docs/reworks/death-knight-frost-rework.md): the once-per-cast guard (moved from spell_dk_blood.cpp), the
 * per-cast school switch (U5), the Frost damage multiplier (U14/U17), Killing Machine / Enduring Strength (U6/U20),
 * Rime, rune refunds (U18), Deathchill (U9), Hungering Cold (U10) and the Breath helpers (U11/U12). Per-player state
 * (rune snapshot, Pillar extension, Final Roar store) lives on CustomData, nothing file-static.
 */
namespace
{
    // U5: Spell::m_spellSchoolMask is protected (Spell.h). A pointer to the protected member, formed inside a derived
    // class, may be applied to any Spell; this is legal C++ and fails to compile if upstream renames the member.
    struct SpellSchoolAccess : Spell
    {
        static SpellSchoolMask Spell::* Member() { return &SpellSchoolAccess::m_spellSchoolMask; }
    };

    // Deathchill lockout by rank (tooltip "Every 60/45/30 sec" [fixed]); the rank passives carry no duration value.
    constexpr std::array<uint32, 3> DEATHCHILL_RANKS = {
        DeathKnightData::SPELL_DEATHCHILL_203308,
        DeathKnightData::SPELL_DEATHCHILL_203309,
        DeathKnightData::SPELL_DEATHCHILL_203310,
    };
    constexpr std::array<int32, 3> DEATHCHILL_LOCKOUT_MS = { 60000, 45000, 30000 };

    // S3 D1: one per-DK rune snapshot (cooldown and CURRENT type per slot, keyed by the cast that took it). S2's
    // SnapshotRuneCooldowns (Obliterate OnCast) and S3's SnapshotRunes (Scourge / Plague Strike OnCast) both write it.
    struct RuneCooldownSnapshot : DataMap::Base
    {
        std::array<uint32, MAX_RUNES> cooldowns = { };
        std::array<uint8, MAX_RUNES> types = { };
        uint32 castSpellId = 0;
    };

    constexpr char const* RUNE_SNAPSHOT_KEY = "deathknight_rune_snapshot";

    // Enduring Strength: how much the Pillar of Frost aura that was applied at applyTime has been extended so far.
    struct PillarExtension : DataMap::Base
    {
        time_t applyTime = 0;
        int32 extendedMs = 0;
    };

    constexpr char const* PILLAR_EXTENSION_KEY = "deathknight_pillar_extension";

    struct FinalRoarStore : DataMap::Base
    {
        uint64 damage = 0;
    };

    constexpr char const* FINAL_ROAR_STORE_KEY = "deathknight_final_roar_store";

    // The amount of effIndex on the highest rank aura the unit carries (ranks listed highest first), or 0.
    int32 RankAmount(Unit const* unit, std::initializer_list<uint32> ranksHighestFirst, uint8 effIndex)
    {
        for (uint32 const spellId : ranksHighestFirst)
            if (AuraEffect const* effect = unit->GetAuraEffect(spellId, effIndex))
                return effect->GetAmount();

        return 0;
    }

    // Unit::GetDiseasesByCaster(caster) != 0 without the non-const call: a disease (dispel type) applied by the DK or
    // their Dancing Rune Weapon, through PERIODIC_DAMAGE (Frost Fever, Blood Plague) or LINKED (Crypt / Ebon Plague).
    bool HasOwnDisease(Player const* dk, Unit const* target)
    {
        ObjectGuid const dkGuid = dk->GetGUID();
        ObjectGuid const drwGuid = const_cast<Player*>(dk)->getRuneWeaponGUID();
        for (AuraType const type : { SPELL_AURA_PERIODIC_DAMAGE, SPELL_AURA_LINKED })
            for (AuraEffect const* effect : target->GetAuraEffectsByType(type))
                if (effect->GetSpellInfo()->Dispel == DISPEL_DISEASE &&
                    (effect->GetCasterGUID() == dkGuid || (drwGuid && effect->GetCasterGUID() == drwGuid)))
                    return true;

        return false;
    }

    bool IsObliterate(uint32 spellId)
    {
        return spellId == DeathKnightData::SPELL_OBLITERATE_203054 ||
            spellId == DeathKnightData::SPELL_OBLITERATE_66198;
    }

    bool IsFrostStrike(uint32 spellId)
    {
        return spellId == DeathKnightData::SPELL_FROST_STRIKE || spellId == DeathKnightData::SPELL_FROST_STRIKE_66196;
    }

    float MasteryMultiplier(Player const* dk)
    {
        return 1.0f + std::max(0.0f, dk->GetMasteryPercentage()) / 100.0f;
    }
}

namespace DeathKnight
{
    // Once-per-cast guard, one per aura script instance (DeathKnight::RuneProcAllowed keys its guard by the aura id
    // for the same reason: one aura's answer must never starve another's on a self-centred cast). First() is true
    // for the first event of a cast and false for the rest of its hits: a cast with an explicit unit target counts
    // only the hit on that unit; a cast without one counts the first event of the same spell object in the same
    // game-time tick; auto attacks and periodic ticks always count.
    bool OncePerCastGuard::First(ProcEventInfo& eventInfo)
    {
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell || (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC))
            return true;

        if (Unit const* castTarget = spell->m_targets.GetUnitTarget())
            return castTarget == eventInfo.GetActionTarget();

        uint32 const spellId = spell->GetSpellInfo() ? spell->GetSpellInfo()->Id : 0;
        int64 const now = int64(GameTime::GetGameTimeMS().count());
        if (_spell == spell && _spellId == spellId && _timeMs == now)
            return false;

        _spell = spell;
        _spellId = spellId;
        _timeMs = now;
        return true;
    }

    // The aura owner's own event, once per cast
    bool OncePerCastGuard::OwnerFirst(Unit const* owner, ProcEventInfo& eventInfo)
    {
        return owner && eventInfo.GetActor() == owner && First(eventInfo);
    }

    void SetCastSchool(Spell* spell, SpellSchoolMask mask)
    {
        if (!spell || !mask)
            return;

        // OnCast only (0-verify item 5): after it the crit roll, EffectWeaponDmg, armor and resist read the member.
        // The power cost was computed earlier with the DBC school, so the switch never changes the cost.
        spell->*SpellSchoolAccess::Member() = mask;
    }

    bool IsSchoolSwitchedCast(Spell const* spell)
    {
        return spell && spell->GetSpellInfo() && spell->GetSpellSchoolMask() != spell->GetSpellInfo()->GetSchoolMask();
    }

    float GetOffhandFactor(Player const* dk)
    {
        if (!dk)
            return 1.0f;

        // The engine's off-hand TOTAL_PCT without the physical %-done auras (Unit::UpdateDamagePctDoneMods): the
        // penalty, then every SPELL_AURA_MOD_OFFHAND_DAMAGE_PCT (Nerves of Cold Steel E1, aura 122) whose weapon
        // requirement the off-hand meets.
        float factor = float(100 - std::clamp<int32>(DeathKnightData::OFFHAND_PENALTY_PCT, 0, 100)) / 100.0f;
        factor *= dk->GetTotalAuraMultiplier(SPELL_AURA_MOD_OFFHAND_DAMAGE_PCT, [dk](AuraEffect const* aurEff)
        {
            return dk->CheckAttackFitToAuraRequirement(OFF_ATTACK, aurEff);
        });

        return factor;
    }

    int32 GetOffhandFlatAddBack(Unit const* caster, SpellInfo const* spellInfo, Unit const* target)
    {
        if (!caster || !spellInfo)
            return 0;

        // Only a physical-base copy stores half the main-hand flat (D1); 66196 (Frost) stores the full flat.
        if (!(spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_NORMAL))
            return 0;

        for (uint8 i = EFFECT_0; i < MAX_SPELL_EFFECTS; ++i)
        {
            switch (spellInfo->Effects[i].Effect)
            {
                case SPELL_EFFECT_WEAPON_DAMAGE:
                case SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL:
                case SPELL_EFFECT_NORMALIZED_WEAPON_DMG:
                    // The value EffectWeaponDmg reads for fixed_bonus (Spell::CalculateSpellDamage, potency included).
                    return std::max<int32>(0, caster->CalculateSpellDamage(target, spellInfo, i));
                default:
                    break;
            }
        }

        return 0;
    }

    float GetFrostDamageMultiplier(Player const* dk, SpellInfo const* spellInfo, Unit const* target, uint32 flags)
    {
        if (!dk || !spellInfo)
            return 1.0f;

        uint32 const spellId = spellInfo->Id;
        bool const obliterate = IsObliterate(spellId);
        bool const frostStrike = IsFrostStrike(spellId);
        bool const glacialEruption = spellId == DeathKnightData::SPELL_GLACIAL_ERUPTION;
        bool const howlingBlast = spellId == DeathKnightData::SPELL_HOWLING_BLAST;
        bool const breathTick = spellId == DeathKnightData::SPELL_BREATH_OF_SINDRAGOSA_TICK;

        float multiplier = 1.0f;

        if (target)
        {
            // Glacier Rot: the target carries one of this DK's diseases. The r3 capstone (49791) adds Mastery 1:1 into
            // the percent for Frost Strike and Glacial Advance; Howling Blast keeps the base value.
            if (frostStrike || glacialEruption || howlingBlast)
            {
                int32 const glacierRot = RankAmount(dk, { DeathKnightData::SPELL_GLACIER_ROT_49791,
                    DeathKnightData::SPELL_GLACIER_ROT_49790, DeathKnightData::SPELL_GLACIER_ROT }, EFFECT_0);
                if (glacierRot > 0 && HasOwnDisease(dk, target))
                {
                    float pct = float(glacierRot);
                    if ((frostStrike || glacialEruption) && dk->HasAura(DeathKnightData::SPELL_GLACIER_ROT_49791))
                        pct += std::max(0.0f, dk->GetMasteryPercentage());

                    AddPct(multiplier, pct);
                }
            }

            // Merciless Combat: target below MERCILESS_COMBAT_HP_PCT (Obliterate, Frost Strike, Breath).
            if ((obliterate || frostStrike || breathTick) &&
                target->HealthBelowPct(int32(DeathKnightData::MERCILESS_COMBAT_HP_PCT)))
            {
                int32 const merciless = RankAmount(dk, { DeathKnightData::SPELL_MERCILESS_COMBAT_49538,
                    DeathKnightData::SPELL_MERCILESS_COMBAT }, EFFECT_0);
                if (merciless > 0)
                    AddPct(multiplier, merciless);
            }

            // Tundra Stalker: the target carries THIS DK's Frost Fever (Obliterate, Breath).
            if ((obliterate || breathTick) && target->HasAura(DeathKnightData::SPELL_FROST_FEVER, dk->GetGUID()))
            {
                int32 const tundra = RankAmount(dk, { DeathKnightData::SPELL_TUNDRA_STALKER_50128,
                    DeathKnightData::SPELL_TUNDRA_STALKER_50127, DeathKnightData::SPELL_TUNDRA_STALKER }, EFFECT_0);
                if (tundra > 0)
                    AddPct(multiplier, tundra);
            }

            // Razorice for a school-switched cast: aura 271 on 51714 is family-mask based and cannot see it.
            if (flags & FROST_MULT_SCHOOL_SWITCHED)
                if (Aura const* razorice = target->GetAura(DeathKnightData::SPELL_FROST_VULNERABILITY, dk->GetGUID()))
                    AddPct(multiplier, float(razorice->GetStackAmount()) *
                        float(DeathKnightData::RAZORICE_PCT_PER_STACK));
        }

        // Obliteration capstone (the 1-rank talent's passive 203292): Killing Machine Obliterates x (1 + Mastery%).
        if ((flags & FROST_MULT_KM_OBLITERATE) && dk->HasAura(DeathKnightData::SPELL_OBLITERATION))
            multiplier *= MasteryMultiplier(dk);

        // Breath of Sindragosa (a 1-rank talent: its capstone is always on): Mastery, then Frostwyrm's Wrath's ramp
        // (203305 is only ever applied with the r2 capstone). Every tick target; the caller applies
        // BREATH_SECONDARY_PCT to the secondaries.
        if (breathTick)
        {
            multiplier *= MasteryMultiplier(dk);
            if (Aura const* ramp = dk->GetAura(DeathKnightData::SPELL_FROSTWYRMS_WRATH_RAMP, dk->GetGUID()))
                AddPct(multiplier, float(ramp->GetStackAmount()) * float(DeathKnightData::FROSTWYRM_RAMP_PCT));
        }

        if (flags & FROST_MULT_DEATHCHILL)
            AddPct(multiplier, float(DeathKnightData::DEATHCHILL_DAMAGE_PCT));

        if (flags & FROST_MULT_OFFHAND)
            multiplier *= GetOffhandFactor(dk);

        return multiplier;
    }

    bool HasKillingMachine(Unit const* dk)
    {
        return dk && dk->HasAura(DeathKnightData::SPELL_KILLING_MACHINE_BUFF, dk->GetGUID());
    }

    void ConsumeKillingMachine(Player* dk)
    {
        if (!dk)
            return;

        Aura* killingMachine = dk->GetAura(DeathKnightData::SPELL_KILLING_MACHINE_BUFF, dk->GetGUID());
        if (!killingMachine)
            return;

        killingMachine->ModStackAmount(-1);

        // Enduring Strength: only when a stack was consumed and Pillar of Frost is up.
        if (!dk->HasAura(DeathKnightData::SPELL_PILLAR_OF_FROST, dk->GetGUID()))
            return;

        int32 const extension = RankAmount(dk, { DeathKnightData::SPELL_ENDURING_STRENGTH_203298,
            DeathKnightData::SPELL_ENDURING_STRENGTH }, EFFECT_0);
        if (extension > 0)
            ExtendPillar(dk, extension);
    }

    void GrantKillingMachine(Player* dk)
    {
        if (!dk)
            return;

        int32 const cap = std::max<int32>(1, DeathKnightData::KILLING_MACHINE_MAX_STACKS);
        if (Aura* killingMachine = dk->GetAura(DeathKnightData::SPELL_KILLING_MACHINE_BUFF, dk->GetGUID()))
        {
            // ModStackAmount(+1) refreshes the duration; at the cap only the duration refreshes.
            if (int32(killingMachine->GetStackAmount()) < cap)
                killingMachine->ModStackAmount(1);
            else
                killingMachine->RefreshDuration();
            return;
        }

        dk->CastSpell(dk, DeathKnightData::SPELL_KILLING_MACHINE_BUFF, TRIGGERED_FULL_MASK);
    }

    void GrantRime(Player* dk)
    {
        if (!dk)
            return;

        dk->CastSpell(dk, DeathKnightData::SPELL_FREEZING_FOG, TRIGGERED_FULL_MASK);
        dk->RemoveSpellCooldown(DeathKnightData::SPELL_HOWLING_BLAST, true);
    }

    void ExtendPillar(Player* dk, int32 ms)
    {
        if (!dk || ms <= 0)
            return;

        Aura* pillar = dk->GetAura(DeathKnightData::SPELL_PILLAR_OF_FROST, dk->GetGUID());
        if (!pillar)
            return;

        int32 const cap = RankAmount(dk, { DeathKnightData::SPELL_ENDURING_STRENGTH_203298,
            DeathKnightData::SPELL_ENDURING_STRENGTH }, EFFECT_1);
        if (cap <= 0)
            return;

        // The cap is per Pillar: a new Pillar aura (another apply time) starts from 0.
        PillarExtension* state = dk->CustomData.GetDefault<PillarExtension>(PILLAR_EXTENSION_KEY);
        if (state->applyTime != pillar->GetApplyTime())
        {
            state->applyTime = pillar->GetApplyTime();
            state->extendedMs = 0;
        }

        int32 const add = std::min(ms, cap - state->extendedMs);
        if (add <= 0)
            return;

        state->extendedMs += add;
        pillar->SetMaxDuration(pillar->GetMaxDuration() + add);
        pillar->SetDuration(pillar->GetDuration() + add);
    }

    void ActivateRune(Player* dk, uint8 slot)
    {
        // m_runes is null for anyone but a Death Knight (InitRunes), and the accessors dereference it unguarded.
        if (!dk || slot >= MAX_RUNES || !dk->IsClass(CLASS_DEATH_KNIGHT, CLASS_CONTEXT_ABILITY))
            return;

        // The stock Empower Rune Weapon tail (SpellEffects.cpp EffectActivateRune); never ResyncRunes.
        dk->SetRuneCooldown(slot, 0);
        dk->SetGracePeriod(slot, dk->IsInCombat()); // xinef: reset grace period
        // is needed to push through to the client that the rune is active
        dk->CastSpell(dk, 47804, true);
    }

    void SnapshotRuneCooldowns(Player* dk)
    {
        // S3 D1: the shared writer (cast id 0 = untagged; FindJustSpentFrostRune reads the latest snapshot).
        SnapshotRunes(dk, 0);
    }

    int8 FindJustSpentFrostRune(Player const* dk)
    {
        if (!dk || !dk->IsClass(CLASS_DEATH_KNIGHT, CLASS_CONTEXT_ABILITY))
            return -1;

        RuneCooldownSnapshot const* snapshot = dk->CustomData.Get<RuneCooldownSnapshot>(RUNE_SNAPSHOT_KEY);
        if (!snapshot)
            return -1;

        // A slot that was ready at the snapshot and is recharging now was just spent. A Frost slot first; else a Death
        // rune (it paid the Frost cost in a Frost rune's place). S3 D1: the Death test reads the snapshot type, since a
        // Death Rune that pays on a hit reverts to its base type inside TakeRunePower (the live type never matched).
        int8 deathSlot = -1;
        for (uint8 slot = 0; slot < MAX_RUNES; ++slot)
        {
            if (snapshot->cooldowns[slot] || !dk->GetRuneCooldown(slot))
                continue;

            if (dk->GetBaseRune(slot) == RUNE_FROST)
                return int8(slot);

            if (deathSlot < 0 && snapshot->types[slot] == RUNE_DEATH)
                deathSlot = int8(slot);
        }

        return deathSlot;
    }

    bool DeathchillReady(Unit const* dk)
    {
        return dk && dk->HasAura(DeathKnightData::SPELL_DEATHCHILL_BUFF, dk->GetGUID());
    }

    void ArmDeathchill(Player* dk, Spell* spell)
    {
        if (!dk || !DeathchillReady(dk))
            return;

        // Never on a Killing Machine Obliterate: two +100% crit mods on one cast are non-deterministic (U9).
        if (spell && spell->GetSpellInfo() && IsObliterate(spell->GetSpellInfo()->Id) &&
            (IsSchoolSwitchedCast(spell) || HasKillingMachine(dk)))
            return;

        if (!dk->HasAura(DeathKnightData::SPELL_DEATHCHILL_MARKER, dk->GetGUID()))
            dk->CastSpell(dk, DeathKnightData::SPELL_DEATHCHILL_MARKER, TRIGGERED_FULL_MASK);
    }

    void ConsumeDeathchill(Player* dk)
    {
        // Only a cast that was armed spends the charge.
        if (!dk || !dk->HasAura(DeathKnightData::SPELL_DEATHCHILL_MARKER, dk->GetGUID()))
            return;

        dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_DEATHCHILL_MARKER, dk->GetGUID());
        dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_DEATHCHILL_BUFF, dk->GetGUID());

        // The highest rank known sets the lockout; its EXPIRE re-grants the buff (spell_dk_deathchill_lockout).
        for (std::size_t i = DEATHCHILL_RANKS.size(); i-- > 0;)
        {
            if (!dk->HasAura(DEATHCHILL_RANKS[i]))
                continue;

            dk->CastCustomSpell(DeathKnightData::SPELL_DEATHCHILL_LOCKOUT, SPELLVALUE_AURA_DURATION,
                DEATHCHILL_LOCKOUT_MS[i], dk, TRIGGERED_FULL_MASK);
            return;
        }
    }

    void StartOrExtendHungeringCold(Player* dk)
    {
        if (!dk)
            return;

        int32 const duration = std::max<int32>(1, DeathKnightData::HUNGERING_COLD_STORM_MS);
        if (Aura* storm = dk->GetAura(DeathKnightData::SPELL_HUNGERING_COLD_STORM, dk->GetGUID()))
        {
            // Never RefreshDuration or a re-cast: both reset the 2 s tick timer. The max duration grows by the time
            // added, since AuraEffect::Update stops ticking at GetMaxDuration() / amplitude ticks.
            storm->SetMaxDuration(storm->GetMaxDuration() + std::max<int32>(0, duration - storm->GetDuration()));
            storm->SetDuration(duration);
            return;
        }

        dk->CastSpell(dk, DeathKnightData::SPELL_HUNGERING_COLD_STORM, TRIGGERED_FULL_MASK);
    }

    void OnHungeringColdHit(Player* dk, Unit* target)
    {
        if (!dk || !target || !target->IsAlive())
            return;

        ObjectGuid const dkGuid = dk->GetGUID();

        // "Each tick slows by a further 20%, and its third tick freezes": a tick that finds the slow already at
        // HUNGERING_COLD_SLOW_STACKS_TO_FREEZE stacks (from the two ticks before) freezes, then the slow is refreshed.
        Aura const* slow = target->GetAura(DeathKnightData::SPELL_HUNGERING_COLD_SLOW, dkGuid);
        int32 const stacksBefore = slow ? int32(slow->GetStackAmount()) : 0;
        if (stacksBefore >= int32(DeathKnightData::HUNGERING_COLD_SLOW_STACKS_TO_FREEZE) &&
            !target->HasAura(DeathKnightData::SPELL_HUNGERING_COLD_LOCKOUT, dkGuid))
        {
            // Stun-immune: only slowed, and no lockout either.
            SpellInfo const* freeze = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_HUNGERING_COLD_FREEZE);
            if (freeze && !target->IsImmunedToSpell(freeze))
            {
                dk->CastSpell(target, DeathKnightData::SPELL_HUNGERING_COLD_FREEZE, TRIGGERED_FULL_MASK);
                dk->CastSpell(target, DeathKnightData::SPELL_HUNGERING_COLD_LOCKOUT, TRIGGERED_FULL_MASK);
            }
        }

        // +1 stack (capped by the slow's StackAmount), duration refreshed.
        dk->CastSpell(target, DeathKnightData::SPELL_HUNGERING_COLD_SLOW, TRIGGERED_FULL_MASK);
    }

    uint32 GetBreathDrain(uint32 tickNumber)
    {
        // Internal runic power (x10 the displayed value): BREATH_BASE_DRAIN, +1 every BREATH_DRAIN_STEP_TICKS ticks.
        uint32 const tick = std::max<uint32>(1, tickNumber);
        uint32 const step = uint32(std::max<int32>(1, DeathKnightData::BREATH_DRAIN_STEP_TICKS));
        uint32 const base = uint32(std::max<int32>(0, DeathKnightData::BREATH_BASE_DRAIN));
        return (base + (tick - 1) / step) * 10;
    }

    void AddFinalRoarDamage(Player* dk, uint32 damage)
    {
        if (!dk || !damage)
            return;

        dk->CustomData.GetDefault<FinalRoarStore>(FINAL_ROAR_STORE_KEY)->damage += damage;
    }

    uint32 TakeFinalRoarDamage(Player* dk)
    {
        if (!dk)
            return 0;

        FinalRoarStore* store = dk->CustomData.Get<FinalRoarStore>(FINAL_ROAR_STORE_KEY);
        if (!store)
            return 0;

        uint32 const damage = ClampToUInt32(store->damage);
        store->damage = 0;
        return damage;
    }
}

// ---- S3 ----
/*
 * S3 block (docs/reworks/death-knight-unholy-rework.md): the shared rune snapshot and Death Runes (U7, D1), Festering
 * Wounds (U8-U10), Dread Host / All Will Serve / Necromancy / Crypt Fever / Ebon Plague readers (U12-U14), the Unholy
 * minions (U15-U23: shares, the damage seam terms, Lesser Ghouls, the Gargoyle, Shadow Infusion, Infected Claws) and
 * Pestilence (U26). Per-player and per-creature state lives on CustomData, nothing file-static; creature state is
 * erased on remove-world (OnMinionRemoveWorld) and dies with the creature anyway.
 */
namespace
{
    // Stock ids without a header name (D14).
    constexpr uint32 SPELL_WANDERING_PLAGUE_DAMAGE = 50526;
    constexpr uint32 SPELL_ON_A_PALE_HORSE_51986 = 51986;

    // Rotten Touch: the armed Coil's missile (Speed 24) lands well inside this; a stale record never bursts later.
    constexpr int64 ROTTEN_TOUCH_RECORD_MS = 5000;

    constexpr char const* WOUND_BURST_CONTEXT_KEY = "deathknight_wound_burst_context";
    constexpr char const* ROTTEN_TOUCH_KEY = "deathknight_rotten_touch";
    constexpr char const* GARGOYLE_RAMP_KEY = "deathknight_gargoyle_ramp";
    constexpr char const* LESSER_GHOUL_TIMER_KEY = "deathknight_lesser_ghoul_timer";
    constexpr char const* GARGOYLE_STATE_KEY = "deathknight_gargoyle_state";
    constexpr char const* LESSER_GHOUL_TARGET_KEY = "deathknight_lesser_ghoul_target";

    // On the Lesser Ghoul: the unit it was raised at (its AI attacks it first).
    struct LesserGhoulSummonTarget : DataMap::Base
    {
        ObjectGuid target;
    };

    // The burst a helper is casting right now (BurstFesteringWounds / overflow): the burst spell's AfterHit calls
    // OnWoundBurstHit synchronously inside that cast (instant, no missile), so the source travels here.
    struct WoundBurstContext : DataMap::Base
    {
        bool active = false;
        DeathKnight::WoundSource source = DeathKnight::WoundSource::ScourgeStrike;
    };

    struct RottenTouchRecord : DataMap::Base
    {
        ObjectGuid target;
        int64 timeMs = 0;
    };

    // Runic Power spent while this Gargoyle is out, below one ramp stack (internal units, x10).
    struct GargoyleRampState : DataMap::Base
    {
        ObjectGuid gargoyle;
        uint32 remainder = 0;
    };

    // D9: on the Lesser Ghoul.
    struct LesserGhoulTimer : DataMap::Base
    {
        int64 startMs = 0;
        uint32 totalMs = 0;
    };

    // On the Gargoyle: its spawn time (the strike window) and whether it has left (flown away).
    struct GargoyleState : DataMap::Base
    {
        int64 startMs = 0;
        bool left = false;
    };

    // Living, not queued for removal, on the owner's map.
    bool IsLiveSummon(Player const* owner, Creature const* creature)
    {
        if (!creature || !creature->IsInWorld() || !creature->IsAlive() || creature->FindMap() != owner->FindMap())
            return false;

        TempSummon const* summon = creature->ToTempSummon();
        return !summon || summon->GetSummonType() != TEMPSUMMON_DESPAWNED;
    }

    std::vector<Creature*> GetLiveMinions(Player const* owner, uint32 entry)
    {
        // GetAllMinionsByEntry copies out of m_Controlled (it only reads it; the const_cast is for its signature).
        std::list<Creature*> minions;
        const_cast<Player*>(owner)->GetAllMinionsByEntry(minions, entry);

        std::vector<Creature*> live;
        for (Creature* creature : minions)
            if (IsLiveSummon(owner, creature))
                live.push_back(creature);

        return live;
    }

    // Time left in ms: the D9 record when there is one, else the summon timer (the full duration until it updates).
    int64 RemainingMs(Creature* creature)
    {
        if (LesserGhoulTimer const* timer = creature->CustomData.Get<LesserGhoulTimer>(LESSER_GHOUL_TIMER_KEY))
            return timer->startMs + int64(timer->totalMs) - NowMs();

        TempSummon* summon = creature->ToTempSummon();
        return summon ? int64(summon->GetTimer()) : 0;
    }

    // n stacks of spellId from caster on target: +n on the caster's existing aura (refreshes, capped by the
    // spell's StackAmount), else a new aura plus n - 1. selfCast casts the first stack (a visible self buff), else
    // AddAura (no range, LOS or hit roll: wounds placed by a far minion, buffs on a minion). Returns the aura or null.
    Aura* AddAuraStacks(Unit* caster, Unit* target, uint32 spellId, int32 n, bool selfCast)
    {
        if (!caster || !target || n <= 0)
            return nullptr;

        if (Aura* aura = target->GetAura(spellId, caster->GetGUID()))
        {
            aura->ModStackAmount(n);
            return aura;
        }

        if (selfCast)
            caster->CastSpell(target, spellId, TRIGGERED_FULL_MASK);
        else
            caster->AddAura(spellId, target);

        Aura* aura = target->GetAura(spellId, caster->GetGUID());
        if (aura && n > 1)
            aura->ModStackAmount(n - 1);

        return aura;
    }

    // One burst cast (203457 / 203458) with n on BASE_POINT1, under the source context for OnWoundBurstHit.
    void CastWoundBurst(Player* dk, Unit* target, uint32 spellId, uint8 n, DeathKnight::WoundSource src)
    {
        WoundBurstContext* context = dk->CustomData.GetDefault<WoundBurstContext>(WOUND_BURST_CONTEXT_KEY);
        WoundBurstContext const saved = *context;
        context->active = true;
        context->source = src;

        int32 const count = int32(n);
        dk->CastCustomSpell(target, spellId, nullptr, &count, nullptr, true);

        context->active = saved.active;
        context->source = saved.source;
    }

    Creature* GetPetGhoul(Player const* dk)
    {
        Pet* pet = dk->GetPet();
        if (!pet || !pet->IsAlive() || DeathKnight::GetMinionKind(pet) != DeathKnight::MinionKind::Ghoul)
            return nullptr;

        return pet;
    }

    // The strike window left on this Gargoyle (ms), from its spawn time.
    int32 GargoyleWindowLeftMs(Creature const* gargoyle)
    {
        GargoyleState const* state = gargoyle->CustomData.Get<GargoyleState>(GARGOYLE_STATE_KEY);
        if (!state)
            return int32(DeathKnightData::GARGOYLE_WINDOW_MS);

        int64 const left = int64(DeathKnightData::GARGOYLE_WINDOW_MS) - (NowMs() - state->startMs);
        return int32(std::clamp<int64>(left, 0, DeathKnightData::GARGOYLE_WINDOW_MS));
    }

    void CastOnAPaleHorse(Player* dk, Unit* target)
    {
        if (!dk || !target || !target->IsAlive() || !DeathKnight::HasOnAPaleHorse(dk))
            return;

        dk->CastSpell(target, DeathKnightData::SPELL_ON_A_PALE_HORSE_DAMAGE, TRIGGERED_FULL_MASK);
    }

    // U18: every GARGOYLE_RP_PER_RAMP_STACK Runic Power spent while the Gargoyle is out = +1 ramp stack on it. The
    // fraction carries on the DK's CustomData and restarts with a new Gargoyle.
    void RampGargoyle(Player* dk, int32 internalRp)
    {
        if (!dk || internalRp <= 0)
            return;

        Creature* gargoyle = DeathKnight::GetActiveGargoyle(dk);
        if (!gargoyle)
            return;

        uint32 const perStack = uint32(std::max<int32>(1, DeathKnightData::GARGOYLE_RP_PER_RAMP_STACK)) * 10;
        GargoyleRampState* state = dk->CustomData.GetDefault<GargoyleRampState>(GARGOYLE_RAMP_KEY);
        if (state->gargoyle != gargoyle->GetGUID())
        {
            state->gargoyle = gargoyle->GetGUID();
            state->remainder = 0;
        }

        state->remainder += uint32(internalRp);
        uint32 const stacks = state->remainder / perStack;
        state->remainder %= perStack;
        if (stacks)
            AddAuraStacks(dk, gargoyle, DeathKnightData::SPELL_GARGOYLE_RAMP, int32(stacks), false);
    }
}

namespace DeathKnight
{
    // ---- Runes (U7, D1) ----
    void SnapshotRunes(Player* dk, uint32 castSpellId)
    {
        if (!dk || !dk->IsClass(CLASS_DEATH_KNIGHT, CLASS_CONTEXT_ABILITY))
            return;

        RuneCooldownSnapshot* snapshot = dk->CustomData.GetDefault<RuneCooldownSnapshot>(RUNE_SNAPSHOT_KEY);
        snapshot->castSpellId = castSpellId;
        for (uint8 slot = 0; slot < MAX_RUNES; ++slot)
        {
            snapshot->cooldowns[slot] = dk->GetRuneCooldown(slot);
            snapshot->types[slot] = uint8(dk->GetCurrentRune(slot));
        }
    }

    uint8 GetSpentPlainRuneSlots(Player const* dk, uint32 castSpellId, uint8 outSlots[6])
    {
        if (!dk || !outSlots || !dk->IsClass(CLASS_DEATH_KNIGHT, CLASS_CONTEXT_ABILITY))
            return 0;

        RuneCooldownSnapshot const* snapshot = dk->CustomData.Get<RuneCooldownSnapshot>(RUNE_SNAPSHOT_KEY);
        if (!snapshot || snapshot->castSpellId != castSpellId)
            return 0;

        // Ready at the snapshot, recharging now, and a plain rune then: a Death Rune that paid (returned or not)
        // gets nothing back, so a returned rune can never feed the next cast (L26 guard).
        uint8 count = 0;
        for (uint8 slot = 0; slot < MAX_RUNES; ++slot)
            if (!snapshot->cooldowns[slot] && dk->GetRuneCooldown(slot) && snapshot->types[slot] != RUNE_DEATH)
                outSlots[count++] = slot;

        return count;
    }

    void ConvertToDeathRune(Player* dk, uint8 slot, bool ready)
    {
        if (!dk || slot >= MAX_RUNES || !dk->IsClass(CLASS_DEATH_KNIGHT, CLASS_CONTEXT_ABILITY))
            return;

        // No convert aura: RestoreBaseRune reverts it on its next spend (on a hit), and no RemoveRunesByAuraEffect
        // ever touches it. ConvertRune sends SMSG_CONVERT_RUNE; ActivateRune then pushes the ready state (47804).
        dk->SetRuneConvertAura(slot, nullptr);
        dk->ConvertRune(slot, RUNE_DEATH);
        if (ready)
            ActivateRune(dk, slot);
    }

    // ---- Festering Wounds (U8-U10) ----
    bool WoundSourceGrantsResources(WoundSource src)
    {
        switch (src)
        {
            case WoundSource::PlagueStrikeOverflow:
            case WoundSource::ScourgeStrike:
            case WoundSource::RottenTouch:
                return true;
            default:
                return false;
        }
    }

    uint8 GetFesteringWounds(Unit const* target, ObjectGuid dkGuid)
    {
        if (!target || !dkGuid)
            return 0;

        Aura const* aura = target->GetAura(DeathKnightData::SPELL_FESTERING_WOUND, dkGuid);
        return aura ? aura->GetStackAmount() : 0;
    }

    void AddFesteringWounds(Player* dk, Unit* target, uint8 n, WoundSource src)
    {
        if (!dk || !target || !n || !target->IsAlive())
            return;

        // The debuff's caster is always the DK (bots read stacks(target, 203456, own)), whoever placed the wound.
        uint8 const cap = uint8(std::clamp<int32>(DeathKnightData::FESTERING_WOUND_MAX_STACKS, 1, 255));
        uint8 const current = GetFesteringWounds(target, dk->GetGUID());
        uint8 const room = current < cap ? uint8(cap - current) : 0;
        uint8 const added = std::min(n, room);
        uint8 const overflow = uint8(n - added);

        if (added)
        {
            if (!AddAuraStacks(dk, target, DeathKnightData::SPELL_FESTERING_WOUND, added, false))
                return;   // immune: no wound, so no overflow either
        }
        else if (Aura* aura = target->GetAura(DeathKnightData::SPELL_FESTERING_WOUND, dk->GetGUID()))
            aura->RefreshDuration();   // a gain at the cap still refreshes

        // Wounds past the cap burst at once in one overflow cast with n.
        if (overflow)
            CastWoundBurst(dk, target, DeathKnightData::SPELL_FESTERING_WOUND_OVERFLOW, overflow, src);
    }

    void BurstFesteringWounds(Player* dk, Unit* target, uint8 n, WoundSource src)
    {
        if (!dk || !target || !n || !target->IsAlive())
            return;

        Aura* aura = target->GetAura(DeathKnightData::SPELL_FESTERING_WOUND, dk->GetGUID());
        if (!aura)
            return;

        uint8 const burst = std::min<uint8>(n, aura->GetStackAmount());
        if (!burst)
            return;

        // Consume first: a burst that kills explodes only the wounds left. A drop to 0 removes by DEFAULT, which the
        // wound's AuraScript never explodes.
        aura->ModStackAmount(-int32(burst));
        CastWoundBurst(dk, target, DeathKnightData::SPELL_FESTERING_WOUND_BURST, burst, src);
    }

    void OnWoundBurstHit(Player* dk, Unit* target, uint32 damage, WoundSource src, uint8 n)
    {
        if (!dk || !target || !n)
            return;

        // The helper casting this burst knows its source (the caller's argument is the fallback).
        if (WoundBurstContext const* context = dk->CustomData.Get<WoundBurstContext>(WOUND_BURST_CONTEXT_KEY))
            if (context->active)
                src = context->source;

        if (!WoundSourceGrantsResources(src))
            return;

        // 3 Runic Power per wound (internal x10).
        int32 const rp = int32(std::max<int32>(0, DeathKnightData::FESTERING_WOUND_RP_PER_WOUND)) * 10 * int32(n);
        if (rp > 0)
            dk->CastCustomSpell(DeathKnightData::SPELL_UNHOLY_RP_ENERGIZE, SPELLVALUE_BASE_POINT0, rp, dk,
                TRIGGERED_FULL_MASK);

        // Wandering Plague: one roll per burst event at the DK's melee crit chance against the target.
        int32 const pct = RankAmount(dk, { DeathKnightData::SPELL_WANDERING_PLAGUE_49655,
            DeathKnightData::SPELL_WANDERING_PLAGUE_49654, DeathKnightData::SPELL_WANDERING_PLAGUE }, EFFECT_0);
        if (pct <= 0 || !damage || !target->IsAlive())
            return;

        if (!roll_chance_f(dk->GetUnitCriticalChance(BASE_ATTACK, target)))
            return;

        int32 const bp = ClampToInt32(uint64(damage) * uint64(pct) / 100);
        if (bp > 0)
            dk->CastCustomSpell(target, SPELL_WANDERING_PLAGUE_DAMAGE, &bp, nullptr, nullptr, true);
    }

    void ScheduleWoundExplosion(Player* dk, Unit* corpse, uint8 stacks)
    {
        if (!dk || !corpse || !stacks || !dk->IsInWorld() || dk->GetMap() != corpse->GetMap())
            return;

        // Bug log :431: a spell dest carries no map id. Capture the map, instance and position now, re-resolve the DK
        // in the event and cast at an explicit dest.
        ObjectGuid const dkGuid = dk->GetGUID();
        uint32 const mapId = corpse->GetMapId();
        uint32 const instanceId = corpse->GetInstanceId();
        Position const position = corpse->GetPosition();
        dk->m_Events.AddEventAtOffset([dkGuid, mapId, instanceId, position, stacks]()
        {
            Player* owner = ObjectAccessor::FindPlayer(dkGuid);
            if (!owner || !owner->IsInWorld() || owner->GetMapId() != mapId || owner->GetInstanceId() != instanceId)
                return;

            SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_FESTERING_WOUND_EXPLOSION);
            if (!spellInfo)
                return;

            SpellCastTargets targets;
            targets.SetDst(position);
            CustomSpellValues values;
            values.AddSpellMod(SPELLVALUE_BASE_POINT1, int32(stacks));
            owner->CastSpell(targets, spellInfo, &values, TRIGGERED_FULL_MASK);
        }, Milliseconds(1));
    }

    // ---- Mastery and multipliers ----
    int32 GetDreadHostPct(Player const* dk)
    {
        if (!dk)
            return 0;

        // Rage of Rivendare eff0 DUMMY 3/6/9; rank 3 (50119) is the capstone: + Mastery.
        int32 pct = RankAmount(dk, { DeathKnightData::SPELL_RAGE_OF_RIVENDARE_50119,
            DeathKnightData::SPELL_RAGE_OF_RIVENDARE_50118, DeathKnightData::SPELL_RAGE_OF_RIVENDARE }, EFFECT_0);
        if (dk->HasAura(DeathKnightData::SPELL_RAGE_OF_RIVENDARE_50119))
            pct += int32(std::lround(std::max(0.0f, dk->GetMasteryPercentage())));

        return std::max<int32>(0, pct);
    }

    int32 GetAllWillServePct(Player const* dk)
    {
        if (!dk)
            return 0;

        return std::max<int32>(0, RankAmount(dk, { DeathKnightData::SPELL_ALL_WILL_SERVE_203442,
            DeathKnightData::SPELL_ALL_WILL_SERVE }, EFFECT_0));
    }

    bool HasNecromancy(Unit const* dk)
    {
        return dk && dk->IsPlayer() && dk->HasAura(DeathKnightData::SPELL_ALL_WILL_SERVE_203442);
    }

    int32 GetCryptFeverPct(Unit const* dk)
    {
        if (!dk || !dk->IsPlayer())
            return 0;

        return std::max<int32>(0, RankAmount(dk, { DeathKnightData::SPELL_CRYPT_FEVER_49632,
            DeathKnightData::SPELL_CRYPT_FEVER_49631, DeathKnightData::SPELL_CRYPT_FEVER }, EFFECT_0));
    }

    int32 GetEbonPlagueMagicPct(Unit const* dk)
    {
        if (!dk || !dk->IsPlayer())
            return 0;

        return std::max<int32>(0, RankAmount(dk, { DeathKnightData::SPELL_EBON_PLAGUEBRINGER_51161,
            DeathKnightData::SPELL_EBON_PLAGUEBRINGER_51160, DeathKnightData::SPELL_EBON_PLAGUEBRINGER }, EFFECT_0));
    }

    // ---- Necromancy (U14) ----
    void GrantNecromanticEnergy(Player* dk)
    {
        if (!dk)
            return;

        int32 const cap = std::max<int32>(1, DeathKnightData::NECROMANTIC_ENERGY_MAX);
        int32 const add = std::max<int32>(0, DeathKnightData::NECROMANTIC_ENERGY_PER_STRIKE);
        Aura* aura = dk->GetAura(DeathKnightData::SPELL_NECROMANTIC_ENERGY, dk->GetGUID());
        int32 const current = aura ? int32(aura->GetStackAmount()) : 0;

        // ModStackAmount refreshes the duration; at the cap only the duration refreshes.
        int32 const n = std::min(add, cap - current);
        if (aura && n <= 0)
        {
            aura->RefreshDuration();
            return;
        }

        AddAuraStacks(dk, dk, DeathKnightData::SPELL_NECROMANTIC_ENERGY, n, true);
    }

    bool ConsumeNecromanticEnergy(Player* dk)
    {
        if (!dk)
            return false;

        Aura* aura = dk->GetAura(DeathKnightData::SPELL_NECROMANTIC_ENERGY, dk->GetGUID());
        if (!aura || !aura->GetStackAmount())
            return false;

        aura->ModStackAmount(-1);
        return true;
    }

    // ---- Minions (U15/U16/U19) ----
    bool IsUnholyMinion(MinionKind kind)
    {
        switch (kind)
        {
            case MinionKind::Ghoul:
            case MinionKind::LesserGhoul:
            case MinionKind::Abomination:
            case MinionKind::Gargoyle:
            case MinionKind::ArmyGhoul:
                return true;
            default:
                return false;   // None (Dancing Rune Weapon included) and Bloodworm
        }
    }

    bool SubtractsMinionBaseAp(MinionKind kind)
    {
        // U15: 26125's IsPetGhoul base (589 + Str + Agi) is about half its AP at the sim footing.
        return kind == MinionKind::Ghoul;
    }

    int32 GetMinionMirrorAttackPower(Player const* owner, Unit const* minion)
    {
        if (!owner || !minion)
            return 0;

        MinionKind const kind = GetMinionKind(minion);
        float const ownerAp = std::max(0.0f, owner->GetTotalAttackPowerValue(BASE_ATTACK) -
            GetSharedAttackPowerBonus(owner, minion));
        int32 const share = SharePct(ownerAp, GetMinionApSharePct(kind));
        if (!SubtractsMinionBaseAp(kind))
            return std::max<int32>(0, share);

        // D12: the ghoul's own base AP (Guardian::UpdateAttackPowerAndDamage BASE_VALUE x BASE_PCT; it moves with
        // Str / Agi, so it is re-read every refresh). Negative is a normal flat: the total clamps at 0.
        float const baseAp = minion->GetFlatModifierValue(UNIT_MOD_ATTACK_POWER, BASE_VALUE) *
            minion->GetPctModifierValue(UNIT_MOD_ATTACK_POWER, BASE_PCT);
        return share - int32(std::lround(baseAp));
    }

    float GetUnholyMinionTerms(Player const* owner, SpellInfo const* spellInfo)
    {
        if (!owner)
            return 1.0f;

        float multiplier = 1.0f;
        AddPct(multiplier, GetDreadHostPct(owner));
        multiplier *= 1.0f + float(GetAllWillServePct(owner)) / 100.0f;

        if (Aura const* necromancy = owner->GetAura(DeathKnightData::SPELL_GARGOYLE_NECROMANCY, owner->GetGUID()))
            multiplier *= 1.0f + float(necromancy->GetStackAmount()) *
                float(DeathKnightData::GARGOYLE_NECROMANCY_PCT) / 100.0f;

        // WP-R m9 / D17: only the owner's own Death Knight auras (Desolation...), never party or raid %-done buffs the
        // pet may already hold itself.
        uint32 const schoolMask = spellInfo ? uint32(spellInfo->GetSchoolMask()) : uint32(SPELL_SCHOOL_MASK_NORMAL);
        ObjectGuid const ownerGuid = owner->GetGUID();
        multiplier *= owner->GetTotalAuraMultiplier(SPELL_AURA_MOD_DAMAGE_PERCENT_DONE,
            [schoolMask, ownerGuid](AuraEffect const* aurEff)
        {
            SpellInfo const* auraInfo = aurEff->GetSpellInfo();
            if (auraInfo->SpellFamilyName != SPELLFAMILY_DEATHKNIGHT || auraInfo->EquippedItemClass != -1)
                return false;

            return aurEff->GetCasterGUID() == ownerGuid && (uint32(aurEff->GetMiscValue()) & schoolMask) != 0;
        });
        return multiplier;
    }

    void CapMinions(Player* dk, uint32 entry, uint32 cap)
    {
        if (!dk)
            return;

        // UnSummon only queues the removal (AddObjectToRemoveList) and GetLiveMinions works on a copy, so nothing
        // here touches m_Controlled while it is read. Minions already queued for removal are skipped.
        std::vector<Creature*> minions = GetLiveMinions(dk, entry);
        if (minions.size() <= cap)
            return;

        // Oldest first: the least time left.
        std::vector<std::pair<int64, TempSummon*>> byRemaining;
        for (Creature* creature : minions)
            if (TempSummon* summon = creature->ToTempSummon())
                byRemaining.emplace_back(RemainingMs(creature), summon);

        if (byRemaining.size() <= cap)
            return;

        std::sort(byRemaining.begin(), byRemaining.end(), [](auto const& a, auto const& b)
        {
            return a.first < b.first;
        });

        std::size_t const excess = byRemaining.size() - std::size_t(cap);
        for (std::size_t i = 0; i < excess; ++i)
            byRemaining[i].second->UnSummon();
    }

    void StartLesserGhoulTimer(Creature* ghoul, uint32 durationMs)
    {
        if (!ghoul || !durationMs || ghoul->CustomData.Get<LesserGhoulTimer>(LESSER_GHOUL_TIMER_KEY))
            return;

        LesserGhoulTimer* timer = ghoul->CustomData.GetDefault<LesserGhoulTimer>(LESSER_GHOUL_TIMER_KEY);
        timer->startMs = NowMs();
        timer->totalMs = durationMs;
    }

    Creature* SummonLesserGhoul(Player* dk, Unit* target)
    {
        if (!dk || !target || !dk->IsInWorld() || target->GetMap() != dk->GetMap())
            return nullptr;

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(DeathKnightData::SPELL_LESSER_GHOUL_SUMMON);
        if (!spellInfo)
            return nullptr;

        GuidSet before;
        for (Creature* ghoul : GetLiveMinions(dk, DeathKnightData::NPC_LESSER_GHOUL))
            before.insert(ghoul->GetGUID());

        // The unit the ghoul attacks first, only if the DK may attack it (not a Coil at the friendly ghoul). Kept on
        // the DK across the cast so OnMinionAddWorld can copy it before the AI's IsSummonedBy runs (WP-R m3).
        ObjectGuid const attackTarget = target->IsAlive() && dk->IsValidAttackTarget(target) ? target->GetGUID() :
            ObjectGuid::Empty;
        dk->CustomData.GetDefault<LesserGhoulSummonTarget>(LESSER_GHOUL_TARGET_KEY)->target = attackTarget;

        // D17: 203469 is SUMMON props 61 at TARGET_DEST_DEST, cast at the target's position, so a friendly or a
        // just-killed target works too. Instant and triggered: the ghoul exists (and is in m_Controlled) when the
        // cast returns. Its AfterCast script caps and recounts too (harmless repeat).
        SpellCastTargets targets;
        targets.SetDst(target->GetPosition());
        dk->CastSpell(targets, spellInfo, nullptr, TRIGGERED_FULL_MASK);
        dk->CustomData.Erase(LESSER_GHOUL_TARGET_KEY);

        Creature* summoned = nullptr;
        for (Creature* ghoul : GetLiveMinions(dk, DeathKnightData::NPC_LESSER_GHOUL))
            if (!before.count(ghoul->GetGUID()))
                summoned = ghoul;

        if (summoned)
        {
            if (TempSummon* summon = summoned->ToTempSummon())
                StartLesserGhoulTimer(summoned, summon->GetTimer());   // the actual duration (Night of the Dead in)

            summoned->CustomData.GetDefault<LesserGhoulSummonTarget>(LESSER_GHOUL_TARGET_KEY)->target = attackTarget;
        }

        uint32 const cap = uint32(std::max<int32>(1, DeathKnightData::LESSER_GHOUL_CAP));
        CapMinions(dk, DeathKnightData::NPC_LESSER_GHOUL, cap);
        RefreshLesserGhoulCounter(dk);

        // The new ghoul has the most time left, so the cap never takes it.
        return summoned;
    }

    void RefreshLesserGhoulCounter(Player* dk)
    {
        if (!dk || !dk->IsInWorld())
            return;

        int32 const count = int32(GetLiveMinions(dk, DeathKnightData::NPC_LESSER_GHOUL).size());
        Aura* counter = dk->GetAura(DeathKnightData::SPELL_LESSER_GHOUL_COUNTER, dk->GetGUID());
        if (!count)
        {
            if (counter)
                dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_LESSER_GHOUL_COUNTER, dk->GetGUID());
            return;
        }

        if (!counter)
        {
            AddAuraStacks(dk, dk, DeathKnightData::SPELL_LESSER_GHOUL_COUNTER, count, true);
            return;
        }

        // A new ghoul refreshes the buff (ModStackAmount); a loss only lowers the count.
        int32 const current = int32(counter->GetStackAmount());
        if (count > current)
            counter->ModStackAmount(count - current);
        else if (count < current)
            counter->SetStackAmount(uint8(count));
    }

    Creature* FindCorpseExplosionGhoul(Player* dk)
    {
        if (!dk)
            return nullptr;

        // The DK's Lesser Ghoul within LESSER_GHOUL_RANGE_YARDS with the most time left.
        float const range = float(std::max<int32>(0, DeathKnightData::LESSER_GHOUL_RANGE_YARDS));
        Creature* best = nullptr;
        int64 bestRemaining = 0;
        for (Creature* ghoul : GetLiveMinions(dk, DeathKnightData::NPC_LESSER_GHOUL))
        {
            if (!dk->IsWithinDistInMap(ghoul, range))
                continue;

            int64 const remaining = RemainingMs(ghoul);
            if (!best || remaining > bestRemaining)
            {
                best = ghoul;
                bestRemaining = remaining;
            }
        }

        return best;
    }

    ObjectGuid GetLesserGhoulSummonTarget(Creature const* ghoul)
    {
        LesserGhoulSummonTarget const* record = ghoul ?
            ghoul->CustomData.Get<LesserGhoulSummonTarget>(LESSER_GHOUL_TARGET_KEY) : nullptr;
        return record ? record->target : ObjectGuid::Empty;
    }

    float GetLesserGhoulRemainingFraction(Creature const* ghoul)
    {
        // D9: from the CustomData record only (TempSummon::GetTimer is non-const); no record = full.
        LesserGhoulTimer const* timer = ghoul ? ghoul->CustomData.Get<LesserGhoulTimer>(LESSER_GHOUL_TIMER_KEY) :
            nullptr;
        if (!timer || !timer->totalMs)
            return 1.0f;

        int64 const left = timer->startMs + int64(timer->totalMs) - NowMs();
        return std::clamp(float(left) / float(timer->totalMs), 0.0f, 1.0f);
    }

    // ---- Gargoyle (U17/U18) ----
    Creature* GetActiveGargoyle(Player const* dk)
    {
        if (!dk)
            return nullptr;

        // Out and not yet flown away (OnGargoyleLeave marks it).
        for (Creature* gargoyle : GetLiveMinions(dk, DeathKnightData::NPC_EBON_GARGOYLE))
        {
            GargoyleState const* state = gargoyle->CustomData.Get<GargoyleState>(GARGOYLE_STATE_KEY);
            if (!state || !state->left)
                return gargoyle;
        }

        return nullptr;
    }

    void OnGargoyleStrikeHit(Player* dk, Unit* target)
    {
        if (!dk || !target)
            return;

        // A strike missile landing after the fly-away (OnGargoyleLeave) does nothing.
        Creature const* gargoyle = GetActiveGargoyle(dk);
        if (!gargoyle)
            return;

        if (!HasNecromancy(dk))
        {
            AddFesteringWounds(dk, target, 1, WoundSource::Gargoyle);
            return;
        }

        // Necromancy: +1 stack of the DK buff (cap GARGOYLE_NECROMANCY_MAX_STACKS), never outlasting the window.
        int32 const windowLeft = GargoyleWindowLeftMs(gargoyle);
        if (windowLeft <= 0)
            return;

        int32 const cap = std::max<int32>(1, DeathKnightData::GARGOYLE_NECROMANCY_MAX_STACKS);
        Aura* aura = dk->GetAura(DeathKnightData::SPELL_GARGOYLE_NECROMANCY, dk->GetGUID());
        if (aura && int32(aura->GetStackAmount()) >= cap)
            aura->RefreshDuration();
        else
            aura = AddAuraStacks(dk, dk, DeathKnightData::SPELL_GARGOYLE_NECROMANCY, 1, true);

        if (aura && (aura->GetDuration() < 0 || aura->GetDuration() > windowLeft))
        {
            aura->SetMaxDuration(windowLeft);
            aura->SetDuration(windowLeft);
        }
    }

    void OnGargoyleLeave(Player* dk)
    {
        if (!dk)
            return;

        // Fly-away (the AI) or the remove-world fallback: the minions' Necromancy bonus leaves with it.
        for (Creature* gargoyle : GetLiveMinions(dk, DeathKnightData::NPC_EBON_GARGOYLE))
            gargoyle->CustomData.GetDefault<GargoyleState>(GARGOYLE_STATE_KEY)->left = true;

        dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_GARGOYLE_NECROMANCY, dk->GetGUID());
        dk->CustomData.Erase(GARGOYLE_RAMP_KEY);
    }

    // ---- Ghoul (U22/U23) ----
    void AddShadowInfusion(Player* dk)
    {
        if (!dk)
            return;

        // WP-R m7: only a DK who knows Dark Transformation; the Master of Ghouls pet, alive and not transformed.
        if (!dk->HasSpell(DeathKnightData::SPELL_DARK_TRANSFORMATION))
            return;

        Creature* ghoul = GetPetGhoul(dk);
        if (!ghoul || ghoul->HasAura(DeathKnightData::SPELL_DARK_TRANSFORMATION))
            return;

        Aura* aura = AddAuraStacks(dk, ghoul, DeathKnightData::SPELL_SHADOW_INFUSION, 1, false);
        if (aura)
            OnShadowInfusionChanged(ghoul, aura->GetStackAmount());
    }

    void OnShadowInfusionChanged(Unit* ghoul, uint8 stacks)
    {
        Player* owner = GetMinionOwner(ghoul);
        if (!owner)
            return;

        bool const ready = stacks >= uint8(std::clamp<int32>(DeathKnightData::SHADOW_INFUSION_STACKS, 1, 255)) &&
            owner->HasSpell(DeathKnightData::SPELL_DARK_TRANSFORMATION);
        bool const marked = owner->HasAura(DeathKnightData::SPELL_DARK_TRANSFORMATION_READY, owner->GetGUID());
        if (ready && !marked)
            owner->CastSpell(owner, DeathKnightData::SPELL_DARK_TRANSFORMATION_READY, TRIGGERED_FULL_MASK);
        else if (!ready && marked)
            owner->RemoveAurasDueToSpell(DeathKnightData::SPELL_DARK_TRANSFORMATION_READY, owner->GetGUID());
    }

    void ApplyInfectedClaws(Player* dk, Pet* ghoul)
    {
        if (!dk || !ghoul || GetMinionKind(ghoul) != MinionKind::Ghoul || GetMinionOwner(ghoul) != dk)
            return;

        bool const known = dk->HasAura(DeathKnightData::SPELL_INFECTED_CLAWS_203444) ||
            dk->HasAura(DeathKnightData::SPELL_INFECTED_CLAWS);
        if (known)
        {
            // Owner-cast so the DK's Proc Chance applies (CalcProcChance reads a player caster).
            if (!ghoul->GetAura(DeathKnightData::SPELL_INFECTED_CLAWS_AURA, dk->GetGUID()))
                dk->AddAura(DeathKnightData::SPELL_INFECTED_CLAWS_AURA, ghoul);

            // D6: the pet-spellbook display passive.
            if (!ghoul->HasSpell(DeathKnightData::SPELL_INFECTED_CLAWS_DISPLAY))
                ghoul->learnSpell(DeathKnightData::SPELL_INFECTED_CLAWS_DISPLAY);
            return;
        }

        ghoul->RemoveAurasDueToSpell(DeathKnightData::SPELL_INFECTED_CLAWS_AURA);
        if (ghoul->HasSpell(DeathKnightData::SPELL_INFECTED_CLAWS_DISPLAY))
            ghoul->removeSpell(DeathKnightData::SPELL_INFECTED_CLAWS_DISPLAY, false);
    }

    // ---- Pestilence (U26) ----
    bool HasOnAPaleHorse(Unit const* dk)
    {
        return dk && dk->IsPlayer() && (dk->HasAura(DeathKnightData::SPELL_ON_A_PALE_HORSE_51983) ||
            dk->HasAura(SPELL_ON_A_PALE_HORSE_51986));
    }

    void OnPestilencePrimary(Player* dk, Unit* primary)
    {
        CastOnAPaleHorse(dk, primary);
    }

    // ---- Pre-agreed additions ----
    void RecordRottenTouchTarget(Player* dk, ObjectGuid target)
    {
        if (!dk || !target)
            return;

        RottenTouchRecord* record = dk->CustomData.GetDefault<RottenTouchRecord>(ROTTEN_TOUCH_KEY);
        record->target = target;
        record->timeMs = NowMs();
    }

    bool ConsumeRottenTouchTarget(Player* dk, ObjectGuid target)
    {
        if (!dk || !target)
            return false;

        RottenTouchRecord* record = dk->CustomData.Get<RottenTouchRecord>(ROTTEN_TOUCH_KEY);
        if (!record || record->target != target)
            return false;

        bool const fresh = NowMs() - record->timeMs <= ROTTEN_TOUCH_RECORD_MS;
        dk->CustomData.Erase(ROTTEN_TOUCH_KEY);
        return fresh;
    }

    // ---- Hook bodies ----
    void OnMinionAddWorld(Creature* creature)
    {
        if (!creature)
            return;

        uint32 const entry = creature->GetEntry();
        if (entry != DeathKnightData::NPC_LESSER_GHOUL && entry != DeathKnightData::NPC_EBON_GARGOYLE)
            return;

        Player* owner = GetMinionOwner(creature);
        if (!owner)
            return;

        if (entry == DeathKnightData::NPC_LESSER_GHOUL)
        {
            // InitStats set the timer to the full duration before AddToMap (Night of the Dead included).
            if (TempSummon* summon = creature->ToTempSummon())
                StartLesserGhoulTimer(creature, summon->GetTimer());

            // A SummonLesserGhoul cast in progress: hand its attack target to the ghoul before IsSummonedBy.
            if (LesserGhoulSummonTarget const* pending =
                owner->CustomData.Get<LesserGhoulSummonTarget>(LESSER_GHOUL_TARGET_KEY))
                creature->CustomData.GetDefault<LesserGhoulSummonTarget>(LESSER_GHOUL_TARGET_KEY)->target =
                    pending->target;

            RefreshLesserGhoulCounter(owner);
            return;
        }

        GargoyleState* state = creature->CustomData.GetDefault<GargoyleState>(GARGOYLE_STATE_KEY);
        state->startMs = NowMs();
        state->left = false;
    }

    void OnMinionRemoveWorld(Creature* creature)
    {
        if (!creature)
            return;

        uint32 const entry = creature->GetEntry();
        if (entry != DeathKnightData::NPC_LESSER_GHOUL && entry != DeathKnightData::NPC_EBON_GARGOYLE)
            return;

        // Already out of m_Controlled here; the owner GUID still resolves on the same map.
        Player* owner = GetMinionOwner(creature);
        if (entry == DeathKnightData::NPC_LESSER_GHOUL)
        {
            creature->CustomData.Erase(LESSER_GHOUL_TIMER_KEY);
            creature->CustomData.Erase(LESSER_GHOUL_TARGET_KEY);
            if (owner)
                RefreshLesserGhoulCounter(owner);
            return;
        }

        GargoyleState const* state = creature->CustomData.Get<GargoyleState>(GARGOYLE_STATE_KEY);
        bool const alreadyLeft = state && state->left;
        creature->CustomData.Erase(GARGOYLE_STATE_KEY);

        // Fallback for every leave path that skipped the fly-away (owner death, logout, despawn). Never strip a
        // newer Gargoyle's stacks.
        if (owner && !alreadyLeft && !GetActiveGargoyle(owner))
            OnGargoyleLeave(owner);
    }

    void OnDeathKnightMapChanged(Player* dk)
    {
        if (!dk)
            return;

        // Minions left behind on the old map were removed where the owner no longer resolves: resync.
        RefreshLesserGhoulCounter(dk);
        if (!GetActiveGargoyle(dk))
        {
            dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_GARGOYLE_NECROMANCY, dk->GetGUID());
            dk->CustomData.Erase(GARGOYLE_RAMP_KEY);
        }

        Creature* ghoul = GetPetGhoul(dk);
        Aura const* infusion = ghoul ? ghoul->GetAura(DeathKnightData::SPELL_SHADOW_INFUSION) : nullptr;
        if (!infusion && dk->HasAura(DeathKnightData::SPELL_DARK_TRANSFORMATION_READY, dk->GetGUID()))
            dk->RemoveAurasDueToSpell(DeathKnightData::SPELL_DARK_TRANSFORMATION_READY, dk->GetGUID());
    }
}
