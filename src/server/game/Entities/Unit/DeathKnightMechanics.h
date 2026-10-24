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

#ifndef __DEATHKNIGHTMECHANICS_H
#define __DEATHKNIGHTMECHANICS_H

#include "Define.h"
#include "Generated/DeathKnightData.h"
#include <cstdint>

class Player;
class Unit;

/*
 * Death Knight-specific "doesn't fit a SpellScript/AuraScript" hooks (death-knight-rework DK0). Append-only:
 * DK0a holds only the block below; later stages add their declarations together with their bodies and never retype
 * an existing signature. Spell ids and tuning numbers come from DeathKnightData:: (DSL-declared); this header is the
 * only place that includes Generated/DeathKnightData.h.
 */
namespace DeathKnight
{
    // ---- DK0a ----
    // True when the player's damage-taken record is read by a spell they know (Death Strike 49998). Class-neutral on
    // purpose (Classless-ready): the record is kept for anyone who knows the spell.
    bool TracksDamageTaken(Player const* player);

    // Appends (now, amount) to the player's record and prunes entries older than DEATH_STRIKE_WINDOW_MS. State lives on
    // player->CustomData. S1's Blood Shield AfterEffectAbsorb and Purgatory call it.
    void RecordDamageTaken(Player* player, uint32 amount);

    // Sum of the recorded damage inside the window (prunes first).
    uint32 GetRecordedDamage(Player* player);

    // max(healPct% of the record, DEATH_STRIKE_MIN_HEAL_PCT% of max health). Never reads diseases or attack power.
    uint32 ComputeDeathStrikeHeal(Player* player, int32 healPct);

    // Called once per enemy a Pestilence copy reached. Empty in DK0a; S3 adds wound copies and On a Pale Horse.
    void OnPestilenceCopy(Player* dk, Unit* source, Unit* target);

    // Anti-Magic Zone shared pool (U12): kept on zone->CustomData, initialised on first use from the owner, returns the
    // amount absorbed (at most the wanted amount), unsummons the zone when the pool reaches 0.
    uint32 ConsumeZoneAbsorb(Unit* zone, Player* owner, uint32 wanted);
}

#endif
