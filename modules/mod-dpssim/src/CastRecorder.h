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
// Fires for triggered/proc spells too (e.g. Missile Barrage's free Arcane Missiles cast, or a
// talent's passive effect being granted via an internal CastSpell(..., true) when learned), not
// just player/bot-initiated ones - Spell::cast() has no "was this triggered" branch around the
// hook call. Recorded here regardless (Spell::IsTriggered() is captured per-event as `IsTriggered`
// below) rather than filtered out at the source: the 2026-09-13 follow-up request ("differentiate
// cast spells from buffs") needs to tell the two apart, not lose one of them - see
// report-template.html's cast-log rendering for how `IsTriggered` splits a cast between the visible
// "cast" column (false - required a deliberate CastSpell(..., triggered=false), i.e. "requires a
// button press" in the user's own words) and the "buffs applied" column of the preceding real cast
// (true - fired on its own, no button press).
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
        // Spell::IsTriggered() at cast time - true for a proc/internal CastSpell(..., true) (a
        // Missile Barrage free cast, a talent's passive effect being granted, a spell-linked
        // trigger, ...), false for a deliberate CastSpell(..., triggered=false) - what the user
        // that requested this field called "requires a button press". See this class's own doc
        // comment for how the report uses it.
        bool IsTriggered;
    };
    [[nodiscard]] std::vector<CastEvent> const& GetCastEvents() const { return _castEvents; }

    // See EventRecorder::Reset()'s doc comment - same reasoning, same "only between iterations"
    // caveat, for SimDaemon::RunPlayerbotBatch().
    void Reset() { _castEvents.clear(); }

private:
    ObjectGuid _actorGuid;
    std::vector<CastEvent> _castEvents;
};

#endif
