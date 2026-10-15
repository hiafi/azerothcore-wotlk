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

#ifndef __HUNTERMECHANICS_H
#define __HUNTERMECHANICS_H

#include "Define.h"
#include "Generated/HunterData.h"
#include "SharedDefines.h"
#include <cstdint>

class Pet;
class Player;
class ProcEventInfo;
class Spell;
class SpellInfo;
class Unit;

/*
 * Hunter-specific "doesn't fit a SpellScript/AuraScript" hooks - mirrors WarlockMechanics.h's shape
 * (.agents/plans/hunter-rework/hunter-rework.SHARED.md §A5, §C4). Append-only: each later stage adds its
 * declarations together with their bodies and never retypes an existing signature. Stage T2 holds only the
 * T2 block; H0 adds the HunterData:: aliases (DSL-declared ids) and the H0 block.
 */
namespace Hunter
{
    // ---- T2 ----
    constexpr uint32 SPELL_REQUIRES_NO_AMMO = 46699;      // stock Thori'dal aura, granted to every player

    // Q5: two hunter stings (SPELL_SPECIFIC_STING) never exclude each other. Called from the one core line in
    // SpellInfo::IsAuraExclusiveBySpecificPerCasterWith. True when both a and b are hunter stings.
    bool StingsStack(SpellInfo const* a, SpellInfo const* b);

    // The player that owns `unit`: itself, or the owner/charmer of a pet, guardian or totem. nullptr otherwise.
    Player* GetOwningPlayer(Unit* unit);
    Player const* GetOwningPlayer(Unit const* unit);

    // Proc Chance for scripted rolls (PLAN §2): chance * (1 + owner Proc Chance / 100). A pet or guardian resolves
    // to its owner (warlock GetOwnerProcChanceMultiplier precedent). Non-player chains use multiplier 1.
    float GetProcChanceMultiplier(Unit const* unit);
    bool  RollProcChance(Unit const* unit, float baseChancePct);

    // Real-seconds, client-visible cooldown cut (Player::ModifySpellCooldown, druid A8); never scaled by
    // Cooldown Haste. No-op when the spell has no running cooldown.
    void  ReduceSpellCooldown(Player* player, uint32 spellId, uint32 ms);

    // Q32: worldserver.conf `Custom.Realm.Classless` (default 0), read once (function-local static).
    bool  IsClasslessRealm();

    // Grants 46699 silently (addSpell on an unknown spell, CastSpell when known but the aura is gone).
    void  EnsureNoAmmoAura(Player* player);

    // Logout cleanup; each later section adds its own Clear*State call here. Removal paths use find-only map
    // access (paladin CR5).
    void  ClearState(Player* player);

    // ---- H0 ----
    // DSL-declared ids the H0 code uses (stock ids the DSL never declares stay hand literals).
    constexpr uint32 SPELL_AUTO_SHOT = HunterData::SPELL_AUTO_SHOT;
    constexpr uint32 SPELL_QUICK_SHOTS = HunterData::SPELL_QUICK_SHOTS;
    constexpr uint32 SPELL_ASPECT_OF_THE_BEAST = HunterData::SPELL_ASPECT_OF_THE_BEAST;
    constexpr uint32 SPELL_ASPECT_OF_THE_MONKEY = HunterData::SPELL_ASPECT_OF_THE_MONKEY;
    constexpr uint32 SPELL_ASPECT_OF_THE_HAWK = HunterData::SPELL_ASPECT_OF_THE_HAWK;
    constexpr uint32 SPELL_ASPECT_OF_THE_VIPER = HunterData::SPELL_ASPECT_OF_THE_VIPER;
    constexpr uint32 SPELL_ASPECT_OF_THE_DRAGONHAWK = HunterData::SPELL_ASPECT_OF_THE_DRAGONHAWK;
    constexpr uint32 SPELL_KILL_COMMAND = HunterData::SPELL_KILL_COMMAND;
    constexpr uint32 SPELL_GLAIVE_TOSS = HunterData::SPELL_GLAIVE_TOSS;
    constexpr uint32 SPELL_ASPECT_OF_THE_DRAGONHAWK_EXPLOSION = HunterData::SPELL_ASPECT_OF_THE_DRAGONHAWK_EXPLOSION;
    constexpr uint32 SPELL_ASPECT_OF_THE_VIPER_POISON = HunterData::SPELL_ASPECT_OF_THE_VIPER_POISON;
    constexpr uint32 SPELL_ASPECT_OF_THE_BEAST_PET_BUFF = HunterData::SPELL_ASPECT_OF_THE_BEAST_PET_BUFF;
    constexpr uint32 SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY = HunterData::SPELL_ASPECT_OF_THE_MONKEY_VERSATILITY;
    constexpr uint32 SPELL_ASPECT_OF_THE_MONKEY_PET = HunterData::SPELL_ASPECT_OF_THE_MONKEY_PET;

