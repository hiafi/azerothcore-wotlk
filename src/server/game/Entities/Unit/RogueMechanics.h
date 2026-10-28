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
#include <initializer_list>

class Aura;
class AuraEffect;
class Player;
class ProcEventInfo;
class Spell;
class SpellInfo;
class Unit;
enum AuraRemoveMode : uint8;

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

    // ---- S1 ----
    // Assassination (docs/reworks/rogue-assassination-rework.md) and the shared helpers S2 / S3 append to, never fork:
    // one dispatcher, one combo-point helper, one Proc Chance roll, one stored-bleed helper, one health-clause hook.

    // roll_chance_f(min(pct x (1 + GetProcChancePercentage() / 100), 100)); the Shaman::RollProcChance copy. Every
    // talent proc a script rolls goes through it.
    bool RollProcChance(Player const* rogue, float pct);

    // Combo points from a script: onto target if it is a valid hostile, else the rogue's hostile selection, else the
    // rogue itself (parked). Never AddComboPoints on an area-hit unit (RG0b-DIAGNOSIS).
    void GainComboPoints(Player* rogue, Unit* target, int8 count);

    // The highest held rank's effect amount (HasAura on the rank spell ids, passed rank 1 first; the last one held
    // wins), 0 if none. A talent id is never a spell id.
    int32 GetRankAmount(Player const* rogue, std::initializer_list<uint32> rankIds, SpellEffIndex eff);

    // The cast-start dispatcher (RoguePlayerScript::OnPlayerSpellCast; runs in Spell::_cast before effects, combo
    // points not yet spent). Skips triggered casts. Finisher branch: Ruthlessness, Fleet Footed, Shattering Vial, Cut
    // Throat. Also stamps the cast of Fan of Knives, Mutilate and Kingsbane for the once-per-cast resolvers.
    void OnSpellCast(Player* rogue, Spell const* spell);

    // Membership tests every clause uses. Bleeds: Rupture, Garrote, the Doomblade bleed and tick (S2 adds Hemorrhage).
    // Poison damage: family 8, d1 b19 (POISON_GROUP), with a damage effect.
    bool IsRogueBleed(SpellInfo const* spellInfo);
    bool IsRoguePoisonDamage(SpellInfo const* spellInfo);

    // This rogue's poison effects on target, one per spell id (Dispel == DISPEL_POISON auras cast by the rogue;
    // Kingsbane's DoT counts, Instant Poison leaves none, Shattering Vial is Dispel none).
    uint8 CountOwnPoisons(Player const* rogue, Unit const* target);
    // This rogue's bleeds on target, one per spell id (IsRogueBleed auras cast by the rogue).
    uint8 CountOwnBleeds(Player const* rogue, Unit const* target);

    // From RogueUnitScript::OnSpellDamageTakenFinal. Dual-strike hands accumulate (damage, crit) for their parent's
    // stamped cast; a Fan of Knives crit (51723 / 52874, hits land after its AfterCast) rolls Seal Fate and Focused
    // Attacks at once, once per dispatcher-stamped cast.
    void RecordStrikeHit(Player* rogue, Unit* target, SpellInfo const* spellInfo, uint32 damage, bool crit);
    // From the parent's AfterCast. Mutilate (1329): Seal Fate, Focused Attacks, Doomblade, Blindside, Quick Recovery,
    // each once. Kingsbane (203822): Seal Fate, Focused Attacks. Clears the cast's record.
    void ResolveDualStrike(Player* rogue, Unit* target, uint32 parentSpellId);
    // The held Seal Fate rank's ProcChance x Proc Chance -> +1 combo point through GainComboPoints.
    void RollSealFate(Player* rogue, Unit* target);
    // The held Focused Attacks rank's ProcChance x Proc Chance -> cast 51637 (energize) on the rogue.
    void RollFocusedAttacks(Player* rogue);

    // Blindside's empowered Sinister Strike (per-cast stamp): marked in the SS script's BeforeCast while 203831 is up,
    // read by guard rule 3a''' and the SS AfterHit, cleared in its AfterCast.
    void MarkBlindsideEmpowered(Player* rogue, Spell const* spell);
    bool IsBlindsideEmpowered(Unit const* rogue, Spell const* spell);
    void ClearBlindsideEmpowered(Player* rogue);

    // Stored bleed (Doomblade now; S2 Hemorrhage and Akaari's Echo): roll-over perTick = (perTick x ticksLeft + share)
    // / ticks, restart the full duration. The aura script reads the state back for each tick.
    void ApplyStoredBleed(Player* rogue, Unit* target, uint32 bleedAuraId, uint32 totalDamage);
    // The current per-tick amount of this rogue's stored bleed on target (0 if none).
    uint32 GetStoredBleedTick(Unit const* rogue, Unit const* target, uint32 bleedAuraId);

    // Live health clause (Zoldyck Recipe now; S2 Executioner): the multiplier for one hit or tick, 1.0f when nothing
    // applies. Called from ModifySpellDamageTaken and ModifyPeriodicDamageAurasTick.
    float GetHealthClauseMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo);

    // Kingsbane's counter on its own target (called from ApplyPoison for a Lethal payload): charges min(n, 50) and
    // ChangeAmount(base x (1 + 0.05 n)).
    void AddKingsbaneStacks(Player* rogue, Unit* target, uint8 count);

    // Dashing Scoundrel: a rogue poison crit while Envenom's buff is up -> 1 energy, once per second per rogue.
    void OnRogueDamageCrit(Player* rogue, SpellInfo const* spellInfo, bool periodic);

    // Hunger for Blood apply / remove: re-run CalculatePeriodic on every PERIODIC_DAMAGE and PERIODIC_DUMMY effect the
    // rogue owns whose spell matches 51662's mask, on every unit in the rogue's combat and threat references.
    void SetHungerForBlood(Player* rogue);

    // Overkill: after any Stealth 1784 / Vanish 11327 apply or remove (idempotent; the hook runs twice per sweep).
    void UpdateOverkill(Player* rogue);
    // Remorseless Attacks: a rogue bleed left victim with AURA_REMOVE_BY_DEATH.
    void OnBleedVictimDied(Unit* victim, Aura const* bleed);

    // ---- S2 ----
    // Subtlety (docs/reworks/rogue-subtlety-rework.md; S2a WP-BRIEF). Cross-spec rules (S2-HANDOFF section 7): S2
    // adds one cooldown-reduction helper and one Hidden-state updater; S3 appends (Restless Blades reuses
    // ReduceCooldown). Hidden = Stealth 1784 | Vanish's aura 11327 | Shadowed 51713 everywhere. State on CustomData,
    // nothing file-static.

    // Takes ms off spellId's running cooldown (the Druid::ReduceSpellCooldown shape: ModifySpellCooldown, which clears
    // and resends the record; bug doc 1172). No-op when the spell is not on cooldown.
    void ReduceCooldown(Player* rogue, uint32 spellId, uint32 ms);

    // Stealth 1784, Vanish's aura 11327 or Shadowed 51713.
    bool IsHidden(Unit const* unit);

    // Master of Subtlety's amount: the held rank's EFFECT_0 (4 / 8 / 12), + lround(Mastery) with rank 3 (204151); 0
    // without a rank. Read by UpdateHiddenBuffs and the buff's own AuraScript (one formula).
    int32 GetMasterOfSubtletyPct(Player const* rogue);

    // After any 1784 / 11327 / 51713 apply or remove (idempotent; the hooks run twice per sweep). Master of Subtlety
    // 204154: infinite while Hidden, an 8 s tail after the last true-Stealth exit only (a Shadowed end removes it
    // unless a tail runs), infinite again on a new Hidden state. Mark of the Master Assassin 204164: infinite while
    // Stealth / Vanish, a 3 s tail on exit. Nothing for a rogue without the rank.
    void UpdateHiddenBuffs(Player* rogue);

    // Shadowed 51713 apply (also fires on a refresh) / remove. Lingering Shadow: the apply removes the old 204156; a
    // removal that is not a death (nor a logout) casts 204156 with SetStackAmount(rank).
    void OnShadowedApplied(Player* rogue);
    void OnShadowedRemoved(Player* rogue, AuraRemoveMode mode);

    // Backstab hit (player, non-triggered): Slaughter's roll (ReduceCooldown(51713, 500)); Lingering Shadow's point
    // (GainComboPoints(target, 1), one stack dropped).
    void OnBackstabHit(Player* rogue, Unit* target);

    // Ambush hit (player, non-triggered; damage = GetHitDamage()): Akaari's Echo's roll, then ScheduleAkaariEcho.
    void OnAmbushHit(Player* rogue, Unit* target, uint32 damage);
    // +2 s (rogue->m_Events, guids re-resolved): target alive -> the clone behind it and
    // CastCustomSpell(target, 204162, 50% x damage, true) (its own range check is "lost out of range").
    void ScheduleAkaariEcho(Player* rogue, Unit* target, uint32 damage);

    // An Eviscerate hit (2098) or Death from Above's landing (204170); damage = GetHitDamage(). Hemorrhage (204152
    // held: ApplyStoredBleed(204160, 30% x damage)) and ResolveFinality(rogue, 2098).
    void OnEviscerateHit(Player* rogue, Unit* target, uint32 damage, uint32 spellId);

    // Finality (U43): reads the dispatcher's stamp for that finisher (was its buff held at cast?) and consumes it
    // (held) or grants it with bp = the rank (not held). Keys: 2098 (Eviscerate and Death from Above), 1943, 26679.
    void ResolveFinality(Player* rogue, uint32 finisherSpellId);

    // Honor Among Thieves (51701 held): the stamped finisher cast's first crit (2098; 26679's primary; 204169 / 204170
    // belong to Death from Above's cast) -> 204172 on the rogue and the chosen ally (U48; the ally guid kept for
    // refreshes).
    void OnFinisherCrit(Player* rogue, Unit* target, SpellInfo const* spellInfo);

    // Death from Above (U32): flight aura 204171, two chained MoveJump legs (rise, dive at the target's position at the
    // moment of the dive), the anticheat calls EffectJumpDest makes, and the landing at the dive's end (guids
    // re-resolved; rogue alive on the same map / instance; target alive within DFA_LANDING_RANGE_YD ->
    // CastCustomSpell(target, 204170, landingBase, true); unreachable point -> 203726).
    void LaunchDeathFromAbove(Player* rogue, Unit* target, int32 landingBase);

    // ---- S3 ----
    // Combat (docs/reworks/rogue-combat-rework.md; S3a WP-BRIEF). Cross-spec rules (S3-HANDOFF section 7): S3 adds one
    // Anticipation bank / release (inside the combo-point helper's path) and one Blade Flurry copier. State on
    // CustomData, nothing file-static; event lambdas re-resolve units by guid.

    // U54 (a)-(c): bank combo points past 5 as Anticipation 203997 stacks (max ANTICIPATION_MAX_STACKS, each gain
    // refreshes its duration; past 7 points they are lost). No-op without Restless Blades 203965. Called from
    // GainComboPoints (before it adds), the builder stamp's +1 ms event and the Fan of Knives award.
    void BankAnticipation(Player* rogue, int8 overflow);
    // After a spent finisher (the third spent-clause event, after Ruthlessness's point): take the stacks, remove
    // 203997, GainComboPoints(rogue, target, stacks).
    void ReleaseAnticipation(Player* rogue, Unit* target);

    // The dispatcher's builder branch (non-triggered cast with an ADD_COMBO_POINTS effect): Adrenaline Rush's +1 point
    // (13750 or 203996 up; 1752, 203958, 14278, 14251, 53, 8676, 51723), Celerity (U74), the U54 (b) stamp.
    void OnBuilderCast(Player* rogue, Spell const* spell);

    // From RogueUnitScript::OnSpellDamageTakenFinal: Blade Twisting's stack (the cast's own id only: 1752, 203958,
    // 14278, 14251, 53) and the U54 (b) "landed" flag.
    void OnCombatStrikeHit(Player* rogue, Unit* target, SpellInfo const* spellInfo, uint32 damage);

    // The spent-clause event (one update after the finisher, only if its points were spent; Deadly Throw at cast):
    // Restless Blades (cp x rank ms off 13750, 13877, 203980, 203963, 51690 unless it is the finisher, 2983, and 5277 /
    // 31224 in Enforcer Stance 203720) and Hair Trigger (Between the Eyes: RollProcChance(rank x cp) -> 203987). Marks
    // the cast spent for the Anticipation release (S3a WP-BRIEF R4).
    void ApplyCombatSpentClauses(Player* rogue, Unit* target, uint32 finisherSpellId, uint8 comboPoints);

    // +1 Opportunity 203983 stack (max 3, each gain refreshes 20 s); the companion 203984 follows by its type-2 link.
    void GrantOpportunity(Player* rogue);

    // Pistol Shot hit (player, non-triggered; empowered = Opportunity was up at BeforeCast): empowered -> Primed
    // Powder +1 (refresh), Quick Draw (203964) +1 point; Surprise Attacks' buff 203989 up -> remove it, stamp
    // `empowered`, schedule SURPRISE_ATTACKS_EXTRA_SHOTS casts of 203988 at SURPRISE_SHOT_DELAY_MS steps
    // (rogue->m_Events, guids re-resolved, target alive, same map). The Opportunity stack itself is spent by the
    // Pistol Shot script's AfterCast, hit or not (the cast was free either way; S3a WP-BRIEF R12).
    void OnPistolShotHit(Player* rogue, Unit* target, bool empowered);
    // The stamp the extra shot's script reads (x (100 + OPPORTUNITY_EMPOWER_PCT) / 100 when true).
    bool IsSurpriseShotEmpowered(Player const* rogue);

    // Sinister Strike hit (player, non-triggered): marker 203957 held -> RollProcChance(rank) -> second strike 203986,
    // GainComboPoints(target, 1), GrantOpportunity, Surprise Attacks r3 (203982) RollProcChance(40) -> 203989.
    void OnSinisterStrikeHit(Player* rogue, Unit* target);
    // Eviscerate hit (player, non-triggered): marker held -> GrantOpportunity; ConsumeBladeRush.
    void OnEviscerateCombatHit(Player* rogue);
    // Riposte hit (player, non-triggered): GrantOpportunity; Improved Riposte r3 (203968) -> 203993 on up to
    // IMPROVED_RIPOSTE_EXTRA_TARGETS units within IMPROVED_RIPOSTE_RADIUS_YD of the target, in combat with the rogue.
    void OnRiposteHit(Player* rogue, Unit* target);

    // Blade Flurry cast (player): Deft Maneuvers (U72): >= DEFT_MANEUVERS_MIN_ENEMIES engaged units within
    // DEFT_MANEUVERS_RADIUS_YD -> strike 203992 (bp = rank) and one GainComboPoints(rogue, nullptr, min(n, 5)).
    void OnBladeFlurryCast(Player* rogue);
    // U59 copier: the rogue holds 13877's aura; spellInfo null = an auto attack. Up to BLADE_FLURRY_EXTRA_TARGETS
    // engaged units within BLADE_FLURRY_RADIUS_YD of target -> CastCustomSpell(unit, 203991, pct of damage, true).
    void OnBladeFlurryDamage(Player* rogue, Unit* target, uint32 damage, SpellInfo const* spellInfo);

    // Celerity (U74): 13750 up -> its remaining time to at least CELERITY_DURATION_MS; else apply / refresh 203996 to
    // at least that.
    void ApplyCelerity(Player* rogue);
    // Removes Blade Rush's empowerment 203990 (the damaging finisher's hit, Killing Spree's end).
    void ConsumeBladeRush(Player* rogue);

    // Prey on the Weak (U60). The dispatcher, on every non-triggered cast with an explicit hostile target: keep this
    // rogue's aura-308 debuff 204003 on target (bp = rank) while it is above PREY_CRIT_HEALTH_PCT, remove it otherwise.
    void UpdatePreyCritDebuff(Player* rogue, Unit* target);
    // Auto attacks (ModifyMeleeDamage): 1 + rank / 100 below PREY_DAMAGE_HEALTH_PCT, else 1.0f.
    float GetAutoAttackHealthMultiplier(Unit const* attacker, Unit const* target);
    // Auto attacks (OnBeforeRollMeleeOutcomeAgainst; critChance in 1/100 %): the > 90% clause, net of the 204003
    // debuff GetUnitCriticalChance already counts.
    void ModifyPreyAutoCrit(Unit const* attacker, Unit const* victim, int32& critChance);

    // Hack and Slash (U63): the proc row's CheckProc (6% x Proc Chance, x weapon speed / 2600 on autos, once per cast
    // on abilities, never triggered or a finisher, a one-hander in the hitting hand) and its strikes (203994 main
    // hand, 203995 off hand with an off-hand weapon, bp = rank %).
    bool RollHackAndSlash(Player* rogue, ProcEventInfo& eventInfo);
    void CastHackAndSlash(Player* rogue, Unit* target);

    // Improved Kick capstone (U73): Kick interrupted a cast with 13867 held -> buff 203999 on the rogue.
    void OnKickInterrupt(Player* rogue);

    // ---- S3a fix pass (S3a-REVIEW L1, L8; data sub-review finding 2) ----
    // Fan of Knives' and Second Volley's one-point award (spell_rog_fan_of_knives, at the first target's hit): a
    // U54 (b) builder stamp that has already landed (points = the held count, gain = the award), resolved by its +1 ms
    // event, so a Seal Fate point from the cast's own crit moves its base before the native gain is clamped.
    void StampFanOfKnivesGain(Player* rogue, int32 gain);
    // Rolls every poison the rogue holds once against target as the cast's own proc would (PoisonRollAllowed's guard,
    // RollPoison's chance with Proc Chance, ApplyPoison). For casts whose own procs are suppressed (Killing Spree).
    void RollCastPoisons(Player* rogue, Unit* target, Spell const* spell);
    // Prey on the Weak's held rank id (0 = none), cached on the player from the rank auras' apply / remove so the
    // per-swing hooks gate on one lookup.
    void UpdatePreyRankCache(Player* rogue);
}

#endif
