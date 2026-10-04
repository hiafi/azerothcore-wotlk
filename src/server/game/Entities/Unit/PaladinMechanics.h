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

#ifndef __PALADINMECHANICS_H
#define __PALADINMECHANICS_H

#include "Define.h"
#include "Generated/PaladinData.h"
#include "ObjectGuid.h"
#include "SharedDefines.h"
#include "SpellAuraDefines.h"
#include "UnitDefines.h"
#include <functional>
#include <initializer_list>
#include <unordered_map>
#include <vector>

class Aura;
class AuraEffect;
class DynamicObject;
class Player;
class ProcEventInfo;
class SpellInfo;
class Unit;

/*
 * Paladin-specific "doesn't fit a SpellScript/AuraScript" mechanics - mirrors WarlockMechanics.h's
 * shape. Created by the Retribution pass's (S1) WP-0 0-cpp package
 * (.agents/plans/paladin-rework/paladin-rework.SHARED.md Part A4 + B2.1, RETRIBUTION.md §0.4 / §2.7).
 * Signatures are frozen contracts: append-only, never retype an existing one. WP-0 declares them with
 * empty/pass-through bodies so WP-A and WP-B compile independently; WP-B2 filled in the bodies.
 *
 * Spell-id constants are aliased to `PaladinData::` (Generated/PaladinData.h, included above; names
 * per SHARED B0/C0 and RETRIBUTION §2.1). Stock ids with no generated name (e.g. 20184-20186, 31930,
 * 57669) and minted talent-rank ids stay hand-typed literals, WarlockMechanics.h's convention.
 */
namespace Paladin
{
    // ------------------------------------------------------------------
    // SHARED Part A4: seal ids and state
    // ------------------------------------------------------------------
    enum class SealType : uint8 { Righteousness = 0, Command, Vengeance, Justice, Light, Wisdom, Count, None = Count };

    // Id lookups (constants come from Generated/PaladinData.h once "paladin" is added to
    // CLASSES_WITH_GENERATED_HEADERS, generate.py:51).
    SealType GetSealType(uint32 sealSpellId);           // stock seal aura id -> type
    uint32   GetSealSpell(SealType type);
    uint32   GetPrimedSpell(SealType type);
    uint32   GetUnleashSpell(SealType type, bool aoe);  // 201069-201080
    uint32   GetPassiveSpell(SealType type, bool normalized); // 201081-201092
    bool     IsPrimedAura(uint32 spellId);

    // Seal state: the authority for stacks (PLAN B8). Display = SetStackAmount(max(1, stacks)).
    uint8    GetSealStacks(Player const* player);
    SealType GetActiveSeal(Player const* player);
    // Once per cast, cap 10. source = the builder's spell id; crit = Conviction capture (PLAN §2).
    // Returns the stacks actually gained (overflow past 10 is not "gained", FEASIBILITY S2 default).
    uint8    AddSealStacks(Player* player, uint8 count, uint32 sourceSpellId, bool crit);
    void     OnSealRemoved(Player* player, SealType type, AuraRemoveMode mode); // BY_EXPIRE -> Primed, else lost
    // Judgement/Deliverance: true if a Primed aura was consumed; fills its type and stack count.
    bool     ConsumePrimed(Player* player, SealType& outType, uint8& outStacks);
    void     ClearState(Player* player);                // logout (paladin_hooks.cpp)

    // Listeners notified with the stacks actually gained (Ret: Execution Sentence counter,
    // Crusade ramp). Holy registers none.
    void     NotifyStacksGained(Player* player, uint8 gained);

    // Consecration-applied hooks (added 2026-10-03 for Prot's Improved Consecration, PROTECTION §0.5):
    // SHARED's spell_pal_consecration aura calls every registered hook once in AfterEffectApply, after
    // the snapshot is stored, with the BASE_POINT0 its first tick will use.
    using ConsecrationAppliedHook = std::function<void(Unit* caster, DynamicObject* dynObj, int32 tickBasePoints)>;
    void     RegisterConsecrationAppliedHook(ConsecrationAppliedHook fn);

    // Proc Chance for scripted rolls (PLAN §2): chance * (1 + GetProcChancePercentage()/100).
    bool     RollScriptedChance(Player const* player, float baseChancePct);

