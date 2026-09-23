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
 * Priest Holy rework (docs/reworks/priest-holy-rework.md,
 * .agents/plans/priest-rework/priest-rework.HOLY.md) - every genuinely new script class this pass
 * needs goes here, same "spell_pri_" naming convention as spell_priest.cpp / spell_priest_new.cpp /
 * spell_priest_disc.cpp. Talents that only retune an existing stock script (spell_pri_renew,
 * spell_pri_circle_of_healing, spell_pri_blessed_recovery, spell_pri_body_and_soul,
 * npc_pet_pri_lightwell, spell_pri_halo_pulse - see HOLY.md's "Stock scripts touched by WP-B" list)
 * are edited in place in their existing files instead. Hooks that can't be a SpellScript/AuraScript
 * at all live in PriestMechanics.h/.cpp next to the core call sites that need them.
 *
 * spell_pri_circle_of_healing (8,1) needed NO change at all: its stock FilterTargets already
 * selects "party/raid within the aura's own radius, sorted ascending by HP%, capped at 5" -
 * Acore::HealthPctOrderPred() defaults to ascending (Unit.h), i.e. lowest-HP%-first, which is
 * exactly "5 most injured." The only real change for that row is WP-A's Amount/coefficient data.
 */

#include "Cell.h"
#include "CellImpl.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Player.h"
#include "PriestMechanics.h"
#include "SpellAuraEffects.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include <algorithm>
#include <cmath>

/*
 * Rank spell ids from HOLY.md's talent table / ID map - never talent_dbc ids (PLAN sec 3.10).
 * Real stock spell ids this file's scripts need by number are listed alongside.
 */
enum PriestHolySpells
{
    // Real stock/baseline spells.
    SPELL_PRIEST_GREATER_HEAL              = 2060,
    SPELL_PRIEST_FLASH_HEAL                = 2061,
    SPELL_PRIEST_BINDING_HEAL              = 32546,
    SPELL_PRIEST_PRAYER_OF_HEALING         = 596,
    SPELL_PRIEST_CIRCLE_OF_HEALING         = 34861,
    SPELL_PRIEST_RENEW                     = 139,
    SPELL_PRIEST_SMITE                     = 585,
    SPELL_PRIEST_HOLY_FIRE                 = 14914,
    SPELL_PALADIN_HOLY_LIGHT               = 635,
    SPELL_PALADIN_FLASH_OF_LIGHT           = 19750,

    // 0,0 Healing Focus.
    SPELL_PRIEST_HEALING_FOCUS_R2          = 15012,
    SPELL_PRIEST_HEALING_FOCUS_BUFF        = 200172,

    // 2,1 Answered Prayers.
    SPELL_PRIEST_ANSWERED_PRAYERS_BUFF     = 200182,

    // 3,0 Holy Reach.
    SPELL_PRIEST_HOLY_REACH_R2             = 27790,
    SPELL_PRIEST_HOLY_REACH_MANA           = 200185,

    // 3,3 Kindled Faith.
    SPELL_PRIEST_KINDLED_FAITH_R1          = 200187,
    SPELL_PRIEST_KINDLED_FAITH_R2          = 200188,
    SPELL_PRIEST_KINDLED_FAITH_R3          = 200189,
    SPELL_PRIEST_KINDLED_FAITH_BUFF        = 200190,

    // 4,1 Spirit of Redemption.
    SPELL_PRIEST_SPIRIT_OF_REDEMPTION_R3   = 200192,
    SPELL_PRIEST_SPIRIT_OF_REDEMPTION_FORM = 200194,
    SPELL_PRIEST_SPIRIT_OF_REDEMPTION_HEALS = 200226,

    // 5,0 Surge of Light.
    SPELL_PRIEST_SURGE_OF_LIGHT_BUFF       = 33151,

    // 5,1 / 5,3 / 8,3 / 9,3 Holy Words + Echo of Light.
    SPELL_PRIEST_HOLY_WORD_SERENITY        = 200197,
    SPELL_PRIEST_HOLY_WORD_SANCTIFY        = 200198,
    SPELL_PRIEST_HOLY_WORD_CHASTISE        = 200223,
    SPELL_PRIEST_ECHO_OF_LIGHT_R1          = 200215,
    SPELL_PRIEST_ECHO_OF_LIGHT_R2          = 200216,
    SPELL_PRIEST_ECHO_OF_LIGHT_R3          = 200217,

    // 6,0 Holy Concentration.
    SPELL_PRIEST_HOLY_CONCENTRATION_R1     = 34753,

    // 6,2 Blessed Warding.
    SPELL_PRIEST_BLESSED_WARDING_BUFF      = 200206,

    // 7,2 Serendipity.
    SPELL_PRIEST_SERENDIPITY_R1            = 63730,
    SPELL_PRIEST_SERENDIPITY_R2            = 63733,
    SPELL_PRIEST_SERENDIPITY_R3            = 63737,
    SPELL_PRIEST_SERENDIPITY_BUFF_R1       = 63731,
    // Not ascending-ID order: the talent ranks' own trigger_spell wiring (priest_trigger_spells.py,
    // serendipity_63733/63737's notes) casts 63735 (-10%) from rank 2 and 63734 (-15%) from rank 3 -
    // confirmed against each buff's own EffectBasePoints. Keep these matched to that, not to ID order.
    SPELL_PRIEST_SERENDIPITY_BUFF_R2       = 63735,
    SPELL_PRIEST_SERENDIPITY_BUFF_R3       = 63734,

    // 7,3 Holy Wrath.
    SPELL_PRIEST_HOLY_WRATH_R3             = 200212,
    SPELL_PRIEST_HOLY_WRATH_CRIT_BUFF      = 200213,
    SPELL_PRIEST_HOLY_WRATH_MAGIC_DMG_BUFF = 200214,

    // 8,0 Empowered Renew.
    SPELL_PRIEST_EMPOWERED_RENEW_R3        = 63543,

    // 10,1 Apotheosis.
    SPELL_PRIEST_APOTHEOSIS                = 200225
};

namespace
{
    // Holy Concentration's stock SpellIconID (apps/dbc-tools/source/classes/priest/
    // priest_trigger_spells.py: holy_concentration_34753, `spell_icon_id=2169`) - a real existing
    // talent being reworked, so (unlike Echo of Light below) it already has a stable icon to key
    // the marker-aura-by-icon read on (PLAN sec 3.9).
    constexpr uint32 PRIEST_ICON_HOLY_CONCENTRATION = 2169;

    // Echo of Light (8,3) reservoir is always redistributed across exactly 3 ticks (design doc
    // 5.1: "6 sec, 3 ticks at a fixed 2 sec interval").
    constexpr int32 PRIEST_ECHO_OF_LIGHT_TICKS = 3;

    // Echo of Light counts Mastery at triple weight (user tuning call, 2026-09-22): Mastery is the
    // only stat this whole tree reads (design doc 1), so at 1x it moved the Echo too little to be
    // worth gearing for. Applies to the Mastery bonus only, never to the rank's base %.
    constexpr float PRIEST_ECHO_OF_LIGHT_MASTERY_WEIGHT = 3.0f;

    // Echo of Light's per-rank base (design doc 5.1: 25 / 30 / 35% of the Holy Word's amount) -
    // read from the rank's hidden EFFECT_1 dummy ($s2 in the tooltip, priest_trigger_spells.py
    // echo_of_light_200215..200217) so the tooltip and the math can't drift apart. A brand-new
    // talent (60019) has no existing stock SpellIconID to key a marker-aura-by-icon read on, so
    // this checks the 3 pre-assigned rank *spell* ids directly (HOLY.md ID map: 200215/200216/
    // 200217), highest rank first. Returns 0 when the talent isn't taken.
    int32 GetEchoOfLightBasePct(Unit* caster)
    {
        for (uint32 rankSpellId : { SPELL_PRIEST_ECHO_OF_LIGHT_R3, SPELL_PRIEST_ECHO_OF_LIGHT_R2,
                                    SPELL_PRIEST_ECHO_OF_LIGHT_R1 })
            if (AuraEffect const* rank = caster->GetAuraEffect(rankSpellId, EFFECT_1))
                return rank->GetAmount();
        return 0;
    }

    /*
     * Echo of Light (8,3) shared apply helper - design doc 5.1. `rawAmount` is the full pre-
     * overheal/overkill amount of the Holy Word that just landed; `echoSpellId` is 200218 (heal) or
     * 200219 (damage). Handles the reservoir math ("take the amount not yet delivered by the
     * existing Echo, add the new amount, redistribute across a fresh 6 sec/3 ticks") and the
     * done/taken bonus snapshot ("does not re-evaluate per tick" - baked in once, here, since
     * SpellAuraEffects.cpp's IsFixedCadencePeriodic() exempts the tick itself from re-applying
     * them). Casting the same spell id on the same target from the same caster naturally
     * refreshes/replaces the existing aura instance rather than stacking a second one.
     */
    void ApplyEchoOfLight(Unit* caster, Unit* target, int32 rawAmount, uint32 echoSpellId, bool isHeal)
    {
        if (!caster || !target || rawAmount <= 0)
            return;

        int32 basePct = GetEchoOfLightBasePct(caster);
        if (basePct <= 0)
            return;

        // "raw amount x base% x (1 + Mastery x 3)" (design doc 5.1). Mastery is a bonus on top of
        // the base Echo - AddPct, the same shape MageMechanics/PriestMechanics' other Mastery
        // consumers use - not a prerequisite for it: a Priest with 0 Mastery still gets the full
        // base Echo. (Originally "x Mastery" as a bare fraction, which silently zeroed the talent
        // on any character without Mastery gear - playtest 2026-09-22.)
        int32 amount = CalculatePct(rawAmount, basePct);
        if (Player* player = caster->ToPlayer())
            AddPct(amount, player->GetMasteryPercentage() * PRIEST_ECHO_OF_LIGHT_MASTERY_WEIGHT);
        if (amount <= 0)
            return;

        int32 remaining = 0;
        if (AuraEffect const* existing = target->GetAuraEffect(echoSpellId, EFFECT_0, caster->GetGUID()))
        {
            int32 const ticksLeft = std::max(0, existing->GetTotalTicks() - int32(existing->GetTickNumber()));
            remaining = existing->GetAmount() * ticksLeft;
        }

        int32 perTick = (remaining + amount) / PRIEST_ECHO_OF_LIGHT_TICKS;
        if (perTick <= 0)
            return;

        SpellInfo const* echoInfo = sSpellMgr->AssertSpellInfo(echoSpellId);
        if (isHeal)
            perTick = int32(target->SpellHealingBonusTaken(caster, echoInfo, uint32(perTick), DOT));
        else
            perTick = int32(target->SpellDamageBonusTaken(caster, echoInfo, uint32(perTick), DOT));

        caster->CastCustomSpell(echoSpellId, SPELLVALUE_BASE_POINT0, perTick, target, true);
    }
}

// Healing Focus (0,0) capstone - registered on rank 2 (15012) only, the idiom for "a capstone that
// only exists on the last rank" (PLAN sec 3.9). procs_on (WP-A data) already restricts this to a
// successful cast of Greater Heal/Prayer of Healing/Divine Hymn at chance=100; nothing left to gate
// here.
class spell_pri_healing_focus_capstone : public AuraScript
{
    PrepareAuraScript(spell_pri_healing_focus_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_HEALING_FOCUS_BUFF });
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        if (Unit* caster = eventInfo.GetActor())
            caster->CastSpell(caster, SPELL_PRIEST_HEALING_FOCUS_BUFF, true);
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_pri_healing_focus_capstone::HandleProc);
    }
};

