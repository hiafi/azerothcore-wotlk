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

/*
 * Paladin rework - Retribution tree scripts
 * (.agents/plans/paladin-rework/paladin-rework.RETRIBUTION.md §2.7, behaviour in §6 and §7).
 *
 * Replacement/additive classes for the Retribution tree. Stock spell_paladin.cpp stays unedited:
 * every stock class this tree displaces is unbound by data (RETRIBUTION §5.2, WP-A's `unbind_script`)
 * and the classes below are bound by data (`scripted_by`). Script names must match WP-A's bindings
 * byte for byte. The seal core (builders, Judgement/Deliverance dispatch, unleashes, passives) is
 * SHARED's, in spell_paladin_seals.cpp; the `Paladin::` Ret section (hooks, Execution Sentence
 * tracker) is in PaladinMechanics.cpp.
 *
 * Common rules (SHARED Part B, CR1-CR5): every hook that needs a Player returns early for a
 * non-player owner/caster (NPC paladins cast through smart_scripts); DUMMY proc effects call
 * PreventDefaultAction(); once-per-cast guards; no Paladin:: state is touched in removal paths
 * beyond the find-only tracker calls.
 */

#include "PaladinMechanics.h"
#include "Generated/PaladinData.h"
#include "Creature.h"
#include "GameTime.h"
#include "Group.h"
#include "HealMechanics.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellDefines.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <list>
#include <vector>

namespace
{
    // Stock ids that are not part of the generated PaladinData header (not declared in the DSL).
    // Divine Storm heal (stock, SUPPRESS_CASTER_PROCS)
    constexpr uint32 SPELL_DIVINE_STORM_HEAL = 54172;
    // Divine Shield Exclude Aura (642's ExcludeCasterAuraSpell)
    constexpr uint32 SPELL_DIVINE_SHIELD_EXCLUDE_AURA = 61988;

    constexpr float ECHO_LIGHT_RANGE = 30.0f;                         // RETRIBUTION §6.1: Light echo ally pick
    constexpr uint8 ECHO_LIGHT_ALLIES = 3;
    constexpr float ECHO_LIGHT_BASE_HEALTH_PCT = 60.0f;               // Echoing Light: % of base health
    constexpr float ECHO_WISDOM_MAX_MANA_PCT = 1.5f;                  // Echoing Wisdom damage: % of max mana
    constexpr float ECHO_WISDOM_BASE_MANA_PCT = 60.0f;                // Wisdom echo energize: % of base mana

    constexpr int32 WAKE_OF_ASHES_RADIANT_GLORY_MS = 6000;            // Crusade capstone: Avenging Wrath time
    constexpr uint32 DIVINE_STORM_MAX_TARGETS = 5;                    // §0.2 item 6: load correction sets 4
    constexpr float SANCTITY_DIVINE_STORM_MULT = 1.5f;                // Sanctity of Battle: Divine Storm +50%
    constexpr float TWO_HANDED_CAPSTONE_PER_STACK = 0.02f;            // Two-Handed Weapon Specialization capstone
    constexpr float DIVINE_STORM_HEAL_RANGE = 30.0f;
    constexpr uint8 DIVINE_STORM_HEAL_TARGETS = 3;

    constexpr int32 EXECUTION_SENTENCE_BONUS_PER_STACK = 5;           // % per seal stack gained while the hammer falls

    constexpr float BENEDICTION_CAPSTONE_RANGE = 30.0f;               // starting guess (§6.10)
    constexpr int32 BENEDICTION_CAPSTONE_MANA_BELOW_PCT = 50;
    constexpr float BENEDICTION_CAPSTONE_MANA_PCT = 10.0f;

    constexpr float EYE_FOR_AN_EYE_HEALTH_PCT = 50.0f;
    constexpr uint8 EYE_FOR_AN_EYE_CAPSTONE_RANK = 3;

    constexpr float SHEATH_OF_LIGHT_CAPSTONE_MANA_PCT = 8.0f;

    // Once-per-cast guard shared by Vindication and The Art of War (§6.7): one proc attempt per Spell
    // object per world tick. State lives in the AuraScript instance (as long as the talent aura).
    struct CastGuard
    {
        Spell const* spell = nullptr;
        uint32 ms = 0;

        // True the first time this cast is seen; auto attacks (no proc spell) always pass.
        bool Claim(ProcEventInfo& eventInfo)
        {
            Spell const* procSpell = eventInfo.GetProcSpell();
            if (!procSpell)
                return true;

            uint32 const now = uint32(GameTime::GetGameTimeMS().count());
            if (procSpell == spell && now == ms)
                return false;

            spell = procSpell;
            ms = now;
            return true;
        }
    };

    Player* GetPlayer(Unit* unit)
    {
        return unit ? unit->ToPlayer() : nullptr;
    }
}

