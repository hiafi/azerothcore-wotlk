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

#include "GridNotifiers.h"
#include "Group.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "TemporarySummon.h"
/*
 * Scripts for spells with SPELLFAMILY_PRIEST and SPELLFAMILY_GENERIC spells used by priest players.
 * Ordered alphabetically using scriptname.
 * Scriptnames of files in this file should be prefixed with "spell_pri_".
 */

enum PriestSpells
{
    SPELL_PRIEST_DIVINE_AEGIS                       = 47753,
    SPELL_PRIEST_EMPOWERED_RENEW                    = 63544,
    SPELL_PRIEST_GLYPH_OF_CIRCLE_OF_HEALING         = 55675,
    SPELL_PRIEST_GLYPH_OF_LIGHTWELL                 = 55673,
    SPELL_PRIEST_GLYPH_OF_PRAYER_OF_HEALING_HEAL    = 56161,
    SPELL_PRIEST_GUARDIAN_SPIRIT_HEAL               = 48153,
    SPELL_PRIEST_ITEM_EFFICIENCY                    = 37595,
    SPELL_PRIEST_LIGHTWELL_CHARGES                  = 59907,
    SPELL_PRIEST_MANA_LEECH_PROC                    = 34650,
    SPELL_PRIEST_PENANCE_R1                         = 47540,
    SPELL_PRIEST_PENANCE_R1_DAMAGE                  = 47758,
    SPELL_PRIEST_PENANCE_R1_HEAL                    = 47757,
    SPELL_PRIEST_REFLECTIVE_SHIELD_TRIGGERED        = 33619,
    SPELL_PRIEST_REFLECTIVE_SHIELD_R1               = 33201,
    SPELL_PRIEST_SHADOW_WORD_DEATH                  = 32409,
    SPELL_PRIEST_T9_HEALING_2P                      = 67201,
    SPELL_PRIEST_VAMPIRIC_TOUCH_DISPEL              = 64085,
    SPELL_PRIEST_T4_4P_FLEXIBILITY                  = 37565,
    SPELL_PRIEST_GLYPH_OF_SHADOWFIEND               = 58228,
    SPELL_PRIEST_GLYPH_OF_SHADOWFIEND_MANA          = 58227,

    SPELL_GENERIC_ARENA_DAMPENING                   = 74410,
    SPELL_GENERIC_BATTLEGROUND_DAMPENING            = 74411,
    SPELL_PRIEST_TWIN_DISCIPLINE_R1                 = 47586,
    SPELL_PRIEST_SPIRITUAL_HEALING_R1               = 14898,
    SPELL_PRIEST_DIVINE_PROVIDENCE_R1               = 47562
};

/*
 * Discipline rework (docs/reworks/priest-disc-rework.md,
 * .agents/plans/priest-rework/priest-rework.DISC.md) - ids the reworked stock scripts below need.
 * Talent entries are the *rank spell* ids from DISC.md's "Rank spell ids" column, never talent_dbc
 * ids (PLAN sec 3.10).
 */
enum PriestDiscSpells
{
    SPELL_PRIEST_POWER_WORD_SHIELD                  = 17,
    SPELL_PRIEST_WEAKENED_SOUL                      = 6788,

    // Talent rank spell ids.
    SPELL_PRIEST_INNER_FOCUS                        = 14751,    // (2,1), single rank
    SPELL_PRIEST_IMPROVED_POWER_WORD_SHIELD_R3      = 14769,    // (2,2) rank 3 - Mastery capstone
    SPELL_PRIEST_FOCUSED_WILL_R3                    = 45244,    // (6,0) rank 3 - Empowered Penance
    SPELL_PRIEST_GRACE_R1                           = 47516,    // (8,2)
    SPELL_PRIEST_GRACE_R2                           = 47517,
    SPELL_PRIEST_GRACE_R3                           = 200163,
    SPELL_PRIEST_DIVINE_AEGIS_R1                    = 47509,    // (8,0)
    SPELL_PRIEST_DIVINE_AEGIS_R2                    = 47511,    // rank 2 - Mastery capstone
    SPELL_PRIEST_RAPTURE_R1                         = 47535,    // (7,1)
    SPELL_PRIEST_RAPTURE_R2                         = 47536,
    SPELL_PRIEST_RAPTURE_R3                         = 47537,
    SPELL_PRIEST_RENEWED_HOPE_R1                    = 57470,    // (7,0)
    SPELL_PRIEST_RENEWED_HOPE_R2                    = 57472,    // rank 2 - Greater PW:S capstone

    // Talent-triggered buffs.
    SPELL_PRIEST_GRACE_BUFF_R1                      = 200164,
    SPELL_PRIEST_GRACE_BUFF_R2                      = 200165,
    SPELL_PRIEST_GRACE_BUFF_R3                      = 47930,
    SPELL_PRIEST_RENEWED_HOPE_BUFF                  = 63944,
    SPELL_PRIEST_RAPTURE_SELF_MANA                  = 47755,
    SPELL_PRIEST_RAPTURE_TARGET_MANA                = 63654,
    SPELL_PRIEST_RAPTURE_TARGET_RAGE                = 63653,
    SPELL_PRIEST_RAPTURE_TARGET_ENERGY              = 63655,
    SPELL_PRIEST_RAPTURE_TARGET_RUNIC_POWER         = 63652,
    // Kept verbatim from the engine block this migrated out of (SpellAuras.cpp): rogues/druids
    // carrying this aura get no energy back.
    SPELL_PRIEST_RAPTURE_ENERGY_EXCLUSION           = 70405,

    // Discipline rework spells (DISC.md "ID map").
    SPELL_PRIEST_GREATER_POWER_WORD_SHIELD          = 200155,
    SPELL_PRIEST_EMPOWERED_PENANCE_READY            = 200159,
    SPELL_PRIEST_EMPOWERED_PENANCE_HEAL             = 200160,
    SPELL_PRIEST_GREATER_POWER_WORD_SHIELD_READY    = 200161,
    SPELL_PRIEST_SPIRIT_SHELL                       = 200166
};

namespace
{
    // "Overhealing generates 75% less shielding, and the absorb is limited to 30% of the target's
    // maximum health" (docs/reworks/priest-disc-rework.md, Divine Aegis).
    constexpr float PRIEST_DIVINE_AEGIS_OVERHEAL_WEIGHT = 0.25f;
    constexpr int32 PRIEST_DIVINE_AEGIS_MAX_HEALTH_PCT = 30;

    // Rapture (7,1): "This effect can only occur once every 5 sec" (stock engine block used 12 s
    // plus an 11.5 s "let every bubble broken by one hit pay out" grace window; the retune makes
    // the internal cooldown a hard one, which is what the design text asks for).
    constexpr uint32 PRIEST_RAPTURE_INTERNAL_COOLDOWN_MS = 5000;
    // "You also energize your shielded target with 1% total mana, 8 rage and 16 energy" - the rage
    // and energy amounts live on their own trigger spell rows, only the mana share is computed.
    constexpr uint32 PRIEST_RAPTURE_TARGET_MANA_PCT = 1;

    // Inner Focus (2,1): "Power Word: Shield: reduces Weakened Soul duration by 10 sec."
    constexpr int32 PRIEST_INNER_FOCUS_WEAKENED_SOUL_REDUCTION_MS = 10000;

    // Greater Power Word: Shield - "the 2 nearest injured party/raid allies within 20 yd of the
    // primary target" (PLAN sec 2).
    constexpr float PRIEST_GREATER_PWS_RADIUS = 20.0f;
    constexpr uint32 PRIEST_GREATER_PWS_EXTRA_TARGETS = 2;

    // Empowered Penance (Focused Will's capstone) - "up to 3 allies within 10 yd of the Penance
    // target" (PLAN sec 2).
    constexpr float PRIEST_EMPOWERED_PENANCE_RADIUS = 10.0f;
    constexpr uint32 PRIEST_EMPOWERED_PENANCE_TARGETS = 3;

    // Renewed Hope (7,0) capstone: "Your Penance bolts have a 5% chance to transform your next
    // Power Word: Shield into Greater Power Word: Shield."
    constexpr float PRIEST_RENEWED_HOPE_CAPSTONE_CHANCE = 5.0f;

    /*
     * "the N nearest injured party/raid allies within <radius> of <center>", excluding `exclude`.
     * Walks the caster's group (falling back to the caster alone when ungrouped) instead of doing
     * a grid search - the same shape Prayer of Mending's jump search uses in Unit.cpp - because a
     * grid search would also return friendly non-group units, which none of these talents want.
     */
    void SelectNearbyInjuredRaidAllies(Unit* caster, Unit* center, float radius, uint32 maxTargets, Unit const* exclude, std::list<Unit*>& out)
    {
        if (!caster || !center || !maxTargets)
            return;

        std::list<Unit*> candidates;
        if (Group* group = caster->IsPlayer() ? caster->ToPlayer()->GetGroup() : nullptr)
        {
            for (GroupReference* itr = group->GetFirstMember(); itr != nullptr; itr = itr->next())
                if (Player* member = itr->GetSource())
                    candidates.push_back(member);
        }
        else
            candidates.push_back(caster);

        candidates.remove_if([caster, center, radius, exclude](Unit* unit)
        {
            return unit == exclude || !unit->IsAlive() || unit->IsFullHealth() || !caster->IsFriendlyTo(unit)
                   || !center->IsWithinDistInMap(unit, radius) || !center->IsWithinLOSInMap(unit);
        });

        candidates.sort(Acore::ObjectDistanceOrderPred(center));
        if (candidates.size() > maxTargets)
            candidates.resize(maxTargets);

        out = std::move(candidates);
    }

