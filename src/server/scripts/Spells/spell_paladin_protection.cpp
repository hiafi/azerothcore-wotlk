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
 * Paladin rework - Protection tree scripts
 * (.agents/plans/paladin-rework/paladin-rework.PROTECTION.md §2.7, behaviour in §4-§6).
 *
 * Script names must match WP-A's bindings byte for byte. Stock spell_paladin.cpp stays unedited. The
 * Paladin:: Protection section (Bulwark state, internal cooldowns, hooks) is in PaladinMechanics.cpp.
 */

#include "PaladinMechanics.h"
#include "Generated/PaladinData.h"
#include "HealMechanics.h"
#include "Player.h"
#include "PriestMechanics.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <vector>

namespace
{
    // Stock ids the DSL never declares (hand literals, WarlockMechanics.h convention)
    enum PaladinProtectionStockSpells
    {
        SPELL_PAL_ARDENT_DEFENDER_HEAL        = 66235,  // self heal, bp from script
        SPELL_PAL_BLESSING_OF_SANCTUARY_BUFF  = 67480   // the blessing's stat / mana-return carrier
    };

    constexpr float   LIGHTS_RESERVOIR_RANGE        = 30.0f;
    constexpr uint8   LIGHTS_RESERVOIR_CANDIDATES   = 100;     // SelectMostInjured trims before the LoS filter
    constexpr int32   RADIANT_ABSORB_CAP_PCT        = 50;      // of max health
    constexpr float   SANCTUARY_BASE_MANA_PCT       = 6.0f;    // of base mana, before Improved BoS
    constexpr uint32  DIVINE_SACRIFICE_THRESHOLD_PCT = 5;      // of max health redirected per Bulwark stack
    constexpr int32   SHIELD_OF_THE_TEMPLAR_REFUND_MS = 1000;
    constexpr uint32  ARDENT_DEFENDER_BELOW_HEALTH_PCT = 35;

    Player* GetPlayerOrNull(Unit* unit)
    {
        return unit ? unit->ToPlayer() : nullptr;
    }
}

// 201360 - Bulwark: the buff is the resource; its removal (expiry, death, click-off, Holy Light) drops the instant cast
class spell_pal_bulwark : public AuraScript
{
    PrepareAuraScript(spell_pal_bulwark);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_RADIANT_BULWARK_BUFF });
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        GetTarget()->RemoveAurasDueToSpell(PaladinData::SPELL_RADIANT_BULWARK_BUFF);
    }

    void Register() override
    {
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_bulwark::HandleRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// 201361 - Bulwark (grant): the one stack granter shared by Anticipation, Vengeful Bulwark, Bulwark of Faith,
// Touched by the Light's block capstone and Guardian of Ancient Kings' periodic
class spell_pal_bulwark_grant : public SpellScript
{
    PrepareSpellScript(spell_pal_bulwark_grant);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_BULWARK });
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        if (Player* player = GetPlayerOrNull(GetCaster()))
            Paladin::GrantBulwark(player, 1);
    }

    void Register() override
    {
        OnEffectHit += SpellEffectFn(spell_pal_bulwark_grant::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
    }
};

// 635 - Holy Light (no other script on the id): consumes the whole Bulwark bar (PROTECTION §6.1)
class spell_pal_holy_light_bulwark : public SpellScript
{
    PrepareSpellScript(spell_pal_holy_light_bulwark);