/*
 * Answered Prayers (2,1) - SpellScript on Renew (139) itself rather than living inside
 * spell_pri_renew (an AuraScript on the Renew *aura*, which never sees the outer cast). Design doc
 * 5.4: "When the buff is consumed by a Renew cast, select 2 additional targets within 30 yds: (1)
 * prefer allies not carrying the caster's Renew, ascending HP%; (2) if fewer than 2 qualify, fill
 * from allies who do, ascending remaining Renew duration then ascending HP%." Spread Renews are
 * cast with TRIGGERED_FULL_MASK, which per design doc sec 6 must not itself re-roll Answered
 * Prayers, charge Serendipity, or trigger Body and Soul - TRIGGERED_FULL_MASK's proc suppression
 * (used throughout this codebase for "silent" triggered casts) covers all of that for free.
 */
class spell_pri_renew_cast : public SpellScript
{
    PrepareSpellScript(spell_pri_renew_cast);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_ANSWERED_PRAYERS_BUFF, SPELL_PRIEST_RENEW });
    }

    void SpreadRenew()
    {
        if (GetSpell()->IsTriggered())
            return;

        Unit* caster = GetCaster();
        if (!caster || !caster->HasAura(SPELL_PRIEST_ANSWERED_PRAYERS_BUFF))
            return;

        Unit* primaryTarget = GetExplTargetUnit();

        std::list<Unit*> nearby;
        Acore::AnyGroupedUnitInObjectRangeCheck check(caster, caster, 30.0f, true);
        Acore::UnitListSearcher<Acore::AnyGroupedUnitInObjectRangeCheck> searcher(caster, nearby, check);
        Cell::VisitObjects(caster, searcher, 30.0f);

        std::vector<Unit*> withoutRenew;
        std::vector<std::pair<int32, Unit*>> withRenew; // (remaining Renew ms, unit)
        for (Unit* unit : nearby)
        {
            if (unit == primaryTarget)
                continue;

            if (Aura const* renew = unit->GetAura(SPELL_PRIEST_RENEW, caster->GetGUID()))
                withRenew.emplace_back(renew->GetDuration(), unit);
            else
                withoutRenew.push_back(unit);
        }

        std::sort(withoutRenew.begin(), withoutRenew.end(), Acore::HealthPctOrderPred());
        std::sort(withRenew.begin(), withRenew.end(), [](auto const& a, auto const& b)
        {
            if (a.first != b.first)
                return a.first < b.first;
            return Acore::HealthPctOrderPred()(a.second, b.second);
        });

        std::vector<Unit*> chosen;
        for (Unit* unit : withoutRenew)
        {
            if (chosen.size() >= 2)
                break;
            chosen.push_back(unit);
        }
        for (auto const& entry : withRenew)
        {
            if (chosen.size() >= 2)
                break;
            chosen.push_back(entry.second);
        }

        for (Unit* unit : chosen)
            caster->CastSpell(unit, SPELL_PRIEST_RENEW, TRIGGERED_FULL_MASK);

        caster->RemoveAurasDueToSpell(SPELL_PRIEST_ANSWERED_PRAYERS_BUFF);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_pri_renew_cast::SpreadRenew);
    }
};