    // Grace (8,2) hands out a different buff per rank (DISC.md "ID map"); Greater Power Word:
    // Shield has to apply it to its two extra targets by hand, since they are hit by a fully
    // triggered cast that suppresses the normal proc chain.
    uint32 GetGraceBuffForCaster(Unit const* caster)
    {
        if (caster->HasAura(SPELL_PRIEST_GRACE_R3))
            return SPELL_PRIEST_GRACE_BUFF_R3;
        if (caster->HasAura(SPELL_PRIEST_GRACE_R2))
            return SPELL_PRIEST_GRACE_BUFF_R2;
        if (caster->HasAura(SPELL_PRIEST_GRACE_R1))
            return SPELL_PRIEST_GRACE_BUFF_R1;
        return 0;
    }

    // Rapture's per-rank self-mana share: 1 / 1.75 / 2.5% (docs/reworks/priest-disc-rework.md).
    // Deliberately not read from the rank row's own base points: those are int32, so 1.75% cannot
    // be stored there - the stock engine block had the same problem and fudged it by adding or
    // subtracting 0.5 per rank id, which is the idiom this replaces.
    float GetRaptureSelfManaPct(uint32 rankSpellId)
    {
        switch (rankSpellId)
        {
            case SPELL_PRIEST_RAPTURE_R1:
                return 1.0f;
            case SPELL_PRIEST_RAPTURE_R2:
                return 1.75f;
            case SPELL_PRIEST_RAPTURE_R3:
                return 2.5f;
            default:
                return 0.0f;
        }
    }
}

/*
 * Divine Aegis's absorb math (docs/reworks/priest-disc-rework.md 8,0), shared between the talent's
 * own proc (spell_pri_divine_aegis) and Empowered Penance, which applies Divine Aegis to each of
 * its extra bolts "as if it had crit" (PLAN sec 2). `healAmount` is the already-weighted heal
 * contribution: the proc folds overhealing in at 25% before calling, Empowered Penance passes its
 * bolt's heal straight through. File-local namespace - both callers live in this translation unit.
 */
namespace PriestDisc
{
    void GrantDivineAegis(Unit* caster, Unit* target, uint32 healAmount, bool isSingleTarget)
    {
        if (!caster || !target || !healAmount)
            return;

        // Spirit Shell already turned this cast into its own Mastery-scaled absorb; one cast must
        // never produce two (docs/reworks/priest-disc-rework.md, Spirit Shell).
        if (caster->HasAura(SPELL_PRIEST_SPIRIT_SHELL))
            return;

        // Only one of the two ranks is ever known, so rank 2 is both the amount source and the
        // Mastery-capstone marker - no dummy-by-icon read needed.
        bool masteryScaled = true;
        AuraEffect const* talent = caster->GetAuraEffect(SPELL_PRIEST_DIVINE_AEGIS_R2, EFFECT_0);
        if (!talent)
        {
            masteryScaled = false;
            talent = caster->GetAuraEffect(SPELL_PRIEST_DIVINE_AEGIS_R1, EFFECT_0);
        }

        if (!talent)
            return;

        int32 absorb = int32(CalculatePct(float(healAmount), float(talent->GetAmount())));

        // "Divine Aegis is doubled for single target heals" (PLAN sec 2: 30/60%).
        if (isSingleTarget)
            absorb *= 2;

        // Rank 2 capstone: "additionally increased by your Mastery. This bonus is multiplicative
        // and applies after all other modifiers." Applied to this application's own contribution
        // before the running total is folded in, so a shield refreshed five times is not scaled by
        // Mastery five times over.
        if (masteryScaled)
            if (Player* player = caster->ToPlayer())
                AddPct(absorb, player->GetMasteryPercentage());

        // Multiple effects stack, so let's try to find this aura.
        if (AuraEffect const* aegis = target->GetAuraEffect(SPELL_PRIEST_DIVINE_AEGIS, EFFECT_0, caster->GetGUID()))
            absorb += aegis->GetAmount();

        absorb = std::min<int32>(absorb, int32(target->CountPctFromMaxHealth(PRIEST_DIVINE_AEGIS_MAX_HEALTH_PCT)));

        caster->CastCustomSpell(SPELL_PRIEST_DIVINE_AEGIS, SPELLVALUE_BASE_POINT0, absorb, target, true);
    }
}

enum PriestSpellIcons
{
    PRIEST_ICON_ID_BORROWED_TIME                    = 2899,
    PRIEST_ICON_ID_EMPOWERED_RENEW_TALENT           = 3021,
    PRIEST_ICON_ID_PAIN_AND_SUFFERING               = 2874,
    PRIEST_ICON_ID_BODY_AND_SOUL                    = 2218
};

// Proc system triggered spells
enum PriestProcSpells
{
    SPELL_PRIEST_VAMPIRIC_EMBRACE_HEAL              = 15290,
    SPELL_PRIEST_GLYPH_OF_DISPEL_MAGIC_HEAL         = 56131,
    SPELL_PRIEST_BODY_AND_SOUL_SPEED                = 64136,
    SPELL_PRIEST_ORACULAR_HEAL                      = 26170,
    SPELL_PRIEST_DIVINE_BLESSING                    = 40440,
    SPELL_PRIEST_DIVINE_WRATH                       = 40441,
    SPELL_PRIEST_ARMOR_OF_FAITH                     = 28810,
    SPELL_PRIEST_BLESSED_HEALING                    = 70772,
    SPELL_PRIEST_SHADOW_WORD_DEATH_R1               = 32379,
    SPELL_PRIEST_MIND_BLAST_R1                      = 8092,
    SPELL_PRIEST_MIND_FLAY_DAMAGE                   = 58381,
    SPELL_PRIEST_BLESSED_RECOVERY_R1                = 27813
};

enum Mics
{
    PRIEST_LIGHTWELL_NPC_1                          = 31897,
    PRIEST_LIGHTWELL_NPC_2                          = 31896,
    PRIEST_LIGHTWELL_NPC_3                          = 31895,
    PRIEST_LIGHTWELL_NPC_4                          = 31894,
    PRIEST_LIGHTWELL_NPC_5                          = 31893,
    PRIEST_LIGHTWELL_NPC_6                          = 31883
};

class spell_pri_shadowfiend_scaling : public AuraScript
{
    PrepareAuraScript(spell_pri_shadowfiend_scaling);

    void CalculateResistanceAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: shadowfiend inherits 40% of resistance from owner and 35% of armor (guessed)
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            SpellSchoolMask schoolMask = SpellSchoolMask(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue);
            int32 modifier = schoolMask == SPELL_SCHOOL_MASK_NORMAL ? 35 : 40;
            amount = CalculatePct(std::max<int32>(0, owner->GetResistance(schoolMask)), modifier);
        }
    }

    void CalculateStatAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: shadowfiend inherits 30% of intellect and 65% of stamina (guessed)
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            Stats stat = Stats(aurEff->GetSpellInfo()->Effects[aurEff->GetEffIndex()].MiscValue);
            amount = CalculatePct(std::max<int32>(0, owner->GetStat(stat)), stat == STAT_STAMINA ? 65 : 30);
        }
    }

    void CalculateAPAmount(AuraEffect const*  /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: shadowfiend inherits 333% of SP as AP - 35.7% of damage increase per hit
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            int32 shadow = owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_SHADOW);
            amount = CalculatePct(std::max<int32>(0, shadow), 300); // xinef: deacrased to 300, including 15% from self buff
        }
    }

    void CalculateSPAmount(AuraEffect const*  /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // xinef: shadowfiend inherits 30% of SP
        if (Unit* owner = GetUnitOwner()->GetOwner())
        {
            int32 shadow = owner->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_SHADOW);
            amount = CalculatePct(std::max<int32>(0, shadow), 30);

            // xinef: Update appropriate player field
            if (owner->IsPlayer())
                owner->SetUInt32Value(PLAYER_PET_SPELL_POWER, (uint32)amount);
        }
    }

    void HandleEffectApply(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, aurEff->GetAuraType(), true, SPELL_BLOCK_TYPE_POSITIVE);
        if (aurEff->GetAuraType() == SPELL_AURA_MOD_ATTACK_POWER)
            GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_ATTACK_POWER_PCT, true, SPELL_BLOCK_TYPE_POSITIVE);
        else if (aurEff->GetAuraType() == SPELL_AURA_MOD_STAT)
            GetUnitOwner()->ApplySpellImmune(0, IMMUNITY_STATE, SPELL_AURA_MOD_TOTAL_STAT_PERCENTAGE, true, SPELL_BLOCK_TYPE_POSITIVE);
    }

    void Register() override
    {
        if (m_scriptSpellId != 35661)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_shadowfiend_scaling::CalculateResistanceAmount, EFFECT_ALL, SPELL_AURA_MOD_RESISTANCE);

        if (m_scriptSpellId == 35661 || m_scriptSpellId == 35662)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_shadowfiend_scaling::CalculateStatAmount, EFFECT_ALL, SPELL_AURA_MOD_STAT);

        if (m_scriptSpellId == 35661)
        {
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_shadowfiend_scaling::CalculateAPAmount, EFFECT_ALL, SPELL_AURA_MOD_ATTACK_POWER);
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_shadowfiend_scaling::CalculateSPAmount, EFFECT_ALL, SPELL_AURA_MOD_DAMAGE_DONE);
        }

        OnEffectApply += AuraEffectApplyFn(spell_pri_shadowfiend_scaling::HandleEffectApply, EFFECT_ALL, SPELL_AURA_ANY, AURA_EFFECT_HANDLE_REAL);
    }
};

