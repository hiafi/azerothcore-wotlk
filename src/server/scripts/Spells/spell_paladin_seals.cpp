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
 * Paladin rework - shared seal core, class-wide baseline scripts and Part C's aura-system scripts
 * (.agents/plans/paladin-rework/paladin-rework.SHARED.md A4 script table, Part B B1.5-B5, Part C C1.6).
 * Stock spell_paladin.cpp stays unedited: every class it displaces is unbound by WP-A (unbind_script)
 * and replaced here, per .agents/docs/upstream-merge.md.
 *
 * Common rules (SHARED Part B CR1-CR5): non-player casters return early (NPC paladins, docs/npc_seals.md),
 * DUMMY / PROC_TRIGGER_SPELL procs prevent their default action, removal paths use find-only state access
 * (inside Paladin::), once-per-cast guards are serial based (Deliverance casts one unleash Spell per target).
 */

#include "Generated/PaladinData.h"
#include "PaladinMechanics.h"
#include "Cell.h"
#include "CellImpl.h"
#include "DynamicObject.h"
#include "GameTime.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Log.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "Util.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <vector>

namespace
{
    enum PaladinSealStockSpells
    {
        // Stock ids kept as literals (WarlockMechanics.h convention; the generated header's JoJ name points at 53407)
        SPELL_PAL_JUDGEMENT_OF_JUSTICE_DEBUFF   = 20184,
        SPELL_PAL_JUDGEMENT_OF_LIGHT_DEBUFF     = 20185,
        SPELL_PAL_JUDGEMENT_OF_WISDOM_DEBUFF    = 20186,
        SPELL_PAL_GLYPH_OF_DIVINITY             = 54939,
        SPELL_PAL_ENERGIZE_GLYPH_OF_DIVINITY    = 54986,
        SPELL_PAL_ARENA_DAMPENING               = 74410,
        SPELL_PAL_BATTLEGROUND_DAMPENING        = 74411
    };

    enum PaladinSealScriptData
    {
        PAL_UNLEASH_MAX_TARGETS         = 5,    // Deliverance: target + up to 4 more (B3.2 step 1)
        PAL_COMMAND_EXTRA_UNLEASHES     = 2,    // Deliverance of Command: 201070 on the main target + its 2 closest
        PAL_SEAL_EFFECT_PCT_OF_BASE     = 20,   // Seal of Light / Wisdom: 20% of base health / mana
        PAL_SPELL_ICON_STRENGTH_OF_WRYNN        = 5033,
        PAL_SPELL_ICON_HELLSCREAM_WARSONG       = 5034,
        PAL_BATTLE_SPEED_PPM                    = 15    // 20185 / 20186 stock PPM (B11)
    };

    // 0.63% haste / damage-done per stack (201099 / 201100), 1.25% Holy damage per stack (201103), 10% base mana per
    // second for 5 s regardless of stacks (201104) - SHARED B4.2
    constexpr float PAL_HASTE_PCT_PER_STACK         = 0.63f;
    constexpr float PAL_LIGHT_DAMAGE_PCT_PER_STACK  = 1.25f;
    constexpr float PAL_WISDOM_MANA_PCT_PER_TICK    = 10.0f;
    constexpr float PAL_VENGEANCE_SHIELD_PCT        = 0.20f;   // 20% of the unleash DoT total
    constexpr float PAL_DELIVERANCE_DOT_SCALE       = 0.4f;    // the AoE DoT is a 40% copy of the Judgement one

    Player* GetPlayerOrNull(Unit* unit)
    {
        return unit ? unit->ToPlayer() : nullptr;
    }

    // "Would have been a valid enemy ignoring death": AfterHit runs after the damage, so a target killed by this very
    // hit already fails IsValidAttackTarget ("can't attack dead", Unit.cpp). Killing blows count (user ruling), so a
    // dead unit is accepted when it is hostile to the caster; every other check still runs for living units.
    bool IsEnemyIgnoringDeath(Unit const* caster, Unit const* target)
    {
        if (!caster || !target || caster == target)
            return false;

        return caster->IsValidAttackTarget(target) || (!target->IsAlive() && caster->IsHostileTo(target));
    }

    Paladin::SealType SealTypeFromPrimed(uint32 spellId)
    {
        for (uint8 i = 0; i < uint8(Paladin::SealType::Count); ++i)
            if (Paladin::GetPrimedSpell(Paladin::SealType(i)) == spellId)
                return Paladin::SealType(i);

        return Paladin::SealType::None;
    }
}

// ===========================================================================================
// SHARED Part B: seal core
// ===========================================================================================

// 21084, 20375, 31801, 20164, 20165, 20166 - the six seals (B1.6)
class spell_pal_seal_aura : public AuraScript
{
    PrepareAuraScript(spell_pal_seal_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        for (uint8 i = 0; i < uint8(Paladin::SealType::Count); ++i)
        {
            Paladin::SealType const type = Paladin::SealType(i);
            if (!ValidateSpellInfo({ Paladin::GetPassiveSpell(type, false), Paladin::GetPassiveSpell(type, true) }))
                return false;
        }

        return true;
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetTarget();
        if (!owner || !eventInfo.GetActionTarget())
            return false;

        Player* player = owner->ToPlayer();
        if (!player)
            return !eventInfo.GetSpellInfo(); // CR3: an NPC paladin's seal procs from white swings only

        return Paladin::IsSealPassiveSource(player, eventInfo);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* owner = GetTarget();
        Unit* target = eventInfo.GetActionTarget();
        if (!owner || !target || !target->IsAlive())
            return;

        Paladin::SealType const type = Paladin::GetSealType(GetId());
        if (type == Paladin::SealType::None)
            return;

        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        bool const normalized = procSpell && owner->IsPlayer();
        uint32 const passiveId = Paladin::GetPassiveSpell(type, normalized);

        if (type == Paladin::SealType::Command)
        {
            // Stock rule (spell_paladin.cpp seal of command): a single-target attack cleaves, a multi-target one
            // doesn't
            int32 const maxTargets = (procSpell && Paladin::IsMultiTargetAttack(procSpell)) ? 1 : 3;
            owner->CastCustomSpell(passiveId, SPELLVALUE_MAX_TARGETS, maxTargets, target, TRIGGERED_FULL_MASK,
                nullptr, aurEff);
        }
        else
            owner->CastSpell(target, passiveId, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Player* player = GetPlayerOrNull(GetTarget()))
            Paladin::OnSealApplied(player, Paladin::GetSealType(GetId()), GetAura());
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetPlayerOrNull(GetTarget());
        AuraApplication const* application = GetTargetApplication();
        if (player && application)
            Paladin::OnSealRemoved(player, Paladin::GetSealType(GetId()), application->GetRemoveMode());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_seal_aura::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_seal_aura::HandleProc, EFFECT_0, SPELL_AURA_PROC_TRIGGER_SPELL);
        AfterEffectApply += AuraEffectApplyFn(spell_pal_seal_aura::HandleApply, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_seal_aura::HandleRemove, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL, AURA_EFFECT_HANDLE_REAL);
    }
};