// ===========================================================================================
// 201400 - Blade of Justice (echo of the active seal) - RETRIBUTION §6.1
// ===========================================================================================
class spell_pal_blade_of_justice : public SpellScript
{
    PrepareSpellScript(spell_pal_blade_of_justice);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({
            PaladinData::SPELL_RIGHTEOUSNESS_ECHO, PaladinData::SPELL_COMMAND_ECHO,
            PaladinData::SPELL_VENGEANCE_ECHO, PaladinData::SPELL_JUSTICE_ECHO,
            PaladinData::SPELL_LIGHT_ECHO, PaladinData::SPELL_WISDOM_ECHO,
            PaladinData::SPELL_ECHOING_VENGEANCE, PaladinData::SPELL_ECHOING_LIGHT,
            PaladinData::SPELL_ECHOING_WISDOM, PaladinData::SPELL_SEAL_OF_JUSTICE_STUN,
            PaladinData::SPELL_UNLEASHED_JUSTICE_AOE_STUN, SPELL_DIVINE_SHIELD_EXCLUDE_AURA });
    }

    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        // AfterHit also runs for a miss/resist/evade on that target; only a landed blade echoes.
        _hit = (missInfo == SPELL_MISS_NONE);
    }

    void HandleAfterHit()
    {
        Player* caster = GetPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!_hit || !caster || !target)
            return;

        // A Primed aura is not an active seal.
        Paladin::SealType const seal = Paladin::GetActiveSeal(caster);
        if (seal == Paladin::SealType::None)
            return;

        // Echo spells are declared in SealType order (Righteousness, Command, Vengeance, Justice, Light, Wisdom).
        static constexpr std::array<uint32, size_t(Paladin::SealType::Count)> echoes =
        {
            PaladinData::SPELL_RIGHTEOUSNESS_ECHO, PaladinData::SPELL_COMMAND_ECHO,
            PaladinData::SPELL_VENGEANCE_ECHO, PaladinData::SPELL_JUSTICE_ECHO,
            PaladinData::SPELL_LIGHT_ECHO, PaladinData::SPELL_WISDOM_ECHO
        };

        // The blade's own hit may have killed the target: the echo still happens, but target-bound parts
        // (strike, DoT, stun, Wisdom damage) are skipped cleanly; caster-side parts always run.
        bool const targetAlive = target->IsAlive();
        if (targetAlive)
            caster->CastSpell(target, echoes[size_t(seal)], TRIGGERED_FULL_MASK);

        switch (seal)
        {
            case Paladin::SealType::Vengeance:
                if (targetAlive)
                    caster->CastSpell(target, PaladinData::SPELL_ECHOING_VENGEANCE, TRIGGERED_FULL_MASK);
                break;
            case Paladin::SealType::Justice:
                if (targetAlive)
                    HandleJusticeEcho(caster, target);
                break;
            case Paladin::SealType::Light:
                HandleLightEcho(caster);
                break;
            case Paladin::SealType::Wisdom:
                HandleWisdomEcho(caster, targetAlive ? target : nullptr);
                break;
            default:
                break;
        }
    }

    // Justice: guaranteed 0.5 s stun on creatures that are not player-controlled, with the same boss and
    // immunity checks as the seal's chance aura (SHARED B1.5) and skipping a target in its Justice Recovery.
    static void HandleJusticeEcho(Player* caster, Unit* target)
    {
        if (target->IsControlledByPlayer() || target->HasAura(PaladinData::SPELL_JUSTICE_RECOVERY))
            return;

        if (Paladin::IsBossForStun(target))
            return;

        SpellInfo const* immunityProbe = sSpellMgr->GetSpellInfo(PaladinData::SPELL_UNLEASHED_JUSTICE_AOE_STUN);
        if (immunityProbe && target->IsImmunedToSpell(immunityProbe, caster))
            return;

        caster->CastSpell(target, PaladinData::SPELL_SEAL_OF_JUSTICE_STUN, TRIGGERED_FULL_MASK);
    }

    // Light: Echoing Light on the paladin and the 3 most injured other allies within 30 yd,
    // 60% of the paladin's base health each (live value, passed as the base point).
    static void HandleLightEcho(Player* caster)
    {
        int32 const healAmount = int32(CalculatePct(caster->GetCreateHealth(), ECHO_LIGHT_BASE_HEALTH_PCT));

        std::vector<Unit*> allies;
        Heal::SelectMostInjured(caster, caster, ECHO_LIGHT_RANGE, ECHO_LIGHT_ALLIES, allies, caster);

        caster->CastCustomSpell(PaladinData::SPELL_ECHOING_LIGHT, SPELLVALUE_BASE_POINT0, healAmount, caster,
            TRIGGERED_FULL_MASK);
        for (Unit* ally : allies)
            caster->CastCustomSpell(PaladinData::SPELL_ECHOING_LIGHT, SPELLVALUE_BASE_POINT0, healAmount, ally,
                TRIGGERED_FULL_MASK);
    }

    // Wisdom: Echoing Wisdom damage (1.5% of max mana) and a direct 60% base-mana energize.
    static void HandleWisdomEcho(Player* caster, Unit* target)
    {
        float const maxMana = float(caster->GetMaxPower(POWER_MANA));
        int32 const damage = int32(std::lround(maxMana * ECHO_WISDOM_MAX_MANA_PCT / 100.0f));
        if (target)
            caster->CastCustomSpell(PaladinData::SPELL_ECHOING_WISDOM, SPELLVALUE_BASE_POINT0, damage, target,
                TRIGGERED_FULL_MASK);

        caster->EnergizeBySpell(caster, PaladinData::SPELL_WISDOM_ECHO,
            CalculatePct(caster->GetCreateMana(), ECHO_WISDOM_BASE_MANA_PCT), POWER_MANA);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_pal_blade_of_justice::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_pal_blade_of_justice::HandleAfterHit);
    }

