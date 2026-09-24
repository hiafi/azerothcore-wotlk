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

class Player;
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
}

#endif