// SpellScript half of the "spell_pal_seal_aura" pair (user ruling 2026-10-03): recasting the SAME seal while it is
// active resets its stacks, exactly like swapping seals. Without this the engine refreshes the live aura through
// ModStackAmount(1) (no AfterEffectApply), bumping the display stack and desyncing SealState.
class spell_pal_seal_recast : public SpellScript
{
    PrepareSpellScript(spell_pal_seal_recast);

    void RemoveActiveCopy()
    {
        Player* player = GetPlayerOrNull(GetCaster()); // CR3: NPC seals keep the stock refresh
        if (!player)
            return;

        // Removal by default mode: OnSealRemoved loses the stacks and casts no Primed (that is expiry only); the
        // fresh application below then runs OnSealApplied exactly once with a full duration and display stack 1.
        player->RemoveAurasDueToSpell(GetSpellInfo()->Id, player->GetGUID());
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_pal_seal_recast::RemoveActiveCopy);
    }
};

// 201081-201092 - seal passives (B1.4)
class spell_pal_seal_passive : public SpellScript
{
    PrepareSpellScript(spell_pal_seal_passive);

    void FilterTargets(std::list<WorldObject*>& targets)
    {
        // Copy of stock spell_pal_seal_of_command: a MaxAffectedTargets of 1 means "no cleave"
        if (SpellValue const* spellValue = GetSpellValue())
            if (spellValue->MaxAffectedTargets == 1)
                targets.clear();
    }

    void Register() override
    {
        // Only the Command pair does work. The ability form (normalized) has the chain on both effects.
        uint32 const autoId = Paladin::GetPassiveSpell(Paladin::SealType::Command, false);
        uint32 const normalizedId = Paladin::GetPassiveSpell(Paladin::SealType::Command, true);
        if (m_scriptSpellId == autoId)
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pal_seal_passive::FilterTargets,
                EFFECT_0, TARGET_UNIT_TARGET_ENEMY);
        else if (m_scriptSpellId == normalizedId)
        {
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pal_seal_passive::FilterTargets,
                EFFECT_0, TARGET_UNIT_TARGET_ENEMY);
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pal_seal_passive::FilterTargets,
                EFFECT_1, TARGET_UNIT_TARGET_ENEMY);
        }
    }
};

// 201093, 201094, 201095 - hidden 20% chance auras linked to Seals of Justice / Light / Wisdom (B1.5)
class spell_pal_seal_chance_aura : public AuraScript
{
    PrepareAuraScript(spell_pal_seal_chance_aura);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_SEAL_OF_JUSTICE_STUN, PaladinData::SPELL_SEAL_OF_LIGHT_HEAL,
            PaladinData::SPELL_SEAL_OF_WISDOM_MANA, PaladinData::SPELL_UNLEASHED_JUSTICE_AOE_STUN,
            PaladinData::SPELL_JUSTICE_RECOVERY });
    }

    Paladin::SealType GetSeal() const
    {
        switch (GetId())
        {
            case PaladinData::SPELL_SEAL_OF_JUSTICE_STUN_CHANCE:
                return Paladin::SealType::Justice;
            case PaladinData::SPELL_SEAL_OF_LIGHT_HEAL_CHANCE:
                return Paladin::SealType::Light;
            case PaladinData::SPELL_SEAL_OF_WISDOM_MANA_CHANCE:
                return Paladin::SealType::Wisdom;
            default:
                return Paladin::SealType::None;
        }
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Player* player = GetPlayerOrNull(GetTarget());
        if (!player) // CR3
            return false;

        // The chance auras are infinite and can reload without their seal (the seal's 10 s can lapse offline)
        if (Paladin::GetActiveSeal(player) != GetSeal())
            return false;

        if (!Paladin::IsSealPassiveSource(player, eventInfo))
            return false;

        if (GetId() != PaladinData::SPELL_SEAL_OF_JUSTICE_STUN_CHANCE)
            return true;

        // Justice: creatures not controlled by a player (R "stun a creature"), never bosses, never stun-immune,
        // never while the 3 s Justice Recovery lockout (any caster) is up (user ruling 2026-10-03, F1)
        Unit* target = eventInfo.GetActionTarget();
        if (!target || !target->IsCreature() || target->IsControlledByPlayer())
            return false;

        if (Paladin::IsBossForStun(target))
            return false;

        SpellInfo const* immunityProbe = sSpellMgr->GetSpellInfo(PaladinData::SPELL_UNLEASHED_JUSTICE_AOE_STUN);
        if (immunityProbe && target->IsImmunedToSpell(immunityProbe, static_cast<Unit const*>(player)))
            return false;

        return !target->HasAura(PaladinData::SPELL_JUSTICE_RECOVERY);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& /*eventInfo*/)
    {
        // Justice keeps its default action: 201096 on the proc target (linked 201106 does the lockout)
        uint32 effectSpell = 0;
        int32 amount = 0;
        Unit* owner = GetTarget();
        if (!owner)
            return;

        switch (GetId())
        {
            case PaladinData::SPELL_SEAL_OF_LIGHT_HEAL_CHANCE:
                effectSpell = PaladinData::SPELL_SEAL_OF_LIGHT_HEAL;
                amount = int32(CalculatePct(owner->GetCreateHealth(), PAL_SEAL_EFFECT_PCT_OF_BASE));
                break;
            case PaladinData::SPELL_SEAL_OF_WISDOM_MANA_CHANCE:
                effectSpell = PaladinData::SPELL_SEAL_OF_WISDOM_MANA;
                amount = int32(CalculatePct(owner->GetCreateMana(), PAL_SEAL_EFFECT_PCT_OF_BASE));
                break;
            default:
                return;
        }

        PreventDefaultAction();
        owner->CastCustomSpell(effectSpell, SPELLVALUE_BASE_POINT0, amount, owner, TRIGGERED_FULL_MASK, nullptr,
            aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_seal_chance_aura::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_pal_seal_chance_aura::HandleProc, EFFECT_0,
            SPELL_AURA_PROC_TRIGGER_SPELL);
    }
};

