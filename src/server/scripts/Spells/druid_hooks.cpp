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
 * Druid rework - every ScriptMgr hook (as opposed to a SpellScript/AuraScript bound to one spell
 * id) the three passes need, in one file (.agents/plans/druid-rework/druid-rework.CORE-AUDIT.md's
 * top summary): UnitScript (ModifySpellDamageTaken, ModifyMeleeDamage,
 * ModifyPeriodicDamageAurasTick, OnAuraApply, OnAuraRemove), GlobalScript
 * (OnSpellHealingBonusTakenNegativeModifiers), AllSpellScript (CanPrepare, OnSpellPrepare),
 * PlayerScript (OnPlayerAfterUpdateMaxHealth). These run on every damage/heal event for every
 * class server-wide - every handler here MUST check for a druid caster/target first before doing
 * anything (CORE-AUDIT's own warning, repeated in PLAN §11 "Risks").
 *
 * Created empty by the Balance pass's WP-0 (PLAN §5.1); WP-B adds Balance's own row (CORE-AUDIT
 * row 9, B6's Moonkin heal-cancel AllSpellScript::OnSpellPrepare, only if the in-game check says
 * the client doesn't already auto-unshift - PLAN §6 item 8). Resto (rows 11-21) and Feral (rows
 * 22-35) extend this same file with their own handlers in their own passes.
 */

#include "DruidMechanics.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraDefines.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "Unit.h"
#include "UnitDefines.h"
#include "Util.h"

/*
 * B6 - "Casting any healing spell cancels Moonkin Form" (PLAN §1B row B6, CORE-AUDIT row 9,
 * BALANCE.md §0.5/§11.5). The user's own rule for this row is to verify in game whether the
 * 3.3.5a client already auto-unshifts Moonkin Form on a blocked heal cast before building a
 * server-side fallback; this pass has no build/deploy/playtest access, so that in-game check
 * could not be performed. Built anyway per the WP-B brief's explicit instruction (the "likely
 * yes" default from PLAN's own B6 row is stated there as not being sufficient on its own) -
 * CORE-AUDIT row 9 recommends shipping this AllSpellScript::OnSpellPrepare fallback regardless,
 * and it can be ripped out later by whoever runs that check if the client turns out to already
 * handle it. Report this explicitly to WP-C/the user so that decision gets made.
 *
 * CORE-AUDIT row 9's own evidence: for an instant-cast heal, OnSpellPrepare fires *after*
 * Spell::prepare() has already called cast(true) (Spell.cpp:3809-3816), so removing Moonkin Form
 * here cannot stop that particular cast's heal from landing while still shapeshifted - the heal
 * itself has already resolved. What this still buys: the form drops immediately afterwards (so a
 * follow-up heal, or anything else gated on "not in Moonkin", works correctly), and for any heal
 * with a real cast time the form drops before the cast bar completes. WP-A's own job (not this
 * file's) is dropping/adjusting the Moonkin StancesNot bit on the druid heal spells themselves
 * (PLAN §11.5) so they're castable at all while shapeshifted for this hook to have anything to
 * remove.
 */
class DruidMoonkinHealCancel : public AllSpellScript
{
public:
    DruidMoonkinHealCancel() : AllSpellScript("DruidMoonkinHealCancel", { ALLSPELLHOOK_ON_PREPARE }) { }

    void OnSpellPrepare(Spell* spell, Unit* caster, SpellInfo const* spellInfo) override
    {
        if (!caster || !spellInfo || !spell)
            return;

        // Every druid/heal event server-wide reaches this hook (CORE-AUDIT's own warning,
        // PLAN §11 "Risks") - gate on a druid player in Moonkin Form before doing anything else.
        Player* player = caster->ToPlayer();
        if (!player || player->getClass() != CLASS_DRUID)
            return;

        if (player->GetShapeshiftForm() != FORM_MOONKIN)
            return;

        // "Non-triggered heal": a real player cast (not a proc/DoT-tick trigger) of a druid spell
        // that either heals directly (Healing Touch, Regrowth's direct part, Swiftmend, ...) or
        // applies a periodic heal (Rejuvenation, Lifebloom, Wild Growth, Tranquility, ...).
        if (spell->IsTriggered())
            return;

        if (spellInfo->SpellFamilyName != SPELLFAMILY_DRUID)
            return;

        if (!spellInfo->HasEffect(SPELL_EFFECT_HEAL) && !spellInfo->HasAura(SPELL_AURA_PERIODIC_HEAL))
            return;

        player->RemoveAurasByType(SPELL_AURA_MOD_SHAPESHIFT);
    }
};

/*
 * Resto pass additions (druid-rework.CORE-AUDIT.md rows 12, 16, 21). Every handler below checks
 * for a druid caster/target before doing anything - these hooks fire on every damage/heal event
 * server-wide.
 */

// CORE-AUDIT rows 12/16/21: Harmony/Nature's Mending on HoT ticks, Natural Shapeshifter's per-form
// bonuses, and Flourish's tick acceleration extending to HoTs applied during its window.
class DruidRestoUnitHooks : public UnitScript
{
public:
    DruidRestoUnitHooks()
        : UnitScript("DruidRestoUnitHooks", true,
                      { UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK, UNITHOOK_ON_AURA_APPLY, UNITHOOK_ON_AURA_REMOVE })
    {
    }

    // Row 12: Harmony + Nature's Mending on core HoT ticks. Real signature/order (target, attacker)
    // despite the "damage" name - this is the same hook used for heal ticks (SpellAuraEffects.cpp:6699,
    // after crit and the final-tick-bonus multiplier, before absorb/DealHeal).
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage,
                                        SpellInfo const* spellInfo) override
    {
        if (!attacker || !target || !spellInfo)
            return;

        Player const* player = attacker->ToPlayer();
        if (!player || player->getClass() != CLASS_DRUID)
            return;

        Druid::ApplyPeriodicHealTickMods(attacker, target, spellInfo, damage);
    }

    // Row 16: Natural Shapeshifter's per-form healing/damage/crit bonuses - fires after
    // HandleShapeshiftBoosts/InitDataForForm have already run for this aura's apply.
    // Row 21 (RESTO §0.13 Q16): a HoT applied by a caster with the Flourish buff up gets the same
    // injected ticks, for the buff's remaining time.
    void OnAuraApply(Unit* unit, Aura* aura) override
    {
        if (!unit || !aura)
            return;

        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (!spellInfo)
            return;

        if (spellInfo->HasAura(SPELL_AURA_MOD_SHAPESHIFT))
        {
            if (Player* player = unit->ToPlayer())
                if (player->getClass() == CLASS_DRUID)
                    Druid::ApplyShapeshiftFormBonuses(player, player->GetShapeshiftForm());
        }

        if (!spellInfo->HasAura(SPELL_AURA_PERIODIC_HEAL))
            return;

        // Druid::OnCoreHotApplied owns both the Flourish acceleration and the Omen of Clarity r3
        // capstone's one-time HoT boost, and de-dupes internally - OnAuraApply also fires on a
        // refresh/stack of an existing aura, not just a genuinely new application (code-review fix).
        Druid::OnCoreHotApplied(unit, aura);
    }

    // Row 16: re-evaluate Natural Shapeshifter's form bonuses for "the form being shifted TO" - by
    // this point HandleShapeshiftBoosts/InitDataForForm have already updated the target's current
    // shapeshift form (whether that's another form or back to FORM_NONE), so reading it directly is
    // equivalent to knowing the incoming aura's form without needing to inspect it separately.
    void OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode /*mode*/) override
    {
        if (!unit || !aurApp || !aurApp->GetBase() || !aurApp->GetBase()->GetSpellInfo())
            return;

        SpellInfo const* spellInfo = aurApp->GetBase()->GetSpellInfo();

        if (spellInfo->HasAura(SPELL_AURA_PERIODIC_HEAL))
            Druid::ClearCoreHotApplication(unit, aurApp->GetBase());

        if (!spellInfo->HasAura(SPELL_AURA_MOD_SHAPESHIFT))
            return;

        Player* player = unit->ToPlayer();
        if (!player || player->getClass() != CLASS_DRUID)
            return;

        Druid::ApplyShapeshiftFormBonuses(player, player->GetShapeshiftForm());
    }
};