private:
    bool _hit = false;
};

// ===========================================================================================
// 201410 - Execution Sentence (aura: tracker + burst on expiry/dispel/immunity) - RETRIBUTION §6.3
// ===========================================================================================
class spell_pal_execution_sentence : public AuraScript
{
    PrepareAuraScript(spell_pal_execution_sentence);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_EXECUTION_SENTENCE_BURST,
            PaladinData::SPELL_EXECUTION_SENTENCE_SPLASH });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* caster = GetPlayer(GetCaster());
        Unit* target = GetTarget();
        if (caster && target)
            Paladin::StartExecutionSentence(caster, target->GetGUID());
    }

    // Heuristic for "the target became immune" (PLAN §9, CORE-AUDIT Q6): an immunity removes the aura
    // with BY_DEFAULT while the target is alive and in the world. Evade fires nothing.
    static bool LooksLikeImmunityRemoval(Unit* target)
    {
        if (!target->IsAlive() || !target->IsInWorld())
            return false;

        if (Creature const* creature = target->ToCreature())
            if (creature->IsInEvadeMode())
                return false;

        return true;
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // A missing caster (logout) fires nothing (ClearStateRet handles it); an out-of-world one
        // fires nothing but still ends the tracker.
        Player* caster = GetPlayer(GetCaster());
        Unit* target = GetTarget();
        if (!caster || !target)
            return;

        if (!caster->IsInWorld())
        {
            Paladin::EndExecutionSentence(caster);
            return;
        }

        bool fireMain = false;
        bool fireSplash = false;
        switch (GetTargetApplication()->GetRemoveMode())
        {
            case AURA_REMOVE_BY_EXPIRE:
            case AURA_REMOVE_BY_ENEMY_SPELL:
                fireMain = true;
                fireSplash = true;
                break;
            case AURA_REMOVE_BY_DEATH:
                // E1: the main-target burst is lost, the splash is centred on the corpse.
                fireSplash = true;
                break;
            case AURA_REMOVE_BY_DEFAULT:
                fireMain = fireSplash = LooksLikeImmunityRemoval(target);
                break;
            default:
                break;
        }

        // Both casts resolve synchronously (no speed), while the tracker still holds the gained count.
        if (fireMain)
            caster->CastSpell(target, PaladinData::SPELL_EXECUTION_SENTENCE_BURST, TRIGGERED_FULL_MASK);

        if (fireSplash)
        {
            if (SpellInfo const* splash = sSpellMgr->GetSpellInfo(PaladinData::SPELL_EXECUTION_SENTENCE_SPLASH))
            {
                SpellCastTargets targets;
                targets.SetDst(*target);
                caster->CastSpell(targets, splash, nullptr, TRIGGERED_FULL_MASK);
            }
        }

        Paladin::EndExecutionSentence(caster);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_execution_sentence::HandleApply, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_execution_sentence::HandleRemove, EFFECT_0,
            SPELL_AURA_PERIODIC_DAMAGE, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 201411 / 201412 - Execution Sentence burst and splash - RETRIBUTION §6.3
// ===========================================================================================
class spell_pal_execution_sentence_burst : public SpellScript
{
    PrepareSpellScript(spell_pal_execution_sentence_burst);

    void HandleSplashTargets(std::list<WorldObject*>& targets)
    {
        // The main target already took the burst; any other hostile within 5 yd is a splash target.
        Player* caster = GetPlayer(GetCaster());
        if (!caster)
            return;

        ObjectGuid const mainTarget = Paladin::GetExecutionSentenceTarget(caster);
        if (mainTarget.IsEmpty())
            return;

        targets.remove_if([mainTarget](WorldObject const* object)
        {
            return object->GetGUID() == mainTarget;
        });
    }

    void HandleHit()
    {
        Player* caster = GetPlayer(GetCaster());
        if (!caster)
            return;

        int32 const gained = Paladin::GetExecutionSentenceGained(caster);
        if (!gained)
            return;

        SetHitDamage(int32(int64(GetHitDamage()) * (100 + EXECUTION_SENTENCE_BONUS_PER_STACK * gained) / 100));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pal_execution_sentence_burst::HandleHit);

        // One class is bound to both ids; only the splash has an area target to filter.
        if (m_scriptSpellId == PaladinData::SPELL_EXECUTION_SENTENCE_SPLASH)
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(
                spell_pal_execution_sentence_burst::HandleSplashTargets, EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// ===========================================================================================
// 201413 - Wake of Ashes - RETRIBUTION §6.4
// ===========================================================================================
class spell_pal_wake_of_ashes : public SpellScript
{
    PrepareSpellScript(spell_pal_wake_of_ashes);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_WAKE_OF_ASHES_STUN, PaladinData::SPELL_AVENGING_WRATH });
    }

    void HandleBeforeHit(SpellMissInfo missInfo)
    {
        _hit = (missInfo == SPELL_MISS_NONE);
    }

    void HandleAfterHit()
    {
        Player* caster = GetPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!_hit || !caster || !target)
            return;

        // Demons and Undead only (players are Humanoid - Forsaken are never stunned).
        uint32 const type = target->GetCreatureType();
        if (type == CREATURE_TYPE_DEMON || type == CREATURE_TYPE_UNDEAD)
            caster->CastSpell(target, PaladinData::SPELL_WAKE_OF_ASHES_STUN, TRIGGERED_FULL_MASK);
    }

    // Crusade capstone (Radiant Glory): Avenging Wrath for 6 s, or +6 s on an active one.
    void HandleAfterCast()
    {
        Player* caster = GetPlayer(GetCaster());
        if (!caster || !caster->HasAura(PaladinData::SPELL_CRUSADE_201465))
            return;

        if (Aura* wrath = caster->GetAura(PaladinData::SPELL_AVENGING_WRATH))
        {
            int32 const duration = wrath->GetDuration() + WAKE_OF_ASHES_RADIANT_GLORY_MS;
            if (duration > wrath->GetMaxDuration())
                wrath->SetMaxDuration(duration);

            wrath->SetDuration(duration);
        }
        else
        {
            // Triggered: no cooldown, no Crusader's Aegis (its CAST row ignores triggered casts).
            caster->CastCustomSpell(PaladinData::SPELL_AVENGING_WRATH, SPELLVALUE_AURA_DURATION,
                WAKE_OF_ASHES_RADIANT_GLORY_MS, caster, TRIGGERED_FULL_MASK);
        }
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_pal_wake_of_ashes::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_pal_wake_of_ashes::HandleAfterHit);
        AfterCast += SpellCastFn(spell_pal_wake_of_ashes::HandleAfterCast);
    }