// 201063-201068 - Primed seal auras (B2.2)
class spell_pal_primed_aura : public AuraScript
{
    PrepareAuraScript(spell_pal_primed_aura);

    uint32 _serial = 0;

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetPlayerOrNull(GetTarget());
        Paladin::SealType const type = SealTypeFromPrimed(GetId());
        if (player && type != Paladin::SealType::None) // CR3: no-op for a non-player owner
            Paladin::OnPrimedApplied(player, type, GetAura(), _serial);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetPlayerOrNull(GetTarget());
        Paladin::SealType const type = SealTypeFromPrimed(GetId());
        if (player && type != Paladin::SealType::None)
            Paladin::OnPrimedRemoved(player, type, _serial); // find-only inside (CR5)
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_primed_aura::HandleApply, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_primed_aura::HandleRemove, EFFECT_0, SPELL_AURA_DUMMY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// Crusader Strike 35395, Divine Storm 53385, Exorcism 879, Hammer of Wrath 24275, Consecration 26573,
// Holy Wrath 2812, Avenger's Shield 31935, Hammer of the Righteous 53595, Holy Shock 20473, Blade of Justice,
// Wake of Ashes - every seal stack builder (B2.3)
class spell_pal_seal_builder : public SpellScript
{
    PrepareSpellScript(spell_pal_seal_builder);

    enum class GrantPath : uint8 { Immediate, Delayed, AtCast, HolyShock };

    bool _hitEnemy = false;
    bool _granted = false;

    GrantPath GetPath()
    {
        SpellInfo const* info = GetSpellInfo();
        if (info->Id == PaladinData::SPELL_CONSECRATION)
            return GrantPath::AtCast;

        if (info->Id == PaladinData::SPELL_HOLY_SHOCK)
            return GrantPath::HolyShock;

        return info->Speed > 0.0f ? GrantPath::Delayed : GrantPath::Immediate;
    }

    void Grant(Player* player)
    {
        if (_granted)
            return;

        _granted = true;
        uint32 const spellId = GetSpellInfo()->Id;
        // Always consume: it also clears a stale Conviction note. AddSealStacks does nothing without an active seal.
        bool const crit = Paladin::ConsumeBuilderCrit(player, spellId);
        Paladin::AddSealStacks(player, Paladin::GetBuilderBaseCount(spellId), spellId, crit);
    }

    void HandleAfterHit()
    {
        Player* player = GetPlayerOrNull(GetCaster()); // CR3
        Unit* target = GetHitUnit();
        if (!player || !target)
            return;

        switch (GetPath())
        {
            case GrantPath::Immediate:
                if (IsEnemyIgnoringDeath(player, target))
                    _hitEnemy = true;
                break;
            case GrantPath::HolyShock:
                _hitEnemy = true; // hostile = enemy hit, friendly = Holy Shock healed someone
                break;
            case GrantPath::Delayed:
                if (!_granted && IsEnemyIgnoringDeath(player, target))
                    Grant(player); // AfterCast runs before the missile lands: grant on the first enemy hit
                break;
            case GrantPath::AtCast:
                break;
        }
    }

    void HandleAfterCast()
    {
        Player* player = GetPlayerOrNull(GetCaster()); // CR3
        if (!player)
            return;

        switch (GetPath())
        {
            case GrantPath::Immediate:
            case GrantPath::HolyShock:
                if (_hitEnemy)
                    Grant(player);
                break;
            case GrantPath::AtCast:
                if (HasEnemyInRange(player))
                    Grant(player);
                break;
            case GrantPath::Delayed:
                break;
        }
    }

    static bool HasEnemyInRange(Player* player)
    {
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(player, player, 8.0f);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(player, nearby, check);
        Cell::VisitObjects(player, searcher, 8.0f);

        for (Unit* unit : nearby)
            if (unit->IsAlive() && player->IsValidAttackTarget(unit) && player->IsWithinLOSInMap(unit))
                return true;

        return false;
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_pal_seal_builder::HandleAfterHit);
        AfterCast += SpellCastFn(spell_pal_seal_builder::HandleAfterCast);
    }
};

// 201060 Judgement, 201061 Deliverance (B3.2)
class spell_pal_judgement_dispatch : public SpellScript
{
    PrepareSpellScript(spell_pal_judgement_dispatch);