    uint8 _stacks = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_BULWARK, PaladinData::SPELL_RADIANT_BULWARK_BUFF,
            PaladinData::SPELL_TOUCHED_BY_THE_LIGHT_53592 });
    }

    // After the cast bar (cost and cast time were fixed at prepare, with 201362 present)
    void HandleBeforeCast()
    {
        _stacks = 0;
        if (Player* player = GetPlayerOrNull(GetCaster()))
            _stacks = Paladin::GetBulwarkStacks(player);
    }

    // Post done and post %-taken mods, pre-crit: a multiplier is exact. Only a self heal with Touched by the Light r3
    void HandleHit()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        if (!player || !_stacks || GetHitUnit() != player)
            return;

        float const multiplier = Paladin::GetBulwarkHealMultiplier(player, _stacks);
        if (multiplier != 1.0f)
            SetHitHeal(int32(float(GetHitHeal()) * multiplier));
    }

    void HandleAfterCast()
    {
        if (!_stacks)
            return;

        if (Player* player = GetPlayerOrNull(GetCaster()))
            Paladin::ConsumeBulwark(player);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_pal_holy_light_bulwark::HandleBeforeCast);
        OnHit += SpellHitFn(spell_pal_holy_light_bulwark::HandleHit);
        AfterCast += SpellCastFn(spell_pal_holy_light_bulwark::HandleAfterCast);
    }
};

// 201343, 201344, 201345 - Radiant Bulwark: overheal of the instant Holy Light on yourself becomes an absorb
class spell_pal_radiant_bulwark : public AuraScript
{
    PrepareAuraScript(spell_pal_radiant_bulwark);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_LIGHT, PaladinData::SPELL_RADIANT_BULWARK_BUFF,
            PaladinData::SPELL_RADIANT_BULWARK_ABSORB });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        SpellInfo const* info = eventInfo.GetSpellInfo();
        HealInfo* healInfo = eventInfo.GetHealInfo();
        if (!owner || !info || !healInfo || info->Id != PaladinData::SPELL_HOLY_LIGHT)
            return false;

        if (eventInfo.GetActor() != owner || eventInfo.GetActionTarget() != owner)
            return false;

        // This Holy Light consumed a 5-stack bar (201362 is still up in the HIT phase, §6.1 step 3)
        return owner->HasAura(PaladinData::SPELL_RADIANT_BULWARK_BUFF) &&
            healInfo->GetHeal() > healInfo->GetEffectiveHeal();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5

        Player* owner = GetPlayerOrNull(GetTarget());
        HealInfo* healInfo = eventInfo.GetHealInfo();
        if (!owner || !healInfo)
            return;

        int32 const overheal = int32(healInfo->GetHeal()) - int32(healInfo->GetEffectiveHeal());
        int32 const fresh = CalculatePct(overheal, aurEff->GetAmount());

        // Highest wins, duration always refreshed
        AuraEffect const* current = owner->GetAuraEffect(PaladinData::SPELL_RADIANT_BULWARK_ABSORB, EFFECT_0);
        int32 const kept = current ? std::max(0, current->GetAmount()) : 0;
        int32 const amount = std::min(int32(owner->CountPctFromMaxHealth(RADIANT_ABSORB_CAP_PCT)),
            std::max(kept, fresh));
        if (amount <= 0)
            return;

        owner->RemoveAurasDueToSpell(PaladinData::SPELL_RADIANT_BULWARK_ABSORB);
        owner->CastCustomSpell(PaladinData::SPELL_RADIANT_BULWARK_ABSORB, SPELLVALUE_BASE_POINT0, amount, owner,
            TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_radiant_bulwark::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_radiant_bulwark::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 53590, 53591, 53592 - Touched by the Light: effective direct healing from another player grants the buff
class spell_pal_touched_by_the_light : public AuraScript
{
    PrepareAuraScript(spell_pal_touched_by_the_light);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_TOUCHED_BY_THE_LIGHT_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        HealInfo* healInfo = eventInfo.GetHealInfo();
        Unit* actor = eventInfo.GetActor();
        if (!owner || !healInfo || !actor || actor == owner || healInfo->GetEffectiveHeal() == 0)
            return false;

        // Direct heals only (P3 #70)
        if (eventInfo.GetTypeMask() & PROC_FLAG_TAKEN_PERIODIC)
            return false;

        // Another player, or their pet / totem
        return actor->GetCharmerOrOwnerPlayerOrPlayerItself() != nullptr;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction(); // X5

        Player* owner = GetPlayerOrNull(GetTarget());
        if (!owner)
            return;

        owner->CastCustomSpell(PaladinData::SPELL_TOUCHED_BY_THE_LIGHT_BUFF, SPELLVALUE_BASE_POINT0,
            aurEff->GetAmount(), owner, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_touched_by_the_light::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_touched_by_the_light::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 201364 - Touched by the Light (buff): aura 283 boosts the next self direct heal; the HIT row spends the charge and
// grants Shroud of Light (8 s internal cooldown)
class spell_pal_touched_by_the_light_buff : public AuraScript
{
    PrepareAuraScript(spell_pal_touched_by_the_light_buff);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_SHROUD_OF_LIGHT_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        return owner && eventInfo.GetActor() == owner && eventInfo.GetActionTarget() == owner;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction(); // X5

        Player* owner = GetPlayerOrNull(GetTarget());
        if (!owner)
            return;

        if (Paladin::TryStartInternalCooldown(owner, PaladinData::SPELL_SHROUD_OF_LIGHT_BUFF,
            Paladin::SHROUD_OF_LIGHT_ICD_MS))
            owner->CastSpell(owner, PaladinData::SPELL_SHROUD_OF_LIGHT_BUFF, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_touched_by_the_light_buff::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_touched_by_the_light_buff::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 31935 - Avenger's Shield (beside S1's spell_pal_seal_builder): +2 Bulwark, and Avenging Light's two extra shields
class spell_pal_avengers_shield_prot : public SpellScript
{
    PrepareSpellScript(spell_pal_avengers_shield_prot);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_BULWARK, PaladinData::SPELL_AVENGING_LIGHT_BUFF,
            PaladinData::SPELL_AVENGERS_SHIELD_EXTRA });
    }

    // Speed 35: AfterCast precedes the hits, once per Spell instance
    void HandleAfterCast()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        if (!player)
            return;

        Paladin::GrantBulwark(player, 2);

        if (!player->HasAura(PaladinData::SPELL_AVENGING_LIGHT_BUFF))
            return;

        player->RemoveAurasDueToSpell(PaladinData::SPELL_AVENGING_LIGHT_BUFF);

        // The extras carry no Avenger's Shield bit and are not bound to the seal builder (one cast for stacks)
        Unit* target = GetExplTargetUnit();
        if (!target || !target->IsAlive())
            return;

        for (uint8 i = 0; i < 2; ++i)
            player->CastSpell(target, PaladinData::SPELL_AVENGERS_SHIELD_EXTRA, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_pal_avengers_shield_prot::HandleAfterCast);
    }
};

