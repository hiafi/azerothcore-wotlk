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

#ifndef __SHAMANMECHANICS_H
#define __SHAMANMECHANICS_H

#include "Define.h"
#include "Generated/ShamanData.h"
#include "SharedDefines.h"
#include <cstdint>
#include <initializer_list>
#include <span>

class Creature;
class Player;
class Unit;

/*
 * Shaman-specific "doesn't fit a SpellScript/AuraScript" hooks (shaman-rework SH0). Append-only: SH0a holds
 * only the SH0a block; later stages add their declarations together with their bodies and never retype an
 * existing signature. Spell ids come from ShamanData:: (DSL-declared); this header is the only place that
 * includes Generated/ShamanData.h.
 */
namespace Shaman
{
    // ---- SH0a ----
    // The player that owns `unit`: itself, or the owner/charmer of a pet, guardian or totem. nullptr otherwise.
    Player* GetOwningPlayer(Unit* unit);
    Player const* GetOwningPlayer(Unit const* unit);

    // CORE-AUDIT-A A12: every owner-side proc's CheckProc guard. True when `actor` is the shaman itself (not a
    // totem, guardian or pet acting for it).
    bool IsOwnAction(Unit const* shaman, Unit const* actor);

    // Proc Chance for scripted rolls: chance * (1 + owner Proc Chance / 100). Pets/guardians resolve to their owner.
    float GetProcChanceMultiplier(Unit const* unit);
    bool  RollProcChance(Unit const* unit, float baseChancePct);

    // Spell id of the imbue aura (Rockbiter, Flametongue, Frostbrand, Windfury, Earthliving) currently on `unit`;
    // 0 if none.
    uint32 GetActiveImbue(Unit const* unit);

    // True while the player knows a Maelstrom Weapon talent rank (stock ranks until the Enhancement stage).
    bool HasMaelstromWeaponTalent(Player const* player);

    // Imbue weapon glow (P0 section 5): writes the temp half of PLAYER_VISIBLE_ITEM_n_ENCHANTMENT.
    uint16 GetImbueGlowEnchant(Player const* player);         // visible enchant id of the active imbue, 0 if none
    void   ApplyImbueGlow(Player* player);                    // both weapon slots, from the active imbue
    void   RestoreImbueGlow(Player* player);                  // re-runs SetVisibleItemSlot for both weapon slots
    void   WriteImbueGlow(Player* player, uint8 slot);        // single slot, called from the visible-slot hook

    // Stoneskin (only while Rockbiter is up; cap Shaman STONESKIN_MAX).
    void AddStoneskin(Player* shaman, uint32 stacks);
    // B15: a landed hit of `landedDamage` on `victim` (after armor and every reduction, Stoneskin's included)
    // removes the same percent of current stacks as the hit is of max health before Stoneskin's reduction.
    void ErodeStoneskin(Player* victim, uint32 landedDamage);
    // Out-of-combat 2 min timer: started on leave, cancelled on re-enter.
    void OnCombatChange(Player* player, bool inCombat);

    // Attunement amounts are per caster level: RecalculateAmountOfEffects on the attunement and its child (B11).
    void RefreshAttunements(Player* player);

    // Grants/keeps the passive 58059 (Reincarnation without the Ankh reagent): HunterNoAmmoGrant shape.
    void EnsureReincarnationAura(Player* player);

    // Logout cleanup; each later section adds its own Clear* call here.
    void ClearState(Player* player);

    // ---- SH0b ----
    // Elementals (Earth 2062, Fire 2894, Water, Storm): a totem in the element's slot whose passive summons the
    // guardian (CORE-AUDIT-A A5). The block keeps no per-player state, so ClearState needs no SH0b call.

    // The shared lockout before Cooldown Haste: ELEMENTAL_LOCKOUT_MS, or CONDUIT_LOCKOUT_MS while the player knows
    // Elemental's Conduit of the Elements (S1).
    uint32 GetElementalLockoutBaseMs(Player const* player);

    // A14: after a non-triggered cast of an elemental summon (the caller skips triggered casts), locks the other
    // three for base / (1 + max(0, Cooldown Haste) / 100). Deferred 1 ms (after SMSG_SPELL_GO and the cast spell's
    // own haste correction); never shortens a longer cooldown; clear-then-set resend so the buttons grey.
    void ApplyElementalLockout(Player* player, uint32 castSpellId);