// -34861 - Circle of Healing
class spell_pri_circle_of_healing : public SpellScript
{
    PrepareSpellScript(spell_pri_circle_of_healing);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_GLYPH_OF_CIRCLE_OF_HEALING });
    }

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if(Acore::RaidCheck(GetCaster(), false));

        uint32 const maxTargets = GetCaster()->HasAura(SPELL_PRIEST_GLYPH_OF_CIRCLE_OF_HEALING) ? 6 : 5; // Glyph of Circle of Healing

        if (targets.size() > maxTargets)
        {
            targets.sort(Acore::HealthPctOrderPred());
            targets.resize(maxTargets);
        }
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pri_circle_of_healing::FilterTargets, EFFECT_0, TARGET_UNIT_DEST_AREA_ALLY);
    }
};

// -47509 - Divine Aegis
class spell_pri_divine_aegis : public AuraScript
{
    PrepareAuraScript(spell_pri_divine_aegis);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_DIVINE_AEGIS });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        return eventInfo.GetProcTarget() && eventInfo.GetHealInfo();
    }

    /*
     * Discipline rework (docs/reworks/priest-disc-rework.md 8,0): "Your critical Holy healing
     * spells create a protective barrier absorbing damage up to 15/30% of the healed amount...
     * Divine Aegis is doubled for single target heals. Overhealing generates 75% less shielding,
     * and the absorb is limited to 30% of the target's maximum health." The old flat
     * `pct x GetHeal(), capped at level*125` is gone: overhealing is now worth a quarter, the cap
     * scales with the target, and the rank-2 Mastery capstone rides on top - all of that lives in
     * PriestDisc::GrantDivineAegis, which Empowered Penance shares.
     */
    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        HealInfo* healInfo = eventInfo.GetHealInfo();
        uint32 effectiveHeal = healInfo->GetEffectiveHeal();
        uint32 overheal = healInfo->GetHeal() > effectiveHeal ? healInfo->GetHeal() - effectiveHeal : 0;
        uint32 contribution = effectiveHeal + uint32(float(overheal) * PRIEST_DIVINE_AEGIS_OVERHEAL_WEIGHT);

        // PoM's bounce and Binding Heal are both plain single-unit heals, so IsAffectingArea()
        // classifies them as single-target for free (PLAN sec 1).
        SpellInfo const* healSpellInfo = healInfo->GetSpellInfo();
        bool singleTarget = !healSpellInfo || !healSpellInfo->IsAffectingArea();

        PriestDisc::GrantDivineAegis(GetTarget(), eventInfo.GetProcTarget(), contribution, singleTarget);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_divine_aegis::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_divine_aegis::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 64844 - Divine Hymn
class spell_pri_divine_hymn : public SpellScript
{
    PrepareSpellScript(spell_pri_divine_hymn);

    // Priest baseline rework (docs/reworks/priest-new-spells.md): "Heals all party or raid
    // members within 40 yards" - the old top-3-lowest-health cap is gone, everyone in range is
    // healed now. Only the RaidCheck (party/raid membership) filter survives.
    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if(Acore::RaidCheck(GetCaster(), false));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pri_divine_hymn::FilterTargets, EFFECT_ALL, TARGET_UNIT_SRC_AREA_ALLY);
    }
};

// 55680 - Glyph of Prayer of Healing
class spell_pri_glyph_of_prayer_of_healing : public AuraScript
{
    PrepareAuraScript(spell_pri_glyph_of_prayer_of_healing);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_GLYPH_OF_PRAYER_OF_HEALING_HEAL });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        HealInfo* healInfo = eventInfo.GetHealInfo();
        if (!healInfo || !healInfo->GetHeal())
        {
            return;
        }

        SpellInfo const* triggeredSpellInfo = sSpellMgr->AssertSpellInfo(SPELL_PRIEST_GLYPH_OF_PRAYER_OF_HEALING_HEAL);
        int32 heal = int32(CalculatePct(int32(healInfo->GetHeal()), aurEff->GetAmount()) / triggeredSpellInfo->GetMaxTicks());
        GetTarget()->CastCustomSpell(SPELL_PRIEST_GLYPH_OF_PRAYER_OF_HEALING_HEAL, SPELLVALUE_BASE_POINT0, heal, eventInfo.GetProcTarget(), true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_glyph_of_prayer_of_healing::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 47788 - Guardian Spirit
class spell_pri_guardian_spirit : public AuraScript
{
    PrepareAuraScript(spell_pri_guardian_spirit);

    uint32 healPct;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_GUARDIAN_SPIRIT_HEAL });
    }

    bool Load() override
    {
        healPct = GetSpellInfo()->Effects[EFFECT_1].CalcValue();
        return true;
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        // Set absorbtion amount to unlimited
        amount = -1;
    }

    void Absorb(AuraEffect* /*aurEff*/, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        Unit* target = GetTarget();
        if (dmgInfo.GetDamage() < target->GetHealth())
            return;

        int32 healAmount = int32(target->CountPctFromMaxHealth(healPct));
        // remove the aura now, we don't want 40% healing bonus
        Remove(AURA_REMOVE_BY_ENEMY_SPELL);
        target->CastCustomSpell(target, SPELL_PRIEST_GUARDIAN_SPIRIT_HEAL, &healAmount, nullptr, nullptr, true);
        absorbAmount = dmgInfo.GetDamage();
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_guardian_spirit::CalculateAmount, EFFECT_1, SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_pri_guardian_spirit::Absorb, EFFECT_1);
    }
};

// 64904 - Hymn of Hope
class spell_pri_hymn_of_hope : public SpellScript
{
    PrepareSpellScript(spell_pri_hymn_of_hope);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        targets.remove_if(Acore::PowerCheck(POWER_MANA, false));
        targets.remove_if(Acore::RaidCheck(GetCaster(), false));

        uint32 const maxTargets = 3;

        if (targets.size() > maxTargets)
        {
            targets.sort(Acore::PowerPctOrderPred(POWER_MANA));
            targets.resize(maxTargets);
        }
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pri_hymn_of_hope::FilterTargets, EFFECT_ALL, TARGET_UNIT_SRC_AREA_ALLY);
    }
};

static bool IsLightwellEntry(uint32 entry)
{
    switch (entry)
    {
        case PRIEST_LIGHTWELL_NPC_1:
        case PRIEST_LIGHTWELL_NPC_2:
        case PRIEST_LIGHTWELL_NPC_3:
        case PRIEST_LIGHTWELL_NPC_4:
        case PRIEST_LIGHTWELL_NPC_5:
        case PRIEST_LIGHTWELL_NPC_6:
            return true;
        default:
            return false;
    }
}

// 60123 - Lightwell
class spell_pri_lightwell : public SpellScript
{
    PrepareSpellScript(spell_pri_lightwell);

    bool Load() override
    {
        return GetCaster()->IsCreature();
    }

