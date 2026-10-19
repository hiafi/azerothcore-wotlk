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
 * Shaman rework - shared baseline spell scripts (shaman-rework SH0a, shared doc "Imbues" to "Air Attunement").
 * The five imbue auras and their children, the imbue proc scripts (Flametongue, Frostbrand, Windfury, Earthliving),
 * Stoneskin grants and the Earth / Fire attunement children. Ids come from ShamanData:: (via ShamanMechanics.h);
 * the stock-id header names (SPELL_ROCKBITER_WEAPON, ...) are the stock rows, the new SH0a rows are the
 * suffixed SPELL_STONESKIN_202206 and SPELL_FROSTBRAND_ATTACK_202203 (the lower stock id owns the short name).
 */

#include "Player.h"
#include "ScriptMgr.h"
#include "ShamanMechanics.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"

namespace
{
    // Stock Maelstrom Weapon buff (the cumulative stack Frostbrand grants); no DSL variable names it
    constexpr uint32 SPELL_MAELSTROM_WEAPON_BUFF = 53817;

    // Earthliving's flat chance (shared doc "Earthliving": 20%), before the owner's Proc Chance
    constexpr float EARTHLIVING_CHANCE_PCT = 20.0f;

    // Windfury Attack's bonus: +20% of attack power per attack (U7), normalized the way weapon damage is
    // (AP / 14 per second of the hitting weapon's speed)
    constexpr float WINDFURY_AP_BONUS = 0.2f;

    // Which hand a melee proc event came from. Auto attacks and melee spells (Lava Lash, Stormstrike's off-hand
    // strike) both carry the hand flag (Unit.cpp GetProcFlagsForAttack / Spell::prepareDataForTriggerSystem).
    WeaponAttackType GetProcHand(ProcEventInfo const& eventInfo)
    {
        return (eventInfo.GetTypeMask() & PROC_FLAG_DONE_OFFHAND_ATTACK) ? OFF_ATTACK : BASE_ATTACK;
    }
}

// 8017 Rockbiter, 8024 Flametongue, 8033 Frostbrand, 8232 Windfury, 51730 Earthliving - the imbue self auras.
// Draws the weapon glow, applies the hidden child (Rockbiter: crit immunity and Earth Shock threat; Frostbrand: its
// proc child) and, when Rockbiter ends, strips Stoneskin ("Exists only while Rockbiter is active").
class spell_sha_imbue : public AuraScript
{
    PrepareAuraScript(spell_sha_imbue);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_ROCKBITER_TANK, ShamanData::SPELL_FROSTBRAND_PROC,
            ShamanData::SPELL_STONESKIN_202206 });
    }

    uint32 GetChildSpell() const
    {
        switch (GetId())
        {
            case ShamanData::SPELL_ROCKBITER_WEAPON:
                return ShamanData::SPELL_ROCKBITER_TANK;
            case ShamanData::SPELL_FROSTBRAND_WEAPON:
                return ShamanData::SPELL_FROSTBRAND_PROC;
            default:
                return 0;
        }
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (uint32 const child = GetChildSpell())
            target->CastSpell(target, child, true);

        // Players only: an NPC casting an imbue has no weapon slots to draw on
        if (Player* player = target->ToPlayer())
            Shaman::ApplyImbueGlow(player);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (uint32 const child = GetChildSpell())
            target->RemoveAurasDueToSpell(child);

        if (GetId() == ShamanData::SPELL_ROCKBITER_WEAPON)
            target->RemoveAurasDueToSpell(ShamanData::SPELL_STONESKIN_202206);

        // The aura is already gone from the unit here, so the restore redraws the real values or the new imbue's glow
        if (Player* player = target->ToPlayer())
            Shaman::RestoreImbueGlow(player);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_imbue::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_imbue::HandleRemove, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

// 8024 Flametongue - every melee hit of either hand casts Flametongue Attack. The hitting hand's speed (ms) rides on
// effect 1's base points; spell_sha_flametongue_attack scales the hit by it (WP brief, "speed carrier").
class spell_sha_flametongue_proc : public AuraScript
{
    PrepareAuraScript(spell_sha_flametongue_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FLAMETONGUE_ATTACK });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer() || !Shaman::IsOwnAction(owner, eventInfo.GetActor()))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        return target && target->IsAlive();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        Unit* target = eventInfo.GetActionTarget();
        if (!player || !target)
            return;

        int32 const speedMs = int32(player->GetAttackTime(GetProcHand(eventInfo)));
        player->CastCustomSpell(ShamanData::SPELL_FLAMETONGUE_ATTACK, SPELLVALUE_BASE_POINT1, speedMs, target, true,
            nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_flametongue_proc::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sha_flametongue_proc::HandleProc, EFFECT_1, SPELL_AURA_DUMMY);
    }
};