private:
    bool _hit = false;
};

// ===========================================================================================
// 53385 - Divine Storm (Retribution) - RETRIBUTION §6.5
// ===========================================================================================
class spell_pal_divine_storm_ret : public SpellScript
{
    PrepareSpellScript(spell_pal_divine_storm_ret);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_DIVINE_STORM_HEAL, PaladinData::SPELL_SANCTITY_OF_BATTLE_EMPOWER,
            PaladinData::SPELL_TWO_HANDED_WEAPON_SPECIALIZATION_20113 });
    }

    // The load correction (SIC) caps Divine Storm at 4 targets; this restores 5 (§0.2 item 6).
    void HandleTargets(std::list<WorldObject*>& /*targets*/)
    {
        GetSpell()->SetSpellValue(SPELLVALUE_MAX_TARGETS, DIVINE_STORM_MAX_TARGETS);
    }

    // Divine Storm's effects 0 and 1 target the caster, so hooks also run for the paladin itself:
    // only a hit on an actual enemy counts (no Sanctity of Battle empower or consume on an empty cast).
    bool IsEnemyHit(Player* caster)
    {
        Unit* target = GetHitUnit();
        return target && target != caster && caster->IsHostileTo(target);
    }

    void HandleHit()
    {
        Player* caster = GetPlayer(GetCaster());
        if (!caster || !IsEnemyHit(caster))
            return;

        float multiplier = 1.0f;

        // Two-Handed Weapon Specialization capstone: the aura stays on without a two-hander, only its
        // effects deactivate, so check the weapon. Stacks held before this cast's own gain.
        SpellInfo const* twoHanded = sSpellMgr->GetSpellInfo(PaladinData::SPELL_TWO_HANDED_WEAPON_SPECIALIZATION_20113);
        if (twoHanded && caster->HasAura(twoHanded->Id) && caster->HasItemFitToSpellRequirements(twoHanded))
            multiplier *= 1.0f + TWO_HANDED_CAPSTONE_PER_STACK * float(Paladin::GetSealStacks(caster));

        // Sanctity of Battle: the empower is consumed in AfterCast, once all targets are hit.
        if (caster->HasAura(PaladinData::SPELL_SANCTITY_OF_BATTLE_EMPOWER))
        {
            multiplier *= SANCTITY_DIVINE_STORM_MULT;
            _empowered = true;
        }

        if (multiplier != 1.0f)
            SetHitDamage(int32(float(GetHitDamage()) * multiplier));
    }

    void HandleAfterHit()
    {
        Player* caster = GetPlayer(GetCaster());
        if (!caster || !IsEnemyHit(caster))
            return;

        _total += std::max<int32>(GetHitDamage(), 0);
    }

    void HandleAfterCast()
    {
        Player* caster = GetPlayer(GetCaster());
        if (!caster)
            return;

        if (_empowered)
            caster->RemoveAurasDueToSpell(PaladinData::SPELL_SANCTITY_OF_BATTLE_EMPOWER);

        if (_total <= 0)
            return;

        // Heals the 3 most injured party/raid members (the caster included when among them), splitting
        // the total of 25% of the damage caused.
        std::vector<Unit*> allies;
        Heal::SelectMostInjured(caster, caster, DIVINE_STORM_HEAL_RANGE, DIVINE_STORM_HEAL_TARGETS, allies);
        if (allies.empty())
            return;

        int32 const healPct = GetSpellInfo()->Effects[EFFECT_1].CalcValue(caster);
        int32 const share = CalculatePct(_total, healPct) / int32(allies.size());
        if (share <= 0)
            return;

        // 54172 carries SUPPRESS_CASTER_PROCS: no Beacon copy.
        for (Unit* ally : allies)
            caster->CastCustomSpell(SPELL_DIVINE_STORM_HEAL, SPELLVALUE_BASE_POINT0, share, ally, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pal_divine_storm_ret::HandleTargets,
            EFFECT_2, TARGET_UNIT_SRC_AREA_ENEMY);
        OnHit += SpellHitFn(spell_pal_divine_storm_ret::HandleHit);
        AfterHit += SpellHitFn(spell_pal_divine_storm_ret::HandleAfterHit);
        AfterCast += SpellCastFn(spell_pal_divine_storm_ret::HandleAfterCast);
    }

