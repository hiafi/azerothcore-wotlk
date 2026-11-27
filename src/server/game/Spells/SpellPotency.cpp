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

#include "SpellPotency.h"
#include "DBCStores.h"
#include "DatabaseEnv.h"
#include "ItemBudget.h"
#include "Log.h"
#include "Player.h"
#include "QueryResult.h"
#include "Random.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"

#include <algorithm>
#include <array>
#include <unordered_map>

namespace
{
    struct PotencyCorrectionRow
    {
        float CorrectionPerLevel = 0.0f;
        uint8 BreakpointLevel = 0;
        float VariancePct = 0.0f;
        // Finishers (docs/potency-system.md's "Combo points don't scale with level" / PLAN P6 step
        // 4) - CpLine is a flat per-combo-point value (no per-level field of its own, unlike the
        // main line above - the DBC's EffectPointsPerCombo_N has none either), CpCorrectionPerLevel
        // its own low-level top-up (same shape as CorrectionPerLevel/BreakpointLevel, just scaled
        // per combo point), CpAp the attack-power coefficient per combo point. All three are 0 for
        // every non-finisher row.
        float CpLine = 0.0f;
        float CpCorrectionPerLevel = 0.0f;
        float CpAp = 0.0f;
    };

    /// (spellId, effIndex) packed into one key - effIndex only ever needs 2 bits (MAX_SPELL_EFFECTS
    /// is 3), so the low byte is more than enough room and keeps this a plain integer key with no
    /// custom hash/pair needed.
    constexpr uint64 PotencyKey(uint32 spellId, uint8 effIndex)
    {
        return (uint64(spellId) << 8) | effIndex;
    }

    std::unordered_map<uint64, PotencyCorrectionRow> g_potencyCorrections;

    // Custom: gear-scaling GS2 D - attack power weapon factor. Both are written once at startup (OnAfterConfigLoad,
    // OnStartup), before any map update, and only read afterwards.
    uint32 g_apWeaponReferenceItemLevel = 0;
    // Reference weapon DPS by caster level, [level][0] one-hand (paired slot), [level][1] two-hand. 0 = no curve row.
    std::array<std::array<float, 2>, 256> g_apWeaponReferenceDps{};

    // dbc-tools' potency constants (apps/dbc-tools/lib/potency.py: DEFAULT_R, SP_BASE_SCALE, SP_COEF_SCALE,
    // AP_BASE_SCALE, AP_COEF_SCALE), used only to split a hybrid's flat part into its spell and attack power shares.
    // A retune there moves a hybrid's share slightly; pure attack power effects do not depend on them.
    constexpr float POTENCY_R = 2.15f;
    constexpr float POTENCY_SP_BASE_SCALE = 0.48f;
    constexpr float POTENCY_SP_COEF_SCALE = 1.93f;
    constexpr float POTENCY_AP_BASE_SCALE = 0.71f;
    constexpr float POTENCY_AP_COEF_SCALE = 2.49f;

    /// Heal and absorb effects keep their flat part: the weapon factor is for damage only.
    bool IsHealingEffect(SpellEffectInfo const& effect)
    {
        switch (effect.Effect)
        {
            case SPELL_EFFECT_HEAL:
            case SPELL_EFFECT_HEAL_MAX_HEALTH:
            case SPELL_EFFECT_HEAL_MECHANICAL:
            case SPELL_EFFECT_HEAL_PCT:
                return true;
            default:
                break;
        }

        switch (effect.ApplyAuraName)
        {
            case SPELL_AURA_PERIODIC_HEAL:
            case SPELL_AURA_OBS_MOD_HEALTH:
            case SPELL_AURA_SCHOOL_ABSORB:
            case SPELL_AURA_MANA_SHIELD:
                return true;
            default:
                return false;
        }
    }

    /// Main-hand weapon DPS, the heirloom ScalingStatValues DPS added as in the feral and ranged weapon scaling hooks
    /// (custom_weapon_scaling.cpp).
    float MainHandWeaponDps(Player const* player, ItemTemplate const* proto)
    {
        float dps = proto->getDPS();
        if (proto->ScalingStatValue)
        {
            uint32 level = player->GetLevel();
            if (ScalingStatDistributionEntry const* ssd = proto->ScalingStatDistribution ?
                sScalingStatDistributionStore.LookupEntry(proto->ScalingStatDistribution) : nullptr)
                level = std::min(level, ssd->MaxLevel);

            if (ScalingStatValuesEntry const* ssv = sScalingStatValuesStore.LookupEntry(level))
                dps += float(ssv->getDPSMod(proto->ScalingStatValue));
        }

        return dps;
    }