// Flametongue Attack - scales the hit by the hitting weapon's speed in seconds (ms from effect 1's base points, set
// by the proc above; 1000 ms leaves the hit unchanged). Runs in OnHit, after launch computed the whole hit (base and
// spell power part) and before crit and mitigation.
class spell_sha_flametongue_attack : public SpellScript
{
    PrepareSpellScript(spell_sha_flametongue_attack);

    void HandleOnHit()
    {
        SpellValue const* spellValue = GetSpellValue();
        if (!spellValue)
            return;

        // SetSpellValue stores CalcBaseValue(value): value - 1 when the effect has die sides
        int32 speedMs = spellValue->EffectBasePoints[EFFECT_1];
        if (GetSpellInfo()->Effects[EFFECT_1].DieSides)
            ++speedMs;

        int32 const damage = GetHitDamage();
        if (speedMs <= 0 || damage <= 0)
            return;

        SetHitDamage(int32(int64(damage) * speedMs / 1000));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_sha_flametongue_attack::HandleOnHit);
    }
};

// 202201 Frostbrand's proc child (15% in spell_proc, native Proc Chance) - Frostbrand Attack, plus one Maelstrom
// Weapon stack when the shaman has the talent.
class spell_sha_frostbrand_proc : public AuraScript
{
    PrepareAuraScript(spell_sha_frostbrand_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FROSTBRAND_ATTACK_202203, SPELL_MAELSTROM_WEAPON_BUFF });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer() || !Shaman::IsOwnAction(owner, eventInfo.GetActor()))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        return target && target->IsAlive();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        Unit* target = eventInfo.GetActionTarget();
        if (!player || !target)
            return;

        player->CastSpell(target, ShamanData::SPELL_FROSTBRAND_ATTACK_202203, true, nullptr, aurEff);

        if (Shaman::HasMaelstromWeaponTalent(player))
            player->CastSpell(player, SPELL_MAELSTROM_WEAPON_BUFF, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_frostbrand_proc::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sha_frostbrand_proc::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 8232 Windfury - 20% on a melee hit of either hand (spell_proc, native Proc Chance, no cooldown): two Windfury
// Attacks on the hit's hand (the off-hand copy for an off-hand hit).
class spell_sha_windfury_proc : public AuraScript
{
    PrepareAuraScript(spell_sha_windfury_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_WINDFURY_ATTACK_MH, ShamanData::SPELL_WINDFURY_ATTACK_OH });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer() || !Shaman::IsOwnAction(owner, eventInfo.GetActor()))
            return false;

        Unit* target = eventInfo.GetActionTarget();
        return target && target->IsAlive();
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Player* player = GetUnitOwner() ? GetUnitOwner()->ToPlayer() : nullptr;
        Unit* target = eventInfo.GetActionTarget();
        if (!player || !target)
            return;

        uint32 const attackId = GetProcHand(eventInfo) == OFF_ATTACK ? ShamanData::SPELL_WINDFURY_ATTACK_OH
            : ShamanData::SPELL_WINDFURY_ATTACK_MH;

        for (uint8 i = 0; i < 2; ++i)
            player->CastSpell(target, attackId, true, nullptr, aurEff);
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_windfury_proc::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sha_windfury_proc::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// Windfury Attack (main hand and off hand) - adds +20% of attack power to the swing (AP / 14 per second of that
// weapon's speed, the way weapon damage normalizes it). Stock puts a bonus like this in the weapon-damage effect
// and then runs the whole sum through the melee done / taken bonuses; the weapon-percent effect here has no flat
// slot, so the bonus gets the same total-percent, done and taken treatment in OnHit, before crit and armor.
class spell_sha_windfury_attack : public SpellScript
{
    PrepareSpellScript(spell_sha_windfury_attack);

