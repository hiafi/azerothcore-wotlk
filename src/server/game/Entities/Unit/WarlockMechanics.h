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

#ifndef __WARLOCKMECHANICS_H
#define __WARLOCKMECHANICS_H

#include "Define.h"
#include "SharedDefines.h"
#include "UnitDefines.h"
#include <deque>
#include <functional>
#include <initializer_list>
#include <unordered_map>
#include <vector>

class Aura;
class AuraEffect;
class ObjectGuid;
class Player;
class Spell;
class SpellInfo;
class Unit;
enum DamageEffectType : uint8;

/*
 * Warlock-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors DruidMechanics.h /
 * PriestMechanics.h's shape. Created by the Affliction pass's WP-0
 * (.agents/plans/warlock-rework/warlock-rework.PLAN.md §5/§6 item 3,
 * warlock-rework.SHARED.md §4). Destruction and Demonology extend it with their own functions
 * (PLAN §7 cross-spec ownership table) - append-only, never retype an existing signature.
 *
 * WP-0 declares this skeleton's signatures (SHARED §4's cross-spec contract plus the
 * Affliction-local members AFFLICTION.md §3 item 5 lists); WP-B (spell_warlock_affliction.cpp /
 * warlock_hooks.cpp / WarlockMechanics.cpp) fills in the bodies - see
 * warlock-rework.AFFLICTION.md §7 for the per-clause mapping.
 */
namespace Warlock
{
    // ------------------------------------------------------------------
    // New spells this pass mints (AFFLICTION.md §2.1, spell block 200720-200819)
    // ------------------------------------------------------------------
    constexpr uint32 SPELL_BANE_OF_AGONY_STACKS = 200720;
    constexpr uint32 SPELL_TAINTED_SOUL = 200721;
    constexpr uint32 SPELL_TAINTED_SOUL_ERUPTION = 200722;
    constexpr uint32 SPELL_INEVITABLE_DEMISE = 200723;
    constexpr uint32 SPELL_GRIM_REACH_DEBUFF = 200724;
    constexpr uint32 SPELL_GRIM_REACH_BOLT = 200725;
    constexpr uint32 SPELL_IMPROVED_LIFE_TAP_BUFF = 200726;
    constexpr uint32 SPELL_SIPHON_POWER_BUFF = 200727;
    constexpr uint32 SPELL_AGONIZING_PAIN_BOLT = 200728;
    constexpr uint32 SPELL_PHANTOM_SINGULARITY = 200729;                // talent (4,1) castable
    constexpr uint32 SPELL_PHANTOM_SINGULARITY_DAMAGE = 200730;
    constexpr uint32 SPELL_PHANTOM_SINGULARITY_HEAL = 200731;
    constexpr uint32 SPELL_DARK_SOUL_MISERY = 200732;                   // talent (8,1) castable
    constexpr uint32 SPELL_SOUL_SWAP = 200733;
    constexpr uint32 SPELL_SOUL_SWAP_EXHALE = 200734;
    constexpr uint32 SPELL_SOUL_SWAP_COPIED_MARKER = 200735;
    constexpr uint32 SPELL_SOUL_HARVEST = 200736;
    // 200737 spare (reserved: separate pet aura for Soul Harvest, AFFLICTION.md §5)
    constexpr uint32 SPELL_BURNING_RUSH = 200738;

    // Shadow Pact r1/r2/r3 (talent 60071) - hidden crit passives linked from these
    constexpr uint32 SPELL_SHADOW_PACT_R1 = 200739;
    constexpr uint32 SPELL_SHADOW_PACT_R2 = 200740;
    constexpr uint32 SPELL_SHADOW_PACT_R3 = 200741;                     // carries the Tainted Soul proc

    // Death's Grasp r1/r2/r3 (talent 1005, repurposed Suppression)
    constexpr uint32 SPELL_DEATHS_GRASP_R1 = 200742;
    constexpr uint32 SPELL_DEATHS_GRASP_R2 = 200743;
    constexpr uint32 SPELL_DEATHS_GRASP_R3 = 200744;

    // Harvester of Death r1/r2/r3 (talent 1668, repurposed Improved Howl of Terror)
    constexpr uint32 SPELL_HARVESTER_OF_DEATH_R1 = 200745;
    constexpr uint32 SPELL_HARVESTER_OF_DEATH_R2 = 200746;
    constexpr uint32 SPELL_HARVESTER_OF_DEATH_R3 = 200747;              // linked to the capstone below
    constexpr uint32 SPELL_HARVESTER_OF_DEATH_CAPSTONE = 200748;        // hidden passive, linked from R3