    void HandleScriptEffect(SpellEffIndex /* effIndex */)
    {
        Creature* caster = GetCaster()->ToCreature();
        if (!caster || !caster->IsSummon())
            return;

        uint32 lightwellRenew = 0;
        switch (caster->GetEntry())
        {
            case PRIEST_LIGHTWELL_NPC_1: lightwellRenew = 7001; break;
            case PRIEST_LIGHTWELL_NPC_2: lightwellRenew = 27873; break;
            case PRIEST_LIGHTWELL_NPC_3: lightwellRenew = 27874; break;
            case PRIEST_LIGHTWELL_NPC_4: lightwellRenew = 28276; break;
            case PRIEST_LIGHTWELL_NPC_5: lightwellRenew = 48084; break;
            case PRIEST_LIGHTWELL_NPC_6: lightwellRenew = 48085; break;
        }

        // proc a spellcast
        if (Aura* chargesAura = caster->GetAura(SPELL_PRIEST_LIGHTWELL_CHARGES))
        {
            caster->CastSpell(GetHitUnit(), lightwellRenew, true, nullptr, nullptr,
                caster->ToTempSummon()->GetSummonerGUID());
            if (chargesAura->ModCharges(-1))
                caster->ToTempSummon()->UnSummon();
        }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_pri_lightwell::HandleScriptEffect, EFFECT_0, SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// -7001 - Lightwell Renew
class spell_pri_lightwell_renew : public AuraScript
{
    PrepareAuraScript(spell_pri_lightwell_renew);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        if (Unit* caster = GetCaster())
        {
            // Bonus from Glyph of Lightwell
            if (AuraEffect* modHealing = caster->GetAuraEffect(SPELL_PRIEST_GLYPH_OF_LIGHTWELL, EFFECT_0))
                AddPct(amount, modHealing->GetAmount());
        }
    }

    void InitializeAmount(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        // Attacks done to you equal to 30% of your total health will cancel the effect
        _remainingAmount = GetTarget()->CountPctFromMaxHealth(30);
    }

    void CheckDropCharge(ProcEventInfo& eventInfo)
    {
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo)
            return;

        uint32 damage = damageInfo->GetDamage();
        if (_remainingAmount <= damage)
            return;

        _remainingAmount -= damage;
        // prevent drop charge
        PreventDefaultAction();
    }

    void HandleUpdateSpellclick(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        if (!player)
            return;

        Unit* caster = GetCaster();
        if (!caster)
            return;

        // Spellclick gets hidden per player on the well's own NPC flags, so the wells are what
        // need resending here, not the aura's caster (the priest).
        for (Unit* controlled : caster->m_Controlled)
        {
            if (!IsLightwellEntry(controlled->GetEntry()))
                continue;

            UpdateData data;
            WorldPacket packet;
            controlled->BuildValuesUpdateBlockForPlayer(&data, player);
            data.BuildPacket(packet);
            player->SendDirectMessage(&packet);
        }
    }

    void Register() override
    {
        DoPrepareProc += AuraProcFn(spell_pri_lightwell_renew::CheckDropCharge);
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_lightwell_renew::CalculateAmount, EFFECT_0, SPELL_AURA_PERIODIC_HEAL);
        AfterEffectApply += AuraEffectApplyFn(spell_pri_lightwell_renew::InitializeAmount, EFFECT_0, SPELL_AURA_PERIODIC_HEAL, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
        AfterEffectApply += AuraEffectApplyFn(spell_pri_lightwell_renew::HandleUpdateSpellclick, EFFECT_0, SPELL_AURA_PERIODIC_HEAL, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pri_lightwell_renew::HandleUpdateSpellclick, EFFECT_0, SPELL_AURA_PERIODIC_HEAL, AURA_EFFECT_HANDLE_REAL);
    }

private:
    uint32 _remainingAmount = 0;
};

// 8129 - Mana Burn
class spell_pri_mana_burn : public SpellScript
{
    PrepareSpellScript(spell_pri_mana_burn);

    void HandleAfterHit()
    {
        if (Unit* unitTarget = GetHitUnit())
            unitTarget->RemoveAurasWithMechanic((1ULL << MECHANIC_FEAR) | (1ULL << MECHANIC_POLYMORPH));
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_pri_mana_burn::HandleAfterHit);
    }
};

// 28305 - Mana Leech (Passive) (Priest Pet Aura)
class spell_pri_mana_leech : public AuraScript
{
    PrepareAuraScript(spell_pri_mana_leech);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_MANA_LEECH_PROC });
    }

    bool Load() override
    {
        _procTarget = nullptr;
        return true;
    }

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        _procTarget = GetTarget()->GetOwner();
        return _procTarget;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        GetTarget()->CastSpell(_procTarget, SPELL_PRIEST_MANA_LEECH_PROC, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_mana_leech::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_mana_leech::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }

private:
    Unit* _procTarget;
};

// -49821 - Mind Sear
class spell_pri_mind_sear : public SpellScript
{
    PrepareSpellScript(spell_pri_mind_sear);

    void FilterTargets(std::list<WorldObject*>& unitList)
    {
        unitList.remove_if(Acore::ObjectGUIDCheck(GetCaster()->GetGuidValue(UNIT_FIELD_CHANNEL_OBJECT), true));
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pri_mind_sear::FilterTargets, EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);
    }
};

// 47948 - Pain and Suffering (Proc)
class spell_pri_pain_and_suffering_proc : public SpellScript
{
    PrepareSpellScript(spell_pri_pain_and_suffering_proc);

    void HandleEffectScriptEffect(SpellEffIndex /*effIndex*/)
    {
        // Refresh Shadow Word: Pain on target
        if (Unit* unitTarget = GetHitUnit())
            if (AuraEffect* aur = unitTarget->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, 0x8000, 0, 0, GetCaster()->GetGUID()))
            {
                aur->GetBase()->RefreshTimersWithMods();
                aur->ChangeAmount(aur->CalculateAmount(aur->GetCaster()), false);
            }
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_pri_pain_and_suffering_proc::HandleEffectScriptEffect, EFFECT_0, SPELL_EFFECT_SCRIPT_EFFECT);
    }
};

// -47540 - Penance
class spell_pri_penance : public SpellScript
{
    PrepareSpellScript(spell_pri_penance);

    bool Load() override
    {
        return GetCaster()->IsPlayer();
    }

    bool Validate(SpellInfo const* spellInfo) override
    {
        if (!ValidateSpellInfo({ SPELL_PRIEST_EMPOWERED_PENANCE_READY, SPELL_PRIEST_EMPOWERED_PENANCE_HEAL,
                                 SPELL_PRIEST_GREATER_POWER_WORD_SHIELD_READY }))
            return false;

        SpellInfo const* firstRankSpellInfo = sSpellMgr->GetSpellInfo(SPELL_PRIEST_PENANCE_R1);
        if (!firstRankSpellInfo)
            return false;

        // can't use other spell than this penance due to spell_ranks dependency
        if (!spellInfo->IsRankOf(firstRankSpellInfo))
            return false;

        uint8 rank = spellInfo->GetRank();
        if (!sSpellMgr->GetSpellWithRank(SPELL_PRIEST_PENANCE_R1_DAMAGE, rank, true))
            return false;
        if (!sSpellMgr->GetSpellWithRank(SPELL_PRIEST_PENANCE_R1_HEAL, rank, true))
            return false;

        return true;
    }

    void HandleDummy(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        if (Unit* unitTarget = GetHitUnit())
        {
            if (!unitTarget->IsAlive())
                return;

            uint8 rank = GetSpellInfo()->GetRank();

            if (caster->IsFriendlyTo(unitTarget))
            {
                caster->CastSpell(unitTarget, sSpellMgr->GetSpellWithRank(SPELL_PRIEST_PENANCE_R1_HEAL, rank), false);
                HandleEmpoweredPenance(caster, unitTarget);
            }
            else
                caster->CastSpell(unitTarget, sSpellMgr->GetSpellWithRank(SPELL_PRIEST_PENANCE_R1_DAMAGE, rank), false);

            HandleRenewedHopeCapstone(caster);
        }
    }

    /*
     * Focused Will (6,0) capstone: "Your Flash Heal and Greater Heal have a 5% chance to empower
     * your next Penance. Empowered Penance fires additional bolts at allies near your target,
     * applying Divine Aegis to each." PLAN sec 2 pins that down to "up to 3 allies within 10 yd of
     * the Penance target, each bolt heals for a normal Penance bolt amount and applies Divine Aegis
     * at the caster's DA rank as if it had crit (no aegis if DA isn't talented)".
     *
     * Fired once per Penance cast, not once per channel tick: Penance's ticks live inside the bolt
     * spell (47757) rather than in 47540, and only 47540 carries a script binding.
     */
    void HandleEmpoweredPenance(Unit* caster, Unit* primaryTarget)
    {
        if (!caster->HasAura(SPELL_PRIEST_EMPOWERED_PENANCE_READY))
            return;

        caster->RemoveAurasDueToSpell(SPELL_PRIEST_EMPOWERED_PENANCE_READY);

        SpellInfo const* boltInfo = sSpellMgr->GetSpellInfo(SPELL_PRIEST_EMPOWERED_PENANCE_HEAL);
        if (!boltInfo)
            return;

        std::list<Unit*> extraTargets;
        SelectNearbyInjuredRaidAllies(caster, primaryTarget, PRIEST_EMPOWERED_PENANCE_RADIUS, PRIEST_EMPOWERED_PENANCE_TARGETS, primaryTarget, extraTargets);

        for (Unit* extraTarget : extraTargets)
        {
            caster->CastSpell(extraTarget, SPELL_PRIEST_EMPOWERED_PENANCE_HEAL, true);

            // The aegis has to be granted "as if it had crit", which the normal crit-driven proc
            // can't express, so the heal the bolt is about to land for is recomputed here with the
            // same pipeline the cast itself uses. A Penance bolt is a single-target heal, so it
            // takes Divine Aegis's doubled single-target value.
            uint32 heal = uint32(std::max<int32>(0, boltInfo->Effects[EFFECT_0].CalcValue(caster)));
            heal = caster->SpellHealingBonusDone(extraTarget, boltInfo, heal, HEAL, EFFECT_0);
            heal = extraTarget->SpellHealingBonusTaken(caster, boltInfo, heal, HEAL);
            PriestDisc::GrantDivineAegis(caster, extraTarget, heal, true);
        }
    }

