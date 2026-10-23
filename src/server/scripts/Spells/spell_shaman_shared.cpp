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
 * shaman-rework S3a adds the Enhancement hooks that belong to the shared spells: the imbue-change reports to
 * Shaman::OnImbueChanged / OnRockbiterChanged, Volcanic Eruption's roll, Earth Shock's taunt and Earthen Ascendance
 * copies, Stoneskin's Mastery scaling and the Lightning Shield orb additions
 * (docs/reworks/shaman-enhancement-rework.md).
 */

#include "Cell.h"
#include "CellImpl.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ShamanMechanics.h"
#include "Spell.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "Unit.h"
#include <array>
#include <list>
#include <unordered_set>

namespace
{
    // Stock Maelstrom Weapon buff (the cumulative stack Frostbrand grants); no DSL variable names it
    constexpr uint32 SPELL_MAELSTROM_WEAPON_BUFF = 53817;

    // Earthliving's flat chance (shared doc "Earthliving": 20%), before the owner's Proc Chance
    constexpr float EARTHLIVING_CHANCE_PCT = 20.0f;

    // Windfury Attack's bonus: +20% of attack power per attack (U7), normalized the way weapon damage is
    // (AP / 14 per second of the hitting weapon's speed)
    constexpr float WINDFURY_AP_BONUS = 0.2f;

    // Talent rank chains the Enhancement hooks read, in rank order (reads go through Shaman::GetTalentRank).
    // Improved Lightning Shield (was Improved Shields); Maelstrom Weapon (ranks 4 and 5 are dropped from the talent).
    constexpr std::array<uint32, 3> IMPROVED_LIGHTNING_SHIELD_RANKS = { ShamanData::SPELL_IMPROVED_SHIELDS,
        ShamanData::SPELL_IMPROVED_SHIELDS_16290, ShamanData::SPELL_IMPROVED_SHIELDS_51881 };
    constexpr uint8 IMPROVED_LIGHTNING_SHIELD_CAPSTONE_RANK = 3;
    constexpr std::array<uint32, 3> MAELSTROM_WEAPON_RANKS = { ShamanData::SPELL_MAELSTROM_WEAPON,
        ShamanData::SPELL_MAELSTROM_WEAPON_51529, ShamanData::SPELL_MAELSTROM_WEAPON_51530 };

    constexpr std::array<uint32, 2> VOLCANIC_ERUPTION_RANKS =
    {
        ShamanData::SPELL_VOLCANIC_ERUPTION_RANK1,
        ShamanData::SPELL_VOLCANIC_ERUPTION_RANK2
    };

    // Taunt immunity (the helper's ATTACK_ME effect or its MOD_TAUNT aura): an immune target is skipped silently, a
    // taunt that can never land is not an error (raid bosses, the sim's Raid Boss).
    bool CanTaunt(Unit* caster, Unit* target, SpellInfo const* tauntInfo)
    {
        if (!target->IsAlive() || target->IsPlayer() || !caster->IsValidAttackTarget(target, tauntInfo))
            return false;

        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
        {
            SpellEffectInfo const& effect = tauntInfo->Effects[i];
            if (effect.Effect != SPELL_EFFECT_ATTACK_ME && effect.ApplyAuraName != SPELL_AURA_MOD_TAUNT)
                continue;

            if (target->IsImmunedToSpellEffect(tauntInfo, i, caster))
                return false;
        }

        return true;
    }

    // Which hand a melee proc event came from. Auto attacks and melee spells (Lava Lash, Stormstrike's off-hand
    // strike) both carry the hand flag (Unit.cpp GetProcFlagsForAttack / Spell::prepareDataForTriggerSystem).
    WeaponAttackType GetProcHand(ProcEventInfo const& eventInfo)
    {
        return (eventInfo.GetTypeMask() & PROC_FLAG_DONE_OFFHAND_ATTACK) ? OFF_ATTACK : BASE_ATTACK;
    }
}