    // Lingering Agony r1/r2 (talent 2205, repurposed Improved Fear)
    constexpr uint32 SPELL_LINGERING_AGONY_R1 = 200749;
    constexpr uint32 SPELL_LINGERING_AGONY_R2 = 200750;

    // Creeping Agony r1/r2/r3 (talent 1061, repurposed Amplify Curse)
    constexpr uint32 SPELL_CREEPING_AGONY_R1 = 200751;
    constexpr uint32 SPELL_CREEPING_AGONY_R2 = 200752;
    constexpr uint32 SPELL_CREEPING_AGONY_R3 = 200753;                  // carries the Bane spread capstone

    // Agonizing Pain r1/r2 (talent 60070, minted)
    constexpr uint32 SPELL_AGONIZING_PAIN_R1 = 200754;
    constexpr uint32 SPELL_AGONIZING_PAIN_R2 = 200755;

    // Fatal Echoes r1/r2/r3 (talent 1022, repurposed Dark Pact)
    constexpr uint32 SPELL_FATAL_ECHOES_R1 = 200756;
    constexpr uint32 SPELL_FATAL_ECHOES_R2 = 200757;
    constexpr uint32 SPELL_FATAL_ECHOES_R3 = 200758;                    // carries the UA re-echo capstone

    // Virulence r1/r2/r3 (talent 60072, minted)
    constexpr uint32 SPELL_VIRULENCE_R1 = 200759;
    constexpr uint32 SPELL_VIRULENCE_R2 = 200760;
    constexpr uint32 SPELL_VIRULENCE_R3 = 200761;                       // carries the Seed-spreads-Corruption capstone

    // Compounding Darkness r1/r2/r3 (talent 60073, minted)
    constexpr uint32 SPELL_COMPOUNDING_DARKNESS_R1 = 200762;
    constexpr uint32 SPELL_COMPOUNDING_DARKNESS_R2 = 200763;
    constexpr uint32 SPELL_COMPOUNDING_DARKNESS_R3 = 200764;

    // New ranks of existing talents (one new rank id each, AFFLICTION.md §2.1/§2.2)
    constexpr uint32 SPELL_IMPROVED_LIFE_TAP_R3 = 200765;               // talent 1007, clone of 18183
    constexpr uint32 SPELL_NIGHTFALL_R3 = 200766;                       // talent 1002, clone of 18095
    constexpr uint32 SPELL_SIPHON_LIFE_R2 = 200767;                     // talent 1041, clone of 63108
    constexpr uint32 SPELL_PANDEMIC_R2 = 200768;                        // talent 2245, clone of 58435

    constexpr uint32 SPELL_INEVITABLE_DEMISE_CAPSTONE = 200769;         // hidden passive, linked from 18372
    constexpr uint32 SPELL_FEL_CONCENTRATION_HEAL = 200770;             // Fel Concentration r3 capstone
    constexpr uint32 SPELL_IMPROVED_FELHUNTER_PET_BUFF = 200771;        // MOD_DAMAGE_PERCENT_DONE on the pet

    // SHARED ids this pass declares the data for (warlock-shared block, SHARED.md §1)
    constexpr uint32 SPELL_SHADOW_PACT_CRIT_R1 = 200698;                // linked from SPELL_SHADOW_PACT_R1
    constexpr uint32 SPELL_SHADOW_PACT_CRIT_R2 = 200699;
    constexpr uint32 SPELL_SHADOW_PACT_CRIT_R3 = 200700;
    constexpr uint32 SPELL_REACH_R1 = 200707;                           // +3 yd, linked from Grim Reach r1
    constexpr uint32 SPELL_REACH_R2 = 200708;                           // +6 yd, linked from Grim Reach r2
    constexpr uint32 SPELL_SOUL_SHARD_BUFF = 200709;
    constexpr uint32 SPELL_SOULBURN = 200710;
    constexpr uint32 SPELL_SOULBURN_MARKER = 200711;
    constexpr uint32 SPELL_SOULBURN_HAUNT_DEBUFF = 200712;
    // 200713 (instant-cast helper) is Destruction's data row (S2) - only the registry/handlers here.