    /// The multiplier on this effect's flat part for this caster (1 when it does not apply). Out of scope: the key at
    /// 0, a non-player caster (pets, guardians, totems), Cat / Bear / Dire Bear form (form attack power already comes
    /// from the weapon), generic-family spells (item and set procs), spells that read ranged attack power (hunter
    /// shots: ranged attack power comes from the bow), heal and absorb effects, effects with no attack power
    /// coefficient, and no usable main-hand weapon.
    float ApWeaponFlatMultiplierFor(uint32 spellId, uint8 effIndex, Unit const* caster)
    {
        if (!g_apWeaponReferenceItemLevel)
            return 1.0f;

        Player const* player = caster->ToPlayer();
        if (!player)
            return 1.0f;

        ShapeshiftForm const form = player->GetShapeshiftForm();
        if (form == FORM_CAT || form == FORM_BEAR || form == FORM_DIREBEAR)
            return 1.0f;

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        if (!spellInfo || spellInfo->SpellFamilyName == SPELLFAMILY_GENERIC || effIndex >= MAX_SPELL_EFFECTS)
            return 1.0f;

        // The same test Unit::SpellDamageBonusDone uses to pick ranged attack power for ap_bonus / ap_dot_bonus.
        if (spellInfo->IsRangedWeaponSpell() && spellInfo->DmgClass != SPELL_DAMAGE_CLASS_MELEE)
            return 1.0f;

        SpellEffectInfo const& effect = spellInfo->Effects[effIndex];
        if (IsHealingEffect(effect))
            return 1.0f;

        SpellBonusEntry const* bonus = sSpellMgr->GetSpellBonusData(spellId);
        if (!bonus)
            return 1.0f;

        // The coefficient pair the damage reads: the DoT pair for a periodic effect, else the direct pair. When only
        // one pair has attack power, that one (Holy Shield's damage aura and Consecration's area aura read one pair).
        bool periodic = bonus->ap_dot_bonus > 0.0f;
        if (bonus->ap_bonus > 0.0f && bonus->ap_dot_bonus > 0.0f)
            periodic = effect.Amplitude != 0;

        float const share = SpellPotency::ApFlatShare(periodic ? bonus->dot_damage : bonus->direct_damage,
            periodic ? bonus->ap_dot_bonus : bonus->ap_bonus);
        if (share <= 0.0f)
            return 1.0f;

        Item const* weapon = player->GetWeaponForAttack(BASE_ATTACK, true);
        if (!weapon)
            return 1.0f;

        ItemTemplate const* proto = weapon->GetTemplate();
        uint8 const handType = ItemBudget::IsSingleSlotWeaponType(proto->InventoryType) ? 1 : 0;
        float const referenceDps = g_apWeaponReferenceDps[player->GetLevel()][handType];
        return SpellPotency::ApWeaponFlatMultiplier(share, MainHandWeaponDps(player, proto), referenceDps);
    }
}

void SpellPotency::Load()
{
    g_potencyCorrections.clear();

    // Plain query, not a PreparedStatement: this is a parameter-free startup/`.reload` load of a
    // small custom table, same idiom several stock command handlers already use for similar ad hoc
    // reads (e.g. cs_npc.cpp) - adding a new PreparedStatement entry would mean editing the
    // upstream-owned WorldDatabase statement enum for no real benefit here.
    QueryResult result = WorldDatabase.Query(
        "SELECT spell_id, effect_index, correction_per_level, breakpoint_level, variance_pct, "
        "cp_line, cp_correction_per_level, cp_ap FROM spell_potency_correction");
    if (!result)
    {
        LOG_INFO("server.loading", "Loaded 0 spell potency correction rows.");
        return;
    }

    uint32 count = 0;
    do
    {
        Field* fields = result->Fetch();
        uint32 spellId = fields[0].Get<uint32>();
        uint8 effIndex = fields[1].Get<uint8>();

        PotencyCorrectionRow row;
        row.CorrectionPerLevel = fields[2].Get<float>();
        row.BreakpointLevel = fields[3].Get<uint8>();
        row.VariancePct = fields[4].Get<float>();
        row.CpLine = fields[5].Get<float>();
        row.CpCorrectionPerLevel = fields[6].Get<float>();
        row.CpAp = fields[7].Get<float>();

        g_potencyCorrections[PotencyKey(spellId, effIndex)] = row;
        ++count;
    } while (result->NextRow());

    LOG_INFO("server.loading", "Loaded {} spell potency correction row(s).", count);
}

