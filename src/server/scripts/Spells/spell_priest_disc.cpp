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
 * Priest Discipline rework (docs/reworks/priest-disc-rework.md,
 * .agents/plans/priest-rework/priest-rework.DISC.md) - every genuinely new script class this pass
 * needs (Reprieve, Martyrdom, Inner Focus's Mind Blast half, Absolution, Focused Will, Improved
 * Flash Heal's capstone, Aspiration's Power Infusion echo) goes here. Scriptnames prefixed
 * "spell_pri_", same convention as spell_priest.cpp / spell_priest_new.cpp. Talents that only
 * retune an existing stock script (spell_pri_divine_aegis, spell_pri_power_word_shield,
 * spell_pri_power_word_shield_aura, spell_pri_penance, spell_pri_divine_star_pulse) are edited in
 * place in spell_priest.cpp / spell_priest_new.cpp instead - see DISC.md's "Stock scripts touched
 * by WP-B" list - and the hooks that can't be a SpellScript at all (Inner Focus's guaranteed Flash
 * Heal crit, Focused Power's Prayer of Healing capstone, Renewed Hope's crit bonus, Spirit Shell's
 * heal conversion) live in PriestMechanics.h/.cpp next to the core call sites that need them.
 *
 * Every talent value read at runtime here keys on the talent's own *rank spell id* (PLAN sec 3.10 -
 * never a talent_dbc id) rather than the marker-aura-by-icon idiom: every capstone in this pass
 * exists on its last rank only, which makes that rank's id the marker, and Absolution's per-rank
 * amount is reachable through the ranked-spell lookup. That keeps the C++ free of SpellIconID
 * literals that the data side would have to be kept in sync with.
 */

#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

enum PriestDiscSpells
{
    // Baseline spells these scripts key on by id.
    SPELL_PRIEST_DISPEL_MAGIC                   = 527,
    SPELL_PRIEST_WEAKENED_SOUL                  = 6788,
    SPELL_PRIEST_MIND_BLAST                     = 8092,
    SPELL_PRIEST_POWER_INFUSION                 = 10060,
    SPELL_PRIEST_INNER_FOCUS                    = 14751,
    SPELL_PRIEST_GREATER_HEAL                   = 2060,
    SPELL_PRIEST_FLASH_HEAL                     = 2061,
    SPELL_PRIEST_MASS_DISPEL                    = 32375,
    // 47757 is the outer Penance bolt spell cast by spell_pri_penance::HandleDummy - it only
    // triggers 47750, the spell that actually carries EffectHeal and is what proc/hit hooks see
    // (docs/bugs-and-fixes.md "A hardcoded spell-id allowlist keyed on a channeled ability's bolt
    // spell never matches"; same fix PriestMechanics.cpp already applies).
    SPELL_PRIEST_PENANCE_HEAL_BOLT              = 47750,

    // Talent rank spell ids (DISC.md's "Rank spell ids" column).
    SPELL_PRIEST_MARTYRDOM_R1                   = 14531,    // (1,2)
    SPELL_PRIEST_MARTYRDOM_R2                   = 14774,
    SPELL_PRIEST_ABSOLUTION_R1                  = 33167,    // (3,0)
    SPELL_PRIEST_FOCUSED_WILL_R3                = 45244,    // (6,0) rank 3 - Empowered Penance
    SPELL_PRIEST_ASPIRATION_R2                  = 47508,    // (7,2) rank 2 - Power Infusion echo
    SPELL_PRIEST_IMPROVED_FLASH_HEAL_R3         = 63506,    // (6,2) rank 3 - Inner Focus cooldown
    SPELL_PRIEST_REPRIEVE_R3                    = 200144,   // (1,0) rank 3 - Weakened Soul trim

    // Discipline rework spells (DISC.md "ID map").
    SPELL_PRIEST_MARTYRDOM_BUFF                 = 200145,
    SPELL_PRIEST_INNER_FOCUS_MIND_BLAST_SLOW    = 200146,
    SPELL_PRIEST_ABSOLUTION_BUFF                = 200153,
    SPELL_PRIEST_EMPOWERED_PENANCE_READY        = 200159
};

namespace
{
    // Reprieve (1,0) capstone: "Flash Heal and each bolt of Penance reduce the remaining duration
    // of Weakened Soul on the healed target by 0.5 sec. Greater Heal reduces it by 2 sec."
    constexpr int32 PRIEST_REPRIEVE_FAST_HEAL_REDUCTION_MS = 500;
    constexpr int32 PRIEST_REPRIEVE_GREATER_HEAL_REDUCTION_MS = 2000;