    /*
     * Renewed Hope (7,0) capstone: "Your Penance bolts have a 5% chance to transform your next
     * Power Word: Shield into Greater Power Word: Shield." Rolled once per Penance cast for the
     * same reason as Empowered Penance above (the bolts themselves carry no script binding), and
     * scaled by the Proc Chance stat by hand because this is a script-side roll, not a spell_proc
     * one (PLAN sec 3.8).
     */
    void HandleRenewedHopeCapstone(Unit* caster)
    {
        if (!caster->HasAura(SPELL_PRIEST_RENEWED_HOPE_R2))
            return;

        Player* player = caster->ToPlayer();
        float chance = PRIEST_RENEWED_HOPE_CAPSTONE_CHANCE * (1.0f + (player ? player->GetProcChancePercentage() : 0.0f) / 100.0f);
        if (!roll_chance_f(chance))
            return;

        caster->CastSpell(caster, SPELL_PRIEST_GREATER_POWER_WORD_SHIELD_READY, true);
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (Unit* target = GetExplTargetUnit())
        {
            if (!caster->IsFriendlyTo(target))
            {
                if (!caster->IsValidAttackTarget(target))
                    return SPELL_FAILED_BAD_TARGETS;

                if (!caster->isInFront(target))
                    return SPELL_FAILED_UNIT_NOT_INFRONT;
            }
        }
        else
            return SPELL_FAILED_BAD_TARGETS;
        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnEffectHitTarget += SpellEffectFn(spell_pri_penance::HandleDummy, EFFECT_0, SPELL_EFFECT_DUMMY);
        OnCheckCast += SpellCheckCastFn(spell_pri_penance::CheckCast);
    }
};

// -17 - Power Word: Shield
static int32 CalculateSpellAmount(Unit* caster, int32 amount, SpellInfo const* spellInfo, AuraEffect const* aurEff)
{
    // +80.68% from sp bonus
    float bonus = 0.8068f;

    // Borrowed Time
    if (AuraEffect const* borrowedTime = caster->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_ID_BORROWED_TIME, EFFECT_1))
        bonus += CalculatePct(1.0f, borrowedTime->GetAmount());

    bonus *= caster->SpellBaseHealingBonusDone(spellInfo->GetSchoolMask());

    // Improved PW: Shield: its weird having a SPELLMOD_ALL_EFFECTS here but its blizzards doing :)
    // Improved PW: Shield is only applied at the spell healing bonus because it was already applied to the base value in CalculateSpellDamage
    bonus = caster->ApplyEffectModifiers(spellInfo, aurEff->GetEffIndex(), bonus);
    bonus *= caster->CalculateLevelPenalty(spellInfo);

    amount += int32(bonus);

    // Twin Disciplines
    if (AuraEffect const* twinDisciplines = caster->GetAuraEffect(SPELL_AURA_ADD_PCT_MODIFIER, SPELLFAMILY_PRIEST, 0x400000, 0, 0, caster->GetGUID()))
        AddPct(amount, twinDisciplines->GetAmount());

    // Focused Power, xinef: apply positive modifier only
    if (int32 healModifier = caster->GetMaxPositiveAuraModifier(SPELL_AURA_MOD_HEALING_DONE_PERCENT))
        AddPct(amount, healModifier);

    // Arena - Dampening
    if (AuraEffect const* arenaDampening = caster->GetAuraEffect(SPELL_GENERIC_ARENA_DAMPENING, EFFECT_0))
    {
        AddPct(amount, arenaDampening->GetAmount());
    }
    // Battleground - Dampening
    else if (AuraEffect const* bgDampening = caster->GetAuraEffect(SPELL_GENERIC_BATTLEGROUND_DAMPENING, EFFECT_0))
    {
        AddPct(amount, bgDampening->GetAmount());
    }

    return amount;
};

class spell_pri_power_word_shield_aura : public AuraScript
{
    PrepareAuraScript(spell_pri_power_word_shield_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_REFLECTIVE_SHIELD_TRIGGERED, SPELL_PRIEST_REFLECTIVE_SHIELD_R1,
                                   SPELL_PRIEST_RAPTURE_SELF_MANA, SPELL_PRIEST_RAPTURE_TARGET_MANA,
                                   SPELL_PRIEST_RAPTURE_TARGET_RAGE, SPELL_PRIEST_RAPTURE_TARGET_ENERGY,
                                   SPELL_PRIEST_RAPTURE_TARGET_RUNIC_POWER });
    }

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;
        Unit* caster = GetCaster();
        if (!caster)
            return;

        amount = CalculateSpellAmount(caster, amount, GetSpellInfo(), aurEff);

        // Improved Power Word: Shield (2,2) capstone: "Your Power Word: Shield and Spirit Shell
        // absorption is additionally increased by your Mastery. This bonus is multiplicative and
        // applies after all other modifiers." Rank 3 only, so its own rank spell id is the marker.
        // Reflective Shield reads the post-Mastery value because it hooks the absorb itself.
        if (Player* player = caster->ToPlayer())
            if (player->HasAura(SPELL_PRIEST_IMPROVED_POWER_WORD_SHIELD_R3))
                AddPct(amount, player->GetMasteryPercentage());
    }

    /*
     * Rapture (7,1): "When your Power Word: Shield is completely absorbed you are instantly
     * energized with 1/1.75/2.5% of your total mana. You also energize your shielded target with
     * 1% total mana, 8 rage and 16 energy. This effect can only occur once every 5 sec."
     *
     * Migrated out of Aura::HandleAuraSpecificMods (SpellAuras.cpp) per PLAN sec 6.8: living on
     * the shield's own aura script means Greater Power Word: Shield (200155), which shares this
     * script, is covered by the same code for free. The engine block keyed purely on
     * AURA_REMOVE_BY_ENEMY_SPELL, which a *dispel* also uses; checking that the remaining absorb
     * ran out distinguishes "completely absorbed" from "stolen/dispelled".
     */
    void HandleRapture(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        if (GetTargetApplication()->GetRemoveMode() != AURA_REMOVE_BY_ENEMY_SPELL || aurEff->GetAmount() > 0)
            return;

        Unit* target = GetTarget();
        Player* caster = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!target || !caster)
            return;

        Aura const* rapture = caster->GetAuraOfRankedSpell(SPELL_PRIEST_RAPTURE_R1);
        if (!rapture)
            return;

        if (caster->HasSpellCooldown(rapture->GetId()))
            return;

        caster->AddSpellCooldown(rapture->GetId(), 0, PRIEST_RAPTURE_INTERNAL_COOLDOWN_MS);

        int32 selfMana = int32(CalculatePct(float(caster->GetMaxPower(POWER_MANA)), GetRaptureSelfManaPct(rapture->GetId())));
        if (selfMana > 0)
            caster->CastCustomSpell(caster, SPELL_PRIEST_RAPTURE_SELF_MANA, &selfMana, nullptr, nullptr, true);

        AuraEffect const* targetEffect = rapture->GetEffect(EFFECT_1);
        if (!targetEffect)
            return;

        // Rolls its own chance, so it has to fold the Proc Chance stat in by hand (PLAN sec 3.8).
        float chance = float(targetEffect->GetAmount()) * (1.0f + caster->GetProcChancePercentage() / 100.0f);
        if (!roll_chance_f(chance))
            return;

        uint32 triggeredSpellId = 0;
        switch (target->getPowerType())
        {
            case POWER_MANA:
            {
                int32 targetMana = int32(CalculatePct(target->GetMaxPower(POWER_MANA), PRIEST_RAPTURE_TARGET_MANA_PCT));
                caster->CastCustomSpell(target, SPELL_PRIEST_RAPTURE_TARGET_MANA, &targetMana, nullptr, nullptr, true);
                break;
            }
            case POWER_RAGE:
                triggeredSpellId = SPELL_PRIEST_RAPTURE_TARGET_RAGE;
                break;
            case POWER_ENERGY:
                triggeredSpellId = !target->HasAura(SPELL_PRIEST_RAPTURE_ENERGY_EXCLUSION) ? SPELL_PRIEST_RAPTURE_TARGET_ENERGY : 0;
                break;
            case POWER_RUNIC_POWER:
                triggeredSpellId = SPELL_PRIEST_RAPTURE_TARGET_RUNIC_POWER;
                break;
            default:
                break;
        }

        if (triggeredSpellId)
            caster->CastSpell(target, triggeredSpellId, true);
    }

    void ReflectDamage(AuraEffect* aurEff, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        Unit* target = GetTarget();
        if (dmgInfo.GetAttacker() == target)
            return;

        if (Unit* owner = GetUnitOwner())
            if (AuraEffect* talentAurEff = owner->GetAuraEffectOfRankedSpell(SPELL_PRIEST_REFLECTIVE_SHIELD_R1, EFFECT_0))
            {
                int32 bp = CalculatePct(absorbAmount, talentAurEff->GetAmount());
                // xinef: prevents infinite loop!
                if (!dmgInfo.GetSpellInfo() || dmgInfo.GetSpellInfo()->Id != SPELL_PRIEST_REFLECTIVE_SHIELD_TRIGGERED)
                    target->CastCustomSpell(dmgInfo.GetAttacker(), SPELL_PRIEST_REFLECTIVE_SHIELD_TRIGGERED, &bp, nullptr, nullptr, true, nullptr, aurEff);
            }
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_power_word_shield_aura::CalculateAmount, EFFECT_0, SPELL_AURA_SCHOOL_ABSORB);
        AfterEffectAbsorb += AuraEffectAbsorbFn(spell_pri_power_word_shield_aura::ReflectDamage, EFFECT_0);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pri_power_word_shield_aura::HandleRapture, EFFECT_0, SPELL_AURA_SCHOOL_ABSORB, AURA_EFFECT_HANDLE_REAL);
    }
};

