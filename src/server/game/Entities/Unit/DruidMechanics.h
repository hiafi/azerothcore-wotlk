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

#ifndef __DRUIDMECHANICS_H
#define __DRUIDMECHANICS_H

#include "Define.h"
#include "SharedDefines.h"
#include "UnitDefines.h"
#include <functional>
#include <initializer_list>

class Aura;
class AuraEffect;
class Player;
class Spell;
class SpellInfo;
class Unit;
enum DamageEffectType : uint8;

/*
 * Druid-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors PriestMechanics.h /
 * MageMechanics.h's shape. Created by the Balance pass's WP-0
 * (.agents/plans/druid-rework/druid-rework.PLAN.md §5.1/§6 item 5); Resto and Feral extend it with
 * their own functions (PLAN §6, "Resto adds"/"Feral adds"). See
 * .agents/plans/druid-rework/druid-rework.CORE-AUDIT.md for why this file's surface is as small as
 * it is - almost everything else is data, a SpellScript/AuraScript, or an existing ScriptMgr hook
 * in src/server/scripts/Spells/druid_hooks.cpp, not a core call site here.
 *
 * WP-0 declares this skeleton's signatures (constants + the functions CORE-AUDIT/BALANCE already
 * pin down); WP-B (spell_druid_balance.cpp / DruidMechanics.cpp) fills in the bodies and may add
 * further mechanic-local helpers as it implements each talent row - see
 * druid-rework.BALANCE.md §6/§7/§10 for the per-talent mapping.
 */
namespace Druid
{
    // Spell ids shared across translation units (Balance pass) - defined once here so
    // spell_druid_balance.cpp, druid_hooks.cpp and this file's own .cpp can't drift from each
    // other. BALANCE.md §2's full ID map (spell block 200320-200419); repurposed talent ids and
    // referenced stock ids are named where a function below actually needs them.

    // Talent-rank passives
    constexpr uint32 SPELL_CELESTIAL_ATTUNEMENT_R1 = 200320;
    constexpr uint32 SPELL_CELESTIAL_ATTUNEMENT_R2 = 200321;
    constexpr uint32 SPELL_CELESTIAL_ATTUNEMENT_R3 = 200322;
    constexpr uint32 SPELL_IMPROVED_MOONFIRE_R3 = 200323;               // carries the capstone proc
    constexpr uint32 SPELL_NATURES_SPLENDOR_R1 = 200324;
    constexpr uint32 SPELL_NATURES_SPLENDOR_R2 = 200325;
    constexpr uint32 SPELL_NATURES_SPLENDOR_R3 = 200326;                // linked to stock 57865
    constexpr uint32 SPELL_STARWEAVER_R1 = 200327;
    constexpr uint32 SPELL_STARWEAVER_R2 = 200328;
    constexpr uint32 SPELL_STARWEAVER_R3 = 200329;
    constexpr uint32 SPELL_SWARMING_ROT_R1 = 200330;
    constexpr uint32 SPELL_SWARMING_ROT_R2 = 200331;
    constexpr uint32 SPELL_SWARMING_ROT_R3 = 200332;                    // carries the capstone proc

    // Baseline / talent-granted castables
    constexpr uint32 SPELL_STARSURGE = 200333;
    constexpr uint32 SPELL_MASS_ENTANGLEMENT = 200334;
    constexpr uint32 SPELL_SOLAR_BEAM = 200335;
    constexpr uint32 SPELL_FURY_OF_ELUNE = 200336;

    // Triggered / hidden
    constexpr uint32 SPELL_STARFIRE_CLEAVE = 200337;
    constexpr uint32 SPELL_FURY_OF_ELUNE_BEAM = 200338;
    constexpr uint32 SPELL_FURY_OF_ELUNE_SPLASH = 200339;
    constexpr uint32 SPELL_CELESTIAL_ALIGNMENT = 200340;
    constexpr uint32 SPELL_LUNAR_FLARE = 200341;                        // Improved Moonfire capstone hit
    constexpr uint32 SPELL_SHOOTING_STARS = 200342;                     // Celestial Focus capstone buff
    constexpr uint32 SPELL_VENGEFUL_SOUL = 200343;                      // Vengeance r3 capstone buff
    constexpr uint32 SPELL_ASTRAL_SURGE_1 = 200344;
    constexpr uint32 SPELL_ASTRAL_SURGE_2 = 200345;
    constexpr uint32 SPELL_ASTRAL_SURGE_3 = 200346;
    constexpr uint32 SPELL_BALANCE_OF_POWER_BUFF = 200347;
    constexpr uint32 SPELL_MOONGLOW_BUFF_R1 = 200348;
    constexpr uint32 SPELL_MOONGLOW_BUFF_R2 = 200349;
    constexpr uint32 SPELL_MOONGLOW_BUFF_R3 = 200350;
    constexpr uint32 SPELL_GALE_WINDS_STACK = 200351;                   // Hurricane ramp buff
    constexpr uint32 SPELL_INSECT_SWARM_COPY = 200352;                  // Swarming Rot's spread copy
    constexpr uint32 SPELL_BRAMBLES_SILENCE = 200353;