// 201353, 201354, 201355 - Avenging Light: Holy Shield blocks may reset Avenger's Shield and arm the triple throw
class spell_pal_avenging_light : public AuraScript
{
    PrepareAuraScript(spell_pal_avenging_light);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_SHIELD, PaladinData::SPELL_AVENGER_S_SHIELD,
            PaladinData::SPELL_AVENGING_LIGHT_BUFF });
    }

    // Collected before Holy Shield's last charge is spent (CheckProc runs in the collection pass)
    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        return owner && owner->HasAura(PaladinData::SPELL_HOLY_SHIELD, owner->GetGUID());
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction(); // X5

        Player* owner = GetPlayerOrNull(GetTarget());
        if (!owner)
            return;

        owner->RemoveSpellCooldown(PaladinData::SPELL_AVENGER_S_SHIELD, true);
        owner->CastSpell(owner, PaladinData::SPELL_AVENGING_LIGHT_BUFF, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_avenging_light::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_avenging_light::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 201070, 201076 - Seal of Command unleashes (beside spell_pal_seal_unleash): Improved Seal of Command's capstone DoT
class spell_pal_improved_soc_dot : public SpellScript
{
    PrepareSpellScript(spell_pal_improved_soc_dot);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_IMPROVED_SEAL_OF_COMMAND_201330,
            PaladinData::SPELL_IMPROVED_SOC_DOT });
    }

    void HandleAfterHit()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target || !target->IsAlive() ||
            !player->HasAura(PaladinData::SPELL_IMPROVED_SEAL_OF_COMMAND_201330))
            return;

        // A same-caster recast replaces, so the main target (201076 + 201070) still carries one DoT
        player->CastSpell(target, PaladinData::SPELL_IMPROVED_SOC_DOT, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_pal_improved_soc_dot::HandleAfterHit);
    }
};

