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

/*
 * Combo points live on the player (druid-rework PLAN A11, FERAL §0.17, CORE-AUDIT row 39).
 *
 * Stock 3.3.5 keeps a unit's combo points on one target: a gain against a new target resets the
 * count (Unit::AddComboPoints), and that target's death, evade or removal wipes every holder's points
 * (Unit::ClearComboPointHolders). For player rogues and druids the points instead carry over to a new
 * target and survive the old one. They are still spent by a finisher and cleared by the player's
 * death, logout and duel end - all stock paths that call ClearComboPoints.
 *
 * The 3.3.5 client shows points, and allows a targeted finisher, only for the unit the server last
 * named in SMSG_UPDATE_COMBO_POINTS, and Spell::CheckCast wants the points on the spell's target. So
 * the points follow the player's hostile selection (RetargetComboPoints, from Player::SetSelection -
 * playerbots call it too) and the next builder's target (MoveComboPoints, from AddComboPoints).
 *
 * Points whose target is gone are parked on the player itself (m_comboTarget == this) rather than on
 * no unit at all: stock ClearComboPoints returns early when m_comboTarget is null, so a null target
 * would let a self-cast finisher (Slice and Dice, Savage Roar) spend nothing, and would carry the
 * points through death. Parked points can't reach a targeted finisher (GetComboPoints(target) is 0)
 * until the player selects or hits a new hostile unit.
 *
 * Warriors' Overpower and hunter pets' Wolverine Bite reuse the combo-point fields as a "target
 * dodged" flag (Unit.cpp ProcSkillsAndReactives/UpdateReactives) and keep stock behaviour: every
 * function here does nothing unless KeepsComboPointsOnSelf().
 *
 * Call sites (one line each, run before the stock code): top of Unit::AddComboPoints, top of
 * Unit::ClearComboPointHolders, end of Player::SetSelection.
 */

#include "Duration.h"
#include "ObjectAccessor.h"
#include "SharedDefines.h"
#include "Unit.h"
#include <vector>

bool Unit::KeepsComboPointsOnSelf() const
{
    return IsPlayer() && (getClass() == CLASS_ROGUE || getClass() == CLASS_DRUID);
}

// Re-points this unit's combo points at newTarget (this unit itself parks them), keeping the count,
// and tells the client unless send is false. Nothing to do without points: the stock AddComboPoints
// branch then starts a fresh count on the gain's target. A null newTarget is a no-op, so
// AddComboPoints(nullptr, n) from SPELL_AURA_RETAIN_COMBO_POINTS leaves the points where they are.
// AddComboPoints passes send=false when it's about to send its own packet either way (count != 0),
// so the client only gets one SMSG_UPDATE_COMBO_POINTS per call instead of two.
void Unit::MoveComboPoints(Unit* newTarget, bool send)
{
    if (!newTarget || newTarget == m_comboTarget || !m_comboPoints || !KeepsComboPointsOnSelf())
        return;

    if (m_comboTarget)
        m_comboTarget->RemoveComboPointHolder(this);

    m_comboTarget = newTarget;
    newTarget->AddComboPointHolder(this);

    if (send)
        SendComboPoints();
}

// Runs first in ClearComboPointHolders (this unit died, evaded or is leaving the map): parks every
// rogue's and druid's points on themselves, so the stock loop only clears everyone else's. A holder
// that still has this unit selected gets the points back one update later if this unit is still a
// valid attack target by then - the evade case, where the unit stays alive and selected.
void Unit::ReleaseComboPointHolders()
{
    // MoveComboPoints edits m_ComboPointHolders, so collect the holders first.
    std::vector<Unit*> keepers;
    for (Unit* holder : m_ComboPointHolders)
        if (holder != this && holder->KeepsComboPointsOnSelf())
            keepers.push_back(holder);

    bool const canReturn = IsAlive();
    for (Unit* holder : keepers)
    {
        holder->MoveComboPoints(holder);

        // The event lives on the holder's own m_Events, so it dies with the holder.
        if (canReturn && holder->GetTarget() == GetGUID())
            holder->m_Events.AddEventAtOffset([holder]() { holder->RetargetComboPoints(holder->GetTarget()); },
                                               Milliseconds(1));
    }
}

// Moves the points to a newly selected unit when it is a living, attackable enemy and there are
// points to move. Selecting a friend, or clearing the selection, leaves them where they are.
void Unit::RetargetComboPoints(ObjectGuid guid)
{
    if (!m_comboPoints || guid.IsEmpty() || !KeepsComboPointsOnSelf())
        return;

    if (m_comboTarget && m_comboTarget->GetGUID() == guid)
        return;

    Unit* target = ObjectAccessor::GetUnit(*this, guid);
    if (!target || !IsValidAttackTarget(target))
        return;

    MoveComboPoints(target);
}
