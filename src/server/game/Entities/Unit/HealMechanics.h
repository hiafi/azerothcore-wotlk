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

#ifndef __HEALMECHANICS_H
#define __HEALMECHANICS_H

class SpellInfo;

/*
 * Class-neutral healing-spell classification helpers. Created by the druid Restoration pass
 * (.agents/plans/druid-rework/druid-rework.RESTO.md §0.13 Q4, WP-0 item 5) specifically so this
 * rule does not live inside `namespace Druid` (DruidMechanics.h) - a later Shaman rework (or any
 * other healer) can call straight into this file instead of re-deriving the same classification.
 * Mirrors DruidMechanics.h/.cpp's "one small fork file, one function per mechanic" shape, just
 * namespaced by concept (`Heal::`) rather than by class, since nothing here is class-specific.
 */
namespace Heal
{
    // "Direct Nature healing spell" (RESTO §0.13 Q4): a rule, not an id list, so it stays correct
    // as new spells are added. True for a class-family spell (SpellFamilyName != SPELLFAMILY_GENERIC
    // - excludes generic/item spells) with a Nature school and a direct SPELL_EFFECT_HEAL effect,
    // minus a per-class never-list of nature-school heals that mechanically match but must never
    // count: periodic-only triggered heals, bloom/seed payloads, and anything whose "direct heal"
    // shape is an implementation detail rather than a real cast the class's talents should see.
    // Druid's never-list (RESTO §9): 44203 (Tranquility's per-tick triggered heal), 33778
    // (Lifebloom's bloom), 48503 (Living Seed's bloom), 200569 (Ysera's Gift), 200574 (Tree of
    // Life's instant Rejuvenation heal), 50464 (Nourish - removed; kept so it can never
    // accidentally re-qualify if the spell row is ever touched again).
    // Callers must independently reject periodic/triggered *events* themselves (a proc's
    // `PROC_FLAG_DONE_PERIODIC`, or `damagetype == DOT` in a calculation hook) - this function only
    // classifies the spell definition, not the event that invoked it.
    bool IsDirectNatureHeal(SpellInfo const* spellInfo);
}

#endif