// CORE-AUDIT row 15: Deep Roots r3 capstone - Regrowth costs 25% less when cast on a target already
// affected by the caster's Regrowth. Toggles a hidden 1-charge SpellMod aura (200602, WP-A's data:
// ADD_FLAT_MODIFIER COST scoped to Regrowth) right before the cost is computed
// (Spell.cpp: CanPrepare at 3578, CalcPowerCost at 3637).
class DruidDeepRootsCapstone : public AllSpellScript
{
public:
    DruidDeepRootsCapstone() : AllSpellScript("DruidDeepRootsCapstone", { ALLSPELLHOOK_CAN_PREPARE }) { }

    bool CanPrepare(Spell* spell, SpellCastTargets const* /*targets*/, AuraEffect const* /*triggeredByAura*/) override
    {
        if (!spell || !spell->m_spellInfo || spell->m_spellInfo->Id != Druid::SPELL_REGROWTH)
            return true;

        Unit* casterUnit = spell->GetCaster() ? spell->GetCaster()->ToUnit() : nullptr;
        Player* player = casterUnit ? casterUnit->ToPlayer() : nullptr;
        if (!player || player->getClass() != CLASS_DRUID)
            return true;

        // Code-review fix: the `targets` parameter is the raw pre-correction pointer
        // InitExplicitTargets was just called with (Spell.cpp: InitExplicitTargets(*targets) then
        // CanPrepare(this, targets, ...) right after, both against the same uncorrected object) - an
        // implicit self-cast (no unit target sent by the client) only gets its unit target filled in
        // on `spell->m_targets`, so `targets->GetUnitTarget()` is null for a self-cast Regrowth even
        // though the spell will resolve one.
        Unit* target = spell->m_targets.GetUnitTarget();
        bool const grant = target && player->HasAura(Druid::SPELL_DEEP_ROOTS_R3) &&
                            target->HasAura(Druid::SPELL_REGROWTH, player->GetGUID());

        if (grant)
        {
            // Code-review fix: CORE-AUDIT row 15 requires the flat reduction to be exactly 25% of
            // Regrowth's own *base* mana cost, computed fresh per cast, so it stays a correct ×0.75
            // at any level - a static DBC constant calibrated to one level (the previous -254,
            // level-80-only value) over- or under-reduces at every other level. ManaCostPercentage
            // mirrors SpellInfo::CalcPowerCost's own pre-SpellMod baseline (SpellInfo.cpp:~2873).
            int32 const rawCost = int32(CalculatePct(player->GetCreateMana(), spell->m_spellInfo->ManaCostPercentage));
            int32 const reduction = int32(CalculatePct(rawCost, 25));
            // Live value: SetSpellValue's CalcBaseValue already takes the die_sides=1 point off.
            int32 const basePoints = -reduction;
            player->CastCustomSpell(player, Druid::SPELL_DEEP_ROOTS_COST_REDUCTION, &basePoints, nullptr, nullptr,
                                     true);
        }
        else
            player->RemoveAurasDueToSpell(Druid::SPELL_DEEP_ROOTS_COST_REDUCTION);

        return true;
    }
};