    // ------------------------------------------------------------------
    // Stock ids this pass reuses (no new id) - AFFLICTION.md §2.1 "Stock ids reused" plus every
    // id its §3 item 5 lists explicitly.
    // ------------------------------------------------------------------
    constexpr uint32 SPELL_CORRUPTION = 172;
    constexpr uint32 SPELL_BANE_OF_AGONY = 980;                         // renamed from Curse of Agony
    constexpr uint32 SPELL_UNSTABLE_AFFLICTION = 30108;
    constexpr uint32 SPELL_SEED_OF_CORRUPTION_DOT = 27243;
    constexpr uint32 SPELL_SEED_OF_CORRUPTION_DETONATION = 27285;
    constexpr uint32 SPELL_DRAIN_SOUL = 1120;
    constexpr uint32 SPELL_DRAIN_LIFE = 689;
    constexpr uint32 SPELL_LIFE_TAP = 1454;
    constexpr uint32 SPELL_HAUNT = 48181;
    constexpr uint32 SPELL_SHADOW_TRANCE = 17941;                       // Nightfall's instant-cast buff
    constexpr uint32 SPELL_CURSE_OF_EXHAUSTION = 18223;
    constexpr uint32 SPELL_FEL_DOMINATION = 18708;
    constexpr uint32 SPELL_EVERLASTING_AFFLICTION_EFFECT = 47422;
    constexpr uint32 SPELL_SIPHON_LIFE_HEAL = 63106;
    constexpr uint32 SPELL_HAUNT_HEAL = 48210;
    constexpr uint32 SPELL_IMPROVED_DRAIN_SOUL_ENERGIZE = 18371;
    constexpr uint32 SPELL_SHADOW_BOLT = 686;
    constexpr uint32 SPELL_DEATH_COIL = 6789;
    constexpr uint32 SPELL_SHADOWBURN = 29341;
    constexpr uint32 SPELL_FEAR = 5782;
    constexpr uint32 SPELL_HOWL_OF_TERROR = 5484;
    constexpr uint32 SPELL_SHADOW_BITE_R1 = 54049;                      // Felhunter pet ability, all 5 ranks
    constexpr uint32 SPELL_SHADOW_BITE_R2 = 54050;
    constexpr uint32 SPELL_SHADOW_BITE_R3 = 54051;
    constexpr uint32 SPELL_SHADOW_BITE_R4 = 54052;
    constexpr uint32 SPELL_SHADOW_BITE_R5 = 54053;
    constexpr uint32 SPELL_SPELL_LOCK_R1 = 19244;                       // Felhunter pet ability
    constexpr uint32 SPELL_SPELL_LOCK_R2 = 19647;
    constexpr uint32 SPELL_DEVOUR_MAGIC = 19505;                        // Felhunter pet ability

    // ------------------------------------------------------------------
    // Talent ids and rank spell ids referenced by this pass's scripts (AFFLICTION.md §2.2)
    // ------------------------------------------------------------------
    constexpr uint32 TALENT_IMPROVED_BANE_OF_AGONY = 1284;
    constexpr uint32 SPELL_IMPROVED_BANE_OF_AGONY_R1 = 18827;
    constexpr uint32 SPELL_IMPROVED_BANE_OF_AGONY_R2 = 18829;
    constexpr uint32 TALENT_IMPROVED_CURSES = 1006;
    constexpr uint32 SPELL_IMPROVED_CURSES_R1 = 18179;
    constexpr uint32 SPELL_IMPROVED_CURSES_R2 = 18180;
    constexpr uint32 TALENT_IMPROVED_LIFE_TAP = 1007;
    constexpr uint32 SPELL_IMPROVED_LIFE_TAP_R1 = 18182;
    constexpr uint32 SPELL_IMPROVED_LIFE_TAP_R2 = 18183;
    constexpr uint32 SPELL_SIPHON_POWER_R1 = 18213;                     // talent 1101 (Improved Drain Soul)
    constexpr uint32 SPELL_SIPHON_POWER_R2 = 18372;
    constexpr uint32 SPELL_FEL_CONCENTRATION_R1 = 17783;                // talent 1001
    constexpr uint32 SPELL_FEL_CONCENTRATION_R2 = 17784;
    constexpr uint32 SPELL_FEL_CONCENTRATION_R3 = 17785;
    constexpr uint32 SPELL_SOUL_SIPHON_R1 = 17804;                      // talent 1004
    constexpr uint32 SPELL_SOUL_SIPHON_R2 = 17805;
    constexpr uint32 SPELL_GRIM_REACH_R1 = 18218;                       // talent 1021
    constexpr uint32 SPELL_GRIM_REACH_R2 = 18219;                       // carries the Grim Reach capstone proc
    constexpr uint32 SPELL_NIGHTFALL_R1 = 18094;                        // talent 1002
    constexpr uint32 SPELL_NIGHTFALL_R2 = 18095;
    constexpr uint32 SPELL_SIPHON_LIFE_R1 = 63108;                      // talent 1041
    constexpr uint32 SPELL_IMPROVED_FELHUNTER_R1 = 54037;               // talent 1873
    constexpr uint32 SPELL_IMPROVED_FELHUNTER_R2 = 54038;
    constexpr uint32 SPELL_CONTAGION_R1 = 30060;                        // talent 1669
    constexpr uint32 SPELL_CONTAGION_R2 = 30061;
    constexpr uint32 SPELL_CONTAGION_R3 = 30062;                        // carries the empowered-tick / spread capstone
    constexpr uint32 SPELL_ERADICATION_R1 = 47195;                      // talent 1878
    constexpr uint32 SPELL_ERADICATION_R2 = 47196;
    constexpr uint32 SPELL_ERADICATION_R3 = 47197;
    constexpr uint32 SPELL_ERADICATION_BUFF = 64371;
    constexpr uint32 SPELL_MALEDICTION_R1 = 32477;                      // talent 1667
    constexpr uint32 SPELL_MALEDICTION_R2 = 32483;
    constexpr uint32 SPELL_MALEDICTION_R3 = 32484;
    constexpr uint32 SPELL_PANDEMIC_R1 = 58435;                         // talent 2245
    constexpr uint32 SPELL_DEATHS_EMBRACE_R1 = 47198;                   // talent 1875
    constexpr uint32 SPELL_DEATHS_EMBRACE_R2 = 47199;
    constexpr uint32 SPELL_DEATHS_EMBRACE_R3 = 47200;
    constexpr uint32 SPELL_EVERLASTING_AFFLICTION_R1 = 47201;           // talent 1876
    constexpr uint32 SPELL_EVERLASTING_AFFLICTION_R2 = 47202;
    constexpr uint32 SPELL_EVERLASTING_AFFLICTION_R3 = 47203;
    constexpr uint32 SPELL_SHADOW_EMBRACE_R1 = 32385;                   // talent 1763
    constexpr uint32 SPELL_SHADOW_EMBRACE_R2 = 32387;
    constexpr uint32 SPELL_SHADOW_EMBRACE_R3 = 32392;
    constexpr uint32 SPELL_SHADOW_EMBRACE_DEBUFF_R1 = 32386;
    constexpr uint32 SPELL_SHADOW_EMBRACE_DEBUFF_R2 = 32388;
    constexpr uint32 SPELL_SHADOW_EMBRACE_DEBUFF_R3 = 32389;
    constexpr uint32 SPELL_SHADOW_MASTERY_R1 = 18271;                   // talent 1042
    constexpr uint32 SPELL_SHADOW_MASTERY_R2 = 18272;
    constexpr uint32 SPELL_SHADOW_MASTERY_R3 = 18273;