    // Q14: does this spell roll the hunter's aspect procs? Hunter family, DmgClass RANGED, not passive, not a pet
    // ability (d1 b28), at least one damage effect (SCHOOL_DAMAGE, WEAPON_DAMAGE[_NOSCHOOL], NORMALIZED_WEAPON_DMG,
    // WEAPON_PERCENT_DAMAGE, or a PERIODIC_DAMAGE aura), and not Kill Command (34026 and PET.md's strike id).
    // Auto Shot is handled by the HIT branch of the aspect CheckProc, not here.
    bool  IsAspectRollSource(SpellInfo const* spellInfo);

    // The unit a proc should act on: the action target, or, in the CAST phase (no action target), the proc
    // spell's explicit unit target.
    Unit* GetProcTarget(ProcEventInfo& eventInfo);

    // REVIEW-MM-SV V1: a direct Fire hit from a spell that carries SUPPRESS_CASTER_PROCS raises no proc at all, the
    // victim's TAKEN procs included (Spell.cpp:2706, :2969-2974), so SV's Tarred proc can't see it. Every such spell
    // that must still count as a "direct Fire hit" calls this from its AfterHit. H0 declares it with an EMPTY body and
    // calls it from 201601's script (§B6.4); S3 fills the body and calls it from its own suppressed blasts.
    // Contract (SURVIVAL §0.23, binding on H0 and S3):
    //  - Callers: Tarred 202048's OnEffectProc (the unsuppressed sources: the 53301 hit, the 202045 impact, the 202051
    //    first blast, the 13812 blast) and the AfterHit of every suppressed Fire source (201601 from H0; 202052, 202053,
    //    202054 from S3). An AfterHit caller passes GetCaster(), GetHitUnit(), GetSpellInfo() and calls only when
    //    GetHitDamage() > 0 (no stack from a full absorb or an immune hit).
    //  - Body (S3): hunter = GetOwningPlayer(attacker); return unless hunter, target alive, target has Tarred 202048
    //    from hunter, spellInfo's school mask has FIRE, the spell is not periodic-only, and spellInfo->Id is not one
    //    of {53352, 202055, 202057, 202050} (blasts, blast splash, ground fire, Burning Tar). Then AddBurningTar.
    //  - Never twice for one hit: a spell either raises the Tarred proc (no SUPPRESS_CASTER_PROCS) or calls this from
    //    AfterHit (it has the attribute), never both. WP-B keeps the list in a comment next to the body.
    void  OnDirectFireHit(Unit* attacker, Unit* target, SpellInfo const* spellInfo);

    // Shot mana (§B2): the percent of maximum mana stored in the shot's EFFECT_1 DUMMY (tenths of a percent),
    // read with CalcValue(caster) so SPELLMOD_EFFECT2 / ALL_EFFECTS talents apply.
    float GetShotManaPct(Unit const* caster, SpellInfo const* shot);
    // EnergizeBySpell(player, shot->Id, max mana * pct * multiplier, POWER_MANA). MM's free Arcane Shot and
    // Lethal Shots capstone call it too.
    void  RestoreShotMana(Player* player, SpellInfo const* shot, float multiplier = 1.0f);

    // ---- H0-P (PET.md §8.4 defines the bodies and the rest of the pet section) ----
    constexpr uint32 SPELL_BLOODTHIRSTY_54131 = HunterData::SPELL_BLOODTHIRSTY_54131;
    constexpr uint32 SPELL_WEB_PULL = HunterData::SPELL_WEB_PULL; // appears once web_pull_201718 is generated
    // ---- S1 / S2 / S3 append their own sections (transform re-cast, mark state, Burning Tar bank) ----
}

#endif