// 201140 - Consecration tick (beside SHARED's tick usage): Improved Consecration's attack-speed slow
class spell_pal_improved_consecration_slow : public SpellScript
{
    PrepareSpellScript(spell_pal_improved_consecration_slow);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_IMPROVED_CONSECRATION,
            PaladinData::SPELL_IMPROVED_CONSECRATION_201324, PaladinData::SPELL_IMPROVED_CONSECRATION_201325,
            PaladinData::SPELL_IMPROVED_CONSECRATION_SLOW });
    }

    void HandleAfterHit()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        Unit* target = GetHitUnit();
        if (!player || !target || !target->IsAlive())
            return;

        // Rank eff1 = slow percent (live 6 / 13 / 20)
        int32 const slow = Paladin::GetRankAmount(player, { PaladinData::SPELL_IMPROVED_CONSECRATION_201325,
            PaladinData::SPELL_IMPROVED_CONSECRATION_201324, PaladinData::SPELL_IMPROVED_CONSECRATION }, EFFECT_1);
        if (slow <= 0)
            return;

        player->CastCustomSpell(PaladinData::SPELL_IMPROVED_CONSECRATION_SLOW, SPELLVALUE_BASE_POINT0, -slow, target,
            TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_pal_improved_consecration_slow::HandleAfterHit);
    }
};

// 64205 - Divine Sacrifice (replaces stock spell_pal_divine_sacrifice): 40% cap, +1 Bulwark per 5% max health
// redirected
class spell_pal_divine_sacrifice_prot : public AuraScript
{
    PrepareAuraScript(spell_pal_divine_sacrifice_prot);

    int32 _remaining = 0;
    uint32 _minHpPct = 0;
    uint32 _threshold = 0;
    uint32 _redirected = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_BULWARK });
    }

    bool Load() override
    {
        Player* caster = GetPlayerOrNull(GetCaster());
        if (!caster)
            return false;

        _remaining = int32(caster->CountPctFromMaxHealth(GetSpellInfo()->Effects[EFFECT_2].CalcValue(caster)));
        _minHpPct = uint32(GetSpellInfo()->Effects[EFFECT_1].CalcValue(caster));
        _threshold = caster->CountPctFromMaxHealth(DIVINE_SACRIFICE_THRESHOLD_PCT);
        _redirected = 0;
        return true;
    }

    void HandleSplit(AuraEffect* /*aurEff*/, DamageInfo& /*dmgInfo*/, uint32& splitAmount)
    {
        Player* caster = GetPlayerOrNull(GetCaster());
        if (!caster)
            return;

        _remaining -= int32(splitAmount);
        _redirected += splitAmount;
        while (_threshold && _redirected >= _threshold)
        {
            Paladin::GrantBulwark(caster, 1);
            _redirected -= _threshold;
        }

        // Break when the cap is used up, or when the caster's health drops below the threshold
        if (_remaining <= 0 || caster->GetHealthPct() < float(_minHpPct))
            caster->RemoveAurasDueToSpell(PaladinData::SPELL_DIVINE_SACRIFICE);
    }

    void Register() override
    {
        OnEffectSplit += AuraEffectSplitFn(spell_pal_divine_sacrifice_prot::HandleSplit, EFFECT_0);
    }
};

// 31850, 31851, 31852 - Ardent Defender (replaces stock spell_pal_ardent_defender): no defense scaling, scripted
// lethal-save roll, other finite absorbs counted before declaring a hit lethal
class spell_pal_ardent_defender_prot : public AuraScript
{
    PrepareAuraScript(spell_pal_ardent_defender_prot);