    // Talent row 1226 (repurposed in place as Impending Doom, PLAN §11 Q7 / DEMONOLOGY.md §6) -
    // data only this pass; S3 adds the C++. Named here since B13 must stop it granting Fel
    // Domination (AFFLICTION.md §4.4).
    constexpr uint32 TALENT_ROW_1226_IMPENDING_DOOM = 1226;

    // ------------------------------------------------------------------
    // B14 bane slot (the one upstream line, SpellInfo.cpp)
    // ------------------------------------------------------------------

    // True for a warlock "bane" spell (Bane of Agony 980 this pass; Demonology adds Bane of Doom
    // in S3) - keyed on spell id, not on SpellSpecific, so it works before GetSpellSpecific()
    // resolves. Used by the one upstream line in
    // SpellInfo::IsAuraExclusiveBySpecificPerCasterWith (B14, AFFLICTION.md §4.5).
    bool IsBane(SpellInfo const* spellInfo);

    // ------------------------------------------------------------------
    // Soul Shards (B9) - per-player deque of expiry timestamps, max 5, each independently expires
    // 120 s after it was gained (AFFLICTION.md §7.10; Priest per-player map precedent,
    // PriestMechanics.cpp).
    // ------------------------------------------------------------------
    void GrantSoulShard(Player* player);
    void ConsumeSoulShards(Player* player, uint8 count);
    uint8 GetSoulShardCount(Player* player);
    void ClearSoulShards(Player* player);                               // shards drop on death (§11 Q9)

    // ------------------------------------------------------------------
    // Soulburn (B10) - consumes the 200711 marker for the next qualifying cast (Seed/Haunt this
    // pass; Destruction adds Chaos Bolt/Soul Fire in S2). Returns true and removes the marker only
    // when it was up.
    // ------------------------------------------------------------------
    bool TryConsumeSoulburnMarker(Player* caster);

    // ------------------------------------------------------------------
    // Instant-cast priority arbiter (SHARED §4's "Arbiter timing contract"). Affliction creates
    // the API and an empty registry; Destruction's Soul Fire (Empowered Imp > Soulburn > Molten
    // Core) and Chaos Bolt (Chaotic Inferno only) register into it in S2.
    // ------------------------------------------------------------------
    enum class InstantCastSource : uint8
    {
        EmpoweredImp,
        Soulburn,
        MoltenCore,
        ChaoticInferno
    };

