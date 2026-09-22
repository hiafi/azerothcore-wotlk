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
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "Unit.h"
#include "Util.h"

namespace
{
    // void_eruption_buff_200140's own SpellIconID (apps/dbc-tools/source/classes/priest/
    // priest_trigger_spells.py, mined into SpellIcon.dbc by apps/dbc-tools/build_patch_i.py's
    // ICON_ID_VOID_ERUPTION) - keep in sync if that spell's icon ever changes.
    constexpr uint32 PRIEST_ICON_VOIDFORM = 90104;

    // Divine Fury's (1,2) stock SpellIconID (apps/dbc-tools/source/classes/priest/
    // priest_trigger_spells.py: divine_fury_18530/18531/18533, `spell_icon_id=307`) and Test of
    // Faith's (8,2) stock SpellIconID (test_of_faith_47558/47559/47560, `spell_icon_id=2844`) -
    // both stock icons, unchanged by the rework's data pass.
    constexpr uint32 PRIEST_ICON_DIVINE_FURY = 307;
    constexpr uint32 PRIEST_ICON_TEST_OF_FAITH = 2844;

    // Priest SpellFamilyFlags bits Holy's cross-cutting hooks need as raw dword values - C++ can't
    // import apps/dbc-tools/source/classes/priest/_masks.py, which is the authoritative source
    // these are copied from (PLAN sec 4.4/HOLY.md). Keep in sync if that file's values ever change.
    constexpr uint32 PRIEST_MASK_DW1_SMITE = 0x00000080;
    constexpr uint32 PRIEST_MASK_DW1_HOLY_FIRE = 0x00100000;
    // _masks.py PRIEST_HEAL_MASK, dword 1/2/3 (Renew|PoH|FlashHeal|GreaterHeal|HolyNovaHeal|
    // DesperatePrayer|CoH|Lightwell, BindingHeal|PoM|PenanceHealBolt|DivineHymn,
    // DivineStar|Halo|HWSerenity|HWSanctify).
    constexpr uint32 PRIEST_HEAL_MASK_DW1 = 0x59001A40;
    constexpr uint32 PRIEST_HEAL_MASK_DW2 = 0x00410024;
    constexpr uint32 PRIEST_HEAL_MASK_DW3 = 0x01830000;

    // Renew extension pool (docs/reworks/priest-holy-rework.md 5.3): "Total duration may never
    // exceed 21 seconds from application" - base Renew duration is 15 s, so this is the ceiling on
    // extensions from Holy Concentration (6,0) and Empowered Renew's capstone (8,0) combined.
    constexpr int32 PRIEST_RENEW_EXTENSION_POOL_MAX_MS = 6000;

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
        SPELL_PRIEST_SPIRIT_SHELL_ABSORB        = 200167,

        // Holy rework (HOLY.md talent table 8,2). Talent rank spell id, never a talent_dbc id
        // (PLAN sec 3.10).
        SPELL_PRIEST_TEST_OF_FAITH_R3            = 47560,   // (8,2) rank 3 - capstone marker

        // Holy rework (HOLY.md talent table 2,0 / docs/reworks/priest-holy-rework.md sec 2):
        // Desperate Prayer's own tooltip. Baseline spell, not a talent rank.
        SPELL_PRIEST_DESPERATE_PRAYER            = 19236
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

    // Test of Faith (8,2) capstone: "10% less magic damage taken while casting Smite, Holy Fire or
    // any Priest healing spell." `castSpell` is whatever the priest is currently casting/channeling.
    bool IsTestOfFaithProtectedCast(SpellInfo const* castSpell)
    {
        if (!castSpell || castSpell->SpellFamilyName != SPELLFAMILY_PRIEST)
            return false;

        if (castSpell->SpellFamilyFlags[0] & (PRIEST_MASK_DW1_SMITE | PRIEST_MASK_DW1_HOLY_FIRE))
            return true;

        return castSpell->SpellFamilyFlags.HasFlag(PRIEST_HEAL_MASK_DW1, PRIEST_HEAL_MASK_DW2, PRIEST_HEAL_MASK_DW3);
    }
}