// Holy Reach (3,0) capstone - registered on rank 2 (27790) only. procs_on (WP-A data) provides the
// 20% chance and the 15 sec internal cooldown (spell_proc.Cooldown, not a spell cooldown - design
// doc sec 1 lists it explicitly as CD-Haste-exempt); this script only adds the ">20 yd" distance
// gate the proc row can't express and computes the restore amount.
class spell_pri_holy_reach_capstone : public AuraScript
{
    PrepareAuraScript(spell_pri_holy_reach_capstone);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_HOLY_REACH_MANA });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetActionTarget();
        if (!caster || !target)
            return false;

        return caster->GetDistance(target) > 20.0f;
    }

    void HandleProc(ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Player* player = GetTarget() ? GetTarget()->ToPlayer() : nullptr;
        if (!player)
            return;

        int32 missing = int32(player->GetMaxPower(POWER_MANA)) - int32(player->GetPower(POWER_MANA));
        if (missing <= 0)
            return;

        int32 perTick = int32(float(missing) * 0.02f / 4.0f);
        if (perTick <= 0)
            return;

        player->CastCustomSpell(SPELL_PRIEST_HOLY_REACH_MANA, SPELLVALUE_BASE_POINT0, perTick, player, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_holy_reach_capstone::CheckProc);
        OnProc += AuraProcFn(spell_pri_holy_reach_capstone::HandleProc);
    }
};