    uint32 _belowPct = 0;   // eff0 live: reduction of the damage below 35% health
    int32 _saveChance = 0;  // eff1 live
    int32 _healPct = 0;     // eff2 live

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PAL_ARDENT_DEFENDER_HEAL, PaladinData::SPELL_ARDENT_DEFENDER_BUFF,
            Priest::SPELL_CHEATED_DEATH_MARKER });
    }

    bool Load() override
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer())
            return false;

        SpellInfo const* info = GetSpellInfo();
        _belowPct = uint32(std::max(0, info->Effects[EFFECT_0].CalcValue()));
        _saveChance = info->Effects[EFFECT_1].CalcValue();
        _healPct = info->Effects[EFFECT_2].CalcValue();
        return true;
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = -1; // unlimited
    }

    // Remaining amount of the victim's other finite school absorbs that match the hit (absorb order is unspecified)
    static uint32 CountOtherFiniteAbsorbs(Unit const* victim, AuraEffect const* self, DamageInfo const& dmgInfo)
    {
        uint32 total = 0;
        for (AuraEffect const* effect : victim->GetAuraEffectsByType(SPELL_AURA_SCHOOL_ABSORB))
        {
            if (effect == self || effect->GetAmount() <= 0)
                continue;

            if (effect->GetMiscValue() & dmgInfo.GetSchoolMask())
                total += uint32(effect->GetAmount());
        }

        return total;
    }

    void HandleAbsorb(AuraEffect* aurEff, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        Player* victim = GetPlayerOrNull(GetTarget());
        if (!victim)
            return;

        int64 const remainingHealth = int64(victim->GetHealth()) - int64(dmgInfo.GetDamage());
        uint32 const allowedHealth = victim->CountPctFromMaxHealth(ARDENT_DEFENDER_BELOW_HEALTH_PCT);

        bool const lethal = remainingHealth + int64(CountOtherFiniteAbsorbs(victim, aurEff, dmgInfo)) <= 0;
        if (lethal && !victim->HasAura(Priest::SPELL_CHEATED_DEATH_MARKER) &&
            Paladin::RollScriptedChance(victim, float(_saveChance)))
        {
            // Completely avoid the damage, heal, buff and start the shared 2 min lockout
            absorbAmount = dmgInfo.GetDamage();

            victim->CastCustomSpell(SPELL_PAL_ARDENT_DEFENDER_HEAL, SPELLVALUE_BASE_POINT0,
                int32(victim->CountPctFromMaxHealth(_healPct)), victim, TRIGGERED_FULL_MASK, nullptr, aurEff);
            victim->CastSpell(victim, PaladinData::SPELL_ARDENT_DEFENDER_BUFF, TRIGGERED_FULL_MASK);
            victim->CastSpell(victim, Priest::SPELL_CHEATED_DEATH_MARKER, TRIGGERED_FULL_MASK);
        }
        else if (remainingHealth < int64(allowedHealth))
        {
            // Reduce the damage that brings us under 35% (all of it when already under) by x%
            uint32 const damageToReduce = victim->GetHealth() < allowedHealth ?
                dmgInfo.GetDamage() : uint32(int64(allowedHealth) - remainingHealth);
            absorbAmount = CalculatePct(damageToReduce, _belowPct);
        }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_ardent_defender_prot::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_pal_ardent_defender_prot::HandleAbsorb, EFFECT_0);
    }
};

// 498 - Divine Protection: Sacred Duty's capstone sets Bulwark to 5
class spell_pal_divine_protection_prot : public SpellScript
{
    PrepareSpellScript(spell_pal_divine_protection_prot);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_SACRED_DUTY_31849, PaladinData::SPELL_BULWARK });
    }

    void HandleAfterCast()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        if (player && player->HasAura(PaladinData::SPELL_SACRED_DUTY_31849))
            Paladin::GrantBulwark(player, Paladin::BULWARK_MAX_STACKS, true);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_pal_divine_protection_prot::HandleAfterCast);
    }
};

// 20911, 25899 - Blessing of Sanctuary (replaces stock spell_pal_blessing_of_sanctuary): 6% base mana, Improved BoS
class spell_pal_blessing_of_sanctuary_prot : public AuraScript
{
    PrepareAuraScript(spell_pal_blessing_of_sanctuary_prot);

