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

#include "PriestMechanics.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "Util.h"

namespace
{
    // void_eruption_buff_200140's own SpellIconID (apps/dbc-tools/source/classes/priest/
    // priest_trigger_spells.py, mined into SpellIcon.dbc by apps/dbc-tools/build_patch_i.py's
    // ICON_ID_VOID_ERUPTION) - keep in sync if that spell's icon ever changes.
    constexpr uint32 PRIEST_ICON_VOIDFORM = 90104;
}

namespace Priest
{
    void ApplyDoneDamagePctMods(Unit* caster, Unit* /*victim*/, SpellInfo const* spellProto, DamageEffectType damagetype, float& doneTotalMod)
    {
        // Voidform (docs/reworks/priest-new-spells.md, Void Eruption): "increases your periodic
        // Shadow damage by 10%." damagetype distinguishes a DoT tick from direct damage - the only
        // caster-side signal that lets this scope to "periodic" without a dedicated AuraType.
        if (damagetype != DOT)
            return;

        if (!(spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_SHADOW))
            return;

        if (AuraEffect const* voidform = caster->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_VOIDFORM, EFFECT_0))
            AddPct(doneTotalMod, voidform->GetAmount());
    }
}
