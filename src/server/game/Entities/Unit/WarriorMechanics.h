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

#ifndef __WARRIORMECHANICS_H
#define __WARRIORMECHANICS_H

#include "Define.h"
#include "Duration.h"
#include <vector>
#include "Generated/WarriorData.h"

class Player;
class Spell;
class SpellInfo;
class Unit;
enum WeaponAttackType : uint8;

/*
 * Warrior-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors MageMechanics.h's own
 * shape and rationale (see that file). Lives in game/Entities/Unit/ (core), not scripts/, because
 * Unit.cpp (core) can't depend on scripts/.
 */
namespace Warrior
{
    // Unit::CalculateMeleeDamage's MELEE_HIT_BLOCK case - Critical Block's guaranteed extra
    // damage-taken reduction on a successful block (Protection Warrior rework,
    // docs/prot_warrior_rework.md Row 7): "successful blocks now further reduce the damage you
    // take from the blocked hit by 8/16/25%." A flat guaranteed reduction, distinct from the
    // stock chance-based MOD_BLOCK_CRIT_CHANCE "double block" mechanic - no SpellScript hook
    // exists for "the block-value subtraction just happened", hence this core-side check.
    void ApplyBlockDamageReduction(Unit* defender, uint32& damage);

    // ---- W0a: the dampened rage model (docs/reworks/warrior-shared-rework.md "Rage generation"), W0b spell haste ----
    // Every player rage user (warriors, Bear and Dire Bear Form); creatures and pets keep the stock formula. No hook
    // sees rage, so Unit.cpp calls these at three places (// Custom: warrior-rework W0a).

    // The weapon-speed factor Unit::RewardRage's dealt formula takes, for a white swing by `attacker`. Non-players:
    // the stock Unit::GetRageWeaponSpeedHitFactor value. Players: the hasted swing time (not GetAttackTime) *
    // max(1, 1 / UNIT_MOD_CAST_SPEED) (W0b D21: spell haste keeps the speed part per swing, so it raises rage per
    // second; attack speed alone shrinks it per swing; a net slow never lowers it) * RAGE_MH_SPEED_FACTOR * m (main
    // hand) or RAGE_OH_SPEED_FACTOR (off hand), in hundredths (RAGE_SPEED_FIXED_POINT) so m's decimals survive. The
    // caller's crit doubling stays linear.
    uint32 RageSpeedFactor(Unit const* attacker, WeaponAttackType attType);

    // First line of Unit::RewardRage. Returns false (the stock body runs) unless `unit` is a player and `attacker`
    // is true (rage taken stays stock, Berserker Rage x3 included, except S1's Focused Rage branch: a player holding a
    // Focused Rage rank gets the stock taken formula x (1 + pct)). Factor 0 from an attacker call grants nothing
    // (the fully-absorbed duplicate). Otherwise: r = (k * 7.5 * d / c + speed / RAGE_SPEED_FIXED_POINT) / 2, capped at
    // the stock 15 * d / c, then aura 213 (Battle Stance +10%), then RATE_POWER_RAGE_INCOME, ModifyPower(r * 10).
    bool RewardRage(Unit* unit, uint32 damage, uint32 weaponSpeedHitFactor, bool attacker);

    // The stock rage conversion c(level) (same constants as Unit::RewardRage).
    float RageConversion(uint8 level);

    struct RageConstants
    {
        float k;
        float m;
    };

    // D13: one table keyed on level; the level-60 bracket applies at every level until 70/80 open.
    RageConstants GetRageConstants(uint8 level);

    // ---- W0b: Charge in combat (D4, user 2026-10-29) ----
    // Rage an in-combat Charge grants, in power units (tenths of a rage point, the unit spell base points use):
    // 10 * (5 + 5 * t), t = clamp((distanceYd - CHARGE_COMBAT_MIN_YD) / (CHARGE_COMBAT_MAX_YD - CHARGE_COMBAT_MIN_YD),
    // 0, 1), rounded. Flat at every level: 50 at 8 yd, 75 at 16.5 yd, 100 at 25 yd. Out-of-combat Charge keeps stock's
    // level curve (spell effect 1).
    int32 ChargeCombatRage(float distanceYd);

