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

#ifndef SPELL_POTENCY_H
#define SPELL_POTENCY_H

#include "Define.h"

class Unit;

/**
 * The potency system's low-level correction + variance roll (docs/potency-system.md,
 * "Implementation" / "Where potency lives"). Potency itself lives only in apps/dbc-tools; the
 * server holds just the per-effect runtime inputs the linear DBC formula can't express, in the
 * `spell_potency_correction` table.
 */
namespace SpellPotency
{
    /// Loads `spell_potency_correction` into the in-memory table. Called from
    /// OnLoadCustomDatabaseTable (before DBC stores / SpellMgr are available - see World.cpp) and
    /// from `.reload spell_potency_correction`.
    void Load();

    /// Validates every loaded row against sSpellMgr once it's available: the spell exists, the
    /// effect index is valid, BaseLevel == SpellLevel, MaxLevel == 0, DieSides == 1 (see
    /// docs/potency-system.md's "Caveats and checks"). Logs problems to the `sql.sql` category.
    /// Called from OnStartup, once SpellMgr/DBC stores have loaded.
    void Validate();

    /// The pure correction math, with no caster or DB lookup: adds `correctionPerLevel` for every
    /// level below `breakpointLevel`, then (when `variancePct > 0`) rolls a random multiplier in
    /// [1, 1 + variancePct/100]. `value` is the effect's own native value - the result of the
    /// existing BasePoints + level*RealPointsPerLevel + DieSides-roll math `CalcValue` already
    /// performs, unmodified. Exposed separately from `Apply` so it's directly unit-testable
    /// (src/test/server/game/Spells/SpellPotencyTest.cpp) without needing a caster or a loaded
    /// correction table.
    float ApplyCorrection(float value, uint8 level, float correctionPerLevel, uint8 breakpointLevel, float variancePct);

    /// The real hook entry point, called from `SpellEffectInfo::CalcValue` (SpellInfo.cpp). Looks
    /// up the row for (spellId, effIndex); returns `value` unchanged if there's no row for this
    /// effect (most spells have none). `caster` supplies the level the correction uses - the
    /// caller already guards this against a null caster.
    float Apply(uint32 spellId, uint8 effIndex, Unit const* caster, float value);

    /// True when (spellId, effIndex) has a loaded `spell_potency_correction` row - i.e. this effect
    /// has been converted to the potency system. Used to gate the hard-coded, spell-ID-keyed
    /// attack-power math still living in SpellEffects.cpp (docs/potency-system.md's "Implementation
    /// catches") so it only runs for spells the potency system hasn't reached yet; once a spell
    /// converts, its generated spell_bonus_data ap_bonus/ap_dot_bonus coefficient is the only one
    /// that should apply, and this hard-coded addition would otherwise double it.
    bool HasRow(uint32 spellId, uint8 effIndex);
}

#endif