    // Holy hooks called by shared code (added 2026-10-02 at HOLY.md's request; bodies in HOLY.md):
    // the Judgement/Deliverance dispatcher calls this once per cast after the own hit lands
    // (Merciful Strikes, Enlightened Judgements pulse, Judgements of the Pure haste);
    // ClearState() calls ClearHolyState().
    void     OnJudgementCastHoly(Player* player, Unit* target, bool deliverance, uint32 ownHitDamage);
    void     ClearHolyState(Player* player);
    // Ret section (Execution Sentence tracker etc.); also called by ClearState()
    void     ClearStateRet(Player* player);

    // Holy section (Holy spec file defines the bodies): Glimmer state, last Holy Shock type,
    // stored pulse values. Ret section: Execution Sentence tracker. Each spec file lists its
    // own additions under "Paladin::" and must not change the signatures above.

    // ------------------------------------------------------------------
    // SHARED Part B2.1: state and additions
    // ------------------------------------------------------------------
    struct SealState                       // one per player, keyed by ObjectGuid::LowType (Priest precedent)
    {
        SealType activeSeal = SealType::None;  uint8 activeStacks = 0;
        SealType primedSeal = SealType::None;  uint8 primedStacks = 0;  uint32 primedSerial = 0;
        // review-2 (S-M4): transient hand-off from OnSealRemoved(EXPIRE) to OnPrimedApplied, valid
        // only during that one synchronous CastSpell; primed* is written in OnPrimedApplied only.
        SealType pendingPrimedSeal = SealType::None;  uint8 pendingPrimedStacks = 0;
        uint32   judgementSerial = 0;          // bumped once per Judgement/Deliverance cast
        std::unordered_map<uint32, uint32> claimedSerials;   // guardKey -> judgementSerial
        uint32   builderCritSpellId = 0;  uint32 builderCritMs = 0;   // Conviction capture
    };

    void     OnSealApplied(Player* player, SealType type, Aura* sealAura);
    void     OnPrimedApplied(Player* player, SealType type, Aura* primedAura, uint32& outSerial);
    void     OnPrimedRemoved(Player* player, SealType type, uint32 serial);
    // review-2: also requires HasAura(GetPrimedSpell(type))
    bool     PeekPrimed(Player const* player, SealType& outType, uint8& outStacks);
    uint8    GetBuilderBaseCount(uint32 spellId);            // 1; Wake of Ashes 3 (Ret adds its id)
    void     NoteBuilderCrit(Player* player, uint32 spellId); // Conviction's HIT-phase proc (Ret)
    bool     ConsumeBuilderCrit(Player* player, uint32 spellId);

    // Hook registries (Ret/Holy register in their AddSC_*; append-only, warlock RegisterInstantCastSource precedent)
    using StackGainModifier    = std::function<uint8(Player*, uint8 count, uint32 sourceSpellId, bool crit)>;
    using StacksGainedListener = std::function<void(Player*, uint8 gained)>;
    using SealSourceFilter     = std::function<bool(Player const*, SpellInfo const*)>;
    void RegisterStackGainModifier(StackGainModifier fn);      // Conviction 2-on-crit, Improved Judgements +1
    void RegisterStacksGainedListener(StacksGainedListener fn); // ES counter, Crusade ramp (NotifyStacksGained)
    void RegisterSealPassiveVeto(SealSourceFilter fn);          // true = no passive/chance from this source
    void RegisterSealPassiveMagicSource(SealSourceFilter fn);   // true = this MAGIC-class source may proc
    bool IsSealPassiveSource(Player const* player, ProcEventInfo const& eventInfo); // review-2: needs actor/target
    bool IsMultiTargetAttack(SpellInfo const* procSpell);      // _masks MULTI_TARGET_ATTACKS or IsAffectingArea()