    // Martyrdom (1,2): "When you fall below 75% health..." Both sides of the crossing are checked,
    // so standing at 20% health and being hit again does not re-trigger it.
    constexpr int32 PRIEST_MARTYRDOM_HEALTH_PCT = 75;

    // Absolution (3,0): "Cannot occur more than once every 30 sec." A script-side cooldown rather
    // than a spell_proc one, because the trigger is a successful dispel rather than a proc event.
    constexpr uint32 PRIEST_ABSOLUTION_INTERNAL_COOLDOWN_MS = 30000;

    // Improved Flash Heal (6,2) capstone: "Flash Heal casts reduce the cooldown of Inner Focus by
    // 1 sec."
    constexpr uint32 PRIEST_IMPROVED_FLASH_HEAL_INNER_FOCUS_REDUCTION_MS = 1000;
}

/*
 * Reprieve (1,0) capstone - registered on rank 3's spell id only, which is where the capstone
 * exists, so the script needs no marker read of its own. The proc itself (Flash Heal / Greater
 * Heal / Penance's heal bolt) is declared on the data side; this only decides how much of Weakened
 * Soul to shave off, and only on the target that was healed.
 */
class spell_pri_reprieve : public AuraScript
{
    PrepareAuraScript(spell_pri_reprieve);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_WEAKENED_SOUL });
    }

    static int32 GetReductionFor(uint32 spellId)
    {
        switch (spellId)
        {
            case SPELL_PRIEST_FLASH_HEAL:
            case SPELL_PRIEST_PENANCE_HEAL_BOLT:
                return PRIEST_REPRIEVE_FAST_HEAL_REDUCTION_MS;
            case SPELL_PRIEST_GREATER_HEAL:
                return PRIEST_REPRIEVE_GREATER_HEAL_REDUCTION_MS;
            default:
                return 0;
        }
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        return eventInfo.GetProcTarget() && procSpell && GetReductionFor(procSpell->Id) != 0;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* target = eventInfo.GetProcTarget();
        // Any caster's Weakened Soul - the capstone text says "on the healed target", not "yours".
        Aura* weakenedSoul = target->GetAura(SPELL_PRIEST_WEAKENED_SOUL);
        if (!weakenedSoul)
            return;

        int32 remaining = weakenedSoul->GetDuration() - GetReductionFor(eventInfo.GetSpellInfo()->Id);
        if (remaining <= 0)
            target->RemoveAura(weakenedSoul);
        else
            weakenedSoul->SetDuration(remaining);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_reprieve::CheckProc);
        // The capstone rides on the rank's second effect (the first is the Weakened Soul duration
        // SpellMod every rank carries).
        OnEffectProc += AuraEffectProcFn(spell_pri_reprieve::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

/*
 * Martyrdom (1,2): "When you fall below 75% health, you gain Martyrdom, increasing your healing
 * done by 5/10% for 10 sec. Triggers on crossing the threshold and cannot occur more than once
 * every 30 sec." The 30 s lockout is the talent's own spell_proc cooldown; the crossing test is
 * here because no proc flag expresses it. Damage has already been applied to health by the time a
 * TAKEN_DAMAGE proc runs, hence the "health + damage was above, health is now below" shape.
 */
class spell_pri_martyrdom : public AuraScript
{
    PrepareAuraScript(spell_pri_martyrdom);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_MARTYRDOM_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || !damageInfo->GetDamage())
            return false;

        Unit* target = GetTarget();
        uint32 threshold = target->CountPctFromMaxHealth(PRIEST_MARTYRDOM_HEALTH_PCT);
        uint64 healthBefore = uint64(target->GetHealth()) + uint64(damageInfo->GetDamage());

        return target->GetHealth() < threshold && healthBefore >= threshold;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        target->CastCustomSpell(SPELL_PRIEST_MARTYRDOM_BUFF, SPELLVALUE_BASE_POINT0, aurEff->GetAmount(), target, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_martyrdom::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_martyrdom::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

/*
 * Inner Focus (2,1), Mind Blast clause: "Mind Blast: reduces cast time by 50% and slows the target
 * by 70% for 5 sec." The cast-time half is a plain SpellMod on the talent; only the slow needs a
 * script. Inner Focus is a one-charge aura consumed by the SpellMod pipeline during the cast, so
 * whether it was up has to be recorded in BeforeCast - by AfterHit the charge is already gone.
 * (The Flash Heal and Greater Heal clauses are pure data plus Priest::ApplySpellCritChanceMods;
 * the Power Word: Shield clause lives in spell_pri_power_word_shield.)
 */
class spell_pri_inner_focus_mind_blast : public SpellScript
{
    PrepareSpellScript(spell_pri_inner_focus_mind_blast);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_INNER_FOCUS, SPELL_PRIEST_INNER_FOCUS_MIND_BLAST_SLOW });
    }

    void RecordInnerFocus()
    {
        _innerFocus = GetCaster() && GetCaster()->HasAura(SPELL_PRIEST_INNER_FOCUS);
    }

    void HandleSlow()
    {
        if (!_innerFocus)
            return;

        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        caster->CastSpell(target, SPELL_PRIEST_INNER_FOCUS_MIND_BLAST_SLOW, true);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_pri_inner_focus_mind_blast::RecordInnerFocus);
        AfterHit += SpellHitFn(spell_pri_inner_focus_mind_blast::HandleSlow);
    }