    // ---- S1: Protection (docs/reworks/warrior-protection-rework.md; S1 handoff D3-D7, D11, D13, D18, D19) ----
    // Bodies live in WarriorMechanics.cpp; the SpellScripts (spell_warrior_protection.cpp) and the ScriptMgr handlers
    // (warrior_hooks.cpp) call these. S2 / S3 append to the same dispatcher and helpers, never fork them.

    // Where a Storm's Bulwark grant comes from (D5). Incite never refreshes the shield's 15 s.
    enum class BulwarkSource : uint8
    {
        ThunderClap,
        Echo,
        Shockwave,
        Incite,
        Reprisal,
        EmpoweredRevenge
    };

    // roll_chance_f(min(pct x (1 + GetProcChancePercentage() / 100), 100)); the Rogue::RollProcChance copy.
    bool RollProcChance(Player const* warrior, float pct);

    // The cast-start dispatcher (WarriorPlayerScript::OnPlayerSpellCast; skips triggered casts; runs before effects).
    // S1 branches: Sword and Board's roll (D13), Improved Bloodrage (D19), the Revenge cast stamp for Incite (D11) and
    // Empowered Revenge's shield (D15), Last Stand's cast record for the Unrelenting floor (D4).
    void OnSpellCast(Player* warrior, Spell const* spell);

    // From WarriorUnitScript::OnSpellDamageTakenFinal (post-mitigation, carries isCrit). S1: Incite's capstone (D11).
    void OnSpellDamageTakenFinal(Unit* target, Unit* attacker, int32 damage, SpellInfo const* spellInfo, bool isCrit);

    // Storm's Bulwark (D5). add = pctOfMaxHealth % of max health, x (1 + Mastery) only with Storm's Bulwark rank 3
    // (200060); cap = 30% of max health x (1 + Mastery if 200060), read at this grant; the new amount is
    // max(current, min(current + add, cap)) (no source ever lowers it); creates 200028 if absent; refreshes its 15 s
    // except BulwarkSource::Incite. No Versatility, no healing modifiers. Shield Discipline's amplification is the
    // Thunder Clap script's job (its part only), not this function's.
    void GrantStormsBulwark(Player* warrior, float pctOfMaxHealth, BulwarkSource source);

    // The echo's stored value: the Thunder Clap script records the UNAMPLIFIED shield percent it computed (talent
    // ranks + targets, before Shield Discipline); the echo grants 50% of it. Kept in the player's CustomData.
    void RecordThunderClapBulwarkPct(Player* warrior, float unamplifiedPct);
    float GetRecordedThunderClapBulwarkPct(Player const* warrior);

    // Sword and Board (D13): rolls the talent rank's chance through RollProcChance. On success, deferred by `deferMs`
    // (the triggering spell's StartRecoveryTime + 100, or 1 when off the GCD): casts 50227 and clears Shield Slam's
    // cooldown, deferred once more to the end of Shield Slam's own GCD + 100 ms when that GCD is still running. The
    // dispatcher and the Thunder Clap echo both call it.
    void RollSwordAndBoard(Player* warrior, uint32 deferMs);

    // Cooldown reduction helper (D4). No-op without a cooldown entry for spellId. Never pushes the entry's end below
    // floorEnd (game-time ms, GameTime::GetGameTimeMS; 0 = no floor). deferMs > 0 runs it from m_Events (a GCD spell
    // cut during the triggering cast's GCD); a cut that lands inside spellId's own GCD waits for its end + 100 ms.
    // The amount is real time: never scaled by Cooldown Haste.
    void ReduceCooldown(Player* warrior, uint32 spellId, Milliseconds amount, Milliseconds floorEnd = 0ms,
        uint32 deferMs = 0);

    // Last Stand cast record (D4): the dispatcher records the cast time and the hasted cooldown length at cast
    // (SpellCooldown::maxduration is the UNHASTED length and `end - maxduration` stops being the cast time once
    // Cooldown Haste's correction lands). Floor end = cast + 50% x hasted length, game-time ms; 0 when no record
    // (server restart since the cast).
    void RecordLastStandCast(Player* warrior, Milliseconds hastedCooldownLength);
    Milliseconds GetLastStandFloorEnd(Player const* warrior);