/*
 * Feral pass additions (druid-rework.CORE-AUDIT.md rows 22, 24, 26, 27, 29, 32). The math lives in
 * DruidMechanics.cpp; these handlers only route. Every handler bails first unless a druid player is
 * involved - these hooks fire on every damage/heal event server-wide.
 */

namespace
{
    // Cat Form white-hit damage multiplier, in percent (user ruling 2026-10-08, DPS balance pass: auto-attacks -50%).
    constexpr float CAT_FORM_AUTOATTACK_DAMAGE_PCT = 50.0f;

    Player* GetDruidPlayer(Unit* unit)
    {
        Player* player = unit ? unit->ToPlayer() : nullptr;
        return player && player->getClass() == CLASS_DRUID ? player : nullptr;
    }

    // CORE-AUDIT row 22's gate: a weapon-damage ability with no SCHOOL_DAMAGE effect. A spell with a
    // SCHOOL_DAMAGE effect already got the Feral clauses from Druid::ApplyDoneDamagePctMods (row 1).
    bool IsWeaponDamageOnlySpell(SpellInfo const* spellInfo)
    {
        if (spellInfo->HasEffect(SPELL_EFFECT_SCHOOL_DAMAGE))
            return false;

        return spellInfo->HasEffect(SPELL_EFFECT_WEAPON_DAMAGE) ||
               spellInfo->HasEffect(SPELL_EFFECT_WEAPON_DAMAGE_NOSCHOOL) ||
               spellInfo->HasEffect(SPELL_EFFECT_NORMALIZED_WEAPON_DMG) ||
               spellInfo->HasEffect(SPELL_EFFECT_WEAPON_PERCENT_DAMAGE);
    }