void SpellPotency::Validate()
{
    for (auto const& [key, row] : g_potencyCorrections)
    {
        uint32 spellId = uint32(key >> 8);
        uint8 effIndex = uint8(key & 0xFF);

        SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(spellId);
        if (!spellInfo)
        {
            LOG_ERROR("sql.sql", "spell_potency_correction references spell {} which does not exist.", spellId);
            continue;
        }

        if (effIndex >= MAX_SPELL_EFFECTS)
        {
            LOG_ERROR("sql.sql", "spell_potency_correction has an out-of-range effect_index {} for spell {}.", effIndex, spellId);
            continue;
        }

        // CalcValue anchors the native line at max(BaseLevel, SpellLevel), so only a SpellLevel above
        // BaseLevel shifts it. A lower one is harmless: SpellInfoCorrections zeroes SpellLevel on some
        // stock spells (Divine Hymn 64844, Lifebloom's bloom 33778).
        if (spellInfo->SpellLevel > spellInfo->BaseLevel)
        {
            LOG_ERROR("sql.sql", "spell_potency_correction's spell {} has SpellLevel ({}) > BaseLevel ({}); "
                "CalcValue anchors the native line at SpellLevel, so the correction formula is off "
                "(docs/potency-system.md's 'Caveats and checks').",
                spellId, spellInfo->SpellLevel, spellInfo->BaseLevel);
        }

        if (spellInfo->MaxLevel != 0)
        {
            LOG_ERROR("sql.sql", "spell_potency_correction's spell {} has MaxLevel {} (expected 0) - "
                "a nonzero MaxLevel caps the native line and the correction would then double count.",
                spellId, spellInfo->MaxLevel);
        }

        SpellEffectInfo const& effect = spellInfo->GetEffect(SpellEffIndex(effIndex));
        if (effect.DieSides != 1)
        {
            LOG_ERROR("sql.sql", "spell_potency_correction's spell {} effect {} has DieSides {} (expected 1) - "
                "the ±variance roll is applied in the hook, not via DieSides.",
                spellId, effIndex, effect.DieSides);
        }
    }
}

float SpellPotency::ApplyCorrection(float value, uint8 level, float correctionPerLevel, uint8 breakpointLevel, float variancePct)
{
    if (level < breakpointLevel)
        value += correctionPerLevel * float(breakpointLevel - level);

    if (variancePct > 0.0f)
        value *= frand(1.0f, 1.0f + variancePct / 100.0f);

    return value;
}

float SpellPotency::Apply(uint32 spellId, uint8 effIndex, Unit const* caster, float value)
{
    auto it = g_potencyCorrections.find(PotencyKey(spellId, effIndex));
    if (it == g_potencyCorrections.end())
        return value;

    PotencyCorrectionRow const& row = it->second;
    value = ApplyCorrection(value, caster->GetLevel(), row.CorrectionPerLevel, row.BreakpointLevel, row.VariancePct);

    // Custom: gear-scaling GS2 D - the attack power share of the flat part grows with the main-hand weapon. `value` is
    // the whole flat part here (the coefficients are added later, in SpellDamageBonusDone), so scaling it by
    // 1 + share x (factor - 1) scales exactly the attack power share. 1 outside the scope (see the helper).
    float const apFlatMultiplier = ApWeaponFlatMultiplierFor(spellId, effIndex, caster);
    value *= apFlatMultiplier;

    // Finishers (docs/potency-system.md's "Combo points don't scale with level" / PLAN P6 step 4):
    // CpLine/CpCorrectionPerLevel/CpAp are 0 for every non-finisher row, so this is a no-op there.
    // The per-combo-point line gets the same low-level correction shape as the flat line above, via
    // the same ApplyCorrection helper - but no variance roll (variance_pct 0.0f here), matching
    // where stock's own PointsPerComboPoint line lands in CalcValue: after the roll, never rolled
    // itself. The DBC's EffectPointsPerCombo_N is generated as 0 for a converted finisher, so this
    // entirely replaces it rather than adding on top.
    if (uint8 comboPoints = caster->GetComboPoints())
    {
        float perPoint = ApplyCorrection(row.CpLine, caster->GetLevel(), row.CpCorrectionPerLevel, row.BreakpointLevel, 0.0f);
        perPoint *= apFlatMultiplier; // Custom: gear-scaling GS2 D - the per-point flat line is on C(L) too
        perPoint +=row.CpAp * caster->GetTotalAttackPowerValue(BASE_ATTACK);
        value += perPoint * float(comboPoints);
    }

    return value;
}