namespace Priest
{
    void ApplyDoneDamagePctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, DamageEffectType damagetype, float& doneTotalMod)
    {
        // Divine Fury (1,2): "+3/6/9% direct magic damage against targets afflicted by your Holy
        // Fire" - the *spell* is classless per PLAN sec 1's resolved design call ("direct
        // Holy-school damage from any class, not Priest-family only"), so this sits above the
        // priest-family gate below. The caster class check is only a cheap pre-filter: only a
        // Priest can carry the aura, so it spares every Paladin/Druid holy hit the dummy-aura scan.
        if (damagetype != DOT && caster->IsClass(CLASS_PRIEST, CLASS_CONTEXT_ABILITY)
            && (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_HOLY))
        {
            AuraEffect const* divineFury = caster->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_DIVINE_FURY,
                EFFECT_1);
            if (divineFury && victim->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST,
                PRIEST_MASK_DW1_HOLY_FIRE, 0, 0, caster->GetGUID()))
                AddPct(doneTotalMod, divineFury->GetAmount());
        }

        // Everything below this gate is priest-family-only and used to live in
        // Unit::SpellPctDamageModsDone's own `case SPELLFAMILY_PRIEST:`.
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

        // Test of Faith (8,2) damage clause: "Smite and Holy Fire damage +4/8/12% against targets
        // at or below 50% health." eff2 (EFFECT_1) is a plain DUMMY carrying the rank amount -
        // eff1 (EFFECT_0, the healing clause) is handled by ApplyDoneHealingPctMods below.
        if (spellProto->SpellFamilyFlags[0] & (PRIEST_MASK_DW1_SMITE | PRIEST_MASK_DW1_HOLY_FIRE))
        {
            AuraEffect const* testOfFaith = caster->GetDummyAuraEffect(SPELLFAMILY_PRIEST, PRIEST_ICON_TEST_OF_FAITH,
                EFFECT_1);
            if (testOfFaith && victim->HealthBelowPct(50))
                AddPct(doneTotalMod, testOfFaith->GetAmount());
        }
    }

    void ApplySpellCritChanceMods(Unit const* caster, SpellInfo const* spellProto, float& critChance)
    {
        // Inner Focus (2,1): "Flash Heal: increases critical strike chance to 100%"
        // (docs/reworks/priest-disc-rework.md). *To*, not *by* - an absolute override, and the
        // charge itself is consumed by the normal SpellMod path on the same cast.
        if (spellProto->Id == SPELL_PRIEST_FLASH_HEAL && caster->HasAura(SPELL_PRIEST_INNER_FOCUS))
            critChance = 100.0f;

        // Desperate Prayer (2,0): "Below 50% health it is a guaranteed critical heal"
        // (docs/reworks/priest-holy-rework.md sec 2; HOLY.md 2,0's own script column names this
        // exact clause - talent-tooltip-audit fix, WP-C: tooltip already claimed this, no
        // implementation existed). Self-cast only, so `caster`'s own health is what the tooltip
        // means by "you."
        if (spellProto->Id == SPELL_PRIEST_DESPERATE_PRAYER && caster->HealthBelowPct(50))
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

    void ApplyDoneHealingPctMods(Unit* caster, Unit* victim, SpellInfo const* spellProto, float& doneTotalMod)
    {
        if (!caster || !victim)
            return;

        // Test of Faith (8,2), migrated out of Unit::SpellPctHealingModsDone's
        // OVERRIDE_CLASS_SCRIPTS loop (`case 21: case 6935: case 6918:`, one misc value per rank -
        // PLAN sec 6.8). The icon-keyed read below matches all three ranks at once, which is why
        // none of them may stay in that switch (they'd apply twice). That loop's own
        // IsAffectedOnSpell() call is what actually scopes the bonus to Priest healing spells;
        // reproduced here so the semantics don't change.
        AuraEffect const* testOfFaith = caster->GetAuraEffect(SPELL_AURA_OVERRIDE_CLASS_SCRIPTS, SPELLFAMILY_PRIEST,
            PRIEST_ICON_TEST_OF_FAITH, EFFECT_0);
        if (testOfFaith && testOfFaith->IsAffectedOnSpell(spellProto) && victim->HealthBelowPct(50))
            AddPct(doneTotalMod, testOfFaith->GetAmount());
    }

    void ApplySpellDamageTakenPctMods(Unit* victim, Unit* /*attacker*/, SpellInfo const* spellProto, float& takenMod)
    {
        // Test of Faith (8,2) capstone (rank 3 only, eff3/EFFECT_2 DUMMY=1 is the marker - no
        // icon-read needed per PLAN sec 3.9's "capstone that only exists on the last rank" idiom):
        // "10% less magic damage taken while casting Smite, Holy Fire or any Priest healing spell."
        Player* player = victim ? victim->ToPlayer() : nullptr;
        if (!player || !spellProto)
            return;

        if (spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_NORMAL)
            return;

        if (!player->HasAura(SPELL_PRIEST_TEST_OF_FAITH_R3))
            return;

        // Whatever the priest is currently casting/channeling - unrelated to the incoming spell
        // that's dealing the damage this function is computing taken-mods for.
        Spell const* currentSpell = player->GetCurrentSpell(CURRENT_GENERIC_SPELL);
        if (!currentSpell)
            currentSpell = player->GetCurrentSpell(CURRENT_CHANNELED_SPELL);
        if (!currentSpell)
            return;

        if (IsTestOfFaithProtectedCast(currentSpell->GetSpellInfo()))
            takenMod *= 0.9f;
    }

    void ExtendRenewDuration(Aura* renew, int32 ms)
    {
        if (!renew)
            return;

        int32 baseDuration = renew->GetSpellInfo()->GetMaxDuration();
        int32 alreadyUsed = renew->GetMaxDuration() - baseDuration;

        ms = std::min(ms, PRIEST_RENEW_EXTENSION_POOL_MAX_MS - alreadyUsed);
        if (ms <= 0)
            return;

        renew->SetDuration(renew->GetDuration() + ms);
        renew->SetMaxDuration(renew->GetMaxDuration() + ms);
    }
}