    int32 _manaBonusPct = 0;    // Improved BoS eff1 live, snapshot of the caster's

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PAL_BLESSING_OF_SANCTUARY_BUFF, PaladinData::SPELL_BLESSING_OF_SANCTUARY_DR,
            PaladinData::SPELL_BLESSING_OF_SANCTUARY_MANA, PaladinData::SPELL_IMPROVED_BLESSING_OF_SANCTUARY,
            PaladinData::SPELL_IMPROVED_BLESSING_OF_SANCTUARY_201338 });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        Unit* caster = GetCaster();
        if (!caster)
            return;

        caster->CastSpell(target, SPELL_PAL_BLESSING_OF_SANCTUARY_BUFF, TRIGGERED_FULL_MASK);

        std::initializer_list<uint32> const ranks = { PaladinData::SPELL_IMPROVED_BLESSING_OF_SANCTUARY_201338,
            PaladinData::SPELL_IMPROVED_BLESSING_OF_SANCTUARY };
        int32 const dr = Paladin::GetRankAmount(caster, ranks, EFFECT_0);
        _manaBonusPct = Paladin::GetRankAmount(caster, ranks, EFFECT_1);

        // Recast so a reapply picks up the live value; the helper lives and dies with the blessing
        target->RemoveAura(PaladinData::SPELL_BLESSING_OF_SANCTUARY_DR, GetCasterGUID());
        if (dr > 0)
            caster->CastCustomSpell(PaladinData::SPELL_BLESSING_OF_SANCTUARY_DR, SPELLVALUE_BASE_POINT0, -dr, target,
                TRIGGERED_FULL_MASK);
    }

    void HandleEffectRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        target->RemoveAura(SPELL_PAL_BLESSING_OF_SANCTUARY_BUFF, GetCasterGUID());
        target->RemoveAura(PaladinData::SPELL_BLESSING_OF_SANCTUARY_DR, GetCasterGUID());
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        return GetTarget()->HasActivePowerType(POWER_MANA);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction(); // X5

        Unit* target = GetTarget();
        float const pct = SANCTUARY_BASE_MANA_PCT * (1.0f + float(_manaBonusPct) / 100.0f);
        int32 const amount = int32(float(target->GetCreateMana()) * pct / 100.0f);
        if (amount <= 0)
            return;

        target->CastCustomSpell(PaladinData::SPELL_BLESSING_OF_SANCTUARY_MANA, SPELLVALUE_BASE_POINT0, amount, target,
            TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_blessing_of_sanctuary_prot::HandleApply, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_blessing_of_sanctuary_prot::HandleEffectRemove, EFFECT_0,
            SPELL_AURA_DUMMY, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        DoCheckProc += AuraCheckProcFn(spell_pal_blessing_of_sanctuary_prot::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_blessing_of_sanctuary_prot::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 201374 - Shield of the Templar capstone (hidden passive linked from 53711): heals from others cut Divine Protection
class spell_pal_shield_of_the_templar_capstone : public AuraScript
{
    PrepareAuraScript(spell_pal_shield_of_the_templar_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_DIVINE_PROTECTION });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        HealInfo* healInfo = eventInfo.GetHealInfo();
        Unit* actor = eventInfo.GetActor();
        return owner && healInfo && actor && actor != owner && healInfo->GetHeal() > 0;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction(); // X5

        // Client-visible real seconds, never Cooldown Haste
        Player* owner = GetPlayerOrNull(GetTarget());
        if (owner && owner->HasSpellCooldown(PaladinData::SPELL_DIVINE_PROTECTION))
            owner->ModifySpellCooldown(PaladinData::SPELL_DIVINE_PROTECTION, -SHIELD_OF_THE_TEMPLAR_REFUND_MS);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_shield_of_the_templar_capstone::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_shield_of_the_templar_capstone::HandleProc, EFFECT_0,
            SPELL_AURA_DUMMY);
    }
};

