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

class Guardian;
class Aura;
class ProcEventInfo;
class SpellInfo;
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

    // ---- DK0b ----
    // Runes (self auras, group 1271). Glow state lives on player->CustomData (P0 m10), nothing file-static.
    uint32 GetActiveRune(Player const* player);           // the rune aura id the player carries, or 0
    uint16 GetRuneGlowEnchant(uint32 runeSpellId);        // DeathKnightData RUNE_GLOW_*, 0 = none
    void ApplyRuneGlow(Player* player);                   // writes the active rune's glow on both weapon slots
    void WriteRuneGlow(Player* player, uint8 slot);       // visible-slot hook: re-write one weapon slot's glow
    void RestoreRuneGlow(Player* player);                 // SetVisibleItemSlot on both weapon slots
    // Shared CheckProc guard: actor == owner; oncePerCast = only the hit on the cast's own unit target rolls (periodic
    // events skip this); dualWieldHalf = an extra 50% roll when the owner has an off-hand weapon.
    bool RuneProcAllowed(Unit const* runeOwner, ProcEventInfo& eventInfo, bool dualWieldHalf, bool oncePerCast);

    // Rune-regen haste (U4): hidden 203052 aura 110 x3 + 203053 sync. Spell haste only; never ResyncRunes.
    int32 GetRuneHastePct(Player const* player);
    void SyncRuneHaste(Player* player, Aura* runeHaste);

    // Minions: live stat mirror + no-proc rule. DRW 27893 is None (core-live).
    enum class MinionKind : uint8 { None, Ghoul, ArmyGhoul, Gargoyle, Bloodworm };
    MinionKind GetMinionKind(Unit const* unit);
    Player* GetMinionOwner(Unit const* minion);           // GetOwner() only, never GetOwningPlayer (bug 3040)
    void ApplyMinionMirror(Guardian* minion);
    void RefreshMinionMirror(Unit* minion, Player* owner);
    // 1.0f seam (U10)
    float GetMinionDamageMultiplier(Player const* owner, Unit const* minion, SpellInfo const* spellInfo);

    // Unending Thirst (U14): the DK's own killing blow; casts the buff triggered if the rune is up.
    void OnRuneKillingBlow(Player* dk, Unit* killed);
}

#endif
