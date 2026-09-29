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
#include "ObjectGuid.h"
#include "SharedDefines.h"
#include "UnitDefines.h"
#include <array>
#include <deque>
#include <functional>
#include <initializer_list>
#include <unordered_map>
#include <vector>

class Aura;
class AuraEffect;
class Creature;
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
    // 200720 (the old separate Bane of Agony stack tracker) is retired - 980 stacks itself.
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
    constexpr uint32 SPELL_SOUL_HARVEST_PET = 200737; // pet half of Soul Harvest (keeps 200736 self-cast only)
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

    // Live stack count of the caster's SPELL_BANE_OF_AGONY (980, a stacking aura) on `target`;
    // 0 when absent.
    uint8 GetAgonyStacks(Unit const* target, ObjectGuid casterGuid);

    // Adds `count` stacks to the caster's 980 on `target` (no-op without it), capped by
    // GetAgonyStackCap.
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
    // SPELL_SHADOWBURN (= 29341) already declared above (Affliction WP-0) - do not redeclare
    // (found by Demonology's WP-0: this duplicate constexpr definition in the same namespace is a
    // hard compile error, undetected until now because neither pass has built yet).
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

    // ------------------------------------------------------------------
    // Demonology pass (S3) additions - DEMONOLOGY.md §2/§3.4/§6/§7/§14. Append-only: WP-B fills in
    // the bodies below and may add further Demonology-local helpers, but must not rename or change
    // the signature of anything already declared without flagging it back (Affliction/Destruction
    // WP-B precedent above).
    // ------------------------------------------------------------------

    // New spells this pass mints (DEMONOLOGY.md §2.1, spell block 200820-200959)
    constexpr uint32 SPELL_HAND_OF_GULDAN = 200820;                     // baseline, learn 10
    constexpr uint32 SPELL_HAND_OF_GULDAN_SPLASH = 200821;              // Metamorphosis only, no procs
    constexpr uint32 SPELL_SUMMON_WILD_IMP = 200822;                    // triggered SUMMON 300150
    constexpr uint32 SPELL_SUMMON_IMP_GANG_BOSS = 200823;               // triggered SUMMON 300151
    constexpr uint32 SPELL_FEL_FIREBOLT = 200824;                       // Wild Imp AI cast
    constexpr uint32 SPELL_BANE_OF_DOOM = 200825;                       // baseline, learn 20, bane slot
    constexpr uint32 SPELL_UNENDING_RESOLVE = 200826;                   // baseline, learn 25
    constexpr uint32 SPELL_IMPLOSION = 200827;                          // talent 1281 rank spell, castable
    constexpr uint32 SPELL_IMPLOSION_EXPLOSION = 200828;                // cast by each imp
    constexpr uint32 SPELL_CALL_DREADSTALKERS = 200829;                 // talent 60083 rank spell, castable
    constexpr uint32 SPELL_DREADSTALKER_BITE = 200830;                  // Dreadstalker AI cast
    constexpr uint32 SPELL_SUMMON_DOOMGUARD = 200831;                   // learned by Legion's Call
    constexpr uint32 SPELL_DOOM_BOLT = 200832;                          // Doomguard AI cast
    constexpr uint32 SPELL_SUMMON_INFERNAL = 200833;                    // learned by Legion's Call
    constexpr uint32 SPELL_INFERNAL_IMMOLATION = 200834;                // Infernal AI pulse
    constexpr uint32 SPELL_DARK_APOTHEOSIS = 200835;                    // form 23 toggle
    constexpr uint32 SPELL_DARK_APOTHEOSIS_PASSIVE = 200836;            // hidden, linked from 200835
    constexpr uint32 SPELL_METAMORPHOSIS_PASSIVE = 200837;              // hidden, linked from 47241
    constexpr uint32 SPELL_DEMONIC_BULWARK_FORM = 200838;               // hidden, linked from 47241 and 200835
    constexpr uint32 SPELL_DEMONIC_TAUNT = 200839;                      // Dark Apotheosis only
    constexpr uint32 SPELL_DEMONIC_POTENCY = 200840;                    // hidden aura on every demon
    constexpr uint32 SPELL_IMP_GANG_BOSS_AURA = 200841;                 // hidden +50% on 300151
    constexpr uint32 SPELL_FEL_CRUELTY_BUFF = 200842;                   // warlock buff, feeds Potency
    constexpr uint32 SPELL_GRIMOIRE_OF_SYNERGY_BUFF = 200843;           // warlock buff, +10% spell dmg
    constexpr uint32 SPELL_GRIMOIRE_OF_SYNERGY_PET_AURA = 200844;       // hidden proc aura on the Felguard
    constexpr uint32 SPELL_DEMONIC_PACT_EMPOWER = 200845;               // warlock buff, +5% spell dmg
    constexpr uint32 SPELL_IMPROVED_SOUL_FIRE_SHIELD = 200846;          // absorb shield, 12 s
    constexpr uint32 SPELL_DEMONIC_BULWARK_DEBUFF = 200847;             // Immolation Aura debuff, 3 s
    constexpr uint32 SPELL_FEL_IMMOLATION_HEAL = 200848;                // self heal
    constexpr uint32 SPELL_IMPROVED_HEALTHSTONE_SP = 200849;            // SP buff, 20 s
    constexpr uint32 SPELL_FEL_VITALITY_DEMON = 200850;                 // hidden on main/enslaved demon + Dreadstalkers
    constexpr uint32 SPELL_FEL_BOND_AURA = 200851;                      // hidden, on warlock and demon
    constexpr uint32 SPELL_BRUTALITY_VOIDWALKER = 200852;               // hidden, Voidwalker HP%/armor%
    constexpr uint32 SPELL_DEMONIC_POWER_IMP_HASTE = 200853;            // hidden self-buff on a Wild Imp
    constexpr uint32 SPELL_DEMONIC_VERSATILITY = 200854;                // hidden aura on every demon
    // 200855-200859 spare

    // Talent rank spells (200860-200905, DEMONOLOGY.md §2.1/§6)
    constexpr uint32 SPELL_DEMONIC_RESOLVE_R1 = 200860;                 // talent 1224 (repurposed), (0,1)
    constexpr uint32 SPELL_DEMONIC_RESOLVE_R2 = 200861;
    constexpr uint32 SPELL_DEMONIC_RESOLVE_R3 = 200862;
    constexpr uint32 SPELL_DARK_APOTHEOSIS_LEARNER = 200863;            // talent 1282 (repurposed), (0,3)
    constexpr uint32 SPELL_DARK_APOTHEOSIS_DEMON_ABILITIES = 200864;    // learn carrier: 54785, 200839, 59671
    constexpr uint32 SPELL_IMPROVED_HAND_OF_GULDAN_R1 = 200865;         // talent 60080 (minted), (1,2)
    constexpr uint32 SPELL_IMPROVED_HAND_OF_GULDAN_R2 = 200866;
    constexpr uint32 SPELL_IMP_GANG_BOSS_R1 = 200867;                   // talent 1243 (repurposed), (2,0)
    constexpr uint32 SPELL_IMP_GANG_BOSS_R2 = 200868;
    constexpr uint32 SPELL_IMPENDING_DOOM_R1 = 200869;                  // talent 1226 (repurposed in S1), (2,2)
    constexpr uint32 SPELL_IMPENDING_DOOM_R2 = 200870;                  // carries the capstone proc
    constexpr uint32 SPELL_LEGION_STRENGTH_R1 = 200871;                 // talent 60082 (minted), (3,0)
    constexpr uint32 SPELL_LEGION_STRENGTH_R2 = 200872;
    constexpr uint32 SPELL_LEGION_STRENGTH_R3 = 200873;
    constexpr uint32 SPELL_FEL_IMMOLATION_R1 = 200874;                  // talent 60084 (minted), (4,3)
    constexpr uint32 SPELL_FEL_IMMOLATION_R2 = 200875;
    constexpr uint32 SPELL_FEL_IMMOLATION_R3 = 200876;                  // capstone marker
    constexpr uint32 SPELL_FEL_BOND_R1 = 200877;                        // talent 1244 (replaces Master Demonologist), (5,1)
    constexpr uint32 SPELL_FEL_BOND_R2 = 200878;
    constexpr uint32 SPELL_FEL_BOND_R3 = 200879;
    constexpr uint32 SPELL_GRIMOIRE_OF_SYNERGY_R1 = 200880;             // talent 60085 (minted), (5,2)
    constexpr uint32 SPELL_GRIMOIRE_OF_SYNERGY_R2 = 200881;
    constexpr uint32 SPELL_GRIMOIRE_OF_SYNERGY_R3 = 200882;
    constexpr uint32 SPELL_DEMONIC_CALLING_R1 = 200883;                 // talent 60086 (minted), (6,0)
    constexpr uint32 SPELL_DEMONIC_CALLING_R2 = 200884;
    constexpr uint32 SPELL_DEMONIC_CALLING_R3 = 200885;
    constexpr uint32 SPELL_IMPROVED_SOUL_FIRE_R1 = 200886;              // talent 60087 (minted), (6,2)
    constexpr uint32 SPELL_IMPROVED_SOUL_FIRE_R2 = 200887;
    constexpr uint32 SPELL_IMPROVED_SOUL_FIRE_R3 = 200888;
    constexpr uint32 SPELL_DECIMATION_R3 = 200889;                      // talent 2261, (7,0) - r1/r2 stay 63156/63158
    constexpr uint32 SPELL_FEL_CRUELTY_R1 = 200890;                     // talent 60088 (minted), (7,2)
    constexpr uint32 SPELL_FEL_CRUELTY_R2 = 200891;
    constexpr uint32 SPELL_FEL_CRUELTY_R3 = 200892;                     // carries the capstone proc
    constexpr uint32 SPELL_DEMONIC_BULWARK_R1 = 200893;                 // talent 60089 (minted), (7,3)
    constexpr uint32 SPELL_DEMONIC_BULWARK_R2 = 200894;
    constexpr uint32 SPELL_DEMONIC_BULWARK_R3 = 200895;
    constexpr uint32 SPELL_IMPROVED_DEMONIC_TACTICS_R1 = 200896;        // talent 1882 - replaces 54347-9
    constexpr uint32 SPELL_IMPROVED_DEMONIC_TACTICS_R2 = 200897;
    constexpr uint32 SPELL_IMPROVED_DEMONIC_TACTICS_R3 = 200898;
    constexpr uint32 SPELL_FEL_REPRISAL_R1 = 200899;                    // talent 60090 (minted), (8,3)
    constexpr uint32 SPELL_FEL_REPRISAL_R2 = 200900;
    constexpr uint32 SPELL_FEL_REPRISAL_R3 = 200901;
    constexpr uint32 SPELL_DEMONIC_FORM_R1 = 200902;                    // talent 60091 (minted), (9,1)
    constexpr uint32 SPELL_DEMONIC_FORM_R2 = 200903;
    constexpr uint32 SPELL_DEMONIC_FORM_R3 = 200904;
    constexpr uint32 SPELL_LEGIONS_CALL = 200905;                       // talent 60092 (minted), (10,1) learner
    // 200906-200959 spare

    // Stock ids this pass reuses (retuned) or references (DEMONOLOGY.md §2.1/§4/§9)
    constexpr uint32 SPELL_METAMORPHOSIS = 47241;
    constexpr uint32 SPELL_METAMORPHOSIS_STUN_SNARE = 54817;
    constexpr uint32 SPELL_METAMORPHOSIS_SPELL_MASK_PASSIVE = 54879;
    constexpr uint32 SPELL_METAMORPHOSIS_TALENT_RANK = 59672;           // talent 1886, (6,1)
    constexpr uint32 SPELL_METAMORPHOSIS_LEARN_CARRIER = 59673;         // learns 50589 + 54786
    constexpr uint32 SPELL_IMMOLATION_AURA = 50589;
    constexpr uint32 SPELL_IMMOLATION_AURA_TICK = 50590;
    constexpr uint32 SPELL_CHALLENGING_HOWL = 59671;                    // Dark Apotheosis only
    constexpr uint32 SPELL_DEMON_CHARGE = 54785;                        // Dark Apotheosis only
    constexpr uint32 SPELL_DEMON_CHARGE_STUN = 60995;
    constexpr uint32 SPELL_DEMONIC_LEAP_SPELL = 54786;                  // "Demon Leap" retuned (B11)
    constexpr uint32 SPELL_MOLTEN_CORE = 71165;                         // the only Molten Core buff from now on
    constexpr uint32 SPELL_DECIMATION_BUFF = 63165;
    constexpr uint32 SPELL_DEMONIC_PACT_RAID = 48090;
    constexpr uint32 SPELL_DEMONIC_EMPOWERMENT_VOIDWALKER = 54443;      // unedited, stock 20 s
    constexpr uint32 SPELL_DEMONIC_EMPOWERMENT_FELGUARD = 54508;        // unedited, stock 15 s
    constexpr uint32 SPELL_DEMONIC_EMPOWERMENT = 47193;
    constexpr uint32 SPELL_SOUL_LINK = 19028;                           // talent -> baseline at 20
    constexpr uint32 SPELL_SOUL_LINK_SPLIT = 25228;
    constexpr uint32 SPELL_CURSE_OF_DOOM = 603;                         // removed, untrained
    constexpr uint32 SPELL_DEMONIC_KNOWLEDGE_INT = 35696;               // stock spell_pet_auras target
    constexpr uint32 SPELL_ENSLAVE_DEMON = 1098;
    constexpr uint32 SPELL_SACRIFICE = 7812;                            // Voidwalker Sacrifice absorb
    constexpr uint32 SPELL_DEMONIC_PACT_PET_PROC_R1 = 53646;
    constexpr uint32 SPELL_DEMONIC_PACT_PET_PROC_R2 = 54909;
    constexpr uint32 SPELL_INFERNO = 1122;                              // replaced by Legion's Call
    constexpr uint32 SPELL_RITUAL_OF_DOOM = 18540;                      // replaced by Legion's Call

    // Talent ids this pass mints/repurposes (DEMONOLOGY.md §2.2)
    constexpr uint32 TALENT_DEMONIC_RESOLVE = 1224;                     // repurposed Improved Health Funnel
    constexpr uint32 TALENT_IMP_GANG_BOSS = 1243;                       // repurposed Improved Succubus
    constexpr uint32 TALENT_DARK_APOTHEOSIS = 1282;                     // repurposed Soul Link
    constexpr uint32 TALENT_IMPLOSION = 1281;                           // repurposed Mana Feed
    constexpr uint32 TALENT_FEL_BOND = 1244;                            // replaces Master Demonologist
    constexpr uint32 TALENT_IMPROVED_HAND_OF_GULDAN = 60080;            // minted
    // TALENT_ROW_1226_IMPENDING_DOOM (= 1226) already declared above (Affliction WP-0)
    constexpr uint32 TALENT_LEGION_STRENGTH = 60082;                    // minted
    constexpr uint32 TALENT_CALL_DREADSTALKERS = 60083;                 // minted
    constexpr uint32 TALENT_FEL_IMMOLATION = 60084;                     // minted
    constexpr uint32 TALENT_GRIMOIRE_OF_SYNERGY = 60085;                // minted
    constexpr uint32 TALENT_DEMONIC_CALLING = 60086;                    // minted
    constexpr uint32 TALENT_IMPROVED_SOUL_FIRE = 60087;                 // minted
    constexpr uint32 TALENT_FEL_CRUELTY = 60088;                        // minted
    constexpr uint32 TALENT_DEMONIC_BULWARK = 60089;                    // minted
    constexpr uint32 TALENT_FEL_REPRISAL = 60090;                       // minted
    constexpr uint32 TALENT_DEMONIC_FORM = 60091;                       // minted
    constexpr uint32 TALENT_LEGIONS_CALL = 60092;                       // minted
    constexpr uint32 TALENT_METAMORPHOSIS = 1886;
    constexpr uint32 TALENT_MOLTEN_CORE = 1283;
    constexpr uint32 TALENT_DEMONIC_RESILIENCE = 1680;
    constexpr uint32 TALENT_NEMESIS = 1884;
    constexpr uint32 TALENT_DEMONIC_PACT = 1885;
    constexpr uint32 TALENT_IMPROVED_DEMONIC_TACTICS = 1882;
    constexpr uint32 TALENT_UNHOLY_POWER = 1262;
    constexpr uint32 TALENT_DEMONIC_TACTICS = 1673;
    constexpr uint32 TALENT_FEL_VITALITY = 1242;
    constexpr uint32 TALENT_DECIMATION = 2261;
    constexpr uint32 TALENT_DEMONIC_BRUTALITY = 1225;

    // Rank arrays for C++ (DEMONOLOGY.md §6 "Rank arrays for C++") - talent id != spell id; every
    // live talent read goes through the rank *spell* id, never the talent id.
    constexpr std::array<uint32, 3> RANKS_IMPROVED_IMP = { 18694, 18695, 18696 };
    constexpr std::array<uint32, 2> RANKS_IMPROVED_HEALTHSTONE = { 18692, 18693 };
    constexpr std::array<uint32, 2> RANKS_MASTER_SUMMONER = { 18709, 18710 };
    constexpr std::array<uint32, 2> RANKS_IMP_GANG_BOSS = { 200867, 200868 };
    constexpr std::array<uint32, 2> RANKS_IMPENDING_DOOM = { 200869, 200870 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_BRUTALITY = { 18705, 18706, 18707 };
    constexpr std::array<uint32, 3> RANKS_LEGION_STRENGTH = { 200871, 200872, 200873 };
    constexpr std::array<uint32, 3> RANKS_UNHOLY_POWER = { 18769, 18770, 18771 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_AEGIS = { 30143, 30144, 30145 };
    constexpr std::array<uint32, 3> RANKS_FEL_VITALITY = { 18731, 18743, 18744 };
    constexpr std::array<uint32, 3> RANKS_FEL_IMMOLATION = { 200874, 200875, 200876 };
    constexpr std::array<uint32, 3> RANKS_MOLTEN_CORE = { 47245, 47246, 47247 };
    constexpr std::array<uint32, 3> RANKS_FEL_BOND = { 200877, 200878, 200879 };
    constexpr std::array<uint32, 3> RANKS_GRIMOIRE_OF_SYNERGY = { 200880, 200881, 200882 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_RESILIENCE = { 30319, 30320, 30321 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_CALLING = { 200883, 200884, 200885 };
    constexpr std::array<uint32, 3> RANKS_IMPROVED_SOUL_FIRE = { 200886, 200887, 200888 };
    constexpr std::array<uint32, 3> RANKS_DECIMATION = { 63156, 63158, 200889 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_TACTICS = { 30242, 30245, 30246 };
    constexpr std::array<uint32, 3> RANKS_FEL_CRUELTY = { 200890, 200891, 200892 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_BULWARK = { 200893, 200894, 200895 };
    constexpr std::array<uint32, 3> RANKS_IMPROVED_DEMONIC_TACTICS = { 200896, 200897, 200898 };
    constexpr std::array<uint32, 3> RANKS_NEMESIS = { 63117, 63121, 63123 };
    constexpr std::array<uint32, 3> RANKS_FEL_REPRISAL = { 200899, 200900, 200901 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_FORM = { 200902, 200903, 200904 };
    constexpr std::array<uint32, 3> RANKS_DEMONIC_PACT = { 47236, 47237, 47238 };

    // Demonic Resilience's two values with no free effect slot (DEMONOLOGY.md §6 (5,3)): demon
    // damage-taken reduction and Soul Link share bonus, by rank (index 0 = rank 1).
    constexpr std::array<uint8, 3> DEMONIC_RESILIENCE_DEMON_DR = { 5, 10, 15 };
    constexpr std::array<uint8, 3> DEMONIC_RESILIENCE_SOUL_LINK = { 2, 4, 6 };

    // creature_template 300150-300154 (DEMONOLOGY.md §2.6, declared via stage T1's DSL creature
    // declarations, not hand-written SQL)
    constexpr uint32 NPC_WILD_IMP = 300150;
    constexpr uint32 NPC_IMP_GANG_BOSS = 300151;
    constexpr uint32 NPC_DREADSTALKER = 300152;
    constexpr uint32 NPC_DOOMGUARD_GUARDIAN = 300153;
    constexpr uint32 NPC_INFERNAL_GUARDIAN = 300154;

    // Wild Imp tuning (DEMONOLOGY.md §3.4)
    constexpr uint8 WILD_IMP_CAP = 15;
    constexpr int32 WILD_IMP_ENERGY = 100;
    constexpr int32 IMP_GANG_BOSS_ENERGY = 150;
    constexpr int32 FEL_FIREBOLT_ENERGY_COST = 20;

    enum class WildImpDespawnReason : uint8
    {
        Energy,
        Implosion,
        Sacrifice,
        Timeout
    };

    enum class DemonKind : uint8
    {
        None,
        Imp,
        Voidwalker,
        Succubus,
        Felhunter,
        Felguard,
        Enslaved,
        WildImp,
        ImpGangBoss,
        Dreadstalker,
        Doomguard,
        Infernal
    };

    // Form 23 = the core enum value FORM_DARK_APOTHEOSIS (UnitDefines.h) - no local Warlock-scoped
    // constant (it would shadow the core enum inside this namespace).
    bool IsInMetamorphosis(Unit const* unit);                            // GetShapeshiftForm() == FORM_METAMORPHOSIS
    bool IsInDarkApotheosis(Unit const* unit);                           // GetShapeshiftForm() == FORM_DARK_APOTHEOSIS
    DemonKind GetDemonKind(Unit const* demon, Player const* owner);

    // Wild Imps (Priest tentacle pattern: m_Controlled scan by entry, PriestMechanics.cpp:708-722).
    // Both skip a "departing" imp (AI GetData(DATA_WILD_IMP_DEPARTING) == 1) - a despawning imp
    // stays in m_Controlled until its delayed UnSummon / the map's remove list runs (§7.2).
    std::vector<Creature*> GetWildImps(Player* owner);                   // copy - DespawnOrUnsummon mutates m_Controlled
    uint32 CountWildImps(Player const* owner);                           // 300150 + 300151, departing excluded
    bool TrySummonWildImp(Player* owner, Unit* target, bool gangBoss);   // cap, pending target, triggered cast
    void OnWildImpDespawn(Player* owner, WildImpDespawnReason reason);   // Molten Core roll (Energy/Implosion)
    void GrantMoltenCore(Player* owner, uint8 stacks);                   // CastSpell(owner, 71165, true) x stacks

    // Summon hand-off (set just before a synchronous triggered/instant summon, read in IsSummonedBy)
    struct PendingSummon
    {
        ObjectGuid target;
        uint32 pairToken = 0;
    };
    void SetPendingSummon(Player* owner, PendingSummon const& pending);
    PendingSummon GetPendingSummon(Player const* owner);
    void ClearPendingSummon(Player* owner);
    uint32 NextDreadstalkerPairToken(Player* owner);
    void OnDreadstalkerDeparted(Player* owner, uint32 pairToken);        // 1 Molten Core per token

    // Guardians (B21): the LIVE L0 base + round(coef x owner SP of the spell's school) - i.e.
    // Effects[0].BasePoints + (Effects[0].DieSides ? 1 : 0) + round(coef x SP) - SetSpellValue's
    // CalcBaseValue takes the 1 back off (SHARED §4 custom-base-points convention).
    int32 ComputeGuardianBasePoints(Unit const* guardian, uint32 spellId, float spCoefficient);
    Unit* SelectGuardianTarget(Creature* guardian, Player* owner, ObjectGuid preferred);   // §7.4

    // Demonic Potency and the other hidden demon auras (§7.1)
    int32 ComputeDemonAuraAmount(Player const* owner, Unit const* target, uint32 spellId, uint8 effIndex);
    void RefreshDemonAuras(Player* owner, Unit* demon);                  // add/remove 200840/200844/200850/200851/200852/200854
    void RefreshDemonicPotency(Player* owner);                           // RecalculateAmount on every demon's 200840 + 200854

    void SyncLegionsCall(Player* player, bool losingTalent = false);     // §7.11
    void ClearDemonologyPlayerState(ObjectGuid playerGuid);              // OnPlayerLogout

    // ------------------------------------------------------------------
    // WP-B addition, flagged in the final report (not part of §3.4's original frozen block): Wild
    // Imp guardian AI action/data ids. DEMONOLOGY-WP-BRIEF.md asked for these as enums "local to
    // pet_warlock_rework.cpp", but GetWildImps/CountWildImps/OnWildImpDespawn above (this same
    // frozen header, WP-0's own comment) already name DATA_WILD_IMP_DEPARTING as something they
    // read via the AI's GetData - and Implosion (spell_warlock_demonology.cpp) drives the AI's
    // DoAction/SetGUID, while Demonic Empowerment reads GetData(DATA_WILD_IMP_ENERGY) - three
    // separate translation units that all need the same numeric id. A same-file-only enum can't
    // satisfy that, so these four constants live here instead; every other AI action/event/data id
    // (EVENT_*, POINT_WILD_IMP_IMPLODE, the Dreadstalker/Doomguard/Infernal scheduling ids) stays a
    // local enum inside pet_warlock_rework.cpp as the brief asked, since nothing outside that file
    // touches them.
    // ------------------------------------------------------------------
    enum WildImpAIAction : int32
    {
        ACTION_WILD_IMP_IMPLODE = 1,
        ACTION_WILD_IMP_SACRIFICE = 2
    };

    enum WildImpAIData : uint32
    {
        DATA_WILD_IMP_ENERGY = 1,
        DATA_WILD_IMP_DEPARTING = 2
    };

    constexpr int32 GUID_SLOT_IMPLODE_TARGET = 1;
}

#endif
