/*
 * This file is part of the AzerothCore Project. See AUTHORS file for Copyright information
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef MODULE_DPSSIM_CASTRECORDER_H
#define MODULE_DPSSIM_CASTRECORDER_H

#include "ObjectGuid.h"
#include "ScriptMgr.h"
#include <vector>

// Records every spell the sim actor actually casts - a "cast log", distinct from EventRecorder's
// "hit log" (landed direct-damage hits only, by design - see its own doc comment). Added
// 2026-09-13 because a hit log alone is blind to non-damage abilities (Evocation, self-buffs,
// interrupts, ...) that still matter for reading a rotation - a hit log has nothing to show for
// the several seconds an Evocation channel actually occupies.
//
// Deliberately a separate class from EventRecorder rather than widening it: EventRecorder is a
// UnitScript (hooks fire off Unit::CalculateSpellDamageTaken/OnAuraApply/OnAuraRemove, all
// target-of-an-effect events), but "a cast happened" has no equivalent UnitScript hook - the
// closest fit is AllSpellScript::OnSpellCast (ALLSPELLHOOK_ON_CAST), fired once from the tail of
// Spell::cast() for *every* successful cast, instant or not, damaging or not, targeted or not
// (self-buffs included) - see Spell.cpp. UnitScript and AllSpellScript are sibling ScriptObject
// subclasses; multiply inheriting both into one class isn't an established pattern anywhere in
// this codebase, so this stays its own small class instead of risking being the first.
//
// Fires for triggered/proc spells too (e.g. Missile Barrage's free Arcane Missiles cast), not just
// player-initiated ones - Spell::cast() has no "was this triggered" branch around the hook call.
// That's intentional here: a proc actually firing is exactly the kind of rotation detail a cast
// log exists to show, not noise to filter out.
//
// No rotationSpellId filter (unlike EventRecorder) - a cast log's whole point per the 2026-09-13
// request is to show every ability the actor uses, DPS or not, so there is nothing to filter by
// spell id here. Still filtered by caster GUID, since AllSpellScript::OnSpellCast fires globally
// for every Unit's every spell in the whole sim map (the target dummy included, though it never
// casts anything).
//
// Same heap-allocation/no-delete/runtime-construction rules as EventRecorder - see its own doc
// comment for the full reasoning (ScriptRegistry<AllSpellScript> owns this from construction
// onward, same as ScriptRegistry<UnitScript> owns EventRecorder).
class CastRecorder : public AllSpellScript
{
public:
    explicit CastRecorder(ObjectGuid actorGuid);

    void OnSpellCast(Spell* spell, Unit* caster, SpellInfo const* spellInfo, bool skipCheck) override;

    // One entry per successful cast, in cast order.
    struct CastEvent
    {
        uint32 TimestampMs;
        uint32 SpellId;
    };
    [[nodiscard]] std::vector<CastEvent> const& GetCastEvents() const { return _castEvents; }

private:
    ObjectGuid _actorGuid;
    std::vector<CastEvent> _castEvents;
};

#endif