// Kindled Faith (3,3) - all 3 ranks bound to this one class via scripted_by (WP-A). procs_on
// supplies the 8/16/25% chance off Smite damage; design doc sec 5.7 explicitly wants no "only
// while on cooldown" gate, so this is a plain unconditional OnProc.
class spell_pri_kindled_faith : public AuraScript
{
    PrepareAuraScript(spell_pri_kindled_faith);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_KINDLED_FAITH_BUFF, SPELL_PRIEST_HOLY_FIRE });
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = eventInfo.GetActor() ? eventInfo.GetActor()->ToPlayer() : nullptr;
        if (!player)
            return;

        player->RemoveSpellCooldown(SPELL_PRIEST_HOLY_FIRE, true);
        player->CastSpell(player, SPELL_PRIEST_KINDLED_FAITH_BUFF, true);
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_pri_kindled_faith::HandleProc);
    }
};

/*
 * Spirit of Redemption (4,1) capstone - AuraScript on rank 3 (200192) only; its eff2/EFFECT_1
 * SCHOOL_ABSORB (misc 127, base -1) is script-driven, same CalculateAmount/OnEffectAbsorb shape as
 * the stock spell_pri_guardian_spirit / spell_pal_ardent_defender absorb-on-lethal pattern.
 * Cross-class: spell_rogue.cpp's Cheat Death and spell_paladin.cpp's Ardent Defender both check/set
 * the shared Priest::SPELL_CHEATED_DEATH_MARKER too (PLAN sec 1's "bidirectional via one shared
 * marker debuff").
 *
 * Deliberately does not use SPELL_AURA_SPIRIT_OF_REDEMPTION (aura 176, stock 27827): its handler
 * kills the target when the aura ends and every Unit::HasSpiritOfRedemptionAura() caller (Map
 * alive-count, battlegrounds, boss target exclusion) treats the priest as dead. This form is a
 * survive cooldown - pacify + root + -50% damage taken, no immunity - per design doc 4,1.
 */