    // Improved Moonfire's Astral crit - hidden linked passives (CORE-AUDIT row 5)
    constexpr uint32 SPELL_ASTRAL_CRIT_R1 = 200354;
    constexpr uint32 SPELL_ASTRAL_CRIT_R2 = 200355;
    constexpr uint32 SPELL_ASTRAL_CRIT_R3 = 200356;

    // Repurposed talent ids (talent_dbc id, not a spell id - see PLAN §4.2)
    constexpr uint32 TALENT_CELESTIAL_ATTUNEMENT = 1785;                // was Improved Faerie Fire
    constexpr uint32 TALENT_FURY_OF_ELUNE = 1923;                       // was Typhoon
    constexpr uint32 TALENT_MOONFURY_R3 = 16899;                        // rank spell id - Astral Surge capstone
    constexpr uint32 TALENT_STARWEAVER_R3 = 200329;                     // Starweaver capstone rank
    constexpr uint32 TALENT_BALANCE_OF_POWER_R1 = 33592;
    constexpr uint32 TALENT_BALANCE_OF_POWER_R2 = 33596;
    constexpr uint32 TALENT_VENGEANCE_R3 = 16911;

    // Referenced stock spells
    constexpr uint32 SPELL_WRATH = 5176;
    constexpr uint32 SPELL_STARFIRE = 2912;
    constexpr uint32 SPELL_MOONFIRE = 8921;
    constexpr uint32 SPELL_INSECT_SWARM = 5570;
    constexpr uint32 SPELL_STARFALL = 48505;
    constexpr uint32 SPELL_TYPHOON = 50516;                             // baseline at 36 (BALANCE §4)
    constexpr uint32 SPELL_HURRICANE = 16914;
    constexpr uint32 SPELL_HURRICANE_TICK = 42231;
    constexpr uint32 SPELL_INNERVATE = 29166;
    constexpr uint32 SPELL_MOONKIN_FORM_PASSIVE_24905 = 24905;
    constexpr uint32 SPELL_ECLIPSE_R1 = 48516;
    constexpr uint32 SPELL_ECLIPSE_R2 = 48521;
    constexpr uint32 SPELL_ECLIPSE_R3 = 48525;                          // Mastery gate (3/3 Eclipse)
    constexpr uint32 SPELL_ECLIPSE_SOLAR = 48517;
    constexpr uint32 SPELL_ECLIPSE_LUNAR = 48518;
    constexpr uint32 SPELL_NATURES_GRACE_BUFF = 16886;
    constexpr uint32 SPELL_BARKSKIN = 22812;

    // Repurposed/rank talent ids referenced only by this pass's scripts (not already declared
    // above as part of the shared cross-file block).
    constexpr uint32 TALENT_WRATH_OF_CENARIUS_R3 = 33605;
    constexpr uint32 TALENT_GALE_WINDS_R2 = 48514;
    constexpr uint32 TALENT_DREAMSTATE_R3 = 33956;