    // Judgement / unleash (B3, B4)
    struct UnleashBonus { float effectPct = 0.0f; float lightPerStackPct = 0.0f; };
    using UnleashBonusProvider = std::function<void(Player const*, SealType, UnleashBonus&)>;
    void         RegisterUnleashBonusProvider(UnleashBonusProvider fn);   // Sanctified Seals (Ret)
    UnleashBonus GetUnleashBonus(Player const* player, SealType type);
    struct UnleashContext { SealType type; uint8 stacks; bool aoe; bool controlled; };
    UnleashContext const* GetUnleashContext(Player const* player);
    // RAII: sets/clears the player's context around one CastSpell. Nests (a stack per player). The storage
    // lives in PaladinMechanics.cpp next to GetUnleashContext; defined here (WP-B2) so there is exactly
    // one definition and the storage cannot be bypassed.
    class UnleashContextScope
    {
    public:
        UnleashContextScope(Player* player, UnleashContext const& ctx);
        UnleashContextScope(Player* player, SealType type, uint8 stacks, bool aoe, bool controlled);
        ~UnleashContextScope();
        UnleashContextScope(UnleashContextScope const&) = delete;
        UnleashContextScope& operator=(UnleashContextScope const&) = delete;

    private:
        ObjectGuid _guid;
    };
    // (1+0.10*stacks)*(1+effectPct/100)*(controlled?2:1)
    float  GetUnleashMultiplier(Player const* player, UnleashContext const& ctx);
    uint32 BeginJudgementCast(Player* player);                  // returns the new serial
    bool   TryClaimJudgementCast(Player* player, uint32 guardKey); // first call per cast per key -> true
    struct JudgementCastInfo
    {
        Player* caster; Unit* mainTarget; uint32 castSpellId; bool deliverance;
        bool primedConsumed; SealType seal; uint8 stacks; std::vector<Unit*> const& targetsHit;
    };
    using JudgementCastHook = std::function<void(JudgementCastInfo const&)>;
    void RegisterJudgementCastHook(JudgementCastHook fn, bool onlyWhenPrimedConsumed);
    void FireJudgementCastHooks(JudgementCastInfo const& info);
    // MOD_STUN | MOD_CONFUSE | MOD_SILENCE | MOD_PACIFY_SILENCE | MOD_DISARM(_OFFHAND/_RANGED)
    bool IsControlled(Unit const* target);
    bool IsBossForStun(Unit const* target);  // creature && (isWorldBoss() || IsDungeonBoss())  (Creature.h:124,132)
    int32 RoundPctAmount(float pct);         // std::lround; >= 1 when pct > 0; 0 when pct <= 0

    // Class-wide baseline helpers (B5)
    // generated coefficient x healing SP
    int32 CalculateAbsorbBonus(Unit* caster, AuraEffect const* aurEff, int32 amount);
    // Runs every hook registered through Part A's RegisterConsecrationAppliedHook (B5.6a; added in Part C review)
    void  FireConsecrationAppliedHooks(Unit* caster, DynamicObject* dynObj, int32 tickBasePoints);

    // ------------------------------------------------------------------
    // Retribution section (RETRIBUTION.md §0.4 / §2.7 / §6.12). Registered with SHARED's registries
    // from RegisterRetributionHooks(), called at the top of AddSC_paladin_retribution_spell_scripts().
    // NoteBuilderCrit / ConsumeBuilderCrit are SHARED's (above), not Ret's.
    // ------------------------------------------------------------------
    bool   HasImprovedJudgements(Player const* player);
    uint8  ModifyStackGainRet(Player* player, uint8 count, uint32 sourceSpellId, bool crit);
    void   OnStacksGainedRet(Player* player, uint8 gained);
    void   OnJudgementCastRet(JudgementCastInfo const& info);
    float  GetSanctifiedSealsPct(Player const* player);
    float  GetSanctifiedSealsLightBuffPerStackPct(Player const* player);
    void   RegisterRetributionHooks();
    // RETRIBUTION §11 R1: one boot-time LOG_INFO with the registry sizes, called from AddSC_paladin_hooks()
    // (the loader runs it after AddSC_paladin_retribution_spell_scripts()).
    void   LogRegistrySizes();

    // Execution Sentence tracker (state: map keyed by player guid, erased by ClearStateRet)
    void       StartExecutionSentence(Player* player, ObjectGuid target);   // ES AfterEffectApply
    ObjectGuid GetExecutionSentenceTarget(Player const* player);
    // stacks gained while the hammer is up (SHARED's "gained", overflow excluded)
    uint8      GetExecutionSentenceGained(Player const* player);
    // after the burst/splash casts, and in ClearStateRet
    void       EndExecutionSentence(Player* player);