    uint32 _serial = 0;
    bool _isPlayerCast = false;
    bool _hasPrimed = false;
    Paladin::SealType _type = Paladin::SealType::None;
    uint8 _stacks = 0;
    std::map<ObjectGuid, bool> _controlled;
    std::vector<ObjectGuid> _hits;
    std::map<ObjectGuid, uint32> _ownHitDamage;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_UNLEASHED_RIGHTEOUSNESS, PaladinData::SPELL_UNLEASHED_COMMAND,
            PaladinData::SPELL_UNLEASHED_VENGEANCE, PaladinData::SPELL_UNLEASHED_JUSTICE,
            PaladinData::SPELL_UNLEASHED_JUSTICE_AOE_STUN, PaladinData::SPELL_UNLEASHED_LIGHT,
            PaladinData::SPELL_UNLEASHED_WISDOM, SPELL_PAL_JUDGEMENT_OF_JUSTICE_DEBUFF,
            SPELL_PAL_JUDGEMENT_OF_LIGHT_DEBUFF, SPELL_PAL_JUDGEMENT_OF_WISDOM_DEBUFF });
    }

    bool IsDeliverance()
    {
        return GetSpellInfo()->Id == PaladinData::SPELL_DELIVERANCE;
    }

    // Deliverance only: explicit target first, the rest by distance to it, at most 5 (step 1)
    void TrimTargets(std::list<WorldObject*>& targets)
    {
        Unit* explicitTarget = GetExplTargetUnit();
        WorldObject* first = nullptr;
        std::vector<WorldObject*> others;
        for (WorldObject* object : targets)
        {
            if (object == explicitTarget)
                first = object;
            else
                others.push_back(object);
        }

        if (explicitTarget)
            std::sort(others.begin(), others.end(), [explicitTarget](WorldObject const* a, WorldObject const* b)
            {
                return explicitTarget->GetDistance(a) < explicitTarget->GetDistance(b);
            });

        targets.clear();
        if (first)
            targets.push_back(first);

        for (WorldObject* object : others)
            targets.push_back(object);

        if (targets.size() > PAL_UNLEASH_MAX_TARGETS)
            targets.resize(PAL_UNLEASH_MAX_TARGETS);
    }

    void HandleBeforeCast()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        if (!player) // CR3: return before any Paladin:: state call
            return;

        _isPlayerCast = true;
        _serial = Paladin::BeginJudgementCast(player);
        _hasPrimed = Paladin::PeekPrimed(player, _type, _stacks); // peek only: castable without Primed (D1)
    }

    void HandleBeforeHit(SpellMissInfo /*missInfo*/)
    {
        if (!_isPlayerCast || !_hasPrimed || _type != Paladin::SealType::Justice)
            return;

        // "Check first, then stun, then damage": the own hit can break an incapacitate
        if (Unit* target = GetHitUnit())
            _controlled[target->GetGUID()] = Paladin::IsControlled(target);
    }

    void HandleAfterHit()
    {
        if (!_isPlayerCast)
            return;

        Unit* target = GetHitUnit();
        if (!target)
            return;

        ObjectGuid const guid = target->GetGUID();
        if (std::find(_hits.begin(), _hits.end(), guid) == _hits.end())
            _hits.push_back(guid);

        _ownHitDamage[guid] = uint32(std::max(0, GetHitDamage()));
    }

    void HandleAfterCast()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        if (!player || !_isPlayerCast)
            return;

        // A cast whose own hit lands on nobody keeps the Primed aura (round-2 Q6) and fires no hook (step 6)
        if (_hits.empty())
            return;

        std::vector<Unit*> targets;
        for (ObjectGuid const& guid : _hits)
            if (Unit* unit = ObjectAccessor::GetUnit(*player, guid)) // dead units stay (killing blows unleash)
                targets.push_back(unit);

        Unit* explicitTarget = GetExplTargetUnit();
        Unit* mainTarget = nullptr;
        if (explicitTarget && std::find(targets.begin(), targets.end(), explicitTarget) != targets.end())
            mainTarget = explicitTarget;
        else if (!targets.empty())
            mainTarget = targets.front();

        bool primedConsumed = false;
        Paladin::SealType consumedType = Paladin::SealType::None;
        uint8 consumedStacks = 0;
        if (_hasPrimed && Paladin::ConsumePrimed(player, consumedType, consumedStacks))
        {
            primedConsumed = true;
            RunUnleash(player, targets, consumedType, consumedStacks);
        }

        Paladin::JudgementCastInfo info{ player, mainTarget, GetSpellInfo()->Id, IsDeliverance(), primedConsumed,
            primedConsumed ? consumedType : Paladin::SealType::None, primedConsumed ? consumedStacks : uint8(0),
                targets };
        Paladin::FireJudgementCastHooks(info);

        // Holy hook (Part A, step 6): once per cast whose own hit landed, main target = explicit target if hit
        ObjectGuid holyGuid = _hits.front();
        if (explicitTarget && std::find(_hits.begin(), _hits.end(), explicitTarget->GetGUID()) != _hits.end())
            holyGuid = explicitTarget->GetGUID();

        Unit* holyTarget = ObjectAccessor::GetUnit(*player, holyGuid);
        auto const damageItr = _ownHitDamage.find(holyGuid);
        Paladin::OnJudgementCastHoly(player, holyTarget, IsDeliverance(), damageItr != _ownHitDamage.end()
            ? damageItr->second : 0);
    }

    // One unleash cast inside its context scope (resolves synchronously, B3.2)
    static void CastUnleash(Player* player, Unit* target, uint32 spellId, Paladin::SealType type, uint8 stacks,
        bool aoe, bool controlled)
    {
        if (!spellId)
            return;

        Paladin::UnleashContextScope scope(player, type, stacks, aoe, controlled);
        player->CastSpell(target, spellId, TRIGGERED_FULL_MASK);
    }

    static int32 PerStackAmount(float perStackPct, uint8 stacks, float effectPct)
    {
        return Paladin::RoundPctAmount(perStackPct * float(stacks) * (1.0f + effectPct / 100.0f));
    }

    static void CastUtility(Player* player, Unit* target, uint32 spellId, int32 amount)
    {
        player->CastCustomSpell(spellId, SPELLVALUE_BASE_POINT0, amount, target, TRIGGERED_FULL_MASK);
    }

    // `hitTargets` keeps units that died to the own hit: caster-side utilities (haste, heal, mana, shield) still
    // apply, while every cast bound to the target (unleash, DoT, stun, debuffs) skips dead units.
    void RunUnleash(Player* player, std::vector<Unit*> const& hitTargets, Paladin::SealType type, uint8 stacks)
    {
        std::vector<Unit*> targets;
        for (Unit* unit : hitTargets)
            if (unit->IsAlive())
                targets.push_back(unit);

        Unit* explicitTarget = GetExplTargetUnit();
        Unit* mainTarget = nullptr;
        if (explicitTarget && std::find(targets.begin(), targets.end(), explicitTarget) != targets.end())
            mainTarget = explicitTarget;
        else if (!targets.empty())
            mainTarget = targets.front();

        bool const aoe = IsDeliverance();
        Paladin::UnleashBonus const bonus = Paladin::GetUnleashBonus(player, type);
        uint32 const unleashId = Paladin::GetUnleashSpell(type, aoe);

        switch (type)
        {
            case Paladin::SealType::Righteousness:
                for (Unit* target : targets)
                    CastUnleash(player, target, unleashId, type, stacks, aoe, false);

                if (stacks)
                    CastUtility(player, player, PaladinData::SPELL_UNLEASHED_RIGHTEOUSNESS,
                        PerStackAmount(PAL_HASTE_PCT_PER_STACK, stacks, bonus.effectPct));
                break;
            case Paladin::SealType::Command:
            {
                int32 const debuff = stacks ? -PerStackAmount(PAL_HASTE_PCT_PER_STACK, stacks, bonus.effectPct) : 0;
                for (Unit* target : targets)
                {
                    CastUnleash(player, target, unleashId, type, stacks, aoe, false);
                    if (debuff)
                        CastUtility(player, target, PaladinData::SPELL_UNLEASHED_COMMAND, debuff);
                }

                if (aoe && mainTarget)
                {
                    // Deliverance of Command: the single-target unleash too on the main target and its 2 closest
                    // hit targets (R test: 5 x 30 + 3 x 75)
                    std::vector<Unit*> closest;
                    for (Unit* target : targets)
                        if (target != mainTarget)
                            closest.push_back(target);

                    std::sort(closest.begin(), closest.end(), [mainTarget](Unit const* a, Unit const* b)
                    {
                        return mainTarget->GetDistance(a) < mainTarget->GetDistance(b);
                    });

                    uint32 const singleId = Paladin::GetUnleashSpell(type, false);
                    CastUnleash(player, mainTarget, singleId, type, stacks, aoe, false);
                    for (size_t i = 0; i < closest.size() && i < PAL_COMMAND_EXTRA_UNLEASHES; ++i)
                        CastUnleash(player, closest[i], singleId, type, stacks, aoe, false);
                }
                break;
            }
            case Paladin::SealType::Vengeance:
            {
                for (Unit* target : targets)
                    CastUnleash(player, target, unleashId, type, stacks, aoe, false);

                // 20% of the main target's DoT total; Deliverance's is a 40% DoT, so divide back to Judgement strength
                AuraEffect const* dot = mainTarget ?
                    mainTarget->GetAuraEffect(unleashId, EFFECT_0, player->GetGUID()) : nullptr;
                if (dot && dot->GetAmplitude() > 0)
                {
                    float const ticks = float(dot->GetBase()->GetMaxDuration()) / float(dot->GetAmplitude());
                    float shield = PAL_VENGEANCE_SHIELD_PCT * float(dot->GetAmount()) * ticks;
                    if (aoe)
                        shield /= PAL_DELIVERANCE_DOT_SCALE;

                    CastUtility(player, player, PaladinData::SPELL_UNLEASHED_VENGEANCE, int32(shield));
                }
                break;
            }
            case Paladin::SealType::Justice:
                for (Unit* target : targets)
                {
                    // Bosses skip the stun only; damage still doubles if they were already controlled
                    if (!Paladin::IsBossForStun(target))
                        player->CastSpell(target, aoe ? PaladinData::SPELL_UNLEASHED_JUSTICE_AOE_STUN
                            : PaladinData::SPELL_UNLEASHED_JUSTICE, TRIGGERED_FULL_MASK);

                    auto const itr = _controlled.find(target->GetGUID());
                    bool const controlled = itr != _controlled.end() && itr->second;
                    CastUnleash(player, target, unleashId, type, stacks, aoe, controlled);
                    player->CastSpell(target, SPELL_PAL_JUDGEMENT_OF_JUSTICE_DEBUFF, TRIGGERED_FULL_MASK);
                }
                break;
            case Paladin::SealType::Light:
                for (Unit* target : targets)
                    player->CastSpell(target, SPELL_PAL_JUDGEMENT_OF_LIGHT_DEBUFF, TRIGGERED_FULL_MASK);

                // Effects on the caster happen once, at full value (the heal's Judgement-strength is the id's own)
                CastUnleash(player, player, unleashId, type, stacks, aoe, false);
                if (stacks)
                    CastUtility(player, player, PaladinData::SPELL_UNLEASHED_LIGHT,
                        Paladin::RoundPctAmount(float(stacks) * (PAL_LIGHT_DAMAGE_PCT_PER_STACK
                            + bonus.lightPerStackPct)));
                break;
            case Paladin::SealType::Wisdom:
                for (Unit* target : targets)
                {
                    CastUnleash(player, target, unleashId, type, stacks, aoe, false);
                    player->CastSpell(target, SPELL_PAL_JUDGEMENT_OF_WISDOM_DEBUFF, TRIGGERED_FULL_MASK);
                }

                // Mana is a 5 s periodic restore of base mana that does not scale with stacks (only the damage does)
                CastUtility(player, player, PaladinData::SPELL_UNLEASHED_WISDOM,
                    int32(CalculatePct(player->GetCreateMana(),
                        PAL_WISDOM_MANA_PCT_PER_TICK * (1.0f + bonus.effectPct / 100.0f))));
                break;
            default:
                break;
        }
    }

    void Register() override
    {
        if (m_scriptSpellId == PaladinData::SPELL_DELIVERANCE)
            OnObjectAreaTargetSelect += SpellObjectAreaTargetSelectFn(spell_pal_judgement_dispatch::TrimTargets,
                EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY);

        BeforeCast += SpellCastFn(spell_pal_judgement_dispatch::HandleBeforeCast);
        BeforeHit += BeforeSpellHitFn(spell_pal_judgement_dispatch::HandleBeforeHit);
        AfterHit += SpellHitFn(spell_pal_judgement_dispatch::HandleAfterHit);
        AfterCast += SpellCastFn(spell_pal_judgement_dispatch::HandleAfterCast);
    }
};