class spell_pri_power_word_shield : public SpellScript
{
    PrepareSpellScript(spell_pri_power_word_shield);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_WEAKENED_SOUL, SPELL_PRIEST_GREATER_POWER_WORD_SHIELD,
                                   SPELL_PRIEST_GREATER_POWER_WORD_SHIELD_READY, SPELL_PRIEST_RENEWED_HOPE_BUFF });
    }

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!target)
            return SPELL_FAILED_BAD_TARGETS;

        if (AuraEffect* aurEff = target->GetAuraEffect(SPELL_AURA_SCHOOL_ABSORB, (SpellFamilyNames)GetSpellInfo()->SpellFamilyName, GetSpellInfo()->SpellIconID, EFFECT_0))
        {
            int32 newAmount = GetSpellInfo()->Effects[EFFECT_0].CalcValue(caster, nullptr, nullptr);
            newAmount = CalculateSpellAmount(caster, newAmount, GetSpellInfo(), aurEff);

            if (aurEff->GetAmount() > newAmount)
                return SPELL_FAILED_AURA_BOUNCED;
        }

        return SPELL_CAST_OK;
    }

    /*
     * Inner Focus (2,1) "Power Word: Shield: reduces Weakened Soul duration by 10 sec". The charge
     * is recorded in BeforeCast and never later: Inner Focus is a one-charge aura, and the normal
     * SpellMod path consumes it during the cast, so an AfterCast/AfterHit read would always come
     * back false.
     */
    void RecordInnerFocus()
    {
        _innerFocus = GetCaster() && GetCaster()->HasAura(SPELL_PRIEST_INNER_FOCUS);
    }

    void HandleHit()
    {
        Unit* target = GetHitUnit();
        if (!target)
            return;

        _primaryTargetGuid = target->GetGUID();

        if (!_innerFocus)
            return;

        // Weakened Soul has just been applied by the shield's own trigger effect, and Reprieve's
        // duration SpellMod has already been folded into it.
        if (Aura* weakenedSoul = target->GetAura(SPELL_PRIEST_WEAKENED_SOUL))
        {
            int32 remaining = weakenedSoul->GetDuration() - PRIEST_INNER_FOCUS_WEAKENED_SOUL_REDUCTION_MS;
            if (remaining <= 0)
                target->RemoveAura(weakenedSoul);
            else
                weakenedSoul->SetDuration(remaining);
        }
    }

    /*
     * Greater Power Word: Shield (docs/reworks/priest-disc-rework.md): Renewed Hope's capstone
     * proc "replaces Power Word: Shield" with a version that "shields the target and the 2 nearest
     * injured allies". Implemented as two extra 200155 absorbs rather than a separate castable
     * spell, so the primary target keeps the real shield (and the only Weakened Soul).
     *
     * The extra shields go out with TRIGGERED_FULL_MASK so they raise no proc events of their own -
     * that is what keeps Borrowed Time and Copious Power firing once, from the primary cast, per
     * the design doc's rules list. Renewed Hope's damage reduction and Grace therefore have to be
     * applied here by hand, since the primary's proc chain never sees these targets.
     */
    void HandleGreaterShield()
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->HasAura(SPELL_PRIEST_GREATER_POWER_WORD_SHIELD_READY))
            return;

        Unit* primary = ObjectAccessor::GetUnit(*caster, _primaryTargetGuid);
        if (!primary)
            return;

        std::list<Unit*> extraTargets;
        SelectNearbyInjuredRaidAllies(caster, primary, PRIEST_GREATER_PWS_RADIUS, PRIEST_GREATER_PWS_EXTRA_TARGETS, primary, extraTargets);

        // Already carrying this caster's Greater Power Word: Shield - don't overwrite it.
        extraTargets.remove_if([caster](Unit* unit) { return unit->GetAura(SPELL_PRIEST_GREATER_POWER_WORD_SHIELD, caster->GetGUID()) != nullptr; });
        if (extraTargets.empty())
            return;

        uint32 graceBuff = GetGraceBuffForCaster(caster);
        bool renewedHope = caster->HasAura(SPELL_PRIEST_RENEWED_HOPE_R1) || caster->HasAura(SPELL_PRIEST_RENEWED_HOPE_R2);

        for (Unit* extraTarget : extraTargets)
        {
            caster->CastSpell(extraTarget, SPELL_PRIEST_GREATER_POWER_WORD_SHIELD, TRIGGERED_FULL_MASK);

            if (renewedHope)
                caster->CastSpell(extraTarget, SPELL_PRIEST_RENEWED_HOPE_BUFF, true);

            if (graceBuff)
                caster->CastSpell(extraTarget, graceBuff, true);
        }

        caster->RemoveAurasDueToSpell(SPELL_PRIEST_GREATER_POWER_WORD_SHIELD_READY);
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_pri_power_word_shield::CheckCast);
        BeforeCast += SpellCastFn(spell_pri_power_word_shield::RecordInnerFocus);
        AfterHit += SpellHitFn(spell_pri_power_word_shield::HandleHit);
        AfterCast += SpellCastFn(spell_pri_power_word_shield::HandleGreaterShield);
    }

private:
    ObjectGuid _primaryTargetGuid;
    bool _innerFocus = false;
};

// 33110 - Prayer of Mending Heal
class spell_pri_prayer_of_mending_heal : public SpellScript
{
    PrepareSpellScript(spell_pri_prayer_of_mending_heal);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
            {
                SPELL_PRIEST_T9_HEALING_2P,
                SPELL_PRIEST_TWIN_DISCIPLINE_R1,
                SPELL_PRIEST_SPIRITUAL_HEALING_R1,
                SPELL_PRIEST_DIVINE_PROVIDENCE_R1
            });
    }

    void HandleHeal(SpellEffIndex /*effIndex*/)
    {
        if (Unit* caster = GetOriginalCaster())
        {
            int32 heal = GetEffectValue();
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_PRIEST_T9_HEALING_2P, EFFECT_0))
            {
                AddPct(heal, aurEff->GetAmount());
            }

            if (AuraEffect* aurEff = caster->GetAuraEffectOfRankedSpell(SPELL_PRIEST_TWIN_DISCIPLINE_R1, EFFECT_0))
            {
                AddPct(heal, aurEff->GetAmount());
            }
            if (AuraEffect* aurEff = caster->GetAuraEffectOfRankedSpell(SPELL_PRIEST_SPIRITUAL_HEALING_R1, EFFECT_0))
            {
                AddPct(heal, aurEff->GetAmount());
            }
            if (AuraEffect* aurEff = caster->GetAuraEffectOfRankedSpell(SPELL_PRIEST_DIVINE_PROVIDENCE_R1, EFFECT_0))
            {
                AddPct(heal, aurEff->GetAmount());
            }

            SetEffectValue(heal);
        }
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_pri_prayer_of_mending_heal::HandleHeal, EFFECT_0, SPELL_EFFECT_HEAL);
    }
};

// -139 - Renew
class spell_pri_renew : public AuraScript
{
    PrepareAuraScript(spell_pri_renew);

    bool Load() override
    {
        return GetCaster() && GetCaster()->IsPlayer();
    }

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({SPELL_PRIEST_EMPOWERED_RENEW});
    }

    void HandleApplyEffect(AuraEffect const* aurEff, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
        {
            // Empowered Renew
            if (AuraEffect const* empoweredRenewAurEff = caster->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_ID_EMPOWERED_RENEW_TALENT, EFFECT_1))
            {
                uint32 heal = GetEffect(EFFECT_0)->GetAmount();
                heal = GetTarget()->SpellHealingBonusTaken(caster, GetSpellInfo(), heal, DOT);

                int32 basepoints0 = empoweredRenewAurEff->GetAmount() * GetEffect(EFFECT_0)->GetTotalTicks() * int32(heal) / 100;
                caster->CastCustomSpell(GetTarget(), SPELL_PRIEST_EMPOWERED_RENEW, &basepoints0, nullptr, nullptr, true, nullptr, aurEff);
            }
        }
    }

    void Register() override
    {
        OnEffectApply += AuraEffectApplyFn(spell_pri_renew::HandleApplyEffect, EFFECT_0, SPELL_AURA_PERIODIC_HEAL, AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK);
    }
};