private:
    bool _innerFocus = false;
};

/*
 * Absolution (3,0): "Dispelling or purging a magic effect grants Absolution, increasing your spell
 * critical strike chance by 8/16/25% for 10 sec. Cannot occur more than once every 30 sec."
 *
 * There is no "successful dispel" script hook in the core (Spell::EffectDispel calls nothing back
 * into SpellScript, and AuraScript's OnDispel/AfterDispel belong to the *dispelled* aura, which
 * could be anyone's). So the script snapshots how many dispellable charges the target had before
 * the effects ran - BeforeHit is called before Spell::HandleEffects - and compares afterwards:
 * fewer charges means at least one aura was actually stripped. Charges rather than aura count,
 * because a multi-charge aura can lose a charge and survive.
 */
class spell_pri_absolution : public SpellScript
{
    PrepareSpellScript(spell_pri_absolution);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_ABSOLUTION_BUFF });
    }

    uint32 CountDispellableCharges(Unit* caster, Unit* target)
    {
        uint32 charges = 0;
        for (uint8 i = EFFECT_0; i < MAX_SPELL_EFFECTS; ++i)
        {
            if (GetSpellInfo()->Effects[i].Effect != SPELL_EFFECT_DISPEL)
                continue;

            uint32 dispelMask = SpellInfo::GetDispelMask(DispelType(GetSpellInfo()->Effects[i].MiscValue));

            DispelChargesList dispelList;
            target->GetDispellableAuraList(caster, dispelMask, dispelList, GetSpellInfo());
            for (auto const& dispelPair : dispelList)
                charges += dispelPair.second;
        }

        return charges;
    }

    void SnapshotDispellable(SpellMissInfo missInfo)
    {
        // Reset unconditionally, before the miss check: Mass Dispel calls BeforeHit/AfterHit once
        // per target through this same script instance, so a miss/immune target here must not
        // leave a stale snapshot behind for RewardOnDispel to compare a *later* target against.
        _snapshotTaken = false;
        _chargesBefore = 0;

        if (missInfo != SPELL_MISS_NONE)
            return;

        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        _chargesBefore = CountDispellableCharges(caster, target);
        _snapshotTaken = true;
    }

    void RewardOnDispel()
    {
        if (!_snapshotTaken)
            return;

        // Consume the snapshot now - this target's AfterHit is the only thing that should ever
        // read it, and clearing it here (both the grant and no-grant paths) keeps a re-entrant or
        // out-of-order call from reusing it.
        _snapshotTaken = false;

        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        if (CountDispellableCharges(caster, target) >= _chargesBefore)
            return;

        if (caster->HasSpellCooldown(SPELL_PRIEST_ABSOLUTION_BUFF))
            return;

        // Rank 1 and rank 3 sit in the same ranked chain, so one lookup covers all three and the
        // dummy effect carries that rank's own crit bonus.
        AuraEffect const* talent = caster->GetAuraEffectOfRankedSpell(SPELL_PRIEST_ABSOLUTION_R1, EFFECT_0);
        if (!talent)
            return;

        caster->AddSpellCooldown(SPELL_PRIEST_ABSOLUTION_BUFF, 0, PRIEST_ABSOLUTION_INTERNAL_COOLDOWN_MS);
        caster->CastCustomSpell(SPELL_PRIEST_ABSOLUTION_BUFF, SPELLVALUE_BASE_POINT0, talent->GetAmount(), caster, true);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_pri_absolution::SnapshotDispellable);
        AfterHit += SpellHitFn(spell_pri_absolution::RewardOnDispel);
    }

