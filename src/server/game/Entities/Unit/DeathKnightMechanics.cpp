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
#include <limits>

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

    void OnPestilenceCopy(Player* /*dk*/, Unit* /*source*/, Unit* /*target*/)
    {
        // Intentionally empty in DK0a: Pestilence's copy rules (skip a target that already has the caster's disease,
        // no Glyph of Disease refresh) live in spell_dk_pestilence_rework. S3 adds the Unholy wound copies and On a
        // Pale Horse here; the script already calls this once per enemy a copy reached.
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

    // Once-per-cast fallback for a cast with no unit target (self-centred AoE such as Blood Boil, Death and Decay's
    // ticks): the first hit of that Spell object rolls, the rest skip. Hits of one cast land in the same server tick
    // (Spell::DoAllEffectOnTarget), so the time stamp keeps a later cast that reuses the address from matching.
    struct RuneCastGuard : DataMap::Base
    {
        Spell const* spell = nullptr;
        uint32 spellId = 0;
        int64 timeMs = -1;
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

    bool RuneProcAllowed(Unit const* runeOwner, ProcEventInfo& eventInfo, bool dualWieldHalf, bool oncePerCast)
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
                if (guard->spell == spell && guard->spellId == spellId && guard->timeMs == now)
                    return false;

                guard->spell = spell;
                guard->spellId = spellId;
                guard->timeMs = now;
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

        // 203056: eff0 attack power, eff1 spell power (Gargoyle only), both from the owner's total melee attack power
        // (U8: no subtraction of the minion's own base AP).
        // The pet ghoul is a real Pet with no stat immunities, so party AP buffs the owner also has already count once
        // on it: leave them out of the copy (same shape as GetSharedCritBonus).
        float const ownerAp = std::max(0.0f, owner->GetTotalAttackPowerValue(BASE_ATTACK) -
            GetSharedAttackPowerBonus(owner, minion));
        if (Aura* mirror = minion->GetAura(DeathKnightData::SPELL_MINION_MIRROR, ownerGuid))
        {
            SetEffectAmount(mirror, EFFECT_0,
                std::max<int32>(0, SharePct(ownerAp, DeathKnightData::MINION_AP_SHARE_PCT)));
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
            SetEffectAmount(critHaste, EFFECT_0,
                std::max<int32>(0, SharePct(critShare, DeathKnightData::MINION_CRIT_SHARE_PCT)));

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

    float GetMinionDamageMultiplier(Player const* /*owner*/, Unit const* /*minion*/, SpellInfo const* /*spellInfo*/)
    {
        // U10 seam: no term in DK0b. S1/S3 add theirs (Mastery, percent mods) together with the per-hit hooks.
        return 1.0f;
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