// 201069-201080 - Judgement / Deliverance unleashes (B4.1): the SpellScript scales direct damage and heals,
// the AuraScript scales the Vengeance DoTs (registered as a pair under one script name)
class spell_pal_seal_unleash : public SpellScript
{
    PrepareSpellScript(spell_pal_seal_unleash);

    static bool IsDot(uint32 spellId)
    {
        return spellId == Paladin::GetUnleashSpell(Paladin::SealType::Vengeance, false) ||
            spellId == Paladin::GetUnleashSpell(Paladin::SealType::Vengeance, true);
    }

    static bool IsHeal(uint32 spellId)
    {
        return spellId == Paladin::GetUnleashSpell(Paladin::SealType::Light, false) ||
            spellId == Paladin::GetUnleashSpell(Paladin::SealType::Light, true);
    }

    void HandleHit()
    {
        uint32 const spellId = GetSpellInfo()->Id;
        if (IsDot(spellId))
            return;

        Player* player = GetPlayerOrNull(GetCaster());
        if (!player)
            return; // no context: x1 (CR3)

        Paladin::UnleashContext const* context = Paladin::GetUnleashContext(player);
        if (!context)
        {
            // A GM cast has no dispatcher; a missile-visual unleash would land here silently (B8 risk "synchronous
            // cast")
            LOG_DEBUG("spells", "spell_pal_seal_unleash: spell {} cast by player without an unleash context (x1)",
                spellId);
            return;
        }

        float const multiplier = Paladin::GetUnleashMultiplier(player, *context);
        if (IsHeal(spellId))
            SetHitHeal(int32(float(GetHitHeal()) * multiplier));
        else
            SetHitDamage(int32(float(GetHitDamage()) * multiplier));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pal_seal_unleash::HandleHit);
    }
};