private:
    uint32 _chargesBefore = 0;
    bool _snapshotTaken = false;
};

/*
 * Focused Will (6,0) capstone: "Your Flash Heal and Greater Heal have a 5% chance to empower your
 * next Penance." Registered on rank 3's spell id only - the capstone dummy exists nowhere else -
 * and the 5% chance plus the Flash Heal / Greater Heal scoping are the talent's own spell_proc
 * row, so the Proc Chance stat is folded in automatically (PLAN sec 3.8). What Empowered Penance
 * then does lives in spell_pri_penance (spell_priest.cpp), which consumes the ready buff.
 */
class spell_pri_focused_will : public AuraScript
{
    PrepareAuraScript(spell_pri_focused_will);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_EMPOWERED_PENANCE_READY });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        target->CastSpell(target, SPELL_PRIEST_EMPOWERED_PENANCE_READY, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_focused_will::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

/*
 * Improved Flash Heal (6,2) capstone: "Flash Heal casts reduce the cooldown of Inner Focus by
 * 1 sec." Registered on Flash Heal itself, gated on rank 3's spell id.
 *
 * Done as clear-then-set rather than Player::ModifySpellCooldown: the SMSG_MODIFY_COOLDOWN delta
 * that function sends was confirmed on this fork to have no client-side effect at all (see the
 * comment above Player::ApplyCooldownHasteCorrection in Player.cpp), which would leave the
 * cooldown moving server-side while the client kept showing the old timer.
 */
class spell_pri_improved_flash_heal_capstone : public SpellScript
{
    PrepareSpellScript(spell_pri_improved_flash_heal_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_INNER_FOCUS });
    }

    void ReduceInnerFocusCooldown()
    {
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!caster || !caster->HasAura(SPELL_PRIEST_IMPROVED_FLASH_HEAL_R3))
            return;

        uint32 remaining = caster->GetSpellCooldownDelay(SPELL_PRIEST_INNER_FOCUS);
        if (!remaining)
            return;

        uint32 corrected = remaining > PRIEST_IMPROVED_FLASH_HEAL_INNER_FOCUS_REDUCTION_MS
                           ? remaining - PRIEST_IMPROVED_FLASH_HEAL_INNER_FOCUS_REDUCTION_MS
                           : 0;
        caster->ApplyCooldownHasteCorrection(SPELL_PRIEST_INNER_FOCUS, 0, corrected);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_pri_improved_flash_heal_capstone::ReduceInnerFocusCooldown);
    }
};

/*
 * Aspiration (7,2) capstone: "Casting Power Infusion on an ally also applies Power Infusion to
 * you." Registered on Power Infusion itself and gated on rank 2's spell id, so no marker is
 * needed. The self-cast's own hit unit *is* the caster, so the `hit unit != caster` guard is also
 * what stops it recursing. TRIGGERED_FULL_MASK skips the mana cost and neither checks nor starts
 * the 2 min cooldown (Spell.cpp's TRIGGERED_IGNORE_SPELL_AND_CATEGORY_CD), and 10060 carries no
 * "limit to N targets" attribute, so the ally's and the caster's buffs coexist.
 */
class spell_pri_aspiration_power_infusion : public SpellScript
{
    PrepareSpellScript(spell_pri_aspiration_power_infusion);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_POWER_INFUSION });
    }

    void HandleSelfInfusion()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || target == caster)
            return;

        if (!caster->HasAura(SPELL_PRIEST_ASPIRATION_R2))
            return;

        caster->CastSpell(caster, SPELL_PRIEST_POWER_INFUSION, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_pri_aspiration_power_infusion::HandleSelfInfusion);
    }
};

void AddSC_priest_disc_spell_scripts()
{
    RegisterSpellScript(spell_pri_absolution);
    RegisterSpellScript(spell_pri_aspiration_power_infusion);
    RegisterSpellScript(spell_pri_focused_will);
    RegisterSpellScript(spell_pri_improved_flash_heal_capstone);
    RegisterSpellScript(spell_pri_inner_focus_mind_blast);
    RegisterSpellScript(spell_pri_martyrdom);
    RegisterSpellScript(spell_pri_reprieve);
}