    // Unit::SpellPctDamageModsDone's druid hook (CORE-AUDIT row 1) - the only done-damage hook
    // that runs at DoT snapshot time as well as on direct hits, so it is the sole call site for
    // Eclipse, Celestial Alignment, Eclipse Mastery and Improved Insect Swarm's conditional bonus.
    // `caster`/`victim` may be any class; the body gates on `caster` being a druid player before
    // doing anything (school-based, so other classes' Nature/Arcane spells reach the Eclipse
    // branch too - BALANCE §7).
    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, DamageEffectType damagetype,
                                 float& doneTotalMod);

    // Every druid "reduce the remaining cooldown of spellId by ms" effect goes through this one
    // helper (PLAN §3.9): clamps the reduction so Barkskin (22812) never drops below its floor
    // (Feral's 30 s floor, added when the Feral pass lands), then calls
    // `player->ModifySpellCooldown(spellId, -int32(ms))` - PLAN A8 made that client-visible.
    // Balance's callers: Starweaver (200329's capstone on Starsurge), Wrath of Cenarius (33605's
    // capstone on Solar Beam), Fury of Elune (halves the running Starsurge cooldown on cast).
    void ReduceSpellCooldown(Player* player, uint32 spellId, uint32 ms);

    // Moonfury r3 capstone (16899): "abilities have a chance to grant a stacking buff that
    // increases spell power" - BALANCE §7 "Astral Surge (Moonfury capstone)". Walks slots
    // {SPELL_ASTRAL_SURGE_1, _2, _3} in order; the first one `caster` lacks is cast; if all three
    // are up, the one with the lowest remaining duration is refreshed (overwrite the oldest).
    void ApplyAstralSurge(Unit* caster);

    // Owlkin Frenzy's own-cast branch and Moonkin Form's mana-on-cast proc both need "was this a
    // direct damaging spell" (BALANCE §7 "One roll per cast"): true for a SCHOOL_DAMAGE effect
    // (Wrath, Starfire, Moonfire, Starsurge) or Typhoon (50516, whose damage sits on a triggered
    // missile). A pure DoT (Insect Swarm) or channel (Hurricane) returns false.
    bool IsDirectDamageCast(SpellInfo const* spellInfo);

    // ---------------------------------------------------------------------------------------
    // Resto pass (.agents/plans/druid-rework/druid-rework.RESTO.md §9/§10, WP-0 item 5). WP-0
    // declares the constants and function signatures below so WP-A (data) and WP-B (C++ bodies +
    // script call sites) can run in parallel; WP-B fills in every body in DruidMechanics.cpp and
    // wires the call sites listed in each function's comment. RESTO §0.2 (PLAN A2 kept - server
    // stays multiplicative): every "% healing bonus" below is a PLAIN multiplier applied with
    // `AddPct`, never an additive-bucket rescale - the older §5 bucket design in RESTO.md is
    // superseded, do not build `GetBucketRescale`/`GetAdditiveSpellModPct`.
    // ---------------------------------------------------------------------------------------

    // Baseline / new castables (RESTO §2.1)
    constexpr uint32 SPELL_BLOOM = 200560;
    constexpr uint32 SPELL_BLOOM_JUMP = 200561;
    constexpr uint32 SPELL_CENARION_WARD = 200562;
    constexpr uint32 SPELL_CENARION_WARD_HEAL = 200563;
    constexpr uint32 SPELL_FLOURISH = 200564;
    constexpr uint32 SPELL_FLOURISH_BUFF = 200565;
    constexpr uint32 SPELL_NATURAL_ALACRITY_HEALING_BUFF = 200566;
    constexpr uint32 SPELL_CULTIVATION = 200567;
    constexpr uint32 SPELL_GERMINATION = 200568;             // second-copy Rejuvenation; shares 774's family bit
    constexpr uint32 SPELL_YSERAS_GIFT_HEAL = 200569;
    constexpr uint32 SPELL_PROLIFERATION_BUFF = 200570;
    constexpr uint32 SPELL_LIVING_SPIRIT_STAT = 200571;
    constexpr uint32 SPELL_CLEARCASTING_OMEN_CAPSTONE = 200572; // Omen r3's Clearcasting variant
    constexpr uint32 SPELL_NATURAL_SHAPESHIFTER_HEALING_BUFF = 200573;
    constexpr uint32 SPELL_TREE_OF_LIFE_REJUV_HEAL = 200574;
    constexpr uint32 SPELL_REVITALIZE_MANA = 200575;
    constexpr uint32 SPELL_TRANQUIL_FOCUS = 200576;          // Nature's Focus capstone buff

    // Talent rank ids referenced by a script/hook (RESTO §8's "C" rows only - "D" rows are pure
    // data and never touched from C++). Named `SPELL_<TALENT>_R<n>` to match the WP-B brief.
    constexpr uint32 SPELL_NATURES_RESILIENCE_R1 = 200577;
    constexpr uint32 SPELL_NATURES_RESILIENCE_R2 = 200578;
    constexpr uint32 SPELL_NATURES_RESILIENCE_R3 = 200579;
    constexpr uint32 SPELL_NATURES_MENDING_R1 = 200580;
    constexpr uint32 SPELL_NATURES_MENDING_R2 = 200581;
    constexpr uint32 SPELL_NATURES_MENDING_R3 = 200582;      // capstone: Cultivation
    constexpr uint32 SPELL_DEEP_ROOTS_R1 = 200583;
    constexpr uint32 SPELL_DEEP_ROOTS_R2 = 200584;
    constexpr uint32 SPELL_DEEP_ROOTS_R3 = 200585;           // capstone: -25% Regrowth cost
    constexpr uint32 SPELL_YSERAS_GIFT_R1 = 200586;
    constexpr uint32 SPELL_YSERAS_GIFT_R2 = 200587;
    constexpr uint32 SPELL_YSERAS_GIFT_R3 = 200588;          // capstone: Waking Dream
    constexpr uint32 SPELL_PERENNIAL_R1 = 200589;
    constexpr uint32 SPELL_PERENNIAL_R2 = 200590;
    constexpr uint32 SPELL_PERENNIAL_R3 = 200591;
    constexpr uint32 SPELL_PROLIFERATION_R1 = 200592;
    constexpr uint32 SPELL_PROLIFERATION_R2 = 200593;
    constexpr uint32 SPELL_PROLIFERATION_R3 = 200594;        // capstone: Germination
    constexpr uint32 SPELL_PHOTOSYNTHESIS_R1 = 200595;
    constexpr uint32 SPELL_PHOTOSYNTHESIS_R2 = 200596;
    constexpr uint32 SPELL_PHOTOSYNTHESIS_R3 = 200597;       // capstone: forced Lifebloom bloom
    constexpr uint32 SPELL_UNSTOPPABLE_GROWTH_R1 = 200598;
    constexpr uint32 SPELL_UNSTOPPABLE_GROWTH_R2 = 200599;
    constexpr uint32 SPELL_OMEN_OF_CLARITY_R2 = 200600;
    constexpr uint32 SPELL_OMEN_OF_CLARITY_R3 = 200601;      // carries 200572, not 16870

    // Repurposed/reused stock talent-rank ids this pass's scripts read directly.
    constexpr uint32 SPELL_NATURES_FOCUS_R1 = 17063;
    constexpr uint32 SPELL_NATURES_FOCUS_R2 = 17065;         // capstone rank: Tranquility protection
    constexpr uint32 SPELL_NATURAL_SHAPESHIFTER_R1 = 16833;
    constexpr uint32 SPELL_NATURAL_SHAPESHIFTER_R2 = 16834;
    constexpr uint32 SPELL_NATURAL_SHAPESHIFTER_R3 = 16835;  // capstone: no-GCD shapeshifts
    constexpr uint32 SPELL_OMEN_OF_CLARITY_R1 = 16864;       // stays bound to spell_dru_omen_of_clarity too
    constexpr uint32 SPELL_NATURALIST_R1 = 17069;
    constexpr uint32 SPELL_NATURALIST_R2 = 17070;
    constexpr uint32 SPELL_NATURALIST_R3 = 17071;            // capstone: Harmony, HT at 2x rate
    constexpr uint32 SPELL_IMPROVED_TRANQUILITY_R1 = 17123;
    constexpr uint32 SPELL_IMPROVED_TRANQUILITY_R2 = 17124;  // capstone: Harmony on Tranquility
    constexpr uint32 SPELL_EMPOWERED_TOUCH_R1 = 33879;
    constexpr uint32 SPELL_EMPOWERED_TOUCH_R2 = 33880;       // capstone: HT/Flourish reduce CDs
    constexpr uint32 SPELL_EMPOWERED_REJUVENATION_R1 = 33886;
    constexpr uint32 SPELL_EMPOWERED_REJUVENATION_R2 = 33887;
    constexpr uint32 SPELL_EMPOWERED_REJUVENATION_R3 = 33888; // capstone: Harmony on the 5 spells
    constexpr uint32 SPELL_NATURES_BOUNTY_R1 = 17074;
    constexpr uint32 SPELL_NATURES_BOUNTY_R2 = 17075;
    constexpr uint32 SPELL_NATURES_BOUNTY_R3 = 17076;        // capstone proc: Regrowth HoT spread
    constexpr uint32 SPELL_LIVING_SPIRIT_R1 = 34151;
    constexpr uint32 SPELL_LIVING_SPIRIT_R2 = 34152;
    constexpr uint32 SPELL_LIVING_SPIRIT_R3 = 34153;         // capstone: Spirit per active Rejuvenation
    constexpr uint32 SPELL_NATURAL_PERFECTION_R1 = 33881;
    constexpr uint32 SPELL_NATURAL_PERFECTION_R2 = 33882;
    constexpr uint32 SPELL_NATURAL_PERFECTION_R3 = 33883;    // capstone: Cenarion Ward CD on crit heal
    constexpr uint32 SPELL_LIVING_SEED_R1 = 48496;
    constexpr uint32 SPELL_LIVING_SEED_R2 = 48499;
    constexpr uint32 SPELL_LIVING_SEED_R3 = 48500;
    constexpr uint32 SPELL_REVITALIZE_R1 = 48539;
    constexpr uint32 SPELL_REVITALIZE_R2 = 48544;
    constexpr uint32 SPELL_REVITALIZE_R3 = 48545;            // capstone: HT-to-full mana refund
    constexpr uint32 SPELL_GIFT_OF_THE_EARTHMOTHER_R1 = 51179;
    constexpr uint32 SPELL_GIFT_OF_THE_EARTHMOTHER_R2 = 51180;
    constexpr uint32 SPELL_GIFT_OF_THE_EARTHMOTHER_R3 = 51181; // capstone: 2 Lifebloom targets

    // Stock Master Shapeshifter form-bonus spells (CORE-AUDIT row 16) - orphaned from their own
    // talent (48411/48412) by this pass's cut, reused as the cast targets of
    // ApplyShapeshiftFormBonuses. Never referenced by icon/GetDummyAuraEffect(GENERIC, 2851, 0)
    // anymore; this pass casts them directly by id instead.
    constexpr uint32 SPELL_NATURAL_SHAPESHIFTER_BEAR = 48418;
    constexpr uint32 SPELL_NATURAL_SHAPESHIFTER_CAT = 48420;
    constexpr uint32 SPELL_NATURAL_SHAPESHIFTER_MOONKIN = 48421;

    // Deep Roots r3 capstone (CORE-AUDIT row 15): hidden 1-charge SpellMod aura toggled by
    // spell_dru_deep_roots_capstone (AllSpellScript::CanPrepare, druid_hooks.cpp) - WP-A's data:
    // ADD_FLAT_MODIFIER COST, BP = -25% of Regrowth's base cost, classmask-scoped to Regrowth
    // (200602 was listed spare in RESTO §2.1's 200602-200679 block; this pass claims it).
    constexpr uint32 SPELL_DEEP_ROOTS_COST_REDUCTION = 200602;

    // Baseline / referenced stock spells
    constexpr uint32 SPELL_REJUVENATION = 774;
    constexpr uint32 SPELL_HEALING_TOUCH = 5185;
    constexpr uint32 SPELL_REGROWTH = 8936;
    constexpr uint32 SPELL_LIFEBLOOM = 33763;
    constexpr uint32 SPELL_LIFEBLOOM_BLOOM = 33778;
    constexpr uint32 SPELL_WILD_GROWTH = 48438;
    constexpr uint32 SPELL_SWIFTMEND = 18562;
    constexpr uint32 SPELL_TRANQUILITY = 740;
    constexpr uint32 SPELL_TRANQUILITY_TICK = 44203;
    constexpr uint32 SPELL_NATURAL_ALACRITY = 17116;         // repurposed Nature's Swiftness (baseline)
    constexpr uint32 SPELL_TREE_OF_LIFE_FORM = 33891;
    constexpr uint32 SPELL_TREE_OF_LIFE_PASSIVE = 5420;
    constexpr uint32 SPELL_TREE_OF_LIFE_TALENT_RANK = 65139; // learns 33891 + 5420
    constexpr uint32 SPELL_NOURISH = 50464;                  // removed; referenced only by the retired-bit comment

    // Repurposed talent ids (talent_dbc id, not a spell id - PLAN §4.2)
    constexpr uint32 TALENT_NATURES_FOCUS = 823;
    constexpr uint32 TALENT_NATURAL_SHAPESHIFTER = 826;
    constexpr uint32 TALENT_NATURES_RESILIENCE = 822;        // was Furor
    constexpr uint32 TALENT_NATURES_MENDING = 1915;          // was Master Shapeshifter
    constexpr uint32 TALENT_DEEP_ROOTS = 841;                // was Subtlety
    constexpr uint32 TALENT_YSERAS_GIFT = 60055;
    constexpr uint32 TALENT_PERENNIAL = 60056;
    constexpr uint32 TALENT_OMEN_OF_CLARITY = 827;
    constexpr uint32 TALENT_SWIFTMEND = 844;
    constexpr uint32 TALENT_NATURALIST = 824;
    constexpr uint32 TALENT_IMPROVED_TRANQUILITY = 842;
    constexpr uint32 TALENT_EMPOWERED_TOUCH = 1788;
    constexpr uint32 TALENT_EMPOWERED_REJUVENATION = 1789;
    constexpr uint32 TALENT_NATURES_BOUNTY = 825;
    constexpr uint32 TALENT_LIVING_SPIRIT = 1797;
    constexpr uint32 TALENT_BLOOM = 831;                     // was Nature's Swiftness
    constexpr uint32 TALENT_NATURAL_PERFECTION = 1790;
    constexpr uint32 TALENT_PROLIFERATION = 60057;
    constexpr uint32 TALENT_LIVING_SEED = 1922;
    constexpr uint32 TALENT_REVITALIZE = 1929;
    constexpr uint32 TALENT_TREE_OF_LIFE = 1791;
    constexpr uint32 TALENT_PHOTOSYNTHESIS = 1930;           // was Improved Tree of Life
    constexpr uint32 TALENT_UNSTOPPABLE_GROWTH = 2264;       // was Improved Barkskin
    constexpr uint32 TALENT_GIFT_OF_THE_EARTHMOTHER = 1916;
    constexpr uint32 TALENT_FLOURISH = 60058;

    // --- §9 definitions/helpers (namespace Druid; Heal::IsDirectNatureHeal covers RESTO §9's own
    // "Druid::IsDirectNatureHeal" per §0.13 Q4 - callers use HealMechanics.h directly instead) ---

    // The closed "core heal over time spell" list (RESTO §9): Rejuvenation, Germination, Regrowth's
    // periodic effect, Lifebloom, Wild Growth, Cenarion Ward's released heal - plus Lifebloom's
    // bloom (33778) for Empowered Rejuvenation's Harmony only (its own capstone lists it). Used by
    // Empowered Rejuvenation (coefficient + Harmony) and anywhere else the closed list matters.
    bool IsCoreHot(SpellInfo const* spellInfo);

    // "Your heal over time effects" (RESTO §9's shared enumeration, used by both CountHarmonyHots
    // and Flourish): walks every distinct Aura on `target` with a SPELL_AURA_PERIODIC_HEAL effect
    // whose caster is `caster`, excluding fixed-cadence periodics, and invokes `fn` once per Aura.
    void ForEachCasterHot(Unit const* caster, Unit* target, std::function<void(Aura*)> const& fn);

    // Mastery: Harmony's N (RESTO §4) - counts distinct Auras via ForEachCasterHot, per the table in
    // RESTO §4 (Lifebloom counts once regardless of stacks; Cenarion Ward's ward does not count, its
    // released heal does; Tranquility and Living Seed never count).
    uint32 CountHarmonyHots(Unit const* caster, Unit const* target);

    // Self plus same-map group members' count of the caster's own Rejuvenation (774) and Germination
    // (200568) auras (RESTO §9/§13 Q34 - "group" means party or raid plus the druid; a non-group
    // target's Rejuvenation is never counted). Used by Living Spirit's capstone and Waking Dream.
    uint32 CountActiveRejuvenations(Player const* caster);

    // Mastery: Harmony's per-effect multiplier (RESTO §4): 0.20, or 0.40 for Healing Touch once
    // Naturalist's capstone (SPELL_NATURALIST_R3) is known. Returns 0 if the spell/effect is not
    // Harmony-enabled for the caster (no relevant capstone known).
    float GetHarmonyCoefficient(Unit const* caster, SpellInfo const* spellInfo, bool isPeriodic);

    // Highest-known-rank-first `GetAuraEffect(id, eff)->GetAmount()` lookup (RESTO §8's "no icon
    // markers" convention - ranks are read by rank spell id, highest first, since only one rank of
    // a given talent is ever known at once).
    int32 GetRankAmount(Unit const* caster, std::initializer_list<uint32> rankSpellIds, uint8 effIndex);

    // --- §10 call-site hooks (namespace Druid; bodies + call sites are WP-B) ---
    //
    // *** WP-0 DRAFT WARNING RESOLVED (WP-B) ***: verified against CORE-AUDIT rows 11-15.
    // `ApplySpellCritChanceMods`, `ApplyHealingCoefficientMods` and `ApplyPowerCostMods` (rows 13-15)
    // are DELETED - CORE-AUDIT's mechanism for each needs no cross-cutting DruidMechanics helper or
    // core-file call site: row 13/14 are self-contained in the new `spell_dru_regrowth` AuraScript's
    // own `DoEffectCalcAmount(EFFECT_1)` (calling the already-public `Unit::SpellDoneCritChance`/
    // `SpellTakenCritChance`/`AuraEffect::SetCritChance` and `Unit::SpellHealingBonusDone` directly);
    // row 15 is self-contained in `spell_dru_deep_roots_capstone` (`AllSpellScript::CanPrepare`,
    // druid_hooks.cpp) toggling `SPELL_DEEP_ROOTS_COST_REDUCTION`. `ApplyPeriodicHealTickMods`'s
    // signature is changed below to match what the real call site (`ModifyPeriodicDamageAurasTick`)
    // actually hands a script - `AuraEffect const*` isn't available there, only `SpellInfo const*`
    // and the tick's already-computed `uint32` heal.

    // Direct-heal Harmony/Nature's Mending/Waking Dream/Omen-capstone multiplier (CORE-AUDIT row 11).
    // NOT a core call site: call this directly from `spell_dru_harmony_direct`'s OnHit handler (the
    // SpellScript bound to 5185, 8936, 18562, 200560, 200561, 44203, 200569 - RESTO §10/CORE-AUDIT
    // row 11), as `SetHitHeal(int32(GetHitHeal() * mult))`. `harmonyHotCount` is the value cached in
    // that script's BeforeHit (`Druid::CountHarmonyHots`), taken *before* this cast's own new HoT (if
    // any, e.g. Regrowth's own periodic effect) could apply - this function does not recompute it
    // itself so that bookkeeping stays correct. Lifebloom's bloom (33778) is NOT bound to this script
    // - `TriggerLifebloomBloom` applies Harmony itself, since it isn't a SpellScript hit at all.
    float GetDirectHealMultiplier(Unit* caster, Unit* victim, SpellInfo const* spellProto,
                                   uint32 harmonyHotCount);

    // Per-tick Harmony + Nature's Mending multiplier (CORE-AUDIT row 12). NOT a SpellAuraEffects.cpp
    // core edit: call this from the EXISTING `UnitScript::ModifyPeriodicDamageAurasTick` hook in
    // druid_hooks.cpp - real signature `(Unit* target, Unit* attacker, uint32& damage, SpellInfo
    // const* spellInfo)` (already declared in ScriptMgr for both damage and heal ticks despite the
    // name; fires after crit and the final-tick-bonus multiplier, before absorb/DealHeal -
    // SpellAuraEffects.cpp:6699), filtered internally to `Druid::IsCoreHot(spellInfo)`.
    void ApplyPeriodicHealTickMods(Unit* caster, Unit* target, SpellInfo const* spellInfo, uint32& heal);

    // Omen of Clarity capstone detection (RESTO §0.10 item 4): true if the spell currently being cast
    // by `caster` has 200572 (the Omen r3 Clearcasting variant) among its applied/consumed SpellMods
    // at cast completion (before `RemoveSpellMods`) - read via `caster->m_spellModTakingSpell`, the
    // same idiom RESTO §8 (2,1) describes. Used both by `spell_dru_harmony_direct` (this pass's
    // healing +10%) and, added in this pass, by Balance's existing `Druid::ApplyDoneDamagePctMods`
    // (its damage-side +10% clause - the Unit.cpp call site for that function already exists from the
    // Balance pass, so extending its body here is still 0 new core lines).
    bool ConsumedEmpoweredClearcasting(Player const* caster);

    // Natural Shapeshifter's per-form healing/damage/crit bonuses (CORE-AUDIT row 16; Feral extends
    // the same hook for its own form boosts, row 32). CORE-AUDIT row 16 OVERRIDES RESTO.md §10's own
    // "migrate the Master Shapeshifter blocks into this function" instruction: the stock
    // `HandleShapeshiftBoosts` blocks (SpellAuraEffects.cpp) are NOT edited or migrated - they stay,
    // untouched and already inert (they key on `GetDummyAuraEffect(GENERIC, 2851, 0)`, and Master
    // Shapeshifter's ranks 48411/48412 are orphaned by this pass's talent cut, so that dummy aura can
    // never exist again). This function is called instead from a *new* ScriptMgr UnitScript hook in
    // druid_hooks.cpp - `OnAuraApply`/`OnAuraRemove` on `SPELL_AURA_MOD_SHAPESHIFT` auras - which
    // fires after `HandleShapeshiftBoosts`/`InitDataForForm` have already run. `OnAuraRemove` must
    // pass the form being shifted TO (computed from the incoming shapeshift aura, or FORM_NONE), not
    // the form being left.
    void ApplyShapeshiftFormBonuses(Unit* target, ShapeshiftForm form);

    // The stock Lifebloom bloom math (`spell_dru_lifebloom`) minus the mana-return energize, shared
    // so Photosynthesis's forced bloom can call the identical formula. `forced` is true only from
    // Photosynthesis (leaves stacks/duration untouched, applies Harmony/Empowered Rejuvenation via
    // the normal SpellHealingBonusDone path, but is not a direct Nature heal and returns no mana).
    void TriggerLifebloomBloom(Unit* caster, Unit* target, Aura* lifebloom, bool forced);

    // Lifebloom's one-target rule (two with Gift of the Earthmother's capstone, RESTO §8 (9,2)).
    // Call site: `spell_dru_lifebloom_target_limit` (SpellScript on 33763, AfterHit). Removes the
    // oldest tracked target's Lifebloom with AURA_REMOVE_BY_DEFAULT (never blooms) once the limit is
    // exceeded; state lives in `caster`'s CustomData (RESTO §10, lost on relog by design).
    void OnLifebloomApplied(Player* caster, Unit* target);

    // Tree of Life's instant Rejuvenation heal on every application (including Proliferation spreads
    // and Germination). Call site: `spell_dru_rejuvenation`'s AfterHit, only when the caster is in
    // FORM_TREE.
    void OnRejuvenationApplied(Unit* caster, Unit* target, Aura* rejuvenation);

    // Extends both Duration and MaxDuration of a HoT aura by `ms` (RESTO §10) - shared by Swiftmend
    // (+6000), Perennial (+2000 per extension) and Flourish (+8000). May exceed the aura's normal
    // maximum duration.
    void ExtendHot(Aura* aura, int32 ms);

    // Flourish's tick-rate doubling (CORE-AUDIT row 21 correction #1 in the WP-B brief - explicitly
    // NO `AuraEffect::AccelerateTicks` core API/no SpellAuraEffects.h/.cpp edit). For every
    // SPELL_AURA_PERIODIC_HEAL effect on `aura` (skipping SpellAuraEffects.h's
    // `IsFixedCadencePeriodic`), schedules floor(windowMs / amplitude) extra
    // `AuraEffect::PeriodicTick()` calls at half-amplitude spacing on the aura owner's own
    // `m_Events` (which dies with the owner, so the raw `Unit*` capture is safe); each scheduled
    // event re-resolves the aura by (ownerGuid-implicit via the same m_Events, casterGUID, base
    // spell id) and compares the resolved `Aura*` against the one captured at schedule time before
    // firing, and only fires while `GetTickNumber() < GetTotalTicks()`. Shared by `spell_dru_flourish`
    // (windowMs = 8000, for every HoT in range at cast) and the `druid_hooks.cpp` `OnAuraApply`
    // handler (RESTO §0.13 Q16 - a HoT applied *during* the Flourish window gets the buff's
    // *remaining* time as its own window).
    void AccelerateHotTicks(Aura* aura, int32 windowMs);

    // Code-review fix: `druid_hooks.cpp`'s `OnAuraApply` fires on a refresh/stack of an existing
    // aura (`Unit.cpp`'s `ModStackAmount` path), not just a genuinely new application - both the
    // Flourish acceleration above and the Omen of Clarity r3 capstone's one-time HoT boost below
    // must only ever run once per aura instance, or repeated refreshes during the same window
    // compound them. Called from `OnAuraApply` for every core-HoT application; internally no-ops
    // (via a per-target tracked set, cleared by `ClearCoreHotApplication` on removal) on any call
    // after the first for the same `Aura*`. Owns both effects so `druid_hooks.cpp` stays thin.
    void OnCoreHotApplied(Unit* target, Aura* aura);
    void ClearCoreHotApplication(Unit* target, Aura* aura);

    // Bloom's breadth-first jump scheduler (RESTO §6). Call site: `spell_dru_bloom`'s AfterHit.
    // Schedules 0.3 s-spaced waves via `caster->m_Events`, each wave healing up to 3 new targets
    // (20 yd, LoS, carrying the caster's Rejuvenation/Germination, lowest HP% first) per unit in the
    // previous wave, until no new targets remain; each target is visited at most once.
    void StartBloomJumps(Unit* caster, Unit* primary);
}

#endif