class spell_pri_spirit_of_redemption : public AuraScript
{
    PrepareAuraScript(spell_pri_spirit_of_redemption);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo(
        {
            Priest::SPELL_CHEATED_DEATH_MARKER,
            SPELL_PRIEST_SPIRIT_OF_REDEMPTION_FORM,
            SPELL_PRIEST_SPIRIT_OF_REDEMPTION_HEALS
        });
    }

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& /*canBeRecalculated*/)
    {
        amount = -1;
    }

    void Absorb(AuraEffect* /*aurEff*/, DamageInfo& dmgInfo, uint32& absorbAmount)
    {
        Unit* target = GetTarget();
        if (dmgInfo.GetDamage() < target->GetHealth())
            return;

        if (target->HasAura(Priest::SPELL_CHEATED_DEATH_MARKER))
            return;

        // Same guard the old Unit::Kill hardcode had: a priest killed by falling off the map dies
        // instead of being rooted somewhere unreachable for 5 s.
        if (Player const* player = target->ToPlayer())
            if (player->HasPlayerFlag(PLAYER_FLAGS_IS_OUT_OF_BOUNDS))
                return;

        // "Absorb otherwise lethal damage up to 300% of Spirit."
        int32 cap = int32(3.0f * target->GetStat(STAT_SPIRIT));
        int32 absorb = std::min<int32>(int32(dmgInfo.GetDamage()), std::max(cap, 0));
        absorbAmount = uint32(std::max(absorb, 0));

        int32 remainingHealth = int32(target->GetHealth()) - (int32(dmgInfo.GetDamage()) - absorb);
        if (remainingHealth <= 0)
            return; // The cap wasn't enough to prevent death - no Spirit of Redemption form.

        target->CastSpell(target, Priest::SPELL_CHEATED_DEATH_MARKER, true);
        target->CastSpell(target, SPELL_PRIEST_SPIRIT_OF_REDEMPTION_FORM, true);
        target->CastSpell(target, SPELL_PRIEST_SPIRIT_OF_REDEMPTION_HEALS, true);
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pri_spirit_of_redemption::CalculateAmount, EFFECT_1,
            SPELL_AURA_SCHOOL_ABSORB);
        OnEffectAbsorb += AuraEffectAbsorbFn(spell_pri_spirit_of_redemption::Absorb, EFFECT_1);
    }
};

/*
 * Surge of Light (5,0) - registered on Smite (585) and Flash Heal (2061). The buff (33151,
 * StackAmount=2, ProcCharges=0) carries its own SPELLMOD_CASTING_TIME/COST/DAMAGE effects that
 * apply automatically while up; because ProcCharges=0 the engine won't auto-consume a stack on
 * use, so this script does that manually - only when the buff was actually present for *this*
 * cast, and only for a real (non-triggered) cast, so the free proc-reroll itself
 * (design doc 5.7: "the free cast can now crit and re-roll this proc") isn't double-consumed.
 */
class spell_pri_surge_of_light_consume : public SpellScript
{
    PrepareSpellScript(spell_pri_surge_of_light_consume);

    bool _hadBuff = false;

    void RecordBuff()
    {
        Unit* caster = GetCaster();
        _hadBuff = caster && caster->HasAura(SPELL_PRIEST_SURGE_OF_LIGHT_BUFF);
    }

    void ConsumeBuff()
    {
        if (!_hadBuff || GetSpell()->IsTriggered())
            return;

        Unit* caster = GetCaster();
        if (!caster)
            return;

        if (Aura* aura = caster->GetAura(SPELL_PRIEST_SURGE_OF_LIGHT_BUFF))
            aura->ModStackAmount(-1);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_pri_surge_of_light_consume::RecordBuff);
        AfterCast += SpellCastFn(spell_pri_surge_of_light_consume::ConsumeBuff);
    }
};

// Echo of Light (8,3) - heal half, bound to Holy Word: Serenity (200197) and Holy Word: Sanctify
// (200198) via scripted_by (WP-A). OnHit, not AfterHit: Spell::DoAllEffectOnTarget overwrites
// m_healing with the post-overheal *gain* once the heal lands (`m_healing = gain`), so by AfterHit
// GetHitHeal() is 0 on a full-health target and the Echo never applied (playtest 2026-09-22). At
// OnHit m_healing is still the pre-overheal amount, but also pre-crit - the crit bonus is applied
// right after the hook - so it's re-derived here the same way DoAllEffectOnTarget does it, to honour
// the design doc's "crit is already baked into the raw amount".
class spell_pri_echo_of_light_heal : public SpellScript
{
    PrepareSpellScript(spell_pri_echo_of_light_heal);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Priest::SPELL_ECHO_OF_LIGHT_HEAL });
    }

    bool DidHitCrit(Unit const* target)
    {
        for (TargetInfo const& info : *GetSpell()->GetUniqueTargetInfo())
            if (info.targetGUID == target->GetGUID())
                return info.crit;
        return false;
    }

    void ApplyEcho()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        int32 rawHeal = GetHitHeal();
        if (rawHeal > 0 && DidHitCrit(target))
            rawHeal = int32(Unit::SpellCriticalHealingBonus(caster, GetSpellInfo(), uint32(rawHeal), nullptr));

        ApplyEchoOfLight(caster, target, rawHeal, Priest::SPELL_ECHO_OF_LIGHT_HEAL, true);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pri_echo_of_light_heal::ApplyEcho);
    }
};