    // True for the four elemental summon spells.
    bool IsElementalSummonSpell(uint32 spellId);

    // Guardian JustDied: unsummons the owner's totem in this elemental's slot when that totem is this elemental's
    // totem entry, so the slot empties (the cooldown keeps running). Any other occupant, or an NPC owner's stock
    // totem, is left alone.
    void OnElementalDied(Creature* guardian);

    // H1: adds the owner-stat aura (202279) to `guardian` if missing, then sets its MOD_DAMAGE_DONE amount to the
    // owner's spell power in the guardian's own bolt school (Frost for Water, Nature for Storm; no other school's
    // bonus is added) and its MOD_HEALING_DONE amount to the owner's healing power (live, nothing else). Called
    // at IsSummonedBy and from the aura script's periodic refresh; never from the aura's own amount calculation.
    void RefreshElementalAuras(Player* owner, Unit* guardian);

    // ---- S1 ----
    // Elemental spec (docs/reworks/shaman-elemental-rework.md). No per-player state: every function reads the
    // shaman's own talents, auras and totem slots, so a non-shaman with the talents gets do-nothing (Q21).

    // GetActiveElementals bits, one per elemental whose player-side totem (300270-300273) holds its slot.
    enum ElementalMask : uint8
    {
        ELEMENTAL_MASK_EARTH = 0x1,
        ELEMENTAL_MASK_FIRE  = 0x2,
        ELEMENTAL_MASK_WATER = 0x4,
        ELEMENTAL_MASK_STORM = 0x8
    };

    // 1-based rank of the highest rank id the player has (talent in the active spec, or its passive aura); 0 if
    // none. Pass the talent's rank ids in rank order. Never reads HasSpell.
    uint8 GetTalentRank(Player const* player, std::span<uint32 const> rankIds);
    uint8 GetTalentRank(Player const* player, std::initializer_list<uint32> rankIds);

    // ElementalMask bits of the elementals currently active for `player` (0 for nullptr).
    uint8 GetActiveElementals(Player const* player);

    // Called from the AllCreatureScript add/remove hook of the four elemental totems. Both reconcile the whole
    // Elemental state against the totem slots, so the order of a replacement (new totem added before the old one
    // leaves the world) never matters: Empowerment buffs on/off (Power of the Elements), Gathering Flames cleared
    // when no Fire Elemental is active, the Elemental Warding capstone health aura, the Empowerment amount, and
    // (one tick later, after the totem's passive summoned it) the guardian auras added by the owner (L5). `totem`
    // may be nullptr and `totemEntry` 0: a plain reconcile (login, map change, talent change).
    // A non-null Earth Elemental `totem` is a real summon: with the Booming Echoes capstone it grants
    // ECHO_EARTH_ELEMENTAL_GRANT Echo.
    void OnElementalAdded(Player* player, Creature* totem);
    void OnElementalRemoved(Player* player, uint32 totemEntry);

    // Sets the live Empowerment amount (EMPOWERMENT_PCT, plus the live Mastery with Conduit of the Elements) on
    // the player's Empowerment buffs and on the guardian-side Empowerment; changes an effect only when it moved.
    void RefreshEmpowerment(Player* player);

    // True for the three Lightning Overload copies (Lightning Bolt, Chain Lightning, Lava Burst).
    bool IsOverloadCopy(uint32 spellId);

    // Booming Echoes: adds `stacks` Echo (cap ECHO_MAX) and refreshes it to ECHO_DURATION_MS.
    void AddEcho(Player* player, uint8 stacks);

    // Call of the Elements: every active elemental totem (and its guardian) gains `ms`; the totem bar is retimed.
    // Call it before summoning the inactive elementals, so the new ones are not extended.
    void ExtendElementals(Player* player, uint32 ms);

    // Thunderstorm rank 2 (usable while stunned) is known exactly while Thunderstorm and Call of Thunder rank 3
    // are known; learns or removes it to match.
    void SyncThunderstormRank(Player* player);

    // Lava Flows talent rank (1-3) -> its haste buff id; 0 for any other rank.
    uint32 LavaFlowsHasteSpell(uint8 rank);
}

#endif