    // ------------------------------------------------------------------
    // Holy section (HOLY.md §2.8). WP-0 declares; WP-B2 fills the bodies.
    // ------------------------------------------------------------------
    enum class ShockType : uint8 { None = 0, Heal, Damage };
    constexpr uint8 GLIMMER_CAP = 5;                         // per caster, allies + enemies together
    constexpr float GLIMMER_PULSE_PCT = 15.0f;               // [TUNE] H "Glimmer's 15% pulse"
    constexpr float DIVINE_TOLL_REPEAT_PCT = 50.0f;          // [TUNE] H "Divine Toll's 50% repeats"
    constexpr uint8 DIVINE_TOLL_SHOCKS = 10;
    constexpr uint8 DIVINE_TOLL_MAX_TARGETS = 5;
    constexpr float DIVINE_TOLL_RANGE = 30.0f;

    void      SetLastShockType(Player* player, ShockType type);
    ShockType GetLastShockType(Player const* player);

    // Glimmer deque (FEASIBILITY §8; C46 - no native N-per-caster cap).
    // Apply or refresh; a refresh moves the entry to the back. At GLIMMER_CAP with a new target, the
    // front (oldest) entry's aura is removed first. Never pulses. No-op unless the caster knows
    // Glimmer of Light (any rank). The new entry is pushed only after the CastSpell, and only if
    // target->GetAura(markerId, caster->GetGUID()) exists.
    void      ApplyGlimmer(Player* caster, Unit* target);
    void      OnGlimmerRemoved(ObjectGuid casterGuid, ObjectGuid targetGuid, uint32 markerSpellId);
    uint8     GetGlimmerCount(Player const* caster);

    // Done-side value Holy Shock would deal to `target` as `type` right now (HOLY §2.8), pre-taken.
    int32     ComputeShockValue(Player* caster, Unit* target, ShockType type, bool crit);
    // Engine-equivalent crit roll for a script-valued Shock (Divine Toll, H2).
    bool      RollShockCrit(Player* caster, Unit* target, ShockType type);
    // 1 + (15 + Mastery%)/100 with Glimmer r3 (201270), else 1. Mastery read live (CORE-AUDIT S8).
    float     GetGlimmerShockMultiplier(Player const* player);

    // Pulse every owned Glimmer once at pctOfShock% of ComputeShockValue(target's own type, crit); stores
    // the latest heal and damage pulse value (HOLY §2.8: no combat / CC filter, fixed reference victim).
    void      PulseGlimmers(Player* caster, bool crit, float pctOfShock);
    // Enlightened Judgements: pulse every Glimmer at pctOfStored% of the stored value of its type.
    void      PulseGlimmersFromStored(Player* caster, float pctOfStored);

    // H §5 step 5, run once per Holy Shock (resolver) or once per Divine Toll. Holy Guidance's debuff is
    // per target, so callers apply it themselves (ApplyHolyGuidance).
    void      RunShockCastHooks(Player* caster, ShockType type);
    void      ApplyHolyGuidance(Player* caster, Unit* target, ShockType type);
    void      AddDawnBeforeDuskStack(Player* caster);        // +1, or remove at 3 (reset)

    // OnJudgementCastHoly / ClearHolyState are declared in Part A above (not redeclared here).

    // Merciful Strikes / Overflowing Light / Divine Toll share this: split `total` evenly over `targets`.
    void      CastSplitHeal(Player* caster, uint32 healSpellId, std::vector<Unit*> const& targets, int32 total);

    // Illuminated Steel's "fromInt" (HOLY §6.5): GetSpellCritFromIntellect() minus the class base crit
    // (percent points). Added by B2 so spell_pal_illuminated_steel's DoEffectCalcAmount can call it.
    float     GetSpellCritFromIntellectOnly(Player* player);
    void      RefreshIlluminatedSteel(Player* player);       // paladin_hooks.cpp OnPlayerAfterUpdateMaxPower
    int32     GetRankAmount(Unit const* caster, std::initializer_list<uint32> rankSpellIdsHighFirst, uint8 effIndex);
}

#endif
