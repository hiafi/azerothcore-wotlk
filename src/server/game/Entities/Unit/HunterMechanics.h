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

#ifndef __HUNTERMECHANICS_H
#define __HUNTERMECHANICS_H

#include "Define.h"
#include "SharedDefines.h"
#include <cstdint>

class Pet;
class Player;
class ProcEventInfo;
class Spell;
class SpellInfo;
class Unit;

/*
 * Hunter-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors WarlockMechanics.h's shape
 * (.agents/plans/hunter-rework/hunter-rework.SHARED.md §A5, §C4). Append-only: each later stage adds its
 * declarations together with their bodies and never retypes an existing signature. Stage T2 holds only the
 * T2 block; H0 WP-0 adds #include "Generated/HunterData.h" and aliases the DSL-declared ids to HunterData::.
 */
namespace Hunter
{
    // ---- T2 ----
    constexpr uint32 SPELL_REQUIRES_NO_AMMO = 46699;      // stock Thori'dal aura, granted to every player

    // Q5: two hunter stings (SPELL_SPECIFIC_STING) never exclude each other. Called from the one core line in
    // SpellInfo::IsAuraExclusiveBySpecificPerCasterWith. True when both a and b are hunter stings.
    bool StingsStack(SpellInfo const* a, SpellInfo const* b);

    // The player that owns `unit`: itself, or the owner/charmer of a pet, guardian or totem. nullptr otherwise.
    Player* GetOwningPlayer(Unit* unit);
    Player const* GetOwningPlayer(Unit const* unit);

    // Proc Chance for scripted rolls (PLAN §2): chance * (1 + owner Proc Chance / 100). A pet or guardian resolves
    // to its owner (warlock GetOwnerProcChanceMultiplier precedent). Non-player chains use multiplier 1.
    float GetProcChanceMultiplier(Unit const* unit);
    bool  RollProcChance(Unit const* unit, float baseChancePct);

    // Real-seconds, client-visible cooldown cut (Player::ModifySpellCooldown, druid A8); never scaled by
    // Cooldown Haste. No-op when the spell has no running cooldown.
    void  ReduceSpellCooldown(Player* player, uint32 spellId, uint32 ms);

    // Q32: worldserver.conf `Custom.Realm.Classless` (default 0), read once (function-local static).
    bool  IsClasslessRealm();

    // Grants 46699 silently (addSpell on an unknown spell, CastSpell when known but the aura is gone).
    void  EnsureNoAmmoAura(Player* player);

    // Logout cleanup; each later section adds its own Clear*State call here. Removal paths use find-only map
    // access (paladin CR5).
    void  ClearState(Player* player);

    // ---- H0 ----
    // ---- H0-P (PET.md §8.4 defines the bodies and the rest of the pet section) ----
    // ---- S1 / S2 / S3 append their own sections (transform re-cast, mark state, Burning Tar bank) ----
}

#endif