    void RegisterInstantCastSource(uint32 baseSpellId, InstantCastSource source,
                                    std::function<bool(Player*)> isReady,
                                    std::function<void(Player*)> onConsumed);

    // AllSpellScript::CanPrepare handler body (warlock_hooks.cpp) - grants the 200713 helper (data
    // row is Destruction's, S2) to the first ready registered source for this cast's base spell id.
    // Never consumes. No-op while the registry is empty (this pass).
    void OnPrepareGrantInstantCast(Player* caster, Spell* spell);

    // AllSpellScript::OnSpellCast handler body - runs the recorded source's onConsumed only when
    // this cast matches the recorded spell id, then clears the record. No-op this pass.
    void OnCastConsumeInstantCast(Player* caster, Spell* spell);

    // ------------------------------------------------------------------
    // Leech-talent exclusivity (user 2026-09-27: only the highest-% leech talent works; every
    // other leech source stacks). SHARED §4's table: SoulLeech (Destro), FelConcentration (Aff),
    // FelImmolation (Demo), SiphonLife (Aff), BlazingSpeed (Fire Mage 31641/31642/200107).
    // ------------------------------------------------------------------
    enum class LeechTalent : uint8
    {
        None,
        SoulLeech,
        FelConcentration,
        FelImmolation,
        SiphonLife,
        BlazingSpeed
    };

    LeechTalent GetActiveLeechTalent(Player const* player);
    void RefreshLeechTalents(Player* player);                           // called from
    // OnPlayerLearnTalents/OnPlayerTalentsReset/OnPlayerAfterSpecSlotChanged/OnPlayerLogin

    // ------------------------------------------------------------------
    // Pet/guardian proc-chance passthrough (SHARED §4) - every scripted proc roll on a
    // pet/guardian spell multiplies by this (the *owning warlock's* Proc Chance, not the pet's).
    // ------------------------------------------------------------------
    float GetOwnerProcChanceMultiplier(Unit* petOrGuardian);

    // Fires one synchronous AuraEffect::PeriodicTick on `target`'s aura `spellId` (owned by
    // `casterGuid`) without touching its timer/tick counter - Nightfall's UA bonus tick
    // (AFFLICTION.md §7.5), Hellstorm's injected ticks (Destruction).
    void FirePeriodicTickNow(Unit* target, ObjectGuid casterGuid, uint32 spellId, uint8 effIndex);

    // Declared for symmetry (SHARED §4), NOT wired to a core call site - PLAN §2/§5.3 found no
    // warlock SpellPctDamageModsDone dispatch is needed; every Affliction clause has its own
    // DoEffectCalcAmount/SpellScript path (Mastery, Compounding Darkness, Soul Siphon).
    void ApplyDoneDamagePctMods(Unit const* caster, Unit const* victim, SpellInfo const* spellInfo,
                                DamageEffectType damagetype, float& doneTotalMod);

    // ------------------------------------------------------------------
    // Affliction-local members (AFFLICTION.md §3 item 5) - not part of SHARED §4's cross-spec
    // contract, but declared here (not a spec-local .h) since Destruction/Demonology's own
    // WarlockMechanics extensions live in this same namespace.
    // ------------------------------------------------------------------

    // Bane of Agony stack cap (AFFLICTION.md §7.2): 10, +2 with SPELL_IMPROVED_CURSES_R1, +5 with
    // SPELL_IMPROVED_CURSES_R2 (only the higher rank's bonus applies - it's a single talent).
    uint8 GetAgonyStackCap(Unit const* caster);

    // Live stack count of the caster's SPELL_BANE_OF_AGONY_STACKS (200720) on `target`.
    uint8 GetAgonyStacks(Unit const* target, ObjectGuid casterGuid);

    // Adds `count` stacks to the caster's 200720 on `target`, capped by GetAgonyStackCap.
    void AddAgonyStacks(Unit* caster, Unit* target, uint8 count);

    // True for the four DoTs Soul Siphon/Compounding Darkness count: Corruption (172), Bane of
    // Agony (980), Unstable Affliction (30108), Phantom Singularity (200729).
    bool IsAfflictionDot(uint32 spellId);

    // Count of the caster's Affliction DoTs (IsAfflictionDot) currently on `target`, optionally
    // excluding one spell id (the DoT asking the question, so it doesn't count itself).
    uint8 CountAfflictionDots(Unit const* target, ObjectGuid casterGuid, uint32 excludeSpellId = 0);

    // Soul Siphon's live multiplier: 1 + min(step * n, cap) / 100, step/cap read from the caster's
    // Soul Siphon rank (SPELL_SOUL_SIPHON_R1/R2), n = CountAfflictionDots(target, caster).
    float GetSoulSiphonMultiplier(Unit const* caster, Unit const* target);