    // ModifyPeriodicDamageAurasTick also fires for heal ticks (SPELL_AURA_PERIODIC_HEAL /
    // OBS_MOD_HEALTH). A spell carrying both kinds counts as a heal, so a heal tick is never reduced.
    bool IsPeriodicDamageSpell(SpellInfo const* spellInfo)
    {
        if (spellInfo->HasAura(SPELL_AURA_PERIODIC_HEAL) || spellInfo->HasAura(SPELL_AURA_OBS_MOD_HEALTH))
            return false;

        return spellInfo->HasAura(SPELL_AURA_PERIODIC_DAMAGE) ||
               spellInfo->HasAura(SPELL_AURA_PERIODIC_DAMAGE_PERCENT) ||
               spellInfo->HasAura(SPELL_AURA_PERIODIC_LEECH);
    }
}

// CORE-AUDIT rows 22, 27 and 32: Feral's done-% clauses on weapon abilities and autoattacks
// (attacker side), Iron Hide's magic damage reduction (victim side) and the form boosts on every
// shapeshift. Its own class rather than DruidRestoUnitHooks: Iron Hide is victim-side, and the Resto
// tick handler bails on non-druid attackers.
class DruidFeralUnitHooks : public UnitScript
{
public:
    DruidFeralUnitHooks()
        : UnitScript("DruidFeralUnitHooks", true,
                      { UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN, UNITHOOK_MODIFY_MELEE_DAMAGE,
                        UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK, UNITHOOK_ON_AURA_APPLY, UNITHOOK_ON_AURA_REMOVE })
    {
    }

    // Unit::CalculateSpellDamageTaken, before armor and crit, for every spell hit.
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (!target || !spellInfo || damage <= 0)
            return;

        float mult = 1.0f;

        // Row 22: weapon-damage abilities. The hook has to honour IGNORE_CASTER_MODIFIERS itself
        // (Unit::MeleeDamageBonusDone does for its own mods).
        if (Player* player = GetDruidPlayer(attacker))
        {
            if (IsWeaponDamageOnlySpell(spellInfo) && !spellInfo->HasAttribute(SPELL_ATTR3_IGNORE_CASTER_MODIFIERS))
            {
                mult *= Druid::GetFeralDamageDoneMultiplier(player, target, spellInfo, spellInfo->GetSchoolMask());

                // Omen of Clarity r3 capstone, melee side (the spell side is in ApplyDoneDamagePctMods):
                // +10% on the ability that consumed the empowered Clearcasting.
                if (Spell const* spell = player->m_spellModTakingSpell)
                    if (spell->GetSpellInfo() == spellInfo && Druid::ConsumedEmpoweredClearcasting(player))
                        if (AuraEffect const* capstone =
                                player->GetAuraEffect(Druid::SPELL_CLEARCASTING_OMEN_CAPSTONE, EFFECT_1))
                            AddPct(mult, capstone->GetAmount());
            }
        }

        // Row 27: Iron Hide.
        if (GetDruidPlayer(target))
            mult *= Druid::GetIronHideDamageTakenMultiplier(target, spellInfo->GetSchoolMask());