// Echo of Light (8,3) - damage half, bound to Holy Word: Chastise (200223) via scripted_by (WP-A).
class spell_pri_echo_of_light_damage : public SpellScript
{
    PrepareSpellScript(spell_pri_echo_of_light_damage);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ Priest::SPELL_ECHO_OF_LIGHT_DAMAGE });
    }

    void ApplyEcho()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        ApplyEchoOfLight(caster, target, GetHitDamage(), Priest::SPELL_ECHO_OF_LIGHT_DAMAGE, false);
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_pri_echo_of_light_damage::ApplyEcho);
    }
};

/*
 * Holy Concentration (6,0) - registered on Greater Heal/Flash Heal/Binding Heal/Circle of Healing.
 * The Spirit buff half (eff1 PROC_TRIGGER_SPELL -> 200199/200200/200201) is fully data-driven
 * (procs_on, WP-A) and needs no script; this class only owns the Renew-extension roll ("33/66/100%
 * chance ... extend your Renew on all nearby party and raid members by 3 sec").
 */
class spell_pri_holy_concentration_extend : public SpellScript
{
    PrepareSpellScript(spell_pri_holy_concentration_extend);

    void ExtendNearbyRenews()
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        AuraEffect const* marker = caster->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_HOLY_CONCENTRATION,
            EFFECT_1);
        if (!marker)
            return;

        float chance = float(marker->GetAmount());
        if (Player* player = caster->ToPlayer())
            chance *= 1.0f + player->GetProcChancePercentage() / 100.0f;

        if (!roll_chance_f(chance))
            return;

        std::list<Unit*> nearby;
        Acore::AnyGroupedUnitInObjectRangeCheck check(caster, caster, 40.0f, true);
        Acore::UnitListSearcher<Acore::AnyGroupedUnitInObjectRangeCheck> searcher(caster, nearby, check);
        Cell::VisitObjects(caster, searcher, 40.0f);

        for (Unit* unit : nearby)
            Priest::ExtendRenewDuration(unit->GetAura(SPELL_PRIEST_RENEW, caster->GetGUID()), 3000);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_pri_holy_concentration_extend::ExtendNearbyRenews);
    }
};

/*
 * Blessed Warding (6,2) - all 3 ranks bound to this one class via scripted_by (WP-A). procs_on
 * supplies PROC_FLAG_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG|PROC_FLAG_TAKEN_PERIODIC at chance=100; this
 * script rejects a direct single-target hit that slipped through those flags (design doc 5.7:
 * "Direct single-target melee and spell damage must not trigger it") and reads its own eff2/
 * EFFECT_1 DUMMY amount directly (no marker/icon read needed - CheckProc/HandleProc always run in
 * the context of whichever rank's own aura instance fired).
 */
class spell_pri_blessed_warding : public AuraScript
{
    PrepareAuraScript(spell_pri_blessed_warding);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_BLESSED_WARDING_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (!procSpell)
            return false;

        bool periodic = (eventInfo.GetTypeMask() & PROC_FLAG_TAKEN_PERIODIC) != 0;
        return periodic || procSpell->IsAffectingArea();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        PreventDefaultAction();

        Unit* target = GetTarget();
        AuraEffect const* markerEff = aurEff->GetBase()->GetEffect(EFFECT_1);
        if (!target || !markerEff)
            return;

        int32 marker = markerEff->GetAmount();
        if (marker <= 0)
            return;

        target->CastCustomSpell(SPELL_PRIEST_BLESSED_WARDING_BUFF, SPELLVALUE_BASE_POINT0, marker, target, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_blessed_warding::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pri_blessed_warding::HandleProc, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN);
    }
};

// Holy Word: Sanctify (5,3) target-count falloff - design doc sec 2: "Full value at 5 targets or
// fewer. Above 5, multiply each target's healing by sqrt(5/n)." Also bound to
// spell_pri_echo_of_light_heal on this same spell id (scripted_by, WP-A) - two independent scripts
// on one spell id is the normal multi-script pattern this codebase already uses elsewhere.
class spell_pri_holy_word_sanctify : public SpellScript
{
    PrepareSpellScript(spell_pri_holy_word_sanctify);

