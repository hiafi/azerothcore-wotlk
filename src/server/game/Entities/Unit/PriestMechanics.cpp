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

#include "PriestMechanics.h"
#include "Player.h"
#include "SpellAuraEffects.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "Util.h"

namespace
{
    // void_eruption_buff_200140's own SpellIconID (apps/dbc-tools/source/classes/priest/
    // priest_trigger_spells.py, mined into SpellIcon.dbc by apps/dbc-tools/build_patch_i.py's
    // ICON_ID_VOID_ERUPTION) - keep in sync if that spell's icon ever changes.
    constexpr uint32 PRIEST_ICON_VOIDFORM = 90104;

    enum PriestMechanicsSpells
    {
        // Baseline spells these hooks key on by id.
        SPELL_PRIEST_POWER_WORD_SHIELD          = 17,
        SPELL_PRIEST_PRAYER_OF_HEALING          = 596,
        SPELL_PRIEST_GREATER_HEAL               = 2060,
        SPELL_PRIEST_FLASH_HEAL                 = 2061,
        SPELL_PRIEST_WEAKENED_SOUL              = 6788,
        SPELL_PRIEST_BINDING_HEAL               = 32546,
        // 47757 is the outer Penance bolt spell cast by spell_pri_penance::HandleDummy - it only
        // applies a DUMMY + PERIODIC_TRIGGER_SPELL aura (no direct heal effect of its own). The
        // trigger fires 47750, which is the spell that actually carries EffectHeal and is what
        // Spell::DoAllEffectOnTarget's m_healing branch (where this check runs) ever sees.
        SPELL_PRIEST_PENANCE_HEAL_BOLT          = 47750,

        // Talent rank spell ids (never talent_dbc ids - see PLAN sec 3.10).
        SPELL_PRIEST_INNER_FOCUS                = 14751,    // (2,1), single rank
        SPELL_PRIEST_IMPROVED_PWS_R3            = 14769,    // (2,2) rank 3, Mastery capstone
        SPELL_PRIEST_FOCUSED_POWER_R2           = 33190,    // (5,0) rank 2, PoH crit capstone

        // Discipline rework spells (DISC.md "ID map").
        SPELL_PRIEST_GREATER_POWER_WORD_SHIELD  = 200155,
        SPELL_PRIEST_SPIRIT_SHELL               = 200166,
        SPELL_PRIEST_SPIRIT_SHELL_ABSORB        = 200167
    };

    // Renewed Hope (7,0) rides SPELL_AURA_OVERRIDE_CLASS_SCRIPTS with these two misc values; the
    // engine used to special-case them inline in Unit::SpellTakenCritChance's class-script loop.
    constexpr int32 PRIEST_CLASS_SCRIPT_RENEWED_HOPE_1 = 7997;
    constexpr int32 PRIEST_CLASS_SCRIPT_RENEWED_HOPE_2 = 7998;

    // Focused Power (5,0) capstone: "Your Prayer of Healing has a 25% increased critical strike
    // chance on targets affected by your Power Word: Shield, Greater Power Word: Shield, or
    // Weakened Soul" (docs/reworks/priest-disc-rework.md).
    constexpr float PRIEST_FOCUSED_POWER_POH_CRIT = 25.0f;

    // Spirit Shell (10,1): "absorption is capped at 60% of the target's maximum health, tracked
    // separately from Divine Aegis."
    constexpr int32 PRIEST_SPIRIT_SHELL_MAX_HEALTH_PCT = 60;

    bool IsSpiritShellConvertibleHeal(uint32 spellId)
    {
        // PLAN sec 1 (resolved design call): "Flash Heal, Greater Heal, Binding Heal, Prayer of
        // Healing, Penance heal bolts. Not Renew, PoM, CoH, Divine Hymn, Halo, Divine Star, Holy
        // Nova, Holy Words, Desperate Prayer."
        switch (spellId)
        {
            case SPELL_PRIEST_FLASH_HEAL:
            case SPELL_PRIEST_GREATER_HEAL:
            case SPELL_PRIEST_BINDING_HEAL:
            case SPELL_PRIEST_PRAYER_OF_HEALING:
            case SPELL_PRIEST_PENANCE_HEAL_BOLT:
                return true;
            default:
                return false;
        }
    }
}