private:
    bool _empowered = false;
    int32 _total = 0;
};

// ===========================================================================================
// 35395 - Crusader Strike (Retribution) - RETRIBUTION §6.5
// ===========================================================================================
class spell_pal_crusader_strike_ret : public SpellScript
{
    PrepareSpellScript(spell_pal_crusader_strike_ret);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_TWO_HANDED_WEAPON_SPECIALIZATION_20113 });
    }

    void HandleHit()
    {
        Player* caster = GetPlayer(GetCaster());
        if (!caster)
            return;

        // Two-Handed Weapon Specialization capstone: +2% per seal stack held (before this cast's gain),
        // only while a two-hander is wielded.
        SpellInfo const* twoHanded =
            sSpellMgr->GetSpellInfo(PaladinData::SPELL_TWO_HANDED_WEAPON_SPECIALIZATION_20113);
        if (!twoHanded || !caster->HasAura(twoHanded->Id) || !caster->HasItemFitToSpellRequirements(twoHanded))
            return;

        uint8 const stacks = Paladin::GetSealStacks(caster);
        if (stacks)
            SetHitDamage(int32(float(GetHitDamage()) * (1.0f + TWO_HANDED_CAPSTONE_PER_STACK * float(stacks))));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pal_crusader_strike_ret::HandleHit);
    }
};

// ===========================================================================================
// 20119 - Conviction (capstone crit capture) - RETRIBUTION §6.6
// ===========================================================================================
class spell_pal_conviction : public AuraScript
{
    PrepareAuraScript(spell_pal_conviction);

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        // eff1 is a DUMMY proc carrier (trigger 0): never run the default trigger path.
        PreventDefaultAction();

        Player* player = GetPlayer(GetTarget());
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (player && procSpell)
            Paladin::NoteBuilderCrit(player, procSpell->Id);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pal_conviction::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// -9452 - Vindication (one attempt per cast) - RETRIBUTION §6.7
// ===========================================================================================
class spell_pal_vindication : public AuraScript
{
    PrepareAuraScript(spell_pal_vindication);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // Divine Storm hits up to 5 targets: the first target consumes the cast's single attempt
        // whether or not the roll then succeeds. Auto attacks always pass.
        return _guard.Claim(eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_vindication::CheckProc);
    }

private:
    CastGuard _guard;
};