// -32379 - Shadow Word Death
class spell_pri_shadow_word_death : public SpellScript
{
    PrepareSpellScript(spell_pri_shadow_word_death);

    void HandleDamage()
    {
        int32 damage = GetHitDamage();

        // Pain and Suffering reduces damage
        if (AuraEffect* aurEff = GetCaster()->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_ID_PAIN_AND_SUFFERING, EFFECT_1))
            AddPct(damage, aurEff->GetAmount());

        GetCaster()->CastCustomSpell(GetCaster(), SPELL_PRIEST_SHADOW_WORD_DEATH, &damage, 0, 0, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pri_shadow_word_death::HandleDamage);
    }
};

// -34914 - Vampiric Touch
class spell_pri_vampiric_touch : public AuraScript
{
    PrepareAuraScript(spell_pri_vampiric_touch);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_VAMPIRIC_TOUCH_DISPEL });
    }

    void HandleDispel(DispelInfo* /*dispelInfo*/)
    {
        if (Unit* caster = GetCaster())
            if (Unit* target = GetUnitOwner())
                if (AuraEffect const* aurEff = GetEffect(EFFECT_1))
                {
                    int32 damage = aurEff->GetBaseAmount();
                    damage = aurEff->GetSpellInfo()->Effects[EFFECT_1].CalcValue(caster, &damage, nullptr) * 8;
                    // backfire damage
                    caster->CastCustomSpell(target, SPELL_PRIEST_VAMPIRIC_TOUCH_DISPEL, &damage, nullptr, nullptr, true, nullptr, aurEff);
                }
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (!eventInfo.GetActionTarget() || GetOwner()->GetGUID() != eventInfo.GetActionTarget()->GetGUID())
        {
            return false;
        }

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        if (!spellInfo || spellInfo->SpellFamilyName != SPELLFAMILY_PRIEST || !(spellInfo->SpellFamilyFlags[0] & 0x00002000))
        {
            return false;
        }

        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        if (Unit* actor = eventInfo.GetActor())
        {
            actor->CastSpell(actor, 57669, true, nullptr, aurEff);
        }
    }

    void Register() override
    {
        AfterDispel += AuraDispelFn(spell_pri_vampiric_touch::HandleDispel);
        DoCheckProc += AuraCheckProcFn(spell_pri_vampiric_touch::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_vampiric_touch::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 605 - Mind Control
class spell_pri_mind_control : public AuraScript
{
    PrepareAuraScript(spell_pri_mind_control);

    void HandleApplyEffect(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
        {
            if (Unit* target = GetTarget())
            {
                caster->SetInCombatWith(target);
                target->SetInCombatWith(caster);
            }
        }
    }

    void HandleRemoveEffect(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
        {
            if (Unit* target = GetTarget())
            {
                caster->SetCombatTimer(0);
                target->SetCombatTimer(0);
            }
        }
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pri_mind_control::HandleApplyEffect, EFFECT_0, SPELL_AURA_MOD_POSSESS, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pri_mind_control::HandleRemoveEffect, EFFECT_0, SPELL_AURA_MOD_POSSESS, AURA_EFFECT_HANDLE_REAL);
    }
};

// 37565 - Flexibility | Item - Priest T4 Holy/Discipline 4P Bonus
class spell_pri_t4_4p_bonus : public AuraScript
{
    PrepareAuraScript(spell_pri_t4_4p_bonus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_T4_4P_FLEXIBILITY });
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        GetTarget()->RemoveAurasDueToSpell(SPELL_PRIEST_T4_4P_FLEXIBILITY);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_t4_4p_bonus::HandleProc, EFFECT_ALL, SPELL_AURA_OVERRIDE_CLASS_SCRIPTS);
    }
};

