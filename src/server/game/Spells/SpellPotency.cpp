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
#include "DatabaseEnv.h"
#include "Log.h"
#include "QueryResult.h"
#include "Random.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"

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
        perPoint += row.CpAp * caster->GetTotalAttackPowerValue(BASE_ATTACK);
        value += perPoint * float(comboPoints);
    }

    return value;
}

bool SpellPotency::HasRow(uint32 spellId, uint8 effIndex)
{
    return g_potencyCorrections.find(PotencyKey(spellId, effIndex)) != g_potencyCorrections.end();
}