// ===========================================================================================
// -53486 - The Art of War (per-cast guard, Divine Storm per target at half chance) - RETRIBUTION §6.7
// ===========================================================================================
class spell_pal_art_of_war : public AuraScript
{
    PrepareAuraScript(spell_pal_art_of_war);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (SpellInfo const* procSpell = eventInfo.GetSpellInfo())
        {
            // Only the burst rolls: one roll per Execution Sentence.
            if (procSpell->Id == PaladinData::SPELL_EXECUTION_SENTENCE_SPLASH)
                return false;

            // Divine Storm rolls on every target at half the chance (the row's chance already
            // carries Proc Chance).
            if (procSpell->Id == PaladinData::SPELL_DIVINE_STORM)
                return roll_chance_i(50);
        }

        return _guard.Claim(eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_art_of_war::CheckProc);
    }

private:
    CastGuard _guard;
};

// ===========================================================================================
// -31876 - Judgements of the Wise (one attempt per Judgement/Deliverance cast) - RETRIBUTION §6.7
// ===========================================================================================
class spell_pal_judgements_of_the_wise_guard : public AuraScript
{
    PrepareAuraScript(spell_pal_judgements_of_the_wise_guard);

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        // Deliverance casts one unleash Spell per target, so a Spell* guard cannot work here:
        // use SHARED's per-cast serial. The first damaging unleash of the cast consumes the attempt.
        Player* player = GetPlayer(GetTarget());
        return player && Paladin::TryClaimJudgementCast(player, PaladinData::SPELL_JUDGEMENTS_OF_THE_WISE);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_judgements_of_the_wise_guard::CheckProc);
    }
};

// ===========================================================================================
// -20101 - Benediction (mana + Strength on kill, party capstone) - RETRIBUTION §6.10
// ===========================================================================================
class spell_pal_benediction : public AuraScript
{
    PrepareAuraScript(spell_pal_benediction);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_BENEDICTION_BUFF });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        // eff0 is a DUMMY proc carrier (trigger 0): never run the default trigger path.
        PreventDefaultAction();

        Player* player = GetPlayer(GetTarget());
        if (!player)
            return;

        player->EnergizeBySpell(player, GetId(), CalculatePct(player->GetCreateMana(), aurEff->GetAmount()),
            POWER_MANA);

        // Strength percent is the rank's second effect; refreshes the 20 s buff.
        if (AuraEffect const* strength = GetAura()->GetEffect(EFFECT_1))
            player->CastCustomSpell(PaladinData::SPELL_BENEDICTION_BUFF, SPELLVALUE_BASE_POINT0,
                strength->GetAmount(), player, TRIGGERED_FULL_MASK);

        if (GetId() == PaladinData::SPELL_BENEDICTION_20103)
            HandleCapstone(player);
    }

    // Party members within range below 50% mana regain 10% of their own base mana.
    static void HandleCapstone(Player* player)
    {
        Group* group = player->GetGroup();
        if (!group)
            return;

        for (GroupReference* ref = group->GetFirstMember(); ref; ref = ref->next())
        {
            Player* member = ref->GetSource();
            if (!member || member == player || !member->IsAlive() || member->getPowerType() != POWER_MANA)
                continue;

            if (!player->IsWithinDistInMap(member, BENEDICTION_CAPSTONE_RANGE))
                continue;

            uint32 const maxMana = member->GetMaxPower(POWER_MANA);
            uint32 const belowPct = uint32(BENEDICTION_CAPSTONE_MANA_BELOW_PCT);
            if (!maxMana || member->GetPower(POWER_MANA) * 100 >= maxMana * belowPct)
                continue;

            member->EnergizeBySpell(member, PaladinData::SPELL_BENEDICTION_20103,
                CalculatePct(member->GetCreateMana(), BENEDICTION_CAPSTONE_MANA_PCT), POWER_MANA);
        }
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pal_benediction::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// -9799 - Eye for an Eye (capstone: rank-gated, crossing 50% health) - RETRIBUTION §6.8
// ===========================================================================================
class spell_pal_eye_for_an_eye_ret : public AuraScript
{
    PrepareAuraScript(spell_pal_eye_for_an_eye_ret);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_EYE_FOR_AN_EYE_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // Only the capstone rank (Talent.dbc chain rank 3) carries the effect.
        if (GetSpellInfo()->GetRank() != EYE_FOR_AN_EYE_CAPSTONE_RANK)
            return false;

        DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
        Unit* victim = GetTarget();
        if (!damageInfo || !damageInfo->GetDamage() || !victim || !victim->GetMaxHealth())
            return false;

        // TAKEN_DAMAGE procs fire after the health change: rebuild the health before the hit.
        float const maxHealth = float(victim->GetMaxHealth());
        float const after = victim->GetHealthPct();
        float const before = 100.0f * (float(victim->GetHealth()) + float(damageInfo->GetDamage())) / maxHealth;
        return before > EYE_FOR_AN_EYE_HEALTH_PCT && after <= EYE_FOR_AN_EYE_HEALTH_PCT && after > 0.0f;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        // The 60 s internal cooldown is the spell_proc row's.
        PreventDefaultAction();

        Unit* victim = GetTarget();
        victim->CastSpell(victim, PaladinData::SPELL_EYE_FOR_AN_EYE_BUFF, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_eye_for_an_eye_ret::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_eye_for_an_eye_ret::HandleProc, EFFECT_0,
            SPELL_AURA_MOD_CUSTOM_STAT_PCT);
    }
};