// 57989 - Shadowfiend Death
class spell_pri_shadowfiend_death : public AuraScript
{
    PrepareAuraScript(spell_pri_shadowfiend_death);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_GLYPH_OF_SHADOWFIEND_MANA });
    }

    bool AfterCheckProc(ProcEventInfo& eventInfo, bool isTriggeredAtSpellProcEvent)
    {
        if (!isTriggeredAtSpellProcEvent)
            return false;
        return eventInfo.GetTypeMask() & PROC_FLAG_KILLED;
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        if (Unit* owner = GetTarget()->GetOwner())
            if (owner->HasAura(SPELL_PRIEST_GLYPH_OF_SHADOWFIEND))
                owner->CastSpell(owner, SPELL_PRIEST_GLYPH_OF_SHADOWFIEND_MANA, true);
    }

    void Register() override
    {
        DoAfterCheckProc += AuraAfterCheckProcFn(spell_pri_shadowfiend_death::AfterCheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_shadowfiend_death::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 15286 - Vampiric Embrace
class spell_pri_vampiric_embrace : public AuraScript
{
    PrepareAuraScript(spell_pri_vampiric_embrace);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_VAMPIRIC_EMBRACE_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // Not proc from Mind Sear
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (!procSpell)
            return false;

        return !(procSpell->SpellFamilyFlags[1] & 0x80000);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        if (!damageInfo || !damageInfo->GetDamage())
            return;

        int32 selfHeal = CalculatePct(static_cast<int32>(damageInfo->GetDamage()), aurEff->GetAmount());
        int32 partyHeal = selfHeal / 5;
        GetTarget()->CastCustomSpell(GetTarget(), SPELL_PRIEST_VAMPIRIC_EMBRACE_HEAL, &partyHeal, &selfHeal, nullptr, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_vampiric_embrace::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_vampiric_embrace::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 55677 - Glyph of Dispel Magic
class spell_pri_glyph_of_dispel_magic : public AuraScript
{
    PrepareAuraScript(spell_pri_glyph_of_dispel_magic);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_GLYPH_OF_DISPEL_MAGIC_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (!procSpell)
            return false;

        // Dispel Magic shares spellfamilyflag with abolish disease - check icon
        if (procSpell->SpellIconID != 74)
            return false;

        Unit* target = eventInfo.GetActionTarget();
        if (!target || !target->IsFriendlyTo(GetTarget()))
            return false;

        return true;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* target = eventInfo.GetActionTarget();
        if (!target)
            return;

        int32 bp = int32(target->CountPctFromMaxHealth(aurEff->GetAmount()));
        GetTarget()->CastCustomSpell(SPELL_PRIEST_GLYPH_OF_DISPEL_MAGIC_HEAL, SPELLVALUE_BASE_POINT0, bp, target, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_glyph_of_dispel_magic::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_glyph_of_dispel_magic::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -64127 - Body and Soul
class spell_pri_body_and_soul : public AuraScript
{
    PrepareAuraScript(spell_pri_body_and_soul);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_BODY_AND_SOUL_SPEED });
    }

    bool CheckProcTriggerSpell(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && (spellInfo->SpellFamilyFlags[0] & 0x00000001) != 0;
    }

    bool CheckProcDummy(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        if (eventInfo.GetActor() != eventInfo.GetActionTarget())
            return false;

        SpellInfo const* spellInfo = eventInfo.GetSpellInfo();
        return spellInfo && spellInfo->Id == 552;
    }

    void HandleProcDummy(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        if (roll_chance_i(aurEff->GetAmount()))
            eventInfo.GetActor()->CastSpell(eventInfo.GetActor(), SPELL_PRIEST_BODY_AND_SOUL_SPEED, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckEffectProc += AuraCheckEffectProcFn(spell_pri_body_and_soul::CheckProcTriggerSpell, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
        DoCheckEffectProc += AuraCheckEffectProcFn(spell_pri_body_and_soul::CheckProcDummy, EFFECT_1, SPELL_AURA_DUMMY);
        OnEffectProc += AuraEffectProcFn(spell_pri_body_and_soul::HandleProcDummy, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// 47569, 47570 - Improved Shadowform
class spell_pri_improved_shadowform : public AuraScript
{
    PrepareAuraScript(spell_pri_improved_shadowform);

    bool CheckProc(ProcEventInfo& /*eventInfo*/)
    {
        return roll_chance_i(GetEffect(EFFECT_0)->GetAmount());
    }

    void HandleProc(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        GetTarget()->RemoveMovementImpairingAuras(true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_improved_shadowform::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_improved_shadowform::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 26169 - AQ 3P Bonus
class spell_pri_aq_3p_bonus : public AuraScript
{
    PrepareAuraScript(spell_pri_aq_3p_bonus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_ORACULAR_HEAL });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (eventInfo.GetActor() == eventInfo.GetActionTarget())
            return false;

        HealInfo* healInfo = eventInfo.GetHealInfo();
        return healInfo && healInfo->GetHeal();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        int32 bp0 = CalculatePct(eventInfo.GetHealInfo()->GetHeal(), 10);
        eventInfo.GetActor()->CastCustomSpell(SPELL_PRIEST_ORACULAR_HEAL, SPELLVALUE_BASE_POINT0, bp0, eventInfo.GetActor(), true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_aq_3p_bonus::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_aq_3p_bonus::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -47569 - Improved Shadowform (talent)
class spell_pri_imp_shadowform : public AuraScript
{
    PrepareAuraScript(spell_pri_imp_shadowform);

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        if (roll_chance_i(aurEff->GetAmount()))
            GetTarget()->RemoveMovementImpairingAuras(true);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_imp_shadowform::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -15337 - Improved Spirit Tap
class spell_pri_improved_spirit_tap : public AuraScript
{
    PrepareAuraScript(spell_pri_improved_spirit_tap);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
        {
            SPELL_PRIEST_SHADOW_WORD_DEATH_R1,
            SPELL_PRIEST_MIND_BLAST_R1
        });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (SpellInfo const* spellInfo = eventInfo.GetSpellInfo())
        {
            if (spellInfo->IsRankOf(sSpellMgr->AssertSpellInfo(SPELL_PRIEST_SHADOW_WORD_DEATH_R1)) ||
                spellInfo->IsRankOf(sSpellMgr->AssertSpellInfo(SPELL_PRIEST_MIND_BLAST_R1)))
                return true;
            else if (spellInfo->Id == SPELL_PRIEST_MIND_FLAY_DAMAGE)
                return roll_chance_i(50);
        }

        return false;
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_improved_spirit_tap::CheckProc);
    }
};

// 40438 - Priest Tier 6 Trinket
class spell_pri_item_t6_trinket : public AuraScript
{
    PrepareAuraScript(spell_pri_item_t6_trinket);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
        {
            SPELL_PRIEST_DIVINE_BLESSING,
            SPELL_PRIEST_DIVINE_WRATH
        });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* caster = eventInfo.GetActor();
        if (eventInfo.GetSpellTypeMask() & PROC_SPELL_TYPE_HEAL)
            caster->CastSpell(caster, SPELL_PRIEST_DIVINE_BLESSING, true, nullptr, aurEff);

        if (eventInfo.GetSpellTypeMask() & PROC_SPELL_TYPE_DAMAGE)
            caster->CastSpell(caster, SPELL_PRIEST_DIVINE_WRATH, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_item_t6_trinket::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 28809 - T3 4P Bonus
class spell_pri_t3_4p_bonus : public AuraScript
{
    PrepareAuraScript(spell_pri_t3_4p_bonus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_ARMOR_OF_FAITH });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        eventInfo.GetActor()->CastSpell(eventInfo.GetActionTarget(), SPELL_PRIEST_ARMOR_OF_FAITH, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_t3_4p_bonus::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 37594 - Greater Heal Refund / T5 2P Bonus
class spell_pri_t5_heal_2p_bonus : public AuraScript
{
    PrepareAuraScript(spell_pri_t5_heal_2p_bonus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_ITEM_EFFICIENCY });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        if (HealInfo* healInfo = eventInfo.GetHealInfo())
            if (Unit* healTarget = healInfo->GetTarget())
                if (healInfo->GetEffectiveHeal())
                    if (healTarget->GetHealth() >= healTarget->GetMaxHealth())
                        return true;

        return false;
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();
        GetTarget()->CastSpell(GetTarget(), SPELL_PRIEST_ITEM_EFFICIENCY, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_t5_heal_2p_bonus::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_t5_heal_2p_bonus::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 70770 - Item - Priest T10 Healer 2P Bonus
class spell_pri_t10_heal_2p_bonus : public AuraScript
{
    PrepareAuraScript(spell_pri_t10_heal_2p_bonus);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_BLESSED_HEALING });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo* healInfo = eventInfo.GetHealInfo();
        return healInfo && healInfo->GetHeal();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        SpellInfo const* spellInfo = sSpellMgr->AssertSpellInfo(SPELL_PRIEST_BLESSED_HEALING);
        int32 amount = CalculatePct(static_cast<int32>(eventInfo.GetHealInfo()->GetHeal()), aurEff->GetAmount());

        ASSERT(spellInfo->GetMaxTicks() > 0);
        amount /= spellInfo->GetMaxTicks();

        Unit* caster = eventInfo.GetActor();
        Unit* target = eventInfo.GetActionTarget();

        caster->CastCustomSpell(target, SPELL_PRIEST_BLESSED_HEALING, &amount, nullptr, nullptr, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_t10_heal_2p_bonus::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_t10_heal_2p_bonus::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// -47580 - Pain and Suffering (dummy aura)
class spell_pri_pain_and_suffering_dummy : public AuraScript
{
    PrepareAuraScript(spell_pri_pain_and_suffering_dummy);

    bool CheckDummy(AuraEffect const* /*aurEff*/, ProcEventInfo& /*eventInfo*/)
    {
        return false;
    }

    void Register() override
    {
        DoCheckEffectProc += AuraCheckEffectProcFn(spell_pri_pain_and_suffering_dummy::CheckDummy, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// -27811 - Blessed Recovery
class spell_pri_blessed_recovery : public AuraScript
{
    PrepareAuraScript(spell_pri_blessed_recovery);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_BLESSED_RECOVERY_R1 });
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        DamageInfo* dmgInfo = eventInfo.GetDamageInfo();
        if (!dmgInfo || !dmgInfo->GetDamage())
            return;

        Unit* target = eventInfo.GetActionTarget();
        uint32 triggerSpell = sSpellMgr->GetSpellWithRank(SPELL_PRIEST_BLESSED_RECOVERY_R1, aurEff->GetSpellInfo()->GetRank());
        SpellInfo const* triggerInfo = sSpellMgr->AssertSpellInfo(triggerSpell);

        int32 bp = CalculatePct(static_cast<int32>(dmgInfo->GetDamage()), aurEff->GetAmount());

        ASSERT(triggerInfo->GetMaxTicks() > 0);
        bp /= triggerInfo->GetMaxTicks();

        target->CastCustomSpell(target, triggerSpell, &bp, nullptr, nullptr, true, nullptr, aurEff);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_pri_blessed_recovery::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

void AddSC_priest_spell_scripts()
{
    RegisterSpellScript(spell_pri_shadowfiend_scaling);
    RegisterSpellScript(spell_pri_circle_of_healing);
    RegisterSpellScript(spell_pri_divine_aegis);
    RegisterSpellScript(spell_pri_divine_hymn);
    RegisterSpellScript(spell_pri_glyph_of_prayer_of_healing);
    RegisterSpellScript(spell_pri_guardian_spirit);
    RegisterSpellScript(spell_pri_hymn_of_hope);
    RegisterSpellScript(spell_pri_lightwell);
    RegisterSpellScript(spell_pri_lightwell_renew);
    RegisterSpellScript(spell_pri_mana_burn);
    RegisterSpellScript(spell_pri_mana_leech);
    RegisterSpellScript(spell_pri_mind_sear);
    RegisterSpellScript(spell_pri_pain_and_suffering_dummy);
    RegisterSpellScript(spell_pri_pain_and_suffering_proc);
    RegisterSpellScript(spell_pri_penance);
    RegisterSpellAndAuraScriptPair(spell_pri_power_word_shield, spell_pri_power_word_shield_aura);
    // RegisterSpellAndAuraScriptPair names the loader after its *first* argument, so the pair
    // above is only reachable from spell_script_names as "spell_pri_power_word_shield". Greater
    // Power Word: Shield (200155) needs the aura half alone - it has no cast of its own, no
    // Weakened Soul and no CheckCast - so the same AuraScript is registered a second time under
    // its own name for that binding (DISC.md: `scripted_by(200155, 'spell_pri_power_word_shield_aura')`).
    RegisterSpellScript(spell_pri_power_word_shield_aura);
    RegisterSpellScript(spell_pri_prayer_of_mending_heal);
    RegisterSpellScript(spell_pri_renew);
    RegisterSpellScript(spell_pri_shadow_word_death);
    RegisterSpellScript(spell_pri_vampiric_touch);
    RegisterSpellScript(spell_pri_mind_control);
    RegisterSpellScript(spell_pri_t4_4p_bonus);
    RegisterSpellScript(spell_pri_shadowfiend_death);
    RegisterSpellScript(spell_pri_vampiric_embrace);
    RegisterSpellScript(spell_pri_glyph_of_dispel_magic);
    RegisterSpellScript(spell_pri_body_and_soul);
    RegisterSpellScript(spell_pri_improved_shadowform);
    // Proc system scripts
    RegisterSpellScript(spell_pri_aq_3p_bonus);
    RegisterSpellScript(spell_pri_blessed_recovery);
    RegisterSpellScript(spell_pri_imp_shadowform);
    RegisterSpellScript(spell_pri_improved_spirit_tap);
    RegisterSpellScript(spell_pri_item_t6_trinket);
    RegisterSpellScript(spell_pri_t3_4p_bonus);
    RegisterSpellScript(spell_pri_t5_heal_2p_bonus);
    RegisterSpellScript(spell_pri_t10_heal_2p_bonus);
}