    uint32 _targetCount = 0;

    void CountTargets(std::list<WorldObject*>& targets)
    {
        _targetCount = uint32(targets.size());
    }

    void ApplyFalloff(SpellEffIndex /*effIndex*/)
    {
        if (_targetCount <= 5)
            return;

        int32 heal = GetHitHeal();
        heal = int32(float(heal) * std::sqrt(5.0f / float(_targetCount)));
        SetHitHeal(heal);
    }

    void Register() override
    {
        OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pri_holy_word_sanctify::CountTargets, EFFECT_0,
            TARGET_UNIT_DEST_AREA_ALLY);
        OnEffectHitTarget += SpellEffectFn(spell_pri_holy_word_sanctify::ApplyFalloff, EFFECT_0, SPELL_EFFECT_HEAL);
    }
};

/*
 * Serendipity (7,2) - all 3 ranks bound to this one class via scripted_by (WP-A). procs_on
 * deliberately carries no family restriction so a Paladin's Holy Light/Flash of Light can pass
 * (design doc: "Classless" per PLAN sec 1's generalized-stats precedent) - this script is the only
 * thing filtering *which* spells actually count, on both classes' identities directly.
 */
class spell_pri_serendipity : public AuraScript
{
    PrepareAuraScript(spell_pri_serendipity);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (!procSpell)
            return false;

        switch (procSpell->Id)
        {
            case SPELL_PRIEST_BINDING_HEAL:
            case SPELL_PRIEST_FLASH_HEAL:
            case SPELL_PRIEST_RENEW:
            case SPELL_PRIEST_SMITE:
            case SPELL_PALADIN_HOLY_LIGHT:
            case SPELL_PALADIN_FLASH_OF_LIGHT:
                return true;
            default:
                return false;
        }
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* caster = eventInfo.GetActor();
        if (!caster)
            return;

        uint32 buff;
        switch (GetId())
        {
            case SPELL_PRIEST_SERENDIPITY_R1: buff = SPELL_PRIEST_SERENDIPITY_BUFF_R1; break;
            case SPELL_PRIEST_SERENDIPITY_R2: buff = SPELL_PRIEST_SERENDIPITY_BUFF_R2; break;
            case SPELL_PRIEST_SERENDIPITY_R3: buff = SPELL_PRIEST_SERENDIPITY_BUFF_R3; break;
            default: return;
        }

        caster->CastSpell(caster, buff, true);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pri_serendipity::CheckProc);
        OnProc += AuraProcFn(spell_pri_serendipity::HandleProc);
    }
};

/*
 * Serendipity capstone - the Holy Word engine (7,2 / design doc 5.2). Registered on every spell in
 * the cadence table; fires on successful CAST (not on the heal/damage landing), so a fully-
 * overhealing Greater Heal still charges Serenity per the design doc's own callout. Free casts
 * granted by Divine Touch/Surge of Light still charge (they're real, non-triggered casts);
 * Answered Prayers' spread Renews don't, since those are cast with TRIGGERED_FULL_MASK.
 */
class spell_pri_holy_word_engine : public SpellScript
{
    PrepareSpellScript(spell_pri_holy_word_engine);

    void ReduceHolyWordCooldown()
    {
        if (GetSpell()->IsTriggered())
            return;

        Player* player = GetCaster() ? GetCaster()->ToPlayer() : nullptr;
        if (!player || !player->HasAura(SPELL_PRIEST_SERENDIPITY_R3))
            return;

        uint32 holyWord = 0;
        int32 ms = 0;
        switch (m_scriptSpellId)
        {
            case SPELL_PRIEST_GREATER_HEAL:
                holyWord = SPELL_PRIEST_HOLY_WORD_SERENITY;
                ms = 6000;
                break;
            case SPELL_PRIEST_FLASH_HEAL:
            case SPELL_PRIEST_BINDING_HEAL:
                holyWord = SPELL_PRIEST_HOLY_WORD_SERENITY;
                ms = 3000;
                break;
            case SPELL_PRIEST_PRAYER_OF_HEALING:
                holyWord = SPELL_PRIEST_HOLY_WORD_SANCTIFY;
                ms = 6000;
                break;
            case SPELL_PRIEST_CIRCLE_OF_HEALING:
            case SPELL_PRIEST_RENEW:
                holyWord = SPELL_PRIEST_HOLY_WORD_SANCTIFY;
                ms = 2000;
                break;
            case SPELL_PRIEST_SMITE:
            case SPELL_PRIEST_HOLY_FIRE:
                holyWord = SPELL_PRIEST_HOLY_WORD_CHASTISE;
                ms = 4000;
                break;
            default:
                return;
        }

        // "All values triple during Apotheosis" (design doc 5.2).
        if (player->HasAura(SPELL_PRIEST_APOTHEOSIS))
            ms *= 3;

        // Clear-then-set rather than Player::ModifySpellCooldown: the SMSG_MODIFY_COOLDOWN delta
        // that function sends has no client-side effect on this fork (see the comment above
        // Player::ApplyCooldownHasteCorrection in Player.cpp) - same fix as
        // spell_pri_improved_flash_heal_capstone in spell_priest_disc.cpp.
        uint32 remaining = player->GetSpellCooldownDelay(holyWord);
        if (!remaining)
            return;

        uint32 corrected = remaining > uint32(ms) ? remaining - uint32(ms) : 0;
        player->ApplyCooldownHasteCorrection(holyWord, 0, corrected);
    }