    void HandleOnHit()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!caster || !target || GetHitDamage() <= 0)
            return;

        bool const offHand = GetSpellInfo()->Id == ShamanData::SPELL_WINDFURY_ATTACK_OH;
        WeaponAttackType const attType = offHand ? OFF_ATTACK : BASE_ATTACK;

        float bonus = caster->GetTotalAttackPowerValue(attType) * WINDFURY_AP_BONUS / 14.0f *
            (float(caster->GetAttackTime(attType)) / 1000.0f);
        bonus *= caster->GetPctModifierValue(offHand ? UNIT_MOD_DAMAGE_OFFHAND : UNIT_MOD_DAMAGE_MAINHAND, TOTAL_PCT);

        SpellSchoolMask const school = GetSpellInfo()->GetSchoolMask();
        uint32 extra = caster->MeleeDamageBonusDone(target, uint32(std::max(bonus, 0.0f)), attType, GetSpellInfo(),
            school);
        extra = target->MeleeDamageBonusTaken(caster, extra, attType, GetSpellInfo(), school);

        SetHitDamage(GetHitDamage() + int32(extra));
    }

    void Register() override
    {
        OnHit += SpellHitFn(spell_sha_windfury_attack::HandleOnHit);
    }
};

// 51730 Earthliving - 20% (scripted roll, Proc Chance applies) on a direct heal the shaman casts, once per target
// healed (each Chain Heal target is its own event): the Earthliving HoT from the shaman, snapshotting at apply.
// Periodic, totem, pet and triggered heals never reach the roll (periodic flag, actor guard, no TRIGGERED_CAN_PROC).
class spell_sha_earthliving_proc : public AuraScript
{
    PrepareAuraScript(spell_sha_earthliving_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTHLIVING });
    }

    bool CheckProc(ProcEventInfo& eventInfo)
    {
        Unit* owner = GetUnitOwner();
        if (!owner || !owner->IsPlayer() || !Shaman::IsOwnAction(owner, eventInfo.GetActor()))
            return false;

        if (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC)
            return false;

        if (!eventInfo.GetHealInfo())
            return false;

        Unit* target = eventInfo.GetActionTarget();
        if (!target || !target->IsAlive())
            return false;

        return Shaman::RollProcChance(owner, EARTHLIVING_CHANCE_PCT);
    }

    void HandleProc(AuraEffect const* aurEff, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();

        Unit* owner = GetUnitOwner();
        Unit* target = eventInfo.GetActionTarget();
        if (!owner || !target)
            return;

        owner->CastSpell(target, ShamanData::SPELL_EARTHLIVING, true, nullptr, aurEff, owner->GetGUID());
    }

    void Register() override
    {
        DoCheckProc += AuraCheckProcFn(spell_sha_earthliving_proc::CheckProc);
        OnEffectProc += AuraEffectProcFn(spell_sha_earthliving_proc::HandleProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// 8042 Earth Shock, 421 Chain Lightning, 17364 Stormstrike, 60103 Lava Lash - Stoneskin grants, only under
// Rockbiter. Earth Shock grants once per cast even if it hits several, Chain Lightning once per target hit,
// Stormstrike and Lava Lash on their hit. NPCs cast 421 and 8042 too, so the caster must be a player.
class spell_sha_stoneskin_grant : public SpellScript
{
    PrepareSpellScript(spell_sha_stoneskin_grant);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_STONESKIN_202206 });
    }

    uint32 GetStacks()
    {
        switch (GetSpellInfo()->Id)
        {
            case ShamanData::SPELL_EARTH_SHOCK:
                return ShamanData::STONESKIN_EARTH_SHOCK;
            case ShamanData::SPELL_CHAIN_LIGHTNING:
                return ShamanData::STONESKIN_CHAIN_LIGHTNING;
            case ShamanData::SPELL_STORMSTRIKE:
                return ShamanData::STONESKIN_STORMSTRIKE;
            case ShamanData::SPELL_LAVA_LASH:
                return ShamanData::STONESKIN_LAVA_LASH;
            default:
                return 0;
        }
    }

    void HandleAfterHit()
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player)
            return;

        // Only Chain Lightning grants per target; the others once per cast
        bool const perTarget = GetSpellInfo()->Id == ShamanData::SPELL_CHAIN_LIGHTNING;
        if (!perTarget && _granted)
            return;

        if (Shaman::GetActiveImbue(player) != ShamanData::SPELL_ROCKBITER_WEAPON)
            return;

        if (uint32 const stacks = GetStacks())
        {
            Shaman::AddStoneskin(player, stacks);
            _granted = true;
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_sha_stoneskin_grant::HandleAfterHit);
    }

    bool _granted = false;
};