        if (mult != 1.0f)
            damage = int32(float(damage) * mult);
    }

    // Unit::CalculateMeleeDamage (autoattacks), before armor. The hook passes neither the attack type
    // nor the damage index, so the school is the attacker's main-hand school.
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        if (!target || !attacker || !damage)
            return;

        float mult = 1.0f;

        if (Player* player = GetDruidPlayer(attacker))
            mult *= Druid::GetFeralDamageDoneMultiplier(player, target, nullptr, attacker->GetMeleeDamageSchoolMask());

        if (Player* player = GetDruidPlayer(attacker))
            if (player->GetShapeshiftForm() == FORM_CAT)
                mult *= CAT_FORM_AUTOATTACK_DAMAGE_PCT / 100.0f;

        if (GetDruidPlayer(target))
            mult *= Druid::GetIronHideDamageTakenMultiplier(target, attacker->GetMeleeDamageSchoolMask());

        if (mult != 1.0f)
            damage = uint32(float(damage) * mult);
    }

    // Row 27: Iron Hide on damage and leech ticks (the same hook fires for heal ticks - skipped).
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* /*attacker*/, uint32& damage,
                                        SpellInfo const* spellInfo) override
    {
        if (!damage || !spellInfo || !GetDruidPlayer(target) || !IsPeriodicDamageSpell(spellInfo))
            return;

        float const mult = Druid::GetIronHideDamageTakenMultiplier(target, spellInfo->GetSchoolMask());
        if (mult != 1.0f)
            damage = uint32(float(damage) * mult);
    }

    // Rows 29 and 32: the new form is set and its boosts/InitDataForForm have run by now.
    void OnAuraApply(Unit* unit, Aura* aura) override
    {
        Player* player = GetDruidPlayer(unit);
        if (!player || !aura || !aura->GetSpellInfo()->HasAura(SPELL_AURA_MOD_SHAPESHIFT))
            return;

        Druid::OnFeralFormChanged(player, true);
    }

    void OnAuraRemove(Unit* unit, AuraApplication* aurApp, AuraRemoveMode /*mode*/) override
    {
        Player* player = GetDruidPlayer(unit);
        if (!player || !aurApp || !aurApp->GetBase()->GetSpellInfo()->HasAura(SPELL_AURA_MOD_SHAPESHIFT))
            return;

        // Shifting straight into another form: the old form is removed from inside the new form's
        // apply handler, whose aura is already registered - its OnAuraApply above does the work once
        // the new form is set (the form field still holds the old form here).
        if (player->HasShapeshiftAura())
            return;

        // Back to caster form (or death/logout). The core has already dropped the Stances-bound
        // boosts, and this runs inside its aura-removal loop, so no aura is removed or cast here.
        Druid::OnFeralFormChanged(player, false);
    }
};

// CORE-AUDIT row 26: healing another player casts on a Feral druid - Heart of the Wild Mastery, Elder
// Hide x Ironfur, Nurturing Instinct (x3 under Survival Instincts). Runs before the DmgClass-NONE early
// return in Unit::SpellHealingBonusTaken, so it covers direct heals, HoT ticks and Lifebloom's bloom.
// The hook replaces the stock "worst MOD_HEALING_PCT" value, so this recomputes it and folds the bonus
// in multiplicatively (PLAN A2); the first handler that returns true wins.
class DruidFeralExternalHealing : public GlobalScript
{
public:
    DruidFeralExternalHealing()
        : GlobalScript("DruidFeralExternalHealing", { GLOBALHOOK_ON_SPELL_HEALING_BONUS_TAKEN_NEGATIVE_MODIFIERS })
    {
    }

    bool OnSpellHealingBonusTakenNegativeModifiers(Unit const* target, Unit const* caster,
                                                   SpellInfo const* /*spellInfo*/, float& val) override
    {
        if (!target || !caster)
            return false;

        Player const* player = target->ToPlayer();
        if (!player || player->getClass() != CLASS_DRUID)
            return false;

        // "Cast on you by another player" (FERAL §0.16): a pet or guardian counts as its owner;
        // self-heals, potions and NPC heals don't qualify.
        Player const* healer = caster->GetCharmerOrOwnerPlayerOrPlayerItself();
        if (!healer || healer == player)
            return false;

        float const factor = Druid::GetExternalHealingReceivedMultiplier(player);
        if (factor == 1.0f)
            return false;

        float const maxNegative = float(target->GetMaxNegativeAuraModifier(SPELL_AURA_MOD_HEALING_PCT));
        val = ((1.0f + maxNegative / 100.0f) * factor - 1.0f) * 100.0f;
        return true;
    }
};

