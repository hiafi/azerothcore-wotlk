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
#include "Creature.h"
#include "GameTime.h"
#include "Player.h"
#include "Random.h"
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

    /*
     * Shadow rework (docs/reworks/priest-shadow-rework.md, priest-rework.SHADOW.md "ID map" /
     * "PriestMechanics additions") - stock spell ids and talent rank spell ids the Shadow hooks
     * below need. Rank entries are the rank *spell* ids, never talent_dbc ids (PLAN sec 3.10).
     */
    enum PriestShadowMechanicsSpells
    {
        SPELL_PRIEST_SHADOW_WORD_PAIN             = 589,
        SPELL_PRIEST_MIND_BLAST                   = 8092,
        SPELL_PRIEST_SHADOW_WORD_DEATH_CAST        = 32379,
        SPELL_PRIEST_DISPERSION                   = 47585,

        // Talent rank spell ids (SHADOW.md "ID map").
        SPELL_PRIEST_CALL_OF_THE_VOID             = 200248,   // (4,0)
        SPELL_PRIEST_CALL_OF_THE_VOID_BUFF        = 200249,
        SPELL_PRIEST_DEATHSPEAKER_R1              = 200250,   // (4,1)
        SPELL_PRIEST_DEATHSPEAKER_R2              = 200251,
        SPELL_PRIEST_DEATHSPEAKER_R3              = 200252,
        SPELL_PRIEST_INSATIABLE_THIRST_R1         = 200256,   // (5,2)
        SPELL_PRIEST_INSATIABLE_THIRST_R2         = 200257,
        SPELL_PRIEST_INSATIABLE_THIRST_R3         = 200258,
        SPELL_PRIEST_LASH_OF_INSANITY_R3          = 200255,   // (5,0) rank 3 - Mastery capstone
        SPELL_PRIEST_VULNERABILITY                = 200259,   // Shadow Power (6,2) capstone debuff
        SPELL_PRIEST_WRITHING_AGONY_R3             = 200265,   // (8,0) rank 3 - Mastery capstone
        SPELL_PRIEST_DISSOLVING_SHADOWS_R3         = 200268,   // (8,3) rank 3
        SPELL_PRIEST_SURRENDER_TO_MADNESS         = 200269,   // (10,1)
        SPELL_PRIEST_MADNESS                      = 200271,   // visible stacking resource aura
        SPELL_PRIEST_TENTACLE_MIND_FLAY           = 200246,   // channeled clone, shares Mind Flay's bit
        SPELL_PRIEST_TENTACLE_OF_MADNESS_SUMMON   = 200245,

        // Improved Devouring Plague (0,1) rank 3 - "Priest spells vs a target carrying your DP" capstone.
        SPELL_PRIEST_IMPROVED_DEVOURING_PLAGUE_R3 = 63627,

        NPC_PRIEST_TENTACLE_OF_MADNESS            = 300102
    };

    constexpr int32 PRIEST_MADNESS_MAX = 500;                        // PLAN sec 1: raised cap, spec units
    constexpr int32 PRIEST_MADNESS_AURA_DURATION_MS = 30000;
    constexpr uint8 PRIEST_MADNESS_MAX_STACKS = 250;

    constexpr uint32 PRIEST_TENTACLE_MAX_COUNT = 5;
    constexpr uint32 PRIEST_TENTACLE_SHARED_ICD_MS = 3000;
    constexpr uint32 PRIEST_TENTACLE_MIND_BLAST_GUARANTEE_MS = 25000;

    // Shadow Power's (6,2) capstone flat bonus and Improved Devouring Plague's (0,1) capstone flat
    // bonus are both plain design-doc constants (8%/5%), not read live off any aura amount -
    // SHADOW.md's talent table gives them as fixed numbers, unlike the marker-read talents below.
    constexpr float PRIEST_SHADOW_POWER_VULNERABILITY_BONUS_PCT = 8.0f;
    constexpr float PRIEST_IMPROVED_DEVOURING_PLAGUE_CAPSTONE_PCT = 5.0f;
    constexpr float PRIEST_DISSOLVING_SHADOWS_CAPSTONE_PCT = 25.0f;
    constexpr float PRIEST_INSATIABLE_THIRST_BASE_VT_BONUS_PCT = 10.0f;   // tentacle's base VT bonus (design doc sec 4.1)

    // Family mask bits (dword-indexed, matching apps/dbc-tools/source/classes/priest/_masks.py -
    // PLAN sec 4.4; C++ can't import that DSL module) the Shadow hooks below match auras by.
    constexpr uint32 PRIEST_MASK_DW1_SHADOW_WORD_PAIN = 0x00008000;
    // 58381 - the helper spell Mind Flay's PERIODIC_TRIGGER_SPELL_WITH_VALUE effect fires each
    // tick, and the SpellInfo every "the player's Mind Flay damage" clause below actually sees.
    // Deliberately dword1: 15407 itself carries only the dword3 MIND_FLAY bit (0/0/1088), and the
    // tentacle's clone 200246 carries dword3 alone too - so matching on dword1 here is what keeps
    // guardians out of the player-only clauses (design doc sec 6's anti-double-dip rule).
    constexpr uint32 PRIEST_MASK_DW1_MIND_FLAY_TICK   = 0x00800000;
    constexpr uint32 PRIEST_MASK_DW1_DEVOURING_PLAGUE = 0x02000000;
    constexpr uint32 PRIEST_MASK_DW2_VAMPIRIC_TOUCH   = 0x00000400;

    // Player-keyed Madness resource (spec units, 0..500) - the first player-keyed state in this
    // file; see PriestMechanics.h's own comment on why an unsynchronized unordered_map here mirrors
    // Unit.h's own `extraAttacksTargets` member (both are only ever touched from world update,
    // which never runs a given map/player concurrently with itself).
    std::unordered_map<ObjectGuid, int32> madnessByPlayer;

    // Shared tentacle-spawn ICD (SHADOW.md "Spawn budget / ICD rules") - game-time ms of when the
    // ICD next allows an ICD-gated trigger (ShadowWordPain/MindFlay/Backlash outside Surrender) to
    // summon again, per player.
    std::unordered_map<ObjectGuid, uint32> tentacleIcdEndByPlayer;

    // Mind Blast's own "guaranteed if none summoned in the last 25 s" timestamp (design doc sec
    // 4.2) - independent of the shared ICD above, since Mind Blast always bypasses that one.
    std::unordered_map<ObjectGuid, uint32> lastMindBlastSpawnByPlayer;

    // Per-tentacle Mastery%/Versatility% snapshot (design doc sec 4.1) - see
    // Priest::TentacleSnapshot's own header comment for why only these two fields live here.
    std::unordered_map<ObjectGuid, Priest::TentacleSnapshot> tentacleSnapshotByGuid;

    // Finds whichever rank of a 3-rank talent is currently known and returns the AuraEffect at
    // `effIndex` on that rank's own spell - the "HasAura + rank-lookup" idiom SHADOW.md names as an
    // alternative to an icon-based marker read, used here instead of icon reads for every brand-new
    // custom Shadow talent (Deathspeaker, Insatiable Thirst, ...): those spells are minted fresh by
    // WP-A's concurrent data pass in this same rework, so this file has no reliable prior knowledge
    // of whatever SpellIconID they end up mined with, while the rank spell ids themselves are fixed
    // and pre-assigned in SHADOW.md's "ID map" and safe to hardcode.
    AuraEffect const* GetKnownRankEffect(Unit const* unit, std::initializer_list<uint32> rankSpellIds, uint8 effIndex)
    {
        for (uint32 rankId : rankSpellIds)
            if (AuraEffect const* eff = unit->GetAuraEffect(rankId, effIndex))
                return eff;
        return nullptr;
    }

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
        if (spellProto->SpellFamilyFlags[0] & PRIEST_MASK_DW1_MIND_FLAY_TICK)
        {
            // Lash of Insanity (5,0) capstone: "Your Mind Flay damage is increased by your Mastery.
            // This does not affect Tentacles of Madness" (design doc sec 6's Mastery table - 1.0x on
            // personal Mind Flay; the tentacle's 1.5x half belongs to Writhing Agony and is applied
            // in the isTentacleMindFlay block further down). The exclusion needs no explicit guard:
            // a tentacle's clone (200246) never reaches this dword1 branch, and `caster` is the
            // guardian rather than a Player - either condition alone already excludes it.
            if (Player* player = caster->ToPlayer())
                if (player->HasAura(SPELL_PRIEST_LASH_OF_INSANITY_R3))
                    AddPct(doneTotalMod, player->GetMasteryPercentage());

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

        // ---- Shadow rework (docs/reworks/priest-shadow-rework.md, priest-rework.SHADOW.md
        // "PriestMechanics additions" / talent table) ----
        //
        // `talentOwner` is `caster` for a normal player cast, or the tentacle's own owning player
        // when `caster` is a live Tentacle of Madness casting its Mind Flay clone (200246, the only
        // spell a tentacle ever casts) - every "caster (or the tentacle's owner)" clause below reads
        // talent state off this instead of `caster` directly, so the same check serves both without
        // duplicating it.
        bool isTentacleMindFlay = caster->IsCreature() && caster->GetEntry() == NPC_PRIEST_TENTACLE_OF_MADNESS
            && spellProto->Id == SPELL_PRIEST_TENTACLE_MIND_FLAY;

        Unit* talentOwner = caster;
        if (isTentacleMindFlay)
            if (Unit* owner = caster->GetOwner())
                talentOwner = owner;

        // Improved Devouring Plague (0,1) capstone: "All your Priest spells deal 5% increased
        // damage to a target afflicted by your Devouring Plague." Rank 3 only (63627 is the
        // capstone marker - PLAN sec 3.9's "capstone that only exists on the last rank" idiom).
        if (talentOwner->HasAura(SPELL_PRIEST_IMPROVED_DEVOURING_PLAGUE_R3))
            if (victim->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, PRIEST_MASK_DW1_DEVOURING_PLAGUE, 0, 0, talentOwner->GetGUID()))
                AddPct(doneTotalMod, PRIEST_IMPROVED_DEVOURING_PLAGUE_CAPSTONE_PCT);

        // Shadow Power (6,2) capstone: "+8% Magic damage taken" from Vulnerability (200259) -
        // applied caster-specifically in C++ since the DBC PROC_TRIGGER_SPELL that applies 200259
        // can't scope its own bonus to whichever caster applied it (WP-A data, SHADOW.md talent
        // table 6,2).
        if ((spellProto->GetSchoolMask() & SPELL_SCHOOL_MASK_MAGIC) && victim->HasAura(SPELL_PRIEST_VULNERABILITY, talentOwner->GetGUID()))
            AddPct(doneTotalMod, PRIEST_SHADOW_POWER_VULNERABILITY_BONUS_PCT);

        // Dissolving Shadows (8,3) capstone: "+25% periodic spell damage while in Dispersion."
        // Deliberately reads the CASTER's own Dispersion state, not `talentOwner`'s - a Guardian can
        // never carry 47585 itself, so using `caster` here already naturally excludes tentacles
        // without an extra IsPlayer() check (SHADOW.md: "since guardians can't be in Dispersion").
        if (damagetype == DOT && caster->HasAura(SPELL_PRIEST_DISPERSION) && caster->HasAura(SPELL_PRIEST_DISSOLVING_SHADOWS_R3))
            AddPct(doneTotalMod, PRIEST_DISSOLVING_SHADOWS_CAPSTONE_PCT);

        // Twisted Faith (9,2), Mind Blast half - migrated out of Unit::SpellPctDamageModsDone's
        // OVERRIDE_CLASS_SCRIPTS loop (`case 7377:`, PLAN sec 6.8/8's Shadow item). Reads the *same*
        // AuraEffect as "Twisted Faith - Mind Flay part" above: Twisted Faith has a single
        // OVERRIDE_CLASS_SCRIPTS effect (EFFECT_1, SpellIconID 2848, engine class-script id 7377) -
        // the two read paths that used to exist (an icon+index lookup here, a
        // GetMiscValue()==7377 switch case in Unit.cpp) both resolved the identical effect - gated
        // on Mind Blast's own spell id instead of Mind Flay's family-flag bit.
        //
        // Correction versus the migration instructions' literal wording: they describe this as
        // `GetAuraEffect(SPELL_AURA_OVERRIDE_CLASS_SCRIPTS, SPELLFAMILY_PRIEST, 7377, <index>)` -
        // but `Unit::GetAuraEffect(AuraType, SpellFamilyNames, uint32 iconId, uint8 effIndex)`
        // matches its 3rd argument against `SpellInfo::SpellIconID` (Unit.cpp ~5640:
        // `if (spell->SpellIconID == iconId && spell->SpellFamilyName == name)`), *not* against the
        // effect's own `GetMiscValue()` (which is what Unit.cpp's original `case 7377:` switch
        // actually matched on, iterating `GetAuraEffectsByType` by hand). Passing 7377 as `iconId`
        // would search for a spell whose *icon* is 7377, which is not Twisted Faith's real icon
        // (2848) and would silently never match anything. Reusing the already-correct icon-based
        // lookup below (same as the Mind Flay part) is the actual fix - see this file's report for
        // the full discrepancy note.
        if (spellProto->Id == SPELL_PRIEST_MIND_BLAST)
            if (AuraEffect* aurEff = caster->GetAuraEffect(SPELL_AURA_OVERRIDE_CLASS_SCRIPTS, SPELLFAMILY_PRIEST, 2848, 1))
                if (victim->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, PRIEST_MASK_DW1_SHADOW_WORD_PAIN, 0, 0, caster->GetGUID()))
                    AddPct(doneTotalMod, aurEff->GetAmount());

        // Tentacle of Madness' own damage path (SHADOW.md, listed right after the PriestMechanics
        // code block) - applied multiplicatively; AddPct's own application order doesn't change the
        // product, kept in the spec's textual order for readability/audit.
        if (isTentacleMindFlay)
        {
            if (Player* owner = talentOwner->ToPlayer())
            {
                // (1) Versatility from the tentacle's own snapshot - guardians skip
                // Unit::SpellPctDamageModsDone's native `IsPlayer()` Versatility gate entirely
                // (Unit.cpp ~8283-8284), so it has to be re-applied here from the snapshot taken at
                // summon instead of read live off `owner`.
                if (TentacleSnapshot const* snapshot = GetTentacleSnapshot(caster))
                    AddPct(doneTotalMod, snapshot->versatility);

                // (2) +10% vs the owner's Vampiric Touch, + Insatiable Thirst's marker on top
                // (additively per design doc sec 6/(5,2)'s own note, reaching 25% at max rank).
                if (victim->GetAuraEffect(SPELL_AURA_PERIODIC_DAMAGE, SPELLFAMILY_PRIEST, 0, PRIEST_MASK_DW2_VAMPIRIC_TOUCH, 0, owner->GetGUID()))
                {
                    float vtBonus = PRIEST_INSATIABLE_THIRST_BASE_VT_BONUS_PCT;
                    if (AuraEffect const* insatiableThirst = GetKnownRankEffect(owner,
                        { SPELL_PRIEST_INSATIABLE_THIRST_R1, SPELL_PRIEST_INSATIABLE_THIRST_R2, SPELL_PRIEST_INSATIABLE_THIRST_R3 }, EFFECT_1))
                        vtBonus += float(insatiableThirst->GetAmount());
                    AddPct(doneTotalMod, vtBonus);
                }

                // (3) Writhing Agony (8,0) capstone: "+150% of your Mastery." Player-only stat, so
                // `owner->GetMasteryPercentage()` (not the tentacle's own, which doesn't exist).
                if (owner->HasAura(SPELL_PRIEST_WRITHING_AGONY_R3))
                    AddPct(doneTotalMod, 1.5f * owner->GetMasteryPercentage());

                // (4) Call of the Void's own damage buff (200249) - read live off the owner so every
                // tentacle summoned during its 15 s window benefits, including ones summoned after
                // the buff was applied (SHADOW.md 4,0's own note; no extra plumbing needed).
                if (AuraEffect const* cotv = owner->GetAuraEffect(SPELL_PRIEST_CALL_OF_THE_VOID_BUFF, EFFECT_0))
                    AddPct(doneTotalMod, cotv->GetAmount());

                // (5)/(6) Improved Devouring Plague capstone and Shadow Power vulnerability are
                // already applied above via `talentOwner` (== `owner` here) - nothing left to do.

                // Deliberately NOT applied here: Lash of Insanity's Mastery capstone (player-only,
                // "tentacles cannot inherit" - design doc sec 6's anti-double-dip rule). It lives in
                // the Mind Flay dword1 branch above, which a tentacle's 200246 never enters.
            }
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

    /*
     * ---- Shadow rework: Madness resource (docs/reworks/priest-shadow-rework.md sec 4.3,
     * priest-rework.SHADOW.md "PriestMechanics additions") ----
     */

    bool HasMadness(Player const* player)
    {
        return player && player->HasSpell(SPELL_PRIEST_CALL_OF_THE_VOID);
    }

    namespace
    {
        Aura* GetOrCreateMadnessAura(Player* player)
        {
            if (Aura* aura = player->GetAura(SPELL_PRIEST_MADNESS))
                return aura;

            player->CastSpell(player, SPELL_PRIEST_MADNESS, true);
            return player->GetAura(SPELL_PRIEST_MADNESS);
        }

        uint8 MadnessStacksFor(int32 value)
        {
            return uint8(std::clamp(value / 2, 1, int32(PRIEST_MADNESS_MAX_STACKS)));
        }

        // "Implementation: one stacking aura, 30 sec duration, refreshing on every stack gained.
        // Not per-stack independent expiry" (design doc sec 4.3) - stack count is the *visible*
        // Madness value (floor(internal/2), min 1 once internal > 0, capped at the raised 500
        // internal / 250 visible ceiling - PLAN sec 1). Only a *gain* refreshes the 30 s duration -
        // used by AddMadness only.
        void RefreshMadnessAura(Player* player, int32 value)
        {
            if (value <= 0)
                return;

            Aura* aura = GetOrCreateMadnessAura(player);
            if (!aura)
                return;

            aura->SetStackAmount(MadnessStacksFor(value));
            aura->SetDuration(PRIEST_MADNESS_AURA_DURATION_MS);
            aura->SetMaxDuration(PRIEST_MADNESS_AURA_DURATION_MS);
        }

        // Companion to RefreshMadnessAura for ConsumeMadness: updates the visible stack count to
        // match a *lower* internal value without touching duration - "refreshing on every stack
        // gained" (design doc sec 4.3) is explicitly a gain-only rule; Call of the Void's full
        // drain and Surrender to Madness' own per-second drain must not keep extending the 30 s
        // window every time they consume Madness, only AddMadness does. Never creates the aura
        // (ConsumeMadness never raises the value, so it can only shrink an aura that already
        // exists; once the value reaches 0 the caller removes the aura outright instead).
        void UpdateMadnessAuraStackCount(Player* player, int32 value)
        {
            if (value <= 0)
                return;

            if (Aura* aura = player->GetAura(SPELL_PRIEST_MADNESS))
                aura->SetStackAmount(MadnessStacksFor(value));
        }
    }

    void AddMadness(Player* player, int32 amount, MadnessSource source)
    {
        if (!player || amount <= 0 || !HasMadness(player))
            return;

        // "Your own Mind Flay damage: 1 per tick / 3 per tick during Surrender ... Mind Blast: 5 /
        // 15 during Surrender" (design doc sec 4.3). Tentacle Mind Flay ticks and Void Eruption's
        // flat 25 are both deliberately exempt (design doc sec 4.1 "unaffected by the exclusion
        // list"; the Void Eruption row's own "flat 25 regardless" line).
        if ((source == MadnessSource::PlayerMindFlay || source == MadnessSource::MindBlast)
            && player->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS))
            amount *= 3;

        int32& value = madnessByPlayer[player->GetGUID()];
        value = std::min(value + amount, PRIEST_MADNESS_MAX);
        RefreshMadnessAura(player, value);
    }

    int32 GetMadness(Player const* player)
    {
        if (!player)
            return 0;

        auto itr = madnessByPlayer.find(player->GetGUID());
        return itr == madnessByPlayer.end() ? 0 : itr->second;
    }

    int32 ConsumeMadness(Player* player, int32 amount)
    {
        if (!player)
            return 0;

        auto itr = madnessByPlayer.find(player->GetGUID());
        if (itr == madnessByPlayer.end() || itr->second <= 0)
            return 0;

        int32 consumed = amount < 0 ? itr->second : std::min(amount, itr->second);
        itr->second -= consumed;

        if (itr->second <= 0)
        {
            madnessByPlayer.erase(itr);

            // The entry is erased first on purpose: this removal does run through
            // spell_pri_madness's OnRemove (which clears unconditionally, see ClearMadness), and
            // that hook then finds nothing left to erase. The internal value is authoritative here.
            player->RemoveAurasDueToSpell(SPELL_PRIEST_MADNESS);
        }
        else
            UpdateMadnessAuraStackCount(player, itr->second);

        return consumed;
    }

    void ClearMadness(ObjectGuid playerGuid)
    {
        madnessByPlayer.erase(playerGuid);
    }

    void ClearShadowPlayerState(ObjectGuid playerGuid)
    {
        madnessByPlayer.erase(playerGuid);
        tentacleIcdEndByPlayer.erase(playerGuid);
        lastMindBlastSpawnByPlayer.erase(playerGuid);
    }

    /*
     * ---- Shadow rework: Tentacle of Madness spawn/despawn (docs/reworks/priest-shadow-rework.md
     * sec 4.1/4.2, priest-rework.SHADOW.md "PriestMechanics additions" / "Spawn budget / ICD rules") ----
     */

    bool TrySummonTentacle(Player* player, TentacleTrigger trigger)
    {
        if (!player)
            return false;

        // Max 5 live tentacles, always enforced regardless of trigger/ICD (design doc sec 4.5:
        // "The 5 tentacle maximum still applies during Surrender."). `m_Controlled` is the same
        // public `Unit::ControlSet` idiom spell_dk.cpp/spell_hunter.cpp/spell_item.cpp already use
        // to find a player's own guardians/minions by entry.
        uint32 liveCount = 0;
        for (Unit* controlled : player->m_Controlled)
            if (controlled->GetEntry() == NPC_PRIEST_TENTACLE_OF_MADNESS)
                ++liveCount;

        if (liveCount >= PRIEST_TENTACLE_MAX_COUNT)
            return false;

        bool surrenderActive = player->HasAura(SPELL_PRIEST_SURRENDER_TO_MADNESS);

        // "Shared internal cooldown: 3 seconds. Applies across [ShadowWordPain/MindFlay/Backlash]
        // ... Mind Blast [and kill] bypass it" (design doc sec 4.2); "While active ... every Shadow
        // Word: Pain and Mind Flay damage event summons one, ignoring the shared cooldown" during
        // Surrender (sec 4.5) - Backlash is never exempted by Surrender.
        bool bypassesIcd = false;
        switch (trigger)
        {
            case TentacleTrigger::MindBlast:
            case TentacleTrigger::Kill:
                bypassesIcd = true;
                break;
            case TentacleTrigger::ShadowWordPain:
            case TentacleTrigger::MindFlay:
                bypassesIcd = surrenderActive;
                break;
            case TentacleTrigger::Backlash:
                bypassesIcd = false;
                break;
        }

        ObjectGuid guid = player->GetGUID();
        uint32 now = GameTime::GetGameTimeMS().count();

        if (!bypassesIcd)
        {
            uint32& icdEnd = tentacleIcdEndByPlayer[guid];
            if (now < icdEnd)
                return false;
            icdEnd = now + PRIEST_TENTACLE_SHARED_ICD_MS;
        }

        // "Always summons one if none has been summoned this way in the last 25 sec" (design doc
        // sec 4.2) - the clock resets only on an actual summon, so pressure keeps building while
        // the max-5 cap blocks it. See IsMindBlastTentacleGuaranteed's own comment for the read side.
        if (trigger == TentacleTrigger::MindBlast)
            lastMindBlastSpawnByPlayer[guid] = now;

        player->CastSpell(player, SPELL_PRIEST_TENTACLE_OF_MADNESS_SUMMON, true);
        return true;
    }

    bool IsMindBlastTentacleGuaranteed(Player const* player)
    {
        if (!player)
            return false;

        auto itr = lastMindBlastSpawnByPlayer.find(player->GetGUID());
        if (itr == lastMindBlastSpawnByPlayer.end())
            return true;

        return GameTime::GetGameTimeMS().count() - itr->second >= PRIEST_TENTACLE_MIND_BLAST_GUARANTEE_MS;
    }

    void DespawnTentacles(Player* player)
    {
        if (!player)
            return;

        // Copy first - Creature::DespawnOrUnsummon() removes the tentacle from `m_Controlled` as
        // part of unsummoning, which would invalidate an iterator over that same set.
        std::vector<Unit*> tentacles;
        for (Unit* controlled : player->m_Controlled)
            if (controlled->GetEntry() == NPC_PRIEST_TENTACLE_OF_MADNESS)
                tentacles.push_back(controlled);

        for (Unit* tentacle : tentacles)
            if (Creature* creature = tentacle->ToCreature())
                creature->DespawnOrUnsummon();
    }

    TentacleSnapshot const* GetTentacleSnapshot(Unit const* tentacle)
    {
        if (!tentacle)
            return nullptr;

        auto itr = tentacleSnapshotByGuid.find(tentacle->GetGUID());
        return itr == tentacleSnapshotByGuid.end() ? nullptr : &itr->second;
    }

    void SetTentacleSnapshot(ObjectGuid tentacleGuid, TentacleSnapshot const& snapshot)
    {
        tentacleSnapshotByGuid[tentacleGuid] = snapshot;
    }

    void ClearTentacleSnapshot(ObjectGuid tentacleGuid)
    {
        tentacleSnapshotByGuid.erase(tentacleGuid);
    }

    void OnKill(Unit* killer, Unit* victim, SpellInfo const* spellProto)
    {
        if (!killer || !victim || !spellProto)
            return;

        Player* killerPlr = killer->ToPlayer();
        if (!killerPlr)
            return;

        // Deathspeaker (4,1) kill clause: "When your Shadow Word: Death kills an enemy ..."
        // Excludes Critter instead of gating on "yields experience or honor" (design doc sec 2's
        // global rule - nothing here yields XP/honor at the level cap). Exempt from the shared ICD
        // (design doc sec 4.2's trigger table). Deliberately NOT gated on Priest::HasMadness (Call
        // of the Void) - that gate is specific to the Madness *resource* (AddMadness/ConsumeMadness,
        // SHADOW.md: "All Madness calls are no-ops unless HasMadness"). Tentacle-spawn triggers
        // (Deathspeaker/Writhing Agony/Lash of Insanity/Mind Blast) are independent talents with no
        // Call of the Void prerequisite - the GetKnownRankEffect lookup below is this clause's own,
        // sufficient gate (no known Deathspeaker rank -> nullptr -> early return).
        if (spellProto->Id != SPELL_PRIEST_SHADOW_WORD_DEATH_CAST || victim->IsCritter())
            return;

        AuraEffect const* deathspeaker = GetKnownRankEffect(killerPlr,
            { SPELL_PRIEST_DEATHSPEAKER_R1, SPELL_PRIEST_DEATHSPEAKER_R2, SPELL_PRIEST_DEATHSPEAKER_R3 }, EFFECT_2);
        if (!deathspeaker)
            return;

        float chance = float(deathspeaker->GetAmount()) * (1.0f + killerPlr->GetProcChancePercentage() / 100.0f);
        if (roll_chance_f(chance))
            TrySummonTentacle(killerPlr, TentacleTrigger::Kill);
    }
}
