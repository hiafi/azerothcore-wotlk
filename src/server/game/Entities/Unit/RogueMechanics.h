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

#ifndef __ROGUEMECHANICS_H
#define __ROGUEMECHANICS_H

#include "Define.h"
#include "Generated/RogueData.h"
#include "SharedDefines.h"
#include <cstdint>

class AuraEffect;
class Player;
class ProcEventInfo;
class Unit;

/*
 * Rogue-specific "doesn't fit a SpellScript/AuraScript" hooks (rogue-rework RG0a). Append-only: later stages add their
 * declarations together with their bodies and never retype an existing signature. Spell ids and tuning numbers come
 * from RogueData:: (DSL-declared); this header is the only place that includes Generated/RogueData.h. Per-player state
 * lives on Unit::CustomData, nothing is file-static.
 */
namespace Rogue
{
    // ---- RG0a: energy haste ----
    // Class rogue or druid. The one Classless change point for "who regenerates energy faster with haste".
    bool IsEnergyUser(Player const* player);

    // clamp(lround(100 / castSpeed - 100), 0, ENERGY_HASTE_MAX_PCT) from UNIT_MOD_CAST_SPEED; 0 for a
    // non-positive speed.
    int32 GetEnergyHastePct(Unit const* unit);

    // Energy user: teach SPELL_ENERGY_HASTE silently, or recast it if known but missing. Not an energy user but knows
    // it: remove it.
    void EnsureEnergyHaste(Player* player);

    // regen->ChangeAmount(pct, false) only when the percentage moved.
    void SyncEnergyHaste(Unit* owner, AuraEffect* regen);

    // ---- RG0a: poisons as self auras ----
    enum class PoisonSlot : uint8
    {
        None,
        Lethal,
        NonLethal
    };

    PoisonSlot GetPoisonSlot(uint32 auraSpellId);

    // POISON_LETHAL_SLOTS (1). S1's Master Poisoner capstone returns 2.
    uint8 GetLethalSlots(Player const* rogue);

    // While the rogue holds more Lethal auras than slots, removes the one with the oldest GetApplyTime() (ties: lowest
    // id) other than keptAuraId.
    void EnforceLethalSlots(Player* rogue, uint32 keptAuraId);

    // The guard: actor is the rogue, a valid hostile non-self target, not a CC/suppress-procs spell, once per cast per
    // aura, no extra attacks.
    bool PoisonRollAllowed(Unit const* rogue, ProcEventInfo& eventInfo, uint32 auraId);

    // base chance + chance-of-success mods (aura id), x weapon speed / 2600 for a melee auto attack, x Proc Chance,
    // cap 100.
    bool RollPoison(Player* rogue, uint32 auraId, ProcEventInfo& eventInfo);

    enum class PoisonSource : uint8
    {
        Roll,
        Shiv,
        Talent
    };

    // Casts payloadId at target, TRIGGERED_FULL_MASK, with triggeredBy as the triggering aura. Every poison application
    // in every later stage goes through it.
    void ApplyPoison(Player* rogue, Unit* target, uint32 payloadId, AuraEffect const* triggeredBy, PoisonSource source);

    bool HasAnyPoison(Player const* rogue);

    // Weapon glow (POISON_GLOW_ENCHANT in the temp half of the visible enchant field of main / off hand).
    void ApplyPoisonGlow(Player* player);
    void WritePoisonGlow(Player* player, uint8 slot);
    void RestorePoisonGlow(Player* player);

    // ---- RG0b ----
    // For every Lethal poison aura the rogue holds (LETHAL_POISON_AURAS), ApplyPoison(rogue, target, the aura's
    // EFFECT_0 TriggerSpell, its EFFECT_0 AuraEffect, source). No roll, no Proc Chance.
    void ApplyLethalPoisons(Player* rogue, Unit* target, PoisonSource source);
}

#endif
