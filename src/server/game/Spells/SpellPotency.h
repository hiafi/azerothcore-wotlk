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

    /// True when any effect of `spellId` has a loaded row - the spell is declared with potency in
    /// dbc-tools, weapon potency included (the generator writes an all-zero marker row for a pure
    /// weapon-percent effect, which has no correction of its own). The spell-level gate for a
    /// hard-coded stock bonus that is not tied to one effect: Rune Strike's 0.15 x AP and Kill
    /// Shot's 0.4 x RAP in Spell::EffectWeaponDmg (potency audit S2, F11, F14).
    bool IsDeclared(uint32 spellId);

    // Custom: gear-scaling GS2 D - attack power abilities grow with the weapon
    // (.agents/plans/gear-scaling, GS1 proposal "Potency, attack power abilities"). The attack power share of a potency
    // effect's flat part (the part on C(L)) is multiplied by main-hand weapon DPS / the reference weapon DPS for the
    // caster's level and the weapon's hand type: item_weapon_dps_curve at the level's reference item level, Rare at 60+
    // and Uncommon below 60. The
    // attack power coefficient is untouched. Applied inside Apply(); the tooltip keeps showing the reference value.

    /// WeaponScaling.ApPotencyReferenceItemLevel, set once at startup (custom_weapon_scaling.cpp). 0 turns the
    /// weapon factor off.
    void SetApWeaponReferenceItemLevel(uint32 itemLevel);
    uint32 GetApWeaponReferenceItemLevel();

    /// Fills the per-level reference DPS cache from item_weapon_dps_curve (ItemBudget). Called from OnStartup, after
    /// the config and the item templates have loaded.
    void BuildApWeaponReference();

    /// The reference item level for a caster level: the configured item level at 60 and above; below 60 the item
    /// level of a weapon a player of that level wears (required level + 5), capped at the configured item level.
    /// 0 when the configured item level is 0.
    uint32 ApWeaponReferenceItemLevel(uint8 level, uint32 itemLevelAt60);

    /// The reference weapon's quality for a caster level: Rare (3) at 60 and above, Uncommon (2) below 60, where
    /// levelers wear greens.
    uint32 ApWeaponReferenceQuality(uint8 level);

    /// The attack power share of a potency effect's flat part, from its spell_bonus_data coefficients (the pair for
    /// the effect's kind): 1 for a pure attack power effect, 0 with no attack power coefficient, else the hybrid
    /// split dbc-tools bakes (lib/potency.py: a_ap x P_ap over a_sp x P_sp + a_ap x P_ap).
    float ApFlatShare(float spCoefficient, float apCoefficient);

    /// The multiplier on the whole flat part: 1 + share x (weapon DPS / reference DPS - 1). 1 when either DPS is 0.
    float ApWeaponFlatMultiplier(float share, float weaponDps, float referenceDps);
}

#endif
