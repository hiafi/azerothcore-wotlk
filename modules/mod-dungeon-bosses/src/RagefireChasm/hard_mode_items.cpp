/*
 * mod-dungeon-bosses, Ragefire Chasm: the hard mode item effects of Taragaman the Hungerer, Starving (designer text:
 * docs/dungeons/ragefire-chasm-rework.md ## Loot, the hard mode list). The spells are
 * apps/dbc-tools/source/items/ragefire_chasm_hard_mode_effects.py; every damage number comes from potency, the heal and
 * the absorb are shares of a hit or a heal that already carries the wearer's bonuses, so nothing here sizes a hit. The
 * scaled effects (scale="budget") carry their own copies on every tier above 71, bound to the same scripts, so a script
 * never casts a family spell by its base id: ItemSpellCopies::Resolve (the generated ItemSpellCopies.h) gives the copy
 * in the tier of the spell or aura it runs for, and the base id on the 71 tier. Feed and Bloodward have no copies.
 *
 *   spell_rfc_taragamans_fang        213500 Taragaman's Fang (Use). The leap is spell data (CHARGE), skipped when the
 *                                    wearer is in melee range of the target already; on the delayed hit the wearer
 *                                    bites with the tier's 213501 as soon as the charge has ended and the wearer is at
 *                                    the target (at once without a leap).
 *   spell_rfc_hungering_bite         213501 Hungering Bite. Heals the wearer (213502) for the damage dealt, overkill
 *                                    left out.
 *   spell_rfc_heart_of_the_starving  213503 Heart of the Starving (Equip). A landed direct heal on a living target (the
 *                                    healer included) that was below effect 1's amount in percent health before it
 *                                    gives it 213504 (Bloodward), effect 2's amount in percent of the heal, unless the
 *                                    target still has a larger Bloodward.
 *   spell_rfc_one_roll_per_cast      213505 Felstorm Greatblade (Equip). The proc check lets each cast reach the
 *                                    spell_proc roll once: an area ability's later targets are refused (Systems.md
 *                                    section 5, "A cast rolls once").
 *
 * Every script (but the proc check) logs one DEBUG line, "rfc-items <effect> ...", in
 * module.dungeonbosses.
 */

#include "EventProcessor.h"
#include "GameTime.h"
#include "ItemSpellCopies.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "RagefireChasmHardModeItemsLogic.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Unit.h"

using namespace RagefireChasmHardModeItems;

namespace
{
    constexpr char const* kLog = "module.dungeonbosses";

    // The spell `baseId` for the tier of the spell or aura `spellInfo` (itself one of the declared spells or a copy).
    uint32 TierSpell(SpellInfo const* spellInfo, uint32 baseId)
    {
        return ItemSpellCopies::Resolve(spellInfo->Id, baseId);
    }

    // One roll per cast: true the first time a cast reaches the check, false for its later targets. An event without
    // a spell (an auto attack) always rolls.
    bool FirstRollOfCast(CastStamp& rolled, ProcEventInfo& eventInfo)
    {
        Spell const* spell = eventInfo.GetProcSpell();
        if (!spell)
            return true;
        CastStamp const now{ spell, spell->GetSpellInfo()->Id, spell->m_cast_count,
            CastMoment(spell->GetDelayStart(), static_cast<std::uint64_t>(GameTime::GetGameTimeMS().count())) };
        if (SameCast(rolled, now))
            return false;
        rolled = now;
        return true;
    }

    // The bite on arrival, if the leap brought the wearer to the target.
    void Bite(Unit* wearer, ObjectGuid victimGuid, uint32 biteId)
    {
        Unit* victim = ObjectAccessor::GetUnit(*wearer, victimGuid);
        if (!wearer->IsAlive() || !victim || !victim->IsAlive() || !wearer->IsWithinCombatRange(victim, kBiteReach))
            return;
        wearer->CastSpell(victim, biteId, true);
        LOG_DEBUG(kLog, "rfc-items fang {} bit {} ({})", wearer->GetGUID().ToString(), victim->GetGUID().ToString(),
            biteId);
    }