// 8017 Rockbiter, 8024 Flametongue, 8033 Frostbrand, 8232 Windfury, 51730 Earthliving - the imbue self auras.
// Draws the weapon glow, applies the hidden child (Rockbiter: crit immunity and Earth Shock threat; Frostbrand: its
// proc child), strips Stoneskin when Rockbiter ends ("Exists only while Rockbiter is active") and reports imbue changes
// to the Enhancement charge machinery. Swap order (group 1251 rule 1): the old aura's remove runs first, with the new
// one not yet applied, and the new aura's apply follows in the same call stack. So the remove reports
// OnImbueChanged(old, 0) (Shaman stashes it) and the apply OnImbueChanged(0, new) (Shaman consumes the stash of this
// tick as the swap old -> new); a remove with no apply this tick (right-click, expiry, death) is no swap. Rockbiter's
// talent children (Spirit Guard parry, Improved Lightning Shield threat) are Shaman::OnRockbiterChanged's.
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

        // Players only: an NPC casting an imbue has no weapon slots to draw on and no talents
        Player* player = target->ToPlayer();
        if (!player)
            return;

        Shaman::ApplyImbueGlow(player);
        Shaman::OnImbueChanged(player, 0, GetId());

        if (GetId() == ShamanData::SPELL_ROCKBITER_WEAPON)
            Shaman::OnRockbiterChanged(player, true);
    }

    void HandleRemove(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Unit* target = GetTarget();
        if (uint32 const child = GetChildSpell())
            target->RemoveAurasDueToSpell(child);

        if (GetId() == ShamanData::SPELL_ROCKBITER_WEAPON)
            target->RemoveAurasDueToSpell(ShamanData::SPELL_STONESKIN_202206);

        Player* player = target->ToPlayer();
        if (!player)
            return;

        Shaman::OnImbueChanged(player, GetId(), 0);

        if (GetId() == ShamanData::SPELL_ROCKBITER_WEAPON)
            Shaman::OnRockbiterChanged(player, false);

        // The aura is already gone from the unit here, so the restore redraws the real values or the new imbue's glow
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
// Volcanic Eruption (S3a) rolls once per Flametongue Attack, no internal cooldown: its chance (rank 1 or 2, times
// Proc Chance) resets Lava Lash's cooldown and grants the +30% Lava Lash buff. Lava Lash is itself a melee hit that
// makes a Flametongue Attack, so a hit by Lava Lash never rolls: no loop. Stormstrike's two strikes (triggered, but
// NOT_A_PROC) do roll; the cleave strikes (202413 / 202415) proc nothing at all, so they never reach this proc.
class spell_sha_flametongue_proc : public AuraScript
{
    PrepareAuraScript(spell_sha_flametongue_proc);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_FLAMETONGUE_ATTACK, ShamanData::SPELL_LAVA_LASH,
            ShamanData::SPELL_VOLCANIC_ERUPTION_BUFF });
    }

    void RollVolcanicEruption(Player* player, ProcEventInfo& eventInfo, AuraEffect const* aurEff)
    {
        uint8 const rank = Shaman::GetTalentRank(player, VOLCANIC_ERUPTION_RANKS);
        if (!rank)
            return;

        if (SpellInfo const* hitSpell = eventInfo.GetSpellInfo())
            if (hitSpell->Id == ShamanData::SPELL_LAVA_LASH)
                return;

        float const chance = float(rank == 1 ? ShamanData::VE_CHANCE_R1 : ShamanData::VE_CHANCE_R2);
        if (!Shaman::RollProcChance(player, chance))
            return;

        player->RemoveSpellCooldown(ShamanData::SPELL_LAVA_LASH, true);
        player->CastSpell(player, ShamanData::SPELL_VOLCANIC_ERUPTION_BUFF, true, nullptr, aurEff);
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

        RollVolcanicEruption(player, eventInfo, aurEff);
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

        // The talent's rank spells (3 ranks, S3a), read by rank and never through HasSpell
        if (Shaman::GetTalentRank(player, MAELSTROM_WEAPON_RANKS))
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
// Blessing of the Eternals (S2a) raises the chance by 40/80% (relative: 20% becomes 28/36%, before Proc Chance) on a
// target at or below 35% health, judged on the health the target had before this heal landed.
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

        return Shaman::RollProcChance(owner, EARTHLIVING_CHANCE_PCT * GetBlessingOfTheEternalsFactor(owner,
            target, eventInfo.GetHealInfo()));
    }

    // 1 + the Blessing of the Eternals bonus when the target was at or below the threshold before the heal, else 1
    static float GetBlessingOfTheEternalsFactor(Unit* owner, Unit const* target, HealInfo const* healInfo)
    {
        uint32 const maxHealth = target->GetMaxHealth();
        if (!maxHealth)
            return 1.0f;

        uint32 const effective = healInfo->GetEffectiveHeal();
        uint32 const health = target->GetHealth();
        float const healthBefore = float(health > effective ? health - effective : 0);
        if (healthBefore * 100.0f > float(ShamanData::BOTE_THRESHOLD_PCT) * float(maxHealth))
            return 1.0f;

        switch (Shaman::GetTalentRank(owner->ToPlayer(), { ShamanData::SPELL_BLESSING_OF_THE_ETERNALS,
            ShamanData::SPELL_BLESSING_OF_THE_ETERNALS_51555 }))
        {
            case 1:
                return 1.0f + float(ShamanData::BOTE_BONUS_R1) / 100.0f;
            case 2:
                return 1.0f + float(ShamanData::BOTE_BONUS_R2) / 100.0f;
            default:
                return 1.0f;
        }
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
// Stormstrike and Lava Lash on their hit. NPCs cast 421 and 8042 too, so the caster must be a player. The triggered
// Earth Shock copies of Earthen Ascendance (spell_sha_earth_shock_rockbiter) grant nothing: the cast grants once.
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

        if (GetSpellInfo()->Id == ShamanData::SPELL_EARTH_SHOCK && GetSpell()->IsTriggered())
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

// 8042 Earth Shock under Rockbiter (shared doc "Earth Shock", Q9): the target is taunted (helper 202394: ATTACK_ME and
// MOD_TAUNT, a few seconds). Only a player caster with Rockbiter up taunts; NPC Earth Shock users (the spell is shared)
// and every other imbue keep the plain shock. A target immune to taunt (raid bosses, the sim's Raid Boss) is skipped
// silently, never an error. One taunt per target per cast.
// Earthen Ascendance (Living Earth's capstone buff, D7): the cast also shocks every other valid enemy within
// EARTHEN_ASC_RADIUS_YD of the shaman, in line of sight, as a triggered copy of Earth Shock; each copy taunts its own
// target. Copies never spawn copies, and spell_sha_stoneskin_grant skips them (the 15 Stoneskin stays once per cast).
class spell_sha_earth_shock_rockbiter : public SpellScript
{
    PrepareSpellScript(spell_sha_earth_shock_rockbiter);

    bool Validate(SpellInfo const* /*spellInfo*/) override
    {
        return ValidateSpellInfo({ ShamanData::SPELL_EARTH_SHOCK_TAUNT });
    }

    // The caster as a player with Rockbiter up, or nullptr
    Player* GetRockbiterPlayer()
    {
        Unit* caster = GetCaster();
        Player* player = caster ? caster->ToPlayer() : nullptr;
        if (!player || Shaman::GetActiveImbue(player) != ShamanData::SPELL_ROCKBITER_WEAPON)
            return nullptr;

        return player;
    }

    void HandleAfterHit()
    {
        Unit* target = GetHitUnit();
        Player* player = GetRockbiterPlayer();
        if (!target || !player || !_taunted.insert(target->GetGUID()).second)
            return;

        SpellInfo const* tauntInfo = sSpellMgr->GetSpellInfo(ShamanData::SPELL_EARTH_SHOCK_TAUNT);
        if (!tauntInfo || !CanTaunt(player, target, tauntInfo))
            return;

        player->CastSpell(target, ShamanData::SPELL_EARTH_SHOCK_TAUNT, true);
    }

    void HandleAfterCast()
    {
        if (GetSpell()->IsTriggered())
            return;

        Player* player = GetRockbiterPlayer();
        if (!player || !Shaman::IsEarthenAscendant(player))
            return;

        float const radius = ShamanData::EARTHEN_ASC_RADIUS_YD;
        Unit const* primary = GetExplTargetUnit();
        std::list<Unit*> nearby;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(player, player, radius);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(player, nearby, check);
        Cell::VisitObjects(player, searcher, radius);

        for (Unit* enemy : nearby)
        {
            if (enemy == primary || !enemy->IsAlive() || !player->IsValidAttackTarget(enemy, GetSpellInfo()) ||
                !player->IsWithinLOSInMap(enemy))
                continue;

            player->CastSpell(enemy, ShamanData::SPELL_EARTH_SHOCK, true);
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_sha_earth_shock_rockbiter::HandleAfterHit);
        AfterCast += SpellCastFn(spell_sha_earth_shock_rockbiter::HandleAfterCast);
    }

    std::unordered_set<ObjectGuid> _taunted;
};

// 202206 Stoneskin - the Ascendance talent scales the reduction by Mastery: the stack count x (1 + Mastery), rounded
// once, is the aura's whole amount (Shaman::GetStoneskinAmount; AddStoneskin and ErodeStoneskin write it after their
// own stack changes). The core recomputes the amount as the per-stack base x stacks on every apply, stack change and
// recalculation, which a per-stack calc hook cannot correct (the Mastery fraction), so this hook puts the whole amount
// back after each of them. It writes only when the amount differs, which ends the recursion the write itself starts.
class spell_sha_stoneskin : public AuraScript
{
    PrepareAuraScript(spell_sha_stoneskin);

    void HandleAmountChanged(AuraEffect const* /*aurEff*/, AuraEffectHandleModes /*mode*/)
    {
        Player* player = GetTarget()->ToPlayer();
        AuraEffect* effect = GetEffect(EFFECT_0);
        if (!player || !effect)
            return;

        int32 const amount = Shaman::GetStoneskinAmount(player, GetStackAmount());
        if (effect->GetAmount() != amount)
            effect->ChangeAmount(amount);
    }

    void Register() override
    {
        AfterEffectApply += AuraEffectApplyFn(spell_sha_stoneskin::HandleAmountChanged, EFFECT_0,
            SPELL_AURA_MOD_DAMAGE_PERCENT_TAKEN,
            AuraEffectHandleModes(AURA_EFFECT_HANDLE_REAL_OR_REAPPLY_MASK | AURA_EFFECT_HANDLE_CHANGE_AMOUNT));
    }
};

// 324 Lightning Shield (added next to the stock spell_sha_lightning_shield, which still casts the orb and stays the
// only script an NPC shaman's shield runs). The passive orb path, after the stock handler cast the orb and the core
// took the charge:
//  - Improved Lightning Shield, any rank, under Rockbiter: the orb grants ILS_ORB_STONESKIN Stoneskin.
//  - Improved Lightning Shield capstone (rank 3): ILS_NO_EXPEND_CHANCE% (x Proc Chance) a proc does not expend a
//    charge. The refund is AfterProc + ModCharges(+1): it runs after the core took the charge and before the aura is
//    removed for having none, and the proc's internal cooldown stays set (never DoPrepareProc, which skips both).
// Static Shock's own orb is cast by spell_sha_enh_static_shock, which owns its refund and Stoneskin.
class spell_sha_enh_lightning_shield : public AuraScript
{
    PrepareAuraScript(spell_sha_enh_lightning_shield);

    void HandleAfterProc(ProcEventInfo& /*eventInfo*/)
    {
        Unit* owner = GetUnitOwner();
        Player* player = owner ? owner->ToPlayer() : nullptr;
        if (!player)
            return;

        uint8 const rank = Shaman::GetTalentRank(player, IMPROVED_LIGHTNING_SHIELD_RANKS);
        if (!rank)
            return;

        if (Shaman::GetActiveImbue(player) == ShamanData::SPELL_ROCKBITER_WEAPON)
            Shaman::AddStoneskin(player, uint32(ShamanData::ILS_ORB_STONESKIN));

        if (rank >= IMPROVED_LIGHTNING_SHIELD_CAPSTONE_RANK &&
            Shaman::RollProcChance(player, float(ShamanData::ILS_NO_EXPEND_CHANCE)))
            GetAura()->ModCharges(1);
    }

    void Register() override
    {
        AfterProc += AuraProcFn(spell_sha_enh_lightning_shield::HandleAfterProc);
    }
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
    RegisterSpellScript(spell_sha_earth_shock_rockbiter);
    RegisterSpellScript(spell_sha_stoneskin);
    RegisterSpellScript(spell_sha_enh_lightning_shield);
    RegisterSpellScript(spell_sha_attunement);
}