bool SpellPotency::HasRow(uint32 spellId, uint8 effIndex)
{
    return g_potencyCorrections.find(PotencyKey(spellId, effIndex)) != g_potencyCorrections.end();
}

bool SpellPotency::IsDeclared(uint32 spellId)
{
    for (uint8 effIndex = 0; effIndex < MAX_SPELL_EFFECTS; ++effIndex)
        if (HasRow(spellId, effIndex))
            return true;

    return false;
}

// Custom: gear-scaling GS2 D - attack power weapon factor (see SpellPotency.h).
void SpellPotency::SetApWeaponReferenceItemLevel(uint32 itemLevel)
{
    g_apWeaponReferenceItemLevel = itemLevel;
}

uint32 SpellPotency::GetApWeaponReferenceItemLevel()
{
    return g_apWeaponReferenceItemLevel;
}

void SpellPotency::BuildApWeaponReference()
{
    for (uint32 level = 0; level < g_apWeaponReferenceDps.size(); ++level)
    {
        uint32 const itemLevel = ApWeaponReferenceItemLevel(uint8(level), g_apWeaponReferenceItemLevel);
        uint32 const quality = ApWeaponReferenceQuality(uint8(level));
        for (uint8 singleSlot = 0; singleSlot < 2; ++singleSlot)
            g_apWeaponReferenceDps[level][singleSlot] =
                itemLevel ? ItemBudget::GetWeaponDpsCurve(itemLevel, quality, singleSlot != 0) : 0.0f;
    }

    if (!g_apWeaponReferenceItemLevel)
        return;

    LOG_INFO("server.loading", "Attack power potency weapon factor on: reference item level {} Rare at level 60 "
        "({:.2f} DPS one-hand, {:.2f} DPS two-hand).", g_apWeaponReferenceItemLevel,
        g_apWeaponReferenceDps[60][0], g_apWeaponReferenceDps[60][1]);
    if (g_apWeaponReferenceDps[60][0] <= 0.0f || g_apWeaponReferenceDps[60][1] <= 0.0f)
        LOG_ERROR("server.loading", "WeaponScaling.ApPotencyReferenceItemLevel {} has no item_weapon_dps_curve Rare "
            "row for a hand type; that hand type keeps a weapon factor of 1.", g_apWeaponReferenceItemLevel);
}

uint32 SpellPotency::ApWeaponReferenceItemLevel(uint8 level, uint32 itemLevelAt60)
{
    if (!itemLevelAt60)
        return 0;

    if (level >= 60)
        return itemLevelAt60;

    return std::min<uint32>(uint32(level) + 5, itemLevelAt60);
}

uint32 SpellPotency::ApWeaponReferenceQuality(uint8 level)
{
    return level >= 60 ? ITEM_QUALITY_RARE : ITEM_QUALITY_UNCOMMON;
}

float SpellPotency::ApFlatShare(float spCoefficient, float apCoefficient)
{
    if (apCoefficient <= 0.0f)
        return 0.0f;

    if (spCoefficient <= 0.0f)
        return 1.0f;

    // Each coefficient back to its potency (sp = P_sp x b_sp x k, ap = P_ap x b_ap / R x k, same k = T / 350 on one
    // effect), then weighted by its side's base scale, as resolve() builds the flat part.
    float const apWeight = apCoefficient * POTENCY_R * POTENCY_AP_BASE_SCALE / POTENCY_AP_COEF_SCALE;
    float const spWeight = spCoefficient * POTENCY_SP_BASE_SCALE / POTENCY_SP_COEF_SCALE;
    return apWeight / (apWeight + spWeight);
}

float SpellPotency::ApWeaponFlatMultiplier(float share, float weaponDps, float referenceDps)
{
    if (share <= 0.0f || weaponDps <= 0.0f || referenceDps <= 0.0f)
        return 1.0f;

    return 1.0f + share * (weaponDps / referenceDps - 1.0f);
}