// CORE-AUDIT row 29 (PLAN C4): Heart of the Wild r3's Mastery raises maximum health in either bear
// form. spell_dru_heart_of_the_wild_mastery's 5 s check and the shapeshift handler above call
// UpdateMaxHealth when the Mastery or the form changes.
class DruidHeartOfTheWildMaxHealth : public PlayerScript
{
public:
    DruidHeartOfTheWildMaxHealth()
        : PlayerScript("DruidHeartOfTheWildMaxHealth", { PLAYERHOOK_ON_AFTER_UPDATE_MAX_HEALTH })
    {
    }

    void OnPlayerAfterUpdateMaxHealth(Player* player, float& value) override
    {
        if (!player || player->getClass() != CLASS_DRUID || !Druid::IsInBearForm(player))
            return;

        if (float const pct = Druid::GetHeartOfTheWildMasteryPct(player))
            AddPct(value, pct);
    }
};

// CORE-AUDIT row 24 (PLAN C5): Rend and Tear's Ferocious Bite crit counts only the caster's own Rip or
// Lacerate. Adds the hidden 1-charge crit aura 200436 (ADD_FLAT_MODIFIER CRITICAL_CHANCE on the
// Rip/Ferocious Bite bit) right before a qualifying Ferocious Bite is cast; any other Ferocious Bite
// or Rip prepare removes a leftover one (Rip shares that bit, and would take the crit on its DoT).
class DruidRendAndTearCrit : public AllSpellScript
{
public:
    DruidRendAndTearCrit() : AllSpellScript("DruidRendAndTearCrit", { ALLSPELLHOOK_CAN_PREPARE }) { }

    bool CanPrepare(Spell* spell, SpellCastTargets const* /*targets*/, AuraEffect const* /*triggeredByAura*/) override
    {
        if (!spell || !spell->m_spellInfo)
            return true;

        uint32 const spellId = spell->m_spellInfo->Id;
        if (spellId != Druid::SPELL_FEROCIOUS_BITE && spellId != Druid::SPELL_RIP)
            return true;

        Player* player = GetDruidPlayer(spell->GetCaster() ? spell->GetCaster()->ToUnit() : nullptr);
        if (!player)
            return true;

        // spell->m_targets, not `targets` - see DruidDeepRootsCapstone.
        int32 critBonus = 0;
        if (spellId == Druid::SPELL_FEROCIOUS_BITE)
            if (Unit* target = spell->m_targets.GetUnitTarget())
                if (target->HasAura(Druid::SPELL_RIP, player->GetGUID()) ||
                    target->HasAura(Druid::SPELL_LACERATE, player->GetGUID()))
                    critBonus = Druid::GetRankAmount(player,
                        { Druid::SPELL_REND_AND_TEAR_R3, Druid::SPELL_REND_AND_TEAR_R2, Druid::SPELL_REND_AND_TEAR_R1 },
                        EFFECT_1);

        if (critBonus > 0)
            player->CastCustomSpell(Druid::SPELL_REND_AND_TEAR_CRIT, SPELLVALUE_BASE_POINT0, critBonus, player, true);
        else
            player->RemoveAurasDueToSpell(Druid::SPELL_REND_AND_TEAR_CRIT);

        return true;
    }
};

void AddSC_druid_hooks()
{
    new DruidMoonkinHealCancel();
    new DruidRestoUnitHooks();
    new DruidDeepRootsCapstone();
    new DruidFeralUnitHooks();
    new DruidFeralExternalHealing();
    new DruidHeartOfTheWildMaxHealth();
    new DruidRendAndTearCrit();
}