    // Percent-of-damage bleed (D7, Rogue::ApplyStoredBleed shape with REPLACE semantics: a new application replaces
    // the running share, it never adds). holderId is the visible holder aura (200030); the per-tick amount is
    // totalDamage / the holder's tick count, stored per (caster, holder) in the target's CustomData. Casts the holder
    // if absent; refreshes its full duration and restarts the period otherwise.
    void ApplyPercentBleed(Player* warrior, Unit* target, uint32 holderId, uint32 totalDamage, bool accumulate = false);
    // The current per-tick amount of this warrior's bleed on target (0 if none).
    uint32 GetPercentBleedTick(Unit const* warrior, Unit const* target, uint32 holderId);

    // ---- S2: Arms (docs/reworks/warrior-arms-rework.md; S2 handoff D3-D25; contract frozen by the S2 brief) ----
    // Bodies live in WarriorMechanics.cpp. The ScriptMgr handlers (warrior_hooks.cpp) call the hook entry points
    // below after a cheap reject (null pointers, non-player attacker); every branch filters inside the body. Per-player
    // stashes live in Player::CustomData (never a static map: map threads). Ids come from WarriorData::.

    // ApplyPercentBleed (above) gains an `accumulate = false` parameter (D5): with it, perTick = (perTick x ticksLeft
    // + total) / ticks (the Rogue::ApplyStoredBleed formula), then the same full refresh + ResetPeriodic(true). S1's
    // callers keep replace semantics.