// 201333, 201334 - Light's Reservoir: your own Holy Light / Flash of Light on yourself also heals the most injured
// other party member in range and line of sight
class spell_pal_lights_reservoir : public AuraScript
{
    PrepareAuraScript(spell_pal_lights_reservoir);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_LIGHT, PaladinData::SPELL_FLASH_OF_LIGHT,
            PaladinData::SPELL_LIGHTS_RESERVOIR_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* owner = GetPlayerOrNull(GetTarget());
        SpellInfo const* info = eventInfo.GetSpellInfo();
        HealInfo* healInfo = eventInfo.GetHealInfo();
        if (!owner || !info || !healInfo || healInfo->GetHeal() == 0)
            return false;

        if (info->Id != PaladinData::SPELL_HOLY_LIGHT && info->Id != PaladinData::SPELL_FLASH_OF_LIGHT)
            return false;

        return eventInfo.GetActor() == owner && eventInfo.GetActionTarget() == owner;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction(); // X5

        Player* owner = GetPlayerOrNull(GetTarget());
        HealInfo* healInfo = eventInfo.GetHealInfo();
        if (!owner || !healInfo)
            return;

        // Total heal including crit and Bulwark (P3 #71)
        int32 const amount = CalculatePct(int32(healInfo->GetHeal()), aurEff->GetAmount());
        if (amount <= 0)
            return;

        // SelectMostInjured trims to `count` before our LoS filter, so over-ask and take the first visible one
        std::vector<Unit*> candidates;
        Heal::SelectMostInjured(owner, owner, LIGHTS_RESERVOIR_RANGE, LIGHTS_RESERVOIR_CANDIDATES, candidates, owner);
        for (Unit* unit : candidates)
        {
            if (!unit->IsAlive() || !owner->IsWithinLOSInMap(unit))
                continue;

            owner->CastCustomSpell(PaladinData::SPELL_LIGHTS_RESERVOIR_HEAL, SPELLVALUE_BASE_POINT0, amount, unit,
                TRIGGERED_FULL_MASK, nullptr, aurEff);
            break;
        }
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_lights_reservoir::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_lights_reservoir::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 20145 - Tenacity (r3 capstone): armor from Strength goes stale on a Strength change, so refresh it every second
class spell_pal_tenacity_capstone : public AuraScript
{
    PrepareAuraScript(spell_pal_tenacity_capstone);

    void HandlePeriodic(AuraEffect const* /*aurEff*/)
    {
        if (Player* player = GetPlayerOrNull(GetTarget()))
            player->UpdateArmor();
    }

    void Register() override
    {
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pal_tenacity_capstone::HandlePeriodic, EFFECT_2,
            SPELL_AURA_PERIODIC_DUMMY);
    }
};

void AddSC_paladin_protection_spell_scripts()
{
    Paladin::RegisterProtectionHooks();

    RegisterSpellScript(spell_pal_bulwark);
    RegisterSpellScript(spell_pal_bulwark_grant);
    RegisterSpellScript(spell_pal_holy_light_bulwark);
    RegisterSpellScript(spell_pal_radiant_bulwark);
    RegisterSpellScript(spell_pal_touched_by_the_light);
    RegisterSpellScript(spell_pal_touched_by_the_light_buff);
    RegisterSpellScript(spell_pal_avengers_shield_prot);
    RegisterSpellScript(spell_pal_avenging_light);
    RegisterSpellScript(spell_pal_improved_soc_dot);
    RegisterSpellScript(spell_pal_improved_consecration_slow);
    RegisterSpellScript(spell_pal_divine_sacrifice_prot);
    RegisterSpellScript(spell_pal_ardent_defender_prot);
    RegisterSpellScript(spell_pal_divine_protection_prot);
    RegisterSpellScript(spell_pal_blessing_of_sanctuary_prot);
    RegisterSpellScript(spell_pal_shield_of_the_templar_capstone);
    RegisterSpellScript(spell_pal_lights_reservoir);
    RegisterSpellScript(spell_pal_tenacity_capstone);
}
