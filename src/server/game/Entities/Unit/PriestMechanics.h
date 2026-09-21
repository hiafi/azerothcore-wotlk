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

#ifndef __PRIESTMECHANICS_H
#define __PRIESTMECHANICS_H

#include "Define.h"
#include "SharedDefines.h"

class SpellInfo;
class Unit;
enum DamageEffectType : uint8;

/*
 * Priest-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors MageMechanics.h's shape
 * (see that file's own header comment for the general rationale: Unit.cpp/core can't depend on
 * scripts/, so this can't live next to spell_priest_new.cpp).
 */
namespace Priest
{
    // Unit::SpellPctDamageModsDone's SPELLFAMILY_PRIEST case - Void Eruption's Voidform buff
    // (docs/reworks/priest-new-spells.md): "increases your periodic Shadow damage by 10% for 10
    // sec." No native WotLK AuraType computes "+X% periodic damage done", hence this live read
    // instead of a stock aura - see spell_priest_new.cpp's void_eruption_buff_200140 notes for the
    // marker-aura-by-icon idiom this uses.
    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, DamageEffectType damagetype, float& doneTotalMod);
}

#endif