namespace Priest
{
    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, DamageEffectType damagetype, float& doneTotalMod)
    {
        // Cross-class clauses (a later pass's Divine Fury, which buffs direct Holy-school damage
        // from *any* class - PLAN sec 1) belong above this gate. Everything below it is
        // priest-family-only and used to live in Unit::SpellPctDamageModsDone's own
        // `case SPELLFAMILY_PRIEST:`.
        if (spellProto->SpellFamilyName != SPELLFAMILY_PRIEST)
            return;

        // Voidform (docs/reworks/priest-new-spells.md, Void Eruption): "increases your periodic
        // Shadow damage by 10%." damagetype distinguishes a DoT tick from direct damage - the only
        // caster-side signal that lets this scope to "periodic" without a dedicated AuraType.
        if (damagetype == DOT && (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_SHADOW))
            if (AuraEffect const* voidform = caster->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_VOIDFORM, EFFECT_0))
                AddPct(doneTotalMod, voidform->GetAmount());

        // Mind Flay
        if (spellProto->SpellFamilyFlags[0] & 0x800000)
        {
            // Glyph of Shadow Word: Pain
            if (AuraEffect* aurEff = caster->GetAuraEffect(55687, 0))
                // Increase Mind Flay damage if Shadow Word: Pain present on target
                if (victim->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, 0x8000, 0, 0, caster->GetGUID()))
                    AddPct(doneTotalMod, aurEff->GetAmount());

            // Twisted Faith - Mind Flay part
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_OVERRIDE_CLASS_SCRIPTS, SPELLFAMILY_PRIEST, 2848, 1))
                // Increase Mind Flay damage if Shadow Word: Pain present on target
                if (victim->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, 0x8000, 0, 0, caster->GetGUID()))
                    AddPct(doneTotalMod, aurEff->GetAmount());
        }
        // Smite
        else if (spellProto->SpellFamilyFlags[0] & 0x80)
        {
            // Glyph of Smite
            if (AuraEffect* aurEff = caster->GetAuraEffect(55692, 0))
                if (victim->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, 0x100000, 0, 0, caster->GetGUID()))
                    AddPct(doneTotalMod, aurEff->GetAmount());
        }
        // Shadow Word: Death
        else if (spellProto->SpellFamilyFlags[1] & 0x2)
        {
            // Glyph of Shadow Word: Death
            if (AuraEffect* aurEff = caster->GetAuraEffect(55682, 1))
                if (victim->HasAuraState(AURA_STATE_HEALTHLESS_35_PERCENT))
                    AddPct(doneTotalMod, aurEff->GetAmount());
        }
    }

    void ApplySpellCritChanceMods(Unit const* caster, SpellInfo const* spellProto, float& critChance)
    {
        // Inner Focus (2,1): "Flash Heal: increases critical strike chance to 100%"
        // (docs/reworks/priest-disc-rework.md). *To*, not *by* - an absolute override, and the
        // charge itself is consumed by the normal SpellMod path on the same cast.
        if (spellProto->Id == SPELL_PRIEST_FLASH_HEAL && caster->HasAura(SPELL_PRIEST_INNER_FOCUS))
            critChance = 100.0f;
    }

    void ApplySpellTakenCritChanceMods(Unit const* victim, Unit const* caster, SpellInfo const* spellProto, float& critChance)
    {
        if (!caster || !victim)
            return;

        // Renewed Hope (7,0): "+2/4% critical effect chance ... on targets afflicted by Weakened
        // Soul." Migrated verbatim out of Unit::SpellTakenCritChance's OVERRIDE_CLASS_SCRIPTS loop
        // (`case 7997: case 7998:`), including that loop's own IsAffectedOnSpell() scoping, which
        // is what restricts the bonus to Flash Heal / Greater Heal / Penance's heal bolt.
        Unit::AuraEffectList const& classScripts = caster->GetAuraEffectsByType(SPELL_AURA_OVERRIDE_CLASS_SCRIPTS);
        for (AuraEffect const* classScript : classScripts)
        {
            if (classScript->GetMiscValue() != PRIEST_CLASS_SCRIPT_RENEWED_HOPE_1 && classScript->GetMiscValue() != PRIEST_CLASS_SCRIPT_RENEWED_HOPE_2)
                continue;

            if (!classScript->IsAffectedOnSpell(spellProto))
                continue;

            if (victim->HasAura(SPELL_PRIEST_WEAKENED_SOUL))
                critChance += classScript->GetAmount();
        }

        // Focused Power (5,0) capstone - rank 2 only, so the rank spell id is the marker and no
        // dummy-by-icon read is needed. Weakened Soul is listed on its own so the bonus survives a
        // shield that has already been consumed, and Greater Power Word: Shield is listed on its
        // own because its two extra shields deliberately apply no Weakened Soul.
        if (spellProto->Id == SPELL_PRIEST_PRAYER_OF_HEALING && caster->HasAura(SPELL_PRIEST_FOCUSED_POWER_R2))
            if (victim->HasAura(SPELL_PRIEST_POWER_WORD_SHIELD) || victim->HasAura(SPELL_PRIEST_GREATER_POWER_WORD_SHIELD) || victim->HasAura(SPELL_PRIEST_WEAKENED_SOUL))
                critChance += PRIEST_FOCUSED_POWER_POH_CRIT;
    }

    bool TryConvertHealToSpiritShell(Unit* caster, Unit* target, SpellInfo const* spellProto, uint32& heal)
    {
        if (!caster || !target || !heal)
            return false;

        if (!caster->HasAura(SPELL_PRIEST_SPIRIT_SHELL))
            return false;

        if (!IsSpiritShellConvertibleHeal(spellProto->Id))
            return false;

        int32 absorb = int32(heal);

        // "Spirit Shell absorption is increased by your Mastery, multiplicatively, after all other
        // modifiers. This scaling comes from the Improved Power Word: Shield capstone at (2,2) and
        // requires 3/3 in that talent." Mastery is a Player-only custom stat (PLAN sec 3.8).
        if (Player* player = caster->ToPlayer())
            if (player->HasAura(SPELL_PRIEST_IMPROVED_PWS_R3))
                AddPct(absorb, player->GetMasteryPercentage());

        // A second Spirit Shell heal adds to the first rather than replacing it, same shape as
        // Divine Aegis.
        if (AuraEffect const* existing = target->GetAuraEffect(SPELL_PRIEST_SPIRIT_SHELL_ABSORB, EFFECT_0, caster->GetGUID()))
            absorb += existing->GetAmount();

        absorb = std::min<int32>(absorb, int32(target->CountPctFromMaxHealth(PRIEST_SPIRIT_SHELL_MAX_HEALTH_PCT)));

        caster->CastCustomSpell(SPELL_PRIEST_SPIRIT_SHELL_ABSORB, SPELLVALUE_BASE_POINT0, absorb, target, true);

        // The heal still "lands" for 0 - that keeps the cast's own proc chain (Grace, Borrowed
        // Time, ...) intact while Divine Aegis, which reads the healed amount, finds nothing to
        // shield with (and carries its own Spirit Shell guard besides, so one cast can never
        // produce two Mastery-scaled absorbs).
        heal = 0;
        return true;
    }
}