// 202207 Earth Attunement, 202209 Fire Attunement - the hidden child that carries the second half of the buff
// (armor / spell power: it joins a different stacking group than the parent's stats). The parent is a raid area
// aura, so this script also runs on every member's copy; only the shaman's own aura manages the child (the child
// is itself a raid area aura and spreads from the shaman).
class spell_sha_attunement : public AuraScript
{
    PrepareAuraScript(spell_sha_attunement);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTH_ATTUNEMENT_ARMOR,
            ShamanData::SPELL_FIRE_ATTUNEMENT_SPELL_POWER });
    }

    uint32 GetChildSpell() const
    {
        switch (GetId())
        {
            case ShamanData::SPELL_EARTH_ATTUNEMENT:
                return ShamanData::SPELL_EARTH_ATTUNEMENT_ARMOR;
            case ShamanData::SPELL_FIRE_ATTUNEMENT:
                return ShamanData::SPELL_FIRE_ATTUNEMENT_SPELL_POWER;
            default:
                return 0;
        }
    }

    void HandleApply(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (!target || GetCasterGUID() != target->GetGUID())
            return;

        if (uint32 const child = GetChildSpell())
            target->CastSpell(target, child, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (!target || GetCasterGUID() != target->GetGUID())
            return;

        if (uint32 const child = GetChildSpell())
            target->RemoveAurasDueToSpell(child, target->GetGUID());
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_attunement::HandleApply, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
        AfterEffectRemove += AuraEffectRemoveFn(spell_sha_attunement::HandleRemove, EFFECT_0, SPELL_AURA_ANY,
            AURA_EFFECT_HANDLE_REAL);
    }
};

void AddSC_shaman_shared_spell_scripts()
{
    RegisterSpellScript(spell_sha_imbue);
    RegisterSpellScript(spell_sha_flametongue_proc);
    RegisterSpellScript(spell_sha_flametongue_attack);
    RegisterSpellScript(spell_sha_frostbrand_proc);
    RegisterSpellScript(spell_sha_windfury_proc);
    RegisterSpellScript(spell_sha_windfury_attack);
    RegisterSpellScript(spell_sha_earthliving_proc);
    RegisterSpellScript(spell_sha_stoneskin_grant);
    RegisterSpellScript(spell_sha_attunement);
}