    // ---- Unit hook entry points (WarriorUnitScript enables exactly: the three Modify* hooks below,
    // OnPeriodicDamageFinal and OnSpellDamageTakenFinal) ----
    // UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN. In this order, for a player attacker: (1) Sweeping capture (D4: the attacker
    // has Sweeping Strikes and the spell is a sweep source -> stash share = damage / the target's
    // MOD_DAMAGE_PERCENT_TAKEN multiplier x 40% (45/50% with Improved Sweeping Strikes) in the attacker's CustomData),
    // (2) Colossus Smash x GetColossusSmashMultiplier, (3) Exploiter x GetExploiterMultiplier (Mortal Strike only).
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo);
    // UNITHOOK_MODIFY_MELEE_DAMAGE: Colossus Smash on white swings (spellInfo null path).
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage);
    // UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK: Colossus Smash on Rend ticks (skips positive spells: heal ticks pass
    // through this hook too).
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage, SpellInfo const* spellInfo);
    // UNITHOOK_ON_PERIODIC_DAMAGE_FINAL (pre-absorb): Second Wind on Rend ticks (OnBleedTick).
    void OnPeriodicDamageFinal(Unit* target, Unit* attacker, uint32 damage, SpellInfo const* spellInfo, bool isCrit);
    // OnSpellDamageTakenFinal (declared above, S1) is extended, in this order: Incite (family-filtered inside, S1
    // behaviour unchanged), Sweeping spend (erase the stash, CastSweepingCopies), Avatar (ApplyColossusSmash after the
    // damage, D7/Q16), the copy 204494 crit -> ApplyDeepWounds, the whirl 204495 crit -> ApplyDeepWounds + the crit
    // stamp (D10), Seismic sums for 1680 / 44949 (D19), Second Wind on the Deep Wounds tick (D18).

    // ---- Colossus Smash (D3) ----
    // 1 + (15 + Mastery% if the attacker knows talent 60456's rank spell 204490) / 100 when `target` carries the
    // attacker's own debuff 204491, else 1.0f. spellInfo null = a white swing. Returns 1.0f for the button's own id
    // (204490) and for stored-share ids (Seismic echo 204509, Bloodstorm tick 204775).
    float GetColossusSmashMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo);
    // Casts the debuff 204491 triggered on `target` (Avatar, Weight of the Earth, the Sweeping copy of a Colossus Smash
    // hit). Never the button (it would deal 150% and grey the button).
    void ApplyColossusSmash(Player* warrior, Unit* target);

    // ---- Exploiter (D15) ----
    // 1 + rank% x stacks / 100 of the attacker's own debuff 204504 on target; Mortal Strike's id only, else 1.0f.
    float GetExploiterMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo);

    // ---- Sweeping Strikes (D4) ----
    // The copy casts 204494 (bp = share, a FINAL value) on up to 4 units within 8 yd
    // of mainTarget that are Engagement::IsEngagedWithOwnerOrGroup, nearest first; the stash is erased first (re-
    // entrancy). A copy crit calls ApplyDeepWounds; a copy of a Colossus Smash hit then casts 204491 on its target.
    // Called from OnSpellDamageTakenFinal.
    void CastSweepingCopies(Player* warrior, Unit* mainTarget, SpellInfo const* spellInfo);
    // <= 4 units, 8 yd from mainTarget, engaged with the owner or group, nearest first, mainTarget excluded.
    std::vector<Unit*> SelectSweepingTargets(Player* warrior, Unit* mainTarget);

    // ---- Deep Wounds (D5) ----
    // total = basis x rank% (11/22/33) x (1 + Trauma 15/30%) -> ApplyPercentBleed(...,
    // DEEP_WOUNDS holder 204496, accumulate = true). basis = the crit weapon's average damage (attType: MH, or OH) +
    // AP x weapon speed / 14, with neither the two-hander talents' percent nor Versatility. Players only (the stock
    // rank spells are also cast by NPCs).
    void ApplyDeepWounds(Player* warrior, Unit* target, WeaponAttackType attType);

    // ---- Mortal Strike (D25): AfterHit, landed, main target, once. In order: Colossus Smash -2 s (deferred past the
    // GCD), Taste for Blood capstone (50% -> 204403), Juggernaut Rend (consume 204499, cast Rend 772 triggered),
    // remove this caster's Exploiter debuff, Strength of Arms buff, Endless Rage overflow buff (204503). ----
    void OnMortalStrikeHit(Player* warrior, Unit* target);

    // ---- Sudden Death (D9) ----
    // RemoveSpellCooldown(Mortal Strike, true) now, or deferred once to Mortal Strike's own GCD end + 100 ms while that
    // sweep still runs (never wait on the GCD category).
    void ResetMortalStrike(Player* warrior);
    // Milliseconds left of spellId's OWN recovery sweep + 100 ms: bounded by end - maxduration + StartRecoveryTime, and
    // by the player's running GCD entry, which holds the hasted length the cast really got (S2 fix pass m3); S1's
    // ShieldSlamGcdRemainingMs generalised (S1's caller keeps its behaviour, now with the hasted GCD).
    uint32 OwnGcdRemainingMs(Player* warrior, uint32 spellId);

    // ---- Bladestorm (D10): the once-per-whirl rolls, called from the whirl 204495's AfterCast (skip with 0 targets).
    // Sudden Death (shares the talent aura's proc cooldown via Aura::IsProcOnCooldown / AddProcCooldown), Wrecking
    // Crew if any target critted (the crit stamp the OnSpellDamageTakenFinal branch wrote), the sword strike. Clears
    // the stamp. ----
    void RollOncePerCastMeleeProcs(Player* warrior, Unit* firstTarget);

    // ---- Seismic Reverberation (D19). RecordWhirlwindHit is called by the OnSpellDamageTakenFinal branch for 1680 /
    // 44949 (pre-absorb); the 1680 script's AfterCast calls ScheduleSeismicEcho (+500 ms on m_Events, counts the
    // targets then, needs >= 3, casts 204509 with bp = 25/50% x the target's sum on each living target, clears the
    // sums). ----
    void RecordWhirlwindHit(Player* warrior, Unit* target, int32 damage);
    void ScheduleSeismicEcho(Player* warrior);

    // ---- Endless Rage (D11). The one core line in Unit::ModifyPower calls this with the rage that did not fit, in
    // power units. Returns at once unless `unit` is a player knowing 204544 (the capstone rank). Fractional carry in
    // CustomData; whole points -> 204503 ModStackAmount up to 20, duration refreshed on every point. ----
    void OnRageOverflow(Unit* unit, int32 overflowPower);

    // ---- Second Wind (D18): heal 204510 on self, bp = damage x (2/4%) x (2 below 35% health). Rend ticks and the
    // Deep Wounds tick. ----
    void OnBleedTick(Player* warrior, Unit* target, SpellInfo const* tickSpell, uint32 damage);

    // ---- Blood Frenzy (D20): casts the rank's debuff (30069 / 30070) on target while either of this warrior's bleeds
    // (Rend, the Deep Wounds holder) is on it, removes this caster's debuff when neither is. Called from the Rend and
    // Deep Wounds holder AuraScripts' AfterEffectApply / AfterEffectRemove (death removal included). ----
    void UpdateBloodFrenzy(Player* warrior, Unit* target);

    // ---- Juggernaut (D13): RollProcChance(rank%: 50 / 100) -> 204499 (visible) + 204500 (hidden Slam crit charge),
    // 20 s. Called from spell_warr_charge_rework (distance > 20 yd or target health > 90%) and the Heroic Leap
    // landing. ----
    void GrantJuggernaut(Player* warrior);

    // ---- Anger Management capstone (D12): casts 204508 on the warrior when it knows rank 3 (204542). Charge calls
    // it. ----
    void GrantAngerManagementCapstone(Player* warrior);

    // ---- Weapon Specialization (D17, Q3): keeps exactly one hidden passive of 204512-204520 (axe/polearm, mace,
    // sword x learned rank) matching the MAIN-HAND subclass; removes the other eight. Called from the login / equip /
    // talent-change hooks (WarriorPlayerScript) and nowhere else. ----
    void UpdateWeaponSpecialization(Player* warrior);

    // ====================================================================================================
    // ====================================================================================================
    // S3 (Fury, docs/reworks/warrior-fury-rework.md). FROZEN CONTRACT (S3-WP-BRIEF.md): bodies in WarriorMechanics.cpp
    // (agent B1), callers in spell_warrior_fury.cpp (B2), warrior_hooks.cpp (B5). Ids = WarriorData:: constants
    // (header regenerated after A2); "rank carrier" = a DUMMY effect read with GetRankCarrier, never HasSpell.

    // ---- Enrage (D3/D4). "Enraged" everywhere = the Fury Enrage buff 204636 (SPELL_ENRAGE_BUFF) is on the unit. ----
    bool IsEnraged(Unit const* unit);

    // The rage meter (D3). `powerPaid` is rage in power units (x10) actually PAID: the dispatcher passes
    // spell->GetPowerCost() of every non-triggered rage cast, the fork Execute script passes the extra rage it
    // removed. No-op unless the warrior holds an Enrage rank AURA (talent 155 chain, DUMMY carrier). Adds to a
    // CustomData meter (carry-over kept), at ENRAGE_METER_FILL x10 power units: GrantEnrage-style refresh cast of
    // 204636 (never stacks) and the meter is reduced by one fill; nothing is banked while Death Wish is up (Q18).
    // Display aura 204635 = meter / (ENRAGE_METER_STACK x10) stacks, SetStackAmount only on a change, removed at 0.
    void AddRagePaid(Player* warrior, int32 powerPaid);

    // Clears the meter, its CustomData and the 204635 display (talent reset; called deferred 1 ms by B5).
    void ResetEnrageMeter(Player* warrior);

    // Forced Enrage (Recklessness, Death Wish, Rampage's second application is NOT this): casts 204636 (refresh) when
    // the warrior holds an Enrage rank aura; otherwise nothing.
    void GrantEnrage(Player* warrior);

    // Percent damage bonus of Enrage right now: (Enrage rank carrier 2..10 + Unshackled Fury 2/4/6 + Mastery% only
    // with Unshackled Fury rank 3) x 1.5 while Death Wish 12292 is up. Also what the Rampage snapshot reads (0 when
    // not Enraged is the CALLER's job: this returns the formula value).
    float GetEnrageBonusPct(Player const* warrior);
    // Percent melee haste of Enrage: the Enrage talent rank's haste carrier only (no Unshackled, no Death Wish).
    float GetEnrageHastePct(Player const* warrior);
    // RecalculateAmount on the live 204636 damage effect, only when the summed value changed (no flicker). Called from
    // Death Wish apply/remove and the Enrage aura's 1 s periodic poll.
    void RefreshEnrageAmount(Player* warrior);
    // Death Wish hold (D5): 204636 back to its full duration (maxduration and duration); never depends on the meter.
    void HoldEnrage(Player* warrior);

    // ---- Recklessness (D6) glue, called by spell_warr_recklessness_fury. OnRecklessnessApply: GrantEnrage +
    // (Merciless rank 3) AddAura 204647. OnRecklessnessRemove: removes 204647; casts Will of the Berserker's 204643
    // when the warrior holds 204676 and `removeMode` is AURA_REMOVE_BY_EXPIRE or AURA_REMOVE_BY_DEFAULT (never cancel
    // / death / enemy spell). `removeMode` is an AuraRemoveMode value passed as uint8. ----
    void OnRecklessnessApply(Player* warrior);
    void OnRecklessnessRemove(Player* warrior, uint8 removeMode);

    // ---- One charge per ability press (Q3 / D6 / D15 / D19). A triggered child cast synchronously inside its parent
    // (Frenzied Blows' strikes 204633 / 204634, Whirlwind's off-hand 44949) runs its own mod window (Spell::cast
    // suspends the parent's) and its finish would drop a charge of every charged mod it read. Hold a guard on the stack
    // around the child's cast: while it lives, Recklessness 1719 and Bloodsurge 204652 (when up) carry one extra charge
    // for the child to spend, so the child still reads them but never spends one or takes the last; the destructor puts
    // each back to its pre-bump count (never above it, also when the child did not read the mod). The parent's own
    // finish then spends exactly one (none if the parent did not read the mod). `warrior` may be null (no-op). ----
    class PressChargeGuard
    {
    public:
        explicit PressChargeGuard(Player* warrior);
        ~PressChargeGuard();

        PressChargeGuard(PressChargeGuard const&) = delete;
        PressChargeGuard& operator=(PressChargeGuard const&) = delete;

    private:
        Player* _warrior;
        uint8 _recklessnessCharges = 0; // pre-bump count; 0 = not bumped
        uint8 _bloodsurgeCharges = 0;
    };

    // ---- Merciless (D18). 1 + rank% (3/6/9) x (2 if Enraged) when attacker is a player in Berserker Stance and
    // target health is below 35%; positive spells / no rank = 1.0f; stored-share ids (IsStoredShare) = 1.0f. Used in
    // the spell, white and periodic modify hooks next to Colossus Smash (after the Sweeping capture). ----
    float GetMercilessMultiplier(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo);
    // The stored-share ids both Colossus Smash and Merciless skip (Seismic echo 204509, Bloodstorm tick 204775): S2's
    // inline list factored into one helper (the CS code calls it too).
    bool IsStoredShare(SpellInfo const* spellInfo);

    // ---- Rampage (D7). OnRampageCast (spell_warr_rampage_fury::OnCast): snapshot GetEnrageBonusPct (0 if not
    // Enraged) and Recklessness into CustomData; if 1719 is up: exactly one charge (DropCharge BY_DEFAULT) and AddAura
    // 204679; removes Blood Rush 204637 (every Rampage consumes it, D14). StartRampage (AfterCast): strikes MH, OH,
    // MH, OH at 0/330/660/1000 ms on warrior->m_Events (OH skipped without an off-hand weapon; stops on target gone /
    // dead / out of melee range; removes 204679 at the end or on stop), plus Will of the Berserker:
    // ReduceCooldown(1719, 2 s).
    void OnRampageCast(Player* warrior);
    void StartRampage(Player* warrior, Unit* target);
    // Second Enrage application for the strike ids 204631 / 204632: (1 + snap)^2 / (1 + live) where snap = the stored
    // snapshot / 100 and live = the Enrage aura-79 amount / 100 now; 1.0f for any other spell. Called from
    // ModifySpellDamageTaken.
    float GetRampageStrikeMultiplier(Player const* warrior, SpellInfo const* spellInfo);
    // A crit that rolls no procs (Rampage strikes; NOT Frenzied Blows' strike, Q5): casts each held rank's Flurry and
    // Shredding Blows buff so they read 3 charges.
    void RefreshCritChargeBuffs(Player* warrior);

    // ---- Bloodthirst (D9-D11). Bleed bonus = 1 + min(8% x n, 40%), n = this caster's applied auras on the target
    // with MECHANIC_BLEED in their mechanic mask (classless rogue/druid bleeds included). OnBloodthirstHit (AfterHit,
    // main target, once): EnergizeBySpell rage (10 + Improved Bloodthirst carrier 3/6) x 10, casts 23885 (triggered),
    // Blood Craze heal 204650 (bp = max health x per-mille / 1000, x2 if Enraged, final value). ApplyFreshMeat: the
    // dispatcher branch on a non-triggered 23881 cast: target health above 90 / 80% (Fresh Meat carrier) -> AddAura
    // 204649. ----
    float GetBloodthirstBleedMultiplier(Player const* warrior, Unit const* target);
    void OnBloodthirstHit(Player* warrior, Unit* target);
    void ApplyFreshMeat(Player* warrior, Unit* target);

    // ---- Execute (D16/D17). GetImprovedExecuteMultiplier: 1 + rank% (8/16) x (2 if target health below 20% at the
    // hit). OnExecuteHit: rank 2 and target below 20% -> cast 204641 (one stack, refresh). Deathmaker's consumption
    // and the meter credit (AddRagePaid) live in the fork Execute script. ----
    float GetImprovedExecuteMultiplier(Player const* warrior, Unit const* target);
    void OnExecuteHit(Player* warrior, Unit* target);

    // Promoted public copy of S2's anonymous helper in spell_warrior_arms.cpp (that file is not edited) plus the
    // Rampage parent (d2 b2): a cast with a direct damage effect, Execute 5308, the Heroic Leap button or Rampage.
    bool IsStrikeCast(SpellInfo const* spellInfo);

    // ---- Titan's Grip (D31) and Two-Handed Weapon Mastery's gate (D32). UpdateTitansGripPenalty: aura 204651 present
    // iff player->CanTitanGrip() and the off-hand item is INVTYPE_2HWEAPON, else removed.
    // UpdateTwoHandedWeaponMastery: RecalculateAmountOfEffects on the 204524 / 204525 aura (the gate script zeroes its
    // effects while an off-hand weapon is wielded). Both are called ONLY from the login / equip (main hand AND off
    // hand) / talent learn / reset / spec swap / learn / forget hooks, never from inside a calc hook. ----
    void UpdateTitansGripPenalty(Player* warrior);
    void UpdateTwoHandedWeaponMastery(Player* warrior);

    // ---- Capstone and talent glue called by the fork scripts. ---- Frenzied Blows rank 2 held (the off-hand strike
    // of Heroic Strike / Cleave while Enraged).
    bool HasFrenziedBlowsCapstone(Player const* warrior);
    // Unending Fury rank 3 held: the Cleave script's AfterCast calls this, it cuts Whirlwind's cooldown by 1.5 s
    // (ReduceCooldown 1680, real seconds, GcdSafeDelayMs; a cut to zero erases the entry).
    void ReduceWhirlwindFromCleave(Player* warrior);
    // Intensify Rage rank 3 held and Pummel interrupted a cast: silence 204648 on target + the cost-free Bloodrage
    // copy 204680 on the warrior. Never cast 2687 triggered.
    void OnPummelInterrupt(Player* warrior, Unit* target);
    // Commanding Presence (D30): round(COMMANDING_PRESENCE_AT_60 x min(casterLevel, 60) / 60 x 0 / 0.5 / 1 by rank
    // carrier). The Battle Shout / Commanding Shout script's new stat effect returns this.
    int32 GetCommandingPresenceAmount(Unit const* caster);
}

#endif