class spell_pal_seal_unleash_aura : public AuraScript
{
    PrepareAuraScript(spell_pal_seal_unleash_aura);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        // A later RecalculateAmount has no unleash context, so the first (in-cast) calculation is final
        canBeRecalculated = false;

        Player* player = GetPlayerOrNull(GetCaster());
        if (!player)
            return;

        if (Paladin::UnleashContext const* context = Paladin::GetUnleashContext(player))
            amount = int32(float(amount) * Paladin::GetUnleashMultiplier(player, *context));
    }

    void Register() override
    {
        uint32 const stId = Paladin::GetUnleashSpell(Paladin::SealType::Vengeance, false);
        uint32 const aoeId = Paladin::GetUnleashSpell(Paladin::SealType::Vengeance, true);
        if (m_scriptSpellId == stId || m_scriptSpellId == aoeId)
            DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_seal_unleash_aura::CalculateAmount, EFFECT_0,
                SPELL_AURA_PERIODIC_DAMAGE);
    }
};

// 20185, 20186 - Judgement of Light / Wisdom debuffs: the stock 15 PPM roll without Proc Chance (B11)
class spell_pal_judgement_debuff_proc_rate : public AuraScript
{
    PrepareAuraScript(spell_pal_judgement_debuff_proc_rate);

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        // The spell_proc row is chance 100 (Proc Chance multiplies it); the real roll is re-done here as
        // Aura::CalcProcChance does for a PPM row, minus the Proc Chance factor.
        if (!eventInfo.GetDamageInfo() && !eventInfo.GetHealInfo())
            return true;

        Unit* caster = GetCaster();
        if (!caster)
            return true;

        SpellInfo const* procSpell = eventInfo.GetSpellInfo();
        uint32 attackSpeed = 0;
        if (!procSpell || procSpell->DmgClass == SPELL_DAMAGE_CLASS_MELEE || procSpell->IsRangedWeaponSpell())
        {
            DamageInfo const* damageInfo = eventInfo.GetDamageInfo();
            attackSpeed = caster->GetAttackTime(damageInfo ? damageInfo->GetAttackType() : BASE_ATTACK);
        }
        else
        {
            if (procSpell->CastTimeEntry)
                attackSpeed = procSpell->CastTimeEntry->CastTime;

            // instants and fast spells use 1.5 s
            if (attackSpeed < 1500)
                attackSpeed = 1500;
        }

        float chance = caster->GetPPMProcChance(attackSpeed, float(PAL_BATTLE_SPEED_PPM), GetSpellInfo());
        if (Player* modOwner = caster->GetSpellModOwner())
            modOwner->ApplySpellMod(GetId(), SPELLMOD_CHANCE_OF_SUCCESS, chance);

        return roll_chance_f(chance);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_pal_judgement_debuff_proc_rate::CheckProc);
    }
};

// ===========================================================================================
// SHARED Part B: class-wide baseline
// ===========================================================================================

// 26573 - Consecration (B5.6a): snapshot at cast, Rain of Fire pattern (spell_warlock_destruction.cpp)
class spell_pal_consecration : public SpellScript
{
    PrepareSpellScript(spell_pal_consecration);

    void RemoveExisting()
    {
        // One Consecration per caster: a recast tears down the earlier ground effect first
        Unit* caster = GetCaster();
        if (!caster)
            return;

        caster->RemoveDynObject(PaladinData::SPELL_CONSECRATION);
        caster->RemoveAurasDueToSpell(PaladinData::SPELL_CONSECRATION, caster->GetGUID());
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_pal_consecration::RemoveExisting);
    }
};

class spell_pal_consecration_aura : public AuraScript
{
    PrepareAuraScript(spell_pal_consecration_aura);

    int32 _snapshot = 0;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_CONSECRATION_TICK });
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        // DOT, not DIRECT: a hybrid periodic row only fills the dot / ap_dot bonus (Unit.cpp:8652-8676), and talents
        // scoping Consecration use SPELLMOD_DOT
        SpellInfo const* info = GetSpellInfo();
        int32 const base = info->Effects[EFFECT_0].CalcValue(caster);
        _snapshot = int32(caster->SpellDamageBonusDone(caster, info, uint32(std::max(0, base)), DOT, EFFECT_0));

        // Consecration-applied hooks (Prot's Improved Consecration): once per cast, after the snapshot is stored.
        // The dynobj already exists (Spell.cpp: the dest effect runs before the caster aura is applied).
        if (DynamicObject* dynObj = caster->GetDynObject(PaladinData::SPELL_CONSECRATION))
            Paladin::FireConsecrationAppliedHooks(caster, dynObj, _snapshot);
    }

    void HandlePeriodic(AuraEffect const* aurEff)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        DynamicObject* dynObj = caster->GetDynObject(PaladinData::SPELL_CONSECRATION);
        if (!dynObj)
            return;

        SpellInfo const* tickInfo = sSpellMgr->GetSpellInfo(PaladinData::SPELL_CONSECRATION_TICK);
        if (!tickInfo)
            return;

        SpellCastTargets targets;
        targets.SetDst(*dynObj);

        CustomSpellValues values;
        values.AddSpellMod(SPELLVALUE_BASE_POINT0, int32(float(_snapshot) * aurEff->GetFinalTickBonusMultiplier()));

        caster->CastSpell(targets, tickInfo, &values, TRIGGERED_FULL_MASK, nullptr, aurEff);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        if (Unit* caster = GetCaster())
            caster->RemoveDynObject(PaladinData::SPELL_CONSECRATION);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_pal_consecration_aura::HandleApply, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
        OnEffectPeriodic += AuraEffectPeriodicFn(spell_pal_consecration_aura::HandlePeriodic, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY);
        AfterEffectRemove += AuraEffectRemoveFn(spell_pal_consecration_aura::HandleRemove, EFFECT_1,
            SPELL_AURA_PERIODIC_DUMMY, AURA_EFFECT_HANDLE_REAL);
    }
};

// 2812 - Holy Wrath (B5.7): double damage against Demons and Undead, plus the stun helper
class spell_pal_holy_wrath : public SpellScript
{
    PrepareSpellScript(spell_pal_holy_wrath);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_HOLY_WRATH_STUN });
    }

    void HandleHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target)
            return;

        uint32 const creatureType = target->GetCreatureType();
        if (creatureType != CREATURE_TYPE_DEMON && creatureType != CREATURE_TYPE_UNDEAD)
            return;

        SetHitDamage(GetHitDamage() * 2);
        caster->CastSpell(target, PaladinData::SPELL_HOLY_WRATH_STUN, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_pal_holy_wrath::HandleHit);
    }
};