    // Lives in the wearer's own event list, so the wearer outlives it.
    class FangLandingEvent : public BasicEvent
    {
    public:
        FangLandingEvent(Unit* wearer, ObjectGuid victimGuid, uint32 biteId) : _wearer(wearer),
            _victimGuid(victimGuid), _biteId(biteId) { }

        bool Execute(uint64 execTime, uint32 /*diff*/) override
        {
            _waitedMs += kLeapPollMs;
            if (WaitForLanding(_wearer->HasUnitState(UNIT_STATE_CHARGING), _waitedMs))
            {
                _wearer->m_Events.AddEvent(this, execTime + kLeapPollMs, false);
                return false;
            }
            Bite(_wearer, _victimGuid, _biteId);
            return true;
        }

    private:
        Unit* _wearer;
        ObjectGuid _victimGuid;
        uint32 _biteId;
        uint32 _waitedMs = 0;
    };
}

// 213500 Taragaman's Fang: no leap for a wearer in melee range; on the hit (delayed by the distance) bite once the
// wearer has landed.
class spell_rfc_taragamans_fang : public SpellScript
{
    PrepareSpellScript(spell_rfc_taragamans_fang);

    bool Validate(SpellInfo const* spellInfo) override
    {
        return ValidateSpellInfo({ TierSpell(spellInfo, SPELL_HUNGERING_BITE) });
    }

    // EffectCharge moves the wearer in the launch target mode, so preventing it here leaves the wearer in place and out
    // of UNIT_STATE_CHARGING; effect 2's DUMMY hit still comes.
    void HandleLeap(SpellEffIndex /*effIndex*/)
    {
        Unit* wearer = GetCaster();
        Unit* victim = GetHitUnit();
        if (!wearer || !victim)
            return;

        if (!LeapMoves(wearer->IsWithinMeleeRange(victim), wearer->GetExactDist(victim), victim->GetCombatReach()))
            PreventHitDefaultEffect(EFFECT_0);
    }

    void HandleHit(SpellEffIndex /*effIndex*/)
    {
        Unit* wearer = GetCaster();
        Unit* victim = GetHitUnit();
        if (!wearer || !victim)
            return;

        uint32 const biteId = TierSpell(GetSpellInfo(), SPELL_HUNGERING_BITE);
        if (WaitForLanding(wearer->HasUnitState(UNIT_STATE_CHARGING), 0))
            wearer->m_Events.AddEventAtOffset(new FangLandingEvent(wearer, victim->GetGUID(), biteId),
                Milliseconds(kLeapPollMs));
        else
            Bite(wearer, victim->GetGUID(), biteId);
    }

    void Register() override
    {
        OnEffectLaunchTarget += SpellEffectFn(spell_rfc_taragamans_fang::HandleLeap, EFFECT_0, SPELL_EFFECT_CHARGE);
        OnEffectHitTarget += SpellEffectFn(spell_rfc_taragamans_fang::HandleHit, EFFECT_1, SPELL_EFFECT_DUMMY);
    }
};

// 213501 Hungering Bite: heal the wearer for the damage dealt.
class spell_rfc_hungering_bite : public SpellScript
{
    PrepareSpellScript(spell_rfc_hungering_bite);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_FEED });
    }

    void HandleBeforeHit(SpellMissInfo /*missInfo*/)
    {
        if (Unit* victim = GetHitUnit())
            _healthBefore = victim->GetHealth();
    }

    // Runs for a hit that landed, after the damage: GetHitDamage is what was dealt (armor, crit and absorbs applied).
    void HandleAfterHit()
    {
        Unit* wearer = GetCaster();
        if (!wearer || !wearer->IsAlive())
            return;

        int32 const heal = BiteHeal(GetHitDamage(), _healthBefore);
        if (heal <= 0)
            return;

        wearer->CastCustomSpell(wearer, SPELL_FEED, &heal, nullptr, nullptr, true);
        LOG_DEBUG(kLog, "rfc-items fang {} fed for {}", wearer->GetGUID().ToString(), heal);
    }

    void Register() override
    {
        BeforeHit += BeforeSpellHitFn(spell_rfc_hungering_bite::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_rfc_hungering_bite::HandleAfterHit);
    }

    uint32 _healthBefore = 0;
};