    void Register() override
    {
        AfterCast += SpellCastFn(spell_pri_holy_word_engine::ReduceHolyWordCooldown);
    }
};

/*
 * Holy Wrath (7,3) capstone - registered on rank 3 (200212) only. procs_on supplies the "direct
 * damaging critical" gate (PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG + hit_mask=CRITICAL); this
 * script implements the capstone's own two independent clauses. Clause 1's "once per second" is a
 * plain elapsed-time gate (SpellScript/AuraScript has no crit accessor in this codebase - the proc
 * system's own hit_mask=CRITICAL gate is the only clean crit signal, hence no extra check here).
 */
class spell_pri_holy_wrath_capstone : public AuraScript
{
    PrepareAuraScript(spell_pri_holy_wrath_capstone);

    uint32 _lastStackMs = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_PRIEST_HOLY_WRATH_CRIT_BUFF, SPELL_PRIEST_HOLY_WRATH_MAGIC_DMG_BUFF });
    }

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* caster = GetTarget();
        if (!caster)
            return;

        uint32 now = getMSTime();
        if (_lastStackMs == 0 || GetMSTimeDiffToNow(_lastStackMs) >= 1000)
        {
            caster->CastSpell(caster, SPELL_PRIEST_HOLY_WRATH_CRIT_BUFF, true);
            _lastStackMs = now;
        }

        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        if (procSpell && (procSpell->GetSchoolMask() & SPELL_SCHOOL_MASK_HOLY))
        {
            float chance = 10.0f;
            if (Player* player = caster->ToPlayer())
                chance *= 1.0f + player->GetProcChancePercentage() / 100.0f;

            if (roll_chance_f(chance))
                caster->CastSpell(caster, SPELL_PRIEST_HOLY_WRATH_MAGIC_DMG_BUFF, true);
        }
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_pri_holy_wrath_capstone::HandleProc);
    }
};

// Empowered Renew (8,0) capstone - registered on rank 3 (63543) only. procs_on supplies "Renew
// periodic critical tick" (PROC_FLAG_DONE_PERIODIC + hit_mask=CRITICAL, family Renew); this script
// just draws on the shared extension pool (Priest::ExtendRenewDuration, PriestMechanics.cpp).
class spell_pri_empowered_renew_capstone : public AuraScript
{
    PrepareAuraScript(spell_pri_empowered_renew_capstone);

    void HandleProc(ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* caster = GetTarget();
        Unit* target = eventInfo.GetProcTarget();
        if (!caster || !target)
            return;

        Priest::ExtendRenewDuration(target->GetAura(SPELL_PRIEST_RENEW, caster->GetGUID()), 1000);
    }

    void Register() override
    {
        OnProc += AuraProcFn(spell_pri_empowered_renew_capstone::HandleProc);
    }
};

void AddSC_priest_holy_spell_scripts()
{
    RegisterSpellScript(spell_pri_healing_focus_capstone);
    RegisterSpellScript(spell_pri_renew_cast);
    RegisterSpellScript(spell_pri_holy_reach_capstone);
    RegisterSpellScript(spell_pri_kindled_faith);
    RegisterSpellScript(spell_pri_spirit_of_redemption);
    RegisterSpellScript(spell_pri_surge_of_light_consume);
    RegisterSpellScript(spell_pri_echo_of_light_heal);
    RegisterSpellScript(spell_pri_echo_of_light_damage);
    RegisterSpellScript(spell_pri_holy_concentration_extend);
    RegisterSpellScript(spell_pri_blessed_warding);
    RegisterSpellScript(spell_pri_holy_word_sanctify);
    RegisterSpellScript(spell_pri_serendipity);
    RegisterSpellScript(spell_pri_holy_word_engine);
    RegisterSpellScript(spell_pri_holy_wrath_capstone);
    RegisterSpellScript(spell_pri_empowered_renew_capstone);
}