// ===========================================================================================
// 201471 - Divine Purpose (capstone lethal save) - RETRIBUTION §6.9
// ===========================================================================================
class spell_pal_divine_purpose_ret : public AuraScript
{
    PrepareAuraScript(spell_pal_divine_purpose_ret);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_DIVINE_SHIELD, PaladinData::SPELL_FORBEARANCE,
            SPELL_DIVINE_SHIELD_EXCLUDE_AURA });
    }

    bool Load() override
    {
        return GetUnitOwner()->IsPlayer();
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // Unlimited absorb (Ardent Defender shape).
        amount = -1;
    }

    void Absorb(AuraEffect* /*aurEff*/, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        // The default would absorb everything: only a lethal hit with Divine Shield available is absorbed.
        absorbAmount = 0;

        Player* player = GetPlayer(GetTarget());
        if (!player || dmgInfo.GetDamage() < player->GetHealth())
            return;

        // Known, off cooldown, and not under Forbearance (61988 is the "Divine Shield Exclude Aura"
        // Divine Shield and Hand of Protection apply; redundant with Forbearance but mirrors a manual cast).
        if (!player->HasSpell(PaladinData::SPELL_DIVINE_SHIELD)
            || player->HasSpellCooldown(PaladinData::SPELL_DIVINE_SHIELD)
            || player->HasAura(PaladinData::SPELL_FORBEARANCE)
            || player->HasAura(SPELL_DIVINE_SHIELD_EXCLUDE_AURA))
            return;

        absorbAmount = dmgInfo.GetDamage();

        // Not "ignore cooldown": 642's cooldown must start on this triggered cast and spell_pal_immunities
        // adds Forbearance. The explicit TriggerCastFlags(...) is required: the `&` result is an int that
        // would otherwise select the `bool triggered` overload (full mask, no cooldown).
        player->CastSpell(player, PaladinData::SPELL_DIVINE_SHIELD,
            TriggerCastFlags(TRIGGERED_FULL_MASK & ~TRIGGERED_IGNORE_SPELL_AND_CATEGORY_CD));

        // Fallback (CORE-AUDIT §6): a triggered cast that skipped its cooldown start.
        if (!player->HasSpellCooldown(PaladinData::SPELL_DIVINE_SHIELD))
            if (SpellInfo const* shield = sSpellMgr->GetSpellInfo(PaladinData::SPELL_DIVINE_SHIELD))
                player->AddSpellAndCategoryCooldowns(shield, 0);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_divine_purpose_ret::CalculateAmount, EFFECT_2,
            SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_pal_divine_purpose_ret::Absorb, EFFECT_2);
    }
};

// ===========================================================================================
// 20164 - Seal of Justice (Pursuit of Justice speed while the seal is active) - RETRIBUTION §6.11
// ===========================================================================================
class spell_pal_pursuit_of_justice_seal : public AuraScript
{
    PrepareAuraScript(spell_pal_pursuit_of_justice_seal);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_PURSUIT_OF_JUSTICE_SPEED });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetPlayer(GetTarget());
        if (!player)
            return;

        // The speed percent is the rank's second effect (10/20); only an active seal counts, not Primed.
        AuraEffect const* rank = player->GetAuraEffect(PaladinData::SPELL_PURSUIT_OF_JUSTICE_26023, EFFECT_1);
        if (!rank)
            rank = player->GetAuraEffect(PaladinData::SPELL_PURSUIT_OF_JUSTICE, EFFECT_1);

        if (rank)
            player->CastCustomSpell(PaladinData::SPELL_PURSUIT_OF_JUSTICE_SPEED, SPELLVALUE_BASE_POINT0,
                rank->GetAmount(), player, TRIGGERED_FULL_MASK);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetPlayer(GetTarget()))
            player->RemoveAurasDueToSpell(PaladinData::SPELL_PURSUIT_OF_JUSTICE_SPEED);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_pursuit_of_justice_seal::HandleApply, EFFECT_FIRST_FOUND,
            SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_pursuit_of_justice_seal::HandleRemove,
            EFFECT_FIRST_FOUND, SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// ===========================================================================================