    // Adds `stacks` of Tainted Soul (200721) to the caster's aura on `target`; erupts (100%) and
    // removes the aura at >= 10 stacks (AFFLICTION.md §7.15).
    void AddTaintedSoul(Unit* caster, Unit* target, uint8 stacks);

    // Casts the Tainted Soul eruption (200722) at `target`'s position, scaling its damage to `pct`
    // percent of the base tooltip amount (100 on a stack-cap eruption, 10 * stacks on a death
    // eruption).
    void EruptTaintedSoul(Unit* caster, Unit* target, uint8 pct);

    // The stock Seed of Corruption detonation path (Remove() then Detonate()), invoked from the
    // rebuilt chain-detonation fix (AFFLICTION.md §7.6) once a Seed's remaining threshold reaches
    // zero or below.
    void DetonateSeed(Aura* seed);

    // Soul Swap's per-player copy store (AFFLICTION.md §7.9): the source target, an expiry time,
    // and one entry per copied DoT (Bane of Agony, Unstable Affliction - Corruption is presence
    //-only, applied fresh with no snapshot).
    struct SoulSwapEntry
    {
        uint32 spellId = 0;
        int32 amount = 0;
        float crit = 0.0f;
        float pctMods = 0.0f;
        int32 duration = 0;
        int32 maxDuration = 0;
        uint8 agonyStacks = 0;
    };

    // ------------------------------------------------------------------
    // Soul Swap store accessors (added by WP-B, AFFLICTION.md §7.9 - the header only declared the
    // SoulSwapEntry payload; these three functions are the append-only addition flagged back per
    // the WP brief's "add a new function and flag it" rule). Keyed by the inhaling player's GUID.
    // ------------------------------------------------------------------

    // Inhale (200733): records the source target and its copied DoTs, replacing any previous copy.
    void StoreSoulSwap(Player* player, ObjectGuid sourceGuid, std::vector<SoulSwapEntry> entries);

    // Exhale (200734) CheckCast: true while an un-consumed copy is held; when non-null, `outSource`
    // is filled with the copy's source target guid so CheckCast can also reject "same target".
    bool HasSoulSwapCopy(Player const* player, ObjectGuid* outSource = nullptr);

    // Exhale (200734) OnEffectHitTarget: returns true and hands back the stored copy (clearing it)
    // only when a copy is held; false leaves nothing to apply.
    bool TakeSoulSwap(Player* player, ObjectGuid& outSource, std::vector<SoulSwapEntry>& outEntries);

    // ------------------------------------------------------------------
    // Destruction pass (S2) additions - DESTRUCTION.md §2.1/§2.6/§14. Append-only: WP-B fills in
    // the bodies below and may add further Destruction-local helpers, but must not rename or
    // change the signature of anything already declared without flagging it back (mirrors the
    // Affliction WP-B precedent above).
    // ------------------------------------------------------------------