// 213503 Heart of the Starving: a heal on a target below the threshold also leaves a Bloodward.
class spell_rfc_heart_of_the_starving : public AuraScript
{
    PrepareAuraScript(spell_rfc_heart_of_the_starving);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ SPELL_BLOODWARD });
    }

    // A landed direct heal (spell_proc: heal type, hit phase) on any living target that was below the threshold before
    // it; the check runs before the internal cooldown starts, so only those heals spend it. At 100% there is no roll to
    // guard: an area heal's next low target meets the cooldown its first one started. A heal whose ward would be
    // smaller than what a Bloodward on the target (any healer's) has left gives none and spends nothing.
    bool CheckProc(ProcEventInfo& eventInfo)
    {
        HealInfo const* heal = eventInfo.GetHealInfo();
        Unit* healed = eventInfo.GetActionTarget();
        AuraEffect const* threshold = GetEffect(EFFECT_0);
        AuraEffect const* share = GetEffect(EFFECT_1);
        if (!heal || !heal->GetSpellInfo() || !healed || !healed->IsAlive() || !threshold || !share)
            return false;
        int32 const absorb = BloodwardAmount(heal->GetHeal(), share->GetAmount());
        AuraEffect const* ward = healed->GetAuraEffect(SPELL_BLOODWARD, EFFECT_0);
        if (absorb <= 0 || !BloodwardReplaces(absorb, ward ? ward->GetAmount() : 0))
            return false;
        return BelowThresholdBeforeHeal(healed->GetHealth(), heal->GetEffectiveHeal(), healed->GetMaxHealth(),
            threshold->GetAmount());
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        Unit* healer = GetTarget();
        Unit* healed = eventInfo.GetActionTarget();
        HealInfo const* heal = eventInfo.GetHealInfo();
        AuraEffect const* share = GetEffect(EFFECT_1);
        if (!healer->IsAlive() || !healed || !heal || !share)
            return;

        int32 const absorb = BloodwardAmount(heal->GetHeal(), share->GetAmount());
        healer->CastCustomSpell(healed, SPELL_BLOODWARD, &absorb, nullptr, nullptr, true, nullptr, aurEff);
        LOG_DEBUG(kLog, "rfc-items heart {} healed {} for {}: Bloodward {}", healer->GetGUID().ToString(),
            healed->GetGUID().ToString(), heal->GetHeal(), absorb);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rfc_heart_of_the_starving::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_rfc_heart_of_the_starving::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 213505 Felstorm Greatblade: one roll per cast. The engine runs this check before it rolls the spell_proc chance, so
// refusing a cast's later targets leaves exactly one roll per cast; the PROC_TRIGGER_SPELL aura's own default action
// casts the Felstorm.
class spell_rfc_one_roll_per_cast : public AuraScript
{
    PrepareAuraScript(spell_rfc_one_roll_per_cast);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* target = eventInfo.GetActionTarget();
        if (!target || !GetTarget()->IsAlive())
            return false;
        return FirstRollOfCast(_rolled, eventInfo);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_rfc_one_roll_per_cast::CheckProc);
    }

    CastStamp _rolled;
};

void AddSC_rfc_hard_mode_items()
{
    RegisterSpellScript(spell_rfc_taragamans_fang);
    RegisterSpellScript(spell_rfc_hungering_bite);
    RegisterSpellScript(spell_rfc_heart_of_the_starving);
    RegisterSpellScript(spell_rfc_one_roll_per_cast);
}