// 1044 - Hand of Freedom (Pursuit of Justice capstone) - RETRIBUTION §6.11
// ===========================================================================================
class spell_pal_pursuit_of_justice_freedom : public SpellScript
{
    PrepareSpellScript(spell_pal_pursuit_of_justice_freedom);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_PURSUIT_OF_JUSTICE_FREEDOM });
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Player* caster = GetPlayer(GetCaster());
        Unit* target = GetHitUnit();
        if (!caster || !target || !caster->HasAura(PaladinData::SPELL_PURSUIT_OF_JUSTICE_26023))
            return;

        target->RemoveAurasWithMechanic(1 << MECHANIC_STUN);
        // 6 s, Hand of Freedom's own duration.
        caster->CastSpell(target, PaladinData::SPELL_PURSUIT_OF_JUSTICE_FREEDOM, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_pal_pursuit_of_justice_freedom::HandleHit, EFFECT_0,
            SPELL_EFFECT_APPLY_AURA);
    }
};

// ===========================================================================================
// 201434 - Sheath of Light capstone (Flash of Light on yourself restores mana) - RETRIBUTION §6.13
// ===========================================================================================
class spell_pal_sheath_of_light_capstone : public AuraScript
{
    PrepareAuraScript(spell_pal_sheath_of_light_capstone);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // The row restricts the spell to Flash of Light; only a heal on yourself counts.
        return eventInfo.GetHealInfo() && eventInfo.GetActionTarget() == GetTarget();
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        // eff0 is a DUMMY proc carrier (trigger 0): never run the default trigger path. The 10 s
        // internal cooldown is the row's.
        PreventDefaultAction();

        Player* player = GetPlayer(GetTarget());
        if (player)
            player->EnergizeBySpell(player, GetId(),
                CalculatePct(player->GetCreateMana(), SHEATH_OF_LIGHT_CAPSTONE_MANA_PCT), POWER_MANA);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_sheath_of_light_capstone::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_sheath_of_light_capstone::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// ===========================================================================================
// 201430 - Crusader's Aegis (absorb spell-power scaling) - RETRIBUTION §4.6
// ===========================================================================================
class spell_pal_crusaders_aegis_absorb : public AuraScript
{
    PrepareAuraScript(spell_pal_crusaders_aegis_absorb);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        // SCHOOL_ABSORB gets no engine spell-power bonus: add the generated coefficient x healing power.
        if (Unit* caster = GetCaster())
            amount += Paladin::CalculateAbsorbBonus(caster, aurEff, amount);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_crusaders_aegis_absorb::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// ===========================================================================================
// -20335 - Heart of the Crusader (replaces stock spell_pal_heart_of_the_crusader) - user ruling
// ===========================================================================================
class spell_pal_heart_of_the_crusader_ret : public AuraScript
{
    PrepareAuraScript(spell_pal_heart_of_the_crusader_ret);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HEART_OF_THE_CRUSADER_21183,
            PaladinData::SPELL_HEART_OF_THE_CRUSADER_54498, PaladinData::SPELL_HEART_OF_THE_CRUSADER_54499 });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        // 21183 has no spell_ranks chain, so GetSpellWithRank would always give rank 1: pick the
        // debuff by the talent rank of this aura's own spell (Talent.dbc chain).
        static constexpr std::array<uint32, 3> debuffs =
        {
            PaladinData::SPELL_HEART_OF_THE_CRUSADER_21183, PaladinData::SPELL_HEART_OF_THE_CRUSADER_54498,
            PaladinData::SPELL_HEART_OF_THE_CRUSADER_54499
        };

        uint8 const rank = GetSpellInfo()->GetRank();
        Unit* actor = eventInfo.GetActor();
        Unit* target = eventInfo.GetActionTarget();
        if (!actor || !target || rank < 1 || rank > debuffs.size())
            return;

        actor->CastSpell(target, debuffs[rank - 1], true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pal_heart_of_the_crusader_ret::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

void AddSC_paladin_retribution_spell_scripts()
{
    Paladin::RegisterRetributionHooks();

    RegisterSpellScript(spell_pal_blade_of_justice);
    RegisterSpellScript(spell_pal_execution_sentence);
    RegisterSpellScript(spell_pal_execution_sentence_burst);
    RegisterSpellScript(spell_pal_wake_of_ashes);
    RegisterSpellScript(spell_pal_divine_storm_ret);
    RegisterSpellScript(spell_pal_crusader_strike_ret);
    RegisterSpellScript(spell_pal_conviction);
    RegisterSpellScript(spell_pal_vindication);
    RegisterSpellScript(spell_pal_art_of_war);
    RegisterSpellScript(spell_pal_judgements_of_the_wise_guard);
    RegisterSpellScript(spell_pal_benediction);
    RegisterSpellScript(spell_pal_eye_for_an_eye_ret);
    RegisterSpellScript(spell_pal_divine_purpose_ret);
    RegisterSpellScript(spell_pal_pursuit_of_justice_seal);
    RegisterSpellScript(spell_pal_pursuit_of_justice_freedom);
    RegisterSpellScript(spell_pal_sheath_of_light_capstone);
    RegisterSpellScript(spell_pal_crusaders_aegis_absorb);
    RegisterSpellScript(spell_pal_heart_of_the_crusader_ret);
}