    // New spells this pass mints (DESTRUCTION.md §2.1, spell block 200960-201059)
    constexpr uint32 SPELL_VOLATILITY_R1 = 200960;                      // talent 965 (repurposed Improved Searing Pain), (0,0)
    constexpr uint32 SPELL_VOLATILITY_R2 = 200961;
    constexpr uint32 SPELL_VOLATILITY_R3 = 200962;
    constexpr uint32 SPELL_KINDLING_R1 = 200963;                        // talent 60100 (minted), (0,3)
    constexpr uint32 SPELL_KINDLING_R2 = 200964;
    constexpr uint32 SPELL_KINDLING_R3 = 200965;                        // carries the Molten Bolts proc
    constexpr uint32 SPELL_HELLSTORM_TALENT_R1 = 200966;                // talent 60101 (minted), (2,2)
    constexpr uint32 SPELL_HELLSTORM_TALENT_R2 = 200967;
    constexpr uint32 SPELL_HELLSTORM_TALENT_R3 = 200968;                // carries the Hellstorm proc
    constexpr uint32 SPELL_DEVASTATION_R2 = 200969;                     // r1 = stock 18130
    constexpr uint32 SPELL_DEVASTATION_R3 = 200970;                     // carries the Chaotic Inferno proc
    constexpr uint32 SPELL_FURY_OF_THE_VOID_R1 = 200971;                // talent 1889 (repurposed Improved Soul Leech), (7,0)
    constexpr uint32 SPELL_FURY_OF_THE_VOID_R2 = 200972;
    constexpr uint32 SPELL_FURY_OF_THE_VOID_R3 = 200973;                // read by the Shadowfury script
    constexpr uint32 SPELL_HAVOC = 200974;                              // talent 60102 (minted), (8,1) castable
    constexpr uint32 SPELL_CHAOTIC_RESONANCE_R1 = 200975;               // talent 60103 (minted), (9,2)
    constexpr uint32 SPELL_CHAOTIC_RESONANCE_R2 = 200976;
    constexpr uint32 SPELL_CHAOTIC_RESONANCE_R3 = 200977;               // read by scripts (Chaos Echo)
    constexpr uint32 SPELL_CHAOS_RIFT = 200978;                         // talent 60104 (minted), (10,1) castable - summons creature 300170
    constexpr uint32 SPELL_RIFT_BOLT = 200979;                          // triggered, cast by the Rift, 50% of Chaos Bolt
    constexpr uint32 SPELL_CHAOS_BOLT_COPY = 200980;                    // Havoc duplicate / Soulburn extra target
    constexpr uint32 SPELL_CHAOS_ECHO_BOLT = 200981;                    // full Chaos Bolt strength echo
    constexpr uint32 SPELL_CHAOS_ECHO_RIFT = 200982;                    // Rift Bolt strength echo (50%)
    constexpr uint32 SPELL_CHAOTIC_BURN = 200983;                       // DoT debuff, fixed base points from the script
    constexpr uint32 SPELL_MOLTEN_BOLTS = 200984;                       // periodic-trigger debuff, 4 x 0.5 s
    constexpr uint32 SPELL_MOLTEN_BOLT = 200985;                        // 10% of an Incinerate
    constexpr uint32 SPELL_IMMOLATE_ERUPTION = 200986;                  // Improved Immolate capstone
    constexpr uint32 SPELL_CHAOTIC_INFERNO = 200987;                    // self buff marker, 15 s
    constexpr uint32 SPELL_INTENSITY = 200988;                          // self buff, +15% haste, 8 s
    constexpr uint32 SPELL_HELLSTORM_BUFF = 200989;                     // self buff, 8 s - drives the Hellfire tick injection
    constexpr uint32 SPELL_FIRE_AND_BRIMSTONE_DEBUFF = 200990;          // target debuff, aura 271 on Soul Fire, 5%/stack, max 10
    constexpr uint32 SPELL_DESTRUCTIVE_REACH_CRIT_HELPER = 200991;      // hidden 1-charge crit SpellMod (C3)
    // 200713 (shared instant-cast helper, SHARED §1.3) - declared by this pass's WP-A (§5); the
    // registry/handlers already exist (Affliction's WP-0, above).

    // Stock ids this pass reuses (retuned) or references (DESTRUCTION.md §2.1/§5/§7)
    constexpr uint32 SPELL_RAIN_OF_FIRE = 5740;
    constexpr uint32 SPELL_RAIN_OF_FIRE_TICK = 42223;
    constexpr uint32 SPELL_CONFLAGRATE = 17962;
    constexpr uint32 SPELL_CHAOS_BOLT = 50796;                          // talent, rebased row 6
    constexpr uint32 SPELL_SHADOWFURY = 30283;                          // talent, rebased row 6
    constexpr uint32 SPELL_INCINERATE = 29722;
    constexpr uint32 SPELL_SHADOWFLAME = 47897;
    constexpr uint32 SPELL_IMMOLATE = 348;
    constexpr uint32 SPELL_SHADOWBURN = 29341;
    constexpr uint32 SPELL_SOUL_FIRE = 6353;
    constexpr uint32 SPELL_IMP_FIREBOLT = 3110;
    constexpr uint32 SPELL_BACKLASH_BUFF = 34936;                       // "Your next Shadow Bolt or Incinerate ..." -> retuned to Immolate only
    constexpr uint32 SPELL_EMPOWERED_IMP_BUFF = 47283;
    constexpr uint32 SPELL_BACKDRAFT_R1 = 54274;
    constexpr uint32 SPELL_BACKDRAFT_R2 = 54276;
    constexpr uint32 SPELL_BACKDRAFT_R3 = 54277;
    constexpr uint32 SPELL_NETHER_PROTECTION_HOLY = 54370;
    constexpr uint32 SPELL_NETHER_PROTECTION_FIRE = 54371;
    constexpr uint32 SPELL_NETHER_PROTECTION_FROST = 54372;
    constexpr uint32 SPELL_NETHER_PROTECTION_ARCANE = 54373;
    constexpr uint32 SPELL_NETHER_PROTECTION_SHADOW = 54374;
    constexpr uint32 SPELL_NETHER_PROTECTION_NATURE = 54375;
    constexpr uint32 SPELL_AFTERMATH_DAZE = 18118;
    constexpr uint32 SPELL_SHADOWFLAME_DOT = 47960;
    constexpr uint32 SPELL_PYROCLASM_R1 = 18093;
    constexpr uint32 SPELL_PYROCLASM_R2 = 63243;
    constexpr uint32 SPELL_PYROCLASM_R3 = 63244;
    constexpr uint32 SPELL_IMPROVED_SHADOW_BOLT_DEBUFF = 17800;         // ISB debuff, used unchanged
    constexpr uint32 SPELL_SOUL_LEECH_HEAL = 30294;                     // used unchanged
    constexpr uint32 SPELL_SOUL_LEECH_R1 = 30293;                       // talent 967, (0,1)
    constexpr uint32 SPELL_SOUL_LEECH_R2 = 30295;
    constexpr uint32 SPELL_SOUL_LEECH_R3 = 30296;
    constexpr uint32 SPELL_BACKLASH_R1 = 34935;                         // talent 1817, (4,0) - moved in from mage_trigger_spells.py
    constexpr uint32 SPELL_BACKLASH_R2 = 34938;
    constexpr uint32 SPELL_BACKLASH_R3 = 34939;
    constexpr uint32 SPELL_MOLTEN_SKIN_R1 = 63349;                      // talent 1887, (1,1) - moved in from rogue_trigger_spells.py
    constexpr uint32 SPELL_MOLTEN_SKIN_R2 = 63350;
    constexpr uint32 SPELL_MOLTEN_SKIN_R3 = 63351;