// 58597 - Sacred Shield (absorb) (B5.11): stock body, the 75% literal replaced by the generated coefficient
class spell_pal_sacred_shield_absorb : public AuraScript
{
    PrepareAuraScript(spell_pal_sacred_shield_absorb);

    void CalculateAmount(AuraEffect const* aurEff, int32& amount, bool& /*canBeRecalculated*/)
    {
        Unit* caster = GetCaster();
        if (!caster)
            return;

        // SCHOOL_ABSORB gets no engine spell-power bonus, so this is the only place the coefficient is applied
        amount += Paladin::CalculateAbsorbBonus(caster, aurEff, amount); // returns the bonus only

        // Arena - Dampening
        if (AuraEffect const* auraEffArenaDampening = caster->GetAuraEffect(SPELL_PAL_ARENA_DAMPENING, EFFECT_0))
            AddPct(amount, auraEffArenaDampening->GetAmount());
        // Battleground - Dampening
        else if (AuraEffect const* auraEffBattlegroundDampening = caster->GetAuraEffect(
            SPELL_PAL_BATTLEGROUND_DAMPENING, EFFECT_0))
            AddPct(amount, auraEffBattlegroundDampening->GetAmount());

        // ICC buff
        if (AuraEffect const* auraStrengthOfWrynn = caster->GetAuraEffect(SPELL_AURA_MOD_HEALING_DONE_PERCENT,
            SPELLFAMILY_GENERIC, PAL_SPELL_ICON_STRENGTH_OF_WRYNN, EFFECT_2))
            AddPct(amount, auraStrengthOfWrynn->GetAmount());
        else if (AuraEffect const* auraHellscreamsWarsong = caster->GetAuraEffect(
            SPELL_AURA_MOD_HEALING_DONE_PERCENT, SPELLFAMILY_GENERIC, PAL_SPELL_ICON_HELLSCREAM_WARSONG, EFFECT_2))
            AddPct(amount, auraHellscreamsWarsong->GetAmount());
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_sacred_shield_absorb::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// ===========================================================================================
// SHARED Part C: aura system and class-wide baseline
// ===========================================================================================

namespace
{
    // Aura button -> its burst (C1.6)
    uint32 GetAuraBurstSpell(uint32 auraId)
    {
        switch (auraId)
        {
            case PaladinData::SPELL_DEVOTION_AURA:
                return PaladinData::SPELL_DEVOTION_BURST;
            case PaladinData::SPELL_RETRIBUTION_AURA:
                return PaladinData::SPELL_RETRIBUTION_BURST;
            case PaladinData::SPELL_CONCENTRATION_AURA:
                return PaladinData::SPELL_CONCENTRATION_BURST;
            case PaladinData::SPELL_RESISTANCE_AURA:
                return PaladinData::SPELL_RESISTANCE_BURST;
            case PaladinData::SPELL_CRUSADER_AURA:
                return PaladinData::SPELL_CRUSADER_BURST;
            default:
                return 0;
        }
    }

    constexpr std::array<uint32, 5> PALADIN_AURA_BUTTONS =
    {
        PaladinData::SPELL_DEVOTION_AURA, PaladinData::SPELL_RETRIBUTION_AURA, PaladinData::SPELL_CONCENTRATION_AURA,
        PaladinData::SPELL_RESISTANCE_AURA, PaladinData::SPELL_CRUSADER_AURA
    };
}

// 465, 7294, 19746, 19876, 32223 - pressing an aura also fires its 10 s raid burst (C1.6)
class spell_pal_aura_press : public SpellScript
{
    PrepareSpellScript(spell_pal_aura_press);

    static constexpr size_t OTHER_AURAS = PALADIN_AURA_BUTTONS.size() - 1;

    std::array<uint32, OTHER_AURAS> _otherIds = { };
    std::array<uint32, OTHER_AURAS> _otherEnds = { };
    bool _active = false;

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ PaladinData::SPELL_RETRIBUTION_BURST, PaladinData::SPELL_DEVOTION_BURST,
            PaladinData::SPELL_RESISTANCE_BURST, PaladinData::SPELL_CRUSADER_BURST,
                PaladinData::SPELL_CONCENTRATION_BURST });
    }

    void RecordCooldowns()
    {
        Player* player = GetPlayerOrNull(GetCaster()); // CR3: NPC 1260's Devotion Aura gets no burst
        if (!player || GetSpell()->IsTriggered())
            return;

        _active = true;

        // The category-1300 write overwrites each sibling's own 60 s with 15 s (Player.cpp _AddSpellCooldown), so
        // remember when each one would have ended and restore any longer cooldown after the press (QC7)
        uint32 const now = uint32(GameTime::GetGameTimeMS().count());
        size_t slot = 0;
        for (uint32 auraId : PALADIN_AURA_BUTTONS)
        {
            if (auraId == GetSpellInfo()->Id)
                continue;

            _otherIds[slot] = auraId;
            _otherEnds[slot] = now + player->GetSpellCooldownDelay(auraId);
            ++slot;
        }
    }

    void FireBurst()
    {
        Player* player = GetPlayerOrNull(GetCaster());
        if (!player || !_active)
            return;

        if (uint32 const burstId = GetAuraBurstSpell(GetSpellInfo()->Id))
            player->CastSpell(player, burstId, TRIGGERED_FULL_MASK);

        // One tick later (the Cooldown Haste block's deferral and reason, Player.cpp): the category write has
        // happened by then. Capturing the player is safe, m_Events dies with it.
        std::array<uint32, OTHER_AURAS> const ids = _otherIds;
        std::array<uint32, OTHER_AURAS> const ends = _otherEnds;
        player->m_Events.AddEventAtOffset([player, ids, ends]()
        {
            uint32 const now = uint32(GameTime::GetGameTimeMS().count());
            for (size_t i = 0; i < ids.size(); ++i)
            {
                int32 const delta = int32(ends[i] - now) - int32(player->GetSpellCooldownDelay(ids[i]));
                if (delta > 0)
                    player->ModifySpellCooldown(ids[i], delta);
            }

            // The restore above and the pressed aura's Cooldown Haste correction (queued earlier, so it runs
            // first) clear-then-set via SMSG_CLEAR_COOLDOWN, which also drops the client's category-1300
            // lock on the other buttons. Re-announce every sibling's server-side cooldown so the client's
            // shared-cooldown sweep matches the server again.
            PacketCooldowns cooldowns;
            for (uint32 auraId : ids)
                if (uint32 const remaining = player->GetSpellCooldownDelay(auraId))
                    cooldowns[auraId] = remaining;

            if (!cooldowns.empty())
            {
                WorldPacket data;
                player->BuildCooldownPacket(data, SPELL_COOLDOWN_FLAG_NONE, cooldowns);
                player->SendDirectMessage(&data);
            }
        }, 1ms);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_pal_aura_press::RecordCooldowns);
        AfterCast += SpellCastFn(spell_pal_aura_press::FireBurst);
    }
};

