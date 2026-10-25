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
class Spell;
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
    // Shared CheckProc guard: actor == owner; auraId = the calling aura (keys the once-per-cast guard, so one aura's
    // answer never starves another's); oncePerCast = only the hit on the cast's own unit target rolls (periodic
    // events skip this); dualWieldHalf = an extra 50% roll when the owner has an off-hand weapon.
    bool RuneProcAllowed(Unit const* runeOwner, ProcEventInfo& eventInfo, uint32 auraId, bool dualWieldHalf,
        bool oncePerCast);

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

    // ---- S1 ----
    // Bone Shield (49222): charges are the stack count the client shows. A re-cast resets to ProcCharges (3), so
    // Marrowrend raises them with SetCharges after the cast. AddBoneShieldCharges returns true when it was already at
    // BONE_SHIELD_MAX_CHARGES (Marrowrend's capped bonus); it applies 49222 when missing.
    uint8 GetBoneShieldCharges(Unit const* unit);
    bool AddBoneShieldCharges(Unit* dk, uint8 add);

    // Blood Shield (203151, Improved Death Strike capstone): Death Strike's overheal adds to the existing shield up to
    // BLOOD_SHIELD_CAP_PCT of current max health and refreshes the duration. OnDeathStrikeHealFinal is called from
    // UnitScript::OnHealFinal for spell 45470 (healer == target) and gates itself on 62908.
    void GrantBloodShield(Player* dk, uint32 amount);
    void OnDeathStrikeHealFinal(Player* dk, uint32 heal, uint32 effective, uint32 healAbsorbed);

    // Purgatory (203145): called from UnitScript::DealDamage after the damage record. Returns true and lowers damage to
    // health - 1 when the hit would kill; OnShroudExpired kills the target when the Shroud ran out unhealed.
    bool TryPurgatory(Player* dk, Unit* attacker, uint32& damage);
    void OnShroudExpired(Unit* target, int32 unhealed);

    // Voracious capstone (203139): own Death Knight heals (family 15 + d2 b15, plus Mark of Blood 61607 and Death Pact
    // 48743) are raised by Mastery. ModifyHealReceived arrives swapped on the direct path; this resolves it.
    bool IsOwnDeathKnightHeal(SpellInfo const* spellInfo);
    void ApplyVoraciousCapstone(Unit* first, Unit* second, uint32& heal, SpellInfo const* spellInfo, bool periodic);

    // Voracious leech and Crimson Communion leech, from UnitScript::OnDamage.
    void OnDamageDealt(Unit* attacker, Unit* victim, uint32 damage);

    // Red Thirst (Thick Blood capstone), from PLAYERHOOK_ON_SPELL_CAST.
    void OnRunicPowerSpent(Player* dk, Spell const* spell);

    // Blood Gorged: rank percent plus half of Mastery with the capstone. BloodGorgedActiveAtCast reads the state the
    // D&D / Bonestorm helper aura snapshotted when the effect was cast (U13).
    int32 GetBloodGorgedPct(Player const* dk);
    void RefreshBloodGorged(Player* dk);
    bool BloodGorgedActiveAtCast(Unit const* dk);

    // Bloodworms: cap BLOODWORM_CAP, the oldest replaced.
    void CapBloodworms(Player* dk);

    // Dancing Rune Weapon (entry 27893) copy rules.
    bool IsRuneWeapon(Unit const* unit);
    bool IsRuneWeaponExcluded(uint32 spellId);

    // ---- S1 helpers (B1) ----
    // U13 snapshot: SnapshotBloodGorged stores, for the cast spell (43265 Death and Decay, 203148 Bonestorm), Blood
    // Gorged's damage multiplier at the cast (BloodGorgedActiveAtCast ? 1 + GetBloodGorgedPct% : 1) on dk->CustomData;
    // GetBloodGorgedTickMultiplier returns snapshot / live (the multiplier the engine applies to this tick now), so a
    // tick's damage times it carries the cast-time state. 1.0 when no snapshot was taken.
    void SnapshotBloodGorged(Player* dk, uint32 castSpellId);
    float GetBloodGorgedTickMultiplier(Unit const* dk, uint32 castSpellId);

    // U16: the minion mirror's attack power share per kind (Bloodworm: MINION_BLOODWORM_AP_SHARE_PCT, else
    // MINION_AP_SHARE_PCT). Read by RefreshMinionMirror and spell_dk_minion_mirror::CalcAttackPower.
    int32 GetMinionApSharePct(MinionKind kind);
}

#endif