    // Talent ids this pass mints/repurposes (DESTRUCTION.md §2.2)
    constexpr uint32 TALENT_VOLATILITY = 965;                           // repurposed Improved Searing Pain
    constexpr uint32 TALENT_FURY_OF_THE_VOID = 1889;                    // repurposed Improved Soul Leech
    constexpr uint32 TALENT_KINDLING = 60100;                           // minted
    constexpr uint32 TALENT_HELLSTORM = 60101;                          // minted
    constexpr uint32 TALENT_HAVOC = 60102;                              // minted
    constexpr uint32 TALENT_CHAOTIC_RESONANCE = 60103;                  // minted
    constexpr uint32 TALENT_CHAOS_RIFT = 60104;                         // minted

    // creature_template 300170 "Chaos Rift" (DESTRUCTION.md §2.6, declared via stage T1's DSL
    // creature declarations, not hand-written SQL)
    constexpr uint32 NPC_CHAOS_RIFT = 300170;

    // ------------------------------------------------------------------
    // Havoc (R2, DESTRUCTION.md §7.5) - scans the caster's single-cast auras for the live Havoc
    // (200974) target. Returns nullptr when Havoc isn't up.
    // ------------------------------------------------------------------
    Unit* GetHavocTarget(Unit* caster);

    // ------------------------------------------------------------------
    // Ruin's ">75% target health" clause (PLAN §2, aura 303 MOD_DAMAGE_DONE_VERSUS_AURASTATE,
    // DESTRUCTION.md §0.1 item 14) - product of the caster's live aura-303 effects whose aura-state
    // condition `victim` currently satisfies. 1.0f when none apply.
    // ------------------------------------------------------------------
    float GetAuraStateDoneFactor(Unit const* caster, Unit const* victim, SpellInfo const* spellInfo);

    // ------------------------------------------------------------------
    // Hellstorm (C4, DESTRUCTION.md §7.4) - injects one extra Hellfire self-tick (1949) every 2 s
    // on the player's running Hellfire channel while Hellstorm (200989) is up (Flourish precedent,
    // Warlock::FirePeriodicTickNow). Owns a per-player generation counter so two starters (re-cast,
    // talent proc) never double-schedule the same channel.
    // ------------------------------------------------------------------
    void StartHellstormAcceleration(Player* player);

    // ------------------------------------------------------------------
    // Destructive Reach crit (C3, DESTRUCTION.md §7.9) - AllSpellScript::CanPrepare branch (in
    // warlock_hooks.cpp, alongside Affliction's instant-cast grant): when the cast target is more
    // than 20 yd from `player`, grants the 1-charge crit helper (200991). Judged against the cast
    // target only; AoE secondary targets don't re-check distance (accepted, C3 RESOLVED).
    // ------------------------------------------------------------------
    void ApplyDestructiveReachCrit(Player* player, Spell* spell);

    // ------------------------------------------------------------------
    // Chaos Bolt cooldown reduction (A8, DESTRUCTION.md §2.6) - real seconds off Chaos Bolt's
    // (50796) remaining cooldown. `ModifySpellCooldown(50796, -ms)`; a no-op when Chaos Bolt isn't
    // currently cooling down (Player.cpp:11391).
    // ------------------------------------------------------------------
    void ReduceChaosBoltCooldown(Player* player, uint32 ms);
}

#endif