// 19746 - Concentration Aura: the area aura's hundredths-of-a-percent amount becomes mana per 5 s (C1.3)
class spell_pal_concentration_aura : public AuraScript
{
    PrepareAuraScript(spell_pal_concentration_aura);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = true;

        // Scales the incoming amount (it already carries SPELLMOD_EFFECT1 via CalcValue), never overwrites it
        Unit* caster = GetCaster();
        amount = caster ? int32(int64(caster->GetCreateMana()) * amount / 10000) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_concentration_aura::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_POWER_REGEN);
    }
};

// 201164 - Concentration Burst: hundredths of a percent of each target's maximum mana per 5 s (C1.4)
class spell_pal_concentration_burst : public AuraScript
{
    PrepareAuraScript(spell_pal_concentration_burst);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;

        Unit* owner = GetUnitOwner();
        amount = owner ? int32(int64(owner->GetMaxPower(POWER_MANA)) * amount / 10000) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_concentration_burst::CalculateAmount, EFFECT_0,
            SPELL_AURA_MOD_POWER_REGEN);
    }
};

// 201162 - Resistance Burst: absorbs magic damage equal to a percent of each target's maximum health (C1.4)
class spell_pal_resistance_burst : public AuraScript
{
    PrepareAuraScript(spell_pal_resistance_burst);

    void CalculateAmount(AuraEffect const* /*aurEff*/, int32& amount, bool& canBeRecalculated)
    {
        canBeRecalculated = false;

        Unit* owner = GetUnitOwner();
        amount = owner ? int32(CalculatePct(owner->GetMaxHealth(), amount)) : 0;
    }

    void Register() override
    {
        DoEffectCalcAmount += AuraEffectCalcAmountFn(spell_pal_resistance_burst::CalculateAmount, EFFECT_0,
            SPELL_AURA_SCHOOL_ABSORB);
    }
};

// -633 - Lay on Hands: fork of stock spell_pal_lay_on_hands without the Forbearance / marker flow (C2.1)
class spell_pal_lay_on_hands_fork : public SpellScript
{
    PrepareSpellScript(spell_pal_lay_on_hands_fork);

    int32 _manaAmount = 0;

    void HandleMaxHealthHeal(SpellEffIndex /*effIndex*/)
    {
        Unit* caster = GetCaster();
        Unit* target = GetExplTargetUnit();
        if (!target || !caster)
            return;

        uint32 const baseHeal = caster->GetMaxHealth();
        uint32 const modifiedHeal = target->SpellHealingBonusTaken(caster, GetSpellInfo(), baseHeal, HEAL);

        // EffectHealMaxHealth() ignores healing modifiers, so pre-apply the difference; it is added on top of the
        // raw heal (Beacon of Light copies the right amount)
        int64 const healAdjustment = int64(modifiedHeal) - int64(baseHeal);
        SetHitHeal(int32(healAdjustment));
    }

    SpellCastResult CheckCast()
    {
        // Glyph of Divinity: remember the target's mana before the heal
        if (Unit* target = GetExplTargetUnit())
            if (target->HasActivePowerType(POWER_MANA))
                _manaAmount = int32(target->GetPower(POWER_MANA));

        return SPELL_CAST_OK;
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        // Stock test kept verbatim: "excluding first rank" never fires on this single-rank fork, as today
        if (caster && target && caster != target && caster->HasAura(SPELL_PAL_GLYPH_OF_DIVINITY)
            && GetSpellInfo()->Id != 633 && _manaAmount > 0)
        {
            _manaAmount = int32(target->GetPower(POWER_MANA)) - _manaAmount;
            if (_manaAmount > 0)
                caster->CastCustomSpell(SPELL_PAL_ENERGIZE_GLYPH_OF_DIVINITY, SPELLVALUE_BASE_POINT1, _manaAmount,
                    caster, true);
        }
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_pal_lay_on_hands_fork::CheckCast);
        AfterHit += SpellHitFn(spell_pal_lay_on_hands_fork::HandleAfterHit);
        OnEffectHitTarget += SpellEffectFn(spell_pal_lay_on_hands_fork::HandleMaxHealthHeal, EFFECT_0,
            SPELL_EFFECT_HEAL_MAX_HEALTH);
    }
};

void AddSC_paladin_seal_spell_scripts()
{
    // SHARED Part B
    RegisterSpellAndAuraScriptPairWithArgs(spell_pal_seal_recast, spell_pal_seal_aura, "spell_pal_seal_aura");
    RegisterSpellScript(spell_pal_seal_passive);
    RegisterSpellScript(spell_pal_seal_chance_aura);
    RegisterSpellScript(spell_pal_primed_aura);
    RegisterSpellScript(spell_pal_seal_builder);
    RegisterSpellScript(spell_pal_judgement_dispatch);
    RegisterSpellAndAuraScriptPair(spell_pal_seal_unleash, spell_pal_seal_unleash_aura);
    RegisterSpellScript(spell_pal_judgement_debuff_proc_rate);
    RegisterSpellAndAuraScriptPair(spell_pal_consecration, spell_pal_consecration_aura);
    RegisterSpellScript(spell_pal_holy_wrath);
    RegisterSpellScript(spell_pal_sacred_shield_absorb);

    // SHARED Part C
    RegisterSpellScript(spell_pal_aura_press);
    RegisterSpellScript(spell_pal_concentration_aura);
    RegisterSpellScript(spell_pal_concentration_burst);
    RegisterSpellScript(spell_pal_resistance_burst);
    RegisterSpellScript(spell_pal_lay_on_hands_fork);
}
