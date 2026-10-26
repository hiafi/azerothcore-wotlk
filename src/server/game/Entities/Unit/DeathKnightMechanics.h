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
#include "ObjectGuid.h"
#include "SharedDefines.h"
#include <cstdint>

class Creature;
class Guardian;
class Pet;
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
    enum class MinionKind : uint8 { None, Ghoul, ArmyGhoul, Gargoyle, Bloodworm, LesserGhoul, Abomination };
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

    // ---- S2 ----
    // Once-per-cast guard (moved unchanged from spell_dk_blood.cpp, S2a U13): one per aura script instance. First() is
    // true for the first event of a cast and false for the rest of its hits (see the definition in
    // DeathKnightMechanics.cpp for the exact rules).
    struct OncePerCastGuard
    {
        bool First(ProcEventInfo& eventInfo);
        bool OwnerFirst(Unit const* owner, ProcEventInfo& eventInfo);

    private:
        Spell const* _spell = nullptr;
        uint32 _spellId = 0;
        int64 _timeMs = 0;
    };

    // Per-cast school switch (U5): the only way a Frost script changes a cast's school. Call from OnCast ONLY (before
    // TakePower and the launch phase). Implemented with a pointer-to-protected-member accessor, zero core lines.
    void SetCastSchool(Spell* spell, SpellSchoolMask mask);
    bool IsSchoolSwitchedCast(Spell const* spell);

    // Target-conditional percents (U14/U17). One multiplier applied with SetHitDamage in OnHit.
    enum FrostMultFlags : uint32
    {
        FROST_MULT_KM_OBLITERATE   = 0x01, // Killing Machine Obliterate (Obliteration capstone term)
        FROST_MULT_SCHOOL_SWITCHED = 0x02, // Razorice term for a school-switched cast (aura 271 cannot tell)
        FROST_MULT_OFFHAND         = 0x04, // non-physical off-hand: x0.5 x (1 + Nerves%), see GetOffhandFactor
        FROST_MULT_BREATH_PRIMARY  = 0x08, // Breath tick on the primary target (capstone, ramp)
        FROST_MULT_DEATHCHILL      = 0x10, // Deathchill +20% (direct hits only)
    };
    float GetFrostDamageMultiplier(Player const* dk, SpellInfo const* spellInfo, Unit const* target, uint32 flags);

    // Killing Machine (buff 203320, 2 stacks, no charges).
    bool HasKillingMachine(Unit const* dk);
    void ConsumeKillingMachine(Player* dk);   // one stack, then Enduring Strength extends Pillar if it was up
    void GrantKillingMachine(Player* dk);     // +1 stack, cap KILLING_MACHINE_MAX_STACKS, refresh

    // Rime: casts Freezing Fog 59052 and resets Howling Blast's cooldown (Rage of the Frozen Champion capstone).
    void GrantRime(Player* dk);

    // Pillar of Frost / Enduring Strength: extend the live Pillar aura by ms, capped per Pillar (3 s / 6 s by rank).
    void ExtendPillar(Player* dk, int32 ms);

    // Runes (U18): ActivateRune mirrors the stock ERW tail (SetRuneCooldown 0, SetGracePeriod, client push 47804).
    void ActivateRune(Player* dk, uint8 slot);
    void SnapshotRuneCooldowns(Player* dk);          // on dk->CustomData, called from Obliterate OnCast
    int8 FindJustSpentFrostRune(Player const* dk);   // Frost slot whose cooldown went 0 -> >0 since the snapshot, or -1

    // Deathchill (U9): script-driven, no charged SpellMod.
    bool DeathchillReady(Unit const* dk);            // buff 203311 up
    void ArmDeathchill(Player* dk, Spell* spell);    // adds marker 203312; never on a Killing Machine Obliterate
    void ConsumeDeathchill(Player* dk);              // removes marker + buff, casts the lockout with the rank duration

    // Hungering Cold (U10).
    void StartOrExtendHungeringCold(Player* dk);     // new storm, or SetDuration(HUNGERING_COLD_STORM_MS) on a live one
    void OnHungeringColdHit(Player* dk, Unit* target); // +1 slow stack; freeze + lockout at 2 stacks

    // Breath of Sindragosa (U11/U12; normal DBC cooldown, so no cooldown helper).
    uint32 GetBreathDrain(uint32 tickNumber);        // internal RP (x10): 10 + (tick - 1) / 5 RP
    void AddFinalRoarDamage(Player* dk, uint32 damage);
    uint32 TakeFinalRoarDamage(Player* dk);          // returns and clears the stored sum

    // ---- S2 helpers (B1) ----
    // Off-hand math (brief D1). p = GetOffhandFactor(dk) = (100 - OFFHAND_PENALTY_PCT)% x the product of every
    // SPELL_AURA_MOD_OFFHAND_DAMAGE_PCT the off-hand fits (Nerves of Cold Steel E1) = 0.5 x (1 + Nerves%), the engine's
    // off-hand TOTAL_PCT minus the physical %-done auras. FROST_MULT_OFFHAND multiplies the result by p.
    //  - Physical off-hand copy (66198 / 66188 / 66216 / 203322, not switched): the engine already pays
    //    p x W x pct + 2 x p x F_stored = p x (W x pct + F_mh) because the copy stores F_stored = F_mh / 2. Do NOT pass
    //    FROST_MULT_OFFHAND for it.
    //  - Non-physical off-hand (66196 always; a school-switched physical copy: KM Obliterate 66198, Gravefrost
    //    203322 / 66216): the engine pays D' = W x pct + F_stored (no x2, no TOTAL_PCT). The caller, in OnHit:
    //        addBack = GetOffhandFlatAddBack(caster, spellInfo, target)  // F_stored (physical-base copy), 0 on 66196
    //        SetHitDamage((GetHitDamage() + addBack) x GetFrostDamageMultiplier(..., flags | FROST_MULT_OFFHAND))
    //    so D = p x (D' + F_stored) = p x (W x pct + F_mh) x (the other terms), matching the physical path.
    //    addBack is the effect's computed fixed_bonus (CalculateSpellDamage, potency included; it rolls the potency
    //    variance again, so it may differ from the engine's own roll by that variance).
    float GetOffhandFactor(Player const* dk);
    int32 GetOffhandFlatAddBack(Unit const* caster, SpellInfo const* spellInfo, Unit const* target);
    // GetFrostDamageMultiplier: every term is multiplicative except Glacier Rot's capstone Mastery, which adds into the
    // Glacier Rot percent. Spell-keyed terms read spellInfo->Id (Obliterate 203054 / 66198, Frost Strike 49143 / 66196,
    // Howling Blast 49184, Glacial Eruption 203274, Breath tick 203307). The Breath terms (Mastery, Frostwyrm's Wrath
    // ramp) apply to every tick target; FROST_MULT_BREATH_PRIMARY adds nothing in the helper, and the caller applies
    // BREATH_SECONDARY_PCT to the secondary targets itself.
    // ---- S3 ----
    // Runes (U7, L26). SnapshotRunes stores, keyed by the cast, every slot's cooldown and CURRENT type on
    // dk->CustomData (call from OnCast: before TakePower). GetSpentPlainRuneSlots returns the slots whose cooldown
    // went 0 -> > 0 since that snapshot AND whose snapshot type was not RUNE_DEATH (a returned Death Rune spent again
    // gets nothing back).
    // ConvertToDeathRune: SetRuneConvertAura(slot, nullptr) + ConvertRune(slot, RUNE_DEATH) (+ ActivateRune when
    // ready).
    // S2's SnapshotRuneCooldowns / FindJustSpentFrostRune keep their signatures and now share the type snapshot.
    void SnapshotRunes(Player* dk, uint32 castSpellId);
    // outSlots holds MAX_RUNES (6, Player.h) entries; returns how many were written.
    uint8 GetSpentPlainRuneSlots(Player const* dk, uint32 castSpellId, uint8 outSlots[6]);
    void ConvertToDeathRune(Player* dk, uint8 slot, bool ready);

    // Festering Wounds (U8-U10). Every adder goes through AddFesteringWounds; the debuff's caster is always the DK.
    enum class WoundSource : uint8
    {
        PlagueStrikeOverflow,
        ScourgeStrike,
        RottenTouch,
        Abomination,
        Gargoyle,
        InfectedClaws,
        Pestilence
    };
    // RP + Wandering Plague: ScourgeStrike, RottenTouch, PlagueStrikeOverflow.
    bool WoundSourceGrantsResources(WoundSource src);
    uint8 GetFesteringWounds(Unit const* target, ObjectGuid dkGuid);
    // Wounds past the cap burst at once (overflow).
    void AddFesteringWounds(Player* dk, Unit* target, uint8 n, WoundSource src);
    void BurstFesteringWounds(Player* dk, Unit* target, uint8 n, WoundSource src);  // one burst cast with n
    void OnWoundBurstHit(Player* dk, Unit* target, uint32 damage, WoundSource src, uint8 n);
    void ScheduleWoundExplosion(Player* dk, Unit* corpse, uint8 stacks);

    // Mastery and multipliers.
    int32 GetDreadHostPct(Player const* dk);             // Rage of Rivendare rank 3/6/9 + Mastery with the capstone
    int32 GetAllWillServePct(Player const* dk);          // 5/10
    bool HasNecromancy(Unit const* dk);                  // All Will Serve rank 2 aura
    int32 GetCryptFeverPct(Unit const* dk);              // 10/20/30 by Crypt Fever rank
    int32 GetEbonPlagueMagicPct(Unit const* dk);         // 4/8/12 by Ebon Plaguebringer rank

    // Necromancy (U14).
    void GrantNecromanticEnergy(Player* dk);             // +NECROMANTIC_ENERGY_PER_STRIKE, cap, refresh
    bool ConsumeNecromanticEnergy(Player* dk);           // -1; false when none

    // Minions (U15/U16/U19).
    bool IsUnholyMinion(MinionKind kind);                // Ghoul, LesserGhoul, Abomination, Gargoyle, ArmyGhoul
    int32 GetMinionApSharePct(MinionKind kind);
    bool SubtractsMinionBaseAp(MinionKind kind);         // the ghoul kind only
    Creature* SummonLesserGhoul(Player* dk, Unit* target);
    void CapMinions(Player* dk, uint32 entry, uint32 cap);
    void RefreshLesserGhoulCounter(Player* dk);
    Creature* FindCorpseExplosionGhoul(Player* dk);
    float GetLesserGhoulRemainingFraction(Creature const* ghoul);

    // Gargoyle (U17/U18).
    Creature* GetActiveGargoyle(Player const* dk);
    void OnGargoyleStrikeHit(Player* dk, Unit* target);
    void OnGargoyleLeave(Player* dk);

    // Ghoul (U22/U23).
    void AddShadowInfusion(Player* dk);
    void ApplyInfectedClaws(Player* dk, Pet* ghoul);

    // Pestilence (U26): On a Pale Horse on the primary (OnPestilenceCopy covers the copies).
    void OnPestilencePrimary(Player* dk, Unit* primary);

    // ---- S3 additions (B1; the brief's pre-agreed ones first) ----
    // Shadow Infusion 203464 changed on the ghoul (stacks 0 = removed): sets the owner's marker 203465 at
    // SHADOW_INFUSION_STACKS (only when the owner knows Dark Transformation 203448), removes it below.
    void OnShadowInfusionChanged(Unit* ghoul, uint8 stacks);
    // Rotten Touch: the armed Coil's target (Death Coil AfterCast) and the 47632 hit's check (true once, then cleared).
    void RecordRottenTouchTarget(Player* dk, ObjectGuid target);
    bool ConsumeRottenTouchTarget(Player* dk, ObjectGuid target);
    // D9: start ms + total ms on the ghoul's CustomData (idempotent: the first call wins).
    void StartLesserGhoulTimer(Creature* ghoul, uint32 durationMs);

    // The mirror's eff0 amount (D12): per-kind share of the owner's AP minus shared party AP; the ghoul kind also
    // minus its own base AP (may be negative), every other kind clamped at 0. RefreshMinionMirror and
    // spell_dk_minion_mirror::CalcAttackPower both use it.
    int32 GetMinionMirrorAttackPower(Player const* owner, Unit const* minion);
    // U16's Unholy terms for a hit of spellInfo's school (null = physical): (1 + Dread Host%) x (1 + All Will Serve%)
    // x (1 + 3% x Gargoyle Necromancy stacks) x the owner's own Death Knight MOD_DAMAGE_PERCENT_DONE auras for that
    // school (never party/raid buffs). For a "counts as minion damage" hit the DK casts itself (Corpse Explosion's
    // corpse branch).
    float GetUnholyMinionTerms(Player const* owner, SpellInfo const* spellInfo);
    // On a Pale Horse known (passive 51983 or 51986).
    bool HasOnAPaleHorse(Unit const* dk);
    // AllCreatureScript add/remove-world bodies (Lesser Ghoul counter + timer, Gargoyle start / leave fallback,
    // creature CustomData cleared on removal) and the owner's map-change resync (counter, Necromancy stacks).
    void OnMinionAddWorld(Creature* creature);
    void OnMinionRemoveWorld(Creature* creature);
    void OnDeathKnightMapChanged(Player* dk);
    // The unit SummonLesserGhoul raised the ghoul at (its AI attacks it first), or Empty.
    ObjectGuid GetLesserGhoulSummonTarget(Creature const* ghoul);
}

#endif
